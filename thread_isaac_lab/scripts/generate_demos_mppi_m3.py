#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MPPI demo trajectory generation on Newton VBD (M3: dual-arm + 12D full pose).

Extends M2 (dual-arm position-only 6D) to full pose (position + orientation) per arm:
left pos(3) + left ori(3 axis-angle) + right pos(3) + right ori(3 axis-angle) = 12D.

Delta from M2:
  I1  action_dim = 12 (M3_ACTION_DIM)
  I2  cost = max(pos_L, pos_R, 0.458*ori_L, 0.458*ori_R) — Method C (success-boundary equivalence)
  I3  MppiIKSolverM3: 5 objectives (L_pos, L_ori, R_pos, R_ori, jlimit)
  I4  warm_start_approach_m3: position + orientation slerp (U5 5-point checklist)
  I5  rollout: action[:3] L_pos, action[3:6] L_ori, action[6:9] R_pos, action[9:12] R_ori (L-first)
  I6  HDF5 output: ee_pose (pos+quat) + action_delta 12D + dist_pos/ori independent + warmup_dist pos/ori
  I7  RUN_METRICS.json writer (save_run_metrics_json): S3 calibration + tangent_drift + drift_violation

3 Quaternion separation (v6.3.2 核心):
  #1 ik_target_quat_L/R_accumulated: IK target (action accumulate, left-mult world frame)
  #2 achieved_ee_quat_L/R: FK read (state body_q per-step), cost input + HDF5 save
  #3 cost_target_quat_L/R_fixed: cable tangent 由来, plan-start 1 回計算 + H 固定 (U3)

Usage:
    cd ~/IsaacLab
    PYTHONPATH=$PYTHONPATH:thread_isaac_lab/scripts:thread_isaac_lab/configs \\
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/generate_demos_mppi_m3.py \\
        --device cuda:0 [--single-lambda 0.3 | --sweep | --no-mppi]

References:
    DEFINE: memory/project_mppi_m3_define.md (v6.3.2)
    Plan:   memory/project_mppi_m3_plan_v2_2.md (v2.2 + minor correction 2026-04-18)
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
from newton._src.sim.ik.ik_common import eval_fk_batched
from newton.ik import (
    IKObjectiveJointLimit,
    IKObjectivePosition,
    IKObjectiveRotation,
    IKSolver,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "configs"))
# envs/__init__.py requires isaaclab.sim (heavy); insert envs dir to bypass
# and direct-import module files (rsl_rl dep still required; verified OK).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "envs"))

from cable_orientation_utils import (
    compute_cable_tangent,  # cable tangent 計算
    compute_hand_quat_for_cable,  # cable tangent → gripper quat
)

# Reuse M2 scene build + common utilities (import, do not duplicate)
from generate_demos_mppi_m2 import (
    DT,
    IK_ITERATIONS,
    IK_STEP_SIZE,
    REPLAN_INTERVAL,
    RIGHT_EE_BODY_OFFSET,
    RL_SIM_SUBSTEPS,
    build_mppi_scene,
    compute_cable_endpoint_pos,
    copy_world0_to_all,
    mppi_weights,
    sample_action_sequences,
    update_kinematic_bodies,
)
from mpc_config import MPPIConfig

# Existing quaternion utilities (plan v2.2 minor correction 2026-04-18).
# envs/__init__.py bypass via sys.path (see top); direct-import sub-modules.
from newton_skill_env_base import (
    axis_angle_to_quat_xyzw as _axis_angle_to_quat_xyzw,  # Env-Refactor 2026-04-21 rename, keep local alias
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
    CABLE_XY_DR_AMPLITUDE,
    FINGER_OPEN_POS,
)
from test_newton_clip_routing import (
    EE_BODY_OFFSET,
    FRANKA_NUM_JOINTS,
    build_fk_model,
)

# =========================================================================
# M3 Module-level constants (DEFINE v6.3.2 I1)
# =========================================================================

M3_ACTION_DIM = 12  # [L_pos(3), L_ori(3), R_pos(3), R_ori(3)]
M3_VERSION = "v6.3.2"
M3_ACTION_LAYOUT = "L-first"
M3_QUAT_CONVENTION = "xyzw"
M3_QUAT_FRAME = "world"
M3_QUAT_SEMANTIC = "achieved_fk"  # HDF5 #2 FK achieved 保存契約
M3_COST_METHOD = "C"  # Method C: max(pos, scale*ori) both arms

# Drift monitoring (DEFINE v6.3.2 [RUN Measurement Items] M1/M2)
DRIFT_THRESHOLD_RAD = 0.05  # tangent drift threshold (~2.86°)
DRIFT_VIOLATION_RATE_LIMIT = 0.30  # >=30% → BLOCKED_FOR_USER (U3 緩和策撤回候補)

# Warm-start parameters (U5 checklist)
WARM_START_OFFSET = 0.12  # [m] stop 120mm short of cable endpoint (M2 継承)
WARM_START_STEPS = 40  # slerp interpolation steps

# Success thresholds (SSOT: mpc_config.py + task_config.py)
_MPPI_POS_THR_M = 0.08  # MPPIConfig.success_threshold_m
_MPPI_ORI_THR_RAD = 0.1745  # MPPIConfig.success_threshold_rad (task_config.py:154 T_ALIGN)

# Cost scale derived from thresholds (success-boundary equivalence, P2 SSOT).
# Runtime compute keeps M3_COST_SCALE in lockstep with threshold changes.
M3_COST_SCALE = _MPPI_POS_THR_M / _MPPI_ORI_THR_RAD  # ≈ 0.458


# =========================================================================
# Local helpers (slerp + FK EE pose reader + cost target computation)
# =========================================================================


def slerp_numpy(q0, q1, alpha):
    """SLERP between unit quaternions (xyzw). Handles double-cover and small-angle lerp fallback.

    Args:
        q0, q1: (4,) unit quaternions [qx, qy, qz, qw]
        alpha:  scalar in [0, 1]

    Returns:
        (4,) unit quaternion
    """
    q0 = np.asarray(q0, dtype=np.float64)
    q1 = np.asarray(q1, dtype=np.float64)
    dot = float(np.dot(q0, q1))
    if dot < 0:
        q1 = -q1
        dot = -dot
    if dot > 0.9995:
        # Small angle: fallback to linear interpolation + renormalize
        r = q0 + alpha * (q1 - q0)
        return (r / np.linalg.norm(r)).astype(np.float32)
    theta = math.acos(max(-1.0, min(1.0, dot)))
    s = math.sin(theta)
    w0 = math.sin((1.0 - alpha) * theta) / s
    w1 = math.sin(alpha * theta) / s
    return (w0 * q0 + w1 * q1).astype(np.float32)


def get_ee_poses_dual(state, info, K):
    """Extract EE (pos, quat) for K worlds from body_q. quat is xyzw world frame.

    Returns:
        (left_pos (K,3), left_quat (K,4)), (right_pos (K,3), right_quat (K,4))

    wp.transform layout: 7 floats = [px, py, pz, qx, qy, qz, qw] (Newton convention).
    """
    bq = state.body_q.numpy()  # (world_body_count, ) wp.transform
    bws = info["bws"]
    lbs = info["left_body_start"]
    rbs = info["right_body_start"]

    # View wp.transform as flat (7,) per body
    flat = bq.view(np.float32).reshape(-1, 7)

    left_pos = np.zeros((K, 3), dtype=np.float32)
    left_quat = np.zeros((K, 4), dtype=np.float32)
    right_pos = np.zeros((K, 3), dtype=np.float32)
    right_quat = np.zeros((K, 4), dtype=np.float32)

    for w in range(K):
        s = bws[w]
        l_idx = s + lbs + EE_BODY_OFFSET
        r_idx = s + rbs + EE_BODY_OFFSET
        left_pos[w] = flat[l_idx, :3]
        left_quat[w] = flat[l_idx, 3:7]
        right_pos[w] = flat[r_idx, :3]
        right_quat[w] = flat[r_idx, 3:7]

    return (left_pos, left_quat), (right_pos, right_quat)


def compute_cost_targets_from_cable(state, info):
    """Compute #3 cost target quaternions from cable tangent at endpoints (world 0).

    Called ONCE at plan-start (U3 mitigation: H-step fixed).

    Returns:
        cost_target_quat_L_fixed: (4,) float32 xyzw
        cost_target_quat_R_fixed: (4,) float32 xyzw
    """
    bq = state.body_q.numpy()
    bws = info["bws"]
    co = info["cable_offset"]
    cpw = info["cable_per_world"]

    flat = bq.view(np.float32).reshape(-1, 7)
    # Cable positions (world 0)
    w0 = bws[0]
    cable_pos_w0 = flat[w0 + co : w0 + co + cpw, :3].copy()

    # Tangent at endpoints (L = seg 0, R = seg last)
    # compute_cable_tangent expects cable positions array + body index
    tangent_L = compute_cable_tangent(cable_pos_w0, 0)
    tangent_R = compute_cable_tangent(cable_pos_w0, cpw - 1)

    # Compute gripper approach quaternion (cable tangent → gripper quat)
    quat_L = compute_hand_quat_for_cable(tangent_L)
    quat_R = compute_hand_quat_for_cable(tangent_R)

    return (
        _normalize_quat_w_positive(np.asarray(quat_L, dtype=np.float32)),
        _normalize_quat_w_positive(np.asarray(quat_R, dtype=np.float32)),
    )


