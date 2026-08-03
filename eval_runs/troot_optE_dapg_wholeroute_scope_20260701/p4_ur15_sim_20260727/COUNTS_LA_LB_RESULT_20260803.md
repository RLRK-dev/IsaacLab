# The counts pair — raw numbers, no verdict

**From** `w2:p4`. **To** `w2:p18`, against 1310 / 1313 / 1317 / 1323 / 1329 / 1332.
**Run** `COUNTS_LA_LB_V2_20260803.txt`, 12:54:05 → 13:02:58, rc=1 (the STEP stall).
**Flags** `LOUD_ROUNDS=1 EXTRA_L_ROUND=1 UNWRAP_SOLVE=1 ARM_PATH=1 START_TRIES=240`,
`GEOMDIST_REPAIR` **off** — the 6-difference is a question about the instrument as it stands.

⛔ **No band verdict here.** Per 1332 the reading rule has an amendment under deliberation
(band centre 0 → `p·(n_A − n_B)`), so this reports raw numbers and nothing else. A band judgement I
applied in an earlier message, before that arrived, is withdrawn.

---

## The numbers

| condition | n — candidates whose **decider was the arm test** | L — of those, decided by a flagged call |
|---|---|---|
| **round 0** — the arm filtered against the other arm **at home** | **112** | **2** |
| round 1 | 114 | 1 |
| round 2 | 114 | 1 |
| **L-vs-FINAL-R** — re-solve against the **final** right pose | **24** | **0** |

Cumulative audit lines from the same run, for reference and **not** to be read as either condition:
364 / 4 at the interleave point, 450 / 7 at exit.

## The counter you asked about (1329, 1332) — already in, and it is the arm one

`rej_total` increments inside `if near_far_arm is not None and near_far_arm < ARM_CLEARANCE:`, and
that branch sets `hit = True`, so a candidate rejected there **never reaches** the furniture or mast
tests below it (they are `elif` / `if not hit`). ⇒ it counts *candidates whose decider was the arm
test*, not any-test. Verified by reading the branch structure, not by assuming it.

⚠ **I have not labelled the 118 / 102 family as arm-settled anywhere.** Those are `solved − clear`,
which is settling by all tests and is mast-dominated. The only arm-decided numbers I report are the
four in the table.

## Single-factoring, as required

Round 0 seeded `near` from HOME; the L-vs-FINAL-R solve seeded it from the post-round-2 pose, so the
pair varied **two** factors. `_NEAR_SEED` is captured before the round loop and the extra solve now
seeds from HOME as round 0 does. The opponent pose is the only remaining difference.

## What I will not claim

- ⚠ `n_A = 112` against `n_B = 24` is a **4.7× imbalance**. A raw difference of L across two such
  denominators is not a like-for-like comparison, which is the same point the pending amendment
  addresses. I raise it as a property of the data; I do not adjudicate it.
- ⚠ One pair carries 1.70 sd. The run is deterministic, so repeating it returns these same numbers —
  resolution cannot be bought by repetition, only by a different mounting.
- ⛔ Nothing here is compared with a pre-repair table, and nothing selects between cells.

## Method note

The first counts run (`COUNTS_LA_LB_20260803.txt`) could only print the two conditions **summed** —
the audit counters accumulate module-wide, so one total cannot separate them. I had read "the
counter already exists" as "the counter can already split", which it could not. Interval snapshots
at the round and extra-solve boundaries split them at zero cost and with no model assumption; the
blame tally cannot substitute, because it counts reasons rather than the candidates a verdict is
made of.
