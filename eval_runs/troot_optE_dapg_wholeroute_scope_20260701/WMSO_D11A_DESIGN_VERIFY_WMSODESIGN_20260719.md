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

---

## 8. ADDENDUM — CC Debate cycle-1 = FAIL; pS misses owned (2026-07-19 10:5x JST)

Debate (5体, task-WMSO-D11A-design-debate-001, `harness-vault/verification-log/verification-log.jsonl`): 46 challenges → **19 union findings (CRIT 1 / HIGH 5 / MED 8 / LOW 4 / note 1), all ACCEPTED by pQ**. Read in full by pS; key items independently re-verified (U4/U8 from in-context doc content; **U3 re-verified on-disk by pS**: manifest rows CLAMP/UNCLAMP/AERIAL_REGRASP have empty identity, 3/9 — the "v1 も必ず保持" premise I endorsed is FALSE). The layered gate worked as designed: the panel caught what my three solo rounds (v1 / v2 / v2.1) did not. **No finding disputed.**

### pS misses owned (records-must-match-fact; each with its lesson)
1. **U8 — I silently disambiguated a malformed test.** v2 metamorphic #4's mutation object ("TrainingProvenance の grade/records") is ill-formed — grades live in EvidenceRecords, not provenance. I picked one reading and certified it "correct per §1.3" (§6.1). Violated my own rule: *don't silently pick one reading of an ambiguous spec — flag it*. (My record was cited in-panel as evidence of the two-oracle divergence.)
2. **U4 — local-cell verification is not cross-surface verification.** I checked the §1.2 kind table "cell-by-cell = sound" (§7) and separately read §6:338 — but never cross-checked them: §6's "UNKNOWN slots for learned/scripted とも" contradicts the table's forced-KNOWN control_mode for SCRIPTED/WAIT. Two locally-sound surfaces, mutually inconsistent — the same class as [[feedback-same-constant-is-not-same-measurement-surface-2026-07-18]].
3. **U2 — my context masked a self-containedness defect.** "§3.1 は v1.1 のまま有効" / "v1.1 から不変" were resolvable *for me* (v1.1 in my context) but dangling for any other reader — v1.1 was destroyed by in-place overwrite; prereg:184 requires the definitions IN the doc. A document must stand alone; context-resident knowledge is not an anchor.
4. **U1 — I over-claimed "Review-4 fidelity … verified".** §6.1's heading asserts fidelity to a source that exists nowhere on disk. What I actually verified = anchor existence + internal coherence. I had flagged the gap (§5) and then accepted the fold-map as sufficient; the panel correctly escalated: **bank the source transcript itself**.
5. **U3 — I endorsed an unverified premise.** "executable_artifact_hash kept required-str … consistent with migration reality (v1 always holds it)" (§7) — I had the manifest open earlier for DC-5 yet never checked identity presence per row. 3/9 rows are identity-less; "v1 全 skill → Draft" was unsatisfiable as written.
6. **U15 — state-level ≠ value-level.** My kind-table check verified allowed slot *states*, not allowed *values*: KNOWN(WAIT) on a LEARNED skill was table-legal nonsense.
7. **U16 — an unrecorded observation is not an anchor.** At v2.1 I noticed regex anchoring was unspecified ("fullmatch assumed — fine at design level") and wrote it nowhere. The panel filed it as LOW. If I see it, I record it.
8. **U6 (adjacent) — "unchanged" claims need column-level diffing.** I passed §3 as "v1.1 のまま" without checking that the prereg's frozen table columns (必須hash/null必須/source-closure) survived the compaction. They didn't.

### Checklist upgrade for v2.2 re-check (standing, added to my method)
(a) cross-surface consistency pass (every rule × every table it touches), (b) document self-containedness pass (no normative reference to destroyed/unbanked versions; grep "のまま/不変/v1.1"), (c) premise verification for every "v1/世界 is X" claim (on-disk, row-level), (d) value-level constraints, not just state-level, (e) claimed-source artifacts must exist on disk before any fidelity PASS, (f) record every observation, however minor. Plus the 19 findings as explicit re-check rows.

Next: pQ = review-4 transcript bank + EvidencePolicy v1 + DESIGN v2.2 → **cycle-2 re-debate → my delta re-check** (order per pQ message 10:44; my re-check follows cycle-2).

---

## 9. ADDENDUM — v2.3 + EvidencePolicy v1.1 全行照合 re-check (pS, 2026-07-19 12:21 JST 実測 — 以後 x-mask 廃止、cycle-2 finding#1 の同族を自分の記録にも適用)

Targets (shas = my measurements == pQ claims, bank `efc355e52d` verified): DESIGN **v2.3** `94a42a0ea73a08d2…` (269 lines, committed-pointer 規約 = U2-sanctioned form, referent `ac5865b66d` blob immutable ✓) + **EvidencePolicy v1.1** `9e4c5019bb1bc6ac…` (84 lines). Both read in full. Method = upgraded 6-pass + explicit row-check of cycle-2 19 items + W-P0-1..4/W-P1-1..6 (all 10 — my 12:0x undercount flag confirmed folded: W-P1-6 = §5B report types + `now` param ✓).

**Verdict: PASS-WITH-CONDITIONS — R-1..R-3 fold → v2.3.1 → pS final confirm → pN DESIGN verify (最終 sha 宛).**

