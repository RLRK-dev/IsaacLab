# PLAN_STATUS_20260719(3) Review v2

- Reviewed archive: `PLAN_STATUS_20260719(3).zip`
- Archive SHA-256: `ca7b037336bd1c572d72e60eb911293f1a80143313c41cd781ca88cb82fd2dc4`
- Result: **OVERALL HOLD**
- Review basis: extracted 11 Markdown files, content hashes, internal cross-document consistency, and design-level semantic review.

## 0. Duplicate check

`PLAN_STATUS_20260719(2).zip` and `PLAN_STATUS_20260719(3).zip` are byte-for-byte identical:

```text
ca7b037336bd1c572d72e60eb911293f1a80143313c41cd781ca88cb82fd2dc4
```

The bundled `08_Rs_PLAN_STATUS_review.md` is also byte-for-byte identical to the previously generated standalone `PLAN_STATUS_review_2026-07-19.md`:

```text
fedd82bb252a8a47fa42c9cc0f78a3ee9315d2f4c406343a70d1d19c0a8406aa
```

Therefore `08_Rs_PLAN_STATUS_review.md` is the previous review preserved as an input/history record. It is not a new review of the updated package.

## 1. Verified improvements

The latest package is materially better than the original six-file archive.

- `00_PLAN_SUMMARY` now separates production implementation, diagnostic scaffolding, diagnostic smoke/readback, formal probe, training, and authority.
- The summary explicitly records WMSO as `scope CLOSED / implementation CLOSED` and the arm probe as `HOLD`.
- The summary contains full SHA-256 values for files 01–07, and every listed digest matches the extracted file bytes.
- WMSO design v2.1 and its pS verification are included.
- The arm design includes correction #2 and correction #3, including the imported-actuator finding and route-start pose finding.
- The substrate defect is now separately tracked and the summary no longer states that historical verdicts are automatically valid.

These are genuine improvements. They do not, however, remove the remaining contradictions in the governing design documents.

## 2. Package-level verdict

| Area | Verdict |
|---|---|
| Archive integrity | PASS |
| SHA table | PASS |
| Previous review traceability | PASS, but should be marked historical/superseded |
| WMSO scope | CLOSED; do not reopen |
| WMSO design v2.1 | **DESIGN HOLD** |
| WMSO implementation | CLOSED, correctly |
| Arm-control design | **DESIGN HOLD** |
| P-D1 formal probe | HOLD, correctly |
| PLAN_STATUS as a single source of truth | **HOLD** |

The summary is now mostly accurate, but it reports corrections that the canonical design documents themselves have not yet incorporated. A summary cannot override a conflicting design record.

# 3. WMSO design v2.1

## 3.1 Prior HOLD items that are successfully closed

The previous review’s main structural blockers are substantially addressed:

- static certification and runtime lifecycle validation are separated;
- execution identity and training provenance are separated;
- `UNKNOWN`, `EXPLICIT_NONE`, and `KNOWN` are represented separately;
- final `SkillActionId` is not issued while execution inputs remain unknown;
- fixed-six-decimal hashing is removed;
- component-specific evidence and `(component, grade) -> ProofKind` policy are introduced;
- runtime outcome/handoff duplicate fields are removed;
- draft migration is explicit;
- strict codec and metamorphic tests are added.

This is a strong revision. The following new or residual issues still block pN DESIGN PASS-CLOSE.

## W-P0-1 — `TrainingProvenance` is inconsistent for SCRIPTED and WAIT

`TrainingProvenance.final_artifact_hash` is mandatory for every skill and is required to equal `ExecutionBundle.executable_artifact_hash` (`06`, lines 87–101). However, the inherited lineage table says SCRIPTED/WAIT have no training hashes and use source closure instead (`06`, line 171 onward, inherited from v1.1).

For a scripted skill, the current types force one of two invalid interpretations:

1. put the source-closure hash into a field named `final_artifact_hash` inside `TrainingProvenance`, contradicting the “all training hash null” rule; or
2. leave it null, which the type does not permit and which fails the equality check.

Required correction: use a tagged provenance union.

```text
LearnedTrainingProvenance
  execution_family
  training_lineage
  final_policy_artifact_hash
  bc/demo fields

NonLearnedProvenance
  execution_family = SCRIPTED | WAIT
  training_lineage = NOT_APPLICABLE
  source_closure_hash
```

