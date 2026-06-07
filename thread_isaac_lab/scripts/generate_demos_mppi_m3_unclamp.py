#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MPPI demo trajectory generation for Unclamp skill (M3-Unclamp, G3).

§0 Downstream dependencies (G5 Converter Contract) — UNCLAMP-CRIT-2
-------------------------------------------------------------------
The HDF5 output of this G3 generator requires a G5 converter
(``convert_m3_to_unclamp_demos.py``, NOT YET IMPLEMENTED) to produce npz
consumable by ``train_unclamp.py --demos``.  Contract:

- Input HDF5 (this script, per episode group):
    * ``obs`` (T, 42) — env-native layout, see env docstring §obs.
    * ``action_delta`` (T, 4) — L-only [finger_delta, L_pos_x, L_pos_y, L_pos_z].
    * ``finger_opening_L`` / ``finger_opening_R`` (T,) — R is constant 0.080.
    * ``left_ee_pos`` / ``left_ee_quat`` / ``right_ee_pos`` / ``right_ee_quat``.
    * ``cable_pos_seq`` (T, cable_per_world, 3).
    * Per-episode attrs: ``success`` (bool), ``success_step`` (int), ``seated_terminal`` (bool),
      ``steps`` (int).
- Output npz keys expected (G5):
    * ``obs`` (total_T, 42) concatenated.
    * ``actions`` (total_T, 4).
    * ``episode_lengths`` (n_ep,), ``episode_success`` (n_ep,).
    * ``source="m3_unclamp_v1"``.
- Filter: success-only by default; ``--all`` flag for Phase 0 low-S3 coverage.
- Action normalization (UNCLAMP-HIGH-4 contract): MPPI samples stored action in
  unitless ±0.6 space (pre env POS_ACTION_SCALE). Policy (train_unclamp.py)
  outputs ±1.0 via tanh. G5 converter MUST normalize:
      bc_actions = mppi_actions / 0.6   (empirical sigma; also allowed:
                                        train side init_noise_std=0.6).
- Action layout check: meta.attrs["action_layout"] MUST be "L-only".
- obs[26:30] substitution (UNCLAMP-CRIT-3 / IC CRITICAL-1 pattern): env writes a
  STATIC identity clip quat at obs[26:30], giving zero ori learning signal. G5
  converter SHOULD replace with a scalar angular error to GROOVE_TARGET_QUAT
  (or drop the channel entirely, obs_bc dim 42→38). Substitution scope is G5,
  NOT this generator.

UNCLAMP-HIGH-5: Legacy ``grip_unclamp_demos_v1.npz`` (14D, Apr 5) is OBSOLETE
and MUST be renamed/deleted (e.g. ``grip_unclamp_demos_v1.OBSOLETE.npz``)
before G8 production to prevent schema collision with the new 4D L-only
format. Recommended preflight command:
``mv data/grip_unclamp_demos_v1.npz data/grip_unclamp_demos_v1.OBSOLETE.npz``.

Without this converter, DAPG training (``train_unclamp.py --demos``) is blocked.

Architecture (Option III env.step hybrid, adapted from Grip G3a, rs approved 2026-04-24):
  - env (NewtonUnclampEnv, K_EXEC=1): episode execution via env.step()
    Handles finger_delta clamping, IK solve, physics/spring/sanitise/state-swap.
  - mppi_scene (build_multiworld_scene, K_MPPI=cfg.K): parallel K-sample rollout for cost

env.step() handles physics/spring/sanitise/state-swap internally. Architecture-
by-construction auto-resolves NaN, cadence, state swap aliasing.

§1.1 IC P0 coupling note (CC6 C5)
---------------------------------
Unclamp precondition (L=HALF_OPEN, cable seated in groove, R=OPEN passive) is
CONSUMED FROM IC skill completion in full pipeline. This G3 generator uses
synthetic precondition via ``env._setup_unclamp_precondition`` (same cache dir
as Unclamp training). If IC precondition distribution evolves (e.g. shifted
seat pos), this generator's synthetic precondition must also be updated to
keep demos aligned with policy runtime.

Differences from Grip G3a:
  - Action: 4D left-only [finger_delta, L_pos_x, L_pos_y, L_pos_z] (vs Grip 14D bimanual)
  - Obs: 42D (same dim but different semantics at [23:30] — groove/clip channels)
  - R arm: passive throughout episode (kinematic soft-pin at initial R EE pose)
  - Finger direction: OPEN only (Δ≥0 clipped; vs Grip CLOSE direction)
  - Cost: additive (default; UNCLAMP-SYS-1) or multiplicative (ablation)
  - No warm-start (P0 proximal; cable already seated, L finger at HALF_OPEN)
  - Success: finger_fully_open ∧ seated ∧ sustained_K5 (vs Grip pos+ori+finger)
  - IK solver: L weight per cfg; R weight soft-pinned to 0.3 (UNCLAMP-HIGH-2)
    NOTE: cfg.r_ori_ik_weight semantic is "passive=0"; we override at the
    solver with 0.3 for rollout wrist stability, documented inline.

Monkey-patches on env (reversible, instance attribute shadowing):
  - env.POS_ACTION_SCALE = cfg.pos_action_scale  (default 0.010 vs env 0.015)
  - env.max_episode_length = large (generator manages max_steps)
  - env._reset_worlds = no-op intra-episode (manual inter-episode reset)
  (no ROT_ACTION_SCALE patch: Unclamp env 4D action has no rot component)

Usage:
    source ~/env_isaaclab6/bin/activate
    cd ~/IsaacLab
    PYTHONPATH=$PYTHONPATH:thread_isaac_lab/scripts:thread_isaac_lab/configs:thread_isaac_lab/envs \\
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/generate_demos_mppi_m3_unclamp.py \\
        --device cuda:0 --world-count 4 --n-demos 5 --single-lambda 0.5

References:
    Design spec: thread-vault/08-DA-MPPI/01-Dashboard/m3_unclamp_design.md
    G1 config:   configs/mpc_config_unclamp.py
    Precedent:   scripts/generate_demos_mppi_m3_grip.py (Option III 1322 LoC)
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

# Reuse M3 quaternion helpers + MppiIKSolverM3 (12D bimanual scene; we pass
# L-only actions but IK solver still expects dual-arm targets — R is soft-pin).
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
from mpc_config_unclamp import get_default_mppi_unclamp_config
from newton_skill_env_base import (
    EE_BODY_OFFSET,
    FRANKA_NUM_JOINTS,
    build_multiworld_scene,
    compute_clamp_pos,
    find_nearest_cable_point,
)
from newton_skill_env_base import (
    normalize_quat_w_positive as _normalize_quat_w_positive,
)
from newton_skill_env_base import (
    quat_distance as _quat_distance,
)
from newton_unclamp_env import (
    FULL_OPEN_SUM,  # 0.080 (2 * FINGER_OPEN_POS)
    NewtonUnclampEnv,
)
from task_config import (
    CABLE_RADIUS,
    CLIP_BASE_HEIGHT,
    FINGER_HALF_OPEN_POS,
    FINGER_OPEN_POS,
    FINGER_STEP_SIZE,
    K_UNCLAMP,
    T_GROOVE,
    T_SEAT,
    TABLE_HEIGHT,
    UNCLAMP_TERMINAL_STEPS,
)

# =========================================================================
# Module constants (v1.0; see §0 docstring for downstream contract)
# =========================================================================

UNCLAMP_VERSION = "v1.0"
UNCLAMP_ARCHITECTURE = "env.step + mppi_scene separate (Option III, additive cost default)"
UNCLAMP_MPPI_ACTION_DIM = 4  # [finger_delta, L_pos_x, L_pos_y, L_pos_z] — L-only
UNCLAMP_HDF5_ACTION_DIM = 4  # env-native, no R-first mapping needed
UNCLAMP_ACTION_LAYOUT = "L-only"  # vs Grip "R-first" (env newton_unclamp_env.py:28-31)

