# p18 evidence ledger — the clamp court, 2026-07-27

**Author:** `w2:p18` T-ROOT-OPS-SUPERVISOR (routing / evidence gate).
**Court:** `w2:p4` (measurement) · `w2:p11` (predicate) · `w2:pZ` (instrument) · `w2:p0` (asset geometry) · `w2:p5` (design).
⛔ **This file takes no design position, flips no gate, authorises no run, and issues no verdict.** It records
what died today, what replaced it, and the one thing still unexplained.

## 1. The visual leg landed — and it does not say what it looks like it says

`w2:pC` returned an independent visual leg on the video Rs sent directly. p18 opened and read the artifact and
re-computed its pin (match).

| | |
|---|---|
| path | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/UR15_RSDIRECT_VIDEO_LEG_pC_20260727.md` |
| content sha256 | `07a64b9a9c58b1523a28e3286ae144e4ecebf256718c8a736b892af068242191` |
| commit | `b6a1641ba4f50190bb41a84df224b77674b3158a` |
| subject | `/home/rlrk/Downloads/ur15_steps.mp4`, pC-measured sha256 `9bacb624…` = the pin in the request |

**Observation (pC `:53`):** across 18 sampled times, both arms, **no cable between the red and blue plates —
the opening.** The cable runs outside the claws, mostly below. Decisive at f600 (t = 20.00 s): two viewpoints,
both jaws, plates separated with empty space between (pC `:55`). Closest approach f300–f360: cable below the red
plate (pC `:56`). ⚠ f360 alone splits between viewpoints and is not decided by a single view — but **no viewpoint
reads as "in the opening"** (pC `:57`).

⛔ **pC issues no verdict** (Rs exclusive) and **does not identify which run this is** — it measured only that it
is *a different run* from the video banked earlier today (per-frame pixel diff: f0 mean 0.518 vs f300 12.943 /
f600 11.513, pC `:26-30`). ⇒ **Do not attach this observation to a particular ctrl value or configuration.**
⚠ Sampling is 18 of 1029 frames, pC's own stated limit (`:69`).

## 2. ⛔⛔ Scope — the no-window mechanism was not exercised in this run

Our no-window result asks: *given a cable in the opening, can the jaw compress it?* Answer: no — the opposing
claws touch at ctrl 219.16 (backplate 10.16 mm), 5.6 counts before the backplate could reach the cable at
ctrl 224.78.

**In this video the cable is never in the opening at all.** ⇒ ⭐ **The closing geometry never got the chance to
fail.** This is a *different* failure, upstream of ours — approach / positioning. pC's own option table says the
same in its own terms: (b) whether the cable is being *pushed* is not separable from video alone (pC `:64`).

⇒ ⛔ **Do not read this video as confirmation of the no-window finding.**
⇒ ⭐ And symmetrically: **the no-window finding does not depend on this video.** It stands on geometry plus two
readings that are both pre-saturation. The two results are independent, and each keeps its own grounds.

## 3. ⭐⭐ Two different "about 10 mm" are circulating on orthogonal axes

Raised by `w2:pC` from the asset (`:44-47`), recorded here because it spans every pane's numbers:

| | value | axis |
|---|---|---|
| (a) コ opening, clear gap | **10.00 mm** | pad-local **z** (up/down) — red `*_pad_f1ext` z = 0.0382, blue `*_pad_f2ext` z = 0.0258 |
| (b) backplate separation at claw zero-crossing | **10.11–10.16 mm** | jaw **closing axis (y)** — `right_pad` ↔ `left_pad` |

⇒ ⛔ **Orthogonal. Never put them in one column.** Same shape as `w2:pB`'s earlier catch (24.0 mm body-origin
separation vs −1.3 mm geom-face separation): two quantities that can both be true because they measure
different things.

## 4. Retraction ledger

**Origin: `w2:p4`'s saturation measurement.** The claw-distance channel floors out, so the old −2.57 was never an
achieved depth. `w2:p0` fixed the bound exactly from the asset: claw box **22.00 × 18.00 × 2.400 mm**, and box
penetration depth is the **minimum overlap across separating axes** ⇒ once the y overlap passes the plate
thickness, escaping in z is shorter ⇒ **the reading cannot exceed 2.400 mm**, however far the jaw closes.

| pane | retracted |
|---|---|
| `w2:p5` | the cable-stop hypothesis **and** its dependent values (backplate 7.59 / compression 0.41 mm) |
| `w2:pZ` | `-092 C` (jaw stopped by the cable) **and its own replacement instrument** `-088 D(3)`, which read in the same saturated region |
| `w2:p11` | the fit, and the third line of its internal-consistency argument (an extrapolation into the saturated band) |
| `w2:p18` (me) | "the measured 1.57° tilt makes the 3.43 mm a measured quantity" — **I never did that calculation** |

⭐ `w2:p4`'s summary is the accurate one: **3.43 mm was never a quantity requiring explanation** — it was the
difference between a saturated reading and an unsaturated extrapolation.

⭐ `w2:p11`'s general form, recorded because it indicts the agreement rather than the arithmetic:
**independent convergence is not corroboration when everyone is fitting the same free parameter to the same one
broken datum. The question is not how many agreed — it is whether the fit could have come out otherwise.**
p11 also self-reported the sharpest case: it solved 7.59 from the datum, then reported that 7.59 − 10.16 = −2.56
"agrees with −2.57 to 0.01 mm". A one-parameter fit to one number **cannot** produce another residual.

## 5. ⛔ WITHDRAWN AT SOURCE — there was never an excess to explain

**Superseded within the hour.** `w2:p0` retracted its own bound: it computed the 2.400 mm cap **for parallel
boxes**, and the pads are not parallel. For two claw boxes at relative angle *a*, the thin-axis overlap is
`h_z + (h_y·|sin a| + h_z·|cos a|)` — and `h_y` is the **18.0 mm** dimension, so it dominates as soon as *a* ≠ 0.

| relative tilt | floor |
|---|---|
| 0° (parallel) | **2.4000 mm** |
| 1.571° | **2.6463 mm** |
| 3.142° | **2.8915 mm** |

⇒ ⭐ **The old datum −2.57 sits *inside* the bound under either tilt convention** (0.076 mm or 0.321 mm of
margin). ⇒ ⛔ **The 0.170 mm "excess" was an artefact of the parallel assumption, not a fact about the build.**

⇒ **2.400 is a lower bound, not an upper one** — the value at zero tilt. `w2:pZ` reached this independently and
first, by actually computing the tilted case (15 separating axes collapsing to 3 because the boxes' x axes are
parallel) and — as p0 notes — was **doubly right: it computed the tilted floor and declined to claim fit.**
p0 states its own error type plainly: *"I said 'exactly' about a bound that was not exact"*, and that it is the
**second instance of the same shape today**.

⇒ ⭐ **Disposition (p18, with p0 and pZ concurring that it is this court's to make): the item is CLOSED as
withdrawn — not as explained.** The difference matters: nobody explained a 0.17 mm discrepancy; the quantity it
was a discrepancy *from* was wrong.

### 5a. What actually remains — two much narrower things

1. **The tilt convention (θ vs 2θ) is undetermined.** p0: the two conventions differ by whether the 180° z-mirror
   and the two pads' tilt directions compound, *"and geometry alone does not decide it for me"*. ⛔ **It does not
   need deciding for the disposition above** — both conventions clear the datum. `w2:p11` and `w2:pZ`
   independently converged on the same one-shot reading that would settle it: **read the two claw geoms' relative
   orientation at ctrl 235 directly** (the f1/f2 difference cannot carry it — that band is saturated).
   ⚠ No new run required. Left in `w2:p4` / `w2:p0`'s court; p18 requests nothing.
2. ⛔ **The instrument's own contract is unverified, and it sits under all four formulas.** `w2:pZ` disclosed it:
   the claim that `mj_geomDistance` returns the SAT minimum-translation depth on penetration is **its assumption
   about MuJoCo's implementation, not read from source or docs**. ⇒ If that is wrong, every floor formula above
   is moot. ⭐ This is pZ's own rule — *verify the instrument can represent the value before explaining a
   discrepancy* — applied one level up, to the instrument's contract rather than its range.

### 5c. ⭐⭐ SUPERSEDES 5a — both remaining items closed by measurement, within the hour

**(1) The instrument's contract is no longer an assumption.** `w2:p5` probed it directly in mujoco 3.8.1 with two
synthetic boxes of the claws' dimensions (⛔ **not a THREAD run** — no asset, harness, GPU or gate; it needed no
run authorisation and asked for none):

| y overlap | returned | `fromto` direction |
|---|---|---|
| 0.50 / 1.00 / 2.00 mm | **−0.50 / −1.00 / −2.00** | **y** |
| 3.00 / 5.00 / 5.93 / 7.42 mm | **−2.400 every time** | **z (+2.40)** |

⇒ ⭐ **Minimum-translation semantics confirmed, and the y→z switch happens exactly at the plate thickness —
visible in the instrument's own output.** ⇒ `w2:pZ`'s premise (3), the item I had put at the top of the stack,
is **measured**. ⚠ Both p5 and `w2:p0` first read the docs and found the same single sentence
(`mujoco.h:628`, identical in the Python `__doc__`): *"Return smallest signed distance between two geoms…"* —
⛔ **the penetration case is documented nowhere.** The reservation was justified; it is now discharged by probe,
not by doc.

**(2) The two families are discriminated, on synthetic boxes, before touching p4's data.** At θ = 1.571° per
plate:

| overlap | probe returned | family II predicts | family I predicts |
|---|---|---|---|
| 2.93 | −2.478 | −2.480 | −2.893 |
| 3.68 | −2.499 | −2.501 | −2.893 |
| 5.93 | −2.561 | −2.563 | −2.893 |
| 7.42 | −2.601 | −2.603 | −2.893 |

⇒ ⭐ **Family II matches to 0.002 mm; family I is out by 0.29–0.33 mm.** ⛔ The floor is **not constant** once
tilted — it grows with overlap. ⚠ p5 notes the 0.002 mm residual is same-sign and same-size on every row ⇒ a
second-order term remains, and p5 claims nothing finer than 0.002 mm.

**(3) The tilt convention is settled, and two independent derivations agree.** `w2:p0` derived it from the asset
kinematics: the left chain's `left_driver:128` / `left_spring_link:142` carry `quat 0 0 0 1` (180° about z) while
every joint has `axis 1 0 0`, and `equality:200` couples them 1:1 ⇒ equal joint angles rotate the two pads
**oppositely** about world x ⇒ **relative angle = 2θ**, θ being the per-plate angle. p5's probe was parametrized
the same way (A at −θ, B at +θ) and what fitted was `t + overlap × radians(θ)` — **half the relative angle**.
⇒ ⭐ **The two agree: relative = 2 × per-plate, and p4's 1.571° is a per-plate angle**, so p5's use of it was
convention-correct. (The forms coincide: `(overlap/2)·sin 2θ ≈ overlap·θ` at these angles.)

⇒ ⭐⭐ **Refined disposition (p18).** The two propositions are different and both are now settled, in opposite
directions — recording them separately, not collapsing them:

- **"There was a 0.17 mm excess over an upper bound" — WITHDRAWN.** The bound was miscomputed. Nothing explains
  an excess that did not exist, and no account should be written as if something did.
- **"What is the datum −2.57?" — EXPLAINED.** It is the moving floor at overlap 5.923 (predicted 2.561–2.563,
  0.007–0.009 mm from the datum), and the explanation was tested against a probe of the instrument that
  **could have refuted it and did not**.

⛔ **What is still not established, and must travel with the above:** p5's probe used **synthetic boxes**, not
the real pads (which also carry `pad1`/`pad2`, and whose tilt comes from the four-bar linkage); **p4's 1.571°
itself was not validated** by the probe; and the probe covers **mujoco 3.8.1 with default flags only**
(`nativeccd` and friends untested). ⇒ **Applying this to p4's sweep still requires p4's recomputation from raw.**

### 5d. Both of §5c's forward-looking notes were answered within minutes — one of them by being refuted

**(1) The upgrade coupling is discharged: the contract is version-neutral.** I flagged that the queued
mujoco 3.8.1 → 3.10.0 move would pull the library out from under these numbers. `w2:p5` did not wait for the
upgrade — a staging env (`env_isaaclab7_latest`, mujoco **3.10.0**) already exists, so it re-ran the same probe
there: **15/15 points identical to 3.8.1** (5 parallel, 4 tilted, 6 deep-overlap). Overlap 5.93 → **−2.561** on
both; parallel ≥ 3.00 → **−2.400** on both.
⇒ ⭐ **The env7 upgrade is neutral with respect to this instrument's contract.**
⚠ Scope, stated by p5 and preserved: this measured **only** `mj_geomDistance`'s box-box penetration semantics.
⛔ **Solver behaviour, contact, and run reproducibility were not measured** — those are separate axes and still
need a post-upgrade smoke.

**(2) ⛔⛔ The "free second path" I relayed does not discriminate. Cause side: p18.**
I recorded, and dispatched in `-114 (7)`, that if p4's sweep had points above ctrl 239 whose floor exceeded the
θ-convention value 2.6463, the θ reading would be refuted. **There is no ceiling.** p5 measured past the
half-width (θ = 1.571°/plate):

| overlap (mm) | 8.00 | 9.00 | 10.00 | 12.00 | 14.00 | 16.00 |
|---|---|---|---|---|---|---|
| returned | −2.617 | −2.645 | −2.672 | −2.727 | −2.782 | −2.837 |

⛔ **My reasoning here was wrong, and `w2:p11` returned it with the arithmetic. Same verdict, different reason.**
I wrote that 2.6463 is crossed at overlap ≈ 9.0 mm "under the θ convention itself". That crossing happens under
the **per-plate** reading (1.571° per plate ⇒ 0.02742 rad), **not** under the relative reading the cap belongs to.
Under the relative reading (per-plate 0.7855°) the floor at overlap 9.053 is **2.524**, and 2.6463 is reached only
at **overlap 18.0 mm — full overlap, backplate −7.89 mm, i.e. the plates passing through each other.**
⇒ I compared the two conventions using **different formulas** — family I's constant arm for one and family II for
the other. p0's original cap was a family-I number; what survived was family II.

⇒ ⭐ **The path is still void, for two better reasons:**
1. **The cap is unreachable under its own convention** — it needs the plates to interpenetrate completely.
2. ⭐⭐ **The existing four points already decide it.** The two conventions differ by a factor of two in the tilt
   term **at every overlap**, so no threshold is needed:

| overlap | relative-reading predicts | per-plate reading predicts | measured |
|---|---|---|---|
| 2.932 | 2.440 | **2.479** | 2.47 |
| 3.680 | 2.450 | **2.499** | 2.49 |
| 5.923 | 2.481 | **2.561** | 2.56 |
| 7.418 | 2.501 | **2.601** | 2.61 |

⇒ **The convention was settled before anyone proposed a test for it.** No sweep extension, no threshold.

⭐ p11's own diagnosis of its part is the sharper general form, and it is not the one I had been repeating:
**it computed how many counts would make the test usable, when the question was whether the test was already
answered.** ⇒ Not only *"could this come out otherwise?"* but *"has it already come out?"*

⛔ And `w2:p0` declined my apportionment of the blame, with a diagnosis sharper than mine: it used, as its
discriminator, **a number from the model it had refuted in the adjacent section** — its own table says "family I:
refuted as an explanation" one paragraph above where its value is installed as a threshold. ⇒ *A refuted model's
numbers are wreckage, not thresholds.*
⚠ `w2:p0` offered it as its own kinematic reading and marked it as such; **I am the one who wrote it into the
ledger as an open path without asking whether it could come out either way.** That is the same failure I had
already recorded three times today, committed while writing the record of it.

⭐ **Why it fails, which also sharpens p0's residual claim (p18's arithmetic, marked as mine):** family I is
family II evaluated at **overlap = half-width**. `2.400 + 9.0 × 0.0274 = 2.6466` ≈ p5's measured −2.645 at
overlap 9.00. ⇒ family I is the **full-overlap limit** of family II, exactly as `w2:p11` said when it retracted.
⇒ ⛔ So p0's "refuted as an explanation, **intact as a bound**" holds **only while overlap < 9.0 mm**. It bounded
the four measured points because their overlaps were 2.93–7.42 mm; it is **not** a bound in general.

**(3) `w2:p5` also refines its own instrument rule, in the generous direction.** Past the floor the claw channel
is **not invalid — its gain drops and becomes tilt-dependent**: below the floor, reading = overlap (gain 1);
above it, reading = thickness + overlap·sin θ (gain 0.0274, about 1/36). ⛔ Inverting it needs **θ at that
configuration**, which is the hardest quantity to obtain. ⇒ The practical recommendation is unchanged:
**backplate separation is the primary instrument.**

⭐ p5 adds one more thing worth keeping: the linear form holds across overlap **2.93 → 16.0 mm (a 5× span)** with
the residual constant at 0.002 mm. ⇒ **Not a local fit.**

### 5e. Which results the upgrade can touch — two panes cut it the same way, and the cut is the useful artefact

`w2:p0` and `w2:p11` independently partitioned their own results by **version-dependence**, before knowing p5
had already tested the upgrade. The partitions agree:

| bucket | contents | lifetime |
|---|---|---|
| **asset geometry** | claw protrusion 5.00, slot [27.00, 37.00], link arms 51.72 / 39.32 / 41.64 / 22.90 | ⭐ survives version changes |
| **model + solver state** | ctrl→backplate gap, claw zero-crossing 219.16, stopping point 10.16 | ⚠ worth re-confirming |
| **instrument contract** | `mj_geomDistance` penetration semantics | ⛔ dies with the version — *by definition* |
| **derived from the contract** | the floor formula's validity (family II) | ⛔ falls with the bucket above |

⭐ **`w2:p11`'s general form, which is the reusable part:** *a number measured from the asset and a number measured
from the instrument have different lifetimes across a version change — the first outlives it, the second dies
with it. Bank a number without saying which kind it is, and after an upgrade nobody can tell what to discard.*

⭐ **`w2:p0`'s application of it is the load-bearing one for this court:** the **no-window ordering conclusion does
not rest on the contract at all.** Its §2 bound is a claim about *where the distance reaches zero* — no
penetration, so no SAT question arises — as are the zero-crossing, the deep pairs, the pair differences, and the
ctrl 219–225 band. ⇒ **The upgrade cannot reopen the no-window result.** Only the floors and caps (§7–§9) sit on
the contract.

⇒ ⭐ **And p5's staging probe empties the third bucket empirically:** the contract is identical on 3.10.0
(15/15). So the bucket that "dies by definition" **did not die in fact** — which is exactly why it had to be
measured rather than reasoned about. ⚠ Both p0 and p11 wrote before seeing that result; p18 relayed it.

⚠ **Bound claims need their range attached — but only one of the two things called "bound" here.**
`w2:p0` kept its family-I values as bounds; by p18's arithmetic on p5's series the θ value 2.6463 is crossed at
overlap ≈ 9.0 mm and the 2θ value 2.8915 at ≈ 18.0 mm (p0 recomputed independently: 9.07 and 17.98 at
0.0275 mm per mm of overlap). ⇒ Neither is a bound in general.

⛔ **Scope correction, from p0: this restriction reaches only the floor bound, not the contact bound.** Two
different objects were both being called "bound":

| | what it is | depends on the contract? |
|---|---|---|
| **contact bound** (p0 §2) | backplate gap **8.188 mm** at which the claws first touch — pure geometry, **first contact so no penetration exists** | ⛔ **no** |
| **floor bound** (§7–§10) | the reported penetration depth 2.6463 / 2.8915 — never reached, band-limited | ⭐ yes |

⇒ ⭐ My range caveat applies to the second only. **The contact bound — and with it the no-window ordering — is
untouched by it, and untouched by the version question.**

⛔ **`w2:p11` computed exactly the number that voids the second path, and read it as enabling the path.**
p11 finds the floor reaches 2.6463 at overlap 9.053 mm ⇒ backplate 1.057 ⇒ **ctrl ≈ 243.4**, notes p4's sweep
stops at 240, and concludes the test is *available* with ~3.4 more counts. ⇒ But that computation **is** the
refutation: under the θ convention the floor **exceeds 2.6463 by construction** past overlap 9.05, so an excess
is what θ *predicts*, not what refutes it. ⇒ ⭐ p11's arithmetic is right and its reading inverts. ⛔ The path
stays void; no sweep extension would rescue it. (p11 wrote at 14:00:52, p5's measurement landed 14:00:38.)

⭐ **`w2:p0` retracted the same misattribution I did** — that p11's tilt label had slipped — and names how it
arrived there: *"I attributed to p11 an error p11 had not made, in the course of agreeing with p11's number."*
⇒ Two panes made the identical error about the same third pane while endorsing its result.

⭐ **`w2:p0` also declined to widen its own retraction, correctly:** p5's probe confirms −2.400 exactly for
parallel boxes, so **the number was right**; the error was applying it as a cap to pads that are not parallel.
⇒ Retract the false clause, keep the true one.

### 5b. The discriminator that did the work

The four formulas are **not the same formula**. They split into two families with different predictions:

| family | tilt term scales with | predicts |
|---|---|---|
| `w2:p11` / `w2:pZ` / `w2:p0` | **half-width** (9.0 mm, constant) | floor is **constant** once tilted |
| `w2:p5` | **actual y overlap** (varies with ctrl) | floor **grows** as the jaw closes |

⭐ `w2:p5` measured the series and the floor **grows monotonically**: ctrl 227 → −2.47, 229 → −2.49,
235 → −2.56, 239 → −2.61. ⇒ **The data discriminates, and it favours the overlap-scaled form.** p5's fit to
those four points lands within 0.001–0.011 mm using **no free parameter** (thickness from the asset, tilt from
p4's independent measurement, overlap from the offset relation) — which is the exact opposite of the identity
`w2:p11` warned about in §4: this one **could** have failed and did not.

⚠ p5 states its own limits and p18 preserves them: p5 worked from **p18's relayed numbers, not p4's raw**, so a
recomputation from raw is required; and p5 claims **the form, not the coefficient**. ⛔ p18 adds no number here.

⛔ **Correction (p18) — I misattributed the cause of `w2:p11`'s +0.32 mm miss, in dispatch `-110`.** I wrote that
p11 mistook the tilt convention. p11 returned it and is right: it used 1.571° **as the per-plate angle and
doubled it inside its own formula**, so its 2.891 sits on p0's 3.142° row — **convention-correct**. Its miss came
from **using a constant arm (half-width) where the actual overlap belongs**. ⚠ And p0's kinematic derivation puts
2θ on the asset-supported side, so **p11's number was the better-founded of the two**; what failed was the shape
of the formula, not its angle. ⭐ p11 then recomputed p5's form independently — zero free parameters, all four
points within 0.01 mm — and **retracted its own formula in favour of it**.

⭐ Both `w2:p11` and `w2:p0` draw the same contrast, and it is the day's most useful one: p11's earlier
cable-present fit put **one free parameter on one number and could not come out otherwise**; this form puts
**zero free parameters on four numbers** and then survived a synthetic-box probe built to break it.
**Same word "agreement", different epistemic objects.** p0 marks its own position precisely: its formula is
**refuted as an explanation, intact as a bound** — all four points lie under its 2.6463 / 2.8915 caps.

## 9. Custody — `w2:pZ` left this court on Rs's direct instruction, and three corrections would have evaporated

Rs directly instructed `w2:pZ` (2026-07-27 13:4x, option A) to leave the clamp-geometry court and return to its
brief: independent verification of `w2:p0`'s implementation
(`VERIFIER_ROLE_BRIEF_pZ_20260721.md` @ `4714493e64` `:1`, `:22`, `:43`). ⇒ pZ will not answer this court again.

⛔ **pZ flagged that three of its corrections exist only inline in messages `-088 D` / `-090 C` / `-094 C`, with
no persistent artifact.** Recording them is what this ledger is for, so they are captured here verbatim in
substance — ⛔ **as pZ's positions, not adopted by p18, and not adjudicated:**

1. **The claw-penetration boolean is true on every pass ⇒ zero discriminating power.** ⇒ It should not be a
   per-run finding at all, but be raised to a **constant design-level caveat**.
2. **The "C leg" (backplate-to-cable contact) is structurally unsatisfiable on the capture branch** — at the real
   stopping point there is clearance, so the cable touches nothing.
3. **Per-run primary instrument = backplate-to-backplate** (`pad1` × `pad1`, does not saturate); the claw
   quantity is **derived**; and if true deep-interference depth is needed, **use position readings, not distance
   queries**.

## 10. ⛔ CLAMP-1's acceptance predicate is now ownerless

pZ's departure leaves the acceptance predicate at **v0.3a, unsettled**, with the three corrections above
**unreflected**. pZ names the assignment as **Rs's / p18's court**. ⇒ p18 records it as an open assignment and
takes no design position on the predicate's content.

Still undecided inside it, unchanged: **grasp-basis vs capture-basis** (`w2:p11`'s position is capture-basis;
final is Rs) and **the §0 DUAL-ARM composition rule** (both arms, or a designated arm — Rs).

#### 10d. ⭐⭐ `w2:p11` specified the predicate's shape — three legs, each naming its own surface

Its court, its ruling; implementation is `w2:p0`'s. p18 checked the cited constants against the files itself
(`task_config.py:137` `CABLE_RADIUS = 0.004` ⇒ Ø8; `:277` verbatim `gap=4mm … 2mm/side compression` ⇒ 4.0 mm),
and the containment arithmetic (slot [27.00, 37.00], Ø8 fully inside ⇒ centre in [31.00, 33.00]).

| leg | condition | axis | source |
|---|---|---|---|
| **L1 containment** | cable centre within pad-local **[31.00, 33.00]** | **z** | ⭐ the quantity the driver **already computes and prints** (`:856-857`, ±1.0 band) |
| **L2 compression** | `pad1` face separation within **[4.0, 8.0] mm** | **y** | 8.0 = Ø8 (`:137`); 4.0 = design full-close (`:277`) |
| **L3 contact identity** | ⛔ the contact must be **on the faces L2 measures** — both `*_pad1` ↔ cable | — | **the missing leg; this is what made R True** |

⚠ p11 adds that L2 must be evaluated **at the cable's z**, not as the box-pair minimum (they differ by 0.30 mm =
30% of the positioning tolerance).

⭐⭐ **The structural lesson, and it generalises past this predicate:** *legs that speak about the same physical
event must be required to speak about the same surface.* "Contact occurred" and "face separation is X" can point
at **different events** unless the surfaces are bound together.

⭐ **L3 is not an addition — it is what Rs's own mechanism requires.** Rs: 「**左右で摩擦が生じれば**」 ⇒ the
friction-bearing surface *is* the backplate. ⇒ And once L3 is in, §10c's observation (only L could satisfy Rs's
mechanism) **falls out of the predicate itself** instead of needing a human to re-read the contact list.

⚠ **`w2:p11` also flags the classification's form, not just its content:** the code says *"name lacks `ext` ⇒
pad"* — a **negative** filter, so **any new geom silently becomes a pad**. ⇒ Use the positive form: *matches
`*_pad1` ⇒ pad1*. Same shape as the attribute-order grep failure p11 committed earlier today — **filters that
silently drop, and filters that silently pick up.**

⭐ **Cost, for whoever decides:** L1's quantity is already computed and printed. ⇒ **What is missing is putting it
into the verdict, not taking a new measurement.**

⛔ **Left open by p11 deliberately** (owner's choice, not the specifier's): whether L1 uses **full containment
[31, 33]** or **centre containment [28, 36]** — `w2:p0` established these are different predicates. p11
recommends [31, 33], because Rs's mechanism cannot work unless the cable is between the claws.

### 10d-1. ⭐⭐⭐ L2's band cannot be satisfied on hardware — the predicate is sim-only by construction

`w2:p5`: L2 requires `pad1` face separation ∈ **[4.0, 8.0] mm**, and the measured hardware stopping point is
**10.16 mm** (claws meet first). ⇒ **The band's upper end sits 2.16 mm inside the stop.** Axes agree — both are
`pad1` separation on the jaw-closing y — so the comparison is same-axis.

⇒ ⭐⭐ **A PASS from L2 is not "non-conservative this time". It is non-conservative by definition**, because the
region the band names is one real hardware cannot enter.

⇒ Options for whoever owns the predicate (⛔ p5 declines to choose; so does p18):
- **(a)** keep [4.0, 8.0] and tag **the predicate itself** sim-only ⇒ every PASS is automatically tagged. Cheap, honest.
- **(b)** additionally define an acceptance that hardware **can** reach, so a transferable claim is expressible.
- ⛔ **Until (b) exists, no predicate in the system can express a hardware-achievable grip at all.**

### 10d-2. ⭐⭐ Capture must be defined by containment, not by contact — and the rejected predicate deserves a fairer reading

At the hardware stop the **z** clearance is unchanged: slot 10.00 mm, Ø8 ⇒ **1.00 mm per side** ⇒ ⭐ **at rest the
cable touches neither claw.** And the judged driver's own design text says so (`:88-91`, verbatim): the claws
*"pass above and below the cable … and **catch it under lift load**"*.

⇒ ⭐ **Claw contact is a consequence under load, not a static requirement.** ⇒ The capture basis is **L1
(geometric containment) alone**; claw contact is evidence *under load*. ⛔ Requiring claw contact at rest would
**reject correctly captured states**.

⇒ ⭐ **So the earlier, "rejected" predicate was not wrong for looking at claws.** It was a **capture-family**
predicate whose defect was **missing L1** — it could fire on contact *outside* the claws. Add L1 and the capture
family is sound.

⇒ ⭐⭐ **The two historical predicates map onto the two substrates:**

| predicate | family | reachable on hardware? |
|---|---|---|
| claw contact (earlier driver) | **capture** | ⭐ yes |
| `pad1` compression (L2) | **pinch** | ⛔ sim only |

⛔ Which one acceptance uses is the owner's and Rs's call.

⭐ **L1's band is [31.00, 33.00]**, now supported by p5, p11 and p0's own correction: [28, 36] would score a
*colliding* configuration as "inside" — centre 28.00 puts the Ø8's underside at pad-local 24.00, overlapping
`f2ext`'s [24.60, 27.00]. That is a collision, not a pass-through.

### 10d-3. ⭐ The tag carries a number, not a boolean (`w2:p11`)

p11 scoped the non-conservative tag rather than letting it spread:

- ✅ **does not attach**: approach / positioning (the slot-vs-cable miss of 17.4 / 25.0 mm — independent of claw
  interference), and the geometry + ordering results (no-window — pre-penetration quantities)
- ⛔ **attaches**: every verdict that rests on **the backplate having reached the cable**
- ⭐ **firing condition, as one number: `pad1` face separation < 10.16 mm** — past that, the sim is travelling
  through a region where real hardware has already stopped
- ⭐ **amount, this run**: **L 6.81 ⇒ 3.35 mm deeper** than the hardware stop; **R 5.68 ⇒ 4.48 mm deeper**. That is
  the claw deflection hardware would have to supply to reproduce the same clamp.
- ⚠ p11 holds **zero** data on claw material, stiffness or allowable deflection ⇒ ⛔ it does **not** say 3.35 mm is
  impossible. Producing the required amount is where its court ends.

⇒ ⭐ **Adopted: the tag is written as "N mm deeper than the hardware stopping point", not merely
"non-conservative".** Small N ⇒ a light hardware check; large N ⇒ approaching a design problem.

⭐ p11 also self-reported the day's third rediscovery: this morning it quoted `2f85_koshape.xml:173-175`'s
**second half** ("Cable contact is UNAFFECTED") without reading the **first half** — which states that the claws
*can overlap at the close*, i.e. the thing it spent the afternoon deriving from geometry. All three rediscoveries
today sat **next to a line someone had already quoted**. ⇒ *Read the whole sentence at the place you opened to
quote.*

### 10d-4. ⛔⛔⛔ The name-matching trap is deliberate, and it is not confined to p4's driver

`w2:p0` measured the same classifier shape in the **production** env — `newton_skill_env_base.py:1392`,
`if "pad" in (gname + bname)`. Body names are `right_pad` / `left_pad`, so **every geom in that body matches**:
the claws (`right_pad_f1ext` / `f2ext`) and the silicone visuals included.

⭐⭐ **And the names were built that way on purpose.** `2f85_koshape.xml:112-113`, verbatim: *"Names contain `pad`
so the suite-wide contact filter (`test_newton_clip_routing.py`) keeps COLLIDE + cable contact."*

⇒ ⭐ The claws are **named to be caught by a contact filter** ⇒ any measurement predicate that reuses the same
substring match **inherits a set that was designed to include the claws**.
⇒ ⛔ So the fix cannot be "exclude `ext`" — a new geom without `ext` silently rejoins the set. The positive-form
`*_pad1` match `w2:p11` asked for is required, and now the **reason the trap exists** is on the record too.
⚠ p0 notes this is its carry-over #7, open since this morning ⇒ **repairing only the driver leaves the same set
live in the production env.**

⭐ p0 also closed a loop on the 0.30 mm caveat: p11's "evaluate L2 at the cable's z, not the box-pair minimum" is
**exactly** p0's §6 leading-edge term — `2 × |37.50 − 32.00| × sin(1.571°) = 0.302 mm`. ⇒ ⭐ **One mechanism
demanded absorption in three separate places today** (p0's §6 residual, the floor-family split, p11's L2
evaluation point). *A box stops being measured from its own faces the moment it tilts.*

⭐ **Cost, restated by the named implementer:** all three legs are **existing measured quantities** — L1 computed
and printed, L2 measured (6.81 / 5.68), L3's contact list already in the log and read by pB. ⇒ **No new
instrumentation whatsoever.** ⛔ p0 states the cost only; the gate is CLOSED and it proposes no start.

### 10g. ⭐⭐⭐ p18 read the log itself — and "the numbers" are not one witness. They disagree with each other.

I framed §10f as *video vs numbers*. That framing is wrong, and reading the log directly shows why. Verbatim,
`ur15_reaim_1352.log` (sha256 `5e4b59ed…`, unchanged), the STEP 4 block:

```
GRASP L: slot vs cable, live [ 22.2 -11.4   1.5] mm (| 25.0| mm; the band is +-1.0)
GRASP L: … cable moved  25.1 mm since the aim
GRASP L: cable touched by pads ['L','R'] / claws ['L','R']   clamped=True
GRASP L: fingers blocked by ['cab17', 'cab18']
GRASP L: nearest cable link cab18 at  33.5 mm from the pinch … pad geoms touching cable =
         ['Lg_left_pad1','Lg_left_pad_f1ext','Lg_left_pad_f2ext',
          'Lg_right_pad1','Lg_right_pad_f1ext','Lg_right_pad_f2ext']
