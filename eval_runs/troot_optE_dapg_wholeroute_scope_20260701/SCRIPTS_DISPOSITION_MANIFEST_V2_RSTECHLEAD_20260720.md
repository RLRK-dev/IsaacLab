# SCRIPTS DISPOSITION MANIFEST v2 (p4 / RS-TECH-LEAD, 2026-07-20)

**v2.3 records-fix (2026-07-20 10:0x JST)** — pN c23 readback R1-R2 folded (chain itself =
MECHANISM/EVIDENCE PASS): R1 = four stale "not executed / pending" sentences corrected to
EXECUTED-c20/c21/c22 or explicitly HISTORICAL · R2 = §1 A/E coupling note demoted to HISTORICAL
(pre-c22) and the **A-prereg closure frozen @ c23**: `newton_routing_utils` 11 unique consumers
(23 import nodes) unchanged / `test_newton_clip_routing` **10 unique surviving (12 import nodes)**
(pre-c22 "18" = historical) — both p4-re-derived by AST, exact match with pN. ⛔ A source [CHANGE]
stays CLOSED until this records-fix banks + pN readback AND the p5 design pin readback.
**v2.2 execution record (2026-07-20 09:5x JST)** — steps 0-4 EXECUTED under pN GO 09:43 (revised
order); see §6/§7. Canonical bar now **35** = A 27 + D 5 + snapshot 3.
**v2.1 disposition fold (2026-07-20 09:3x JST)** — pN court verdict 09:24 folded: §3 E = **ADOPT**
(gen4 DELETE + consumer5 RETIRE, one atomic bundle) · §4 = **DELETE** both · §5 = **RETAIN +
records-only docstring correction** · §1 `newton_routing_utils` = classification **env-class**
(placement), action unchanged PHYSICS_REWRITE. v2.0 as-read sha256 =
`499b21b0e2dfa13ca6e8810d70f09fc94a63ca3a09fcd7217b0da0b9004828bc`; v2.1 banked blob =
`ec0e5211975c` (c18). Canonical guard note added to §0.

Supersedes manifest v1 (`ARM_CONTROL_REMOVAL_SOURCE_REVIEW_RSTECHLEAD_20260719.md` §14, as-read
sha256 `10d1bad3a0511f4d744a636c7106cd9bde584820f4ae711c3923cb70e31ed403`).
⚠ **records-fix**: the p4 handoff pinned manifest v1 as `222e5d58a52a`. That string matches neither the
file's sha256, nor its git blob (`91c1b306052d…`), nor the §14-section sha256 (`f1d41aef2350…`), and
appears nowhere under `eval_runs/`. File mtime (2026-07-19 19:00) predates the 03:42 dispatch, so the
content never moved. `222e5d58a52a` = **bad pin, withdrawn**; the sha256 above governs. (Consistent with
`00-DESIGN-STATUS-LEDGER.md:109`, which pins the same doc as `10d1bad3a051`.)

**Authority**: pN B-drive court ruling ① (2026-07-20 08:04) = CONDITIONAL ADOPT, within Rs option B.
**Measurement surface**: worktree `/home/rlrk/IsaacLab/.claude/worktrees/pd1-arm-pd-probe`, branch
`probe/pd1-arm-pd`, **at banked commit `3117bbd21cd7fad7e790d9d2ab50180817d06448` (c17/F2), tree clean**.
All blob SHAs below are `git hash-object` of the file at that commit.
**Guard bar at that commit**: `LAYER8_FAIL=125`, `LAYER8_WARN=0`; envs **0**, scripts **125**
(pre-F3 restricted-scope guard — the bar the 08:04 ruling was phrased against).
**Canonical (F3-expanded) guard** (pN bank `7803f58f17`, blob `f498f888f18c…`, all-`thread_isaac_lab`
recursive): c17-equivalent `LAYER8_FAIL=128` = **scripts 125 + `skills/snapshot.py` 3**. The scripts
bucket is byte-identical between the two guards, so this manifest's 125/125 coverage arithmetic is
unchanged; `snapshot.py` 3 = **separate owner gate (HOLD), deliberately not a row here**.
**Execution state (v2.3)**: steps 0-4 **EXECUTED** c19-c22 (§6/§7); A = pending (p5 design pin +
records readback gate); D = blocked. 〔The v2.0-v2.1 sentence "Nothing in this manifest has been
executed" is **HISTORICAL** — true when written, superseded by §7.〕

