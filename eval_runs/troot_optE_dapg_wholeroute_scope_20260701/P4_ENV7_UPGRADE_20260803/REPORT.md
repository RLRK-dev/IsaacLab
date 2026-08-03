# env7 upgraded to the current upstream releases — 2026-08-03

**Instruction** Rs, this session, in two steps: first *resolve* the version discrepancy between the
record and the environment; then, when told the record was not the thing to change, **"venv 自体を
upstream の最新へ上げる"**.

**Executed by** `w2:p4`. **Venv** `/home/rlrk/env_isaaclab7`. **Precedent + method** =
`P5_ENV7_UPGRADE_20260727/` (the 07-27 upgrade, Rs's task, executed by `w2:p5`).

---

## 1. What moved

| package | before | after | note |
|---|---|---|---|
| `mujoco` | 3.10.0 | **3.11.0** | |
| `mujoco-warp` | 3.10.0.3 | **3.11.0** | |
| `newton` | 1.4.0 | 1.4.0 | **already the latest upstream release** |
| `warp-lang` | 1.15.0 | 1.15.0 | **already the latest upstream release** |

**Nothing else moved.** `diff` of the two freezes is exactly the two lines above; package count
246 → 246. `torch==2.10.0+cu128` and `numpy==2.3.1` unchanged — the pull that was feared on 07-27
did not happen this time either.

- `pip_freeze_BEFORE.txt` (246 pkgs, sha256 `f700f94f8b56eeaa856365f29716a75fc17330d42fccce6bb7dba5a0f7d41668` (full — a truncated hash is not a pin))
- `pip_freeze_AFTER.txt` (246 pkgs)
- `install.log` — ends `Successfully installed mujoco-3.11.0 mujoco-warp-3.11.0` (`:37`).
  ⚠ **The file carries no exit code and no timestamps** — the `rc=0` and the 06:19:34–06:19:41 window
  reported earlier came from my shell, not from this artifact, and the run log's own `rc=` convention
  was not applied here. Corroboration is external: `mujoco-3.11.0.dist-info` mtime 06:19:40.
- `dryrun.txt` — the plan, taken before the install

**Rollback** (full prior state, not just the two pins):

```
/home/rlrk/env_isaaclab7/bin/python -m pip install -r <this dir>/pip_freeze_BEFORE.txt
```

## 2. The conflict lines are pre-existing, and one of them is only newly *printed*

The install printed four `isaacsim-core 6.0.0.0 requires …` conflicts. Three are the ones p5
recorded on 07-27 as **pre-existing** (*"I widened it; I did not create it"*): `mujoco`,
`mujoco-warp`, `newton[sim]`. The fourth, `filelock==3.20.0` vs `3.25.2`, is **not new either** —
`filelock` is byte-identical in BEFORE and AFTER (`3.25.2` both sides). pip prints the whole
conflict set on any install, so a line appearing in this log is not evidence that this install
caused it.

⛔ The standing caveat is unchanged: **any path importing `isaacsim` and `newton` in one process
needs checking.** ⛔ **CORRECTED 2026-08-03 07:0x — "widens, does not open" is FALSE for the newton
edge.** `newton-1.4.0.dist-info/METADATA:76-77` declares `mujoco~=3.10.0` and
`mujoco-warp~=3.10.0,>=3.10.0.2` under `extra == "sim"`. Both were SATISFIED before this upgrade and
are VIOLATED after. pip printed nothing because newton is installed as the base distribution, so the
resolver never evaluated the `sim` extra — and auditing only pip stdout treated that silence as
safety. `SolverMuJoCo` now emits a RuntimeWarning on every construction (`solver_mujoco.py:559`,
reproduced live). newton 1.4.0 IS the latest upstream release, so no newton supports mujoco 3.11:
"upgrade everything to latest" produced a mutually incompatible set. Escalated to Rs.

## 3. The dry-run again failed to predict the install

`dryrun.txt` printed **zero** conflict lines. `install.log` printed **four**. This reproduces
exactly what p5 recorded on 07-27 — *"a dry-run is not a predictor of install output"* — on a
second, independent upgrade. It is a property of `pip --dry-run`, not a one-off.

## 4. Smoke

```
newton      1.4.0
mujoco      3.11.0
warp        1.15.0
Warp 1.15.0 initialized: CUDA Toolkit 12.9, Driver 13.0
  "cuda:0" : "NVIDIA RTX PRO 4000 Blackwell" (23 GiB, sm_120, mempool enabled)
cuda_available True
```

⚠ A smoke proves the packages import and CUDA initialises. It does **not** prove the instrument
reads the same — §5.

## 5. What this does to the evidence banked on 2026-08-02

`mujoco` is the instrument for everything the UR15 lane measured yesterday: `mj_geomDistance`, the
clearance tests, the arm-to-arm path test. Replacing it replaces the thing that produced the
numbers.

⛔ **CORRECTED — the count was 31 and the denominator came from the wrong space.** The first list
asked "written on 2026-08-02" when the predicate is "measured on the old instrument". mujoco became
3.10.0 at **2026-07-27 20:05** and stopped being it at **2026-08-03 06:19**; over that window,
recursively and excluding `__pycache__`, the directory holds **189 files**, not 31 — including
`unwrap_logs/phase_histogram.txt`, the very baseline §6 compares against. `premeasured_on_3.10.0.txt`
is rebuilt on the instrument's own window:

```
find …/p4_ur15_sim_20260727 -type f ! -path '*__pycache__*' \
     -newermt '2026-07-27 20:05' ! -newermt '2026-08-03 06:19'
```

⚠ The list is by mtime, so it mixes outputs with the `.py` sources that produced them; a source
file's mtime is not a measurement date. Read it as "files touched while the instrument was 3.10.0",
not as "189 measurements".

⛔ Those numbers stay **true as measured**. They are not restated for 3.11.0, and their version
clauses are **not** rewritten — rewriting a measurement's recorded stack falsifies the record. Only
forward-looking statements about what env7 *is* were updated (`CLAUDE.md:82`, commit `3f95f27bda`).

`WHY_THE_ROUTE_NEVER_MOVED_20260802.md` carried no stack at all; a header note was added before the
upgrade so the provenance could still be stated honestly afterwards.

## 6. Instrument re-measure — done, identical (see the result subsection)

The decisive check is whether the same driver, same settings, one axis changed (mujoco 3.10.0 →
3.11.0), reproduces the recorded numbers.

**Baseline to match** (measured 2026-08-02 on 3.10.0, `WHY_THE_ROUTE_NEVER_MOVED_20260802.md` §7,
grasp centre −0.200, `UNWRAP_SOLVE=1 ARM_PATH=1`, 240 draws):

| | L | R |
|---|---|---|
| solved | 138 | 139 |
| clear | 36 | 8 |
| standing error | 0.00 mrad | 0.00 mrad |

Precedent: when p5 moved 3.8.1 → 3.10.0 on 07-27, a 15-point probe of the gripper model was
**identical** across the versions. That is evidence about *that* move, not this one.

### ⭐ Result — identical on all four quantities

Re-measured 2026-08-03 06:22–06:24 on **mujoco 3.11.0**, same driver, same settings, one axis
changed (`postupgrade_run.log`):

| | baseline 3.10.0 | **measured 3.11.0** | |
|---|---|---|---|
| L solved / collision-free | 138 / 36 | **138 / 36** | ✅ |
| R solved / collision-free | 139 / 8 | **139 / 8** | ✅ |
| L standing error | 0.00 mrad | **0.00 mrad** | ✅ |
| R standing error | 0.00 mrad | **0.00 mrad** | ✅ |

Both arms also read `touching: nothing` and no joint at a limit, as on 3.10.0.

⚠ *(superseded)* `postupgrade_run.log` was first banked with the run in flight. The run has since
finished — 06:22:51 → 06:42:15, **exit 1**, 385 lines — and the completed log is banked. The four
quantities above are unchanged by the rest of the run; they are start-pose quantities, printed
before the first step. §8 records what the rest of the run showed.

### ⛔ WITHDRAWN 2026-08-03 07:0x — this section over-claimed, and the L3 panel broke it

The sentence that stood here — *"The instrument's reading did not move. The clearance and arm-to-arm
path tests return the same candidate sets and the same standing errors"* — **is false as written.**
Raised by the numerical/measurement challenger; every point below reproduced by me before accepting.

**What actually held** (the table above is correct as far as it goes): the four quoted quantities are
identical, and independently the 44 clear-candidate joint vectors are byte-identical.

**What actually moved**, in the same two logs, lines away from the four I quoted:

| quantity | baseline 3.10.0 | 3.11.0 |
|---|---|---|
| arm-to-arm closest **pair** (`arm_pair_min` → `mj_geomDistance`) | `16 ↔ 70` | **`20 ↔ 66`** |
| cable link held after the approach | `L=cab4 / R=cab10` | **`L=cab3 / R=cab9`** (≈11 mm) |
| standing-error per-joint residual signs | — | **3 of 12 flipped** |

⇒ The arm-to-arm test **is the test the withdrawn sentence named**, and its own output changed.
The honest claim is the narrower one: **the candidate set did not move; the settled physics state
did.**

**And two of the four quantities could not have moved.** The 240 draws come from
`np.random.default_rng(seed)` (`ur15_steps_wired.py:1545`) — bit-identical across any mujoco build by
construction. The IK inner loop excludes collision by design (`:1585`, *"⛔ kinematics only, NOT
mj_forward … Nothing in this loop reads contacts"*), so `solved` is FK + Jacobian only. Only
`collision-free` exercises `mj_geomDistance`. **Four ✅ were roughly one real test**, and the query
beside it disagreed.

⚠ **The log does not record its own instrument.** `grep -c '3.11.0' postupgrade_run.log` → **0**; no
version banner at all. "Measured on 3.11.0" is inferred from mtime ordering in a shared tree — the
same defect this report flags in the 08-02 baseline at §5, repeated in its replacement. The only
in-band evidence that a different mujoco ran is incidental: the attach-warning text changed from
`impratio: parent has 1` to `parent has 1 (default)`.

⚠ **`premeasured_on_3.10.0.txt` is not closed either.** Built with `-maxdepth 1`; without it the
window holds **67** files, not 31 — including `unwrap_logs/phase_histogram.txt`, **the very baseline
compared against above**.

⚠ **Scope of what survives.** Start-pose solve at grasp centre −0.200, `START_TRIES=240`,
`UNWRAP_SOLVE=1 ARM_PATH=1`, this driver, this mounting. It does not cover the other six grasp
centres, the crown/mast sweeps, or the clamp-window probes. And "one axis changed" was wrong: the
driver also differs from the baseline revision `5dcd1d4e81` by +12 print-only lines.

## 7. ⛔ A blocker found on the way, unrelated to the upgrade

The first attempt to run the driver failed in 0 s with

```
IndentationError: unindent does not match any outer indentation level   (line 1804)
```

This is **not caused by the upgrade** — it is a parse error, reproducible with any interpreter and
no imports.

- The file was **clean** (`git status --porcelain` empty) ⇒ the *committed* state was broken.
- `5dcd1d4e81` parses; **`82e845e80c` does not**. That commit (08-02 23:56:07) is the last one to
  touch the driver, landing 2 min 39 s before the handoff commit.
- ⇒ **The driver has not parsed since 23:56 on 08-02**, and the handoff's "next task #1" command
  could not have run as handed off. This also explains the previous session's unexplained
  *"走らせたが log が出ず未取得"* — the run never started.

**Cause.** `82e845e80c` inserted its new un-gated block at indent 4 *inside* the body of
`if not quiet and _blame:`, which both ended that body early and left `if _phase:` with a 12-space
body and an 8-space sibling.

**Repair.** The new block moved below the enclosing block, `if _phase:` restored to indent 8.
Verified structurally rather than by eye: `diff` against `5dcd1d4e81` (the last version that parsed)
is **+12 / −0 / 0 changed** — pure addition, exactly the block `82e845e80c` intended.

⚠ **Lesson, in the lane's own recurring shape.** `82e845e80c`'s message says the fallback will now
*"say what rejected it"*. It never said anything, because the file it changed stopped parsing. The
commit was banked without running it — the label was read and the thing itself was never opened,
which is the one error form the 08-02 handoff names as running through the whole session.

---

## 8. What the same run also showed — the route, not the upgrade

⚠ **This section is about the route, not about mujoco 3.11.0.** It is recorded here only because
this run produced it; the route's own record is `p4_ur15_sim_20260727/`. Nothing here is attributed
to the upgrade.

The run doubles as the handoff's "next task #1" (measure where the aim solves are stuck).

### 8.1 The aim solves are stuck against the mounting, not mainly against the other arm

86 fallback lines. Rejections, after stripping each line's explanatory tail before splitting:

| rejected against | count |
|---|---|
| `g43 on R_upper_arm_link` vs **crown** | **65** |
| **the other arm** | 39 |
| `g6 on L_forearm_link` vs **stem** | 10 |
| various, on the way (forearm/pads/coupler vs stem or crown) | ~7 |

And the solves are as cramped as the handoff predicted: `NOT ONE of 1 candidates` ×52,
`NOT ONE of 2 candidates` ×80. With one or two candidates, any added test turns a cramped option
into none.

⇒ ⭐ The dominant obstacle at the aim poses is **the crown against the right upper arm**, not the
other arm. That is a different target from the one the start-pose work was aimed at.

### 8.2 ⛔ The route now advances — but STEP 2 advances THROUGH the other arm

| | STEP 2 | STEP 3 |
|---|---|---|
| L reached | **100.0%**, never held back | 30.4%, held back |
| R reached | **100.0%**, never held back | 49.7% |
| arm-to-arm at the pose | +17.5 mm | **−0.9 mm ← TOUCHING OR THROUGH** |
| arm-to-arm **along the move** | **−171.2 mm** (30 ↔ 65 at t=8.34 s) | −1.0 mm |

Negative is penetration — the driver's own marker (`<- TOUCHING OR THROUGH`) appears at −0.9 mm.

⛔ **So STEP 2's "100.0%, never held back" is a statement about the tracking gate, not about
clearance.** The gate measures whether the arm followed its command; it does not measure whether
the path was free. That much stands.

⛔ **CORRECTED — "the arms passed 171 mm through each other" was over-claimed and is withdrawn.**
The −171.2 mm is a reading, and I reported it as a fact about the arms without checking it could be
one. What is established:

- The pair is `Lg_left_coupler` ↔ `Rg_right_silicone_pad`, bounding radii 33.5 and 22.0 mm.
  **Two convex shapes cannot overlap more deeply than their bounding spheres together — 55.5 mm.**
  −171.2 mm is over three times that, so it is not a penetration depth.
- But I could not reproduce an impossible return anywhere: **0 in 143,626 distance calls across 60
  poses**, and **0 in 4,000 poses swept on that exact pair** (which never came closer than +28.7 mm).
- The geom-id mapping is read from `_steps_cell_full.xml`, written by that run via `to_xml()`. Left
  ids land on `Lg_*` bodies and right ids on `Rg_*`, so the ordering is consistent by side — but not
  proven identical to the runtime model.

⇒ **Unresolved.** The number cannot be a penetration depth and cannot be reproduced as an artifact.
The driver's own docstring anticipated exactly this: *"a path minimum that disagrees with both
endpoints is either a real transient or a broken instrument, and a bare number cannot say which."*
⛔ Until it is settled, **no conclusion about STEP 2's physical validity rests on this number** — in
either direction. STEP 3's −0.9 / −1.0 mm are *within* the bound and remain plausible as real light
contact.

**Discriminator added to the driver** so the next run answers it instead of the next reader guessing:
`arm_pair_min` now checks each returned depth against the two bounding radii and, the first time one
exceeds it, prints the distance, the bound, the `fromto` segment the same call reports, and the
centre separation. A segment whose length disagrees with the distance is the instrument's signature.
Print-only; it decides nothing.

⇒ The same sentence the 08-02 handoff found four times holds again, one layer in:
**a pose the arm reaches is not made valid by the gate opening.**

### 8.3 Where it stopped

STEP 3, deliberately: the driver raised

> `STEP3 L: THIS arm's command stopped advancing for a whole step's worth of ticks and its move did
> not finish (the other arm was still advancing, at 49.7% …)`

with the arms at −0.9 mm. ⚠ Note also that STEP 3 works from an **inherited aim pose**, and its
arm-to-arm check states in its own output that *"posts and table are invisible to this test"* — so
the furniture and path tests added on 08-02 are **not** applied at that pose.

### 8.4 ⛔ Not claimed here

Physical validity is not asserted. Per CLAUDE.md the physical-validity verdict needs the video leg
and Rs; this section reports what the instrument printed. `~/Downloads/ur15_live.mp4` was written by
the run and has not been read by anyone.

---

## 9. ⭐ Rs ruled A — rolled back, and the restore is exact

**Rs's decision, this session: A** — pin back to the set `newton 1.4.0` declares.
Executed 2026-08-03 08:55 JST. `rollback_install.log`, `pip_freeze_AFTER_ROLLBACK.txt`.

```
pip install 'mujoco==3.10.0' 'mujoco-warp==3.10.0.3'    -> rc=0
```

Four checks, all passed:

| check | result |
|---|---|
| 246-package freeze vs the pre-upgrade freeze | **byte-identical**, sha256 `f700f94f8b56eeaa856365f29716a75fc17330d42fccce6bb7dba5a0f7d41668` |
| `newton`'s two declared pins | **both SATISFIED** |
| `SolverMuJoCo` version-mismatch warning | **0 raised** |
| `mj_geomDistance`, all 496 gripper pairs vs the 3.10.0 snapshot | **bitwise identical** |

⇒ The 08-02 evidence is back on the substrate it was measured on, and nothing needs re-deriving.

**What the excursion bought, stated plainly:** nothing functional. `newton` and `warp-lang` were
already at their latest release, so the only movable packages were the two that `newton` pins.
"Latest upstream" and "the set newton supports" are not the same set, and for this stack the second
is the one that exists.

**What it cost, and what it is worth:** ~35 minutes, and it produced the measurement nobody had —
that `mj_geomDistance` moves up to 87 mm across a mujoco minor release, on the claw's own geoms, in
the direction that turns a rejection into an acceptance. That number now exists in the record and
did not before.