# UNCLAMP-SYS-1: ADDITIVE cost is default; MULTIPLICATIVE retained as ablation.
UNCLAMP_COST_METHOD_ADDITIVE = (
    "-alpha*r_finger - beta*r_seated + unclamp_scale*(pos_L + m3*ori_L) + seated_scale*(1 - r_seated) + P_drop*I(drop)"
)
UNCLAMP_COST_METHOD_MULTIPLICATIVE = (
    "-(r_finger * r_seated) + unclamp_scale*(pos_L + m3*ori_L) + seated_scale*(1 - r_seated) + P_drop*I(drop)"
)

# UNCLAMP-SYS-1: independent weights for additive reward terms (module consts;
# kept out of cfg to preserve G1 spec — config changes require re-approval).
UNCLAMP_ALPHA_FINGER = 2.0  # independent finger progress weight (additive)
UNCLAMP_BETA_SEATED = 1.0  # independent cable-seated weight (additive)

# Finger joint-coord indices (joint-coord layout; per-arm [7, 8]).
FINGER_JOINT_COORD_INDICES_L = [7, 8]
FINGER_JOINT_COORD_INDICES_R = [FRANKA_NUM_JOINTS + 7, FRANKA_NUM_JOINTS + 8]

# Cable drop detection. UNCLAMP-HIGH-3: align with env DROP_Z_THRESH =
# TABLE_HEIGHT - 0.02 (20mm below table), NOT GROOVE_CENTER_Z — PROPOSE used
# the groove reference which creates false-positives at the normal seated z.
CABLE_DROP_Z_MARGIN_M = 0.020
CABLE_DROP_Z_THR = TABLE_HEIGHT - CABLE_DROP_Z_MARGIN_M
P_CABLE_DROP = 100.0  # AR precedent `P_DROP` catastrophic penalty

# UNCLAMP-HIGH-2: override cfg.r_ori_ik_weight (0.0 "passive") with soft-pin
# value for rollout wrist stability. Prevents indeterminate R wrist rotation
# between replans while still leaving cfg semantic unchanged (cfg value is
# the "intent"; solver value is the pragmatic stability bound).
IK_SOFT_R_ORI = 0.3

# RUN_METRICS / S3 labels
UNCLAMP_S1_LABEL = "S1_finger_open_rate"
UNCLAMP_S2_LABEL = "S2_seated_rate"
UNCLAMP_S3_LABEL = "S3_combined_sustained_rate"


# =========================================================================
# base_scene_to_m2_info — inline duplicate from AR/Grip (FM-10 mitigation).
# =========================================================================


def base_scene_to_m2_info(scene):
    """Translate build_multiworld_scene dict to M2-compat info keys.

    M2-compat keys required by get_ee_poses_dual / update_kinematic_bodies.
    Mirrors Grip G3a:153-166 verbatim.
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
# Env state cloning: env world 0 -> mppi_scene all K worlds.
# =========================================================================


def clone_env_to_mppi(env, mppi_scene, mppi_info, K):
    """Copy env._state_0 world 0 body_q/body_qd into mppi_scene all K worlds.

    Called at start of every MPPI plan so mppi_scene rollout starts from env's
    authoritative physics state. Identical to Grip G3a:174-217.

    Args:
        env: NewtonUnclampEnv instance (K_EXEC=1).
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
# Unclamp-specific helpers.
# =========================================================================


def compute_unclamp_groove_seg_indices(state, info, groove_center_xy, world_count, win=1):
    """Compute per-world ±win cable seg indices nearest groove center (xy plane).

    Mirrors ``newton_unclamp_env._compute_groove_seg_indices`` (L587-597) but
    reads from mppi_scene state via info dict (M2-compat). Used to identify
    the cable seg that should remain seated during the Unclamp episode.
    """
    bq = state.body_q.numpy()
    flat = bq.view(np.float32).reshape(-1, 7)
    bws = info["bws"]
    co = info["cable_offset"]
    cpw = info["cable_per_world"]
    clip_xy = np.asarray(groove_center_xy, dtype=np.float32)

    indices = []
    for w in range(world_count):
        ws = bws[w]
        cable_pos = flat[ws + co : ws + co + cpw, :3]
        dists_xy = np.linalg.norm(cable_pos[:, :2] - clip_xy, axis=1)
        center_idx = int(np.argmin(dists_xy))
        lo = max(0, center_idx - win)
        hi = min(cpw - 1, center_idx + win)
        indices.append(np.arange(lo, hi + 1, dtype=np.int32))
    return indices


def compute_seated_mask(state, info, K, groove_seg_indices, groove_center_pos, groove_target_quat):
    """Return bool (K,) mask: True iff cable is seated for that world.

    Seated = nearest cable seg to groove_center has:
      - 3D pos distance < T_GROOVE (0.003), and
      - |quat dot groove_target_quat| > T_SEAT (0.85).
    """
    bq = state.body_q.numpy()
    flat = bq.view(np.float32).reshape(-1, 7)
    bws = info["bws"]
    co = info["cable_offset"]
    cpw = info["cable_per_world"]

    seated = np.zeros(K, dtype=bool)
    for w in range(K):
        ws = bws[w]
        cable_pos = flat[ws + co : ws + co + cpw, :3]
        seg_pos, seg_tangent, _ = find_nearest_cable_point(cable_pos, groove_center_pos, groove_seg_indices[w])
        dist_pos = float(np.linalg.norm(seg_pos - groove_center_pos))
        seg_quat = _normalize_quat_w_positive(np.asarray(compute_hand_quat_for_cable(seg_tangent), dtype=np.float32))
        cos_sim = abs(float(np.dot(seg_quat, groove_target_quat)))
        seated[w] = (dist_pos < T_GROOVE) and (cos_sim > T_SEAT)
    return seated


def compute_l_arm_to_seg_costs(state, info, K, groove_seg_indices):
    """Per-world L arm clamp (pos, ori) distance to nearest seated cable seg.

    Returns (pos_dist_L[K], ori_dist_L[K]) float32 arrays used for tracking
    cost: ``cfg.unclamp_cost_scale * (pos_dist_L + cfg.m3_cost_scale * ori_dist_L)``.
    """
    bq = state.body_q.numpy()
    flat = bq.view(np.float32).reshape(-1, 7)
    bws = info["bws"]
    co = info["cable_offset"]
    cpw = info["cable_per_world"]

    pos_L = np.zeros(K, dtype=np.float32)
    ori_L = np.zeros(K, dtype=np.float32)

    for w in range(K):
        ws = bws[w]
        cable_pos = flat[ws + co : ws + co + cpw, :3]
        left_ee_idx = ws + EE_BODY_OFFSET
        left_ee_pos = flat[left_ee_idx, :3]
        left_ee_quat = _normalize_quat_w_positive(flat[left_ee_idx, 3:7])
        clamp_L = compute_clamp_pos(left_ee_pos, left_ee_quat)

        seg_pos, seg_tangent, d_L = find_nearest_cable_point(cable_pos, clamp_L, groove_seg_indices[w])
        pos_L[w] = d_L
        target_quat_L = _normalize_quat_w_positive(
            np.asarray(compute_hand_quat_for_cable(seg_tangent), dtype=np.float32)
        )
        ori_L[w] = _quat_distance(left_ee_quat, target_quat_L)

    return pos_L, ori_L


