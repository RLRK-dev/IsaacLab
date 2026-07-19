# PLAN_STATUS Review v5 — 2026-07-19

## 1. Review target

- Archive: `/mnt/data/PLAN_STATUS_20260719(3).zip`
- Size: `136462` bytes
- SHA-256: `581fc38f6698c8a3893cf3a9abb8954b7e93fa5c8c1c3edf01eca1f4240b4c05`
- Previous archive: `/mnt/data/PLAN_STATUS_20260719(2).zip`
- Previous SHA-256: `5aa20817e0b4119825de9927e86d3dae4ab421c4fc055f9d5b6d2348741cd69d`
- Conclusion: the archive is new, not a duplicate.

The archive contains 15 Markdown files, including WMSO design v2.5 working-tree content, EvidencePolicy v1.3 working-tree content, arm-control design content through v1.7/v1.8 notes, and the P-D1 result.

## 2. Overall verdict

```text
Archive byte integrity:                     PASS
Summary-to-as-read SHA consistency:          PASS
WMSO D1.1-A scope:                           CLOSED — maintain
WMSO design:                                 HOLD
WMSO implementation/training/authority:      CLOSED — maintain
Arm P-D1 evidence run:                       COMPLETED, provisional interpretation
Arm production implementation/training:      CLOSED — maintain
Operational PLAN_STATUS SSOT:                HOLD
```

The archive is materially better than v4, but it is not a final, bankable single source of truth. It deliberately mixes banked pins with later working-tree snapshots. That can be useful for handoff, but the current design and evidence status must not be interpreted as gate closure.

## 3. Custody and status findings

### C-P0-1 — pN DESIGN HOLD B1-B7 record is absent

The summary says pN issued `DESIGN HOLD B1-B7` at 13:26. The archive does not contain the pN verification artifact. Only the summary and the design author's fold claims are present.

Therefore the package cannot independently establish:

- the exact B1-B7 wording;
- the exact reviewed SHA;
- whether v2.5 closes each pN finding without semantic drift.

**Required:** include the pN DESIGN verify/HOLD document with canonical path, full SHA-256, commit, and reviewed design/policy hashes.

### C-P0-2 — pS final-confirm record remains unbanked

File 07 has actual SHA-256:

```text
43ef06ef7f137659a6c6beb3f4aa6dbefed1085011bd9bbac7b940321ac31ded
```

The summary correctly marks this as a working-tree-only record. Until it is explicitly banked and read back, it cannot satisfy the records leg of pN B1.

### C-P0-3 — review-4 transcript fidelity

`11_WMSO_RS_review4_transcript.md` is semantically faithful to the prior review message in this conversation. I found no material omission or change in the findings, verdict, required fixes, or internal summary.

It is not byte-identical to a source file because the source was a chat message and the transcript normalizes Markdown bullets and link references. The correct record is:

```text
semantic fidelity: CONFIRMED
byte identity: NOT APPLICABLE — no original file existed
```

The transcript's `Rs確認 PENDING` can therefore be changed to `SEMANTIC FIDELITY CONFIRMED`.

### C-P0-4 — working-tree content and filenames are intentionally out of sync

Examples:

- file name says WMSO design v2.4.1, content title says v2.5;
- file name says EvidencePolicy v1.2, content title says v1.3;
- file name says arm design v1.6, content contains v1.7 and v1.8 result/readback notes.

The summary explains this as an as-read snapshot, so the SHA table itself is not false. Nevertheless, this is not suitable for a final review packet. Final banking should use canonical filenames matching the content version, or a machine-readable manifest mapping logical artifact versions to blob hashes.

## 4. WMSO design v2.5 / EvidencePolicy v1.3

### 4.1 Material improvements

The following prior findings are materially improved:

- callable selection is now hash-visible for SCRIPTED/WAIT;
- source-closure hashing is deterministic;
- behavior revision has a registry backstop;
- proof payload/binding rules have been added;
- closed-loop evidence floors were raised to the Rs-approved ceiling;
- evidence rank ordering is explicit;
- schema-registry projection is defined;
- eligibility remains distinct from authority grant;
- the review-4 transcript is bundled.

These are real improvements. The design is close to a stable D1.1-A boundary, but the following blockers remain.

