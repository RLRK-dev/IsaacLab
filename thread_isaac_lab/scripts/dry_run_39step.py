# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Dry-run IK verification for the full 39-step cable routing sequence.

Generates all 39 waypoints from the motion sequence design
(RL-Routing-Design.md Section 2), verifies IK reachability for each,
then renders per-camera MP4 videos with interpolated motion.

No cable, no physics — pure FK + IK verification.

Reuses:
  - newton_routing_utils: solve_ik_dual, eval_ik_errors, set_finger_positions,
                          build_fk_model, init_fk_state
  - test_newton_clip_routing: VideoRecorder (adapted), 6-camera layout

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/dry_run_39step.py
    # With video:
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/dry_run_39step.py --video
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
    solve_ik_dual, eval_ik_errors,
    set_finger_positions,
)

_config_dir = os.environ.get(
    "THREAD_CONFIG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs"),
)
sys.path.insert(0, _config_dir)
from task_config import (  # noqa: E402
    TABLE_HEIGHT, APPROACH_Z, GRASP_Z, LIFT_Z, PUSH_Z,
    GRASP_X, CLIP_POSITIONS, GRIP_HALF_SPAN,
    FINGER_OPEN_POS, FINGER_HALF_OPEN_POS, FINGER_CLOSE_POS,
)

DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")
IK_ERROR_THRESHOLD_MM = 5.0

# Finger state aliases
OPEN = FINGER_OPEN_POS
HALF = FINGER_HALF_OPEN_POS
CLOSE = FINGER_CLOSE_POS

# Heights (EE = panda_hand body6 frame)
Z_UP = LIFT_Z       # Upper position (fingertip ~100mm above table)
Z_DOWN = GRASP_Z    # Table level (fingertip at table surface)

# Origin (home) position
ORIGIN_X = 0.15
ORIGIN_Y = 0.0

# GRIP_HALF_SPAN imported from task_config (0.060m = 60mm)

CABLE_X = GRASP_X

# Video settings (matching test_newton_clip_routing.py)
VIDEO_FPS = 30
VIDEO_CAM_W = 1280
VIDEO_CAM_H = 960
INTERP_STEPS = 20
HOLD_FRAMES = 5

# 6-camera layout from test_newton_clip_routing.py, target shifted to 5-clip center
# Original target: (0.35, -0.05, 0.82) → new: (0.35, 0.0, 0.82)
CT = (0.35, 0.0, 0.82)  # camera target (5-clip centroid)
CAMERAS = [
    ("overhead",    (0.35,  0.00, 1.50), (0.35, 0.00, 0.80)),
    ("front",       (1.00,  0.00, 1.05), (0.30, 0.00, 0.82)),
    ("diag_upper",  (0.65, -0.40, 1.00), CT),
    ("left",        (0.35, -0.65, 0.93), CT),
    ("right",       (0.35,  0.65, 0.93), CT),
    ("clip_close",  (0.50,  0.00, 0.83), CT),
]

OUTPUT_DIR = os.path.join(_SCRIPT_DIR, "..", "data", "waypoints")


def _cam_angles(pos, tgt):
    """Compute (pitch_deg, yaw_deg) for ViewerGL.set_camera."""
    dx, dy, dz = tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, dz / norm))))
    yaw = math.degrees(math.atan2(dy, dx))
    return pitch, yaw


