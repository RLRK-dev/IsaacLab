# L3 CC-Debate [VERIFY] verdict — grip-substep-decouple plan = **FAIL (fix-first)**

**2026-07-18 10:01 JST · RS-TECH-LEAD (w2:p4) · §運用2 [VERIFY] gate, L3, 5-body panel (CC2-5 lensed + CC6 NHA).**
Subject: p5's grip-phase substep decouple (4→10, sim_dt=DT/10) plan (`GRIP_SUBSTEP_DECOUPLE_DESIGN_VTDESIGN_20260718.md`).
**VERDICT = FAIL** — the plan's load-bearing premise ("slip is pure substep-fidelity") is **refuted on-disk**. Do NOT proceed to [CHANGE]. Fix-first = re-target the actual (drive-dependent) root cause.

## Panel results
| Body | lens | verdict |
|---|---|---|
| CC2 | premise/provenance | **1 CRITICAL** + 1 HIGH + 3 MED — slip is DRIVE-dependent, not substep |
| CC3 | rule/SSOT | 0 CRIT/0 HIGH (4 LOW hygiene) — no rule violation; plan is arg-only, §0 invariants untouched |
| CC4 | numerical/physics | 1 HIGH + 3 MED — crux numerics airtight; but drop = single-arm 22mm gap, fast lateral escape (not creep) |
| CC5 | side-effects/regression | **1 HIGH** + 1 MED + 1 LOW — re-measure harness false-provenance; recording-sync/byte-repro SAFE |
| CC6 | NHA | CHANGE_JUSTIFIED **on the refuted premise** (necessity rests on "golden drops at 4-sub" — but FF@4 HOLDS) |

## CC1 REBUT_OR_ACCEPT (on-disk verified)
**ACCEPT — CC2 C-1 (CRITICAL): slip is drive-dependent, not substep-fidelity.**
- `ikchord_deadlock_render/run.log`: `drive=ik_chord … done_step=267 … final_reward=-10.0` (DROP).
- `ikchord_deadlock_render/run_ff.log`: `drive=feedforward … reached step budget 300 without env done … final_reward=-0.0099` (HOLDS full route).
- SAME recording, SAME `apply_recorded_grip`, SAME substep=4; only the arm drive differs. My own decision doc `PIN_DB_IKCHORD_GRIPSLIP_DECISION_RSTECHLEAD_20260718.md:12,17` already states: "**The −10 is DRIVE-DEPENDENT** (FF holds, ik_chord slips; only the arm drive differs) → ik_chord grip-slip, NOT the … deadlock." solref-overdamp `MUJOCO_PAD_SOLREF=(-65789,-2105)` (`task_config.py:187`) = the "softening" candidate (Rs video-GT).
- The design's regime-match compares the WRONG pair: recording(mujoco@10, scripted/dual-arm) vs measure(mujoco@4, ik_chord) — confounding substep with drive, and OMITTING the FF@4-holds control from my own 06:17 doc. IK targets are substep-invariant ⇒ ik_chord@10 arm path ≈ ik_chord@4 ⇒ finer contact integration unlikely to undo an arm-path-induced cage-open.

**ACCEPT — CC4 CH1 (HIGH): the drop window is a single-arm (left-only) hold; right arm never engages.**
- `per_step_metrics.json` steps 254-267: `contact_r=False` throughout, `r_near≈0.0214-0.0234 m` (constant ~22 mm), while `grip_r=1.0` (commanded closed). GOLDEN@10 held via DUAL load (`l_grip_N=21.5, r_grip_N=119.3`). A 22 mm end-effector standoff is a kinematic/IK gap — substep granularity cannot close it. The re-measure PASS criterion (design §7) checks only `l_near`/`held_z`/`G3`, never `r_near` → would miss the right-arm root.

**ACCEPT — CC5 CH1 (HIGH): the re-measure harness would falsely certify 4-substep while running 10.**
- `measure_grip_retention.py:82-84` asserts/prints `RL_SIM_SUBSTEPS==4` (module constant); design changes only the call-site (constant unchanged) ⇒ post-change the DoD anchor records "4 CONFIRMED" while physically running 10 = false provenance + zero discriminating power (gate-validated-under-the-bug). Records-must-match-fact violation on the #18 anchor.

**ACCEPT (mechanism/rationale) — CC2 C-3 / CC4 CH3 (MED): the drop is a fast lateral escape, not substep-creep.**
- l_near: slow 0.0087→0.0129 (255-261), then FAST 0.0129→0.044→0.065 (262-264); escape 10-480× the banked axial creep floor (60.4 µm/f). The design's "substep→creep→cage-escape" causal chain is contradicted by its own §13 (axial creep benign; the drop is on the un-measured lateral axis).

**NOTE — CC4 CH2 (MED): "finer dt → more stable/NaN-down" is a category error** (SolverMuJoCo is implicit/unconditionally stable in ke; no NaN occurred — `env_explosion_count=0`). Rationale must be reframed as resolution, not stability. (Moot given FAIL.)

**REBUT (not defects) — CC3 all (rule-clean): confirmed** — the plan is arg-only, no control-API touch (Newton env), no §0 invariant change, force params unchanged. CC3's items are hygiene, not violations. (This does not save the plan — the premise, not the rule-compliance, is what fails.)

## NO_ACTION_EVALUATION
- No-change on the substep decouple = correct: the slip persists, but substep would not fix it (wrong variable). The task is NOT solved by any listed alternative — it needs a DIFFERENT fix (drive/solref/right-arm).
- CC6 NHA "CHANGE_JUSTIFIED" is built on "golden drops at 4-substep" — **refuted** (FF@4 replays the golden arm path and HOLDS). With the premise corrected, the substep change is NOT justified.

## DECIDE = **FAIL** → fix-first
Do NOT implement the substep decouple. The demonstrated root cause is a **drive-dependent grip-slip under ik_chord** (candidates: `MUJOCO_PAD_SOLREF` overdamp "softening" / IK arm-path jerk / right-arm 22 mm disengagement) — a drive/contact/solref DESIGN question. This matches my own decision-doc option **(b) escalate to p5 / force-design**, which the fix-selection skipped in favor of substep.

## Recommendation (Rs decides — §運用10 inconsistency: Rs chose "1"=substep; L3 gate refutes its premise)
1. **Re-target root → p5 / force-design** (drive/solref/right-arm), NOT substep. [my rec]
2. Optional empirical closure: ONE controlled contrast probe (FF@4 / ik_chord@4 / ik_chord@10 / FF@10) to isolate substep before any commitment (predicted: ik_chord@10 still drops).
3. Ripple: §DDR #18 (p6 `34ebd31b2c`) currently records "fix=grip-substep-decouple" — needs re-qualification after Rs rules (hold; do not unilaterally reverse).

## Own-it (confirmation bias — the gate's purpose)
I held the disconfirming FF@4-holds control in my own 06:17 doc, yet the fix-selection + p5 design + my grounding proceeded on the substep-fidelity framing without reconciling it. The L3 [VERIFY] gate caught it before [CHANGE]. This is the anti-先走り / 確証バイアス禁止 discipline working as designed.
