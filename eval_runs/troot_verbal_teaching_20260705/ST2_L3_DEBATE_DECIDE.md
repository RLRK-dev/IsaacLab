# St2 Build Spec — L3 5-body [VERIFY] debate — DECIDE (VT-DESIGN / CC1 lead)

**Subject:** `ST2_BUILD_SPEC.md` v0.2. **Format:** §運用2 [VERIFY] / §運用15. **Date:** 2026-07-06.
**Panel:** CC2 byte-id · CC3 INVARIANTS/Rs-LOCK · CC4 branch-completeness · CC5 grounding · CC6 NHA. **Lead:** CC1 (VT-DESIGN/p5).
**Provenance:** v0.1 → v0.1a (self-review) → v0.1b (%12 Q1/Q2) → v0.2 (%10 CONCUR/1 MEDIUM) → this debate.
**Baseline:** runner @`6808964dc3` (== working tree; CC5 re-confirmed byte-identical).

## Panel tallies

| Agent | CRIT | HIGH | MED | LOW | verdict |
|---|---|---|---|---|---|
| CC2 byte-id | 0 | 1 | 3 | 2 | Q1 (snap-down offset-gated) VERIFIED CORRECT |
| CC3 INVARIANTS/Rs-LOCK | 0 | 2 | 2 | 0 | Q2 governance correct; no raw INVARIANT-field leak |
| CC4 branch-completeness | 0 | 0 | 2 | 1 | **② F-1a fold CLEARED (leaf-complete, correct)**; k/N normalization sound |
| CC5 grounding | 0 | 0 | 1 | 2 | 33/36 cites EXACT; baseline re-confirmed |
| CC6 NHA | 0 | — | — | — | **NULL_HYPOTHESIS = HOLD (build-defer)** |
| **unique** | **0** | **3** | **~7** | **~5** | |

**Core VALIDATED (no defect — the panel confirmed these sound):** Q1 (snap-down offset-gated → `RUN1_REFERENCE_V2 5f1c3f92` nominal EXACT, CC2); the **② F-1a leaf-complete branch fold is CORRECT** (CC4 re-read `:4224-4321`, no hidden 3rd leaf); Q2 staging governance (both A/B, Rs-decision, %12-lean-labeled — no CC leak, CC3); no raw INVARIANT-field leak, 88-span held by construction `:4666` (CC3); 33/36 runner cites EXACT (CC5); k/N ordered-multiset normalization sound (CC4). **The design DIRECTION holds; the defects are fixable.**

## REBUT_OR_ACCEPT (CC1)

