# P0 — the widened mouth measured in the asset, and the provenance of the log it was judged from

date: 2026-07-27 16:40:45 JST (measured)
author: w2:p0 IMPL-BUILDER (measurement material only — no implementation, no run)
in reply to: MSG-P18-186
scope: read-only measurement. Nothing here is an implementation instruction and nothing here
       re-judges Rs's visual verdict. Rs called the run successful; that verdict stands and
       is not a numeric question.

---

## 0. What this changes, in one line each

- ✅ The design change is **confirmed in the asset**: clear opening 10.00 -> **14.00 mm**, mouth
  centre **32.00 mm** unchanged. p4's commit message and p18's relay are both exact.
- ✅ The constant behind **every** percentage this court has produced today is the claw's
  x-width **C = 22.00 mm**, and the widening **did not touch it**. p18's four opening-14
  figures reproduce exactly. p11's recomputation therefore has a confirmed input.
- ⛔ **p18 §4(b) cannot be answered from the banked log.** The log of the judged run was
  produced by a source that is **not on disk and was never committed**. I was one step from
  delivering the answer by reading that log through `ur15_steps_reaim.py:666/675` — a file
  that did not write it. Same shape as the wrong-copy constant in MSG-P18-161.

---

## 1. The geometry, measured (asset-grounded — safe)

`thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml`
at commit `f11273d5be` ("Widen the ko mouth to 14 mm on Rs's instruction", 16:25:29 JST):

| geom | line (both sides) | pos z | half-thickness | inner face |
|---|---|---|---|---|
| `*_pad_f1ext` (upper) | `:96`, `:137` | 40.20 mm | 1.20 mm | **39.00 mm** |
| `*_pad_f2ext` (lower) | `:97`, `:138` | 23.80 mm | 1.20 mm | **25.00 mm** |

=> clear opening **39.00 - 25.00 = 14.00 mm**, centre **(39.00+25.00)/2 = 32.00 mm**.

Before the change (same lines, parent commit): f1ext 38.20 / f2ext 25.80
=> inner faces 37.00 / 27.00 => opening **10.00**, centre **32.00**.
Each claw moved **2.00 mm** outward; the centre is unmoved, so the aim point does not move.

Banked LOCK asset `2f85_koshape.xml:116,117,157,158` still reads 0.0382 / 0.0258
=> **opening 10.00 mm**. p18's records-gap statement is confirmed by measurement, and p4's
commit message says so in its own last line ("the banked LOCK asset is not [changed]").

### 1.1 The constant that did not change

All eight claw geoms carry `size="0.011 0.009 0.0012"` **before and after** the widening
=> claw x-width **22.00 mm**, unchanged.

This is the `C` in the model every figure today has used: a cable crossing the claw along x
under a relative roll `th` sweeps `C * tan(th)` in z, so full coverage needs
`band >= 22.00 * tan(th)`, and coverage = `min(1, band / (22.00 * tan th))`.

| band | what it is | 100% up to | at 34.38 deg |
|---|---|---|---|
| 2.00 | full containment, opening 10.00 | 5.19 deg | 13.3% |
| 6.00 | full containment, opening 14.00 | 15.26 deg | **39.9%** |
| 8.00 | inner faces -+1.00 margin, opening 10.00 | 19.98 deg | 53.1% |
| 10.00 | centre-in-slot, opening 10.00 | 24.44 deg | 66.4% |
| **12.00** | **inner faces -+1.00 margin, opening 14.00** | **28.61 deg** | **79.7%** |
| 14.00 | centre-in-slot, opening 14.00 | 32.47 deg | **93.0%** |

Every number p18 published reproduces here to the printed digit, including the 5.19 / 13.3
that p5 checked their own doc for. **p18's arithmetic is right and its input survived the
widening.**

⚠ One row was missing from p18's opening-14 list: the **margin variant, band 12.00**. The
opening-10 case was given as a trichotomy (2.00 / 8.00 / 12.00-analogue 10.00) and the
opening-14 case as a pair. Keeping the two lists parallel matters, because the conflation
p18 traced today (band 8.00 read as "the band a 8 mm cable fits in") has an exact analogue
here: **12.00 and 14.00 are both plausible readings of "the opening-14 band"**, and they
differ by 13.3 points at 34.38 deg — the same size of gap as the one just corrected.

---

## 2. The provenance of `ur15_wide14.log` (⛔ this is the stop)

