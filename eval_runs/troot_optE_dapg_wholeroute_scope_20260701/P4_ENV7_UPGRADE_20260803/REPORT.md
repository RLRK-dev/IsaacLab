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

- `pip_freeze_BEFORE.txt` (246 pkgs, sha256 `f700f94f8b56eeaa856365f29716a75f…`)
- `pip_freeze_AFTER.txt` (246 pkgs)
- `install.log` — rc=0, 06:19:34–06:19:41 JST
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
needs checking.** This upgrade widens that gap; it does not open it.

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

**31 artifacts** written in `p4_ur15_sim_20260727/` on 2026-08-02 were measured on **mujoco 3.10.0 /
mujoco-warp 3.10.0.3 / newton 1.4.0 / warp-lang 1.15.0** — the closed list is
`premeasured_on_3.10.0.txt` (built by mtime window, not by recall).

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

⇒ **The instrument's reading did not move.** The clearance and arm-to-arm path tests return the same
candidate sets and the same standing errors under `mujoco` 3.11.0 as under 3.10.0.

⚠ **Scope of this ✅.** It covers the start-pose solve at grasp centre **−0.200**, `START_TRIES=240`,
`UNWRAP_SOLVE=1 ARM_PATH=1`, on this driver and this mounting. It does **not** cover the other six
grasp centres, the crown/mast sweeps, the clamp-window probes, or any quantity measured by a
different instrument. Those 31 artifacts keep their recorded stack (§5) and are not re-derived here.

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
the path was free. The arms passed **171 mm through each other** during a step that reported
complete success.

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