### W-P0-1 — current design and current EvidencePolicy contradict each other

The design's evidence section still says:

```text
all tables = EvidencePolicy v1.2
TRAINING_PROVENANCE closed-loop minimum >= 2
```

The bundled policy content is v1.3 and defines:

```text
TRAINING_PROVENANCE closed-loop minimum >= 3
```

The policy header itself says `EvidencePolicy v1.3` on line 1 but `status: DRAFT v1.2` on line 5.

**Required:** remove every stale v1.2/`>=2` normative statement, update the parent-design pointer to v2.5, and re-run the semantic-hash golden fixture.

### W-P0-2 — SCRIPTED/WAIT still cannot satisfy TRAINING_PROVENANCE

The ApplicabilityResolver exempts EXPLICIT_NONE bundle slots and makes TRAINING_DATASET conditional on BC lineage. It does not mark TRAINING_PROVENANCE as not applicable for SCRIPTED/WAIT.

Consequently:

```text
SCRIPTED/WAIT
  training_lineage = NOT_APPLICABLE
  TRAINING_PROVENANCE required for CLOSED_LOOP at grade >=3
```

But the TRAINING_PROVENANCE proof policy at grade 3/4 requires training-run/config/final-artifact evidence that a non-learned skill cannot legitimately provide.

**Required:** one of:

1. `TRAINING_PROVENANCE -> NOT_APPLICABLE` for SCRIPTED/WAIT; or
2. split `TRAINING_PROVENANCE` and `EXECUTION_PROVENANCE`, using the latter for source-closure-based actions.

Do not encode non-applicability as UNKNOWN.

### W-P0-3 — proof binding is not total or executable

Three gaps remain.

1. `CONFIG_HASH` is required for learned-policy evidence, but `TrainingProvenance` has no generic final/RL training-config hash. It only has `bc_config_hash`. RL_ONLY PPO evidence therefore has no field to bind against.
2. `FINAL_ARTIFACT_HASH` is required for TRAINING_PROVENANCE claims, but the binding table does not define the TRAINING_PROVENANCE target.
3. `certify_definition()` receives no proof-artifact resolver or trusted evaluator result. It cannot inspect the manifest, binding blob, reproduction procedure, or compatibility-test bytes whose hashes are asserted. Structural hash matching alone does not make the grade measured rather than self-asserted.

**Required:** add, at minimum:

```text
TrainingProvenance.final_training_config_hash
TrainingProvenance.final_source_commit
```

and define either:

```text
certify_definition(..., proof_artifact_resolver)
```

or a separately certified `EvidenceEvaluationCertificate` produced by an allowlisted evaluator artifact and bound into `EvidenceRecord`.

### W-P0-4 — BehaviorSignature omits semantic observation/action schemas

The behavior-signature section claims a complement definition but enumerates only 11 current surfaces. `semantic_obs_schema` and `semantic_action_schema` are absent.

A schema-semantic change under the same bundle, variant, and behavior revision can therefore evade `E_BEHAVIOR_REVISION_STALE`, even though it changes the interpretation of the skill action and SDM data.

**Required:** include at least:

```text
semantic_obs_schema
semantic_action_schema
```

in the behavior-bearing signature. Add one mutation test for each.

### W-P0-5 — handoff references and registry projection remain ambiguous

`AcceptedHandoffSpec` still references:

```text
producer_skill_id + handoff_schema_id + major version
```

It does not identify producer variant, action ID, definition hash, or schema content hash. Multiple variants of one skill can therefore make the producer reference ambiguous.

The registry projection also uses a plain `schema_id`; if schema IDs are skill-local, collisions are possible. Hashing the entire registry additionally causes unrelated schema additions to churn all certificates.

**Required:** prefer a content-addressed reference:

```text
producer_handoff_schema_hash
```

or at least:

```text
producer_skill_action_id + handoff_schema_id
```

The certificate should bind the transitive projection actually used by the definition, not necessarily the entire global registry.

### W-P0-6 — EvidencePolicy is described as machine-readable but no canonical policy object is included

The Markdown defines `policy_object` and its semantic hash, but the archive contains no canonical JSON fixture or generated semantic-hash value. A validator cannot independently prove that its hard-coded table equals the reviewed Markdown semantics.

