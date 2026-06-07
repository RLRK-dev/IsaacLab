# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Dry-run IK verification for the full 43-step cable routing sequence.

Loads waypoints from full_43step.json, verifies IK reachability,
then renders per-camera MP4 videos with interpolated motion.

No cable, no physics -- pure FK + IK verification.

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/dry_run_43step.py
    # With video:
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/dry_run_43step.py --video
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
    add_clip_visual, TABLE_HEIGHT,
)

_config_dir = os.environ.get(
    "THREAD_CONFIG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs"),
)
sys.path.insert(0, _config_dir)
from task_config import CLIP_POSITIONS  # noqa: E402

DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")
IK_ERROR_THRESHOLD_MM = 5.0

# Video settings
VIDEO_FPS = 30
VIDEO_CAM_W = 1280
VIDEO_CAM_H = 960
INTERP_STEPS = 20
HOLD_FRAMES = 5

CT = (0.35, 0.0, 0.82)
CAMERAS = [
    ("overhead",    (0.35,  0.00, 1.50), (0.35, 0.00, 0.80)),
    ("front",       (1.00,  0.00, 1.05), (0.30, 0.00, 0.82)),
    ("diag_upper",  (0.65, -0.40, 1.00), CT),
    ("left",        (0.35, -0.65, 0.93), CT),
    ("right",       (0.35,  0.65, 0.93), CT),
    ("clip_close",  (0.50,  0.00, 0.83), CT),
]

WAYPOINT_JSON = os.path.join(_SCRIPT_DIR, "..", "data", "waypoints", "full_43step.json")
OUTPUT_DIR = os.path.join(_SCRIPT_DIR, "..", "data", "waypoints")


def load_steps(json_path):
    """Load waypoint steps from JSON file."""
    with open(json_path) as f:
        data = json.load(f)
    steps = data["steps"]
    assert len(steps) == 43, f"Expected 43 steps, got {len(steps)}"
    return steps


def build_fk_model_with_scene(device):
    """Build FK model augmented with table and clip visuals for rendering."""
    from newton_routing_utils import FRANKA_URDF, ROBOT_LEFT_BASE, ROBOT_RIGHT_BASE

    builder = newton.ModelBuilder(gravity=-9.81)
    cfg = newton.ModelBuilder.ShapeConfig()
    cfg.gap = 0.0
    cfg.density = 0.0
    builder.default_shape_cfg = cfg

    # Table (static, body=-1)
    table_half = (0.40, 0.45, 0.005)
    table_center_y = np.mean([cy for _, cy in CLIP_POSITIONS])
    table_xf = wp.transform(
        (0.3, table_center_y, TABLE_HEIGHT - table_half[2]), wp.quat_identity())
    builder.add_shape_box(
        body=-1, hx=table_half[0], hy=table_half[1], hz=table_half[2],
        xform=table_xf)

    # 5 routing clips (static, body=-1)
    for cx, cy in CLIP_POSITIONS:
        add_clip_visual(builder, cx, cy, TABLE_HEIGHT)

    # 3 resting clips — cable support stands, 20cm behind nearest routing clip (X=0.35)
    REST_CLIPS = [
        (0.15,  0.20),   # S1
        (0.15,  0.00),   # S2
        (0.15, -0.20),   # S3
    ]
    for cx, cy in REST_CLIPS:
        add_clip_visual(builder, cx, cy, TABLE_HEIGHT)

    # Arms (articulated)
    builder.add_urdf(
        FRANKA_URDF,
        xform=wp.transform(ROBOT_LEFT_BASE, wp.quat_identity()),
        floating=False, enable_self_collisions=False, collapse_fixed_joints=True,
    )
    builder.add_urdf(
        FRANKA_URDF,
        xform=wp.transform(ROBOT_RIGHT_BASE, wp.quat_identity()),
        floating=False, enable_self_collisions=False, collapse_fixed_joints=True,
    )

    builder.color()
    model = builder.finalize(device=device, requires_grad=True)
    print(f"  [FK+SCENE] Model: bodies={model.body_count}, "
          f"joints={model.joint_count}, shapes={model.shape_count}")
    return model


def _cam_angles(pos, tgt):
    dx, dy, dz = tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, dz / norm))))
    yaw = math.degrees(math.atan2(dy, dx))
    return pitch, yaw


