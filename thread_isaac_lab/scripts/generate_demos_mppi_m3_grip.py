#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MPPI demo trajectory generation for Grip (Clamp) skill — Option B MVP.

Architecture (PROPOSE v3, Option III, rs approved 2026-04-24):
  - env (NewtonClampEnv, K_EXEC=1): episode execution via env.step()
  - mppi_scene (build_multiworld_scene, K_MPPI=256): parallel K-sample rollout for cost

env.step() handles physics/spring/sanitise/state-swap internally → auto-resolves
v2.1 CRITICAL items (sanitise omission, cadence math, state swap aliasing,
settled_body_q revert, K ambiguity).

Option B MVP (scripted finger close + 12D MPPI):
  - MPPI samples 12D EE delta (L-first internal), H=25, replan_interval=4
  - Execute: scripted finger_cmd (+1 until opening < T_FINGER, then 0)
  - Env applies via 14D R-first action [R_pos, R_ori, L_pos, L_ori, R_finger, L_finger]
  - Cost: max(pos_L, pos_R, m3_cost_scale*ori_L, m3_cost_scale*ori_R) + P_drop
  - Success: env native (sustained K_CLAMP=5 pos<T_DIST ^ ori<T_ALIGN ^ finger<T_FINGER)

Monkey-patches on env (reversible, instance attribute shadowing):
  - env.POS_ACTION_SCALE = cfg.pos_action_scale  (0.020 override env default 0.015)
  - env.ROT_ACTION_SCALE = cfg.rot_action_scale  (0.15 override env default 0.05)
  - env.ADAPTIVE_POS_SCALE = False
  - env.max_episode_length = large (generator manages max_steps)
  - env._reset_worlds = no-op intra-episode (manually restore for inter-episode)

Usage:
    source ~/env_isaaclab6/bin/activate
    cd ~/IsaacLab
    PYTHONPATH=$PYTHONPATH:thread_isaac_lab/scripts:thread_isaac_lab/configs:thread_isaac_lab/envs \\
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/generate_demos_mppi_m3_grip.py \\
        --device cuda:0 --world-count 4 --n-demos 5 --single-lambda 0.3

References:
    PROPOSE v3: /tmp/m3_grip_g3_propose_v3.md
    Design spec: thread-vault/08-DA-MPPI/01-Dashboard/m3_grip_design.md
    G1 config: configs/mpc_config_grip.py (sha256 62b20692...)
