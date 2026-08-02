# The two crown sweeps at 240 draws — the last of the four

**Artifacts.** `CROWN_HEIGHT_SWEEP_TRIES240.txt`, `CROWN_RADIUS_SWEEP_TRIES240.txt`.
With these, all four 24-draw sweeps in this investigation have been re-run at 240.

⛔ Not a verdict. What to build is p5's call and Rs's to settle.

---

## 1. ⛔ Crown HEIGHT — the third banked conclusion refuted, and it lands on the head question

Same mounting as the banked table (**spread 0.280, tilt 20**), so this is like-for-like. Radius is
derived as `(1.530 − Z0)/2`, so every row is a head whose top lands exactly on the mounts.

| Z0 [m] | R [m] | L clear @24 | **L clear @240** | R clear @240 | arms closest | |
|---|---|---|---|---|---|---|
| **1.330** | **0.100** | 0 | **5** | 31 | **+14.7 mm** | **PASS** |
| 1.380 | 0.075 | 0 | 4 | 30 | +0.0 | fail |
| 1.430 | 0.050 | 0 | 5 | 31 | +0.0 | fail |
| 1.470 | 0.030 | 0 | 5 | 31 | +0.0 | fail |
| 1.510 | 0.010 | 0 | 4 | 29 | +0.0 | fail |

The banked table's conclusion was **"⭐ PASSING heights: none"**. At 240 draws **one passes**, and
it is the **tallest** head — `Z0 1.330 / R 0.100`, the one that actually reaches the mounts.

⭐ **The left arm is clear at every height** (4–5). What separates the rows is the **interleave**:
+14.7 mm at the tallest head and +0.0 at the other four. ⇒ The head's height is not deciding
whether the left arm can stand somewhere; it is deciding **which pose pair gets chosen**, and only
one of those pairs is separated. ⚠ And by §4 of the grid reading, the four +0.0 rows are "no
witness found at the chosen pair", not "no separated pair exists".

⇒ This is the third banked conclusion of mine refuted today by the same mechanism, after the
grasp-centre and work-row sweeps.

## 2. Crown RADIUS — ⛔ not a re-run, because the banked table cannot say where it was taken

`CROWN_RADIUS_SWEEP_20260729.txt` has **no `TAKEN AT` line** — that header was added after it, in
response to this exact failure (`sweep_mounting.py:164-168`: the first crown sweep ran entirely at
one tilt and I reported its result as a property of the crown). Its point logs have since been
overwritten. ⇒ **Its mounting is not recoverable from the artifact or from any surviving log**, so
nothing can be re-run against it like-for-like. What follows is a **new measurement at a named
mounting**, not a correction of that table.

**At the built mounting (spread 0.220, tilt 45), 240 draws:**

| crown r [m] | L clear | R clear | arms closest | |
|---|---|---|---|---|
| none | **3** | 14 | +0.0 | fail |
| 0.020 | **1** | 14 | +0.0 | fail |
| 0.050 | **0** | 34 | +0.0 | fail |
| 0.080 | 0 | 34 | +9.6 | fail |
| 0.110 (built) | 0 | 19 | +26.2 | fail |

1. ⭐ **The left arm closes between radius 0.020 and 0.050.** Removing the crown gives it three
   clear poses, a 20 mm crown one, and a 50 mm crown none. ⚠ The boundary is between two swept
   values, not resolved.
2. ⛔ **No radius gives a witness at this mounting.** Where the left arm is clear the pair touches
   (+0.0); where the pair separates (+9.6, +26.2) the left arm has nothing. The two conditions do
   not overlap anywhere on this column — consistent with the grid, which fails 0.220/45 on both
   sheets.
3. ⚠ Reading 1 and 2 together does **not** license "a smaller crown would fix the built cell":
   it says the left arm's *count* recovers as the crown shrinks, and that at no swept radius did
   the chosen pair also separate. A fail is not a refutation.

## 3. Where the four sweeps stand now

| sweep | 24-draw conclusion | at 240 |
|---|---|---|
| grasp centre | no centre keeps a clear left pose | ⛔ **refuted** — 3 open, 2 are witnesses |
| work row y | no offset keeps a clear left pose | ⛔ **refuted** — 3 open, 2 are witnesses |
| crown height | no height passes | ⛔ **refuted** — the tallest head passes |
| crown radius | (conclusion not stated; mounting not recorded) | **not comparable**; new measurement above |

⇒ **Three of the three testable conclusions were refuted.** The fourth could not be tested because
the artifact does not record the conditions it was taken under.

## 4. Limits

1. **Start pose only**, everywhere.
2. **240 is a sample too** — three of these zeros moved between 24 and 240; nothing says none would
   move at 2400.
3. **The interleave is read at one pose pair** out of N × M, so every "fail" here is "no witness
   found", not "no witness exists". The all-pairs measurement p5 costed (`bank #71`) is what would
   convert those into real negatives.
4. **Both crown sweeps are single-mounting columns.** §1 is 0.280/20 and §2 is 0.220/45; neither is
   a statement about the crown in general — which is the mistake §2 exists to record.
