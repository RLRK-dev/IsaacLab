# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""State schema and helpers for no-reset chain-runtime handoff."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class ChainRuntimeState:
    """Newton state captured for a chain handoff between skills.

    The schema is intentionally explicit so a future live chain evaluator can
    verify that solver, body, and skill metadata move together instead of
    measuring a reset-based proxy.
    """

    source_skill: str
    world_idx: int
    step_id: int
    body_q: np.ndarray | None
    body_qd: np.ndarray | None
    body_q_prev: np.ndarray | None = None
    fk_jq: np.ndarray | None = None
    per_world_fk_jq: np.ndarray | None = None
    clip_status: dict[str, Any] = field(default_factory=dict)
    world_episode_identity: dict[str, Any] = field(default_factory=dict)
    solver_state: dict[str, Any] = field(default_factory=dict)
    skill_state: dict[str, Any] = field(default_factory=dict)
    rng_state: dict[str, Any] = field(default_factory=dict)
    topology_fingerprint: dict[str, Any] = field(default_factory=dict)
    validation_metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        """Return a small JSON-safe summary for dry preflight reports."""

        return {
            "source_skill": self.source_skill,
            "world_idx": self.world_idx,
            "step_id": self.step_id,
            "body_q_shape": None if self.body_q is None else list(self.body_q.shape),
            "body_qd_shape": None if self.body_qd is None else list(self.body_qd.shape),
            "body_q_prev_shape": None if self.body_q_prev is None else list(self.body_q_prev.shape),
            "fk_jq_shape": None if self.fk_jq is None else list(self.fk_jq.shape),
            "per_world_fk_jq_shape": None
            if self.per_world_fk_jq is None
            else list(self.per_world_fk_jq.shape),
            "topology_fingerprint": dict(self.topology_fingerprint),
            "validation_metadata": dict(self.validation_metadata),
        }


@dataclass
class ChainRuntimeRestoreReport:
    """Validation report for importing a :class:`ChainRuntimeState`."""

    ok: bool
    source_skill: str
    target_skill: str
    topology_match: bool
    body_q_finite: bool
    body_qd_finite: bool
    body_q_prev_aligned: bool
    missing_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _as_numpy_copy(value: Any) -> np.ndarray | None:
    """Copy common array/tensor values to a NumPy array."""

    if value is None:
        return None
    if hasattr(value, "numpy"):
        return np.array(value.numpy(), copy=True)
    if hasattr(value, "detach"):
        return value.detach().cpu().numpy().copy()
    return np.array(value, copy=True)


def _assign_array(target: Any, value: np.ndarray | None) -> bool:
    """Assign a NumPy array to a Warp-like or NumPy-like target."""

    if value is None or target is None:
        return False
    if hasattr(target, "assign"):
        target.assign(value)
        return True
    try:
        target[...] = value
    except Exception:
        return False
    return True


def _field_array(obj: Any, name: str) -> np.ndarray | None:
    """Return a copied field array from an object if present."""

    return _as_numpy_copy(getattr(obj, name, None))


def _small_mapping_from_env(env: Any, names: tuple[str, ...]) -> dict[str, Any]:
    """Collect compact copied attributes from an environment."""

    values: dict[str, Any] = {}
    for name in names:
        if hasattr(env, name):
            values[name] = _as_numpy_copy(getattr(env, name))
    return values


def make_chain_topology_fingerprint(env: Any) -> dict[str, Any]:
    """Build a compact topology fingerprint for state compatibility checks."""

    model = getattr(env, "_model", None)
    cable_bodies = getattr(env, "_cable_bodies", None)
    world_offsets = getattr(env, "_bws", None)
    return {
        "env_class": env.__class__.__name__,
        "world_count": getattr(env, "_world_count", None),
        "num_envs": getattr(env, "num_envs", None),
        "num_observations": getattr(env, "num_observations", None),
        "num_actions": getattr(env, "num_actions", None),
        "body_count": getattr(model, "body_count", None),
        "joint_count": getattr(model, "joint_count", None),
        "cable_body_shape": None if cable_bodies is None else list(np.asarray(cable_bodies).shape),
        "world_offsets_shape": None if world_offsets is None else list(np.asarray(world_offsets).shape),
    }


def validate_chain_state_schema(state: ChainRuntimeState) -> ChainRuntimeRestoreReport:
    """Validate that a chain state has the mandatory finite body arrays."""

    missing: list[str] = []
    if state.body_q is None:
        missing.append("body_q")
    if state.body_qd is None:
        missing.append("body_qd")
    body_q_finite = state.body_q is not None and bool(np.isfinite(state.body_q).all())
    body_qd_finite = state.body_qd is not None and bool(np.isfinite(state.body_qd).all())
    body_q_prev_aligned = False
    if state.body_q_prev is not None and state.body_q is not None:
        body_q_prev_aligned = state.body_q_prev.shape == state.body_q.shape and bool(
            np.isfinite(state.body_q_prev).all()
        )
    warnings = []
    if state.body_q_prev is None:
        warnings.append("body_q_prev_missing_import_will_align_to_body_q")
    return ChainRuntimeRestoreReport(
        ok=not missing and body_q_finite and body_qd_finite,
        source_skill=state.source_skill,
        target_skill="schema",
        topology_match=True,
        body_q_finite=body_q_finite,
        body_qd_finite=body_qd_finite,
        body_q_prev_aligned=body_q_prev_aligned,
        missing_fields=missing,
        warnings=warnings,
    )