def angular_diff(q1, q2):
    """Angular difference [rad] between two unit quaternions xyzw. Alias of _quat_distance."""
    return _quat_distance(q1, q2)


def compute_success_rates(demos):
    """S1/S2/S3 rates from demos list (pos+ori threshold AND both arms AND)."""
    if not demos:
        return {"s1": 0.0, "s2": 0.0, "s3": 0.0}
    n1 = n2 = n3 = 0
    for d in demos:
        dpl = d["dist_pos_left"]
        dpr = d["dist_pos_right"]
        dol = d["dist_ori_left"]
        dor = d["dist_ori_right"]
        if len(dpl) == 0:
            continue
        pos_ok = dpl[-1] < _MPPI_POS_THR_M and dpr[-1] < _MPPI_POS_THR_M
        ori_ok = dol[-1] < _MPPI_ORI_THR_RAD and dor[-1] < _MPPI_ORI_THR_RAD
        if pos_ok:
            n1 += 1
        if ori_ok:
            n2 += 1
        if pos_ok and ori_ok:
            n3 += 1
    n = len(demos)
    return {"s1": n1 / n, "s2": n2 / n, "s3": n3 / n}


def _stats(arr):
    """Summary stats for numeric array. Returns 0-filled dict if empty."""
    a = np.asarray(arr, dtype=np.float64)
    if a.size == 0:
        return {k: 0.0 for k in ["mean", "std", "max", "min", "p95"]}
    return {
        "mean": float(a.mean()),
        "std": float(a.std()),
        "max": float(a.max()),
        "min": float(a.min()),
        "p95": float(np.percentile(a, 95)),
    }


# =========================================================================
# MppiIKSolverM3 class (canonical; F2 smoke test moved here per refactor checklist)
# =========================================================================


class MppiIKSolverM3:
    """Batched IK for M3 MPPI (dual arm, position + orientation, n_problems=K).

    5 objectives: L_pos + L_ori + R_pos + R_ori + jlimit.

    Attributes (F2 smoke test references these names; do not rename):
        obj_L_pos, obj_L_ori, obj_R_pos, obj_R_ori, obj_jlimit
    """

    def __init__(self, fk_model, K, device, l_ori_weight=0.5, r_ori_weight=0.5):
        """Args:
            l_ori_weight: IK objective weight for L arm orientation (default 0.5).
                Phase 0 (2026-04-21) R2 sweep values: 0.75 / 1.0 / 1.5.
            r_ori_weight: IK objective weight for R arm orientation (default 0.5).
                Phase 0 sweep values same as l_ori_weight.
        """
        self.fk_model = fk_model
        self.K = K
        self.device = device

        self.obj_L_pos = IKObjectivePosition(
            link_index=EE_BODY_OFFSET,
            link_offset=wp.vec3(0, 0, 0),
            target_positions=wp.zeros(K, dtype=wp.vec3, device=device),
            weight=1.0,
        )
        self.obj_L_ori = IKObjectiveRotation(
            link_index=EE_BODY_OFFSET,
            link_offset_rotation=wp.quat_identity(),
            target_rotations=wp.zeros(K, dtype=wp.vec4, device=device),
            weight=l_ori_weight,
        )
        self.obj_R_pos = IKObjectivePosition(
            link_index=RIGHT_EE_BODY_OFFSET,
            link_offset=wp.vec3(0, 0, 0),
            target_positions=wp.zeros(K, dtype=wp.vec3, device=device),
            weight=1.0,
        )
        self.obj_R_ori = IKObjectiveRotation(
            link_index=RIGHT_EE_BODY_OFFSET,
            link_offset_rotation=wp.quat_identity(),
            target_rotations=wp.zeros(K, dtype=wp.vec4, device=device),
            weight=r_ori_weight,
        )
        self.obj_jlimit = IKObjectiveJointLimit(
            joint_limit_lower=fk_model.joint_limit_lower,
            joint_limit_upper=fk_model.joint_limit_upper,
            weight=10.0,
        )

        self.solver = IKSolver(
            fk_model,
            n_problems=K,
            objectives=[
                self.obj_L_pos,
                self.obj_L_ori,
                self.obj_R_pos,
                self.obj_R_ori,
                self.obj_jlimit,
            ],
        )

        coord_count = fk_model.joint_coord_count
        self.jq_in = wp.zeros((K, coord_count), dtype=float, device=device)
        self.jq_out = wp.zeros((K, coord_count), dtype=float, device=device)

        dof_count = fk_model.joint_dof_count
        body_count = fk_model.body_count
        self.batch_fk_jq = wp.zeros((K, coord_count), dtype=float, device=device)
        self.batch_fk_jqd = wp.zeros((K, dof_count), dtype=float, device=device)
        self.batch_fk_body_q = wp.zeros((K, body_count), dtype=wp.transform, device=device)
        self.batch_fk_body_qd = wp.zeros((K, body_count), dtype=wp.spatial_vector, device=device)

    def solve(self, target_L_pos, target_L_quat, target_R_pos, target_R_quat, jq_starts):
        """Solve 5-obj IK for K problems.

        Args:
            target_L_pos:  (K, 3) np.float32 left EE target position
            target_L_quat: (K, 4) np.float32 left EE target quat xyzw (#1 IK target accumulated)
            target_R_pos:  (K, 3) np.float32 right EE target position
            target_R_quat: (K, 4) np.float32 right EE target quat xyzw (#1 IK target accumulated)
            jq_starts:     (K, coord_count) initial joint positions

        Returns:
            (K, coord_count) solved joint positions (numpy)
        """
        self.obj_L_pos.set_target_positions(
            wp.array(target_L_pos.astype(np.float32), dtype=wp.vec3, device=self.device)
        )
        self.obj_L_ori.set_target_rotations(
            wp.array(target_L_quat.astype(np.float32), dtype=wp.vec4, device=self.device)
        )
        self.obj_R_pos.set_target_positions(
            wp.array(target_R_pos.astype(np.float32), dtype=wp.vec3, device=self.device)
        )
        self.obj_R_ori.set_target_rotations(
            wp.array(target_R_quat.astype(np.float32), dtype=wp.vec4, device=self.device)
        )
        self.jq_in.assign(jq_starts.astype(np.float64))
        self.solver.step(self.jq_in, self.jq_out, iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)
        return self.jq_out.numpy()

    def eval_fk_batch(self, jq_np):
        """Evaluate FK for K joint configs. Returns (K, body_count) body transforms."""
        self.batch_fk_jq.assign(jq_np.astype(np.float64))
        eval_fk_batched(
            self.fk_model,
            self.batch_fk_jq,
            self.batch_fk_jqd,
            self.batch_fk_body_q,
            self.batch_fk_body_qd,
        )
        return self.batch_fk_body_q.numpy()


# =========================================================================
# C.2  Rollout + cost — M3 12D + 3 quat separation
#      (stub for now; full implementation in next coding session)
# =========================================================================


