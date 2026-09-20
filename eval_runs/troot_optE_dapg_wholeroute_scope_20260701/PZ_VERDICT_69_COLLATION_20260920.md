# pZ — verdict on the #69 collation leg (`PZ_69_COLLATION_LEG_PREREG_20260920.md` @ `94d7e04e18`): rows C-1..C-6 on p0's pinned products, and the collation with pB's verdict — every number equal; no return

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-20 23:35:20 JST on m-p18-482 (pB verdict landed; pZ = C-3 + C-1/C-2/C-4/C-5 → one file). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. This line is one input to p4's acceptance word (after pB's verdict, VERDICT_C and Rs1's eye); it judges numbers against pre-registered expectations and **says nothing about physical validity** (Rs1's eye) or about the cause of the stop (p4's ruling after pB's (iii)).

**Order of existence**: pre-registration `94d7e04e18` (committed 23:09:30; rows, bars, instruments by sha; products unread) ≺ this desk's first read of any product (this leg, 23:2x) — the products themselves were produced 22:55-23:03 and pinned by p0 at 23:07 (§8.66 @ `4583fa7444`; run.log force-added @ `0d22720834`). HEAD at writing `57fa59fa47`. **Inputs (fetched from git, sha256 verified before reading)**: `run.log` @ `0d22720834` blob `c79fdfd1d410` = `9fe9685aba333506df9d9199e3cfe826e62c715899e48b8ca2034d8a796b22fa` (402 lines); `RUN_METRICS.json` @ `4583fa7444` = `bcf7fa5783b1e60207f34ac7fb2ad905920e87964eb21dd010b4179bbdedf8e4`; the run's cell dump `_steps_cell_full.xml` @ `4583fa7444` = `f650fc322781a915dbb72565aa60d19d6bb7b1d9db9ecdbfb0b39969cd1ae4e0` (= `RUN_METRICS` `ur15_steps.cell_dump.sha256`); pB's verdict `PB_RUN69_ROW7_R3_STOP_LOGANALYST_20260920.md` @ `8b16ce641a` blob `15c5f1f65242` = `b8a3ab568ddf6abba6aee1d806dcd3ccd12e713d488164193078e266d696557a` (210 lines). Nothing modified; run 0; instruments `pz_69_log.py` `ea122b25080c3f84…` / `pz_69_dump.py` `b8ca76268e644811…` = the registered shas, each run once. **Stop-cause tag of the run** (quoted, not assigned here): p0 §8.66 = **controller の不収束** (the driver's stall raise `:3996-3997`); this leg's own stop-cause tag: **none**.

## Verdict per row

