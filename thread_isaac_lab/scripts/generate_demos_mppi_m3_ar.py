#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MPPI demo trajectory generation on Newton VBD (M3-AR: AR-compat aerial-regrasp variant).

Delta from M3 (generate_demos_mppi_m3.py):
  - Precondition: L arm holding cable at WIDE_LEFT_Y, R arm free at WIDE_RIGHT_Y (inline build)
  - Cost: max(pos_dist_R, AR_COST_SCALE*ori_dist_R) + P_DROP*I(cable_dropped)  (FM-5 L-drift removed)
  - L arm: IK target frozen at precondition-end L EE pose (Q1=(ii), FM-5 approved)
  - Success: pos<12mm AND ori<10deg AND K=5 sustained (T_DIST_APPROACH, T_ALIGN)
  - HOLD_W: L-action noise sigma fraction in {0.1, 0.2, 0.4} (higher = more frozen)
  - FM-10: info dict translation from build_multiworld_scene to M2-compat keys

Usage:
    cd ~/IsaacLab
    PYTHONPATH=$PYTHONPATH:thread_isaac_lab/scripts:thread_isaac_lab/configs:thread_isaac_lab/envs \\
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/generate_demos_mppi_m3_ar.py \\
        --device cuda:0 --world-count 256 [--single-lambda 0.3 | --sweep] [--hold-w 0.2]

References:
    Design: thread-vault/08-DA-MPPI/01-Dashboard/m3_aerial_regrasp_design.md
    DEFINE: m3_aerial_regrasp_define_v1.md
    Reward: m3_aerial_regrasp_reward_design.md
    Pre-check: m3_aerial_regrasp_pre_check.md
