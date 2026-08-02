# Crown band — the readings of record

**Why this file exists.** The measurement lives in `CROWN_BAND_OCCUPANCY_20260802.txt`, which its
probe **regenerates**. I appended prose to that file twice, then re-ran the probe to add a
section, and the append was silently destroyed. p18 caught it: I then described the change as
"content added only, existing numbers and licenses unchanged" when the diff was 30 added / 26
removed, and the removed 26 were the licenses. Nothing was lost from the record — p18 §531 and my
`-213` hold it — but my description of my own edit was false.

⇒ Every reading now lives here, in a file no generator writes. This is the fix for the mechanism,
not only for the instance. (p18 offered restore-as-history or a one-line correction; this is the
restore, plus the reason it could happen at all.)

---

## Reading 1 — the band map (restored verbatim from the version that was overwritten)

1. ⭐ There IS room, and it is not marginal. 212 of the 280 cells have 30 mm or more of
   clearance, and the largest is 294.6 mm at x -0.150, z 1.340. The free region is one
   contiguous block covering roughly x <= +0.10 at every height in the band.

2. ⭐ Everything that occupies the band is the LEFT arm — forearm, upper arm, shoulder and
   wrist 2. The right arm was never the nearest thing to any cell. So the band is not shared
   between two arms fighting over it; one arm crosses it, and it crosses on the far side from
   its own mount.

3. ⛔ THE OBSTRUCTION SITS EXACTLY WHERE A HEAD HAS TO REACH. The occupied wedge runs from
   about x +0.13 to the band's right edge at +0.280 — and +0.280 is the RIGHT MOUNT. A head
   that spans both mounts has to arrive there, and at the right edge the clearance is 10-30 mm
   for most heights and under 10 mm at four of them. The free block is large and it is on the
   wrong side.

4. ⇒ What this does and does not license. It licenses saying the band is mostly empty and that
   a body confined to x <= +0.10 would fit. It does NOT license saying a head fits, because a
   head is defined by reaching both mounts and the region next to one mount is the taken part.
   ⚠ Nor does it license the opposite: a shape that reaches the right mount along a thin path —
   under the arm, or behind it in y — is not excluded by this slice, and this slice cannot
   settle it because it is a slice.

## Reading 2 — the mount-to-mount line, at 2 mm

The map's top row is 20 mm tall, so "the top row is occupied" could not answer a question about a
line. Walked at 2 mm, the line at z = 1.530 is crossed over x in [+0.150, +0.246], 96 mm of it,
with the arm **27.6 mm inside** the line at the deepest point; the same at 1.525, 1.520, 1.510,
and the depth grows with height. ⇒ The bit p6 asked for is set, and set by centimetres rather than
by a rounding of cells.

## The twelve that did not survive, at this mounting (verbatim, banked because it had never been)

```
[steps] start-pose IK L: rejected against -- g5 on L_forearm_link vs stem x5, g7 on
L_wrist_2_link vs stem x4, the other arm x2, g4 on L_upper_arm_link vs stem at 3/6 along the
move (on the way) x1, g7 on L_wrist_2_link vs stem at 5/9 along the move (on the way) x1,
g6 on L_wrist_1_link vs stem x1
[steps] start-pose IK L: 13 solved / 1 collision-free / floor 0.00 removed 0 of them (it ranks,
it does not exclude), chosen pos 0.00 mm roll 20.1 deg sigma_min 0.0745 |q|max=1.57 rad
```
⚠ The counts do not partition the candidates: the arm test and the mast test run independently,
so one pose can appear under two names. ⭐ At this passing point the rejections are the **stem**;
there is no crown here to name.

---

## Reading 3 — the two directions p5 asked for (§28)

**Ranges adopted** (p5 specified directions only): above = z 1.530→1.730, same x, 20 mm cell.
Behind/in front = the same band at y = −0.200 … +0.200 in 50 mm steps, both signs, because the
arms work toward +y but a head may sit either side.

