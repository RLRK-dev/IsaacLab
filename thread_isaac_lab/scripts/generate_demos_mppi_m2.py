#!/usr/bin/env python3
"""MPPI demo trajectory generation on Newton VBD (M2: dual arm + cable 40seg).

Extends M1 (single arm) to bimanual_reach: both arms simultaneously reach
cable endpoints (left arm → seg 0, right arm → seg 39).

Delta from M1 (generate_demos_mppi.py):
  I1  action_dim = 6 (left pos 3D + right pos 3D)
  I2  build_mppi_scene: 2 arms per world
  I3  MppiIKSolver: 3 objectives (left_pos + right_pos + jlimit)
  I4  cost = max(dist_L, dist_R) — aligns with AND success condition
  I5  warm_start_approach: symmetric dual-arm to cable endpoints
  I6  rollout: left action[:3] + right action[3:6]

Usage:
    cd ~/IsaacLab
    PYTHONPATH=$PYTHONPATH:thread_isaac_lab/scripts:thread_isaac_lab/configs \
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/generate_demos_mppi_m2.py \
        --device cuda:0
"""

import argparse
import csv
import os
import sys
import time

import numpy as np
import h5py

import warp as wp
import newton
from newton.solvers import SolverVBD
from newton.ik import IKSolver, IKObjectivePosition, IKObjectiveJointLimit
from newton._src.sim.ik.ik_common import eval_fk_batched

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "configs"))

from task_config import (
    TABLE_HEIGHT,
    CABLE_SEGMENTS, CABLE_SEG_LEN,
    CABLE_CONTACT_KE, CABLE_CONTACT_KD, CABLE_CONTACT_MU,
    GRASP_X, CLIP1_Y, CLIP_BASE_HEIGHT, CABLE_RADIUS,
    FINGER_OPEN_POS, NJMAX,
)
from test_newton_clip_routing import (
    build_fk_model, add_kinematic_arm, FRANKA_NUM_JOINTS, EE_BODY_OFFSET, GRAVITY,
)
from thread_isaac_lab.configs.mpc_config import MPPIConfig

RL_SIM_SUBSTEPS = 4
VBD_ITERATIONS = 20
DT = 1.0 / 480.0
IK_ITERATIONS = 30
IK_STEP_SIZE = 1.0
REPLAN_INTERVAL = 4  # Hybrid N=4

# M2 constants
M2_ACTION_DIM = 6  # I1: left pos 3D + right pos 3D
RIGHT_EE_BODY_OFFSET = FRANKA_NUM_JOINTS + EE_BODY_OFFSET  # body 15


# =========================================================================
# C.1  Sampling (unchanged from M1, action_dim parameterized)
# =========================================================================

def sample_action_sequences(K, H, action_dim, sigma, beta, rng=None):
    """Sample K action sequences of length H with temporal correlation."""
    if rng is None:
        rng = np.random.default_rng()

    white = rng.normal(0, sigma, size=(K, H, action_dim)).astype(np.float32)

    if beta <= 0:
        return np.clip(white, -1.0, 1.0)

    colored = np.zeros_like(white)
    scale = np.sqrt(1.0 - beta ** 2)
    colored[:, 0, :] = white[:, 0, :]
    for t in range(1, H):
        colored[:, t, :] = beta * colored[:, t - 1, :] + scale * white[:, t, :]

    return np.clip(colored, -1.0, 1.0)


# =========================================================================
# C.3  Weighting (unchanged from M1)
# =========================================================================

def mppi_weights(costs, temperature):
    """Compute MPPI importance weights via softmax(-cost/lambda)."""
    scaled = -costs / temperature
    scaled -= scaled.max()
    w = np.exp(scaled)
    return w / w.sum()


# =========================================================================
# C.4  IK Solver wrapper — I3: dual-arm (3 objectives)
# =========================================================================