"""

import argparse
import csv
import json
import math
import os
import sys
import time

import h5py
import newton
import numpy as np
import warp as wp

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "configs"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "envs"))

# Reuse from M2/M3 (DO NOT duplicate).
from generate_demos_mppi_m2 import (
    DT,
    REPLAN_INTERVAL,
    RL_SIM_SUBSTEPS,
    compute_cable_endpoint_pos,
    copy_world0_to_all,
    mppi_weights,
    sample_action_sequences,
    update_kinematic_bodies,
)
from generate_demos_mppi_m3 import (
    DRIFT_THRESHOLD_RAD,
    DRIFT_VIOLATION_RATE_LIMIT,
    M3_ACTION_DIM,
    M3_ACTION_LAYOUT,
    M3_QUAT_CONVENTION,
    M3_QUAT_FRAME,
    M3_QUAT_SEMANTIC,
    MppiIKSolverM3,
    _stats,
    compute_cost_targets_from_cable,
    get_ee_poses_dual,
)

from newton_skill_env_base import (
    axis_angle_to_quat_xyzw as _axis_angle_to_quat_xyzw,  # Env-Refactor 2026-04-21 rename, keep local alias
    normalize_quat_w_positive as _normalize_quat_w_positive,
    quat_distance as _quat_distance,
    quat_multiply_xyzw as _quat_multiply_xyzw,
)
from newton_skill_env_base import (
    FINGER_JOINT_INDICES,
    MAX_MOVE_STEPS,
    SIM_DT,
    SIM_SUBSTEPS,
    broadcast_fk_to_all_worlds,
    build_fk_and_init,
    build_multiworld_scene,
    compute_clamp_pos,
    find_nearest_cable_point,
    hold_position,
    load_precondition_cache,
    physics_step,
    quat_rotate_vec,
    save_precondition_cache,
    solve_ik_single,
)
from cable_orientation_utils import compute_cable_tangent, compute_hand_quat_for_cable
from task_config import (
    CABLE_RADIUS,
    CLIP_BASE_HEIGHT,
    EE_TO_FINGERTIP,
    FINGER_CLOSE_POS,
    FINGER_OPEN_POS,
    GRASP_X,
    GRASP_Z,
    LIFT_Z,
    T_ALIGN,
    T_DIST_APPROACH,
    TABLE_HEIGHT,
    WIDE_LEFT_Y,
    WIDE_RIGHT_Y,
)
from test_newton_clip_routing import EE_BODY_OFFSET, FRANKA_NUM_JOINTS

from mpc_config_ar import MPPIConfigAR

# =========================================================================
# M3-AR Module constants
# =========================================================================

AR_VERSION = "v1.0"
AR_COST_METHOD = "R-only-max + P_DROP"  # FM-5: L-drift removed; FM-2: P_DROP additive
# AR_COST_SCALE: default baseline. Runtime value via cfg.ar_cost_scale (mpc_config_ar.py).
# Phase 0 (2026-04-21) R1 sweep via cfg override to 0.15 / 0.20 / 0.30.
AR_COST_SCALE = T_DIST_APPROACH / T_ALIGN  # ~= 0.0688 (12mm/10deg) baseline
P_DROP = 100.0  # FM-2 approved: additive penalty for cable-dropped rollout
CABLE_DROP_Z_THR = 0.820  # [m] cable z_min below this = dropped (AR env not-dropped condition)
K_SUSTAIN = 5  # Q5 approved: required consecutive success steps
DRIFT_CAP = 0.010  # [m] L-EE drift cap (matches AR env DRIFT_CAP)

# Precondition builder constants (duplicated from build_aerial_regrasp_precondition.py per F2 audit).
CABLE_TABLE_Z = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS  # ~= 0.809m
FINGERTIP_Z = LIFT_Z - EE_TO_FINGERTIP  # ~= 0.900m
FINGER_CLOSE_STEPS = 500
FINGER_CLOSE_SETTLE = 3

# Success thresholds (SSOT: task_config.py).
AR_POS_THR_M = T_DIST_APPROACH  # 0.012 m
AR_ORI_THR_RAD = T_ALIGN  # 0.1745 rad (~10 deg)

# Cable target segment window (SSOT: newton_aerial_regrasp_env.py:GRIP_SEG_WINDOW=5).
GRIP_SEG_WINDOW = 5


# =========================================================================
# Precondition helpers (duplicated from build_aerial_regrasp_precondition.py:88-122, 283-356, 188-363)
# Per F2 audit + OPEN ISSUE D Q4 approval: duplicate into entry script.
# =========================================================================


def close_left_fingers(fk_model, fk_state, scene, world_count):
    """Gradually close left arm fingers from OPEN to CLOSED over 500 x 3 physics frames.

    Right arm fingers remain OPEN. Only joints (j7, j8) are updated on left.

    Duplicated from build_aerial_regrasp_precondition.py:88-122 (F2 audit).
    """
    print("[AR-PRE] Closing left fingers...")
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

        for _ in range(FINGER_CLOSE_SETTLE):
            state_0.clear_forces()
            scene["model"].collide(state_0, scene["contacts"])
            for _ in range(SIM_SUBSTEPS):
                scene["solver"].step(state_0, state_1, scene["control"], scene["contacts"], SIM_DT)
                state_0, state_1 = state_1, state_0

    scene["state_0"], scene["state_1"] = state_0, state_1
    final_gap = 2 * FINGER_CLOSE_POS * 1000
    print(f"  [AR-PRE] Left finger close complete: gap={final_gap:.1f}mm")


def lift_both_arms_to_z(fk_model, fk_state, scene, target_left, target_right, world_count, device):
    """Lift both arms via interpolated IK to LIFT_Z with physics stepping.

    Exits early when max(err_L, err_R) < 10 mm, else runs MAX_MOVE_STEPS.
    Duplicated (as function) from build_aerial_regrasp_precondition.py:283-356 (F2 audit).
    """
    print("[AR-PRE] Lifting both arms to LIFT_Z...")
    jq_target = solve_ik_single(fk_model, fk_state, target_left, target_right, device)
    if np.any(np.isnan(jq_target)):
        raise RuntimeError("[AR-PRE] Lift IK FAILED (NaN)")

    jq_start = fk_state.joint_q.numpy().copy()
    n_coords = fk_model.joint_coord_count
    state_0, state_1 = scene["state_0"], scene["state_1"]
    bws = scene["bws"]
    err_l = err_r = 0.0
    step = 0

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
            scene["model"], scene["solver"], state_0, state_1, scene["control"], scene["contacts"],
        )

        if (step + 1) % 10 == 0:
            wp.synchronize()
            bq = state_0.body_q.numpy()
            left_ee = bq[bws[0] + EE_BODY_OFFSET][:3]
            right_ee = bq[bws[0] + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
            err_l = np.linalg.norm(left_ee - np.array(target_left)) * 1000
            err_r = np.linalg.norm(right_ee - np.array(target_right)) * 1000
            if max(err_l, err_r) < 10.0:
                break

    scene["state_0"], scene["state_1"] = state_0, state_1
    print(f"  [AR-PRE] Lift done: steps={step + 1}, err_L={err_l:.1f}mm, err_R={err_r:.1f}mm")


def _compute_ar_target_seg_indices(state, info, world_count):
    """Compute per-world cable target indices for L/R arms using ±GRIP_SEG_WINDOW.

    Mirrors `newton_aerial_regrasp_env._compute_target_seg_indices`: from each
    arm's fingertip (EE minus EE_TO_FINGERTIP in world Z, hand-down approximation),
    find the nearest cable seg and take a ±5 window clipped to [0, n_cable-1].

    Returns:
        (target_r (W, 2*GRIP_SEG_WINDOW+1), target_l (W, ...)) int32 arrays.
    """
    bq = state.body_q.numpy()
    bws = info["bws"]
    co = info["cable_offset"]
    cpw = info["cable_per_world"]
    win = GRIP_SEG_WINDOW
    n_seg = 2 * win + 1
    target_r = np.zeros((world_count, n_seg), dtype=np.int32)
    target_l = np.zeros((world_count, n_seg), dtype=np.int32)
    flat = bq.view(np.float32).reshape(-1, 7)
    for w in range(world_count):
        ws = bws[w]
        cable_pos = flat[ws + co : ws + co + cpw, :3]
        right_ee = flat[ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET, :3].copy()
        right_tip = right_ee.copy()
        right_tip[2] -= EE_TO_FINGERTIP
        right_seg = int(np.argmin(np.linalg.norm(cable_pos - right_tip, axis=1)))
        target_r[w] = np.clip(np.arange(right_seg - win, right_seg + win + 1), 0, cpw - 1)

        left_ee = flat[ws + EE_BODY_OFFSET, :3].copy()
        left_tip = left_ee.copy()
        left_tip[2] -= EE_TO_FINGERTIP
        left_seg = int(np.argmin(np.linalg.norm(cable_pos - left_tip, axis=1)))
        target_l[w] = np.clip(np.arange(left_seg - win, left_seg + win + 1), 0, cpw - 1)
    return target_r, target_l


def _load_ar_precondition_from_cache(world_count, device, cache_path):
    """Fast-path: load precondition from existing cache (skip W1-W5 build).

    Used by F7 sweep to avoid rebuilding precondition for each (lambda, hold_w)
    cell at the same K. Falls back to full build if cache is stale/missing.
    """
    print(f"[AR-PRE] Loading cached precondition: {cache_path}")
    data = load_precondition_cache(cache_path)

    # Validate cache compatibility.
    if int(data["world_count"][0]) != world_count:
        raise RuntimeError(
            f"[AR-PRE] Cache world_count mismatch: cache={int(data['world_count'][0])}, expected={world_count}"
        )

    # Build FK (left CLOSED, right OPEN, matching precondition-end state).
    fk_model, fk_state, fk_jq = build_fk_and_init(
        left_finger_pos=FINGER_CLOSE_POS, right_finger_pos=FINGER_OPEN_POS, device=device,
    )
    # Restore cached FK joint positions.
    fk_state.joint_q.assign(data["fk_jq"])
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    # Build multi-world scene (same geometry as original precondition build).
    scene = build_multiworld_scene(
        fk_model, fk_state, world_count, device,
        cable_start_pos=(GRASP_X, 0, CABLE_TABLE_Z),
        add_support_clips=True,
    )
    if data["body_count"][0] != scene["model"].body_count:
        raise RuntimeError(
            f"[AR-PRE] Cache body_count mismatch: cache={data['body_count'][0]}, "
            f"scene={scene['model'].body_count}"
        )

    # Apply cached body state (overrides default spawn positions).
    scene["state_0"].body_q.assign(data["body_q"])
    scene["state_0"].body_qd.assign(data["body_qd"])
    scene["solver"].body_q_prev = wp.clone(scene["state_0"].body_q)
    return fk_model, fk_state, scene


def build_ar_precondition(world_count, device, force_rebuild=False):
    """Build aerial-regrasp precondition state inline (Steps 1-5).

    If a cache exists at `data/rl_aerial_regrasp_cache/aerial_regrasp_w{K}_p0_v2.npz`
    and `force_rebuild=False`, loads from cache (~1s) instead of rebuilding (~5-15min).
    Cache is written at the end of a fresh build.

    Returns:
        fk_model, fk_state, scene: Ready for MPPI consumption. L arm holds cable at
        (GRASP_X, WIDE_LEFT_Y, LIFT_Z); R arm free at (GRASP_X, WIDE_RIGHT_Y, LIFT_Z).

    Adapted from build_aerial_regrasp_precondition.py:188-363 main() body.
    """
    cache_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "rl_aerial_regrasp_cache",
    )
    cache_path = os.path.join(cache_dir, f"aerial_regrasp_w{world_count}_p0_v2.npz")

    if not force_rebuild and os.path.exists(cache_path):
        try:
            return _load_ar_precondition_from_cache(world_count, device, cache_path)
        except Exception as e:
            print(f"[AR-PRE] Cache load failed ({e}); rebuilding fresh")

    t0 = time.perf_counter()
    print(f"[AR-PRE] Building precondition: {world_count} worlds on {device}")

    # Step 1: FK init (both OPEN) + IK pre-solve for GRASP_Z.
    fk_model, fk_state, fk_jq = build_fk_and_init(
        left_finger_pos=FINGER_OPEN_POS, right_finger_pos=FINGER_OPEN_POS, device=device,
    )
    target_left_grasp = (GRASP_X, WIDE_LEFT_Y, GRASP_Z)
    target_right_grasp = (GRASP_X, WIDE_RIGHT_Y, GRASP_Z)
    jq_solved = solve_ik_single(fk_model, fk_state, target_left_grasp, target_right_grasp, device)
    if np.any(np.isnan(jq_solved)):
        raise RuntimeError("[AR-PRE] IK pre-solve returned NaN")

    finger_indices = {7, 8, FRANKA_NUM_JOINTS + 7, FRANKA_NUM_JOINTS + 8}
    for d in range(fk_model.joint_coord_count):
        if d not in finger_indices:
            fk_jq[d] = jq_solved[d]
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    # Step 2: build scene (cable on table, support clips enabled).
    scene = build_multiworld_scene(
        fk_model, fk_state, world_count, device,
        cable_start_pos=(GRASP_X, 0, CABLE_TABLE_Z),
        add_support_clips=True,
    )

    # Step 3: settle 2s (cable + table contact stabilization).
    settle_frames = int(2.0 / DT)
    hold_position(fk_state, scene, world_count, settle_frames)

    # Step 4: close left fingers.
    close_left_fingers(fk_model, fk_state, scene, world_count)
    hold_position(fk_state, scene, world_count, int(0.5 / DT))

    # Step 5: lift to LIFT_Z.
    lift_left = (GRASP_X, WIDE_LEFT_Y, LIFT_Z)
    lift_right = (GRASP_X, WIDE_RIGHT_Y, LIFT_Z)
    lift_both_arms_to_z(fk_model, fk_state, scene, lift_left, lift_right, world_count, device)

    # Final settle 2s.
    hold_position(fk_state, scene, world_count, int(2.0 / DT))

    # W6 cache save (FM-12 mitigation + F4 handoff test dependency).
    cache_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "rl_aerial_regrasp_cache",
    )
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"aerial_regrasp_w{world_count}_p0_v2.npz")
    wp.synchronize()
    bq = scene["state_0"].body_q.numpy()
    w0 = scene["bws"][0]
    left_ee_hold = bq[w0 + EE_BODY_OFFSET][:3].copy()
    right_ee_start = bq[w0 + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3].copy()
    cable_x = float(np.mean(bq[scene["cable_bodies"][0], 0]))
    save_precondition_cache(
        cache_path, scene, fk_state, world_count,
        extra_keys={
            "left_ee_hold": left_ee_hold.astype(np.float32),
            "right_ee_start": right_ee_start.astype(np.float32),
            "settled_grasp_x": np.array([cable_x], dtype=np.float32),
        },
    )

    elapsed = time.perf_counter() - t0
    print(f"[AR-PRE] Precondition ready in {elapsed:.1f}s (cache -> {cache_path})")
    return fk_model, fk_state, scene


# =========================================================================
# FM-10 MITIGATION: info dict translation from base-scene to M2-compat keys.
# =========================================================================


def base_scene_to_m2_info(scene):
    """Translate build_multiworld_scene output to M2-compatible info dict.

    M2 keys expected by imported functions (get_ee_poses_dual, compute_cable_endpoint_pos,
    copy_world0_to_all, update_kinematic_bodies). FM-10 CRITICAL mitigation.

    Base keys -> M2 keys map:
        cable_body_offset       -> cable_offset
        cable_bodies_per_world  -> cable_per_world
        (new)                   -> left_body_start  = 0
        (new)                   -> right_body_start = FRANKA_NUM_JOINTS
    """
    return {
        "bws": scene["bws"],
        "bodies_per_world": scene["bodies_per_world"],
        "cable_per_world": scene["cable_bodies_per_world"],
        "cable_offset": scene["cable_body_offset"],
        "left_body_start": 0,  # Left Franka base in each world
        "right_body_start": FRANKA_NUM_JOINTS,  # Right Franka base after left 9 joints
    }


# =========================================================================
# AR rollout + cost: R-only max + P_DROP (L arm frozen via fixed IK target)
# =========================================================================


def _detect_cable_dropped_l_excl(state, info, K, l_excl_per_world):
    """L-exclusive cable drop detection (mirrors newton_aerial_regrasp_env.py:877-879).

    Checks cable_z_min only over segments exclusive to L arm target window.
    Avoids false positives from R-arm contact sag on L-R overlap region.

    Args:
        l_excl_per_world: list of length K, each an int array of l_excl indices.
    """
    assert state.body_q.numpy().dtype == np.float32, "body_q must be float32 for safe view"
    bq = state.body_q.numpy()
    flat = bq.view(np.float32).reshape(-1, 7)
    bws = info["bws"]
    co = info["cable_offset"]
    cpw = info["cable_per_world"]
    dropped = np.zeros(K, dtype=bool)
    for w in range(K):
        excl = l_excl_per_world[w]
        if len(excl) == 0:
            continue
        start = bws[w] + co
        cable_z_l_excl = flat[start + excl, 2]
        if cable_z_l_excl.min() < CABLE_DROP_Z_THR:
            dropped[w] = True
    return dropped


def rollout_and_cost_ar(
    model, solver_vbd, state_0, state_1, control,
    actions_seq, ik_solver, per_world_jq, info, K, H, cfg,
    ik_target_L_pos_fixed, ik_target_L_quat_fixed,
    ik_target_quat_R_init,
    target_seg_indices_r,
    l_excl_per_world,
):
    """Rollout K trajectories for H steps; compute AR cost.

    Cost (FM-5 + FM-2): max(pos_dist_R, AR_COST_SCALE*ori_dist_R) + P_DROP*I(drop_l_excl)

    Pos reference: R fingertip (clamp_pos = ee + quat_rotate(ee_quat, [0,0,EE_TO_FINGERTIP])).
    R target: per-world `find_nearest_cable_point` within target_seg_indices_r window.
    L arm IK target FIXED at settled precondition pose (Q1=(ii) frozen FK).
    Action layout R-first (AR env: [0:3]=R_pos, [3:6]=R_ori, [6:9]=L_pos, [9:12]=L_ori).

    Returns:
        costs (K,) float32, nan_count, t_ik, t_phys, ee_spread_max_R, drop_count.
    """
    sim_dt = DT / RL_SIM_SUBSTEPS
    costs = np.zeros(K, dtype=np.float32)
    jq = per_world_jq.copy()
    t_ik_total = 0.0
    t_physics_total = 0.0
    nan_mask = np.zeros(K, dtype=bool)
    ee_spread_max_right = 0.0

    tgt_L_pos_all = np.tile(ik_target_L_pos_fixed[None].astype(np.float32), (K, 1))
    tgt_L_quat_all = np.tile(ik_target_L_quat_fixed[None].astype(np.float32), (K, 1))
    ik_tgt_R = np.tile(ik_target_quat_R_init[None].astype(np.float32), (K, 1))

    for h in range(H):
        # Current R EE pos for action delta reference (pre-IK).
        (_, _), (right_ee, _) = get_ee_poses_dual(state_0, info, K)

        # R-first action layout (matches AR env): [0:3]=R_pos, [3:6]=R_ori, [6:9]=L_pos, [9:12]=L_ori.
        R_pos_delta = actions_seq[:, h, 0:3] * cfg.pos_action_scale
        R_ori_delta = actions_seq[:, h, 3:6] * cfg.rot_action_scale

        target_R_pos = right_ee + R_pos_delta

        for k in range(K):
            q_dR = _axis_angle_to_quat_xyzw(R_ori_delta[k])
            ik_tgt_R[k] = _quat_multiply_xyzw(q_dR, ik_tgt_R[k])
            ik_tgt_R[k] = ik_tgt_R[k] / np.linalg.norm(ik_tgt_R[k])

        t0_ik = time.perf_counter()
        jq_solved = ik_solver.solve(tgt_L_pos_all, tgt_L_quat_all, target_R_pos, ik_tgt_R, jq)

        jq_solved[:, 7] = FINGER_CLOSE_POS
        jq_solved[:, 8] = FINGER_CLOSE_POS
        jq_solved[:, FRANKA_NUM_JOINTS + 7] = FINGER_OPEN_POS
        jq_solved[:, FRANKA_NUM_JOINTS + 8] = FINGER_OPEN_POS

        fk_body_q = ik_solver.eval_fk_batch(jq_solved)
        t_ik_total += time.perf_counter() - t0_ik

        update_kinematic_bodies(state_0, fk_body_q, info, K)

        (_, _), (ik_right, _) = get_ee_poses_dual(state_0, info, K)
        valid_idx = ~nan_mask
        if valid_idx.sum() > 1:
            ee_spread_max_right = max(
                ee_spread_max_right,
                float(np.sqrt(np.sum(np.var(ik_right[valid_idx], axis=0)))),
            )

        t0_phys = time.perf_counter()
        contacts = model.collide(state_0)
        for _ in range(RL_SIM_SUBSTEPS):
            solver_vbd.step(state_0, state_1, control, contacts, sim_dt)
            state_0, state_1 = state_1, state_0
        t_physics_total += time.perf_counter() - t0_phys

        bq_check = state_0.body_q.numpy()
        bpw = info["bodies_per_world"]
        bws = info["bws"]
        co = info["cable_offset"]
        cpw = info["cable_per_world"]
        for w in range(K):
            if not nan_mask[w]:
                s = bws[w]
                chunk = bq_check[s : s + bpw]
                if np.any(np.isnan(chunk)) or np.any(np.isinf(chunk)):
                    nan_mask[w] = True
                    costs[w] = 1e6

        # Achieved R pose post-physics; compute clamp_pos (fingertip) per world.
        (_, _), (achieved_pos_R, achieved_quat_R) = get_ee_poses_dual(state_0, info, K)
        flat = bq_check.view(np.float32).reshape(-1, 7)

        pos_dist_R = np.zeros(K, dtype=np.float32)
        ori_dist_R = np.zeros(K, dtype=np.float32)
        for w in range(K):
            if nan_mask[w]:
                continue
            q_R = _normalize_quat_w_positive(achieved_quat_R[w])
            clamp_R = compute_clamp_pos(achieved_pos_R[w], q_R)
            ws = bws[w]
            cable_pos = flat[ws + co : ws + co + cpw, :3]
            seg_pos, seg_tangent, dist = find_nearest_cable_point(
                cable_pos, clamp_R, target_seg_indices_r[w],
            )
            pos_dist_R[w] = dist
            cost_target_quat_w = _normalize_quat_w_positive(
                np.asarray(compute_hand_quat_for_cable(seg_tangent), dtype=np.float32),
            )
            ori_dist_R[w] = _quat_distance(q_R, cost_target_quat_w)

        dropped = _detect_cable_dropped_l_excl(state_0, info, K, l_excl_per_world)
        drop_penalty = np.where(dropped, P_DROP, 0.0).astype(np.float32)

        step_cost = np.maximum(pos_dist_R, cfg.ar_cost_scale * ori_dist_R).astype(np.float32) + drop_penalty
        costs += np.where(nan_mask, 0.0, step_cost)

        jq = jq_solved.copy()

    drop_count = int(_detect_cable_dropped_l_excl(state_0, info, K, l_excl_per_world).sum())

    return (
        costs, int(nan_mask.sum()), t_ik_total, t_physics_total, ee_spread_max_right,
        drop_count,
    )


# =========================================================================
# AR MPPI main loop: K_sustain=5, HOLD_W controls L-action noise sigma
# =========================================================================


def mppi_generate_demos_ar(
    cfg, hold_w, device,
    max_steps=128, n_demos=5, seed=42,
    diag_csv_path="/tmp/mppi_ar_metrics.csv",
    l_ori_weight=0.5, r_ori_weight=0.5,
):
    """Generate M3-AR aerial-regrasp demos with 12D MPPI + K_sustain=5 success.

    Returns:
        demos: list of per-episode dicts with trajectories + AR metrics.
        drifts_per_episode_max: per-episode max L-EE drift [m] for Gate 6.
        cable_L/R_endpoint_mean: per-episode seg 0 / seg last mean positions.
    """
    K = cfg.K
    H = cfg.H

    rng = np.random.default_rng(seed)

    print(f"\n[MPPI-AR] {AR_VERSION} Building AR precondition K={K} HOLD_W={hold_w}...")
    fk_model, fk_state, scene = build_ar_precondition(K, device)

    info = base_scene_to_m2_info(scene)
    model = scene["model"]
    solver_vbd = scene["solver"]
    state_0 = scene["state_0"]
    state_1 = scene["state_1"]
    control = scene["control"]

    ik_solver = MppiIKSolverM3(fk_model, K, device, l_ori_weight=l_ori_weight, r_ori_weight=r_ori_weight)

    coord_count = fk_model.joint_coord_count

    # Snapshot precondition state as episode reset state.
    init_body_q = state_0.body_q.numpy().copy()
    init_body_qd = state_0.body_qd.numpy().copy()
    init_fk_jq = fk_state.joint_q.numpy().copy()

    # Precondition-end L/R EE pose: L target frozen here throughout MPPI (Q1=(ii)).
    (left_pos0, left_quat0), (right_pos0, right_quat0) = get_ee_poses_dual(state_0, info, 1)
    ik_target_L_pos_fixed = left_pos0[0].copy().astype(np.float32)
    ik_target_L_quat_fixed = _normalize_quat_w_positive(left_quat0[0]).astype(np.float32)

    demos = []
    drifts_per_episode_max = []
    cable_endpoints_L = []
    cable_endpoints_R = []

    diag_file = open(diag_csv_path, "w", newline="")  # noqa: SIM115
    diag_csv = csv.writer(diag_file)
    diag_csv.writerow([
        "episode", "step", "nan_count", "k_eff", "weight_entropy", "weight_mass_valid",
        "top1_weight", "best_action_nan", "plan_time_s",
        "cost_min", "cost_max", "cost_range", "cost_std",
        "ee_spread_max_mm", "drop_count", "sustain_count",
    ])
    print(f"[DIAG] CSV -> {diag_csv_path}")

    per_world_jq_init = np.tile(init_fk_jq[:coord_count], (K, 1))

    # Per-world target seg indices (computed once from precondition, mirrors AR env reset).
    target_seg_indices_r, target_seg_indices_l = _compute_ar_target_seg_indices(state_0, info, K)
    l_excl_per_world = [
        np.setdiff1d(target_seg_indices_l[w], target_seg_indices_r[w]) for w in range(K)
    ]
    print(
        f"[MPPI-AR] Target seg indices w0: R={target_seg_indices_r[0].tolist()}  "
        f"L={target_seg_indices_l[0].tolist()}  l_excl={l_excl_per_world[0].tolist()}"
    )

    for ep in range(n_demos):
        print(f"\n[MPPI-AR] Episode {ep + 1}/{n_demos}")

        # Reset to precondition state.
        state_0.body_q.assign(init_body_q)
        state_0.body_qd.assign(init_body_qd)
        solver_vbd.body_q_prev = wp.clone(state_0.body_q)
        per_world_jq = per_world_jq_init.copy()

        # IK target R: initial = current R EE quat (accumulates via action deltas).
        ik_target_quat_R = _normalize_quat_w_positive(right_quat0[0]).astype(np.float32)

        cable_ep_L_reset, cable_ep_R_reset = compute_cable_endpoint_pos(state_0, info, 1)
        cable_endpoints_L.append(cable_ep_L_reset[0].astype(np.float32).copy())
        cable_endpoints_R.append(cable_ep_R_reset[0].astype(np.float32).copy())

        traj_left_pos, traj_right_pos = [], []
        traj_left_quat, traj_right_quat = [], []
        traj_actions = []
        traj_dist_pos_L, traj_dist_pos_R = [], []
        traj_dist_ori_L, traj_dist_ori_R = [], []
        traj_cable_pos = []
        traj_l_drift = []
        traj_cable_dropped = []

        step = 0
        sustain_count = 0
        success = False
        last_cost_target_quat_R = None  # recomputed per plan

        while step < max_steps:
            copy_world0_to_all(state_0, info["bws"], info["bodies_per_world"], K, device, solver_vbd=solver_vbd)
            per_world_jq[:] = per_world_jq[0:1]

            # Save state for restore after rollout.
            saved_q = state_0.body_q.numpy().copy()
            saved_qd = state_0.body_qd.numpy().copy()
            saved_bq_prev = solver_vbd.body_q_prev.numpy().copy()
            saved_jq = per_world_jq.copy()
            saved_ik_tgt_R = ik_target_quat_R.copy()

            # Sample K action sequences (12D). HOLD_W scales L components (idx 6:12, R-first layout).
            actions = sample_action_sequences(K, H, M3_ACTION_DIM, cfg.noise_sigma, cfg.noise_correlation, rng)
            actions[:, :, 6:12] *= hold_w

            t0_plan = time.perf_counter()
            (
                costs, nan_count, t_ik, t_phys, ee_spread_max, drop_count,
            ) = rollout_and_cost_ar(
                model, solver_vbd, state_0, state_1, control,
                actions, ik_solver, per_world_jq, info, K, H, cfg,
                ik_target_L_pos_fixed, ik_target_L_quat_fixed,
                ik_target_quat_R,
                target_seg_indices_r,
                l_excl_per_world,
            )
            t_plan = time.perf_counter() - t0_plan

            if step == 0:
                print(
                    f"  [TIMING] plan={t_plan:.2f}s (IK={t_ik:.2f}s phys={t_phys:.2f}s)  "
                    f"drop_count={drop_count}/{K}"
                )

            weights = mppi_weights(costs, cfg.temperature_lambda)
            best_actions = np.einsum("k,kha->ha", weights, actions)

            valid_costs = costs[costs < 1e5]
            if len(valid_costs) > 1:
                c_min = float(valid_costs.min())
                c_max = float(valid_costs.max())
                c_range = c_max - c_min
                c_std = float(valid_costs.std())
            else:
                c_min = c_max = c_range = c_std = 0.0

            k_eff = K - nan_count
            valid_mask = costs < 1e5
            w_valid = weights[valid_mask]
            if len(w_valid) > 0:
                w_entropy = -np.sum(w_valid * np.log(w_valid + 1e-30))
                w_mass_valid = float(w_valid.sum())
                top1_w = float(w_valid.max())
            else:
                w_entropy = 0.0
                w_mass_valid = 0.0
                top1_w = 0.0
            ba_has_nan = bool(np.any(np.isnan(best_actions)) or np.any(np.isinf(best_actions)))

            diag_csv.writerow([
                ep, step, nan_count, k_eff,
                f"{w_entropy:.4f}", f"{w_mass_valid:.6f}", f"{top1_w:.6f}", int(ba_has_nan),
                f"{t_plan:.3f}",
                f"{c_min:.4f}", f"{c_max:.4f}", f"{c_range:.4f}", f"{c_std:.4f}",
                f"{ee_spread_max * 1000:.2f}", drop_count, sustain_count,
            ])
            if step % 16 == 0:
                print(
                    f"  [DIAG] step={step} nan={nan_count}/{K} k_eff={k_eff} "
                    f"entropy={w_entropy:.2f} cost_range={c_range:.4f} sustain={sustain_count}"
                )

            # Restore state for execute.
            state_0.body_q.assign(saved_q)
            state_0.body_qd.assign(saved_qd)
            solver_vbd.body_q_prev.assign(saved_bq_prev)
            per_world_jq = saved_jq.copy()
            ik_target_quat_R = saved_ik_tgt_R.copy()

            # Execute first REPLAN_INTERVAL steps on world 0.
            n_exec = min(REPLAN_INTERVAL, max_steps - step)
            sim_dt = DT / RL_SIM_SUBSTEPS

            for h in range(n_exec):
                (_, _), (right_ee_now, _) = get_ee_poses_dual(state_0, info, 1)

                # R-first action layout: [0:3]=R_pos, [3:6]=R_ori, [6:9]=L_pos, [9:12]=L_ori.
                R_pos_delta = best_actions[h, 0:3] * cfg.pos_action_scale
                R_ori_delta = best_actions[h, 3:6] * cfg.rot_action_scale
                # L action deltas recorded via traj_actions (raw best_actions) but NOT applied to IK target.

                target_R_pos = right_ee_now[0] + R_pos_delta

                # R IK target accumulate.
                q_dR = _axis_angle_to_quat_xyzw(R_ori_delta)
                ik_target_quat_R = _quat_multiply_xyzw(q_dR, ik_target_quat_R)
                ik_target_quat_R = ik_target_quat_R / np.linalg.norm(ik_target_quat_R)

                # K tile (only idx 0 used after physics).
                jq_all = np.tile(per_world_jq[0:1], (K, 1))
                tgt_L_pos_all = np.tile(ik_target_L_pos_fixed[None].astype(np.float32), (K, 1))
                tgt_L_quat_all = np.tile(ik_target_L_quat_fixed[None].astype(np.float32), (K, 1))
                tgt_R_pos_all = np.tile(target_R_pos[None].astype(np.float32), (K, 1))
                tgt_R_quat_all = np.tile(ik_target_quat_R[None].astype(np.float32), (K, 1))

                jq_solved = ik_solver.solve(tgt_L_pos_all, tgt_L_quat_all, tgt_R_pos_all, tgt_R_quat_all, jq_all)
                jq_solved[:, 7] = FINGER_CLOSE_POS
                jq_solved[:, 8] = FINGER_CLOSE_POS
                jq_solved[:, FRANKA_NUM_JOINTS + 7] = FINGER_OPEN_POS
                jq_solved[:, FRANKA_NUM_JOINTS + 8] = FINGER_OPEN_POS

                fk_body_q = ik_solver.eval_fk_batch(jq_solved)
                update_kinematic_bodies(state_0, fk_body_q, info, K)

                contacts = model.collide(state_0)
                for _ in range(RL_SIM_SUBSTEPS):
                    solver_vbd.step(state_0, state_1, control, contacts, sim_dt)
                    state_0, state_1 = state_1, state_0

                per_world_jq[0] = jq_solved[0]

                # Post-physics measurements (world 0): clamp_pos + find_nearest_cable_point.
                (new_L_pos, new_L_quat), (new_R_pos, new_R_quat) = get_ee_poses_dual(state_0, info, 1)
                q2_L = _normalize_quat_w_positive(new_L_quat[0])
                q2_R = _normalize_quat_w_positive(new_R_quat[0])
                clamp_L = compute_clamp_pos(new_L_pos[0], q2_L)
                clamp_R = compute_clamp_pos(new_R_pos[0], q2_R)

                bq_flat = state_0.body_q.numpy().view(np.float32).reshape(-1, 7)
                _bws0 = info["bws"][0]
                _co = info["cable_offset"]
                _cpw = info["cable_per_world"]
                cable_pos_w0 = bq_flat[_bws0 + _co : _bws0 + _co + _cpw, :3]

                seg_pos_r, seg_tangent_r, dpr = find_nearest_cable_point(
                    cable_pos_w0, clamp_R, target_seg_indices_r[0],
                )
                cost_target_quat_R_step = _normalize_quat_w_positive(
                    np.asarray(compute_hand_quat_for_cable(seg_tangent_r), dtype=np.float32),
                )
                dor = float(_quat_distance(q2_R, cost_target_quat_R_step))
                seg_pos_l, _, dpl = find_nearest_cable_point(
                    cable_pos_w0, clamp_L, target_seg_indices_l[0],
                )
                dol = float(_quat_distance(q2_L, ik_target_L_quat_fixed))  # L vs frozen target

                l_drift = float(np.linalg.norm(new_L_pos[0] - ik_target_L_pos_fixed))
                # L-exclusive cable drop (v38 alignment).
                l_excl_w0 = l_excl_per_world[0]
                cable_dropped_w0 = bool(
                    len(l_excl_w0) > 0
                    and cable_pos_w0[l_excl_w0, 2].min() < CABLE_DROP_Z_THR
                )
                last_cost_target_quat_R = cost_target_quat_R_step

                traj_left_pos.append(new_L_pos[0].copy())
                traj_right_pos.append(new_R_pos[0].copy())
                traj_left_quat.append(q2_L)
                traj_right_quat.append(q2_R)
                traj_actions.append(best_actions[h].astype(np.float32).copy())
                traj_dist_pos_L.append(dpl)
                traj_dist_pos_R.append(dpr)
                traj_dist_ori_L.append(dol)
                traj_dist_ori_R.append(dor)
                traj_l_drift.append(l_drift)
                traj_cable_dropped.append(cable_dropped_w0)
                _bq_now = state_0.body_q.numpy()
                _co = info["cable_offset"]
                _cpw = info["cable_per_world"]
                _bws0 = info["bws"][0]
                traj_cable_pos.append(_bq_now[_bws0 + _co : _bws0 + _co + _cpw, :3].astype(np.float32).copy())

                # K_SUSTAIN success check (Q5 approved).
                r_success = (
                    dpr < AR_POS_THR_M
                    and dor < AR_ORI_THR_RAD
                    and not cable_dropped_w0
                )
                if r_success:
                    sustain_count += 1
                    if sustain_count >= K_SUSTAIN:
                        success = True
                        print(
                            f"  SUCCESS at step {step + 1} (sustained {K_SUSTAIN}), "
                            f"R pos={dpr * 1000:.1f}mm ori={math.degrees(dor):.1f}deg "
                            f"L drift={l_drift * 1000:.1f}mm"
                        )
                        step += 1
                        break
                else:
                    sustain_count = 0  # reset on failure

                step += 1

            if success:
                break

        if not success:
            if traj_dist_pos_R:
                print(
                    f"  FAILED at step {step}, R pos={traj_dist_pos_R[-1] * 1000:.1f}mm "
                    f"ori={math.degrees(traj_dist_ori_R[-1]):.1f}deg "
                    f"sustain={sustain_count}/{K_SUSTAIN}"
                )
            else:
                print("  FAILED (no steps)")

        # R-first layout: L action indices are [6:12].
        l_action_rms = (
            float(np.sqrt(np.mean(np.square(np.asarray(traj_actions, dtype=np.float32)[:, 6:12]))))
            if traj_actions else 0.0
        )
        demo = {
            "left_ee_pos": np.array(traj_left_pos, dtype=np.float32),
            "right_ee_pos": np.array(traj_right_pos, dtype=np.float32),
            "left_ee_quat": np.array(traj_left_quat, dtype=np.float32),
            "right_ee_quat": np.array(traj_right_quat, dtype=np.float32),
            "actions": np.array(traj_actions, dtype=np.float32),
            "dist_pos_left": np.array(traj_dist_pos_L, dtype=np.float32),
            "dist_pos_right": np.array(traj_dist_pos_R, dtype=np.float32),
            "dist_ori_left": np.array(traj_dist_ori_L, dtype=np.float32),
            "dist_ori_right": np.array(traj_dist_ori_R, dtype=np.float32),
            "l_drift": np.array(traj_l_drift, dtype=np.float32),
            "cable_dropped": np.array(traj_cable_dropped, dtype=bool),
            "cable_pos_seq": (
                np.array(traj_cable_pos, dtype=np.float32)
                if traj_cable_pos else np.zeros((0, 0, 3), dtype=np.float32)
            ),
            "success": success,
            "steps": step,
            "l_action_rms": l_action_rms,
            "cost_target_quat_right_last": (
                last_cost_target_quat_R.copy() if last_cost_target_quat_R is not None
                else np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
            ),
        }
        demos.append(demo)
        drifts_per_episode_max.append(float(max(traj_l_drift)) if traj_l_drift else 0.0)

    diag_file.close()
    print(f"[DIAG] CSV written -> {diag_csv_path}")

    if cable_endpoints_L:
        cable_L_endpoint_mean = np.mean(cable_endpoints_L, axis=0).astype(np.float32)
        cable_R_endpoint_mean = np.mean(cable_endpoints_R, axis=0).astype(np.float32)
    else:
        cable_L_endpoint_mean = cable_R_endpoint_mean = None

    return (demos, drifts_per_episode_max, cable_L_endpoint_mean, cable_R_endpoint_mean)


# =========================================================================
# HDF5 + metrics save
# =========================================================================


def compute_ar_success_rates(demos):
    """S1_pos_R (pos<12mm), S2_ori_R (ori<10deg), S3_combined (both AND sustain)."""
    if not demos:
        return {"s1": 0.0, "s2": 0.0, "s3": 0.0}
    n1 = n2 = n3 = 0
    for d in demos:
        dpr = d["dist_pos_right"]
        dor = d["dist_ori_right"]
        if len(dpr) == 0:
            continue
        pos_ok = dpr[-1] < AR_POS_THR_M
        ori_ok = dor[-1] < AR_ORI_THR_RAD
        if pos_ok:
            n1 += 1
        if ori_ok:
            n2 += 1
        if d["success"]:  # success already includes K_SUSTAIN and not-dropped
            n3 += 1
    n = len(demos)
    return {"s1": n1 / n, "s2": n2 / n, "s3": n3 / n}


def save_demos_hdf5_ar(demos, cfg, hold_w, output_path, cable_L_endpoint_mean=None, cable_R_endpoint_mean=None):
    """Save M3-AR demos to HDF5 (pos+quat + cable_pos_seq + AR metrics)."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    n_success = sum(1 for d in demos if d["success"])

    with h5py.File(output_path, "w") as f:
        meta = f.create_group("metadata")
        meta.attrs["generator"] = "mppi_m3_ar"
        meta.attrs["ar_version"] = AR_VERSION
        meta.attrs["K"] = cfg.K
        meta.attrs["H"] = cfg.H
        meta.attrs["hold_w"] = hold_w
        meta.attrs["temperature_lambda"] = cfg.temperature_lambda
        meta.attrs["noise_sigma"] = cfg.noise_sigma
        meta.attrs["noise_correlation"] = cfg.noise_correlation
        meta.attrs["success_threshold_m"] = cfg.success_threshold_m
        meta.attrs["success_threshold_rad"] = cfg.success_threshold_rad
        meta.attrs["success_eval"] = "R_pos_AND_R_ori_AND_K_sustain"
        meta.attrs["K_SUSTAIN"] = K_SUSTAIN
        meta.attrs["P_DROP"] = P_DROP
        meta.attrs["AR_COST_SCALE"] = cfg.ar_cost_scale
        meta.attrs["CABLE_DROP_Z_THR"] = CABLE_DROP_Z_THR
        meta.attrs["DRIFT_CAP"] = DRIFT_CAP
        meta.attrs["action_dim"] = M3_ACTION_DIM
        meta.attrs["action_layout"] = "R-first"  # AR-compat: [0:3]=R_pos, [3:6]=R_ori, [6:9]=L_pos, [9:12]=L_ori
        meta.attrs["quat_convention"] = M3_QUAT_CONVENTION
        meta.attrs["quat_frame"] = M3_QUAT_FRAME
        meta.attrs["quat_semantic"] = M3_QUAT_SEMANTIC
        meta.attrs["cost_method"] = AR_COST_METHOD
        meta.attrs["l_arm_strategy"] = "frozen_FK_Q1ii"
        meta.attrs["pos_action_scale"] = cfg.pos_action_scale
        meta.attrs["rot_action_scale"] = cfg.rot_action_scale
        meta.attrs["newton_dt"] = cfg.newton_dt
        meta.attrs["sim_substeps"] = cfg.sim_substeps
        meta.attrs["replan_interval"] = REPLAN_INTERVAL
        meta.attrs["n_demos"] = len(demos)
        meta.attrs["n_success"] = n_success
        if cable_L_endpoint_mean is not None:
            meta.attrs["cable_L_endpoint_mean"] = np.asarray(cable_L_endpoint_mean, dtype=np.float32)
        if cable_R_endpoint_mean is not None:
            meta.attrs["cable_R_endpoint_mean"] = np.asarray(cable_R_endpoint_mean, dtype=np.float32)

        for i, demo in enumerate(demos):
            g = f.create_group(f"episode_{i}")
            g.create_dataset("left_ee_pos", data=demo["left_ee_pos"])
            g.create_dataset("right_ee_pos", data=demo["right_ee_pos"])
            g.create_dataset("left_ee_quat", data=demo["left_ee_quat"])
            g.create_dataset("right_ee_quat", data=demo["right_ee_quat"])
            g.create_dataset("action_delta", data=demo["actions"])
            g.create_dataset("dist_pos_left", data=demo["dist_pos_left"])
            g.create_dataset("dist_pos_right", data=demo["dist_pos_right"])
            g.create_dataset("dist_ori_left", data=demo["dist_ori_left"])
            g.create_dataset("dist_ori_right", data=demo["dist_ori_right"])
            g.create_dataset("l_drift", data=demo["l_drift"])
            g.create_dataset("cable_dropped", data=demo["cable_dropped"])
            if demo["cable_pos_seq"].size > 0:
                g.create_dataset("cable_pos_seq", data=demo["cable_pos_seq"], compression="gzip")
            g.attrs["success"] = demo["success"]
            g.attrs["steps"] = demo["steps"]
            g.attrs["l_action_rms"] = demo["l_action_rms"]
            g.attrs["cost_target_quat_right_last"] = demo["cost_target_quat_right_last"]

    print(f"[HDF5-AR] Saved {len(demos)} demos ({n_success} success) -> {output_path}")


