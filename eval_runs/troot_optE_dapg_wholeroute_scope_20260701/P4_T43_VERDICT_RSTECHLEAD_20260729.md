# p4 — t43 VERDICT (both legs in)

**Authority:** run verdict = p4. Physical-validity authority for video remains Rs (human GT).
**Gate:** opened by p18 `-806`. Both leg artifacts read directly, not via the routing summary.

| leg | artifact | content sha256 |
|---|---|---|
| numeric / log | `PB_T43_FIVE_CLAIMS_AND_INSTRUMENTS_LOGANALYST_20260729.md` | `b81bebcc…5fe1e3` |
| video (blind) | `P18_T43_BLIND_VIDEO_READ_20260729.md` | `e319f3ae…5efa21` |
| trace | `p4_ur15_sim_20260727/T43_RUN_TRACE_20260729.txt` | `0d93cbc4…64e6ab1` |
| video | `p4_ur15_sim_20260727/t43_live_20260729.mp4` | `7e08abab…7d482fdc` |
| sweep | `p4_ur15_sim_20260727/GRASP_CENTRE_SWEEP_20260729.txt` | `ef788fae…8a9ebd83` |
| driver | `p4_ur15_sim_20260727/ur15_steps_wired.py` @ `fa948b8a53` | — |

---

## 1. VERDICT

**TASK: FAIL**, and it is the same failure as t42 with one link removed. Neither arm grasped;
the cable did not move in any of the 66 frames; the run ended at the stall.

**PHYSICS: PLAUSIBLE** (blind video read, all 66 frames, zero discrete events, no collapse).

**⭐ INSTRUMENTS: the run did what it was built to do.** t43 was not run to succeed — it was run
to find out whether the four changes made the failure legible. They did, and one of them closed
an open question in a single run. That is the useful outcome and it is stated separately from the
task verdict so the two are not confused.

---

## 2. What the run settled

**The left arm's start pose was never clear.** `⛔ start-pose IK L: NOT ONE of 7 candidates
cleared the clearance or its path, so all 7 were put back`. t42 printed `6 solved / 6
collision-free` for the same situation, because the survivor list silently fell back to the full
candidate list — "all cleared" and "none cleared" shared one number. pB re-proved the t42 case
from t42's own lines afterwards, so this is not only a t43 fact.

**One arm's jam no longer freezes the other.** L held on every tick; R reached 71.5% and was
never held back. ⚠ Two things that does NOT mean, both from pB and both accepted: *never held
back* is not *tracking freely* — R still lags about 2.5 mrad on average; and 71.5% is where L's
stall cut the step off, not a ceiling — R needed about 3.1 s to finish.

**The stall ends the run.** 68 lines against t42's 161, and the last word is the jam rather than
an unrelated angle four steps later.

**⛔ The mirrored menu is NOT demonstrated by this run.** The aim line's yaw came back `+0.15`
where t42 had `-0.15`, and I offered that as the change working. p6 is right that it is not
evidence: the menu set is ±symmetric, so `+0.15` was always available. pB adds that the left
arm's winning start pose was the sign-invariant `(0,0)` entry and matched t42 to the last
printed digit. The mechanism is in the diff; the demonstration needs a static menu print or a run
whose winner is not `(0,0)`. **Withdrawn as evidence, kept as an unverified change.**

**⛔ The table check is untested.** It never fired — the stall ends things before any descent.
Recorded as untested, not as passing.

---

## 3. ⭐ What the sweep then settled, and what it did not

p5 asked for the highest grasp-pair centre x at which the left arm keeps ≥1 collision-free start
pose. **There is no such x.** Across +0.150 to −0.250 — every centre the cable can carry the span
at — the left arm keeps **zero**. Moving toward −x, the ruled direction, buys the left nothing and
costs the right what it had (2, 2, 1, then 0 from centre 0.000 on).

**It is placement, not reach**, and the table is direct evidence: the left arm's *solved* count
**rises** as the centre moves away (7 → 14) while its clear count stays at zero. An arm out of
reach runs out of solutions; this one runs out of clear ones. ⚠ I had written "reachability" and
p6 corrected it before this measurement existed; the measurement agrees with the correction.

⛔ **Not a recommendation.** Whether to open the upstream options p5 named — moving a clip,
swapping the arms' roles, changing the mounting — is p5's call and Rs's to settle.

---

## 4. What I got wrong, again stated plainly

1. ⛔ **"The mirrored menu is working."** Withdrawn — see §2. A ±symmetric set produces the same
   line either way.
2. ⛔ **"never held back", read as the right arm tracking freely.** It lags ~2.5 mrad. And 71.5%
   was a cut-off, not a limit. Both from pB.
3. ⛔ **"reachability"** where the right word is **placement**. Solutions exist; they collide.
4. ⛔ **Cause misattributed on the sweep.** Nine identical rows appeared, I blamed a duplicate
   target computation that read the old constant, fixed it, and it was **not** the cause — the
   sweep built a child environment and never passed it. The duplicate was real and is fixed; it
   was not the defect. What caught me was not noticing: it was the self-check I had added, which
   refuses to report when the centre moves and the links held do not. Finding *a* defect is not
   finding *the* defect, and I did not take a control before concluding.
5. ⚠ **Cross-driver count comparison — and then the correction to the correction.** I accepted
   that t42's and t43's collision-free counts were not the same quantity because the mast geom
   set had changed (ngeom 139 → 140). ⛔ The pair was wrong: both traces print `ngeom=140`, and
   the crown entered the set on 07-28 23:05, before t42. The 139 → 140 step belongs to an earlier
   cell. So **t42 and t43 are comparable**, and reading t42's "6 of 6" as the all-put-back case
   does not depend on an assumption. The habit stands — counts from drivers whose predicate
   differs are not one quantity — but it did not apply here, and I had propagated it into two
   documents before it was checked.

---

## 5. Next, and where the boundary is

| # | item | authority |
|---|---|---|
| 1 | four instrument defects from pB `-516`: the repair print reaches only 1 of 4 solve sites (the per-step solve that historically produced the mast jam is still silent); `removed X of Y` double-counts the excluded in Y; the same line can report an aim solve with no field to tell which; `best dropped` omits the mast rejections named in its own sentence | mine |
| 2 | the stall message names the run, not the side — in t43 only L froze while R was advancing | mine |
| 3 | a static menu print at startup, to demonstrate or refute the yaw mirroring | mine |
| 4 | where the grasp pair sits, and whether to open clip placement / role swap / mounting | ⛔ p5, then Rs |
| 5 | two unresolved video flags (orange elbow ↔ purple link adjacency; purple lower claw ↔ cable contact) — viewpoint-limited, want numeric cross-check | mine, after 1 |

⛔ No re-run until items 1–3 are in: the failure is now in placement, and another run of the same
placement would re-measure what the sweep already answered.
