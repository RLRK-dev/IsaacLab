# p4 — t42 VERDICT (both legs in)

**Issued:** 2026-07-29 (date-THEN-write; the desk clock is in the message that carries this).
**Authority:** run verdict = p4 (RS-TECH-LEAD). Formal physical-validity authority for video remains Rs (human ground truth) — this verdict does not claim it.
**Gate:** opened by p18 `-790` after both legs landed. I read both artifacts myself rather than adjudicating from the routing summary.

## 0. What this verdict stands on (pins, all desk-verified and re-verified here)

| leg | artifact | content sha256 | commit |
|---|---|---|---|
| numeric / log | `PB_T42_FOUR_READINGS_LOGANALYST_20260729.md` | `a94411fd…0c64e65` | `8ce693e631` |
| video (blind) | `P18_T42_BLIND_VIDEO_READ_20260729.md` | `a54733c9…4e24858` | `05069d885e` |
| video (blind, prior run) | `P18_T25_BLIND_VIDEO_READ_20260729.md` | `bd21bc2e…7c8002c2d` | `33807c6824` |
| run trace | `p4_ur15_sim_20260727/T42_RUN_TRACE_20260729.txt` | `178479bf…397c6cf` | `fc9d999e20` |
| video | `p4_ur15_sim_20260727/t42_live_20260729.mp4` | `1583297c…d3c4531c` | `fc9d999e20` |
| my static probe | `p4_ur15_sim_20260727/HOME_POSE_SYMMETRY_20260729.txt` | `87bde87b…205c739a` | `dfb8dc1bde` |
| producing driver | `p4_ur15_sim_20260727/ur15_steps_wired.py` | — | `576cb8f029` (worktree == commit, measured) |

---

## 1. VERDICT

**TASK: FAIL.** Neither arm grasped. The cable did not move once in the whole run. The run
terminated on the vertical check at STEP7 R.

**PHYSICS: PLAUSIBLE.** No NaN, no explosion, no teleport, no object loss, no rendering
collapse, no penetration of table or mast, across 63 sampled instants plus an 8-frame burst plus
the terminal frame (video read §2-4). ⇒ **This is a control-and-targeting failure, not a physics
failure.** That distinction decides where the fix goes, so it is stated first.

**CONSERVATISM DIRECTION:** neither. Nothing here made the task easier than reality; nothing
made it harder. The run never reached the conditions where that question applies.

---

## 2. The chain, in the order it actually runs

Each link is carried by a reader who is not me, or by a measurement I can point at.

1. **The start pose is clear.** Held at the cell's home values in t42's own as-built cell, no arm
   geom is inside anything: both shoulders read `+60.10 mm` to the crown, both forearms
   `+113.77 mm`, every paired link is an exact mirror to `0.0000 mm`, and the physics reports
   **zero arm contacts** (probe §1–§4). ⛔ So the contact is not born with the pose.
2. **What is commanded next is not the home pose.** The driver solves a start-pose IK
   (trace `:27`/`:28`) and commands that. `:27` L: `6 solved / 6 collision-free … roll 0.0 deg`.
   `:28` R: `17 solved / 2 collision-free … roll 34.4 deg`.
3. **The left arm jams on the way to it.** `:31` `STEP1 L arm touching: ['column (via g6 on
   L_forearm_link)']`; `:36` act force `[206.9, 433., 204., …]` against limits
   `(433, 433, 204, …)`; `:38` j1 and j2 saturated; `:35` joint error `-233.5 mrad` against a
   `5.175 mrad` allowance = **45.1×** (pB §1, arithmetic re-done here).
4. **One arm's jam freezes both.** `576cb8f029:2359-2360` computes a single `_room` as
   `1 - max(...) over SIDES`, and `:2363` advances a single `prog` by it. ⛔ The comment
   immediately above, `:2348-2349`, states the opposite intent verbatim: *"Each arm against its
   own bound, because reach differs and a single max would hold the shorter arm to the longer
   arm's tolerance."* The intent is per-arm; the code is shared. (pB §1 found it; I confirmed it
   in source.) Consequence in the trace: STEP2–6 held `10560/10560, 21600/21600, 21600/21600,
   9600/9600, 13440/13440` ticks — the ramp never advanced once after STEP1.
5. **The right arm is not blocked — it is unaddressed.** `:32` `STEP1 R arm touching: clear`;
   `:39` `tool err= 2.1mm`; `:113` all actuator forces `0`, nothing saturated. It sat where it was
   told for 11.2 s (video §1: *"完全静止（約11.2秒）"*). Its 34.4° attitude is not where a frozen
   command abandoned it — it is the roll its own start-pose solve **chose** at `:28`.
6. **The one close that happens, closes on nothing.** Video §2-3: before the close the cable sits
   **below the outer face of the lower claw**, not inside the mouth; during the close (11.25–11.8 s)
   the cable moves **0 px**; after it the claw tips lift clear. Trace agrees on the geometry:
   `:117` nearest cable link `76.9 mm` from the pinch, `:115` `clamped=False`, `:116` `fingers
   blocked by nothing`.