GRASP R: slot vs cable, live [ -1.8   7.3 -15.7] mm (| 17.4| mm; the band is +-1.0)
GRASP R: cable touched by pads ['L','R'] / claws none   clamped=True
GRASP R: nearest cable link cab21 at  18.8 mm … pad geoms touching cable = ['Rg_left_pad2','Rg_right_pad2']
STEP 4 cable把持      t= 10.2s … grip=LR
```

⭐ First, this confirms `w2:p5`: the GRASP prints sit **inside** the STEP 4 block, so they are the same instant as
the disagreement. ⇒ p0's concern #1 (time correspondence) is discharged for the slot quantity.

⛔⛔ **But the arm the log calls L is internally inconsistent**, and nobody had put these lines side by side:

| quantity for log-L | says |
|---|---|
| `slot vs cable` **25.0 mm** (band ±1.0) | cable is far from the slot |
| `nearest cable link` **33.5 mm** from the pinch | cable is far from the jaw |
| `fingers blocked by ['cab17','cab18']` | ⛔ a cable link is **physically obstructing the jaw** |
| contacts: **6 geoms** — `pad1` **and** `f1ext` **and** `f2ext`, on **both** pads | ⛔ the cable is **inside the コ**, touching both claws |
| face gap **+6.81 mm** at `ctrl=255` | ⛔ the jaw is **fully commanded shut and stopped by something 6.81 mm thick** |

⇒ ⭐ **A cable 25 mm outside the slot cannot simultaneously touch both claws and both backplates and block the
fingers and hold the jaw open at ctrl 255.** ⇒ ⛔ **The two geometric prints disagree with the physics prints,
for the same arm at the same instant.**

⚠ By contrast **log-R is self-consistent**: `slot vs cable` 17.4 and `nearest link` 18.8 agree; contacts are
`pad2` only; no claw contact. ⇒ Cable low, outside the slot, resting on the lower box.

⇒ ⭐⭐ **So "the numbers" cannot be treated as a single witness against `w2:pC`.** One arm's numbers corroborate
pC's reading of *some* arm being properly engaged; the other arm's numbers corroborate p0. What is actually in
conflict is **which arm is which**.

### 10g-0. ⛔⛔ DIRECTION INVERTED — the cable was ABOVE the opening, not below (`w2:p11`)

⛔ **§10f's "at least 16.25 mm **below**" has the sign backwards, and so did every restatement of it, mine
included.** `2f85_koshape.xml` labels **`f1ext` BOTTOM (red)** and **`f2ext` TOP (blue)** — yet pad-local z is
**f1ext 38.2 > f2ext 25.8** (I had this in front of me at `:9` and did not use it). ⇒ ⭐ **pad-local +z points
DOWN in world**, consistent with `GD-KoShape-Finger.md:58-59` (world Z: f1ext 796.6 < f2ext 809).

⇒ `pad2` occupies pad-local **[0, 18.75]**, i.e. **smaller** z than `f2ext`'s 25.8 ⇒ ⭐ **in world, `pad2` sits
ABOVE the upper claw.** ⇒ **At that instant the cable was above the opening.**
⚠ p11 reports it made the same sign error this morning — writing the GD-KoShape inversion **two sections above**
the place it then failed to apply it. ⛔ Scope: that instant, R side only; do not generalise to other runs, other
steps, or the L side.

### 10g-1x. ⛔⛔ RETRACTED — there is no transposition. `w2:p0` settled it at the source.

p0 read the producing commit's build code (no run) and found the label↔arm binding is **structural**:

```
:42   SIDES = {L: -1.0, R: +1.0}
:193  for tag, sign in SIDES.items():
:195      column.add_frame(pos=[sign * YOKE_SPREAD, 0, SHOULDER_HEIGHT])
:196      attach_body(..., f"{tag}_")
:230-231  PADG[t] = geoms whose name starts with t + "g_"
```

⇒ ⭐⭐ **The name prefix and the world position are set from the same `sign`, in the same loop iteration**
(`YOKE_SPREAD = 0.40`, `:37`). ⇒ **`L` *is* the arm at column-local x = −0.40 and `R` the one at +0.40; they
cannot be transposed.** ⇒ ⛔ **My §10g-1 hypothesis is dead**, and it was dead in the build code the whole time.

⚠ p0 also bounds it: the separation is **column-local x**, not the production env's y = ∓0.35 — this driver
builds its own cell ⇒ ⛔ do not import `ROBOT_LEFT_BASE`/`RIGHT_BASE` into readings of this run.

⇒ ⭐ **What actually remains open is one link: column-local x ↔ which side of the screen.** p0 confirms from
source that the close-up `cam2` has **fixed azimuth 250** (`:723`, only `cam` varies at `:813`) with lookat at the
midpoint of the two pinch points (`:816`) ⇒ **`w2:pC`'s methodological claim — close-up stable, wide panel
unusable — is source-backed.** ⛔ p0 declines to convert azimuth 250 into "screen-left is +x" from memory; that
needs the convention read, or one frame rendered with the two pinch points marked. **p0 left the last link open
rather than closing it from recall.**

⭐ **And the physics now points one way.** `w2:p4` derived (from camera geometry alone, projecting world grasp
coordinates) that in the close-up **screen-right = L**. Under that mapping: pC saw screen-right with the cable
**inside the opening**, and log-L records **6 contacts including both claws, fingers blocked, jaw held at
6.81 mm** ⇒ ⭐⭐ **all three agree.** Under pC's mapping they contradict. ⇒ p18 notes the asymmetry as
**evidence favouring p4's mapping — not as proof.** The deciding read is the one p0 named, and it is pC's court.

⛔ **Two other things I suspected do not exist, and p0 checked before reporting:** the arm/pad mix-up
(`clamp_faces`'s `side` is the two pads of the *same* gripper; the arm is selected by `PADG[t]` at `:364`), and
any need for new measurement. ⭐ p0's posture: *"I do not report bugs that are not there."*

### 10g-1y. ⭐⭐⭐ The defended sets already exist — one line from the defect

p0 confirmed the real defect at source: `:366` splits only on `ext`, so the pad set is true for **`pad1` or
`pad2`**, while the docstring says `pad1`. ⇒ **That is the mechanism for R's `clamped=True` on `pad2` alone.**

⇒ ⭐⭐⭐ **And the positive-form sets `w2:p11` asked for are already in the same file**: `:234 CLAWG` and
`:236 PAD1G`, built from explicit names, carrying the comment — verbatim — *"Named, not substring-matched, so the
set cannot silently pick up another geom."*

⇒ **The author knew about the substring trap, built defended sets against it, and `clamp_faces` reaches past them
for the prefix-only `PADG` one line away.** ⇒ The repair is not new code; it is using the set that is already
there. ⚠ The production env's `newton_skill_env_base.py:1392` still carries the undefended form.

### 10g-1. ⚠ SUPERSEDED by §10g-1x — retained for the record

⭐ **The reconciliation survives the direction fix and gets stronger.** With the sign corrected:

| | log's numbers say | `w2:pC` saw |
|---|---|---|
| **log-L** | cable **in the コ** — both claws + both `pad1` touching, fingers blocked, jaw held at 6.81 mm | *"cable above both plates"* — **outside** |
| **log-R** | cable **above the opening**, `pad2` only | *"below blue, above red"* — **inside** |

⇒ ⛔ **Exactly opposite, and consistently so on both arms.** ⇒ ⭐ **One transposition reconciles every observation
at once**, and nothing else has to be wrong.

⛔ **Correction to my first statement of this.** I wrote the swap as *"log labels vs world"*. That does not work:
`w2:pC` derived its attribution **from this same log** (STEP 8 `L=259.3 / R=5.3`), so pC's "world L/R" is really
*"the arm the log calls L/R"* — a **video↔log correspondence**, not an independent world determination. A swap of
log-vs-world moves both together and resolves nothing.
⇒ ⭐ The transposition that does fit sits **between the log's per-arm data blocks and the arms pC identified** —
i.e. in the identification step or in the per-arm reporting, not in the naming convention.

⇒ ⛔ **And pC's leg cannot arbitrate it**, because the identification hinged on a log field. ⇒ ⭐ **The
non-circular check** (cheap, no run): resolve arm↔label from the **model** — the two grippers' body/site world
positions — rather than from any log field. ⛔ p18 requests nothing; `w2:p0` / `w2:p4`'s court.

⚠ It also fits `w2:p4`'s earlier note that its log read `L` succeeded where Rs saw **the right one** clamp.

⇒ ⭐ **The non-circular check** (cheap, no run): resolve the arm→label mapping from the **model** — body/site world
positions of the two grippers — rather than from any log field. ⛔ p18 requests nothing; this is `w2:p0`'s
(implementation) and `w2:p4`'s (driver) court.

### 10g-2. The other lead: what does `slot vs cable` measure the cable *at*?

⚠ Also inference. For log-L the printed drift is **`cable moved 25.1 mm since the aim`** and the slot error is
**25.0 mm** — the same magnitude. ⇒ Consistent with `slot vs cable` being evaluated against **the link that was
aimed at**, which has since moved away, while a *neighbouring* link (`cab17`/`cab18`) is what actually sits in
the jaw. ⇒ That would make the 25.0 mm a true statement about the **wrong link**, and would leave both pC and the
contact list correct.
⇒ ⭐ Cheap check, no run: does the slot-vs-cable computation use a **fixed link index chosen at aim time** or the
**nearest link at evaluation time**? ⛔ Same court as above.

## 10f. ⛔⛔ The visual leg and the contact-identity derivation disagree about R

Both concern the **same instant** — STEP 4 grasp, t = 10.2 s.

| leg | finding for **world R** |
|---|---|
| `w2:pC` (video, frame 306) | ⭐ cable **inside the opening** — below the blue plate, above the red |
| `w2:p0` (contact identity + asset geometry) | ⛔ R touches **only `pad2`**, whose pad-local z band is [0.00, 18.75]; Ø8 ⇒ centre ≤ **14.75 mm** ⇒ **at least 16.25 mm below** the containment band [31, 33] |

⇒ ⛔ **These cannot both be right, and p18 does not resolve it.** Recorded so the disagreement is not averaged
away. Predicate court = `w2:p11`; final physical judgement = Rs.

⚠ `w2:p0` flagged a related self-consistency problem *against its own result*: reading R's printed 17.4 as
(slot centre 32.00 − cable centre) gives centre 14.60, agreeing with its contact bound 14.75 to **0.15 mm** from
two unrelated signals — ⛔ **but the same reading breaks for L** (25.0 ⇒ centre 7.00, contradicting L touching
`pad1`). p0 raised it precisely so R's agreement would not be mistaken for endorsement of the reading.

⭐ **What the visual leg did settle — the world-frame attribution, which three parties had been reading three
different ways.** `w2:pC` established it from log ground truth (STEP 8, L = 259.3 mm / R = 5.3 mm at frame 582),
cross-checked against camera azimuth and the grasp coordinates (L x = 0.1141 / R x = 0.2036):
⇒ **close-up panel: screen-left = world L, screen-right = world R.** ⚠ The wide panel's azimuth varies with time
(`108 + 14·sin`), so it **cannot** be used for attribution.
⇒ At STEP 4: **world R inside the opening, world L outside** ⇒ ⛔ **not "both outside"**.

⛔ **`w2:pC` retracted the basis of its earlier `-094` leg, cause side pC:** it sampled at even intervals **without
locating the phase boundaries**, that run had **no log** so the grasp instant was never targeted, and it did no
world-frame attribution — so "both arms" was not established. ⇒ **`-094`'s "both arms, 18/18" must not be used as
established**, and this is the leading explanation of its disagreement with Rs's *"the right one clamps"*.
⚠ Its own briefing required sampling at every phase boundary; pC states plainly that it had not followed it.

The predicate has no owner (§10), but it does have natural courts, and all of them are already staffed:
**`w2:p11` specifies** (done, above) → **`w2:p0` implements** (p11 names it) → **`w2:pZ` verifies** (its restored
brief is exactly *"independently verify p0's implementation"*) → **`w2:p4` uses it**.
⇒ ⭐ So what §10 recorded as a vacancy may need **no new owner** — only a decision that the document follows this
chain. ⛔ p18 proposes the routing; it takes no design position on the predicate's content, and Rs decides.

## 10a. ⭐⭐ Rs's own words bear on the grasp/capture branch — placed here, not adjudicated

Relayed verbatim by `w2:p4` (⛔ p4's relay of Rs, not p4's reading):

> 爪の上下の隙間は問題ない、**左右で摩擦が生じれば**ケーブルをコ内に固定できる
> 逆に**上下をきつくしすぎると**ケーブルをクランプしずらくなる
> 単にコがケーブル位置にいっていないだけだ。**物理的にクランプ可能**

⇒ ⭐ The hold Rs describes is **left–right friction — compression**, not clearance-based containment.
⇒ ⚠ So `w2:p11`'s ruling (a correctly captured cable touches nothing ⇒ a contact predicate is false exactly when
the goal is met) is right **about capture**, but the state Rs calls clamped appears to be **the compression side**.
⛔ p18 does not decide this; the predicate is p11's court and the final call is Rs's. The verbatim is placed on
the branch, nothing more.
⛔⛔ **I attached that verbatim to the wrong axis, and `w2:p11` returned it.** I wrote that "tightening the top
and bottom makes it harder to clamp" reads against **option B** (reducing claw protrusion). It does not:

| Rs's phrase | axis | current |
|---|---|---|
| 「上下」 = the claw slot inside **one** pad | **pad-local z** | 10.00 mm |
| 「爪の突出」 = backplate front face → claw tip | **y (jaw closing)** | 5.00 mm/side |

⇒ ⭐ **Both of Rs's sentences are about z. Neither touches the y protrusion.** ⇒ ⛔ **Option B is neither endorsed
nor rejected** and remains under §0#4 LOCK, in Rs's court. What Rs did rule out explicitly is **narrowing the z
slot**.

⚠ Worth stating plainly: **§3 of this very file is my own warning that two ~10 mm quantities live on orthogonal
axes** — and I then conflated the same two axes, in the same court, two hours later. Raising a hazard is not the
same as being immune to it.

### 10a-2. `w2:p11` retracts its capture-basis ruling, and places the sim/real split without asking me to judge it

⭐ **p11 retracted the ruling as a *target*, keeping the part that is true:** the clearance-capture state does
exist geometrically (y 2.16 mm, z 2.00 mm at the stopping point) — ⛔ **but it is not what Rs calls clamped.**
p11's own words: *"I mistook 'it exists' for 'it is the goal'."* ⇒ The acceptance predicate goes on the
**contact + compression** side, which makes `w2:p4`'s repaired predicate the right *shape*.

⭐⭐ **And p11 resolved the tension I was preparing to escalate, correctly and without over-reaching:**

- **In sim**, the pad-pair `exclude` means the two pads never collide ⇒ the jaw travels to the cable and the
  backplates **can** compress Ø8 ⇒ **it behaves exactly as Rs describes.**
- **In real hardware built to this geometry**, the claws meet at backplate gap 10.16 mm and the backplates fall
  **2.16 mm short** of the cable.
- ⇒ ⭐ **Not a contradiction — different substrates.** p11 notes physical validity is Rs's exclusive and that it
  holds **zero** data on real claw stiffness or deflection, so it argues nothing and asks nothing.

⇒ ⭐⭐ **The consequence is mine to state, and I state it: any clamp success measured in this sim is
NON-CONSERVATIVE for transfer.** The sim is *easier* than reality here, because the claws pass through each other
where real ones would jam — and the asset says so in its own words (`2f85_koshape.xml:173-175`: the exclude
exists to *"Prevent claw-claw self-collision jam at the scripted close … the protruding コ claws f1ext/f2ext can
overlap at GRIPPER_CLOSE_QPOS"*). ⇒ Per §運用15, a non-conservative PASS requires high-fidelity or hardware
confirmation before transfer. ⛔ This tags the evidence; it does not question Rs's ruling about the real
mechanism, which is Rs's to make.

### 10a-3. A non-arbitrary lower bound already exists

`w2:p4` flagged its own 2.0 mm lower bound as neither measured nor designed. ⭐ `w2:p11` supplies the designed
value: `task_config.py:277` verbatim — `FINGER_CLOSE_POS = 0.002 # 2mm gripping (gap=4mm < cable 8mm → 2mm/side
compression)` ⇒ **design full-close = 4.0 mm face separation**. Paired with the upper bound 8.0 mm (Ø8, `:137`),
**the design's own band is [4.0, 8.0]**.

⇒ Choosing 2.0 means *allowing 2.0 mm deeper than the design's full close* — ⛔ which needs its reason and its
amount written down. p11 recommends 4.0; the predicate's owner decides, and that seat is vacant (§10).
⚠ Note it changes no verdict here: L 6.81 and R 5.68 both sit inside [4.0, 8.0]. **What decides R is the surface
problem in §10b, not the band.**

### 10b. ⛔⛔ The repaired predicate still has a hole, and `w2:pB` measured it

`w2:p4` repaired its predicate against Rs's ground truth — from *"both backplates contact the cable"* to
*"contact **and** backplate face separation within 2.0–8.0 mm"* — which removed the `clamp4` false positive
(faces at −8.43 mm, i.e. closed through where the cable was, had scored True). p4 scored `clamp5` **True/True**.

⛔ **`w2:pB`'s log leg shows the two conjuncts can be satisfied by different surfaces:**

| arm | face separation (`pad1` × `pad1`) | contacting geoms | do the measured faces touch the cable? |
|---|---|---|---|
| **L** | +6.81 mm | 6 faces incl. `Lg_left_pad1` / `Lg_right_pad1` (log `:59`) | ⭐ **yes** — measuring and touching surfaces coincide |
| **R** | +5.68 mm | ⛔ **only `Rg_left_pad2` / `Rg_right_pad2`** (log `:65`) | ⛔ **no** — the measured `pad1` pair is not touching |

⇒ ⭐ **R's +5.68 mm is the gap between two faces that are not on the cable**, so it cannot be read as
compression — and R nonetheless **passes** the repaired predicate. ⇒ **A second false-positive route, structurally
identical to the first**: contact *somewhere* standing in for grip *at the place being measured*.
⇒ The structural gap, stated without prescribing the fix (p11's court): the predicate does not require the
contact to be **on the pair it measures**.

⭐ pB retracted its own R figure inside the same message — it had computed R compression as 2.32 mm in one
paragraph and invalidated it in the next, keeping the L half, which is sound. ⇒ Retract the false clause, keep
the true one.

⭐ **One real repair did land**, measured by pB: the driver's `CABLE_R` is now **0.004 = Ø8**, citing
`task_config.py:137` — corrected from the previous run's Ø10. ⇒ The compression arithmetic is now on the right
diameter. Design target for reference: `task_config.py:277` verbatim — `FINGER_CLOSE_POS = 0.002 # 2mm gripping
(gap=4mm < cable 8mm → 2mm/side compression)` ⇒ **4.00 mm face separation**. L's 6.81 mm is **1.19 mm of
compression = 30% of design**. ⛔ The corresponding R figure does not exist, per the table above.

### 10c. PART 2 — the deciding predicate is missing the term that discriminates, and that term is already printed

⛔⛔ **RETRACTED — this paragraph was wrong, and the retraction is the sharpest instance of the day's type.**
The original text is preserved below, struck, followed by what I measured myself.

> ~~In `-121 (2)` I relayed p4's account that the predicate went from *contact only* → *contact + band 2.0–8.0*.
> `w2:pB` read the producing blob and found the band was already in `grasped()` when this log was made. ⇒ This
> log's `clamped=True` was produced by the banded predicate ⇒ the band did not remove R's True. ⇒ I relayed a
> before/after story about code without reading the code at the producing commit.~~

⭐ `w2:p5` refused the relay and read the banked commit itself. p18 then read it too — **`git show` at the exact
commits, not the working tree**:

```
$ git show e9f93a7556:…/ur15_steps_reaim.py | grep -n "def grasped" -A 4
371:def grasped(t):
372-    """Clamped = the cable is compressed between the two pad1 faces (bilateral)."""
373-    pad, _ = clamp_faces(t)
374-    return {"L", "R"} <= pad
$ git show e9f93a7556:…/ur15_steps_reaim.py | grep -cE "2\.0 <|< 8\.0|8\.0"
0
```

⇒ ⛔ **The judged predicate has ONE leg and no band.** No `pad1` test, no compression test, no slot test — and the
docstring claims *"compressed between the two pad1 faces"*, so **both conjuncts of its own docstring are
unimplemented**.

⇒ ⭐ **Therefore: `w2:p4`'s original account was correct** (judged driver = contact-only; the band came after, and
p18 verified it present at `7869a01b82`). ⛔ **`w2:pB`'s `[9)(b)]` was wrong, and my `-123 (1)` "correction" of p4
was wrong.** I overturned a correct account on the strength of an unverified relay — **inside a message whose
subject was reading code at the producing commit.** The rule was in the sentence I was writing.

### 10c-1. The pin was never broken — two hash namespaces were being compared

p5 also reported `git cat-file -t b06c5334` → *fatal: Not a valid object name* and treated the pin as unresolvable.
⛔ That is a category error, and p18 resolved it by measurement:

| identifier | what it is | value |
|---|---|---|
| `b06c5334f69a92f1df40f6dd130140539f99c278bd7cabcf5261ee70cb04110d` | **sha256 of the content** (64 hex) | ⭐ matches `git show e9f93a7556:…` piped to `sha256sum` **exactly** |
| `9c6aae562842e76e5a869ccbb804d42f273e4bc3` | **git blob id** (sha1, 40 hex) | p5's value, also correct |

⇒ **Both name the same bytes.** `git cat-file` fails on a sha256 because git objects live in a different
namespace — not because the pin is bad. ⇒ ⭐ The standing directive says *pin by content*; the pin obeyed it.
⚠ Worth carrying: **a content hash and a git object id are not interchangeable, and a failed `git cat-file` is
not evidence that a content pin is invalid.**

### 10c-2. ⛔⛔⛔ The judged driver reinstated a predicate that the previous driver documents as rejected

p18 verified this at the same commit. The **earlier** driver `ur15_steps.py` (`:330-342`) carries, verbatim:

> ```
> """True only when the cable is inside the ko bracket: it must touch a CLAW geom (f1ext/f2ext)
> on BOTH pads.  Contact with any pad face is not a clamp -- that predicate could not tell the
> two apart, and reported a grip that Rs could see was not there."""
> ```

⇒ ⭐⭐ **"Contact with any pad face is not a clamp … reported a grip that Rs could see was not there" — that is
exactly the predicate the judged driver went back to, and exactly the failure that recurred today.** The reason
for the rejection was written down, in the repository, in the file next to it. ⛔ p18 states the fact and not the
intent; whether the revert was deliberate is not measured.

⇒ ⭐ The repair now on disk (`7869a01b82`) restores a band and documents the 8.4 mm overlap case — but note what
that means for the sequence: **the fix landed after the judged run, so nothing in this run was produced by it.**

⭐⭐ **The finding that matters most today.** The quantity that would discriminate **is computed and printed, and
is not in the verdict**:

- the driver computes slot-vs-cable and prints it with an explicit **±1.0 mm** band (`:856-857`)
- measured: **L 25.0 mm / R 17.4 mm** ⇒ **17–25× outside that band**
- but `grasped()` (`:371-385`) has exactly two legs — pad-side contact on both sides, and `2.0 < gap < 8.0`.
  ⛔ **There is no slot term.**
- the driver's own design statement (`:88-91`, verbatim): *cable must arrive in the slot **BETWEEN the claws***

⇒ ⭐ **The verdict does not look at the design's arrival condition.** That is why `gates grasp True` (log `:81`)
and p4's refusal to call it success are both correct at once.

⛔ **And the mechanism behind §10b's split surfaces (`:353-368`):** the docstring says the clamp face is `pad1`,
but the code treats *any geom whose name lacks `ext`* as a pad — **so `pad2` satisfies it**. ⇒ R's `clamped=True`
stands on that docstring/code divergence, and **the two legs are looking at different faces**.

**L and R are not the same state** (pB):

| | L | R |
|---|---|---|
| face separation (`pad1`×`pad1`) | +6.81 mm | +5.68 mm |
| slot-vs-cable (band ±1.0) | **25.0 mm** | **17.4 mm** |
| cable moved after aim | 25.1 mm | 14.4 mm |
| **aim's own residual** | ⭐ **1.0 mm** | ⭐ **0.4 mm** |
| contacts | `pad1`×2 + claws×4 = 6 faces | ⛔ `pad2`×2 only |
| nearest link to pinch | cab18 @ 33.5 mm | cab21 @ 18.8 mm |

⇒ ⭐⭐ **The aim is solving.** It lands to 1.0 / 0.4 mm; the miss comes from **the cable moving 14–25 mm between
aiming and closing**. ⇒ The failure is not a targeting failure. ⛔ p18 draws no design conclusion from this.

⭐ **Under Rs's stated mechanism the two arms are not merely unequal — only one can satisfy it.** Rs: the hold is
**left–right backplate friction**. R has **zero backplate-cable contact** (log `:65`) ⇒ no friction-bearing
surface at all. L has two. ⇒ Same `True`, and only L's could be the mechanism Rs describes. ⛔ pB does not
adjudicate; nor do I. Predicate = p11's court, final = Rs's video.

⚠ Also from pB: the grip does not survive the push — `LR` at STEP 4-6, `L-` at STEP 7, **`--` at STEP 8**
(log `:66-70`). And the claw channel reads L −2.44 / R −2.48, which per §5 carries no depth information; pB
correctly declines to read transfer implications from it.

⚠ Line numbers in this section are at the **producing** blob `b06c5334` / commit `e9f93a7556`, not at the new
driver `28d10f15`. The log and the video are unchanged, so the object under judgement has not moved.

## 6. Instrument disposition (converged inside `w2:pZ`'s court — relayed, not decided by me)

- Primary per-run channel = **backplate-to-backplate** (`pad1` × `pad1`), which needs 8 mm of overlap to floor
  and therefore does **not** saturate in the clamp region.
- Claw overlap is **derived** from it (backplate − offset), and any use below ctrl 225 must be **marked as
  extrapolation** — the measured offset 10.11–10.16 is established only down to ctrl 225.
- If true deep-interference depth is ever needed, **stop using distance queries** and take face positions from FK;
  positions do not saturate.
- ⭐ `w2:pZ`'s structural point, retained: **the region where the offset matters most is exactly the region this
  instrument cannot measure.** ⇒ ⛔ Reading "interference is about 2.5 mm" into a transfer argument
  **under-states it**, and pZ declines to supply a number in place of the missing measurement.

## 7. `w2:p11`'s adjudication (its court — relayed verbatim in substance, unaltered)

**The capture predicate is written as geometric containment — z centre within [31.00, 33.00], y between the two
backplates — not as contact.** Grounds: in a correctly captured state the cable touches nothing (y clearance
2.16 mm, z clearance 2.00 mm) ⇒ a contact-based predicate is **false at exactly the moment the goal is met**.

⚠ Under gravity a captured cable rests on the lower claw, so contact does exist — but that is **resting on**, not
**grasping**. ⛔ It must not be used as evidence of a grasp.

## 8. Unchanged

Gate unchanged. Nothing unlocked. p18 authorises no run. Still with Rs: the holding-mechanism choice (A accept
capture / B change claw protrusion — §0#4 LOCK / C declare sim-only), the DUAL-ARM reading of the acceptance
predicate, and OPEN 5 (does capture suffice for the しごき / drag process — 捕捉 ≠ 把持, clearance ⇒ zero normal force).

### 10g-2x. ⭐⭐⭐ CONFIRMED AT SOURCE — the error metric was comparing against the wrong link

`w2:p4` read its own code and confirmed §10g-2. `ur15_steps.py:548-555`: `cable_at(x)` returns the centre of the
link **nearest a given world x**. `:878`: `cw, _ci = cable_at(GL[0] if t == 'L' else GR[0])` — and **`GL[0]` /
`GR[0]` are fixed x values measured at STEP 1 and never updated.**

⇒ ⭐⭐ **`slot vs cable` was comparing the mouth against the link nearest the start-of-run x, not the link in the
jaw.** ⇒ **`w2:p4` retracts:**

1. every live `slot vs cable` error (L 25.0 / R 17.4 …) ⇒ ⛔ **not evidence that the aim missed**
2. *"the cable moved 14–26 mm during the descent"* ⇒ against a fixed x, **a cable sliding in x changes which link
   is compared** ⇒ displacement and identity-change are mixed together
3. ⇒ ⛔ **p4's question D2 to `w2:p5` — "the arm must move because the cable shifts 14–26 mm" — has lost its
   basis.** ⚠ **p5's delivered Q2 answer rests partly on that magnitude and must be revisited.** The other half of
   p5's evidence (contact geom = `f1ext`, i.e. the claws struck the cable) is independent and survives.

⇒ ⭐ **This dissolves §10g's internal contradiction**: log-L printed 25.0 mm while touching both claws and holding
the jaw at 6.81 mm — not a conflict between physics and geometry, but **one invalid number**. The physics prints
were right throughout.

⇒ ⭐ It also explains p4's invention ⑤ (the live correction loop): **it used this metric as its objective**, and
its divergence (11.6 → 21.0 → 17.1 → 2.4) is consistent with optimising against a quantity that tracks the wrong
body. ⛔ p4 retracts ⑤ at its basis; causation not claimed.

⚠ **On `w2:p11`'s slot-motion hypothesis, p4 reports what its code does and does not do:** `slot_after_close`
predicts the post-close mouth position and aligns the arm to it ⇒ **it handles the endpoint, not the path.**
⇒ p11's mechanism — the mouth sweeping 13.4 mm while closing and the claws flicking the cable — is **not guarded
against** in this implementation.
⇒ ⭐ This is the banked lesson *a recovery mechanism must respect the same constraint on its path, not just its
endpoint* landing on a new surface: endpoint-consistency ≠ path-consistency, and the unguarded interval is
exactly where the disturbance lives.

### 10g-2y. ⭐⭐⭐ The precise mechanism is a third form — and it invalidates one more number I relayed

`w2:p0` read the same source and refined it. `cable_at` is **neither a fixed index nor the link in the jaw**: it
is an **argmin over a frozen x, re-evaluated every call** — `:529 argmin(|C[:,0] − x|)`, with x frozen at setup
(`:535`, `GL[0]`) and positions live. `:842` feeds it to slot-vs-cable, and `:849`'s *"cable moved"* reuses the
same value.

⇒ ⭐⭐⭐ **When the cable slides in x, the argmin jumps to a different link, both prints move discontinuously —
and it is reported as "the cable moved". What moved is which link is being measured.**

⭐ The magnitude fits: `CABLE_SEG = 30 mm` (`:47`) against L's 25.1 mm drift print ⇒ **less than one spacing** ⇒ a
single jump suffices. ⛔ p0 marks this as consistency, not proof — a genuine 25 mm motion prints the same number.

⛔⛔ **And the discriminating quantity is computed and then discarded.** `cable_at` returns the index (`:530`);
`:842` throws it away as `_ci`; `aim_cable[t]` stores position only (`:749`, `:768`). ⇒ Comparing the aim-time
index with the grasp-time index separates *"the cable moved"* from *"the measurement jumped"* **in one step**, and
**both indices exist at that moment**. ⇒ ⚠ **One grade worse than §10c**: there a quantity was computed, printed,
and left out of the verdict; here it is computed and thrown away. ⛔ Existing logs cannot settle it — neither
index was ever emitted.

⛔⛔ **A second number I relayed is biased.** The same output block contains **two different "nearest cable link"
computations with different references and different corrections**:

| site | reference | link position used |
|---|---|---|
| `:842` | **frozen x** | **segment centre** ⭐ corrected |
| `:823-824` | **pinch** | **body origin** (`d.xpos[b]` raw) ⛔ uncorrected |

And `cable_at`'s own docstring states the size of the difference, verbatim: *"A link's body origin is the START of
its capsule … targeting the origin misses by ~15 mm"* — half of a 30 mm segment is exactly 15.0 mm.

⇒ ⭐⭐⭐ **The correction is written down, its magnitude is documented, and it is applied at one of the two sites.**
⇒ ⛔ `:860`'s *"nearest cable link cab18 at 33.5 mm from the pinch"* — which I put in §10g's table as evidence of
internal contradiction — **carries that ~15 mm bias.** That row weakens; the rest of the table (contacts, fingers
blocked, face gap at ctrl 255) is unaffected.

⚠ p0's scope, preserved: **source only**, log not opened, no run ⇒ **whether the jump actually occurred is not
established.** Mechanism and two checks offered; no verdict.

⇒ ⭐ **The pattern of the day, three times in one file:** a quantity computed and printed but absent from the
verdict (the slot term); a quantity computed and discarded (the link index); a documented correction applied at
one of two sites. **Every time, the information needed was already there and was not used.**

### 10g-3. ⭐ The contradiction I raised in §10g is fully dissolved — every geometric row was measuring elsewhere

`w2:p5` read the driver and downgraded its own "third witness", which removes the **second** row of my table:
the same log carries **three different references for "the cable"** —

1. the **mouth**, against the link chosen by nearest **frozen x** (`:842`)
2. the **pinch point**, 3-D nearest (`:822-824`)
3. the geoms **actually in contact**

⚠ And the **pinch point sits 26–31 mm from the mouth**. ⇒ ⭐ *"nearest cable link at 33.5 mm from the pinch"* is a
value you get **even when the cable is correctly in the mouth** ⇒ ⛔ **it never was evidence of non-grasp** — on
top of the ~15 mm body-origin bias `w2:p0` found at the same site.

⇒ ⭐⭐ **So both geometric rows of §10g's contradiction table are gone**: `slot vs cable 25.0` (argmin jump) and
`nearest link 33.5` (wrong reference + uncorrected origin). **What survives is entirely physics-side** — six
contacting geoms including both claws, fingers blocked by `cab17`/`cab18`, and a face gap of 6.81 mm at ctrl 255.
⇒ ⭐ **The physics prints were right the whole way through, and every geometric print I set against them was
measuring something else.** I framed that as *"the numbers disagree with each other"*; it is better stated as
**three quantities that were never about the same thing.**

### 10h. ⭐⭐ The Rs question has narrowed to one sentence

`w2:p5` accepted `w2:p11`'s correction that the position/force dichotomy was false — the current control is
**position target + effort limit**, i.e. already force-limited compression (`task_config.py:129 = 60.0`,
`:316 = 2.5`). It **keeps the conclusion** (do not use ctrl 255) and **replaces the grounds**:

1. the terminal −1.3 mm **ejects** a correctly seated Ø8 (p11)
2. ⭐ **measured: L stops at 6.81 mm even at ctrl 255** (log `:56`, `:59`) ⇒ **with a cable present, even in sim
   the commanded 4.0 mm is never reached**

⇒ ⭐⭐ **The quantity to design is therefore not the commanded gap but the effort limit** — command the table's
4.0 mm and let arrival be self-limiting, which is **what the implementation already does.**

⇒ ⭐⭐⭐ **So the escalation is one sentence, and no in-sim choice addresses it:**

> **On hardware the claws stop everything at a backplate gap of 10.16 mm, so the compression Rs describes —
> left–right friction on the cable — is zero. The LOCKed geometry admits no command value that both compresses
> and is reachable.**

Branches, unchanged and both Rs's: **(A) capture** — stop ahead of claw contact (command ≈ 11.0 mm), hold by form
closure under load; **(B) pinch** — keep 4.0 mm and treat all Phase-A results as sim-only.
⛔ Force-closing is not a third branch: position → force is a **control-method change requiring Rs approval**
(`prohibited.md`).

⚠ One more source-derived design correction from p5: **the descent point's x is a design constant** (§0#2's 88 mm
span), not taken from the cable ⇒ **only y and z are re-aimed**. p5's first version said "fix x,y" and is corrected.
⚠ Revised design: sha256 **`b9eda46e7b98e408a3221d038dcd12b322f908ccd1fc5a48e21f9711cef4c444`** supersedes
`afa56085…`; still **untracked** — banking is `w2:p4`'s court, p5 is 0-commit.

## 11. ⭐⭐⭐ The day's general lesson, named by `w2:p11` — three instances of one shape

**Three times today a quantity that seemed to demand an explanation turned out not to be that quantity at all:**

| # | quantity | what it actually was |
|---|---|---|
| 1 | **3.43 mm** | the difference between a **saturated** reading and an unsaturated extrapolation |
| 2 | **0.17 mm** | an "excess" over an **upper bound computed for parallel boxes** that were not parallel |
| 3 | **14–26 mm** | an instrument comparing against the link nearest a **frozen x**, not the link in the jaw |

⇒ ⭐⭐ **Discipline: before setting out to explain a number, check that it measures what its name says.**
⇒ Each of the three would have vanished from **one check taken before the explanation began** — and in each case
substantial work by several panes was spent explaining an artefact.

⭐ `w2:p11` also split its own corroboration correctly rather than defending it whole:
- ✅ **survives** — the contact-based estimate (`pad2`-only contact ⇒ centre ≤ 14.75 mm). **It uses no instrument.**
- ⛔ **weakened** — the printed 17.4 ⇒ centre 14.60, since that instrument is retracted.
⇒ **"R's cable was outside the opening" stands**, carried by the contact identification, not by the print. ⇒ And
p11 retracted the *phrasing* "two quantities agree" in favour of "one quantity plus one weakened quantity".

⭐ **A reverse implication worth keeping:** if the 0.15 mm agreement was not coincidence, then in R the frozen-x
link and the pad-touching link were **the same**, i.e. the cable barely slid in x. ⇒ That gives the
state-dependence a concrete reading: **slid ⇒ different link; did not slide ⇒ same link.**
⇒ ⭐ And the hypothesis is no longer a hypothesis — **the mechanism is confirmed in code**; only *which run, how
much* remains open.

⭐ `w2:p11` kept the true half of its own falsified hypothesis: `slot_after_close` demonstrably handles the
**endpoint and not the path**, so an unguarded sweep during closing **does exist** — ⛔ but the conclusion it
supported (that this caused the observed miss, downward) stays falsified on R and is **not to be revived as a
root cause**. ⚠ And the 14–26 mm it was invented to explain has itself since been retracted.

⭐ **`w2:p4` then repaired the instrument** (⛔ explicitly *not* a new design version — it remains on hold): the
comparison is now against the link nearest the **seat point**, and **the compared link's identity is printed**
(`seat vs NEAREST cable link cab19`), with the drift line reworded to *"nearest link is N mm from where the aimed
link was (identity may differ — not a drift)"*. driver sha256 `770b2271…` @ `887d3fefde` (p18 verified).
⇒ ⭐⭐ That is the direct answer to `w2:p0`'s finding that the index was **computed and discarded**: from here on,
*"the cable moved"* and *"the measurement jumped"* are separable by a reader of the log.
⚠ The existing log and video are unchanged, so the object under judgement has not moved.

### 11a. ⚠ A new design requirement, a conditional that could invert the design, and a moving pin

⭐ **`w2:p5` added one requirement** in response to §10g-2x's endpoint/path point: the cable must be inside the
slot **for the whole closing interval**, not merely at the endpoint — matching the endpoint only lets the claws
sweep it on the way.

⇒ ⭐⭐ **A conditional worth reading carefully:** if the slot moves **13.4 mm** from open to closed and the slot
height is **10.00 mm**, then ⛔ **the open-pose band and the closed-pose band do not overlap** ⇒ ⭐ **no aim point
keeps the cable inside for the whole interval.** ⇒ In that case the design changes direction — from *avoid
contact* to **contact without flicking the cable out**.
⛔ p5 does not carry this as settled: the 13.4 mm **direction is unmeasured** (inherited from p11's own caveat).

⇒ ⭐ **Falsifier: one run, and a cheap one** — hold the arm fixed, close only the fingers, measure the slot
centre's displacement **magnitude and direction**. Under 10.00 mm ⇒ overlapping bands exist and a single aim point
suffices. ⚠ Needs run authorisation; p5 notes that is not its court, and p18 authorises nothing.

⚠ **Pin hygiene, on this file specifically:** p5's design has moved **three times in about ten minutes**
(`afa56085…` → `b9eda46e…` → `d0e48413…`, 195 lines, still untracked). ⇒ ⛔ **Every sha of it in this ledger is
stale on arrival**, including the one recorded in §10h. ⇒ ⭐ **Cite it as "the version `w2:p4` banks", not by
hash** — this is precisely the case the standing rule covers: *pin by content, and treat the version as a
collation note*. Banking is p4's court; p5 is 0-commit.

⚠ `w2:p5` also disclosed that its own `-029` reached me with **three passages missing**: an unquoted heredoc let
backticks be command-substituted away. That is the project's documented **backtick hazard**, and p5 restored the
three passages in plain text. ⇒ p18's dispatches use quoted heredocs and are unaffected — checked, not assumed.

### 11b. The aim residual, the narrow scope of the repair, and one inference withdrawn from my own argument

⛔ **p18's own relay needs qualifying.** I passed on *"the aim is solving (1.0 / 0.4 mm)"* as established. Reading
the producing blob myself: `:438 err = slot_after_close(t, w, CLAMP) − cable_w`, and the call site supplies
`cable_w` from `:743-744 cable_at(GL[0]) / cable_at(GR[0])` — **the frozen-x rule.**
⇒ ⭐ So the residual is a valid measure of convergence **onto the link the frozen-x argmin selected at aim time**.
⛔ It is **not** evidence that the aim was at the right link, and that selection can differ from the link that
later occupies the jaw. ⇒ **"The solver converges" survives; "the aim was correct" does not.**
⭐ `w2:pB` reached the same place independently and stated it plainly: what survives is **the servo reached the
commanded pose** (joints vs commanded ≤ 0.5 mrad, log `:55`/`:61`); **whether the aim was on target is UNKNOWN**.
⭐ Incidentally the same line confirms the endpoint/path split from the other side: `slot_after_close` sits
**inside** the aim loop, so the **endpoint** is explicitly accounted for — and the path still is not.

⛔⛔ **`w2:p11` withdrew an inference it had handed me, while it was load-bearing in my argument.** It had reasoned
that the 0.15 mm agreement implied the cable had not slid in x in R. With p0's second defect (body origin,
15.0 mm uncorrected, `CABLE_SEG = 0.030` ⇒ half = 15.0), a ±15.0 systematic on the printed 17.4 would put the
centre at −0.4 or 29.6 — ⇒ **neither near the contact bound of 14.75** ⇒ ⭐ **the agreement can be coincidence.**
⇒ p11 withdraws *"in R the frozen-x link and the contact link were the same."*
⭐ Its stated reason for the urgency is worth keeping: **it does not leave an inference it originated sitting
inside another pane's argument.** ⚠ And it phrases the limit correctly — *"cannot be used as grounds"*, not
*"is false"* — because it has not read whether the 15.0 mm systematic reaches the z comparison.
✅ Unaffected: the contact-based estimate (`pad2`-only ⇒ centre ≤ 14.75) ⇒ **"R's cable was outside the opening"
still stands**, on no instrument at all. ✅ My hypothesis also unaffected — the mechanism is confirmed in code;
what is lost is only the limitation *"it did not bite in R"*.

⚠⚠ **`w2:p0` checked p4's repair and its verdict is deliberately narrow — do not widen it.**
✅ Independently reproduced the sha; the **reporting** path is genuinely fixed: `:886` selects by
`argmin(norm(_cc − sp))` — **seat point, 3-D norm, frozen x gone**; `:890` prints `cab{_ci}`, so the discarded
discriminator is now **visible**; `:895-896` no longer asserts motion it cannot establish.
⛔ **Two sites did not get the repair:**
1. **The aiming path is still frozen-x** (`:768-769`), under a comment reading *"aim at where the cable IS, right
   now"* ⇒ ⭐ **reporting now follows the seat point while aiming follows the frozen x** ⇒ the same jump survives
   **on the control side rather than the reporting side**, and the new line compares a seat-selected link against
   a frozen-x-selected link — **two rules**. The added *"identity may differ"* caveat is honest about the
   consequence but does not remove the mismatch.
2. **The pinch-reference print still uses the body origin** (`:859 norm(d.xpos[b] − pw)`) ⇒ the documented
   half-segment bias is still on it. ⭐ `-137` told the court not to use that number — ⛔ **but an instruction is
   not a guard.**
⇒ ⭐ **Correct scope: "repaired with respect to the reported slot quantity."** Not a general fix.

### 11c. ⛔⛔ My falsifier could not have answered correctly — caught by two panes before it reached Rs

I wrote the test as *"under 10.00 mm the bands overlap and one aim point suffices"*. **The threshold is 2.00 mm.**
`w2:p11` and `w2:p0` reached it independently.

⇒ What must overlap is **not the slot height** but the **containment band of the cable centre**: Ø8 fully inside a
10.00 mm slot ⇒ centre band **[31.00, 33.00] = ±1.00 mm** ⇒ the open-pose band `[c−1, c+1]` and the closed-pose
band `[c+t−1, c+t+1]` overlap **iff |t| < 2.00 mm**. ⇒ **3 mm of travel already destroys the single aim point.**

⇒ ⛔⛔ **So my test would answer "the bands overlap" for every displacement between 2.00 and 10.00 mm, when they
do not** — ⭐ `w2:p0`'s phrasing: *a test that cannot give the right answer across an 8 mm range of the very
quantity it measures.* ⇒ **The measurement was right; only the number I compared it against was wrong.**
⇒ ⚠ **Third time today I published a check without asking whether it could come out either way** (the "free
second path", the pinch-distance row, and now this) — and this one was on its way to Rs.

⭐ **Two corrections that make the escalation sound:**

1. **`w2:p11`: the window is too wide.** Claw tips only reach the cable's y-extent at backplate gap
   `2 × (4.00 + 5.00) = 18.00 mm` ⇒ **the constraint bites only over backplate gap [10.16, 18.00] — the last
   7.84 mm of the close.** ⇒ Measure the slot-centre displacement **inside that window**, not across the whole
   13.4 mm of travel. ⇒ ⭐ **Total travel of 13.4 mm is compatible with success if in-window displacement is
   < 2.00 mm.** ⚠ Assumes the cable is y-centred.
2. ⭐⭐ **`w2:p11`: the condition depends only on |t|, so direction is irrelevant.** ⇒ **The unmeasured sign of the
   13.4 mm is not needed** — p5 held the conditional back citing p11's own caveat, and **that caveat does not
   apply to this question.**

⭐ **`w2:p0` adds two things that change how the escalation should be put:**
- **Full containment and "not struck by the claws" are the same band** — the claws bound the slot, so clearing
  `f2ext` needs centre ≥ 31.00 and clearing `f1ext` needs ≤ 33.00. ⇒ p5's whole-interval requirement **is** the
  2.00 mm band.
- ⇒ The conclusion is **far stronger than stated**: 13.4 mm against a 2.00 mm band is **short by 11.4 mm = 6.7×
  the band**. ⚠ Against 10.00 mm it reads as "3.4 mm short" — **an 8 mm understatement**.
- ⭐⭐ ⛔ **But the design does not invert automatically.** Under the weaker requirement — cable stays within the
  claws' span, contact permitted — the centre tolerance is **[23.00, 41.00] = 18.00 mm wide**, and 13.4 mm leaves
  **4.6 mm of room.** ⇒ **Inversion follows only if whole-interval *full containment* is required**, and which
  requirement to adopt is `w2:p5`'s and `w2:p11`'s call, not arithmetic's.
⚠ p0's scope: all of it conditional on the 13.4 mm being real and along the slot's z. It grounded the **frame**
from vault (`GD-KoShape-Finger.md:58-59`), **not the displacement**.

### 11d. ⭐⭐ The attribution conflict is closed — `w2:pC` retracted, `w2:p4` was right

pC redid the azimuth math and found its own sign error: az 250 / el −16 ⇒ forward (−0.329, −0.903, −0.276) ⇒
**screen-right = (−0.940, +0.342, 0)**, i.e. world **−x**. Projecting the grasp points (L x = 0.1141 /
R x = 0.2036) gives L −0.107 > R −0.191 ⇒ **L is on screen-right.** ⛔ In `-128` pC had taken screen-right as
`+x`.

⭐ **And pC then checked it a second way that does not use the log's labels at all**: pixel change between
STEP 7 (`grip=L-`, f534) and STEP 8 (L departs to 259.3 mm, f582), compared across the close-up's two halves —
**right 39.12 vs left 22.10** ⇒ the arm that moved is on **screen-right** ⇒ that arm is L. **Calculation and video
agree.**

⇒ ⭐ **Corrected reading of STEP 4 — the observation is unchanged, only the names swap:** **L (screen-right) =
cable inside the opening; R (screen-left) = outside.**
⇒ ⭐⭐ **So pC's observation and log-L now describe the same arm** — the one with six contacting geoms including
both claws and the jaw held at 6.81 mm. ⛔ pC notes, correctly, that agreement is not proof; the verdict is Rs's.
⇒ **§10f is closed: the disagreement was a sign error in a projection axis, and the physics was consistent
throughout.**

## 12. ⛔⛔ Rs's second video finding lands on a surface the sim cannot report

`w2:p5` ran a closed query on the banked commit and p18 verified it independently at the same commit
(`git show e9f93a7556:…/ur15_cell.py`, `:112-115`):

```
<geom name="floor" type="plane"    … contype="0" conaffinity="0"/>
<body name="column">
  <geom name="stem" type="cylinder" size="0.102 …" … contype="0" conaffinity="0"/>
  <geom name="foot" type="cylinder" size="0.215 0.03" … contype="0" conaffinity="0"/>
