# 5体 [VERIFY] VERDICT — route-executor Layer-B build plan v0.1

**gate:** L3 pre-build 5体 CC Debate (§運用2 [VERIFY] + §運用15). CC1 lead = %12 RS-TECH-LEAD.
**subject:** BUILD_PLAN_ROUTEEXEC_LAYERB_COORD_20260707.md v0.1 (commit a51825bd28).
**date:** 2026-07-07 15:1x JST.
**DECIDE:** ⭐ **REVISE → v0.2** (NOT build-authorized as-is; NOT a node-killing FAIL). Architecture sound; re-scope + specify + restore-dropped-carry required. Re-gate v0.2 deltas → then authorize minimal Stage-A.

---

## Per-challenger verdicts (all 5 = NEEDS-REVISION)

### CC2 (step_target / recorded_replay / ⑨b) — NEEDS-REVISION
- **CH1 HIGH** — recorded `ee_tgt_pos` is the piecewise-constant leg GOAL, not per-frame path. Replaying goal at cadence-10 → RL arm SNAPS to waypoint (~1 step) vs monolith RAMP (50-500 frames): first-order motion divergence (~323mm mid-leg, ~49 RL-steps early). "single-source" holds for targets, trajectory diverges. FIX: for ⑨b substrate-isolation replay recorded `ee_pos` (achieved smooth path), OR keep `ee_tgt` + name ramp-vs-snap as dominant divergence in §13. **[design fork — may touch trainer fork-(iv) base contract]**
- **CH2 HIGH** — phase_id/grip_2 provenance unspecified; both obvious sources WRONG. Recorded phase_id ∈{-1..14} (15 vals) but contract needs [0,6); stub re-derives phase/grip from EQUAL-SPLIT clock even in recorded_replay → desync 100s of steps → **cable dropped every ⑨b episode**. grip_cmd = per-arm RADIANS not 0/1. FIX: source phase_id/grip_2/is_dual from RECORDED arrays; define 15→6 map + radians→{0,1} threshold.
- **CH3 HIGH** — interface carries no world/cell index; `step_target(t)` returns single target → all worlds same. 81 per-cell recordings can't batch-replay; `__init__` takes no recorded_targets. ⑨b = **81 sequential single-cell runs** (Stage-B cost unstated). INIT_XY_NOISE=0.005 corrupts pure replay. FIX: state 81 single-cell; extend `__init__` recording-carry; INIT_XY_NOISE=0 for replay.
- **CH5 MED** — R/L concat footgun: consumer reads [0:3]=R,[3:6]=L (R-first) but recorder `_STACK_KEYS` lists `ee_tgt_pos_l` BEFORE `_r` → field-order stack = [L,R] → arms SWAPPED silently. FIX: explicit [R,L] assembly + unit assert.
- CH4 MED (per-cell n_frames 7706-7710 not const, hardcode; pad holds grippers-OPEN, need G6-latch-before-pad assert), CH6 MED (⑨b C1-retention not orthogonal to SRG; ⑨b NOT vacuous — C2-seat@0.5mm is genuine new test).
- **SOUND:** deferring live mode well-founded; **cadence-10 IS sim-time-consistent** (verified); non-accumulating base+residual correct; flag-gated default-off sound.

### CC3 (SRG grip physics) — NEEDS-REVISION
- **CH1 CRITICAL** — "no slip / slip-onset" PASS criterion is banked-UNREACHABLE. Substrate has INTRINSIC creep (60.4 µm/frame @F=0, 10-substep; LL-Creep-Characterization). Absolute no-slip physically unreachable → already caused **2× false-PASS** (LL-G3-Vacuity). Grip = form-closure CAGE (cage≠hold). **4-substep creep UNMEASURED** (10-substep bank doesn't transfer, likely worse). FIX: creep-BUDGETED criterion (rate-under-load ≤~1.2 OR service-exposure window); **re-measure creep floor at 4-substep as FIRST SRG substep**. (resolves plan's own Q4.)
- **CH2 HIGH** — nominal-only doesn't gate 81-offset tail (nominal=easiest; table-VOID edge ±16mm + contact-angle offset-dependent). FIX: screen nominal + DR-corner + known-hard; gate=worst-screened.
- **CH3 HIGH** — §7 FAIL-lever list omits banked-BEST levers noslip_iterations (110×) + impratio (∝1/impratio), which are ACTIVE here (condim6+pad rolling rows). FIX: add {noslip_iterations, impratio, solver iters, pad friction/solref} ranked cheap→campaign; substep 4→N LAST.
- **CH4 HIGH** — threshold-relax blocked (good) but silent MARGINAL-ACCEPT not (single nominal video+human-GT insufficient observable). FIX: bind no-silent-cap to OBSERVABLE (creep metric + tail cells + quantified slip-time-series).
- CH5 MED (per-axis conservatism: substep=conservative-w-caveat / offset=non-conservative / creep-floor=unknown).
- **SOUND:** stage separation; flag-gated default-off byte-identity (verified :1584); refusing 58/81 assumption; substep→Rs; human-GT.

