# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for WMSO D1 typed contract records (structural fail-closed validation + I1/I2)."""

from __future__ import annotations

import pytest

from thread_isaac_lab.wmso.d1 import contracts as C

_H = "a" * 64  # a valid 64-hex placeholder
_BAD = "a" * 63  # too short


def test_root_required_fields_count():
    assert len(C.ROOT_REQUIRED_FIELDS) == 19
    assert "required_belief_confidence" in C.ROOT_REQUIRED_FIELDS


def test_is_hex64():
    assert C.is_hex64(_H)
    assert not C.is_hex64(_BAD)
    assert not C.is_hex64("A" * 64)  # uppercase rejected


def test_lineage_rejects_bad_hashes():
    C.Lineage(family=C.PolicyFamily.BC_RL, final_policy_hash=_H, base_ckpt_hash=_H, finetune_cfg_hash=_H)
    with pytest.raises(ValueError):
        C.Lineage(family=C.PolicyFamily.BC_RL, final_policy_hash=_BAD)
    with pytest.raises(ValueError):
        C.Lineage(family=C.PolicyFamily.BC_RL, final_policy_hash=_H, base_ckpt_hash=_BAD)


def test_learned_identity_crypto_and_rl_only_invariants():
    # A non-crypto association must not claim a train-time crypto bind.
    with pytest.raises(ValueError):
        C.LearnedIdentity(
            policy_weight_hash=_H,
            lineage=C.Lineage(family=C.PolicyFamily.BC_RL, final_policy_hash=_H),
            train_time_crypto_bound=True,
            association_strength=C.AssociationStrength.RECORDED_PATH_CONFIG_COLOCATION,
        )
    # RL-only must have null base/finetune.
    with pytest.raises(ValueError):
        C.LearnedIdentity(
            policy_weight_hash=_H,
            lineage=C.Lineage(family=C.PolicyFamily.PPO, final_policy_hash=_H, base_ckpt_hash=_H),
            train_time_crypto_bound=False,
            association_strength=C.AssociationStrength.NOT_APPLICABLE_RL_ONLY,
        )
    ok = C.LearnedIdentity(
        policy_weight_hash=_H,
        lineage=C.Lineage(family=C.PolicyFamily.PPO, final_policy_hash=_H),
        train_time_crypto_bound=False,
        association_strength=C.AssociationStrength.NOT_APPLICABLE_RL_ONLY,
    )
    assert ok.kind is C.IdentityKind.LEARNED


def test_policy_weight_must_equal_final_policy_hash():
    with pytest.raises(ValueError):
        C.LearnedIdentity(
            policy_weight_hash="b" * 64,
            lineage=C.Lineage(family=C.PolicyFamily.PPO, final_policy_hash=_H),
            train_time_crypto_bound=False,
            association_strength=C.AssociationStrength.NOT_APPLICABLE_RL_ONLY,
        )


def test_recorded_bc_rl_requires_non_null_base_and_finetune():
    with pytest.raises(ValueError):
        C.LearnedIdentity(
            policy_weight_hash=_H,
            lineage=C.Lineage(family=C.PolicyFamily.BC_RL, final_policy_hash=_H),
            train_time_crypto_bound=False,
            association_strength=C.AssociationStrength.RECORDED_PATH_CONFIG_COLOCATION,
        )
    ok = C.LearnedIdentity(
        policy_weight_hash=_H,
        lineage=C.Lineage(
            family=C.PolicyFamily.BC_RL, final_policy_hash=_H, base_ckpt_hash="b" * 64, finetune_cfg_hash="c" * 64
        ),
        train_time_crypto_bound=False,
        association_strength=C.AssociationStrength.RECORDED_PATH_CONFIG_COLOCATION,
    )
    assert ok.lineage.base_ckpt_hash == "b" * 64


def test_obs_action_schema_rejects_duplicate_field_id():
    dup = C.FieldSpec(field_id="dup", dtype=C.Dtype.FLOAT32, shape=(1,), unit="m", frame=C.Frame.WORLD)
    with pytest.raises(ValueError):
        C.ObsActionSchema(obs_fields=[dup, dup], action_fields=[], field_semantics=C.FieldSemantics.RESOLVED)


def test_scripted_and_wait_identity_hash_validation():
    C.ScriptedIdentity(skill_id="TRANSPORT", callable_qualname="transport_to_clip", source_closure_sha256=_H)
    with pytest.raises(ValueError):
        C.WaitIdentity(skill_id="CLIP_CONFIRM", callable_qualname="_run_wait", source_closure_sha256=_BAD)


def test_belief_ref_tagged_union_both_or_neither_rejects():
    # I2: exactly one of SNAPSHOT / HASH_REF.
    C.BeliefRef(value=C.HashRef(ref_hash=_H), t_obs=0.0, ttl=1.0, confidence=1.0, ood_flag=False)
    C.BeliefRef(value=C.SnapshotRef(canonical_belief_snapshot={}), t_obs=0.0, ttl=1.0, confidence=1.0, ood_flag=False)
    with pytest.raises(ValueError):
        C.HashRef(ref_hash=_BAD)
    with pytest.raises(ValueError):
        C.BeliefRef(value="not-a-ref", t_obs=0.0, ttl=1.0, confidence=1.0, ood_flag=False)  # type: ignore[arg-type]


def test_interrupt_outcome_requires_checkpoint():
    C.TerminalOutcome(terminal_class=C.TerminationClass.SUCCESS)  # checkpoint nullable
    C.InterruptOutcome(checkpoint_id="cp0", interrupt_reason=C.InterruptReason.PLANNED_SWITCH)
    with pytest.raises(ValueError):
        C.InterruptOutcome(checkpoint_id="", interrupt_reason=C.InterruptReason.EVENT)


def test_contract_root_validation():
    contract = _minimal_contract()
    assert contract.admissibility.offline_orchestration_admissible is False
    assert contract.admissibility.closed_loop_admissible is False
    with pytest.raises(ValueError):
        _minimal_contract(termination_classes=frozenset())
    with pytest.raises(ValueError):
        _minimal_contract(required_belief_confidence=1.5)


def _minimal_contract(
    *, termination_classes=frozenset({C.TerminationClass.SUCCESS}), required_belief_confidence=0.5
) -> C.SkillLifecycleContract:
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
    return C.SkillLifecycleContract(
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
        required_belief_confidence=required_belief_confidence,
        termination_classes=termination_classes,
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
