# DAPG WHOLE-ROUTE (C1→C2) — Port/Build Scoping (proposal for %3 / Rs review)

**Author:** COORD2 (%1, scoping/audit). **Date:** 2026-07-01 22:07 JST. **HEAD** `bcb7393ec8`, env7 mujoco-コ.
**Charter:** RS-TECH-LEAD(%3)→COORD2(%1), Rs 2026-07-01「A=経路全体 / B=はい delegate」. READ-ONLY scoping, PROPOSE-only (no build / no code change). Rs GOAL = collect DAPG guide-data → DAPG training; TARGET = the WHOLE C1→C2 route (approach→grasp→route/drag→re-grasp→seat) as ONE DAPG unit, NOT per-skill-only, NOT yet full-5-clip.
**Status:** design-adjacent (L2+); FLAGS design-gate items (env/reward/obs = Rs-reserved). Report → %3 for the §運用2 [VERIFY] before any build.

---

## §0. GROUNDING (anchor-set, §運用4 — read + cited myself)

| Anchor | Cite | Fact used |
|---|---|---|
| LEDGER row43 | `00-DESIGN-STATUS-LEDGER.md:43` | `C1→C2 re-grasp (guide-data)` = 🟢 **WORKING Rs-confirmed 2026-07-01**, **COMMITTED `bcb7393ec8`** + pushed. Square-on default (`C2_TILT_SIGN=0`); L retains (0-N cage), R re-grasps ACTUAL cable (X-follow bow); Y-span 88mm held; 4 Rs decisions (a square-on / b asymmetric OK for guide-data / c C2 positive-retention DEFERRED / d 100.3mm 3D chord accepted). = **the DAPG demo SEED.** |
| LEDGER row42 | `:42` | `RL-Routing-Design.md` = ⚠️ MIXED. AR 92.2% Gate G3 but spring-follow+kinematic hold **fidelity-QUARANTINED**; **5-skill product P0-KILL'd as-scoped (infeasible)**. |
| LEDGER row54 | `:54` | AR mujoco-コ: single-L コ-cage is **NOT load-bearing** (force-falsified 06-29; hold = dual-clamp+tension). Clip-anchored routing was the documented plan (`RL-Routing-Design.md:1410-1470`). **Clip-retention sub-thread IN-PROGRESS, NOT resolved: retain-vs-load tension is FUNDAMENTAL for the rigid mujoco-コ cable.** Rs-approved 2026-06-30 real-feed test. |
| LEDGER §FAILED 2-3 | `:69-87` | ALL FIVE env6-VBD skill envs (AC/AR/Clamp/IC/Unclamp) DISCARDED → mujoco-コ. Do NOT restore/port the deleted VBD envs (先祖返り). |
| RS71 §0 INV | `RS71-System-Spec-SSOT.md:23-27` | #1 DUAL-ARM (both arms every motion) / #2 88mm span, bases Y=∓0.35 / #3 DiffIK-only / #4 コ-shape LOCKED / #5 NO kinematic trick (only clip-pin `log.md:6534`). |
| RS71 §4 CABLE | `RS71-System-Spec-SSOT.md:53-54` | ⚠ **FIDELITY BOUNDARY (Rs B2):** cable = 1-DOF-per-joint VERTICAL bender → dynamic = vertical SAG + free-root pose ONLY; **horizontal routing curvature is KINEMATIC** (grasp-drag + authorized clip-pin), NOT a dynamically-curved cable. Banked sim2real limitation → the cause of the AR routing fidelity-QUARANTINE. |
| RS71 §6 PIPELINE | `RS71-System-Spec-SSOT.md:63` | Grasp → Lift 50mm → Route 131mm → Hook — AERIAL. Full-clamp = insert / half-clamp = guide (`:64`). |
| SOMA / task_config | `task_config.py:257-262` | Cable pos/pose-RANDOM = deploy req (Rs 2026-06-24, SOMA L38 SUPERSEDED); DR impl PENDING (opt-in/OFF; range+retrain-wiring = Rs to spec). |
| prior-art gate | `check_thread_vault_prior_art.sh` | BLOCKER context: `D1_GOAL_ALIGNMENT` **GS-3** (zero Option-E routing runs EVER; S0 smoke FAILED cable-table penetration) + **GS-5 KEYSTONE** (no physically-valid routing EVER demonstrated; the one 2026-03-14 SIM route used **Fix1 Cable Kinematic Transport — BANNED as foundation proof**). **DELTA (why not the same failed path):** this is SCOPING (read-only), not a rerun; and the design target is a forward DAPG path seeded by the NOW-committed physics-faithful square-on route (`bcb7393ec8`), explicitly AVOIDING the banned kinematic-transport — see §7 conservatism. |

