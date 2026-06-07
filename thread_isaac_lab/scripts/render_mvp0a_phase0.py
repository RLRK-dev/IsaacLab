# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MVP-0A Phase 0 dataset generation.

Renders wrist L/R RGB-D + per-pixel shape_index from AC env on cuda:1
(PRO 4000, project label "cuda:2"). Output goes to
``data/mvp0a_phase0_dataset/`` with ``LABELS_ONLY/`` subdirectory
segregating ground-truth metadata per CC5-1 R6 mitigation.

Scope: OQ-1a APPROVE / Rs Option A narrowed scope (PROPOSE v2). No env edits,
no policy training, no cuda:0 sim slot usage.

Usage::

    CUDA_VISIBLE_DEVICES=1 ./isaaclab.sh -p \
        thread_isaac_lab/scripts/render_mvp0a_phase0.py \
        --device cuda:0 --num-frames 250 --num-resets 3
"""

import argparse
import json
import math
import os
import sys
import time

import numpy as np
import torch
import warp as wp

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)


# Camera offsets matching wrist_camera_manager.py defaults (verified body 6 / link7 frame).
HAND_R_OFFSET = 6  # right arm panda_hand
HAND_L_OFFSET = 6 + 9  # left arm panda_hand
WRIST_LOCAL_POS = np.array([0.05, 0.05, 0.10])
WRIST_LOCAL_TARGET = np.array([0.0, 0.0, 0.17])
RES = 128
FOV_DEG = 45.0
CAM_COUNT = 2  # wrist L + R


def _look_at_quat(pos, target):
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
    return Rotation.from_matrix(rot_mat).as_quat()  # xyzw


def build_camera_transforms(env, hand_offsets):
    from scipy.spatial.transform import Rotation
    N = env._world_count
    bq = env._state_0.body_q.numpy()
    tf_list = []
    for body_offset, local_pos, local_target in hand_offsets:
        cam_world_tfs = []
        for w in range(N):
            bws = env._bws[w]
            body_idx = bws + body_offset
            body_tf = bq[body_idx]
            hand_pos = body_tf[:3]
            hand_quat = body_tf[3:7]  # xyzw
            r = Rotation.from_quat([hand_quat[0], hand_quat[1], hand_quat[2], hand_quat[3]])
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


def build_shape_class_lut(env, debug_log_path=None):
    """Build per-shape semantic class LUT.

    Class IDs:
      0 = background / no hit (shape_idx == 0xFFFFFFFF)
      1 = cable
      2 = clip (any clip support body in this AC variant — 3 support clips)
      3 = gripper / finger (panda fingers, 2 per arm)
      4 = robot arm (other arm/hand bodies)
      5 = table / other

    Returns dict with class IDs and the LUT array of shape (model.shape_count,) uint8.
    """
    model = env._model
    shape_count = model.shape_count
    shape_body = model.shape_body.numpy()  # (shape_count,) → body index per shape

    cable_body_set = set()
    for w_bodies in env._cable_bodies:
        cable_body_set.update(w_bodies)

    # Support clip bodies: env added 3 support clips in newton_approach_cable_env (lines 452-468).
    # We don't have direct API to list clip bodies; we infer them as bodies with index >= ROBOT+CABLE
    # per world * world_count, so any body not in cable + robot + non-zero is clip-like.
    # ROBOT_BODY_COUNT=18 per world, 40 cable bodies per world.
    ROBOT_BODY_COUNT = 18
    CABLE_BODIES_PER_WORLD = 40
    bodies_per_world = env._bodies_per_world

    clip_body_set = set()
    for w in range(env._world_count):
        bws = env._bws[w]
        # bodies in [bws + ROBOT_BODY_COUNT + CABLE_BODIES_PER_WORLD, bws + bodies_per_world)
        # are extra (clips + table)
        for b in range(bws + ROBOT_BODY_COUNT + CABLE_BODIES_PER_WORLD, bws + bodies_per_world):
            clip_body_set.add(b)

    # Gripper bodies: finger bodies are at offset 7 and 8 within each arm (Franka has 9 bodies, finger = body 7,8).
    # Actually for Franka: bodies 7,8 are fingers in URDF. Verify with FK joint_q range.
    # Per AC env: panda_hand = body 6, fingers = body 7,8.
    gripper_body_set = set()
    arm_body_set = set()
    for w in range(env._world_count):
        bws = env._bws[w]
        for arm_off in (0, 9):  # right arm, left arm offsets
            for b_idx in range(9):  # 9 bodies per arm
                body_idx = bws + arm_off + b_idx
                if b_idx in (7, 8):  # finger left/right
                    gripper_body_set.add(body_idx)
                else:
                    arm_body_set.add(body_idx)

    lut = np.zeros(shape_count, dtype=np.uint8)
    counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for shape_idx in range(shape_count):
        body_idx = int(shape_body[shape_idx])
        if body_idx == -1:
            class_id = 5  # static/world (table)
        elif body_idx in cable_body_set:
            class_id = 1  # cable
        elif body_idx in clip_body_set:
            class_id = 2  # clip
        elif body_idx in gripper_body_set:
            class_id = 3  # gripper
        elif body_idx in arm_body_set:
            class_id = 4  # arm
        else:
            class_id = 5  # other / static
        lut[shape_idx] = class_id
        counts[class_id] += 1

    summary = {
        "shape_count": int(shape_count),
        "world_count": int(env._world_count),
        "bodies_per_world": int(bodies_per_world),
        "class_counts_total_shapes": counts,
        "class_legend": {
            "0": "background_no_hit",
            "1": "cable",
            "2": "clip",
            "3": "gripper_finger",
            "4": "robot_arm",
            "5": "other_static",
        },
        "cable_body_count": len(cable_body_set),
        "clip_body_count": len(clip_body_set),
        "gripper_body_count": len(gripper_body_set),
        "arm_body_count": len(arm_body_set),
    }
    if debug_log_path:
        with open(debug_log_path, "w") as f:
            json.dump(summary, f, indent=2)
    return lut, summary


def verify_lut_against_projection(env, lut, sensor, camera_rays, color_buf, depth_buf,
                                   shape_idx_buf, hand_offsets, summary):
    """CC4-3 GT verification: render once, check shape_index pixels match lut classes.

    Sanity assertions:
      - At least 100 cable pixels visible across all worlds/cameras (cable should be in ROI).
      - Background pixels (class 0) should also exist (sky / out-of-frustum).
      - Class 5 (other_static, table) should exist.
    """
    cam_tf = build_camera_transforms(env, hand_offsets)
    sensor.update(env._state_0, cam_tf, camera_rays,
                  color_image=color_buf, depth_image=depth_buf,
                  shape_index_image=shape_idx_buf)
    wp.synchronize()
    shape_idx_np = shape_idx_buf.numpy()  # (W, C, H, W) uint32

    # 0xFFFFFFFF means no hit; label as class 0 (background)
    NO_HIT = np.uint32(0xFFFFFFFF)
    bg_mask = shape_idx_np == NO_HIT
    # For shapes that do hit, look up class via lut. shape_idx out-of-range → treat as 0
    shape_count = lut.shape[0]
    safe_idx = np.where(bg_mask, np.uint32(0), shape_idx_np)
    safe_idx = np.minimum(safe_idx, np.uint32(shape_count - 1))
    class_map = lut[safe_idx]
    class_map[bg_mask] = 0

    # Pixel counts per class
    pixel_counts = {int(c): int((class_map == c).sum()) for c in range(6)}
    summary["pixel_counts_first_frame"] = pixel_counts

    cable_pixels = pixel_counts.get(1, 0)
    if cable_pixels < 50:
        print(f"[verify_lut][WARN] cable pixels = {cable_pixels} (< 50). "
              f"Camera ROI may not include cable; not necessarily a bug.")
    print(f"[verify_lut] pixel counts (first frame): {pixel_counts}")
    return class_map


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cuda:0",
                        help="Relative CUDA device (use CUDA_VISIBLE_DEVICES to pin physical GPU).")
    parser.add_argument("--num-resets", type=int, default=3,
                        help="Number of env resets (different DR seeds).")
    parser.add_argument("--steps-per-reset", type=int, default=50)
    parser.add_argument("--capture-every", type=int, default=5)
    parser.add_argument("--world-count", type=int, default=4)
    parser.add_argument("--output-dir", default="/home/rlrk/IsaacLab/data/mvp0a_phase0_dataset")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-frames", type=int, default=400,
                        help="Hard cap on saved frames (per-camera-per-world counted).")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    rgb_dir = os.path.join(args.output_dir, "RGB")
    depth_dir = os.path.join(args.output_dir, "DEPTH")
    labels_dir = os.path.join(args.output_dir, "LABELS_ONLY")
    os.makedirs(rgb_dir, exist_ok=True)
    os.makedirs(depth_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)

    print(f"[render_mvp0a_phase0] device={args.device}, world_count={args.world_count}, "
          f"resets={args.num_resets}, steps={args.steps_per_reset}, capture_every={args.capture_every}")
    print(f"[render_mvp0a_phase0] output: {args.output_dir}")

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    # Init AC env
    from newton_approach_cable_env import NewtonApproachCableEnv
    env = NewtonApproachCableEnv(
        world_count=args.world_count,
        device=args.device,
        enable_camera=False,  # we set up our own sensor with shape_index
    )
    print(f"[render_mvp0a_phase0] env ready: obs={env.num_obs}, actions={env.num_actions}")

    # Build my own SensorTiledCamera with shape_index buffer
    from newton.sensors import SensorTiledCamera
    sensor = SensorTiledCamera(
        model=env._model,
        config=SensorTiledCamera.Config(
            default_light=True,
            default_light_shadows=False,
            colors_per_shape=True,
            backface_culling=True,
        ),
    )
    fov_list = [math.radians(FOV_DEG)] * CAM_COUNT
    camera_rays = sensor.compute_pinhole_camera_rays(RES, RES, fov_list)
    color_buf = sensor.create_color_image_output(RES, RES, CAM_COUNT)
    depth_buf = sensor.create_depth_image_output(RES, RES, CAM_COUNT)
    shape_idx_buf = sensor.create_shape_index_image_output(RES, RES, CAM_COUNT)

    hand_offsets = [
        (HAND_R_OFFSET, WRIST_LOCAL_POS, WRIST_LOCAL_TARGET),
        (HAND_L_OFFSET, WRIST_LOCAL_POS, WRIST_LOCAL_TARGET),
    ]

    # Build shape_class LUT (LABELS_ONLY/ segregation per CC5-1)
    lut_path = os.path.join(labels_dir, "shape_class_lut.npz")
    summary_path = os.path.join(labels_dir, "shape_class_lut_summary.json")
    lut, summary = build_shape_class_lut(env, debug_log_path=summary_path)
    print(f"[render_mvp0a_phase0] LUT built: shape_count={summary['shape_count']}, "
          f"class_counts={summary['class_counts_total_shapes']}")
    np.savez_compressed(lut_path, lut=lut)
    print(f"[render_mvp0a_phase0] LUT saved: {lut_path}")

    # CC4-3 GT verification
    verify_lut_against_projection(env, lut, sensor, camera_rays, color_buf, depth_buf,
                                  shape_idx_buf, hand_offsets, summary)
    # Re-save summary with pixel counts
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Dataset gen loop
    saved_frames = 0
    metadata = []
    t0 = time.perf_counter()

    for reset_idx in range(args.num_resets):
        # Reset (uses internal random seed; we'll vary by adding different small actions)
        env.reset()
        wp.synchronize()
        print(f"[render_mvp0a_phase0] Reset {reset_idx + 1}/{args.num_resets}")

        for step_idx in range(args.steps_per_reset):
            # Apply small random action to perturb cable state (still safe, just noise)
            actions = (torch.rand(args.world_count, env.num_actions,
                                  device=args.device, dtype=torch.float32) - 0.5) * 0.01
            env.step(actions)

            if step_idx % args.capture_every == 0 and step_idx >= 5:
                wp.synchronize()
                cam_tf = build_camera_transforms(env, hand_offsets)
                sensor.update(env._state_0, cam_tf, camera_rays,
                              color_image=color_buf, depth_image=depth_buf,
                              shape_index_image=shape_idx_buf)
                wp.synchronize()

                color_np = color_buf.numpy()  # (W, C, H, W) uint32 RGBA
                depth_np = depth_buf.numpy()  # (W, C, H, W) float32
                shape_idx_np = shape_idx_buf.numpy()  # (W, C, H, W) uint32
                bq_np = env._state_0.body_q.numpy()  # (total_bodies, 7)

                # Save per-frame: 1 npz per (reset, step) for easier random access
                frame_id = f"r{reset_idx:02d}_s{step_idx:03d}"
                np.savez_compressed(
                    os.path.join(rgb_dir, f"{frame_id}_rgb.npz"),
                    color=color_np,
                )
                np.savez_compressed(
                    os.path.join(depth_dir, f"{frame_id}_depth.npz"),
                    depth=depth_np,
                )
                np.savez_compressed(
                    os.path.join(labels_dir, f"{frame_id}_label.npz"),
                    shape_idx=shape_idx_np,
                    body_q=bq_np,
                )
                metadata.append({
                    "frame_id": frame_id,
                    "reset_idx": int(reset_idx),
                    "step_idx": int(step_idx),
                    "world_count": int(args.world_count),
                    "camera_count": int(CAM_COUNT),
                    "resolution": int(RES),
                })
                saved_frames += args.world_count * CAM_COUNT  # per-world-per-camera count
                if saved_frames >= args.max_frames * args.world_count * CAM_COUNT:
                    break
        if saved_frames >= args.max_frames * args.world_count * CAM_COUNT:
            print(f"[render_mvp0a_phase0] Reached max-frames cap ({args.max_frames}); stopping.")
            break

    elapsed = time.perf_counter() - t0

    # Save metadata
    metadata_path = os.path.join(args.output_dir, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump({
            "device": args.device,
            "num_resets": args.num_resets,
            "steps_per_reset": args.steps_per_reset,
            "capture_every": args.capture_every,
            "world_count": args.world_count,
            "camera_count": CAM_COUNT,
            "resolution": RES,
            "fov_deg": FOV_DEG,
            "hand_r_offset": HAND_R_OFFSET,
            "hand_l_offset": HAND_L_OFFSET,
            "wrist_local_pos": WRIST_LOCAL_POS.tolist(),
            "wrist_local_target": WRIST_LOCAL_TARGET.tolist(),
            "frames": metadata,
            "saved_frame_count": int(saved_frames),
            "elapsed_seconds": float(elapsed),
            "lut_path": lut_path,
            "shape_class_summary": summary,
        }, f, indent=2)

    print(f"[render_mvp0a_phase0] DONE. Saved {saved_frames} per-camera-per-world frames "
          f"({len(metadata)} npz triplets) in {elapsed:.1f}s")
    print(f"[render_mvp0a_phase0] Metadata: {metadata_path}")


if __name__ == "__main__":
    main()
