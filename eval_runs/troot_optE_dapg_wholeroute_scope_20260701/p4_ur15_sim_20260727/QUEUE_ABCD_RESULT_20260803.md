# The queue, measured — and (a) turns a vacuous bound into 4.674 %

**From** `w2:p4`. **To** `w2:p18`, against the queue in 1232 (a), 1225 (b), 1235 (c), 1242 (d).
**Run** `QUEUE_ABCD_20260803.txt`, 11:41:03 → 12:06:54, rc=1. **Flags** `UNWRAP_SOLVE=1 ARM_PATH=1`,
`GEOMDIST_REPAIR` **off** — attribution is measured against the instrument as it stands.

---

## (a) Rejection attribution — the number the bound could not give

> of **599** candidates dropped by the arm-clearance test, **28** were dropped by a call the floors
> had already flagged — **4.674 %**

⭐ This replaces an upper bound that was vacuous: at 1,444 pairs per call the C·k·p product exceeds
the candidate pool, so it could not distinguish "possible" from "happened". Now 6 and 16 can be
compared against a measured width instead of an unusable one.

⚠ What it is not. It counts candidates whose **deciding minimum** carried a flag. A flagged call
that was not the minimum, or a flag on a candidate that would have failed anyway, is not in it. It
is the rate at which contamination **reached the verdict**, not the rate at which it existed.

## (b) Violations per candidate evaluation

**2,496** candidate evaluations; **17.23** violations per evaluation.

⭐ Read the two together: a candidate touches ~17 contaminated calls on average, and 4.674 % of
rejections were actually decided by one. **Touching is not deciding** — reasoning from 17.23 alone
would have overstated the leak by more than an order of magnitude. That is exactly why (a) had to be
a measurement.

## (d1) `seg_under` split by what the scalar claimed

| | count |
|---|---|
| asserted **CONTACT** (`dv ≤ 0`) — answerable by the contact list | **28,522** |
| merely too narrow (`dv > 0`) — a magnitude error the list cannot speak to | **50** |

⇒ **99.8 % assert contact.** The sign reference therefore addresses nearly the whole class, which is
what turns "94 % unreferenced" into the accurate "94 % with no reference **for magnitude**".

## (d2) Sign reference — it caught things, at no extra distance call

> **705** minima cross-checked against the solver's own contact list — **65 ghosts** (asserted
> contact the solver does not record), **0 misses** (asserted clearance over a pair the solver *is*
> contacting)

⭐ 65 cases where the instrument said "touching" and the solver's own contact list disagreed. Free,
per p5's design: the selector already runs `mj_forward` and `arm_pair_min` on the same scratch.

⚠ Bounds neither way, and the reason is structural, not a caveat added for safety: contacts exist
only inside the margin band, and the list is per geom pair while the minimum is one pair.
⚠ **The jaw channel is invisible to it** — `jaw_gaps` measures `pad↔pad`, which is exactly the
excluded pair. Verified separately: of the 64 arm-vs-arm pairs `arm_pair_min` compares, **0** are
excluded, so no false ghost can arise from exclusion there.

## (c) Pair tally, whole

1,529 distinct pairs, all now printed rather than the head six — which were 0.4 % of it. The
distribution is the input to the common-mode versus independent read.

## Floor 1 with its own denominator

**8,563,740** calls (85.75 % of unsaturated) had bounding spheres far enough apart for the bound to
mean anything. Within that visible domain the rate is **0.1677 %**, against 0.1438 % on the whole
population. ⚠ Outside it — 14.25 % of calls — the bound is vacuous and a clean sheet from floor 1 is
not evidence.

## Unchanged from the earlier runs, as controls

Channel rates (`arm_pair_min` 0.27692 %, `column_gap` 0.02067 %, `jaw_gaps` 1.51355 %) and the
type-pair rates (MESH×MESH 0.44444 % highest; CAPSULE 0/596,494) reproduce the previous run exactly.
Coverage is unchanged: `furniture_gap` and `release_ctrl` never asked, `gap` asked 13 times.

## ⛔ Two hazards found while answering, neither fixed

1. **`mouth_clear()` is defined twice** — same body at two places, and **the later definition binds**.
   Editing the earlier one has no effect. The holding gate `_half` derives from this function's
   return, so a half-applied edit here would be silently wrong rather than loudly wrong.
2. The mouth-opening custody question (2 mm, 14.00 → 16.00) is with Rs. Its consequence — the
   holding gate loosening from 3.00 to 4.00 mm per side — was **not** recorded in the commit that
   caused it, though the same author recorded the equivalent consequence for the preceding change.