| # | row (bar as pre-registered) | verdict | measured |
|---|---|---|---|
| C-1 | row 7: the two `[steps] controller record` lines vs `e41d0a9304` `:16` (18 numbers ≤ 1e-6; relation ≤ 1e-6; zero signs ignored) | **CONFIRMED** | lines `:41` (L) and `:42` (R) present; L max\|diff\| **0.00e+00**, R **0.00e+00**, relation `AXFIX_R − diag(1,−1,1)·AXFIX_L·A` **0.00e+00** — the printed rows are exactly c=[0 +1 0] s=[+1 0 0] a=[0 0 −1] on both sides (negative zeros in the print compared as numbers) |
| C-2 | R3-i: `[steps] vertical check` cap prints = `5.73` ×3 | **CONFIRMED** | line `:112`: `cap 5.73`, `(L 5.73 / R 5.73`; allowance **5.73** (recorded, no bar — `vertical_tol_deg()` evaluates to the cap here) |
| C-3 | collation with pB's verdict (`8b16ce641a`): its numbers == this desk's | **CONFIRMED — no differing number** | pB: row 7 L/R max 0.000e+00, relation 0.000e+00; cap 5.73, (L 5.73 / R 5.73), allowance 5.73; Traceback 1 at `:375`, raise from driver `:3996`, `RuntimeError` message at `:378` byte-equal to `RUN_METRICS`; `end_reason` raised, `exit_code` 1, `phase_max_reached` 2; tag 「controller の不収束」 three-way; `tool_err_mm` step1 L 658.4929864857596 / R 2.1924360046211926, step 2 L 1126.4214452980132 / R 2.1632956854191416; **pB issues no PASS** — each item re-read here from the same blobs: row7 L max, row7 R max, relation, cap, allowance 5.73, Traceback :375, raise :3996, end_reason raised / exit 1, tag controller non-convergence, phase_max_reached 2, tool_err 658.4929864857596 / 2.1924360046211926 / 1126.4214452980132 / 2.1632956854191416, no PASS issued (pB's own words: PASS ではない) — all equal. This desk's own read of `RUN_METRICS` `tool_err_mm` fields: `{"step1_approach.L.tool_err_mm": 658.4929864857596, "step1_approach.R.tool_err_mm": 2.1924360046211926, "steps[0].tool_err_mm.L": 1126.4214452980132, "steps[0].tool_err_mm.R": 2.1632956854191416}` |
| C-4 | injected parameters, text vs text, on **the run's** dump (`f650fc322781a915…`) | **CONFIRMED** | **40/40** attribute pairs L == R (6 arm actuators × 4, 6 J6 joints × 2, fingers actuator × 4); L values match the pinned rule constants (kp 10000/1200, bias (0, −kp, −0.06·kp), force ±433/204/70, ctrl LIMS, armature 0.1, damping 1) — R2-9's "effective values" hole is closed at the text level of the built cell. **The run's dump vs the 09-05 dump** (`4158e4e6…`, this desk's R0 target source): `diff` = 2 hunks, 3 lines per side — `crown` capsule half-length 0.22 → 0.28 and both `*_shoulder_link` mount `pos`/`quat` — = p4's item 78 ① reading (C-2 default 0.28/20° vs the 0.22/45° built cell); no actuator, joint or cable line differs. Reported to p4; the consequence for the R0 targets (rows 2-5 came from the 09-05 dump's cable rest) is p4's/p11's to read |
| C-5 | stop-cause tags (counted, quoted) | **as recorded** | `Traceback` ×1 (`:375`), `RuntimeError` ×2 (the raise statement and the message line; line numbers in Appendix A), `[steps] STOP` ×0; `RUN_METRICS.run` = `{"end_reason": "raised", "exit_code": 1, "elapsed_s": 483.301}`, exception `RuntimeError: STEP2 L: THIS arm's command stopped advancing for a whole step's worth of ticks …`; p0's tag line present (§8.66) — the three agree; **whether the stall is 「controller の不収束」 or a geometric jam (p4's observation E: L tool err 658.5 mm at STEP1, `R_shoulder_link`–column contact) is p4's ruling after pB's (iii), not this row's** |
| C-6 | no run, no parameter | **CONFIRMED** | text instruments only on git blobs; products unmodified; route run (2)・D4′・WIP untouched |

**Reading (fact, not design)**: the controller record and the cap print of the authorized run are exactly what the composed-model pre-registrations predicted, the two log readers (pB's and this desk's, independent code on the same bytes) agree on every number, and the built cell's injected parameters are side-identical text. Nothing in this leg says the route step succeeded — it did not (STEP 2 stall, `phase_max_reached` 2, no final video) — and nothing here grades that; the visual leg (pC) and Rs1's eye read the 2.2 s live video.

## What this leg does not show (holes)
- Row 7 and R3-i are start-of-run prints (before any pose is judged): they say the controller class, the tool axes and the cap are as pre-registered, not that the motion is right.
- C-4 reads the dump text; effective dynamics under contact are #69's run itself and pB/pC/Rs1's.
- The stop's cause, and whether the 09-05-dump-derived R0 targets still name the built cell's cable rest, are open for p4/p11.

## Appendix A — `pz_69_log.py` output (verbatim; sha256 ea122b25080c3f84f75f4faba951e227615f547acf6d82487ef6c90d092dd3e5)
```text
row7 L AXFIX vs expectation max|diff|: ('0.00e+00', 'PASS')
row7 R AXFIX vs expectation max|diff|: ('0.00e+00', 'PASS')
row7 relation AXFIX_R vs diag(1,-1,1).AXFIX_L.A max|diff|: ('0.00e+00', 'PASS')
R3-i printed cap / L / R (want 5.73): (('5.73', '5.73', '5.73'), 'PASS')
R3-i allowance (recorded, no bar): 5.73
stop lines (recorded): Traceback / RuntimeError / '[steps] STOP': (1, 2, 0)
overall: PASS
```
The three lines it read (run.log, line-numbered, truncated at 260 chars):
```text
41:[steps] controller record L: class=existing per-arm 6D DLS + position servo; AXFIX c=[+0.000000 +1.000000 -0.000000] s=[+1.000000 -0.000000 -0.000000] a=[-0.000000 +0.000000 -1.000000]; QADR=[np.int32(0), np.int32(1), np.int32(2), np.int32(3), np.int32(4), 
42:[steps] controller record R: class=existing per-arm 6D DLS + position servo; AXFIX c=[+0.000000 +1.000000 +0.000000] s=[+1.000000 -0.000000 +0.000000] a=[+0.000000 +0.000000 -1.000000]; QADR=[np.int32(14), np.int32(15), np.int32(16), np.int32(17), np.int32(
112:[steps] vertical check: allowance 5.73 deg, cap 5.73 deg (the smallest non-zero tilt the attitude menu can make, measured as pinch->mouth against world -z, not as a roll); the allowance is an interim until a run reports the worst residual an upright comman
```
Stop lines:
```text
375:Traceback (most recent call last):
377:    raise RuntimeError(
378:RuntimeError: STEP2 L: THIS arm's command stopped advancing for a whole step's worth of ticks and its move did not finish (the other arm was still advancing, at 100.0% -- the ramps are per arm now
```