| # | Finding | Agent(s) | Sev | Verdict | Fix (→ v0.3) |
|---|---|---|---|---|---|
| 1 | **§2.1 blanket "every derived source is offset-gated → collapses to constant on nominal" is FALSE for DS1(caveat-a `:3942-3948`) + DS4(argmin `:4665`)** — they run UNCONDITIONALLY; byte-id by DETERMINISTIC reproduction (fixed seed+settle), not offset-collapse. **Regresses the CC2-VERIFIED fact in DESIGN_V1 §2.2:58**; would FAIL byte-id DoD if DS1 built per gate=offset | CC2 | **HIGH** | **ACCEPT** | two-mechanism byte-id taxonomy: (a) offset-gated-SKIP {DS2,DS3,F-1b} vs (b) always-run-DETERMINISM {DS1,DS4}; set DS1 `gate=always`, DS4 `gate=phase/clip-seat`; state the determinism premise (fixed seed `:355-356` + settle) as their byte-id basis |
| 2 | **DS4 has TWO Rs-LOCKs, not one** — beyond argmin-position (`:4662`), a 2nd on ORIENTATION (`:4678-4681` `C2_TILT_SIGN=0` square-on, "do NOT revert to tilt"); DS4 inv_binding omits it, and DESIGN_V1 §3.1 exposes `orientation`=tilt-follow with NO gate → teachable 先祖返り | CC3 | **HIGH** | **ACCEPT** | add `C2_TILT_SIGN=0` to DS4 inv_binding; **governance-escalate** (not silent-edit) that DESIGN_V1 §3.1's Rs-approved orientation row needs the same inv_binding for the C2_REGRASP arm → `BLOCKED_FOR_USER`/Rs |
| 3 | **DS4 Rs-LOCK breakable without tripping a gate** — editing `reduce` argmin→mean is PERMITTED by §2.3 teachable-set AND not caught by §2.2 "pin-to-constant" (stays "derived"), yet re-introduces the air-grip bug `:4633-4635`. Tripwire is the wrong predicate | CC3 | **HIGH** | **ACCEPT** | per-DS **Rs-LOCKED derivation fields IMMUTABLE** — DS4 `{reduce=argmin, target=c2y+GHS}` removed from the teachable within-branch set; §2.3 carves out per-DS Rs-LOCK fields; reword inv_binding "reduce=argmin over ACTUAL cable, IMMUTABLE" |
| 4 | **§3.1 "DS1-DS4 are ik_move_both legs" is FALSE** — only DS3 emits legs; DS1/DS2/DS4 are VALUE-derivations (emit ∅ legs, modify downstream targets) → the ordered-multiset audit bounds DS3 ONLY; DS1/2/4 covered by npz-sha §4 (different gate). Regressed from DESIGN_V1 §4.4 | CC4 | **MED** | **ACCEPT** | reframe §3.1: `emits_legs`={∅ for DS1/DS2/DS4 value-derivations → npz-sha; DS3 conditional leg-emitter → branch-set; DS5 event token}; the ordered-multiset audit is a **DS3-only** guard |
| 5 | **§3.3 "pin blind-spot closes at St2" not delivered by the cited audit** — `route_leg_diff.py:17` parses only dist-lines; `[PIN]` token needs a NEW/EXTENDED parser, not just a print | CC4 (+CC2-CH3) | **MED** | **ACCEPT** | state the close needs BOTH (a) emit event token AND (b) extend `route_leg_diff`/new sequence parser to consume non-`ik_move_both` tokens (St1b/St2 instrumentation) |
| 6 | **§4 "proves equivalence" overclaims** — npz-sha proves the 6-tap fingerprint (necessary), blind to untapped state (IK resid `:4090`, contacts, non-`_sample` bodies) | CC2 | **MED** | **ACCEPT** | qualify: "reproduces the recorded-tap fingerprint; untapped non-divergence rests on `_sample` completeness — enumerate `_sample` at build" |
| 7 | **§7 CP1 "instrumentation non-behavioral" under-specified** — safe ONLY if tokens are STDOUT-print-to-run.log, not new recorder taps (a `note_*` tap shifts frame-stamping → npz changes → CP1 false) | CC2 | **MED** | **ACCEPT** | mandate §3/§7: St2 structural tokens = stdout-to-run.log ONLY (leg-diff parses run.log), NEVER a recorder tap; CP1 guarantee becomes structural |
| 8 | **§4/§6 leave 3/5 primitives (DS1,DS4,DS5) without a row-ification equivalence proof** — only DS2/DS3 proven; DS5=detection-only; DS1(canonical obstacle-B)/DS4 neither | CC2 | **MED** | **ACCEPT** | add DS1/DS4 nominal-regen equivalence (assert row `GRASP_YC`==R3 `np.mean`; row `_kR`==R3 argmin) OR explicitly scope-out with rationale; DS5 = detection + activation-equivalence |
| 9 | **audit ≠ authorship** — the ordered-multiset audit checks executed==declared, blind to WHO authored; "branch-add=Rs 専権" is a PARSER gate (DESIGN_V1 §4.2), not an audit property | CC3 | **MED** | **ACCEPT** | reframe §2.3/§3: audit guarantees consistency (executed==declared); branch-authorship-authority = parser/governance gate, NOT the audit |
| 10 | **DS5 pin lacks the schema-level mandatory binding DS4 got** — clip-seat is only 1 enum value; nothing MANDATES a pin row's gate=clip-seat (INV#5 sole exception deserves parity) | CC3 | **MED** | **ACCEPT** | add DS5 mandatory `inv_binding: gate MUST be clip-seat-verified (RS71 §2); pin/clip-derived row with gate≠clip-seat → BLOCKED_FOR_USER` |
| 11 | **`np.savez :295` mis-attributed to R3** — runner `:295` is blank (grep savez in R3 = 0); real site = `route_demo_recorder.py:295` + `:283-284` | CC5 (+CC4) | **MED** | **ACCEPT** | cite `route_demo_recorder.py:295`/`:283-284`; note it lives in the recorder module, not R3 |
| 12 | **DS3 "C2-analog `:4840`" is code-named F-3 = a WITHDRAWN counterproductive deviation** (`LEDGER:44`, DESIGN_V1 §4.3); §2.2 treats it as a primitive to reproduce while §4.3 treats it as the regression to catch (internally inconsistent; a 先祖返り echo) | CC2 + CC5 | **LOW→elevated** | **ACCEPT** | REMOVE the DS3 C2-analog from the reproduced-primitive set OR annotate it as a KNOWN-WITHDRAWN deviation excluded from "faithful reproduction"; reconcile `LEDGER:44` (this is the same class-error as the DESIGN_V1 CRITICAL — treat with care) |
| 13 | DS5 gate = `PERCLIP_PIN` env flag (default OFF) ∧ clip-seat, not auto clip-seat; reference's PERCLIP_PIN value unstated → DS5 byte-id target membership ambiguous | CC2 | LOW | **ACCEPT** | DS5 gate = "`PERCLIP_PIN` flag ∧ clip-seat"; state the reference's PERCLIP_PIN value |
| 14 | DS4 config precondition (`C2_DUALSEAT ∧ SEAT_TOPDOWN`, both default 0, `:4624-4626`) under-declared; C2-seat is a config-selected 3-way branch; "leaf-complete" is per-primitive-under-fixed-config | CC4 | LOW | **ACCEPT** | add DS4 config precondition; scope "leaf-complete" to "per conditional primitive under the fixed canonical config" |
| 15 | DS5 activation range `:4345-4357` undershoots — `eq_active=1` at `:4379`, ACTIVATED print `:4385-4387` (outside range) | CC5 | LOW | **ACCEPT** | `:4356-4387` (activation block through print) |
| 16 | DS4 bow X/Z extraction at `:4667`, outside `:4662-4665` | CC5 | LOW | **ACCEPT** | `:4662-4667` |

