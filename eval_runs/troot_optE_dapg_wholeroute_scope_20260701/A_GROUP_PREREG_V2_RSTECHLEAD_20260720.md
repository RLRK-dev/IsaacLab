# A-group PHYSICS_REWRITE — prereg **v2** (p4, 2026-07-20 10:4x JST)

Supersedes v1 (banked c28 `adf486bb0d`, blob `976d6a935729`). Written to clear pN blockers **B1-B4**
(10:39). B5 = charter records, returned to p5 (its author, live-editing) — banked when it lands.
Design authority: charter §14.24 + §14.24-a + §14.23-b (banked c25 `e1e24617c3` / c27 `bfc35ca87c`).
Facts: call-graph c26 (blob `c84c2743f51e`). **Base sha for every path/blob below: c28
`adf486bb0df4ffd12b83cda5aff78ad7c38236a4`** (tree clean at measurement).
⛔ **No source edit under this document until pN re-readback OPENs A [CHANGE].**

---

## B1 — exact path freeze

### B1.1 `newton_routing_utils` closure — 11 unique / 23 import nodes (all must be in the A-1 stage set)

| # | path | base blob | nodes |
|---|---|---|---|
| 1 | `thread_isaac_lab/envs/route_executor.py` | `d9e97bf5e279` | 5 |
| 2 | `thread_isaac_lab/scripts/dry_run_39step.py` | `5d34ed07295a` | 1 |
| 3 | `thread_isaac_lab/scripts/dry_run_43step.py` | `5d3a2d1437e9` | 2 |
| 4 | `thread_isaac_lab/scripts/dry_run_approach_cable.py` | `b58ccde391d9` | 1 |
| 5 | `thread_isaac_lab/scripts/run_demo_from_waypoints.py` | `1ecdd2d3188f` | 1 |
| 6 | `thread_isaac_lab/scripts/test_motion_sequence_dry_run.py` | `64e2d39a299d` | 1 |
| 7 | `thread_isaac_lab/scripts/test_newton_20clip_reachability.py` | `c7b248719a38` | 1 |
| 8 | `thread_isaac_lab/scripts/test_newton_5clip_routing.py` | `f22dc903fc2b` | 1 |
| 9 | `thread_isaac_lab/scripts/test_newton_clip_routing.py` | `3d6c979e2e6f` | 5 |
| 10 | `thread_isaac_lab/scripts/test_step_table_dryrun.py` | `27bf617df597` | 1 |
| 11 | `thread_isaac_lab/skills/scripted_skills.py` | `e8faa50c30f7` | 4 |

### B1.2 `test_newton_clip_routing` closure — 10 unique / 12 import nodes

| # | path | base blob | nodes |
|---|---|---|---|
| 1 | `thread_isaac_lab/envs/newton_approach_cable_mujoco_env.py` | `72ea06adaff1` | 1 |
| 2 | `thread_isaac_lab/envs/newton_grip_env.py` | `80404b7d0c47` | 1 |
| 3 | `thread_isaac_lab/envs/newton_route_env.py` | `24e679d72aba` | 1 |
| 4 | `thread_isaac_lab/envs/newton_skill_env_base.py` | `c28656dfc1c4` | 1 |
| 5 | `thread_isaac_lab/scripts/build_mppi_scene.py` | `7295d3c77d71` | 1 |
| 6 | `thread_isaac_lab/scripts/demo_aerial_regrasp.py` | `15b0fa0eb3d7` | 1 |
| 7 | `thread_isaac_lab/scripts/measure_finger_extent.py` | `fc65fb0029fe` | 1 |
| 8 | `thread_isaac_lab/scripts/policy_route_runner.py` | `5e8c6285cf4e` | 2 |
| 9 | `thread_isaac_lab/scripts/test_routeexec_byte_repro.py` | `4e8b694ccb8d` | 1 |
| 10 | `thread_isaac_lab/scripts/wet_run_full_sequence.py` | `ce3dbbbdf34f` | 2 |

### B1.3 A-1 **changed path set** (exactly these; the staged set is asserted equal to this list)

| path | base blob | change |
|---|---|---|
| `thread_isaac_lab/scripts/newton_routing_utils.py` | `b6eaf1a828fe` | realization added; `update_kinematic_bodies` body deleted; `restore_state_snapshot` body deleted; `physics_step` loop drops the per-substep body copy |
| `thread_isaac_lab/skills/snapshot.py` | `4c172899ab8d` | `restore` body deleted (3 sinks) |
| `thread_isaac_lab/scripts/test_newton_clip_routing.py` | `3d6c979e2e6f` | 17 sinks → realization; harness acceptance |
| `thread_isaac_lab/scripts/test_grip_modes.py` | `bb633944a2b9` | 2 sinks → realization (PS-1 servo semantics; `skip_bodies` = finger exclusion) |
| `thread_isaac_lab/scripts/test_step_table_dryrun.py` | `27bf617df597` | B3-a adaptation |
| `thread_isaac_lab/scripts/test_newton_5clip_routing.py` | `f22dc903fc2b` | B3-b adaptation |

