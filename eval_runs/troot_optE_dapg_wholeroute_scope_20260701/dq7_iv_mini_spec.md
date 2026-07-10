---
doc_class: reference
---
> ⛔ SUPERSEDED / HISTORICAL (as-of 2026-07-11, COORD2 vault-audit) — tracking SSOT = LEDGER VL1 (`00-DESIGN-STATUS-LEDGER.md`). optE-DQ7-offpath: R1 CLOSED (LEDGER row47), historical. Do not copy live values — pointer task_config.py / successor docs.

# DQ7 stage (iv) mini-spec v1.1 — restoring-augmented BC (denoising) 0-GPU pathfinder

**COORD %11. v1.0 = 2026-07-03 06:07 JST · v1.1 = 2026-07-03 06:5x JST (same-turn date).** CP-(iv)-1 deliverable per `charter_dq7_stage_iv_coord.txt` §4. 0-commit; build starts only after %12 conformance check PASS → stage2 rule-check. **A/B boundary numbers = charter §3 verbatim, UNCHANGED (not restated-modified here).**

**v1.1 provenance:** 5体 CC Debate (CC2-6) → `DQ7_IV_MINISPEC_DEBATE_DECIDE.md` (%12, 06:3x). Package v1.0 + %12 M1-M4 = **FAIL** → amended plan **APPROVED conditional on this v1.1**. This v1.1 folds U1-U11:
- **U1 (V1=OFF):** my v1.0 default RESTORED (%12 M1 V1=ON withdrawn; CC6 representativeness + CC3 authority). V1 = pre-declared post-Outcome-B diagnostic toggle only (§1.2).
- **U2 (final_L=L3):** my v1.0 L2 OVERTURNED (4/5 panel + E15 retraction precedent `B_BC_BUILD_SPEC.md:159`). §8.
- **U3 (per-leg magnitude table + tangent projection), U4 (faithful per-axis seg-leg label), U5-U11:** folded in the sections below.

