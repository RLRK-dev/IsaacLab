# WMSO D1.1-A Design Review v6 — 2026-07-19

## 1. Review target

Reviewed together:

- `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md` — v2.7.1
- `WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md` — v1.5
- `WMSO_EvidencePolicy_v1.5.json`
- `WMSO_D11A_DESIGN_VERIFY_WMSODESIGN_20260719.md`
- `WMSO_PN_DESIGN_VERIFY_HOLD_B1B7_TRANSCRIPT_20260719.md`
- `WMSO_RS_REVIEW4_DESIGN_TRANSCRIPT_20260719.md`
- `WMSO_DELIVERABLES_MANIFEST_20260719.md`

## 2. Verdict

```text
File byte/SHA consistency:            PASS
EvidencePolicy JSON syntax:           PASS
EvidencePolicy structural coverage:   PASS
Review-4 semantic fidelity:           CONFIRMED
WMSO D1.1-A scope:                    CLOSED — maintain
WMSO D1.1-A design:                   HOLD
D1.1-A freeze:                        HOLD
Implementation/training/authority:    CLOSED — maintain
```

No scope reopen is required. The remaining issues are bounded design, policy, handoff, and custody corrections. After those corrections, D1.1-A should be frozen rather than expanded again.

## 3. Verified integrity

Recomputed SHA-256 values:

```text
8a7915dfa3386889d4efe3cbacb063c0ea20df0f138c8099b84ec64cbab5ad50  WMSO_RS_REVIEW4_DESIGN_TRANSCRIPT_20260719.md
3b568dcf851feacac7909703399717729d6e970cd0aecd8c0c4956aa0e1cfa56  WMSO_EvidencePolicy_v1.5.json
6dc3f93b78c9e673353b55d55e624a49ffea35ce0b6e46e4c300e07f19274e88  WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md
43ef06ef7f137659a6c6beb3f4aa6dbefed1085011bd9bbac7b940321ac31ded  WMSO_D11A_DESIGN_VERIFY_WMSODESIGN_20260719.md
6d26efde4739cf0811ffcad0a4eb77cb7e79660817398b878d44d8789b3ae50d  WMSO_PN_DESIGN_VERIFY_HOLD_B1B7_TRANSCRIPT_20260719.md
64e2b005d6dd7f7a64dc884356e860da43762638c328a215ba5b464fd8164ac3  WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md
```

The EvidencePolicy JSON was parsed with duplicate-key and non-finite-value rejection. Results:

- strict JSON: PASS
- 13 unique components: PASS
- EXACT and HASH_BOUND coverage of all 13 components: PASS
- DIMENSION_ONLY applicability partition: PASS
- all three usage-profile component partitions: PASS
- all 15 ProofKinds have binding entries: PASS

## 4. Review-4 transcript

The transcript is semantically faithful to the prior review message. Correct custody wording:

```text
semantic fidelity: CONFIRMED
byte identity: NOT APPLICABLE — the source was a chat message, not a file
```

Do not silently rewrite the historical transcript and retain its old SHA. Either:

1. create a separate fidelity-confirmation artifact targeting SHA `8a7915...`; or
2. append the confirmation, regenerate the transcript SHA, and update all dependent records.

## 5. P0 design blockers

### P0-1 — EvidencePolicy semantic-hash projection is contradictory

The JSON says its semantic hash covers the full top-level object except `note_semantic_hash` and `source_markdown`. The Markdown defines `policy_object` as only:

```text
grades
component_groups
proof_policy
proof_binding
profiles
applicability_rules
policy_semver
```

The JSON interpretation additionally includes:

```text
artifact
proof_item_canonical_order
proof_conflict_rules
trust_boundary
exemption_reporting
usage_ceiling_note
```

These produce different `evidence_policy_definition_hash` values.

Required correction:

```json
{
  "metadata": {"artifact": "...", "source_markdown": "..."},
  "policy_definition": {
    "policy_semver": "...",
    "grades": [],
    "component_groups": {},
    "proof_policy": {},
    "proof_item_canonical_order": {},
    "proof_conflict_rules": {},
    "proof_binding": {},
    "trust_boundary": {},
    "applicability_rules": [],
    "profiles": {},
    "exemption_reporting": {},
    "usage_ceiling": {}
  }
}
```

