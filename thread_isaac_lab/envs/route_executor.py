# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Route-executor: faithful extraction of the locked C1->C2 route engine (charter D-1=C).

This module extracts the canonical route logic from the Rs-LOCKED monolith
``test_newton_clip_routing.py::_run_mujoco_grasp_route`` (:3692, the 0.716 MOTION
STANDARD) into a reusable ``RouteExecutor`` so ``NewtonRouteEnv`` drives the real
route instead of ``NominalRouteStub``. Faithfulness is guarded empirically by a
byte-repro regression harness (``test_routeexec_byte_repro.py``): the extracted
route must reproduce the locked runner byte-identically over the canonical 81-grid
(cuda:0 canonical only -- the route is device-fragile).

Build spec: ``eval_runs/troot_optE_dapg_wholeroute_scope_20260701/BUILD_PLAN_ROUTEEXEC_COORD_20260707.md``
(v1.8, sections referenced inline below).

Grip mechanism (v1.6 flag-flip / v1.8 §13): the gripper is a genuine model-level
POSITION servo + 4-bar equality (built by ``build_multiworld_scene(grasp_actuation=True)``);
it is NOT kinematically pinned. The load-bearing correctness property is that the
gripper coordinates are EXCLUDED from every kinematic ``joint_q``/``joint_qd`` write
(so the servo drives them) AND are RESTORED to their banked grip state at reset --
both derived from ONE source set (``_GRIPPER_COORDS_LOCAL``, §13.0-2 / §13.4 / §13.7 G7).

