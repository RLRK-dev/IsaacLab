# DQ7 stage-(ii) wave-1 LOUD WAVE GATE — DECISION = PROCEED to full batch (W0-W3 gated)

**Timestamp:** 2026-07-03 14:35 JST
**Deciders:** %12 RS-TECH-LEAD (independent verification) + %9 OPS-SUPERVISOR (independent cross-PV = **CONCUR-proceed**)
**Inputs:** %11 `dq7_ii_cp2_wave1_report.md` / %12 verification (`log.md` 14:27) / %9 `DQ7_II_WAVE1_CROSSPV_PCT9.md` (W0-W3)
**Gate purpose:** authorize CP-(ii)-3 full batch (~28 recordings, GPU spend).

## VERDICT = PROCEED (both CONCUR); GPU batch UNLOCKED, GATED by W0-W3.

## Mechanism result (the load-bearing finding)
- **{1} GRASP_DESCEND γ⊥ = 1.257 → 1.098 (−0.159 ↓)** = the kick-and-recover mechanism TEACHES restoring. **%12 + %9 both independently re-extracted from `og_gate.json` — all 6 metrics exact match** ({0}−0.322/{1}−0.159/{2}−0.010/{3}−0.006/{11}seg−0.033/{11}ee+0.001). **This directly refutes the (iv)-Outcome-B concern that imitation can't teach off-path restoring.**
- %9 strengthening: relative drop {0}−12.9% / {1}−12.6% LOCALIZED vs {2,3}<1% = localized restoring teaching (NOT a size-artifact).
- BONUS: {0} GRASP_HOVER (un-injected) −0.322 ↓ = {1} teacher generalization.
- **No anti-restoring ↑ anywhere → NO ABORT.** M1 == CP-E baseline exact = measurement faithful. Both models overall STOP (absolute verdict = CP-(ii)-5).

## Key uncertainty — {11} C2_REGRASP ee_only STATIC (+0.001)
- %12 initial read: weak-signal (1 rec), full batch resolves.
- **%9 CORRECTION (adopted): STRUCTURAL DILUTION risk** — the ee_only probe spans the full **1530-row** C2_REGRASP regression (on-disk confirmed); the c11 kick-teacher is only the **RHOVER sub-loop (~1%)**, diluted by RDESCEND+cage. If DILUTION (not noise), **more {11} recordings WON'T fix it.** → cannot conclude {11} from n=1, AND cannot assume the batch resolves it. This is a genuine correction to the %12 "weak-signal" framing.

## Effective conditions (W0-W3)
- **W0 (HARD pre-req, before batch convert):** converter naming fix = **Option B (meta-read)** — extend `route_demo_to_bc.py:_offset_from_npz_path` (:520-529) to read the IC offset from the recording META (authoritative) + unique rec-ID demo key + clean byte-id regression. **Option A (IC-offset dir naming) REJECTED** (d1a & c11 both IC(0,0) → `rec_0_0` collision + offset-fake pollutes affine). NON-locked; **%12 review REQUIRED.** convert crashes without it → hard blocker.
- **W1 ({11} spend gate, NOT whole-batch):** before committing {11} recordings, run a **cheap RHOVER-vs-RDESCEND sub-segment ee_only discriminator (~0 GPU, on existing c11/M2)** to separate dilution-vs-noise. NOISE → proceed {11}. DILUTION → HOLD {11} spend + escalate the {11}-mechanism question (%12 + Rs). **The {1}+adjA portion proceeds FULLY regardless.**
- **W2 (deferred to CP-(ii)-5):** bankable physics = mj_geomDistance penetration + intra-finger slip + human-GT (esp {11} real-cable grasp). NOT a proceed-blocker (mechanism verdict = γ⊥).
- **W3 (batch design):** adjA → distinct 5mm-grid reach-screened offsets + avoid val twin-leak → batch whole-demo val becomes a secondary check.

## INVARIANT real-data confirmation (%9)
c11 under the {11} kick: release-margin guard held `regrasp_ok=True` (reach 22→0.8mm) = v2 §D confirmed on a REAL recording.

## §運用14
%12 + %9 rely on %11's skill-path video-analyst (advisory 3 VALID, render byte-matches banked traj) + %12 frame spot-check (c11 68/78/88: dual-arm / cable-held / clips-placed / no explosion-drop-penetration). Bankable physics (penetration/slip/human-GT) = W2 → CP-(ii)-5. **proceed rests on γ⊥.**

## Sequence
%11: **W0 (Option B + byte-id regression) + W1 discriminator (~0 GPU) + batch design (per W1/W3) → report to %12 for review BEFORE batch convert/spend** → %12 review → batch: {1}+adjA full / {11} per W1 verdict → CP-(ii)-4 convert+train → CP-(ii)-5 OG gate (band=γ, W2 physics).
- **rollout PROHIBITED** (別途 Rs GO). 0-commit until %12 commit judgement. band=γ = CP-(ii)-5 only.

— %12 RS-TECH-LEAD 2026-07-03 14:35 JST (with %9 OPS-SUPERVISOR CONCUR-proceed)
