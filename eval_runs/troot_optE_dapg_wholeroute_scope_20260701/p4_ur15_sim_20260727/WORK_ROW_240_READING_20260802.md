# The work-row sweep at 240 draws — the second banked zero that was the sample

**Artifacts.** `WORK_ROW_Y_SWEEP_TRIES240.txt` (this run); the banked 24-draw table
`WORK_ROW_Y_SWEEP_20260729.txt`, whose conclusion this supersedes. Mounting = the built cell
(only `WORK_ROW_DY` moves; `REST_Y` and both clip rows shift together and the table follows, so
relative spacing is untouched at every point).

⛔ **SUPERSEDED — the 24-draw conclusion is REFUTED.** It read: *"⛔ The LEFT arm keeps ZERO
collision-free candidates at every offset swept."*

---

## 1. At 240 draws it does not

| dy [m] | cable y | L solved | L clear | R solved | R clear | arms closest | all three legs |
|---|---|---|---|---|---|---|---|
| 0.000 | +0.280 | 58 | 0 | 132 | 19 | — | fail (L) |
| 0.050 | +0.330 | 86 | 0 | 140 | 23 | — | fail (L) |
| 0.100 | +0.380 | 122 | 0 | 137 | 36 | — | fail (L) |
| 0.150 | +0.430 | 147 | 0 | 136 | 41 | +0.0 | fail (L) |
| **0.200** | +0.480 | 151 | **1** | 135 | 5 | **+34.5 mm** | **witness** |
| **0.250** | +0.530 | 142 | **1** | 136 | 3 | **+29.5 mm** | **witness** |
| 0.300 | +0.580 | 136 | **7** | 138 | 1 | +0.0 | fail (touching) |

⇒ **Moving the work row is not dead.** Two offsets carry all three legs at one witness pair. This
is the **second** banked conclusion of mine refuted by the same mechanism today — the first was the
grasp-centre sweep (`GRASP_CENTRE_240_READING_20260802.md`). Both were columns of zeros taken at
twenty-four draws.

## 2. ⚠ The two arms trade

L clear rises with the offset (0, 0, 0, 0, 1, 1, 7) while R clear collapses (19, 23, 36, 41, 5,
3, 1). The row moving away from the column frees the left arm and crowds the right one. At 0.300
the left arm has its best count and the pair touches.

⇒ The passing window is narrow and it is **between** the two trends, not at either end. ⛔ Whether
the row may move 200 mm at all is a task question (where the clips must be), and it is not mine.

## 3. ⭐ The print cap was crossed here — ten minutes after I called its margin two

At **dy 0.150 the right arm has 41 clear poses**, and the driver printed
`start-pose IK R: (1 further clear poses not printed)` — the `_strict[:40]` cap
(`ur15_steps_wired.py:1651`, announced at `:1654`).

This matters immediately for p5's all-pairs interleave costing (`bank #71`), which is exact
**because** every clear pose of the mounting grid is printed (max L 17, max R 38, both under 40).
That holds for the grid. **It does not hold here**: extend the same calculation to this sweep and
one point's pose set is already incomplete.

⇒ The protocol I sent (`-242`: measure `max free` before running an all-pairs calculation) is not
hypothetical — the first sweep run after sending it crossed the cap. ⭐ And the announcement is
what made that visible rather than silent, which is the design p6 flagged as load-bearing
(`-999`: the announcement is safe only while it shares a gate with the list).

## 4. Limits

1. **Start pose only**, as everywhere in this investigation.
2. **The boundary is unresolved** — 50 mm between 0.150 (closed) and 0.200 (open), unsampled.
3. **A fail is not a refutation**: the interleave is read at one pose pair out of N × M, so the
   four closed rows are "no witness found", not "no witness exists".
4. **240 is a sample too.** Nothing here says a count would not move again at 2400.
5. **The 24-draw table's own self-check still stands** — the cable's settled y was read back from
   each run, so the knob demonstrably reached the cell at every offset (+0.280 … +0.580).
