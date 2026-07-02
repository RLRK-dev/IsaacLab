# B2 converter v2 (§1.3/§1.4) + trainer — impl report (0-commit; %11 independently verified)

**2026-07-03 03:41 JST.** Files edited (non-locked): `route_demo_to_bc.py` (+602/−79, 22 hunks), `bc_train_route.py` (+65, 5 hunks). Locked-4 + `policy_route_runner.py` = **0-diff**. Dataset built at `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/b2_dataset_v2/`. (Implemented via a subagent on my design brief; **every DoD number below is %11's own independent recompute, not the agent's.**)

## DoD — independently re-verified (my recompute)
| DoD | result (my check) |
|---|---|
| A. 13-phase byte-identity | **PASS** — NEW code on canonical `p3_dod_cuda_demo_raw` auto-detects 13-phase, obs (770,25), self-check ALL PASS (delta+abs), round-trip 6.84e-06mm. Agent also sha-identical old-vs-new. |
| B. converter runs 11+3 | **PASS** — train obs **(6930,27)**=9×770, val **(1540,27)**=2×770, actions (…,6); union affine **(15,6,2)**; onehot sums-to-1 (train+val); \|labels\|max **0.833** (≤0.95); guard1=56. |
| C. round-trip | **PASS** — my recompute over all 11 train = **2.776e-14mm** (float64 exact); 6.84e-06mm with float32 npz storage. ≤1e-3 bound. |
| D. hull assert | **PASS 3/3 INTERIOR** — (+8,+8) 0.833, (+8,−8) 0.833, (−8,−8) 0.850 max\|a\|≤1. No EXTRAPOLATION. |
| E. box-span audit | min 30mm (guard1 floor), max 473.9mm, degenerate-below-floor 0, empty_phase=[9 GUIDE_C2]. |
| F. obs 27D consistency | **PASS** — meta obs_dim=27 == obs.shape[1]; trainer builds `build_actor_critic(27,…)` (bc_pretrain's is obs-dim-parametric — LOCKED, untouched). |
| G. runner v2 (report-only) | listed below (CP-E prerequisite). |
| H. py_compile + no reformat + 0-commit | PASS. |
- **Frozen val (seed=0, deterministic): (0,0) and (−10,0)** — both non-hull-vertex interior (pin b). Train 9 = 6 hull-vertex + 3 interior {(+10,0),(0,+10),(0,−10)}.
- **Whole-demo val (trainer, pin/spec §3.1):** since LOCKED `bc_pretrain.train_bc` does a RANDOM-row split, the trainer trains on the 9-demo `bc_dataset_abs.npz` (train_bc's internal split = a labeled *proxy*) and computes the authoritative **whole-demo val loss on `bc_dataset_abs_val.npz`** (2 held-out demos, same MSE-on-actor-mean). CPU smoke: whole-demo val 0.101 vs proxy 0.118.

## ⚠ TWO DEVIATIONS — need %12 adjudication (both correctly handled + flagged, NOT silent)
**D1 — E4' argmin cross-check relaxed to a seating-quality flag (multi-demo path only).** 3/11 TRAIN demos have the cable **22-24mm off C1** at the pin (pinned-seg ≠ nearest-to-C1): **(0,+20) 24.3mm, (−20,+20) 21.9mm, (0,−10) 24.1mm**. Other 8 train + 3 held-out well-seated (≤7.4mm). Handling: `strict=True` (single-demo/13-phase → RAISES, canonical passes = byte-identity intact) vs `strict=False` (B2 → records `seat_quality_audit`, loud-warns, proceeds with the STRUCTURAL `seated_seg=pinned_body−28`).
- **Correctness (I verified):** the runner uses the SAME `cable_pos[seated_body_row]` (pinned-28) for C1_SEAT/C1_PIN (`policy_route_runner.py:117`), NOT argmin → the converter's seg_pos is **obs-parity-consistent with rollout**. The 22-24mm off-C1 only touches obs[:,6:9] for those demos' C1 rows; affine/labels/hull are EE-based, unaffected.
- **%12 call (§5.3-adjacent quality):** keep the 3 (default; they're §5.3 survivors, obs-parity correct) OR filter to a stricter C1-seat bar → 8 train (still ≥6). My read: KEEP + flag (consistent with the mechanical §5.3 = they passed regrasp_ok+c2_seated). Adjudicate.

**D2 — GUIDE_C2 (idx 9) empty → inert placeholder.** The CP-C route NEVER enters GUIDE_C2 (phase_id goes 8→10; 9 absent at every frame). `_build_abs_affine` assigns an inert floor-wide box for empty phases (never indexed by encode/decode — no row is phase 9); 15 slots kept for onehot/index alignment; 13-phase never triggers it (byte-identity safe).
- **%12 call:** accept GUIDE_C2 as a reserved/dead onehot slot (default; functionally safe) OR note a spec§1.1-vs-route mismatch (the route skips GUIDE_C2). My read: accept (route property; the onehot dead-slot is harmless). Note for OG/runner (a 15-dim onehot with dim 9 always 0).

## Runner v2 (CP-E prerequisite, NOT implemented — report only)
`policy_route_runner.py`: `:128` obs=np.zeros(25)→27; `:327` build_actor_critic(25→27 from meta); `:339` `assert abs_affine.shape==(13,6,2)`→(15,6,2); `:881` np.zeros((0,25))→27; obs-parity `:265/:881` (25 vs 27). **Also:** `convert_b2` emits no `schedule.json`/`macro_schedule.json` (not needed for the abs BC dataset) → CP-E's open-loop path needs a 15-phase schedule source. **Also:** LOCKED `og_offline_gate.py` imports PHASES13 + hardcodes 13 → the OG gate needs 15-phase awareness before CP-E (its own gate; flag). These are CP-E items, like the converter was for CP-D.

## Status + recommendation
Dataset built + independently verified. **GPU-1 Blackwell preflight = PASS** (sm_120, torch 2.10.0+cu128, kernel OK) → CP-D can train on GPU-1. Recommend: %12 縮退 review the diff + adjudicate D1/D2 → CP-D (BC on `bc_dataset_abs.npz` ∥ replicate-null, GPU-1, whole-demo val on `_val.npz`). 0-commit until %12.