Alternatively make `final_artifact_hash` optional and apply the equality check only to learned skills, while explicitly checking source closure for non-learned skills.

## W-P0-2 — Definition certification and usage eligibility remain conflated

`certify_definition()` receives no requested usage profile, yet its validation list includes profile aggregation (`06`, lines 252–262). This leaves three incompatible interpretations:

- all profiles must pass before a certificate is issued;
- any one profile may pass;
- the certificate is profile-neutral and profiles are evaluated later.

The third interpretation is the sound one, but it is not expressed as a separate API.

Required split:

```text
certify_definition(...)
  -> static contract/evidence validity
  -> ContractCertificate

evaluate_usage_eligibility(
    certificate,
    evidence_bundle,
    evidence_policy,
    requested_profile,
    external_gate_state,
)
  -> UsageEligibilityReport
```

A definition with RECONSTRUCTED evidence may be valid and certifiable for offline use while remaining closed-loop ineligible. Static certification must not silently become “all profiles pass.”

## W-P0-3 — Schema-registry-dependent certification is not reproducible

`certify_definition()` accepts `SchemaRegistry`, and static handoff compatibility depends on its contents (`06`, lines 252–261). The resulting certificate binds definition, evidence, policy, and validator hashes, but not the registry (`06`, lines 278–286).

The same definition could therefore pass under registry A and fail under registry B while producing a certificate with no record of which registry was used.

Required correction: either

- add `schema_registry_hash` to `ContractCertificate`; or
- make every referenced schema content-addressed and prove compatibility solely from hashes embedded in the definition.

The same rule applies to predicate registries if initiation/termination references are resolved during certification.

## W-P0-4 — EvidencePolicy v1 is a required design artifact but is absent

The design explicitly requires the complete EvidencePolicy table to be banked and included in pN DESIGN verification (`06`, lines 223–246). The ZIP contains no EvidencePolicy artifact.

Therefore:

```text
pS design-axis delta confirm: usable as an intermediate review
pN DESIGN PASS-CLOSE: not yet possible
implementation GO: remains closed
```

The summary already describes EvidencePolicy as a next step; that gate must remain hard.

## W-P1-1 — WCJ has a key-domain contradiction

The canonicalizer is described as supporting UTF-16 key ordering and a non-BMP golden vector, while also asserting that every hash-visible object key is 7-bit ASCII (`06`, lines 150–163).

If the canonicalizer rejects non-ASCII keys, the non-BMP object-key vector cannot pass through that canonicalizer.

Required correction: define two layers explicitly.

```text
jcs_canonicalize_generic:
  RFC-style Unicode key ordering; golden vectors include non-BMP keys

wmso_typed_encode:
  only schema-generated ASCII field names; rejects arbitrary/non-ASCII keys
```

Then hash WMSO objects as `jcs_canonicalize_generic(wmso_typed_encode(x))`.

## W-P1-2 — Learned policy normalization cannot always be assumed to exist

The design forbids `EXPLICIT_NONE` for a learned policy’s normalization slot (`06`, lines 50–83). A learned policy can legitimately consume already-normalized/raw observations and have no separate normalizer artifact.

Safer alternatives:

- rename the field to `preprocessing_spec` and always require a KNOWN hash, including a content-hashed identity transform; or
- allow `EXPLICIT_NONE` when training evidence proves that no normalization/preprocessing was applied.

Do not encode an empirical assumption as a universal type invariant.

## W-P1-3 — Evidence hashing does not fully define ProofItem canonical order

Records are sorted by component, but the order of `ProofItem` entries inside each record is not fixed (`06`, lines 191–240). Duplicate proofs are described as idempotent, but conflicting duplicates with the same `(kind, ref)` and different hashes are not defined.

Required rule:

```text
proof items sort by (kind rank, ref, artifact_hash-or-empty)
exact duplicate -> deduplicate
same (kind, ref) with different artifact_hash -> E_PROOF_CONFLICT
```

Add a proof-order shuffle metamorphic test.

## W-P1-4 — `TRAINING_PROVENANCE` has no profile role

`TRAINING_PROVENANCE` is a declared evidence component, but it is absent from the listed closed-loop required set (`06`, lines 179–246). Either:

