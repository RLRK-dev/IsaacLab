# ⛔ A-group substrate finding — the PS-1 rewrite premise does not hold on the VBD branch

> ## ⚠ v1.1 NARROW CORRECTION (2026-07-20 11:1x JST) — read this before §2
> pN ran a **source-only capability check** (11:12) and refuted part of my reasoning. Corrections:
> 1. **"VBD supports none" is NOT a solver-capability fact.** It is a *repo build comment*
>    (`test_newton_clip_routing.py:771`). Measured by pN on the installed package: current env7 =
>    Newton **1.2.1**, `newton/_src/solvers/vbd/solver_vbd.py` (sha256 `f11cb9dabe44…`) doc `:105-121`
>    lists supported joint types **including REVOLUTE / PRISMATIC / D6 / CABLE**, with `target_ke/kd`
>    drives supported. ⇒ **VBD does not hard-reject REVOLUTE. The jointless scene is a build choice.**
> 2. **My §2 S1B citation over-blocked.** Re-running the prior-art guard with better keywords
>    (`"S1B" "do not re-attempt"`) returns the blocker — and its own text says:
>    "⚠ Scoped 復活禁止 … **NOT a blanket ban**: closed/blocked **on the env6 Newton substrate** …
>    (a) VBD-prismatic retry … **⚠ Scope limit (do NOT over-block): … Only the *faithful-prismatic
>    Newton rebuild* is walled**" (`07-Design/S1B-Faithful-Finger-Design.md:25`). The A-group is on
>    **env7 / Newton 1.2.1**, and the ask is a REVOLUTE arm, not a prismatic finger. **I retract
>    "same shape as the closed S1B attempt" and "substrate-walled".**
> 3. **The measurement I requested in §5 is withdrawn** — pN ruled it NO-GO/unnecessary: the installed
>    source already answers it. No constructor/finalize/step probe.
>
> **What survives unchanged** (all independently measured, §1): the zeroed inverse mass, the absent
> actuator wiring, the currently jointless scene, and therefore **prereg v2 §B2 = DO-NOT-IMPLEMENT**.
> pN concurs on the operative point for an independent reason: **VBD does not support
> `joint_target_mode`** (nor armature/friction/effort/velocity limit, equality, mimic) ⇒ **the PS-1
> POSITION-servo form cannot transfer**. The correct statement of this finding is
> **"the current scene is jointless (a build choice) and the PS-1 transfer is invalid"** — *not*
> "VBD rejects joints". The faithful-Robotiq equality/mimic wall does remain.
>
> ⭐ **Process lesson (mine)**: my first prior-art run used keywords
> (`"VBD kinematic bodies" "physics rewrite arm actuator" "S1B prismatic substrate"`) that returned
> **0 hits**, and I treated that PASS as clearance. A guard PASS is an **absence claim**, and an
> absence claim from a query that cannot hit the target proves nothing. Re-running with the banked
> document's own vocabulary found it immediately.

**p4 / RS-TECH-LEAD, 2026-07-20 11:0x JST. Raised while clearing pN R2 (11:01).**
Measured at c29 `6970bbd22c` (clean worktree, committed blobs). **This is a STOP-and-report, not a
design change**: it contradicts a premise of charter §14.24 and of my own prereg v1/v2, so I am not
writing a prereg v3 until p5 (design) and pN (scope) rule.

## 1. What pN found, and what it turned out to be

pN R2 (correct, and I confirmed it independently): `apply_arm_joint_targets` writing
`control.joint_target_pos` cannot drive the arms, because the builder never wires actuators and zeroes
the robot bodies' inverse mass. Verified on-disk:

- `thread_isaac_lab/scripts/newton_routing_utils.py:875-881` — for every robot body,
  `inv_mass[bi] = 0.0` and `inv_inertia[bi] = zeros(3)`, then both arrays are re-uploaded.
  **Zero inverse mass = infinite mass: no force can move these bodies, by construction.**
- Closed query over the same file for `joint_target_mode|joint_target_ke|joint_target_kd|joint_effort_limit|arm_qd_idx`
  = **0 hits**. No actuator wiring exists.

