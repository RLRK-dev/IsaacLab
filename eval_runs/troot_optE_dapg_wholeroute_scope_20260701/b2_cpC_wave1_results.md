# CP-C wave-1 results (4 concurrent recordings, GPU-0)

Parallel addendum cfa48d6951. **2026-07-03 02:21 JST.** 0-commit. Launch 02:15:05 → all done 02:20:01 = **~5 min wall for 4 concurrent** (serial est ~11.4h for 17 was over-conservative; a route run is ~5 min).

## Per-offset results
| tag | offset (dx,dy) mm | caveat-a-X Δ (x_grasp) | regrasp verdict | c2_seated_honest | finite/qvel | demo npz | disposition |
|---|---|---|---|---|---|---|---|
| p10_0 | (+10,0) [required #1] | +10.00mm exact | SUCCESS_DUAL_LOADED_AT_88 | True | T/T | 12M | **SUCCESS** |
| m20_0 | (−20,0) | −20.00mm exact | SUCCESS_DUAL_LOADED_AT_88 | True | T/T | 12M | **SUCCESS** |
| p20_p20 | (+20,+20) | +20.00mm exact | SUCCESS_DUAL_LOADED_AT_88 | **False** | T/T | 12M | grasp ✓ / **seat-FLAG** |
| m20_m20 | (−20,−20) | −20.00mm exact | SUCCESS_R_GRIP_L_CAGE_AT_88 | True | T/T | 12M | **SUCCESS** |

## Verdict: NO systemic grasp-miss → fix-⑤ X-follow VALIDATED; proceed pending %12 adjudication
- **fix-⑤ ground-truth exact for every dx:** +10/−20/+20/−20 mm re-center, both X signs + corners. The X-follow generalizes beyond the RUN-2 (+20,0) single point.
- **4/4 grasp-capture + route SUCCESS** (regrasp_ok=True; no R_MISS / drop / IK-NaN / Traceback in any run; all reached ROUTE-LIFT12/12 converged; all demo npz 12M produced).
- Wave-1 early-abort trigger (addendum §2 = "SYSTEMIC grasp-miss pattern") = **NOT triggered.**

## (+20,+20) c2_seated_honest=False — taxonomy (downstream seat, NOT grasp-follow)
- `SETTLED_IN_NOTCH=False`: near-C2 cable z=837.8mm vs groove 829.0 = **8.8mm high** (|d|>3mm → in_groove=False); `cradle_break@X=0.356`, C1 rode high (z_c1 866mm).
- Cause = the KNOWN carried conservatism, worst at the +X corner: `[C2-VERDICT] slide_through=False` (the CPU-rigid しごき — **present identically in RUN-1 baseline + (−20,−20)**) + the (c) "C2-over-solid bottom-claw ride-up / cradle-break" (void X-ceiling 0.366 < C2 X 0.40) which the +X offset pushes further into. Directions: (a) DRAG + (b) C2-unreached = NON-conservative @CPU-rigid (may seat on GPU/flexible); (c) ride-up = conservative-real geometry. Spec R2/R5 carried risk — **not introduced by fix-⑤** (the grasp-follow it validates is SUCCESS).
- §5.3 scripted-SUCCESS filter disposition (grasp+regrasp SUCCESS but c2_seated_honest=False) = **%12 adjudication** (fingerprint-SUCCESS definition). My read: if the fingerprint requires honest C2-seat, (+20,+20) filters OUT of training (survivorship-honest, still counts the feasible-region coverage); the fix-⑤ X-follow validation is unaffected.

## Marker '9' count answer (%12's remaining CP-⑤a item)
My CP-⑤a "9 markers still present" = `grep -ciE "ANTI-REVERT|先祖返り-fenced|DO NOT REVERT"` (line-count over 3 patterns). **ANTI-REVERT alone = 4** (:1756 pin-comment + :4401/:4417/:4516 markers = %12's count). Extra 5 = 2×`先祖返り-fenced` (:3210/:3513) + 3×`Do NOT revert` (:4403/:4419/:4517). Substantive claim (0 marker lines in the diff) holds under both counts. Lesson noted: cite the exact grep pattern for count claims.

## Waves 2-5 plan (pending %12 adjudication)
Remaining 13 offsets (9 training + 4 held-out): (0,0),(+20,0),(0,+20),(0,−20),(+20,−20),(−20,+20),(−10,0),(0,+10),(0,−10) + held-out (±8,±8). ~3 more waves of 4 + 1 = ~15-20 min total. Same isolation (unique dir DEMO_OUT+output_dir, no --record-video, EGL, GPU-0, nvidia-smi cap check per wave). Per-offset FAIL = taxonomy log (not wave abort).
