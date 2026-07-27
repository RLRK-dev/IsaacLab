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

### 5b. A discriminator nobody has used yet

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