This foundation reuses the L3-landed proven wiring from
``newton_aerial_regrasp_mujoco_env.py`` (§13.1 F10): the programmatic exclusion map,
the per-world driver DOFs, the vectorized arm-only re-pose maps, the fail-loud
servo-seed assert, and ``_set_gripper_target``. The AR-specific LEFT-arm freeze
(AR:1570, aerial-hold-only) is deliberately NOT reused -- route is active dual-arm
(§13.2 G3; both arms IK-tracked, adapted from the locked monolith choreography).
"""

import math as _math
import os

import mujoco
import newton
import numpy as np
import route_env_config as rc
import warp as wp
from configs.task_config import (
    ARM_DOF,
    CABLE_RADIUS,
    CLIP1_Z,
    CLIP_POSITIONS,
    EE_BODY_OFFSET,
    FRANKA_NUM_JOINTS,
    GRASP_X,
    GRIP_HALF_SPAN,
    GRIPPER_DRIVER_CLOSE_RAD,
    GRIPPER_DRIVER_JOINT_IDX,
    GRIPPER_DRIVER_OPEN_RAD,
    GRIPPER_JOINT_RANGE,
    JOINTS_PER_ARM,
    MAX_MOVE_STEPS,
    ROBOT_LEFT_BASE,
    ROBOT_RIGHT_BASE,
    SIM_SUBSTEPS,
    STEPS_PER_CM,
    WIDE_LEFT_Y,
    WIDE_RIGHT_Y,
)
from newton.ik import IKObjectiveJointLimit, IKObjectivePosition, IKObjectiveRotation, IKSolver

# =============================================================================
# §13.0-2 / §13.4 / §13.7 (G7) -- SINGLE SSOT for the gripper coordinate set.
# BOTH the write-site exclusion (§13.1) AND the reset restore (§13.4) are co-derived
# from this one set. Their historical divergence was the F1(exclusion)->G7(restore)
# recurrence source; a single source eradicates it. Any coordinate missed here shows
# up empirically as a byte-repro re-pin failure (§13.0-3, the empirical guard).
# Mirrors newton_aerial_regrasp_mujoco_env.py:200-201 (SSOT test:1622-28).
# =============================================================================
_N_ARM_JOINTS = 2 * JOINTS_PER_ARM  # 28 (per-arm 14 = arm{0-5} + gripper{6-13}, x2 arms)
_GRIPPER_COORDS_LOCAL = set(GRIPPER_JOINT_RANGE) | {JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE}  # {6-13,20-27}
_ARM_OVERWRITE_LOCAL = [i for i in range(_N_ARM_JOINTS) if i not in _GRIPPER_COORDS_LOCAL]  # {0-5,14-19}
_L_DRIVER_LOCAL = list(GRIPPER_DRIVER_JOINT_IDX)  # [6, 10] driver DOFs within the LEFT arm
_R_DRIVER_LOCAL = [JOINTS_PER_ARM + j for j in GRIPPER_DRIVER_JOINT_IDX]  # [20, 24] driver DOFs (RIGHT arm)

# §13.5 (G4/G5) invariant numeric constants.
_GHS = float(GRIP_HALF_SPAN)  # 0.044: R lane = c2y + GHS, L lane = c2y - GHS
_SPAN_NOMINAL_M = 0.088  # FOUNDATIONAL 88mm two-EE grasp span (RS71-System-Spec-SSOT.md:24, §0 #2)


def assert_span_invariant(c2y: float) -> tuple[float, float]:
    """Invariant-specific anti-revert check for the 88mm span (§13.5 G5).

    This is a NUMERIC pin, not a generic AST/string-equal check: it catches an
    off-grid ``GRIP_HALF_SPAN`` revert (e.g. 0.044 -> 0.030 = 60mm; a 60mm backup
    exists on-disk at ``task_config.py.pre_3c_backup:121``) that on-grid byte-repro
    alone cannot see. Both the R (c2y+GHS) and L (c2y-GHS) endpoints are pinned.

    Args:
        c2y: The clip-2 grasp-centre Y coordinate [m].

    Returns:
        The (R, L) target-lane Y coordinates ``(c2y + GHS, c2y - GHS)`` [m].
    """
    assert abs(2.0 * _GHS - _SPAN_NOMINAL_M) < 1e-9, (
        f"INVARIANT#2 (FOUNDATIONAL 88mm span) broken: 2*GRIP_HALF_SPAN={2.0 * _GHS} != {_SPAN_NOMINAL_M} "
        f"(off-grid revert; see RS71 §0 #2 -- Rs premise, STOP)"
    )
    r_ty = c2y + _GHS
    l_ty = c2y - _GHS
    assert abs((r_ty - l_ty) - _SPAN_NOMINAL_M) < 1e-9, f"span L<->R = {(r_ty - l_ty) * 1e3:.3f}mm != 88mm"
    return r_ty, l_ty


def compute_c2_regrasp_target(cbq: np.ndarray, c2y: float) -> tuple[tuple[float, float, float], int, float]:
    """Compute the C2 re-grasp RIGHT-arm target (§13.5 G4; faithful to monolith test:5127-5137).

    Anti-revert (Rs-LOCKED 2026-07-01): the target X FOLLOWS the actual cable bow X at the
    picked body -- it is NOT a fixed geometric ``c2x`` (a fixed target = the air-grip
    "R not re-grasping" bug). Y is HELD at ``c2y + GHS`` (88mm span, INVARIANT#2).

    Args:
        cbq: Cable-body poses ``state.body_q[cable_bodies]`` [m], shape ``[n_body, 7]``.
        c2y: The clip-2 grasp-centre Y coordinate [m].

    Returns:
        A tuple ``(target, k_r, picked_dy_mm)`` where ``target`` is the RIGHT-arm
        ``(x, y, z)`` [m] (x = bow-follow, y = 88mm lane, z = picked body Z), ``k_r`` is
        the picked cable-body index, and ``picked_dy_mm`` is the picked body's Y offset
        from the 88mm lane [mm] (G9 tolerance metric).
    """
    r_ty = c2y + _GHS  # (a1) HOLD Y = 88mm span (span-preserving, INVARIANT#2)
    k_r = int(np.argmin(np.abs(cbq[:, 1] - r_ty)))  # (a1) picker: cable body nearest R's +Y grip lane
    bow_x, bow_z = float(cbq[k_r, 0]), float(cbq[k_r, 2])  # (a2) FOLLOW actual cable X (bow) + Z, NOT fixed c2x
    picked_dy_mm = float(cbq[k_r, 1] - r_ty) * 1e3  # G9: how far the picked body's Y is from the lane
    return (bow_x, r_ty, bow_z), k_r, picked_dy_mm


# =============================================================================
# §13.1 (F10 / G1) -- AR-reuse arm-only write-site machinery (3 patterns).
# Every kinematic joint_q/joint_qd write during the dynamic-gripper window MUST route
# through one of these, so the gripper coords ``_GRIPPER_COORDS_LOCAL`` are left to the
# POSITION servo (never re-pinned). The index arrays (``arm_ow_q_idx`` etc.) are built
# once per world in ``RouteExecutor.__init__`` from ``_ARM_OVERWRITE_LOCAL`` and the
# per-world coord starts (cable FREE root => q-start != qd-start for world>=1).
# Verbatim reuse of newton_aerial_regrasp_mujoco_env.py:472-489 / :1575-1576, EXCEPT the
# AR LEFT-arm freeze (AR:1570, aerial-hold-only) is NOT reused -- route is dual-arm (§13.2 G3).
# =============================================================================
def apply_arm_only_write_broadcast(phys_jq, phys_jqd, fk_jq_1world, arm_ow_q_idx, arm_ow_qd_idx, arm_ow_src):
    """Broadcast ONE FK arm pose to all worlds, excluding gripper coords (§13.1 :387; AR:472-478).

    Used by the setup/hold path (``_broadcast_arm_jointq``): a single-world ``fk_jq`` is
    written to every world's arm coords via ``arm_ow_src`` (= ``_ARM_OVERWRITE_LOCAL`` tiled
    per world). The gripper coords ``_GRIPPER_COORDS_LOCAL`` are never indexed, so the servo
    keeps driving them. ``phys_jq``/``phys_jqd`` are host copies (``.numpy()``); the caller
    ``.assign()``s them back.

    Args:
        phys_jq: Physics joint positions [m or rad], shape ``[total_q]``, mutated in place.
        phys_jqd: Physics joint velocities [m/s or rad/s], shape ``[total_qd]``, mutated in place.
        fk_jq_1world: One world's FK arm joint positions [m or rad], shape ``[_N_ARM_JOINTS]``.
        arm_ow_q_idx: Destination q indices for arm coords across all worlds, int array.
        arm_ow_qd_idx: Destination qd indices for arm coords across all worlds, int array.
        arm_ow_src: Source indices into ``fk_jq_1world`` (``_ARM_OVERWRITE_LOCAL`` tiled), int array.

    Returns:
        The mutated ``(phys_jq, phys_jqd)`` tuple.
    """
    phys_jq[arm_ow_q_idx] = fk_jq_1world[arm_ow_src]
    phys_jqd[arm_ow_qd_idx] = 0.0
    return phys_jq, phys_jqd


def apply_arm_only_write_perworld(phys_jq, phys_jqd, jq_interp, arm_ow_q_idx, arm_ow_qd_idx):
    """Write per-world arm targets, excluding gripper coords (§13.1 :738 RL-drive; AR:1575-1576).

    Used by the per-step drive path (``_apply_actions_batch``): ``jq_interp`` holds a distinct
    arm pose per world, so the arm coords are taken as ``jq_interp[:, _ARM_OVERWRITE_LOCAL]``
    (world-major, aligned with ``arm_ow_q_idx``). The gripper coords are never indexed. NO
    LEFT-arm freeze (route is dual-arm, both arms IK-tracked; §13.2 G3).

    Args:
        phys_jq: Physics joint positions [m or rad], shape ``[total_q]``, mutated in place.
        phys_jqd: Physics joint velocities [m/s or rad/s], shape ``[total_qd]``, mutated in place.
        jq_interp: Per-world interpolated arm targets [m or rad], shape ``[n_world, _N_ARM_JOINTS]``.
        arm_ow_q_idx: Destination q indices for arm coords across all worlds, int array.
        arm_ow_qd_idx: Destination qd indices for arm coords across all worlds, int array.

    Returns:
        The mutated ``(phys_jq, phys_jqd)`` tuple.
    """
    phys_jq[arm_ow_q_idx] = jq_interp[:, _ARM_OVERWRITE_LOCAL].reshape(-1)
    phys_jqd[arm_ow_qd_idx] = 0.0
    return phys_jq, phys_jqd


def set_gripper_target(joint_target_pos, dofs, target_rad):
    """Schedule the gripper POSITION-servo target on ``dofs`` (§13.1 grip cadence; AR:480-489).

    ``dofs`` are qd-indexed driver DOFs (per-world ``_arm_qd_start[w] + [6,10,20,24]``). The
    array is read by SolverMuJoCo each step, so a runtime change takes effect. This is the
    SOLE writer of ``joint_target_pos`` for the gripper (§13.6 G12 single-writer).

    Args:
        joint_target_pos: Servo target array [rad], mutated in place.
        dofs: Driver DOF indices to set, iterable of int.
        target_rad: The commanded driver target [rad].

    Returns:
        The mutated ``joint_target_pos``.
    """
    for d in dofs:
        joint_target_pos[d] = float(target_rad)
    return joint_target_pos


def build_perworld_index_maps(arm_q_start, arm_qd_start):
    """Build per-world arm-only re-pose maps + driver DOFs + gripper restore set (§13.1/§13.4; AR:421-433).

    The cable FREE root makes the per-world ``joint_q`` start differ from the ``joint_qd`` start for
    world >= 1, so the arm (q-indexed) re-pose and the driver (qd-indexed) targets are threaded
    separately. The gripper RESTORE index set is derived from the SAME ``_GRIPPER_COORDS_LOCAL`` as the
    write-site EXCLUSION (§13.0-2 / G7): the arm and gripper sets are complements over each world's
    ``_N_ARM_JOINTS`` span, so no coordinate can be excluded-from-writes yet not restored-at-reset.

    Args:
        arm_q_start: Per-world arm ``joint_q`` start indices, list[int] of length ``n_world``.
        arm_qd_start: Per-world arm ``joint_qd`` start indices, list[int] of length ``n_world``.

    Returns:
        A dict with ``arm_ow_q_idx``/``arm_ow_qd_idx`` (destination indices for the arm-only re-pose),
        ``arm_ow_src`` (source into a per-world arm row = ``_ARM_OVERWRITE_LOCAL`` tiled), ``l_driver_dofs``/
        ``r_driver_dofs``/``all_driver_dofs`` (per-world qd driver indices), and ``gripper_restore_q_idx``
        (the all-16 gripper ``joint_q`` coords per world, for the banked reset restore).
    """
    n_world = len(arm_q_start)
    grip_local = sorted(_GRIPPER_COORDS_LOCAL)
    return {
        "arm_ow_q_idx": np.array(
            [arm_q_start[w] + li for w in range(n_world) for li in _ARM_OVERWRITE_LOCAL], dtype=np.int64
        ),
        "arm_ow_qd_idx": np.array(
            [arm_qd_start[w] + li for w in range(n_world) for li in _ARM_OVERWRITE_LOCAL], dtype=np.int64
        ),
        "arm_ow_src": np.array(_ARM_OVERWRITE_LOCAL * n_world, dtype=np.int64),
        "l_driver_dofs": [[arm_qd_start[w] + d for d in _L_DRIVER_LOCAL] for w in range(n_world)],
        "r_driver_dofs": [[arm_qd_start[w] + d for d in _R_DRIVER_LOCAL] for w in range(n_world)],
        "all_driver_dofs": [arm_qd_start[w] + d for w in range(n_world) for d in _L_DRIVER_LOCAL + _R_DRIVER_LOCAL],
        "gripper_restore_q_idx": np.array(
            [arm_q_start[w] + gc for w in range(n_world) for gc in grip_local], dtype=np.int64
        ),
        "gripper_restore_qd_idx": np.array(
            [arm_qd_start[w] + gc for w in range(n_world) for gc in grip_local], dtype=np.int64
        ),
    }


def servo_seed_assert(joint_target_pos, all_driver_dofs):
    """Fail-loud servo-seed check: every driver DOF carries the build-time OPEN target (§13; AR:435-441).

    A wrong per-world qd offset would silently drive the wrong DOF, so the gripper never closes; this
    catches it at build time instead of as a hard-to-localize byte-repro miss.

    Args:
        joint_target_pos: The servo target array [rad] read from the built control.
        all_driver_dofs: Flat per-world driver DOF indices (from :func:`build_perworld_index_maps`).

    Raises:
        AssertionError: If any driver DOF's target is not the build-time ``GRIPPER_DRIVER_OPEN_RAD``.
    """
    for d in all_driver_dofs:
        assert abs(float(joint_target_pos[d]) - GRIPPER_DRIVER_OPEN_RAD) < 1e-6, (
            f"servo-seed: driver DOF {d} target={joint_target_pos[d]} != OPEN {GRIPPER_DRIVER_OPEN_RAD} "
            f"(per-world qd offset wrong)"
        )


def apply_banked_restore(phys_jq, phys_jqd, joint_target_pos, maps, banked):
    """Restore a banked phase-k state at reset: arm + ALL-16 gripper joint_q/qd + banked grip target (§13.3/§13.4).

    The reset-side counterpart to the write-site exclusion. The gripper coords restored here are the SAME
    ``_GRIPPER_COORDS_LOCAL`` set excluded from the per-step writes (both index maps come from
    :func:`build_perworld_index_maps`), so a gripped phase-k restores a CLOSED gripper -- NOT a blanket-OPEN,
    which would release the banked cable and fail the A2 handover-fidelity DoD (§13.3 F5, supersedes item7).

    Args:
        phys_jq: Physics joint positions [m or rad], mutated in place.
        phys_jqd: Physics joint velocities [m/s or rad/s], mutated in place.
        joint_target_pos: Servo target array [rad], mutated in place.
        maps: The dict from :func:`build_perworld_index_maps`.
        banked: Dict with ``arm_q``/``arm_qd`` (world-major over ``_ARM_OVERWRITE_LOCAL``), ``gripper_q``/
            ``gripper_qd`` (world-major over ``_GRIPPER_COORDS_LOCAL``), and ``grip_target`` (per driver DOF,
            world-major) -- the banked phase-k grip command (OPEN for phase-0, banked-CLOSED for G3-G6).

    Returns:
        The mutated ``(phys_jq, phys_jqd, joint_target_pos)`` tuple.
    """
    phys_jq[maps["arm_ow_q_idx"]] = banked["arm_q"]
    phys_jqd[maps["arm_ow_qd_idx"]] = banked["arm_qd"]
    phys_jq[maps["gripper_restore_q_idx"]] = banked["gripper_q"]  # G7: all 16 gripper coords (drivers + followers)
    phys_jqd[maps["gripper_restore_qd_idx"]] = banked["gripper_qd"]
    for i, d in enumerate(maps["all_driver_dofs"]):
        joint_target_pos[d] = float(banked["grip_target"][i])  # F5 banked grip target (NOT blanket-OPEN)
    return phys_jq, phys_jqd, joint_target_pos


# =============================================================================
# §13.7 -- Layer A single-world motion/IK substrate (self-contained verbatim copy).
# These module-level primitives are the substrate that the self-driving byte-repro path
# (``run_route``, subsequent chunk) calls. They are COPIED, not imported: importing
# ``test_newton_clip_routing.py`` would run its top-level (sys.path inserts, the ``DEVICE``
# env read, the :929 cable-stiffness assert) and couple to its mutable module globals.
# Copy faithfulness is guarded empirically by the 81-grid byte-repro (Layer A) plus the
# static two-copy drift tripwire on the IK stack (added with :func:`solve_ik_dual` / A2).
#
# Constant sourcing: SSOT-shared values (``SIM_SUBSTEPS``/``EE_BODY_OFFSET`` here;
# ``STEPS_PER_CM``/``MAX_MOVE_STEPS``/``FRANKA_NUM_JOINTS`` in A2) are imported from
# ``configs.task_config`` -- the SAME SSOT the monolith imports (test:59) -- so byte-identical
# by construction with no drift. Test-local physics constants (``DT``/``SIM_DT``; ``IK_*``/
# ``DEVICE`` in A2) are mirrored below with their source line; a value drift surfaces as a
# byte-repro miss (§13.0-3).
# =============================================================================
DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")  # test:122 (byte-repro pins NEWTON_DEVICE=cuda:0)
DT = 1.0 / 480.0  # test:123 frame dt (outer step)
SIM_DT = DT / SIM_SUBSTEPS  # test:124 solver dt (inner substep)
IK_ITERATIONS = 100  # test:237 Levenberg-Marquardt iterations per solve_ik_dual call
IK_STEP_SIZE = 1.0  # test:238 LM step size
_BOX = int(mujoco.mjtGeom.mjGEOM_BOX)  # test:3800 (route-local const promoted; mjGEOM_BOX enum, for _clip2_geoms)
# Recorder-meta (test:1783): the ANTI-REVERT marker lines pinned into the P3 demo meta. Read ONLY in the
# DEMO_RECORD block (dead for Layer A byte-repro). Copied faithfully; when the recorder is wired (Layer B),
# update to route_executor's OWN ANTI-REVERT marker lines (placed verbatim + banner in A4d).
_ANTI_REVERT_MARKER_LINES = [4477, 4493, 4593]

# Pre-allocated double-buffer physics state, created on the first ``physics_step`` call (test:1768).
_physics_state_buffer = None
# Whole-route P3 DAgger demo recorder. None = default-off = byte-identical; the recorder is orthogonal
# to Layer A byte-identity (reference and candidate both run with it None), so it is deferred (test:1780).
_demo_rec = None


def update_kinematic_bodies(physics_state, fk_state, robot_body_count):
    """Copy robot body transforms from FK state to physics state (verbatim; test:1752).

    FK model body indices map 1:1 to physics model body indices (both start at 0). Called each
    substep to ensure kinematic bodies reflect current FK positions before contact detection.
    """
    fk_bq = fk_state.body_q.numpy()
    phys_bq = physics_state.body_q.numpy()
    phys_bq[:robot_body_count] = fk_bq[:robot_body_count]
    physics_state.body_q.assign(phys_bq)


def get_ee_positions(state, scene_info):
    """Get current EE positions for both arms (verbatim; test:1945)."""
    body_q = state.body_q.numpy()
    left_ee = scene_info["left_body_start"] + EE_BODY_OFFSET
    right_ee = scene_info["right_body_start"] + EE_BODY_OFFSET
    pos_l = body_q[left_ee][:3]
    pos_r = body_q[right_ee][:3]
    return pos_l, pos_r


def physics_step(model, state, solver, contacts, scene_info):
    """VBD physics step with kinematic body override (double-buffer pattern; test:1790).

    1. Update kinematic robot bodies from FK state each substep
    2. model.collide() for contact detection (BOX-CAPSULE finger-cable)
    3. VBD solver step -- cable CABLE joint dynamics only (kinematic bodies inv_mass=0)
    4. Double-buffer swap

    Substeps: ``SIM_SUBSTEPS`` per frame. External interface: 1 call = ``DT`` time advancement.
    Returns state with updated body_q (cable from VBD, robot from FK). The ``gripper_dynamic`` branch
    (:1827) overwrites ONLY the arm coords via ``_ARM_OVERWRITE_LOCAL`` -- the SAME G7 SSOT set used by
    the env-path exclusion (§13.0-2); the source name ``_ARM_OVERWRITE_IDX`` (test:1776) is unified here
    to it (identical value {0-5,14-19}, numeric behaviour byte-identical).
    """
    global _physics_state_buffer
    if _physics_state_buffer is None:
        _physics_state_buffer = model.state()

    state_0 = state
    state_1 = _physics_state_buffer

    fk_state = scene_info["fk_state"]
    robot_body_count = scene_info["robot_body_count"]
    vbd_control = scene_info["vbd_control"]
    solver_backend = scene_info.get("solver_backend", "vbd")
    gripper_dynamic = scene_info.get("gripper_dynamic", False)  # R-S6.6 (default False = legacy byte-identical)

    for i in range(SIM_SUBSTEPS):
        if solver_backend == "mujoco":
            # MuJoCo articulated kinematic re-pose (D-Opt1-2): per-substep OVERWRITE joint_q=FK + zero
            # joint_qd (STEP-1 probe-validated; MuJoCo poses bodies from joint_q). disable_contacts=True
            # -> no model.collide (contacts None), mirroring the base mujoco branch.
            n = 2 * JOINTS_PER_ARM
            phys_jq = state_0.joint_q.numpy()
            phys_jqd = state_0.joint_qd.numpy()
            if gripper_dynamic:
                # The gripper is a POSITION actuator (S6_GRASP) -> overwrite ONLY the arm coords
                # ({0-5,14-19}); leave the gripper coords ({6-13,20-27}) DYNAMIC so the servo drives
                # them via control.joint_target_pos. _ARM_OVERWRITE_LOCAL is the G7 SSOT (§13.0-2).
                phys_jq[_ARM_OVERWRITE_LOCAL] = fk_state.joint_q.numpy()[_ARM_OVERWRITE_LOCAL]
                phys_jqd[_ARM_OVERWRITE_LOCAL] = 0.0
            else:
                phys_jq[:n] = fk_state.joint_q.numpy()[:n]
                phys_jqd[:n] = 0.0
            state_0.joint_q.assign(phys_jq)
            state_0.joint_qd.assign(phys_jqd)
            state_0.clear_forces()
            solver.step(state_0, state_1, vbd_control, None, SIM_DT)
        else:
            # Ensure kinematic bodies reflect current FK positions
            update_kinematic_bodies(state_0, fk_state, robot_body_count)

            state_0.clear_forces()
            model.collide(state_0, contacts)
            solver.step(state_0, state_1, vbd_control, contacts, SIM_DT)

        state_0, state_1 = state_1, state_0

    if _demo_rec is not None:  # P3 recorder: sample the post-step frame (read-only, deferred chunk)
        _demo_rec.sample(state_0, scene_info)
    return state_0


def solve_ik_dual(scene_info, target_left, target_right, warmstart_jq=None):
    """Solve IK for both arms using the FK model (verbatim; test:1854).

    Args:
        warmstart_jq: optional full joint-config vector used as the LM solver's initial guess
            (R-S6.2 C2). Default ``None`` uses the current ``fk_state.joint_q`` (byte-identical to
            the prior behavior). Decouples the IK initial guess from the interpolation start so a
            move can re-seed from a known-good config (e.g. the converged hover) instead of a
            post-close LM-stuck point (RS6_1_FINDINGS §2.2).

    Returns (fk_joint_q, cost) — the FK model joint positions with IK solution.
    """
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]

    # EE body indices in FK model (body 6 = panda_hand for each arm)
    left_ee_body = EE_BODY_OFFSET  # 5 (UR5e wrist_3; S2a aliased EE_BODY_OFFSET=EE_BODY_IDX=5)
    right_ee_body = FRANKA_NUM_JOINTS + EE_BODY_OFFSET  # 19 (FRANKA_NUM_JOINTS aliased to ROBOT_NUM_JOINTS=14)

    target_l = np.array([target_left], dtype=np.float32)
    target_r = np.array([target_right], dtype=np.float32)

    obj_l = IKObjectivePosition(
        link_index=left_ee_body,
        link_offset=wp.vec3(0.0, 0.0, 0.0),
        target_positions=wp.array(target_l, dtype=wp.vec3, device=DEVICE),
        weight=1.0,
    )
    obj_r = IKObjectivePosition(
        link_index=right_ee_body,
        link_offset=wp.vec3(0.0, 0.0, 0.0),
        target_positions=wp.array(target_r, dtype=wp.vec3, device=DEVICE),
        weight=1.0,
    )

    # Rotation objectives: gripper pointing DOWN, fingers PERPENDICULAR to cable (world Y).
    # S6 retarget (UR5e+2F-85, NOT Franka): target = wrist_3 (body 5/19) world orientation
    # q = Rx(-90°), xyzw = (-√2/2, 0, 0, √2/2). Maps wrist_3 local +Y (approach) → world -Z (down)
    # and local X (finger-sep) → world ±X (⊥ cable Y). VALIDATED on the UR5e FK model: probe_ik_verify
    # (right arm down_dot=1.0/perp_|x|=1.0/z_leak=0) + probe_smoke_geom (BOTH arms down_dot=1.0/perp=1.0).
    # Convention seam: warp wp.vec4/IKObjectiveRotation = xyzw (newton ik_objectives.py:618,
    # target=wp.quat(vec[0..3]), w=vec[3]); the wrist_3 MuJoCo attachment_site is wxyz.
    # (The prior Franka π/8 quat was built for the collapsed panda_hand_joint frame → mis-orients the
    # UR5e wrist_3 = the S5 P1.3 horizontal-gripper failure; the S6 smoke now asserts this DOWN/⊥ TRIAD.)
    target_rot = wp.array([wp.vec4(-0.7071067811865476, 0.0, 0.0, 0.7071067811865476)], dtype=wp.vec4, device=DEVICE)
    rot_l = IKObjectiveRotation(
        link_index=left_ee_body,
        link_offset_rotation=wp.quat_identity(),
        target_rotations=target_rot,
        weight=0.5,
    )
    rot_r = IKObjectiveRotation(
        link_index=right_ee_body,
        link_offset_rotation=wp.quat_identity(),
        target_rotations=target_rot,
        weight=0.5,
    )

    # Joint limit objective: keeps IK solutions within URDF limits
    obj_joint_limits = IKObjectiveJointLimit(
        joint_limit_lower=fk_model.joint_limit_lower,
        joint_limit_upper=fk_model.joint_limit_upper,
        weight=10.0,
    )

    # Dual-arm collision avoidance objectives
    from newton_routing_utils import _build_collision_objectives

    _use_collision = os.environ.get("COLLISION_AVOIDANCE", "1") != "0"
    collision_objs = _build_collision_objectives() if _use_collision else []

    ik_solver = IKSolver(
        fk_model, n_problems=1, objectives=[obj_l, obj_r, rot_l, rot_r, *collision_objs, obj_joint_limits]
    )

    # Initial guess for the LM solver: the warm-start config if provided (R-S6.2 C2, decoupled from
    # the interpolation start), else the current FK joint positions (byte-identical default).
    fk_jq = fk_state.joint_q.numpy().copy()
    if warmstart_jq is not None:
        fk_jq = np.asarray(warmstart_jq, dtype=fk_jq.dtype).reshape(-1).copy()
    jq_in = wp.array(fk_jq.reshape(1, -1), dtype=float, device=DEVICE)
    jq_out = wp.zeros((1, fk_model.joint_coord_count), dtype=float, device=DEVICE)

    ik_solver.step(jq_in, jq_out, iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)

    cost = ik_solver.costs.numpy()[0]
    result = jq_out.numpy()[0]

    return result, cost


def ik_move_both(
    model,
    state,
    scene_info,
    solver,
    contacts,
    target_left,
    target_right,
    label="MOVE",
    converge_mm=5.0,
    speed_factor=1.0,
    warmstart_jq=None,
    ik_solve_fn=None,
):
    """Move both EEs to target positions using IK + VBD stepping (test:1958; F11 explicit ik-solve-fn).

    Strategy: Solve IK ONCE for the final target, then interpolate FK joint
    positions over physics steps. Kinematic bodies follow FK instantly.

    Args:
        speed_factor: multiplier for step count (>1 = slower motion).
        ik_solve_fn: the dual-arm IK solve function (F11 §12.6). ``None`` => the module
            :func:`solve_ik_dual` (byte-identical to the monolith default). The C2 re-grasp passes the
            per-arm-rotation ``_solve_ik_dual_rot`` (same signature) here instead of monkeypatching the
            module global (no-global-mutation, HIGH4), reproducing the windowed monkeypatch byte-identically.

    Returns (final_state, success).
    """
    if _demo_rec is not None:  # P3 recorder: last-COMMANDED EE target positions (spec §2.3, positions only)
        _demo_rec.note_targets(target_left, target_right)
    _ik_solve = ik_solve_fn if ik_solve_fn is not None else solve_ik_dual  # F11: injected solver or default
    cable_bodies = scene_info.get("cable_bodies", [])
    fk_model = scene_info["fk_model"]
    fk_state = scene_info["fk_state"]

    pos_l, pos_r = get_ee_positions(state, scene_info)
    dist = max(np.linalg.norm(np.array(target_left) - pos_l), np.linalg.norm(np.array(target_right) - pos_r))
    n_steps = max(int(dist * 100 * STEPS_PER_CM * speed_factor), 50)
    n_steps = min(n_steps, MAX_MOVE_STEPS)

    print(
        f"  [{label}] Moving: L=({pos_l[0]:.3f},{pos_l[1]:.3f},{pos_l[2]:.3f}) "
        f"→ ({target_left[0]:.3f},{target_left[1]:.3f},{target_left[2]:.3f})"
    )
    print(
        f"  [{label}] Moving: R=({pos_r[0]:.3f},{pos_r[1]:.3f},{pos_r[2]:.3f}) "
        f"→ ({target_right[0]:.3f},{target_right[1]:.3f},{target_right[2]:.3f})"
    )
    print(f"  [{label}] dist={dist * 1000:.1f}mm, steps={n_steps}")

    tgt_l = np.array(target_left, dtype=np.float32)
    tgt_r = np.array(target_right, dtype=np.float32)

    # Solve IK once for final target (R-S6.2 C2: optional warm-start seed, default = current FK config)
    jq_target, ik_cost = _ik_solve(scene_info, tuple(tgt_l), tuple(tgt_r), warmstart_jq=warmstart_jq)
    if np.any(np.isnan(jq_target)):
        print(f"  [{label}] IK NaN!")
        return state, False
    print(f"  [{label}] IK solved: cost={ik_cost:.2e}")

    # FK joint interpolation: arm joints only (j0-j6), preserve finger joints (j7-j8)
    fk_coord_count = fk_model.joint_coord_count
    jq_start = fk_state.joint_q.numpy().copy()
    jq_end = jq_target.copy()

    # Gripper coord indices to EXCLUDE from arm-IK interpolation (hold the gripper through arm moves).
    # S6: exclude ALL 8 gripper joints/arm via SSOT GRIPPER_JOINT_RANGE ([6..13]; right arm +JOINTS_PER_ARM
    # = [20..27]). The old {7,8,21,22} (Franka 2-finger) left 6/8 gripper joints/arm in the interpolation.
    # (IK leaves gripper joints ~unchanged — zero Jacobian on the arm-EE/collision objectives — so this is
    # SSOT-correctness + defense: it guarantees a scripted close is held through the post-close LIFT.)
    finger_coords = set(GRIPPER_JOINT_RANGE) | {JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE}

    for step in range(n_steps):
        t = min((step + 1) / n_steps, 1.0)

        # Interpolate arm joints, preserve finger positions
        jq_interp = jq_start.copy()
        for d in range(fk_coord_count):
            if d not in finger_coords:
                jq_interp[d] = jq_start[d] + (jq_end[d] - jq_start[d]) * t

        # Update FK state → body transforms
        fk_state.joint_q.assign(jq_interp)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

        # VBD step (kinematic bodies updated from FK inside physics_step)
        state = physics_step(model, state, solver, contacts, scene_info)

        # Video frame capture
        recorder = scene_info.get("recorder")
        if recorder:
            recorder.capture(state)

        # Check cable NaN
        if cable_bodies:
            bq = state.body_q.numpy()
            if np.any(np.isnan(bq[cable_bodies])):
                print(f"  [{label}] Cable NaN at step {step}!")
                return state, False

        # Log progress
        if step % max(n_steps // 5, 1) == 0:
            cur_l, cur_r = get_ee_positions(state, scene_info)
            err_l = np.linalg.norm(cur_l - tgt_l) * 1000
            err_r = np.linalg.norm(cur_r - tgt_r) * 1000
            cable_str = ""
            if cable_bodies:
                bq = state.body_q.numpy()
                cz = bq[cable_bodies, 2]
                cz_nan = np.any(np.isnan(cz))
                cable_str = f" cable_z=[{np.nanmin(cz):.4f},{np.nanmean(cz):.4f}] nan={cz_nan}"
            # Extended diagnostics during lift phases
            diag_str = ""
            if label.startswith("P2") and cable_bodies:
                fk_jq = fk_state.joint_q.numpy()
                fj = [fk_jq[7], fk_jq[8], fk_jq[FRANKA_NUM_JOINTS + 7], fk_jq[FRANKA_NUM_JOINTS + 8]]
                diag_str += f" fingers=[{fj[0] * 1000:.1f},{fj[1] * 1000:.1f},{fj[2] * 1000:.1f},{fj[3] * 1000:.1f}]mm"
                # Contact diagnostics
                model.collide(state, contacts)
                wp.synchronize()
                nc = contacts.rigid_contact_count.numpy()[0]
                if nc > 0:
                    s0 = contacts.rigid_contact_shape0.numpy()[:nc]
                    s1 = contacts.rigid_contact_shape1.numpy()[:nc]
                    sb = model.shape_body.numpy()
                    lb = scene_info["left_body_start"]
                    rb = scene_info["right_body_start"]
                    fset = {lb + 7, lb + 8, rb + 7, rb + 8}
                    cset = set(cable_bodies)
                    fc_cnt = sum(
                        1
                        for ci in range(nc)
                        if (sb[s0[ci]] in fset or sb[s1[ci]] in fset) and (sb[s0[ci]] in cset or sb[s1[ci]] in cset)
                    )
                    co_cnt = sum(
                        1
                        for ci in range(nc)
                        if (sb[s0[ci]] in cset or sb[s1[ci]] in cset) and not (sb[s0[ci]] in fset or sb[s1[ci]] in fset)
                    )
                    diag_str += f" contacts={nc}(fc={fc_cnt},co={co_cnt})"
                else:
                    diag_str += " contacts=0"
            print(f"  [{label}] step {step}/{n_steps}: err L={err_l:.1f}mm R={err_r:.1f}mm{cable_str}{diag_str}")

    # Final error
    pos_l, pos_r = get_ee_positions(state, scene_info)
    err_l = np.linalg.norm(pos_l - tgt_l) * 1000
    err_r = np.linalg.norm(pos_r - tgt_r) * 1000
    converged = err_l < converge_mm and err_r < converge_mm
    print(f"  [{label}] Final: err L={err_l:.1f}mm R={err_r:.1f}mm converged={converged} (thresh={converge_mm}mm)")

    return state, converged


# =============================================================================
# §13 / item-1 -- C2 re-grasp per-arm-rotation IK closures, re-plumbed to module level.
# In the monolith these are route-LOCAL closures (test:5156/5161/5171) capturing route state
# (``state``/``cable_bodies``/``_ROT``); verbatim copy is impossible (item-1). They are re-plumbed
# to explicit params (closure-var -> arg), BEHAVIOR-PRESERVING: no change beyond the arg-ification
# (proven by the ast semantic-equiv check, which reverses only the re-plumb). The route body (A4+)
# builds ``_ROT`` and injects the rotated solver into ``ik_move_both`` via
# ``ik_solve_fn=functools.partial(_solve_ik_dual_rot, rot=_ROT)`` (F11, no monkeypatch of a global).
# =============================================================================
def _rot_quat_rx(angle):  # X-rotation target in solve_ik_dual's XYZW convention (w LAST)
    return wp.array([wp.vec4(_math.sin(angle / 2), 0.0, 0.0, _math.cos(angle / 2))], dtype=wp.vec4, device=DEVICE)


def _cable_local_pitch(y_t, state, cable_bodies):
    # cable local Y-Z pitch theta [rad] at lane y_t (tangent of adjacent segments).
    # (re-plumb A3/item-1: ``state``/``cable_bodies`` were route-local closures -> explicit params.)
    wp.synchronize()
    cbs = state.body_q.numpy()[cable_bodies]
    cbs = cbs[np.argsort(cbs[:, 1])]
    ys = cbs[:, 1]
    j = int(np.argmin(np.abs(ys - y_t)))
    a, b = max(j - 1, 0), min(j + 1, len(ys) - 1)
    dY, dZ = float(ys[b] - ys[a]), float(cbs[b, 2] - cbs[a, 2])
    return _math.atan2(dZ, dY) if abs(dY) > 1e-9 else 0.0


def _solve_ik_dual_rot(scene_info_, target_left, target_right, warmstart_jq=None, rot=None):
    # Faithful copy of solve_ik_dual (test:1814) but with PER-ARM rotation targets _ROT['L']/_ROT['R'].
    # (re-plumb A3/item-1: the ``_ROT`` closure -> explicit ``rot`` param; C2 passes rot=_ROT via partial.)
    fk_model_ = scene_info_["fk_model"]
    fk_state_ = scene_info_["fk_state"]
    le, re = EE_BODY_OFFSET, FRANKA_NUM_JOINTS + EE_BODY_OFFSET
    ol = IKObjectivePosition(
        link_index=le,
        link_offset=wp.vec3(0.0, 0.0, 0.0),
        target_positions=wp.array(np.array([target_left], dtype=np.float32), dtype=wp.vec3, device=DEVICE),
        weight=1.0,
    )
    orr = IKObjectivePosition(
        link_index=re,
        link_offset=wp.vec3(0.0, 0.0, 0.0),
        target_positions=wp.array(np.array([target_right], dtype=np.float32), dtype=wp.vec3, device=DEVICE),
        weight=1.0,
    )
    rl = IKObjectiveRotation(
        link_index=le, link_offset_rotation=wp.quat_identity(), target_rotations=rot["L"], weight=0.5
    )
    rr = IKObjectiveRotation(
        link_index=re, link_offset_rotation=wp.quat_identity(), target_rotations=rot["R"], weight=0.5
    )
    jl = IKObjectiveJointLimit(
        joint_limit_lower=fk_model_.joint_limit_lower,
        joint_limit_upper=fk_model_.joint_limit_upper,
        weight=10.0,
    )
    from newton_routing_utils import _build_collision_objectives

    cobjs = _build_collision_objectives() if os.environ.get("COLLISION_AVOIDANCE", "1") != "0" else []
    iks = IKSolver(fk_model_, n_problems=1, objectives=[ol, orr, rl, rr, *cobjs, jl])
    fj = fk_state_.joint_q.numpy().copy()
    if warmstart_jq is not None:
        fj = np.asarray(warmstart_jq, dtype=fj.dtype).reshape(-1).copy()
    qin = wp.array(fj.reshape(1, -1), dtype=float, device=DEVICE)
    qout = wp.zeros((1, fk_model_.joint_coord_count), dtype=float, device=DEVICE)
    iks.step(qin, qout, iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)
    return qout.numpy()[0], float(iks.costs.numpy()[0])


# =============================================================================
# §13 / charter extract-7 -- the remaining 4 target/scene closures, re-plumbed to module level
# (A4a; test tgt:4197 / tgt2:4200 / _w0e_guarded_cx:4205 / _clip2_geoms:3859). Same item-1 discipline
# as the A3 IK closures: closure-var -> explicit param, BEHAVIOR-PRESERVING (ast semantic-equiv reverses
# only the arg-ification). These are shared between the Layer A self-driving ``run_route`` (A4b+) and the
# Layer B ``step_target`` facade (the per-step target/seat computation). ``GHS`` (=GRIP_HALF_SPAN=0.044,
# 88mm span INVARIANT#2) and ``GRASP_YC`` (settled grasp centre) are the route-local closure vars.
# =============================================================================
def tgt(x, z, grasp_yc, ghs):
    return (x, grasp_yc - ghs, z), (x, grasp_yc + ghs, z)


def tgt2(x, yc, z, ghs):
    # M-Route-2 C1: diagonal target with a MOVING grasp centre yc (interp GRASP_YC -> y_clip); the 88mm span is
    # preserved (yc +- GHS = INVARIANT#2). For y_clip=0 (centred M-Route-1) tgt2(x, GRASP_YC, z) == tgt(x, z).
    return (x, yc - ghs, z), (x, yc + ghs, z)


def _w0e_guarded_cx(y_ref, x_ref, state, cable_bodies):
    # W0-e common guarded crossing-X selector (spec v0.9 cluster A): mean cable-body X within the Y window
    # |y-y_ref|<=7.5mm AND the X plausibility window |x-x_ref|<=30mm (offline-validated: n=1, 0 tail-hijack
    # on all 81 cells, validate_measurands.py:54-57). Returns (mean_x_m, n_nodes); (None, 0) if the window is
    # empty (plausibility reject). Reads the LIVE `state` by closure (same pattern as _zc1).
    # (re-plumb A4a/item-1: ``state``/``cable_bodies`` were route-local closures -> explicit params.)
    wp.synchronize()
    _P = state.body_q.numpy()[cable_bodies]
    _m = (np.abs(_P[:, 1] - y_ref) <= 0.0075) & (np.abs(_P[:, 0] - x_ref) <= 0.030)
    if not _m.any():
        return None, 0
    return float(_P[_m, 0].mean()), int(_m.sum())


def _clip2_geoms(mjm, mjd, c2x, c2y):
    # C2 (Rs C1->C2 routing): the SECOND clip's collision BOXes near (c2x, c2y) for the cable<->C2 mj_geomDistance
    # reach/seat proof. Same worldbody-BOX-near-XY filter as _clip_geoms but centred on C2 (C1 excluded: dx>=50mm).
    # (re-plumb A4a/item-1: ``mjm``/``mjd``/``c2x``/``c2y`` were route-local closures -> explicit params; ``mujoco``/
    # ``_BOX`` resolve to the module import/const, same value as the route-local test:3800.)
    mujoco.mj_forward(mjm, mjd)
    return [
        g
        for g in range(mjm.ngeom)
        if int(mjm.geom_type[g]) == _BOX
        and int(mjm.geom_bodyid[g]) == 0
        and abs(float(mjd.geom_xpos[g][0]) - c2x) < 0.03
        and abs(float(mjd.geom_xpos[g][1]) - c2y) < 0.03
    ]


# =============================================================================
# Module helpers copied for run_route (Layer A). _set_gripper_target (test:3019) is the CONTROL-level
# gripper cadence (control.joint_target_pos read-set-assign) used by run_route -- DISTINCT from the
# array-level set_gripper_target above (env-drive :738 / Layer B path); both legitimate, do not conflate.
# The DQ7 _pj_* subsystem (test:3622-3690) is present-but-dead for Layer A byte-repro: PERTURB_INJECT
# unset => _pj_load_schedule('') returns None => _inject_detour is a literal passthrough; kept faithful.
# =============================================================================
_PJ_ELIGIBLE = ("GRASP_DESCEND", "C2_REGRASP")


_PJ_RELEASE_MARGIN = {"C2_REGRASP": 2}


def _pj_load_schedule(path):
    """Load the PERTURB_INJECT schedule [dict] or return None (off). Asserts every injection phase is eligible (v2 §B)."""
    if not path:
        return None
    import json

    with open(path) as fh:
        raw = json.load(fh)
    injs = raw.get("injections", [])
    for e in injs:
        assert e["phase"] in _PJ_ELIGIBLE, (
            f"PERTURB_INJECT STOP: phase {e['phase']!r} not in eligible {_PJ_ELIGIBLE} "
            f"(SKIP-phase injection forbidden -- mini-spec v2 §B _ph-eligibility assert)"
        )
    return {"by_key": {(e["phase"], int(e["kick_call_idx"])): e for e in injs}, "open": None, "seed": raw.get("seed")}


def _pj_step(sched, rec, phase, call_idx, loop_len, tgl, tgr):
    """Stateful kick-and-recover target wrap (v2 §A/§B): offsets ONE arm during the kick, passes through otherwise.

    Opens a window at the scheduled (phase, kick_call_idx) (``rec.mark_injection`` start), holds it for kick_calls
    calls, then closes it (``rec.mark_injection`` end) so the recorded ``[start_frame, end_frame)`` marks the kick.
    The regrasp_ok release-margin guard (U5) refuses a kick that would still be open within the phase's
    verdict-critical tail. NEVER offsets both arms (INVARIANT#1). Called ONLY when ``sched`` is not None (the
    None-path literal passthrough is handled by the caller ``_inject_detour``).
    """
    op = sched.get("open")
    if op is not None and call_idx >= op["end_call"]:  # release -> recovery begins
        if rec is not None:
            rec.mark_injection(event="end")
        sched["open"] = op = None
    if op is None:  # maybe start a new kick here
        e = sched["by_key"].get((phase, call_idx))
        if e is not None:
            kc = int(e["kick_calls"])
            if call_idx + kc <= loop_len - _PJ_RELEASE_MARGIN.get(phase, 0):
                sched["open"] = op = {
                    "phase": phase,
                    "arm": e["arm"],
                    "offset_m": list(e["offset_m"]),
                    "end_call": call_idx + kc,
                }
                if rec is not None:
                    rec.mark_injection(
                        phase=phase,
                        arm=e["arm"],
                        offset_m=e["offset_m"],
                        kick_calls=kc,
                        seed=e.get("seed"),
                        event="start",
                    )
            else:
                print(
                    f"  [PERTURB_INJECT] SKIP {phase} kick@call{call_idx} (+{kc}) breaches release-margin of "
                    f"loop_len {loop_len} -> passthrough (regrasp_ok guard)"
                )
    if op is not None and op["phase"] == phase and call_idx < op["end_call"]:  # within the kick -> offset ONE arm
        o = op["offset_m"]
        if op["arm"] == "R":
            return tgl, (tgr[0] + o[0], tgr[1] + o[1], tgr[2] + o[2])
        return (tgl[0] + o[0], tgl[1] + o[1], tgl[2] + o[2]), tgr
    return tgl, tgr


def _set_gripper_target(control, driver_joints, target_rad):
    """R-S6.6: schedule the gripper POSITION-servo target by writing ``control.joint_target_pos`` on the
    driver dofs (the array SolverMuJoCo reads each step, solver_mujoco.py:362/:3606 -- NOT model-level,
    so a runtime change takes effect). ``model.control()`` seeds it from the build-time OPEN target."""
    tp = control.joint_target_pos.numpy()
    for d in driver_joints:
        tp[d] = float(target_rad)
    control.joint_target_pos.assign(tp)
    if _demo_rec is not None:  # P3 recorder: gripper CHOKEPOINT -> per-arm servo command (spec §2.2)
        _demo_rec.note_grip(driver_joints, target_rad)


# =============================================================================
# section 13.7 run_route -- Layer A self-driving byte-repro subject. SCRIPTED verbatim extraction of the
# Rs-LOCKED _run_mujoco_grasp_route (test:3692) with ONLY localized transforms (signature rename here;
# C2 F11 in A4d). All inner closures are kept INNER-verbatim (max byte-fidelity, verbatim call sites);
# the module-level extract-7 shadow-serve the Layer B step_target facade and are held byte-identical to
# these inner copies by the section-12.4/item-1 ast semantic-equiv drift tripwire (standing gate).
# Built incrementally A4b/c/d; the NotImplementedError tail = the next chunk boundary.
# =============================================================================
def run_route(model, solver, contacts, scene_info, fk_state, output_dir=None, record_video=False):
    """M-Route-1 / M-Route-2 C1 (env-gate S6_GRASP_ROUTE=1): the BANKED centred grasp+lift (M-Grasp-engage-1) +
    AERIAL TRANSPORT (GX 0.30 -> CLIP_X, both arms together) + a CONTINUOUS two-claw cage + drop-in seat@809.
    CLIP_Y=0 = M-Route-1 (centred, X-only). CLIP_Y!=0 = M-Route-2 (DIAGONAL drag to an OFF-CENTRE clip, e.g. C1
    (0.35,+0.150) CLIP_X=0.35 CLIP_Y=0.150): the route loop interpolates BOTH x and the grasp-centre yck while
    holding the 88mm span (yck+-GHS) -> the LEFT arm STRETCHES (lateral ~0.456 near-reach) / the RIGHT FOLDS
    (~0.156) = the asymmetric diagonal drag (INVARIANT#1-compliant: both arms move, neither parked). The seat
    refs follow the gripped seg to y_clip; the cable<->clip mj_geomDistance AT seat = the real-seat proof.

    FAITHFUL-TO-INTENT of the banked CPU r_s71_clip_dropin_72 (the ROUTE step :226-231: symmetric X move both
    arms at z_lift); NOT a port of the legacy VBD do_p3_move/do_p4_push (先祖返り-fenced). REUSES ik_move_both /
    the 2-phase コ close / the WR lift. The DROP-IN/seat (809) = M-Hook-1, a SEPARATE next milestone -- NOT here.
    INVARIANTS untouched: 88mm span (Y=+-GHS), dual-arm both arms route together, DiffIK (ik_move_both), コ.

    PRE-STEP caveat-a (%9 MANDATORY): centre the grasp on the SETTLED cable Y so BOTH arms contact symmetrically
    (the 0.74mm off-centre cable gave L-deep/R-12um-hairgap; the drag load-tests the marginal RIGHT harder).
    CONTINUOUS gate (%2 owns M2ii): at EVERY route waypoint, BOTH arms' f1ext must be UNDER the cable
    (mj_geomDistance fromto = dz-VERTICAL, not lateral=beside) AND within the cage; + nodrop (sag<=10mm through
    the WHOLE route); + caveat-d drag (the draping far-ends must not pull the span out / snag). CPU; grip-magnitude
    + penetration NON-conservative x3 vs GPU. Emits [S6_ROUTE] + sys.exit (0 PASS / 2 FAIL).
    """
    import mujoco  # lazy: CPU mj_model/mj_data

    assert scene_info.get("grasp_actuation"), "S6_GRASP_ROUTE needs build_scene(grasp_actuation=True)"
    assert scene_info.get("cable_bodies"), "S6_GRASP_ROUTE needs a cable (run WITHOUT --no-cable)"
    fk_model = scene_info["fk_model"]
    control = scene_info["vbd_control"]
    driver_joints = scene_info["driver_joints"]
    cable_bodies = scene_info["cable_bodies"]
    scene_info["gripper_dynamic"] = True
    _set_gripper_target(control, driver_joints, GRIPPER_DRIVER_OPEN_RAD)

    global _demo_rec
    if os.environ.get("DEMO_RECORD", "0") == "1":  # P3 whole-route demo RECORDER (env-gated, read-only; spec §2)
        from route_demo_recorder import RouteDemoRecorder

        _demo_rec = RouteDemoRecorder(
            scene_info,
            EE_BODY_OFFSET,
            driver_joints[:2],
            driver_joints[2:],  # per-arm drivers, SSOT :1461
            os.environ.get("DEMO_OUT", "eval_runs/troot_optE_dapg_wholeroute_scope_20260701/demo_raw"),
            {
                "dt": DT,
                "sim_dt": SIM_DT,
                "sim_substeps": SIM_SUBSTEPS,
                "device": DEVICE,
                "solver_backend": scene_info.get("solver_backend"),
                # F2: physics-model joint_label (74=2*JPA+cable), not fk_model.joint_key (28, wrong obj)
                "joint_names": list(getattr(scene_info["model"], "joint_label", []) or []),
                "joint_names_source": "physics_model.joint_label",
                "arm_q_layout": {
                    "l_arm": [0, JOINTS_PER_ARM],
                    "r_arm": [JOINTS_PER_ARM, 2 * JOINTS_PER_ARM],
                    "cable": [2 * JOINTS_PER_ARM, None],
                },
                # env-resolved (no hardcode); mirrors the route's own resolution (c1 :3543-3544 / c2 :3591-3592)
                "resolved_clip_c1_xy": [
                    float(os.environ.get("CLIP_X", "0.40")),
                    float(os.environ.get("CLIP_Y", "0.0")),
                ],
                "resolved_clip_c2_xy": [
                    float(os.environ.get("CLIP2_X", str(CLIP_POSITIONS[1][0]))),
                    float(os.environ.get("CLIP2_Y", str(CLIP_POSITIONS[1][1]))),
                ],
                "anti_revert_marker_lines": _ANTI_REVERT_MARKER_LINES,
            },
        )

    def _ph(name):  # P3 recorder: label the native route section (forward, at each block start; spec §2.6)
        if _demo_rec is not None:
            _demo_rec.set_phase(name)

    # DQ7 (ii): load the injection schedule ONCE (None when PERTURB_INJECT is unset -> hook = literal passthrough).
    _pj_sched = _pj_load_schedule(os.environ.get("PERTURB_INJECT", ""))

    def _inject_detour(phase_name, call_idx, loop_len, tgl, tgr):
        """kick-and-recover hook wrapping an ik_move_both target arg (v2 §B). None-path = LITERAL passthrough."""
        if _pj_sched is None:
            return (
                tgl,
                tgr,
            )  # U11/C1 byte-identity: returns the EXACT target tuples unchanged (pure-Python, no round-trip)
        return _pj_step(_pj_sched, _demo_rec, phase_name, call_idx, loop_len, tgl, tgr)

    GHS = (WIDE_RIGHT_Y - WIDE_LEFT_Y) / 2.0  # 0.044 = 88mm span INVARIANT#2
    z_grasp = 1.0668  # banked WR cradle (M-Grasp-engage-1 validated)
    z_high = z_grasp + 0.10
    # W0-e transport-clearance raise (Rs 2026-07-05「c1 搬送で高さ不足→clip 上面かする」, /geometric-design gate):
    # 0.05->0.08 (+30mm) so the transported cable centre clears the clip high-wall top (850mm @float20) + cable r4 +
    # margin5 = >=859mm (measured baseline 831mm scraped). GLOBAL (nominal too = Rs baseline correction -> new sha).
    # Also lands the C1_SEAT-else descent START above the clip -> the existing v1 X-comp descent seats VERTICALLY (no
    # wall-ride) = the v2 physics re-expressed in COORDINATES, no new legs (step-table-faithful). env-overridable to tune.
    LIFT_M, LIFT_SUBSTEPS = float(os.environ.get("W0E_LIFT_M", "0.08")), 12
    z_lift = z_grasp + LIFT_M  # aerial transport height (lift end)
    x_grasp = GRASP_X  # 0.30
    x_clip = float(os.environ.get("CLIP_X", "0.40"))  # banked void-cleared target (NOT C3 0.35 on the void)
    y_clip = float(os.environ.get("CLIP_Y", "0.0"))  # M-Route-2: off-centre clip Y (C1=+0.150); 0.0 = centred M-Route-1
    N_ROUTE = 6  # banked r_s71:228 symmetric X waypoints
    GRASP_YC = 0.0  # nominal; caveat-a re-centres on the settled cable below

    mjm, mjd = getattr(solver, "mj_model", None), getattr(solver, "mj_data", None)
    assert mjm is not None and mjd is not None, "S6_GRASP_ROUTE needs CPU mj_model/mj_data"
    _freeze_scope_rec = None  # PERCLIP_PIN (b)-pin freeze-scope record (%3 charter); persisted into metrics below
    _c2_settle_rec = None  # C2_DUALSEAT release-and-settle record (%0 seat-capture concern, charter metric #3)
    _c2_regrasp_rec = (
        None  # C2_DUALSEAT R re-grasp record (Rs guide-data charter: R-reach + R-grip-nonzero, %0 cross-PV)
    )
    _BOX, _CAP = int(mujoco.mjtGeom.mjGEOM_BOX), int(mujoco.mjtGeom.mjGEOM_CAPSULE)

    def _gn(gi):
        return (mujoco.mj_id2name(mjm, mujoco.mjtObj.mjOBJ_GEOM, int(gi)) or "").lower()

    pad_geoms = [
        g for g in range(mjm.ngeom) if int(mjm.geom_type[g]) == _BOX and ("pad1" in _gn(g) or "pad2" in _gn(g))
    ]
    f1_geoms = [g for g in range(mjm.ngeom) if int(mjm.geom_type[g]) == _BOX and "f1ext" in _gn(g)]  # BOTTOM claw
    f2_geoms = [g for g in range(mjm.ngeom) if int(mjm.geom_type[g]) == _BOX and "f2ext" in _gn(g)]  # TOP claw
    cable_geoms = [g for g in range(mjm.ngeom) if int(mjm.geom_type[g]) == _CAP]

    # PART 1 GATE-FIX (%2 log:6738 two-claw cage): retention = the cable is SANDWICHED between the two claws
    # (f1ext bottom + f2ext top, mouth ~10mm, Ø8 cable -> ~2mm play; GD-KoShape-Finger.md:51-58) AND laterally
    # within the claw footprint. The OLD f1ext-only gate false-FAILed "cable risen to the TOP claw under drag"
    # (f1_gap grows but f2 holds it = still caged). New PASS = |f1_gap + Ø8 + f2_gap - mouth| <= tol  AND
    # |cable_x - claw_x| < claw half-extent. Real escape is LATERAL (out the open コ mouth, world X = route axis).
    CABLE_DIAM_MM = 2.0 * CABLE_RADIUS * 1e3  # 8.0
    MOUTH_MM = 10.0  # f1ext<->f2ext inner gap (GD-KoShape-Finger.md:58)
    SAND_TOL_MM = 3.0  # cable "between claws" if f1+Ø8+f2 in [7,13]mm (snug rests-on-bottom sum=10; drag-to-top sum=10)
    LATERAL_MAX_MM = 9.0  # claw half-extent in the closing axis (pad-local half_y 0.009; GD-KoShape-Finger.md:51-54)
    # PART 2 M-Hook-1 (banked r_s71_clip_dropin_72): drop-in onto the REAL collidable clip at (CLIP_X, CLIP_Y).
    REL_CABLE_Z = float(os.environ.get("REL_CABLE_Z", "0.820"))  # banked depth: lower the claw to the wall top
    # CLIP_FLOAT_Z (human-Rs FLOAT-the-clips probe, 0-commit): the SAME h read in build_scene (clip boxes). Here it
    # floats the cable SEAT target (GROOVE_CENTER_Z+h), the gripper DESCENT target (seat_ee_z/c2_seat_ee_z = seat+ee_off),
    # and the retention wall criterion (LOW_WALL_TOP = CLIP1_Z+h+0.020). TABLE_HEIGHT STAYS 0.80 (the table is what the
    # float clears). DEFAULT 0.0 -> byte-identical. NOTE: GRASP_Z/PUSH_Z (task_config) are the LEGACY P1-P4 path, NOT
    # used by route_c1_c2 -> the route descent target is GROOVE_CENTER_Z+ee_off (dynamic), floated below.
    _clip_float_z = float(os.environ.get("CLIP_FLOAT_Z", "0.0"))
    _ROUTE_C2 = os.environ.get("S13_ROUTE_C2", "0") == "1"  # %3 Rs C1->C2 routing directive (half-unclamp + guide)
    DO_HOOK = (os.environ.get("S6_HOOK", "1") == "1") and not _ROUTE_C2  # C1->C2 supplies its own clamped seat
    _clip_collidable = os.environ.get("CLIP_COLLISION", "0") == "1"
    # C2 (Rs directive): canonical CLIP_POSITIONS[1]=(0.40,+0.075); overridable for sweeps. Used by _clip2_geoms
    # (the cable<->C2 reach proof) and the §運用14 C2 label/camera. Built only when CLIP2=1 (build_scene).
    c2x = float(os.environ.get("CLIP2_X", str(CLIP_POSITIONS[1][0])))
    c2y = float(os.environ.get("CLIP2_Y", str(CLIP_POSITIONS[1][1])))

    def _min_dist_mm(setA, setB):
        mujoco.mj_forward(mjm, mjd)
        d = 1e9
        for a in setA:
            for b in setB:
                d = min(d, mujoco.mj_geomDistance(mjm, mjd, a, b, 0.05, np.zeros(6)))
        return d * 1000.0

    def _clip_geoms():
        # %9 ADD (real-seat proof): the clip's collision BOXes for the cable<->clip mj_geomDistance AT seat (vs an
        # ee_off-stale FALSE-seat; M-Hook-1 gave -0.053mm). The 5 clip parts are small worldbody (bodyid 0) BOXes
        # clustered at (x_clip, y_clip); the table (also worldbody) is centred far in Y -> excluded by the XY gate.
        mujoco.mj_forward(mjm, mjd)
        return [
            g
            for g in range(mjm.ngeom)
            if int(mjm.geom_type[g]) == _BOX
            and int(mjm.geom_bodyid[g]) == 0
            and abs(float(mjd.geom_xpos[g][0]) - x_clip) < 0.03
            and abs(float(mjd.geom_xpos[g][1]) - y_clip) < 0.03
        ]

    def _clip2_geoms():
        # C2 (Rs C1->C2 routing): the SECOND clip's collision BOXes near (c2x, c2y) for the cable<->C2 mj_geomDistance
        # reach/seat proof. Same worldbody-BOX-near-XY filter as _clip_geoms but centred on C2 (C1 excluded: dx>=50mm).
        mujoco.mj_forward(mjm, mjd)
        return [
            g
            for g in range(mjm.ngeom)
            if int(mjm.geom_type[g]) == _BOX
            and int(mjm.geom_bodyid[g]) == 0
            and abs(float(mjd.geom_xpos[g][0]) - c2x) < 0.03
            and abs(float(mjd.geom_xpos[g][1]) - c2y) < 0.03
        ]

    def _table_geoms():
        # the LARGE worldbody BOXes = the table (1 solid box, or the 4 grasp-slot boxes). Small clip BOXes (<=25mm)
        # are excluded by the size gate -> separates a "claw vs SOLID table JAM" from a "claw vs cable/clip" contact
        # (OPS-SUP cross-PV flag 2: the C2-over-solid jam is geometry, NOT the cable-physics drag).
        return [
            g
            for g in range(mjm.ngeom)
            if int(mjm.geom_type[g]) == _BOX and int(mjm.geom_bodyid[g]) == 0 and float(np.max(mjm.geom_size[g])) > 0.05
        ]

    def _cage_pair(arm_geoms):
        # closest (claw <-> cable) pair for this arm's claw-set: (dist_mm, fromto6, claw_gid, cable_gid).
        # fromto = [claw_pt(3), cable_pt(3)]; gap = cable_pt - claw_pt.
        mujoco.mj_forward(mjm, mjd)
        best_d, best_ft, best_claw, best_cab = 1e9, None, -1, -1
        for a in arm_geoms:
            for b in cable_geoms:
                ft = np.zeros(6)
                d = mujoco.mj_geomDistance(mjm, mjd, a, b, 0.06, ft)
                if d < best_d:
                    best_d, best_ft, best_claw, best_cab = d, ft.copy(), a, b
        return best_d * 1000.0, best_ft, best_claw, best_cab

    def _cage(f1set, f2set):
        # %2 two-claw cage (PART 1 GATE-FIX): the cable is HELD iff (a) it is SANDWICHED between the bottom
        # (f1ext) and top (f2ext) claws -- |f1_gap + Ø8 + f2_gap - mouth| <= tol -- AND (b) laterally within the
        # claw footprint -- |cable_x - claw_x| < claw half-extent (the open コ mouth faces world X = the route axis).
        d1, ft1, claw1, cab1 = _cage_pair(f1set)  # bottom claw
        d2, _ft2, _c2, _b2 = _cage_pair(f2set)  # top claw
        sand_sum = d1 + CABLE_DIAM_MM + d2
        sandwiched = bool(abs(sand_sum - MOUTH_MM) <= SAND_TOL_MM)
        vert1 = False  # f1ext fromto mostly-vertical = the bottom claw UNDER the cable (form-closure direction)
        if ft1 is not None:
            g = ft1[3:6] - ft1[0:3]
            gn = float(np.linalg.norm(g)) + 1e-9
            vert1 = bool(abs(g[2]) / gn > 0.6)
        lateral_mm = 9e9
        if claw1 >= 0 and cab1 >= 0:
            lateral_mm = abs(float(mjd.geom_xpos[cab1][0] - mjd.geom_xpos[claw1][0])) * 1e3
        lateral_ok = bool(lateral_mm < LATERAL_MAX_MM)
        held = bool(sandwiched and lateral_ok)
        return {
            "f1": round(d1, 3),
            "f2": round(d2, 3),
            "sand": round(sand_sum, 2),
            "sandwiched": sandwiched,
            "f1_vert": vert1,
            "lat": round(lateral_mm, 2),
            "lat_ok": lateral_ok,
            "held": held,
        }

    def _cable_z():
        wp.synchronize()
        return float(np.mean(state.body_q.numpy()[cable_bodies, 2]))

    def _seg_z_mm(y_ref):
        # gripped-segment z [mm]: the cable bodies WITHIN the grasp span (|Y - y_ref| <= GHS) -- the held middle
        # that travels to the clip + seats. NOT the whole-cable mean (the 600mm rod's far ends dilute it = the
        # M-Grasp-engage artifact). Seated z~=809 (GROOVE_CENTER_Z); resting on the clip top ~834.
        wp.synchronize()
        bq = state.body_q.numpy()[cable_bodies]
        m = np.abs(bq[:, 1] - y_ref) <= GHS
        return float(np.mean(bq[m, 2]) if np.any(m) else np.mean(bq[:, 2])) * 1e3

    def _arm_split():
        # split BOTH claw-sets into (f1_L, f1_R, f2_L, f2_R) by world-Y about the grasp centre.
        mujoco.mj_forward(mjm, mjd)
        gy = mjd.geom_xpos[:, 1]
        return (
            [g for g in f1_geoms if gy[g] < GRASP_YC],
            [g for g in f1_geoms if gy[g] >= GRASP_YC],
            [g for g in f2_geoms if gy[g] < GRASP_YC],
            [g for g in f2_geoms if gy[g] >= GRASP_YC],
        )

    # --- §運用14 GL-free render (mujoco.Renderer + matplotlib, like M-Grasp-engage-1) ---
    _renderer = None
    _frames_dir = os.path.join(output_dir or ".", "_route_frames")
    _fidx = [0]
    _cams = []
    if record_video:
        import matplotlib

        matplotlib.use("Agg")
        os.makedirs(_frames_dir, exist_ok=True)
        for _old in os.listdir(_frames_dir):
            if _old.endswith(".png"):
                os.remove(os.path.join(_frames_dir, _old))
        _renderer = mujoco.Renderer(mjm, height=480, width=640)
        mjm.vis.headlight.ambient[:] = [0.5, 0.5, 0.5]
        mjm.vis.headlight.diffuse[:] = [0.85, 0.85, 0.85]
        _mx = 0.5 * (x_grasp + x_clip)
        _my = 0.5 * (0.0 + y_clip)  # diagonal-route midpoint Y (grasp centre 0 -> off-centre clip y_clip)
        _camspec = [
            ([_mx, _my, 0.85], 90.0, -6.0, 0.46, "side X-Z: aerial diagonal transport, cable held?"),
            ([x_clip, y_clip, 0.83], 0.0, -14.0, 0.24, "front Y-Z @clip: steep slot-descent into the groove?"),
            ([_mx, _my, 0.86], 235.0, -22.0, 0.50, "oblique diagonal"),
        ]
        if os.environ.get("CLIP_DELTAH", "0") == "1" or os.environ.get("S13_TAIL_HOLD", "0") == "1":
            # %3 video-confirm probe (2026-06-30): add overhead + a tight FRONT zoom on body30<->clip (the delta-h
            # escape / B tail-hold retention) + a tight zoom on the adjacent-below region (claw <-> clip Y-edge =
            # the re-grasper claw). Shared by CLIP_DELTAH and the S13_TAIL_HOLD (direction-B) retention probe.
            _camspec += [
                ([x_clip, y_clip, 0.81], 90.0, -82.0, 0.30, "overhead: seat + claws (top-down)"),
                ([x_clip, y_clip, 0.815], 0.0, -10.0, 0.085, "ZOOM front: body30 in the OPEN-TOP groove (escape?)"),
                ([x_clip, y_clip - 0.013, 0.808], 28.0, -8.0, 0.11, "ZOOM: adjacent-below claw <-> clip Y-edge"),
            ]
        if os.environ.get("S13_FEED", "0") == "1":
            # しごき slide-through (option-1 CORRECTED): CLAW-LOCAL zoom on the FEED hand. (a) FRONT Y-Z spanning
            # the seat AND the feed lane -> the cable runs left-right (Y); SLIDE = the cable stays put while the
            # finger moves; DRAG = the cable moves with the finger. (b) SIDE X-Z tight on the feed claw -> the
            # cradle wrap. The seat (clip groove) is kept in (a) throughout.
            _camspec += [
                (
                    [x_clip, y_clip - 0.020, 0.812],
                    0.0,
                    -10.0,
                    0.17,
                    "ZOOM front Y-Z: seat + FEED hand (cable SLIDE vs DRAG)",
                ),
                ([x_clip, y_clip - 0.040, 0.810], 90.0, -10.0, 0.11, "ZOOM side X-Z: FEED claw cradles cable"),
            ]
        if _ROUTE_C2:
            # %3 Rs C1->C2 routing: (a) OVERHEAD over both clips + the cable path, (b) a FRONT Y-Z spanning the C1
            # seat and the L guide toward C2, (c) a CLAW-LOCAL zoom on the L half-clamp (slide vs drag), (d) an
            # oblique of both arms. lookat = the C1<->C2 midpoint so both clips stay in frame.
            _midx, _midy = 0.5 * (x_clip + c2x), 0.5 * (y_clip + c2y)
            _camspec += [
                ([_midx, _midy, 0.81], 90.0, -80.0, 0.42, "OVERHEAD: C1+C2 + cable path (both clips)"),
                ([_midx, _midy, 0.83], 0.0, -12.0, 0.36, "front Y-Z: C1 seat + L half-clamp GUIDE toward C2"),
                ([x_clip, y_clip - 0.030, 0.812], 35.0, -8.0, 0.13, "ZOOM L claw: half-clamp + cable SLIDE vs DRAG"),
                ([_midx, _midy, 0.85], 235.0, -22.0, 0.46, "oblique: both arms, C1->C2 route"),
            ]
            # §運用14 clip coloring for the mj render: C1 green / C2 cyan (geom_rgba is render-only, no physics).
            for _cg in _clip_geoms():
                mjm.geom_rgba[_cg] = [0.20, 0.80, 0.35, 1.0]
            for _cg in _clip2_geoms():
                mjm.geom_rgba[_cg] = [0.10, 0.70, 0.92, 1.0]
        for _la, _az, _el, _d, _t in _camspec:
            _c = mujoco.MjvCamera()
            _c.type = mujoco.mjtCamera.mjCAMERA_FREE
            _c.lookat[:] = _la
            _c.distance, _c.azimuth, _c.elevation = _d, _az, _el
            _cams.append((_t, _c))

    # L/R EE label overlay (Rs frame-clarity 2026-06-30): R = +Y-side arm (anchor/holder, ROBOT_RIGHT_BASE Y=+0.35),
    # L = -Y-side arm (mover/しごき, ROBOT_LEFT_BASE Y=-0.35). get_ee_positions returns (left, right).
    _LABEL_LR = bool(record_video and (os.environ.get("S13_FEED", "0") == "1" or _ROUTE_C2))
    _LABEL_CLIPS = bool(record_video and _ROUTE_C2)  # draw C1/C2 clip labels for the routing video
    _fovy = float(mjm.vis.global_.fovy) if (record_video and mjm is not None) else 45.0

    def _world_to_pixel(p, cam, W=640, H=480):  # project a world pt to image px for a FREE MjvCamera
        azr, elr = np.radians(cam.azimuth), np.radians(cam.elevation)
        fwd = np.array([np.cos(elr) * np.cos(azr), np.cos(elr) * np.sin(azr), np.sin(elr)])  # camera -> lookat
        eye = np.array(cam.lookat, dtype=float) - cam.distance * fwd
        right = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
        rn = float(np.linalg.norm(right))
        if rn < 1e-9:
            return None
        right /= rn
        up = np.cross(right, fwd)
        rel = np.array(p, dtype=float) - eye
        zc = float(np.dot(rel, fwd))
        if zc <= 1e-6:
            return None
        f = (H / 2.0) / np.tan(np.radians(_fovy) / 2.0)
        px = W / 2.0 + f * float(np.dot(rel, right)) / zc
        py = H / 2.0 - f * float(np.dot(rel, up)) / zc
        if -25 <= px <= W + 25 and -25 <= py <= H + 25:
            return float(px), float(py)
        return None

    def _cap(phase):
        if _renderer is None:
            return
        import matplotlib.pyplot as plt

        mujoco.mj_forward(mjm, mjd)
        imgs = []
        for _nm, _c in _cams:
            _renderer.update_scene(mjd, camera=_c)
            _im = _renderer.render().astype(np.float32) * 1.3
            imgs.append(np.clip(_im, 0, 255).astype(np.uint8))
        _ncw = len(imgs)
        fig, axes = plt.subplots(1, _ncw, figsize=(15, 4.6) if _ncw <= 3 else (5.0 * _ncw, 4.6))
        for ax, im, (nm, _c2) in zip(axes, imgs, _cams):
            ax.imshow(im)
            ax.axis("off")
            ax.set_title(nm, fontsize=7.5, color="0.3")
            if _LABEL_LR:
                try:
                    _pl_ee, _pr_ee = get_ee_positions(state, scene_info)
                    # label at CLAW level (EE - ~0.24m in Z = the pinch/claw the zoom cameras frame), NOT the EE
                    # body (~0.25m higher -> off the tight zoom frames). X,Y still identify L(-Y) vs R(+Y).
                    _pl = (float(_pl_ee[0]), float(_pl_ee[1]), float(_pl_ee[2]) - 0.24)
                    _pr = (float(_pr_ee[0]), float(_pr_ee[1]), float(_pr_ee[2]) - 0.24)
                    for _pp, _lab, _col in ((_pl, "L", "#19e64b"), (_pr, "R", "#ff2bd6")):
                        _pxy = _world_to_pixel(_pp, _c2)
                        if _pxy is not None:
                            ax.text(
                                _pxy[0],
                                _pxy[1],
                                _lab,
                                color=_col,
                                fontsize=11,
                                fontweight="bold",
                                ha="center",
                                va="center",
                                clip_on=True,
                                bbox=dict(boxstyle="round,pad=0.12", fc="black", ec=_col, alpha=0.55),
                            )
                except Exception:  # noqa: BLE001
                    pass
            if _LABEL_CLIPS:
                try:
                    for _cp, _clab, _ccol in (
                        ((x_clip, y_clip, CLIP1_Z + _clip_float_z + 0.026), "C1", "#27e060"),
                        ((c2x, c2y, CLIP1_Z + _clip_float_z + 0.026), "C2", "#19c8ee"),
                    ):
                        _cpxy = _world_to_pixel(_cp, _c2)
                        if _cpxy is not None:
                            ax.text(
                                _cpxy[0],
                                _cpxy[1],
                                _clab,
                                color=_ccol,
                                fontsize=10,
                                fontweight="bold",
                                ha="center",
                                va="center",
                                clip_on=True,
                                bbox=dict(boxstyle="round,pad=0.12", fc="black", ec=_ccol, alpha=0.6),
                            )
                except Exception:  # noqa: BLE001
                    pass
        _supt = (
            f"C1->C2 §運用14 ({DEVICE}) — seat C1 (full-clamp) -> L HALF-unclamp -> guide toward C2 — {phase}"
            if _ROUTE_C2
            else f"M-Route §運用14 ({DEVICE}) — centred grasp+lift + DIAGONAL transport "
            f"GX0.30,Y0 -> clip({x_clip:.2f},{y_clip:+.2f}) + drop-in seat@809 — {phase}"
        )
        fig.suptitle(_supt, fontsize=8.5)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.01, wspace=0.02)
        fig.savefig(os.path.join(_frames_dir, f"f{_fidx[0]:05d}.png"), dpi=98)
        plt.close(fig)
        _fidx[0] += 1

    # seeds + settle
    seed_l = [3.194257, -1.979768, 1.6, -1.853054, 2.0, -1.518132]
    seed_r = [-0.052664, -1.161825, -1.6, -1.288538, -2.0, -1.62346]
    fk_jq = fk_state.joint_q.numpy()
    fk_jq[0:ARM_DOF] = seed_l
    fk_jq[JOINTS_PER_ARM : JOINTS_PER_ARM + ARM_DOF] = seed_r
    for j in GRIPPER_JOINT_RANGE:
        fk_jq[j] = 0.0
        fk_jq[JOINTS_PER_ARM + j] = 0.0
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
    state = model.state()
    for _ in range(10):
        state = physics_step(model, state, solver, contacts, scene_info)

    # PRE-STEP caveat-a: re-centre GRASP_YC on the SETTLED cable Y (the cable bodies within the grasp region),
    # preserving the 88mm span (arms = GRASP_YC +- GHS). Symmetrises the L/R f1ext for the drag.
    # %3 over-void test (Rs (b) routing-port auth, 2026-06-29): re-centre the grasp on S6_ENGAGE_YC (= the
    # void+clip Y) so grasp+void+clip CO-LOCATE at C1-over-void (the banked grasp_y=None strategy-ii config,
    # build:1066). DEFAULT S6_ENGAGE_YC=0 -> _grasp_at=0 -> |Y-0|<0.10 = the array centre = BYTE-IDENTICAL.
    _grasp_at = float(os.environ.get("S6_ENGAGE_YC", "0.0"))
    wp.synchronize()
    _cy_all = state.body_q.numpy()[cable_bodies, 1]
    _near = _cy_all[np.abs(_cy_all - _grasp_at) < 0.10]  # grasp-region cable bodies (|Y - grasp_at|<100mm)
    GRASP_YC = float(np.mean(_near)) if _near.size else _grasp_at
    print(
        f"  [S6_ROUTE] caveat-a: settled-cable-centre GRASP_YC={GRASP_YC * 1e3:+.2f}mm "
        f"(grasp_at={_grasp_at * 1e3:+.0f}mm arms +-{GHS * 1e3:.0f}mm = 88 span)"
    )

    # W0-e F-1b (Y-phase retreat, spec v0.9 + %12 (A)-injection 2026-07-05): shift the grasp centre GRASP_YC by
    # a common-mode Δy so the WHOLE route forms the buckle at the TARGET phase (== S6_ENGAGE_YC grasp-Y knob class;
    # the C1_SEAT descent target stays FULLY nominal). B1 = phase-periodic (floor_mod(dy,15)->7.5), B2 = absolute
    # one-sided ([10.5,13.5]->10.0). offset-gated (dy!=0) + W0E_F1B flag -> (0,0) BYTE-IDENTICAL (no shift/print).
    # config-derived operand (NO node-state read; bright-line 4). SIM-ONLY: node-lattice artifact (real cable has
    # no node phase) -- excluded from the real playbook. provenance: cuda:0 + build sha (PREREG U).
    _dy_off_mm = float(scene_info.get("cable_xy_offset", (0.0, 0.0))[1]) * 1e3
    if _dy_off_mm != 0.0 and os.environ.get("W0E_F1B", "1") == "1":
        _dphase = _dy_off_mm % 15.0  # Python floor-mod (B1 operand; -10 -> 5)
        _dygr = None
        _f1b_mode = None
        # W0-e F-1b'' 150mm band re-derivation (mapping B, Rs "進めて" 2026-07-06, two-key agree): ADOPT snap-DOWN only.
        # phi in (0,7.5] -> Delta = -phi (snap grasp dy to the nearest LOWER 15-lattice node). phi>7.5 (snap-UP) NOT
        # adopted -> falls through to the committed B1/B2 bands (== 81-run behavior on phi10 cols, known fail annotated).
        # snap-down REPLACES B1 [2.5,6.5] (its 7.5 target is counterproductive at 150mm, PREREG-confirmed; snap-down's
        # if is FIRST -> precedence). production flag W0E_F1B_SNAPDOWN. offset-gated (dy!=0) -> C-0 (0,0) byte-id UNTOUCHED.
        if os.environ.get("W0E_F1B_SNAPDOWN", "0") == "1" and 0.0 < _dphase <= 7.5:
            _dygr = -_dphase
            _f1b_mode = "SNAPDOWN(phi->0)"
        elif 2.5 <= _dphase <= 6.5:  # B1 phase-periodic band -> retreat phase to 7.5 (cross-period correct)
            _dygr = _dphase - 7.5
            _f1b_mode = "B1-retreat"
        elif 10.5 <= _dy_off_mm <= 13.5:  # B2 absolute one-sided band (positive dy) -> retreat to dy 10.0
            _dygr = _dy_off_mm - 10.0
            _f1b_mode = "B2-retreat"
        if _dygr is not None:
            _dygr = float(np.clip(_dygr, -7.5, 7.5))  # |Delta_y| <= 7.5mm (H2; observed max 5.0)
            GRASP_YC += _dygr * 1e-3
            print(
                f"  [W0E-F1B] {_f1b_mode}: dy={_dy_off_mm:+.2f}mm phi={_dphase:.2f} Delta={_dygr:+.2f}mm "
                f"GRASP_YC={GRASP_YC * 1e3:+.2f}mm; SIM-ONLY node-lattice artifact"
            )

    # fix-5 (Rs A / Opt-1, 2026-07-03): X analog of caveat-a -- re-centre x_grasp on the SETTLED cable X,
    # offset-gated (dx != 0 only; scene_info :1668 collapses None/(0,0) -> (0,0) so None / (0,dy) / nominal
    # keep the constant-X banked trajectory = byte-identical BY CONSTRUCTION). Cable || Y -> region X approx
    # const -> mean well-defined. Fixes b2_cpA_reach_screen_finding.md (canonical route had ZERO cable-X
    # follow; the legacy do_p1_grasp grasp_dy is inert on this path).
    if scene_info.get("cable_xy_offset", (0.0, 0.0))[0] != 0.0:
        _cx_near = state.body_q.numpy()[cable_bodies, 0][np.abs(_cy_all - _grasp_at) < 0.10]  # same mask as caveat-a
        if _cx_near.size:
            x_grasp = float(np.mean(_cx_near))
        print(
            f"  [S6_ROUTE] caveat-a-X: settled-cable-X x_grasp={x_grasp * 1e3:+.2f}mm "
            f"(nominal GRASP_X={GRASP_X * 1e3:+.0f}mm, delta={(x_grasp - GRASP_X) * 1e3:+.2f}mm)"
        )

    def tgt(x, z):
        return (x, GRASP_YC - GHS, z), (x, GRASP_YC + GHS, z)

    def tgt2(x, yc, z):
        # M-Route-2 C1: diagonal target with a MOVING grasp centre yc (interp GRASP_YC -> y_clip); the 88mm span is
        # preserved (yc +- GHS = INVARIANT#2). For y_clip=0 (centred M-Route-1) tgt2(x, GRASP_YC, z) == tgt(x, z).
        return (x, yc - GHS, z), (x, yc + GHS, z)

    def _w0e_guarded_cx(y_ref, x_ref):
        # W0-e common guarded crossing-X selector (spec v0.9 cluster A): mean cable-body X within the Y window
        # |y-y_ref|<=7.5mm AND the X plausibility window |x-x_ref|<=30mm (offline-validated: n=1, 0 tail-hijack
        # on all 81 cells, validate_measurands.py:54-57). Returns (mean_x_m, n_nodes); (None, 0) if the window is
        # empty (plausibility reject). Reads the LIVE `state` by closure (same pattern as _zc1).
        wp.synchronize()
        _P = state.body_q.numpy()[cable_bodies]
        _m = (np.abs(_P[:, 1] - y_ref) <= 0.0075) & (np.abs(_P[:, 0] - x_ref) <= 0.030)
        if not _m.any():
            return None, 0
        return float(_P[_m, 0].mean()), int(_m.sum())

    # --- GRASP + LIFT (reuse the validated M-Grasp-engage-1 orchestration) ---
    _ph("GRASP_HOVER")
    ok = {}
    state, ok["hover"] = ik_move_both(
        model,
        state,
        scene_info,
        solver,
        contacts,
        *tgt(x_grasp, z_high),
        label="ROUTE-HOVER",
        converge_mm=8.0,
        speed_factor=0.2,
        warmstart_jq=fk_jq,
    )
    _cap("HOVER")
    _ph("GRASP_DESCEND")
    ok["descend"] = True
    for k in range(1, 9):
        zk = z_high + (z_grasp - z_high) * k / 8
        _dl, _dr = _inject_detour(
            "GRASP_DESCEND", k, 8, *tgt(x_grasp, zk)
        )  # DQ7 (ii): kick-and-recover (None-path passthrough)
        state, okk = ik_move_both(
            model,
            state,
            scene_info,
            solver,
            contacts,
            _dl,
            _dr,
            label=f"ROUTE-DESCEND{k}/8",
            converge_mm=2.5,
            speed_factor=0.25,
        )
        ok["descend"] = ok["descend"] and bool(okk)
        _cap(f"DESCEND {k}/8")
    # 2-PHASE cage90 close (validated capture-then-gentle)
    _ph("GRASP_CLOSE")
    CAGE_FRAC = 0.9
    cage_rad = GRIPPER_DRIVER_OPEN_RAD + (GRIPPER_DRIVER_CLOSE_RAD - GRIPPER_DRIVER_OPEN_RAD) * CAGE_FRAC
    _set_gripper_target(control, driver_joints, cage_rad)
    for _ in range(30):
        state = physics_step(model, state, solver, contacts, scene_info)
    _cap("CAGE 90%")
    for ck in range(1, 13):
        ctgt = cage_rad + (GRIPPER_DRIVER_CLOSE_RAD - cage_rad) * ck / 12
        _set_gripper_target(control, driver_joints, ctgt)
        for _ in range(12):
            state = physics_step(model, state, solver, contacts, scene_info)
        if ck % 3 == 0:
            _cap(f"CLAMP {ck}/12")
    for _ in range(40):
        state = physics_step(model, state, solver, contacts, scene_info)
    _cap("CLOSED")
    # M-Hook-1: capture the EE->gripped-cable z offset at close (BEFORE the route), the banked
    # r_s71_clip_dropin_72:216-218 convention. NOT re-measured after the route, so the drag-loosening
    # (cable migrates UP in the cage) is NOT compensated -> the drop-in faithfully TESTS %9's integration
    # concern (does the loosened post-route cable still seat at 809, or rest high on the clip top ~834?).
    ee_off = float(get_ee_positions(state, scene_info)[1][2]) - _seg_z_mm(GRASP_YC) / 1e3
    _ph("LIFT")
    ok["lift"] = True
    for k in range(1, LIFT_SUBSTEPS + 1):
        zl = z_grasp + LIFT_M * k / LIFT_SUBSTEPS
        state, okk = ik_move_both(
            model,
            state,
            scene_info,
            solver,
            contacts,
            *tgt(x_grasp, zl),
            label=f"ROUTE-LIFT{k}/{LIFT_SUBSTEPS}",
            converge_mm=3.0,
            speed_factor=0.3,
        )
        ok["lift"] = ok["lift"] and bool(okk)
        _cap(f"LIFT {k}/{LIFT_SUBSTEPS}")

    # --- CONTINUOUS RETENTION GATE (PART 1 GATE-FIX: %2 two-claw cage log:6738) sampled at EVERY waypoint ---
    f1_L, f1_R, f2_L, f2_R = _arm_split()
    wps = []  # per-waypoint dicts

    def _sample(label, xcur):
        cgL = _cage(f1_L, f2_L)
        cgR = _cage(f1_R, f2_R)
        cz = _cable_z() * 1e3
        okL, okR = cgL["held"], cgR["held"]  # %2 cage: SANDWICHED between both claws AND lateral within footprint
        rec = {"wp": label, "x": round(xcur, 3), "L": cgL, "R": cgR, "okL": okL, "okR": okR, "cable_z_mm": round(cz, 1)}
        wps.append(rec)
        print(
            f"  [S6_ROUTE] wp={label:12s} x={xcur:.3f} "
            f"L[f1/f2={cgL['f1']:+.2f}/{cgL['f2']:+.2f} sum={cgL['sand']:.1f} lat={cgL['lat']:.1f} held={okL}] "
            f"R[f1/f2={cgR['f1']:+.2f}/{cgR['f2']:+.2f} sum={cgR['sand']:.1f} lat={cgR['lat']:.1f} held={okR}] "
            f"cable_z={cz:.0f}mm"
        )
        return rec

    cable_z_start = _cable_z() * 1e3
    _sample("START(lift)", x_grasp)
    # ROUTE: M-Route-2 C1 DIAGONAL drag -- both arms together from (GX, GRASP_YC) to (x_clip, y_clip) at z_lift,
    # interpolating BOTH xk AND the grasp-centre yck while preserving the 88mm span (yck +- GHS). For y_clip=0
    # (centred M-Route-1) yck stays GRASP_YC so this is byte-equivalent to the prior X-only route. INVARIANT#1:
    # both arms move (different MIRRORED joint-motions -- LEFT stretches, RIGHT folds -- neither parked);
    # INVARIANT#2: span fixed at 2*GHS, bases untouched. The y_clip drag is the off-centre TEST (5-CC reach wall).
    _ph("ROUTE_C1")
    ok["route"] = True
    for k in range(1, N_ROUTE + 1):
        xk = x_grasp + (x_clip - x_grasp) * k / N_ROUTE
        yck = GRASP_YC + (y_clip - GRASP_YC) * k / N_ROUTE
        state, okk = ik_move_both(
            model,
            state,
            scene_info,
            solver,
            contacts,
            *tgt2(xk, yck, z_lift),
            label=f"ROUTE{k}/{N_ROUTE}",
            converge_mm=3.0,
            speed_factor=0.3,
        )
        ok["route"] = ok["route"] and bool(okk)
        _sample(f"ROUTE{k}/{N_ROUTE}", xk)
        _cap(f"ROUTE {k}/{N_ROUTE} (X={xk:.3f} Y={yck:+.3f})")
    # per-arm reach residual at the C1 endpoint: under-cable realization of the MARGINAL 2.21mm aerial probe
    # (log:6750) + the asymmetric-drag WATCH. resid = ||EE - commanded target||; lateral = |EE_y - base_y| (the
    # LEFT arm stretches to ~0.456 = near reach, the RIGHT folds to ~0.156 = the asymmetry). A blown residual =
    # the marginal reach became a WALL under cable -> the route gate (ok["route"]) catches it -> STOP->%9.
    _pl, _pr = get_ee_positions(state, scene_info)
    _tl, _tr = tgt2(x_clip, y_clip, z_lift)
    resid_l_mm = float(np.linalg.norm(np.array(_pl) - np.array(_tl))) * 1e3
    resid_r_mm = float(np.linalg.norm(np.array(_pr) - np.array(_tr))) * 1e3
    lat_l_m = abs(float(_pl[1]) - ROBOT_LEFT_BASE[1])
    lat_r_m = abs(float(_pr[1]) - ROBOT_RIGHT_BASE[1])
    # the STRETCH arm = the larger-lateral (near-reach, fragile) one -- DERIVED from the data, not hardcoded: for a
    # +Y clip (C1) the LEFT stretches; for a -Y clip (C5) the RIGHT stretches (the mirror). The OTHER arm FOLDS.
    stretch_arm = "L" if lat_l_m > lat_r_m else "R"
    print(
        f"  [S6_ROUTE] endpoint per-arm reach: residual L={resid_l_mm:.2f}mm R={resid_r_mm:.2f}mm | "
        f"lateral L={lat_l_m:.3f}m R={lat_r_m:.3f}m -> {stretch_arm} STRETCHES (near-reach, fragile), the other "
        f"FOLDS -- asymmetric diagonal drag to clip Y={y_clip:+.3f}, both arms moving (INVARIANT#1)"
    )
    # hold at the clip (aerial, pre-hook) + final sample
    for _ in range(60):
        state = physics_step(model, state, solver, contacts, scene_info)
    _sample("END(hold)", x_clip)
    _cap("END (aerial @ clipX, pre-hook=M-Hook-1)")
    raise NotImplementedError("route body continues: ROUTE C1->C2 guide = A4c (build plan v1.8 section 13.7)")


class RouteExecutor(rc.RouteInterfaceV1):
    """Real route-executor: faithful C1->C2 route engine replacing ``NominalRouteStub`` (§13; charter D-1=C).

    Implements the :class:`route_env_config.RouteInterfaceV1` contract. The gripper is driven by the
    model-level POSITION servo (``grasp_actuation=True``); every per-step kinematic joint write excludes the
    gripper coords (:func:`apply_arm_only_write_broadcast` / :func:`apply_arm_only_write_perworld`) and each
    reset restores them from the banked state (:func:`apply_banked_restore`) -- both co-derived from
    ``_GRIPPER_COORDS_LOCAL`` (§13.0-2 G7), so no coordinate is excluded-from-writes yet not restored.

    ``reset_to_phase`` keeps the SCALAR ``k`` contract (per-world curriculum start-mix is deferred to the
    trainer, §13.2 F14/F15). ``step_target`` is the env-facing per-step facade; the self-driving byte-repro
    path (``run_route``) and the real per-step targets are added by the route-orchestration extraction
    (subsequent build chunks; faithful copy of the locked ``_run_mujoco_grasp_route``:3692).
    """

    def __init__(self, arm_q_start, arm_qd_start, horizon, state_0=None, control=None, state_bank=None):
        """Wire the per-world index maps + optional physics handles.

        Args:
            arm_q_start: Per-world arm ``joint_q`` start indices (env-computed; cable FREE-root => q != qd).
            arm_qd_start: Per-world arm ``joint_qd`` start indices.
            horizon: Episode horizon [steps].
            state_0: The Newton physics state to re-pose at reset (None for pure-index construction/tests).
            control: The Newton control whose ``joint_target_pos`` carries the servo targets (None => skip seed).
            state_bank: Optional ``{k: banked_dict}`` phase-k state bank (empty => reset is env-authoritative).
        """
        self._maps = build_perworld_index_maps(arm_q_start, arm_qd_start)
        self._horizon = int(horizon)
        self._state_0 = state_0
        self._control = control
        self._state_bank = dict(state_bank) if state_bank else {}
        self._requested_phase = 0
        if control is not None:
            servo_seed_assert(control.joint_target_pos.numpy(), self._maps["all_driver_dofs"])

    def reset_to_phase(self, k: int) -> None:
        """Fork all worlds to phase ``k``'s banked state (SCALAR ``k``; §13.2/§13.3/§13.4).

        Restores the banked arm + all-16 gripper ``joint_q``/``joint_qd`` + the banked grip target
        (banked-CLOSED for a gripped phase, NOT a blanket-OPEN). Phase-0 / no bank => no-op (the env-core
        reset is authoritative), matching the stub. Per-world different-``k`` is deferred to the trainer.
        """
        self._requested_phase = int(k)
        banked = self._state_bank.get(int(k))
        if banked is None or self._state_0 is None:
            return  # phase-0 / no bank / index-only construction: the env-core reset stands
        phys_jq = self._state_0.joint_q.numpy()
        phys_jqd = self._state_0.joint_qd.numpy()
        jtp = self._control.joint_target_pos.numpy()
        apply_banked_restore(phys_jq, phys_jqd, jtp, self._maps, banked)
        self._state_0.joint_q.assign(phys_jq)
        self._state_0.joint_qd.assign(phys_jqd)
        self._control.joint_target_pos.assign(jtp)

    def step_target(self, t: int) -> tuple:
        """Return the per-step route packet ``(target_6d, phase_id, grip_2, is_dual)`` for RL step ``t``.

        The real per-step targets come from the extracted route orchestration (faithful copy of the locked
        ``_run_mujoco_grasp_route``:3692) -- added by the route-orchestration build chunks. Not yet wired.
        """
        raise NotImplementedError("step_target route orchestration is the next build chunk (§13.7)")
