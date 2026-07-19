# PLAN_STATUS Review v3 — 2026-07-19

## 1. Review target and integrity

Target archive:

- `/mnt/data/PLAN_STATUS_20260719.zip`
- SHA-256: `77dc0495beb10467e1f3d1f192517d644ea806e98d7fa88792e794af682195b8`
- Size: 91,924 bytes

This archive is not identical to the prior `(2)/(3)` archive (`ca7b0373...`, 74,818 bytes). It contains updated WMSO design v2.2, EvidencePolicy v1, arm-control design v1.4, and the prior Rs reviews as history.

The SHA-256 values listed in `00_PLAN_SUMMARY_p6_20260719.md` for files 01–07 match the extracted bytes.

## 2. Overall verdict

**OVERALL HOLD**

| Surface | Verdict |
|---|---|
| Archive byte integrity | PASS |
| WMSO D1.1-A scope | CLOSED; do not reopen |
| WMSO design v2.2 | DESIGN HOLD |
| WMSO implementation/training/authority | CLOSED; correct |
| Arm-control design v1.4 | DESIGN HOLD |
| Formal P-D1 probe | HOLD; correct |
| PLAN_STATUS as self-contained SSOT | HOLD |

The summary's top-level decision to keep both arcs on HOLD is correct. The remaining problems are design closure and package self-containedness, not scope reopening.

## 3. Material improvements since review v2

### WMSO

The following prior blockers are materially improved:

- Execution identity and training provenance are separated.
- Learned and non-learned provenance are conditionally distinguished.
- `KNOWN / EXPLICIT_NONE / UNKNOWN` slots and Draft-vs-certified definitions are present.
- Final `SkillActionId` is blocked while identity inputs remain unknown.
- Static certification and runtime lifecycle checks are separated at the architectural level.
- RFC-8785-compatible key ordering, strict codec requirements, CanonicalDecimal, migration disposition, and metamorphic tests are substantially stronger.
- EvidencePolicy v1 now exists as a separate artifact.

### Arm control

The following prior blockers are materially improved:

- B1 strip-at-import is selected as the primary mechanism.
- L-P0 is promoted to REQUIRED in the substantive design text.
- Historical verdict language is weakened appropriately and clean-substrate validity is marked UNVERIFIED.
- The divergence guard has persistence semantics and a more accurate name.
- Gain/force hierarchy claims are marked UNVERIFIED rather than PASS.
- The `@4 is conservative` claim is explicitly tagged as a hypothesis.

## 4. WMSO design v2.2 — blocking findings

### W-P0-1 — EvidencePolicy cannot authorize SCRIPTED or WAIT skills

The design forces these execution slots for SCRIPTED/WAIT:

- `model_architecture = EXPLICIT_NONE`
- `tensor_binding = EXPLICIT_NONE`
- `normalization = EXPLICIT_NONE`

See `06_WMSO_D11A_design_v2.2_asread.md`, lines 72–81.

However EvidencePolicy requires, without conditioning on skill kind:

- MODEL_ARCHITECTURE for closed-loop, shadow, and offline replay
- TENSOR_BINDING for closed-loop and shadow
- NORMALIZATION for closed-loop, shadow, and offline replay

See `06b_WMSO_EvidencePolicy_v1.md`, lines 51–67.

No `NOT_APPLICABLE` evidence grade or cryptographically bound absence proof exists. Therefore a correctly declared SCRIPTED or WAIT skill can never satisfy the profiles. This is central because WMSO explicitly relies on scripted, transition, recovery, and wait-type actions.

**Required correction:** define component applicability as a function of `IdentityKind` / lineage, for example:

```text
ApplicabilityResolver(kind, lineage, component)
  -> REQUIRED(min_grade) | NOT_APPLICABLE | OPTIONAL
```

For non-applicable components, either exclude them from aggregation or require a distinct, validated proof of non-applicability. Do not treat N/A as UNKNOWN.

### W-P0-2 — SchemaRegistry affects certification but is not bound into the certificate

`certify_definition(..., schema_registry)` and handoff compatibility depend on registry contents, while `ContractCertificate` does not contain a registry hash. See design lines 229–244.

The same definition and evidence can therefore pass under one registry snapshot and fail under another while producing indistinguishable certificate fields.

**Required correction:** use one of:

1. `schema_registry_hash` in the certificate; or
2. content-addressed producer definition/schema hashes in every accepted handoff reference.

A mutable registry object must not be an unrecorded certification input.

### W-P0-3 — Definition certification and usage eligibility remain underspecified