class MppiIKSolver:
    """Batched IK for MPPI (dual arm, position-only, n_problems=K).

    3 objectives: left EE position + right EE position + joint limits.
    """

    def __init__(self, fk_model, K, device):
        self.fk_model = fk_model
        self.K = K
        self.device = device

        self.obj_left_pos = IKObjectivePosition(
            link_index=EE_BODY_OFFSET,
            link_offset=wp.vec3(0, 0, 0),
            target_positions=wp.zeros(K, dtype=wp.vec3, device=device),
            weight=1.0,
        )
        self.obj_right_pos = IKObjectivePosition(
            link_index=RIGHT_EE_BODY_OFFSET,
            link_offset=wp.vec3(0, 0, 0),
            target_positions=wp.zeros(K, dtype=wp.vec3, device=device),
            weight=1.0,
        )
        self.obj_jlimit = IKObjectiveJointLimit(
            joint_limit_lower=fk_model.joint_limit_lower,
            joint_limit_upper=fk_model.joint_limit_upper,
            weight=10.0,
        )

        self.solver = IKSolver(
            fk_model, n_problems=K,
            objectives=[self.obj_left_pos, self.obj_right_pos, self.obj_jlimit],
        )

        coord_count = fk_model.joint_coord_count
        self.jq_in = wp.zeros((K, coord_count), dtype=float, device=device)
        self.jq_out = wp.zeros((K, coord_count), dtype=float, device=device)

        dof_count = fk_model.joint_dof_count
        body_count = fk_model.body_count
        self.batch_fk_jq = wp.zeros((K, coord_count), dtype=float, device=device)
        self.batch_fk_jqd = wp.zeros((K, dof_count), dtype=float, device=device)
        self.batch_fk_body_q = wp.zeros((K, body_count), dtype=wp.transform, device=device)
        self.batch_fk_body_qd = wp.zeros(
            (K, body_count), dtype=wp.spatial_vector, device=device)

    def solve(self, target_left_np, target_right_np, jq_starts_np):
        """Solve IK for K problems (dual arm).

        Args:
            target_left_np: (K, 3) left EE target positions
            target_right_np: (K, 3) right EE target positions
            jq_starts_np: (K, coord_count) initial joint positions
        """
        self.obj_left_pos.set_target_positions(
            wp.array(target_left_np.astype(np.float32), dtype=wp.vec3, device=self.device))
        self.obj_right_pos.set_target_positions(
            wp.array(target_right_np.astype(np.float32), dtype=wp.vec3, device=self.device))
        self.jq_in.assign(jq_starts_np.astype(np.float64))
        self.solver.step(self.jq_in, self.jq_out,
                         iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)
        return self.jq_out.numpy()

    def eval_fk_batch(self, jq_np):
        """Evaluate FK for K joint configs. Returns (K, body_count) body transforms."""
        self.batch_fk_jq.assign(jq_np.astype(np.float64))
        eval_fk_batched(
            self.fk_model, self.batch_fk_jq, self.batch_fk_jqd,
            self.batch_fk_body_q, self.batch_fk_body_qd,
        )
        return self.batch_fk_body_q.numpy()


# =========================================================================
# Scene building — I2: dual-arm (2 arms per world)
# =========================================================================

def build_cable_rod(builder, start_pos, direction=(0, 1, 0)):
    """Add cable rod using task_config.py SSOT."""
    n_points = CABLE_SEGMENTS + 1
    dir_np = np.array(direction, dtype=np.float64)
    dir_np /= np.linalg.norm(dir_np)
    positions = [tuple(np.array(start_pos) + dir_np * (i * CABLE_SEG_LEN))
                 for i in range(n_points)]
    cfg = newton.ModelBuilder.ShapeConfig()
    cfg.ke = CABLE_CONTACT_KE
    cfg.kd = CABLE_CONTACT_KD
    cfg.mu = CABLE_CONTACT_MU
    cfg.is_hydroelastic = False
    cfg.gap = 0.002
    cfg.density = 1100.0
    body_ids, joint_ids = builder.add_rod(
        positions=positions, radius=CABLE_RADIUS,
        stretch_stiffness=1.0e6, stretch_damping=0.0,
        bend_stiffness=0.1, bend_damping=0.01, cfg=cfg,
    )
    return body_ids, joint_ids


def _configure_arm_shapes(proto, arm_bs, arm_ss, arm_se, fv):
    """Set shape flags for an arm: link bodies visual-only, fingers contact."""
    fv_set = set(fv)
    for si in range(arm_ss, arm_se):
        local = proto.shape_body[si] - arm_bs
        if local < 7:
            proto.shape_flags[si] = 1
        elif si in fv_set:
            proto.shape_flags[si] = 1
        elif local in (7, 8):
            proto.shape_flags[si] = 0x6