def save_run_metrics_json_ar(demos, drifts_per_episode_max, wall_clock_s, cfg, hold_w, output_dir):
    """Write per-(lambda, hold_w) RUN_METRICS JSON (AR variant)."""
    rates = compute_ar_success_rates(demos)

    ep_max_arr = np.asarray(drifts_per_episode_max, dtype=np.float64)
    n_viol = int(np.sum(ep_max_arr > DRIFT_CAP)) if ep_max_arr.size else 0
    n_ep = int(len(ep_max_arr))
    drift_violation = {
        "drift_cap_m": DRIFT_CAP,
        "violation_count": n_viol,
        "total_episodes": n_ep,
        "violation_rate": n_viol / n_ep if n_ep > 0 else 0.0,
        "per_episode_max": ep_max_arr.tolist() if ep_max_arr.size else [],
    }

    l_rms_arr = np.asarray([d["l_action_rms"] for d in demos], dtype=np.float64)
    s7 = {
        "target": 0.30,
        "mean": float(l_rms_arr.mean()) if l_rms_arr.size else 0.0,
        "pass_count": int(np.sum(l_rms_arr >= 0.30)),
        "per_demo": l_rms_arr.tolist(),
    }

    metrics = {
        "schema_version": "v1",
        "ar_version": AR_VERSION,
        "lambda": float(cfg.temperature_lambda),
        "hold_w": float(hold_w),
        "n_demos": len(demos),
        "wall_clock_s": float(wall_clock_s),
        "S1_pos_R_rate": rates["s1"],
        "S2_ori_R_rate": rates["s2"],
        "S3_combined_sustain_rate": rates["s3"],
        "S7_L_action_rms": s7,
        "drift_violation": drift_violation,
        "cost_threshold_m": AR_POS_THR_M,
        "cost_threshold_rad": AR_ORI_THR_RAD,
        "cost_method": AR_COST_METHOD,
        "ar_cost_scale": cfg.ar_cost_scale,
        "p_drop": P_DROP,
        "k_sustain": K_SUSTAIN,
    }

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"run_metrics_lam{cfg.temperature_lambda}_hw{hold_w}.json")
    with open(out_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[RUN_METRICS-AR] {out_path}")
    return metrics


# =========================================================================
# CLI main
# =========================================================================


def main():
    parser = argparse.ArgumentParser(description=f"MPPI demo generation M3-AR aerial-regrasp variant ({AR_VERSION})")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--world-count", type=int, default=256, help="K worlds (=cfg.K)")
    parser.add_argument("--single-lambda", type=float, default=0.3)
    parser.add_argument("--sweep", action="store_true", help="Lambda sweep [0.3, 0.5, 1.0]")
    parser.add_argument("--hold-w", type=float, default=0.2, help="L-action noise sigma scale (F7 sweep {0.1, 0.2, 0.4})")
    parser.add_argument("--hold-w-sweep", action="store_true", help="HOLD_W sweep [0.1, 0.2, 0.4] x lambda")
    parser.add_argument("--n-demos", type=int, default=5)
    parser.add_argument("--max-steps", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=str, default="data/mppi_demos_m3_ar")
    parser.add_argument("--diag-csv", type=str, default="/tmp/mppi_ar_metrics.csv")
    # Phase 0 (2026-04-21) AR Gate 5a retune sweep: R1/R2/R3 parameters
    parser.add_argument("--ar-cost-scale", type=float, default=None,
                        help="R1: override cfg.ar_cost_scale (baseline 0.0688)")
    parser.add_argument("--r-ori-weight", type=float, default=0.5,
                        help="R2: MppiIKSolverM3 R_ori objective weight (baseline 0.5)")
    parser.add_argument("--rot-action-scale", type=float, default=None,
                        help="R3: override cfg.rot_action_scale (baseline 0.05)")
    parser.add_argument("--phase1-sweep", action="store_true",
                        help="Phase 0 27-cell R1xR2xR3 sweep (AR Gate 5a retune); lambda=0.3, hold_w=0.2 fixed")
    args = parser.parse_args()

    wp.init()
    wp.set_device(args.device)

    # Phase 0 sweep overrides other sweep modes: fix lambda=0.3, hold_w=0.2 (F7 best-ori), vary R1/R2/R3.
    if args.phase1_sweep:
        phase1_cost_vals = [0.15, 0.20, 0.30]
        phase1_oriw_vals = [0.75, 1.0, 1.5]
        phase1_rot_vals = [0.08, 0.10, 0.15]
        lambdas = [0.3]
        hold_ws = [0.2]
    else:
        lambdas = [0.3, 0.5, 1.0] if args.sweep else [args.single_lambda]
        hold_ws = [0.1, 0.2, 0.4] if args.hold_w_sweep else [args.hold_w]

    sweep_results = []
    cost_scale_iter = phase1_cost_vals if args.phase1_sweep else [args.ar_cost_scale]
    oriw_iter = phase1_oriw_vals if args.phase1_sweep else [args.r_ori_weight]
    rot_iter = phase1_rot_vals if args.phase1_sweep else [args.rot_action_scale]

    for lam in lambdas:
        for hw in hold_ws:
            for cost_override in cost_scale_iter:
                for oriw in oriw_iter:
                    for rot_override in rot_iter:
                        print(f"\n{'=' * 60}")
                        if args.phase1_sweep:
                            print(f"  [P0] cost={cost_override}  oriW={oriw}  rot={rot_override}  lam={lam}  hw={hw}  K={args.world_count}")
                        else:
                            print(f"  lambda={lam}  HOLD_W={hw}  K={args.world_count}")
                        print(f"{'=' * 60}")

                        cfg = MPPIConfigAR()
                        cfg.temperature_lambda = lam
                        cfg.K = args.world_count
                        cfg.world_count = args.world_count
                        cfg.device = args.device
                        if cost_override is not None:
                            cfg.ar_cost_scale = cost_override
                        if rot_override is not None:
                            cfg.rot_action_scale = rot_override

                        if args.phase1_sweep:
                            suffix = f"_p0_cost{cost_override}_ow{oriw}_rot{rot_override}"
                            diag_csv = f"/tmp/mppi_ar_p0{suffix}.csv"
                            output_dir = os.path.join(args.output_dir, "phase1_sweep")
                        else:
                            suffix = f"_l{lam}_hw{hw}"
                            diag_csv = f"/tmp/mppi_ar_lam{lam}_hw{hw}.csv"
                            output_dir = args.output_dir

                        t0 = time.perf_counter()
                        (demos, drifts_per_ep_max, cable_L_mean, cable_R_mean) = mppi_generate_demos_ar(
                            cfg, hw, args.device,
                            max_steps=args.max_steps, n_demos=args.n_demos, seed=args.seed,
                            diag_csv_path=diag_csv,
                            l_ori_weight=oriw, r_ori_weight=oriw,
                        )
                        elapsed = time.perf_counter() - t0

                        h5_path = os.path.join(output_dir, f"demos{suffix}.hdf5")
                        save_demos_hdf5_ar(demos, cfg, hw, h5_path, cable_L_mean, cable_R_mean)
                        metrics = save_run_metrics_json_ar(demos, drifts_per_ep_max, elapsed, cfg, hw, output_dir)

                        n_success = sum(1 for d in demos if d["success"])
                        result_entry = {
                            "lambda": lam, "hold_w": hw,
                            "n_demos": len(demos), "n_success": n_success,
                            "S1_pos_R": metrics["S1_pos_R_rate"],
                            "S2_ori_R": metrics["S2_ori_R_rate"],
                            "S3": metrics["S3_combined_sustain_rate"],
                            "S7_L_rms_mean": metrics["S7_L_action_rms"]["mean"],
                            "drift_violation_rate": metrics["drift_violation"]["violation_rate"],
                            "wall_clock_s": round(elapsed, 1),
                        }
                        if args.phase1_sweep:
                            result_entry["ar_cost_scale"] = cost_override
                            result_entry["r_ori_weight"] = oriw
                            result_entry["rot_action_scale"] = rot_override
                        sweep_results.append(result_entry)

    # Sweep summary + CSV.
    if args.sweep or args.hold_w_sweep or args.phase1_sweep:
        print(f"\n{'=' * 90}\n  M3-AR SWEEP RESULTS\n{'=' * 90}")
        if args.phase1_sweep:
            hdr = f"  {'cost':>6} {'oriW':>5} {'rot':>6} {'S1':>6} {'S2':>6} {'S3':>6} {'L_rms':>7} {'t_s':>7}"
            print(hdr)
            print(f"  {'-' * (len(hdr) - 2)}")
            for r in sweep_results:
                print(
                    f"  {r['ar_cost_scale']:>6.2f} {r['r_ori_weight']:>5.2f} {r['rot_action_scale']:>6.2f} "
                    f"{r['S1_pos_R']:>6.1%} {r['S2_ori_R']:>6.1%} {r['S3']:>6.1%} "
                    f"{r['S7_L_rms_mean']:>7.3f} {r['wall_clock_s']:>7.1f}"
                )
            csv_path = "/tmp/mppi_ar_phase1_sweep.csv"
        else:
            hdr = f"  {'lam':>6} {'hw':>5} {'n':>4} {'succ':>5} {'S1':>6} {'S2':>6} {'S3':>6} {'L_rms':>7} {'dviol':>6} {'t_s':>7}"
            print(hdr)
            print(f"  {'-' * (len(hdr) - 2)}")
            for r in sweep_results:
                print(
                    f"  {r['lambda']:>6.1f} {r['hold_w']:>5.1f} {r['n_demos']:>4d} {r['n_success']:>5d} "
                    f"{r['S1_pos_R']:>6.1%} {r['S2_ori_R']:>6.1%} {r['S3']:>6.1%} "
                    f"{r['S7_L_rms_mean']:>7.3f} {r['drift_violation_rate']:>6.1%} {r['wall_clock_s']:>7.1f}"
                )
            csv_path = "/tmp/mppi_ar_sweep.csv"
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(sweep_results[0].keys()))
            w.writeheader()
            w.writerows(sweep_results)
        print(f"\n  CSV: {csv_path}")
        if args.phase1_sweep:
            best = max(sweep_results, key=lambda r: r["S3"])
            print(f"\n  [PHASE 0 BEST] S3={best['S3']:.1%} at cost={best['ar_cost_scale']} oriW={best['r_ori_weight']} rot={best['rot_action_scale']}")
            pass_cells = [r for r in sweep_results if r["S3"] >= 0.60]
            print(f"  [GATE 5a PASS cells] {len(pass_cells)}/{len(sweep_results)}")

    # Single-config S3 + drift gate check (F6 calibration).
    if not args.sweep and not args.hold_w_sweep and not args.phase1_sweep and len(sweep_results) == 1:
        s3 = sweep_results[0]["S3"]
        dv = sweep_results[0]["drift_violation_rate"]
        s3_fail = s3 < 0.60
        drift_fail = dv >= DRIFT_VIOLATION_RATE_LIMIT
        if s3_fail or drift_fail:
            reasons = []
            if s3_fail:
                reasons.append(f"S3={s3:.1%} < 60% (Gate 5a)")
            if drift_fail:
                reasons.append(f"drift_violation={dv:.1%} >= {DRIFT_VIOLATION_RATE_LIMIT:.0%} (Gate 6)")
            print("\n[BLOCKED_FOR_USER] " + " AND ".join(reasons))
            print("  rs review required before proceeding to F7.")
            sys.exit(2)
        print(f"\n[GATE 5a] S3={s3:.1%} >= 60%  [GATE 6] drift_viol={dv:.1%} < {DRIFT_VIOLATION_RATE_LIMIT:.0%}  -> PASS")


if __name__ == "__main__":
    main()