</body>
<body name="table"> <geom name="table_top" type="box" …/>          ← no flags: the table DOES collide
```

⇒ ⭐ **The scene's cylinders are the robot's stem and foot, and both have collision disabled.** The cable is
capsules (`cab{i}_g`), a separate matter.

⇒ ⛔⛔ **So if the video shows the arm hitting a cylinder, that is not contact — it is penetration.** With
`contype=0 / conaffinity=0` the physics offers **no resistance at all** ⇒ ⭐⭐ **the sim cannot report it as a
failure**: no contacts are generated, so it is invisible to every contact-based check we have.
⇒ ⭐ **Rs's eye was the only detector.** That is the clearest justification for the visual leg the day has
produced.

⇒ ⭐ **Design consequence (`w2:p5`'s court):** the current path **cannot work on hardware** — the real column is
physically there. Path and pose must be designed with the column as a **real obstacle**. ⚠ p5 notes this is the
project's named anti-pattern: **do not justify penetration by disabled collision; design must not rest on a
collision-disabled value.**

⭐ **Two cheap things decide it, and p5 named both:**
1. **Whether Rs's 「円柱」 means the column or the cable capsule** — one word from Rs. ⚠ If the cable, this is
   ordinary contact and not the above.
2. ⭐⭐ **Measure arm-geom to `stem`/`foot` minimum distance along the trajectory.** `mj_geomDistance` is
   **independent of the contact filter** — p5 established exactly that in today's probe ⇒ **distance is
   measurable even where collision is disabled, and penetration appears as a negative value.**
   ⇒ ⭐ Today's instrument work now supplies the tool that sees what the physics was told to ignore.

⚠ **p18 adds two observations from its own closed query, neither of which p5 reported:**
- **The floor is also collision-disabled** (`contype=0 conaffinity=0`) ⇒ a second surface the arm can pass
  through without the sim objecting. Same class, not yet examined.
- **The cylinder definition appears in five files** at that commit, not one — `ur15_cell.py`, `ur15_route.py`,
  `ur15_steps.py`, `ur15_steps_reaim.py`, `ur15_yoke_video.py` (2 matches each). ⛔ p18 has **not** established
  whether these are duplicate cell builders or references, so this is **not** a claim that five scenes are
  affected. ⇒ ⚠ But if a repair is applied to `ur15_cell.py` alone, the others must be checked — **the same
  shape as `newton_skill_env_base.py:1392` surviving a driver-only fix.**

⭐ `w2:p5` also declined to defend its own conditional: *"the conditional said 'conditional because the quantity
is undetermined'; once the quantity lands the conditional is spent, and I will not defend it."* And it lifted its
freeze after confirming the bank, adding future material as **new sections without rewriting banked lines**.

## 13. The inversion probably does not happen, and the aim "improvement" is not one

**(a) `w2:p0` reproduced the window and bounded the answer.** Claw reach at backplate gap
`2 × (4.00 + 5.000) = 18.00 mm` ⇒ window `[10.16, 18.00]` = 7.84 mm wide ⇒ **ctrl [198.19, 219.16]**;
`w2:p11` re-derived it independently from both calibration slopes (2.6750 → ctrl 198.0; 2.8882 → 196.8) ⇒
**window ≈ ctrl [197, 219] either way.**
⇒ ⭐⭐ The window spans two of p4's sample intervals ⇒ **in-window displacement ≤ 0.47 + 0.05 = 0.52 mm** ⇒
**3.8× margin against the 2.00 mm band** ⇒ ⭐ **the bands overlap and the design does not invert.**
⚠ Reservations kept by p0 and not dropped here: the series reached it by **relay** (source unread); it assumes no
reversal **within** a sample interval; and the values are **base +z**, not the component (b) requires.
⇒ **An upper bound, not a measurement of the window.** ⛔ p18 does not report an inversion to Rs.

**(b) `w2:p0` settled the axis question exactly.** The mouth's height axis **is pad-local z**: `f1ext`
(0, −0.0026, **0.0382**) and `f2ext` (0, −0.0026, **0.0258**) share x and y and differ only in z ⇒ the line
joining them is precisely pad-local z ⇒ the decomposition is **"project onto the pad body's local z"** — no new
geometry, no ambiguity, and the world direction is already grounded (`GD-KoShape-Finger.md:58-59`), so the sign
is not free either.
⭐ `w2:p11` accordingly tightened its own rule: **|t| < 2.00 mm is sufficient but not necessary** — a large
displacement with a small height component still overlaps ⇒ ⛔ **its rule errs toward over-detecting inversion**
⇒ adopt **|t_slot| < 2.00 mm** on the height component, and report decomposed into the mouth's own axes.

**(c) ⛔⛔ The improved aim residual is not evidence of a better aim.** `w2:p0` checked all three commits of the
driver: even at the latest (`887d3fefde`), `:767-769` still calls `cable_at(GL[0])` / `cable_at(GR[0])` — **the
frozen x. Only the reporting path moved to the seat point** (`:883-886`).
⇒ ⭐⭐ So **L 0.09 / R 0.16 mm measures convergence onto the link the frozen x selected.**
⇒ ⭐ p0 states the trap plainly, and it is worth keeping in this form: **a small residual against a target that
can be wrong means the convergence tightened, not that the aim improved. What separates the two is the selection
rule — and that is unchanged.** ⚠ A 10× improvement looks like success, which is exactly why it needed saying.

**(d) `w2:p11` took Rs's singularity finding, with a measurement plan and no design choice yet.**
- Instrument = **Jacobian minimum singular value**. ⭐ p4's offered quantity is the right one — ⛔ **but per
  waypoint is not enough: singularities are passed *between* waypoints** ⇒ sample along the interpolated path and
  report the **minimum over the window**. *(The path-not-endpoint lesson, third surface today.)*
- Options, all inside DiffIK and none a method change: ① raise DLS damping λ — ⚠ **blunts tracking** (λ 0.20 can
  drop effective tracking to ~0.5%), the "safe but immobile" trap; ② ⭐⭐ **use the free axis** — the tool-pose
  spec permits outward roll, so roll about the closing axis is free ⇒ **even a 6-DoF arm gains one redundancy**,
  usable as a nullspace objective to raise σ_min — p11 judges this best-founded; ③ re-lay waypoints to detour —
  ⚠ touches the step table's geometry ⇒ **`w2:p5`'s court**.
- ⛔ **It chooses none, because σ_min measurements are zero.** Measure, then choose.
- ⚠ ⛔ It has not measured UR15's joint layout and **refuses to assume "UR family ⇒ wrist singularity"**.
- ⭐ And it turned p18's correlation remark into a test: **if the departure and the singularity share a root, the
  σ_min valley and the 259 mm departure should coincide in time** ⇒ falsifiable; if they do not, different cause.

### 12a. Closed by measurement — all five copies, and the day's failure shape a third way

`w2:p5` closed my open (b): **the five files are independent copies, not references** — none of them imports
`ur15_cell` (import count 0 in all five), each carries its own scene. ⇒ ⛔ **Repairing `ur15_cell.py` alone
repairs none of the other four.** ⚠ The same shape as `newton_skill_env_base.py:1392` surviving a driver-only
fix — **five-fold, on the same day.**

⭐ p5's complete enumeration of collision-disabled geoms (`ur15_cell.py` + `ur15_base.xml`, closed query):
**`floor` (`:112`, plane 6×6), `stem` (`:114`, r 0.102), `foot` (`:115`, r 0.215)**; `ur15_base.xml` = **0**.
⇒ ⭐ **Three surfaces are invisible to the physics: the floor, the column, and the base.** The table collides.
⚠ p5 marked what it had **not** checked: whether the other four files' cylinders carry the same flags.

⇒ ⭐ **p18 closed that in one query: they do. All five files, both cylinders, `contype="0" conaffinity="0"`.**

⚠⚠ **And I nearly reported the opposite.** A line-oriented `grep -c 'contype="0" conaffinity="0"'` on the `stem`
line returned **1, 1, 1, 1, 0** — the last file appearing to differ. ⛔ It does not: in `ur15_yoke_video.py` the
geom element **spans two lines** (`:65-66`) and the flags sit on the second.
⇒ ⭐ **A line-scoped predicate against a multi-line element produces a false absence** — the day's shape a third
way: `w2:p12`'s `cut -c1-170` on a 337-character line, my relay of it unread, and now a per-line grep on an XML
element that is not per-line. ⇒ ⭐⭐ **Print the whole element before asserting absence** — the general form of
p12's own rule, and it caught this one.

⭐ p5's design triage, held rather than acted on: the **column and base are real obstacles** and their radii
(0.102 / 0.215) bear directly on shoulder-region pose selection; the **floor** is probably out of reach with the
table above — ⛔ **p5 marks that as its own unverified guess** and measurable (are there waypoints below the
table?). ⇒ ⛔ p5 will not rewrite the path until the distance measurement establishes whether penetration is
actually happening: **if it is not, this is adding a constraint, not changing a design.**

## 14. ⭐⭐⭐ "The sim permits what hardware forbids" is a class — and the production env shares it by design

`w2:p11` generalised the day's three instances rather than treating them as separate accidents:

| # | disabled pair | what it permits |
|---|---|---|
| ① | pad-pair `exclude` (`2f85_koshape.xml:176`) | claws interpenetrate ⇒ **backplates reach the cable** (the compression clamp) |
| ② | `stem` / `foot` `contype=0` | **the arm passes through the yoke column** |
| ③ | `floor` `contype=0` | the arm passes through the floor (⛔ unexamined) |

⇒ ⭐⭐⭐ **Rule adopted, replacing the single-item tag: if a verdict's validity depends on a
collision-disabled pair not interfering, that verdict is non-conservative for transfer.**
⇒ ⭐⭐ And it is **enumerable by closed query**: (1) list every collision-disabled pair (`contype`/`conaffinity`
zero, plus `exclude` body pairs); (2) for each, ask whether any verdict depends on it; (3) tag those.
⛔ **Do not stop at "repair what was found"** — that is how ② and ③ survived ① all day.

### 14a. ⛔⛔ The same blind spot is in the production env, and it is deliberate — p18 verified it

`w2:p0` found it; p18 read `thread_isaac_lab/envs/newton_skill_env_base.py:1574-1583` directly. Comment, verbatim:

> `# A-1 VISIBLE-only pass (probe-proven, F4c): clear COLLIDE on non-pad arm shapes (→ MuJoCo`
> `# contype=conaffinity=0); KEEP COLLIDE on the gripper PAD geoms (cable grasp).`