**Required:** include one normative machine-readable artifact, for example:

```text
WMSO_EvidencePolicy_v1.3.json
```

with:

```text
(component, grade, applicability class)
  -> exact proof set / min grade / usage ceiling
```

and publish both document SHA and semantic-definition SHA.

### W-P1-1 — design v2.5 is still a delta document

The design repeatedly states `v2.2 unchanged` for lineage, codec, handoff compatibility, runtime types, migration, and tests. The v2.2 blob is not included in this archive.

This is acceptable for an internal repository review with guaranteed commit access, but not for a self-contained transfer package or external design close.

**Disposition:** final pN packet should contain either a full v2.5 snapshot or a dependency manifest plus all referenced blobs.

### WMSO gate decision

```text
Scope: CLOSED
Design: HOLD
Implementation: CLOSED
```

The transcript-fidelity part of B1 is discharged by this review. The unbanked pS record, absent pN record, and technical issues above remain.

## 5. Arm-control v1.6+ and P-D1 result

### 5.1 Prior findings that are genuinely closed

- B2 fallback now requires STOP + design delta + p5/pN re-review.
- B1 strip-at-import is used for the evidence-grade clean substrate.
- the FF command path is explicitly instrumented;
- the result reports `max|ctrl-intended| = 0.0`, closing the positive write-path assertion;
- L-P0 was executed rather than deferred;
- the stale-target instrument leg successfully demonstrated fail-ability;
- the ramp leg was empirically shown to be a no-op under a synchronized route start.

### A-P0-1 — arm document status is internally stale

The header says:

```text
DESIGN v1.6 (bank pending), latest banked = v1.5, evidence = zero
```

The same document's version table says v1.6 is banked, later adds v1.7, and §13 records p5 adjudication plus a v1.8 prereg readback. The PLAN summary still says v1.6 and `p5裁定待ち`.

These cannot all be current.

**Required current status:**

```text
P-D1 run: complete
p5 verdict: complete — FAIL(tracking-transient)
video/Rs physical interpretation: pending
next prereg/gain exploration: drafted/read back, bank status to be recorded
production/training: closed
```

Publish a canonical v1.8-or-later design snapshot with a single status header.

### A-P0-2 — obsolete L-P5 and pass equation remain normative

The main probe section still says:

```text
L-P5 = gains x0.1 must fail
overall pass requires L-P5 FAIL
```

A later section supersedes this with stale-target as the primary instrument and x0.1 as exploratory. The actual result follows the later rule, but the document remains two-valued.

**Required:** rewrite the main L-P5 definition and pass equation directly. Do not rely on a later supersession note.

### A-P0-3 — the ramp run is confirmed to be informationally empty

R3 is exactly equal to R2 because the route-start q/ctrl synchronization removes the command jump that would trigger the ramp.

This confirms the prior prediction. Future run matrices should either:

- remove the ramp leg; or
- define an explicit, isolated jump event and compare only that event.

Do not retain a run that is structurally identical to nominal.

### A-P0-4 — run IDs are not traceable across design/result/package

The design uses:

```text
R0, R0b, R1, R2, R3, R4
```

The result uses:

```text
R0, R1, R2, R3, R4, R5
```

The summary calls this the canonical R0-R4 matrix, while also saying six runs completed. The governing P-D1 prereg v1.2 is not included, so the package cannot resolve the mapping.

**Required:** include the frozen prereg and a run-ID crosswalk with run directory, drive mode, substrate, purpose, and exact config hash.

### A-P0-5 — P-D1 evidence is not self-auditing in this archive

The result cites `analysis_result_v12.json`, run summaries, `COMPLETE.ok`, source-integrity checks, and per-step logs. None are included in the package.

The numerical claims may be accurate, but this archive only contains the narrative result. Independent verification is impossible.

**Required minimum evidence manifest:**

```text
prereg v1.2 blob/hash
probe code hash
run config hash per run
run summary hash per run
analysis_result_v12.json
video/render manifest
source-integrity report
```

Raw high-volume trajectories may remain external if each is content-addressed.

### A-P0-6 — conclusions are stronger than the evidence supports

