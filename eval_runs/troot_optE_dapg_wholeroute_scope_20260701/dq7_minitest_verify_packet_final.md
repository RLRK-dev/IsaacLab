---
doc_class: reference
---
> ⛔ SUPERSEDED / HISTORICAL (as-of 2026-07-11, COORD2 vault-audit) — tracking SSOT = LEDGER VL1 (`00-DESIGN-STATUS-LEDGER.md`). optE-DQ7-offpath: R1 CLOSED (LEDGER row47), historical. Do not copy live values — pointer task_config.py / successor docs.

> **Archived by %11 (COORD) at R1 close — Rs decision (B), 2026-07-05 10:17 JST.** DQ7 mini-test terminated at 0 GPU per 5体 [VERIFY] = FAIL (2 CRITICAL: span-break [per-arm guard-2] + state-blind-expert confound; + high-INCONCLUSIVE/validity). Content below unchanged from the scratchpad working copy.

# [VERIFY] packet — DQ7 mini-test β-mix + multi-offset (COORD %11 PROPOSE for 5体 debate)

Status: DRAFT-for-READY. L3 (VERIFY 5体 pre-debate). Fire NOT started (rollout HALT). 0-commit.
Grounding (anchor set, cited): node state.md :112(3-regime LOCK)/:140(19:33 design)/:146(09:10 JOINT, banked 231639c0d1) ; devplan V2 §0/§4.3/§5-R1 ; DQ7 DECIDE 170b905575 (per-step relabel + in-scene IK) ; RS71 §0 INV#1-5.

## PROPOSE (change plan — NOT a verdict; no confidence/pre-defense per §運用15)

### Goal
Resolve A-vs-B (de-risk left OPEN): A = real budget-tension (→ (i)-RL, Rs専権) / B = β=0-single-offset-minimal-artifact (→ full-build reconsider). Add the 2 real-DAgger mechanisms the β=0 minimal omitted.