def render_video(scene_model, waypoint_jqs, output_dir, steps=None, fk_model=None, fk_state=None):
    """Render interpolated trajectory as per-camera MP4 videos.

    Uses Cartesian-space interpolation with per-frame IK solving when step
    data and FK model are provided, producing straight-line EE paths.
    Falls back to joint-space interpolation otherwise.

    Args:
        scene_model: Newton model with table + clips + arms for rendering.
        waypoint_jqs: list of joint angle arrays from IK solving.
        output_dir: directory for output videos.
        steps: waypoint step dicts with target_l/target_r/finger positions.
        fk_model: FK model for IK solving (needed for Cartesian interpolation).
        fk_state: FK state for IK solving (needed for Cartesian interpolation).
    """
    cartesian_mode = steps is not None and fk_model is not None and fk_state is not None
    n_wp = len(waypoint_jqs)
    total_frames = 15 + (n_wp - 1) * (INTERP_STEPS + HOLD_FRAMES) + 15
    mode_str = "Cartesian" if cartesian_mode else "joint-space"
    print(f"\n[dry-run] Rendering video ({n_wp} waypoints, ~{total_frames} frames, {mode_str} interp) ...")

    viewer = ViewerGL(width=VIDEO_CAM_W, height=VIDEO_CAM_H,
                      vsync=False, headless=True)
    viewer.set_model(scene_model)
    viewer.camera.near = 0.01
    viewer.camera.far = 10.0

    cam_params = []
    cam_frames = {}
    for name, pos, tgt in CAMERAS:
        pitch, yaw = _cam_angles(pos, tgt)
        cam_params.append((name, wp.vec3(*pos), pitch, yaw))
        cam_frames[name] = []

    scene_state = scene_model.state()
    sim_time = 0.0
    dt = 1.0 / VIDEO_FPS

    def capture_frame():
        nonlocal sim_time
        sim_time += dt
        for name, pos, pitch, yaw in cam_params:
            viewer.set_camera(pos, pitch, yaw)
            viewer.begin_frame(sim_time)
            viewer.log_state(scene_state)
            viewer.end_frame()
            frame = viewer.get_frame().numpy().copy()
            cam_frames[name].append(frame)

    def set_jq(jq_array):
        scene_state.joint_q.assign(jq_array)
        newton.eval_fk(scene_model, scene_state.joint_q, scene_state.joint_qd, scene_state)

    # Hold first waypoint
    set_jq(waypoint_jqs[0])
    for _ in range(15):
        capture_frame()

    # Interpolate between waypoints
    for i in range(n_wp - 1):
        if cartesian_mode:
            # Cartesian-space interpolation: lerp EE targets, solve IK per frame
            tl_a = np.array(steps[i]["target_l"], dtype=np.float32)
            tl_b = np.array(steps[i + 1]["target_l"], dtype=np.float32)
            tr_a = np.array(steps[i]["target_r"], dtype=np.float32)
            tr_b = np.array(steps[i + 1]["target_r"], dtype=np.float32)
            fl_a = steps[i]["left_finger"]
            fl_b = steps[i + 1]["left_finger"]
            fr_a = steps[i]["right_finger"]
            fr_b = steps[i + 1]["right_finger"]
            for s in range(INTERP_STEPS):
                t = (s + 1) / INTERP_STEPS
                tl_interp = tuple(tl_a + (tl_b - tl_a) * t)
                tr_interp = tuple(tr_a + (tr_b - tr_a) * t)
                jq, _ = solve_ik_dual(fk_model, fk_state, tl_interp, tr_interp, DEVICE)
                # jq is numpy array with IK solution; fk_state.joint_q is NOT updated by solve_ik_dual
                jq_np = jq.copy()
                jq_np[7] = fl_a + (fl_b - fl_a) * t
                jq_np[8] = jq_np[7]
                jq_np[FRANKA_NUM_JOINTS + 7] = fr_a + (fr_b - fr_a) * t
                jq_np[FRANKA_NUM_JOINTS + 8] = jq_np[FRANKA_NUM_JOINTS + 7]
                # Update fk_state for next IK seed
                fk_state.joint_q.assign(jq_np)
                newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
                set_jq(jq_np)
                capture_frame()
        else:
            # Fallback: joint-space interpolation
            jq_a = waypoint_jqs[i]
            jq_b = waypoint_jqs[i + 1]
            for s in range(INTERP_STEPS):
                t = (s + 1) / INTERP_STEPS
                jq_interp = jq_a + (jq_b - jq_a) * t
                set_jq(jq_interp)
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

        video_path = os.path.join(output_dir, f"dryrun_43step_{name}.mp4")
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

    print(f"[dry-run] 43-step motion sequence verification (device={DEVICE})")
    print(f"  Waypoint source: {WAYPOINT_JSON}")

    fk_model = build_fk_model(device=DEVICE)
    fk_state = init_fk_state(fk_model)

    steps = load_steps(WAYPOINT_JSON)

    # Verify IK reachability
    waypoint_jqs = []
    all_pass = True
    n_fail = 0
    for wp_def in steps:
        target_l = tuple(wp_def["target_l"])
        target_r = tuple(wp_def["target_r"])

        jq, cost = solve_ik_dual(fk_model, fk_state, target_l, target_r, DEVICE)
        err_l, err_r = eval_ik_errors(fk_model, fk_state, jq, target_l, target_r)

        # Set finger positions
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

    # Save updated JSON with IK results
    n_pass = sum(1 for s in steps if s["status"] == "PASS")
    with open(WAYPOINT_JSON) as f:
        output = json.load(f)
    output["steps"] = steps
    output["summary"] = {"total": len(steps), "pass": n_pass, "fail": n_fail}

    with open(WAYPOINT_JSON, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n[dry-run] Summary: {n_pass}/{len(steps)} PASS, {n_fail} FAIL")
    print(f"[dry-run] Updated: {WAYPOINT_JSON}")
    if not all_pass:
        print("[dry-run] WARNING: Some waypoints FAILED IK verification!")

    if do_video:
        scene_model = build_fk_model_with_scene(device=DEVICE)
        video_dir = os.path.join(OUTPUT_DIR, "..", "videos", "dryrun_43step")
        paths = render_video(scene_model, waypoint_jqs, video_dir,
                             steps=steps, fk_model=fk_model, fk_state=fk_state)
        # Copy to ~/Downloads
        dl_dir = os.path.expanduser("~/Downloads")
        os.makedirs(dl_dir, exist_ok=True)
        import shutil
        for p in paths:
            if os.path.isfile(p):
                dst = os.path.join(dl_dir, os.path.basename(p))
                shutil.copy2(p, dst)
                print(f"  Copied -> {dst}")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