---

## §0 Method (how the closure was computed, so it can be re-derived)

`scratchpad/build_manifest_v2.py` — for every candidate: exact path; `git hash-object` blob; guard FAIL
count parsed from the guard's own per-file `[FAIL:…]` lines at the banked sha; and a **direct-import
closure computed from AST `Import`/`ImportFrom` nodes over every `.py` under `thread_isaac_lab/`** —
deliberately separated from mere **text mentions**. That separation is what settles pN's correction
(§5 below): a filename appearing in another file's text is not an import edge.

**Coverage arithmetic (this is the check that manifest v1 lacked):**
`123` FAILs across the 29 rows pN named, `+2` across two files pN's ruling did **not** name
(§4) `= 125` = the entire scripts bucket. Without §4, dispositioning every row pN listed still leaves
Layer8 at 2, not 0.

---

## §1 Group A — PHYSICS_REWRITE (4 rows, pN ①A)

Body/mocap/eq solver-state writes → actuator / physical contact. Sanctioned reset seed and offline
joint-state replay keep their existing exemptions (`CLAUDE.md:67`, charter §14.16-R).

| path | blob | trk | guard FAILs | direct-import consumers | acceptance leg |
|---|---|---|---|---|---|
| `thread_isaac_lab/scripts/dry_run_43step.py` | `5d3a2d1437e9` | ✓ | 1 (`set_jq`) | **0** | rewrite → guard 1→0; 43-step table output byte-compared pre/post |
| `thread_isaac_lab/scripts/newton_routing_utils.py` | `b6eaf1a828fe` | ✓ | 7 (`restore_state_snapshot`, `update_kinematic_bodies`) | **11** | ⚠ highest blast radius — see note | 
| `thread_isaac_lab/scripts/test_newton_clip_routing.py` | `3d6c979e2e6f` | ✓ | 17 | **18** | rewrite → guard 17→0; Fingertip Z-Check gate still fires (positive control) |
| `thread_isaac_lab/scripts/test_grip_modes.py` | `bb633944a2b9` | ✓ | 2 (`update_kinematic_bodies`) | **0** | align to PS-1 servo; guard 2→0 |

⚠ **`newton_routing_utils.py` is library code misfiled under `scripts/`.** Its 11 importers include
`thread_isaac_lab/envs/route_executor.py` and `thread_isaac_lab/skills/scripted_skills.py`. Its
`restore_state_snapshot` writes `state.body_q/body_qd/joint_q/joint_qd` and `solver.body_q_prev` —
**the same operation set F2 just removed from `envs/`** — but it counts in the *scripts* bucket, so
"envs 0" was never disturbed by it.
**pN 09:24 ruling (adopted)**: classification = **env-class by placement only**; action stays
**PHYSICS_REWRITE**; the 11-consumer closure means **no solo land** — it moves with its consumers.

⚠ `test_newton_clip_routing.py` is the CLAUDE.md-sanctioned scripted verification harness.
〔**HISTORICAL (pre-c22)**: it was imported by all 4 MPPI generators and 3 of the 5 MPPI consumers, so
the A rewrite and the E bundle were then coupled. The E bundle was deleted in c22 — the coupling is
dissolved.〕 **A-prereg frozen closure @ c23 `07324776ac`** (p4 AST re-derivation, exact match with pN):
`test_newton_clip_routing` = **10 unique surviving consumers (12 import nodes)** — 4 envs
(approach/grip/route/skill_env_base) + 6 scripts (build_mppi_scene, demo_aerial_regrasp,
measure_finger_extent, policy_route_runner, test_routeexec_byte_repro, wet_run_full_sequence);
`newton_routing_utils` = **11 unique consumers (23 import nodes), unchanged** (the §1 table's "18" for
clip_routing is the pre-c22 historical value).

