# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""env7 whole-route env-core -- C1->C2 DAPG (Newton 1.2.1 SolverMuJoCo, UR5ex2 + Robotiq koshape).

STAGED COMPONENT 1 of 5 (env-core -> route-executor -> oracle -> OG -> trainer). This module owns the
observation/action/reward/termination MDP surface for the whole-route policy. The phase clock and the
per-step ABSOLUTE base target are owned by the route-executor (``_run_mujoco_grasp_route``, a locked-
runner monolith) -- the env-core receives them through :class:`route_env_config.RouteInterfaceV1`,
which is a STUB here (fixed nominal target) and wires to the real route-executor at the next stage.

Substrate REUSE (not a copy of ApproachCable logic): the scene (UR5e+Robotiq koshape arms + cable +
SolverMuJoCo + cable contacts), per-arm ``IKSolver``, ``broadcast``-style joint_q kinematic re-pose
driving, and the reset/settle/P0 scaffolding are reused from ``newton_skill_env_base`` /
``newton_approach_cable_mujoco_env`` (the same active-mujoco patterns). The obs [0:42] base block is
mirrored; the route-specific parts (obs [42:62], the alpha-6D residual + (b') projection, and the
G1-G6 latched reward) are new.

Obs (62D, per world) -- index map is the SSOT in :mod:`route_env_config` (``OBS_*``):
    [0:42]  base proprio (mirror of newton_approach_cable_mujoco_env [0:42]).
            [16:19] REDEFINED = lane-matched regrasp target (CC2-CH5), NOT argmin find_nearest.
    [42:48] phase one-hot(6, base-scripted phase_id)     [48]    held cable z [m]
    [49]    seated-seg distance [m] (phase-active clip)   [50]    within-phase progress [0,1]
    [51:53] next-clip xy [m]                              [53:55] per-arm contact flag (R,L) telemetry
    [55:57] per-arm IK residual [m] (R,L)                 [57]    crossing-x deviation [m]
    [58:60] axis-resolved seat ([58] z-gap [m], [59] lateral [m])
    [60:62] C1-retention ([60] z_c1 [m], [61] flank-max [m]) -- c1_retained_final live inputs (v1.5g)

Action (6D, per world): alpha-6D = 2x3D position-only residual, NON-accumulating.
    [0:3] R EE residual XYZ [m], [3:6] L EE residual XYZ [m]. Delta = per-step OFFSET added to the
    route base ABSOLUTE target (NOT integrated). (b') phase-conditional projection: dual-grip window
    (base grip-schedule ALONE) -> hard-project to the common-mode subspace ((d_R,d_L)->(m,m), m=mean)
    so the span differential is 0 by construction; non-dual-grip transit -> asymmetric per-arm
    (reaching arm full, gripping arm sigma-capped). The as-executed residual + projection mode are
    exposed in ``extras["info"]`` (CC4-CH1/NEW-C, trainer pushforward -- boolean is not sufficient).

Reward: sparse-primary G1-G6, latched-monotonic / fire-once / never-revoked / ORDERED (G_k fires only
    if G_{k-1} latched). +5 each G1-G5, +200 G6, -0.01/step, -10 terminate. G6 SUCCESS = strict_v2
    full mirror: c2_seated_honest (groove+settle, NOT raw d<3mm) sustained K_ROUTE_SEAT and
    c1_retained_final (z_c1<0.840 and flank<0.840 [m], obs [60]/[61]) and not dropped and span-guard.

Termination: horizon 900 + explosion (physics-fault invalid, PPO-mask flag) + drop (-10). span-violation
    and reach-fail are INFORMATIVE-ONLY (never terminate). ``time_outs`` = timeout(900) ONLY
    (prohibited.md value_loss-105x history; explosionandtimeout -> time_outs=False precedence).

[!] KNOWN-GAPS / VALIDATION-STATUS (records-must-match-fact; do NOT over-claim) [!]
- STAGED-COMPONENT-1 skeleton, ROUTE-VIA-STUB, CPU-SMOKE-ONLY intended. NO training / NO GPU here.
- The route is a STUB (fixed nominal target): full whole-route physics (C1/C2 groove seating, the real
  phase clock, per-step targets) connects at the route-executor stage. With the stub the G1-G6
  predicates will not all fire -- the env-core provides the predicate MACHINERY, not a live route.
- LOUD-CARRY (route-executor / trainer stages; build plan sec 2 / sec 12 CC5-3): DoD 7 handover-fidelity,
  9b online-numerator, 12 projection-accounting, 13 adversarial-numerator, the invalid-episode PPO mask
  wiring (stock RSL-RL has no mask field), the phase-conditioned sigma, and ``reset_to_phase`` state-
  bank fork are DEFERRED-BUT-TRACKED. Producer-grade seat metrics (wall/spacer split, frozen seat-body
  pin) are route-executor refinements; the env-core uses geometric cable-vs-clip proxies from cable
  body positions (raw per-clip sim distance, NEW-5) and documents the proxy at each site.
- Per-world contact obs [53:55] is a geometric PROXY (nearest-cable proximity and grip-schedule close);
  the batched per-world claw<->cable normal-force contact is a route-executor extraction (sec 7 LOUD-CARRY).

Usage:
    source ~/env_isaaclab7/bin/activate
    # SOLVER_BACKEND is forced to "mujoco" by this module (see import block below).
"""

import os
import sys
import time
from collections import deque

import newton
import numpy as np
import torch
import warp as wp
from newton.ik import IKObjectiveJointLimit, IKObjectivePosition, IKObjectiveRotation, IKSolver
from newton.solvers import SolverMuJoCo
from rsl_rl.env import VecEnv

# --- sys.path: envs/, scripts/, configs/ (same precedent the active mujoco envs use) --------------
_env_dir = os.path.dirname(os.path.abspath(__file__))
if _env_dir not in sys.path:
    sys.path.insert(0, _env_dir)
_script_dir = os.path.join(_env_dir, "..", "scripts")
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
_config_dir = os.path.join(_env_dir, "..", "configs")
if _config_dir not in sys.path:
    sys.path.insert(0, _config_dir)

# [*][*] SOLVER-BACKEND FLIP -- MUST happen BEFORE newton_skill_env_base is imported (same as the active
# mujoco envs). build_multiworld_scene + make_solver's frozen default bind SOLVER_BACKEND at base
# import; setting it here first makes both consistent (mujoco arms + SolverMuJoCo + cable contacts).
import task_config  # noqa: E402

task_config.SOLVER_BACKEND = "mujoco"

import newton_skill_env_base as _nseb  # noqa: E402
import test_newton_clip_routing as _tncr  # noqa: E402  (DEVICE override, same as the active envs)

_nseb.SOLVER_BACKEND = "mujoco"  # defensive: cover the case where base was already imported

import route_env_config as rc  # noqa: E402  (obs map + new route params + route interface contract)
from cable_orientation_utils import compute_hand_quat_for_cable  # noqa: E402
from newton_skill_env_base import (  # noqa: E402
    DT,
    EE_BODY_OFFSET,
    IK_ITERATIONS_RL,
    IK_STEP_SIZE,
    RL_SIM_DT,
    RL_SIM_SUBSTEPS,
    SIM_DT,
    build_fk_and_init,
    build_multiworld_scene,
    compute_ori_error_axis_angle,
    derive_cable_joint_q_from_tangents,
    find_nearest_cable_point,
    normalize_quat_w_positive,
    quat_rotate_vec,
    reset_dahl_friction_for_envs,
    seed_cable_joint_state,
    temporal_quat_consistency,
)
from task_config import (  # noqa: E402
    CABLE_RADIUS,
    CLIP_BASE_HEIGHT,
    CLIP_POSITIONS,
    EE_TO_PINCH_OPEN,
    EE_Z_SAFETY_UPPER,
    FINGER_OPEN_POS,
    GRIP_HALF_SPAN,
    GRIPPER_DRIVER_EFFORT_LIMIT_NM,
    GRIPPER_DRIVER_JOINT_IDX,
    GRIPPER_SERVO_TARGET_KD,
    GRIPPER_SERVO_TARGET_KE,
    JOINTS_PER_ARM,
    MAX_MOVE_STEPS,
    ROBOT_BODIES_PER_ARM,
    SETTLE_STEPS,
    SIM_SUBSTEPS,
    TABLE_HEIGHT,
    WIDE_LEFT_Y,
    WIDE_RIGHT_Y,
)

# Per-arm strides (UR5e+Robotiq collapse=True: bodies == joints == 14).
_RIGHT_ARM_BODY_OFFSET = ROBOT_BODIES_PER_ARM  # 14
_LEFT_EE_BODY = EE_BODY_OFFSET  # 5: UR5e wrist_3 (left arm)
_RIGHT_EE_BODY = _RIGHT_ARM_BODY_OFFSET + EE_BODY_OFFSET  # 19: UR5e wrist_3 (right arm)
_N_ARM_JOINTS = 2 * JOINTS_PER_ARM  # 28: both arms' joint_q span within a world (cable joints follow)
# Route-start pose gate tolerance [rad] (max-abs over the 12 arm dofs): the arm must ARRIVE at the
# recording's frame-0 pose PHYSICALLY (design sec14.2/14.3 homing transit) before the route may start.
# 0.01 rad (10 mrad) = p5 TK-3 ruling 2026-07-19 16:36 JST: 2x the measured static PD tracking error
# (1-5 mrad, P-D1 R2) -- 50 mrad would admit ~42 mm EE offset vs the 3.5 mm seat scale. PROVISIONAL
# (freeze-after-measure): reconcile with the sec14.3 epsilon_arrival when the transit chunk lands.
# Until that chunk exists the gate always raises (home is ~5.6 rad away) = fail-closed.
_ROUTE_START_POSE_TOL_RAD = 0.01

# koshape wrist-down IK rotation target (Rx(-90) xyzw) -- NOT Franka pi/8 (S5 horizontal-gripper bug).
# alpha-6D is position-only, so this rotation target is HELD (no rot residual accumulation).
KO_ROT_TARGET_XYZW = (-0.7071067811865476, 0.0, 0.0, 0.7071067811865476)
KO_BASE_HAND_DOWN_QUAT = np.array([-0.7071067811865476, 0.0, 0.0, 0.7071067811865476], dtype=np.float32)

# EE-Z action-clamp FLOOR (koshape): fingertip reaches the cable centerline at the floor.
EE_Z_FLOOR_KO = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS + EE_TO_PINCH_OPEN  # ~= 1.06992
# Lane-aware floor (G1 root-cause fix, Rs adjudication B 2026-07-10): inside the S6_GRASP void footprint
# the cable rests at TABLE level (no clip base below), so the pinch must reach the TABLE-level cable
# centerline -- the clip-base term drops. The recorded grasp-park ee z (1.06680, both arms) sits 3.12mm
# below the clip-base floor and was clipped across the whole close window (every grid cell), pushing the
# close 3mm high -> cable under the throat (comp3_g1_armq_diag root_cause_floor_clip). Lane bounds mirror
# the void builder literals (newton_skill_env_base.py:1746,1750; runtime void parity = probe leg C +
# build-time lane_void_parity_assert). This intentionally CHANGES the flag-OFF drive path too (the clip
# site has no flag branch) -- Rs-approved env-core latent-defect fix superseding the chunk-1 flag-OFF
# byte-preserve claim at this site (65b5b9dd21 + 5tai verdict COMP3_LANEFLOOR_5TAI a35cb359a0).
EE_Z_FLOOR_KO_LANE = TABLE_HEIGHT + CABLE_RADIUS + EE_TO_PINCH_OPEN  # ~= 1.06492 (pinch @ cable center)
_LANE_Y_LO, _LANE_Y_HI = WIDE_LEFT_Y - 0.016, WIDE_RIGHT_Y + 0.016  # [0.090, 0.210] void Y slot
_LANE_X_LO, _LANE_X_HI = 0.3 - 0.066, 0.3 + 0.066  # [0.234, 0.366] void X window (base table_cx=0.3)
# C1 routing-clip island (R-B, 5tai CC4-F1): C1 (0.35, 0.15) + spacer sits INSIDE the lane box and floats
# ROUTE_CLIP_FLOAT_Z above the table -- there the seated-cable centerline rides the FLOATING clip, so the
# floor is the clip-base floor RAISED by the float (~1.08992; degenerates to the table-mount clip-base
# value automatically if the float returns to 0). Island footprint per 5tai verdict R-B (C1 +-20/15mm).
_C1_ISLAND_X_LO, _C1_ISLAND_X_HI = 0.330, 0.370
_C1_ISLAND_Y_LO, _C1_ISLAND_Y_HI = 0.135, 0.165
EE_Z_FLOOR_KO_C1_ISLAND = EE_Z_FLOOR_KO + rc.ROUTE_CLIP_FLOAT_Z  # ~= 1.08992 (float-aware)


def ee_z_floor_ko(x: float, y: float) -> float:
    """Lane-aware EE-Z floor [m]: C1 island -> float-aware clip floor; void lane -> table-level cable
    centerline; else clip-base floor."""
    if _C1_ISLAND_X_LO <= x <= _C1_ISLAND_X_HI and _C1_ISLAND_Y_LO <= y <= _C1_ISLAND_Y_HI:
        return EE_Z_FLOOR_KO_C1_ISLAND
    if _LANE_X_LO <= x <= _LANE_X_HI and _LANE_Y_LO <= y <= _LANE_Y_HI:
        return EE_Z_FLOOR_KO_LANE
    return EE_Z_FLOOR_KO


def ee_z_floor_ko_pair(rx: float, ry: float, lx: float, ly: float, common_mode: bool) -> tuple:
    """Per-arm floors for one world's (R, L) targets. R-A (5tai CC3-M2): in common-mode (dual, the b'
    projection asserts the z-span invariant) BOTH arms clip at the SHARED max floor, so a lane-edge
    excursion lifts both arms together (span-preserving, conservative); transit keeps per-arm floors.
    Replay-neutral: the replay's below-old-floor frames are in-lane on BOTH arms in every cell
    (comp3_lane_floor_sweep artifact)."""
    fr, fl = ee_z_floor_ko(rx, ry), ee_z_floor_ko(lx, ly)
    if common_mode:
        fr = fl = max(fr, fl)
    return fr, fl


_AC_IK_ITERATIONS_P0 = 400  # P0 dual-arm solve needs the generous local count (88mm span convergence).

# C1 / C2 clip context (C1C2 whole-route scope).
_C1_XY = np.array([CLIP_POSITIONS[0][0], CLIP_POSITIONS[0][1]], dtype=np.float32)  # (0.35, +0.150)
_C2_XY = np.array([rc.ROUTE_C2_XY[0], rc.ROUTE_C2_XY[1]], dtype=np.float32)  # route-scope C2 = rc.ROUTE_C2_XY
_GHS = float(GRIP_HALF_SPAN)  # 0.044: R lane = c2y + GHS (recount p9_recount_strict_v2.py:47)


def clamp_pos_ko(ee_pos, ee_quat_xyzw):
    """DC2: koshape OPEN fingertip/clamp point (wrist_3 local +Y == world -Z at the Rx(-90) pose).

    Local koshape helper (per blast-radius; the shared ``compute_clamp_pos`` stays Franka-faithful).
    """
    offset_local = np.array([0.0, +EE_TO_PINCH_OPEN, 0.0], dtype=np.float32)
    return ee_pos + quat_rotate_vec(ee_quat_xyzw, offset_local)


class NominalRouteStub(rc.RouteInterfaceV1):
    """STUB route-executor (env-core skeleton smoke). Returns a FIXED nominal target + a deterministic
    placeholder phase clock so the env machinery is exercisable. The real per-step targets and phase
    clock connect at the route-executor stage; this class only satisfies the v1 contract.

    ``is_dual_grip_window`` is single-sourced HERE (CC5-2): the env must NOT re-derive a phase->window
    table. A ``recorded_replay`` mode replays externally-supplied per-step targets for the whole-route
    DoDs (3/6/10/9a/13); with no recording it degrades to the nominal schedule.
    """

    def __init__(self, target_r, target_l, horizon, mode=rc.ROUTE_MODE_NOMINAL, recorded_targets=None):
        self._nominal_6d = np.concatenate([np.asarray(target_r, np.float32), np.asarray(target_l, np.float32)])
        self._horizon = int(horizon)
        self._mode = mode
        self._recorded = np.asarray(recorded_targets, np.float32) if recorded_targets is not None else None
        self._requested_phase = 0

    def reset_to_phase(self, k, world_ids=None):
        # STUB: record only (v2 world_ids accepted for interface compat; no per-world state to fork).
        self._requested_phase = int(k)

    def _phase_at(self, t):
        # Placeholder 6-phase clock (equal split of the horizon). Route-executor owns the real clock.
        frac = min(max(t / max(self._horizon, 1), 0.0), 0.999999)
        phase_id = int(frac * rc.N_ROUTE_PHASES)
        within = (frac * rc.N_ROUTE_PHASES) - phase_id
        return phase_id, float(within)

    def _dual_and_grip(self, phase_id, within):
        # Single-source (b') gate. Dual for G1-G3 (0,1,2) and G4(post re-cage)-G6 (4,5); the G4 regrasp
        # transit (phase 3) is single-grip until the re-cage latches at within>=0.5 (CC3-CH2). Grip: R
        # re-grasps (reaching=open) while L holds (gripping=close) during the transit; else both close.
        if phase_id == 3 and within < 0.5:
            return False, (0.0, 1.0)  # transit: R open (reaching), L close (gripping)
        return True, (1.0, 1.0)  # dual-grip: both close

    def step_target(self, t):
        if self._mode == rc.ROUTE_MODE_RECORDED_REPLAY and self._recorded is not None:
            idx = min(int(t), len(self._recorded) - 1)
            target_6d = self._recorded[idx].astype(np.float32)
        else:
            target_6d = self._nominal_6d.copy()
        phase_id, within = self._phase_at(t)
        is_dual, grip_2 = self._dual_and_grip(phase_id, within)
        return target_6d, phase_id, np.array(grip_2, dtype=np.float32), bool(is_dual)


def servo_readback_assert(model, mj_model, all_driver_dofs, negative_dofs):
    """comp3 (R8): DISCRIMINATING servo readback on the built model -- fails loud on an UNWIRED build.

    Replaces the vacuous OPEN-seed assert as the discriminating leg (K6: OPEN_RAD == 0.0 == zero-init, so a
    seed assert passes on unwired builds). Three legs:

    (1) Newton-model driver leg: every driver DOF carries ``joint_target_mode == POSITION`` +
        ``joint_target_ke/kd/effort_limit`` == the task_config servo SSOT (66.7/2.0/2.5).
    (2) NEGATIVE CONTROL: every ``negative_dofs`` entry (non-driver: arm / 4-bar follower) carries NO servo
        ke -- ``not (mode == POSITION and ke == KE)``. A blanket-wired build fails here.
    (3) mj_model leg (authoritative per R3, CPU substrate): the actuators with ``gainprm[0] == KE`` number
        exactly 4 (the single-world template's [6,10,20,24] drivers), each carries the POSITION convention
        ``biasprm[1] == -KE, biasprm[2] == -KD``, and each TARGET JOINT carries the effort cap as
        ``jnt_actfrcrange == (-EFF, +EFF)`` (solver_mujoco.py maps ``joint_effort_limit`` to the JOINT-level
        ``actfrcrange`` for hinge dofs -- NOT the actuator ``forcerange``, which the hinge branch never
        sets). A flag-OFF build has 0 such actuators -> raises.

    Args:
        model: The built Newton model (``joint_target_mode/ke/kd``, ``joint_effort_limit`` read).
        mj_model: The solver's single-world-template MuJoCo host model (``nu``, ``actuator_*`` read).
        all_driver_dofs: Flat per-world driver DOF indices (``build_perworld_index_maps``).
        negative_dofs: Non-driver DOF indices for the negative control, iterable of int.

    Raises:
        AssertionError: On any unwired / mis-wired driver, a servo-carrying non-driver, or a wrong
            mj actuator population.
    """
    jtm = model.joint_target_mode.numpy()
    ke = model.joint_target_ke.numpy()
    kd = model.joint_target_kd.numpy()
    eff = model.joint_effort_limit.numpy()
    pos_mode = int(newton.JointTargetMode.POSITION)
    tol = 1e-3
    for d in all_driver_dofs:
        assert int(jtm[d]) == pos_mode, f"servo-readback: driver dof {d} mode={jtm[d]} != POSITION ({pos_mode})"
        assert abs(float(ke[d]) - GRIPPER_SERVO_TARGET_KE) < tol, f"driver dof {d} ke={ke[d]}"
        assert abs(float(kd[d]) - GRIPPER_SERVO_TARGET_KD) < tol, f"driver dof {d} kd={kd[d]}"
        assert abs(float(eff[d]) - GRIPPER_DRIVER_EFFORT_LIMIT_NM) < tol, f"driver dof {d} effort={eff[d]}"
    for d in negative_dofs:
        carries_servo = int(jtm[d]) == pos_mode and abs(float(ke[d]) - GRIPPER_SERVO_TARGET_KE) < tol
        assert not carries_servo, f"servo-readback NEGATIVE CONTROL: non-driver dof {d} carries the servo ke"
    gain = np.asarray(mj_model.actuator_gainprm)
    bias = np.asarray(mj_model.actuator_biasprm)
    trnid = np.asarray(mj_model.actuator_trnid)
    jfrange = np.asarray(mj_model.jnt_actfrcrange)
    servo_acts = [a for a in range(int(mj_model.nu)) if abs(float(gain[a, 0]) - GRIPPER_SERVO_TARGET_KE) < tol]
    assert len(servo_acts) == 4, (
        f"servo-readback: mj_model servo actuators (gainprm[0]=={GRIPPER_SERVO_TARGET_KE}) = {len(servo_acts)} != 4 "
        f"(template drivers [6,10,20,24]; nu={int(mj_model.nu)}) -- unwired or mis-replicated build"
    )
    for a in servo_acts:
        assert abs(float(bias[a, 1]) + GRIPPER_SERVO_TARGET_KE) < tol, f"mj actuator {a} biasprm[1]={bias[a, 1]}"
        assert abs(float(bias[a, 2]) + GRIPPER_SERVO_TARGET_KD) < tol, f"mj actuator {a} biasprm[2]={bias[a, 2]}"
        j = int(trnid[a, 0])  # target joint: the effort cap lives at the JOINT level (jnt_actfrcrange)
        assert abs(float(jfrange[j, 0]) + GRIPPER_DRIVER_EFFORT_LIMIT_NM) < tol, (
            f"mj actuator {a} target joint {j} jnt_actfrcrange lo={jfrange[j, 0]}"
        )
        assert abs(float(jfrange[j, 1]) - GRIPPER_DRIVER_EFFORT_LIMIT_NM) < tol, (
            f"mj actuator {a} target joint {j} jnt_actfrcrange hi={jfrange[j, 1]}"
        )


def lane_void_parity_assert(mj_model):
    """R-C (5tai CC2-INFO2/CC6-cond2): flag-ON build-time parity of the lane-floor bounds vs the AS-BUILT
    table void (leg-C style readback). The lane constants mirror the void builder literals; a future void
    change without a floor update would silently mis-place the floor -- this fails the BUILD loud instead.

    Identifies the 4 static table boxes (bodyid 0, hz==table_half[2]==0.005, z-center==TABLE_HEIGHT-0.005),
    derives the as-built void slot from their edges (Y solids: full-X boxes; X fills: the rest), and
    asserts it equals the lane box within 1e-6 (float32 geometry tolerance, probe leg C).
    """
    tol = 1e-6
    boxes = []
    for g in range(int(mj_model.ngeom)):
        if int(mj_model.geom_bodyid[g]) == 0 and abs(float(mj_model.geom_size[g][2]) - 0.005) < tol:
            if abs(float(mj_model.geom_pos[g][2]) - (TABLE_HEIGHT - 0.005)) < tol:
                boxes.append(
                    (
                        float(mj_model.geom_size[g][0]),
                        float(mj_model.geom_size[g][1]),
                        float(mj_model.geom_pos[g][0]),
                        float(mj_model.geom_pos[g][1]),
                    )
                )
    assert len(boxes) == 4, f"lane-void parity: table boxes = {len(boxes)} (exp 4 flag-ON void)"
    y_solids = sorted([b for b in boxes if b[0] > 0.3], key=lambda b: b[3])  # full-X halves (0.35)
    x_fills = sorted([b for b in boxes if b[0] <= 0.3], key=lambda b: b[2])
    assert len(y_solids) == 2 and len(x_fills) == 2, f"lane-void parity: box split {len(y_solids)}/{len(x_fills)}"
    built_y_lo = y_solids[0][3] + y_solids[0][1]  # -Y solid top edge
    built_y_hi = y_solids[1][3] - y_solids[1][1]  # +Y solid bottom edge
    built_x_lo = x_fills[0][2] + x_fills[0][0]  # -X fill right edge
    built_x_hi = x_fills[1][2] - x_fills[1][0]  # +X fill left edge
    for name, built, lane in (
        ("y_lo", built_y_lo, _LANE_Y_LO),
        ("y_hi", built_y_hi, _LANE_Y_HI),
        ("x_lo", built_x_lo, _LANE_X_LO),
        ("x_hi", built_x_hi, _LANE_X_HI),
    ):
        assert abs(built - lane) < tol, f"lane-void parity: {name} as-built {built:.6f} != lane {lane:.6f}"


def physics_finger_obs(phys_jq, arm_q_start_w):
    """comp3 (R6): flag-ON obs[7]/[15] source = PHYSICS joint_q driver readback for one world.

    The FK-side sum (``fk_jq[...]``, flag-OFF source) pins the fingers OPEN, so it would LIE under the live
    servo (K7). Same formula (sum of the two driver angles per arm), sourced from the physics ``joint_q``
    at this world's driver coords (q-local == qd-local within the arm span; the cable FREE root only shifts
    the per-world base offset).

    Args:
        phys_jq: The full physics ``joint_q`` host array [rad].
        arm_q_start_w: This world's arm ``joint_q`` start index.

    Returns:
        ``(r_finger, l_finger)`` driver-angle sums [rad], floats.
    """
    rd0, rd1 = JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0], JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]
    r_finger = float(phys_jq[arm_q_start_w + rd0]) + float(phys_jq[arm_q_start_w + rd1])
    l_finger = float(phys_jq[arm_q_start_w + GRIPPER_DRIVER_JOINT_IDX[0]]) + float(
        phys_jq[arm_q_start_w + GRIPPER_DRIVER_JOINT_IDX[1]]
    )
    return r_finger, l_finger


class NewtonRouteEnv(VecEnv):
    """RSL-RL VecEnv: whole-route (C1->C2) env-core on the env7 mujoco-ko substrate (UR5ex2 + koshape).

    N physical worlds -> N RL environments (one dual-arm agent per world, 6D position-only residual).
    Arms are kinematically re-posed via IK -> joint_q (SC2b, the Newton mujoco substrate norm); the
    cable + contacts are the dynamic part. Newton steps all worlds at once.
    """

    # --- Action: alpha-6D residual (position-only, NON-accumulating) ----------------------------------
    POS_RESIDUAL_SCALE = 0.015  # [m] 15mm per-step residual (raw action in [-1,1] scaled to meters)
    DELTA_BOUND_M = 0.020  # [m] env-core Delta-bound clamp per arm (CC3-CH1). TODO: derive from P3 corner-miss.
    GRIPPING_ARM_SIGMA_CAP_M = 0.002  # [m] transit gripping-arm residual cap (drop-prevention; artifacts sigma<=~2mm)
    PHYSICS_STEPS_PER_RL = 10

    # --- Termination / drop / guard thresholds -------------------------------------------------------
    MAX_EPISODE_STEPS = rc.ROUTE_TERMINAL_STEPS  # 900
    EXPLOSION_DIST_THRESH = 1.0  # [m] EE<->cable divergence -> physics-fault invalid episode
    LIFT_RISE_MIN_M = 0.040  # [m] G2: held_cable_z - z_rest(P0) >= +40mm (artifacts G2)
    DROP_LIFT_MARGIN_M = 0.010  # [m] held cable within this of rest during a held phase -> dropped
    DROP_CONTACT_LOSS_DEBOUNCE = 8  # sustained gripping-arm contact-loss steps -> dropped (CC3-CH3 debounce)
    DROP_LATERAL_DEV_MAX_M = 0.060  # [m] crossing-x lateral escape -> lateral-escape-drape drop
    CONTACT_PROXIMITY_M = 0.012  # [m] geometric contact-flag proxy (nearest-cable < this and grip-close)
    REGRASP_REACH_TOL_M = 0.020  # [m] G4 _at_88 proxy (runner _reach_R_mm <= 20mm)

    # --- IK / init ----------------------------------------------------------------------------------
    INIT_XY_NOISE = 0.005  # +/-5mm initial EE target randomization (tracked target only on mujoco)

    def __init__(self, world_count=1, device="cuda:0", cfg=None):
        # fork-B R5-1 flip (D1 spec sec 4, Rs-adopted fork B): the default is the WORKING config -- under
        # USE_MUJOCO_CPU=True only the single-world template integrates, so a bare 4-world build would run
        # three silently frozen worlds (COMP3:79; ENV_MULTIWORLD_SUBSTRATE_CHARTER). Every live caller passes
        # world_count=1 explicitly (grep-verified, D0 materials item 5), so this changes no existing behavior;
        # intentional multi-world diagnostics opt out via THREAD_ALLOW_CPU_MULTIWORLD=1 at the make_solver
        # tripwire.
        self.num_envs = world_count
        self.num_actions = 6  # alpha-6D = 2x3D position-only residual
        self._total_env_steps = 0
        self.max_episode_length = self.MAX_EPISODE_STEPS
        self.device = device
        self.cfg = cfg or {}
        # comp3 (Stage-B): grasp_actuation flag. Default OFF = env-core byte-preserve (solid table, gripper
        # kinematically pinned OPEN). ON = build the DYNAMIC POSITION-servo gripper + table VOID and let the
        # recorded grip_cmd schedule close it. Bool-type asserted (K5/R8: cfg.get truthiness hazard). ON
        # REQUIRES the RouteExecutor route (the grip-cmd writer) -- else the servo is built with no schedule
        # = silent inert grip; fail loud (K5).
        _ga = self.cfg.get("grasp_actuation", False)
        assert isinstance(_ga, bool), f"cfg['grasp_actuation'] must be a bool, got {type(_ga).__name__}"
        self._grasp_actuation = _ga
        # (d) P-D1 probe flags (design v1.2 sec5): ARM ctrl-drive switch for the per-step drive ONLY
        # (reset/settle B-sites stay kinematic in the probe). Default OFF -> byte-identical.
        # ARM_XML_ACT_NEUTRALIZE alone = L-P0 mode (imported-actuator neutralization, kinematic drive).
        self._arm_pd_drive = os.environ.get("ARM_PD_DRIVE") == "1"
        self._arm_xml_act_neutralize = self._arm_pd_drive or os.environ.get("ARM_XML_ACT_NEUTRALIZE") == "1"
        self._arm_pd_ramp_frames = int(os.environ.get("ARM_PD_RAMP_FRAMES", "0") or "0")
        self._arm_pd_ramp_k = None  # M-5 ramp frame counter; None = not yet activated
        self._arm_pd_ramp_q0 = None  # M-4 sync snapshot: activation-time realized arm q
        self._armpd_repose_count = 0  # v1.3 #3 route-start re-pose counter (probe npz/summary flag)
        if self._grasp_actuation and self.cfg.get("route_executor_impl", "stub") != "route_executor":
            raise ValueError(
                "grasp_actuation=True requires cfg['route_executor_impl']=='route_executor' "
                "(the recorded grip_cmd schedule drives the servo; a stub route leaves the servo inert)"
            )
        # comp3 G1 prework (Rs adjudication A, 2026-07-10): align the flag-ON scene to the RECORDING's scene so the
        # replayed grip schedule meets the cable where the recording put it (G-F1): (a) NO support clips
        # (the recording scene has none -> table-resting, not clip-suspended) + (b) cable start Y shifted to
        # the recording's cable_y_start (base hardwires CLIP1_Y - half; the recording used -0.30). Default
        # False = current behavior byte-preserve. G1-scene concept -> requires grasp_actuation.
        _al = self.cfg.get("g1_scene_align", False)
        assert isinstance(_al, bool), f"cfg['g1_scene_align'] must be a bool, got {type(_al).__name__}"
        self._g1_scene_align = _al
        if self._g1_scene_align and not self._grasp_actuation:
            raise ValueError("g1_scene_align=True requires grasp_actuation=True (it is a G1 flag-ON scene config)")
        # comp5 (route-executor): route_c2_scene wires the real C2 V-groove into the MW env-core scene for
        # DoD6 C2-seating video + MW route seating (env-core-build-ONLY; NOT the single-world 5/9b path).
        # Default False = byte-identical (build_multiworld_scene add_c2_clip omitted).
        _rc2 = self.cfg.get("route_c2_scene", False)
        assert isinstance(_rc2, bool), f"cfg['route_c2_scene'] must be a bool, got {type(_rc2).__name__}"
        self._route_c2_scene = _rc2
        # (d2) route_c1_pin: pre-allocate + activate the C1 clip-retention pin, so the open-loop replay can be
        # re-measured on a substrate where the pin ACTUALLY holds. The producer has this mechanism and the
        # multi-world env-core did not -- so every "open-loop drops the cable" measurement to date was taken on
        # an env missing a mechanism the reference trajectory depends on. Default False = byte-identical.
        # MEASUREMENT ONLY: making the pin permanent is a premise-scope decision (INVARIANT #5) and is Rs's.
        _rc1p = self.cfg.get("route_c1_pin", False) or os.environ.get("ROUTE_C1_PIN", "0") == "1"
        assert isinstance(_rc1p, bool), f"cfg['route_c1_pin'] must be a bool, got {type(_rc1p).__name__}"
        self._route_c1_pin = bool(_rc1p)
        if self._route_c1_pin:
            raise RuntimeError(
                "clip-retention pin REMOVED from active execution (Rs directive 2026-07-19: the sec0#5 "
                "exception is superseded) -- retention must be physical clip contact (design sec14.10)"
            )
        self._c1_pin_witness = None  # persisted proof the pin fired -- a run that cannot show this proves nothing
        # (d-a) live-geometric trigger state (charter sec 8.10.1 / sec 8.2 / sec 2-D; prereg PIN_D_TRIGGER v0.6).
        self._c1_pin_dwell = 0  # consecutive (capture AND depth) physics frames; reset on a gap and on clear
        self._pin_mismatch_total = 0  # sec 8.2 bypass/divergence count -- LOUD only, NEVER wired to reward/term
        self._last_pin_record = self._sentinel_pin_record()  # sec 2-D per-episode snapshot; set before each clear
        # W1-B1 (Stage-A sec 4.1): route_t_clock gates the route-clock DIVERGENCE machinery only (B2 HOLD
        # freeze / B3 fork init). False (default) = route_t mirrors episode_length_buf exactly (increment/
        # reset at the same sites) -> flag-OFF behavior byte-preserved. B1 ships no divergence mechanism,
        # so ON has no behavioral effect yet (skeleton; Layer-B re-BASELINE lands with B2).
        _rtc = self.cfg.get("route_t_clock", False)
        assert isinstance(_rtc, bool), f"cfg['route_t_clock'] must be a bool, got {type(_rtc).__name__}"
        self._route_t_clock = _rtc
        # W1-B2 (conformance R5g, keyed on IMPL TYPE not recording presence -- a stub with recorded_targets
        # would otherwise pass a presence check and late-fail at the first flag-ON query): the HOLD
        # divergence machinery needs the RouteExecutor's recorded cable ground truth; a stub run under the
        # flag would silently never HOLD (fail-OPEN).
        if self._route_t_clock and self.cfg.get("route_executor_impl", "stub") != "route_executor":
            raise ValueError(
                "route_t_clock=True requires cfg['route_executor_impl']=='route_executor' "
                "(HOLD needs the recorded cable_xyz/held_seg_l ground truth; stub = silent no-HOLD)"
            )
        # D rho=0 (Rs adjudication (1) 2026-07-10): route drive mode. 'ik_chord' (default) = the current
        # step-level batched IK + 10-frame joint chord (byte-preserve); 'feedforward' = the recording's
        # arm_q replayed per physics frame (the armqdirect-proven mechanism promoted to a drive mode;
        # SCRIPTED-VERIFICATION-STAGE only -- the trainer-stage D-b window design is a SEPARATE gate).
        # feedforward REQUIRES the live-grip stack (K5 pattern): the servo grip schedule is the only
        # gripper writer in this mode, and the recording supplies the arm path (arm_q asserted at first use).
        _dm = self.cfg.get("route_drive_mode", "ik_chord")
        assert _dm in ("ik_chord", "feedforward"), (
            f"cfg['route_drive_mode'] must be 'ik_chord' | 'feedforward', got {_dm!r}"
        )
        self._route_drive_ff = _dm == "feedforward"
        if self._route_drive_ff:
            if not self._grasp_actuation:
                raise ValueError(
                    "route_drive_mode='feedforward' requires grasp_actuation=True (live-grip scripted stage)"
                )
            if self.cfg.get("route_executor_impl", "stub") != "route_executor":
                raise ValueError(
                    "route_drive_mode='feedforward' requires cfg['route_executor_impl']=='route_executor' "
                    "(the RouteExecutor owns the recorded arm_q feedforward writer)"
                )
            if not self.cfg.get("route_recording_npz"):
                raise ValueError("route_drive_mode='feedforward' requires cfg['route_recording_npz'] (arm_q source)")
        self._world_count = world_count

        self.episode_length_buf = torch.zeros(world_count, dtype=torch.long, device=device)
        # W1-B1 route_t (Stage-A spec v0.8.1 sec 4.1): the per-world ROUTE clock, separated from the episode
        # clock above. Single-source rule: ALL route consumers (step_target / grip staircase / ff replay /
        # obs[50] phase-entry) read route_t, NEVER episode_length_buf. Under route_t_clock=False (default)
        # route_t is incremented/zeroed at the SAME sites as episode_length_buf (mirror -> value-identical
        # -> downstream byte-invariant); the flag only arms the divergence machinery (B2 HOLD freeze /
        # B3 bank-fork init), none of which exists in B1.
        self.route_t = torch.zeros(world_count, dtype=torch.long, device=device)
        self._target_seg_indices_r = None
        self._target_seg_indices_l = None
        self._episode_count = 0
        self._episode_success_buf = deque(maxlen=200)
        self._last_success_rate = 0.0

        # Per-world EE targets (tracked for IK warm-start / P0; the RESIDUAL contract is non-accumulating).
        self._ee_target_right = np.zeros((world_count, 3), dtype=np.float32)
        self._ee_target_left = np.zeros((world_count, 3), dtype=np.float32)

        # Temporal quat consistency (avoid w~=0 sign flip in obs quats).
        _id4 = np.array([0, 0, 0, 1], dtype=np.float32)
        self._prev_clamp_r_quat = np.tile(_id4, (world_count, 1))
        self._prev_clamp_l_quat = np.tile(_id4, (world_count, 1))
        self._prev_seg_r_quat = np.tile(_id4, (world_count, 1))
        self._prev_seg_l_quat = np.tile(_id4, (world_count, 1))

        # --- Reward latch state (G1-G6: latched-monotonic, fire-once, never-revoked, ORDERED) ---
        self._g_latched = np.zeros((world_count, 6), dtype=bool)
        self._g6_sustain = np.zeros(world_count, dtype=np.int32)  # c2 groove+settle sustain counter (K_ROUTE_SEAT)
        self._contact_loss_count = np.zeros(world_count, dtype=np.int32)  # gripping-arm contact-loss debounce

        # --- (b') action-path telemetry (exposed in extras["info"] for trainer pushforward, NEW-C) ---
        self._last_executed_residual = np.zeros((world_count, 6), dtype=np.float32)  # as-executed a' (post-projection)
        self._last_projection_mode = np.zeros(world_count, dtype=np.int32)  # 0=common-mode (dual), 1=transit-asym
        self._last_ik_resid = np.zeros((world_count, 2), dtype=np.float32)  # (R, L) IK residual [m] -> obs [55:57]
        self._route_phase_id = np.zeros(world_count, dtype=np.int32)  # base-scripted phase_id (route stub)
        self._route_within = np.zeros(world_count, dtype=np.float32)
        self._route_grip = np.zeros((world_count, 2), dtype=np.float32)  # (R, L) scripted grip (0=open,1=close)
        self._route_is_dual = np.ones(world_count, dtype=bool)
        self._phase_entry_step = np.zeros(world_count, dtype=np.int64)  # for env-side within-phase progress
        self._prev_phase_id = np.full(world_count, -1, dtype=np.int32)
        # --- W1-B2 HOLD wiring (flag-gated; inert numpy state under route_t_clock=False) ---
        self._hold_mask_np = np.zeros(world_count, dtype=bool)  # frozen set as of the LAST sync update
        self._suppressed_drop_count = np.zeros(world_count, dtype=np.int64)  # tail (iv) events (B5 export)
        self._route_release_step = None  # recording-derived scheduled-release boundary (set with the executor)

        os.environ["NEWTON_DEVICE"] = device
        _tncr.DEVICE = device

        print(f"[NewtonRouteEnv] Initializing: {world_count} worlds on {device} (backend=mujoco)")
        t0 = time.perf_counter()

        self._build_model()
        if self._g1_scene_align:
            # comp3 G1 prework (Rs adjudication A): re-seed the built (straight) cable to the recording's start Y
            # BEFORE settling, so the settle converges to the recording's table-resting pre-grasp state.
            self._align_cable_to_recording_start()
        self._settle_cable()
        self._setup_p0_precondition()
        self._save_precondition_state()
        self._init_batched_ik_solver()

        # Route interface: STUB by default (env-core byte-preserve) or the real RouteExecutor when the
        # cfg flag selects it (comp2 env-wiring). is_dual_grip_window is single-sourced by whichever
        # implementation is active (CC5-2). flag-OFF keeps the env-core 25/81 byte-identity (gate-iii);
        # flag-ON replays the recorded_replay route + supplies the phase-k state-bank for reset_to_phase.
        if self.cfg.get("route_executor_impl", "stub") == "route_executor":
            self._route = self._build_route_executor()
            # W1-B2 sec 9 tail (iv): scheduled-release boundary, recording-derived (never hardcoded;
            # None = the recording has no scheduled release -> suppression inert).
            _rls = self._route._recording["release_step"]
            self._route_release_step = int(_rls) if _rls is not None else None
            self._wire_c1_pin_from_recording()  # C1 identity always; (d2) onset only when pin is enabled
        else:
            self._route = NominalRouteStub(self._settled_ee_r_pos, self._settled_ee_l_pos, self.MAX_EPISODE_STEPS)

        # M-E guard: SolverMuJoCo backend assert (VBD-residue regression guard).
        assert isinstance(self._solver, SolverMuJoCo), (
            f"route env-core requires SolverMuJoCo (mujoco-ko substrate); got {type(self._solver).__name__}"
        )
        print(
            f"[NewtonRouteEnv] Ready in {time.perf_counter() - t0:.1f}s. "
            f"obs={self.num_obs}, act={self.num_actions}, worlds={world_count}"
        )

    def _build_route_executor(self):
        """Construct the real RouteExecutor from a recorded_replay npz (comp2 env-wiring; flag-ON path).

        Loaded ONLY when ``cfg["route_executor_impl"] == "route_executor"`` so the default (stub) path keeps
        the env-core byte-identity (gate-iii). The ONE-cell recording drives ``step_target`` (recorded_replay)
        AND seeds the phase-k state-bank for ``reset_to_phase`` (built from the recorded phase-boundary
        arm_q/grip; qvel=0 is data-forced -- see :func:`route_executor.build_state_bank_from_recording`).
        Requires ``cfg["route_recording_npz"]`` (a ``route_demo_raw.npz`` from the canonical 81-grid).

        Note (Stage-A scope): the flag-ON env is not rolled out in Stage-A (the env-core reset calls
        ``reset_to_phase(0)`` = no-op, and gate-iii runs flag-OFF); a live flag-ON run + the cable-fork
        re-seed for ``reset_to_phase(k>=1)`` (build plan sec 8 (B)) belong to the Stage-B / trainer stage.
        """
        # thread_isaac_lab/ (parent of configs) on the path so route_executor's `from configs.task_config` resolves.
        _til = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if _til not in sys.path:
            sys.path.insert(0, _til)
        import route_executor as rex

        # P-F3 (fold 5): the grip staircase lookup cf[t]+sub_i is 1:1 with the drive loop ONLY if the
        # recording cadence equals the env's physics-frames-per-RL-step -- cross-assert the two SSOTs.
        assert rex._REC_CADENCE == self.PHYSICS_STEPS_PER_RL, (
            f"cadence mismatch: route_executor._REC_CADENCE={rex._REC_CADENCE} != "
            f"PHYSICS_STEPS_PER_RL={self.PHYSICS_STEPS_PER_RL} (grip frame lookup would de-sync)"
        )
        npz_path = self.cfg.get("route_recording_npz")
        if not npz_path:
            raise ValueError(
                "route_executor_impl='route_executor' requires cfg['route_recording_npz'] "
                "(a canonical route_demo_raw.npz)"
            )
        if self._grasp_actuation:
            # G-F2 (fold 7): the replayed grip staircase timing is NOMINAL-cell-specific; a non-nominal
            # recording would close on a cable the schedule never saw. Pin the provenance (sha256) to the
            # banked nominal golden until DoD-7 cell-geometry compatibility lands.
            import hashlib

            with open(npz_path, "rb") as _fh:
                got = hashlib.sha256(_fh.read()).hexdigest()
            assert got == rex.RUN1_REFERENCE_V2_SHA256, (
                f"grasp_actuation=True requires the NOMINAL golden recording (RUN1_REFERENCE_V2): "
                f"sha256({npz_path})={got} != {rex.RUN1_REFERENCE_V2_SHA256}"
            )
        z = np.load(npz_path, allow_pickle=True)
        recording = {
            "ee_pos_r": z["ee_pos_r"],
            "ee_pos_l": z["ee_pos_l"],
            "grip_cmd": z["grip_cmd"],
            "phase_id": z["phase_id"],
            "arm_q": z["arm_q"],  # full physics joint_q/frame (arm[0:28] + cable[28:74]); the state_bank source
            # W1-B2 recording contract v2 (spec sec 4.2 N9): the div_grip ground truth, now REQUIRED keys.
            "cable_xyz": z["cable_xyz"],
            "held_seg_l": z["held_seg_l"],
        }
        # Optional canonical pin witness. RouteExecutor preparation must preserve this all-or-none triple;
        # it supplies both the C1 routed-segment identity (reward FM4) and the recorded pin onset. The old
        # prepared recording dropped these fields, so route_c1_pin crashed before the authorizer could run.
        _pin_keys = ("pin_active", "pin_eqid", "pinned_body")
        if any(key in z for key in _pin_keys):
            missing_pin = [key for key in _pin_keys if key not in z]
            if missing_pin:
                raise ValueError(f"route recording has a partial pin witness; missing {missing_pin}")
            recording.update({key: z[key] for key in _pin_keys})
        state_bank = rex.build_state_bank_from_recording(recording, self._world_count, arm_off=0)
        print(
            f"[NewtonRouteEnv] route_executor ON: recording={npz_path} "
            f"(frames={recording['arm_q'].shape[0]}, state_bank phases={sorted(state_bank)})"
        )
        return rex.RouteExecutor(
            self._arm_q_start,
            self._arm_qd_start,
            self.MAX_EPISODE_STEPS,
            state_0=self._state_0,
            control=self._control,
            state_bank=state_bank,
            recording=recording,
            forbid_banked_fork=self._grasp_actuation,  # comp3 (R1): k>=1 banked fork needs DoD-7(b) (comp3b)
        )

    # =====================================================================================================
    # Model construction / physics (reuse the mujoco base scene + joint_q re-pose driving)
    # =====================================================================================================

    def _build_model(self):
        """Build FK model + reuse the mujoco multi-world scene (UR5e+Robotiq koshape + cable + contacts).

        Reuse of the base pattern (build plan sec 1 'AC/AR base 2109 pattern'): support clips + C1 target
        groove present. The full multi-clip (C2 groove) route scene connects at the route-executor stage;
        env-core seat predicates read geometric cable-vs-clip distance from cable body positions.
        """
        print("[NewtonRouteEnv] Building FK model...")
        self._fk_model, self._fk_state, fk_jq = build_fk_and_init(
            left_finger_pos=FINGER_OPEN_POS, right_finger_pos=FINGER_OPEN_POS, device=self.device
        )
        self._per_world_fk_jq = np.tile(fk_jq, (self._world_count, 1))

        if self._route_c2_scene:
            # comp5 H3: build<->replay c2y guard. The MW C2 is built at rc.ROUTE_C2_XY[1]; a replayed recording
            # MUST match (else the cable seats vs a phantom-Y C2). Assert vs the recording sidecar meta
            # env_gates.CLIP2_Y (route_demo_raw.npz -> route_demo_raw_meta.json). Fail-loud.
            _npz_c2 = self.cfg.get("route_recording_npz")
            _meta_c2 = str(_npz_c2).replace("route_demo_raw.npz", "route_demo_raw_meta.json") if _npz_c2 else ""
            if _meta_c2 and os.path.exists(_meta_c2):
                import json as _json_c2

                with open(_meta_c2) as _fh_c2:
                    _gates_c2 = _json_c2.load(_fh_c2).get("env_gates", {})
                _rec_c2y = float(_gates_c2.get("CLIP2_Y", rc.ROUTE_C2_XY[1]))
                assert abs(_rec_c2y - float(rc.ROUTE_C2_XY[1])) < 1e-6, (
                    f"comp5 C2 build<->replay c2y mismatch: recording CLIP2_Y={_rec_c2y} != "
                    f"ROUTE_C2_XY[1]={rc.ROUTE_C2_XY[1]}"
                )
        print(f"[NewtonRouteEnv] Building scene ({self._world_count} worlds, backend=mujoco)...")
        scene = build_multiworld_scene(
            self._fk_model,
            self._fk_state,
            self._world_count,
            self.device,
            add_support_clips=not self._g1_scene_align,  # G1 align (Rs adj. A): recording scene has NO clips
            add_target_clip=True,  # C1 V-groove present (routing/seating scenario, cf Grip clamp mode)
            target_clip_float_z=rc.ROUTE_CLIP_FLOAT_Z,  # C1 clip float +20mm (route env-gate; %12 build+predicate flag)
            grasp_actuation=self._grasp_actuation,  # comp3: OFF (default)=byte-id solid table; ON=VOID+servo
            add_c2_clip=self._route_c2_scene,  # comp5: real C2 V-groove (MW env-core route seating + DoD6 video)
            c2_xy=rc.ROUTE_C2_XY,  # param-idiom single-source (0.000); NO os.environ CLIP2_Y
            perclip_pin=self._route_c1_pin,  # (d2): pre-allocate the C1 clip-retention pin (measurement only)
        )
        self._model = scene["model"]
        self._solver = scene["solver"]
        self._state_0 = scene["state_0"]
        self._state_1 = scene["state_1"]
        self._control = scene["control"]
        self._contacts = scene["contacts"]
        self._bws = scene["bws"]
        self._jws = scene["jws"]
        self._cable_bodies = scene["cable_bodies"]
        self._cable_bodies_per_world = scene["cable_bodies_per_world"]

        # sec 23: derive the authoritative per-world ARM coord starts (q and qd separately) -- the cable FREE
        # root adds 6 extra coords/world, so a joint-index slice is wrong for world>=1.
        _jqs = self._model.joint_q_start.numpy()
        _jqds = self._model.joint_qd_start.numpy()
        _jws_joint = self._model.joint_world_start.numpy()
        self._arm_q_start = [int(_jqs[_jws_joint[w]]) for w in range(self._world_count)]
        self._arm_qd_start = [int(_jqds[_jws_joint[w]]) for w in range(self._world_count)]
        # comp3 (flag-ON only): env-owned per-world arm-only write index maps (single-source with
        # route_executor via build_perworld_index_maps). Built here because _broadcast_arm_jointq runs
        # BEFORE the RouteExecutor exists (K5/R8). flag-OFF builds nothing -> byte-preserve.
        self._arm_ow_maps = None
        self._rex = None  # route_executor module handle (arm-only write fns); flag-ON only
        if self._grasp_actuation:
            _til = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if _til not in sys.path:
                sys.path.insert(0, _til)
            import route_executor as _rex_maps

            self._rex = _rex_maps
            self._arm_ow_maps = _rex_maps.build_perworld_index_maps(self._arm_q_start, self._arm_qd_start)
            # comp3 (R8/K6): DISCRIMINATING servo readback on the built model (drivers POSITION + ke/kd/eff
            # SSOT + negative control + mj_model actuator population). Fails loud on an unwired build; the
            # RouteExecutor's OPEN-seed assert stays as the SECONDARY leg.
            _neg = [
                self._arm_qd_start[w] + off
                for w in range(self._world_count)
                for off in (0, GRIPPER_DRIVER_JOINT_IDX[0] + 1, JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0] + 1)
            ]  # arm j0 + one 4-bar follower per arm (non-driver gripper coords)
            servo_readback_assert(self._model, self._solver.mj_model, self._arm_ow_maps["all_driver_dofs"], _neg)
            # R-C: fail-loud lane-floor vs as-built void parity (drift guard for future void changes).
            lane_void_parity_assert(self._solver.mj_model)
            if self._arm_xml_act_neutralize:
                # (d) P-D1 L-P6 census (design v1.4-③ B1-STRIP): on the BUILT model --
                # (1) the imported ur5e.xml arm actuators are structurally ABSENT (stripped at the
                #     proto -- no inert set to verify, the B1 point): NO arm-mapped actuator exists
                #     beyond the [PD mode] 12 proto-wired servos; nu is exact (16 PD / 4 L-P0);
                # (2) [PD mode only] exactly 12 actuators carry the SCALED design servo shape;
                #     jnt_actfrcrange at the arm joints == the UNSCALED effort caps; negative control.
                import mujoco as _apd_mj

                _apd_scale = float(os.environ.get("ARM_PD_GAINS_SCALE", "1.0"))
                _apd_ke_scale = float(os.environ.get("ARM_PD_KE_SCALE", str(_apd_scale)))
                _apd_kd_scale = float(os.environ.get("ARM_PD_KD_SCALE", str(_apd_scale)))
                _apd_m = self._solver.mj_model
                _apd_gain = np.asarray(_apd_m.actuator_gainprm)
                _apd_bias = np.asarray(_apd_m.actuator_biasprm)
                _apd_trn = np.asarray(_apd_m.actuator_trnid)
                _apd_arm_acts = []
                for a in range(int(_apd_m.nu)):
                    j = int(_apd_trn[a, 0])
                    jn = _apd_mj.mj_id2name(_apd_m, _apd_mj.mjtObj.mjOBJ_JOINT, j) or ""
                    if "ur5e" in jn:
                        _apd_arm_acts.append(a)
                _apd_live = list(_apd_arm_acts)  # B1-strip: every arm-mapped actuator must be a live design servo
                _apd_nu_want = 16 if self._arm_pd_drive else 4
                assert int(_apd_m.nu) == _apd_nu_want, (
                    f"armpd-census (B1-strip): nu = {int(_apd_m.nu)} != {_apd_nu_want} "
                    f"(imported actuators not stripped, or wiring missing)"
                )
                if self._arm_pd_drive:
                    _apd_sz3 = (2000.0 * _apd_ke_scale, 400.0 * _apd_kd_scale, 150.0)
                    _apd_sz1 = (500.0 * _apd_ke_scale, 100.0 * _apd_kd_scale, 28.0)
                    assert len(_apd_live) == 12, (
                        f"armpd-census: live (synthesized) arm actuators = {len(_apd_live)} != 12"
                    )
                    _apd_jfr = np.asarray(_apd_m.jnt_actfrcrange)
                    for a in _apd_live:
                        _is3 = abs(float(_apd_gain[a, 0]) - _apd_sz3[0]) < 1e-3
                        _is1 = abs(float(_apd_gain[a, 0]) - _apd_sz1[0]) < 1e-3
                        assert _is3 or _is1, f"armpd-census: live act {a} gain0 {float(_apd_gain[a, 0])} matches neither size"
                        _eke, _ekd, _eeff = _apd_sz3 if _is3 else _apd_sz1
                        assert abs(float(_apd_bias[a, 1]) + _eke) < 1e-3, f"armpd-census: live act {a} biasprm1"
                        assert abs(float(_apd_bias[a, 2]) + _ekd) < 1e-3, f"armpd-census: live act {a} biasprm2"
                        j = int(_apd_trn[a, 0])
                        assert abs(float(_apd_jfr[j, 0]) + _eeff) < 1e-3 and abs(float(_apd_jfr[j, 1]) - _eeff) < 1e-3, (
                            f"armpd-census: live act {a} joint {j} actfrcrange {_apd_jfr[j]} != +-{_eeff} (caps UNSCALED)"
                        )
                    _apd_jtm = self._model.joint_target_mode.numpy()
                    _apd_ke = self._model.joint_target_ke.numpy()
                    _apd_pos = int(newton.JointTargetMode.POSITION)
                    for w in range(self._world_count):
                        for _apd_base in (0, JOINTS_PER_ARM):
                            for _apd_li in range(6):
                                d = self._arm_qd_start[w] + _apd_base + _apd_li
                                eke = (_apd_sz3 if _apd_li < 3 else _apd_sz1)[0]
                                assert int(_apd_jtm[d]) == _apd_pos, f"armpd-census: dof {d} mode {_apd_jtm[d]}"
                                assert abs(float(_apd_ke[d]) - eke) < 1e-3, f"armpd-census: dof {d} ke {_apd_ke[d]} != {eke}"
                        d = self._arm_qd_start[w] + GRIPPER_DRIVER_JOINT_IDX[0] + 1  # a 4-bar follower
                        _apd_neg = int(_apd_jtm[d]) == _apd_pos and (
                            abs(float(_apd_ke[d]) - _apd_sz3[0]) < 1e-3 or abs(float(_apd_ke[d]) - _apd_sz1[0]) < 1e-3
                        )
                        assert not _apd_neg, f"armpd-census NEGATIVE CONTROL: follower dof {d} carries an arm servo"
                else:
                    # L-P0 mode: neutralize-only -- NO synthesized arm servos may exist.
                    assert len(_apd_live) == 0, (
                        f"armpd-census (L-P0): expected 0 live arm actuators, got {len(_apd_live)}"
                    )
                print(
                    f"  [ARMPD] L-P6 census PASS (B1-strip): imported=ABSENT, nu={int(_apd_m.nu)}, "
                    f"live={len(_apd_live)}, mode={'PD' if self._arm_pd_drive else 'L-P0'}, "
                    f"ke_scale={_apd_ke_scale}, kd_scale={_apd_kd_scale}"
                )
        print(
            f"[NewtonRouteEnv] Model: {self._model.body_count} bodies, "
            f"{self._model.joint_count} joints, solver={type(self._solver).__name__}"
        )

    def _align_cable_to_recording_start(self):
        """comp3 G1 prework (Rs adjudication A, G-F1): shift the built cable to the RECORDING's start Y, pre-settle.

        The base builder hardwires ``cable_y_start = CLIP1_Y - half`` (-0.15) even when ``cable_start_pos``
        is passed (base is zero-drift for comp3), while the recording scene starts the cable at -0.30
        (probe leg-G measured the delta as a UNIFORM 150 mm dy). Re-seed via the SANCTIONED reset-init
        machinery (:func:`seed_cable_joint_state`, episode-init exception) with the delta DERIVED from the
        recording npz (frame-0 seg-0 y) vs the as-built root y -- no hardcoded constants. Runs BEFORE
        ``_settle_cable``; the settle then converges to the recording's table-resting pre-grasp state
        (no support clips under ``g1_scene_align``).
        """
        npz_path = self.cfg.get("route_recording_npz")
        assert npz_path, "g1_scene_align requires cfg['route_recording_npz'] (the recording defines the target Y)"
        rec_y0 = float(np.load(npz_path)["cable_xyz"][0][0][1])  # recording frame-0 seg-0 y (-0.30)
        phys_jq = self._state_0.joint_q.numpy()
        n_angles = self._cable_bodies_per_world - 1
        for w in range(self._world_count):
            cq0 = self._arm_q_start[w] + _N_ARM_JOINTS  # cable FREE-root joint_q start (root7 + seg angles)
            root7 = phys_jq[cq0 : cq0 + 7].copy()
            root7[1] = rec_y0
            seg_angles = phys_jq[cq0 + 7 : cq0 + 7 + n_angles].copy()
            cable_joints_w = list(
                range(self._jws[w] + _N_ARM_JOINTS, self._jws[w] + _N_ARM_JOINTS + self._cable_bodies_per_world)
            )
            seed_cable_joint_state(self._state_0, self._model, cable_joints_w, root7, seg_angles, dr_xy=(0.0, 0.0))
        print(f"[NewtonRouteEnv] G1 scene-align: cable start y -> {rec_y0} (recording frame-0; support clips OFF)")

    def _physics_step_all(self, substeps=None, sim_dt=None):
        """One physics frame for all worlds (clear_forces -> collide -> solver.step -> swap)."""
        n_sub = substeps if substeps is not None else SIM_SUBSTEPS
        dt = sim_dt if sim_dt is not None else SIM_DT
        for _ in range(n_sub):
            self._state_0.clear_forces()
            self._model.collide(self._state_0, self._contacts)
            self._solver.step(self._state_0, self._state_1, self._control, self._contacts, dt)
            self._state_0, self._state_1 = self._state_1, self._state_0

    def _broadcast_arm_jointq(self):
        """Refresh both arms' POSITION-servo hold target at the FK home (NO joint_q write).

        NO-KINEMATIC (Rs 2026-07-19): the former SC2b joint_q re-pose is REMOVED; the hold is a
        servo TARGET refresh (actuator write only), fail-closed without the arm servo wiring.
        """
        n = _N_ARM_JOINTS
        fk_jq = self._fk_state.joint_q.numpy()[:n]
        # NO-KINEMATIC (Rs 2026-07-19): the hold is a POSITION-servo TARGET refresh (actuator write),
        # never a joint_q force. Requires the arm servo wiring (fail-closed otherwise).
        if not (self._grasp_actuation and self._arm_pd_drive):
            raise RuntimeError("kinematic arm drive REMOVED (Rs directive 2026-07-19 kinematic complete-removal): settle/hold requires the arm POSITION-servo wiring")
        _h_src = self._arm_ow_maps["arm_ow_src"]
        _h_jtp = self._control.joint_target_pos.numpy()
        _h_jtp[self._arm_ow_maps["arm_ow_qd_idx"]] = np.tile(fk_jq[_h_src[: len(_h_src) // self._world_count]], self._world_count)
        self._control.joint_target_pos.assign(_h_jtp)

    def _settle_cable(self):
        """Settle the cable (~2s sim time) while holding both arms at the FK home via the POSITION servo."""
        print("[NewtonRouteEnv] Settling cable (~2s, arms held via POSITION-servo target)...")
        for _ in range(int(2.0 / DT)):
            self._broadcast_arm_jointq()
            self._physics_step_all()
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        self._settled_grasp_x = float(np.mean(bq[self._cable_bodies[0], 0]))
        # z_rest(P0): mean settled cable z (world 0) -- the G2 lift baseline.
        self._cable_z_rest = float(np.mean(bq[self._cable_bodies[0], 2]))
        print(f"[NewtonRouteEnv] Cable settled: mean_x={self._settled_grasp_x:.4f} z_rest={self._cable_z_rest:.4f}")

    # =====================================================================================================
    # P0 precondition (lift-point: arms wide @ 88mm span above the cable) -- reuse of the AC scaffolding
    # =====================================================================================================

    def _setup_p0_precondition(self):
        """Move both arms to the NON-degenerate lift-point P0 (wide 88mm span, wrist ~100mm above table)."""
        print("[NewtonRouteEnv] Setting up P0 precondition (lift-point)...")
        grasp_x = self._settled_grasp_x
        p0_ee_z = TABLE_HEIGHT + 0.100 + EE_TO_PINCH_OPEN  # 1.16092 (wrist)
        self._ik_move_all_worlds(
            (grasp_x, WIDE_LEFT_Y, p0_ee_z), (grasp_x, WIDE_RIGHT_Y, p0_ee_z), label="P0-UPRISE", converge_mm=2.0
        )
        self._hold_all_worlds(SETTLE_STEPS)
        print("[NewtonRouteEnv] P0 complete -- lift-point reached")

    def _solve_ik_single_ko(self, target_left, target_right):
        """Solve dual-arm IK (P0 init) with the DC1 koshape rotation target, PER-ARM (88mm span err=0)."""
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
        step = 0
        for step in range(MAX_MOVE_STEPS):
            t = min((step + 1) / MAX_MOVE_STEPS, 1.0)
            jq_interp = jq_start + (jq_target - jq_start) * t
            # Hold driver fingers at the start (OPEN): the EE pos/rot IK objectives have zero Jacobian on
            # the gripper 4-bar, so let them not drift under the joint-limit objective (faithful to AC).
            for base in (0, JOINTS_PER_ARM):
                jq_interp[base + GRIPPER_DRIVER_JOINT_IDX[0]] = jq_start[base + GRIPPER_DRIVER_JOINT_IDX[0]]
                jq_interp[base + GRIPPER_DRIVER_JOINT_IDX[1]] = jq_start[base + GRIPPER_DRIVER_JOINT_IDX[1]]
            self._fk_state.joint_q.assign(jq_interp)
            newton.eval_fk(self._fk_model, self._fk_state.joint_q, self._fk_state.joint_qd, self._fk_state)
            self._broadcast_arm_jointq()
            self._physics_step_all()
            if (step + 1) % 10 == 0:
                wp.synchronize()
                bq = self._state_0.body_q.numpy()
                ws0 = self._bws[0]
                err_l = np.linalg.norm(bq[ws0 + _LEFT_EE_BODY][:3] - np.array(target_left)) * 1000
                err_r = np.linalg.norm(bq[ws0 + _RIGHT_EE_BODY][:3] - np.array(target_right)) * 1000
                if max(err_l, err_r) < converge_mm:
                    break
        # NO-KINEMATIC fail-loud (c5, pre-check ISSUE 2): under the POSITION servo the arm can silently
        # end short of the IK target (tracking lag) -- kinematic drive could not. A silent shortfall
        # here corrupts P0 (span/pose wrong) and every state derived from it, so verify EVERY world.
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        _mv_errs = []
        for w in range(self._world_count):
            ws = self._bws[w]
            _mv_errs.append(float(np.linalg.norm(bq[ws + _LEFT_EE_BODY][:3] - np.array(target_left)) * 1000))
            _mv_errs.append(float(np.linalg.norm(bq[ws + _RIGHT_EE_BODY][:3] - np.array(target_right)) * 1000))
        if max(_mv_errs) >= converge_mm:
            raise RuntimeError(
                f"[{label}] servo-held move did NOT converge: max EE err {max(_mv_errs):.2f}mm >= "
                f"{converge_mm}mm across {self._world_count} world(s) after {step + 1} steps -- "
                "failing loud instead of returning a corrupt P0 (design sec14)"
            )
        print(f"  [{label}] Done: steps={step + 1}, max EE err {max(_mv_errs):.2f}mm (all worlds)")
        return True

    def _hold_all_worlds(self, n_frames):
        for _ in range(n_frames):
            self._broadcast_arm_jointq()
            self._physics_step_all()

    def _save_precondition_state(self):
        """Cache the P0-complete settled state for episode reset + the nominal EE targets (route stub)."""
        wp.synchronize()
        self._settled_body_q = self._state_0.body_q.numpy().copy()
        self._settled_body_qd = self._state_0.body_qd.numpy().copy()
        self._settled_fk_jq = self._fk_state.joint_q.numpy().copy()
        if self._grasp_actuation:
            # comp3 (R1d/CC4-CH5): the FK gripper coords are FINGER_OPEN_POS FOLLOWER constants -> seeding
            # them at reset risks a 4-bar branch-flip under the POSITION servo. Patch them to world-0's
            # post-settle PHYSICS gripper config (route step-0 = OPEN both arms) so the 28-wide reset-init
            # (and the per-world FK cache below) seed a consistent physics-branch gripper. self._rex (the
            # route_executor module) is set flag-ON in _build_model, which runs before this.
            self._rex.patch_settled_fk_gripper(self._settled_fk_jq, self._state_0.joint_q.numpy(), self._arm_q_start[0])
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
        print(f"[NewtonRouteEnv] P0 saved: EE_R={self._settled_ee_r_pos}, EE_L={self._settled_ee_l_pos}")

    def _init_batched_ik_solver(self):
        """Cached IKSolver(n_problems=world_count) with the KO rot target (held; action is position-only)."""
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
        self._ik_solver_batch = IKSolver(
            self._fk_model,
            n_problems=N,
            objectives=[
                self._ik_obj_pos_left,
                self._ik_obj_pos_right,
                self._ik_obj_rot_left,
                self._ik_obj_rot_right,
                self._ik_obj_jlimit,
            ],
        )
        coord_count = self._fk_model.joint_coord_count
        self._ik_jq_in = wp.zeros((N, coord_count), dtype=float, device=self.device)
        self._ik_jq_out = wp.zeros((N, coord_count), dtype=float, device=self.device)
        print(f"[NewtonRouteEnv] Batched IK solver: n_problems={N}, joint_coords={coord_count}")

    def _solve_ik_batch(self, targets_left_np, targets_right_np, jq_starts_np):
        """Solve IK for all worlds in one batched, warm-started call. Returns [N, coord_count] numpy."""
        self._ik_obj_pos_left.set_target_positions(wp.array(targets_left_np, dtype=wp.vec3, device=self.device))
        self._ik_obj_pos_right.set_target_positions(wp.array(targets_right_np, dtype=wp.vec3, device=self.device))
        self._ik_jq_in.assign(jq_starts_np)
        self._ik_solver_batch.step(self._ik_jq_in, self._ik_jq_out, iterations=IK_ITERATIONS_RL, step_size=IK_STEP_SIZE)
        return self._ik_jq_out.numpy()

    def _compute_target_seg_indices(self, bq):
        """Per-arm target cable seg indices (+/-window, MID-SPLIT so arms can't share a seg)."""
        n_cable = self._cable_bodies_per_world
        win = 5
        n_seg = 2 * win + 1
        result_r = np.zeros((self._world_count, n_seg), dtype=np.int32)
        result_l = np.zeros((self._world_count, n_seg), dtype=np.int32)
        mid = n_cable // 2
        for w in range(self._world_count):
            ws = self._bws[w]
            cable_pos = bq[self._cable_bodies[w], :3]
            right_idx = ws + _RIGHT_EE_BODY
            right_tip = clamp_pos_ko(bq[right_idx][:3], bq[right_idx][3:7])
            right_seg = mid + int(np.argmin(np.linalg.norm(cable_pos[mid:n_cable] - right_tip, axis=1)))
            result_r[w] = np.clip(np.arange(right_seg - win, right_seg + win + 1), 0, n_cable - 1)
            left_idx = ws + _LEFT_EE_BODY
            left_tip = clamp_pos_ko(bq[left_idx][:3], bq[left_idx][3:7])
            left_seg = int(np.argmin(np.linalg.norm(cable_pos[0 : mid + 1] - left_tip, axis=1)))
            result_l[w] = np.clip(np.arange(left_seg - win, left_seg + win + 1), 0, n_cable - 1)
        return result_r, result_l

    # =====================================================================================================
    # Reset (mujoco: body_q restore + AUTHORITATIVE joint_q seeding of arm + cable)
    # =====================================================================================================

    def _reset_worlds(self, env_ids):
        """Reset specified worlds to the P0 settled state; clear reward-latch / route / debounce state."""
        if len(env_ids) == 0:
            return
        # (a)(b) clip-pin lifecycle: audit-then-clear BEFORE the state restore, on every reset path
        # (done-driven and public reset()) -- prereg v0.3.1 sec 4.
        self._clear_c1_pin(env_ids)
        # NO-KINEMATIC (c13): the settled-BODY-state restore (restore_world_body_state /
        # assign_world_states_to_sim) is REMOVED. On the mujoco joint-authoritative path bodies follow
        # joint_q via the CABLE-SEED eval_fk (below); the arm is held by its POSITION servo (design
        # sec14.2, per-episode qpos re-pose abolished). No body_q/body_qd write at reset.
        for w in env_ids:
            w = int(w)
            self._per_world_fk_jq[w] = self._settled_fk_jq.copy()
            self._ee_target_right[w] = self._settled_ee_r_pos.copy()
            self._ee_target_left[w] = self._settled_ee_l_pos.copy()
            if self.INIT_XY_NOISE > 0:
                self._ee_target_right[w][:2] += np.random.uniform(-self.INIT_XY_NOISE, self.INIT_XY_NOISE, size=2)
                self._ee_target_left[w][:2] += np.random.uniform(-self.INIT_XY_NOISE, self.INIT_XY_NOISE, size=2)
            _id4 = np.array([0, 0, 0, 1], dtype=np.float32)
            self._prev_clamp_r_quat[w] = _id4.copy()
            self._prev_clamp_l_quat[w] = _id4.copy()
            self._prev_seg_r_quat[w] = _id4.copy()
            self._prev_seg_l_quat[w] = _id4.copy()
            # reward-latch / sustain / debounce / route state
            self._g_latched[w] = False
            self._g6_sustain[w] = 0
            self._contact_loss_count[w] = 0
            self._last_executed_residual[w] = 0.0
            self._last_projection_mode[w] = 0
            self._last_ik_resid[w] = 0.0
            self._phase_entry_step[w] = 0
            self._prev_phase_id[w] = -1
            self.episode_length_buf[w] = 0
            self.route_t[w] = 0  # W1-B1 mirror (per-world reset site; fork init bank_boundary[k] = B3)
            # W1-B2 (conformance R3k): per-world HOLD clear through the executor's world-sliced API --
            # never a blanket clear (a neighbor's done-reset must leave OTHER held worlds byte-intact).
            self._suppressed_drop_count[w] = 0
            if self._route_t_clock:
                self._route.clear_sync_state([int(w)])
                self._hold_mask_np[int(w)] = False

        # AUTHORITATIVE re-pose (mujoco): seed arm joint_q = settled + cable joint_q from settled tangents.
        # NO-KINEMATIC (Rs 2026-07-19): the reset does NOT re-pose the arm joints (per-episode qpos
        # seeding abolished, design sec14.0/14.2). The arm continues under its POSITION-servo hold;
        # the physical homing transit (sec14.2 steps 1-2) is the replacement mechanism (future chunk).
        # Servo target refresh to the settled home = actuator write only.
        if self._grasp_actuation and self._arm_pd_drive:
            _r_jtp = self._control.joint_target_pos.numpy()
            _r_src12 = self._arm_ow_maps["arm_ow_src"][:12]
            _r_home = self._settled_fk_jq[_r_src12]
            for w in env_ids:
                w = int(w)
                _r_jtp[self._arm_ow_maps["arm_ow_qd_idx"][w * 12 : (w + 1) * 12]] = _r_home
            self._control.joint_target_pos.assign(_r_jtp)
        if self._grasp_actuation:
            # comp3 (R1a): the 28-wide reset-init above re-poses the gripper joint_q (patched OPEN branch)
            # + zeroes qd, but the servo TARGET still carries the episode-end CLOSED command -> re-seed it to
            # OPEN (route step-0) for the reset worlds only (per-world subset; K1c) so episode >= 2 starts OPEN.
            self._route.reseed_grip_open(env_ids)
            if self._arm_pd_drive:
                # NO-KINEMATIC (Rs 2026-07-19): the route-start re-pose (teleport of the arm joint_q to
                # the recording's frame-0; design v1.3 correction #3) is REMOVED -- per-episode qpos
                # seeding is abolished (design sec14.0/14.2). The replacement is the physical homing
                # transit (sec14.2 steps 1-2 / sec14.3, future chunk): it must DELIVER the arm to the
                # frame-0 pose under the POSITION servo before the route may start. Until then this
                # gate fails LOUDLY: starting the route from a distant pose would PD-slew the arm
                # across the whole gap and replay the choreography against a wrong start state.
                _rs_rec = getattr(self._route, "_recording", None)
                if _rs_rec is None or _rs_rec.get("arm_q") is None:
                    raise RuntimeError("route-start pose gate needs a recording with arm_q")
                _rs_row = np.asarray(_rs_rec["arm_q"][0], dtype=np.float64)[:_N_ARM_JOINTS]
                _rs_tgt12 = _rs_row[self._arm_ow_maps["arm_ow_src"][:12]]  # arm-local columns {0-5,14-19}
                _rs_jq = self._state_0.joint_q.numpy()  # read-only: gate measurement, never written back
                _rs_jtp = self._control.joint_target_pos.numpy()
                for w in env_ids:
                    w = int(w)
                    _rs_q12 = _rs_jq[self._arm_ow_maps["arm_ow_q_idx"][w * 12 : (w + 1) * 12]]
                    _rs_gap = float(np.max(np.abs(_rs_q12 - _rs_tgt12)))
                    if _rs_gap > _ROUTE_START_POSE_TOL_RAD:
                        raise RuntimeError(
                            f"route-start pose gate: world {w} arm q is {_rs_gap:.3f} rad (max-abs) from "
                            f"the recording's frame-0 (tol {_ROUTE_START_POSE_TOL_RAD}) and the kinematic "
                            "re-pose is REMOVED (Rs directive 2026-07-19 kinematic complete-removal) -- "
                            "the physical homing transit (design sec14.2/14.3) is not implemented yet, "
                            "so the route cannot start from this pose"
                        )
                    # Within tolerance (the transit delivered the arm): sync the POSITION-servo target
                    # to the EXACT frame-0 row -- actuator write only (M-4 ctrl/q sync, kept).
                    _rs_jtp[self._arm_ow_maps["arm_ow_qd_idx"][w * 12 : (w + 1) * 12]] = _rs_tgt12
                self._control.joint_target_pos.assign(_rs_jtp)
        for w in env_ids:
            w = int(w)
            cable_joints_w = list(
                range(self._jws[w] + _N_ARM_JOINTS, self._jws[w] + _N_ARM_JOINTS + self._cable_bodies_per_world)
            )
            root7, seg_angles = derive_cable_joint_q_from_tangents(self._settled_body_q, self._cable_bodies[w])
            seed_cable_joint_state(self._state_0, self._model, cable_joints_w, root7, seg_angles, dr_xy=(0.0, 0.0))

        new_r, new_l = self._compute_target_seg_indices(self._state_0.body_q.numpy())
        for w in env_ids:
            w = int(w)
            self._target_seg_indices_r[w] = new_r[w]
            self._target_seg_indices_l[w] = new_l[w]
        reset_dahl_friction_for_envs(self._solver, self._jws, env_ids)
        self._episode_count += len(env_ids)

    # =====================================================================================================
    # Action: alpha-6D residual (NON-accumulating) + (b') phase-conditional projection
    # =====================================================================================================

    def _sigma_cap(self, delta):
        """Clamp a per-arm residual vector's norm to GRIPPING_ARM_SIGMA_CAP_M (transit drop-prevention)."""
        n = float(np.linalg.norm(delta))
        if n > self.GRIPPING_ARM_SIGMA_CAP_M and n > 1e-9:
            return delta * (self.GRIPPING_ARM_SIGMA_CAP_M / n)
        return delta

    def _delta_bound(self, delta):
        """Clamp a per-arm residual vector's norm to DELTA_BOUND_M (env-core Delta-bound, CC3-CH1)."""
        n = float(np.linalg.norm(delta))
        if n > self.DELTA_BOUND_M and n > 1e-9:
            return delta * (self.DELTA_BOUND_M / n)
        return delta

    def _project_residual(self, delta_r, delta_l, is_dual, grip_r, grip_l):
        """(b') phase-conditional structural projection of the AS-EXECUTED residual.

        dual-grip window (base grip-schedule ALONE) -> hard-project to the common-mode subspace
        ((d_R,d_L)->(m,m), m=(d_R+d_L)/2): the differential is 0 by construction so the span is
        structurally invariant (enforcement, not detection). non-dual-grip transit -> asymmetric
        per-arm: reaching arm (grip open) full, gripping arm (grip close) sigma-capped. arm-role is
        derived from the base grip-schedule (NEW-D single deterministic source, boundary-consistent).

        Returns:
            (residual_r [3], residual_l [3], mode int) -- mode 0 = common-mode, 1 = transit-asym.
        """
        dr = self._delta_bound(delta_r)
        dl = self._delta_bound(delta_l)
        if is_dual:
            m = 0.5 * (dr + dl)
            return m.copy(), m.copy(), 0
        out_r = self._sigma_cap(dr) if grip_r >= 0.5 else dr
        out_l = self._sigma_cap(dl) if grip_l >= 0.5 else dl
        return out_r, out_l, 1

    def _apply_actions_batch(self, actions, route_targets):
        """Apply the 6D residual to the route ABSOLUTE base target (NON-accumulating) via batched IK.

        actions [N, 6]: [0:3] R residual, [3:6] L residual (position-only). route_targets [N, 6]: the
        route's per-step ABSOLUTE base target [R_xyz, L_xyz]. commanded = base + projected-residual --
        the base target is absolute each step (NOT integrated), so Delta=const -> drift=0 by construction
        (the AC accumulating delta at newton_approach_cable_mujoco_env.py:40 is NOT reused).
        """
        N = self._world_count
        actions_np = actions.cpu().numpy()
        r_delta = actions_np[:, 0:3] * self.POS_RESIDUAL_SCALE
        l_delta = actions_np[:, 3:6] * self.POS_RESIDUAL_SCALE

        targets_left = np.zeros((N, 3), dtype=np.float32)
        targets_right = np.zeros((N, 3), dtype=np.float32)
        jq_starts = np.array(self._per_world_fk_jq[:N])
        # Fingers held OPEN in the IK warm-start (grip is a scripted servo predicate, not an action dim).
        for w in range(N):
            for base in (0, JOINTS_PER_ARM):
                jq_starts[w, base + GRIPPER_DRIVER_JOINT_IDX[0]] = FINGER_OPEN_POS
                jq_starts[w, base + GRIPPER_DRIVER_JOINT_IDX[1]] = FINGER_OPEN_POS

        for w in range(N):
            proj_r, proj_l, mode = self._project_residual(
                r_delta[w], l_delta[w], self._route_is_dual[w], self._route_grip[w, 0], self._route_grip[w, 1]
            )
            base_r = route_targets[w, 0:3]
            base_l = route_targets[w, 3:6]
            # NON-accumulating: commanded = absolute base + projected residual (no += integration).
            target_r = base_r + proj_r
            target_l = base_l + proj_l
            # Substrate Z safety floor/ceiling ONLY (koshape lane-aware floor; not an accumulation anchor).
            # mode 0 (common-mode dual) -> shared max floor for both arms (R-A span preservation).
            floor_r, floor_l = ee_z_floor_ko_pair(target_r[0], target_r[1], target_l[0], target_l[1], mode == 0)
            target_r[2] = np.clip(target_r[2], floor_r, EE_Z_SAFETY_UPPER)
            target_l[2] = np.clip(target_l[2], floor_l, EE_Z_SAFETY_UPPER)
            targets_right[w] = target_r
            targets_left[w] = target_l
            self._ee_target_right[w] = target_r.copy()
            self._ee_target_left[w] = target_l.copy()
            # as-executed a' (post-projection) + mode -> exposed in extras["info"] (NEW-C).
            self._last_executed_residual[w, 0:3] = proj_r
            self._last_executed_residual[w, 3:6] = proj_l
            self._last_projection_mode[w] = mode

        if self._route_drive_ff:
            # D rho=0 feedforward drive (Rs adjudication (1); SCRIPTED-VERIFICATION stage -- trainer D-b
            # window design is a SEPARATE gate): the arms replay the RECORDED arm_q per physics frame
            # (armqdirect-proven mechanism, c2045a9a1a) -- the step-level IK solve + 10-frame joint chord
            # are SKIPPED entirely (the decision-packet sec4 3.61x saving). The residual/target bookkeeping
            # above is kept (obs/extras contract; the projected residual is NOT driven in this mode).
            # reset/broadcast paths are untouched (feedforward lives in this drive loop only).
            route_steps = [int(self.route_t[w].item()) for w in range(N)]  # W1-B1: route clock (consumer 3)
            # W1-B2 (spec sec 4.2 N3): held worlds clamp the replay frame to the frozen chunk END --
            # re-walking the chunk's staircase every held step would saw-tooth the servo/arm.
            hm = self._hold_mask_np if self._route_t_clock else None
            jq_ff = None
            for step in range(self.PHYSICS_STEPS_PER_RL):
                jq_ff = self._route.apply_recorded_arm_ff(
                    route_steps,
                    step,
                    self._state_0,
                    self._arm_ow_maps["arm_ow_q_idx"],
                    self._arm_ow_maps["arm_ow_qd_idx"],
                    hold_mask=hm,
                )
                self._route.apply_recorded_grip(route_steps, step, hold_mask=hm)
                self._maybe_activate_c1_pin(route_steps, step)  # (d2): no-op unless route_c1_pin
                self._physics_step_all(substeps=RL_SIM_SUBSTEPS, sim_dt=RL_SIM_DT)
            # FK-side warm-start/obs source: arm cols <- the final feedforward row; gripper cols keep
            # their pinned-OPEN values (production fk_jq semantic; flag-ON obs[7]/[15] read physics).
            for w in range(N):
                row = self._per_world_fk_jq[w].copy()
                for li in self._rex._ARM_OVERWRITE_LOCAL:
                    row[li] = jq_ff[w][li]
                self._per_world_fk_jq[w] = row
        else:
            jq_targets = self._solve_ik_batch(targets_left, targets_right, jq_starts)
            nan_mask = np.any(np.isnan(jq_targets), axis=1)
            if np.any(nan_mask):
                jq_targets[nan_mask] = jq_starts[nan_mask]
            # Preserve OPEN fingers in the IK output.
            for w in range(N):
                for base in (0, JOINTS_PER_ARM):
                    jq_targets[w, base + GRIPPER_DRIVER_JOINT_IDX[0]] = jq_starts[w, base + GRIPPER_DRIVER_JOINT_IDX[0]]
                    jq_targets[w, base + GRIPPER_DRIVER_JOINT_IDX[1]] = jq_starts[w, base + GRIPPER_DRIVER_JOINT_IDX[1]]

            # DRIVE: interpolate the arm target start->target per frame and write it to the
            # POSITION-servo ctrl (NO joint_q write -- Rs 2026-07-19 kinematic complete-removal).
            old_fk_jq = np.array(self._per_world_fk_jq[:N])
            if self._grasp_actuation:
                # comp3 (R2): per-world route step for the recorded grip staircase lookup cf[t_w]+sub_i. This is
                # read HERE (before the per-frame loop) because route_t is not incremented until after
                # _apply_actions_batch returns, so it holds THIS step's t_w == the value _pull_route used.
                route_steps = [int(self.route_t[w].item()) for w in range(N)]  # W1-B1: route clock (consumer 2)
            for step in range(self.PHYSICS_STEPS_PER_RL):
                t = min((step + 1) / self.PHYSICS_STEPS_PER_RL, 1.0)
                jq_interp = old_fk_jq + (jq_targets - old_fk_jq) * t
                if self._grasp_actuation and self._arm_pd_drive:
                    # (d) P-D1 ARM ctrl-drive (design M-2 / sec2 (A)): write the SAME per-frame interp
                    # target into the POSITION-servo ctrl (read->mutate->assign, CC3-CH5) instead of
                    # forcing joint_q/qd (the kinematic write path is REMOVED, Rs 2026-07-19).
                    # joint_target_pos is qd-indexed (set_gripper_target docstring); rows/cols via the
                    # maps so no private import. M-5 ramp: on activation, blend from the realized arm
                    # q over ARM_PD_RAMP_FRAMES physics frames (0 = off).
                    _apd_src = self._arm_ow_maps["arm_ow_src"]
                    _apd_rows = np.repeat(np.arange(jq_interp.shape[0]), len(_apd_src) // jq_interp.shape[0])
                    _apd_tgt = jq_interp[_apd_rows, _apd_src]
                    if self._arm_pd_ramp_frames > 0:
                        if self._arm_pd_ramp_k is None:
                            self._arm_pd_ramp_q0 = self._state_0.joint_q.numpy()[self._arm_ow_maps["arm_ow_q_idx"]].copy()
                            self._arm_pd_ramp_k = 0
                        _apd_b = min(1.0, self._arm_pd_ramp_k / float(self._arm_pd_ramp_frames))
                        _apd_tgt = _apd_b * _apd_tgt + (1.0 - _apd_b) * self._arm_pd_ramp_q0
                        self._arm_pd_ramp_k += 1
                    _apd_jtp = self._control.joint_target_pos.numpy()
                    _apd_jtp[self._arm_ow_maps["arm_ow_qd_idx"]] = _apd_tgt
                    self._control.joint_target_pos.assign(_apd_jtp)
                else:
                    raise RuntimeError("kinematic arm drive REMOVED (Rs directive 2026-07-19 kinematic complete-removal): the per-step arm drive is the POSITION-servo ctrl path only")
                if self._grasp_actuation:
                    # comp3 (R2): drive the gripper POSITION-servo from the recorded grip_cmd staircase for THIS
                    # physics sub-frame, AFTER the arm servo retarget and BEFORE the solver step (so the servo
                    # target is in place). Writes control.joint_target_pos ONLY (gripper joint_q is servo-DYNAMIC).
                    self._route.apply_recorded_grip(
                        route_steps, step, hold_mask=self._hold_mask_np if self._route_t_clock else None
                    )
                self._physics_step_all(substeps=RL_SIM_SUBSTEPS, sim_dt=RL_SIM_DT)
            for w in range(N):
                self._per_world_fk_jq[w] = jq_targets[w].copy()

        # IK residual per arm ([55:57]): achieved EE vs commanded target.
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        for w in range(N):
            ws = self._bws[w]
            self._last_ik_resid[w, 0] = float(np.linalg.norm(bq[ws + _RIGHT_EE_BODY][:3] - targets_right[w]))
            self._last_ik_resid[w, 1] = float(np.linalg.norm(bq[ws + _LEFT_EE_BODY][:3] - targets_left[w]))

    # =====================================================================================================
    # Live geometric helpers (raw per-clip sim distance, NEW-5; cable-position proxies)
    # =====================================================================================================

    def _active_clip_xy(self, phase_id):
        """Phase-active clip XY (base-scripted phase_id pin, CC2-CH4). C1 through G4-start, then C2."""
        return _C1_XY if phase_id < 3 else _C2_XY

    _SEAT_MISS_DX_M = 9.0  # sentinel dx when the cable never crosses y=clip_y (fail-closed: seat legs
    #                        reject; finite so np.nan_to_num leaves it in obs, unlike NaN -> 0 = "seated").

    def _seat_crossing(self, cable_pos, clip_x, clip_y, segment_indices=None):
        """Interpolate the cable's (x, z) where it crosses exactly y=clip_y, at the groove-closest crossing.

        reward-design 2 fix (ruling REWARDDESIGN_GATE2_SEAT_PREDICATE_RULING sec 2/sec 8/sec 11). The pre-fix
        seat metric took the nearest-in-Y cable NODE and used its 2D lateral, leaking the node's Y-quantisation
        residual (~half the 15mm segment pitch, ~7.5mm) into the off-axis distance -- so a physically seated
        cable failed the 3mm bar ~60-70% of the time. Here we interpolate x,z at exactly y=clip_y (dy == 0 by
        construction, quantisation-free). ``segment_indices`` optionally restricts the search to routed
        identity candidates (FM4); an empty set therefore fails closed. Among the remaining segments
        straddling y=clip_y (S-curve / D-5) we prefer a crossing inside the z-band, then the minimum
        ``|x - clip_x|``. Returns ``(x_cross, z_cross)`` [m], or ``(None, None)`` if no allowed segment reaches
        y=clip_y (fail-closed). ``cable_pos`` is node-ordered (the
        40-body chain, :1644), so consecutive rows are adjacent -- the offline mirror
        (``p9_recount_strict_v2``) walks the same polyline and DoD-9a (live == frozen) holds.
        """
        ys = cable_pos[:, 1]
        y0 = ys[:-1]
        y1 = ys[1:]
        straddle = ((y0 - clip_y) * (y1 - clip_y) <= 0.0) & (y0 != y1)
        if segment_indices is not None:
            allowed = np.zeros(len(straddle), dtype=bool)
            allowed_idx = np.asarray(tuple(segment_indices), dtype=np.int64)
            allowed_idx = allowed_idx[(allowed_idx >= 0) & (allowed_idx < len(straddle))]
            allowed[allowed_idx] = True
            straddle &= allowed
        if not straddle.any():
            return None, None
        idx = np.nonzero(straddle)[0]
        t = (clip_y - y0[idx]) / (y1[idx] - y0[idx])
        x_cross = cable_pos[idx, 0] + t * (cable_pos[idx + 1, 0] - cable_pos[idx, 0])
        z_cross = cable_pos[idx, 2] + t * (cable_pos[idx + 1, 2] - cable_pos[idx, 2])
        dx = np.abs(x_cross - clip_x)
        in_band = (z_cross > rc.SEAT_Z_LO_M) & (z_cross < rc.SEAT_Z_HI_M)
        best = int(np.lexsort((dx, np.where(in_band, 0, 1)))[0])  # primary: prefer in-band; secondary: min dx
        return float(x_cross[best]), float(z_cross[best])

    _SEAT_MONOTONE_TOL_M = 1.0e-6  # [m] permits micron-scale numeric wobble, not a physical Y reversal

    def _seat_identity_segments(self, cable_pos, clip_xy):
        """Return routed crossing-segment candidates for a C1 or C2 seat measurement.

        C1 uses the producer-equivalent hard identity: the pinned seat node must be one endpoint of the
        interpolated crossing. C2 has no fixed seat body, so its crossing must be connected to that C1 node by
        a Y-monotone cable span ON THE ROUTED CABLE-INDEX SIDE of the pin (``ROUTE_C2_SIDE_FROM_PIN``; I4,
        ruling section S3.2 -- a FEED-side free span can drape through the C2 groove Y-monotonically too, so
        monotony alone is not identity). This is pay-through robust and rejects a disconnected stray loop
        without a fixed N-hop assumption (reward-design gate-2 ruling section 13.4).
        """
        pin_seg = getattr(self, "_pin_seat_seg", None)
        if pin_seg is None:
            return ()  # identity unavailable -> fail closed, never fall back to the exploitable global search
        pin_seg = int(pin_seg)
        n_nodes = int(len(cable_pos))
        if not 0 <= pin_seg < n_nodes:
            raise ValueError(f"C1 pin seat segment {pin_seg} outside cable node range [0, {n_nodes})")

        clip_xy = np.asarray(clip_xy, dtype=np.float64)
        if np.allclose(clip_xy, np.asarray(_C1_XY), rtol=0.0, atol=1.0e-12):
            # A crossing segment i owns nodes (i, i+1); requiring the pin node as an endpoint is the minimal
            # interpolation window. Canonical 81-cell evidence is exactly i-pin in {-1, 0}.
            return (pin_seg - 1, pin_seg)
        if not np.allclose(clip_xy, np.asarray(_C2_XY), rtol=0.0, atol=1.0e-12):
            raise ValueError(f"no routed seat identity is defined for clip centre {clip_xy.tolist()}")

        ys = np.asarray(cable_pos[:, 1], dtype=np.float64)
        target_y = float(clip_xy[1])
        direction = target_y - float(ys[pin_seg])
        if abs(direction) <= self._SEAT_MONOTONE_TOL_M:
            return ()  # C1 identity is already at C2Y: ambiguous/corrupt route, fail closed
        # I4: only the routed index side may seat C2; the side is a route design constant (grounded in
        # route_env_config). An empty side (degenerate pin at a cable end) falls through to () = fail closed.
        if int(rc.ROUTE_C2_SIDE_FROM_PIN) < 0:
            seg_range = range(0, pin_seg)
        else:
            seg_range = range(pin_seg, n_nodes - 1)
        candidates = []
        for seg in seg_range:
            # Walk in cable order FROM the C1 pin node TO both endpoints of this candidate crossing.
            if seg < pin_seg:
                path_y = ys[seg : pin_seg + 1][::-1]
            else:
                path_y = ys[pin_seg : seg + 2]
            steps = np.diff(path_y)
            if direction < 0.0:
                monotone = bool(np.all(steps <= self._SEAT_MONOTONE_TOL_M))
            else:
                monotone = bool(np.all(steps >= -self._SEAT_MONOTONE_TOL_M))
            if monotone:
                candidates.append(seg)
        return tuple(candidates)

    @staticmethod
    def _seated_in_groove(dx, z_cross):
        """Shared seat predicate: cable centre geometrically inside the groove (built-model bars,
        ``route_env_config.SEAT_*``). ``dx`` (walls) and ``z`` (floor/rim) are SEPARATE legs -- supersedes
        the combined ``seat_dist < T_GROOVE`` (ruling sec 2)."""
        return bool(dx <= rc.SEAT_LAT_BAR_M and rc.SEAT_Z_LO_M < z_cross < rc.SEAT_Z_HI_M)

    def _seat_metrics(self, cable_pos, clip_xy):
        """(dx [m], z_cross [m]) of the interpolated y=clip_y crossing vs a clip groove axis.

        ``dx = |x_cross - clip_x|`` at the groove-closest crossing (quantisation-free). ``z_cross`` =
        interpolated cable-centre z. Fail-closed: a cable never reaching y=clip_y returns
        ``(_SEAT_MISS_DX_M, 0.0)`` so both seat legs reject. Consumers: G3/G5 (:1487-1488 / :1550-1552),
        obs [49]/[58]/[59], c2_honest, c1_retained, and the post-G3 escape guard (I3: the same-step dx at
        the reward site feeds :meth:`_c1_escape_after_seat`).
        """
        identity_segments = self._seat_identity_segments(cable_pos, clip_xy)
        x_cross, z_cross = self._seat_crossing(
            cable_pos,
            float(clip_xy[0]),
            float(clip_xy[1]),
            segment_indices=identity_segments,
        )
        if x_cross is None:
            return self._SEAT_MISS_DX_M, 0.0
        return abs(x_cross - float(clip_xy[0])), z_cross

    def _c1_retention_m(self, cable_pos):
        """(dx_c1 [m], z_cross_c1 [m]) at the C1 groove -- the c1_retained live inputs (obs [60]/[61]).

        Interp-dx REPLACES the pre-fix z-only ceiling (z_c1 < 0.840 and flank_max < 0.840), which had no
        lateral (identity) leg and passed 81/81 = a no-op (ruling sec 8b, defect #2). The SAME interpolation
        runs here (live) and in the frozen recount (``p9_recount_strict_v2.flank_from_npz``), both on the
        node-ordered 40-body cable, so DoD-9a (live == frozen) holds on the corrected instrument.
        ``c1_retained := _seated_in_groove(dx_c1, z_cross_c1)``.
        """
        return self._seat_metrics(cable_pos, _C1_XY)

    def _crossing_x_dev(self, cable_pos):
        """Signed crossing-x deviation at y=C1Y [m] -- obs [57] (H-drape sensing) ONLY. Now truly
        interpolated (the pre-fix code took the nearest-in-Y NODE x despite its 'interpolation' comment; Rs
        '4th site'). Returns ``None`` when there is no crossing; pre-G3 callers may map that to zero.
        NOT a reward/termination input: the post-G3 escape guard reads the identity-restricted
        :meth:`_c1_retention_m` dx instead (I3, ruling sec S3.1) -- this global, identity-UNRESTRICTED
        crossing wanders to ~50mm dev pre-onset on canonical and must never gate anything."""
        x_cross, _ = self._seat_crossing(cable_pos, float(_C1_XY[0]), float(_C1_XY[1]))
        return None if x_cross is None else float(x_cross - float(_C1_XY[0]))

    def _c1_escape_after_seat(self, dx_c1, c1_latched):
        """Return whether C1 escaped after G3 established a routed seat (FM3, fail-closed).

        ``dx_c1`` MUST be the same-step identity-restricted C1 seat measurement -- the
        :meth:`_seat_metrics` ``(cable_pos, _C1_XY)`` / :meth:`_c1_retention_m` dx the seat predicate itself
        consumed (I3, ruling sec S3.1: the guard and the predicate read the SAME instrument; identity is a
        property of the measurement, not a per-predicate choice). Before G3, not crossing C1Y is normal and
        cannot terminate the episode. After G3, a MISS (the identity window lost its crossing) or a lateral
        deviation beyond the drop bar is a fail-closed escape. Scope: lateral escape and crossing loss
        ONLY -- a z-excursion out of the groove band keeps dx small and is NOT drop-guarded; it is sealed on
        the success side by the G6 ``c1_retained`` z-band leg (:meth:`_seated_in_groove`).
        """
        if not bool(c1_latched):
            return False
        return bool(dx_c1 == self._SEAT_MISS_DX_M or dx_c1 > self.DROP_LATERAL_DEV_MAX_M)

    def _lane_matched_target(self, cable_pos, phase_id, r_clamp_pos, search_idx):
        """[16:19] redefine (CC2-CH5): in the regrasp window, the reaching-arm's lane-matched grip target
        = the cable point nearest the R lane (y = C2Y + GHS), NOT argmin find_nearest. Else = the R-arm
        nearest cable seg (base semantics), searched within this world's window ``search_idx``.
        """
        if phase_id == 3:  # G4 regrasp window
            r_lane_y = float(_C2_XY[1]) + _GHS
            i = int(np.argmin(np.abs(cable_pos[:, 1] - r_lane_y)))
            return cable_pos[i, :3].astype(np.float32)
        seg_pos, _, _ = find_nearest_cable_point(cable_pos, r_clamp_pos, search_idx)
        return seg_pos.astype(np.float32)

    # =====================================================================================================
    # Observation (62D)
    # =====================================================================================================

    def _compute_obs_batch(self):
        """Compute observations for all worlds. Returns [N, 62] tensor (index map = route_env_config)."""
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        # comp3 (R6): flag-ON obs[7]/[15] read the PHYSICS joint_q (servo-driven fingers); the FK-side sum
        # pins fingers OPEN and would lie under the live servo (K7). flag-OFF stays FK-side (byte-preserve).
        phys_jq_obs = self._state_0.joint_q.numpy() if self._grasp_actuation else None
        obs_np = np.zeros((self._world_count, rc.OBS_DIM), dtype=np.float32)

        for w in range(self._world_count):
            ws = self._bws[w]
            ph = int(self._route_phase_id[w])

            # ---- base [0:42] (mirror of the AC base obs block) ----
            ee_r_idx = ws + _RIGHT_EE_BODY
            clamp_r_pos = clamp_pos_ko(bq[ee_r_idx][:3], bq[ee_r_idx][3:7])
            clamp_r_quat = temporal_quat_consistency(
                normalize_quat_w_positive(bq[ee_r_idx][3:7]), self._prev_clamp_r_quat[w]
            )
            self._prev_clamp_r_quat[w] = clamp_r_quat.copy()
            ee_l_idx = ws + _LEFT_EE_BODY
            clamp_l_pos = clamp_pos_ko(bq[ee_l_idx][:3], bq[ee_l_idx][3:7])
            clamp_l_quat = temporal_quat_consistency(
                normalize_quat_w_positive(bq[ee_l_idx][3:7]), self._prev_clamp_l_quat[w]
            )
            self._prev_clamp_l_quat[w] = clamp_l_quat.copy()

            if self._grasp_actuation:
                # comp3 (R6): physics joint_q driver readback (per-world) -- the live-servo truth.
                r_finger, l_finger = physics_finger_obs(phys_jq_obs, self._arm_q_start[w])
            else:
                fk_jq = self._per_world_fk_jq[w]
                _rd0, _rd1 = JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0], JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]
                r_finger = fk_jq[_rd0] + fk_jq[_rd1]
                l_finger = fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] + fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]]

            cable_pos = bq[self._cable_bodies[w], :3]
            seg_pos, seg_tangent, _ = find_nearest_cable_point(cable_pos, clamp_r_pos, self._target_seg_indices_r[w])
            seg_quat = temporal_quat_consistency(
                normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent, base_quat=KO_BASE_HAND_DOWN_QUAT)),
                self._prev_seg_r_quat[w],
            )
            self._prev_seg_r_quat[w] = seg_quat.copy()
            seg_pos_l, seg_tangent_l, _ = find_nearest_cable_point(
                cable_pos, clamp_l_pos, self._target_seg_indices_l[w]
            )
            grasp_quat_l = temporal_quat_consistency(
                normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_l, base_quat=KO_BASE_HAND_DOWN_QUAT)),
                self._prev_seg_l_quat[w],
            )
            self._prev_seg_l_quat[w] = grasp_quat_l.copy()

            # [16:19] REDEFINED = lane-matched regrasp target (CC2-CH5).
            lane_seg = self._lane_matched_target(cable_pos, ph, clamp_r_pos, self._target_seg_indices_r[w])
            ori_error_aa = compute_ori_error_axis_angle(clamp_r_quat, seg_quat)
            ori_error_aa_l = compute_ori_error_axis_angle(clamp_l_quat, grasp_quat_l)

            obs_np[w, 0:3] = clamp_r_pos
            obs_np[w, 3:7] = clamp_r_quat
            obs_np[w, 7] = r_finger
            obs_np[w, 8:11] = clamp_l_pos
            obs_np[w, 11:15] = clamp_l_quat
            obs_np[w, 15] = l_finger
            obs_np[w, 16:19] = lane_seg  # CC2-CH5 lane-matched regrasp target
            obs_np[w, 19:23] = seg_quat
            obs_np[w, 23:26] = np.array([_C1_XY[0], _C1_XY[1], TABLE_HEIGHT], dtype=np.float32)
            obs_np[w, 26:30] = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
            obs_np[w, 30:33] = ori_error_aa
            obs_np[w, 33:36] = clamp_r_pos - lane_seg  # pos-err vs the (redefined) target seg
            obs_np[w, 36:39] = ori_error_aa_l
            obs_np[w, 39:42] = clamp_l_pos - seg_pos_l

            # ---- route-specific [42:62] ----
            # [42:48] phase one-hot (argmax = base-scripted phase_id).
            if 0 <= ph < rc.N_ROUTE_PHASES:
                obs_np[w, 42 + ph] = 1.0
            # [48] held cable z: cable body nearest the R/L clamp midpoint.
            mid_xy = 0.5 * (clamp_r_pos[:2] + clamp_l_pos[:2])
            held_i = int(np.argmin(np.linalg.norm(cable_pos[:, :2] - mid_xy, axis=1)))
            obs_np[w, rc.OBS_HELD_CABLE_Z] = float(cable_pos[held_i, 2])
            # [49] seated-seg distance (phase-active clip, base-scripted phase_id pin).
            active_xy = self._active_clip_xy(ph)
            dx_a, z_cross_a = self._seat_metrics(cable_pos, active_xy)  # interp seat (dx, z_cross) -- rd2 fix
            zgap_a = z_cross_a - rc.ROUTE_GROOVE_Z
            obs_np[w, rc.OBS_SEATED_SEG_D] = float(np.hypot(dx_a, zgap_a))  # combined interp seat distance
            # [50] within-phase progress.
            obs_np[w, rc.OBS_WITHIN_PHASE] = float(self._route_within[w])
            # [51:53] next-clip xy (C2 for the C1->C2 route; per-phase next-clip map = N-clip forward-compat).
            obs_np[w, 51:53] = _C2_XY
            # [53:55] per-arm contact flag (geometric proxy: nearest-cable proximity and grip-close).
            r_near = float(np.min(np.linalg.norm(cable_pos - clamp_r_pos, axis=1)))
            l_near = float(np.min(np.linalg.norm(cable_pos - clamp_l_pos, axis=1)))
            obs_np[w, rc.OBS_R_CONTACT] = float(r_near < self.CONTACT_PROXIMITY_M and self._route_grip[w, 0] >= 0.5)
            obs_np[w, rc.OBS_L_CONTACT] = float(l_near < self.CONTACT_PROXIMITY_M and self._route_grip[w, 1] >= 0.5)
            # [55:57] per-arm IK residual (from the last action apply).
            obs_np[w, rc.OBS_R_IK_RESID] = self._last_ik_resid[w, 0]
            obs_np[w, rc.OBS_L_IK_RESID] = self._last_ik_resid[w, 1]
            # [57] crossing-x deviation (sensing ONLY -- the sole _crossing_x_dev consumer; the post-G3
            # escape guard reads the identity-restricted dx instead, I3). Pre-seat, not reaching C1Y is
            # normal; keep the finite observation contract by mapping None to zero.
            crossing_x_dev = self._crossing_x_dev(cable_pos)
            obs_np[w, rc.OBS_CROSSING_X_DEV] = 0.0 if crossing_x_dev is None else crossing_x_dev
            # [58:60] axis-resolved seat: [58] z-gap (z_cross - groove), [59] lateral = interp dx (rd2 fix).
            obs_np[w, rc.OBS_SEAT_ZGAP] = zgap_a
            obs_np[w, rc.OBS_SEAT_LATERAL] = dx_a
            # [60:62] C1-retention live inputs: now interp (dx_c1, z_cross_c1) -- rd2 fix (dim names kept; the
            #         retention predicate = _seated_in_groove(dx_c1, z_cross_c1), sec 8b).
            dx_c1_obs, z_cross_c1_obs = self._c1_retention_m(cable_pos)
            obs_np[w, rc.OBS_C1_REGION_Z] = dx_c1_obs
            obs_np[w, rc.OBS_C1_FLANK_MAX_Z] = z_cross_c1_obs

        np.nan_to_num(obs_np, copy=False, nan=0.0)
        return torch.from_numpy(obs_np).to(device=self.device)

    # =====================================================================================================
    # Reward / done (sparse-primary G1-G6, latched-monotonic, ORDERED gating)
    # =====================================================================================================

    def _compute_rewards_dones_batch(self):
        """G1-G6 latched reward + termination. Returns (rewards, dones, extras)."""
        wp.synchronize()
        bq = self._state_0.body_q.numpy()
        N = self._world_count
        rewards = np.zeros(N, dtype=np.float32)
        dones = np.zeros(N, dtype=np.int64)
        timeouts = np.zeros(N, dtype=np.int64)
        successes = np.zeros(N, dtype=np.float32)
        invalids = np.zeros(N, dtype=np.bool_)  # explosion -> PPO batch mask (LOUD-CARRY: stock RSL-RL has no field)
        drops = np.zeros(N, dtype=np.bool_)

        for w in range(N):
            ws = self._bws[w]
            ph = int(self._route_phase_id[w])
            clamp_r = clamp_pos_ko(bq[ws + _RIGHT_EE_BODY][:3], bq[ws + _RIGHT_EE_BODY][3:7])
            clamp_l = clamp_pos_ko(bq[ws + _LEFT_EE_BODY][:3], bq[ws + _LEFT_EE_BODY][3:7])
            cable_pos = bq[self._cable_bodies[w], :3]

            # --- live quantities ---
            r_near = float(np.min(np.linalg.norm(cable_pos - clamp_r, axis=1)))
            l_near = float(np.min(np.linalg.norm(cable_pos - clamp_l, axis=1)))
            grip_r, grip_l = self._route_grip[w, 0], self._route_grip[w, 1]
            contact_r = r_near < self.CONTACT_PROXIMITY_M and grip_r >= 0.5
            contact_l = l_near < self.CONTACT_PROXIMITY_M and grip_l >= 0.5
            span = float(np.linalg.norm(clamp_r[:2] - clamp_l[:2]))  # Y-plane EE-EE separation
            mid_xy = 0.5 * (clamp_r[:2] + clamp_l[:2])
            held_i = int(np.argmin(np.linalg.norm(cable_pos[:, :2] - mid_xy, axis=1)))
            held_z = float(cable_pos[held_i, 2])
            # Interp seat metrics (dx at exactly y=clip_y, z_cross) -- reward-design 2 fix.
            dx_c1, z_cross_c1 = self._seat_metrics(cable_pos, _C1_XY)
            dx_c2, z_cross_c2 = self._seat_metrics(cable_pos, _C2_XY)
            c1_seated = self._seated_in_groove(dx_c1, z_cross_c1)
            c2_seated = self._seated_in_groove(dx_c2, z_cross_c2)
            # c1_retained := C1 still seated (interp-dx + z-band) -- supersedes the pre-fix z-only ceiling
            # (81/81 no-op, defect #2). Same interp as the frozen recount => DoD-9a preserved (ruling sec 8b/11).
            c1_retained = c1_seated
            c2_honest = c2_seated  # G6 C2-honest = interp seat predicate (auto-follows _seat_metrics, sec 11)
            lane_seg = self._lane_matched_target(cable_pos, ph, clamp_r, self._target_seg_indices_r[w])
            r_reach = float(np.linalg.norm(clamp_r - lane_seg))  # R reach to lane-matched target (G4 _at_88 proxy)

            # --- explosion (physics-fault invalid) ---
            explosion = (
                r_near > self.EXPLOSION_DIST_THRESH
                or l_near > self.EXPLOSION_DIST_THRESH
                or np.isnan(r_near)
                or np.isnan(l_near)
            )

            # --- drop (-10; held-z floor / debounced contact-loss / lateral escape). Only meaningful AFTER
            # grasp (G1 cage latched) -- before grasp there is nothing to drop. span/reach = INFORMATIVE. ---
            grip_active = grip_r >= 0.5 or grip_l >= 0.5
            grasped = bool(self._g_latched[w, 0])
            if grasped and grip_active and not (contact_r or contact_l):
                self._contact_loss_count[w] += 1
            else:
                self._contact_loss_count[w] = 0
            # I3: the escape guard reads the SAME identity-restricted measurement (:1600 dx_c1) that the
            # seat predicate consumed this step -- never the global crossing (obs-only).
            c1_escape = self._c1_escape_after_seat(dx_c1, self._g_latched[w, 2])
            dropped = bool(
                grasped
                and (
                    (self._g_latched[w, 1] and held_z < self._cable_z_rest + self.DROP_LIFT_MARGIN_M)
                    or (self._contact_loss_count[w] >= self.DROP_CONTACT_LOSS_DEBOUNCE)
                    or c1_escape
                )
            )
            # W1-B2 sec 9 tail (iv) (charter ERRATUM-3): past the SCHEDULED release the cable is let go on
            # purpose -- a "drop" there is a category error whose -10 inverts the incentive (fail-slow -7.6
            # < fail-fast -3.99: the longer you route, the worse). Suppress POST-release ONLY (pre-release
            # drop semantics byte-identical = S5 preserved, %9 condition); flag-gated (OFF = legacy).
            if (
                dropped
                and self._route_t_clock
                and self._route_release_step is not None
                and int(self.route_t[w].item()) >= self._route_release_step
            ):
                dropped = False
                self._suppressed_drop_count[w] += 1

            # --- span guard: dual-grip phase ONLY, INFORMATIVE tier (no terminate) ---
            span_ok = True
            if self._route_is_dual[w]:
                span_ok = abs(span - rc.HOLD_SPAN_ACHIEVED) <= rc.HOLD_SPAN_TOL_M  # informative-only

            # --- raw predicates p1..p6 (ORDERED latch applied below) ---
            p1 = (
                (grip_r >= 0.5 and grip_l >= 0.5)
                and (contact_r and contact_l)
                and (abs(span - rc.HOLD_SPAN_ACHIEVED) <= rc.HOLD_SPAN_TOL_M)
            )
            p2 = (held_z - self._cable_z_rest) >= self.LIFT_RISE_MIN_M
            p3 = c1_seated and (ph >= 2)  # C1-seat (interp dx<=3.5 and z in-band) and phase reached G3
            p4 = (r_reach <= self.REGRASP_REACH_TOL_M) and contact_r  # _at_88 and _R_grips proxy (in-scene lane)
            p5 = c2_seated  # C2-seat (interp)
            preds = [p1, p2, p3, p4, p5]

            # --- ordered, latched, fire-once phase bonuses (G1..G5) ---
            r_phase = 0.0
            for k in range(5):
                if self._g_latched[w, k]:
                    continue
                if k > 0 and not self._g_latched[w, k - 1]:
                    break  # ORDERED: G_k fires only if G_{k-1} latched
                if preds[k]:
                    self._g_latched[w, k] = True
                    r_phase += rc.G_PHASE_BONUS
                else:
                    break

            # --- G6 SUCCESS = strict_v2 full mirror (requires G5 latched; sustained K_ROUTE_SEAT) ---
            success = False
            if self._g_latched[w, 4]:
                g6_live = c2_honest and c1_retained and (not dropped) and span_ok
                self._g6_sustain[w] = self._g6_sustain[w] + 1 if g6_live else 0
                if self._g6_sustain[w] >= rc.K_ROUTE_SEAT and not self._g_latched[w, 5]:
                    self._g_latched[w, 5] = True
                    success = True

            # --- reward assembly (explosion/drop override to -10; else time + phase (+200 on success)) ---
            if explosion or dropped:
                r = rc.TERM_PENALTY
            else:
                r = rc.TIME_PENALTY + r_phase + (rc.G6_TASK_BONUS if success else 0.0)

            timeout = self.episode_length_buf[w].item() >= self.max_episode_length
            done = success or timeout or explosion or dropped
            rewards[w] = r
            dones[w] = int(done)
            # [!] TIMEOUTS PURITY (prohibited.md value_loss-105x history): timeout ONLY, with the
            # explosionandtimeout -> time_outs=False precedence (CC4-CH4).
            timeouts[w] = int(timeout and not success and not explosion and not dropped)
            successes[w] = float(success)
            invalids[w] = bool(explosion)
            drops[w] = bool(dropped)
            if done:
                self._episode_success_buf.append(float(success))

        if len(self._episode_success_buf) > 0:
            self._last_success_rate = float(np.mean(self._episode_success_buf))

        extras = {
            "observations": {},
            "time_outs": torch.tensor(timeouts, dtype=torch.long, device=self.device),
            # LOUD-CARRY: trainer wires invalid_mask (explosion) into the PPO batch mask (no stock field).
            "invalid_mask": torch.tensor(invalids, dtype=torch.bool, device=self.device),
            # (b') pushforward info (NEW-C): as-executed residual a' + projection mode (0=common,1=transit).
            "info": {
                "executed_residual": torch.tensor(
                    self._last_executed_residual, dtype=torch.float32, device=self.device
                ),
                "projection_mode": torch.tensor(self._last_projection_mode, dtype=torch.long, device=self.device),
                "phase_id": torch.tensor(self._route_phase_id, dtype=torch.long, device=self.device),
                "is_dual_grip": torch.tensor(self._route_is_dual, dtype=torch.bool, device=self.device),
            },
            "log": {
                "/episode/success": float(np.mean(successes)),
                "/metrics/episode_success_rate": self._last_success_rate,
                "/metrics/explosion_count": int(np.sum(invalids)),
                "/metrics/drop_count": int(np.sum(drops)),
                "/metrics/g_latched_mean": float(np.mean(self._g_latched.sum(axis=1))),
                "/reward/r_total": float(np.mean(rewards)),
            },
        }
        return (
            torch.tensor(rewards, dtype=torch.float32, device=self.device),
            torch.tensor(dones, dtype=torch.long, device=self.device),
            extras,
        )

    # =====================================================================================================
    # RSL-RL VecEnv interface
    # =====================================================================================================

    @property
    def num_obs(self):
        return rc.OBS_DIM  # 62

    def _wire_c1_pin_from_recording(self):
        """Derive the C1 routed seat identity and optional pin onset from the recording.

        Onset: the first frame the producer's own ``pin_active`` is set (B3a leg 6 measured the recorder/solver
        lag as exactly 0, so the frame transfers directly).

        Seat: the recording pins eq 27 on body 55. Those are indices into the PRODUCER's model, and transplanting
        an absolute body index into a different model is the B3-alpha mistake. What DOES transfer is the
        CABLE-RELATIVE segment index -- both models build the same 40-body cable -- so the seat is derived as
        (pin_eqid - first_pin_eq) and applied to THIS env's own ``_cable_bodies``. B3a measured the eq table to
        be contiguous and +1-monotone in body id, which is what licenses that derivation; the eq itself is then
        re-resolved by WORLD POSITION at activation, never by index.
        """
        self._pin_onset_frame = None
        self._pin_seat_seg = None
        self._route_rec_step_f = None
        rec = self._route._recording
        pin_keys = ("pin_active", "pin_eqid", "pinned_body")
        missing = [key for key in pin_keys if key not in rec]
        if missing:
            if self._route_c1_pin:
                raise ValueError(f"route_c1_pin=True but prepared recording dropped pin witness fields {missing}")
            return  # non-pin route without identity: seat predicates remain conservatively fail-closed
        self._route_rec_step_f = np.asarray(rec["step_f"]).ravel()
        pin = np.asarray(rec["pin_active"]).ravel()
        on = np.nonzero(pin > 0)[0]
        if on.size == 0:
            if self._route_c1_pin:
                raise ValueError("route_c1_pin=True but the recording never pinned -- there is no onset to replay")
            return
        if self._route_c1_pin:
            self._pin_onset_frame = int(on[0])
        eqid = np.unique(np.asarray(rec["pin_eqid"]).ravel()[pin > 0])
        body = np.unique(np.asarray(rec["pinned_body"]).ravel()[pin > 0])
        if eqid.size != 1 or body.size != 1:
            raise ValueError(f"recording pins more than one eq/body (eq={eqid.tolist()}, body={body.tolist()})")
        # cable-relative seat: the 40 pin eqs are one per cable body, contiguous and in order (B3a, measured),
        # so the eq's ordinal IS the segment ordinal. Cross-check it against the body numbering before trusting it.
        seat_seg = int(eqid[0])
        n_cable = len(self._cable_bodies[0])
        if not 0 <= seat_seg < n_cable:
            raise ValueError(f"derived seat segment {seat_seg} outside this env's cable (0..{n_cable - 1})")
        self._pin_seat_seg = seat_seg
        if self._route_c1_pin:
            print(
                f"[NewtonRouteEnv] (d2) C1 pin armed: onset frame {self._pin_onset_frame}, seat segment {seat_seg} "
                f"(producer eq {int(eqid[0])} / body {int(body[0])}; resolved in THIS env's body space at activation)"
            )

    def _maybe_activate_c1_pin(self, route_steps, sub_i):
        """(d-a) Fire the C1 clip-retention pin when the identity cable body DWELLS in a route clip's capture
        volume AT DEPTH for K consecutive physics frames -- a LIVE geometric trigger. No-op unless route_c1_pin.

        This REPLACES the (a)(b) recorded-onset replay (charter sec 8.4-1 condition substitution; prereg
        PIN_D_TRIGGER v0.6). The (a)(b) form fired at the recording's own ``pin_active`` onset, which asks whether
        the producer's pin -- driven the producer's way -- changes the outcome. This form asks the (d) question:
        can a LIVE geometric rule (one a policy could later drive) fire the same authorized pin. It fires only when
        BOTH (i) the identity seat body is inside some authorized clip's capture volume (``clip_capture_check``, the
        SAME predicate + cache the authorizer uses -- containment-by-identity, sec 8.10.2) AND (ii) that body has
        descended to ``z <= Z_FIRE_DEPTH_M`` (sec 8.11.2: a rim-height fire elastic-restores out of the groove),
        for K consecutive physics frames (``PIN_TRIGGER_DWELL_K``; a single gap resets the dwell).

        The identity seat is recording-derived (``_pin_seat_seg``; sec 8.1 (B)) and its world position is read ONCE
        per frame -- that single snapshot is passed to BOTH the capture check and the authorizer, so a fire-True is
        an authorizer-accept by construction (sec 2-6a same-snapshot). The pin welds through the clip-only
        authorizer :func:`route_executor.authorize_clip_pin`, which permits an eq ONLY at an authorized clip seat
        (RS71 §0 INVARIANT #5, Rs 2026-07-15). ``clip_capture_check`` is non-raising (an out-of-volume seat quietly
        resets the dwell); only a broken selector or a missing CPU model raises (fail-loud, sec 2-6 / sec 8.10.4).
        """
        if not self._route_c1_pin or self._c1_pin_witness is not None or self._pin_seat_seg is None:
            return  # identity None (a non-pin recording) = fail-closed, no evaluation (sec 2-7)
        import route_executor as rex  # lazy, mirroring _build_route_executor's idiom (path set there)

        step_f = self._route_rec_step_f
        t = min(max(int(route_steps[0]), 0), len(step_f) - 1)
        bq = self._state_0.body_q.numpy()
        seat_body = int(self._cable_bodies[0][int(self._pin_seat_seg)])  # identity body only (sec 2-3)
        seat_world = bq[seat_body, :3].copy()  # single snapshot (sec 2-6a): check AND authorizer read THIS value
        captured = rex.clip_capture_check(self._solver, seat_world)
        if not (captured and float(seat_world[2]) <= rc.Z_FIRE_DEPTH_M):  # fire = capture AND depth (sec 8.11.2)
            self._c1_pin_dwell = 0  # strict consecutive: any gap (capture OR depth False) resets the dwell
            return
        self._c1_pin_dwell += 1
        if self._c1_pin_dwell < rc.PIN_TRIGGER_DWELL_K:  # K = 3 physics frames (sec 8.10.1)
            return
        self._c1_pin_witness = rex.authorize_clip_pin(self._solver, seat_body, seat_world)  # same snapshot
        self._c1_pin_witness["fired_at_frame"] = int(step_f[t]) + int(sub_i)
        self._c1_pin_witness["fire_step"] = int(self.episode_length_buf[0].item())  # episode-relative (sec 2-D)
        self._c1_pin_witness["dwell_count"] = int(self._c1_pin_dwell)

    def _clear_c1_pin(self, env_ids):
        """Clear every fired clip pin and the episode witness on a world-0 reset ((a)(b) lifecycle).

        Model-state authority (prereg v0.3.1 sec 4): the clear set is ALL fired pin candidates returned
        by the design sec 15.4 audit's who-wrote-it-agnostic scan -- NOT the witness eq alone -- so a
        bypass write (an ``eq_active`` flipped without the authorizer) is audited-then-cleared on EVERY
        reset path (done-driven and public :meth:`reset`). The audit-then-clear order is load-bearing:
        the clear destroys the episode's weld evidence. Identity (``_pin_seat_seg`` /
        ``_pin_onset_frame`` / ``_route_rec_step_f``) is recording-derived and NEVER cleared here
        (design sec 21.11.1 coupling note: the escape guard reads identity, not witness).
        """
        if 0 not in env_ids:
            # pin is world-0-only: a reset not touching world 0 is out of this helper's scope
            # (CPU x wc>1 whole-config loudness is owned by the make_solver tripwire, base:1324).
            return
        if int(self._world_count) != 1:
            # env-authoritative count: the solver object exposes no world_count attribute, so a
            # getattr default would be fail-open. CPU eq writes are GPU-inert at wc>1 (banked
            # hypothesis 2026-07-16) -- the readback below would confirm the MIRROR, not physics.
            raise RuntimeError(f"clip-pin lifecycle requires world_count==1 (CPU path); got {self._world_count}")
        import route_executor as rex  # lazy, path set in _build_route_executor (mirrors :1930)

        mjm = getattr(self._solver, "mj_model", None)
        if mjm is None:
            return  # no CPU eq table -> no pin can exist (mirrors the done-path guard)
        mjd = self._solver.mj_data
        fired = rex.audit_pin_anchors(mjm, mjd)  # raises on count/anchor violation BEFORE any clear
        # (d-a) sec 8.2: classify the witness<->fired mismatch (bypass / divergence / concurrent) and snapshot the
        # per-episode record BEFORE the clear destroys the weld. LOUD + counted; NEVER wired to reward/term/invalid.
        mismatch_class = self._pin_mismatch_class(fired)
        if mismatch_class != 0:
            self._pin_mismatch_total += 1
            w_eq = None if self._c1_pin_witness is None else self._c1_pin_witness.get("eq_id")
            print(
                f"[NewtonRouteEnv] (d-a) PIN MISMATCH class {mismatch_class}: fired={list(fired)} "
                f"witness_eq={w_eq} total={self._pin_mismatch_total} (LOUD; not wired to reward)",
                flush=True,
            )
        self._last_pin_record = self._snapshot_pin_record(fired, mismatch_class)
        if fired:
            # NO-KINEMATIC (c6): firing is REMOVED, so an ACTIVE pin eq at the episode boundary can
            # only mean a surviving kinematic writer upstream -- raise, never silently disarm (a
            # clean-up write would itself be the last eq_active writer in envs/ and would mask the
            # upstream violation).
            raise RuntimeError(
                f"clip-pin eq ACTIVE at the episode boundary: {sorted(int(e) for e in fired)} -- pin "
                "firing is REMOVED (Rs directive 2026-07-19 kinematic complete-removal); an active eq "
                "means a kinematic writer survives somewhere upstream"
            )
        self._c1_pin_witness = None  # pin FIRING is removed (Rs 2026-07-19); this clear is defense-in-depth
        self._c1_pin_dwell = 0  # (d-a): re-arm the dwell counter for the next episode

    def _sentinel_pin_record(self):
        """The (d-a) sec 2-D per-episode pin record for a window with NO reset (budget cutoff) -- the "no reset"
        sentinel: ``pin_mismatch_class`` / ``pin_audit_verdict_at_reset`` are -1 and the fire fields are -1 / NaN.
        The identity ordinal is still reported when the episode was armed (a per-episode constant), else -1. The
        collector writes THIS for an in-flight (budget-cut) window whose pin state is deliberately not closed
        (window<->episode 1:1, the record travels with done); a done window overwrites it via
        :meth:`_snapshot_pin_record`.
        """
        seat_seg = getattr(self, "_pin_seat_seg", None)
        return {
            "pin_fire_step": -1,
            "pin_fire_frame": -1,
            "pin_eq_id": -1,
            "pin_seat_seg": -1 if seat_seg is None else int(seat_seg),
            "pin_anchor_xyz": (float("nan"), float("nan"), float("nan")),
            "pin_dwell_count_at_fire": -1,
            "pin_mismatch_class": -1,
            "pin_audit_verdict_at_reset": -1,
        }

    def _snapshot_pin_record(self, fired, mismatch_class):
        """The (d-a) sec 2-D per-episode pin record captured at reset, BEFORE the clear destroys the weld evidence.

        A done window carries this: real values when the pin fired this episode, and the "no fire" sentinel (fire
        fields -1 / NaN) when it did not. ``pin_audit_verdict_at_reset`` is 1 when a fired pin eq was audited and 0
        when the audit passed with none -- distinguishing a done-no-fire window (0) from a budget-cut window (-1).

        Args:
            fired: the audited fired-eq tuple from :func:`route_executor.audit_pin_anchors`.
            mismatch_class: the sec 8.2 witness<->fired class (0 none / 1 bypass / 2 divergence / 3 concurrent).
        """
        w = self._c1_pin_witness
        seat_seg = getattr(self, "_pin_seat_seg", None)
        anchor = w["seat_world"] if w is not None else None
        return {
            "pin_fire_step": int(w["fire_step"]) if w is not None else -1,
            "pin_fire_frame": int(w["fired_at_frame"]) if w is not None else -1,
            "pin_eq_id": int(w["eq_id"]) if w is not None else -1,
            "pin_seat_seg": -1 if seat_seg is None else int(seat_seg),
            "pin_anchor_xyz": (
                (float(anchor[0]), float(anchor[1]), float(anchor[2]))
                if anchor is not None
                else (float("nan"), float("nan"), float("nan"))
            ),
            "pin_dwell_count_at_fire": int(w["dwell_count"]) if w is not None else -1,
            "pin_mismatch_class": int(mismatch_class),
            "pin_audit_verdict_at_reset": 1 if len(fired) > 0 else 0,
        }

    def _pin_mismatch_class(self, fired):
        """Classify the witness<->fired mismatch at reset (sec 8.2). 0 = none (agreement, or both empty).

        * 1 (bypass): an eq fired but no authorizer witness recorded it (``fired`` non-empty, witness None) -- an
          ``eq_active`` flipped outside :func:`route_executor.authorize_clip_pin`.
        * 2 (divergence): a witness exists but its eq is NOT among the fired set (the weld vanished or moved).
        * 3 (concurrent): the witness eq IS fired but more than one pin fired (a bypass ran alongside the pin).

        LOUD only -- the caller prints and counts; nothing here is wired to reward, termination, or invalid.

        Args:
            fired: the audited fired-eq tuple from :func:`route_executor.audit_pin_anchors`.
        """
        w = self._c1_pin_witness
        if w is None:
            return 1 if len(fired) > 0 else 0
        if int(w["eq_id"]) not in fired:
            return 2
        return 3 if len(fired) > 1 else 0

    def _pull_route(self):
        """Query the route interface for all worlds (per-step ABSOLUTE base target + phase + grip + dual
        gate). within-phase progress [50] is derived env-side from phase-entry tracking (route-agnostic:
        the 4-tuple contract does not carry it), normalized by a nominal equal-split phase length.
        """
        N = self._world_count
        route_targets = np.zeros((N, 6), dtype=np.float32)
        nominal_phase_len = max(self.MAX_EPISODE_STEPS / rc.N_ROUTE_PHASES, 1.0)
        for w in range(N):
            t = int(self.route_t[w].item())  # W1-B1: route clock (consumer 1); == episode clock while mirrored
            if self._route_t_clock:
                # W1-B2: the oracle query (READ-ONLY -- fire/resume live in the post-physics update_sync,
                # conformance R3m/R5d). Under MARCH the packet is value-identical to step_target; under
                # HOLD the grip-derived fields evaluate at the frozen chunk-END frame (sec 4.2 N3).
                target_6d, phase_id, grip_2, is_dual, _validity, _sync = self._route.query(
                    int(self.episode_length_buf[w].item()), w, {"route_t": t}
                )
            else:
                target_6d, phase_id, grip_2, is_dual = self._route.step_target(t)
            route_targets[w] = target_6d
            if phase_id != int(self._prev_phase_id[w]):
                self._phase_entry_step[w] = t
                self._prev_phase_id[w] = phase_id
            self._route_phase_id[w] = phase_id
            self._route_within[w] = float(np.clip((t - self._phase_entry_step[w]) / nominal_phase_len, 0.0, 1.0))
            self._route_grip[w] = grip_2
            self._route_is_dual[w] = is_dual
        return route_targets

    def _update_route_sync(self):
        """W1-B2: post-physics HOLD sync update (the conformance R3m evaluation point).

        Reads the post-physics cable state (``_apply_actions_batch`` ends with ``wp.synchronize()``) and
        the G1 latch as of the PREVIOUS reward pass (a 1-step arming lag with no bar sensitivity: latch
        ~t100 vs onset t343), and delegates the fire/resume decision to the oracle's single sync-mutation
        site. Returns the per-world hold mask the increment site applies.
        """
        bq = self._state_0.body_q.numpy()
        views = [bq[self._cable_bodies[w], :3] for w in range(self._world_count)]
        route_ts = [int(self.route_t[w].item()) for w in range(self._world_count)]
        return self._route.update_sync(route_ts, views, self._g_latched[:, 0])

    def get_observations(self) -> tuple[torch.Tensor, dict]:
        obs = self._compute_obs_batch()
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)
        return obs, {"observations": {}}

    def reset(self) -> tuple[torch.Tensor, dict]:
        self._reset_worlds(list(range(self._world_count)))
        self.episode_length_buf[:] = 0
        self.route_t[:] = 0  # W1-B1 mirror (global reset site)
        self._route.reset_to_phase(0)  # STUB: no-op record (real = state-bank fork, LOUD-CARRY)
        self._pull_route()
        return self.get_observations()

    def step(self, actions: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]:
        actions = torch.nan_to_num(actions, nan=0.0, posinf=0.0, neginf=0.0).clamp(-1.0, 1.0)
        route_targets = self._pull_route()  # base ABSOLUTE targets + phase/grip/dual for THIS step
        self._apply_actions_batch(actions, route_targets)
        self.episode_length_buf += 1
        # W1-B1 mirror increment / W1-B2 HOLD freeze mask (conformance R3m/R4a): under the flag the sync
        # decision runs HERE -- post-physics (wp.synchronize'd inside _apply_actions_batch), PRE-increment,
        # at the PRE-increment route_t: the chunk just driven, whose chunk-END comparison frame is exactly
        # where the env state now sits (spec sec 4.2 N4 alignment; a top-of-step evaluation would compare
        # the WRONG chunk). Held worlds skip the increment (= freeze; next step re-holds the chunk end);
        # the episode clock above ALWAYS advances (spec sec 4.1: time-penalty / horizon / timeout).
        if self._route_t_clock:
            self._hold_mask_np = self._update_route_sync()
            self.route_t += torch.from_numpy((~self._hold_mask_np).astype(np.int64)).to(self.route_t.device)
        else:
            self.route_t += 1
        self._total_env_steps += self._world_count

        rewards, dones, extras = self._compute_rewards_dones_batch()
        rewards = torch.nan_to_num(rewards, nan=-10.0, posinf=0.0, neginf=-10.0)

        done_ids = dones.nonzero(as_tuple=False).squeeze(-1)
        if len(done_ids) > 0:
            if self._route_c1_pin:
                # §15.4 episode-end invariant: every fired clip pin must anchor inside an authorized route clip.
                # Runs BEFORE _reset_worlds (which may clear eq_active). Who-wrote-it-agnostic -> catches a
                # bypass write / aerial weld regardless of caller. No-op (empty scan) when no pin has fired.
                import route_executor as rex  # lazy, path set in _build_route_executor (mirrors :1717)

                _pin_solver = self._solver
                if getattr(_pin_solver, "mj_model", None) is not None:
                    rex.audit_pin_anchors(_pin_solver.mj_model, _pin_solver.mj_data)
            self._reset_worlds(done_ids.cpu().tolist())
            # W1-B1 consumer 6 (Stage-A sec 4.1 H6): per-world re-fork on done-reset. k=0 = env-authoritative
            # reset = structural no-op today (stub records only; RouteExecutor early-returns on k==0);
            # the curriculum start-mix (k>0 per world) lands at B4. Placed AFTER _reset_worlds (restore-
            # after-reseed order; reseed_grip_open runs inside _reset_worlds -- B4 ordering dependency).
            self._route.reset_to_phase(0, world_ids=done_ids.cpu().tolist())

        obs = self._compute_obs_batch()
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)
        return obs, rewards, dones, extras

    def close(self):
        pass
