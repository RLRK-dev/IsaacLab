# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Newton VBD Grip RL environment -- 2-agent independent control.

Each arm is an independent agent with shared policy weights.
N physical worlds → 2N RL environments (slot 2w = right arm, 2w+1 = left arm).

Mode: "clamp" or "unclamp" -- controls P0, reward, and success conditions.

Per-arm Obs (28D -- independent from AC/AR/IC):
    [0:3]   Own hand clamp position XYZ [m]
    [3:7]   Own hand clamp quaternion (qx, qy, qz, qw), w >= 0
    [7]     Own finger opening (j7 + j8) [m]
    [8:11]  Own cable target segment position XYZ [m]
    [11:15] Own cable target segment quaternion (qx, qy, qz, qw), w >= 0
    [15:18] Clip/groove position XYZ [m]
    [18:22] Clip quaternion (qx, qy, qz, qw), w >= 0
    [22:25] Own orientation error axis-angle [rad]
    [25:28] Own position error XYZ [m]

Per-arm Action (6D):
    [0:3]   EE delta XYZ * POS_ACTION_SCALE [m]
    [3:6]   EE delta axis-angle * ROT_ACTION_SCALE [rad]
    Fingers: auto-close when pos+ori thresholds met.

Reward (per-arm, mode-dependent):
  clamp:   W_GRIP * grip_score + W_CLAMP * clamp_quality
  unclamp: W_FINGER * finger_progress + W_SEATED * cable_seated + W_COUPLED * finger * seated

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/train_grip.py --mode clamp --world-count 4
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

# Import shared utilities from base module
_env_dir = os.path.dirname(os.path.abspath(__file__))
if _env_dir not in sys.path:
    sys.path.insert(0, _env_dir)

from cable_orientation_utils import BASE_HAND_DOWN_QUAT, compute_hand_quat_for_cable
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
    axis_angle_to_quat_xyzw,
    build_fk_and_init,
    build_multiworld_scene,
    compute_clamp_pos,
    derive_cable_joint_q_from_tangents,
    compute_ori_error_axis_angle,
    extract_clamp_pose,
    find_nearest_cable_point,
    normalize_quat_w_positive,
    quat_distance,
    quat_multiply_xyzw,
    seed_cable_joint_state,
    solve_ik_single,
    temporal_quat_consistency,
)

# Dynamic finger spring parameters (aligned with GC/AR/Clamp/Unclamp)
FINGER_SPRING_KE = 10000.0
FINGER_SPRING_KD = 500.0
FINGER_DYNAMIC_INV_MASS = 20.0
FINGER_DYNAMIC_INV_INERTIA = 100.0

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
    CABLE_RADIUS,
    CABLE_SEG_LEN,
    CABLE_SEGMENTS,
    CLIP1_X,
    CLIP1_Y,
    CLIP1_Z,
    EE_TO_FINGERTIP,
    EE_Z_SAFETY_UPPER,
    FINGER_CLOSE_POS,
    FINGER_HALF_OPEN_POS,
    FINGER_LOCAL,
    FINGER_OPEN_POS,
    FINGER_STEP_SIZE,
    GRASP_X,
    GRASP_Z,
    GRIP_HALF_SPAN,
    GRIP_TERMINAL_STEPS,
    GRIPPER_DRIVER_JOINT_IDX,
    GRIPPER_JOINT_RANGE,
    GROOVE_BODIES_MIN,
    GROOVE_CENTER_Z,
    JOINTS_PER_ARM,
    K_CLAMP,
    K_UNCLAMP,
    PUSH_Z,
    SETTLE_STEPS,
    SIM_SUBSTEPS,
    T_ALIGN,
    T_DIST,
    T_FINGER,
    T_GROOVE,
    T_SEAT,
    TABLE_HEIGHT,
)

# IK rotation target
_cos_pi8 = math.cos(math.pi / 8)
_sin_pi8 = math.sin(math.pi / 8)
EXPECTED_ARMS = {"right", "left", "both"}
SELECTED_SUCCESS_SEMANTICS_VERSION = "b5_expected_arm_v1"

# Grip Z: raise by CABLE_RADIUS so fingertip targets cable center (not cable bottom).
# GRASP_Z puts fingertip at clip base top (=cable bottom); adding CABLE_RADIUS aligns with cable center.
GRIP_Z = GRASP_Z + CABLE_RADIUS  # 1.029m: fingertip at cable center Z (0.809)

# Groove check radius
GROOVE_CHECK_RADIUS = CABLE_SEG_LEN + CABLE_RADIUS  # 19mm

# Finger opening sums
HALF_OPEN_SUM = 2 * FINGER_HALF_OPEN_POS  # 0.012
FULL_OPEN_SUM = 2 * FINGER_OPEN_POS  # 0.08

# Groove spring: simulates clip snap retention (physical snap impossible in VBD)
GROOVE_SPRING_KE = 50.0  # [N/m]
GROOVE_SPRING_KD = 0.5  # [N·s/m]
GROOVE_SPRING_RADIUS = 0.025  # 25mm — covers VBD settle drift (~20mm observed)


def _gradual_finger(dist, ori_dist, ori_thresh, ramp_dist):
    """Gradual finger target: OPEN→CLOSE linearly as dist decreases, gated by ori."""
    if ori_dist > ori_thresh:
        return FINGER_OPEN_POS
    alpha = max(0.0, min(1.0, 1.0 - dist / ramp_dist))
    return FINGER_OPEN_POS + alpha * (FINGER_CLOSE_POS - FINGER_OPEN_POS)


