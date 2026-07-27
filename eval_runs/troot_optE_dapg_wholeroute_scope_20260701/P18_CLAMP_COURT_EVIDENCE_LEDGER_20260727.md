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

## 5. ⛔ Still open — one item, and it must not be quietly closed

**The old datum −2.57 exceeds p0's 2.400 mm bound by 0.17 mm.**

- `w2:p0`: states plainly that it has no explanation for the excess and declines to construct one.
- `w2:pZ`: computes that a 1.571° relative tilt raises the floor to −2.647, which would bracket the observed
  −2.57…−2.62 — but **declines to claim fit**, because the exact minimum-translation distance for tilted box
  pairs was not computed. Recorded as *order and mechanism agree, residual 0.17–0.22 mm uncomputed*.

⇒ ⭐ **OPEN.** Nobody has explained it, and two panes have explicitly refused to pretend otherwise. That is the
correct posture and this ledger keeps the item alive rather than absorbing it into the settled account.

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
