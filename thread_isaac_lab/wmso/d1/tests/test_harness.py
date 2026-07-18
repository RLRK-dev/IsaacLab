# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for the fail-closed WMSO D1 harness (conformance, negative controls, manifest validation)."""

from __future__ import annotations

from pathlib import Path

import pytest

from thread_isaac_lab.wmso.d1 import contracts as C
from thread_isaac_lab.wmso.d1 import harness as H
from thread_isaac_lab.wmso.d1 import identity as I

_H = "a" * 64
_REPO_ROOT = Path(__file__).resolve().parents[4]


def _contract(**overrides) -> C.SkillLifecycleContract:
    identity = C.ScriptedIdentity(skill_id="TRANSPORT", callable_qualname="transport_to_clip", source_closure_sha256=_H)
    key = C.SkillActionKey(
        skill_id="TRANSPORT",
        executable_identity=identity,
        handoff_start_context=C.HandoffStartContext(incoming_handoff_state_id=None, initiation_context_hash=_H),
    )
    handoff = C.SkillHandoffState(
        handoff_state_id="h0",
        schema_version="1.0.0",
        producer_action_key=key,
        outcome=C.TerminalOutcome(terminal_class=C.TerminationClass.SUCCESS),
        belief_ref=C.BeliefRef(value=C.HashRef(ref_hash=_H), t_obs=0.0, ttl=1.0, confidence=1.0, ood_flag=False),
        ownership=C.Ownership(contact=False, resource={}, control={"EE_L": False, "EE_R": False}),
        compatibility=C.Compatibility(
            predicate_schema_ref="p", predicate_schema_hash=_H, predicate_version="1.0.0", next_owner="none"
        ),
    )
    base = dict(
        schema_version="1.0.0",
        action_key=key,
        policy_family=C.PolicyFamily.SCRIPTED,
        obs_action_schema=C.ObsActionSchema(obs_fields=[], action_fields=[], field_semantics=C.FieldSemantics.RESOLVED),
        initiation_predicate=C.InitiationPredicate(
            expr_kind=C.ExprKind.THRESHOLD,
            schema_ref="s",
            schema_hash=_H,
            payload_canonical_json="{}",
            required_belief_fields=[],
        ),
        required_belief_confidence=0.5,
        termination_classes=frozenset({C.TerminationClass.SUCCESS}),
        progress_phase=C.ProgressPhase(phase_id="TRANSPORT/move", progress=None),
        safe_interruption_checkpoints=[],
        handoff=handoff,
        accepted_incoming_handoff_set=[],
        duration_cost_distribution=C.DurationCostDistribution(dist_kind=C.DistKind.UNKNOWN),
        resource_requirements=C.ResourceRequirements(control_ownership={}, compute=C.Compute.FAST_PATH),
        recovery_rollback_target=None,
        fail_closed_action=C.FailClosedAction.SAFE_STOP,
        policy_version="1.0.0",
        freshness=C.Freshness(max_staleness_s=1.0),
        support_boundary=C.SupportBoundary(region_ref="all"),
        admissibility=C.Admissibility(identity_pinned=True, contract_conformant=True),
    )
    base.update(overrides)
    return C.SkillLifecycleContract(**base)


def test_good_contract_is_conformant():
    result = H.evaluate_conformance(_contract())
    assert result.conformant is True
    assert result.reasons == []


def test_unresolved_schema_is_not_conformant():
    schema = C.ObsActionSchema(obs_fields=[], action_fields=[], field_semantics=C.FieldSemantics.UNRESOLVED)
    result = H.evaluate_conformance(_contract(obs_action_schema=schema))
    assert result.conformant is False
    assert any("UNRESOLVED" in r for r in result.reasons)


def test_null_freshness_and_empty_boundary_fail_closed():
    r1 = H.evaluate_conformance(_contract(freshness=C.Freshness(max_staleness_s=None)))
    assert r1.conformant is False
    r2 = H.evaluate_conformance(_contract(support_boundary=C.SupportBoundary()))
    assert r2.conformant is False


def test_authority_true_is_rejected():
    adm = C.Admissibility(identity_pinned=True, contract_conformant=True, offline_orchestration_admissible=True)
    result = H.evaluate_conformance(_contract(admissibility=adm))
    assert result.conformant is False
    with pytest.raises(ValueError):
        H.assert_no_authority(_contract(admissibility=adm))
    live = C.Admissibility(identity_pinned=True, contract_conformant=True, closed_loop_admissible=True)
    with pytest.raises(ValueError):
        H.assert_no_authority(_contract(admissibility=live))


def test_parse_root_fields_rejects_missing_and_unknown():
    good = {name: None for name in C.ROOT_REQUIRED_FIELDS}
    assert H.parse_root_fields(good) is good
    missing = {name: None for name in C.ROOT_REQUIRED_FIELDS if name != "freshness"}
    with pytest.raises(ValueError):
        H.parse_root_fields(missing)
    unknown = dict(good, extra_field=1)
    with pytest.raises(ValueError):
        H.parse_root_fields(unknown)


def test_parse_belief_value_both_or_neither_rejects():
    assert isinstance(H.parse_belief_value({"ref_hash": _H}), C.HashRef)
    assert isinstance(H.parse_belief_value({"canonical_belief_snapshot": {}}), C.SnapshotRef)
    with pytest.raises(ValueError):
        H.parse_belief_value({"ref_hash": _H, "canonical_belief_snapshot": {}})
    with pytest.raises(ValueError):
        H.parse_belief_value({})


@pytest.mark.skipif(
    not all((_REPO_ROOT / m).is_file() for m in I.SCRIPTED_CLOSURE_MEMBERS),
    reason="source-closure members not present",
)
def test_validate_source_closure_match_and_mismatch():
    pinned = I.source_closure_sha256(I.SCRIPTED_CLOSURE_MEMBERS, _REPO_ROOT)
    H.validate_source_closure(pinned, I.SCRIPTED_CLOSURE_MEMBERS, str(_REPO_ROOT))
    with pytest.raises(ValueError):
        H.validate_source_closure("f" * 64, I.SCRIPTED_CLOSURE_MEMBERS, str(_REPO_ROOT))
