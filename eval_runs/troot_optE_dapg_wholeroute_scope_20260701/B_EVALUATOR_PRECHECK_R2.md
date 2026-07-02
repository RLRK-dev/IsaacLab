# B_EVALUATOR_PRECHECK_R2 — focused re-check of spec v2.1 §10 ERRATA (post-BLOCK)

**Date:** 2026-07-02. **Verifier:** pre-check sub-agent (focused re-check mode).
**Object:** `B_BC_BUILD_SPEC.md` **v2.1** §10 ERRATA (binding) vs `B_EVALUATOR_PRECHECK.md` ISSUE 1-9.
**New fact verified:** recorder COMMITTED as `fd005ab83f` ("Add DEMO_RECORD-gated whole-route demo recorder", 2026-07-02 09:33 JST, HEAD of branch) — exactly 2 files: `route_demo_recorder.py` +315 (new) + `test_newton_clip_routing.py` +68/−3 (`git show fd005ab83f --stat`). Working tree of BOTH files == committed state (sha-identical, verified below).
**Method:** every errata claim re-verified on disk (sha recompute, git-reconstruction replay, hook-site re-grep of the committed file, recorder source read in full, env7-python npz probe, canonical-json read). No prior-pass output reused as evidence.

---

## E1 — sha assert accept-set (ISSUE 1 CRIT) → **RESOLVED**

| Chain element | On-disk result |
|---|---|
| Current `test_newton_clip_routing.py` sha256 | `ac0e3f5311ea71943d02f2ff299f202b8796b36e4c904f9d4923891be29c6eb5` == errata "committed state `ac0e3f53…`" ✓ |
| `git show fd005ab83f:…/test_newton_clip_routing.py \| sha256sum` | `ac0e3f5311ea…` — working tree == committed state, no drift since commit ✓ |
| Equivalence-chain leg 1: `p3_dod_evidence/wt_hook_diff_8a3c265ad7.patch` | EXISTS (14,658 B). Replayed: `git show 8a3c265ad7:…test_newton_clip_routing.py` + `patch -p3` ⇒ sha `9bdf8f63c192739e6beab7c44771eec01415d2d1b03589cfae7212ddc7dcfc34` == meta `as_run_sha256` EXACT ✓ (independently re-executed this pass) |
| Equivalence-chain leg 2: `P3_RECORDER_BATCHFIX_REPORT.md` byte-identity claim | EXISTS — DoD row "`DEMO_RECORD=0` byte-identity (static: gating unchanged) ✅ default `_demo_rec=None` (test:1753) + import-in-gate (test:3532) + 9 `if _demo_rec is not None` guards + `_ph` no-op helper". On-disk grep confirms: `_demo_rec = None` at :1753; ALL recorder touch-points guarded (`:1815, :1950, :2994, :3552, :4135, :4453, :4533, :4770, :5947` = 9 guards + gate :3532) ✓ |
| Runner records actual sha in `runner_verdict.json` | Specified in E1 text ✓ |

**Accept-SET semantics if the file changes AGAIN before build:** third sha ∉ {`9bdf8f63…`, `ac0e3f53…`} → §4.1-2 assert fires → startup STOP → binding-contract escalation (%12). **Fail-closed by construction** — safe. The errata defines no explicit set-extension procedure (new equivalence evidence + spec rev would be needed), but the failure mode is loud, not silent. **LOW note only, no flag.**

## E2 — event/frame ledger convention (ISSUE 2 HIGH) → **RESOLVED**

