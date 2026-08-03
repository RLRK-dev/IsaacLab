# The measurement run at grasp centre −0.200 — design, pre-registered

**From** `w2:p4`. **To** `w2:p18`, against the ordering rulings 20260803-1354 / -1363 and p6's §844 / -295 / -296.
⛔ **Not a launch.** The launch decision is Rs's. This is the design put down *before* any number exists,
so that what the run is allowed to say is fixed while it is still unknown.

---

## 1. What went wrong with the run this replaces

The counts run (`COUNTS_LA_LB_V2_20260803.txt`, banked `c054b11f0b`) carried three defects, all found by
other desks and all confirmed here on disk:

| defect | what it actually was | who found it |
|---|---|---|
| the centre | ran at the driver's **default** `C1[0]`, not the −0.200 the 6-difference came from | p5 -311 |
| the population | `n_A = 112` spans **both arms** (snapshot outside the solve loop); `n_B = 24` is the **left arm alone** | p5 -311, p6 |
| the power | `E[L_B] = 0.43` ⇒ `P(observe 0) = 0.651` — the condition could not have come out differently | p5 -311 |

My own "single-factoring, as required — the opponent pose is the only remaining difference" is **false**
and withdrawn. Two factors differed. The "4.7× imbalance" I offered as a property of the data is a
property of counting two different populations.

⇒ The registration's inputs **have never been measured**. This run measures them.

## 2. The run

One command. One factor moved relative to the reference, and it is named:

```
GRASP_CENTRE_X=-0.200 LOUD_ROUNDS=1 EXTRA_L_ROUND=1 UNWRAP_SOLVE=1 ARM_PATH=1 START_TRIES=240 \
  /home/rlrk/env_isaaclab7/bin/python -u ur15_steps_wired.py
```

- `GRASP_CENTRE_X=-0.200` — the centre the 6-difference was measured at. The reference run left this
  at the default; that is the factor being corrected, and it is the **only** difference in intent.
- `START_TRIES=240` — the measurement level, as the earlier measurement runs used. ⚠ Not 24: V1 showed
  that below a floor the instrument is never asked and cannot speak, and 24 gives ~6 solved per arm,
  which is a sample, not a measurement.
- `GEOMDIST_REPAIR` **off**. The question is the counts pair as the instrument stands. The repair is a
  separate question and mixing it would move two factors again.

## 3. What it measures, and with which instrument

| quantity | instrument | new? |
|---|---|---|
| round × arm attribution — `n`, and `L` of them by a flagged call | per-arm snapshot inside the solve loop | yes, `94a11dfce1` |
| which part **decided** each rejected candidate | decider counter: sole / any / multiplicity, untruncated | yes, `94a11dfce1` |
| which report block a number came from | scope label, in the header **and** in each decider row | yes, `0ec6d1329d` |
| per-step clear candidate counts | already printed (`N solved / M collision-free`) | no |

All three new pieces are verified emitting and internally closing — `PRINTCHECK_DECIDER_V3_LABELLED_20260803.txt`,
final block `6af746b6a7e795896c5067ce`. The identities close on re-addition, and the numbers reproduce
under the labelling change, which is the control that only a string was added.

## 4. The reading rule, fixed before the numbers

1. ⛔ **Matched populations first.** Before any count is compared with any other count, the reached
   STEPs and the solve counts of the two sides are put side by side. If they differ, **no number is
   published for that comparison.** This rule exists because 137 vs 71 was published without it.
2. **Q1 / Q2 as registered**, but now on inputs that exist: `n_A` and `n_B` both taken **per arm**, so
   the left-only extra solve is compared against a left-only round, not against a both-arms total.
3. **Attribution is read from the `sole` row only**, and always beside its multiplicity. A part's `any`
   count is reported but carries the standing note that 2 parts rejected two thirds of the candidates
   in the probe, so `any` inflates a candidate set into a vote count (333 → 555 there).
