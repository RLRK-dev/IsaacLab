# P2 Whole-Route (C1→C2) RL env/reward — DESIGN (proposal for Rs approval)

**Author:** RS-TECH-LEAD (%3, 全体設計). **Date:** 2026-07-02. **HEAD** `bcb7393ec8`, env7 mujoco-コ.
**Charter:** Rs「go」(P2) + 「ok」(arch A + §運用21 obs fix). Architecture A = Residual-PPO/DAPG on the committed square-on route. **env/reward = Rs-reserved → this is a PROPOSAL; NO build until Rs approves.**

> ⛔ **STATUS 2026-07-02: /pre-check = BLOCK (2 CRIT/4 HIGH/4 MED) + %9 OPS-SUP GT cross-PV = CONCUR-BLOCK (all 10 CONCUR; HIGH6→CRIT; env-ABSENT = co-root; W_ORI 0.5 regression vs AR 0.75).** The §7 "GATE: PASS" below is the SELF-assessment, SUPERSEDED — the 4 artifacts are un-measurable without the (absent) whole-route env. See `P2_PRECHECK_CROSSPV_OPSSUP.md` + `logs/pre-check-log.jsonl`. **Rs 2026-07-02「継続 推奨で良い」= reframe approved: Q3 demo-recorder FIRST (UNIT-independent), Q1 UNIT choice = Rs-pending; reward finalization deferred until Q1-Q3 resolved.**
> **DQ1 RESOLVED 2026-07-02 ~07:37: Rs =「B」(BC-imitation).** This residual-PPO reward design is therefore **PARKED** (not the chosen next unit; NOT killed — revisit iff A [residual + noisy-pose obs] is later selected). Successor work = B-scoping (converter + pure-BC trainer + rollout evaluator).
**Grounding:** agent inventory (AC=`newton_approach_cable_mujoco_env.py`, AR=`newton_aerial_regrasp_mujoco_env.py`, TC=`task_config.py`, committed route `test_newton_clip_routing.py`), P1_VERDICT.md, DAPG_WHOLEROUTE_C1C2_SCOPING_COORD2.md, `train_common.py`.

---

## §0. Design summary

- **Base controller** = the committed square-on route (deterministic `ee_target_L/R` per phase, `ik_move_both` interp-to-IK). Policy learns a **12D dual-arm EE-delta RESIDUAL** on top (`+` auto-close gripper channel, NOT a 13th action dim — matches AC/AR).
- **Phases (6):** APPROACH → GRASP → LIFT → ROUTE(drag) → REGRASP → SEAT (collapsed from the committed 14 sub-phases; `full_43step.json` C1→C2 = steps 1-18).
- **DAPG:** BC-loss anchors residual≈0 to the demo (committed route); α 0.7→0.5 anneal (`train_common.py:87-92`).
- **DR:** cable pose-random (`CABLE_XY_DR_AMPLITUDE=±20mm`, `TC:264`) — the residual absorbs it.

---

## §1. OBS schema (49D) — extends AC/AR 42D; §運用21 fix is the crux

