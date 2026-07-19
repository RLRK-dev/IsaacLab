# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""State snapshot for per-STEP save/restore in routing orchestrator.

Uses the same data structure as newton_skill_env_base.save_precondition_cache.
Memory: ~4KB/world × 43 steps × 256 worlds ≈ 44 MB.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class StateSnapshot:
    """Complete physics state at a STEP boundary."""

    step_id: int
    body_q: np.ndarray  # cable + robot body positions/orientations
    body_qd: np.ndarray  # velocities
    fk_jq: np.ndarray  # FK joint positions
    clip_status: list[bool]  # C1-C5 fixed status
    finger_l: float = 0.04  # left finger opening [m]
    finger_r: float = 0.04  # right finger opening [m]
    ik_target_l: tuple[float, float, float] | None = None  # left IK target (x,y,z)
    ik_target_r: tuple[float, float, float] | None = None  # right IK target (x,y,z)


class SnapshotManager:
    """Manages per-STEP state snapshots for save/restore."""

    def __init__(self):
        self._snapshots: dict[int, StateSnapshot] = {}

    def save(
        self,
        step_id: int,
        state_0,
        fk_state,
        clip_status: list[bool],
        ik_target_l: tuple[float, float, float] | None = None,
        ik_target_r: tuple[float, float, float] | None = None,
        fk_jq_indices: tuple[int, int, int, int] = (7, 8, 16, 17),
    ) -> None:
        """Save physics state before STEP execution.

        Args:
            step_id: STEP number (1-43).
            state_0: Newton physics state (has body_q, body_qd).
            fk_state: FK state (has joint_q).
            clip_status: List of 5 bools for C1-C5 fixed status.
            ik_target_l: Current left IK target (x,y,z) or None.
            ik_target_r: Current right IK target (x,y,z) or None.
            fk_jq_indices: Joint indices for L/R finger positions.
                Default: (7, 8, 16, 17) = L_j7, L_j8, R_j7, R_j8.
        """
        fk_jq = fk_state.joint_q.numpy().copy()
        l7, l8, r7, r8 = fk_jq_indices
        self._snapshots[step_id] = StateSnapshot(
            step_id=step_id,
            body_q=state_0.body_q.numpy().copy(),
            body_qd=state_0.body_qd.numpy().copy(),
            fk_jq=fk_jq,
            clip_status=list(clip_status),
            finger_l=float(fk_jq[l7]),
            finger_r=float(fk_jq[r7]),
            ik_target_l=ik_target_l,
            ik_target_r=ik_target_r,
        )

    def restore(
        self,
        step_id: int,
        state_0,
        fk_state,
        fk_model,
        solver=None,
    ) -> StateSnapshot:
        """Restore physics state to a saved snapshot.

        Follows the reset pattern once embodied by ``restore_world_body_state``
        (removed 2026-07-19, kinematic-complete-removal) in
        :mod:`thread_isaac_lab.envs.newton_skill_env_base`: after writing
        ``body_q`` / ``body_qd`` / ``joint_q``, the VBD solver's
        ``body_q_prev`` must be overwritten with the **just-restored**
        ``body_q`` (not the pre-save value). This zeroes the implicit
        per-frame velocity ``(body_q - body_q_prev) / dt`` that VBD uses
        on its next ``solver.step()`` call. Skipping this step
        re-introduces the VBD cable-explosion pattern documented at
        ``newton_aerial_regrasp_env.py:1301`` ("L3 fix: also update
        ``body_q_prev``") and in ``thread-vault/06-Knowledge/LL-Newton.md``
        §Episode Reset.

        Args:
            step_id: STEP number to restore.
            state_0: Newton physics state to overwrite.
            fk_state: FK state to overwrite.
            fk_model: FK model for eval_fk after restore.
            solver: Optional Newton solver. When provided and the solver
                exposes a ``body_q_prev`` attribute (e.g. ``SolverVBD``),
                it is overwritten with ``snap.body_q`` to match the
                just-restored state. Pass ``None`` for solvers without
                this state or when the caller handles it externally.

        Returns:
            The restored StateSnapshot (caller reads clip_status from it).

        Raises:
            KeyError: If step_id has no saved snapshot.
        """
        import newton  # local import so snapshot.py loads without newton installed

        snap = self._snapshots[step_id]
        state_0.body_q.assign(snap.body_q)
        state_0.body_qd.assign(snap.body_qd)
        fk_state.joint_q.assign(snap.fk_jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        # Phase 5-1b C6: align solver.body_q_prev with the restored body_q
        # to prevent the VBD velocity spike on the next solver step.
        if solver is not None:
            body_q_prev = getattr(solver, "body_q_prev", None)
            if body_q_prev is not None:
                body_q_prev.assign(snap.body_q)
        return snap

    def has(self, step_id: int) -> bool:
        return step_id in self._snapshots

    def clear(self) -> None:
        self._snapshots.clear()

    @property
    def saved_steps(self) -> list[int]:
        return sorted(self._snapshots.keys())
