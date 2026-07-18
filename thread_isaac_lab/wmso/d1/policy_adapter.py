# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Static WMSO D1 policy adapter — schema-bound payload canonicalization.

The adapter maps ``(ExecutableIdentity + declared obs/action schema)`` to a canonical contract
representation. It is a *static* transform: it does not ground belief, run a policy, or touch
runtime observations. It has no inverse (canonical -> raw is undefined / not required), so no
round-trip is claimed; the adapter is exercised by canonicalization-correctness, schema-conformance,
and determinism tests. Generic shape acceptance fails closed: an ``UNRESOLVED`` field-semantics
schema yields ``schema_resolved=False`` and never a resolved canonicalization (pN B3).
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    ExecutableIdentity,
    FieldSemantics,
    FieldSpec,
    IdentityKind,
    LearnedIdentity,
    ObsActionSchema,
)

# A canonical per-field tuple: (field_id, dtype, shape, unit, frame). Sorted by field_id for determinism.
CanonicalField = tuple[str, str, tuple[int, ...], str, str]


@dataclass(frozen=True)
class CanonicalContractRepr:
    """Deterministic canonical form of a skill's identity + declared schema.

    ``schema_resolved`` is ``True`` only when the source schema's ``field_semantics`` is ``RESOLVED``;
    otherwise the representation carries shape-only fields and must drive ``contract_conformant=false``.
    """

    skill_id: str
    identity_kind: str
    identity_hash: str
    obs_canonical: tuple[CanonicalField, ...]
    action_canonical: tuple[CanonicalField, ...]
    field_semantics: str
    schema_resolved: bool


def _identity_hash(identity: ExecutableIdentity) -> str:
    """Return the primary content hash of an executable identity."""
    if isinstance(identity, LearnedIdentity):
        return identity.policy_weight_hash
    return identity.source_closure_sha256


def _resolve_skill_id(identity: ExecutableIdentity, skill_id: str) -> str:
    """Return the skill id, rejecting a scripted/wait identity whose id disagrees with the caller."""
    if isinstance(identity, LearnedIdentity):
        return skill_id
    if identity.skill_id != skill_id:
        raise ValueError(f"skill_id mismatch: caller {skill_id!r} != identity {identity.skill_id!r}")
    return identity.skill_id


def _canonical_fields(fields: list[FieldSpec]) -> tuple[CanonicalField, ...]:
    """Return the canonical, field_id-sorted tuple form of a list of :class:`.FieldSpec` (deterministic)."""
    return tuple(sorted((f.field_id, f.dtype.value, tuple(f.shape), f.unit, f.frame.value) for f in fields))


def canonicalize(identity: ExecutableIdentity, skill_id: str, schema: ObsActionSchema) -> CanonicalContractRepr:
    """Statically canonicalize a skill's identity + declared schema.

    Args:
        identity: The skill's executable identity.
        skill_id: The canonical skill id.
        schema: The skill's declared obs/action schema.

    Returns:
        A deterministic :class:`CanonicalContractRepr`. ``schema_resolved`` is ``False`` when the
        schema field-semantics are ``UNRESOLVED`` (fail-closed; no generic shape acceptance).
    """
    resolved = schema.field_semantics is FieldSemantics.RESOLVED
    kind = identity.kind.value if isinstance(identity.kind, IdentityKind) else str(identity.kind)
    return CanonicalContractRepr(
        skill_id=_resolve_skill_id(identity, skill_id),
        identity_kind=kind,
        identity_hash=_identity_hash(identity),
        obs_canonical=_canonical_fields(schema.obs_fields),
        action_canonical=_canonical_fields(schema.action_fields),
        field_semantics=schema.field_semantics.value,
        schema_resolved=resolved,
    )


def is_deterministic(identity: ExecutableIdentity, skill_id: str, schema: ObsActionSchema) -> bool:
    """Return whether canonicalizing the same input twice yields identical output (determinism check)."""
    return canonicalize(identity, skill_id, schema) == canonicalize(identity, skill_id, schema)
