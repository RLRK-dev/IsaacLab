# CP-⑤b results — RUN-1 (byte-identity) + RUN-2 (dx=+20 confirm) + CP-A′ re-screen

fix-⑤ X-follow proof runs, cuda:0 / MUJOCO_GL=egl. **2026-07-03.** 0-commit (→ %12 one-shot commit after review).

## RUN-1 — None-path byte-identity re-proof = **PASS**
- Cmd: `b2_fix5_run1.sh` (canonical env, **CABLE_XY_OFFSET UNSET**, fix-⑤ harness).
- `route_c2_pin.json` sha256 = `e01ac1fad2ff415538a53c9786a9ed6060cb189b99a4ab6fc5fdda619717df6a` = **baseline (bit-identical, `diff -q` clean; independent recompute concurs)**.
- regrasp_ok=True; LIFT targets X=0.300 (fix-⑤ block NOT fired, dx=0). ⇒ fix-⑤ preserves the None/(0,0)/(0,dy) path **by construction**. **BYTE_IDENTICAL_PASS.**

## RUN-2 — dx=+20 physical confirm = **PASS on the charter bar (grasp-capture + lift HOLD)**
- Cmd: `b2_fix5_run2.sh` (`CABLE_XY_OFFSET="0.020,0"` = dx=+20mm, dy=0).
- **fix-⑤ fired, ground-truth exact:** `[S6_ROUTE] caveat-a-X: x_grasp=+320.00mm (nominal +300mm, delta=+20.00mm)` = measured cable X = GRASP_X + dx **exactly**. caveat-a Y unchanged (GRASP_YC=+150mm, S6_ENGAGE_YC=0.15, dy=0).
- **Grasp-capture + lift HOLD (PASS bar):** cable held through all 12 LIFT substeps (converged, no drop) → C1 seat cable↔C1 = −0.58mm (retained, `c1_retained_lowwall`=True through the drag).
- **Full route (informative, §3.4):** C2 regrasp `SUCCESS_DUAL_LOADED_AT_88` (L=15.96N, R=101.25N, both grip, R-reach resid **1.0mm**, at_88=True, Y-span 88.0mm INVARIANT#2 held); `c2_seated_honest=True` / `SETTLED_IN_NOTCH=True`; `any_table_jam=False`; finite=True, qvel_ok=True.
- **Known carried artifact (NOT a fix-⑤ effect):** `[C2-VERDICT] slide_through=False → MIXED conservatism`. **Parity-verified: RUN-1 (byte-identical baseline) shows the SAME line** ⇒ this is the pre-existing CPU-rigid しごき conservatism (rigid cable + pad-pinned claw μ~0.70 OVERSTATE drag/unreach; direction = NON-conservative @CPU, a flexible/lower-μ/GPU cable may slide+reach better — memory `feedback-ko-guide-drag-c2-conservative`). Unchanged by fix-⑤; a spec R2/R5 carried risk, not a grasp gate.
- **§運用14 video leg (video-analyst, claw-zoom + slip-onset) = PHYSICALLY PLAUSIBLE:** two-arm capture of the +20mm-offset cable VISUALLY CONFIRMED — cable passes through BOTH claw throats (f16-f22) then suspended horizontal off the table (f19-f22) = impossible with edge-grab/empty-close; symmetric grasp (no asymmetric shove, the 2026-06-17 mode avoided). Continuous hold through the R-anchor / L-half-unclamp handoff + drag to C2 (no drop, no pop-out). **No penetration / teleport / NaN.** Only note: a minor TRANSIENT slack-loop/buckle at the C1 throat ~f54-f57 (35-37s, ~78-82%), resolved by f60 — reported, NOT a FAIL. Visual limits (do NOT trigger FAIL): C1 groove-seat depth + final C2 seat/pin not confirmable in the 46s clip (need computational_checks). Video-analyst defers final grasp pass/fail to **human ground truth** (standing memory `feedback-grasp-verdict-...-human-ground-truth`). Artifacts: `scratchpad/va_1783011313/` (p2/p6 zoom strips, sandwich/slip/pen grids); video `~/Downloads/route_fix5_dx+20.mp4`.

## CP-A′ — structural feasibility re-screen (fix-⑤ X-follow) : floor CLEARED
CP-A BLOCK was: 5 feasible (dx=0 only) < floor 6, because the canonical route had zero X-follow. fix-⑤ re-centers x_grasp on the measured cable X for any dx≠0 ⇒ |cable_x − claw_x| ≈ settle-ε (<~2mm) < 9mm for ALL dx:

| offset (dx,dy) mm | CP-A (no follow) | CP-A′ (fix-⑤) | evidence |
|---|---|---|---|
| (0,0),(0,±20),(0,±10) ×5 | ✅ | ✅ (fire OFF, unchanged) | RUN-1 byte-identical + caveat-a Y |
| (+20,0) | ❌ miss | ✅ | **RUN-2 EMPIRICAL** (x_grasp+20.00mm, SUCCESS_DUAL_LOADED_AT_88) |
| (−20,0),(±10,0) ×3 | ❌/marginal | ✅ | structural (same offset-agnostic X-measure mechanism as RUN-2) |
| (±20,±20) ×4 | ❌ miss | ✅ | structural (fix-⑤ X + caveat-a Y, both proven mechanisms) |
| held-out (±8,±8) ×4 | marginal | ✅ | structural (dx=±8 X-follow + caveat-a Y) |

**Feasible = 17/17 (13 training + 4 held-out) ≥ floor 6 ⇒ CP-A BLOCK CLEARED.** Conservatism note: dx=0 rows PROVEN (RUN-1); dx=+20/0 PROVEN (RUN-2); the remaining dx≠0 rows are STRUCTURAL-feasible (the fix measures the actual cable X regardless of dx magnitude — mechanism identical to the RUN-2-confirmed case; caveat-a Y independently proven). Per-offset recording SUCCESS (the §5.3 scripted-SUCCESS filter) is confirmed at CP-C recording, as spec §6 pre-registered.

## Verdict
RUN-1 PASS (byte-identity) + RUN-2 PASS (grasp-capture + lift HOLD at dx=+20, exact +20mm re-center) + CP-A′ floor cleared ⇒ fix-⑤ works. C2-seat しごき MIXED-conservatism = known baseline carried risk (unchanged). Video leg = COMPLETE (§16 above, PHYSICALLY PLAUSIBLE, human-GT deferred). ⟦stale "pending" wording corrected by %12 at commit review 2026-07-03 02:1x; §16 was already final⟧ %12 one-shot commit follows.
