# IKCHORD GRIP-SLIP FIX — L3 CC-DEBATE VERDICT = **FAIL** (design revision required)

**CC1:** RS-TECH-LEAD (w2:p4). **Panel:** CC2 premise/provenance · CC3 rule/SSOT · CC4 numerical/physics · CC5 side-effects/regression · CC6 NHA. **Stamped:** 2026-07-18 13:17 JST.
**Input PROPOSE:** `IKCHORD_GRIPSLIP_FIX_L3_PROPOSE_RSTECHLEAD_20260718.md`. **Design authority:** VT-DESIGN (p5). **Governing:** DDR #18 (`00-DESIGN-STATUS-LEDGER.md:98`, execution HOLD).

---

## VERDICT: **FAIL** — do NOT proceed to impl.
The fix **direction** (recorded-branch IK seed) is sound for the immediate scripted residual-0 drop, but the fix as **specified** carries a HIGH internal inconsistency (missing branch/flip guard) and its **necessity + whole-route efficacy are unproven**. Revision routes to p5 (design) + read-only measurements ([VERIFY]) before any [CHANGE]. This is a FAIL-**revise**, not FAIL-abandon.

## MECHANISM = CONFIRMED (all 5 challengers, airtight)
- **CC2 (premise)** independently reproduced every load-bearing number: right-arm branch **4.324 rad** (j14 2.37/j16 1.96/j17 1.89/j19 2.37; left 0.034), endpoint coincidence **0.24 mm** both drives, fingertip **22 mm (ik) vs 6.3 mm (FF)**, drop@267 −10, clamp 0.82 mm, grasp@90 ~2 mm, onset@176, spike@195. M-b2 is real and control-isolated.
- **CC4 (physics)** verified IK = deterministic Levenberg-Marquardt (`n_seeds=1`, `sampler=NONE`, λ=0.1, 30 iter; `ik_solver.py:233-244`) → the seed **genuinely and reproducibly selects the branch**; ≥2 real minima (both achieve position + orientation). The failing run is a **residual≈0 golden replay** → for that scripted drop, seed=recorded=solution ⇒ LM stays ⇒ drop removed (V2 PASS for the scripted case).
- **CC3 (rule/SSOT):** no §0 STOP — the seed is a genuine IK **input** (`:1235` solves the real target `base+residual`; `:1173` is warm-start only); control method / dual-arm / 88 mm / コ untouched. L3 classification correct.
- No-change / "grip is the RS71 §4 fidelity boundary" framing **REJECTED** by CC2+CC3+CC4 (V5): FF proves the grip *can* hold → the −10 is a **drive-artifact**, not the banked fidelity debt (which is routing curvature + pin, not grip).

## ACCEPTED CHALLENGES (basis for FAIL)