class NewtonGripEnv(VecEnv):
    """RSL-RL VecEnv for unified Clamp/Unclamp -- auto-close fingers (B1).

    mode="clamp":   P0=arms near cable (<5mm), fingers OPEN. Task: close fingers.
                    12D action (arm EE only), fingers auto-close when aligned.
    mode="unclamp": P0=arms at clip, L=HALF_OPEN, R=OPEN. Task: open left finger.
                    DEPRECATED for RL (scripted). Kept for reference.

    Clamp mode: 42D obs, 12D action, auto-close via pos+ori threshold.
    """

    # Action scaling
    POS_ACTION_SCALE = 0.015
    ROT_ACTION_SCALE = 0.05
    EE_XY_BOUND = 0.050  # 50mm: max XY drift from settled position (prevents Brownian walk)
    EE_MAX_ROT_DEV = 0.5  # 0.5 rad (~29°): max rotation deviation from settled orientation
    FINGER_CMD_SCALE = FINGER_STEP_SIZE  # 1mm per RL step (legacy 14D)
    ADAPTIVE_POS_SCALE = True
    # Gradual finger close: finger_target = OPEN + (CLOSE-OPEN) * clamp(1 - dist/RAMP, 0, 1)
    FINGER_RAMP_DIST = (
        0.020  # 20mm: gradual close starts at this distance (implicit finger threshold aligns with T_DIST=2mm)
    )
    FINGER_CLOSE_ORI_THRESH = 1.0  # ~57deg: relaxed gate so fingers can close during orientation correction
    FINE_THRESHOLD = 0.015
    MIN_POS_SCALE = 0.003
    PHYSICS_STEPS_PER_RL = 10
    EXPLOSION_DIST_THRESH = 1.0
    GRIP_SEG_WINDOW = 20  # full cable coverage (40 segments) — prevents stale index bugs
    INIT_POS_NOISE = 0.012  # 12mm 3D sphere around target (matches T_DIST_APPROACH handoff)

    # Reward weights (clamp mode) -- positive reward: exp(-d/s) in [0,1]
    CLAMP_W_POS = 0.6
    CLAMP_W_ORI = 0.4
    CLAMP_RANGE_POS = 0.015  # tight range for gradient at 0-17mm operating distances
    CLAMP_RANGE_ORI = 1.50

    # Per-arm milestone bonuses (clamp mode) -- intermediate reward bridges
    CLAMP_MILESTONE_DIST_1 = 0.005  # 5mm: first milestone
    CLAMP_MILESTONE_DIST_2 = T_DIST  # 2mm: second milestone (= success threshold)
    R_MILESTONE_1 = 2.0  # per-arm, one-time
    R_MILESTONE_2 = 5.0  # per-arm, one-time
    R_JOINT_CLOSE = 5.0  # both arms < threshold simultaneously, one-time

    # Reward weights (unclamp mode)
    UNCLAMP_W_FINGER = 0.3
    UNCLAMP_W_SEATED = 0.3
    UNCLAMP_W_COUPLED = 0.4
    UNCLAMP_RANGE_SEATED = 0.005
    UNCLAMP_RANGE_ORI = 0.5

    # Shared reward
    PROGRESS_SCALE = 2.0
    R_STEP_BONUS = 5.0
    R_TASK_BONUS = 20.0
    R_PENALTY = -0.01
    R_DROP = -5.0  # Unclamp: cable fell out of groove

    # Success thresholds
    CLAMP_DIST_THRESH = T_DIST  # 2mm
    CLAMP_ORI_THRESH = T_ALIGN  # 10deg
    CLAMP_FINGER_THRESH = T_FINGER  # 12mm
    CLAMP_SUSTAIN = K_CLAMP  # 5 (design doc: sustained K=5)

    UNCLAMP_FINGER_OPEN_THRESH = 2 * (FINGER_OPEN_POS - 0.003)  # 0.074
    UNCLAMP_SEATED_POS_THRESH = T_GROOVE  # 3mm
    UNCLAMP_SEATED_ORI_THRESH = T_SEAT  # cos > 0.85
    UNCLAMP_SUSTAIN = K_UNCLAMP  # 5 (design doc: sustained K=5)
    UNCLAMP_MIN_GROOVE_BODIES = GROOVE_BODIES_MIN  # 2
    DROP_Z_THRESH = TABLE_HEIGHT - 0.02  # 20mm below table

    # Clip C1 pose (constant obs)
    CLIP1_POS = np.array([CLIP1_X, CLIP1_Y, CLIP1_Z], dtype=np.float32)
    CLIP1_QUAT_XYZW = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    GROOVE_CENTER_POS = np.array([CLIP1_X, CLIP1_Y, GROOVE_CENTER_Z], dtype=np.float32)
    # C1 groove runs along Y → cable tangent=[0,1,0] → hand quat = BASE_HAND_DOWN_QUAT
    GROOVE_TARGET_QUAT = normalize_quat_w_positive(BASE_HAND_DOWN_QUAT.copy())

    MAX_EPISODE_STEPS = GRIP_TERMINAL_STEPS  # Consistent with AC/AR/IC envs

    # Cache
    CACHE_DIR = os.path.join(_env_dir, "..", "data", "rl_grip_cache")
    # v9->v10_ps2: joint-seed restore (c11); pre-PS2 caches = kinematic-lineage states, invalidated.
    CACHE_VERSION = "v10_ps2"

    def __init__(self, world_count=4, device="cuda:0", mode="clamp", cfg=None, dual_arm=False):
        assert mode in ("clamp", "unclamp"), f"Invalid mode: {mode}"
        self._mode = mode
        self._dual_arm = dual_arm
        if dual_arm:
            self.num_envs = world_count
            self.num_actions = 14  # 12D EE + 2D finger
        else:
            # 2-agent: each arm is an independent env. 2N RL envs for N worlds.
            self.num_envs = world_count * 2
            self.num_actions = 6  # per-arm: EE delta XYZ(3) + rotation(3)
        self._total_env_steps = 0
        self.max_episode_length = GRIP_TERMINAL_STEPS
        self.device = device
        self.cfg = cfg or {}
        self._expected_arm = self.cfg.get("expected_arm", "both")
        if self._expected_arm not in EXPECTED_ARMS:
            raise ValueError(f"Invalid expected_arm: {self._expected_arm!r}. Expected one of {sorted(EXPECTED_ARMS)}.")
        self._expected_arm_code = {"both": 0, "right": 1, "left": 2}[self._expected_arm]
        self._world_count = world_count
        # PS-1 (Rs 2026-07-19 kinematic complete-removal; design sec14.15/14.17): the arm is driven
        # by the POSITION-servo ctrl path ONLY. Flag mirrors the (d) route-env rollout; default OFF
        # keeps the legacy build byte-identical but the per-step arm drive then FAILS CLOSED.
        self._arm_pd_drive = os.environ.get("ARM_PD_DRIVE") == "1"

        # episode_length_buf is per-world (both arms share episode lifecycle)
        self._world_episode_length = torch.zeros(world_count, dtype=torch.long, device=device)
        # RSL-RL expects episode_length_buf of shape [num_envs]
        self.episode_length_buf = torch.zeros(self.num_envs, dtype=torch.long, device=device)
        self._target_seg_indices_r = None
        self._target_seg_indices_l = None
        self._groove_seg_indices = None
        self._success_sustain_count = np.zeros(world_count, dtype=np.int32)
        self._step_bonus_given_r = np.zeros(world_count, dtype=bool)
        self._step_bonus_given_l = np.zeros(world_count, dtype=bool)
        # Clamp milestone tracking (per-arm, per-world, one-time per episode)
        self._clamp_ms1_r = np.zeros(world_count, dtype=bool)  # dist < 5mm
        self._clamp_ms1_l = np.zeros(world_count, dtype=bool)
        self._clamp_ms2_r = np.zeros(world_count, dtype=bool)  # dist < 2mm
        self._clamp_ms2_l = np.zeros(world_count, dtype=bool)
        self._clamp_joint_ms = np.zeros(world_count, dtype=bool)  # both < threshold
        self._episode_count = 0
        self._episode_success_buf = deque(maxlen=200)
        self._last_success_rate = 0.0

        # Per-world EE targets
        self._ee_target_right = np.zeros((world_count, 3), dtype=np.float32)
        self._ee_target_left = np.zeros((world_count, 3), dtype=np.float32)
        self._ee_quat_right = np.zeros((world_count, 4), dtype=np.float32)
        self._ee_quat_left = np.zeros((world_count, 4), dtype=np.float32)

        # Temporal quaternion consistency
        _id4 = np.array([0, 0, 0, 1], dtype=np.float32)
        self._prev_clamp_r_quat = np.tile(_id4, (world_count, 1))
        self._prev_clamp_l_quat = np.tile(_id4, (world_count, 1))
        self._prev_seg_r_quat = np.tile(_id4, (world_count, 1))
        self._prev_seg_l_quat = np.tile(_id4, (world_count, 1))
        self._prev_seg_quat = np.tile(_id4, (world_count, 1))

        # Auto-close state (B1: clamp mode uses 12D + auto-close)
        self._finger_closed_right = np.zeros(world_count, dtype=bool)
        self._finger_closed_left = np.zeros(world_count, dtype=bool)

        # Override device for Newton
        os.environ["NEWTON_DEVICE"] = device
        _tncr.DEVICE = device

        print(f"[GripEnv:{mode}] Initializing: {world_count} worlds on {device}, expected_arm={self._expected_arm}")
        t0 = time.perf_counter()

        self._build_model()

        if not self._load_and_restore_cache():
            if mode == "clamp":
                self._build_p0_clamp()
            else:
                self._build_p0_unclamp()

        self._init_dynamic_fingers()
        self._init_batched_ik_solver()

        print(
            f"[GripEnv:{mode}] Ready in {time.perf_counter() - t0:.1f}s. "
            f"obs={self.num_obs}, act={self.num_actions}, worlds={world_count}"
        )

    # =========================================================================
    # Model Construction
    # =========================================================================

    def _build_model(self):
        """Build FK model + multi-world physics scene with target clip."""
        print(f"[GripEnv:{self._mode}] Building FK model...")

        if self._mode == "clamp":
            finger_l, finger_r = FINGER_OPEN_POS, FINGER_OPEN_POS
        else:
            finger_l, finger_r = FINGER_HALF_OPEN_POS, FINGER_OPEN_POS

        self._fk_model, self._fk_state, fk_jq = build_fk_and_init(
            left_finger_pos=finger_l,
            right_finger_pos=finger_r,
            device=self.device,
        )
        self._per_world_fk_jq = np.tile(fk_jq, (self._world_count, 1))

        print(f"[GripEnv:{self._mode}] Building scene ({self._world_count} worlds)...")
        scene = build_multiworld_scene(
            self._fk_model,
            self._fk_state,
            self._world_count,
            self.device,
            add_support_clips=(self._mode == "clamp"),
            add_target_clip=True,
        )

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
        self._jws = self._model.joint_world_start.numpy()

        # PS-1: per-world qd indices of the 2*JOINTS_PER_ARM robot joint columns (joint_target_pos
        # is qd-indexed). Robot joints lead each world's joint slice; the cable chain follows.
        _jqds = self._model.joint_qd_start.numpy()
        self._arm_qd_idx = np.stack(
            [
                np.array([int(_jqds[self._jws[w] + k]) for k in range(2 * JOINTS_PER_ARM)], dtype=np.int64)
                for w in range(self._world_count)
            ]
        )
        if self._arm_pd_drive:
            # PS-1 census (ports the (d) L-P6 asserts; grip builds WITHOUT gripper servos so the
            # expected actuator population is EXACTLY the 12 proto-wired arm servos, B1-strip clean).
            import mujoco as _ps1_mj

            _ps1_m = self._solver.mj_model
            _ps1_scale = float(os.environ.get("ARM_PD_GAINS_SCALE", "1.0"))
            _ps1_ke_scale = float(os.environ.get("ARM_PD_KE_SCALE", str(_ps1_scale)))
            _ps1_arm_acts = []
            for a in range(int(_ps1_m.nu)):
                j = int(np.asarray(_ps1_m.actuator_trnid)[a, 0])
                jn = _ps1_mj.mj_id2name(_ps1_m, _ps1_mj.mjtObj.mjOBJ_JOINT, j) or ""
                if "ur5e" in jn:
                    _ps1_arm_acts.append(a)
            assert int(_ps1_m.nu) == 12 and len(_ps1_arm_acts) == 12, (
                f"grip PS-1 census (B1-strip): nu={int(_ps1_m.nu)}, arm-mapped={len(_ps1_arm_acts)} "
                "(expected exactly the 12 proto-wired arm servos; imported actuators must be ABSENT)"
            )
            _ps1_jtm = self._model.joint_target_mode.numpy()
            _ps1_ke = self._model.joint_target_ke.numpy()
            _ps1_pos = int(newton.JointTargetMode.POSITION)
            for w in range(self._world_count):
                for _base in (0, JOINTS_PER_ARM):
                    for _li in range(6):
                        d = int(self._arm_qd_idx[w, _base + _li])
                        eke = (2000.0 if _li < 3 else 500.0) * _ps1_ke_scale
                        assert int(_ps1_jtm[d]) == _ps1_pos, f"grip PS-1 census: dof {d} mode {_ps1_jtm[d]}"
                        assert abs(float(_ps1_ke[d]) - eke) < 1e-3, (
                            f"grip PS-1 census: dof {d} ke {_ps1_ke[d]} != {eke}"
                        )
            print(f"[GripEnv:{self._mode}] PS-1 census PASS: nu=12 arm servos wired (B1-strip clean)")

        print(f"[GripEnv:{self._mode}] Model: {self._model.body_count} bodies, {self._model.joint_count} joints")

    # =========================================================================
    # P0 Precondition: Clamp mode
    # =========================================================================

    def _build_p0_clamp(self):
        """P0 for clamp: settle cable, IK arms to cable height, fingers OPEN."""
        print("[GripEnv:clamp] Building P0 from scratch...")

        for _ in range(SETTLE_STEPS):
            self._physics_step_all()

        # Arms flanking cable: ±5mm offset along Y so each arm grips a different cable segment.
        # Keeps dist_pos ≈5mm (within CLAMP_RANGE_POS=15mm effective gradient zone).
        _P0_Y_OFFSET = 0.005
        target_l = wp.vec3(GRASP_X, CLIP1_Y - _P0_Y_OFFSET, GRIP_Z)
        target_r = wp.vec3(GRASP_X, CLIP1_Y + _P0_Y_OFFSET, GRIP_Z)
        jq_solved = solve_ik_single(self._fk_model, self._fk_state, target_l, target_r, self.device)

        jq_solved[GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
        jq_solved[GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS
        jq_solved[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
        jq_solved[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS

        self._fk_state.joint_q.assign(jq_solved)
        newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)

        # NO-KINEMATIC (c11, PS-3): arms placed by the sanctioned build-time joint seed (once,
        # before the next physics step) + servo hold; body poses follow via eval_fk.
        self._seed_robot_joint_row(jq_solved, range(self._world_count), "p0-clamp")

        for _ in range(SETTLE_STEPS):
            self._physics_step_all()

        wp.synchronize()
        self._settled_body_q = self._state_0.body_q.numpy().copy()
        self._settled_body_qd = self._state_0.body_qd.numpy().copy()
        self._settled_fk_jq = jq_solved.copy()

        self._finish_p0_setup()
        self._save_cache()
        print("[GripEnv:clamp] P0 built and cached")

    # =========================================================================
    # P0 Precondition: Unclamp mode
    # =========================================================================

    def _build_p0_unclamp(self):
        """P0 for unclamp: arms at clip, L=HALF_OPEN, cable teleported to groove."""
        print("[GripEnv:unclamp] Building P0 from scratch...")

        ee_left = (CLIP1_X, CLIP1_Y - GRIP_HALF_SPAN, PUSH_Z)
        ee_right = (CLIP1_X, CLIP1_Y + GRIP_HALF_SPAN, PUSH_Z)
        jq_target = solve_ik_single(self._fk_model, self._fk_state, wp.vec3(*ee_left), wp.vec3(*ee_right), self.device)
        if np.any(np.isnan(jq_target)):
            raise RuntimeError("[GripEnv:unclamp] IK failed for P0")

        jq_target[GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_HALF_OPEN_POS
        jq_target[GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_HALF_OPEN_POS
        jq_target[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
        jq_target[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS

        self._fk_state.joint_q.assign(jq_target)
        newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)
        for w in range(self._world_count):
            self._per_world_fk_jq[w] = jq_target.copy()

        # NO-KINEMATIC (c11, PS-3): arms placed by the sanctioned build-time joint seed + servo
        # hold; the cable's groove-line placement is an OBJECT episode-boundary init done
        # JOINT-SPACE via the CABLE-SEED path (straight chain at the groove: free root at the
        # groove start, zero bend angles) -- the former body teleport is REMOVED.
        self._seed_robot_joint_row(jq_target, range(self._world_count), "p0-unclamp")
        cable_half_len = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
        cable_y_start = CLIP1_Y - cable_half_len
        _uc_root7 = np.array([CLIP1_X, cable_y_start, GROOVE_CENTER_Z, 0.0, 0.0, 0.0, 1.0], dtype=np.float64)
        _uc_seg0 = np.zeros(self._cable_bodies_per_world - 1, dtype=np.float64)
        for w in range(self._world_count):
            cable_joints_w = list(
                range(
                    self._jws[w] + 2 * JOINTS_PER_ARM,
                    self._jws[w] + 2 * JOINTS_PER_ARM + self._cable_bodies_per_world,
                )
            )
            seed_cable_joint_state(self._state_0, self._model, cable_joints_w, _uc_root7, _uc_seg0, dr_xy=(0.0, 0.0))

        # Reset Dahl friction
        if hasattr(self._solver, "enable_dahl_friction") and self._solver.enable_dahl_friction:
            if self._solver.joint_C_fric is not None:
                self._solver.joint_C_fric.zero_()
            if self._solver.joint_sigma_prev is not None:
                self._solver.joint_sigma_prev.zero_()

        # NO-KINEMATIC (c11, PS-3): the VBD-era Z-clamped settle (per-frame arm FK broadcast +
        # cable XZ hard-clamp + velocity zeroing = kinematic interventions) is REMOVED. The settle
        # is PHYSICAL: the servo holds the arms, the groove spring (a force) retains the cable.
        # Whether the unclamp P0 remains buildable under pure physics on the mujoco substrate is
        # run-fenced (grip P-D1-analog leg) -- if the cable escapes the groove here, that is the
        # physical truth, reported by the settle telemetry below, not masked.
        SETTLE_FRAMES = 100
        print(f"[GripEnv:unclamp] settling ({SETTLE_FRAMES} frames; servo hold + groove spring, physical only)...")
        for settle_i in range(SETTLE_FRAMES):
            self._physics_step_all()
            if settle_i % 20 == 0:
                _dbg_bq = self._state_0.body_q.numpy()
                _dbg_z = np.mean(_dbg_bq[self._cable_bodies[0], 2])
                print(
                    f"  [settle {settle_i:3d}] cable_z={_dbg_z:.4f} delta={((_dbg_z - GROOVE_CENTER_Z) * 1000):.1f}mm"
                )

        wp.synchronize()
        bq_post = self._state_0.body_q.numpy()
        cable_z_w0 = np.mean(bq_post[self._cable_bodies[0], 2])
        print(
            f"[GripEnv:unclamp] Post-settle cable Z: {cable_z_w0:.4f} "
            f"(groove: {GROOVE_CENTER_Z:.4f}, delta: {(cable_z_w0 - GROOVE_CENTER_Z) * 1000:.1f}mm)"
        )

        self._settled_body_q = bq_post.copy()
        self._settled_body_qd = self._state_0.body_qd.numpy().copy()
        self._settled_fk_jq = self._fk_state.joint_q.numpy().copy()

        self._finish_p0_setup()
        self._save_cache()
        print("[GripEnv:unclamp] P0 built and cached")

    # =========================================================================
    # P0 Common Finalization
    # =========================================================================

    def _finish_p0_setup(self):
        """Common P0 finalization after cache load or from-scratch build."""
        self._fk_state.joint_q.assign(self._settled_fk_jq)
        newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)

        for w in range(self._world_count):
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()

        bq = self._settled_body_q
        self._target_seg_indices_r, self._target_seg_indices_l = self._compute_target_seg_indices(bq)

        if self._mode == "unclamp":
            self._groove_seg_indices = self._compute_groove_seg_indices(bq)

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

        print(f"[GripEnv:{self._mode}] P0: EE_R={self._settled_ee_r_pos}, EE_L={self._settled_ee_l_pos}")

    # =========================================================================
    # Cache I/O
    # =========================================================================

    def _cache_path(self):
        return os.path.join(self.CACHE_DIR, f"grip_{self._mode}_w{self._world_count}_{self.CACHE_VERSION}.npz")

    def _save_cache(self):
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        path = self._cache_path()
        np.savez_compressed(
            path,
            body_q=self._settled_body_q,
            body_qd=self._settled_body_qd,
            fk_jq=self._settled_fk_jq,
            world_count=np.array([self._world_count], dtype=np.int32),
            body_count=np.array([self._model.body_count], dtype=np.int32),
        )
        print(f"[GripEnv:{self._mode}] Cache saved to {path}")

    def _load_and_restore_cache(self):
        path = self._cache_path()
        if not os.path.exists(path):
            print(f"[GripEnv:{self._mode}] No cache at {path}")
            return False
        try:
            data = np.load(path)
            if int(data["world_count"][0]) != self._world_count:
                print(f"[GripEnv:{self._mode}] Cache world_count mismatch")
                return False
            if int(data["body_count"][0]) != self._model.body_count:
                print(f"[GripEnv:{self._mode}] Cache body_count mismatch")
                return False

            self._settled_body_q = data["body_q"]
            self._settled_body_qd = data["body_qd"]
            self._settled_fk_jq = data["fk_jq"]
            print(f"[GripEnv:{self._mode}] Loaded cache from {path}")
        except Exception as e:
            print(f"[GripEnv:{self._mode}] Cache load failed: {e}")
            return False

        # NO-KINEMATIC (c11, PS-4): cache restore = the sanctioned joint seed (robot row from the
        # cached FK row + cable derived from the cached settled snapshot); NO body-state writes.
        # Pre-PS2 caches carried kinematic-lineage settled states -> CACHE_VERSION invalidates them.
        self._seed_robot_joint_row(self._settled_fk_jq, range(self._world_count), "cache-restore")
        self._seed_cable_from_snapshot(range(self._world_count))

        if hasattr(self._solver, "enable_dahl_friction") and self._solver.enable_dahl_friction:
            if self._solver.joint_C_fric is not None:
                self._solver.joint_C_fric.zero_()
            if self._solver.joint_sigma_prev is not None:
                self._solver.joint_sigma_prev.zero_()

        self._finish_p0_setup()
        return True

    # =========================================================================
    # Dynamic Finger Spring
    # =========================================================================

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
        print(f"[GripEnv:{self._mode}] Dynamic fingers: {len(self._finger_physics_ids)} bodies")

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

    def _apply_groove_spring(self, ke_override=None, kd_override=None):
        """Apply restoring spring toward groove center for cable bodies inside groove.

        Simulates clip snap retention. XZ force only (Y = cable tangent, free).
        Only active in unclamp mode (clamp mode: cable not yet in groove).
        """
        if self._mode != "unclamp":
            return
        ke = ke_override if ke_override is not None else GROOVE_SPRING_KE
        kd = kd_override if kd_override is not None else GROOVE_SPRING_KD
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
                    body_f[bi][3] += -ke * dx - kd * vx
                    body_f[bi][5] += -ke * dz - kd * vz
        self._state_0.body_f.assign(body_f)

    def _sanitise_body_state(self):
        """Physics-fault DETECTOR (c11, PS-5): the per-substep settled-state RESTORE is REMOVED --
        silently teleporting diverged bodies back masks the fault and is itself a kinematic write.
        INTERIM disposition = fail-closed raise (p5 termination-design pending: option A raise /
        option B route-env-style explosion termination + PPO mask)."""
        bq = self._state_0.body_q.numpy()
        pos = bq[:, :3]
        fix_mask = ~np.isfinite(pos).all(axis=1) | (np.abs(pos) > 5.0).any(axis=1)
        if fix_mask.any():
            raise RuntimeError(
                f"physics fault: {int(fix_mask.sum())} body pose(s) non-finite/divergent -- the "
                "silent settled-state restore is REMOVED (Rs directive 2026-07-19 kinematic "
                "complete-removal); fail-closed pending the p5 termination-design ruling (A/B)"
            )

    def _physics_step_all(
        self, substeps=None, sim_dt=None, fk_batch_bq=None, n_worlds=None, groove_ke=None, groove_kd=None
    ):
        n_sub = substeps if substeps is not None else SIM_SUBSTEPS
        dt = sim_dt if sim_dt is not None else SIM_DT
        for _ in range(n_sub):
            self._state_0.clear_forces()
            self._apply_groove_spring(ke_override=groove_ke, kd_override=groove_kd)
            if fk_batch_bq is not None and n_worlds is not None:
                self._apply_finger_spring(fk_batch_bq, n_worlds)
            self._model.collide(self._state_0, self._contacts)
            self._solver.step(self._state_0, self._state_1, self._control, self._contacts, dt)
            self._state_0, self._state_1 = self._state_1, self._state_0
            self._sanitise_body_state()

    # =========================================================================
    # Target Segment / Groove Computation
    # =========================================================================

    def _compute_target_seg_indices(self, bq):
        n_cable = self._cable_bodies_per_world
        win = self.GRIP_SEG_WINDOW
        n_seg = 2 * win + 1
        result_r = np.zeros((self._world_count, n_seg), dtype=np.int32)
        result_l = np.zeros((self._world_count, n_seg), dtype=np.int32)
        for w in range(self._world_count):
            ws = self._bws[w]
            cable_pos = bq[self._cable_bodies[w], :3]

            right_ee = bq[ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
            right_tip = right_ee.copy()
            right_tip[2] -= EE_TO_FINGERTIP
            right_seg = int(np.argmin(np.linalg.norm(cable_pos - right_tip, axis=1)))
            result_r[w] = np.clip(np.arange(right_seg - win, right_seg + win + 1), 0, n_cable - 1)

            left_ee = bq[ws + EE_BODY_OFFSET][:3]
            left_tip = left_ee.copy()
            left_tip[2] -= EE_TO_FINGERTIP
            left_seg = int(np.argmin(np.linalg.norm(cable_pos - left_tip, axis=1)))
            result_l[w] = np.clip(np.arange(left_seg - win, left_seg + win + 1), 0, n_cable - 1)
        return result_r, result_l

    def _compute_groove_seg_indices(self, bq):
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
    # Batched IK Solver
    # =========================================================================

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

        dof_count = fk_model.joint_dof_count
        body_count = fk_model.body_count
        self._batch_fk_jq = wp.zeros((N, coord_count), dtype=float, device=self.device)
        self._batch_fk_jqd = wp.zeros((N, dof_count), dtype=float, device=self.device)
        self._batch_fk_body_q = wp.zeros((N, body_count), dtype=wp.transform, device=self.device)
        self._batch_fk_body_qd = wp.zeros((N, body_count), dtype=wp.spatial_vector, device=self.device)

        print(f"[GripEnv:{self._mode}] Batched IK solver: n_problems={N}")

    def _solve_ik_batch(self, targets_left_np, targets_right_np, jq_starts_np):
        self._ik_obj_pos_left.set_target_positions(wp.array(targets_left_np, dtype=wp.vec3, device=self.device))
        self._ik_obj_pos_right.set_target_positions(wp.array(targets_right_np, dtype=wp.vec3, device=self.device))
        self._ik_jq_in.assign(jq_starts_np)
        self._ik_solver_batch.step(self._ik_jq_in, self._ik_jq_out, iterations=IK_ITERATIONS_RL, step_size=IK_STEP_SIZE)
        return self._ik_jq_out.numpy()

    # =========================================================================
    # Reset
    # =========================================================================

    def _sample_sphere_noise(self):
        """Uniform random point within sphere of radius INIT_POS_NOISE."""
        d = np.random.randn(3).astype(np.float32)
        norm = np.linalg.norm(d)
        if norm < 1e-8:
            return np.zeros(3, dtype=np.float32)
        d /= norm
        r = self.INIT_POS_NOISE * (np.random.uniform() ** (1.0 / 3.0))
        return d * r

    def _seed_robot_joint_row(self, jq_row, worlds, label):
        """RESET-SEED: the SINGLE sanctioned joint-state write site of this env (pN 18:17 ruling
        adopting the CLAUDE.md once-at-reset init exception; guard RESET_SEED_MANIFEST pins this
        (file, function)). Sets the robot joint columns of the given worlds to ``jq_row``, zeroes
        their joint velocities, and syncs the arm POSITION-servo targets so the servo HOLDS the
        seeded pose from the first step. Body poses follow via eval_fk (engine kinematics from the
        sanctioned seed -- NOT a body-state write by us). Callers: episode reset / P0 build /
        cache restore only -- all episode boundaries, before the next physics step.
        """
        worlds = [int(w) for w in worlds]
        jq = self._state_0.joint_q.numpy()
        jqd = self._state_0.joint_qd.numpy()
        _jqs = self._model.joint_q_start.numpy()
        jtp = self._control.joint_target_pos.numpy()
        for w in worlds:
            for k in range(2 * JOINTS_PER_ARM):
                jq[int(_jqs[self._jws[w] + k])] = float(jq_row[k])
                jqd[int(self._arm_qd_idx[w, k])] = 0.0
            for _base in (0, JOINTS_PER_ARM):
                jtp[self._arm_qd_idx[w, _base : _base + 6]] = jq_row[_base : _base + 6]
        self._state_0.joint_q.assign(jq)
        self._state_0.joint_qd.assign(jqd)
        self._control.joint_target_pos.assign(jtp)
        newton.eval_fk(self._model, self._state_0.joint_q, self._state_0.joint_qd, self._state_0)
        print(
            f"[GripEnv:{self._mode}] RESET-SEED ({label}): robot joints seeded, "
            f"worlds={worlds[:4]}{'...' if len(worlds) > 4 else ''}"
        )

    def _seed_cable_from_snapshot(self, worlds):
        """Cable OBJECT episode-boundary init via the sanctioned CABLE-SEED path: derive the cable
        chain's joint coords from the settled body snapshot (read-only source) and seed them
        joint-space. No body-state writes."""
        for w in worlds:
            w = int(w)
            cable_joints_w = list(
                range(
                    self._jws[w] + 2 * JOINTS_PER_ARM,
                    self._jws[w] + 2 * JOINTS_PER_ARM + self._cable_bodies_per_world,
                )
            )
            root7, seg_angles = derive_cable_joint_q_from_tangents(self._settled_body_q, self._cable_bodies[w])
            seed_cable_joint_state(self._state_0, self._model, cable_joints_w, root7, seg_angles, dr_xy=(0.0, 0.0))

    def _reset_worlds(self, env_ids):
        if len(env_ids) == 0:
            return
        # NO-KINEMATIC (c11, PS-2): the settled BODY-state restore is REMOVED -- the reset is
        # carried by the once-per-boundary joint seed (the :898-era comment's promise is now the
        # code): robot columns from the settled FK row (servo target synced = the servo holds),
        # cable chain re-derived from the settled snapshot via the CABLE-SEED path.
        env_ids_int = [int(w) for w in env_ids]
        self._seed_robot_joint_row(self._settled_fk_jq, env_ids_int, "reset")
        self._seed_cable_from_snapshot(env_ids_int)

        for w in env_ids:
            w = int(w)
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()
            self._step_bonus_given_r[w] = False
            self._step_bonus_given_l[w] = False
            self._clamp_ms1_r[w] = False
            self._clamp_ms1_l[w] = False
            self._clamp_ms2_r[w] = False
            self._clamp_ms2_l[w] = False
            self._clamp_joint_ms[w] = False
            self._success_sustain_count[w] = 0
            self._ee_target_right[w] = self._settled_ee_r_pos.copy()
            self._ee_target_left[w] = self._settled_ee_l_pos.copy()
            self._ee_quat_right[w] = self._settled_ee_r_quat.copy()
            self._ee_quat_left[w] = self._settled_ee_l_quat.copy()

            # Reset temporal quat consistency
            _id4 = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_clamp_r_quat[w] = _id4.copy()
            self._prev_clamp_l_quat[w] = _id4.copy()
            self._prev_seg_r_quat[w] = _id4.copy()
            self._prev_seg_l_quat[w] = _id4.copy()
            self._prev_seg_quat[w] = _id4.copy()
            # Reset auto-close state (B1)
            self._finger_closed_right[w] = False
            self._finger_closed_left[w] = False

            # Init noise: 3D sphere (12mm) — noise EE target only; first step's IK
            # naturally moves the robot to the noised position. Direct body_q noise
            # was undone by FK snapback (C4 fix).
            if self.INIT_POS_NOISE > 0 and self._mode == "clamp":
                noise_r = self._sample_sphere_noise()
                self._ee_target_right[w][:3] += noise_r

                noise_l = self._sample_sphere_noise()
                self._ee_target_left[w][:3] += noise_l

            self._world_episode_length[w] = 0
            if self._dual_arm:
                self.episode_length_buf[w] = 0
            else:
                self.episode_length_buf[2 * w] = 0
                self.episode_length_buf[2 * w + 1] = 0

        # Reset Dahl friction
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

        self._episode_count += len(env_ids)

    # =========================================================================
    # Observation (42D)
    # =========================================================================

    def _compute_obs_batch(self):
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        N = self._world_count
        if self._dual_arm:
            return self._compute_obs_dual_arm(bq, N)
        # 2-agent: [2N, 28] — slot 2w = right arm, 2w+1 = left arm
        obs_np = np.empty((N * 2, 28), dtype=np.float32)

        for w in range(N):
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

            # Cable target segment (mode-dependent query point)
            cable_pos = bq[self._cable_bodies[w], :3]

            if self._mode == "clamp":
                # Per-arm nearest cable point
                seg_pos_r, seg_tangent_r, _ = find_nearest_cable_point(
                    cable_pos, clamp_r_pos, self._target_seg_indices_r[w]
                )
                grasp_quat_r = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_r))
                grasp_quat_r = temporal_quat_consistency(grasp_quat_r, self._prev_seg_r_quat[w])
                self._prev_seg_r_quat[w] = grasp_quat_r.copy()

                seg_pos_l, seg_tangent_l, _ = find_nearest_cable_point(
                    cable_pos, clamp_l_pos, self._target_seg_indices_l[w]
                )
                grasp_quat_l = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_l))
                grasp_quat_l = temporal_quat_consistency(grasp_quat_l, self._prev_seg_l_quat[w])
                self._prev_seg_l_quat[w] = grasp_quat_l.copy()

                ori_error_r = compute_ori_error_axis_angle(clamp_r_quat, grasp_quat_r)
                pos_error_r = clamp_r_pos - seg_pos_r
                ori_error_l = compute_ori_error_axis_angle(clamp_l_quat, grasp_quat_l)
                pos_error_l = clamp_l_pos - seg_pos_l

                clip_pos = self.CLIP1_POS
                clip_quat = self.CLIP1_QUAT_XYZW
            else:
                # Unclamp: groove-nearest cable point (shared for both arms)
                seg_pos, seg_tangent, _ = find_nearest_cable_point(
                    cable_pos, self.GROOVE_CENTER_POS, self._groove_seg_indices[w]
                )
                seg_quat = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent))
                seg_quat = temporal_quat_consistency(seg_quat, self._prev_seg_quat[w])
                self._prev_seg_quat[w] = seg_quat.copy()

                seg_pos_r = seg_pos_l = seg_pos
                grasp_quat_r = grasp_quat_l = seg_quat
                ori_error_r = compute_ori_error_axis_angle(clamp_r_quat, seg_quat)
                pos_error_r = clamp_r_pos - seg_pos
                ori_error_l = compute_ori_error_axis_angle(clamp_l_quat, seg_quat)
                pos_error_l = clamp_l_pos - seg_pos

                clip_pos = self.GROOVE_CENTER_POS
                clip_quat = self.CLIP1_QUAT_XYZW

            # Right arm obs → slot 2w
            obs_np[2 * w, 0:3] = clamp_r_pos
            obs_np[2 * w, 3:7] = clamp_r_quat
            obs_np[2 * w, 7] = r_finger_opening
            obs_np[2 * w, 8:11] = seg_pos_r
            obs_np[2 * w, 11:15] = grasp_quat_r
            obs_np[2 * w, 15:18] = clip_pos
            obs_np[2 * w, 18:22] = clip_quat
            obs_np[2 * w, 22:25] = ori_error_r
            obs_np[2 * w, 25:28] = pos_error_r

            # Left arm obs → slot 2w+1
            obs_np[2 * w + 1, 0:3] = clamp_l_pos
            obs_np[2 * w + 1, 3:7] = clamp_l_quat
            obs_np[2 * w + 1, 7] = l_finger_opening
            obs_np[2 * w + 1, 8:11] = seg_pos_l
            obs_np[2 * w + 1, 11:15] = grasp_quat_l
            obs_np[2 * w + 1, 15:18] = clip_pos
            obs_np[2 * w + 1, 18:22] = clip_quat
            obs_np[2 * w + 1, 22:25] = ori_error_l
            obs_np[2 * w + 1, 25:28] = pos_error_l

        np.nan_to_num(obs_np, copy=False, nan=0.0)
        return torch.from_numpy(obs_np).to(device=self.device)

    def _compute_obs_dual_arm(self, bq, N):
        """Compute 45D dual-arm observations matching unified base model format."""
        obs_np = np.empty((N, 45), dtype=np.float32)
        obs_np[:, 42:45] = 0.0  # Pad dims [42:45] = zeros for IC-compatibility
        for w in range(N):
            ws = self._bws[w]

            # Clamp pose (fingertip position + orientation) for both arms via helper
            clamp_r_pos, clamp_r_quat = extract_clamp_pose(
                bq, ws, FRANKA_NUM_JOINTS + EE_BODY_OFFSET, self._prev_clamp_r_quat[w]
            )
            self._prev_clamp_r_quat[w] = clamp_r_quat.copy()
            clamp_l_pos, clamp_l_quat = extract_clamp_pose(bq, ws, EE_BODY_OFFSET, self._prev_clamp_l_quat[w])
            self._prev_clamp_l_quat[w] = clamp_l_quat.copy()

            fk_jq = self._per_world_fk_jq[w]
            r_finger_opening = (
                fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]]
                + fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]]
            )
            l_finger_opening = fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] + fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]]

            cable_pos = bq[self._cable_bodies[w], :3]

            if self._mode == "clamp":
                seg_pos_r, seg_tangent_r, _ = find_nearest_cable_point(
                    cable_pos, clamp_r_pos, self._target_seg_indices_r[w]
                )
                grasp_quat_r = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_r))
                grasp_quat_r = temporal_quat_consistency(grasp_quat_r, self._prev_seg_r_quat[w])
                self._prev_seg_r_quat[w] = grasp_quat_r.copy()

                seg_pos_l, seg_tangent_l, _ = find_nearest_cable_point(
                    cable_pos, clamp_l_pos, self._target_seg_indices_l[w]
                )
                grasp_quat_l = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_l))
                grasp_quat_l = temporal_quat_consistency(grasp_quat_l, self._prev_seg_l_quat[w])
                self._prev_seg_l_quat[w] = grasp_quat_l.copy()

                ori_error_r = compute_ori_error_axis_angle(clamp_r_quat, grasp_quat_r)
                pos_error_r = clamp_r_pos - seg_pos_r
                ori_error_l = compute_ori_error_axis_angle(clamp_l_quat, grasp_quat_l)
                pos_error_l = clamp_l_pos - seg_pos_l
                seg_pos = seg_pos_r
                seg_quat = grasp_quat_r
                clip_pos = self.CLIP1_POS
                clip_quat = self.CLIP1_QUAT_XYZW
            else:
                seg_pos, seg_tangent, _ = find_nearest_cable_point(
                    cable_pos, self.GROOVE_CENTER_POS, self._groove_seg_indices[w]
                )
                seg_quat = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent))
                seg_quat = temporal_quat_consistency(seg_quat, self._prev_seg_quat[w])
                self._prev_seg_quat[w] = seg_quat.copy()
                ori_error_r = compute_ori_error_axis_angle(clamp_r_quat, seg_quat)
                pos_error_r = clamp_r_pos - seg_pos
                ori_error_l = compute_ori_error_axis_angle(clamp_l_quat, seg_quat)
                pos_error_l = clamp_l_pos - seg_pos
                clip_pos = self.GROOVE_CENTER_POS
                clip_quat = self.CLIP1_QUAT_XYZW

            # AC/AR 42D format
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
    # Reward / Done (mode-dependent)
    # =========================================================================

    def _compute_rewards_dones_batch(self):
        if self._mode == "clamp":
            return self._compute_rewards_clamp()
        return self._compute_rewards_unclamp()

    def _select_clamp_success(self, clamp_r_ok: bool, clamp_l_ok: bool) -> bool:
        """Select the clamp success predicate for the configured expected arm."""
        if self._expected_arm == "right":
            return clamp_r_ok
        if self._expected_arm == "left":
            return clamp_l_ok
        return clamp_r_ok and clamp_l_ok

    def _compute_rewards_clamp(self):
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        N = self._world_count
        E = N if self._dual_arm else N * 2

        rewards = np.zeros(E, dtype=np.float32)
        dones = np.zeros(E, dtype=np.int64)
        timeouts = np.zeros(E, dtype=np.int64)
        successes = np.zeros(N, dtype=np.float32)  # per-world success
        rc_dist_r = np.zeros(N, dtype=np.float32)
        rc_dist_l = np.zeros(N, dtype=np.float32)
        rc_ori_r = np.zeros(N, dtype=np.float32)
        rc_ori_l = np.zeros(N, dtype=np.float32)
        rc_finger_r = np.zeros(N, dtype=np.float32)
        rc_finger_l = np.zeros(N, dtype=np.float32)
        rc_explosion = np.zeros(N, dtype=np.bool_)
        rc_clamp_r_ok = np.zeros(N, dtype=np.bool_)
        rc_clamp_l_ok = np.zeros(N, dtype=np.bool_)
        rc_selected_success = np.zeros(N, dtype=np.bool_)
        rc_selected_sustain = np.zeros(N, dtype=np.int32)
        rc_target_seg_idx_r = np.zeros(N, dtype=np.int32)
        rc_target_seg_idx_l = np.zeros(N, dtype=np.int32)

        for w in range(N):
            ws = self._bws[w]

            ee_r_idx = ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
            ee_r_pos = bq[ee_r_idx][:3]
            ee_r_quat = bq[ee_r_idx][3:7]
            clamp_r_pos = compute_clamp_pos(ee_r_pos, ee_r_quat)
            clamp_r_quat = normalize_quat_w_positive(ee_r_quat)

            ee_l_idx = ws + EE_BODY_OFFSET
            ee_l_pos = bq[ee_l_idx][:3]
            ee_l_quat = bq[ee_l_idx][3:7]
            clamp_l_pos = compute_clamp_pos(ee_l_pos, ee_l_quat)
            clamp_l_quat = normalize_quat_w_positive(ee_l_quat)

            cable_pos = bq[self._cable_bodies[w], :3]

            _, seg_tangent_r, dist_pos_r = find_nearest_cable_point(
                cable_pos, clamp_r_pos, self._target_seg_indices_r[w]
            )
            grasp_quat_r = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_r))
            dist_ori_r = quat_distance(clamp_r_quat, grasp_quat_r)

            _, seg_tangent_l, dist_pos_l = find_nearest_cable_point(
                cable_pos, clamp_l_pos, self._target_seg_indices_l[w]
            )
            grasp_quat_l = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_l))
            dist_ori_l = quat_distance(clamp_l_quat, grasp_quat_l)

            fk_jq = self._per_world_fk_jq[w]
            finger_r = (
                fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]]
                + fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]]
            )
            finger_l = fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] + fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]]
            finite_measurements = all(
                math.isfinite(v) for v in (dist_pos_r, dist_pos_l, dist_ori_r, dist_ori_l, finger_r, finger_l)
            )

            # Per-arm rewards: positive exp [0,1] + milestone bonuses
            def _arm_reward(dist_pos, dist_ori):
                r_pos = math.exp(-dist_pos / self.CLAMP_RANGE_POS)
                r_ori = math.exp(-dist_ori / self.CLAMP_RANGE_ORI)
                return self.PROGRESS_SCALE * (self.CLAMP_W_POS * r_pos + self.CLAMP_W_ORI * r_ori)

            r_main_r = _arm_reward(dist_pos_r, dist_ori_r)
            r_main_l = _arm_reward(dist_pos_l, dist_ori_l)

            # Per-arm milestone bonuses (one-time per episode)
            r_ms_r = 0.0
            r_ms_l = 0.0
            if not self._clamp_ms1_r[w] and dist_pos_r < self.CLAMP_MILESTONE_DIST_1:
                r_ms_r += self.R_MILESTONE_1
                self._clamp_ms1_r[w] = True
            if not self._clamp_ms1_l[w] and dist_pos_l < self.CLAMP_MILESTONE_DIST_1:
                r_ms_l += self.R_MILESTONE_1
                self._clamp_ms1_l[w] = True
            if not self._clamp_ms2_r[w] and dist_pos_r < self.CLAMP_MILESTONE_DIST_2:
                r_ms_r += self.R_MILESTONE_2
                self._clamp_ms2_r[w] = True
            if not self._clamp_ms2_l[w] and dist_pos_l < self.CLAMP_MILESTONE_DIST_2:
                r_ms_l += self.R_MILESTONE_2
                self._clamp_ms2_l[w] = True

            # Joint milestone: both arms within threshold simultaneously
            r_joint_val = 0.0
            explosion = (
                not finite_measurements
                or dist_pos_r > self.EXPLOSION_DIST_THRESH
                or dist_pos_l > self.EXPLOSION_DIST_THRESH
            )
            rc_explosion[w] = explosion
            clamp_r_ok = finite_measurements and (
                dist_pos_r < self.CLAMP_DIST_THRESH
                and dist_ori_r < self.CLAMP_ORI_THRESH
                and finger_r < self.CLAMP_FINGER_THRESH
            )
            clamp_l_ok = finite_measurements and (
                dist_pos_l < self.CLAMP_DIST_THRESH
                and dist_ori_l < self.CLAMP_ORI_THRESH
                and finger_l < self.CLAMP_FINGER_THRESH
            )
            selected_success = self._select_clamp_success(clamp_r_ok, clamp_l_ok) and not explosion
            if clamp_r_ok and clamp_l_ok:
                if not self._clamp_joint_ms[w]:
                    r_joint_val = self.R_JOINT_CLOSE
                    self._clamp_joint_ms[w] = True
            if selected_success:
                self._success_sustain_count[w] += 1
            else:
                self._success_sustain_count[w] = 0
            success = self._success_sustain_count[w] >= self.CLAMP_SUSTAIN and not explosion

            r_task_val = self.R_TASK_BONUS if success else 0.0
            timeout = self._world_episode_length[w].item() >= self.max_episode_length
            done = success or timeout or explosion

            if self._dual_arm:
                # Dual-arm: combine both arms' rewards into single per-world value
                rewards[w] = r_main_r + r_ms_r + r_main_l + r_ms_l + r_joint_val + r_task_val + self.R_PENALTY
                dones[w] = int(done)
                timeouts[w] = int(timeout)
            else:
                # Per-arm: separate rewards for each arm slot
                rewards[2 * w] = r_main_r + r_ms_r + r_joint_val + r_task_val + self.R_PENALTY
                rewards[2 * w + 1] = r_main_l + r_ms_l + r_joint_val + r_task_val + self.R_PENALTY
                dones[2 * w] = dones[2 * w + 1] = int(done)
                # BUG-1 fix: explosion is a true terminal state (value=0),
                # not a timeout (which would bootstrap γV(s)).
                timeouts[2 * w] = timeouts[2 * w + 1] = int(timeout)
            successes[w] = float(success)
            if done:
                self._episode_success_buf.append(float(success))
            rc_dist_r[w] = dist_pos_r
            rc_dist_l[w] = dist_pos_l
            rc_ori_r[w] = dist_ori_r
            rc_ori_l[w] = dist_ori_l
            rc_finger_r[w] = finger_r
            rc_finger_l[w] = finger_l
            rc_clamp_r_ok[w] = clamp_r_ok
            rc_clamp_l_ok[w] = clamp_l_ok
            rc_selected_success[w] = selected_success
            rc_selected_sustain[w] = self._success_sustain_count[w]
            rc_target_seg_idx_r[w] = self._target_seg_indices_r[w]
            rc_target_seg_idx_l[w] = self._target_seg_indices_l[w]

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
                    "/reward/r_main_r": float(np.mean(rewards[0::2]))
                    if not self._dual_arm
                    else float(np.mean(rewards)),
                    "/reward/r_main_l": float(np.mean(rewards[1::2]))
                    if not self._dual_arm
                    else float(np.mean(rewards)),
                    "/reward/r_total": float(np.mean(rewards)),
                    "/metrics/dist_pos_median": float(np.median(np.concatenate([rc_dist_r, rc_dist_l]))),
                    "/metrics/dist_pos_r_median": float(np.median(rc_dist_r)),
                    "/metrics/dist_pos_l_median": float(np.median(rc_dist_l)),
                    "/metrics/dist_ori_r_median": float(np.median(rc_ori_r)),
                    "/metrics/dist_ori_l_median": float(np.median(rc_ori_l)),
                    "/metrics/finger_r_mean": float(np.mean(rc_finger_r)),
                    "/metrics/finger_l_mean": float(np.mean(rc_finger_l)),
                    "/metrics/clamp_r_ok_rate": float(np.mean(rc_clamp_r_ok)),
                    "/metrics/clamp_l_ok_rate": float(np.mean(rc_clamp_l_ok)),
                    "/metrics/selected_success_rate": float(np.mean(rc_selected_success)),
                    "/metrics/both_success_rate": float(np.mean(rc_clamp_r_ok & rc_clamp_l_ok)),
                    "/metrics/expected_arm_code": float(self._expected_arm_code),
                    "/metrics/selected_sustain_mean": float(np.mean(rc_selected_sustain)),
                    "/metrics/selected_sustain_max": int(np.max(rc_selected_sustain)),
                    "/reward/r_task_selected": float(self.R_TASK_BONUS * np.mean(successes)),
                    "/metrics/auto_close_r_pct": float(np.mean(self._finger_closed_right[:N])),
                    "/metrics/auto_close_l_pct": float(np.mean(self._finger_closed_left[:N])),
                    "/metrics/explosion_count": int(
                        np.sum((rc_dist_r > self.EXPLOSION_DIST_THRESH) | (rc_dist_l > self.EXPLOSION_DIST_THRESH))
                    ),
                    "/metrics/ms1_r_pct": float(np.mean(self._clamp_ms1_r[:N])),
                    "/metrics/ms1_l_pct": float(np.mean(self._clamp_ms1_l[:N])),
                    "/metrics/ms2_r_pct": float(np.mean(self._clamp_ms2_r[:N])),
                    "/metrics/ms2_l_pct": float(np.mean(self._clamp_ms2_l[:N])),
                    "/metrics/joint_ms_pct": float(np.mean(self._clamp_joint_ms[:N])),
                },
                "log_per_world": {
                    "dist_pos_r": rc_dist_r.copy(),
                    "dist_pos_l": rc_dist_l.copy(),
                    "dist_ori_r": rc_ori_r.copy(),
                    "dist_ori_l": rc_ori_l.copy(),
                    "finger_r": rc_finger_r.copy(),
                    "finger_l": rc_finger_l.copy(),
                    "reward": rewards.copy(),
                    "success": successes.copy(),
                    "explosion": rc_explosion.copy(),
                    "clamp_r_ok": rc_clamp_r_ok.copy(),
                    "clamp_l_ok": rc_clamp_l_ok.copy(),
                    "selected_instant_success": rc_selected_success.copy(),
                    "selected_sustain_count": rc_selected_sustain.copy(),
                    "expected_arm_code": np.full(N, self._expected_arm_code, dtype=np.int32),
                    "target_seg_idx_r": rc_target_seg_idx_r.copy(),
                    "target_seg_idx_l": rc_target_seg_idx_l.copy(),
                },
            },
        )

    def _compute_rewards_unclamp(self):
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        N = self._world_count
        clip_pos_xy = np.array([CLIP1_X, CLIP1_Y])

        rewards = np.zeros(N, dtype=np.float32)
        dones = np.zeros(N, dtype=np.int64)
        timeouts = np.zeros(N, dtype=np.int64)
        successes = np.zeros(N, dtype=np.float32)
        rc_score_finger = np.zeros(N, dtype=np.float32)
        rc_score_seated = np.zeros(N, dtype=np.float32)
        rc_seated_dist = np.zeros(N, dtype=np.float32)
        rc_finger_opening = np.zeros(N, dtype=np.float32)
        rc_groove_bodies = np.zeros(N, dtype=np.float32)
        rc_drop = np.zeros(N, dtype=np.float32)
        rc_explosion = np.zeros(N, dtype=np.bool_)

        for w in range(N):
            cable_pos = bq[self._cable_bodies[w], :3]
            seg_pos, seg_tangent, _ = find_nearest_cable_point(
                cable_pos, self.GROOVE_CENTER_POS, self._groove_seg_indices[w]
            )
            seg_quat = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent))

            dist_pos = float(np.linalg.norm(seg_pos - self.GROOVE_CENTER_POS))
            dist_ori = quat_distance(seg_quat, self.GROOVE_TARGET_QUAT)

            fk_jq = self._per_world_fk_jq[w]
            finger_opening = fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] + fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]]

            # Finger progress: 0 at HALF_OPEN, 1 at FULL_OPEN
            score_finger = np.clip((finger_opening - HALF_OPEN_SUM) / (FULL_OPEN_SUM - HALF_OPEN_SUM), 0.0, 1.0)

            # Seated score
            score_seated_pos = math.exp(-dist_pos / self.UNCLAMP_RANGE_SEATED)
            score_seated_ori = math.exp(-dist_ori / self.UNCLAMP_RANGE_ORI)
            score_seated = 0.5 * score_seated_pos + 0.5 * score_seated_ori

            progress = (
                self.UNCLAMP_W_FINGER * score_finger
                + self.UNCLAMP_W_SEATED * score_seated
                + self.UNCLAMP_W_COUPLED * score_finger * score_seated
            )
            r_base = self.PROGRESS_SCALE * (progress - 1.0)

            # Groove bodies count
            dists_xy = np.linalg.norm(cable_pos[:, :2] - clip_pos_xy, axis=1)
            cable_z_near = np.abs(cable_pos[:, 2] - GROOVE_CENTER_Z) < 0.015
            bodies_in_groove = int(np.sum((dists_xy < GROOVE_CHECK_RADIUS) & cable_z_near))

            # Step bonus
            r_step_val = 0.0
            finger_open_ok = finger_opening >= self.UNCLAMP_FINGER_OPEN_THRESH
            seated_pos_ok = dist_pos < self.UNCLAMP_SEATED_POS_THRESH
            cos_sim = abs(float(np.dot(seg_quat, self.GROOVE_TARGET_QUAT)))
            seated_ori_ok = cos_sim > self.UNCLAMP_SEATED_ORI_THRESH
            groove_ok = bodies_in_groove >= self.UNCLAMP_MIN_GROOVE_BODIES

            if finger_open_ok and seated_pos_ok and seated_ori_ok and groove_ok:
                if not self._step_bonus_given_l[w]:
                    r_step_val = self.R_STEP_BONUS
                    self._step_bonus_given_l[w] = True

            # Success: sustained
            if finger_open_ok and seated_pos_ok and seated_ori_ok and groove_ok:
                self._success_sustain_count[w] += 1
            else:
                self._success_sustain_count[w] = 0
            success = self._success_sustain_count[w] >= self.UNCLAMP_SUSTAIN

            r_task_val = self.R_TASK_BONUS if success else 0.0

            # Cable drop
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
            rc_explosion[w] = explosion
            timeout = self._world_episode_length[w].item() >= self.max_episode_length
            done = success or timeout or explosion or cable_dropped

            rewards[w] = r
            dones[w] = int(done)
            timeouts[w] = int(timeout)
            successes[w] = float(success)
            if done:
                self._episode_success_buf.append(float(success))
            rc_score_finger[w] = score_finger
            rc_score_seated[w] = score_seated
            rc_seated_dist[w] = dist_pos
            rc_finger_opening[w] = finger_opening
            rc_groove_bodies[w] = bodies_in_groove
            rc_drop[w] = float(cable_dropped)

        if len(self._episode_success_buf) > 0:
            self._last_success_rate = float(np.mean(self._episode_success_buf))

        # Capture per-world (N-sized) rewards before potential 2N expansion
        rewards_per_world = rewards.copy()

        if not self._dual_arm:
            # Per-arm: expand to 2N for 2-agent interface
            rewards = np.repeat(rewards, 2)
            dones = np.repeat(dones, 2)
            timeouts = np.repeat(timeouts, 2)
        # dual_arm: keep N-sized arrays (single agent per world)
        return (
            torch.tensor(rewards, dtype=torch.float32, device=self.device),
            torch.tensor(dones, dtype=torch.long, device=self.device),
            {
                "observations": {},
                "time_outs": torch.tensor(timeouts, dtype=torch.long, device=self.device),
                "log": {
                    "/episode/success": float(np.mean(successes)),
                    "/metrics/episode_success_rate": self._last_success_rate,
                    "/reward/r_base": float(np.mean(rewards_per_world)),
                    "/reward/r_penalty": float(self.R_PENALTY),
                    "/metrics/score_finger_mean": float(np.mean(rc_score_finger)),
                    "/metrics/score_seated_mean": float(np.mean(rc_score_seated)),
                    "/metrics/seated_dist_mean": float(np.nanmean(rc_seated_dist)),
                    "/metrics/seated_dist_median": float(np.nanmedian(rc_seated_dist)),
                    "/metrics/finger_opening_mean": float(np.mean(rc_finger_opening)),
                    "/metrics/groove_bodies_mean": float(np.mean(rc_groove_bodies)),
                    "/metrics/drop_count": int(np.sum(rc_drop)),
                },
                "log_per_world": {
                    "score_finger": rc_score_finger.copy(),
                    "score_seated": rc_score_seated.copy(),
                    "seated_dist": rc_seated_dist.copy(),
                    "finger_opening": rc_finger_opening.copy(),
                    "groove_bodies": rc_groove_bodies.copy(),
                    "reward": rewards_per_world,
                    "success": successes.copy(),
                    "explosion": rc_explosion.copy(),
                },
            },
        )

    # =========================================================================
    # Action Application (2-agent: [2N, 6] per-arm)
    # =========================================================================

    def _apply_actions_batch(self, actions):
        N = self._world_count
        actions_np = actions.cpu().numpy()

        if self._dual_arm:
            # [N, 14]: [0:3] R pos, [3:6] R rot, [6:9] L pos, [9:12] L rot, [12] R finger, [13] L finger
            r_actions = actions_np[:, 0:6]  # [N, 6]
            l_actions = actions_np[:, 6:12]  # [N, 6]
            r_finger_cmd = actions_np[:, 12]  # [N]
            l_finger_cmd = actions_np[:, 13]  # [N]
        else:
            # [2N, 6]: Deinterleave: slot 2w = right arm, 2w+1 = left arm
            r_actions = actions_np[0::2]  # [N, 6]
            l_actions = actions_np[1::2]  # [N, 6]

        wp.synchronize()
        bq = self._state_0.body_q.numpy()

        # Adaptive pos scaling (clamp mode uses per-arm distance; unclamp uses fixed)
        if self.ADAPTIVE_POS_SCALE and self._mode == "clamp":
            r_pos_scales = np.full(N, self.POS_ACTION_SCALE, dtype=np.float32)
            l_pos_scales = np.full(N, self.POS_ACTION_SCALE, dtype=np.float32)
            for w in range(N):
                ws = self._bws[w]
                cable_pos = bq[self._cable_bodies[w], :3]

                ee_r_idx = ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
                clamp_r = compute_clamp_pos(bq[ee_r_idx][:3], bq[ee_r_idx][3:7])
                _, _, dist_r = find_nearest_cable_point(cable_pos, clamp_r, self._target_seg_indices_r[w])
                r_pos_scales[w] = max(
                    self.MIN_POS_SCALE, self.POS_ACTION_SCALE * min(1.0, dist_r / self.FINE_THRESHOLD)
                )

                ee_l_idx = ws + EE_BODY_OFFSET
                clamp_l = compute_clamp_pos(bq[ee_l_idx][:3], bq[ee_l_idx][3:7])
                _, _, dist_l = find_nearest_cable_point(cable_pos, clamp_l, self._target_seg_indices_l[w])
                l_pos_scales[w] = max(
                    self.MIN_POS_SCALE, self.POS_ACTION_SCALE * min(1.0, dist_l / self.FINE_THRESHOLD)
                )
            r_pos_delta = r_actions[:, 0:3] * r_pos_scales[:, None]
            l_pos_delta = l_actions[:, 0:3] * l_pos_scales[:, None]
        else:
            r_pos_delta = r_actions[:, 0:3] * self.POS_ACTION_SCALE
            l_pos_delta = l_actions[:, 0:3] * self.POS_ACTION_SCALE

        r_rot_delta = r_actions[:, 3:6] * self.ROT_ACTION_SCALE
        l_rot_delta = l_actions[:, 3:6] * self.ROT_ACTION_SCALE

        # Finger control: dual_arm always uses explicit RL-controlled fingers;
        # per-arm clamp uses auto-close, per-arm unclamp uses explicit
        use_auto_close = (self._mode == "clamp") and not self._dual_arm

        fk_coord_count = self._fk_model.joint_coord_count
        finger_mask = np.ones(fk_coord_count, dtype=bool)
        for fc in (*GRIPPER_JOINT_RANGE, *(JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE)):
            finger_mask[fc] = False

        targets_left = np.zeros((N, 3))
        targets_right = np.zeros((N, 3))
        rot_targets_left = []
        rot_targets_right = []
        jq_starts = np.array(self._per_world_fk_jq[:N])

        for w in range(N):
            # EE position targets (with XY workspace clamp to prevent Brownian drift)
            target_r = self._ee_target_right[w].copy() + r_pos_delta[w]
            target_r[0] = np.clip(
                target_r[0], self._settled_ee_r_pos[0] - self.EE_XY_BOUND, self._settled_ee_r_pos[0] + self.EE_XY_BOUND
            )
            target_r[1] = np.clip(
                target_r[1], self._settled_ee_r_pos[1] - self.EE_XY_BOUND, self._settled_ee_r_pos[1] + self.EE_XY_BOUND
            )
            target_r[2] = np.clip(target_r[2], GRIP_Z, EE_Z_SAFETY_UPPER)
            targets_right[w] = target_r
            self._ee_target_right[w] = target_r.copy()

            target_l = self._ee_target_left[w].copy() + l_pos_delta[w]
            target_l[0] = np.clip(
                target_l[0], self._settled_ee_l_pos[0] - self.EE_XY_BOUND, self._settled_ee_l_pos[0] + self.EE_XY_BOUND
            )
            target_l[1] = np.clip(
                target_l[1], self._settled_ee_l_pos[1] - self.EE_XY_BOUND, self._settled_ee_l_pos[1] + self.EE_XY_BOUND
            )
            target_l[2] = np.clip(target_l[2], GRIP_Z, EE_Z_SAFETY_UPPER)
            targets_left[w] = target_l
            self._ee_target_left[w] = target_l.copy()

            # EE rotation targets (with angular deviation clamp)
            delta_r_quat = axis_angle_to_quat_xyzw(r_rot_delta[w])
            new_r_quat = quat_multiply_xyzw(delta_r_quat, self._ee_quat_right[w])
            new_r_quat = new_r_quat / np.linalg.norm(new_r_quat)
            if quat_distance(new_r_quat, self._settled_ee_r_quat) > self.EE_MAX_ROT_DEV:
                new_r_quat = self._ee_quat_right[w].copy()  # reject delta
            self._ee_quat_right[w] = new_r_quat.copy()
            rot_targets_right.append(
                wp.vec4(float(new_r_quat[0]), float(new_r_quat[1]), float(new_r_quat[2]), float(new_r_quat[3]))
            )

            delta_l_quat = axis_angle_to_quat_xyzw(l_rot_delta[w])
            new_l_quat = quat_multiply_xyzw(delta_l_quat, self._ee_quat_left[w])
            new_l_quat = new_l_quat / np.linalg.norm(new_l_quat)
            if quat_distance(new_l_quat, self._settled_ee_l_quat) > self.EE_MAX_ROT_DEV:
                new_l_quat = self._ee_quat_left[w].copy()  # reject delta
            self._ee_quat_left[w] = new_l_quat.copy()
            rot_targets_left.append(
                wp.vec4(float(new_l_quat[0]), float(new_l_quat[1]), float(new_l_quat[2]), float(new_l_quat[3]))
            )

            if use_auto_close:
                # Gradual finger close: proportional to distance, parallel with arm movement
                ws = self._bws[w]
                cable_pos = bq[self._cable_bodies[w], :3]

                ee_r_pos = bq[ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
                ee_r_quat = bq[ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][3:7]
                clamp_r = compute_clamp_pos(ee_r_pos, ee_r_quat)
                _, seg_t_r, dist_r = find_nearest_cable_point(cable_pos, clamp_r, self._target_seg_indices_r[w])
                grasp_q_r = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_t_r))
                ori_dist_r = quat_distance(ee_r_quat, grasp_q_r)

                ee_l_pos = bq[ws + EE_BODY_OFFSET][:3]
                ee_l_quat = bq[ws + EE_BODY_OFFSET][3:7]
                clamp_l = compute_clamp_pos(ee_l_pos, ee_l_quat)
                _, seg_t_l, dist_l = find_nearest_cable_point(cable_pos, clamp_l, self._target_seg_indices_l[w])
                grasp_q_l = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_t_l))
                ori_dist_l = quat_distance(ee_l_quat, grasp_q_l)

                r_finger_target = _gradual_finger(
                    dist_r, ori_dist_r, self.FINGER_CLOSE_ORI_THRESH, self.FINGER_RAMP_DIST
                )
                jq_starts[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = r_finger_target
                jq_starts[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = r_finger_target
                l_finger_target = _gradual_finger(
                    dist_l, ori_dist_l, self.FINGER_CLOSE_ORI_THRESH, self.FINGER_RAMP_DIST
                )
                jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[0]] = l_finger_target
                jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[1]] = l_finger_target

                # Track auto-close state for metrics (fully closed = within 2mm)
                self._finger_closed_right[w] = r_finger_target <= FINGER_CLOSE_POS + 0.002
                self._finger_closed_left[w] = l_finger_target <= FINGER_CLOSE_POS + 0.002
            else:
                # Legacy 14D: explicit finger commands
                r_finger_new = (
                    jq_starts[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] - r_finger_cmd[w] * self.FINGER_CMD_SCALE
                )
                r_finger_new = np.clip(r_finger_new, FINGER_CLOSE_POS, FINGER_OPEN_POS)
                jq_starts[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = r_finger_new
                jq_starts[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = r_finger_new

                l_finger_new = jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[0]] - l_finger_cmd[w] * self.FINGER_CMD_SCALE
                l_finger_new = np.clip(l_finger_new, FINGER_CLOSE_POS, FINGER_OPEN_POS)
                jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[0]] = l_finger_new
                jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[1]] = l_finger_new

        # Set IK rotation targets
        self._ik_obj_rot_left.set_target_rotations(wp.array(rot_targets_left, dtype=wp.vec4, device=self.device))
        self._ik_obj_rot_right.set_target_rotations(wp.array(rot_targets_right, dtype=wp.vec4, device=self.device))

        # Batched IK solve
        jq_targets = self._solve_ik_batch(targets_left, targets_right, jq_starts)

        # Handle NaN
        nan_mask = np.any(np.isnan(jq_targets), axis=1)
        if np.any(nan_mask):
            jq_targets[nan_mask] = jq_starts[nan_mask]

        # Preserve finger positions in IK output
        for w in range(N):
            jq_targets[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = jq_starts[
                w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]
            ]
            jq_targets[w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = jq_starts[
                w, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]
            ]
            jq_targets[w, GRIPPER_DRIVER_JOINT_IDX[0]] = jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[0]]
            jq_targets[w, GRIPPER_DRIVER_JOINT_IDX[1]] = jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[1]]

        # DRIVE: interpolate the FULL joint row per frame (arm columns included -- p5 sec14.17 Q2,
        # route-env parity) and realize the ARM through the POSITION-servo ctrl ONLY (PS-1, Rs
        # 2026-07-19 kinematic complete-removal). The former FK body_q broadcast of the arm bodies
        # is REMOVED; eval_fk_batched stays as the FINGER-SPRING TARGET source (p5 sec14.17 Q1 --
        # the spring applies FORCES, a physical mechanism, not a state write).
        old_fk_jq = np.array(self._per_world_fk_jq[:N])
        for step in range(self.PHYSICS_STEPS_PER_RL):
            t = min((step + 1) / self.PHYSICS_STEPS_PER_RL, 1.0)

            # Full-row lerp: subsumes the former finger-only interp (identical formula per column;
            # the finger columns of jq_targets already carry their preserved commanded values).
            jq_interp = old_fk_jq + (jq_targets - old_fk_jq) * t

            self._batch_fk_jq.assign(jq_interp)
            eval_fk_batched(
                self._fk_model, self._batch_fk_jq, self._batch_fk_jqd, self._batch_fk_body_q, self._batch_fk_body_qd
            )
            batch_bq = self._batch_fk_body_q.numpy()[:, :ROBOT_BODY_COUNT]

            if self._arm_pd_drive:
                # ARM realization = servo target write only (qd-indexed; local cols 0-5 per arm).
                _ps1_jtp = self._control.joint_target_pos.numpy()
                for w in range(N):
                    for _base in (0, JOINTS_PER_ARM):
                        _ps1_jtp[self._arm_qd_idx[w, _base : _base + 6]] = jq_interp[w, _base : _base + 6]
                self._control.joint_target_pos.assign(_ps1_jtp)
            else:
                raise RuntimeError(
                    "kinematic arm drive REMOVED (Rs directive 2026-07-19 kinematic complete-removal): "
                    "the grip arm drive is the POSITION-servo ctrl path only (PS-1; set ARM_PD_DRIVE=1)"
                )

            self._physics_step_all(substeps=RL_SIM_SUBSTEPS, sim_dt=RL_SIM_DT, fk_batch_bq=batch_bq, n_worlds=N)

        for w in range(N):
            self._per_world_fk_jq[w] = jq_targets[w].copy()

    # =========================================================================
    # RSL-RL VecEnv Interface
    # =========================================================================

    @property
    def num_obs(self):
        return 45 if self._dual_arm else 28

    def get_observations(self) -> tuple[torch.Tensor, dict]:
        obs = self._compute_obs_batch()
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)
        return obs, {"observations": {}}

    def reset(self) -> tuple[torch.Tensor, dict]:
        self._reset_worlds(list(range(self._world_count)))
        self._world_episode_length[:] = 0
        self.episode_length_buf[:] = 0
        return self.get_observations()

    def step(self, actions: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]:
        actions = torch.nan_to_num(actions, nan=0.0, posinf=0.0, neginf=0.0)
        self._apply_actions_batch(actions)
        self._world_episode_length += 1
        if self._dual_arm:
            self.episode_length_buf[:] = self._world_episode_length
        else:
            # Mirror to per-arm episode_length_buf for RSL-RL
            self.episode_length_buf[0::2] = self._world_episode_length
            self.episode_length_buf[1::2] = self._world_episode_length
        self._total_env_steps += self._world_count

        rewards, dones, extras = self._compute_rewards_dones_batch()
        rewards = torch.nan_to_num(rewards, nan=-10.0, posinf=0.0, neginf=-10.0)

        done_ids = dones.nonzero(as_tuple=False).squeeze(-1)
        if len(done_ids) > 0:
            if self._dual_arm:
                world_ids = sorted(idx.item() for idx in done_ids)
            else:
                world_ids = sorted(set((idx.item() // 2) for idx in done_ids))
            self._reset_worlds(world_ids)

        obs = self._compute_obs_batch()
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)
        return obs, rewards, dones, extras

    def close(self):
        pass