and the code does exactly that — `if "pad" not in lbl.lower(): proto.shape_flags[si] = VISIBLE`.

⇒ ⭐⭐ **Every arm shape whose label lacks `pad` has collision cleared in the production env too.** ⇒ **Arm-to-
structure penetration generates no contacts there either** ⇒ ⛔ **§12's conclusion is not confined to p4's
driver.** Any check that looks for arm/structure interference **through contacts** is blind on the production
path as well — ⭐ and this is an **explicit design decision, not an oversight** (it is even labelled
*probe-proven*).
⛔ **p0 does not call the design wrong, and neither do I.** The claim is narrower and sharper: **the detector
everyone instinctively reaches for does not exist on that path.**
⚠ Note the selection is the **same substring rule** as `:1392` — one rule in two places. ⚠ p0's reservation
kept: `shape_label` is a Newton label and need not equal the MuJoCo geom name, so **whether the claws fall in
that set is unverified** — the shared rule is the point, not the specific membership.

⇒ ⭐ **And the instrument this court spent the whole day characterising is the one tool that sees it:**
`mj_geomDistance` is independent of the contact filter (established by p5's probe, corroborated by p0's contract
read) ⇒ **it measures distance where collision is off, and penetration reads negative** ⇒ the proposed
arm-to-column sweep works **despite** the flags, and for the same reason it works on the production path too.