---

## §1. INVENTORY (grep, not assumed)

| Asset | State | Evidence |
|---|---|---|
| **DAPG demo SEED** (scripted C1→C2 route) | ✅ EXISTS, COMMITTED, Rs-WORKING | `test_newton_clip_routing.py` square-on route (`:4126` R-unclamp / `:4176` lift+traverse / `:4322` L-regrasp / `:4345` R span-preserving / `:4466` regrasp-gate / `:4350` `C2_TILT_SIGN=0` Rs-LOCKED). Driven by `data/waypoints/full_43step.json` (43 steps; phases A5/B5/C+D32/E1). |
| **Demo FORMAT** (npz superset) | ✅ EXISTS (grasp+lift only) | `R_S71_KO_GRASP_DAPG_DEMO_SPEC_77.md:15-17`: keys `phase, ee_target_L/R[N,3], clamp[N], arm_q[N,28], cable_z, gripped_xyz, contact_n, pen_mm`. Legacy action = **12-dim dual-arm EE-delta** R[posΔ3+oriΔ3]+L[posΔ3+oriΔ3] + separate gripper channel (`:20-21`). |
| **Demo RECORDER** | ⚠ PARTIAL (grasp+lift, not route) | `r_s71_grasp_demo_record_77.py`: records REST→APPROACH→8×DESCEND→CLOSED→12×LIFT (23 waypoints), inline choreography — does **NOT** replay `full_43step.json` / the route. Reusable = the npz-superset logging pattern (`:78-123`). |
| **DAPG trainer INFRA** | ✅ EXISTS, env7-proven | `train_common.py` = "Shared DAPG (PPO + BC auxiliary loss) infrastructure" (`--demos`/`--alpha-init 0.7`/`--alpha-min 0.5`/`--alpha-anneal-iters`/`--bc-warmup`/`_build_ppo_config`/`_default_get_alpha`). `train_grip.py` = "Train Grip … with DAPG", env7 `NewtonGripEnv` + `--demos …grip_clamp_demos_v1.npz` + `_convert_demos` (42D/12D→per-arm). §5.3 design `RL-Routing-Design.md:2606` (PPO update + 1× BC loss). |
| `train_dapg.py` (named file) | ❌ ABSENT | `find train_dapg* / *dapg*.py` = 0. **But** the DAPG *algorithm* is NOT missing (see row above) — only a route-specific entry is. |
| **env7 mujoco RL envs** | ✅ AC / AR / Grip (per-skill) | `envs/newton_approach_cable_mujoco_env.py` (AC, 42D/12D, MuJoCo, MAX 200), `newton_aerial_regrasp_mujoco_env.py` (AR, 42D/12D R-active, MuJoCo, MAX 200), `newton_grip_env.py` (Grip, 28D/6D 2-agent or 45D/14D dual, MAX 200). |
| **ROUTING / しごき / Transport / whole-route ENV** | ❌ **ABSENT** | grep `route/routing/shigoki/transport/drag` in `envs/*.py` = no env class. Every env is single-skill (AC=approach only / AR=one re-grasp event / Grip=finger-close only); NONE spans approach→grasp→route→re-grasp→seat. |
| **env7 demo→DAPG pipeline (wired)** | ❌ ABSENT | No env loads `.npz`/BC/DAPG (only Grip has an npz **P0-cache**, not demos). All legacy collectors = env6-VBD, walled (`RL-Routing-Design.md:278-293`; SPEC_77:23-24). |
| **DR / init-distribution** | ⚠ knob EXISTS, wiring PENDING | `task_config.py:264` `CABLE_XY_DR_AMPLITUDE=±20mm` (opt-in/OFF); `RL-Routing-Design.md:2746` §7 DR (visual/target clip separation). Deploy range + retrain wiring = Rs to spec (`:257-262`). |

