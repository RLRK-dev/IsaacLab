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

import json
import math as _math
import os
import sys

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
    GRIPPER_DRIVER_HALF_OPEN_RAD,
    GRIPPER_DRIVER_JOINT_IDX,
    GRIPPER_DRIVER_OPEN_RAD,
    GRIPPER_JOINT_RANGE,
    GROOVE_CENTER_Z,
    JOINTS_PER_ARM,
    MAX_MOVE_STEPS,
    ROBOT_LEFT_BASE,
    ROBOT_RIGHT_BASE,
    SIM_SUBSTEPS,
    STEPS_PER_CM,
    TABLE_HEIGHT,
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

# --- comp1 recorded_replay: cadence + 15->6 phase map (Layer-B step_target; %12 ruling 2026-07-07 16:04) ---
# Cadence is SINGLE-SOURCE with the banked BC/trainer base (route_demo_to_bc.py:34-35 / :255-258): the
# per-step target = ee_pos at the NEXT control frame (fork-(iv) base == achieved-path waypoint, %12 15:44 +
# route_demo_to_bc.py:13/:287; ee_tgt_pos = macro-leg segmentation ONLY, :854). cf = arange(0, LAST+1, cad).
_REC_CADENCE = 10  # == PHYSICS_STEPS_PER_RL (route_demo_to_bc.py:34 / newton_route_env.py:237)
_REC_LAST_CTRL_FRAME = 7700  # route_demo_to_bc.py:35 (last control frame; 6-frame zero-motion tail dropped)
# Recorded 15-phase (PHASES15, route_demo_to_bc.py:58) phase_id -> 6-phase G-clock (N_ROUTE_PHASES=6,
# route_env_config:46). %12 RULING 2026-07-07 16:04 = the single-source (no prior spec; grep=0). Grounded in
# the phase names + the consumer boundaries (newton_route_env _active_clip_xy phase<3=C1 / _dual_and_grip
# phase==3=G4-transit / phase>=4=C2). ⚠ CC5-2: phase does NOT drive grip/is_dual (route_env_config:152-153);
# phase drives ONLY clip-selection + obs-onehot + state_bank keying.
_RECORDED_PHASE_TO_G = {
    -1: 0,  # pre-start -> G1
    0: 0,
    1: 0,
    2: 0,  # GRASP_HOVER/DESCEND/CLOSE -> G1 (grasp)
    3: 1,  # LIFT -> G2
    4: 2,
    5: 2,
    6: 2,  # ROUTE_C1/C1_SEAT/C1_PIN -> G3 (C1 route+seat)
    7: 3,
    8: 3,
    9: 3,
    10: 3,
    11: 3,  # L_HALF_UNCLAMP/R_UNCLAMP_RISE/GUIDE_C2/GUIDE_PRELIFT/C2_REGRASP -> G4 (regrasp transit; ends at recage-latch C2_REGRASP)
    12: 4,  # C2_TRANSPORT -> G5 (first C2-dual)
    13: 5,
    14: 5,  # C2_DUAL_SEAT/C2_SETTLE -> G6 (C2 seat+settle)
}
# grip threshold: recorded grip_cmd radians -> gripping {0,1}. HALF_OPEN (0.69) is the L_HALF_UNCLAMP hold
# point (still gripping the cable), so >=HALF_OPEN == gripping; below == reaching/open. This reproduces the
# transit semantics (L half-unclamp holds=1, R re-grasp opens=0) WITHOUT a phase table (CC5-2).
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


def patch_settled_fk_gripper(settled_fk_jq, phys_jq, arm_q_start0):
    """Overwrite the FK-constant gripper coords in the reset-init source with world-0 PHYSICS coords (CC4-CH5).

    The env-core reset re-poses arms + gripper from ``settled_fk_jq`` (a 28-wide FK arm row). The gripper
    coords there are the ``FINGER_OPEN_POS`` FOLLOWER constants, NOT a servo-settled config -- seeding them
    at reset risks a 4-bar follower BRANCH-FLIP under the POSITION servo. Mirror of the AR:866-872 patch:
    replace the gripper coords ``_GRIPPER_COORDS_LOCAL`` ({6-13, 20-27}) with world-0's POST-SETTLE physics
    gripper config (route step-0 = OPEN both arms, dual-arm ADAPT of the AR L-close mirror) so the 28-wide
    reset-init seeds a consistent physics-branch gripper. ``comp3`` flag-ON only; arm coords are untouched.

    Args:
        settled_fk_jq: The 28-wide FK arm row [rad] used as the reset-init source, mutated in place.
        phys_jq: The full physics ``joint_q`` array [rad] (world-0's post-settle gripper is read from it).
        arm_q_start0: World-0's arm ``joint_q`` start index into ``phys_jq``.

    Returns:
        The mutated ``settled_fk_jq``.
    """
    for gc in sorted(_GRIPPER_COORDS_LOCAL):
        settled_fk_jq[gc] = phys_jq[arm_q_start0 + gc]
    return settled_fk_jq


