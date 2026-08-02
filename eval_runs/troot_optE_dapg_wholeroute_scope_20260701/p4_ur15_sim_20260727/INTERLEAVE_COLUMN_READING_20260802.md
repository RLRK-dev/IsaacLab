# The interleave column — what it measures, and what it was measured on

**Scope.** This is a reading of the `arms closest [mm]` / `interleaving?` columns of the mounting
grid: the banked 24-draw table `SPREAD_TILT_SWEEP_TRIES24_20260729.txt` (content sha
`7e2423ed…62ee6` @ `528654735e`, byte-identical copy @ `378a5b5cfa`), and the 240-draw grid now in
flight, which prints the same two columns the same way.

⛔ Not a verdict and not a recommendation. Which mounting to build is p5's call and Rs's to settle.

---

## 1. The two columns carry two different quantities

The gap is measured with **both arms at their chosen start poses** (`_interleave_report(_sci)`,
`ur15_steps_wired.py:1723`, on a throwaway state whose joints are set to `START[t]` at `:1717-1722`).

When an arm has **no** collision-free candidate, the solver puts them all back and chooses among
poses that were rejected — `_strict = [c for c in cands if not c[3]]`, `_fell_back = not _strict`,
`free = _strict or cands` (`:1564-1566`), announced loudly at `:1574`.

⇒ On those rows the interleave is the distance between the arms **at a configuration the
collision-free column says does not exist**. Same two columns, two quantities.

**⭐ Nothing is missing from the record.** The printed `collision-free` count *is* `len(_strict)`
(`:1641`), so

> **L free = 0 ⟺ the left arm was put back**, and likewise for R.

What was missing is the label saying that one column governs another. A reader lifting the
interleave column off a row — which is exactly what the spec-comment question invites — is reading
a number whose meaning is decided by a column they were not looking at.

⚠ This changes **no** conjunction verdict: a row with L free = 0 fails on its first leg regardless.

---

## 2. The banked 24-draw table, every row, with the marker derived

| crown | spread | tilt | L solved/free | R solved/free | gap [mm] | interleaving | measured on |
|---|---|---|---|---|---|---|---|
| none | 0.220 | 45 | 7 / 0 | 17 / 4 | +9.6 | no | L put back |
| none | 0.220 | 30 | 7 / 2 | 16 / 3 | +0.0 | YES | **both clear** |
| none | 0.220 | 20 | 16 / 3 | 16 / 3 | +0.0 | YES | **both clear** |
| none | 0.280 | 45 | 8 / 0 | 16 / 3 | +0.0 | YES | L put back |
| none | 0.280 | 30 | 10 / 0 | 17 / 4 | +0.0 | YES | L put back |
| none | 0.280 | 20 | 13 / 1 | 16 / 4 | +22.7 | no | **both clear** |
| none | 0.340 | 45 | 9 / 0 | 14 / 0 | −110.3 | YES | ⛔ BOTH put back |
| none | 0.340 | 30 | 9 / 0 | 16 / 3 | +0.0 | YES | L put back |
| none | 0.340 | 20 | 11 / 2 | 15 / 3 | +0.0 | YES | **both clear** |
| none | 0.400 | 45 | 14 / 0 | 16 / 1 | +0.0 | YES | L put back |
| none | 0.400 | 30 | 9 / 0 | 17 / 1 | +0.0 | YES | L put back |
| none | 0.400 | 20 | 9 / 2 | 16 / 2 | +0.0 | YES | **both clear** |
| 0.110 | 0.220 | 45 | 7 / 0 | 17 / 2 | +26.2 | no | L put back |
| 0.110 | 0.220 | 30 | 7 / 0 | 16 / 3 | +0.0 | YES | L put back |
| 0.110 | 0.220 | 20 | 16 / 0 | 16 / 4 | +9.6 | no | L put back |
| 0.110 | 0.280 | 45 | 8 / 0 | 16 / 2 | +0.0 | YES | L put back |
| 0.110 | 0.280 | 30 | 10 / 0 | 17 / 4 | +0.0 | YES | L put back |
| 0.110 | 0.280 | 20 | 13 / 0 | 16 / 4 | +0.0 | YES | L put back |
| 0.110 | 0.340 | 45 | 9 / 0 | 14 / 0 | −110.3 | YES | ⛔ BOTH put back |
| 0.110 | 0.340 | 30 | 9 / 0 | 16 / 3 | +0.0 | YES | L put back |
| 0.110 | 0.340 | 20 | 11 / 2 | 15 / 3 | +0.0 | YES | **both clear** |
| 0.110 | 0.400 | 45 | 14 / 0 | 16 / 1 | +0.0 | YES | L put back |
| 0.110 | 0.400 | 30 | 9 / 0 | 17 / 2 | +0.0 | YES | L put back |
| 0.110 | 0.400 | 20 | 9 / 0 | 16 / 2 | +22.7 | no | L put back |

