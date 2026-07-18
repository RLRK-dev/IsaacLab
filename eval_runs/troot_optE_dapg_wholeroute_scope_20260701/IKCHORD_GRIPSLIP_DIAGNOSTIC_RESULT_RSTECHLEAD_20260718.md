# §3 diagnostic RESULT — ik_chord grip-slip mechanism = **M2 (drive-dependent cable displacement)**, M1 REFUTED

**2026-07-18 10:53 JST · RS-TECH-LEAD (w2:p4) → VT-DESIGN (p5).** Executed p5's force-design §3 diagnostic probe
(`IKCHORD_GRIPSLIP_FORCEDESIGN_VTDESIGN_20260718.md`) via `diagnose_ikchord_resid.py` (read-only, wc=1, GOLDEN,
effective-config recorded). Two runs: ik_chord@4 (drops) + FF@4 control (holds). Diagnostic-first — this reports
the MECHANISM; the lever is p5's (§4). Physical validity = Rs.

## Result (window 248-267, median; `ikchord_resid_diag/summary_{ik_chord,feedforward}.json`)
| metric | ik_chord@4 (drop 267, −10) | FF@4 (holds, no drop) | reading |
|---|---|---|---|
| `ik_resid_r` (achieved wrist EE vs commanded target) | **0.24 mm** | **0.24 mm** | BOTH reach the recorded target pose → **IK converges** |
| `fingertip_r_to_cable` (clamp point, not wrist) | **22.0 mm** (≥ CONTACT_PROXIMITY 12 mm → NOT gripping) | **6.3 mm** (< 12 mm → GRIPPING) | same target pose, cable ~16 mm further under ik_chord |
| `wrist_r_to_cable` (reference only) | 266 mm | 266 mm | wrist is far by gripper geometry (ee-pos-is-wrist-flange) |

`fingertip_r_to_cable` (22 mm) reconciles exactly with `grip_retention_measure` r_near (22 mm) — same clamp reference.

## Mechanism (airtight, control-isolated)
- **M1 (IK non-convergence) = REFUTED.** Both drives reach the commanded right-arm target to 0.24 mm — `IK_ITERATIONS_RL=30` IS enough for this target. **The lever is NOT more IK iterations / warm-start.**
- **M2 (cable displaced by the drive) = CONFIRMED.** The right arm is at the SAME recorded grip pose in both drives (ik_resid 0.24 mm), yet the right fingertip is **6.3 mm from the cable under FF (gripping)** vs **22 mm under ik_chord (not gripping)**. Only the drive differs ⇒ **the ik_chord drive path displaces the cable ~16 mm relative to FF**, so the right fingertip (at the correct pose) misses the cable → right arm never engages → left single-arm hold → fast lateral escape (drop 267).
- The 22 mm offset is **persistent across the whole window** (not a transient at the drop) → the displacement is established early (approach/grasp/early-route under ik_chord) and holds.
- **solref is NOT the primary lever** (a contact-stiffness knob cannot grip a cable 22 mm away — the right pad never contacts).

## For p5 (§4 lever selection — this is your call, not mine)
The mechanism is the **M2 branch**: WHY does the ik_chord drive leave the cable ~16 mm from where FF (recorded arm_q replay) leaves it, at the same right-arm target pose? Candidate sub-mechanisms for p5 to adjudicate:
- ik_chord's **arm PATH** (10-frame joint-chord interpolation to the target) vs FF's direct recorded-arm_q replay — does the ik_chord trajectory drag/knock the cable during approach/route?
- the **LEFT arm's** ik_chord grip/path holding the cable in a config ~16 mm off vs the recording (the left arm is the one still holding at the drop).
- a **target/phase** timing mismatch between the ik_chord targets and the cable state.
Diagnostic levers available cheaply (residual + fingertip already wired): FF-vs-ik_chord path deviation per phase, left-arm fingertip_l_to_cable comparison, cable-body displacement trace.

## Gate chain (unchanged from p5 §8, M1 branch dropped)
p5 §4 lever (M2 branch) → design-gate → **L3 CC-Debate** → rule-check → impl → **re-measure** (FIXED harness:
effective-config + right-arm `fingertip_r_to_cable`/`contact_r`/dual-load in DoD). ⛔ invariant guard (§6): if the
lever would change dual-arm/88mm/DiffIK/コ/no-trick → STOP+Rs.

## Note (own-it, verification discipline)
My first diagnostic run mismeasured the cable distance using the raw EE/wrist body (266 mm) instead of the clamp
point (fingertip). I caught it by cross-checking against `grip_retention_measure`'s 22 mm, fixed to `clamp_pos_ko`,
and re-ran (22 mm, now consistent). The `ik_resid_r` finding (M1 refuted) was unaffected (EE-vs-target, no reference bug).

