# DQ7 stage (ii) mini-spec — perturb-and-recover injection hooks (CP-(ii)-0)

**COORD %11 · 2026-07-03 08:45 JST (same-turn date) · 0-commit, 0-GPU, locked-UNTOUCHED (design only).** Per `charter_dq7_stage_ii_coord.txt` §8. Build (CP-(ii)-1) starts only after %12 review → 5体 pre-debate → %9 concur → Rs loud notify (§8 order strict). This doc edits NO code.

**Grounding (self-read, cited):** charter §2/§3/§5/§6/§7/§8 · `DQ7_OFFPATH_SCOPING_COORD2.md` §3 (injection map + Fact A/B + label structure :81) · `DQ7_CONSULT_PCT9_VERDICT.md` 条件2 (:87)/条件3 (:61)/追加1 (:70 meta records-vs-fact) · `dq7_iv_pathfinder_report.md` §4-5 (2 pre-flags) · route `test_newton_clip_routing.py` phase/ik_move_both map (grounded below) · markers `:1758 _ANTI_REVERT_MARKER_LINES=[4401,4417,4516]`.

**L-TRIAGE (§8 self-run):** final_L = **L3** — the CP-(ii)-1 build edits Rs-LOCKED `test_newton_clip_routing.py` (§0 path-match auto-escalation, no demotion). CP-(ii)-0 (this doc) = design-only precursor (0-GPU, no edit). The 5体 pre-debate = the L3 [VERIFY]; rule-check stage2 before build. **Prior-art V10 (injection/detour/dwell):** BLOCKER hits = ALL DQ7 self-referential (state.md/scoping/this task's provenance + injection-map) — NOT a prior failed path; delta = this IS the scoping-recommended + Rs-approved (ii) leg, (iv) Outcome B banked, physics-vs-model discriminator documented. Continue per charter §8.

## §A. Mechanism (charter §2, restated — zero deviation)
Flag-gated **`PERTURB_INJECT`** env-gate (default unset/off → **None-path byte-identity**, fix-⑤/recorder precedent). When set = a path to a pre-sampled **injection schedule** (deterministic, seed-recorded). During a SAFE phase a scheduled **EE-target detour offset** is added to ONE arm's target (per-arm single-sided) and **held for `dwell` control-steps** (off-path obs accumulate) → released → the script's absolute-target servo restores (recovery frames) → recorder captures all frames + logs the window. NO xfrc (D-2). Cable never teleported (INV#5).

## §B. Element 1 — hook insertion points (markers UNTOUCHED)
Single helper `_inject_detour(phase_name, arm, tgt_xyz, ctrl_step, rec)` wraps the **target argument** at each SAFE-phase `ik_move_both` call (downstream of every target derivation — the LOCKED logic is not re-authored). None-path returns `tgt_xyz` unchanged.

| 15-idx phase | `_ph` line | ik_move_both target-arg site(s) | inject arm | note |
|---|---|---|---|---|
| 0 GRASP_HOVER | 3891 | **3893** (`tgt(x_grasp,z_high)`) | one side | both arms move; single-sided |
| 1 GRASP_DESCEND | 3896 | **3900** (`tgt(x_grasp,zk)`), **3931** | one side | Z≤0 component forbidden |
| 4 ROUTE_C1 | 3961 | **3966** (`tgt2(xk,yck,z_lift)`) | one side | held transport |
| 5 C1_SEAT | 4092 | **4097** (`tgt2(x_clip,y_clip,zk)`) | one side | pre-seat frames only |
| 9 GUIDE_C2 | 4221 | (region) | — | ⚠ **VACUOUS in CP-C recordings** (route 8→10; 0 control frames) → no rows → effectively no injection; record the fact, no hook needed |
| 10 GUIDE_PRELIFT | 4248 | **4255**, **4263** (`(…),R_hold`) | **L** (R is `R_hold`) | L is the moving arm |
| 11 C2_REGRASP | 4414 | **4481**, **4494** (`_La, _fr`) | **R** (`_fr`, acting) | ⛔ markers :4401/:4417 = `_fr` argmin+square-on derivation UPSTREAM, :4516 = regrasp_ok — **NOT touched**; hook wraps `_fr` at the call, holds detour, releases pre-contact |
| 12 C2_TRANSPORT | 4551 | **4558** (`_La, _fr`) | one side | held transport |
| 13 C2_DUAL_SEAT | 4574 | **4578** | one side | pre-seat frames only |
| 2,3,6,7,8,14 | — | — | ⛔ SKIP | close-servo/lift-choreography/event/gripper-transition/verdict-window (charter §3) |

**Marker-safety declaration:** the 3 Rs-LOCKED markers (`:4401/:4417/:4516`) and every phase's target-DERIVATION are byte-untouched; the hook only wraps the already-derived target passed to `ik_move_both`. `_ANTI_REVERT_MARKER_LINES` re-sync to post-build lines is a mechanical addendum (fix-⑤ precedent) verified at CP-(ii)-1 diff review.

## §C. Element 2 — dwell / direction numerics
- **dwell = 20 control-steps** (initial; within charter [10,40]). Held-at-offset window = [start, start+20]; recovery observed in the subsequent same-phase loop iterations (DESCEND :3900 / ROUTE_C1 :3966 / C2_REGRASP :4481 are interpolation loops → natural recovery frames).
- **direction:** unit 3D random per injection, magnitude log-U per §3 table (§E). Constraints: **DESCEND {1}: Z-component ≤ 0 FORBIDDEN** (table-collision avoidance, resample if drawn); **pre-seat {5,13}: XY only** (Z=0, seat-precision protection); {10,12} = the moving arm only. Direction seed recorded.
- **count:** 2-4 injections per recording; **≤1 injection per phase-instance**; per-arm single-sided (never both arms same injection → INV#1 both-arms-engaged preserved). Priority weighting: primary {0,1,11} (direct teachers of the failing cells 2.497/1.257/0.973) get ≥1 each when eligible; {4,5,10,12,13} fill to the 2-4 budget.
- **INV#2 span-watch:** post-detour, if dual-hold span deviates >5mm from 88mm → the recording is **invalid-marked + loud-counted** (validity filter, charter §3).

## §D. Element 3 — recorder meta injection-window fields (records-vs-fact, %9 追加1)
New recorder method `mark_injection(...)` appends to `meta["injection_windows"]` (additive; absent when PERTURB_INJECT off = byte-identity):

| field | type | meaning |
|---|---|---|
| `phase` / `phase_idx` | str / int | SAFE phase the injection fired in |
| `arm` | "L"/"R" | the single perturbed arm |
| `offset_mm` | [dx,dy,dz] | the **ACTUAL** applied detour vector [mm] (not nominal) |
| `start_frame` / `end_frame` | int | dwell window (physics-frame stamps, same clock as `phase_id`) |
| `dwell_ctrl_steps` | int | 20 |
| `schedule_seed` | int | reproducibility |

**records-vs-fact scrutiny (CP-(ii)-1 review, %9 追加1):** the meta `offset_mm`/`start/end_frame` MUST equal what the hook actually applied — verified by (a) the converter reading `injection_windows` back and (b) an on-disk cross-check that the recorded EE-target at `start_frame` = script_target + `offset_mm` (± IK residual). A meta that could lie under a future config = a build-review BLOCK.

## §E. Element 4 — expected-fire table + Element 5 — §3 amplitude re-listing (ZERO-deviation)
**§3 amplitude table (charter, verbatim re-listing — I declare ZERO deviation from it):** {0}[2,20] / {1}[2,20] Z≤0-forbidden / {4}[2,8] / {5}[2,5] pre-seat / {9}[2,8] (vacuous) / {10}[2,8] / {11}[2,20] R / {12}[2,8] / {13}[2,5] pre-seat; skip {2,3,6,7,8,14}. Change = %9 re-concur.

**Expected-fire (per recording, 2-4 injections):**

| phase | eligible? | expected fires/recording | amplitude |
|---|---|---|---|
| 0 HOVER, 1 DESCEND | ✅ primary | ~1 each (priority) | [2,20] |
| 11 C2_REGRASP (R) | ✅ primary | ~1 (priority) | [2,20] |
| 4,5,10,12,13 | ✅ fill | 0-1 (to budget) | [2,8]/[2,5] |
| 9 GUIDE_C2 | vacuous | 0 (no frames) | — |
| 2,3,6,7,8,14 | ⛔ skip | 0 | — |
Across ~24 recordings: {0,1,11} each get ~20-24 injected instances (the load-bearing coverage); the fill phases scatter. adj-A 8 recordings (charter §4) carry **0 injections** (pure 5mm-grid density for leg-2, reach-screened first).

## §F. Downstream references (not built here; for %12 context)
- **Converter outbound-mask (charter §5, CP-(ii)-1/4):** detour OUTBOUND frames (target = detour) = anti-restoring → **drop**; RECOVERY frames (target = script next-waypoint) = **keep** (auto restoring label, doc §3:81); **dwell frames = keep** (off-path obs + legit label). Additive default-off branch on `route_demo_to_bc.py` (my augment-branch precedent); regression = normal convert sha b3472e8c/0ed5149c + py_compile. Output `b2_dataset_v2_p2r/bc_dataset_abs_p2r.npz` (`_p2r` tag, U7 meta contract).
- **Beat interpretation (charter §5, 1-line):** physical recordings can't be replicated → **no augmented-null**; null = CP-D replicate-null **as-is**; beat = pre-registered "diverse+p2r vs single-path" (§3.4), NOT an augmented-null.
- **band recalibration (charter §7 = Rs 決定項 α/β/γ):** blocks CP-(ii)-5 (OG gate) ONLY; recording+training (CP-(ii)-1..4) are band-independent → proceed. faithful pair seg-follow ceiling ≈0.667 < band-lo 0.8 (U4).

## §G. Chain / next
CP-(ii)-0 (this) → %12 review → 5体 pre-debate (L3) → %9 concur → Rs loud notify (GPU-h ~3-5h / device pins cuda:0+EGL / (iv) Outcome-B summary / wave-granular early-abort / abort procedure) → CP-(ii)-1 build (hooks + converter mask + meta) + None-path byte-identity (canonical sha e01ac1fa… re-proof) + 縮退 review. 0-commit; commit 判断 = %12. rollout prohibited (OG GO 後も別途 Rs GO).
