# WMSO D1.1-A contracts_v2 DESIGN v1 — Design-Axis Verify (WMSO-DESIGN / w2:pS)

- reviewer: w2:pS (WMSO-DESIGN, design steward; 0-commit — bank by pQ)
- target: `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md` **v1** (sha256 `8bec472a6ac11656…`, 317 lines, untracked, read in full)
- governing: prereg v3.2.2 (`71097e58102e`, `ea6e39b93c`) — §2 IN / §5b / N-1・N-2 / §10b DC-1..DC-6; charter gates #1/#8/#10
- date: 2026-07-19 09:1x JST
- **verdict: DESIGN PASS-WITH-CONDITIONS — D-1..D-6 fold into DESIGN v1.1 BEFORE CC Debate** (the debate panel must see the corrected design). No scope reopen; no Rs escalation required (all conditions are completions inside already-ruled principles).

---

## 1. Fidelity matrix (pQ mapping claims — all verified on-disk)

| requirement | claimed | verified |
|---|---|---|
| prereg §2 IN 7 items | §1-§7 | ✅ all (types/identity/JCS-minimal/evidence/validator/report-cert/migration/tests) |
| 5b R1 (supersede) | §6 | ✅ hard-deprecate + DeprecationWarning; shim=delegation only; consistent w/ AGENTS.md deprecation-first |
| 5b R2 (no evidence reuse) | §6 | ✅ explicit |
| P1/P2/(a)-(d) | §4 | ✅ non-increasing + ceiling + two-key conjoin (§4.4); proof obligations = (a) MEASURED (§4.3); grades recorded not binary |
| N-1 (table ≠ classification) | §3.1 | ✅ explicit 導出禁止 |
| N-2 (demo_dataset_hash) | §3.1 | ✅ added, new=required / historical=None+UNKNOWN — enforcement gap → **D-2** |
| DC-1 ExecutionBundleHash | §2.2 | ✅ ABSENT sentinel sound (identity SHOULD change when binding lands); double fail-close (identity + profile) — placement gap → **D-1**; action-scale mapping → **N-a** |
| DC-2 cert 拡張+profiles | §4.4/§5.5 | ✅ evidence_bundle_hash/policy_hash/schema_ver; 9-component ClosedLoopProfile matches DC-2 list — min_grade values unstated → **D-3** |
| DC-3 proof obligations | §4.3 | ✅ table matches Rs text; E_PROOF_INSUFFICIENT; downgrade-resubmit OK (monotone) |
| DC-4 isfinite+corpus | §5.1/§7 | ✅ full list incl ttl/p50/p95/std/bounds/norm/scale-bias; corpus has all DC-4 items; known-forbidden vs unknown enum split (E_LINEAGE_FORBIDDEN vs E_ENUM_UNKNOWN) = elegant |
| DC-5 実在限定 | §3.1 | ✅ DAPG rows excluded; enum retained w/ distinct code; **premise verified on-disk by pS**: `wmso/d1/skill_contracts_manifest.json` families = {BC+RL, PPO, SCRIPTED, WAIT}, DAPG appears only inside the `design_ref` file PATH — no DAPG family row. gate#1 structural admit preserved via PPO×RL_ONLY row |
| DC-6 shim | §6 | ✅ |
| JCS minimal | §2.3 | ✅ float-forbidden subset approach is sound — one equivalence caveat → **D-5** |
| 条件付き cell 定義 | §4.4 | ✅ all three defined (acceptance-test-added / non-authority record-compare / diagnostics-only) — discharges my §6#4 fully |
| pN dep condition | §7 | ✅ stdlib-random property tests, no new dependency |

**先祖返り sweep**: P0-1..P0-6 each structurally closed (§1 split / §2.2 context removal / order-preserving tuples + binding deferred / §5 validator + Admissibility-bool abolition / §4 graded / §7 standalone). No v1 pattern reintroduced. **先走り sweep**: no artifact grading asserted, no INSERT classification, closed-loop structurally unsatisfiable pre-B + two-key external, §8 paths "impl GO 時に確定", TransitionRecord = type only. Clean.

