# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for the fail-closed WMSO D1 harness (conformance, negative controls, manifest validation)."""

from __future__ import annotations

import json
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
        obs_action_schema=C.ObsActionSchema(
            obs_fields=[C.FieldSpec(field_id="x", dtype=C.Dtype.FLOAT32, shape=(1,), unit="m", frame=C.Frame.WORLD)],
            action_fields=[],
            field_semantics=C.FieldSemantics.RESOLVED,
        ),
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


def test_identity_not_pinned_is_not_conformant():
    adm = C.Admissibility(identity_pinned=False, contract_conformant=False)
    result = H.evaluate_conformance(_contract(admissibility=adm))
    assert result.conformant is False
    assert any("identity_pinned" in r for r in result.reasons)


def test_empty_resolved_schema_is_not_conformant():
    schema = C.ObsActionSchema(obs_fields=[], action_fields=[], field_semantics=C.FieldSemantics.RESOLVED)
    result = H.evaluate_conformance(_contract(obs_action_schema=schema))
    assert result.conformant is False
    assert any("no obs/action fields" in r for r in result.reasons)


_MANIFEST = Path(__file__).resolve().parent.parent / "skill_contracts_manifest.json"


def test_manifest_internal_consistency():
    manifest = json.loads(_MANIFEST.read_text())
    problems = H.validate_manifest(manifest, str(_REPO_ROOT), require_closure=False)
    assert problems == [], problems


def test_manifest_source_closure_pins_recompute_on_clean_tree():
    # Required closure (no skip): a clean checkout recomputes the pins; a dirty tree fails closed.
    manifest = json.loads(_MANIFEST.read_text())
    problems = H.validate_manifest(manifest, str(_REPO_ROOT), require_closure=True)
    assert problems == [], problems


def test_invalid_initiation_predicate_is_not_conformant():
    bad_ref = C.InitiationPredicate(
        expr_kind=C.ExprKind.THRESHOLD,
        schema_ref="",
        schema_hash=_H,
        payload_canonical_json="{}",
        required_belief_fields=[],
    )
    r1 = H.evaluate_conformance(_contract(initiation_predicate=bad_ref))
    assert r1.conformant is False
    assert any("schema_ref" in x for x in r1.reasons)
    bad_payload = C.InitiationPredicate(
        expr_kind=C.ExprKind.THRESHOLD,
        schema_ref="s",
        schema_hash=_H,
        payload_canonical_json="{not json",
        required_belief_fields=[],
    )
    r2 = H.evaluate_conformance(_contract(initiation_predicate=bad_payload))
    assert r2.conformant is False
    assert any("JSON" in x for x in r2.reasons)


def test_declared_conformant_must_equal_computed():
    # An otherwise-valid contract declaring contract_conformant=false must not evaluate conformant.
    adm = C.Admissibility(identity_pinned=True, contract_conformant=False)
    result = H.evaluate_conformance(_contract(admissibility=adm))
    assert result.conformant is False
    assert any("declared contract_conformant" in x for x in result.reasons)


def test_manifest_validator_catches_mutations():
    corrupt = json.loads(_MANIFEST.read_text())
    corrupt["skills"][0]["identity"]["policy_weight_hash"] = "not-a-hash"
    assert H.validate_manifest(corrupt, str(_REPO_ROOT), require_closure=False)

    bad_closure = json.loads(_MANIFEST.read_text())
    for row in bad_closure["skills"]:
        if row.get("kind") == "SCRIPTED":
            row["identity"]["source_closure_sha256"] = "a" * 64
            break
    assert H.validate_manifest(bad_closure, str(_REPO_ROOT), require_closure=False)

    dup = json.loads(_MANIFEST.read_text())
    dup["skills"][1]["skill_id"] = dup["skills"][0]["skill_id"]
    assert H.validate_manifest(dup, str(_REPO_ROOT), require_closure=False)


def test_noncanonical_initiation_payload_is_not_conformant():
    noncanon = C.InitiationPredicate(
        expr_kind=C.ExprKind.THRESHOLD,
        schema_ref="s",
        schema_hash=_H,
        payload_canonical_json='{ "b": 1, "a": 2 }',
        required_belief_fields=[],
    )
    result = H.evaluate_conformance(_contract(initiation_predicate=noncanon))
    assert result.conformant is False
    assert any("canonical" in x for x in result.reasons)


def test_manifest_validator_catches_policy_weight_final_mismatch():
    m = json.loads(_MANIFEST.read_text())
    m["skills"][0]["identity"]["final_policy_hash"] = "b" * 64
    problems = H.validate_manifest(m, str(_REPO_ROOT), require_closure=False)
    assert any("policy_weight_hash != final_policy_hash" in p for p in problems)


def test_manifest_validator_catches_renamed_skill():
    m = json.loads(_MANIFEST.read_text())
    for row in m["skills"]:
        if row["skill_id"] == "CLAMP":
            row["skill_id"] = "ARBITRARY_NEW_SKILL"
            break
    problems = H.validate_manifest(m, str(_REPO_ROOT), require_closure=False)
    assert any("expected 9" in p for p in problems)


_APPROACH_FINAL = _REPO_ROOT / "thread_isaac_lab/data/rl_approach_cable_A_w256_20260409_073409/model_best.pt"


@pytest.mark.skipif(not _APPROACH_FINAL.is_file(), reason="learned artifacts not present (clean worktree)")
def test_manifest_artifacts_match_actual_digests():
    manifest = json.loads(_MANIFEST.read_text())
    assert H.verify_manifest_artifacts(manifest, str(_REPO_ROOT)) == []
    mutated = json.loads(_MANIFEST.read_text())
    mutated["skills"][0]["identity"]["final_policy_hash"] = "b" * 64
    mutated["skills"][0]["identity"]["policy_weight_hash"] = "b" * 64
    assert H.verify_manifest_artifacts(mutated, str(_REPO_ROOT))
