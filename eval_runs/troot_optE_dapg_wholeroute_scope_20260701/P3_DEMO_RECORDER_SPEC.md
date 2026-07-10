---
doc_class: design-surface
---

# P3-prep — Whole-route demo RECORDER spec **v2.4** (ROUTE_DEMO_RAW_v1)

**Author:** RS-TECH-LEAD (%12). **Date:** 2026-07-02. **HEAD** `bcb7393ec8`, env7 mujoco-コ (env_isaaclab7).
**v2 changelog:** v1 was adversarially reviewed by the 5体 CC debate (CC2 impl / CC3 invariants / CC4 rules / CC5 sufficiency / CC6 NHA — 32 challenges, ALL ACCEPTed; NHA verdict = CHANGE_JUSTIFIED conditional). v2 folds every fix. **v2.1:** independent re-verify = all 25 fixes FOLDED-OK, zero architectural defects; this pass applies its 5 editorial findings (cite-drift ×4 clusters, +2 servo sites `:4431/:4434`, event-vs-site count basis, `ee_tgt_pos` initial fill). Key v1 defects fixed: WRONG anchors (`run_episode` = 先祖返り-fenced legacy VBD driver; engage-close `:3353-3369` = dead branch), gripper hooks → chokepoint, quat-target fabrication, double-buffer aliasing, finalize-vs-sys.exit, device pin, arm_q source, substep conservatism, L2 size arithmetic, sidecar provenance.
**Authorization:** Rs 2026-07-02「継続 推奨で良い」+「3 go = Q3 demo recorder go」. Build executor = COORD (%11); GT cross-PV = OPS-SUP (%9). Q1 (UNIT) = Rs-pending — this artifact is Q1-invariant.
**Constraint:** 0-commit / working-tree only / INVARIANTS #1-5 untouched / recorder NEVER writes physics state.

---

## §0. Goal / non-goals

**GOAL:** a UNIT-independent RAW superset recording of the committed square-on C1→C2 route —
**`_run_mujoco_grasp_route` (`test:3486`, env-gate `S6_GRASP_ROUTE=1`, dispatched FIRST at `test:6568-6572`)** —
into `route_demo_raw.npz` + meta sidecar, so any UNIT Rs picks at Q1 can derive its (obs, actions) via a
**separate offline converter** (a P3 follow-on deliverable — NOT `train_common.py`'s `convert_demos` hook,
which only massages arrays already keyed `obs`/`actions` loaded at `train_common.py:312-313`).

⛔ **NOT the recording target:** `run_episode` (`test:2702`) = the legacy VBD-track episode driver
(main `test:6563` "the full VBD episode below is NOT ported"; docstring `test:3193` 先祖返り-fence). v1 cited it
in error — 3 debate agents caught it. Likewise `_run_mujoco_grasp_engage_episode` (`test:3184`) is a
mutually-exclusive `elif` branch; its close code `:3353-3369` never runs under the route gate.

**Scope honesty (CRIT2 partial):** 1 deterministic demo = PREREQUISITE artifact only — **this npz alone does
NOT make DAPG/BC trainable**; demo-SET size/diversity under DR = open Rs question (DR range Rs-reserved,
`task_config.py:257-262`; SPEC_77:56-58 caveat — grasp_y sweep is NOT a diversity proxy). Pre-check CRIT2
remains PARTIALLY open until the SET question is decided.

**NON-GOALS (§運用24):** NO whole-route env build (Q2). NO 49D/12D conversion (UNIT-dependent → after Q1).
NO DR demo-SET recording. NO RL. NO reward. NO route-motion change.

## §1. Prior-art disposition + §運用4 duplicate-check (per-artifact, on-disk verified)

`check_thread_vault_prior_art.sh` blocker context = the COORD2 scoping doc's OWN recommendation
(`DAPG_WHOLEROUTE_C1C2_SCOPING_COORD2.md:70` item 5: reuse the SPEC_77 logging pattern, hook the committed
route, ~200-300 LOC) — guidance, not a failed path. New directive = Rs today.