**⭐ 6 of 24 rows may be read for their interleave on their own.** On 18 an arm was put back, and
on two of those (`0.340 / 45`, both sheets) **both** arms were — the −110.3 mm there is the depth
to which two rejected poses overlap, which is not a fact about the mounting.

---

## 3. The pair the spec comment records

> ⛔ **SUPERSEDED by `GRID240_READING_20260802.md` §3a.** At 240 draws both halves of the pair
> **reproduce** on rows that are readable: (0.220, 45) interleaves, (0.400, 20) clears by 17.2 mm.
> The contradiction below was a property of a 24-draw pose pair, not of the mounting. The section
> is kept as written because the reasoning about *readability* is what the rest of this document
> rests on — only its conclusion about the comment is withdrawn.

The comment records **(0.22, 45) as interleaving** at an 88 mm span and **(0.40, 20) as clearing**.

- **(0.22, 45)** — L put back on both sheets. ⇒ **The banked table cannot answer it.**
- **(0.40, 20)** — readable on one sheet only (crown removed): gap **+0.0**, i.e. **not
  separated**. On the crown-0.110 sheet the same point has L put back and is not readable.

⇒ On the single row where the pair's second half is readable, it reads the **opposite** of what the
comment records. ⚠ That is not "the comment is wrong": it is a different pose (see §5), a different
mounting in the crown, and the comment's own measurement conditions are not in front of me.

---

## 4. What "+0.0" means, measured rather than assumed

`arm_pair_min` (`:1311`) returns `mujoco.mj_geomDistance` over arm-geom pairs only, with `None`
rather than the cutoff when nothing is within range. `+0.0` is the most common value in the table,
so what the function does at and past contact was measured directly
(`probe_geomdistance_sign.py`, mujoco 3.10.0):

| centres apart | true gap | returned |
|---|---|---|
| box/box +0.101 | +1.0 mm | +1.000 mm |
| box/box +0.100 | 0.0 | +0.000 |
| box/box +0.090 | −10.0 mm | −10.000 mm |
| box/box +0.050 | −50.0 mm | −50.000 mm |
| **box/box 0.000** | **−100.0 mm** | ⛔ **+0.000** |
| box/box −0.020 | −120.0 mm | −80.000 mm |
| capsule/capsule, whole sweep | −40 … +60 mm | exact |

1. ⭐ **Penetration is resolved**, as a signed negative, for both shapes — so a negative row is a
   real overlap, not a flag.
2. ⛔ **Two boxes at coincident centres return +0.000 for a 100 mm overlap.** So `+0.0` means
   **"not separated"** — touching, or a degenerate total overlap — and must not be written up as
   "touching to within 0.05 mm".
3. ⛔ **A negative number is a minimum-translation depth, not the overlap**: at 120 mm of true
   overlap the function returned 80 mm.

⇒ The **YES / no** verdict is safe in both directions. The millimetre value on a negative row is a
lower bound and should not be quoted as a depth.

---

## 5. ⛔ The asymmetry, and it is the one that matters

The interleave is measured at **one pair of poses** — the chosen one.

- **A "no" row is a witness.** There is a clear L pose, a clear R pose, and *that* pair is
  separated. The existence claim the conjunction wants is sound.
- **A "YES" row is not a refutation.** It says the chosen pair interleaves. With N clear poses on
  one arm and M on the other there are N×M pairs, and exactly one was measured. In the 240-draw
  grid N and M reach the tens, so the fraction measured falls as the sample grows.

⇒ **A failing row does not exclude a mounting.** Making "fail" sound would need the interleave
measured across all clear pairs, not the chosen one. That is not built; it is named here as the
instrument's limit rather than left for a reader to assume the stronger reading.

---

## 6. Limits

1. **One step.** Start pose only; the arms move afterwards.
2. **The counts are a sample.** p5 §31: 24 uniform draws in a six-dimensional joint space. The
   240-draw grid re-measures every point; the marker rule in §1 is independent of the draw count.
3. **17 of the 24 point logs from the 24-draw run are preserved** at `grid_logs_tries24/`, renamed
   from `.log` to `.txt` because `.gitignore:5` (`**/*.log*`) would otherwise drop them — they are
   being kept as evidence, not as run output. The other 7 were overwritten before this was
   noticed. ⚠ Nothing above depends on them — every marker is derived from the table's own two
   count columns — and they are corroboration only.
