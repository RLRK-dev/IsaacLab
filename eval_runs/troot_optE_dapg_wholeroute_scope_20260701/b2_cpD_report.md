# CP-D report — BC ∥ replicate-null (GPU-1); strong null-beat on whole-demo val

**2026-07-03 03:53 JST.** 0-commit. Both trained on GPU-1 (Blackwell sm_120, torch 2.10.0+cu128) in parallel, seed=0, epochs=2000, obs 27D, whole-demo val on `_val.npz` (spec §3.1).

## Loss-curve highlights
| policy | train demos | final train_loss | proxy val (random-row) | **whole-demo val (§3.1 authoritative)** | elapsed |
|---|---|---|---|---|---|
| **BC (DR)** | 9 diverse offsets | 0.000638 | 0.000547 | **0.000659** | 90.1s |
| **NULL** | (+10,0)×9 replicate | 0.000149 | 0.000128 | **0.011979** | 91.4s |
- BC convergence: ep1 loss 0.1310 → ep2000 0.000638 (smooth, converged).
- NULL fits its single replicated demo TIGHTER (train 0.000149 < BC 0.000638) but generalizes far worse.

## ⭐ Null-beat material (§3.4 attribution — diversity vs budget)
**BC whole-demo val 0.000659 vs NULL 0.011979 = BC generalizes ~18× better (MSE) / ~4× (RMSE) to the held-out demos (0,0),(−10,0).**
- Matched: same volume (both 6930 rows = 9×770), same union affine, same seed=0, same epochs=2000, same GPU. The ONLY difference = **diversity** (9 different cable-XY offsets vs 9 copies of one).
- Interpretation: the DR policy's held-out generalization comes from **diversity, not training budget** — the null (1 demo replicated) overfits one config (low train, high held-out val), the DR learns a map that transfers to unseen offsets. This is the pre-registered diversity signal.
- ⚠ This is the CP-D **null-beat MATERIAL** (whole-demo val loss). The FORMAL §3.4 beat metric (worst-demo γ⊥ over DR-movable {0-3} + C2_REGRASP ee-only gain, ≥0.15 absolute) is an **OG computation at CP-E** (needs the runner v2 + OG 15-phase = the prep below). The 18× val gap strongly predicts a null-beat but is not itself the γ⊥ metric.

## ⚠ null design decision (flag for %12 validation)
n=1 analog = **(+10,0)** (`rec_p10_0`), the smallest-offset well-seated TRAIN demo. Rationale: the true nominal (0,0) is a **VAL** demo, so training the null on it would contaminate the whole-demo val comparison (null would have seen a val demo). (+10,0) keeps the val fair for BOTH (neither BC nor null trained on (0,0)/(−10,0)). Replicated **9×** = matched to the DR's actual 9-train-demo volume (spec §3.4 "13 replicates" was the pre-survivor candidate count; 9 matches the surviving DR budget). Same union affine + seed. If %12 prefers a different n=1/count, cheap re-run (~90s).

## Provenance (sha256, first 16)
- bc_dataset_abs.npz `b3472e8ca06be481` / _val.npz `0ed5149ce60bb2b2` / null_dataset.npz `565717c0c4cd39eb`
- policy_abs_b2_e2000.pt `e10ec5eb79073abe` / policy_abs_null_e2000.pt `2cd05d74a6c0f733`
- converter+dataset committed `c5e58d5636`. null_dataset built from rec_p10_0 via `route_demo_to_bc._compute_demo` + union affine (round-trip 7.05e-06mm).
- GPU-1 measured: 2 parallel trainings, ~90-91s each, no interference (GPU-1 mem ~1GB during).

## Next (CP-E prep, authorized 0-commit)
(a) runner v2 design proposal (obs27/affine15/obs-parity + 15-phase schedule source). (b) og_offline_gate.py 15-phase parametrize + empty-phase graceful (scoped, §3.3 verdict byte-untouched, regression = b1p_og_e2000 13-phase byte-identical). Both → %12 review → CP-E OG gate on the BC+null policies (formal §3.4 γ⊥ beat + restoring verification) → held-out rollouts iff OG=GO.
