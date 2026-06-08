# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Newton VBD AerialRegrasp RL environment -- Multi-world RSL-RL VecEnv.

Independent AerialRegrasp skill (DAPG Approach A, Phase 3).
Task: Right arm approaches and grasps cable held by left arm at LIFT_Z.
Initial state: Left arm holds cable at LIFT_Z (fingers CLOSED), right arm OPEN at LIFT_Z.

Obs (42D): 30D base (v5) + 12D error signals.
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
  [30:33] Right orientation error axis-angle [rad] (hand -> grasp target)
  [33:36] Right position error XYZ [m] (hand clamp -> target segment)
  [36:39] Left orientation error axis-angle [rad] (hand -> grasp target)
  [39:42] Left position error XYZ [m] (hand clamp -> target segment)

Action (12D): Dual-arm EE delta (v18 cooperative).
  [0:3]   Right EE delta XYZ * POS_ACTION_SCALE [m]
  [3:6]   Right EE delta axis-angle * ROT_ACTION_SCALE [rad]
  [6:9]   Left EE delta XYZ * POS_ACTION_SCALE [m]
  [9:12]  Left EE delta axis-angle * ROT_ACTION_SCALE [rad]

Finger control: auto (STEP table), not in action space.
  Left: always CLOSED (from precondition).
  Right: auto-close when within pose_match threshold of cable.

Single-agent reward: both arms optimise one unified objective.
  r_pos/r_ori: right arm approach. r_ease/r_height/r_stable: cable state.

Success: clamp(R) ^ cable_not_dropped ^ sustained(K=5).
  Left arm dist is a geometric constant (~25mm) — excluded from success (Session 84).
Done: success | timeout | explosion | cable_terminated (grace period K=5).

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/train_aerial_regrasp.py --world-count 4
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

# Import shared utilities from base module
_env_dir = os.path.dirname(os.path.abspath(__file__))
if _env_dir not in sys.path:
    sys.path.insert(0, _env_dir)

from cable_orientation_utils import BASE_HAND_DOWN_QUAT, compute_hand_quat_for_cable
from chain_runtime_state import (
    export_chain_state_from_env,
    import_chain_state_into_env,
    validate_chain_state_for_env,
)
from newton_skill_env_base import (
    EE_BODY_OFFSET,
    FINGER_JOINT_INDICES,
    FRANKA_NUM_JOINTS,
    IK_ITERATIONS_RL,
    IK_STEP_SIZE,
    RL_SIM_DT,
    RL_SIM_SUBSTEPS,
    ROBOT_BODY_COUNT,
    # Constants
    SIM_DT,
    assign_world_states_to_sim,
    axis_angle_to_quat_xyzw,
    # Scene building
    build_fk_and_init,
    build_multiworld_scene,
    compute_clamp_pos,
    compute_ori_error_axis_angle,
    extract_clamp_pose,
    # Cable / clamp utilities
    find_nearest_cable_point,
    # Quaternion utilities
    normalize_quat_w_positive,
    quat_distance,
    quat_multiply_xyzw,
    reset_dahl_friction_for_envs,
    restore_ee_targets_per_world,
    restore_world_body_state,
    temporal_quat_consistency,
)

# Finger pad-follower body indices (local within one arm); FINGER_LOCAL = [9, 13] imported from task_config SSOT
# Dynamic finger spring parameters (Mode 2 from test_grip_modes.py)
FINGER_SPRING_KE = 10000.0  # Position spring stiffness [N/m]
FINGER_SPRING_KD = 500.0  # Velocity damping [N·s/m]
FINGER_DYNAMIC_INV_MASS = 20.0  # 1/0.05kg
FINGER_DYNAMIC_INV_INERTIA = 100.0  # Approximate
KINEMATIC_HOLD_STEPS = 30
KINEMATIC_INV_MASS = 0.0
KINEMATIC_INV_INERTIA = 0.0
KINEMATIC_GATE_STEP_COUNT = "step_count"
KINEMATIC_GATE_RELEASE_AFTER_SUCCESS_HOLD_K = "release_after_success_hold_k"
KINEMATIC_GATE_HOLD_TO_COMPLETION = "hold_to_completion"
KINEMATIC_GATE_TYPE = KINEMATIC_GATE_STEP_COUNT
KINEMATIC_GATE_TYPES = {
    KINEMATIC_GATE_STEP_COUNT,
    KINEMATIC_GATE_RELEASE_AFTER_SUCCESS_HOLD_K,
    KINEMATIC_GATE_HOLD_TO_COMPLETION,
}
KINEMATIC_RELEASE_SUCCESS_HOLD_STEPS = 5
KINEMATIC_RELEASE_STABILITY_STEPS = 5
KINEMATIC_MAX_HOLD_STEPS = 200
D0_CONTACT_TELEMETRY_ENABLED_KEY = "d0_contact_telemetry_enabled"
D0_CONTACT_SENSOR_PRIM_PATH_KEY = "d0_contact_sensor_prim_path"
D0_CONTACT_SENSOR_SHAPE_EXPR_KEY = "d0_contact_sensor_shape_expr"
D0_CONTACT_FILTER_PRIM_PATHS_EXPR_KEY = "d0_contact_filter_prim_paths_expr"
D0_CONTACT_FILTER_SHAPE_EXPR_KEY = "d0_contact_filter_shape_prim_expr"
D0_CONTACT_FORCE_LIMIT_KEY = "d0_contact_force_limit"
D0_CONTROL_ARM_KEY = "d0_control_arm"
D0_CONTROL_ARM_NONE = ""
D0_CONTROL_ARM_ORACLE_POSE_OR_FORCE_HOLD = "oracle_pose_or_force_hold"
D0_CONTROL_ARM_RELEASE_RAMP_5 = "release_ramp_5"
D0_CONTROL_ARM_RELEASE_RAMP_10 = "release_ramp_10"
D0_CONTROL_ARM_IMPEDANCE_HANDOFF_CONTACT_FORCE_LIMITED = "impedance_handoff_contact_force_limited"
D0_CONTROL_ARM_SUPPORT_REMOVAL_ABLATION = "support_removal_ablation"
D0_CONTROL_ARM_HOLD_TO_COMPLETION_COMPARATOR = "hold_to_completion_comparator"
D0_CONTROL_ARMS = {
    D0_CONTROL_ARM_NONE,
    D0_CONTROL_ARM_ORACLE_POSE_OR_FORCE_HOLD,
    D0_CONTROL_ARM_RELEASE_RAMP_5,
    D0_CONTROL_ARM_RELEASE_RAMP_10,
    D0_CONTROL_ARM_IMPEDANCE_HANDOFF_CONTACT_FORCE_LIMITED,
    D0_CONTROL_ARM_SUPPORT_REMOVAL_ABLATION,
    D0_CONTROL_ARM_HOLD_TO_COMPLETION_COMPARATOR,
}
D0_CONTROL_PRODUCT_ARMS = {
    D0_CONTROL_ARM_ORACLE_POSE_OR_FORCE_HOLD,
    D0_CONTROL_ARM_RELEASE_RAMP_5,
    D0_CONTROL_ARM_RELEASE_RAMP_10,
    D0_CONTROL_ARM_IMPEDANCE_HANDOFF_CONTACT_FORCE_LIMITED,
    D0_CONTROL_ARM_SUPPORT_REMOVAL_ABLATION,
}
D0_CONTROL_COMPARATOR_ARMS = {D0_CONTROL_ARM_HOLD_TO_COMPLETION_COMPARATOR}
D0_CONTROL_FORCE_SCALE_KEY = "d0_control_force_scale"
D0_CONTROL_FORCE_SCALE_MIN_KEY = "d0_control_force_scale_min"
D0_CONTROL_RELEASE_STEP_KEY = "d0_control_release_step"
D0_CONTROL_TARGET_BLEND_KEY = "d0_control_target_blend"
D0_CONTROL_LEFT_TARGET_OFFSET_KEY = "d0_control_left_target_offset_xyz"
D0_CONTROL_HUMAN_RS_PREDICATE_CONFIRMED_KEY = "d0_human_rs_predicate_confirmed"
S1B_GRASP_GEOMETRY_TELEMETRY_ENABLED_KEY = "s1b_grasp_geometry_telemetry_enabled"
S1B_GRASP_GEOMETRY_TELEMETRY_SCHEMA_VERSION = "s1b_grasp_geometry_telemetry_v2"
S1B_GRASP_GEOMETRY_TELEMETRY_PRE_RELEASE_STEPS = 4
S1B_GRASP_GEOMETRY_TELEMETRY_POST_RELEASE_STEPS = 34
S1B_GRASP_GEOMETRY_TELEMETRY_MAX_WINDOW_STEPS = 40
S1A_REWARD_ENABLED_KEY = "s1a_release_readiness_reward_enabled"
S1A_OBSERVATION_ENABLED_KEY = "s1a_release_readiness_observation_enabled"
S1A_CURRICULUM_METADATA_ENABLED_KEY = "s1a_curriculum_metadata_enabled"
S1A_OBS_SCHEMA_VERSION = 1
S1A_OBS_EXTENSION_DIM = 7

# Import scene building functions (for DEVICE override)
_script_dir = os.path.join(_env_dir, "..", "scripts")
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
import test_newton_clip_routing as _tncr

# Import task_config (SSOT)
_config_dir = os.path.join(_env_dir, "..", "configs")
if _config_dir not in sys.path:
    sys.path.insert(0, _config_dir)
from task_config import (
    BODIES_PER_ARM,
    CLIP1_X,
    CLIP1_Y,
    CLIP1_Z,
    EE_TO_FINGERTIP,
    FINGER_CLOSE_POS,
    FINGER_LOCAL,
    FINGER_OPEN_POS,
    GRIPPER_DRIVER_JOINT_IDX,
    JOINTS_PER_ARM,
    K_GRASP,
    LIFT_Z,
    SIM_SUBSTEPS,
    T_ALIGN,
    T_DIST_APPROACH,
    TABLE_HEIGHT,
)

# IK rotation targets: hand down
_cos_pi8 = math.cos(math.pi / 8)
_sin_pi8 = math.sin(math.pi / 8)