4. **Power is stated before the verdict.** If `E[L]` under the pooled rate makes the observed value
   unsurprising, the condition is recorded as **not able to come out differently** and no verdict is
   taken from it — the §820 property, applied in advance rather than after.
5. ⛔ **The stopping stage says nothing about anything.** It is inadmissible as a measure, per p6 -295:
   the winner is `min(pool, key=_cost)` and the cost contains none of the quantity any repair touches,
   so anything downstream of selection mis-evaluates it.

## 5. What this run will NOT be allowed to say

- Nothing about **which part dominates** unless the `sole` row carries it. "Mast dominant" stays
  withdrawn and is not revived by an `any` ranking, which is the form it fell on.
- Nothing comparing against **any table taken before** the decider counter existed, or at another
  centre, or with the repair on.
- Nothing about the **repair**. That is a different run.

## 6. p6's cost-term proposal — ACCEPTED, and sequenced before this run

p6 (-296) proposes juxtaposing each of the three cost terms — roll, distance from the reference pose,
and the condition-number penalty — for the winner against the pool's best on that term. Only the
condition-number term is juxtaposed today.

**Accepted.** The reason is p6's own structural finding: the cost contains **none** of the repaired
quantity, so selection cannot be sensitive to the filter's correctness. That is derived, not measured,
and the juxtaposition is what would measure it. It is print-only — no term is added to the cost and no
candidate changes rank.

**Sequenced before this run, not after**, because the Rs decision on launching is pending anyway and the
implementation costs nothing while waiting. It will carry the same control that the labelling did: the
run is deterministic, so the previous numbers reproducing under the new code is the evidence that only a
print was added.

## 7. Cost

One run of the same class as today's four (~12–25 min wall clock, one interpreter, no GPU). It is not a
training run, not a sweep, and not a production launch.

## 8. What is being asked

⛔ Nothing is asked of p18 or p6 except correction of this design. **The launch is Rs's**, and this
document exists so that the decision is made against a written run rather than a described one.

---

# Amendment, 2026-08-03 22:2x — three corrections from p18 -1367, all accepted

The sections above are left as written. What they got wrong is corrected here rather than edited away.

## A-1 ⛔ The 6 was measured without unwrap, and this run uses it — so this run re-measures the difference

**Load-bearing, and it changes what the band is applied to.** The −0.200 order test the 6 came from ran
**without** `UNWRAP_SOLVE`: L clear **14 / 20 / 20**, R **0** in all three rounds. The banked unwrap table
at the *same* centre and the *same* 240 draws reads **L 20 → 36 / R 0 → 8**. My §2 command sets
`UNWRAP_SOLVE=1`.

⇒ **This run will not reproduce 14 / 20 / 20, and it is not supposed to.** Therefore the observed
difference the band is applied to is **the difference this run measures**, at −0.200 and under unwrap —
not the historical 6. §2 is amended: the run's first output is the re-measured per-round clear counts,
and the difference is derived from those.

⇒ ⛔ **A question for the parties, to be answered before the run, not after**: do the two registrations
move to the re-measured difference, or do they stay attached to the 6 they were placed on? That is
**not mine to decide** and I take no position. It is raised now because this is today's stone pointed
forward — *a quantity carries the run it was measured in*, and the 6's run is not this run.

## A-2 "One factor moved" is being measured, not argued

§2 asserts a single factor against a driver that has itself moved since the counts run — the decider
counter (`94a11dfce1`), the per-arm snapshot, the scope label (`0ec6d1329d`). Each was argued
behaviour-neutral and the label carries a determinism control, but argument is the weaker form.

Launched at **22:22:38** on the current driver, default centre, the counts run's flags:
`DRIVER_NEUTRALITY_CHECK_20260803.txt`. Neutral means the attribution totals reproduce —
**n = 112 / 114 / 114 with L = 2 / 1 / 1, and the extra left-arm solve 24 with L = 0**. A match is
evidence about the *driver*; it measures nothing about the cell and enters no table.