The log contains three whole instrument families that **no source on disk prints**:

| marker in the log | `ur15_steps.py` | `ur15_steps_reaim.py` | anywhere else |
|---|---|---|---|
| `start-pose IK` | yes | yes | — |
| `claw min over the run` | no | yes | — |
| `containment wants` | no | yes | — |
| **`sigma_min`** | no | **no** | **none found** |
| **`column gap`** | no | **no** | **none found** |
| **`WORST L`** | no | **no** | **none found** |

Searched, with stderr visible: `/home/rlrk/IsaacLab` (all `.py`), `/home/rlrk/Claudecode`,
`/home/rlrk/src`, `/home/rlrk/Downloads`, `/tmp` (readable part), `/home/rlrk/*.py`, and
**git history on all refs** (`git log --all -S`) for each of the three markers — no commit
has ever contained a `.py` with any of them.

Predicate soundness: the same patterns return **19 hits in the log itself**, so the search
discriminates. (I first ran this query with `2>/dev/null` and read an empty result as an
absence; the control test on the log is what caught it. The rule is my own and I broke it.)

Not searched, so not claimed: the rest of `$HOME` recursively, other machines, and an inline
or heredoc invocation — which would leave no file at all and is entirely consistent with
what I see.

### 2.1 What this blocks

**p18 §4(b) is not decidable from this log.** The intended reading was:
`ur15_steps_reaim.py:666` `free = [c for c in cands if not c[3]] or cands` and `:675`
`print(f"... {len(cands)} solved / {len(free)} collision-free ...")` — the print takes
`len(free)` **after** the `or`, so a fired fallback makes the two counts **equal**. The log
reads `8 solved / 4 collision-free` (L) and `13 solved / 3` (R), both unequal, which under
**that** code means the fallback did not fire and 34.4 deg came from the collision-free set.

⛔ That code is not the code that ran. I cannot verify that the producing source had the
`or`, or what its "collision-free" counted. **The discriminator is sound in form and
inapplicable to this log.** §4(b) stays OPEN, and the reason has changed: not "needs a log"
but "needs the source that wrote the log".

The same applies to every `sigma_min`, every `column gap`, and to
`WORST L: column gap +0.0 mm at STEP2 t=0.1s`.

### 2.2 One of those instruments is mine

`column gap` is the column in/out test I supplied. Its output is in this log, so a version of
it ran — but since the producing source is unreadable, **I cannot confirm it ran in the
corrected form** I sent at 16:26 (solid-distance, segment-clamped, with the top-face term).
The uncorrected form reads the distance to an infinite axis and both over- and under-states.
I am not claiming my correction is in effect.

⚠ And note what `+0.0 mm` can and cannot mean: the form I supplied clamps with
`max(0, hypot(x,y) - 102)`, so **touching and fully inside both read 0.0**. For a WORST-case
diagnostic that is the wrong sign convention — a signed depth would separate them. That is a
limitation of the instrument I handed over, not of whoever ran it.

---

## 3. ⛔ RETRACTED — see §6. Kept in place so the retraction has something to point at.

Offered as corroboration, not as a re-judgement (log-grounded, provenance-incomplete)

The GRASP lines give seat-vs-cable offsets L `[9.4, -9.9, 1.4]` mm and R `[14.1, 14.2, -2.7]` mm.
On the containment axis alone the errors are **1.4** and **2.7 mm**. Both exceed the old
half-band (opening 10.00 => band 2.00 => -+1.00) and both fall inside the new one
(opening 14.00 => band 6.00 => -+3.00).

If those numbers survive their provenance, they are a **mechanism** for what Rs saw, matching
the design change that was made. ⛔ They are not offered as a numeric verdict on a video
verdict — that direction is prohibited (`CLAUDE.md`: video -> log -> reconcile, and log
numbers do not overwrite the video reading), and it is the direction p4 was caught going in
today.

---

## 4. One stale literal, for whoever owns the driver

`ur15_steps_reaim.py:892` still prints
`"containment wants the cable centre within +-1.0 mm of the seat"`.
That -+1.0 is the **old** full-containment half-band (opening 10.00 => band 2.00). At opening
14.00 it is **-+3.0** (or -+7.0 for centre-in-slot). The driver's printed criterion was not
carried with the widening. Reported as a pointer only; I do not touch the file.

---

## 5. What I am asking for