- require it for learned-skill registration/closed-loop eligibility; or
- explicitly designate it as informational and explain why it cannot affect any usage profile.

Leaving a component in the evidence model without a policy role makes its authority semantics unclear.

## W-P1-5 — Test #4 names the wrong object

The metamorphic table says “TrainingProvenance grade/records change,” but `TrainingProvenance` has no grade (`06`, lines 397–408). This should distinguish:

```text
EvidenceRecord(TRAINING_PROVENANCE) change
  -> ActionId unchanged; EvidenceBundleHash/certificate changes

TrainingProvenance field change
  -> ActionId unchanged; SkillDefinitionHash/certificate changes
```

## W-P1-6 — Runtime report types and clock inputs need definition

`LifecycleValidationReport` and `HandoffValidationReport` are named but not typed. `validate_invocation_start()` evaluates freshness without an explicit `now` or clock parameter.

Define stable issue structures and pass a deterministic clock/time value. Avoid hidden wall-clock access in validation tests.

# 4. Arm-control design v1.3

The summary correctly keeps the formal probe on HOLD. The governing design itself still contains unresolved contradictions.

## A-P0-1 — Header/version/status is still stale

`04_d_controldesign_v1.3_asread.md` line 3 still says:

```text
Status: DESIGN v1.1 — 0-commit
```

while the same line narrates v1.2 and v1.3 changes, and the summary calls v1.3 banked.

Required correction: create and bank a canonical v1.3 document with a short header and a separate change log. Do not use one very long status line as both status and history.

## A-P0-2 — B1/B2 remains delegated to implementation

M-1 still permits either:

- strip imported actuators (`nu=16`); or
- retain but neutralize them (`nu=28`).

It then says the mechanism choice belongs to `%12` (`04`, line 36). This choice changes model topology, actuator indices, readback, and failure modes; it is a design decision.

Required ruling before prereg freeze: **B1 or B2, selected by the design owner**. B1 remains the cleaner default. If B2 is selected, dynamic zero-force verification is required in addition to model-array checks.

## A-P0-3 — L-P0 is REQUIRED in the summary but still RECOMMENDED/deferable in the design

The summary promotes L-P0 to REQUIRED. The design still says `RECOMMENDED`, allows four runs if deferred, and excludes it from the pass expression (`04`, lines 121–132).

Required correction:

- mark L-P0 `REQUIRED` in the design and prereg;
- remove the four-run alternative;
- state whether L-P0 is a P-D1 pass condition or a mandatory impact-assessment output that gates historical evidence reuse.

## A-P0-4 — Historical contrast validity is still overclaimed in the canonical design

The summary now correctly says historical impact is unresolved. The control design still states that banked contrast verdicts are “internally valid as-is” because the disturbance was common to both sides (`04`, line 167).

A state-dependent torque disturbance is not guaranteed to cancel between runs with different trajectories, contact states, or grasp outcomes.

Required replacement:

```text
The finding alone does not automatically invalidate every prior contrast.
Continued use of each load-bearing verdict remains conditional on L-P0 sensitivity measurement and review.
```

## A-P0-5 — Probe specification is stale after finding #2

Finding #2 establishes that the FF path bypassed the RL-path site and required wiring in `apply_recorded_arm_ff`. The v1.3 header acknowledges that fix, but §5 still says the experimental flag migrates “only the per-step drive :1270 site” (`04`, line 121).

The formal prereg must enumerate the actual FF-path write sites exercised by P-D1. A probe whose design description names the wrong active site is not frozen.

## A-P0-6 — L-P4 and the run matrix are internally inconsistent

The v1.3 header says L-P4 was repurposed after the route-start teleport. §5 still defines L-P4 as a settle-to-route ramp on/off comparison (`04`, line 128). The run count lists one “ramp” run, even though the text says ramp on/off each one (`04`, lines 128–132). §10 then refers to four runs.

Required correction: publish one explicit run matrix with one row per run, flags, substrate, expected artifact, and pass/fail role.

## A-P1-1 — Tracking trip remains single-frame and is misnamed

M-6 is still called `anti-windup`, although the detected condition is tracking divergence, and it trips on a single frame above 15 mrad (`04`, lines 40–41, 74–85).

