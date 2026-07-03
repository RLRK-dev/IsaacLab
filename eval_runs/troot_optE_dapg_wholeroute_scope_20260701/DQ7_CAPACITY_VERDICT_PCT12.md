# DQ7 capacity pre-test — VERDICT = PASS (%12 §運用28 verification; %9 result-concur pending → joint)

**Author:** RS-TECH-LEAD (%12). **Written:** 2026-07-03 23:20 JST (same-turn `date`).
**Object:** the capacity pre-test build (`dq7_capacity_pretest/`, %11 2026-07-03 23:10) vs SPEC `dq7_capacity_pretest_mini_spec.md` (`9a4140a8aa`).
**Design cross-PV:** `DQ7_CAPACITY_CROSSPV_PCT9.md` (%9, CONCUR-with-refinements — all adopted: Var(δ) criterion / primary={0,1} / [A]dwell / degenerate ×4).
**Status:** %12 verdict = **PASS** (§運用28 independent re-extraction below). %9 RESULT-concur dispatched → joint verdict → Rs. 0-commit build / rollout PROHIBITED / band=γ unchanged / INVARIANTS untouched (offline, no sim).

---

## §1. §運用28 independent verification (on-disk, exact-match to %11 relay + %12 independent recompute)

| quantity | value | source (independent) | %11 relay | match |
|---|---|---|---|---|
| whole_demo_val_loss | **5.5616e-05** | `bc/policy_abs_sidecar.json` 直読 | 0.0000556 | ✓ |
| ckpt sha256 | f0389683… | sidecar 直読 | f0389683 | ✓ |
| **copycat floor = Var(δ)** (label MSE) | **0.0842** | %12 recompute: `encode(obs[0:6]) vs labels` on iso_train | 0.084 | ✓ |
| corr(c,\|δ\|) | **−0.0014** | %12 recompute from iso_train | −0.0014 | ✓ |
| c-carrier | seg.Y std 7.9mm(=c) / next_clip.Y **0.000mm**(const) / eeR.Y 10.1mm(=c+δ) | %12 recompute | — | seg = sole clean carrier |
| og γ⊥ {0}HOVER | **0.031** → GO | `og/og_gate.json` `ogb_anchor_gate` 直読 | 0.031 | ✓ (co_seg OFF, clean) |
| og γ⊥ {1}DESCEND | **0.003** → GO | og_gate.json 直読 | 0.003 | ✓ (co_seg OFF, clean) |
| og γ⊥ {2}CLOSE | 1.415 → STOP | og_gate.json 直読 | 1.415 | ✓ (co_seg ON — artifact, §3) |
| og γ⊥ {3}LIFT | 1.422 → STOP | og_gate.json 直読 | 1.422 | ✓ (co_seg ON — artifact, §3) |
| co_seg-FREE ee-gain {0/1/2/3} | **0.0142 / 0.0016 / 0.0033 / 0.0019** | %12 independent probe (obs[0:6]±5mm, seg FIXED, max same-axis d(tgt)/d(ee)) | 0.013/0.001/0.003/0.002 | ✓ all ≈0 |
| clamp fraction (eval) | **0.00%** | %12 probe + og `per_axis_clamp_counts` all 0 | — | degenerate#3 clean |
| max\|out−T*\| vs own-ee dev | **1.658mm ≪ 13.64mm** | %12 probe on iso_eval | — | copycat-refute |

Instruments = the applied CP-(ii)-5 `og_offline_gate.py` (band=γ) UNCHANGED + `bc_train_route.py` (seed-PINNED). Generator `gen_isolated.py` verified §2-faithful (T*(c) X/Z=frozen affine-midpoint / Y=c±GHS / own-ee=T*+δ decorrelated / seg.Y=c; N=8000/2000/1200).

## §2. Verdict = PASS (%9-pinned criterion)

**Joint criterion (%12+%9 pin):** PASS = `val ≪ Var(δ)` **AND** γ⊥{0,1} ≤ 0.5 / FAIL = γ⊥{0,1}≈1 **AND** val≈Var(δ) / degenerate = val≫Var(δ)+γ⊥low. **primary = {0,1}** (co_seg OFF).

