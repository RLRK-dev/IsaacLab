# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""env7 ApproachCable RL env -- mujoco-koshape substrate (Newton 1.2.1 SolverMuJoCo, UR5e×2 + Robotiq koshape).

PORT-BY-INTENT, not a copy of the VBD impl. The quarantined VBD-AC snapshot under
``eval_runs/troot_ac_vbd_superseded_20260626/`` (the ``newton_approach_cable_env.py`` superseded copy)
is the INTENT reference for the RL-WRAPPER logic ONLY (obs/reward/action/success). The substrate
(scene + UR5e+Robotiq koshape arms + cable + SolverMuJoCo + cable contacts) is REUSED from the
active mujoco base ``newton_skill_env_base.build_multiworld_scene`` (the same scaffolding the active
``NewtonGripEnv`` mirrors). Driving = ``broadcast_jointq_to_all_worlds`` (SC2b joint_q kinematic
re-pose), the Newton mujoco substrate norm -- NOT VBD ``body_q.assign``.

Anchor: LEDGER FAILED §2 (VBD-AC DISCARDED -> mujoco-koshape) / RS71-SSOT:15 (env7 SolverMuJoCo) /
§0 INVARIANTS (DUAL-ARM, 88mm grasp span, koshape-LOCK, no-kinematic-trick).

Skill: independent ApproachCable (DAPG Approach A). Both arms approach the cable (fingers OPEN;
grasp is a separate skill). Pre-grasp only.

Obs (42D, per world):
    [0:3]   Right clamp position XYZ [m]   (koshape DC2 fingertip = clamp_pos_ko)
    [3:7]   Right clamp quaternion (qx, qy, qz, qw), w >= 0
    [7]     Right finger opening (driver j0 + j1) [m]
    [8:11]  Left clamp position XYZ [m]
    [11:15] Left clamp quaternion (qx, qy, qz, qw), w >= 0
    [15]    Left finger opening [m]
    [16:19] Target cable segment position XYZ [m]
    [19:23] Target cable segment quaternion (qx, qy, qz, qw), w >= 0  (KO_BASE hand-down)
    [23:26] Clip C1 position XYZ [m]   (constant obs context, not a reward target)
    [26:30] Clip C1 quaternion
    [30:33] Right orientation error axis-angle [rad]
    [33:36] Right position error XYZ [m]
    [36:39] Left orientation error axis-angle [rad]
    [39:42] Left position error XYZ [m]

Action (12D, per world):
    [0:3]   Right EE delta XYZ * POS_ACTION_SCALE [m]
    [3:6]   Right EE delta axis-angle * ROT_ACTION_SCALE [rad]  (accumulates into IK rot target)
    [6:9]   Left EE delta XYZ * POS_ACTION_SCALE [m]
    [9:12]  Left EE delta axis-angle * ROT_ACTION_SCALE [rad]

Reward: pose_match v37 (R_pos 3-scale + R_ori 2-scale + R_STEP + R_TASK + R_PENALTY).
Success: BOTH arms dist_pos < T_DIST_APPROACH(12mm) ∧ dist_ori < T_ALIGN(10°) ∧ sustained K_GRASP(5).