def rollout_and_cost_m3(
    model,
    solver_vbd,
    state_0,
    state_1,
    control,
    actions_seq,
    ik_solver,
    per_world_jq,
    info,
    K,
    H,
    cfg,
    cost_target_quat_L_fixed,
    cost_target_quat_R_fixed,
    ik_target_quat_L_init,
    ik_target_quat_R_init,
):
    """Rollout K trajectories for H steps with 12D actions + 3 quat separation.

    Cost = max(pos_L, pos_R, 0.458*ori_L, 0.458*ori_R) per step, accumulated.
    #1 IK target: per-step left-multiply accumulation (world frame axis-angle delta).
    #2 achieved FK quat: state.body_q per-step read (cost input).
    #3 cost target: fixed throughout H (passed as args; U3 mitigation).

    State save/restore is the caller's responsibility (M2 pattern). Drift is
    measured in-function between entry state_0 (plan start) and exit state_0
    (plan end, post-H physics steps).

    Returns:
        costs: (K,) float32 accumulated cost
        n_nan: int
        t_ik_total, t_physics_total: timings
        ee_spread_max: diagnostic
        drift_L, drift_R: float — tangent angular diff at plan start vs end (world 0)
    """
    sim_dt = DT / RL_SIM_SUBSTEPS
    costs = np.zeros(K, dtype=np.float32)
    jq = per_world_jq.copy()
    t_ik_total = 0.0
    t_physics_total = 0.0
    nan_mask = np.zeros(K, dtype=bool)
    ee_spread_max_left = 0.0
    ee_spread_max_right = 0.0

    bws = info["bws"]
    co = info["cable_offset"]
    cpw = info["cable_per_world"]
    bpw = info["bodies_per_world"]
    w0 = bws[0]

    # M1 drift: cable tangent at plan start (world 0)
    bq_start = state_0.body_q.numpy()
    flat_start = bq_start.view(np.float32).reshape(-1, 7)
    cable_pos_w0_start = flat_start[w0 + co : w0 + co + cpw, :3].copy()
    tangent_L_start = compute_cable_tangent(cable_pos_w0_start, 0)
    tangent_R_start = compute_cable_tangent(cable_pos_w0_start, cpw - 1)

    # #1 IK target init (tile warm-start end state, (K, 4) xyzw float32)
    ik_tgt_L = np.tile(ik_target_quat_L_init[None].astype(np.float32), (K, 1))
    ik_tgt_R = np.tile(ik_target_quat_R_init[None].astype(np.float32), (K, 1))

    # #3 cost target: tile to (K, 4) for element-wise _quat_distance
    ct_L = cost_target_quat_L_fixed.astype(np.float32)
    ct_R = cost_target_quat_R_fixed.astype(np.float32)

    for h in range(H):
        # Current EE pos (pos delta accumulation reference)
        (left_ee, _), (right_ee, _) = get_ee_poses_dual(state_0, info, K)

        # I5: split 12D action into 4 components (L-first)
        L_pos_delta = actions_seq[:, h, 0:3] * cfg.pos_action_scale
        L_ori_delta = actions_seq[:, h, 3:6] * cfg.rot_action_scale  # world frame
        R_pos_delta = actions_seq[:, h, 6:9] * cfg.pos_action_scale
        R_ori_delta = actions_seq[:, h, 9:12] * cfg.rot_action_scale

        target_L_pos = left_ee + L_pos_delta
        target_R_pos = right_ee + R_pos_delta

        # #1 accumulate IK target (left-multiply, world frame; unit-norm maintained)
        for k in range(K):
            q_dL = _axis_angle_to_quat_xyzw(L_ori_delta[k])
            ik_tgt_L[k] = _quat_multiply_xyzw(q_dL, ik_tgt_L[k])
            ik_tgt_L[k] = ik_tgt_L[k] / np.linalg.norm(ik_tgt_L[k])
            q_dR = _axis_angle_to_quat_xyzw(R_ori_delta[k])
            ik_tgt_R[k] = _quat_multiply_xyzw(q_dR, ik_tgt_R[k])
            ik_tgt_R[k] = ik_tgt_R[k] / np.linalg.norm(ik_tgt_R[k])

        # I3: 5-obj IK solve (per-step set_target_rotations, E5)
        t0_ik = time.perf_counter()
        jq_solved = ik_solver.solve(target_L_pos, ik_tgt_L, target_R_pos, ik_tgt_R, jq)

        # Keep fingers open (both arms)
        jq_solved[:, 7] = FINGER_OPEN_POS
        jq_solved[:, 8] = FINGER_OPEN_POS
        jq_solved[:, FRANKA_NUM_JOINTS + 7] = FINGER_OPEN_POS
        jq_solved[:, FRANKA_NUM_JOINTS + 8] = FINGER_OPEN_POS

        fk_body_q = ik_solver.eval_fk_batch(jq_solved)
        t_ik_total += time.perf_counter() - t0_ik

        update_kinematic_bodies(state_0, fk_body_q, info, K)

        # EE spread diagnostic (both arms, K-world variance)
        (ik_left, _), (ik_right, _) = get_ee_poses_dual(state_0, info, K)
        valid_idx = ~nan_mask
        if valid_idx.sum() > 1:
            ee_spread_max_left = max(ee_spread_max_left, float(np.sqrt(np.sum(np.var(ik_left[valid_idx], axis=0)))))
            ee_spread_max_right = max(ee_spread_max_right, float(np.sqrt(np.sum(np.var(ik_right[valid_idx], axis=0)))))

        # Physics step (RL_SIM_SUBSTEPS substeps, VBD)
        t0_phys = time.perf_counter()
        contacts = model.collide(state_0)
        for _ in range(RL_SIM_SUBSTEPS):
            solver_vbd.step(state_0, state_1, control, contacts, sim_dt)
            state_0, state_1 = state_1, state_0
        t_physics_total += time.perf_counter() - t0_phys

        # NaN check per world
        bq_check = state_0.body_q.numpy()
        for w in range(K):
            if not nan_mask[w]:
                s = bws[w]
                chunk = bq_check[s : s + bpw]
                if np.any(np.isnan(chunk)) or np.any(np.isinf(chunk)):
                    nan_mask[w] = True
                    costs[w] = 1e6
        if h == 0 and np.any(nan_mask):
            n_nan_h0 = int(nan_mask.sum())
            print(f"  [WARN] {n_nan_h0}/{K} worlds NaN at h=0")

        # #2 Achieved FK (post-physics): state.body_q per-step read
        (achieved_pos_L, achieved_quat_L), (achieved_pos_R, achieved_quat_R) = get_ee_poses_dual(state_0, info, K)

        cable_left_ep, cable_right_ep = compute_cable_endpoint_pos(state_0, info, K)

        # Method C cost = max(pos_L, pos_R, 0.458*ori_L, 0.458*ori_R)
        pos_dist_L = np.linalg.norm(achieved_pos_L - cable_left_ep, axis=1)
        pos_dist_R = np.linalg.norm(achieved_pos_R - cable_right_ep, axis=1)
        ori_dist_L = np.zeros(K, dtype=np.float32)
        ori_dist_R = np.zeros(K, dtype=np.float32)
        for k in range(K):
            # #2 vs #3 fixed (normalize #2, #3 already normalized by caller)
            q2_L = _normalize_quat_w_positive(achieved_quat_L[k])
            q2_R = _normalize_quat_w_positive(achieved_quat_R[k])
            ori_dist_L[k] = _quat_distance(q2_L, ct_L)
            ori_dist_R[k] = _quat_distance(q2_R, ct_R)

        step_cost = np.maximum.reduce(
            [
                pos_dist_L,
                pos_dist_R,
                M3_COST_SCALE * ori_dist_L,
                M3_COST_SCALE * ori_dist_R,
            ]
        ).astype(np.float32)
        costs += np.where(nan_mask, 0.0, step_cost)

        jq = jq_solved.copy()

    # M1 drift at plan end (world 0)
    bq_end = state_0.body_q.numpy()
    flat_end = bq_end.view(np.float32).reshape(-1, 7)
    cable_pos_w0_end = flat_end[w0 + co : w0 + co + cpw, :3].copy()
    tangent_L_end = compute_cable_tangent(cable_pos_w0_end, 0)
    tangent_R_end = compute_cable_tangent(cable_pos_w0_end, cpw - 1)

    dot_L = float(np.clip(np.dot(tangent_L_start, tangent_L_end), -1.0, 1.0))
    dot_R = float(np.clip(np.dot(tangent_R_start, tangent_R_end), -1.0, 1.0))
    drift_L = float(math.acos(dot_L))
    drift_R = float(math.acos(dot_R))

    n_nan = int(nan_mask.sum())
    if n_nan > 0:
        print(f"  [NaN] {n_nan}/{K} worlds had NaN ({n_nan * 100 // K}%)")
    ee_spread_max = max(ee_spread_max_left, ee_spread_max_right)

    return (costs, n_nan, t_ik_total, t_physics_total, ee_spread_max, drift_L, drift_R)


# =========================================================================
# C.5  Warm-start (M3 pos + ori slerp, U5 checklist)
# =========================================================================


