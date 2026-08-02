# Package notes — the four items p18 put in my court (`-936 §2`)

⛔ None of this needed a run. It is code read at `ur15_steps_wired.py` and stated so that a reader
does not have to re-derive it. Where the answer is "a measurement is needed", the measurement is
named rather than replaced with an explanation.

---

## (a) Are the printed `solved` / `collision-free` counts the final round only?

**Yes.** `START[t] = solve_ik(..., quiet=(_round < 2))` (`:1712`) inside `for _round in range(3)`
(`:1705`). `quiet` suppresses the count line, so rounds 0 and 1 print nothing and **every printed
count is round 2** — the last one.

⚠ Two consequences worth carrying:

1. The counts describe the solve that produced the **final** pose, which is the right one — but the
   final pose was reached through two earlier solves whose counts nobody sees.
2. The fallback disclosure is **not** gated on `quiet` (`:1574`), so it prints on all three rounds.
   That is why a log can carry three "NOT ONE of N candidates cleared" lines and one count line,
   and why the N in those lines can differ from the printed `solved`.

---

## (b) p5's 4 vs 5 — what measurement settles it

p18: *"一致は説明を作る理由にならない — 説明でなく測定を"*. Agreed, and the same applies to the
disagreement. The seeding is settled (`default_rng` at `:1415`, no `seed` argument at the `START`
call site), so an identical configuration must give an identical survivor set.

**The measurement.** The driver already prints **every** clear pose, not only the winner
(`clear #k: q = [...] sigma ...`, `:1651-1655`). So the two runs' survivor sets can be compared
directly:

1. take the `clear #k` lines from each run;
2. compare the `q` vectors as a **set**, not the counts;
3. read off which case it is —
   - one set is a subset of the other ⇒ a sampling difference, and the extra pose is nameable;
   - the sets are disjoint or partly so ⇒ the two runs are not solving the same problem, and the
     `near=` / `other=` chain is where the difference entered.

⚠ **The print is capped at 40** (`_strict[:40]`, `:1651`; the overflow is announced at `:1654`).
At 240 draws a survivor count above 40 is reachable — the right arm has already printed 38 — so a
set comparison must check the announcement line before treating the printed poses as the whole set.

### ⭐ Answered — p18 `-939 §2` supplied the run identities, and the sets invert the counts

⚠ **First, a trap I walked into — and then misattributed.** For B and C I opened
`/tmp/mounting_sweep/crown_0.110_0.280_20.log` and `z_1.330_0.280_20.log`, because their filenames
carry exactly the right cell. Both read **13 solved**: they are **24-draw** sweep points. The
filename encodes crown, spread and tilt and *not the draw count*, so a 24-draw point and a
240-draw point are reachable by names that differ in nothing a reader would check.

⛔ **And I then wrote that p18 had named those two logs. p18 had not.** `-939` gave the SEED
artifact lines for B and C and said, verbatim, *"B/C の出所 log は貴殿 bookkeeping（当卓は割当て
ない）"* — the only log it named was A1's. Choosing those two files was mine, and so was the
error. p18 returned it (`-946 §2`, machine-checked: zero hits for either path in the sent file).
⚠ Twice in one paragraph I read a label instead of the thing: the filename for the run, and my
memory for who supplied it.

The 240-draw sources were then found by a closed query for `106 solved`:

| | cell (all spread 0.280, tilt 20, 240 draws) | source |
|---|---|---|
| **A0** | crown removed | `scratchpad/tries240.log` (09:31) |
| **A1** | crown removed | `/tmp/mounting_sweep/st_none_0.280_20.log` (11:00, this grid) |
| **B** | crown pinned 0.110 | `scratchpad/rt_grid_240.log` (09:50) |
| **C** | real reaching head, Z0 1.330 / r 0.100 | `scratchpad/stage1.log` (09:56) |

**The counts, compared as sets.**

| | printed entries | distinct poses (exact) | distinct at 1e-3 rad |
|---|---|---|---|
| A (crown removed) | 4 | 4 | **3** |
| B (crown 0.110) | 5 | **2** | **2** |
| C (real head) | 5 | **2** | **2** |

1. ⭐ **"5 beats 4" is an artifact of counting entries.** Four of B's five printed entries are the
   *same pose*, byte-identical to the last digit (sigma 0.0338), reached from four different
   seeds. C is the same. ⇒ With the head in, the left arm has **two** distinct clear start poses;
   with it removed, **three**. The head **removes** an option; it does not add one.
2. ⭐ **B and C are indistinguishable here.** Identical survivor sets, identical sigmas
   (0.0338, 0.0381), and both interleave lines read **+14.7 mm at the same geom pair (7 ↔ 46)**.
   ⇒ For the left arm's start pose at this mounting, a pinned 0.110 crown and the real reaching
   head are the same obstacle. ⚠ For *this* predicate at *this* mounting — not in general.
3. **One pose is common to all three cells** — sigma 0.0381,
   `q = [+1.140126 +0.416080 +1.845414 −0.556151 +0.433782 +1.581307]`. It is the only survivor A
   shares with B and C: the pose that does not care whether the head is there.
4. **A0 vs A1: identical, 4 shared and 0 differences** — two independent runs ninety minutes
   apart, one launched directly and one through the sweep. ⇒ Reproducible, and the grid's reuse
   mechanism is validated against a run that never used it.