Add:

- startup/teleport/ramp grace semantics;
- consecutive-frame or dwell requirement;
- phase-specific threshold;
- hysteresis/reset rule;
- exact termination reason code;
- rename to `tracking_divergence_tripwire`.

## A-P1-2 — Gain hierarchy is still marked PASS before measurement

The hierarchy table marks arm-vs-gripper and effort relationships as PASS while the same section admits that coordinates differ and L-P3 is needed (`04`, lines 182–190).

Change these rows to `UNVERIFIED — L-P3` until measured.

## A-P1-3 — `gains ×0.1 must fail` is not a guaranteed negative control

A 0.1-gain controller may still satisfy a short/easy trajectory. If it passes, that does not prove the instrumentation is invalid.

Use a stronger deterministic negative control, for example:

- arm actuation disabled;
- fixed stale target;
- deliberate target offset above the declared bar.

If ×0.1 is retained, define it as an expected-fail exploratory leg with a fallback negative control.

## A-P1-4 — Route-start teleport needs full-state acceptance checks

The arm-only re-pose is intended to reproduce the banked frame-0 state, but the design should explicitly verify:

- joint limits and winding representation;
- gripper state;
- cable/object pose consistency;
- no initial penetration/self-collision;
- bounded contact impulse immediately after forward/step;
- q, qd, ctrl, and derived kinematic state synchronization;
- recording identity/hash used for frame 0.

The existing OPEN/non-grasp assertion is useful but not sufficient to prove full-state consistency.

# 5. PLAN_STATUS/document-control issues

## P-P0-1 — Summary and governing docs disagree

The summary has the safer current state, but the control design still contains the old claims. The authoritative fix must land in the design document, not only in `00_PLAN_SUMMARY`.

## P-P0-2 — WMSO documents are untracked

The summary records WMSO design v2.1 and pS verify as untracked. They cannot support a banked-SHA pN verdict until explicitly banked and read back.

## P-P1-1 — The old Rs review should be labeled historical

Because `08_Rs_PLAN_STATUS_review.md` is exactly the previous review, rename or annotate it as:

```text
08_Rs_PLAN_STATUS_review_v1_SUPERSEDED.md
```

and include this report as a new review artifact. This prevents readers from assuming the old review analyzed v2.1/v1.3.

## P-P1-2 — Placeholder times remain in authoritative/as-read docs

Examples include `08:1x`, `09:2x`, and `09:4x`. Replace them with exact times before declaring a document final/banked, or state explicitly that the as-read copy preserves historical placeholders and is not the canonical final record.

# 6. Corrected current status

```text
WMSO D1.1-A
  scope:          CLOSED
  design:         HOLD — new P0 corrections + EvidencePolicy artifact + CC Debate + pN verify
  implementation: CLOSED
  training:       CLOSED
  authority:      CLOSED

Arm-control remediation
  design:         HOLD — canonical v1.3 not internally closed
  diagnostic code: BUILT, UNLANDED
  diagnostic smoke: EXECUTED
  formal P-D1:    HOLD
  production impl: CLOSED
  training:       CLOSED
  authority:      CLOSED

PLAN_STATUS package
  archive/hash integrity: PASS
  operational SSOT: HOLD
```

# 7. Recommended next order

1. Decide arm B1/B2 in the design court; prefer B1 unless a measured reason favors B2.
2. Rewrite the canonical arm v1.3 header and fold L-P0, historical-impact language, actual FF sites, L-P4, run matrix, trip semantics, and hierarchy statuses.
3. Bank/read back the corrected arm design; only then freeze the P-D1 prereg.
4. Correct WMSO P0-1 through P0-3 in design v2.2.
5. Produce the full EvidencePolicy v1 artifact and bind registry/policy hashes.
6. Run CC Debate on the corrected WMSO design and artifact set.
7. Bank/read back WMSO design + pS verification + EvidencePolicy; then request pN DESIGN PASS-CLOSE.
8. Keep implementation, training, and authority closed until their respective gates pass.

## Final decision

The archive is internally better documented and its hash table is correct. It is **not yet implementation-ready**. The appropriate disposition is:

> **Archive integrity PASS; WMSO DESIGN HOLD; arm DESIGN HOLD; formal probes/implementation remain CLOSED.**