### HIGH
- **[CC4 CH-B ∧ CC5 CH-3] AMEND-2 per-step reseed is internally inconsistent with AMEND-1 — a branch/flip GUARD is missing.** AMEND-1 pins **both** reads at step 0 precisely to prevent a cross-branch sweep. But the per-step reseed (C2/AMEND-2) reseeds only `jq_starts` (`:1173`); the within-step interp START `old_fk_jq` (`:1246`) is a **separate read** fed by the previous step's commit `_per_world_fk_jq = jq_targets` (`:1283`). If a trained residual (up to `DELTA_BOUND_M=0.020`) flips the branch at step *t*, `:1254` linearly sweeps the right arm ≈4.4 rad through joint space in 10 frames — kinematically driven (`phys_jqd=0`, no PD damping) — i.e. the **exact catastrophe AMEND-1 declares and prevents at step 0**, now un-guarded at every mid-route flip (and the reseed "recovery" at *t+1* is a second ≈4-rad sweep). "Self-correct in 1 step" is true of the **endpoint**, false of the **path**. Two challengers found this independently.
- **[CC4 CH-D] Basin geometry at the trained-policy 20 mm residual is unverified.** Convergence-from-recorded was shown only at residual 0. The two branches differ ~2 rad at shoulder AND elbow → one is nearer a singularity; near a branch point the minima merge and the seed loses selective power. Whether a 20 mm target keeps the recorded seed in the recorded basin is an unmeasured property.
- **[CC2 CH-1] Evidence + DoD cover only ~40% of the route.** Whole route = 771 RL steps; both probes stop ~300. **C2_REGRASP @ ~step 500 is a FRESH right-arm IK branch selection** (cable-derived target, `route_executor.py:105`) = the highest grip-slip-risk event, **entirely unmeasured**. A DoD centered on 176-195 + drop@267 goes green on the C1 half while G4-G6 stay unvalidated = phase-scope-generalized-to-whole-route.
- **[CC6 / NHA = HOLD] Necessity unproven under the operative config.** The grip-slip was measured **pin-OFF** (`grip_retention_measure/summary.json` cfg — no `route_c1_pin`); the trainer D-b gate runs ik_chord **pin-ON** (`PIN_DB_WINDOW_GATE_PREREG:51`). **CC1 added finding:** `summary.json g3_reached:false` — grip is lost **before** a C1 seat, and the (d-b) pin **fires on seating**, so the pin likely cannot rescue this drop → the fix is *probably still necessary* — but that is a **prediction, not a measurement**. NHA HOLD accepted as "measure necessity + close design gaps before impl," NOT "grip is a fidelity boundary" (that sub-argument is rejected).
- **[CC3 CH-1] Surface-to-Rs (NOT a fix-blocker):** the §0 compliance is inheritance-based; the pre-existing **kinematic arm joint_q drive** (`route_executor.py:236` qd=0; `:1272`) is §0-adjacent (literal #5 grants no exception beyond the clip pin), sanctioned only for the **scripted-verification stage** — its status as the trainer/production control method is unratified. Worth a one-line Rs confirmation (physics-faithful position control vs a §0#5 exception). Evidence + Rs-authorship favor "compliant."

### MEDIUM
- **[CC5 CH-1/CH-6] The `_per_world_fk_jq`-only O1 resolution creates a step-0 settled→recorded arm teleport** (`:1094` stays at settled P0 branch; step-0 drive assigns recorded before the first physics step) that the current code does not produce — probably benign (open gripper, qd=0, cable at rest, FK-recomputed bodies) but a NEW ~4.32 rad per-reset pop. Record the O1 tradeoff explicitly; add a step-0 + **visual** re-measure leg.
- **[CC5 CH-2] Reset-seed FRAME under-specified:** `old_fk_jq[0]` needs the step-START `arm_q[step_f[0]]` (frame 0) while `jq_starts[0]` needs `arm_q[next_f[0]]` — one `_per_world_fk_jq` seed cannot be both; C2 must also reseed `jq_starts` at step 0. Elevates O3 from "confirm index" to "two consumers need distinct frames."
- **[CC4 CH-A] "branch fix removes the entire 2.4× cable push" is inferred** (config offset quasi-constant while separation is a non-monotonic spike; grip is fine@90 despite the arm already flipped). Keep AMEND-4 (cable-disp ≈1×arm) as a **falsifiable gate**, not a confirmation.
- **[CC4 CH-E] A fixed nonzero-residual leg is self-proving unless it CROSSES a basin boundary + instruments the within-step path.** ("a test that cannot come out differently is not a test.")
- **[CC3 CH-2] Provenance fix:** "banked c2045a9a1a" = the **diagnosis** commit; acceptance = `cdac6b6972`+`f8b1ff6b4c`; the drive is Rs-adjudicated for the **scripted-verification stage**, production control path = separate pending Rs gate.

### LOW
- **[CC4 CH-C]** AMEND-3 seed is **position-exact, not "0-iter"** (held-KO rot w=0.5 + joint-limit w=10.0 terms are nonzero at recorded arm_q). Soften wording; log IK cost 0→30 from the recorded seed.
- **[CC5 CH-4]** the fix couples ik_chord to `arm_q` (OPTIONAL for ik_chord recordings today) → guard (a) must fail **LOUD** (never silent fallback-to-buggy-settled-seed).
- **[CC5 CH-5]** guard (b) is a wc=1 no-op; validate at wc>1 (held world + mid-batch reset) before fork-B.
- **[CC2 nits]** window label is 248-270 (not 248-267); FF-probe = 39% of route ("holds through step 300", not "whole route"); proximate cause@267 = the **LEFT** arm (correct branch) escaping laterally under single-arm load — the right wrong-branch is the ROOT (single-arm from ~195), not the proximate terminal.

## REQUIRED BEFORE IMPL

### A. Design revision — routes to p5 (design = Rs-専権代弁; CC1 does NOT self-derive)
1. **Branch/flip guard** on `jq_targets`: reject/clamp any IK solution whose per-joint wrap-distance from the recorded arm_q exceeds a branch threshold (fall back to recorded / previous recorded-branch), so **no cross-branch delta is ever driven through `:1254`** — makes AMEND-2 self-consistent with AMEND-1.
2. **Frame spec:** `old_fk_jq[0]=arm_q[step_f[0]]` (frame 0), `jq_starts[0]=arm_q[next_f[0]]`.
3. **Step-0 teleport decision:** accept `_per_world_fk_jq`-only + a step-0/visual verification leg, or revisit.

### B. Read-only measurements — [VERIFY] (need HOLD/scope concurrence; the original `grip_retention_measure` was read-only and allowed)
4. **Necessity:** re-run `grip_retention_measure` with `route_c1_pin=True` (does the `A_held_z_floor` drop persist pin-ON?).
5. **Coverage:** whole-route ik_chord + FF baseline to G6 / past C2_REGRASP (~step 500) — is the slip C1-half-only or whole-route; is C2_REGRASP a second slip site?
6. **Robustness probe:** a residual sweep that **provably crosses a basin boundary** on ≥1 route step + within-step config-path logging + the branch-guard check (not a self-proving fixed-residual leg).

### C. Surface to Rs
7. One-line confirmation that the kinematic arm joint_q drive is sanctioned physics-faithful position control for the trainer stage (CC3 CH-1), and provenance/wording fixes (CC3 CH-2, CC4 CH-A/C, CC2 nits).

## NO_ACTION_EVALUATION
- No CODE change breaks nothing on the current **operative** path (FF holds). But **ik_chord is the trainer drive** (FF replay cannot accept policy residuals; CC3 V5), so the fix is needed for training **iff** the grip-slip blocks pinned ik_chord — the necessity gap (measurement 4) resolves this.
- KNOWN_ALTERNATIVES already-solved: none (substep REFUTED, null-space ruled out, M-b1 refuted, solref not-primary — all re-confirmed by the panel).
- CC6 NHA = HOLD, accepted as "revise design + measure necessity/coverage before impl," rejected as "grip is a fidelity boundary."

## OUTCOME
**FAIL** → (A) design revision @ p5, (B) read-only necessity/coverage/robustness measurements, (C) Rs surface. **impl remains fenced** (execution HOLD unchanged). **Re-debate after the revised design.** WMSO untouched.