def compute_cable_drop_mask(state, info, K):
    """Detect cable-dropped worlds: any cable seg z < CABLE_DROP_Z_THR.

    UNCLAMP-HIGH-3: aligns with env DROP_Z_THRESH = TABLE_HEIGHT - 0.02.
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


def sample_action_sequences_with_bias(K, H, action_dim, sigma, beta, nominal, rng=None):
    """Sample K action sequences with an additive nominal bias.

    Reuses ``sample_action_sequences`` (which returns clipped ±1.0 noise) and
    adds a per-timestep nominal bias. Output is NOT re-clipped to ±1.0 — the
    biased finger dim (nominal=1.0) is expected to saturate near ±1.6 which
    is within the downstream env scale handling (finger_delta is
    ``max(0, a) * FINGER_STEP_SIZE``, unbounded on the positive side is fine).

    Args:
        K, H, action_dim: shape of output.
        sigma: noise_sigma for underlying Gaussian.
        beta: noise_correlation (temporal AR1).
        nominal: (H, action_dim) float32 additive bias per timestep.
        rng: numpy Generator.

    UNCLAMP-SYSTEMIC-2: finger dim biased to 1.0 so K-rollout generates
    ~40mm opening over H=20 (vs ~1.6mm with noise alone).
    """
    noise = sample_action_sequences(K, H, action_dim, sigma, beta, rng=rng)
    return (noise + nominal[None, :, :]).astype(np.float32)


# =========================================================================
# MPPI rollout + cost (mppi_scene only; env untouched during rollout).
# =========================================================================


def rollout_and_cost_unclamp(
    mppi_scene,
    mppi_info,
    ik_solver,
    per_world_jq,
    K,
    H,
    cfg,
    groove_seg_indices,
    groove_center_pos,
    groove_target_quat,
    ik_target_quat_L_init,
    initial_R_ee_pos_world,
    initial_R_ee_quat_world,
    cost_mode,
):
    """Rollout K trajectories in mppi_scene for H steps with 4D Unclamp actions.

    Action layout (L-only, env native):
        [0]   finger_delta (clipped ``max(0, a)`` — OPEN direction only)
        [1:4] L EE ΔXYZ (scaled by cfg.pos_action_scale for rollout IK;
              stored unscaled for env.step replay which applies POS_ACTION_SCALE).

    UNCLAMP-SYS-1: default cost is ADDITIVE, multiplicative is opt-in.

    Returns:
        actions, costs, n_nan, t_ik_total, t_physics_total, ee_spread_max_L,
        drift_tangent, drop_count
    """
    model = mppi_scene["model"]
    solver_vbd = mppi_scene["solver"]
    state_0 = mppi_scene["state_0"]
    state_1 = mppi_scene["state_1"]
    control = mppi_scene["control"]

    sim_dt = DT / RL_SIM_SUBSTEPS
    costs = np.zeros(K, dtype=np.float32)
    t_ik_total = 0.0
    t_physics_total = 0.0
    nan_mask = np.zeros(K, dtype=bool)
    ee_spread_max_left = 0.0

    bws = mppi_info["bws"]
    bpw = mppi_info["bodies_per_world"]
    co = mppi_info["cable_offset"]
    cpw = mppi_info["cable_per_world"]

    # UNCLAMP-SYS-2: bias finger dim to 1.0 nominal (open-velocity). H=20 ×
    # biased base gives ~40mm opening vs ~1.6mm with unit noise alone.
    base_action_seq = np.zeros((H, UNCLAMP_MPPI_ACTION_DIM), dtype=np.float32)
    base_action_seq[:, 0] = 1.0  # finger open bias (full-velocity nominal)

    rng = np.random.default_rng(cfg.K + int(time.time_ns() % 1_000_000))
    actions = sample_action_sequences_with_bias(
        K,
        H,
        UNCLAMP_MPPI_ACTION_DIM,
        cfg.noise_sigma,
        cfg.noise_correlation,
        base_action_seq,
        rng,
    )

    # Tangent drift capture (world 0, tracked on cable seg nearest to groove).
    w0 = bws[0]
    flat_start = state_0.body_q.numpy().view(np.float32).reshape(-1, 7)
    cable_start = flat_start[w0 + co : w0 + co + cpw, :3].copy()
    # Tangent at the central groove seg (middle of groove_seg_indices[0]).
    center_idx_start = int(groove_seg_indices[0][len(groove_seg_indices[0]) // 2])
    tangent_L_start = compute_cable_tangent(cable_start, center_idx_start)

    # IK target quat (L arm ori is held at hand-down throughout; no per-step accumulate).
    ik_tgt_L = np.tile(ik_target_quat_L_init[None].astype(np.float32), (K, 1))
    # R arm targets: fixed at initial pose for all K worlds, all H steps.
    r_pos_target = np.tile(initial_R_ee_pos_world[None].astype(np.float32), (K, 1))
    r_quat_target = np.tile(initial_R_ee_quat_world[None].astype(np.float32), (K, 1))

    # Per-world L finger joint-coord position accumulator (init from per_world_jq[:, 7]).
    finger_pos_L = per_world_jq[:K, 7].copy().astype(np.float32)

    jq = per_world_jq.copy()

    for h in range(H):
        # Current L EE pos (pre-IK, post previous-step physics).
        (left_ee_pos_curr, _), _ = get_ee_poses_dual(state_0, mppi_info, K)

        # === 4D action split ===
        # Enforce OPEN-only finger direction via max(0, .). Post-weighting
        # best_action uses this same clip pattern (feasibility assertion in mppi_plan).
        finger_delta_raw = actions[:, h, 0]
        finger_delta = np.maximum(finger_delta_raw, 0.0).astype(np.float32) * FINGER_STEP_SIZE
        L_pos_delta = actions[:, h, 1:4] * cfg.pos_action_scale
        target_L_pos = left_ee_pos_curr + L_pos_delta

        # === IK solve (bimanual scene; R soft-pinned via IK_SOFT_R_ORI) ===
        t0_ik = time.perf_counter()
        jq_solved = ik_solver.solve(target_L_pos, ik_tgt_L, r_pos_target, r_quat_target, jq)

        # Apply finger deltas directly to joint-coord array.
        # L fingers: clamp within [HALF_OPEN, FULL_OPEN] to match env :914 behavior.
        finger_pos_L = np.clip(finger_pos_L + finger_delta, FINGER_HALF_OPEN_POS, FINGER_OPEN_POS)
        for fc in FINGER_JOINT_COORD_INDICES_L:
            jq_solved[:, fc] = finger_pos_L
        # R fingers: passive OPEN (env holds R at FINGER_OPEN_POS constantly).
        for fc in FINGER_JOINT_COORD_INDICES_R:
            jq_solved[:, fc] = FINGER_OPEN_POS

        fk_body_q = ik_solver.eval_fk_batch(jq_solved)
        t_ik_total += time.perf_counter() - t0_ik

        update_kinematic_bodies(state_0, fk_body_q, mppi_info, K)

        # EE spread diagnostic (L arm only; R is fixed pin).
        (ik_left, _), _ = get_ee_poses_dual(state_0, mppi_info, K)
        valid_idx = ~nan_mask
        if valid_idx.sum() > 1:
            ee_spread_max_left = max(
                ee_spread_max_left,
                float(np.sqrt(np.sum(np.var(ik_left[valid_idx], axis=0)))),
            )

        # === Physics step (mppi_scene; no groove_spring — env only has it) ===
        t0_phys = time.perf_counter()
        contacts = model.collide(state_0)
        for _ in range(RL_SIM_SUBSTEPS):
            solver_vbd.step(state_0, state_1, control, contacts, sim_dt)
            state_0, state_1 = state_1, state_0
        t_physics_total += time.perf_counter() - t0_phys

        # NaN check (K-scoped; invalid worlds get huge cost and are skipped).
        bq_check = state_0.body_q.numpy()
        for w in range(K):
            if not nan_mask[w]:
                s = bws[w]
                chunk = bq_check[s : s + bpw]
                if np.any(np.isnan(chunk)) or np.any(np.isinf(chunk)):
                    nan_mask[w] = True
                    costs[w] = 1e6

        # === Compute per-world cost terms ===
        # Finger progress (normalized): [0, 1] across [HALF_OPEN_SUM, FULL_OPEN_SUM].
        opening_L = 2.0 * finger_pos_L  # j7 + j8 sum
        denom_finger = cfg.finger_full_open_sum_m - cfg.finger_half_open_sum_m
        r_finger = np.clip(
            (opening_L - cfg.finger_half_open_sum_m) / denom_finger,
            0.0,
            1.0,
        ).astype(np.float32)

        # Seated mask
        seated = compute_seated_mask(state_0, mppi_info, K, groove_seg_indices, groove_center_pos, groove_target_quat)
        r_seated = seated.astype(np.float32)

        # L arm tracking cost (pos to nearest seg, ori to tangent-derived quat).
        pos_L, ori_L = compute_l_arm_to_seg_costs(state_0, mppi_info, K, groove_seg_indices)

        # === Cost assembly ===
        if cost_mode == "additive":
            # UNCLAMP-SYS-1 default: independent reward terms + tracking + unseat.
            step_cost = (
                -UNCLAMP_ALPHA_FINGER * r_finger
                - UNCLAMP_BETA_SEATED * r_seated
                + cfg.unclamp_cost_scale * (pos_L + cfg.m3_cost_scale * ori_L)
                + cfg.cable_seated_cost_scale * (1.0 - r_seated)
            ).astype(np.float32)
        else:
            # Multiplicative (ablation only; collapses when r_seated=0 all K).
            step_cost = (
                -(r_finger * r_seated)
                + cfg.unclamp_cost_scale * (pos_L + cfg.m3_cost_scale * ori_L)
                + cfg.cable_seated_cost_scale * (1.0 - r_seated)
            ).astype(np.float32)

        # Cable drop catastrophe (additive).
        drop_mask = compute_cable_drop_mask(state_0, mppi_info, K)
        step_cost += np.where(drop_mask, P_CABLE_DROP, 0.0).astype(np.float32)

        costs += np.where(nan_mask, 0.0, step_cost)
        jq = jq_solved.copy()

    # Tangent drift end (world 0, same center seg).
    flat_end = state_0.body_q.numpy().view(np.float32).reshape(-1, 7)
    cable_end = flat_end[w0 + co : w0 + co + cpw, :3].copy()
    center_idx_end = int(groove_seg_indices[0][len(groove_seg_indices[0]) // 2])
    tangent_L_end = compute_cable_tangent(cable_end, center_idx_end)
    dot_L = float(np.clip(np.dot(tangent_L_start, tangent_L_end), -1.0, 1.0))
    drift_tangent = float(math.acos(dot_L))

    drop_final_mask = compute_cable_drop_mask(state_0, mppi_info, K)
    drop_count = int(drop_final_mask.sum())

    n_nan = int(nan_mask.sum())
    if n_nan > 0:
        print(f"  [NaN] {n_nan}/{K} worlds had NaN ({n_nan * 100 // K}%)")

    return (
        actions,
        costs,
        n_nan,
        t_ik_total,
        t_physics_total,
        ee_spread_max_left,
        drift_tangent,
        drop_count,
    )


# =========================================================================
# MPPI plan: clone env state, rollout, weight, return best 4D action.
# =========================================================================


def mppi_plan(
    env,
    mppi_scene,
    mppi_info,
    ik_solver,
    cfg,
    cfg_K,
    per_world_jq_ref,
    ik_target_L_init,
    initial_R_ee_pos_world,
    initial_R_ee_quat_world,
    groove_center_pos,
    groove_target_quat,
    cost_mode,
):
    """One MPPI plan step for Unclamp: clone -> rollout -> weight -> best action.

    Returns:
        best_action_4d: (H, 4) weighted-mean action sequence (unitless).
        diag: dict of diagnostics (n_nan, cost_range, entropy, drop_count, ...).
    """
    K = cfg_K

    clone_env_to_mppi(env, mppi_scene, mppi_info, K)

    # Per-world groove seg indices from cloned state (fixed for H steps).
    groove_seg_indices = compute_unclamp_groove_seg_indices(
        mppi_scene["state_0"],
        mppi_info,
        groove_center_pos[:2],
        K,
        win=1,
    )

    per_world_jq = np.tile(per_world_jq_ref[None].astype(np.float64), (K, 1))

    actions, costs, n_nan, t_ik, t_phys, ee_spread, drift_tangent, drop_count = rollout_and_cost_unclamp(
        mppi_scene,
        mppi_info,
        ik_solver,
        per_world_jq,
        K,
        cfg.H,
        cfg,
        groove_seg_indices,
        groove_center_pos,
        groove_target_quat,
        ik_target_L_init,
        initial_R_ee_pos_world,
        initial_R_ee_quat_world,
        cost_mode,
    )

    # Softmax weighting over negative cost (mppi_weights is canonical M2 impl).
    weights = mppi_weights(costs, cfg.temperature_lambda)
    best_action_4d = np.einsum("k,kha->ha", weights, actions).astype(np.float32)

    # UNCLAMP-SYS-2 defensive assertion (CC3): finger dim must retain
    # non-degenerate bias after weighting. If this fails, the finger bias +
    # noise is not producing gradient signal.
    finger_abs_max = float(np.abs(best_action_4d[:, 0]).max())
    if finger_abs_max <= 0.3:
        print(
            f"  [WARN UNCLAMP-SYS-2] best_action finger dim max={finger_abs_max:.3f} <= 0.3 "
            "(expected ~1.0 with bias; signal may be degenerate)"
        )

    # Diagnostics structure mirrors Grip G3a:524-563.
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

    ba_has_nan = bool(np.any(np.isnan(best_action_4d)) or np.any(np.isinf(best_action_4d)))

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
        "drift_tangent_rad": drift_tangent,
        "drop_count": drop_count,
        "t_ik_total_s": t_ik,
        "t_physics_total_s": t_phys,
        "finger_abs_max": finger_abs_max,
    }
    return best_action_4d, diag


# =========================================================================
# Main demo generation: env.step execute + mppi_plan rollout.
# =========================================================================


def mppi_generate_demos_unclamp(
    cfg,
    device,
    max_steps=UNCLAMP_TERMINAL_STEPS,
    n_demos=5,
    seed=42,
    diag_csv_path="/tmp/mppi_unclamp_metrics.csv",
    cost_mode="additive",
):
    """Generate Unclamp demos via env.step hybrid (Option III).

    env (K_EXEC=1) for episode execution + mppi_scene (K_MPPI=cfg.K) for rollout.

    Returns:
        demos: list of per-episode dicts (action_delta/obs/ee_pos/quat/
               finger_opening_L/R/dist_pos_L/dist_ori_L/cable_pos_seq + success attrs).
        drifts_per_plan: list[float] — per-plan tangent drift across all episodes.
        drifts_per_episode_max: list[float] — max drift per episode.
        cable_endpoints_L/R: list of ndarrays — per-episode seg 0 / seg last pos at reset.
    """
    K = cfg.K
    H = cfg.H
    replan_interval = cfg.replan_interval

    print(f"\n[MPPI-Unclamp] {UNCLAMP_VERSION} Option III: env.step hybrid (cost_mode={cost_mode})")
    print(f"  K_EXEC=1 (env), K_MPPI={K} (mppi_scene), H={H}, replan={replan_interval}")
    print(f"  pos_scale={cfg.pos_action_scale}, m3_cost_scale={cfg.m3_cost_scale:.4f}")
    print(f"  unclamp_cost_scale={cfg.unclamp_cost_scale}, cable_seated_cost_scale={cfg.cable_seated_cost_scale}")
    print(f"  alpha_finger={UNCLAMP_ALPHA_FINGER}, beta_seated={UNCLAMP_BETA_SEATED} (additive)")
    print(f"  l_ori_ik_weight={cfg.l_ori_ik_weight}, r_ori_ik_weight={cfg.r_ori_ik_weight} (cfg intent)")
    print(f"  IK_SOFT_R_ORI={IK_SOFT_R_ORI} (UNCLAMP-HIGH-2 override)")
    print("[FIX UNCLAMP-SYS-1] ADDITIVE cost default (multiplicative available as --cost-mode)")
    print("[FIX UNCLAMP-SYS-2] Finger sample bias base_action_seq[:, 0] = 1.0 (H=20 infeasibility mitigation)")
    print("[FIX UNCLAMP-SYS-3] K_MPPI default 128 (Grip G6a-128 stable optimum)")
    print("[FIX UNCLAMP-HIGH-2] IK_SOFT_R_ORI=0.3 override cfg.r_ori_ik_weight")
    print(f"[FIX UNCLAMP-HIGH-3] CABLE_DROP_Z_THR={CABLE_DROP_Z_THR:.4f} (TABLE_HEIGHT - 0.020)")

    # =====================================================================
    # Phase A: env construction + monkey-patches (instance attribute shadowing)
    # =====================================================================
    print("[MPPI-Unclamp] Phase A: env construction...")
    env = NewtonUnclampEnv(world_count=1, device=device)

    # Defensive assert (CC3): env FINGER_ACTION_SCALE must match our module's
    # assumption about FINGER_STEP_SIZE since the rollout and env.step apply
    # the same scale independently.
    if not math.isclose(env.FINGER_ACTION_SCALE, FINGER_STEP_SIZE, rel_tol=1e-6):
        raise RuntimeError(
            f"env.FINGER_ACTION_SCALE ({env.FINGER_ACTION_SCALE}) != "
            f"FINGER_STEP_SIZE ({FINGER_STEP_SIZE}). Rollout/env scale mismatch."
        )

    # Monkey-patch (reversible; env default POS_ACTION_SCALE=0.015, override with cfg 0.010).
    env.POS_ACTION_SCALE = cfg.pos_action_scale
    env.max_episode_length = 100_000  # disable env internal timeout (generator manages)
    _env_reset_original = env._reset_worlds
    env._reset_worlds = lambda env_ids: None  # no-op intra-episode; manual inter-episode

    def env_reset_manual():
        """Invoke original _reset_worlds for inter-episode reset."""
        _env_reset_original(list(range(env._world_count)))

    # Capture initial R EE pose (FIXED for all episodes — R arm passive, P0 always same).
    initial_R_ee_pos_world = env._settled_ee_r_pos.copy().astype(np.float32)
    initial_R_ee_quat_world = _normalize_quat_w_positive(env._settled_ee_r_quat).astype(np.float32)
    # L ori target: env holds L rotation at initial hand-down quat.
    initial_L_ee_quat_world = _normalize_quat_w_positive(env._settled_ee_l_quat).astype(np.float32)

    # CC6 C4: use env runtime attrs (not module redefinition) for groove center + target quat.
    groove_center_pos = env.GROOVE_CENTER_POS.copy().astype(np.float32)
    groove_target_quat = env.GROOVE_TARGET_QUAT.copy().astype(np.float32)

    # =====================================================================
    # Phase B: mppi_scene build + IK solver
    # =====================================================================
    print(f"[MPPI-Unclamp] Phase B: mppi_scene (K={K})...")
    fk_model_mppi = env._fk_model
    fk_state_mppi = env._fk_state
    # Unclamp env has target clip C1 at (CLIP1_X, CLIP1_Y), no support clips.
    # cable_start_pos is pre-settle layout; cloning from env every plan rewrites
    # cable state anyway so exact initial layout doesn't affect rollout.
    cable_start_x = float(env.UNCLAMP_EE_LEFT[0])
    mppi_scene = build_multiworld_scene(
        fk_model_mppi,
        fk_state_mppi,
        K,
        device,
        cable_start_pos=(cable_start_x, 0.0, TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS),
        add_support_clips=False,  # Unclamp env uses only target clip C1
        add_target_clip=True,  # C1 V-groove matches env (env:384-410)
    )
    mppi_info = base_scene_to_m2_info(mppi_scene)
    if mppi_info["bodies_per_world"] != env._bodies_per_world:
        raise RuntimeError(
            f"[MPPI-Unclamp] bodies_per_world mismatch: env={env._bodies_per_world}, "
            f"mppi_scene={mppi_info['bodies_per_world']}. "
            "Check add_target_clip / add_support_clips alignment with env."
        )
    print(f"  mppi bodies_per_world={mppi_info['bodies_per_world']}, cable_per_world={mppi_info['cable_per_world']}")

    # UNCLAMP-HIGH-2: IK solver instantiated with IK_SOFT_R_ORI, NOT cfg.r_ori_ik_weight.
    # cfg.r_ori_ik_weight=0.0 is the semantic "R passive" declaration; the solver
    # uses 0.3 soft-pin to prevent wrist indeterminacy between replans.
    ik_solver = MppiIKSolverM3(
        fk_model_mppi,
        K,
        device,
        l_ori_weight=cfg.l_ori_ik_weight,
        r_ori_weight=IK_SOFT_R_ORI,
    )

    # =====================================================================
    # Phase C: episode loop
    # =====================================================================
    demos = []
    drifts_per_plan = []
    drifts_per_episode_max = []
    cable_endpoints_L = []
    cable_endpoints_R = []

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
            "drift_tangent_rad",
            "drop_count",
            "sustain_count",
            "opening_L",
            "seated_flag",
            "finger_abs_max",
            "pos_action_scale",
            "cost_mode",
        ]
    )

    env_cable_off = env._cable_body_offset
    env_cable_per = env._cable_bodies_per_world

    for ep in range(n_demos):
        print(f"\n[MPPI-Unclamp] Episode {ep + 1}/{n_demos}")

        env_reset_manual()
        obs, _ = env.get_observations()

        # Cable endpoints at reset (from env state, world 0).
        wp.synchronize()
        env_bq = env._state_0.body_q.numpy()
        env_bws0 = env._bws[0]
        cable_flat = env_bq.view(np.float32).reshape(-1, 7)
        cable_L_reset = cable_flat[env_bws0 + env_cable_off, :3].astype(np.float32).copy()
        cable_R_reset = cable_flat[env_bws0 + env_cable_off + env_cable_per - 1, :3].astype(np.float32).copy()
        cable_endpoints_L.append(cable_L_reset)
        cable_endpoints_R.append(cable_R_reset)

        # Per-episode trajectory buffers.
        traj_actions = []
        traj_obs = []
        traj_left_pos = []
        traj_left_quat = []
        traj_right_pos = []
        traj_right_quat = []
        traj_finger_L = []
        traj_dist_pos_L = []
        traj_dist_ori_L = []
        traj_cable_pos = []
        traj_seated = []
        drifts_ep = []

        step = 0
        sustain_count = 0
        success = False
        success_step = -1
        seated_terminal = False

        best_action_4d = None
        plan_idx = 0
        diag = {}

        while step < max_steps:
            # MPPI plan (every replan_interval steps, or at step=0).
            if step % replan_interval == 0:
                t0_plan = time.perf_counter()
                per_world_jq_env_w0 = env._per_world_fk_jq[0].copy()
                best_action_4d, diag = mppi_plan(
                    env,
                    mppi_scene,
                    mppi_info,
                    ik_solver,
                    cfg,
                    K,
                    per_world_jq_env_w0,
                    initial_L_ee_quat_world,
                    initial_R_ee_pos_world,
                    initial_R_ee_quat_world,
                    groove_center_pos,
                    groove_target_quat,
                    cost_mode,
                )
                t_plan = time.perf_counter() - t0_plan
                drifts_ep.append(diag["drift_tangent_rad"])

                if plan_idx == 0 or plan_idx % 5 == 0:
                    print(
                        f"  [PLAN {plan_idx}] step={step} plan_t={t_plan:.2f}s "
                        f"nan={diag['n_nan']}/{K} k_eff={diag['k_eff']} "
                        f"cost_range={diag['cost_range']:.4f} entropy={diag['weight_entropy']:.2f} "
                        f"drift={math.degrees(diag['drift_tangent_rad']):.1f}° drop={diag['drop_count']} "
                        f"finger|max|={diag['finger_abs_max']:.3f}"
                    )
                plan_idx += 1

            h_exec = step % replan_interval
            action_4d = best_action_4d[h_exec].astype(np.float32)  # (4,) unitless
            assert action_4d.shape == (4,), f"action shape {action_4d.shape} != (4,)"

            # UNCLAMP-HIGH-4 sanity: policy output ±1.0 range. MPPI noise typ ±0.6,
            # bias pushes finger dim to ~1.6 max; L_pos dims [1:4] unbiased in ±0.6.
            # Large deviation likely indicates scale / normalization bug.
            if np.abs(action_4d[1:4]).max() > 1.5:
                print(f"  [WARN UNCLAMP-HIGH-4] action_4d[1:4] |max|={np.abs(action_4d[1:4]).max():.3f} > 1.5")

            action_tensor = torch.from_numpy(action_4d).unsqueeze(0).to(device)  # (1, 4)

            # Record state BEFORE env.step (trajectory entry is "state at which action was taken").
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
                    env_bws0 + env_cable_off : env_bws0 + env_cable_off + env_cable_per,
                    :3,
                ]
                .astype(np.float32)
                .copy()
            )

            # env.step handles finger clip / IK / physics / spring / sanitise / state-swap / obs.
            obs, reward, done, extras = env.step(action_tensor)

            # Extract post-step metrics.
            obs_np = obs[0].cpu().numpy()
            # env obs layout (newton_unclamp_env.py :11-26):
            #   [15]    left finger opening (j7 + j8)
            #   [16:19] cable groove seg pos
            #   [19:23] cable groove seg quat
            #   [36:39] left ori error axis-angle
            #   [39:42] left pos error
            dist_pos_L = float(np.linalg.norm(obs_np[39:42]))
            dist_ori_L = float(np.linalg.norm(obs_np[36:39]))
            opening_L_post = float(env._per_world_fk_jq[0, 7] + env._per_world_fk_jq[0, 8])

            # Seated check from obs (seg_pos at 16:19, seg_quat at 19:23).
            seg_pos_obs = obs_np[16:19]
            seg_quat_obs = obs_np[19:23]
            seated_pos_err = float(np.linalg.norm(seg_pos_obs - groove_center_pos))
            seated_ori_cos = abs(float(np.dot(seg_quat_obs, groove_target_quat)))
            is_seated_now = (seated_pos_err < T_GROOVE) and (seated_ori_cos > T_SEAT)
            is_finger_open_now = opening_L_post >= cfg.success_threshold_finger_open_m

            # Sustained-K5 check (generator-side, mirrors env semantics).
            success_this_step = is_finger_open_now and is_seated_now
            if success_this_step:
                sustain_count += 1
                if sustain_count >= K_UNCLAMP and success_step < 0:
                    success = True
                    success_step = step
            else:
                sustain_count = 0

            # Record trajectory
            traj_actions.append(action_4d)
            traj_obs.append(obs_np.copy())
            traj_left_pos.append(left_pos_now)
            traj_left_quat.append(left_quat_now)
            traj_right_pos.append(right_pos_now)
            traj_right_quat.append(right_quat_now)
            traj_finger_L.append(opening_L_post)
            traj_dist_pos_L.append(dist_pos_L)
            traj_dist_ori_L.append(dist_ori_L)
            traj_cable_pos.append(cable_now)
            traj_seated.append(is_seated_now)
            seated_terminal = is_seated_now

            # Diag CSV row (per-step).
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
                    f"{diag.get('drift_tangent_rad', 0.0):.4f}",
                    diag.get("drop_count", 0),
                    sustain_count,
                    f"{opening_L_post:.4f}",
                    int(is_seated_now),
                    f"{diag.get('finger_abs_max', 0.0):.4f}",
                    f"{cfg.pos_action_scale:.4f}",
                    cost_mode,
                ]
            )

            step += 1

            # UNCLAMP-HIGH-1: unconditional break on env-done (success already recorded above).
            if done[0].item():
                print(f"  [TERMINAL] step={step} env-done (success={success})")
                break

        # End of episode
        if success:
            print(
                f"  SUCCESS at step {success_step}, final "
                f"pos L={traj_dist_pos_L[-1]:.4f}m ori L={math.degrees(traj_dist_ori_L[-1]):.1f}° "
                f"finger L={traj_finger_L[-1] * 1000:.1f}mm seated={seated_terminal}"
            )
        else:
            print(
                f"  FAILED at step {step}, final "
                f"pos L={traj_dist_pos_L[-1]:.4f}m ori L={math.degrees(traj_dist_ori_L[-1]):.1f}° "
                f"finger L={traj_finger_L[-1] * 1000:.1f}mm seated={seated_terminal}"
            )

        T = len(traj_actions)
        # UNCLAMP-CRIT-1: constant finger_opening_R dataset (R passive at FULL_OPEN_SUM).
        finger_opening_R = np.full(T, FULL_OPEN_SUM, dtype=np.float32)

        demo = {
            "action_delta": np.array(traj_actions, dtype=np.float32).reshape(-1, UNCLAMP_HDF5_ACTION_DIM),
            "obs": np.array(traj_obs, dtype=np.float32).reshape(-1, 42),
            "left_ee_pos": np.array(traj_left_pos, dtype=np.float32),
            "left_ee_quat": np.array(traj_left_quat, dtype=np.float32),
            "right_ee_pos": np.array(traj_right_pos, dtype=np.float32),
            "right_ee_quat": np.array(traj_right_quat, dtype=np.float32),
            "finger_opening_L": np.array(traj_finger_L, dtype=np.float32),
            "finger_opening_R": finger_opening_R,
            "dist_pos_left": np.array(traj_dist_pos_L, dtype=np.float32),
            "dist_ori_left": np.array(traj_dist_ori_L, dtype=np.float32),
            "cable_pos_seq": np.array(traj_cable_pos, dtype=np.float32)
            if traj_cable_pos
            else np.zeros((0, 0, 3), dtype=np.float32),
            "seated_per_step": np.array(traj_seated, dtype=bool),
            "success": bool(success),
            "success_step": int(success_step),
            "sustain_count_final": int(sustain_count),
            "seated_terminal": bool(seated_terminal),
            "steps": int(step),
        }
        demos.append(demo)
        for d in drifts_ep:
            drifts_per_plan.append(d)
        ep_max = max(drifts_ep, default=0.0)
        drifts_per_episode_max.append(float(ep_max))

    diag_file.close()
    print(f"\n[DIAG] CSV -> {diag_csv_path}")

    return demos, drifts_per_plan, drifts_per_episode_max, cable_endpoints_L, cable_endpoints_R


# =========================================================================
# Success rates + HDF5 save + RUN_METRICS.
# =========================================================================


def compute_unclamp_success_rates(demos, cfg):
    """S1/S2/S3 rates from demos list.

    - S1: opening_L_terminal >= cfg.success_threshold_finger_open_m
    - S2: seated at terminal (seg pos < T_GROOVE ∧ cos > T_SEAT)
    - S3: demo.success (sustained K_UNCLAMP steps ∧ finger open ∧ seated)
    """
    if not demos:
        return {"s1": 0.0, "s2": 0.0, "s3": 0.0}
    n1 = n2 = n3 = 0
    for d in demos:
        if len(d["finger_opening_L"]) == 0:
            continue
        if d["finger_opening_L"][-1] >= cfg.success_threshold_finger_open_m:
            n1 += 1
        if bool(d.get("seated_terminal", False)):
            n2 += 1
        if d["success"]:
            n3 += 1
    n = len(demos)
    return {"s1": n1 / n, "s2": n2 / n, "s3": n3 / n}


def save_demos_hdf5_unclamp(demos, cfg, output_path, mppi_mode, cost_mode, cable_endpoint_mean=None):
    """Save Unclamp demos to HDF5 (4D L-only schema).

    Differences from Grip G3a HDF5:
      - action_dim=4 (L-only) vs Grip 14D.
      - finger_opening_R is a constant dataset (R passive); see UNCLAMP-CRIT-1.
      - r_arm_status="passive_kinematic_hold" meta attr.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    n_success = sum(1 for d in demos if d["success"])

    with h5py.File(output_path, "w") as f:
        meta = f.create_group("metadata")
        meta.attrs["generator"] = "m3_unclamp_v1_envstep"
        meta.attrs["source"] = "m3_unclamp_v1"  # G5 converter schema match
        meta.attrs["unclamp_version"] = UNCLAMP_VERSION
        meta.attrs["architecture"] = UNCLAMP_ARCHITECTURE
        meta.attrs["K_EXEC"] = 1
        meta.attrs["K_MPPI"] = cfg.K
        meta.attrs["H"] = cfg.H
        meta.attrs["replan_interval"] = cfg.replan_interval
        meta.attrs["temperature_lambda"] = cfg.temperature_lambda
        meta.attrs["noise_sigma"] = cfg.noise_sigma
        meta.attrs["noise_correlation"] = cfg.noise_correlation
        meta.attrs["mppi_pos_action_scale"] = cfg.pos_action_scale
        meta.attrs["env_pos_action_scale_override"] = cfg.pos_action_scale
        meta.attrs["m3_cost_scale"] = cfg.m3_cost_scale
        meta.attrs["unclamp_cost_scale"] = cfg.unclamp_cost_scale
        meta.attrs["cable_seated_cost_scale"] = cfg.cable_seated_cost_scale
        meta.attrs["alpha_finger"] = UNCLAMP_ALPHA_FINGER
        meta.attrs["beta_seated"] = UNCLAMP_BETA_SEATED
        meta.attrs["cost_mode"] = cost_mode
        meta.attrs["cost_method"] = (
            UNCLAMP_COST_METHOD_ADDITIVE if cost_mode == "additive" else UNCLAMP_COST_METHOD_MULTIPLICATIVE
        )
        meta.attrs["p_cable_drop"] = P_CABLE_DROP
        meta.attrs["cable_drop_z_margin_m"] = CABLE_DROP_Z_MARGIN_M
        meta.attrs["cable_drop_z_thr_m"] = CABLE_DROP_Z_THR
        meta.attrs["mppi_l_ori_ik_weight"] = cfg.l_ori_ik_weight
        meta.attrs["mppi_r_ori_ik_weight_cfg"] = cfg.r_ori_ik_weight
        meta.attrs["mppi_r_ori_ik_weight_solver"] = IK_SOFT_R_ORI  # HIGH-2 override
        meta.attrs["warm_start_offset_m"] = cfg.warm_start_offset_m
        meta.attrs["mppi_action_dim"] = UNCLAMP_MPPI_ACTION_DIM
        meta.attrs["hdf5_action_dim"] = UNCLAMP_HDF5_ACTION_DIM
        meta.attrs["action_dim"] = UNCLAMP_HDF5_ACTION_DIM  # legacy alias
        meta.attrs["action_layout"] = UNCLAMP_ACTION_LAYOUT
        meta.attrs["quat_convention"] = M3_QUAT_CONVENTION
        meta.attrs["quat_frame"] = M3_QUAT_FRAME
        meta.attrs["quat_semantic"] = M3_QUAT_SEMANTIC
        meta.attrs["mppi_mode"] = mppi_mode
        meta.attrs["success_threshold_m"] = cfg.success_threshold_m
        meta.attrs["success_threshold_rad"] = cfg.success_threshold_rad
        meta.attrs["success_threshold_finger_open_m"] = cfg.success_threshold_finger_open_m
        meta.attrs["finger_half_open_sum_m"] = cfg.finger_half_open_sum_m
        meta.attrs["finger_full_open_sum_m"] = cfg.finger_full_open_sum_m
        meta.attrs["success_eval"] = "finger_fully_open_AND_seated_AND_sustained"
        meta.attrs["k_sustain"] = K_UNCLAMP
        meta.attrs["unclamp_terminal_steps"] = UNCLAMP_TERMINAL_STEPS
        meta.attrs["obs_dim"] = 42
        meta.attrs["n_demos"] = len(demos)
        meta.attrs["n_success"] = n_success
        meta.attrs["r_arm_status"] = "passive_kinematic_hold"  # UNCLAMP-CRIT-1
        if cable_endpoint_mean is not None:
            meta.attrs["cable_endpoint_mean"] = np.asarray(cable_endpoint_mean, dtype=np.float32)

        for i, demo in enumerate(demos):
            g = f.create_group(f"episode_{i}")
            g.create_dataset("action_delta", data=demo["action_delta"])
            g.create_dataset("obs", data=demo["obs"])
            g.create_dataset("left_ee_pos", data=demo["left_ee_pos"])
            g.create_dataset("left_ee_quat", data=demo["left_ee_quat"])
            g.create_dataset("right_ee_pos", data=demo["right_ee_pos"])
            g.create_dataset("right_ee_quat", data=demo["right_ee_quat"])
            g.create_dataset("finger_opening_L", data=demo["finger_opening_L"])
            # UNCLAMP-CRIT-1: R constant dataset for downstream schema compat.
            g.create_dataset("finger_opening_R", data=demo["finger_opening_R"])
            g.create_dataset("dist_pos_left", data=demo["dist_pos_left"])
            g.create_dataset("dist_ori_left", data=demo["dist_ori_left"])
            g.create_dataset("seated_per_step", data=demo["seated_per_step"].astype(np.uint8))
            if demo["cable_pos_seq"].size > 0:
                g.create_dataset("cable_pos_seq", data=demo["cable_pos_seq"], compression="gzip")
            g.attrs["success"] = demo["success"]
            g.attrs["success_step"] = demo["success_step"]
            g.attrs["sustain_count_final"] = demo["sustain_count_final"]
            g.attrs["seated_terminal"] = demo["seated_terminal"]
            g.attrs["steps"] = demo["steps"]

    print(f"[HDF5] Saved {len(demos)} demos ({n_success} success, cost_mode={cost_mode}) -> {output_path}")


