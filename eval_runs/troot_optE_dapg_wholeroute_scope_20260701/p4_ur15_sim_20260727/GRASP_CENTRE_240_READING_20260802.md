# The grasp-centre sweep at 240 draws — it refutes my own verdict

**Artifacts.** `GRASP_CENTRE_SWEEP_TRIES240.txt` (12 centres, this run); the banked 24-draw table
`GRASP_CENTRE_SWEEP_20260729.txt` it replaces the conclusion of; point logs for the three centres
that open, in `grasp_centre_logs_240/`.

**Mounting.** Read out of the run itself, not assumed: `spread 0.220 tilt 45.0 deg crown r 0.110`
— **the built cell**. `GRASP_CENTRE_X` is the only thing swept.

⛔ Not a verdict about what to build. Where the pair should sit is p5's call and Rs's to settle.

---

## 1. ⛔ The claim that is refuted

`P4_T43_VERDICT_RSTECHLEAD_20260729.md` §3, mine:

> p5 asked for the highest grasp-pair centre x at which the left arm keeps ≥1 collision-free start
> pose. **There is no such x.** Across +0.150 to −0.250 — every centre the cable can carry the span
> at — the left arm keeps **zero**.

**There is such an x. There are three of them.** At 240 draws, at the same mounting, over the same
range:

| centre x [m] | L solved | L clear | R solved | R clear | held links |
|---|---|---|---|---|---|
| +0.150 | 58 | 0 | 132 | 19 | cab27 / cab32 |
| +0.120 | 56 | 0 | 133 | 17 | cab25 / cab30 |
| +0.090 | 55 | 0 | 132 | 14 | cab23 / cab28 |
| +0.060 | 55 | 0 | 132 | 12 | cab21 / cab26 |
| +0.030 | 56 | 0 | 133 | 0 | cab19 / cab24 |
| 0.000 | 55 | 0 | 137 | 0 | cab17 / cab22 |
| −0.030 | 75 | 0 | 139 | 0 | cab15 / cab20 |
| −0.060 | 90 | 0 | 140 | 0 | cab13 / cab18 |
| −0.100 | 112 | 0 | 139 | 0 | cab10 / cab16 |
| **−0.150** | 140 | **15** | 139 | **3** | cab7 / cab12 |
| **−0.200** | 138 | **31** | 139 | **4** | cab3 / cab9 |
| **−0.250** | 133 | **30** | 140 | **2** | cab0 / cab6 |

The 24-draw table read **0 for the left arm at every one of these**, including the three that open.

## 2. ⭐ And two of them carry the third leg

The interleave line is in each point's log, measured at the same chosen poses as the counts, and on
these rows both arms are clear so it is readable on its own:

| centre | L clear | R clear | arms closest | all three legs |
|---|---|---|---|---|
| −0.150 | 15 | 3 | **+10.7 mm** | **witness** |
| −0.200 | 31 | 4 | **+10.7 mm** | **witness** |
| −0.250 | 30 | 2 | +0.0 mm | fails — the chosen pair touches |
| −0.100 | 0 | 0 | −131.9 mm | not readable, both arms put back |

⇒ **At the built mounting, moving the grasp pair to x ≈ −0.150 … −0.200 gives a witness**: a clear
left start pose, a clear right start pose, and about eleven millimetres between the arms at the
commanded 88 mm span.

## 3. What this does to the day's other conclusion

The grid (`GRID240_READING_20260802.md` §1) shows the built mounting keeping **L clear = 0** at 240
draws — measured at the **built grasp centre**. Both facts hold:

- **at the built grasp centre**, the built mounting does not open, even at ten times the sample;
- **at grasp centre −0.150 or −0.200**, the same mounting does.

⇒ The grasp centre is a **live variable**, not a dead one. What said otherwise was twenty-four
draws. ⛔ I wrote in the grid reading that "the variable that matters is the mounting"; that was
about to be said out loud on the strength of a sweep whose range I had cut short, and it is not
what the evidence says.

## 4. ⚠ What a reader must carry with this

1. **The opening centres sit at the cable's end.** Held links go cab7/cab12, cab3/cab9, cab0/cab6 —
   cab0 is the end of the cable. Whether the pair may sit there at all is a task question (where
   the clips are), and it is **not mine**. The measurement says the arms can start clear there; it
   does not say the route can be run from there.
2. **Start pose only**, as everywhere in this investigation.
3. **The boundary is not resolved.** The sweep steps 50 mm between −0.100 (closed) and −0.150
   (open). The transition lies somewhere in between and was not sampled.
4. **A fail is still not a refutation** — the interleave is read at one pose pair out of N × M, so
   the nine closed centres are "no witness found", not "no witness exists".
5. **240 is a sample too.** Nine centres read zero here; four zeros in the mounting grid moved
   between 24 and 240, and nothing says none of these would move between 240 and 2400.