The design defines `certify_definition()` but does not define a separate, typed API/result for OFFLINE_REPLAY, SHADOW, and CLOSED_LOOP eligibility. The test plan refers to eligibility, but no `UsageEligibilityReport` or evaluation contract exists.

This matters because:

- a definition may be valid while evidence is insufficient for a particular usage;
- an old certificate may remain historically valid while current policy becomes stricter;
- a certificate must never be interpreted as an authority grant.

**Required correction:** define:

```python
evaluate_usage_eligibility(
    certificate,
    evidence_bundle,
    current_evidence_policy,
    usage_profile,
) -> UsageEligibilityReport
```

The report should include profile, applicable components, effective grades, stable issue codes, policy hash, and eligibility. Acceptance tests, O0/S0/V0 two-key, and safety gates remain external conjuncts.

### W-P0-4 — The design is still not self-contained on evidence types

Design line 216 says the evidence types are “unchanged from v2.1,” but does not define:

- `ComponentKind`
- `EvidenceGrade`
- `ProofKind`
- `ProofItem`
- `EvidenceRecord`
- `EvidenceBundle`
- eligibility/report types

The current archive does not include design v2.1. EvidencePolicy defines tables and ProofKind meanings, but not the complete type schema. This reintroduces the cycle-1 self-containedness defect.

**Required correction:** inline all type definitions in v2.3 or provide a machine-readable sibling schema whose hash is normative and included in the archive.

### W-P0-5 — EvidencePolicy proof obligations contain semantic gaps

Examples:

- `HASH_BOUND_REPRODUCED` for TRAINING_PROVENANCE does not require `REPRODUCED_OUTPUT_HASH`.
- `RECONSTRUCTED_COMPATIBLE` for TRAINING_PROVENANCE does not require a compatibility/consistency test.
- The component-specific override at EvidencePolicy line 45 is ambiguous about whether it replaces or supplements the group rule.
- Duplicate proofs with the same `(kind, ref)` but different payload/hash have no explicit conflict rule.

**Required correction:** make the policy a total machine-readable map:

```text
(component_kind, evidence_grade, applicability_class)
  -> exact required ProofKind set
```

Conflicting duplicate proof claims must fail closed.

### W-P0-6 — Highest-precedence review transcript is absent from the archive

The design declares `WMSO_RS_REVIEW4_DESIGN_TRANSCRIPT_20260719.md` a sibling normative artifact and gives it highest precedence after Rs confirmation. The summary also claims it was banked. It is not included in the current ZIP, and only an abbreviated hash appears in the design.

**Required correction:** include the transcript, full SHA-256, canonical path, bank commit, and confirmation status in the PLAN_STATUS table. Until then the archive cannot independently substantiate its top-precedence design source.

### W-P1-1 — Source-closure aggregate hashing is not fully specified

The action identity for SCRIPTED/WAIT depends on an aggregate source-closure hash, but the design does not pin:

- relative-path normalization
- member ordering
- symlink treatment
- line-ending treatment
- composition format of path and member hash
- duplicate path behavior

This must be deterministic before it can participate in `SkillActionId`.

### W-P1-2 — `behavior_revision` is a manual identity safety valve

Initiation/termination semantics can change without changing `SkillActionId` if an editor forgets to increment `behavior_revision`.

Add either:

- a derived `BehaviorSignatureHash` to action identity; or
- a registry invariant that rejects behavior-affecting changes under an unchanged action ID/revision.

### W-P1-3 — Separate semantic policy hash from document custody hash

`evidence_policy_hash = markdown file SHA-256` pins the exact document, including status/timestamp/editorial changes. Keep this as a document hash, but also define a canonical machine-readable policy-definition hash used by validators and certificates.

## 5. Arm-control design v1.4 — blocking findings

### A-P0-1 — Header still contradicts the banked state

The first status line says `DESIGN v1.4 — 0-commit (bank = %12)`, while the version table and PLAN summary state that v1.4 is banked at `e32c75c3a4`.

**Required correction:** use a single canonical status, for example:

```text
DESIGN v1.4 BANKED — implementation CLOSED — formal probe HOLD
```

### A-P0-2 — B1 is primary, but B2 fallback is not re-gated

B1 is selected, but B2 remains available if stripping is considered impossible. The document does not state that switching to B2 requires a design delta and re-verification.

**Required correction:**

```text
B1 failure/infeasibility -> STOP -> design delta -> p5/pN re-review.
Implementer may not select B2 unilaterally.
```

### A-P0-3 — Formal FF probe still targets the wrong execution site

The design correctly identifies the FF path at `route_executor.py:5050` / `apply_recorded_arm_ff`, and finding #2 proves that FF bypasses the RL `:1270` site. However the probe specification still says the experimental migration target is the `:1270` path only.

