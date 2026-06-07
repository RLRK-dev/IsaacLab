#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MPPI demo trajectory generation for InsertIntoClip (IC) skill — approach-first MVP.

Architecture (Option III env.step hybrid, Grip G3a precedent, rs approved 2026-04-24):
  - env (NewtonInsertClipEnv, K_EXEC=1, mode={approach|insert}): episode execution via env.step()
  - mppi_scene (build_multiworld_scene, K_MPPI=cfg.K): parallel K-sample rollout for cost

env.step() handles physics/spring/sanitise/state-swap internally (same
auto-resolution of the v2.1 sanitise/cadence/state-swap/revert/K items as Grip).

IC-specific differences vs Grip G3a:
  - action_dim = 12 (no finger cmd; fingers always CLOSED per env :21 contract)
  - target = FIXED world-frame GROOVE_CENTER_POS (per-world identical, NOT per-world
    cable tangent). GROOVE_TARGET_QUAT is world-fixed (cable Y-axis aligned).
  - Cost adds cable_seg_cost term (nearest cable seg → groove center XY) rewarding
    cable shape alignment — Grip rewards clamp→cable, IC rewards cable→groove.
  - Mode branch: approach (12mm, POS_SCALE=0.020 IC-CRIT-1 override, H=25,
    replan=8) vs insert (3mm, POS_SCALE=0.003, H=30, replan=10, DEFERRED to G10+).
  - Groove seg selection: XY nearest-to-GROOVE_CENTER_POS (env
    `_compute_groove_seg_indices` parity, NOT cable-tangent like Grip).
  - Warm-start SLERP (approach only): pre-align IK accumulator to GROOVE_TARGET_QUAT
    (MVP inline ~10 LoC per CC6 NHA C2 recommendation; full-slerp loop deferred).
  - Cost uses compute_clamp_pos (fingertip) NOT raw EE per IC-HIGH-1.
  - Rollout applies LEFT_ACTION_DAMPING=0.3 to L arm deltas per IC-HIGH-2.
  - EE Z clipped to [PUSH_Z, LIFT_Z+0.05] in rollout per IC-HIGH-3.
  - 6-term max cost with cable_seg_ori term per IC-HIGH-7.

Monkey-patches on env (instance attribute shadowing, reversible):
  - env.POS_ACTION_SCALE = cfg.pos_action_scale (override env default 0.015 approach
    / 0.003 insert)
  - env.ROT_ACTION_SCALE = cfg.rot_action_scale (0.05, env default)
  - env.ADAPTIVE_POS_SCALE = False  (CRITICAL: fixed scale per Grip Option III)
  - env.max_episode_length = 100_000  (generator owns max_steps)
  - env._reset_worlds = no-op intra-episode; manual inter-episode reset

Usage:
    source ~/env_isaaclab6/bin/activate
    cd ~/IsaacLab
    PYTHONPATH=$PYTHONPATH:thread_isaac_lab/scripts:thread_isaac_lab/configs:thread_isaac_lab/envs \\
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/generate_demos_mppi_m3_insert_clip.py \\
        --device cuda:0 --world-count 4 --n-demos 5 --single-lambda 0.3 --mode approach

References:
    Design spec: thread-vault/08-DA-MPPI/01-Dashboard/m3_ic_design.md (2026-04-24)
    Grip G3a precedent: scripts/generate_demos_mppi_m3_grip.py (sha 65c4cbea…)
    G1 config: configs/mpc_config_ic.py (sha 340c3769…)
    Fixes applied: /tmp/ic_g3_propose_revised_fixes.md (1 CRIT + 8 HIGH + NHA conditions)
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

# NOTE: compute_cable_tangent + compute_hand_quat_for_cable retained for
# diagnostic tangent drift AND for the cable_seg_ori cost term (IC-HIGH-7).
from cable_orientation_utils import compute_cable_tangent, compute_hand_quat_for_cable

# Reuse MPPI primitives from M2
from generate_demos_mppi_m2 import (
    DT,
    RL_SIM_SUBSTEPS,
    mppi_weights,
    sample_action_sequences,
    update_kinematic_bodies,
)

# Reuse M3 quaternion/drift/stats helpers + MppiIKSolverM3
# DO NOT import compute_cost_targets_from_cable (AC-specific, endpoint-based)
# DO NOT import M3_ACTION_DIM/M3_ACTION_LAYOUT (use local IC_* constants)
from generate_demos_mppi_m3 import (
    DRIFT_THRESHOLD_RAD,
    DRIFT_VIOLATION_RATE_LIMIT,
    M3_QUAT_CONVENTION,
    M3_QUAT_FRAME,
    M3_QUAT_SEMANTIC,
    MppiIKSolverM3,
    _stats,
    get_ee_poses_dual,
    slerp_numpy,
)
from mpc_config_ic import get_default_mppi_ic_config, get_insert_mppi_ic_config
from newton_insert_clip_env import NewtonInsertClipEnv
from newton_skill_env_base import (
    EE_BODY_OFFSET,
    FRANKA_NUM_JOINTS,
    build_multiworld_scene,
    compute_clamp_pos,
)
from newton_skill_env_base import axis_angle_to_quat_xyzw as _axis_angle_to_quat_xyzw
from newton_skill_env_base import normalize_quat_w_positive as _normalize_quat_w_positive
from newton_skill_env_base import quat_distance as _quat_distance
from newton_skill_env_base import quat_multiply_xyzw as _quat_multiply_xyzw
from task_config import (
    CABLE_RADIUS,
    CABLE_SEG_LEN,
    CABLE_SEGMENTS,
    CLIP1_X,
    CLIP1_Y,
    CLIP_BASE_HEIGHT,
    EE_TO_FINGERTIP,  # F1 2026-04-26 P1: warm-start target Z compute
    FINGER_CLOSE_POS,
    GRASP_X,
    GRIP_HALF_SPAN,  # B+ 2026-04-25 F4: per-arm target offset
    GROOVE_BODIES_MIN,
    GROOVE_CENTER_Z,
    INSERT_TERMINAL_STEPS,
    INSERT_TERMINAL_STEPS_INSERT,
    K_INSERT,
    LIFT_Z,
    PUSH_Z,
    T_DIST_APPROACH,
    T_GROOVE,
    T_SEAT,
    TABLE_HEIGHT,
)

# =========================================================================
# Module constants
# =========================================================================

IC_VERSION = "v1.0"
IC_ARCHITECTURE = "env.step + mppi_scene separate (Option III, Grip G3a precedent)"

# Action layout — IC is 12D both internally and on the HDF5 wire.
# MPPI internal: L-first 12D = [L_pos(3), L_ori(3), R_pos(3), R_ori(3)]
# HDF5/env:      R-first 12D = [R_pos(3), R_ori(3), L_pos(3), L_ori(3)]  (env :21 native)
# No finger action — fingers always CLOSED (env _apply_actions_batch :1447-1452, :1504-1509).
IC_MPPI_ACTION_DIM = 12
IC_HDF5_ACTION_DIM = 12
IC_ACTION_LAYOUT = "R-first"

IC_COST_METHOD = (
    "max(pos_L, pos_R, m3_cost_scale*ori_L, m3_cost_scale*ori_R, "
    "cable_seg_cost_scale*seg_dist_groove, seg_ori_scale*seg_ori_dist_groove) + P_drop"
)

# Groove target (FIXED world frame per env :217, :221) — per-world identical.
# Single instance: rs approved mono-clip MVP; clip_x/clip_y overrides deferred to future sweep.
GROOVE_CENTER_POS = np.array([CLIP1_X, CLIP1_Y, GROOVE_CENTER_Z], dtype=np.float32)
# B+ 2026-04-25 F4 fix: per-arm targets matching env INSERT_EE_LEFT/RIGHT (env :228-229).
# Both arms targeting same GROOVE_CENTER_POS creates ill-posed L-R cost saddle (cable arc
# 120mm taut prevents both arms reaching same point). Per-arm targets eliminate the
# coupling conflict: L targets (clip_x, clip_y - GRIP_HALF_SPAN, groove_z), R mirrors.
TARGET_POS_L = np.array([CLIP1_X, CLIP1_Y - GRIP_HALF_SPAN, GROOVE_CENTER_Z], dtype=np.float32)  # (0.35, 0.090, 0.809)
TARGET_POS_R = np.array([CLIP1_X, CLIP1_Y + GRIP_HALF_SPAN, GROOVE_CENTER_Z], dtype=np.float32)  # (0.35, 0.210, 0.809)
# GROOVE_TARGET_QUAT: per env :219-221, hand quat aligned with cable Y-axis tangent (0, 1, 0).
GROOVE_TARGET_QUAT = _normalize_quat_w_positive(
    np.asarray(compute_hand_quat_for_cable(np.array([0.0, 1.0, 0.0], dtype=np.float32)), dtype=np.float32)
).astype(np.float32)

# Success thresholds (SSOT task_config.py) — used for MPPI internal success eval + S1/S2/S3.
IC_T_DIST_APPROACH = T_DIST_APPROACH  # 0.012
IC_T_GROOVE = T_GROOVE  # 0.003
IC_T_SEAT_COS = T_SEAT  # 0.85 (used as |q1·q2| > cos threshold)
# IC-CC3 CHALLENGE #1 fix: removed dead `if False else` conditional.
IC_T_SEAT_RAD = math.acos(IC_T_SEAT_COS)  # 0.5548 rad ≈ 31.8°

# Cable drop detection — IC uses env's DROP_Z_THRESH semantics (below table surface).
# approach mode env :186 DROP_Z_THRESH = TABLE_HEIGHT + CLIP_BASE_HEIGHT = 0.805
# insert  mode env :276 DROP_Z_THRESH = TABLE_HEIGHT = 0.80
CABLE_DROP_Z_THR_APPROACH = TABLE_HEIGHT + CLIP_BASE_HEIGHT  # 0.805
CABLE_DROP_Z_THR_INSERT = TABLE_HEIGHT  # 0.80
P_CABLE_DROP = 100.0  # Grip/AR parity

# Finger joint coord indices (pinned CLOSED in mppi_scene rollout).
FINGER_JOINT_COORD_INDICES = [7, 8, FRANKA_NUM_JOINTS + 7, FRANKA_NUM_JOINTS + 8]

# Groove_seg window (env :202 GROOVE_SEG_WINDOW=1).
GROOVE_SEG_WINDOW = 1