### 14b. `w2:p11` reports two of its own items hit by the class

**(a) Its singularity work assumed a physically valid path.** ⇒ If the arm penetrates the column, the trajectory
it would measure σ_min along **cannot be executed on hardware** ⇒ ⭐ **singularity correction and column
avoidance are two constraints on one path and must not be solved separately.**
⇒ ⚠⚠ And the option p11 judged best — free roll about the closing axis, used as a nullspace objective — supplies
**exactly one** redundant DoF on a 6-axis arm ⇒ ⛔ **the same single DoF would have to serve both raising σ_min
and clearing the column** ⇒ they may not be simultaneously satisfiable. ⭐ p11 states the budget **before**
anyone picks: *there is one.*

**(b) Its GATED item's evidence has a checkable hole.** The yoke geometry (spread 0.40 m / tilt 20°) rests on
p4's finding that at 0.22 m / 45° the **two arms** interfere (`P4_UR15_HANDOVER_TO_IMPL_CHAIN_20260727.md:73`) —
**arm-to-arm**. ⇒ ⛔ Could **arm-to-yoke** interference have entered that sweep's predicate at all? **If the
predicate was contact-based, in principle no** — those cylinders generate no contacts. ⇒ ⭐ **"0.40 m / 20°
works" may never have been tested against the yoke itself.** ⚠ p11 has not read whether the sweep was contact- or
distance-based and **does not assert it** — it registers the hole in its **own** item's evidence.

