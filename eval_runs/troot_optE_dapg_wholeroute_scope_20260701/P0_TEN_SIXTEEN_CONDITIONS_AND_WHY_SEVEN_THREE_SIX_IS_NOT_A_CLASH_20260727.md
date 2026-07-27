# P0 — 10.16 restated with its conditions, and why the run's 7.36 does not contradict it

date: 2026-07-27 (measured at dispatch; see message timestamp)
author: w2:p0 IMPL-BUILDER (measurement material only — no implementation, no run)
in reply to: MSG-P18-188 §6 ("10.16 を どの条件下で測ったかを添えて再掲")
scope: read-only. Nothing here re-judges Rs's visual verdict.

---

## 0. The answer in three lines

- **10.16 mm is not mine and is not a sim stop.** It is **p4's sweep measurement**, recorded by
  p5 as **"実機の顎の停止点"** — the gap at which the claws would touch **in hardware**.
- **The sim has no such stop**: `<exclude body1="right_pad" body2="left_pad"/>` removes *every*
  geom pair between the two pad bodies — claw-to-claw **and** pad1-to-pad1. Nothing but the
  cable stops the close, so the faces land just under Ø8.00: **7.36 / 7.44 measured**.
- ⇒ **7.36 < 10.16 is expected, not anomalous.** Two correct numbers about two different worlds.

---

## 1. 10.16, restated with attribution and conditions

| what | value | where |
|---|---|---|
| producer | **p4's ctrl sweep** (not p0, not p11) | `P5_PHASE_A_STEP1_5_DETAIL_DESIGN_20260727.md:27` "(実測 / p4 sweep)" |
| what it measures | pad1 face-to-face gap at which **the claws touch first** | `P11_UR15_DESIGN_DISPOSITION_20260727.md:1264` |
| the margin it implies | claws touch **5.6 counts earlier**; backplate is then **2.16 mm** short of Ø8 (1.08/side) | same `:1264` |
| tilt during the sweep | the two claw pairs differ by a **constant 0.68–0.70 mm** ⇒ **θ = 1.57°** | same `:1264` |
| range and behaviour | **ctrl 205–240, monotone** | same `:1264` |
| cross-check | at ctrl 219.16, p11 predicts 10.11 vs measured **10.16** = 0.05 mm | `:1273` |
| **which world** | **実機 / hardware.** p5: "実機の停止点は pad1 面間 10.16 mm (爪が先に当たる) ⇒ 4.0 mm は実機で到達不能" | `P5...:85`, and `:151` |

My own contribution to this number was only the **bound** it confirmed: the worst claw pair
protrudes ≥ 4.0938 mm/side over the admissible tilt range ⇒ contact at backplate gap
≥ **8.188 mm**, which 10.16 satisfies (`P0_CLAW_WINDOW_GEOMETRIC_BOUND_20260727.md:144`).

⚠ Not established from the record and therefore not claimed: whether the sweep ran with the
cable present or absent. `:1264` describes a geometric touch-first ordering, which does not
need the cable, but I did not find that stated.

---

## 2. Why the run's 7.36 / 7.44 is not a clash — measured today

`thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml:166`
(and banked LOCK `2f85_koshape.xml:176`, identical):

```
<exclude body1="right_pad" body2="left_pad"/>
```

And the claws are **geoms of those very bodies** (`:95-97`):

```
<body name="right_pad" ...>
  <geom name="right_pad_f1ext" .../>
  <geom name="right_pad_f2ext" .../>
```

⇒ a MuJoCo `<exclude>` on a **body pair** removes every geom pair between them. So in this
model the opposing **claws cannot contact each other, and neither can the opposing pad1
faces**. **The 10.16 mm claw stop has no way to act.**

⇒ the only body left to stop the close is **the cable**. With Ø8.00 and some compression the
faces settle just under 8.00 — the run reports **L +7.36 / R +7.44 mm**. That is the
predicted behaviour of a jaw with its own stop removed, not a violation of the stop.

### 2.1 This was already derived, and only its *check* was retracted

`P11_UR15_DESIGN_DISPOSITION_20260727.md:1278` states the mechanism verbatim:

> sim では爪の contact が `exclude` 済ゆえ爪では止まらず、唯一止めるのはケーブル
> ⇒ 背板 ≈ 7.6 mm で停止

p11 then retracted at `:1337` — correctly — because the "0.01 mm agreement" was an **identity**:
the stop gap 7.59 had been *solved from* the datum (7.59 = −2.57 + 10.16), so the residual
could not have come out otherwise. **One free parameter fitted to one number.**

⭐ What was retracted was the **check**, not the **mechanism**. And the check can now be
replaced by one that is not a fit: p11's ≈7.6 came from an **old datum**; p4's wide14 run
measures **7.36 / 7.44** independently, on a different run, with nothing fitted between them.
Agreement to **0.15–0.23 mm** is therefore evidence in a way the 0.01 mm was not.

⚠ The two runs are not on an identical model — the mouth was widened between them. But the
widening moved the claws in **z only** (`y = -0.0026` and `size` unchanged in all 8 geoms;
verified in the `f11273d5be` diff and re-derived from the asset), and 10.16 / 2.16 / 1.08 are
**closing-axis (y)** quantities. p5 states the same at `P5...:323`. So the comparison holds.

### 2.2 The residual I cannot close

Predicted claw overlap at the measured face gaps: **7.36 − 10.16 = −2.80** and
**7.44 − 10.16 = −2.72**. The log reports **−2.45** and **−2.43**. So **0.35 / 0.29 mm** unexplained.

A candidate: the log prints one claw number while `:1264` measures the two claw pairs
**0.68–0.70 mm apart**, so reporting the shallower pair (or a mean) would move it by ~0.34 mm.
⛔ I am not asserting that. It is the same shape as the fit p11 was caught on, and the number
that would make it convincing is half of a number already in play — which is exactly when a
match means least.

**What would discriminate:** whether the driver reports the min, the mean, or a named pair.
⛔ I cannot read that: the source that produced `ur15_wide14.log` is not on disk and is in no
commit on any ref (`P0_WIDE14_ASSET_AND_LOG_PROVENANCE_20260727.md` §2). The two open items
are the same item.

---

## 3. The consequence p18 asked me to cross with p5's observation

The clamp predicate, as printed by the run (`ur15_steps_reaim.py:906`, nearest driver):

> `needs both pads AND a 2-8 mm face gap`

| world | face gap at close | inside [2, 8]? | predicate |
|---|---|---|---|
| **sim** (claw contact excluded) | **7.36 / 7.44** | yes | **True** |
| **hardware** (claws stop it) | **10.16** | **no** | **False** |

⇒ **the clamp predicate passes in sim precisely because the sim lacks the claw stop.** On
hardware the same predicate, unchanged, returns False at the stop. The run's own log already
flags the direction: `opposing claws -2.45 mm <- NEGATIVE: non-conservative for transfer`, and
`touch alone passed on a jaw that had closed through the cable`.

⚠ Conditional on: (i) 10.16 being the true hardware stop, and (ii) the band being `[2, 8]` as
printed — and (ii) carries the same provenance gap, since `:906` lives in a file that did not
write that log.

⛔ This says nothing about Rs's verdict. Rs judged the video and the video shows what it shows;
physical validity is Rs's alone. This is about **what would transfer**, which is a different
question from **what happened in the sim**, and p18's §6 is right that the mechanism of the
success needs to be established rather than assumed.

---

## 4. What does not move

The widening was z-only, so **2.16 mm (1.08/side) is unchanged** and the closing-axis shortfall
is exactly as p5 states. Widening the mouth did not narrow it by a millimetre. Those are
orthogonal axes and remain so.

---

## 5. What I am asking for

1. **p18** — 10.16 is restated above with producer, conditions and world. The clash in §6
   dissolves into "hardware stop vs sim without that stop"; no measurement is missing to close it.
2. **p11 / p4** — if the claw-pair reporting convention is recoverable, the 0.35 mm residual
   closes with it. It needs the producing source, not a new run.
3. Nothing else. gate unchanged, no run, no implementation.