# IC-HIGH-2: Mirror env class attr :198 (newton_insert_clip_env.py).
# Rollout applies damping to L arm deltas (pos + ori) to match env execution.
# 2026-04-26 P2 revert: 0.5 → 0.3 (env-matching, plan-execute consistency).
# Original 0.3 was hypothesized to cause L UP bias under shared GROOVE target;
# F4 per-arm fix (project_ic_perarm_target_fix_2026-04-25) removes that root cause.
# Z plateau analysis (project_ic_z_plateau_analysis_2026-04-26) confirms
# action-velocity correlation=1.000, mismatch 0.5/0.3 created plan-vs-env
# dynamics divergence; reverting to 0.3 aligns MPPI plan optimization with
# true env L authority. ENV-SIDE damping unchanged (CC#3 frozen scope).
LEFT_ACTION_DAMPING = 0.3

# IC-HIGH-3: EE Z clip bounds (mirror env :1457, :1473 in _apply_actions_batch).
PUSH_Z_CLIP_MIN = PUSH_Z  # 1.025
PUSH_Z_CLIP_MAX = LIFT_Z + 0.05  # 1.170

# Pre-MPPI position warm-start (F1 P1 implementation 2026-04-26).
# Bypass initial 91mm Z gap by descending L+R EE to target_Z + WARM_START_HEIGHT_ABOVE_GROOVE
# before MPPI rollout starts. Reduces MPPI's effective gap to WARM_START_HEIGHT_ABOVE_GROOVE.
# Uses env.step() with controlled descent action for real-physics safety (no kinematic teleport).
# Reference: project_ic_z_plateau_analysis_2026-04-26.md (action-velocity Pearson 1.0000,
# L EE Z plateau ~1.074m vs target 1.029m due to 91mm initial gap exceeding 200-step budget).
WARM_START_POSITION_ENABLE = True  # F1 enable flag
WARM_START_HEIGHT_ABOVE_GROOVE = 0.011  # 11mm above target Z=0.809 → fingertip 0.820, EE Z 1.040
WARM_START_MAX_STEPS = 50  # max env.step iterations during warm-start
WARM_START_TOLERANCE_M = 0.005  # 5mm tolerance for descent termination
WARM_START_ACTION_Z_MAGNITUDE = 0.5  # action_z command during warm-start (-1..1 normalized)


# =========================================================================
# base_scene_to_m2_info + clone_env_to_mppi — verbatim from Grip G3a (FM-10 pattern).
# =========================================================================


def base_scene_to_m2_info(scene):
    """Translate build_multiworld_scene dict to M2-compat info keys.

    Identical to Grip G3a:153-166.
    """
    return {
        "bws": scene["bws"],
        "bodies_per_world": scene["bodies_per_world"],
        "cable_per_world": scene["cable_bodies_per_world"],
        "cable_offset": scene["cable_body_offset"],
        "left_body_start": 0,
        "right_body_start": FRANKA_NUM_JOINTS,
    }


def clone_env_to_mppi(env, mppi_scene, mppi_info, K):
    """Copy env._state_0 world 0 body_q/body_qd into mppi_scene all K worlds.

    Identical to Grip G3a:174-217 — env access fields are common VecEnv attributes
    (``_bws``, ``_state_0``, ``_bodies_per_world``). Both clamp_env and
    insert_clip_env expose the same layout.
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
# IC-specific helpers (groove_seg, drop_mask, nearest_seg_pos, seg_tangents).
# =========================================================================


def compute_ic_groove_seg_indices(state, info, world_count, window=GROOVE_SEG_WINDOW):
    """Compute per-world ±window cable seg indices nearest to GROOVE_CENTER_POS (XY).

    Mirrors newton_insert_clip_env._compute_groove_seg_indices (:893-905) but
    reads from mppi_scene state via info dict (M2-compat).

    Returns:
        indices: (world_count, 2*window+1) int32 — groove_n±window clipped to [0, cpw-1].
    """
    bq = state.body_q.numpy()
    bws = info["bws"]
    co = info["cable_offset"]
    cpw = info["cable_per_world"]
    n_seg = 2 * window + 1

    indices = np.zeros((world_count, n_seg), dtype=np.int32)
    flat = bq.view(np.float32).reshape(-1, 7)
    clip_xy = GROOVE_CENTER_POS[:2]  # fixed world-frame (CLIP1_X, CLIP1_Y)

    for w in range(world_count):
        ws = bws[w]
        cable_pos = flat[ws + co : ws + co + cpw, :3]
        dists_xy = np.linalg.norm(cable_pos[:, :2] - clip_xy, axis=1)
        groove_n = int(np.argmin(dists_xy))
        indices[w] = np.clip(np.arange(groove_n - window, groove_n + window + 1), 0, cpw - 1)

    return indices


def compute_cable_drop_mask(state, info, K, drop_z_thr):
    """Detect cable-dropped worlds (cable min z < threshold).

    IC uses env's DROP_Z_THRESH semantics (below clip base for approach, below
    table for insert). Parametrised on threshold (approach vs insert).

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
        if cable_z.min() < drop_z_thr:
            dropped[w] = True
    return dropped


def compute_ic_nearest_seg_pos_per_world(state, info, K, groove_seg_indices):
    """Extract nearest cable seg 3D position per world (center of window).

    For cable_seg_cost term: distance from nearest-to-groove cable seg to fixed
    GROOVE_CENTER_POS (3D, not just XY).

    Returns:
        seg_pos: (K, 3) float32 — center-of-window seg 3D pos per world.
    """
    bq = state.body_q.numpy()
    flat = bq.view(np.float32).reshape(-1, 7)
    bws = info["bws"]
    co = info["cable_offset"]
    n_seg = groove_seg_indices.shape[1]
    mid = n_seg // 2  # center index within window

    seg_pos = np.zeros((K, 3), dtype=np.float32)
    for w in range(K):
        ws = bws[w]
        center_idx = int(groove_seg_indices[w, mid])
        body_idx = ws + co + center_idx
        seg_pos[w] = flat[body_idx, :3]

    return seg_pos


def compute_ic_cable_seg_tangents(state, info, K, groove_seg_indices):
    """Compute cable tangent at nearest-to-groove segment per world.

    Used for IC-HIGH-7 (cable_seg_ori cost term): cable tangent → GROOVE_TARGET_QUAT
    alignment mirrors env reward :1224 seg_quat computation.

    Returns:
        tangents: (K, 3) float32 — unit tangent vector at center seg per world.
    """
    bq = state.body_q.numpy()
    flat = bq.view(np.float32).reshape(-1, 7)
    bws = info["bws"]
    co = info["cable_offset"]
    cpw = info["cable_per_world"]
    n_seg = groove_seg_indices.shape[1]
    mid = n_seg // 2

    tangents = np.zeros((K, 3), dtype=np.float32)
    for w in range(K):
        ws = bws[w]
        center_idx = int(groove_seg_indices[w, mid])
        # Build 3-seg window of cable positions (indexed by cable-local).
        cable_pos_local = np.zeros((3, 3), dtype=np.float32)
        for i, offset in enumerate((-1, 0, 1)):
            idx = int(np.clip(center_idx + offset, 0, cpw - 1))
            body_idx = ws + co + idx
            cable_pos_local[i] = flat[body_idx, :3]
        # compute_cable_tangent reads index 1 of the local 3-body window.
        tangents[w] = compute_cable_tangent(cable_pos_local, 1)

    return tangents


# =========================================================================
# MPPI rollout + cost (mppi_scene only; env untouched during rollout).
# =========================================================================