## Appendix B — `pz_69_dump.py` output (verbatim; sha256 b8ca76268e64481128a7a83e20a23c66c1dce8f38aafe87fc3beade102368dd6)
```text
[dump] shoulder_pan_joint_act.gainprm           L=10000                    R=10000                    eq
[dump] shoulder_pan_joint_act.biasprm           L=0 -10000 -600            R=0 -10000 -600            eq
[dump] shoulder_pan_joint_act.forcerange        L=-433 433                 R=-433 433                 eq
[dump] shoulder_pan_joint_act.ctrlrange         L=-6.28319 6.28319         R=-6.28319 6.28319         eq
[dump] shoulder_pan_joint.armature              L=0.1                      R=0.1                      eq
[dump] shoulder_pan_joint.damping               L=1                        R=1                        eq
[dump] shoulder_lift_joint_act.gainprm          L=10000                    R=10000                    eq
[dump] shoulder_lift_joint_act.biasprm          L=0 -10000 -600            R=0 -10000 -600            eq
[dump] shoulder_lift_joint_act.forcerange       L=-433 433                 R=-433 433                 eq
[dump] shoulder_lift_joint_act.ctrlrange        L=-6.28319 6.28319         R=-6.28319 6.28319         eq
[dump] shoulder_lift_joint.armature             L=0.1                      R=0.1                      eq
[dump] shoulder_lift_joint.damping              L=1                        R=1                        eq
[dump] elbow_joint_act.gainprm                  L=10000                    R=10000                    eq
[dump] elbow_joint_act.biasprm                  L=0 -10000 -600            R=0 -10000 -600            eq
[dump] elbow_joint_act.forcerange               L=-204 204                 R=-204 204                 eq
[dump] elbow_joint_act.ctrlrange                L=-3.14159 3.14159         R=-3.14159 3.14159         eq
[dump] elbow_joint.armature                     L=0.1                      R=0.1                      eq
[dump] elbow_joint.damping                      L=1                        R=1                        eq
[dump] wrist_1_joint_act.gainprm                L=1200                     R=1200                     eq
[dump] wrist_1_joint_act.biasprm                L=0 -1200 -72              R=0 -1200 -72              eq
[dump] wrist_1_joint_act.forcerange             L=-70 70                   R=-70 70                   eq
[dump] wrist_1_joint_act.ctrlrange              L=-6.28319 6.28319         R=-6.28319 6.28319         eq
[dump] wrist_1_joint.armature                   L=0.1                      R=0.1                      eq
[dump] wrist_1_joint.damping                    L=1                        R=1                        eq
[dump] wrist_2_joint_act.gainprm                L=1200                     R=1200                     eq
[dump] wrist_2_joint_act.biasprm                L=0 -1200 -72              R=0 -1200 -72              eq
[dump] wrist_2_joint_act.forcerange             L=-70 70                   R=-70 70                   eq
[dump] wrist_2_joint_act.ctrlrange              L=-6.28319 6.28319         R=-6.28319 6.28319         eq
[dump] wrist_2_joint.armature                   L=0.1                      R=0.1                      eq
[dump] wrist_2_joint.damping                    L=1                        R=1                        eq
[dump] wrist_3_joint_act.gainprm                L=1200                     R=1200                     eq
[dump] wrist_3_joint_act.biasprm                L=0 -1200 -72              R=0 -1200 -72              eq
[dump] wrist_3_joint_act.forcerange             L=-70 70                   R=-70 70                   eq
[dump] wrist_3_joint_act.ctrlrange              L=-6.28319 6.28319         R=-6.28319 6.28319         eq
[dump] wrist_3_joint.armature                   L=0.1                      R=0.1                      eq
[dump] wrist_3_joint.damping                    L=1                        R=1                        eq
[dump] fingers_actuator.gainprm                 L=0.313725                 R=0.313725                 eq
[dump] fingers_actuator.biasprm                 L=0 -100 -10               R=0 -100 -10               eq
[dump] fingers_actuator.forcerange              L=-5 5                     R=-5 5                     eq
[dump] fingers_actuator.ctrlrange               L=0 255                    R=0 255                    eq
[dump] L vs R text: 40/40 pairs equal -> PASS
[dump] rule check on L (reported): all match the pinned constants
```
`diff` of the 09-05 dump copy (`4158e4e6…`) against the run's dump (`f650fc322781a915…`), verbatim:
```diff
131,132c131,132
<       <geom name="crown" size="0.11 0.22" pos="0 0 1.44" quat="0.707107 0 -0.707107 0" type="capsule" material="col"/>
<       <body name="L_shoulder_link" pos="-0.374574 0 1.68457" quat="0 -0.382683 0 0.92388" gravcomp="1">
---
>       <geom name="crown" size="0.11 0.28" pos="0 0 1.44" quat="0.707107 0 -0.707107 0" type="capsule" material="col"/>
>       <body name="L_shoulder_link" pos="-0.485417 0 1.60477" quat="0 -0.573576 0 0.819152" gravcomp="1">
242c242
<       <body name="R_shoulder_link" pos="0.374574 0 1.68457" quat="0 0.382683 0 0.92388" gravcomp="1">
---
>       <body name="R_shoulder_link" pos="0.485417 0 1.60477" quat="0 0.573576 0 0.819152" gravcomp="1">
```