## 5. How this was nearly reported the other way

The first run of this sweep used the script's default centre list, **+0.150 … −0.060** — eight
points, all closed — and printed *"LEFT ARM keeps ZERO collision-free candidates at every centre
swept"*. That sentence is true of what it swept and would have been read as confirming the verdict.
The banked 24-draw table covers **+0.150 … −0.250**, and the three centres that open are all in the
part the shorter list left out. ⇒ The scope check — does my range match the range of the claim I am
testing? — is the only thing that stood between a confirmation and a refutation.

---

## 6. ⭐ The boundary, bisected — the window is wider and closer in than §1 said

§1 swept in 50 mm steps and reported −0.150 as "the highest swept centre with a left-arm
candidate", with the explicit warning that it is a swept value and not a boundary. Bisecting the
gap between −0.100 (closed) and −0.150 (open), at 240 draws, same built mounting
(`GRASP_CENTRE_SWEEP_TRIES240_BOUNDARY.txt`; point logs in `grasp_centre_logs_240/`):

| centre x [m] | L solved | L clear | R clear | arms closest | all three legs |
|---|---|---|---|---|---|
| −0.110 | 123 | **1** | 2 | +0.0 | no witness found |
| **−0.120** | 124 | **1** | 2 | **+24.2 mm** | **witness** |
| −0.130 | 126 | **7** | 3 | +0.0 | no witness found |
| −0.140 | 137 | **14** | 3 | +0.0 | no witness found |

1. ⭐ **The left arm is open at every bisected centre**, including −0.110 — the point immediately
   adjacent to −0.100, which is measured closed. ⛔ **I first wrote that as "the boundary is
   between −0.100 and −0.110, a 10 mm interval". That is an overclaim** and p6 returned it
   (`-247`): calling it a *boundary* assumes the left-arm-clear predicate is monotone in the
   centre, and nothing here establishes that. What is measured is narrower — **the nearest sampled
   closed centre and the nearest sampled open centre are 10 mm apart.** A bracket between sample
   points, not a boundary.
   ⚠ The same caution runs the other way: the nine closed centres above −0.100 were sampled at 30
   and 50 mm steps, so without monotonicity an open centre could sit between two of them
   unsampled.
2. ⭐ **−0.120 is a witness**, 30 mm closer to the built centre than the nearest one previously
   known. The witness set is now **−0.120, −0.150, −0.200**. ⚠ **It is not an interval**: −0.130
   and −0.140 sit between two witnesses and are not witnesses themselves. ⛔ Which does *not* mean
   the set has holes — those rows are "no witness found at the chosen pair", and the 125-pair
   measurement in point 4 is what would say whether they are holes or unmeasured.
3. ⚠ **The interleave is not monotone** across the open region: +0.0, +24.2, +0.0, +0.0, +10.7,
   +10.7, +0.0 from −0.110 to −0.250. Nothing in the cell moves between those rows except the
   grasp centre; what changes is **which pose pair gets chosen**. This is §4 of the grid reading
   showing up as a jagged column rather than as an argument.
4. **The four "no witness found" rows are cheap to settle**: 2, 21, 42 and 60 pairs, of which one
   each was measured — **125 pairs in total** for the whole open region. That is the all-pairs
   measurement p5 costed (`bank #71`) applied here.

⛔ Still start-pose only, and still not a recommendation.

## 7. ⭐ Why the interleave column is jagged — p6's identification, re-derived

p6 (`-247`) traced the non-monotone column to the **argmin switching**: the closest pair of geoms
is not the same pair from one centre to the next. Re-derived here from the point logs rather than
taken on their word — **six distinct closest pairs across eight centres**:

| centre | arms closest | the pair |
|---|---|---|
| −0.100 | −131.9 mm | 6 ↔ 44 |
| −0.110 | +0.0 | 8 ↔ 45 |
| **−0.120** | **+24.2** | **16 ↔ 50** — occurs at this centre only |
| −0.130 | +0.0 | 12 ↔ Rg_left_pad2 |
| −0.140 | +0.0 | 41 ↔ 52 |
| −0.150 | +10.7 | 6 ↔ 44 |
| −0.200 | +10.7 | 6 ↔ 44 |
| −0.250 | +0.0 | Lg_right_pad_f1ext ↔ 50 |

⇒ The column is **not a continuous quantity being sampled**. It is a minimum over a set whose
argmin changes, so **interpolating between two of its rows, or bracketing a crossing in it, is not
a valid operation**. The +24.2 mm at −0.120 is that centre's own pair; it says nothing about
−0.115 or −0.125.

⚠ This is the same shape as everything else in this file — a number that looks like a function of
the swept variable and is not. It is also why point 1 above had to be weakened: a bisection assumes
the thing being bisected is monotone, and neither column here has been shown to be.
