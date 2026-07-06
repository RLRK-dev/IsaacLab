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

import numpy as np
import route_env_config as rc
from configs.task_config import (
    GRIP_HALF_SPAN,
    GRIPPER_DRIVER_JOINT_IDX,
    GRIPPER_DRIVER_OPEN_RAD,
    GRIPPER_JOINT_RANGE,
    JOINTS_PER_ARM,
)

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