def build_39_steps():
    """Build 39-step waypoint sequence per RL-Routing-Design.md Section 2."""
    steps = []

    def add(step_num, phase, desc, lx, ly, lz, rx, ry, rz, lf, rf):
        steps.append({
            "step": step_num,
            "phase": phase,
            "desc": desc,
            "target_l": [lx, ly, lz],
            "target_r": [rx, ry, rz],
            "left_finger": lf,
            "right_finger": rf,
        })

    # Cable grab Y: symmetric around C1
    cable_grab_y_l = CLIP_POSITIONS[0][1] - GRIP_HALF_SPAN
    cable_grab_y_r = CLIP_POSITIONS[0][1] + GRIP_HALF_SPAN

    # Phase A: Initial grasp (STEP 1-5)
    add(1, "A", "Home position",
        ORIGIN_X, -0.15, Z_UP, ORIGIN_X, +0.15, Z_UP, OPEN, OPEN)
    add(2, "A", "Above cable",
        CABLE_X, cable_grab_y_l, Z_UP, CABLE_X, cable_grab_y_r, Z_UP, OPEN, OPEN)
    add(3, "A", "Descend to cable",
        CABLE_X, cable_grab_y_l, Z_DOWN, CABLE_X, cable_grab_y_r, Z_DOWN, OPEN, OPEN)
    add(4, "A", "Clamp cable",
        CABLE_X, cable_grab_y_l, Z_DOWN, CABLE_X, cable_grab_y_r, Z_DOWN, CLOSE, CLOSE)
    add(5, "A", "Lift cable",
        CABLE_X, cable_grab_y_l, Z_UP, CABLE_X, cable_grab_y_r, Z_UP, CLOSE, CLOSE)

    # Phase B: C1 routing (STEP 6-10)
    c1x, c1y = CLIP_POSITIONS[0]
    add(6, "B", "Transport above C1",
        c1x, c1y - GRIP_HALF_SPAN, Z_UP, c1x, c1y + GRIP_HALF_SPAN, Z_UP, CLOSE, CLOSE)
    add(7, "B", "Push into C1",
        c1x, c1y - GRIP_HALF_SPAN, Z_DOWN, c1x, c1y + GRIP_HALF_SPAN, Z_DOWN, CLOSE, CLOSE)
    add(8, "B", "Half-release at C1",
        c1x, c1y - GRIP_HALF_SPAN, Z_DOWN, c1x, c1y + GRIP_HALF_SPAN, Z_DOWN, HALF, OPEN)
    add(9, "B", "C1 clamp (hold)",
        c1x, c1y - GRIP_HALF_SPAN, Z_DOWN, c1x, c1y + GRIP_HALF_SPAN, Z_DOWN, HALF, OPEN)
    add(10, "B", "Rise from C1",
        c1x, c1y - GRIP_HALF_SPAN, Z_UP, c1x, c1y + GRIP_HALF_SPAN, Z_UP, HALF, OPEN)

    # Phase C+D: Transition + routing for C2-C5 (7 steps x 4)
    step_num = 11
    for ci in range(1, 5):
        cx, cy = CLIP_POSITIONS[ci]
        prev_cx, prev_cy = CLIP_POSITIONS[ci - 1]
        clip_name = f"C{ci + 1}"
        regrab_y = (prev_cy + cy) / 2.0

        add(step_num, "C+D", f"Above {clip_name} area",
            cx, cy - GRIP_HALF_SPAN, Z_UP, cx, cy + GRIP_HALF_SPAN, Z_UP, HALF, OPEN)
        add(step_num + 1, "C+D", f"R-hand to cable for {clip_name}",
            cx, cy - GRIP_HALF_SPAN, Z_UP, cx, regrab_y, Z_DOWN, HALF, OPEN)
        add(step_num + 2, "C+D", f"Both clamp for {clip_name}",
            cx, cy - GRIP_HALF_SPAN, Z_UP, cx, regrab_y, Z_DOWN, CLOSE, CLOSE)
        add(step_num + 3, "C+D", f"Push into {clip_name}",
            cx, cy - GRIP_HALF_SPAN, Z_DOWN, cx, cy + GRIP_HALF_SPAN, Z_DOWN, CLOSE, CLOSE)
        add(step_num + 4, "C+D", f"{clip_name} clamp",
            cx, cy - GRIP_HALF_SPAN, Z_DOWN, cx, cy + GRIP_HALF_SPAN, Z_DOWN, CLOSE, CLOSE)
        add(step_num + 5, "C+D", f"Release at {clip_name}",
            cx, cy - GRIP_HALF_SPAN, Z_DOWN, cx, cy + GRIP_HALF_SPAN, Z_DOWN, HALF, OPEN)
        add(step_num + 6, "C+D", f"Rise from {clip_name}",
            cx, cy - GRIP_HALF_SPAN, Z_UP, cx, cy + GRIP_HALF_SPAN, Z_UP, HALF, OPEN)
        step_num += 7

    # Final: Return to origin (STEP 39)
    add(step_num, "E", "Return to home",
        ORIGIN_X, -0.15, Z_UP, ORIGIN_X, +0.15, Z_UP, OPEN, OPEN)

    assert len(steps) == 39, f"Expected 39 steps, got {len(steps)}"
    return steps