## Provenance
Products by `git show` at the pinned commits (sha256 checked against p0 §8.66 / hub §1620 before any parse); pB's verdict by `git show` at `8b16ce641a`; instruments = appendices A/B of the pre-registration (shas equal). Zero tracked-content modifications by pZ other than this file. Committed under the standing custody form (m-p18-342/344), pathspec-limited, `--no-verify`, no push; hub instruction m-p18-482. Not sent to pC (v2-6).


## Addendum 1 (2026-09-20 23:41:56 JST; re m-p18-483 / m-p18-486 / m-p18-488) — C-3 re-collated on pB's latest commit; C-5's class word re-cited to p4's ruling (item 86); one line-cite slip in pB's Addendum 1 reported, not returned

HEAD at writing `e6b3fed386`; this file's prior commit `160e06ce0f`; run 0; no product modified.

**A-1 · C-3 on the moving pB file (each commit judged against its own parent; prefix compared as bytes to the `8b16ce641a` blob that the table above collated):**

| commit | time | blob | sha256 | lines | numstat vs parent | first 210 lines vs `8b16ce641a` |
|---|---|---|---|---|---|---|
| `8b16ce641a` | 23:23:23 | `15c5f1f65242` | `b8a3ab568ddf6abb…` | 210 | +210 / −0 | identical |
| `4711c2c248` | 23:27:22 | `de0e6677f96c` | `b34edbe9a7b36b51…` | 262 | +52 / −0 | identical |
| `e36c84a161` | 23:29:43 | `850860c4d8df` | `2fe36e586cc3137a…` | 268 | +6 / −0 | identical |
| `ff396f98e6` | 23:37:27 | `b45f792fd068` | `09afb7f82babb8d0…` | 274 | +6 / −0 | identical |

Commits touching the file after `ff396f98e6` at reading: **0**. Every step is append-only and the 210-line prefix is byte-identical, so **every number C-3 collated is unchanged at `4711c2c248` and at `ff396f98e6`** — the C-3 verdict stands with the cite moved to the latest commit.

**A-2 · pB's Addendum 1 (the observation-E material) re-read against the same run.log blob `c79fdfd1d410` (sha `9fe9685aba333506…`) and `RUN_METRICS`:** its 30 bullet cites of the form `:NNN` + quoted text → **30/30 text-equal** to the cited line; `steps[0].command` (L 0.0 / 10560 of 10560 / stalled true; R 1.0 / 0 / false), `steps[0].sigma_min` (L 0.11047350128312033 / R 0.151651571628065), `steps[0].mast` (L −0.6403175818046059 mm, g12 on Lg_base vs crown), `steps[0].arm_to_arm.closest_mm` −1.1194554926176923 — all equal. **One cite slip (reported, not a return):** A1-4 (b) writes "`:369` ARM-TO-ARM −1.1 mm"; in the blob the ARM-TO-ARM line is **`:367`** (`[steps] STEP 2 ARM-TO-ARM: closest -1.1 mm (9 <-> 42)  <- TOUC…`) and `:369` is the CARRY line (`[steps] STEP 2 CARRY: L mouth[+0.394…`). The number is right, the line number is off by two in a pointer sentence; the bullet list itself does not cite `:367` at all. pB's to fix append-only if it wishes; nothing in this desk's rows depends on it.

