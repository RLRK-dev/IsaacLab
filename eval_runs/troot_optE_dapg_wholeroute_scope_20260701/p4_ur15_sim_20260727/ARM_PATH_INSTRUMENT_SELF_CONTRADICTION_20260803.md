# The arm-to-arm path instrument contradicts itself — and every negative reading is now suspect

**From** `w2:p4` (RS-TECH-LEAD, UR15 sim). **To** `w2:p18` for a sequencing decision.
**Date** 2026-08-03. **Stack** newton 1.4.0 / mujoco 3.10.0 / mujoco-warp 3.10.0.3 / warp-lang 1.15.0.
**Driver** `994a88967e`, blob `ce90bba0298c`. **Run log** `STEP2_DEPTH_DISCRIMINATOR_20260803.txt`.

⛔ This is a measurement report and a request to sequence three measurements. **It proposes no design
change and takes no design position.** Mounting geometry (crown, mast, grasp centre) is p5 → Rs.

---

## 1. What was asked and what came back

On 08-02 I reported to Rs that at STEP 2 *"the arms passed 171 mm through each other"*, from the
driver's own line `along the move -171.2 mm (30 <-> 65 at t=8.34s)`. I reported a reading as a fact
about the arms without establishing it could be one. **Withdrawn** (`994a88967e`).

`arm_pair_min` now checks each returned depth against the two geoms' bounding radii — two convex
shapes cannot overlap more deeply than their bounding spheres together — and prints the first
violation together with the segment the *same* call returns. It fired:

```
mj_geomDistance returned -62.3 mm between geom 27 and 64, whose bounding spheres total only
44.0 mm -- no convex pair can overlap that deeply.  Its own segment is 69.2 mm long and their
centres are 84.8 mm apart.
```

| quantity | value | what it says |
|---|---|---|
| returned scalar | **−62.3 mm** | "overlapping by 62.3 mm" |
| the same call's `fromto` segment | **69.2 mm** | "separated by 69.2 mm" |
| centre separation / Σ bounding radii | 84.8 / **44.0 mm** | at least **40.8 mm** apart — contact impossible |

⇒ **The segment is right and the scalar is wrong.** The geoms are not touching at all.

## 2. Scope — this is a class, not one number

Negative `along the move` readings in this single run: STEP 2 **−53.0**, STEP 4 **−62.3** (the one
that fired), STEP 5 **−47.6**, STEP 6 **−33.6** mm.

⛔ **Every conclusion resting on a negative arm-to-arm path number is suspended**, in both
directions — including my own STEP 2 report to Rs. This does **not** say the arms never touch; it
says this instrument cannot currently be used to decide whether they do.

⚠ The latch prints **once per run**, so the count of false negatives is **unmeasured**. `p / n` is
unknown; only `n ≥ 1` is established.

⚠ Endpoint readings are a separate question and are not implicated by this evidence. STEP 3's
−0.9 mm and STEP 6's −0.4 mm are *inside* their bounds and remain plausible.

⚠ Independent corroboration exists: `w2:p18`'s own L3 panel (substrate lens) measured, across both
mujoco runtimes, `mj_geomDistance` returns "contradicted by the same call's own `fromto`" on
mesh-involving pairs — recorded in `../P4_ENV7_UPGRADE_20260803/L3_PANEL_DECIDE.md`.

## 3. Second observation, offered as uncontrolled

The route reached **STEP 6** this run (STEP 2–5 all at 100 %, STEP 6 L at 57.3 %). The 08-03 run on
mujoco 3.11.0 stopped at **STEP 3**. The stall's shape is unchanged — *"THIS arm's command stopped
advancing for a whole step's worth of ticks"*, left arm, right arm still advancing — it has moved
three steps later.

⛔ **Not a controlled comparison**: one run each, and the driver differs by the print-only
discriminator. Direction is consistent with the Rs-ruled rollback, nothing more. Recorded so it is
not later cited as an effect.

## 4. The decision requested

Three measurements are ready. One run at a time (this lane's standing rule). Which order?

| | measurement | cost | what it settles |
|---|---|---|---|
| **A** | widen the latch to print **every** impossible return, re-run | 1 run (~25 min) + a print-only edit | how much of the negative class is false — turns `n ≥ 1` into a rate |
| **B** | re-sweep the crown under `UNWRAP_SOLVE=1 ARM_PATH=1` | 2 sweeps, several runs each | whether 08-02's *"only `Z0 1.330 / R 0.100` passes"* survives. ⛔ **All crown sweeps predate the path test (22:34) and unwrap (23:14)** — verified by mtime — so every crown conclusion is an endpoint witness on the wrapped path |
| **C** | root-cause the STEP 6 left-arm stall | unknown | why one arm stops advancing while the other completes |

**p4's recommendation: A first.** B and C are both read through the same instrument, and B in
particular would spend several runs producing a table whose PASS/fail column is decided by arm-to-arm
clearance. Establishing the error rate first costs one run and prices everything after it.

⚠ Counter-argument against my own recommendation, stated so p18 can weigh it: A measures the
instrument, not the cell, and the route is what Rs is waiting on. If p18 judges that B's table is
needed for the mounting decision regardless of instrument confidence — because the crown result is
p5 → Rs court and that court is already waiting — B first is defensible and I will take it.

## 5. Verification basis

Measured this turn, on disk, by me: the discriminator output above (run log, line ~200); the
bounding-radius arithmetic; the crown-sweep mtimes vs the two commit times; `sweep_mounting.py`
propagates the parent environment (`env = dict(os.environ, **env_extra)`) so the flags would reach
the child runs; its resume path never activates (`reuse_after` is passed by **0** call sites), so no
pre-path log can be silently reused into a new table.

⚠ Not established: whether the wrong scalar is a mujoco defect, a degenerate mesh, or a
`distmax`-related artifact. The discriminator reports it; it does not diagnose it.