def warm_start_approach_m3(
    model, solver_vbd, state_0, state_1, control, ik_solver, info, K, fk_jq, coord_count, device
):
    """Scripted dual-arm pos + ori warm-start (U5 5-point checklist).

    (a) start_quat: FK read at warm-start start (world 0)
    (b) target_quat (= #3 cost target): cable tangent 1-shot compute at plan start
    (c) 40-step slerp interpolation, per-step IK
    (d) K tile + float32 cast
    (e) target_quat fixed (not recomputed)

    Returns:
        per_world_jq, cost_target_quat_L_fixed, cost_target_quat_R_fixed,
        ik_target_quat_L_init, ik_target_quat_R_init,
        warmup_dist_pos_L, warmup_dist_pos_R, warmup_dist_ori_L, warmup_dist_ori_R,
        warmup_steps
    """
    sim_dt = DT / RL_SIM_SUBSTEPS

    # (a) start pose FK read (world 0, K=1)
    (left_start_pos, left_start_quat), (right_start_pos, right_start_quat) = get_ee_poses_dual(state_0, info, 1)
    left_start_pos = left_start_pos[0]
    right_start_pos = right_start_pos[0]
    start_quat_L = _normalize_quat_w_positive(left_start_quat[0])
    start_quat_R = _normalize_quat_w_positive(right_start_quat[0])

    # (b) #3 cost target: cable tangent 1-shot compute (U3 mitigation)
    cost_target_quat_L_fixed, cost_target_quat_R_fixed = compute_cost_targets_from_cable(state_0, info)

    # Pos target: offset from cable endpoints (M2 pattern)
    cable_left, cable_right = compute_cable_endpoint_pos(state_0, info, 1)
    cable_left = cable_left[0]
    cable_right = cable_right[0]
    dir_L = cable_left - left_start_pos
    dir_R = cable_right - right_start_pos
    dist_pos_L_init = float(np.linalg.norm(dir_L))
    dist_pos_R_init = float(np.linalg.norm(dir_R))

    # Skip if already within offset (degenerate case)
    if dist_pos_L_init < WARM_START_OFFSET and dist_pos_R_init < WARM_START_OFFSET:
        print(f"  [WARM-M3] Already within offset (L={dist_pos_L_init:.3f}m, R={dist_pos_R_init:.3f}m) — skip")
        per_world_jq = np.tile(fk_jq[:coord_count], (K, 1))
        d_ori_L = float(_quat_distance(start_quat_L, cost_target_quat_L_fixed))
        d_ori_R = float(_quat_distance(start_quat_R, cost_target_quat_R_fixed))
        return (
            per_world_jq,
            cost_target_quat_L_fixed,
            cost_target_quat_R_fixed,
            start_quat_L.copy(),
            start_quat_R.copy(),
            dist_pos_L_init,
            dist_pos_R_init,
            d_ori_L,
            d_ori_R,
            0,
        )

    target_L_pos = left_start_pos + dir_L / dist_pos_L_init * (dist_pos_L_init - WARM_START_OFFSET)
    target_R_pos = right_start_pos + dir_R / dist_pos_R_init * (dist_pos_R_init - WARM_START_OFFSET)

    per_world_jq = np.tile(fk_jq[:coord_count], (K, 1))

    print(f"  [WARM-M3] L pos {left_start_pos}→{target_L_pos} dist {dist_pos_L_init:.3f}m→{WARM_START_OFFSET:.3f}m")
    print(f"  [WARM-M3] R pos {right_start_pos}→{target_R_pos} dist {dist_pos_R_init:.3f}m→{WARM_START_OFFSET:.3f}m")
    print(f"  [WARM-M3] quat slerp L/R to cable-tangent targets, {WARM_START_STEPS} steps")

    # (c) 40-step slerp loop + per-step IK
    for s in range(WARM_START_STEPS):
        alpha = (s + 1) / WARM_START_STEPS

        # Pos lerp
        ee_L_interp = left_start_pos + (target_L_pos - left_start_pos) * alpha
        ee_R_interp = right_start_pos + (target_R_pos - right_start_pos) * alpha

        # Ori slerp (target fixed = #3 cost target, U3 mitigation)
        quat_L_interp = _normalize_quat_w_positive(slerp_numpy(start_quat_L, cost_target_quat_L_fixed, alpha))
        quat_R_interp = _normalize_quat_w_positive(slerp_numpy(start_quat_R, cost_target_quat_R_fixed, alpha))

        # (d) K tile + float32
        tgt_L_pos_all = np.tile(ee_L_interp[None].astype(np.float32), (K, 1))
        tgt_R_pos_all = np.tile(ee_R_interp[None].astype(np.float32), (K, 1))
        tgt_L_quat_all = np.tile(quat_L_interp[None].astype(np.float32), (K, 1))
        tgt_R_quat_all = np.tile(quat_R_interp[None].astype(np.float32), (K, 1))

        jq_solved = ik_solver.solve(tgt_L_pos_all, tgt_L_quat_all, tgt_R_pos_all, tgt_R_quat_all, per_world_jq)
        jq_solved[:, 7] = FINGER_OPEN_POS
        jq_solved[:, 8] = FINGER_OPEN_POS
        jq_solved[:, FRANKA_NUM_JOINTS + 7] = FINGER_OPEN_POS
        jq_solved[:, FRANKA_NUM_JOINTS + 8] = FINGER_OPEN_POS

        fk_body_q = ik_solver.eval_fk_batch(jq_solved)
        update_kinematic_bodies(state_0, fk_body_q, info, K)

        contacts = model.collide(state_0)
        for _ in range(RL_SIM_SUBSTEPS):
            solver_vbd.step(state_0, state_1, control, contacts, sim_dt)
            state_0, state_1 = state_1, state_0

        per_world_jq[:] = jq_solved
        solver_vbd.body_q_prev = wp.clone(state_0.body_q)

    # End-of-warm-start measurements (world 0)
    (final_L_pos, final_L_quat), (final_R_pos, final_R_quat) = get_ee_poses_dual(state_0, info, 1)
    cable_L_final, cable_R_final = compute_cable_endpoint_pos(state_0, info, 1)

    warmup_dist_pos_L = float(np.linalg.norm(final_L_pos[0] - cable_L_final[0]))
    warmup_dist_pos_R = float(np.linalg.norm(final_R_pos[0] - cable_R_final[0]))
    final_qL = _normalize_quat_w_positive(final_L_quat[0])
    final_qR = _normalize_quat_w_positive(final_R_quat[0])
    warmup_dist_ori_L = float(_quat_distance(final_qL, cost_target_quat_L_fixed))
    warmup_dist_ori_R = float(_quat_distance(final_qR, cost_target_quat_R_fixed))

    # #1 IK target init = warm-start end (slerp completed to #3)
    ik_target_quat_L_init = cost_target_quat_L_fixed.copy()
    ik_target_quat_R_init = cost_target_quat_R_fixed.copy()

    print(
        f"  [WARM-M3] Done. pos L={warmup_dist_pos_L:.4f}m "
        f"R={warmup_dist_pos_R:.4f}m  "
        f"ori L={math.degrees(warmup_dist_ori_L):.2f}° "
        f"R={math.degrees(warmup_dist_ori_R):.2f}°"
    )

    return (
        per_world_jq,
        cost_target_quat_L_fixed,
        cost_target_quat_R_fixed,
        ik_target_quat_L_init,
        ik_target_quat_R_init,
        warmup_dist_pos_L,
        warmup_dist_pos_R,
        warmup_dist_ori_L,
        warmup_dist_ori_R,
        WARM_START_STEPS,
    )


# =========================================================================
# C.6  Main MPPI loop — M3 (stub)
# =========================================================================


