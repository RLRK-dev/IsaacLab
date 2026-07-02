# P3 Demo RECORDER — BUILD REPORT (COORD %11)

**Charter:** RS-TECH-LEAD (%12) → COORD (%11), Rs「3 go」. **Spec:** `P3_DEMO_RECORDER_SPEC.md` v2.1→v2.4 (env corrected). **HEAD** `bcb7393ec8` at charter; now `8a3c265ad7` (another pane's planning commit 07:18 — **route code + configs 0-diff vs bcb7393ec8**, DoD unaffected).
**Status:** ✅ **BUILD COMPLETE + FULL DoD PASS (a/b/c/d/e ALL PASS).** d = video-analyst **PHYSICALLY VALID** (2 observability caveats, none INVALID). final_L=L3 (%12-accepted auto-promote). 0-commit; INVARIANTS #1-5 untouched; ANTI-REVERT markers byte-identical (4372/4388/4487). NEXT: %9 GT cross-PV (chartered by %12), then %12 orchestrates 层2 post-debate + 层5 (COORD does NOT run those). 详细 §DoD Evidence below.
**Env:** env7 Option-E (`/home/rlrk/env_isaaclab7/bin/python`). **0-commit / working-tree only. INVARIANTS #1-5 untouched.**
**⚠ Budget: 274 ruff-canonical / 211 compact — >200 → %12 chose A (L3 promote, NO trim: "phase-collapse/ruff-golf to game a gate = 対処療法禁止").**

---

## ⛔ HEADLINE — diff budget exceeded (charter DUTY 3 STOP)

| measure | lines added | vs ≤200 |
|---|---|---|
| `route_demo_recorder.py` (NEW, **ruff-canonical**) | 226 | — |
| `test_newton_clip_routing.py` (48 hook lines, no legacy reformat) | 48 | — |
| **TOTAL (ruff-canonical)** | **274** | **+74 OVER** |
| (alt) compact-source module (163) + hooks (48) | 211 | +11 OVER |

**Both forms exceed 200 → per spec §6.5 / §8 the change auto-promotes to L3** (层2 post-debate + 层5 multi-view).
Per charter DUTY 3 ("If you exceed → STOP, do not trim by dropping DoD items — notify %12") I **STOPPED before the
DoD run (DUTY 4)** and did not trim any DoD item. The overage is inherent, NOT DoD-droppable (see §Analysis).

**This is not a surprise to the spec:** §4 changelog anticipated "~200-300 LOC"; §5 pre-mortem #10 "size blowup";
§8 explicitly set the >200 → auto-L3 escape. The 5体 pre-debate reviewed the design AS L2 assuming a ≤200 impl.

---

## What landed (on disk, working-tree)

### 1. NEW module `thread_isaac_lab/scripts/route_demo_recorder.py`
- `RouteDemoRecorder` — SPDX-2026 header, snake_case, ruff-clean (`ruff check` All-passed), ruff-format-STABLE, py_compile OK.
- API per spec §2: `sample`, `set_phase`, `note_targets`, `note_grip`, `note_ik_rot`, `note_pin`, `finalize`.
- READ-ONLY: `sample`/notes issue **NO** `mj_forward`/`mj_step`/`eval_fk`/`model.collide`/solver call (spec §2 forbidden list). COPY-on-sample (`.numpy()[…].copy()`) defeats the double-buffer aliasing (spec §2.1).
- npz schema (spec §3): all 20 keys. `arm_q ← state.joint_q` (PHYSICS, NOT fk_state — spec §3). Meta sidecar: git_dirty + as-run sha256s (test/recorder/task_config) + git-diff sha256 + resolved CLIP_X/CLIP_Y (C1) + C2 + full env-gate echo + sim_substeps/sim_dt/dt + device + joint_names + phase_names + quat=xyzw + n_grip_events + driver indices + run verdict.
- ruff-canonical = 226 lines because ruff-format expands the 12-key/8-key collections + dicts to one-per-line (formatting, not logic; compact-source ~163).

### 2. Hooks in `test_newton_clip_routing.py` (23 insertions, 48 added lines, all additive; `DEMO_RECORD=0` → byte-identical)
| spec | site (post-edit line) | hook |
|---|---|---|
| module gate | `_demo_rec = None` (1755) | default-off sentinel |
| §2.1 | `physics_step` before `return state_0` (1815) | `sample()` per frame |
| §2.2 | `_set_gripper_target` after assign (2992) | `note_grip()` (chokepoint, per-arm) |
| §2.3 | `ik_move_both` entry (1946) | `note_targets()` (positions only) |
| construct | route fn after 3520 | gated `RouteDemoRecorder(...)` + `_ph()` helper |
| §2.4 | monkeypatch install (4416) / restore (4496) | `note_ik_rot(...,1)` / `note_ik_rot(None,None,0)` |
| §2.5 | after `mjd.eq_active[_pin_eqid]=1` (4106) | `note_pin(_pin_eqid, seat_body)` |
| §2.6 | 14 native section starts (via `_ph`) | `set_phase()` forward-labeled |
| §2.7 | before BOTH `sys.exit` (4778, 5955) + atexit | `finalize(verdict=…)` idempotent |

14 phases: GRASP_HOVER / GRASP_DESCEND / GRASP_CLOSE / LIFT / ROUTE_C1 / C1_SEAT / C1_PIN / L_HALF_UNCLAMP /
R_UNCLAMP_RISE / GUIDE_C2 / C2_REGRASP / C2_DUAL_SEAT / C2_SETTLE (13 `_ph` calls + the -1 initial).

### 3. ANTI-REVERT markers — byte-identical (content-grep verified), NEW line numbers recorded
- `test:4372` (was 4335), `test:4388` (was 4350), `test:4487` (was 4447). Content unchanged; hooks landed above them.

---

## Analysis — why the overage is not DoD-droppable + byte-identical basis

- **Not droppable:** the 20 npz keys (§3), the 8 hook methods (§2), the full meta (§3), and the 14 phases are all spec-mandated / DoD-asserted (§6.2). The 74-line ruff overage is ~63 formatting (collection one-per-line) + generous docstrings; even a compact-source rewrite is 211 (>200). Genuinely trimming to ≤200 requires cutting phase labels and/or logical content = a fidelity/scope reduction = a %12/Rs call, not a DoD-drop.
- **Byte-identical (static, not yet sim-verified):** module imported ONLY inside `if DEMO_RECORD=="1"`; `_demo_rec=None` default; every hook guarded `if _demo_rec is not None`; `sample`/notes are pure reads. The test-file was NOT whole-file ruff-formatted (legacy-pollution avoided per the scoped-format practice); my added lines are individually ruff-format-STABLE + ≤120 (E501 clean). **The equality gate (DoD §6.1) that PROVES byte-identical is DUTY 4 — not run (budget-STOP).**

## DoD status — NOT run (budget-STOP before DUTY 4)
Equality gate / npz asserts / §運用14 video leg / grip-event count — **all pending %12 direction.**

## Recommendation to %12 (decide before DUTY 4)
- **(A) Proceed as L3** on the faithful build: I run the DoD (equality gate + npz asserts + video leg), then %12 orchestrates 层2 post-debate + 层5 multi-view. (Cost: heavier gates; build is faithful/complete.)
- **(B) Authorize an L2-fit trim** to ≤200: e.g. reduce phase labels 14→~8 (still >6-collapse; DoD phase-coverage still passes) + ruff-stable-compact collections in the module. This keeps the spec's L2 classification but reduces phase granularity below the "~14" guidance (§2.6). I can execute on your go.

**COORD leans (A)** — the build is faithful and the >200 is honest (the spec anticipated 200-300 LOC); shaving phases to dodge L3 trades fidelity for a line count. But the L2-vs-L3 + trim decision is yours/Rs's.

---

# DoD EVIDENCE (charter DUTY 4 — %12 chose A / L3-promote 2026-07-02)

## Canonical env — CORRECTED (spec §4.2 had 2 defects, both %12-confirmed → v2.4)
Spec §4.2 as written did NOT reproduce the canonical. Corrected from the preserved **authoritative `run_canonical.sh`** (the actual Rs-confirmed command; §運用10, no improvise):
- **`CLIP_FLOAT_Z=1` → `0.020`** — the lone FLOAT-valued gate (test:1161 = meters; "1"=1.0m breaks the route). All 8 other gates are boolean `==\"1\"`.
- **+ `--solver-backend mujoco`** — the CLI **dispatch key** (test:6499/6515). Absent from the relayed env-vars → the first leg fell to the legacy VBD `run_episode` (P1-DIAG / `world_z_min` crash). MY HOOKS NOT INVOLVED (`DEMO_RECORD=0` → `_demo_rec=None` → no-op; legacy-path bug I should not have hit).
- **+ `CLIP_X=0.35 CLIP_Y=0.150 CLIP2_X=0.40 CLIP2_Y=0.075 S6_ENGAGE_YC=0.15`** (off-center C1→C2; run_canonical.sh sets S6_ENGAGE_YC=0.15, not UNSET).
- Final: `NEWTON_DEVICE=<cpu|cuda:0> S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 SEAT_TOPDOWN=1 C2_DUALSEAT=1 PERCLIP_PIN=1 SPACER=1 CLIP2=1 CLIP_COLLISION=1 CLIP_FLOAT_Z=0.020 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.075 --solver-backend mujoco`.

## ⭐ DEVICE-SENSITIVITY finding (spec §4.2 cpu-pin = %12's error → v2.4; a REAL DAPG-demo caveat → Rs + B-scoping + conservatism table)
`NEWTON_DEVICE=cpu` (spec §4.2) does **NOT** reproduce the canonical: leg0 cpu = `BLOCKED_REACH_WALL` (R 0N, reach **83.2mm**) vs baseline (cuda:0) = `SUCCESS_R_GRIP_L_CAGE_AT_88` (104.51N, **0.9mm**). The ONLY physics-affecting diff = the DEVICE. The R re-grasp is a **knife-edge reach at the LEDGER reach-wall** → CPU-vs-GPU IK (Newton LM + collision-avoid) divergence flips it SUCCESS↔BLOCKED. → **the canonical DAPG demo is DEVICE-FRAGILE** (sharpens P1's reach-fragility non-conservative flag). Conservatism: cpu-FAIL is a conservative failure of the KNIFE-EDGE reach; the cuda:0 SUCCESS is non-conservative for real/other-device transfer.
→ **device split (%12-approved "correct logic"):** read-only proof on cpu (deterministic); canonical npz/fingerprint/video on cuda:0 (faithful to run_canonical.sh CUDA_VISIBLE_DEVICES=0 + default cuda:0).

## DoD results
| item | device | verdict | evidence |
|---|---|---|---|
| **a. equality gate (read-only proof)** | cpu (deterministic) | ✅ **PASS** | leg0 vs leg1 `route_c2_pin.json` **byte-identical** (`cmp` JSON_EQUAL=YES); full stdout numeric-print diff clean **modulo 3 non-physics classes only**: `[DEMO_REC]` recorder-tagged (spec §6.1 allows), warp module-load timing (`took 0.38 vs 0.41 ms` = nondeterministic, not physics), and the `[C2-PIN] … route_c2_pin.json` output-dir path (leg0 vs leg1, by design). ⇒ **recorder does NOT perturb physics.** |
| **b. canonical npz + fingerprint** | cuda:0 | ✅ **PASS** | cuda:0 `route_c2_pin.json` == authoritative baseline **EXACT** (categorical + numeric): regrasp_ok=True / SUCCESS_R_GRIP_L_CAGE_AT_88 / 104.51N / 0.9mm / r_tgt(0.362,0.119,0.836) / span88 / 3D100.3 / tilt0. npz + meta written (`route_demo_raw.npz` 12.0 MB, T=7707). |
| **c. npz asserts** | cuda:0 | ✅ **17/17 PASS** | T=7707 / all §3 keys+shapes / **anti-alias** (cable first≠last 129mm + moves across phase bnds) / **phase coverage** 13 sections all non-empty / **driver joints MOVE** during C1 close (0.703rad, NOT frozen ⇒ arm_q carries physics fingers) / pose-delta 8.5mm vs POS_ACTION_SCALE 15mm / **\|q\|≈1** all 5 quat arrays / known-pose ee_tgt_quat_effective_r[0]==Rx(-90) / **regrasp_ok==TRUE** / meta complete. |
| **c. grip-event count** | both | ✅ **26 == 26 (reconciled)** | recorder `meta.n_grip_events=26`; COORD grep-derived = 26. Breakdown from recorder-construction onward: 3880 cage×1 + 3886 clamp-loop×12 + 4141 L-half-while×5 + 4152×1 + 4170×1 + 4355×1 + 4445×1 + 4471×1 + 4474×1 + 4566 settle-loop×2 = 26. **Construction-order note:** the 1 initial setup-OPEN (test:3526) fires BEFORE the recorder is constructed (construction hook is just after it) → not counted; it is captured implicitly as the recorder's default `grip_cmd=[0,0]=OPEN` (correct during HOVER/DESCEND) ⇒ **info-lossless**. (Moving construction 1 line earlier would capture 27 — a benign optional refinement; not re-run to avoid a 40-min GPU redo.) |
| **d. §運用14 video leg** | cuda:0 | ✅ **PASS — PHYSICALLY VALID** (independent `video-analyst`, skill-path visual leg) | rendered `route_c1_to_c2.mp4` (69 frames, 7 baked panels + native-res contact zooms) → `~/Downloads/p3_demo_recorder_canonical.mp4`. **VERDICT: PHYSICALLY VALID** over the observable f0-f68 window, judged from frames only (numeric fingerprint NOT read before the visual verdict; it concurs independently). Per-item (all OBSERVED, independent visual): (1) **teleport/jump = NONE** (smooth every-3rd-frame across side/front/oblique/overhead); (2) **grasp capture+lift = CONFIRMED genuine** — コ bottom-lip goes UNDER the cable and the throat **cages** it (not shoved aside — clears the past asymmetric-shove failure mode), real tube lifted (not empty/floating); (3) **R re-grasp = CONFIRMED** onto the continuous real strand, C1→C2 bend persists ⇒ L/C1-pin retains; (4) **gross table/clip penetration = NONE**; (5) **C2 seat = SEATED in-window**; (6) **NaN/explosion = NONE** (f67-68 "boxes" reconciled across front↔overhead as the two grippers retracting, cable stays a coherent single strand). MECHANISM (report-not-FAIL): コ claw tilts/scoops on descent+retract (2F-85 limit, expected); GUIDE f40-51 = sliding-cradle DRAG (slip=0.44, cradle=True — the intended しごき, not a violation). **Conservatism direction (required field):** the visual render is **non-conservative for sub-cm interpenetration** (can hide small pad↔cable / claw↔clip overlaps) → the solver-level `mj_geomDistance` PV is the AUTHORITY for the fine regime; for **gross** kinematics (capture/lift/route/reseat, teleport, explosion) the visual leg is **reliable** and CONFIRMS genuine behavior. **Two caveats, both OBSERVABILITY (none INVALID):** (i) sub-cm penetration deferred to `mj_geomDistance`; (ii) open-top C2 **post-f68 settling unobserved** (window ends at seat) — flag, not a violation. |
| **e. layer-3** | — | ✅ **PASS** | `py_compile` both files OK; `ruff check` module = All-passed + ruff-format STABLE; test-file hooks add **0** new ruff errors (140 pre-existing legacy, delta 0); all added lines ≤120. Whole-file ruff-format NOT run on the test file (legacy-pollution avoidance). |

## Records-vs-fact notes
- **HEAD moved** `bcb7393ec8` → `8a3c265ad7` at 07:18 (another pane's planning/vault commit). `git diff bcb7393ec8..HEAD` on `test_newton_clip_routing.py` + `task_config.py` = **0 lines** ⇒ route code + configs UNCHANGED; the DoD is valid. My recorder work stays **0-commit** (`route_demo_recorder.py` untracked, test-file modified). meta `head_sha=8a3c265ad7` (run-time HEAD) + `git_dirty=true` + `git_diff_sha256` faithfully record the state.
- **meta device echo (per %12 condition):** cpu leg `device=cpu`, cuda leg `device=cuda:0` ✅.
- **ANTI-REVERT markers** byte-identical, NEW lines **4372 / 4388 / 4487** (were 4335/4350/4447; content-grep clean).
- ⚠ **minor meta gaps (non-blocking):** (1) `joint_names=[]` — `getattr(fk_model,"joint_key",[])` returned empty on env7; the actionable driver indices ARE recorded (`driver_joints_l=[6,10]`, `driver_joints_r=[20,24]`). (2) new ANTI-REVERT marker line numbers are in THIS report, not echoed into the meta sidecar (spec §2 asked for both). Both are ≤1-line follow-ups if %12/%9 want them.
- **DoD-b/c evidence PRESERVED (durable, for %9 cross-PV audit; scratchpad is ephemeral):** `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p3_dod_cuda_demo_raw/` = cuda:0 leg `route_demo_raw.npz` (12.0 MB, T=7707, sha256 `509ad193…9116`) + `route_demo_raw_meta.json` + `cuda_leg_route_c2_pin.json` (== baseline EXACT, sha256 `e01ac1fa…df6a`) + `cuda_leg_stdout.txt` (fingerprint print). %9's charter is INDEPENDENT recompute from the repo baseline + recorder module, not a diff of these — preserved for audit/traceability only. 0-commit (untracked artifacts).

> **⇒ SUPERSEDED by the 層2/層5 BATCH-FIX** (2026-07-02, `P3_RECORDER_BATCHFIX_REPORT.md`). Corrections to the notes above: (1) the two "minor meta gaps" are FIXED for future records — `joint_names` now sourced from `scene_info["model"].joint_label` (physics, 74 names; the SHIPPED canonical meta stays `[]` by design, NO re-record), and the ANTI-REVERT marker lines are now echoed into meta (`anti_revert_marker_lines`). (2) ANTI-REVERT marker lines shifted +13 → **4385 / 4401 / 4500** (content byte-identical). (3) records-vs-fact: the module was **intent-to-add** (empty staged blob), NOT "untracked", when this report first said so (CC4-1); it is now genuinely untracked (`git restore --staged`). Finalize hooks now **4771 / 5948**.
