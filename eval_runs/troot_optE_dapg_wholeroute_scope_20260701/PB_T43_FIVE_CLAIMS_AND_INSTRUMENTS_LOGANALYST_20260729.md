# pB — t43: the five readings, and the new instruments themselves

Request: p18 `MSG-P18-PB-T43-TRACE-READ-FIVE-CLAIMS-AND-THE-NEW-INSTRUMENTS-THEMSELVES-20260729-798`.
Asked for: hold-or-break on each of p4's five readings, **plus** a check of the new instruments
themselves. ⛔ Numbers only. **No PASS is issued here.** The verdict is p4's, after both legs.

---

## 0. Pins (measured by me, this session)

| item | value | how I checked |
|---|---|---|
| trace | `p4_ur15_sim_20260727/T43_RUN_TRACE_20260729.txt` sha256 `0d93cbc458f98182f5d3ee77faccefa548d6ec23992a166c355e4369064e6ab1` | `sha256sum` — MATCH to p18's pin |
| trace length | 68 lines | `wc -l` |
| producing driver | `fa948b8a53` "Give each arm its own ramp, and stop when one stalls" | `git log -1` |
| driver blob | `d8d10b695a6c378e276eafdbdaad5b0d931c848d29c6600222ef65490bee9eb1` | identical at `fa948b8a53`, at HEAD `bd0d8dd7c1`, and in the worktree — all three measured |
| driver length | 2821 lines | `wc -l` on all three |
| trace landed at | `99d45e2114` (containing, not producing) | `git log --all -- <trace>` |
| comparison trace | t42 `178479bf8336d810ed3e4c7e2062f009f6505cbf7ba2aaff13483d4da397c6cf`, 161 lines | `sha256sum` |

⭐ **The model is the same in t42 and t43.** Both traces print `nq=113 nu=14 nbody=88 ngeom=140 eq=8`
(t42 `:20` / t43 `:20`), `arm geom sets L=38 R=38` (t42 `:23` / t43 `:23`), and
`L reach 1546 mm -> 5.18 mrad | R reach 1546 mm -> 5.18 mrad` (t42 `:21` / t43 `:21`).
This matters for §2: a geometry query on the same joints gives the same answer in both runs.

Line numbers below are: t43 trace = `t43:N`; t42 trace = `t42:N`; driver at `fa948b8a53` = `drv:N`.

---

## 1. Reading (i) — L 0 of 7, all put back — **HOLDS**, and I can close it harder than p4 did

**The fact.** `t43:27` prints the fallback warning and `t43:28` prints `7 solved / 0 collision-free
(⛔ 0 -- all 7 put back)`. The code is `drv:1509-1518` (`_strict = [c for c in cands if not c[3]]`,
`_fell_back = not _strict`, `free = _strict or cands`) and `drv:1570-1571`. ✅ **The repair fires,
and its first reading is zero.** This is the first live firing of the change.

**The second half — "t42's 6/6 was the all-put-back side".** p18's ledger §476 records this as
*"discriminated now; not re-proven for t42"*. ⭐ **It can be re-proven for t42, from t42's own line.**

| quantity, L start pose | t42 `:27` | t43 `:28` |
|---|---|---|
| chosen pos | 0.00 mm | 0.00 mm |
| roll | 0.0 deg | 0.0 deg |
| sigma_min | **0.1083** | **0.1083** |
| \|q\|max | **2.26 rad** | **2.26 rad** |
| solved / collision-free | 6 / 6 | 7 / **0** |

The chain:

1. The mast test (`drv:1478-1481`) is `mujoco.mj_geomDistance` on scratch data with the candidate's
   joints written in — a pure geometry query, deterministic given (model, joint vector).
2. The model is identical between the runs (§0).
3. The two winners print the same four scalars, and `roll 0.0 deg` means the winner came from menu
   entry `(0.0, sgn*0.0)` (`drv:1367`) — the one entry the sign flip cannot move.
4. In t43 the winner is drawn from a set in which **every** candidate has `hit=True`.
5. If t42's `_strict` had been non-empty, then `free = _strict` (`drv:1511`) and the winner —
   drawn from `pool ⊆ well ⊆ free` (`drv:1519-1537`) — would have had `hit=False`.
6. (2)+(3) ⇒ the same pose gets the same `hit` in both runs ⇒ `hit=True` in t42 ⇒ contradicts (5).

⇒ **t42's `_strict` was empty. The 6/6 was the all-put-back side.** Not an inference across runs —
it closes on t42's own printed winner.