| Alternative | Verdict | Evidence |
|---|---|---|
| `eval_runs/troot_optE_rs71_kinematic_retention_20260616/r_s71_grasp_demo_record_77.py` | pattern-REUSE only | inline REST/APPROACH/DESCEND/LIFT choreography `:94-116`, own scene `:66` — cannot replay the route; npz dict-append pattern `:78-123` reused. ⚠ its per-sample `mujoco.mj_forward` (`:82`) is a state-visible write — **must NOT be ported** (§2 forbidden list) |
| `thread_isaac_lab/scripts/collect_expert_demos.py` | ⛔ banned | imports DELETED env6-VBD envs (`:186,191`; deletion `13f3d55c0a`) = 先祖返り |
| `thread_isaac_lab/scripts/collect_grip_demos.py` | unusable | env-bound (`NewtonGripEnv.step()` 42D/14D `:12,38`) — the whole-route env is the ABSENT artifact |
| `thread_isaac_lab/scripts/convert_m3_to_*_demos.py` | converter not recorder | HDF5→npz for deleted AR env; proves the raw→convert house pattern only |
| route's own logging | insufficient | `RawEvidenceLogger` = phase-boundary snapshots wired to the legacy `run_episode` path (`test:2083-2131`, `:2437-2757`); `route_c2_pin.json` (`test:4700-4708`) = scalar summaries. No per-frame state exists |

→ NEW recorder justified; no equivalent exists (NHA CHANGE_JUSTIFIED).

## §2. Mechanism (additive, env-gated `DEMO_RECORD=1`, read-only)

**New module** `thread_isaac_lab/scripts/route_demo_recorder.py`: `RouteDemoRecorder` — append buffers,
`sample(state, scene_info)`, `set_phase(name)`, `note_targets(tL3, tR3)`, `note_grip(driver_joints, target_rad)`,
`note_ik_rot(quat_L, quat_R, override_active)`, `note_pin(eqid, body_idx)`, `finalize(out_path, verdict)`.
SPDX 2026 header, snake_case. Output dir via `DEMO_OUT` (default `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/demo_raw/`).

**Hooks in `test_newton_clip_routing.py` (ALL additive one-liners; `DEMO_RECORD=0` → byte-identical behavior,
module imported ONLY under the gate):**
1. `physics_step` (`test:1752`) → `sample()` per frame. ⚠ **COPY semantics MANDATORY**: `physics_step`
   ping-pongs TWO State objects (`_physics_state_buffer` `test:1741`, swap `test:1806`) and `.numpy()` is a
   zero-copy VIEW → append-without-copy aliases every stored frame to the final buffers. `sample()` must
   `.numpy()[…].copy()` (in-route exemplar: `test:4075` `state.body_q.numpy()[…].copy()`).
2. **`_set_gripper_target` (`test:2975`) = the gripper CHOKEPOINT** → `note_grip`. Per-arm attribution by
   intersecting `driver_joints` with the L_drv/R_drv index sets. (v1's call-site enumeration REJECTED — the
   executed route path has 12 servo SITES: `:3516, :3850-3865, :4106, :4117, :4134, :4318, :4405, :4431, :4434,
   :4522, :4555`; a 2-site hook records a silently wrong `grip_cmd`. Count basis for the DoD = command EVENTS
   incl. loop multiplicities — e.g. `:3856-3858` fires ×12, `:4519-4522` ×2 — not bare grep site count.)