- val 5.56e-05 ≪ Var(δ) 0.0842 (**1515× below**) ✓
- γ⊥{0,1} = 0.031 / 0.003 ≤ 0.5 ✓ (clean primary)
- → **PASS.** (FAIL/degenerate quadrants both non-satisfied.)

**%9 CRITICAL refinement (adopted):** a representation-attractor FAIL manifests as `val≈Var(δ)` (elevated) + γ⊥≈1, NOT "γ⊥≈1 despite low val" (unreachable). The verified `val ≪ Var(δ)` therefore *is* the discriminating PASS evidence — quantified against the on-disk Var(δ)=0.0842 reference (prevents mis-routing an elevated-val FAIL to (i)-RL).

## §3. {2,3} co_seg confound — resolved 3 ways (not a rationalization)

og_offline_gate.py `:97-108`: for `p ≥ grasp_close(2)` the γ⊥ probe **co-moves seg (obs[6:9]) with the holding-arm ee axis** (post-grasp cable-coupling model). A policy that correctly READS seg therefore follows the co-moved seg → γ⊥≈1.4 = **legit seg-tracking, wrong-signed γ⊥ on a co-moving target** (memory `reference-og-gate-moving-target-gamma-perp-wrong-sign`), NOT copycat. Independently confirmed {2,3}=restoring (own-ee ignored) by: **(a)** co_seg-FREE ee-gain probe {2}0.0033/{3}0.0019 (%12 independent); **(b)** OG-a decode table all-GO, {2,3} Ry rmse ≤0.19mm ≪ δ; **(c)** max|out−T*| 1.658mm ≪ own-ee dev 13.64mm. Per %9 [B], primary discriminator = clean {0,1}; {2,3} corroborate via the co_seg-free path. (The og_gate.json `overall_verdict:STOP` is the mechanical ≤0.5 bar applied uniformly incl. the {2,3} co_seg cells — it is NOT the capacity answer; the capacity question is answered by the co_seg-free measurement.)

## §4. Meaning + conservatism direction (§運用15)

- **PASS ⟹ the fork-(iv) arch CAN represent restoring** (ignore own-ee, emit the frozen target) given isolated decorrelated data. Therefore the (ii)/(iv)/{11} γ⊥≈1 plateau was **data-correlation** (on-path own-ee↔target), NOT a representation-capacity limit → **DAgger is justified** (its on-policy off-path relabel decorrelates own-ee from target at the states the policy visits — exactly the lever the isolated set proves the arch can exploit).
- **Conservatism = PASS is NECESSARY-but-NON-CONSERVATIVE.** The isolated set is EASIER than DAgger's on-policy data (perfect decorrelation, no compounding drift, no reach-infeasibility). PASS justifies *trying* DAgger; it does NOT promise the rollout reaches GO. The DAgger rollout + §9 pre-registered falsification + a rollout-SR/high-fidelity confirm remain the actual GO gates. (Had capacity FAILed, it would have been conservative-definite → skip DAgger → (i)-RL. It PASSed → DAgger with the scoping-§4 guarded prior.)

## §5. Next (Rs decision, escalated on %9 result-concur)

capacity PASS routes DQ7 to the **DAgger 5 decision points** (`DQ7_III_DAGGER_SCOPING_COORD2.md` §D, %12+%9 CONCUR): D-1 run DAgger [now capacity-supported] vs skip-to-RL / D-2 batched-GO+§9-abort-cap / D-3 §9 thresholds / D-4 β-mixing + feasibility-filter / D-5 (i)-RL re-decide-at-abort. rollout leg remains HIGH-COST-GATE + fresh Rs GO.

---
*RS-TECH-LEAD %12 — 2026-07-03 23:20 JST. %9 RESULT-concur pending → this becomes the %12+%9 joint verdict. 0-commit build / rollout PROHIBITED / no push (Rs-pending).*