⭐ `w2:p5` appended to the banked design with **deletions = 0**, provable by `git diff --numstat` ⇒ no banked
observation, verdict or caveat was altered; new sha `d8a1494d06ea4b8cee9d6dc81fc6a6fec900c1b1cd39be4a08065d59615e2765`
(233 lines), re-frozen pending `w2:p4`'s bank. ⛔ It declines to design the detour while σ_min measurements are
zero, and pre-states the invariant: **a detour must satisfy its condition over the whole path** — citing today's
two endpoint-only failures so the same error is not repeated in the fix.

## 15. ⚠⚠ A conditional path from today's finding to a FOUNDATIONAL invariant — flagged, not triggered

`w2:p11` traced where §12–§14 lead, before anyone re-runs anything:

1. `w2:p5` will treat **stem** and **foot** as real obstacles ⇒ their radii (0.102 / 0.215 m) bear directly on
   **shoulder-region pose selection**.
2. ⛔ The sweep that adopted the yoke geometry (**spread 0.40 m / tilt 20°**) used a predicate that **could not
   see those obstacles** — the cylinders generate no contacts.
3. ⇒ ⭐⭐ **So adding the obstacles is not merely a path constraint: it reopens the yoke-geometry selection
   itself.** The sweep has to be re-run **with the obstacles present**.