def rollout_and_cost_ic(
    mppi_scene, mppi_info, ik_solver, per_world_jq, K, H, cfg,
    groove_seg_indices, ik_target_quat_L_init, ik_target_quat_R_init, drop_z_thr,
):  # fmt: skip
    """Rollout K trajectories in mppi_scene for H steps with 12D L-first actions.

    Cost = max(pos_L, pos_R, m3_cost_scale*ori_L, m3_cost_scale*ori_R,
               cable_seg_cost_scale*seg_dist_groove,
               seg_ori_scale*seg_ori_dist_groove) + P_DROP*I(drop).
    Target = FIXED GROOVE_CENTER_POS + GROOVE_TARGET_QUAT (world frame, per-world
             identical — unlike Grip per-world cable tangent).
    Fingers pinned CLOSED in mppi_scene throughout (env contract; IC never opens).
    L arm deltas damped by LEFT_ACTION_DAMPING (IC-HIGH-2) to match env execution.
    EE Z clipped to [PUSH_Z, LIFT_Z+0.05] (IC-HIGH-3) to match env constraint.

    Returns:
        actions: (K, H, 12) sampled action sequences
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

    # Per-plan dominance tracking (IC-HIGH-4 diag CSV extensions).
    max_pos_L_plan = 0.0
    max_pos_R_plan = 0.0
    max_seg_dist_plan = 0.0
    max_m3_ori_L_plan = 0.0
    max_m3_ori_R_plan = 0.0
    max_seg_ori_plan = 0.0  # B+ 2026-04-25: track scaled seg_ori contribution

    # Sample K action sequences (caller provides rng)
    rng = np.random.default_rng(cfg.K + int(time.time_ns() % 1_000_000))
    actions = sample_action_sequences(K, H, IC_MPPI_ACTION_DIM, cfg.noise_sigma, cfg.noise_correlation, rng)

    # Tangent drift capture (world 0 plan start) — endpoint-based diagnostic only.
    w0 = bws[0]
    flat_start = state_0.body_q.numpy().view(np.float32).reshape(-1, 7)
    cable_start = flat_start[w0 + co : w0 + co + cpw, :3].copy()
    tangent_L_start = compute_cable_tangent(cable_start, 0)
    tangent_R_start = compute_cable_tangent(cable_start, cpw - 1)

    # IK target init (tile warm-start-end or current, (K, 4) xyzw float32)
    ik_tgt_L = np.tile(ik_target_quat_L_init[None].astype(np.float32), (K, 1))
    ik_tgt_R = np.tile(ik_target_quat_R_init[None].astype(np.float32), (K, 1))

    # Targets (broadcast to all K worlds, identical per world — KEY IC DIFF vs Grip).
    # B+ 2026-04-25 F4 fix: per-arm targets matching env INSERT_EE_LEFT/RIGHT (env :228-229).
    # Old single GROOVE_CENTER_POS for both arms was ill-posed (cable arc constraint).
    target_pos_world = GROOVE_CENTER_POS  # (3,) — kept for seg_dist_groove (cable seg → groove ctr)
    target_pos_L = TARGET_POS_L  # (3,) const = GROOVE + [0, -GRIP_HALF_SPAN, 0]
    target_pos_R = TARGET_POS_R  # (3,) const = GROOVE + [0, +GRIP_HALF_SPAN, 0]
    target_quat_world = GROOVE_TARGET_QUAT  # (4,) const

    for h in range(H):
        # Current EE pos reference (pre-IK, post-physics previous step)
        (left_ee, _), (right_ee, _) = get_ee_poses_dual(state_0, mppi_info, K)

        # 12D L-first split. IC-HIGH-2: damp L arm deltas by LEFT_ACTION_DAMPING.
        L_pos_delta = actions[:, h, 0:3] * cfg.pos_action_scale * LEFT_ACTION_DAMPING
        L_ori_delta = actions[:, h, 3:6] * cfg.rot_action_scale * LEFT_ACTION_DAMPING
        R_pos_delta = actions[:, h, 6:9] * cfg.pos_action_scale
        R_ori_delta = actions[:, h, 9:12] * cfg.rot_action_scale

        target_L_pos = left_ee + L_pos_delta
        target_R_pos = right_ee + R_pos_delta

        # IC-HIGH-3: clip EE Z to env-enforced bounds [PUSH_Z, LIFT_Z+0.05].
        target_L_pos[:, 2] = np.clip(target_L_pos[:, 2], PUSH_Z_CLIP_MIN, PUSH_Z_CLIP_MAX)
        target_R_pos[:, 2] = np.clip(target_R_pos[:, 2], PUSH_Z_CLIP_MIN, PUSH_Z_CLIP_MAX)

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

        # Pin fingers CLOSED in rollout (IC env :1447-1452 contract; IC never opens).
        for fc in FINGER_JOINT_COORD_INDICES:
            jq_solved[:, fc] = FINGER_CLOSE_POS
        # CC2 ITEM #9 / CC6-C5 invariant check: confirm fingers are actually pinned.
        assert np.all(jq_solved[:, FINGER_JOINT_COORD_INDICES] == FINGER_CLOSE_POS), (
            "IC rollout invariant violated: fingers not pinned CLOSED"
        )

        fk_body_q = ik_solver.eval_fk_batch(jq_solved)
        t_ik_total += time.perf_counter() - t0_ik

        update_kinematic_bodies(state_0, fk_body_q, mppi_info, K)

        # EE spread diagnostic
        (ik_left, _), (ik_right, _) = get_ee_poses_dual(state_0, mppi_info, K)
        valid_idx = ~nan_mask
        if valid_idx.sum() > 1:
            ee_spread_max_left = max(ee_spread_max_left, float(np.sqrt(np.sum(np.var(ik_left[valid_idx], axis=0)))))
            ee_spread_max_right = max(ee_spread_max_right, float(np.sqrt(np.sum(np.var(ik_right[valid_idx], axis=0)))))

        # Physics step (mppi_scene, kinematic fingers OK)
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

        # IC cost (6-term max, IC-HIGH-1 + IC-HIGH-7).
        pos_dist_L = np.zeros(K, dtype=np.float32)
        pos_dist_R = np.zeros(K, dtype=np.float32)
        ori_dist_L = np.zeros(K, dtype=np.float32)
        ori_dist_R = np.zeros(K, dtype=np.float32)
        seg_ori_dist_groove = np.zeros(K, dtype=np.float32)

        # IC-HIGH-7: cable tangent quat → GROOVE_TARGET_QUAT per world (matches env reward semantics).
        seg_tangents = compute_ic_cable_seg_tangents(state_0, mppi_info, K, groove_seg_indices)

        for k in range(K):
            if nan_mask[k]:
                continue

            # IC-HIGH-1: cost uses compute_clamp_pos (fingertip) NOT raw EE.
            # compute_clamp_pos = ee_pos + quat_rotate(ee_quat, [0, 0, +EE_TO_FINGERTIP])
            q_L = _normalize_quat_w_positive(achieved_quat_L[k])
            q_R = _normalize_quat_w_positive(achieved_quat_R[k])
            clamp_L_k = compute_clamp_pos(achieved_pos_L[k], q_L)
            clamp_R_k = compute_clamp_pos(achieved_pos_R[k], q_R)
            pos_dist_L[k] = np.linalg.norm(clamp_L_k - target_pos_L)  # B+ 2026-04-25 F4: per-arm
            pos_dist_R[k] = np.linalg.norm(clamp_R_k - target_pos_R)  # B+ 2026-04-25 F4: per-arm

            ori_dist_L[k] = _quat_distance(q_L, target_quat_world)
            ori_dist_R[k] = _quat_distance(q_R, target_quat_world)

            # IC-HIGH-7: seg_quat from cable tangent, distance to GROOVE_TARGET_QUAT.
            seg_quat_k = _normalize_quat_w_positive(
                np.asarray(compute_hand_quat_for_cable(seg_tangents[k]), dtype=np.float32)
            )
            seg_ori_dist_groove[k] = _quat_distance(seg_quat_k, target_quat_world)

        # IC cable_seg_cost term: nearest cable seg → groove center 3D distance.
        seg_pos_k = compute_ic_nearest_seg_pos_per_world(state_0, mppi_info, K, groove_seg_indices)
        seg_dist_groove = np.linalg.norm(seg_pos_k - target_pos_world[None, :], axis=1).astype(np.float32)

        # Cable drop detection
        drop_mask = compute_cable_drop_mask(state_0, mppi_info, K, drop_z_thr)

        # Method C cost (max-based) — IC-specific 6-term max + P_drop penalty.
        step_cost = np.maximum.reduce(
            [
                pos_dist_L,
                pos_dist_R,
                cfg.m3_cost_scale * ori_dist_L,
                cfg.m3_cost_scale * ori_dist_R,
                cfg.cable_seg_cost_scale * seg_dist_groove,
                cfg.seg_ori_scale * seg_ori_dist_groove,  # B+ 2026-04-25: separate field
            ]
        ).astype(np.float32)
        step_cost += np.where(drop_mask, P_CABLE_DROP, 0.0).astype(np.float32)
        costs += np.where(nan_mask, 0.0, step_cost)

        # IC-HIGH-4: track per-plan maxima for dominance analysis.
        valid_dom_mask = ~nan_mask
        if np.any(valid_dom_mask):
            max_pos_L_plan = max(max_pos_L_plan, float(np.max(pos_dist_L[valid_dom_mask])))
            max_pos_R_plan = max(max_pos_R_plan, float(np.max(pos_dist_R[valid_dom_mask])))
            max_seg_dist_plan = max(max_seg_dist_plan, float(np.max(seg_dist_groove[valid_dom_mask])))
            max_m3_ori_L_plan = max(max_m3_ori_L_plan, float(np.max(cfg.m3_cost_scale * ori_dist_L[valid_dom_mask])))
            max_m3_ori_R_plan = max(max_m3_ori_R_plan, float(np.max(cfg.m3_cost_scale * ori_dist_R[valid_dom_mask])))
            max_seg_ori_plan = max(
                max_seg_ori_plan, float(np.max(cfg.seg_ori_scale * seg_ori_dist_groove[valid_dom_mask]))
            )

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

    drop_final_mask = compute_cable_drop_mask(state_0, mppi_info, K, drop_z_thr)
    drop_count = int(drop_final_mask.sum())

    n_nan = int(nan_mask.sum())
    if n_nan > 0:
        print(f"  [NaN] {n_nan}/{K} worlds had NaN ({n_nan * 100 // K}%)")
    ee_spread_max = max(ee_spread_max_left, ee_spread_max_right)

    return (
        actions, costs, n_nan, t_ik_total, t_physics_total, ee_spread_max,
        drift_L, drift_R, drop_count,
        max_pos_L_plan, max_pos_R_plan, max_seg_dist_plan, max_m3_ori_L_plan, max_m3_ori_R_plan,
        max_seg_ori_plan,
    )  # fmt: skip


# =========================================================================
# MPPI plan: clone env state, rollout, weight, return best EE action.
# =========================================================================


def mppi_plan(
    env, mppi_scene, mppi_info, ik_solver, cfg, cfg_K,
    per_world_jq_ref, ik_target_L, ik_target_R, drop_z_thr,
):  # fmt: skip
    """One MPPI plan step: clone env state → rollout → weight → best action.

    Returns:
        best_action_ee: (H, 12) weighted-mean action sequence (L-first 12D)
        diag: dict with n_nan, cost_range, weight_entropy, top1_w, drift_L, drift_R, etc.
    """
    K = cfg_K

    # Clone env state → mppi_scene all K worlds
    clone_env_to_mppi(env, mppi_scene, mppi_info, K)

    # Compute per-world groove seg indices ONCE per plan (U3 mitigation parity with AC).
    groove_seg_indices = compute_ic_groove_seg_indices(mppi_scene["state_0"], mppi_info, K, window=GROOVE_SEG_WINDOW)

    # Initialize per_world_jq for mppi_scene IK solver (from env's FK state world 0, tiled)
    per_world_jq = np.tile(per_world_jq_ref[None].astype(np.float64), (K, 1))

    # Rollout + cost
    (
        actions, costs, n_nan, t_ik, t_phys, ee_spread,
        drift_L, drift_R, drop_count,
        max_pos_L, max_pos_R, max_seg_dist, max_m3_ori_L, max_m3_ori_R,
        max_seg_ori,
    ) = rollout_and_cost_ic(
        mppi_scene, mppi_info, ik_solver, per_world_jq, K, cfg.H, cfg,
        groove_seg_indices, ik_target_L, ik_target_R, drop_z_thr,
    )  # fmt: skip

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
        # IC-HIGH-4 dominance diagnostics
        "max_pos_L": max_pos_L,
        "max_pos_R": max_pos_R,
        "max_seg_dist_groove": max_seg_dist,
        "max_m3_ori_L": max_m3_ori_L,
        "max_m3_ori_R": max_m3_ori_R,
        "max_seg_ori_groove": max_seg_ori,  # B+ 2026-04-25
    }
    return best_action_ee, diag


# =========================================================================
# Warm-start SLERP helper (simplified MVP per CC6-C2 ~10 LoC).
# =========================================================================


def _warm_start_slerp_ic(cfg, ik_target_L_init, ik_target_R_init):
    """Warm-start IK target quat toward GROOVE_TARGET_QUAT (no physics loop).

    Simpler than AC warm_start_approach_m3 (no 40-step physics) because IC target
    is world-fixed and identical for L and R. Sets IK accumulator directly
    (alpha=1.0) so MPPI doesn't waste the first plan realigning ori.
    cfg.warm_start_offset_m is retained for future full-SLERP extension (D7).

    Returns:
        ik_target_L, ik_target_R: (4,) float32 xyzw pre-aligned accumulators.
    """
    target_world = GROOVE_TARGET_QUAT.copy()
    q_L_warm = _normalize_quat_w_positive(slerp_numpy(ik_target_L_init, target_world, alpha=1.0)).astype(np.float32)
    q_R_warm = _normalize_quat_w_positive(slerp_numpy(ik_target_R_init, target_world, alpha=1.0)).astype(np.float32)
    print(
        f"  [WARM-IC] IK target ori pre-aligned to GROOVE_TARGET_QUAT "
        f"(L Δ={math.degrees(_quat_distance(ik_target_L_init, q_L_warm)):.1f}° "
        f"R Δ={math.degrees(_quat_distance(ik_target_R_init, q_R_warm)):.1f}°)"
    )
    return q_L_warm, q_R_warm


def _query_ee_z_world0(env):
    """Query L/R EE (body6) Z position from env world-0 state via body_q.

    Uses public env state (no env API change). Mirrors the precondition check
    pattern at script :873 (env_flat_reset[bws + EE_BODY_OFFSET, 2]).

    Returns:
        (l_ee_z, r_ee_z) tuple of floats (achieved EE Z, not target).
    """
    wp.synchronize()
    bq = env._state_0.body_q.numpy().view(np.float32).reshape(-1, 7)
    bws0 = env._bws[0]
    l_ee_z = float(bq[bws0 + EE_BODY_OFFSET, 2])
    r_ee_z = float(bq[bws0 + FRANKA_NUM_JOINTS + EE_BODY_OFFSET, 2])
    return l_ee_z, r_ee_z


def _warm_start_position_ic(env, target_l_ee_z, target_r_ee_z, mode="approach"):
    """Pre-MPPI position warm-start: descend L+R EE to target Z via controlled env.step.

    F1 P1 implementation per project_ic_z_plateau_analysis_2026-04-26.md.
    Bypasses initial 91mm Z gap to give MPPI a near-target starting state.

    Action layout is env-native R-first 12D (per env :1427-1434):
      action[0, 0:3] = R_pos (XYZ deltas)
      action[0, 3:6] = R_ori
      action[0, 6:9] = L_pos (XYZ deltas, env applies LEFT_ACTION_DAMPING=0.3)
      action[0, 9:12] = L_ori
    Only Z components of pos are non-zero; XY/ORI deltas are zero (env tracks
    targets internally).

    Termination conditions:
      - Both L and R EE Z within WARM_START_TOLERANCE_M of their targets, OR
      - WARM_START_MAX_STEPS reached, OR
      - env reports done (cable drop / explosion / sanitise failure).

    Args:
        env: NewtonInsertClipEnv instance (single-world).
        target_l_ee_z: Target L EE Z position (e.g., GROOVE_CENTER_Z + EE_TO_FINGERTIP +
            WARM_START_HEIGHT_ABOVE_GROOVE = 1.040m).
        target_r_ee_z: Target R EE Z position (same as L for symmetric warm-start).
        mode: "approach" or "insert" (informational, unused for action computation).

    Returns:
        success: True if both L and R EE within tolerance of target Z.
        steps_taken: Number of env.step iterations performed.
        final_l_ee_z: Final L EE Z achieved (world 0).
        final_r_ee_z: Final R EE Z achieved (world 0).
    """
    # 12D action tensor: env-native R-first layout.
    action = torch.zeros(1, 12, dtype=torch.float32, device=env.device)

    final_l_z, final_r_z = _query_ee_z_world0(env)

    for step in range(WARM_START_MAX_STEPS):
        l_ee_z_now, r_ee_z_now = _query_ee_z_world0(env)
        final_l_z, final_r_z = l_ee_z_now, r_ee_z_now

        l_gap = l_ee_z_now - target_l_ee_z
        r_gap = r_ee_z_now - target_r_ee_z

        # Termination check: both arms within tolerance.
        if abs(l_gap) < WARM_START_TOLERANCE_M and abs(r_gap) < WARM_START_TOLERANCE_M:
            return True, step, final_l_z, final_r_z

        # Direction: descend if above target, ascend if below.
        l_dir = -1.0 if l_gap > WARM_START_TOLERANCE_M else (1.0 if l_gap < -WARM_START_TOLERANCE_M else 0.0)
        r_dir = -1.0 if r_gap > WARM_START_TOLERANCE_M else (1.0 if r_gap < -WARM_START_TOLERANCE_M else 0.0)

        # Env-native R-first: action[0, 2] = R_pos_z, action[0, 8] = L_pos_z.
        action.zero_()
        action[0, 2] = WARM_START_ACTION_Z_MAGNITUDE * r_dir
        action[0, 8] = WARM_START_ACTION_Z_MAGNITUDE * l_dir

        _obs, _reward, done, _extras = env.step(action)
        if bool(done[0].item()):
            # Unexpected episode termination (cable drop / explosion / sanitise).
            final_l_z, final_r_z = _query_ee_z_world0(env)
            return False, step + 1, final_l_z, final_r_z

    # Max steps reached without convergence; query final state.
    final_l_z, final_r_z = _query_ee_z_world0(env)
    converged = (
        abs(final_l_z - target_l_ee_z) < WARM_START_TOLERANCE_M
        and abs(final_r_z - target_r_ee_z) < WARM_START_TOLERANCE_M
    )
    return converged, WARM_START_MAX_STEPS, final_l_z, final_r_z


# =========================================================================
# Main demo generation: env.step execute + mppi_plan rollout.
# =========================================================================


def mppi_generate_demos_ic(
    cfg, device, max_steps, n_demos=5, seed=42, mode="approach",
    diag_csv_path="/tmp/mppi_ic_metrics.csv",
):  # fmt: skip
    """Generate IC demos via env.step hybrid (Option III).

    env (K_EXEC=1, mode=mode) for episode execution + mppi_scene (K_MPPI=cfg.K).

    Returns:
        demos: list of per-episode dicts (see schema in Phase E).
        drifts_per_plan_LR: list[(L, R)] per-plan tangent drift across all episodes.
        drifts_per_episode_max: list[float] max(L, R) per episode.
        cable_endpoints_L, cable_endpoints_R: per-episode cable seg 0 / last position.
    """
    K = cfg.K
    H = cfg.H
    replan_interval = cfg.replan_interval

    print(f"\n[MPPI-IC] {IC_VERSION} Option III: env.step hybrid  mode={mode}")
    print(f"  K_EXEC=1 (env), K_MPPI={K}, H={H}, replan={replan_interval}")
    print(
        f"  pos_scale={cfg.pos_action_scale}  rot_scale={cfg.rot_action_scale}  "
        f"m3_cost_scale={cfg.m3_cost_scale:.4f}  cable_seg_cost_scale={cfg.cable_seg_cost_scale:.4f}"
    )
    print(f"  l/r_ori_ik_weight={cfg.l_ori_ik_weight}  warm_start_offset_m={cfg.warm_start_offset_m}")

    # =====================================================================
    # Phase A: env construction + monkey-patches
    # =====================================================================
    print("[MPPI-IC] Phase A: env construction...")
    env = NewtonInsertClipEnv(world_count=1, device=device, mode=mode)

    # Monkey-patches (instance attribute shadowing, reversible)
    env.POS_ACTION_SCALE = cfg.pos_action_scale
    env.ROT_ACTION_SCALE = cfg.rot_action_scale
    env.ADAPTIVE_POS_SCALE = False  # CRITICAL: disable env's adaptive shrinking
    # CC2 ITEM #9 / CC6-C5 invariant check: confirm monkey-patch applied.
    assert env.ADAPTIVE_POS_SCALE is False, "IC monkey-patch failed: ADAPTIVE_POS_SCALE must be False"
    env.max_episode_length = 100_000
    _env_reset_original = env._reset_worlds
    env._reset_worlds = lambda env_ids: None  # no-op intra-episode

    def env_reset_manual():
        """Invoke original _reset_worlds for inter-episode reset."""
        _env_reset_original(list(range(env._world_count)))

    # Mode-specific drop threshold for MPPI rollout.
    drop_z_thr = CABLE_DROP_Z_THR_APPROACH if mode == "approach" else CABLE_DROP_Z_THR_INSERT

    # =====================================================================
    # Phase B: mppi_scene build + IK solver
    # =====================================================================
    print(f"[MPPI-IC] Phase B: mppi_scene (K={K})...")
    fk_model_mppi = env._fk_model
    fk_state_mppi = env._fk_state
    # IC env uses add_support_clips=False, add_target_clip=True (env :411+ inline add
    # matches build_multiworld_scene add_target_clip=True flag path).
    cable_y_start = CLIP1_Y - (CABLE_SEGMENTS * CABLE_SEG_LEN / 2)
    mppi_scene = build_multiworld_scene(
        fk_model_mppi,
        fk_state_mppi,
        K,
        device,
        cable_start_pos=(GRASP_X, cable_y_start, TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS),
        add_support_clips=False,  # IC env does NOT have support clips
        add_target_clip=True,  # IC env has target clip at C1 (env :464-491 inline)
    )
    mppi_info = base_scene_to_m2_info(mppi_scene)
    if mppi_info["bodies_per_world"] != env._bodies_per_world:
        raise RuntimeError(
            f"[MPPI-IC] bodies_per_world mismatch: env={env._bodies_per_world}, "
            f"mppi_scene={mppi_info['bodies_per_world']}. "
            f"Check add_support_clips/add_target_clip flags."
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
    # Phase C: episode loop + diag CSV
    # =====================================================================
    demos = []
    drifts_per_plan_LR = []
    drifts_per_episode_max = []
    cable_endpoints_L = []
    cable_endpoints_R = []

    # Diag CSV (IC-HIGH-4: adds max_pos_L/R, max_seg_dist_groove, max_m3_ori_L/R cols).
    diag_file = open(diag_csv_path, "w", newline="")  # noqa: SIM115
    diag_csv = csv.writer(diag_file)
    diag_csv.writerow([
        "episode", "step", "n_nan", "k_eff",
        "weight_entropy", "weight_mass_valid", "top1_weight", "best_action_nan",
        "plan_time_s", "cost_min", "cost_max", "cost_range", "cost_std",
        "ee_spread_max_mm", "drift_L_rad", "drift_R_rad", "drop_count", "sustain_count",
        "dist_pos_L", "dist_pos_R", "dist_ori_L", "dist_ori_R",
        "seg_dist_groove", "groove_bodies", "pos_action_scale", "mode",
        # IC-HIGH-4 dominance columns + B+ max_seg_ori
        "max_pos_L", "max_pos_R", "max_seg_dist_groove", "max_m3_ori_L", "max_m3_ori_R",
        "max_seg_ori_groove",
        # E1 H1 diag (revertable, 2026-05-12): per-step ik_tgt vs cable seg tangent angle
        "angle_ik_vs_tan_L_rad", "angle_ik_vs_tan_R_rad",
    ])  # fmt: skip

    for ep in range(n_demos):
        print(f"\n[MPPI-IC] Episode {ep + 1}/{n_demos}")

        # Reset env (original _reset_worlds, cached precondition restore).
        env_reset_manual()

        # IC-HIGH-6: precondition integrity assertion (EE Z + cable_z_min).
        wp.synchronize()
        env_bq_reset = env._state_0.body_q.numpy()
        env_flat_reset = env_bq_reset.view(np.float32).reshape(-1, 7)
        env_bws0 = env._bws[0]
        ee_L_z = float(env_flat_reset[env_bws0 + EE_BODY_OFFSET, 2])
        ee_R_z = float(env_flat_reset[env_bws0 + FRANKA_NUM_JOINTS + EE_BODY_OFFSET, 2])
        env_cable_off = env._cable_body_offset
        env_cable_per = env._cable_bodies_per_world
        cable_z_min = float(
            env_flat_reset[
                env_bws0 + env_cable_off : env_bws0 + env_cable_off + env_cable_per,
                2,
            ].min()
        )
        expected_ee_z = env.INSERT_START_EE_Z if mode == "insert" else env.APPROACH_EE_Z
        if abs(ee_L_z - expected_ee_z) > 0.010 or abs(ee_R_z - expected_ee_z) > 0.010:
            raise RuntimeError(
                f"[PRECONDITION CORRUPT] EE_L_z={ee_L_z:.4f}, EE_R_z={ee_R_z:.4f}, "
                f"expected {expected_ee_z:.4f} ± 10mm. Check rl_insert_cache/."
            )
        if cable_z_min < (GROOVE_CENTER_Z - 0.005):
            raise RuntimeError(f"[PRECONDITION CORRUPT] cable sagged below groove, z_min={cable_z_min:.4f}")
        print(f"  [PRECONDITION OK] EE_L_z={ee_L_z:.4f}, EE_R_z={ee_R_z:.4f}, cable_z_min={cable_z_min:.4f}")

        obs, _ = env.get_observations()

        # Capture cable endpoints at reset (world 0).
        cable_flat = env_bq_reset.view(np.float32).reshape(-1, 7)
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
        traj_dist_pos_L = []
        traj_dist_pos_R = []
        traj_dist_ori_L = []
        traj_dist_ori_R = []
        traj_seg_dist_groove = []
        traj_groove_bodies = []
        traj_cable_pos = []
        drifts_L_ep = []
        drifts_R_ep = []

        step = 0
        sustain_count = 0
        success = False
        success_step = -1

        # F1 P1 2026-04-26: pre-MPPI position warm-start (approach mode only).
        # Closes the ~91mm initial Z gap (LIFT_Z=1.120 → target ~1.040m) BEFORE the
        # MPPI plan loop starts, so MPPI's weak action signal (mean -0.04, effective
        # 0.234 mm/step due to LEFT_ACTION_DAMPING=0.3) is sufficient within 200 steps.
        # Reference: project_ic_z_plateau_analysis_2026-04-26.md (action-velocity
        # Pearson 1.0000 confirms action-limited descent, not cable resistance).
        # cfg.warm_start_offset_m wired as descent intent from LIFT_Z; capped at
        # WARM_START_HEIGHT_ABOVE_GROOVE floor (1.040m) so default 0.20 doesn't
        # overshoot and small values (e.g., 0.04) yield tunable mid-descent (1.080m).
        if WARM_START_POSITION_ENABLE and mode == "approach" and cfg.warm_start_offset_m > 0.0:
            target_floor = float(GROOVE_CENTER_Z + EE_TO_FINGERTIP + WARM_START_HEIGHT_ABOVE_GROOVE)  # 1.040m
            target_intent = float(LIFT_Z - cfg.warm_start_offset_m)
            target_l_ee_z = max(target_intent, target_floor)
            target_r_ee_z = max(target_intent, target_floor)
            ws_success, ws_steps, ws_l_z, ws_r_z = _warm_start_position_ic(env, target_l_ee_z, target_r_ee_z, mode)
            print(
                f"  [WARM-POS] success={ws_success} steps={ws_steps}/{WARM_START_MAX_STEPS} "
                f"L_z={ws_l_z:.4f} R_z={ws_r_z:.4f} (target {target_l_ee_z:.4f}, "
                f"cfg.offset={cfg.warm_start_offset_m:.3f})"
            )

        # Initial IK target = current env EE quat (world 0).
        # NOTE: captured AFTER warm-start so MPPI starts from post-warm achieved quat.
        env_flat = env._state_0.body_q.numpy().view(np.float32).reshape(-1, 7)
        left_quat0 = _normalize_quat_w_positive(env_flat[env_bws0 + EE_BODY_OFFSET, 3:7]).astype(np.float32)
        right_quat0 = _normalize_quat_w_positive(env_flat[env_bws0 + FRANKA_NUM_JOINTS + EE_BODY_OFFSET, 3:7]).astype(
            np.float32
        )
        ik_target_L = left_quat0.copy()
        ik_target_R = right_quat0.copy()

        # Warm-start SLERP (approach mode only) — simplified MVP per CC6-C2.
        if mode == "approach" and cfg.warm_start_offset_m > 0.0:
            ik_target_L, ik_target_R = _warm_start_slerp_ic(cfg, ik_target_L, ik_target_R)

        best_action_ee = None  # (H, 12) refreshed every replan_interval
        diag = {}
        plan_idx = 0

        while step < max_steps:
            # MPPI plan (every replan_interval steps, or at step=0)
            if step % replan_interval == 0:
                t0_plan = time.perf_counter()
                per_world_jq_env_w0 = env._per_world_fk_jq[0].copy()
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
                    drop_z_thr,
                )
                t_plan = time.perf_counter() - t0_plan
                drifts_L_ep.append(diag["drift_L_rad"])
                drifts_R_ep.append(diag["drift_R_rad"])

                if plan_idx == 0 or plan_idx % 5 == 0:
                    print(
                        f"  [PLAN {plan_idx}] step={step} plan_t={t_plan:.2f}s "
                        f"nan={diag['n_nan']}/{K} k_eff={diag['k_eff']} "
                        f"cost_range={diag['cost_range']:.4f} "
                        f"entropy={diag['weight_entropy']:.2f} "
                        f"drift L={math.degrees(diag['drift_L_rad']):.1f}° "
                        f"R={math.degrees(diag['drift_R_rad']):.1f}° "
                        f"drop={diag['drop_count']}"
                    )
                plan_idx += 1

            # Current step's executed action (L-first 12D from MPPI best)
            h_exec = step % replan_interval
            action_ee_12d = best_action_ee[h_exec]  # L-first internal

            # IK target accumulate (for next plan consistency)
            L_ori_delta_world = action_ee_12d[3:6] * cfg.rot_action_scale
            R_ori_delta_world = action_ee_12d[9:12] * cfg.rot_action_scale
            q_dL = _axis_angle_to_quat_xyzw(L_ori_delta_world)
            ik_target_L = _quat_multiply_xyzw(q_dL, ik_target_L)
            ik_target_L = ik_target_L / np.linalg.norm(ik_target_L)
            q_dR = _axis_angle_to_quat_xyzw(R_ori_delta_world)
            ik_target_R = _quat_multiply_xyzw(q_dR, ik_target_R)
            ik_target_R = ik_target_R / np.linalg.norm(ik_target_R)

            # -------------------------------------------------------
            # CRITICAL: L-first MPPI → R-first env conversion (IC 12D)
            # MPPI internal 12D L-first: [L_pos(3), L_ori(3), R_pos(3), R_ori(3)]
            # env native 12D R-first:    [R_pos(3), R_ori(3), L_pos(3), L_ori(3)]
            # Per env newton_insert_clip_env.py :1427-1434 (r_pos_delta from
            # actions[:, 0:3], l_pos_delta from actions[:, 6:9]).
            # -------------------------------------------------------
            action_12d_r_first = np.array(
                [
                    *action_ee_12d[6:9],  # R_pos  ← L-first[6:9]
                    *action_ee_12d[9:12],  # R_ori  ← L-first[9:12]
                    *action_ee_12d[0:3],  # L_pos  ← L-first[0:3]
                    *action_ee_12d[3:6],  # L_ori  ← L-first[3:6]
                ],
                dtype=np.float32,
            )
            assert action_12d_r_first.shape == (12,), f"action shape {action_12d_r_first.shape} != (12,)"

            action_tensor = torch.from_numpy(action_12d_r_first).unsqueeze(0).to(device)

            # Record pre-step EE state + cable
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
            cable_now = (
                env_flat[
                    env_bws0 + env._cable_body_offset : env_bws0 + env._cable_body_offset + env._cable_bodies_per_world,
                    :3,
                ]
                .astype(np.float32)
                .copy()
            )

            # E1 H1 diag (revertable, 2026-05-12): per-step ik_tgt vs cable seg tangent angle.
            # Same time snapshot pair: ik_target_L/R updated at lines 1097-1101 (pre-env-step,
            # reflecting THIS step's IK target) + cable_now captured at 1134-1141 (pre-env-step).
            # Used to validate H1 IK-cable frame mismatch hypothesis (state.md §24 E1_JUSTIFIED).
            try:
                _cable_seg0_tan = compute_cable_tangent(cable_now, 0)
                _cable_segN_tan = compute_cable_tangent(cable_now, cable_now.shape[0] - 1)
                if np.any(np.isnan(_cable_seg0_tan)) or np.any(np.isnan(_cable_segN_tan)):
                    angle_ik_vs_tan_L_rad = float("nan")
                    angle_ik_vs_tan_R_rad = float("nan")
                else:
                    _tan_L_quat = _normalize_quat_w_positive(
                        np.asarray(compute_hand_quat_for_cable(_cable_seg0_tan), dtype=np.float32)
                    )
                    _tan_R_quat = _normalize_quat_w_positive(
                        np.asarray(compute_hand_quat_for_cable(_cable_segN_tan), dtype=np.float32)
                    )
                    angle_ik_vs_tan_L_rad = float(_quat_distance(ik_target_L, _tan_L_quat))
                    angle_ik_vs_tan_R_rad = float(_quat_distance(ik_target_R, _tan_R_quat))
            except Exception:
                angle_ik_vs_tan_L_rad = float("nan")
                angle_ik_vs_tan_R_rad = float("nan")
            # end E1 H1 diag

            # env.step (single entry for physics/spring/sanitise/swap/obs)
            obs, reward, done, extras = env.step(action_tensor)

            # Extract post-step distances from env obs (45D layout per env :10-20)
            #   [0:3]   R clamp pos - groove
            #   [7:10]  L clamp pos - groove
            #   [14:17] nearest cable seg pos - groove
            #   [17:20] cable-groove ori error (axis-angle)
            #   [20]    cable-groove distance (scalar)
            obs_np = obs[0].cpu().numpy()
            dist_pos_R = float(np.linalg.norm(obs_np[0:3]))  # R clamp → groove
            dist_pos_L = float(np.linalg.norm(obs_np[7:10]))  # L clamp → groove
            seg_dist_groove_step = float(obs_np[20])  # cable → groove scalar

            # EE quat → target quat distances (ours; env doesn't expose directly).
            dist_ori_L = float(_quat_distance(left_quat_now, GROOVE_TARGET_QUAT))
            dist_ori_R = float(_quat_distance(right_quat_now, GROOVE_TARGET_QUAT))

            # Groove_bodies: env logs per-world via extras["log_per_world"]["groove_bodies"][0].
            # D12 protection: dict-key fallback.
            groove_bodies_step = int(extras.get("log_per_world", {}).get("groove_bodies", [0])[0])

            # Record trajectory (HDF5 R-first 12D per env native).
            traj_actions.append(action_12d_r_first)
            traj_obs.append(obs_np.copy())
            traj_left_pos.append(left_pos_now)
            traj_left_quat.append(left_quat_now)
            traj_right_pos.append(right_pos_now)
            traj_right_quat.append(right_quat_now)
            traj_dist_pos_L.append(dist_pos_L)
            traj_dist_pos_R.append(dist_pos_R)
            traj_dist_ori_L.append(dist_ori_L)
            traj_dist_ori_R.append(dist_ori_R)
            traj_seg_dist_groove.append(seg_dist_groove_step)
            traj_groove_bodies.append(groove_bodies_step)
            traj_cable_pos.append(cable_now)

            # Success eval (mode-dependent).
            if mode == "approach":
                # approach: terminal-only (K=1 suffices).
                pos_ok = dist_pos_L < IC_T_DIST_APPROACH and dist_pos_R < IC_T_DIST_APPROACH
                seg_ok = seg_dist_groove_step < IC_T_DIST_APPROACH
                cos_L = abs(float(np.dot(left_quat_now, GROOVE_TARGET_QUAT)))
                cos_R = abs(float(np.dot(right_quat_now, GROOVE_TARGET_QUAT)))
                ori_ok = cos_L > IC_T_SEAT_COS and cos_R > IC_T_SEAT_COS
                seated = pos_ok and seg_ok and ori_ok
            else:
                # insert: tighter threshold + groove_bodies.
                pos_ok = dist_pos_L < IC_T_GROOVE and dist_pos_R < IC_T_GROOVE
                seg_ok = seg_dist_groove_step < IC_T_GROOVE
                cos_L = abs(float(np.dot(left_quat_now, GROOVE_TARGET_QUAT)))
                cos_R = abs(float(np.dot(right_quat_now, GROOVE_TARGET_QUAT)))
                ori_ok = cos_L > IC_T_SEAT_COS and cos_R > IC_T_SEAT_COS
                seated = pos_ok and seg_ok and ori_ok and (groove_bodies_step >= GROOVE_BODIES_MIN)

            if seated:
                sustain_count += 1
                required = 1 if mode == "approach" else K_INSERT
                if sustain_count >= required and success_step < 0:
                    success = True
                    success_step = step
            else:
                sustain_count = 0

            # Diag CSV row (IC-HIGH-4 dominance cols appended).
            diag_csv.writerow([
                ep, step, diag.get("n_nan", 0), diag.get("k_eff", K),
                f"{diag.get('weight_entropy', 0.0):.4f}",
                f"{diag.get('weight_mass_valid', 0.0):.6f}",
                f"{diag.get('top1_weight', 0.0):.6f}",
                int(diag.get("best_action_nan", False)),
                f"{diag.get('t_ik_total_s', 0.0) + diag.get('t_physics_total_s', 0.0):.3f}",
                f"{diag.get('cost_min', 0.0):.4f}", f"{diag.get('cost_max', 0.0):.4f}",
                f"{diag.get('cost_range', 0.0):.4f}", f"{diag.get('cost_std', 0.0):.4f}",
                f"{diag.get('ee_spread_max_mm', 0.0):.2f}",
                f"{diag.get('drift_L_rad', 0.0):.4f}", f"{diag.get('drift_R_rad', 0.0):.4f}",
                diag.get("drop_count", 0), sustain_count,
                f"{dist_pos_L:.5f}", f"{dist_pos_R:.5f}",
                f"{dist_ori_L:.5f}", f"{dist_ori_R:.5f}",
                f"{seg_dist_groove_step:.5f}", groove_bodies_step,
                f"{cfg.pos_action_scale:.4f}", mode,
                # IC-HIGH-4 dominance + B+ seg_ori
                f"{diag.get('max_pos_L', 0.0):.5f}", f"{diag.get('max_pos_R', 0.0):.5f}",
                f"{diag.get('max_seg_dist_groove', 0.0):.5f}",
                f"{diag.get('max_m3_ori_L', 0.0):.5f}", f"{diag.get('max_m3_ori_R', 0.0):.5f}",
                f"{diag.get('max_seg_ori_groove', 0.0):.5f}",
                # E1 H1 diag (revertable, 2026-05-12)
                f"{angle_ik_vs_tan_L_rad:.5f}", f"{angle_ik_vs_tan_R_rad:.5f}",
            ])  # fmt: skip

            step += 1

            # Env-detected terminal (explosion/drop/timeout) — break if not already success.
            if done[0].item() and not success:
                print(f"  [TERMINAL] step={step} env-reported done (explosion/drop?)")
                break

        # End of episode
        if success:
            print(
                f"  SUCCESS at step {success_step}, final "
                f"pos L={traj_dist_pos_L[-1]:.4f}m R={traj_dist_pos_R[-1]:.4f}m "
                f"ori L={math.degrees(traj_dist_ori_L[-1]):.1f}° "
                f"R={math.degrees(traj_dist_ori_R[-1]):.1f}° "
                f"seg={traj_seg_dist_groove[-1] * 1000:.1f}mm "
                f"groove_bodies={traj_groove_bodies[-1]}"
            )
        else:
            print(
                f"  FAILED at step {step}, final "
                f"pos L={traj_dist_pos_L[-1]:.4f}m R={traj_dist_pos_R[-1]:.4f}m "
                f"ori L={math.degrees(traj_dist_ori_L[-1]):.1f}° "
                f"R={math.degrees(traj_dist_ori_R[-1]):.1f}° "
                f"seg={traj_seg_dist_groove[-1] * 1000:.1f}mm "
                f"groove_bodies={traj_groove_bodies[-1]}"
            )

        demo = {
            "action_delta": np.array(traj_actions, dtype=np.float32).reshape(-1, IC_HDF5_ACTION_DIM),
            "obs": np.array(traj_obs, dtype=np.float32).reshape(-1, 45),
            "left_ee_pos": np.array(traj_left_pos, dtype=np.float32),
            "right_ee_pos": np.array(traj_right_pos, dtype=np.float32),
            "left_ee_quat": np.array(traj_left_quat, dtype=np.float32),
            "right_ee_quat": np.array(traj_right_quat, dtype=np.float32),
            "dist_pos_left": np.array(traj_dist_pos_L, dtype=np.float32),
            "dist_pos_right": np.array(traj_dist_pos_R, dtype=np.float32),
            "dist_ori_left": np.array(traj_dist_ori_L, dtype=np.float32),
            "dist_ori_right": np.array(traj_dist_ori_R, dtype=np.float32),
            "seg_dist_groove": np.array(traj_seg_dist_groove, dtype=np.float32),
            "groove_bodies": np.array(traj_groove_bodies, dtype=np.int32),
            "cable_pos_seq": (
                np.array(traj_cable_pos, dtype=np.float32) if traj_cable_pos else np.zeros((0, 0, 3), dtype=np.float32)
            ),
            "success": bool(success),
            "success_step": int(success_step),
            "sustain_count_final": int(sustain_count),
            "steps": int(step),
            "mode": mode,
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


def compute_ic_success_rates(demos, mode):
    """Compute S1 (pos), S2 (ori), S3 (combined terminal) rates.

    S1: terminal pos_dist_L AND pos_dist_R AND seg_dist_groove < threshold
    S2: terminal |cos(EE_L, groove)| > T_SEAT AND |cos(EE_R, groove)| > T_SEAT
    S3: S1 AND S2 (approach)
        S1 AND S2 AND groove_bodies >= GROOVE_BODIES_MIN (insert)

    Mode-dependent threshold: approach=T_DIST_APPROACH (12mm), insert=T_GROOVE (3mm).
    """
    if not demos:
        return {"s1": 0.0, "s2": 0.0, "s3": 0.0}

    thr_pos = IC_T_DIST_APPROACH if mode == "approach" else IC_T_GROOVE

    n1 = n2 = n3 = 0
    for d in demos:
        if len(d["dist_pos_left"]) == 0:
            continue
        dpL = d["dist_pos_left"][-1]
        dpR = d["dist_pos_right"][-1]
        seg_d = d["seg_dist_groove"][-1]
        pos_ok = dpL < thr_pos and dpR < thr_pos and seg_d < thr_pos
        cos_L = abs(float(np.dot(d["left_ee_quat"][-1], GROOVE_TARGET_QUAT)))
        cos_R = abs(float(np.dot(d["right_ee_quat"][-1], GROOVE_TARGET_QUAT)))
        ori_ok = cos_L > IC_T_SEAT_COS and cos_R > IC_T_SEAT_COS
        if pos_ok:
            n1 += 1
        if ori_ok:
            n2 += 1
        if mode == "approach":
            if pos_ok and ori_ok:
                n3 += 1
        else:  # insert
            gb = int(d["groove_bodies"][-1])
            if pos_ok and ori_ok and gb >= GROOVE_BODIES_MIN:
                n3 += 1

    n = len(demos)
    return {"s1": n1 / n, "s2": n2 / n, "s3": n3 / n}


def save_demos_hdf5_ic(
    demos,
    cfg,
    output_path,
    mppi_mode,
    mode,
    cable_L_endpoint_mean=None,
    cable_R_endpoint_mean=None,
):
    """Save IC demos to HDF5.

    Schema: mppi_action_dim (12 L-first internal) + hdf5_action_dim (12 R-first
    env-native) are identical value (both 12) but layouts differ; action_layout
    attr records the on-disk ordering.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    n_success = sum(1 for d in demos if d["success"])

    with h5py.File(output_path, "w") as f:
        meta = f.create_group("metadata")
        meta.attrs["generator"] = f"mppi_ic_v1_envstep_{mode}"
        meta.attrs["ic_version"] = IC_VERSION
        meta.attrs["architecture"] = IC_ARCHITECTURE
        meta.attrs["mode"] = mode
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
        meta.attrs["cable_seg_cost_scale"] = cfg.cable_seg_cost_scale
        meta.attrs["seg_ori_scale"] = cfg.seg_ori_scale  # B+ 2026-04-25
        meta.attrs["cost_method"] = IC_COST_METHOD
        meta.attrs["p_cable_drop"] = P_CABLE_DROP
        meta.attrs["left_action_damping"] = LEFT_ACTION_DAMPING
        meta.attrs["mppi_l_ori_ik_weight"] = cfg.l_ori_ik_weight
        meta.attrs["mppi_r_ori_ik_weight"] = cfg.r_ori_ik_weight
        meta.attrs["warm_start_offset_m"] = cfg.warm_start_offset_m
        meta.attrs["mppi_action_dim"] = IC_MPPI_ACTION_DIM
        meta.attrs["hdf5_action_dim"] = IC_HDF5_ACTION_DIM
        meta.attrs["action_dim"] = IC_HDF5_ACTION_DIM
        meta.attrs["action_layout"] = IC_ACTION_LAYOUT
        meta.attrs["quat_convention"] = M3_QUAT_CONVENTION
        meta.attrs["quat_frame"] = M3_QUAT_FRAME
        meta.attrs["quat_semantic"] = M3_QUAT_SEMANTIC
        meta.attrs["mppi_mode"] = mppi_mode
        meta.attrs["success_threshold_m"] = IC_T_DIST_APPROACH if mode == "approach" else IC_T_GROOVE
        meta.attrs["success_threshold_cos"] = IC_T_SEAT_COS
        meta.attrs["success_threshold_rad"] = IC_T_SEAT_RAD
        meta.attrs["groove_bodies_min"] = GROOVE_BODIES_MIN if mode == "insert" else 0
        meta.attrs["k_sustain"] = 1 if mode == "approach" else K_INSERT
        meta.attrs["terminal_steps"] = INSERT_TERMINAL_STEPS if mode == "approach" else INSERT_TERMINAL_STEPS_INSERT
        meta.attrs["success_eval"] = "approach_terminal" if mode == "approach" else "insert_sustained_K10"
        meta.attrs["groove_center_pos"] = GROOVE_CENTER_POS
        meta.attrs["groove_target_quat"] = GROOVE_TARGET_QUAT
        meta.attrs["source"] = f"m3_ic_{mode}_v1"
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
            g.create_dataset("dist_pos_left", data=demo["dist_pos_left"])
            g.create_dataset("dist_pos_right", data=demo["dist_pos_right"])
            g.create_dataset("dist_ori_left", data=demo["dist_ori_left"])
            g.create_dataset("dist_ori_right", data=demo["dist_ori_right"])
            g.create_dataset("seg_dist_groove", data=demo["seg_dist_groove"])
            g.create_dataset("groove_bodies", data=demo["groove_bodies"])
            if demo["cable_pos_seq"].size > 0:
                g.create_dataset("cable_pos_seq", data=demo["cable_pos_seq"], compression="gzip")
            g.attrs["success"] = demo["success"]
            g.attrs["success_step"] = demo["success_step"]
            g.attrs["sustain_count_final"] = demo["sustain_count_final"]
            g.attrs["steps"] = demo["steps"]
            g.attrs["mode"] = demo["mode"]

    print(f"[HDF5] Saved {len(demos)} demos ({n_success} success, mode={mode}) → {output_path}")