**A-3 · C-5 class word:** the count stays **1 stop / 1 tag**. The class quoted in the C-5 row (「controller の不収束」, p0 §8.66 @ `4583fa7444`) is **superseded** by p4's chain-court ruling, kickoff item 86 @ `57fa59fa47` (23:35:17): class = **「その他」**, tag text verbatim 「その他: driver の追従 gate（stall raise `:3996`）・原因 = L 腕 rest 姿勢の接触（column・R_shoulder_link）と 3 関節の力飽和・IK は solved・§11／calibration 不発・R 腕は追従」. Follow-ups read at their commits: p0 §8.66 addendum 6 @ `88dc6842aa` (insertion, existing lines untouched); pB Addendum 3 @ `ff396f98e6` (pointer); p11 §17.26 @ `48ad9c1e37` (design court: §17.4 applied as defined, no objection). This desk does not rule the class; C-5 now cites item 86 for the word. This leg's own stop-cause tag: **none**.

**A-4 · Nothing else changes.** C-1, C-2, C-4, C-6 untouched; no return reason; acceptance remains p4's word after Rs1's eye.


## Addendum 2 (2026-09-21 01:29:01 JST; re m-p18-490 / 493 / 494 / 495 / 496 / 498 / 500) — the open item this verdict left at `:23` is closed here **by measurement at this desk**; pB's corrected file re-checked at its newest commit; the adopted carry re-derived, with its limit

This file's prior commit `675c6b459d`; HEAD at writing `7b3a76e1f9`; **run 0**, no product modified, no parameter touched, nothing re-run. #69 was **accepted** by p4 (item 95 @ `70e6417e46`, 01:20:22, relayed m-p18-498) and this addendum adds no claim about the run's outcome: physical validity is untouched here and, as p4's own record states, human ground truth remains unapplied to this run.

### A-5 · The open item at `:23` — "do the 09-05-dump-derived R0 targets still name the built cell's cable rest?" — **yes**, measured here rather than taken from the desks that answered it

Answers received, each read at its own pin and judged against its own parent: p11 §17.27 @ `e6b3fed386` (420 lines, +7/−0, sha `6dbcd12da2cb0c13…`), §17.28 @ `7df8773e45`, §17.29 @ `912c67f920` (441 lines, +13/−0, sha `0124f59d925c1ce7…`); p4 item 91 @ `181babc70a` word 2, item 93 @ `e19d767680` word 1, item 97 @ `e47cc510a3`; p0 §8.66 addendum 11 @ `d6a4613825`. Four desks agreeing is not a re-derivation, so this desk measured the question:

1. **Structure of both dumps (parsed, not diffed).** 87 bodies each; 40 cable bodies `cab0..cab39`; the **cable subtree XML is byte-identical**; every cable body's ancestor chain is `<worldbody> → cab0 → …` and contains **no other body**, so it is disjoint from the bodies whose lines differ (the `crown` geom sits inside body `column`; the rest are `L/R_shoulder_link`). The cable's initial-state forward kinematics is therefore identical in the two dumps **by construction**, not by numerical coincidence — which is the step "the diff shows no cable line" leaves open.
2. **The grid values re-derived from the dump text** (a second source, independent of the constants module): `cab0` pos = `-0.3 0.28 0.954`, every child pos = `0.015 0 0`, **no `quat` attribute and no joint `ref`** on any cable body ⇒ the chain sum plus half a segment gives link centres **c27 = 0.112500** and **c32 = 0.187500** at y 0.28, z 0.954 — equal to the closed form from the constants (x0 = −CABLE_SEG·CABLE_N/2 = −0.300000, z0 = REST_TOP + CABLE_R = 0.954, REST_Y = 0.28), and identical in both dumps.
3. **What the target path actually reads** (harness `r0_convergence_harness.py` @ `8e5905539c`, read as text, never imported): `_grasp_targets` `:1002-1050` loads the dump, runs `mj_forward` at its initial state, binds the cable bodies **by name** (`:1023`, so body order cannot matter), and `cable_at` `:936-943` picks `argmin |C[:,0] − x_cmd|` with C = xpos + R·(CABLE_SEG/2, 0, 0); the two paths must agree ≤ 1e-9 **in value and in link number** or the instrument stops (`:1042`). No arm, mount, crown or column quantity enters either path.
4. **The accepted R0 leg's own record** (this desk's earlier verdict `PZ_VERDICT_8e5905539c_R0_LEG_20260920.md` @ `2bd3be01c2`): `dump_sha256 = 4158e4e638e9b0fc…` (the 09-05 dump), `env_overrides_set = {}`, `17.7 env unset (GRASP_CENTRE_X, WORK_ROW_DY) = (True, True, 0.15, 0.0)`, §17.7 paths agree to 1.7e-16, `mj_step_calls = 0` ⇒ that execution ran on the **cell-spec defaults** — the same mount and the same grasp centre as #69, whose `env_before.txt` / `env_after.txt` @ `4583fa7444` `:5` `:10` `:21` `:25` show `CROWN_R_OVERRIDE`, `GRASP_CENTRE_X`, `TILT_DEG_OVERRIDE`, `YOKE_SPREAD_OVERRIDE` all `<unset>` **before and after** the run.

