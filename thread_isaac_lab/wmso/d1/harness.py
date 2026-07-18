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
from .identity import SCRIPTED_CLOSURE_MEMBERS, WAIT_CLOSURE_MEMBERS, source_closure_sha256


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
    if not adm.identity_pinned:
        reasons.append("identity_pinned is false")
    schema = contract.obs_action_schema
    if schema.field_semantics is FieldSemantics.UNRESOLVED:
        reasons.append("obs_action_schema.field_semantics=UNRESOLVED (no generic shape acceptance)")
    elif not (schema.obs_fields or schema.action_fields):
        reasons.append("RESOLVED schema has no obs/action fields")
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


def validate_manifest(manifest: dict, repo_root: str, *, require_closure: bool = True) -> list[str]:
    """Validate a skill-contracts manifest dict; return a list of problems (empty means valid).

    Checks that the top-level D1 exit is ``HOLD``; that there are exactly nine skill rows; and that
    every row's offline/closed-loop authority is ``False``, its ``contract_conformant`` is a bool, and
    an ``identity_pinned`` row carries identity pins. When ``require_closure`` is true, each
    source-closure pin is recomputed and must match (fail-closed: a missing member raises).

    Args:
        manifest: The parsed ``skill_contracts_manifest.json``.
        repo_root: Repository root the source-closure members are relative to.
        require_closure: Whether to recompute and verify the source-closure pins against the tree.

    Returns:
        A list of human-readable problems; empty when the manifest is internally valid.

    Raises:
        FileNotFoundError: if ``require_closure`` and a source-closure member is absent.
        ValueError: if ``require_closure`` and a recomputed source-closure differs from its pin.
    """
    problems: list[str] = []
    if manifest.get("d1_exit") != "HOLD":
        problems.append(f"d1_exit must be HOLD, got {manifest.get('d1_exit')!r}")
    if require_closure:
        closures = manifest.get("source_closures", {})
        for name, members in (("SCRIPTED", SCRIPTED_CLOSURE_MEMBERS), ("WAIT", WAIT_CLOSURE_MEMBERS)):
            pinned = closures.get(name, {}).get("source_closure_sha256")
            if pinned is None:
                problems.append(f"source_closures.{name} missing a pin")
                continue
            validate_source_closure(pinned, members, repo_root)
    skills = manifest.get("skills", [])
    if len(skills) != 9:
        problems.append(f"expected 9 skill rows, got {len(skills)}")
    for row in skills:
        sid = row.get("skill_id", "?")
        adm = row.get("admissibility", {})
        if adm.get("offline_orchestration_admissible") is not False:
            problems.append(f"{sid}: offline_orchestration_admissible must be false")
        if adm.get("closed_loop_admissible") is not False:
            problems.append(f"{sid}: closed_loop_admissible must be false")
        if not isinstance(adm.get("contract_conformant"), bool):
            problems.append(f"{sid}: contract_conformant must be a bool")
        if adm.get("identity_pinned") is True and not row.get("identity"):
            problems.append(f"{sid}: identity_pinned=true but no identity pins")
    return problems