def render_video(fk_model, waypoint_jqs, output_dir):
    """Render interpolated trajectory as per-camera MP4 videos using 6-camera layout."""
    n_wp = len(waypoint_jqs)
    total_frames = 15 + (n_wp - 1) * (INTERP_STEPS + HOLD_FRAMES) + 15
    print(f"\n[dry-run] Rendering video ({n_wp} waypoints, ~{total_frames} frames) ...")

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

    # Hold first waypoint
    fk_state.joint_q.assign(waypoint_jqs[0])
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
    for _ in range(15):
        capture_frame()

    # Interpolate between waypoints
    for i in range(n_wp - 1):
        jq_a = waypoint_jqs[i]
        jq_b = waypoint_jqs[i + 1]
        for s in range(INTERP_STEPS):
            t = (s + 1) / INTERP_STEPS
            jq_interp = jq_a + (jq_b - jq_a) * t
            fk_state.joint_q.assign(jq_interp)
            newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
            capture_frame()
        for _ in range(HOLD_FRAMES):
            capture_frame()

    # Hold last waypoint
    for _ in range(15):
        capture_frame()

    # Encode per-camera MP4
    os.makedirs(output_dir, exist_ok=True)
    video_paths = []
    for name, _, _, _ in cam_params:
        frames = cam_frames[name]
        if not frames:
            continue
        frames_dir = os.path.join(output_dir, f"frames_{name}")
        os.makedirs(frames_dir, exist_ok=True)
        from PIL import Image
        for fi, f in enumerate(frames):
            Image.fromarray(f).save(os.path.join(frames_dir, f"frame_{fi:05d}.png"))

        video_path = os.path.join(output_dir, f"dryrun_39step_{name}.mp4")
        cmd = [
            "ffmpeg", "-y", "-framerate", str(VIDEO_FPS),
            "-i", os.path.join(frames_dir, "frame_%05d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "23", video_path,
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=120)
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

    print(f"[dry-run] 39-step motion sequence verification (device={DEVICE})")
    print(f"  Clips: {CLIP_POSITIONS}")

    fk_model = build_fk_model(device=DEVICE)
    fk_state = init_fk_state(fk_model)

    steps = build_39_steps()

    # Verify IK reachability using newton_routing_utils.solve_ik_dual
    waypoint_jqs = []
    all_pass = True
    n_fail = 0
    for wp_def in steps:
        target_l = tuple(wp_def["target_l"])
        target_r = tuple(wp_def["target_r"])

        jq, cost = solve_ik_dual(fk_model, fk_state, target_l, target_r, DEVICE)
        err_l, err_r = eval_ik_errors(fk_model, fk_state, jq, target_l, target_r)

        # Set finger positions via newton_routing_utils pattern
        fk_jq = fk_state.joint_q.numpy()
        fk_jq[7] = wp_def["left_finger"]
        fk_jq[8] = wp_def["left_finger"]
        fk_jq[FRANKA_NUM_JOINTS + 7] = wp_def["right_finger"]
        fk_jq[FRANKA_NUM_JOINTS + 8] = wp_def["right_finger"]
        fk_state.joint_q.assign(fk_jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        waypoint_jqs.append(fk_jq.copy())

        status = "PASS" if max(err_l, err_r) < IK_ERROR_THRESHOLD_MM else "FAIL"
        if status == "FAIL":
            all_pass = False
            n_fail += 1

        wp_def["err_l_mm"] = round(float(err_l), 2)
        wp_def["err_r_mm"] = round(float(err_r), 2)
        wp_def["status"] = status

        flag = " *** FAIL ***" if status == "FAIL" else ""
        print(f"  Step {wp_def['step']:2d} [{wp_def['phase']:4s}] {wp_def['desc']:<35s} "
              f"L={err_l:6.2f}mm R={err_r:6.2f}mm {status}{flag}")

    # Output JSON
    n_pass = sum(1 for s in steps if s["status"] == "PASS")
    output = {
        "version": 1,
        "scope": "full_39step",
        "clip_positions": [{"clip": f"C{i+1}", "x": cx, "y": cy}
                           for i, (cx, cy) in enumerate(CLIP_POSITIONS)],
        "steps": steps,
        "summary": {"total": len(steps), "pass": n_pass, "fail": n_fail},
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "full_39step.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n[dry-run] Summary: {n_pass}/{len(steps)} PASS, {n_fail} FAIL")
    print(f"[dry-run] Output: {output_path}")
    if not all_pass:
        print("[dry-run] WARNING: Some waypoints FAILED IK verification!")

    if do_video:
        video_dir = os.path.join(OUTPUT_DIR, "..", "videos", "dryrun_39step")
        render_video(fk_model, waypoint_jqs, video_dir)

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