⇒ 1-4 close the item: evaluating path (b-1) on #69's dump returns the same GL/GR and the same link numbers. The optional `mj_forward` confirmation line would print a number these four already fix; p4 ruled it unnecessary (item 93) and this desk's measurement agrees for a reason of its own.

**Corroboration inside the run** (a partly independent instrument — the driver, a different code path, shared constants): run.log `:44` L=`cab27` [0.1125 0.28 0.9486], R=`cab32` [0.1875 0.28 0.9509] = the targets' links and x/y (dx = dy = **0.000 mm**), z below the rest 0.954 by **5.4 mm (L)** and **3.1 mm (R)**; the driver's own print on that line reports the **L−R difference** as "drop across the span = 2.3 mm" — two different quantities, both stated here so neither is read as the other. run.log `:101` (re-measured after the approach) L=`cab26` [0.0986 0.28 0.9488] R=`cab32` [0.1886 0.28 0.951] equals the harness's `U0_SETTLED` constants (`:118`) at the printed precision (1e-4 m).

### A-6 · The carry p4 adopted (item 97, form ①-⑧) re-derived here by arithmetic — and its limit

The selection inputs, read in their blobs: `x_cmd = GRASP_CENTRE_X ∓ GRIP_HALF_SPAN` (harness `:1005`), `GRASP_CENTRE_X = float(os.environ.get("GRASP_CENTRE_X", C1[0]))` (harness `:164`, driver blob `84a372439c59` `:1246`), `C1 = (0.150, …)` (cell_spec blob `6bdf7ea4f9ca` `:499`), `GRIP_HALF_SPAN = 0.044` (task_config @ `96e9ece175` `:235`). Recomputed at this desk (appendix D): 0.1500 → L cab27 / R cab32, 0.1575 → R cab33, 0.1600 → R cab33, 0.1650 → L cab28 / R cab33, 0.1700 → L cab28 / R cab34 — equal to p0's as-run sweep and p11's closed form; **quantisation floor = half pitch 7.5 mm**. Also measured, and already on the record rather than new: at the default the two named link centres sit **75.000 mm** apart while the commanded span is **88.0 mm** (2 × GRIP_HALF_SPAN) — the 15 mm link pitch quantises it; the driver flags the same thing at `:92` ("commanded span, not the links actually held") and the R0-iii leg banked Δ_pair 75.000 → 107.314 mm.
**Limit, stated plainly:** p0, p11, p4, the hub and this desk all read the same rule text and the same constants. Five re-derivations of one source are not five instruments; the partly independent one is run.log `:44`, and it agrees at the default centre only.

### A-7 · pB's file at its newest commit (m-p18-496) — C-3 unchanged, and the correction verified in the named objects

| commit | time | blob | sha256 | lines | numstat vs parent | first 210 lines vs `8b16ce641a` |
|---|---|---|---|---|---|---|
| `8b16ce641a` | 23:23:23 | `15c5f1f65242` | `b8a3ab568ddf6abb…` | 210 | +210 / −0 | identical |
| `4711c2c248` | 23:27:22 | `de0e6677f96c` | `b34edbe9a7b36b51…` | 262 | +52 / −0 | identical |
| `e36c84a161` | 23:29:43 | `850860c4d8df` | `2fe36e586cc3137a…` | 268 | +6 / −0 | identical |
| `ff396f98e6` | 23:37:27 | `b45f792fd068` | `09afb7f82babb8d0…` | 274 | +6 / −0 | identical |
| `77ba6e0b25` | 01:17:39 | `80b756e4347b` | `7cf7b3324f54ae72…` | 303 | +29 / −0 | identical |
| `659a014a4a` | 01:25:55 | `2314d08d4eb5` | `5a1e0f372710e45d…` | 311 | +8 / −0 | identical |

Commits touching the file after `659a014a4a` at reading: **0**. Every step is append-only and the 210-line prefix is byte-identical ⇒ **C-3's numbers are unchanged**; the C-3 cite target moves to `659a014a4a`. The added-line count of the newest step measures **+29 / −0** here (the hub's m-p18-496 body said +18/−0 and corrected itself in m-p18-498; this desk's figure was taken from `git diff --numstat`, independently).

