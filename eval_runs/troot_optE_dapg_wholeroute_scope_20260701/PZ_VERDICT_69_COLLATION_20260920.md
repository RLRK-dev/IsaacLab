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
