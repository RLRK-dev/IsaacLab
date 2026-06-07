# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Benchmark SensorTiledCamera rendering cost for visual RL obs.

Measures FPS with and without per-step camera rendering at various
world_count × camera_count × resolution configurations.

Usage:
    source ~/env_isaaclab6/bin/activate
    CUDA_VISIBLE_DEVICES=0 python thread_isaac_lab/scripts/bench_sensor_tiled_camera.py \
        --device cuda:0
"""

import argparse
import math
import os
import sys
import time

import numpy as np
import warp as wp

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)


def _look_at_quat(pos, target):
    """Compute quaternion for camera looking from pos at target."""
    from scipy.spatial.transform import Rotation
    forward = target - pos
    forward = forward / (np.linalg.norm(forward) + 1e-8)
    up = np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, up)
    right_norm = np.linalg.norm(right)
    if right_norm < 1e-6:
        up = np.array([0.0, 1.0, 0.0])
        right = np.cross(forward, up)
        right_norm = np.linalg.norm(right)
    right = right / right_norm
    up = np.cross(right, forward)
    rot_mat = np.stack([right, up, -forward], axis=1)
    return Rotation.from_matrix(rot_mat).as_quat()  # (x, y, z, w)


def build_camera_transforms(env, camera_count, hand_offsets):
    """Build camera transforms from hand body positions.

    Args:
        env: Newton env with _state_0, _bws
        camera_count: number of cameras
        hand_offsets: list of (type, body_offset, pos, target) per camera
            type="wrist": pos/target are local offsets relative to hand body
            type="fixed": pos/target are world-space positions (same for all worlds)

    Returns:
        wp.array of shape (camera_count, world_count) dtype=wp.transformf
    """
    from scipy.spatial.transform import Rotation

    N = env._world_count
    bq = env._state_0.body_q.numpy()
    tf_list = []

    for cam_idx in range(camera_count):
        cam_type, body_offset, local_pos, local_target = hand_offsets[cam_idx]
        cam_world_tfs = []

        for w in range(N):
            if cam_type == "fixed":
                cam_pos = local_pos.copy()
                cam_target = local_target.copy()
            else:  # "wrist"
                bws = env._bws[w]
                body_idx = bws + body_offset
                body_tf = bq[body_idx]
                hand_pos = body_tf[:3]
                hand_quat = body_tf[3:7]
                r = Rotation.from_quat([hand_quat[0], hand_quat[1],
                                        hand_quat[2], hand_quat[3]])
                cam_pos = hand_pos + r.apply(local_pos)
                cam_target = hand_pos + r.apply(local_target)

            cam_quat = _look_at_quat(cam_pos, cam_target)
            cam_world_tfs.append(
                wp.transformf(
                    wp.vec3f(float(cam_pos[0]), float(cam_pos[1]), float(cam_pos[2])),
                    wp.quatf(float(cam_quat[0]), float(cam_quat[1]),
                             float(cam_quat[2]), float(cam_quat[3])),
                )
            )
        tf_list.append(cam_world_tfs)

    return wp.array(tf_list, dtype=wp.transformf)


def run_benchmark(env, world_count, camera_count, resolution, fov_deg, n_steps, device):
    """Run benchmark for a specific configuration."""
    from newton.sensors import SensorTiledCamera

    W, H = resolution, resolution

    # Setup sensor
    sensor = SensorTiledCamera(
        model=env._model,
        config=SensorTiledCamera.Config(
            default_light=True,
            default_light_shadows=False,  # shadows off for speed
            colors_per_shape=True,
            backface_culling=True,
        ),
    )

    # camera_fovs must be a list of length camera_count
    fov_list = [math.radians(fov_deg)] * camera_count
    camera_rays = sensor.compute_pinhole_camera_rays(W, H, fov_list)
    color_buf = sensor.create_color_image_output(W, H, camera_count)
    depth_buf = sensor.create_depth_image_output(W, H, camera_count)

    # Camera offsets: (body_offset_from_bws, local_pos, local_target)
    # body 6 = panda_hand (right arm)
    # body 15 = panda_hand (left arm, 9 bodies offset)
    HAND_R_OFFSET = 6
    HAND_L_OFFSET = 6 + 9  # second robot
    WRIST_LOCAL_POS = np.array([0.05, 0.0, 0.04])  # PhysX wrist camera offset
    WRIST_LOCAL_TARGET = np.array([0.0, 0.0, 0.22])  # look at fingertip

    OVERHEAD_POS = np.array([0.35, -0.05, 1.50])
    OVERHEAD_TARGET = np.array([0.35, -0.05, 0.80])

    if camera_count == 1:
        hand_offsets = [("wrist", HAND_R_OFFSET, WRIST_LOCAL_POS, WRIST_LOCAL_TARGET)]
    elif camera_count == 2:
        hand_offsets = [
            ("wrist", HAND_R_OFFSET, WRIST_LOCAL_POS, WRIST_LOCAL_TARGET),
            ("wrist", HAND_L_OFFSET, WRIST_LOCAL_POS, WRIST_LOCAL_TARGET),
        ]
    else:  # 3
        hand_offsets = [
            ("wrist", HAND_R_OFFSET, WRIST_LOCAL_POS, WRIST_LOCAL_TARGET),
            ("wrist", HAND_L_OFFSET, WRIST_LOCAL_POS, WRIST_LOCAL_TARGET),
            ("fixed", 0, OVERHEAD_POS, OVERHEAD_TARGET),
        ]

    # Warmup: 5 steps with rendering
    obs, _ = env.reset()
    for _ in range(5):
        actions = torch.zeros(world_count, env.num_actions, device=device)
        obs, _, _, _ = env.step(actions)
        wp.synchronize()
        cam_tf = build_camera_transforms(env, camera_count, hand_offsets)
        sensor.update(env._state_0, cam_tf, camera_rays,
                      color_image=color_buf, depth_image=depth_buf)
        wp.synchronize()

    # Benchmark 1: Physics only (no rendering)
    obs, _ = env.reset()
    wp.synchronize()
    t0 = time.perf_counter()
    for _ in range(n_steps):
        actions = torch.zeros(world_count, env.num_actions, device=device)
        obs, _, _, _ = env.step(actions)
    wp.synchronize()
    t_physics = time.perf_counter() - t0
    fps_physics = n_steps / t_physics

    # Benchmark 2: Physics + Rendering (RGB + Depth)
    obs, _ = env.reset()
    wp.synchronize()
    t0 = time.perf_counter()
    for _ in range(n_steps):
        actions = torch.zeros(world_count, env.num_actions, device=device)
        obs, _, _, _ = env.step(actions)
        wp.synchronize()
        cam_tf = build_camera_transforms(env, camera_count, hand_offsets)
        sensor.update(env._state_0, cam_tf, camera_rays,
                      color_image=color_buf, depth_image=depth_buf)
    wp.synchronize()
    t_with_render = time.perf_counter() - t0
    fps_with_render = n_steps / t_with_render

    # Benchmark 3: Rendering only (no physics step)
    wp.synchronize()
    t0 = time.perf_counter()
    for _ in range(n_steps):
        cam_tf = build_camera_transforms(env, camera_count, hand_offsets)
        sensor.update(env._state_0, cam_tf, camera_rays,
                      color_image=color_buf, depth_image=depth_buf)
    wp.synchronize()
    t_render_only = time.perf_counter() - t0
    fps_render_only = n_steps / t_render_only
    ms_per_render = (t_render_only / n_steps) * 1000

    # Verify output
    color_np = color_buf.numpy()
    depth_np = depth_buf.numpy()
    assert color_np.shape == (world_count, camera_count, H, W), f"color shape: {color_np.shape}"
    assert depth_np.shape == (world_count, camera_count, H, W), f"depth shape: {depth_np.shape}"
    has_content = color_np.max() > color_np.min()

    return {
        "world_count": world_count,
        "camera_count": camera_count,
        "resolution": f"{W}x{H}",
        "fps_physics_only": fps_physics,
        "fps_physics_render": fps_with_render,
        "fps_render_only": fps_render_only,
        "ms_per_render": ms_per_render,
        "overhead_pct": (t_with_render - t_physics) / t_physics * 100,
        "has_content": has_content,
        "total_pixels": world_count * camera_count * W * H,
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark SensorTiledCamera")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--n-steps", type=int, default=100,
                        help="Steps per benchmark run")
    parser.add_argument("--quick", action="store_true",
                        help="Quick mode: fewer configurations")
    args = parser.parse_args()

    os.environ["NEWTON_DEVICE"] = args.device

    import torch
    global torch

    from newton_approach_cable_env import NewtonApproachCableEnv

    # Test configurations: (world_count, camera_count, resolution, fov_deg)
    if args.quick:
        configs = [
            (4, 1, 128, 60),
            (4, 3, 128, 60),
            (32, 3, 128, 60),
        ]
    else:
        configs = [
            # Baseline: single camera, varying worlds
            (4, 1, 128, 60),
            (16, 1, 128, 60),
            (32, 1, 128, 60),
            # 2 wrist cameras
            (4, 2, 128, 60),
            (16, 2, 128, 60),
            (32, 2, 128, 60),
            # 3 cameras (2 wrist + 1 overhead)
            (4, 3, 128, 60),
            (16, 3, 128, 60),
            (32, 3, 128, 60),
            # Resolution comparison at 32 worlds, 3 cameras
            (32, 3, 64, 60),
            (32, 3, 128, 60),
            (32, 3, 224, 60),
        ]

    print(f"[BENCH] SensorTiledCamera Benchmark")
    print(f"[BENCH] Device: {args.device}")
    print(f"[BENCH] Steps per config: {args.n_steps}")
    print(f"[BENCH] Configurations: {len(configs)}")
    print()

    results = []
    prev_world_count = None

    for wc, cc, res, fov in configs:
        # Create env only when world_count changes
        if wc != prev_world_count:
            if prev_world_count is not None and hasattr(env, 'close'):
                env.close()
            print(f"[BENCH] Creating {wc}-world environment...")
            env = NewtonApproachCableEnv(world_count=wc, device=args.device)
            prev_world_count = wc

        label = f"W={wc:3d} C={cc} R={res:3d}x{res:3d}"
        print(f"[BENCH] Running: {label} ...", end="", flush=True)

        try:
            r = run_benchmark(env, wc, cc, res, fov, args.n_steps, args.device)
            results.append(r)
            print(f"  physics={r['fps_physics_only']:.1f} FPS  "
                  f"phys+render={r['fps_physics_render']:.1f} FPS  "
                  f"render_only={r['fps_render_only']:.1f} FPS  "
                  f"render={r['ms_per_render']:.1f}ms  "
                  f"overhead={r['overhead_pct']:.0f}%  "
                  f"content={'OK' if r['has_content'] else 'EMPTY'}")
        except Exception as e:
            print(f"  FAILED: {e}")
            results.append({
                "world_count": wc, "camera_count": cc, "resolution": f"{res}x{res}",
                "error": str(e),
            })

    if hasattr(env, 'close'):
        env.close()

    # Summary table
    print(f"\n{'='*100}")
    print(f"{'Config':<25} {'Physics':>10} {'Phys+Rend':>10} {'Render':>10} {'ms/render':>10} {'Overhead':>10} {'Pixels':>12}")
    print(f"{'='*100}")
    for r in results:
        if "error" in r:
            print(f"W={r['world_count']:3d} C={r['camera_count']} {r['resolution']:<7s}  ERROR: {r['error']}")
            continue
        label = f"W={r['world_count']:3d} C={r['camera_count']} {r['resolution']:<7s}"
        print(f"{label:<25} {r['fps_physics_only']:>8.1f}Hz {r['fps_physics_render']:>8.1f}Hz "
              f"{r['fps_render_only']:>8.1f}Hz {r['ms_per_render']:>8.1f}ms "
              f"{r['overhead_pct']:>8.0f}% {r['total_pixels']:>10,d}")
    print(f"{'='*100}")

    # Training viability assessment
    print(f"\n[BENCH] === Training Viability Assessment ===")
    for r in results:
        if "error" in r:
            continue
        fps = r['fps_physics_render']
        # At 32 worlds, PHYSICS_STEPS_PER_RL=10, we need ~55 FPS baseline
        # Acceptable slowdown: < 50% overhead
        viable = r['overhead_pct'] < 50
        status = "VIABLE" if viable else "TOO SLOW"
        print(f"  W={r['world_count']:3d} C={r['camera_count']} {r['resolution']:<7s}: "
              f"{fps:.1f} FPS, {r['overhead_pct']:.0f}% overhead → {status}")


if __name__ == "__main__":
    import torch
    main()
