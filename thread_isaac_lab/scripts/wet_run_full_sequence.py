#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Wet-run: Execute full 43-step routing sequence in Newton VBD with video.

Reads verified waypoints from dry-run JSON, executes them with Newton VBD
cable physics, and records per-camera MP4 videos.

Usage:
    source ~/env_isaaclab6/bin/activate
    DISPLAY=:1 python thread_isaac_lab/scripts/wet_run_full_sequence.py \
        --waypoints thread_isaac_lab/data/waypoints/full_43step.json \
        --output-dir data/wet_run_43step \
        --device cuda:0
"""

import argparse
import json
import os
import sys
import time

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import numpy as np
import warp as wp
import newton
from newton.solvers import SolverVBD

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "..", "configs"))
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "..", "envs"))

# Reuse scene building functions from clip routing test
from test_newton_clip_routing import (
    build_fk_model,
    add_kinematic_arm,
    add_cable_rod,
    update_kinematic_bodies,
    physics_step,
    VideoRecorder,
    FRANKA_NUM_JOINTS,
    EE_BODY_OFFSET,
    GRAVITY,
    DEVICE as DEFAULT_DEVICE,
    DT,
    CAMERAS,
    VIDEO_FPS,
)

from task_config import (
    TABLE_HEIGHT, CABLE_SEGMENTS, CABLE_SEG_LEN, CABLE_RADIUS,
    FINGER_OPEN_POS, FINGER_CLOSE_POS, FINGER_HALF_OPEN_POS,
    SETTLE_STEPS, NJMAX, SIM_SUBSTEPS, GRASP_X, CLIP1_Y,
)

# Newton IK
from newton.ik import IKSolver, IKObjectivePosition, IKObjectiveRotation, IKObjectiveJointLimit
import math

_cos_pi8 = math.cos(math.pi / 8)
_sin_pi8 = math.sin(math.pi / 8)

ROBOT_BODY_COUNT = 2 * FRANKA_NUM_JOINTS  # 18
IK_ITERATIONS = 100
IK_STEP_SIZE = 1.0
MAX_MOVE_STEPS = 1600
STEPS_PER_CM = 20
FINGER_INTERP_STEPS = 240  # steps to interpolate finger open/close


def solve_ik(fk_model, fk_state, target_left, target_right, device):
    """Solve IK for both arms. Returns joint_q numpy array."""
    left_ee = EE_BODY_OFFSET
    right_ee = FRANKA_NUM_JOINTS + EE_BODY_OFFSET

    rot_quat = wp.vec4(_cos_pi8, _sin_pi8, 0.0, 0.0)
    target_rot = wp.array([rot_quat], dtype=wp.vec4, device=device)

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

    fk_jq = fk_state.joint_q.numpy()
    jq_in = wp.array(fk_jq.reshape(1, -1), dtype=float, device=device)
    jq_out = wp.zeros((1, fk_model.joint_coord_count), dtype=float, device=device)
    ik_solver.step(jq_in, jq_out, iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)

    return jq_out.numpy()[0]


def move_to_waypoint(model, state, solver, contacts, fk_model, fk_state,
                     target_l, target_r, finger_l, finger_r,
                     label, device, recorder=None):
    """Move both arms to waypoint targets with finger interpolation + VBD physics."""
    # Current positions
    bq = state.body_q.numpy()
    pos_l = bq[EE_BODY_OFFSET][:3]
    pos_r = bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
    dist = max(np.linalg.norm(np.array(target_l) - pos_l),
               np.linalg.norm(np.array(target_r) - pos_r))
    n_arm_steps = max(int(dist * 100 * STEPS_PER_CM), 200)
    n_arm_steps = min(n_arm_steps, MAX_MOVE_STEPS)

    # Finger interpolation
    fk_jq_start = fk_state.joint_q.numpy().copy()
    finger_start_l = fk_jq_start[7]
    finger_start_r = fk_jq_start[FRANKA_NUM_JOINTS + 7]
    finger_change = (abs(finger_l - finger_start_l) > 0.001 or
                     abs(finger_r - finger_start_r) > 0.001)

    # Use max of arm steps and finger interpolation steps
    n_steps = n_arm_steps
    if finger_change:
        n_steps = max(n_steps, FINGER_INTERP_STEPS)

    # Solve IK for arm target (finger coords excluded)
    jq_target = solve_ik(fk_model, fk_state, tuple(target_l), tuple(target_r), device)
    if np.any(np.isnan(jq_target)):
        print(f"  [{label}] IK NaN!")
        return state, False

    # Set finger targets in jq_target
    jq_target[7] = finger_l
    jq_target[8] = finger_l
    jq_target[FRANKA_NUM_JOINTS + 7] = finger_r
    jq_target[FRANKA_NUM_JOINTS + 8] = finger_r

    jq_start = fk_jq_start.copy()
    finger_coords = {7, 8, FRANKA_NUM_JOINTS + 7, FRANKA_NUM_JOINTS + 8}
    coord_count = fk_model.joint_coord_count

    err_l = err_r = 0.0
    for step in range(n_steps):
        t = min((step + 1) / n_steps, 1.0)

        jq_interp = jq_start.copy()
        for d in range(coord_count):
            jq_interp[d] = jq_start[d] + (jq_target[d] - jq_start[d]) * t

        fk_state.joint_q.assign(jq_interp)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

        # Update kinematic bodies in physics
        update_kinematic_bodies(state, fk_state, ROBOT_BODY_COUNT)

        # Physics substeps
        control = model.control()
        for _ in range(SIM_SUBSTEPS):
            state_1 = model.state()
            state.clear_forces()
            model.collide(state, contacts)
            solver.step(state, state_1, control, contacts, DT / SIM_SUBSTEPS)
            state, state_1 = state_1, state

        # Video capture
        if recorder:
            recorder.capture(state)

        # NaN check on cable
        bq_check = state.body_q.numpy()
        if np.any(np.isnan(bq_check[ROBOT_BODY_COUNT:])):
            print(f"  [{label}] Cable NaN at step {step}!")
            return state, False

    # Final error
    wp.synchronize()
    bq = state.body_q.numpy()
    pos_l = bq[EE_BODY_OFFSET][:3]
    pos_r = bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
    err_l = np.linalg.norm(pos_l - np.array(target_l)) * 1000
    err_r = np.linalg.norm(pos_r - np.array(target_r)) * 1000
    fk_jq = fk_state.joint_q.numpy()
    fl = fk_jq[7] * 1000
    fr = fk_jq[FRANKA_NUM_JOINTS + 7] * 1000
    print(f"  [{label}] Done: {n_steps} steps, err L={err_l:.1f}mm R={err_r:.1f}mm, "
          f"finger L={fl:.1f}mm R={fr:.1f}mm")

    return state, True


# 5 routing clips (cable routes through these)
CLIP_POSITIONS = [
    ("C1", 0.35,  0.15),
    ("C2", 0.40,  0.075),
    ("C3", 0.35,  0.0),
    ("C4", 0.40, -0.075),
    ("C5", 0.35, -0.15),
]
# 3 resting clips (cable support stands, at cable X=0.30)
REST_CLIPS = [
    ("S1", 0.30,  0.20),
    ("S2", 0.30,  0.00),
    ("S3", 0.30, -0.20),
]

# V-groove clip geometry (5 box parts per clip, visual only)
CLIP_PARTS = [
    (0,      0, 0.0025, 0.020,  0.015, 0.0025),  # base
    (-0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),  # left wall
    (+0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),  # right wall
    (-0.013, 0, 0.025,  0.002,  0.015, 0.005),    # left top
    (+0.013, 0, 0.025,  0.002,  0.015, 0.005),    # right top
]


def build_physics_scene(fk_model, fk_state, device):
    """Build VBD physics scene: cable + kinematic arms + table + 5 clips."""
    proto = newton.ModelBuilder()

    # Robot arms (kinematic)
    left_info = add_kinematic_arm(proto, fk_model, fk_state,
                                  arm_body_offset=0, label_prefix="left")
    right_info = add_kinematic_arm(proto, fk_model, fk_state,
                                   arm_body_offset=FRANKA_NUM_JOINTS, label_prefix="right")
    left_body_start, left_shape_start, left_shape_end, left_fv = left_info
    right_body_start, right_shape_start, right_shape_end, right_fv = right_info
    all_finger_visual = set(left_fv + right_fv)

    # Contact filtering: arm bodies 0-6 -> VISIBLE only, finger 7-8 -> COLLIDE
    for arm_ss, arm_se, arm_bs in [
        (left_shape_start, left_shape_end, left_body_start),
        (right_shape_start, right_shape_end, right_body_start),
    ]:
        for si in range(arm_ss, arm_se):
            local = proto.shape_body[si] - arm_bs
            if local < 7:
                proto.shape_flags[si] = 1  # VISIBLE only
            elif si in all_finger_visual:
                proto.shape_flags[si] = 1
            elif local in (7, 8):
                proto.shape_flags[si] = 0x6  # COLLIDE | BROADPHASE

    # Cable
    cable_half_len = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
    cable_y_start = CLIP1_Y - cable_half_len
    cable_start = (GRASP_X, cable_y_start, TABLE_HEIGHT + CABLE_RADIUS)
    cable_shape_start_idx = proto.shape_count
    cable_bodies, cable_joints = add_cable_rod(proto, start_pos=cable_start, direction=(0, 1, 0))
    cable_shape_end_idx = proto.shape_count

    # Cable-arm collision filter (arm 0-6 only)
    for cable_si in range(cable_shape_start_idx, cable_shape_end_idx):
        for arm_ss, arm_se, arm_bs in [
            (left_shape_start, left_shape_end, left_body_start),
            (right_shape_start, right_shape_end, right_body_start),
        ]:
            for arm_si in range(arm_ss, arm_se):
                local = proto.shape_body[arm_si] - arm_bs
                if local < 7:
                    proto.add_shape_collision_filter_pair(cable_si, arm_si)

    # Finger mesh -> CONVEX_MESH
    finger_mesh_indices = []
    for si in range(proto.shape_count):
        if si in all_finger_visual:
            continue
        bi = proto.shape_body[si]
        if bi < 0 or bi >= ROBOT_BODY_COUNT:
            continue
        local_l = bi - left_body_start
        local_r = bi - right_body_start
        if local_l in (7, 8) or local_r in (7, 8):
            if proto.shape_type[si] == newton.GeoType.MESH:
                finger_mesh_indices.append(si)
    if finger_mesh_indices:
        proto.approximate_meshes(method="convex_hull", shape_indices=finger_mesh_indices,
                                 keep_visual_shapes=False)

    print(f"[Scene] Proto: {proto.body_count} bodies, {proto.joint_count} joints")

    # Scene: ground + table + proto (single world)
    scene = newton.ModelBuilder(gravity=GRAVITY)
    scene.add_ground_plane()

    table_cfg = newton.ModelBuilder.ShapeConfig()
    table_cfg.ke = 500.0
    table_cfg.kd = 100.0
    table_cfg.mu = 1.0
    table_cfg.gap = 0.002
    table_xform = wp.transform((0.35, 0.0, TABLE_HEIGHT - 0.005), wp.quat_identity())
    scene.add_shape_box(body=-1, hx=0.50, hy=0.40, hz=0.005,
                        xform=table_xform, cfg=table_cfg)

    # 5 routing clips + 3 resting clips (all visual only)
    clip_shape_indices = []
    for clip_name, cx, cy in CLIP_POSITIONS + REST_CLIPS:
        cz = TABLE_HEIGHT
        for dx, dy, dz, hx, hy, hz in CLIP_PARTS:
            xf = wp.transform((cx + dx, cy + dy, cz + dz), wp.quat_identity())
            idx = scene.add_shape_box(body=-1, xform=xf, hx=hx, hy=hy, hz=hz)
            scene.shape_flags[idx] = 1  # VISIBLE only
            clip_shape_indices.append(idx)
        print(f"  [SCENE] Clip {clip_name} at ({cx}, {cy}, {cz})")

    scene.replicate(proto, world_count=1)
    scene.color()
    model = scene.finalize(device=device, requires_grad=False)

    # Zero inv_mass for robot bodies
    inv_mass = model.body_inv_mass.numpy()
    inv_inertia = model.body_inv_inertia.numpy()
    for bi in range(ROBOT_BODY_COUNT):
        inv_mass[bi] = 0.0
        inv_inertia[bi] = np.zeros(3, dtype=np.float32)
    model.body_inv_mass = wp.array(inv_mass, dtype=model.body_inv_mass.dtype, device=device)
    model.body_inv_inertia = wp.array(inv_inertia, dtype=model.body_inv_inertia.dtype, device=device)

    # Post-finalize: CONVEX_MESH flags
    model_sflags = model.shape_flags.numpy()
    model_stypes = model.shape_type.numpy()
    model_sbodies = model.shape_body.numpy()
    for si in range(len(model_stypes)):
        bi = model_sbodies[si]
        if bi < 0 or bi >= ROBOT_BODY_COUNT:
            continue
        local_l = bi
        local_r = bi - FRANKA_NUM_JOINTS
        if local_l in (7, 8) or local_r in (7, 8):
            if model_stypes[si] == 10:  # CONVEX_MESH
                model_sflags[si] = 0x6
            elif model_stypes[si] == 8:  # MESH
                model_sflags[si] = 0x1
    model.shape_flags = wp.array(model_sflags, dtype=model.shape_flags.dtype, device=device)

    print(f"[Scene] Model: {model.body_count} bodies, {model.joint_count} joints")

    solver = SolverVBD(model, iterations=20)
    model.rigid_contact_max = NJMAX
    state = model.state()
    contacts = model.contacts()

    return model, state, solver, contacts, cable_bodies, clip_shape_indices


def main():
    parser = argparse.ArgumentParser(description="43-step wet-run with video")
    parser.add_argument("--waypoints", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

    global DEFAULT_DEVICE
    device = args.device
    os.environ["NEWTON_DEVICE"] = device

    # Monkey-patch DEVICE for test_newton_clip_routing imports
    import test_newton_clip_routing as _tncr
    _tncr.DEVICE = device

    os.makedirs(args.output_dir, exist_ok=True)

    # Load waypoints
    with open(args.waypoints) as f:
        wp_data = json.load(f)
    steps = wp_data["steps"]
    print(f"[WetRun] Loaded {len(steps)} waypoints")

    # Build FK model
    print("[WetRun] Building FK model...")
    fk_model = build_fk_model()
    fk_state = fk_model.state()

    # Init FK to home config with fingers open
    fk_jq = fk_state.joint_q.numpy()
    fk_tp = fk_model.joint_target_pos.numpy()
    fk_jq[:] = fk_tp[:]
    fk_jq[7] = FINGER_OPEN_POS
    fk_jq[8] = FINGER_OPEN_POS
    fk_jq[FRANKA_NUM_JOINTS + 7] = FINGER_OPEN_POS
    fk_jq[FRANKA_NUM_JOINTS + 8] = FINGER_OPEN_POS
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    # Build physics scene
    print("[WetRun] Building physics scene...")
    model, state, solver, contacts, cable_bodies, clip_shape_indices = build_physics_scene(
        fk_model, fk_state, device)

    # Settle cable
    print("[WetRun] Settling cable (2s)...")
    control = model.control()
    settle_frames = int(2.0 / DT)
    for _ in range(settle_frames):
        update_kinematic_bodies(state, fk_state, ROBOT_BODY_COUNT)
        state_1 = model.state()
        state.clear_forces()
        model.collide(state, contacts)
        solver.step(state, state_1, control, contacts, DT / SIM_SUBSTEPS)
        state, state_1 = state_1, state
    wp.synchronize()
    bq = state.body_q.numpy()
    cable_z = bq[cable_bodies, 2]
    print(f"[WetRun] Cable settled: z=[{cable_z.min():.4f}, {cable_z.mean():.4f}]")

    # Video recorder
    scene_info = {
        "cable_bodies": cable_bodies,
        "left_body_start": 0,
        "right_body_start": FRANKA_NUM_JOINTS,
        "clip_shape_indices": clip_shape_indices,
    }
    recorder = VideoRecorder(args.output_dir, model, enabled=True,
                             scene_info=scene_info)

    # Capture initial frame
    recorder.capture(state)

    # Execute waypoints
    t0 = time.perf_counter()
    print(f"\n[WetRun] Executing {len(steps)} waypoints...")

    for i, wp_step in enumerate(steps):
        step_num = wp_step["step"]
        phase = wp_step["phase"]
        desc = wp_step["desc"]
        target_l = wp_step["target_l"]
        target_r = wp_step["target_r"]
        finger_l = wp_step["left_finger"]
        finger_r = wp_step["right_finger"]
        label = f"S{step_num:02d}-{phase}"

        print(f"\n── STEP {step_num}/{len(steps)}: {desc} ({phase}) ──")

        state, ok = move_to_waypoint(
            model, state, solver, contacts, fk_model, fk_state,
            target_l, target_r, finger_l, finger_r,
            label=label, device=device, recorder=recorder,
        )

        if not ok:
            print(f"[WetRun] FAILED at step {step_num}")
            break

        # Short settle between waypoints
        for _ in range(80):
            update_kinematic_bodies(state, fk_state, ROBOT_BODY_COUNT)
            state_1 = model.state()
            state.clear_forces()
            model.collide(state, contacts)
            solver.step(state, state_1, control, contacts, DT / SIM_SUBSTEPS)
            state, state_1 = state_1, state
            recorder.capture(state)

    elapsed = time.perf_counter() - t0
    print(f"\n[WetRun] Complete in {elapsed:.1f}s")

    # Save videos
    video_paths = recorder.finalize(episode_idx=0)
    if video_paths:
        print(f"\n[WetRun] Videos saved to {args.output_dir}/")
        for p in video_paths:
            print(f"  {p}")


if __name__ == "__main__":
    main()
