# L3 5-body [VERIFY] debate — DECIDE (VT-DESIGN / CC1 lead)

**Subject:** `DESIGN_V1.md` v1.2. **Format:** §運用2 [VERIFY] / §運用15. **Date:** 2026-07-06.
**Panel:** CC2 byte-id · CC3 INVARIANTS/gov · CC4 scope/step-table · CC5 grounding · CC6 NHA. **Lead:** CC1 (VT-DESIGN/p5).
**Provenance:** v1.0 → %12 APPROVE → %10 CONCUR → v1.2 → this debate.

## Panel tallies

| Agent | CRIT | HIGH | MED | LOW | verdict |
|---|---|---|---|---|---|
| CC2 byte-id | 0 | 1 | 4 | 3 | obstacle-B thesis + 4 St1a env-reads VERIFIED CORRECT |
| CC3 INVARIANTS/gov | 0 | 1 | 4 | 1 | — |
| CC4 scope/step-table | **1** | 3 | 3 | 1 | scope-discipline clean |
| CC5 grounding | 0 | 0 | 0 | 5 | 5 line-drifts of ~44; all facts correct |
| CC6 NHA | 0 | 2 | 2 | 2 | **NULL_HYPOTHESIS = HOLD** |
| **unique** | **1** | **6** | **~12** | **~7** | |

Core VALIDATED (no defect): obstacle B (`caveat-a GRASP_YC=np.mean(_near)` runs unconditionally on nominal, `:3937-3948`) — the `target_source` thesis holds; St1a's 4 env-params ARE genuinely env-read (CLIP2_Y :3688, CLIP_X :3645, CLIP_Y :3646, LIFT_M :3642); scope discipline (no full-route over-claim).

## REBUT_OR_ACCEPT (CC1)

