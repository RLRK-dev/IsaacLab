# WMSO D1.1 Scope Prereg — Design-Axis Ratification (WMSO-DESIGN / w2:pS)

- reviewer: **w2:pS = WMSO-DESIGN** (design-content steward; 0-commit — bank by builder pQ)
- request: pQ (RS-TECH-LEAD2) 2026-07-19 07:53 JST — design-axis verify/ratify of the D1.1 scope prereg
- target: `WMSO_D11_CONTRACT_V2_SCOPE_PREREG_RSTECHLEAD2_20260719.md` (sha256 `3eadfc38ca638f4cd0f15038cb430734e7473db44a7a77373c8226a91f51053f`, **DRAFT**, untracked)
- grounding (on-disk, not narrative): charter `WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md` §5:119-130 / §6:135-154 / §8:167-175; Rs verbatim = prereg §0:14-18; LEDGER row 41; D1 design v1 §6/§9 (gate①/exit).
- date: 2026-07-19 08:01 JST | grounding HEAD `11da258f75`
- **verdict: RATIFY-WITH-CONDITIONS** — scope §3 is design-faithful; conditions are pre-registered design-invariants to carry into the `contracts_v2` DESIGN doc, plus one records-provenance gap to close before the D1-exit criterion change is banked (that change is Rs-専権).

---

## 1. Fidelity — §3 scope ↔ charter §5/§6 + Rs directive = **FAITHFUL** ✅