def save_run_metrics_ic(
    demos,
    drifts_per_plan_LR,
    drifts_per_episode_max,
    wall_clock_s,
    cfg,
    output_dir,
    mode,
):
    """Write per-lambda RUN_METRICS.json."""
    rates = compute_ic_success_rates(demos, mode)

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
        m2 = {
            "threshold_rad": DRIFT_THRESHOLD_RAD,
            "violation_count": 0,
            "total_episodes": 0,
            "violation_rate": 0.0,
        }
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
        "ic_version": IC_VERSION,
        "architecture": IC_ARCHITECTURE,
        "mode": mode,
        "lambda": float(cfg.temperature_lambda),
        "n_demos": len(demos),
        "wall_clock_s": float(wall_clock_s),
        "S1_pos_success_rate": rates["s1"],
        "S2_ori_success_rate": rates["s2"],
        "S3_combined_rate": rates["s3"],
        "tangent_drift": m1,
        "drift_violation": m2,
        "cost_threshold_m": IC_T_DIST_APPROACH if mode == "approach" else IC_T_GROOVE,
        "cost_threshold_cos": IC_T_SEAT_COS,
        "cost_threshold_rad": IC_T_SEAT_RAD,
        "cost_method": IC_COST_METHOD,
        "m3_cost_scale": cfg.m3_cost_scale,
        "cable_seg_cost_scale": cfg.cable_seg_cost_scale,
        "seg_ori_scale": cfg.seg_ori_scale,  # B+ 2026-04-25
        "left_action_damping": LEFT_ACTION_DAMPING,
        "p_cable_drop": P_CABLE_DROP,
        "cfg_snapshot": {
            "K": cfg.K,
            "H": cfg.H,
            "replan_interval": cfg.replan_interval,
            "pos_action_scale": cfg.pos_action_scale,
            "rot_action_scale": cfg.rot_action_scale,
            "warm_start_offset_m": cfg.warm_start_offset_m,
            "l_ori_ik_weight": cfg.l_ori_ik_weight,
            "r_ori_ik_weight": cfg.r_ori_ik_weight,
            "noise_sigma": cfg.noise_sigma,
            "noise_correlation": cfg.noise_correlation,
        },
    }

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"run_metrics_{mode}_lam{cfg.temperature_lambda}.json")
    with open(out_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[RUN_METRICS] {out_path}")
    return metrics


# =========================================================================
# CLI / main.
# =========================================================================


def main():
    parser = argparse.ArgumentParser(
        description=f"MPPI IC (InsertIntoClip) demo generator ({IC_VERSION}, Option III env.step)"
    )
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--mode", choices=["approach", "insert"], default="approach",
                        help="IC mode (approach-first; insert deferred G10+).")  # fmt: skip
    # IC-HIGH-5: default 128 (Grip G6a-128 stable optimum precedent per m3_grip_design.md:123).
    parser.add_argument("--world-count", type=int, default=128, help="K_MPPI (K_EXEC fixed=1)")
    parser.add_argument("--n-demos", type=int, default=5)
    parser.add_argument("--max-steps", type=int, default=None, help="Override max episode steps")
    parser.add_argument("--single-lambda", type=float, default=None, help="Conflicts with --lambdas/--sweep")
    parser.add_argument("--lambdas", type=str, default=None, help="Comma list (e.g. 0.3,0.5,1.0)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=str, default="data/mppi_demos_m3_ic")
    parser.add_argument("--diag-csv", type=str, default=None, help="Diag CSV path")
    parser.add_argument("--no-mppi", action="store_true", help="Skip MPPI (no-op baseline)")

    # Mutex sweep axes (Grip γ-3c precedent)
    sweep_group = parser.add_mutually_exclusive_group()
    sweep_group.add_argument("--sweep", action="store_true", help="Lambda sweep [0.3, 0.5, 1.0]")
    sweep_group.add_argument("--sweep-pos", action="store_true", help="pos_action_scale sweep")

    parser.add_argument("--pos-scale", type=float, default=None, help="Override cfg.pos_action_scale")
    parser.add_argument("--m3-cost-scale", type=float, default=None, help="Override cfg.m3_cost_scale")
    parser.add_argument("--cable-seg-cost-scale", type=float, default=None, help="Override cfg.cable_seg_cost_scale")
    parser.add_argument("--seg-ori-scale", type=float, default=None, help="Override cfg.seg_ori_scale (B+ 2026-04-25)")
    parser.add_argument(
        "--warm-start-offset", type=float, default=None, help="Override cfg.warm_start_offset_m (B+ 2026-04-25)"
    )
    parser.add_argument(
        "--left-action-damping", type=float, default=None, help="Override LEFT_ACTION_DAMPING (B+ 2026-04-25)"
    )

    args = parser.parse_args()

    # ---- mode dispatch (G10+ defer per design spec §3.2) ----
    if args.mode == "insert":
        raise NotImplementedError(
            "insert mode deferred to G10+ per m3_ic_design.md §3.2. "
            "Use --mode approach for Phase 0 — approach-first pipeline PASS first."
        )

    # ---- argparse validation (Grip γ-3c parity) ----
    if args.pos_scale is not None and args.sweep_pos:
        parser.error("--pos-scale conflicts with --sweep-pos")
    if args.pos_scale is not None:
        lo, hi = (0.005, 0.050) if args.mode == "approach" else (0.001, 0.010)
        if args.pos_scale <= 0 or not (lo <= args.pos_scale <= hi):
            parser.error(f"--pos-scale must be in [{lo}, {hi}] for mode={args.mode} (got {args.pos_scale})")
    if args.single_lambda is not None and args.lambdas is not None:
        parser.error("--single-lambda and --lambdas are mutually exclusive")
    if args.sweep and (args.single_lambda is not None or args.lambdas is not None):
        parser.error("--sweep conflicts with --single-lambda/--lambdas")

    wp.init()
    wp.set_device(args.device)

    # Resolve lambda list
    if args.sweep:
        lambdas = [0.3, 0.5, 1.0]
    elif args.lambdas is not None:
        lambdas = [float(x) for x in args.lambdas.split(",")]
    else:
        lambdas = [args.single_lambda if args.single_lambda is not None else 0.3]

    # Resolve pos_scale list
    if args.sweep_pos:
        pos_scales = [0.015, 0.020, 0.025] if args.mode == "approach" else [0.003, 0.005, 0.008]
    else:
        pos_scales = [args.pos_scale]

    # Resolve max_steps
    max_steps_default = INSERT_TERMINAL_STEPS if args.mode == "approach" else INSERT_TERMINAL_STEPS_INSERT
    max_steps = args.max_steps if args.max_steps is not None else max_steps_default

    mppi_mode = "off" if args.no_mppi else "on"
    sweep_label = "POS-SWEEP" if args.sweep_pos else ("SWEEP" if args.sweep else "SINGLE")

    sweep_results = []

    for lam in lambdas:
        for pos_scale in pos_scales:
            print(f"\n{'=' * 60}")
            pos_label = f"pos={pos_scale}" if pos_scale is not None else "pos=<cfg default>"
            print(f"  {sweep_label} mode={args.mode} lambda={lam} {pos_label}  mppi={mppi_mode}")
            print(f"{'=' * 60}")

            # Config factory per mode.
            cfg = get_default_mppi_ic_config() if args.mode == "approach" else get_insert_mppi_ic_config()
            cfg.temperature_lambda = lam
            cfg.K = args.world_count
            cfg.device = args.device

            # IC-CRIT-1: override pos_action_scale 0.015 → 0.020 for approach when
            # user did NOT pass --pos-scale (preserves config immutability; AC T9_F
            # precedent — 128-step PASS faster convergence).
            if args.pos_scale is None and args.mode == "approach" and not args.sweep_pos:
                cfg.pos_action_scale = 0.020
                print("[FIX IC-CRIT-1] pos_action_scale 0.015→0.020 per AC T9_F precedent")

            if pos_scale is not None:
                cfg.pos_action_scale = pos_scale
            if args.m3_cost_scale is not None:
                cfg.m3_cost_scale = args.m3_cost_scale
            if args.cable_seg_cost_scale is not None:
                cfg.cable_seg_cost_scale = args.cable_seg_cost_scale
            if args.seg_ori_scale is not None:  # B+ 2026-04-25
                cfg.seg_ori_scale = args.seg_ori_scale
            if args.warm_start_offset is not None:  # B+ 2026-04-25
                cfg.warm_start_offset_m = args.warm_start_offset
            if args.left_action_damping is not None:  # B+ 2026-04-25
                global LEFT_ACTION_DAMPING
                LEFT_ACTION_DAMPING = args.left_action_damping

            # Log applied fixes (proof-of-application markers per impl spec).
            print("[FIX IC-HIGH-1] cost uses compute_clamp_pos (fingertip) vs raw EE")
            print(f"[FIX IC-HIGH-2] rollout applies LEFT_ACTION_DAMPING={LEFT_ACTION_DAMPING} to L arm")
            print(f"[FIX IC-HIGH-3] rollout clips EE Z to [{PUSH_Z_CLIP_MIN:.4f}, {PUSH_Z_CLIP_MAX:.4f}]")
            print("[FIX IC-HIGH-4] diag CSV adds max_pos_L/R, max_seg_dist_groove, max_m3_ori_L/R")
            print(f"[FIX IC-HIGH-5] --world-count default=128 (was 256); current K={cfg.K}")
            print("[FIX IC-HIGH-6] precondition integrity assertion armed (EE Z + cable_z_min)")
            print(
                f"[FIX IC-HIGH-7] 6-term max cost: seg_dist_scale={cfg.cable_seg_cost_scale}, "
                f"seg_ori_scale={cfg.seg_ori_scale} (B+ 2026-04-25)"
            )
            print("[FIX IC-HIGH-8] G5 converter must default --all until Phase 0 S3 >= 20% (design note)")
            print("[FIX CC6-C5] env.ADAPTIVE_POS_SCALE=False + finger pin CLOSED invariants enforced")

            print(
                f"[CFG] mode={args.mode} K={cfg.K} H={cfg.H} replan={cfg.replan_interval} "
                f"pos={cfg.pos_action_scale} rot={cfg.rot_action_scale} "
                f"m3_cost={cfg.m3_cost_scale} seg_cost={cfg.cable_seg_cost_scale}"
            )

            # Diag CSV name
            if args.sweep_pos:
                diag_csv = f"/tmp/mppi_ic_{args.mode}_sweep_pos{int(round(cfg.pos_action_scale * 1000)):03d}.csv"
            elif args.sweep:
                diag_csv = f"/tmp/mppi_ic_{args.mode}_sweep_lam{lam}.csv"
            else:
                diag_csv = args.diag_csv or f"/tmp/mppi_ic_{args.mode}.csv"

            t0 = time.perf_counter()
            demos, drifts, drifts_per_ep_max, cable_L_list, cable_R_list = mppi_generate_demos_ic(
                cfg, args.device, max_steps=max_steps, n_demos=args.n_demos,
                seed=args.seed, mode=args.mode, diag_csv_path=diag_csv,
            )  # fmt: skip
            elapsed = time.perf_counter() - t0

            cable_L_mean = np.mean(cable_L_list, axis=0).astype(np.float32) if cable_L_list else None
            cable_R_mean = np.mean(cable_R_list, axis=0).astype(np.float32) if cable_R_list else None

            # HDF5 naming
            if args.sweep_pos:
                h5_name = f"demos_{args.mode}_pos{int(round(cfg.pos_action_scale * 1000)):03d}.hdf5"
            elif args.sweep:
                h5_name = f"demos_{args.mode}_l{lam}.hdf5"
            else:
                h5_name = f"demos_{args.mode}_default.hdf5"
            h5_path = os.path.join(args.output_dir, h5_name)
            save_demos_hdf5_ic(
                demos, cfg, h5_path, mppi_mode, args.mode,
                cable_L_endpoint_mean=cable_L_mean, cable_R_endpoint_mean=cable_R_mean,
            )  # fmt: skip
            metrics = save_run_metrics_ic(
                demos, drifts, drifts_per_ep_max, elapsed, cfg, args.output_dir, args.mode,
            )  # fmt: skip

            n_success = sum(1 for d in demos if d["success"])
            sweep_results.append({
                "mode": args.mode, "lambda": lam,
                "pos_action_scale": cfg.pos_action_scale,
                "n_demos": len(demos), "n_success": n_success,
                "S1_pos": metrics["S1_pos_success_rate"],
                "S2_ori": metrics["S2_ori_success_rate"],
                "S3": metrics["S3_combined_rate"],
                "drift_max_L": metrics["tangent_drift"]["left"].get("max", 0.0),
                "drift_max_R": metrics["tangent_drift"]["right"].get("max", 0.0),
                "drift_violation_rate": metrics["drift_violation"]["violation_rate"],
                "wall_clock_s": round(elapsed, 1),
            })  # fmt: skip

    # Sweep summary print + CSV
    if args.sweep or args.sweep_pos:
        print(f"\n{'=' * 78}")
        print(f"  IC {args.mode} {sweep_label} RESULTS")
        print(f"{'=' * 78}")
        for r in sweep_results:
            print(
                f"  lam={r['lambda']:>4.1f} pos={r['pos_action_scale']:>5.3f} "
                f"demos={r['n_demos']:>3d} succ={r['n_success']:>3d} "
                f"S1={r['S1_pos']:>6.1%} S2={r['S2_ori']:>6.1%} S3={r['S3']:>6.1%} "
                f"dL={math.degrees(r['drift_max_L']):>5.1f}° "
                f"dR={math.degrees(r['drift_max_R']):>5.1f}° "
                f"t={r['wall_clock_s']:>6.1f}s"
            )
        csv_path = f"/tmp/mppi_ic_{args.mode}_{'pos' if args.sweep_pos else 'lam'}_sweep.csv"
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(sweep_results[0].keys()))
            w.writeheader()
            w.writerows(sweep_results)
        print(f"  CSV: {csv_path}")

    # S3 gate (single-run only, MPPI ON; AC parity per rs 2026-04-24 OQ #4).
    if not args.sweep and not args.sweep_pos and not args.no_mppi and len(sweep_results) == 1:
        s3 = sweep_results[0]["S3"]
        drift_v = sweep_results[0]["drift_violation_rate"]
        s3_threshold = 0.50  # rs 2026-04-24: AC parity, 60%→50%
        s3_fail = s3 < s3_threshold
        drift_fail = drift_v >= DRIFT_VIOLATION_RATE_LIMIT
        if s3_fail or drift_fail:
            reasons = []
            if s3_fail:
                reasons.append(f"S3={s3:.1%} < {s3_threshold:.0%} (m3_ic_design §6-4 rs approved)")
            if drift_fail:
                reasons.append(f"drift_violation={drift_v:.1%} >= {DRIFT_VIOLATION_RATE_LIMIT:.0%}")
            print("\n[BLOCKED_FOR_USER] " + " AND ".join(reasons))
            sys.exit(2)
        print(f"\n[S3 GATE] S3={s3:.1%} >= {s3_threshold:.0%}  [DRIFT GATE] violation={drift_v:.1%} → PASS")


if __name__ == "__main__":
    main()