4. ⇒ ⚠⚠ **And that can reach a foundational premise.** If the adopted point fails with obstacles, the question
   becomes whether *any* point in the sweep's range survives; if none does, it touches **the 88 mm grasp span and
   the fixed base positions — `RS71-System-Spec-SSOT.md:24`, §0#2** ⇒ ⛔ **Rs-exclusive** (`prohibited.md:18`).

⛔ **Nothing is established as failing.** p11 does not know the adopted point's margin, nor what the 12 swept
combinations covered — the handover records only *"0.22 m / 45° interferes; all 12 failed"*
(`P4_UR15_HANDOVER_TO_IMPL_CHAIN_20260727.md:73`). ⇒ ⭐ Its formulation is the right one: **not "it will fail"
but "we cannot proceed without checking."**

⇒ ⭐ **p18's gate action, stated so it cannot be skipped by accident:** if that sweep is re-run with obstacles and
returns a **different** yoke geometry, that result is **not** a routine parameter update — it is a candidate
**premise change**, and it must reach Rs before it is adopted anywhere. ⛔ Nothing is stopped today, because
nothing is running toward it; what is recorded is that **the quiet path from "re-run the sweep" to "§0#2 moved"
is now closed.**

### 15a. The upgrade smoke passed on the real model, and the two 10 mm appear side by side

`w2:p5` loaded the **assembled THREAD gripper model** under both mujoco 3.8.1 and 3.10.0:
`nq=8 nv=8 njnt=8 ngeom=32 neq=3 nu=1 ntendon=1` — **identical**, and the three `mj_geomDistance` pairs identical.
⇒ ⭐ The model loads on 3.10.0 and the instrument's values do not move ⇒ **upgrade risk down another notch.**
⚠ Scope: **load and static distance only** — solver behaviour, contact, and run reproducibility remain unmeasured,
so the post-upgrade run smoke is still required. ⛔ p5 has not started the upgrade; it waits for p4's explicit
"series complete", not for process counts.

⭐⭐ **And the same output shows §3's axis hazard on the real model rather than on synthetic boxes:**

| pair | separation | axis |
|---|---|---|
| `left_pad1` ↔ `right_pad1` | 85.400 mm | jaw y |
| `left_pad_f1ext` ↔ `right_pad_f1ext` | 75.400 mm | jaw y — **difference 10.000 mm** = 5.00 protrusion × 2 |
| `left_pad_f1ext` ↔ `left_pad_f2ext` | **10.000 mm** | **pad-local z** — the mouth height *within one pad* |

⇒ ⭐ **Two 10.000 mm in one output, on different pairs and different axes.** ⇒ And the parallel-face relation
(claw gap = backplate gap − 10.00) is confirmed on the **assembled model at its default pose**, not just on the
probe's boxes.

### 15b. My near-miss and p11's morning failure are the same shape

- **p18**: a **line-scoped** `grep` against a geom element that **spans two lines** ⇒ nearly reported a false absence.
- **p11**: a `grep` that **assumed attribute order** ⇒ dropped the four class-first cases.

⇒ ⭐⭐ **Same shape: the predicate's unit (a line, an attribute order) did not match the object's unit (an
element).** ⇒ **Discipline: extract the object at its own granularity before asserting absence** — the general
form of `w2:p12`'s rule, and the third distinct way this failure appeared today.

## 16. ⭐⭐⭐ The yoke has no geometry — and that corrects §14's rule at its root

`w2:p5` ran a closed query over every scene-building file at the banked commit:
`ur15_cell.py` holds a `YOKE_SPREAD` constant and `column.add_frame(...)` — **a frame, not a body**;
`ur15_yoke_video.py` has **add_frame 2 / add_body 0 / geoms named "yoke" 0**.

⇒ ⭐⭐ **The Y-yoke exists only as a coordinate frame that offsets the shoulder positions. It has no body and no
geom.**

⇒ ⛔⛔ **So arm-to-yoke interference cannot be detected by any means at all:**

| structure | in the model | contacts? | distance measurable? |
|---|---|---|---|
| `stem` / `foot` | geometry present, **collision disabled** | ⛔ no | ⭐ **yes** — `mj_geomDistance` ignores the filter |
| **yoke** | ⛔ **no geometry** | ⛔ no | ⛔ **no — there is nothing to measure against** |

⇒ ⭐ **The GATED yoke geometry (spread 0.40 m / tilt 20°) could never have been checked against the yoke itself.**
⛔ Not *"it fails"* — **the check was impossible in principle.**
⚠ p5 records without reconciling: this scene's constant is **`YOKE_SPREAD = 0.22`**, a different value from the
GATED item's 0.40.

### 16a. ⛔ This corrects the class rule I adopted in §14 — cause side: p18

My enumeration was *"every geom with `contype`/`conaffinity` zero, plus every `exclude` body pair"*.
⇒ ⛔ **That query cannot find the yoke, because a thing with no geometry leaves no row to find.**

⇒ ⭐ **Third leg, required:** **structures that exist in the design but not in the model.**
⇒ ⭐⭐ And the enumeration's **starting point** has to change: it must begin from the **design-side parts list**,
not from the model. Started from the model, this class is missed **in principle**, not by oversight.

⇒ ⭐⭐⭐ **General form, and it is the strongest version of today's recurring shape:
absence cannot be enumerated from the side of the absence.**
⇒ Today's smaller instances were all the same thing seen through a narrower window — a truncated display treated
as the line, a per-line grep treated as the element, a `grep -c` treated as the fact. ⛔ Each time the query's
own blind spot was invisible **inside the query's output.**

### 16b. Measurements that arrived with it

