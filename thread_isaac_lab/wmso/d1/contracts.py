# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Typed WMSO D1 skill-lifecycle contract records (design-frozen).

Instantiates the D0 §B/§E schema at skill resolution per the banked design v4.1.1. These are
pure typed records with fail-closed structural validation; they do not run policies, ground
belief at runtime, or grant orchestration authority. Construction raises on a structural
violation (fail-closed); contract-level conformance (schema resolution, freshness, support
boundary, authority) is evaluated by :mod:`.harness`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def is_hex64(value: str) -> bool:
    """Return whether ``value`` is a lowercase 64-character hex sha256 digest."""
    return isinstance(value, str) and bool(_HEX64.match(value))


# --------------------------------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------------------------------
class PolicyFamily(Enum):
    """Training provenance family of a skill's policy."""

    BC = "BC"
    BC_RL = "BC+RL"
    PPO = "PPO"
    DAPG = "DAPG"
    SCRIPTED = "SCRIPTED"
    WAIT = "WAIT"


class IdentityKind(Enum):
    """Discriminant of :data:`ExecutableIdentity`."""

    LEARNED = "LEARNED"
    SCRIPTED = "SCRIPTED"
    WAIT = "WAIT"


class AssociationStrength(Enum):
    """Strength of a learned skill's base->finetune->final lineage association."""

    CRYPTO_TRAIN_TIME_BOUND = "CRYPTO_TRAIN_TIME_BOUND"
    RECORDED_PATH_CONFIG_COLOCATION = "RECORDED_PATH_CONFIG_COLOCATION"
    NOT_APPLICABLE_RL_ONLY = "NOT_APPLICABLE_RL_ONLY"


class FieldSemantics(Enum):
    """Whether an obs/action schema's field semantics are resolved from an authoritative source."""

    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"


class Frame(Enum):
    """Coordinate frame of a field's value."""

    WORLD = "world"
    ROBOT_BASE = "robot_base"
    EE_L = "EE_L"
    EE_R = "EE_R"
    CLIP = "clip"
    N_A = "N/A"


class Dtype(Enum):
    """Field data type."""

    FLOAT32 = "float32"
    INT32 = "int32"
    BOOL = "bool"