def build_mppi_scene(fk_model, fk_state, K, device):
    """Build full MPPI scene: K worlds, each with 2 arms + cable."""
    proto = newton.ModelBuilder()

    # Left arm
    left_info = add_kinematic_arm(proto, fk_model, fk_state,
                                  arm_body_offset=0, label_prefix="left")
    left_bs, left_ss, left_se, left_fv = left_info
    _configure_arm_shapes(proto, left_bs, left_ss, left_se, left_fv)

    # Right arm (I2: add second arm)
    right_info = add_kinematic_arm(proto, fk_model, fk_state,
                                   arm_body_offset=FRANKA_NUM_JOINTS,
                                   label_prefix="right")
    right_bs, right_ss, right_se, right_fv = right_info
    _configure_arm_shapes(proto, right_bs, right_ss, right_se, right_fv)

    cable_half = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
    cable_start = (GRASP_X, CLIP1_Y - cable_half,
                   TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS)
    cable_shape_s = proto.shape_count
    cable_bodies, _ = build_cable_rod(proto, cable_start)
    cable_shape_e = proto.shape_count

    # Collision filters: cable vs arm link bodies (not fingers)
    for csi in range(cable_shape_s, cable_shape_e):
        for arm_label, arm_ss, arm_se, arm_bs in [
            ("left", left_ss, left_se, left_bs),
            ("right", right_ss, right_se, right_bs),
        ]:
            for asi in range(arm_ss, arm_se):
                if proto.shape_body[asi] - arm_bs < 7:
                    proto.add_shape_collision_filter_pair(csi, asi)

    bodies_per_world = proto.body_count
    cable_per_world = len(cable_bodies)
    cable_offset = cable_bodies[0]

    scene = newton.ModelBuilder(gravity=GRAVITY)
    scene.add_ground_plane()
    tcfg = newton.ModelBuilder.ShapeConfig()
    tcfg.ke = 500.0; tcfg.kd = 100.0; tcfg.mu = 1.0; tcfg.gap = 0.002
    scene.add_shape_box(body=-1, hx=0.35, hy=0.35, hz=0.005,
                        xform=wp.transform((0.3, -0.05, TABLE_HEIGHT - 0.005),
                                           wp.quat_identity()), cfg=tcfg)
    scene.replicate(proto, world_count=K)
    scene.color()
    model = scene.finalize(device=device, requires_grad=False)

    # Zero inv_mass for kinematic arm bodies (both arms)
    bws = model.body_world_start.numpy()
    im = model.body_inv_mass.numpy()
    ii = model.body_inv_inertia.numpy()
    arm_body_count = 2 * FRANKA_NUM_JOINTS  # both arms
    for w in range(K):
        s = bws[w]
        for b in range(arm_body_count):
            im[s + b] = 0.0
            ii[s + b] = np.zeros(3, dtype=np.float32)
    model.body_inv_mass = wp.array(im, dtype=model.body_inv_mass.dtype, device=device)
    model.body_inv_inertia = wp.array(ii, dtype=model.body_inv_inertia.dtype, device=device)

    model.rigid_contact_max = NJMAX
    solver = SolverVBD(model, iterations=VBD_ITERATIONS)

    info = {
        "bws": bws,
        "bodies_per_world": bodies_per_world,
        "cable_per_world": cable_per_world,
        "cable_offset": cable_offset,
        "left_body_start": left_bs,  # 0
        "right_body_start": right_bs,  # FRANKA_NUM_JOINTS = 9
    }
    return model, solver, info


# =========================================================================
# C.2  Rollout + cost — I4: cost=max, I6: dual-arm rollout
# =========================================================================

def copy_world0_to_all(state, bws, bodies_per_world, K, device,
                       solver_vbd=None):
    """Reset all worlds to world 0 state."""
    bq = state.body_q.numpy()
    bqd = state.body_qd.numpy()
    s0 = bws[0]
    ref_q = bq[s0:s0 + bodies_per_world].copy()
    ref_qd = bqd[s0:s0 + bodies_per_world].copy()
    for w in range(1, K):
        sw = bws[w]
        bq[sw:sw + bodies_per_world] = ref_q
        bqd[sw:sw + bodies_per_world] = ref_qd
    state.body_q.assign(bq)
    state.body_qd.assign(bqd)
    if solver_vbd is not None:
        bqp = solver_vbd.body_q_prev.numpy()
        ref_qp = bqp[s0:s0 + bodies_per_world].copy()
        for w in range(1, K):
            sw = bws[w]
            bqp[sw:sw + bodies_per_world] = ref_qp
        solver_vbd.body_q_prev.assign(bqp)


def compute_cable_endpoint_pos(state, info, K):
    """Get cable endpoint positions for each world.

    Returns:
        left_end: (K, 3) — seg 0 position
        right_end: (K, 3) — seg 39 (last) position
    """
    bq = state.body_q.numpy()
    bws = info["bws"]
    co = info["cable_offset"]
    cpw = info["cable_per_world"]
    left_end = np.zeros((K, 3), dtype=np.float32)
    right_end = np.zeros((K, 3), dtype=np.float32)
    for w in range(K):
        left_end[w] = bq[bws[w] + co, :3]
        right_end[w] = bq[bws[w] + co + cpw - 1, :3]
    return left_end, right_end


def get_ee_positions_dual(state, info, K):
    """Get left and right EE positions for each world.

    Returns:
        left_ee: (K, 3), right_ee: (K, 3)
    """
    bq = state.body_q.numpy()
    bws = info["bws"]
    lbs = info["left_body_start"]
    rbs = info["right_body_start"]
    left_ee = np.zeros((K, 3), dtype=np.float32)
    right_ee = np.zeros((K, 3), dtype=np.float32)
    for w in range(K):
        left_ee[w] = bq[bws[w] + lbs + EE_BODY_OFFSET, :3]
        right_ee[w] = bq[bws[w] + rbs + EE_BODY_OFFSET, :3]
    return left_ee, right_ee