def build_state_bank_from_recording(recording, n_world, arm_off=0, phases=(1, 2, 3, 4, 5)):
    """Build the phase-k state bank ``{k: banked}`` from a ONE-cell recording (comp2 §8; Q3, %12 16:04).

    For each requested G-phase ``k``, the banked state is the recorded physics snapshot at the phase-``k``
    BOUNDARY -- the first frame whose recorded 15-phase ``phase_id`` maps to ``k`` via
    :data:`_RECORDED_PHASE_TO_G`. The returned per-``k`` dict matches the :func:`apply_banked_restore`
    contract EXACTLY: ``arm_q``/``arm_qd`` (world-major over ``_ARM_OVERWRITE_LOCAL``), ``gripper_q``/
    ``gripper_qd`` (world-major over sorted ``_GRIPPER_COORDS_LOCAL``), ``grip_target`` (per driver DOF,
    world-major, order ``[L, L, R, R]`` per world). Every world forks to the SAME scalar-``k`` state
    (per-world curriculum start-mix is deferred to the trainer, §13.2), so the one snapshot is tiled.

    Phase-0 (``k=0``, G1) is intentionally OMITTED: :meth:`RouteExecutor.reset_to_phase` treats a missing
    bank as a no-op and lets the env-core reset stand (matches the stub + the ``reset()`` contract).

    qvel note (comp2 design decision, %12-surfaced -- the plan said "qpos/qvel from recording" but the
    recording carries NO ``joint_qd``, only ``arm_q`` positions): banked velocities are ZERO. This is EXACT
    for the arm -- the mujoco-ko substrate zeroes arm ``joint_qd`` every step in the kinematic re-pose
    (:meth:`NewtonRouteEnv._broadcast_arm_jointq` / :func:`apply_arm_only_write_perworld`). The gripper is
    POSITION-servo-driven and its boundary ``joint_qd`` is unrecorded -> banked 0 (a momentarily still
    gripper the servo re-accelerates; benign for a curriculum fork start, re-validated live at Stage-B ⑦(b)).
    ``grip_target`` = the recorded ``grip_cmd`` (COMMANDED driver target [rad], cols ``[L, R]``), which is
    DISTINCT from the servo-lagged ACTUAL gripper ``joint_q`` restored from ``arm_q`` (verified: at a gripped
    frame ``grip_cmd``=0.7407 while the driver ``joint_q``~0.71).

    Args:
        recording: A mapping with ``arm_q`` [frames, W] (the full physics ``joint_q`` per frame; the arm
            occupies ``[arm_off, arm_off + _N_ARM_JOINTS)`` [rad]), ``grip_cmd`` [frames, 2] (cols [L, R]
            [rad]), ``phase_id`` [frames] (the recorded 15-phase clock).
        n_world: Number of worlds the env forks (banked arrays are tiled world-major over this).
        arm_off: The arm's start offset within the recorded ``arm_q`` row (single-world recording => 0).
        phases: The G-phase keys in ``[1, N_ROUTE_PHASES)`` to bank (default G2..G6; k=0 = env reset).

    Returns:
        ``{k: banked}`` for each requested ``k`` that has a boundary frame in the recording (a phase absent
        from the recording is skipped, so ``reset_to_phase(k)`` falls back to the env reset for it).
    """
    arm_q = np.asarray(recording["arm_q"], dtype=np.float32)
    grip = np.asarray(recording["grip_cmd"], dtype=np.float32)
    phase = np.asarray(recording["phase_id"]).astype(np.int64)
    n_frames = arm_q.shape[0]
    if not (grip.shape[0] == phase.shape[0] == n_frames):
        raise ValueError("recording arm_q/grip_cmd/phase_id have inconsistent frame counts")
    if arm_q.ndim != 2 or arm_q.shape[1] < arm_off + _N_ARM_JOINTS:
        raise ValueError(f"recording arm_q must be [frames, >={arm_off + _N_ARM_JOINTS}]; got {arm_q.shape}")
    if grip.shape[1:] != (2,):
        raise ValueError("recording grip_cmd must be [frames, 2] (cols [L, R])")
    # phase-map TOTAL coverage (mirror _prepare_recording): every recorded phase_id maps to exactly one G.
    uncovered = {int(p) for p in np.unique(phase)} - set(_RECORDED_PHASE_TO_G)
    if uncovered:
        raise ValueError(f"recorded phase_id {sorted(uncovered)} not in _RECORDED_PHASE_TO_G")
    g_of_frame = np.array([_RECORDED_PHASE_TO_G[int(p)] for p in phase], dtype=np.int64)
    arm_local = list(_ARM_OVERWRITE_LOCAL)  # {0-5,14-19} (12)
    grip_local = sorted(_GRIPPER_COORDS_LOCAL)  # {6-13,20-27} (16)
    bank = {}
    for k in phases:
        hits = np.nonzero(g_of_frame == int(k))[0]
        if hits.size == 0:
            continue  # phase absent in this recording -> reset_to_phase(k) falls back to the env reset
        bf = int(hits[0])  # phase-k boundary = FIRST frame mapped to k
        arm_span = arm_q[bf, arm_off : arm_off + _N_ARM_JOINTS]  # 28-wide two-arm joint_q snapshot
        g_l, g_r = float(grip[bf, 0]), float(grip[bf, 1])  # [L, R] commanded driver targets [rad]
        bank[int(k)] = {
            "arm_q": np.tile(arm_span[arm_local], n_world).astype(np.float32),
            "arm_qd": np.zeros(n_world * len(arm_local), dtype=np.float32),
            "gripper_q": np.tile(arm_span[grip_local], n_world).astype(np.float32),
            "gripper_qd": np.zeros(n_world * len(grip_local), dtype=np.float32),
            "grip_target": np.tile(np.array([g_l, g_l, g_r, g_r], dtype=np.float32), n_world),
        }
    return bank


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
# Rs-LOCKED _run_mujoco_grasp_route (test:3692-5765, the S6_GRASP_ROUTE path ending at test:5765 sys.exit;
# the monolith fn continues to test:7475 with dead env-gated paths, excluded). All inner closures are kept
# INNER-verbatim (max byte-fidelity, verbatim call sites); the module-level extract-7 shadow-serve the
# Layer B step_target facade and are held byte-identical by the section-12.4 ast drift tripwire.
#
# The ONLY non-verbatim change is the C2 F11 (A4d-2): the two C2 re-grasp ik_move_both calls take
# ik_solve_fn=_solve_ik_dual_rot explicitly instead of the monolith's runtime monkeypatch of the module
# solve_ik_dual global (no-global-mutation; the monkeypatch exception-window is thereby eliminated).
#
# ANTI-REVERT / Rs-LOCKED -- do NOT edit any line of run_route without Rs. It mirrors the FOUNDATIONAL
# ANTI-REVERT markers test:5128 (R targets the ACTUAL cable X via argmin, NOT a fixed target = the
# air-grip bug), test:5148 (square-on default C2_TILT_SIGN=0; the banked tilt is floating-cable-specific),
# and test:5290 (regrasp_ok = _at_88 AND _R_grips, NOT the both-hands-force gate). Drift is caught by the
# byte-repro harness plus a static byte-for-byte tripwire against the golden hash below (F11 delta reversed).
# =============================================================================
_ROUTE_MONOLITH_GOLDEN_SHA256 = (
    "5a47dacfd010e0beccc044c5bf820e27dcd9f1937f08ab59e704e21099eb8410"  # sha256(test:3692-5765)
)


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

    # --- ROUTE C1->C2 with HALF-UNCLAMP GUIDE (env-gate S13_ROUTE_C2=1; %3 Rs directive 2026-06-30) -------------
    # FAITHFUL choreography (NOT the S6_HOOK full-release seat -> DO_HOOK forced False above):
    #   (1) both arms clamped at C1 (route end; L=-Y@y_clip-GHS, R=+Y@y_clip+GHS).
    #   (2) SEAT C1 by pushing the cable into the groove WHILE FULLY CLAMPED (lower both to GROOVE_CENTER_Z, NO
    #       release) = "full clamp seat / InsertIntoClip".
    #   (3) L HALF-UNCLAMP (CLOSE->GRIPPER_DRIVER_HALF_OPEN_RAD 0.69, NOT full open); R KEEPS its grasp = the +Y
    #       anchor above C1 (cross-PV flag 1; without it the open-top C1 escapes). L stays ON the cable.
    #   (4) L GUIDE (しごき) toward C2 (X,Y interp at cradle height); cable slides through the L half-clamp. R holds.
    #   (5) at C2: lower L to push the cable into C2's groove. MEASURE slip(slide/drag), C1 retention (frozen seat-z
    #       + cable<->C1), C2 reach (cable<->C2), held/cradle gates, AND SEPARATELY the claw-vs-SOLID-table JAM
    #       (C2 over solid; cross-PV flag 2 = a GEOMETRY jam, distinct from the cable-physics drag).
    if _ROUTE_C2 and _clip_collidable:
        import glob as _glob
        import shutil as _shutil
        import subprocess as _subp

        LOW_WALL_TOP = (CLIP1_Z + _clip_float_z + 0.020) * 1e3  # 820mm(+float): cable-centre escape crit (low-wall top)
        L_drv, R_drv = [6, 10], [20, 24]  # per-arm gripper drivers (test:1344-1345; L=-Y arm, R=+Y arm)
        _clip1g, _clip2g, _tabg = _clip_geoms(), _clip2_geoms(), _table_geoms()
        # CLIP_FLOAT_Z CONSISTENCY READBACK (guard: clip boxes + cable SEAT Z + EE DESCENT target all raise by the SAME
        # h; TABLE_HEIGHT STAYS 0.80). A partial raise = mis-seat = INVALID. GAP = floated cable Z - table 0.80 = the
        # empty space the f1ext bottom claw cages UNDER the cable (the コ rationale; must be EMPTY = no stray geom).
        _cab_seat_target = GROOVE_CENTER_Z + _clip_float_z  # (ii) cable seated Z target
        _ee_descent_target = _cab_seat_target + ee_off  # (iii) gripper EE descent target (= seat + ee_off)
        _c1_floor_z = float(np.min([mjd.geom_xpos[g][2] for g in _clip1g])) if _clip1g else float("nan")  # (i) actual
        _c2_floor_z = float(np.min([mjd.geom_xpos[g][2] for g in _clip2g])) if _clip2g else float("nan")  # clip box z
        _gap_mm = (_cab_seat_target - TABLE_HEIGHT) * 1e3
        print(
            f"  [C2-FLOAT] CLIP_FLOAT_Z={_clip_float_z * 1e3:.1f}mm (TABLE stays {TABLE_HEIGHT * 1e3:.0f}) | "
            f"(i) clip floor geom zmin C1={_c1_floor_z * 1e3:.1f} C2={_c2_floor_z * 1e3:.1f}mm "
            f"(expect {(CLIP1_Z + _clip_float_z + 0.0025) * 1e3:.1f}) | (ii) cable SEAT target="
            f"{_cab_seat_target * 1e3:.1f}mm (=809+float) | (iii) EE descent target={_ee_descent_target * 1e3:.1f}mm "
            f"(=seat+ee_off {ee_off * 1e3:.1f}) | GAP(cable-table)={_gap_mm:.1f}mm | LOW_WALL_TOP={LOW_WALL_TOP:.0f}mm"
        )
        rc2 = {
            "clip1_geoms": len(_clip1g),
            "clip2_geoms": len(_clip2g),
            "table_geoms": len(_tabg),
            "void_x_ceiling": 0.366,
            "c2_over_solid": bool(c2x > 0.366 or not (0.090 <= c2y <= 0.210)),
        }
        print(
            f"  [C2] geoms: C1={len(_clip1g)} C2={len(_clip2g)} table={len(_tabg)} | "
            f"C1@({x_clip:.3f},{y_clip:+.3f})over-void  C2@({c2x:.3f},{c2y:+.3f})over-SOLID "
            f"(X {c2x} vs void-ceil 0.366; Y {c2y:+.3f} vs void [0.090,0.210])"
        )

        # item1 HAND-HAND clearance at ARM-LINK level (Rs core concern). MATCHES the active IK
        # DualArmLinkAvoidObjective (newton_routing_utils:192-193: dist=||pos_l-pos_r||, penetrate if dist<r_l+r_r) so
        # it is the SAME quantity COLLISION_AVOIDANCE=1 minimises. FK-model body_q (fk_state, refreshed by eval_fk in
        # ik_move_both): left link = body[l_local], right = body[FRANKA_NUM_JOINTS+r_local] (= _build_collision_objectives
        # mapping). UNCAPPED Euclidean (no 50mm mj_geomDistance ceiling) + forearm/wrist/EE spheres (NOT pad-only).
        from newton_routing_utils import COLLISION_PAIRS as _HH_PAIRS  # noqa: E402
        from newton_routing_utils import COLLISION_SPHERE_RADII as _HH_RAD  # noqa: E402

        _hh_avoid_on = os.environ.get("COLLISION_AVOIDANCE", "1") != "0"

        def _hh_clear_mm():
            bq = fk_state.body_q.numpy()
            best, bp = 9e9, None
            for _ll, _rl in _HH_PAIRS:
                _pl, _pr = np.asarray(bq[_ll][:3]), np.asarray(bq[FRANKA_NUM_JOINTS + _rl][:3])
                _c = (float(np.linalg.norm(_pl - _pr)) - (_HH_RAD[_ll] + _HH_RAD[_rl])) * 1e3
                if _c < best:
                    best, bp = _c, (_ll, _rl)
            return best, bp

        def _claw_cable_load(claw_set):  # (claw<->cable) NORMAL force + eff mu: low N=cradle, high N=grip
            mujoco.mj_forward(mjm, mjd)
            _cs, _cab = set(claw_set), set(cable_geoms)
            tot, peak, n, mu = 0.0, 0.0, 0, None
            f6 = np.zeros(6)
            for ci in range(int(mjd.ncon)):
                c = mjd.contact[ci]
                if (int(c.geom1) in _cs and int(c.geom2) in _cab) or (int(c.geom2) in _cs and int(c.geom1) in _cab):
                    mujoco.mj_contactForce(mjm, mjd, ci, f6)
                    fn = abs(float(f6[0]))
                    tot += fn
                    peak = max(peak, fn)
                    n += 1
                    if mu is None:
                        mu = float(c.friction[0])
            return tot, peak, n, mu

        def _claw_table_load(claw_set):  # (claw<->SOLID-table) NORMAL force = the geometry JAM, NOT a cable drag
            mujoco.mj_forward(mjm, mjd)
            _cs, _tb = set(claw_set), set(_tabg)
            tot, n = 0.0, 0
            f6 = np.zeros(6)
            for ci in range(int(mjd.ncon)):
                c = mjd.contact[ci]
                if (int(c.geom1) in _cs and int(c.geom2) in _tb) or (int(c.geom2) in _cs and int(c.geom1) in _tb):
                    mujoco.mj_contactForce(mjm, mjd, ci, f6)
                    tot += abs(float(f6[0]))
                    n += 1
            return tot, n

        def _claw_c2_load(
            claw_set,
        ):  # (claw<->C2-clip) NORMAL force = the soft over-penetration reaction (Rs corrected-route metric; harness only logged claw-vs-table before)
            mujoco.mj_forward(mjm, mjd)
            _cs, _c2 = set(claw_set), set(_clip2g)
            tot, n = 0.0, 0
            f6 = np.zeros(6)
            for ci in range(int(mjd.ncon)):
                c = mjd.contact[ci]
                if (int(c.geom1) in _cs and int(c.geom2) in _c2) or (int(c.geom2) in _cs and int(c.geom1) in _c2):
                    mujoco.mj_contactForce(mjm, mjd, ci, f6)
                    tot += abs(float(f6[0]))
                    n += 1
            return tot, n

        def _f1_zmin_mm(claw_set):  # bottom-claw lowest z [mm] = can it reach UNDER the cable over solid?
            mujoco.mj_forward(mjm, mjd)
            return (float(np.min([mjd.geom_xpos[g][2] for g in claw_set])) * 1e3) if claw_set else 9e9

        # (2) FULL-CLAMP SEAT: lower both arms (still CLOSED) so the gripped cable centre -> GROOVE_CENTER_Z+float.
        _ph("C1_SEAT")
        seat_ee_z = (
            GROOVE_CENTER_Z + _clip_float_z + ee_off
        )  # CLIP_FLOAT_Z: descend to the FLOATED groove (consistency)
        # W0-e F-1a (C1-seat X-follow, spec v0.9; offset-gated + W0E_F1A). Measure guarded crossing dx at ROUTE_C1
        # end (settled, pre-seat; no physics_step since the aerial hold) -> common-mode compensate the C1_SEAT
        # descent x via tgt2's shared x arg (scalar clamp BEFORE fan-out). k=4 residual re-measure (30-step settle)
        # uses the (ii) MINUS/nominal form comp<-clamp(comp-(crossing-x_clip),+-22) (%12 2026-07-05; nominal-ref
        # self-cancels). plausibility: initial reject -> comp 0 (no-comp, monotone-safe) / k=4 reject -> comp
        # MAINTAINED + loud (mid-descent comp drop = +-16-22mm arm jump = non-monotone). (0,0) BYTE-IDENTICAL
        # (comp=0.0 -> x_clip+0.0==x_clip, prints gated). CLAMP22 provenance: cuda:0 + build sha (PREREG U).
        _f1a_on = (
            float(scene_info.get("cable_xy_offset", (0.0, 0.0))[0]) != 0.0
            or float(scene_info.get("cable_xy_offset", (0.0, 0.0))[1]) != 0.0
        ) and os.environ.get("W0E_F1A", "1") == "1"
        # W0-e F-1a v2 (%12 §運用10 v2, clearance-lift): the g=0.5-only smoke showed the cable RIDES the wall-top
        # during a low-height X-shift -> LIFT clear of the wall, shift + settled re-measure at height (contact-free =
        # unbiased), then descend VERTICALLY. coeff c-i (%12): comp = -(1-lam)*bow, lam=0.5 (retention 0.552/0.506).
        # W0E_F1A_V2=0 falls back to the flat comp-descent (study). offset-gated + W0E_F1A -> (0,0) BYTE-IDENTICAL
        # (else-branch, comp=0.0 -> tgt2(x_clip,..)). prints gated. provenance: cuda:0 + build sha (PREREG U).
        _f1a_comp = 0.0
        _lam = float(os.environ.get("W0E_F1A_LAMBDA", "0.5"))
        _f1a_v2 = _f1a_on and os.environ.get("W0E_F1A_V2", "1") == "1"
        _dx0 = None
        if _f1a_on:
            _cx0, _n0 = _w0e_guarded_cx(y_clip, x_clip)
            if _cx0 is None or abs(_cx0 - x_clip) > 0.030:
                print(f"  [W0E-F1A] initial guarded measure REJECT (n={_n0}) -> comp=0 + no lift (nominal fallback)")
                _f1a_v2 = False
            else:
                _dx0 = _cx0 - x_clip
                _f1a_comp = float(np.clip(-(1.0 - _lam) * _dx0, -0.022, 0.022))  # comp1 (also the flat comp if V2 off)
                _cby0 = state.body_q.numpy()[cable_bodies, 1]
                _nny = float(_cby0[int(np.argmin(np.abs(_cby0 - y_clip)))] - y_clip) * 1e3
                print(
                    f"  [W0E-F1A] guarded dx={_dx0 * 1e3:+.2f}mm (n={_n0}) lam={_lam} -> comp1={_f1a_comp * 1e3:+.2f}mm; "
                    f"pre-seat nearest-node Dy={_nny:+.2f}mm"
                )
        ok["c2_seat_descend"] = True
        if _f1a_v2 and _dx0 is not None:
            _pl0, _ = get_ee_positions(state, scene_info)
            _z0 = float(_pl0[2])
            _zhi = _z0 + 0.015
            for kk in range(1, 3):  # (2) clearance lift +15mm at x_clip (2 leg) -> cable clears the wall-top
                _lz = _z0 + (_zhi - _z0) * kk / 2
                state, _ = ik_move_both(
                    model,
                    state,
                    scene_info,
                    solver,
                    contacts,
                    *tgt2(x_clip, y_clip, _lz),
                    label=f"C1v2-LIFT{kk}/2",
                    converge_mm=2.5,
                    speed_factor=0.22,
                )
            for _ in range(30):
                state = physics_step(model, state, solver, contacts, scene_info)
            _plL, _ = get_ee_positions(state, scene_info)  # (log 3) lift-pose IK residual
            _lresid = float(np.linalg.norm(np.array(_plL) - np.array((x_clip, y_clip - GHS, _zhi)))) * 1e3
            print(
                f"  [W0E-F1A-v2] clearance lift +15mm -> EE z={float(_plL[2]) * 1e3:.1f}mm, lift IK resid={_lresid:.2f}mm"
            )
            for kk in range(1, 4):  # (3) high X-shift to x_clip+comp1 at height (3 leg)
                _xk = x_clip + _f1a_comp * kk / 3
                state, _ = ik_move_both(
                    model,
                    state,
                    scene_info,
                    solver,
                    contacts,
                    *tgt2(_xk, y_clip, _zhi),
                    label=f"C1v2-SHIFT{kk}/3",
                    converge_mm=2.5,
                    speed_factor=0.22,
                )
            for _ in range(30):  # (4) settle -> clean contact-free re-measure at height
                state = physics_step(model, state, solver, contacts, scene_info)
            _arm_x = x_clip + _f1a_comp
            _cxh, _nh = _w0e_guarded_cx(y_clip, _arm_x)
            _b1 = None
            if _cxh is None or abs(_cxh - _arm_x) > 0.030:
                print(
                    f"  [W0E-F1A-v2] high re-measure REJECT (n={_nh}) -> comp1 MAINTAINED {_f1a_comp * 1e3:+.2f}mm + FLAG"
                )
            else:
                _b1 = _cxh - _arm_x  # (c-i) arm-relative bow at height (contact-free)
                _comp_final = float(np.clip(-(1.0 - _lam) * _b1, -0.022, 0.022))
                print(
                    f"  [W0E-F1A-v2] high b1={_b1 * 1e3:+.2f}mm (crossing_h={_cxh:.4f} arm={_arm_x:.4f}) -> "
                    f"comp_final={_comp_final * 1e3:+.2f}mm"
                )
                state, _ = ik_move_both(
                    model,
                    state,
                    scene_info,
                    solver,
                    contacts,
                    *tgt2(x_clip + _comp_final, y_clip, _zhi),
                    label="C1v2-TRIM",
                    converge_mm=2.5,
                    speed_factor=0.22,
                )  # (5) 1-leg trim
                _f1a_comp = _comp_final
            for k in range(1, 9):  # (6) vertical descent 8 leg (X fixed, no mid-descent re-measure)
                zk = _zhi + (seat_ee_z - _zhi) * k / 8
                # deep-seat discriminator (%12 2026-07-05, offset-gated flag): SLOW the last 3 leg to test whether the
                # -1.6mm pin-frozen deep-seat is descent-dynamics (z->829 given settle time) or static equilibrium
                # (stays). ik_move_both:1960 n_steps=max(int(dist*100*STEPS_PER_CM*sf),50): STEPS_PER_CM=50 + leg
                # dist~5mm -> sf MUST be >1 to clear the 50-step floor (sf<1 = no-op = the INVALID byte-identical
                # smoke bgm2). %12: sf=8 -> ~208 steps (4.16x) = a real settle window (MAX_MOVE_STEPS=3000 headroom).
                # validity gate (else re-INVALID): :1971 print shows steps>50 on these legs + slowseat npz sha != fast f2 cell.
                _sf = 8.0 if (k >= 6 and os.environ.get("W0E_F1A_SLOWSEAT", "0") == "1") else 0.25
                state, okk = ik_move_both(
                    model,
                    state,
                    scene_info,
                    solver,
                    contacts,
                    *tgt2(x_clip + _f1a_comp, y_clip, zk),
                    label=f"C2-SEAT{k}/8",
                    converge_mm=2.5,
                    speed_factor=_sf,
                )
                ok["c2_seat_descend"] = ok["c2_seat_descend"] and bool(okk)
                wp.synchronize()  # (log 1) during-descent crossing z-x trace (wall-contact-free mouth entry)
                _Pz = state.body_q.numpy()[cable_bodies]
                _mz = np.abs(_Pz[:, 1] - y_clip) <= 0.0075
                if _mz.any():
                    _iz = np.where(_mz)[0]
                    _ci = int(_iz[np.argmin(np.abs(_Pz[_iz, 0] - (x_clip + _f1a_comp)))])
                    print(f"  [W0E-F1A-v2] descend k={k}/8 crossing x={_Pz[_ci, 0]:.4f} z={_Pz[_ci, 2] * 1e3:.1f}mm")
                if k % 2 == 0:
                    _cap(f"C1 v2-seat {k}/8")
            for _ in range(30):  # (log 2) per-cell retention: b_final/b1
                state = physics_step(model, state, solver, contacts, scene_info)
            _cxf, _ = _w0e_guarded_cx(y_clip, x_clip + _f1a_comp)
            if _cxf is not None and _b1 is not None and abs(_b1) > 1e-6:
                _bfin = _cxf - (x_clip + _f1a_comp)
                print(
                    f"  [W0E-F1A-v2] retention b_final/b1 = {(_bfin / _b1):.3f} (b_final={_bfin * 1e3:+.2f}mm, "
                    f"b1={_b1 * 1e3:+.2f}mm); crossing_final={_cxf:.4f}"
                )
        else:
            for k in range(
                1, 9
            ):  # v1 flat descent (V2 off / reject fallback; nominal comp=0.0 -> nominal path, NEW baseline post-LIFT_M raise)
                zk = (
                    z_lift + (seat_ee_z - z_lift) * k / 8
                )  # z_lift raised (W0E_LIFT_M 0.08) -> descent STARTS above the clip -> vertical entry
                state, okk = ik_move_both(
                    model,
                    state,
                    scene_info,
                    solver,
                    contacts,
                    *tgt2(x_clip + _f1a_comp, y_clip, zk),
                    label=f"C2-SEAT{k}/8",
                    converge_mm=2.5,
                    speed_factor=0.25,
                )
                ok["c2_seat_descend"] = ok["c2_seat_descend"] and bool(okk)
                if _f1a_on:  # (log 1) offset C1_SEAT z-x crossing trace (%12 2026-07-05: prove wall-contact-free VERTICAL entry from the raised clearance z; logging-only, offset-gated)
                    wp.synchronize()
                    _Pv1 = state.body_q.numpy()[cable_bodies]
                    _mv1 = np.abs(_Pv1[:, 1] - y_clip) <= 0.0075
                    if _mv1.any():
                        _iv1 = np.where(_mv1)[0]
                        _cv1 = int(_iv1[np.argmin(np.abs(_Pv1[_iv1, 0] - (x_clip + _f1a_comp)))])
                        print(
                            f"  [W0E-F1A-v1] descend k={k}/8 crossing x={_Pv1[_cv1, 0]:.4f} z={_Pv1[_cv1, 2] * 1e3:.1f}mm"
                        )
                if k % 2 == 0:
                    _cap(f"C1 full-clamp seat {k}/8")
        for _ in range(60):
            state = physics_step(model, state, solver, contacts, scene_info)
        wp.synchronize()
        _cb_y = state.body_q.numpy()[cable_bodies, 1]
        _seat_k = int(np.argmin(np.abs(_cb_y - y_clip)))
        seat_body = int(cable_bodies[_seat_k])

        def _zc1():
            wp.synchronize()
            return float(state.body_q.numpy()[seat_body, 2]) * 1e3  # mm: FROZEN C1 seat body, the SSOT retention z

        f1L0, f1R0, f2L0, f2R0 = _arm_split()  # FREEZE the claw partition at the symmetric seat pose
        z_c1_seated = _zc1()
        c1_seat_dist = _min_dist_mm(cable_geoms, _clip1g)
        c2_dist_atseat = _min_dist_mm(cable_geoms, _clip2g)
        print(
            f"  [C2] C1 FULL-CLAMP seat: seat_body=idx{seat_body}(Y{_cb_y[_seat_k]:+.3f}) z_seat={z_c1_seated:.1f}mm "
            f"(groove 809 / low-wall {LOW_WALL_TOP:.0f}) cable<->C1={c1_seat_dist:+.3f}mm "
            f"cable<->C2={c2_dist_atseat:+.3f}mm (<=0=touching)"
        )
        _cap("C1 SEATED (full-clamp, pre half-unclamp)")

        _ph("C1_PIN")
        # PERCLIP_PIN (b)-pin ACTIVATION on the VERIFIED C1 seat (%3 charter 2026-07-01) -- the headline freeze-scope
        # probe. Toggle the pre-allocated per-clip connect eq (seat_body <-> world@seat) ACTIVE now (mid-episode
        # eq_active; pre-seat activation forbidden per restore-gate log:6814 C2 -> gated on the verified seat above).
        # PER-CLIP: ONLY seat_body is anchored; body29/28.. stay articulated (measured over the guide below). The
        # anchor is set to the seat body's CURRENT world pos (~clip groove 809) so activation does NOT yank it.
        _perclip_on = os.environ.get("PERCLIP_PIN", "0") == "1"
        _fs_on = _perclip_on or os.environ.get("FREEZE_SCOPE", "0") == "1"
        _pin_eqid, _z_c1_after_pin = None, None
        # W0-e producer field (%9 pin-excluded floor bar / %12 pin-frame-onward, 2026-07-05): _seat_geom_mj = the
        # mujoco cable geom co-located with the pinned seat body -> EXCLUDED from the POST-pin cable<->C1 min-dist
        # (the free-neighbor "床" bar; pre-pin uses ALL geoms so the un-pinned body's penetration is NOT masked).
        # _c1_np_min/_c2_pen_min = per-clip episode-min penetration (mm, <0=penetration) = the planned producer field.
        _seat_geom_mj, _c1_np_min, _c2_pen_min = None, 9e9, 9e9
        if _perclip_on:
            assert scene_info.get("perclip_pin_n", 0) > 0, "PERCLIP_PIN=1 but build_scene pre-allocated no eqs"
            wp.synchronize()
            mujoco.mj_forward(mjm, mjd)  # refresh mjd.xpos so the seat-body position-match is current
            _seat_world = state.body_q.numpy()[seat_body, :3].astype(float).copy()
            # W0-e: the mujoco cable geom co-located with the pinned seat body (world-pos match, no Newton<->mjc index
            # assumption -- same primitive as the eq match below) -> excluded from the POST-pin free-neighbor floor bar.
            _seat_geom_mj = (
                min(cable_geoms, key=lambda g: float(np.linalg.norm(np.asarray(mjd.geom_xpos[g]) - _seat_world)))
                if cable_geoms
                else None
            )
            # Activate the pre-allocated DISABLED connect-to-world eq whose body1 IS the runtime seat body, found by
            # WORLD-POSITION match (no Newton<->mjc index assumptions): mjd.xpos[eq_obj1id] == the seat body's pos.
            _best, _bestd = None, 9e9
            for i in range(int(mjm.neq)):
                if (
                    int(mjm.eq_type[i]) == int(mujoco.mjtEq.mjEQ_CONNECT)
                    and int(mjm.eq_obj2id[i]) == 0
                    and int(mjm.eq_active0[i]) == 0
                ):
                    _d = float(np.linalg.norm(np.asarray(mjd.xpos[int(mjm.eq_obj1id[i])]) - _seat_world))
                    if _d < _bestd:
                        _bestd, _best = _d, i
            assert _best is not None and _bestd < 5e-3, (
                f"PERCLIP_PIN: no disabled connect eq matches the runtime seat body (best dist {_bestd * 1e3:.2f}mm)"
            )
            _pin_eqid = _best
            mjm.eq_data[_pin_eqid, 0:3] = [0.0, 0.0, 0.0]  # anchor in seat-body frame = its origin
            mjm.eq_data[_pin_eqid, 3:6] = _seat_world  # anchor in world frame = current seat pos (~clip groove)
            mjd.eq_active[_pin_eqid] = 1
            if _demo_rec is not None:  # P3 recorder: eq-pin AFTER activation (spec §2.5)
                _demo_rec.note_pin(_pin_eqid, seat_body)
            for _ in range(40):
                state = physics_step(model, state, solver, contacts, scene_info)
            _z_c1_after_pin = _zc1()
            print(
                f"  [PERCLIP_PIN] ACTIVATED eq#{_pin_eqid} on the EXACT runtime seat body idx{seat_body} "
                f"(position-match {_bestd * 1e3:.3f}mm) @world{[round(v, 4) for v in _seat_world]}; "
                f"z_c1 {z_c1_seated:.1f}->{_z_c1_after_pin:.1f}mm; eq_active={int(mjd.eq_active[_pin_eqid])} "
                f"(does the pin hold the seat? body29/28.. freedom measured over the guide below)"
            )
            _cap(f"PERCLIP_PIN ON seat idx{seat_body}: z_c1={_z_c1_after_pin:.1f}mm")

        _ph("L_HALF_UNCLAMP")
        # (3) L HALF-UNCLAMP: ramp L CLOSE->HALF (R stays CLOSED = the +Y anchor). MEASURE is_cradle through the
        # loosening -> the cable must NOT fall out of the L claw (else the guide starts from a dropped cable=artifact).
        HALF = GRIPPER_DRIVER_HALF_OPEN_RAD  # 0.69
        _trans = []
        _q = GRIPPER_DRIVER_CLOSE_RAD
        while _q >= HALF - 1e-6:
            _set_gripper_target(control, L_drv, _q)
            for _ in range(14):
                state = physics_step(model, state, solver, contacts, scene_info)
            _N, _, _, _ = _claw_cable_load(f1L0 + f2L0)
            _gap = _min_dist_mm(f1L0 + f2L0, cable_geoms)
            _cr = bool(-2.0 <= _gap <= 2.5 and 0.1 < _N < 60.0)
            _trans.append(
                {
                    "drv": round(_q, 4),
                    "claw_cable_gap_mm": round(_gap, 3),
                    "normal_N": round(_N, 2),
                    "is_cradle": _cr,
                    "z_c1_mm": round(_zc1(), 1),
                }
            )
            print(
                f"  [C2-HALF] L drv={_q:.4f} claw<->cable gap={_gap:+.3f}mm NORMAL={_N:.2f}N is_cradle={_cr} "
                f"z_c1={_zc1():.1f}mm"
            )
            _q -= 0.0125
        _set_gripper_target(control, L_drv, HALF)
        for _ in range(40):
            state = physics_step(model, state, solver, contacts, scene_info)
        _LhalfN, _, _, _Lmu = _claw_cable_load(f1L0 + f2L0)
        _Lhalfgap = _min_dist_mm(f1L0 + f2L0, cable_geoms)
        L_is_cradle = bool(-2.0 <= _Lhalfgap <= 2.5 and 0.1 < _LhalfN < 60.0)
        print(
            f"  [C2] AFTER half-unclamp (L drv={HALF}): claw<->cable gap={_Lhalfgap:+.3f}mm NORMAL={_LhalfN:.2f}N "
            f"eff_mu={_Lmu} is_cradle={L_is_cradle} z_c1={_zc1():.1f}mm (cable still held in L half-clamp?)"
        )
        _cap(f"L HALF-unclamp (drv={HALF}): is_cradle={L_is_cradle}")
        # 43-step step 8: R FULL-UNCLAMP (R->open) once C1 is seated -- human-Rs 2026-07-01 「Rはケーブルがクリップに
        # 固定されたらアンクランプし上昇」 + full_43step.json step8 (R_finger 0.002->0.04). The OLD route kept R CLOSED
        # as a +Y anchor = a DEVIATION from the 43-step. ⭐ CRITICAL DE-RISK: the 43-step releases R here ASSUMING C1
        # stays seated by the clip; the open-top clip has zero up-retention -> if C1 ESCAPES when R lets go, the full
        # 43-step is BLOCKED on clip-retention (Rs design call). Measure z_c1 before vs after R-release. Gated SEAT_TOPDOWN.
        _ph("R_UNCLAMP_RISE")
        _route43_mode = os.environ.get("SEAT_TOPDOWN", "0") == "1"
        if _route43_mode:
            _zc1_preR = _zc1()
            _set_gripper_target(control, R_drv, GRIPPER_DRIVER_OPEN_RAD)  # R unclamp (43-step step8)
            for _ in range(40):
                state = physics_step(model, state, solver, contacts, scene_info)
            _zc1_postR = _zc1()
            _c1_held_noR = bool(_zc1_postR < LOW_WALL_TOP)  # C1 stayed below the low-wall escape crit after R let go?
            print(
                f"  [C2-43-RUNCLAMP] R released (step8): z_c1 {_zc1_preR:.1f}->{_zc1_postR:.1f}mm "
                f"(low-wall {LOW_WALL_TOP:.0f}); C1_held_without_R={_c1_held_noR} "
                f"(⭐ if False = open-top clip does NOT retain C1 w/o R = 43-step BLOCKED on clip-retention)"
            )
            _cap(f"R unclamp (43-step step8): C1_held_without_R={_c1_held_noR} z_c1={_zc1_postR:.1f}")
            if (
                os.environ.get("C2_DUALSEAT", "0") == "1"
            ):  # Rs corrected-route 2026-07-01: R RISES after unclamp (pin holds C1 -> R free); rejoins ABOVE C2 at the dual-finger seat
                _plRr, _prRr = get_ee_positions(state, scene_info)
                _Lhold_r = (
                    float(_plRr[0]),
                    float(_plRr[1]),
                    float(_plRr[2]),
                )  # L holds its C1-seat pose (cable in half-clamp)
                _Rz0, _Rz1 = float(_prRr[2]), float(_prRr[2]) + 0.045
                for kk in range(1, 9):
                    _rz = _Rz0 + (_Rz1 - _Rz0) * kk / 8
                    state, _ = ik_move_both(
                        model,
                        state,
                        scene_info,
                        solver,
                        contacts,
                        _Lhold_r,
                        (float(_prRr[0]), float(_prRr[1]), _rz),
                        label=f"C2-RRISE{kk}/8",
                        converge_mm=2.5,
                        speed_factor=0.22,
                    )
                    for _ in range(10):
                        state = physics_step(model, state, solver, contacts, scene_info)
                print(
                    f"  [C2-RRISE] R risen {_Rz0:.3f}->{_Rz1:.3f} (+45mm; R free after pin holds C1, no longer anchors descended)"
                )
                _cap("R rise +45mm (corrected-route)")

        _ph("GUIDE_C2")
        # (4) GUIDE (しごき) L toward C2; R HOLDS at +Y (anchor above C1). cable slides through the L half-clamp.
        _pl0, _pr0 = get_ee_positions(state, scene_info)
        R_hold = (float(_pr0[0]), float(_pr0[1]), float(_pr0[2]))  # R frozen at its achieved +Y anchor pose
        L_x0, L_y0, L_z0 = float(_pl0[0]), float(_pl0[1]), float(_pl0[2])
        print(
            f"  [C2] R ANCHOR held @({R_hold[0]:.3f},{R_hold[1]:+.3f},{R_hold[2]:.3f}) [+Y above C1 {y_clip:+.3f}]; "
            f"L guide ({L_x0:.3f},{L_y0:+.3f},{L_z0:.3f}) -> C2 ({c2x:.3f},{c2y:+.3f}), z held at cradle level"
        )
        wp.synchronize()
        _gk = int(np.argmin(np.abs(state.body_q.numpy()[cable_bodies, 1] - L_y0)))
        guide_body = int(cable_bodies[_gk])
        gb_xy0 = state.body_q.numpy()[guide_body, :2].copy()
        ee_xy0 = np.array([L_x0, L_y0])
        N_GUIDE = 8
        guide_legs, cradle_break_x, jam_onset_x = [], None, None
        # FREEZE-SCOPE (%3 charter headline): snapshot every cable body's world pos at the guide START, vs the guide
        # END below -> per-body displacement. Pinned seat_body should ~freeze; body29/28.. should still move = (b)
        # viable (rest routes); ALL freeze = (a) degenerate; seat_body moves = pin not holding (or the no-pin control).
        if _fs_on:
            wp.synchronize()
            _fs_p0 = state.body_q.numpy()[cable_bodies, :3].astype(float).copy()
        # 43-step LIFT + HIGH TRAVERSE (gated SEAT_TOPDOWN; human-Rs 2026-07-01 + full_43step.json steps 10-11):
        # the C1->C2 transition LIFTS after the C1 seat (step 10: EE +45mm, 1.025->1.07) THEN traverses to ABOVE C2
        # at the lifted height (step 11: z=1.07, 上空移動) so the gripper CLEARS the C2 clip during the しごき
        # traverse. The OLD guide traversed at the cradle/insert height (L_z0) -> the finger drove INTO the C2 clip
        # (Rs video: 「クリップ下降点からそのまま横にスライド...フィンガがC2に衝突」). +45mm clears the floated wall
        # top 0.850 (bottom claw ~0.864 > 0.850 = 14mm margin). DEFAULT off (gate w/ the seat fix) -> byte-identical
        # low slide. Lead-implemented per the banked 43-step SSOT (authority layer; Rs directed 「43step表を確認」).
        # W0-e F-2 (GUIDE cable-line follow, spec v0.9 + %12 4-Q 2026-07-05): the L guide (しごき) follows the
        # cable's ACTUAL X at the look-ahead Y so the cable stays in the throat (RC-2 fix). Q1 = PLUS (lx tracks
        # cable), Q3 = rate-limited (a) c(k)=c(k-1)+clamp(dev-c(k-1),±8) then clamp(±cap), Q4 = update ONLY while
        # cradled (seed L_is_cradle) + FREEZE c on cradle loss (no 0-reset = jerk-safe). offset-gated + W0E_F2 ->
        # (0,0) BYTE-IDENTICAL (c=0). cap = W0E_F2_CAP_MM = 7mm (%12-confirmed conservative: pad X-half 11 - cable
        # r 4; geom-uncertainty logged, RUN-2 revisits via XML throat if guide authority is short). measures LIVE cable.
        _f2_on = (
            float(scene_info.get("cable_xy_offset", (0.0, 0.0))[0]) != 0.0
            or float(scene_info.get("cable_xy_offset", (0.0, 0.0))[1]) != 0.0
        ) and os.environ.get("W0E_F2", "1") == "1"
        _f2_cap = float(os.environ.get("W0E_F2_CAP_MM", "7.0")) * 1e-3
        _f2_c = 0.0
        _f2_prev_cradle = bool(L_is_cradle)
        _f2_frozen = False
        _ph("GUIDE_PRELIFT")  # P3 label: step-10 lift as its own phase (future re-records; CC2-C1)
        _route43 = os.environ.get("SEAT_TOPDOWN", "0") == "1"
        _trav_z = (L_z0 + 0.045) if _route43 else L_z0  # 43-step lift delta (insert 1.025 -> traverse 1.07)
        if _route43:
            _npre = 8
            for kk in range(1, _npre + 1):
                _lz = L_z0 + (_trav_z - L_z0) * kk / _npre
                if _f2_on and _f2_prev_cradle and not _f2_frozen:  # F-2 follow during the lift (measure at L_y0)
                    _cxg, _ng = _w0e_guarded_cx(L_y0, L_x0)
                    if _cxg is not None and abs(_cxg - L_x0) <= 0.030:
                        _f2_c = _f2_c + float(np.clip((_cxg - L_x0) - _f2_c, -0.008, 0.008))
                        _f2_c = float(np.clip(_f2_c, -_f2_cap, _f2_cap))
                state, _ = ik_move_both(
                    model,
                    state,
                    scene_info,
                    solver,
                    contacts,
                    (L_x0 + _f2_c, L_y0, _lz),
                    R_hold,
                    label=f"C2-PRELIFT{kk}/{_npre}",
                    converge_mm=2.5,
                    speed_factor=0.22,
                )
                for _ in range(12):
                    state = physics_step(model, state, solver, contacts, scene_info)
            print(
                f"  [C2-PRELIFT] L lifted {L_z0:.3f}->{_trav_z:.3f} (43-step step10 +45mm) before the high しごき traverse"
            )
        for k in range(1, N_GUIDE + 1):
            lx = L_x0 + (c2x - L_x0) * k / N_GUIDE
            ly = L_y0 + (c2y - L_y0) * k / N_GUIDE
            if _f2_on and _f2_prev_cradle and not _f2_frozen:  # F-2: follow the cable X at the look-ahead Y (ly)
                _cxg, _ng = _w0e_guarded_cx(ly, lx)
                if _cxg is not None and abs(_cxg - lx) <= 0.030:
                    _dev = _cxg - lx  # Q1 PLUS: deviation of the cable from the nominal straight line
                    _f2_c = _f2_c + float(np.clip(_dev - _f2_c, -0.008, 0.008))  # Q3 (a) rate-limited follow
                    _f2_c = float(np.clip(_f2_c, -_f2_cap, _f2_cap))  # Q2 cap (throat half - cable r)
                    print(
                        f"  [W0E-F2] guide{k} Y={ly:+.3f} dev={_dev * 1e3:+.2f}mm -> c={_f2_c * 1e3:+.2f}mm (cap{_f2_cap * 1e3:.0f})"
                    )
            lx = lx + _f2_c  # Q1 apply (a frozen c still applies)
            state, _ = ik_move_both(
                model,
                state,
                scene_info,
                solver,
                contacts,
                (lx, ly, _trav_z),
                R_hold,
                label=f"C2-GUIDE{k}/{N_GUIDE}",
                converge_mm=3.0,
                speed_factor=0.25,
            )
            for _ in range(30):
                state = physics_step(model, state, solver, contacts, scene_info)
            _plk, _ = get_ee_positions(state, scene_info)
            ee_xy = np.array([float(_plk[0]), float(_plk[1])])
            wp.synchronize()
            gb_xy = state.body_q.numpy()[guide_body, :2]
            ee_disp = float(np.linalg.norm(ee_xy - ee_xy0))
            cab_disp = float(np.linalg.norm(gb_xy - gb_xy0))
            slip_xy = (cab_disp / ee_disp) if ee_disp > 1e-6 else 0.0
            ee_dy, cab_dy = float(ee_xy0[1] - ee_xy[1]), float(gb_xy0[1] - gb_xy[1])
            slip_y = (cab_dy / ee_dy) if abs(ee_dy) > 1e-6 else 0.0
            _N, _pk, _n, _mu = _claw_cable_load(f1L0 + f2L0)
            _gap = _min_dist_mm(f1L0 + f2L0, cable_geoms)
            is_cradle = bool(-2.0 <= _gap <= 2.5 and 0.1 < _N < 60.0)
            if _f2_on and not _f2_frozen and not is_cradle:  # Q4: cradle lost -> FREEZE c at last value, stop updates
                _f2_frozen = True
                print(f"  [W0E-F2] cradle lost @guide{k} -> c FROZEN {_f2_c * 1e3:+.2f}mm (no re-capture, no 0-reset)")
            _f2_prev_cradle = is_cradle
            tabN, _tabn = _claw_table_load(f1L0)  # BOTTOM claw vs SOLID table = the geometry JAM
            tab_d = _min_dist_mm(f1L0, _tabg)
            f1z = _f1_zmin_mm(f1L0)
            zc1, c1d, c2d = _zc1(), _min_dist_mm(cable_geoms, _clip1g), _min_dist_mm(cable_geoms, _clip2g)
            _c1np = (
                _min_dist_mm(
                    [g for g in cable_geoms if g != _seat_geom_mj], _clip1g
                )  # %9 pin-excluded free-neighbor 床 bar (post-pin)
                if _seat_geom_mj is not None
                else c1d
            )
            _c1_np_min = min(_c1_np_min, _c1np)
            _c2_pen_min = min(_c2_pen_min, c2d)  # W0-e per-clip episode-min penetration (producer)
            lgrip_c2 = _min_dist_mm(
                f1L0 + f2L0, _clip2g
            )  # FLAG-D: L-gripper claws <-> C2 clip (penetration PV; <0=overlap)
            lr_sep, _lr_pair = (
                _hh_clear_mm()
            )  # item1 HAND-HAND at ARM-LINK level (sphere model, matches IK avoid; uncapped)
            rpad_c1 = _min_dist_mm(f1R0 + f2R0, _clip1g)  # item4 FINGER-CLIP: R-anchor pad <-> C1 clip (<0=penetration)
            ret_low = bool(zc1 < LOW_WALL_TOP)
            jam = bool(tab_d <= 0.2 or tabN > 0.5)
            if (not is_cradle) and cradle_break_x is None:
                cradle_break_x = round(lx, 4)
            if jam and jam_onset_x is None:
                jam_onset_x = round(lx, 4)
            smode = "SLIDE" if slip_xy < 0.35 else ("DRAG" if slip_xy > 0.65 else "PARTIAL")
            guide_legs.append(
                {
                    "k": k,
                    "L_ee_x": round(lx, 4),
                    "L_ee_y": round(ly, 4),
                    "ee_disp_mm": round(ee_disp * 1e3, 2),
                    "cable_disp_mm": round(cab_disp * 1e3, 2),
                    "slip_xy": round(slip_xy, 3),
                    "slip_y": round(slip_y, 3),
                    "slide_mode": smode,
                    "is_cradle": is_cradle,
                    "claw_cable_gap_mm": round(_gap, 3),
                    "claw_cable_N": round(_N, 2),
                    "bottom_claw_table_dist_mm": round(tab_d, 3),
                    "bottom_claw_table_N": round(tabN, 2),
                    "bottom_claw_zmin_mm": round(f1z, 1),
                    "JAM": jam,
                    "z_c1_mm": round(zc1, 1),
                    "c1_retained_lowwall": ret_low,
                    "cable_c1_dist_mm": round(c1d, 3),
                    "cable_c2_dist_mm": round(c2d, 3),
                    "lgrip_c2_dist_mm": round(lgrip_c2, 3),
                    "lr_gripper_sep_mm": round(lr_sep, 3),
                    "rpad_c1_dist_mm": round(rpad_c1, 3),
                }
            )
            print(
                f"  [C2-GUIDE] k={k}/{N_GUIDE} Lx={lx:.3f} Ly={ly:+.3f} | slip_xy={slip_xy:.3f}({smode}) "
                f"slip_y={slip_y:+.3f} cradle={is_cradle}(gap{_gap:+.2f}/N{_N:.1f}) | bottomclaw<->table={tab_d:+.2f}mm "
                f"N={tabN:.1f} zmin={f1z:.1f} JAM={jam} | C1 z={zc1:.1f}({'IN' if ret_low else 'OUT'}) "
                f"cable<->C1={c1d:+.2f} cable<->C2={c2d:+.2f} | Lgrip<->C2={lgrip_c2:+.2f} "
                f"Rpad<->C1={rpad_c1:+.2f} | HH-armlink={lr_sep:+.2f}mm{_lr_pair} (sphere, <0=overlap)"
            )
            _cap(
                f"GUIDE {k}/{N_GUIDE} Lx={lx:.3f}: slip={slip_xy:.2f}({smode}) cradle={is_cradle} JAM={jam} "
                f"C1{'IN' if ret_low else 'OUT'}"
            )

        # FREEZE-SCOPE compute (%3 charter headline) -- the (a)/(b) discriminator + C1-retention + route-reach summary.
        if _fs_on:
            wp.synchronize()
            _fs_p1 = state.body_q.numpy()[cable_bodies, :3].astype(float).copy()
            _fs_disp = (np.linalg.norm(_fs_p1 - _fs_p0, axis=1) * 1e3).astype(float)  # mm per cable body over guide
            _seat_arr = np.asarray(cable_bodies)
            _seat_kk = (
                int(np.where(_seat_arr == seat_body)[0][0])
                if seat_body in _seat_arr
                else int(np.argmin(np.abs(state.body_q.numpy()[cable_bodies, 1] - y_clip)))
            )
            _MOVE_THR = 2.0
            _n_moved = int(np.sum(_fs_disp > _MOVE_THR))
            _seat_disp = float(_fs_disp[_seat_kk])
            _nbr_k = [k for k in (_seat_kk - 2, _seat_kk - 1, _seat_kk + 1, _seat_kk + 2) if 0 <= k < len(_fs_disp)]
            _nbr_disp = [round(float(_fs_disp[k]), 2) for k in _nbr_k]
            _max_disp = float(np.max(_fs_disp))
            if not _perclip_on:
                _scope = "CONTROL_NO_PIN(seat free)"
            elif _seat_disp >= _MOVE_THR:
                _scope = "SEAT_MOVED(pin-not-holding)"
            elif _n_moved == 0:
                _scope = "ALL_FROZEN(a-degenerate)"
            elif _n_moved >= 3:
                _scope = "SEAT_ONLY_FROZEN(b-viable)"
            else:
                _scope = "PARTIAL"
            _zc1_final = _zc1()
            _c1_ret_final = bool(_zc1_final < LOW_WALL_TOP)
            _c2_reach_final = _min_dist_mm(cable_geoms, _clip2g)
            print(
                f"  [FREEZE-SCOPE] pin={'ON' if _perclip_on else 'OFF(control)'} seat_k={_seat_kk} "
                f"seat_disp={_seat_disp:.2f}mm nbr={_nbr_disp} max={_max_disp:.1f}mm "
                f"n_moved(>{_MOVE_THR})={_n_moved}/{len(_fs_disp)} -> {_scope} | C1 z={_zc1_final:.1f}"
                f"({'IN' if _c1_ret_final else 'OUT'} low-wall {LOW_WALL_TOP:.0f}) cable<->C2={_c2_reach_final:+.2f}mm"
            )
            _freeze_scope_rec = {
                "pin_active": _perclip_on,
                "pin_eqid": _pin_eqid,
                "pin_body": (int(seat_body) if _perclip_on else None),
                "seat_k": _seat_kk,
                "seat_disp_mm": round(_seat_disp, 2),
                "neighbor_disp_mm": _nbr_disp,
                "max_disp_mm": round(_max_disp, 1),
                "n_moved_gt2mm": _n_moved,
                "n_cable_bodies": len(_fs_disp),
                "verdict": _scope,
                "z_c1_seated_mm": round(float(z_c1_seated), 1),
                "z_c1_after_pin_mm": (round(float(_z_c1_after_pin), 1) if _z_c1_after_pin is not None else None),
                "z_c1_final_mm": round(float(_zc1_final), 1),
                "c1_retained_lowwall": _c1_ret_final,
                "low_wall_top_mm": round(float(LOW_WALL_TOP), 1),
                "cable_c2_final_mm": round(float(_c2_reach_final), 2),
                "per_body_disp_mm": [round(float(d), 2) for d in _fs_disp],
                "guide_legs": guide_legs,
            }

        # (5) C2 SEAT ATTEMPT: lower L to push the cable into C2's groove. Over SOLID -> expect the bottom claw to
        # hit the table before the cable seats; MEASURE cable<->C2 + the table jam (do NOT add a void).
        _plg, _ = get_ee_positions(state, scene_info)
        # SEAT_TOPDOWN (penetration fix, human-Rs 2026-06-30 「クリップの壁面にフィンガ、ケーブルが貫通している」):
        # the default C2-PUSH descends the (half-open) gripper to the groove AT the clip (x,y) -> the claws + the
        # dragged cable are forced INTO the clip-wall envelope (a kinematic position-drive can't be stopped by
        # contact). SEAT_TOPDOWN=1 replaces it with a proper open-top insertion: LIFT the cable above the clip wall
        # tops, position over the groove X-centre, then OPEN the gripper (release) so the cable settles into the
        # open-top channel by gravity -- the gripper claws STAY above the wall tops, so neither finger nor cable is
        # forced into the walls (a drag-mis-delivered cable simply MISSES = physically valid, vs forced penetration).
        # DEFAULT 0 -> byte-identical old C2-PUSH. Lead-implemented (authority layer holds Rs's actual directive).
        _seat_topdown = os.environ.get("SEAT_TOPDOWN", "0") == "1"
        _c2_dualseat = (
            (os.environ.get("C2_DUALSEAT", "0") == "1") and _seat_topdown
        )  # Rs corrected-route 2026-07-01: R-rejoin + dual-finger clamp-push (replaces the L-single top-down slide)
        if _c2_dualseat:
            _GHS = (
                WIDE_RIGHT_Y - WIDE_LEFT_Y
            ) / 2.0  # 0.044 = 88mm two-EE span (INVARIANT#2; tgt2 yc-+GHS: L=-GHS, R=+GHS)
            _wall_top_d = CLIP1_Z + _clip_float_z + 0.030
            _z_above_d = _wall_top_d + 0.012 + ee_off  # hold above the C2 wall tops before the top-down descent
            _seat_z_d = (
                GROOVE_CENTER_Z + _clip_float_z + ee_off
            )  # push the gripped cable centre to the FLOATED C2 groove
            # 1) RE-GRASP the ACTUAL cable (Rs guide-data charter fix). The OLD code moved both arms to the FIXED
            #    (c2x, c2y+-GHS) then CLOSED -> R closed at (c2x, c2y+GHS)=(0.40,0.119) but the cable BOWS to X~0.37
            #    there (between L's grip & the C1 pin) => R gripped EMPTY SPACE (Rs: "R is NOT re-grasping"). FIX:
            #    query the REAL cable body per side + target the EE to the actual world-XYZ. KEEP L holding (the +Y
            #    span stays SUSPENDED between L & the C1 pin -> R re-grasps it in the AIR, no drop onto the solid table).
            # 1a) L (still holding the cable in half-clamp) moves to the -Y grip side + full-clamp. Cable stays held.
            _pld, _prd = get_ee_positions(state, scene_info)
            _La = (c2x, c2y - _GHS, _z_above_d)
            for kk in range(1, 11):
                _fl = tuple(float(_pld[i]) + (_La[i] - float(_pld[i])) * kk / 10 for i in range(3))
                state, _ = ik_move_both(
                    model,
                    state,
                    scene_info,
                    solver,
                    contacts,
                    _fl,
                    R_hold,
                    label=f"C2-LMOVE{kk}/10",
                    converge_mm=3.0,
                    speed_factor=0.22,
                )
                for _ in range(12):
                    state = physics_step(model, state, solver, contacts, scene_info)
            _set_gripper_target(control, L_drv, GRIPPER_DRIVER_CLOSE_RAD)  # L half->full clamp (already on the cable)
            for _ in range(30):
                state = physics_step(model, state, solver, contacts, scene_info)
            _NLg1, _, _, _ = _claw_cable_load(f1L0 + f2L0)
            print(
                f"  [C2-REGRASP-L] L moved to -Y grip ({c2x:.3f},{c2y - _GHS:+.3f}) + full-clamp: claw<->cable L={_NLg1:.2f}N "
                f"(L holds -> the +Y cable span is suspended for R to re-grasp)"
            )
            _cap(f"C2 L -Y grip full-clamp: L={_NLg1:.1f}N")
            # 1b) R RE-GRASP the ACTUAL cable at the +Y side, with the BANKED TILT-FOLLOW recipe + SPAN-PRESERVING
            #     targeting (%3 refinements from GD-KoShape-Finger.md §Mid-air re-grasp, human-CONFIRMED 2026-06-21):
            #     - SPAN-PRESERVING (INVARIANT#2): HOLD R's target Y = c2y+GHS (88mm vs L at c2y-GHS); correct ONLY X
            #       to the ACTUAL cable X at that Y (follow the bow). Fixes 'R grips air' WITHOUT touching the span.
            #     - TILT-FOLLOW (banked Finding 2 :126-134): the suspended cable is locally TILTED; a square-on claw
            #       MISSES. Measure theta = cable local Y-Z pitch at R's lane; set R EE = Rx(-90+theta) so the claws
            #       ALIGN with the tilt. Faithful COPY of the _64 monkeypatch (GD-KoShape:157-160); R=re-grasp arm
            #       mirrors the banked L; production solve_ik_dual UNCHANGED (runtime monkeypatch, restored after).
            wp.synchronize()
            _cbq = state.body_q.numpy()[cable_bodies]
            # ⛔ ANTI-REVERT (Rs-LOCKED 2026-07-01「先祖返りしないように」): R targets the ACTUAL cable X (the bow) via argmin
            #    over cable_bodies, NOT a fixed c2x. A FIXED geometric target = the air-grip "R not re-grasping" bug (Rs
            #    2026-07-01). Do NOT revert to a fixed geometric target. Y is HELD at c2y+GHS = 88mm INVARIANT#2 (span-preserving).
            _kR = int(
                np.argmin(np.abs(_cbq[:, 1] - (c2y + _GHS)))
            )  # cable body nearest R's +Y grip lane (for the bow X/Z)
            _R_ty = c2y + _GHS  # HOLD Y = 88mm span (span-preserving, INVARIANT#2)
            _cRx, _cRz = float(_cbq[_kR, 0]), float(_cbq[_kR, 2])  # follow the ACTUAL cable X (bow) + Z at that lane
            _span_y_mm = float(abs(_R_ty - (c2y - _GHS))) * 1e3  # target Y-separation = 88mm by construction
            _picked_dy_mm = float(_cbq[_kR, 1] - _R_ty) * 1e3  # how far the picked body's Y is from the 88mm lane
            _cR = (_cRx, _R_ty, _cRz)
            _zgrip_R = _cRz + ee_off
            print(
                f"  [C2-REGRASP-R] span-preserving: R target=({_cR[0]:.3f},{_cR[1]:+.3f},{_cR[2]:.3f}) "
                f"(HOLD Y={_R_ty:+.3f}=+GHS, X follows bow) vs OLD-FIXED X={c2x:.3f} [dX {(_cRx - c2x) * 1e3:+.0f}mm] "
                f"| picked body idx{_kR} Y{_cbq[_kR, 1]:+.3f} (dY from lane {_picked_dy_mm:+.0f}mm) | target Y-span={_span_y_mm:.1f}mm (88, INVARIANT#2)"
            )
            _ph("C2_REGRASP")
            # --- TILT-FOLLOW monkeypatch (byte-faithful copy of the banked _64, GD-KoShape:157-160; R=re-grasp arm) ---
            _BASE_RX = -_math.pi / 2  # default Rx(-90deg) = gripper down (test:1851)
            # ⛔ ANTI-REVERT (Rs-LOCKED 2026-07-01「先祖返りしないように」): square-on DEFAULT (C2_TILT_SIGN=0). The banked
            #    tilt-follow is FLOATING-cable-specific (GD-KoShape:117) & does NOT transfer to this TAUT route (tilt -> R
            #    misses 0N). Do NOT revert the default to 1. The override + tilt machinery are KEPT for future floating cases.
            _TILT_SIGN = float(
                os.environ.get("C2_TILT_SIGN", "0")
            )  # DEFAULT 0 = SQUARE-ON (Rs-approved 2026-07-01「これでやってみて」: the banked tilt-follow is FLOATING-cable-specific & does NOT transfer to this TAUT C1->C2 route, §運用10). Override kept for future floating cases: 1 (banked tilt) / -1 (flip)
            _ROT = {}

            def _rot_quat_rx(angle):  # X-rotation target in solve_ik_dual's XYZW convention (w LAST)
                return wp.array(
                    [wp.vec4(_math.sin(angle / 2), 0.0, 0.0, _math.cos(angle / 2))], dtype=wp.vec4, device=DEVICE
                )

            def _cable_local_pitch(y_t):  # cable local Y-Z pitch theta [rad] at lane y_t (tangent of adjacent segments)
                wp.synchronize()
                cbs = state.body_q.numpy()[cable_bodies]
                cbs = cbs[np.argsort(cbs[:, 1])]
                ys = cbs[:, 1]
                j = int(np.argmin(np.abs(ys - y_t)))
                a, b = max(j - 1, 0), min(j + 1, len(ys) - 1)
                dY, dZ = float(ys[b] - ys[a]), float(cbs[b, 2] - cbs[a, 2])
                return _math.atan2(dZ, dY) if abs(dY) > 1e-9 else 0.0

            def _solve_ik_dual_rot(scene_info_, target_left, target_right, warmstart_jq=None):
                # Faithful copy of solve_ik_dual (test:1814) but with PER-ARM rotation targets _ROT['L']/_ROT['R'].
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
                    link_index=le, link_offset_rotation=wp.quat_identity(), target_rotations=_ROT["L"], weight=0.5
                )
                rr = IKObjectiveRotation(
                    link_index=re, link_offset_rotation=wp.quat_identity(), target_rotations=_ROT["R"], weight=0.5
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

            _theta_R = _cable_local_pitch(_R_ty)  # cable local pitch at R's grip lane (measured at THIS route's geom)
            _ROT["R"] = _rot_quat_rx(_BASE_RX + _TILT_SIGN * _theta_R)  # R = re-grasp arm = TILT-FOLLOW
            _ROT["L"] = _rot_quat_rx(_BASE_RX)  # L = anchor/holder = default down
            if _demo_rec is not None:  # P3 recorder: effective-rotation register at C2 monkeypatch INSTALL (spec §2.4)
                _demo_rec.note_ik_rot(_ROT["L"].numpy()[0], _ROT["R"].numpy()[0], 1)
            print(
                f"  [C2-REGRASP-TILT] cable local pitch theta={_math.degrees(_theta_R):+.1f}deg at R lane Y={_R_ty:+.3f} "
                f"-> R EE Rx({_math.degrees(_BASE_RX + _TILT_SIGN * _theta_R):+.1f}deg); L default (anchor) "
                f"[banked _64 tilt-follow; a square-on claw MISSES the tilted cable, GD-KoShape:126-134]"
            )
            _set_gripper_target(control, R_drv, GRIPPER_DRIVER_OPEN_RAD)  # R open before descending onto the cable
            for _ in range(15):
                state = physics_step(model, state, solver, contacts, scene_info)
            _prr = get_ee_positions(state, scene_info)[1]
            _hovR = (_cR[0], _cR[1], _z_above_d)
            for kk in range(1, 11):
                _fr = tuple(float(_prr[i]) + (_hovR[i] - float(_prr[i])) * kk / 10 for i in range(3))
                _La2, _fr2 = _inject_detour(
                    "C2_REGRASP", kk, 10, _La, _fr
                )  # DQ7 (ii): R-arm kick-and-recover (None-path passthrough; release-margin guards regrasp_ok)
                state, _ = ik_move_both(
                    model,
                    state,
                    scene_info,
                    solver,
                    contacts,
                    _La2,
                    _fr2,
                    label=f"C2-RHOVER{kk}/10",
                    converge_mm=3.0,
                    speed_factor=0.22,
                    ik_solve_fn=_solve_ik_dual_rot,
                )
                for _ in range(10):
                    state = physics_step(model, state, solver, contacts, scene_info)
            # R-REACH check (LEDGER R-reach wall crux): achieved R XY vs the span-preserving target (Y=c2y+GHS)
            _paR = get_ee_positions(state, scene_info)[1]
            _reach_R_mm = float(np.hypot(_hovR[0] - float(_paR[0]), _hovR[1] - float(_paR[1]))) * 1e3
            print(
                f"  [C2-REGRASP-REACH] R achieved XY=({float(_paR[0]):.3f},{float(_paR[1]):+.3f}) vs tgt "
                f"=({_hovR[0]:.3f},{_hovR[1]:+.3f}) resid={_reach_R_mm:.1f}mm "
                f"(LEDGER R-reach wall: >20mm = R can't reach the 88mm lane = BLOCKED_FOR_USER)"
            )
            _desR = (_cR[0], _cR[1], _zgrip_R)
            for kk in range(1, 9):
                _fr = tuple(float(_hovR[i]) + (_desR[i] - float(_hovR[i])) * kk / 8 for i in range(3))
                state, _ = ik_move_both(
                    model,
                    state,
                    scene_info,
                    solver,
                    contacts,
                    _La,
                    _fr,
                    label=f"C2-RDESCEND{kk}/8",
                    converge_mm=2.5,
                    speed_factor=0.20,
                    ik_solve_fn=_solve_ik_dual_rot,
                )
                for _ in range(12):
                    state = physics_step(model, state, solver, contacts, scene_info)
            _cap("C2 R re-grasp: descended onto ACTUAL cable (tilt-follow)")
            _cage_d = GRIPPER_DRIVER_OPEN_RAD + (GRIPPER_DRIVER_CLOSE_RAD - GRIPPER_DRIVER_OPEN_RAD) * 0.9
            _set_gripper_target(control, R_drv, _cage_d)  # 2-phase cage close (capture-then-gentle, mirrors C1)
            for _ in range(30):
                state = physics_step(model, state, solver, contacts, scene_info)
            _set_gripper_target(control, R_drv, GRIPPER_DRIVER_CLOSE_RAD)
            for _ in range(40):
                state = physics_step(model, state, solver, contacts, scene_info)
            # VERIFY grip: claw<->cable NORMAL force NONZERO for BOTH L AND R (old failure = R grips air = N_R~0).
            # Judge caveat (GD-KoShape:161): per-arm CAPTURE false-negatives when tilted -> the RELIABLE signal is the
            # claw<->cable NORMAL force (+ cable-tracks-EE) + the §運用14/human video, NOT the b<c<t capture window.
            _NLg, _, _nL, _ = _claw_cable_load(f1L0 + f2L0)
            _NRg, _pkR, _nR, _muR = _claw_cable_load(f1R0 + f2R0)
            _paL2, _paR2 = get_ee_positions(state, scene_info)
            _span_3d_mm = float(np.linalg.norm(np.array(_paL2) - np.array(_paR2))) * 1e3  # achieved L<->R 3D EE span
            _L_grips = bool(_NLg > 0.1)
            _R_grips = bool(_NRg > 0.1)
            _at_88 = bool(_reach_R_mm <= 20.0)
            # ⛔ ANTI-REVERT (Rs-LOCKED 2026-07-01「先祖返りしないように」): regrasp_ok = (_at_88 AND _R_grips) = the charter
            #    core (R genuinely grips the ACTUAL cable @88mm). Do NOT revert to the both-hands-force gate (the
            #    "BLOCKED_INVARIANT2" misnomer, %0 records-vs-fact 2026-07-01): L=0N is a valid 0-normal CAGE, not a miss.
            # RE-GRASP VERDICT (re-spec per %0 GT cross-PV 2026-07-01, records-vs-fact): the charter's core = does R
            # genuinely GRIP the ACTUAL cable at the 88mm lane (not air)? The OLD gate required BOTH L AND R force >0.1N
            # -> it MISLABELED the R-grip + L-0-normal-cage case as "MISS" (R did NOT miss; L is an unloaded cage that
            # RETAINS the cable, video + GD-KoShape:161 "per-arm force misleads"). Split R-reach / R-grip / L-load state.
            if not _at_88:
                _regrasp_verdict = "BLOCKED_REACH_WALL"  # R cannot reach the 88mm lane (LEDGER reach wall)
            elif not _R_grips:
                _regrasp_verdict = (
                    "R_MISS_AT_88"  # R reached the lane but gripped AIR (e.g. tilted claws off the taut cable)
                )
            elif _L_grips:
                _regrasp_verdict = "SUCCESS_DUAL_LOADED_AT_88"  # R + L BOTH load-bearing at the 88mm span
            else:
                _regrasp_verdict = "SUCCESS_R_GRIP_L_CAGE_AT_88"  # R grips @88mm; L = 0-normal-load cage (verify RETAIN via video, GD-KoShape:161)
            _regrasp_ok = bool(
                _at_88 and _R_grips
            )  # charter core: R genuinely grips the ACTUAL cable @88mm (L-load-share = a separate Rs Q)
            print(
                f"  [C2-REGRASP-GRIP] claw<->cable NORMAL: L={_NLg:.2f}N(grips={_L_grips}) R={_NRg:.2f}N(n={_nR},grips={_R_grips}) "
                f"| R-reach={_reach_R_mm:.1f}mm at_88={_at_88} | achieved 3D span={_span_3d_mm:.1f}mm (Y-sep tgt 88) "
                f"=> VERDICT={_regrasp_verdict} regrasp_ok={_regrasp_ok}"
            )
            print(
                f"  [C2-REGRASP-GATE] charter core = R grips the ACTUAL cable @88mm lane (regrasp_ok={_regrasp_ok}). "
                f"labels: SUCCESS_DUAL_LOADED (R+L force) / SUCCESS_R_GRIP_L_CAGE (R force, L 0-normal cage=retain per video) / "
                f"R_MISS_AT_88 (R reached but air) / BLOCKED_REACH_WALL. INVARIANT#2 Y-span held; L-load-share + 3D-chord excess = Rs Q. => {_regrasp_verdict}"
            )
            _cap(
                f"C2 R re-grasp: {_regrasp_verdict} (L={_NLg:.1f} R={_NRg:.1f}N theta={_math.degrees(_theta_R):+.0f}deg)"
            )
            _c2_regrasp_rec = {
                "r_target_x": round(_cRx, 3),
                "r_target_y": round(_R_ty, 3),
                "r_target_z": round(_cRz, 3),
                "r_old_fixed_x": round(float(c2x), 3),
                "r_x_offset_from_fixed_mm": round((_cRx - c2x) * 1e3, 1),
                "picked_body_dy_from_lane_mm": round(_picked_dy_mm, 1),
                "target_y_span_mm": round(_span_y_mm, 1),
                "achieved_3d_span_mm": round(_span_3d_mm, 1),
                "tilt_theta_deg": round(_math.degrees(_theta_R), 2),
                "tilt_sign": _TILT_SIGN,
                "r_reach_resid_mm": round(_reach_R_mm, 1),
                "reached_88mm_lane": _at_88,
                "l_grip_N": round(float(_NLg), 2),
                "r_grip_N": round(float(_NRg), 2),
                "l_grips": _L_grips,
                "r_grips": _R_grips,
                "regrasp_verdict": _regrasp_verdict,
                "regrasp_ok": _regrasp_ok,
            }
            if _demo_rec is not None:  # P3 recorder: rotation register RESTORE to default Rx(-90) (spec §2.4)
                _demo_rec.note_ik_rot(None, None, 0)
            _ph("C2_TRANSPORT")  # P3 label: lateral carry to C2 as its own phase (future re-records; CC2-C1)
            # 2) TRANSPORT: carry R's gripped cable segment laterally to the C2 +Y seat point (L already at the -Y seat).
            #    The gripped cable comes WITH the hand -> the cable centre (between L & R) arrives over the C2 groove.
            _carR = (c2x, c2y + _GHS, _z_above_d)
            _prc = get_ee_positions(state, scene_info)[1]
            for kk in range(1, 11):
                _fr = tuple(float(_prc[i]) + (_carR[i] - float(_prc[i])) * kk / 10 for i in range(3))
                state, _ = ik_move_both(
                    model,
                    state,
                    scene_info,
                    solver,
                    contacts,
                    _La,
                    _fr,
                    label=f"C2-TRANSPORT{kk}/10",
                    converge_mm=3.0,
                    speed_factor=0.20,
                )
                for _ in range(12):
                    state = physics_step(model, state, solver, contacts, scene_info)
            wp.synchronize()
            _cb_t = state.body_q.numpy()[cable_bodies]
            _nk_t = int(np.argmin(np.abs(_cb_t[:, 1] - c2y)))
            _NLt, _, _, _ = _claw_cable_load(f1L0 + f2L0)
            _NRt, _, _, _ = _claw_cable_load(f1R0 + f2R0)
            print(
                f"  [C2-TRANSPORT] R carried its grip to C2 +Y; near-c2y cable body X={_cb_t[_nk_t, 0]:.3f} (c2x={c2x:.3f}, "
                f"dX={(float(_cb_t[_nk_t, 0]) - c2x) * 1e3:+.0f}mm) | still gripped: L={_NLt:.1f}N R={_NRt:.1f}N"
            )
            if _c2_regrasp_rec is not None:
                _c2_regrasp_rec["transport_near_c2_dx_mm"] = round((float(_cb_t[_nk_t, 0]) - c2x) * 1e3, 1)
                _c2_regrasp_rec["transport_still_gripped_L_N"] = round(float(_NLt), 2)
                _c2_regrasp_rec["transport_still_gripped_R_N"] = round(float(_NRt), 2)
            _cap("C2 transport: R grip carried to C2 +Y seat point")
            _ph("C2_DUAL_SEAT")
            # W0-e F-3 (C2 X-follow, %12 2026-07-05, offset-gated + W0E_F3): C2_DUAL_SEAT is already TOP-DOWN (no
            # wall-ride) so a single _c2x_comp on BOTH L/R descent tuples suffices (the v2 crossing-comp insight; no
            # clearance-lift). (a) MEASURE at the post-transport sync via _w0e_guarded_cx (self-syncs, NO new physics
            # step) + plausibility (NOT bare argmin-Y). comp=clamp(-(1-lam)*(cx-c2x),+-22), lam=0.5 (F-1a coeff).
            # (b) log crossing z: z<=840 (wall-height) => PREMISE-FAIL loud (reconsider a lift variant). (0,0)/no-flag
            # -> comp=0.0 -> c2x+0.0==c2x = BYTE-IDENTICAL (gated off on nominal). provenance: cuda:0 + build sha.
            _c2x_comp = 0.0
            _f3_on = (
                float(scene_info.get("cable_xy_offset", (0.0, 0.0))[0]) != 0.0
                or float(scene_info.get("cable_xy_offset", (0.0, 0.0))[1]) != 0.0
            ) and os.environ.get("W0E_F3", "1") == "1"
            if _f3_on:
                _cxc2, _nc2 = _w0e_guarded_cx(c2y, c2x)  # (a) guarded selector + plausibility (self-syncs)
                _cb_f3 = state.body_q.numpy()[cable_bodies]  # already synced by the call above (no new step)
                _mzc2 = np.abs(_cb_f3[:, 1] - c2y) <= 0.0075
                _zc2 = float(_cb_f3[_mzc2, 2].mean()) * 1e3 if _mzc2.any() else float("nan")
                if _cxc2 is None or abs(_cxc2 - c2x) > 0.030:
                    print(f"  [W0E-F3] guarded c2 crossing REJECT (n={_nc2}) -> _c2x_comp=0 (nominal fallback) + FLAG")
                else:
                    _lam3 = float(os.environ.get("W0E_F1A_LAMBDA", "0.5"))
                    _c2x_comp = float(np.clip(-(1.0 - _lam3) * (_cxc2 - c2x), -0.022, 0.022))
                    _pf3 = (
                        " ⚠PREMISE-FAIL(z<=840 wall-height -> reconsider lift)"
                        if (_zc2 == _zc2 and _zc2 <= 840.0)
                        else ""
                    )
                    print(
                        f"  [W0E-F3] guarded c2 dx={(_cxc2 - c2x) * 1e3:+.2f}mm (n={_nc2}) lam={_lam3} -> "
                        f"_c2x_comp={_c2x_comp * 1e3:+.2f}mm; crossing z={_zc2:.1f}mm{_pf3}"
                    )
            # 3) both descend (CLOSED) from above -> clamp-push the cable into the C2 groove (top-down, NOT the lateral slide that drove the claw into the wall)
            for kk in range(1, 13):
                _zk = _z_above_d + (_seat_z_d - _z_above_d) * kk / 12
                state, _ = ik_move_both(
                    model,
                    state,
                    scene_info,
                    solver,
                    contacts,
                    (c2x + _c2x_comp, c2y - _GHS, _zk),
                    (c2x + _c2x_comp, c2y + _GHS, _zk),
                    label=f"C2-DUAL-SEAT{kk}/12",
                    converge_mm=2.5,
                    speed_factor=0.20,
                )
                for _ in range(18):
                    state = physics_step(model, state, solver, contacts, scene_info)
                _lgc2 = _min_dist_mm(f1L0 + f2L0, _clip2g)
                _rgc2 = _min_dist_mm(f1R0 + f2R0, _clip2g)
                _NLc2, _ = _claw_c2_load(f1L0 + f2L0)
                _NRc2, _ = _claw_c2_load(f1R0 + f2R0)
                _cabc2 = _min_dist_mm(cable_geoms, _clip2g)
                print(
                    f"  [C2-DUAL-SEAT] k={kk}/12 z={_zk:.3f} Lgrip<->C2={_lgc2:+.3f} Rgrip<->C2={_rgc2:+.3f}mm "
                    f"| claw<->C2 CONTACT-N: L={_NLc2:.2f} R={_NRc2:.2f} | cable<->C2={_cabc2:+.3f}mm"
                )
                _cap(f"C2 dual-seat {kk}/12 Lgrip<->C2={_lgc2:+.2f}")
                if (
                    _f3_on
                ):  # (c) F-3 during-descent crossing z-x trace (%12 (log 1) form; offset-gated -> nominal unaffected)
                    wp.synchronize()
                    _Pf3 = state.body_q.numpy()[cable_bodies]
                    _mf3 = np.abs(_Pf3[:, 1] - c2y) <= 0.0075
                    if _mf3.any():
                        _if3 = np.where(_mf3)[0]
                        _cif3 = int(_if3[np.argmin(np.abs(_Pf3[_if3, 0] - (c2x + _c2x_comp)))])
                        print(
                            f"  [W0E-F3] dual-seat k={kk}/12 crossing x={_Pf3[_cif3, 0]:.4f} z={_Pf3[_cif3, 2] * 1e3:.1f}mm"
                        )
            _ph("C2_SETTLE")
            # 4) RELEASE both grippers + settle -> genuine NOTCH SETTLE vs claw-held / pop-out (%0 seat-capture concern, charter metric #3;
            #    the C2 clip is open-top w/ zero up-retention -> if the cable pops out on release it was claw-HELD, not settled)
            _cab_c2_held = _min_dist_mm(cable_geoms, _clip2g)
            for _drv in (L_drv, R_drv):
                _set_gripper_target(control, _drv, GRIPPER_DRIVER_OPEN_RAD)
            for _ in range(90):
                state = physics_step(model, state, solver, contacts, scene_info)
            _cab_c2_rel = _min_dist_mm(cable_geoms, _clip2g)
            wp.synchronize()
            _nk_c2 = int(np.argmin(np.abs(state.body_q.numpy()[cable_bodies, 1] - c2y)))
            _z_c2_rel = float(state.body_q.numpy()[cable_bodies][_nk_c2][2]) * 1e3
            _c2_settled = bool(_cab_c2_rel <= 0.5 and abs(_z_c2_rel - (GROOVE_CENTER_Z + _clip_float_z) * 1e3) <= 3.0)
            _c2_settle_rec = {
                "cable_c2_held_mm": round(_cab_c2_held, 3),
                "cable_c2_released_mm": round(_cab_c2_rel, 3),
                "near_c2_cable_z_released_mm": round(_z_c2_rel, 1),
                "groove_z_mm": round((GROOVE_CENTER_Z + _clip_float_z) * 1e3, 1),
                "settled_in_notch": _c2_settled,
            }
            print(
                f"  [C2-DUAL-SETTLE] after RELEASE both grippers (+90 steps): cable<->C2 {_cab_c2_held:+.3f}(claw-held)->{_cab_c2_rel:+.3f}mm(released) "
                f"| near-C2 cable z={_z_c2_rel:.1f} vs groove {(GROOVE_CENTER_Z + _clip_float_z) * 1e3:.1f} => SETTLED_IN_NOTCH={_c2_settled} "
                f"(%0 seat-capture: True=genuine settle held by the groove / False=was claw-HELD, popped from the open-top clip)"
            )
            _cap(f"C2 dual-settle: settled={_c2_settled} cable<->C2_released={_cab_c2_rel:+.2f}")
            print(
                "  [C2-DUAL] dual-finger clamp-push complete (top-down; claw-C2 penetration + contact-force + release-settle logged above)"
            )
        elif _seat_topdown:
            _wall_top = CLIP1_Z + _clip_float_z + 0.030  # clip_parts[3/4] dz0.025+hz0.005 = V-groove wall top
            _z_above_ee = _wall_top + 0.012 + ee_off  # hold the cable ~12mm above the wall tops (+ EE offset)
            _nlift = 14
            for k in range(1, _nlift + 1):
                _tx = float(_plg[0]) + (c2x - float(_plg[0])) * k / _nlift
                _ty = float(_plg[1]) + (c2y - float(_plg[1])) * k / _nlift
                _tz = float(_plg[2]) + (_z_above_ee - float(_plg[2])) * k / _nlift
                state, _ = ik_move_both(
                    model,
                    state,
                    scene_info,
                    solver,
                    contacts,
                    (_tx, _ty, _tz),
                    R_hold,
                    label=f"C2-LIFT{k}/{_nlift}",
                    converge_mm=2.5,
                    speed_factor=0.22,
                )
                for _ in range(15):
                    state = physics_step(model, state, solver, contacts, scene_info)
                _lgc2 = _min_dist_mm(f1L0 + f2L0, _clip2g)
                _lrsep, _ = _hh_clear_mm()
                print(
                    f"  [C2-LIFT] k={k}/{_nlift} EE->({_tx:.3f},{_ty:+.3f},{_tz:.3f}) Lgrip<->C2={_lgc2:+.3f}mm "
                    f"HH-armlink={_lrsep:+.2f}mm (claws ABOVE walls; Lgrip>=0 = no penetration)"
                )
                _cap(f"C2 lift-above-walls {k}/{_nlift}")
            _set_gripper_target(
                control, L_drv, GRIPPER_DRIVER_OPEN_RAD
            )  # release -> cable settles into open-top channel
            for _ in range(60):
                state = physics_step(model, state, solver, contacts, scene_info)
            _lgc2_rel = _min_dist_mm(f1L0 + f2L0, _clip2g)
            print(
                f"  [C2-RELEASE] gripper OPEN -> cable settles into groove (or MISSES if drag mis-delivered); "
                f"Lgrip<->C2={_lgc2_rel:+.3f}mm (claws stayed above walls = no wall penetration)"
            )
            _cap("C2 release-settle (open-top insertion)")
        else:
            c2_seat_ee_z = GROOVE_CENTER_Z + _clip_float_z + ee_off  # CLIP_FLOAT_Z: descend to the FLOATED C2 groove
            for k in range(1, 7):
                zk = float(_plg[2]) + (c2_seat_ee_z - float(_plg[2])) * k / 6
                state, _ = ik_move_both(
                    model,
                    state,
                    scene_info,
                    solver,
                    contacts,
                    (float(_plg[0]), float(_plg[1]), zk),
                    R_hold,
                    label=f"C2-PUSH{k}/6",
                    converge_mm=2.5,
                    speed_factor=0.22,
                )
                for _ in range(20):
                    state = physics_step(model, state, solver, contacts, scene_info)
                _lgc2 = _min_dist_mm(f1L0 + f2L0, _clip2g)  # FLAG-D per-frame L-gripper claws <-> C2 (penetration PV)
                _lrsep, _ = _hh_clear_mm()  # item1 hand-hand ARM-LINK clearance (sphere, matches IK avoid; uncapped)
                print(
                    f"  [C2-PUSH] k={k}/6 Lgrip<->C2={_lgc2:+.3f}mm cable<->C2={_min_dist_mm(cable_geoms, _clip2g):+.3f}mm "
                    f"HH-armlink={_lrsep:+.2f}mm (<0=penetration)"
                )
                _cap(f"C2 seat attempt {k}/6")
        c2_seat_dist = _min_dist_mm(cable_geoms, _clip2g)
        c2_tabN, _ = _claw_table_load(f1L0)
        c2_tab_d = _min_dist_mm(f1L0, _tabg)
        c2_lgrip_dist = _min_dist_mm(f1L0 + f2L0, _clip2g)  # FLAG-D final L-gripper <-> C2 (penetration PV)
        c2_lclaw_c2_N, _ = _claw_c2_load(
            f1L0 + f2L0
        )  # Rs corrected-route metric: L-claw <-> C2 CONTACT FORCE (soft over-pen reaction)
        c2_rclaw_c2_N, _ = _claw_c2_load(f1R0 + f2R0)  # R-claw <-> C2 contact force (dual-finger)
        c2_rgrip_dist = _min_dist_mm(f1R0 + f2R0, _clip2g)  # R-gripper claws <-> C2 (penetration PV, dual-finger)
        print(
            f"  [C2-CLAW-FORCE] L-claw<->C2 pen={c2_lgrip_dist:+.3f}mm N={c2_lclaw_c2_N:.2f} | "
            f"R-claw<->C2 pen={c2_rgrip_dist:+.3f}mm N={c2_rclaw_c2_N:.2f} (N>0 + pen<0 = soft over-penetration; N=0 + pen>=0 = no claw-clip contact)"
        )
        c2_seated = bool(c2_seat_dist <= 0.5)
        # SPACER-CONTAMINATION SPLIT: _clip2g (BOX near c2 XY, no size gate) INCLUDES the spacer box (z-center ~0.81)
        # when SPACER=1 -> cable<->C2 = MIN(cable<->clip-walls, cable<->spacer). Split by z: clip floor = CLIP1_Z+float.
        # If WALLS>>0 but the MIN is ~0/neg, the "seated" is SPACER-CONTACT (cable touches the riser), NOT in-groove.
        _floor_z = CLIP1_Z + _clip_float_z
        _c2_wall_g = [g for g in _clip2g if float(mjd.geom_xpos[g][2]) >= (_floor_z - 0.001)]  # clip V-groove boxes
        _c2_sp_g = [g for g in _clip2g if float(mjd.geom_xpos[g][2]) < (_floor_z - 0.001)]  # spacer riser (z~0.81)
        c2_wall_dist = _min_dist_mm(cable_geoms, _c2_wall_g) if _c2_wall_g else 9e9
        c2_sp_dist = _min_dist_mm(cable_geoms, _c2_sp_g) if _c2_sp_g else 9e9
        print(
            f"  [C2-SPACER-SPLIT] cable<->C2-clip-WALLS={c2_wall_dist:+.3f}mm cable<->C2-SPACER={c2_sp_dist:+.3f}mm "
            f"(n_walls={len(_c2_wall_g)} n_spacer={len(_c2_sp_g)}; c2_seated used MIN={c2_seat_dist:+.3f}. "
            f"WALLS>>0 + SPACER~0 => 'seated' is SPACER-CONTACT not groove = FALSE seat)"
        )
        # item2 HONEST C2-SEAT verdict (fixes the false positive): (a) use the SPACER-EXCLUDED clip-wall distance,
        # (b) REQUIRE the near-C2 cable centre be at the floated GROOVE z (829+float), not the wall base / low z.
        wp.synchronize()
        _cb2 = state.body_q.numpy()[cable_bodies]
        _near_c2 = int(np.argmin(np.abs(_cb2[:, 1] - c2y)))  # cable body nearest C2 in Y
        cable_z_at_c2 = float(_cb2[_near_c2, 2]) * 1e3
        _groove_c2_mm = (GROOVE_CENTER_Z + _clip_float_z) * 1e3
        c2_in_groove = bool(abs(cable_z_at_c2 - _groove_c2_mm) <= 3.0)
        c2_seated_honest = bool(c2_wall_dist <= 0.5 and c2_in_groove)
        print(
            f"  [C2-SEAT-HONEST] cable<->C2-WALLS(spacer-excluded)={c2_wall_dist:+.3f}mm (<=0.5 needed) | "
            f"near-C2 cable z={cable_z_at_c2:.1f}mm vs groove {_groove_c2_mm:.1f} (|d|<=3 needed -> in_groove={c2_in_groove}) "
            f"=> c2_seated_HONEST={c2_seated_honest} (vs naive c2_seated={c2_seated} which counts wall/spacer contact)"
        )
        zc1_final, c1_final_dist = _zc1(), _min_dist_mm(cable_geoms, _clip1g)
        # W0-e producer (%12 addendum 2026-07-05): FINAL settled-frame pin-excluded free-node cable<->C1 min = the ①/②
        # classifier input (%9 pre-read pin); _c1_np_min (episode-min over guide+final) = the separate validity diagnostic.
        _c1np_final = (
            _min_dist_mm([g for g in cable_geoms if g != _seat_geom_mj], _clip1g)
            if _seat_geom_mj is not None
            else c1_final_dist
        )
        _c1_np_min = min(_c1_np_min, _c1np_final)
        _c2_pen_min = min(_c2_pen_min, c2_seat_dist)
        print(
            f"  [C2] C2 SEAT ATTEMPT: cable<->C2={c2_seat_dist:+.3f}mm seated={c2_seated} "
            f"bottomclaw<->table={c2_tab_d:+.2f}mm N={c2_tabN:.1f} | C1 final z={zc1_final:.1f}mm "
            f"cable<->C1={c1_final_dist:+.3f}mm (nonpin_final={_c1np_final:+.3f}mm classifier; epmin={_c1_np_min:+.3f}) "
            f"| FLAG-D Lgrip<->C2={c2_lgrip_dist:+.3f}mm (<0=penetration)"
        )
        _cap(f"C2 seat attempt END: cable<->C2={c2_seat_dist:+.2f}mm seated={c2_seated}")

        # --- VERDICT (honest; the probe expects the negative per prior findings) ---
        wp.synchronize()
        _jq, _jqd = state.joint_q.numpy(), state.joint_qd.numpy()
        finite = bool(np.all(np.isfinite(_jq)) and np.all(np.isfinite(state.body_q.numpy())))
        qvel_ok = bool(finite and float(np.max(np.abs(_jqd))) < 100.0)
        _slips = [r["slip_xy"] for r in guide_legs]
        max_slip = max(_slips) if _slips else 9.9
        mean_slip = float(np.mean(_slips)) if _slips else 9.9
        any_drag = bool(max_slip > 0.5)
        all_cradle = bool(all(r["is_cradle"] for r in guide_legs)) if guide_legs else False
        all_c1_ret = bool(all(r["c1_retained_lowwall"] for r in guide_legs)) if guide_legs else False
        any_jam = bool(any(r["JAM"] for r in guide_legs)) or bool(c2_tab_d <= 0.2 or c2_tabN > 0.5)
        slide_through = bool(max_slip < 0.35 and all_cradle and all_c1_ret and not any_jam and finite)
        # item1/4 SPACER-config summary (min over the guide; <0 = penetration). lr MIN = closest HAND-HAND approach at
        # ARM-LINK level (sphere model = the SAME quantity the active IK COLLISION_AVOIDANCE minimises). rpad_c1/lgrip_c2
        # = finger-clip (pad<->clip). NOTE arm geoms are visible-only in sim -> arm-link sphere clearance is the real
        # IK-avoidance metric, but a sim-clear value is still NON-conservative for the true real-robot wrist envelope.
        _gl = guide_legs or []
        _min_lr = min((r.get("lr_gripper_sep_mm", 9e9) for r in _gl), default=9e9)
        _min_rpad_c1 = min((r.get("rpad_c1_dist_mm", 9e9) for r in _gl), default=9e9)
        _min_lgrip_c2 = min((r.get("lgrip_c2_dist_mm", 9e9) for r in _gl), default=9e9)
        print(
            f"  [C2-FINGERCLIP] min over guide: Rpad<->C1={_min_rpad_c1:+.3f}mm Lgrip<->C2={_min_lgrip_c2:+.3f}mm "
            f"(<0=finger-clip penetration) | min HAND-HAND arm-link clearance={_min_lr:+.3f}mm "
            f"(sphere model, IK avoidance {'ON' if _hh_avoid_on else 'OFF'}; <0=overlap; uncapped)"
        )
        rc2.update(
            {
                "min_handhand_armlink_mm": round(_min_lr, 3),
                "hh_avoidance_on": _hh_avoid_on,
                "min_rpad_c1_mm": round(_min_rpad_c1, 3),
                "min_lgrip_c2_mm": round(_min_lgrip_c2, 3),
                "c2_wall_dist_spacer_excluded_mm": round(c2_wall_dist, 3),
                "cable_z_at_c2_mm": round(cable_z_at_c2, 1),
                "c2_seated_honest": c2_seated_honest,
                "c2_seated_naive": c2_seated,
                "half_unclamp_transition": _trans,
                "L_cradle_after_halfunclamp": L_is_cradle,
                "z_c1_seated_mm": round(z_c1_seated, 1),
                "z_c1_final_mm": round(zc1_final, 1),
                "cable_c1_seat_dist_mm": round(c1_seat_dist, 3),
                "cable_c1_final_dist_mm": round(c1_final_dist, 3),
                "cable_c1_nonpin_final_mm": round(
                    _c1np_final, 3
                ),  # %12 ①/② classifier input (final settled, pin-excluded free-node 床 bar)
                "cable_c1_nonpin_epmin_mm": round(_c1_np_min, 3),
                "cable_c2_pen_epmin_mm": round(_c2_pen_min, 3),  # episode-min penetration diagnostic
                "cable_c2_seat_dist_mm": round(c2_seat_dist, 3),
                "c2_seated": c2_seated,
                "guide_legs": guide_legs,
                "max_abs_slip_xy": round(max_slip, 3),
                "mean_slip_xy": round(mean_slip, 3),
                "any_drag": any_drag,
                "all_cradle_during_guide": all_cradle,
                "all_c1_retained_lowwall": all_c1_ret,
                "any_table_jam": any_jam,
                "cradle_break_x": cradle_break_x,
                "jam_onset_x": jam_onset_x,
                "c2_lclaw_c2_contact_N": round(c2_lclaw_c2_N, 2),
                "c2_rclaw_c2_contact_N": round(c2_rclaw_c2_N, 2),
                "c2_lgrip_c2_pen_mm": round(c2_lgrip_dist, 3),
                "c2_rgrip_c2_pen_mm": round(c2_rgrip_dist, 3),
                "c2_dualseat_on": bool(os.environ.get("C2_DUALSEAT", "0") == "1"),
                "c2_regrasp_verdict": (_c2_regrasp_rec or {}).get("regrasp_verdict"),
                "c2_regrasp_r_reach_resid_mm": (_c2_regrasp_rec or {}).get("r_reach_resid_mm"),
                "c2_regrasp_l_grip_N": (_c2_regrasp_rec or {}).get("l_grip_N"),
                "c2_regrasp_r_grip_N": (_c2_regrasp_rec or {}).get("r_grip_N"),
                "c2_regrasp_ok": (_c2_regrasp_rec or {}).get("regrasp_ok"),
                "c2_regrasp_target_y_span_mm": (_c2_regrasp_rec or {}).get("target_y_span_mm"),
                "c2_regrasp_tilt_theta_deg": (_c2_regrasp_rec or {}).get("tilt_theta_deg"),
                "slide_through": slide_through,
                "finite": finite,
                "qvel_ok": qvel_ok,
            }
        )
        _cons = (
            "SLIDE-THROUGH @CPU-rigid+claw-mu~0.70 -> CONSERVATIVE for 'しごき works' (a flexible/lower-mu real "
            "cable slides MORE) = bankable yes"
            if slide_through
            else "FAILS, MIXED conservatism: (a) DRAG + (b) C2-unreached are NON-conservative @CPU-rigid (rigid cable "
            "+ pad-pinned claw mu~0.70 OVERSTATE drag/unreach; a flexible/lower-mu/GPU cable may slide+reach "
            "better -> confirm before banking the 'しごき' negative); (c) the C2-over-solid bottom-claw "
            "ride-up/cradle-break (void X-ceiling 0.366 < C2 X 0.40) is CONSERVATIVE geometry = transfers"
        )
        print(
            f"  [C2-VERDICT] half_unclamp_cradle={L_is_cradle} | GUIDE max|slip_xy|={max_slip:.3f} "
            f"(mean {mean_slip:+.3f}) -> {'SLIDE' if max_slip < 0.35 else ('DRAG' if max_slip > 0.65 else 'PARTIAL')} "
            f"| all_cradle={all_cradle} cradle_break@X={cradle_break_x} | C1_ret_all={all_c1_ret} "
            f"z_c1 {z_c1_seated:.1f}->{zc1_final:.1f}mm cable<->C1 {c1_seat_dist:+.2f}->{c1_final_dist:+.2f}mm"
        )
        print(
            f"  [C2-VERDICT] C2 reach: cable<->C2 {c2_dist_atseat:+.2f}->{c2_seat_dist:+.2f}mm seated={c2_seated} "
            f"| TABLE-JAM (claw vs SOLID, NOT cable-drag): any_jam={any_jam} jam_onset@X={jam_onset_x} "
            f"(void X-ceil 0.366; C2 X={c2x}) | finite={finite} qvel_ok={qvel_ok}"
        )
        print(f"  [C2-VERDICT] slide_through={slide_through} -> {_cons}")

        # §運用14 video: the FULL sequence (grasp->carry->seat C1->half-unclamp->guide->C2 attempt) + a summary PNG.
        if record_video:
            _out_mp4 = os.path.join(output_dir or ".", "route_c1_to_c2.mp4")
            _subp.run(
                [
                    "ffmpeg",
                    "-loglevel",
                    "error",
                    "-y",
                    "-framerate",
                    "1.5",
                    "-i",
                    os.path.join(_frames_dir, "f%05d.png"),
                    "-vf",
                    "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                    "-pix_fmt",
                    "yuv420p",
                    _out_mp4,
                ],
                check=False,
            )
            _frames = sorted(_glob.glob(os.path.join(_frames_dir, "f*.png")))
            _png = os.path.join(output_dir or ".", "route_c1_to_c2.png")
            if _frames:
                _shutil.copy(_frames[-1], _png)
            for _src, _dst in ((_out_mp4, "route_c1_to_c2.mp4"), (_png, "route_c1_to_c2.png")):
                try:
                    _shutil.copy(_src, os.path.expanduser(f"~/Downloads/{_dst}"))
                except Exception:  # noqa: BLE001
                    pass
            print(
                f"  [C2] §運用14 video -> {_out_mp4} (+ ~/Downloads/route_c1_to_c2.mp4); "
                f"PNG -> {_png} (+ ~/Downloads/route_c1_to_c2.png) [{len(_frames)} frames]"
            )
        # PERCLIP_PIN (b)-pin freeze-scope + route summary -> JSON. The route block exits HERE (before the
        # fn-level metrics dump at the end of _run_mujoco_grasp_route is reached), so persist the headline metrics
        # for %0 cross-PV. Only when the freeze-scope was measured (_fs_on); default route writes nothing extra.
        if output_dir and _fs_on:
            try:
                os.makedirs(output_dir, exist_ok=True)
                with open(os.path.join(output_dir, "route_c2_pin.json"), "w") as _jf:
                    json.dump(
                        {
                            "route_c2_freeze_scope": _freeze_scope_rec,
                            "route_c2_regrasp": _c2_regrasp_rec,  # Rs guide-data charter: R re-grasp (R-reach + R-grip-nonzero, %0 cross-PV)
                            "route_c2_settle": _c2_settle_rec,  # C2_DUALSEAT release-and-settle (%0 seat-capture, charter metric #3)
                            "route_c2_metrics": rc2,  # %3 integrated-route charter: full 5-metric dict for A/B + %0 cross-PV
                            "x_clip": float(x_clip),
                            "y_clip": float(y_clip),
                            "c2x": float(c2x),
                            "c2y": float(c2y),
                            "clip_float_z_mm": round(float(_clip_float_z) * 1e3, 1),
                            "spacer_on": bool(os.environ.get("SPACER", "0") == "1" and _clip_float_z > 0.0),
                            "finite": bool(finite),
                            "qvel_ok": bool(qvel_ok),
                        },
                        _jf,
                        indent=2,
                    )
                print(f"  [C2-PIN] freeze-scope metrics -> {os.path.join(output_dir, 'route_c2_pin.json')}")
            except Exception as _e:  # noqa: BLE001
                print(f"  [C2-PIN] (json dump skipped: {_e})")
        if _demo_rec is not None:  # P3 recorder: finalize with the run verdict BEFORE the mid-fn sys.exit (spec §2.7)
            _demo_rec.finalize(verdict=_c2_regrasp_rec)
        sys.exit(0 if (finite and qvel_ok) else 2)


# grip close-threshold = HALF_OPEN (the L_HALF_UNCLAMP hold point >= gripping / below = reaching), stored as
# float32 to match the recorded grip_cmd dtype exactly (else the recorded half-open falls just below 0.69).
_GRIP_CLOSE_THR = np.float32(GRIPPER_DRIVER_HALF_OPEN_RAD)


def _prepare_recording(recording):
    """Validate a ONE-cell recorded_replay source + precompute the cadence frames (comp1; %12 16:04).

    Args:
        recording: A mapping with ``ee_pos_r``/``ee_pos_l`` [frames, 3], ``grip_cmd`` [frames, 2] (cols
            [L, R]), ``phase_id`` [frames]. 81 single-cell (the interface carries no world index, CC2-CH3).

    Returns:
        A dict with the validated arrays + int ``step_f``/``next_f`` (770 steps) precomputed single-source
        with ``route_demo_to_bc.py``:255-258.
    """
    req = ("ee_pos_r", "ee_pos_l", "grip_cmd", "phase_id")
    missing = [k for k in req if k not in recording]
    if missing:
        raise ValueError(f"recording missing {missing}; need {req}")
    ee_r = np.asarray(recording["ee_pos_r"], dtype=np.float32)
    ee_l = np.asarray(recording["ee_pos_l"], dtype=np.float32)
    grip = np.asarray(recording["grip_cmd"], dtype=np.float32)
    phase = np.asarray(recording["phase_id"]).astype(np.int64)
    n_frames = ee_r.shape[0]
    if not (ee_l.shape[0] == grip.shape[0] == phase.shape[0] == n_frames):
        raise ValueError("recording arrays have inconsistent frame counts")
    if n_frames < _REC_LAST_CTRL_FRAME + 1:
        raise ValueError(f"recording has {n_frames} frames; need >= {_REC_LAST_CTRL_FRAME + 1}")
    if ee_r.shape[1:] != (3,) or ee_l.shape[1:] != (3,) or grip.shape[1:] != (2,):
        raise ValueError("ee_pos must be [frames, 3] and grip_cmd [frames, 2]")
    # cadence single-source (route_demo_to_bc.py:255-258): cf = 0,cad,..,LAST; action = delta step_f -> next_f.
    cf = np.arange(0, _REC_LAST_CTRL_FRAME + 1, _REC_CADENCE)
    step_f, next_f = cf[:-1], cf[1:]
    # phase-map TOTAL coverage (%12: every recorded phase_id maps to exactly one [0, 6)).
    uncovered = {int(p) for p in np.unique(phase)} - set(_RECORDED_PHASE_TO_G)
    if uncovered:
        raise ValueError(f"recorded phase_id {sorted(uncovered)} not in _RECORDED_PHASE_TO_G")
    return {
        "ee_pos_r": ee_r,
        "ee_pos_l": ee_l,
        "grip_cmd": grip,
        "phase_id": phase,
        "step_f": step_f,
        "next_f": next_f,
    }


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

    def __init__(
        self,
        arm_q_start,
        arm_qd_start,
        horizon,
        state_0=None,
        control=None,
        state_bank=None,
        recording=None,
        forbid_banked_fork=False,
    ):
        """Wire the per-world index maps + optional physics handles + the recorded_replay source.

        Args:
            arm_q_start: Per-world arm ``joint_q`` start indices (env-computed; cable FREE-root => q != qd).
            arm_qd_start: Per-world arm ``joint_qd`` start indices.
            horizon: Episode horizon [steps].
            state_0: The Newton physics state to re-pose at reset (None for pure-index construction/tests).
            control: The Newton control whose ``joint_target_pos`` carries the servo targets (None => skip seed).
            state_bank: Optional ``{k: banked_dict}`` phase-k state bank (empty => reset is env-authoritative).
            recording: Optional ONE-cell recorded_replay source (:meth:`step_target`) -- a mapping with
                ``ee_pos_r``/``ee_pos_l`` [frames, 3], ``grip_cmd`` [frames, 2] (cols [L, R]), ``phase_id``
                [frames]. 81 single-cell (interface carries no world index, CC2-CH3). None => step_target
                raises (pure-index construction).
            forbid_banked_fork: comp3 (R1) hard-guard. When True, :meth:`reset_to_phase` raises for
                ``k >= 1`` (the banked phase-k fork needs the DoD-7(b) cable re-seed = comp3b; comp3 scope is
                G1 nominal k=0). Default False keeps the general banked-restore capability (state-bank unit).
        """
        self._maps = build_perworld_index_maps(arm_q_start, arm_qd_start)
        self._horizon = int(horizon)
        self._state_0 = state_0
        self._control = control
        self._state_bank = dict(state_bank) if state_bank else {}
        self._requested_phase = 0
        self._forbid_banked_fork = bool(forbid_banked_fork)
        self._grip_rb_checked = False  # one-time device-readback assert flag (CC3-CH5/R8) for apply_recorded_grip
        if control is not None:
            servo_seed_assert(control.joint_target_pos.numpy(), self._maps["all_driver_dofs"])
        self._recording = _prepare_recording(recording) if recording is not None else None

    def reset_to_phase(self, k: int) -> None:
        """Fork all worlds to phase ``k``'s banked state (SCALAR ``k``; §13.2/§13.3/§13.4).

        Restores the banked arm + all-16 gripper ``joint_q``/``joint_qd`` + the banked grip target
        (banked-CLOSED for a gripped phase, NOT a blanket-OPEN). Phase-0 / no bank => no-op (the env-core
        reset is authoritative), matching the stub. Per-world different-``k`` is deferred to the trainer.

        Raises:
            NotImplementedError: If ``k >= 1`` and this executor was built with ``forbid_banked_fork=True``
                (comp3 R1 hard-guard: the banked phase-k fork needs the DoD-7(b) cable re-seed = comp3b).
        """
        if int(k) >= 1 and self._forbid_banked_fork:
            raise NotImplementedError(
                f"reset_to_phase(k={int(k)}) is comp3b: the banked phase-k fork restores a gripped arm/gripper "
                "but NOT the cable to phase k (DoD-7(b) cable re-seed is unwired) -> mismatched state. comp3 "
                "scope = G1 nominal (k=0). Built with forbid_banked_fork=True until the cable-fork re-seed lands."
            )
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

        recorded_replay (Layer-B, %12 15:44/16:04): the per-step base target = the recorded ``ee_pos`` at the
        NEXT control frame (fork-(iv) base == achieved-path waypoint, single-source with
        ``route_demo_to_bc.py``:255-287). ``grip_2``/``is_dual`` come from the recorded ``grip_cmd`` (CC5-2:
        NEVER phase-derived). ``phase_id`` = the recorded 15-phase mapped to the 6-phase G-clock
        (:data:`_RECORDED_PHASE_TO_G`) and drives ONLY clip-selection + obs-onehot + state_bank keying. Past
        the recording => hold the last waypoint (grippers latched).

        Returns:
            ``(target_6d [R_xyz, L_xyz] float32, phase_id int in [0, 6), grip_2 [R, L] {0,1} float32,
            is_dual bool)``.
        """
        rec = self._recording
        if rec is None:
            raise NotImplementedError("recorded_replay needs recording= (pure-index construction has none)")
        n_steps = len(rec["next_f"])  # 770 (= len(cf) - 1)
        tt = min(max(int(t), 0), n_steps - 1)  # pad-to-horizon: hold the last waypoint
        tgt_f = int(rec["next_f"][tt])  # cf[t+1] = next-waypoint frame (target)
        pg_f = int(rec["step_f"][tt])  # cf[t]   = current frame (phase + grip)
        # target_6d = ee_pos [R, L] -- ⚠ recorder _STACK_KEYS stacks [L, R]; consumer reads R-first (CC2-CH5).
        target_6d = np.concatenate([rec["ee_pos_r"][tgt_f], rec["ee_pos_l"][tgt_f]]).astype(np.float32)
        # grip_2 [R, L] {0,1} -- ⚠ recorded grip_cmd cols are [L, R] (route_demo_to_bc.py:13, OPPOSITE of the
        # action layout). gripping := grip_cmd >= HALF_OPEN (the L_HALF_UNCLAMP hold point). CC5-2: from grip.
        gc = rec["grip_cmd"][pg_f]  # [L, R]
        # ⚠ float32-consistent compare: the recorded half-open == float32(HALF_OPEN)=0.6899999976; a float64
        # compare (float(gc)>=0.69) wrongly EXCLUDES it, dropping the L_HALF_UNCLAMP hold (must be grip=1).
        grip_r = 1.0 if gc[1] >= _GRIP_CLOSE_THR else 0.0
        grip_l = 1.0 if gc[0] >= _GRIP_CLOSE_THR else 0.0
        grip_2 = np.array([grip_r, grip_l], dtype=np.float32)  # [R, L]
        is_dual = bool(grip_r > 0.0 and grip_l > 0.0)  # both arms gripping (CC5-2: NOT from phase)
        phase_id = _RECORDED_PHASE_TO_G[int(rec["phase_id"][pg_f])]  # 15 -> 6 (%12 ruling; total-coverage)
        return target_6d, phase_id, grip_2, is_dual

    def apply_recorded_grip(self, route_steps, sub_i):
        """comp3 (R2): write the recorded ``grip_cmd`` staircase (RAW radians) for physics sub-frame ``sub_i``.

        The gripper is NOT a policy action -- it replays the recorded per-PHYSICS-frame schedule EXACTLY
        (engineered jumps + staircase incl 0.667 cage90 / 0.69 L_HALF_UNCLAMP hold; NO thresholding /
        smoothing / re-ramp). For each world at route step ``t_w = route_steps[w]`` the physics frame is
        ``cf[t_w] + sub_i`` (``cf[t] = step_f[t]``; ``_REC_CADENCE == PHYSICS_STEPS_PER_RL`` => cf[t]+i is
        1:1 with the env drive-loop sub-frame, CC3-CH9). The recorded ``grip_cmd`` columns are ``[L, R]``
        (route_demo_to_bc.py:13 footgun -- OPPOSITE the action layout): col 0 -> LEFT driver dofs, col 1 ->
        RIGHT driver dofs. The servo target is written via a SINGLE read -> mutate (:func:`set_gripper_target`,
        the §13.6 G12 SOLE per-step gripper writer) -> ``.assign()`` cycle (CC3-CH5: a ``.numpy()`` host copy
        never reaches the solver unless assigned back), with a one-time device-readback assert (R8).

        Args:
            route_steps: Per-world RL route step ``t_w``, sequence of int length ``n_world``.
            sub_i: The physics sub-frame index within the RL step, int in ``[0, _REC_CADENCE)``.
        """
        rec = self._recording
        if rec is None:
            raise NotImplementedError("apply_recorded_grip needs recording= (pure-index construction has none)")
        step_f = rec["step_f"]
        grip = rec["grip_cmd"]  # [frames, 2], cols [L, R]
        n_steps = len(step_f)
        n_frames = grip.shape[0]
        jtp = self._control.joint_target_pos.numpy()  # host copy (CC3-CH5)
        for w, t in enumerate(route_steps):
            tt = min(max(int(t), 0), n_steps - 1)  # pad-to-horizon: hold the last waypoint (mirror step_target)
            f = min(int(step_f[tt]) + int(sub_i), n_frames - 1)
            set_gripper_target(jtp, self._maps["l_driver_dofs"][w], float(grip[f, 0]))  # [L] -> LEFT drivers
            set_gripper_target(jtp, self._maps["r_driver_dofs"][w], float(grip[f, 1]))  # [R] -> RIGHT drivers
        self._control.joint_target_pos.assign(jtp)
        if not self._grip_rb_checked:  # one-time device-readback: confirm the .assign() reached the solver
            rb = self._control.joint_target_pos.numpy()
            for w, t in enumerate(route_steps):
                tt = min(max(int(t), 0), n_steps - 1)
                f = min(int(step_f[tt]) + int(sub_i), n_frames - 1)
                for d in self._maps["l_driver_dofs"][w]:
                    assert abs(float(rb[d]) - float(grip[f, 0])) < 1e-6, f"grip .assign() did not reach dof {d}"
                for d in self._maps["r_driver_dofs"][w]:
                    assert abs(float(rb[d]) - float(grip[f, 1])) < 1e-6, f"grip .assign() did not reach dof {d}"
            self._grip_rb_checked = True

    def reseed_grip_open(self, env_ids):
        """comp3 (R1): reset-time re-seed the gripper POSITION-servo target to OPEN both arms for ``env_ids``.

        The env-core k=0 reset re-poses arm + gripper ``joint_q`` (28-wide) and zeroes ``joint_qd``, but the
        servo TARGET would otherwise carry the episode-end CLOSED command -> the gripper re-closes on step 1
        (cross-episode leak). Re-seed the driver targets to ``GRIPPER_DRIVER_OPEN_RAD`` = route step-0 grip
        (both OPEN; dual-arm ADAPT of the AR:1095-1104 mirror, NOT AR's L-close/R-open) via a SINGLE read ->
        mutate -> ``.assign()`` (device-robust CC3-CH5) with a device-readback assert (R8). Per-world SUBSET
        (``env_ids``), not an all-world clobber (K1c); the sole RESET-time servo writer alongside
        :func:`apply_banked_restore`.

        Args:
            env_ids: The world indices being reset, iterable of int.
        """
        jtp = self._control.joint_target_pos.numpy()  # host copy (CC3-CH5)
        for w in env_ids:
            w = int(w)
            set_gripper_target(jtp, self._maps["l_driver_dofs"][w], GRIPPER_DRIVER_OPEN_RAD)
            set_gripper_target(jtp, self._maps["r_driver_dofs"][w], GRIPPER_DRIVER_OPEN_RAD)
        self._control.joint_target_pos.assign(jtp)
        rb = self._control.joint_target_pos.numpy()  # device-readback: confirm OPEN reached the solver
        for w in env_ids:
            for d in self._maps["l_driver_dofs"][int(w)] + self._maps["r_driver_dofs"][int(w)]:
                assert abs(float(rb[d]) - GRIPPER_DRIVER_OPEN_RAD) < 1e-6, f"reseed OPEN did not reach dof {d}"