"""

import argparse
import csv
import json
import math
import os
import sys
import time

import h5py
import numpy as np
import torch
import warp as wp

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "configs"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "envs"))

from cable_orientation_utils import compute_cable_tangent, compute_hand_quat_for_cable

# Reuse MPPI primitives from M2 (not REPLAN_INTERVAL — use cfg.replan_interval).
from generate_demos_mppi_m2 import (
    DT,
    RL_SIM_SUBSTEPS,
    mppi_weights,
    sample_action_sequences,
    update_kinematic_bodies,
)

# Reuse M3 quaternion helpers + MppiIKSolverM3 (L-first 12D MPPI IK; mppi_scene only).
# NOTE: Do NOT import M3_ACTION_DIM / M3_ACTION_LAYOUT — v3 uses local GRIP_* constants.
# NOTE: Do NOT import compute_cost_targets_from_cable (endpoint-based, wrong for Grip).
from generate_demos_mppi_m3 import (
    DRIFT_THRESHOLD_RAD,
    DRIFT_VIOLATION_RATE_LIMIT,
    M3_QUAT_CONVENTION,
    M3_QUAT_FRAME,
    M3_QUAT_SEMANTIC,
    MppiIKSolverM3,
    _stats,
    get_ee_poses_dual,
)
from mpc_config_grip import get_default_mppi_grip_config
from newton_clamp_env import NewtonClampEnv
from newton_skill_env_base import (
    EE_BODY_OFFSET,
    FRANKA_NUM_JOINTS,
    build_multiworld_scene,
    compute_clamp_pos,
    find_nearest_cable_point,
)
from newton_skill_env_base import (
    axis_angle_to_quat_xyzw as _axis_angle_to_quat_xyzw,
)
from newton_skill_env_base import (
    normalize_quat_w_positive as _normalize_quat_w_positive,
)
from newton_skill_env_base import (
    quat_distance as _quat_distance,
)
from newton_skill_env_base import (
    quat_multiply_xyzw as _quat_multiply_xyzw,
)
from task_config import (
    CABLE_RADIUS,
    CLAMP_TERMINAL_STEPS,
    CLIP_BASE_HEIGHT,
    EE_TO_FINGERTIP,
    FINGER_OPEN_POS,
    GRASP_X,
    K_CLAMP,
    T_ALIGN,
    T_DIST,
    T_FINGER,
    TABLE_HEIGHT,
)

# =========================================================================
# Module constants (v3 local; see docstring)
# =========================================================================

GRIP_VERSION = "v1.0"
GRIP_ARCHITECTURE = "env.step + mppi_scene separate (PROPOSE v3)"
GRIP_MPPI_ACTION_DIM = 12  # L-first EE delta internal to MPPI (mppi_scene)
GRIP_HDF5_ACTION_DIM = 14  # R-first env-native [R_pos, R_ori, L_pos, L_ori, R_fin, L_fin]
GRIP_ACTION_LAYOUT = "R-first"  # env newton_clamp_env.py:28-34 native
GRIP_COST_METHOD = "max(pos_L, pos_R, scale*ori_L, scale*ori_R) + P_drop"

# Success thresholds (SSOT: task_config.py)
GRIP_POS_THR_M = T_DIST  # 0.002
GRIP_ORI_THR_RAD = T_ALIGN  # 0.1745
GRIP_FINGER_THR_M = T_FINGER  # 0.012

# Finger joint indices (joint-coord layout; per-arm [7, 8], dual-arm stride FRANKA_NUM_JOINTS=9).
# Used ONLY in mppi_scene rollout to pin fingers OPEN (env internal IK handles execute-time finger cmd).
FINGER_JOINT_COORD_INDICES = [7, 8, FRANKA_NUM_JOINTS + 7, FRANKA_NUM_JOINTS + 8]

# Cable drop detection (P_CABLE_DROP cost penalty added in rollout when cable z < threshold)
CABLE_DROP_MARGIN_M = 0.010  # 10mm below resting cable-on-table height
CABLE_DROP_Z_THR = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS - CABLE_DROP_MARGIN_M
P_CABLE_DROP = 100.0  # AR precedent `P_DROP` value

# B3-β R-only mode constants (CC-CLAMP-R-Phase-C2 Phase C2, 2026-04-26).
# Phase C2 generates CLAMP_R standalone single-arm BC demos (audit B3 fix).
L_RECLAMP_PREAMBLE_STEPS = 50  # Max env.step calls to close L finger pre-MPPI (~T_FINGER converge)
L_DRIFT_ABORT_M = 0.005  # 5mm L EE drift triggers episode abort in r_arm_only mode

# Warmup (not used in Grip — cfg.warm_start_offset_m=0.0 by design)
# Kept here for potential future Option A slerp warm-start.

# F1-inspired finger close warm-start (T-GC-EvalGap-Fix 2026-04-29).
# Closes both fingers pre-MPPI to provide BC anchor with finger-close trajectory from cold start.
# Addresses H3 root cause (BC dominance + scripted finger_cmd noise brittleness, det 14.5% / stoch 0%).
# Differs from L_RECLAMP_PREAMBLE: helper steps ARE recorded in traj_* (BC anchor required for cold-start eval).
# Gated by --warm-start-finger-close CLI flag (default disabled). Mutually exclusive with --r-arm-only.
WARM_START_FINGER_CLOSE_MAX_STEPS = 50  # Max env.step iterations for both fingers to reach < T_FINGER

# =========================================================================
# base_scene_to_m2_info — inline duplicate from AR (FM-10 mitigation).
# =========================================================================


def base_scene_to_m2_info(scene):
    """Translate build_multiworld_scene dict to M2-compat info keys.

    M2-compat keys required by copy_world0_to_all / compute_cable_endpoint_pos /
    get_ee_poses_dual / update_kinematic_bodies. Mirrors AR m3_ar.py:404-423.
    """
    return {
        "bws": scene["bws"],
        "bodies_per_world": scene["bodies_per_world"],
        "cable_per_world": scene["cable_bodies_per_world"],
        "cable_offset": scene["cable_body_offset"],
        "left_body_start": 0,
        "right_body_start": FRANKA_NUM_JOINTS,
    }


# =========================================================================
# Env state cloning: env world 0 → mppi_scene all K worlds.
# =========================================================================


def clone_env_to_mppi(env, mppi_scene, mppi_info, K):
    """Copy env._state_0 world 0 body_q/body_qd into mppi_scene all K worlds.

    Called at start of every MPPI plan. Uses env's authoritative state so
    mppi_scene rollout starts from current env-physics ground truth.

    Args:
        env: NewtonClampEnv instance (K_EXEC=1).
        mppi_scene: dict from build_multiworld_scene with K_MPPI worlds.
        mppi_info: M2-compat info dict (from base_scene_to_m2_info).
        K: mppi_scene world_count.
    """
    env_bws = env._bws
    mppi_bws = mppi_info["bws"]
    env_bpw = env._bodies_per_world
    mppi_bpw = mppi_info["bodies_per_world"]

    if env_bpw != mppi_bpw:
        raise RuntimeError(
            f"[clone_env_to_mppi] bodies_per_world mismatch: env={env_bpw}, mppi={mppi_bpw}. "
            "env and mppi_scene must be built with identical add_target_clip / add_support_clips."
        )

    wp.synchronize()
    env_bq = env._state_0.body_q.numpy()
    env_bqd = env._state_0.body_qd.numpy()

    mppi_bq = mppi_scene["state_0"].body_q.numpy()
    mppi_bqd = mppi_scene["state_0"].body_qd.numpy()

    env_w0_start = env_bws[0]
    env_w0_end = env_w0_start + env_bpw
    env_w0_bq = env_bq[env_w0_start:env_w0_end]
    env_w0_bqd = env_bqd[env_w0_start:env_w0_end]

    for w in range(K):
        s = mppi_bws[w]
        e = s + mppi_bpw
        mppi_bq[s:e] = env_w0_bq
        mppi_bqd[s:e] = env_w0_bqd

    mppi_scene["state_0"].body_q.assign(mppi_bq)
    mppi_scene["state_0"].body_qd.assign(mppi_bqd)
    mppi_scene["solver"].body_q_prev = wp.clone(mppi_scene["state_0"].body_q)


# =========================================================================
# Grip-specific cost target: per-world nearest-seg tangent (both arms).
# Replaces AC compute_cost_targets_from_cable (endpoint-based, wrong for Grip).
# Mirrors AR _compute_ar_target_seg_indices but dual-arm.
# =========================================================================


def compute_grip_target_seg_indices(state, info, world_count, grip_seg_window=1):
    """Compute per-world ±grip_seg_window cable seg indices per arm.

    Mirrors newton_clamp_env._compute_target_seg_indices (L493-517) but reads
    from mppi_scene state via info dict (M2-compat).
    """
    bq = state.body_q.numpy()
    bws = info["bws"]
    co = info["cable_offset"]
    cpw = info["cable_per_world"]
    win = grip_seg_window
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


def compute_cable_drop_mask(state, info, K):
    """Detect cable-dropped worlds (cable min z < threshold).

    Returns bool (K,) mask. True = cable dropped.
    """
    bq = state.body_q.numpy()
    flat = bq.view(np.float32).reshape(-1, 7)
    bws = info["bws"]
    co = info["cable_offset"]
    cpw = info["cable_per_world"]
    dropped = np.zeros(K, dtype=bool)
    for w in range(K):
        ws = bws[w]
        cable_z = flat[ws + co : ws + co + cpw, 2]
        if cable_z.min() < CABLE_DROP_Z_THR:
            dropped[w] = True
    return dropped


# =========================================================================
# MPPI rollout + cost (mppi_scene only; env untouched during rollout).
# =========================================================================


def rollout_and_cost_grip(
    mppi_scene,
    mppi_info,
    ik_solver,
    per_world_jq,
    K,
    H,
    cfg,
    target_seg_indices_l,
    target_seg_indices_r,
    ik_target_quat_L_init,
    ik_target_quat_R_init,
    r_arm_only=False,
):
    """Rollout K trajectories in mppi_scene for H steps with 12D L-first actions.

    Cost (bimanual) = max(pos_L, pos_R, m3_cost_scale*ori_L, m3_cost_scale*ori_R) + P_DROP*I(drop).
    Cost (r_arm_only) = max(pos_R, m3_cost_scale*ori_R) + P_DROP*I(drop).
    Fingers pinned OPEN in mppi_scene throughout (Option B: MPPI blind to finger).

    When r_arm_only=True, L EE delta sampling is zeroed (actions[:, :, 0:6] = 0) so the
    rollout's predicted L-arm state matches env's frozen-L behavior. L cost terms are
    excluded from max-reduce. L IK target accumulation still runs (cheap, mppi_scene
    L EE motion suppressed via zeroed sample → IK targets stay near init).

    Returns:
        actions: (K, H, 12) sampled action sequences (for weighting post-return)
        costs: (K,) float32 accumulated cost
        n_nan, t_ik_total, t_physics_total, ee_spread_max, drift_L, drift_R, drop_count
    """
    model = mppi_scene["model"]
    solver_vbd = mppi_scene["solver"]
    state_0 = mppi_scene["state_0"]
    state_1 = mppi_scene["state_1"]
    control = mppi_scene["control"]

    sim_dt = DT / RL_SIM_SUBSTEPS
    costs = np.zeros(K, dtype=np.float32)
    jq = per_world_jq.copy()
    t_ik_total = 0.0
    t_physics_total = 0.0
    nan_mask = np.zeros(K, dtype=bool)
    ee_spread_max_left = 0.0
    ee_spread_max_right = 0.0

    bws = mppi_info["bws"]
    bpw = mppi_info["bodies_per_world"]
    co = mppi_info["cable_offset"]
    cpw = mppi_info["cable_per_world"]

    # Sample K action sequences (caller provides rng)
    rng = np.random.default_rng(cfg.K + int(time.time_ns() % 1_000_000))
    actions = sample_action_sequences(K, H, GRIP_MPPI_ACTION_DIM, cfg.noise_sigma, cfg.noise_correlation, rng)

    # B3-β r_arm_only: zero L EE delta in MPPI sample (CC3-2 mitigation).
    # This makes rollout's L-arm trajectory match env's frozen-L behavior, preventing
    # phantom L motion bias in cost ranking when env will execute action[6:12]=0.
    if r_arm_only:
        actions[:, :, 0:6] = 0.0  # L_pos (0:3) + L_ori (3:6) zeroed

    # Tangent drift capture (world 0 plan start)
    w0 = bws[0]
    flat_start = state_0.body_q.numpy().view(np.float32).reshape(-1, 7)
    cable_start = flat_start[w0 + co : w0 + co + cpw, :3].copy()
    tangent_L_start = compute_cable_tangent(cable_start, 0)
    tangent_R_start = compute_cable_tangent(cable_start, cpw - 1)

    # IK target init (tile warm-start-end or current, (K, 4) xyzw float32)
    ik_tgt_L = np.tile(ik_target_quat_L_init[None].astype(np.float32), (K, 1))
    ik_tgt_R = np.tile(ik_target_quat_R_init[None].astype(np.float32), (K, 1))

    for h in range(H):
        # Current EE pos reference (pre-IK, post-physics previous step)
        (left_ee, _), (right_ee, _) = get_ee_poses_dual(state_0, mppi_info, K)

        # 12D L-first split
        L_pos_delta = actions[:, h, 0:3] * cfg.pos_action_scale
        L_ori_delta = actions[:, h, 3:6] * cfg.rot_action_scale
        R_pos_delta = actions[:, h, 6:9] * cfg.pos_action_scale
        R_ori_delta = actions[:, h, 9:12] * cfg.rot_action_scale

        target_L_pos = left_ee + L_pos_delta
        target_R_pos = right_ee + R_pos_delta

        # IK target accumulate (left-multiply, world frame)
        for k in range(K):
            q_dL = _axis_angle_to_quat_xyzw(L_ori_delta[k])
            ik_tgt_L[k] = _quat_multiply_xyzw(q_dL, ik_tgt_L[k])
            ik_tgt_L[k] = ik_tgt_L[k] / np.linalg.norm(ik_tgt_L[k])
            q_dR = _axis_angle_to_quat_xyzw(R_ori_delta[k])
            ik_tgt_R[k] = _quat_multiply_xyzw(q_dR, ik_tgt_R[k])
            ik_tgt_R[k] = ik_tgt_R[k] / np.linalg.norm(ik_tgt_R[k])

        # IK solve (5-obj)
        t0_ik = time.perf_counter()
        jq_solved = ik_solver.solve(target_L_pos, ik_tgt_L, target_R_pos, ik_tgt_R, jq)

        # Pin fingers OPEN in rollout (Option B: MPPI blind to finger close timing)
        for fc in FINGER_JOINT_COORD_INDICES:
            jq_solved[:, fc] = FINGER_OPEN_POS

        fk_body_q = ik_solver.eval_fk_batch(jq_solved)
        t_ik_total += time.perf_counter() - t0_ik

        update_kinematic_bodies(state_0, fk_body_q, mppi_info, K)

        # EE spread diagnostic
        (ik_left, _), (ik_right, _) = get_ee_poses_dual(state_0, mppi_info, K)
        valid_idx = ~nan_mask
        if valid_idx.sum() > 1:
            ee_spread_max_left = max(ee_spread_max_left, float(np.sqrt(np.sum(np.var(ik_left[valid_idx], axis=0)))))
            ee_spread_max_right = max(ee_spread_max_right, float(np.sqrt(np.sum(np.var(ik_right[valid_idx], axis=0)))))

        # Physics step (mppi_scene, kinematic fingers OK during rollout since no close)
        t0_phys = time.perf_counter()
        contacts = model.collide(state_0)
        for _ in range(RL_SIM_SUBSTEPS):
            solver_vbd.step(state_0, state_1, control, contacts, sim_dt)
            state_0, state_1 = state_1, state_0
        t_physics_total += time.perf_counter() - t0_phys

        # NaN check
        bq_check = state_0.body_q.numpy()
        for w in range(K):
            if not nan_mask[w]:
                s = bws[w]
                chunk = bq_check[s : s + bpw]
                if np.any(np.isnan(chunk)) or np.any(np.isinf(chunk)):
                    nan_mask[w] = True
                    costs[w] = 1e6

        # Achieved FK post-physics
        (achieved_pos_L, achieved_quat_L), (achieved_pos_R, achieved_quat_R) = get_ee_poses_dual(state_0, mppi_info, K)

        # Grip-specific per-world nearest-seg cost (C3 fix: interior seg, not endpoint)
        flat = bq_check.view(np.float32).reshape(-1, 7)
        pos_dist_L = np.zeros(K, dtype=np.float32)
        pos_dist_R = np.zeros(K, dtype=np.float32)
        ori_dist_L = np.zeros(K, dtype=np.float32)
        ori_dist_R = np.zeros(K, dtype=np.float32)

        for k in range(K):
            if nan_mask[k]:
                continue
            ws = bws[k]
            cable_pos = flat[ws + co : ws + co + cpw, :3]

            q_L = _normalize_quat_w_positive(achieved_quat_L[k])
            clamp_L = compute_clamp_pos(achieved_pos_L[k], q_L)
            _, seg_tangent_L, d_L = find_nearest_cable_point(cable_pos, clamp_L, target_seg_indices_l[k])
            pos_dist_L[k] = d_L
            target_quat_L = _normalize_quat_w_positive(
                np.asarray(compute_hand_quat_for_cable(seg_tangent_L), dtype=np.float32)
            )
            ori_dist_L[k] = _quat_distance(q_L, target_quat_L)

            q_R = _normalize_quat_w_positive(achieved_quat_R[k])
            clamp_R = compute_clamp_pos(achieved_pos_R[k], q_R)
            _, seg_tangent_R, d_R = find_nearest_cable_point(cable_pos, clamp_R, target_seg_indices_r[k])
            pos_dist_R[k] = d_R
            target_quat_R = _normalize_quat_w_positive(
                np.asarray(compute_hand_quat_for_cable(seg_tangent_R), dtype=np.float32)
            )
            ori_dist_R[k] = _quat_distance(q_R, target_quat_R)

        # Cable drop detection
        drop_mask = compute_cable_drop_mask(state_0, mppi_info, K)

        # Method C cost + drop penalty (r_arm_only excludes L terms; CC3-2 lens)
        if r_arm_only:
            step_cost = np.maximum.reduce(
                [
                    pos_dist_R,
                    cfg.m3_cost_scale * ori_dist_R,
                ]
            ).astype(np.float32)
        else:
            step_cost = np.maximum.reduce(
                [
                    pos_dist_L,
                    pos_dist_R,
                    cfg.m3_cost_scale * ori_dist_L,
                    cfg.m3_cost_scale * ori_dist_R,
                ]
            ).astype(np.float32)
        step_cost += np.where(drop_mask, P_CABLE_DROP, 0.0).astype(np.float32)
        costs += np.where(nan_mask, 0.0, step_cost)

        jq = jq_solved.copy()

    # Tangent drift end (world 0)
    flat_end = state_0.body_q.numpy().view(np.float32).reshape(-1, 7)
    cable_end = flat_end[w0 + co : w0 + co + cpw, :3].copy()
    tangent_L_end = compute_cable_tangent(cable_end, 0)
    tangent_R_end = compute_cable_tangent(cable_end, cpw - 1)
    dot_L = float(np.clip(np.dot(tangent_L_start, tangent_L_end), -1.0, 1.0))
    dot_R = float(np.clip(np.dot(tangent_R_start, tangent_R_end), -1.0, 1.0))
    drift_L = float(math.acos(dot_L))
    drift_R = float(math.acos(dot_R))

    drop_final_mask = compute_cable_drop_mask(state_0, mppi_info, K)
    drop_count = int(drop_final_mask.sum())

    n_nan = int(nan_mask.sum())
    if n_nan > 0:
        print(f"  [NaN] {n_nan}/{K} worlds had NaN ({n_nan * 100 // K}%)")
    ee_spread_max = max(ee_spread_max_left, ee_spread_max_right)

    return actions, costs, n_nan, t_ik_total, t_physics_total, ee_spread_max, drift_L, drift_R, drop_count


# =========================================================================
# MPPI plan: clone env state, rollout, weight, return best EE action.
# =========================================================================


def mppi_plan(
    env, mppi_scene, mppi_info, ik_solver, cfg, cfg_K, per_world_jq_ref, ik_target_L, ik_target_R, r_arm_only=False
):
    """One MPPI plan step: clone env state → rollout → weight → best action.

    Returns:
        best_action_ee: (H, 12) weighted-mean action sequence (L-first 12D)
        diag: dict with n_nan, cost_range, weight_entropy, top1_w, drift_L, drift_R, etc.
        new_ik_target_L, new_ik_target_R: accumulated IK targets (world 0 copy for next plan)
    """
    K = cfg_K

    # Clone env state → mppi_scene all K worlds
    clone_env_to_mppi(env, mppi_scene, mppi_info, K)

    # Compute per-world target seg indices (pre-rollout, from cloned state).
    # In r_arm_only mode, target_seg_indices_l is computed but unused in cost; kept for code uniformity.
    target_seg_indices_r, target_seg_indices_l = compute_grip_target_seg_indices(
        mppi_scene["state_0"], mppi_info, K, grip_seg_window=1
    )

    # Initialize per_world_jq for mppi_scene IK solver (from env's FK state world 0, tiled)
    per_world_jq = np.tile(per_world_jq_ref[None].astype(np.float64), (K, 1))

    # Rollout + cost
    actions, costs, n_nan, t_ik, t_phys, ee_spread, drift_L, drift_R, drop_count = rollout_and_cost_grip(
        mppi_scene,
        mppi_info,
        ik_solver,
        per_world_jq,
        K,
        cfg.H,
        cfg,
        target_seg_indices_l,
        target_seg_indices_r,
        ik_target_L,
        ik_target_R,
        r_arm_only=r_arm_only,
    )

    # Weight + best action (softmax over negative cost)
    weights = mppi_weights(costs, cfg.temperature_lambda)
    best_action_ee = np.einsum("k,kha->ha", weights, actions).astype(np.float32)

    # Diagnostics
    valid_costs = costs[costs < 1e5]
    if len(valid_costs) > 1:
        c_min = float(valid_costs.min())
        c_max = float(valid_costs.max())
        c_range = c_max - c_min
        c_std = float(valid_costs.std())
    else:
        c_min = c_max = c_range = c_std = 0.0

    k_eff = K - n_nan
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

    ba_has_nan = bool(np.any(np.isnan(best_action_ee)) or np.any(np.isinf(best_action_ee)))

    diag = {
        "n_nan": n_nan,
        "k_eff": k_eff,
        "weight_entropy": w_entropy,
        "weight_mass_valid": w_mass_valid,
        "top1_weight": top1_w,
        "best_action_nan": ba_has_nan,
        "cost_min": c_min,
        "cost_max": c_max,
        "cost_range": c_range,
        "cost_std": c_std,
        "ee_spread_max_mm": ee_spread * 1000,
        "drift_L_rad": drift_L,
        "drift_R_rad": drift_R,
        "drop_count": drop_count,
        "t_ik_total_s": t_ik,
        "t_physics_total_s": t_phys,
    }
    return best_action_ee, diag


# =========================================================================
# F1-inspired finger close warm-start helper (T-GC-EvalGap-Fix 2026-04-29).
# =========================================================================


def _warm_start_finger_close_grip(env, cfg, device, env_bws0):
    """Pre-MPPI finger close warm-start for Grip-CLAMP, records steps for BC training.

    Closes both fingers via env.step iteration with action_14d R-first env-native layout
    (env newton_clamp_env.py:28-34): [0:3]=R_pos=0, [3:6]=R_ori=0, [6:9]=L_pos=0, [9:12]=L_ori=0,
    [12]=R_finger_cmd, [13]=L_finger_cmd. Z and rotation deltas zeroed (Grip P0 cable-proximal at
    GRIP_Z=1.029m, no descent needed; differs from IC F1 91mm Z descent).

    finger_cmd is float scalar default cfg.finger_close_rate (1.0), applied conditionally per
    opening gate (matches main loop scripted gating at line ~876-879).

    Returns (success, steps_taken, final_opening_L, final_opening_R, recordings: list[dict]).
    Caller must append recordings to traj_* (BC anchor needed for cold-start eval; differs from
    r_arm_only L_RECLAMP_PREAMBLE which excludes from traj per CLAMP-R semantics).

    Termination: opening_L < T_FINGER AND opening_R < T_FINGER (both axes), OR MAX_STEPS, OR done.
    On failure (cable interference / env terminal), caller skips episode (graceful, no over-close).
    """
    recordings = []
    final_l, final_r = 0.0, 0.0
    for step in range(WARM_START_FINGER_CLOSE_MAX_STEPS):
        wp.synchronize()
        opening_L = env._per_world_fk_jq[0, 7] + env._per_world_fk_jq[0, 8]
        opening_R = env._per_world_fk_jq[0, FRANKA_NUM_JOINTS + 7] + env._per_world_fk_jq[0, FRANKA_NUM_JOINTS + 8]
        final_l, final_r = float(opening_L), float(opening_R)
        if opening_L < T_FINGER and opening_R < T_FINGER:
            return True, step, final_l, final_r, recordings
        # Build action_14d R-first (env native, only finger commands non-zero)
        action_14d = np.zeros(GRIP_HDF5_ACTION_DIM, dtype=np.float32)
        action_14d[12] = cfg.finger_close_rate if opening_R > T_FINGER else 0.0
        action_14d[13] = cfg.finger_close_rate if opening_L > T_FINGER else 0.0
        assert action_14d.shape == (GRIP_HDF5_ACTION_DIM,), f"action shape mismatch: {action_14d.shape}"
        # Record state BEFORE env.step (matches main loop pattern at lines ~920-940)
        env_flat = env._state_0.body_q.numpy().view(np.float32).reshape(-1, 7)
        record = {
            "action": action_14d.copy(),
            "left_pos": env_flat[env_bws0 + EE_BODY_OFFSET, :3].astype(np.float32).copy(),
            "left_quat": _normalize_quat_w_positive(env_flat[env_bws0 + EE_BODY_OFFSET, 3:7]).astype(np.float32),
            "right_pos": env_flat[env_bws0 + FRANKA_NUM_JOINTS + EE_BODY_OFFSET, :3].astype(np.float32).copy(),
            "right_quat": _normalize_quat_w_positive(
                env_flat[env_bws0 + FRANKA_NUM_JOINTS + EE_BODY_OFFSET, 3:7]
            ).astype(np.float32),
            "cable_pos": env_flat[
                env_bws0 + env._cable_body_offset : env_bws0 + env._cable_body_offset + env._cable_bodies_per_world,
                :3,
            ]
            .astype(np.float32)
            .copy(),
        }
        # env.step (single entry for physics/spring/sanitise/swap/obs)
        action_t = torch.from_numpy(action_14d).unsqueeze(0).to(device)
        obs, _r, done, _ex = env.step(action_t)
        wp.synchronize()
        # Post-step state
        record["obs"] = obs[0].cpu().numpy().copy()
        record["opening_L"] = float(env._per_world_fk_jq[0, 7] + env._per_world_fk_jq[0, 8])
        record["opening_R"] = float(
            env._per_world_fk_jq[0, FRANKA_NUM_JOINTS + 7] + env._per_world_fk_jq[0, FRANKA_NUM_JOINTS + 8]
        )
        record["dist_pos_L"] = float(np.linalg.norm(record["obs"][39:42]))
        record["dist_pos_R"] = float(np.linalg.norm(record["obs"][33:36]))
        record["dist_ori_L"] = float(np.linalg.norm(record["obs"][36:39]))
        record["dist_ori_R"] = float(np.linalg.norm(record["obs"][30:33]))
        recordings.append(record)
        if done[0].item():
            return False, step + 1, record["opening_L"], record["opening_R"], recordings
    return False, WARM_START_FINGER_CLOSE_MAX_STEPS, final_l, final_r, recordings


# =========================================================================
# Main demo generation: env.step execute + mppi_plan rollout.
# =========================================================================


def mppi_generate_demos_grip(
    cfg,
    device,
    max_steps=CLAMP_TERMINAL_STEPS,
    n_demos=5,
    seed=42,
    diag_csv_path="/tmp/mppi_grip_metrics.csv",
    r_arm_only=False,
    warm_start_finger_close=False,
):
    """Generate Grip demos via env.step hybrid (Option III).

    env (K_EXEC=1) for episode execution + mppi_scene (K_MPPI=cfg.K) for rollout.

    When r_arm_only=True (B3-β CC-CLAMP-R-Phase-C2 mode):
      1. L-arm RECLAMP scripted preamble (`L_RECLAMP_PREAMBLE_STEPS` env.step calls with
         finger_cmd_L = cfg.finger_close_rate; not recorded in traj_*).
      2. MPPI rollout suppresses L-arm action sampling (rollout_and_cost_grip handles).
      3. Execution: action[6:12] (L EE delta) zeroed; finger_cmd_L scripted-held with
         re-close if opening_L slips above T_FINGER (CC3-5 lens).
      4. Episode-level success criterion uses R-only conditions (CC2-4 lens).
      5. L drift abort: if L EE drifts > L_DRIFT_ABORT_M during episode, terminate "L_DRIFT".

    Returns:
        demos: list of per-episode dicts (action_delta/obs/ee_pos/quat/finger_opening/dist_*/
            cable_pos_seq + success attrs).
        drifts_per_plan_LR: list[(float, float)] — per-plan tangent drift [L, R] across all episodes.
        drifts_per_episode_max: list[float] — max(drift_L, drift_R) per episode.
        cable_endpoints_L: list[ndarray(3,)] — per-episode cable seg 0 position at reset.
        cable_endpoints_R: list[ndarray(3,)] — per-episode cable seg last position at reset.
    """
    K = cfg.K  # MPPI sample count
    H = cfg.H
    replan_interval = cfg.replan_interval

    print(f"\n[MPPI-Grip] {GRIP_VERSION} Option III: env.step hybrid")
    print(f"  K_EXEC=1 (env), K_MPPI={K} (mppi_scene), H={H}, replan={replan_interval}")
    print(
        f"  pos_scale={cfg.pos_action_scale}, rot_scale={cfg.rot_action_scale}, m3_cost_scale={cfg.m3_cost_scale:.4f}"
    )
    print(f"  l/r_ori_ik_weight={cfg.l_ori_ik_weight}, finger_close_rate={cfg.finger_close_rate}")

    # =====================================================================
    # Phase A: env construction + monkey-patches
    # =====================================================================
    print("[MPPI-Grip] Phase A: env construction...")
    env = NewtonClampEnv(world_count=1, device=device)

    # Monkey-patch (instance attribute shadowing; reversible)
    env.POS_ACTION_SCALE = cfg.pos_action_scale
    env.ROT_ACTION_SCALE = cfg.rot_action_scale
    env.ADAPTIVE_POS_SCALE = False
    env.max_episode_length = 100_000  # disable env internal timeout
    _env_reset_original = env._reset_worlds
    env._reset_worlds = lambda env_ids: None  # no-op intra-episode, manual reset between episodes

    def env_reset_manual():
        """Invoke original _reset_worlds for inter-episode reset."""
        _env_reset_original(list(range(env._world_count)))

    # =====================================================================
    # Phase B: mppi_scene build + IK solver
    # =====================================================================
    print(f"[MPPI-Grip] Phase B: mppi_scene (K={K})...")
    # IMPORTANT: mppi_scene must match env's scene body_count.
    # env uses add_support_clips=True (newton_clamp_env.py _build_model).
    # Verify env and mppi_scene bodies_per_world match before cloning.
    fk_model_mppi = env._fk_model
    fk_state_mppi = env._fk_state
    mppi_scene = build_multiworld_scene(
        fk_model_mppi,
        fk_state_mppi,
        K,
        device,
        cable_start_pos=(GRASP_X, 0, TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS),
        add_support_clips=True,  # match env newton_clamp_env.py _build_model call (line 263)
    )
    mppi_info = base_scene_to_m2_info(mppi_scene)
    if mppi_info["bodies_per_world"] != env._bodies_per_world:
        raise RuntimeError(
            f"[MPPI-Grip] bodies_per_world mismatch: env={env._bodies_per_world}, "
            f"mppi_scene={mppi_info['bodies_per_world']}. Check add_support_clips alignment."
        )
    print(f"  mppi bodies_per_world={mppi_info['bodies_per_world']}, cable_per_world={mppi_info['cable_per_world']}")

    ik_solver = MppiIKSolverM3(
        fk_model_mppi,
        K,
        device,
        l_ori_weight=cfg.l_ori_ik_weight,
        r_ori_weight=cfg.r_ori_ik_weight,
    )

    # =====================================================================
    # Phase C: episode loop
    # =====================================================================
    demos = []
    drifts_per_plan_LR = []
    drifts_per_episode_max = []
    cable_endpoints_L = []
    cable_endpoints_R = []

    # Diag CSV
    diag_file = open(diag_csv_path, "w", newline="")  # noqa: SIM115
    diag_csv = csv.writer(diag_file)
    diag_csv.writerow(
        [
            "episode",
            "step",
            "n_nan",
            "k_eff",
            "weight_entropy",
            "weight_mass_valid",
            "top1_weight",
            "best_action_nan",
            "plan_time_s",
            "cost_min",
            "cost_max",
            "cost_range",
            "cost_std",
            "ee_spread_max_mm",
            "drift_L_rad",
            "drift_R_rad",
            "drop_count",
            "sustain_count",
            "opening_L",
            "opening_R",
            "pos_action_scale",  # γ-3c: logged per-row for sweep analysis
        ]
    )

    for ep in range(n_demos):
        print(f"\n[MPPI-Grip] Episode {ep + 1}/{n_demos}")

        # Reset env (original _reset_worlds)
        env_reset_manual()
        obs, _ = env.get_observations()

        # Cable endpoints at reset (from env state, world 0)
        wp.synchronize()
        env_bq = env._state_0.body_q.numpy()
        env_cable_off = env._cable_body_offset
        env_cable_per = env._cable_bodies_per_world
        env_bws0 = env._bws[0]
        cable_flat = env_bq.view(np.float32).reshape(-1, 7)
        cable_L_reset = cable_flat[env_bws0 + env_cable_off, :3].astype(np.float32).copy()
        cable_R_reset = cable_flat[env_bws0 + env_cable_off + env_cable_per - 1, :3].astype(np.float32).copy()
        cable_endpoints_L.append(cable_L_reset)
        cable_endpoints_R.append(cable_R_reset)

        # Per-episode trajectory buffers
        traj_actions = []
        traj_obs = []
        traj_left_pos = []
        traj_right_pos = []
        traj_left_quat = []
        traj_right_quat = []
        traj_finger_L = []
        traj_finger_R = []
        traj_dist_pos_L = []
        traj_dist_pos_R = []
        traj_dist_ori_L = []
        traj_dist_ori_R = []
        traj_cable_pos = []
        drifts_L_ep = []
        drifts_R_ep = []

        step = 0
        sustain_count = 0
        success = False
        success_step = -1

        # Initial IK target = current env EE quat (world 0)
        env_flat = env._state_0.body_q.numpy().view(np.float32).reshape(-1, 7)
        left_quat0 = _normalize_quat_w_positive(env_flat[env_bws0 + EE_BODY_OFFSET, 3:7]).astype(np.float32)
        right_quat0 = _normalize_quat_w_positive(env_flat[env_bws0 + FRANKA_NUM_JOINTS + EE_BODY_OFFSET, 3:7]).astype(
            np.float32
        )
        ik_target_L = left_quat0.copy()
        ik_target_R = right_quat0.copy()

        # B3-β r_arm_only: L-arm RECLAMP scripted preamble (CC2-2 + CC3-3 lenses).
        # Close L finger via env.step with finger_cmd_L=cfg.finger_close_rate; both arms EE held.
        # Steps are NOT recorded in traj_* (preamble is pre-data-collection setup).
        # NaN abort criterion per step. F1 caveat: P0 != deployment RECLAMP'd state (left endpoint
        # vs clip-N) — Phase C5 BC bridges generalization gap. l_ee_anchor used for drift abort.
        l_ee_anchor = None
        preamble_aborted = False
        if r_arm_only:
            preamble_steps_used = 0
            for _preamble_step in range(L_RECLAMP_PREAMBLE_STEPS):
                opening_L_pre = env._per_world_fk_jq[0, 7] + env._per_world_fk_jq[0, 8]
                if opening_L_pre < T_FINGER:
                    break
                preamble_action = np.zeros(GRIP_HDF5_ACTION_DIM, dtype=np.float32)
                preamble_action[13] = cfg.finger_close_rate  # L finger close (R-first [13])
                preamble_tensor = torch.from_numpy(preamble_action).unsqueeze(0).to(device)
                _obs_p, _r_p, done_p, _ex_p = env.step(preamble_tensor)
                wp.synchronize()
                env_bq_check = env._state_0.body_q.numpy()
                if np.any(np.isnan(env_bq_check)) or np.any(np.isinf(env_bq_check)):
                    print(f"  [PREAMBLE_NAN] step={_preamble_step} env body NaN/inf — abort episode")
                    preamble_aborted = True
                    break
                if done_p[0].item():
                    print(f"  [PREAMBLE_TERMINAL] step={_preamble_step} env done — abort episode")
                    preamble_aborted = True
                    break
                preamble_steps_used += 1
            if preamble_aborted:
                # Skip rest of episode; demo not added (under-counts drifts/cable_endpoints by 1).
                continue
            # L EE anchor for drift-abort criterion (CC3-4 lens)
            wp.synchronize()
            env_flat_pa = env._state_0.body_q.numpy().view(np.float32).reshape(-1, 7)
            l_ee_anchor = env_flat_pa[env_bws0 + EE_BODY_OFFSET, :3].astype(np.float32).copy()
            opening_L_done = env._per_world_fk_jq[0, 7] + env._per_world_fk_jq[0, 8]
            print(
                f"  [PREAMBLE] L closed in {preamble_steps_used}/{L_RECLAMP_PREAMBLE_STEPS} steps; "
                f"opening_L={opening_L_done * 1000:.1f}mm; L EE anchor z={l_ee_anchor[2]:.4f}"
            )

        # F1-inspired finger close warm-start (T-GC-EvalGap-Fix 2026-04-29, Rs override on iter 1+2 BLOCK fold-in).
        # Mutual exclusion with r_arm_only (CLAMP-R has its own L_RECLAMP preamble).
        if warm_start_finger_close and not r_arm_only:
            ws_success, ws_steps, ws_l, ws_r, ws_records = _warm_start_finger_close_grip(env, cfg, device, env_bws0)
            print(
                f"  [WARM-Grip-Finger] success={ws_success} steps={ws_steps}/{WARM_START_FINGER_CLOSE_MAX_STEPS} "
                f"L={ws_l * 1000:.1f}mm R={ws_r * 1000:.1f}mm; remaining {max_steps} steps for MPPI"
            )
            if not ws_success:
                # Helper failed (cable interference / env terminal); skip episode (graceful, follows preamble pattern).
                print(f"  [WARM-Grip-Finger] Helper failed, skipping episode {ep + 1}")
                continue
            # Append helper records to traj_* (BC anchor: cold-start eval needs to see finger close trajectory)
            for rec in ws_records:
                traj_actions.append(rec["action"])
                traj_obs.append(rec["obs"])
                traj_left_pos.append(rec["left_pos"])
                traj_right_pos.append(rec["right_pos"])
                traj_left_quat.append(rec["left_quat"])
                traj_right_quat.append(rec["right_quat"])
                traj_finger_L.append(rec["opening_L"])
                traj_finger_R.append(rec["opening_R"])
                traj_dist_pos_L.append(rec["dist_pos_L"])
                traj_dist_pos_R.append(rec["dist_pos_R"])
                traj_dist_ori_L.append(rec["dist_ori_L"])
                traj_dist_ori_R.append(rec["dist_ori_R"])
                traj_cable_pos.append(rec["cable_pos"])

        best_action_ee = None  # (H, 12) refreshed every replan_interval
        plan_idx = 0

        while step < max_steps:
            # MPPI plan (every replan_interval steps, or at step=0)
            if step % replan_interval == 0:
                t0_plan = time.perf_counter()
                per_world_jq_env_w0 = env._per_world_fk_jq[0].copy()  # world 0 FK jq from env
                best_action_ee, diag = mppi_plan(
                    env,
                    mppi_scene,
                    mppi_info,
                    ik_solver,
                    cfg,
                    K,
                    per_world_jq_env_w0,
                    ik_target_L,
                    ik_target_R,
                    r_arm_only=r_arm_only,
                )
                t_plan = time.perf_counter() - t0_plan
                drifts_L_ep.append(diag["drift_L_rad"])
                drifts_R_ep.append(diag["drift_R_rad"])

                if plan_idx == 0 or plan_idx % 5 == 0:
                    print(
                        f"  [PLAN {plan_idx}] step={step} plan_t={t_plan:.2f}s "
                        f"nan={diag['n_nan']}/{K} k_eff={diag['k_eff']} "
                        f"cost_range={diag['cost_range']:.4f} entropy={diag['weight_entropy']:.2f} "
                        f"drift L={math.degrees(diag['drift_L_rad']):.1f}° R={math.degrees(diag['drift_R_rad']):.1f}° "
                        f"drop={diag['drop_count']}"
                    )

                # Advance IK target (world-frame delta from plan's first H-step accumulated in rollout)
                # For executor, use the first execute step's delta to update ik_target incrementally
                plan_idx += 1

            # Current step's executed action (best_action_ee is H-length, pick index h_exec)
            h_exec = step % replan_interval
            action_ee_12d = best_action_ee[h_exec]  # L-first 12D

            # IK target accumulate using first h_exec's world-frame delta (for next plan consistency)
            L_ori_delta_world = action_ee_12d[3:6] * cfg.rot_action_scale
            R_ori_delta_world = action_ee_12d[9:12] * cfg.rot_action_scale
            q_dL = _axis_angle_to_quat_xyzw(L_ori_delta_world)
            ik_target_L = _quat_multiply_xyzw(q_dL, ik_target_L)
            ik_target_L = ik_target_L / np.linalg.norm(ik_target_L)
            q_dR = _axis_angle_to_quat_xyzw(R_ori_delta_world)
            ik_target_R = _quat_multiply_xyzw(q_dR, ik_target_R)
            ik_target_R = ik_target_R / np.linalg.norm(ik_target_R)

            # Scripted finger cmd (Option B): +1=close until opening < T_FINGER, else 0.
            # env applies +1 cmd as pos -= cmd * FINGER_STEP_SIZE, clamped to [CLOSE, OPEN].
            opening_L = env._per_world_fk_jq[0, 7] + env._per_world_fk_jq[0, 8]
            opening_R = env._per_world_fk_jq[0, FRANKA_NUM_JOINTS + 7] + env._per_world_fk_jq[0, FRANKA_NUM_JOINTS + 8]
            finger_cmd_L = cfg.finger_close_rate if opening_L > T_FINGER else 0.0
            finger_cmd_R = cfg.finger_close_rate if opening_R > T_FINGER else 0.0

            # Compose 14D R-first action (env native)
            # env newton_clamp_env.py:28-34 layout: [R_pos, R_ori, L_pos, L_ori, R_finger, L_finger]
            # MPPI internal L-first 12D: [L_pos, L_ori, R_pos, R_ori]
            #
            # r_arm_only: L_pos / L_ori forced to 0 (CC2-1 + CC3-2 lenses); finger_cmd_L
            # uses scripted close-on-slip logic (line 791-792 above; CC3-5 lens).
            # finger_cmd_R gating preserved unchanged (CC2-1 lens).
            if r_arm_only:
                action_14d = np.array(
                    [
                        *action_ee_12d[6:9],  # R_pos
                        *action_ee_12d[9:12],  # R_ori
                        0.0,
                        0.0,
                        0.0,  # L_pos = 0 (frozen)
                        0.0,
                        0.0,
                        0.0,  # L_ori = 0 (frozen)
                        finger_cmd_R,  # R finger (existing scripted close gating preserved)
                        finger_cmd_L,  # L finger (existing scripted close, re-close on slip)
                    ],
                    dtype=np.float32,
                )
            else:
                action_14d = np.array(
                    [
                        *action_ee_12d[6:9],  # R_pos (from L-first[6:9])
                        *action_ee_12d[9:12],  # R_ori
                        *action_ee_12d[0:3],  # L_pos
                        *action_ee_12d[3:6],  # L_ori
                        finger_cmd_R,
                        finger_cmd_L,
                    ],
                    dtype=np.float32,
                )
            assert action_14d.shape == (14,), f"action shape {action_14d.shape} != (14,)"

            action_tensor = torch.from_numpy(action_14d).unsqueeze(0).to(device)  # (1, 14)

            # Record state BEFORE env.step (for trajectory)
            wp.synchronize()
            env_bq = env._state_0.body_q.numpy()
            env_flat = env_bq.view(np.float32).reshape(-1, 7)
            env_bws0 = env._bws[0]
            left_pos_now = env_flat[env_bws0 + EE_BODY_OFFSET, :3].astype(np.float32).copy()
            left_quat_now = _normalize_quat_w_positive(env_flat[env_bws0 + EE_BODY_OFFSET, 3:7]).astype(np.float32)
            right_pos_now = env_flat[env_bws0 + FRANKA_NUM_JOINTS + EE_BODY_OFFSET, :3].astype(np.float32).copy()
            right_quat_now = _normalize_quat_w_positive(
                env_flat[env_bws0 + FRANKA_NUM_JOINTS + EE_BODY_OFFSET, 3:7]
            ).astype(np.float32)
            # Cable body positions (for cable_pos_seq HDF5 key)
            cable_now = (
                env_flat[
                    env_bws0 + env._cable_body_offset : env_bws0 + env._cable_body_offset + env._cable_bodies_per_world,
                    :3,
                ]
                .astype(np.float32)
                .copy()
            )

            # env.step (single entry for physics/spring/sanitise/swap/obs)
            obs, reward, done, extras = env.step(action_tensor)

            # Extract post-step distances from env obs (42D layout per newton_clamp_env.py:11-26)
            obs_np = obs[0].cpu().numpy()
            # [30:33] right ori error axis-angle, [33:36] right pos error
            # [36:39] left ori error axis-angle, [39:42] left pos error
            dist_pos_R = float(np.linalg.norm(obs_np[33:36]))
            dist_ori_R = float(np.linalg.norm(obs_np[30:33]))
            dist_pos_L = float(np.linalg.norm(obs_np[39:42]))
            dist_ori_L = float(np.linalg.norm(obs_np[36:39]))

            # Post-step finger openings (env updated _per_world_fk_jq)
            opening_L_post = env._per_world_fk_jq[0, 7] + env._per_world_fk_jq[0, 8]
            opening_R_post = (
                env._per_world_fk_jq[0, FRANKA_NUM_JOINTS + 7] + env._per_world_fk_jq[0, FRANKA_NUM_JOINTS + 8]
            )

            # Record trajectory
            traj_actions.append(action_14d)
            traj_obs.append(obs_np.copy())
            traj_left_pos.append(left_pos_now)
            traj_left_quat.append(left_quat_now)
            traj_right_pos.append(right_pos_now)
            traj_right_quat.append(right_quat_now)
            traj_finger_L.append(float(opening_L_post))
            traj_finger_R.append(float(opening_R_post))
            traj_dist_pos_L.append(dist_pos_L)
            traj_dist_pos_R.append(dist_pos_R)
            traj_dist_ori_L.append(dist_ori_L)
            traj_dist_ori_R.append(dist_ori_R)
            traj_cable_pos.append(cable_now)

            # Sustained-K5 check (generator-side, mirrors env semantics).
            # r_arm_only: R-only criterion (CC2-4 lens, severity escalated to CRITICAL).
            if r_arm_only:
                clamped = (
                    dist_pos_R < GRIP_POS_THR_M and dist_ori_R < GRIP_ORI_THR_RAD and opening_R_post < GRIP_FINGER_THR_M
                )
            else:
                clamped = (
                    dist_pos_L < GRIP_POS_THR_M
                    and dist_pos_R < GRIP_POS_THR_M
                    and dist_ori_L < GRIP_ORI_THR_RAD
                    and dist_ori_R < GRIP_ORI_THR_RAD
                    and opening_L_post < GRIP_FINGER_THR_M
                    and opening_R_post < GRIP_FINGER_THR_M
                )
            if clamped:
                sustain_count += 1
                if sustain_count >= K_CLAMP and success_step < 0:
                    success = True
                    success_step = step
            else:
                sustain_count = 0

            # Diag CSV row (per-step, coarse)
            diag_csv.writerow(
                [
                    ep,
                    step,
                    diag.get("n_nan", 0),
                    diag.get("k_eff", K),
                    f"{diag.get('weight_entropy', 0.0):.4f}",
                    f"{diag.get('weight_mass_valid', 0.0):.6f}",
                    f"{diag.get('top1_weight', 0.0):.6f}",
                    int(diag.get("best_action_nan", False)),
                    f"{diag.get('t_ik_total_s', 0.0) + diag.get('t_physics_total_s', 0.0):.3f}",
                    f"{diag.get('cost_min', 0.0):.4f}",
                    f"{diag.get('cost_max', 0.0):.4f}",
                    f"{diag.get('cost_range', 0.0):.4f}",
                    f"{diag.get('cost_std', 0.0):.4f}",
                    f"{diag.get('ee_spread_max_mm', 0.0):.2f}",
                    f"{diag.get('drift_L_rad', 0.0):.4f}",
                    f"{diag.get('drift_R_rad', 0.0):.4f}",
                    diag.get("drop_count", 0),
                    sustain_count,
                    f"{opening_L_post:.4f}",
                    f"{opening_R_post:.4f}",
                    f"{cfg.pos_action_scale:.4f}",  # γ-3c: per-row for sweep analysis
                ]
            )

            step += 1

            # B3-β r_arm_only: L drift abort criterion (CC3-4 lens).
            # If L EE drifts > L_DRIFT_ABORT_M from post-preamble anchor, terminate episode.
            if r_arm_only and l_ee_anchor is not None:
                l_drift = float(np.linalg.norm(left_pos_now - l_ee_anchor))
                if l_drift > L_DRIFT_ABORT_M:
                    print(
                        f"  [L_DRIFT_ABORT] step={step} L EE drift {l_drift * 1000:.2f}mm > "
                        f"{L_DRIFT_ABORT_M * 1000:.0f}mm threshold"
                    )
                    break

            # env.step auto-reset suppressed via monkey-patch; check done manually.
            # If we want to early-break on success, uncomment:
            # if success and step >= success_step + 3: break  # grace window
            # For v3 we run until max_steps (固定長 demos per CC2-18 resolution) OR env done explosion.
            if done[0].item() and not success:
                # Env-detected terminal (likely explosion). Break episode.
                print(f"  [TERMINAL] step={step} env-reported done (explosion?)")
                break

        # End of episode
        if success:
            print(
                f"  SUCCESS at step {success_step}, final "
                f"pos L={traj_dist_pos_L[-1]:.4f}m R={traj_dist_pos_R[-1]:.4f}m "
                f"ori L={math.degrees(traj_dist_ori_L[-1]):.1f}° R={math.degrees(traj_dist_ori_R[-1]):.1f}° "
                f"finger L={traj_finger_L[-1] * 1000:.1f}mm R={traj_finger_R[-1] * 1000:.1f}mm"
            )
        else:
            print(
                f"  FAILED at step {step}, final "
                f"pos L={traj_dist_pos_L[-1]:.4f}m R={traj_dist_pos_R[-1]:.4f}m "
                f"ori L={math.degrees(traj_dist_ori_L[-1]):.1f}° R={math.degrees(traj_dist_ori_R[-1]):.1f}° "
                f"finger L={traj_finger_L[-1] * 1000:.1f}mm R={traj_finger_R[-1] * 1000:.1f}mm"
            )

        demo = {
            "action_delta": np.array(traj_actions, dtype=np.float32).reshape(-1, GRIP_HDF5_ACTION_DIM),
            "obs": np.array(traj_obs, dtype=np.float32).reshape(-1, 42),
            "left_ee_pos": np.array(traj_left_pos, dtype=np.float32),
            "right_ee_pos": np.array(traj_right_pos, dtype=np.float32),
            "left_ee_quat": np.array(traj_left_quat, dtype=np.float32),
            "right_ee_quat": np.array(traj_right_quat, dtype=np.float32),
            "finger_opening_L": np.array(traj_finger_L, dtype=np.float32),
            "finger_opening_R": np.array(traj_finger_R, dtype=np.float32),
            "dist_pos_left": np.array(traj_dist_pos_L, dtype=np.float32),
            "dist_pos_right": np.array(traj_dist_pos_R, dtype=np.float32),
            "dist_ori_left": np.array(traj_dist_ori_L, dtype=np.float32),
            "dist_ori_right": np.array(traj_dist_ori_R, dtype=np.float32),
            "cable_pos_seq": np.array(traj_cable_pos, dtype=np.float32)
            if traj_cable_pos
            else np.zeros((0, 0, 3), dtype=np.float32),
            "success": bool(success),
            "success_step": int(success_step),
            "sustain_count_final": int(sustain_count),
            "steps": int(step),
        }
        demos.append(demo)
        for dL, dR in zip(drifts_L_ep, drifts_R_ep):
            drifts_per_plan_LR.append([dL, dR])
        ep_max = max(max(drifts_L_ep, default=0.0), max(drifts_R_ep, default=0.0))
        drifts_per_episode_max.append(float(ep_max))

    diag_file.close()
    print(f"\n[DIAG] CSV → {diag_csv_path}")

    return demos, drifts_per_plan_LR, drifts_per_episode_max, cable_endpoints_L, cable_endpoints_R


# =========================================================================
# Success rates + HDF5 save + RUN_METRICS.
# =========================================================================


def compute_grip_success_rates(demos, r_arm_only=False):
    """S1 (pos)/S2 (ori)/S3 (combined+finger+sustained) rates from demos.

    Bimanual: S1 = both R+L pos < T_DIST, S2 = both R+L ori < T_ALIGN, S3 = sustained_K5.
    R-only: S1 = R pos < T_DIST, S2 = R ori < T_ALIGN, S3 = sustained_K5 (R-only criterion
    set by episode loop `clamped` predicate when r_arm_only=True).

    S3 uses env-native sustained_K5 criterion (demo.success True; CC2-4 lens.)
    """
    if not demos:
        return {"s1": 0.0, "s2": 0.0, "s3": 0.0}
    n1 = n2 = n3 = 0
    for d in demos:
        if len(d["dist_pos_right"]) == 0:
            continue
        if r_arm_only:
            pos_ok = d["dist_pos_right"][-1] < GRIP_POS_THR_M
            ori_ok = d["dist_ori_right"][-1] < GRIP_ORI_THR_RAD
        else:
            pos_ok = d["dist_pos_left"][-1] < GRIP_POS_THR_M and d["dist_pos_right"][-1] < GRIP_POS_THR_M
            ori_ok = d["dist_ori_left"][-1] < GRIP_ORI_THR_RAD and d["dist_ori_right"][-1] < GRIP_ORI_THR_RAD
        if pos_ok:
            n1 += 1
        if ori_ok:
            n2 += 1
        if d["success"]:  # sustained_K5 pos + ori + finger (R-only criterion if r_arm_only)
            n3 += 1
    n = len(demos)
    return {"s1": n1 / n, "s2": n2 / n, "s3": n3 / n}


def save_demos_hdf5_grip(
    demos,
    cfg,
    output_path,
    mppi_mode,
    finger_mode,
    cable_L_endpoint_mean=None,
    cable_R_endpoint_mean=None,
    r_arm_only=False,
):
    """Save Grip demos to HDF5 with v3 schema (env.step architecture).

    Schema includes both mppi_action_dim (12, L-first internal) and
    hdf5_action_dim (14, R-first env-native) for downstream converter clarity.

    r_arm_only writes single_arm="R" + generator_variant="r_only_v1" attrs (CC4-5 lens);
    all existing required attrs (action_layout="R-first", hdf5_action_dim=14, etc.) preserved.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    n_success = sum(1 for d in demos if d["success"])

    with h5py.File(output_path, "w") as f:
        meta = f.create_group("metadata")
        meta.attrs["generator"] = "mppi_grip_v3_envstep"
        meta.attrs["grip_version"] = GRIP_VERSION
        meta.attrs["architecture"] = GRIP_ARCHITECTURE
        # B3-β r_arm_only metadata (CC4-5 lens; preserved-attrs invariant maintained below)
        meta.attrs["single_arm"] = "R" if r_arm_only else "none"
        meta.attrs["generator_variant"] = "r_only_v1" if r_arm_only else "bimanual_v3_envstep"
        meta.attrs["K_EXEC"] = 1
        meta.attrs["K_MPPI"] = cfg.K
        meta.attrs["H"] = cfg.H
        meta.attrs["replan_interval"] = cfg.replan_interval
        meta.attrs["temperature_lambda"] = cfg.temperature_lambda
        meta.attrs["noise_sigma"] = cfg.noise_sigma
        meta.attrs["noise_correlation"] = cfg.noise_correlation
        meta.attrs["mppi_pos_action_scale"] = cfg.pos_action_scale
        meta.attrs["mppi_rot_action_scale"] = cfg.rot_action_scale
        meta.attrs["env_pos_action_scale_override"] = cfg.pos_action_scale
        meta.attrs["env_rot_action_scale_override"] = cfg.rot_action_scale
        meta.attrs["env_adaptive_pos_scale"] = False
        meta.attrs["m3_cost_scale"] = cfg.m3_cost_scale
        meta.attrs["cost_method"] = GRIP_COST_METHOD
        meta.attrs["p_cable_drop"] = P_CABLE_DROP
        meta.attrs["cable_drop_margin_m"] = CABLE_DROP_MARGIN_M
        meta.attrs["mppi_l_ori_ik_weight"] = cfg.l_ori_ik_weight
        meta.attrs["mppi_r_ori_ik_weight"] = cfg.r_ori_ik_weight
        meta.attrs["warm_start_offset_m"] = cfg.warm_start_offset_m
        meta.attrs["finger_mode"] = finger_mode
        meta.attrs["finger_close_rate"] = cfg.finger_close_rate
        meta.attrs["mppi_action_dim"] = GRIP_MPPI_ACTION_DIM
        meta.attrs["hdf5_action_dim"] = GRIP_HDF5_ACTION_DIM
        meta.attrs["action_dim"] = GRIP_HDF5_ACTION_DIM  # legacy alias
        meta.attrs["action_layout"] = GRIP_ACTION_LAYOUT
        meta.attrs["quat_convention"] = M3_QUAT_CONVENTION
        meta.attrs["quat_frame"] = M3_QUAT_FRAME
        meta.attrs["quat_semantic"] = M3_QUAT_SEMANTIC
        meta.attrs["mppi_mode"] = mppi_mode
        meta.attrs["success_threshold_m"] = GRIP_POS_THR_M
        meta.attrs["success_threshold_rad"] = GRIP_ORI_THR_RAD
        meta.attrs["success_threshold_finger_m"] = GRIP_FINGER_THR_M
        meta.attrs["success_eval"] = "sustained_K5_pos_ori_finger"
        meta.attrs["k_sustain"] = K_CLAMP
        meta.attrs["clamp_terminal_steps"] = CLAMP_TERMINAL_STEPS
        meta.attrs["n_demos"] = len(demos)
        meta.attrs["n_success"] = n_success
        if cable_L_endpoint_mean is not None:
            meta.attrs["cable_L_endpoint_mean"] = np.asarray(cable_L_endpoint_mean, dtype=np.float32)
        if cable_R_endpoint_mean is not None:
            meta.attrs["cable_R_endpoint_mean"] = np.asarray(cable_R_endpoint_mean, dtype=np.float32)

        for i, demo in enumerate(demos):
            g = f.create_group(f"episode_{i}")
            g.create_dataset("action_delta", data=demo["action_delta"])
            g.create_dataset("obs", data=demo["obs"])
            g.create_dataset("left_ee_pos", data=demo["left_ee_pos"])
            g.create_dataset("right_ee_pos", data=demo["right_ee_pos"])
            g.create_dataset("left_ee_quat", data=demo["left_ee_quat"])
            g.create_dataset("right_ee_quat", data=demo["right_ee_quat"])
            g.create_dataset("finger_opening_L", data=demo["finger_opening_L"])
            g.create_dataset("finger_opening_R", data=demo["finger_opening_R"])
            g.create_dataset("dist_pos_left", data=demo["dist_pos_left"])
            g.create_dataset("dist_pos_right", data=demo["dist_pos_right"])
            g.create_dataset("dist_ori_left", data=demo["dist_ori_left"])
            g.create_dataset("dist_ori_right", data=demo["dist_ori_right"])
            if demo["cable_pos_seq"].size > 0:
                g.create_dataset("cable_pos_seq", data=demo["cable_pos_seq"], compression="gzip")
            g.attrs["success"] = demo["success"]
            g.attrs["success_step"] = demo["success_step"]
            g.attrs["sustain_count_final"] = demo["sustain_count_final"]
            g.attrs["steps"] = demo["steps"]

    print(f"[HDF5] Saved {len(demos)} demos ({n_success} success, mode={mppi_mode}) → {output_path}")