def update_kinematic_bodies(state, fk_body_q, info, K):
    """Copy FK body transforms to physics state for all worlds (both arms)."""
    bq = state.body_q.numpy()
    bws = info["bws"]
    arm_body_count = 2 * FRANKA_NUM_JOINTS
    for w in range(K):
        s = bws[w]
        bq[s:s + arm_body_count] = fk_body_q[w, :arm_body_count]
    state.body_q.assign(bq)


def rollout_and_cost(model, solver, state_0, state_1, control,
                     actions_seq, ik_solver, per_world_jq,
                     info, K, H, cfg):
    """Rollout K trajectories for H steps, return total costs.

    I4: cost = max(dist_L, dist_R) per step, accumulated over horizon.
    I6: left action[:3], right action[3:6].
    """
    sim_dt = DT / RL_SIM_SUBSTEPS
    costs = np.zeros(K, dtype=np.float32)
    jq = per_world_jq.copy()
    t_ik_total = 0.0
    t_physics_total = 0.0
    nan_mask = np.zeros(K, dtype=bool)
    ee_spread_max_left = 0.0
    ee_spread_max_right = 0.0

    for h in range(H):
        left_ee, right_ee = get_ee_positions_dual(state_0, info, K)

        # I6: split action into left ([:3]) and right ([3:6])
        left_delta = actions_seq[:, h, :3] * cfg.pos_action_scale
        right_delta = actions_seq[:, h, 3:6] * cfg.pos_action_scale
        target_left = left_ee + left_delta
        target_right = right_ee + right_delta

        # I3: dual-arm IK solve
        t0_ik = time.perf_counter()
        jq_solved = ik_solver.solve(target_left, target_right, jq)

        # Keep fingers open, preserve non-arm coords
        jq_solved[:, 7] = FINGER_OPEN_POS
        jq_solved[:, 8] = FINGER_OPEN_POS
        jq_solved[:, FRANKA_NUM_JOINTS + 7] = FINGER_OPEN_POS
        jq_solved[:, FRANKA_NUM_JOINTS + 8] = FINGER_OPEN_POS

        fk_body_q = ik_solver.eval_fk_batch(jq_solved)
        t_ik_total += time.perf_counter() - t0_ik

        update_kinematic_bodies(state_0, fk_body_q, info, K)

        # EE spread diagnostics (both arms)
        ik_left, ik_right = get_ee_positions_dual(state_0, info, K)
        valid_idx = ~nan_mask
        if valid_idx.sum() > 1:
            ee_spread_max_left = max(ee_spread_max_left,
                float(np.sqrt(np.sum(np.var(ik_left[valid_idx], axis=0)))))
            ee_spread_max_right = max(ee_spread_max_right,
                float(np.sqrt(np.sum(np.var(ik_right[valid_idx], axis=0)))))

        t0_phys = time.perf_counter()
        contacts = model.collide(state_0)
        for _ in range(RL_SIM_SUBSTEPS):
            solver.step(state_0, state_1, control, contacts, sim_dt)
            state_0, state_1 = state_1, state_0
        t_physics_total += time.perf_counter() - t0_phys

        # NaN check
        bq_check = state_0.body_q.numpy()
        bws = info["bws"]
        bpw = info["bodies_per_world"]
        for w in range(K):
            if not nan_mask[w]:
                s = bws[w]
                chunk = bq_check[s:s + bpw]
                if np.any(np.isnan(chunk)) or np.any(np.isinf(chunk)):
                    nan_mask[w] = True
                    costs[w] = 1e6
        if h == 0 and np.any(nan_mask):
            n_nan = nan_mask.sum()
            print(f"  [WARN] {n_nan}/{K} worlds NaN at h=0")

        # I4: cost = max(dist_L, dist_R)
        new_left, new_right = get_ee_positions_dual(state_0, info, K)
        cable_left, cable_right = compute_cable_endpoint_pos(state_0, info, K)
        dist_l = np.linalg.norm(new_left - cable_left, axis=1)
        dist_r = np.linalg.norm(new_right - cable_right, axis=1)
        step_cost = np.maximum(dist_l, dist_r)
        costs += np.where(nan_mask, 0.0, step_cost)

        jq = jq_solved.copy()

    n_nan = int(nan_mask.sum())
    if n_nan > 0:
        print(f"  [NaN] {n_nan}/{K} worlds had NaN ({n_nan * 100 // K}%)")
    ee_spread_max = max(ee_spread_max_left, ee_spread_max_right)
    return costs, n_nan, t_ik_total, t_physics_total, ee_spread_max


# =========================================================================
# I5: Warm-start (dual-arm symmetric approach to cable endpoints)
# =========================================================================

WARM_START_OFFSET = 0.12  # [m] stop 120mm short of target (> threshold 80mm)
WARM_START_STEPS = 40