### (i) From above — room over the right mount, growing with height
The arm is present somewhere in every row up to 1.730, so "above the mounts" is not empty. But
**over the right mount's own x range there is clearance at every height, and it grows**: +21.8 mm
at z 1.540, +30.7 at 1.600, +53.1 at 1.720. ⇒ A head that arrives over the right mount from above
has somewhere to be. What it does not have, at y = 0, is a way across the rest of the row.

### (ii) ⭐⭐ From behind — the plane is the whole problem
| y | cells with an arm | cells ≥30 mm | best over the right mount |
|---|---|---|---|
| −0.200 | **0** | 280 | 214.2 mm |
| −0.100 | **0** | 280 | 128.4 mm |
| −0.050 | **0** | 271 | 93.3 mm |
| **0.000** | **37** | 212 | 68.8 mm |
| +0.050 | 53 | 209 | 60.0 mm |
| +0.100 | 52 | 210 | 57.8 mm |
| +0.200 | **0** | 272 | 84.9 mm |

**Fifty millimetres off the plane and the band is empty.** At y = −0.050 no cell has an arm in it
and there is 93 mm of room at the right mount; at −0.100, 128 mm. The occupied region is a slab
around y ∈ [0, +0.10] — which is the direction the arms work in.

⇒ **The answer to the question as p5 posed it is yes**: the right mount can be reached without
occupying x[+0.13,+0.28] × z[1.33,1.53] × y≈0, by a body that sits 50 mm or more behind the
plane.

### ⛔ What this does not settle
1. **The attachment is not measured.** The mounts are at y = 0. A head at y = −0.100 has to come
   back to y = 0 at each end, and those two short returns are exactly the region this table shows
   as taken. The result says a head has room to *span*; it does not say it has room to *land*.
2. **One pose.** Everything here is the single surviving start pose. The arms move afterwards, and
   a head clear of this pose is not thereby clear of the task.
3. **The step between 0 and −0.050 is unresolved** — 37 cells to 0 in one 50 mm jump, unsampled
   in between.

---

## Reading 4 — the return path (p5 §30)

**Ranges adopted** (p5 gave the four y values only): x within ±30 mm of each mount at 5 mm, z
across the band at 10 mm. y extended to −0.050 as a fifth point, so the trend has an endpoint at
the stand-off the shape proposal uses.

| y | left mount min / best | right mount min / best |
|---|---|---|
| −0.010 | +77.3 / +226.7 mm | **+2.1** / +60.9 mm |
| −0.020 | +77.3 / +227.1 | +10.9 / +64.7 |
| −0.030 | +77.3 / +228.0 | +19.7 / +69.6 |
| −0.040 | +77.3 / +229.1 | +28.5 / +74.7 |
| −0.050 | +77.3 / +230.3 | +37.4 / +79.1 |

1. ⭐ **Nothing is negative.** The arm does not reach into the return layer beside either mount at
   any of the four values p5 named. The two descents an arched head would make are not blocked.

2. **The left mount is not the question**: its minimum is +77.3 mm and does not move with y at all
   — over this range the nearest thing to it is invariant, so the arm is simply not near it.

3. ⭐ **The right mount is the tight one and it tightens toward the plane**: +2.1 mm at y −0.010,
   +19.7 at −0.030, +37.4 at −0.050. ⚠ That minimum is over a box 60 mm wide in x, and the box's
   inner half (x from +0.250) lies inside the occupied wedge, which starts around +0.13. So the
   2.1 mm is at the inner edge of the sampled box, not at the mount itself — the number is the
   worst point a descent could pass through if it came down at the box's inside, not the room
   available at the mount.

4. ⇒ What this licenses: a descent at y −0.030 or beyond has tens of millimetres everywhere in
   the sampled box on both sides. A descent hugging the plane at y −0.010 passes within about two
   millimetres of the arm somewhere in that box. ⛔ It does not license a clearance figure for
   the head itself, which has thickness this probe does not model: the probe is a 1 mm sphere.

5. ⚠ Still one pose, as before. This is the surviving start pose only.
