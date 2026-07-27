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

### 10a. ⭐⭐ Rs's own words bear on the grasp/capture branch — placed here, not adjudicated

Relayed verbatim by `w2:p4` (⛔ p4's relay of Rs, not p4's reading):

> 爪の上下の隙間は問題ない、**左右で摩擦が生じれば**ケーブルをコ内に固定できる
> 逆に**上下をきつくしすぎると**ケーブルをクランプしずらくなる
> 単にコがケーブル位置にいっていないだけだ。**物理的にクランプ可能**

⇒ ⭐ The hold Rs describes is **left–right friction — compression**, not clearance-based containment.
⇒ ⚠ So `w2:p11`'s ruling (a correctly captured cable touches nothing ⇒ a contact predicate is false exactly when
the goal is met) is right **about capture**, but the state Rs calls clamped appears to be **the compression side**.
⛔ p18 does not decide this; the predicate is p11's court and the final call is Rs's. The verbatim is placed on
the branch, nothing more.
⇒ ⚠ Separately, "tightening the top and bottom makes it *harder* to clamp" reads against **option B** (reducing
claw protrusion) from the mechanism menu. Also placed, not decided.

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

⛔ **Correction to my own relay first (cause side: p18).** In `-121 (2)` I relayed p4's account that the predicate
went from *contact only* → *contact + band 2.0–8.0*. `w2:pB` read the **producing blob** (`b06c5334`, commit
`e9f93a7556`) and found **the band was already in `grasped()` when this log was made.**
⇒ ⭐ **This log's `clamped=True` was produced by the banded predicate, not the contact-only one** ⇒ **the band did
not remove R's True.** ⇒ I relayed a before/after story about code without reading the code at the commit that
produced the evidence — the failure `feedback-verify-on-disk-at-the-producing-commit-not-at-head` names exactly.

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
