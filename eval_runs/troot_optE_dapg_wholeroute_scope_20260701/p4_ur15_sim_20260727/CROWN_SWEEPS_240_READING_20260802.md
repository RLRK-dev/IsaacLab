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

## 2. Crown RADIUS — ⛔ CORRECTED: it *is* a re-run, and the mounting was recorded all along

> ⛔ **What this section said first was wrong.** I wrote that the banked table's mounting is *not
> recoverable*, because it has no `TAKEN AT` line. p6 returned it (`-221`) and I checked: the
> table's own line 37 says, in prose, *"Every row of this table was taken at the built tilt of 45
> degrees"* — a correction block **I wrote into that file myself** on 07-29. I searched for the
> label and, not finding it, declared the fact absent. ⚠ Today's recurring failure, in its most
> pointed form: the thing I could not find was my own writing.
>
> The spread is recoverable too, and independently: the table's `L solved` is **7** at every
> radius, and at tilt 45 the grid's L-solved signature is **7 / 8 / 9 / 14** for spreads
> 0.220 / 0.280 / 0.340 / 0.400 — on *both* crown sheets, so 7 identifies **0.220** uniquely
> (`SPREAD_TILT_SWEEP_TRIES24_20260729.txt`, re-derived here, not taken on p6's word).
>
> ⇒ The banked table was taken at **spread 0.220, tilt 45 — the built mounting**, which is exactly
> where the measurement below was run. **It is like-for-like after all.**
>
> ⚠ The lesson survives but changes shape: what rescued the provenance was a *different* artifact
> written later (the prose block, and the grid's signature), not the table's own field. A silent
> field is still the defect — `TAKEN AT` exists because of it — and a decoder existing elsewhere is
> luck, not design.

`sweep_mounting.py:164-168` records why the header was added: the first crown sweep ran entirely at
one tilt and I reported its result as a property of the crown.

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
| crown radius | left arm zero at every radius | ⛔ **refuted** — 2 of 5 zeros were the sample |

⇒ **All four were testable, and all four had sampling zeros.** The radius column at 24 draws read
0 at every radius; at 240 it reads **3, 1, 0, 0, 0**.

| radius | L clear @24 | **@240** |
|---|---|---|
| none | 0 | **3** |
| 0.020 | 0 | **1** |
| 0.050 | 0 | 0 |
| 0.080 | 0 | 0 |
| 0.110 | 0 | 0 |

### ⚠ And the fails here are the *weak* kind (p5 `-235`)

On the two radius rows where the left arm is clear, **both** arms are — so the interleave was read
at 1 pair out of 42 and 1 out of 14. On the four failing height rows, 4 pairs out of **546**.
⇒ **A thin crown at 45° is not excluded**; it was not measured. p5 costs the decision at 56
distance evaluations for the radius column. ⛔ "No radius gives a witness" is what the table
supports; "no radius works" is not.

## 4. Limits

1. **Start pose only**, everywhere.
2. **240 is a sample too** — three of these zeros moved between 24 and 240; nothing says none would
   move at 2400.
3. **The interleave is read at one pose pair** out of N × M, so every "fail" here is "no witness
   found", not "no witness exists". The all-pairs measurement p5 costed (`bank #71`) is what would
   convert those into real negatives.
4. **Both crown sweeps are single-mounting columns.** §1 is 0.280/20 and §2 is 0.220/45; neither is
   a statement about the crown in general — which is the mistake §2 exists to record.


---

## 5. ⭐⭐ ALL PAIRS on both crown columns — every row with two clear arms is a witness

Rs authorised this (`RS_AUTHORISATION_CUSTODY_P4_20260802.md`; the crown column was named in the
approved text). Driver's own `arm_pair_min` over every clear L × R pair, no IK and no draws.
Logs: `allpairs_logs/`.

| column | row | clear L × R | pairs | chosen pair | **BEST pair** |
|---|---|---|---|---|---|
| radius @ 0.220/45 | **none** | 3 × 14 | 42 | +0.0 | **+37.5 mm** |
| radius @ 0.220/45 | **0.020** | 1 × 14 | 14 | +0.0 | **+37.5 mm** |
| height @ 0.280/20 | 1.380 | 4 × 30 | 120 | +0.0 | **+35.7 mm** |
| height @ 0.280/20 | 1.430 | 5 × 31 | 155 | +0.0 | **+37.2 mm** |
| height @ 0.280/20 | 1.470 | 5 × 31 | 155 | +0.0 | **+37.9 mm** |
| height @ 0.280/20 | 1.510 | 4 × 29 | 116 | +0.0 | **+38.9 mm** |

**602 pairs. A separated pair exists in 6 of 6.**

### ⛔ Two of my own readings in this file are refuted

1. **§2 point 2 said "No radius gives a witness at this mounting… the two conditions do not overlap
   anywhere on this column."** They overlap at both rows where the left arm is clear. ⇒ **At the
   built mounting, with the crown removed or at 20 mm, all three legs hold** — 3 clear left poses,
   14 clear right, and a pair separated by 37.5 mm.
   ⚠ What still stands: at the built crown of **0.110** the left arm has **no** clear pose at all
   (L clear 0 at 240 draws), so there is no pair to evaluate. **The built cell's zero is still
   real — and it is the crown that causes it.** The left arm closes between radius 0.020 and 0.050
   (§2 point 1), and below that the mounting works.
2. **§1 said the tallest head is the one that passes, and it is the only one.** ⛔ **All four other
   heights are witnesses too** (+35.7 … +38.9 mm). So the height decides **nothing** about passage
   here: §1's mechanism ("the height decides which pose pair gets chosen") was right, and the
   consequence I drew from it was wrong. Every head in the swept range has a separated pair.

### ⭐ What this adds to the standing recommendation

Menu (0) as it stands keeps the reference cell whole and moves the grasp pair to
−0.120 … −0.200. This measurement puts a **second** witnessed option on the table: **keep the
grasp centre where it is and shrink the crown to 20 mm or less.** ⛔ Whether the crown may be
changed at all is not mine — its size came from a photograph and the reference asset carries no
crown collision shape (`sweep_mounting.py:164-168`). Both options are now measured; choosing is
p5's and Rs's.

⚠ Still start-pose only, and a witness pose pair is not a route.