### 9.1 Row-check results (abridged; every row anchored in body)
- **cycle-2 #1..#17**: all dispositioned ✓ — highlights verified: x-mask 廃止 + 実測時刻 (headers); W-copy = byte-identical banked (no fidelity confirm needed — reasonable, file copy > transcription); §6-6 Decimal(repr) algorithm w/ corpus (integral→integer string; exponent window; double-check via CanonicalDecimal form) = sound; EP §4 EXPLICIT_NONE exemption-with-attestation + **UNKNOWN gets no exemption** (知識不足 ≠ 免除) = the crucial asymmetry, correct; per-component semantics + supersession register ④ (prereg §4 rescope recorded); EP §3 3-cell exact 化 (no "or"); §6-4 total symbol disposition incl. dual-canonicalization guard + closure equality invariant + v1-tests-green window; enumerated-only register (5 items); §6-1 fixture-supplementation w/ provenance + E_MIGRATE_STATICS_ABSENT + non-promotion; §2.3 frozenset sorted-array + ≥2-member vector; enum .value=name / .rank split (EP consistent); DC-3 準拠復元 checked against prereg §10b DC-3 text = conformant (not supersession); ownership key-vocab pin + required⊆offered; recovery_rollback_target loud-discard; LOW cluster 11/11 (incl. anchored `re.fullmatch \A…\Z` = my U16 residual closed; #4b hashed-fields + notes row; E_GRADE_INAPPLICABLE S-group extension; BC×BC_ONLY null 列 + E_MIGRATE_BC_CONFIG_UNEXPECTED fail-close mapping).
- **W-P0-1** ✓ §1.3 learned-conditional (Rs の "Alternatively" 分岐を採用 — sanctioned)。**W-P0-2** ✓ §0/§5A profile-neutral + §5A2 split — one residual → R-2. **W-P0-3** ✓ certificate.schema_registry_hash. **W-P0-4** ✓ EP exists/banked/v1.1. **W-P1-1** ✓ two-layer WCJ. **W-P1-2** ✓ evidence-gated EXPLICIT_NONE (E_SLOT_NONE_UNPROVEN; empirical assumption no longer a type invariant)。**W-P1-3** ✓ EP §3b order/dedupe/E_PROOF_CONFLICT — test residual → R-3. **W-P1-4** ✓ EP §4 TP≥2 CL/SHADOW + offline exemption WITH stated rationale. **W-P1-5** ✓ (#4a/4b + C-CH7). **W-P1-6** ✓ typed reports + `now: float`.
- **Cross-surface passes**: §1.3 ↔ §3 rows ✓; §1.2† ↔ EP §4 exemption ✓ coherent (the slot-legalizing evidence IS the attestation); EP profile monotonicity CL⊇SHADOW⊇OFFLINE re-derived from the table ✓ (note: EP v1.1 puts TB/CM in SHADOW ≥2, superseding v2 §4.4 prose — no dangling text remains in v2.3 since §4 defers wholly to EP ✓); Rs 確定表 correspondence (EP:77) ✓; §6-2 "5 slot" wording ↔ §1.2 field count ✓.
- **My 3 pre-announced owns confirmed against the fixes**: W-P0-1 (I praised the unconditional cross-check without checking SCRIPTED/WAIT rows — cross-surface recurrence), W-P1-2 (I endorsed the universal forbid as "sound" — endorsed an empirical assumption as a type invariant), W-P0-3 (my D-4 asked for the registry param but not the certificate binding — the reproducibility hole was my condition's own consequence). All three now fixed in-body.

### 9.2 Conditions (R-1..R-3 — small; fold as v2.3.1, no re-debate needed [debate terminated at max-2; residuals ride the pS→pN chain per §11])
- **R-1 (records):** header line 9 の W-copy sha が 16-hex 省略形 — B-CH5 の自らの規則 (sibling shas = full 64-hex) と不整合 (transcript/EP は full)。bank commit anchor があるため回復可能だが、規則どおり full 化。
- **R-2 (unrecorded deviation — the substantive one):** §5A2 `evaluate_usage_eligibility(definition, evidence_bundle, evidence_policy, profile)` は W-P0-2 の Rs sketch `(certificate, evidence_bundle, evidence_policy, requested_profile, external_gate_state)` から **certificate と external_gate_state を落としている**。分離の本質は達成済みだが、header line 14 の enumerated-only 規律では「未記録の分岐 = 欠陥」— supervening Rs doc の具体 API sketch からの逸脱は **採用するか register に記録**のどちらか。実質面も 2 点: certificate-first は未認証 definition の eligibility 評価を型で防ぐ / external_gate_state は two-key conjoin を prose でなく機械可視にする。推奨 = Rs sketch のパラメータを採用 (certificate 必須入力 + external_gate_state で two-key/acceptance/安全 gate 状態を受けて conjoin を判定に含める) — さもなくば register ⑥ として理由付き記録。
- **R-3 (test):** W-P1-3 が明示要求した **ProofItem 順序 shuffle metamorphic**(bundle hash 不変) が §8 に見当たらない (metamorphic #8 は record 級 shuffle のみ・E_PROOF_CONFLICT は corpus 側)。1 行追加。

### 9.3 Verdict
19+10 全行 disposition 確認・cross-surface/自立性/premise/value/source/記録の 6-pass クリア。R-1..R-3 は completion 級 (R-2 のみ register 規律との整合を要する実質)。**v2.3.1 fold → pS final confirm → pN DESIGN verify (最終 sha)。**残 open = review-4 transcript の Rs 確認 PENDING (v2.3 §10 が正直に保持 ✓)。impl CLOSED 不変。

---

## 10. ADDENDUM — v2.4 + EP v1.2 + Rs review v3 全行照合 (pS, 2026-07-19 13:02 JST 実測)

Targets (bank `130813e934`, all shas = my measurements == pQ claims): DESIGN **v2.4** `772f346c32cf15f1…` (357 lines) + **EP v1.2** `9ef8d558d0ebea44…` + **Rs review v3 byte-copy** `20da075f9566904e…` (318 lines, WMSO §4 = v3 W-P0-1..6 / W-P1-1..3 read in full). Method: exact git diffs `efc355e52d→130813e934` for both artifacts + v3 source read + row-check (R-1..R-3, v3 9 項, cycle-2/W(v2) regression sweep on the delta).

**Verdict: PASS-WITH-CONDITIONS — F-1・F-2 fold (v2.4.1) → pS final confirm → pN DESIGN verify.**

### 10.1 R-1..R-3 = 3/3 DISCHARGED
- **R-1** ✅ W-copy sha full 64-hex (+ v3 copy full-hex from birth).
- **R-2** ✅ **via a better path than my recommendation**: Rs review v3 W-P0-3 sketch (verbatim vs v3 copy lines 112-121 = EXACT: 4 params `certificate / evidence_bundle / current_evidence_policy / usage_profile`; report fields all present + additive `exemptions`; "Acceptance tests, O0/S0/V0 two-key, and safety gates **remain external conjuncts**" quoted) supersedes v2's `external_gate_state` — **register ⑥ records it correctly**. My R-2 recommendation (adopt v2 sketch) is properly outranked by Rs's own later text; both my substantive concerns land: certificate-first = typed ✓, gate conjoin = Rs explicitly wants it OUTSIDE the API ✓ (Rs authority > my preference — correct precedence). `E_CERT_INPUT_MISMATCH` (bundle↔cert hash check) = good fail-close addition.
- **R-3** ✅ metamorphic #9 ProofItem-shuffle (distinct object from #8) + corpus.

### 10.2 v3 W' 9 項 row-check (fold-map §11 vs body vs v3 source)
- **W-P0-1** ✅ EP §3c ApplicabilityResolver = Rs sketch adopted; 3-layer (instance=EXPLICIT_NONE attest / lineage=TD BC-conditional, else OPTIONAL / profile="—" cells); **N/A ≠ UNKNOWN** verbatim honored (N/A = validated absence·集約除外 / UNKNOWN = 失格·免除なし); resolver = typed form of EP §4 exemption (correctly marked non-supersession); N/A-vs-UNKNOWN discriminating corpus case.
- **W-P0-2 / (a)(b)(d) of W-P0-5** ✅ 先行治癒 claims VERIFIED against my own prior reads (schema_registry_hash was in v2.3; REPRODUCED_OUTPUT_HASH@P×HB + COMPATIBILITY_TEST@P×RC present in EP v1.1; E_PROOF_CONFLICT in §3b) — the "先行治癒" labels are true, not narrative.
- **W-P0-3** ✅ verbatim adoption + current-policy semantics (old certificate stays historically valid; stricter current policy → ineligible; corpus case) — one input gap → **F-1**.
- **W-P0-4** ✅ evidence-chain types fully inlined in §4 (+ report types §5A2/§5B) — archive reader needs no git show for the evidence chain. Runtime types stay committed-pointer (sanctioned; not in v3's list).
- **W-P0-5(c)** ✅ replace-vs-supplement cell semantics defined in EP §3 preamble; total-map domain (component, grade, applicability_class) declared; machine-readable via §6 policy_object.
- **W-P0-6** ✅ design side (bank commit + full sha + PENDING kept honest); package side = p6 lane (noted, not folded here — correct lane separation, as is the exclusion of v3 §5 arm-control items).
- **W-P1-1** ✅ §3-3 pins all 6 aspects Rs listed (path normalization / UTF-8-bytes member order / symlink forbidden / bytes-as-committed [= explicit no-line-ending-transform answer] / WCJ keyed-object composition [no delimiter ambiguity] / duplicate-path reject) + golden vector. Sound.
- **W-P1-2** ✅ §3-4 registry invariant chosen (of Rs's two options) with stated rationale (no 5th identity input); `E_BEHAVIOR_REVISION_STALE` compares behavior-bearing hash group at same (skill_id, behavior_revision); corpus case.
- **W-P1-3** ✅ EP §6 two-layer hash (custody doc-sha vs semantic H_WCJ(policy_object) incl. policy_semver); certificate/report bind semantic. → one records gap → **F-2**.
- **Regression sweep (delta-scoped)**: kind table / §1-§2 / §6 / §7 untouched or additive; register grew ⑥ only; EP §4 table unchanged (monotonicity re-holds; "—" cells now named as profile-layer N/A); §10 process 注記 (debate coverage ends at v2.2; v2.3/v2.4 folds ride pS+pN; cycle-3 = Rs discretion — no self-start) = honest 先走り hygiene ✓.

### 10.3 New conditions (fold as v2.4.1 — completions inside v3's own requirements)
- **F-1 (small-medium, cross-surface):** `evaluate_usage_eligibility` **cannot execute the resolver's lineage layer**: the v3-verbatim signature is certificate-first (no definition input), but `ContractCertificate` carries neither `IdentityKind` nor `training_lineage` — so TD's BC-conditional applicability (and kind-dependent rules) are uncomputable from the API's inputs. Fix: add `identity_kind: str` + `training_lineage: str` (`.value` strings, definition-derived at certification) to `ContractCertificate` — making the resolver fully certificate-computable (same completion class as the already-added `explicit_none_components`).
- **F-2 (records, 1 line):** DC-2's literal "evidence_policy_hash" → certificate now binds `evidence_policy_semantic_hash` (v3 W-P1-3 典拠) — record as **register ⑦** (enumerated-only 規律の適用; ④⑥ と同形).

### 10.4 Verdict
R-1..R-3 = discharged; v3 9 項 = faithful fold (先行治癒 claims independently verified); regression = clean. **F-1/F-2 → v2.4.1 → pS final confirm → pN DESIGN verify (最終 sha 宛).** 残 open = review-4 transcript Rs 確認 PENDING のみ。impl CLOSED 不変。

---

## 11. FINAL CONFIRM — DESIGN v2.4.1 (pS, 2026-07-19 13:12 JST 実測)

Target: **v2.4.1** sha256 `8310cb6fd3f8f239…` (359 lines, bank `ba10218549`, EP v1.2 不変 — diffstat で確認)。Exact diff `130813e934→ba10218549` 全読:
- **F-1** ✅ `ContractCertificate` += `identity_kind` (IdentityKind.value, certify 時に definition から抽出) + `training_lineage` (TrainingLineage.value) — rationale コメント正確; §5A2 に「resolver の (kind, lineage) 入力 = certificate fields — definition 実体なしで全 3 層計算可能」明記。私の指定どおり。
- **F-2** ✅ register **⑦** (prereg §10b DC-2「evidence_policy_hash」→ `evidence_policy_semantic_hash` 結合; v3 W-P1-3 典拠; doc sha = custody 層残置)。
- 副作用なし (delta = header records + cert 2 fields + 1 bullet のみ); version 履歴に v2.4 full sha + 私の §10 verdict sha を正確に記録 ✓。

**FINAL CONFIRM = PASS。設計軸は D1.1-A DESIGN v2.4.1 (`8310cb6fd3f8f239…`) + EvidencePolicy v1.2 (`9ef8d558d0ebea44…`) を pN DESIGN verify (最終 sha 宛) へ送る状態にある。** 私の設計軸残タスク = pN verdict readback のみ。residual open = review-4 transcript の Rs 確認 PENDING (fidelity — 設計内容の blocker ではない)。impl は pN DESIGN PASS → pre-check → rule-check → path freeze まで CLOSED 不変。

---

## 12. ADDENDUM — v2.4.1→v2.7.1 全区間 re-check (pS, 2026-07-19 15:52 JST 実測)

⚠ **honest scope**: 私の前 anchor = v2.4.1 (§11)。以後 **pN DESIGN HOLD B1-B7 (v2.5) → RV4 (v2.6) → RV5 (v2.7) → records-only (v2.7.1)** の未検証区間があった。PASS は検証 sha にのみ bind ゆえ、区間全体を照合。⭐**pN が私の FINAL CONFIRM PASS した exact sha (v2.4.1 `8310cb6fd3f8`) に対し B1-B7 の HOLD を出した** — 層状 gate が私の solo 3-round + final の逃した点を捕捉 (debate cycle-1 に続く 2 度目)。

Targets (bank `86d127b5c0`, shas = 実測 == pQ claim): DESIGN **v2.7.1** `64e2b005d6dd7f7a…` (v2.7→v2.7.1 = design body 無変更・transcript fidelity PENDING→CONFIRMED のみ、私が git diff で確認) + EP **v1.5** `6dc3f93b78c9e673…` + JSON fixture `WMSO_EvidencePolicy_v1.5.json` `3b568dcf851feaca…`。EP markdown ↔ JSON = **全 cell 突合で完全一致** (grades/groups/proof_policy 各 grade×component/proof_binding/trust_boundary/applicability_rules/profiles) — W-P0-6 の三面一致要件を満たす (semantic hash は impl golden fixture へ正直に defer)。

### 12.1 fold の忠実性 = B1-B7 + RV4 + RV5 全項 faithful/sound (要点)
- **B2** callable identity 衝突 = §1.2 `callable_selector` を **hash-visible slot 化 (ExecutionBundleHash→ActionId 参加)**・canonical 形式 pin・旧 record-only scripted_callable_ref 廃止 → 衝突除去。✓
- **B3** = §3-4 BehaviorSignature を **補集合定義** (列挙漏れを fail-closed 化、新 field は既定で signature 入り) + semantic schema 2 面追加。✓ (ただし面数 stale = G-2)
- **B4** proof binding = EP §3d に total payload/binding + trust boundary (proof_artifact_resolver)。✓
- **B5** ceiling = **私の lane の見落とし。Rs 確定表 (RECONSTRUCTED closed-loop 不可) を設計内 register ④ で per-component ≥2 に緩めていた** → EP §4 で **全 required ≥3 整列・register ④ 撤回**・「human-ruled ceiling の変更権限は設計内宣言に無い」明記。私が §7/§9 で register ④ を「sound」と通した点を訂正する fix。✓
- **B6** 順序 = EP §3b を単一順序 (kind.value UTF-8 bytes) に固定・旧二義撤回。✓
- **B7** registry = §1.4 **transitive projection** (definition が実参照する schema のみ・全域でない)・content-addressed producer_handoff_schema_hash・E_REGISTRY_DUPLICATE。✓
- **B1** custody/fidelity = pN HOLD transcript bank + **pN 著者 readback CONFIRMED (15:42)**、review-4 transcript = RV5 §7-1 が Rs 確認提供 → **両 transcript fidelity leg CLOSE**。✓
- **RV4/RV5** = TP+2 field (final_training_config_hash/final_source_commit)・TP applicability N/A for SCRIPTED/WAIT・EvidenceEvaluation trust boundary・JSON fixture — §11 W'/RV4 fold-map の全 anchor を body で確認。✓

### 12.2 pS misses owned (pN HOLD; records-must-match-fact)
私が v2.4.1 で PASS した設計に pN が見つけた 7 点のうち、**B5 は完全に私の lane** (Rs 専権 ceiling の設計内緩和 = 先走り抑制の核心を私が見逃した)。B2/B3 = identity 完全性 (value/cross-surface pass)、B4 = proof が「存在」だけで「束縛」を検査しない (structural≠measured)、B6 = 二義順序 (value 級)。§9/§10 の checklist を持ちながら B5 の register ④ を「sound」と通したのは、**「設計内 register は Rs 文言を supersede できる」を無検査で受けた** — 私の R-2 で「enumerated-only register は正当」と判定した延長で、register が human-ruled 面を触る時の権限接地を怠った。→ checklist に (g) **register 項目ごとに「触れる面が human-ruled か」を判定し、human-ruled なら Rs 明示裁定を要求 (設計内宣言で緩めない)** を追加。

### 12.3 findings (機械照合で検出)
- **G-1 (records, W-P0-1 class)**: DESIGN §4 line 239「全表 = EvidencePolicy **v1.4**」← 現 EP + JSON は **v1.5**。stale policy-version pointer = RV5-W-P0-1 が叩いたのと同一 class。→ v1.5 に更新。
- **G-2 (records/test-completeness)**: B3 mutation 面数が §8 corpus:502 と §11 fold-map:532 で「**11 面**」、§3-4 body:193 (正) と RV5 fold:558 で「**13 面**」。impl が §8:502 を読むと mutation case を **RV5-W-P0-4 が要求した semantic schema 2 面ぶん過少 test** する。→ 502/532 を 13 に整合 (または「11 base + 2 = 13」明記)。
- **G-3 (records, small)**: DESIGN header:15 が私の verify 記録を「banked `cd5482310d`」と cite。実際の last bank = `59b7720408` (sha `43ef06ef7f13`)。→ 更新。加えて **本 §12 追記後は私の記録が再び working-tree only** → RV5 §7-8 の順 (design/policy/pS record bank → pS final delta → pN 再 verify) どおり、pN 再 verify 前に pQ が私の記録を再 bank する必要 (custody leg、C-P0-2 の継続)。
- **⭐G-4 (MEDIUM, cross-surface — RV5-W-P0-2 の部分未閉)**: RV5-W-P0-2 の fix (TP→N/A for SCRIPTED/WAIT) は TP を解くが、**SCRIPTED/WAIT は POLICY_ARTIFACT を CLOSED_LOOP で ≥3 に到達できない**。理由 = POLICY_ARTIFACT@HASH_BOUND(≥3) の A群 proof set が **SOURCE_COMMIT・CONFIG_HASH** を要求し、その binding (EP §3d/JSON) は learned 文脈 (final_source_commit / final_training_config_hash) に束縛。scripted は lineage=N/A ゆえ両 field = null → binding 不能 or null 不一致 → scripted POLICY_ARTIFACT は grade 2 (RECONSTRUCTED) が上限 → **CLOSED_LOOP 不可 (SHADOW/OFFLINE 止まり)**。WMSO は「scripted/transition/recovery/wait に依存」(RV5 逐語) ゆえ emergent な cap を放置しない。→ 解 = (a) 非学習 POLICY_ARTIFACT の evidence path を定義 (source-closure 再現ベース、訓練 proof でなく)、**又は** (b) 「D1.1-A では scripted/wait を SHADOW/OFFLINE cap・closed-loop は後段」を**明示** (emergent にしない)。⚠ (b) 意図なら fix 不要・記述のみ = 私は intent 確認を求める (誤 MEDIUM の可能性を明記)。

### 12.4 Verdict
**PASS-WITH-CONDITIONS (v2.7.1 `64e2b005d6dd7f7a` 宛)**。B1-B7/RV4/RV5 fold = 忠実・健全 (特に B5 = 私の lane の見落としを正しく修正)。EP↔JSON = 完全一致。G-1/G-2/G-3 = records・G-4 = cross-surface 実質 (intent 確認で記述解になり得る)。→ **G-1..G-4 fold → v2.7.2 + 私の記録 re-bank → pS final delta → pN 再 verify (最終 sha 宛)**。RV5 §6-5 = 本 bounded fix 後 D1.1-A **freeze → D1.1-B/C + 2-3 skill boundary-only** (Rs 方向) を design header が正しく保持。impl は pN DESIGN PASS まで CLOSED 不変。⭐**私の PASS は pN/panel を代替しない (層の一つ)** — G-4 も pN 再 verify で追加検出があり得る。

---

## 13. FINAL CONFIRM — DESIGN v2.8 + EP v1.6 (pS, 2026-07-19 16:17 JST 実測)

Targets (bank `ba99db30f6`, shas 実測 == pQ claim): DESIGN **v2.8** `24f5fd3d8e8ec850…` / EP **v1.6** `fe3f4f1864d0f00a…` / JSON **v1.6** `WMSO_EvidencePolicy_v1.6.json` (v1.5→v1.6 改名, C-P0-4 filename/内容同期). 私の記録 §12 版 = banked `98e47cace83a` (G-3 record re-bank, HEAD blob 一致確認).

**G-1..G-4 = 4/4 discharged (git diff v2.7.1→v2.8 + on-disk 照合):**
- **G-1** ✅ DESIGN §4:239 EP版 → **v1.6** + 恒久規則「本行の版数は EP header と同期更新」(再発防止 = RV5-W-P0-1 class の構造的 close).
- **G-2** ✅ §8:502 / §11:532 の「11 面」→ **13 面** (body §3-4 と整合; §567 fold-map が declare). 残る「11 面」2 件 = 193 (旧状態の historical 記述) / 567 (fix 記述) のみ — stale でない.
- **G-3** ✅ header:15 = 「最終 bank = 本 v2.8 commit〔§12 込み〕; 以後 pS addendum 毎に re-bank」(cite 訂正 + 恒久 custody 規則).
- **G-4** ✅ **実欠陥として正しく根治**: EP §3d + JSON proof_binding とも SOURCE_COMMIT/CONFIG_HASH を **kind 条件化** (learned=final_source_commit/stage-config / SCRIPTED-WAIT=closure source commit/runtime_config slot hash) — **EP markdown ↔ JSON 完全一致** (両 binding 逐語対応, semver 1.6.0, source_markdown v1.6). **完全性検証**: scripted CLOSED_LOOP 必須全 component (POLICY_ARTIFACT/OBS/ACT/CONTROL_MODE/RUNTIME_CONFIG/INITIATION/TERMINATION/HANDOFF) の HB(3) 阻害は learned-only 束縛の SOURCE_COMMIT・CONFIG_HASH の 2 点のみ → 両 kind 条件化で包括解消 (spot-patch でない). EXACT(4) は TRAIN_RUN_MANIFEST/TTCB が訓練実体要求 → scripted 不能維持・かつ Rs 確定表で EXACT と HB は同一 closed-loop row ゆえ機能欠損なし (pQ の ceiling-row 論拠を確認). learned 束縛不変・corpus に交差汚染 guard (learned に closure-commit → E_PROOF_MISBOUND) + scripted EXACT→E_PROOF_INSUFFICIENT (期待). intent = (a) 非学習 evidence path 採用 (SHADOW cap でない) = WMSO の scripted/transition/recovery/wait 依存に整合.

**FINAL CONFIRM = PASS。設計軸は D1.1-A DESIGN v2.8 (`24f5fd3d8e8ec850`) + EP v1.6 (`fe3f4f1864d0f00a`) + JSON v1.6 (`e1f8d300dc206ac3`) を pN 再 verify (最終 sha 宛) へ送る状態。** ⚠ **本 §13 追記で私の記録が再び working-only** → G-3 の恒久規則どおり pN 再 verify 前に pQ が同 commit で re-bank 要 (RV5 §7-8 順)。私の設計軸残 = pN 再 verdict readback のみ。impl は pN DESIGN PASS → pre-check → rule-check → path freeze まで CLOSED 不変。⭐私の FINAL CONFIRM は pN 再 verify を代替しない (層の一つ)。B1-B7 の前例どおり pN が追加検出する可能性は残る。

---

## 14. ADDENDUM — v2.8→v2.9 re-check (RV6 + pN HOLD C1-C3) (pS, 2026-07-19 17:14 JST 実測)

⚠ honest scope: anchor = v2.8 (§13 FINAL CONFIRM PASS)。区間 = **pN 再 verify ⛔HOLD C1-C3 (v2.8 宛・16:26 — 私の PASS 後 3 度目の層状捕捉) + RV6 (7 領域 P0-1..P0-6 + custody)**。C ⊂ RV6 と同根。Rs RV6 §10 逐語「これ以上一般精緻化せず、証拠束縛/handoff/migration の閉包だけ直して **freeze**」= 終盤。

Targets (bank `8caa19a7a4`, shas 実測==pQ claim): DESIGN **v2.9** `e64c192b62e754da…` / EP **v1.7** `586fec2a770207b5…` / JSON **v1.7** `WMSO_EvidencePolicy_v1.7.json`. ⚠版名 collision (Rs RV6 §10 が「v2.8/EP v1.6」命名、当該ラベルは pS-G fold が消費済 → 実版 v2.9/v1.7) = design header に loud 記録済 ✓。

### 14.0 ⭐pS §13 の miss owned (3 度目・直接的)
§13 で「scripted schema/spec が HB(3) 到達 ✓・包括解消 (spot-patch でない)」と**断言**したが、pN C1 / RV6 P0-2 が**同領域のより深い欠陥**を捕捉: S 系 component の HB は `REPRODUCED_OUTPUT_HASH == FINAL_ARTIFACT_HASH` を要求するが S cell に FINAL_ARTIFACT_HASH が無く **REPRODUCED の target が未定義**。私は SOURCE_COMMIT/CONFIG_HASH の providability は確認したが **REPRODUCED の target 存在を確認せず「包括」と over-claim**。→ checklist に (h) **組合せ空間 (component×grade×kind) の「包括/完全/comprehensive」を subset 検査から主張しない — 検査した leg を列挙し未検査を明示**。§13 の「包括」表現が正にこの overreach。

### 14.1 RV6 P0-1..P0-6 + pN C1-C3 = 全 fold faithful/sound
- **P0-1 (semantic hash 二重定義) = ⭐AIRTIGHT**: JSON 二層 {metadata, policy_definition}・hash=H_WCJ(policy_definition)・**EP §6 markdown ↔ JSON の policy_definition = 16 member 完全一致**・metadata 除外。⭐**pinned hash を私が独立再計算 = `066eed1049f4f51a89dd86e9d50614a65adba070b2ff650424ea7cef05dec4ea` 完全一致** (JSON metadata 埋込 command 実行、この chain で初の claimed-hash 実測成功 = records-vs-fact 満点)。
- **P0-2 (S/spec HB の reproduced target 不在 = 私の §13 miss) = claim_target 機構**: EvidenceRecord.artifact_hash→claim_target_hash 改名・全 13 component 導出表 (EP §3d ↔ JSON claim_targets 一致)・REPRODUCED==claim_target で S 系も成立・TTCB/manifest も claim_target 一般化。scripted 全 required (POLICY_ARTIFACT/OBS/ACT/CONTROL_MODE/RUNTIME_CONFIG/INIT/TERM/HANDOFF) の HB 到達を再検証 = 成立 ✓。
- **P0-3 (scripted binding) = ExecutionProvenance 型 (§1.3b)**: SCRIPTED/WAIT 必須・LEARNED None 必須 (E_EXECUTION_PROVENANCE_KIND_MISMATCH)・binding が typed field (source_commit/runtime_config_hash) 参照・coherence 2 本。私の G-4 kind 条件を typed record へ昇格。
- **P0-4 (evaluator trust) = evaluator_registry**: certify 入力 + certificate.evaluator_registry_hash + membership E_EVALUATOR_UNKNOWN (EP↔JSON 一致)。
- **P0-5 (handoff identity/epoch) = validate_handoff に 5 producer 検査** (action_id/definition_hash==invocation==H_WCJ(producer)/schema_id∈producer/producer_handoff_schema_hash) + **epoch 二層分離** (validator=等値のみ / authority manager O0=CAS・発行・stale/used-offer 拒否 via handoff_offer_id)。
- **P0-6 (migration UNKNOWN 型不能) = 保守案** (§1.3b/line143: fixture 供給→Draft / 不能→E_MIGRATE_STATICS_ABSENT・UNKNOWN 分岐撤回)。⚠ **line 398 に未伝播 = H-1**。
- **resolver 分割** (resolve_artifact / resolve_git_commit for SOURCE_COMMIT) ✓ / **C1-C3 = RV6 P0 と同根で同時解消** (C1=claim_target/C2=hash 実算出/C3=型 inline)。

### 14.2 conditions (within Rs-named closure — 一般精緻化でない)
- **H-1 (must-fix, records/cross-surface — P0-6 closure 内)**: DESIGN line 398 migration 表が「producer_handoff_schema_hash は … **or UNKNOWN→Draft**〔RV4 §2.6〕; 不足情報は **UNKNOWN 扱い**」を残し、**P0-6 修正の line 143「UNKNOWN 分岐は型に存在しないため撤回・供給不能→E_MIGRATE_STATICS_ABSENT」と直接矛盾**。型定義に適用済みの P0-6 fix が migration 表に未伝播 → line 398 を保守案に整合 (UNKNOWN→Draft 削除)。RV6 P0-6 が叩いた「UNKNOWN handoff-schema hash 型不能」がこの 1 行に残存。
- **H-3 (custody, records)**: pN C1-C3 の as-received transcript が未 bank (B1-B7 は bank 済)。design line 16 が「次 round で pN v2.9 verdict と併せ確定」と defer。→ C→fold-map が現状 banked pN source に対し独立検証不能 (RV5 C-P0-1 と同型)。pN v2.9 再 verdict と併せ as-received bank 要 (pQ deferral は defensible だが open leg として記録)。
- **H-2 (minor, records)**: RV6 §7-7「JSON file 自身の sha を header に」は semantic definition_hash 掲載のみで **JSON file の sha256 は manifest+bank commit へ defer**。file は commit で pin 済ゆえ実害小だが、§7-7 逐語は file sha inline → inline するか manifest 委譲を §7-7 充足と明記。

### 14.3 Verdict
**PASS-WITH-CONDITIONS (v2.9 `e64c192b62e754da` 宛)**。RV6 6 P0 + C1-C3 fold = 忠実・健全 (P0-1 = hash 実測で airtight・P0-2 = 私の §13 miss を根治する claim_target)。H-1 = P0-6 closure の 1 行未閉 (must-fix records)・H-3 = C custody・H-2 = minor。→ H-1..H-3 fold → v2.9.1 + 私記録 re-bank → pS final delta → **pN 再 verify (最終 sha 宛) → PASS なら D1.1-A freeze** (RV5 §6-5 / RV6 §9)。⭐私の PASS は pN 再 verify を代替しない — **B1-B7・C1-C3 の前例 (2 度)** どおり追加検出があり得る。impl は最終 PASS-CLOSE まで CLOSED 不変。

---

## 15. CLOSURE — design-axis chain complete; evidence-axis PASS-CLOSE relayed (pS, 2026-07-19 17:50 JST 実測)

**確定 (on-disk 実測):**
- 現行版 = DESIGN **v2.9.2** `e83a29061400b42c…`（bank `ba69702cb9`、EP v1.7.1 同時）。
- pN v2.9.1 = ⛔**HOLD R1-R3**（17:30、記録: version 履歴）— 内容 = records/completeness（EP 旧重複行統一 / enum member 全数 inline / 版数 3 面同期）= 非設計実質。→ v2.9.2 に fold。
- **design-axis chain (私の §1-§14) = 完走**。全 supervening review (RV3-RV6 + W-review v2) + pN 4 verdict (B1-B7 / C1-C3 / R1-R3) + CC Debate 2 cycle を fold し、私の各 verdict が bank 済。

**⚠ relayed (未 on-disk・記録すべき custody):**
- **pN evidence-axis PASS-CLOSE (17:43) = pQ relay** — 私は v2.9.2 が pN review 対象版であることは実測できるが、**PASS-CLOSE verdict 自体の as-received transcript は未 bank**（R1-R3 HOLD も同）。⭐この chain の規律 = pN verdict を as-received bank（RV5 C-P0-1 が「pN HOLD record 不在」を CRITICAL 化・B1-B7/C1-C3 は transcript bank 済）。**終端 PASS-CLOSE = 最重要 verdict** ゆえ、freeze 上程と併せ **pN R1-R3 + PASS-CLOSE の as-received transcript を bank 要**（terminal verdict の独立監査可能化）。私は本 §15 で「PASS-CLOSE = pN 発・pQ relay」とタグ付けし、on-disk 確認済とは記さない（an-absence/verdict-claim must be read not relayed）。
- **design header status が stale**: 「HOLD R1-R3 / freeze PENDING」のまま（v2.9.2 は 17:35 bank・PASS-CLOSE は 17:43 後）。Rs freeze 裁定時に PASS-CLOSE/frozen へ更新要。

**境界 (over-claim 防止):**
- 本 PASS-CLOSE = **DESIGN evidence-axis** の判定。**freeze = Rs 専権**（上程中）。**training-ready ではない** — WMSO charter §0/§8-4 どおり production control / training launch / closed-loop authority は本 gate で未承認。D1.1-A freeze → D1.1-B（tensor binding）/ D1.1-C（artifact manifest）+ 2-3 skill boundary-only（RV5 §6-5 / RV6 §9）。impl は path freeze まで CLOSED 不変。

**pS 自己記録 (chain 全体で own した 3 miss — 層状 gate が私の PASS 後に捕捉):**
1. **register-④ / B5**（pN HOLD B1-B7）: Rs 確定 ceiling を設計内 register で緩めた案を「sound」と通した = 先走り抑制の核心を見逃し → checklist (g) register が human-ruled 面を触るなら Rs 裁定要求。
2. **§13「scripted schema/spec HB 包括解消」over-claim**（pN HOLD C1-C3 / RV6 P0-2）: subset 検査から組合せ空間の完全性を主張 → checklist (h) 「包括/完全」を subset から主張しない・検査 leg 列挙。
3. **pattern**: 私の design-axis PASS は 3 度 pN/panel に上書きされた。**私の PASS は層の一つで pN を代替しない** — 恒久記録。

design-axis 役割 = 本 §15 で closure。freeze 裁定 (Rs) + 上記 custody bank 待ち。

---

## 16. RV7 re-verify — Rs review v7 ⛔HOLD fold (v2.9.2→v2.10) design-axis PASS (pS, 2026-07-19 20:54 JST 実測)

**§15 closure の再開**: pN evidence-axis PASS-CLOSE (17:43) 後、**Rs review v7 = ⛔HOLD**（freeze 差し戻し、対象 = v2.9.2 + 旧 zip 世代 companion）。§15 で「freeze 待ち」とした chain が Rs HOLD で再開。RV7 = 規範ブロッカー P0-1..P0-7 + 記録 R-1..R-4 + custody（提示 bundle が exact-pin 不成立）+ 工程 1-14。pQ fold → **DESIGN v2.10 / EP v1.8 / JSON v1.8**（bank `a87525cc15`）。本 §16 = **工程 12（pS 差分照合）**。

**pin 実測一致（records-must-match-fact — 全 4）**: DESIGN `86a882219780dc43…` / EP md `9713cafbd2919c5d…` / JSON v1.8 `00032f90916b56ab…` / RV7 transcript `91923be57c206eaa…`。bank `a87525cc15`（4 file）・prior v2.9.2 = `ba69702cb9`・4 file tree clean（committed==worktree、pin==worktree）。

**RV7 11 項 per-item 照合（v2.9.2→v2.10 diff + EP v1.7.1→v1.8 + JSON parity）:**

| 項 | Rs 要求 | fold（実測） | 判定 |
|---|---|---|---|
| P0-1 | EP 実体不在・v1.7 重複規則 | semantic = v1.7.1 で先行修正（REPRODUCED/TTCB → 単一 claim_target anchor・重複 0、grep 確認）; custody = 実 v1.8 bytes + manifest bank | ✅ semantic 閉／custody=pN leg |
| P0-2 | resolver 5 引数 + 優先順位 instance→profile→lineage→default | EP §3c `resolve_applicability(...)` + 設計 §4 mirror + JSON `applicability_rules` order 1-4 一致 + regression_vector 埋込 + register ⑨ | ✅ md↔JSON airtight |
| P0-3 | projection 確定形 + slot state/tuple 順/accepted/空/golden | EP §3d + JSON `projection_rules`（member 16→17）: control_mode={state,value}(KNOWN) / handoff={handoff_schema,accepted_handoff}・宣言順保持・空=[] / golden 2 本掲載 | ✅ golden 2 本独立再計算一致 |
| P0-4 | CONFIG_HASH stage 入力不在 → total map | (identity_kind,training_lineage,component) 全域 map・**JSON `stage` 0 件**（判別子撤去）・EvidenceRecord 不変 | ✅（Rs 2 案中 total map 採用） |
| P0-5 | validate_handoff に epoch snapshot | `validate_handoff(...,authority_epoch_snapshot:int)` + `E_HANDOFF_EPOCH_STALE` + manager 責務に snapshot 読出し | ✅ |
| P0-6 | evaluation cert を certify/certificate/eligibility へ接続 | `DefinitionCertificationResult.evidence_evaluations` + `ContractCertificate.evidence_evaluation_bundle_hash` + eligibility 第2引数 evidence_bundle→evidence_evaluations(assigned_grade) + `E_GRADE_MISMATCH` + register ⑧ | ✅ |
| P0-7 | IdentityKind inline | §1.2 `class IdentityKind(Enum)` + §1.4 enum inventory 収載 | ✅ |
| R-1 | v1.6 現行参照 | §4 冒頭表・§8 三面一致 fixture 共に v1.8；全文 grep = 現行規則 0（残存は履歴/fold-map/退役 pin 注記のみ） | ✅ 完全 |
| R-2 | mutation test 旧 field 名 | §8 #4b = {grade, source_ref, proof, claim_target_hash, evaluator_artifact_hash} | ✅ |
| R-3 | manifest 全面旧版 | manifest 全面書換 + 別 commit **`1ba0d0a9df`** で bank（v2.10/v1.8/bdc508 pin + pS/pN record + v2.9.2 SUPERSEDED copy + pN R+PASS-CLOSE transcript `2847e2aa9d30…`） | ✅ |
| R-4 | JSON 型記述（bool 欠落） | metadata = 「ASCII key/str・int・bool のみ・float/null/非 ASCII なし」 | ✅ 機械検証済 |

**hash 3 本 独立再計算 = 全一致（airtight）:**
- `evidence_policy_definition_hash` = `bdc508200889005142eaab5ac15c48cdfb8281df63bbb35537542f1f248891a8`（JSON metadata 埋込 command 実行）
- control_mode golden = `4f0b26d50ca9def398021dc39027cd4aaeabde2440cb83a12360191134b6a01c`
- handoff_schema golden = `00ffb0154ddb241a4bf5f3b49e362cae02013338c051f7b9206c7c8cedfb602d`（+ canonical round-trip 一致 = 掲載文字列が実正準・実装再正準化で同一 bytes）

**先祖返り / 先走り / over-reach 抑制（pS duty）:**
- register ⑧⑨ = 旧 Rs sketch（RV3-W-P0-3 / RV3-W-P0-1）を **後発 Rs review text（RV7 P0-6 / P0-2）が supersede** = human-ruled 面を Rs 自身の text で変更 = **checklist (g) 充足**（設計内宣言でない）。
- §10 の無条件「open=0」= **撤回**（自己申告 fold を「open 0」と書かず、残 gate = pS→pN→Rs freeze を明記）= RV7 末尾指摘に忠実・**先走り抑制**。
- FOUNDATIONAL invariant（RS71 §0 DUAL-ARM/88mm/DiffIK/コ/no-trick）**不抵触**。ControlMode enum = {DIFF_IK_EE_TARGET, SCRIPTED_SEQUENCE, WAIT}（kinematic mode 無し）; DESIGN 唯一の kinematic 言及 = 除去 directive 写像（line 563・契約層で DiffIK-only 執行・v1 kinematic 期 executable は Draft/evidence 化して実行候補から除外）; EP md kinematic 0 件 → **Rs 最上位原則「sim is reality / kinematic 完全削除」と整合・先祖返り無し**。
- 退役 pin `066e…`/`ed10…` = 正しく退役表記（再利用無し）; register ④（B5 撤回）維持。

**§15 custody 2 懸念の discharge（RV7 round で解消）:** (1) pN R1-R3 + 終端 PASS-CLOSE の as-received transcript = **bank 済** `2847e2aa9d30a9b5…`（manifest 記載）→ §15 の「terminal verdict 独立監査不能」concern 解消。(2) design header stale = v2.10 で現行 gate state（pS 差分照合→pN exact-pin 再検証→Rs freeze）へ更新済。

### 16.1 Verdict
**design-axis PASS（DESIGN v2.10 `86a882219780dc43…` 宛）。** RV7 11 項 = 忠実・完全 fold、hash 3 本 airtight、md↔JSON parity 成立、規範/records 全閉、regression/over-reach 無し、FOUNDATIONAL invariant 不抵触。**PASS-WITH-CONDITIONS でない = must-fix 検出 0**（H/G/F/R 系のような未閉 leg なし）。

**境界（私の PASS の scope — over-claim 防止）:**
- **exact-pin / custody 閉包 = pN の leg（工程 13）**。RV7 HOLD の中核（提示 bundle が旧 zip 世代 → exact-pin 不成立）は本 round の実 v1.8 bytes + manifest bank で解消される見込みだが、最終確認は **pN exact-pin 再検証**が担う。私の design-axis PASS は fold 忠実性 + hash 内部整合の確認で、pN custody leg を**代替しない**（standing: 私の PASS は層の一つ・過去 3 度上書きされた）。
- **⚠ pN へ渡す最終 bundle は manifest commit `1ba0d0a9df` を必ず含めること（custody 完全性 — RV7 教訓の再発防止）**。fold = `a87525cc15`・manifest（R-3 deliverable, 全 pin）= 別 commit `1ba0d0a9df`。pQ dispatch は前者のみ pin。RV7 HOLD を招いた「companion pointer 欠落の bundle 納品 gap」を再発させぬよう、工程 13 で pN へ渡す SHA set は DESIGN/EP/JSON + **manifest** の完全 bundle とする。
- **RV7 transcript fidelity = Rs 確認 PENDING**（chat 原文・byte identity N/A — 従前 transcript と同類・doc に明記）。
- **freeze = Rs 専権（工程 14）**。**training-ready でない** — production control / training launch / closed-loop authority は WMSO charter §0/§8-4 で CLOSED 不変。

**minor（非 must-fix・記録のみ）**: design header line 24 の pS-record bank pointer が「最終 bank = 本 v2.8 commit」と旧表記（実 record sha は manifest が `7a212b9374e3…` で正しく pin）。cosmetic + manifest-authoritative ゆえ本 PASS を gate しない。次 re-bank 時に header 同期すれば足る（churn 回避のため単独 fix 不要）。

→ **工程 12 完了。pQ は工程 13（最終 SHA のみ pN へ・manifest 込み完全 bundle）へ進める。**