## §2 diagnostic (1) left fingertip + onset timing (2026-07-18 11:16, from existing per-step data, no GPU)
**REFINES the phase: the displacement is NOT approach/grasp — it is a MID-ROUTE right-arm disengagement.**
- **Grasp SUCCEEDS in ik_chord**: at step 90 both fingertips are ~2 mm from the cable (dual grip established, same as FF). So it is not an approach/grasp displacement.
- **Right arm disengages MID-ROUTE**: ik_chord `fingertip_r_to_cable` diverges from FF at **onset step 176** (11 mm vs FF 4.4 mm), **spikes to 52 mm at step 195**, then settles to ~22 mm (route_t 177-196 = mid-route). FF right stays ~6 mm (gripping) the whole route.
- **Left arm holds until step 261**: ik_chord `fingertip_l_to_cable` stays ~5-10 mm (gripping) through step 260, then spikes (13 → 44 → 65 mm at 262-267) at the drop. So the sequence is: **dual grasp OK → RIGHT disengages mid-route (176-195) → left single-arm route → left disengages (261) → drop (267)**.
- ⇒ the **right arm is primary**, and the trigger is a **specific mid-route motion at step 176-195** (route_t 177-196), not the approach/grasp. p5's arm-path branch stands; the phase is corrected to mid-route.

Remaining to isolate (diagnostic 2/3, EE + joint-config instrument at the 176-195 window): H-a config-jump vs H-b interp-curvature, and whether the 52 mm spike is a right-arm route motion or a left-arm coupling. In progress.

## §3 diagnostic (3) EE + joint-config deviation at 176-195 (2026-07-18 11:27, extended instrument, ik_chord@4)
Per-step right-fingertip motion (`dClampR`), arm joint-config delta (`dJointQ`), and fingertip-to-cable, steps 168-201:
| window | dClampR/step (median) | dJointQ/step (median, max) | fingertip_r_to_cable |
|---|---|---|---|
| 176-195 | **1.67 mm** | **0.0093 (max 0.0183 — no spike)** | grows 9 → 52 mm monotonically |
| 100-170 baseline (stable grip) | 1.33 mm | 0.0066 | ~6-9 mm (gripping) |

**Findings:**
- **H-a (IK config-jump) = REFUTED.** `dJointQ` is smooth (0.0093, no spike/discontinuity — warm-start `:1173` works). The arm config does NOT jump at the disengagement.
- The right arm moves **moderately** during the window (1.67 mm/step ≈ 1.3× baseline = a routing motion, NOT a large sweep). The joint path is continuous.
- **The right grip separates STEADILY (9 → 52 mm) during this routing motion** while the arm reaches its commanded end pose each step (ik_resid 0.24 mm) and the config is smooth.
- ⇒ (INFERENCE, not directly measured within-step) the remaining explanation is **H-b (interp path)**: the linear-joint interp within each step follows a path that differs from FF's recorded arm_q, gradually walking the right grip off the cable during the routing motion. The end poses match (ik_resid 0.24 mm), so the difference lives in the within-step path.

**Decision-relevance for p5:** the **cheap H-a config-continuity lever is OUT** (config already smooth). The indicated lever is the **expensive H-b task-space incremental EE interp (~10× IK cost, p5 §10.4)**. ⚠ Recommend confirming H-b directly before committing to the 10× cost: a within-step per-frame EE-path probe (does the ik_chord EE bow vs FF within a step?) or diagnostic (2) cable-body displacement trace. p5's call on the lever + whether to run the confirmation.

## §4 diagnostic (2) 3-quantity correlation (p5 G1) — cable-motion vs arm-motion (2026-07-18 11:35, ik_chord + FF, cable-body trace)
Tracked the cable segment nearest the right fingertip at step 170 (pre-divergence) and measured its WORLD displacement vs each arm's clamp motion over 176-195 (`ikchord_resid_diag/per_step_{ik_chord,feedforward}.json`):
| drive | cable seg world-move (176-195) | clampR move | clampL move | seg↔clampR | reading |
|---|---|---|---|---|---|
| **FF (holds)** | **33.9 mm** | 33.3 mm | 33.3 mm | ~6 mm held | cable segment moves = the arm (33.9 ≈ 33.3) → tracks the grip |
| **ik_chord (drops)** | **80.8 mm** (spike 14 mm/step @186-187) | 33.4 mm | 33.4 mm | 6.6 → 52 mm | cable moves **2.4× the arm** → displaced extra, grip lost |

