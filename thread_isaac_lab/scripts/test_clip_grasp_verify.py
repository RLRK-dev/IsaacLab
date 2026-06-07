# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause

"""Verify clip-supported cable grasp with video.

Creates ApproachCable env (1 world), runs scripted descend→close→lift,
records video to verify physical grasp feasibility.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/test_clip_grasp_verify.py --device cuda:0
"""

import argparse
import math
import os
import subprocess
import sys
import time

import numpy as np

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)

_config_dir = os.path.join(_script_dir, "..", "configs")
sys.path.insert(0, _config_dir)


def main():
    parser = argparse.ArgumentParser(description="Verify clip-supported cable grasp")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--output-dir", type=str, default=None)
    args = parser.parse_args()

    os.environ["NEWTON_DEVICE"] = args.device

    import warp as wp
    import newton
    from newton.viewer import ViewerGL

    from task_config import (
        TABLE_HEIGHT, GRASP_Z, LIFT_Z, CLIP_BASE_HEIGHT,
        GRASP_X, WIDE_LEFT_Y, WIDE_RIGHT_Y,
        CABLE_RADIUS, EE_TO_FINGERTIP,
        FINGER_CLOSE_POS, FINGER_CLOSE_STEPS, SETTLE_STEPS,
    )
    from test_newton_clip_routing import FRANKA_NUM_JOINTS

    from newton_approach_cable_env import NewtonApproachCableEnv, EE_BODY_OFFSET

    if args.output_dir is None:
        ts = time.strftime("%Y%m%d_%H%M%S")
        args.output_dir = os.path.join(_script_dir, "..", "data", f"clip_grasp_verify_{ts}")
    os.makedirs(args.output_dir, exist_ok=True)

    cable_center_z = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS
    print("=" * 60)
    print("[VERIFY] Clip-supported cable grasp test")
    print(f"  GRASP_Z = {GRASP_Z:.3f} (fingertip = {GRASP_Z - EE_TO_FINGERTIP:.3f})")
    print(f"  Cable center Z = {cable_center_z:.3f}")
    print(f"  Output: {args.output_dir}")
    print("=" * 60)

    # Create env (1 world)
    env = NewtonApproachCableEnv(world_count=1, device=args.device)

    model = env._model
    fk_model = env._fk_model
    fk_state = env._fk_state

    # Set up headless viewer for frame capture
    W, H = 1280, 960
    viewer = ViewerGL(width=W, height=H, vsync=False, headless=True)
    viewer.set_model(model)
    viewer.camera.near = 0.01
    viewer.camera.far = 10.0

    # Camera definitions
    cameras = [
        ("front", (1.0, 0.15, 1.05), (GRASP_X, 0.15, 0.82)),
        ("overhead", (GRASP_X, 0.15, 1.50), (GRASP_X, 0.15, TABLE_HEIGHT)),
        ("right", (GRASP_X, 0.55, 0.93), (GRASP_X, 0.15, 0.82)),
    ]

    def cam_angles(pos, tgt):
        dx, dy, dz = tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]
        norm = math.sqrt(dx * dx + dy * dy + dz * dz)
        pitch = math.degrees(math.asin(max(-1.0, min(1.0, dz / norm))))
        yaw = math.degrees(math.atan2(dy, dx))
        return pitch, yaw

    # Frame storage per camera
    cam_frames = {name: [] for name, _, _ in cameras}

    sim_time = [0.0]

    def capture_all():
        state = env._state_0
        sim_time[0] += 1.0 / 30.0
        for name, pos, tgt in cameras:
            pitch, yaw = cam_angles(pos, tgt)
            viewer.set_camera(wp.vec3(*pos), pitch, yaw)
            viewer.begin_frame(sim_time[0])
            viewer.log_state(state)
            viewer.end_frame()
            frame = viewer.get_frame().numpy().copy()
            cam_frames[name].append(frame)

    def broadcast_fk():
        env._broadcast_fk_to_all_worlds()

    def physics_step_n(n=10):
        """n substeps of physics."""
        for _ in range(n):
            s0 = env._state_0
            s1 = env._state_1
            s0.clear_forces()
            model.collide(s0, env._contacts)
            env._solver.step(s0, s1, env._control, env._contacts, 1.0 / 480.0 / 10.0)
            env._state_0, env._state_1 = s1, s0

    w0 = env._bws[0]
    cable_bodies = env._cable_bodies[0]

    def diag(label):
        wp.synchronize()
        bq = env._state_0.body_q.numpy()
        ee_r_z = bq[w0 + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][2]
        ft_z = ee_r_z - EE_TO_FINGERTIP
        cz = bq[cable_bodies, 2]
        print(f"  [{label}] fingertip_z={ft_z:.4f}, cable_z_mean={np.mean(cz):.4f}, "
              f"gap={(ft_z - np.mean(cz))*1000:.1f}mm")

    # Initial capture
    capture_all()

    # --- Phase 1: Descend to GRASP_Z ---
    print("\n[P1-DESCEND] Descending to GRASP_Z...")
    grasp_x = env._settled_grasp_x
    env._ik_move_all_worlds(
        (grasp_x, WIDE_LEFT_Y, GRASP_Z),
        (grasp_x, WIDE_RIGHT_Y, GRASP_Z),
        label="DESCEND", converge_mm=3.0,
    )
    diag("POST-DESCEND")

    # Hold + capture
    for i in range(50):
        broadcast_fk()
        physics_step_n()
        if i % 10 == 0:
            capture_all()

    # --- Phase 2: Close fingers (BOTH arms) ---
    print("\n[P2-CLOSE] Closing both arms' fingers...")
    fk_jq = fk_state.joint_q.numpy()
    start_l7 = fk_jq[7]
    start_l8 = fk_jq[8]
    start_r7 = fk_jq[FRANKA_NUM_JOINTS + 7]
    start_r8 = fk_jq[FRANKA_NUM_JOINTS + 8]

    for step in range(FINGER_CLOSE_STEPS):
        t = min((step + 1) / FINGER_CLOSE_STEPS, 1.0)
        fk_jq = fk_state.joint_q.numpy()
        # Left arm fingers (joints 7, 8)
        fk_jq[7] = start_l7 + (FINGER_CLOSE_POS - start_l7) * t
        fk_jq[8] = start_l8 + (FINGER_CLOSE_POS - start_l8) * t
        # Right arm fingers (joints FRANKA_NUM_JOINTS+7, FRANKA_NUM_JOINTS+8)
        fk_jq[FRANKA_NUM_JOINTS + 7] = start_r7 + (FINGER_CLOSE_POS - start_r7) * t
        fk_jq[FRANKA_NUM_JOINTS + 8] = start_r8 + (FINGER_CLOSE_POS - start_r8) * t
        fk_state.joint_q.assign(fk_jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        broadcast_fk()
        physics_step_n()
        if step % 50 == 0:
            capture_all()
            grip_r = fk_jq[FRANKA_NUM_JOINTS + 7] + fk_jq[FRANKA_NUM_JOINTS + 8]
            grip_l = fk_jq[7] + fk_jq[8]
            wp.synchronize()
            bq = env._state_0.body_q.numpy()
            cz_mean = np.mean(bq[cable_bodies, 2])
            print(f"  step {step}/{FINGER_CLOSE_STEPS}: grip_L={grip_l*1000:.1f}mm grip_R={grip_r*1000:.1f}mm, cable_z={cz_mean:.4f}")

    diag("POST-CLOSE")

    # Settle
    print("\n[P2-SETTLE] Holding...")
    for i in range(SETTLE_STEPS):
        broadcast_fk()
        physics_step_n()
        if i % 50 == 0:
            capture_all()
    diag("POST-SETTLE")

    # --- Phase 3: Lift ---
    print("\n[P3-LIFT] Lifting to LIFT_Z...")
    env._ik_move_all_worlds(
        (grasp_x, WIDE_LEFT_Y, LIFT_Z),
        (grasp_x, WIDE_RIGHT_Y, LIFT_Z),
        label="LIFT", converge_mm=5.0,
    )

    # Hold + capture
    for i in range(100):
        broadcast_fk()
        physics_step_n()
        if i % 10 == 0:
            capture_all()

    diag("POST-LIFT")

    # Check cable lift
    wp.synchronize()
    bq = env._state_0.body_q.numpy()
    cz = bq[cable_bodies, 2]
    cable_lifted = np.mean(cz) > TABLE_HEIGHT + 0.020

    # --- Save videos ---
    print(f"\n[SAVE] Writing videos ({len(cam_frames)} cameras)...")
    video_paths = []
    for name, _, _ in cameras:
        frames = cam_frames[name]
        if not frames:
            continue
        frames_dir = os.path.join(args.output_dir, f"frames_{name}")
        os.makedirs(frames_dir, exist_ok=True)
        from PIL import Image
        for i, f in enumerate(frames):
            Image.fromarray(f).save(os.path.join(frames_dir, f"frame_{i:05d}.png"))
        video_path = os.path.join(args.output_dir, f"grasp_verify_{name}.mp4")
        cmd = [
            "ffmpeg", "-y", "-framerate", "15",
            "-i", os.path.join(frames_dir, "frame_%05d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23",
            video_path,
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=60)
            video_paths.append(video_path)
            import shutil
            shutil.rmtree(frames_dir, ignore_errors=True)
        except Exception as e:
            print(f"  ffmpeg failed for {name}: {e}")
            video_paths.append(frames_dir)

    for p in video_paths:
        print(f"  {p}")

    # --- Verdict ---
    print("\n" + "=" * 60)
    if cable_lifted:
        print("[VERDICT] PASS — Cable lifted >20mm above table")
    else:
        print(f"[VERDICT] FAIL — Cable Z mean={np.mean(cz):.4f} (need >{TABLE_HEIGHT + 0.020:.3f})")
    print("=" * 60)

    if hasattr(env, "close"):
        env.close()


if __name__ == "__main__":
    main()