def validate_chain_state_for_env(
    env: Any,
    state: ChainRuntimeState,
    *,
    target_skill: str | None = None,
) -> ChainRuntimeRestoreReport:
    """Validate a state against an environment topology."""

    schema_report = validate_chain_state_schema(state)
    env_fingerprint = make_chain_topology_fingerprint(env)
    expected_body_count = env_fingerprint.get("body_count")
    observed_body_count = state.topology_fingerprint.get("body_count")
    topology_match = True
    warnings = list(schema_report.warnings)
    if expected_body_count is not None and observed_body_count is not None:
        topology_match = int(expected_body_count) == int(observed_body_count)
        if not topology_match:
            warnings.append("body_count_mismatch")
    return ChainRuntimeRestoreReport(
        ok=schema_report.ok and topology_match,
        source_skill=state.source_skill,
        target_skill=target_skill or env.__class__.__name__,
        topology_match=topology_match,
        body_q_finite=schema_report.body_q_finite,
        body_qd_finite=schema_report.body_qd_finite,
        body_q_prev_aligned=schema_report.body_q_prev_aligned,
        missing_fields=schema_report.missing_fields,
        warnings=warnings,
    )


def export_chain_state_from_env(
    env: Any,
    *,
    source_skill: str | None = None,
    world_idx: int = 0,
    step_id: int = 0,
    validation_metadata: dict[str, Any] | None = None,
) -> ChainRuntimeState:
    """Export the shared Newton state from an environment for chain handoff."""

    state_0 = getattr(env, "_state_0", None)
    solver = getattr(env, "_solver", None)
    fk_state = getattr(env, "_fk_state", None)
    return ChainRuntimeState(
        source_skill=source_skill or env.__class__.__name__,
        world_idx=world_idx,
        step_id=step_id,
        body_q=_field_array(state_0, "body_q"),
        body_qd=_field_array(state_0, "body_qd"),
        body_q_prev=_field_array(solver, "body_q_prev"),
        fk_jq=_field_array(fk_state, "joint_q"),
        per_world_fk_jq=_as_numpy_copy(getattr(env, "_per_world_fk_jq", None)),
        clip_status=_small_mapping_from_env(
            env,
            (
                "clip_inserted",
                "clip_closed",
                "clip_status",
                "_target_seg_indices_r",
                "_target_seg_indices_l",
                "_groove_seg_indices",
            ),
        ),
        world_episode_identity=_small_mapping_from_env(
            env,
            (
                "episode_length_buf",
                "reset_buf",
                "time_out_buf",
                "_world_episode_length",
                "_total_env_steps",
            ),
        ),
        solver_state=_small_mapping_from_env(env, ("_prev_body_q", "_last_body_q", "_last_body_qd")),
        skill_state=_small_mapping_from_env(
            env,
            (
                "_last_actions",
                "_ee_target_right",
                "_ee_target_left",
                "_ee_quat_right",
                "_ee_quat_left",
                "success_sustain_count",
            ),
        ),
        topology_fingerprint=make_chain_topology_fingerprint(env),
        validation_metadata=validation_metadata or {},
    )


def import_chain_state_into_env(
    env: Any,
    state: ChainRuntimeState,
    *,
    target_skill: str | None = None,
    validate: bool = True,
) -> ChainRuntimeRestoreReport:
    """Import a chain state into an environment without triggering reset."""

    report = validate_chain_state_for_env(env, state, target_skill=target_skill)
    if validate and not report.ok:
        return report

    state_0 = getattr(env, "_state_0", None)
    solver = getattr(env, "_solver", None)
    fk_state = getattr(env, "_fk_state", None)
    warnings = list(report.warnings)

    if state_0 is not None:
        if not _assign_array(getattr(state_0, "body_q", None), state.body_q):
            warnings.append("body_q_assign_failed")
        if not _assign_array(getattr(state_0, "body_qd", None), state.body_qd):
            warnings.append("body_qd_assign_failed")

    if solver is not None:
        body_q_prev_target = getattr(solver, "body_q_prev", None)
        if body_q_prev_target is not None:
            _assign_array(body_q_prev_target, state.body_q)
            warnings.append("body_q_prev_aligned_to_imported_body_q")

    if fk_state is not None and state.fk_jq is not None:
        if not _assign_array(getattr(fk_state, "joint_q", None), state.fk_jq):
            warnings.append("fk_jq_assign_failed")

    if state.per_world_fk_jq is not None and hasattr(env, "_per_world_fk_jq"):
        _assign_array(getattr(env, "_per_world_fk_jq", None), state.per_world_fk_jq)

    return ChainRuntimeRestoreReport(
        ok=report.ok and "body_q_assign_failed" not in warnings and "body_qd_assign_failed" not in warnings,
        source_skill=state.source_skill,
        target_skill=target_skill or env.__class__.__name__,
        topology_match=report.topology_match,
        body_q_finite=report.body_q_finite,
        body_qd_finite=report.body_qd_finite,
        body_q_prev_aligned=True,
        missing_fields=report.missing_fields,
        warnings=warnings,
    )