Digging one level further shows the cause is not missing wiring but **what the current build
constructs** — ⚠ the original wording here said "the substrate", which v1.1 ② retracted. The build
comments quoted next state the *build's* contract, **not** VBD's capability:

- `test_newton_clip_routing.py:11` — "Robot = kinematic bodies (positions from FK model).
  **No REVOLUTE/PRISMATIC joints in physics model.**"
- `:771-773` — "Add one UR5e+Robotiq arm as **kinematic bodies** … Creates BODIES_PER_ARM (14)
  kinematic bodies (**no joints — VBD supports none**)"
- `:1274` — "Robot arms: **VBD = jointless kinematic bodies** (FK body_q); **MuJoCo = articulated**
  UR5e+Robotiq."
- `newton_routing_utils.py:35` — `from newton.solvers import SolverVBD`; its `physics_step` steps
  `SolverVBD`.

⇒ **On the VBD branch there are no arm joints in the physics model at all.** There is no
`joint_target_pos` for an arm to write, and the bodies cannot respond to force. A "physics rewrite to
actuators" is not under-specified there — it is **undefined**.

## 2. ⛔ SUPERSEDED IN FULL (v1.1 ②) — retained only as the record of a retracted argument

> **Everything from here to the end of §2 is WITHDRAWN. Do not cite it as current state.**
> The S1B wall is scoped to a **faithful PRISMATIC finger on the env6 substrate**, and that document
> explicitly warns against a blanket reading. The A-group runs on **env7 / Newton 1.2.1**, and the ask
> is a REVOLUTE arm. The claims below — "same shape as the closed S1B attempt", "substrate-walled",
> and the open-measurement request — are all retracted. **Current state = header v1.1 + §5.**

### 2-HISTORICAL (withdrawn argument, verbatim)

