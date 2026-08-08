# ik_chord grip-slip → force-design escalation (RS-TECH-LEAD p4 → VT-DESIGN p5)

**2026-07-18 10:11 JST.** Rs ruled **A** (2026-07-18 ~10:1x): the grip-substep-decouple plan FAILed the L3 [VERIFY] gate (premise refuted); escalate the ACTUAL root cause to p5 / force-design. Per discipline (設計=p5, 自分で導出しない), requesting p5's force-design of the fix. **substep decouple is REFUTED — do NOT design around it.**

## What the L3 debate + on-disk control established (full verdict: `GRIP_SUBSTEP_L3_DEBATE_VERDICT_RSTECHLEAD_20260718.md`)
The slip is **DRIVE-dependent, not substep-fidelity**:
- **FF@4 HOLDS, ik_chord@4 DROPS** — same recording, same `apply_recorded_grip`, same substep=4; only the arm drive differs. `ikchord_deadlock_render/run_ff.log` (reward −0.01, full 300 steps) vs `run.log` (drop step 267, −10). Already stated in `PIN_DB_IKCHORD_GRIPSLIP_DECISION_RSTECHLEAD_20260718.md:17`.
- **Right arm never engages**: `per_step_metrics.json` steps 254-267 = `contact_r=False`, `r_near≈0.022 m` constant, `grip_r=1.0` commanded → single-arm (left) hold. GOLDEN@10 held via DUAL load (`l_grip_N=21.5, r_grip_N=119.3`). A 22 mm EE standoff is kinematic/IK, not substep.
- **Drop = fast lateral cage-escape** (l_near 0.013→0.065 over steps 262-264, 10-480× the axial creep floor), not gradual creep. Left-finger loses contact at 261, cable falls step 267.
- Rs video-GT: under ik_chord the cable **softens when clamped and slips out** (no effective finger↔cable friction).

## The force-design question for p5 (root cause = drive/contact, not fidelity)
Why does the **ik_chord** drive soften/slip the cable out of the grip while the **feedforward** (recorded arm_q replay) drive holds it — at identical substep, contact params, and grip command? Candidate levers (p5 to adjudicate, not me):
1. **`MUJOCO_PAD_SOLREF=(-65789,-2105)` "TRUE-overdamp"** (`task_config.py:187`) — the "softening" candidate; does the ik_chord arm motion excite the overdamped pad↔cable contact into releasing?
2. **IK arm-path** — ik_chord solves its own arm trajectory (vs FF replaying the recorded one); is it jerkier / does it shear the cable out of the cage? (`IK_ITERATIONS_RL=30`.)
3. **Right-arm 22 mm disengagement** — is the right EE supposed to be gripping at steps 254-267? If so, restoring dual-arm load may be the fix (IK target / phase), and it is unreachable by any contact/friction lever.

## Constraints (fix-first)
- NOT substep decouple (refuted). NOT a threshold relax / symptom patch (`prohibited.md` 対処療法禁止).
- Do NOT touch RS71 §0 FOUNDATIONAL invariants (dual-arm / 88mm / DiffIK-only / コ-geometry / no-kinematic-trick). If a candidate fix WOULD touch one → STOP + Rs (premise change = Rs-専権).
- Validate at wc=1 fork-B. L3.

## Flow after p5's force-design
p5 /force-design (drive/contact/solref root) + /pre-check → L3 CC-Debate → rule-check → RS-TECH-LEAD implements → **re-measure with a FIXED harness** (⚠ `measure_grip_retention.py:82-84` asserts/records the module constant `RL_SIM_SUBSTEPS`, not the effective run config — CC5 CH1; fix the provenance before it certifies anything) → if grip holds under ik_chord, #18 resolved.

## Superseded
`GRIP_SUBSTEP_DECOUPLE_DESIGN_VTDESIGN_20260718.md` (p5) is **SUPERSEDED / REFUTED** by this L3 verdict (substep was the wrong variable). p5 to mark it. §DDR #18 (p6) "fix=grip-substep-decouple" → re-qualify to "fix=TBD via p5 force-design (drive/solref); substep REFUTED".

**Request: p5 force-design the ik_chord grip-slip fix** (which lever, why, physical validity, wc=1 validation). I hold implementation until the design + gates.