3. `ik_move_both` entry (`test:1918`) → `note_targets` — **POSITIONS ONLY** (the signature has no quat).
4. **Rotation register** (v1's "quat at ik_move_both entry" was impossible): recorder-owned effective-rotation
   state, default = the `solve_ik_dual` constant Rx(−90°) xyzw (`test:1858`); one-liner `note_ik_rot` updates at
   the C2 monkeypatch INSTALL (`test:~4400`) and RESTORE (`test:~4479`) sites, recording the per-arm override
   quats + `ik_rot_override_active[T]`. Channel name = `ee_tgt_quat_effective` (labeled DERIVED, not commanded).
5. eq-pin: `note_pin` **AFTER activation** (`test:4090` `mjd.eq_active[_pin_eqid]=1` — NOT the flag-parse block
   `:4063-4071`), recording `_pin_eqid` + pinned body idx.
6. `set_phase("<native-section-name>")` at each route section boundary inside `_run_mujoco_grasp_route`
   (~14 native sub-phases; NOT the 6-phase collapse — that mapping is convert-time).
7. **finalize:** `atexit`-registered at recorder construction (env-gated) **+ explicit calls immediately before
   BOTH `sys.exit` sites** (the C2 block exits mid-function at `test:~4712` and never reaches the fn tail — the
   verdict dict `_c2_regrasp_rec`/`route_c2_pin` fields exist only in that block; a tail-only finalize writes NOTHING).

**Forbidden-call list (read-only operationalized):** inside `sample()`/hooks — NO `mujoco.mj_forward`, NO
`mj_step`, NO `eval_fk`, NO `model.collide`, NO solver calls. Reads = `state.*.numpy().copy()` + existing pure
accessors only (`get_ee_positions` `test:1905` is position-only; EE quat = NEW read `body_q[ee, 3:7]`, xyzw).

**Anti-revert gate:** the 3 Rs-LOCKED markers (currently `test:4335/4350/4447`) byte-identical post-edit
(content-grep); hooks land ABOVE them → their line numbers WILL shift → build report + meta record the NEW
line numbers (records-hygiene).

## §3. Schema — `route_demo_raw.npz` (T = physics frames @ DT=1/480 `test:124`; S = 40 cable bodies `task_config.py:135`)

| key | shape/dtype | content / source (PINNED) |
|---|---|---|
| `frame_idx`, `sim_time` | [T] i64/f64 | frame counter, t=frame×DT |
| `phase_id` (+`phase_names` meta) | [T] i16 | native route section |
| `ee_pos_r/l`, `ee_quat_r/l` | [T,3]/[T,4] f32 | ACTUAL EE pose ← `state.body_q[ee]` (pos `[:3]`, quat `[3:7]` **xyzw**) |
| `ee_tgt_pos_r/l` | [T,3] f32 | last-COMMANDED positions (ik_move_both entry; held between commands). **Initial fill (pre-first-command frames, before `test:3839`) = actual EE pos at recorder construction** — no undefined frames |
| `ee_tgt_quat_effective_r/l` | [T,4] f32 | DERIVED rotation register (§2.4) — default Rx(−90°) const; NOT a commanded stream |
| `ik_rot_override_active` | [T] i8 | C2 monkeypatch window flag |
| `arm_q` | [T,Q] f32 | ← **`state.joint_q` (PHYSICS vector)**. ⛔ NOT `fk_state.joint_q` — route runs `gripper_dynamic=True` (`test:3515`): FK fingers stay frozen ~0.0 (`test:1785-1794`, `:1980/:1986-1989`, `:3807-3812`); only physics joint_q carries servo-achieved fingers |
| `grip_cmd` | [T,2] f32 | last-commanded servo per arm ← chokepoint (§2.2) |
| `cable_xyz`, `cable_quat` | [T,S,3]/[T,S,4] f32 | ALL cable body poses (superset; see arrow caveat below) |
| `nearest_seg_r/l`, `held_seg_l` | [T] i16 | argmin seg indices |
| `pin_active`, `pinned_body`, `pin_eqid` | [T] i8/i16/i16 | eq-pin state (post-activation) |

**Meta sidecar `route_demo_raw_meta.json`:** head_sha + **`git_dirty: true`** + **sha256 of the 2 as-run files**
(`test_newton_clip_routing.py`, `route_demo_recorder.py`) + `git diff HEAD | sha256` + task_config sha256 +
**RESOLVED numeric clip poses** (C1/C2 — env-var-driven `CLIP_X`/`CLIP_Y` `test:3524-3525`, so a config hash does
NOT pin them) + full env-gate echo + `NEWTON_DEVICE` + **`sim_substeps=10` + `SIM_DT`** + solver backend + DT +
`phase_names[]` + **`joint_names[]`/driver-joint indices** + the run's OWN verdict (`regrasp_ok` etc.) + recorder
version + quat convention (**xyzw, warp**) + new ANTI-REVERT marker line numbers.

**Sufficiency map (REWORDED — raw-SUFFICIENCY ≠ derivation-SOLVED):**
- 49D obs: all dims derivable from raw — with the CORRECT convert-time pipelines:
  obs[0:16] ← EE poses + **physics** finger q; obs[16:19] ← cable_xyz + seg idx (SEAT-phase seated-seg re-index
  = convert-time ISSUE8 fix); **obs[19:23] ← cable TANGENT → `compute_hand_quat_for_cable` + `KO_BASE_HAND_DOWN_QUAT`
  (AC:824-836) — NOT cable body quats** (body quats are solver-internal/twist-arbitrary; the raw field is superset
  only); obs[3:7]/[11:15]/[19:23] additionally need the STATEFUL `temporal_quat_consistency` replay (AC:798-812)
  at the chosen cadence (train_common's static w≥0 flip is NOT equivalent at sign boundaries); obs[23:30] ←
  sidecar RESOLVED clip poses; obs[30:42] err dims ← derivable (seg-relative per AC:838-841); phase one-hot ←
  phase_id mapping; held_cable_z ← cable_xyz[held_seg_l].z.
- 12D actions: **raw supports BOTH synthesis routes; WHICH is BC-valid = a Q1/convert-time DECISION, not solved
  here.** Target-deltas = zero/spike train (`ik_move_both` solves once + FK-interps `test:1962-1996`; e.g. the
  100mm transport jump ≈ 6.7× POS_ACTION_SCALE 0.015 at one boundary) → needs boundary re-chunking. Pose-deltas
  = smooth (~2mm/RL-step) but encode the interp schedule. **Rot dims [3:6]/[9:12] carry NO commanded signal**
  (constant Rx(−90°), C2_TILT_SIGN=0) + G7 ~100× under-apply in the target env → label semantics = Q1/Q5 question.
- Gripper channel ← grip_cmd (separate channel per SPEC_77 convention).

**CONSERVATISM directions (mandatory field, GROVE §2.2):**
| claim | direction | note |
|---|---|---|
| demo states @ SIM_SUBSTEPS=10 (SIM_DT=1/4800, `task_config.py:101`) consumed by env @ RL_SIM_SUBSTEPS=4 (1/1920, base:95, AC:1201) | **NON-CONSERVATIVE** | demo drawn from 2.5× finer contact integration — cage/close/drag behavior may not reproduce under coarser env dynamics → convert/env-time re-validation gate |
| CPU-newton demo vs GPU-cg env consumption | **unknown** | cg-GPU whole-route validity screen = pending (cross-PV gate iii) |
| pin-ON dynamics embedded in demo | **NON-CONSERVATIVE vs pinless deploy** | see §4 LOUD FLAG |
| **DEVICE-FRAGILITY of the canonical demo (v2.4)** | **NON-CONSERVATIVE** | the canonical route is cuda:0-SPECIFIC — cpu-IK cannot even reproduce it (reach knife-edge flips to BLOCKED). The recorded demo inherits a trajectory sitting on the R-reach-wall knife-edge → BC/DAPG consumers must match device (cuda:0) AND treat reach-margin as a first-class robustness gap (sharpens P1 risk④ reach-fragility) |

## §4. LOUD FLAGS for Q1/Q2 (Rs — recorded, NOT silently embedded)

1. **pin-ON vs pin-OFF demos = Rs design Q (INVARIANT#5-adjacent):** the canonical route holds C1 via the
   Rs-authorized eq-pin; a demo-trained policy learns C1-stays-seated dynamics whose CAUSE is absent from any
   obs (§運用21 class for the downstream env). Pin authorization covers the ROUTE; whether TRAINING DATA may
   embed it = a separate Q1/Q2 decision. The recorder records `pin_active` faithfully AND flags this here.
2. **Canonical config PINNED for DoD (v2.3; v2.2 corrected COORD catch #1-2 [CLIP_FLOAT_Z float-typo + missing
   position envs]; v2.3 corrects #3-4 from the authoritative `run_canonical.sh`):**
   **CLI: `--solver-backend mujoco`** (`test:6499/6515` — the mujoco-dispatch key; WITHOUT it the run falls to
   the legacy VBD `run_episode` = v2.2's miss, env-vars alone are NOT the full invocation) + env
   `S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 SEAT_TOPDOWN=1 C2_DUALSEAT=1 PERCLIP_PIN=1 SPACER=1
   CLIP2=1 CLIP_COLLISION=1 CLIP_FLOAT_Z=0.020 CLIP_X=0.35 CLIP_Y=0.150 CLIP2_Y=0.075 S6_ENGAGE_YC=0.15`;
   **DEVICE (v2.4 CORRECTION — COORD empirical catch #5): the canonical is `cuda:0`** (`CUDA_VISIBLE_DEVICES=0`
   + script default `NEWTON_DEVICE` cuda:0, per `run_canonical.sh`). v2.2-2.3's `NEWTON_DEVICE=cpu` pin was
   EMPIRICALLY WRONG for reproduction: on cpu the R re-grasp hits the reach-wall knife-edge and BLOCKS
   (R 0N / reach 83.2mm vs canonical 104.51N / 0.9mm) — the CPU-vs-GPU IK (Newton LM + collision-avoid)
   divergence flips SUCCESS↔BLOCKED. **Device split for the DoD:** cpu = the EQUALITY-PROOF substrate only
   (deterministic; leg0-vs-leg1 byte-identity proves the recorder read-only, route-outcome-independent);
   the SHIPPED demo npz + fingerprint + video = **cuda:0** (canonical-faithful). Meta echoes DEVICE per leg;
   `C2_TILT_SIGN` **UNSET** (committed default 0, Rs-locked `test:4353`). ⚠ `S6_ENGAGE_YC=0.15`: v2.2 said
   UNSET based on the CHARTERS (zero hits) — but the EXECUTED `run_canonical.sh` sets 0.15 (evidence-tier
   lesson: the run script outranks the charter; likely inert since the route hardcodes GRASP_YC re-centering
   `test:3527`, but the DoD matches the authoritative command EXACTLY). **The full authoritative invocation =
   `canonical_run_records/integrated_route/run_canonical.sh`** — the DoD baseline runs THAT command shape. CLIP_X/CLIP_Y must be explicit: build-side default = task_config
   `CLIP1_*` (`test:1153-1154`) but route-target default = 0.40/0.0 (`test:3549-3550`) — a dual-default mismatch
   unless pinned. **EVIDENCE (authoritative, preserved from the volatile %2 scratchpad 2026-07-02):**
   `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/canonical_run_records/integrated_route/run_canonical/
   route_c2_pin.json` — the Rs-viewed canonical run's OWN config echo (`x_clip=0.35, y_clip=0.15,
   clip_float_z_mm=20.0, spacer_on=True, c2x=0.40, c2y=0.075`) + fingerprint (`regrasp_ok=True,
   SUCCESS_R_GRIP_L_CAGE_AT_88, r_grip 104.51N, reach 0.9mm, r_target (0.362,0.119,0.836), Y-span 88,
   3D 100.3, tilt_sign 0.0`); P1 run echo = MATCH (same dir `p1_probe/run_p1/`). The DEMO_RECORD=0 leg must
   reproduce this fingerprint BEFORE the equality gate counts (empirical backstop for any env mistake).
   All lineage charters preserved at `canonical_run_records/charters/`.
3. Single-demo insufficiency (§0) — do not over-close CRIT2.

## §5. Pre-mortem (v2)

| # | failure mode | mitigation (now designed-in) |
|---|---|---|
| 1 | recorder perturbs physics | forbidden-call list + read-only copies + STRENGTHENED equality gate (§6.1) |
| 2 | aliasing (double-buffer views) | copy-on-sample MANDATE + anti-aliasing DoD assert |
| 3 | wrong joint vector (FK fingers frozen) | arm_q source PINNED to `state.joint_q` + finger-movement DoD assert |
| 4 | grip_cmd stale/wrong | chokepoint hook + transition-count DoD |
| 5 | npz never written (mid-fn `sys.exit`) | atexit + explicit finalize before BOTH exits |
| 6 | phase labels drift | explicit set_phase per section; reviewer checks vs section prints |
| 7 | quat convention mixup (xyzw/wxyz seam `test:2350-2352`) | xyzw declared everywhere + finalize |q|≈1 + known-pose spot-check vs Rx(−90°) |
| 8 | locked sections touched / line drift | content-grep gate + new line numbers recorded |
| 9 | GPU nondeterminism poisons equality gate | NEWTON_DEVICE=cpu pinned BOTH legs |
| 10 | size blowup | ~27-50 MB est (T≈20k, S=40) + T sanity bound |

## §6. DoD + verification plan

1. **Equality gate (DEMO_RECORD=0 vs 1, both `NEWTON_DEVICE=cpu`, exact §4.2 gate set):** verdict-JSON fields
   equal **+ final full-state hash equal (`state.body_q`+`joint_q` byte-compare) + full stdout numeric-print diff
   clean (modulo recorder-tagged lines)** — verdict-fields-only is NECESSARY-not-SUFFICIENT (CC4).
2. **DEMO_RECORD=1 canonical run:** npz loads; all §3 keys/shapes; T>0 within sanity bound; phase coverage = all
   sections non-empty; `regrasp_ok=TRUE`; **anti-aliasing assert** (cable_xyz differs first/last frame + across
   phase boundaries); **grip transition count == COORD's grep-derived servo-event count on the executed path**;
   **driver-joint columns MOVE during the C1 close window (`test:3850-3865`)**; every-10th-frame pose-delta max
   reported vs POS_ACTION_SCALE (0.015) + rot-delta vs ROT_ACTION_SCALE; all quat arrays |q|≈1 + known-pose check.
3. **§運用14 video leg: INCLUDED** (v1's justified-omission RETIRED per CC4) — run with `HARNESS_RECORD_VIDEO=1`
   (`test:6453` gate) + skill-path visual leg (`/video-analyzer` or video-analyst) on the recorded run.
4. Layer-3 mechanical: `./isaaclab.sh -f` + py_compile; **/rule-check stage2 BEFORE editing** (COORD duty).
5. **Diff budget: total ≤200 lines** (new module + hooks, code files). If exceeded → STOP, auto-promote **L3**
   (層2 post-debate + 層5 fire), notify %12/Rs. (Fixes v1's false "200-300 LOC → L2 band" arithmetic.)
6. %9 OPS-SUP GT cross-PV — INCLUDING verification of the §8 L-demotion grounds (log:6755 precedent).
7. 層5 count basis: tracked-modified + untracked-added **code** files (run artifacts npz/json + docs excluded);
   expected = 2 (`route_demo_recorder.py` + `test_newton_clip_routing.py`) → 層5 n/a unless it grows to ≥3.

## §7. KNOWN_ALTERNATIVES — see §1 table (all dispositioned on-disk; NHA adjudicated CHANGE_JUSTIFIED).

## §8. L-TRIAGE (Stage 1) v2 — final_L = **L2**, with corrected mechanics

- Qualitative L2 trigger: NEW FILE. Quantitative guard: **≤200-line diff hard-target; >200 → auto-promote L3**
  (§6.5) — v1's "200-300 LOC → L2 band" was arithmetic-false vs the §0 table (L2 ≤200行).
- Keyword hits (`phase`/`ik`/`newton` in diff) auto-promote to L3 **by default**; CC files a false-positive
  demotion **RECOMMENDATION** (grounds: read-only references, no control/phase/physics LOGIC change; precedents
  log:6755 M-Route-2 "ik"-token demotion %9-verified + P1 probe L1). **Ratification = Rs spec-approval; %9
  verifies the demotion grounds in its cross-PV** (fixes v1's inverted demote-by-default direction).
- L2 gates: DoD ✓(§6) / pre-mortem ✓(§5) / 5体 pre-debate ✓(DONE — this v2 IS its output) / rule-check stage2 =
  COORD pre-edit / 層3 = COORD post-build / 層2 post-debate = n/a (L3-only, unless promoted) / 層5 = n/a at 2
  code files (§6.7) / DESIGN-GATE = skip-justified (no reward/env/success change; the `regrasp_ok` validity gate
  reuses the committed run's existing Rs-locked verdict `test:4447` unmodified) / handoff = not required (§運用25).
