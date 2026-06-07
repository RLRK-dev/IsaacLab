# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Newton VBD InsertIntoClip RL environment -- Multi-world RSL-RL VecEnv.

Independent InsertIntoClip skill (DAPG Approach A, Phase 2).
Task: Push cable into clip groove with dual arms.
Initial state: cable grasped between closed fingers at LIFT_Z above clip (synthetic precondition).
Obs (45D): 14D arm + 3D cable-groove error + 3D ori error + 1D dist + 21D cable shape + 3D cable velocity.
  [0:3]   Right clamp pos relative to groove center [m]
  [3:7]   Right clamp quat (xyzw)
  [7:10]  Left clamp pos relative to groove center [m]
  [10:14] Left clamp quat (xyzw)
  [14:17] Nearest cable segment pos relative to groove center [m]
  [17:20] Cable-groove orientation error (axis-angle) [rad]
  [20]    Cable-groove distance (scalar) [m]
  [21:42] Cable shape: 7 segments × 3D pos relative to groove center [m]
  [42:45] Cable velocity: groove-nearest segment linear vel [m/s]
Action (12D): EE delta XYZ + axis-angle x 2 arms. Finger always CLOSED.
Reward: pose_match cable_seg -> clip (multiplicative/hybrid/exp + R_groove + R_step + R_task + R_penalty + R_drop).
Success: seated(groove_n, clip_n) ^ sustained(K=10).

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/train_insert_clip.py --world-count 4
"""

import math
import os
import sys
import time
from collections import deque

import newton
import numpy as np
import torch
import warp as wp
from newton._src.sim.ik.ik_common import eval_fk_batched
from newton.ik import IKObjectiveJointLimit, IKObjectivePosition, IKObjectiveRotation, IKSolver
from newton.solvers import SolverVBD
from rsl_rl.env import VecEnv

_env_dir = os.path.dirname(os.path.abspath(__file__))
if _env_dir not in sys.path:
    sys.path.insert(0, _env_dir)
from chain_runtime_state import (
    export_chain_state_from_env,
    import_chain_state_into_env,
    validate_chain_state_for_env,
)

# Import scene building functions from test_newton_clip_routing
_script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
sys.path.insert(0, _script_dir)
from test_newton_clip_routing import (
    EE_BODY_OFFSET,
    FRANKA_NUM_JOINTS,
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
from cable_orientation_utils import compute_hand_quat_for_cable
from newton_skill_env_base import (
    assign_world_states_to_sim,
    axis_angle_to_quat_xyzw,
    compute_ori_error_axis_angle,
    extract_clamp_pose,
    find_nearest_cable_point,
    normalize_quat_w_positive,
    quat_distance,
    quat_multiply_xyzw,
    reset_dahl_friction_for_envs,
    restore_ee_targets_per_world,
    restore_world_body_state,
)

# Clip position -- from task_config SSOT
from task_config import (
    CABLE_RADIUS,
    CABLE_SEG_LEN,
    CABLE_SEGMENTS,
    CLIP1_X,
    CLIP1_Y,
    CLIP1_Z,
    CLIP_BASE_HEIGHT,
    EE_TO_FINGERTIP,
    FINGER_CLOSE_POS,
    FINGER_LOCAL,
    GRASP_X,
    GRIPPER_PAD_BODY_IDX,
    GRIP_HALF_SPAN,
    GROOVE_BODIES_MIN,
    GROOVE_CENTER_Z,
    INSERT_TERMINAL_STEPS,
    INSERT_TERMINAL_STEPS_INSERT,
    K_INSERT,
    LIFT_Z,
    NJMAX,
    PUSH_Z,
    ROBOT_BODIES_PER_ARM,
    SIM_SUBSTEPS,
    T_DIST_APPROACH,
    T_GROOVE,
    T_SEAT,
    TABLE_HEIGHT,
)

# Constants
DT = 1.0 / 480.0
SIM_DT = DT / SIM_SUBSTEPS
RL_SIM_SUBSTEPS = 4
RL_SIM_DT = DT / RL_SIM_SUBSTEPS
VBD_ITERATIONS = 20
IK_ITERATIONS_INIT = 100
IK_ITERATIONS_RL = 30
IK_STEP_SIZE = 1.0
ROBOT_BODY_COUNT = 2 * ROBOT_BODIES_PER_ARM  # 18

# IK rotation targets: hand down
_cos_pi8 = math.cos(math.pi / 8)
_sin_pi8 = math.sin(math.pi / 8)

# Groove check radius (from routing utils)
GROOVE_CHECK_RADIUS = CABLE_SEG_LEN + CABLE_RADIUS  # 19mm (must exceed segment spacing 15mm)

# Dynamic finger spring parameters (aligned with AerialRegrasp Mode 2)
FINGER_SPRING_KE = 10000.0  # Position spring stiffness [N/m]
FINGER_SPRING_KD = 500.0  # Velocity damping [N·s/m]
FINGER_DYNAMIC_INV_MASS = 20.0  # 1/0.05kg
FINGER_DYNAMIC_INV_INERTIA = 100.0  # Approximate


# =========================================================================
# InsertIntoClip Environment
# =========================================================================


class NewtonInsertClipEnv(VecEnv):
    """RSL-RL VecEnv for InsertIntoClip -- multi-world with replicate().

    mode="approach": cable at LIFT_Z → descend to groove+12mm. Coarse positioning.
    mode="insert":   cable at groove+12mm → push into groove (3mm). Precision insertion.

    Reward target: cable segment pose -> clip pose.
    """

    # --- Tunable Constants ---
    MAX_EPISODE_STEPS = INSERT_TERMINAL_STEPS  # 200 (unified with ApproachCable at PHYSICS_STEPS_PER_RL=10)

    # Reward: pose_match (cable_seg -> clip)
    REWARD_MODE = "hybrid"  # "exp" | "hybrid" | "multiplicative"
    EPS_POS = 0.015  # 15mm position decay (unified with ApproachCable)
    EPS_POS_MED = 0.10  # 100mm mid-range decay (bridges 45-200mm gradient desert)
    EPS_POS_COARSE = 1.0  # 1m coarse scale (long-range gradient, unified with ApproachCable)
    EPS_ORI = 0.25  # 0.25 rad (~14°) orientation decay (unified with ApproachCable)
    EPS_ORI_COARSE = 1.5  # 1.5 rad (~86°) coarse ori decay (long-range gradient, unified with AC/AR)
    W_POS = 0.5  # v36: halved (non-negative shift — total range [0, 1.5])
    W_ORI = 0.5  # v36: halved (non-negative shift — total range [0, 0.5])
    # Multiplicative reward (from ApproachCable, RL-Routing-Design §4.3):
    #   progress = W_POS*score_pos + W_ORI*score_ori + W_COUPLED*score_pos*score_ori
    #   R_base = PROGRESS_SCALE * (progress - 1.0)   range: [-PROGRESS_SCALE, 0]
    #   R = R_base + R_groove + R_step + R_task + R_penalty + R_drop
    RANGE_POS = 0.050  # 50mm: score_pos exp decay length [m]
    RANGE_ORI = 0.5  # 0.5 rad: score_ori exp decay length (v8: 1.0→0.5 for stronger ori gradient)
    PROGRESS_SCALE = 2.0  # Scale factor ([-2, 0] matches exp reward range)
    PROGRESS_W_POS = 0.2  # Independent pos weight
    PROGRESS_W_ORI = 0.2  # Independent ori weight
    PROGRESS_W_COUPLED = 0.6  # Coupled pos*ori weight (forces joint optimization)

    # Sparse rewards (mode-dependent: R_STEP_BONUS, W_GROOVE, R_PENALTY set in __init__)
    R_STEP_BONUS = 5.0  # Groove entry bonus (insert mode; approach=0)
    R_TASK_BONUS = 200.0  # v36: 20→200 (anti-hover: success must dominate hover)
    R_PENALTY = -1.16  # Default (approach). Insert mode: -1.66. Set in __init__
    R_DROP = -50.0  # v36: -5→-50 (drop catastrophic: 10x previous)
    W_GROOVE = 0.5  # Groove bodies reward (insert mode; approach=0)
    GROOVE_BODIES_NORM = 4.0  # Normalization: r_groove = W_GROOVE * (bodies / NORM)

    # Success thresholds — mode-dependent (set in __init__)
    # approach: pos < 12mm, ori cos > 0.85, no groove requirement
    # insert:   pos < 3mm, ori cos > 0.85, groove >= 2
    SUSTAIN_STEPS = K_INSERT  # K_INSERT RL steps (design doc: 10)

    # Cable drop detection: must be BELOW groove Z (0.809) so insertion can succeed.
    # GROOVE_Z = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS = 0.809
    # Threshold at TABLE_HEIGHT - 20mm = cable fell through/below table surface.
    DROP_Z_THRESH = TABLE_HEIGHT + CLIP_BASE_HEIGHT  # 0.805m — cable on table surface (5-body review P2)

    # Action scaling (unified across all skills — ApproachCable/InsertIntoClip/AerialRegrasp)
    POS_ACTION_SCALE = 0.015  # 15mm per action unit
    ROT_ACTION_SCALE = 0.05  # ~2.9° per action unit (axis-angle rad)
    PHYSICS_STEPS_PER_RL = 10  # FK interpolation steps per RL action (contact stability)
    ADAPTIVE_POS_SCALE = True  # Distance-adaptive pos scale: shrink near clip for 1mm precision
    FINE_THRESHOLD = 0.050  # 50mm: below this distance, pos action scale shrinks linearly
    MIN_POS_SCALE = 0.0005  # 0.5mm: minimum pos action scale (1mm precision target)

    # Left arm control: damping + action norm penalty (Session 101 fix)
    # Left arm has NO direct reward → PPO explores randomly at 15mm/step → cable destabilization
    LEFT_ACTION_DAMPING = 0.3  # Damp left arm delta to 30% (4.5mm/step: allows transport, prevents chaos)
    W_HOLD = 0.0  # Disabled (5-body review L1: double-suppression with LEFT_ACTION_DAMPING)

    # Target cable segment: clip-nearest (+-1 window)
    GROOVE_SEG_WINDOW = 1
    # Per-arm cable target: arm-nearest (+-1 window, unified with AC)
    GRIP_SEG_WINDOW = 1

    # Explosion guard
    EXPLOSION_DIST_THRESH = 1.0  # 1m

    # Init noise
    INIT_XY_NOISE = 0.002  # +/-2mm

    # Clip C1 pose (CLIP1_Z = TABLE_HEIGHT = clip base, used for visual placement)
    CLIP1_POS = np.array([CLIP1_X, CLIP1_Y, CLIP1_Z], dtype=np.float32)
    CLIP1_QUAT_XYZW = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)  # identity
    # Groove center: where cable sits when fully seated (reward/success target)
    # GROOVE_CENTER_Z imported from task_config (0.809m)
    GROOVE_CENTER_POS = np.array([CLIP1_X, CLIP1_Y, GROOVE_CENTER_Z], dtype=np.float32)

    # Groove target quaternion: ideal cable tangent when seated in groove.
    # Groove runs along clip local Y. For identity clip: groove_dir = [0, 1, 0].
    GROOVE_TARGET_QUAT = normalize_quat_w_positive(compute_hand_quat_for_cable(np.array([0.0, 1.0, 0.0])))

    # Precondition heights (mode-dependent, overridden in __init__ for insert mode)
    # approach: arms at LIFT_Z (cable at 0.900m, 91mm above groove)
    # insert:   arms at groove+12mm+fingertip (cable at 0.821m, 12mm above groove)
    APPROACH_EE_Z = LIFT_Z  # 1.120m
    INSERT_START_EE_Z = GROOVE_CENTER_Z + T_DIST_APPROACH + EE_TO_FINGERTIP  # 1.041m
    INSERT_EE_LEFT = np.array([CLIP1_X, CLIP1_Y - GRIP_HALF_SPAN, LIFT_Z], dtype=np.float32)
    INSERT_EE_RIGHT = np.array([CLIP1_X, CLIP1_Y + GRIP_HALF_SPAN, LIFT_Z], dtype=np.float32)
    INSERT_CABLE_Z = LIFT_Z - EE_TO_FINGERTIP  # ~0.900m (approach mode)

    # Cache directory
    CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "rl_insert_cache")

    def __init__(
        self,
        world_count=4,
        device="cuda:0",
        mode="approach",
        cfg=None,
        clip_x: float | None = None,
        clip_y: float | None = None,
    ):
        assert mode in ("approach", "insert"), f"Invalid mode: {mode}"
        self._mode = mode
        self.num_envs = world_count
        self.num_actions = 12
        self._total_env_steps = 0
        self.max_episode_length = self.MAX_EPISODE_STEPS
        self.device = device
        self.cfg = cfg or {}
        self._world_count = world_count

        # Mode-dependent thresholds and action scale
        if mode == "approach":
            self.SEATED_POS_THRESH = T_DIST_APPROACH  # 12mm
            self.SEATED_ORI_THRESH = T_SEAT  # cos > 0.85
            self.MIN_GROOVE_BODIES = 0  # not required for approach
            self.R_STEP_BONUS = 0.0  # no groove entry bonus (always true with MIN_GROOVE=0)
            self.W_GROOVE = 0.0  # no groove seating reward (goal is proximity, not insertion)
            # R_PENALTY: P0 dist_pos ≈ 91mm (LIFT_Z - GROOVE_Z)
            #   r_pos = 0.5*(exp(-91/15)+exp(-91/100)+exp(-91/1000)) = 0.659
            #   r_ori = 0.5*(exp(0)+exp(0))/2 = 0.500
            #   R_PENALTY = -(0.659 + 0.500) = -1.16
            self.R_PENALTY = -1.16
        else:  # insert
            self.SEATED_POS_THRESH = T_GROOVE  # 3mm
            self.SEATED_ORI_THRESH = T_SEAT  # cos > 0.85
            self.MIN_GROOVE_BODIES = GROOVE_BODIES_MIN  # 2
            self.R_STEP_BONUS = 0.0  # disable: cable starts inside 15mm Z-band → fires step 1
            self.W_GROOVE = 0.0  # disable: bodies_in_groove ≈ 3 at P0 → no gradient
            self.POS_ACTION_SCALE = 0.003  # 3mm (5x more precise)
            self.MIN_POS_SCALE = 0.0001  # 0.1mm
            self.FINE_THRESHOLD = 0.015  # 15mm (start shrinking earlier)
            self.MAX_EPISODE_STEPS = INSERT_TERMINAL_STEPS_INSERT  # 300 (from SSOT)
            self.DROP_Z_THRESH = TABLE_HEIGHT  # 0.80m (groove=0.809, need margin for insertion)
            # R_PENALTY: P0 dist_pos ≈ 12mm. r_groove=0 (disabled), r_step=0 (disabled)
            #   r_pos = 0.5*(exp(-12/15)+exp(-12/100)+exp(-12/1000)) = 1.162
            #   r_ori = 0.5*(exp(0)+exp(0))/2 = 0.500
            #   R_PENALTY = -(1.162 + 0.500) = -1.66
            self.R_PENALTY = -1.66

        self.max_episode_length = self.MAX_EPISODE_STEPS

        # Clip position (parameterized for X-stagger DR across clips)
        self._clip_x = clip_x if clip_x is not None else CLIP1_X
        self._clip_y = clip_y if clip_y is not None else CLIP1_Y
        # Override class-level constants with instance-level (clip-dependent)
        self.CLIP1_POS = np.array([self._clip_x, self._clip_y, CLIP1_Z], dtype=np.float32)
        self.GROOVE_CENTER_POS = np.array([self._clip_x, self._clip_y, GROOVE_CENTER_Z], dtype=np.float32)
        ee_z = self.INSERT_START_EE_Z if mode == "insert" else self.APPROACH_EE_Z
        self.INSERT_EE_LEFT = np.array([self._clip_x, self._clip_y - GRIP_HALF_SPAN, ee_z], dtype=np.float32)
        self.INSERT_EE_RIGHT = np.array([self._clip_x, self._clip_y + GRIP_HALF_SPAN, ee_z], dtype=np.float32)
        self.INSERT_CABLE_Z = ee_z - EE_TO_FINGERTIP

        self.episode_length_buf = torch.zeros(world_count, dtype=torch.long, device=device)
        self._groove_seg_indices = None  # [world_count, n_segs] -- near clip
        self._success_sustain_count = np.zeros(world_count, dtype=np.int32)
        self._groove_entered = np.zeros(world_count, dtype=bool)  # one-time step bonus
        self._cable_clip_dist_cache = np.full(world_count, 1.0, dtype=np.float32)  # adaptive scale
        self._iter_dist_sum = 0.0  # rollout-averaged dist_median accumulator
        self._iter_dist_count = 0
        self._episode_count = 0
        self._episode_success_buf = deque(maxlen=200)
        self._last_success_rate = 0.0
        self._last_actions = None  # for r_hold computation

        # Per-world EE targets (tracked explicitly)
        self._ee_target_right = np.zeros((world_count, 3), dtype=np.float32)
        self._ee_target_left = np.zeros((world_count, 3), dtype=np.float32)
        self._ee_quat_right = np.zeros((world_count, 4), dtype=np.float32)
        self._ee_quat_left = np.zeros((world_count, 4), dtype=np.float32)

        # Temporal quat consistency state (Bug #2 fix)
        self._prev_clamp_r_quat = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))
        self._prev_clamp_l_quat = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))
        self._prev_seg_quat = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))
        # Per-arm cable target quat consistency (unified obs A1)
        self._prev_seg_r_quat = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))
        self._prev_seg_l_quat = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))
        self._target_seg_indices_r = None
        self._target_seg_indices_l = None

        t0 = time.perf_counter()

        # Phase 1: Build FK + physics scene
        self._build_model()

        # Phase 2: Try cache -> skip precondition setup
        if self._load_precondition_cache():
            self._restore_from_cache()
        else:
            self._setup_insert_precondition()
            self._save_precondition_state()
            self._save_precondition_cache()

        # Phase 3: Batched IK solver for RL stepping
        self._init_batched_ik_solver()

        print(
            f"[InsertClipEnv:{mode}] Ready in {time.perf_counter() - t0:.1f}s. "
            f"obs={self.num_obs}, act={self.num_actions}, worlds={world_count}"
        )

    # =========================================================================
    # Environment Construction
    # =========================================================================

    def _build_model(self):
        """Build FK model + multi-world physics scene + VBD solver."""
        print("[InsertClipEnv] Building FK model...")
        self._fk_model = build_fk_model(device=self.device)
        self._fk_state = self._fk_model.state()

        # Initialize FK to URDF home config with fingers CLOSED (insert precondition)
        fk_jq = self._fk_state.joint_q.numpy()
        fk_tp = self._fk_model.joint_target_pos.numpy()
        fk_jq[:] = fk_tp[:]
        fk_jq[7] = FINGER_CLOSE_POS
        fk_jq[8] = FINGER_CLOSE_POS
        fk_jq[FRANKA_NUM_JOINTS + 7] = FINGER_CLOSE_POS
        fk_jq[FRANKA_NUM_JOINTS + 8] = FINGER_CLOSE_POS
        self._fk_state.joint_q.assign(fk_jq)
        newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)

        # Per-world FK joint state storage
        self._per_world_fk_jq = np.tile(fk_jq, (self._world_count, 1))

        # Build multi-world physics scene
        self._build_multiworld_physics()

    def _build_multiworld_physics(self):
        """Build proto -> replicate -> finalize multi-world physics model.

        Same as ApproachCable but adds target clip at C1 position.
        """
        print("[InsertClipEnv] Building world prototype...")
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

        # Contact filtering: non-pad bodies -> VISIBLE only, pad followers (GRIPPER_PAD_BODY_IDX) -> COLLIDE
        for arm_ss, arm_se, arm_bs in [
            (left_shape_start, left_shape_end, left_body_start),
            (right_shape_start, right_shape_end, right_body_start),
        ]:
            for si in range(arm_ss, arm_se):
                local = proto.shape_body[si] - arm_bs
                if local not in GRIPPER_PAD_BODY_IDX or si in all_finger_visual:
                    proto.shape_flags[si] = 1  # VISIBLE only
                elif local in GRIPPER_PAD_BODY_IDX:
                    proto.shape_flags[si] = 0x6  # COLLIDE_SHAPES | COLLIDE_PARTICLES

        # Cable (Cosserat Rod) -- starts on table, will be teleported in precondition
        cable_half_len = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
        cable_y_start = self._clip_y - cable_half_len
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

        # Cable-arm collision filter (non-pad bodies filtered; pad followers collide)
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
        print(
            f"[InsertClipEnv] Proto: {proto.body_count} bodies, {proto.joint_count} joints, {proto.shape_count} shapes"
        )

        # --- Scene: global entities + replicate ---
        print(f"[InsertClipEnv] Building scene ({self._world_count} worlds)...")
        scene = newton.ModelBuilder(gravity=GRAVITY)

        # Ground plane
        self._floor_shape_idx = scene.add_ground_plane()

        # Table
        table_cfg = newton.ModelBuilder.ShapeConfig()
        table_cfg.ke = 500.0
        table_cfg.kd = 100.0
        table_cfg.mu = 1.0
        table_cfg.gap = 0.002
        table_xform = wp.transform((0.3, -0.05, TABLE_HEIGHT - 0.005), wp.quat_identity())
        self._table_shape_idx = scene.add_shape_box(
            body=-1,
            hx=0.35,
            hy=0.35,
            hz=0.005,
            xform=table_xform,
            cfg=table_cfg,
        )

        # Target clip at C1 (V-groove geometry)
        clip_cfg = newton.ModelBuilder.ShapeConfig()
        clip_cfg.ke = 2500.0
        clip_cfg.kd = 100.0
        clip_cfg.mu = 1.0
        clip_cfg.gap = 0.001
        clip_parts = [
            (0, 0, 0.0025, 0.020, 0.015, 0.0025),  # Base plate
            (-0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),  # Left inner wall
            (+0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),  # Right inner wall
            (-0.013, 0, 0.025, 0.002, 0.015, 0.005),  # Left outer wall
            (+0.013, 0, 0.025, 0.002, 0.015, 0.005),  # Right outer wall
        ]
        for dx, dy, dz, hx, hy, hz in clip_parts:
            xf = wp.transform(
                (self._clip_x + dx, self._clip_y + dy, TABLE_HEIGHT + dz),
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
            scene.shape_flags[idx] = 0x6  # COLLIDE | BROADPHASE
        print(f"[InsertClipEnv] Added target clip at ({self._clip_x}, {self._clip_y})")

        # Replicate proto to N worlds
        scene.replicate(proto, world_count=self._world_count)
        scene.color()

        # Finalize
        self._model = scene.finalize(device=self.device, requires_grad=False)
        print(
            f"[InsertClipEnv] Model: {self._model.body_count} bodies, "
            f"{self._model.joint_count} joints, {self._model.shape_count} shapes"
        )

        # World index arrays
        self._bws = self._model.body_world_start.numpy()
        self._jws = self._model.joint_world_start.numpy()

        # Zero inv_mass for ALL worlds' robot bodies (kinematic)
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

        # VBD solver
        self._solver = SolverVBD(self._model, iterations=VBD_ITERATIONS)
        self._model.rigid_contact_max = NJMAX

        # Physics state + contacts
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
    # Synthetic Precondition (Step 2-1)
    # =========================================================================

    def _setup_insert_precondition(self):
        """Construct synthetic initial state: cable between closed fingers at LIFT_Z.

        Steps:
        1. IK: move both arms to positions above clip
        2. Teleport cable bodies to fingertip height at CLIP_X
        3. Fingers already CLOSED (set in _build_model)
        4. Broadcast FK to physics
        5. VBD settle (cable-finger contact stabilization)
        """
        print("[InsertClipEnv] Setting up InsertIntoClip precondition...")

        # Step 1: IK solve for arm positions above clip
        jq_target = self._solve_ik_single(tuple(self.INSERT_EE_LEFT), tuple(self.INSERT_EE_RIGHT))
        if np.any(np.isnan(jq_target)):
            raise RuntimeError("[InsertClipEnv] IK failed for insert precondition")

        # Keep fingers CLOSED in the IK solution
        jq_target[7] = FINGER_CLOSE_POS
        jq_target[8] = FINGER_CLOSE_POS
        jq_target[FRANKA_NUM_JOINTS + 7] = FINGER_CLOSE_POS
        jq_target[FRANKA_NUM_JOINTS + 8] = FINGER_CLOSE_POS

        # Apply IK solution to FK
        self._fk_state.joint_q.assign(jq_target)
        newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)
        for w in range(self._world_count):
            self._per_world_fk_jq[w] = jq_target.copy()

        # Broadcast FK to all worlds (arms now at insert position)
        self._broadcast_fk_to_all_worlds()

        # Step 2: Teleport cable bodies to fingertip height at CLIP_X
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        cable_half_len = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
        cable_y_start = self._clip_y - cable_half_len

        for w in range(self._world_count):
            for i, bi in enumerate(self._cable_bodies[w]):
                seg_y = cable_y_start + i * CABLE_SEG_LEN
                bq[bi, 0] = self._clip_x  # X: above clip
                bq[bi, 1] = seg_y  # Y: unchanged
                bq[bi, 2] = self.INSERT_CABLE_Z  # Z: fingertip height
                # Keep orientation (identity quat for straight cable)
                bq[bi, 3:7] = [0.0, 0.0, 0.0, 1.0]
        self._state_0.body_q.assign(bq)

        # Zero velocities
        bqd = self._state_0.body_qd.numpy()
        for w in range(self._world_count):
            for bi in self._cable_bodies[w]:
                bqd[bi, :] = 0.0
        self._state_0.body_qd.assign(bqd)

        # Sync VBD prev state
        self._solver.body_q_prev.assign(bq)

        # Step 3: VBD settle (cable-finger contact stabilization)
        print("[InsertClipEnv] VBD settling (100 frames)...")
        for _ in range(100):
            self._broadcast_fk_to_all_worlds()
            self._physics_step_all()

        # Verify: check cable Z didn't fall to table
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        cable_z_w0 = np.mean(bq[self._cable_bodies[0], 2])
        fingertip_z = self.INSERT_CABLE_Z
        print(
            f"[InsertClipEnv] Post-settle cable Z: {cable_z_w0:.4f} "
            f"(target: {fingertip_z:.4f}, delta: {(cable_z_w0 - fingertip_z) * 1000:.1f}mm)"
        )

        if cable_z_w0 < TABLE_HEIGHT + 0.05:
            print("[InsertClipEnv] WARNING: Cable fell to table level! Precondition may be invalid.")

        print("[InsertClipEnv] Precondition complete.")

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

    def _broadcast_per_world_fk(self):
        phys_bq = self._state_0.body_q.numpy()
        for w in range(self._world_count):
            self._fk_state.joint_q.assign(self._per_world_fk_jq[w])
            newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)
            fk_bq = self._fk_state.body_q.numpy()[:ROBOT_BODY_COUNT]
            start = self._bws[w]
            phys_bq[start : start + ROBOT_BODY_COUNT] = fk_bq
        self._state_0.body_q.assign(phys_bq)

    def _init_dynamic_fingers(self):
        """Make finger bodies dynamic for spring-based grip (aligned with AerialRegrasp)."""
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
        print(
            f"[InsertClipEnv] Dynamic fingers: {len(self._finger_physics_ids)} bodies "
            f"(inv_mass={FINGER_DYNAMIC_INV_MASS}, spring k={FINGER_SPRING_KE})"
        )

    def _apply_finger_spring(self, fk_batch_bq, N):
        """Apply spring forces to dynamic finger bodies toward FK target positions."""
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
                    vel = body_qd[bi][0:3]  # linear velocity
                    target = fk_batch_bq[w, local_bi, :3]
                    force = -FINGER_SPRING_KE * (pos - target) - FINGER_SPRING_KD * vel
                    body_f[bi][0:3] += force
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
            self._model.collide(self._state_0, self._contacts)
            self._solver.step(self._state_0, self._state_1, self._control, self._contacts, dt)
            self._state_0, self._state_1 = self._state_1, self._state_0
            self._sanitise_body_state()

    # =========================================================================
    # IK Solving
    # =========================================================================

    def _solve_ik_single(self, target_left, target_right):
        """Solve IK for both arms (single problem, used for precondition init)."""
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
        """Create cached IKSolver with n_problems=world_count for RL stepping."""
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
            joint_limit_lower=fk_model.joint_limit_lower, joint_limit_upper=fk_model.joint_limit_upper, weight=10.0
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

        # Pre-allocate batched FK buffers (types match ApproachCable: wp.transform/wp.spatial_vector)
        dof_count = fk_model.joint_dof_count
        body_count = fk_model.body_count
        self._batched_fk_jq = wp.zeros((N, coord_count), dtype=float, device=self.device)
        self._batched_fk_jqd = wp.zeros((N, dof_count), dtype=float, device=self.device)
        self._batched_fk_bq = wp.zeros((N, body_count), dtype=wp.transform, device=self.device)
        self._batched_fk_bqd = wp.zeros((N, body_count), dtype=wp.spatial_vector, device=self.device)

    # =========================================================================
    # Target Segment (clip-nearest cable bodies)
    # =========================================================================

    def _compute_target_seg_indices(self, bq):
        """Compute per-arm cable segment indices (unified obs A1, matches AC)."""
        n_cable = self._cable_bodies_per_world
        win = self.GRIP_SEG_WINDOW
        n_seg = 2 * win + 1
        result_r = np.zeros((self._world_count, n_seg), dtype=np.int32)
        result_l = np.zeros((self._world_count, n_seg), dtype=np.int32)
        for w in range(self._world_count):
            ws = self._bws[w]
            cable_pos = bq[self._cable_bodies[w], :3]
            # Right arm
            right_ee = bq[ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
            right_tip = right_ee.copy()
            right_tip[2] -= EE_TO_FINGERTIP
            right_seg = int(np.argmin(np.linalg.norm(cable_pos - right_tip, axis=1)))
            result_r[w] = np.clip(np.arange(right_seg - win, right_seg + win + 1), 0, n_cable - 1)
            # Left arm
            left_ee = bq[ws + EE_BODY_OFFSET][:3]
            left_tip = left_ee.copy()
            left_tip[2] -= EE_TO_FINGERTIP
            left_seg = int(np.argmin(np.linalg.norm(cable_pos - left_tip, axis=1)))
            result_l[w] = np.clip(np.arange(left_seg - win, left_seg + win + 1), 0, n_cable - 1)
        return result_r, result_l

    def _update_target_seg_hysteresis(self, bq):
        """Update target seg indices with ±1 hysteresis (matches AC env).

        Only updates when the nearest cable segment center changes by more
        than ±1 from the current center.  Prevents gradient oscillation from
        cable-sway-induced target jumps.
        """
        n_cable = self._cable_bodies_per_world
        win = self.GRIP_SEG_WINDOW

        for w in range(self._world_count):
            ws = self._bws[w]
            cable_pos = bq[self._cable_bodies[w], :3]

            # Right arm
            right_ee = bq[ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
            right_tip = right_ee.copy()
            right_tip[2] -= EE_TO_FINGERTIP
            new_center_r = int(np.argmin(np.linalg.norm(cable_pos - right_tip, axis=1)))
            prev_center_r = int(self._target_seg_indices_r[w][win])
            if abs(new_center_r - prev_center_r) > 1:
                self._target_seg_indices_r[w] = np.clip(
                    np.arange(new_center_r - win, new_center_r + win + 1), 0, n_cable - 1
                )

            # Left arm
            left_ee = bq[ws + EE_BODY_OFFSET][:3]
            left_tip = left_ee.copy()
            left_tip[2] -= EE_TO_FINGERTIP
            new_center_l = int(np.argmin(np.linalg.norm(cable_pos - left_tip, axis=1)))
            prev_center_l = int(self._target_seg_indices_l[w][win])
            if abs(new_center_l - prev_center_l) > 1:
                self._target_seg_indices_l[w] = np.clip(
                    np.arange(new_center_l - win, new_center_l + win + 1), 0, n_cable - 1
                )

    def _compute_groove_seg_indices(self, bq):
        """Compute cable segment indices nearest to clip (groove_n +/- window)."""
        n_cable = self._cable_bodies_per_world
        clip_pos_xy = np.array([self._clip_x, self._clip_y])
        window = self.GROOVE_SEG_WINDOW
        result = np.zeros((self._world_count, 2 * window + 1), dtype=np.int32)
        for w in range(self._world_count):
            cable_pos = bq[self._cable_bodies[w], :3]
            dists_xy = np.linalg.norm(cable_pos[:, :2] - clip_pos_xy, axis=1)
            groove_n = int(np.argmin(dists_xy))
            indices = np.arange(groove_n - window, groove_n + window + 1)
            result[w] = np.clip(indices, 0, n_cable - 1)
        return result

    # =========================================================================
    # State Management
    # =========================================================================

    def _save_precondition_state(self):
        wp.synchronize()
        self._settled_body_q = self._state_0.body_q.numpy().copy()
        self._settled_body_qd = self._state_0.body_qd.numpy().copy()
        self._settled_fk_jq = self._fk_state.joint_q.numpy().copy()
        self._settled_inv_mass = self._model.body_inv_mass.numpy().copy()
        self._settled_inv_inertia = self._model.body_inv_inertia.numpy().copy()

        for w in range(self._world_count):
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()

        bq = self._settled_body_q
        self._groove_seg_indices = self._compute_groove_seg_indices(bq)
        self._target_seg_indices_r, self._target_seg_indices_l = self._compute_target_seg_indices(bq)

        # Cache settled EE poses from FK
        fk_bq = self._fk_state.body_q.numpy()
        self._settled_ee_r_pos = fk_bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3].copy()
        self._settled_ee_r_quat = fk_bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][3:7].copy()
        self._settled_ee_l_pos = fk_bq[EE_BODY_OFFSET][:3].copy()
        self._settled_ee_l_quat = fk_bq[EE_BODY_OFFSET][3:7].copy()

        for w in range(self._world_count):
            self._ee_target_right[w] = self._settled_ee_r_pos.copy()
            self._ee_target_left[w] = self._settled_ee_l_pos.copy()
            self._ee_quat_right[w] = self._settled_ee_r_quat.copy()
            self._ee_quat_left[w] = self._settled_ee_l_quat.copy()

        print(
            f"[InsertClipEnv] Precondition saved: "
            f"L_EE={self._settled_ee_l_pos}, R_EE={self._settled_ee_r_pos}, "
            f"groove_seg={self._groove_seg_indices[0]}"
        )

    def _cache_path(self):
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        return os.path.join(
            self.CACHE_DIR,
            f"insert_{self._mode}_w{self._world_count}_cx{self._clip_x:.3f}_cy{self._clip_y:.3f}_v3.npz",
        )

    def _save_precondition_cache(self):
        path = self._cache_path()
        np.savez_compressed(
            path,
            body_q=self._settled_body_q,
            body_qd=self._settled_body_qd,
            fk_jq=self._settled_fk_jq,
            inv_mass=self._settled_inv_mass,
            inv_inertia=self._settled_inv_inertia,
            world_count=np.array([self._world_count], dtype=np.int32),
            body_count=np.array([self._model.body_count], dtype=np.int32),
        )
        print(f"[InsertClipEnv] Precondition cached to {path}")

    def _load_precondition_cache(self):
        path = self._cache_path()
        if not os.path.exists(path):
            print(f"[InsertClipEnv] No cache at {path}")
            return False
        try:
            data = np.load(path)
            if int(data["world_count"][0]) != self._world_count:
                print("[InsertClipEnv] Cache world_count mismatch")
                return False
            if int(data["body_count"][0]) != self._model.body_count:
                print("[InsertClipEnv] Cache body_count mismatch")
                return False
            self._settled_body_q = data["body_q"]
            self._settled_body_qd = data["body_qd"]
            self._settled_fk_jq = data["fk_jq"]
            self._settled_inv_mass = data["inv_mass"]
            self._settled_inv_inertia = data["inv_inertia"]
            print(f"[InsertClipEnv] Loaded cache from {path}")
            return True
        except Exception as e:
            print(f"[InsertClipEnv] Cache load failed: {e}")
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
        self._solver.body_q_prev.assign(self._settled_body_q)
        if hasattr(self._solver, "enable_dahl_friction") and self._solver.enable_dahl_friction:
            if self._solver.joint_C_fric is not None:
                self._solver.joint_C_fric.zero_()
            if self._solver.joint_sigma_prev is not None:
                self._solver.joint_sigma_prev.zero_()

        bq = self._settled_body_q
        self._groove_seg_indices = self._compute_groove_seg_indices(bq)
        self._target_seg_indices_r, self._target_seg_indices_l = self._compute_target_seg_indices(bq)

        wp.synchronize()
        fk_bq = self._fk_state.body_q.numpy()
        self._settled_ee_r_pos = fk_bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3].copy()
        self._settled_ee_r_quat = fk_bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][3:7].copy()
        self._settled_ee_l_pos = fk_bq[EE_BODY_OFFSET][:3].copy()
        self._settled_ee_l_quat = fk_bq[EE_BODY_OFFSET][3:7].copy()

        for w in range(self._world_count):
            self._ee_target_right[w] = self._settled_ee_r_pos.copy()
            self._ee_target_left[w] = self._settled_ee_l_pos.copy()
            self._ee_quat_right[w] = self._settled_ee_r_quat.copy()
            self._ee_quat_left[w] = self._settled_ee_l_quat.copy()

        print(f"[InsertClipEnv] Restored from cache: groove_seg={self._groove_seg_indices[0]}")

    def _reset_worlds(self, env_ids):
        if len(env_ids) == 0:
            return
        bq = self._state_0.body_q.numpy()
        bqd = self._state_0.body_qd.numpy()
        prev = self._solver.body_q_prev.numpy()

        for w in env_ids:
            w = int(w)
            restore_world_body_state(
                bq=bq,
                bqd=bqd,
                prev=prev,
                settled_body_q=self._settled_body_q,
                settled_body_qd=self._settled_body_qd,
                w=w,
                bws=self._bws,
            )
            start = self._bws[w]  # preserved for XY-noise block below (uses body_idx)
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()
            self._groove_entered[w] = False
            self._success_sustain_count[w] = 0
            self._cable_clip_dist_cache[w] = 1.0  # reset to far
            restore_ee_targets_per_world(
                ee_target_right=self._ee_target_right,
                ee_target_left=self._ee_target_left,
                ee_quat_right=self._ee_quat_right,
                ee_quat_left=self._ee_quat_left,
                settled_ee_r_pos=self._settled_ee_r_pos,
                settled_ee_l_pos=self._settled_ee_l_pos,
                settled_ee_r_quat=self._settled_ee_r_quat,
                settled_ee_l_quat=self._settled_ee_l_quat,
                w=w,
            )

            # Reset temporal quat consistency state (Bug #2)
            self._prev_clamp_r_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_clamp_l_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_seg_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_seg_r_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_seg_l_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)

            # Init noise: small perturbation of both arms
            if self.INIT_XY_NOISE > 0:
                for ee_offset in [FRANKA_NUM_JOINTS + EE_BODY_OFFSET, EE_BODY_OFFSET]:
                    ee_body_idx = start + ee_offset
                    noise_xy = np.random.uniform(-self.INIT_XY_NOISE, self.INIT_XY_NOISE, size=2)
                    bq[ee_body_idx, 0] += noise_xy[0]
                    bq[ee_body_idx, 1] += noise_xy[1]
                    prev[ee_body_idx, 0] += noise_xy[0]
                    prev[ee_body_idx, 1] += noise_xy[1]
                    if ee_offset == FRANKA_NUM_JOINTS + EE_BODY_OFFSET:
                        self._ee_target_right[w][0] += noise_xy[0]
                        self._ee_target_right[w][1] += noise_xy[1]
                    else:
                        self._ee_target_left[w][0] += noise_xy[0]
                        self._ee_target_left[w][1] += noise_xy[1]

            self.episode_length_buf[w] = 0

        assign_world_states_to_sim(self._state_0, self._solver, bq, bqd, prev)

        # Update segment indices for reset worlds only (preserve hysteresis
        # state for non-reset worlds)
        new_r, new_l = self._compute_target_seg_indices(bq)
        new_groove = self._compute_groove_seg_indices(bq)
        for w in env_ids:
            w = int(w)
            self._target_seg_indices_r[w] = new_r[w]
            self._target_seg_indices_l[w] = new_l[w]
            self._groove_seg_indices[w] = new_groove[w]

        reset_dahl_friction_for_envs(self._solver, self._jws, env_ids)

    # =========================================================================
    # Obs (45D)
    # =========================================================================

    # Number of cable segments to observe around groove center (±OBS_CABLE_HALF)
    OBS_CABLE_HALF = 3  # 7 segments total: groove_center ± 3

    def _compute_obs_batch(self):
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        bqd = self._state_0.body_qd.numpy()
        N = self._world_count
        n_cable = self._cable_bodies_per_world
        n_shape = 2 * self.OBS_CABLE_HALF + 1  # 7
        obs_np = np.empty((N, 45), dtype=np.float32)

        for w in range(N):
            ws = self._bws[w]

            # Clamp pose (fingertip position + orientation) for both arms via helper
            clamp_r_pos, clamp_r_quat = extract_clamp_pose(
                bq, ws, FRANKA_NUM_JOINTS + EE_BODY_OFFSET, self._prev_clamp_r_quat[w]
            )
            self._prev_clamp_r_quat[w] = clamp_r_quat.copy()
            clamp_l_pos, clamp_l_quat = extract_clamp_pose(bq, ws, EE_BODY_OFFSET, self._prev_clamp_l_quat[w])
            self._prev_clamp_l_quat[w] = clamp_l_quat.copy()

            # Cable shape: 7 segments centered on groove-nearest
            cable_bodies = self._cable_bodies[w]
            cable_pos = bq[cable_bodies, :3]
            groove_center_idx = self._groove_seg_indices[w][len(self._groove_seg_indices[w]) // 2]
            shape_indices = np.arange(
                groove_center_idx - self.OBS_CABLE_HALF,
                groove_center_idx + self.OBS_CABLE_HALF + 1,
            )
            shape_indices = np.clip(shape_indices, 0, n_cable - 1)
            cable_shape = cable_pos[shape_indices].flatten()  # [7*3 = 21]

            # Cable velocity: groove-nearest segment linear velocity
            groove_body_idx = cable_bodies[groove_center_idx]
            cable_vel = bqd[groove_body_idx][0:3]  # linear velocity [m/s]

            # Groove-relative coordinates (5-body review C2+C3: replace constants with error signals)
            groove_pos = self.GROOVE_CENTER_POS
            groove_quat = self.GROOVE_TARGET_QUAT

            # Cable-groove nearest point and orientation error
            cable_nearest_pos = cable_pos[groove_center_idx]
            cable_groove_error_pos = cable_nearest_pos - groove_pos  # 3D position error
            # Cable tangent at groove-nearest -> orientation error as axis-angle
            if groove_center_idx + 1 < n_cable:
                seg_tangent = cable_pos[groove_center_idx + 1] - cable_pos[groove_center_idx]
            elif groove_center_idx > 0:
                seg_tangent = cable_pos[groove_center_idx] - cable_pos[groove_center_idx - 1]
            else:
                seg_tangent = np.array([0.0, 1.0, 0.0], dtype=np.float32)
            seg_quat_obs = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent))
            ori_error_aa = compute_ori_error_axis_angle(seg_quat_obs, groove_quat)  # 3D axis-angle
            dist_pos_scalar = float(np.linalg.norm(cable_groove_error_pos))

            # [0:3]   R clamp pos relative to groove
            obs_np[w, 0:3] = clamp_r_pos - groove_pos
            # [3:7]   R clamp quat
            obs_np[w, 3:7] = clamp_r_quat
            # [7:10]  L clamp pos relative to groove
            obs_np[w, 7:10] = clamp_l_pos - groove_pos
            # [10:14] L clamp quat
            obs_np[w, 10:14] = clamp_l_quat
            # [14:17] cable-groove position error
            obs_np[w, 14:17] = cable_groove_error_pos
            # [17:20] cable-groove orientation error (axis-angle)
            obs_np[w, 17:20] = ori_error_aa
            # [20]    cable-groove distance (scalar)
            obs_np[w, 20] = dist_pos_scalar
            # [21:42] cable shape relative to groove (7 seg × 3D)
            obs_np[w, 21:42] = (cable_pos[shape_indices] - groove_pos).flatten()
            # [42:45] cable linear velocity
            obs_np[w, 42:45] = cable_vel

        np.nan_to_num(obs_np, copy=False, nan=0.0)
        return torch.from_numpy(obs_np).to(device=self.device)

    # =========================================================================
    # Reward + Done (cable_seg -> clip)
    # =========================================================================

    def _compute_rewards_dones_batch(self):
        wp.synchronize()
        bq = self._state_0.body_q.numpy()

        # Update groove and per-arm segment indices dynamically (cable moves during transport)
        self._groove_seg_indices = self._compute_groove_seg_indices(bq)
        self._target_seg_indices_r, self._target_seg_indices_l = self._compute_target_seg_indices(bq)

        rewards = np.zeros(self._world_count, dtype=np.float32)
        dones = np.zeros(self._world_count, dtype=np.int64)
        timeouts = np.zeros(self._world_count, dtype=np.int64)
        successes = np.zeros(self._world_count, dtype=np.float32)

        rc_r_pos = np.zeros(self._world_count, dtype=np.float32)
        rc_r_ori = np.zeros(self._world_count, dtype=np.float32)
        rc_r_step = np.zeros(self._world_count, dtype=np.float32)
        rc_r_groove = np.zeros(self._world_count, dtype=np.float32)
        rc_cable_clip_dist = np.zeros(self._world_count, dtype=np.float32)
        rc_cable_clip_ori = np.zeros(self._world_count, dtype=np.float32)
        rc_groove_bodies = np.zeros(self._world_count, dtype=np.int32)
        rc_drop = np.zeros(self._world_count, dtype=np.int32)
        rc_explosion = np.zeros(self._world_count, dtype=np.bool_)
        rc_r_hold = np.zeros(self._world_count, dtype=np.float32)
        rc_left_action_norm = np.zeros(self._world_count, dtype=np.float32)

        clip_pos_xy = np.array([self._clip_x, self._clip_y])

        for w in range(self._world_count):
            # Cable segment near groove
            cable_bq = bq[self._cable_bodies[w]]
            cable_pos = cable_bq[:, :3]
            seg_pos, seg_tangent, _ = find_nearest_cable_point(
                cable_pos, self.GROOVE_CENTER_POS, self._groove_seg_indices[w]
            )
            seg_quat = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent))

            # Cable -> groove center distance (XYZ, reward uses full 3D)
            dist_pos = float(np.linalg.norm(seg_pos - self.GROOVE_CENTER_POS))
            self._cable_clip_dist_cache[w] = dist_pos
            dist_ori = quat_distance(seg_quat, self.GROOVE_TARGET_QUAT)

            # Reward: pose_match
            if self.REWARD_MODE == "multiplicative":
                score_pos = math.exp(-dist_pos / self.RANGE_POS)
                score_ori = math.exp(-dist_ori / self.RANGE_ORI)
                progress = (
                    self.PROGRESS_W_POS * score_pos
                    + self.PROGRESS_W_ORI * score_ori
                    + self.PROGRESS_W_COUPLED * score_pos * score_ori
                )
                # v36: non-negative shift (remove -1.0). R_PENALTY handles baseline.
                r_pos = self.PROGRESS_SCALE * progress
                r_ori = 0.0  # included in r_pos via multiplicative coupling
            elif self.REWARD_MODE == "hybrid":
                # v36: non-negative shift (remove -1.0). Range [0, 1] per term.
                # R_PENALTY calibrated to zero-out at P0. Approach → positive reward.
                r_fine = math.exp(-dist_pos / self.EPS_POS)
                r_med = math.exp(-dist_pos / self.EPS_POS_MED)
                r_coarse = math.exp(-dist_pos / self.EPS_POS_COARSE)
                r_pos = self.W_POS * (r_fine + r_med + r_coarse)
                r_ori = (
                    self.W_ORI * (math.exp(-dist_ori / self.EPS_ORI) + math.exp(-dist_ori / self.EPS_ORI_COARSE)) / 2
                )
            else:
                # v36: non-negative shift for exp mode too
                r_pos = self.W_POS * math.exp(-dist_pos / self.EPS_POS)
                r_ori = (
                    self.W_ORI * (math.exp(-dist_ori / self.EPS_ORI) + math.exp(-dist_ori / self.EPS_ORI_COARSE)) / 2
                )

            # R_step: one-time bonus when cable first enters groove
            # XY + Z check: cable must be near clip Z (not just overhead at LIFT_Z)
            r_step_val = 0.0
            dists_xy = np.linalg.norm(cable_pos[:, :2] - clip_pos_xy, axis=1)
            clip_z = GROOVE_CENTER_Z
            cable_z_near_clip = np.abs(cable_pos[:, 2] - clip_z) < 0.015
            bodies_in_groove = int(np.sum((dists_xy < GROOVE_CHECK_RADIUS) & cable_z_near_clip))
            if bodies_in_groove >= self.MIN_GROOVE_BODIES and not self._groove_entered[w]:
                r_step_val = self.R_STEP_BONUS
                self._groove_entered[w] = True

            # Continuous groove seating reward: proportional to bodies in groove
            r_groove = self.W_GROOVE * min(bodies_in_groove / self.GROOVE_BODIES_NORM, 1.0)

            # Success: seated(groove_n, clip_n) ^ sustained(K)
            # seated.pos: cable seg within T_GROOVE of clip
            seated_pos_ok = dist_pos < self.SEATED_POS_THRESH
            # seated.ori: quat dot threshold (|q1·q2| > T_SEAT, NOT tangent cos)
            # T_SEAT=0.85 → ~64° max rotation difference (cos⁻¹(0.85)*2)
            cos_sim = float(np.dot(seg_quat, self.GROOVE_TARGET_QUAT))
            cos_sim = abs(cos_sim)  # double-cover
            seated_ori_ok = cos_sim > self.SEATED_ORI_THRESH
            # bodies in groove
            groove_ok = bodies_in_groove >= self.MIN_GROOVE_BODIES
            if seated_pos_ok and seated_ori_ok and groove_ok:
                self._success_sustain_count[w] += 1
            else:
                self._success_sustain_count[w] = 0
            success = self._success_sustain_count[w] >= self.SUSTAIN_STEPS

            r_task_val = self.R_TASK_BONUS if success else 0.0

            # R_drop: cable fell to table (check grip-region segments only,
            # not free-hanging ends which naturally sag under gravity)
            grip_center = self._groove_seg_indices[w][len(self._groove_seg_indices[w]) // 2]
            grip_lo = max(0, grip_center - 5)
            grip_hi = min(len(cable_pos), grip_center + 6)
            min_grip_z = float(np.min(cable_pos[grip_lo:grip_hi, 2]))
            r_drop_val = self.R_DROP if min_grip_z < self.DROP_Z_THRESH else 0.0
            cable_dropped = min_grip_z < self.DROP_Z_THRESH

            # Left arm hold penalty: penalize left arm action magnitude
            if self._last_actions is not None:
                a_left = self._last_actions[w, 6:12]
                left_sq = float(torch.sum(a_left**2))
                r_hold_val = -self.W_HOLD * left_sq
                rc_left_action_norm[w] = math.sqrt(left_sq)
            else:
                r_hold_val = 0.0
            rc_r_hold[w] = r_hold_val

            # Explosion guard (NaN also triggers — IEEE 754 NaN > x is False)
            explosion = dist_pos > self.EXPLOSION_DIST_THRESH or math.isnan(dist_pos)

            if explosion:
                r = -10.0  # Fixed penalty: clear signal without inf gradient contamination
            else:
                r = r_pos + r_ori + r_groove + r_step_val + r_task_val + self.R_PENALTY + r_drop_val + r_hold_val
                if math.isnan(r):
                    r = self.R_PENALTY

            timeout = self.episode_length_buf[w].item() >= self.max_episode_length
            done = success or timeout or explosion or cable_dropped

            rewards[w] = r
            rc_r_pos[w] = r_pos
            rc_r_ori[w] = r_ori
            rc_r_step[w] = r_step_val
            rc_r_groove[w] = r_groove
            # Clamp dist to EXPLOSION_DIST_THRESH to prevent inf in mean computation
            rc_cable_clip_dist[w] = (
                min(dist_pos, self.EXPLOSION_DIST_THRESH) if not math.isnan(dist_pos) else self.EXPLOSION_DIST_THRESH
            )
            rc_cable_clip_ori[w] = dist_ori if not math.isnan(dist_ori) else 0.0
            rc_groove_bodies[w] = bodies_in_groove
            rc_drop[w] = int(cable_dropped)
            rc_explosion[w] = explosion
            dones[w] = int(done)
            # BUG-1 fix: explosion/cable_dropped are true terminal states (value=0),
            # not timeouts. Only actual timeout should bootstrap value via RSL-RL PPO.
            timeouts[w] = int(timeout)
            successes[w] = float(success)
            if done:
                self._episode_success_buf.append(float(success))

        if len(self._episode_success_buf) > 0:
            self._last_success_rate = float(np.mean(self._episode_success_buf))

        # Accumulate rollout-averaged dist_median (for distance-conditioned alpha)
        self._iter_dist_sum += float(np.nanmedian(rc_cable_clip_dist))
        self._iter_dist_count += 1

        return (
            torch.tensor(rewards, dtype=torch.float32, device=self.device),
            torch.tensor(dones, dtype=torch.long, device=self.device),
            {
                "observations": {},
                "time_outs": torch.tensor(timeouts, dtype=torch.long, device=self.device),
                "log": {
                    "/episode/success": float(np.mean(successes)),
                    "/metrics/episode_success_rate": self._last_success_rate,
                    "/reward/r_pos": float(np.mean(rc_r_pos)),
                    "/reward/r_ori": float(np.mean(rc_r_ori)),
                    "/reward/r_step": float(np.mean(rc_r_step)),
                    "/reward/r_groove": float(np.mean(rc_r_groove)),
                    "/reward/r_penalty": float(self.R_PENALTY),
                    "/metrics/cable_clip_dist_mean": float(np.nanmean(rc_cable_clip_dist)),
                    "/metrics/cable_clip_dist_median": float(np.nanmedian(rc_cable_clip_dist)),
                    "/metrics/cable_clip_ori_mean": float(np.nanmean(rc_cable_clip_ori)),
                    "/metrics/cable_clip_ori_median": float(np.nanmedian(rc_cable_clip_ori)),
                    "/metrics/groove_bodies_mean": float(np.mean(rc_groove_bodies)),
                    "/metrics/explosion_count": int(np.sum(rc_explosion)),
                    "/metrics/drop_count": int(np.sum(rc_drop)),
                    "/reward/r_hold": float(np.mean(rc_r_hold)),
                    "/metrics/left_action_norm": float(np.mean(rc_left_action_norm)),
                },
                "log_per_world": {
                    "dist_pos": rc_cable_clip_dist.copy(),
                    "dist_ori": rc_cable_clip_ori.copy(),
                    "groove_bodies": rc_groove_bodies.copy(),
                    "reward": rewards.copy(),
                    "success": successes.copy(),
                    "explosion": rc_explosion.copy(),
                },
            },
        )

    def get_rollout_dist_median(self):
        """Return rollout-averaged dist_median and reset accumulator.

        Called by training loop after runner.learn() to get stable distance
        metric for distance-conditioned alpha (avoids BUG-6 cache timing issue).
        """
        if self._iter_dist_count > 0:
            avg = self._iter_dist_sum / self._iter_dist_count
        else:
            avg = 1.0  # fallback: far
        self._iter_dist_sum = 0.0
        self._iter_dist_count = 0
        return avg

    # =========================================================================
    # Action Application (12D: delta EE pos + rot, fingers always CLOSED)
    # =========================================================================

    def _apply_actions_batch(self, actions):
        """Apply per-world 12D actions via batched IK + FK interpolation + physics.

        Structure matches ApproachCable: 10-step FK interpolation loop for contact stability.
        Fingers always CLOSED (no auto-control transition).
        """
        N = self._world_count
        actions_np = actions.cpu().numpy()
        wp.synchronize()

        # Right arm: adaptive pos scale (shrink near clip for precision)
        if self.ADAPTIVE_POS_SCALE:
            r_pos_scales = np.array(
                [
                    max(
                        self.MIN_POS_SCALE,
                        self.POS_ACTION_SCALE * min(1.0, self._cable_clip_dist_cache[w] / self.FINE_THRESHOLD),
                    )
                    for w in range(N)
                ],
                dtype=np.float32,
            )
            r_pos_delta = actions_np[:, 0:3] * r_pos_scales[:, None]
        else:
            r_pos_delta = actions_np[:, 0:3] * self.POS_ACTION_SCALE
        r_rot_delta = actions_np[:, 3:6] * self.ROT_ACTION_SCALE

        # Left arm: fixed scale + damping (no adaptive — cable-clip dist is irrelevant for left arm)
        l_pos_delta = actions_np[:, 6:9] * self.POS_ACTION_SCALE * self.LEFT_ACTION_DAMPING
        l_rot_delta = actions_np[:, 9:12] * self.ROT_ACTION_SCALE * self.LEFT_ACTION_DAMPING

        fk_coord_count = self._fk_model.joint_coord_count
        finger_mask = np.ones(fk_coord_count, dtype=bool)
        for fc in (7, 8, FRANKA_NUM_JOINTS + 7, FRANKA_NUM_JOINTS + 8):
            finger_mask[fc] = False

        targets_left = np.zeros((N, 3))
        targets_right = np.zeros((N, 3))
        rot_targets_left = []
        rot_targets_right = []
        jq_starts = np.array(self._per_world_fk_jq[:N])

        # Fingers always CLOSED
        for w in range(N):
            jq_starts[w, 7] = FINGER_CLOSE_POS
            jq_starts[w, 8] = FINGER_CLOSE_POS
            jq_starts[w, FRANKA_NUM_JOINTS + 7] = FINGER_CLOSE_POS
            jq_starts[w, FRANKA_NUM_JOINTS + 8] = FINGER_CLOSE_POS

        for w in range(N):
            # Right EE: tracked target + delta
            target_r = self._ee_target_right[w].copy() + r_pos_delta[w]
            target_r[2] = np.clip(target_r[2], PUSH_Z, LIFT_Z + 0.05)
            targets_right[w] = target_r
            self._ee_target_right[w] = target_r.copy()

            # Right rotation: tracked quat + axis-angle delta
            delta_r_quat = axis_angle_to_quat_xyzw(r_rot_delta[w])
            new_r_quat = quat_multiply_xyzw(delta_r_quat, self._ee_quat_right[w])
            new_r_quat = new_r_quat / np.linalg.norm(new_r_quat)
            self._ee_quat_right[w] = new_r_quat.copy()
            # IK target_rotations: xyzw convention (ik_objectives.py:618)
            rot_targets_right.append(
                wp.vec4(float(new_r_quat[0]), float(new_r_quat[1]), float(new_r_quat[2]), float(new_r_quat[3]))
            )

            # Left EE: tracked target + delta
            target_l = self._ee_target_left[w].copy() + l_pos_delta[w]
            target_l[2] = np.clip(target_l[2], PUSH_Z, LIFT_Z + 0.05)
            targets_left[w] = target_l
            self._ee_target_left[w] = target_l.copy()

            # Left rotation: tracked quat + axis-angle delta
            delta_l_quat = axis_angle_to_quat_xyzw(l_rot_delta[w])
            new_l_quat = quat_multiply_xyzw(delta_l_quat, self._ee_quat_left[w])
            new_l_quat = new_l_quat / np.linalg.norm(new_l_quat)
            self._ee_quat_left[w] = new_l_quat.copy()
            rot_targets_left.append(
                wp.vec4(float(new_l_quat[0]), float(new_l_quat[1]), float(new_l_quat[2]), float(new_l_quat[3]))
            )

        # Update batched IK targets (use API methods, not direct assignment)
        pos_l_wp = wp.array([wp.vec3(*targets_left[w]) for w in range(N)], dtype=wp.vec3, device=self.device)
        pos_r_wp = wp.array([wp.vec3(*targets_right[w]) for w in range(N)], dtype=wp.vec3, device=self.device)
        self._ik_obj_pos_left.set_target_positions(pos_l_wp)
        self._ik_obj_pos_right.set_target_positions(pos_r_wp)
        self._ik_obj_rot_left.set_target_rotations(wp.array(rot_targets_left, dtype=wp.vec4, device=self.device))
        self._ik_obj_rot_right.set_target_rotations(wp.array(rot_targets_right, dtype=wp.vec4, device=self.device))

        # Batched IK solve
        self._ik_jq_in.assign(jq_starts)
        self._ik_solver_batch.step(self._ik_jq_in, self._ik_jq_out, iterations=IK_ITERATIONS_RL, step_size=IK_STEP_SIZE)
        jq_targets = self._ik_jq_out.numpy()

        # Handle NaN (fallback to start config)
        nan_mask = np.any(np.isnan(jq_targets), axis=1)
        if np.any(nan_mask):
            jq_targets[nan_mask] = jq_starts[nan_mask]

        # Preserve finger positions (always CLOSED)
        for w in range(N):
            jq_targets[w, 7] = FINGER_CLOSE_POS
            jq_targets[w, 8] = FINGER_CLOSE_POS
            jq_targets[w, FRANKA_NUM_JOINTS + 7] = FINGER_CLOSE_POS
            jq_targets[w, FRANKA_NUM_JOINTS + 8] = FINGER_CLOSE_POS

        # FK interpolation + physics stepping (10 steps, matching ApproachCable)
        for step in range(self.PHYSICS_STEPS_PER_RL):
            t = min((step + 1) / self.PHYSICS_STEPS_PER_RL, 1.0)

            # Interpolate arm joints (linear)
            jq_interp_all = jq_starts.copy()
            jq_interp_all[:, finger_mask] = (
                jq_starts[:, finger_mask] + (jq_targets[:, finger_mask] - jq_starts[:, finger_mask]) * t
            )
            # Fingers stay CLOSED (no transition)
            for fc in (7, 8, FRANKA_NUM_JOINTS + 7, FRANKA_NUM_JOINTS + 8):
                jq_interp_all[:, fc] = FINGER_CLOSE_POS

            # Batched FK eval
            self._batched_fk_jq.assign(jq_interp_all)
            eval_fk_batched(
                self._fk_model, self._batched_fk_jq, self._batched_fk_jqd, self._batched_fk_bq, self._batched_fk_bqd
            )
            batch_bq = self._batched_fk_bq.numpy()[:, :ROBOT_BODY_COUNT]

            # Broadcast FK to physics (all robot bodies are kinematic)
            phys_bq = self._state_0.body_q.numpy()
            for w in range(N):
                ws = self._bws[w]
                for bi in range(ROBOT_BODY_COUNT):
                    phys_bq[ws + bi] = batch_bq[w, bi]
            self._state_0.body_q.assign(phys_bq)

            # Physics step
            self._physics_step_all(substeps=RL_SIM_SUBSTEPS, sim_dt=RL_SIM_DT)

        # Save final FK state per world
        for w in range(N):
            self._per_world_fk_jq[w] = jq_targets[w].copy()

    # =========================================================================
    # RSL-RL VecEnv Interface
    # =========================================================================

    @property
    def num_obs(self):
        return 45

    def get_observations(self) -> tuple[torch.Tensor, dict]:
        obs = self._compute_obs_batch()
        return obs, {"observations": {}}

    def reset(self) -> tuple[torch.Tensor, dict]:
        self._reset_worlds(list(range(self._world_count)))
        return self.get_observations()

    def export_chain_state(self, *, world_idx=0, step_id=0):
        """Export shared Newton state for an opt-in no-reset chain handoff."""

        return export_chain_state_from_env(
            self,
            source_skill="IC",
            world_idx=world_idx,
            step_id=step_id,
            validation_metadata={"stage": "stage0_tracked_api"},
        )

    def import_chain_state(self, state, *, world_idx=0, validate=True):
        """Import shared Newton state for an opt-in no-reset chain handoff."""

        return import_chain_state_into_env(self, state, target_skill="IC", validate=validate)

    def validate_chain_state(self, state, *, world_idx=0):
        """Validate a chain state against this environment without reset."""

        return validate_chain_state_for_env(self, state, target_skill="IC")

    def step_chain(self, actions: torch.Tensor, *, auto_reset: bool = False):
        """Run an opt-in chain step while preserving default :meth:`step` behavior."""

        if auto_reset:
            return self.step(actions)
        actions = torch.nan_to_num(actions, nan=0.0).clamp(-1.0, 1.0)

        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        self._update_target_seg_hysteresis(bq)
        self._groove_seg_indices = self._compute_groove_seg_indices(bq)

        self._last_actions = actions
        self._apply_actions_batch(actions)
        self.episode_length_buf += 1
        self._total_env_steps += self._world_count

        rewards, dones, extras = self._compute_rewards_dones_batch()
        rewards = torch.nan_to_num(rewards, nan=-10.0, posinf=0.0, neginf=-10.0)
        obs = self._compute_obs_batch()
        return obs, rewards, dones, extras

    def step(self, actions: torch.Tensor):
        actions = torch.nan_to_num(actions, nan=0.0).clamp(-1.0, 1.0)

        # Dynamic segment index update with ±1 hysteresis (target seg) + full
        # recompute (groove seg).  Hysteresis prevents gradient oscillation from
        # cable-sway-induced target jumps while still tracking genuine arm drift.
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        self._update_target_seg_hysteresis(bq)
        self._groove_seg_indices = self._compute_groove_seg_indices(bq)

        self._last_actions = actions
        self._apply_actions_batch(actions)
        self.episode_length_buf += 1
        self._total_env_steps += self._world_count

        rewards, dones, extras = self._compute_rewards_dones_batch()
        rewards = torch.nan_to_num(rewards, nan=-10.0, posinf=0.0, neginf=-10.0)

        # Auto-reset done worlds
        done_ids = torch.where(dones > 0)[0].tolist()
        if done_ids:
            self._reset_worlds(done_ids)
            self._episode_count += len(done_ids)

        obs, obs_extras = self.get_observations()
        extras["observations"] = obs_extras.get("observations", {})

        return obs, rewards, dones, extras

    def close(self):
        pass