def save_run_metrics_grip(
    demos, drifts_per_plan_LR, drifts_per_episode_max, wall_clock_s, cfg, output_dir, r_arm_only=False
):
    """Write per-lambda RUN_METRICS.json."""
    rates = compute_grip_success_rates(demos, r_arm_only=r_arm_only)

    drifts_arr = np.asarray(drifts_per_plan_LR, dtype=np.float64)
    if drifts_arr.size == 0:
        m1 = {"left": _stats([]), "right": _stats([])}
    else:
        m1_left = _stats(drifts_arr[:, 0])
        m1_left["per_plan"] = drifts_arr[:, 0].tolist()
        m1_right = _stats(drifts_arr[:, 1])
        m1_right["per_plan"] = drifts_arr[:, 1].tolist()
        m1 = {"left": m1_left, "right": m1_right}

    ep_max_arr = np.asarray(drifts_per_episode_max, dtype=np.float64)
    if ep_max_arr.size == 0:
        m2 = {"threshold_rad": DRIFT_THRESHOLD_RAD, "violation_count": 0, "total_episodes": 0, "violation_rate": 0.0}
    else:
        n_viol = int(np.sum(ep_max_arr > DRIFT_THRESHOLD_RAD))
        n_ep = int(len(ep_max_arr))
        m2 = {
            "threshold_rad": DRIFT_THRESHOLD_RAD,
            "violation_count": n_viol,
            "total_episodes": n_ep,
            "violation_rate": n_viol / n_ep if n_ep > 0 else 0.0,
            "per_episode_max": ep_max_arr.tolist(),
        }

    metrics = {
        "schema_version": "v1",
        "grip_version": GRIP_VERSION,
        "architecture": GRIP_ARCHITECTURE,
        "lambda": float(cfg.temperature_lambda),
        "n_demos": len(demos),
        "wall_clock_s": float(wall_clock_s),
        "S1_pos_success_rate": rates["s1"],
        "S2_ori_success_rate": rates["s2"],
        "S3_combined_sustained_rate": rates["s3"],
        "tangent_drift": m1,
        "drift_violation": m2,
        "cost_threshold_m": GRIP_POS_THR_M,
        "cost_threshold_rad": GRIP_ORI_THR_RAD,
        "cost_threshold_finger_m": GRIP_FINGER_THR_M,
        "cost_method": GRIP_COST_METHOD,
        "cost_scale": cfg.m3_cost_scale,
        "p_cable_drop": P_CABLE_DROP,
    }

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"run_metrics_lam{cfg.temperature_lambda}.json")
    with open(out_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[RUN_METRICS] {out_path}")
    return metrics


# =========================================================================
# CLI / main.
# =========================================================================


def main():
    parser = argparse.ArgumentParser(description=f"MPPI Grip demo generator ({GRIP_VERSION}, Option III env.step)")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument(
        "--finger-mode",
        choices=["scripted", "mppi"],
        default="scripted",
        help="Option B (scripted, MVP) or Option A (mppi, G3b deferred)",
    )
    parser.add_argument("--world-count", type=int, default=256, help="K_MPPI (K_EXEC fixed=1)")
    parser.add_argument("--n-demos", type=int, default=5)
    parser.add_argument("--max-steps", type=int, default=CLAMP_TERMINAL_STEPS)
    parser.add_argument("--single-lambda", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=str, default="data/mppi_demos_m3_grip")
    parser.add_argument("--diag-csv", type=str, default="/tmp/mppi_grip_metrics.csv")
    parser.add_argument("--no-mppi", action="store_true", help="Skip MPPI rollout (no-op baseline)")
    # γ-3c: pos_action_scale sweep (AC T9_F precedent; empirical primary blocker for Grip S3)
    # Mutex: --sweep (lambda) XOR --sweep-pos (pos_action_scale). --pos-scale allowed alongside --sweep.
    sweep_group = parser.add_mutually_exclusive_group()
    sweep_group.add_argument("--sweep", action="store_true", help="Run lambda sweep [0.3, 0.5, 1.0]")
    sweep_group.add_argument(
        "--sweep-pos",
        action="store_true",
        help="Run pos_action_scale sweep [0.015, 0.020, 0.025] (γ-3c, uses --single-lambda)",
    )
    parser.add_argument(
        "--pos-scale",
        type=float,
        default=None,
        help="Override cfg.pos_action_scale (default=cfg default 0.020). Range [0.005, 0.050]. "
        "Conflicts with --sweep-pos.",
    )
    # B3-β r_arm_only mode (CC-CLAMP-R-Phase-C2 Phase C2, audit B3 fix)
    parser.add_argument(
        "--r-arm-only",
        action="store_true",
        help="Generate R-arm-only demos for CLAMP_R adapter (audit B3 fix). "
        "L-arm scripted RECLAMP'd via preamble + frozen during MPPI. "
        "Cost / success criteria use R-only conditions. Output: demos_r_only.hdf5.",
    )
    # T-GC-EvalGap-Fix (2026-04-29): F1-inspired finger close warm-start (Rs override on iter 1+2 BLOCK fold-in).
    # Closes both fingers pre-MPPI to provide BC anchor for cold-start eval (addresses H3 root cause:
    # BC dominance + scripted finger_cmd noise brittleness, det 14.5% / stoch 0%).
    # Helper steps recorded in traj_* (differs from r_arm_only L_RECLAMP_PREAMBLE).
    # Mutually exclusive with --r-arm-only (CLAMP-R has its own preamble).
    parser.add_argument(
        "--warm-start-finger-close",
        action="store_true",
        help="Enable F1-inspired finger close warm-start for Grip-CLAMP (default disabled). "
        "Closes both fingers pre-MPPI, helper steps recorded in traj_* for BC anchor. "
        "Mutually exclusive with --r-arm-only.",
    )
    args = parser.parse_args()

    # γ-3c: --pos-scale validation + mutex
    if args.pos_scale is not None and args.sweep_pos:
        parser.error("--pos-scale conflicts with --sweep-pos (sweep uses fixed values [0.015, 0.020, 0.025])")
    # T-GC-EvalGap-Fix (2026-04-29): mutex check --warm-start-finger-close vs --r-arm-only
    if args.warm_start_finger_close and args.r_arm_only:
        parser.error(
            "--warm-start-finger-close conflicts with --r-arm-only "
            "(CLAMP-R already has L_RECLAMP_PREAMBLE for L finger close; F1 helper is for default dual-arm path)"
        )
    if args.pos_scale is not None:
        if args.pos_scale <= 0:
            parser.error(f"--pos-scale must be > 0 (got {args.pos_scale})")
        if args.pos_scale < 0.005 or args.pos_scale > 0.050:
            parser.error(f"--pos-scale must be in [0.005, 0.050] (got {args.pos_scale})")

    # CC5-7 fix: raise early at argparse parse, before env construction
    if args.finger_mode == "mppi":
        raise NotImplementedError(
            "Option A (14D MPPI sampled finger) is scoped to G3b next session. See m3_grip_design.md §4 phase table."
        )

    wp.init()
    wp.set_device(args.device)

    lambdas = [0.3, 0.5, 1.0] if args.sweep else [args.single_lambda]
    # γ-3c: pos_action_scale sweep axis (None → use cfg default; otherwise list driven by --sweep-pos or --pos-scale)
    pos_scales = [0.015, 0.020, 0.025] if args.sweep_pos else [args.pos_scale]
    mppi_mode = "off" if args.no_mppi else "on"
    # Sweep mode label for logging
    if args.sweep_pos:
        sweep_label = "POS-SWEEP"
    elif args.sweep:
        sweep_label = "SWEEP"
    else:
        sweep_label = "SINGLE"

    sweep_results = []
    # Outer product: (lam, pos_scale) pairs. Both --sweep and --sweep-pos are mutex (argparse enforced),
    # so only one of lambdas/pos_scales is multi-valued at a time.
    for lam in lambdas:
        for pos_scale in pos_scales:
            print(f"\n{'=' * 60}")
            pos_label = f"pos={pos_scale}" if pos_scale is not None else "pos=<cfg default>"
            print(f"  {sweep_label} lambda={lam} {pos_label}  mode={mppi_mode}")
            print(f"{'=' * 60}")

            cfg = get_default_mppi_grip_config()
            cfg.temperature_lambda = lam
            cfg.K = args.world_count
            cfg.device = args.device
            # γ-3c: apply pos_action_scale override (None → keep cfg default 0.020)
            if pos_scale is not None:
                cfg.pos_action_scale = pos_scale
            print(
                f"[CFG] K={cfg.K} H={cfg.H} replan={cfg.replan_interval} "
                f"pos={cfg.pos_action_scale} rot={cfg.rot_action_scale}"
            )

            # Diag CSV filename: distinguish by active sweep axis
            if args.sweep_pos:
                diag_csv = f"/tmp/mppi_grip_sweep_pos{int(round(cfg.pos_action_scale * 1000)):03d}.csv"
            elif args.sweep:
                diag_csv = f"/tmp/mppi_grip_sweep_lam{lam}.csv"
            else:
                diag_csv = args.diag_csv
            t0 = time.perf_counter()
            demos, drifts, drifts_per_ep_max, cable_L_list, cable_R_list = mppi_generate_demos_grip(
                cfg,
                args.device,
                max_steps=args.max_steps,
                n_demos=args.n_demos,
                seed=args.seed,
                diag_csv_path=diag_csv,
                r_arm_only=args.r_arm_only,
                warm_start_finger_close=args.warm_start_finger_close,
            )
            elapsed = time.perf_counter() - t0

            cable_L_mean = np.mean(cable_L_list, axis=0).astype(np.float32) if cable_L_list else None
            cable_R_mean = np.mean(cable_R_list, axis=0).astype(np.float32) if cable_R_list else None

            # γ-3c: HDF5 naming — pos sweep uses pos tag, λ sweep uses lam tag, single-run keeps legacy.
            # r_arm_only mode (B3-β) overrides naming to demos_r_only.hdf5 (CC4-4 lens).
            if args.r_arm_only:
                h5_name = "demos_r_only.hdf5"
            elif args.sweep_pos:
                h5_name = f"demos_pos{int(round(cfg.pos_action_scale * 1000)):03d}.hdf5"
            elif args.sweep:
                h5_name = f"demos_l{lam}.hdf5"
            else:
                h5_name = "demos_default.hdf5"
            h5_path = os.path.join(args.output_dir, h5_name)
            save_demos_hdf5_grip(
                demos,
                cfg,
                h5_path,
                mppi_mode,
                args.finger_mode,
                cable_L_endpoint_mean=cable_L_mean,
                cable_R_endpoint_mean=cable_R_mean,
                r_arm_only=args.r_arm_only,
            )
            metrics = save_run_metrics_grip(
                demos, drifts, drifts_per_ep_max, elapsed, cfg, args.output_dir, r_arm_only=args.r_arm_only
            )

            n_success = sum(1 for d in demos if d["success"])
            sweep_results.append(
                {
                    "lambda": lam,
                    "pos_action_scale": cfg.pos_action_scale,
                    "n_demos": len(demos),
                    "n_success": n_success,
                    "S1_pos": metrics["S1_pos_success_rate"],
                    "S2_ori": metrics["S2_ori_success_rate"],
                    "S3": metrics["S3_combined_sustained_rate"],
                    "drift_max_L": metrics["tangent_drift"]["left"].get("max", 0.0),
                    "drift_max_R": metrics["tangent_drift"]["right"].get("max", 0.0),
                    "drift_violation_rate": metrics["drift_violation"]["violation_rate"],
                    "wall_clock_s": round(elapsed, 1),
                }
            )

    if args.sweep or args.sweep_pos:
        print(f"\n{'=' * 78}")
        print(f"  Grip {'POS-SWEEP' if args.sweep_pos else 'SWEEP'} RESULTS")
        print(f"{'=' * 78}")
        for r in sweep_results:
            print(
                f"  lam={r['lambda']:>4.1f} pos={r['pos_action_scale']:>5.3f} "
                f"demos={r['n_demos']:>3d} succ={r['n_success']:>3d} "
                f"S1={r['S1_pos']:>6.1%} S2={r['S2_ori']:>6.1%} S3={r['S3']:>6.1%} "
                f"dL={math.degrees(r['drift_max_L']):>5.1f}° dR={math.degrees(r['drift_max_R']):>5.1f}° "
                f"t={r['wall_clock_s']:>6.1f}s"
            )
        csv_path = "/tmp/mppi_grip_sweep_pos.csv" if args.sweep_pos else "/tmp/mppi_grip_sweep.csv"
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(sweep_results[0].keys()))
            w.writeheader()
            w.writerows(sweep_results)
        print(f"  CSV: {csv_path}")

    # S3 gate (single-run only; MPPI ON). Skipped for both λ and pos sweeps.
    # r_arm_only mode uses 30% threshold (Phase C2 acceptance gate, CC2-6 lens) vs bimanual 50%.
    if not args.sweep and not args.sweep_pos and not args.no_mppi and len(sweep_results) == 1:
        s3 = sweep_results[0]["S3"]
        drift_v = sweep_results[0]["drift_violation_rate"]
        s3_threshold = 0.30 if args.r_arm_only else 0.50
        s3_threshold_label = "30% (B3-β r-only Phase C2 gate)" if args.r_arm_only else "50% (spec §6-2)"
        s3_fail = s3 < s3_threshold
        drift_fail = drift_v >= DRIFT_VIOLATION_RATE_LIMIT
        if s3_fail or drift_fail:
            reasons = []
            if s3_fail:
                reasons.append(f"S3={s3:.1%} < {s3_threshold_label}")
            if drift_fail:
                reasons.append(f"drift_violation={drift_v:.1%} >= {DRIFT_VIOLATION_RATE_LIMIT:.0%}")
            print("\n[BLOCKED_FOR_USER] " + " AND ".join(reasons))
            sys.exit(2)
        print(f"\n[S3 GATE] S3={s3:.1%} >= {s3_threshold_label}  [DRIFT GATE] violation={drift_v:.1%} → PASS")


if __name__ == "__main__":
    main()
