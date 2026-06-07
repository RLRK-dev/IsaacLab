# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Dry-run IK verification for ApproachCable demo trajectory.

Verifies IK reachability for the 4-step ApproachCable sequence
(P0 approach → descend → close → lift) and outputs verified
waypoints as JSON for wet-run demo collection.

No cable, no physics — pure FK + IK verification.

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/dry_run_approach_cable.py
    # With video:
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/dry_run_approach_cable.py --video
    # Specify GPU:
    NEWTON_DEVICE=cuda:1 OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/dry_run_approach_cable.py --video
"""

import json
import math
import os
import subprocess
import sys

import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import warp as wp  # noqa: E402
import newton  # noqa: E402
from newton.viewer import ViewerGL  # noqa: E402

from newton_routing_utils import (  # noqa: E402
    FRANKA_NUM_JOINTS, EE_BODY_OFFSET,
    build_fk_model, init_fk_state,
)

_config_dir = os.environ.get(
    "THREAD_CONFIG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs"),
)
sys.path.insert(0, _config_dir)
from task_config import (  # noqa: E402
    TABLE_HEIGHT, APPROACH_Z, GRASP_Z, LIFT_Z,
    GRASP_X, WIDE_LEFT_Y, WIDE_RIGHT_Y,
    CABLE_RADIUS, EE_TO_FINGERTIP,
    FINGER_OPEN_POS, FINGER_CLOSE_POS, FINGER_STEP_SIZE,
)

DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")
IK_ITERATIONS = 100
IK_STEP_SIZE = 1.0
IK_ERROR_THRESHOLD_MM = 5.0

# P0 EE height: fingertip 10mm above cable surface
P0_EE_Z = TABLE_HEIGHT + CABLE_RADIUS + 0.010 + EE_TO_FINGERTIP

# Output path
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "waypoints")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "grasp_cable_c1.json")

# Video settings
VIDEO_CAM_W = 1280
VIDEO_CAM_H = 960
VIDEO_FPS = 30
INTERP_STEPS = 30  # frames to interpolate between waypoints

# Camera definitions matching test_newton_clip_routing.py
CAMERAS = [
    ("overhead",    (0.35, -0.05, 1.50), (0.35, -0.05, 0.80)),
    ("front",       (1.00, -0.05, 1.05), (0.30, -0.05, 0.82)),
    ("left",        (0.35, -0.65, 0.93), (0.35, -0.05, 0.82)),
    ("right",       (0.35,  0.55, 0.93), (0.35, -0.05, 0.82)),
]


def _cam_angles(pos, tgt):
    """Compute (pitch_deg, yaw_deg) for ViewerGL.set_camera."""
    dx, dy, dz = tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, dz / norm))))
    yaw = math.degrees(math.atan2(dy, dx))
    return pitch, yaw


def solve_ik_dual(fk_model, fk_state, target_left, target_right, device):
    """Solve IK for dual-arm, return joint config and per-arm errors [mm]."""
    from newton.ik import IKSolver, IKObjectivePosition, IKObjectiveRotation, IKObjectiveJointLimit

    left_ee = EE_BODY_OFFSET
    right_ee = FRANKA_NUM_JOINTS + EE_BODY_OFFSET

    _cos_pi8 = float(np.cos(np.pi / 8))
    _sin_pi8 = float(np.sin(np.pi / 8))
    target_rot = wp.array(
        [wp.vec4(_cos_pi8, _sin_pi8, 0.0, 0.0)],
        dtype=wp.vec4, device=device,
    )

    objectives = [
        IKObjectivePosition(link_index=left_ee, link_offset=wp.vec3(0, 0, 0),
                            target_positions=wp.array([target_left], dtype=wp.vec3, device=device), weight=1.0),
        IKObjectivePosition(link_index=right_ee, link_offset=wp.vec3(0, 0, 0),
                            target_positions=wp.array([target_right], dtype=wp.vec3, device=device), weight=1.0),
        IKObjectiveRotation(link_index=left_ee, link_offset_rotation=wp.quat_identity(),
                            target_rotations=target_rot, weight=0.5),
        IKObjectiveRotation(link_index=right_ee, link_offset_rotation=wp.quat_identity(),
                            target_rotations=target_rot, weight=0.5),
        IKObjectiveJointLimit(joint_limit_lower=fk_model.joint_limit_lower,
                              joint_limit_upper=fk_model.joint_limit_upper, weight=10.0),
    ]
    ik_solver = IKSolver(fk_model, n_problems=1, objectives=objectives)

    jq_in = wp.array(fk_state.joint_q.numpy().reshape(1, -1), dtype=float, device=device)
    jq_out = wp.zeros((1, fk_model.joint_coord_count), dtype=float, device=device)
    ik_solver.step(jq_in, jq_out, iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)

    jq = jq_out.numpy()[0]

    # Update FK state for next solve
    fk_state.joint_q.assign(jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    # Compute EE errors
    body_q = fk_state.body_q.numpy()
    l_pos = body_q[left_ee][:3]
    r_pos = body_q[right_ee][:3]
    err_l = np.linalg.norm(l_pos - np.array(target_left)) * 1000.0
    err_r = np.linalg.norm(r_pos - np.array(target_right)) * 1000.0

    return jq, err_l, err_r


def render_video(fk_model, waypoint_jqs, output_dir):
    """Render interpolated waypoint trajectory as per-camera MP4 videos."""
    print(f"\n[dry-run] Rendering video ({len(waypoint_jqs)} waypoints, "
          f"{INTERP_STEPS} interp steps each) ...")

    viewer = ViewerGL(width=VIDEO_CAM_W, height=VIDEO_CAM_H,
                      vsync=False, headless=True)
    viewer.set_model(fk_model)
    viewer.camera.near = 0.01
    viewer.camera.far = 10.0

    cam_params = []
    cam_frames = {}
    for name, pos, tgt in CAMERAS:
        pitch, yaw = _cam_angles(pos, tgt)
        cam_params.append((name, wp.vec3(*pos), pitch, yaw))
        cam_frames[name] = []

    fk_state = init_fk_state(fk_model)
    sim_time = 0.0
    dt = 1.0 / VIDEO_FPS

    def capture_frame():
        nonlocal sim_time
        sim_time += dt
        for name, pos, pitch, yaw in cam_params:
            viewer.set_camera(pos, pitch, yaw)
            viewer.begin_frame(sim_time)
            viewer.log_state(fk_state)
            viewer.end_frame()
            frame = viewer.get_frame().numpy().copy()
            cam_frames[name].append(frame)

    # Hold first waypoint for 15 frames
    fk_state.joint_q.assign(waypoint_jqs[0])
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
    for _ in range(15):
        capture_frame()

    # Interpolate between consecutive waypoints
    for i in range(len(waypoint_jqs) - 1):
        jq_a = waypoint_jqs[i]
        jq_b = waypoint_jqs[i + 1]
        for s in range(INTERP_STEPS):
            t = (s + 1) / INTERP_STEPS
            jq_interp = jq_a + (jq_b - jq_a) * t
            fk_state.joint_q.assign(jq_interp)
            newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
            capture_frame()
        # Hold at waypoint for 10 frames
        for _ in range(10):
            capture_frame()

    # Hold last waypoint for 15 frames
    for _ in range(15):
        capture_frame()

    # Encode to MP4
    os.makedirs(output_dir, exist_ok=True)
    video_paths = []
    for name, _, _, _ in cam_params:
        frames = cam_frames[name]
        if not frames:
            continue
        frames_dir = os.path.join(output_dir, f"frames_{name}")
        os.makedirs(frames_dir, exist_ok=True)
        try:
            from PIL import Image
        except ImportError:
            print("  [VIDEO] PIL not available, saving raw frames only")
            for fi, f in enumerate(frames):
                np.save(os.path.join(frames_dir, f"frame_{fi:05d}.npy"), f)
            continue

        for fi, f in enumerate(frames):
            Image.fromarray(f).save(
                os.path.join(frames_dir, f"frame_{fi:05d}.png"))

        video_path = os.path.join(output_dir, f"dryrun_{name}.mp4")
        cmd = [
            "ffmpeg", "-y", "-framerate", str(VIDEO_FPS),
            "-i", os.path.join(frames_dir, "frame_%05d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "23", video_path,
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=60)
            video_paths.append(video_path)
            import shutil
            shutil.rmtree(frames_dir, ignore_errors=True)
        except Exception as e:
            print(f"  [VIDEO] ffmpeg failed for {name}: {e}")
            video_paths.append(frames_dir)

    n_frames = len(next(iter(cam_frames.values()), []))
    print(f"  [VIDEO] {len(video_paths)} cameras, {n_frames} frames each")
    for p in video_paths:
        print(f"    {p}")
    return video_paths


def main():
    do_video = "--video" in sys.argv

    wp.init()
    wp.set_device(DEVICE)

    print(f"[dry-run] ApproachCable waypoint verification (device={DEVICE})")
    print(f"  GRASP_X={GRASP_X}, WIDE_LEFT_Y={WIDE_LEFT_Y}, WIDE_RIGHT_Y={WIDE_RIGHT_Y}")
    print(f"  P0_EE_Z={P0_EE_Z:.4f}, GRASP_Z={GRASP_Z}, LIFT_Z={LIFT_Z}")

    fk_model = build_fk_model(device=DEVICE)
    fk_state = init_fk_state(fk_model)

    # Define waypoints for ApproachCable demo trajectory
    # Left arm holds position at P0 throughout. Right arm moves.
    left_hold = (GRASP_X, WIDE_LEFT_Y, P0_EE_Z)

    waypoints = [
        {
            "step": 1,
            "phase": "P0_approach",
            "desc": "Both arms at approach height, fingers open",
            "target_l": list(left_hold),
            "target_r": [GRASP_X, WIDE_RIGHT_Y, P0_EE_Z],
            "finger_cmd": 0.0,
            "finger_pos": FINGER_OPEN_POS,
        },
        {
            "step": 2,
            "phase": "descend",
            "desc": "Right arm descend to cable (fingertip at table)",
            "target_l": list(left_hold),
            "target_r": [GRASP_X, WIDE_RIGHT_Y, GRASP_Z],
            "finger_cmd": 0.0,
            "finger_pos": FINGER_OPEN_POS,
        },
        {
            "step": 3,
            "phase": "close",
            "desc": "Close right fingers around cable",
            "target_l": list(left_hold),
            "target_r": [GRASP_X, WIDE_RIGHT_Y, GRASP_Z],
            "finger_cmd": 1.0,
            "finger_pos": FINGER_CLOSE_POS,
        },
        {
            "step": 4,
            "phase": "lift",
            "desc": "Lift cable to LIFT_Z",
            "target_l": list(left_hold),
            "target_r": [GRASP_X, WIDE_RIGHT_Y, LIFT_Z],
            "finger_cmd": 1.0,
            "finger_pos": FINGER_CLOSE_POS,
        },
    ]

    # Verify IK reachability for each waypoint
    results = []
    waypoint_jqs = []
    all_pass = True
    for wp_def in waypoints:
        target_l = tuple(wp_def["target_l"])
        target_r = tuple(wp_def["target_r"])

        jq, err_l, err_r = solve_ik_dual(fk_model, fk_state, target_l, target_r, DEVICE)

        # Set finger positions in joint config
        jq_with_fingers = jq.copy()
        fp = wp_def["finger_pos"]
        jq_with_fingers[7] = fp   # left finger 1
        jq_with_fingers[8] = fp   # left finger 2
        jq_with_fingers[FRANKA_NUM_JOINTS + 7] = fp  # right finger 1
        jq_with_fingers[FRANKA_NUM_JOINTS + 8] = fp  # right finger 2
        waypoint_jqs.append(jq_with_fingers)

        status = "PASS" if max(err_l, err_r) < IK_ERROR_THRESHOLD_MM else "FAIL"
        if status == "FAIL":
            all_pass = False

        wp_def["err_l_mm"] = round(float(err_l), 2)
        wp_def["err_r_mm"] = round(float(err_r), 2)
        wp_def["status"] = status
        results.append(wp_def)

        print(f"  Step {wp_def['step']} [{wp_def['phase']}]: "
              f"err_L={err_l:.2f}mm err_R={err_r:.2f}mm → {status}")

    # Build output JSON
    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")

    output = {
        "version": 2,
        "scope": "approach_cable",
        "layout": {
            "grasp_x": GRASP_X,
            "wide_left_y": WIDE_LEFT_Y,
            "wide_right_y": WIDE_RIGHT_Y,
            "table_height": TABLE_HEIGHT,
        },
        "finger_config": {
            "open_pos": FINGER_OPEN_POS,
            "close_pos": FINGER_CLOSE_POS,
            "step_size": FINGER_STEP_SIZE,
        },
        "steps": results,
        "summary": {
            "total": len(results),
            "pass": n_pass,
            "fail": n_fail,
        },
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n[dry-run] Summary: {n_pass}/{len(results)} PASS")
    print(f"[dry-run] Output: {OUTPUT_PATH}")
    if not all_pass:
        print("[dry-run] WARNING: Some waypoints FAILED IK verification!")
        sys.exit(1)

    # Video rendering
    if do_video:
        video_dir = os.path.join(OUTPUT_DIR, "..", "videos", "dryrun_approach_cable")
        render_video(fk_model, waypoint_jqs, video_dir)


if __name__ == "__main__":
    main()