⚠ **The one link I did not measure:** step 3 infers "same joint vector" from four printed scalars.
The vector itself is not printed by either run. Everything above is conditional on that link.

**Why the count went 6 → 7:** the start-pose call is `drv:1590` with `wide` defaulting to False, so
its menu is the 11-entry base (`drv:1367-1368`), which contains `(sgn*y, sgn*r)` for `y ∈ {0.3,-0.3}`.
The sign flip changes those entries, so the two runs searched different sets. **The sets are not the
same; the winner is.**

---

## 2. Reading (ii) — the split ramp works — **the fact HOLDS; two things read into it do not**

**Holds.** t42 printed **one** line for both arms (`t42:51`, `reached 0.0%`, "because **the arm** was
more than 5.2 mrad behind"). t43 prints **two**, each naming its side: `t43:52` L 0.0%, held on
10560 of 10560 ticks; `t43:53` R **71.5%, never held back**. Code: `prog`/`held_ticks`/`_last_gain`
are all per-side dicts (`drv:2401-2415`), `_room` is per side (`drv:2428-2433`), the print indexes by
side (`drv:2622-2631`). R's tool error at the same step: **3.6 mm** (`t43:64`) against **10.4 mm**
(`t42:62`). ✅ The split is real and R is free of L's jam.

⛔ **Break 1 — "never held back" does not mean R was tracking freely.** `held_ticks` counts only ticks
where `_room ≤ 0`, i.e. where the arm is a **whole** tolerance behind. R never hit that. But R's
progress is throttled by the same term continuously (`drv:2433`). Re-derived from the printed numbers:

- `steps` = 10560 (from `t43:52` "of 10560" = `s_`, and the stall fires at `s_ = steps`, `drv:2571-2572`)
- `ramp = int(0.72 × steps)` = **7603** (`drv:2356`), `dprog = 1/ramp`
- R reached 0.715 ⇒ Σ`_room[R]` over the step = 0.715 × 7603 = **5436** ticks-worth over 10560 ticks
- ⇒ mean `_room[R]` ≈ **0.515** ⇒ **R sat about 2.5 mrad behind its command on average**, roughly half
  its 5.18 mrad tolerance, for the whole step.

⇒ R was running at about **half** the commanded ramp rate the entire time. "Never held back" is the
count of a hard stop, not a statement that the lag was small.

⛔ **Break 2 — 71.5 % is where R was cut off, not where R stopped.** The step ended because **L**
stalled (`drv:2571-2575`), not because R ran out. At mean `_room` ≈ 0.515, R needed ≈ 7603/0.515 ≈
**14 800 ticks (3.08 s)** to reach 100 %; it was given 10 560 (2.2 s). `t43:53` carries
`<- THE MOVE DID NOT FINISH` for R as well, which is correct and loud. **R's ceiling is not measured
by this run.**

---

## 3. Reading (iii) — 68 lines, last word the jam — **both facts HOLD; the stated reason no longer does**

**Holds.** 68 lines against 161 (§0). `t43:65-68` is the traceback and `drv:2768-2778` raises only
under `if _stalled:`, after everything above has printed. ✅

⛔ **Break — the justification in the error text is now true of one arm only.** `drv:2776-2778` reads
*"Continuing would re-measure this same configuration once per remaining step, which is what the
previous run did."* In t42 that covered both arms: both sat at 0.0 %. In t43 **R was at 71.5 % and
still gaining** (`_last_gain['R']` kept updating, which is why R is absent from `_stalled_sides`).
`prog` is re-initialised to 0 each step (`drv:2401`) and R gets a new target, so R's STEP 3-6 would
have been **new** configurations, not re-measurements.

⇒ Stopping at the stall now discards R's remaining information. Whether that is the right trade is
p4's call; what I can say is that **the reason printed for it no longer covers both arms**.

---

## 4. Reading (iv) — mirrored menu — **the printed sign flipped; nothing else did**

**Holds as stated.** `t43:50` `aim L: yaw +0.15` against `t42:49` `yaw -0.15`. The `0.15` entries live
only in the `wide` block (`drv:1370-1371`), which confirms the aim solve ran with `wide=True`
(`drv:723`). The sign is `sgn` applied to yaw. ✅

⛔ **Break — the line offers no evidence the mirroring changed anything measurable.** Everything else on
the left arm is identical between the two runs:

| L quantity | t42 | t43 |
|---|---|---|
| aim roll / tilt | +0.10 rad / +6 deg | +0.10 rad / +6 deg |
| aim **seat error** | **117.96 mm** | **117.96 mm** |
| STEP 2 sigma_min L | 0.0482 | 0.0482 |
| mast L | −0.8 mm (g6 on `L_forearm_link`) | −0.8 mm (g6 on `L_forearm_link`) |
| ARM REACH L | 21.9 mm below the mouth, +107.7 vs table | 21.9 mm below the mouth, +107.7 vs table |
| AS REALISED L | 14.8 deg, pads +79.89 mm | 14.8 deg, pads +79.89 mm |
| CARRY L | cab39 at (−15.3,+177.7,+26.2) | cab39 at (−15.3,+177.7,+26.2) |
| step summary L | 511.9 mm | 511.9 mm |

The yaw sign flipped and the **seat error did not move by 0.01 mm**. That is consistent — L never left
0.0 %, so the aim's effect cannot show — but it means this run **cannot** show the mirroring working.
It shows the sign in the print. ⚠ Separately: "mirrored" as a geometric claim would want L's chosen
attitude to mirror R's; they do not (L sigma 0.1083 / roll 0.0 vs R sigma 0.2539 / roll 34.4 deg,
`t43:28/:29`). p4's `HOME_POSE_SYMMETRY_20260729.txt` measured the **cell's** mirror symmetry; the
**menu's** is a different claim and is untested here.

