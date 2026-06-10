# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Newton VBD ApproachCable RL environment — Multi-world RSL-RL VecEnv (v5).

Independent ApproachCable skill (DAPG Approach A).
Task: Approach cable on table with dual arms (finger always OPEN).
Obs (42D): clamp pos+quat × 2 arms + finger × 2 + target seg pos+quat + clip pos+quat + ori_error axis-angle + pos_error XYZ (right) + ori_error_l + pos_error_l (left).
Action (12D): EE delta XYZ + axis-angle × 2 arms. Finger auto-controlled (STEP table).
Reward: pose_match (R_pos + R_ori + R_step + R_task + R_penalty).

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/train_approach_cable.py --world-count 4
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
import test_newton_clip_routing as _tncr
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
from task_config import (
    CABLE_RADIUS,
    CABLE_SEG_LEN,
    CABLE_SEGMENTS,
    CABLE_XY_DR_AMPLITUDE,
    CLIP_BASE_HEIGHT,
    EE_TO_FINGERTIP,
    FINGER_LOCAL,
    FINGER_OPEN_POS,
    GRASP_TERMINAL_STEPS,
    GRASP_X,
    GRASP_Z,
    GRIPPER_DRIVER_JOINT_IDX,
    GRIPPER_JOINT_RANGE,
    GRIPPER_PAD_BODY_IDX,
    JOINTS_PER_ARM,
    K_GRASP,
    LIFT_Z,
    NJMAX,
    ROBOT_BODIES_PER_ARM,
    SETTLE_STEPS,
    SIM_SUBSTEPS,
    T_ALIGN,
    T_DIST_APPROACH,
    TABLE_HEIGHT,
    WIDE_LEFT_Y,
    WIDE_RIGHT_Y,
)

# Constants
DT = 1.0 / 480.0
SIM_DT = DT / SIM_SUBSTEPS  # Cable settling dt (full precision)
RL_SIM_SUBSTEPS = 4  # Reduced substeps for RL speed
RL_SIM_DT = DT / RL_SIM_SUBSTEPS  # RL stepping dt
IK_ITERATIONS_INIT = 100  # Full iterations for P0 precondition
IK_ITERATIONS_RL = 30  # Warm-started for RL small deltas
IK_STEP_SIZE = 1.0
ROBOT_BODY_COUNT = 2 * ROBOT_BODIES_PER_ARM  # 18 (both arms)

# IK rotation targets: hand down, fingers perpendicular to cable Y-axis.
# Newton IK wp.vec4 uses (x, y, z, w) convention — same as wp.quat.
# 180° rotation around axis (cos(pi/8), sin(pi/8), 0): quat_xyzw = [cos(pi/8), sin(pi/8), 0, 0]
_cos_pi8 = math.cos(math.pi / 8)
_sin_pi8 = math.sin(math.pi / 8)

# Clip position — from task_config SSOT
from cable_orientation_utils import compute_hand_quat_for_cable
from newton_skill_env_base import (
    assign_world_states_to_sim,
    axis_angle_to_quat_xyzw,
    compute_clamp_pos,
    compute_ori_error_axis_angle,
    extract_clamp_pose,
    find_nearest_cable_point,
    make_solver,
    normalize_quat_w_positive,
    quat_distance,
    quat_multiply_xyzw,
    reset_dahl_friction_for_envs,
    restore_ee_targets_per_world,
    restore_world_body_state,
    temporal_quat_consistency,
)
from task_config import CLIP1_X, CLIP1_Y, CLIP1_Z

# Dynamic finger spring parameters (aligned with AerialRegrasp Mode 2)
FINGER_SPRING_KE = 10000.0  # Position spring stiffness [N/m]
FINGER_SPRING_KD = 500.0  # Velocity damping [N·s/m]
FINGER_DYNAMIC_INV_MASS = 20.0  # 1/0.05kg
FINGER_DYNAMIC_INV_INERTIA = 100.0  # Approximate


