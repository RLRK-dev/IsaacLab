# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Newton VBD Unclamp RL environment -- Multi-world RSL-RL VecEnv.

Independent Unclamp skill. Precondition: IC completed + half-unclamp (scripted).
Task: Open left finger from HALF_OPEN to FULL_OPEN while tracking cable position
with EE movement. Cable must remain seated in groove throughout.

Obs (42D — unified with GC/Clamp/AR for SkillAdapter):
    [0:3]   Right clamp position XYZ [m]
    [3:7]   Right clamp quaternion (qx, qy, qz, qw), w >= 0
    [7]     Right finger opening (j7 + j8) [m]
    [8:11]  Left clamp position XYZ [m]
    [11:15] Left clamp quaternion (qx, qy, qz, qw), w >= 0
    [15]    Left finger opening (j7 + j8) [m]
    [16:19] Cable groove segment position XYZ [m]
    [19:23] Cable groove segment quaternion (qx, qy, qz, qw), w >= 0
    [23:26] Groove center position XYZ [m]
    [26:30] Clip quaternion (qx, qy, qz, qw), w >= 0
    [30:33] Right orientation error (axis-angle) [rad]
    [33:36] Right position error [m]
    [36:39] Left orientation error (axis-angle) [rad]
    [39:42] Left position error [m]

Action (4D):
    [0]     Left finger Δopening * FINGER_STEP_SIZE [m]
    [1:4]   Left EE ΔXYZ * POS_ACTION_SCALE [m]

Right arm: passive (OPEN fingers, holds initial position throughout episode).

