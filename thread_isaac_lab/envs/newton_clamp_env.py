# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Newton VBD Clamp RL environment — Multi-world RSL-RL VecEnv.

Independent Clamp skill (DAPG Approach A).
Task: Close fingers to grip cable after ApproachCable has positioned both arms.
Handles cable position AND orientation displacement during clamping via EE compensation.

Obs (42D): Same as ApproachCable v5 (unified obs for SkillAdapter base model sharing).
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

Action (14D): EE delta (12D) + finger command (2D).
  [0:3]   Right EE delta XYZ * POS_ACTION_SCALE [m]
  [3:6]   Right EE delta axis-angle * ROT_ACTION_SCALE [rad]
  [6:9]   Left EE delta XYZ * POS_ACTION_SCALE [m]
  [9:12]  Left EE delta axis-angle * ROT_ACTION_SCALE [rad]
  [12]    Right finger_cmd in [-1, 1]: -1=open, 0=hold, +1=close
  [13]    Left  finger_cmd in [-1, 1]: -1=open, 0=hold, +1=close

Finger control: RL-controlled via action[12:13] (NOT auto-control).
  finger_target = current_pos + finger_cmd * FINGER_STEP_SIZE (1mm/step)
  Clamped to [FINGER_CLOSE_POS, FINGER_OPEN_POS].
  Dynamic finger spring drives physical finger toward FK target.

Reward: multiplicative (grip_score × clamp_quality).
  r_grip: finger close progress (exp decay).
  r_clamp: pos + ori maintenance (cable tracking during finger close).
  Coupled: grip × clamp (reward only when both grip closing AND cable tracked).

Success: clamp(L) ^ clamp(R) ^ sustained(K_CLAMP=5).
  clamp(hand) = pos < T_DIST(2mm) ^ ori < T_ALIGN(10°) ^ grip < T_FINGER(12mm).
Done: success | timeout | explosion.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/train_clamp.py --world-count 4
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

from cable_orientation_utils import compute_hand_quat_for_cable
from newton_skill_env_base import (
    EE_BODY_OFFSET,
    # Re-exported constants
    FRANKA_NUM_JOINTS,
    IK_ITERATIONS_RL,
    IK_STEP_SIZE,
    RL_SIM_DT,
    RL_SIM_SUBSTEPS,
    ROBOT_BODIES_PER_ARM,
    ROBOT_BODY_COUNT,
    # Constants
    SIM_DT,
    axis_angle_to_quat_xyzw,
    # Scene building
    build_fk_and_init,
    build_multiworld_scene,
    compute_clamp_pos,
    compute_ori_error_axis_angle,
    # Cable / clamp utilities
    find_nearest_cable_point,
    # Quaternion utilities
    normalize_quat_w_positive,
    quat_distance,
    quat_multiply_xyzw,
    solve_ik_single,
    temporal_quat_consistency,
)

# Dynamic finger spring parameters (aligned with ApproachCable/AerialRegrasp)
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
    CLAMP_TERMINAL_STEPS,
    CLIP1_X,
    CLIP1_Y,
    CLIP1_Z,
    EE_TO_FINGERTIP,
    FINGER_CLOSE_POS,
    FINGER_LOCAL,
    FINGER_OPEN_POS,
    FINGER_STEP_SIZE,
    GRASP_X,
    GRASP_Z,
    GRIPPER_DRIVER_JOINT_IDX,
    GRIPPER_JOINT_RANGE,
    JOINTS_PER_ARM,
    K_CLAMP,
    LIFT_Z,
    SETTLE_STEPS,
    SIM_SUBSTEPS,
    T_ALIGN,
    T_DIST,
    T_FINGER,
    WIDE_LEFT_Y,
    WIDE_RIGHT_Y,
)

# IK rotation target
_cos_pi8 = math.cos(math.pi / 8)
_sin_pi8 = math.sin(math.pi / 8)