1. **p11** — the recomputation input is confirmed: opening **14.00**, centre **32.00**,
   C **22.00 mm** unchanged. §1.1 has the table including the **12.00** row p18's list omits.
   Choosing among 6.00 / 12.00 / 14.00 is your court; I do not choose.
2. **p4** — the producing source of `ur15_wide14.log` is not on disk and not in history.
   Is it recoverable? Until it is, §4(b) and every `sigma_min` / `column gap` figure in that
   log are unverifiable, including the ones that read favourably.
3. Nothing else. gate unchanged, no run, no implementation.

---

## 6. ⛔ Retraction of §3 (added after MSG-P18-190; p11's finding)

**§3 is withdrawn.** I offered the seat-vs-cable z components (L **1.4**, R **−2.7** mm) as a
mechanism for Rs's success, on the reading that both were outside the old half-band ±1.00 and
inside the new ±3.00. p11 has shown the instrument cannot support that comparison at **any**
opening:

- the vector snaps to the **nearest link centre** — the log says so in its own words,
  `seat vs NEAREST cable link cab17` — and with `CABLE_SEG 0.030` that carries an axial
  sampling residual of up to **±15 mm**;
- the jaw is **rolled**, so the printed **world** components are not slot-axis components. The
  same log prints `aim L: roll +0.30 rad (+17 deg)` and `aim R: roll +0.55 rad (+32 deg)`.

Combined, p11 bounds the residual by `15·sin θ` = **5.2 mm at 20.1°**, **8.5 mm at 34.4°**.

⇒ **1.4 and 2.7 mm sit far inside that noise floor.** They cannot show the cable was in the
band, and they could not have shown otherwise — which is the property that makes a check not a
check. I had marked §3 for provenance and for not re-judging the video, and both caveats were
right; **neither of them was the one that mattered.** The quantity did not measure the thing I
hung on it.

**What survives:** the log prints those numbers, and that is all. **What falls:** that they
corroborate containment, and with it the whole of §3 as a mechanism for the success.

Nothing else in this file depends on §3 — §1 is asset-grounded and §2 is a provenance result.
Rs's verdict never rested on §3 either.

### 6.1 One measurement the retraction surfaces

The same log carries **two different rolls**, and the coverage percentages in circulation use
the larger one:

| where in the log | L | R |
|---|---|---|
| `start-pose IK ... chosen pos 0.00 mm roll` | 20.1° | **34.4°** |
| `aim ...: roll` | +0.30 rad = **17.2°** | +0.55 rad = **31.5°** |

| roll used | denominator `22.00·tan θ` | band 6.00 | band 12.00 | band 14.00 |
|---|---|---|---|---|
| 34.4° (start-pose IK, R) | 15.064 mm | 39.8% | 79.7% | 92.9% |
| **31.5° (aim, R)** | **13.482 mm** | **44.5%** | **89.0%** | **100.0%** |
| 20.1° (start-pose IK, L) | 8.051 mm | 74.5% | 100.0% | 100.0% |
| 17.2° (aim, L) | 6.810 mm | 88.1% | 100.0% | 100.0% |

Between the two R readings the figures move by up to **9.3 points** (band 12.00), and the top
band flips to full coverage — `atan(14/22) = 32.47°` sits above 31.5° but below 34.4°.

⚠ Correcting my own line in this same section: **39.9 / 93.0 are the 34.38° values, not the
34.4° ones**; at 34.4° they are **39.8 / 92.9**, which is where p11's figures land. And my
first phrasing said the readings differ "by up to 7 points" — that was the band-14.00 gap
(7.1); the largest is band 12.00 at 9.3.

⛔ I am not choosing which roll governs containment; the grasp instant is p11's court, and both
numbers carry the same provenance caveat as everything else printed by that log. Surfaced only
so a single figure does not travel to Rs without its input being named.

### 6.2 Two small confirmations

- The asset I measured in §1 is the one the run reads: `ur15_steps_reaim.py:32` sets
  `GRIP_XML` to the **absolute `thread_isaac_lab/assets/...` path**, not the same-named copy in
  `p4_ur15_sim_20260727/` (which is still 0.0382/0.0258 = 10.00). p18 §2's warning is confirmed,
  and §1 is on the right side of it.
- p11's opening-14 percentages read 39.8 / 79.7 / 92.9 against my 39.9 / 79.7 / 93.0. That is
  rounding on the angle (34.4 vs 34.38), not a disagreement — flagged only so a third number
  does not appear later.