class NewtonAerialRegraspEnv(VecEnv):
    """RSL-RL VecEnv for AerialRegrasp -- multi-world with replicate().

    v5 unified obs/action/reward design.
    Precondition: left arm holds cable at LIFT_Z, right arm open at LIFT_Z.
    Task: right arm approaches cable and grasps it.
    """

    # Action scaling (same as ApproachCable v5)
    POS_ACTION_SCALE = 0.015  # 15mm per RL step
    ROT_ACTION_SCALE = 0.05  # ~2.9deg per RL step
    ADAPTIVE_POS_SCALE = True  # Distance-adaptive pos scale for 1mm precision
    FINE_THRESHOLD = 0.050  # 50mm
    MIN_POS_SCALE = 0.0005  # 0.5mm
    MAX_EPISODE_STEPS = 200
    PHYSICS_STEPS_PER_RL = 10
    EXPLOSION_DIST_THRESH = 1.0  # VBD explosion guard [m]

    # Target cable segment: wider window for regrasp approach
    GRIP_SEG_WINDOW = 5  # +/-5 segments (11 segments = 165mm range)
    TARGET_EMA_ALPHA = 1.0  # EMA disabled: raw cable position used directly (obs/reward/success all consistent)
    INIT_XY_NOISE = 0.005  # +/-5mm initial EE position randomization (was 2mm — CC4 CH4 reset diversity fix 2026-04-20)

    # Reward: pose_match (v37) -- non-negative shift [0, 1] (IC v36 pattern)
    REWARD_MODE = "hybrid"
    EPS_POS = 0.015  # 15mm
    EPS_POS_MED = 0.10  # 100mm mid-range (ACと統一)
    EPS_POS_COARSE = 1.0  # 1m (long-range gradient)
    EPS_ORI = 0.18  # α.4b V7.1: 0.25→0.18 sharper ori grad at empirical 15° band (~10.3deg)
    EPS_ORI_COARSE = 1.5  # ~86deg coarse ori decay (long-range gradient, mirrors AC/IC)
    W_POS = 0.5  # v37: halved (non-negative shift — range [0, 1.0])
    W_ORI = 0.75  # α.4b V7.1: 0.5→0.75 ori reward +50% (empirical 15.3° bottleneck)
    RANGE_POS = 0.050  # 50mm (multiplicative mode, unified with GC/IC)
    RANGE_ORI = 0.5  # 0.5 rad (1.0→0.5 for stronger ori gradient)
    PROGRESS_SCALE = 2.0
    PROGRESS_W_POS = 0.2
    PROGRESS_W_ORI = 0.2
    PROGRESS_W_COUPLED = 0.6
    R_STEP_BONUS = 10.0  # α.4b V7.1: 5.0→10.0 gate crossing reward 2x
    R_TASK_BONUS = 200.0  # v37: 20→200 (anti-hover: success must dominate hover)
    # R_PENALTY calibrated to zero-out non-negative reward at P0 (dist_pos~50mm, dist_ori~0.3):
    # v38 baseline (W_ORI=0.5, EPS_ORI=0.25, W_TAIL=3.0):
    #   r_pos_P0 = 0.5*(exp(-50/15)+exp(-50/100)+exp(-50/1000))/3 = 0.5*0.531 = 0.265
    #   r_ori_P0_v38 = 0.5*(exp(-0.3/0.25)+exp(-0.3/1.5))/2 = 0.280
    #   r_ease_P0 = 0.3*exp(-0.5/0.5) = 0.110, r_height_P0 = 0.2*1.0 = 0.200
    #   r_ori_tail_P0_v38 = -3.0*min(0.3-0.14, 0.15) = -0.450
    #   r_sum_P0_v38 = 0.265+0.280+0.110+0.200-0.450 = 0.405, Net@P0_v38 = -0.595
    # α.4b V7.1 (2026-04-30 Rs Q1+C; W_ORI 0.5→0.75, EPS_ORI 0.25→0.18, W_TAIL 3.0→4.0):
    #   r_ori_P0_v7.1 = 0.75*(exp(-0.3/0.18)+exp(-0.3/1.5))/2 = 0.75*(0.189+0.819)/2 = 0.378
    #   r_ori_tail_P0_v7.1 = -4.0*min(0.3-0.14, 0.15) = -0.600 (capped)
    #   r_sum_P0_v7.1 = 0.265+0.378+0.110+0.200-0.600 = 0.353, Net@P0_v7.1 = -0.647 (strictly negative)
    # v38 CC5 fix 2026-04-20: R_PENALTY = -1.0 (was -0.41). Hover-trap mitigation preserved in V7.1.
    # Rationale: hover-trap resolution — policy must progress to earn positive reward.
    # Hover 200 steps_v7.1 = -141 vs R_TASK_BONUS=200, success advantage +351 typical (CC3 verified).
    # /reward-design gate iter 3 PASS post-5-CC: 0 CRIT/HIGH, 4 MED operational, 7 LOW. CV1+CV2 monitor active.
    R_PENALTY = -1.0  # v38: CC5 hover-trap fix (was -0.41 v37c)
    R_DROP = -50.0  # v37: one-shot terminal penalty (replaces per-step grace)

    # Ori tail penalty: linear penalty for dist_ori exceeding warning threshold
    # Targets the heavy tail (p95≈12° > success 10°) without affecting median (2.3°)
    W_TAIL = 4.0  # α.4b V7.1: 3.0→4.0 ori-drive +33% at empirical 15° band
    THRESH_WARN = 0.14  # 8° — warning zone starts 2° below success threshold (10°)
    ORI_TAIL_CAP = 0.15  # Cap ori_excess 0.15 rad → V7.1 max penalty -0.60/step (W_TAIL=4)

    CLOSE_ACTION_DAMPING = 0.1  # Left arm action damping (stabilizer role)
    ORI_GATE_POS_THRESH = 0.010  # 10mm: ori-gated approach zone radius
    ORI_GATE_ORI_THRESH = 0.2618  # 15°: ori must be below this before close approach

    # SUCCESS condition: approach(pos + ori) ^ cable_not_dropped ^ sustained(K)
    # finger close is NOT part of this skill — handled by Grip.
    CLAMP_DIST_THRESH = T_DIST_APPROACH  # approach.pos: 12mm (Grip INIT_POS_NOISE=12mmと整合)
    CLAMP_ORI_THRESH = T_ALIGN  # 10deg
    C5_SUSTAIN_STEPS = K_GRASP  # K_GRASP RL steps (design doc: 5)

    # Cable state reward: cable presentation quality (both arms contribute as one agent)
    W_EASE = 0.3  # v37: 0.5→0.3 (non-negative shift, reduced — approach中制御不能)
    RANGE_EASE = 0.5  # Exponential scale [rad], same as RANGE_ORI
    W_HEIGHT = 0.2  # v37: 0.3→0.2 (non-negative shift, reduced)
    W_STAB = 0.0  # α.4b grid.1 v3 (2026-05-03 Rs Z1+B): 0.2→0.0 obs-gap noise removal (§運用21, MLP, no jitter in obs)
    STAB_JITTER_CAP = 0.01  # 10mm jitter cap for r_stable normalization

    # Left arm hold: dense regularizers to prevent cable drop
    W_HOLD = 0.0  # v37: 0.3→0 (eliminated — CLOSE_ACTION_DAMPING=0.1 handles mechanically)
    W_DRIFT = 2.0  # v37: 5→2 (reduced — max penalty -0.02/step)
    DRIFT_CAP = 0.010  # 10mm cap → max penalty -0.02/step (200 steps = -4, within R_TASK_BONUS budget)

    # Cable drop threshold: cable Z must stay above TABLE_HEIGHT + 20mm
    CABLE_DROP_Z_THRESH = TABLE_HEIGHT + 0.02
    DROP_GRACE_STEPS = 5  # v37: 20→5 (shorter grace; R_DROP=-50 one-shot at termination)
    # A6 Phase 5: additional drop grace if terminal_entered (per Rs代行 06:35 disposition β + E1 saturation K=5)
    # Effective grace = DROP_GRACE_STEPS + TERMINAL_GRACE_STEPS only when self._terminal_entered[w] is True.
    # AR success criterion unchanged. A2 cable_drop subclassing deferred per pre-check NO_GO.
    TERMINAL_GRACE_STEPS = 5

    # Clip C1 pose (constant, same as ApproachCable)
    CLIP1_POS = np.array([CLIP1_X, CLIP1_Y, CLIP1_Z], dtype=np.float32)
    CLIP1_QUAT_XYZW = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)

    # Cache directory
    CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "rl_aerial_regrasp_cache")
    CACHE_VERSION = "v2"  # v2 cache is compatible (inv_mass overridden at load time)

    def __init__(
        self,
        world_count=4,
        device="cuda:0",
        cfg=None,
        clip_x: float | None = None,
        clip_y: float | None = None,
        *,
        # === Phase 4 #2 behavioral: V0.1 gating flags + cache_path_override (default off = Q1 state) ===
        enable_b_a5_2_hold_break_termination: bool = False,
        enable_b_a3_1_success_right_clamp_left_hold_metric: bool = False,
        cache_path_override: str | None = None,
        # === END Phase 4 #2 behavioral constructor args ===
        # === Phase 5 A6: termination-ordering grace gating (default OFF = V6 baseline reproduction) ===
        # Per Rs代行 disposition 2026-05-13 modified (α) post V7 gate NO_GO finding:
        # A6 grace extends drop_grace threshold conditional on terminal_entered; gated by this flag
        # to permit clean V7 A/B (control arm enable_a6_grace=False reproduces V6; intervention=True
        # applies A6). AR success criterion `clamp(R) ∧ cable_not_dropped ∧ sustained(K=5)` UNCHANGED.
        enable_a6_grace: bool = False,
        # === END Phase 5 A6 constructor args ===
        # === R2-A: left-anchor freeze (default ON per Phase 1-B smoke evidence) ===
        freeze_left_anchor: bool = True,
        # === END R2-A left-anchor freeze ===
        # === R2-A Track A: opt-in kinematic pre-contact support predicate ===
        kinematic_left_finger_support_enabled: bool = False,
        kinematic_left_finger_support_hold_steps: int = KINEMATIC_HOLD_STEPS,
        kinematic_left_finger_support_gate_type: str = KINEMATIC_GATE_TYPE,
        kinematic_left_finger_support_release_success_hold_steps: int = KINEMATIC_RELEASE_SUCCESS_HOLD_STEPS,
        kinematic_left_finger_support_release_stability_steps: int = KINEMATIC_RELEASE_STABILITY_STEPS,
        kinematic_left_finger_support_max_hold_steps: int = KINEMATIC_MAX_HOLD_STEPS,
        # === END R2-A Track A kinematic predicate args ===
    ):
        self.num_envs = world_count
        self.num_actions = 12
        self._total_env_steps = 0
        self.max_episode_length = self.MAX_EPISODE_STEPS
        self.device = device
        self.cfg = cfg or {}
        self._world_count = world_count
        # === Phase 4 #2 behavioral: V0.1 intervention gating + cache_path_override validation ===
        if cache_path_override is not None:
            if not isinstance(cache_path_override, str):
                raise ValueError("cache_path_override must be str or None")
            if not os.path.exists(cache_path_override):
                raise ValueError(f"cache_path_override file does not exist: {cache_path_override}")
        self._cache_path_override = cache_path_override
        self._enable_b_a5_2 = bool(enable_b_a5_2_hold_break_termination)
        self._enable_b_a3_1 = bool(enable_b_a3_1_success_right_clamp_left_hold_metric)
        # === END Phase 4 #2 behavioral validation ===
        # === Phase 5 A6 gating flag store (default False reproduces V6 baseline behavior) ===
        self._enable_a6_grace = bool(enable_a6_grace)
        # === END Phase 5 A6 gating ===
        # === R2-A left-anchor freeze flag ===
        self._freeze_left_anchor = bool(freeze_left_anchor)
        self._freeze_wdrift_warned = False  # one-time W_DRIFT no-op warning (fires at first freeze activation)
        # === END R2-A left-anchor freeze ===
        # === R2-A Track A kinematic predicate validation/store ===
        if kinematic_left_finger_support_gate_type not in KINEMATIC_GATE_TYPES:
            raise ValueError(
                "kinematic_left_finger_support_gate_type must be one of "
                f"{sorted(KINEMATIC_GATE_TYPES)} "
                f"(got {kinematic_left_finger_support_gate_type!r})"
            )
        kinematic_hold_steps = int(kinematic_left_finger_support_hold_steps)
        if kinematic_hold_steps <= 0 or kinematic_hold_steps > self.MAX_EPISODE_STEPS:
            raise ValueError(
                "kinematic_left_finger_support_hold_steps must be in "
                f"[1, {self.MAX_EPISODE_STEPS}] (got {kinematic_hold_steps})"
            )
        kinematic_release_success_hold_steps = int(
            kinematic_left_finger_support_release_success_hold_steps
        )
        if (
            kinematic_release_success_hold_steps <= 0
            or kinematic_release_success_hold_steps > self.MAX_EPISODE_STEPS
        ):
            raise ValueError(
                "kinematic_left_finger_support_release_success_hold_steps must be in "
                f"[1, {self.MAX_EPISODE_STEPS}] (got {kinematic_release_success_hold_steps})"
            )
        kinematic_release_stability_steps = int(
            kinematic_left_finger_support_release_stability_steps
        )
        if (
            kinematic_release_stability_steps <= 0
            or kinematic_release_stability_steps > self.MAX_EPISODE_STEPS
        ):
            raise ValueError(
                "kinematic_left_finger_support_release_stability_steps must be in "
                f"[1, {self.MAX_EPISODE_STEPS}] (got {kinematic_release_stability_steps})"
            )
        kinematic_max_hold_steps = int(kinematic_left_finger_support_max_hold_steps)
        if kinematic_max_hold_steps <= 0 or kinematic_max_hold_steps > self.MAX_EPISODE_STEPS:
            raise ValueError(
                "kinematic_left_finger_support_max_hold_steps must be in "
                f"[1, {self.MAX_EPISODE_STEPS}] (got {kinematic_max_hold_steps})"
            )
        self._kinematic_left_finger_support_enabled = bool(kinematic_left_finger_support_enabled)
        if self._kinematic_left_finger_support_enabled and not self._freeze_left_anchor:
            raise ValueError("kinematic_left_finger_support_enabled=True requires freeze_left_anchor=True")
        self._kinematic_left_finger_support_hold_steps = kinematic_hold_steps
        self._kinematic_left_finger_support_gate_type = str(kinematic_left_finger_support_gate_type)
        self._kinematic_release_success_hold_steps = kinematic_release_success_hold_steps
        self._kinematic_release_stability_steps = kinematic_release_stability_steps
        self._kinematic_max_hold_steps = kinematic_max_hold_steps
        self._kinematic_support_active = np.zeros(world_count, dtype=np.bool_)
        self._kinematic_release_step = np.full(world_count, -1, dtype=np.int32)
        self._kinematic_release_reason = np.full(world_count, "not_enabled", dtype="<U32")
        self._kinematic_release_ready_count = np.zeros(world_count, dtype=np.int32)
        self._kinematic_post_release_steps = np.full(world_count, -1, dtype=np.int32)
        self._kinematic_release_ready_reason = np.full(world_count, "not_ready", dtype="<U32")
        self._kinematic_released_after_success = np.zeros(world_count, dtype=np.bool_)
        self._kinematic_release_terminal_hold_len = np.zeros(world_count, dtype=np.int32)
        self._kinematic_release_right_clamp = np.zeros(world_count, dtype=np.bool_)
        self._kinematic_release_left_hold = np.zeros(world_count, dtype=np.bool_)
        self._kinematic_release_cable_not_dropped = np.zeros(world_count, dtype=np.bool_)
        self._left_finger_dynamic_inv_mass = None
        self._left_finger_dynamic_inv_inertia = None
        self._left_finger_inv_mass = None
        self._left_finger_inv_inertia = None
        # === END R2-A Track A kinematic predicate store ===
        # === D0 telemetry-only source draft (default off, observational only) ===
        self._d0_contact_telemetry_enabled = bool(self._cfg_get(D0_CONTACT_TELEMETRY_ENABLED_KEY, False))
        self._d0_contact_sensor_prim_path = self._cfg_get(D0_CONTACT_SENSOR_PRIM_PATH_KEY, None)
        self._d0_contact_sensor_shape_expr = self._cfg_list(D0_CONTACT_SENSOR_SHAPE_EXPR_KEY)
        self._d0_contact_filter_prim_paths_expr = self._cfg_list(D0_CONTACT_FILTER_PRIM_PATHS_EXPR_KEY)
        self._d0_contact_filter_shape_expr = self._cfg_list(D0_CONTACT_FILTER_SHAPE_EXPR_KEY)
        self._d0_contact_force_limit = self._cfg_get(D0_CONTACT_FORCE_LIMIT_KEY, None)
        if self._d0_contact_force_limit is not None:
            self._d0_contact_force_limit = float(self._d0_contact_force_limit)
        self._d0_contact_sensor = None
        self._d0_contact_sensor_error = None
        self._d0_contact_net_force_w = None
        self._d0_contact_force_matrix_w = None
        self._d0_contact_force_norm = np.zeros(world_count, dtype=np.float32)
        self._d0_contact_force_over_limit = np.zeros(world_count, dtype=np.bool_)
        self._d0_impedance_command_force_norm = np.zeros(world_count, dtype=np.float32)
        self._d0_impedance_command_force_norm_per_finger = np.zeros(
            (world_count, len(FINGER_LOCAL)),
            dtype=np.float32,
        )
        # === END D0 telemetry-only source draft ===
        # === S1B grasp-geometry telemetry (default off, observational only) ===
        self._s1b_grasp_geometry_telemetry_enabled = bool(
            self._cfg_get(S1B_GRASP_GEOMETRY_TELEMETRY_ENABLED_KEY, False)
        )
        self._s1b_grasp_geometry_telemetry_history = (
            [[] for _ in range(world_count)]
            if self._s1b_grasp_geometry_telemetry_enabled
            else None
        )
        self._s1b_first_cable_drop_step = np.full(world_count, -1, dtype=np.int32)
        self._s1b_first_clamp_loss_step = np.full(world_count, -1, dtype=np.int32)
        self._s1b_first_explosion_step = np.full(world_count, -1, dtype=np.int32)
        self._s1b_observed_release_step = np.full(world_count, -1, dtype=np.int32)
        self._s1b_actual_release_event = np.zeros(world_count, dtype=np.bool_)
        self._s1b_telemetry_anchor_step = np.full(world_count, -1, dtype=np.int32)
        self._s1b_telemetry_anchor_event = np.full(world_count, "unanchored", dtype="<U32")
        self._s1b_prev_left_cable_point = np.zeros((world_count, 3), dtype=np.float32)
        self._s1b_prev_right_cable_point = np.zeros((world_count, 3), dtype=np.float32)
        self._s1b_prev_left_gripper = np.zeros((world_count, 3), dtype=np.float32)
        self._s1b_prev_right_gripper = np.zeros((world_count, 3), dtype=np.float32)
        self._s1b_prev_geometry_valid = np.zeros(world_count, dtype=np.bool_)
        # === END S1B grasp-geometry telemetry ===
        # === D0 control-source draft (default off, no-crutch, source surface only) ===
        self._d0_control_arm = str(self._cfg_get(D0_CONTROL_ARM_KEY, D0_CONTROL_ARM_NONE) or D0_CONTROL_ARM_NONE)
        self._d0_control_enabled = self._d0_control_arm != D0_CONTROL_ARM_NONE
        self._d0_control_force_scale = self._cfg_float(D0_CONTROL_FORCE_SCALE_KEY, 1.0)
        self._d0_control_force_scale_min = self._cfg_float(D0_CONTROL_FORCE_SCALE_MIN_KEY, 0.0)
        self._d0_control_release_step = int(self._cfg_float(D0_CONTROL_RELEASE_STEP_KEY, 0))
        self._d0_control_target_blend = self._cfg_float(D0_CONTROL_TARGET_BLEND_KEY, 0.0)
        self._d0_control_left_target_offset = self._cfg_float_array(
            D0_CONTROL_LEFT_TARGET_OFFSET_KEY,
            3,
            [0.0, 0.0, 0.0],
        )
        self._d0_human_rs_predicate_confirmed = bool(
            self._cfg_get(D0_CONTROL_HUMAN_RS_PREDICATE_CONFIRMED_KEY, False)
        )
        self._d0_control_refusal_reason = None
        self._d0_control_force_scale_per_world = np.ones(world_count, dtype=np.float32)
        self._d0_control_target_blend_applied = np.zeros(world_count, dtype=np.bool_)
        self._validate_d0_control_source_config()
        # === END D0 control-source draft ===
        # === S1A Track A release-readiness source surface (default off) ===
        self._s1a_reward_enabled = bool(self._cfg_get(S1A_REWARD_ENABLED_KEY, False))
        self._s1a_observation_enabled = bool(self._cfg_get(S1A_OBSERVATION_ENABLED_KEY, False))
        self._s1a_curriculum_metadata_enabled = bool(
            self._cfg_get(S1A_CURRICULUM_METADATA_ENABLED_KEY, False)
            or self._s1a_reward_enabled
            or self._s1a_observation_enabled
        )
        self._s1a_any_enabled = (
            self._s1a_reward_enabled
            or self._s1a_observation_enabled
            or self._s1a_curriculum_metadata_enabled
        )
        self._validate_s1a_source_config()
        # === END S1A release-readiness source surface ===

        # Clip position (parameterized for X-stagger DR across clips)
        self._clip_x = clip_x if clip_x is not None else CLIP1_X
        self._clip_y = clip_y if clip_y is not None else CLIP1_Y
        self.CLIP1_POS = np.array([self._clip_x, self._clip_y, CLIP1_Z], dtype=np.float32)

        self.episode_length_buf = torch.zeros(world_count, dtype=torch.long, device=device)
        self._target_seg_indices_r = None
        self._target_seg_indices_l = None
        self._success_sustain_count = np.zeros(world_count, dtype=np.int32)
        self._terminal_entered = np.zeros(world_count, dtype=np.bool_)
        self._terminal_hold_len = np.zeros(world_count, dtype=np.int32)
        self._terminal_break_reason = np.full(world_count, "unspecified", dtype="<U11")
        # === A5 Phase 4 #2: Hold-Detection Feedback Loop signal tracking (logging-only) ===
        self._prev_terminal_candidate = np.zeros(world_count, dtype=np.bool_)
        # _hold_signal_event_this_step encoding: 0=none, 1=acquired, 2=lost, 3=k5_sustained
        self._hold_signal_event_this_step = np.zeros(world_count, dtype=np.int32)
        self._hold_signal_acquired_count = np.zeros(world_count, dtype=np.int32)  # cumulative per-episode
        self._hold_signal_lost_count = np.zeros(world_count, dtype=np.int32)
        self._hold_signal_k5_sustained_count = np.zeros(world_count, dtype=np.int32)
        # === END A5 Phase 4 #2 ===
        # === B-A5.2 Phase 4 #2 behavioral: hold-failure-aware termination state (gated by self._enable_b_a5_2) ===
        self._hold_break_count = np.zeros(world_count, dtype=np.int32)
        self._hold_break_terminated = np.zeros(world_count, dtype=np.bool_)
        self.B_A5_2_HOLD_BREAK_THRESHOLD = 3  # terminate after N hold-break events per episode
        # === END B-A5.2 Phase 4 #2 behavioral ===
        # === B-A3.1 Phase 4 #2 behavioral: R-clamp + L-hold counterfactual state (gated) ===
        self._success_right_clamp_left_hold_sustain_count = np.zeros(world_count, dtype=np.int32)
        self._success_right_clamp_left_hold = np.zeros(world_count, dtype=np.bool_)
        # === END B-A3.1 Phase 4 #2 behavioral ===
        self._step_completed_right = np.zeros(world_count, dtype=bool)
        self._drop_grace = np.zeros(world_count, dtype=np.int32)
        self._episode_count = 0
        # L2 fix: episode-level success tracking for best-model save
        from collections import deque

        self._episode_success_buf = deque(maxlen=200)
        self._last_success_rate = 0.0

        # Per-world EE targets (explicit tracking avoids FK drift)
        self._ee_target_right = np.zeros((world_count, 3), dtype=np.float32)
        self._ee_target_left = np.zeros((world_count, 3), dtype=np.float32)
        self._ee_quat_right = np.zeros((world_count, 4), dtype=np.float32)
        self._ee_quat_left = np.zeros((world_count, 4), dtype=np.float32)

        # Temporal quaternion consistency state (Bug #2 fix)
        self._prev_clamp_r_quat = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))
        self._prev_clamp_l_quat = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))
        self._prev_seg_r_quat = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))
        self._prev_seg_l_quat = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))

        # Left arm hold penalty: store last actions for reward computation
        self._last_actions = None

        # Cable jitter tracking for r_stable
        self._prev_seg_pos_raw_r = np.zeros((world_count, 3), dtype=np.float32)
        self._prev_seg_pos_raw_valid = np.zeros(world_count, dtype=bool)

        # Bug #4 fix: EMA smoothing for aerial cable target (obs only)
        self._ema_seg_pos_r = np.zeros((world_count, 3), dtype=np.float32)
        self._ema_seg_pos_l = np.zeros((world_count, 3), dtype=np.float32)
        self._ema_seg_quat_r = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))
        self._ema_seg_quat_l = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (world_count, 1))
        self._ema_initialized = np.zeros(world_count, dtype=bool)

        # Override device for Newton
        os.environ["NEWTON_DEVICE"] = device
        _tncr.DEVICE = device

        print(f"[AerialRegraspEnv] Initializing: {world_count} worlds on {device}")
        t0 = time.perf_counter()

        # Phase 1: Build FK model + multi-world scene
        self._build_model()
        self._init_d0_contact_telemetry()

        # Phase 2: Load precondition cache (mandatory)
        if not self._load_and_restore_cache():
            raise RuntimeError(
                f"[AerialRegraspEnv] Precondition cache not found. "
                f"Run build_aerial_regrasp_precondition.py first. "
                f"Expected: {self._cache_path()}"
            )

        # Phase 3: Batched IK solver for RL stepping
        self._init_batched_ik_solver()
        if self._kinematic_left_finger_support_enabled:
            self._activate_kinematic_left_finger_support(range(self._world_count))

        print(
            f"[AerialRegraspEnv] Ready in {time.perf_counter() - t0:.1f}s. "
            f"obs={self.num_obs}, act={self.num_actions}, worlds={world_count}"
        )

    # =========================================================================
    # Environment Construction
    # =========================================================================

    def _cfg_get(self, key, default=None):
        """Read an optional environment config key with default-off behavior."""
        if isinstance(self.cfg, dict):
            return self.cfg.get(key, default)
        return getattr(self.cfg, key, default)

    def _cfg_list(self, key):
        """Read an optional config list while accepting a single string."""
        value = self._cfg_get(key, [])
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    def _cfg_float(self, key, default):
        """Read an optional config value as a finite float."""
        value = self._cfg_get(key, default)
        if value is None:
            value = default
        result = float(value)
        if not np.isfinite(result):
            raise ValueError(f"{key} must be finite (got {value!r})")
        return result

    def _cfg_float_array(self, key, expected_len, default):
        """Read an optional numeric config array with a fixed length."""
        value = self._cfg_get(key, default)
        if value is None:
            value = default
        if isinstance(value, str):
            value = [part.strip() for part in value.split(",") if part.strip()]
        result = np.asarray(value, dtype=np.float32)
        if result.shape != (expected_len,):
            raise ValueError(f"{key} must contain {expected_len} values (got shape {result.shape})")
        if not np.all(np.isfinite(result)):
            raise ValueError(f"{key} must contain finite values")
        return result

    def _validate_s1a_source_config(self):
        """Fail closed for inconsistent default-off S1A source-surface config."""
        if self._s1a_reward_enabled and not self._s1a_observation_enabled:
            raise ValueError(
                f"{S1A_REWARD_ENABLED_KEY}=True requires "
                f"{S1A_OBSERVATION_ENABLED_KEY}=True so reward inputs are policy-observed"
            )
        if self._s1a_reward_enabled and self._d0_control_arm not in D0_CONTROL_PRODUCT_ARMS:
            raise ValueError(
                f"{S1A_REWARD_ENABLED_KEY}=True requires a D0 product release arm so "
                "never-release and hold-to-completion-only states are not rewarded"
            )
        if self._s1a_any_enabled and self._kinematic_left_finger_support_enabled:
            raise ValueError("S1A source surfaces refuse kinematic_left_finger_support_enabled=True")

    def _validate_d0_control_source_config(self):
        """Fail closed for opt-in D0 control arms that would use crutch paths."""
        if self._d0_control_arm not in D0_CONTROL_ARMS:
            raise ValueError(
                f"{D0_CONTROL_ARM_KEY} must be one of {sorted(D0_CONTROL_ARMS)} "
                f"(got {self._d0_control_arm!r})"
            )
        if self._d0_control_force_scale < 0.0:
            raise ValueError(f"{D0_CONTROL_FORCE_SCALE_KEY} must be non-negative")
        if self._d0_control_force_scale_min < 0.0:
            raise ValueError(f"{D0_CONTROL_FORCE_SCALE_MIN_KEY} must be non-negative")
        if self._d0_control_force_scale_min > self._d0_control_force_scale:
            raise ValueError(
                f"{D0_CONTROL_FORCE_SCALE_MIN_KEY} must be <= {D0_CONTROL_FORCE_SCALE_KEY}"
            )
        if self._d0_control_release_step < 0 or self._d0_control_release_step > self.MAX_EPISODE_STEPS:
            raise ValueError(
                f"{D0_CONTROL_RELEASE_STEP_KEY} must be in [0, {self.MAX_EPISODE_STEPS}] "
                f"(got {self._d0_control_release_step})"
            )
        if not 0.0 <= self._d0_control_target_blend <= 1.0:
            raise ValueError(f"{D0_CONTROL_TARGET_BLEND_KEY} must be in [0, 1]")
        if not self._d0_control_enabled:
            return
        if self._d0_control_arm in D0_CONTROL_PRODUCT_ARMS and self._kinematic_left_finger_support_enabled:
            self._d0_control_refusal_reason = (
                "D0 product arms refuse kinematic_left_finger_support_enabled=True"
            )
            raise ValueError(self._d0_control_refusal_reason)
        if (
            self._d0_control_arm == D0_CONTROL_ARM_IMPEDANCE_HANDOFF_CONTACT_FORCE_LIMITED
            and not self._d0_contact_telemetry_enabled
        ):
            self._d0_control_refusal_reason = (
                "impedance_handoff_contact_force_limited requires d0_contact_telemetry_enabled=True"
            )
            raise ValueError(self._d0_control_refusal_reason)

    def _init_d0_contact_telemetry(self):
        """Initialize opt-in D0 contact telemetry without changing default behavior."""
        if not self._d0_contact_telemetry_enabled:
            return
        if not self._d0_contact_sensor_prim_path:
            raise RuntimeError(
                "BLOCKED_CONTACT_SENSOR_INTEGRATION: "
                f"{D0_CONTACT_SENSOR_PRIM_PATH_KEY} is required when "
                f"{D0_CONTACT_TELEMETRY_ENABLED_KEY}=True"
            )
        try:
            from isaaclab_newton.sensors.contact_sensor.contact_sensor import ContactSensor
            from isaaclab_newton.sensors.contact_sensor.contact_sensor_cfg import ContactSensorCfg

            sensor_cfg = ContactSensorCfg(
                prim_path=str(self._d0_contact_sensor_prim_path),
                sensor_shape_prim_expr=self._d0_contact_sensor_shape_expr,
                filter_prim_paths_expr=self._d0_contact_filter_prim_paths_expr,
                filter_shape_prim_expr=self._d0_contact_filter_shape_expr,
                track_contact_points=False,
                track_friction_forces=False,
            )
            self._d0_contact_sensor = ContactSensor(sensor_cfg)
            if not self._d0_contact_sensor.is_initialized:
                self._d0_contact_sensor._initialize_impl()
                self._d0_contact_sensor._is_initialized = True
        except Exception as err:
            self._d0_contact_sensor = None
            self._d0_contact_sensor_error = str(err)
            raise RuntimeError(
                "BLOCKED_CONTACT_SENSOR_INTEGRATION: "
                "D0 ContactSensor could not be initialized cleanly"
            ) from err

    def _as_numpy_telemetry(self, value):
        """Convert a telemetry array to NumPy without changing control state."""
        if value is None:
            return None
        if hasattr(value, "numpy"):
            return np.array(value.numpy(), copy=True)
        return wp.to_torch(value).detach().cpu().numpy()

    def _update_d0_contact_telemetry(self, dt):
        """Refresh observational-only D0 contact telemetry after a physics step."""
        if not self._d0_contact_telemetry_enabled or self._d0_contact_sensor is None:
            return
        try:
            self._d0_contact_sensor.update(dt)
            data = self._d0_contact_sensor.data
            self._d0_contact_net_force_w = self._as_numpy_telemetry(data.net_forces_w)
            self._d0_contact_force_matrix_w = self._as_numpy_telemetry(data.force_matrix_w)
            if self._d0_contact_net_force_w is None:
                self._d0_contact_force_norm[:] = 0.0
                self._d0_contact_force_over_limit[:] = False
                return
            force_norm = np.linalg.norm(self._d0_contact_net_force_w, axis=-1)
            if force_norm.ndim > 1:
                force_norm = np.max(force_norm, axis=tuple(range(1, force_norm.ndim)))
            self._d0_contact_force_norm[:] = np.asarray(force_norm, dtype=np.float32)
            if self._d0_contact_force_limit is None:
                self._d0_contact_force_over_limit[:] = False
            else:
                self._d0_contact_force_over_limit[:] = (
                    self._d0_contact_force_norm > self._d0_contact_force_limit
                )
        except Exception as err:
            self._d0_contact_sensor_error = str(err)
            raise RuntimeError(
                "BLOCKED_CONTACT_SENSOR_INTEGRATION: "
                "D0 ContactSensor update failed during observational telemetry refresh"
            ) from err

    def d0_contact_telemetry_state(self) -> dict:
        """Return copied D0 telemetry state for future runner inspection."""
        return {
            "enabled": bool(self._d0_contact_telemetry_enabled),
            "default_off": True,
            "observational_only": True,
            "true_contact_force_surface_present": self._d0_contact_sensor is not None,
            "true_contact_force_normal_only": True,
            "proxy_force_field_present": True,
            "contact_points_supported": False,
            "friction_forces_supported": False,
            "sensor_prim_path": self._d0_contact_sensor_prim_path,
            "sensor_shape_expr": list(self._d0_contact_sensor_shape_expr),
            "filter_prim_paths_expr": list(self._d0_contact_filter_prim_paths_expr),
            "filter_shape_expr": list(self._d0_contact_filter_shape_expr),
            "force_limit": self._d0_contact_force_limit,
            "contact_sensor_error": self._d0_contact_sensor_error,
            "d0_contact_net_force_w": (
                None
                if self._d0_contact_net_force_w is None
                else self._d0_contact_net_force_w.copy()
            ),
            "d0_contact_force_matrix_w": (
                None
                if self._d0_contact_force_matrix_w is None
                else self._d0_contact_force_matrix_w.copy()
            ),
            "d0_contact_force_norm": self._d0_contact_force_norm.copy(),
            "d0_contact_force_over_limit": self._d0_contact_force_over_limit.copy(),
            "d0_impedance_command_force_norm": self._d0_impedance_command_force_norm.copy(),
            "d0_impedance_command_force_norm_is_proxy": True,
            "no_crutch_constraints": {
                "write_joint_state_to_sim_in_control_loop": False,
                "fixture_pinning": False,
                "kinematic_support": False,
                "teleport_or_direct_state_reset": False,
                "hidden_support": False,
                "hold_to_completion_as_success": False,
                "active_at_completion_as_product_success": False,
            },
        }

    def _d0_contact_telemetry_log_fields(self):
        """Return optional D0 telemetry log fields without affecting disabled output."""
        if not self._d0_contact_telemetry_enabled:
            return {}, {}
        log = {
            "/metrics/d0_contact_telemetry_enabled": True,
            "/metrics/d0_contact_telemetry_default_off": True,
            "/metrics/d0_contact_telemetry_observational_only": True,
            "/metrics/d0_contact_true_force_surface_present": self._d0_contact_sensor is not None,
            "/metrics/d0_contact_force_norm_mean": float(np.mean(self._d0_contact_force_norm)),
            "/metrics/d0_contact_force_norm_max": float(np.max(self._d0_contact_force_norm)),
            "/metrics/d0_contact_force_over_limit_count": int(np.sum(self._d0_contact_force_over_limit)),
            "/metrics/d0_impedance_command_force_norm_mean": float(
                np.mean(self._d0_impedance_command_force_norm)
            ),
            "/metrics/d0_impedance_command_force_norm_max": float(
                np.max(self._d0_impedance_command_force_norm)
            ),
            "/metrics/d0_impedance_command_force_norm_is_proxy": True,
        }
        log_per_world = {
            "d0_contact_telemetry_enabled": np.full(self._world_count, True, dtype=np.bool_),
            "d0_contact_force_norm": self._d0_contact_force_norm.copy(),
            "d0_contact_force_over_limit": self._d0_contact_force_over_limit.copy(),
            "d0_impedance_command_force_norm": self._d0_impedance_command_force_norm.copy(),
            "d0_impedance_command_force_norm_is_proxy": np.full(self._world_count, True, dtype=np.bool_),
        }
        return log, log_per_world

    def _reset_s1b_grasp_geometry_telemetry_world(self, world_idx):
        """Reset default-off S1B geometry telemetry buffers for one world."""
        if not self._s1b_grasp_geometry_telemetry_enabled:
            return
        self._s1b_grasp_geometry_telemetry_history[int(world_idx)] = []
        self._s1b_first_cable_drop_step[int(world_idx)] = -1
        self._s1b_first_clamp_loss_step[int(world_idx)] = -1
        self._s1b_first_explosion_step[int(world_idx)] = -1
        self._s1b_observed_release_step[int(world_idx)] = -1
        self._s1b_actual_release_event[int(world_idx)] = False
        self._s1b_telemetry_anchor_step[int(world_idx)] = -1
        self._s1b_telemetry_anchor_event[int(world_idx)] = "unanchored"
        self._s1b_prev_geometry_valid[int(world_idx)] = False

    def _record_s1b_grasp_geometry_telemetry(
        self,
        *,
        world_idx,
        step_i,
        configured_release_step,
        post_release_phase,
        clamp_r_pos,
        clamp_l_pos,
        cable_point_r,
        cable_point_l,
        finger_opening_r,
        finger_opening_l,
        cable_drop,
        clamp_loss,
        explosion,
        terminal_break_reason,
        body_q,
        body_qd,
        world_body_start,
        fk_body_q_world=None,
    ):
        """Record one bounded, observation-only S1B grasp-geometry telemetry row."""
        if not self._s1b_grasp_geometry_telemetry_enabled:
            return
        world_idx = int(world_idx)
        step_i = int(step_i)
        if bool(cable_drop) and self._s1b_first_cable_drop_step[world_idx] < 0:
            self._s1b_first_cable_drop_step[world_idx] = step_i
        if bool(clamp_loss) and self._s1b_first_clamp_loss_step[world_idx] < 0:
            self._s1b_first_clamp_loss_step[world_idx] = step_i
        if bool(explosion) and self._s1b_first_explosion_step[world_idx] < 0:
            self._s1b_first_explosion_step[world_idx] = step_i
        release_transition = bool(post_release_phase > 0.0) and not bool(
            self._s1b_actual_release_event[world_idx]
        )
        if release_transition:
            self._s1b_actual_release_event[world_idx] = True
            self._s1b_observed_release_step[world_idx] = step_i
        diagnostic_failure_event = bool(
            cable_drop or clamp_loss or explosion or terminal_break_reason != "unspecified"
        )
        if self._s1b_telemetry_anchor_step[world_idx] < 0:
            if release_transition:
                self._s1b_telemetry_anchor_step[world_idx] = step_i
                self._s1b_telemetry_anchor_event[world_idx] = "observed_release"
            elif diagnostic_failure_event:
                self._s1b_telemetry_anchor_step[world_idx] = step_i
                self._s1b_telemetry_anchor_event[world_idx] = "first_terminal_or_failure"

        cable_point_r = np.asarray(cable_point_r, dtype=np.float32)
        cable_point_l = np.asarray(cable_point_l, dtype=np.float32)
        clamp_r_pos = np.asarray(clamp_r_pos, dtype=np.float32)
        clamp_l_pos = np.asarray(clamp_l_pos, dtype=np.float32)
        if self._s1b_prev_geometry_valid[world_idx]:
            cable_delta_l = cable_point_l - self._s1b_prev_left_cable_point[world_idx]
            grip_delta_l = clamp_l_pos - self._s1b_prev_left_gripper[world_idx]
            cable_delta_r = cable_point_r - self._s1b_prev_right_cable_point[world_idx]
            grip_delta_r = clamp_r_pos - self._s1b_prev_right_gripper[world_idx]
            slip_proxy_l = float(np.linalg.norm(cable_delta_l - grip_delta_l))
            slip_proxy_r = float(np.linalg.norm(cable_delta_r - grip_delta_r))
        else:
            slip_proxy_l = 0.0
            slip_proxy_r = 0.0

        contact_sensor_present = self._d0_contact_sensor is not None
        contact_force_available = bool(
            self._d0_contact_telemetry_enabled
            and contact_sensor_present
            and self._d0_contact_net_force_w is not None
        )
        force_matrix_available = bool(contact_force_available and self._d0_contact_force_matrix_w is not None)
        if force_matrix_available:
            force_matrix_norm = float(np.linalg.norm(self._d0_contact_force_matrix_w[world_idx]))
        else:
            force_matrix_norm = 0.0
        if contact_force_available:
            contact_force_norm = float(self._d0_contact_force_norm[world_idx])
        else:
            contact_force_norm = 0.0

        def point_segment_distance(point, segment_a, segment_b):
            segment = segment_b - segment_a
            denom = float(np.dot(segment, segment))
            if denom <= 1.0e-12:
                return float(np.linalg.norm(point - segment_a)), 0.0
            t = float(np.dot(point - segment_a, segment) / denom)
            t_clamped = max(0.0, min(1.0, t))
            closest = segment_a + t_clamped * segment
            return float(np.linalg.norm(point - closest)), t

        left_finger0_pos = np.asarray(
            body_q[int(world_body_start) + FINGER_LOCAL[0]][:3],
            dtype=np.float32,
        )
        left_finger1_pos = np.asarray(
            body_q[int(world_body_start) + FINGER_LOCAL[1]][:3],
            dtype=np.float32,
        )
        right_finger0_pos = np.asarray(
            body_q[int(world_body_start) + BODIES_PER_ARM + FINGER_LOCAL[0]][:3],
            dtype=np.float32,
        )
        right_finger1_pos = np.asarray(
            body_q[int(world_body_start) + BODIES_PER_ARM + FINGER_LOCAL[1]][:3],
            dtype=np.float32,
        )
        left_finger0_fk_error = 0.0
        left_finger1_fk_error = 0.0
        right_finger0_fk_error = 0.0
        right_finger1_fk_error = 0.0
        if fk_body_q_world is not None:
            fk_body_q_world = np.asarray(fk_body_q_world, dtype=np.float32)
            left_finger0_fk_pos = fk_body_q_world[FINGER_LOCAL[0]][:3]
            left_finger1_fk_pos = fk_body_q_world[FINGER_LOCAL[1]][:3]
            right_finger0_fk_pos = fk_body_q_world[BODIES_PER_ARM + FINGER_LOCAL[0]][:3]
            right_finger1_fk_pos = fk_body_q_world[BODIES_PER_ARM + FINGER_LOCAL[1]][:3]
            left_finger0_fk_error = float(np.linalg.norm(left_finger0_pos - left_finger0_fk_pos))
            left_finger1_fk_error = float(np.linalg.norm(left_finger1_pos - left_finger1_fk_pos))
            right_finger0_fk_error = float(np.linalg.norm(right_finger0_pos - right_finger0_fk_pos))
            right_finger1_fk_error = float(np.linalg.norm(right_finger1_pos - right_finger1_fk_pos))
        right_cable_finger_line_distance, right_cable_finger_line_t = point_segment_distance(
            cable_point_r, right_finger0_pos, right_finger1_pos
        )
        left_cable_finger_line_distance, left_cable_finger_line_t = point_segment_distance(
            cable_point_l, left_finger0_pos, left_finger1_pos
        )
        right_cable_finger0_distance = float(np.linalg.norm(cable_point_r - right_finger0_pos))
        right_cable_finger1_distance = float(np.linalg.norm(cable_point_r - right_finger1_pos))
        left_cable_finger0_distance = float(np.linalg.norm(cable_point_l - left_finger0_pos))
        left_cable_finger1_distance = float(np.linalg.norm(cable_point_l - left_finger1_pos))
        right_finger_span_distance = float(np.linalg.norm(right_finger0_pos - right_finger1_pos))
        left_finger_span_distance = float(np.linalg.norm(left_finger0_pos - left_finger1_pos))
        release_class = "actual_release" if self._s1b_actual_release_event[world_idx] else "not_released"
        if not self._s1b_actual_release_event[world_idx] and diagnostic_failure_event:
            release_class = "aborted_before_release"
        record = {
            "schema_version": S1B_GRASP_GEOMETRY_TELEMETRY_SCHEMA_VERSION,
            "world_id": world_idx,
            "step": step_i,
            "anchor_step": int(self._s1b_telemetry_anchor_step[world_idx]),
            "anchor_event": str(self._s1b_telemetry_anchor_event[world_idx]),
            "configured_release_step": int(configured_release_step),
            "observed_release_step": int(self._s1b_observed_release_step[world_idx]),
            "actual_release_event": bool(self._s1b_actual_release_event[world_idx]),
            "release_class": release_class,
            "release_detection_source": "env.s1a_post_release_phase",
            "post_release_phase": float(post_release_phase),
            "first_cable_drop_step": int(self._s1b_first_cable_drop_step[world_idx]),
            "first_clamp_loss_step": int(self._s1b_first_clamp_loss_step[world_idx]),
            "first_explosion_step": int(self._s1b_first_explosion_step[world_idx]),
            "terminal_break_reason": str(terminal_break_reason),
            "cable_point_right_xyz": cable_point_r.copy(),
            "cable_point_left_xyz": cable_point_l.copy(),
            "gripper_right_xyz": clamp_r_pos.copy(),
            "gripper_left_xyz": clamp_l_pos.copy(),
            "right_gripper_to_cable_distance": float(np.linalg.norm(clamp_r_pos - cable_point_r)),
            "left_gripper_to_cable_distance": float(np.linalg.norm(clamp_l_pos - cable_point_l)),
            "right_cable_finger0_distance": right_cable_finger0_distance,
            "right_cable_finger1_distance": right_cable_finger1_distance,
            "right_cable_finger_min_distance": min(
                right_cable_finger0_distance, right_cable_finger1_distance
            ),
            "right_cable_finger_line_distance": right_cable_finger_line_distance,
            "right_cable_finger_line_t": right_cable_finger_line_t,
            "right_finger_span_distance": right_finger_span_distance,
            "left_cable_finger0_distance": left_cable_finger0_distance,
            "left_cable_finger1_distance": left_cable_finger1_distance,
            "left_cable_finger_min_distance": min(
                left_cable_finger0_distance, left_cable_finger1_distance
            ),
            "left_cable_finger_line_distance": left_cable_finger_line_distance,
            "left_cable_finger_line_t": left_cable_finger_line_t,
            "left_finger_span_distance": left_finger_span_distance,
            "left_finger0_fk_error_distance": left_finger0_fk_error,
            "left_finger1_fk_error_distance": left_finger1_fk_error,
            "left_finger_fk_error_max": max(left_finger0_fk_error, left_finger1_fk_error),
            "right_finger0_fk_error_distance": right_finger0_fk_error,
            "right_finger1_fk_error_distance": right_finger1_fk_error,
            "right_finger_fk_error_max": max(right_finger0_fk_error, right_finger1_fk_error),
            "finger_opening_right": float(finger_opening_r),
            "finger_opening_left": float(finger_opening_l),
            "d0_contact_telemetry_enabled": bool(self._d0_contact_telemetry_enabled),
            "contact_sensor_present": bool(contact_sensor_present),
            "contact_force_available": bool(contact_force_available),
            "contact_force_norm": contact_force_norm,
            "contact_force_matrix_norm": force_matrix_norm,
            "contact_force_matrix_available": bool(force_matrix_available),
            "contact_force_matrix_vector_persisted": False,
            "contact_time_available": False,
            "contact_points_available": False,
            "contact_normals_available": False,
            "contact_impulses_available": False,
            "friction_forces_available": False,
            "force_matrix_history_available": False,
            "slip_proxy_left": slip_proxy_l,
            "slip_proxy_right": slip_proxy_r,
            "product_credit_authorized": False,
        }
        for prefix, body_idx in (
            ("left_ee", int(world_body_start) + EE_BODY_OFFSET),
            ("left_finger0", int(world_body_start) + FINGER_LOCAL[0]),
            ("left_finger1", int(world_body_start) + FINGER_LOCAL[1]),
            ("right_ee", int(world_body_start) + FRANKA_NUM_JOINTS + EE_BODY_OFFSET),
            ("right_finger0", int(world_body_start) + FRANKA_NUM_JOINTS + FINGER_LOCAL[0]),
            ("right_finger1", int(world_body_start) + FRANKA_NUM_JOINTS + FINGER_LOCAL[1]),
        ):
            q = np.asarray(body_q[body_idx], dtype=np.float32)
            qd = np.asarray(body_qd[body_idx], dtype=np.float32)
            angular_velocity = qd[:3]
            linear_velocity = qd[3:6]
            record[f"{prefix}_xyz"] = q[:3].copy()
            record[f"{prefix}_quat_xyzw"] = q[3:7].copy()
            record[f"{prefix}_angular_velocity"] = angular_velocity.copy()
            record[f"{prefix}_linear_velocity"] = linear_velocity.copy()
            record[f"{prefix}_angular_speed"] = float(np.linalg.norm(angular_velocity))
            record[f"{prefix}_linear_speed"] = float(np.linalg.norm(linear_velocity))
        history = self._s1b_grasp_geometry_telemetry_history[world_idx]
        history.append(record)
        anchor_step = int(self._s1b_telemetry_anchor_step[world_idx])
        if anchor_step < 0:
            del history[:-S1B_GRASP_GEOMETRY_TELEMETRY_PRE_RELEASE_STEPS]
        else:
            window_start = max(0, anchor_step - S1B_GRASP_GEOMETRY_TELEMETRY_PRE_RELEASE_STEPS)
            window_stop = anchor_step + S1B_GRASP_GEOMETRY_TELEMETRY_POST_RELEASE_STEPS
            history[:] = [
                item for item in history
                if window_start <= int(item["step"]) <= window_stop
            ][-S1B_GRASP_GEOMETRY_TELEMETRY_MAX_WINDOW_STEPS:]
        self._s1b_prev_left_cable_point[world_idx] = cable_point_l
        self._s1b_prev_right_cable_point[world_idx] = cable_point_r
        self._s1b_prev_left_gripper[world_idx] = clamp_l_pos
        self._s1b_prev_right_gripper[world_idx] = clamp_r_pos
        self._s1b_prev_geometry_valid[world_idx] = True

    def _s1b_grasp_geometry_telemetry_log_fields(self):
        """Return enabled S1B telemetry fields without changing default-off output."""
        if not self._s1b_grasp_geometry_telemetry_enabled:
            return {}, {}, None
        log = {
            "/metrics/s1b_grasp_geometry_telemetry_enabled": True,
            "/metrics/s1b_grasp_geometry_telemetry_default_off": True,
            "/metrics/s1b_grasp_geometry_telemetry_product_credit_authorized": False,
            "/metrics/s1b_grasp_geometry_telemetry_contact_points_available": False,
            "/metrics/s1b_grasp_geometry_telemetry_contact_normals_available": False,
            "/metrics/s1b_grasp_geometry_telemetry_contact_impulses_available": False,
            "/metrics/s1b_grasp_geometry_telemetry_friction_forces_available": False,
            "/metrics/s1b_grasp_geometry_telemetry_contact_force_available_count": int(
                sum(
                    1
                    for world_history in self._s1b_grasp_geometry_telemetry_history
                    if world_history and bool(world_history[-1].get("contact_force_available", False))
                )
            ),
        }
        log_per_world = {
            "s1b_grasp_geometry_telemetry_enabled": np.full(self._world_count, True, dtype=np.bool_),
            "s1b_observed_release_step": self._s1b_observed_release_step.copy(),
            "s1b_actual_release_event": self._s1b_actual_release_event.copy(),
            "s1b_telemetry_anchor_step": self._s1b_telemetry_anchor_step.copy(),
            "s1b_telemetry_anchor_event": self._s1b_telemetry_anchor_event.copy(),
            "s1b_first_cable_drop_step": self._s1b_first_cable_drop_step.copy(),
            "s1b_first_clamp_loss_step": self._s1b_first_clamp_loss_step.copy(),
            "s1b_first_explosion_step": self._s1b_first_explosion_step.copy(),
            "s1b_d0_contact_telemetry_enabled": np.full(
                self._world_count, bool(self._d0_contact_telemetry_enabled), dtype=np.bool_
            ),
            "s1b_contact_sensor_present": np.full(
                self._world_count, self._d0_contact_sensor is not None, dtype=np.bool_
            ),
            "s1b_contact_force_available": np.asarray(
                [
                    bool(world_history[-1].get("contact_force_available", False))
                    if world_history else False
                    for world_history in self._s1b_grasp_geometry_telemetry_history
                ],
                dtype=np.bool_,
            ),
            "s1b_contact_force_matrix_available": np.asarray(
                [
                    bool(world_history[-1].get("contact_force_matrix_available", False))
                    if world_history else False
                    for world_history in self._s1b_grasp_geometry_telemetry_history
                ],
                dtype=np.bool_,
            ),
            "s1b_contact_points_available": np.full(self._world_count, False, dtype=np.bool_),
            "s1b_contact_normals_available": np.full(self._world_count, False, dtype=np.bool_),
            "s1b_contact_impulses_available": np.full(self._world_count, False, dtype=np.bool_),
            "s1b_friction_forces_available": np.full(self._world_count, False, dtype=np.bool_),
            "s1b_contact_time_available": np.full(self._world_count, False, dtype=np.bool_),
            "s1b_contact_force_matrix_vector_persisted": np.full(self._world_count, False, dtype=np.bool_),
        }
        payload = {
            "schema_version": S1B_GRASP_GEOMETRY_TELEMETRY_SCHEMA_VERSION,
            "default_off": True,
            "product_credit_authorized": False,
            "pre_release_steps": S1B_GRASP_GEOMETRY_TELEMETRY_PRE_RELEASE_STEPS,
            "post_release_steps": S1B_GRASP_GEOMETRY_TELEMETRY_POST_RELEASE_STEPS,
            "max_window_steps": S1B_GRASP_GEOMETRY_TELEMETRY_MAX_WINDOW_STEPS,
            "anchoring": "observed_release_step_else_first_terminal_or_failure",
            "records_by_world": [
                [dict(record) for record in world_history]
                for world_history in self._s1b_grasp_geometry_telemetry_history
            ],
            "unavailable_contact_fields": [
                "contact_points",
                "contact_normals",
                "contact_impulses",
                "friction_forces",
                "force_matrix_history",
                "contact_time",
                "force_matrix_vector_persistence",
            ],
        }
        return log, log_per_world, payload

    def d0_control_source_state(self) -> dict:
        """Return copied D0 control-source metadata for future runner inspection."""
        selected_arm = None if not self._d0_control_arm else self._d0_control_arm
        return {
            "enabled": bool(self._d0_control_enabled),
            "selected_arm": selected_arm,
            "default_off": True,
            "supported_arms": sorted(D0_CONTROL_ARMS - {D0_CONTROL_ARM_NONE}),
            "product_arms": sorted(D0_CONTROL_PRODUCT_ARMS),
            "comparator_arms": sorted(D0_CONTROL_COMPARATOR_ARMS),
            "product_success_credit_authorized": False,
            "d0_execution_authorized": False,
            "gpu_or_sim_authorized": False,
            "task_config_mutation_authorized": False,
            "human_rs_predicate_confirmation_required_before_strategic_routing": True,
            "human_rs_predicate_confirmed": bool(self._d0_human_rs_predicate_confirmed),
            "autonomous_post_release_hold_required": True,
            "continuous_hold_classification": (
                "DESCOPE_OR_COMPARATOR_ONLY_NOT_PRODUCT_SUCCESS_UNDER_ORIGINAL_PREDICATE"
            ),
            "force_scale": float(self._d0_control_force_scale),
            "force_scale_min": float(self._d0_control_force_scale_min),
            "release_step": int(self._d0_control_release_step),
            "target_blend": float(self._d0_control_target_blend),
            "left_target_offset_xyz": self._d0_control_left_target_offset.copy(),
            "force_scale_per_world": self._d0_control_force_scale_per_world.copy(),
            "target_blend_applied": self._d0_control_target_blend_applied.copy(),
            "refusal_reason": self._d0_control_refusal_reason,
            "allowed_source_surfaces": [
                "_apply_actions_batch",
                "_solve_ik_batch",
                "_apply_left_finger_spring",
                "d0_contact_telemetry_state",
                "d0_control_source_state",
            ],
            "no_crutch_constraints": {
                "_apply_kinematic_left_finger_pin": False,
                "_activate_kinematic_left_finger_support": False,
                "KINEMATIC_INV_MASS": False,
                "inv_mass_zeroing": False,
                "write_joint_state_to_sim_in_control_loop": False,
                "fixture_pinning": False,
                "teleport_or_direct_state_reset": False,
                "hidden_support": False,
                "hold_to_completion_as_product_success": False,
                "active_at_completion_as_product_success": False,
            },
        }

    def _d0_control_source_log_fields(self):
        """Return optional D0 control-source log fields without affecting disabled output."""
        if not self._d0_control_enabled:
            return {}, {}
        log = {
            "/metrics/d0_control_enabled": True,
            "/metrics/d0_control_default_off": True,
            "/metrics/d0_control_selected_arm": self._d0_control_arm,
            "/metrics/d0_control_product_success_credit_authorized": False,
            "/metrics/d0_control_human_rs_predicate_confirmed": bool(
                self._d0_human_rs_predicate_confirmed
            ),
            "/metrics/d0_control_force_scale_mean": float(
                np.mean(self._d0_control_force_scale_per_world)
            ),
            "/metrics/d0_control_target_blend_applied_count": int(
                np.sum(self._d0_control_target_blend_applied)
            ),
        }
        log_per_world = {
            "d0_control_enabled": np.full(self._world_count, True, dtype=np.bool_),
            "d0_control_selected_arm": np.full(self._world_count, self._d0_control_arm, dtype="<U48"),
            "d0_control_force_scale": self._d0_control_force_scale_per_world.copy(),
            "d0_control_target_blend_applied": self._d0_control_target_blend_applied.copy(),
            "d0_control_product_success_credit_authorized": np.full(
                self._world_count,
                False,
                dtype=np.bool_,
            ),
        }
        return log, log_per_world

    def _d0_control_adjust_left_target(self, world_idx, target_l):
        """Apply opt-in D0 left-target blend without changing default behavior."""
        if not self._d0_control_enabled or self._d0_control_arm not in D0_CONTROL_PRODUCT_ARMS:
            return target_l
        if self._d0_control_arm == D0_CONTROL_ARM_SUPPORT_REMOVAL_ABLATION:
            self._d0_control_target_blend_applied[world_idx] = False
            return target_l
        if self._d0_control_target_blend <= 0.0:
            self._d0_control_target_blend_applied[world_idx] = False
            return target_l
        self._d0_control_target_blend_applied[world_idx] = True
        return target_l + self._d0_control_left_target_offset * self._d0_control_target_blend

    def _d0_control_force_scale_for_world(self, world_idx):
        """Return opt-in D0 force scale for real spring effort surfaces only."""
        if not self._d0_control_enabled or self._d0_control_arm in D0_CONTROL_COMPARATOR_ARMS:
            return 1.0
        step = int(self.episode_length_buf[world_idx].item())
        if step < self._d0_control_release_step:
            scale = self._d0_control_force_scale
        elif self._d0_control_arm == D0_CONTROL_ARM_SUPPORT_REMOVAL_ABLATION:
            scale = self._d0_control_force_scale_min
        elif self._d0_control_arm in (D0_CONTROL_ARM_RELEASE_RAMP_5, D0_CONTROL_ARM_RELEASE_RAMP_10):
            horizon = 5 if self._d0_control_arm == D0_CONTROL_ARM_RELEASE_RAMP_5 else 10
            progress = min(max((step - self._d0_control_release_step + 1) / horizon, 0.0), 1.0)
            scale = self._d0_control_force_scale - (
                self._d0_control_force_scale - self._d0_control_force_scale_min
            ) * progress
        else:
            scale = self._d0_control_force_scale
        self._d0_control_force_scale_per_world[world_idx] = float(scale)
        return float(scale)

    def _s1a_post_release_phase_for_world(self, world_idx):
        """Return diagnostic post-release phase for opt-in S1A metadata."""
        if not self._d0_control_enabled or self._d0_control_arm not in D0_CONTROL_PRODUCT_ARMS:
            return 0.0
        step = int(self.episode_length_buf[int(world_idx)].item())
        return float(step >= self._d0_control_release_step)

    def _s1a_cable_drop_margin(self, world_idx, cable_pos):
        """Return left-hold cable-drop margin [m] for S1A diagnostics."""
        l_excl = np.setdiff1d(self._target_seg_indices_l[world_idx], self._target_seg_indices_r[world_idx])
        cable_z_min = float(cable_pos[l_excl, 2].min()) if len(l_excl) > 0 else 999.0
        return cable_z_min - self.CABLE_DROP_Z_THRESH

    def _s1a_observation_extension(
        self,
        world_idx,
        *,
        terminal_candidate,
        terminal_hold_len,
        cable_drop_margin,
        dist_pos_raw,
        dist_pos_l_raw,
    ):
        """Return the opt-in S1A observation extension for one world."""
        hold_norm = min(max(float(terminal_hold_len) / float(self.C5_SUSTAIN_STEPS), 0.0), 1.0)
        drop_margin_norm = min(max(cable_drop_margin / 0.05, -1.0), 1.0)
        explosion_margin_right = min(
            max((self.EXPLOSION_DIST_THRESH - dist_pos_raw) / self.EXPLOSION_DIST_THRESH, -1.0),
            1.0,
        )
        explosion_margin_left = min(
            max((self.EXPLOSION_DIST_THRESH - dist_pos_l_raw) / self.EXPLOSION_DIST_THRESH, -1.0),
            1.0,
        )
        if terminal_hold_len >= self.C5_SUSTAIN_STEPS:
            readiness_stage = 1.0
        elif terminal_candidate:
            readiness_stage = max(0.5, hold_norm)
        else:
            readiness_stage = 0.0
        return [
            float(bool(terminal_candidate)),
            hold_norm,
            drop_margin_norm,
            explosion_margin_right,
            explosion_margin_left,
            readiness_stage,
            self._s1a_post_release_phase_for_world(world_idx),
        ]

    def _s1a_reward_value(
        self,
        *,
        terminal_candidate,
        previous_terminal_hold,
        terminal_hold_len,
        cable_drop_margin,
        dist_pos_raw,
        dist_pos_l_raw,
        explosion,
        cable_terminated,
        post_release_phase,
    ):
        """Return bounded opt-in S1A reward shaping without product credit."""
        if not self._s1a_reward_enabled:
            return 0.0
        if not post_release_phase:
            return 0.0
        if explosion or cable_terminated:
            return 0.0

        reward = 0.0
        if terminal_candidate and previous_terminal_hold == 0:
            reward += 1.0
        if terminal_candidate and terminal_hold_len <= self.C5_SUSTAIN_STEPS:
            reward += 0.2

        if cable_drop_margin < 0.05:
            reward -= min((0.05 - cable_drop_margin) / 0.05, 1.0)
        explosion_margin = min(
            self.EXPLOSION_DIST_THRESH - dist_pos_raw,
            self.EXPLOSION_DIST_THRESH - dist_pos_l_raw,
        )
        if explosion_margin < 0.20:
            reward -= 0.5 * min((0.20 - explosion_margin) / 0.20, 1.0)
        return float(reward)

    def _s1a_curriculum_log_fields(
        self,
        *,
        reward_values,
        terminal_candidate,
        readiness_stage,
        cable_drop_margin,
        explosion_margin_right,
        explosion_margin_left,
        post_release_phase,
    ):
        """Return optional S1A metadata logs without affecting disabled output."""
        if not self._s1a_curriculum_metadata_enabled:
            return {}, {}
        log = {
            "/metrics/s1a_enabled": bool(self._s1a_any_enabled),
            "/metrics/s1a_reward_enabled": bool(self._s1a_reward_enabled),
            "/metrics/s1a_observation_enabled": bool(self._s1a_observation_enabled),
            "/metrics/s1a_curriculum_metadata_enabled": True,
            "/metrics/s1a_obs_schema_version": int(S1A_OBS_SCHEMA_VERSION),
            "/metrics/s1a_reward_mean": float(np.mean(reward_values)),
            "/metrics/s1a_terminal_candidate_count": int(np.sum(terminal_candidate)),
            "/metrics/s1a_readiness_stage_mean": float(np.mean(readiness_stage)),
            "/metrics/s1a_post_release_phase_count": int(np.sum(post_release_phase > 0.0)),
            "/metrics/s1a_product_success_credit_authorized": False,
            "/metrics/s1a_product_scoring_authorized": False,
            "/metrics/s1a_no_crutch_required": True,
        }
        log_per_world = {
            "s1a_enabled": np.full(self._world_count, bool(self._s1a_any_enabled), dtype=np.bool_),
            "s1a_reward_enabled": np.full(self._world_count, bool(self._s1a_reward_enabled), dtype=np.bool_),
            "s1a_observation_enabled": np.full(self._world_count, bool(self._s1a_observation_enabled), dtype=np.bool_),
            "s1a_obs_schema_version": np.full(self._world_count, int(S1A_OBS_SCHEMA_VERSION), dtype=np.int32),
            "s1a_reward": reward_values.copy(),
            "s1a_terminal_candidate": terminal_candidate.copy(),
            "s1a_release_readiness_stage": readiness_stage.copy(),
            "s1a_cable_drop_margin": cable_drop_margin.copy(),
            "s1a_explosion_margin_right": explosion_margin_right.copy(),
            "s1a_explosion_margin_left": explosion_margin_left.copy(),
            "s1a_post_release_phase": post_release_phase.copy(),
            "s1a_product_success_credit_authorized": np.full(self._world_count, False, dtype=np.bool_),
            "s1a_product_scoring_authorized": np.full(self._world_count, False, dtype=np.bool_),
            "s1a_active_at_completion_credit_authorized": np.full(self._world_count, False, dtype=np.bool_),
            "s1a_hold_to_completion_credit_authorized": np.full(self._world_count, False, dtype=np.bool_),
            "s1a_sim_only_crutch_credit_authorized": np.full(self._world_count, False, dtype=np.bool_),
        }
        return log, log_per_world

    def _build_model(self):
        """Build FK model + multi-world physics scene (using shared utilities)."""
        print("[AerialRegraspEnv] Building FK model...")
        self._fk_model, self._fk_state, fk_jq = build_fk_and_init(
            left_finger_pos=FINGER_OPEN_POS,
            right_finger_pos=FINGER_OPEN_POS,
            device=self.device,
        )

        # Per-world FK joint state storage
        self._per_world_fk_jq = np.tile(fk_jq, (self._world_count, 1))

        # Build multi-world physics scene (support clips match builder)
        print(f"[AerialRegraspEnv] Building scene ({self._world_count} worlds)...")
        scene = build_multiworld_scene(
            self._fk_model,
            self._fk_state,
            self._world_count,
            self.device,
            add_support_clips=True,
        )

        # Unpack scene dict to instance variables
        self._model = scene["model"]
        self._solver = scene["solver"]
        self._state_0 = scene["state_0"]
        self._state_1 = scene["state_1"]
        self._control = scene["control"]
        self._contacts = scene["contacts"]
        self._bws = scene["bws"]
        self._cable_bodies = scene["cable_bodies"]
        self._cable_bodies_per_world = scene["cable_bodies_per_world"]
        self._cable_body_offset = scene["cable_body_offset"]
        self._bodies_per_world = scene["bodies_per_world"]

        # Joint world start (for Dahl friction reset)
        self._jws = self._model.joint_world_start.numpy()

        print(f"[AerialRegraspEnv] Model: {self._model.body_count} bodies, {self._model.joint_count} joints")

    # =========================================================================
    # Cache Management
    # =========================================================================

    def _cache_path(self):
        # === Phase 4 #2 behavioral: honor cache_path_override if provided ===
        if self._cache_path_override is not None:
            return self._cache_path_override
        # === END Phase 4 #2 behavioral cache_path override ===
        return os.path.join(self.CACHE_DIR, f"aerial_regrasp_w{self._world_count}_p0_{self.CACHE_VERSION}.npz")

    def _load_and_restore_cache(self):
        """Load and restore precondition cache. Returns True if successful."""
        path = self._cache_path()
        if not os.path.exists(path):
            print(f"[AerialRegraspEnv] No cache at {path}")
            return False

        try:
            data = np.load(path)
            if int(data["world_count"][0]) != self._world_count:
                print(
                    f"[AerialRegraspEnv] Cache world_count mismatch: "
                    f"cache={data['world_count'][0]}, current={self._world_count}"
                )
                return False
            if int(data["body_count"][0]) != self._model.body_count:
                print(
                    f"[AerialRegraspEnv] Cache body_count mismatch: "
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
            print(f"[AerialRegraspEnv] Loaded cache from {path}")
        except Exception as e:
            print(f"[AerialRegraspEnv] Cache load failed: {e}")
            return False

        # Restore physics state
        self._state_0.body_q.assign(self._settled_body_q)
        self._state_0.body_qd.assign(self._settled_body_qd)

        # Restore inv_mass/inv_inertia — left finger bodies made dynamic for grip
        inv_mass = self._settled_inv_mass.copy()
        inv_inertia = self._settled_inv_inertia.copy()
        self._left_finger_physics_ids = []
        for w in range(self._world_count):
            ws = self._bws[w]
            for lf in FINGER_LOCAL:
                bi = ws + lf
                inv_mass[bi] = FINGER_DYNAMIC_INV_MASS
                inv_inertia[bi] = np.full(3, FINGER_DYNAMIC_INV_INERTIA, dtype=np.float32)
                self._left_finger_physics_ids.append(bi)
        self._model.body_inv_mass = wp.array(inv_mass, dtype=self._model.body_inv_mass.dtype, device=self.device)
        self._model.body_inv_inertia = wp.array(
            inv_inertia, dtype=self._model.body_inv_inertia.dtype, device=self.device
        )
        self._left_finger_set = set(self._left_finger_physics_ids)
        self._left_finger_dynamic_inv_mass = self._model.body_inv_mass.numpy().copy()
        self._left_finger_dynamic_inv_inertia = self._model.body_inv_inertia.numpy().copy()
        self._left_finger_inv_mass = self._left_finger_dynamic_inv_mass.copy()
        self._left_finger_inv_inertia = self._left_finger_dynamic_inv_inertia.copy()
        print(
            f"[AerialRegraspEnv] Dynamic left fingers: {len(self._left_finger_physics_ids)} bodies "
            f"(inv_mass={FINGER_DYNAMIC_INV_MASS}, spring k={FINGER_SPRING_KE})"
        )

        # Restore FK state (left fingers CLOSED from cache)
        self._fk_state.joint_q.assign(self._settled_fk_jq)
        newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)

        # Restore per-world FK
        for w in range(self._world_count):
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()

        # Sync kinematic bodies to physics
        fk_bq = self._fk_state.body_q.numpy()[:ROBOT_BODY_COUNT]
        phys_bq = self._state_0.body_q.numpy()
        for w in range(self._world_count):
            start = self._bws[w]
            phys_bq[start : start + ROBOT_BODY_COUNT] = fk_bq
        self._state_0.body_q.assign(phys_bq)

        # Restore VBD solver prev state (prevents velocity explosion)
        self._solver.body_q_prev.assign(self._settled_body_q)

        # Reset Dahl friction state
        if hasattr(self._solver, "enable_dahl_friction") and self._solver.enable_dahl_friction:
            if self._solver.joint_C_fric is not None:
                self._solver.joint_C_fric.zero_()
            if self._solver.joint_sigma_prev is not None:
                self._solver.joint_sigma_prev.zero_()

        # Compute target seg indices
        bq = self._settled_body_q
        self._target_seg_indices_r, self._target_seg_indices_l = self._compute_target_seg_indices(bq)

        # Cache settled EE poses from FK (used by _reset_worlds)
        wp.synchronize()
        fk_bq_full = self._fk_state.body_q.numpy()
        self._settled_ee_r_pos = fk_bq_full[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3].copy()
        self._settled_ee_r_quat = fk_bq_full[FRANKA_NUM_JOINTS + EE_BODY_OFFSET][3:7].copy()
        self._settled_ee_l_pos = fk_bq_full[EE_BODY_OFFSET][:3].copy()
        self._settled_ee_l_quat = fk_bq_full[EE_BODY_OFFSET][3:7].copy()
        # Guard: freeze_left_anchor Z-clamp in per-world loop clips to [LIFT_Z±0.05]; settled Z must lie within.
        assert abs(self._settled_ee_l_pos[2] - LIFT_Z) < 0.05, (
            f"settled_ee_l_pos Z={self._settled_ee_l_pos[2]:.4f} outside [LIFT_Z±0.05]=[{LIFT_Z-0.05:.4f},{LIFT_Z+0.05:.4f}]; "
            "freeze_left_anchor would silently clip the frozen target"
        )

        # Init per-world EE targets from settled poses
        for w in range(self._world_count):
            self._ee_target_right[w] = self._settled_ee_r_pos.copy()
            self._ee_target_left[w] = self._settled_ee_l_pos.copy()
            self._ee_quat_right[w] = self._settled_ee_r_quat.copy()
            self._ee_quat_left[w] = self._settled_ee_l_quat.copy()

        # Pre-compute settled cable target positions for EMA initialization at reset
        # (C1 fix: prevents stale EMA from previous episode corrupting first-step reward)
        self._settled_seg_pos_r = np.zeros((self._world_count, 3), dtype=np.float32)
        self._settled_seg_pos_l = np.zeros((self._world_count, 3), dtype=np.float32)
        self._settled_seg_quat_r = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (self._world_count, 1))
        self._settled_seg_quat_l = np.tile(np.array([0, 0, 0, 1], dtype=np.float32), (self._world_count, 1))
        for w in range(self._world_count):
            cable_pos_w = bq[self._cable_bodies[w], :3]
            clamp_r = compute_clamp_pos(self._settled_ee_r_pos, self._settled_ee_r_quat)
            clamp_l = compute_clamp_pos(self._settled_ee_l_pos, self._settled_ee_l_quat)
            seg_pos_r, seg_tangent_r, _ = find_nearest_cable_point(cable_pos_w, clamp_r, self._target_seg_indices_r[w])
            seg_pos_l, seg_tangent_l, _ = find_nearest_cable_point(cable_pos_w, clamp_l, self._target_seg_indices_l[w])
            self._settled_seg_pos_r[w] = seg_pos_r
            self._settled_seg_pos_l[w] = seg_pos_l
            self._settled_seg_quat_r[w] = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_r))
            self._settled_seg_quat_l[w] = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_l))

        print(
            f"[AerialRegraspEnv] Restored from cache: "
            f"L_EE={self._left_ee_hold}, R_EE={self._right_ee_start}, "
            f"target_seg_r={self._target_seg_indices_r[0]}, "
            f"target_seg_l={self._target_seg_indices_l[0]}"
        )
        return True

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

    # =========================================================================
    # R2-A Track A Kinematic Left-Finger Support Predicate
    # =========================================================================

    def _left_finger_ids_for_world(self, world_idx: int) -> list[int]:
        """Return physics body ids for the left finger bodies in one world."""
        ws = self._bws[int(world_idx)]
        return [int(ws + lf) for lf in FINGER_LOCAL]

    def _assign_left_finger_inverse_mass(self):
        """Push cached left-finger inverse-mass arrays to the Newton model."""
        if self._left_finger_inv_mass is None or self._left_finger_inv_inertia is None:
            return
        self._model.body_inv_mass = wp.array(
            self._left_finger_inv_mass, dtype=self._model.body_inv_mass.dtype, device=self.device
        )
        self._model.body_inv_inertia = wp.array(
            self._left_finger_inv_inertia, dtype=self._model.body_inv_inertia.dtype, device=self.device
        )

    def _activate_kinematic_left_finger_support(self, env_ids, *, bq=None, bqd=None, prev=None, fk_batch_bq=None):
        """Activate opt-in kinematic support for reset worlds."""
        if not self._kinematic_left_finger_support_enabled:
            return
        env_ids = [int(w) for w in env_ids]
        if not env_ids:
            return
        owns_state = bq is None or bqd is None or prev is None
        if owns_state:
            bq = self._state_0.body_q.numpy()
            bqd = self._state_0.body_qd.numpy()
            prev = self._solver.body_q_prev.numpy()

        for w in env_ids:
            self._kinematic_support_active[w] = True
            self._kinematic_release_step[w] = -1
            self._kinematic_release_reason[w] = "pending_release"
            self._kinematic_release_ready_count[w] = 0
            self._kinematic_post_release_steps[w] = -1
            self._kinematic_release_ready_reason[w] = "not_ready"
            self._kinematic_released_after_success[w] = False
            self._kinematic_release_terminal_hold_len[w] = 0
            self._kinematic_release_right_clamp[w] = False
            self._kinematic_release_left_hold[w] = False
            self._kinematic_release_cable_not_dropped[w] = False
            for lf, bi in zip(FINGER_LOCAL, self._left_finger_ids_for_world(w)):
                self._left_finger_inv_mass[bi] = KINEMATIC_INV_MASS
                self._left_finger_inv_inertia[bi] = np.full(3, KINEMATIC_INV_INERTIA, dtype=np.float32)
                if fk_batch_bq is not None:
                    bq[bi] = fk_batch_bq[w, lf]
                bqd[bi] = 0.0
                prev[bi] = bq[bi]

        self._assign_left_finger_inverse_mass()
        if owns_state:
            self._state_0.body_q.assign(bq)
            self._state_0.body_qd.assign(bqd)
            self._solver.body_q_prev.assign(prev)

    def _release_kinematic_left_finger_support_for_world(
        self,
        world_idx: int,
        step: int,
        reason: str,
        *,
        after_success: bool = False,
        terminal_hold_len: int | None = None,
        right_clamp: bool | None = None,
        left_hold: bool | None = None,
        cable_not_dropped: bool | None = None,
        ready_reason: str | None = None,
    ):
        """Release kinematic support for one world and restore dynamic finger bodies."""
        if not self._kinematic_left_finger_support_enabled:
            return
        w = int(world_idx)
        if not self._kinematic_support_active[w]:
            return

        ids = self._left_finger_ids_for_world(w)
        self._kinematic_support_active[w] = False
        self._kinematic_release_step[w] = int(step)
        self._kinematic_release_reason[w] = str(reason)
        self._kinematic_post_release_steps[w] = 0
        self._kinematic_released_after_success[w] = bool(after_success)
        if terminal_hold_len is not None:
            self._kinematic_release_terminal_hold_len[w] = int(terminal_hold_len)
        if right_clamp is not None:
            self._kinematic_release_right_clamp[w] = bool(right_clamp)
        if left_hold is not None:
            self._kinematic_release_left_hold[w] = bool(left_hold)
        if cable_not_dropped is not None:
            self._kinematic_release_cable_not_dropped[w] = bool(cable_not_dropped)
        if ready_reason is not None:
            self._kinematic_release_ready_reason[w] = str(ready_reason)
        self._left_finger_inv_mass[ids] = self._left_finger_dynamic_inv_mass[ids]
        self._left_finger_inv_inertia[ids] = self._left_finger_dynamic_inv_inertia[ids]
        self._assign_left_finger_inverse_mass()

        bq = self._state_0.body_q.numpy()
        bqd = self._state_0.body_qd.numpy()
        prev = self._solver.body_q_prev.numpy()
        bqd[ids] = 0.0
        prev[ids] = bq[ids]
        self._state_0.body_qd.assign(bqd)
        self._solver.body_q_prev.assign(prev)

    def _release_kinematic_left_finger_support(self, env_ids, *, reason: str):
        """Release active worlds using the current episode step as metadata."""
        for w in [int(env_id) for env_id in env_ids]:
            self._release_kinematic_left_finger_support_for_world(
                w, int(self.episode_length_buf[w].item()), reason
            )

    def _update_kinematic_left_finger_support_release(self):
        """Release active worlds for step-count gates and maintain post-release age."""
        if not self._kinematic_left_finger_support_enabled:
            return
        released = (~self._kinematic_support_active) & (self._kinematic_release_step >= 0)
        self._kinematic_post_release_steps[released] += 1
        if not self._kinematic_support_active.any():
            return
        active_worlds = np.where(self._kinematic_support_active)[0]
        for w in active_worlds:
            step = int(self.episode_length_buf[int(w)].item())
            if self._kinematic_left_finger_support_gate_type == KINEMATIC_GATE_STEP_COUNT:
                if step >= self._kinematic_left_finger_support_hold_steps:
                    self._release_kinematic_left_finger_support_for_world(int(w), step, "step_count_gate")
            elif step >= self._kinematic_max_hold_steps:
                self._release_kinematic_left_finger_support_for_world(
                    int(w), step, "max_hold_guard"
                )

    def _update_kinematic_left_finger_support_readiness(
        self,
        world_idx: int,
        *,
        success: bool,
        right_clamp: bool,
        left_hold: bool,
        cable_not_dropped: bool,
        explosion: bool,
        cable_terminated: bool,
        terminal_end_reason: str,
        terminal_hold_len: int,
    ):
        """Update readiness-gated release state for one world."""
        if (
            not self._kinematic_left_finger_support_enabled
            or self._kinematic_left_finger_support_gate_type
            != KINEMATIC_GATE_RELEASE_AFTER_SUCCESS_HOLD_K
        ):
            return
        w = int(world_idx)
        if not self._kinematic_support_active[w]:
            return

        ready = (
            bool(right_clamp)
            and bool(left_hold)
            and bool(cable_not_dropped)
            and not bool(explosion)
            and not bool(cable_terminated)
        )
        if ready:
            self._kinematic_release_ready_count[w] += 1
            self._kinematic_release_ready_reason[w] = "ready"
        else:
            self._kinematic_release_ready_count[w] = 0
            self._kinematic_release_ready_reason[w] = "not_ready"
            return

        success_ready = (
            bool(success)
            and terminal_end_reason == "success"
            and self._kinematic_release_ready_count[w]
            >= self._kinematic_release_success_hold_steps
            and self._kinematic_release_ready_count[w]
            >= self._kinematic_release_stability_steps
        )
        if success_ready:
            self._release_kinematic_left_finger_support_for_world(
                w,
                int(self.episode_length_buf[w].item()),
                "success_stability_gate",
                after_success=True,
                terminal_hold_len=terminal_hold_len,
                right_clamp=right_clamp,
                left_hold=left_hold,
                cable_not_dropped=cable_not_dropped,
                ready_reason="success_stability_ready",
            )

    def _apply_kinematic_left_finger_pin(self, fk_batch_bq=None, n_worlds=None):
        """Pin active left finger bodies to FK pose and sync VBD previous state."""
        if not self._kinematic_left_finger_support_enabled or not self._kinematic_support_active.any():
            return
        n_worlds = self._world_count if n_worlds is None else int(n_worlds)
        bq = self._state_0.body_q.numpy()
        bqd = self._state_0.body_qd.numpy()
        prev = self._solver.body_q_prev.numpy()
        for w in np.where(self._kinematic_support_active[:n_worlds])[0]:
            for lf, bi in zip(FINGER_LOCAL, self._left_finger_ids_for_world(int(w))):
                if fk_batch_bq is not None:
                    bq[bi] = fk_batch_bq[int(w), lf]
                bqd[bi] = 0.0
                prev[bi] = bq[bi]
        self._state_0.body_q.assign(bq)
        self._state_0.body_qd.assign(bqd)
        self._solver.body_q_prev.assign(prev)

    def kinematic_left_finger_support_state(self) -> dict:
        """Return copied read-only state for the kinematic support predicate."""
        release_steps = [
            None if int(step) < 0 else int(step)
            for step in self._kinematic_release_step.copy().tolist()
        ]
        ids = list(getattr(self, "_left_finger_physics_ids", []))
        dynamic_inv_mass = (
            [float(self._left_finger_dynamic_inv_mass[bi]) for bi in ids]
            if self._left_finger_dynamic_inv_mass is not None
            else []
        )
        dynamic_inv_inertia = (
            [self._left_finger_dynamic_inv_inertia[bi].copy().tolist() for bi in ids]
            if self._left_finger_dynamic_inv_inertia is not None
            else []
        )
        return {
            "enabled": bool(self._kinematic_left_finger_support_enabled),
            "gate_type": str(self._kinematic_left_finger_support_gate_type),
            "hold_steps": int(self._kinematic_left_finger_support_hold_steps),
            "release_success_hold_steps": int(self._kinematic_release_success_hold_steps),
            "release_stability_steps": int(self._kinematic_release_stability_steps),
            "max_hold_steps": int(self._kinematic_max_hold_steps),
            "active": self._kinematic_support_active.copy().tolist(),
            "release_step": release_steps,
            "release_reason": self._kinematic_release_reason.copy().tolist(),
            "release_ready_count": self._kinematic_release_ready_count.copy().tolist(),
            "post_release_steps": self._kinematic_post_release_steps.copy().tolist(),
            "release_ready_reason": self._kinematic_release_ready_reason.copy().tolist(),
            "released_after_success": self._kinematic_released_after_success.copy().tolist(),
            "release_terminal_hold_len": self._kinematic_release_terminal_hold_len.copy().tolist(),
            "release_right_clamp": self._kinematic_release_right_clamp.copy().tolist(),
            "release_left_hold": self._kinematic_release_left_hold.copy().tolist(),
            "release_cable_not_dropped": self._kinematic_release_cable_not_dropped.copy().tolist(),
            "active_count": int(np.sum(self._kinematic_support_active)),
            "dynamic_inv_mass": dynamic_inv_mass,
            "dynamic_inv_inertia": dynamic_inv_inertia,
            "kinematic_inv_mass": float(KINEMATIC_INV_MASS),
            "kinematic_inv_inertia": float(KINEMATIC_INV_INERTIA),
        }

    # =========================================================================
    # Reset
    # =========================================================================

    def _reset_worlds(self, env_ids):
        """Reset specific worlds to precondition state."""
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

            # Reset FK state for this world
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()

            self._step_completed_right[w] = False
            self._success_sustain_count[w] = 0
            self._terminal_entered[w] = False
            self._terminal_hold_len[w] = 0
            self._terminal_break_reason[w] = "unspecified"
            # === A5 Phase 4 #2: reset hold-detection signal counters ===
            self._prev_terminal_candidate[w] = False
            self._hold_signal_event_this_step[w] = 0
            self._hold_signal_acquired_count[w] = 0
            self._hold_signal_lost_count[w] = 0
            self._hold_signal_k5_sustained_count[w] = 0
            # === END A5 Phase 4 #2 ===
            # === B-A5.2 Phase 4 #2 behavioral: reset hold-break counters ===
            self._hold_break_count[w] = 0
            self._hold_break_terminated[w] = False
            # === END B-A5.2 Phase 4 #2 behavioral ===
            # === B-A3.1 Phase 4 #2 behavioral: reset R-clamp + L-hold counterfactual counters ===
            self._success_right_clamp_left_hold_sustain_count[w] = 0
            self._success_right_clamp_left_hold[w] = False
            # === END B-A3.1 Phase 4 #2 behavioral ===
            self._drop_grace[w] = 0
            if self._d0_control_enabled:
                self._d0_control_force_scale_per_world[w] = 1.0
                self._d0_control_target_blend_applied[w] = False
            self._reset_s1b_grasp_geometry_telemetry_world(w)

            # Reset EE targets from settled poses
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

            # Reset cable jitter tracking
            self._prev_seg_pos_raw_r[w] = np.zeros(3, dtype=np.float32)
            self._prev_seg_pos_raw_valid[w] = False

            # Reset temporal quaternion consistency state (Bug #2)
            self._prev_clamp_r_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_clamp_l_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_seg_r_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_seg_l_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)
            # C1 fix: initialize EMA from settled cable positions (not stale previous episode)
            # Bug #4 compatible: _ema_initialized=True so obs skips re-init
            self._ema_initialized[w] = True
            self._ema_seg_pos_r[w] = self._settled_seg_pos_r[w].copy()
            self._ema_seg_pos_l[w] = self._settled_seg_pos_l[w].copy()
            self._ema_seg_quat_r[w] = self._settled_seg_quat_r[w].copy()
            self._ema_seg_quat_l[w] = self._settled_seg_quat_l[w].copy()

            # C2 fix: noise applied to IK target only (not body_q directly).
            # Body_q noise was immediately overwritten by FK on first substep.
            # IK target noise lets the first IK solve naturally move to the perturbed position.
            if self.INIT_XY_NOISE > 0:
                noise_xy = np.random.uniform(-self.INIT_XY_NOISE, self.INIT_XY_NOISE, size=2)
                self._ee_target_right[w][0] += noise_xy[0]
                self._ee_target_right[w][1] += noise_xy[1]

            self.episode_length_buf[w] = 0

        if self._kinematic_left_finger_support_enabled:
            self._activate_kinematic_left_finger_support(env_ids, bq=bq, bqd=bqd, prev=prev)

        assign_world_states_to_sim(self._state_0, self._solver, bq, bqd, prev)

        # Reset Dahl friction for reset worlds
        reset_dahl_friction_for_envs(self._solver, self._jws, env_ids)

        self._episode_count += len(env_ids)

    # =========================================================================
    # Observation
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

            # Finger openings
            fk_jq = self._per_world_fk_jq[w]
            r_finger_opening = (
                fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]]
                + fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]]
            )
            l_finger_opening = fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] + fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]]

            # Target cable point: interpolated nearest on piecewise-linear cable
            cable_bq = bq[self._cable_bodies[w]]
            cable_pos = cable_bq[:, :3]
            seg_pos_raw, seg_tangent, _ = find_nearest_cable_point(
                cable_pos, clamp_r_pos, self._target_seg_indices_r[w]
            )
            # Bug #4 fix: EMA smoothing for aerial cable target (pos + quat, obs only)
            if not self._ema_initialized[w]:
                self._ema_seg_pos_r[w] = seg_pos_raw
                # Init quat EMA from first observation
                q0_r = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent))
                self._ema_seg_quat_r[w] = q0_r.copy()
                # NOTE: left arm EMA init deferred to after left cable point computation (below)
                self._ema_initialized[w] = True
                _need_left_ema_init = True
            else:
                _need_left_ema_init = False
            a = self.TARGET_EMA_ALPHA
            seg_pos = a * seg_pos_raw + (1 - a) * self._ema_seg_pos_r[w]
            self._ema_seg_pos_r[w] = seg_pos.copy()
            seg_quat = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent))
            seg_quat = temporal_quat_consistency(seg_quat, self._prev_seg_r_quat[w])
            self._prev_seg_r_quat[w] = seg_quat.copy()
            # Quat EMA (NLERP): smooth seg_quat in obs space
            if np.dot(seg_quat, self._ema_seg_quat_r[w]) < 0:
                seg_quat_for_lerp = -seg_quat
            else:
                seg_quat_for_lerp = seg_quat
            seg_quat = a * seg_quat_for_lerp + (1 - a) * self._ema_seg_quat_r[w]
            seg_quat = seg_quat / (np.linalg.norm(seg_quat) + 1e-8)
            self._ema_seg_quat_r[w] = seg_quat.copy()

            # Left arm: independent nearest cable point
            seg_pos_l_raw, seg_tangent_l, _ = find_nearest_cable_point(
                cable_pos, clamp_l_pos, self._target_seg_indices_l[w]
            )
            # Bug hunt fix: init left EMA from left arm's cable point, not right arm's
            if _need_left_ema_init:
                self._ema_seg_pos_l[w] = seg_pos_l_raw
            seg_pos_l = a * seg_pos_l_raw + (1 - a) * self._ema_seg_pos_l[w]
            self._ema_seg_pos_l[w] = seg_pos_l.copy()
            grasp_target_quat_l = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_l))
            grasp_target_quat_l = temporal_quat_consistency(grasp_target_quat_l, self._prev_seg_l_quat[w])
            self._prev_seg_l_quat[w] = grasp_target_quat_l.copy()
            # R2 fix: use flag-based init (consistent with right arm), not fragile np.allclose
            if _need_left_ema_init:
                self._ema_seg_quat_l[w] = grasp_target_quat_l.copy()
            # Quat EMA for left arm
            if np.dot(grasp_target_quat_l, self._ema_seg_quat_l[w]) < 0:
                qt_l_for_lerp = -grasp_target_quat_l
            else:
                qt_l_for_lerp = grasp_target_quat_l
            grasp_target_quat_l = a * qt_l_for_lerp + (1 - a) * self._ema_seg_quat_l[w]
            grasp_target_quat_l = grasp_target_quat_l / (np.linalg.norm(grasp_target_quat_l) + 1e-8)
            self._ema_seg_quat_l[w] = grasp_target_quat_l.copy()

            # Clip pose (constant)
            clip_pos = self.CLIP1_POS
            clip_quat = self.CLIP1_QUAT_XYZW

            # Orientation error: axis-angle from hand to grasp target
            ori_error_aa = compute_ori_error_axis_angle(clamp_r_quat, seg_quat)
            pos_error = clamp_r_pos - seg_pos

            # Left arm error signals
            ori_error_aa_l = compute_ori_error_axis_angle(clamp_l_quat, grasp_target_quat_l)
            pos_error_l = clamp_l_pos - seg_pos_l

            row = [
                clamp_r_pos[0],
                clamp_r_pos[1],
                clamp_r_pos[2],
                clamp_r_quat[0],
                clamp_r_quat[1],
                clamp_r_quat[2],
                clamp_r_quat[3],
                r_finger_opening,
                clamp_l_pos[0],
                clamp_l_pos[1],
                clamp_l_pos[2],
                clamp_l_quat[0],
                clamp_l_quat[1],
                clamp_l_quat[2],
                clamp_l_quat[3],
                l_finger_opening,
                seg_pos[0],
                seg_pos[1],
                seg_pos[2],
                seg_quat[0],
                seg_quat[1],
                seg_quat[2],
                seg_quat[3],
                clip_pos[0],
                clip_pos[1],
                clip_pos[2],
                clip_quat[0],
                clip_quat[1],
                clip_quat[2],
                clip_quat[3],
                ori_error_aa[0],
                ori_error_aa[1],
                ori_error_aa[2],
                pos_error[0],
                pos_error[1],
                pos_error[2],
                ori_error_aa_l[0],
                ori_error_aa_l[1],
                ori_error_aa_l[2],
                pos_error_l[0],
                pos_error_l[1],
                pos_error_l[2],
            ]
            if self._s1a_observation_enabled:
                row.extend([0.0, 0.0, 0.0])
                dist_pos_raw = float(np.linalg.norm(clamp_r_pos - seg_pos_raw))
                dist_ori_raw = quat_distance(
                    clamp_r_quat,
                    normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent)),
                )
                dist_pos_l_raw = float(np.linalg.norm(clamp_l_pos - seg_pos_l_raw))
                cable_drop_margin = self._s1a_cable_drop_margin(w, cable_pos)
                terminal_candidate = (
                    dist_pos_raw < self.CLAMP_DIST_THRESH
                    and dist_ori_raw < self.CLAMP_ORI_THRESH
                    and cable_drop_margin > 0.0
                )
                row.extend(
                    self._s1a_observation_extension(
                        w,
                        terminal_candidate=terminal_candidate,
                        terminal_hold_len=int(self._terminal_hold_len[w]),
                        cable_drop_margin=cable_drop_margin,
                        dist_pos_raw=dist_pos_raw,
                        dist_pos_l_raw=dist_pos_l_raw,
                    )
                )
            obs_list.append(row)

        obs = torch.tensor(obs_list, dtype=torch.float32, device=self.device)
        # Pad 42D → 45D for unified base model (IC-compatible). Dims [42:45] = zeros.
        if not self._s1a_observation_enabled:
            pad = torch.zeros(obs.shape[0], 3, dtype=obs.dtype, device=obs.device)
            obs = torch.cat([obs, pad], dim=1)
        return obs

    # =========================================================================
    # Reward / Done
    # =========================================================================

    def _compute_rewards_dones_batch(self):
        """Compute rewards and dones for all worlds.

        Reward: r_pos + r_ori + r_ori_tail + r_step + r_task + r_penalty + r_drop + r_ease + r_height + r_stable + r_hold + r_drift
        Success: clamp(R) ^ cable_not_dropped ^ sustained(K).
        """
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        bqd = self._state_0.body_qd.numpy()
        fk_body_q = self._batch_fk_body_q.numpy()[:, :ROBOT_BODY_COUNT]

        rewards = np.zeros(self._world_count, dtype=np.float32)
        dones = np.zeros(self._world_count, dtype=np.int64)
        timeouts = np.zeros(self._world_count, dtype=np.int64)
        successes = np.zeros(self._world_count, dtype=np.float32)

        rc_r_pos = np.zeros(self._world_count, dtype=np.float32)
        rc_r_ori = np.zeros(self._world_count, dtype=np.float32)
        rc_r_step = np.zeros(self._world_count, dtype=np.float32)
        rc_dist = np.zeros(self._world_count, dtype=np.float32)
        rc_ori_dist = np.zeros(self._world_count, dtype=np.float32)
        rc_dist_raw = np.zeros(self._world_count, dtype=np.float32)
        rc_ori_dist_raw = np.zeros(self._world_count, dtype=np.float32)
        rc_dist_l = np.zeros(self._world_count, dtype=np.float32)
        rc_ori_dist_l = np.zeros(self._world_count, dtype=np.float32)
        rc_finger = np.zeros(self._world_count, dtype=np.float32)
        rc_finger_l = np.zeros(self._world_count, dtype=np.float32)
        rc_cable_z_min = np.zeros(self._world_count, dtype=np.float32)
        rc_cable_z_min_r = np.zeros(self._world_count, dtype=np.float32)
        rc_cable_z_min_l = np.zeros(self._world_count, dtype=np.float32)
        rc_explosion = np.zeros(self._world_count, dtype=np.bool_)
        rc_r_ease = np.zeros(self._world_count, dtype=np.float32)
        rc_r_height = np.zeros(self._world_count, dtype=np.float32)
        rc_r_stable = np.zeros(self._world_count, dtype=np.float32)
        rc_r_hold = np.zeros(self._world_count, dtype=np.float32)
        rc_r_drift = np.zeros(self._world_count, dtype=np.float32)
        rc_r_ori_tail = np.zeros(self._world_count, dtype=np.float32)
        rc_left_action_norm = np.zeros(self._world_count, dtype=np.float32)
        rc_left_ee_drift = np.zeros(self._world_count, dtype=np.float32)
        rc_ease_dist = np.zeros(self._world_count, dtype=np.float32)
        rc_cable_terminated = np.zeros(self._world_count, dtype=np.bool_)
        rc_terminal_entered = np.zeros(self._world_count, dtype=np.bool_)
        rc_terminal_hold_len = np.zeros(self._world_count, dtype=np.int32)
        rc_terminal_break_reason = np.full(self._world_count, "unspecified", dtype="<U11")
        rc_terminal_end_reason = np.full(self._world_count, "in_progress", dtype="<U16")
        rc_terminal_status_right_clamp = np.zeros(self._world_count, dtype=np.bool_)
        rc_terminal_status_left_hold = np.zeros(self._world_count, dtype=np.bool_)
        rc_terminal_status_cable_not_dropped = np.zeros(self._world_count, dtype=np.bool_)
        rc_s1a_reward = np.zeros(self._world_count, dtype=np.float32)
        rc_s1a_terminal_candidate = np.zeros(self._world_count, dtype=np.bool_)
        rc_s1a_release_readiness_stage = np.zeros(self._world_count, dtype=np.float32)
        rc_s1a_cable_drop_margin = np.zeros(self._world_count, dtype=np.float32)
        rc_s1a_explosion_margin_right = np.zeros(self._world_count, dtype=np.float32)
        rc_s1a_explosion_margin_left = np.zeros(self._world_count, dtype=np.float32)
        rc_s1a_post_release_phase = np.zeros(self._world_count, dtype=np.float32)

        for w in range(self._world_count):
            ws = self._bws[w]

            # Right EE body pose
            ee_r_idx = ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
            ee_r_pos = bq[ee_r_idx][:3]
            ee_r_quat = bq[ee_r_idx][3:7]
            clamp_r_pos = compute_clamp_pos(ee_r_pos, ee_r_quat)
            clamp_r_quat = normalize_quat_w_positive(ee_r_quat)
            clamp_r_quat = temporal_quat_consistency(clamp_r_quat, self._prev_clamp_r_quat[w])

            # Left EE body pose
            ee_l_idx = ws + EE_BODY_OFFSET
            ee_l_pos = bq[ee_l_idx][:3]
            ee_l_quat = bq[ee_l_idx][3:7]
            clamp_l_pos = compute_clamp_pos(ee_l_pos, ee_l_quat)
            clamp_l_quat = normalize_quat_w_positive(ee_l_quat)
            clamp_l_quat = temporal_quat_consistency(clamp_l_quat, self._prev_clamp_l_quat[w])

            # BUG-2 fix: use EMA-smoothed cable target for dist_pos/dist_ori (aligned with obs).
            # Raw seg_pos/seg_tangent still needed for r_ease (line 866) and jitter (line 882).
            cable_bq = bq[self._cable_bodies[w]]
            cable_pos = cable_bq[:, :3]
            seg_pos, seg_tangent, _ = find_nearest_cable_point(cable_pos, clamp_r_pos, self._target_seg_indices_r[w])
            # dist_pos/dist_ori: EMA targets (aligned with obs for correct credit assignment)
            dist_pos = float(np.linalg.norm(clamp_r_pos - self._ema_seg_pos_r[w]))
            dist_ori = quat_distance(clamp_r_quat, self._ema_seg_quat_r[w])
            # Raw distances for success judgment (L3 fix: EMA lag causes false success)
            dist_pos_raw = float(np.linalg.norm(clamp_r_pos - seg_pos))
            grasp_quat_raw = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent))
            dist_ori_raw = quat_distance(clamp_r_quat, grasp_quat_raw)

            # Left arm errors (EMA-aligned)
            dist_pos_l = float(np.linalg.norm(clamp_l_pos - self._ema_seg_pos_l[w]))
            dist_ori_l = quat_distance(clamp_l_quat, self._ema_seg_quat_l[w])
            # R1 fix: raw left arm distance for explosion guard
            seg_pos_l_raw, _, _ = find_nearest_cable_point(cable_pos, clamp_l_pos, self._target_seg_indices_l[w])
            dist_pos_l_raw = float(np.linalg.norm(clamp_l_pos - seg_pos_l_raw))

            # Finger opening
            fk_jq = self._per_world_fk_jq[w]
            finger_opening = (
                fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]]
                + fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]]
            )
            l_finger_opening = fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] + fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]]

            # Cable drop check: L-exclusive segments only (v38 fix).
            # R arm hasn't grasped cable yet — R-target contact causes transient sag
            # that propagates to overlapping L-R segments (19-22, margin 73-88mm).
            # L-exclusive segments (closer to L grip center) have 92-120mm margin
            # and only drop from actual grip loss, not R-arm contact propagation.
            l_excl = np.setdiff1d(self._target_seg_indices_l[w], self._target_seg_indices_r[w])
            cable_z_min_l_excl = float(cable_pos[l_excl, 2].min()) if len(l_excl) > 0 else 999.0
            cable_not_dropped = cable_z_min_l_excl > self.CABLE_DROP_Z_THRESH
            rc_cable_z_min[w] = cable_z_min_l_excl
            # Per-hand cable Z for diagnostics (always computed for monitoring)
            rc_cable_z_min_r[w] = float(cable_pos[self._target_seg_indices_r[w], 2].min())
            rc_cable_z_min_l[w] = float(cable_pos[self._target_seg_indices_l[w], 2].min())

            # ---- Reward: right arm only (left arm dist is geometric constant ~25mm) ----
            if self.REWARD_MODE == "multiplicative":
                score_pos_r = math.exp(-dist_pos / self.RANGE_POS)
                score_ori_r = math.exp(-dist_ori / self.RANGE_ORI)
                progress = (
                    self.PROGRESS_W_POS * score_pos_r
                    + self.PROGRESS_W_ORI * score_ori_r
                    + self.PROGRESS_W_COUPLED * score_pos_r * score_ori_r
                )
                # v37: non-negative shift (remove -1.0). R_PENALTY handles baseline.
                r_pos = self.PROGRESS_SCALE * progress
                r_ori = 0.0
            elif self.REWARD_MODE == "hybrid":
                # v37: non-negative shift (remove -1.0). Range [0, 1] per term.
                # R_PENALTY calibrated to zero-out at P0. Approach → positive reward.
                r_fine_r = math.exp(-dist_pos / self.EPS_POS)
                r_med_r = math.exp(-dist_pos / self.EPS_POS_MED)
                r_coarse_r = math.exp(-dist_pos / self.EPS_POS_COARSE)
                r_ori_fine_r = math.exp(-dist_ori / self.EPS_ORI)
                r_ori_coarse_r = math.exp(-dist_ori / self.EPS_ORI_COARSE)
                r_pos = self.W_POS * (r_fine_r + r_med_r + r_coarse_r) / 3
                r_ori = self.W_ORI * (r_ori_fine_r + r_ori_coarse_r) / 2
            else:
                # v37: non-negative shift for exp mode too
                r_pos = self.W_POS * math.exp(-dist_pos / self.EPS_POS)
                r_ori = (
                    self.W_ORI * (math.exp(-dist_ori / self.EPS_ORI) + math.exp(-dist_ori / self.EPS_ORI_COARSE)) / 2
                )

            # Ori tail penalty: raw dist_ori for threshold alignment with success (R3 fix)
            ori_excess = min(max(0.0, dist_ori_raw - self.THRESH_WARN), self.ORI_TAIL_CAP)
            r_ori_tail_val = -self.W_TAIL * ori_excess
            rc_r_ori_tail[w] = r_ori_tail_val

            # R_step: one-time bonus when right arm reaches approach zone
            # Uses raw distances (aligned with L3 success judgment, not EMA)
            r_step_val = 0.0
            precision_ok = dist_pos_raw < self.CLAMP_DIST_THRESH and dist_ori_raw < self.CLAMP_ORI_THRESH
            if precision_ok and not self._step_completed_right[w]:
                r_step_val = self.R_STEP_BONUS
                self._step_completed_right[w] = True

            # v37: Grace counter for termination timing (no per-step penalty).
            # R_DROP applied as one-shot on cable_terminated (clean credit assignment).
            if cable_not_dropped:
                self._drop_grace[w] = 0
            else:
                self._drop_grace[w] += 1

            # ---- Cable state reward (both arms contribute as one agent) ----
            # Term 1: Cable graspability — tangent at R target → grasp quat distance from BASE_HAND_DOWN
            grasp_target_quat_raw = compute_hand_quat_for_cable(seg_tangent)
            ease_dist = quat_distance(grasp_target_quat_raw, BASE_HAND_DOWN_QUAT)
            # v37: non-negative shift (remove -1.0)
            r_ease_val = self.W_EASE * math.exp(-ease_dist / self.RANGE_EASE)

            # Term 2: Cable height at R target zone — maintain LIFT_Z
            cable_z_r_target = float(cable_pos[self._target_seg_indices_r[w], 2].mean())
            height_norm = (cable_z_r_target - self.CABLE_DROP_Z_THRESH) / (LIFT_Z - self.CABLE_DROP_Z_THRESH)
            height_norm = max(0.0, min(1.0, height_norm))
            # v37: non-negative shift (remove -1.0 offset)
            r_height_val = self.W_HEIGHT * height_norm

            # Term 3: Cable stability at R target — anti-jitter regularizer
            if self._prev_seg_pos_raw_valid[w]:
                jitter = float(np.linalg.norm(seg_pos - self._prev_seg_pos_raw_r[w]))
                r_stable_val = -self.W_STAB * min(jitter / self.STAB_JITTER_CAP, 1.0)
            else:
                r_stable_val = 0.0
            self._prev_seg_pos_raw_r[w] = seg_pos.copy()
            self._prev_seg_pos_raw_valid[w] = True

            # Left arm hold penalty: penalize left arm action magnitude
            if self._last_actions is not None:
                a_left = self._last_actions[w, 6:12]
                left_sq = float(torch.sum(a_left**2))
                r_hold_val = -self.W_HOLD * left_sq
                rc_left_action_norm[w] = math.sqrt(left_sq)
            else:
                r_hold_val = 0.0
            rc_r_hold[w] = r_hold_val

            # Left arm drift penalty: penalize EE position deviation from episode start (capped)
            left_ee_drift = float(np.linalg.norm(ee_l_pos - self._settled_ee_l_pos))
            r_drift_val = -self.W_DRIFT * min(left_ee_drift, self.DRIFT_CAP)
            rc_r_drift[w] = r_drift_val
            rc_left_ee_drift[w] = left_ee_drift

            rc_r_ease[w] = r_ease_val
            rc_r_height[w] = r_height_val
            rc_r_stable[w] = r_stable_val
            rc_ease_dist[w] = ease_dist

            # SUCCESS: right arm pos ^ ori ^ cable_not_dropped ^ sustained(K)
            # Left arm dist_pos_l excluded: L arm holds cable, so clamp-to-cable
            # distance is a geometric constant (~25mm) that policy cannot reduce.
            # Left arm health is covered by cable_not_dropped condition.
            # L3 fix: use raw distances (not EMA) to prevent false success from EMA lag
            clamp_pos_ok = dist_pos_raw < self.CLAMP_DIST_THRESH
            clamp_ori_ok = dist_ori_raw < self.CLAMP_ORI_THRESH
            right_clamp_ok = clamp_pos_ok and clamp_ori_ok
            terminal_candidate = right_clamp_ok and cable_not_dropped
            previous_terminal_hold = int(self._success_sustain_count[w])
            if terminal_candidate:
                self._success_sustain_count[w] += 1
            else:
                self._success_sustain_count[w] = 0
            # === A5 Phase 4 #2: emit hold-detection signal event (logging-only; reward/policy unaffected) ===
            prev_cand = bool(self._prev_terminal_candidate[w])
            self._hold_signal_event_this_step[w] = 0
            if terminal_candidate and not prev_cand:
                self._hold_signal_event_this_step[w] = 1  # acquired (False -> True transition)
                self._hold_signal_acquired_count[w] += 1
            elif (not terminal_candidate) and prev_cand:
                self._hold_signal_event_this_step[w] = 2  # lost (True -> False transition)
                self._hold_signal_lost_count[w] += 1
            # k5_sustained: count just reached K_GRASP for the first time this hold run
            if terminal_candidate and self._success_sustain_count[w] == self.C5_SUSTAIN_STEPS:
                self._hold_signal_event_this_step[w] = 3  # k5_sustained takes precedence within this step
                self._hold_signal_k5_sustained_count[w] += 1
            self._prev_terminal_candidate[w] = terminal_candidate
            # === END A5 Phase 4 #2 ===
            s1a_cable_drop_margin = self._s1a_cable_drop_margin(w, cable_pos)
            s1a_terminal_hold_len = int(self._success_sustain_count[w])
            s1a_explosion_margin_right = self.EXPLOSION_DIST_THRESH - dist_pos_raw
            s1a_explosion_margin_left = self.EXPLOSION_DIST_THRESH - dist_pos_l_raw
            rc_s1a_terminal_candidate[w] = terminal_candidate
            rc_s1a_release_readiness_stage[w] = self._s1a_observation_extension(
                w,
                terminal_candidate=terminal_candidate,
                terminal_hold_len=s1a_terminal_hold_len,
                cable_drop_margin=s1a_cable_drop_margin,
                dist_pos_raw=dist_pos_raw,
                dist_pos_l_raw=dist_pos_l_raw,
            )[5]
            rc_s1a_cable_drop_margin[w] = s1a_cable_drop_margin
            rc_s1a_explosion_margin_right[w] = s1a_explosion_margin_right
            rc_s1a_explosion_margin_left[w] = s1a_explosion_margin_left
            rc_s1a_post_release_phase[w] = self._s1a_post_release_phase_for_world(w)
            # === B-A5.2 Phase 4 #2 behavioral: count hold breaks (gated, logging-only when off) ===
            if self._enable_b_a5_2:
                # hold_signal_event_this_step == 2 means "lost" transition fired this step;
                # restrict counting to post-acquisition (_terminal_entered) so a never-hold world
                # does not accumulate spurious hold_break events.
                if self._hold_signal_event_this_step[w] == 2 and self._terminal_entered[w]:
                    self._hold_break_count[w] += 1
                    if self._hold_break_count[w] >= self.B_A5_2_HOLD_BREAK_THRESHOLD:
                        self._hold_break_terminated[w] = True
            # === END B-A5.2 Phase 4 #2 behavioral ===
            success = self._success_sustain_count[w] >= self.C5_SUSTAIN_STEPS

            r_task_val = self.R_TASK_BONUS if success else 0.0
            r_penalty = self.R_PENALTY

            # VBD explosion guard — raw distances for instant detection (R1 fix)
            explosion = (
                dist_pos_raw > self.EXPLOSION_DIST_THRESH
                or dist_pos_l_raw > self.EXPLOSION_DIST_THRESH
                or math.isnan(dist_pos_raw)
                or math.isnan(dist_pos_l_raw)
            )

            # A6 Phase 5: extend drop grace conditional on terminal_entered (per Rs代行 06:35 disposition β
            # + modified (α) revision 07:50 post V7 gate NO_GO to add enable_a6_grace flag gating).
            # When self._enable_a6_grace is False (default), V6 baseline behavior is preserved exactly.
            # When True, effective threshold = DROP_GRACE_STEPS + TERMINAL_GRACE_STEPS for terminal_entered worlds.
            # _drop_grace counter behavior unchanged; only the threshold for cable_terminated declaration shifts.
            # AR success criterion `clamp(R) ∧ cable_not_dropped ∧ sustained(K=5)` UNCHANGED.
            if self._enable_a6_grace:
                effective_drop_grace_steps = (
                    self.DROP_GRACE_STEPS + self.TERMINAL_GRACE_STEPS
                    if self._terminal_entered[w]
                    else self.DROP_GRACE_STEPS
                )
                cable_terminated = self._drop_grace[w] >= effective_drop_grace_steps
            else:
                cable_terminated = self._drop_grace[w] >= self.DROP_GRACE_STEPS
            timeout = self.episode_length_buf[w].item() >= self.max_episode_length

            left_hold_ok = rc_cable_z_min_l[w] > self.CABLE_DROP_Z_THRESH
            if terminal_candidate:
                self._terminal_entered[w] = True
            self._terminal_hold_len[w] = int(self._success_sustain_count[w])

            # === B-A3.1 Phase 4 #2 behavioral: additive R-clamp + L-hold counterfactual (gated) ===
            # Counterfactual requires R clamp pos+ori (right_clamp_ok), L cable region hold
            # (left_hold_ok = rc_cable_z_min_l[w] > CABLE_DROP_Z_THRESH), AND cable_not_dropped,
            # sustained K=5. L is cable region z-min check, NOT L clamp match. Canonical
            # success criterion clamp(R) ^ cable_not_dropped ^ sustained(K=5) is UNCHANGED.
            if self._enable_b_a3_1:
                terminal_candidate_right_clamp_left_hold = (
                    right_clamp_ok and left_hold_ok and cable_not_dropped
                )
                if terminal_candidate_right_clamp_left_hold:
                    self._success_right_clamp_left_hold_sustain_count[w] += 1
                else:
                    self._success_right_clamp_left_hold_sustain_count[w] = 0
                self._success_right_clamp_left_hold[w] = (
                    self._success_right_clamp_left_hold_sustain_count[w]
                    >= self.C5_SUSTAIN_STEPS
                )
            # === END B-A3.1 Phase 4 #2 behavioral ===

            terminal_break_reason = "unspecified"
            if cable_terminated or (previous_terminal_hold > 0 and not cable_not_dropped):
                terminal_break_reason = "cable_drop"
            elif explosion:
                terminal_break_reason = "explosion"
            # === B-A5.2 Phase 4 #2 behavioral: hold_break inserted between explosion and timeout/clamp_loss ===
            elif self._enable_b_a5_2 and bool(self._hold_break_terminated[w]):
                terminal_break_reason = "hold_break"
            # === END B-A5.2 Phase 4 #2 behavioral ===
            elif timeout and not success:
                terminal_break_reason = "timeout"
            elif previous_terminal_hold > 0 and not right_clamp_ok:
                terminal_break_reason = "clamp_loss"
            if terminal_break_reason != "unspecified":
                self._terminal_break_reason[w] = terminal_break_reason
            self._record_s1b_grasp_geometry_telemetry(
                world_idx=w,
                step_i=int(self.episode_length_buf[w].item()),
                configured_release_step=int(self._d0_control_release_step),
                post_release_phase=float(rc_s1a_post_release_phase[w]),
                clamp_r_pos=clamp_r_pos,
                clamp_l_pos=clamp_l_pos,
                cable_point_r=seg_pos,
                cable_point_l=seg_pos_l_raw,
                finger_opening_r=finger_opening,
                finger_opening_l=l_finger_opening,
                cable_drop=bool(cable_terminated),
                clamp_loss=bool(previous_terminal_hold > 0 and not right_clamp_ok),
                explosion=bool(explosion),
                terminal_break_reason=terminal_break_reason,
                body_q=bq,
                body_qd=bqd,
                world_body_start=ws,
                fk_body_q_world=fk_body_q[w],
            )

            s1a_reward_val = self._s1a_reward_value(
                terminal_candidate=terminal_candidate,
                previous_terminal_hold=previous_terminal_hold,
                terminal_hold_len=s1a_terminal_hold_len,
                cable_drop_margin=s1a_cable_drop_margin,
                dist_pos_raw=dist_pos_raw,
                dist_pos_l_raw=dist_pos_l_raw,
                explosion=explosion,
                cable_terminated=cable_terminated,
                post_release_phase=bool(rc_s1a_post_release_phase[w] > 0.0),
            )
            rc_s1a_reward[w] = s1a_reward_val

            if explosion:
                r = -10.0  # Fixed penalty: clear signal without inf gradient contamination
            elif cable_terminated:
                # v37: one-shot terminal penalty (replaces per-step R_DROP_PENALTY)
                r = self.R_DROP
            else:
                r = (
                    r_pos
                    + r_ori
                    + r_ori_tail_val
                    + r_step_val
                    + r_task_val
                    + r_penalty
                    + r_ease_val
                    + r_height_val
                    + r_stable_val
                    + r_hold_val
                    + r_drift_val
                    + s1a_reward_val
                )
                if math.isnan(r):
                    r = self.R_PENALTY
            done = success or timeout or explosion or cable_terminated
            # === B-A5.2 Phase 4 #2 behavioral: add hold_break_terminated to done condition (gated) ===
            if self._enable_b_a5_2:
                done = done or bool(self._hold_break_terminated[w])
            # === END B-A5.2 Phase 4 #2 behavioral ===

            terminal_end_reason = "in_progress"
            if done:
                if success:
                    terminal_end_reason = "success"
                elif cable_terminated:
                    terminal_end_reason = "cable_drop"
                elif explosion:
                    terminal_end_reason = "explosion"
                elif self._enable_b_a5_2 and bool(self._hold_break_terminated[w]):
                    terminal_end_reason = "hold_break"
                elif timeout:
                    terminal_end_reason = "timeout"
                elif previous_terminal_hold > 0 and not right_clamp_ok:
                    terminal_end_reason = "clamp_loss"
                else:
                    terminal_end_reason = "unknown"

            self._update_kinematic_left_finger_support_readiness(
                w,
                success=success,
                right_clamp=right_clamp_ok,
                left_hold=left_hold_ok,
                cable_not_dropped=cable_not_dropped,
                explosion=explosion,
                cable_terminated=cable_terminated,
                terminal_end_reason=terminal_end_reason,
                terminal_hold_len=self._terminal_hold_len[w],
            )
            if (
                self._kinematic_left_finger_support_enabled
                and self._kinematic_left_finger_support_gate_type
                == KINEMATIC_GATE_HOLD_TO_COMPLETION
                and self._kinematic_support_active[w]
                and done
            ):
                self._kinematic_release_reason[w] = "episode_complete_no_release"
                self._kinematic_release_ready_reason[w] = str(terminal_end_reason)
                self._kinematic_release_terminal_hold_len[w] = int(self._terminal_hold_len[w])
                self._kinematic_release_right_clamp[w] = bool(right_clamp_ok)
                self._kinematic_release_left_hold[w] = bool(left_hold_ok)
                self._kinematic_release_cable_not_dropped[w] = bool(cable_not_dropped)

            rewards[w] = r
            rc_r_pos[w] = r_pos
            rc_r_ori[w] = r_ori
            rc_r_step[w] = r_step_val
            # Clamp dist to EXPLOSION_DIST_THRESH to prevent inf in mean computation
            rc_dist[w] = (
                min(dist_pos, self.EXPLOSION_DIST_THRESH) if not math.isnan(dist_pos) else self.EXPLOSION_DIST_THRESH
            )
            rc_ori_dist[w] = dist_ori if not math.isnan(dist_ori) else 0.0
            # R4 fix: log raw distances (success-determining)
            rc_dist_raw[w] = (
                min(dist_pos_raw, self.EXPLOSION_DIST_THRESH)
                if not math.isnan(dist_pos_raw)
                else self.EXPLOSION_DIST_THRESH
            )
            rc_ori_dist_raw[w] = dist_ori_raw if not math.isnan(dist_ori_raw) else 0.0
            rc_dist_l[w] = (
                min(dist_pos_l, self.EXPLOSION_DIST_THRESH)
                if not math.isnan(dist_pos_l)
                else self.EXPLOSION_DIST_THRESH
            )
            rc_ori_dist_l[w] = dist_ori_l if not math.isnan(dist_ori_l) else 0.0
            rc_finger[w] = finger_opening
            rc_finger_l[w] = l_finger_opening
            rc_explosion[w] = explosion
            rc_cable_terminated[w] = cable_terminated
            rc_terminal_entered[w] = self._terminal_entered[w]
            rc_terminal_hold_len[w] = self._terminal_hold_len[w]
            rc_terminal_break_reason[w] = self._terminal_break_reason[w]
            rc_terminal_end_reason[w] = terminal_end_reason
            rc_terminal_status_right_clamp[w] = right_clamp_ok
            rc_terminal_status_left_hold[w] = left_hold_ok
            rc_terminal_status_cable_not_dropped[w] = cable_not_dropped
            dones[w] = int(done)
            # BUG-1 fix: explosion/cable_terminated are true terminal states (value=0),
            # not timeouts. Only actual timeout should bootstrap value via RSL-RL PPO.
            timeouts[w] = int(timeout)
            successes[w] = float(success)
            # N2 fix: track episode-level success (not per-step snapshot)
            if done:
                self._episode_success_buf.append(float(success))

        # L2 fix: episode-level success rate for best-model save
        if len(self._episode_success_buf) > 0:
            self._last_success_rate = float(np.mean(self._episode_success_buf))
        else:
            self._last_success_rate = 0.0

        # === A3 Phase 4 #2: Per-arm separation buckets (defined once, reused in metrics + log_per_world) ===
        # Exhaustive disjoint partition over (right_clamp_ok, left_hold_ok, cable_not_dropped):
        #   both         = right & left & cable_not_dropped
        #   right_only   = right & ~left & cable_not_dropped
        #   left_only    = ~right & left & cable_not_dropped
        #   neither      = ~(both | right_only | left_only)
        # Logging-only; does NOT change current AR success criterion clamp(R) ^ cable_not_dropped ^ sustained(K=5).
        per_arm_both_at_terminal = (
            rc_terminal_status_right_clamp
            & rc_terminal_status_left_hold
            & rc_terminal_status_cable_not_dropped
        )
        per_arm_right_only_at_terminal = (
            rc_terminal_status_right_clamp
            & ~rc_terminal_status_left_hold
            & rc_terminal_status_cable_not_dropped
        )
        per_arm_left_only_at_terminal = (
            ~rc_terminal_status_right_clamp
            & rc_terminal_status_left_hold
            & rc_terminal_status_cable_not_dropped
        )
        per_arm_neither_at_terminal = ~(
            per_arm_both_at_terminal
            | per_arm_right_only_at_terminal
            | per_arm_left_only_at_terminal
        )
        # === END A3 Phase 4 #2 ===

        rc_kinematic_enabled = np.full(
            self._world_count, self._kinematic_left_finger_support_enabled, dtype=np.bool_
        )
        rc_kinematic_hold_steps = np.full(
            self._world_count, self._kinematic_left_finger_support_hold_steps, dtype=np.int32
        )
        rc_kinematic_gate_type = np.full(
            self._world_count, self._kinematic_left_finger_support_gate_type, dtype="<U32"
        )
        rc_kinematic_release_success_hold_steps = np.full(
            self._world_count, self._kinematic_release_success_hold_steps, dtype=np.int32
        )
        rc_kinematic_release_stability_steps = np.full(
            self._world_count, self._kinematic_release_stability_steps, dtype=np.int32
        )
        rc_kinematic_max_hold_steps = np.full(
            self._world_count, self._kinematic_max_hold_steps, dtype=np.int32
        )
        rc_kinematic_release_step = np.array(
            [
                None if int(step) < 0 else int(step)
                for step in self._kinematic_release_step.copy().tolist()
            ],
            dtype=object,
        )
        rc_kinematic_active_at_completion = self._kinematic_support_active.copy()
        rc_kinematic_release_reason = self._kinematic_release_reason.copy()
        rc_kinematic_release_ready_count = self._kinematic_release_ready_count.copy()
        rc_kinematic_post_release_steps = self._kinematic_post_release_steps.copy()
        rc_kinematic_release_ready_reason = self._kinematic_release_ready_reason.copy()
        rc_kinematic_release_after_success = self._kinematic_released_after_success.copy()
        rc_kinematic_release_terminal_hold_len = self._kinematic_release_terminal_hold_len.copy()
        rc_kinematic_release_right_clamp = self._kinematic_release_right_clamp.copy()
        rc_kinematic_release_left_hold = self._kinematic_release_left_hold.copy()
        rc_kinematic_release_cable_not_dropped = self._kinematic_release_cable_not_dropped.copy()
        d0_contact_log, d0_contact_log_per_world = self._d0_contact_telemetry_log_fields()
        d0_control_log, d0_control_log_per_world = self._d0_control_source_log_fields()
        s1b_telemetry_log, s1b_telemetry_log_per_world, s1b_telemetry_payload = (
            self._s1b_grasp_geometry_telemetry_log_fields()
        )
        s1a_log, s1a_log_per_world = self._s1a_curriculum_log_fields(
            reward_values=rc_s1a_reward,
            terminal_candidate=rc_s1a_terminal_candidate,
            readiness_stage=rc_s1a_release_readiness_stage,
            cable_drop_margin=rc_s1a_cable_drop_margin,
            explosion_margin_right=rc_s1a_explosion_margin_right,
            explosion_margin_left=rc_s1a_explosion_margin_left,
            post_release_phase=rc_s1a_post_release_phase,
        )

        return (
            torch.tensor(rewards, dtype=torch.float32, device=self.device),
            torch.tensor(dones, dtype=torch.long, device=self.device),
            {
                "observations": {},
                "time_outs": torch.tensor(timeouts, dtype=torch.long, device=self.device),
                "log": {
                    "/metrics/step_success_fraction": float(np.mean(successes)),
                    "/episode/success": float(np.mean(successes)),  # backward compat for consumers
                    "/reward/r_pos": float(np.mean(rc_r_pos)),
                    "/reward/r_ori": float(np.mean(rc_r_ori)),
                    "/reward/r_step": float(np.mean(rc_r_step)),
                    "/reward/r_penalty": float(self.R_PENALTY),
                    "/metrics/dist_pos_mean": float(np.mean(rc_dist)),
                    "/metrics/dist_pos_median": float(np.median(rc_dist)),
                    "/metrics/dist_pos_p95": float(np.percentile(rc_dist, 95)) if len(rc_dist) > 0 else 0.0,
                    "/metrics/dist_ori_mean": float(np.mean(rc_ori_dist)),
                    "/metrics/dist_ori_median": float(np.median(rc_ori_dist)),
                    "/metrics/dist_pos_raw_median": float(np.median(rc_dist_raw)),
                    "/metrics/dist_ori_raw_median": float(np.median(rc_ori_dist_raw)),
                    "/metrics/dist_pos_l_median": float(np.median(rc_dist_l)),
                    "/metrics/dist_ori_l_median": float(np.median(rc_ori_dist_l)),
                    "/metrics/finger_opening_mean": float(np.mean(rc_finger)),
                    "/metrics/finger_opening_l_mean": float(np.mean(rc_finger_l)),
                    "/metrics/cable_z_min": float(np.min(rc_cable_z_min)),
                    "/metrics/cable_drop_count": int(np.sum(rc_cable_z_min <= self.CABLE_DROP_Z_THRESH)),
                    "/metrics/cable_drop_count_r": int(np.sum(rc_cable_z_min_r <= self.CABLE_DROP_Z_THRESH)),
                    "/metrics/cable_drop_count_l": int(np.sum(rc_cable_z_min_l <= self.CABLE_DROP_Z_THRESH)),
                    "/metrics/explosion_count": int(np.sum(rc_explosion)),
                    "/metrics/drop_grace_mean": float(np.mean(self._drop_grace)),
                    "/metrics/terminal_entered_count": int(np.sum(rc_terminal_entered)),
                    "/metrics/terminal_hold_len_mean": float(np.mean(rc_terminal_hold_len)),
                    "/metrics/terminal_hold_len_median": float(np.median(rc_terminal_hold_len)),
                    "/metrics/terminal_hold_len_max": int(np.max(rc_terminal_hold_len)),
                    "/metrics/terminal_break_cable_drop_count": int(
                        np.sum(rc_terminal_break_reason == "cable_drop")
                    ),
                    "/metrics/terminal_break_explosion_count": int(
                        np.sum(rc_terminal_break_reason == "explosion")
                    ),
                    "/metrics/terminal_break_clamp_loss_count": int(
                        np.sum(rc_terminal_break_reason == "clamp_loss")
                    ),
                    "/metrics/terminal_break_timeout_count": int(np.sum(rc_terminal_break_reason == "timeout")),
                    "/metrics/terminal_end_success_count": int(np.sum(rc_terminal_end_reason == "success")),
                    "/metrics/terminal_end_cable_drop_count": int(
                        np.sum(rc_terminal_end_reason == "cable_drop")
                    ),
                    "/metrics/terminal_end_explosion_count": int(
                        np.sum(rc_terminal_end_reason == "explosion")
                    ),
                    "/metrics/terminal_end_hold_break_count": int(
                        np.sum(rc_terminal_end_reason == "hold_break")
                    ),
                    "/metrics/terminal_end_timeout_count": int(np.sum(rc_terminal_end_reason == "timeout")),
                    "/metrics/terminal_end_clamp_loss_count": int(
                        np.sum(rc_terminal_end_reason == "clamp_loss")
                    ),
                    "/metrics/terminal_end_unknown_count": int(np.sum(rc_terminal_end_reason == "unknown")),
                    "/metrics/terminal_end_in_progress_count": int(
                        np.sum(rc_terminal_end_reason == "in_progress")
                    ),
                    "/metrics/terminal_right_clamp_count": int(np.sum(rc_terminal_status_right_clamp)),
                    "/metrics/terminal_left_hold_count": int(np.sum(rc_terminal_status_left_hold)),
                    "/metrics/terminal_cable_not_dropped_count": int(
                        np.sum(rc_terminal_status_cable_not_dropped)
                    ),
                    # === A5 Phase 4 #2: hold-detection aggregate metrics (logging-only) ===
                    "/metrics/hold_signal_emitted_count": int(np.sum(self._hold_signal_event_this_step > 0)),
                    "/metrics/hold_signal_acquired_rate": float(np.mean(self._hold_signal_acquired_count > 0)),
                    "/metrics/hold_signal_lost_rate": float(np.mean(self._hold_signal_lost_count > 0)),
                    "/metrics/hold_signal_k5_sustained_rate": float(np.mean(self._hold_signal_k5_sustained_count > 0)),
                    # === END A5 Phase 4 #2 ===
                    # === A3 Phase 4 #2: per-arm separation aggregate metrics (reuses defined-once arrays) ===
                    "/metrics/per_arm_both_count": int(np.sum(per_arm_both_at_terminal)),
                    "/metrics/per_arm_right_only_count": int(np.sum(per_arm_right_only_at_terminal)),
                    "/metrics/per_arm_left_only_count": int(np.sum(per_arm_left_only_at_terminal)),
                    "/metrics/per_arm_neither_count": int(np.sum(per_arm_neither_at_terminal)),
                    # === END A3 Phase 4 #2 ===
                    # === B-A5.2 Phase 4 #2 behavioral: hold-break aggregate metrics ===
                    "/metrics/b_a5_2_enabled": bool(self._enable_b_a5_2),
                    "/metrics/hold_break_terminated_count": int(np.sum(self._hold_break_terminated)),
                    "/metrics/hold_break_count_mean": float(np.mean(self._hold_break_count)),
                    "/metrics/hold_break_count_max": int(np.max(self._hold_break_count)),
                    "/metrics/terminal_break_hold_break_count": int(
                        np.sum(rc_terminal_break_reason == "hold_break")
                    ),
                    # === END B-A5.2 Phase 4 #2 behavioral ===
                    # === B-A3.1 Phase 4 #2 behavioral: R-clamp + L-hold counterfactual aggregate ===
                    "/metrics/b_a3_1_enabled": bool(self._enable_b_a3_1),
                    "/metrics/success_right_clamp_left_hold_count": int(
                        np.sum(self._success_right_clamp_left_hold)
                    ),
                    "/metrics/success_right_clamp_left_hold_sustain_count_mean": float(
                        np.mean(self._success_right_clamp_left_hold_sustain_count)
                    ),
                    # === END B-A3.1 Phase 4 #2 behavioral ===
                    "/reward/r_ease": float(np.mean(rc_r_ease)),
                    "/reward/r_height": float(np.mean(rc_r_height)),
                    "/reward/r_stable": float(np.mean(rc_r_stable)),
                    "/reward/r_hold": float(np.mean(rc_r_hold)),
                    "/reward/r_drift": float(np.mean(rc_r_drift)),
                    "/reward/r_ori_tail": float(np.mean(rc_r_ori_tail)),
                    "/metrics/left_action_norm": float(np.mean(rc_left_action_norm)),
                    "/metrics/left_ee_drift": float(np.mean(rc_left_ee_drift)),
                    "/metrics/ease_dist_mean": float(np.mean(rc_ease_dist)),
                    "/metrics/ease_dist_median": float(np.median(rc_ease_dist)),
                    "/metrics/episode_success_rate": self._last_success_rate,
                    "/metrics/kinematic_left_finger_support_enabled": bool(
                        self._kinematic_left_finger_support_enabled
                    ),
                    "/metrics/kinematic_left_finger_support_hold_steps": int(
                        self._kinematic_left_finger_support_hold_steps
                    ),
                    "/metrics/kinematic_left_finger_support_gate_type": str(
                        self._kinematic_left_finger_support_gate_type
                    ),
                    "/metrics/kinematic_release_success_hold_steps": int(
                        self._kinematic_release_success_hold_steps
                    ),
                    "/metrics/kinematic_release_stability_steps": int(
                        self._kinematic_release_stability_steps
                    ),
                    "/metrics/kinematic_max_hold_steps": int(self._kinematic_max_hold_steps),
                    "/metrics/kinematic_left_finger_support_active_count": int(
                        np.sum(self._kinematic_support_active)
                    ),
                    "/metrics/kinematic_release_ready_count_mean": float(
                        np.mean(self._kinematic_release_ready_count)
                    ),
                    "/metrics/kinematic_post_release_count": int(
                        np.sum(self._kinematic_post_release_steps >= 0)
                    ),
                    "/metrics/kinematic_released_after_success_count": int(
                        np.sum(self._kinematic_released_after_success)
                    ),
                    "/metrics/kinematic_release_step_count": int(
                        np.sum(self._kinematic_release_step >= 0)
                    ),
                    "/metrics/kinematic_release_step_count_step_count_gate": int(
                        np.sum(self._kinematic_release_reason == "step_count_gate")
                    ),
                    "/metrics/kinematic_release_step_count_success_stability_gate": int(
                        np.sum(self._kinematic_release_reason == "success_stability_gate")
                    ),
                    "/metrics/kinematic_release_step_count_max_hold_guard": int(
                        np.sum(self._kinematic_release_reason == "max_hold_guard")
                    ),
                    "/metrics/kinematic_release_episode_complete_no_release_count": int(
                        np.sum(self._kinematic_release_reason == "episode_complete_no_release")
                    ),
                    **d0_contact_log,
                    **d0_control_log,
                    **s1b_telemetry_log,
                    **s1a_log,
                },
                "log_per_world": {
                    "dist_pos": rc_dist.copy(),
                    "dist_ori": rc_ori_dist.copy(),
                    "finger_opening": rc_finger.copy(),
                    "reward": rewards.copy(),
                    "success": successes.copy(),
                    "explosion": rc_explosion.copy(),
                    "cable_terminated": rc_cable_terminated.copy(),
                    "cable_z_min": rc_cable_z_min.copy(),
                    "terminal_entered": rc_terminal_entered.copy(),
                    "terminal_hold_len": rc_terminal_hold_len.copy(),
                    "terminal_break_reason": rc_terminal_break_reason.copy(),
                    "terminal_end_reason": rc_terminal_end_reason.copy(),
                    "terminal_status_right_clamp": rc_terminal_status_right_clamp.copy(),
                    "terminal_status_left_hold": rc_terminal_status_left_hold.copy(),
                    "terminal_status_cable_not_dropped": rc_terminal_status_cable_not_dropped.copy(),
                    "kinematic_left_finger_support_enabled": rc_kinematic_enabled.copy(),
                    "kinematic_left_finger_support_gate_type": rc_kinematic_gate_type.copy(),
                    "kinematic_left_finger_support_hold_steps": rc_kinematic_hold_steps.copy(),
                    "kinematic_release_success_hold_steps": (
                        rc_kinematic_release_success_hold_steps.copy()
                    ),
                    "kinematic_release_stability_steps": rc_kinematic_release_stability_steps.copy(),
                    "kinematic_max_hold_steps": rc_kinematic_max_hold_steps.copy(),
                    "kinematic_release_step": rc_kinematic_release_step.copy(),
                    "kinematic_release_reason": rc_kinematic_release_reason.copy(),
                    "kinematic_release_ready_count": rc_kinematic_release_ready_count.copy(),
                    "kinematic_post_release_steps": rc_kinematic_post_release_steps.copy(),
                    "kinematic_release_ready_reason": rc_kinematic_release_ready_reason.copy(),
                    "kinematic_release_after_success": rc_kinematic_release_after_success.copy(),
                    "kinematic_release_terminal_hold_len": (
                        rc_kinematic_release_terminal_hold_len.copy()
                    ),
                    "kinematic_release_right_clamp": rc_kinematic_release_right_clamp.copy(),
                    "kinematic_release_left_hold": rc_kinematic_release_left_hold.copy(),
                    "kinematic_release_cable_not_dropped": (
                        rc_kinematic_release_cable_not_dropped.copy()
                    ),
                    "kinematic_active_at_completion": rc_kinematic_active_at_completion.copy(),
                    # === A5 Phase 4 #2: hold-detection signal per-world emission (logging-only) ===
                    "hold_signal_event_this_step": self._hold_signal_event_this_step.copy(),
                    "hold_signal_acquired_count": self._hold_signal_acquired_count.copy(),
                    "hold_signal_lost_count": self._hold_signal_lost_count.copy(),
                    "hold_signal_k5_sustained_count": self._hold_signal_k5_sustained_count.copy(),
                    # === END A5 Phase 4 #2 ===
                    # === A3 Phase 4 #2: per-arm separation per-world emission (reuses defined-once arrays) ===
                    "per_arm_both_at_terminal": per_arm_both_at_terminal.copy(),
                    "per_arm_right_only_at_terminal": per_arm_right_only_at_terminal.copy(),
                    "per_arm_left_only_at_terminal": per_arm_left_only_at_terminal.copy(),
                    "per_arm_neither_at_terminal": per_arm_neither_at_terminal.copy(),
                    # === END A3 Phase 4 #2 ===
                    # === B-A5.2 Phase 4 #2 behavioral: hold-break per-world emission ===
                    "b_a5_2_enabled": np.full(self._world_count, bool(self._enable_b_a5_2), dtype=np.bool_),
                    "hold_break_count": self._hold_break_count.copy(),
                    "hold_break_terminated": self._hold_break_terminated.copy(),
                    # === END B-A5.2 Phase 4 #2 behavioral ===
                    # === B-A3.1 Phase 4 #2 behavioral: R-clamp + L-hold counterfactual per-world emission ===
                    "b_a3_1_enabled": np.full(self._world_count, bool(self._enable_b_a3_1), dtype=np.bool_),
                    "success_right_clamp_left_hold": self._success_right_clamp_left_hold.copy(),
                    "success_right_clamp_left_hold_sustain_count": (
                        self._success_right_clamp_left_hold_sustain_count.copy()
                    ),
                    # === END B-A3.1 Phase 4 #2 behavioral ===
                    **d0_contact_log_per_world,
                    **d0_control_log_per_world,
                    **s1b_telemetry_log_per_world,
                    **s1a_log_per_world,
                },
                **(
                    {"s1b_grasp_geometry_telemetry": s1b_telemetry_payload}
                    if s1b_telemetry_payload is not None
                    else {}
                ),
            },
        )

    # =========================================================================
    # Action Application
    # =========================================================================

    def _apply_actions_batch(self, actions):
        """Apply per-world 12D actions via batched IK + physics.

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

        # Compute per-world adaptive pos scale for right arm
        if self.ADAPTIVE_POS_SCALE:
            r_pos_scales = np.full(N, self.POS_ACTION_SCALE, dtype=np.float32)
            for w in range(N):
                ws = self._bws[w]
                cable_bq = bq[self._cable_bodies[w]]
                cable_pos = cable_bq[:, :3]

                ee_r_idx = ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
                clamp_r = compute_clamp_pos(bq[ee_r_idx][:3], bq[ee_r_idx][3:7])
                _, _, dist_r = find_nearest_cable_point(cable_pos, clamp_r, self._target_seg_indices_r[w])
                r_pos_scales[w] = max(
                    self.MIN_POS_SCALE, self.POS_ACTION_SCALE * min(1.0, dist_r / self.FINE_THRESHOLD)
                )
            r_pos_delta = actions_np[:, 0:3] * r_pos_scales[:, None]
        else:
            r_pos_delta = actions_np[:, 0:3] * self.POS_ACTION_SCALE

        r_rot_delta = actions_np[:, 3:6] * self.ROT_ACTION_SCALE
        # Left arm: scaled same as right arm; damping applied once in per-world loop (L1121)
        l_pos_delta = actions_np[:, 6:9] * self.POS_ACTION_SCALE
        l_rot_delta = actions_np[:, 9:12] * self.ROT_ACTION_SCALE

        # R2-A: freeze left EE at settled pose each step (Phase 1-B evidence: -13.9pp high_drop)
        if self._freeze_left_anchor:
            if not self._freeze_wdrift_warned and self.W_DRIFT > 0.0:
                import warnings
                warnings.warn(
                    f"freeze_left_anchor=True with W_DRIFT={self.W_DRIFT}: left EE stays at settled → "
                    "drift≈0, W_DRIFT is a structural no-op. Set W_DRIFT=0 to suppress.",
                    stacklevel=2,
                )
                self._freeze_wdrift_warned = True
            l_pos_delta[:] = 0.0
            l_rot_delta[:] = 0.0
            self._ee_target_left[:] = self._settled_ee_l_pos
            self._ee_quat_left[:] = self._settled_ee_l_quat

        fk_coord_count = self._fk_model.joint_coord_count
        finger_mask = np.ones(fk_coord_count, dtype=bool)
        for fc in FINGER_JOINT_INDICES:
            finger_mask[fc] = False

        # Compute per-world EE targets
        targets_left = np.zeros((N, 3))
        targets_right = np.zeros((N, 3))
        rot_targets_left = []
        rot_targets_right = []
        jq_starts = np.array(self._per_world_fk_jq[:N])

        # --- Finger auto-control: right arm only (left always CLOSED) ---
        per_w_dist_pos_r = np.zeros(N, dtype=np.float32)
        per_w_dist_ori_r = np.zeros(N, dtype=np.float32)
        for w in range(N):
            ws = self._bws[w]
            ee_r_idx = ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
            ee_r_pos = bq[ee_r_idx][:3]
            ee_r_quat = bq[ee_r_idx][3:7]

            # C3 fix: use EMA distances for ori-gate (aligned with obs/reward)
            clamp_r_pos = compute_clamp_pos(ee_r_pos, ee_r_quat)
            clamp_r_quat_norm = normalize_quat_w_positive(ee_r_quat)
            per_w_dist_pos_r[w] = float(np.linalg.norm(clamp_r_pos - self._ema_seg_pos_r[w]))
            per_w_dist_ori_r[w] = quat_distance(clamp_r_quat_norm, self._ema_seg_quat_r[w])

            # Finger targets: R always OPEN, L always CLOSED
            jq_starts[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
            jq_starts[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS
            jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_CLOSE_POS
            jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_CLOSE_POS

        # Ori-gated approach: suppress pos delta when near cable but ori not ready
        for w in range(N):
            if per_w_dist_pos_r[w] < self.ORI_GATE_POS_THRESH and per_w_dist_ori_r[w] > self.ORI_GATE_ORI_THRESH:
                r_pos_delta[w] *= self.CLOSE_ACTION_DAMPING

        # Left arm: unconditional damping (stabilizer role)
        for w in range(N):
            l_pos_delta[w] *= self.CLOSE_ACTION_DAMPING
            l_rot_delta[w] *= self.CLOSE_ACTION_DAMPING

        # --- EE position + rotation targets ---
        for w in range(N):
            # Right EE: tracked target + delta
            target_r = self._ee_target_right[w].copy() + r_pos_delta[w]
            target_r[2] = np.clip(target_r[2], LIFT_Z - 0.05, LIFT_Z + 0.05)
            targets_right[w] = target_r
            self._ee_target_right[w] = target_r.copy()

            # Right EE rotation
            delta_r_quat = axis_angle_to_quat_xyzw(r_rot_delta[w])
            new_r_quat = quat_multiply_xyzw(delta_r_quat, self._ee_quat_right[w])
            new_r_quat = new_r_quat / np.linalg.norm(new_r_quat)
            self._ee_quat_right[w] = new_r_quat.copy()
            rot_targets_right.append(
                wp.vec4(float(new_r_quat[0]), float(new_r_quat[1]), float(new_r_quat[2]), float(new_r_quat[3]))
            )

            # Left EE: tracked target + delta
            target_l = self._ee_target_left[w].copy() + l_pos_delta[w]
            target_l[2] = np.clip(target_l[2], LIFT_Z - 0.05, LIFT_Z + 0.05)
            target_l = self._d0_control_adjust_left_target(w, target_l)
            targets_left[w] = target_l
            self._ee_target_left[w] = target_l.copy()

            # Left EE rotation
            delta_l_quat = axis_angle_to_quat_xyzw(l_rot_delta[w])
            new_l_quat = quat_multiply_xyzw(delta_l_quat, self._ee_quat_left[w])
            new_l_quat = new_l_quat / np.linalg.norm(new_l_quat)
            self._ee_quat_left[w] = new_l_quat.copy()
            rot_targets_left.append(
                wp.vec4(float(new_l_quat[0]), float(new_l_quat[1]), float(new_l_quat[2]), float(new_l_quat[3]))
            )

        # Set IK rotation targets
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
            for fc in FINGER_JOINT_INDICES:
                jq_targets[w, fc] = jq_starts[w, fc]

        # Interpolate FK + physics stepping
        for step in range(self.PHYSICS_STEPS_PER_RL):
            t = min((step + 1) / self.PHYSICS_STEPS_PER_RL, 1.0)

            jq_interp_all = jq_starts.copy()
            jq_interp_all[:, finger_mask] = (
                jq_starts[:, finger_mask] + (jq_targets[:, finger_mask] - jq_starts[:, finger_mask]) * t
            )

            # Finger interpolation from old to new
            for fc in FINGER_JOINT_INDICES:
                jq_interp_all[:, fc] = (
                    self._per_world_fk_jq[:N, fc] + (jq_targets[:, fc] - self._per_world_fk_jq[:N, fc]) * t
                )

            # Batched FK
            self._batch_fk_jq.assign(jq_interp_all)
            eval_fk_batched(
                self._fk_model, self._batch_fk_jq, self._batch_fk_jqd, self._batch_fk_body_q, self._batch_fk_body_qd
            )
            batch_bq = self._batch_fk_body_q.numpy()[:, :ROBOT_BODY_COUNT]
            phys_bq = self._state_0.body_q.numpy()
            for w in range(N):
                ws = self._bws[w]
                for bi in range(ROBOT_BODY_COUNT):
                    if (ws + bi) not in self._left_finger_set:
                        phys_bq[ws + bi] = batch_bq[w, bi]
            self._state_0.body_q.assign(phys_bq)

            self._physics_step_all(substeps=RL_SIM_SUBSTEPS, sim_dt=RL_SIM_DT, fk_batch_bq=batch_bq, n_worlds=N)

        # Save final FK state per world
        for w in range(N):
            self._per_world_fk_jq[w] = jq_targets[w].copy()

    # =========================================================================
    # Physics
    # =========================================================================

    def _apply_left_finger_spring(self, fk_batch_bq, N):
        """Apply spring forces to dynamic left finger bodies toward FK target positions."""
        body_q = self._state_0.body_q.numpy()
        body_qd = self._state_0.body_qd.numpy()
        body_f = self._state_0.body_f.numpy()
        if self._d0_contact_telemetry_enabled:
            self._d0_impedance_command_force_norm_per_finger[:N] = 0.0
        for w in range(N):
            ws = self._bws[w]
            force_scale = None
            if self._d0_control_enabled:
                force_scale = self._d0_control_force_scale_for_world(w)
            for finger_idx, lf in enumerate(FINGER_LOCAL):
                bi = ws + lf
                pos = body_q[bi][:3]
                vel = body_qd[bi][3:6]  # linear velocity
                target = fk_batch_bq[w, lf, :3]
                force = -FINGER_SPRING_KE * (pos - target) - FINGER_SPRING_KD * vel
                if force_scale is not None:
                    force = force * force_scale
                body_f[bi][3:6] += force
                if self._d0_contact_telemetry_enabled:
                    self._d0_impedance_command_force_norm_per_finger[w, finger_idx] = float(
                        np.linalg.norm(force)
                    )
        if self._d0_contact_telemetry_enabled:
            self._d0_impedance_command_force_norm[:N] = np.max(
                self._d0_impedance_command_force_norm_per_finger[:N],
                axis=1,
            )
        self._state_0.body_f.assign(body_f)

    def _sanitise_body_state(self):
        """Clamp body positions and zero NaN/inf to prevent VBD segfault."""
        bq = self._state_0.body_q.numpy()
        bqd = self._state_0.body_qd.numpy()
        # Detect NaN/inf in positions (columns 0-2) and quaternions (columns 3-6)
        pos = bq[:, :3]
        quat = bq[:, 3:7]
        bad_mask = ~np.isfinite(pos).all(axis=1) | ~np.isfinite(quat).all(axis=1)
        # Also clamp bodies that have drifted far from workspace
        drift_mask = (np.abs(pos) > 5.0).any(axis=1)
        fix_mask = bad_mask | drift_mask
        if fix_mask.any():
            # Reset bad bodies to cached settle positions, zero velocities
            bq[fix_mask] = self._settled_body_q[fix_mask]
            bqd[fix_mask] = 0.0
            self._state_0.body_q.assign(bq)
            self._state_0.body_qd.assign(bqd)
            # L3 fix: also update body_q_prev to prevent VBD velocity explosion
            # VBD computes velocity from (body_q - body_q_prev) / dt
            prev = self._solver.body_q_prev.numpy()
            prev[fix_mask] = self._settled_body_q[fix_mask]
            self._solver.body_q_prev.assign(prev)

    def _physics_step_all(self, substeps=None, sim_dt=None, fk_batch_bq=None, n_worlds=None):
        """One physics frame for all worlds.

        If fk_batch_bq is provided, spring forces are applied to dynamic left
        finger bodies each substep (after clear_forces, before collide).
        """
        n_sub = substeps if substeps is not None else SIM_SUBSTEPS
        dt = sim_dt if sim_dt is not None else SIM_DT
        for _ in range(n_sub):
            self._state_0.clear_forces()
            # Spring forces on dynamic left fingers (must be after clear_forces)
            if fk_batch_bq is not None and n_worlds is not None:
                self._apply_left_finger_spring(fk_batch_bq, n_worlds)
            self._apply_kinematic_left_finger_pin(fk_batch_bq=fk_batch_bq, n_worlds=n_worlds)
            self._model.collide(self._state_0, self._contacts)
            self._solver.step(self._state_0, self._state_1, self._control, self._contacts, dt)
            self._state_0, self._state_1 = self._state_1, self._state_0
            # Sanitise body state: clamp positions and kill NaN/inf to prevent
            # VBD solver segfault from accumulated explosive drift.
            self._sanitise_body_state()
            self._apply_kinematic_left_finger_pin(fk_batch_bq=fk_batch_bq, n_worlds=n_worlds)
            self._update_d0_contact_telemetry(dt)

    # =========================================================================
    # Batched IK Solver
    # =========================================================================

    def _init_batched_ik_solver(self):
        """Create cached IKSolver with n_problems=world_count for batched solving."""
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

        # Pre-allocate batched FK buffers
        dof_count = fk_model.joint_dof_count
        body_count = fk_model.body_count
        self._batch_fk_jq = wp.zeros((N, coord_count), dtype=float, device=self.device)
        self._batch_fk_jqd = wp.zeros((N, dof_count), dtype=float, device=self.device)
        self._batch_fk_body_q = wp.zeros((N, body_count), dtype=wp.transform, device=self.device)
        self._batch_fk_body_qd = wp.zeros((N, body_count), dtype=wp.spatial_vector, device=self.device)

        print(f"[AerialRegraspEnv] Batched IK solver: n_problems={N}, joint_coords={coord_count}")

    def _solve_ik_batch(self, targets_left_np, targets_right_np, jq_starts_np):
        """Solve IK for all worlds in one batched call."""
        self._ik_obj_pos_left.set_target_positions(wp.array(targets_left_np, dtype=wp.vec3, device=self.device))
        self._ik_obj_pos_right.set_target_positions(wp.array(targets_right_np, dtype=wp.vec3, device=self.device))
        self._ik_jq_in.assign(jq_starts_np)
        self._ik_solver_batch.step(
            self._ik_jq_in,
            self._ik_jq_out,
            iterations=IK_ITERATIONS_RL,
            step_size=IK_STEP_SIZE,
        )
        return self._ik_jq_out.numpy()

    # =========================================================================
    # RSL-RL VecEnv Interface
    # =========================================================================

    @property
    def num_obs(self):
        s1a_obs_dim = (
            S1A_OBS_EXTENSION_DIM if getattr(self, "_s1a_observation_enabled", False) else 0
        )
        return 45 + s1a_obs_dim

    def get_observations(self) -> tuple[torch.Tensor, dict]:
        obs = self._compute_obs_batch()
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)
        return obs, {"observations": {}}

    def reset(self) -> tuple[torch.Tensor, dict]:
        self._reset_worlds(list(range(self._world_count)))
        return self.get_observations()

    def export_chain_state(self, *, world_idx=0, step_id=0):
        """Export shared Newton state for an opt-in no-reset chain handoff."""

        return export_chain_state_from_env(
            self,
            source_skill="AR",
            world_idx=world_idx,
            step_id=step_id,
            validation_metadata={"stage": "stage0_tracked_api"},
        )

    def import_chain_state(self, state, *, world_idx=0, validate=True):
        """Import shared Newton state for an opt-in no-reset chain handoff."""

        return import_chain_state_into_env(self, state, target_skill="AR", validate=validate)

    def validate_chain_state(self, state, *, world_idx=0):
        """Validate a chain state against this environment without reset."""

        return validate_chain_state_for_env(self, state, target_skill="AR")

    def step_chain(self, actions: torch.Tensor, *, auto_reset: bool = False):
        """Run an opt-in chain step while preserving default :meth:`step` behavior."""

        if auto_reset:
            return self.step(actions)
        actions = torch.nan_to_num(actions, nan=0.0, posinf=0.0, neginf=0.0).clamp(-1.0, 1.0)
        self._update_kinematic_left_finger_support_release()
        self._last_actions = actions
        self._apply_actions_batch(actions)
        self.episode_length_buf += 1
        self._total_env_steps += self._world_count

        rewards, dones, extras = self._compute_rewards_dones_batch()
        rewards = torch.nan_to_num(rewards, nan=-10.0, posinf=0.0, neginf=-10.0)
        obs = self._compute_obs_batch()
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)
        return obs, rewards, dones, extras

    def step(self, actions: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]:
        # Sanitise actions: NaN/inf → zero (prevents physics engine crash)
        actions = torch.nan_to_num(actions, nan=0.0, posinf=0.0, neginf=0.0).clamp(-1.0, 1.0)
        self._update_kinematic_left_finger_support_release()
        self._last_actions = actions
        self._apply_actions_batch(actions)
        self.episode_length_buf += 1
        self._total_env_steps += self._world_count

        rewards, dones, extras = self._compute_rewards_dones_batch()
        # Sanitise rewards: NaN → large negative (prevents PPO gradient corruption)
        rewards = torch.nan_to_num(rewards, nan=-10.0, posinf=0.0, neginf=-10.0)

        # Auto-reset done worlds
        done_ids = dones.nonzero(as_tuple=False).squeeze(-1)
        if len(done_ids) > 0:
            self._reset_worlds(done_ids.cpu().tolist())

        obs = self._compute_obs_batch()
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)
        return obs, rewards, dones, extras