Reward: multiplicative (finger_progress × cable_seated) + R_step + R_task + R_penalty.
Success: finger_fully_open ∧ seated(groove_n, clip_n) ∧ sustained(K=5).

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/train_unclamp.py --world-count 4
"""

import math
import os
import sys
import time

import newton
import numpy as np
import torch
import warp as wp
from newton._src.sim.ik.ik_common import eval_fk_batched
from newton.ik import IKObjectiveJointLimit, IKObjectivePosition, IKObjectiveRotation, IKSolver
from rsl_rl.env import VecEnv

# Import scene building functions from test_newton_clip_routing
_script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
sys.path.insert(0, _script_dir)
import test_newton_clip_routing as _tncr

# Import shared utilities from newton_skill_env_base (S2: dedup)
from newton_skill_env_base import (
    EE_BODY_OFFSET,
    FRANKA_NUM_JOINTS,
    IK_ITERATIONS_RL,
    IK_STEP_SIZE,
    RL_SIM_DT,
    RL_SIM_SUBSTEPS,
    ROBOT_BODIES_PER_ARM,
    ROBOT_BODY_COUNT,
    SIM_DT,
    compute_clamp_pos,
    compute_ori_error_axis_angle,
    find_nearest_cable_point,
    make_solver,
    normalize_quat_w_positive,
    quat_distance,
    temporal_quat_consistency,
)
from test_newton_clip_routing import (
    GRAVITY,
    add_cable_rod,
    add_kinematic_arm,
    build_fk_model,
)

# Import task_config (SSOT)
_config_dir = os.environ.get(
    "THREAD_CONFIG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs"),
)
sys.path.insert(0, _config_dir)
from cable_orientation_utils import BASE_HAND_DOWN_QUAT, compute_hand_quat_for_cable
from task_config import (
    CABLE_RADIUS,
    CABLE_SEG_LEN,
    CABLE_SEGMENTS,
    CLIP1_X,
    CLIP1_Y,
    CLIP1_Z,
    CLIP_BASE_HEIGHT,
    FINGER_HALF_OPEN_POS,
    FINGER_LOCAL,
    FINGER_OPEN_POS,
    FINGER_STEP_SIZE,
    GRASP_X,
    GRASP_Z,
    GRIP_HALF_SPAN,
    GRIPPER_DRIVER_JOINT_IDX,
    GRIPPER_JOINT_RANGE,
    GRIPPER_PAD_BODY_IDX,
    GROOVE_BODIES_MIN,
    GROOVE_CENTER_Z,
    JOINTS_PER_ARM,
    K_UNCLAMP,
    LIFT_Z,
    NJMAX,
    PUSH_Z,
    SIM_SUBSTEPS,
    T_GROOVE,
    T_SEAT,
    TABLE_HEIGHT,
    UNCLAMP_TERMINAL_STEPS,
)

# Constants (env-specific, not in base)
IK_ITERATIONS_INIT = 100

# IK rotation targets: hand down
_cos_pi8 = math.cos(math.pi / 8)
_sin_pi8 = math.sin(math.pi / 8)

# Groove check radius
GROOVE_CHECK_RADIUS = CABLE_SEG_LEN + CABLE_RADIUS  # 19mm

# Dynamic finger spring parameters (aligned with other envs)
FINGER_SPRING_KE = 10000.0
FINGER_SPRING_KD = 500.0
FINGER_DYNAMIC_INV_MASS = 20.0
FINGER_DYNAMIC_INV_INERTIA = 100.0

# Finger opening sums (j7 + j8 for each state)
HALF_OPEN_SUM = 2 * FINGER_HALF_OPEN_POS  # 0.012
FULL_OPEN_SUM = 2 * FINGER_OPEN_POS  # 0.08

# Groove spring: simulates clip snap retention (physical snap impossible in VBD)
# Applies restoring force toward groove center for cable bodies within groove radius.
# XZ only (Y = cable tangent direction, unconstrained).
GROOVE_SPRING_KE = 50.0  # [N/m] — 1mm displacement → 0.05N (seg_mass ~0.83g)
GROOVE_SPRING_KD = 0.5  # [N·s/m] — near critical damping
GROOVE_SPRING_RADIUS = 0.025  # 25mm — covers VBD settle drift (~20mm observed)


# =========================================================================
# Unclamp Environment
# =========================================================================


class NewtonUnclampEnv(VecEnv):
    """RSL-RL VecEnv for Unclamp — multi-world with replicate().

    Precondition: IC completed + half-unclamp (L=HALF_OPEN, R=OPEN, cable in groove).
    Task: Open left finger fully while tracking cable position with EE.

    Observation (42D per world — unified with GC/Clamp/AR for SkillAdapter):
        [0:7]   Right clamp pose (pos XYZ + quat XYZW) [m] — passive
        [7]     Right finger opening (j7+j8) [m] — constant OPEN
        [8:15]  Left clamp pose (pos XYZ + quat XYZW) [m] — active
        [15]    Left finger opening (j7+j8) [m]
        [16:23] Cable groove segment pose (pos XYZ + quat XYZW)
        [23:30] Groove center pose (pos XYZ + clip quat XYZW)
        [30:36] Right arm errors (ori axis-angle + pos) [rad, m]
        [36:42] Left arm errors (ori axis-angle + pos) [rad, m]

    Action (4D per world):
        [0]     Left finger Δopening * FINGER_STEP_SIZE [m]
        [1:4]   Left EE ΔXYZ * POS_ACTION_SCALE [m]

    Right arm: passive (OPEN, holds initial position).
    """

    # Action scaling
    POS_ACTION_SCALE = 0.015  # 15mm per RL step
    FINGER_ACTION_SCALE = FINGER_STEP_SIZE  # 1mm per RL step
    MAX_EPISODE_STEPS = UNCLAMP_TERMINAL_STEPS  # 100
    PHYSICS_STEPS_PER_RL = 10
    EXPLOSION_DIST_THRESH = 1.0
    INIT_XY_NOISE = 0.002  # ±2mm initial position noise

    # Target cable segment: groove-nearest (±1 window)
    GRIP_SEG_WINDOW = 1

    # Reward: multiplicative (finger_progress × cable_seated)
    REWARD_MODE = "multiplicative"
    RANGE_SEATED = 0.005  # 5mm: seated distance exp decay [m]
    RANGE_ORI = 0.5  # 0.5 rad: seated ori exp decay
    PROGRESS_SCALE = 2.0
    PROGRESS_W_FINGER = 0.3  # Independent finger weight
    PROGRESS_W_SEATED = 0.3  # Independent cable-seated weight
    PROGRESS_W_COUPLED = 0.4  # Coupled finger × seated weight
    R_STEP_BONUS = 5.0  # Finger fully open AND cable seated (one-time)
    R_TASK_BONUS = 20.0  # Sustained success
    R_PENALTY = -0.01  # Per-step
    R_DROP = -5.0  # Cable fell out of groove (terminal)

    # Success condition
    FINGER_OPEN_THRESH_SUM = 2 * (FINGER_OPEN_POS - 0.003)  # 0.074 (3mm tolerance per finger)
    SEATED_POS_THRESH = T_GROOVE  # 3mm
    SEATED_ORI_THRESH = T_SEAT  # cos > 0.85
    SUSTAIN_STEPS = K_UNCLAMP  # K_UNCLAMP RL steps (design doc: 5)
    MIN_GROOVE_BODIES = GROOVE_BODIES_MIN  # 2

    # Cable drop: segment Z below table
    DROP_Z_THRESH = TABLE_HEIGHT - 0.02  # 20mm below table

    # Clip C1 pose (constant)
    CLIP1_POS = np.array([CLIP1_X, CLIP1_Y, CLIP1_Z], dtype=np.float32)
    CLIP1_QUAT_XYZW = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    GROOVE_CENTER_POS = np.array([CLIP1_X, CLIP1_Y, GROOVE_CENTER_Z], dtype=np.float32)

    # Groove target quat: cable tangent along Y when seated in C1 groove
    # Must match GripEnv (BASE_HAND_DOWN_QUAT ≈ [0.924, 0.383, 0, 0])
    GROOVE_TARGET_QUAT = normalize_quat_w_positive(BASE_HAND_DOWN_QUAT.copy())

    # Precondition: arms at push height near clip
    UNCLAMP_EE_LEFT = np.array([CLIP1_X, CLIP1_Y - GRIP_HALF_SPAN, PUSH_Z], dtype=np.float32)
    UNCLAMP_EE_RIGHT = np.array([CLIP1_X, CLIP1_Y + GRIP_HALF_SPAN, PUSH_Z], dtype=np.float32)

    # Cache directory
    CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "rl_unclamp_cache")
    PRECONDITION_CACHE_OVERRIDE = None
    TERMINAL_STEPS_OVERRIDE = None

    def __init__(self, world_count=4, device="cuda:0", cfg=None):
        self.num_envs = world_count
        self.num_actions = 4
        self._total_env_steps = 0
        terminal = self.TERMINAL_STEPS_OVERRIDE or self.MAX_EPISODE_STEPS
        self.max_episode_length = terminal
        self.device = device
        self.cfg = cfg or {}
        self._world_count = world_count

        self.episode_length_buf = torch.zeros(world_count, dtype=torch.long, device=device)
        self._groove_seg_indices = None  # [world_count, n_segs]
        self._success_sustain_count = np.zeros(world_count, dtype=np.int32)
        self._step_bonus_given = np.zeros(world_count, dtype=bool)
        self._episode_count = 0

        # Per-world EE targets (left only moves; right holds initial position)
        self._ee_target_left = np.zeros((world_count, 3), dtype=np.float32)
        self._ee_target_right = np.zeros((world_count, 3), dtype=np.float32)
        self._ee_quat_left = np.zeros((world_count, 4), dtype=np.float32)
        self._ee_quat_right = np.zeros((world_count, 4), dtype=np.float32)

        # Per-world left finger target position (per joint, NOT sum)
        self._finger_target_left = np.full(world_count, FINGER_HALF_OPEN_POS, dtype=np.float32)

        # Temporal quat consistency (both arms for 42D obs)
        _id4 = np.array([0, 0, 0, 1], dtype=np.float32)
        self._prev_clamp_r_quat = np.tile(_id4, (world_count, 1))
        self._prev_clamp_l_quat = np.tile(_id4, (world_count, 1))
        self._prev_seg_quat = np.tile(_id4, (world_count, 1))

        # Override device for Newton
        os.environ["NEWTON_DEVICE"] = device
        _tncr.DEVICE = device

        print(f"[UnclampEnv] Initializing: {world_count} worlds on {device}")
        t0 = time.perf_counter()

        self._build_model()

        if self._load_precondition_cache():
            self._restore_from_cache()
        else:
            self._setup_unclamp_precondition()
            self._save_precondition_cache()

        self._init_dynamic_fingers()
        self._init_batched_ik_solver()

        print(
            f"[UnclampEnv] Ready in {time.perf_counter() - t0:.1f}s. "
            f"obs={self.num_obs}, act={self.num_actions}, worlds={world_count}"
        )

    # =========================================================================
    # Model Construction
    # =========================================================================

    def _build_model(self):
        print("[UnclampEnv] Building FK model...")
        self._fk_model = build_fk_model()
        self._fk_state = self._fk_model.state()

        fk_jq = self._fk_state.joint_q.numpy()
        fk_tp = self._fk_model.joint_target_pos.numpy()
        fk_jq[:] = fk_tp[:]
        # Left: HALF_OPEN (precondition), Right: OPEN (passive)
        fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_HALF_OPEN_POS
        fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_HALF_OPEN_POS
        fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
        fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS
        self._fk_state.joint_q.assign(fk_jq)
        newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)

        self._per_world_fk_jq = np.tile(fk_jq, (self._world_count, 1))
        self._build_multiworld_physics()

    def _build_multiworld_physics(self):
        """Build proto with robot arms + cable + target clip, then replicate."""
        print("[UnclampEnv] Building world prototype...")
        proto = newton.ModelBuilder()

        # Robot arms (kinematic bodies)
        left_info = add_kinematic_arm(
            proto,
            self._fk_model,
            self._fk_state,
            arm_body_offset=0,
            label_prefix="left",
        )
        right_info = add_kinematic_arm(
            proto,
            self._fk_model,
            self._fk_state,
            arm_body_offset=FRANKA_NUM_JOINTS,
            label_prefix="right",
        )
        left_body_start, left_shape_start, left_shape_end, left_fv = left_info
        right_body_start, right_shape_start, right_shape_end, right_fv = right_info
        all_finger_visual = set(left_fv + right_fv)

        # Contact filtering: non-pad bodies VISIBLE only, pad followers (GRIPPER_PAD_BODY_IDX) COLLIDE
        for arm_ss, arm_se, arm_bs in [
            (left_shape_start, left_shape_end, left_body_start),
            (right_shape_start, right_shape_end, right_body_start),
        ]:
            for si in range(arm_ss, arm_se):
                local = proto.shape_body[si] - arm_bs
                if local not in GRIPPER_PAD_BODY_IDX or si in all_finger_visual:
                    proto.shape_flags[si] = 1
                elif local in GRIPPER_PAD_BODY_IDX:
                    proto.shape_flags[si] = 0x6

        # Cable (Cosserat Rod)
        cable_half_len = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
        cable_y_start = CLIP1_Y - cable_half_len
        cable_start = (GRASP_X, cable_y_start, TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS)
        cable_shape_start_idx = proto.shape_count
        cable_bodies_proto, cable_joints_proto = add_cable_rod(
            proto,
            start_pos=cable_start,
            direction=(0, 1, 0),
        )
        cable_shape_end_idx = proto.shape_count
        self._cable_bodies_per_world = len(cable_bodies_proto)
        self._cable_body_offset = cable_bodies_proto[0]

        # Cable-arm filter pairs
        for cable_si in range(cable_shape_start_idx, cable_shape_end_idx):
            for arm_ss, arm_se, arm_bs in [
                (left_shape_start, left_shape_end, left_body_start),
                (right_shape_start, right_shape_end, right_body_start),
            ]:
                for arm_si in range(arm_ss, arm_se):
                    local = proto.shape_body[arm_si] - arm_bs
                    if local not in GRIPPER_PAD_BODY_IDX:
                        proto.add_shape_collision_filter_pair(cable_si, arm_si)

        self._bodies_per_world = proto.body_count

        # --- Scene: global entities + replicate ---
        print(f"[UnclampEnv] Building scene ({self._world_count} worlds)...")
        scene = newton.ModelBuilder(gravity=GRAVITY)
        scene.add_ground_plane()

        # Table
        table_cfg = newton.ModelBuilder.ShapeConfig()
        table_cfg.ke = 500.0
        table_cfg.kd = 100.0
        table_cfg.mu = 1.0
        table_cfg.gap = 0.002
        table_xform = wp.transform((0.3, -0.05, TABLE_HEIGHT - 0.005), wp.quat_identity())
        scene.add_shape_box(body=-1, hx=0.35, hy=0.35, hz=0.005, xform=table_xform, cfg=table_cfg)

        # Target clip at C1 (V-groove geometry — same as InsertClipEnv)
        clip_cfg = newton.ModelBuilder.ShapeConfig()
        clip_cfg.ke = 2500.0
        clip_cfg.kd = 100.0
        clip_cfg.mu = 1.0
        clip_cfg.gap = 0.001
        clip_parts = [
            (0, 0, 0.0025, 0.020, 0.015, 0.0025),
            (-0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),
            (+0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),
            (-0.013, 0, 0.025, 0.002, 0.015, 0.005),
            (+0.013, 0, 0.025, 0.002, 0.015, 0.005),
        ]
        for dx, dy, dz, hx, hy, hz in clip_parts:
            xf = wp.transform(
                (CLIP1_X + dx, CLIP1_Y + dy, TABLE_HEIGHT + dz),
                wp.quat_identity(),
            )
            idx = scene.add_shape_box(
                body=-1,
                xform=xf,
                hx=hx,
                hy=hy,
                hz=hz,
                cfg=clip_cfg,
            )
            scene.shape_flags[idx] = 0x6

        # Replicate
        scene.replicate(proto, world_count=self._world_count)
        scene.color()
        self._model = scene.finalize(device=self.device, requires_grad=False)

        # World index arrays
        self._bws = self._model.body_world_start.numpy()
        self._jws = self._model.joint_world_start.numpy()

        # Zero inv_mass for robot bodies (kinematic)
        inv_mass = self._model.body_inv_mass.numpy()
        inv_inertia = self._model.body_inv_inertia.numpy()
        for w in range(self._world_count):
            start = self._bws[w]
            for bi in range(ROBOT_BODY_COUNT):
                inv_mass[start + bi] = 0.0
                inv_inertia[start + bi] = np.zeros(3, dtype=np.float32)
        self._model.body_inv_mass = wp.array(inv_mass, dtype=self._model.body_inv_mass.dtype, device=self.device)
        self._model.body_inv_inertia = wp.array(
            inv_inertia, dtype=self._model.body_inv_inertia.dtype, device=self.device
        )

        # Finger BOX collision / MESH visual flags
        model_sflags = self._model.shape_flags.numpy()
        model_stypes = self._model.shape_type.numpy()
        model_sbodies = self._model.shape_body.numpy()
        for si in range(len(model_stypes)):
            bi = model_sbodies[si]
            if bi < 0:
                continue
            for w in range(self._world_count):
                ws, we = self._bws[w], self._bws[w + 1]
                if ws <= bi < we:
                    local = bi - ws
                    local_l = local - 0
                    local_r = local - ROBOT_BODIES_PER_ARM
                    if local_l in GRIPPER_PAD_BODY_IDX or local_r in GRIPPER_PAD_BODY_IDX:
                        if model_stypes[si] == 7:  # BOX = collision
                            model_sflags[si] = 0x6
                        elif model_stypes[si] == 8:  # MESH = visual
                            model_sflags[si] = 0x1
                    break
        self._model.shape_flags = wp.array(model_sflags, dtype=self._model.shape_flags.dtype, device=self.device)

        # solver via the SOLVER_BACKEND factory (default "vbd" => byte-identical to the prior SolverVBD)
        self._solver = make_solver(self._model)
        self._model.rigid_contact_max = NJMAX

        # Physics states
        self._state_0 = self._model.state()
        self._state_1 = self._model.state()
        self._control = self._model.control()
        self._contacts = self._model.contacts()

        # Cable body indices per world
        self._cable_bodies = []
        for w in range(self._world_count):
            start = self._bws[w] + self._cable_body_offset
            self._cable_bodies.append(list(range(start, start + self._cable_bodies_per_world)))

    # =========================================================================
    # Precondition: synthetic (cable in groove + arms at push height)
    # =========================================================================

    def _setup_unclamp_precondition(self):
        """Construct synthetic initial state: cable in groove, L=HALF_OPEN, R=OPEN.

        Steps:
        1. IK: move both arms to push positions near clip
        2. Teleport cable bodies to groove height at CLIP_X
        3. L finger = HALF_OPEN, R finger = OPEN
        4. Broadcast FK to physics
        5. VBD settle
        """
        print("[UnclampEnv] Setting up Unclamp precondition (synthetic)...")

        # Step 1: IK solve
        jq_target = self._solve_ik_single(tuple(self.UNCLAMP_EE_LEFT), tuple(self.UNCLAMP_EE_RIGHT))
        if np.any(np.isnan(jq_target)):
            raise RuntimeError("[UnclampEnv] IK failed for unclamp precondition")

        # Finger positions: L=HALF_OPEN, R=OPEN
        jq_target[GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_HALF_OPEN_POS
        jq_target[GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_HALF_OPEN_POS
        jq_target[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
        jq_target[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS

        # Apply to FK
        self._fk_state.joint_q.assign(jq_target)
        newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)
        for w in range(self._world_count):
            self._per_world_fk_jq[w] = jq_target.copy()

        self._broadcast_fk_to_all_worlds()

        # Step 2: Teleport cable into groove
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        cable_half_len = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
        cable_y_start = CLIP1_Y - cable_half_len

        for w in range(self._world_count):
            for i, bi in enumerate(self._cable_bodies[w]):
                seg_y = cable_y_start + i * CABLE_SEG_LEN
                bq[bi, 0] = CLIP1_X
                bq[bi, 1] = seg_y
                bq[bi, 2] = GROOVE_CENTER_Z  # Cable seated in groove
                bq[bi, 3:7] = [0.0, 0.0, 0.0, 1.0]
        self._state_0.body_q.assign(bq)

        # Zero velocities
        bqd = self._state_0.body_qd.numpy()
        for w in range(self._world_count):
            for bi in self._cable_bodies[w]:
                bqd[bi, :] = 0.0
        self._state_0.body_qd.assign(bqd)
        if hasattr(self._solver, "body_q_prev") and self._solver.body_q_prev is not None:
            self._solver.body_q_prev.assign(bq)

        # Step 3: Reset Dahl friction state before settle
        if hasattr(self._solver, "enable_dahl_friction") and self._solver.enable_dahl_friction:
            if self._solver.joint_C_fric is not None:
                self._solver.joint_C_fric.zero_()
            if self._solver.joint_sigma_prev is not None:
                self._solver.joint_sigma_prev.zero_()

        # Step 4: VBD settle
        print("[UnclampEnv] VBD settling (100 frames)...")
        for _ in range(100):
            self._broadcast_fk_to_all_worlds()
            self._physics_step_all()

        # Zero cable velocities after settle (VBD settle leaves residual
        # oscillation velocities that cause cable explosion on first RL step).
        wp.synchronize()
        bqd_post = self._state_0.body_qd.numpy()
        bq_post = self._state_0.body_q.numpy()
        for w in range(self._world_count):
            for bi in self._cable_bodies[w]:
                bqd_post[bi, :] = 0.0
        self._state_0.body_qd.assign(bqd_post)
        if hasattr(self._solver, "body_q_prev") and self._solver.body_q_prev is not None:
            self._solver.body_q_prev.assign(bq_post)

        # Verify
        cable_z_w0 = np.mean(bq_post[self._cable_bodies[0], 2])
        print(
            f"[UnclampEnv] Post-settle cable Z: {cable_z_w0:.4f} "
            f"(groove: {GROOVE_CENTER_Z:.4f}, "
            f"delta: {(cable_z_w0 - GROOVE_CENTER_Z) * 1000:.1f}mm)"
        )

        # Compute groove segment indices
        self._groove_seg_indices = self._compute_groove_seg_indices(bq_post)

        # Save settled state
        self._settled_body_q = bq_post.copy()
        self._settled_body_qd = self._state_0.body_qd.numpy().copy()
        self._settled_fk_jq = self._fk_state.joint_q.numpy().copy()
        self._settled_inv_mass = self._model.body_inv_mass.numpy().copy()
        self._settled_inv_inertia = self._model.body_inv_inertia.numpy().copy()

        wp.synchronize()
        fk_bq = self._fk_state.body_q.numpy()
        self._settled_ee_l_pos = fk_bq[EE_BODY_OFFSET][:3].copy()
        self._settled_ee_l_quat = fk_bq[EE_BODY_OFFSET][3:7].copy()
        self._settled_ee_r_pos = fk_bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3].copy()
        self._settled_ee_r_quat = fk_bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][3:7].copy()

        for w in range(self._world_count):
            self._ee_target_left[w] = self._settled_ee_l_pos.copy()
            self._ee_target_right[w] = self._settled_ee_r_pos.copy()
            self._ee_quat_left[w] = self._settled_ee_l_quat.copy()
            self._ee_quat_right[w] = self._settled_ee_r_quat.copy()

        print("[UnclampEnv] Precondition complete.")

    def _compute_groove_seg_indices(self, bq):
        """Compute cable segment indices near groove for each world."""
        indices = []
        for w in range(self._world_count):
            cable_pos = bq[self._cable_bodies[w], :3]
            dists = np.linalg.norm(cable_pos[:, :2] - np.array([CLIP1_X, CLIP1_Y]), axis=1)
            center_idx = int(np.argmin(dists))
            lo = max(0, center_idx - self.GRIP_SEG_WINDOW)
            hi = min(len(cable_pos) - 1, center_idx + self.GRIP_SEG_WINDOW)
            indices.append(np.arange(lo, hi + 1))
        return indices

    # =========================================================================
    # Cache I/O
    # =========================================================================

    def _get_cache_path(self):
        if self.PRECONDITION_CACHE_OVERRIDE:
            return self.PRECONDITION_CACHE_OVERRIDE
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        return os.path.join(self.CACHE_DIR, f"unclamp_w{self._world_count}.npz")

    def _save_precondition_cache(self):
        path = self._get_cache_path()
        wp.synchronize()
        data = {
            "body_q": self._settled_body_q,
            "body_qd": self._settled_body_qd,
            "fk_jq": self._settled_fk_jq,
            "inv_mass": self._settled_inv_mass,
            "inv_inertia": self._settled_inv_inertia,
            "world_count": np.array([self._world_count], dtype=np.int32),
            "body_count": np.array([self._model.body_count], dtype=np.int32),
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        np.savez_compressed(path, **data)
        size_kb = os.path.getsize(path) / 1024
        print(f"[UnclampEnv] Cache saved: {path} ({size_kb:.1f} KB)")

    def _load_precondition_cache(self):
        path = self._get_cache_path()
        if not os.path.exists(path):
            print(f"[UnclampEnv] No cache at {path}")
            return False
        try:
            data = np.load(path)
            if int(data["world_count"][0]) != self._world_count:
                print("[UnclampEnv] Cache world_count mismatch")
                return False
            if int(data["body_count"][0]) != self._model.body_count:
                print("[UnclampEnv] Cache body_count mismatch")
                return False
            self._settled_body_q = data["body_q"]
            self._settled_body_qd = data["body_qd"]
            self._settled_fk_jq = data["fk_jq"]
            self._settled_inv_mass = data["inv_mass"]
            self._settled_inv_inertia = data["inv_inertia"]
            print(f"[UnclampEnv] Loaded cache from {path}")
            return True
        except Exception as e:
            print(f"[UnclampEnv] Cache load failed: {e}")
            return False

    def _restore_from_cache(self):
        self._state_0.body_q.assign(self._settled_body_q)
        self._state_0.body_qd.assign(self._settled_body_qd)
        self._model.body_inv_mass = wp.array(
            self._settled_inv_mass, dtype=self._model.body_inv_mass.dtype, device=self.device
        )
        self._model.body_inv_inertia = wp.array(
            self._settled_inv_inertia, dtype=self._model.body_inv_inertia.dtype, device=self.device
        )
        self._fk_state.joint_q.assign(self._settled_fk_jq)
        newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)
        for w in range(self._world_count):
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()
        self._broadcast_fk_to_all_worlds()
        if hasattr(self._solver, "body_q_prev") and self._solver.body_q_prev is not None:
            self._solver.body_q_prev.assign(self._settled_body_q)

        if hasattr(self._solver, "enable_dahl_friction") and self._solver.enable_dahl_friction:
            if self._solver.joint_C_fric is not None:
                self._solver.joint_C_fric.zero_()
            if self._solver.joint_sigma_prev is not None:
                self._solver.joint_sigma_prev.zero_()

        self._groove_seg_indices = self._compute_groove_seg_indices(self._settled_body_q)

        wp.synchronize()
        fk_bq = self._fk_state.body_q.numpy()
        self._settled_ee_l_pos = fk_bq[EE_BODY_OFFSET][:3].copy()
        self._settled_ee_l_quat = fk_bq[EE_BODY_OFFSET][3:7].copy()
        self._settled_ee_r_pos = fk_bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3].copy()
        self._settled_ee_r_quat = fk_bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][3:7].copy()

        for w in range(self._world_count):
            self._ee_target_left[w] = self._settled_ee_l_pos.copy()
            self._ee_target_right[w] = self._settled_ee_r_pos.copy()
            self._ee_quat_left[w] = self._settled_ee_l_quat.copy()
            self._ee_quat_right[w] = self._settled_ee_r_quat.copy()

        print(f"[UnclampEnv] Restored from cache: groove_seg={self._groove_seg_indices[0]}")

    # =========================================================================
    # Physics Stepping
    # =========================================================================

    def _broadcast_fk_to_all_worlds(self):
        fk_bq = self._fk_state.body_q.numpy()[:ROBOT_BODY_COUNT]
        phys_bq = self._state_0.body_q.numpy()
        for w in range(self._world_count):
            start = self._bws[w]
            phys_bq[start : start + ROBOT_BODY_COUNT] = fk_bq
        self._state_0.body_q.assign(phys_bq)

    def _init_dynamic_fingers(self):
        inv_mass = self._model.body_inv_mass.numpy()
        inv_inertia = self._model.body_inv_inertia.numpy()
        self._finger_physics_ids = []
        for w in range(self._world_count):
            ws = self._bws[w]
            for arm_offset in [0, ROBOT_BODIES_PER_ARM]:
                for lf in FINGER_LOCAL:
                    bi = ws + arm_offset + lf
                    inv_mass[bi] = FINGER_DYNAMIC_INV_MASS
                    inv_inertia[bi] = np.full(3, FINGER_DYNAMIC_INV_INERTIA, dtype=np.float32)
                    self._finger_physics_ids.append(bi)
        self._model.body_inv_mass = wp.array(inv_mass, dtype=self._model.body_inv_mass.dtype, device=self.device)
        self._model.body_inv_inertia = wp.array(
            inv_inertia, dtype=self._model.body_inv_inertia.dtype, device=self.device
        )
        self._finger_set = set(self._finger_physics_ids)
        print(f"[UnclampEnv] Dynamic fingers: {len(self._finger_physics_ids)} bodies")

    def _apply_finger_spring(self, fk_batch_bq, N):
        body_q = self._state_0.body_q.numpy()
        body_qd = self._state_0.body_qd.numpy()
        body_f = self._state_0.body_f.numpy()
        for w in range(N):
            ws = self._bws[w]
            for arm_offset in [0, ROBOT_BODIES_PER_ARM]:
                for lf in FINGER_LOCAL:
                    bi = ws + arm_offset + lf
                    local_bi = arm_offset + lf
                    pos = body_q[bi][:3]
                    vel = body_qd[bi][3:6]
                    target = fk_batch_bq[w, local_bi, :3]
                    force = -FINGER_SPRING_KE * (pos - target) - FINGER_SPRING_KD * vel
                    body_f[bi][3:6] += force
        self._state_0.body_f.assign(body_f)

    def _apply_groove_spring(self):
        """Apply restoring spring toward groove center for cable bodies inside groove.

        Simulates clip snap retention. XZ force only (Y = cable tangent, free).
        """
        body_q = self._state_0.body_q.numpy()
        body_qd = self._state_0.body_qd.numpy()
        body_f = self._state_0.body_f.numpy()
        gx, gz = CLIP1_X, GROOVE_CENTER_Z
        for w in range(self._world_count):
            for bi in self._cable_bodies[w]:
                px, pz = body_q[bi][0], body_q[bi][2]
                dx, dz = px - gx, pz - gz
                dist_xz = math.sqrt(dx * dx + dz * dz)
                if dist_xz < GROOVE_SPRING_RADIUS:
                    vx, vz = body_qd[bi][3], body_qd[bi][5]
                    body_f[bi][3] += -GROOVE_SPRING_KE * dx - GROOVE_SPRING_KD * vx
                    body_f[bi][5] += -GROOVE_SPRING_KE * dz - GROOVE_SPRING_KD * vz
        self._state_0.body_f.assign(body_f)

    def _sanitise_body_state(self):
        """Clamp body positions and zero NaN/inf to prevent VBD segfault."""
        bq = self._state_0.body_q.numpy()
        bqd = self._state_0.body_qd.numpy()
        pos = bq[:, :3]
        bad_mask = ~np.isfinite(pos).all(axis=1)
        drift_mask = (np.abs(pos) > 5.0).any(axis=1)
        fix_mask = bad_mask | drift_mask
        if fix_mask.any():
            bq[fix_mask] = self._settled_body_q[fix_mask]
            bqd[fix_mask] = 0.0
            self._state_0.body_q.assign(bq)
            self._state_0.body_qd.assign(bqd)

    def _physics_step_all(self, substeps=None, sim_dt=None, fk_batch_bq=None, n_worlds=None):
        n_sub = substeps if substeps is not None else SIM_SUBSTEPS
        dt = sim_dt if sim_dt is not None else SIM_DT
        for _ in range(n_sub):
            self._state_0.clear_forces()
            self._apply_groove_spring()
            if fk_batch_bq is not None and n_worlds is not None:
                self._apply_finger_spring(fk_batch_bq, n_worlds)
            self._model.collide(self._state_0, self._contacts)
            self._solver.step(self._state_0, self._state_1, self._control, self._contacts, dt)
            self._state_0, self._state_1 = self._state_1, self._state_0
            self._sanitise_body_state()

    # =========================================================================
    # IK Solving
    # =========================================================================

    def _solve_ik_single(self, target_left, target_right):
        fk_model = self._fk_model
        left_ee = EE_BODY_OFFSET
        right_ee = FRANKA_NUM_JOINTS + EE_BODY_OFFSET
        target_rot = wp.array(
            [wp.vec4(_cos_pi8, _sin_pi8, 0.0, 0.0)],
            dtype=wp.vec4,
            device=self.device,
        )
        objectives = [
            IKObjectivePosition(
                link_index=left_ee,
                link_offset=wp.vec3(0, 0, 0),
                target_positions=wp.array([target_left], dtype=wp.vec3, device=self.device),
                weight=1.0,
            ),
            IKObjectivePosition(
                link_index=right_ee,
                link_offset=wp.vec3(0, 0, 0),
                target_positions=wp.array([target_right], dtype=wp.vec3, device=self.device),
                weight=1.0,
            ),
            IKObjectiveRotation(
                link_index=left_ee, link_offset_rotation=wp.quat_identity(), target_rotations=target_rot, weight=0.5
            ),
            IKObjectiveRotation(
                link_index=right_ee, link_offset_rotation=wp.quat_identity(), target_rotations=target_rot, weight=0.5
            ),
            IKObjectiveJointLimit(
                joint_limit_lower=fk_model.joint_limit_lower, joint_limit_upper=fk_model.joint_limit_upper, weight=10.0
            ),
        ]
        ik_solver = IKSolver(fk_model, n_problems=1, objectives=objectives)
        fk_jq = self._fk_state.joint_q.numpy()
        jq_in = wp.array(fk_jq.reshape(1, -1), dtype=float, device=self.device)
        jq_out = wp.zeros((1, fk_model.joint_coord_count), dtype=float, device=self.device)
        ik_solver.step(jq_in, jq_out, iterations=IK_ITERATIONS_INIT, step_size=IK_STEP_SIZE)
        return jq_out.numpy()[0]

    def _init_batched_ik_solver(self):
        N = self._world_count
        fk_model = self._fk_model
        left_ee = EE_BODY_OFFSET
        right_ee = FRANKA_NUM_JOINTS + EE_BODY_OFFSET

        rot_quat = wp.vec4(_cos_pi8, _sin_pi8, 0.0, 0.0)

        self._ik_obj_pos_left = IKObjectivePosition(
            link_index=left_ee,
            link_offset=wp.vec3(0, 0, 0),
            target_positions=wp.zeros(N, dtype=wp.vec3, device=self.device),
            weight=1.0,
        )
        self._ik_obj_pos_right = IKObjectivePosition(
            link_index=right_ee,
            link_offset=wp.vec3(0, 0, 0),
            target_positions=wp.zeros(N, dtype=wp.vec3, device=self.device),
            weight=1.0,
        )
        # Rotation objectives: held at initial hand-down orientation
        self._ik_obj_rot_left = IKObjectiveRotation(
            link_index=left_ee,
            link_offset_rotation=wp.quat_identity(),
            target_rotations=wp.array([rot_quat] * N, dtype=wp.vec4, device=self.device),
            weight=0.5,
        )
        self._ik_obj_rot_right = IKObjectiveRotation(
            link_index=right_ee,
            link_offset_rotation=wp.quat_identity(),
            target_rotations=wp.array([rot_quat] * N, dtype=wp.vec4, device=self.device),
            weight=0.5,
        )
        self._ik_obj_jlimit = IKObjectiveJointLimit(
            joint_limit_lower=fk_model.joint_limit_lower,
            joint_limit_upper=fk_model.joint_limit_upper,
            weight=10.0,
        )

        objectives = [
            self._ik_obj_pos_left,
            self._ik_obj_pos_right,
            self._ik_obj_rot_left,
            self._ik_obj_rot_right,
            self._ik_obj_jlimit,
        ]
        self._ik_solver_batch = IKSolver(fk_model, n_problems=N, objectives=objectives)

        coord_count = fk_model.joint_coord_count
        self._ik_jq_in = wp.zeros((N, coord_count), dtype=float, device=self.device)
        self._ik_jq_out = wp.zeros((N, coord_count), dtype=float, device=self.device)

        dof_count = fk_model.joint_dof_count
        body_count = fk_model.body_count
        self._batch_fk_jq = wp.zeros((N, coord_count), dtype=float, device=self.device)
        self._batch_fk_jqd = wp.zeros((N, dof_count), dtype=float, device=self.device)
        self._batch_fk_body_q = wp.zeros((N, body_count), dtype=wp.transform, device=self.device)
        self._batch_fk_body_qd = wp.zeros((N, body_count), dtype=wp.spatial_vector, device=self.device)

        print(f"[UnclampEnv] Batched IK solver: n_problems={N}")

    # =========================================================================
    # Action Application (4D: finger delta + EE ΔXYZ)
    # =========================================================================

    def _apply_actions_batch(self, actions):
        """Apply 4D actions: [0] finger delta, [1:4] left EE ΔXYZ.

        Right arm holds position (no action). Left EE rotation held constant.
        """
        N = self._world_count
        actions_np = actions.cpu().numpy()

        # Parse actions — finger can only open (HALF_OPEN→OPEN), clamp negative
        finger_delta = np.maximum(actions_np[:, 0], 0.0) * self.FINGER_ACTION_SCALE
        l_pos_delta = actions_np[:, 1:4] * self.POS_ACTION_SCALE  # [N, 3]

        fk_coord_count = self._fk_model.joint_coord_count
        finger_mask = np.ones(fk_coord_count, dtype=bool)
        for fc in (*GRIPPER_JOINT_RANGE, *(JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE)):
            finger_mask[fc] = False

        jq_starts = np.array(self._per_world_fk_jq[:N])

        # --- Update per-world finger targets (left arm only) ---
        for w in range(N):
            new_target = self._finger_target_left[w] + finger_delta[w]
            new_target = np.clip(new_target, FINGER_HALF_OPEN_POS, FINGER_OPEN_POS)
            self._finger_target_left[w] = new_target

            # Left finger target
            jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[0]] = new_target
            jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[1]] = new_target
            # Right finger: always OPEN (constant)
            jq_starts[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
            jq_starts[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS

        # --- Compute EE position targets ---
        targets_left = np.zeros((N, 3))
        targets_right = np.zeros((N, 3))

        for w in range(N):
            # Left: tracked target + delta (active tracking)
            target_l = self._ee_target_left[w].copy() + l_pos_delta[w]
            target_l[2] = np.clip(target_l[2], GRASP_Z, LIFT_Z + 0.05)
            targets_left[w] = target_l
            self._ee_target_left[w] = target_l.copy()

            # Right: hold initial position (passive)
            targets_right[w] = self._ee_target_right[w].copy()

        # Update IK position targets
        self._ik_obj_pos_left.set_target_positions(
            wp.array([wp.vec3(*t) for t in targets_left], dtype=wp.vec3, device=self.device)
        )
        self._ik_obj_pos_right.set_target_positions(
            wp.array([wp.vec3(*t) for t in targets_right], dtype=wp.vec3, device=self.device)
        )
        # Rotation objectives: NO update (held at initial hand-down)

        # Batched IK solve
        self._ik_jq_in.assign(jq_starts)
        self._ik_solver_batch.step(self._ik_jq_in, self._ik_jq_out, iterations=IK_ITERATIONS_RL, step_size=IK_STEP_SIZE)
        jq_targets = self._ik_jq_out.numpy()

        # Handle NaN
        nan_mask = np.any(np.isnan(jq_targets), axis=1)
        if np.any(nan_mask):
            jq_targets[nan_mask] = jq_starts[nan_mask]

        # Preserve finger positions in IK output
        for w in range(N):
            jq_targets[w, GRIPPER_DRIVER_JOINT_IDX[0]] = jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[0]]
            jq_targets[w, GRIPPER_DRIVER_JOINT_IDX[1]] = jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[1]]
            jq_targets[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
            jq_targets[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS

        # FK interpolation + physics stepping
        for step in range(self.PHYSICS_STEPS_PER_RL):
            t = min((step + 1) / self.PHYSICS_STEPS_PER_RL, 1.0)

            # Arm joint interpolation
            jq_interp_all = jq_starts.copy()
            jq_interp_all[:, finger_mask] = (
                jq_starts[:, finger_mask] + (jq_targets[:, finger_mask] - jq_starts[:, finger_mask]) * t
            )
            # Finger interpolation
            for fc in (*GRIPPER_JOINT_RANGE, *(JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE)):
                jq_interp_all[:, fc] = (
                    self._per_world_fk_jq[:N, fc] + (jq_targets[:, fc] - self._per_world_fk_jq[:N, fc]) * t
                )

            # Batched FK
            self._batch_fk_jq.assign(jq_interp_all)
            eval_fk_batched(
                self._fk_model, self._batch_fk_jq, self._batch_fk_jqd, self._batch_fk_body_q, self._batch_fk_body_qd
            )
            batch_bq = self._batch_fk_body_q.numpy()[:, :ROBOT_BODY_COUNT]

            # Broadcast FK to physics (skip dynamic finger bodies)
            phys_bq = self._state_0.body_q.numpy()
            for w in range(N):
                ws = self._bws[w]
                for bi in range(ROBOT_BODY_COUNT):
                    if (ws + bi) not in self._finger_set:
                        phys_bq[ws + bi] = batch_bq[w, bi]
            self._state_0.body_q.assign(phys_bq)

            # Physics step (with finger spring)
            self._physics_step_all(substeps=RL_SIM_SUBSTEPS, sim_dt=RL_SIM_DT, fk_batch_bq=batch_bq, n_worlds=N)

        # Save final FK state
        for w in range(N):
            self._per_world_fk_jq[w] = jq_targets[w].copy()

    # =========================================================================
    # Observations (42D — unified with GC/Clamp/AR for SkillAdapter)
    # =========================================================================

    def _compute_obs_batch(self):
        """Compute observations for all worlds. Returns [N, 42] tensor.

        Layout matches Clamp/GC/AR for SkillAdapter backbone compatibility:
            [0:3]   Right clamp position XYZ [m]
            [3:7]   Right clamp quaternion (qx,qy,qz,qw), w >= 0
            [7]     Right finger opening (j7+j8) [m]
            [8:11]  Left clamp position XYZ [m]
            [11:15] Left clamp quaternion (qx,qy,qz,qw), w >= 0
            [15]    Left finger opening (j7+j8) [m]
            [16:19] Cable groove segment position XYZ [m]
            [19:23] Cable groove segment quaternion (qx,qy,qz,qw), w >= 0
            [23:26] Groove center position XYZ [m]
            [26:30] Clip quaternion (qx,qy,qz,qw), w >= 0
            [30:33] Right orientation error (axis-angle) [rad]
            [33:36] Right position error [m]
            [36:39] Left orientation error (axis-angle) [rad]
            [39:42] Left position error [m]
        """
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        N = self._world_count
        obs_np = np.empty((N, 42), dtype=np.float32)

        clip_pos = self.GROOVE_CENTER_POS
        clip_quat = self.CLIP1_QUAT_XYZW

        for w in range(N):
            ws = self._bws[w]

            # Right EE (passive arm)
            ee_r_idx = ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
            ee_r_pos = bq[ee_r_idx, :3]
            ee_r_quat = bq[ee_r_idx, 3:7]
            clamp_r_pos = compute_clamp_pos(ee_r_pos, ee_r_quat)
            clamp_r_quat = normalize_quat_w_positive(ee_r_quat)
            clamp_r_quat = temporal_quat_consistency(clamp_r_quat, self._prev_clamp_r_quat[w])
            self._prev_clamp_r_quat[w] = clamp_r_quat.copy()

            # Left EE (active arm)
            ee_l_idx = ws + EE_BODY_OFFSET
            ee_l_pos = bq[ee_l_idx, :3]
            ee_l_quat = bq[ee_l_idx, 3:7]
            clamp_l_pos = compute_clamp_pos(ee_l_pos, ee_l_quat)
            clamp_l_quat = normalize_quat_w_positive(ee_l_quat)
            clamp_l_quat = temporal_quat_consistency(clamp_l_quat, self._prev_clamp_l_quat[w])
            self._prev_clamp_l_quat[w] = clamp_l_quat.copy()

            # Finger openings
            fk_jq = self._per_world_fk_jq[w]
            r_finger_opening = (
                fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]]
                + fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]]
            )
            l_finger_opening = fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] + fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]]

            # Cable target segment (near groove)
            cable_pos = bq[self._cable_bodies[w], :3]
            seg_pos, seg_tangent, _ = find_nearest_cable_point(
                cable_pos, self.GROOVE_CENTER_POS, self._groove_seg_indices[w]
            )
            seg_quat = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent))
            seg_quat = temporal_quat_consistency(seg_quat, self._prev_seg_quat[w])
            self._prev_seg_quat[w] = seg_quat.copy()

            # Error terms (arm vs cable segment)
            ori_error_r = compute_ori_error_axis_angle(clamp_r_quat, seg_quat)
            pos_error_r = clamp_r_pos - seg_pos
            ori_error_l = compute_ori_error_axis_angle(clamp_l_quat, seg_quat)
            pos_error_l = clamp_l_pos - seg_pos

            obs_np[w, 0:3] = clamp_r_pos
            obs_np[w, 3:7] = clamp_r_quat
            obs_np[w, 7] = r_finger_opening
            obs_np[w, 8:11] = clamp_l_pos
            obs_np[w, 11:15] = clamp_l_quat
            obs_np[w, 15] = l_finger_opening
            obs_np[w, 16:19] = seg_pos
            obs_np[w, 19:23] = seg_quat
            obs_np[w, 23:26] = clip_pos
            obs_np[w, 26:30] = clip_quat
            obs_np[w, 30:33] = ori_error_r
            obs_np[w, 33:36] = pos_error_r
            obs_np[w, 36:39] = ori_error_l
            obs_np[w, 39:42] = pos_error_l

        np.nan_to_num(obs_np, copy=False, nan=0.0)
        return torch.from_numpy(obs_np).to(device=self.device)

    # =========================================================================
    # Rewards & Dones
    # =========================================================================

    def _compute_rewards_dones_batch(self):
        wp.synchronize()
        bq = self._state_0.body_q.numpy()

        rewards = np.zeros(self._world_count, dtype=np.float32)
        dones = np.zeros(self._world_count, dtype=np.int64)
        timeouts = np.zeros(self._world_count, dtype=np.int64)
        successes = np.zeros(self._world_count, dtype=np.float32)

        rc_r_finger = np.zeros(self._world_count, dtype=np.float32)
        rc_r_seated = np.zeros(self._world_count, dtype=np.float32)
        rc_seated_dist = np.zeros(self._world_count, dtype=np.float32)
        rc_finger_opening = np.zeros(self._world_count, dtype=np.float32)
        rc_groove_bodies = np.zeros(self._world_count, dtype=np.int32)
        rc_drop = np.zeros(self._world_count, dtype=np.int32)

        clip_pos_xy = np.array([CLIP1_X, CLIP1_Y])

        for w in range(self._world_count):
            # Cable segment near groove
            cable_bq = bq[self._cable_bodies[w]]
            cable_pos = cable_bq[:, :3]
            seg_pos, seg_tangent, _ = find_nearest_cable_point(
                cable_pos, self.GROOVE_CENTER_POS, self._groove_seg_indices[w]
            )
            seg_quat = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent))

            # Seated distance
            dist_pos = float(np.linalg.norm(seg_pos - self.GROOVE_CENTER_POS))
            dist_ori = quat_distance(seg_quat, self.GROOVE_TARGET_QUAT)

            # Finger opening (sum of j7+j8)
            fk_jq = self._per_world_fk_jq[w]
            finger_opening = fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] + fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]]

            # --- Scores ---
            # Finger progress: 0 at HALF_OPEN_SUM, 1 at FULL_OPEN_SUM
            score_finger = np.clip((finger_opening - HALF_OPEN_SUM) / (FULL_OPEN_SUM - HALF_OPEN_SUM), 0.0, 1.0)

            # Seated: exp decay from groove center
            score_seated_pos = math.exp(-dist_pos / self.RANGE_SEATED)
            score_seated_ori = math.exp(-dist_ori / self.RANGE_ORI)
            score_seated = 0.5 * score_seated_pos + 0.5 * score_seated_ori

            # Multiplicative reward
            progress = (
                self.PROGRESS_W_FINGER * score_finger
                + self.PROGRESS_W_SEATED * score_seated
                + self.PROGRESS_W_COUPLED * score_finger * score_seated
            )
            r_base = self.PROGRESS_SCALE * (progress - 1.0)

            # Groove bodies count
            dists_xy = np.linalg.norm(cable_pos[:, :2] - clip_pos_xy, axis=1)
            cable_z_near = np.abs(cable_pos[:, 2] - GROOVE_CENTER_Z) < 0.015
            bodies_in_groove = int(np.sum((dists_xy < GROOVE_CHECK_RADIUS) & cable_z_near))

            # R_step: one-time bonus when finger fully open + cable seated
            r_step_val = 0.0
            finger_open_ok = finger_opening >= self.FINGER_OPEN_THRESH_SUM
            seated_pos_ok = dist_pos < self.SEATED_POS_THRESH
            cos_sim = abs(float(np.dot(seg_quat, self.GROOVE_TARGET_QUAT)))
            seated_ori_ok = cos_sim > self.SEATED_ORI_THRESH
            groove_ok = bodies_in_groove >= self.MIN_GROOVE_BODIES

            if finger_open_ok and seated_pos_ok and seated_ori_ok and groove_ok:
                if not self._step_bonus_given[w]:
                    r_step_val = self.R_STEP_BONUS
                    self._step_bonus_given[w] = True

            # Success: finger open + seated + sustained
            if finger_open_ok and seated_pos_ok and seated_ori_ok and groove_ok:
                self._success_sustain_count[w] += 1
            else:
                self._success_sustain_count[w] = 0
            success = self._success_sustain_count[w] >= self.SUSTAIN_STEPS

            r_task_val = self.R_TASK_BONUS if success else 0.0

            # Cable drop detection
            grip_center = self._groove_seg_indices[w][len(self._groove_seg_indices[w]) // 2]
            grip_lo = max(0, grip_center - 5)
            grip_hi = min(len(cable_pos), grip_center + 6)
            min_grip_z = float(np.min(cable_pos[grip_lo:grip_hi, 2]))
            r_drop_val = self.R_DROP if min_grip_z < self.DROP_Z_THRESH else 0.0
            cable_dropped = min_grip_z < self.DROP_Z_THRESH

            r = r_base + r_step_val + r_task_val + self.R_PENALTY + r_drop_val
            if math.isnan(r):
                r = self.R_PENALTY

            explosion = dist_pos > self.EXPLOSION_DIST_THRESH or math.isnan(dist_pos)
            timeout = self.episode_length_buf[w].item() >= self.max_episode_length
            done = success or timeout or explosion or cable_dropped

            rewards[w] = r
            rc_r_finger[w] = score_finger
            rc_r_seated[w] = score_seated
            rc_seated_dist[w] = dist_pos if not math.isnan(dist_pos) else self.EXPLOSION_DIST_THRESH
            rc_finger_opening[w] = finger_opening
            rc_groove_bodies[w] = bodies_in_groove
            rc_drop[w] = int(cable_dropped)
            dones[w] = int(done)
            # Only actual timeout should bootstrap value; explosion/drop are
            # true terminal states (value=0).
            timeouts[w] = int(timeout)
            successes[w] = float(success)

        return (
            torch.tensor(rewards, dtype=torch.float32, device=self.device),
            torch.tensor(dones, dtype=torch.long, device=self.device),
            {
                "observations": {},
                "time_outs": torch.tensor(timeouts, dtype=torch.long, device=self.device),
                "log": {
                    "/episode/success": float(np.mean(successes)),
                    "/reward/r_base": float(np.mean(rewards)),
                    "/reward/r_penalty": float(self.R_PENALTY),
                    "/metrics/score_finger_mean": float(np.mean(rc_r_finger)),
                    "/metrics/score_seated_mean": float(np.mean(rc_r_seated)),
                    "/metrics/seated_dist_mean": float(np.nanmean(rc_seated_dist)),
                    "/metrics/seated_dist_median": float(np.nanmedian(rc_seated_dist)),
                    "/metrics/finger_opening_mean": float(np.mean(rc_finger_opening)),
                    "/metrics/groove_bodies_mean": float(np.mean(rc_groove_bodies)),
                    "/metrics/drop_count": int(np.sum(rc_drop)),
                },
            },
        )

    # =========================================================================
    # Reset
    # =========================================================================

    def _reset_worlds(self, env_ids):
        if len(env_ids) == 0:
            return
        bq = self._state_0.body_q.numpy()
        bqd = self._state_0.body_qd.numpy()
        prev = self._solver.body_q_prev.numpy()

        for w in env_ids:
            w = int(w)
            start, end = self._bws[w], self._bws[w + 1]
            bq[start:end] = self._settled_body_q[start:end]
            bqd[start:end] = self._settled_body_qd[start:end]
            prev[start:end] = self._settled_body_q[start:end]
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()
            self._success_sustain_count[w] = 0
            self._step_bonus_given[w] = False
            self._finger_target_left[w] = FINGER_HALF_OPEN_POS
            self._ee_target_left[w] = self._settled_ee_l_pos.copy()
            self._ee_target_right[w] = self._settled_ee_r_pos.copy()
            self._ee_quat_left[w] = self._settled_ee_l_quat.copy()
            self._ee_quat_right[w] = self._settled_ee_r_quat.copy()
            self._prev_clamp_r_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_clamp_l_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_seg_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)

            # Init noise: perturb EE target only; first IK step resolves
            # FK and physics consistently (no body_q/joint_q mismatch).
            if self.INIT_XY_NOISE > 0:
                noise_xy = np.random.uniform(-self.INIT_XY_NOISE, self.INIT_XY_NOISE, size=2)
                self._ee_target_left[w][0] += noise_xy[0]
                self._ee_target_left[w][1] += noise_xy[1]

            self.episode_length_buf[w] = 0

        self._state_0.body_q.assign(bq)
        self._state_0.body_qd.assign(bqd)
        self._solver.body_q_prev.assign(prev)

        if hasattr(self._solver, "enable_dahl_friction") and self._solver.enable_dahl_friction:
            jws = self._jws
            cf = self._solver.joint_C_fric.numpy()
            sp = self._solver.joint_sigma_prev.numpy()
            for w in env_ids:
                w = int(w)
                js, je = jws[w], jws[w + 1]
                cf[js:je] = 0.0
                sp[js:je] = 0.0
            self._solver.joint_C_fric.assign(cf)
            self._solver.joint_sigma_prev.assign(sp)

    # =========================================================================
    # RSL-RL VecEnv Interface
    # =========================================================================

    @property
    def num_obs(self):
        return 42

    def get_observations(self) -> tuple[torch.Tensor, dict]:
        obs = self._compute_obs_batch()
        return obs, {"observations": {}}

    def reset(self) -> tuple[torch.Tensor, dict]:
        self._reset_worlds(list(range(self._world_count)))
        return self.get_observations()

    def step(self, actions: torch.Tensor):
        actions = torch.nan_to_num(actions, nan=0.0, posinf=0.0, neginf=0.0)
        self._apply_actions_batch(actions)
        self.episode_length_buf += 1
        self._total_env_steps += self._world_count

        rewards, dones, extras = self._compute_rewards_dones_batch()
        rewards = torch.nan_to_num(rewards, nan=-10.0, posinf=0.0, neginf=-10.0)

        done_ids = dones.nonzero(as_tuple=False).squeeze(-1)
        if len(done_ids) > 0:
            self._reset_worlds(done_ids.cpu().tolist())
            self._episode_count += len(done_ids)

        obs = self._compute_obs_batch()
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)
        return obs, rewards, dones, {"observations": {}, **extras}

    def close(self):
        pass