⚠ **Grip-VBD residue flag (needs %3/Rs confirm):** the agent found `newton_grip_env.py:366` builds the scene WITHOUT the mujoco backend override (unlike AC/AR's forced flip) and applies VBD springs (`FINGER_SPRING_KE`, `:646-705`). This matches commit `13f3d55c0a`'s own caveat ("the VBD code-paths still interleaved in the shared env7 env files — a separate refactor"). Grip's banked R-S6.6 30/30 ran on cg-GPU (RS71 §0#4), so the label "Grip = env7-mujoco ACTIVE" holds for the tuned recipe, but the **default env code-path still has VBD springs** — a DAPG-route consumer that reuses Grip must force the mujoco backend, not inherit Grip's default. (Read-only observation; not a proposal to refactor.)

---

## §2. ARCHITECTURE — the key decision (whole-route ONE policy vs CHAIN of skills)

| | **A. END-TO-END whole-route (ONE policy)** | **B. CHAIN of per-skill policies** |
|---|---|---|
| Shape | 1 policy: approach→grasp→route→re-grasp→seat; 12D EE-delta + auto-close | AC[RL]→Clamp[RL]→Transport[**scripted**]→…→AR[RL] + orchestration seam (`RL-Routing-Design.md:1037-1075`) |
| Matches Rs directive? | ✅「経路全体 as ONE DAPG unit」 | ❌ per-skill (explicitly NOT what Rs asked) |
| Demo seed fit | ✅ the seed IS a single whole-route script (`full_43step.json` / committed square-on route) | ✂ must be sliced into per-skill demos |
| Existing envs | ✗ whole-route env ABSENT (biggest cost) | ✅ AC/AR/Grip envs exist on env7 |
| Known failure mode | long-horizon credit assignment; multi-phase reward | **the chain product was P0-KILL'd as-scoped** (SR-multiplication; AR fidelity-QUARANTINE, LEDGER row42); transport = the **scripted drag that keeps drag-failing** = the very problem to solve |
| Fidelity risk | route/drag middle is §4 KINEMATIC either way | same |

**RECOMMENDATION (for %3/Rs) = A, realized as Residual-PPO/DAPG on top of the committed scripted route.** Rationale:
- Rs chose 経路全体; the chain's SR-multiplication is already P0-KILL'd (row42) → B is the known-bad path.
- The cleanest realization of "whole route as ONE unit seeded by the committed script" = the **base controller = the committed square-on route** (`test_newton_clip_routing.py` / `full_43step.json`), and the policy learns a **12D EE-delta RESIDUAL** (+ auto-close) on top. This is exactly the DA-MPPI design's "DAPG+DR+**Residual-PPO**" tail.
- Why residual (not from-scratch end-to-end): it sidesteps long-horizon-from-scratch credit assignment; BC-loss anchors the residual ≈0 at the nominal IC; the residual is precisely what must absorb the DR/init-distribution (randomized cable pose) → it turns the DETERMINISTIC committed route into a robust policy without discarding the Rs-confirmed motion. Faithful-to-intent, no 先祖返り (the committed route is the backbone, not re-derived).
- ⚠ HONEST caveat: a residual policy cannot make a §4-kinematic route segment physical, and if retention is fundamentally unsolved (row54) there is no physical retention for the residual to learn — so **A is gated behind the §7 feasibility probe**, same as B would be.

---

## §3. PORT-SURFACE ANSWERS (a–d + obs/action/DR = charter items 1-7)

**a. TARGET RL env (item 2):** GAP — no whole-route env exists (§1). Options: (i) **NEW `newton_route_mujoco_env.py`** combining AC's P0/reset + AR's re-grasp/hold + route phases + a phase-conditioned reward [recommended — clean single-skill boundary]; or (ii) extend AR (closest: it already does the hardest sub-motion, R re-grasp of a held cable, `newton_aerial_regrasp_mujoco_env.py`) into a multi-phase route env. Either is an **env change = Rs-reserved design-gate** (`/reward-design` + `/pre-check`). NOT AC/Grip (approach/finger-close only).

**b. obs schema (item 3):** largely PORTABLE from the AC/AR **42D** layout (`newton_approach_cable_mujoco_env.py:23-36`): R+L clamp pose+finger [0:16], target cable seg pose [16:23], clip C1 pose [23:30], per-arm pos/ori error [30:42]. Whole-route ADDS: (1) a **phase indicator** (A/B/C/D — the route is multi-phase; needed for the phase-conditioned residual/reward); (2) the **target CLIP index / next-clip pose** (C1 vs C2, so the policy knows where it is on the route); (3) possibly the L-hold cable-z (AR reads `cz_l_excl` OUTSIDE the 42D obs, `:48-52` — a §運用21 obs-reward-integrity risk if the route reward depends on retention state that isn't observed). **§運用21 flag:** any route reward term that depends on retention / seat-z / clip-anchor state MUST have a matching obs dim, or it is gradient-zero noise → DEADLOCK. This is a design-gate item.

**c. action schema + control freq (item 4):** action = the existing **12D dual-arm EE-delta** (`POS_ACTION_SCALE 15mm/step`, `ROT_ACTION_SCALE ~2.9°/step`) + **auto-close** gripper (AC/AR fold the gripper OUT of the action vector — fingers auto-close at pose thresholds, matching D2 `RL-Routing-Design.md:1073-1075`). The demo's `clamp[N]` channel maps to the auto-close trigger, NOT a 13th action dim. **Control:** DT=1/480, PHYSICS_STEPS_PER_RL=10, MAX_EPISODE_STEPS=200 (`newton_skill_env_base.py:93` + env `:237`). ⚠ **Horizon problem:** the C1→C2 route is ~16 macro-steps × N control-substeps; if it exceeds 200 RL steps, the episode length must grow (a `time_outs`-purity-sensitive change per prohibited.md — do NOT put route-early-termination into `time_outs`). **43-step→control-dt resample (item 4):** `full_43step.json` gives 16 absolute-EE macro-waypoints (C1→C2 slice); these must be interpolated to per-control-step 12D deltas for the demo actions — the SPEC_77 recorder already emits per-control-waypoint `ee_target_L/R`, so the resample = run the committed route through the env at control dt and log, NOT hand-resample the JSON.

**d. demo RECORDER (item 5):** REUSE the SPEC_77 npz-superset logging pattern (`r_s71_grasp_demo_record_77.py:78-123`); NEW = hook it into `test_newton_clip_routing.py`'s **committed square-on route loop** (not the grasp-only choreography) so it logs (obs, action, phase) per control step across steps 1-16. Best faithful path = wrap the committed route (the Rs-WORKING motion) rather than re-scripting. ~200-300 LOC.

**demo diversity / DR (item 6):** the committed route is DETERMINISTIC → a DAPG demo SET needs demos across the INIT distribution. Knob exists (`CABLE_XY_DR_AMPLITUDE=±20mm`, `task_config.py:264`) but is opt-in/OFF and the **deploy range + retrain wiring = Rs to spec** (`:257-262`, SUPERSEDED-2026-06-24). SPEC_77:34 caveat: a grasp_y sweep is NOT a valid diversity proxy (EE targets must FOLLOW the randomized cable, and off-center hits the L/R reach wall `RS71-SSOT:37`). → DR = record the committed route under cable-XY-DR (+ the pose/shape axes Rs must scope) = the residual's training distribution. **DR range = Rs-reserved design.**

**GAPS/BLOCKERS/conservatism (item 7) — see §5.**

---

## §4. PHASED PLAN + COST (propose-only; NO build/launch here)

| Phase | Work | Files / LOC (est.) | Cost | Gate |
|---|---|---|---|---|
| **P0 (this doc)** | scoping | — | done | %3 [VERIFY] L2+ 5体 before P1 |
| **P1 — feasibility probe (CHEAP, HARD GATE)** | scripted probe: does a whole C1→C2 route + re-grasp + seat hold up DYNAMICALLY on env7 mujoco-コ given §4-kinematic-route + retain-vs-load (row54)? Reuse the committed route + `contact_diag_lib`/`mj_geomDistance` cross-PV. No new env, no RL, no commit. | ~150 LOC probe | CPU, ~0 GPU | **If the physical route/retention has no window → STOP; DAPG has no valid demo to imitate. Rs decision.** |
| **P2 — whole-route RL env** | NEW `newton_route_mujoco_env.py` (or AR-extend): multi-phase reset + phase-conditioned reward + success/terminated + obs (42D + phase + clip-idx) | ~600-900 LOC new env + `task_config` additions | CPU-smoke | **Rs design-gate: `/reward-design` + `/pre-check` + §運用21 obs-reward integrity + 5体 [VERIFY] (env = L3).** |
| **P3 — demo recorder + demo SET** | extend SPEC_77 recorder → wrap committed route → whole_route demos.npz across the DR init-distribution | ~200-300 LOC | CPU | proxy-representativeness gate (§運用14); DR range = Rs |
| **P4 — DAPG/Residual-PPO TRAIN** | new `train_route.py` (follow `train_grip.py` + `train_common.py`) + DAPG (PPO+BC α-anneal) + DR + Residual-PPO on the committed-route base | ~150-250 LOC entry (infra reused) | **GPU 10h+ = production training** | ⛔ **§運用2 HIGH-COST-GATE — default NO_GO; `/production-launch-gate`; Rs explicit approval. DO NOT launch.** |

**Total new code ≈ 1000-1500 LOC across ~3-4 new files + `task_config` additions.** The trainer AXIS is low-risk (DAPG infra reused from `train_common.py`/`train_grip.py`); the RISK + cost concentrate in P2 (new multi-phase env = Rs design-gate) and P4 (GPU).

---

## §5. GAPS / DESIGN-GATE FLAGS / 先祖返り GUARD / CONSERVATISM

**Top GAP (viability, item 7) — the §4 + retain-vs-load wall:** the route/drag middle of the whole route is §4-**KINEMATIC** (horizontal curvature not dynamic), and LEDGER row54 banks **retain-vs-load as FUNDAMENTAL for the rigid mujoco-コ cable** (single-L cage non-load-bearing; retain-vs-load has NO window in the explored space). A whole-route DAPG policy can learn the DYNAMIC sub-motions (approach/grasp/re-grasp/seat), but (i) it cannot make the kinematic route segment physical, and (ii) if retention is unsolved, there is no physical retention for the residual to imitate. **This is why P1 (feasibility probe) is a HARD GATE before the P2 env build — do not build the env / collect demos / train until a physically-valid whole-route window is shown to exist (or Rs accepts the kinematic-route fidelity boundary as the training substrate).**

**Design-gate items (Rs-reserved — I FLAG, do not design):**
- P2 whole-route **ENV** + **multi-phase REWARD** + **success/terminated** = `/reward-design` + `/pre-check` + 5体 [VERIFY] (env/reward = L3).
- **obs schema** additions (phase / clip-idx / retention-state) + §運用21 obs-reward integrity (reward must not depend on unobserved retention state).
- **DR range** (cable pos/pose/shape) = Rs to spec (`task_config.py:257-262`).
- Episode-length / `time_outs` purity if the horizon grows (prohibited.md — route early-termination ∉ `time_outs`).
- INVARIANT check: the 43-step re-grasp uses body21(L)/body29(R) = 120mm ARC, but the committed square-on route holds **Y-span 88mm** (the INV#2 metric; 3D chord 100.3mm accepted, row43) → INV#2 satisfied for the square-on route; any env that re-grasps must assert the 88mm **Y-span** guard (`newton_aerial_regrasp_mujoco_env.py:306` `REGRASP_SPAN_MAX`), not the arc.

**先祖返り / faithful-to-intent guard (CONFIRMED clean):** the plan ports FORWARD to env7 mujoco-コ, faithful to the **DA-MPPI/DAPG design INTENT + the committed square-on route**, NOT to the deleted env6-VBD impl. It does NOT restore/import any of the 5 deleted VBD skill envs (LEDGER §FAILED 2-3). The base controller = the committed `bcb7393ec8` route (physics-faithful, Rs-confirmed), explicitly NOT the BANNED Fix1 Cable Kinematic Transport (GS-5). Legacy env6-VBD demos are walled (`RL-Routing-Design.md:278-293`) — NOT reused.

**Conservatism direction (GROVE §2.2):** P1 as a CPU scripted probe is CONSERVATIVE for feasibility (holds on CPU → holds stiffer on GPU) but NON-conservative for grip-magnitude / GPU-softness (×3, SPEC_77:38) and for the §4-kinematic route (sim EASIER than a real dynamically-curved cable). A P1 FAIL (no physical window) = **conservative-definite → bank**. A P1 PASS = **non-conservative → real-fidelity/GPU gate before banking "route feasible."** GS-3 (S0 smoke cable-table penetration FAIL) stands as the conservative catch on GPU softness.

---

## §6. NEST + recommendation

- **NEST node (PROPOSED, pending %3/Rs approval per §3.1):** `T-ROOT-optE-route-dapg-C1C2` (child of the routing/DAPG tree; parent = the AR mujoco-コ / routing-port thread, LEDGER row54). goal = "DAPG whole-route C1→C2 policy on env7 mujoco-コ, seeded by the committed square-on route"; status = SCOPED (this doc); blocker = P1 feasibility + Rs design-gates. Node creation = Rs/§3.1 gate (I note the id, do not create it).
- **Recommendation to %3/Rs:** (1) adopt architecture **A (end-to-end whole-route as Residual-PPO/DAPG on the committed route)**; (2) run **P1 feasibility probe FIRST as a hard gate** (cheap, CC-domain, no RL/commit) before authorizing the P2 env build; (3) P2/P3/P4 each behind their gates (P2 env = 5体 [VERIFY] + `/reward-design`; P4 = HIGH-COST-GATE + Rs). **DO NOT** build/collect/train until P1 clears and Rs authorizes the env (design-gate).

**0-commit, HEAD `bcb7393ec8`, INVARIANTS untouched. READ-ONLY scoping — no source/spec/07-Design edits.**
