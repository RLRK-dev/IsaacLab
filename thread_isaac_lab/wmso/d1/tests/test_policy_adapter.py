# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for the WMSO D1 static policy adapter (determinism, ordering, fail-closed schema)."""

from __future__ import annotations

from thread_isaac_lab.wmso.d1 import policy_adapter as A
from thread_isaac_lab.wmso.d1.contracts import (
    AssociationStrength,
    Dtype,
    FieldSemantics,
    FieldSpec,
    Frame,
    LearnedIdentity,
    Lineage,
    PolicyFamily,
    ScriptedIdentity,
)

_H = "a" * 64


def _schema(field_semantics=FieldSemantics.RESOLVED, reverse=False):
    fields = [
        FieldSpec(field_id="ee_r_pos", dtype=Dtype.FLOAT32, shape=(3,), unit="m", frame=Frame.WORLD),
        FieldSpec(field_id="cable_z", dtype=Dtype.FLOAT32, shape=(1,), unit="m", frame=Frame.WORLD),
    ]
    if reverse:
        fields = list(reversed(fields))
    action = [FieldSpec(field_id="dq", dtype=Dtype.FLOAT32, shape=(12,), unit="rad", frame=Frame.N_A)]
    return A.ObsActionSchema(obs_fields=fields, action_fields=action, field_semantics=field_semantics)


def _scripted():
    return ScriptedIdentity(skill_id="TRANSPORT", callable_qualname="transport_to_clip", source_closure_sha256=_H)


def _learned():
    return LearnedIdentity(
        policy_weight_hash=_H,
        lineage=Lineage(family=PolicyFamily.PPO, final_policy_hash=_H),
        train_time_crypto_bound=False,
        association_strength=AssociationStrength.NOT_APPLICABLE_RL_ONLY,
    )


def test_canonicalize_is_deterministic():
    assert A.is_deterministic(_scripted(), "TRANSPORT", _schema())


def test_canonicalize_is_field_order_independent():
    a = A.canonicalize(_scripted(), "TRANSPORT", _schema(reverse=False))
    b = A.canonicalize(_scripted(), "TRANSPORT", _schema(reverse=True))
    assert a.obs_canonical == b.obs_canonical


def test_unresolved_schema_fails_closed():
    resolved = A.canonicalize(_scripted(), "TRANSPORT", _schema(FieldSemantics.RESOLVED))
    unresolved = A.canonicalize(_scripted(), "TRANSPORT", _schema(FieldSemantics.UNRESOLVED))
    assert resolved.schema_resolved is True
    assert unresolved.schema_resolved is False
    assert unresolved.field_semantics == "UNRESOLVED"


def test_identity_hash_source_by_kind():
    scripted = A.canonicalize(_scripted(), "TRANSPORT", _schema())
    learned = A.canonicalize(_learned(), "INSERT_INTO_CLIP", _schema())
    assert scripted.identity_kind == "SCRIPTED"
    assert learned.identity_kind == "LEARNED"
    assert scripted.identity_hash == _H
    assert learned.identity_hash == _H