class NewtonApproachCableEnv(VecEnv):
    """RSL-RL VecEnv for ApproachCable — multi-world with replicate().

    v5 unified obs/action/reward design.

    Observation (42D per world):
        [0:3]   Right clamp position XYZ [m]
        [3:7]   Right clamp quaternion (qx, qy, qz, qw), w >= 0
        [7]     Right finger opening (j7 + j8) [m]
        [8:11]  Left clamp position XYZ [m]
        [11:15] Left clamp quaternion (qx, qy, qz, qw), w >= 0
        [15]    Left finger opening (j7 + j8) [m]
        [16:19] Target cable segment position XYZ [m]
        [19:23] Target cable segment quaternion (qx, qy, qz, qw), w >= 0
        [23:26] Clip position XYZ [m]
        [26:30] Clip quaternion (qx, qy, qz, qw), w >= 0
        [30:33] Right orientation error axis-angle [rad] (hand → grasp target)
        [33:36] Right position error XYZ [m] (hand clamp → target segment)
        [36:39] Left orientation error axis-angle [rad] (hand → grasp target)
        [39:42] Left position error XYZ [m] (hand clamp → target segment)

    Action (12D per world):
        [0:3]   Right EE delta XYZ * POS_ACTION_SCALE [m]
        [3:6]   Right EE delta axis-angle * ROT_ACTION_SCALE [rad]
        [6:9]   Left EE delta XYZ * POS_ACTION_SCALE [m]
        [9:12]  Left EE delta axis-angle * ROT_ACTION_SCALE [rad]

    Finger control: always OPEN (approach-only skill). Grasp is a separate skill.
    """

    # Action scaling
    POS_ACTION_SCALE = 0.015  # 15mm per RL step for EE position delta (3x to compensate ori-induced clamp shift)
    ROT_ACTION_SCALE = 0.05  # ~2.9° per RL step for EE rotation delta (axis-angle rad)
    ADAPTIVE_POS_SCALE = True  # Distance-adaptive pos scale for 1mm precision
    FINE_THRESHOLD = 0.050  # 50mm: below this distance, pos action scale shrinks linearly
    MIN_POS_SCALE = 0.0005  # 0.5mm: minimum pos action scale (caps adaptive reduction)
    MAX_EPISODE_STEPS = GRASP_TERMINAL_STEPS
    PHYSICS_STEPS_PER_RL = 10
    EXPLOSION_DIST_THRESH = 1.0  # Early-reset worlds where dist_pos > 1m (VBD explosion guard)

    # Target cable segment: per-arm nearest (±GRIP_SEG_WINDOW)
    GRIP_SEG_WINDOW = 5  # ±5 segment tolerance (11 segments = 165mm range, matching AR)
    INIT_XY_NOISE = 0.005  # ±5mm initial EE position randomization (was 2mm — P3 curriculum fix 2026-04-20 for 30% persistent-failure worlds)

    # Reward: pose_match (v37) — non-negative shift [0, 1] (IC v36 pattern)
    REWARD_MODE = "hybrid"  # "exp" | "hybrid" | "multiplicative"
    EPS_POS = 0.015  # 15mm position decay length [m] (precision gradient)
    EPS_POS_MED = 0.10  # v37: 100mm mid-range decay (bridges gradient desert 15mm-1m)
    EPS_POS_COARSE = 1.0  # hybrid mode: coarse scale [m] (long-range gradient)
    EPS_ORI = 0.25  # 0.25 rad (~14°) orientation decay length [rad]
    EPS_ORI_COARSE = 1.5  # 1.5 rad (~86°) coarse ori decay (long-range gradient, mirrors pos 3-scale)
    W_POS = 0.5  # v37: halved (non-negative shift — per-arm avg range [0, 1])
    W_ORI = 0.5  # v37: halved (non-negative shift — per-arm range [0, 0.5])
    # Multiplicative reward (RL-Routing-Design §4.3):
    #   progress = (progress_r + progress_l), each = 0.2*score_pos + 0.2*score_ori + 0.6*score_pos*score_ori
    #   R = PROGRESS_SCALE * (progress - 2.0)   range: [-2*PROGRESS_SCALE, 0]
    RANGE_POS = 0.015  # 15mm: score_pos exp decay length [m] (v26: tighter gradient for 5mm→3mm finger-close zone)
    RANGE_ORI = 0.5  # 0.5 rad: score_ori exp decay length (1.0→0.5 for stronger ori gradient)
    PROGRESS_SCALE = 2.0  # Scale factor ([-2, 0] matches exp reward range)
    PROGRESS_W_POS = 0.2  # Independent pos weight in multiplicative reward
    PROGRESS_W_ORI = 0.2  # Independent ori weight in multiplicative reward
    PROGRESS_W_COUPLED = 0.6  # Coupled pos*ori weight in multiplicative reward
    R_STEP_BONUS = 5.0  # STEP completion bonus (pose_match achieved)
    R_TASK_BONUS = 200.0  # v37: 20→200 (anti-hover: success must dominate hover)
    # R_PENALTY calibrated to zero-out non-negative reward at P0 (both arms @31.6mm, ori~0.15):
    #   r_pos_P0 = 0.5*((exp(-31.6/15)+exp(-31.6/100)+exp(-31.6/1000))/3 * 2arms) = 0.607
    #   r_ori_P0 = 0.5*((exp(-0.15/0.25)+exp(-0.15/1.5))/2 * 2arms) = 0.727
    #   R_PENALTY = -(0.607+0.727) = -1.334 ≈ -1.33
    R_PENALTY = -1.33  # v37: calibrated incl. coarse ori (idle@P0 ≈ 0, approach > 0)
    W_HOLD = 0.0  # v37: 0.3→0 (eliminated — CLOSE_ACTION_DAMPING handles mechanically)

    CLOSE_ACTION_DAMPING = 0.3  # v37: 0.1→0.3 (allow L arm to learn approach, was 10x too slow)
    ORI_GATE_POS_THRESH = 0.010  # 10mm: ori-gated approach zone radius
    ORI_GATE_ORI_THRESH = 0.2618  # 15°: ori must be below this before close approach

    # SUCCESS condition: approach(pos + ori) ∧ sustained (v3)
    # finger close is NOT part of this skill — handled by Grip.
    # Values from task_config.py (07-Design SSOT). Do NOT hardcode overrides.
    CLAMP_DIST_THRESH = T_DIST_APPROACH  # approach.pos: 12mm (Grip INIT_POS_NOISE=12mmと整合)
    CLAMP_ORI_THRESH = T_ALIGN  # clamp.ori: 10° (0.1745 rad)
    C5_SUSTAIN_STEPS = K_GRASP  # sustained: K_GRASP RL steps (design doc: 5)

    # Clip C1 pose (constant for ApproachCable obs — not reward target)
    # Groove axis ≈ Y (cable runs along Y through C1)
    CLIP1_POS = np.array([CLIP1_X, CLIP1_Y, CLIP1_Z], dtype=np.float32)
    CLIP1_QUAT_XYZW = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)  # identity

    # Cache directory for saved precondition states
    CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "rl_grasp_cache")
    PRECONDITION_CACHE_OVERRIDE = None  # set to .npz path to use custom precondition
    TERMINAL_STEPS_OVERRIDE = None  # set to override MAX_EPISODE_STEPS
    OBS_L_ARM_MASK_PROB = 0.0  # v37: 0.3→0 (L arm obs must be visible — success requires both arms)

    def __init__(self, world_count=4, device="cuda:0", cfg=None, enable_camera=False):
        self.num_envs = world_count
        self.num_actions = 12
        self._total_env_steps = 0
        terminal = self.TERMINAL_STEPS_OVERRIDE or self.MAX_EPISODE_STEPS
        self.max_episode_length = terminal
        self.device = device
        self.cfg = cfg or {}
        self._world_count = world_count

        self.episode_length_buf = torch.zeros(world_count, dtype=torch.long, device=device)
        self._target_seg_indices_r = None  # [world_count, n_target_segs] — right arm
        self._target_seg_indices_l = None  # [world_count, n_target_segs] — left arm
        self._success_sustain_count = np.zeros(world_count, dtype=np.int32)
        self._step_completed_right = np.zeros(world_count, dtype=bool)  # STEP bonus tracking
        self._last_actions = None  # [N, 12] tensor for r_hold computation
        self._episode_count = 0
        # Option C' (2026-04-25): cable XY domain randomization flag
        # Default False preserves existing fixed-cable behavior. Enable via
        # set_cable_xy_randomize(True) before first reset (see task_config.py
        # CABLE_XY_DR_AMPLITUDE for magnitude).
        self._randomize_cable_xy: bool = False
        self._episode_success_buf = deque(maxlen=200)
        self._last_success_rate = 0.0

        # Per-world EE targets: maintained explicitly to avoid FK/body_q drift.
        # Initialized from precondition EE positions; deltas applied to these.
        self._ee_target_right = np.zeros((world_count, 3), dtype=np.float32)
        self._ee_target_left = np.zeros((world_count, 3), dtype=np.float32)
        self._ee_quat_right = np.zeros((world_count, 4), dtype=np.float32)  # xyzw
        self._ee_quat_left = np.zeros((world_count, 4), dtype=np.float32)  # xyzw

        # Bug #2 fix: temporal quat consistency (avoid sign flip at w≈0)
        self._prev_clamp_r_quat = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))
        self._prev_clamp_l_quat = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))
        self._prev_seg_r_quat = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))
        self._prev_seg_l_quat = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))

        # Override device for Newton
        os.environ["NEWTON_DEVICE"] = device
        _tncr.DEVICE = device

        print(f"[ApproachCableEnv] Initializing: {world_count} worlds on {device}")
        t0 = time.perf_counter()

        # Phase 1: Build model (FK + proto + replicate + finalize + solver)
        self._build_model()

        # Phase 2 visual obs: optional wrist camera
        self._camera = None
        self._visual_encoder = None
        self._visual_feature_dim = 0
        if enable_camera:
            from wrist_camera_manager import WristCameraManager

            self._camera = WristCameraManager(
                model=self._model,
                bws=self._bws,
                world_count=self._world_count,
                device=self.device,
            )
            print(
                f"[ApproachCableEnv] Camera enabled: {self._camera.camera_count} cameras, "
                f"{self._camera.resolution}x{self._camera.resolution}"
            )
            # Phase 3: frozen encoder for visual obs → compact features
            _models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
            sys.path.insert(0, _models_dir)
            from visual_encoder import FrozenResNetEncoder

            _per_cam_dim = 64
            self._visual_encoder = FrozenResNetEncoder(out_dim=_per_cam_dim).to(self.device)
            self._visual_encoder.eval()  # batchnorm in eval mode
            self._visual_feature_dim = _per_cam_dim * self._camera.camera_count  # 64 * 2 = 128
            print(
                f"[ApproachCableEnv] Visual encoder: ResNet-18 frozen + "
                f"projection(512→{_per_cam_dim}) × {self._camera.camera_count} cams = "
                f"{self._visual_feature_dim}D"
            )

        # Phase 2: Try cache -> skip cable settling
        if self._load_precondition_cache():
            self._restore_from_cache()
        else:
            # No cache: settle cable + position arms (slow path)
            self._settle_cable()
            self._setup_p0_precondition()
            self._save_precondition_state()
            self._save_precondition_cache()

        # Phase 2.5: Make finger bodies dynamic for spring-based grip (AR-aligned)
        self._init_dynamic_fingers()

        # Phase 3: Batched IK solver for RL stepping
        self._init_batched_ik_solver()

        print(
            f"[ApproachCableEnv] Ready in {time.perf_counter() - t0:.1f}s. "
            f"obs={self.num_obs}, act={self.num_actions}, worlds={world_count}"
        )

    # =========================================================================
    # Environment Construction
    # =========================================================================

    def _build_model(self):
        """Build FK model + multi-world physics scene + VBD solver (no settling)."""
        # FK model (single, shared -- used for IK solving)
        print("[ApproachCableEnv] Building FK model...")
        self._fk_model = build_fk_model()
        self._fk_state = self._fk_model.state()

        # Initialize FK to URDF home config with fingers open
        fk_jq = self._fk_state.joint_q.numpy()
        fk_tp = self._fk_model.joint_target_pos.numpy()
        fk_jq[:] = fk_tp[:]
        # Both arms: OPEN (dual clamp design)
        fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
        fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS
        fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
        fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS
        self._fk_state.joint_q.assign(fk_jq)
        newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)

        # Per-world FK joint state storage (N worlds x joint_coord_count)
        self._per_world_fk_jq = np.tile(fk_jq, (self._world_count, 1))  # [N, joint_coord_count]

        # Build multi-world physics scene (no cable settling)
        self._build_multiworld_physics()

    def _build_multiworld_physics(self):
        """Build proto -> replicate -> finalize multi-world physics model."""
        # --- Proto: per-world entities (robot kinematic bodies + cable) ---
        print("[ApproachCableEnv] Building world prototype...")
        proto = newton.ModelBuilder()

        # Robot arms (kinematic bodies, no joints)
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

        # Cable (Cosserat Rod) — rests on clip base plates
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
        self._cable_body_offset = cable_bodies_proto[0]  # First cable body index within proto

        # Cable-arm filter pairs (within proto)
        for cable_si in range(cable_shape_start_idx, cable_shape_end_idx):
            for arm_ss, arm_se, arm_bs in [
                (left_shape_start, left_shape_end, left_body_start),
                (right_shape_start, right_shape_end, right_body_start),
            ]:
                for arm_si in range(arm_ss, arm_se):
                    local = proto.shape_body[arm_si] - arm_bs
                    if local not in GRIPPER_PAD_BODY_IDX:
                        proto.add_shape_collision_filter_pair(cable_si, arm_si)

        # Finger collision is now BOX primitives (no approximate_meshes needed)

        self._bodies_per_world = proto.body_count  # robot + cable bodies
        print(
            f"[ApproachCableEnv] Proto: {proto.body_count} bodies, "
            f"{proto.joint_count} joints, {proto.shape_count} shapes"
        )

        # --- Scene: global entities + replicate ---
        print(f"[ApproachCableEnv] Building scene ({self._world_count} worlds)...")
        scene = newton.ModelBuilder(gravity=GRAVITY)

        # Ground plane (global, body=-1)
        self._floor_shape_idx = scene.add_ground_plane()

        # Table (global, body=-1)
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

        # Cable support clips (collision-enabled, body=-1 static)
        # 3 clips along cable at GRASP_X, avoiding grasp area (Y=0.090..0.210)
        clip_cfg = newton.ModelBuilder.ShapeConfig()
        clip_cfg.ke = 2500.0  # Match cable contact stiffness
        clip_cfg.kd = 100.0
        clip_cfg.mu = 1.0
        clip_cfg.gap = 0.001  # 1mm
        # V-groove geometry (from test_newton_clip_routing / Mechanical-Specs §5)
        clip_parts = [
            (0, 0, 0.0025, 0.020, 0.015, 0.0025),  # Base plate
            (-0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),  # Left inner wall
            (+0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),  # Right inner wall
            (-0.013, 0, 0.025, 0.002, 0.015, 0.005),  # Left outer wall
            (+0.013, 0, 0.025, 0.002, 0.015, 0.005),  # Right outer wall
        ]
        support_clip_ys = [-0.100, +0.050, +0.300]  # Avoid grasp zone (0.090..0.210)
        for clip_y in support_clip_ys:
            for dx, dy, dz, hx, hy, hz in clip_parts:
                xf = wp.transform(
                    (GRASP_X + dx, clip_y + dy, TABLE_HEIGHT + dz),
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
        print(f"[ApproachCableEnv] Added {len(support_clip_ys)} support clips at X={GRASP_X}")

        # Replicate proto to N worlds
        scene.replicate(proto, world_count=self._world_count)

        # Color for VBD
        scene.color()

        # Finalize
        self._model = scene.finalize(device=self.device, requires_grad=False)
        print(
            f"[ApproachCableEnv] Model: {self._model.body_count} bodies, "
            f"{self._model.joint_count} joints, {self._model.shape_count} shapes"
        )

        # World index arrays
        self._bws = self._model.body_world_start.numpy()
        self._jws = self._model.joint_world_start.numpy()

        # Post-finalize: zero inv_mass for ALL worlds' robot bodies
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

        # Post-finalize: shape flags for finger BOX collision / MESH visual
        model_sflags = self._model.shape_flags.numpy()
        model_stypes = self._model.shape_type.numpy()
        model_sbodies = self._model.shape_body.numpy()
        for si in range(len(model_stypes)):
            bi = model_sbodies[si]
            if bi < 0:
                continue
            # Find which world this body belongs to
            for w in range(self._world_count):
                ws, we = self._bws[w], self._bws[w + 1]
                if ws <= bi < we:
                    local = bi - ws
                    local_l = local - 0  # left arm starts at 0
                    local_r = local - ROBOT_BODIES_PER_ARM  # right arm starts at 9
                    if local_l in GRIPPER_PAD_BODY_IDX or local_r in GRIPPER_PAD_BODY_IDX:
                        if model_stypes[si] == 7:  # BOX = collision only
                            model_sflags[si] = 0x6
                        elif model_stypes[si] == 8:  # MESH = visual only
                            model_sflags[si] = 0x1
                    break
        self._model.shape_flags = wp.array(model_sflags, dtype=self._model.shape_flags.dtype, device=self.device)

        # solver via the SOLVER_BACKEND factory (default "vbd" => byte-identical to the prior SolverVBD)
        self._solver = make_solver(self._model)
        self._model.rigid_contact_max = NJMAX

        # Physics state + contacts
        self._state_0 = self._model.state()
        self._state_1 = self._model.state()
        self._control = self._model.control()
        self._contacts = self._model.contacts()

        # Cable body indices per world (global indices)
        self._cable_bodies = []  # [world_count][n_cable_bodies]
        for w in range(self._world_count):
            start = self._bws[w] + self._cable_body_offset
            self._cable_bodies.append(list(range(start, start + self._cable_bodies_per_world)))

        # Right arm finger body indices per world (global indices)
        # Right arm body 7 = right_finger_link, body 8 = left_finger_link
        self._right_finger_bodies = []  # [world_count][2]
        for w in range(self._world_count):
            ws = self._bws[w]
            self._right_finger_bodies.append(
                [
                    ws + ROBOT_BODIES_PER_ARM + 7,  # right arm finger body 7
                    ws + ROBOT_BODIES_PER_ARM + 8,  # right arm finger body 8
                ]
            )

    def _settle_cable(self):
        """Settle cable (2s sim time). Only needed for first-time P0 setup."""
        print("[ApproachCableEnv] Settling cable (2s)...")
        settle_frames = int(2.0 / DT)
        for _ in range(settle_frames):
            self._physics_step_all()

        # Record settled cable X
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        cable_x = np.mean(bq[self._cable_bodies[0], 0])
        self._settled_grasp_x = float(cable_x)
        print(f"[ApproachCableEnv] Cable settled: mean_x={cable_x:.4f}")

    # =========================================================================
    # Physics Stepping
    # =========================================================================

    def _broadcast_fk_to_all_worlds(self):
        """Copy current FK body transforms to all worlds' robot bodies."""
        fk_bq = self._fk_state.body_q.numpy()[:ROBOT_BODY_COUNT]
        phys_bq = self._state_0.body_q.numpy()
        for w in range(self._world_count):
            start = self._bws[w]
            phys_bq[start : start + ROBOT_BODY_COUNT] = fk_bq
        self._state_0.body_q.assign(phys_bq)

    def _broadcast_per_world_fk(self):
        """Copy per-world FK body transforms to physics model.

        Uses self._per_world_fk_jq[w] for each world's FK joint positions.
        """
        phys_bq = self._state_0.body_q.numpy()
        for w in range(self._world_count):
            # Set FK joint positions for this world
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
            f"[ApproachCableEnv] Dynamic fingers: {len(self._finger_physics_ids)} bodies "
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
                    vel = body_qd[bi][3:6]  # linear velocity
                    target = fk_batch_bq[w, local_bi, :3]
                    force = -FINGER_SPRING_KE * (pos - target) - FINGER_SPRING_KD * vel
                    body_f[bi][3:6] += force
        self._state_0.body_f.assign(body_f)

    def _physics_step_all(self, substeps=None, sim_dt=None, fk_batch_bq=None, n_worlds=None):
        """One physics frame for all worlds.

        Args:
            substeps: Override substep count (default: SIM_SUBSTEPS for init).
            sim_dt: Override substep dt (default: SIM_DT for init).
            fk_batch_bq: FK body positions [N, ROBOT_BODY_COUNT, 7] for finger spring.
            n_worlds: Number of worlds for finger spring.
        """
        n_sub = substeps if substeps is not None else SIM_SUBSTEPS
        dt = sim_dt if sim_dt is not None else SIM_DT
        for _ in range(n_sub):
            self._state_0.clear_forces()
            if fk_batch_bq is not None and n_worlds is not None:
                self._apply_finger_spring(fk_batch_bq, n_worlds)
            self._model.collide(self._state_0, self._contacts)
            self._solver.step(self._state_0, self._state_1, self._control, self._contacts, dt)
            self._state_0, self._state_1 = self._state_1, self._state_0

    # =========================================================================
    # P0 Precondition Setup
    # =========================================================================

    def _setup_p0_precondition(self):
        """Position arms at cable-proximal height (fingertip ~10mm above cable center).

        Approach is handled by P0, not RL. RL starts from grasp-ready position.
        EE_Z = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS + 10mm + EE_TO_FINGERTIP
        """
        print("[ApproachCableEnv] Setting up P0 precondition...")
        grasp_x = self._settled_grasp_x

        # Fingertip 10mm above cable center (cable on clips) → EE height
        p0_ee_z = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS + 0.010 + EE_TO_FINGERTIP  # 1.039m

        # Move both arms to grasp-ready position
        self._ik_move_all_worlds(
            (grasp_x, WIDE_LEFT_Y, p0_ee_z),
            (grasp_x, WIDE_RIGHT_Y, p0_ee_z),
            label="P0-GRASP-READY",
            converge_mm=10.0,
        )
        self._hold_all_worlds(SETTLE_STEPS)
        print("[ApproachCableEnv] P0 complete -- precondition reached")

    def _init_batched_ik_solver(self):
        """Create cached IKSolver with n_problems=world_count for batched solving."""
        N = self._world_count
        fk_model = self._fk_model
        left_ee = EE_BODY_OFFSET
        right_ee = FRANKA_NUM_JOINTS + EE_BODY_OFFSET

        rot_quat = wp.vec4(_cos_pi8, _sin_pi8, 0.0, 0.0)

        # Placeholder targets (updated in-place each step)
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

        # Pre-allocate IK I/O buffers
        coord_count = fk_model.joint_coord_count
        self._ik_jq_in = wp.zeros((N, coord_count), dtype=float, device=self.device)
        self._ik_jq_out = wp.zeros((N, coord_count), dtype=float, device=self.device)

        # Pre-allocate batched FK buffers (for interpolation loop)
        dof_count = fk_model.joint_dof_count
        body_count = fk_model.body_count
        self._batch_fk_jq = wp.zeros((N, coord_count), dtype=float, device=self.device)
        self._batch_fk_jqd = wp.zeros((N, dof_count), dtype=float, device=self.device)
        self._batch_fk_body_q = wp.zeros((N, body_count), dtype=wp.transform, device=self.device)
        self._batch_fk_body_qd = wp.zeros((N, body_count), dtype=wp.spatial_vector, device=self.device)

        print(f"[ApproachCableEnv] Batched IK solver: n_problems={N}, joint_coords={coord_count}")

    def _solve_ik_batch(self, targets_left_np, targets_right_np, jq_starts_np):
        """Solve IK for all worlds in one batched call.

        Args:
            targets_left_np: [N, 3] numpy -- left arm target positions per world.
            targets_right_np: [N, 3] numpy -- right arm target positions per world.
            jq_starts_np: [N, joint_coord_count] numpy -- initial joint positions per world.

        Returns:
            [N, joint_coord_count] numpy -- solved joint positions.
        """
        N = self._world_count
        # Update targets on GPU
        self._ik_obj_pos_left.set_target_positions(wp.array(targets_left_np, dtype=wp.vec3, device=self.device))
        self._ik_obj_pos_right.set_target_positions(wp.array(targets_right_np, dtype=wp.vec3, device=self.device))

        # Set initial joint positions
        self._ik_jq_in.assign(jq_starts_np)

        # Solve (reduced iterations -- warm-started from previous solution)
        self._ik_solver_batch.step(
            self._ik_jq_in,
            self._ik_jq_out,
            iterations=IK_ITERATIONS_RL,
            step_size=IK_STEP_SIZE,
        )

        return self._ik_jq_out.numpy()

    def _solve_ik_single(self, target_left, target_right):
        """Solve IK for both arms (single problem, used for P0 init)."""
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

    def _ik_move_all_worlds(self, target_left, target_right, label="MOVE", converge_mm=5.0):
        """Move both arms to target -- all worlds get same IK solution."""
        from task_config import MAX_MOVE_STEPS

        jq_target = self._solve_ik_single(target_left, target_right)
        if np.any(np.isnan(jq_target)):
            print(f"  [{label}] IK FAILED (NaN)")
            return False

        jq_start = self._fk_state.joint_q.numpy().copy()
        finger_coords = set(GRIPPER_JOINT_RANGE) | {JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE}
        n_coords = self._fk_model.joint_coord_count

        err_l = 0.0
        err_r = 0.0
        for step in range(MAX_MOVE_STEPS):
            t = min((step + 1) / MAX_MOVE_STEPS, 1.0)
            jq_interp = jq_start.copy()
            for d in range(n_coords):
                if d not in finger_coords:
                    jq_interp[d] = jq_start[d] + (jq_target[d] - jq_start[d]) * t

            self._fk_state.joint_q.assign(jq_interp)
            newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)
            self._broadcast_fk_to_all_worlds()
            self._physics_step_all()

            # Check convergence
            if (step + 1) % 10 == 0:
                wp.synchronize()
                bq = self._state_0.body_q.numpy()
                w0_start = self._bws[0]
                left_ee_pos = bq[w0_start + EE_BODY_OFFSET][:3]
                right_ee_pos = bq[w0_start + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
                err_l = np.linalg.norm(left_ee_pos - np.array(target_left)) * 1000
                err_r = np.linalg.norm(right_ee_pos - np.array(target_right)) * 1000
                if max(err_l, err_r) < converge_mm:
                    break

        print(f"  [{label}] Done: steps={step + 1}, err_L={err_l:.1f}mm, err_R={err_r:.1f}mm")
        return True

    def _hold_all_worlds(self, n_frames):
        """Hold position for n_frames physics frames."""
        for _ in range(n_frames):
            self._broadcast_fk_to_all_worlds()
            self._physics_step_all()

    # =========================================================================
    # Target Segment Computation
    # =========================================================================

    def _compute_target_seg_indices(self, bq):
        """Compute target cable segment indices per arm (±GRIP_SEG_WINDOW each)."""
        n_cable = self._cable_bodies_per_world
        win = self.GRIP_SEG_WINDOW
        n_seg = 2 * win + 1
        result_r = np.zeros((self._world_count, n_seg), dtype=np.int32)
        result_l = np.zeros((self._world_count, n_seg), dtype=np.int32)
        for w in range(self._world_count):
            ws = self._bws[w]
            cable_pos = bq[self._cable_bodies[w], :3]

            # Right arm (rotation-aware fingertip position)
            right_ee_idx = ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
            right_tip = compute_clamp_pos(bq[right_ee_idx][:3], bq[right_ee_idx][3:7])
            right_seg = int(np.argmin(np.linalg.norm(cable_pos - right_tip, axis=1)))
            result_r[w] = np.clip(np.arange(right_seg - win, right_seg + win + 1), 0, n_cable - 1)

            # Left arm (rotation-aware fingertip position)
            left_ee_idx = ws + EE_BODY_OFFSET
            left_tip = compute_clamp_pos(bq[left_ee_idx][:3], bq[left_ee_idx][3:7])
            left_seg = int(np.argmin(np.linalg.norm(cable_pos - left_tip, axis=1)))
            result_l[w] = np.clip(np.arange(left_seg - win, left_seg + win + 1), 0, n_cable - 1)
        return result_r, result_l

    def _update_target_seg_hysteresis(self, bq):
        """Update target seg indices with ±1 hysteresis.

        Only updates when the nearest cable segment center changes by more
        than ±1 from the current center.  This prevents target position jumps
        caused by window boundary shifts when the cable sways, which was
        observed to destabilise the right-arm gradient in AC v39.
        """
        n_cable = self._cable_bodies_per_world
        win = self.GRIP_SEG_WINDOW

        for w in range(self._world_count):
            ws = self._bws[w]
            cable_pos = bq[self._cable_bodies[w], :3]

            # Right arm (rotation-aware fingertip position)
            right_ee_idx = ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
            right_tip = compute_clamp_pos(bq[right_ee_idx][:3], bq[right_ee_idx][3:7])
            new_center_r = int(np.argmin(np.linalg.norm(cable_pos - right_tip, axis=1)))
            prev_center_r = int(self._target_seg_indices_r[w][win])
            if abs(new_center_r - prev_center_r) > 1:
                self._target_seg_indices_r[w] = np.clip(
                    np.arange(new_center_r - win, new_center_r + win + 1), 0, n_cable - 1
                )

            # Left arm (rotation-aware fingertip position)
            left_ee_idx = ws + EE_BODY_OFFSET
            left_tip = compute_clamp_pos(bq[left_ee_idx][:3], bq[left_ee_idx][3:7])
            new_center_l = int(np.argmin(np.linalg.norm(cable_pos - left_tip, axis=1)))
            prev_center_l = int(self._target_seg_indices_l[w][win])
            if abs(new_center_l - prev_center_l) > 1:
                self._target_seg_indices_l[w] = np.clip(
                    np.arange(new_center_l - win, new_center_l + win + 1), 0, n_cable - 1
                )

    # =========================================================================
    # State Management
    # =========================================================================

    def _save_precondition_state(self):
        """Save P0-complete state for episode reset."""
        wp.synchronize()
        self._settled_body_q = self._state_0.body_q.numpy().copy()
        self._settled_body_qd = self._state_0.body_qd.numpy().copy()
        self._settled_fk_jq = self._fk_state.joint_q.numpy().copy()
        self._settled_inv_mass = self._model.body_inv_mass.numpy().copy()
        self._settled_inv_inertia = self._model.body_inv_inertia.numpy().copy()

        # Cache per-world initial FK
        for w in range(self._world_count):
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()

        # Cache EE positions
        bq = self._settled_body_q
        w0 = self._bws[0]
        self._left_ee_hold = bq[w0 + EE_BODY_OFFSET][:3].copy()
        self._right_ee_start = bq[w0 + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3].copy()

        self._target_seg_indices_r, self._target_seg_indices_l = self._compute_target_seg_indices(bq)

        # Cache settled EE poses from FK (used by _reset_worlds)
        fk_bq = self._fk_state.body_q.numpy()
        self._settled_ee_r_pos = fk_bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3].copy()
        self._settled_ee_r_quat = fk_bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][3:7].copy()
        self._settled_ee_l_pos = fk_bq[EE_BODY_OFFSET][:3].copy()
        self._settled_ee_l_quat = fk_bq[EE_BODY_OFFSET][3:7].copy()

        # Init per-world EE targets from settled poses
        for w in range(self._world_count):
            self._ee_target_right[w] = self._settled_ee_r_pos.copy()
            self._ee_target_left[w] = self._settled_ee_l_pos.copy()
            self._ee_quat_right[w] = self._settled_ee_r_quat.copy()
            self._ee_quat_left[w] = self._settled_ee_l_quat.copy()

        print(
            f"[ApproachCableEnv] Precondition saved: "
            f"L_EE={self._left_ee_hold}, R_EE={self._right_ee_start}, "
            f"target_seg_r={self._target_seg_indices_r[0]}, "
            f"target_seg_l={self._target_seg_indices_l[0]}"
        )

    def _cache_path(self):
        if self.PRECONDITION_CACHE_OVERRIDE is not None:
            return self.PRECONDITION_CACHE_OVERRIDE
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        return os.path.join(self.CACHE_DIR, f"grasp_w{self._world_count}_p0_v8.npz")

    def _save_precondition_cache(self):
        """Save precondition state to disk for fast restart."""
        path = self._cache_path()

        np.savez_compressed(
            path,
            body_q=self._settled_body_q,
            body_qd=self._settled_body_qd,
            fk_jq=self._settled_fk_jq,
            inv_mass=self._settled_inv_mass,
            inv_inertia=self._settled_inv_inertia,
            left_ee_hold=self._left_ee_hold,
            right_ee_start=self._right_ee_start,
            settled_grasp_x=np.array([self._settled_grasp_x], dtype=np.float32),
            world_count=np.array([self._world_count], dtype=np.int32),
            body_count=np.array([self._model.body_count], dtype=np.int32),
        )
        print(f"[ApproachCableEnv] Precondition cached to {path}")

    def _load_precondition_cache(self):
        """Try to load cached precondition state. Returns True if successful."""
        path = self._cache_path()
        if not os.path.exists(path):
            print(f"[ApproachCableEnv] No cache at {path}")
            return False
        try:
            data = np.load(path)
            # Validate world_count and body_count
            if int(data["world_count"][0]) != self._world_count:
                print(
                    f"[ApproachCableEnv] Cache world_count mismatch: "
                    f"cache={data['world_count'][0]}, current={self._world_count}"
                )
                return False
            if int(data["body_count"][0]) != self._model.body_count:
                print(
                    f"[ApproachCableEnv] Cache body_count mismatch: "
                    f"cache={data['body_count'][0]}, current={self._model.body_count}"
                )
                return False

            self._settled_body_q = data["body_q"]
            self._settled_body_qd = data["body_qd"]
            self._settled_fk_jq = data["fk_jq"]
            self._settled_inv_mass = data["inv_mass"]
            self._settled_inv_inertia = data["inv_inertia"]
            self._left_ee_hold = data["left_ee_hold"]
            self._right_ee_start = data["right_ee_start"]
            self._settled_grasp_x = float(data["settled_grasp_x"][0])

            print(f"[ApproachCableEnv] Loaded cache from {path}")
            return True
        except Exception as e:
            print(f"[ApproachCableEnv] Cache load failed: {e}")
            return False

    def _restore_from_cache(self):
        """Restore environment state from cached precondition."""
        # Restore physics state
        self._state_0.body_q.assign(self._settled_body_q)
        self._state_0.body_qd.assign(self._settled_body_qd)

        # Restore inv_mass/inv_inertia
        self._model.body_inv_mass = wp.array(
            self._settled_inv_mass, dtype=self._model.body_inv_mass.dtype, device=self.device
        )
        self._model.body_inv_inertia = wp.array(
            self._settled_inv_inertia, dtype=self._model.body_inv_inertia.dtype, device=self.device
        )

        # Restore FK state
        self._fk_state.joint_q.assign(self._settled_fk_jq)
        newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)

        # Restore per-world FK
        for w in range(self._world_count):
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()

        # Sync kinematic bodies to physics
        self._broadcast_fk_to_all_worlds()

        # Restore VBD solver prev state
        if hasattr(self._solver, "body_q_prev") and self._solver.body_q_prev is not None:
            self._solver.body_q_prev.assign(self._settled_body_q)

        # Reset Dahl friction if enabled
        if hasattr(self._solver, "enable_dahl_friction") and self._solver.enable_dahl_friction:
            if self._solver.joint_C_fric is not None:
                self._solver.joint_C_fric.zero_()
            if self._solver.joint_sigma_prev is not None:
                self._solver.joint_sigma_prev.zero_()

        bq = self._settled_body_q
        self._target_seg_indices_r, self._target_seg_indices_l = self._compute_target_seg_indices(bq)
        # Cache settled EE poses from FK (used by _reset_worlds)
        wp.synchronize()
        fk_bq = self._fk_state.body_q.numpy()
        self._settled_ee_r_pos = fk_bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3].copy()
        self._settled_ee_r_quat = fk_bq[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][3:7].copy()
        self._settled_ee_l_pos = fk_bq[EE_BODY_OFFSET][:3].copy()
        self._settled_ee_l_quat = fk_bq[EE_BODY_OFFSET][3:7].copy()

        # Init per-world EE targets from settled poses
        for w in range(self._world_count):
            self._ee_target_right[w] = self._settled_ee_r_pos.copy()
            self._ee_target_left[w] = self._settled_ee_l_pos.copy()
            self._ee_quat_right[w] = self._settled_ee_r_quat.copy()
            self._ee_quat_left[w] = self._settled_ee_l_quat.copy()

        print(
            f"[ApproachCableEnv] Restored from cache: "
            f"L_EE={self._left_ee_hold}, R_EE={self._right_ee_start}, "
            f"target_seg_r={self._target_seg_indices_r[0]}, "
            f"target_seg_l={self._target_seg_indices_l[0]}"
        )

    def set_cable_xy_randomize(self, enabled: bool) -> None:
        """Enable/disable cable XY ±CABLE_XY_DR_AMPLITUDE randomize at next reset.

        Takes effect at the next `_reset_worlds` call (no effect on the currently
        in-flight episode). Intended to be called once at training/generation
        startup before the first reset. Default is False (fixed cable).

        Args:
            enabled: if True, cable bodies receive uniform XY noise per world
                per reset. Noise range is defined by
                task_config.CABLE_XY_DR_AMPLITUDE.
        """
        self._randomize_cable_xy = bool(enabled)

    def _reset_worlds(self, env_ids):
        """Reset specific worlds to precondition state (per-world slice reset)."""
        if len(env_ids) == 0:
            return

        bq = self._state_0.body_q.numpy()
        bqd = self._state_0.body_qd.numpy()
        # S4b: SolverMuJoCo has no body_q_prev (VBD-only prev-position buffer); on that path the
        # reset is carried by joint_q seeding, so the prev maintenance is skipped (None-tolerant).
        prev = self._solver.body_q_prev.numpy() if hasattr(self._solver, "body_q_prev") else None

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

            # Reset FK state for this world
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()

            self._step_completed_right[w] = False
            self._success_sustain_count[w] = 0

            # Reset EE targets from settled poses (NOT shared _fk_state which
            # holds the last IK-solved world's state — see bug fix 2026-03-30)
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
            self._prev_seg_r_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_seg_l_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)

            # Initial state randomization: perturb both arm EE XY positions
            # Applied AFTER target reset so body_q and tracked target stay consistent
            # (C1 fix 2026-04-11: L arm was deterministic → DAPG R arm obs distribution
            #  poisoning via fixed L arm coupling. Symmetric noise restores exploration.)
            if self.INIT_XY_NOISE > 0:
                ee_body_idx_r = start + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
                noise_xy_r = np.random.uniform(-self.INIT_XY_NOISE, self.INIT_XY_NOISE, size=2)
                bq[ee_body_idx_r, 0] += noise_xy_r[0]
                bq[ee_body_idx_r, 1] += noise_xy_r[1]
                prev[ee_body_idx_r, 0] += noise_xy_r[0]
                prev[ee_body_idx_r, 1] += noise_xy_r[1]
                self._ee_target_right[w][0] += noise_xy_r[0]
                self._ee_target_right[w][1] += noise_xy_r[1]

                ee_body_idx_l = start + EE_BODY_OFFSET
                noise_xy_l = np.random.uniform(-self.INIT_XY_NOISE, self.INIT_XY_NOISE, size=2)
                bq[ee_body_idx_l, 0] += noise_xy_l[0]
                bq[ee_body_idx_l, 1] += noise_xy_l[1]
                prev[ee_body_idx_l, 0] += noise_xy_l[0]
                prev[ee_body_idx_l, 1] += noise_xy_l[1]
                self._ee_target_left[w][0] += noise_xy_l[0]
                self._ee_target_left[w][1] += noise_xy_l[1]

            # Option C' (2026-04-25): cable XY domain randomization per-world.
            # Applied AFTER settled_body_q restore (cable at clean settled state)
            # and AFTER EE noise (independent signal). Inside per-world loop so
            # each world gets an independent noise draw (§運用23 multi-world
            # state separation). self._cable_bodies[w] is world-absolute indices
            # (see L528-531). Velocity zeroed + prev=bq to avoid VBD artifact.
            if self._randomize_cable_xy and CABLE_XY_DR_AMPLITUDE[0] > 0.0:
                amp_x, amp_y = CABLE_XY_DR_AMPLITUDE
                noise_xy_cable = np.random.uniform(
                    low=(-amp_x, -amp_y),
                    high=(amp_x, amp_y),
                    size=2,
                )
                cable_bodies_w = self._cable_bodies[w]
                bq[cable_bodies_w, 0] += noise_xy_cable[0]
                bq[cable_bodies_w, 1] += noise_xy_cable[1]
                # Enforce zero velocity + prev=bq post-noise to prevent
                # VBD solver artifact from stale prev-frame (pre-check Issue #5).
                bqd[cable_bodies_w, :] = 0.0
                prev[cable_bodies_w, :7] = bq[cable_bodies_w, :7]

            # Reset last actions for r_hold penalty (avoid cross-episode leakage)
            if self._last_actions is not None:
                self._last_actions[w] = 0.0

            self.episode_length_buf[w] = 0

        assign_world_states_to_sim(self._state_0, self._solver, bq, bqd, prev)

        # Update target segment indices for reset worlds only (preserve hysteresis
        # state for non-reset worlds)
        new_r, new_l = self._compute_target_seg_indices(bq)
        for w in env_ids:
            w = int(w)
            self._target_seg_indices_r[w] = new_r[w]
            self._target_seg_indices_l[w] = new_l[w]

        # Reset Dahl friction if enabled
        reset_dahl_friction_for_envs(self._solver, self._jws, env_ids)

        self._episode_count += len(env_ids)

    # =========================================================================
    # Observation / Reward / Action
    # =========================================================================

    def _compute_obs_batch(self):
        """Compute observations for all worlds. Returns [N, 42] tensor."""
        wp.synchronize()
        bq = self._state_0.body_q.numpy()

        obs_list = []
        for w in range(self._world_count):
            ws = self._bws[w]

            # Clamp pose (fingertip position + orientation) for both arms via helper
            clamp_r_pos, clamp_r_quat = extract_clamp_pose(
                bq, ws, FRANKA_NUM_JOINTS + EE_BODY_OFFSET, self._prev_clamp_r_quat[w]
            )
            self._prev_clamp_r_quat[w] = clamp_r_quat.copy()
            clamp_l_pos, clamp_l_quat = extract_clamp_pose(bq, ws, EE_BODY_OFFSET, self._prev_clamp_l_quat[w])
            self._prev_clamp_l_quat[w] = clamp_l_quat.copy()

            # Finger openings (raw, no scaling)
            fk_jq = self._per_world_fk_jq[w]
            r_finger_opening = (
                fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]]
                + fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]]
            )
            l_finger_opening = fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] + fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]]

            # Target cable point: interpolated nearest on piecewise-linear cable
            cable_bq = bq[self._cable_bodies[w]]  # [n_cable, 7]
            cable_pos = cable_bq[:, :3]
            seg_pos, seg_tangent, _ = find_nearest_cable_point(cable_pos, clamp_r_pos, self._target_seg_indices_r[w])
            grasp_target_quat_obs = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent))
            grasp_target_quat_obs = temporal_quat_consistency(grasp_target_quat_obs, self._prev_seg_r_quat[w])
            self._prev_seg_r_quat[w] = grasp_target_quat_obs.copy()
            seg_quat = grasp_target_quat_obs

            # Left arm: independent nearest cable point
            seg_pos_l, seg_tangent_l, _ = find_nearest_cable_point(
                cable_pos, clamp_l_pos, self._target_seg_indices_l[w]
            )
            grasp_target_quat_l = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_l))
            grasp_target_quat_l = temporal_quat_consistency(grasp_target_quat_l, self._prev_seg_l_quat[w])
            self._prev_seg_l_quat[w] = grasp_target_quat_l.copy()

            # Clip pose (constant for ApproachCable)
            clip_pos = self.CLIP1_POS
            clip_quat = self.CLIP1_QUAT_XYZW

            # Orientation error: axis-angle from hand to grasp target (world frame)
            ori_error_aa = compute_ori_error_axis_angle(clamp_r_quat, grasp_target_quat_obs)

            # Position error: hand clamp → target point (world frame)
            pos_error = clamp_r_pos - seg_pos  # [3]

            # Left arm error signals (independent nearest cable point)
            ori_error_aa_l = compute_ori_error_axis_angle(clamp_l_quat, grasp_target_quat_l)
            pos_error_l = clamp_l_pos - seg_pos_l  # [3]

            obs_list.append(
                [
                    clamp_r_pos[0],
                    clamp_r_pos[1],
                    clamp_r_pos[2],  # [0:3]
                    clamp_r_quat[0],
                    clamp_r_quat[1],
                    clamp_r_quat[2],
                    clamp_r_quat[3],  # [3:7]
                    r_finger_opening,  # [7]
                    clamp_l_pos[0],
                    clamp_l_pos[1],
                    clamp_l_pos[2],  # [8:11]
                    clamp_l_quat[0],
                    clamp_l_quat[1],
                    clamp_l_quat[2],
                    clamp_l_quat[3],  # [11:15]
                    l_finger_opening,  # [15]
                    seg_pos[0],
                    seg_pos[1],
                    seg_pos[2],  # [16:19]
                    seg_quat[0],
                    seg_quat[1],
                    seg_quat[2],
                    seg_quat[3],  # [19:23]
                    clip_pos[0],
                    clip_pos[1],
                    clip_pos[2],  # [23:26]
                    clip_quat[0],
                    clip_quat[1],
                    clip_quat[2],
                    clip_quat[3],  # [26:30]
                    ori_error_aa[0],
                    ori_error_aa[1],
                    ori_error_aa[2],  # [30:33]
                    pos_error[0],
                    pos_error[1],
                    pos_error[2],  # [33:36]
                    ori_error_aa_l[0],
                    ori_error_aa_l[1],
                    ori_error_aa_l[2],  # [36:39]
                    pos_error_l[0],
                    pos_error_l[1],
                    pos_error_l[2],  # [39:42]
                ]
            )

        obs = torch.tensor(obs_list, dtype=torch.float32, device=self.device)
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)
        # L arm obs masking: reduce R arm policy dependence on L arm state
        # Mask L clamp pos+quat (8:15), L finger opening (15), and L error signals (36:42)
        if self.OBS_L_ARM_MASK_PROB > 0:
            mask = torch.rand(obs.shape[0], device=obs.device) < self.OBS_L_ARM_MASK_PROB
            obs[mask, 8:16] = 0.0  # L clamp pos[8:11] + quat[11:15] + finger[15]
            obs[mask, 36:42] = 0.0  # L ori_error[36:39] + pos_error[39:42]
        # Pad 42D → 45D for unified base model (IC-compatible). Dims [42:45] = zeros.
        pad = torch.zeros(obs.shape[0], 3, dtype=obs.dtype, device=obs.device)
        obs = torch.cat([obs, pad], dim=1)

        # Phase 3: append visual features (frozen encoder) when camera is enabled
        if self._visual_encoder is not None:
            rgb = self._camera.rgb_tensor  # [W, C, 3, H, W_px] float32 in [0, 1]
            W, C = rgb.shape[0], rgb.shape[1]
            rgb_flat = rgb.reshape(W * C, *rgb.shape[2:])  # [W*C, 3, H, W_px]
            feat_flat = self._visual_encoder(rgb_flat)  # [W*C, per_cam_dim]
            visual_feat = feat_flat.reshape(W, C * feat_flat.shape[-1])  # [W, C*per_cam]
            visual_feat = torch.nan_to_num(visual_feat, nan=0.0, posinf=0.0, neginf=0.0)
            obs = torch.cat([obs, visual_feat], dim=1)
        return obs

    def visual_encoder_params(self):
        """Return trainable parameters of the visual encoder (projection layer only)."""
        if self._visual_encoder is None:
            return []
        return list(self._visual_encoder.trainable_parameters())

    def _compute_rewards_dones_batch(self):
        """Compute rewards and dones for all worlds (v5 pose_match).

        Reward: R_pos + R_ori + R_step + R_task + R_penalty
        Target: cable segment (both arms averaged for dual-arm coordination).
        """
        wp.synchronize()
        bq = self._state_0.body_q.numpy()

        rewards = np.zeros(self._world_count, dtype=np.float32)
        dones = np.zeros(self._world_count, dtype=np.int64)
        timeouts = np.zeros(self._world_count, dtype=np.int64)
        successes = np.zeros(self._world_count, dtype=np.float32)

        rc_r_pos = np.zeros(self._world_count, dtype=np.float32)
        rc_r_ori = np.zeros(self._world_count, dtype=np.float32)
        rc_r_step = np.zeros(self._world_count, dtype=np.float32)
        rc_dist = np.zeros(self._world_count, dtype=np.float32)
        rc_ori_dist = np.zeros(self._world_count, dtype=np.float32)
        rc_dist_l = np.zeros(self._world_count, dtype=np.float32)
        rc_ori_dist_l = np.zeros(self._world_count, dtype=np.float32)
        rc_finger = np.zeros(self._world_count, dtype=np.float32)
        rc_finger_l = np.zeros(self._world_count, dtype=np.float32)
        rc_explosion = np.zeros(self._world_count, dtype=np.bool_)
        rc_r_hold = np.zeros(self._world_count, dtype=np.float32)
        rc_r_pos_r = np.zeros(self._world_count, dtype=np.float32)
        rc_r_pos_l = np.zeros(self._world_count, dtype=np.float32)
        rc_r_ori_r = np.zeros(self._world_count, dtype=np.float32)
        rc_r_ori_l = np.zeros(self._world_count, dtype=np.float32)

        for w in range(self._world_count):
            ws = self._bws[w]

            # Right EE body pose
            ee_r_idx = ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
            ee_r_pos = bq[ee_r_idx][:3]
            ee_r_quat = bq[ee_r_idx][3:7]

            # Clamp position (fingertip)
            clamp_r_pos = compute_clamp_pos(ee_r_pos, ee_r_quat)
            clamp_r_quat = normalize_quat_w_positive(ee_r_quat)

            # Left EE body pose
            ee_l_idx = ws + EE_BODY_OFFSET
            ee_l_pos = bq[ee_l_idx][:3]
            ee_l_quat = bq[ee_l_idx][3:7]
            clamp_l_pos = compute_clamp_pos(ee_l_pos, ee_l_quat)
            clamp_l_quat = normalize_quat_w_positive(ee_l_quat)

            # Target cable point (interpolated nearest on piecewise-linear cable)
            cable_bq = bq[self._cable_bodies[w]]  # [n_cable, 7]
            cable_pos = cable_bq[:, :3]
            seg_pos, seg_tangent, dist_pos = find_nearest_cable_point(
                cable_pos, clamp_r_pos, self._target_seg_indices_r[w]
            )
            grasp_target_quat = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent))
            dist_ori = quat_distance(clamp_r_quat, grasp_target_quat)

            # Left arm errors (independent nearest cable point)
            _, seg_tangent_l, dist_pos_l = find_nearest_cable_point(
                cable_pos, clamp_l_pos, self._target_seg_indices_l[w]
            )
            grasp_target_quat_l = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_l))
            dist_ori_l = quat_distance(clamp_l_quat, grasp_target_quat_l)

            # Finger opening
            fk_jq = self._per_world_fk_jq[w]
            finger_opening = (
                fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]]
                + fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]]
            )
            l_finger_opening = fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] + fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]]

            # ---- Reward: pose_match (v37) — non-negative shift, 3-scale hybrid ----
            if self.REWARD_MODE == "multiplicative":
                # Right arm score
                score_pos_r = math.exp(-dist_pos / self.RANGE_POS)
                score_ori_r = math.exp(-dist_ori / self.RANGE_ORI)
                progress_r = (
                    self.PROGRESS_W_POS * score_pos_r
                    + self.PROGRESS_W_ORI * score_ori_r
                    + self.PROGRESS_W_COUPLED * score_pos_r * score_ori_r
                )
                # Left arm score
                score_pos_l = math.exp(-dist_pos_l / self.RANGE_POS)
                score_ori_l = math.exp(-dist_ori_l / self.RANGE_ORI)
                progress_l = (
                    self.PROGRESS_W_POS * score_pos_l
                    + self.PROGRESS_W_ORI * score_ori_l
                    + self.PROGRESS_W_COUPLED * score_pos_l * score_ori_l
                )
                # v37: non-negative shift (remove -2.0 offset). R_PENALTY handles baseline.
                progress = progress_r + progress_l
                r_pos = self.PROGRESS_SCALE * progress
                r_ori = 0.0  # included in r_pos via multiplicative coupling
            elif self.REWARD_MODE == "hybrid":
                # v37: non-negative shift (remove -1.0) + 3-scale (add EPS_POS_MED).
                # R_PENALTY calibrated to zero-out at P0. Approach → positive reward.
                # Right arm
                r_fine_r = math.exp(-dist_pos / self.EPS_POS)
                r_med_r = math.exp(-dist_pos / self.EPS_POS_MED)
                r_coarse_r = math.exp(-dist_pos / self.EPS_POS_COARSE)
                r_ori_fine_r = math.exp(-dist_ori / self.EPS_ORI)
                r_ori_coarse_r = math.exp(-dist_ori / self.EPS_ORI_COARSE)
                r_ori_r = (r_ori_fine_r + r_ori_coarse_r) / 2
                # Left arm
                r_fine_l = math.exp(-dist_pos_l / self.EPS_POS)
                r_med_l = math.exp(-dist_pos_l / self.EPS_POS_MED)
                r_coarse_l = math.exp(-dist_pos_l / self.EPS_POS_COARSE)
                r_ori_fine_l = math.exp(-dist_ori_l / self.EPS_ORI)
                r_ori_coarse_l = math.exp(-dist_ori_l / self.EPS_ORI_COARSE)
                r_ori_l = (r_ori_fine_l + r_ori_coarse_l) / 2
                # v37: average 3 pos scales per arm, average 2 ori scales per arm, sum both arms
                r_pos = self.W_POS * ((r_fine_r + r_med_r + r_coarse_r) / 3 + (r_fine_l + r_med_l + r_coarse_l) / 3)
                r_ori = self.W_ORI * (r_ori_r + r_ori_l)
            else:
                # v37: non-negative shift for exp mode too
                r_pos_r = self.W_POS * math.exp(-dist_pos / self.EPS_POS)
                r_ori_r = (
                    self.W_ORI * (math.exp(-dist_ori / self.EPS_ORI) + math.exp(-dist_ori / self.EPS_ORI_COARSE)) / 2
                )
                r_pos_l = self.W_POS * math.exp(-dist_pos_l / self.EPS_POS)
                r_ori_l = (
                    self.W_ORI
                    * (math.exp(-dist_ori_l / self.EPS_ORI) + math.exp(-dist_ori_l / self.EPS_ORI_COARSE))
                    / 2
                )
                r_pos = r_pos_r + r_pos_l
                r_ori = r_ori_r + r_ori_l

            # R_step: one-time bonus when both arms reach approach zone
            # Uses CLAMP_DIST_THRESH (12mm) — fires on first entry, before sustained success
            r_step_val = 0.0
            precision_ok = (
                dist_pos < self.CLAMP_DIST_THRESH
                and dist_pos_l < self.CLAMP_DIST_THRESH
                and dist_ori < self.CLAMP_ORI_THRESH
                and dist_ori_l < self.CLAMP_ORI_THRESH
            )
            if precision_ok and not self._step_completed_right[w]:
                r_step_val = self.R_STEP_BONUS
                self._step_completed_right[w] = True

            # SUCCESS: both arms pos ∧ ori ∧ sustained(K)
            # finger close is NOT part of this skill — handled by next step
            clamp_pos_ok = dist_pos < self.CLAMP_DIST_THRESH and dist_pos_l < self.CLAMP_DIST_THRESH
            clamp_ori_ok = dist_ori < self.CLAMP_ORI_THRESH and dist_ori_l < self.CLAMP_ORI_THRESH
            if clamp_pos_ok and clamp_ori_ok:
                self._success_sustain_count[w] += 1
            else:
                self._success_sustain_count[w] = 0
            success = self._success_sustain_count[w] >= self.C5_SUSTAIN_STEPS

            r_task_val = self.R_TASK_BONUS if success else 0.0
            r_penalty = self.R_PENALTY

            # r_hold: penalize L arm action magnitude only (R arm free to approach)
            # BUG-3 fix: use damped action (physical effect) not raw action.
            # Raw action is 3.3x larger due to CLOSE_ACTION_DAMPING=0.3, causing
            # 11x over-penalization (squared) that suppresses L arm learning.
            r_hold_val = 0.0
            if self._last_actions is not None and self.W_HOLD > 0:
                a_l = self._last_actions[w, 6:12] * self.CLOSE_ACTION_DAMPING
                r_hold_val = -self.W_HOLD * float(torch.sum(a_l**2))
            rc_r_hold[w] = r_hold_val

            # Per-arm reward components for diagnostics (v37: non-negative)
            if self.REWARD_MODE == "hybrid":
                rc_r_pos_r[w] = self.W_POS * (r_fine_r + r_med_r + r_coarse_r) / 3
                rc_r_pos_l[w] = self.W_POS * (r_fine_l + r_med_l + r_coarse_l) / 3
                rc_r_ori_r[w] = self.W_ORI * r_ori_r
                rc_r_ori_l[w] = self.W_ORI * r_ori_l
            elif self.REWARD_MODE == "multiplicative":
                # v37: non-negative shift
                rc_r_pos_r[w] = self.PROGRESS_SCALE * progress_r
                rc_r_pos_l[w] = self.PROGRESS_SCALE * progress_l
                rc_r_ori_r[w] = 0.0
                rc_r_ori_l[w] = 0.0
            elif self.REWARD_MODE == "exp":
                rc_r_pos_r[w] = self.W_POS * math.exp(-dist_pos / self.EPS_POS)
                rc_r_pos_l[w] = self.W_POS * math.exp(-dist_pos_l / self.EPS_POS)
                rc_r_ori_r[w] = (
                    self.W_ORI * (math.exp(-dist_ori / self.EPS_ORI) + math.exp(-dist_ori / self.EPS_ORI_COARSE)) / 2
                )
                rc_r_ori_l[w] = (
                    self.W_ORI
                    * (math.exp(-dist_ori_l / self.EPS_ORI) + math.exp(-dist_ori_l / self.EPS_ORI_COARSE))
                    / 2
                )

            # VBD explosion guard (NaN also triggers — IEEE 754 NaN > x is False)
            explosion = (
                dist_pos > self.EXPLOSION_DIST_THRESH
                or dist_pos_l > self.EXPLOSION_DIST_THRESH
                or math.isnan(dist_pos)
                or math.isnan(dist_pos_l)
            )

            if explosion:
                r = -10.0  # Fixed penalty: clear signal without inf gradient contamination
            else:
                r = r_pos + r_ori + r_step_val + r_task_val + r_penalty + r_hold_val
                if math.isnan(r):
                    r = self.R_PENALTY

            timeout = self.episode_length_buf[w].item() >= self.max_episode_length
            done = success or timeout or explosion

            rewards[w] = r
            rc_r_pos[w] = r_pos
            rc_r_ori[w] = r_ori
            rc_r_step[w] = r_step_val
            # Clamp dist to EXPLOSION_DIST_THRESH to prevent inf in mean computation
            rc_dist[w] = (
                min(dist_pos, self.EXPLOSION_DIST_THRESH) if not math.isnan(dist_pos) else self.EXPLOSION_DIST_THRESH
            )
            rc_ori_dist[w] = dist_ori if not math.isnan(dist_ori) else 0.0
            rc_dist_l[w] = (
                min(dist_pos_l, self.EXPLOSION_DIST_THRESH)
                if not math.isnan(dist_pos_l)
                else self.EXPLOSION_DIST_THRESH
            )
            rc_ori_dist_l[w] = dist_ori_l if not math.isnan(dist_ori_l) else 0.0
            rc_finger[w] = finger_opening
            rc_finger_l[w] = l_finger_opening
            rc_explosion[w] = explosion
            dones[w] = int(done)
            # P3 fix (2026-04-11): timeouts must exclude success and explosion.
            # RSL-RL PPO bootstraps V(s_{T+1}) when timeouts[w]=1, so any terminal
            # state (success/explosion) leaking into timeouts pollutes value targets
            # (see CLAUDE.md "timeouts汚染禁止"; value_loss 105x blowup 2026-04-08).
            timeouts[w] = int(timeout and not success and not explosion)
            successes[w] = float(success)
            if done:
                self._episode_success_buf.append(float(success))

        if len(self._episode_success_buf) > 0:
            self._last_success_rate = float(np.mean(self._episode_success_buf))

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
                    "/reward/r_penalty": float(self.R_PENALTY),
                    "/metrics/dist_pos_mean": float(np.nanmean(rc_dist)),
                    "/metrics/dist_pos_median": float(np.nanmedian(rc_dist)),
                    "/metrics/dist_pos_bottleneck_median": float(np.nanmedian(np.maximum(rc_dist, rc_dist_l))),
                    "/metrics/dist_pos_p95": float(np.nanmean(rc_dist[rc_dist <= np.nanpercentile(rc_dist, 95)]))
                    if len(rc_dist) > 0
                    else 0.0,
                    "/metrics/dist_ori_mean": float(np.nanmean(rc_ori_dist)),
                    "/metrics/dist_ori_median": float(np.nanmedian(rc_ori_dist)),
                    "/metrics/dist_pos_l_median": float(np.nanmedian(rc_dist_l)),
                    "/metrics/dist_ori_l_median": float(np.nanmedian(rc_ori_dist_l)),
                    "/metrics/finger_opening_mean": float(np.mean(rc_finger)),
                    "/metrics/finger_opening_l_mean": float(np.mean(rc_finger_l)),
                    "/metrics/explosion_count": int(np.sum(rc_explosion)),
                    "/reward/r_hold": float(np.mean(rc_r_hold)),
                    "/reward/r_pos_r": float(np.mean(rc_r_pos_r)),
                    "/reward/r_pos_l": float(np.mean(rc_r_pos_l)),
                    "/reward/r_ori_r": float(np.mean(rc_r_ori_r)),
                    "/reward/r_ori_l": float(np.mean(rc_r_ori_l)),
                },
                "log_per_world": {
                    "dist_pos": rc_dist.copy(),
                    "dist_ori": rc_ori_dist.copy(),
                    "finger_opening": rc_finger.copy(),
                    "reward": rewards.copy(),
                    "success": successes.copy(),
                    "explosion": rc_explosion.copy(),
                },
            },
        )

    def _apply_actions_batch(self, actions):
        """Apply per-world 12D actions (pos + rot deltas) via batched IK + physics.

        Args:
            actions: [N, 12] tensor -- per world:
                [0:3]  right EE delta XYZ
                [3:6]  right EE delta axis-angle
                [6:9]  left EE delta XYZ
                [9:12] left EE delta axis-angle
        """
        N = self._world_count
        actions_np = actions.cpu().numpy()

        wp.synchronize()
        bq = self._state_0.body_q.numpy()

        # Compute per-world adaptive pos scale if enabled (independent per arm)
        if self.ADAPTIVE_POS_SCALE:
            r_pos_scales = np.full(N, self.POS_ACTION_SCALE, dtype=np.float32)
            l_pos_scales = np.full(N, self.POS_ACTION_SCALE, dtype=np.float32)
            for w in range(N):
                ws = self._bws[w]
                cable_bq = bq[self._cable_bodies[w]]
                cable_pos = cable_bq[:, :3]

                # Right arm scale (interpolated nearest)
                ee_r_idx = ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
                clamp_r = compute_clamp_pos(bq[ee_r_idx][:3], bq[ee_r_idx][3:7])
                _, _, dist_r = find_nearest_cable_point(cable_pos, clamp_r, self._target_seg_indices_r[w])
                r_pos_scales[w] = max(
                    self.MIN_POS_SCALE, self.POS_ACTION_SCALE * min(1.0, dist_r / self.FINE_THRESHOLD)
                )

                # Left arm scale (independent nearest)
                ee_l_idx = ws + EE_BODY_OFFSET
                clamp_l = compute_clamp_pos(bq[ee_l_idx][:3], bq[ee_l_idx][3:7])
                _, _, dist_l = find_nearest_cable_point(cable_pos, clamp_l, self._target_seg_indices_l[w])
                l_pos_scales[w] = max(
                    self.MIN_POS_SCALE, self.POS_ACTION_SCALE * min(1.0, dist_l / self.FINE_THRESHOLD)
                )
            r_pos_delta = actions_np[:, 0:3] * r_pos_scales[:, None]  # [N, 3]
            l_pos_delta = actions_np[:, 6:9] * l_pos_scales[:, None]  # [N, 3]
        else:
            r_pos_delta = actions_np[:, 0:3] * self.POS_ACTION_SCALE  # [N, 3]
            l_pos_delta = actions_np[:, 6:9] * self.POS_ACTION_SCALE  # [N, 3]

        r_rot_delta = actions_np[:, 3:6] * self.ROT_ACTION_SCALE  # [N, 3] axis-angle
        l_rot_delta = actions_np[:, 9:12] * self.ROT_ACTION_SCALE  # [N, 3] axis-angle

        fk_coord_count = self._fk_model.joint_coord_count
        finger_mask = np.ones(fk_coord_count, dtype=bool)
        for fc in (*GRIPPER_JOINT_RANGE, *(JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE)):
            finger_mask[fc] = False

        # --- Compute per-world EE position + rotation targets ---
        targets_left = np.zeros((N, 3))
        targets_right = np.zeros((N, 3))
        rot_targets_left = []  # list of wp.vec4
        rot_targets_right = []  # list of wp.vec4
        jq_starts = np.array(self._per_world_fk_jq[:N])

        # --- Finger auto-control (STEP table, v5) ---
        per_w_dist_pos = np.zeros(N, dtype=np.float32)
        per_w_dist_ori = np.zeros(N, dtype=np.float32)
        per_w_dist_pos_l = np.zeros(N, dtype=np.float32)
        per_w_dist_ori_l = np.zeros(N, dtype=np.float32)
        for w in range(N):
            ws = self._bws[w]
            ee_r_idx = ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
            ee_r_pos = bq[ee_r_idx][:3]
            ee_r_quat = bq[ee_r_idx][3:7]

            # Check pose_match for both hands (AND condition: both must be ready)
            cable_bq = bq[self._cable_bodies[w]]
            cable_pos = cable_bq[:, :3]

            # Compute R arm dist for ori-gate (fingers never close in AC)
            clamp_r_pos = compute_clamp_pos(ee_r_pos, ee_r_quat)
            _, seg_tangent_r, dist_pos = find_nearest_cable_point(cable_pos, clamp_r_pos, self._target_seg_indices_r[w])
            clamp_r_quat_norm = normalize_quat_w_positive(ee_r_quat)
            grasp_target_quat = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_r))
            dist_ori = quat_distance(clamp_r_quat_norm, grasp_target_quat)
            per_w_dist_pos[w] = dist_pos
            per_w_dist_ori[w] = dist_ori

            # Left hand dist (for metrics)
            ee_l_idx = ws + EE_BODY_OFFSET
            ee_l_pos = bq[ee_l_idx][:3]
            ee_l_quat = bq[ee_l_idx][3:7]
            clamp_l_pos = compute_clamp_pos(ee_l_pos, ee_l_quat)
            _, seg_tangent_l, dist_pos_l = find_nearest_cable_point(
                cable_pos, clamp_l_pos, self._target_seg_indices_l[w]
            )
            clamp_l_quat_norm = normalize_quat_w_positive(ee_l_quat)
            grasp_target_quat_l = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_l))
            dist_ori_l = quat_distance(clamp_l_quat_norm, grasp_target_quat_l)
            per_w_dist_pos_l[w] = dist_pos_l
            per_w_dist_ori_l[w] = dist_ori_l

            # Finger targets: both arms always OPEN
            jq_starts[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
            jq_starts[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS
            jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
            jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS

        # Ori-gated approach: suppress pos delta when near cable but ori not ready.
        # C2 narrowing (2026-04-11): removed L arm unconditional 0.3x damping.
        # Prior rationale claimed "150mm init dist" — actually ~15.59mm at P0, so the
        # full 200-step budget × 4.5mm/step was unnecessary and caused L arm to lag
        # into the R arm's ori-ready window. Keeping symmetric ori-gates only.
        for w in range(N):
            # R arm ori-gate
            if per_w_dist_pos[w] < self.ORI_GATE_POS_THRESH and per_w_dist_ori[w] > self.ORI_GATE_ORI_THRESH:
                r_pos_delta[w] *= self.CLOSE_ACTION_DAMPING
            # L arm ori-gate (symmetric with R arm)
            if per_w_dist_pos_l[w] < self.ORI_GATE_POS_THRESH and per_w_dist_ori_l[w] > self.ORI_GATE_ORI_THRESH:
                l_pos_delta[w] *= self.CLOSE_ACTION_DAMPING

        for w in range(N):
            # Right EE: tracked target + delta (avoids FK/body_q drift)
            target_r = self._ee_target_right[w].copy() + r_pos_delta[w]
            target_r[2] = np.clip(target_r[2], GRASP_Z, LIFT_Z + 0.05)
            targets_right[w] = target_r
            self._ee_target_right[w] = target_r.copy()

            # Right EE: tracked rot + axis-angle delta (world frame)
            delta_r_quat = axis_angle_to_quat_xyzw(r_rot_delta[w])
            new_r_quat = quat_multiply_xyzw(delta_r_quat, self._ee_quat_right[w])
            new_r_quat = new_r_quat / np.linalg.norm(new_r_quat)
            self._ee_quat_right[w] = new_r_quat.copy()
            # xyzw → IK expects xyzw (same as wp.quat)
            rot_targets_right.append(
                wp.vec4(float(new_r_quat[0]), float(new_r_quat[1]), float(new_r_quat[2]), float(new_r_quat[3]))
            )

            # Left EE: tracked target + delta
            target_l = self._ee_target_left[w].copy() + l_pos_delta[w]
            target_l[2] = np.clip(target_l[2], GRASP_Z, LIFT_Z + 0.05)
            targets_left[w] = target_l
            self._ee_target_left[w] = target_l.copy()

            # Left EE: tracked rot + axis-angle delta
            delta_l_quat = axis_angle_to_quat_xyzw(l_rot_delta[w])
            new_l_quat = quat_multiply_xyzw(delta_l_quat, self._ee_quat_left[w])
            new_l_quat = new_l_quat / np.linalg.norm(new_l_quat)
            self._ee_quat_left[w] = new_l_quat.copy()
            # xyzw → IK expects xyzw (same as wp.quat)
            rot_targets_left.append(
                wp.vec4(float(new_l_quat[0]), float(new_l_quat[1]), float(new_l_quat[2]), float(new_l_quat[3]))
            )

        # Set IK rotation targets (policy-controlled, not cable-tracking)
        self._ik_obj_rot_left.set_target_rotations(wp.array(rot_targets_left, dtype=wp.vec4, device=self.device))
        self._ik_obj_rot_right.set_target_rotations(wp.array(rot_targets_right, dtype=wp.vec4, device=self.device))

        # Batched IK solve
        jq_targets = self._solve_ik_batch(targets_left, targets_right, jq_starts)

        # Handle NaN
        nan_mask = np.any(np.isnan(jq_targets), axis=1)
        if np.any(nan_mask):
            jq_targets[nan_mask] = jq_starts[nan_mask]

        # Preserve finger positions in jq_targets
        for w in range(N):
            jq_targets[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = jq_starts[
                w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]
            ]
            jq_targets[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = jq_starts[
                w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]
            ]
            jq_targets[w, GRIPPER_DRIVER_JOINT_IDX[0]] = jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[0]]
            jq_targets[w, GRIPPER_DRIVER_JOINT_IDX[1]] = jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[1]]

        # Interpolate FK + physics stepping
        for step in range(self.PHYSICS_STEPS_PER_RL):
            t = min((step + 1) / self.PHYSICS_STEPS_PER_RL, 1.0)

            jq_interp_all = jq_starts.copy()
            jq_interp_all[:, finger_mask] = (
                jq_starts[:, finger_mask] + (jq_targets[:, finger_mask] - jq_starts[:, finger_mask]) * t
            )

            # Finger interpolation from old to new
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

            # Broadcast FK to physics (skip dynamic finger bodies — spring-driven)
            phys_bq = self._state_0.body_q.numpy()
            for w in range(N):
                ws = self._bws[w]
                for bi in range(ROBOT_BODY_COUNT):
                    if (ws + bi) not in self._finger_set:
                        phys_bq[ws + bi] = batch_bq[w, bi]
            self._state_0.body_q.assign(phys_bq)

            # Physics step (with finger spring forces)
            self._physics_step_all(substeps=RL_SIM_SUBSTEPS, sim_dt=RL_SIM_DT, fk_batch_bq=batch_bq, n_worlds=N)

        # Save final FK state per world
        for w in range(N):
            self._per_world_fk_jq[w] = jq_targets[w].copy()

    # =========================================================================
    # RSL-RL VecEnv Interface
    # =========================================================================

    @property
    def num_obs(self):
        return 45 + self._visual_feature_dim

    def get_observations(self) -> tuple[torch.Tensor, dict]:
        obs = self._compute_obs_batch()
        extras = {"observations": {}}
        if self._camera is not None:
            extras["visual_obs"] = {"depth": self._camera.depth_tensor}
            if self._camera.color_tensor is not None:
                extras["visual_obs"]["color"] = self._camera.color_tensor
        return obs, extras

    def reset(self) -> tuple[torch.Tensor, dict]:
        self._reset_worlds(list(range(self._world_count)))
        if self._camera is not None:
            self._camera.update(self._state_0)
        return self.get_observations()

    def export_chain_state(self, *, world_idx=0, step_id=0):
        """Export shared Newton state for an opt-in no-reset chain handoff."""

        return export_chain_state_from_env(
            self,
            source_skill="AC",
            world_idx=world_idx,
            step_id=step_id,
            validation_metadata={"stage": "stage0_tracked_api"},
        )

    def import_chain_state(self, state, *, world_idx=0, validate=True):
        """Import shared Newton state for an opt-in no-reset chain handoff."""

        return import_chain_state_into_env(self, state, target_skill="AC", validate=validate)

    def validate_chain_state(self, state, *, world_idx=0):
        """Validate a chain state against this environment without reset."""

        return validate_chain_state_for_env(self, state, target_skill="AC")

    def step_chain(self, actions: torch.Tensor, *, auto_reset: bool = False):
        """Run an opt-in chain step while preserving default :meth:`step` behavior."""

        if auto_reset:
            return self.step(actions)
        actions = torch.nan_to_num(actions, nan=0.0, posinf=0.0, neginf=0.0).clamp(-1.0, 1.0)

        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        self._update_target_seg_hysteresis(bq)

        self._last_actions = actions
        self._apply_actions_batch(actions)
        self.episode_length_buf += 1
        self._total_env_steps += self._world_count

        rewards, dones, extras = self._compute_rewards_dones_batch()
        rewards = torch.nan_to_num(rewards, nan=-10.0, posinf=0.0, neginf=-10.0)

        if self._camera is not None:
            self._camera.update(self._state_0)

        obs = self._compute_obs_batch()
        return obs, rewards, dones, extras

    def step(self, actions: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]:
        actions = torch.nan_to_num(actions, nan=0.0, posinf=0.0, neginf=0.0).clamp(-1.0, 1.0)

        # Dynamic target segment update with ±1 hysteresis: only shifts window
        # when the nearest cable segment moves by more than 1 from the current
        # center.  Prevents gradient oscillation from cable-sway-induced target
        # jumps while still tracking genuine arm drift (window escape fix).
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        self._update_target_seg_hysteresis(bq)

        self._last_actions = actions
        self._apply_actions_batch(actions)
        self.episode_length_buf += 1
        self._total_env_steps += self._world_count

        rewards, dones, extras = self._compute_rewards_dones_batch()
        rewards = torch.nan_to_num(rewards, nan=-10.0, posinf=0.0, neginf=-10.0)

        # Auto-reset done worlds
        done_ids = dones.nonzero(as_tuple=False).squeeze(-1)
        if len(done_ids) > 0:
            self._reset_worlds(done_ids.cpu().tolist())

        # Phase 2: camera rendering (after reset so fresh worlds get correct images)
        if self._camera is not None:
            self._camera.update(self._state_0)
            extras["visual_obs"] = {"depth": self._camera.depth_tensor}
            if self._camera.color_tensor is not None:
                extras["visual_obs"]["color"] = self._camera.color_tensor

        obs = self._compute_obs_batch()
        return obs, rewards, dones, extras