---

## 3. ⭐ What the two legs together show that neither shows alone

### 3-1. The grasp check is evaluated before the jaw closes

The GRASP block (`:100`–`:117`) is printed inside STEP4, and STEP4 ends at **t = 11.2 s**
(`:129`). The video's only close is at **11.25–11.8 s** — *after* that. So `ctrl=18`, `pad
separation 93.3 mm`, `clamped=False` were all measured **with the hand still open**.

⇒ ⛔ **The containment/clamp verdict cannot report a success, because it is taken at an instant
where success is not yet possible.** A check that cannot come out positive is not measuring what
its name says. This is mine, and it is the single clearest defect the pair of legs exposes; the
log leg alone reads it as "the fingers had not closed", and the video leg alone reads it as "the
close whiffed" — only together do they place the print *before* the motion.

### 3-2. The empty close repeats across runs, and is not a capability limit

t25 (`P18_T25_BLIND_VIDEO_READ_20260729.md` §2) shows the same shape on the idle arm — an empty
close at 11.0–12.0 s — **and** shows the other arm grasping the cable at 23.5–27 s and holding it
stably to the end. ⇒ Grasping works in this cell. t42's failure is not "the hand cannot grasp".
⚠ The t25 read carries the instrument's own attribution caveat (no colour in that run; left/right
assigned behaviourally, possible mirror), so t25 is used here **only** for the two facts that do
not depend on which side is which.

### 3-3. The missing table check is confirmed, not weakened

`:156` L and `:157` R report the lowest point at **−84.2 mm** and **−27.5 mm** versus the table
while the angle check passes on one side (`margin +2.86`). The video sees no table penetration —
and that is consistent, because those are **commanded-state** figures and the run raised its
exception there instead of driving into them. p5 and pB reached this line independently. Rs's own
stated goal quantity (the fingers must not hit the table) is already being computed by that same
print; what is missing is a check that reads it. ⛔ The angle check is not the thing to remove.

---

## 4. What I got wrong, stated plainly

1. ⛔ **"The left arm did not move a step."** Wrong as written. The command *ramp* never advanced
   (that is `prog`, and it is true); the arm itself moved — the video shows the orange arm
   travelling and converging over roughly the first 6.5 s while pinned against the crown at a
   constant `-0.8 mm`. A stalled ramp and a stationary arm are different claims and I merged them.
2. ⛔ **"The stop is the same shape as the two-threshold register item."** Withdrawn. 41.5° is
   outside *both* thresholds, and `:44` shows this run's two numbers agreeing at 5.73/5.73
   (pB §5).
3. ⛔ **Wrong citation** for the right arm's arrival: I cited `:113-114`, which are the GRASP
   non-arrival lines. Correct: `:32` and `:39` (p18 caught it). The claim survives; the pointer
   was wrong, and a wrong pointer is how a true sentence becomes unverifiable.
4. ⛔ **"−0.8 mm persists across STEP2–6" read as five pieces of evidence.** It is one state
   sampled five times (pB §3), and separately the reading is on a link held in contact while the
   arm keeps moving — so it is neither five observations nor proof of stillness.

---

## 5. What follows, in my court (implementation), with the design questions marked

| # | action | why now | authority |
|---|---|---|---|
| A | a check that reads the lowest point versus the table and stops the descent | Rs's own stated goal; the quantity is already computed; two readers converged | mine (implements an existing directive) |
| B | split the command ramp per arm | the code's own comment says per-arm and the code is shared; it turned a one-arm jam into a two-arm freeze | ⚠ touches the follow-control Rs approved as "A" — **holding for a word** |
| C | move the grasp/containment measurement to after the close | §3-1: it currently cannot report success | mine |
| D | the left arm's start-pose solve returns a pose that jams in the crown | `6 solved / 6 collision-free` yet the arm arrives in contact — the clearance screen and the realised path disagree | measure first, then report; no fix until measured |
| E | the two sides stop being mirrors once yaw ≠ 0 (probe §5) | may or may not be intended | ⛔ p5's court — routed, awaiting a one-line ruling |

⛔ Nothing is re-run until A and C are in and B has a word, because a re-run before then would
re-measure the same frozen ramp and produce another trace with the same shape.

---

## 6. Scope of this verdict

- Covers **t42 only**. t25 is cited for two side-independent facts and nothing else.
- **Physical validity of the video is not mine to certify** — the blind instrument reports
  PLAUSIBLE with its own list of five undecidable items (video read §"判定不能"), and Rs remains
  the authority. I am relying on the *absence of collapse*, which is the part the instrument
  states at high confidence.
- The pane court `w2:pC` is unstaffed and both video legs came from p18's independent instrument
  (video read header §5). That substitution is disclosed here because it changes who read, and
  restaffing is Rs's call.
