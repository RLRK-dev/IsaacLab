# Rs 設計承認 packet — Verbal-Teaching Motion Authoring (design)

**For:** Rs (via %12). **From:** VT-DESIGN (w2:p5). **Date:** 2026-07-06. **Status:** L3 chain COMPLETE → **DECIDE = PASS**.
**The ask:** Rs 設計承認 of the design DIRECTION + the staged/gated plan below (paper only; build after W0-e close). Several points are Rs decisions/ratifications (§D).

---

## 1. Design in one paragraph

Make the C1→C2 scripted route **table-driven** so verbal teaching = a table-row edit, mechanically verified. Core finding (validated): the live route's nominal targets are runtime-measured (`caveat-a :3946`), so a static waypoint table can never be byte-identical → rows must carry a **target-SOURCE** (constant/cable-derived/clip-derived). Teaching splits into **class A** (offset, nominal preserved) vs **class B** (base-motion 修正, nominal changes → new RUN1_REFERENCE with Rs as the authorizing key). Staged build, **St1a first (evidence-gated)**; heavier stages deferred. INVARIANTS + the Rs motion-standard are gated at generation time.

## 2. Provenance (the L3 process that hardened this)

| Step | Result | File |
|---|---|---|
| Charter (Rs 承認 07-05) | — | `CHARTER_V1.md` |
| draft v1.0 → %12 review | APPROVE (2 fix + 2 note + 1 nit) | — |
| %10 author-review | CONCUR (fix-⑤ facts §運用28-re-verified; St1a/b ENDORSED) | — |
| v1.2 → **5-body L3 debate** | **FAIL** (1 CRITICAL + 6 HIGH) — caught a 先祖返り CRITICAL + 3 structural mis-framings | `L3_DEBATE_PROPOSE.md`, `L3_DEBATE_DECIDE.md` |
| v1.3 → **targeted re-verify** (RV1+RV2) | FAIL-triggers RESOLVED; **2 new HIGH + 4 MED + 1 LOW** (bounded) | `L3_REVERIFY_RESULT.md` |
| v1.4 (fold 7) → grep-verify | **CLEAN → PASS** | `DESIGN_V1.md` (v1.4) — §9 changelog / §10 re-verify / §11 build-time |

The debate + re-verify (7 independent challenger agents) materially changed the design; the record is in the three files above.

## 3. What survived / what the debate changed (honest)

**Validated:** the byte-id thesis (target-SOURCE required); St1a's env-routing premise (4 params ARE env-read); scope discipline (C1→C2, no full-route over-claim).

**Materially weakened — Rs should note before approving the BUILD:**
- ⚠ **St1a's near-term ROI is ≈0.** Its 4 params (`CLIP2_Y`/`CLIP_X`/`CLIP_Y`/`LIFT_M`) **already have runner env-overrides**, so the DoD-1 examples ("間隔を倍に" etc.) are already one-shot env edits today. **St1a's value is param-address ORGANIZATION (single-home) + the row-diff gate, NOT a new edit capability.** It is **evidence-gated and may HOLD** (D-1).
- ⚠ **St1a cannot mechanically enforce full step-table-first.** At St1a (R3 untouched) the table→run gate sees only `ik_move_both` legs → a moved/added **pin** (INV#5's sole kinematic exception) passes undetected. Full enforcement (grip/settle/pin) needs the St1b runner edit. This limitation is surfaced in §4.4, not hidden.
- The one MEASURED efficiency case (fix-⑤ ~1.5h) is a **new-primitive** change (St2 class), and the scoping says that class is **nearly closed** → St2/St3 are deferred on a measured trigger (≥2 new-primitive needs).

**Net:** the design's durable value is (a) the **param-ownership consolidation** (single-home), (b) the **class-A/B + INVARIANT + Rs-motion-standard governance framework**, (c) the **fix-⑤-as-row thesis** (St2, deferred). The near-term St1a build may not clear its own evidence-gate — and that is stated honestly.

## 4. Rs decision points (§7 of the design)

- **D-1:** St1a near-term (evidence-gated: measured scene/global-edit baseline + discipline-only doesn't already meet ≤1-round-trip; may HOLD); St1b/St2/St3 DEFERRED on measured triggers. **Approve this posture?**
- **D-2:** St3 (b) CODEGEN vs (c) INTERPRETER — deferred to St2 evidence.
- **D-3:** scope = C1→C2 (charter); full-5-clip later, separately validated.
- **D-4:** Rs-LOCK semantics for St3.
- **D-5:** `/web-research` on skill-DSLs before St3? (recommend internal precedent).
- **D-6:** the 3 DoD examples as class-A offsets or class-B base changes (recommend ≥1 each; class-A must use `{F-1b,F-2,F-1a-v1}`, NOT v2/F-3).
- **D-7 (governance, needs Rs ratify):** class-B reference supersession requires **Rs as the authorizing key** + same-turn LEDGER:44 (verbatim-cited); the current V2 freeze is a precedent-with-caveat that v1.4 formalizes.

## 5. Build-time spec items (recorded, not blocking — §11)

- N5: enumerate the EXACT nominal env set for the St1a launch-wrapper byte-id.
- N6: implement the class-B freeze artifact quarantine + Rs-verbatim-cited LEDGER annotation.

## 6. CC1 recommendation

**Approve the FRAMEWORK + governance (class-A/B, INVARIANT gates, D-7 Rs-key, param-ownership single-home) as the design direction.** For the BUILD: adopt the evidence-gate (D-1) — **run the discipline-only baseline (DoD-0) first**; authorize St1a only if it shows a real gap over the existing env-override (it may not, and HOLD is an honest outcome). St1b/St2/St3 remain deferred on measured triggers. Build starts after W0-e close.

*VT-DESIGN (w2:p5) — Rs 設計承認 packet. L3 chain complete; DECIDE = PASS.*