Convention re-verified against the committed hook sites + recorder internals:
- **Sample is POST-step:** `physics_step` `test:1759`; `_demo_rec.sample(state_0, …)` at `:1815-1816`, AFTER the full `SIM_SUBSTEPS` loop (`:1784-1813`) and final buffer swap — comment "sample the post-step frame". So npz frame f = state AFTER the f-th step ✓.
- **Events are registers, not stamped indices:** recorder (`route_demo_recorder.py:115-124, :150-184`) holds `_grip/_pin_on/_rot/_cur_phase` registers updated at note-time and stamped onto every subsequent `sample` row (`:201-222`). Therefore the npz "event frame" f = FIRST post-step sample reflecting the register = the first frame whose physics already ran WITH the event applied. Replaying "fire BEFORE the physics_step that produces frame f" is exactly demo-faithful ✓.
- **Grip at assign:** `note_grip` inside `_set_gripper_target` chokepoint `test:2994-2995` — note and servo write co-located between steps; servo consumed inside `solver.step` via `vbd_control` (`:1780, :1804`) ✓.
- **Pin post-eq_active pre-settle:** `mjd.eq_active[_pin_eqid] = 1` at `:4134` → `note_pin` `:4135-4136` → 40-frame settle loop `:4137-4138` — matches errata wording exactly; the 40 settle frames call `physics_step` and are ALREADY in the recorded stream, so "no extra settle steps injected / §4.5 mirror wording void" is correct and kills the 7740≠7700 double-step trap ✓.
- **npz probe (env7 python):** pin first-active frame = 2544; override window = 5000..6180 contiguous; `ee_tgt_quat_effective` maxdev = 0.0 both arms; grip init `[0,0]`; per-arm grip transitions = 37; **last event frame = 7617; NO event > frame 7699** → every event lies inside the 770×10 ledger; formula `t=⌊f/10⌋, pos f−10t` well-defined for all events ✓.
- **Event-class sweep for a fire-before-frame counterexample:** grip (register+servo pre-step) ✓; pin (eq poke pre-step, anchor read from pre-step state — replay §4.5 live-derivation reads the same pre-step state) ✓; ik_rot override (register at monkeypatch install; replay is assert-only no-op since effective quat == default all frames) ✓; `note_targets`/`set_phase` are annotations, not replayed events ✓. **No counterexample found.**

## E3 — phase-schema versioning (ISSUE 3 HIGH) → **RESOLVED**

- Committed file has exactly **15 `_ph(` call sites** (re-grep): 13 original + `GUIDE_PRELIFT` `:4232` + `C2_TRANSPORT` `:4535`. Both new labels sit on the SAME mainline blocks as adjacent labels that fired in the canonical run (GUIDE_PRELIFT at the GUIDE_C2 nesting level between `:4205` and `:4398`; C2_TRANSPORT between the fired rot-restore `:4533-4534` and fired `C2_DUAL_SEAT` `:4558`) → any new recording with canonical gates emits **15 phases** ✓ (errata claim correct).
- **13 vs 15 assert-able from meta alone: YES** — recorder builds `phase_names` by set_phase accumulation (`route_demo_recorder.py:144-148`), `_write_meta` emits it (`:300`); canonical meta on disk has `len(phase_names)==13` (probe-verified). `len(meta.phase_names)` is exactly the converter's schema discriminator; mixed-version STOP is well-defined ✓. (Redundant npz check also possible: `unique(phase_id)` = −1,0..12.)

## E4 — cable_body_start=28 + self-validating assert (ISSUE 4 MED) → **PARTIAL**

- **Constant re-verified on the npz (env7 python):** pin fire frame 2544, `pinned_body`=55, argmin-to-C1 at the FIRE frame = 27 → `cable_body_start = 55 − 27 = 28` ✓. seg27→C1 = **2.81mm** (seat). Derivation and constant are CORRECT.
- **The assert AS WRITTEN is NOT computable/validating numpy-only — two defects:**
  1. **Circular reference:** "(pin-frame pinned-body pos)" has NO independent npz source (probe: no global-body-position array; `arm_q` is joint coords). The only accessor is `cable_xyz[t_pin, pinned_body−28]` — which USES the constant under test → the distance is identically 0 and the assert passes vacuously (validates nothing).
  2. **Threshold non-discriminating even under the charitable reading** (compare vs `meta.resolved_clip_c1_xy`): a wrong constant 27 → cable index 55−27=28 → measured dist **12.22mm < 15mm** → the assert PASSES on the off-by-one it exists to catch.
- **Working replacement (computable + discriminating, numpy+meta only):** assert `argmin_s ‖cable_xyz[t_pin, s, :2] − meta.resolved_clip_c1_xy‖ == pinned_body − 28` (threshold-free, exact; measured: argmin=27 ✓, runner-up 12.2mm away). Echo `cable_body_start` into dataset meta as ISSUE 4 asked (errata is silent on the echo).
- Severity of the residual: **MED** on the errata text (the pinned constant is right and independently verified, so the build is not endangered TODAY; but the shipped guard formula provides zero protection and must be replaced before the converter is coded).