**No full REBUTs.** Every HIGH/MED/LOW is grounded and code-correct (CC1 verified the load-bearing ones: DS1/DS4 always-run; DS4 2nd Rs-LOCK + reduce loophole; §3 value-vs-leg; F-3 identity). PARTIAL only on CC6 (below).

## Convergences (multi-agent → per §運用15, rebut needs added evidence; none rebutted)

- **DS4 = the epicenter (5 agents):** CC2-1 (always-run gate), CC3-2 (orientation Rs-LOCK), CC3-3 (reduce loophole), CC4-14 (config precondition), CC5-16 (range). → DS4 needs a full rework in v0.3.
- **F-3 echo (CC2 + CC5 independent):** the DS3 C2-analog `:4840` is F-3 (withdrawn). → remove/annotate.
- **§3 audit over-claim (CC4 + CC3 + CC2):** bounds DS3-only (CC4-4), ≠authorship (CC3-9), tokens-must-be-stdout (CC2-7). → §3 full reframe.

## NO_ACTION_EVALUATION

- **NHA (CC6) = HOLD** — the St2 BUILD should defer to a genuine (non-reuse) 3rd derived-source trigger; the 5 DS primitives already exist (fix-⑤ cost sunk), the set is "nearly closed", the "gate met by 2" counts BUILT not FUTURE sources (DS1/DS2 = same template).
- **Is NO_ACTION (leave the doc unchanged) warranted? NO — REJECTED.** The doc carries 3 accepted HIGH (gate-taxonomy that would break the build; two Rs-LOCK safety loopholes) + ~7 MED + a 先祖返り F-3 echo. These are DOC defects INDEPENDENT of the build-defer decision — the doc must be revised regardless.
- **CC6's HOLD is folded, not NO_ACTION:** (a) its build-defer is ALREADY the spec's posture (build is Rs-gated, post-φ10/DC-1) — consistent, not contradictory; (b) its **trigger-economics + over-claim points are ACCEPTED as honesty folds** (like DESIGN_V1's honest St1a-ROI≈0 surfacing) — v0.3 will state St2's value is for FUTURE non-reuse sources, caveat the "gate-by-2" (built + DS1/DS2-template-overlap), temper §1/§4.1 (efficiency-from-fidelity) + §3.3 (pin-security is St1b-class). **PARTIAL on "de-scope to skeleton": REBUTTED** — Rs authorized the full St2 paper + %12 directed full deliverables, and CC4 CLEARED the F-1a branch audit as JUSTIFIED (live-dormant conditional, not over-engineering); only the F-3 echo (finding 12) is genuine over-reach, removed. So v0.3 keeps the schema, removes F-3, folds honesty.

## DECIDE

**FAIL → revise to v0.3, then targeted re-verify** (§運用15: accepted CRITICAL/HIGH → FAIL).

The L3 gate worked as designed: the **core is VALIDATED** (Q1; the ② fold; Q2 governance; 33/36 cites; no INVARIANT leak), but the 5-body panel found **real, fixable defects the %10 single-pass (CONCUR/1 MEDIUM) missed** — most importantly the byte-id gate-taxonomy error (would break the build), two DS4 Rs-LOCK teachable-loopholes (safety), and the F-3 先祖返り echo. FAIL = revise-and-strengthen, NOT reject.

## v0.3 revision plan (grouped)

- **Group A — correctness/safety (HIGH + the F-3 echo; must fix):** #1 (two-mechanism byte-id taxonomy), #2 (DS4 orientation Rs-LOCK + DESIGN_V1 §3.1 governance-escalation), #3 (per-DS Rs-LOCK immutable carve-out), #12 (remove/annotate F-3).
- **Group B — audit/proof precision (MED):** #4 (§3 DS3-only audit + value-vs-leg), #5 (pin-close needs parser), #6 (equivalence→tap-fingerprint), #7 (CP1 stdout-only), #8 (DS1/DS4/DS5 proof coverage), #9 (audit≠authorship), #10 (DS5 mandatory binding), #11 (savez module).
- **Group C — citations/config (LOW):** #13 (DS5 flag-gate), #14 (DS4 config precondition + leaf-complete scope), #15 (DS5 range), #16 (DS4 range).
- **Group D — NHA honesty folds (ratified by Rs at approval):** trigger-economics caveat (future-non-reuse; built + DS1/DS2 template-overlap); temper over-claims (§1/§4.1 efficiency-from-fidelity; §3.3 pin-security-is-St1b); state build-defer is unchanged.

**Re-verification after v0.3:** targeted re-check of the 3 HIGH fixes + F-3 removal + the §3 reframe (a focused challenger pass on the changed sections; a full 5-body re-run is not warranted for scoped fixes to an already-panel-reviewed doc — CC1 judgment, §運用15). Then PASS → %12 verify → Rs packet (with Q2 staging decision).

*VT-DESIGN (w2:p5) — St2 L3 debate DECIDE: FAIL → v0.3.*