The result states that the chain flip is carried `entirely` by cable-side physics and that the choreography `requires` contamination.

The measured facts strongly support a substrate dependency for this pinned deterministic replay. They do not yet prove a universal requirement because:

- there is one seed/run per condition;
- contact dynamics can amplify a 1.1 mrad arm difference;
- the video leg is pending;
- raw evidence is not bundled.

Use the bounded wording:

> Under the pinned build, seed, recording, and B1-clean contrast, the deterministic banked replay failed to form the grasp chain after the hidden actuator load was removed. The result is consistent with contact/cable dynamics being the dominant mediator.

Likewise, the `viscous lag` explanation is a well-supported working mechanism, not yet causal identification. C-1/C-2 perturbations should confirm the predicted `kd/ke` scaling before the mechanism is treated as established.

### A-P1-1 — evidence record still contains placeholder time

The banked result says `13:1x JST`. An evidence-grade result should contain an exact creation time or explicitly state that time is non-authoritative and point to a signed run manifest.

### Arm gate decision

```text
P-D1 numerical verdict: FAIL(tracking-transient)
P-D1 instrument validity: supported
Substrate/choreography impact: high, provisional until video/Rs review
Production implementation/training: CLOSED
```

## 6. Architectural consequence for WMSO

The arm result is directly relevant to future WMSO data collection:

1. The corrected substrate must be the only substrate used for new WMSO transition data.
2. Old contaminated transition logs need an explicit substrate identifier and must not be pooled silently with clean data.
3. Handoff states must encode grasp/contact stability, not just arm pose; a 1 mrad-scale arm difference can coexist with a discrete chain flip.
4. The first vertical slice should include failure/no-chain outcomes and calibrated uncertainty, not only successful transitions.
5. Do not delay the vertical slice indefinitely for contract perfection: after the bounded D1.1-A fixes above, freeze it and move to tensor binding, artifact manifest, and a 2-3-skill boundary-only experiment.

## 7. Required next sequence

### WMSO

1. Confirm review-4 transcript semantic fidelity in records — this review provides that confirmation.
2. Add the missing pN HOLD artifact.
3. Fix v2.5/EP v1.3 stale references and non-learned TRAINING_PROVENANCE applicability.
4. Complete proof binding/trust boundary.
5. Include semantic schemas in BehaviorSignature.
6. Make handoff references content-addressed.
7. Publish a canonical machine-readable EvidencePolicy object.
8. Bank design/policy/pS record, then pS final delta and pN re-verify on exact hashes.

### Arm

1. Publish one canonical current design/status document.
2. Include the frozen prereg and run evidence manifest.
3. Replace obsolete L-P5/pass-equation text.
4. Remove or operationally define the ramp leg.
5. Finish video human-GT review.
6. Bound the L-P0 claims to the pinned contrast.
7. Run C-1/C-2 only under a new prereg; do not retroactively rescue the failed P-D1 verdict.

## 8. Final status wording

```text
PLAN_STATUS archive bytes: PASS
PLAN_STATUS as-read SHA table: PASS
Operational SSOT: HOLD

WMSO scope: CLOSED
WMSO design: HOLD — v2.6-equivalent cleanup and exact-hash re-review required
WMSO implementation/training/authority: CLOSED

Arm P-D1: COMPLETE; FAIL(tracking-transient)
Arm physical interpretation: PROVISIONAL — video/Rs review pending
Arm production/training: CLOSED
```

## Internal working output

**Verified delta**

- The latest ZIP differs from the preceding ZIP.
- Summary as-read SHA prefixes match the extracted files.
- WMSO working-tree content advanced to design v2.5 and EvidencePolicy v1.3.
- Arm-control content includes the P-D1 result and later design-court disposition.
- The bundled review-v4 transcript is semantically faithful to the earlier chat response.

**Primary blockers**

- Missing pN HOLD artifact and unbanked pS record.
- Non-learned TRAINING_PROVENANCE applicability contradiction.
- Incomplete proof binding and proof-artifact trust boundary.
- BehaviorSignature omission of semantic schemas.
- Ambiguous handoff/schema registry identity.
- Stale arm status and normative probe text.
- Missing self-auditing P-D1 evidence bundle.