All six blobs measured at c28 this session (`snapshot.py` had never been pinned in a manifest row
before; it is pinned here).

**Unchanged-by-construction** (verified at execution, not edited): the remaining 9 `routing_utils`
consumers (B1.1 #2,4,5,6,7,11 + #1 `route_executor` whose `update_kinematic_bodies` is already
raise-only) and the 9 non-overlapping `clip_routing` consumers (B1.2 minus #6 aerial which is
BLOCKED_OWNER). **Acceptance asserts their blobs are byte-identical post-bundle** — that is the
"remaining 9" binding pN asked for, expressed as blob equality rather than prose.

---

## B2 — realization contract (frozen)

**Owner**: `thread_isaac_lab/scripts/newton_routing_utils.py` (the surviving shared library; **no
relocation in this bundle** — moving it would perturb the frozen 11-consumer closure).
**Qualname**: `apply_arm_joint_targets` (module-level).
**Signature**: `apply_arm_joint_targets(control, joint_target_pos_row, arm_qd_idx) -> None`.

| contract clause | value |
|---|---|
| writes | **`control.joint_target_pos`** only, via `.assign()` — the POSITION-servo surface, precedent `newton_grip_env.py:865/874` (PS-1) and `:1731/1735` |
| body / raw / eq / mocap writes | **0** (guard-asserted; a must-fire negative control proves the guard would catch a regression) |
| solver steps added by the helper | **0** — the helper never calls `solver.step` |
| single solver-step owner | **`newton_routing_utils.physics_step`** remains the sole owner (`solver.step` at the current `:941`) |
| call order | targets written **once per frame, before** `physics_step`'s substep loop; the loop then runs `clear_forces → collide → solver.step` per substep and **no longer calls any body copy** |
| target consumption | the written joint target is consumed by the existing `physics_step` **once per frame** (the servo holds across substeps); no re-write inside the loop |
| `eval_fk` | **read / instrument only** — permitted to derive body poses for measurement and IK seeding; never as a write path into physics state |
| deleted | `update_kinematic_bodies` body (all 4 copies converge here); `restore_state_snapshot` body; `snapshot.py restore` body |
| compat symbols | if retained: **F2-shape fail-closed** — warn + raise before any read/mutation, provenance comment, signature preserved, **no old body** |

---

## B3 — standalone consumer disposition (unique per path)

### B3-a `test_step_table_dryrun.py` → **ADAPT** (not retire)

Measured: its snapshot use is a **pure mechanism-validation leg** — `:207-232` are literally
"Test snapshot restore to STEP 1" and "Test restore to mid-point (STEP 20)", printing restored
bookkeeping. Its other three validations (step-table IK reachability / scripted-skill execution /
43-step coherence, per its docstring `:1-16`) are independent of the rewind.
**Contract**: delete validation leg #3 — the two restore blocks (`:210`, `:226`), the `save` call
(`:128`), the import (`:50`), and the docstring line claiming "SnapshotManager save/restore works".
**No physical reset/replay substitute is introduced**: the leg asserted a *mechanism*, not a task
outcome, and the mechanism is banned (§14.23-b(d)) — there is nothing to replay. Legs #1/#2/#4 are
untouched. **Old-restore non-reachability registered**: post-bundle, `SnapshotManager` and
`snapshot` do not appear in this file (closed query, asserted in acceptance).

### B3-b `test_newton_5clip_routing.py` → **ADAPT** (not retire)

Measured: `restore_state_snapshot` at `:350` runs under `if ep > 0:` — an **episode-boundary
re-initialisation**, not a mid-episode rewind (`save_state_snapshot` at `:320`, once, pre-loop).
This maps exactly onto the sanctioned recovery shape of §14.23-b(d) (episode reset → physical).
**Contract**: replace the pair with a sanctioned episode-boundary reset —
(1) capture at `:320` becomes a **joint-row capture** (`joint_q` / `joint_qd` only; no body, no solver
state); (2) at `:350`, `state = model.state()` followed by a **one-time joint seed** of that row +
`newton.eval_fk` (read-derivation of body poses) + `reset_physics_buffer(device)` + a **physical
settle** under the servo before the episode runs. This is the CLAUDE.md:67 authorised once-per-episode
joint seed, not a body write. **Old-restore non-reachability registered**: post-bundle,
`restore_state_snapshot` / `save_state_snapshot` do not appear in this file (closed query, asserted).

---

