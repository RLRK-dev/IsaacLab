> **Archived by %11 (COORD) at R1 close — Rs decision (B), 2026-07-05 10:17 JST.** DQ7 mini-test terminated at 0 GPU per 5体 [VERIFY] = FAIL (2 CRITICAL: span-break [per-arm guard-2] + state-blind-expert confound; + high-INCONCLUSIVE/validity). Content below unchanged from the scratchpad working copy.

# DQ7 mini-test — 5体 [VERIFY] debate results (CC1=%11 collecting)

Launched 2026-07-05 09:4x. CC1 REBUT_OR_ACCEPT + NO_ACTION_EVAL + DECIDE after all 5 return.

## CC6 (NHA) — RETURNED 09:5x — **NULL_HYPOTHESIS: HOLD**
Argument (well-grounded in proposer's OWN docs):
- (c) close-declaration = proposer-certified EQUIVALENT (devplan:136 "skip=等価選択肢" / D-A :206), zero-GPU/zero-code.
- value = epistemic-only, does NOT gate critical path (devplan:135); env-build independent of mini-test (D-B :207); neither A nor B changes near-term action (both build P2 env).
- β-mix code throwaway (non-portable to P2, devplan:135 "concept precedent 降格").
- devplan:278 (CC4-5, the proposal's own debate) already conceded 2/3 justifications dead + "RESOLVE 産物の消費者なし" → PARTIAL-ACCEPT.
- material INCONCLUSIVE risk: materiality floor (packet:71) + ADAPT voids leg-1 (packet:78→VERDICT needs BOTH legs) → can't conclude → INCONCLUSIVE; seed-repeat escalation can exceed 2.3h.
- CONCEDES: (a) β=0 + (b) single-offset genuinely superseded — no existing DATA resolves A-vs-B. HOLD rests on ONE premise: "A-vs-B resolution NOW lacks near-term decision value" — devplan grants it (:135/:136/:207/:278).
- NOTE: devplan's own CC6 CHANGE_JUSTIFIED (:285) was on the L2 PAPER, not this L3 CODE build → doesn't transfer.

CC1 preliminary REBUT direction (pending CC2-5):
- CC6 is SOUND-ON-MERITS (epistemic-only value, throwaway code, INCONCLUSIVE risk = all real, all from proposer's docs). NOT silently dismissable (§運用15).
- BUT the mini-test-vs-close decision = **D-A = Rs 専権**, and Rs ALREADY chose **mini-test-first** (node state.md:140, 19:33 AskUserQuestion, over (i)-RL-now/保留) AND **re-authorized TODAY** (Rs std-authority 08:5x → %12+%9 JOINT-DECIDED, banked 231639c0d1 = the charter). So CC6's HOLD re-opens an Rs-decided strategic point.
- → Disposition likely = **REVIEW/surface to Rs via %12** (NHA raises sound HOLD re-opening D-A; Rs already decided + re-authorized; flag for Rs to confirm proceed vs reconsider close-declaration), NOT unilateral NO_ACTION by CC1 (reversing an Rs strategic decision is outside COORD lane; §運用10/prohibited「方針変更は Rs」). CC1 does not rubber-stamp NOR unilaterally reverse Rs.

## CC4 (span-projection purification) — RETURNED 09:5x — **CH1 CRITICAL + 3 HIGH/MED**
- ⭐**CH1 CRITICAL (load-bearing, likely ACCEPT):** o2 ordering (blend→guard-2→solve) with PER-ARM guard-2 (:826-834) BREAKS span-preservation. guard-2 clamps each arm's _dv independently by 15/mag; off-path the EE pair is asymmetric → dv_R≠dv_L magnitude → different clamp factors → executed span ≠ 88mm. Worked: dv_R=40→×0.375, dv_L=10→unclamped ⇒ ~25mm span error (cf B1 34.9mm grip-0N). Break occurs in the off-path expert-pull transient (%9:19 expert >>15mm → guard-2 GUARANTEED fires asymmetrically) = exactly the regime β-mix exercises. "structurally guarded / never blended" (packet KEY DESIGN DECISION) = FALSE as executed (span guarded on a value never solved/applied). FIX: (a) guard-2 → explicit center-clamp + span-clamp decomposition / (b) per-step post-guard-2 span ASSERT → on-fail log+VOID / (c) span at C1-grasp landmark = GATE not informative. Min: retract "structurally guarded" → "preserved only when guard-2 doesn't fire asymmetrically".
- **CH2 HIGH:** informative span telemetry can't surface suppressed span pathology — measured OFF-distribution (β>0 executed uses expert-span → visited states expert-span-driven; ‖s_policy−s_tp‖ logged at wrong distribution) + p90-over-trajectory dilutes the transient + 10mm loose vs grip physics + capture-point unpinned. FIX: gate span at grasp landmark (grip-relevant thresh) + pin raw-s_policy capture + per-iter distribution statement.
- **CH3 HIGH:** center-blend chimera = policy-drifted-center + rigid expert-span (+guard-clamped) = pose neither agent commands. %9's purification only removed the span-SHRINK chimera, not this center-blend one. Off-path, claws at drifted-center±44mm → possible contact into clip/table absent from both pure-expert & β=0 → mis-read as policy divergence (PERSIST A) or noise. FIX: video-verify grasp-landmark contact vs both baselines; if present tag chimera-suspect/VOID; add to risk ledger.
- **CH4 MED-HIGH:** RESOLVE(B) over-claims — VERDICT rule (:69) has no span condition, reads as clearing policy; deploy executes raw β=0 policy (span = whatever policy emits) but test guarded span toward expert → non-conservative on span, missing the GROVE §2.2 conservatism-direction tag. FIX: scope RESOLVE(B) = "clears center-axis budget-tension ONLY; span deployability UNTESTED, non-conservative → needs raw-policy/hi-fidelity confirm".
- CONCEDES: narrow center-axis confound-reduction (span-drift muddies γ⊥) STANDS.
- CC1 note: CH1 is a genuine CRITICAL the whole chain (me/%9/%12) missed — o2+per-arm-guard-2 interaction. Rebuttal ("rate-limit converges over steps") weak: transient deviation IS the correction regime + CH3 contact risk. Direction = ACCEPT CH1 → design needs span fix before build → [VERIFY] leans FAIL/REVISE.

## CC2 (mechanism/correctness) — PENDING
## CC3 (discriminator/read-structure) — PENDING
(CC4 recorded above.)

## CC2 (mechanism/correctness) — RETURNED — **CH1 CRITICAL (=CC4 CH1 INDEPENDENT) + 3 HIGH + MED/LOW**
- ⭐CH1 CRITICAL: per-arm guard-2 (:826-834) breaks span off-path (15/mag_R ≠ 15/mag_L). FIX: common-mode rate-limit. 2 independent challengers.
- CH2 HIGH: t==0 canary (:820-824 abort) + item-9 P1 log ordering vs blend under-specified. CH3 HIGH: t==0 blend uses UN-recentered demo-frame center (grasp_yc/x_grasp set at END of t==0) → dy-sized spurious pull for offset rollouts. CH4 HIGH: β==0 byte-identity needs explicit whole-block bypass; span-basis DISCONTINUOUS iter1/2(expert-span) vs iter3(policy-span).
- CH5-10 MED/LOW: guard-2 effective-mix≠β; c notation ambiguous; recenter⇐dagger_dump; span telemetry must snapshot PRE-blend; solve_ik_dual(L,R) footgun; recenter x,y-only. NO DEFECT: {0-3} scope, index/axis math, o1 hoist byte-safe.

## CC3 (discriminator/read-structure) — RETURNED — **CH1 CRITICAL + 3 HIGH → BLOCK**
- ⭐⭐CH1 CRITICAL (deepest): expert STATE-BLIND/feedforward (_tp=demo-ramp[t], runner:843-850). β changes only INPUT not target → (a) β>0 pulls toward demo ramp → aggregate under-covers drifted states → iter3 divergence = covariate-shift EXPECTED, not budget; (b) feedforward labels ≠ "(off-path)→recover" → β>0 STRICTLY WORSE than β=0 for leg-2; (c) demo-restoring≠expert-correcting-drift; (d) de-risk verdict already flipped when chained. → "leg-2 divergent⟹A" INVALID. FIX: re-scope as data-composition probe OR state-feedback expert.
- CH2 HIGH: same-β⟹shell unsound (shell=f(β,policy)); near-duplicate β=0.5 data → leg-1 trivially non-worsens. CH3 HIGH: zeroed cross-β = discards the crutch-removal MAIN signal; no γ⊥ noise band → can't call divergence-vs-noise. CH4 HIGH: high-INCONCLUSIVE basin (needs leg-1 AND leg-2 agree; ADAPT VOID; de-risk precedent MIXED) → ~2.3 GPU-h likely no resolution.

## CC5 (implementation/INV/contamination) — RETURNED — **2 HIGH + 2 MED + 1 LOW-MED + locked-file CLEAN**
- CH1 HIGH: contamination guard ASSERTED not CODED — dagger_loop main() chains aggregate+retrain UNCONDITIONALLY (no --band-only). "nominal' as reference" auto-safe, BUT the PRIMARY offset=0 band rollout produces kept_states → if run via dagger_loop → contaminates D_base w/ offset=0 rows. FIX: pre-register band orchestration = policy_route_runner.py direct dump-only + standalone dagger_relabel/numpy-diff, NOT dagger_loop main().
- CH2 HIGH: o1 hoist as-worded (:843-855) REORDERS the two solve_ik_dual → β=0 byte-identity now contingent on solver-reorder determinism (unverified). FIX (refines my o1): hoist ONLY _tp arithmetic (:846-851), keep H2 solve (:852) AFTER executed solve; keep guard-2 unconditional; β-gate arithmetic only; ADD byte-identity regression (baseline npz vs β0/eps0). 
- CH3 MED: executed-span has NO runtime INV#2 guard (only training targets do :148) + phase-window index trap (must replicate phase_idx<=3 AND t<_rwp.shape[0]). CH4 MED: o5 eps-independence asserted not structural. CH5 LOW-MED: guard-2 attenuation confounds leg-1.
- ✅ NO DEFECT: locked-file boundary — test_newton_clip_routing.py imported read-only, solve_ik_dual CALLED not edited, GUARD2_M local, anti-revert markers undisturbed. No edit required.

---

# DECIDE (CC1 = %11, all 5 in) — **[VERIFY] = FAIL → REVIEW (escalate %12→Rs)**

## REBUT_OR_ACCEPT
- **ACCEPT CRITICAL (span-break, CC2CH1=CC4CH1, 2 independent):** per-arm guard-2 provably breaks 88mm span off-path = the exact regime β-mix targets. NOT rebuttable. Fixable (common-mode rate-limit) but the KEY DESIGN DECISION as-folded is FALSE-as-executed. My fold (%12 ADOPT + %9 o2) missed it.
- **ACCEPT CRITICAL/HIGH (state-blind-expert confound, CC3CH1):** β>0 reduces drift-induced off-path coverage + feedforward labels don't encode "recover" → "leg-2 divergent⟹A" invalid → test may not resolve A-vs-B at all. Partial-rebut noted (de-risk off-path was ~99% offset-dominated, so coverage-removal is less total than CC3's strongest wording) — but the label-validity + confound STAND and require %9 adjudication; NOT rebutted. This is the deepest finding: it questions whether ANY amount of bug-fixing makes the mini-test resolve A-vs-B.
- **ACCEPT HIGH:** read-structure confound (CC3 CH2/3/4 — same-β unsound, no γ⊥ noise band, high-INCONCLUSIVE basin) + impl (CC2 t==0-frame/byte-identity-discontinuity; CC5 contamination-guard-uncoded/hoist-reorder; CC4 telemetry-off-distribution/center-blend-chimera/RESOLVE-overclaim).
- **ACCEPT MED/LOW:** detail fixes (CC2 CH5-10, CC5 CH3/4/5, CC4 minor).
- **CC6 NHA = HOLD, argument SOUND** (epistemic-only value, close-declaration proposer-certified-equivalent devplan:136) — but re-opens D-A = Rs 専権 (already decided mini-test-first node:140 + re-authorized today) → SURFACE to Rs, not unilateral NO_ACTION by COORD.
- **Clean (no defect):** locked-file boundary (CC5), {0-3} scoping (CC2), narrow center-axis confound-reduction (CC4 concession).

## NO_ACTION_EVALUATION
CC6's (c) close-declaration = proposer-certified equivalent for the mini-test's epistemic-only value (devplan:135/136/207). The debate additionally found the mini-test likely CANNOT reliably deliver even that value (CC3CH1 confound + CC3CH4 high-INCONCLUSIVE). → NO_ACTION (close-declaration) is MORE attractive than a redesign. BUT the mini-test-vs-close = D-A = Rs decision, already made + re-authorized → COORD cannot unilaterally NO_ACTION an Rs strategic decision.

## DECIDE
**[VERIFY] = FAIL** (multiple accepted CRITICALs). Do NOT build/fire as designed. rollout HALT stays. Escalate %12→Rs as REVIEW with 2 paths:
- **(A) REVISE + rebuild:** common-mode rate-limit span-fix + resolve the state-blind-expert validity (state-FEEDBACK expert = MAJOR redesign ≈ a different experiment, OR re-scope to a data-composition probe that does NOT claim to resolve A-vs-B) + establish a γ⊥ noise band + code the contamination guard (standalone band orch) + t==0/byte-identity/hoist-arithmetic-only fixes. Substantial rework of code that is throwaway (non-portable to P2).
- **(B) CLOSE R1 via D-A "plateau + A-vs-B OPEN (logged)":** NHA-recommended, proposer-certified equivalent, zero-GPU/zero-code; A-vs-B resolvable later as a natural byproduct of the P2 whole-route env (portable). Rs's D-A call.
- **CC1 recommendation = lean (B).** Rationale: CC3CH1 means the mini-test may not resolve A-vs-B even after the span fix (the deepest CRITICAL is a validity problem, not a bug); combined with the NHA's sound HOLD + epistemic-only value + high-INCONCLUSIVE risk, a major redesign of throwaway code is poor expected value. If Rs wants A-vs-B closed now, the honest minimum is (A)-rescope-to-data-composition-probe (drop the A-vs-B claim). D-A = Rs decides; %12 DECIDE-review first.
- The [VERIFY] gate did its job: caught 2 CRITICALs + a validity problem BEFORE ~2.3 GPU-h + a throwaway L3 build. This is a GOOD outcome (prevention), not a setback.

