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
from configs.task_config import (
    GRIP_HALF_SPAN,
    GRIPPER_DRIVER_JOINT_IDX,
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