## B4 — acceptance (exact)

Run from the worktree root `/home/rlrk/IsaacLab/.claude/worktrees/pd1-arm-pd-probe`, tree clean,
interpreter `/home/rlrk/env_isaaclab7/bin/python`. Outbox for this bundle:
`eval_runs/troot_optE_dapg_wholeroute_scope_20260701/a1_acceptance/` (**fresh — created empty at
bundle start; provenance header records base sha, banked sha, interpreter path, and `date` at run**).

| # | leg | exact command | expected |
|---|---|---|---|
| 1 | staged-set identity | `git diff --cached --name-only` | **exactly** the 6 paths of B1.3, sorted |
| 2 | unchanged-consumer proof | `git rev-parse HEAD:<path>` for the 9+9 non-edited closure paths | blob == the B1.1/B1.2 base blob for each |
| 3 | compile | `python -m py_compile <each of the 6 changed paths>` | rc 0 |
| 4 | lint | `python -m ruff check <each changed path>` | finding count **≤** the file's **measured base-sha count** (0 new). Baselines @ c28: `newton_routing_utils` **12** · `snapshot` **0** · `test_newton_clip_routing` **94** · `test_grip_modes` **4** · `test_step_table_dryrun` **9** · `test_newton_5clip_routing` **12** (all pre-existing; this bundle does not adopt them) |
| 5 | canonical census | `bash scripts/validations/check_control_method.sh` | `LAYER8_FAIL=6`, `LAYER8_WARN=0` |
| 6 | census identity | `grep -cE '^\s+\[FAIL' <out>` | **== 6** (defeats the self-test false-pass: on self-test failure the guard prints `LAYER8_FAIL=1` with zero per-file lines) |
| 7 | per-file zero | `grep -c 'FAIL:.*<path>' <out>` for `newton_routing_utils.py`, `test_newton_clip_routing.py`, `test_grip_modes.py`, `skills/snapshot.py` | **0** each |
| 8 | residual identity | remaining FAIL lines | `demo_aerial_regrasp.py` 5 + `dry_run_43step.py` 1 = 6, no others |
| 9 | **must-fire negative control** | inject `state.body_q.assign(x)` into `apply_arm_joint_targets` in a scratch copy; rerun guard | census **rises** (RED); revert; census returns to 6. Proves the guard would catch a regression of exactly this realization (baseline RED → landed PASS) |
| 10 | closure re-run | the B1 AST closure script (banked as `a1_acceptance/closure_query.py`) | routing_utils **11/23**, clip_routing **10/12** — any drift = STOP + re-prereg |
| 11 | old-restore non-reachability | `grep -nE 'SnapshotManager\|snapshot' test_step_table_dryrun.py` and `grep -nE 'restore_state_snapshot\|save_state_snapshot' test_newton_5clip_routing.py` | **0 hits each** (B3 registration) |
| 12 | rewind-symbol absence | `grep -rn 'update_kinematic_bodies' --include=*.py thread_isaac_lab/` | only fail-closed compat entries, **no live body copy** |
| 13 | target tests | ⚠ **there is no pytest root for these scripts** — `thread_isaac_lab/tests` does not exist at c28 (measured; the WMSO suite `thread_isaac_lab/wmso/d1/tests` is unrelated and untouched). The changed files are standalone scripts requiring a GPU/Newton session, so executing them is a **RUN leg = HALT-fenced**. Substitute static legs: `python -c "import ast,sys; [ast.parse(open(p).read()) for p in PATHS]"` (parse) + legs #3/#9/#11/#12. **No test-execution claim is made in this bundle** |

⚠ **Not in this bundle**: harness acceptance duty **(iv)** (re-acquiring kinematic-era PASSes) is a
**RUN leg** — CLOSED under HALT; it needs the separate run prereg pN specified (10:39 §3). Legs (i)-(iii)
of §14.24(3) are static and are covered by #9/#10/#7 above plus the instrument-identity review in the
two-key.

---

## B-carry / scope

- **A-2** (`dry_run_43step`, typed OFFLINE-REPLAY, 1 FAIL) = **CLOSED** pending the pN-owned
  `OFFLINE_REPLAY_MANIFEST` guard mechanism (conditional-adopt, 10:39 §2). p4 does not touch the guard.
  ⇒ **A-1 alone takes the census 35 → 6**, not 5.
- `demo_aerial_regrasp.py` 5 = D BLOCKED_OWNER, untouched. **Floor after A-1 = 6; after A-2 = 5.**
  ⛔ No global Layer8-clean claim at any point in this prereg.
- Sequencing: **A-first** (pN C2); post-land, source-closure-dependent B0/B1 artifacts →
  HISTORICAL / NOT_COMPARABLE → fresh re-acquisition → #18 on the compliant substrate.
