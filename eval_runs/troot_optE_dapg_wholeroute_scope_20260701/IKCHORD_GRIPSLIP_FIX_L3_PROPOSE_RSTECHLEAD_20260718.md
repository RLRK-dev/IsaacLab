# IKCHORD GRIP-SLIP FIX — L3 CC-DEBATE PROPOSE (pre-impl [VERIFY])

**CC1:** RS-TECH-LEAD (w2:p4). **Design authority:** VT-DESIGN (p5). **Stamped:** 2026-07-18 12:47 JST.
**L:** L3 (env control-code change, "ik" keyword auto-escalation). **Gate:** [VERIFY] pre-impl — non-mutating; NOT fenced by DDR #18 execution HOLD (HOLD fences [CHANGE]/probe only).
**Governing SSOT (grounded on-disk this turn):**
- LEDGER DDR #18 `00-DESIGN-STATUS-LEDGER.md:98` — IN-RESOLUTION, execution HOLD, M2 drive-dependent CONFIRMED, old substep fix REFUTED/SUPERSEDED, FOUNDATIONAL.
- p5 design `IKCHORD_GRIPSLIP_FORCEDESIGN_VTDESIGN_20260718.md` §10.8 (lever) / §10.9 (/pre-check WARN + AMEND-1..5) / §6 (invariant guard).
- RS71 §0 FOUNDATIONAL INVARIANTS (dual-arm / 88mm / DiffIK-only / コ-gripper / no-kinematic-trick).

---

## GOAL
Remove the ik_chord grip-slip that peels the cable off the right gripper mid-route and drops it (`-10` at step 267), which blocks DDR #18 (grip-efficacy) → trainer grip verdict → launch. The fix must (i) restore recorded-branch grip, (ii) NOT touch §0 invariants, (iii) NOT use the REFUTED substep approach.

## ROOT CAUSE (diagnosed; on-disk verified this turn)
**M-b2 CONFIRMED** — the right-arm position-only IK (`IK_ITERATIONS_RL=30`, position + held-KO rot objective) converges to a **different discrete config branch** than the recorded/FF branch:
- right arm `|arm_q(ik) − arm_q(ff)|` wrap-corrected = **4.32 rad** (j14 shoulder 2.37 / j16 elbow 1.96 / j17 wrist 1.89 / j19 wrist 2.37); left arm 0.034 rad = matches recorded.
- Endpoints COINCIDE (`ik_resid_r` 0.24 mm both drives; clampR |Δ| 0.82 mm) ⇒ NOT within-step bow, NOT orientation. It is a **branch mis-selection**: the IK warm-start starts from the P0-settled config (`_settled_fk_jq`, `:933`, P0 branch, recording-independent), the solve lands on the wrong branch, and `:1283` propagates it via warm-start continuity through the whole route → fragile flip-config grip (holds ~86 steps, 90→176) → peels in route motion → drop 267.

**Drive-dependent evidence (same target pose, same 4-substep):**
| drive | fingertip_r→cable (window 248-267) | outcome |
|---|---|---|
| ik_chord | ~22 mm (0.0208–0.0232) | drop 267, reward −10 |
| feedforward | ~6.3 mm (0.0059–0.0076) | holds to 300, reward −0.01 |

Source: `ikchord_resid_diag/run_ik_chord_v2.log` / `run_ff_v2.log`; `IKCHORD_GRIPSLIP_DIAGNOSTIC_RESULT_RSTECHLEAD_20260718.md` §5 [P2]; on-disk `:1173`/`:1246`/`:942`/`:933`/`:1283`.

## PROPOSED CHANGE (p5 lever = recorded-branch IK seed + AMEND-1 dual-seed)
**[C1] Reset dual-seed (AMEND-1, HIGH — the confirmed defect):** seed the **ARM coords {0-5, 14-19}** of the FK warm-start cache (`_per_world_fk_jq`) to the **recorded `arm_q[route_t0]`** (route step-0 target frame), keeping the existing gripper patch (`:934-940`). Both downstream reads — `jq_starts` (`:1173`, IK warm-start) AND `old_fk_jq` (`:1246`, within-step interp start) — read this array, so seeding it once pins **both** to the recorded branch at step 0. Without this, seeding only `jq_starts` leaves the step-0 interp start on the settled (wrong) branch → a one-time step-0 settled→recorded **cross-branch sweep**, kinematically realized (arm is joint_q re-pose, no PD damping — AMEND-5) = a wild intermediate config near approach.
**[C2] Per-step reseed (AMEND-2 robustness + AMEND-3 frame):** reseed `jq_starts` (`:1173`) from recorded `arm_q[next_f[t]]` each step, so every N≥1 IK solve anchors to the recorded branch (a trained-policy residual that flips the branch self-corrects in 1 step).
**[C3] Impl guards a/b/c (p5 `:187`):** (a) assert/fallback if recording arm_q absent for the ik_chord reseed (currently FF-path only `:5033`); (b) held/frozen worlds apply the same `hold_mask` frame-clamp (`:5045`) to the seed lookup (wc=1 no-op, fork-B multi-world needs it); (c) recorded arm_q is 28-wide same layout, the finger-OPEN overwrite (`:1175-1178`) still runs on the new seed.