### CC4 (byte-preserve / regression / tripwire) — NEEDS-REVISION
- **C1 HIGH** — component-4 write-site swap flag-gating UNSPECIFIED. Current env-core writes 28-wide INCLUDING gripper (pin to FK-home every frame); AR machinery excludes gripper. Unconditional swap → flag-OFF gripper DRIFT → **byte-identity BREAKS = the twice-recurring gripper-overwrite defect**. FIX: write-site exclusion MUST be flag-gated; flag-OFF retains byte-exact 28-wide write.
- **C2 HIGH** — §10 tripwire "reverse F11 on monolith slice" is a TAUTOLOGY. Golden = sha256(test:3692-5765); hashing that slice vs golden = D-1=C monolith-edit detector, catches ZERO run_route drift (its stated purpose). FIX: 2 legs — (a) raw-sha test:3692-5765==golden = monolith-edit tripwire; (b) run_route drift = ast-semantic-equiv reversing only F11 (mirror §12.4). Keep stub non-blocking until (b) specified.
- **C4 MED** — pin B⑨a′ as full-arm_q sha-byte INCL gripper coords (not verdict/arm-only, else gripper drift invisible) + carry ⑩ mjModel geom introspection assert (C2/void default-off).
- C3 MED (Stage-A byte-verify near-vacuous for NEW code once flag-gated → reword §5 to claim non-perturbation + offline-fidelity + static-drift only), C5 LOW (lazy-import route_executor / DEVICE import-capture).
- **SOUND:** grasp_actuation gating byte-clean by construction (all 4 scene mutations gated, else rebuilds identical solid table); **D-1=C preserved** (route_executor self-contained, doesn't import monolith); _GRIPPER_COORDS_LOCAL single-SSOT (G7); Layer-A harness strong guard.

### CC5 (DoD / scope / C2 geometry) — NEEDS-REVISION (additive)
- **CH1 HIGH** — **DoD⑤ / charter carry #1 (wall/spacer EXACT seat-predicate) silently DROPPED** (plan grep=0). Node state.md:11 = wall-dist≤0.5mm spacer-excluded via mjModel geom introspection (upgrade from 3.5mm center proxy `_c2_seated_honest:793-800`). If ⑨b uses proxy → OVER-counts + DIVERGES from Layer-A offline 58/81 (predicate mismatch masquerading as substrate divergence). FIX: add wall/spacer exact-split component+DoD; ⑨b uses EXACT predicate.
- CH2 MED (§運用29 name-dropped not discharged → add explicit leg table: 把持/C1-retention/C2-seat/crossing conjoined-vs-diagnostic), CH3/CH4 MED (classify open-Qs; Stage-A gate-i static-not-GPU), CH5 LOW-MED (pin 81 recordings now).
- **SOUND (verified, de-risks concerns):** strict_v2 molecule does NOT repeat J-9 (C1-retention IN numerator, grasp covered transitively); **C2 geometry CORRECT** (C2=even clip X=0.40 on SOLID floor, NO void, additive build → Q2 pre-resolved); scope discipline clean (no creep, trainer/oracle/OG absent); conservatism right.

### CC6 (NHA) — CHANGE_JUSTIFIED (minimal subset) / DEFER majority
- Strong-null (build nothing) REJECTED: real low-risk grip-INDEPENDENT slice discharges ⑦(a) + ⑬-precursor, no premise bet; node Rs-authorized.
- **Full 8-component build NOT justified now** — plan front-loads grip/C2 (3/4/5) into Stage-A where NO Stage-A gate exercises them, resting on the flagged UNKNOWN (4-substep grip). If SRG FAILs + fix = PD/substep → Stage-A-built 3/4/5 need REWORK = building on sand. flag-OFF byte-identity is a CONSTRAINT (must satisfy regardless of when built), NOT a payoff.
- **Disposition:** 1=JUSTIFIED-NOW (recorded_replay-only, CUT live) / 2=JUSTIFIED-NOW (only path to ⑦, no-GPU) / 3=DEFER activation (bundle w/ SRG) / 4=DEFER (grasp_actuation=ON only) / 5=DEFER (live Stage-B only; early build = 4th byte-preserve surface, zero static payoff) / 6=DEFER (not DoD; already protected by ANTI-REVERT + Layer-A) / 7=re-scope to MINIMAL probe FIRST (cheapest C1-grasp+hold go/no-go) / 8=DEFER (Stage-B gated).
- **Minimal-viable Stage-A = {1 recorded_replay-only, 2 + state_bank}.** 2 risks: recorded_replay source unresolved (Q5); ⑦ has 2 halves (⑦(a) restore-L∞ no-GPU Stage-A; ⑦(b) 1-step-after-reset needs grasp_actuation=ON = Stage-B → plan's "⑦ Stage-A verifiable" only half-true).

---

## CC1 REBUT_OR_ACCEPT (no REBUTs — all challenges code-verified, not speculation)

All accepted. Convergence (multi-challenger → strong):
1. **Stage-A over-scoped** (CC6 + CC4-C3 + CC5-CH4): re-scope to minimal grip-independent core {1,2}. ACCEPT.
2. **step_target packet under-specified** (CC2 CH1/2/3/5): phase/grip from recorded arrays; ee_pos-vs-ee_tgt fork; 81 single-cell + __init__ carry + INIT_XY_NOISE=0; R-first. ACCEPT (become component-1 build spec).
3. **write-site (comp4) must be flag-gated** (CC4-C1): else the twice-recurring gripper-overwrite defect. ACCEPT (comp4 deferred; flag-gate when built).
4. **§9 tripwire semantics incoherent** (CC4-C2): defer + fix to 2-leg (raw-sha monolith-edit + ast-equiv run_route-drift). ACCEPT.
5. **DoD⑤/carry#1 dropped** (CC5-CH1): restore; ⑨b uses EXACT wall/spacer predicate not 3.5mm proxy. ACCEPT.
6. **SRG criterion not build-ready** (CC3-CH1 CRITICAL): creep-budgeted + 4-substep creep re-measure + tail screening + noslip/impratio levers + per-axis conservatism. ACCEPT (before Stage-B).

## NO_ACTION_EVALUATION
- NHA = CHANGE_JUSTIFIED-minimal (not HOLD): node Rs-authorized, real low-risk deliverable exists → build-nothing rejected.
- Existing-alternative = the minimal Stage-A {1,2} itself (CC6) → adopt it (less code, no premise bet).

## DECIDE = REVISE → v0.2 (then focused re-gate → authorize minimal Stage-A)
ACCEPTED CRITICAL (CC3-CH1) + multiple HIGH ⇒ v0.1 NOT build-authorized. Path is clear + additive ⇒ REVISE not FAIL. No GPU spent; node healthy.

### v0.2 revision directive (COORD)
1. **Re-scope Stage-A → minimal {1,2}**: comp1 step_target recorded_replay-ONLY (live CUT/deferred-to-trainer, Q1 resolved) + comp2 env-wiring + state_bank. Discharges ⑦(a) restore-fidelity (no-GPU) + ⑬-precursor. NO 4-substep premise bet.
2. **Bake step_target packet spec** (CC2): phase_id/grip_2/is_dual from RECORDED arrays (15→6 map + radians→{0,1}); resolve ee_pos-vs-ee_tgt for ⑨b **[flag if it touches banked fork-(iv) trainer-base → escalate to me/design-gate]**; 81 single-cell + __init__ recording-carry + INIT_XY_NOISE=0; R-first assembly + unit assert.
3. **DEFER 3/4/5/6/7/8 → Stage-B**, gated behind a **MINIMAL SRG probe FIRST** (cheapest C1-grasp+hold go/no-go before committing 3/4/5). When built: comp4 flag-gate write-site (CC4-C1); comp6 tripwire 2-leg semantics (CC4-C2).
4. **Restore DoD⑤/carry#1** (CC5-CH1) + discharge §運用29 leg table (CC5-CH2). ⑨b strict_v2 uses EXACT wall/spacer predicate.
5. **Revise SRG design** (CC3, before Stage-B): creep-budgeted criterion + 4-substep creep re-measure (first substep) + tail-cell screening + add noslip/impratio/solver-iters/friction levers (substep 4→N last, Rs-level) + per-axis conservatism + observable-bound no-silent-cap.
6. **Split ⑦** → ⑦(a) restore-L∞ no-GPU Stage-A / ⑦(b) 1-step-after-reset grasp_actuation=ON Stage-B (CC6). Pin B⑨a′ = full-arm_q sha incl gripper + ⑩ geom assert (CC4-C4). Stage-A gate-i = STATIC diff not GPU (CC5-CH4).
7. **Open-Q resolutions**: Q1=recorded_replay-only (live deferred); Q2=C2 pre-resolved (over-solid additive flag-gated, CC5 SOUND-B); Q3=pin state_bank phase-k boundary NOW (recording carries phase_id per frame); Q4→creep-budgeted (CC3-CH1); Q5=reuse+pin 81 recordings now.