---

## 5. Reading (v) — the table-breach check did not fire — **HOLDS, and no one wrote "passed"**

**The measurement did run; only its warning branch did not.** `t43:55` prints
`L … +107.7 mm vs the table | R … +165.1 mm vs the table`. The code (`drv:2645-2668`) takes the eight
box corners of every box geom (`drv:2651-2654`), the bounding radius otherwise, keeps the lowest, and
appends `<- THROUGH THE TABLE` only when `bot_ - TABLE_TOP < 0`. Both readings positive ⇒ no fire.

⇒ **The sign convention and the threshold are untested by this run.** The arithmetic that produces the
number ran and produced plausible values; the branch that would raise the alarm did not execute.

**Searched for a claim that it passed — found none, and found two places that say the opposite:**

- p4, `99d45e2114` commit message, verbatim: *"The table check did NOT fire and is therefore untested
  by this run … It is not evidence of anything yet and is recorded here as untested rather than as
  passing."*
- p18, `P18_CLAMP_COURT_EVIDENCE_LEDGER_20260727.md` §476 (added in `bd0d8dd7c1`), verbatim:
  *"⛔ the table-breach check DID NOT FIRE ⇒ recorded by p4 as UNVERIFIED, not passed"*.

⚠ Two notes on the instrument, neither a break:
- `bot_` is selected by maximising `sc_[2] - bot` where `sc_[2]` is constant inside the loop, so it
  *is* the true minimum — correct, but by coincidence of a constant, not by asking for a minimum.
- The test compares against a scalar `TABLE_TOP`, so it reads "below the table plane", not "inside the
  table". An arm past the table's edge would read as a breach. That direction is the safe one.

---

## 6. The new instruments themselves (p18's added point) — four findings

### 6-1. ⭐⭐⭐ The repaired count is printed at **one of the four** places that can produce it

`solve_ik` has exactly four call sites in the file:

| line | what it solves | `quiet` | can the ⛔ fallback line print? |
|---|---|---|---|
| `drv:721` | the **aim** pose | `quiet=True` | **no** |
| `drv:1590` | the **start** pose | `quiet=(_round < 2)` | **yes**, on the last of three rounds |
| `drv:2222` | the **seating-step** waypoint | `quiet=True` | **no** |
| `drv:2235` | the **ordinary per-step** waypoint | `quiet=True` | **no** |

Both new prints are inside `if _fell_back and not quiet:` (`drv:1514`) and `if not quiet:`
(`drv:1562`). ⇒ **The fallback is still completely silent on every per-step solve** — which is where
the poses that jam on the mast at STEP 3-14 come from. t20 read the mast negative at eight steps of
thirteen; every one of those came from `drv:2235`, and if the fallback fired there, nothing said so
then and nothing would say so now.

⇒ The repair covers the start pose. **The three silent call sites are the ones the earlier jams came
through.** `CLEARANCE_REPORT` is written regardless of `quiet` (`drv:1558`), so the number exists —
it is the printing that is gated.

### 6-2. ⭐ The ⛔ line names a narrower cause than the test it reports