def mppi_generate_demos_m3(
    cfg,
    device,
    max_steps=128,
    n_demos=5,
    seed=42,
    no_warmstart=False,
    no_mppi=False,
    diag_csv_path="/tmp/mppi_m3_metrics.csv",
    l_ori_weight=0.5,
    r_ori_weight=0.5,
    randomize_cable_xy: bool = False,
):
    """Generate M3 bimanual_reach demos with 12D MPPI + 3 quat separation.

    Returns:
        demos: list of per-episode dicts with pos+quat trajectories
        drifts_per_plan_LR: list of [drift_L, drift_R] per MPPI plan (all episodes)
    """
    K = cfg.K
    H = cfg.H

    rng = np.random.default_rng(seed)

    print(f"\n[MPPI-M3] {M3_VERSION} Building scene K={K} (dual-arm + ori)...")
    fk_model = build_fk_model(device=device)
    fk_state = fk_model.state()
    fk_jq = fk_state.joint_q.numpy()
    fk_tp = fk_model.joint_target_pos.numpy()
    fk_jq[:] = fk_tp[:]
    fk_jq[7] = FINGER_OPEN_POS
    fk_jq[8] = FINGER_OPEN_POS
    fk_jq[FRANKA_NUM_JOINTS + 7] = FINGER_OPEN_POS
    fk_jq[FRANKA_NUM_JOINTS + 8] = FINGER_OPEN_POS
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    model, solver_vbd, info = build_mppi_scene(fk_model, fk_state, K, device)
    ik_solver = MppiIKSolverM3(fk_model, K, device, l_ori_weight=l_ori_weight, r_ori_weight=r_ori_weight)

    state_0 = model.state()
    state_1 = model.state()
    control = model.control()

    coord_count = fk_model.joint_coord_count

    init_body_q = state_0.body_q.numpy().copy()
    init_body_qd = state_0.body_qd.numpy().copy()

    demos = []
    drifts_per_plan_LR = []
    drifts_per_episode_max = []  # (n_demos,): max(drift_L, drift_R) over all plans in episode
    cable_endpoints_L = []  # (n_demos, 3) cable seg 0 at episode reset
    cable_endpoints_R = []  # (n_demos, 3) cable seg last at episode reset

    diag_file = open(diag_csv_path, "w", newline="")  # noqa: SIM115
    diag_csv = csv.writer(diag_file)
    diag_csv.writerow(
        [
            "episode",
            "step",
            "nan_count",
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
        ]
    )
    print(f"[DIAG] CSV → {diag_csv_path}")

    for ep in range(n_demos):
        print(f"\n[MPPI-M3] Episode {ep + 1}/{n_demos}")

        # Option C' (2026-04-25): per-episode cable XY domain randomization.
        # Each of K worlds receives an independent uniform noise draw in
        # ±CABLE_XY_DR_AMPLITUDE applied to all cable body positions
        # (uniform translate preserves cable shape). noise applied to
        # init_body_q_ep copy BEFORE state_0.body_q.assign so downstream
        # compute_cost_targets_from_cable + warm_start read noised cable state.
        init_body_q_ep = init_body_q.copy()
        if randomize_cable_xy:
            amp_x, amp_y = CABLE_XY_DR_AMPLITUDE
            co = info["cable_offset"]
            cpw = info["cable_per_world"]
            bpw = info["bodies_per_world"]
            for w in range(K):
                world_start = w * bpw
                cable_body_indices_w = list(range(
                    world_start + co,
                    world_start + co + cpw,
                ))
                noise_xy = np.random.uniform(
                    low=(-amp_x, -amp_y),
                    high=(amp_x, amp_y),
                    size=2,
                )
                init_body_q_ep[cable_body_indices_w, 0] += noise_xy[0]
                init_body_q_ep[cable_body_indices_w, 1] += noise_xy[1]

        state_0.body_q.assign(init_body_q_ep)
        state_0.body_qd.assign(init_body_qd)
        solver_vbd.body_q_prev = wp.clone(state_0.body_q)

        # Record cable endpoints at episode reset (Test 7 L/R geometric consistency)
        cable_ep_L_reset, cable_ep_R_reset = compute_cable_endpoint_pos(state_0, info, 1)
        cable_endpoints_L.append(cable_ep_L_reset[0].astype(np.float32).copy())
        cable_endpoints_R.append(cable_ep_R_reset[0].astype(np.float32).copy())

        if no_warmstart:
            per_world_jq = np.tile(fk_jq[:coord_count], (K, 1))
            (left_ee0, left_q0), (right_ee0, right_q0) = get_ee_poses_dual(state_0, info, 1)
            cost_target_quat_L_fixed, cost_target_quat_R_fixed = compute_cost_targets_from_cable(state_0, info)
            cable_l0, cable_r0 = compute_cable_endpoint_pos(state_0, info, 1)
            warmup_dist_pos_L = float(np.linalg.norm(left_ee0[0] - cable_l0[0]))
            warmup_dist_pos_R = float(np.linalg.norm(right_ee0[0] - cable_r0[0]))
            ql0 = _normalize_quat_w_positive(left_q0[0])
            qr0 = _normalize_quat_w_positive(right_q0[0])
            warmup_dist_ori_L = float(_quat_distance(ql0, cost_target_quat_L_fixed))
            warmup_dist_ori_R = float(_quat_distance(qr0, cost_target_quat_R_fixed))
            ik_target_quat_L = ql0.copy()
            ik_target_quat_R = qr0.copy()
            warmup_steps = 0
            print(
                f"  [WARM-M3] SKIPPED: "
                f"pos L={warmup_dist_pos_L:.3f}m R={warmup_dist_pos_R:.3f}m "
                f"ori L={math.degrees(warmup_dist_ori_L):.1f}° "
                f"R={math.degrees(warmup_dist_ori_R):.1f}°"
            )
        else:
            (
                per_world_jq,
                cost_target_quat_L_fixed,
                cost_target_quat_R_fixed,
                ik_target_quat_L,
                ik_target_quat_R,
                warmup_dist_pos_L,
                warmup_dist_pos_R,
                warmup_dist_ori_L,
                warmup_dist_ori_R,
                warmup_steps,
            ) = warm_start_approach_m3(
                model, solver_vbd, state_0, state_1, control, ik_solver, info, K, fk_jq, coord_count, device
            )

        traj_left_pos = []
        traj_right_pos = []
        traj_left_quat = []
        traj_right_quat = []
        traj_actions = []
        traj_dist_pos_L = []
        traj_dist_pos_R = []
        traj_dist_ori_L = []
        traj_dist_ori_R = []
        traj_cable_pos = []  # AR-compat: full cable body positions per step [(T, cpw, 3)]
        drifts_L_ep = []
        drifts_R_ep = []

        step = 0
        success = False

        if no_mppi:
            # η: MPPI OFF branch — warm-start end state eval only
            (left_ee, left_quat), (right_ee, right_quat) = get_ee_poses_dual(state_0, info, 1)
            cable_l, cable_r = compute_cable_endpoint_pos(state_0, info, 1)
            dpl = float(np.linalg.norm(left_ee[0] - cable_l[0]))
            dpr = float(np.linalg.norm(right_ee[0] - cable_r[0]))
            ql = _normalize_quat_w_positive(left_quat[0])
            qr = _normalize_quat_w_positive(right_quat[0])
            dol = float(_quat_distance(ql, cost_target_quat_L_fixed))
            dor = float(_quat_distance(qr, cost_target_quat_R_fixed))
            traj_left_pos.append(left_ee[0].copy())
            traj_right_pos.append(right_ee[0].copy())
            traj_left_quat.append(ql)
            traj_right_quat.append(qr)
            traj_actions.append(np.zeros(M3_ACTION_DIM, dtype=np.float32))
            traj_dist_pos_L.append(dpl)
            traj_dist_pos_R.append(dpr)
            traj_dist_ori_L.append(dol)
            traj_dist_ori_R.append(dor)
            step = 1
            success = (
                dpl < cfg.success_threshold_m
                and dpr < cfg.success_threshold_m
                and dol < _MPPI_ORI_THR_RAD
                and dor < _MPPI_ORI_THR_RAD
            )
            print(
                f"  [NO-MPPI-M3] pos L={dpl:.4f}m R={dpr:.4f}m "
                f"ori L={math.degrees(dol):.1f}° R={math.degrees(dor):.1f}° "
                f"success={success}"
            )

        while not no_mppi and step < max_steps:
            copy_world0_to_all(state_0, info["bws"], info["bodies_per_world"], K, device, solver_vbd=solver_vbd)
            per_world_jq[:] = per_world_jq[0:1]

            # Save state + IK target for restore after rollout
            saved_q = state_0.body_q.numpy().copy()
            saved_qd = state_0.body_qd.numpy().copy()
            saved_bq_prev = solver_vbd.body_q_prev.numpy().copy()
            saved_jq = per_world_jq.copy()
            saved_ik_tgt_L = ik_target_quat_L.copy()
            saved_ik_tgt_R = ik_target_quat_R.copy()

            # Sample K action sequences (12D)
            actions = sample_action_sequences(K, H, M3_ACTION_DIM, cfg.noise_sigma, cfg.noise_correlation, rng)

            t0_plan = time.perf_counter()
            (costs, nan_count, t_ik, t_phys, ee_spread_max, drift_L, drift_R) = rollout_and_cost_m3(
                model,
                solver_vbd,
                state_0,
                state_1,
                control,
                actions,
                ik_solver,
                per_world_jq,
                info,
                K,
                H,
                cfg,
                cost_target_quat_L_fixed,
                cost_target_quat_R_fixed,
                ik_target_quat_L,
                ik_target_quat_R,
            )
            t_plan = time.perf_counter() - t0_plan
            drifts_L_ep.append(drift_L)
            drifts_R_ep.append(drift_R)
            if step == 0:
                print(
                    f"  [TIMING] plan={t_plan:.2f}s "
                    f"(IK={t_ik:.2f}s, physics={t_phys:.2f}s, "
                    f"other={t_plan - t_ik - t_phys:.2f}s)  "
                    f"drift L={math.degrees(drift_L):.2f}° "
                    f"R={math.degrees(drift_R):.2f}°"
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
            diag_csv.writerow(
                [
                    ep,
                    step,
                    nan_count,
                    k_eff,
                    f"{w_entropy:.4f}",
                    f"{w_mass_valid:.6f}",
                    f"{top1_w:.6f}",
                    int(ba_has_nan),
                    f"{t_plan:.3f}",
                    f"{c_min:.4f}",
                    f"{c_max:.4f}",
                    f"{c_range:.4f}",
                    f"{c_std:.4f}",
                    f"{ee_spread_max * 1000:.2f}",
                    f"{drift_L:.4f}",
                    f"{drift_R:.4f}",
                ]
            )
            if step % 16 == 0:
                print(
                    f"  [DIAG] step={step} nan={nan_count}/{K} "
                    f"k_eff={k_eff} entropy={w_entropy:.2f} "
                    f"mass={w_mass_valid:.4f} top1={top1_w:.4f} "
                    f"ba_nan={ba_has_nan} cost_range={c_range:.4f} "
                    f"drift L={math.degrees(drift_L):.2f}° "
                    f"R={math.degrees(drift_R):.2f}°"
                )

            # Restore state for execute
            state_0.body_q.assign(saved_q)
            state_0.body_qd.assign(saved_qd)
            solver_vbd.body_q_prev.assign(saved_bq_prev)
            per_world_jq = saved_jq.copy()
            ik_target_quat_L = saved_ik_tgt_L.copy()
            ik_target_quat_R = saved_ik_tgt_R.copy()

            # Execute first REPLAN_INTERVAL steps on world 0
            n_exec = min(REPLAN_INTERVAL, max_steps - step)
            sim_dt = DT / RL_SIM_SUBSTEPS

            for h in range(n_exec):
                (left_ee_now, _), (right_ee_now, _) = get_ee_poses_dual(state_0, info, 1)

                # I5: 12D split (L-first)
                L_pos_delta = best_actions[h, 0:3] * cfg.pos_action_scale
                L_ori_delta = best_actions[h, 3:6] * cfg.rot_action_scale
                R_pos_delta = best_actions[h, 6:9] * cfg.pos_action_scale
                R_ori_delta = best_actions[h, 9:12] * cfg.rot_action_scale

                target_L_pos = left_ee_now[0] + L_pos_delta
                target_R_pos = right_ee_now[0] + R_pos_delta

                # #1 IK target accumulate (left-multiply, world frame)
                q_dL = _axis_angle_to_quat_xyzw(L_ori_delta)
                ik_target_quat_L = _quat_multiply_xyzw(q_dL, ik_target_quat_L)
                ik_target_quat_L = ik_target_quat_L / np.linalg.norm(ik_target_quat_L)
                q_dR = _axis_angle_to_quat_xyzw(R_ori_delta)
                ik_target_quat_R = _quat_multiply_xyzw(q_dR, ik_target_quat_R)
                ik_target_quat_R = ik_target_quat_R / np.linalg.norm(ik_target_quat_R)

                # K tile world 0 (batched solver; only idx 0 used afterward)
                jq_all = np.tile(per_world_jq[0:1], (K, 1))
                tgt_L_pos_all = np.tile(target_L_pos[None].astype(np.float32), (K, 1))
                tgt_R_pos_all = np.tile(target_R_pos[None].astype(np.float32), (K, 1))
                tgt_L_quat_all = np.tile(ik_target_quat_L[None].astype(np.float32), (K, 1))
                tgt_R_quat_all = np.tile(ik_target_quat_R[None].astype(np.float32), (K, 1))

                jq_solved = ik_solver.solve(tgt_L_pos_all, tgt_L_quat_all, tgt_R_pos_all, tgt_R_quat_all, jq_all)
                jq_solved[:, 7] = FINGER_OPEN_POS
                jq_solved[:, 8] = FINGER_OPEN_POS
                jq_solved[:, FRANKA_NUM_JOINTS + 7] = FINGER_OPEN_POS
                jq_solved[:, FRANKA_NUM_JOINTS + 8] = FINGER_OPEN_POS

                fk_body_q = ik_solver.eval_fk_batch(jq_solved)
                update_kinematic_bodies(state_0, fk_body_q, info, K)

                contacts = model.collide(state_0)
                for _ in range(RL_SIM_SUBSTEPS):
                    solver_vbd.step(state_0, state_1, control, contacts, sim_dt)
                    state_0, state_1 = state_1, state_0

                per_world_jq[0] = jq_solved[0]

                # #2 Achieved FK post-physics
                (new_L_pos, new_L_quat), (new_R_pos, new_R_quat) = get_ee_poses_dual(state_0, info, 1)
                cable_l, cable_r = compute_cable_endpoint_pos(state_0, info, 1)

                dpl = float(np.linalg.norm(new_L_pos[0] - cable_l[0]))
                dpr = float(np.linalg.norm(new_R_pos[0] - cable_r[0]))
                q2_L = _normalize_quat_w_positive(new_L_quat[0])
                q2_R = _normalize_quat_w_positive(new_R_quat[0])
                dol = float(_quat_distance(q2_L, cost_target_quat_L_fixed))
                dor = float(_quat_distance(q2_R, cost_target_quat_R_fixed))

                traj_left_pos.append(new_L_pos[0].copy())
                traj_right_pos.append(new_R_pos[0].copy())
                traj_left_quat.append(q2_L)
                traj_right_quat.append(q2_R)
                traj_actions.append(best_actions[h].astype(np.float32).copy())
                traj_dist_pos_L.append(dpl)
                traj_dist_pos_R.append(dpr)
                traj_dist_ori_L.append(dol)
                traj_dist_ori_R.append(dor)
                # AR-compat: log full cable body positions for obs reconstruction
                _bq_now = state_0.body_q.numpy()
                _co = info["cable_offset"]
                _cpw = info["cable_per_world"]
                _bws0 = info["bws"][0]
                traj_cable_pos.append(_bq_now[_bws0 + _co : _bws0 + _co + _cpw, :3].astype(np.float32).copy())

                step += 1

            # Success: 4-condition AND (pos L/R + ori L/R)
            if traj_dist_pos_L and traj_dist_pos_R:
                if (
                    traj_dist_pos_L[-1] < cfg.success_threshold_m
                    and traj_dist_pos_R[-1] < cfg.success_threshold_m
                    and traj_dist_ori_L[-1] < _MPPI_ORI_THR_RAD
                    and traj_dist_ori_R[-1] < _MPPI_ORI_THR_RAD
                ):
                    success = True
                    print(
                        f"  SUCCESS at step {step}, "
                        f"pos L={traj_dist_pos_L[-1]:.4f}m "
                        f"R={traj_dist_pos_R[-1]:.4f}m  "
                        f"ori L={math.degrees(traj_dist_ori_L[-1]):.1f}° "
                        f"R={math.degrees(traj_dist_ori_R[-1]):.1f}°"
                    )
                    break

        if not success and not no_mppi:
            if traj_dist_pos_L and traj_dist_pos_R:
                print(
                    f"  FAILED at step {step}, "
                    f"pos L={traj_dist_pos_L[-1]:.4f}m "
                    f"R={traj_dist_pos_R[-1]:.4f}m  "
                    f"ori L={math.degrees(traj_dist_ori_L[-1]):.1f}° "
                    f"R={math.degrees(traj_dist_ori_R[-1]):.1f}°"
                )
            else:
                print("  FAILED (no steps)")

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
            "cable_pos_seq": np.array(traj_cable_pos, dtype=np.float32) if traj_cable_pos else np.zeros((0, 0, 3), dtype=np.float32),
            "success": success,
            "steps": step,
            "warmup_dist_pos_left": warmup_dist_pos_L,
            "warmup_dist_pos_right": warmup_dist_pos_R,
            "warmup_dist_ori_left": warmup_dist_ori_L,
            "warmup_dist_ori_right": warmup_dist_ori_R,
            "warmup_steps": warmup_steps,
            "cost_target_quat_left": cost_target_quat_L_fixed.copy(),
            "cost_target_quat_right": cost_target_quat_R_fixed.copy(),
        }
        demos.append(demo)
        for dL, dR in zip(drifts_L_ep, drifts_R_ep):
            drifts_per_plan_LR.append([dL, dR])
        # Per-episode max(drift_L, drift_R) for DEFINE M2 violation counting
        if drifts_L_ep and drifts_R_ep:
            ep_max = max(max(drifts_L_ep), max(drifts_R_ep))
        else:
            ep_max = 0.0
        drifts_per_episode_max.append(float(ep_max))

    diag_file.close()
    print(f"[DIAG] CSV written → {diag_csv_path}")

    # Cable endpoint means across episodes (Test 7 F4 contract)
    if cable_endpoints_L:
        cable_L_endpoint_mean = np.mean(cable_endpoints_L, axis=0).astype(np.float32)
        cable_R_endpoint_mean = np.mean(cable_endpoints_R, axis=0).astype(np.float32)
    else:
        cable_L_endpoint_mean = None
        cable_R_endpoint_mean = None

    return (demos, drifts_per_plan_LR, drifts_per_episode_max, cable_L_endpoint_mean, cable_R_endpoint_mean)


