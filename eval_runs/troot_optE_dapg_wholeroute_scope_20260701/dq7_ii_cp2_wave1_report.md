# DQ7 stage (ii) CP-(ii)-2 wave-1 report — loud wave gate (STOP before full batch)

**COORD %11 · 2026-07-03 14:18 JST · 0-commit.** Scope=(b) per %12 (2026-07-03 13:37). 4 outputs (i)-(iv). **STOP here → %12 loud wave gate + %9 independent cross-PV before the full batch.** rollout prohibited.

## (i) per-recording quality — PASS (4/4)
4 recordings (cuda:0, full C1→C2, `dq7_ii_cp2_wave1/rec_{d1a,d1b,c11,adjA}/`): all **15 phases + regrasp_ok=True** (incl. rec_c11 UNDER the {11} kick → **release-margin guard held the LOCKED verdict on real data**), non-disarmed. Window offsets match schedules EXACTLY (d1a DESCEND-R[10,−4,8]@[660,710) / d1b[−8,6,4]@[611,661) / c11 C2_REGRASP-R[12,9,−5]@[5195,5255) / adjA 0-window). Converter mask drops 6/6/7 kick control-frames (d1a/d1b/c11), C1 command-key holds. Span-watch: dual-hold Y-span dev ≤4.4mm (<5mm); injections are pre-contact → no dual-hold detour → 0 invalid-marks (%9 N1 pre-contact exemption; informative).

## (ii) 2-model whole-demo val — CONFOUNDED (do not use; γ⊥ is the anchor)
- Model 1 (clean-only, b2_dataset_v2): val **0.000659** = reproduces CP-D exactly (protocol faithful).
- Model 2 (clean+4p2r): val 0.001179 **but LEAKED/optimistic** — the seed-0 val split put clean (0,0)+(10,0) in val while their byte-identical twins are in train (adjA ≡ clean rec_p10_0 dup); M1 val-set ≠ M2 val-set. ⇒ **whole-demo val is NOT a clean cross-model comparison** (subagent anomaly 3, my dataset-meta check confirms val=[[0,0],[10,0]] both in train). The directional-γ⊥ (iii) is the clean anchor.

## (iii) directional-γ⊥ @ {1},{11} — mechanism VALIDATED; {11} INCONCLUSIVE (§運用28-verified from ogb_anchor_gate)
| phase | metric | M1 (clean) | M2 (clean+p2r) | delta | read |
|---|---|---|---|---|---|
| **{1} GRASP_DESCEND** | γ⊥ (movable) | 1.257 | 1.098 | **−0.159 ↓** | restoring ✓ (toward GO≤0.5) |
| **{11} C2_REGRASP** | seg_following (pair) | 0.282 | 0.249 | −0.033 | ↓ (further below [0.8,1.2]) |
| **{11} C2_REGRASP** | ee_only (pair) | 0.973 | 0.974 | +0.001 | **STATIC** |

M1 == CP-E baseline exactly (1.257 / 0.282 / 0.973) → faithful. Both models overall still STOP (absolute verdict = CP-(ii)-5).
**判定則 (%12):** no metric moved anti-restoring (↑) → **NO ABORT** (not silent-wrong-teacher, not false Outcome-B). {1} γ⊥ ↓ −0.159 (2 recs, model-consistent) satisfies "↓ @ {1} and/or {11} → mechanism OK" → **the p2r kick-and-recover DOES teach restoring** (directly counters the (iv)-Outcome-B concern that imitation can't). **{11} ee_only STATIC (+0.001, 1 rec = weak signal) = INCONCLUSIVE** — can't separate weak-signal from an {11}-specific issue; the full batch's added {11} recordings + %12+%9 resolve it. Caveat: directional/sanity, NOT absolute-bar.

## (iv) video legs — all 3 physically VALID (advisory)
video-analyst (render byte-matches banked trajectory): **injection→release→recovery VALID ×3** (detour matches kick, smooth return post-release, no freeze/explosion); **grasp/regrasp on the ACTUAL cable ×3** (R grip 75.4/110.6/101.5 N SUCCESS_R_GRIP; rec_c11 align 22mm→recovers 0.8mm→grips, regrasp_ok=True); **no drop / no table-penetration / no NaN**; cable held throughout (min-z≈table, jump ≤1.9mm/frame). Advisory (fine intra-finger slip deferred to independent gate / mj_geomDistance; CPU-rigid non-conservative for grip magnitude, kick→recover kinematics robust).

## Recommendation (→ %12 loud gate + %9 cross-PV)
The mechanism is **validated** (no anti-restoring; {1} teaches restoring; recordings physically valid) → per the 判定則 this is **OK / proceed-direction**, NOT abort. **Recommend proceeding to the full batch**, WITH the **{11} ee_only-static flagged as the key uncertainty** (the hardest cell, 1 wave-1 recording = weak) for %12+%9 + more {11} recordings in the batch.

## Findings for the full batch (CP-(ii)-3)
1. **⚠ converter dir-name blocker:** `route_demo_to_bc.py:_offset_from_npz_path` requires `rec_<x>_<y>` naming; my `rec_d1a`-style dirs crash convert_b2. Subagent worked around via offset-named symlinks. **The full batch must name recordings by IC offset `rec_<x>_<y>`** (unique per IC) — or extend `_offset_from_npz_path` (NON-locked, needs %12 review). Flag before the batch.
2. **adjA ≡ clean p10_0 dup** (byte-identical) — non-load-bearing; use distinct 5mm-grid reach-screened offsets for the batch adj-A set (charter §4).
3. artifacts: `dq7_ii_cp2_wave1/bmodel/` (datasets/checkpoints/og_m{1,2}); videos `~/Downloads/p2r_{d1a,d1b,c11}_route.mp4` + figures `inj_{d1a,d1b,c11}.png`.