## E5 — stale anchors → indicative + re-grep policy (ISSUE 5 MED) → **RESOLVED**

Policy fix (anchors indicative; builder MUST re-grep vs `fd005ab83f`; resolved anchor table in the build report) is actionable. Spot-verified the drift examples on the committed file: `__main__` at **:6912** ✓; 4-way verdict block at **:4506-4515** ✓ (read on disk; old :4495-4502 now lands in the ANTI-REVERT comment area); `_c2_regrasp_rec` **:4523-4531** ✓; `physics_step` **:1759** ✓; `make_solver` import/call/solref-wire **:6613/:6615/:6623** ✓; `state = model.state()` in main **:6595** ✓; `_ANTI_REVERT_MARKER_LINES = [4385, 4401, 4500]` at :1756 ✓ (errata footer values match). Drift magnitudes consistent with "+3..+14".

## E6 — grip_cmd [L,R] + vbd_control provenance (ISSUE 6 MED) → **RESOLVED**

- **Recorder source:** `_grip = np.zeros(2)` documented "[L, R] last-commanded servo rad" (`route_demo_recorder.py:119`); `note_grip` maps `l_drv`→col0, `r_drv`→col1 (`:156-164`). Construct passes `driver_joints[:2]` = L, `[2:]` = R (`test:3535-3536`, "per-arm drivers, SSOT :1461"); canonical meta `driver_joints_l=[6,10]`, `driver_joints_r=[20,24]` ✓.
- **Behavioral npz confirmation:** during L_HALF_UNCLAMP (frames 2584..2693) col0 ramps 0.7407→0.6900 while col1 stays 0.7407 — col0 IS the L arm ✓. Errata's "[L, R] — OPPOSITE of the action layout (R-then-L)" is exactly right.
- Servo-object rule matches code: `physics_step` consumes `scene_info["vbd_control"]` (`test:1780`, step at `:1804`) ✓.

## E7 — C2-seat knife-edge margins (ISSUE 7 MED) → **RESOLVED**

Canonical `p3_dod_cuda_demo_raw/cuda_leg_route_c2_pin.json` `route_c2_settle`: `cable_c2_released_mm = −0.392` vs ≤0.5 bar → margin **0.892mm** ✓; `near_c2_cable_z_released_mm = 830.6` vs `groove_z_mm = 829.0`, |Δ|=1.6 vs ±3.0 bar → margin **1.4mm** ✓; `settled_in_notch = True`. Both errata numbers exist verbatim in the durable evidence. Wide-margin contrast also present (`r_reach_resid_mm = 0.9` vs 20mm bar; `r_grip_N = 104.51` vs 0.1N). Added seat-z tracking at C2 landmarks + explicit margin-consumption reporting = actionable and correctly targeted.

## E8 — video leg + IK-failure policy (ISSUE 8 MED) → **RESOLVED**

- **Capture pattern exists and is mirrorable:** `_cap` (`test:3786+`, also `:3322`) = offscreen `mujoco.Renderer.update_scene + render()` per named camera → composite frame; no viewer/GUI dependency; the evaluator can call the same pattern per control step behind `--record-video` → mp4 post-hoc. LOC risk now explicitly scoped.
- **Failure policy mirrors the actual code semantics:** `solve_ik_dual` returns `(result, cost)` and has NO raise path for non-convergence (`test:1823-1912`); the route's NaN handling is print + `return state, False` (log-and-continue, `ik_move_both`). "log + continue + tag frame in runner_verdict.json; hard crash → artifacts tagged INVALID, never counted" is implementable and closes the B1-taxonomy hole (ik-tagged frames give the `ik_failure` attribution the first pass asked for).

## E9 — startup additions (ISSUE 9 MED) → **RESOLVED**

- `state = model.state()` — present in route main at `test:6595` ✓ (checklist §4.1-5.5 mirrors it).
- **`DEMO_RECORD=0` forcing pre-import: POSSIBLE and doubly safe** — the gate is read INSIDE the route fn (`os.environ.get("DEMO_RECORD","0")=="1"` at `test:3532`, under `global _demo_rec` :3531), NOT at import time; so (a) setting env before import trivially wins, and (b) the evaluator never calls the route fn at all → `_demo_rec` stays `None` and all 9 hooks are no-ops regardless ✓.
- Null-skip: canonical meta `env_gates.C2_TILT_SIGN = None` (probe-verified) → skip-null rule prevents the `"None"`-string poisoning of `test:4404` consumers ✓.
- task_config extension: current `task_config.py` sha256 = `1a0851db9cfc2c740c98821c73c84f5405d1cc96df5fe22a71f66906bb1762bc` == errata "as-run `1a0851db…`, currently unchanged" ✓ (recomputed this pass).