IK: P0 init = per-arm independent solve (``_solve_ik_single_ko``); RL = per-step batched ``IKSolver``.
NOTE: this is a DEVIATION from the banked debate DECIDE ("reuse ``solve_ik_dual``") -- the per-arm/custom
solves were chosen because the combined dual solve compromises ~5mm/arm INWARD (span 78mm vs 88mm
INVARIANT#2); per-arm reaches err=0 at the 88mm raise-point. CONSEQUENCE: the ``solve_ik_dual`` arm-arm
collision spheres are DROPPED -> arm-arm clearance now relies on the reward + seg mid-split + the smoke
mj_geomDistance check (NOT a solver objective).

⛔ KNOWN-GAPS / VALIDATION-STATUS (records-must-match-fact; do NOT over-claim) ⛔
- CPU-SMOKE validated ONLY (world_count=2, 8/9 gates): SolverMuJoCo, obs=42D, cable-contacts-active
  (cable @Z0.809 on clips), non-degenerate (dist 91mm both worlds), 88mm span, ori<10°, idle@P0≈0
  (anti-hover), timeouts purity. GPU / RL-training / high-fidelity = NOT run (RL FORBIDDEN this phase).
- ⛔ ACTIVE ORI-CONTROL is WEAK (G7 KNOWN-GAP, %9-ruling 2026-06-26 accept-for-scope, NOT a pass):
  the action-IK rot UNDER-APPLIES the command ~100x (14° commanded -> 0.11° actual). The straight-cable
  build is functionally complete ONLY because ori is PASSIVELY aligned (P0 ori=0° + IK rot-target holds
  EE@KO_ROT + the cable settles ~straight so grasp_target≈KO_ROT). Active ori-control is a HARD
  PREREQUISITE for the curved-cable/deploy front and is UNRESOLVED. CONSERVATISM (GROVE §2.2): the
  straight-cable ori-PASS is NON-CONSERVATIVE on ori-control -> any curved/deploy claim REQUIRES
  resolving active ori-control + high-fidelity ori validation FIRST (RS71-SSOT §4 curved/shape =
  production-pending, separate front).
- arm-arm collision: no solver objective (see IK NOTE) -> a kinematic arm-overlap window is reachable
  during RL exploration (EE_XY_BOUND ±50mm/arm); CPU-smoke exercises P0 + a few steps only, NOT the
  full RL-exploration extremes. Arm-arm clearance under RL = UNVERIFIED.

Usage:
    source ~/env_isaaclab7/bin/activate
    # SOLVER_BACKEND is forced to "mujoco" by this module (see import block below).
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
from newton.ik import IKObjectiveJointLimit, IKObjectivePosition, IKObjectiveRotation, IKSolver
from rsl_rl.env import VecEnv

# --- sys.path: envs/, scripts/, configs/ (same precedent NewtonGripEnv uses) ------------------------
_env_dir = os.path.dirname(os.path.abspath(__file__))
if _env_dir not in sys.path:
    sys.path.insert(0, _env_dir)
_script_dir = os.path.join(_env_dir, "..", "scripts")
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
_config_dir = os.path.join(_env_dir, "..", "configs")
if _config_dir not in sys.path:
    sys.path.insert(0, _config_dir)

# ⭐⭐ SOLVER-BACKEND FLIP -- MUST happen BEFORE newton_skill_env_base is imported. ⭐⭐
# build_multiworld_scene branches on the base module-global SOLVER_BACKEND (binds at base import),
# and make_solver's frozen default arg `backend=SOLVER_BACKEND` ALSO binds at base import. Setting
# task_config.SOLVER_BACKEND here -- before the `from newton_skill_env_base import ...` below -- makes
# BOTH consistent (mujoco arms + SolverMuJoCo + enable_cable_contacts), avoiding the silent-disable
# trap (mujoco arms wired to a VBD solver). task_config:107 default is "vbd" (the routing A/B SSOT;
# a known TRAP for the RL substrate). This is a runtime override (no task_config-file edit), the
# documented "--solver-backend mujoco overrides locally, no SSOT flip" mechanism (task_config:110-112).
# TODO(%4-review): if ANY module imports newton_skill_env_base BEFORE this env (so base binds with
# the "vbd" default), make_solver's frozen default could still build a VBD solver under mujoco arms.
# In the CPU-smoke, assert isinstance(env._solver, SolverMuJoCo) AND cable contacts ACTIVE (ncon>0)
# to confirm the flip took effect end-to-end.
import task_config  # noqa: E402

task_config.SOLVER_BACKEND = "mujoco"

import test_newton_clip_routing as _tncr  # noqa: E402  (DEVICE override, same as NewtonGripEnv)
import newton_skill_env_base as _nseb  # noqa: E402

# Defensive: also pin the base module-global (covers the case where base was already imported above).
# build_multiworld_scene reads this name at call time. (make_solver's frozen default is handled by the
# task_config flip happening before base import -- see TODO above.)
_nseb.SOLVER_BACKEND = "mujoco"

from cable_orientation_utils import compute_hand_quat_for_cable  # noqa: E402
from chain_runtime_state import (  # noqa: E402
    export_chain_state_from_env,
    import_chain_state_into_env,
    validate_chain_state_for_env,
)
from newton_skill_env_base import (  # noqa: E402
    DT,
    EE_BODY_OFFSET,
    IK_ITERATIONS_RL,
    IK_STEP_SIZE,
    RL_SIM_DT,
    RL_SIM_SUBSTEPS,
    SIM_DT,
    assign_world_states_to_sim,
    axis_angle_to_quat_xyzw,
    build_fk_and_init,
    build_multiworld_scene,
    compute_ori_error_axis_angle,
    derive_cable_joint_q_from_tangents,
    find_nearest_cable_point,
    normalize_quat_w_positive,
    quat_distance,
    quat_multiply_xyzw,
    quat_rotate_vec,
    reset_dahl_friction_for_envs,
    restore_ee_targets_per_world,
    restore_world_body_state,
    seed_cable_joint_state,
    temporal_quat_consistency,
)
from task_config import (  # noqa: E402
    CABLE_RADIUS,
    CABLE_XY_DR_AMPLITUDE,
    CLIP1_X,
    CLIP1_Y,
    CLIP1_Z,
    CLIP_BASE_HEIGHT,
    EE_TO_PINCH_OPEN,
    EE_Z_SAFETY_UPPER,
    FINGER_OPEN_POS,
    GRASP_TERMINAL_STEPS,
    GRIPPER_DRIVER_JOINT_IDX,
    GRIPPER_JOINT_RANGE,
    JOINTS_PER_ARM,
    K_GRASP,
    MAX_MOVE_STEPS,
    ROBOT_BODIES_PER_ARM,
    SETTLE_STEPS,
    SIM_SUBSTEPS,
    T_ALIGN,
    T_DIST_APPROACH,
    TABLE_HEIGHT,
    WIDE_LEFT_Y,
    WIDE_RIGHT_Y,
)

# Per-arm strides (UR5e+Robotiq collapse=True: bodies == joints == 14). The legacy base also exposes
# a Franka-era per-arm-joint-count alias equal to the same 14, but we use the descriptive
# ROBOT_BODIES_PER_ARM / JOINTS_PER_ARM to stay grep-clean of VBD-only symbol names.
_RIGHT_ARM_BODY_OFFSET = ROBOT_BODIES_PER_ARM  # 14: right-arm body slice start within a world
_RIGHT_ARM_JOINT_OFFSET = JOINTS_PER_ARM  # 14: right-arm joint_q slice start within an arm-pair
_LEFT_EE_BODY = EE_BODY_OFFSET  # 5: UR5e wrist_3 (left arm)
_RIGHT_EE_BODY = _RIGHT_ARM_BODY_OFFSET + EE_BODY_OFFSET  # 19: UR5e wrist_3 (right arm)
_N_ARM_JOINTS = 2 * JOINTS_PER_ARM  # 28: both arms' joint_q span within a world (cable joints follow)

# --- DC1: koshape wrist-down IK rotation target (Rx(-90) xyzw). NOT Franka pi/8 (that mis-orients the
# UR5e wrist_3 -> S5 horizontal-gripper failure). The agent rot-delta accumulates ON TOP of this. ---
KO_ROT_TARGET_XYZW = (-0.7071067811865476, 0.0, 0.0, 0.7071067811865476)
# --- ori target base for compute_hand_quat_for_cable: koshape hand-down (NOT the Franka default
# BASE_HAND_DOWN_QUAT = [cos pi/8, sin pi/8, 0, 0], which is the S5 horizontal-gripper bug). ---
KO_BASE_HAND_DOWN_QUAT = np.array([-0.7071067811865476, 0.0, 0.0, 0.7071067811865476], dtype=np.float32)

# --- EE-Z action-clamp FLOOR (koshape). At the floor the koshape OPEN claw bottom reaches the cable
# centerline (NOT 40mm into the table via the stale Franka GRASP_Z=1.025). pre-check ISSUE-3.
#   wrist_floor = TABLE + CLIP_BASE + CABLE_RADIUS + EE_TO_PINCH_OPEN ≈ 0.80+0.005+0.004+0.26092 = 1.06992
#   -> clamp (fingertip) = wrist_floor - EE_TO_PINCH_OPEN ≈ 0.808 ≈ cable center (TABLE+CLIP_BASE+RADIUS).
EE_Z_FLOOR_KO = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS + EE_TO_PINCH_OPEN  # ≈ 1.06992

# P0 init IK iterations: the base IK_ITERATIONS_INIT=100 under-converges the dual-arm solve at the
# Raise-point (wrist 1.16092, wide 88mm span, DC1) -> jq_target ~9mm short -> arms pulled ~8mm inward (span
# 72mm vs 88mm INVARIANT#2). The gate_c2 per-arm probe reached err=0 at 200 iters; use a generous local
# count for the one-time P0 solve (cost negligible). Scoped to AC (base const unchanged, ops-rule sec24).
_AC_IK_ITERATIONS_P0 = 400


def clamp_pos_ko(ee_pos, ee_quat_xyzw):
    """DC2: koshape OPEN fingertip/clamp point.

    Offset along the wrist_3 LOCAL +Y (= world -Z "down" at the Rx(-90) koshape pose), magnitude
    EE_TO_PINCH_OPEN (UR5e+ko OPEN pinch drop). Replaces the Franka compute_clamp_pos (local +Z,
    0.220). LOCAL helper per blast-radius (the shared compute_clamp_pos stays Franka-faithful).
    """
    offset_local = np.array([0.0, +EE_TO_PINCH_OPEN, 0.0], dtype=np.float32)
    offset_world = quat_rotate_vec(ee_quat_xyzw, offset_local)
    return ee_pos + offset_world


class NewtonApproachCableMujocoEnv(VecEnv):
    """RSL-RL VecEnv: ApproachCable on the env7 mujoco-koshape substrate (UR5e×2 + Robotiq koshape).

    N physical worlds -> N RL environments (single 12D dual-arm agent per world). Fingers are always
    OPEN (approach is pre-grasp). The arm is kinematically re-posed via IK -> joint_q (SC2b, the Newton
    mujoco substrate norm, Rs-CONFIRMED 2026-06-26); the cable + contacts are the dynamic part.
    """

    # --- Action scaling (faithful v37) ---------------------------------------------------------------
    POS_ACTION_SCALE = 0.015  # 15mm per RL step EE position delta
    ROT_ACTION_SCALE = 0.05  # ~2.9° per RL step EE rotation delta (axis-angle rad)
    ADAPTIVE_POS_SCALE = True  # distance-adaptive pos scale for 1mm precision
    FINE_THRESHOLD = 0.050  # 50mm: below this, pos action scale shrinks linearly
    MIN_POS_SCALE = 0.0005  # 0.5mm: minimum pos action scale floor
    EE_XY_BOUND = 0.050  # ±50mm max XY drift of the IK target from the settled EE (anti-Brownian)
    INIT_XY_NOISE = 0.005  # ±5mm initial EE target randomization (tracked-target only on mujoco)
    MAX_EPISODE_STEPS = GRASP_TERMINAL_STEPS  # 200
    PHYSICS_STEPS_PER_RL = 10
    EXPLOSION_DIST_THRESH = 1.0  # early-term worlds where dist_pos > 1m (contact-divergence guard)

    # Ori-gated approach: suppress pos delta when near cable but ori not ready (faithful v37).
    CLOSE_ACTION_DAMPING = 0.3
    ORI_GATE_POS_THRESH = 0.010  # 10mm
    ORI_GATE_ORI_THRESH = 0.2618  # 15°

    # Target cable segment: per-arm nearest within ±GRIP_SEG_WINDOW (mid-split, see _compute_target_seg_indices).
    GRIP_SEG_WINDOW = 5  # ±5 segments

    # --- Reward: pose_match v37 (hybrid, non-negative shift [0,1]; idle@P0 ≈ 0 via R_PENALTY) --------
    EPS_POS = 0.015  # 15mm fine position decay [m]
    EPS_POS_MED = 0.10  # 100mm mid-range decay (bridges the 15mm-1m gradient desert)
    EPS_POS_COARSE = 1.0  # coarse long-range decay [m]
    EPS_ORI = 0.25  # ~14° orientation decay [rad]
    EPS_ORI_COARSE = 1.5  # ~86° coarse ori decay [rad]
    W_POS = 0.5  # per-arm pos weight (avg of 3 scales)
    W_ORI = 0.5  # per-arm ori weight (avg of 2 scales)
    R_STEP_BONUS = 5.0  # one-time bonus when BOTH arms reach the approach zone
    R_TASK_BONUS = 200.0  # v37 anti-hover: success must dominate hover
    W_HOLD = 0.0  # v37: eliminated (ori-gate damping handles it mechanically)
    # R_PENALTY re-derived (§18 ground-truth) at the NEW P0 (both arms ~91.8mm, ori~0): -(r_pos_P0+r_ori_P0).
    # The geometric estimate is ~ -(0.438 + 0.998) = -1.436. v37 anti-hover: idle@P0 ≈ 0.
    # TODO(%4-review): re-derive from MEASURED P0 ori in the CPU-smoke (the P0 IK move converges
    # POSITION-only -> actual r_ori_P0 ≤ 0.998; do NOT bank -1.436 on the geometric 0.0007 ori assumption).
    R_PENALTY = -1.436

    # --- Success thresholds (task_config SSOT -- do NOT hardcode overrides) --------------------------
    CLAMP_DIST_THRESH = T_DIST_APPROACH  # 12mm (Grip INIT_POS_NOISE handoff, INVARIANT)
    CLAMP_ORI_THRESH = T_ALIGN  # 10° (0.1745 rad)
    C5_SUSTAIN_STEPS = K_GRASP  # 5 sustained RL steps

    # --- Clip C1 pose (constant obs context; groove axis ≈ Y) ----------------------------------------
    CLIP1_POS = np.array([CLIP1_X, CLIP1_Y, CLIP1_Z], dtype=np.float32)
    CLIP1_QUAT_XYZW = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)  # identity

    # INVARIANT#1: success requires BOTH arms -> L arm obs must always be visible.
    OBS_L_ARM_MASK_PROB = 0.0

    def __init__(self, world_count=4, device="cuda:0", cfg=None):
        self.num_envs = world_count
        self.num_actions = 12
        self._total_env_steps = 0
        self.max_episode_length = self.MAX_EPISODE_STEPS
        self.device = device
        self.cfg = cfg or {}
        self._world_count = world_count

        self.episode_length_buf = torch.zeros(world_count, dtype=torch.long, device=device)
        self._target_seg_indices_r = None  # [world_count, n_target_segs]
        self._target_seg_indices_l = None
        self._success_sustain_count = np.zeros(world_count, dtype=np.int32)
        self._step_completed_right = np.zeros(world_count, dtype=bool)  # R_STEP bonus tracking
        self._last_actions = None  # [N, 12] tensor for r_hold (W_HOLD=0 -> unused, kept faithful)
        self._episode_count = 0
        self._randomize_cable_xy = False  # cable XY DR (off by default; mujoco seam = seed dr_xy)
        self._episode_success_buf = deque(maxlen=200)
        self._last_success_rate = 0.0

        # Per-world EE targets (tracked explicitly to avoid FK/body_q drift).
        self._ee_target_right = np.zeros((world_count, 3), dtype=np.float32)
        self._ee_target_left = np.zeros((world_count, 3), dtype=np.float32)
        self._ee_quat_right = np.zeros((world_count, 4), dtype=np.float32)  # xyzw
        self._ee_quat_left = np.zeros((world_count, 4), dtype=np.float32)  # xyzw

        # Temporal quat consistency (avoid w≈0 sign flip).
        _id4 = np.array([0, 0, 0, 1], dtype=np.float32)
        self._prev_clamp_r_quat = np.tile(_id4, (world_count, 1))
        self._prev_clamp_l_quat = np.tile(_id4, (world_count, 1))
        self._prev_seg_r_quat = np.tile(_id4, (world_count, 1))
        self._prev_seg_l_quat = np.tile(_id4, (world_count, 1))

        os.environ["NEWTON_DEVICE"] = device
        _tncr.DEVICE = device

        print(f"[ApproachCableMujocoEnv] Initializing: {world_count} worlds on {device} (backend=mujoco)")
        t0 = time.perf_counter()

        self._build_model()
        # No disk cache for the initial mujoco port: a body_q-only cache would NOT re-pose the mujoco
        # arm/cable (which are joint_q-authoritative) -> a silent-invalid restore. Build P0 fresh.
        # TODO(%4-review): add a joint_q-aware precondition cache once the substrate is validated.
        self._settle_cable()
        self._setup_p0_precondition()
        self._save_precondition_state()
        self._init_batched_ik_solver()

        print(
            f"[ApproachCableMujocoEnv] Ready in {time.perf_counter() - t0:.1f}s. "
            f"obs={self.num_obs}, act={self.num_actions}, worlds={world_count}"
        )

    # =====================================================================================================
    # Model Construction
    # =====================================================================================================

    def _build_model(self):
        """Build FK model + reuse the mujoco multi-world scene (UR5e+Robotiq koshape + cable + contacts)."""
        print("[ApproachCableMujocoEnv] Building FK model...")
        # Both arms OPEN (approach is pre-grasp -- fingers never close in this skill).
        self._fk_model, self._fk_state, fk_jq = build_fk_and_init(
            left_finger_pos=FINGER_OPEN_POS,
            right_finger_pos=FINGER_OPEN_POS,
            device=self.device,
        )
        self._per_world_fk_jq = np.tile(fk_jq, (self._world_count, 1))  # [N, joint_coord_count(=28)]

        print(f"[ApproachCableMujocoEnv] Building scene ({self._world_count} worlds, backend=mujoco)...")
        # REUSE the mujoco base scene: add_ur5e_robotiq×2 (A-1 VISIBLE pass + pad COLLIDE) + add_revolute_cable
        # + make_solver(backend=mujoco, enable_cable_contacts=True). add_support_clips=True (cable rests on
        # clips); add_target_clip=False (AC has no clip-groove target). enable_cable_contacts is wired
        # automatically inside build_multiworld_scene on the mujoco branch (MUST-ADD #4).
        scene = build_multiworld_scene(
            self._fk_model,
            self._fk_state,
            self._world_count,
            self.device,
            add_support_clips=True,
            add_target_clip=False,
        )
        self._model = scene["model"]
        self._solver = scene["solver"]
        self._state_0 = scene["state_0"]
        self._state_1 = scene["state_1"]
        self._control = scene["control"]
        self._contacts = scene["contacts"]
        self._bws = scene["bws"]
        self._jws = scene["jws"]  # JOINT-index world start (cable-joint range :_compute reset + dahl)
        self._cable_bodies = scene["cable_bodies"]
        self._cable_bodies_per_world = scene["cable_bodies_per_world"]
        self._cable_body_offset = scene["cable_body_offset"]
        self._bodies_per_world = scene["bodies_per_world"]

        # §23 fix: joint_q/joint_qd are COORD-indexed, but scene["jws"] (=model.joint_world_start) is a
        # JOINT index. The cable FREE root adds 6 extra coords/world (7 q-coords but 6 qd-coords), so a
        # joint-index slice is wrong for world>=1. Derive the authoritative per-world ARM coord starts
        # (q and qd SEPARATELY) from joint_q_start/joint_qd_start at each world's first (arm) joint.
        _jqs = self._model.joint_q_start.numpy()
        _jqds = self._model.joint_qd_start.numpy()
        _jws_joint = self._model.joint_world_start.numpy()
        self._arm_q_start = [int(_jqs[_jws_joint[w]]) for w in range(self._world_count)]
        self._arm_qd_start = [int(_jqds[_jws_joint[w]]) for w in range(self._world_count)]

        print(
            f"[ApproachCableMujocoEnv] Model: {self._model.body_count} bodies, "
            f"{self._model.joint_count} joints, solver={type(self._solver).__name__}"
        )

    # =====================================================================================================
    # Physics stepping (clean mujoco step -- no VBD finger/groove springs)
    # =====================================================================================================

    def _physics_step_all(self, substeps=None, sim_dt=None):
        """One physics frame for all worlds (clear_forces -> collide -> solver.step -> swap).

        No finger/groove spring forces: under mujoco the arm (incl. fingers) is articulated and posed
        from joint_q, so the VBD spring machinery is not used. Mirrors newton_skill_env_base.physics_step.
        """
        n_sub = substeps if substeps is not None else SIM_SUBSTEPS
        dt = sim_dt if sim_dt is not None else SIM_DT
        for _ in range(n_sub):
            self._state_0.clear_forces()
            self._model.collide(self._state_0, self._contacts)
            self._solver.step(self._state_0, self._state_1, self._control, self._contacts, dt)
            self._state_0, self._state_1 = self._state_1, self._state_0

    def _broadcast_arm_jointq(self):
        """Re-pose both arms' joint_q (SC2b) at the COORD-correct per-world offset (§23 fix).

        The base :func:`broadcast_jointq_to_all_worlds` indexes ``joint_q`` with
        ``model.joint_world_start`` (a JOINT index); the cable FREE root adds 6 extra coords/world, so
        that slice is wrong for world>=1 (world0 cable displaced + world1 arm un-posed in the smoke).
        This local version uses the authoritative per-world arm coord starts (q and qd separately).
        [base broadcast_jointq fix PROPOSED to %9 — it has the same latent bug for its own callers.]

        NO-KINEMATIC (Rs 2026-07-19): the re-pose body is REMOVED; raises unconditionally until
        the approach env is migrated to the POSITION-servo actuator path.
        """
        raise RuntimeError(
            "kinematic arm drive REMOVED (Rs directive 2026-07-19 kinematic complete-removal): "
            "approach env awaits actuator migration"
        )

    def _settle_cable(self):
        """Settle the cable (~2s sim time). Fail-closed: the arm hold awaits actuator migration."""
        print("[ApproachCableMujocoEnv] Settling cable (~2s; arm hold = actuator migration pending)...")
        settle_frames = int(2.0 / DT)
        for _ in range(settle_frames):
            # Hold the articulated arm against gravity every frame (SC2b overwrite; else the mujoco arm
            # falls). fk_state still holds the home config from build_fk_and_init.
            self._broadcast_arm_jointq()
            self._physics_step_all()
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        self._settled_grasp_x = float(np.mean(bq[self._cable_bodies[0], 0]))
        print(f"[ApproachCableMujocoEnv] Cable settled: mean_x={self._settled_grasp_x:.4f}")

    # =====================================================================================================
    # P0 Precondition (the raise-point: arms wide @ 88mm span, wrist 100mm above table)
    # =====================================================================================================

    def _setup_p0_precondition(self):
        """Move both arms to the NON-degenerate raise-point P0 (Rs-CONFIRMED frame ii, 2026-06-26).

        wrist Z = TABLE_HEIGHT + 0.100 + EE_TO_PINCH_OPEN = 1.16092 (koshape OPEN claw at 0.900, i.e.
        ~91mm ABOVE the cable center 0.809 -> dist_pos ≈ 91.8mm >> 12mm = NON-degenerate). XY span =
        WIDE_LEFT_Y(0.106)/WIDE_RIGHT_Y(0.194) = 88mm UNCHANGED (INVARIANT#2). DC1 koshape rot target.
        """
        print("[ApproachCableMujocoEnv] Setting up P0 precondition (raise-point)...")
        grasp_x = self._settled_grasp_x
        p0_ee_z = TABLE_HEIGHT + 0.100 + EE_TO_PINCH_OPEN  # 1.16092 (wrist; NOT the grasp-ready degenerate point)
        self._ik_move_all_worlds(
            (grasp_x, WIDE_LEFT_Y, p0_ee_z),
            (grasp_x, WIDE_RIGHT_Y, p0_ee_z),
            label="P0-UPRISE",
            converge_mm=2.0,  # tight: 10mm let the move break ~9mm short (t≈0.993) -> 78mm span vs 88 (INVARIANT#2)
        )
        self._hold_all_worlds(SETTLE_STEPS)
        print("[ApproachCableMujocoEnv] P0 complete -- raise-point reached")

    def _solve_ik_single_ko(self, target_left, target_right):
        """Solve dual-arm IK (P0 init) with the DC1 koshape rotation target, PER-ARM.

        A single COMBINED solve (both arms' pos+rot + a shared joint-limit objective) compromises the
        optimizer ~5mm/arm INWARD at the wide 88mm raise-point span (span 78mm vs 88mm INVARIANT#2). Solving
        each arm INDEPENDENTLY reaches err=0 (gate_c2 per-arm pure-IK proof), and is collision-safe at P0
        (arms are 88mm apart -- no inter-arm contact). Each solve starts from the FK home; we keep only
        that arm's joint slice (the other arm's joints from a given solve are free/discarded).
        """
        target_rot = wp.array([wp.vec4(*KO_ROT_TARGET_XYZW)], dtype=wp.vec4, device=self.device)
        fk_jq = self._fk_state.joint_q.numpy()
        jq_combined = fk_jq.copy()
        for ee_body, tgt, jslice in (
            (_LEFT_EE_BODY, target_left, slice(0, JOINTS_PER_ARM)),
            (_RIGHT_EE_BODY, target_right, slice(JOINTS_PER_ARM, 2 * JOINTS_PER_ARM)),
        ):
            objectives = [
                IKObjectivePosition(
                    link_index=ee_body,
                    link_offset=wp.vec3(0, 0, 0),
                    target_positions=wp.array([tgt], dtype=wp.vec3, device=self.device),
                    weight=1.0,
                ),
                IKObjectiveRotation(
                    link_index=ee_body, link_offset_rotation=wp.quat_identity(), target_rotations=target_rot, weight=0.5
                ),
                IKObjectiveJointLimit(
                    joint_limit_lower=self._fk_model.joint_limit_lower,
                    joint_limit_upper=self._fk_model.joint_limit_upper,
                    weight=10.0,
                ),
            ]
            ik_solver = IKSolver(self._fk_model, n_problems=1, objectives=objectives)
            jq_in = wp.array(fk_jq.reshape(1, -1), dtype=float, device=self.device)
            jq_out = wp.zeros((1, self._fk_model.joint_coord_count), dtype=float, device=self.device)
            ik_solver.step(jq_in, jq_out, iterations=_AC_IK_ITERATIONS_P0, step_size=IK_STEP_SIZE)
            jq_combined[jslice] = jq_out.numpy()[0][jslice]
        return jq_combined

    def _ik_move_all_worlds(self, target_left, target_right, label="MOVE", converge_mm=5.0):
        """Move both arms to target -- all worlds share the IK solution; mujoco joint_q re-pose driving."""
        jq_target = self._solve_ik_single_ko(target_left, target_right)
        if np.any(np.isnan(jq_target)):
            print(f"  [{label}] IK FAILED (NaN)")
            return False

        jq_start = self._fk_state.joint_q.numpy().copy()
        n_coords = self._fk_model.joint_coord_count
        finger_coords = set(GRIPPER_JOINT_RANGE) | {JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE}
        err_l = err_r = 0.0
        step = 0
        for step in range(MAX_MOVE_STEPS):
            t = min((step + 1) / MAX_MOVE_STEPS, 1.0)
            jq_interp = jq_start.copy()
            for d in range(n_coords):
                if d not in finger_coords:
                    jq_interp[d] = jq_start[d] + (jq_target[d] - jq_start[d]) * t

            self._fk_state.joint_q.assign(jq_interp)
            newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)
            self._broadcast_arm_jointq()
            self._physics_step_all()

            if (step + 1) % 10 == 0:
                wp.synchronize()
                bq = self._state_0.body_q.numpy()
                ws0 = self._bws[0]
                left_ee_pos = bq[ws0 + _LEFT_EE_BODY][:3]
                right_ee_pos = bq[ws0 + _RIGHT_EE_BODY][:3]
                err_l = np.linalg.norm(left_ee_pos - np.array(target_left)) * 1000
                err_r = np.linalg.norm(right_ee_pos - np.array(target_right)) * 1000
                if max(err_l, err_r) < converge_mm:
                    break
        print(f"  [{label}] Done: steps={step + 1}, err_L={err_l:.1f}mm, err_R={err_r:.1f}mm")
        return True

    def _hold_all_worlds(self, n_frames):
        """Hold the current FK pose for n_frames physics frames (mujoco joint_q re-pose)."""
        for _ in range(n_frames):
            self._broadcast_arm_jointq()
            self._physics_step_all()

    def _save_precondition_state(self):
        """Cache the P0-complete settled state for episode reset."""
        wp.synchronize()
        self._settled_body_q = self._state_0.body_q.numpy().copy()
        self._settled_body_qd = self._state_0.body_qd.numpy().copy()
        self._settled_fk_jq = self._fk_state.joint_q.numpy().copy()  # [28] arm-pair coords
        for w in range(self._world_count):
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()

        self._target_seg_indices_r, self._target_seg_indices_l = self._compute_target_seg_indices(self._settled_body_q)

        fk_bq = self._fk_state.body_q.numpy()
        self._settled_ee_r_pos = fk_bq[_RIGHT_EE_BODY][:3].copy()
        self._settled_ee_r_quat = fk_bq[_RIGHT_EE_BODY][3:7].copy()
        self._settled_ee_l_pos = fk_bq[_LEFT_EE_BODY][:3].copy()
        self._settled_ee_l_quat = fk_bq[_LEFT_EE_BODY][3:7].copy()

        for w in range(self._world_count):
            self._ee_target_right[w] = self._settled_ee_r_pos.copy()
            self._ee_target_left[w] = self._settled_ee_l_pos.copy()
            self._ee_quat_right[w] = self._settled_ee_r_quat.copy()
            self._ee_quat_left[w] = self._settled_ee_l_quat.copy()
        print(
            f"[ApproachCableMujocoEnv] P0 saved: EE_R={self._settled_ee_r_pos}, EE_L={self._settled_ee_l_pos}, "
            f"seg_r={self._target_seg_indices_r[0]}, seg_l={self._target_seg_indices_l[0]}"
        )

    # =====================================================================================================
    # Batched IK Solver (RL stepping) -- DC1 koshape rotation target
    # =====================================================================================================

    def _init_batched_ik_solver(self):
        """Cached IKSolver(n_problems=world_count). Mirrors NewtonGripEnv but with the KO rot target."""
        N = self._world_count
        rot_quat = wp.vec4(*KO_ROT_TARGET_XYZW)

        self._ik_obj_pos_left = IKObjectivePosition(
            link_index=_LEFT_EE_BODY,
            link_offset=wp.vec3(0, 0, 0),
            target_positions=wp.zeros(N, dtype=wp.vec3, device=self.device),
            weight=1.0,
        )
        self._ik_obj_pos_right = IKObjectivePosition(
            link_index=_RIGHT_EE_BODY,
            link_offset=wp.vec3(0, 0, 0),
            target_positions=wp.zeros(N, dtype=wp.vec3, device=self.device),
            weight=1.0,
        )
        self._ik_obj_rot_left = IKObjectiveRotation(
            link_index=_LEFT_EE_BODY,
            link_offset_rotation=wp.quat_identity(),
            target_rotations=wp.array([rot_quat] * N, dtype=wp.vec4, device=self.device),
            weight=0.5,
        )
        self._ik_obj_rot_right = IKObjectiveRotation(
            link_index=_RIGHT_EE_BODY,
            link_offset_rotation=wp.quat_identity(),
            target_rotations=wp.array([rot_quat] * N, dtype=wp.vec4, device=self.device),
            weight=0.5,
        )
        self._ik_obj_jlimit = IKObjectiveJointLimit(
            joint_limit_lower=self._fk_model.joint_limit_lower,
            joint_limit_upper=self._fk_model.joint_limit_upper,
            weight=10.0,
        )
        objectives = [
            self._ik_obj_pos_left,
            self._ik_obj_pos_right,
            self._ik_obj_rot_left,
            self._ik_obj_rot_right,
            self._ik_obj_jlimit,
        ]
        self._ik_solver_batch = IKSolver(self._fk_model, n_problems=N, objectives=objectives)

        coord_count = self._fk_model.joint_coord_count
        self._ik_jq_in = wp.zeros((N, coord_count), dtype=float, device=self.device)
        self._ik_jq_out = wp.zeros((N, coord_count), dtype=float, device=self.device)
        print(f"[ApproachCableMujocoEnv] Batched IK solver: n_problems={N}, joint_coords={coord_count}")

    def _solve_ik_batch(self, targets_left_np, targets_right_np, jq_starts_np):
        """Solve IK for all worlds in one batched, warm-started call. Returns [N, coord_count] numpy."""
        self._ik_obj_pos_left.set_target_positions(wp.array(targets_left_np, dtype=wp.vec3, device=self.device))
        self._ik_obj_pos_right.set_target_positions(wp.array(targets_right_np, dtype=wp.vec3, device=self.device))
        self._ik_jq_in.assign(jq_starts_np)
        self._ik_solver_batch.step(self._ik_jq_in, self._ik_jq_out, iterations=IK_ITERATIONS_RL, step_size=IK_STEP_SIZE)
        return self._ik_jq_out.numpy()

    # =====================================================================================================
    # Target Segment Computation (per-arm MID-SPLIT -- INVARIANT#2 anti-collapse)
    # =====================================================================================================

    def _compute_target_seg_indices(self, bq):
        """Per-arm target cable seg indices (±GRIP_SEG_WINDOW), MID-SPLIT so arms can't share a seg.

        Cable index 0 = lowest Y (cable runs +Y, left base at -Y): the LEFT arm searches the lower-Y
        half [0, mid], the RIGHT arm the upper-Y half [mid, n-1]. Prevents a span->0 reward-hack where
        both arms collapse onto the same segment (pre-check ISSUE-4). Fingertip = clamp_pos_ko (DC2).
        """
        n_cable = self._cable_bodies_per_world
        win = self.GRIP_SEG_WINDOW
        n_seg = 2 * win + 1
        result_r = np.zeros((self._world_count, n_seg), dtype=np.int32)
        result_l = np.zeros((self._world_count, n_seg), dtype=np.int32)
        mid = n_cable // 2
        for w in range(self._world_count):
            ws = self._bws[w]
            cable_pos = bq[self._cable_bodies[w], :3]

            right_ee_idx = ws + _RIGHT_EE_BODY
            right_tip = clamp_pos_ko(bq[right_ee_idx][:3], bq[right_ee_idx][3:7])
            right_dists = np.linalg.norm(cable_pos[mid:n_cable] - right_tip, axis=1)
            right_seg = mid + int(np.argmin(right_dists))
            result_r[w] = np.clip(np.arange(right_seg - win, right_seg + win + 1), 0, n_cable - 1)

            left_ee_idx = ws + _LEFT_EE_BODY
            left_tip = clamp_pos_ko(bq[left_ee_idx][:3], bq[left_ee_idx][3:7])
            left_dists = np.linalg.norm(cable_pos[0 : mid + 1] - left_tip, axis=1)
            left_seg = int(np.argmin(left_dists))
            result_l[w] = np.clip(np.arange(left_seg - win, left_seg + win + 1), 0, n_cable - 1)
        return result_r, result_l

    # =====================================================================================================
    # Reset (mujoco: body_q restore + AUTHORITATIVE joint_q seeding of arm + cable)
    # =====================================================================================================

    def set_cable_xy_randomize(self, enabled: bool) -> None:
        """Enable/disable cable XY ±CABLE_XY_DR_AMPLITUDE randomization at the next reset (default off)."""
        self._randomize_cable_xy = bool(enabled)

    def _reset_worlds(self, env_ids):
        """Reset specified worlds to the P0 settled state (per-world slice reset).

        mujoco is joint_q-authoritative: the body_q restore is kept (VBD-tolerant helpers) but the
        arm + cable are re-posed by SEEDING joint_q (the proven C-1 PRIMARY path,
        test_newton_clip_routing:3670). Without the joint_q seed the mujoco solver would re-derive
        body_q from the in-flight (stale) joint_q -> a silent-invalid reset.
        TODO(%4-review): verify the per-world cable-joint index arithmetic
        (cable FREE root = jws[w] + 2*JOINTS_PER_ARM) against the build_multiworld_scene joint layout
        assert in the CPU-smoke (reset world 0, step, confirm cable returns to the settled Z band).
        """
        if len(env_ids) == 0:
            return

        bq = self._state_0.body_q.numpy()
        bqd = self._state_0.body_qd.numpy()
        # S4b: SolverMuJoCo has no body_q_prev (VBD-only); None-tolerant (reset carried by joint_q seeding).
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
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()
            self._step_completed_right[w] = False
            self._success_sustain_count[w] = 0
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
            _id4 = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_clamp_r_quat[w] = _id4.copy()
            self._prev_clamp_l_quat[w] = _id4.copy()
            self._prev_seg_r_quat[w] = _id4.copy()
            self._prev_seg_l_quat[w] = _id4.copy()

            # Initial EE XY noise: tracked target ONLY (mujoco body_q is re-derived from joint_q, so a
            # body_q noise write would not stick -- the first step's IK naturally moves to the noised target).
            if self.INIT_XY_NOISE > 0:
                noise_xy_r = np.random.uniform(-self.INIT_XY_NOISE, self.INIT_XY_NOISE, size=2)
                self._ee_target_right[w][0] += noise_xy_r[0]
                self._ee_target_right[w][1] += noise_xy_r[1]
                noise_xy_l = np.random.uniform(-self.INIT_XY_NOISE, self.INIT_XY_NOISE, size=2)
                self._ee_target_left[w][0] += noise_xy_l[0]
                self._ee_target_left[w][1] += noise_xy_l[1]

            if self._last_actions is not None:
                self._last_actions[w] = 0.0
            self.episode_length_buf[w] = 0

        # Push body_q/bqd (None prev tolerated on mujoco).
        assign_world_states_to_sim(self._state_0, self._solver, bq, bqd, prev)

        # NO-KINEMATIC (Rs 2026-07-19): the arm joint_q reset re-pose is REMOVED; raises
        # unconditionally until the approach env is migrated to the POSITION-servo actuator path.
        raise RuntimeError(
            "kinematic arm drive REMOVED (Rs directive 2026-07-19 kinematic complete-removal): "
            "approach env awaits actuator migration"
        )

        for w in env_ids:
            w = int(w)
            # cable joints follow the 28 arm joints in each world's slice (FREE root first).
            cable_joints_w = list(
                range(self._jws[w] + _N_ARM_JOINTS, self._jws[w] + _N_ARM_JOINTS + self._cable_bodies_per_world)
            )
            root7, seg_angles = derive_cable_joint_q_from_tangents(self._settled_body_q, self._cable_bodies[w])
            dr_xy = (0.0, 0.0)
            if self._randomize_cable_xy and CABLE_XY_DR_AMPLITUDE[0] > 0.0:
                amp_x, amp_y = CABLE_XY_DR_AMPLITUDE
                dr_xy = (
                    float(np.random.uniform(-amp_x, amp_x)),
                    float(np.random.uniform(-amp_y, amp_y)),
                )
            # seed_cable_joint_state runs eval_fk on the whole model -> body_q becomes consistent with
            # the just-written arm + cable joint_q (non-reset worlds are idempotent: re-derived from their
            # own unchanged joint_q).
            seed_cable_joint_state(self._state_0, self._model, cable_joints_w, root7, seg_angles, dr_xy=dr_xy)

        # Update target seg indices for reset worlds only (preserve others).
        new_r, new_l = self._compute_target_seg_indices(self._state_0.body_q.numpy())
        for w in env_ids:
            w = int(w)
            self._target_seg_indices_r[w] = new_r[w]
            self._target_seg_indices_l[w] = new_l[w]

        reset_dahl_friction_for_envs(self._solver, self._jws, env_ids)
        self._episode_count += len(env_ids)

    # =====================================================================================================
    # Observation (42D)
    # =====================================================================================================

    def _compute_obs_batch(self):
        """Compute observations for all worlds. Returns [N, 42] tensor."""
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        obs_np = np.zeros((self._world_count, 42), dtype=np.float32)

        for w in range(self._world_count):
            ws = self._bws[w]

            # Clamp pose (koshape DC2 fingertip). NOTE: clamp_pos_ko (NOT the Franka extract_clamp_pose)
            # -- keeps obs pos_error consistent with the ko reward dist (§21 obs-reward integrity).
            # TODO(%4-review): the VBD-AC reference obs used extract_clamp_pose (Franka compute_clamp_pos,
            # local +Z 0.220) while its reward used clamp_pos_ko -- a latent obs/reward offset mismatch.
            # This port uses clamp_pos_ko in BOTH; confirm ko-consistency is the intended fix.
            # Bug #2 fix (faithful): temporal_quat_consistency on OBS quats avoids the w≈0 sign-flip
            # discontinuity. (The reward path uses the un-temporally-corrected quat, matching VBD-AC.)
            ee_r_idx = ws + _RIGHT_EE_BODY
            ee_r_pos = bq[ee_r_idx][:3]
            ee_r_quat = bq[ee_r_idx][3:7]
            clamp_r_pos = clamp_pos_ko(ee_r_pos, ee_r_quat)
            clamp_r_quat = temporal_quat_consistency(normalize_quat_w_positive(ee_r_quat), self._prev_clamp_r_quat[w])
            self._prev_clamp_r_quat[w] = clamp_r_quat.copy()

            ee_l_idx = ws + _LEFT_EE_BODY
            ee_l_pos = bq[ee_l_idx][:3]
            ee_l_quat = bq[ee_l_idx][3:7]
            clamp_l_pos = clamp_pos_ko(ee_l_pos, ee_l_quat)
            clamp_l_quat = temporal_quat_consistency(normalize_quat_w_positive(ee_l_quat), self._prev_clamp_l_quat[w])
            self._prev_clamp_l_quat[w] = clamp_l_quat.copy()

            # Finger openings (driver joints; both arms always OPEN in AC).
            fk_jq = self._per_world_fk_jq[w]
            r_finger_opening = (
                fk_jq[_RIGHT_ARM_JOINT_OFFSET + GRIPPER_DRIVER_JOINT_IDX[0]]
                + fk_jq[_RIGHT_ARM_JOINT_OFFSET + GRIPPER_DRIVER_JOINT_IDX[1]]
            )
            l_finger_opening = fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] + fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]]

            # Target cable point: interpolated nearest on the piecewise-linear cable (per arm).
            cable_pos = bq[self._cable_bodies[w], :3]
            seg_pos, seg_tangent, _ = find_nearest_cable_point(cable_pos, clamp_r_pos, self._target_seg_indices_r[w])
            seg_quat = temporal_quat_consistency(
                normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent, base_quat=KO_BASE_HAND_DOWN_QUAT)),
                self._prev_seg_r_quat[w],
            )
            self._prev_seg_r_quat[w] = seg_quat.copy()

            seg_pos_l, seg_tangent_l, _ = find_nearest_cable_point(cable_pos, clamp_l_pos, self._target_seg_indices_l[w])
            grasp_quat_l = temporal_quat_consistency(
                normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_l, base_quat=KO_BASE_HAND_DOWN_QUAT)),
                self._prev_seg_l_quat[w],
            )
            self._prev_seg_l_quat[w] = grasp_quat_l.copy()

            ori_error_aa = compute_ori_error_axis_angle(clamp_r_quat, seg_quat)
            pos_error = clamp_r_pos - seg_pos
            ori_error_aa_l = compute_ori_error_axis_angle(clamp_l_quat, grasp_quat_l)
            pos_error_l = clamp_l_pos - seg_pos_l

            obs_np[w, 0:3] = clamp_r_pos
            obs_np[w, 3:7] = clamp_r_quat
            obs_np[w, 7] = r_finger_opening
            obs_np[w, 8:11] = clamp_l_pos
            obs_np[w, 11:15] = clamp_l_quat
            obs_np[w, 15] = l_finger_opening
            obs_np[w, 16:19] = seg_pos
            obs_np[w, 19:23] = seg_quat
            obs_np[w, 23:26] = self.CLIP1_POS
            obs_np[w, 26:30] = self.CLIP1_QUAT_XYZW
            obs_np[w, 30:33] = ori_error_aa
            obs_np[w, 33:36] = pos_error
            obs_np[w, 36:39] = ori_error_aa_l
            obs_np[w, 39:42] = pos_error_l

        np.nan_to_num(obs_np, copy=False, nan=0.0)
        obs = torch.from_numpy(obs_np).to(device=self.device)
        # INVARIANT#1: OBS_L_ARM_MASK_PROB=0 -> both arms always visible (success requires both).
        if self.OBS_L_ARM_MASK_PROB > 0:
            mask = torch.rand(obs.shape[0], device=obs.device) < self.OBS_L_ARM_MASK_PROB
            obs[mask, 8:16] = 0.0
            obs[mask, 36:42] = 0.0
        return obs

    # =====================================================================================================
    # Reward / Done (v37 pose_match)
    # =====================================================================================================

    def _compute_rewards_dones_batch(self):
        """Reward v37: R_pos(3-scale) + R_ori(2-scale) + R_STEP + R_TASK + R_PENALTY. Returns (r, done, extras)."""
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        N = self._world_count

        rewards = np.zeros(N, dtype=np.float32)
        dones = np.zeros(N, dtype=np.int64)
        timeouts = np.zeros(N, dtype=np.int64)
        successes = np.zeros(N, dtype=np.float32)
        rc_r_pos = np.zeros(N, dtype=np.float32)
        rc_r_ori = np.zeros(N, dtype=np.float32)
        rc_r_step = np.zeros(N, dtype=np.float32)
        rc_dist = np.zeros(N, dtype=np.float32)
        rc_ori_dist = np.zeros(N, dtype=np.float32)
        rc_dist_l = np.zeros(N, dtype=np.float32)
        rc_ori_dist_l = np.zeros(N, dtype=np.float32)
        rc_explosion = np.zeros(N, dtype=np.bool_)

        for w in range(N):
            ws = self._bws[w]

            ee_r_idx = ws + _RIGHT_EE_BODY
            ee_r_pos = bq[ee_r_idx][:3]
            ee_r_quat = bq[ee_r_idx][3:7]
            clamp_r_pos = clamp_pos_ko(ee_r_pos, ee_r_quat)
            clamp_r_quat = normalize_quat_w_positive(ee_r_quat)

            ee_l_idx = ws + _LEFT_EE_BODY
            ee_l_pos = bq[ee_l_idx][:3]
            ee_l_quat = bq[ee_l_idx][3:7]
            clamp_l_pos = clamp_pos_ko(ee_l_pos, ee_l_quat)
            clamp_l_quat = normalize_quat_w_positive(ee_l_quat)

            cable_pos = bq[self._cable_bodies[w], :3]
            seg_pos, seg_tangent, dist_pos = find_nearest_cable_point(
                cable_pos, clamp_r_pos, self._target_seg_indices_r[w]
            )
            grasp_target_quat = normalize_quat_w_positive(
                compute_hand_quat_for_cable(seg_tangent, base_quat=KO_BASE_HAND_DOWN_QUAT)
            )
            dist_ori = quat_distance(clamp_r_quat, grasp_target_quat)

            _, seg_tangent_l, dist_pos_l = find_nearest_cable_point(
                cable_pos, clamp_l_pos, self._target_seg_indices_l[w]
            )
            grasp_target_quat_l = normalize_quat_w_positive(
                compute_hand_quat_for_cable(seg_tangent_l, base_quat=KO_BASE_HAND_DOWN_QUAT)
            )
            dist_ori_l = quat_distance(clamp_l_quat, grasp_target_quat_l)

            # ---- R_pos: 3-scale hybrid (per arm avg of 3), summed both arms (non-negative [0,1]) ----
            r_fine_r = math.exp(-dist_pos / self.EPS_POS)
            r_med_r = math.exp(-dist_pos / self.EPS_POS_MED)
            r_coarse_r = math.exp(-dist_pos / self.EPS_POS_COARSE)
            r_fine_l = math.exp(-dist_pos_l / self.EPS_POS)
            r_med_l = math.exp(-dist_pos_l / self.EPS_POS_MED)
            r_coarse_l = math.exp(-dist_pos_l / self.EPS_POS_COARSE)
            r_pos = self.W_POS * ((r_fine_r + r_med_r + r_coarse_r) / 3 + (r_fine_l + r_med_l + r_coarse_l) / 3)

            # ---- R_ori: 2-scale (per arm avg of 2), summed both arms ----
            r_ori_r = (math.exp(-dist_ori / self.EPS_ORI) + math.exp(-dist_ori / self.EPS_ORI_COARSE)) / 2
            r_ori_l = (math.exp(-dist_ori_l / self.EPS_ORI) + math.exp(-dist_ori_l / self.EPS_ORI_COARSE)) / 2
            r_ori = self.W_ORI * (r_ori_r + r_ori_l)

            # ---- R_step: one-time bonus when BOTH arms reach the approach zone (pos ∧ ori) ----
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

            # ---- SUCCESS: BOTH arms pos ∧ ori ∧ sustained(K_GRASP). Finger close is NOT this skill. ----
            clamp_pos_ok = dist_pos < self.CLAMP_DIST_THRESH and dist_pos_l < self.CLAMP_DIST_THRESH
            clamp_ori_ok = dist_ori < self.CLAMP_ORI_THRESH and dist_ori_l < self.CLAMP_ORI_THRESH
            if clamp_pos_ok and clamp_ori_ok:
                self._success_sustain_count[w] += 1
            else:
                self._success_sustain_count[w] = 0
            success = self._success_sustain_count[w] >= self.C5_SUSTAIN_STEPS
            r_task_val = self.R_TASK_BONUS if success else 0.0

            # ---- r_hold: W_HOLD=0 in v37 (eliminated; kept faithful, gated off) ----
            r_hold_val = 0.0
            if self._last_actions is not None and self.W_HOLD > 0:
                a_l = self._last_actions[w, 6:12] * self.CLOSE_ACTION_DAMPING
                r_hold_val = -self.W_HOLD * float(torch.sum(a_l**2))

            # ---- contact-divergence guard (NaN-safe: IEEE 754 NaN > x is False) ----
            explosion = (
                dist_pos > self.EXPLOSION_DIST_THRESH
                or dist_pos_l > self.EXPLOSION_DIST_THRESH
                or math.isnan(dist_pos)
                or math.isnan(dist_pos_l)
            )
            if explosion:
                r = -10.0  # fixed penalty: clear signal without inf-gradient contamination
            else:
                r = r_pos + r_ori + r_step_val + r_task_val + self.R_PENALTY + r_hold_val
                if math.isnan(r):
                    r = self.R_PENALTY

            timeout = self.episode_length_buf[w].item() >= self.max_episode_length
            done = success or timeout or explosion

            rewards[w] = r
            rc_r_pos[w] = r_pos
            rc_r_ori[w] = r_ori
            rc_r_step[w] = r_step_val
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
            rc_explosion[w] = explosion
            dones[w] = int(done)
            # ⛔ TIMEOUTS PURITY (MUST-ADD #1, prohibited.md value_loss-105× history): time_outs =
            # MAX_EPISODE_STEPS reached ONLY. success / explosion are TRUE terminals (value=0) and MUST
            # be excluded -- RSL-RL PPO bootstraps γV(s_{T+1}) on timeouts; leaking a terminal there
            # pollutes value targets (CLAUDE.md timeouts-contamination prohibition).
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
                    "/reward/r_total": float(np.mean(rewards)),
                    "/metrics/dist_pos_mean": float(np.nanmean(rc_dist)),
                    "/metrics/dist_pos_median": float(np.nanmedian(rc_dist)),
                    "/metrics/dist_pos_bottleneck_median": float(np.nanmedian(np.maximum(rc_dist, rc_dist_l))),
                    "/metrics/dist_ori_median": float(np.nanmedian(rc_ori_dist)),
                    "/metrics/dist_pos_l_median": float(np.nanmedian(rc_dist_l)),
                    "/metrics/dist_ori_l_median": float(np.nanmedian(rc_ori_dist_l)),
                    "/metrics/explosion_count": int(np.sum(rc_explosion)),
                },
                "log_per_world": {
                    "dist_pos": rc_dist.copy(),
                    "dist_ori": rc_ori_dist.copy(),
                    "dist_pos_l": rc_dist_l.copy(),
                    "dist_ori_l": rc_ori_dist_l.copy(),
                    "reward": rewards.copy(),
                    "success": successes.copy(),
                    "explosion": rc_explosion.copy(),
                },
            },
        )

    # =====================================================================================================
    # Action Application (12D dual-arm -> batched IK -> mujoco joint_q re-pose)
    # =====================================================================================================

    def _apply_actions_batch(self, actions):
        """Apply per-world 12D actions (pos + rot deltas) via batched IK + mujoco joint_q re-pose.

        actions [N, 12]: [0:3] R pos, [3:6] R rot (axis-angle), [6:9] L pos, [9:12] L rot.
        The rot-delta accumulates into the IK rot target (new_quat = delta ∘ current, from KO_ROT) so
        the orientation stays AGENT-CONTROLLABLE (pre-check ISSUE-1 CRITICAL). Driving = per-world
        joint_q write (SC2b), NOT body_q.assign (Rs-CONFIRMED 2026-06-26).
        """
        N = self._world_count
        actions_np = actions.cpu().numpy()

        wp.synchronize()
        bq = self._state_0.body_q.numpy()

        # --- Adaptive per-arm pos scale (independent per arm) ---
        if self.ADAPTIVE_POS_SCALE:
            r_pos_scales = np.full(N, self.POS_ACTION_SCALE, dtype=np.float32)
            l_pos_scales = np.full(N, self.POS_ACTION_SCALE, dtype=np.float32)
            for w in range(N):
                ws = self._bws[w]
                cable_pos = bq[self._cable_bodies[w], :3]
                ee_r_idx = ws + _RIGHT_EE_BODY
                clamp_r = clamp_pos_ko(bq[ee_r_idx][:3], bq[ee_r_idx][3:7])
                _, _, dist_r = find_nearest_cable_point(cable_pos, clamp_r, self._target_seg_indices_r[w])
                r_pos_scales[w] = max(self.MIN_POS_SCALE, self.POS_ACTION_SCALE * min(1.0, dist_r / self.FINE_THRESHOLD))
                ee_l_idx = ws + _LEFT_EE_BODY
                clamp_l = clamp_pos_ko(bq[ee_l_idx][:3], bq[ee_l_idx][3:7])
                _, _, dist_l = find_nearest_cable_point(cable_pos, clamp_l, self._target_seg_indices_l[w])
                l_pos_scales[w] = max(self.MIN_POS_SCALE, self.POS_ACTION_SCALE * min(1.0, dist_l / self.FINE_THRESHOLD))
            r_pos_delta = actions_np[:, 0:3] * r_pos_scales[:, None]
            l_pos_delta = actions_np[:, 6:9] * l_pos_scales[:, None]
        else:
            r_pos_delta = actions_np[:, 0:3] * self.POS_ACTION_SCALE
            l_pos_delta = actions_np[:, 6:9] * self.POS_ACTION_SCALE

        r_rot_delta = actions_np[:, 3:6] * self.ROT_ACTION_SCALE
        l_rot_delta = actions_np[:, 9:12] * self.ROT_ACTION_SCALE

        # --- Ori-gated approach: damp pos delta when near cable but ori not ready (faithful v37) ---
        for w in range(N):
            ws = self._bws[w]
            cable_pos = bq[self._cable_bodies[w], :3]
            ee_r_idx = ws + _RIGHT_EE_BODY
            clamp_r = clamp_pos_ko(bq[ee_r_idx][:3], bq[ee_r_idx][3:7])
            _, seg_t_r, dist_r = find_nearest_cable_point(cable_pos, clamp_r, self._target_seg_indices_r[w])
            ori_r = quat_distance(
                normalize_quat_w_positive(bq[ee_r_idx][3:7]),
                normalize_quat_w_positive(compute_hand_quat_for_cable(seg_t_r, base_quat=KO_BASE_HAND_DOWN_QUAT)),
            )
            if dist_r < self.ORI_GATE_POS_THRESH and ori_r > self.ORI_GATE_ORI_THRESH:
                r_pos_delta[w] *= self.CLOSE_ACTION_DAMPING
            ee_l_idx = ws + _LEFT_EE_BODY
            clamp_l = clamp_pos_ko(bq[ee_l_idx][:3], bq[ee_l_idx][3:7])
            _, seg_t_l, dist_l = find_nearest_cable_point(cable_pos, clamp_l, self._target_seg_indices_l[w])
            ori_l = quat_distance(
                normalize_quat_w_positive(bq[ee_l_idx][3:7]),
                normalize_quat_w_positive(compute_hand_quat_for_cable(seg_t_l, base_quat=KO_BASE_HAND_DOWN_QUAT)),
            )
            if dist_l < self.ORI_GATE_POS_THRESH and ori_l > self.ORI_GATE_ORI_THRESH:
                l_pos_delta[w] *= self.CLOSE_ACTION_DAMPING

        # --- Per-world EE position + rotation targets ---
        targets_left = np.zeros((N, 3))
        targets_right = np.zeros((N, 3))
        rot_targets_left = []
        rot_targets_right = []
        jq_starts = np.array(self._per_world_fk_jq[:N])

        # Fingers always OPEN (approach is pre-grasp).
        for w in range(N):
            jq_starts[w, _RIGHT_ARM_JOINT_OFFSET + GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
            jq_starts[w, _RIGHT_ARM_JOINT_OFFSET + GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS
            jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
            jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS

        for w in range(N):
            # Right EE position: tracked target + delta, XY anti-Brownian clamp, Z koshape-floor clamp.
            target_r = self._ee_target_right[w].copy() + r_pos_delta[w]
            target_r[0] = np.clip(
                target_r[0], self._settled_ee_r_pos[0] - self.EE_XY_BOUND, self._settled_ee_r_pos[0] + self.EE_XY_BOUND
            )
            target_r[1] = np.clip(
                target_r[1], self._settled_ee_r_pos[1] - self.EE_XY_BOUND, self._settled_ee_r_pos[1] + self.EE_XY_BOUND
            )
            target_r[2] = np.clip(target_r[2], EE_Z_FLOOR_KO, EE_Z_SAFETY_UPPER)
            targets_right[w] = target_r
            self._ee_target_right[w] = target_r.copy()

            # Right EE rotation: new_quat = delta ∘ current (free accumulation -> agent-controllable ori).
            delta_r_quat = axis_angle_to_quat_xyzw(r_rot_delta[w])
            new_r_quat = quat_multiply_xyzw(delta_r_quat, self._ee_quat_right[w])
            new_r_quat = new_r_quat / np.linalg.norm(new_r_quat)
            self._ee_quat_right[w] = new_r_quat.copy()
            rot_targets_right.append(
                wp.vec4(float(new_r_quat[0]), float(new_r_quat[1]), float(new_r_quat[2]), float(new_r_quat[3]))
            )

            # Left EE position.
            target_l = self._ee_target_left[w].copy() + l_pos_delta[w]
            target_l[0] = np.clip(
                target_l[0], self._settled_ee_l_pos[0] - self.EE_XY_BOUND, self._settled_ee_l_pos[0] + self.EE_XY_BOUND
            )
            target_l[1] = np.clip(
                target_l[1], self._settled_ee_l_pos[1] - self.EE_XY_BOUND, self._settled_ee_l_pos[1] + self.EE_XY_BOUND
            )
            target_l[2] = np.clip(target_l[2], EE_Z_FLOOR_KO, EE_Z_SAFETY_UPPER)
            targets_left[w] = target_l
            self._ee_target_left[w] = target_l.copy()

            # Left EE rotation.
            delta_l_quat = axis_angle_to_quat_xyzw(l_rot_delta[w])
            new_l_quat = quat_multiply_xyzw(delta_l_quat, self._ee_quat_left[w])
            new_l_quat = new_l_quat / np.linalg.norm(new_l_quat)
            self._ee_quat_left[w] = new_l_quat.copy()
            rot_targets_left.append(
                wp.vec4(float(new_l_quat[0]), float(new_l_quat[1]), float(new_l_quat[2]), float(new_l_quat[3]))
            )

        self._ik_obj_rot_left.set_target_rotations(wp.array(rot_targets_left, dtype=wp.vec4, device=self.device))
        self._ik_obj_rot_right.set_target_rotations(wp.array(rot_targets_right, dtype=wp.vec4, device=self.device))

        jq_targets = self._solve_ik_batch(targets_left, targets_right, jq_starts)

        nan_mask = np.any(np.isnan(jq_targets), axis=1)
        if np.any(nan_mask):
            jq_targets[nan_mask] = jq_starts[nan_mask]

        # Preserve finger positions (OPEN) in the IK output.
        for w in range(N):
            jq_targets[w, _RIGHT_ARM_JOINT_OFFSET + GRIPPER_DRIVER_JOINT_IDX[0]] = jq_starts[
                w, _RIGHT_ARM_JOINT_OFFSET + GRIPPER_DRIVER_JOINT_IDX[0]
            ]
            jq_targets[w, _RIGHT_ARM_JOINT_OFFSET + GRIPPER_DRIVER_JOINT_IDX[1]] = jq_starts[
                w, _RIGHT_ARM_JOINT_OFFSET + GRIPPER_DRIVER_JOINT_IDX[1]
            ]
            jq_targets[w, GRIPPER_DRIVER_JOINT_IDX[0]] = jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[0]]
            jq_targets[w, GRIPPER_DRIVER_JOINT_IDX[1]] = jq_starts[w, GRIPPER_DRIVER_JOINT_IDX[1]]

        # --- DRIVE: the former per-frame arm joint_q OVERWRITE (SC2b mujoco kinematic re-pose) is
        # REMOVED (Rs 2026-07-19 kinematic complete-removal); raises unconditionally until the
        # approach env is migrated to the POSITION-servo actuator path. ---
        raise RuntimeError(
            "kinematic arm drive REMOVED (Rs directive 2026-07-19 kinematic complete-removal): "
            "approach env awaits actuator migration"
        )

        for w in range(N):
            self._per_world_fk_jq[w] = jq_targets[w].copy()

    # =====================================================================================================
    # RSL-RL VecEnv Interface
    # =====================================================================================================

    @property
    def num_obs(self):
        # 42D proprioceptive (DECISION: dropped the VBD-AC 45D pad -- the IC consumer that needed it is
        # DELETED, LEDGER item3). No visual obs in this port.
        return 42

    def get_observations(self) -> tuple[torch.Tensor, dict]:
        obs = self._compute_obs_batch()
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)
        return obs, {"observations": {}}

    def reset(self) -> tuple[torch.Tensor, dict]:
        self._reset_worlds(list(range(self._world_count)))
        self.episode_length_buf[:] = 0
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
        """Run an opt-in chain step while preserving default :meth:`step` behavior (no auto-reset)."""
        if auto_reset:
            return self.step(actions)
        actions = torch.nan_to_num(actions, nan=0.0, posinf=0.0, neginf=0.0).clamp(-1.0, 1.0)
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
        actions = torch.nan_to_num(actions, nan=0.0, posinf=0.0, neginf=0.0).clamp(-1.0, 1.0)
        self._last_actions = actions
        self._apply_actions_batch(actions)
        self.episode_length_buf += 1
        self._total_env_steps += self._world_count

        rewards, dones, extras = self._compute_rewards_dones_batch()
        rewards = torch.nan_to_num(rewards, nan=-10.0, posinf=0.0, neginf=-10.0)

        done_ids = dones.nonzero(as_tuple=False).squeeze(-1)
        if len(done_ids) > 0:
            self._reset_worlds(done_ids.cpu().tolist())

        obs = self._compute_obs_batch()
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)
        return obs, rewards, dones, extras

    def close(self):
        pass
