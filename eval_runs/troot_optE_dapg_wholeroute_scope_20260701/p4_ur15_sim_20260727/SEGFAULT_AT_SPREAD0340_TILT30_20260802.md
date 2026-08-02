# A point that crashes — and the story I told about it first

## 1. ⛔ Correction, before anything else

What I sent p18 in `-224 §2` — that the point was **slow**, that it "ran past fifteen minutes
without printing its first count", and that at spread 0.340 more geom pairs fall inside the pair
cutoff so every candidate costs more — is **withdrawn**. None of it was measured.

- The `RuntimeError` text interpolated `TIMEOUT_S`, the **cap**, not the elapsed time. It read
  *"did not finish inside 900s"* for a point that had died in well under two minutes. I read the
  message and reported the cap as an observation.
- Measured: in the aborted run the point started at **11:05:32** and the sweep was dead by
  **11:06:53** — **≤ 81 s**, not 900. Run alone it dies at **37.1 s**.
- The physical explanation was invented to account for a duration that never happened. It may even
  be true of some other point; it was not true here, and it was not measured anywhere.

⚠ The timeout therefore **never fired**. Raising 900 → 2400 s was not a fix for this. It stays as
insurance against a genuinely slow point and is not evidence about this one.

## 2. What is actually happening

| run | exit | elapsed | stdout |
|---|---|---|---|
| isolated 1 | **139** (SIGSEGV) | 37.15 s | 33 lines |
| isolated 2 | **139** | 37.69 s | 33 lines |
| isolated 3 | **139** | 37.15 s | 33 lines |
| under faulthandler | **139** | ~37 s | 33 lines |

Deterministic, to the tenth of a second, at the same point in execution every time.

**Where.** `faulthandler`: `ur15_steps_wired.py:1455 in solve_ik` — `mujoco.mj_forward(m, sc)`
inside the IK iteration loop (mujoco 3.10.0).

**Not a bad joint vector.** A scratch copy checked `np.isfinite(q).all()` and `|q|max ≤ 1e3` on the
joints of arm `t` immediately before every one of those calls. Neither guard ever fired, so the
fault happens with a finite, in-limits pose ⇒ it is inside MuJoCo's collision stage, on an
**intermediate** IK pose rather than a converged one.

**Why the 24-draw grid never saw it.** That table has a row for this point. The crash needs enough
draws to reach the candidate that triggers it — one more way the draw count is part of what a
table says.

## 3. The fix, and the control that says it is safe

The IK inner loop reads only kinematic quantities: `mj_jacBody`, `sc.xmat`, and `pinch()`.
Contacts are read **after** convergence, by `touching()` at `:1494`. So the collision stage inside
the loop is pure overhead — and it is the part that crashes.

`mujoco.mj_kinematics(m, sc)` + `mujoco.mj_comPos(m, sc)` (jacobians need `cdof`) in place of the
in-loop `mj_forward`:

- **The crashing point completes**: L 54 solved / 0 clear, R 132 / 32, arms closest +0.0 mm.
- ⭐ **Control — a point that already has a measurement.** crown none / spread 0.280 / tilt 45:

  | | baseline (`mj_forward` in loop) | kinematics only |
  |---|---|---|
  | L | 56 solved / 4 clear | 56 solved / 4 clear |
  | R | 132 solved / 8 clear | 132 solved / 8 clear |
  | arms closest | +11.9 mm (8 ↔ 46) | +11.9 mm (8 ↔ 46) |

  and **all 14 printed pose lines** — every clear pose and both chosen `q` — are identical to the
  last printed digit (`diff` clean). The random stream is untouched because the change consumes no
  draws.

⛔ **Not applied.** The driver is the instrument and the grid is mid-run; changing it now would
split the grid across two versions. It lands after the grid finishes, with this control recorded.

## 4. ⛔ And one more label that cannot tell two things apart

The row I added this morning reads `-- NOT MEASURED: no interleave line within 2400s --` whichever
way the point failed — cap reached, or process killed by a signal. That is the same defect as the
one the whole morning has been about, written by me while fixing it. The row has to carry the
**measured elapsed time and the exit code**, so a crash and a timeout cannot share a sentence.

## 5. What is still open

1. **Why MuJoCo faults there** is not diagnosed — only that it is in the collision stage on an
   intermediate pose. The fix routes around it rather than explaining it.
2. ⚠ The full `mj_forward` at `:1475` / `:1484` and the contact read at `:1494` still run on
   **converged** poses. If a converged pose can trigger the same fault, this fix does not cover it.
   Nothing has been observed there; nothing has been proven either.
3. The point's own numbers (L 54 / 0 clear) are from the patched scratch copy, not from the grid.
   They are stated here as a demonstration that the point can be measured, ⛔ not as a grid row.
