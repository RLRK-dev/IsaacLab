# CP-A pre-C1 reach screen — FINDING: BLOCK (pre-run structural, no improvisation)

**Charter:** B2 EXECUTION (`charter_b2_execution_coord.txt`, %12→%11). CP-A = "pre-C1 reach screen; MUST consume the real target-derivation code path … NOT a standalone recomputation; ≥6 feasible offsets else BLOCK and report." **2026-07-03 01:12 JST.** 0-commit.

## Verdict: **BLOCK** — the canonical route has NO cable-X follow. Feasible offsets = 5 (all dx=0) < floor 6.

Consuming the REAL canonical target-derivation path (by reading `_run_mujoco_grasp_route`, the actual B2 route) — rather than the `do_p1_grasp`+`grasp_dy` path the charter/③ assumed — surfaces that the offset does NOT flow into the canonical grasp X. This is the exact failure mode "consume the real path, not recompute" is designed to catch: a standalone recomputation using the legacy `settled_grasp_x + grasp_dy` formula would have FALSE-PASSED.

## Mechanism (airtight, all citations verified this session)

**1. The B2 canonical route = `_run_mujoco_grasp_route` (`test:3503`), NOT the legacy `do_p1_grasp`.**
- Dispatch: `s6_grasp_route` (`S6_GRASP_ROUTE=1`) → `_run_mujoco_grasp_route(...)` (`test:6642`). The B2 recorder (`DEMO_RECORD=1`) lives INSIDE it (`test:3536`).
- `do_p1_grasp`/`do_p2_lift` (which hold my ③ `grasp_dy`, `test:2214/2480`) are called ONLY inside `run_episode` (`test:2717`, the legacy P1-P4 VBD flow) → **never reached by the S6 canonical route.**

**2. Canonical grasp-X is a FIXED CONSTANT, independent of dx.**
- `x_grasp = GRASP_X  # 0.30` (`test:3564`) is the ONLY assignment; used at `test:3715/3881/3888/3919/3952`, **never reassigned from a cable measurement.** No `S6_ENGAGE_XC`, no X analog of caveat-a.
- ⇒ the grasp/descend/lift/route EE-X target does not depend on `dx` in any way.

**3. Canonical grasp-Y IS followed automatically (pre-existing, needs NO wiring).**
- caveat-a (`test:3857-3866`): `GRASP_YC = mean(settled cable Y within |Y−S6_ENGAGE_YC|<100mm)`; arms = `GRASP_YC ± GHS` (88mm span, INVARIANT#2). For `dy=±20mm` the cable stays inside the 100mm window ⇒ Y-follow holds.

**4. Cable ∥ Y ⇒ dx is perpendicular (the grasp-critical axis).**
- `add_revolute_cable(..., direction=(0,1,0))` (`test:1369`); `cable_start=(GRASP_X+dx, cable_y_start+dy, …)` (`test:1366`).
- `dy` shifts the cable along its own axis (Y) → caveat-a absorbs it. `dx` shifts the whole cable to `X=GRASP_X+dx`, perpendicular, out the コ mouth (world-X = route axis, `test:3589`). The claws grasp at `X=GRASP_X`; lateral half-extent `LATERAL_MAX_MM=9.0` (`test:3593`) ⇒ **`|dx| ≳ 9mm` → cable outside the claw footprint → grasp miss.**

**5. `grasp_dy` (my committed ③) is INERT for the canonical route** — it is Y-only AND in the wrong (legacy `run_episode`) function AND on a different Y baseline (`WIDE_*_Y≈+0.15` (`task_config:268-269`) vs the canonical caveat-a `GRASP_YC≈0`). Byte-identity (offset UNSET) still holds — the ③ diff is harmless, just not load-bearing for B2. The 縮退 review verified additive/None-path but not that `grasp_dy` reaches `_run_mujoco_grasp_route`.

## Per-offset feasibility (§2.1 grid, structural)

Y-follow = caveat-a (all rows ✓). X-follow = none. Feasible ⟺ dx within the claw footprint (~9mm) AND representative ⟺ dx=0.

| offset (dx,dy) mm | X-follow | grasp feasible | note |
|---|---|---|---|
| (0,0),(0,±20),(0,±10) ×5 | n/a (dx=0) | ✓ | Y-DR only |
| (±10,0) ×2 | NO | ✗ (10>9mm; + non-representative even if edge-grasped) | |
| (±20,0),(±20,±20) ×6 | NO | ✗ (20≫9mm, definite miss) | |

**Feasible = 5 (dx=0 only) < floor 6 ⇒ BLOCK.** (Even counting the 2 marginal ±10mm-X as feasible = 7, those grasp nominal-X while the cable is +10mm off ⇒ non-representative X-DR, not a valid X-offset demo.) Held-out (±8,±8): dx=±8<9mm marginal-feasible in X but likewise non-representative. **Net: the X dimension of the ±20mm XY DR is structurally unsupported — 0 valid X-offset demos.**

## Why a naive IK reach screen would FALSE-PASS (conservatism note)

An IK-only screen that solves IK to the route's targets would report ALL offsets "feasible" — IK to `x_grasp=GRASP_X` always converges (reach ∈ 508-553mm per §6, envelope not breached) — while completely missing that the cable isn't at that X. The binding feasibility axis is **grasp-X-capture**, not reach. IK-residual numbers do NOT prove the grasp captures the offset cable (§運用14: metric ≠ property). Hence this finding is reported structurally, and any IK-residual "PASS" is **non-conservative** (would over-claim feasibility).

## Fix = root cause, requires a LOCKED-file edit ⇒ %12/Rs adjudication (I do NOT decide/implement)

Per Gate-FAIL-fix-first, the root-cause fix is presented first. All are record-only for %12/Rs (charter: locked-file change = STOP + report; §8-6b own L3+DESIGN-GATE+Rs).

- **Opt-1 (root-cause fix — recommended direction): X-follow in `_run_mujoco_grasp_route`** — re-center `x_grasp` on the measured settled cable X (the X analog of caveat-a Y, `test:3866`), None/dx=0 ⇒ byte-identical. Edits the Rs-LOCKED route file ⇒ its own L3 + DESIGN-GATE + Rs GO. Enables the full ±20mm XY DR. *(A COORD inline edit here is forbidden by the charter — surfacing only.)*
- **Opt-2 (interim, no wiring): Y-only DR** — offset dy only (dx=0). caveat-a already follows Y; needs zero code change. But it re-scopes DQ4 (±20mm XY → ±20mm Y) and the feasible-offset count drops to the dy grid ⇒ re-plan the grid to clear the ≥6 floor. Requires Rs confirmation that a Y-only "start" is acceptable.
- **Opt-3:** anything else at %12/Rs discretion.

## Offer (next action, if wanted)
1-shot empirical confirmation: run the canonical route at `CABLE_XY_OFFSET="0.020,0"` (dx=20) vs `"0,0.020"` (dy=20) on cuda:0 (~40-80min) → show grasp-miss for dx vs grasp-hold for dy. The structural fact above is already decisive (x_grasp is a literal constant), so this only adds a physical datapoint; awaiting %12 before any run (checkpoint-gated).

## Constraints honored
No inline fix to any locked file (`test_newton_clip_routing.py`/`og_offline_gate.py`/`B2_KICKOFF_SPEC.md` untouched). No recording started. 0-commit. This is the CP-A checkpoint report; HOLD for %12.
