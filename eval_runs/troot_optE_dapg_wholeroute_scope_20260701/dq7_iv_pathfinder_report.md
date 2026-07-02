# DQ7 stage (iv) pathfinder report — restoring-augmented BC (denoising)

**COORD %11 · 2026-07-03 07:09 JST (same-turn date) · 0-commit.** CP-(iv)-4 mechanical judgment per `charter_dq7_stage_iv_coord.txt` §3 + `dq7_iv_mini_spec.md` v1.1 (%12-approved, U1-U11). final_L = **L2** (Rs demotion 承認 07:0x「推奨でよい」; 事後 層2 免除 [pre-debate 済], 層3+層5 不変). Instrument = committed `og_offline_gate.py` UNCHANGED. Rollout prohibition held; GPU-1 only; §運用14 = N/A (offline).

## VERDICT: Outcome B (structural finding — Rs-escalation material; %12/Rs adjudicate)
**Validity precondition v1 UNMET across all 3 pre-registered ladder steps → per charter §3 the A/B judgment is not rendered as GO; the mechanical A/B on the closest-to-valid step-3 policy is reported INFORMATIVE and every Outcome-A bar is UNMET.** The pathfinder answer: **synthetic co-move-manifold augmentation does not teach the restoring term to the BC policy within the on-path-fit budget** — the two are in tension (enough augmentation to move γ⊥ destroys the clean fit; little enough to preserve the fit does not move γ⊥ to bar).

---

## §1. Validity ladder (v1 = whole-demo val ≤ 0.001318 = 2× baseline 0.000659) — UNMET 3/3

| step | cfg | aug rows | aug-BC whole-demo val | vs bar 0.001318 |
|---|---|---|---|---|
| 1 | K=2, ee{0,1}[2,20]/ee{2,3}[2,8]/ee{11}[2,20]/seg[2,10] | +7257 | 0.001943 | **FAIL** (2.95× baseline) |
| 2 | K=1, ee[2,10]/[2,6]/[2,10]/seg[2,6] | +3658 | 0.002363 | **FAIL** (3.59×) |
| 3 | K=1, [2,5] all legs | +3662 | 0.001439 | **FAIL** (2.18×, closest) |

**Non-monotonic dial-back = inherent trade-off (not an over-perturbation artifact, %12 framing):** reducing K+magnitude step1→step2 made the clean val **WORSE** (0.001943→0.002363), not better. Only step-3's aggressive narrowing to [2,5]mm dented it (0.001439) but still exceeded the 2× bar. ⇒ the on-path degradation is a ~2.2-3.6× **floor** roughly insensitive to (even anti-correlated with) moderate dial-back — inherent to mixing off-manifold denoising targets into the BC objective, NOT a tunable magnitude problem. Ladder exhausted (3/3) → STOP per pre-registration. train_loss tracks val (aug-BC-s3 train 0.001198 ≈ val 0.001439 = not overfitting; the augmented objective has a higher achievable floor than clean 0.000638).

## §2. Informative A/B on the closest-to-valid policy (step 3) — every Outcome-A bar UNMET
(og on the CLEAN train npz, instrument basis unchanged; `b2_cpE_iv/og_aug_bc_s3/og_gate.json`.)

| Outcome-A cell | bar (charter §3) | baseline (CP-E) | aug-BC-s3 | met? |
|---|---|---|---|---|
| γ⊥ GRASP_HOVER {0} | ≤1.249 | 2.497 | **1.680** | UNMET (moved ↓, not to bar) |
| γ⊥ GRASP_DESCEND {1} | ≤0.629 | 1.257 | **0.906** | UNMET (moved ↓) |
| γ⊥ GRASP_CLOSE {2} | ≤0.521 | 1.041 | **1.046** | UNMET (did NOT move) |
| γ⊥ LIFT {3} | ≤0.528 | 1.055 | **1.051** | UNMET (did NOT move) |
| C2_REGRASP ee-only (b) | ≤0.487 | 0.973 | **0.902** | UNMET (barely moved) |

**Prediction table CONFIRMED (mini-spec §5):** {0,1} = "↓ strong" (moved, direct 6-dim/R ee-leg) but not to the 50%-baseline bar; **{2,3} = "RISK cells, generalization-only" (did NOT move)** — exactly as predicted: the ee-leg at {2,3} perturbs only L-dims, and V1 (the direct {2,3} R+seg supervisor) was held OFF per U1, so those probe columns got no direct teacher → γ⊥ unchanged. seg-follow (informative) 0.282→**0.349**, moving toward the U4-derived **~0.67 faithful ceiling** as predicted (still < band-lo 0.8).

## §3. Attribution — null_beat −0.476 is INCONCLUSIVE (aug-null ignore-obs collapse), NOT a BC restoring failure
Beat = worst{movable γ⊥ ∪ C2 ee-only}: aug-BC-s3 worst **1.680** vs aug-null-s3 worst **1.204** → null_beat **−0.476** (bar +0.15; baseline was −0.261). Naïvely the null "beats" the BC. **Own/off-slice split (U5, %12-requested — `og_b` on (+10,0) own-slice vs the other 8 offsets):**