Pin exactly:

```text
evidence_policy_definition_hash = H_WCJ(policy_definition)
```

Metadata is excluded; every validator-affecting rule is included.

### P0-2 — HASH_BOUND schema/spec claims have no valid reproduced-output target

For schema/spec components, HASH_BOUND requires `REPRODUCED_OUTPUT_HASH` plus a schema/config hash, but the binding rule says:

```text
REPRODUCED_OUTPUT_HASH == corresponding FINAL_ARTIFACT_HASH
```

Those cells do not contain `FINAL_ARTIFACT_HASH`. The target is undefined.

Required correction: define one component-specific `claim_target_hash`.

```text
POLICY_ARTIFACT      -> executable_artifact_hash
MODEL_ARCHITECTURE   -> model_architecture slot hash
OBSERVATION_SCHEMA   -> H_WCJ(semantic_obs_schema)
ACTION_SCHEMA        -> H_WCJ(semantic_action_schema)
TENSOR_BINDING       -> tensor_binding slot hash
NORMALIZATION        -> normalization slot hash
CONTROL_MODE         -> H_WCJ(control-mode projection)
RUNTIME_CONFIG       -> runtime_config slot hash
TRAINING_PROVENANCE  -> H_WCJ(provenance projection) or a precisely chosen artifact target
TRAINING_DATASET     -> demo_dataset_hash
INITIATION_SPEC      -> H_WCJ(initiation_spec)
TERMINATION_SPEC     -> H_WCJ(termination_spec)
HANDOFF_SCHEMA       -> H_WCJ(handoff schema projection)
```

Then:

```text
EvidenceRecord.claim_target_hash == derived component target
REPRODUCED_OUTPUT_HASH == claim_target_hash
TRAIN_TIME_CRYPTO_BINDING binds claim_target_hash + manifest hash
```

The current unbound `EvidenceRecord.artifact_hash` should be renamed and bound as this target, or removed.

### P0-3 — SCRIPTED/WAIT cannot satisfy current proof binding

SCRIPTED and WAIT correctly mark `TRAINING_PROVENANCE` as not applicable. However their remaining required components at HASH_BOUND still require `SOURCE_COMMIT` and `CONFIG_HASH`.

Current bindings point only to learned-policy fields:

```text
SOURCE_COMMIT -> TrainingProvenance.final_source_commit
CONFIG_HASH   -> TrainingProvenance training-stage config
```

For SCRIPTED/WAIT those fields are null, so legitimate non-learned skills cannot satisfy the closed-loop evidence floor.

Required correction: make proof binding provenance-class-aware. For example:

```text
LEARNED:
  SOURCE_COMMIT -> final_source_commit
  CONFIG_HASH   -> final/bc training config

SCRIPTED/WAIT:
  SOURCE_COMMIT -> source-closure provenance commit
  CONFIG_HASH   -> runtime-config/source-build config target
```

This requires either a small `ExecutionProvenance` record or an equivalent typed source-closure provenance structure. Do not use `UNKNOWN` as a substitute for not-applicable or non-training provenance.

### P0-4 — Evidence evaluator trust is ambient and unbound

The policy requires `evaluator_artifact_hash` to belong to an allowlisted evaluator registry, but:

- the certification API does not receive an evaluator registry;
- the certificate does not bind an evaluator-registry hash;
- the policy JSON does not include an evaluator allowlist;
- the resolver verifies bytes but does not prove that a trusted evaluator issued the grade.

Required correction: choose one explicit trust boundary.

Preferred:

```text
certify_definition(..., evaluator_registry, proof_artifact_resolver)
ContractCertificate.evaluator_registry_hash
```

and use a structured `EvidenceEvaluationCertificate` binding component, grade, proof hashes, evaluator artifact, and result. Alternatively include the immutable evaluator allowlist in `policy_definition`.

### P0-5 — Handoff runtime identity and epoch checks are incomplete

`HandoffOffer` carries `producer_action_id` and `producer_definition_hash`, but the listed `validate_handoff()` checks do not compare them with the invocation and producer definition.

Required checks:

```text
offer.producer_action_id == invocation.skill_action_id
offer.producer_definition_hash == invocation.skill_definition_hash
offer.producer_definition_hash == H_WCJ(producer_definition)
offer.handoff_schema_id belongs to that exact producer definition
accepted producer_handoff_schema_hash == computed producer schema hash
```

