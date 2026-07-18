# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Fail-closed WMSO D1 contract-test harness.

Evaluates whether a published :class:`.SkillLifecycleContract` is conformant and provides the
negative-control validators the tests exercise. Every check must come out *differently* on a broken
input than on a good one. The harness never sets an authority axis true: a contract asserting
``offline_orchestration_admissible`` or ``closed_loop_admissible`` is rejected. Contract
``contract_conformant`` is a validated result, never a bare constant.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    ROOT_REQUIRED_FIELDS,
    BeliefValue,
    FieldSemantics,
    HashRef,
    SkillLifecycleContract,
    SnapshotRef,
)
from .identity import source_closure_sha256


@dataclass
class ConformanceResult:
    """Result of a conformance evaluation."""

    conformant: bool
    reasons: list[str]


def evaluate_conformance(contract: SkillLifecycleContract) -> ConformanceResult:
    """Evaluate a contract's ``contract_conformant`` status with explicit fail-close reasons.

    A contract is non-conformant if it claims any orchestration authority, if its schema field
    semantics are unresolved, if its freshness bound is null, or if its support boundary is empty.

    Args:
        contract: The published skill lifecycle contract.

    Returns:
        A :class:`ConformanceResult` whose ``conformant`` is ``True`` only when no reason applies.
    """
    reasons: list[str] = []
    adm = contract.admissibility
    if adm.offline_orchestration_admissible:
        reasons.append("offline_orchestration_admissible must be false at D1")
    if adm.closed_loop_admissible:
        reasons.append("closed_loop_admissible must be false at D1")
    if contract.obs_action_schema.field_semantics is FieldSemantics.UNRESOLVED:
        reasons.append("obs_action_schema.field_semantics=UNRESOLVED (no generic shape acceptance)")
    if contract.freshness.max_staleness_s is None:
        reasons.append("freshness.max_staleness_s is None")
    sb = contract.support_boundary
    if sb.region_ref is None and sb.in_support_predicate is None:
        reasons.append("support_boundary has neither region_ref nor in_support_predicate")
    return ConformanceResult(conformant=not reasons, reasons=reasons)


def assert_no_authority(contract: SkillLifecycleContract) -> None:
    """Raise if a contract grants any offline/closed-loop authority (positive authority control)."""
    if contract.admissibility.offline_orchestration_admissible:
        raise ValueError("offline_orchestration_admissible must be false at D1")
    if contract.admissibility.closed_loop_admissible:
        raise ValueError("closed_loop_admissible must be false at D1")


def parse_root_fields(payload: dict) -> dict:
    """Return ``payload`` if its keys are exactly the required root set, else raise (unknown/missing reject).

    Args:
        payload: A mapping of contract root field names to values.

    Raises:
        ValueError: if any required field is missing or any unknown field is present.
    """
    keys = set(payload)
    missing = ROOT_REQUIRED_FIELDS - keys
    unknown = keys - ROOT_REQUIRED_FIELDS
    if missing:
        raise ValueError(f"missing required contract fields: {sorted(missing)}")
    if unknown:
        raise ValueError(f"unknown contract fields: {sorted(unknown)}")
    return payload


def parse_belief_value(payload: dict) -> BeliefValue:
    """Parse a belief-ref value as the SNAPSHOT | HASH_REF tagged union (both-or-neither rejects, I2).

    Args:
        payload: A mapping that must contain exactly one of ``canonical_belief_snapshot`` / ``ref_hash``.

    Raises:
        ValueError: if both or neither discriminant key is present.
    """
    has_snapshot = "canonical_belief_snapshot" in payload
    has_ref = "ref_hash" in payload
    if has_snapshot == has_ref:
        raise ValueError("belief_ref must carry exactly one of canonical_belief_snapshot / ref_hash")
    if has_snapshot:
        return SnapshotRef(canonical_belief_snapshot=payload["canonical_belief_snapshot"])
    return HashRef(ref_hash=payload["ref_hash"])


def validate_source_closure(pinned_sha256: str, members: tuple[str, ...] | list[str], repo_root: str) -> None:
    """Raise if the recomputed source-closure aggregate does not match the pinned value (fail-closed).

    Args:
        pinned_sha256: The manifest-pinned source-closure aggregate hash.
        members: The enumerated closure members (repo-relative paths).
        repo_root: Repository root the members are relative to.

    Raises:
        FileNotFoundError: if a member is missing (fail-closed).
        ValueError: if the recomputed aggregate differs from ``pinned_sha256``.
    """
    recomputed = source_closure_sha256(members, repo_root)
    if recomputed != pinned_sha256:
        raise ValueError(f"source-closure mismatch: pinned {pinned_sha256} != recomputed {recomputed}")