**Grounding (self-read, cited — U9 corrected lines):** `DQ7_OFFPATH_SCOPING_COORD2.md` §1/§3/§4.2-(iv)/§5 · `DQ7_CONSULT_PCT9_VERDICT.md` 条件1-3 · `DQ7_IV_MINISPEC_DEBATE_DECIDE.md` U1-U11 · `og_offline_gate.py:33-38` (constants DR_MOVABLE/CABLE_ANCHORED/L_HELD_PHASES/GPERP/PAIR/NULL_BEAT_MARGIN) · `:34`/`:37`/`:407-413` (band scope) · `:97-140` og_b co-move (dwp tangent) · `:252-265` pair per-axis (R-response, **3-axis mean** at `:265`) · `:425-441` _beat_metric+null_beat · `test_newton_clip_routing.py:4377` (`_La` L frozen) / `:4405` (`_R_ty = c2y+GHS` = 88mm HELD, INV#2) · `route_demo_to_bc.py:91` (task_config lazy leaf read), `:266-289` (obs layout, wp = next-waypoint abs target) · baseline = `b2_cpE_og/bc/og_gate.json` (%11 re-derived: 2.497/1.257/1.041/1.055, pair 0.282/0.973, null_beat −0.261) + `b2_cpD_report.md` · 語法 = 9 train-fit + 2 whole-demo-val + 3 held-out-hull (%9 調停).

---

## 1. Sampler (og_b co-move model reuse — 2 legs, phase-scoped, faithful per-axis labels)

Operates on committed `b2_dataset_v2/bc_dataset_abs.npz` (obs[27], a[6]): `ph=argmax(obs[12:27])`, `wp=_abs_decode(a,ph,union_affine)` (round-trip 0.000, %11-verified). Per clean row in a gated phase emit K augmented rows `(obs′,a′)`; magnitude `m` per the U3 **per-leg** table; direction `d` per §2.

### 1.1 Legs (U3 magnitude + U4 faithful label)

| leg | phases | obs′ perturbation | label rule (U4 faithful) | mag (U3) | teaches |
|---|---|---|---|---|---|
| **ee-leg** | {0,1} HOVER/DESCEND (pre-close = free dims) | `d`∈R⁶ on EE[0:6], **tangent-⊥ projected** (§1.3), seg[6:9] fixed | **a′=a (preserved)** | log-U[2,20]mm | γ⊥{0,1}→0 |
| **ee-leg** | {2,3} CLOSE/LIFT (holder=R) | `d`∈R³ on **non-holder L[3:6]**, tangent-⊥, seg fixed | preserved | **log-U[2,8]mm** | γ⊥{2,3} L-cols→0 |
| **ee-leg** | {11} C2_REGRASP (holder=L) | `d`∈R³ on **acting-R[0:3]**, tangent-⊥, seg fixed | preserved | log-U[2,20]mm | ee-only 0.973→↓ |
| **seg-leg** | **{11} ONLY** | `d`∈R³ on seg[6:9] **AND holder-L[3:6]** co-moved (og pair-probe obs pattern `:252`) | **faithful (U4): a′ = encode(wp′), wp′ = wp with R_x+=d_x, R_z+=d_z; R_y AND L[3:6] PRESERVED** | **log-U[2,10]mm** | seg-follow 0.282→~0.67 (INFORMATIVE, §5/U11) |

**U4 faithfulness (code-grounded, %11+%12 verified):** the scripted C2_REGRASP expert re-targets **R to the ACTUAL cable X,Z at R's lane** (`test:4404` `_kR` argmin → `_cRx,_cRz`) but **HOLDS R_y = c2y+GHS = 88mm** (`:4405` `_R_ty`, INV#2 span-preserving) and sends **L to a FROZEN grip `_La=(c2x,c2y−GHS,·)`** (`:4377`). So faithful per-axis cable-following = **R_x YES, R_z YES, R_y NO (held), L NO (frozen)**. The v1.0 all-axis co-move was WRONG — it would teach L self-following (integrator-class, at the phase whose closed-loop probe already diverges: og_bprime C2_REGRASP contracted=false) and fabricate R_y-following the expert holds at 0. Reject rate under the faithful rule (only R_x[box 38.5mm]/R_z[49.6mm] move, %11 re-measured seed0): 2mm 100% / 5mm 95.2% / 8mm 89.4% / 10mm 80.7% keep@|a′|≤0.95 — comfortable at the [2,10]mm cap (the earlier 30mm-floor truncation was the v1.0 all-axis artifact, now moot).

### 1.2 V1 (default OFF — U1; post-Outcome-B diagnostic toggle only)
V1 = an extra co-move-obs/label-preserved leg at {2,3} (would directly supervise the holder-R+seg probe columns). **OFF** (CC6: keeping {2,3} generalization-only preserves the load-bearing question — (ii)'s fate — at 0 GPU; V1-ON would over-predict (ii); CC3: a third leg = charter amendment needing %9 consult). V1 is **gate-MODEL-consistent, NOT physically consistent** (L-coupling unmodeled at dual-hold — CC5 wording). Toggle path if needed: attributable Outcome-B diagnosis + one-message %9 consult + spec/prediction re-issue. Not in this build.

### 1.3 Tangent-orthogonal projection (U3 / CC5 tangent-aliasing) — label-PRESERVED ee-legs ONLY
For the 3 ee-legs (label preserved), a sampled `d` with a component along the local path tangent would move FORWARD along the demo path, where the "correct target unchanged" assumption is FALSE (the next waypoint does change). Fix per row: sample `d` in the leg subspace → **project out the local tangent** `dwp = wp[t+1]−wp[t]` (og_b's dwp construction `:99-101`, restricted to the leg's dims) → renormalize → apply the §2 25°-axis rejection. Seg-leg is EXEMPT (its label co-moves by construction — following IS a target-moving signal, not a preserved one).

---

## 2. m1 — direction split / magnitudes / rate (pre-registered)

- **D_heldout = the gate's probe family** = axis-aligned singles {±e_k} (og_b/pair perturb one axis at a time, `:97`/`:252-260`). **NEVER trained** (anti-teach-to-the-test).
- **D_train** = uniform random unit `d` in the leg subspace, tangent-⊥ (preserved legs), **rejection: discard if max_k|d·e_k|>0.906 (≥25° from every probe axis)**. Gate then measures on directions training never saw.
- **Magnitudes = per-leg (U3, §1.1 table):** ee{0,1}=log-U[2,20] / ee{2,3}=log-U[2,8] (< 10.0mm DR-lattice spacing, span-stretch physics) / ee{11}=log-U[2,20] / seg{11}=log-U[2,10] (union-box truncation + (ii) ≤10mm mirror). All bounds mm.
- **Rate:** K=2 per applicable leg per clean gated row. Gated rows (%11-measured): {0}466 {1}360 {2}191 {3}540 {11}1063 = 2620 ee-leg + 1063 seg-leg → **+~7366 aug rows** on 6930 clean (train ~2-4 min GPU-1).
- **Union-box guard:** any row with |a′|>0.95 → **REJECT + loud per-(leg×magnitude-bin) count** (preserves frozen-affine hull; no affine re-fit). Counts → meta + report (U3/U7).
- **Retry ladder (charter §3, validity 未達時 max 3):** ①K=2 per-leg table above → ②K=1, ee halved-tail [2,10]/[2,6]/[2,10], seg[2,6] → ③K=1, [2,5] all → still failing = STOP→%12.
- Sampler seed = 0 (meta-recorded).

---

## 3. m2 — augmented-null + beat formula (in-instrument) + U5 attribution

- **augmented-null** = CP-D replicate-null protocol verbatim ((+10,0)×9 `null_dataset.npz` 565717c0, same union affine, arch (128,128), seed 0, ep2000, GPU-1) + **the IDENTICAL augmentation** (same legs/phases/K/per-leg magnitudes/direction rule/tangent-proj/seed).
- **Beat** = committed `_beat_metric` (`og:425-441`): worst over {γ⊥ movable 0-3} ∪ {C2_REGRASP ee_only}; `null_beat = worst(aug-null) − worst(aug-BC) ≥ +0.15` via `--null-og`. Both og runs on the **CLEAN committed train npz** (instrument basis unchanged, B2 precedent). **§3-sentence correction (U5/CC4):** the aug-null is NOT "probed on rows it never fit" — its (+10,0) source path = **1/9 of the clean probe rows**; the beat isolates cross-offset restoring (BC, 9 offsets) vs single-path restoring (null, 1 offset replicated), NOT unseen-vs-seen.
- **U5 both-failure-direction prediction + reporting:** the report predicts BOTH (c)-failure modes and includes (i) aug-null **full per-cell γ⊥/pair table**, (ii) **own-slice vs off-slice split** (BC's own training offsets vs held-out-direction cells), (iii) **per-leg aug counts for BOTH arms** (volume note if >10% R/L mismatch). Pre-committed diagnostic cell: **"(c)-fail ∧ (a)(b)-pass = attribution INCONCLUSIVE"** (aug-null ignore-obs collapse | null-coverage geometry) — distinct from mechanism failure; recorded, not silently folded into A/B.

---

## 4. Pipeline / touch-points / regression / U7 meta / U10 gate-map

1. `route_demo_to_bc.py` **additive post-processor branch** (`--b2-augment <cfg>`; default-off; convert_b2/convert internals untouched; `:91` task_config lazy leaf read unaffected): reads committed npz → emits **`bc_dataset_abs_aug.npz`** (U7 distinct basename, `_aug` schema tag).
2. **U7 meta contract** (`bc_dataset_abs_aug_meta.json` = copy base meta + truthful overrides): `n_rows_clean` / `n_rows_aug`, `{V1:false, ladder_step, K, per_leg_magnitude_ranges, rejection:{axis_cos:0.906, deg:25, tangent_projection:true}, sampler_seed:0, source_npz_sha256, converter_git_sha, per_leg_bin_accept_reject}`. **Report** quotes og json per-phase n vs clean baseline {466,360,191,540,1063} as a basis check (kills wrong-basis og).
3. **Regression proof (charter §2):** default-off = branch only writes NEW files; re-run normal B2 convert → **sha match vs committed b3472e8c (train) / 0ed5149c (val)** (b2-heldout proof form) + py_compile.
4. Train ×2 (aug-BC on aug npz; aug-null on aug null npz) — `bc_train_route.py` UNCHANGED (point at aug dirs; whole-demo val = clean `_val.npz`). GPU-1, CUDA_VISIBLE_DEVICES=1, seed pin.
5. og --full --carried-stops GUIDE_C2 on **clean** train npz: aug-null first → aug-BC with --null-og. **`og_offline_gate.py` = UNCHANGED (0 edits).** D_train-direction + per-axis-pair breakdown (og returns 3-axis mean only, `:265`) = standalone eval_runs analysis script (imports og public fns; b2_make_heldout_npz precedent).
6. Locked-4 = 0-diff. §運用14 video leg = **N/A (loud): offline 変換+学習+offline gate のみ、motion-bearing sim なし.** sim 必要化 = STOP→%12.
7. **U10 gate-set map:** DoD = charter §3 A/B + validity (v1/v2 §6); pre-mortem = §5 predictions + retry ladder + panel scenarios; handoff = §運用25 judgment (not triggered, ctx ok); **層2 post-debate = fires (L3)**; **層5 3-view = fires post-build (L3 + expected 3+ files: converter + analysis script + eval_runs)**; all offline. **commit 判断 = %12** (U9 wording).

---

## 5. Prediction table (U11 — B0a precedent, predicted BEFORE build; V1-OFF currency)

| metric | baseline | prediction (推測, mechanism-reasoned) |
|---|---|---|
| γ⊥ {0}/{1} | 2.497/1.257 | **↓ strong** (direct 6-dim ee-leg; bars 1.249/0.629 reachable) |
| γ⊥ {2}/{3} | 1.041/1.055 | **↓ partial — RISK cells** (L-cols direct [2,8]mm; R+seg cols generalization-only, V1-OFF by design; bars 0.521/0.528 may miss → attributable Outcome-B or Rs-consult V1 toggle) |
| ee-only {11} | 0.973 | **↓ strong** (direct R-dim ee-leg [2,20]mm) |
| **seg-follow {11}** (INFORMATIVE) | 0.282 | **↑ toward ~0.67 CEILING** (U4/U11: faithful expert = mean(R_x 1, R_y 0, R_z 1)=0.667 < band-lo 0.8 → **the B2 §3.3 [0.8,1.2] pair band may be UNREACHABLE by faithful behavior**; no (iv) boundary impact [seg-follow = informative], but a **band-recalibration question for the (ii) GO gate = Rs 専権**, carried loud to (ii) charter + Rs notify) |
| beat (c) | −0.261 | **both directions predicted (U5):** (+) positive-plausible ≥+0.15 if aug-BC restores cross-offset while aug-null restores only near its 1 path; (−) < 0.15 if augmentation transfers to the null via smoothness OR aug-null ignore-obs collapse makes (c) structurally unreachable (→ INCONCLUSIVE cell, not mechanism-fail) |
| v1 val / v2 OG-a | 0.000659 / GO | **PASS** (label-preserving noise rarely hurts clean fit; seg-leg volume small; v2 pinned §6) |

---

## 6. Validity pins (charter §3 v1 + U6 v2 amendment; A/B numbers untouched)
- **v1 (charter §3):** augmented-BC whole-demo val ≤ **0.001318** (= 2× baseline 0.000659).
- **v2 (U6 pin, pre-train):** (OG-a mean rmse over ALL cells ≤ **0.550mm** = 1.10× baseline mean 0.500mm) **AND** (every VERDICT_CRITICAL cell rmse ≤ **1.10× its baseline cell** in `b2_cpE_og/bc/og_gate.json`). Recorded as charter §3 v1.1 amendment (validity-precondition sharpening; %9 条件1 A/B letter preserved).
-未達 → retry ladder (§2), max 3, then STOP→%12.

## 7. Tie rule (U8, pre-registered pre-train)
Any (a)/(b) cell within **±0.02** of its bar → **one same-seed re-train**; if the side flips → take the **unfavorable side**.

## 8. L3 chain (U2) + demotion recommendation
**final_L = L3** (§0 Phase-keyword auto-escalation; 4/5 panel + E15 v1 L2-retraction precedent `B_BC_BUILD_SPEC.md:159`「§0 keyword に new-file 免除なし」). Factual substrate (converter offline, no sim import, `route_demo_to_bc.py:91` task_config lazy leaf) = a **demotion RECOMMENDATION to Rs, loud, non-blocking** (demotion = Rs-initiated per rule-check Step 6). **Default = run the L3 chain:** this pre-debate (DONE) + 層3 mechanical (py_compile + sha regression) + post-build 層2 debate + 層5 3-view — all offline (§4-7). %9 O-1 (「本 consult は gates を免除しない」) honored.

## 9. Cite corrections (U9)
og constants `:24-31`→**`:33-38`**; band scope → **`og:34/:37/:407-413`**; import-audit sentence += `route_demo_to_bc.py:91` task_config lazy leaf read; "until CC1 review"→**「commit 判断 = %12」**; og:97-140/:268-277/:425-441 = re-grep VERIFIED correct (CC2).

## 10. Execution order after %12 conformance PASS
[RULE-CHECK] stage2 → CP-(iv)-2 build + regression (sha b3472e8c/0ed5149c + py_compile) → CP-(iv)-3 trains ×2 + og ×2 (GPU-1) → CP-(iv)-4 charter §3 A/B 機械判定 (+ v1/v2 validity, tie rule) → `dq7_iv_pathfinder_report.md`. Each CP = pane 報告 + same-turn JST stamp. Est wall ~1-2h; 失敗 3 回 = ハードストップ→%12. rollout 禁止不変; cuda:0 不使用; GPU-1 のみ.
