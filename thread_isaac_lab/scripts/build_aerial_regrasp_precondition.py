#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Build AerialRegrasp precondition cache.

Strategy: IK pre-solve + table placement + finger close + lift.
  1. FK init with both fingers OPEN, solve IK for GRASP_Z → arms start at target
  2. Scene: cable at table height (gravity-stable), arms pre-positioned
  3. Short settle (cable + table contact stabilization)
  4. Left finger OPEN→CLOSED gradually (cable grasp via contact force)
  5. IK move both arms → LIFT_Z (lift cable)
  6. Final settle + validation

Precondition output state:
  - Left arm: fingers CLOSED, holding cable at (GRASP_X, WIDE_LEFT_Y, LIFT_Z)
  - Right arm: fingers OPEN, at (GRASP_X, WIDE_RIGHT_Y, LIFT_Z)
  - Cable: held by left fingers at LIFT_Z, sagging elsewhere under gravity

Usage:
    source ~/env_isaaclab6/bin/activate
    cd ~/IsaacLab
    python thread_isaac_lab/scripts/build_aerial_regrasp_precondition.py \\
        --world-count 4 --device cuda:1
"""

import argparse
import os
import sys
import time

import numpy as np
import newton
import warp as wp

# Ensure envs/ is importable (for newton_skill_env_base)
_envs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "envs")
if _envs_dir not in sys.path:
    sys.path.insert(0, _envs_dir)

from newton_skill_env_base import (
    build_fk_and_init,
    build_multiworld_scene,
    broadcast_fk_to_all_worlds,
    physics_step,
    solve_ik_single,
    ik_move_all_worlds,
    hold_position,
    save_precondition_cache,
    FRANKA_NUM_JOINTS,
    EE_BODY_OFFSET,
    DT,
    SIM_SUBSTEPS,
    SIM_DT,
)

# Ensure configs/ is importable
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

# Cache
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "data", "rl_aerial_regrasp_cache")
CACHE_VERSION = "v2"

# Cable center Z on table
CABLE_TABLE_Z = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS  # 0.809m

# Fingertip Z at LIFT_Z
FINGERTIP_Z = LIFT_Z - EE_TO_FINGERTIP  # 0.900m

# Finger close parameters (catapult bug: too fast ejects cable)
FINGER_CLOSE_STEPS = 500      # gradual close (match test_newton_clip_routing 10/10 PASS)
FINGER_CLOSE_SETTLE = 3       # physics frames per close step (total: 1500 frames = 3.1s)


def close_left_fingers(fk_model, fk_state, scene, world_count):
    """Gradually close left arm fingers from OPEN to CLOSED.

    Right arm fingers remain OPEN throughout.
    Arm joints (j0-j6) are NOT modified here -- only finger joints (j7, j8) are updated.
    Each step: update FK finger pos → eval_fk → broadcast → physics settle.
    """
    print("[AerialRegrasp] Closing left fingers...")
    state_0, state_1 = scene["state_0"], scene["state_1"]

    for step in range(FINGER_CLOSE_STEPS):
        t = (step + 1) / FINGER_CLOSE_STEPS
        finger_pos = FINGER_OPEN_POS + (FINGER_CLOSE_POS - FINGER_OPEN_POS) * t

        fk_jq = fk_state.joint_q.numpy()
        fk_jq[7] = finger_pos
        fk_jq[8] = finger_pos
        fk_state.joint_q.assign(fk_jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        broadcast_fk_to_all_worlds(fk_state, state_0, scene["bws"], world_count)

        # Physics settle between each close step
        for _ in range(FINGER_CLOSE_SETTLE):
            state_0.clear_forces()
            scene["model"].collide(state_0, scene["contacts"])
            for _ in range(SIM_SUBSTEPS):
                scene["solver"].step(state_0, state_1, scene["control"],
                                     scene["contacts"], SIM_DT)
                state_0, state_1 = state_1, state_0

    scene["state_0"], scene["state_1"] = state_0, state_1
    final_gap = 2 * FINGER_CLOSE_POS * 1000
    print(f"  Left finger close complete: gap={final_gap:.1f}mm "
          f"({FINGER_CLOSE_STEPS} steps × {FINGER_CLOSE_SETTLE} frames)")


def validate_precondition(scene, fk_state, world_count):
    """Validate precondition state is physically sound."""
    wp.synchronize()
    bq = scene["state_0"].body_q.numpy()
    bws = scene["bws"]
    cable_bodies = scene["cable_bodies"]

    errors = []

    for w in range(min(world_count, 4)):
        ws = bws[w]

        world_bq = bq[ws:bws[w + 1]]
        if np.any(np.isnan(world_bq)):
            errors.append(f"World {w}: NaN in body_q")
            continue

        cable_z = bq[cable_bodies[w], 2]
        cable_z_min = float(np.min(cable_z))
        cable_z_max = float(np.max(cable_z))
        cable_z_mean = float(np.mean(cable_z))

        if cable_z_min < TABLE_HEIGHT - 0.020:
            errors.append(f"World {w}: Cable below table: z_min={cable_z_min:.4f} "
                          f"< TABLE_HEIGHT-20mm={TABLE_HEIGHT - 0.020:.4f}")

        near_fingertip = np.sum(np.abs(cable_z - FINGERTIP_Z) < 0.050)  # within 50mm
        if near_fingertip < 2:
            errors.append(f"World {w}: Only {near_fingertip} cable bodies near "
                          f"fingertip Z={FINGERTIP_Z:.3f} (±50mm)")

        left_ee = bq[ws + EE_BODY_OFFSET][:3]
        left_ee_err = np.linalg.norm(left_ee - np.array([GRASP_X, WIDE_LEFT_Y, LIFT_Z])) * 1000

        right_ee = bq[ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
        right_ee_err = np.linalg.norm(right_ee - np.array([GRASP_X, WIDE_RIGHT_Y, LIFT_Z])) * 1000

        print(f"  World {w}: cable_z=[{cable_z_min:.4f}, {cable_z_max:.4f}] "
              f"mean={cable_z_mean:.4f}, near_fingertip={near_fingertip}, "
              f"L_EE_err={left_ee_err:.1f}mm, R_EE_err={right_ee_err:.1f}mm")

    if errors:
        for e in errors:
            print(f"  VALIDATION ERROR: {e}")
        return False

    # FK state check
    fk_jq = fk_state.joint_q.numpy()
    left_finger = fk_jq[7] + fk_jq[8]
    right_finger = fk_jq[FRANKA_NUM_JOINTS + 7] + fk_jq[FRANKA_NUM_JOINTS + 8]
    print(f"  FK fingers: left={left_finger:.4f} (CLOSED={2*FINGER_CLOSE_POS:.4f}), "
          f"right={right_finger:.4f} (OPEN={2*FINGER_OPEN_POS:.4f})")

    expected_left = 2 * FINGER_CLOSE_POS
    expected_right = 2 * FINGER_OPEN_POS
    if abs(left_finger - expected_left) > 0.01:
        print(f"  WARNING: Left finger opening {left_finger:.4f} != expected {expected_left:.4f}")
    if abs(right_finger - expected_right) > 0.01:
        print(f"  WARNING: Right finger opening {right_finger:.4f} != expected {expected_right:.4f}")

    print("[AerialRegrasp] Validation PASSED")
    return True


def main():
    parser = argparse.ArgumentParser(description="Build AerialRegrasp precondition cache")
    parser.add_argument("--world-count", type=int, default=4)
    parser.add_argument("--device", type=str, default="cuda:1")
    args = parser.parse_args()

    world_count = args.world_count
    device = args.device

    print(f"[AerialRegrasp] Building precondition: {world_count} worlds on {device}")
    print(f"  CABLE_TABLE_Z={CABLE_TABLE_Z:.3f}, GRASP_Z={GRASP_Z:.3f}, LIFT_Z={LIFT_Z:.3f}")
    print(f"  Left arm: ({GRASP_X}, {WIDE_LEFT_Y}) OPEN→CLOSED")
    print(f"  Right arm: ({GRASP_X}, {WIDE_RIGHT_Y}) OPEN")
    t0 = time.perf_counter()

    # --- Step 1: FK init (both OPEN) + IK pre-solve for GRASP_Z ---
    print("[Step 1] FK init + IK pre-solve...")
    fk_model, fk_state, fk_jq = build_fk_and_init(
        left_finger_pos=FINGER_OPEN_POS,
        right_finger_pos=FINGER_OPEN_POS,
        device=device,
    )

    target_left = (GRASP_X, WIDE_LEFT_Y, GRASP_Z)
    target_right = (GRASP_X, WIDE_RIGHT_Y, GRASP_Z)
    jq_solved = solve_ik_single(fk_model, fk_state, target_left, target_right, device)

    if np.any(np.isnan(jq_solved)):
        print("[FATAL] IK pre-solve returned NaN")
        sys.exit(1)

    # Apply IK solution (preserve finger positions)
    finger_indices = {7, 8, FRANKA_NUM_JOINTS + 7, FRANKA_NUM_JOINTS + 8}
    for d in range(fk_model.joint_coord_count):
        if d not in finger_indices:
            fk_jq[d] = jq_solved[d]
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    # Verify EE positions
    fk_bq = fk_state.body_q.numpy()
    left_ee = fk_bq[EE_BODY_OFFSET][:3]
    right_ee = fk_bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
    err_l = np.linalg.norm(left_ee - np.array(target_left)) * 1000
    err_r = np.linalg.norm(right_ee - np.array(target_right)) * 1000
    print(f"  IK pre-solve: L_err={err_l:.1f}mm, R_err={err_r:.1f}mm")
    print(f"  Fingertip Z ≈ {GRASP_Z - EE_TO_FINGERTIP:.3f}m, "
          f"Cable Z = {CABLE_TABLE_Z:.3f}m")

    # --- Step 2: Build scene (cable on table, arms at GRASP_Z) ---
    print("[Step 2] Building scene...")
    scene = build_multiworld_scene(
        fk_model, fk_state, world_count, device,
        cable_start_pos=(GRASP_X, 0, CABLE_TABLE_Z),  # Y=0 placeholder; base module computes actual Y from CLIP1_Y
        add_support_clips=True,  # prevent cable ends from falling off table edge
    )

    # --- Diagnostic: cable Z before settle ---
    wp.synchronize()
    _bq = scene["state_0"].body_q.numpy()
    _bws = scene["bws"]
    for _w in range(min(world_count, 4)):
        _cb = scene["cable_bodies"][_w]
        _cz = _bq[_cb, 2]
        print(f"  [DIAG] World {_w} cable_z BEFORE settle: [{_cz.min():.4f}, {_cz.max():.4f}] mean={_cz.mean():.4f}")

    # --- Step 3: Settle (2.0s) -- cable + table contact stabilization ---
    print("[Step 3] Settling (2.0s)...")
    settle_frames = int(2.0 / DT)  # 960 frames
    hold_position(fk_state, scene, world_count, settle_frames)

    # --- Diagnostic: cable Z after settle, before close ---
    wp.synchronize()
    _bq = scene["state_0"].body_q.numpy()
    for _w in range(min(world_count, 4)):
        _cb = scene["cable_bodies"][_w]
        _cz = _bq[_cb, 2]
        print(f"  [DIAG] World {_w} cable_z AFTER settle: [{_cz.min():.4f}, {_cz.max():.4f}] mean={_cz.mean():.4f}")

    # --- Step 4: Close left fingers ---
    close_left_fingers(fk_model, fk_state, scene, world_count)

    # Post-close settle (0.5s)
    print("[Step 4b] Post-close settle (0.5s)...")
    post_close_frames = int(0.5 / DT)  # 240 frames
    hold_position(fk_state, scene, world_count, post_close_frames)

    # --- Diagnostic: cable Z after close + settle ---
    wp.synchronize()
    _bq = scene["state_0"].body_q.numpy()
    for _w in range(min(world_count, 4)):
        _cb = scene["cable_bodies"][_w]
        _cz = _bq[_cb, 2]
        print(f"  [DIAG] World {_w} cable_z AFTER close: [{_cz.min():.4f}, {_cz.max():.4f}] mean={_cz.mean():.4f}")

    # --- Step 5: Lift to LIFT_Z (with diagnostics) ---
    print("[Step 5] Lifting to LIFT_Z...")
    lift_left = (GRASP_X, WIDE_LEFT_Y, LIFT_Z)
    lift_right = (GRASP_X, WIDE_RIGHT_Y, LIFT_Z)

    # Inline lift with per-step diagnostics
    from newton_skill_env_base import (
        solve_ik_single as _solve, FINGER_JOINT_INDICES, MAX_MOVE_STEPS,
    )
    jq_target = _solve(fk_model, fk_state, lift_left, lift_right, device)
    if np.any(np.isnan(jq_target)):
        print("[FATAL] Lift IK FAILED (NaN)")
        sys.exit(1)

    jq_start = fk_state.joint_q.numpy().copy()
    n_coords = fk_model.joint_coord_count
    state_0, state_1 = scene["state_0"], scene["state_1"]

    # Body indices for diagnostics — use World 1 (World 0 may catapult)
    bws = scene["bws"]
    diag_w = min(1, world_count - 1)
    cable_bodies_diag = scene["cable_bodies"][diag_w]
    left_finger7_body = bws[diag_w] + 7
    left_finger8_body = bws[diag_w] + 8
    print(f"  [DIAG] Monitoring World {diag_w}")

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

        # Diagnostics every 200 steps + first 5 steps
        if step < 5 or (step + 1) % 200 == 0:
            wp.synchronize()
            bq = state_0.body_q.numpy()

            # Finger body Z (world)
            f7z = bq[left_finger7_body, 2]
            f8z = bq[left_finger8_body, 2]

            # Cable Z
            cz = bq[cable_bodies_diag, 2]
            cz_min, cz_max, cz_mean = float(cz.min()), float(cz.max()), float(cz.mean())

            # Left EE (diag world)
            lee = bq[bws[diag_w] + EE_BODY_OFFSET][:3]
            ee_z = float(lee[2])

            print(f"  [LIFT step {step:4d}] t={t:.3f} EE_z={ee_z:.4f} "
                  f"finger7_z={f7z:.4f} finger8_z={f8z:.4f} "
                  f"cable_z=[{cz_min:.4f},{cz_max:.4f}] mean={cz_mean:.4f}")

        if (step + 1) % 10 == 0:
            wp.synchronize()
            bq = state_0.body_q.numpy()
            left_ee = bq[bws[diag_w] + EE_BODY_OFFSET][:3]
            right_ee = bq[bws[diag_w] + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
            err_l = np.linalg.norm(left_ee - np.array(lift_left)) * 1000
            err_r = np.linalg.norm(right_ee - np.array(lift_right)) * 1000
            if max(err_l, err_r) < 10.0:
                break

    scene["state_0"], scene["state_1"] = state_0, state_1
    print(f"  [LIFT] Done: steps={step + 1}, err_L={err_l:.1f}mm, err_R={err_r:.1f}mm")

    # --- Step 6: Final settle (2s) + validation ---
    print("[Step 6] Final settle (2s)...")
    final_settle = int(2.0 / DT)  # 960 frames
    hold_position(fk_state, scene, world_count, final_settle)

    ok = validate_precondition(scene, fk_state, world_count)
    if not ok:
        print("[AerialRegrasp] FAILED: validation failed")
        sys.exit(1)

    # --- Save cache ---
    bws = scene["bws"]
    w0 = bws[0]
    body_q = scene["state_0"].body_q.numpy()
    left_ee_hold = body_q[w0 + EE_BODY_OFFSET][:3].copy()
    right_ee_start = body_q[w0 + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3].copy()
    cable_x = np.mean(body_q[scene["cable_bodies"][0], 0])

    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR,
                              f"aerial_regrasp_w{world_count}_p0_{CACHE_VERSION}.npz")
    save_precondition_cache(
        cache_path, scene, fk_state, world_count,
        extra_keys={
            "left_ee_hold": left_ee_hold,
            "right_ee_start": right_ee_start,
            "settled_grasp_x": np.array([cable_x], dtype=np.float32),
        },
    )

    elapsed = time.perf_counter() - t0
    print(f"\n[AerialRegrasp] Done in {elapsed:.1f}s. Cache: {cache_path}")


if __name__ == "__main__":
    main()