---

## NEW ISSUES (introduced by / missed by the errata)

### NEW-1: the evaluator's import surface lives in an UNCOMMITTED, UN-SHA-GATED `newton_skill_env_base.py`
**SEVERITY: MEDIUM**
**EVIDENCE:** `git status` — base is working-tree modified (+301/−13 vs HEAD). `_wire_s6_grasp_solref` (def :1343) **does not exist at HEAD** (`git show HEAD:…/newton_skill_env_base.py | grep _wire_s6_grasp_solref` → no match; the function was RELOCATED to base per `test:2998/:6611-6613` and exists only in the dirty tree). Spec §4.1-2 imports `make_solver, _wire_s6_grasp_solref` from base; the demo's grasp-contact physics is co-determined by this file. Yet meta `as_run_sha256` pins only 3 files ({test, recorder, task_config} — `route_demo_recorder.py:63-67 _PROV_RELPATHS`), and E1/E9's extended sha gate covers route-file + task_config ONLY. The whole-tree `git_diff_sha256` (`62a9baca…`, `git_dirty=True`, head `8a3c265ad7`) is already stale (route file changed since) and is not per-file resolvable.
**CONSEQUENCES:** (a) clean checkout / revert of base before build → ImportError at §4.1-2 = **loud, fail-closed** (and `fd005ab83f` alone is NOT a self-contained substrate — the canonical route itself cannot run from a clean checkout); (b) a DIFFERENT base edit (multi-pane repo) → **silent substrate drift**, only partially caught at runtime by §4.1-7's solref-readback parity assert (solref values only; `make_solver` / multiworld changes unguarded); (c) records gap — the canonical demo's substrate is co-determined by a file with no durable per-file pin, and future B2 re-records inherit the omission via `_PROV_RELPATHS`.
**FIX (cheap):** commit the base state (or record `sha256(newton_skill_env_base.py)` NOW into the spec/errata as a third pinned sha, assert it at §4.1-2, echo it in `runner_verdict.json`); add base to recorder `_PROV_RELPATHS` for all future records (one tuple).

### NEW-2: E4's self-validating assert formula (errata-authored) is circular and non-discriminating
Covered under **E4 PARTIAL** above (defects (1)+(2) + working replacement). Errata-introduced text defect; MED; converter-code-time fix, no re-record needed.

### NEW-3 (note, LOW): E1 accept-set has no set-extension procedure for a future third sha
Fail-closed by construction (assert fires → STOP → %12 per binding contract). Acceptable; a one-line "any further route-file change re-opens the errata" would make it explicit.

---

## SUMMARY
- **E1 RESOLVED / E2 RESOLVED / E3 RESOLVED / E4 PARTIAL / E5 RESOLVED / E6 RESOLVED / E7 RESOLVED / E8 RESOLVED / E9 RESOLVED** — the CRIT (B0 unreachable) and both HIGHs (frame-ledger double-step, phase-schema break) are genuinely closed with on-disk evidence; commit `fd005ab83f` state == working tree == the errata's pinned sha.
- Residuals: **2 MED** — (i) E4's guard formula is vacuous as written (constant 28 itself is verified correct; replace with the exact argmin-vs-`resolved_clip_c1_xy` form + meta echo before converter coding); (ii) NEW-1 base-env un-pinned/uncommitted dependency (fails loud in the revert case; silent-drift window partially covered by the §4.1-7 solref parity assert; fix = commit or pin+assert one more sha). Plus 1 LOW note (E1 set-extension).
- Neither residual makes B0 unreachable or corrupts the dataset schema; both are one-line-class spec/errata patches (v2.2) or a base commit, NOT design rework.

## VERDICT: **WARN** — build may charter once the two MED items are folded into the errata (E4 assert formula fix + base-env sha pin/commit); no BLOCK-class defect remains.
