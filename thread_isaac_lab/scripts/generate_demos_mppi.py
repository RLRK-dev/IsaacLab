#!/usr/bin/env python3
"""MPPI demo trajectory generation on Newton VBD (M1: single arm + cable 40seg).

Modules:
  C.1  sample_action_sequences()  — Gaussian + temporal correlation
  C.2  rollout_and_cost()         — parallel physics + distance cost
  C.4  MppiIKSolver               — batched IK (n_problems=K)
  C.3  mppi_weights()             — softmax(-cost/lambda)
  C.5  mppi_generate_demos()      — Hybrid N=4 loop + 3x3 sweep

Usage:
    cd ~/IsaacLab
    PYTHONPATH=$PYTHONPATH:thread_isaac_lab/scripts:thread_isaac_lab/configs \
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/generate_demos_mppi.py \
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


# =========================================================================
# C.1  Sampling
# =========================================================================

def sample_action_sequences(K, H, action_dim, sigma, beta, rng=None):
    """Sample K action sequences of length H with temporal correlation.

    Args:
        K: number of samples
        H: horizon length
        sigma: noise std in [-1,1] space
        beta: temporal correlation [0=white, 1=fully correlated]
        rng: numpy random generator

    Returns:
        (K, H, action_dim) array, clipped to [-1, 1]
    """
    if rng is None:
        rng = np.random.default_rng()

    white = rng.normal(0, sigma, size=(K, H, action_dim)).astype(np.float32)

    if beta <= 0:
        return np.clip(white, -1.0, 1.0)

    # AR(1) colored noise: a[t] = beta * a[t-1] + sqrt(1-beta^2) * white[t]
    colored = np.zeros_like(white)
    scale = np.sqrt(1.0 - beta ** 2)
    colored[:, 0, :] = white[:, 0, :]
    for t in range(1, H):
        colored[:, t, :] = beta * colored[:, t - 1, :] + scale * white[:, t, :]

    return np.clip(colored, -1.0, 1.0)


# =========================================================================
# C.3  Weighting
# =========================================================================

def mppi_weights(costs, temperature):
    """Compute MPPI importance weights via softmax(-cost/lambda).

    Args:
        costs: (K,) array of total trajectory costs
        temperature: lambda parameter

    Returns:
        (K,) normalized weights summing to 1
    """
    scaled = -costs / temperature
    scaled -= scaled.max()  # numerical stability
    w = np.exp(scaled)
    return w / w.sum()


# =========================================================================
# C.4  IK Solver wrapper
# =========================================================================

class MppiIKSolver:
    """Batched IK for MPPI (single arm, position-only, n_problems=K)."""

    def __init__(self, fk_model, K, device):
        self.fk_model = fk_model
        self.K = K
        self.device = device

        left_ee = EE_BODY_OFFSET

        self.obj_pos = IKObjectivePosition(
            link_index=left_ee,
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
            objectives=[self.obj_pos, self.obj_jlimit],
        )

        coord_count = fk_model.joint_coord_count
        self.jq_in = wp.zeros((K, coord_count), dtype=float, device=device)
        self.jq_out = wp.zeros((K, coord_count), dtype=float, device=device)

        # Batched FK buffers
        dof_count = fk_model.joint_dof_count
        body_count = fk_model.body_count
        self.batch_fk_jq = wp.zeros((K, coord_count), dtype=float, device=device)
        self.batch_fk_jqd = wp.zeros((K, dof_count), dtype=float, device=device)
        self.batch_fk_body_q = wp.zeros((K, body_count), dtype=wp.transform, device=device)
        self.batch_fk_body_qd = wp.zeros(
            (K, body_count), dtype=wp.spatial_vector, device=device)

    def solve(self, target_positions_np, jq_starts_np):
        """Solve IK for K problems.

        Args:
            target_positions_np: (K, 3) EE target positions
            jq_starts_np: (K, coord_count) initial joint positions

        Returns:
            (K, coord_count) solved joint positions (numpy)
        """
        self.obj_pos.set_target_positions(
            wp.array(target_positions_np.astype(np.float32), dtype=wp.vec3, device=self.device))
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
# Scene building (reuses build_mppi_scene.py pattern)
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


def build_mppi_scene(fk_model, fk_state, K, device):
    """Build full MPPI scene: K worlds, each with 1 arm + cable."""
    proto = newton.ModelBuilder()
    arm_info = add_kinematic_arm(proto, fk_model, fk_state,
                                  arm_body_offset=0, label_prefix="left")
    arm_bs, arm_ss, arm_se, fv = arm_info
    fv_set = set(fv)
    for si in range(arm_ss, arm_se):
        local = proto.shape_body[si] - arm_bs
        if local < 7:
            proto.shape_flags[si] = 1
        elif si in fv_set:
            proto.shape_flags[si] = 1
        # Franka-legacy finger indices, NOT UR5e-swapped (S2); port for UR5e (see S2_DEFERRED_OBLIGATIONS.md)
        elif local in (7, 8):
            proto.shape_flags[si] = 0x6

    cable_half = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
    cable_start = (GRASP_X, CLIP1_Y - cable_half,
                   TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS)
    cable_shape_s = proto.shape_count
    cable_bodies, _ = build_cable_rod(proto, cable_start)
    cable_shape_e = proto.shape_count

    for csi in range(cable_shape_s, cable_shape_e):
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

    # Zero inv_mass for kinematic arm bodies
    bws = model.body_world_start.numpy()
    im = model.body_inv_mass.numpy()
    ii = model.body_inv_inertia.numpy()
    for w in range(K):
        s = bws[w]
        for b in range(FRANKA_NUM_JOINTS):
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
    }
    return model, solver, info


# =========================================================================
# C.2  Rollout + cost
# =========================================================================

def copy_world0_to_all(state, bws, bodies_per_world, K, device,
                       solver_vbd=None):
    """Reset all worlds to world 0 state (body_q, body_qd, body_q_prev)."""
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


def compute_cable_center_pos(state, info, K):
    """Get cable center position for each world. Returns (K, 3)."""
    bq = state.body_q.numpy()
    bws = info["bws"]
    co = info["cable_offset"]
    mid = info["cable_per_world"] // 2
    centers = np.zeros((K, 3), dtype=np.float32)
    for w in range(K):
        centers[w] = bq[bws[w] + co + mid, :3]
    return centers


def get_ee_positions(state, info, K):
    """Get left EE position for each world. Returns (K, 3)."""
    bq = state.body_q.numpy()
    bws = info["bws"]
    positions = np.zeros((K, 3), dtype=np.float32)
    for w in range(K):
        positions[w] = bq[bws[w] + EE_BODY_OFFSET, :3]
    return positions


def update_kinematic_bodies(state, fk_body_q, info, K):
    """Copy FK body transforms to physics state for all worlds.

    Args:
        fk_body_q: (K, body_count, 7) — [x, y, z, qx, qy, qz, qw]
    """
    bq = state.body_q.numpy()
    bws = info["bws"]
    for w in range(K):
        s = bws[w]
        bq[s:s + FRANKA_NUM_JOINTS] = fk_body_q[w, :FRANKA_NUM_JOINTS]
    state.body_q.assign(bq)


def rollout_and_cost(model, solver, state_0, state_1, control,
                     actions_seq, ik_solver, per_world_jq,
                     info, K, H, cfg):
    """Rollout K trajectories for H steps, return total costs.

    Args:
        actions_seq: (K, H, action_dim) actions in [-1,1]
        per_world_jq: (K, coord_count) current joint positions
        cfg: MPPIConfig

    Returns:
        (costs, nan_count, t_ik, t_physics): costs (K,), NaN world count, IK time [s], physics time [s]
    """
    sim_dt = DT / RL_SIM_SUBSTEPS
    costs = np.zeros(K, dtype=np.float32)
    jq = per_world_jq.copy()
    t_ik_total = 0.0
    t_physics_total = 0.0
    nan_mask = np.zeros(K, dtype=bool)
    ee_spread_max = 0.0

    for h in range(H):
        ee_pos = get_ee_positions(state_0, info, K)

        pos_delta = actions_seq[:, h, :3] * cfg.pos_action_scale
        target_pos = ee_pos + pos_delta

        t0_ik = time.perf_counter()
        jq_solved = ik_solver.solve(target_pos, jq)

        jq_solved[:, 7] = FINGER_OPEN_POS
        jq_solved[:, 8] = FINGER_OPEN_POS
        jq_solved[:, 9:] = jq[:, 9:]

        fk_body_q = ik_solver.eval_fk_batch(jq_solved)
        t_ik_total += time.perf_counter() - t0_ik

        update_kinematic_bodies(state_0, fk_body_q, info, K)

        ik_ee = get_ee_positions(state_0, info, K)
        valid_idx = ~nan_mask
        if valid_idx.sum() > 1:
            ee_std_3d = float(np.sqrt(np.sum(np.var(ik_ee[valid_idx], axis=0))))
            ee_spread_max = max(ee_spread_max, ee_std_3d)

        t0_phys = time.perf_counter()
        contacts = model.collide(state_0)
        for _ in range(RL_SIM_SUBSTEPS):
            solver.step(state_0, state_1, control, contacts, sim_dt)
            state_0, state_1 = state_1, state_0
        t_physics_total += time.perf_counter() - t0_phys

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

        new_ee = get_ee_positions(state_0, info, K)
        new_cable = compute_cable_center_pos(state_0, info, K)
        dist = np.linalg.norm(new_ee - new_cable, axis=1)
        costs += np.where(nan_mask, 0.0, dist)

        jq = jq_solved.copy()

    n_nan = int(nan_mask.sum())
    if n_nan > 0:
        print(f"  [NaN] {n_nan}/{K} worlds had NaN ({n_nan * 100 // K}%)")
    return costs, n_nan, t_ik_total, t_physics_total, ee_spread_max


# =========================================================================
# Depend E: Warm-start (IK straight-line approach)
# =========================================================================

WARM_START_OFFSET = 0.12  # [m] stop 120mm short of cable center (> success_threshold 80mm)
WARM_START_STEPS = 40     # interpolation steps for approach

def warm_start_approach(model, solver_vbd, state_0, state_1, control,
                        ik_solver, info, K, fk_jq, coord_count, device):
    """Scripted IK straight-line from home to cable near-grasp position.

    Moves EE linearly from home pose to 50mm above cable center.
    Only world 0 is meaningful; all K worlds receive the same arm state.

    Returns:
        per_world_jq: (K, coord_count) joint positions after warm-start
        warmup_dist: final EE-to-cable distance [m]
        n_steps: number of warm-start steps executed
    """
    sim_dt = DT / RL_SIM_SUBSTEPS
    bws = info["bws"]

    ee_start = get_ee_positions(state_0, info, 1)[0]
    cable_center = compute_cable_center_pos(state_0, info, 1)[0]

    direction = cable_center - ee_start
    dist_total = np.linalg.norm(direction)
    if dist_total < WARM_START_OFFSET:
        print(f"  [WARM] Already within offset ({dist_total:.3f}m), skipping")
        per_world_jq = np.tile(fk_jq[:coord_count], (K, 1))
        return per_world_jq, dist_total, 0

    unit_dir = direction / dist_total
    target_dist = dist_total - WARM_START_OFFSET
    ee_target = ee_start + unit_dir * target_dist

    per_world_jq = np.tile(fk_jq[:coord_count], (K, 1))

    print(f"  [WARM] EE {ee_start} → target {ee_target} "
          f"(dist {dist_total:.3f}m → {WARM_START_OFFSET:.3f}m, {WARM_START_STEPS} steps)")

    for s in range(WARM_START_STEPS):
        alpha = (s + 1) / WARM_START_STEPS
        ee_interp = ee_start + (ee_target - ee_start) * alpha

        tgt_all = np.tile(ee_interp[None, :].astype(np.float32), (K, 1))
        jq_solved = ik_solver.solve(tgt_all, per_world_jq)
        jq_solved[:, 7] = FINGER_OPEN_POS
        jq_solved[:, 8] = FINGER_OPEN_POS
        jq_solved[:, 9:] = per_world_jq[:, 9:]

        fk_body_q = ik_solver.eval_fk_batch(jq_solved)
        update_kinematic_bodies(state_0, fk_body_q, info, K)

        contacts = model.collide(state_0)
        for _ in range(RL_SIM_SUBSTEPS):
            solver_vbd.step(state_0, state_1, control, contacts, sim_dt)
            state_0, state_1 = state_1, state_0

        per_world_jq[:] = jq_solved
        solver_vbd.body_q_prev = wp.clone(state_0.body_q)

    final_ee = get_ee_positions(state_0, info, 1)[0]
    final_cable = compute_cable_center_pos(state_0, info, 1)[0]
    final_dist = np.linalg.norm(final_ee - final_cable)
    print(f"  [WARM] Done. Final dist={final_dist:.4f}m")

    return per_world_jq, final_dist, WARM_START_STEPS


# =========================================================================
# C.5  MPPI outer loop
# =========================================================================

def mppi_generate_demos(cfg, device, max_steps=128, n_demos=5, seed=42,
                        no_warmstart=False, no_mppi=False,
                        diag_csv_path="/tmp/mppi_m1_depC_fix_metrics.csv"):
    """Generate demos using MPPI with Hybrid N=4 replanning.

    Returns list of demo dicts with trajectory data.
    """
    K = cfg.K
    H = cfg.H
    rng = np.random.default_rng(seed)

    print(f"\n[MPPI] Building scene K={K}...")
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
    ik_solver = MppiIKSolver(fk_model, K, device)

    state_0 = model.state()
    state_1 = model.state()
    control = model.control()

    coord_count = fk_model.joint_coord_count

    # Save initial state for episode reset
    init_body_q = state_0.body_q.numpy().copy()
    init_body_qd = state_0.body_qd.numpy().copy()

    demos = []

    diag_csv = None
    diag_file = None
    diag_path = diag_csv_path
    diag_file = open(diag_path, "w", newline="")
    diag_csv = csv.writer(diag_file)
    diag_csv.writerow(["episode", "step", "nan_count", "k_eff",
                        "weight_entropy", "weight_mass_valid",
                        "top1_weight", "best_action_nan", "plan_time_s", "dist",
                        "cost_min", "cost_max", "cost_range", "cost_std",
                        "ee_spread_max_mm", "jq_sync"])
    print(f"[DIAG] CSV → {diag_path}")

    for ep in range(n_demos):
        ep_i = ep
        print(f"\n[MPPI] Episode {ep + 1}/{n_demos}")

        # Reset to initial state
        state_0.body_q.assign(init_body_q)
        state_0.body_qd.assign(init_body_qd)
        bws = info["bws"]
        solver_vbd.body_q_prev = wp.clone(state_0.body_q)

        # Phase 1: warm-start approach
        if no_warmstart:
            per_world_jq = np.tile(fk_jq[:coord_count], (K, 1))
            ee0 = get_ee_positions(state_0, info, 1)[0]
            cc0 = compute_cable_center_pos(state_0, info, 1)[0]
            warmup_dist = float(np.linalg.norm(ee0 - cc0))
            warmup_steps = 0
            print(f"  [WARM] SKIPPED (--no-warmstart), dist={warmup_dist:.3f}m")
        else:
            per_world_jq, warmup_dist, warmup_steps = warm_start_approach(
                model, solver_vbd, state_0, state_1, control,
                ik_solver, info, K, fk_jq, coord_count, device)

        traj_ee = []
        traj_actions = []
        traj_dist = []

        step = 0
        success = False

        if no_mppi:
            ee_now = get_ee_positions(state_0, info, 1)[0]
            cc_now = compute_cable_center_pos(state_0, info, 1)[0]
            d = float(np.linalg.norm(ee_now - cc_now))
            traj_ee.append(ee_now.copy())
            traj_actions.append(np.zeros(cfg.action_dim))
            traj_dist.append(d)
            step = 1
            success = d < cfg.success_threshold_m
            print(f"  [NO-MPPI] hold dist={d:.4f}m success={success}")

        while not no_mppi and step < max_steps:
            # Copy world 0 to all for planning rollout
            copy_world0_to_all(state_0, bws, info["bodies_per_world"], K, device,
                               solver_vbd=solver_vbd)
            per_world_jq[:] = per_world_jq[0:1]

            # Save state for restoration after planning rollout
            saved_q = state_0.body_q.numpy().copy()
            saved_qd = state_0.body_qd.numpy().copy()
            saved_bq_prev = solver_vbd.body_q_prev.numpy().copy()
            saved_jq = per_world_jq.copy()

            # C.1: Sample action sequences
            actions = sample_action_sequences(
                K, H, cfg.action_dim, cfg.noise_sigma, cfg.noise_correlation, rng)

            # C.2: Rollout and compute costs
            t0_plan = time.perf_counter()
            costs, nan_count, t_ik, t_phys, ee_spread_max = rollout_and_cost(
                model, solver_vbd, state_0, state_1, control,
                actions, ik_solver, per_world_jq, info, K, H, cfg)
            t_plan = time.perf_counter() - t0_plan
            if step == 0:
                print(f"  [TIMING] plan={t_plan:.2f}s (IK={t_ik:.2f}s, "
                      f"physics={t_phys:.2f}s, other={t_plan - t_ik - t_phys:.2f}s)")

            # C.3: MPPI weights
            weights = mppi_weights(costs, cfg.temperature_lambda)

            # Weighted mean action sequence
            best_actions = np.einsum('k,kha->ha', weights, actions)  # (H, action_dim)

            # Cost statistics (valid worlds only)
            valid_costs = costs[costs < 1e5]
            if len(valid_costs) > 1:
                c_min = float(valid_costs.min())
                c_max = float(valid_costs.max())
                c_range = c_max - c_min
                c_std = float(valid_costs.std())
            else:
                c_min = c_max = c_range = c_std = 0.0

            # Diagnostic metrics
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
                                   f"{t_plan:.3f}", "",
                                   f"{c_min:.4f}", f"{c_max:.4f}",
                                   f"{c_range:.4f}", f"{c_std:.4f}",
                                   f"{ee_spread_max * 1000:.2f}", 1])
            if step % 16 == 0:
                print(f"  [DIAG] step={step} nan={nan_count}/{K} k_eff={k_eff} "
                      f"entropy={w_entropy:.2f} mass={w_mass_valid:.4f} "
                      f"top1={top1_w:.4f} ba_nan={ba_has_nan} "
                      f"cost_range={c_range:.4f} cost_std={c_std:.4f} "
                      f"ee_spread={ee_spread_max * 1000:.1f}mm")

            # Restore state (planning was exploratory)
            state_0.body_q.assign(saved_q)
            state_0.body_qd.assign(saved_qd)
            solver_vbd.body_q_prev.assign(saved_bq_prev)
            per_world_jq = saved_jq.copy()

            # Execute first REPLAN_INTERVAL steps on world 0 only
            n_exec = min(REPLAN_INTERVAL, max_steps - step)
            sim_dt = DT / RL_SIM_SUBSTEPS

            for h in range(n_exec):
                # Apply action to world 0
                bq = state_0.body_q.numpy()
                ee_pos = bq[bws[0] + EE_BODY_OFFSET, :3]
                pos_delta = best_actions[h, :3] * cfg.pos_action_scale
                target_pos = ee_pos + pos_delta

                # Single IK solve (reuse batch solver, world 0 only)
                jq_all = np.tile(per_world_jq[0:1], (K, 1))
                tgt_all = np.tile(target_pos[None, :], (K, 1))
                jq_solved = ik_solver.solve(tgt_all, jq_all)
                jq_solved[:, 7] = FINGER_OPEN_POS
                jq_solved[:, 8] = FINGER_OPEN_POS
                jq_solved[:, 9:] = jq_all[:, 9:]

                # FK → update kinematic bodies (all worlds get same state)
                fk_body_q = ik_solver.eval_fk_batch(jq_solved)
                update_kinematic_bodies(state_0, fk_body_q, info, K)

                # Physics step
                contacts = model.collide(state_0)
                for _ in range(RL_SIM_SUBSTEPS):
                    solver_vbd.step(state_0, state_1, control, contacts, sim_dt)
                    state_0, state_1 = state_1, state_0

                per_world_jq[0] = jq_solved[0]

                # Record trajectory
                new_ee = get_ee_positions(state_0, info, 1)[0]
                cable_ctr = compute_cable_center_pos(state_0, info, 1)[0]
                dist = np.linalg.norm(new_ee - cable_ctr)

                traj_ee.append(new_ee.copy())
                traj_actions.append(best_actions[h].copy())
                traj_dist.append(dist)

                step += 1

            # Check terminal success
            if traj_dist and traj_dist[-1] < cfg.success_threshold_m:
                success = True
                print(f"  SUCCESS at step {step}, dist={traj_dist[-1]:.4f}m")
                break

        if not success:
            print(f"  FAILED at step {step}, final dist={traj_dist[-1]:.4f}m"
                  if traj_dist else "  FAILED (no steps)")

        demo = {
            "ee_pos": np.array(traj_ee),
            "actions": np.array(traj_actions),
            "distance": np.array(traj_dist),
            "success": success,
            "steps": step,
            "warmup_dist": warmup_dist,
            "warmup_steps": warmup_steps,
        }
        demos.append(demo)

    if diag_file is not None:
        diag_file.close()
        print(f"[DIAG] CSV written → {diag_path}")

    return demos


def save_demos_hdf5(demos, cfg, output_path):
    """Save demos to HDF5."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    n_success = sum(1 for d in demos if d["success"])
    with h5py.File(output_path, "w") as f:
        meta = f.create_group("metadata")
        meta.attrs["generator"] = "mppi"
        meta.attrs["K"] = cfg.K
        meta.attrs["H"] = cfg.H
        meta.attrs["temperature_lambda"] = cfg.temperature_lambda
        meta.attrs["noise_sigma"] = cfg.noise_sigma
        meta.attrs["noise_correlation"] = cfg.noise_correlation
        meta.attrs["success_threshold_m"] = cfg.success_threshold_m
        meta.attrs["success_eval"] = "terminal"
        meta.attrs["newton_dt"] = cfg.newton_dt
        meta.attrs["sim_substeps"] = cfg.sim_substeps
        meta.attrs["replan_interval"] = REPLAN_INTERVAL
        meta.attrs["n_demos"] = len(demos)
        meta.attrs["n_success"] = n_success

        for i, demo in enumerate(demos):
            g = f.create_group(f"episode_{i}")
            g.create_dataset("ee_pos", data=demo["ee_pos"])
            g.create_dataset("action_delta", data=demo["actions"])
            g.create_dataset("distance", data=demo["distance"])
            g.attrs["success"] = demo["success"]
            g.attrs["steps"] = demo["steps"]
            g.attrs["warmup_dist"] = demo["warmup_dist"]
            g.attrs["warmup_steps"] = demo["warmup_steps"]

    print(f"[HDF5] Saved {len(demos)} demos ({n_success} success) to {output_path}")