A formal FF whole-route probe built from that text can again exercise kinematic FF while believing it exercises PD.

**Required correction:** enumerate every active FF command path in the prereg and add a positive readback assertion that the selected path updates the arm target on every expected frame.

### A-P0-4 — Probe run matrix is still internally inconsistent

Current contradictions include:

- L-P0 is REQUIRED, but the run-count text still says it may be deferred.
- L-P4 is repurposed to route-start synchronization, while a separate “ramp run” remains without a defined event/contrast.
- The declared primary baseline is contaminated kinematic, even though clean kinematic is available as L-P0.

Use an explicit matrix:

| Run | Drive | Imported actuator | Purpose |
|---|---|---|---|
| R0 | kinematic | current/contaminated | historical substrate reference |
| R1 | kinematic | B1 clean | L-P0 contamination isolation |
| R2 | PD nominal | B1 clean | main realization/acceptance contrast vs R1 |
| R3 | PD nominal | B1 clean + specified ramp event | ramp effect only |
| R4 | PD negative control | B1 clean | fail-able instrumentation |

Then define:

- contamination effect = R0 vs R1
- PD realization effect = R1 vs R2
- total migration effect = R0 vs R2
- ramp effect = R2 vs R3

### A-P0-5 — The negative control is known to be non-discriminating but remains in the pass equation

The design states that gains ×0.1 did not separate from nominal and must be redesigned. Nevertheless:

- L-P5 still says ×0.1 must fail;
- the overall pass equation still requires L-P5 FAIL;
- the sensitivity table still lists ×0.1 as the mandatory negative control.

**Required correction:** replace L-P5 before prereg freeze. A deterministic fault injection such as stale target, disabled live actuator set, deliberate target step, or a settling-time perturbation with a predeclared expected failure is preferable.

### A-P0-6 — L-P2 acceptance semantics remain undefined

The design downgrades parity to characterization and says clean-substrate acceptance will be redefined in the next prereg. That is correct, but it means the present probe specification is not closure-ready. The pass equation must not cite L-P2 until the new criterion is explicit.

### A-P1-1 — Route-start teleport acceptance is incomplete

Current checks include OPEN/non-grasp and q/qd/ctrl synchronization. Add:

- joint-limit and winding validity
- cable/gripper pose consistency
- penetration/contact-distance check before the first physics step
- first-step contact impulse/force bound
- no equality/pin ownership inconsistency
- exact recording/source hash in the run record

### A-P1-2 — `implicitfast` is not a stability guarantee

Implicit integration reduces numerical stiffness constraints, but does not guarantee closed-loop stability or physical fidelity with contacts and saturation. Keep the two-cadence empirical gates as the authority and soften the analytical wording.

## 6. PLAN_STATUS package corrections

1. Include the missing review-4 transcript and its full custody record.
2. Mark review v2 as historical/baseline for v2.1/v1.3 once this review v3 is added.
3. Correct the summary claim that the arm header is fixed; the as-read header still contains `0-commit`.
4. Add the current cycle-2 output when available. The included pS verify is explicitly only through v2.1 plus the cycle-1 failure addendum.
5. Keep the following gates closed:
   - WMSO implementation/training/authority
   - arm production implementation
   - formal P-D1 probe

## 7. Required next sequence

### WMSO

1. Fix kind-conditional evidence applicability.
2. Bind SchemaRegistry into certification.
3. Define `UsageEligibilityReport` and current-policy evaluation.
4. Make evidence types and ProofPolicy machine-readable/self-contained.
5. Include and confirm the review-4 transcript.
6. Run CC Debate cycle-2 against the new exact SHA.
7. pS delta verification.
8. pN DESIGN PASS-CLOSE on the final SHA only.

### Arm control

1. Publish canonical v1.5 status/header.
2. Make B2 a STOP/re-design fallback, not an implementation choice.
3. Fix FF site enumeration and positive path readback.
4. Freeze an explicit R0–R4 run matrix and clean-clean main contrast.
5. Replace L-P5 and define L-P2 acceptance.
6. Complete teleport safety checks.
7. Bank/read back v1.5, then freeze the formal P-D1 prereg.

## 8. Final status wording

```text
PLAN_STATUS archive integrity: PASS
WMSO scope: CLOSED
WMSO design: HOLD — revision required
WMSO implementation/training/authority: CLOSED
Arm design: HOLD — v1.5 required
Formal P-D1 probe: HOLD
Operational SSOT: HOLD — missing normative transcript + remaining cross-document contradictions
```