| dims | content | source |
|---|---|---|
| `[0:42]` | AC/AR 42D base: R/L clamp pose+finger, target cable seg pose, **current-target-clip** pose (phase-dependent: C1 in GRASP/seat-C1, C2 in ROUTE/REGRASP/SEAT — repurposes AC's static-C1 `[23:30]`), per-arm pos/ori error | AC:843-856 |
| `[42:48]` | **phase one-hot (6)** — APPROACH/GRASP/LIFT/ROUTE/REGRASP/SEAT (NEW, needed for phase-conditioned residual+reward) | new |
| `[48]` | **★ held_cable_z** — z of the L-held cable seg (the §運用21 RETENTION-state fix) | new |

⭐ **§運用21 FIX (Rs-approved):** AR reward reads `cz_l_excl` (retention/height) but it is NOT in the 42D obs — sound ONLY because AR FREEZES L (`cz_l_excl≈LIFT_Z` const, `AR:48-52`). **The whole route MOVES L (drags the cable) → `held_cable_z` varies → any retention reward that reads it would be gradient-zero noise = DEADLOCK unless it is in obs.** `[48]` closes this. (This is the #1 design decision; without it, r_retention below is a Pattern-4 deadlock.)

---

## §2. REWARD components (phase-conditioned; weights = env-class attrs, AC/AR template)

| # | component | formula | weight | phase-gate | obs-backed? (§運用21) |
|---|---|---|---|---|---|
| 1 | `r_pos` | `W_POS·[(e^(−dR/.015)+e^(−dR/.10)+e^(−dR/1.0))/3 + (L)]`, target = current-phase base ee_target | W_POS=0.5 | ALL | ✅ err `[33:36]/[39:42]` |
| 2 | `r_ori` | `W_ORI·[(e^(−oR/.25)+e^(−oR/1.5))/2 + (L)]` | W_ORI=0.5 | ALL | ✅ err `[30:33]/[36:39]` — ⚠ G7 weak-ori (~100× under-apply): residual can't fix ori → **relies on base-route ori** |
| 3 | `r_retention` | `W_RET·clamp((held_cable_z−DROP_Z)/(NOM_Z−DROP_Z),0,1)` | W_RET=0.3 | GRASP→SEAT | ✅ `[48]` held_cable_z (the FIX) |
| 4 | `r_seat` | `W_SEAT·e^(−d_cable_C2groove/.003)` (cable seg `[16:23]` vs C2 groove `[23:30]`) | W_SEAT=0.5 | SEAT | ✅ both in obs |
| 5 | `r_phase` | one-time `R_PHASE_BONUS` at each phase-complete (the **BRIDGE** across gates) | 5.0 | transitions | ✅ phase `[42:48]` |
| 6 | `r_task` | `R_TASK_BONUS` if whole-route success | 200.0 (anti-hover) | success | — |
| 7 | `R_PENALTY` | **measured-in-build** (`_measure_p0_and_calibrate` AR:1380-1428 pattern) so Net@P0 = `TARGET_NET_P0=−0.07` — NOT AC's stale `−1.436` hardcode | measured | — | — |
| 8 | penalties | explosion (d>1m∨NaN → −10) ; drop_pen (cable_dropped → −10 + terminate) ; **reach-fail terminate** (IK-resid>thresh ∨ EE_XY_BOUND hit → terminate, handles %0 reach-fragility WITHOUT an obs dim) | — | — | — |

**Assembled:** `r = r_pos + r_ori + r_retention + r_seat + r_phase + r_task + R_PENALTY + penalties`.

**SUCCESS (whole-route):** `d_cable_C2groove < T_GROOVE(3mm)` ∧ seat-ori `cos > T_SEAT(0.85)` ∧ `¬cable_dropped` ∧ both arms reached seat pose, **sustained K_INSERT=10** (`TC:362-374`).
**done** = success ∨ timeout ∨ explosion ∨ cable_dropped ∨ reach_fail. **time_outs = timeout ∧ ¬(others)** — MAX_EPISODE_STEPS ONLY (prohibited.md value_loss-105× guard).
⚠ **HORIZON:** committed C1→C2 ≈ 14 macro sub-phases; at 48Hz control this likely **exceeds MAX_EPISODE_STEPS=200** → propose `ROUTE_TERMINAL_STEPS=400` (a `time_outs`-purity-sensitive change → Rs design-gate item).

---

## §3. Artifact 1 — REACHABILITY TABLE (gradient at P0 / dead-zone check)

P0 = APPROACH phase, both arms ~91.8mm pos, ori≈0 (`AC:56,260`).

| Component | Gate | Reachable from P0? | Gradient at P0 | Dead zone? |
|---|---|---|---|---|
| r_pos | none | yes | dR=91.8mm: coarse `e^(−.0918/1.0)=.912` dominates → grad `−.912/m` NONZERO | **no** |
| r_ori | none | yes (ori≈0 → r≈1.0, small grad near 0, maintained by base) | small but base-held | no |
| r_retention | GRASP→ | reached via r_pos+r_phase driving APPROACH→GRASP | held_cable_z in obs `[48]` → NONZERO once active | **no** (obs-backed) |
| r_seat | SEAT | reached via r_phase chain APPROACH→…→SEAT | cable-vs-C2 in obs → NONZERO once active | **no** |
| r_phase | transitions | yes (r_pos drives each phase-target) | one-time +5 at each complete | no |
| r_task | success | reached via the full r_phase chain + r_seat | +200 | no |

**No row has Dead zone = YES** — because (a) `held_cable_z` in obs kills the §運用21 retention dead zone, and (b) `r_phase` bridges the phase gates (Pattern-1 fix). **Artifact 1 = PASS.**

---

## §4. Artifact 2 — CAUSAL GATE DAG

```
action(EE-delta residual) → (base+residual) → EE moves → dR↓ → r_pos↑
   dR<12mm ∧ oR<10° --[GATE:APPROACH-done]--> r_phase+5 → enter GRASP
       │ driven by r_pos+r_ori (NONZERO from P0)                 │
       ▼                                                          ▼
   auto-close (pos<thresh) → cage → held_cable_z set → r_retention↑ (GRASP→)
                                        │  held_cable_z in OBS[48] → NOT dead (§運用21 fix)
   --[GATE:GRASP-done]--> r_phase+5 → LIFT → --[GATE]--> ROUTE(drag)
       r_retention keeps cable held through drag (row54; obs-backed)   │
   --[GATE:ROUTE-done]--> REGRASP (R re-grasp, span≤88mm guard AR:992) │
   --[GATE:REGRASP-done]--> SEAT → cable-vs-C2groove↓ → r_seat↑ → --[GATE:seated∧retained∧sustained]--> r_task+200
```

Every `--[GATE]-->` has a driving reward (r_pos / r_phase / r_seat). The **only** gate that WOULD be a deadlock (retention, GRASP→SEAT) is fed by `held_cable_z` ∈ obs → **not** a deadlock. **Artifact 2 = PASS** (no un-driven gate).

---

## §5. Artifact 3 — GROUND-TRUTH VALUES (computed from grounded params)

| State | phase | dR pos | ori | held_z | r_pos | r_ori | r_ret | r_seat | r_phase | r_task | R_PEN | **r_total** | behavior |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P0 (init) | APPROACH | 91.8mm | ~0 | — | +0.44 | +1.0 | 0 | 0 | 0 | 0 | −1.51 | **−0.07** | move to grasp (anti-hover calib) |
| Grasp-done | GRASP | 3mm | ~0 | nom | +0.89 | +1.0 | +0.30 | 0 | +5(1×) | 0 | −1.51 | **+0.68**(+5 transient) | cage set, hold |
| Mid-route | ROUTE | 5mm(track) | ~0 | nom | +0.89 | +1.0 | +0.30 | 0 | — | 0 | −1.51 | **+0.68** | drag, keep held |
| Seat-near | SEAT | 4mm | cos.9 | nom | +0.85 | +0.9 | +0.30 | +0.36 | — | 0 | −1.51 | **+0.90** | push into C2 |
| **Success** | SEAT | 2mm | cos.95 | nom | +0.9 | +0.95 | +0.30 | +0.49 | — | **+200** | −1.51 | **≈+201** | seated+retained |

- Calibration: `R_PENALTY` measured so Net@P0 = −0.07 (anti-hover; AR pattern, not AC hardcode). 
- `r_total` **monotonically rises** P0→success; success (+201) ≫ hover (−0.07) → **anti-hover holds** (Pattern-3 mask check: r_task dominates, no single component masks the gated ones because r_phase forces progression). **Artifact 3 = PASS.**

---

## §6. Artifact 4 — EPISODE TRACE (5 steps from P0)

```
Step 0: P0 APPROACH. obs: both arms 91.8mm, phase=APPROACH, held_z=n/a. Best action: residual≈0 (base drives down); r_pos grad pulls.
Step 1: base descends ~15mm; dR=77mm. r_pos↑ (.912→.88 coarse). residual small (DR-correction). No retention yet.
Step 2: dR=40mm. r_pos↑. still APPROACH.
Step 3: dR=11mm < 12mm ∧ ori<10° → APPROACH-done GATE → r_phase +5 → phase→GRASP. auto-close triggers → cage forms → held_cable_z SET.
Step 4: GRASP. r_retention now ACTIVE (held_z in obs → nonzero grad). base begins LIFT. residual learns to keep held_z high under DR.
...→ ROUTE: base drags to C2; r_retention rewards held_z through the slide (row54 mechanism, obs-backed); residual absorbs the ±20mm cable-DR.
No dead step: r_phase advances the gate, r_retention is live (not noise), r_pos tracks. **Artifact 4 = PASS.**
```

---

## §7. GATE DECISION

```
[REWARD DESIGN GATE]
Reachability : PASS (no dead zone — held_cable_z in obs kills the §運用21 retention dead zone; r_phase bridges gates)
Causal DAG   : PASS (every gate has a driving reward; retention gate obs-fed)
Ground-truth : PASS (monotone rise, +201 success ≫ −0.07 hover, anti-hover)
Episode trace: PASS (no dead step)
GATE: PASS → proceed to /pre-check + 5体 [VERIFY] (NOT to build — Rs approval first)
```
⟦SUPERSEDED 2026-07-02: /pre-check overturned this self-assessed PASS → BLOCK; %9 cross-PV CONCUR-BLOCK. See the ⛔ STATUS banner at the top.⟧

---

## §8. How the design carries the 4 P1 risks + OPEN Rs design questions

| P1 risk | how the design carries it | residual risk |
|---|---|---|
| ① retention row54 (sliding cradle) | `r_retention` (obs-backed) + `drop_pen`/terminate + DR trains robustness | non-load-bearing on soft/real = GPU/real gate (P4+), NOT solved by reward alone |
| ② §4 curvature | base route provides the (kinematic) curvature; residual only corrects locally; obs has cable seg pose | fidelity boundary → real-cable gate |
| ③ GPU whole-route validity | (out of P2 reward scope) | ⚠ NEW screen (cg-GPU whole-route) before P4 |
| ④ reach-fragility | `reach-fail terminate` (no obs dim) + EE_XY_BOUND ±50mm | inter-arm collision UNVERIFIED (AC drops collision spheres, `AC:47-52`) → **Rs Q** |

**OPEN Rs design questions (design-gate, your call):**
1. **Retention reward vs mechanism:** accept `r_retention` + DR to train robustness (this design), OR add a physical retention mechanism first (the deferred C2-pin/latch/finger, decision-c)? (The sliding-cradle is non-load-bearing; reward may not overcome soft-cable slip.)
2. **HORIZON:** `ROUTE_TERMINAL_STEPS=400` (time_outs-purity-sensitive) — OK?
3. **Inter-arm collision:** AC dropped the arm-arm collision spheres; the whole route moves both arms independently → re-enable collision spheres for the route env? (reach-fragility + safety).
4. **G7 weak-ori:** rely on base-route ori (residual position-only), or resolve G7 (active ori-control) first?

**NEXT:** /pre-check (failure-mode sub-agent) + 5体 [VERIFY] → present the full proposal (+ reward-detail figure) to Rs. **0-commit, no build until Rs approves.**
