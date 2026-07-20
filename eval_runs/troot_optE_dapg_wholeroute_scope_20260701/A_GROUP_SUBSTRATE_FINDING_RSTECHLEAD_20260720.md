# ⛔ A-group substrate finding — the PHYSICS_REWRITE premise does not hold on the VBD branch

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

Digging one level further shows the cause is not missing wiring but the substrate:

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

## 2. This is the already-banked substrate wall, not a new problem

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

⇒ The A-group is **not one class**. The mujoco-branch sites are plausibly PS-1-style rewritable; the
VBD-branch sites are on the walled substrate.

## 5. What I am asking for (no design authored here)

- **p5 (design)**: §14.24(0)'s "principle transfers, grip PS-1 precedent holds" is measured false for
  the VBD branch. Does the A-group split into (a) mujoco-branch → PHYSICS_REWRITE per PS-1 and
  (b) VBD-branch → DISCARDED-track disposition (the env6-VBD track is already DISCARDED per
  `CLAUDE.md`, Rs 2026-06-26), rather than a uniform rewrite?
- **pN (scope)**: if the VBD-branch sites are DISCARDED-track, their disposition class changes from
  PHYSICS_REWRITE to DELETE/retire — which moves rows in manifest v2.3 §1 and changes the expected
  census arithmetic. Manifest and prereg both need re-issue after the ruling.
- **The one open measurement** (§2 caveat): whether `SolverVBD` rejects a REVOLUTE arm articulation
  (making it a hard wall) or the jointless build was a choice. I can run this as a static/API check —
  it is cheap and needs no GPU run. **Requesting authorisation to measure it**; I have not.

## 6. Status of my own artifacts

Prereg **v2 §B2 is now known-defective** on this point: its realization contract presumes an actuator
surface that the VBD build does not have. It stands as the record of the B1/B3/B4 work; **§B2 must not
be implemented as written**. ⛔ A [CHANGE] remains CLOSED — correctly so; had it been opened, the
bundle would have produced a green census (35→6) with arms that no longer move, which is precisely the
"a gate validated under the bug" / "appearance-only ≠ working" failure class.