`hit` is set by **four** independent tests: actual contact `touching()` (`drv:1447`), the far-arm
clearance (`drv:1458-1461`), the mast at the pose (`drv:1479-1481`), and the mast along the path
(`drv:1488-1490`). `_strict` correctly excludes all four. But `drv:1515-1517` tells the reader
*"cleared the clearance or its path"* — two of the four. If seven candidates were rejected by contact
with the table or the cable, the line would still name the clearance.

The breakdown is already computed (`_clear_dropped` / `_col_dropped` / `_path_dropped`, `drv:1342-1344`)
and stored (`drv:1558-1561`) — but the start-pose call's copy is **overwritten** by the next solve
before any step prints it. ⇒ **"None passed" is now honest; "which test removed them" is still not
printed at the one place the count is.** That is one field.

### 6-3. ⭐⭐⭐ `clearance removed X of Y candidates` — Y counts the removed ones twice

`CLEARANCE_REPORT[t] = (_clear_dropped, len(cands), …)` (`drv:1558`), unpacked as `_dr, _kept`
(`drv:2703`), printed as `{_dr} of {_dr + _kept}` (`drv:2709`, and again at `drv:2714`).
But `cands.append(...)` at `drv:1501` is **unconditional** — a candidate that incremented
`_clear_dropped` at `drv:1460` is still appended. ⇒ `len(cands)` already contains them, and the
denominator is `numerator + total`.

**Independent refutation from the traces, not from the code.** `len(cands)` can never exceed the
number of IK attempts. The largest `n_try` any call site can produce is **54** (`tries=None` at
`drv:721` with `wide=True` ⇒ `2 × 27` poses, `drv:1367-1371`, `drv:1390`); the per-step sites pass
`tries=44`. Denominators found in the banked traces:

| trace | line | implied `len(cands)` = Y − X |
|---|---|---|
| t43 | `clearance removed 26 of **64**` | 38 |
| t42 | `clearance removed 27 of **66**` | 39 |
| t25 | `clearance removed 18 of **55**` | 37 |
| t25 | `clearance removed 14 of 49` | 35 |
| t20 | `clearance removed 17 of 54` / `13 of 48` | 37 / 35 |
| t42 | `13 of 46` / `13 of 49` / `2 of 17` / `1 of 14` | 33 / 36 / 15 / 13 |

**64, 66 and 55 exceed the maximum attempt count of 54 — impossible as candidate totals.** Subtracting
the numerator brings every one of them to ≤ 39. And every line whose numerator is 0 has a denominator
≤ 44 — those are right by accident, because adding zero is harmless. That is the positive control:
**the defect is visible only when the numerator is non-zero, and it is present in every such line in
every banked trace.**

⇒ The clearance's share of the candidate pool has been over-reported for as long as this line has run:
26 of 38 (68 %) has been printing as 26 of 64 (41 %).

### 6-4. ⭐⭐ The step-end clearance line does not say **which** solve it is reporting

`CLEARANCE_REPORT[t]` is overwritten by every `solve_ik` call, and the step-end print (`drv:2702`)
reads whatever is there. The traces show it is **not always the waypoint solve**: lines reading
`clearance removed 0 of 2 candidates` appear in t20, t22, t25 and t42. `len(cands) = 2` is only
reachable with `n_try = 2`, which only `drv:721` produces (`tries=None` with `pose_only`/`pose_rd`
collapsing the menu to one entry, `drv:1376`/`drv:1383`). ⇒ **those lines are reporting the aim solve
while sitting under a step heading.**

⇒ Same family as 6-1 and 6-3: one line, two different questions, no field that says which.

### 6-5. ⭐ "best dropped" is a maximum over one of the three rejecting tests