Also, a pure validator cannot establish “epoch monotonicity” without authoritative state. Split this into:

```text
validator:
  offer.control_epoch == current invocation/authority epoch

authority manager:
  compare-and-swap owner + epoch
  issue next epoch
  reject old-epoch commands
  reject duplicate/replayed handoff offers
```

Add a unique `handoff_offer_id` or equivalent consumption token if replay prevention is required.

### P0-6 — Migration says UNKNOWN handoff-schema hash, but the type cannot represent it

`AcceptedHandoffSpec.producer_handoff_schema_hash` is a plain hash field. Migration says missing v1 information may become “UNKNOWN -> Draft”, while `DraftSkillDefinition` only permits UNKNOWN inside the execution bundle.

Therefore this migration outcome is not typeable.

Required correction: choose one:

```text
A. registry fixture must provide the schema hash; otherwise reject with E_MIGRATE_STATICS_ABSENT
B. introduce a typed SchemaRefSlot(KNOWN|UNKNOWN) in Draft only
```

Do not use a placeholder hash.

## 6. P1 completion items

1. `SOURCE_COMMIT` has `artifact_hash = null`, but the resolver signature requires `expected_sha256`. Add a tagged Git-commit resolver or a distinct resolution path.
2. `CONFIG_HASH` uses “claimed stage” without a typed stage discriminator. Pin the stage in the proof or derive it unambiguously from component and lineage.
3. `UNRESOLVED_DIFFERENCES` permits an explicit empty document while the resolver rejects zero-length bytes. Define the empty set as a non-empty canonical record such as `{"unresolved_differences":[]}`.
4. `UsageEligibilityReport` should report all applicability decisions—not only EXPLICIT_NONE exemptions—including lineage/profile N/A and OPTIONAL with stable reason codes.
5. The JSON is syntactically machine-readable, but several operative rules remain natural-language strings. Either encode them as typed condition/target structures or call the artifact “structured normative specification,” not an executable policy map.

## 7. Custody and records corrections

Before pS/pN dispatch:

1. design title/status: make both `v2.7.1`;
2. design evidence reference: `EvidencePolicy v1.4` -> `v1.5`;
3. review-4 status: remove header `PENDING` via immutable confirmation record;
4. pS record pointer: replace stale `cd5482310d` with the actual current bank/pin;
5. EvidencePolicy parent pointer: `v2.7` -> exact `v2.7.1`;
6. EvidencePolicy line saying the JSON fixture will be created during implementation: update because the fixture already exists;
7. include the JSON file’s full SHA in the design/policy header;
8. replace manifest `本 commit` with the explicit bank commit hash;
9. update manifest current-state line from `DESIGN v2.7` to `v2.7.1`.

## 8. Required tests added by this review

```text
- policy semantic projection golden test: metadata mutation does not change hash; every semantic-rule mutation does
- schema/spec HASH_BOUND valid and invalid claim-target cases
- SCRIPTED and WAIT HASH_BOUND/CLOSED_LOOP evidence cases
- arbitrary EvidenceRecord.artifact_hash/claim_target_hash mismatch rejection
- evaluator registry A/B changes certificate hash or eligibility as designed
- SOURCE_COMMIT typed resolver tests
- handoff producer_action_id mismatch rejection
- handoff producer_definition_hash mismatch rejection
- stale epoch and replayed offer rejection
- v1 missing producer schema hash -> deterministic Draft or deterministic migration rejection
```

## 9. Recommended next version and gate sequence

Produce:

```text
DESIGN v2.8
EvidencePolicy v1.6
EvidencePolicy v1.6 JSON
```

Bounded sequence:

```text
fix P0-1..P0-6 + records corrections
-> bank exact files with explicit commits
-> pS delta/full-line verification on those exact hashes
-> pN DESIGN re-verify on the same hashes
-> if PASS, freeze D1.1-A
-> proceed to D1.1-B, D1.1-C, and the 2-3-skill boundary-only vertical slice
```

Do not reopen D1.1-A for unrelated refinements after these corrections. Implementation, training, and authority remain closed until the exact final design receives PASS-CLOSE.