def warm_start_approach(model, solver_vbd, state_0, state_1, control,
                        ik_solver, info, K, fk_jq, coord_count, device):
    """Scripted dual-arm IK straight-line from home to cable endpoint near-positions.

    Both arms approach their respective cable endpoints simultaneously.
    3-inequality: target_distance (0.316-0.361m) > offset (0.12m) > threshold (0.08m).
    """
    sim_dt = DT / RL_SIM_SUBSTEPS
    bws = info["bws"]

    left_ee_start, right_ee_start = get_ee_positions_dual(state_0, info, 1)
    left_ee_start = left_ee_start[0]
    right_ee_start = right_ee_start[0]
    cable_left, cable_right = compute_cable_endpoint_pos(state_0, info, 1)
    cable_left = cable_left[0]
    cable_right = cable_right[0]

    dir_left = cable_left - left_ee_start
    dir_right = cable_right - right_ee_start
    dist_left = np.linalg.norm(dir_left)
    dist_right = np.linalg.norm(dir_right)

    if dist_left < WARM_START_OFFSET and dist_right < WARM_START_OFFSET:
        print(f"  [WARM] Already within offset (L={dist_left:.3f}m, R={dist_right:.3f}m)")
        per_world_jq = np.tile(fk_jq[:coord_count], (K, 1))
        return per_world_jq, dist_left, dist_right, 0

    target_left = left_ee_start + dir_left / dist_left * (dist_left - WARM_START_OFFSET)
    target_right = right_ee_start + dir_right / dist_right * (dist_right - WARM_START_OFFSET)

    per_world_jq = np.tile(fk_jq[:coord_count], (K, 1))

    print(f"  [WARM] Left EE {left_ee_start} → {target_left} "
          f"(dist {dist_left:.3f}m → {WARM_START_OFFSET:.3f}m)")
    print(f"  [WARM] Right EE {right_ee_start} → {target_right} "
          f"(dist {dist_right:.3f}m → {WARM_START_OFFSET:.3f}m)")
    print(f"  [WARM] {WARM_START_STEPS} steps, synchronized approach")

    for s in range(WARM_START_STEPS):
        alpha = (s + 1) / WARM_START_STEPS
        ee_left_interp = left_ee_start + (target_left - left_ee_start) * alpha
        ee_right_interp = right_ee_start + (target_right - right_ee_start) * alpha

        tgt_left_all = np.tile(ee_left_interp[None, :].astype(np.float32), (K, 1))
        tgt_right_all = np.tile(ee_right_interp[None, :].astype(np.float32), (K, 1))

        jq_solved = ik_solver.solve(tgt_left_all, tgt_right_all, per_world_jq)
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

    final_left, final_right = get_ee_positions_dual(state_0, info, 1)
    cable_l_final, cable_r_final = compute_cable_endpoint_pos(state_0, info, 1)
    final_dist_l = np.linalg.norm(final_left[0] - cable_l_final[0])
    final_dist_r = np.linalg.norm(final_right[0] - cable_r_final[0])
    print(f"  [WARM] Done. Left dist={final_dist_l:.4f}m, Right dist={final_dist_r:.4f}m")

    return per_world_jq, final_dist_l, final_dist_r, WARM_START_STEPS


# =========================================================================
# C.5  MPPI outer loop — M2 dual-arm
# =========================================================================