**Resolves p5's G1 question ("did the cable move, or did the right EE separate?"): the CABLE MOVED.**
- The **arm END motion is IDENTICAL in both drives** (clampR/clampL = 33 mm; `ik_resid_r=0.24 mm` both → both reach the same recorded poses each step). So it is NOT the right EE separating and NOT a config-jump (§3: joint smooth).
- The **cable segment moves EXTRA in ik_chord** (80.8 vs 33.9 mm; the arm moves 33 mm in both) → the cable is pushed ~47 mm beyond the arm's motion, with a spike at step 186-187.
- ⇒ Since the arm end-poses match but the cable moves extra, the displacement comes from the **within-step arm PATH** (ik_chord's linear-joint interp → curved EE micro-sweep, vs FF's recorded smooth arm_q). The curved within-step sweep pushes the cable extra during the routing motion → **H-b (interp-curvature) CONFIRMED** (now direct, not just inferred). Consistent with p5 G2 (substep leaves the EE geometric path unchanged → cannot fix H-b).

**Lever (p5 §10.4/§10.6 call): H-b → task-space incremental EE interp (~10× IK).** Not H-a config-continuity (config already smooth), not solref (cable moves, not a static contact gap).

⚠ **Right-vs-left not fully isolated**: both arms use the same joint-interp and move identically, so the within-step curved sweep afflicts BOTH arms; the tracked (near-right) segment is displaced by the drive's within-step path. The H-b task-space-interp lever applies to the DRIVE (both arms), so it covers the mechanism regardless of which arm's sweep dominates the near-right segment. If p5 needs the per-arm attribution (e.g., to fix only one arm's path = §10.6 coupling branch), a directional correlation of the segment motion with each arm is a cheap follow-up.

## §5 diagnostic P2 (p5 §10.7) — H-b sub-fork M-b1 (within-step shape, ~10×) vs M-b2 (config diff, cheap) → **M-b2 CONFIRMED**
p5's on-disk catch (my §4 missed it): the batched IK action is **position-only** (`ik_resid` is a POSITION residual `:1290`; wrist rot target is HELD-KO `:955`/`:1005-1006`), so the IK is free to pick any config/orientation achieving the target position. Tested M-b1 vs M-b2 on existing data (no GPU):

**P2a (orientation, via clamp point):** `|clamp_r(ik) − clamp_r(ff)|` = **0.82 mm** (constant, 176-195), `|clamp_l|` = 0.71 mm. The fingertips (clamp points, which encode EE orientation) COINCIDE between the two drives → wrist orientation is NOT different. So the fingertip mismatch (22 vs 6 mm) is the cable being displaced, not a mis-oriented fingertip.

**P2b (config / IK branch, via arm joint_q):** `|arm_joint_q(ik) − arm_joint_q(ff)|` wrap-corrected over 176-195:
| arm | true config diff (rad) | joints |
|---|---|---|
| **LEFT (j0-13)** | **0.034** (≈ matches recorded) | all < 0.02 |
| **RIGHT (j14-27)** | **4.32** (a DIFFERENT IK branch) | j14=2.37, j16=1.96, j17=1.89, j19=2.37 (shoulder/elbow/wrist) |

Time profile: the right-arm config diff is already **3.93 rad at grasp (step 90)** and grows slowly (3.93 → 4.40 over the route); the fingertip grips (2-7 mm) until step 176 despite the wrong branch, then diverges.

**Conclusion — M-b2 (config difference) CONFIRMED; M-b1 (within-step shape) REFUTED:**
- endpoints coincide (`ik_resid` 0.24 mm) + clamps coincide (0.82 mm) ⇒ NOT a within-step EE-bow (M-b1) and NOT orientation.
- the **right-arm IK converges to a different config branch** (elbow/shoulder flipped ~2 rad, same wrist/fingertip pose) than the recorded arm_q, **from grasp onward**; the left arm matches recorded. The flipped right-arm links make the grip fragile → it fails under the route motion at 176.
- ⇒ **the lever is CHEAP, not the ~10× task-space interp**: bias/seed the right-arm IK to the recorded config branch (warm-start from recorded arm_q / null-space regularization toward recorded / branch selection). p5's refusal to rubber-stamp ~10× (§10.7) was correct.

**For p5 (§10.7 fork):** M-b2 branch → the cheap config-continuity-toward-recorded lever. Exact form (warm-start source, null-space bias, or explicit branch pick) + physical-validity (does the recorded-branch right arm keep the links clear of the cable) is p5's design call. The precise HOW the flipped branch loses the grip (forearm/elbow sweep vs another coupling) is a p5 analysis; the diagnostic establishes the WHAT (wrong right-arm branch, cheap fix).