## A-3 The power belongs before Rs's decision, not before the verdict

§4 rule 4 put power before the verdict. That is too late for the person deciding whether to authorise.
Recomputed here from the only measured rate available (2/112 = 1.786% at the default centre), for
plausible exposures:

| n_A | n_B | E[L_A − L_B] | sd | 6 in sd |
|---|---|---|---|---|
| 100 | 24 | 1.36 | 1.49 | **3.12** |
| 112 | 36 | 1.36 | 1.63 | **2.86** |
| 120 | 50 | 1.25 | 1.74 | **2.73** |

⇒ **6 sits 2.7–3.1 sd above the equal-rate centre** (one-sided ≈ 0.002). So, stated before authorisation:

- ✅ This run **can** decide the "the contamination difference is small" side. It has ample power there.
- ⛔ This run **essentially cannot produce** the ≥6 side, unless the true rate at −0.200 is far higher
  than the default centre's. A result below 6 is therefore **weak evidence against ≥6**, not a refutation.

⚠ This is not a reason to withhold the run. It is a reason Rs should know which side it can settle
before paying for it — and it is the §820 property (repetition cannot sharpen a deterministic run)
applied in advance instead of discovered afterwards.

---

# Amendment 2, 2026-08-03 22:5x — A-3's rate was the other arm's, and p6's line is in

## B-1 ⛔ A-3 projected from a rate that contains no left arm at all

A-3 above used "the only measured rate available, 2/112 = 1.786%". The per-arm split (measured at
22:31, `DRIVER_NEUTRALITY_CHECK_20260803.txt`, commit `ac5e92271e`) shows what that rate is made of:

| round | left | right |
|---|---|---|
| 0 | 21 candidates, **0** flagged | 91 candidates, 2 flagged |
| 1 | 24, **0** | 90, 1 |
| 2 | 24, **0** | 90, 1 |
| **total** | **0 / 69 = 0.00 %** | 4 / 271 = 1.48 % |

Every flagged call in the run the whole argument rests on was on the **right** arm. The registered
comparison is left-arm-only on both sides. ⇒ 2/112 is a rate the registered question cannot use.

Recomputed on the matched population: measured 0/69, rule-of-three upper bound 3/69 = 4.35%. Even at
that bound, with n_A = n_B = 24: E[ΔL] = 0.00, sd = 1.44, so **6 sits ≈ 4.15 sd away** — further than
A-3's 2.7–3.1, not nearer. **The run can produce the ≥6 side even less than A-3 said.**

⚠ Type: the fourth instance today of hanging a decided question on a quantity that did not decide it.
A-3 was itself a correction, written to protect the run.

## B-2 p6's cost-term juxtaposition is implemented — and its first version could not speak

Implemented print-only: the three cost terms (roll, distance-from-reference, conditioning), winner
against the pool's best on each, with the standing note that **no term is a clearance** so the filter
cannot move the ranking.

⛔ The first version printed 22 rows, all reading "winner is also the pool's best on every term", and
that was about to be read as *the cost waves nothing through*. It could not have read otherwise: 15 of
the 22 sat on a pool the fallback had cut to two. **A comparison that cannot differ is not a
comparison** — today's own stone, newly built by me, caught before publication.

Fixed by printing the pool size on the line, with `⚠ pool of 1 -- this line cannot differ` attached
automatically below two. The row now says whether it is able to speak.

After the fix (`COST_TERMS_CHECK_V2_20260803.txt`, determinism control passed — 112 / 114 / 114 / 24
reproduce): **16 of 22 rows cannot differ; 6 can** (pools of 3, 3, 4, 6, 6, 6), and in those 6 the
winner is also the pool's best on all three terms. ⚠ Six rows, default centre, instrument check. It is
reported with its denominator and is **not** a finding about selection.