class NewtonClampEnv(VecEnv):
    """RSL-RL VecEnv for Clamp — finger close with EE compensation.

    P0: Both arms at cable-proximal position (GC terminal), fingers OPEN.
    Task: Close fingers to grip cable while compensating for cable displacement.
    """

    # Action scaling (EE: same as GC/AR; finger: FINGER_STEP_SIZE from SSOT)
    POS_ACTION_SCALE = 0.015
    ROT_ACTION_SCALE = 0.05
    FINGER_CMD_SCALE = FINGER_STEP_SIZE  # 1mm per RL step
    ADAPTIVE_POS_SCALE = True
    FINE_THRESHOLD = 0.050
    MIN_POS_SCALE = 0.0005
    MAX_EPISODE_STEPS = CLAMP_TERMINAL_STEPS  # 100
    PHYSICS_STEPS_PER_RL = 10
    EXPLOSION_DIST_THRESH = 1.0

    # Target cable segment window
    GRIP_SEG_WINDOW = 1
    INIT_XY_NOISE = 0.001  # ±1mm (smaller than GC — already positioned)

    # Reward: multiplicative (grip × clamp_quality)
    REWARD_MODE = "multiplicative"
    RANGE_GRIP = 0.020  # 20mm: exp decay for finger opening score
    RANGE_POS = 0.015  # 15mm: pos maintenance (same as GC)
    RANGE_ORI = 0.5  # 0.5 rad: ori maintenance (same as GC)
    PROGRESS_SCALE = 2.0
    W_GRIP = 0.2  # Independent grip weight
    W_CLAMP = 0.2  # Independent clamp quality weight (pos+ori)
    W_COUPLED = 0.6  # Coupled grip × clamp weight
    R_STEP_BONUS = 5.0  # One-time bonus: both arms reach finger-close threshold
    R_TASK_BONUS = 20.0  # Task completion bonus
    R_PENALTY = -0.01  # Per-step time penalty

    # Success: clamp(pos + ori + grip) ^ sustained(K_CLAMP)
    CLAMP_DIST_THRESH = T_DIST
    CLAMP_ORI_THRESH = T_ALIGN
    CLAMP_FINGER_THRESH = T_FINGER
    SUSTAIN_STEPS = K_CLAMP

    # Clip C1 pose (constant obs, same as GC)
    CLIP1_POS = np.array([CLIP1_X, CLIP1_Y, CLIP1_Z], dtype=np.float32)
    CLIP1_QUAT_XYZW = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)

    # Cache
    CACHE_DIR = os.path.join(_env_dir, "..", "data", "rl_clamp_cache")
    CACHE_VERSION = "v1"

    def __init__(self, world_count=4, device="cuda:0", cfg=None):
        self.num_envs = world_count
        self.num_actions = 14
        self._total_env_steps = 0
        self.max_episode_length = self.MAX_EPISODE_STEPS
        self.device = device
        self.cfg = cfg or {}
        self._world_count = world_count

        self.episode_length_buf = torch.zeros(world_count, dtype=torch.long, device=device)
        self._target_seg_indices_r = None
        self._target_seg_indices_l = None
        self._success_sustain_count = np.zeros(world_count, dtype=np.int32)
        self._step_bonus_given = np.zeros(world_count, dtype=bool)
        self._episode_count = 0

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

        # Override device for Newton
        os.environ["NEWTON_DEVICE"] = device
        _tncr.DEVICE = device

        print(f"[ClampEnv] Initializing: {world_count} worlds on {device}")
        t0 = time.perf_counter()

        self._build_model()

        if not self._load_and_restore_cache():
            self._build_p0_from_scratch()

        self._init_dynamic_fingers()
        self._init_batched_ik_solver()

        print(
            f"[ClampEnv] Ready in {time.perf_counter() - t0:.1f}s. "
            f"obs={self.num_obs}, act={self.num_actions}, worlds={world_count}"
        )

    # =========================================================================
    # Environment Construction
    # =========================================================================

    def _build_model(self):
        """Build FK model + multi-world physics scene."""
        print("[ClampEnv] Building FK model...")
        self._fk_model, self._fk_state, fk_jq = build_fk_and_init(
            left_finger_pos=FINGER_OPEN_POS,
            right_finger_pos=FINGER_OPEN_POS,
            device=self.device,
        )
        self._per_world_fk_jq = np.tile(fk_jq, (self._world_count, 1))

        print(f"[ClampEnv] Building scene ({self._world_count} worlds)...")
        scene = build_multiworld_scene(
            self._fk_model,
            self._fk_state,
            self._world_count,
            self.device,
            add_support_clips=True,
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

        print(f"[ClampEnv] Model: {self._model.body_count} bodies, {self._model.joint_count} joints")

    # =========================================================================
    # P0 Precondition: arms at cable-proximal position, fingers OPEN
    # =========================================================================

    def _cache_path(self):
        return os.path.join(self.CACHE_DIR, f"clamp_w{self._world_count}_p0_{self.CACHE_VERSION}.npz")

    def _build_p0_from_scratch(self):
        """Build P0 without cache: settle cable, IK arms to cable height, save cache."""
        print("[ClampEnv] Building P0 from scratch (no cache)...")

        # Settle cable on table
        print("[ClampEnv] Settling cable...")
        for _ in range(SETTLE_STEPS):
            self._physics_step_all()

        # IK-solve arms to cable-proximal position (fingertip at cable center)
        target_l = wp.vec3(GRASP_X, WIDE_LEFT_Y, GRASP_Z)
        target_r = wp.vec3(GRASP_X, WIDE_RIGHT_Y, GRASP_Z)
        jq_solved = solve_ik_single(self._fk_model, self._fk_state, target_l, target_r, self.device)

        # Preserve finger OPEN
        jq_solved[GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
        jq_solved[GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS
        jq_solved[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
        jq_solved[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS

        self._fk_state.joint_q.assign(jq_solved)
        newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)

        # Broadcast FK to all worlds
        fk_bq = self._fk_state.body_q.numpy()[:ROBOT_BODY_COUNT]
        phys_bq = self._state_0.body_q.numpy()
        for w in range(self._world_count):
            ws = self._bws[w]
            phys_bq[ws : ws + ROBOT_BODY_COUNT] = fk_bq
        self._state_0.body_q.assign(phys_bq)
        if hasattr(self._solver, "body_q_prev") and self._solver.body_q_prev is not None:
            self._solver.body_q_prev.assign(phys_bq)

        # Additional settling with arms in place
        for _ in range(SETTLE_STEPS):
            self._physics_step_all()

        # Save settled state
        wp.synchronize()
        self._settled_body_q = self._state_0.body_q.numpy().copy()
        self._settled_body_qd = self._state_0.body_qd.numpy().copy()
        self._settled_fk_jq = jq_solved.copy()

        self._finish_p0_setup()
        self._save_cache()
        print("[ClampEnv] P0 built and cached")

    def _finish_p0_setup(self):
        """Common P0 finalization (after cache load or from-scratch build)."""
        # Restore FK
        self._fk_state.joint_q.assign(self._settled_fk_jq)
        newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)

        for w in range(self._world_count):
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()

        # Compute target seg indices
        bq = self._settled_body_q
        self._target_seg_indices_r, self._target_seg_indices_l = self._compute_target_seg_indices(bq)

        # Cache settled EE poses
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

        print(
            f"[ClampEnv] P0: EE_R={self._settled_ee_r_pos}, EE_L={self._settled_ee_l_pos}, "
            f"seg_r={self._target_seg_indices_r[0]}, seg_l={self._target_seg_indices_l[0]}"
        )

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
        print(f"[ClampEnv] Cache saved to {path}")

    def _load_and_restore_cache(self):
        """Load P0 cache. Returns True if successful."""
        path = self._cache_path()
        if not os.path.exists(path):
            print(f"[ClampEnv] No cache at {path}")
            return False
        try:
            data = np.load(path)
            if int(data["world_count"][0]) != self._world_count:
                print("[ClampEnv] Cache world_count mismatch")
                return False
            if int(data["body_count"][0]) != self._model.body_count:
                print("[ClampEnv] Cache body_count mismatch")
                return False

            self._settled_body_q = data["body_q"]
            self._settled_body_qd = data["body_qd"]
            self._settled_fk_jq = data["fk_jq"]
            print(f"[ClampEnv] Loaded cache from {path}")
        except Exception as e:
            print(f"[ClampEnv] Cache load failed: {e}")
            return False

        # Restore physics state
        self._state_0.body_q.assign(self._settled_body_q)
        self._state_0.body_qd.assign(self._settled_body_qd)
        if hasattr(self._solver, "body_q_prev") and self._solver.body_q_prev is not None:
            self._solver.body_q_prev.assign(self._settled_body_q)

        # Reset Dahl friction
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
        """Make finger bodies dynamic for spring-based grip (aligned with GC/AR)."""
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
            f"[ClampEnv] Dynamic fingers: {len(self._finger_physics_ids)} bodies "
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
                    vel = body_qd[bi][3:6]
                    target = fk_batch_bq[w, local_bi, :3]
                    force = -FINGER_SPRING_KE * (pos - target) - FINGER_SPRING_KD * vel
                    body_f[bi][3:6] += force
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
        """One physics frame for all worlds."""
        n_sub = substeps if substeps is not None else SIM_SUBSTEPS
        dt = sim_dt if sim_dt is not None else SIM_DT
        for _ in range(n_sub):
            self._state_0.clear_forces()
            if fk_batch_bq is not None and n_worlds is not None:
                self._apply_finger_spring(fk_batch_bq, n_worlds)
            self._model.collide(self._state_0, self._contacts)
            self._solver.step(self._state_0, self._state_1, self._control, self._contacts, dt)
            self._state_0, self._state_1 = self._state_1, self._state_0
            self._sanitise_body_state()

    # =========================================================================
    # Target Segment Computation
    # =========================================================================

    def _compute_target_seg_indices(self, bq):
        """Compute target cable segment indices per arm (±GRIP_SEG_WINDOW)."""
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
    # IK Solver
    # =========================================================================

    def _init_batched_ik_solver(self):
        """Create cached IKSolver with n_problems=world_count."""
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

        print(f"[ClampEnv] Batched IK solver: n_problems={N}")

    def _solve_ik_batch(self, targets_left_np, targets_right_np, jq_starts_np):
        """Solve IK for all worlds in one batched call."""
        self._ik_obj_pos_left.set_target_positions(wp.array(targets_left_np, dtype=wp.vec3, device=self.device))
        self._ik_obj_pos_right.set_target_positions(wp.array(targets_right_np, dtype=wp.vec3, device=self.device))
        self._ik_jq_in.assign(jq_starts_np)
        self._ik_solver_batch.step(self._ik_jq_in, self._ik_jq_out, iterations=IK_ITERATIONS_RL, step_size=IK_STEP_SIZE)
        return self._ik_jq_out.numpy()

    # =========================================================================
    # Reset
    # =========================================================================

    def _reset_worlds(self, env_ids):
        """Reset specific worlds to P0 (arms positioned, fingers OPEN)."""
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

            # Reset FK (fingers OPEN)
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()

            # Reset state
            self._step_bonus_given[w] = False
            self._success_sustain_count[w] = 0

            # Reset EE targets
            self._ee_target_right[w] = self._settled_ee_r_pos.copy()
            self._ee_target_left[w] = self._settled_ee_l_pos.copy()
            self._ee_quat_right[w] = self._settled_ee_r_quat.copy()
            self._ee_quat_left[w] = self._settled_ee_l_quat.copy()

            # Reset temporal quat consistency (Bug #2)
            self._prev_clamp_r_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_clamp_l_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_seg_r_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_seg_l_quat[w] = np.array([0, 0, 0, 1], dtype=np.float32)

            # Small initial noise (both arms)
            if self.INIT_XY_NOISE > 0:
                for ee_offset in [EE_BODY_OFFSET, FRANKA_NUM_JOINTS + EE_BODY_OFFSET]:
                    ee_bi = start + ee_offset
                    noise = np.random.uniform(-self.INIT_XY_NOISE, self.INIT_XY_NOISE, size=2)
                    bq[ee_bi, 0] += noise[0]
                    bq[ee_bi, 1] += noise[1]
                    prev[ee_bi, 0] += noise[0]
                    prev[ee_bi, 1] += noise[1]
                    if ee_offset == FRANKA_NUM_JOINTS + EE_BODY_OFFSET:
                        self._ee_target_right[w][0] += noise[0]
                        self._ee_target_right[w][1] += noise[1]
                    else:
                        self._ee_target_left[w][0] += noise[0]
                        self._ee_target_left[w][1] += noise[1]

            self.episode_length_buf[w] = 0

        self._state_0.body_q.assign(bq)
        self._state_0.body_qd.assign(bqd)
        self._solver.body_q_prev.assign(prev)

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
    # Observation (42D — unified with GC/AR)
    # =========================================================================

    def _compute_obs_batch(self):
        """Compute observations for all worlds. Returns [N, 42] tensor."""
        wp.synchronize()
        bq = self._state_0.body_q.numpy()

        obs_list = []
        for w in range(self._world_count):
            ws = self._bws[w]

            # Right EE
            ee_r_idx = ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
            ee_r_pos = bq[ee_r_idx][:3]
            ee_r_quat = bq[ee_r_idx][3:7]

            # Left EE
            ee_l_idx = ws + EE_BODY_OFFSET
            ee_l_pos = bq[ee_l_idx][:3]
            ee_l_quat = bq[ee_l_idx][3:7]

            # Clamp positions
            clamp_r_pos = compute_clamp_pos(ee_r_pos, ee_r_quat)
            clamp_l_pos = compute_clamp_pos(ee_l_pos, ee_l_quat)

            # Clamp quaternions (w >= 0, temporal consistency)
            clamp_r_quat = normalize_quat_w_positive(ee_r_quat)
            clamp_r_quat = temporal_quat_consistency(clamp_r_quat, self._prev_clamp_r_quat[w])
            self._prev_clamp_r_quat[w] = clamp_r_quat.copy()
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

            # Target cable segment (interpolated nearest)
            cable_bq = bq[self._cable_bodies[w]]
            cable_pos = cable_bq[:, :3]

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

            # Errors
            ori_error_r = compute_ori_error_axis_angle(clamp_r_quat, grasp_quat_r)
            pos_error_r = clamp_r_pos - seg_pos_r
            ori_error_l = compute_ori_error_axis_angle(clamp_l_quat, grasp_quat_l)
            pos_error_l = clamp_l_pos - seg_pos_l

            obs_list.append(
                [
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
                    seg_pos_r[0],
                    seg_pos_r[1],
                    seg_pos_r[2],
                    grasp_quat_r[0],
                    grasp_quat_r[1],
                    grasp_quat_r[2],
                    grasp_quat_r[3],
                    self.CLIP1_POS[0],
                    self.CLIP1_POS[1],
                    self.CLIP1_POS[2],
                    self.CLIP1_QUAT_XYZW[0],
                    self.CLIP1_QUAT_XYZW[1],
                    self.CLIP1_QUAT_XYZW[2],
                    self.CLIP1_QUAT_XYZW[3],
                    ori_error_r[0],
                    ori_error_r[1],
                    ori_error_r[2],
                    pos_error_r[0],
                    pos_error_r[1],
                    pos_error_r[2],
                    ori_error_l[0],
                    ori_error_l[1],
                    ori_error_l[2],
                    pos_error_l[0],
                    pos_error_l[1],
                    pos_error_l[2],
                ]
            )

        obs = torch.tensor(obs_list, dtype=torch.float32, device=self.device)
        return torch.nan_to_num(obs, nan=0.0)

    # =========================================================================
    # Reward / Done
    # =========================================================================

    def _compute_rewards_dones_batch(self):
        """Compute rewards and dones for all worlds.

        Reward: multiplicative (grip_score × clamp_quality).
        Success: clamp(L) ^ clamp(R) ^ sustained(K_CLAMP).
        """
        wp.synchronize()
        bq = self._state_0.body_q.numpy()

        rewards = np.zeros(self._world_count, dtype=np.float32)
        dones = np.zeros(self._world_count, dtype=np.int64)
        timeouts = np.zeros(self._world_count, dtype=np.int64)
        successes = np.zeros(self._world_count, dtype=np.float32)

        rc_r_grip = np.zeros(self._world_count, dtype=np.float32)
        rc_r_clamp = np.zeros(self._world_count, dtype=np.float32)
        rc_dist_r = np.zeros(self._world_count, dtype=np.float32)
        rc_dist_l = np.zeros(self._world_count, dtype=np.float32)
        rc_ori_r = np.zeros(self._world_count, dtype=np.float32)
        rc_ori_l = np.zeros(self._world_count, dtype=np.float32)
        rc_finger_r = np.zeros(self._world_count, dtype=np.float32)
        rc_finger_l = np.zeros(self._world_count, dtype=np.float32)

        for w in range(self._world_count):
            ws = self._bws[w]

            # Right EE
            ee_r_idx = ws + FRANKA_NUM_JOINTS + EE_BODY_OFFSET
            ee_r_pos = bq[ee_r_idx][:3]
            ee_r_quat = bq[ee_r_idx][3:7]
            clamp_r_pos = compute_clamp_pos(ee_r_pos, ee_r_quat)
            clamp_r_quat = normalize_quat_w_positive(ee_r_quat)

            # Left EE
            ee_l_idx = ws + EE_BODY_OFFSET
            ee_l_pos = bq[ee_l_idx][:3]
            ee_l_quat = bq[ee_l_idx][3:7]
            clamp_l_pos = compute_clamp_pos(ee_l_pos, ee_l_quat)
            clamp_l_quat = normalize_quat_w_positive(ee_l_quat)

            # Cable targets
            cable_bq = bq[self._cable_bodies[w]]
            cable_pos = cable_bq[:, :3]

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

            # Finger openings
            fk_jq = self._per_world_fk_jq[w]
            finger_r = (
                fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]]
                + fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]]
            )
            finger_l = fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] + fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]]

            # ---- Reward: multiplicative (grip × clamp_quality) ----
            # Per-arm grip score: 0 when open, ~1 when closed
            score_grip_r = math.exp(-finger_r / self.RANGE_GRIP)
            score_grip_l = math.exp(-finger_l / self.RANGE_GRIP)
            score_grip = 0.5 * (score_grip_r + score_grip_l)

            # Per-arm clamp quality: pos + ori combined
            score_pos_r = math.exp(-dist_pos_r / self.RANGE_POS)
            score_ori_r = math.exp(-dist_ori_r / self.RANGE_ORI)
            score_pos_l = math.exp(-dist_pos_l / self.RANGE_POS)
            score_ori_l = math.exp(-dist_ori_l / self.RANGE_ORI)
            score_clamp = 0.25 * (score_pos_r + score_ori_r + score_pos_l + score_ori_l)

            # Multiplicative coupling: close fingers only when well-positioned
            progress = self.W_GRIP * score_grip + self.W_CLAMP * score_clamp + self.W_COUPLED * score_grip * score_clamp
            r_main = self.PROGRESS_SCALE * (progress - 1.0)

            # R_step: one-time bonus when both arms' fingers reach close threshold
            r_step_val = 0.0
            both_fingers_close = finger_r < self.CLAMP_FINGER_THRESH and finger_l < self.CLAMP_FINGER_THRESH
            if both_fingers_close and not self._step_bonus_given[w]:
                r_step_val = self.R_STEP_BONUS
                self._step_bonus_given[w] = True

            # SUCCESS: clamp(L) ^ clamp(R) ^ sustained(K_CLAMP)
            clamp_r_ok = (
                dist_pos_r < self.CLAMP_DIST_THRESH
                and dist_ori_r < self.CLAMP_ORI_THRESH
                and finger_r < self.CLAMP_FINGER_THRESH
            )
            clamp_l_ok = (
                dist_pos_l < self.CLAMP_DIST_THRESH
                and dist_ori_l < self.CLAMP_ORI_THRESH
                and finger_l < self.CLAMP_FINGER_THRESH
            )
            if clamp_r_ok and clamp_l_ok:
                self._success_sustain_count[w] += 1
            else:
                self._success_sustain_count[w] = 0
            success = self._success_sustain_count[w] >= self.SUSTAIN_STEPS

            r_task_val = self.R_TASK_BONUS if success else 0.0
            r = r_main + r_step_val + r_task_val + self.R_PENALTY

            # Done conditions
            explosion = dist_pos_r > self.EXPLOSION_DIST_THRESH or dist_pos_l > self.EXPLOSION_DIST_THRESH
            timeout = self.episode_length_buf[w].item() >= self.max_episode_length
            done = success or timeout or explosion

            rewards[w] = r
            rc_r_grip[w] = r_main
            rc_r_clamp[w] = score_clamp
            rc_dist_r[w] = dist_pos_r
            rc_dist_l[w] = dist_pos_l
            rc_ori_r[w] = dist_ori_r
            rc_ori_l[w] = dist_ori_l
            rc_finger_r[w] = finger_r
            rc_finger_l[w] = finger_l
            dones[w] = int(done)
            # BUG-1 fix: explosion is a true terminal state (value=0), not a timeout.
            # Only actual timeout should bootstrap value via RSL-RL PPO.
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
                    "/reward/r_main": float(np.mean(rc_r_grip)),
                    "/reward/r_step": float(np.mean([1 if b else 0 for b in self._step_bonus_given])),
                    "/reward/r_penalty": float(self.R_PENALTY),
                    "/metrics/score_clamp_mean": float(np.mean(rc_r_clamp)),
                    "/metrics/dist_pos_r_median": float(np.median(rc_dist_r)),
                    "/metrics/dist_pos_l_median": float(np.median(rc_dist_l)),
                    "/metrics/dist_ori_r_median": float(np.median(rc_ori_r)),
                    "/metrics/dist_ori_l_median": float(np.median(rc_ori_l)),
                    "/metrics/finger_r_mean": float(np.mean(rc_finger_r)),
                    "/metrics/finger_l_mean": float(np.mean(rc_finger_l)),
                    "/metrics/explosion_count": int(
                        np.sum((rc_dist_r > self.EXPLOSION_DIST_THRESH) | (rc_dist_l > self.EXPLOSION_DIST_THRESH))
                    ),
                },
            },
        )

    # =========================================================================
    # Action Application (14D: 12D EE + 2D finger)
    # =========================================================================

    def _apply_actions_batch(self, actions):
        """Apply per-world 14D actions via batched IK + physics.

        Args:
            actions: [N, 14] tensor -- per world:
                [0:3]   right EE delta XYZ
                [3:6]   right EE delta axis-angle
                [6:9]   left EE delta XYZ
                [9:12]  left EE delta axis-angle
                [12]    right finger_cmd in [-1, 1]
                [13]    left  finger_cmd in [-1, 1]
        """
        N = self._world_count
        actions_np = actions.cpu().numpy()

        wp.synchronize()
        bq = self._state_0.body_q.numpy()

        # --- EE action scaling (adaptive, same as GC) ---
        if self.ADAPTIVE_POS_SCALE:
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
            r_pos_delta = actions_np[:, 0:3] * r_pos_scales[:, None]
            l_pos_delta = actions_np[:, 6:9] * l_pos_scales[:, None]
        else:
            r_pos_delta = actions_np[:, 0:3] * self.POS_ACTION_SCALE
            l_pos_delta = actions_np[:, 6:9] * self.POS_ACTION_SCALE

        r_rot_delta = actions_np[:, 3:6] * self.ROT_ACTION_SCALE
        l_rot_delta = actions_np[:, 9:12] * self.ROT_ACTION_SCALE

        # --- Finger commands (RL-controlled) ---
        r_finger_cmd = actions_np[:, 12]  # [N]
        l_finger_cmd = actions_np[:, 13]  # [N]

        fk_coord_count = self._fk_model.joint_coord_count
        finger_mask = np.ones(fk_coord_count, dtype=bool)
        for fc in (*GRIPPER_JOINT_RANGE, *(JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE)):
            finger_mask[fc] = False

        # --- Compute EE targets + finger targets ---
        targets_left = np.zeros((N, 3))
        targets_right = np.zeros((N, 3))
        rot_targets_left = []
        rot_targets_right = []
        jq_starts = np.array(self._per_world_fk_jq[:N])

        for w in range(N):
            # EE position targets
            target_r = self._ee_target_right[w].copy() + r_pos_delta[w]
            target_r[2] = np.clip(target_r[2], GRASP_Z, LIFT_Z + 0.05)
            targets_right[w] = target_r
            self._ee_target_right[w] = target_r.copy()

            target_l = self._ee_target_left[w].copy() + l_pos_delta[w]
            target_l[2] = np.clip(target_l[2], GRASP_Z, LIFT_Z + 0.05)
            targets_left[w] = target_l
            self._ee_target_left[w] = target_l.copy()

            # EE rotation targets
            delta_r_quat = axis_angle_to_quat_xyzw(r_rot_delta[w])
            new_r_quat = quat_multiply_xyzw(delta_r_quat, self._ee_quat_right[w])
            new_r_quat = new_r_quat / np.linalg.norm(new_r_quat)
            self._ee_quat_right[w] = new_r_quat.copy()
            rot_targets_right.append(
                wp.vec4(float(new_r_quat[0]), float(new_r_quat[1]), float(new_r_quat[2]), float(new_r_quat[3]))
            )

            delta_l_quat = axis_angle_to_quat_xyzw(l_rot_delta[w])
            new_l_quat = quat_multiply_xyzw(delta_l_quat, self._ee_quat_left[w])
            new_l_quat = new_l_quat / np.linalg.norm(new_l_quat)
            self._ee_quat_left[w] = new_l_quat.copy()
            rot_targets_left.append(
                wp.vec4(float(new_l_quat[0]), float(new_l_quat[1]), float(new_l_quat[2]), float(new_l_quat[3]))
            )

            # Finger position targets (RL-controlled: incremental position command)
            # Negate: +1 cmd = close = decrease joint position (CLOSE_POS < OPEN_POS)
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

        # Interpolate FK + physics stepping
        old_fk_jq = np.array(self._per_world_fk_jq[:N])
        for step in range(self.PHYSICS_STEPS_PER_RL):
            t = min((step + 1) / self.PHYSICS_STEPS_PER_RL, 1.0)

            jq_interp = old_fk_jq.copy()
            # Arm joints: interpolate
            jq_interp[:, finger_mask] = (
                old_fk_jq[:, finger_mask] + (jq_targets[:, finger_mask] - old_fk_jq[:, finger_mask]) * t
            )
            # Finger joints: interpolate from old to new
            for fc in (*GRIPPER_JOINT_RANGE, *(JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE)):
                jq_interp[:, fc] = old_fk_jq[:, fc] + (jq_targets[:, fc] - old_fk_jq[:, fc]) * t

            # Batched FK
            self._batch_fk_jq.assign(jq_interp)
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

            # Physics step with finger spring forces
            self._physics_step_all(substeps=RL_SIM_SUBSTEPS, sim_dt=RL_SIM_DT, fk_batch_bq=batch_bq, n_worlds=N)

        # Save final FK state
        for w in range(N):
            self._per_world_fk_jq[w] = jq_targets[w].copy()

    # =========================================================================
    # RSL-RL VecEnv Interface
    # =========================================================================

    @property
    def num_obs(self):
        return 42

    def get_observations(self) -> tuple[torch.Tensor, dict]:
        obs = self._compute_obs_batch()
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)
        return obs, {"observations": {}}

    def reset(self) -> tuple[torch.Tensor, dict]:
        self._reset_worlds(list(range(self._world_count)))
        return self.get_observations()

    def step(self, actions: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]:
        # Sanitise actions: NaN/inf -> zero
        actions = torch.nan_to_num(actions, nan=0.0, posinf=0.0, neginf=0.0)
        self._apply_actions_batch(actions)
        self.episode_length_buf += 1
        self._total_env_steps += self._world_count

        rewards, dones, extras = self._compute_rewards_dones_batch()
        rewards = torch.nan_to_num(rewards, nan=-10.0, posinf=0.0, neginf=-10.0)

        # Auto-reset done worlds
        done_ids = dones.nonzero(as_tuple=False).squeeze(-1)
        if len(done_ids) > 0:
            self._reset_worlds(done_ids.cpu().tolist())

        obs = self._compute_obs_batch()
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)
        return obs, rewards, dones, extras
