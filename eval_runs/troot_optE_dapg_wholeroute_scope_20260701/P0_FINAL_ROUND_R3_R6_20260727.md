# P0 — final verification round: R3, R6, the z three, and the controls

date: 2026-07-27 22:5x JST (measured)
author: w2:p0 — verifier of the UR15 lane
targets (-444): R3 @ `c7c799c150`; R6 @ `e2b8979f5b` + `50fb6a8259` + `ee13ed33c8`; the z three
numbers; the positive/negative control pair (`r6_positive_result.txt` sha `89a3fd87a6d7a34ec8ae6fc2…`
— re-derived, matches).
method: re-ran **both** control programs end to end; probed the fixed point with 8 seeds; read R3's
aim path, the z-three implementation and the datum convention.

---

## 0. Verdict

| item | verdict |
|---|---|
| positive leg, independently re-run | ✅ **reproduces, 5/5 lines identical** — `held() = True` |
| negative control, independently re-run | ✅ **reproduces byte-for-byte** |
| release floor, seed-independence | ✅ **8 seeds spanning 0→100 all give 18.1875** |
| R3 — aim with `fix_x`, y/z only, residual printed | ✅ present as described |
| the z three numbers | ✅ present, and measured through the phase's own path |
| datum sign (pad-z large = world down) | ✅ consistent |
| **the negative control's discriminability** | ⛔ **the jaw is never brought to the cable, so one leg is pinned False in all four rows** |
| **the negcontrol docstring** | ⛔ **promises a `True` the run does not deliver** |
| **a third value under p18's own criterion** | ⭐ **7.44 mm, outside the declared band 6.67–7.36** |

---

## 1. ✅ Both controls reproduce, and the predicate has now been True

Re-running `r6_positive.py` gives all five lines identical to the banked file — `seat error 2.90`,
`backplate 79.89` open, **`backplate 6.67 (floor 18.19) -> past floor=True`**, `pad-local z 29.02
in band -> True`, **`R6 held() = True`**.

⇒ the *"a predicate that has only ever returned False"* problem is **resolved**: it has returned
True on a case that is not the task claim but instrument evidence, which is the right kind.

Re-running `r6_negcontrol.py` reproduces its four rows byte-for-byte.

## 2. ✅ The floor is a fixed point, not a seed

| seed (mm) | 0 | 2 | 5 | 10.20 | 15 | 25 | 50 | 100 |
|---|---|---|---|---|---|---|---|---|
| floor | 18.1875 | 18.1875 | 18.1875 | 18.1875 | 18.1875 | 18.1875 | 18.1875 | 18.1875 |

⇒ across a 0→100 mm span of seeds the answer does not move. The docstring's claim
(`18.20 → 18.19 → 18.19`) understates it: it is not merely convergent from a nearby seed, it is
**invariant over every seed tried**.

## 3. ✅ R3, the z three, and the datum sign

- **R3**: `aim_slot_at(..., fix_x=...)` at `:567`/`:582-583`, called at `:620` with
  `fix_x = GL[0] if t=="L" else GR[0]` ⇒ x pinned, y and z solved, residual printed. As described.
- **the z three** (`:1325-1341`): `required` is *this* re-grasp's own offset, with an explicit
  ⛔ *"not the 8.7 mm from the judged run, which was a different span on a different cable"* —
  the scope I asked for is written into the code. `available` is measured by **re-solving at
  offset targets through the same path the phase uses**, not taken from the solver's self-report,
  and the difference is printed as *"printed, not a verdict"*.
  ⭐ The `pose_only` misuse is recorded as a caught defect in the source itself: *"My first version
  passed a position as `pose_only`, which selects an ATTITUDE INDEX — it would have reported a
  number that measured nothing."*
- **datum sign**: open `pad-local z = 34.49` (near f1ext's inner face, 39.00) → closed
  `29.02` (toward f2ext's, 25.00). The cable settles **downward in the mouth** as the jaw closes.
  ⇒ consistent with *large pad-z = toward the upper claw*, and physically what a cable resting onto
  the lower claw should do.

## 4. ⛔ The negative control does not demonstrate discriminability

Its four rows, with the mouth band at **25.00–39.00**:

| state | claw | **mouth z** | in band | held |
|---|---|---|---|---|
| wide open, nothing between | 69.87 | **−169.06** | False | False |
| half closed | 1.81 | **−163.92** | False | False |
| clamped | −6.42 | **−161.99** | False | False |
| cable moved away, jaw CLAMPED | −6.42 | **−209.92** | False | False |

The **claw** column varies properly (69.87 → 1.81 → −6.42), so that leg responds. But **mouth z is
160–210 mm outside the band in every row**, because this program never brings the jaw to the
cable — the positive does that (`aim at the resting cable`), and the negative control does not.

⇒ **the band leg is pinned False before the jaw state can matter**, so `held` cannot flip whatever
the claws do. The four rows are one negative repeated: *the cable is not in the mouth*. Row 4
moves it further away (−210 vs −162), but it was already out.

⇒ **no single setup shows the predicate going True → False as a state changes.** The positive
(aimed) is True and the negatives (unaimed, ~200 mm away) are False, and the dominant difference
between them is **where the jaw is**, not what it is doing.

⭐ **What would close it, cheaply:** run the same four states *from the positive's aimed pose*.
Then `in band` starts True, the claw leg alone decides, and the flip is visible in one table.

## 5. ⛔ The negcontrol's header promises a `True` the run does not deliver

`r6_negcontrol.py:8`, verbatim:

> *half closed on the cable -> tips 1.8 mm, cable inside -> **must be True***

The table reports that row as **False**, with its `expect` column set to `-` rather than `True`.
The file's own note at `:37-39` explains why — *"The positive case is NOT here: placing the cable in
the jaw moved it further away (491 mm)"* — but the docstring at `:8` was not brought into line
with it.

⇒ the header states an expectation the body says cannot be met. Same class as the `66.67` contract
text and the `known` docstring: **prose asserting a behaviour the code does not have.** One line.

## 6. ⭐ A third value, under p18's own falsification criterion

-447/-450 pre-registered the achieved clamp as a band **6.67–7.36** and said a *third value* would
be a real finding. There is one, and it is in the same banked log:

```
ur15_wide14.log  GRASP L: pad faces  +7.36 mm
ur15_wide14.log  GRASP R: pad faces  +7.44 mm
```

Same quantity, same run, the **other arm**. **7.44 > 7.36**, so the band's top is understated.

⇒ this is not a contradiction of the pre-registration — it is a correction to its endpoint before
it is written: **6.67–7.44**. And it strengthens the reason for making it a band at all, since the
single 7.36 in §12-1 was already omitting its own run's second arm.

⚠ Not flagged, per -447/-450: §12-1's single value and §13-5's instrument note are declared stale
and are being rewritten. Only the endpoint above is offered as new.

## 7. Scope

**Did**: re-derive the positive's sha; re-run both control programs to completion and compare every
line; probe `release_floor` with 8 seeds; read R3's aim path, the z-three implementation and the
`pose_only` correction; check the datum sign against the asset's claw faces; compare the achieved
clamp values across the banked log.

**Did not**: run the route (no authorisation, and none needed for the above); judge whether R6 is
the right predicate for the task — the positive is instrument evidence, not a task claim, as -444
states; assess the `FLOAT_Z` freeze; re-verify items closed in earlier rounds.

⛔ No implementation, no route run.