# =========================================================================
# Main: 3x3 sweep
# =========================================================================

def main():
    parser = argparse.ArgumentParser(description="MPPI demo generation (M1)")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--sweep", action="store_true", help="Run 3x3 lambda/sigma sweep")
    parser.add_argument("--n_demos", type=int, default=5)
    parser.add_argument("--max_steps", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output_dir", type=str, default="data/mppi_demos")
    parser.add_argument("--no-warmstart", action="store_true", help="Skip warm-start (verify A)")
    parser.add_argument("--no-mppi", action="store_true", help="Skip MPPI (verify B)")
    parser.add_argument("--diag-csv", type=str,
                        default="/tmp/mppi_m1_depC_fix_metrics.csv")
    args = parser.parse_args()

    wp.init()
    wp.set_device(args.device)

    if args.sweep:
        lambdas = [0.3, 0.5, 1.0]
        sigmas = [0.2]
        sweep_results = []

        for lam in lambdas:
            for sig in sigmas:
                print(f"\n{'=' * 60}")
                print(f"  SWEEP: lambda={lam}, sigma={sig}")
                print(f"{'=' * 60}")

                cfg = MPPIConfig()
                cfg.temperature_lambda = lam
                cfg.noise_sigma = sig
                cfg.device = args.device

                t0 = time.perf_counter()
                sweep_csv = f"/tmp/mppi_sweep_lam{lam}_sig{sig}.csv"
                demos = mppi_generate_demos(
                    cfg, args.device,
                    max_steps=args.max_steps,
                    n_demos=args.n_demos,
                    seed=args.seed,
                    diag_csv_path=sweep_csv,
                )
                elapsed = time.perf_counter() - t0

                n_success = sum(1 for d in demos if d["success"])
                final_dists = [d["distance"][-1] for d in demos if len(d["distance"]) > 0]
                mean_dist = np.mean(final_dists) if final_dists else float("nan")

                sweep_results.append({
                    "lambda": lam,
                    "sigma": sig,
                    "success_rate": n_success / len(demos),
                    "mean_terminal_error": round(float(mean_dist), 4),
                    "wall_clock_s": round(elapsed, 1),
                })

                h5_path = os.path.join(
                    args.output_dir, f"demos_l{lam}_s{sig}.hdf5")
                save_demos_hdf5(demos, cfg, h5_path)

        # Sweep summary
        print(f"\n{'=' * 70}")
        print(f"  SWEEP RESULTS")
        print(f"{'=' * 70}")
        print(f"  {'lambda':>8} | {'sigma':>8} | {'success':>8} | "
              f"{'mean_err':>10} | {'time_s':>8}")
        print(f"  {'-' * 8}-+-{'-' * 8}-+-{'-' * 8}-+-{'-' * 10}-+-{'-' * 8}")
        for r in sweep_results:
            print(f"  {r['lambda']:>8.1f} | {r['sigma']:>8.2f} | "
                  f"{r['success_rate']:>8.1%} | "
                  f"{r['mean_terminal_error']:>10.4f} | {r['wall_clock_s']:>8.1f}")

        csv_path = "/tmp/mppi_m1_depC_sweep.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["lambda", "sigma", "success_rate",
                               "mean_terminal_error", "wall_clock_s"])
            writer.writeheader()
            writer.writerows(sweep_results)
        print(f"\n  CSV: {csv_path}")

        best = min(sweep_results, key=lambda r: r["mean_terminal_error"])
        print(f"\n  BEST: lambda={best['lambda']}, sigma={best['sigma']}, "
              f"err={best['mean_terminal_error']:.4f}m, "
              f"success={best['success_rate']:.0%}")

    else:
        cfg = MPPIConfig()
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
