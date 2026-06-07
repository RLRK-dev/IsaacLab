# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""PoC: Wrist-mounted RGB-D camera via SensorTiledCamera.

Creates a 1-world ApproachCable env, attaches 2 wrist cameras (L/R)
to panda_hand bodies, runs a few steps, and saves RGB + depth frames
as PNG images for visual inspection.

Usage:
    source ~/env_isaaclab6/bin/activate
    CUDA_VISIBLE_DEVICES=1 python thread_isaac_lab/scripts/poc_wrist_camera.py \
        --device cuda:0
"""

import argparse
import math
import os
import sys

import numpy as np
import torch
import warp as wp

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)


def look_at_transform(cam_pos, cam_target):
    """Compute wp.transformf for camera looking from pos at target."""
    from scipy.spatial.transform import Rotation

    forward = cam_target - cam_pos
    forward = forward / (np.linalg.norm(forward) + 1e-8)
    up = np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, up)
    rn = np.linalg.norm(right)
    if rn < 1e-6:
        up = np.array([0.0, 1.0, 0.0])
        right = np.cross(forward, up)
        rn = np.linalg.norm(right)
    right = right / rn
    up = np.cross(right, forward)
    rot_mat = np.stack([right, up, -forward], axis=1)
    q = Rotation.from_matrix(rot_mat).as_quat()  # (x,y,z,w)
    return wp.transformf(
        wp.vec3f(float(cam_pos[0]), float(cam_pos[1]), float(cam_pos[2])),
        wp.quatf(float(q[0]), float(q[1]), float(q[2]), float(q[3])),
    )


def get_wrist_camera_transforms(env, world_idx=0):
    """Get camera transforms for L/R wrist cameras from body state."""
    from scipy.spatial.transform import Rotation

    bq = env._state_0.body_q.numpy()
    bws = env._bws[world_idx]

    # panda_hand body indices (left arm added first → body 0-8, right arm → body 9-17)
    EE_BODY_OFFSET = 6
    FRANKA_NUM_JOINTS = 9
    HAND_L = bws + EE_BODY_OFFSET
    HAND_R = bws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET

    # Local offsets in body 6 (link7) frame — matches test_newton_clip_routing.py
    # ~45° diagonal view of finger clamp area
    LOCAL_POS = np.array([0.05, 0.05, 0.10])    # 5cm X, 5cm Y, 10cm along Z (past finger joints)
    LOCAL_TARGET = np.array([0.0, 0.0, 0.17])   # finger mid-area

    transforms = []
    hand_info = []

    for label, body_idx in [("L", HAND_L), ("R", HAND_R)]:
        body_tf = bq[body_idx]
        hand_pos = body_tf[:3]
        hand_quat = body_tf[3:7]

        print(f"  [{label}] hand_quat (xyzw): [{hand_quat[0]:.4f}, {hand_quat[1]:.4f}, {hand_quat[2]:.4f}, {hand_quat[3]:.4f}]")
        r = Rotation.from_quat([hand_quat[0], hand_quat[1],
                                hand_quat[2], hand_quat[3]])
        cam_pos = hand_pos + r.apply(LOCAL_POS)
        cam_target = hand_pos + r.apply(LOCAL_TARGET)

        tf = look_at_transform(cam_pos, cam_target)
        transforms.append(tf)
        hand_info.append({
            "label": label,
            "hand_pos": hand_pos.copy(),
            "cam_pos": cam_pos.copy(),
            "cam_target": cam_target.copy(),
        })

    return transforms, hand_info


def save_color_frame(color_buf, world_idx, cam_idx, output_dir, step, label):
    """Save RGBA uint32 buffer as RGB PNG."""
    from PIL import Image

    frame = color_buf.numpy()[world_idx, cam_idx]  # (H, W) uint32
    # uint32 RGBA → (H, W, 4) uint8
    rgba = np.frombuffer(frame.tobytes(), dtype=np.uint8).reshape(frame.shape[0], frame.shape[1], 4)
    rgb = rgba[:, :, :3]  # drop alpha
    img = Image.fromarray(rgb)
    path = os.path.join(output_dir, f"step{step:03d}_{label}_rgb.png")
    img.save(path)
    return path


def save_depth_frame(depth_buf, world_idx, cam_idx, output_dir, step, label):
    """Save depth float32 buffer as normalized grayscale PNG."""
    from PIL import Image

    depth = depth_buf.numpy()[world_idx, cam_idx]  # (H, W) float32
    # Normalize to 0-255 for visualization
    valid = depth[depth > 0]
    if len(valid) == 0:
        d_min, d_max = 0.0, 1.0
    else:
        d_min, d_max = valid.min(), valid.max()
    depth_norm = np.clip((depth - d_min) / (d_max - d_min + 1e-6), 0, 1)
    depth_u8 = (depth_norm * 255).astype(np.uint8)
    img = Image.fromarray(depth_u8, mode='L')
    path = os.path.join(output_dir, f"step{step:03d}_{label}_depth.png")
    img.save(path)
    return path, d_min, d_max


def main():
    parser = argparse.ArgumentParser(description="PoC: Wrist Camera RGB-D")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--steps", type=int, default=10,
                        help="Number of env steps to capture")
    parser.add_argument("--output-dir", type=str,
                        default="thread_isaac_lab/data/poc_wrist_camera")
    parser.add_argument("--fov", type=float, default=45.0,
                        help="Camera FOV in degrees")
    parser.add_argument("--resolution", type=int, default=128,
                        help="Camera resolution (square)")
    args = parser.parse_args()

    os.environ["NEWTON_DEVICE"] = args.device

    from newton.sensors import SensorTiledCamera
    from newton_approach_cable_env import NewtonApproachCableEnv

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    print(f"[POC] Creating 1-world env on {args.device}...")
    env = NewtonApproachCableEnv(world_count=1, device=args.device)
    print(f"[POC] Env ready. Bodies: {env._model.body_count}, Shapes: {env._model.shape_count}")

    # Setup SensorTiledCamera
    W, H = args.resolution, args.resolution
    CAM_COUNT = 2  # L wrist + R wrist
    FOV_DEG = args.fov

    print(f"[POC] Setting up SensorTiledCamera: {CAM_COUNT} cameras, {W}x{H}, FOV={FOV_DEG}°")
    sensor = SensorTiledCamera(
        model=env._model,
        config=SensorTiledCamera.Config(
            default_light=True,
            default_light_shadows=True,
            colors_per_shape=True,
            backface_culling=True,
        ),
    )

    fov_list = [math.radians(FOV_DEG)] * CAM_COUNT
    camera_rays = sensor.compute_pinhole_camera_rays(W, H, fov_list)
    color_buf = sensor.create_color_image_output(W, H, CAM_COUNT)
    depth_buf = sensor.create_depth_image_output(W, H, CAM_COUNT)

    print(f"[POC] color_buf shape: {color_buf.shape}")
    print(f"[POC] depth_buf shape: {depth_buf.shape}")

    # Reset env
    obs, _ = env.reset()
    wp.synchronize()

    print(f"\n[POC] Running {args.steps} steps, capturing RGB-D frames...")

    for step in range(args.steps):
        # Zero actions (hold position)
        actions = torch.zeros(1, env.num_actions, device=args.device)
        obs, _, _, extras = env.step(actions)
        wp.synchronize()

        # Get wrist camera transforms
        cam_tfs, hand_info = get_wrist_camera_transforms(env, world_idx=0)
        # Shape must be (camera_count, world_count) = (2, 1)
        cam_tf_array = wp.array([[tf] for tf in cam_tfs], dtype=wp.transformf)

        # Render
        sensor.update(env._state_0, cam_tf_array, camera_rays,
                      color_image=color_buf, depth_image=depth_buf)
        wp.synchronize()

        # Save frames
        labels = ["wrist_L", "wrist_R"]
        for cam_idx, label in enumerate(labels):
            rgb_path = save_color_frame(color_buf, 0, cam_idx, output_dir, step, label)
            depth_path, d_min, d_max = save_depth_frame(depth_buf, 0, cam_idx, output_dir, step, label)

            hi = hand_info[cam_idx]
            if step == 0 or step == args.steps - 1:
                print(f"  step {step} [{label}]:")
                print(f"    hand_pos = [{hi['hand_pos'][0]:.4f}, {hi['hand_pos'][1]:.4f}, {hi['hand_pos'][2]:.4f}]")
                print(f"    cam_pos  = [{hi['cam_pos'][0]:.4f}, {hi['cam_pos'][1]:.4f}, {hi['cam_pos'][2]:.4f}]")
                print(f"    depth range: {d_min:.4f} - {d_max:.4f} m")
                print(f"    → {rgb_path}")
                print(f"    → {depth_path}")

    # Verify image content
    color_np = color_buf.numpy()
    depth_np = depth_buf.numpy()
    print(f"\n[POC] === Verification ===")
    print(f"  color range: [{color_np.min()}, {color_np.max()}]")
    print(f"  depth range: [{depth_np.min():.4f}, {depth_np.max():.4f}] m")
    print(f"  color non-zero pixels: {(color_np > 0).sum()} / {color_np.size}")
    print(f"  depth valid pixels: {(depth_np > 0).sum()} / {depth_np.size}")

    # Check if cable is visible (depth variation in frame)
    for cam_idx, label in enumerate(labels):
        d = depth_np[0, cam_idx]
        valid = d[d > 0]
        if len(valid) > 0:
            std = valid.std()
            print(f"  [{label}] depth std: {std:.4f}m — {'objects visible' if std > 0.001 else 'flat (nothing visible?)'}")
        else:
            print(f"  [{label}] no valid depth pixels — PROBLEM")

    print(f"\n[POC] Frames saved to: {output_dir}/")
    print(f"[POC] Total files: {len(os.listdir(output_dir))}")


if __name__ == "__main__":
    main()