def mppi_generate_demos(cfg, device, max_steps=128, n_demos=5, seed=42,
                        no_warmstart=False, no_mppi=False,
                        diag_csv_path="/tmp/mppi_m2_metrics.csv"):
    """Generate M2 bimanual_reach demos using MPPI with Hybrid N=4 replanning."""
    K = cfg.K
    H = cfg.H

    rng = np.random.default_rng(seed)

    print(f"\n[MPPI-M2] Building scene K={K} (dual-arm)...")
    fk_model = build_fk_model(device=device)
    fk_state = fk_model.state()
    fk_jq = fk_state.joint_q.numpy()
    fk_tp = fk_model.joint_target_pos.numpy()
    fk_jq[:] = fk_tp[:]
    # Both arms: open fingers
    fk_jq[7] = FINGER_OPEN_POS
    fk_jq[8] = FINGER_OPEN_POS
    fk_jq[FRANKA_NUM_JOINTS + 7] = FINGER_OPEN_POS
    fk_jq[FRANKA_NUM_JOINTS + 8] = FINGER_OPEN_POS
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    model, solver_vbd, info = build_mppi_scene(fk_model, fk_state, K, device)
    ik_solver = MppiIKSolver(fk_model, K, device)

    state_0 = model.state()
    state_1 = model.state()
    control = model.control()

    coord_count = fk_model.joint_coord_count

    init_body_q = state_0.body_q.numpy().copy()
    init_body_qd = state_0.body_qd.numpy().copy()

    demos = []

    diag_file = open(diag_csv_path, "w", newline="")
    diag_csv = csv.writer(diag_file)
    diag_csv.writerow(["episode", "step", "nan_count", "k_eff",
                        "weight_entropy", "weight_mass_valid",
                        "top1_weight", "best_action_nan", "plan_time_s",
                        "dist_left", "dist_right",
                        "cost_min", "cost_max", "cost_range", "cost_std",
                        "ee_spread_max_mm", "jq_sync"])
    print(f"[DIAG] CSV → {diag_csv_path}")

    for ep in range(n_demos):
        ep_i = ep
        print(f"\n[MPPI-M2] Episode {ep + 1}/{n_demos}")

        state_0.body_q.assign(init_body_q)
        state_0.body_qd.assign(init_body_qd)
        solver_vbd.body_q_prev = wp.clone(state_0.body_q)

        if no_warmstart:
            per_world_jq = np.tile(fk_jq[:coord_count], (K, 1))
            left_ee0, right_ee0 = get_ee_positions_dual(state_0, info, 1)
            cable_l0, cable_r0 = compute_cable_endpoint_pos(state_0, info, 1)
            warmup_dist_l = float(np.linalg.norm(left_ee0[0] - cable_l0[0]))
            warmup_dist_r = float(np.linalg.norm(right_ee0[0] - cable_r0[0]))
            warmup_steps = 0
            print(f"  [WARM] SKIPPED, dist_L={warmup_dist_l:.3f}m, "
                  f"dist_R={warmup_dist_r:.3f}m")
        else:
            per_world_jq, warmup_dist_l, warmup_dist_r, warmup_steps = \
                warm_start_approach(
                    model, solver_vbd, state_0, state_1, control,
                    ik_solver, info, K, fk_jq, coord_count, device)

        traj_left_ee = []
        traj_right_ee = []
        traj_actions = []
        traj_dist_left = []
        traj_dist_right = []

        step = 0
        success = False

        if no_mppi:
            left_ee, right_ee = get_ee_positions_dual(state_0, info, 1)
            cable_l, cable_r = compute_cable_endpoint_pos(state_0, info, 1)
            dl = float(np.linalg.norm(left_ee[0] - cable_l[0]))
            dr = float(np.linalg.norm(right_ee[0] - cable_r[0]))
            traj_left_ee.append(left_ee[0].copy())
            traj_right_ee.append(right_ee[0].copy())
            traj_actions.append(np.zeros(M2_ACTION_DIM))
            traj_dist_left.append(dl)
            traj_dist_right.append(dr)
            step = 1
            success = dl < cfg.success_threshold_m and dr < cfg.success_threshold_m
            print(f"  [NO-MPPI] hold dist_L={dl:.4f}m dist_R={dr:.4f}m success={success}")

        while not no_mppi and step < max_steps:
            copy_world0_to_all(state_0, info["bws"], info["bodies_per_world"],
                               K, device, solver_vbd=solver_vbd)
            per_world_jq[:] = per_world_jq[0:1]

            saved_q = state_0.body_q.numpy().copy()
            saved_qd = state_0.body_qd.numpy().copy()
            saved_bq_prev = solver_vbd.body_q_prev.numpy().copy()
            saved_jq = per_world_jq.copy()

            # I1: action_dim=6
            actions = sample_action_sequences(
                K, H, M2_ACTION_DIM, cfg.noise_sigma, cfg.noise_correlation, rng)

            t0_plan = time.perf_counter()
            costs, nan_count, t_ik, t_phys, ee_spread_max = rollout_and_cost(
                model, solver_vbd, state_0, state_1, control,
                actions, ik_solver, per_world_jq, info, K, H, cfg)
            t_plan = time.perf_counter() - t0_plan
            if step == 0:
                print(f"  [TIMING] plan={t_plan:.2f}s (IK={t_ik:.2f}s, "
                      f"physics={t_phys:.2f}s, other={t_plan - t_ik - t_phys:.2f}s)")

            weights = mppi_weights(costs, cfg.temperature_lambda)
            best_actions = np.einsum('k,kha->ha', weights, actions)

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
            w_entropy = -np.sum(w_valid * np.log(w_valid + 1e-30)) if len(w_valid) > 0 else 0.0
            w_mass_valid = float(w_valid.sum()) if len(w_valid) > 0 else 0.0
            top1_w = float(w_valid.max()) if len(w_valid) > 0 else 0.0
            ba_has_nan = bool(np.any(np.isnan(best_actions)) or np.any(np.isinf(best_actions)))
            if diag_csv is not None:
                diag_csv.writerow([ep_i, step, nan_count, k_eff,
                                   f"{w_entropy:.4f}", f"{w_mass_valid:.6f}",
                                   f"{top1_w:.6f}", int(ba_has_nan),
                                   f"{t_plan:.3f}", "", "",
                                   f"{c_min:.4f}", f"{c_max:.4f}",
                                   f"{c_range:.4f}", f"{c_std:.4f}",
                                   f"{ee_spread_max * 1000:.2f}", 1])
            if step % 16 == 0:
                print(f"  [DIAG] step={step} nan={nan_count}/{K} k_eff={k_eff} "
                      f"entropy={w_entropy:.2f} mass={w_mass_valid:.4f} "
                      f"top1={top1_w:.4f} ba_nan={ba_has_nan} "
                      f"cost_range={c_range:.4f} cost_std={c_std:.4f} "
                      f"ee_spread={ee_spread_max * 1000:.1f}mm")

            state_0.body_q.assign(saved_q)
            state_0.body_qd.assign(saved_qd)
            solver_vbd.body_q_prev.assign(saved_bq_prev)
            per_world_jq = saved_jq.copy()

            # Execute first REPLAN_INTERVAL steps on world 0
            n_exec = min(REPLAN_INTERVAL, max_steps - step)
            sim_dt = DT / RL_SIM_SUBSTEPS
            bws = info["bws"]

            for h in range(n_exec):
                # I6: left action[:3], right action[3:6]
                left_ee_now, right_ee_now = get_ee_positions_dual(state_0, info, 1)
                left_pos_delta = best_actions[h, :3] * cfg.pos_action_scale
                right_pos_delta = best_actions[h, 3:6] * cfg.pos_action_scale
                target_l = left_ee_now[0] + left_pos_delta
                target_r = right_ee_now[0] + right_pos_delta

                jq_all = np.tile(per_world_jq[0:1], (K, 1))
                tgt_l_all = np.tile(target_l[None, :], (K, 1))
                tgt_r_all = np.tile(target_r[None, :], (K, 1))
                jq_solved = ik_solver.solve(tgt_l_all, tgt_r_all, jq_all)
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

                new_left, new_right = get_ee_positions_dual(state_0, info, 1)
                cable_l, cable_r = compute_cable_endpoint_pos(state_0, info, 1)
                dl = np.linalg.norm(new_left[0] - cable_l[0])
                dr = np.linalg.norm(new_right[0] - cable_r[0])

                traj_left_ee.append(new_left[0].copy())
                traj_right_ee.append(new_right[0].copy())
                traj_actions.append(best_actions[h].copy())
                traj_dist_left.append(dl)
                traj_dist_right.append(dr)

                step += 1

            # AND success: both arms within threshold
            if traj_dist_left and traj_dist_right:
                if (traj_dist_left[-1] < cfg.success_threshold_m and
                        traj_dist_right[-1] < cfg.success_threshold_m):
                    success = True
                    print(f"  SUCCESS at step {step}, "
                          f"dist_L={traj_dist_left[-1]:.4f}m, "
                          f"dist_R={traj_dist_right[-1]:.4f}m")
                    break

        if not success:
            if traj_dist_left and traj_dist_right:
                print(f"  FAILED at step {step}, "
                      f"dist_L={traj_dist_left[-1]:.4f}m, "
                      f"dist_R={traj_dist_right[-1]:.4f}m")
            else:
                print("  FAILED (no steps)")

        demo = {
            "left_ee_pos": np.array(traj_left_ee),
            "right_ee_pos": np.array(traj_right_ee),
            "actions": np.array(traj_actions),
            "dist_left": np.array(traj_dist_left),
            "dist_right": np.array(traj_dist_right),
            "success": success,
            "steps": step,
            "warmup_dist_left": warmup_dist_l,
            "warmup_dist_right": warmup_dist_r,
            "warmup_steps": warmup_steps,
        }
        demos.append(demo)

    diag_file.close()
    print(f"[DIAG] CSV written → {diag_csv_path}")

    return demos