def save_run_metrics_unclamp(demos, drifts_per_plan, drifts_per_episode_max, wall_clock_s, cfg, output_dir, cost_mode):
    """Write per-lambda RUN_METRICS.json."""
    rates = compute_unclamp_success_rates(demos, cfg)

    drifts_arr = np.asarray(drifts_per_plan, dtype=np.float64)
    if drifts_arr.size == 0:
        drift_stats = _stats([])
        drift_stats["per_plan"] = []
    else:
        drift_stats = _stats(drifts_arr)
        drift_stats["per_plan"] = drifts_arr.tolist()

    ep_max_arr = np.asarray(drifts_per_episode_max, dtype=np.float64)
    if ep_max_arr.size == 0:
        drift_violation = {
            "threshold_rad": DRIFT_THRESHOLD_RAD,
            "violation_count": 0,
            "total_episodes": 0,
            "violation_rate": 0.0,
        }
    else:
        n_viol = int(np.sum(ep_max_arr > DRIFT_THRESHOLD_RAD))
        n_ep = int(len(ep_max_arr))
        drift_violation = {
            "threshold_rad": DRIFT_THRESHOLD_RAD,
            "violation_count": n_viol,
            "total_episodes": n_ep,
            "violation_rate": n_viol / n_ep if n_ep > 0 else 0.0,
            "per_episode_max": ep_max_arr.tolist(),
        }

    metrics = {
        "schema_version": "v1",
        "unclamp_version": UNCLAMP_VERSION,
        "architecture": UNCLAMP_ARCHITECTURE,
        "lambda": float(cfg.temperature_lambda),
        "n_demos": len(demos),
        "wall_clock_s": float(wall_clock_s),
        "cost_mode": cost_mode,
        UNCLAMP_S1_LABEL: rates["s1"],
        UNCLAMP_S2_LABEL: rates["s2"],
        UNCLAMP_S3_LABEL: rates["s3"],
        "tangent_drift": drift_stats,
        "drift_violation": drift_violation,
        "cost_threshold_m": cfg.success_threshold_m,
        "cost_threshold_rad": cfg.success_threshold_rad,
        "cost_threshold_finger_open_m": cfg.success_threshold_finger_open_m,
        "cost_method": (
            UNCLAMP_COST_METHOD_ADDITIVE if cost_mode == "additive" else UNCLAMP_COST_METHOD_MULTIPLICATIVE
        ),
        "unclamp_cost_scale": cfg.unclamp_cost_scale,
        "cable_seated_cost_scale": cfg.cable_seated_cost_scale,
        "m3_cost_scale": cfg.m3_cost_scale,
        "alpha_finger": UNCLAMP_ALPHA_FINGER,
        "beta_seated": UNCLAMP_BETA_SEATED,
        "p_cable_drop": P_CABLE_DROP,
        "ik_soft_r_ori": IK_SOFT_R_ORI,
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
    parser = argparse.ArgumentParser(
        description=f"MPPI Unclamp demo generator ({UNCLAMP_VERSION}, Option III env.step)"
    )
    parser.add_argument("--device", type=str, default="cuda:0")
    # UNCLAMP-SYS-3: K_MPPI default 128 (Grip G6a-128 stable optimum; PROPOSE had 256).
    parser.add_argument(
        "--world-count",
        type=int,
        default=128,
        help="K_MPPI (K_EXEC fixed=1). Default 128 per Grip G6a stable optimum.",
    )
    parser.add_argument("--n-demos", type=int, default=5)
    parser.add_argument("--max-steps", type=int, default=UNCLAMP_TERMINAL_STEPS)
    parser.add_argument("--single-lambda", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=str, default="data/mppi_demos_m3_unclamp")
    parser.add_argument("--diag-csv", type=str, default="/tmp/mppi_unclamp_metrics.csv")
    parser.add_argument("--no-mppi", action="store_true", help="(stub) disable MPPI — not implemented for Unclamp v1")
    # UNCLAMP-SYS-1: default additive, multiplicative retained for ablation.
    parser.add_argument(
        "--cost-mode",
        choices=["additive", "multiplicative"],
        default="additive",
        help="Cost function form. Default additive (UNCLAMP-SYS-1).",
    )
    # CC6 C1 PARTIAL: keep --sweep (lambda) and --sweep-pos (γ-3c precedent).
    # REMOVED --sweep-unclamp-cost / --sweep-seated-cost — deferred to G7.
    sweep_group = parser.add_mutually_exclusive_group()
    sweep_group.add_argument(
        "--sweep",
        action="store_true",
        help="Run lambda sweep [0.3, 0.5, 1.0] (exclusive with --sweep-pos)",
    )
    sweep_group.add_argument(
        "--sweep-pos",
        action="store_true",
        help="Run pos_action_scale sweep [0.005, 0.010, 0.015] (exclusive with --sweep)",
    )
    parser.add_argument(
        "--pos-scale",
        type=float,
        default=None,
        help="Override cfg.pos_action_scale (default cfg 0.010). Range [0.005, 0.050].",
    )
    # CC6 C3: --s3-threshold default 0.0 (no hard gate); warn if S3 < 60%.
    parser.add_argument(
        "--s3-threshold",
        type=float,
        default=0.0,
        help="S3 gate threshold. Default 0 = no block; warning printed if S3 < 60 percent.",
    )
    args = parser.parse_args()

    if args.pos_scale is not None:
        if args.sweep_pos:
            parser.error("--pos-scale conflicts with --sweep-pos (sweep uses fixed list)")
        if args.pos_scale <= 0:
            parser.error(f"--pos-scale must be > 0 (got {args.pos_scale})")
        if args.pos_scale < 0.005 or args.pos_scale > 0.050:
            parser.error(f"--pos-scale must be in [0.005, 0.050] (got {args.pos_scale})")

    if args.no_mppi:
        raise NotImplementedError("--no-mppi not implemented for Unclamp v1 (cost-structure requires MPPI rollout).")

    wp.init()
    wp.set_device(args.device)

    lambdas = [0.3, 0.5, 1.0] if args.sweep else [args.single_lambda]
    pos_scales = [0.005, 0.010, 0.015] if args.sweep_pos else [args.pos_scale]
    mppi_mode = "on"  # Unclamp v1 always runs MPPI
    if args.sweep_pos:
        sweep_label = "POS-SWEEP"
    elif args.sweep:
        sweep_label = "SWEEP"
    else:
        sweep_label = "SINGLE"

    sweep_results = []
    for lam in lambdas:
        for pos_scale in pos_scales:
            print(f"\n{'=' * 60}")
            pos_label = f"pos={pos_scale}" if pos_scale is not None else "pos=<cfg default>"
            print(f"  {sweep_label} lambda={lam} {pos_label} mode={mppi_mode} cost_mode={args.cost_mode}")
            print(f"{'=' * 60}")

            cfg = get_default_mppi_unclamp_config()
            cfg.temperature_lambda = lam
            cfg.K = args.world_count
            cfg.device = args.device
            if pos_scale is not None:
                cfg.pos_action_scale = pos_scale
            # Re-validate after mutation (dataclass __post_init__ re-invoke).
            cfg.__post_init__()

            print(
                f"[CFG] K={cfg.K} H={cfg.H} replan={cfg.replan_interval} "
                f"pos={cfg.pos_action_scale} m3_cost_scale={cfg.m3_cost_scale:.4f}"
            )

            if args.sweep_pos:
                diag_csv = f"/tmp/mppi_unclamp_sweep_pos{int(round(cfg.pos_action_scale * 1000)):03d}.csv"
            elif args.sweep:
                diag_csv = f"/tmp/mppi_unclamp_sweep_lam{lam}.csv"
            else:
                diag_csv = args.diag_csv

            t0 = time.perf_counter()
            demos, drifts, drifts_per_ep_max, cable_L_list, cable_R_list = mppi_generate_demos_unclamp(
                cfg,
                args.device,
                max_steps=args.max_steps,
                n_demos=args.n_demos,
                seed=args.seed,
                diag_csv_path=diag_csv,
                cost_mode=args.cost_mode,
            )
            elapsed = time.perf_counter() - t0

            # Use groove-nearest cable endpoint mean (diagnostic).
            cable_mean = np.mean(cable_L_list + cable_R_list, axis=0).astype(np.float32) if cable_L_list else None

            if args.sweep_pos:
                h5_name = f"demos_pos{int(round(cfg.pos_action_scale * 1000)):03d}.hdf5"
            elif args.sweep:
                h5_name = f"demos_l{lam}.hdf5"
            else:
                h5_name = "demos_default.hdf5"
            h5_path = os.path.join(args.output_dir, h5_name)
            save_demos_hdf5_unclamp(
                demos,
                cfg,
                h5_path,
                mppi_mode,
                args.cost_mode,
                cable_endpoint_mean=cable_mean,
            )
            metrics = save_run_metrics_unclamp(
                demos,
                drifts,
                drifts_per_ep_max,
                elapsed,
                cfg,
                args.output_dir,
                args.cost_mode,
            )

            n_success = sum(1 for d in demos if d["success"])
            sweep_results.append(
                {
                    "lambda": lam,
                    "pos_action_scale": cfg.pos_action_scale,
                    "n_demos": len(demos),
                    "n_success": n_success,
                    "S1_finger_open": metrics[UNCLAMP_S1_LABEL],
                    "S2_seated": metrics[UNCLAMP_S2_LABEL],
                    "S3_combined": metrics[UNCLAMP_S3_LABEL],
                    "drift_max": metrics["tangent_drift"].get("max", 0.0),
                    "drift_violation_rate": metrics["drift_violation"]["violation_rate"],
                    "wall_clock_s": round(elapsed, 1),
                    "cost_mode": args.cost_mode,
                }
            )

    if args.sweep or args.sweep_pos:
        print(f"\n{'=' * 78}")
        print(f"  Unclamp {'POS-SWEEP' if args.sweep_pos else 'SWEEP'} RESULTS")
        print(f"{'=' * 78}")
        for r in sweep_results:
            print(
                f"  lam={r['lambda']:>4.1f} pos={r['pos_action_scale']:>5.3f} "
                f"demos={r['n_demos']:>3d} succ={r['n_success']:>3d} "
                f"S1={r['S1_finger_open']:>6.1%} S2={r['S2_seated']:>6.1%} "
                f"S3={r['S3_combined']:>6.1%} "
                f"d={math.degrees(r['drift_max']):>5.1f}° t={r['wall_clock_s']:>6.1f}s"
            )
        csv_path = "/tmp/mppi_unclamp_sweep_pos.csv" if args.sweep_pos else "/tmp/mppi_unclamp_sweep.csv"
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(sweep_results[0].keys()))
            w.writeheader()
            w.writerows(sweep_results)
        print(f"  CSV: {csv_path}")

    # CC6 C3: S3 gate is INFORMATIONAL by default (no block).
    if not args.sweep and not args.sweep_pos and len(sweep_results) == 1:
        s3 = sweep_results[0]["S3_combined"]
        drift_v = sweep_results[0]["drift_violation_rate"]
        info_threshold = 0.60  # Phase 0 target (info only)
        s3_low_info = s3 < info_threshold
        drift_fail = drift_v >= DRIFT_VIOLATION_RATE_LIMIT
        hard_gate_fail = s3 < args.s3_threshold
        if hard_gate_fail or drift_fail:
            reasons = []
            if hard_gate_fail:
                reasons.append(f"S3={s3:.1%} < --s3-threshold={args.s3_threshold:.1%}")
            if drift_fail:
                reasons.append(f"drift_violation={drift_v:.1%} >= {DRIFT_VIOLATION_RATE_LIMIT:.0%}")
            print("\n[BLOCKED_FOR_USER] " + " AND ".join(reasons))
            sys.exit(2)
        if s3_low_info:
            print(f"\n[INFO] S3={s3:.1%} < {info_threshold:.0%} Phase 0 target (not a block).")
        else:
            print(f"\n[S3 INFO] S3={s3:.1%} >= {info_threshold:.0%} Phase 0 target.")


if __name__ == "__main__":
    main()