## §2 Groups B / C / D — DELETE and BLOCKED_OWNER (15 rows, pN ①B/①C/①D)

git blob SHA = the evidence per pN; no entry-raise dead body is left behind.

| group | path (`thread_isaac_lab/scripts/…`) | blob | FAILs | consumers |
|---|---|---|---|---|
| B | `build_unclamp_precondition.py` | `6062bf9555ea` | 8 | 0 |
| B | `diag_heuristic_dist.py` | `dbb004946201` | 1 (UNPARSEABLE) | 0 |
| B | `diag_particle_q_layout.py` | `0ef8a4b31249` | 3 | **0** (see §5) |
| B10 | `test_newton_vbd_multiworld.py` | `d0aa51b9208f` | 7 | 0 |
| B10 | `test_newton_fem_cable.py` | `8e4f01ed1556` | 3 | 0 |
| B10 | `test_newton_cable.py` | `138018f0cdd1` | 1 | 0 |
| B10 | `test_newton_cable_video.py` | `28643b2511c3` | 4 | 0 |
| B10 | `test_newton_phase4_gravity_collision.py` | `e814138ddee6` | 3 | 0 |
| B10 | `test_newton_phase5_combined.py` | `a8c7c59baf4e` | 2 | 0 |
| B10 | `test_newton_phase5_grip_tuning.py` | `dfac349e67bf` | 2 | 0 |
| B10 | `test_newton_phase7_franka.py` | `ca4360dc5762` | 2 | 0 |
| B10 | `test_newton_ur10e.py` | `5b665619a6a2` | 2 | 0 |
| B10 | `test_newton_clip_routing_sdf_plain.py` | `5136e02477ed` | 2 | 0 |
| C | `test_newton_dual_clip_routing.py` | `73b8cb6456fb` | 7 | **0** — standalone, imported by nobody, Franka legacy duplicate ⇒ DELETE (pN ①C resolves v1's REVIEW) |
| D | `demo_aerial_regrasp.py` | `15b0fa0eb3d7` | 5 | 0 | **BLOCKED_OWNER — not touched.** Owner unknown; aerial excluded per pN ①D |

All B/C rows: tracked ✓, direct-import consumers **0** (AST closure), guard FAILs → 0 on delete.
B subtotal 12 · +B10 = 40 FAILs · C = 7 · D = 5 (**remains open**, by ruling).

## §3 Group E — MPPI atomic bundle (9 rows, pN ①E)

pN's condition: the 5 direct-import consumers get their own rows with RETIRE / PHYSICS_REWRITE decided
per row, in **one atomic bundle** with the generators. Standalone generator DELETE is not permitted.

**Generators** (all tracked; all import `test_newton_clip_routing.py` = an §1 A-row):

| path | blob | FAILs | imported by |
|---|---|---|---|
| `generate_demos_mppi.py` | `25191c31e218` | 14 | `test_mppi_m1_regression.py` |
| `generate_demos_mppi_m2.py` | `de0491ef4bc4` | 14 | `generate_demos_mppi_m3.py`, `generate_demos_mppi_m3_ar.py`, `smoke_test_m3_ik_rotation.py`, `test_mppi_m2_regression.py` |
| `generate_demos_mppi_m3.py` | `31bd25d97df0` | 7 | `generate_demos_mppi_m3_ar.py`, `test_mppi_m3_regression.py` |
| `generate_demos_mppi_m3_ar.py` | `c0dc66af122b` | 9 | `test_m3_ar_handoff.py` |

**Consumers** (all tracked; **all have guard FAILs = 0** — they are not Layer8 items, they are breakage
risk):

| path | blob | imports from this set | proposed action |
|---|---|---|---|
| `test_mppi_m1_regression.py` | `0317af4d4e9a` | `generate_demos_mppi` | **RETIRE** (its only subject is deleted) |
| `test_mppi_m2_regression.py` | `60086015259d` | `generate_demos_mppi_m2`, `test_newton_clip_routing` | **RETIRE** |
| `test_mppi_m3_regression.py` | `48bd22f5b53a` | `generate_demos_mppi_m3`, `test_newton_clip_routing` | **RETIRE** |
| `test_m3_ar_handoff.py` | `be1526944950` | `generate_demos_mppi_m3_ar` | **RETIRE** |
| `smoke_test_m3_ik_rotation.py` | `68b071b2d54b` | `generate_demos_mppi_m2`, `test_newton_clip_routing` | **RETIRE** |

**pN 09:24 ruling = ADOPT (supersedes the escalation below).** Generator 4 = DELETE + consumer 5 =
**RETIRE**, all nine in **one atomic bundle** (single commit; blob SHAs above are the bundle pin).
pN rationale, verified where checkable: every consumer's *subject* is a deleted generator with no
external direct consumer (my §0 AST closure shows all `imported_by` edges are intra-bundle — consistent);
`smoke_test_m3_ik_rotation` is a temporary duplicate — `IKObjectiveRotation` is implemented in the
current env/route surface (**verified**: `newton_route_env.py:76,960,1070,1076`,
`newton_skill_env_base.py:25,1207` at c17). Demo re-recording remains the W-b programme.
(Original p4 escalation, retained for the record: RETIRE-all-5 recommended; demo-strategy ownership
made it pN/Rs's call — now decided.) Bundle subtotal: 44 FAILs (generators) + 0 (consumers).
**Execution: EXECUTED c22 `873c255ddb` (single atomic bundle; §7).**

## §4 ⚠ NOT IN pN's RULING — 2 rows required for Layer8 = 0 (p4 addition)

Both are tracked, both carry a live guard FAIL, and **neither appears in manifest v1 or in pN's 08:04
ruling**. Without a disposition, the scripts bucket floors at 2, not 0.

| path | blob | FAILs | site | consumers |
|---|---|---|---|---|
| `thread_isaac_lab/scripts/test_cradle_lift.py` | `c5cbda9bbcbd` | 1 | `:124 ATTR-STORE .body_q = …` in `set_platform_z` | 0 |
| `thread_isaac_lab/scripts/test_l_finger_cable_lift.py` | `c06e0ea10312` | 1 | `:268 ATTR-STORE .body_q = …` in `set_finger_positions` | 0 |

Both write body state to place a fixture (platform height / finger positions).
**pN 09:24 ruling = DELETE both (adopted)**: each test's *purpose itself* is moving kinematic bodies by
`body_q` substitution, and with consumer 0 a rewrite would be a new test design, not preservation of
this one. git blob SHA = evidence, same as group B. **Execution: EXECUTED c21 `2ada23b6ab` (§7).**

## §5 pN's correction — mechanically confirmed, and manifest v1's claim withdrawn

pN: *"`test_newton_phase5_ground_collision.py` is not an import consumer of `diag_particle_q_layout.py`,
only a documentation reference."* **Confirmed by AST closure at the banked sha:**
- `diag_particle_q_layout.py` → `imported_by = []` (no import edge anywhere in `thread_isaac_lab/`).
- Its only cross-reference from `test_newton_phase5_ground_collision.py` is **text-only**.
⇒ manifest v1's cell "consumers: 1 (`test_newton_phase5_ground_collision`)" and its instruction
"**DELETE** (with its consumer)" are **WITHDRAWN**. Deleting that consumer implicitly would have
destroyed an unrelated file on a false edge.

**Independent row** (per pN):

| path | blob | FAILs | disposition |
|---|---|---|---|
| `thread_isaac_lab/scripts/test_newton_phase5_ground_collision.py` | `659cac050e50` | **0** | **pN 09:24 = RETAIN + records-only docstring correction (adopted)**: replace the stale current-dependency wording on `diag_particle_q_layout` with a reference to its historical evidence blob `0ef8a4b31249` (its §2 row blob at c17); solver behaviour and test body untouched. **Execution: EXECUTED c20 `56bca10f48`, atomic with B/C per pN step-1 (§7).** |

## §6 Execution status (v2.2) — steps 0-4 EXECUTED under pN GO (09:43); A pending

| group | rows | disposition (pN 08:04 + 09:24) | execution |
|---|---|---|---|
| A PHYSICS_REWRITE | 4 | adopted; `newton_routing_utils` = env-class by placement, action unchanged, **atomic with 11-consumer adaptation + tests, no solo land**; `test_newton_clip_routing` needs surviving positive-control acceptance (pN 09:43) | **pending — next chunk** (p5 physics-replacement semantics consult per §14.14) |
| B/C DELETE | 14 | adopted; closure verified 0 consumers | **EXECUTED c20** |
| D BLOCKED_OWNER | 1 | **stands — not touched** (aerial excluded) | — (5 FAILs carry) |
| E MPPI bundle | 9 | ADOPTED: gen4 DELETE + consumer5 RETIRE, one atomic commit | **EXECUTED c22** |
| §4 additions | 2 | DELETE | **EXECUTED c21** |
| §5 correction | 1 | RETAIN + records-only docstring fix | **EXECUTED c20** (atomic with B/C per pN step-1) |
| **total** | **31** | covers 125/125 scripts FAILs | 26 executed / 4 pending (A) / 1 blocked (D) |

## §7 EXECUTION RECORD (steps 0-4, 2026-07-20 09:4x-09:5x JST, branch `probe/pd1-arm-pd`)

Authority: pN execution GO 09:43 (Rs option B / isolated worktree / adjudicated rows only), revised
order followed exactly. Every bank: clean tree at commit, canonical guard rerun at the banked sha,
**exact expected decrement**, FAIL-line-count == `LAYER8_FAIL` identity, import-closure closed query
(no survivor imports a deleted stem), `py_compile`+`ruff` on the one edited file (7 findings pre-edit ==
7 post-edit ⇒ 0 new). Pre-delete git blob SHAs recorded in each commit message + §1-§5 tables.

| step | commit | content | canonical `LAYER8_FAIL` | buckets (envs/scripts/skills) |
|---|---|---|---|---|
| 0 | c19 `78431144f0` | cherry-pick pN F3 guard `7803f58f17` (guard blob **`f498f888f18c`** exact) | **128** baseline fixed | 0 / 125 / 3 |
| 1+2 | c20 `56bca10f48` | B/C DELETE 14 + §5 ground-collision docstring fix (atomic — no stale-reference intermediate state) | 128 → **81** | 0 / 78 / 3 |
| 3 | c21 `2ada23b6ab` | §4 DELETE 2 | 81 → **79** | 0 / 76 / 3 |
| 4 | c22 `873c255ddb` | E bundle: gen4 DELETE + consumer5 RETIRE (single atomic commit) | 79 → **35** | 0 / 32 / 3 |

Residual 35 = **A group 27** (`test_newton_clip_routing` 17 + `newton_routing_utils` 7 +
`test_grip_modes` 2 + `dry_run_43step` 1) + **D aerial 5** (BLOCKED_OWNER) + **`skills/snapshot.py` 3**
(separate owner gate). After A completes: floor = **8** (D 5 + snapshot 3) — **Layer8 = 0 is not
reached by this manifest alone**, per pN 09:43. Full hooks + two-key precede any promotion/landing;
main-tree, push, and training remain CLOSED.

Per-row acceptance leg (uniform): execute → rerun `check_control_method.sh` **at the banked post-change
sha on a clean tree** → assert (a) that file's per-file FAIL count is 0, (b) `LAYER8_FAIL` drops by
exactly that file's prior count, (c) total `[FAIL` lines == `LAYER8_FAIL` (defeats the self-test
false-pass: on self-test failure the guard prints `LAYER8_FAIL=1` with **zero** per-file lines, so a
naive per-file grep returns 0 and falsely passes) → `py_compile` + `ruff check` → two-key.
