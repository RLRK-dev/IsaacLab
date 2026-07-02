# CP-C FINAL — survivor set resolved; convert BLOCKED on §1.3/§1.4 converter impl

**2026-07-03 02:56 JST.** 0-commit. Post-adjudication resolution of `b2_cpC_summary.md`.

## m8pair resolution (per %12 pre-registered branches)
- **m8_m8 (−8,−8) = SUCCESS** (caveat-a-X −8.00mm exact, regrasp_ok=True, SUCCESS_DUAL_LOADED_AT_88, r_grip=115.4N, resid=1.1mm, seated_honest=True) → **held-out floor met**.
- **m8_p8-rerun (−8,+8) = R_MISS again** (regrasp_ok=False, r_grip=0.0N, resid=0.1mm) → **2/2 R_MISS = DETERMINISTIC geometry** (not flaky) → **exclude (−8,+8)** + record. The C2 re-grasp at (−8,+8) deterministically closes on air (cable-bow chord 112mm at that offset); the +X/−Y/−X−Y siblings all succeed. Downstream of fix-⑤ (initial grasp succeeded both times). Carry to OG/rollout interpretation.

## FINAL survivor set (both floors CLEARED)
- **Training survivors = 11** (≥6 floor ✓): (0,0),(+20,0),(−20,0),(0,+20),(+20,−20),(−20,+20),(−20,−20),(+10,0),(−10,0),(0,+10),(0,−10).
  - seat-filtered (2, §5.3): (0,−20),(+20,+20) [c2_seated_honest=False; grasp OK]. Honest note (per %12): (0,−20) is a **pure-Y** seat-fail (OUTSIDE the +X ride-up hypothesis) → the seat-fail distribution is not purely +X; carry to OG/rollout.
- **Held-out survivors = 3** (≥3 floor ✓): (+8,+8),(+8,−8),(−8,−8). Excluded: (−8,+8) [deterministic R_MISS].
- **Hull-assert (preliminary, offset-grid): PASS** — scipy Delaunay: all 3 held-out interior to the 11-training-survivor convex hull (the per-waypoint decode-clip check runs at convert per spec :75).
- **Coverage (honest count):** 18 route runs (13 train + 4 held-out + 1 diagnostic re-run); 16 unique offsets recorded; 14 survivors train/eval; 4 recorded-non-SUCCESS (2 seat + (−8,+8)×2 R_MISS); all npz retained as survivorship evidence.

## ⛔ CONVERT BLOCKER — the converter needs §1.3 + §1.4 (designed, NOT implemented)
`route_demo_to_bc.py` (committed 942ce85f1c) is **13-phase, SINGLE-demo only**:
- **Schema (§1.4):** :34-49 `PHASES13`; :146-147 `if len(phase_names)!=13: raise SystemExit(...->schema v2 (B2))`; :202 `onehot=zeros((tc,13))`; :50 `OBS_DIM=25`. My demos are **15-phase / obs 27D** → hits the E3 STOP.
- **Single-demo (§1.3):** `_build_abs_affine(wp, ph)` (:91-124) builds `abs_affine[13,6,2]` from ONE demo's waypoints. B2 needs the **UNION abs_affine over ALL 11 training demos** (spec §1.3 — one policy's action encoding must be consistent across every offset; a per-demo affine breaks BC label consistency).
So "convert" = an implementation step (spec §1.3 + §1.4), not a run. Neither was in the ③④ charter (which covered og_offline_gate + route wiring).

### §1.3/§1.4 implementation scope (per spec, for %12's decision)
1. `PHASES15` const + E3 auto-detect len∈{13,15} + phase-name assert.
2. `_build_abs_affine` parametrized on n_phases → `abs_affine[15,6,2]`.
3. **UNION affine (§1.3):** compute lo/hi over the concatenated waypoints of ALL 11 survivor training demos (not per-demo); FREEZE into `bc_dataset_abs_meta.json`; runner asserts affine-identity at load.
4. `_seg_rule` schema-v2 index branch (indices +1 after GUIDE_C2=9): GUIDE_PRELIFT(10)→argmin-to-C2, C2_TRANSPORT(12)→argmin-to-C2-held; C2_REGRASP=11, C2_DUAL_SEAT=13, C2_SETTLE=14.
5. onehot 15 → obs 27D (dims 12:27); meta schema→`BC_ROUTE_v2_15phase_abs`, phase_schema=15.
6. Post-filter hull assert (§1.3-ii/:75) + held-out ≥3 re-assert; v1↔v2 box-span audit (§1.4 instr 5, loud-flag verdict-critical z-span >20%).
7. Multi-demo aggregation: concat all survivor demos' (obs, abs-action) into one BC dataset; whole-demo val split (train 9 / val 2 of the 11, spec §3.1).

## RECOMMENDATION
I implement §1.3/§1.4 (0-commit) faithfully to spec → **%12 縮退 review (③④ pattern)** → convert on the 11+3 survivors → CP-D (BC ∥ null, GPU-1). Surfacing rather than silently implementing a substantial correctness-critical converter branch. Awaiting %12's impl-method decision.