| # | Finding | Agent(s) | Sev | Verdict | Fix (→ v1.3) |
|---|---|---|---|---|---|
| 1 | class-A examples "F-1a/F-1b/F-2/F-3" include F-1a-**v2** (C1v2-LIFT/SHIFT/TRIM, leg-adding) + F-3 = LEDGER:44-removed deviations; charter:15 blesses only F-1b/F-2/F-1a-**v1** | CC4 | **CRIT** | **ACCEPT** | restrict class-A to {F-1b, F-2, F-1a-v1}; EXCLUDE F-1a-v2 + F-3; add rule "an offset that adds/removes any `ik_move_both` leg is NOT class-A = structural = Rs 専権" |
| 2 | class-B freezes a NEW `RUN1_REFERENCE` (SSOT standard) via **CC-only tri-key**, effective BEFORE Rs step-6, no Rs re-declaration, no LEDGER:44 update (violates §運用4) | CC2 + CC3 | HIGH | **ACCEPT** | class-B freeze = PROVISIONAL until Rs step-6 re-declaration; **Rs = required authorizing key** for standard supersession; same-turn LEDGER:44 annotation; p2r_c11 stays FROZEN structure ref |
| 3 | St3 does NOT structurally prevent leg invention — 1 primitive → N legs via code loops/flags (`:4010`,`:4076`,F-1a-v2); "row=leg" is 1:N | CC4 | HIGH | **ACCEPT** | each row DECLARES its emitted leg-label list+count; mechanical assert primitive emits EXACTLY declared legs; downgrade "structurally impossible" → "gated by table↔leg-count assertion + primitive audit" |
| 4 | leg-diff ground truth = a reference RUN.LOG, NOT the table → enforces run==run, cannot enforce step-table-first (table↔run) | CC4 | HIGH | **ACCEPT** | add a distinct table→run gate (assert executed leg-set == table's declared per-row leg-set); reframe leg-diff as run-regression guard ONLY |
| 5 | grip/settle/pin primitives INVISIBLE to leg-diff (`LEG_RE:17` matches only `ik_move_both` dist-line) → dropped settle / added re-clamp / moved pin passes SAME-STRUCTURE | CC4 (+CC2 obstacle-D) | HIGH | **ACCEPT** | emit a parseable structural token for EVERY primitive; extend the detector to consume grip/settle/pin events |
| 6 | St1a ROI premise unmeasured (sole measured = fix-⑤ ~1.5h = a NEW-primitive change = St2/St3 class, not St1a's amplitude class) | CC6 | HIGH | **ACCEPT** | evidence-gate the recommendation: measure a real amplitude-edit baseline + show discipline-only doesn't already meet ≤1-round-trip, BEFORE authorizing St1a build |
| 7 | St2/St3 target a "nearly-closed" class (scoping S-7, cited by the doc) → ROI≈0 | CC6 | HIGH | **ACCEPT** | reframe D-1: St1a = near-term candidate; **St1b/St2/St3 DEFERRED**, each gated on a measured trigger (≥2 genuine new-primitive needs) |
| 8 | St1a byte-id needs the FULL nominal env set (~19 vars) + `NEWTON_DEVICE=cuda:0`, not just the 4 | CC2 | MED | **ACCEPT** | enumerate the full nominal env; 4 params necessary-not-sufficient; pin cuda:0 ([[project-canonical-route-device-fragile]]) |
| 9 | St1a delivery unspecified — R3 reads env at call time → must be a launch-wrapper | CC2 | MED | **ACCEPT** | specify St1a = launch-wrapper (env exported before runner exec) |
| 10 | obstacle-D tap set omits `note_grip`+`note_pin` (byte-affecting) | CC2 | MED | **ACCEPT** | add them → 6 taps not 4 |
| 11 | pin gated on the TOKEN 「ピン留め」, not the clip-retention SEMANTIC (RS71 §2 clip-only) | CC3 | MED | **ACCEPT** | pin row needs a mandatory seat-AT-CLIP gate; non-clip pin → BLOCKED_FOR_USER |
| 12 | 「間隔」 referent overloaded: clip-spacing (allowed) vs grasp-span (INV#2, Rs 専権) | CC3 | MED | **ACCEPT** | parser resolves the referent BEFORE mapping; grasp/arm/EE-span → INV#2 BLOCKED_FOR_USER |
| 13 | St2/St3 edit the locked runner but tagged bare "→ L3" without "+ Rs explicit auth" (charter mandate) | CC3 | MED | **ACCEPT** | tag St2/St3 = "L3 + Rs explicit auth + byte-id re-proof" like St1b |
| 14 | L-triage under-classifies GLOBAL amplitude (LIFT_M) as L1; scene/leg taxonomy has no GLOBAL bucket | CC3 | MED | **ACCEPT** | add GLOBAL consumed-by → L3; any class-B/global amplitude = L3, overriding L1 "pure-amplitude" |
| 15 | coordinate-only quality-degrading change escapes leg-diff+sha (F-3 = the anchor-cited counterexample: passes both, only video/Rs catches) | CC4 | MED | **ACCEPT** | state leg-diff+sha guard STRUCTURE + nominal-drift ONLY; keep video/Rs load-bearing (not "automatable"); add per-leg amplitude-bound check where a standard exists |
| 16 | no reachability branch — a class-B change unsatisfiable coordinate-only (reach-wall/`MAX_MOVE_STEPS` clamp) yields degraded-but-SAME-STRUCTURE that both gates PASS | CC4 | MED | **ACCEPT** | add a reachability/clamp check to the loop; unsatisfiable coordinate-only → BLOCKED_FOR_USER; wire §6 `/geometric-design` into the loop |
| 17 | "substep count" listed as class-A amplitude, but changing a loop bound adds/removes "k/N" legs → STRUCTURE-DEVIATES (internal contradiction) | CC4 | MED | **ACCEPT** | split schema: within-leg step-count (`speed_factor`/`n_steps` = class-A) vs number-of-sub-legs (LIFT_SUBSTEPS/N_ROUTE = STRUCTURAL) |
| 18 | DoD clearable discipline-only with existing GT-verified tools | CC6 | MED | **ACCEPT** | run discipline-only first as the baseline; St1a's value = the measured gap over discipline |
| 19 | St1b avoidable via env-routable example choice | CC6 | MED | **PARTIAL** | ACCEPT "pick 3 env-routable DoD examples, defer St1b"; REBUT "route speed via env var" — that IS an R3 edit = St1b (self-contradictory) |
| 20 | St1a "single home" only true post-St1b (literals stay in R3) | CC6 | LOW-MED | **ACCEPT** | §3.2: St1a REDUCES scatter; full single-home = St1b+ |
| 21 | St3 anti-invention ≈ existing leg-diff | CC6 | LOW | **PARTIAL** | REBUT "duplicates" (structural prevention ≠ post-hoc detection → fewer round-trips); ACCEPT "adopt run-leg-diff-every-edit as discipline now + gate St3 on evidence" |
| 22 | class-B leg-diff needs the p2r_c11 run.log, not the `.mp4` | CC2 | LOW | **ACCEPT** | note class-B 5a diffs the p2r_c11 run.log artifact |
| 23 | verdict-critical L3 list omits GRASP/CLAMP | CC3 | LOW | **ACCEPT** | state grasp-phase params are non-teachable (constant-only) by design; if ever exposed → L3 |
| 24 | St2 fix-⑤ proof cites notes 13/21/29/37 but validated scope = C1→C2 (29/37 beyond) | CC4 | LOW | **ACCEPT** | scope St2 proof to rows 13/21; 29/37 under D-3 full-5-clip |
| 25 | 6 citation line-drifts (3626-3648/3946 region), all facts correct | CC5 + CC2 | LOW | **ACCEPT** | GHS→:3634, z_grasp→:3635, CLIP_X/Y→:3645-3646, CLIP2_Y→:3688, R.x→:3970-3978, np.savez→:295 |

## NO_ACTION_EVALUATION

- **NHA (CC6) = HOLD**, arguing an existing alternative (St1a-only-evidence-gated / discipline-only) suffices → the build should be minimized/gated.
- **Is NO_ACTION (leave the doc unchanged) warranted? NO — REJECTED.** The doc carries an accepted CRITICAL (class-A smuggles LEDGER-removed deviations) + 6 accepted HIGH (governance hole, 3 structural leg-diff/leg-invention gaps, 2 recommendation over-reaches). These are DOC defects independent of the build-scope decision; the doc must be revised regardless.
- The NHA's HOLD is **not** grounds for NO_ACTION-on-the-doc; it is **folded into v1.3** as the corrected, evidence-gated, conservative recommendation (findings 6/7/18/19/20/21).

## DECIDE

**FAIL → revise to v1.3, then re-verify** (§運用15: accepted CRITICAL/HIGH → FAIL).

This is the L3 gate working as designed: the design's **core is VALIDATED** (obstacle-B thesis; St1a env-routing; scope discipline), but the debate found **real, fixable defects** — most importantly the CRITICAL 先祖返り risk (class-A examples) and three structural mis-framings of what leg-diff can enforce. FAIL = revise-and-strengthen, NOT reject.

## v1.3 revision plan

**Group A — doc-defect fixes (CC1 authority, charter-faithful, no direction change):** findings 1 (CRITICAL, align to charter:15), 3, 4, 5 (leg-diff/leg-invention structural reframe + table→run gate + all-primitive tokens), 8-17, 20, 22-25.

**Group B — recommendation-tempering (more conservative; ratified by Rs at the design-approval gate):** findings 6, 7, 18, 19, 21 — St1a evidence-gated (measure baseline + discipline-first), St1b/St2/St3 DEFERRED on measured triggers.

**Group C — governance (Rs-authority addition):** finding 2 — class-B reference supersession requires Rs as the authorizing key + LEDGER:44 same-turn update. (Adds an Rs gate; Rs to confirm at approval.)

**Re-verification after v1.3:** targeted re-check of the CRITICAL fix + the 6 HIGH fixes (a focused challenger pass on the changed sections is sufficient; a full 5-body re-run is not warranted for scoped fixes to an already-panel-reviewed doc — CC1 judgment, per §運用15 "修正版を再検証").

*VT-DESIGN (w2:p5) — L3 debate DECIDE: FAIL → v1.3.*