⚠ **Scope.** Left arm, start pose, spread 0.280 / tilt 20, 240 draws. The distinct-pose counts are
properties of that draw count — though A0 ≡ A1 shows the draw is deterministic given the seed, so
"a different sample" here means a different `START_TRIES`, not a different roll.

---

## (c) ⭐ The three legs are not all evaluated against the final partner

`SIDES = {"L": -1.0, "R": +1.0}` (`ur15_cell_spec.py:471`) — a dict, so iteration is **L then R**.
With three rounds (`:1705-1712`), each solve passing `other=START[<the other side>]`:

| solved | with `other` = | which is |
|---|---|---|
| L, round 2 (final) | `START["R"]` | the **round-1** R — *not* the final R |
| R, round 2 (final) | `START["L"]` | the **round-2** L — the final L ✓ |
| interleave | both final poses | the final pair ✓ |

⇒ **The left arm's clearance was checked against a right-arm pose that is not the one it ends up
beside.**

**What that does and does not damage.** On a PASS row the conjunction still holds, but for a
reason worth writing down rather than assuming:

1. **L vs the mounting** — independent of R, so the round makes no difference. Valid.
2. **R vs the mounting, and R vs the final L** — round 2, against the final partner. Valid.
3. **Final L vs final R at the commanded span** — measured directly by the interleave, and on a
   PASS row it is positive. Valid, and it is what covers leg 1's stale partner **at the endpoint**.

⛔ **What is left uncovered: L's *path* clearance against the final R.** The "on the way" checks
(the ones that print `at 5/9 along the move`) ran against the round-1 R, and the interleave
measures the endpoint only. So a PASS row says the two arms are clear **where they end up**, not
that the left arm's approach is clear of where the right arm ends up.

**Can one observation settle it?** Yes, and it does not need a new run design: print `START[t]`
at the end of each round, so the round-to-round movement is visible, and re-run the path check for
L against the final R. Small, and it is the only part of the conjunction currently taken on trust.

### ⛔ Run 1 was void — and I nearly reported it as a pass

`EXTRA_L_ROUND=1` re-solves the left arm once more with `other` set to the **final** right pose,
using the driver's own predicate (`ur15_steps_wired.py:1731-1746`; `START` is not overwritten, so
the run is unchanged). At both witnesses it returned **the identical count and the identical
pose**:

| centre | original solve (vs round-1 R) | vs FINAL R | chosen pose differs by |
|---|---|---|---|
| −0.150 | 140 solved / 15 clear | 140 / 15 | **0.000000 rad** |
| −0.200 | 138 solved / 31 clear | 138 / 31 | **0.000000 rad** |

That reads as "the left arm is clear against the final right pose". ⛔ **It is not evidence**: if
the right arm never moved between rounds, "clear against the final R" and "clear against the R it
was already checked against" print exactly the same line. A test that cannot come out differently
is not a test, and I could not tell which it was — because the other half of my own proposal, the
per-round pose print, was not implemented.

**With the print in** (same flag, `:1727-1729`), at both centres:

```
round 0 L … round 1 L … round 2 L   max |q − round0| = 0.000000, 0.000000
round 0 R … round 1 R … round 2 R   max |q − round0| = 0.000000, 0.000000
```

⇒ **Neither arm moves after round 0.** The test was void, as suspected.

### ⭐ What the void test does settle, and what it does not

1. **At these two witnesses the §c caveat evaporates** — not because the left arm was re-tested,
   but because **there is no stale partner**: the pose it was cleared against and the pose it ends
   up beside are the same object. The conjunction at −0.150 and −0.200, which is what the current
   recommendation rests on, is clean on all three legs.
2. ⛔ **The general concern is NOT closed.** It needs a point where the poses *do* move between
   rounds, and whether such a point exists is unmeasured. §c stands as written for the grid at
   large.
3. ⚠ **A narrower observation, stated at its own width:** round 0 solves the left arm against the
   **home** right arm and rounds 1–2 against the solved one — different partners — and the left
   arm returned the same pose each time. So at these centres the partner does not decide the left
   arm's *chosen pose*. It does **not** follow that the partner leaves the survivor *set* alone:
   rounds 0 and 1 are quiet, so their counts were never printed.
4. The three-round loop therefore does no work after round 0 here — three solves for one result.
   That is the loop converging, not a defect; recorded because the cost is real.

---

## (d) The `NOT MEASURED` row cannot tell a cap from a crash

Confirmed, self-caught, and p18 concurs. The row currently reads
`-- NOT MEASURED: no interleave line within 2400s --` whether the cap was reached or the child was
killed by a signal — and for `(none, 0.340, 30)` it was a **SIGSEGV at 37 s**
(`SEGFAULT_AT_SPREAD0340_TILT30_20260802.md`, sha `740eb72a…3dff7e7e` @ `62536001cd`).

**Fix, with the fix to the fix.** The row must carry the **measured elapsed time** and the **exit
status**, and `one()` must return them rather than leaving the caller to infer from an absent
line — the caller cannot distinguish "no line yet" from "no line ever". Until that lands, the
`(none, 0.340, 30)` row is to be read with the exit evidence beside it, as p18 is already doing.