⭐ **`w2:p4`: the arm does not penetrate the column at the sampled times.** Minimum arm-to-column distance over
STEP 2–8 is **+85 mm to +258 mm — all positive.** ⇒ So §12's concern, **for the column specifically, is not
firing at those instants.** ⛔ Between samples is unmeasured, and the class rule (§14, as corrected) still stands
regardless: the detector is absent whether or not this instance fires.

⭐⭐ **`w2:p4`: σ_min measured, and the asymmetry is large.** Left arm **0.0381** at STEP 3–4 against right
**0.2188** ⇒ **the left arm is 5.7× closer to a singularity.** ⚠ Between waypoints unmeasured, so the valley's
location is not established — which is exactly the sampling `w2:p11` said would be insufficient.

⭐ **`w2:p4` set out its predicate's lineage for `w2:pB`:** ① contact only ⇒ ② + face gap 2–8 mm ⇒ ③ + **the
contact must be on `pad1`**. ⛔ ① is true even while the jaw passes through the cable; ⛔ ② still counts `pad2`
contact, i.e. outside the コ. ⇒ All four Rs-judged videos agree with ③ — ⛔ **but p4 states plainly that this is
calibration, not verification**: repaired on those four and scored on those four, three of which are failures.

## 17. ⛔⛔⛔ The class already has a name in this project, and I re-invented it

`w2:p0` found it and p18 verified both citations on disk.

⭐⭐⭐ **The rule I "adopted" in §14 is `CLAUDE.md:198`'s third bucket — `ABSENT-IN-CODE`**, verbatim:
> 第3 bucket = ABSENT-IN-CODE: 「robust fact」主張は bank 前に mechanism が runtime code で ACTIVE か検証
> （未 wired =「wire-then-validate」= premise FALSE、appearance-only ≠ working）

⇒ ⛔ **`CLAUDE.md` is auto-loaded every session. I formulated as a new rule something already governing, in a
file in my own context.** ⇒ **The day's fourth rediscovery of banked knowledge, and the sharpest.**

⭐⭐⭐ **And `RS71-System-Spec-SSOT.md:55` already carries an instance — about the clip**, verbatim:
> **Collision (⚠ ABSENT-IN-CODE):** the clip boxes are `shape_flags=1` VISIBLE-only — collision is OFF
> (`test_newton_clip_routing.py:958` intent comment / `:971` flag; %3-audit-confirmed ROBUST — not re-enabled …)

⇒ ⛔ **The very object this whole task is about — the clip — has collision OFF in the committed build**, audited
and recorded. ⇒ ⭐ Today's `stem`/`foot` is **not a new class: it is the fourth instance of a class this project
has already banked, tagged, and written the rule for.**

⭐ **`w2:p0`'s enumeration, which shows how little of it we had looked at:** `2f85_koshape.xml` carries **7
`exclude` pairs**, not one — ① `right_pad`/`left_pad` (the only one examined today), ②–⑤ base with the left and
right `driver` / `spring_link`, ⑥⑦ `coupler` with `follower`. ⚠ ②–⑦ are *probably* ordinary suppressions inside
the closed-loop mechanism — ⛔ **and "probably" is exactly what the rule exists to stop**, so p0 enumerates them
without clearing them. Collision-disabled geoms: p4's three cell surfaces × 5 files; the production arm shapes
(`:1581`, `test_newton_clip_routing.py:855`); ⭐⭐ **and the clip** (`:1168 _clip_collide` default 0 ⇒ `:1194`
VISIBLE-only).

⭐ **`w2:p0` also reports that its own multi-line-safe check failed** — its pattern's `[^/]*` could not cross the
`/` inside `{SHOULDER_HEIGHT/2:.4f}`, returning 1 per file instead of 2. Redone element-wise it confirms all five.
⇒ ⭐⭐ **The lesson is not "join the lines" but "parse the element, then test."** Widening a regex around a
just-named hazard **inherits a new hole** — p0 made the same move **inside the correction itself**.

## 18. ⛔⛔⛔ In the production env the two arms do not collide with each other

`w2:p11` read it on disk; p18 verified the range: `mj_left_ss = proto.shape_count` (`:1560`) is taken **before**
the arms are added and `mj_arm_se` (`:1573`) **after both**, so `for si in range(mj_left_ss, mj_arm_se)` covers
**both arms' shapes** ⇒ every non-`pad` shape on **either** arm has `COLLIDE` cleared.

⇒ ⭐⭐⭐ **This hits the yoke geometry's justification directly.** Spread 0.40 m was adopted **because at
0.22 m / 45° the two arms' wrists and upper arms interfere** — ⛔ **and that interference cannot occur in the
production env.** ⇒ **The phenomenon that justified the geometry does not exist in the world that geometry runs
in.**
⇒ ⭐ **So the transfer tag attaches not only to run verdicts but to the geometry's justification**, and further:
**a policy trained in the production env can freely exploit arm-to-arm penetration.**
⛔ Neither p11 nor p18 calls the design wrong — the comment carries its grounds (*probe-proven, F4c*). The claim
is only that **the detector is not on that path.**

⭐ **`w2:p11` narrowed its own earlier claim first**, which is what made this credible: p4's sweep **did** detect
arm-arm interference, which a contact-based sweep could not have under these flags ⇒ **the sweep was probably not
contact-based** ⇒ ⛔ "it could not have seen the yoke" is **too strong**, and my §14b(b) took that too-strong
version. ⇒ ⭐ The question narrows to **whether the yoke's geom was in that sweep's query set** — and §15's gate
holds unchanged under the narrowed form.

### 18a. ⭐ The highest-value unresolved check in the whole session

`w2:p11` half-resolved p0's reservation: on the **`:1392`** side the claws' geom names are `right_pad_f1ext` /
`right_pad_f2ext` — they **contain `pad`** (`2f85_koshape.xml:116-117`) ⇒ they enter `pad_geoms` and **keep
COLLIDE**; the asset `:112-113` says the names were built that way on purpose. ⚠ **The `:1580` side — the Newton
`shape_label` — remains unverified**, and p11 declines to assert.

⇒ ⚠⚠ **Why it matters more than anything else open:** if the claws do **not** fall in the pad set there, then in
the production env **the claws do not collide with the cable at all** ⇒ ⛔ **the capture mechanism — holding the
cable inside the コ — is void on the production path.**
⇒ ⭐ p11 judges this the single highest-value thing to check, and p18 concurs: it is cheap, it is a read, and it
decides whether the approach works in the environment that actually matters.

## 19. ✅ RESOLVED BY READING — the claws keep COLLIDE in the production env

§18a's question — the highest-value item open in this session — is **closed, affirmatively, with no run.**
`w2:p0`, `w2:p5` and `w2:p11` walked the chain independently; **p18 verified every link directly:**

| link | measured |
|---|---|
| production clears COLLIDE on arm shapes whose label lacks `pad` | `newton_skill_env_base.py:1578-1583` |
| `shape_label` **is** the MJCF geom name | `import_mjcf.py:693` — `shape_label = f"{label_prefix}/{geom_name}" if label_prefix else geom_name` |
| unnamed geoms fall back to a **body-derived** name | `import_mjcf.py:597` — `f"{body_name}_geom_{geo_count}{'_visual' if just_visual else ''}"` |
| production loads the LOCK asset | `test_newton_clip_routing.py:161` → `2f85_koshape.xml` |
| claw geom names | `:116` `right_pad_f1ext`, `:117` `right_pad_f2ext`, `:157` `left_pad_f1ext`, `:158` `left_pad_f2ext` |

⇒ ⭐⭐⭐ **All four claw names contain `pad` ⇒ `"pad" not in lbl` is False ⇒ the claws keep COLLIDE and enter
`pad_shape_idx`.** ⇒ **The capture mechanism is ACTIVE in runtime code, not ABSENT-IN-CODE.**
⭐ `w2:p0` closed the unnamed-geom case too: a nameless geom on `right_pad` becomes `right_pad_geom_N`, which also
matches ⇒ **`:1580` and `:1392` agree even for unnamed geoms** — not by design, but because the importer's default
already folds in what the other site adds by hand.
⭐ `w2:p5` checked the queued upgrade: **newton 1.4.0 carries the same rule** (`import_mjcf.py:808`) ⇒ **the env7
upgrade does not break this mechanism.**

⚠ Limits carried forward, unabridged: this was **read, not executed** — no import was run and no label list
observed (⭐ though `CLAUDE.md:198` asks whether the mechanism is ACTIVE in runtime code, and the chain closes at
that level); it establishes only that **the claws collide with the cable** — ⛔ **the arm-vs-structure finding
(§18) is untouched**; and ⛔ **whether the hold physically works is a separate, unverified question.**
⚠ `w2:p5` also excluded a silent failure mode: `:1576` uses `getattr(proto, "shape_label", [])`, so a missing
attribute would empty every label and drop **everything including the pads** to VISIBLE. Measured: newton 1.2.1's
ModelBuilder **has** `shape_label`, so it does not happen here — ⚠ but the idiom would disable the whole mechanism
**silently, by default rather than by exception**, if the attribute were ever renamed.
⚠ `w2:p0` left one detail open honestly: the importer's default appends `_visual`, which also matches `pad`, so a
visual-only geom on a pad body could keep COLLIDE. `add_ur5e_robotiq` passes `parse_meshes=False` so they may not
exist at all — **unverified, and p0 asserts neither way.**

### 19a. ⭐⭐ Two by-products, and the second changes how path checks must be done

**(a) A name that contradicts its value.** `ROBOTIQ_STRIPPED_XML`'s value is `2f85_koshape.xml` — ⛔ the name
reads *"stripped"*, i.e. no claws, while the asset it names **has the コ claws**. ⇒ ⭐ **Reading the name alone,
one would conclude production has no claws.** Today's records-vs-fact shape, in an identifier.

**(b) ⭐⭐ The claws are in physics but not in the FK/IK model.** `test_newton_clip_routing.py:7577-7579`,
verbatim (p18 read it):
> `ROBOTIQ_STRIPPED_XML = the コ-shape claw asset the mujoco physics build loads (test:975/980). The FK/IK model`
> `loads the un-clawed 2f85.xml, but the コ claw is geom-only (no new body/joint) so wrist_3 kinematics --`
> `hence the IK -- are identical; the コ f1ext claw tip (only in physics) drops EE_TO_PINCH_TIP_CLOSED below`

⇒ ⭐ **Kinematics are identical, so the IK solutions are right.** ⛔ **But any geometric check run on the FK/IK
model — clearance, interference, path margin — cannot see the claws.**
⇒ ⭐⭐ This lands directly on `w2:p11`'s singularity/path work: **measuring clearance on the FK/IK side silently
drops the claws' 5.00 mm protrusion.** ⇒ p11 adds it as a design requirement: **path checks must use the
physics-side model.**

⭐ `w2:p11` also reports the **same ABSENT-IN-CODE rediscovery** — it proposed the rule I then adopted — and notes
its own version is the worse one: the three earlier rediscoveries sat *next to a line someone had read*, while
this rule sits in **a file loaded into every session**. ⭐ And it points at the disposition template already in
`RS71:55`: **audit → confirm ROBUST → record "not re-enabled"** ⇒ **`stem`/`foot` should ride that template; no
new disposition needs inventing.**

## 20. ⭐⭐⭐ The model states the court's central finding in its own comment — and a provenance trap

`w2:pB` found both; **p18 verified every number.**

### 20a. Two same-named files, differing by exactly the line that matters

| file | size | `<exclude>` pairs | pad pair present? | sha256 |
|---|---|---|---|---|
| `thread_isaac_lab/assets/…/_ur15_2f85_koshape_actuated.xml` | 10907 | **7** | ⭐ **yes** (`:166`) | `1966631e…` |
| `eval_runs/…/p4_ur15_sim_20260727/_ur15_2f85_koshape_actuated.xml` | 10422 | **6** | ⛔ **no** | `c2d65167…` |

⭐ **The driver reads the assets one** — the producing blob's `:32` pins it absolutely:
`GRIP_XML = "/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml"`

⇒ ⛔⛔ **The copy sitting next to the log is not the model the run used, and the single difference is the one line
that permits claw-claw crossing.** ⇒ ⭐ **Auditing the copy yields the opposite conclusion — "the claws cannot
cross."** Recorded as a provenance trap: **a same-named file beside the evidence, differing only where it decides
the argument.**

### 20b. ⭐⭐⭐ The asset says it, in the comment above that line

`_ur15_2f85_koshape_actuated.xml:161-165`, verbatim (p18 read it):

> `Restored from the banked LOCK design 2f85_koshape.xml:176. Prevents the claw-claw`
> `self-collision jam at the scripted close (the protruding コ claws f1ext/f2ext can`
> `overlap at GRIPPER_CLOSE_QPOS). Cable contact is UNAFFECTED (the cable is a separate`
> `body). **Without this line the opposing claws jam at -0.07mm while pad1 is still 9.98mm**`
> `**open, so the flat pads can never reach the cable.**`

⇒ ⭐⭐⭐ **That is the no-window result, written by the asset's author, with a number.** The court derived it from
geometry across the whole afternoon and measured the claw zero-crossing at **pad1 = 10.16 mm**; the comment says
**9.98 mm** — **0.18 mm apart**, plainly the same phenomenon. ⛔ p18 does not reconcile the difference (different
conditions: the comment describes the jam point with the exclude removed).

⇒ ⭐ **Fifth rediscovery of the day, and it settles the strongest form:** the sim reaches a pad1 gap under 10 mm
**only because the exclude removes claw-claw contact**, and the model says so where the exclude is defined.
⇒ ⭐⭐ **It corroborates the Rs escalation from the author's side rather than from our measurement** — the A/B
branch rests on exactly this sentence.

⭐ pB corrected two things of its own on the way: it had cut its own `grep` with `head -5` and asserted about the
whole block from the cut view (**its second instance today**), and it had cited the run-dir copy as "the model the
banked run read". ⇒ Its **conclusion survives re-verification against the file the run actually reads** (no
collision-disabling on any pad geom — the only disabled item is the visual mesh at `:42`; the exclude is
pad-to-pad, not pad-to-cable ⇒ **contact 0 still means neither touching nor penetrating**), and the claw z-gap of
10.00 mm holds on that file too.

### 20c. The discriminating frame is ready, and it carries a third candidate

`w2:pC` delivered `~/Downloads/pC_WHICH_CYLINDER_f130.png` (f130, t = 4.33 s, wide panel): **A = the thick white
cylinder** (running through the table down to the floor), **B = the thin white tube = the cable**; ⭐ **A is about
25× B's diameter.** ⚠ pC separates its sourcing: it read Ø8 itself (`task_config.py:137`), while the column radius
0.102 is a quotation it has **not** verified. ⛔ It does not assert which Rs meant — it made the question
answerable at a glance.

⭐ **And an unasked-for observation that opens a third possibility:** in that frame **the thick cylinder passes
through the table plate down to the floor.** With `contype=0` no interference is generated, and it may well be
intentional — ⛔ pC judges nothing. ⇒ ⭐ **So Rs's 「円柱のもぶつかっている」 might mean the column against the
table, not the arm against the column** — and the same single frame settles that too.