`_drop_sv = [c[5] for c in cands if c[7]]` (`drv:1543`) and `_by_clearance` (`c[7]`) is set **only** in
the far-arm branch (`drv:1461`). Mast rejections never set it. So on `t43:58` the phrase
*"vs best dropped 0.1983"* sits in the same sentence as *"the mast removed 33 at the pose and 3 on the
way there"* — **36 rejected candidates that are not in the maximum being quoted.** The comparison the
comment at `drv:1530-1535` describes ("the filter removing good candidates vs the cost passing over a
good survivor") is therefore run against a third of the filter.

⚠ Latent, not realised in t43: when the fallback fires, `free = cands`, so "best survivor" (`_pool_sv`,
`drv:1536`) and "best dropped" are drawn from **overlapping** sets and the comparison loses its meaning
entirely. In t43 the ⛔ line printed only at the start pose, where no clearance line is emitted, so this
did not surface in this run.

### 6-6. The side-named prints — verified per-arm, but this run cannot demonstrate it by value

`prog[t2]`, `held_ticks[t2]`, `TRACK_TOL[t2]` are all indexed by side (`drv:2623-2631`); `s_` and
`steps` are shared and are the loop counter, correctly. ✅ `TRACK_TOL` is re-measured per step
(`drv:2389-2393`) and is constant within a step, so the value printed at the end is the value used. ✅

⚠ **But both sides print `5.2 mrad`**, because `ARM_REACH` is 1546 mm on both (`t43:21`). The
per-arm tolerance is real in the code and numerically indistinguishable in this run. ⇒ **the printed
value cannot be used as evidence that the tolerance is per-arm.** The code can; the number cannot.

### 6-7. The stall condition does **not** wrongly stop an arm that has arrived

`_stalled_sides = [t2 for t2 in SIDES if prog[t2] < 1.0 and s_ - _last_gain[t2] >= steps]`
(`drv:2571-2572`). An arm at `prog == 1.0` is excluded by the first conjunct, so the finished side is
never called stalled even though it has stopped gaining. ✅ Confirmed in the run: R is at 71.5 %, is
gaining, and carries no `STALLED` marker on `t43:53`, while L does on `t43:52`.

⚠ One scope note, not a break: the guard fires on **absence of gain**, and an arm can gain nothing
because the *other* arm is momentarily in its way. With the ramps now independent, that is a state the
run can enter and did not previously. The guard would call it a stall after one step's worth of ticks.
Nothing in t43 exercises this.

---

## 7. What this trace cannot decide

- **Whether L has any reachable start pose at all.** `0 of 7` says none of *seven attempts under this
  menu, this warm start and this seed* cleared. `drv:1590` passes `tries=24` over an 11-entry menu.
  A different sample could hold one. The trace refutes "the chosen pose was clear"; it does not
  establish "no clear pose exists".
- **Which of the four tests removed the seven.** Computed, overwritten, never printed (§6-2).
- **Whether R can finish the step.** Cut off at 71.5 % (§2).
- **Whether the table-breach check works.** Its warning branch never ran (§5).
- **Whether the menu mirroring does anything geometric.** Every measurable L quantity is unchanged (§4).
- **Anything about the physical validity of the motion.** Not my leg. ⛔ No PASS is issued here.

---

## 8. Summary

| p4's reading | verdict from the trace + code |
|---|---|
| (i) L 0/7 all put back; t42's 6/6 was the same world | **HOLDS** — and re-provable on t42's own winner (§1), modulo the unprinted joint vector |
| (ii) split ramp works, R 71.5 %, never held | **HOLDS as fact.** ⛔ "never held back" ≠ tracking freely (mean lag ≈ 2.5 mrad); ⛔ 71.5 % is a cutoff, not a ceiling (§2) |
| (iii) 68 lines, last word the jam | **HOLDS.** ⛔ The reason printed for stopping no longer covers R (§3) |
| (iv) aim L yaw +0.15 = mirroring | **The print flipped.** ⛔ No measurable L quantity changed; the run cannot show the mirroring working (§4) |
| (v) table check did not fire = untested | **HOLDS**, and both p4's commit message and p18's ledger already say "untested, not passed" (§5) |

**New instrument findings, in order of weight:**

1. ⭐⭐⭐ The repaired count prints at **1 of 4** call sites; the three silent ones are where the
   mast jams came from (§6-1).
2. ⭐⭐⭐ `clearance removed X of Y` has Y = X + total — three banked denominators exceed the maximum
   possible attempt count (§6-3).
3. ⭐⭐ The step-end clearance line sometimes reports the **aim** solve and has no field saying so (§6-4).
4. ⭐ The ⛔ line names two of the four tests that can have rejected the candidates (§6-2).
5. ⭐ "best dropped" covers far-arm rejections only, printed beside 36 mast rejections it excludes (§6-5).
6. Per-arm prints verified in code; ⚠ the two tolerances are numerically equal here, so the value
   cannot demonstrate it (§6-6). The stall test does not mis-stop an arrived arm (§6-7).

⛔ **No PASS.** Numbers and code only. The visual leg is p18/pC's; the verdict is p4's, after both.

---
pB (LOG-ANALYST) — 2026-07-29 JST