| policy | OWN-slice (+10,0) worst-mov γ⊥ | OFF-slice (8 offsets) worst-mov γ⊥ | whole-demo val |
|---|---|---|---|
| aug-BC-s3 | 1.685 | 1.680 | 0.001439 |
| aug-null-s3 | 1.198 | **1.204** | **0.018994 (29× BC)** |

**The null's low γ⊥ is UNIFORM own≈off (1.198≈1.204) — a GLOBAL ee-insensitivity, not a localized restoring around its training slice.** Combined with its whole-demo val 0.018994 (= 29× the aug-BC = wrong targets everywhere), this is the pre-registered **ignore-obs collapse** (mini-spec §3 / U5 pre-committed diagnostic cell): the null wins the naïve worst-γ⊥ beat by IGNORING obs (degenerate low γ⊥ + high val), not by genuine restoring. The aug-BC's HIGHER γ⊥ reflects a policy that actually RESPONDS to its input (fits 9 offsets) = correct behavior penalized by the confounded metric. ⇒ **(c)-fail is INCONCLUSIVE (attribution artifact), distinct from the genuine (a)/(b) UNMET.** The primary structural finding rests on validity + (a) + (b), not on the confounded beat.

## §4. Structural interpretation (the pathfinder's answer)
- **Genuine (not confound):** even the mildest effective augmentation ([2,5]mm) (i) exceeds the 2× on-path-fit budget (v1 3/3) and (ii) fails to move movable γ⊥ / ee-only to the restoring bar. The on-path/off-path tension is inherent to the denoising objective.
- **{2,3} untouched = by design** (V1 OFF, generalization-only) — a KNOWN, pre-registered gap, not a new failure. A V1-ON variant would directly supervise them (%9-consult toggle), but v1 (on-path budget) would likely worsen further.
- **(iv)-vs-(ii) discriminator STANDS (does NOT auto-doom (ii)):** (iv) is **model-consistent** (linear co-move approx); (ii) gets consistency from **physics** for free. So (iv)'s Outcome B does not prove (ii) fails — physically-generated off-path frames may carry restoring signal (iv)'s synthetic frames couldn't. BUT (iv) surfaces a tension **(ii) will also face**: physical detour recordings ALSO add off-path rows to the BC objective → the same on-path-fit degradation risk (ii)'s convert-time outbound mask + recovery-frame clustering must be watched against this budget. Net: (iv) Outcome B **weakens the prior** that cheap imitation-only restoring supervision suffices, and pre-flags the on-path/off-path budget conflict for (ii).

## §5. Carries (unchanged) + conservatism direction
- **Band-recalibration → (ii) charter (U4, unchanged):** faithful C2_REGRASP pair seg-follow ceiling ≈ mean(R_x 1, R_y 0, R_z 1) = 0.667 < band-lo 0.8 → the B2 §3.3 [0.8,1.2] pair band may be unreachable by faithful behavior. Rs 専権; decide before the (ii) GO gate runs. (iv) itself unaffected — seg-follow is informative here.
- **Conservatism (§運用15):** this is a **conservative-definite STOP** (the augmentation FAILS to reach GO even under the teach-to-the-test-favorable condition where the gate probes the same co-move family the augmentation trained on — the mildest, most-charitable magnitude; a harder/independent test would not do better). The (c) confound is flagged non-conservative-for-the-null (ignore-obs inflates the null's apparent restoring) but is EXEMPTED from the finding.
- **Rs escalation = %12** (per charter §1: Outcome B → 追加 spend なしで %12 → Rs). Decision options for Rs (record-only, not selected): (A) proceed to (ii) accepting the on-path/off-path budget risk it flags; (B) relax the v1 2× bar (moving-goalpost — Rs-only) to re-open (iv); (C) V1-ON diagnostic (%9 consult) for the {2,3} columns; (D) re-scope. NOT my call.

## Provenance
- ladder aug datasets: `b2_dataset_v2_aug{,_s2,_s3}/` + `b2_cpD_aug_null{,_s2,_s3}/` · policies `b2_cpE_iv/aug_{bc,null}{,_s2,_s3}/` · og `b2_cpE_iv/og_aug_{bc,null}_s3/og_gate.json` · train logs `b2_cpE_iv/aug_*_train.log`.
- baseline instruments: `b2_cpE_og/bc/og_gate.json` (γ⊥ 2.497/1.257/1.041/1.055, pair 0.282/0.973, null_beat −0.261) · `b2_cpD_report.md` (clean BC whole-demo val 0.000659).
- converter: `route_demo_to_bc.py` augment_b2 (+189/−1, regression byte-identical b3472e8c/0ed5149c, locked-4 0-diff). og UNCHANGED.