# =========================================================================
# C.7  HDF5 saving — M3 schema (pos + quat + warmup_ori)
# =========================================================================


def save_demos_hdf5_m3(demos, cfg, output_path, mppi_mode="on", cable_L_endpoint_mean=None, cable_R_endpoint_mean=None):
    """Save M3 demos to HDF5 (pos+quat + warmup_dist pos/ori independent + full metadata).

    Schema (plan v2.2):
        metadata attrs: quat_convention/frame/semantic, mppi_mode, m3_version,
            cost_method/scale, action_layout, cable_L/R_endpoint_mean (optional).
        per-episode: left/right_ee_pos, left/right_ee_quat, action_delta (12D),
            dist_pos_{left,right}, dist_ori_{left,right}, attrs incl.
            warmup_dist_pos/ori_{left,right}, cost_target_quat_{left,right}.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    n_success = sum(1 for d in demos if d["success"])

    with h5py.File(output_path, "w") as f:
        meta = f.create_group("metadata")
        meta.attrs["generator"] = "mppi_m3"
        meta.attrs["m3_version"] = M3_VERSION
        meta.attrs["K"] = cfg.K
        meta.attrs["H"] = cfg.H
        meta.attrs["temperature_lambda"] = cfg.temperature_lambda
        meta.attrs["noise_sigma"] = cfg.noise_sigma
        meta.attrs["noise_correlation"] = cfg.noise_correlation
        meta.attrs["success_threshold_m"] = cfg.success_threshold_m
        meta.attrs["success_threshold_rad"] = cfg.success_threshold_rad
        meta.attrs["success_eval"] = "terminal_AND_pos_ori"
        meta.attrs["action_dim"] = M3_ACTION_DIM
        meta.attrs["action_layout"] = M3_ACTION_LAYOUT
        meta.attrs["quat_convention"] = M3_QUAT_CONVENTION
        meta.attrs["quat_frame"] = M3_QUAT_FRAME
        meta.attrs["quat_semantic"] = M3_QUAT_SEMANTIC
        meta.attrs["mppi_mode"] = mppi_mode
        meta.attrs["cost_method"] = M3_COST_METHOD
        meta.attrs["cost_scale"] = M3_COST_SCALE
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
            # AR-compat: per-step cable body positions (T, cable_per_world, 3)
            if "cable_pos_seq" in demo and demo["cable_pos_seq"].size > 0:
                g.create_dataset("cable_pos_seq", data=demo["cable_pos_seq"], compression="gzip")
            g.attrs["success"] = demo["success"]
            g.attrs["steps"] = demo["steps"]
            g.attrs["warmup_dist_pos_left"] = demo["warmup_dist_pos_left"]
            g.attrs["warmup_dist_pos_right"] = demo["warmup_dist_pos_right"]
            g.attrs["warmup_dist_ori_left"] = demo["warmup_dist_ori_left"]
            g.attrs["warmup_dist_ori_right"] = demo["warmup_dist_ori_right"]
            g.attrs["warmup_steps"] = demo["warmup_steps"]
            g.attrs["cost_target_quat_left"] = demo["cost_target_quat_left"]
            g.attrs["cost_target_quat_right"] = demo["cost_target_quat_right"]

    print(f"[HDF5-M3] Saved {len(demos)} demos ({n_success} success, mode={mppi_mode}) → {output_path}")


# =========================================================================
# I7: RUN_METRICS.json writer — S3 calibration + drift monitoring
# =========================================================================


def save_run_metrics_json(demos, drifts_per_plan_LR, drifts_per_episode_max, wall_clock_s, cfg, output_dir):
    """Write per-λ RUN_METRICS.json with S3 rates + tangent_drift + drift_violation.

    Schema (DEFINE v6.3.2 I7):
        lambda, n_demos, wall_clock_s,
        S1_pos_success_rate, S2_ori_success_rate, S3_combined_rate,
        tangent_drift: {left: {mean, std, max, min, p95, per_plan: [...]},
                        right: {...}},               # M1: per-plan stats
        drift_violation: {threshold_rad, violation_count, total_episodes,
                          violation_rate},           # M2: per-episode count
        cost thresholds, statistical_power_note.
    """
    rates = compute_success_rates(demos)

    drifts_arr = np.asarray(drifts_per_plan_LR, dtype=np.float64)  # (n_plans, 2) = [L, R]
    if drifts_arr.size == 0:
        m1 = {"left": _stats([]), "right": _stats([])}
    else:
        m1_left = _stats(drifts_arr[:, 0])
        m1_left["per_plan"] = drifts_arr[:, 0].tolist()
        m1_right = _stats(drifts_arr[:, 1])
        m1_right["per_plan"] = drifts_arr[:, 1].tolist()
        m1 = {"left": m1_left, "right": m1_right}

    # M2: per-episode violation count (DEFINE v6.3.2 [RUN Measurement Items])
    ep_max_arr = np.asarray(drifts_per_episode_max, dtype=np.float64)
    if ep_max_arr.size == 0:
        m2 = {
            "threshold_rad": DRIFT_THRESHOLD_RAD,
            "violation_count": 0,
            "total_episodes": 0,
            "violation_rate": 0.0,
        }
    else:
        n_viol_ep = int(np.sum(ep_max_arr > DRIFT_THRESHOLD_RAD))
        n_ep = int(len(ep_max_arr))
        m2 = {
            "threshold_rad": DRIFT_THRESHOLD_RAD,
            "violation_count": n_viol_ep,
            "total_episodes": n_ep,
            "violation_rate": n_viol_ep / n_ep if n_ep > 0 else 0.0,
            "per_episode_max": ep_max_arr.tolist(),
        }

    metrics = {
        "schema_version": "v1",
        "m3_version": M3_VERSION,
        "lambda": float(cfg.temperature_lambda),
        "n_demos": len(demos),
        "wall_clock_s": float(wall_clock_s),
        "S1_pos_success_rate": rates["s1"],
        "S2_ori_success_rate": rates["s2"],
        "S3_combined_rate": rates["s3"],
        "tangent_drift": m1,
        "drift_violation": m2,
        "cost_threshold_m": _MPPI_POS_THR_M,
        "cost_threshold_rad": _MPPI_ORI_THR_RAD,
        "cost_method": M3_COST_METHOD,
        "cost_scale": M3_COST_SCALE,
        "statistical_power_note": {
            "n_demos": len(demos),
            "threshold": 0.60,
            "false_demotion_rate_at_p08": 0.06,
            "mitigation": "BLOCKED_FOR_USER, rs review",
        },
    }

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"run_metrics_lam{cfg.temperature_lambda}.json")
    with open(out_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[RUN_METRICS] {out_path}")
    return metrics


# =========================================================================
# CLI / main — M3 default single-lambda + sweep + --no-mppi
# =========================================================================


def main():
    global _MPPI_POS_THR_M, _MPPI_ORI_THR_RAD, M3_COST_SCALE, M3_ACTION_LAYOUT, WARM_START_OFFSET, WARM_START_STEPS
    parser = argparse.ArgumentParser(description=f"MPPI demo generation (M3 12D full pose, {M3_VERSION})")
    parser.add_argument("--device", type=str, default="cuda:0")
    # AC / Phase 0 retune args (2026-04-21 Phase 1 α-2 Step 2).
    parser.add_argument("--ac-mode", action="store_true",
                        help="Use MPPIConfigAC (AC tight thresholds + Phase 0 validated params)")
    parser.add_argument("--cost-scale-override", type=float, default=None,
                        help="Override M3_COST_SCALE (default: auto-derive from threshold)")
    parser.add_argument("--l-ori-weight", type=float, default=0.5,
                        help="IK L_ori objective weight (M3 default 0.5, Phase 0 validated 0.75)")
    parser.add_argument("--r-ori-weight", type=float, default=0.5,
                        help="IK R_ori objective weight (M3 default 0.5, Phase 0 validated 0.75)")
    parser.add_argument("--output-layout", choices=["l-first", "r-first"], default="l-first",
                        help="HDF5 action_delta layout: l-first (M3 native) or r-first (AC env native)")
    parser.add_argument("--rot-action-scale-override", type=float, default=None,
                        help="Override cfg.rot_action_scale (Phase 0 validated 0.10)")
    parser.add_argument("--pos-action-scale-override", type=float, default=None,
                        help="Override cfg.pos_action_scale (MPPI per-step position delta)")
    parser.add_argument("--warm-start-offset-override", type=float, default=None,
                        help="Override warm-start end offset [m] (cfg.warm_start_offset_m)")
    parser.add_argument("--warm-start-steps-override", type=int, default=None,
                        help="Override WARM_START_STEPS (default 40, slerp interpolation steps)")
    parser.add_argument(
        "--single-lambda", type=float, default=0.3, help="Run single lambda (default 0.3, for calibration/S3 gate)"
    )
    parser.add_argument("--sweep", action="store_true", help="Run lambda sweep [0.3, 0.5, 1.0] (skips --single-lambda)")
    parser.add_argument("--n-demos", type=int, default=5)
    parser.add_argument("--max-steps", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=str, default="data/mppi_demos_m3")
    parser.add_argument("--no-warmstart", action="store_true", help="Skip warm-start (baseline verification)")
    parser.add_argument(
        "--no-mppi", action="store_true", help="Skip MPPI outer loop (S4 baseline, warm-start terminal eval only)"
    )
    parser.add_argument("--diag-csv", type=str, default="/tmp/mppi_m3_metrics.csv")
    parser.add_argument(
        "--randomize-cable-xy",
        action="store_true",
        help=(
            "Option C' (2026-04-25): Randomize cable base XY per episode by "
            "uniform noise in ±CABLE_XY_DR_AMPLITUDE (see task_config.py). "
            "Applied per-world before state_0.body_q.assign. Default False."
        ),
    )
    args = parser.parse_args()

    wp.init()
    wp.set_device(args.device)

    # AC mode: select MPPIConfigAC and propagate tight thresholds to module const.
    if args.ac_mode:
        from mpc_config_ac import MPPIConfigAC
        cfg_class = MPPIConfigAC
        print("[AC-MODE] Using MPPIConfigAC (AC tight thresholds + Phase 0 params)")
    else:
        cfg_class = MPPIConfig

    # Set module constants from selected cfg (override via CLI if provided).
    _probe_cfg = cfg_class()
    _MPPI_POS_THR_M = _probe_cfg.success_threshold_m
    _MPPI_ORI_THR_RAD = _probe_cfg.success_threshold_rad
    if args.cost_scale_override is not None:
        M3_COST_SCALE = args.cost_scale_override
    elif hasattr(_probe_cfg, "m3_cost_scale"):
        M3_COST_SCALE = _probe_cfg.m3_cost_scale
    else:
        M3_COST_SCALE = _MPPI_POS_THR_M / _MPPI_ORI_THR_RAD
    if hasattr(_probe_cfg, "warm_start_offset_m"):
        WARM_START_OFFSET = _probe_cfg.warm_start_offset_m
    if args.warm_start_offset_override is not None:
        WARM_START_OFFSET = args.warm_start_offset_override
    if args.warm_start_steps_override is not None:
        WARM_START_STEPS = args.warm_start_steps_override
    print(f"[CONFIG] pos_thr={_MPPI_POS_THR_M}m  ori_thr={_MPPI_ORI_THR_RAD}rad  cost_scale={M3_COST_SCALE:.4f}")
    print(f"[CONFIG] IK weights: L_ori={args.l_ori_weight}  R_ori={args.r_ori_weight}")
    print(f"[CONFIG] warm_start_offset={WARM_START_OFFSET}m  warm_start_steps={WARM_START_STEPS}")

    lambdas = [0.3, 0.5, 1.0] if args.sweep else [args.single_lambda]
    mppi_mode = "off" if args.no_mppi else "on"

    sweep_results = []
    for lam in lambdas:
        print(f"\n{'=' * 60}")
        print(f"  {'SWEEP' if args.sweep else 'SINGLE'} lambda={lam}  mode={mppi_mode}")
        print(f"{'=' * 60}")

        cfg = cfg_class()
        cfg.temperature_lambda = lam
        cfg.action_dim = M3_ACTION_DIM
        cfg.device = args.device
        if args.rot_action_scale_override is not None:
            cfg.rot_action_scale = args.rot_action_scale_override
        if args.pos_action_scale_override is not None:
            cfg.pos_action_scale = args.pos_action_scale_override
        print(f"[CFG-RUNTIME] pos_action_scale={cfg.pos_action_scale}  rot_action_scale={cfg.rot_action_scale}")

        diag_csv = f"/tmp/mppi_m3_sweep_lam{lam}.csv" if args.sweep else args.diag_csv
        t0 = time.perf_counter()
        (demos, drifts, drifts_per_ep_max, cable_L_mean, cable_R_mean) = mppi_generate_demos_m3(
            cfg,
            args.device,
            max_steps=args.max_steps,
            n_demos=args.n_demos,
            seed=args.seed,
            no_warmstart=args.no_warmstart,
            no_mppi=args.no_mppi,
            diag_csv_path=diag_csv,
            l_ori_weight=args.l_ori_weight,
            r_ori_weight=args.r_ori_weight,
            randomize_cable_xy=args.randomize_cable_xy,
        )

        # Phase 1 α-2 Step 2: convert action_delta L-first → R-first for AC DAPG.
        if args.output_layout == "r-first":
            for d in demos:
                # actions shape (T, 12): [L_pos, L_ori, R_pos, R_ori] → [R_pos, R_ori, L_pos, L_ori]
                acts = d["actions"]
                d["actions"] = np.concatenate(
                    [acts[:, 6:9], acts[:, 9:12], acts[:, 0:3], acts[:, 3:6]], axis=1
                )
            print(f"[LAYOUT] Converted action_delta L-first → R-first for all {len(demos)} demos")
            M3_ACTION_LAYOUT = "R-first"  # propagate to HDF5 metadata
        elapsed = time.perf_counter() - t0

        # HDF5 output path + mppi_off subdir for S4 baseline separation
        suffix = ""
        if args.no_warmstart:
            suffix += "_noWS"
        if args.no_mppi:
            suffix += "_noMPPI"
        if args.no_mppi:
            out_dir = os.path.join(args.output_dir, "mppi_off")
            h5_name = f"demos_l{lam}{suffix}.hdf5" if args.sweep else f"demos_default{suffix}.hdf5"
            h5_path = os.path.join(out_dir, h5_name)
            metrics_dir = out_dir
        else:
            h5_name = f"demos_l{lam}{suffix}.hdf5" if args.sweep else f"demos_default{suffix}.hdf5"
            h5_path = os.path.join(args.output_dir, h5_name)
            metrics_dir = args.output_dir

        save_demos_hdf5_m3(
            demos,
            cfg,
            h5_path,
            mppi_mode=mppi_mode,
            cable_L_endpoint_mean=cable_L_mean,
            cable_R_endpoint_mean=cable_R_mean,
        )

        # I7: RUN_METRICS.json per-λ (M1 per-plan stats + M2 per-episode violation)
        metrics = save_run_metrics_json(demos, drifts, drifts_per_ep_max, elapsed, cfg, metrics_dir)

        n_success = sum(1 for d in demos if d["success"])
        sweep_results.append(
            {
                "lambda": lam,
                "n_demos": len(demos),
                "n_success": n_success,
                "S1_pos": metrics["S1_pos_success_rate"],
                "S2_ori": metrics["S2_ori_success_rate"],
                "S3": metrics["S3_combined_rate"],
                "drift_max_L": metrics["tangent_drift"]["left"]["max"],
                "drift_max_R": metrics["tangent_drift"]["right"]["max"],
                "drift_violation_rate": metrics["drift_violation"]["violation_rate"],
                "wall_clock_s": round(elapsed, 1),
            }
        )

    if args.sweep:
        print(f"\n{'=' * 78}")
        print("  M3 SWEEP RESULTS")
        print(f"{'=' * 78}")
        hdr = (
            f"  {'lambda':>8} | {'n_demo':>6} | {'succ':>4} | {'S1':>6} "
            f"| {'S2':>6} | {'S3':>6} | {'dL_max°':>7} | {'dR_max°':>7} "
            f"| {'t_s':>7}"
        )
        print(hdr)
        print(f"  {'-' * (len(hdr) - 2)}")
        for r in sweep_results:
            print(
                f"  {r['lambda']:>8.1f} | {r['n_demos']:>6d} | "
                f"{r['n_success']:>4d} | {r['S1_pos']:>6.1%} | "
                f"{r['S2_ori']:>6.1%} | {r['S3']:>6.1%} | "
                f"{math.degrees(r['drift_max_L']):>7.2f} | "
                f"{math.degrees(r['drift_max_R']):>7.2f} | "
                f"{r['wall_clock_s']:>7.1f}"
            )

        csv_path = "/tmp/mppi_m3_sweep.csv"
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(sweep_results[0].keys()))
            w.writeheader()
            w.writerows(sweep_results)
        print(f"\n  CSV: {csv_path}")

        best = min(sweep_results, key=lambda r: -r["S3"])  # max S3
        print(
            f"\n  BEST (by S3): lambda={best['lambda']}, "
            f"S3={best['S3']:.1%}, success={best['n_success']}/"
            f"{best['n_demos']}"
        )

    # S3 calibration + drift gate (single-λ MPPI ON only; both checked before exit)
    if not args.sweep and not args.no_mppi and len(sweep_results) == 1:
        s3 = sweep_results[0]["S3"]
        drift_v = sweep_results[0]["drift_violation_rate"]
        s3_fail = s3 < 0.60
        drift_fail = drift_v >= DRIFT_VIOLATION_RATE_LIMIT
        if s3_fail or drift_fail:
            reasons = []
            if s3_fail:
                reasons.append(f"S3={s3:.1%} < 60% (S3 calibration)")
            if drift_fail:
                reasons.append(
                    f"drift_violation={drift_v:.1%} >= {DRIFT_VIOLATION_RATE_LIMIT:.0%} (U3 mitigation re-evaluation)"
                )
            print("\n[BLOCKED_FOR_USER] " + " AND ".join(reasons))
            print("  rs review required before proceeding.")
            sys.exit(2)
        print(
            f"\n[S3 GATE] S3={s3:.1%} >= 60%  "
            f"[DRIFT GATE] violation={drift_v:.1%} "
            f"< {DRIFT_VIOLATION_RATE_LIMIT:.0%}  → PASS"
        )


if __name__ == "__main__":
    main()
