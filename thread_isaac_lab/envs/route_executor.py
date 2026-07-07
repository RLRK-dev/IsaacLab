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

import newton
import numpy as np
import route_env_config as rc
import warp as wp
from configs.task_config import (
    EE_BODY_OFFSET,
    FRANKA_NUM_JOINTS,
    GRIP_HALF_SPAN,
    GRIPPER_DRIVER_JOINT_IDX,
    GRIPPER_DRIVER_OPEN_RAD,
    GRIPPER_JOINT_RANGE,
    JOINTS_PER_ARM,
    MAX_MOVE_STEPS,
    SIM_SUBSTEPS,
    STEPS_PER_CM,
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
