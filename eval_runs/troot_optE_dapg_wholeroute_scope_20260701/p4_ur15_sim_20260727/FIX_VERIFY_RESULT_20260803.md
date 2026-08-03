# The repair ran, and the rate did not move — which is the design, not a failure

**From** `w2:p4`. **To** `w2:p18`, against ruling 1191 (adopt the fix, keep floor 1) and the
additions in 1195 / 1198 / 1199 / 1204 / 1206 / 1211 / 1217 / 1222.
**Run** `FIX_VERIFY_REPAIR_20260803.txt`, 10:54:30 → 11:20:25, rc=1 (the STEP stall).
**Flags** `GEOMDIST_REPAIR=1 UNWRAP_SOLVE=1 ARM_PATH=1`. **Baseline** `DEPTH_AUDIT_V4_20260803.txt`,
same flags, repair OFF.

---

## 1. What the repair did

**28,664 values replaced by their own segment** — **28,534** where the scalar was exactly zero (the
dominant signature) and **130** keeping the scalar's sign. **0 left unrepairable.**

⭐ The second blind spot p18 banked — genuine contact, where the segment is degenerate too and there
is nothing to repair from — **did not occur once in this run**. It remains a real hole in the method;
it simply was not entered here. Counted, not folded away.

## 2. ⛔ The rate did not move, and that is correct

| | repair OFF | repair ON |
|---|---|---|
| floor 2 | 28,632 (0.2867 %) | **28,664 (0.2870 %)** |
| floor 1 | 14,362 (0.1438 %) | **14,362** |
| arm channel | 0.27692 % | 0.27647 % |

The detectors read the **pre-repair** value; the repair is applied after. So the rate keeps measuring
*how broken the instrument is*, and the repair count measures *how much was mended*. They are
different quantities and the first should not fall. ⚠ It also means **this run does not show the
repair helping** — it shows it firing. Whether the mended values are right is §5.

## 3. Mechanism — now a rate, and it answers

| geom-type pair | violations / calls | rate |
|---|---|---|
| **MESH × MESH** | 21,489 / 4,829,049 | **0.445 %** |
| BOX × BOX | 1,724 / 534,609 | 0.322 % |
| BOX × MESH | 5,069 / 2,823,529 | 0.180 % |
| CYLINDER × MESH | 330 / 926,659 | 0.036 % |
| CYLINDER × BOX | 67 / 278,295 | 0.024 % |
| **CAPSULE × MESH** | **0 / 475,083** | **0.000 %** |
| **CAPSULE × BOX** | **0 / 121,445** | **0.000 %** |

⭐ **Mesh leads on rate, not merely on count** — MESH×MESH is 12× to 18× the cylinder pairs. The
cutoff hypothesis loses on the measure that the count could not settle.

⭐ **CAPSULE is clean over 596,528 calls.** And the crown is a **CAPSULE**, not a cylinder — measured,
`stem` and `foot` are `CYLINDER`, `crown` is `CAPSULE`. ⇒ **"the mast" is not one class.** Its stem
and foot carry a small rate; its crown carries none. Every earlier sentence in this arc that treated
the mast as a unit, mine included, was coarser than the object.

⛔ Also measured, correcting a premise this lane has been repeating: **`stem`, `foot` and `crown` all
have `contype=1 conaffinity=1`.** They are collidable. The "mast is excluded because contype=0"
reasoning does not hold on this model.

## 4. Coverage, in three classes

- **MEASURED** — `arm_pair_min` (9.90 M calls), `column_gap` (1.92 M), `jaw_gaps` (60,652)
- **ASKED, TOO FEW TIMES TO TELL** — `gap`, 13 calls, 0 violations. At the arm rate that is
  P(0 | 13) = 96.5 %; ~1,081 calls are needed before a clean sheet means anything at 95 %.
- **NEVER ASKED** — `furniture_gap`, `release_ctrl`

## 5. ⛔ The trust map, and why its top grade is currently hollow

Per 1211 / 1222, the analytic reference reaches **box×box = 1,724 exactly**: `jaw_gaps` 918 plus
**806** in `arm_pair_min`, from the unique decomposition 27,332 = 21,458 + 5,068 + 806 (re-derived
here, both routes agree).

| grade | target | status |
|---|---|---|
| VALIDATED (analytic box×box) | 1,724 = 6.0 % | ⛔ **effectively 0 so far** — see below |
| SIGN-CHECKED (`d.contact`, collidable pairs) | available in principle | ⛔ **power 0 on random poses** |
| TRUSTED (segment construction only) | the rest, incl. MESH×MESH 74.9 % | no external reference |

⛔ **The external box×box check agreed perfectly — at poses where nothing was wrong.** Over 800
samples the analytic distance matched `mj_geomDistance` with zero disagreements above 0.01 mm. But a
separate measurement showed **3,840 random arm-pair calls produced 0 zero-returns and 0 negatives**.
So the agreement was measured where the defect does not occur, and **it validates nothing about the
repaired values.** A test that could not have come out differently is not a test.

Same for the sign check: arm pairs are **64/64 collidable**, so `d.contact` reaches them in
principle — but with no violations in the sampled poses there was nothing to check.

⇒ **Both external validators need the run's own poses, not sampled ones.** That is a driver-side
change, not a read-side one, and it is not done.

## 6. The GRASP lines — two measurements, not a correction

Per p6 -260, the fix does not correct the old grid; it requires re-running it. So these sit side by
side rather than one superseding the other:

| | repair OFF | repair ON |
|---|---|---|
| `GRASP L: pad faces` | **+0.00 mm** | **+11.30 mm** |
| `GRASP L: opposing claws` | −1.10 mm | **−1.10 mm** (unchanged) |
| `GRASP R: pad faces` | — | +5.36 mm |

⭐ p5's example was exactly the dominant signature: the `+0.00` was a failure to compute, and reads
+11.30 mm once repaired — against a design target of 4.00 mm.
⚠ But `opposing claws −1.10` **did not move**, so that half of p5's example is **not** an
instrument-caused false alarm. The finding was half right and the half that was right was the
load-bearing half.

## 7. Residual floor 1, scoped

15 calls fired floor 1 alone — the scalar fell below the geometric bound *and* its segment agreed, so
the segment substitution has no premise there. Per 1204(i) that count is drawn only from the pairs
whose bounding spheres are far enough apart for the bound to say anything; **all twelve illustrative
rows had a vacuous bound** (−31.9 mm to −275.1 mm), so 15 is a sample of the visible domain, not the
residual for the population. Floor 1 stays: it is the only check with an **external** reference, and
after the repair floor 2 compares the segment against a value derived from the segment.

## 8. Adopted, not yet built

p5's per-candidate call counter (m1225). At the measured 0.287 % per call, a candidate whose verdict
consumes 1,000 distance calls has a **94.3 %** chance of including a contaminated one; at 5,000 it is
indistinguishable from certainty. Until that counter exists, no statement about whether 14→20 or
20→36 lies inside the width contamination can produce is supportable.
