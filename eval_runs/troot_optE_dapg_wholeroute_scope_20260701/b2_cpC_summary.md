# CP-C 総括 — 16/17 offsets recorded (aborted at m8_p8 R_MISS); fix-⑤ X-follow validated

**2026-07-03 02:46 JST.** 0-commit. GPU-0 4-way waves. 16 npz + 16 meta produced (all 12M); m8_m8 (−8,−8) not run (abort-before).

## Headline
- **fix-⑤ X-follow VALIDATED across ALL 16 recorded offsets:** every dx≠0 caveat-a-X = the exact offset (±20/±10/±8, both signs). **ALL 16 initial grasps SUCCESS** (incl. m8_p8, which grasped+lifted+C1-seated fine).
- Recording aborted at **m8_p8 (−8,+8) = R_MISS_AT_88 at the C2 RE-GRASP** (per %12's abort-on-new-mechanism rule). This is **downstream of fix-⑤** (a device-fragile re-grasp, not the initial grasp).

## Per-offset table (17)
### Training (13): survivors=11 (≥6 floor CLEARED), seat-filter=2
| offset (dx,dy) | caveat-a-X Δ | regrasp_ok | verdict | seated_honest | §5.3 |
|---|---|---|---|---|---|
| (0,0) | non-fire | T | SUCCESS_R_GRIP_L_CAGE_AT_88 | T | **survivor** |
| (+20,0) | +20.00 | T | SUCCESS_DUAL_LOADED_AT_88 | T | **survivor** |
| (−20,0) | −20.00 | T | SUCCESS_DUAL_LOADED_AT_88 | T | **survivor** |
| (0,+20) | non-fire | T | SUCCESS_DUAL_LOADED_AT_88 | T | **survivor** |
| (0,−20) | non-fire | T | SUCCESS_R_GRIP_L_CAGE_AT_88 | **F** | filter (seat) |
| (+20,+20) | +20.00 | T | SUCCESS_DUAL_LOADED_AT_88 | **F** | filter (seat) |
| (+20,−20) | +20.00 | T | SUCCESS_R_GRIP_L_CAGE_AT_88 | T | **survivor** |
| (−20,+20) | −20.00 | T | SUCCESS_DUAL_LOADED_AT_88 | T | **survivor** |
| (−20,−20) | −20.00 | T | SUCCESS_R_GRIP_L_CAGE_AT_88 | T | **survivor** |
| (+10,0) | +10.00 | T | SUCCESS_DUAL_LOADED_AT_88 | T | **survivor** |
| (−10,0) | −10.00 | T | SUCCESS_DUAL_LOADED_AT_88 | T | **survivor** |
| (0,+10) | non-fire | T | SUCCESS_R_GRIP_L_CAGE_AT_88 | T | **survivor** |
| (0,−10) | non-fire | T | SUCCESS_DUAL_LOADED_AT_88 | T | **survivor** |

### Held-out (4): survivors=2, filter=1, PENDING=1 → **≥3 floor AT RISK**
| offset (dx,dy) | caveat-a-X Δ | regrasp_ok | verdict | seated_honest | §5.3 |
|---|---|---|---|---|---|
| (+8,+8) | +8.00 | T | SUCCESS_DUAL_LOADED_AT_88 | T | **survivor** |
| (+8,−8) | +8.00 | T | SUCCESS_DUAL_LOADED_AT_88 | T | **survivor** |
| (−8,+8) | −8.00 | **F** | **R_MISS_AT_88** | F | filter (R_MISS) |
| (−8,−8) | — | **NOT RUN** | — | — | pending (needed for floor) |

## m8_p8 (−8,+8) R_MISS — characterization (NOT a fix-⑤ failure)
- Initial grasp: SUCCESS (caveat-a-X −8.00mm exact, LIFT12/12 converged, C1 seat cable↔C1=−3.23mm).
- C2 re-grasp: R **reached** the target (achieved XY=(0.336,+0.119) vs tgt=(0.336,+0.119), **resid 0.1mm** — NOT the reach-wall) but closed on **AIR (L=0N/R=0N, r_grips=False)** → R_MISS_AT_88. 3D span=112.2mm (24mm excess over the 88mm Y-target = the (−8,+8) cable-bow chord).
- Siblings same |±8| magnitude re-grasped FINE: (+8,+8) r_grip=137.5N / (+8,−8) r_grip=142.1N, both SUCCESS. So the miss is specific to (−8,+8)'s cable geometry at the C2 re-grasp.
- Location = the KNOWN device-fragile / GPU#562-stochastic / geometry-sensitive **C2 re-grasp** (RS71 anchor-set; memory `project-canonical-route-device-fragile`) — **downstream of the fix-⑤ initial grasp**, which succeeded.

## ⚠ false-abort disclosure (my orchestrator bug, fixed)
Waves-2-5 first attempt false-aborted after batch-1: the abort grep `R_MISS_AT_88` matched the `[C2-REGRASP-GATE]` **label-enumeration** line present in EVERY run (incl. successes). Batch-1's 4 (p20_0/p20_m20/m20_p20/z0_0) were all genuine SUCCESS. **Fix:** abort now = JSON-verdict-based (`regrasp_ok`/`finite`), not a log-grep of the label. The fixed check preserved batch-1 and then **correctly caught the REAL m8_p8 R_MISS**. Lesson: gate on the JSON verdict, not a log string that also appears in label lists.

## hull-assert preliminary
- Training hull = the 11 survivors (spans ±20 in X and Y). Held-out survivors (+8,+8),(+8,−8) at |x|+|y|=16 are **INTERIOR** to the ±20 hull (spec :75/:96 satisfied for these 2).
- **Held-out ≥3 floor:** currently 2 survivors; needs m8_m8 (−8,−8). If m8_m8 SUCCESS → 3 ≥ floor. If m8_m8 also R_MISS → spec :96/:75 loud-reclassify / re-assert (in-spec, no new design).

## npz+meta inventory (0-commit)
16 recorded offsets, each `route_demo_raw.npz` (12M) + `route_demo_raw_meta.json` under `b2_cpC_wave1/rec_*` (4) + `b2_cpC_waves2_5/rec_*` (12). m8_m8 pending.

## Adjudication requested (%12)
1. **m8_p8 R_MISS disposition:** filter-out per §5.3 (regrasp_ok=False, mechanical) — my read. Optional: 1 re-run to test GPU-non-det reproducibility (the re-grasp is GPU#562-stochastic; a re-run may SUCCEED, which would keep (−8,+8) in the held-out pool).
2. **Run m8_m8 (−8,−8)?** — needed for the held-out ≥3 floor (recommend yes; the abort stopped it).
3. **Seat-flags (0,−20) + (+20,+20):** filter-out per §5.3 (same as your wave-1 (+20,+20) disposition) — confirm.