---

## 2. Conditions (fold into DESIGN v1.1 before CC Debate)

- **D-1 (MEDIUM — type-model completion; the one substantive finding):** `execution_family`, `training_lineage`, `bc_base_hash`, `bc_config_hash`, `demo_dataset_hash` have **no defined home** in the §1/§2 type model (§3.1's validator table references them; §2.2 ExecutionBundle carries only `training_lineage`). Placement has identity consequences: anything inside ExecutionBundle enters `ExecutionBundleHash` → `SkillActionId`, so a **provenance records-fix (e.g., adding a demo hash to a historical artifact, correcting a mislabeled lineage) would CHANGE action identity and orphan its SDM/dataset rows**. Rs DC-1's own principle is "identity binds to what determines execution". Training lineage/provenance does NOT determine execution. **Required:** define a `TrainingProvenance` (or equiv.) record holding family/lineage/bc hashes/demo_dataset_hash **inside SkillDefinition but outside ExecutionBundle** — pinned by `SkillDefinitionHash`, excluded from `ExecutionBundleHash`/`SkillActionId`; move `training_lineage` OUT of ExecutionBundle; add the `IdentityKind ↔ ExecutionFamily` coherence rule (LEARNED⇔{PPO,BC(,DAPG)}, SCRIPTED⇔SCRIPTED, WAIT⇔WAIT) to §5.2. (Decision owner = pQ; this direction follows DC-1's stated principle — if pQ intends provenance-in-identity instead, that is a deviation from DC-1's rationale and needs Rs.)
- **D-2 (small):** N-2's "新規登録では必須 / 歴史は None 可" is unenforceable by a validator that cannot distinguish new vs historical. Define the discriminator explicitly: e.g. `demo_dataset_absent_reason: Literal["HISTORICAL_PRE_D11"] | None` (None + absent hash on a BC lineage = `E_DEMO_HASH_MISSING`), or state that enforcement lives in the registration procedure with the validator rule spelled out.
- **D-3 (small):** `UsageProfile.min_grade` concrete values are unstated. Tabulate the three profiles' per-component minimum grades, read conservatively off the Rs 確定表 (e.g. CLOSED_LOOP: all required ≥ HASH_BOUND_REPRODUCED; SHADOW(authority-less): ≥ RECONSTRUCTED_COMPATIBLE; OFFLINE_REPLAY: ≥ RECONSTRUCTED_COMPATIBLE, DIMENSION_ONLY = diagnostics-only not replay). Impl must not invent these.
- **D-4 (small):** §5.4 handoff compatibility is cross-definition, but `validate(definition, evidence_bundle)` has no registry input. State the mechanism: a `schema_registry` context param (A-stage tests use fixture registries; full cross-skill compat exercised at `vertical_slice_registry` chunk). Without this the check silently degrades to format-only.
- **D-5 (small, technical):** §2.3's claim "restricted json.dumps == RFC 8785" has one residual divergence: Python `sort_keys` sorts by **code points**, JCS by **UTF-16 code units** — differs for non-BMP keys. Close it by **restricting hash-input object KEYS to ASCII** (canonicalizer asserts; values may stay full Unicode/NFC per §10-2). Cheap and makes the equivalence claim true.
- **D-6 (small; found via pS manifest spot-check):** §6 lacks the **v1 `policy_family` string → (ExecutionFamily, TrainingLineage) migration map**. The live manifest contains `"BC+RL"` — not an ExecutionFamily value. Define the total map ({"BC+RL"→(PPO, BC_THEN_RL), "PPO"→(PPO, <declared v1 provenance>), "SCRIPTED"→(SCRIPTED, NOT_APPLICABLE), "WAIT"→(WAIT, NOT_APPLICABLE)}), unknown strings → `E_MIGRATE_FAMILY_UNKNOWN` (fail-closed). Lineage declarations carried by migration remain declarations — their truth grade stays with the evidence process (N-1).
- **N-a (note):** DC-1's Rs component list includes "action scale"; §2.2 has no such field. Covered transitively (scale/bias ⊂ TensorBindingSpec, D1.1-B) — add one line saying so, so the Rs list is visibly fully mapped.

## 3. Verdict

**PASS-WITH-CONDITIONS.** Architecture, identity system, evidence system, validator, migration, and test plan are faithful to every driving requirement and sound; the six conditions are completions (undefined placements/values/maps), not redesigns — **D-1 is the only one touching the type model's semantics, and it follows Rs DC-1's own principle**. Fold D-1..D-6 (+N-a) → DESIGN v1.1 → pS delta confirm → CC Debate 5体 → pN DESIGN verify (§9 order). Implementation stays CLOSED per header gate.

---

## 4. ADDENDUM — DESIGN v1.1 delta confirm (pS, 2026-07-19 09:2x JST)

Target: DESIGN **v1.1** (same path; sha256 **`b807ce2abbd70b75…`** = my on-disk measurement, == pQ's claim; 374 lines = v1+57). All deltas read on-disk + full-file placement sweep (`training_lineage`/`TrainingProvenance`/`demo_dataset`/`bc_base_hash` grep — no stale placement remains).

| cond | discharged | verified detail |
|---|---|---|
| D-1 | ✅ | `TrainingProvenance` §2.2b (execution_family+lineage+bc/demo fields) placed in SkillDefinition:31, **in DefinitionHash / NOT in BundleHash·ActionId** (formula block updated "training_provenance を含む"); ExecutionBundle field list re-read — lineage REMOVED; placement principle = DC-1 rationale verbatim + orphan-prevention recorded; coherence rule §5.2 `E_KIND_FAMILY_MISMATCH` (LEARNED⇔{PPO,BC(,future DAPG)}) |
| D-2 | ✅ | `demo_dataset_absent_reason` §2.2b + §5.2 rule: BC-lineage ∧ hash=None ∧ reason=None → `E_DEMO_HASH_MISSING`; sole allowed reason `"HISTORICAL_PRE_D11"`, others `E_ENUM_UNKNOWN` |
| D-3 | ✅ | §4.4 table exactly the conservative read-off: REPLAY ≥ RECONSTRUCTED (DIM=diagnostics-only, UNKNOWN 不可) / SHADOW ≥ RECONSTRUCTED / CLOSED_LOOP ≥ HASH_BOUND + acceptance + two-key + safety conjoin |
| D-4 | ✅ | `validate(definition, evidence_bundle, schema_registry)` — registry REQUIRED, silent format-only degradation named as the reason; A-stage fixture registries; full cross-compat at vertical_slice_registry |
| D-5 | ✅ | §2.3 ASCII-key restriction w/ exact divergence rationale (code point vs UTF-16 unit); canonicalizer raises on float/NaN/Inf/non-ASCII key; values full Unicode NFC (§10-2) |
| D-6 | ✅ | §6 total map incl `"BC+RL"→(PPO,BC_THEN_RL)`; `"DAPG"` mapped **totally** with admissibility separated to §3.1 (initially `E_LINEAGE_FORBIDDEN`) — totality vs allowance correctly split; unknown → `E_MIGRATE_FAMILY_UNKNOWN`; `"PPO"→RL_ONLY` conditioned on v1 declared provenance = mechanical mapping, not classification (N-1-compatible) |
| N-a | ✅ | §2.2 note: action scale ⊂ TensorBindingSpec via tensor_binding_hash — Rs DC-1 list fully mapped |

§11 fold table complete & accurate. **Delta confirm = PASS. Design-axis gate for DESIGN v1.1 = CLEAR → CC Debate 5体 GO** (§9 order; my next checkpoints = post-Debate design 修正 delta if any, then pN DESIGN PASS-CLOSE readback).

---

## 5. SUPERSESSION — Rs review-4 = DESIGN HOLD (2026-07-19 09:31 relay; pS ack 09:3x)

**My §4 "gate CLEAR → CC Debate GO" is WITHDRAWN** — Rs review-4 (DESIGN 宛) = HOLD, v1.1 is superseded by a forthcoming **v2 full revision** (P0×6 + P1×4 + metamorphic×10 + open-point promotion). My §1-§4 verdicts remain accurate *for the artifacts they reviewed* but confer **no gate clearance on v2** (R2/C3 discipline: PASS binds only the reviewed sha).

Dispositions of my conditions under review-4 (as relayed; verbatim check at v2 verify):
- **D-1 → CONFIRMED-AND-DEEPENED** (review-4 P0-2): same separation direction, plus `ArtifactSlot KNOWN|EXPLICIT_NONE|UNKNOWN` 3-value + Draft/Certified 2-stage, **no final ActionId while UNKNOWN** — strictly stronger than my binary None/ABSENT treatment.
- **D-5 → SUPERSEDED** (review-4 P0-3): Rs chose full JCS 案A (UTF-16 sort + CanonicalDecimal) over my ASCII-key restriction. My restriction was sound but Rs prefers the complete implementation.
- **pS misses to own (records):** (1) v1 §2.3 **fixed 6-digit decimal** — I passed it without flagging precision loss / representation lock-in; review-4 drops it for CanonicalDecimal. (2) The **ABSENT-vs-UNKNOWN conflation** in ExecutionBundle (None meaning both "known absent" and "not yet known") — review-4's 3-value ArtifactSlot fixes a distinction my review did not surface. Both = paraphrase-level conservatism gaps, same lesson class as §9-R2 of the scope doc.

Next: **v2 一括 verify** (my request to pQ: include a review-4 → v2 fold-map [P0-1..6 / P1-1..4 / metamorphic / promoted opens → §], same auditability pattern as prereg §0b — I do not hold review-4's full text). All prior carries (5b / N-1 / N-2 / DC-1..6 / D-1..D-6 as transformed) roll into the v2 checklist.

---

## 6. ADDENDUM — DESIGN v2 一括 verify (pS, 2026-07-19 09:4x JST)

Target: DESIGN **v2** (same path, sha256 **`4880dc0d6c6dd818…`** = my measurement == pQ claim, 428 lines, read in full).

**Verdict: DESIGN PASS-WITH-CONDITIONS — V-1..V-4 fold → v2.1 → pS delta confirm → CC Debate 5体.** No Rs escalation needed (all four follow already-ruled principles).

### 6.1 Review-4 fidelity — §12 fold-map 13/13 rows, every anchor verified in body
- **P0-1** ✓ §0 two-track + certify_definition/validate_{invocation_start,outcome,handoff} 4 系統 + metamorphic #10 (runtime violation leaves certificate valid).
- **P0-2** ✓ ArtifactSlot 3-value w/ `E_SLOT_INCONSISTENT` state⇔hash coherence; LEARNED forbids EXPLICIT_NONE on binding/normalization (`E_SLOT_FORBIDDEN_NONE`) — sound; Draft/Certified split; **final ActionId only from resolved bundle — v1.1 ABSENT-hash design explicitly retracted with correct rationale** (knowledge gaps must not be burned into identity; certified-only SDM aggregation ⇒ no orphans); NEW `TrainingProvenance.final_artifact_hash` cross-check (`E_PROVENANCE_ARTIFACT_MISMATCH`) closes a v1.1 gap (required-hash rule had no field/check).
- **P0-3** ✓ WCJ: UTF-16 sort via `utf-16-be` encode key = correct technique; lone-surrogate & duplicate-key rejection; JCS escaping; int-only ≤2^53−1; CanonicalDecimal (fixed-6 廃止); NFC as schema precondition; ASCII-key defensive assert (my D-5 correctly subsumed); golden vector 絵文字 vs U+FB33 is well-chosen (U+1F600 → D83D DE00; UTF-16-unit order puts emoji BEFORE U+FB33, code-point order after — pins the divergence).
- **P0-4** ✓ 13 ComponentKind (counted); TRAINING_DATASET replaces the NORMALIZATION-UNKNOWN proxy for demo data (upgrades my N-2); explicit grade ranks; ProofKind ids; 1-claim-per-component + `E_EVIDENCE_DUPLICATE` — which also makes the §4.2 component-sorted bundle hash total (no tie ambiguity; clean interlock w/ metamorphic #8); notes excluded from bundle hash.
- **P0-5** ✓ SkillOutcome.checkpoint_id removed (union-only = type-level dedup); HandoffOffer.compatibility removed (producer self-declared compat eliminated — validate_handoff derives from producer_def × consumer_def × offer) + control_epoch monotonicity + handoff_schema_id/producer_definition_hash added (validate_handoff's needed inputs — coherent).
- **P0-6** ✓ MigrationResult; **"v1 migration main output = Draft" honesty** (v1 lacks runtime_config/control_mode/model_architecture); fixed defaults; D-6 map retained; RESOLVED non-promotion; R2.
- **P1-1..P1-4** ✓ §5D conservative compat rules / ValidationIssue+stable sort / §5C strict codec (no raw json.loads on hash paths) / FreshnessPolicy rename w/ runtime evaluation.
- **T** ✓ mutation-operator method (expected code+path declared; valid→valid excluded) fixes v1's unsound "any 1-field mutation → invalid" — *(pS own, in passing: I passed that v1 claim; underspecified, same paraphrase-gap class as §5's two)*. Metamorphic 10 — each checked consistent with the hash/separation semantics (incl. #4: provenance change → ActionId invariant, DefinitionHash/cert change — correct per §1.3). Seed-fixed generative tests w/ artifact-saved failures. Corpus additions complete.
- **OP** ✓ all three former opens resolved in-body (§2.4 runtime_config normal form / §2-6·7 Unicode / §7 SchemaVersionStamp minimal); §10 = zero.
- **header** ✓ real times, full-64 governing sha, canonical path, commit.

### 6.2 Preservation checks
- §11 map of my D-1..D-6+N-a: **all preserved** (D-1 deepened §1.3 / D-2 §1.3 / D-3 §4.4 unchanged / D-4 §5A SchemaRegistry / D-5 → §2-7 strengthened / D-6 §6 / N-a §1.2) — verified in body, not just the map.
- Prior carries intact: 5b R1·R2 (§6 v1 処遇) / N-1 (§3) / N-2 (§1.3 + TRAINING_DATASET) / DC-1..DC-6 / ceiling+two-key+条件付き cell 定義 (§4.4) / charter gate#1 structural admit via PPO×RL_ONLY (§3) / pN dep condition (stdlib, seed-fixed).
- Regression (P0-1..P0-6 of v1-defect list) closed-and-stronger; 先走り sweep clean (no artifact grading, no INSERT classification, Draft-first honesty, §10 empty).
- Verified consequences (not defects, for awareness): (a) during D1.1-A, LEARNED skills necessarily remain **Draft** (binding UNKNOWN until B) — consistent w/ chunk exit; (b) OFFLINE_REPLAY requiring RUNTIME_CONFIG ≥ RECONSTRUCTED means historical learned skills stay replay-ineligible until config reconstruction — conservative, coherent w/ gate#10.

### 6.3 Conditions (fold into v2.1 before CC Debate)
- **V-1 (small):** CanonicalDecimal regex `-?(0|[1-9][0-9]*)(\.[0-9]*[1-9])?` **permits literal `-0`** while the prose forbids it — add the explicit `-0` rejection to the normal form (regex guard or stated side-condition + corpus case).
- **V-2 (small):** the full **EvidencePolicy table** (13 components × grades × 3 profiles) is deferred to a banked artifact — bind its **bank + pN-verify timing explicitly** (within this design chunk / before impl GO), so impl does not invent policy. Include the SHADOW/OFFLINE required-set detail there.
- **V-3 (MEDIUM — the substantive one):** Draft's UNKNOWN capability is **typed only for the two ArtifactSlot fields**, but §6 requires UNKNOWN for **runtime_config_hash (str) / control_mode (enum, no UNKNOWN member) / model_architecture_hash (str|None)** — the three v1-absent fields have **no UNKNOWN representation**, so the honest "v1 → Draft" outcome is currently untypeable. Extend P0-2's own slot principle to all five identity inputs (e.g., DraftExecutionBundle with tri-state slots for these fields; `str|None` reintroduces exactly the ABSENT/UNKNOWN conflation P0-2 abolished).
- **V-4 (small):** migration disposition of v1's **`Admissibility` 4 bools is unspecified** — state explicit **discard** (conformance/authority are re-derived via certificate + profiles; carrying input bools would resurrect the abolished pattern).

### 6.4 Verdict
Review-4 fold = faithful and complete (13/13 anchored); my conditions and all carries preserved; architecture is materially stronger than v1.1 (3-value slots, two-track validation, WCJ, closed evidence model, honest Draft migration). **V-1..V-4 are completions inside ruled principles — fold → v2.1 → pS delta confirm → CC Debate 5体 → pN DESIGN verify.** Implementation stays CLOSED.

---

## 7. ADDENDUM — DESIGN v2.1 delta confirm (pS, 2026-07-19 09:4x JST)

Target: **v2.1** (same path, sha256 **`c49ff132ff200257…`** = my measurement == pQ claim, 446 lines). All four folds verified in body:

- **V-1** ✅ new regex `(0|-?[1-9][0-9]*)(\.[0-9]*[1-9])?|-0\.[0-9]*[1-9]` — tested against cases: `-0` rejected (neither alternative matches), `-0.5` allowed (2nd alt), `0.5`/`0` allowed, trailing zeros still rejected; corpus `"-0"` case added (§8:410).
- **V-2** ✅ §4.3:240 — EvidencePolicy v1 artifact (full 13×grade ProofPolicy + 3-profile required-set/min_grade incl SHADOW/OFFLINE detail) banked **within the design chunk, before impl GO, in pN DESIGN verify scope**.
- **V-3** ✅ §1.2 — slot principle extended to all 5 identity inputs: `ControlModeSlot` (KNOWN|UNKNOWN; EXPLICIT_NONE forbidden with sound rationale — a control mode always exists), `runtime_config` ArtifactSlot (EXPLICIT_NONE forbidden — config always exists), `executable_artifact_hash` kept required-str with sound floor rationale (v1 always holds it — consistent with migration reality). **Kind-allowance table checked cell-by-cell = sound** (LEARNED: no EXPLICIT_NONE anywhere [P0-2 preserved]; SCRIPTED/WAIT: forced KNOWN control_mode values; runtime_config UNKNOWN allowed for migrated definitions). `resolved()` predicate + "v1→Draft is now typeable" + `E_SLOT_INCONSISTENT`/`E_SLOT_FORBIDDEN_NONE` corpus additions (§8:410).
- **V-4** ✅ §6:339 — 4 bools explicitly discarded with the correct re-derivation rationale, **loud** in MigrationReport (not silent drop).
- §11:428 fold map accurate. Version history line telling (v1→v1.1→v2→v2.1 with all shas + verdict shas) = complete provenance chain.

**Delta confirm = PASS. Design-axis gate for DESIGN v2.1 = CLEAR → CC Debate 5体 GO** (§9 gate order; my next checkpoints = post-Debate delta re-confirm if the debate changes design, EvidencePolicy v1 artifact verify [V-2 scope], then pN DESIGN PASS-CLOSE readback).