class TerminationClass(Enum):
    """Skill termination class."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    INVALID_STATE = "invalid_state"


class InterruptReason(Enum):
    """Reason a running skill is interrupted at a safe checkpoint (non-terminal)."""

    PLANNED_SWITCH = "planned_switch"
    EVENT = "event"
    SAFETY_STABILIZED = "safety_stabilized"


class FailClosedAction(Enum):
    """Action taken when no safe continuation exists."""

    RE_OBSERVE = "re_observe"
    SAFE_STOP = "safe_stop"
    HANDBACK_TO_OWNER = "handback_to_owner"


class Compute(Enum):
    """Orchestrator compute path a skill decision requires."""

    FAST_PATH = "fast_path"
    SLOW_PATH = "slow_path"


class DistKind(Enum):
    """Kind of a duration/cost distribution."""

    EMPIRICAL = "empirical"
    GAUSSIAN = "gaussian"
    UNKNOWN = "unknown"


class CostUnits(Enum):
    """Units of a cost distribution."""

    TIME_S = "time_s"
    ENERGY_J = "energy_j"
    NORMALIZED_UNITLESS = "normalized_unitless"


class ExprKind(Enum):
    """Kind of an initiation predicate expression."""

    THRESHOLD = "threshold"
    REGION = "region"
    BOOLEAN_AND = "boolean_and"
    CALLABLE_REF = "callable_ref"


# --------------------------------------------------------------------------------------------------
# Schema (I1: one FieldSpec, both obs and action are list[FieldSpec])
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class FieldSpec:
    """One typed obs/action field.

    Args:
        field_id: Stable canonical field id (never a positional index).
        dtype: Field data type.
        shape: Tensor shape [dims].
        unit: SI unit string, e.g. ``"m"``, ``"rad"``, ``"dimensionless"``.
        frame: Coordinate frame of the value.
    """

    field_id: str
    dtype: Dtype
    shape: tuple[int, ...]
    unit: str
    frame: Frame


@dataclass
class ObsActionSchema:
    """A skill's declared observation/action schema.

    ``field_semantics=UNRESOLVED`` means the field order/unit/frame/action-scaling are not bound
    from an authoritative training-env source; generic shape acceptance is fail-closed.
    """

    obs_fields: list[FieldSpec]
    action_fields: list[FieldSpec]
    field_semantics: FieldSemantics


# --------------------------------------------------------------------------------------------------
# Executable identity (tagged union; construction is fail-closed on malformed hashes)
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Lineage:
    """Learned-policy lineage. ``base_ckpt_hash``/``finetune_cfg_hash`` are ``None`` for RL-only."""

    family: PolicyFamily
    final_policy_hash: str
    base_ckpt_hash: str | None = None
    finetune_cfg_hash: str | None = None

    def __post_init__(self) -> None:
        if not is_hex64(self.final_policy_hash):
            raise ValueError("final_policy_hash must be a 64-hex sha256")
        for name in ("base_ckpt_hash", "finetune_cfg_hash"):
            value = getattr(self, name)
            if value is not None and not is_hex64(value):
                raise ValueError(f"{name} must be None or a 64-hex sha256")


@dataclass(frozen=True)
class LearnedIdentity:
    """Identity of a learned (BC / BC+RL / PPO / DAPG) skill action."""

    policy_weight_hash: str
    lineage: Lineage
    train_time_crypto_bound: bool
    association_strength: AssociationStrength
    kind: IdentityKind = IdentityKind.LEARNED

    def __post_init__(self) -> None:
        if not is_hex64(self.policy_weight_hash):
            raise ValueError("policy_weight_hash must be a 64-hex sha256")
        # A recorded (non-crypto) or RL-only association must never claim a train-time crypto bind.
        if self.train_time_crypto_bound and (
            self.association_strength is not AssociationStrength.CRYPTO_TRAIN_TIME_BOUND
        ):
            raise ValueError("train_time_crypto_bound=True requires association_strength=CRYPTO_TRAIN_TIME_BOUND")
        if self.association_strength is AssociationStrength.NOT_APPLICABLE_RL_ONLY and (
            self.lineage.base_ckpt_hash is not None or self.lineage.finetune_cfg_hash is not None
        ):
            raise ValueError("RL-only identity must have null base_ckpt_hash and finetune_cfg_hash")


@dataclass(frozen=True)
class ScriptedIdentity:
    """Identity of a scripted skill (no policy weights)."""

    skill_id: str
    callable_qualname: str
    source_closure_sha256: str
    kind: IdentityKind = IdentityKind.SCRIPTED

    def __post_init__(self) -> None:
        if not is_hex64(self.source_closure_sha256):
            raise ValueError("source_closure_sha256 must be a 64-hex sha256")


@dataclass(frozen=True)
class WaitIdentity:
    """Identity of a wait skill."""

    skill_id: str
    callable_qualname: str
    source_closure_sha256: str
    kind: IdentityKind = IdentityKind.WAIT

    def __post_init__(self) -> None:
        if not is_hex64(self.source_closure_sha256):
            raise ValueError("source_closure_sha256 must be a 64-hex sha256")


ExecutableIdentity = LearnedIdentity | ScriptedIdentity | WaitIdentity


@dataclass(frozen=True)
class HandoffStartContext:
    """The handoff-state + initiation context an action was entered from."""

    incoming_handoff_state_id: str | None
    initiation_context_hash: str

    def __post_init__(self) -> None:
        if not is_hex64(self.initiation_context_hash):
            raise ValueError("initiation_context_hash must be a 64-hex sha256")


@dataclass(frozen=True)
class SkillActionKey:
    """The identity a skill action is modeled/evaluated under (never keyed by name alone)."""

    skill_id: str
    executable_identity: ExecutableIdentity
    handoff_start_context: HandoffStartContext


# --------------------------------------------------------------------------------------------------
# Predicate / phase
# --------------------------------------------------------------------------------------------------
@dataclass
class InitiationPredicate:
    """Typed initiation predicate; extensible payload pinned by ``schema_ref`` + ``schema_hash``."""

    expr_kind: ExprKind
    schema_ref: str
    schema_hash: str
    payload_canonical_json: str
    required_belief_fields: list[str]

    def __post_init__(self) -> None:
        if not is_hex64(self.schema_hash):
            raise ValueError("initiation_predicate.schema_hash must be a 64-hex sha256")


@dataclass
class ProgressPhase:
    """Namespaced skill-local progress phase (not a global route enum)."""

    phase_id: str
    progress: float | None = None


# --------------------------------------------------------------------------------------------------
# Handoff state (I2: belief_ref is a SNAPSHOT | HASH_REF tagged union; outcome is TERMINAL | INTERRUPT)
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class SnapshotRef:
    """Belief reference carrying an inline canonical BeliefState snapshot."""

    canonical_belief_snapshot: dict


@dataclass(frozen=True)
class HashRef:
    """Belief reference carrying a content-hash of a canonical BeliefState."""

    ref_hash: str

    def __post_init__(self) -> None:
        if not is_hex64(self.ref_hash):
            raise ValueError("belief_ref HASH_REF.ref_hash must be a 64-hex sha256")


BeliefValue = SnapshotRef | HashRef


@dataclass
class BeliefRef:
    """Grounded belief at a handoff. ``value`` is exactly one of SNAPSHOT / HASH_REF (I2)."""

    value: BeliefValue
    t_obs: float
    ttl: float
    confidence: float
    ood_flag: bool

    def __post_init__(self) -> None:
        if not isinstance(self.value, (SnapshotRef, HashRef)):
            raise ValueError("belief_ref.value must be exactly one of SnapshotRef | HashRef")


@dataclass(frozen=True)
class TerminalOutcome:
    """A terminal end of the producing action; ``checkpoint_id`` is nullable."""

    terminal_class: TerminationClass
    checkpoint_id: str | None = None


@dataclass(frozen=True)
class InterruptOutcome:
    """A resumable safe-checkpoint interrupt (non-terminal); ``checkpoint_id`` is mandatory."""

    checkpoint_id: str
    interrupt_reason: InterruptReason

    def __post_init__(self) -> None:
        if not self.checkpoint_id:
            raise ValueError("INTERRUPT outcome requires a non-empty checkpoint_id")


ProducerOutcome = TerminalOutcome | InterruptOutcome


@dataclass(frozen=True)
class Ownership:
    """Physical/compute resources held at a handoff (control is per-EE + gripper)."""

    contact: bool
    resource: dict
    control: dict


@dataclass(frozen=True)
class Compatibility:
    """Who may accept a handoff and under what pinned predicate."""

    predicate_schema_ref: str
    predicate_schema_hash: str
    predicate_version: str
    next_owner: str

    def __post_init__(self) -> None:
        if not is_hex64(self.predicate_schema_hash):
            raise ValueError("compatibility.predicate_schema_hash must be a 64-hex sha256")


@dataclass
class SkillHandoffState:
    """The typed state a skill leaves behind for the next skill to accept (charter §3 / D0 §E)."""

    handoff_state_id: str
    schema_version: str
    producer_action_key: SkillActionKey
    outcome: ProducerOutcome
    belief_ref: BeliefRef
    ownership: Ownership
    compatibility: Compatibility


# --------------------------------------------------------------------------------------------------
# Cost / resource / support / freshness / admissibility
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class DurationEstimate:
    """Duration distribution summary [s]."""

    mean_s: float
    std_s: float
    p50_s: float
    p95_s: float


@dataclass(frozen=True)
class CostEstimate:
    """Cost distribution summary with an explicit unit."""

    mean: float
    std: float
    p50: float
    p95: float
    cost_units: CostUnits


@dataclass
class DurationCostDistribution:
    """Skill duration/cost distribution; ``None`` legs mean unmodeled (LL-WMF gap)."""

    dist_kind: DistKind
    duration: DurationEstimate | None = None
    cost: CostEstimate | None = None


@dataclass(frozen=True)
class ResourceRequirements:
    """Resources a skill requires (per-EE + gripper control + compute path)."""

    control_ownership: dict
    compute: Compute


@dataclass(frozen=True)
class Freshness:
    """Max policy staleness before void; ``None`` = unbounded (fail-closed at conformance)."""

    max_staleness_s: float | None


@dataclass(frozen=True)
class SupportBoundary:
    """Region a policy/model is calibrated on. Needs at least a region ref or an in-support predicate."""

    region_ref: str | None = None
    in_support_predicate: dict | None = None


@dataclass
class Admissibility:
    """Four-axis admissibility. D1 may set only the first two true; both authority axes are hard-false."""

    identity_pinned: bool
    contract_conformant: bool
    offline_orchestration_admissible: bool = False
    closed_loop_admissible: bool = False


@dataclass
class SkillLifecycleContract:
    """The single uniform contract every learned/scripted/wait skill publishes (D0 §B, §3b root shape).

    Constructed records are structurally valid; contract-level conformance (schema resolution,
    freshness, support boundary, no-authority) is evaluated by :func:`.harness.evaluate_conformance`.
    """

    schema_version: str
    action_key: SkillActionKey
    policy_family: PolicyFamily
    obs_action_schema: ObsActionSchema
    initiation_predicate: InitiationPredicate
    required_belief_confidence: float
    termination_classes: frozenset[TerminationClass]
    progress_phase: ProgressPhase
    safe_interruption_checkpoints: list[str]
    handoff: SkillHandoffState
    accepted_incoming_handoff_set: list[str]
    duration_cost_distribution: DurationCostDistribution
    resource_requirements: ResourceRequirements
    recovery_rollback_target: str | None
    fail_closed_action: FailClosedAction
    policy_version: str
    freshness: Freshness
    support_boundary: SupportBoundary
    admissibility: Admissibility

    def __post_init__(self) -> None:
        if not self.termination_classes:
            raise ValueError("termination_classes must be non-empty")
        if not 0.0 <= self.required_belief_confidence <= 1.0:
            raise ValueError("required_belief_confidence must be in [0, 1]")


#: The exact set of root fields every SkillLifecycleContract must carry (C2). Used by the harness to
#: reject an unknown or missing field fail-closed.
ROOT_REQUIRED_FIELDS: frozenset[str] = frozenset(
    {
        "schema_version",
        "action_key",
        "policy_family",
        "obs_action_schema",
        "initiation_predicate",
        "required_belief_confidence",
        "termination_classes",
        "progress_phase",
        "safe_interruption_checkpoints",
        "handoff",
        "accepted_incoming_handoff_set",
        "duration_cost_distribution",
        "resource_requirements",
        "recovery_rollback_target",
        "fail_closed_action",
        "policy_version",
        "freshness",
        "support_boundary",
        "admissibility",
    }
)