- Rs verbatim (prereg §0:14-16) = continue / D1.1-before-D2 / defer full-9-skill+deep-SDM+realtime+interruption → decision-of-record §1#1-3 + roadmap §4 = accurate, no distortion.
- §3 six Phase-A items map cleanly to the charter:
  - static/runtime split (§3#1: SkillDefinition/Invocation/Outcome/HandoffOffer/TransitionRecord) → charter §2.1 (SDM ← TransitionRecord) / §2.3 (transition mgr ← HandoffOffer).
  - stable action ID (§3#2) + tensor-binding split (§3#3) → fixes P0-2/P0-3 without touching physics control (RS71 §0 non-抵触, prereg §5:89 ✓).
  - validator identity rules "PPO/BC 混在禁止・RL-only base/config null・BC+RL 必須" (§3#5) → **charter gate #1 (algorithm independence)**.
  - evidence grade × usage table (§3#4) → **charter gate #10 (no premature claim)**.
  - real-time deferred to Phase F (§4/§4b) → sequence-faithful (RT0 is later in §5).
- D1.1 is scoped **narrowly to contracts_v2**; vertical slice / D2 dataset / SDM / O0 are correctly deferred to §4. **No scope creep** into the deferred phases (this itself is anti-先走り).

## 2. 先祖返り (regression) watch

- **R1 (must-fix in design doc):** contracts_v2 must **SUPERSEDE**, not coexist with, the flawed v1 types (`contracts.py:475` etc., P0-1..P0-6). If the old mixed static/runtime contract stays importable/usable, the defect regresses via the back door. Design doc must state v1 types are removed / hard-deprecated, not appended.
- **R2 (evidence hygiene):** the D1 impl-leg PASS-CLOSE (`57ed32b27a`, 40P/5S/0F) verified **v1** contracts only. It must **not** be cited as evidence for contracts_v2. contracts_v2 needs its own pN IMPL PASS-CLOSE. prereg §5:91 process (prereg→CONCUR→design→DESIGN PASS→impl→IMPL PASS) already encodes this ✓.
- **R3 (minor wording):** prereg §0:18 "World-Model Skill Orchestration" vs charter §0 "World-Model-**Based** Skill Orchestration". Trivial; keep charter spelling canonical. Name=WMSO / owner=pQ — no regression ✓.

## 3. 先走り (premature-claim) watch

- **P1 (crux):** the grade×usage table (§3#4) MUST be **conservative + monotone**: a lower grade unlocks strictly LESS. *[CORRECTED §8: "strictly LESS" was wrong-as-stated — correct predicate = monotone NON-INCREASING (adjacent grades may share permissions; the Rs table itself has EXACT = HASH_BOUND). pN C2.]* Because exact schema is **unrecoverable**, the historical RL-only exemplar will realistically land at a LOW grade (RECONSTRUCTED_COMPATIBLE / DIMENSION_ONLY / UNKNOWN). The table must forbid a low grade from unlocking `shadow` or `closed_loop` — offline_replay only. Verify the concrete table in the contracts_v2 DESIGN doc.
- **P2:** D1-exit must **record the achieved grade**, never launder it into a binary "RESOLVED". Node state + LEDGER must carry the grade forward so O0/S0/V0 gates see the true epistemic state.
- **P3:** the new INSERT candidate (approach-mode → INSERT exemplar) stays hard-gated on behavioral-equivalence + initiation/termination validity + independent acceptance (Rs §1#5, prereg §6:95). Schema-recoverability alone is insufficient. Keep this gate hard ✓.
- Boundaries (production control / training launch / closed-loop / WMSO inference) all deferred per charter §8-4 ✓.

## 4. §6 charter-judgment — folding grade×usage into the D1-exit criterion

Design-**SOUND** and faithful to charter gate #10 + gate #1, **conditional on**:

- **(a)** grade is **MEASURED** from surviving on-disk schema facts (exact train-time config present? hash-bound reproduced? dimension-only?), **not asserted** (records-must-match-fact; ABSENT-IN-CODE discipline).
- **(b)** grade×usage conservative + monotone (= P1).
- **(c)** D1-exit records grade, no binary collapse (= P2).
- **(d) separate the two axes the current gate① conflates:**
  - **Gate #1 algorithm-independence** = STRUCTURAL: the contract *admits* an RL-only lineage (provable via contract + validator + negative controls, §3#5). This does **NOT** require exact schema recovery of the historical exemplar.
  - **RL-only exemplar PROVENANCE grade** (P0-5) = identity axis, for later O0/S0/V0 use of the *real* skill.
  - Conflating them either over-blocks D1 forever (waiting on unrecoverable schema) or over-claims ("RL-only demonstrated" when only structurally admitted). Separating them lets D1 exit on structural independence + a recorded provenance grade — which is exactly the graded-evidence intent.

Process = **CORRECT**: prereg §6:96 marks the D1-exit criterion change as Rs-専権, PROPOSED pending Rs/pN. **Do not bank the criterion change without Rs ratify + pN.**

## 5. Records-provenance finding (WMSO-DESIGN role)

- prereg §0:14-16 shows Rs verbatim for **continue / D1.1-before-D2 / defer**. It does **not** verbatim-cover the "strict-vs-pragmatic RESOLVED via graded evidence P0-5" ruling — §1#4 states it as Rs's, but no verbatim is quoted.
- This grading ruling is precisely what is being folded into the D1-exit charter criterion. Per CLAUDE.md §15 (records-must-match-fact / human-verbatim before propagation): **cite the Rs verbatim for the grading disposition** (from the full 2026-07-19 written review) into §0/§1#4 **before** banking grade→D1-exit. Non-blocking for the SCOPE itself; blocking for the criterion-change bank.

## Verdict

**RATIFY-WITH-CONDITIONS.** Scope §3 is design-faithful to Rs's directive and charter §5/§6 → OK to proceed to pN SCOPE CONCUR. Carry **R1-R3 / P1-P3 / (a)-(d)** into the `contracts_v2` DESIGN doc. The **D1-exit criterion change (grade×usage) is Rs-専権** — hold for Rs ratify + pN, and close the §5 records-provenance gap first. Lanes unchanged: pQ=impl / **pS=design-ratify (this doc)** / pN=evidence-verify / p6=custody.

---

## 6. ADDENDUM — prereg v2 verification (pS, 2026-07-19 08:0x JST)

Target: prereg **v2** (same path, sha256 `386ad443979e1089…`, on-disk read in full). Claims vs fact:

1. **§5 records gap = CLOSED** ✅ — v2 §0:18-38 quotes Rs verbatim for the P0-5 grading disposition, **including both the 5-grade ladder AND the grade×usage table as Rs's own words**; §0:40-42 adds the INSERT-candidate verbatim.
2. **pS self-correction (records-must-match-fact):** my §5 above and my 08:03 dispatch inferred "ladder+usage table = pQ design (needs my ratify + pN)". That inference is **REFUTED by the v2 verbatim** — ladder + table are **Rs-specified**, not CC-derived. Consequence: provenance is STRONGER than I assumed; my P1 conservativity/monotonicity check applied to the Rs table itself = **SATISFIED** (rows monotone non-increasing; low grades locked out of shadow/closed-loop; even EXACT_TRAIN_TIME closed-loop is only 条件付き可).
3. **R3 fix** ✅ (§0:46 charter spelling). **§5b fold of R1-R3/P1-P3/(a)-(d)** ✅ faithful, no distortion (compared item-by-item against this doc). **Criterion change kept PROPOSED** ✅ (§6:133, §7:142 — no bank before Rs ratify + pN).
4. **New minor design note (non-blocking, → contracts_v2 DESIGN doc):** the Rs table's 「条件付き(可)」 cells need an explicit representation — either a third enum state pointing to the gate that defines the condition (O0/S0/V0 two-key), or an explicit defer. Do not silently collapse 条件付き→可.

**All pS ratify-conditions for the SCOPE stage = discharged.** Remaining holds: D1-exit criterion bank = Rs ratify + pN (unchanged); R1/R2/P1-P3/(a)-(d)/条件付き-representation = carried into the contracts_v2 DESIGN doc review (my next design leg).

---

## 7. ADDENDUM — prereg v3 design re-check (pS, 2026-07-19 08:1x JST)

Target: prereg **v3** (same path, sha256 `56e91818fef4…`, 332 lines, read in full). Trigger = pQ re-check request 08:13 (Rs review-2 = "修正後PASS", mandatory fixes before pN).

**Verdict: RE-CHECK PASS (design axis) + 1 records condition before pN.**

### Design-content findings (all ✅)
1. **Identity 4-way split (§3, Rs #3)** = SOUND. `contract_schema_version` excluded from action identity — serialization v2→v3 no longer mutates `SkillActionId` (removes v2's defect where `contract_version` sat inside the hash). `behavior_revision` in, `entry_mode` string → principled `skill_variant_id`. Two hashes serve distinct surfaces (SDM aggregation vs exact content pin) — no conflation.
2. **§5 lineage split (Rs #5)** corrects a genuine design ERROR in v2's my-ratified text ("PPO/BC 混在禁止" would have outlawed the legal BC→PPO fine-tune). New rules preserve every old invariant (RL_ONLY→bc null / BC_THEN_RL→bc+final-PPO-hash required [stronger] / BC→RL-fields null [new] / skill_id + family↔identity coherence moved to §6). Charter gate #1 mapping + my (d) 2-axis kept (§5:187, §10).
3. **Criterion-change handling = correctly split, NOT premature**: direction (usage matrix = D1.1 milestone Exit 必須) is now **Rs-verbatim-backed** (§0:42-44) and folded at the right level (milestone A+B+C exit, §2:88-95 — matches verbatim "D1.1 Exit"); the **charter-document amendment stays held** for formal Rs ratify + pN (§12). 
4. **New usage table (review-2 確定版, §4)** re-checked: still conservative + monotone (EXACT≥HASH≥RECONSTRUCTED≥DIMENSION≥UNKNOWN; row-wise non-increasing). Delta vs review-1: DIMENSION_ONLY offline 不可→**診断のみ** (Rs-authored widening, bounded to diagnostics — acceptable); conditional cells now *named* (acceptance-test-gated / 非authority / 診断のみ) — partially discharges my §6#4; full definitions still due in DESIGN doc (carried, §4:160 ✓).
5. **Phase E 3-split (E0/E1/E2, Rs #11)** closes a real epistemic hole in v2 (raw factual replay cannot ground counterfactual task-success claims; E1 = OPE/simulator; E2 = shadow no-authority). This is 先走り-prevention encoded into the roadmap.
6. **§6 certificate flow**: fail-closed (no certificate on invalid), timestamps excluded from contract hash (kills nondeterministic-hash defect class), validator pinned by artifact hash. **§7b migration**: no guessing → UNKNOWN, fail-closed, no silent grade promotion — consistent with my (a) MEASURED-not-asserted. **§7c**: standalone/monorepo 二択 escape hatch removed (fixes P0-6 properly).
7. **先祖返り sweep**: review-1 verbatims preserved (§0); review-1 table superseded EXPLICITLY (not silently, §0:36); §10 carries R1-R3/P1-P3/(a)-(d) intact; boundaries intact (implementation NOT_STARTED / L3 / RS71 非抵触 / reward-design at Phase D). Scope narrowing A-only with B/C split is Rs-directed and recorded. JCS kept (§3:116); canonical-JSON全面化 correctly moved to D1.1-C.

### Records condition (REQUIRED before pN dispatch)
- **C-1 fold-map**: v3 anchors Rs #2,#3,#4,#5,#6,#8,#9,#10,#11,#12 visibly; **#1 and #7 have no visible anchor**, and pS does not hold the review-2 full text — so "必須修正 #1-#8 + 重要事項 #9-#12 全 fold" is not independently auditable (independent-confirmation-must-cover-every-conjunct). Fix = add a 12-line fold-map (Rs item # → v3 §) to the prereg (or an appendix). This also pre-empts the same HOLD from pN.

**After C-1: OK to pN SCOPE CONCUR.** My next leg unchanged = contracts_v2 DESIGN doc ratify (§10 invariants + 条件付き-cell definitions + corpus/validator completeness).

### C-1 DISCHARGE CONFIRMED (pS, v3.1 verify, 2026-07-19 08:2x JST)
v3.1 (sha256 `9375d15c157d…`, 351 lines = v3+19, delta confined to header + §0b) read on-disk. §0b fold-map = 12/12 rows with Rs verbatim headings; the two previously-invisible anchors verified in body: **#1** (正式名称) → 冒頭太字定義行 line 12 ✓; **#7** (decision/scope status 分離) → header 3-way status split ✓ (retroactively explains the v3 header restructure). Rows #2-#6/#8-#12 anchor to sections already verified SOUND at v3. Header design-axis line reflects my §7 verdict accurately. **Scope-stage design ratification = fully closed; pN SCOPE CONCUR dispatch (08:18) proceeds on a clean design-axis record.**

---

## 8. ADDENDUM — v3.2 delta re-check (pN SCOPE HOLD C1-C4 fold) + pS self-correction (2026-07-19 08:3x JST)

Target: prereg **v3.2** (same path, sha256 `7ba0ea5c0760…`, 359 lines). Delta enumeration verified: all `pN C1-C4` attributions confined to §4/§5/§9/header/§13 (grep sweep — no stray edits). Design-content deltas = C1/C2; C3 (fail-closed re-verify loop) / C4 (atomic bank + banked-sha readback) = process/records legs, no design-axis objection (C3's "PASS valid only against final design sha" matches my R2 spirit).

### C2 (§4) = CONFIRM + pS self-correction (records-must-match-fact)
- pN's correction of MY P1 phrasing is **factually right and I adopt it**: "低 grade は厳密に少なく unlock (strictly less)" is falsified by the Rs table itself (EXACT_TRAIN_TIME and HASH_BOUND_REPRODUCED rows are identical). Correct predicate = **monotone NON-INCREASING** with adjacent-grade permission ties allowed. My §3 P1 line carries an in-place correction marker; conservativity + monotonicity substance of P1 is unchanged and remains SATISFIED by the Rs table.
- **ceiling-not-authority-grant** + explicit conjoin of O0/S0/V0 two-key + independent-safety gates = SOUND and strengthens the 先走り protection (charter gates #8/#10 aligned). A "可" cell is a necessary-condition ceiling, never a grant — adopted as design invariant.

### C1 (§5 全列挙 fail-close 表) = CONFIRM, with 2 carried design notes (non-blocking)
- Closed enums (PPO|DAPG|BC|SCRIPTED|WAIT × RL_ONLY|BC_ONLY|BC_THEN_RL|NOT_APPLICABLE), 7 allowed rows, everything else fail-close with stable error code, learned⊥NOT_APPLICABLE / non-learned⊥trained-lineage partition, SCRIPTED/WAIT pinned by source-closure with v1's FileNotFoundError fail-closed behavior retained = **SOUND**; closes the v3 fall-through hole (unlisted combos were undefined). Charter §0 provenance kinds (BC / BC+RL / online-RL / DAPG) all covered.
- **N-1 (carried, anti-先走り):** the `DAPG|RL_ONLY (from-scratch)` row is a **structural admissibility rule, NOT a classification verdict** for any historical artifact. In the D1 design-v1 record, DAPG-family artifacts were treated as BC+RL for gate① purposes and the from-scratch insert candidate was an **unverified hypothesis** (pQ handoff 07-19). Classifying that artifact as RL_ONLY for gate① remains an artifact-level evidence question (grade + §12 behavioral gates + Rs/pN), NOT derivable from this table. DESIGN doc must state this so the table is never cited as "our candidate is RL-only ⇒ gate① PASS".
- **N-2 (carried, design question):** for DAPG rows the demo dataset is a training input with **no identity field** (bc_base/bc_config = null on from-scratch): final-artifact hash still pins the artifact uniquely, but demo-lineage provenance is uncaptured (matters for SDM stratification / provenance completeness). DESIGN doc should decide: add `demo_dataset_hash` (or an §4 evidence component for demo data) vs explicitly record as out-of-scope. Either is acceptable; silence is not.

### Verdict
**v3.2 delta re-check = 設計軸 PASS.** C1/C2 folds faithful and sound; my P1 correction owned in-record. **Bank GO (pN C4 procedure):** prereg v3.2 + THIS ratify doc (this version = final readback 版) + LEDGER, explicit-path atomic commit → pN banked-sha readback. N-1/N-2 join §10's carried invariants for the contracts_v2 DESIGN doc review (my next leg). Design authoring / [CHANGE] stays closed until pN banked-sha readback per header gate.