`00-DESIGN-STATUS-LEDGER.md:112-121` (§FAILED #1, verbatim): S1B faithful prismatic-finger Newton
rebuild — "env6 Newton has **no single solver** that hosts both a PRISMATIC finger joint and the
existing CABLE-jointed `add_rod` cable (CABLE = VBD-only; VBD rejects PRISMATIC; Kamino/Featherstone
reject CABLE)… **Do not re-attempt**: VBD-prismatic retry … or rebuilding the faithful finger on this
substrate — all are closed/blocked."

The A-group ask (articulated, force-driven arms **in the same model as the VBD cable**) is the same
shape as the closed S1B attempt. Specifying builder wiring for it would be re-attempting a
human-abandoned, substrate-walled path.

⚠ Honest scope of the citation: S1B's banked wall is about a **PRISMATIC finger** joint. I did not
re-measure whether VBD rejects **REVOLUTE arm** joints specifically; `test_newton_clip_routing.py:771`
states "no joints — VBD supports none" as the build's own contract, and `newton_routing_utils` wires
none. Whether that is a VBD hard rejection or a build choice is **the one open measurement** (§4).

## 3. Why grip PS-1 is not a transferable precedent here

Charter §14.24(0) grounds the A-group rewrite on "the mechanism is identical to grip PS-1". Measured:
grip PS-1 succeeded on **env7-mujoco** — an *articulated* UR5e where `joint_target_pos` exists
(`newton_grip_env.py:865/874`). The A-group's `newton_routing_utils` runs **SolverVBD** with jointless
kinematic bodies. Same operation name, **different substrate** — the precedent does not carry.
(This is the "same constant ≠ same measurement surface" failure applied to substrates.)

## 4. Branch split of the 27 A-group FAILs (measured at c22/c29)

`test_newton_clip_routing.py` is dual-backend (it imports `SolverMuJoCo` at `:46` and rebuilds the
cable as a REVOLUTE chain for the mujoco path at `:937+`). Its 17 FAILs split by function:

| function | FAILs | branch |
|---|---|---|
| `physics_step` | 6 | VBD |
| `main` | 5 | VBD |
| `_run_mujoco_cable_settle_smoke` | 4 | **mujoco** |
| `update_kinematic_bodies` | 2 | VBD |

Plus `newton_routing_utils` 7 (VBD), `test_grip_modes` 2, `dry_run_43step` 1 (A-2, typed OFFLINE).

⇒ The A-group is **not one class**. Current statement (v1.1): the mujoco-branch sites are
PHYSICS_REWRITE *candidates*; the VBD-branch writer sites require **KINEMATIC DELETE**, while their
consumer/function disposition is **SUBSTRATE-BLOCKED pending Rs** — the p5 class ruling is done and
**banked c33** `eab548a988` (§14.24-c); what remains is the Rs decision of §8 (retire vs env7-MuJoCo
migrate).
⚠ The original wording here — "on the walled substrate" — is **retracted** (v1.1 ②).

## 5. What I am asking for (no design authored here) — **updated by v1.1 + pN scope ruling 11:12**

- **p5 (design)**: §14.24(0)'s "principle transfers, grip PS-1 precedent holds" is **measured false**
  for the VBD branch — not because VBD refuses joints, but because the scene is jointless and VBD
  lacks `joint_target_mode`. Class question stands: how does the A-group split?
- **pN (scope) — RULED 11:12, recorded**: a blanket "VBD sites → DISCARDED-track DELETE" is
  **HOLD / NOT APPROVED** (`routing_utils` has active B0/B1 consumers so it cannot be called
  DISCARDED at file/row granularity; `clip_routing` is mixed-backend). **Interim classes**:
  MuJoCo-only 4 = PHYSICS_REWRITE *candidate* · VBD-only writer sites = **KINEMATIC DELETE required**,
  but their consumer/function disposition is **SUBSTRATE-BLOCKED** (retire vs env7-MuJoCo migrate =
  p5/Rs ruling) · mixed definitions = branch/callsite split · `test_grip_modes` 2 = **unclassified**
  until backend/liveness is exactly pinned. ⛔ **Manifest rows and census do not move now**, and
  **a class change is not automatically an arithmetic change** (closing all 29 may still read 35→6).
- **pN recommendation (recorded, not yet a ruling)**: do not rebuild the VBD track — delete/fail-close
  the VBD kinematic writers and migrate the active B0/B1 to the articulated env7-MuJoCo path with
  fresh re-acquisition. Sequenced after the p5 class ruling → Rs scope.
- **Measurement request: WITHDRAWN** (v1.1 ③). If an empirical probe is ever judged necessary by p5,
  pN's condition is a **new Rs directive naming the Newton version delta + an L3 substrate prereg**.

## 6. Status of my own artifacts

Prereg **v2 §B2 is now known-defective** on this point: its realization contract presumes an actuator
surface that the VBD build does not have. It stands as the record of the B1/B3/B4 work; **§B2 must not
be implemented as written**. ⛔ A [CHANGE] remains CLOSED — correctly so; had it been opened, the
bundle would have produced a green census (35→6) with arms that no longer move, which is precisely the
"a gate validated under the bug" / "appearance-only ≠ working" failure class.

## 7. Current state (⚠ **SUPERSEDED 2026-07-20 ~11:56 by the Rs ruling** — see pointer)

> ⛔ **This section is no longer the current SSOT.** Rs ruled the decision package of §8 on
> 2026-07-20 ~11:56 JST (verbatim "1：a 2:承認"). **Current SSOT =
> `RS_RULING_AGROUP_SUBSTRATE_20260720.md` (banked c36 `eefad77773`, blob `b6edae469ea4`).**
> In particular the rows below that read "pending Rs" are **discharged**: the disposition is decided
> (migrate-then-retire; B0/B1 migration approved). What the table still states correctly is the
> substrate facts and the gate posture. (pN C1, 12:03.)

Below = the pre-ruling snapshot, retained as the record of what was true before Rs answered; it
supersedes earlier phrasing in §§1-6 only.

| question | current answer |
|---|---|
| Does VBD reject articulated arm joints? | **No.** Newton 1.2.1 VBD documents REVOLUTE/PRISMATIC/D6/CABLE as supported, with `target_ke/kd` drives (pN source check, `solver_vbd.py` sha256 `f11cb9dabe44…` doc `:105-121`) |
| Why can't prereg v2 §B2 be implemented? | The **current build constructs a jointless robot** (`newton_routing_utils.py:875-881` zeroes robot `inv_mass`/`inv_inertia`; no actuator wiring) **and VBD does not support `joint_target_mode`** ⇒ the PS-1 POSITION-servo form cannot transfer |
| Is this the S1B wall? | **No — retracted.** S1B is env6 + faithful PRISMATIC finger, and its own text forbids a blanket reading |
| Is a substrate probe needed? | **No** — pN NO-GO; source answered it. Any future probe needs a new Rs directive naming the Newton version delta + an L3 substrate prereg |
| A-group class | mujoco-only 4 = REWRITE candidate · VBD-only writer sites = KINEMATIC DELETE required · consumer disposition = **SUBSTRATE-BLOCKED pending Rs** (p5 class ruling **banked c33** `eab548a988`) · mixed = branch/callsite split · `test_grip_modes` 2 = unclassified pending backend/liveness pin |
| Manifest / census | **frozen** — a class change is not automatically an arithmetic change |
| Gates | A [CHANGE], A-2, RUN, landing, push, training = **all CLOSED** |

## 8. ✅ DECISION PACKAGE FOR Rs — **DECIDED / SUPERSEDED by c36; pre-ruling package retained below**

> **Rs ruled this package on 2026-07-20 ~11:56 JST** (verbatim "1：a 2:承認"): ① = option (a),
> ② = approved. **Current SSOT = `RS_RULING_AGROUP_SUBSTRATE_20260720.md` (c36 `eefad77773`).**
> Everything below is the package **as put to Rs**, kept as the record of what was asked. Its
> future-tense wording ("Rs options…", "What unblocks on a decision…") describes the *pre-ruling*
> state and must not be read as still-open. (pN N1, 12:12.)

Design axis (p5, charter §14.24-c @ c33 `eab548a988`) and evidence/scope axis (pN, 11:39, from
`git show @c33` + its own installed-source check) **independently reached the same recommendation**.
Both fence execution behind Rs. Nothing below has been executed.

**Recommendation (both axes):**
1. **Migrate the Fingertip Z-Check Gate to env7-mujoco, then retire the VBD copy** — Rs updates
   `CLAUDE.md` accordingly.
2. **Approve the B0/B1 evaluator's migration to env7-mujoco**; existing B0/B1 artifacts become
   **HISTORICAL / NOT_COMPARABLE** and fresh re-acquisition is **mandatory**.
3. **Do not retain the VBD track** — pN: retention "runs counter to complete-removal and to single-substrate";
   p5: it is reinvestment in a Rs-discarded track, re-meets the `joint_friction` gripper wall, and
   defeats the single-realization convergence §14.24(2) already ordered.

**Why this is Rs's call and not CC's:**
- `CLAUDE.md:271` names the Fingertip Z-Check Gate as a sanctioned harness. **CLAUDE.md changes are
  Rs prerogative** (三原則 #1 / `prohibited.md`), and §14.16-2 forbids removing a sanctioned gate
  without verification. CC will not execute it.
- Changing the substrate of an **active evaluator** invalidates banked B0/B1 evidence; the migration
  cost and re-acquisition scope need Rs sign-off.

**Rs options on item ①**: (a) migrate the gate to env7-mujoco and retire the VBD copy *(both axes'
recommendation)* · (b) approve the retire and update `CLAUDE.md` · (c) hold the VBD branch for now.

**What unblocks on a decision**: the A-group class closes → manifest v2.x rows and census arithmetic
can move → prereg is re-issued against the ruled class → implementation may then be gated normally.
**Until then**: A [CHANGE], A-2, RUN, landing, push, training all remain **CLOSED**, and prereg v2
§B2 remains **DO-NOT-IMPLEMENT**.
