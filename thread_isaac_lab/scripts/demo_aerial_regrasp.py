#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Demo: AerialRegrasp motion sequence with video.

Loads precondition cache (left arm holds cable at LIFT_Z), then:
  Step 12: Initial state — left CLAMP, right OPEN, both at LIFT_Z
  Step 13: Right arm moves to cable position
  Step 14: Right arm CLAMPs — both hands hold cable

Usage:
    # First build cache (if not done):
    #   python thread_isaac_lab/scripts/build_aerial_regrasp_precondition.py --world-count 1 --device cuda:1
    # Then run demo:
    source ~/env_isaaclab6/bin/activate
    cd ~/IsaacLab
    python thread_isaac_lab/scripts/demo_aerial_regrasp.py --device cuda:1
"""

import argparse
import os
import sys
import time

import numpy as np
import newton
import warp as wp

_envs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "envs")
if _envs_dir not in sys.path:
    sys.path.insert(0, _envs_dir)

from newton_skill_env_base import (
    build_fk_and_init,
    build_multiworld_scene,
    broadcast_fk_to_all_worlds,
    physics_step,
    solve_ik_single,
    hold_position,
    FRANKA_NUM_JOINTS,
    EE_BODY_OFFSET,
    FINGER_JOINT_INDICES,
    ROBOT_BODY_COUNT,
    DT,
    SIM_SUBSTEPS,
    SIM_DT,
    MAX_MOVE_STEPS,
)

_config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs")
if _config_dir not in sys.path:
    sys.path.insert(0, _config_dir)

from task_config import (
    TABLE_HEIGHT, GRASP_Z, LIFT_Z,
    GRASP_X, WIDE_LEFT_Y, WIDE_RIGHT_Y,
    CABLE_RADIUS, CLIP_BASE_HEIGHT,
    FINGER_OPEN_POS, FINGER_CLOSE_POS,
    EE_TO_FINGERTIP,
)

_scripts_dir = os.path.dirname(os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from test_newton_clip_routing import VideoRecorder

CABLE_TABLE_Z = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS
FINGER_CLOSE_STEPS = 500
FINGER_CLOSE_SETTLE = 3

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "data", "rl_aerial_regrasp_cache")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "data", "demo_aerial_regrasp")


def load_precondition(world_count, device):
    """Load precondition: rebuild scene structure, restore body state from cache.

    Returns (fk_model, fk_state, scene).
    """
    # Find cache file
    cache_path = os.path.join(
        CACHE_DIR, f"aerial_regrasp_w{world_count}_p0_v2.npz")
    if not os.path.exists(cache_path):
        # Try any world count
        import glob
        candidates = glob.glob(os.path.join(CACHE_DIR, "aerial_regrasp_w*_p0_v2.npz"))
        if not candidates:
            print(f"[FATAL] No cache found in {CACHE_DIR}")
            print("  Run build_aerial_regrasp_precondition.py first")
            sys.exit(1)
        cache_path = candidates[0]
        print(f"  [WARN] Requested w={world_count}, using cache: {cache_path}")

    cache = np.load(cache_path)
    cached_wc = int(cache["world_count"][0])
    print(f"  Loading cache: {cache_path} (worlds={cached_wc})")

    # Rebuild scene with same structure (fast — no physics sim)
    fk_model, fk_state, fk_jq = build_fk_and_init(
        left_finger_pos=FINGER_CLOSE_POS,   # left CLOSED
        right_finger_pos=FINGER_OPEN_POS,    # right OPEN
        device=device,
    )

    # Restore FK joint positions from cache
    cached_fk_jq = cache["fk_jq"]
    fk_state.joint_q.assign(cached_fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    # Solve IK for LIFT_Z to get correct arm configuration
    # (FK already has the right joint angles from cache)
    scene = build_multiworld_scene(
        fk_model, fk_state, world_count, device,
        cable_start_pos=(GRASP_X, 0, CABLE_TABLE_Z),
        add_support_clips=True,
    )

    # Restore physics state from cache
    wp.synchronize()
    cached_bq = cache["body_q"]
    cached_bqd = cache["body_qd"]

    # If world counts differ, tile/truncate
    bq_np = scene["state_0"].body_q.numpy()
    bqd_np = scene["state_0"].body_qd.numpy()
    bpw = len(bq_np) // world_count  # bodies per world

    cached_bpw = len(cached_bq) // cached_wc
    for w in range(world_count):
        src_w = w % cached_wc
        src_start = src_w * cached_bpw
        dst_start = w * bpw
        n = min(bpw, cached_bpw)
        bq_np[dst_start:dst_start + n] = cached_bq[src_start:src_start + n]
        bqd_np[dst_start:dst_start + n] = cached_bqd[src_start:src_start + n]

    scene["state_0"].body_q.assign(bq_np)
    scene["state_0"].body_qd.assign(bqd_np)

    # Critical: reset solver.body_q_prev to match body_q
    # Without this, VBD computes (body_q - body_q_prev)/dt = huge velocity → explosion
    solver = scene["solver"]
    prev_np = solver.body_q_prev.numpy()
    for w in range(world_count):
        src_w = w % cached_wc
        src_start = src_w * cached_bpw
        dst_start = w * bpw
        n = min(bpw, cached_bpw)
        prev_np[dst_start:dst_start + n] = cached_bq[src_start:src_start + n]
    solver.body_q_prev.assign(prev_np)

    # Reset Dahl friction state
    if hasattr(solver, 'enable_dahl_friction') and solver.enable_dahl_friction:
        if solver.joint_C_fric is not None:
            solver.joint_C_fric.zero_()
        if solver.joint_sigma_prev is not None:
            solver.joint_sigma_prev.zero_()

    print(f"  Precondition restored: left=CLAMP, right=OPEN, both at LIFT_Z")

    # Verify
    bq = scene["state_0"].body_q.numpy()
    bws = scene["bws"]
    cb = scene["cable_bodies"][0]
    cz = bq[cb, 2]
    fingertip_z = LIFT_Z - EE_TO_FINGERTIP
    near = np.sum(np.abs(cz - fingertip_z) < 0.050)
    print(f"  cable_z=[{cz.min():.3f},{cz.max():.3f}], near_fingertip={near}")

    return fk_model, fk_state, scene


def find_regrasp_target(scene, world_idx=0):
    """Find cable midpoint for regrasp (visible Y motion)."""
    wp.synchronize()
    bq = scene["state_0"].body_q.numpy()
    cable_bodies = scene["cable_bodies"][world_idx]
    cable_pos = bq[cable_bodies, :3]

    # Use cable midpoint between left arm and cable end for visible motion
    mid_y = (WIDE_LEFT_Y + WIDE_RIGHT_Y) / 2  # 0.15
    y_dists = np.abs(cable_pos[:, 1] - mid_y)
    nearest_idx = np.argmin(y_dists)
    target = cable_pos[nearest_idx]

    return float(target[0]), float(target[1]), float(target[2])


def ik_move_with_video(fk_model, fk_state, scene, target_left, target_right,
                       world_count, device, recorder, label="MOVE"):
    """IK move both arms with video capture."""
    jq_target = solve_ik_single(fk_model, fk_state, target_left, target_right, device)
    if np.any(np.isnan(jq_target)):
        print(f"  [{label}] IK FAILED (NaN)")
        return False

    jq_start = fk_state.joint_q.numpy().copy()
    n_coords = fk_model.joint_coord_count
    state_0, state_1 = scene["state_0"], scene["state_1"]
    bws = scene["bws"]

    for step in range(MAX_MOVE_STEPS):
        t = min((step + 1) / MAX_MOVE_STEPS, 1.0)
        jq_interp = jq_start.copy()
        for d in range(n_coords):
            if d not in FINGER_JOINT_INDICES:
                jq_interp[d] = jq_start[d] + (jq_target[d] - jq_start[d]) * t

        fk_state.joint_q.assign(jq_interp)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        broadcast_fk_to_all_worlds(fk_state, state_0, bws, world_count)
        state_0, state_1 = physics_step(
            scene["model"], scene["solver"], state_0, state_1,
            scene["control"], scene["contacts"],
        )
        recorder.capture(state_0)

        if (step + 1) % 10 == 0:
            wp.synchronize()
            bq = state_0.body_q.numpy()
            left_ee = bq[bws[0] + EE_BODY_OFFSET][:3]
            right_ee = bq[bws[0] + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
            err_l = np.linalg.norm(left_ee - np.array(target_left)) * 1000
            err_r = np.linalg.norm(right_ee - np.array(target_right)) * 1000
            if max(err_l, err_r) < 5.0:
                break

    scene["state_0"], scene["state_1"] = state_0, state_1
    print(f"  [{label}] Done: steps={step + 1}, err_L={err_l:.1f}mm, err_R={err_r:.1f}mm")
    return True


def hold_with_video(fk_state, scene, world_count, n_frames, recorder):
    """Hold position with video capture."""
    state_0, state_1 = scene["state_0"], scene["state_1"]
    for _ in range(n_frames):
        broadcast_fk_to_all_worlds(fk_state, state_0, scene["bws"], world_count)
        state_0, state_1 = physics_step(
            scene["model"], scene["solver"], state_0, state_1,
            scene["control"], scene["contacts"],
        )
        recorder.capture(state_0)
    scene["state_0"], scene["state_1"] = state_0, state_1


def close_fingers_with_video(fk_model, fk_state, scene, world_count,
                             finger_indices, recorder):
    """Close specified fingers with video capture."""
    j7, j8 = finger_indices
    state_0, state_1 = scene["state_0"], scene["state_1"]

    for step in range(FINGER_CLOSE_STEPS):
        t = (step + 1) / FINGER_CLOSE_STEPS
        finger_pos = FINGER_OPEN_POS + (FINGER_CLOSE_POS - FINGER_OPEN_POS) * t

        fk_jq = fk_state.joint_q.numpy()
        fk_jq[j7] = finger_pos
        fk_jq[j8] = finger_pos
        fk_state.joint_q.assign(fk_jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        broadcast_fk_to_all_worlds(fk_state, state_0, scene["bws"], world_count)

        for _ in range(FINGER_CLOSE_SETTLE):
            state_0, state_1 = physics_step(
                scene["model"], scene["solver"], state_0, state_1,
                scene["control"], scene["contacts"],
            )
            recorder.capture(state_0)

    scene["state_0"], scene["state_1"] = state_0, state_1


def main():
    parser = argparse.ArgumentParser(description="Demo: AerialRegrasp (step 12→13→14)")
    parser.add_argument("--device", type=str, default="cuda:1")
    args = parser.parse_args()

    device = args.device
    world_count = 1  # demo: single world
    t0 = time.perf_counter()

    # =========================================================================
    # Step 12: Load precondition — left CLAMP, right OPEN, both at LIFT_Z
    # =========================================================================
    print("=== Step 12: Load Precondition ===")
    fk_model, fk_state, scene = load_precondition(world_count, device)

    # Short settle to stabilize restored state (0.5s)
    print("  Stabilizing restored state (0.5s)...")
    hold_position(fk_state, scene, world_count, int(0.5 / DT))

    # Verify cable state after stabilization
    wp.synchronize()
    bq = scene["state_0"].body_q.numpy()
    bws = scene["bws"]
    cb = scene["cable_bodies"][0]
    cz = bq[cb, 2]
    cy = bq[cb, 1]
    print(f"  Post-settle cable: z=[{cz.min():.3f},{cz.max():.3f}], "
          f"y=[{cy.min():.3f},{cy.max():.3f}]")

    load_time = time.perf_counter() - t0
    print(f"  Step 12 done in {load_time:.1f}s")

    # Initialize video recorder
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    scene_info = {
        "left_body_start": bws[0],
        "right_body_start": bws[0] + FRANKA_NUM_JOINTS,
    }
    recorder = VideoRecorder(OUTPUT_DIR, scene["model"],
                             enabled=True, scene_info=scene_info)

    # Record initial state (1.5s)
    print("  Recording initial state (1.5s)...")
    hold_with_video(fk_state, scene, world_count, int(1.5 / DT), recorder)

    # =========================================================================
    # Step 13: Right arm moves to cable (right OPEN, approaching)
    # =========================================================================
    print("\n=== Step 13: Right Arm → Cable ===")

    # Find regrasp target (cable midpoint for visible motion)
    cable_x, cable_y, cable_z = find_regrasp_target(scene, world_idx=0)
    regrasp_ee_z = cable_z + EE_TO_FINGERTIP
    right_dy = abs(WIDE_RIGHT_Y - cable_y) * 1000
    right_dz = abs(LIFT_Z - regrasp_ee_z) * 1000
    print(f"  Cable target: ({cable_x:.3f}, {cable_y:.3f}, {cable_z:.3f})")
    print(f"  Right arm: Y move={right_dy:.0f}mm, Z move={right_dz:.0f}mm")

    # 13a: Right arm lateral + descent in one move
    print("[13] Right arm approach...")
    ok = ik_move_with_video(
        fk_model, fk_state, scene,
        target_left=(GRASP_X, WIDE_LEFT_Y, LIFT_Z),
        target_right=(GRASP_X, cable_y, regrasp_ee_z),
        world_count=world_count, device=device,
        recorder=recorder, label="APPROACH",
    )
    if not ok:
        print("[FATAL] Approach IK failed")
        sys.exit(1)

    # Short settle (0.3s)
    hold_with_video(fk_state, scene, world_count, int(0.3 / DT), recorder)

    # =========================================================================
    # Step 14: Right arm CLAMPs — both hands hold cable
    # =========================================================================
    print("\n=== Step 14: Right Arm CLAMP ===")
    # Franka-legacy finger indices, NOT UR5e-swapped (S2); port for UR5e (see S2_DEFERRED_OBLIGATIONS.md)
    right_j7 = FRANKA_NUM_JOINTS + 7
    right_j8 = FRANKA_NUM_JOINTS + 8
    close_fingers_with_video(fk_model, fk_state, scene, world_count,
                             finger_indices=(right_j7, right_j8),
                             recorder=recorder)
    print("  Right finger close complete")

    # Final hold (1.5s)
    print("  Final hold (1.5s)...")
    hold_with_video(fk_state, scene, world_count, int(1.5 / DT), recorder)

    # Validate
    wp.synchronize()
    bq = scene["state_0"].body_q.numpy()
    cz = bq[cb, 2]
    cy = bq[cb, 1]
    fk_jq = fk_state.joint_q.numpy()
    left_gap = (fk_jq[7] + fk_jq[8]) * 1000
    right_gap = (fk_jq[right_j7] + fk_jq[right_j8]) * 1000
    print(f"\n  Final cable: z=[{cz.min():.3f},{cz.max():.3f}], "
          f"y=[{cy.min():.3f},{cy.max():.3f}]")
    print(f"  Fingers: left={left_gap:.1f}mm (CLAMP), right={right_gap:.1f}mm (CLAMP)")

    # Save video
    print("\n[VIDEO] Encoding...")
    paths = recorder.finalize(episode_idx=0)
    if paths:
        for p in paths:
            print(f"  {p}")

    elapsed = time.perf_counter() - t0
    print(f"\n[AerialRegrasp Demo] Total: {elapsed:.1f}s (load: {load_time:.1f}s)")


if __name__ == "__main__":
    main()