**Machine re-check of the file at its newest commit** (appendix C): 124 `:NNN` tokens, of which 46 carry an adjacent quoted line and **43/46 sit on the named line** of the run.log blob `c79fdfd1d410`, the run's driver blob `84a372439c59`, or the driver blob `75eefef4e27e` that commit `22feba17a6` carries. The 3 that do not are each accounted for: file line 59 is the original §3 row pairing `:369` with the ARM-TO-ARM text, which Addendum 4 names as error site 1 (append-only leaves the original in place); file line 284 is the erratum row that quotes the wrong pairing in order to correct it; file line 308 quotes `:1300` in the abbreviated form `upright = [attitude_tilt_deg(...)]`, and that line does carry that call verbatim as `upright = [attitude_tilt_deg(y, r) for y, r in _spec.GRASP_ATTITUDES if abs(r) < 1e-9]` ⇒ **no wrong line number and no unnamed mismatch**. The other **78 tokens are pointer-only and this instrument cannot decide them**; pB reports machine-checking 93 prose cites and, in Addendum 5, all 38 hex identifiers in the file by `git cat-file -t`. The corrections re-read in their objects: run.log `:367` is the ARM-TO-ARM line and `:369` the CARRY line; the run's own driver blob carries the calibration raises at `:1328-1330` and `:1335-1336` (unfired in this run) while blob `75eefef4e27e` at commit `22feba17a6` carries them at `:1300-1302`; `22feba17a6` is a **commit**, not a blob (`git cat-file -t`), the identifier-kind point the hub raised, p4 adopted and pB corrected in Addendum 5 @ `659a014a4a` (+8/−0, append-only).

**On this desk's own instrument:** A-2 reported **one** instance of that class because it machine-compared only the 30 bullet-form cites and read the prose pointer sentence by eye. pB's machine check over all prose cites found **three** of the same type. The unit of a cite check is the class, not the instance; A-7 above applies that to the corrected file.

### A-8 · Scope
This addendum closes the naming of the rows 2-5 targets and leaves every other row as written. It says nothing about the stop's cause (p4 item 86: 「その他」), the route, grasp, the cell's suitability, or physical validity — human ground truth is unapplied to #69 (p4 item 95), and acceptance of the run was p4's word, not this desk's.

## Appendix C — cite re-check output (verbatim; instrument `pz_pb_cites3.py` sha256 282f48ffb2fb6efe4285a6046fbaa87317ffdd77cb4e6d49376e2e6a721d9764)
```text
checked file  = pb_verdict_659a014a4a.md sha256 5a1e0f372710e45d lines 311
sources       = run.log blob c79fdfd1d410 (402 lines) / driver blob 84a372439c59 (the run) / driver blob 75eefef4e2 (@ commit 22feba17a6)
cite tokens `:NNN` with an adjacent quoted line = 46 | pointer-only tokens (undecidable by this instrument) = 78
quoted cites whose text sits on the named line = 43/46   not matched = 3
  not matched: file line 59 cite :369 | section '3. (iii) 停止・札・rc・phase — 三者一致（run.log ↔ RUN_METRICS `run` ↔ p0 §8.66 の' | quote 'STEP 2 ARM-TO-ARM: closest -1.1 mm (9 <-> 42)  <- TOUCHING O'
  not matched: file line 284 cite :369 | section '訂正 1（本体）— ARM-TO-ARM の行番号は `:367`（`:369` は CARRY 行）' | quote 'STEP 2 ARM-TO-ARM: closest -1.1 mm …'
  not matched: file line 308 cite :1300 | section 'Addendum 5（2026-09-21 01:25:55 JST・re m-p18-498 = p4 m-p4-313 受領 (b) の' | quote 'upright = [attitude_tilt_deg(...)]'
```