def save_demos_hdf5(demos, cfg, output_path):
    """Save M2 demos to HDF5."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    n_success = sum(1 for d in demos if d["success"])
    with h5py.File(output_path, "w") as f:
        meta = f.create_group("metadata")
        meta.attrs["generator"] = "mppi_m2"
        meta.attrs["K"] = cfg.K
        meta.attrs["H"] = cfg.H
        meta.attrs["temperature_lambda"] = cfg.temperature_lambda
        meta.attrs["noise_sigma"] = cfg.noise_sigma
        meta.attrs["noise_correlation"] = cfg.noise_correlation
        meta.attrs["success_threshold_m"] = cfg.success_threshold_m
        meta.attrs["success_eval"] = "terminal_AND"
        meta.attrs["action_dim"] = M2_ACTION_DIM
        meta.attrs["newton_dt"] = cfg.newton_dt
        meta.attrs["sim_substeps"] = cfg.sim_substeps
        meta.attrs["replan_interval"] = REPLAN_INTERVAL
        meta.attrs["n_demos"] = len(demos)
        meta.attrs["n_success"] = n_success

        for i, demo in enumerate(demos):
            g = f.create_group(f"episode_{i}")
            g.create_dataset("left_ee_pos", data=demo["left_ee_pos"])
            g.create_dataset("right_ee_pos", data=demo["right_ee_pos"])
            g.create_dataset("action_delta", data=demo["actions"])
            g.create_dataset("dist_left", data=demo["dist_left"])
            g.create_dataset("dist_right", data=demo["dist_right"])
            g.attrs["success"] = demo["success"]
            g.attrs["steps"] = demo["steps"]
            g.attrs["warmup_dist_left"] = demo["warmup_dist_left"]
            g.attrs["warmup_dist_right"] = demo["warmup_dist_right"]
            g.attrs["warmup_steps"] = demo["warmup_steps"]

    print(f"[HDF5] Saved {len(demos)} demos ({n_success} success) to {output_path}")


# =========================================================================
# Main: 3x1 sweep (lambda only, sigma fixed)
# =========================================================================

def main():
    parser = argparse.ArgumentParser(description="MPPI demo generation (M2 dual-arm)")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--sweep", action="store_true",
                        help="Run lambda sweep [0.3, 0.5, 1.0]")
    parser.add_argument("--n_demos", type=int, default=5)
    parser.add_argument("--max_steps", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output_dir", type=str, default="data/mppi_demos_m2")
    parser.add_argument("--no-warmstart", action="store_true",
                        help="Skip warm-start (baseline verification)")
    parser.add_argument("--no-mppi", action="store_true",
                        help="Skip MPPI (baseline verification)")
    parser.add_argument("--diag-csv", type=str,
                        default="/tmp/mppi_m2_metrics.csv")
    args = parser.parse_args()

    wp.init()
    wp.set_device(args.device)

    if args.sweep:
        lambdas = [0.3, 0.5, 1.0]
        sweep_results = []

        for lam in lambdas:
            print(f"\n{'=' * 60}")
            print(f"  SWEEP: lambda={lam}")
            print(f"{'=' * 60}")

            cfg = MPPIConfig()
            cfg.temperature_lambda = lam
            cfg.action_dim = M2_ACTION_DIM
            cfg.device = args.device

            t0 = time.perf_counter()
            sweep_csv = f"/tmp/mppi_m2_sweep_lam{lam}.csv"
            demos = mppi_generate_demos(
                cfg, args.device,
                max_steps=args.max_steps,
                n_demos=args.n_demos,
                seed=args.seed,
                diag_csv_path=sweep_csv,
            )
            elapsed = time.perf_counter() - t0

            n_success = sum(1 for d in demos if d["success"])
            final_dists_l = [d["dist_left"][-1] for d in demos
                             if len(d["dist_left"]) > 0]
            final_dists_r = [d["dist_right"][-1] for d in demos
                             if len(d["dist_right"]) > 0]
            mean_dist_l = np.mean(final_dists_l) if final_dists_l else float("nan")
            mean_dist_r = np.mean(final_dists_r) if final_dists_r else float("nan")

            sweep_results.append({
                "lambda": lam,
                "success_rate": n_success / len(demos),
                "mean_dist_left": round(float(mean_dist_l), 4),
                "mean_dist_right": round(float(mean_dist_r), 4),
                "wall_clock_s": round(elapsed, 1),
            })

            h5_path = os.path.join(args.output_dir, f"demos_l{lam}.hdf5")
            save_demos_hdf5(demos, cfg, h5_path)

        print(f"\n{'=' * 70}")
        print(f"  M2 SWEEP RESULTS")
        print(f"{'=' * 70}")
        print(f"  {'lambda':>8} | {'success':>8} | {'mean_L':>10} | "
              f"{'mean_R':>10} | {'time_s':>8}")
        print(f"  {'-' * 8}-+-{'-' * 8}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 8}")
        for r in sweep_results:
            print(f"  {r['lambda']:>8.1f} | {r['success_rate']:>8.1%} | "
                  f"{r['mean_dist_left']:>10.4f} | "
                  f"{r['mean_dist_right']:>10.4f} | {r['wall_clock_s']:>8.1f}")

        csv_path = "/tmp/mppi_m2_sweep.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["lambda", "success_rate",
                               "mean_dist_left", "mean_dist_right", "wall_clock_s"])
            writer.writeheader()
            writer.writerows(sweep_results)
        print(f"\n  CSV: {csv_path}")

        best = min(sweep_results,
                   key=lambda r: max(r["mean_dist_left"], r["mean_dist_right"]))
        print(f"\n  BEST: lambda={best['lambda']}, "
              f"dist_L={best['mean_dist_left']:.4f}m, "
              f"dist_R={best['mean_dist_right']:.4f}m, "
              f"success={best['success_rate']:.0%}")

    else:
        cfg = MPPIConfig()
        cfg.action_dim = M2_ACTION_DIM
        cfg.device = args.device
        demos = mppi_generate_demos(
            cfg, args.device,
            max_steps=args.max_steps,
            n_demos=args.n_demos,
            seed=args.seed,
            no_warmstart=args.no_warmstart,
            no_mppi=args.no_mppi,
            diag_csv_path=args.diag_csv,
        )
        suffix = ""
        if args.no_warmstart:
            suffix += "_noWS"
        if args.no_mppi:
            suffix += "_noMPPI"
        h5_path = os.path.join(args.output_dir, f"demos_default{suffix}.hdf5")
        save_demos_hdf5(demos, cfg, h5_path)


if __name__ == "__main__":
    main()