### Change 1 — β-mix (CODE ADDITION, the L3 core)
- dagger_loop.py: `--beta FLOAT` (default 0.0); when is_rollout append `--beta` to runner_cmd(:111 area). ~6-10 LOC.
- policy_route_runner.py: main() `--beta` arg (default 0.0) + ctx["beta"] + mix block in _control_loop + verdict log(β, n_mixed). ~25-50 LOC.
- Mechanism (%9 o1-o4 CORRECTED — my earlier "after :852" was WRONG): (o1) HOIST expert `_tp` computation (currently :843-855, AFTER the executed solve :838 = pure logging) to BEFORE the executed solve. (o2)⭐ ORDER = blend → guard-2(:830-834, 15mm rate-limit) → SINGLE solve_ik_dual, applying guard-2 to the BLENDED target (placing mix AFTER guard-2 silently disables the rate-limit on expert-pull steps where the expert target is >>15mm from ee = restoring itself; uniform per-step 15mm semantics, restoring realized over multiple servo steps = E15-consistent). (o3) H2 feasibility logging (ik_resid_tstar_series :853) stays on RAW _tp (blend-target measurement changes instrument meaning). (o4) β==0.0 BYPASSES the entire blend block (byte-identity + iter3 = true policy exec = de-risk-comparable endpoint).
- β-schedule (%9 3b PIN): **β = (iter1 0.5, iter2 0.5, iter3 0)** + ADAPT rule (iter1 off-path p90<2mm = shell too small → iter2 β=0.25 ONCE, loud log; leg-1 same-β comparison then VOID). Rationale: iter1→iter2 same-β = comparable visited-shell radius → γ⊥ monotone = pure budget effect (no β-shift confound); iter3 β=0 = de-risk-condition endpoint = direct B-falsifier. (Ross 0.5→0.25→0 inferior = all-3-points β-confounded; see KNOWN_ALTERNATIVES(f).)
- ⭐ KEY DESIGN DECISION (span-preservation, INV#2) — %12 ADOPT-direction (09:31, debate attacks; %9 verifies the ②logic):
  - naïve per-arm blend β·expert+(1−β)·policy does NOT preserve 88mm span when expert≠policy (‖β·(A_R−A_L)+(1−β)·(B_R−B_L)‖<88mm by triangle-ineq unless collinear; disagreement LARGEST off-path = where β-mix acts; = B1's span 122.9→grip 0N recurrence risk).
  - ADOPT = blend the COMMON-MODE CENTER c=(EE_R+EE_L)/2 by β, keep the 88mm span-vector FIXED (mix corrective translation only; span is an invariant, never blended).
  - span-vector source = **expert pair, same step** (expert is span-preserving by construction :850-851 → zero new mechanism; policy-derived rejected = off-path unreliable).
  - ②discriminator PURIFICATION (not pollution): γ⊥/off-path instruments read the center-tracking axis; span-drift would pollute EE-position → confound γ⊥ read → the center-only projection CLEANS the discriminator. (%9 to verify this logic.)
  - pre-register note (honest scope): this mini-test's A-vs-B measures **center-axis restoring**; the span axis is structurally guarded, not measured.
- INV: #3 DiffIK-only PRESERVED (blend IK-solved, no teleport) / #5 no-kinematic-trick PRESERVED (jq from solve_ik_dual) / #2 span — handled by span-preserving blend above (the RISK if naïve).
- Backward-compat: β=0.0 → mix = policy-only = current byte-identical (demo-replay EXEMPT path unaffected).
- Scope: expert target only for phase<=3 & t<_rwp.shape[0] (:845) → β-mix naturally {0-3}-scoped = matches --truncate-after-phase 3.

### Change 2 — multi-offset {−20,+10}
- No code change. Existing demos step2_offset_z0_m20 + step2_offset_z0_p10 (both present, E4'-seat-quality screened: −20=29/29, +10=27/27 → both seatable per 19:33 spec). Run mini-test over BOTH offsets → addresses single-offset(−20) confound of de-risk.

### Change 3 — rider-1 nominal' band leg — ✅ RE-SPEC'd (%9 09:38, option 1; PENDING RESOLVED)
- %9 re-spec (owns the earlier zero-code false premise; my 3 findings all CONFIRMED on-disk by %9): ε mechanism = **--nominal-eps** flag (default-off, ~5-10 LOC, bundled in the same L3 β-mix diff, locked-file untouched, FLOAT direct = rounding moot). ε = **executed EE-target CENTER, deterministic per-step +0.5mm common-mode, dy axis (+y), same axis as mini-test offset** = forced-response sensitivity probe (o5: --nominal-eps block INDEPENDENT of the β-blend block — nominal' leg = β=0 + eps, so o4's β=0-bypass kills blend while eps stays; common pre-guard-2 ordering, 0.5mm≪15mm so guard no-op but uniform).
- measurement re-definition (over-claim guard): determinism (my 3 findings) means run-to-run stochasticity does NOT exist; the question is trajectory sensitivity to a small config diff (deterministic chaos). ε contraction (servo-dominated) → band ~0.5-1mm = (I) / amplification (cable-contact nonlinear) → band large = (II).
- 3-way (thresholds 2/5mm kept, labels revised): p90≤2mm → **(I) RESOLVED-smooth/common-mode** (%9 07-04 pin) / p90≥5mm → **(II) HOLDS-sensitivity-dominated** (bucket read unreliable, trajectory-direction legs only) / 2-5mm → **(III)** band-exceeding readable. Falsifier: eps flag set + byte-identical → wiring bug → STOP. contamination guard: nominal' rows = band-measurement ONLY, NOT mixed into aggregate/training (dump only). Band leg does NOT block the main γ⊥-verdict.
- band = dagger_relabel obs-distance mm (phase-align :133-135 + length guard :118-121, %9 citation verified), matched-step per-step p50/p90/max, n=1 pair (~15-16min GPU).

### Files + DESIGN-GATE (2a %9 CONFIRM)
- Touch list: dagger_loop.py, policy_route_runner.py (2 files, ~30-60 LOC + rider-1 ε ~5-10 LOC). ⭐ caveat-iii CONFIRM: **test_newton_clip_routing.py = Rs-LOCKED, NOT in touch list** (β-mix + ε = runner + dagger_loop only). NOT task_config.py. Anti-revert markers (_verify_anti_revert_markers :137) undisturbed.
- DESIGN-GATE (/reward-design) = **SKIP CONFIRMED lawful (%9 2a)**. caveat-i void-if-drift: if impl touches env / task_config / success-predicate → skip invalid, re-triggered (L-RETRIAGE). caveat-ii β-schedule biasing A-vs-B read = out of design-gate scope → %9 metric-plan + L3 5体 cover.

## Core SSOT references (fixed list)
task_config.py (span/offset params) / SOMA.md (goal) / CLAUDE.md prohibited (INV#3/#5, control-API, no-kinematic-trick) / node state.md :112/:140/:146 / devplan V2 §4.3(yardstick)/§5-R1 / DQ7 DECIDE 170b905575 / RS71 §0 INV#1-5.

## KNOWN_ALTERNATIVES (+ satisfaction state)
- (a) β=0 minimal — DONE, DEGENERATE (no expert-mix → uncorrected drift → can't distinguish A/B). Superseded by β>0.
- (b) single-offset −20 — DONE, CONFOUND. Superseded by multi-offset {−20,+10}.
- (c) close R1 w/o mini-test — D-A equivalent (Rs choice); cheaper but leaves A-vs-B remnant. mini-test = epistemic-close path.
- (d) straight to (i)-RL / full-8proc — REJECTED (premature; de-risk showed non-robust divergence pre-full-scale).
- (e) DAgger (iii) full — DQ7:106 deferred (state-blind expert at frozen-waypoint). β-mix here IS β-scheduled DAgger, scoped {0-3} where expert IS restoring (Fact A).
- (f) Ross 2011 STOCHASTIC per-step switch (execute expert pair w.p. β) — REJECTED (%9 09:40): constructively avoids the blend-chimera BUT injects EXECUTION VARIANCE into the 2-3-point monotonicity read of a deterministic pipeline (de-risk byte-identical) → breaks read stability. Deterministic center-blend chosen instead.

## rider-2 — runner-path enumeration + margin (CORRECTED)
Enumeration: mini-test (dagger_loop) rollout — policy OR demo-replay — uses **_control_loop ONLY** (evidence: :447-448 --policy⊥--macro-ik-replay assert / :676-682 macro-XOR-control dispatch / dagger_loop :94-114 never sets --macro-ik-replay / :1195 3-mode label). It NEVER enters _macro_ik_loop.
Margin table (%12 DECISION (a) 2026-07-05 09:27; (b) macro-ik-replay leg NOT added):
| assert | path | on mini-test? | dy=−20 | dy=+10 |
|--------|------|---------------|--------|--------|
| :913 (offset-aware _tol=0.010+|dy|/1000) | _control_loop | **YES** | tol=30mm / shift~5mm / **margin~25mm SAFE** (perturbed_m20 exit0 EMPIRICAL) | tol=20mm / shift~2.5mm / **margin~17.5mm SAFE** |
| :1021 (fixed ±10mm) | _macro_ik_loop | **NO (moot-for-minitest)** | shift~5mm / margin~5mm TIGHT (informative only) | shift~2.5mm / margin~7.5mm (informative) |
- :913 is the ONLY grasp_yc assert the mini-test traverses; it is offset-aware and SAFE with large margin at both offsets. :1021 is off-path (informative row retained per %12).
- CORRECTION (filed+accepted %12 09:27, 3/3 spot-verified): prior "perturbed_m20 exit0 = :1021 未 trip" was wrong — that policy rollout hit :913, not :1021.
- 2c inputs (%12): :913 margin table must also cover {+0.5ε (rider-1, mechanism pending), β-mix intermediate executed-target}. Both perturb grasp_yc only slightly — ε center-shift +0.5mm and the β-blend executed-target both stay near ~150mm (β blends expert~150 with policy~150; span fixed) → _tol margin preserved by wide margin. FINALIZE row values once rider-1 ε-mechanism locked by %9.

## Adversarial scenarios (for 5体 Challengers)
1. Span-break (INV#2): naïve blend shrinks span off-path (see KEY DESIGN DECISION). → span-preserving blend required.
2. Read-framework validity: β-blended visited-states differ from policy-only distribution. → %9 3c RESOLVED: γ⊥ = offline probe (blend-independent); PRIMARY read = leg-1 (iter1→iter2 same-β) + leg-2 (iter3 β=0 endpoint); cross-β direction (iter2→iter3) = ZERO verdict weight (annotation only).
3. β masks divergence (false-B): high β = expert-steered looks convergent. → %9 3c STRUCTURALLY CLOSED: RESOLVE(B) REQUIRES leg-2 (iter3 β=0 = raw policy exec) non-divergent; expert-steered apparent convergence alone ≠ RESOLVE.
4. IK-infeasible blend: convex blend of 2 feasible targets may be IK-infeasible (non-convex IK) → NaN → ik_fail inflation at high β. Handled by E8 (log+continue+tag) but monitor.

## VERDICT rule (%9 3c :45)
- PERSIST(A) = leg-1 WORSENS **AND** leg-2 (iter3 β=0) DIVERGENT (under off-path-material) → real budget-tension → (i)-RL (Rs専権).
- RESOLVE(B) = leg-1 NON-worsens **AND** leg-2 NON-divergent (same condition) → β=0-artifact → full-build reconsider.
- else = INCONCLUSIVE ladder (3-regime 16:14 LOCK → seed-repeat → Rs).
- materiality gate: floor-unmet PERSIST/RESOLVE → INCONCLUSIVE-underpowered.

## CONSOLIDATED PRE-REGISTER (%9 6 項 verbatim fold)
1. PRIMARY read: leg-1 (iter1→2 same-β γ⊥ direction) + leg-2 (iter3 β=0 endpoint qualitative divergence). PERSIST/RESOLVE/INCONCLUSIVE = VERDICT rule above.
2. materiality: per-iter off-path fraction + p50/p90 required; floor-unmet → INCONCLUSIVE-underpowered.
3. band leg: --nominal-eps (L3 diff bundled, flag-gated default-off) nominal' = executed-center per-step +0.5mm (dy) pair ×1; rows band-measurement ONLY (aggregate-excluded). 3-way: p90≤2mm→RESOLVED-smooth/common-mode / ≥5mm→HOLDS-sensitivity-dominated / 2-5mm→band-exceeding readable. gate = contingent immaterial-diagnostic + %9 07-04 pin only, main-verdict-independent. falsifier: eps flag set + byte-identical → wiring bug → STOP.
4. span telemetry: per-step ‖s_policy − s_tp‖ (s=tgt_r−tgt_l, mm) log, p50/p90/max, INFORMATIVE (p90>10mm = caveat row). iter3 β=0 = raw policy exec → span pathology physically manifests → endpoint supplies measurement. cost ~0.
5. β/iter + n_mixed in verdict log; cross-β direction annotation only. ADAPT rule (iter1 off-path p90<2mm → iter2 β=0.25, ONCE, loud) when fired → leg-1 VOID noted.
6. 3-regime immaterial-diagnostic (16:14 LOCK) + seed-repeat contingency = unchanged inheritance. null-beat intersection = report metric (no verdict weight).

## GPU budget (%9 3b check): 3 iter × 2 offset × ~15.5min ≈ 93min + band pair ~31min + retrain 90s×3 + og offline ≈ ~2.1-2.3h ✓ (1-3h envelope, timebox ≤2d). code = β-mix ~30-60 LOC + --nominal-eps ~5-10 LOC (same L3 diff, 2 files).

## Gate chain
[DEFINE]✅ [L-TRIAGE]✅L3(%12 CONCUR) [CHECK]✅ → **[VERIFY 5体]◀ THIS packet, LAUNCHING** → [RULE-CHECK st2]⬜ → --rs-go RS-GO-DAGGER-ROLLOUT + %12 verify + %9 metric + Rs loud-notify⬜ → fire⬜. rollout HALT until fire GO.
Division: %11 build-prep(this) / %9 design-verify (✅ READY-for-5体 09:40) / %12 verify (DECIDE review + fire authz).
%9 design-verify = READY (all opens resolved: span-preserving center-blend ADOPT / β=(0.5,0.5,0)+ADAPT / discriminator 3c read-structure / rider-1 --nominal-eps). debate 主攻撃点 (per %12) = span-projection purification logic + β-schedule read structure + o2 ordering.