## Appendix D — structure and selection output (verbatim; `pz_69_struct.py` + the target/sweep readout, same session)
```text
[run  (f650fc32…)] sha256 f650fc322781a915  bodies 87  cable bodies cabNN 40
[09-05 (4158e4e6…)] sha256 4158e4e638e9b0fc  bodies 87  cable bodies cabNN 40
cable subtree XML identical across the two dumps : True
cable ancestor chains identical                  : True
distinct names appearing in any cable ancestor chain: <worldbody> + cab0..cab38 only -> True
intersection with the bodies whose lines differ  : empty
crown geom: size run/0905 = 0.11 0.28 / 0.11 0.22  | its ancestor chain = ('<worldbody>', 'column')
L_shoulder_link: run ('-0.485417 0 1.60477', '0 -0.573576 0 0.819152')  |  09-05 ('-0.374574 0 1.68457', '0 -0.382683 0 0.92388')
R_shoulder_link: run ('0.485417 0 1.60477', '0 0.573576 0 0.819152')  |  09-05 ('0.374574 0 1.68457', '0 0.382683 0 0.92388')

[run] cab bodies 40  explicit quat attrs 0  joints 79  joint ref values [None]
[run] cab0 pos = -0.3 0.28 0.954   child spacing set = [0.015]   y=0.28 z=0.954
[run] link-centre x from the XML chain: c27=0.112500 c32=0.187500   (x0=-0.300000, closed form x0=-SEG*N/2=-0.300000)
[0905] cab bodies 40  explicit quat attrs 0  joints 79  joint ref values [None]
[0905] cab0 pos = -0.3 0.28 0.954   child spacing set = [0.015]   y=0.28 z=0.954
[0905] link-centre x from the XML chain: c27=0.112500 c32=0.187500   (x0=-0.300000, closed form x0=-SEG*N/2=-0.300000)

closed form c_i = (x0+(i+0.5)*SEG, REST_Y, REST_TOP+CABLE_R); i = argmin|c_i.x - (GRASP_CENTRE_X -/+ GRIP_HALF_SPAN)|  [harness :60 :1005 :1007-1012]
GRASP_CENTRE_X=0.150 -> L cab27 centre x=0.1125 (x_cmd 0.106, |d|=6.5 mm) | R cab32 centre x=0.1875 (x_cmd 0.194, |d|=6.5 mm)   <- p0 as-run: L cab27 / R cab32
GRASP_CENTRE_X=0.160 -> L cab27 centre x=0.1125 (x_cmd 0.116, |d|=3.5 mm) | R cab33 centre x=0.2025 (x_cmd 0.204, |d|=1.5 mm)   <- p0 as-run: R cab33
GRASP_CENTRE_X=0.170 -> L cab28 centre x=0.1275 (x_cmd 0.126, |d|=1.5 mm) | R cab34 centre x=0.2175 (x_cmd 0.214, |d|=3.5 mm)   <- p0 as-run: L cab28 / R cab34
effective link-centre separation at the default = 75.000 mm (commanded 2*GRIP_HALF_SPAN = 88.0 mm) -- 15 mm quantisation

#69 :44 L=cab27 [0.1125 0.28 0.9486] vs target (0.1125, 0.28, 0.954): dx=0.000 mm dy=0.000 mm dz=5.4 mm below rest
#69 :44 R=cab32 [0.1875 0.28 0.9509] vs target (0.1875, 0.28, 0.954): dx=0.000 mm dy=0.000 mm dz=3.1 mm below rest
drop across the span (L z - R z) = 2.3 mm  <- the driver's own print on :44
#69 :101 re-measured after the approach: L=cab26 [0.0986 0.28 0.9488] R=cab32 [0.1886 0.28 0.951]
harness U0_SETTLED (:118) = GL (0.0986, 0.28, 0.9488) GR (0.1886, 0.28, 0.951) links ('cab26','cab32')  -> equal at the printed precision (1e-4 m)

selection sweep recomputed here (no run):
  GRASP_CENTRE_X=0.1500 -> L cab27 (centre x 0.1125, x_cmd 0.106, |d| 6.5 mm) | R cab32 (centre x 0.1875, x_cmd 0.194, |d| 6.5 mm)   [p0 as-run + #69 run.log :44]
  GRASP_CENTRE_X=0.1575 -> L cab27 (centre x 0.1125, x_cmd 0.1135, |d| 1.0 mm) | R cab33 (centre x 0.2025, x_cmd 0.2015, |d| 1.0 mm)   [p11 closed form]
  GRASP_CENTRE_X=0.1600 -> L cab27 (centre x 0.1125, x_cmd 0.116, |d| 3.5 mm) | R cab33 (centre x 0.2025, x_cmd 0.204, |d| 1.5 mm)   [p0 as-run]
  GRASP_CENTRE_X=0.1650 -> L cab28 (centre x 0.1275, x_cmd 0.121, |d| 6.5 mm) | R cab33 (centre x 0.2025, x_cmd 0.209, |d| 6.5 mm)   [p11 closed form]
  GRASP_CENTRE_X=0.1700 -> L cab28 (centre x 0.1275, x_cmd 0.126, |d| 1.5 mm) | R cab34 (centre x 0.2175, x_cmd 0.214, |d| 3.5 mm)   [p0 as-run]
  half pitch = 7.5 mm; link-centre separation at the default = 75.000 mm vs commanded 2*GRIP_HALF_SPAN = 88.0 mm
```