## WHY (mechanism)
Recorded arm_q is a **proven physically-valid** config (the successful FF run tracks it for the whole route). Seeding the IK from it makes the 30-iter solve converge to the recorded branch (target = base + small residual is in the recorded config's basin). Endpoint on the recorded branch ⇒ the `:1254` linear-joint chord is a small intra-branch interpolation ⇒ EE path ≈ recorded (small bow) ⇒ the wrong-branch fragility (the "2.4× cable push") is removed. This also resolves the §10.7 within-step magnitude puzzle — a branch fix covers the M-b1-looking symptom.

## SSOT / INVARIANT COMPLIANCE (§0)
- **DiffIK-only (#3):** the seed is a standard IK **input** (warm-start); control method unchanged. Arm drive is kinematic joint_q re-pose (`:1270-1272` phys_jqd=0; `route_executor.py:236`) = the PRE-EXISTING route drive (armqdirect, banked `c2045a9a1a`) — the lever neither introduces nor alters it. [AMEND-5; CC1-verified on-disk]
- **No-kinematic-trick (#5):** IK solves the real target (base+residual); the seed only selects the basin. No teleport / forced placement. [p5 §10.8; CC1 on-disk]
- **dual-arm / 88mm / コ (#1/#2/#4):** untouched (both arms seeded; span + gripper geometry unchanged).
- **obs semantics:** `_last_ik_resid` (`:1290`) is post-hoc achieved-vs-target, seed-independent → unchanged.
- p5 §6/§10.8 invariant guard = §0 不触 ⇒ no STOP. Design-gate + /pre-check + L3 still mandatory (control-code change).

## KNOWN_ALTERNATIVES
- **[REFUTED] grip-substep-decouple (4→10):** premise "slip = substep-fidelity" refuted by L3 [VERIFY] (FF@4 holds vs ik_chord@4 drops, same substep = drive-dependent). `GRIP_SUBSTEP_L3_DEBATE_VERDICT_RSTECHLEAD_20260718.md`; LEDGER #18.
- **[RULED OUT] null-space bias:** 6-DOF arm at a 6D pose (position + held-KO rot) has no continuous null-space; the branch is discrete, selected by the warm-start basin → the seed is the correct lever. [p5 §10.8:148]
- **[REFUTED] M-b1 within-step task-space interp (~10×):** endpoints coincide + config offset quasi-constant → not within-step shape. [DIAGNOSTIC §5]
- **[NOT primary] solref / contact stiffening:** the wrong-branch fingertip is ~22 mm from the cable → pad contact unreachable, so a contact-stiffness lever cannot engage. [DDR #18]

## MECHANICAL CHECKS
Design-stage — no code diff yet. p5 /pre-check verdict = **WARN** (0 crit / 2 high / 2 med / 1 low + 3 guards), AMEND-1..5 folded. Post-impl re-measure DoD (on a FIXED harness — `measure_grip_retention.py:82-84` false-provenance fixed to record effective config): nonzero-residual leg (AMEND-2) + cable-disp ≈ 1× arm assert (AMEND-4) + right-arm config-vs-recorded + fingertip_r / contact_r / dual-load + 176–195 window.

## OPEN ITEMS FOR THE PANEL (adversarial targets)
- **O1 (side-effect, CC1-flagged) → RESOLVED (p5 design call, 2026-07-18 12:59, on-disk verify):** AMEND-1's parenthetical "+`_settled_fk_jq`" seed has a real side-effect at **`:1094`** (`phys_jq[arm] = _settled_fk_jq[:28]`, the reset AUTHORITATIVE arm re-pose): seeding `_settled_fk_jq` would start the reset arm at *recorded* config while bodies/cable are restored to *settled* pose (`:1086`) — a joint_q↔body_q mismatch, because `_settled_fk_jq` is the FK of the settled bodies co-captured at `:931-933`. **Design resolution: seed `_per_world_fk_jq`-ONLY; do NOT touch `_settled_fk_jq`.** Then `:1094` stays settled/body-consistent, and only the two step-0 reads (`jq_starts` `:1173` / `old_fk_jq` `:1246`, both = `_per_world_fk_jq`) become recorded → step-0 is a single settled→recorded jump (same as the FF jump from `:1094`, no cross-branch intermediate). **Impl (makes [C1] precise):** in `_reset_worlds`, AFTER `:1057` `_per_world_fk_jq[w]=_settled_fk_jq.copy()`, overwrite arm coords {0-5,14-19} with recorded `arm_q[route_t0]` (keep the gripper patch `:934-940`). CC1's O1 flag validated the `:1094` concern; folded at DECIDE. (CC5 reviewed this as an OPEN item — its independent finding now corroborates.)
- **O2 (AMEND-2):** is per-step reseed sufficient for a trained policy whose residual (up to ~DELTA_BOUND ~20mm, not the 2mm transit cap) crosses the basin boundary and re-flips the right arm? Is the "self-correct in 1 step" claim sound, and can a residual-0 probe ever surface this (it cannot — hence the mandated nonzero-residual re-measure leg)?
- **O3 (AMEND-3 frame):** seed frame = recorded `arm_q[next_f[t]]` (target frame, matches `step_target.tgt_f`), NOT `step_f[t]+9`. route_executor indexing (`:4547`/`:4760`/`:5042`) is a sub-agent read — confirm the exact recorded-frame index at impl.
- **O4 (necessity / NHA):** is the null-hypothesis (leave ik_chord as-is; grip is a fidelity boundary per RS71 §4:62) defensible, or is the drop a genuine defect the recorded-branch seed must fix?
- **O5 (representativeness):** the diagnostic ran wc=1, ik_chord vs FF, on the GOLDEN recording (`w0e_81rerun_snapdown_0537/cell_x0_y0`). Does the branch mis-selection generalize across cells / initial conditions, or is 4.32 rad cell-specific?
