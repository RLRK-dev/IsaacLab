# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO D0 — factual read-only inventory (for D0-exit design verify)

- node `T-WMSO` (owner `T-ROOT-RS-TECH-LEAD2` / `w2:pQ`); verify `w2:pN`; custody `w2:p6`
- prepared_at: 2026-07-18 14:18 JST · repo HEAD `b4d32b5e54`
- gate basis: pN prereg-execution PASS (13:44) authorized **registered 6-item read-only content extraction only**. This is
  the **factual inventory** (design draft is a separate, later deliverable). No code/param/spec change; no run.
- provenance:
  - closure = v3 frozen manifest `…_MANIFEST_20260718_v3.tsv` (file sha `6abb176e…`, aggregate `5d8d2216…`, 46 rows).
  - **post-bracket `changed_during_inventory=[]`** (checked 45 as-read sources, 0 changed over the inventory window; tree
    moved via peer commits but no closure source content changed).
  - extension = `…_INVENTORY_EXT_MANIFEST_20260718.tsv` (file sha `821323c8…`, aggregate `678cd87d…`, 7 rows) — sources
    **discovered during item-2/3 extraction, outside the v3 closure** (read-then-freeze; disclosed).
- method: 3 read-only inventory agents (policy-lineage / obs-vision / env-termination-timing) + direct reads of
  `routing_orchestrator.py`, `safety_envelope.py`, `fallback_guard.py`, `skill_transforms.py`, `snapshot.py` + targeted greps.
- taxonomy: `ABSENT_IN_DECLARED_CLOSURE` (registered query returned nothing) / `UNVERIFIED` (exists, property not read-confirmed).

---

## 0. Architecture orientation — TWO parallel control stacks (do not share a termination path)

- **Stack A — per-skill orchestrator**: `orchestrator/routing_orchestrator.py` chains a 43-STEP table
  (`skills/step_table.py`) of per-skill RL envs + scripted skills → `SkillResult`, with snapshot/rollback recovery.
- **Stack B — monolithic whole-route env**: `envs/newton_route_env.py` (`NewtonRouteEnv(VecEnv)`, :392) runs ONE policy
  over the C1→C2 route with latched G1–G6 phases; per-step phase clock + HOLD/MARCH pause from `envs/route_executor.py`
  (5078-line scripted engine). Emits `dones`/`time_outs`/`invalid_mask`, **not** `SkillResult`.
- **Closure correction**: the v3 closure named `route_executor.py` + `newton_skill_env_base.py` as the env surface, but the
  actual policy MDP is `newton_route_env.py` (obs SSOT `envs/route_env_config.py` `OBS_DIM=62`, :45), which was outside the
  v3 closure → frozen in v3_ext. `newton_skill_env_base.py` is a utility module (scene/IK/quat/`physics_step`), no
  termination logic.

---

## 1. Learned skills + policy lineage (item 1)

**Three unreconciled skill vocabularies coexist** (the main D0 integration risk):
| taxonomy | where | family |
|---|---|---|
| T1 `SkillType` enum (7): APPROACH_CABLE, CLAMP, CLAMP_R, CLAMP_L, INSERT_INTO_CLIP, UNCLAMP, AERIAL_REGRASP | `models/skill_adapter.py:45-58` | **DAPG** (PPO + BC-aux) on frozen base + LoRA adapter |
| T2 scripted (transport/reclamp/half_unclamp/clip_confirm) | `skills/scripted_skills.py` | **SCRIPTED** (IK waypoint + finger interp) |
| T3 `bimanual_*` (6): reach/grasp/lift/transport/hang/release | `models/skill_adapter_with_prediction.py:150-157`; `training/dual_arm_skill_rewards.py:180-187` | **World-Model + PPO** (352D latent) |

**Policy families (evidence):**
- **T2 = scripted** (no NN): `ik_move_both`, `interpolate_fingers`, `check_groove_insertion` (`scripted_skills.py:124-136,244-256,342-351`).
- **T1 RL = DAPG** = PPO (RSL-RL `OnPolicyRunner`, `class_name:"PPO"`) + separate BC-MSE aux with annealed `alpha`
  (`scripts/train_common.py:7,126,195,237,343-345,488-503`); LoRA adapter freezes base + adds adapter
  (`train_common.py:249-255`). Grip (Clamp/Unclamp) = only present per-skill wrapper (`train_grip.py:268-291`).
  **AC/AR/IC per-skill `train_*.py` wrappers are ABSENT** from the working tree (trained artifact dirs exist on disk).
- **Base model = BC-only** (`train_base_model.py:96,140-147`, actor `45→128→128→12`) — the frozen base for LoRA, not a skill.
- **Route policy (B1, Stack B) = BC-only, deterministic actor-mean** (`bc_pretrain.py:107-108`, `bc_train_route.py:74-78`
  builds `obs_dim→6, (128,128)`; runner uses `policy.actor(obs)` mean, never `.act()` sample,
  `policy_route_runner.py:216-226`).
- **T3 `bimanual_*` = WM + PPO** (no BC): frozen 352D `WorldModelEncoder` + trainable Gaussian `PolicyNetwork` + `ValueNetwork`
  (`base_policy.py:66-104,281-297,369-376`); trainer `train_dual_arm_msa.py` referenced but ABSENT.

**Immutable policy/version hash recorded?** YES in `bc_train_route.py:117-135` (`ckpt_sha256`, `dataset_sha256` sidecar) and
`policy_route_runner.py` (`policy_sha256`, fail-closed `ROUTE_SHA_ACCEPT`/`TASKCFG_SHA`/`BASE_SHA` pins, :35-46,149-167,456,622).
NO in `eval_skill.py:862` (path only) / `train_common.py` / `train_base_model.py` (paths+hyperparams only).

---

## 2. Observation / action schema + vision-grounded belief (item 2)

**Live route policy MDP (Stack B, `newton_route_env.py`):**
- **Observation = 62D** (`_compute_obs_batch` :1475-1587; SSOT `route_env_config.py:44-70`). Base `[0:42]` mirrors AC proprio
  (EE pos/quat/finger ×2, target seg, clip nominal, ori/pos errors); route block `[42:62]` = phase one-hot(6), held-z,
  seat dist, within-phase progress, next-clip xy(const), contact proxy `[53:55]`, IK residual `[55:57]`, crossing-x dev,
  axis-resolved seat, C1-retention. All from `self._state_0.body_q/joint_q` (:1478,1481).
- **Action = 6D alpha residual** (`num_actions=6`, :427): `[0:3]` R EE XYZ, `[3:6]` L EE XYZ, position-only, **non-accumulating**,
  scaled `POS_RESIDUAL_SCALE=0.015 m` (:401,1168-1169), added to the route's **scripted absolute base target**; phase-conditional
  projection `_project_residual` (:1137-1156). **Grip is NOT an action dim** (scripted servo, :1174-1178). Consumed by
  `_apply_actions_batch`→`_solve_ik_batch` (`IKSolver`+`IKObjectivePosition`, rotation HELD, :955,1003,1235).

**Vision-vs-privileged (charter gate②):** **all 62 obs dims are PRIVILEGED SIM GROUND-TRUTH or config constants; ZERO
vision-derived.** Contact `[53:55]` is a geometric proximity proxy, not a sensor (:1564-1568). Confirmed by grep over the env
(no camera/encoder/pipeline call in `_compute_obs_batch`).

**Vision pipeline exists but is UNWIRED to the route policy:**
- `VisionPipelineStage1to3` (cable midpoint, `vision_pipeline.py:45-157`), `MultiCamCableStatePipeline` (40-seg cable state,
  :456 — estimator track), `FrozenResNetEncoder` (ResNet-18, `visual_encoder.py:21` — feeds separate camera-based `BasePolicy`).
- `VisionObsAssembler` (50D late-fusion, `vision_obs_assembler.py:76`) = **skeleton stub, `assemble_50d`/`_recompute_error`
  raise `NotImplementedError`** (:149-153,189-193).
- `ObsBuilder24D` (`obs_builder.py:33`) vision only if `num_envs==1` + pipeline passed; and its config import is **broken**
  (`OBS_DIM/OBS_MODES/OBS_NORMALIZATION` undefined in `task_config.py`, :30) → legacy/dead.

---

## 3. Termination / failure / timeout + safe-interruption (item 3)

**`SkillResult` (Stack A):** SUCCESS/TIMEOUT/FAIL/CABLE_DROP/EXPLOSION (`skills/result.py:18-25`). `derive_skill_result`
(`routing_orchestrator.py:419-469`): explosion→EXPLOSION, success→SUCCESS, time_outs→TIMEOUT, else→FAIL. **CABLE_DROP is not
derivable** (subsumed by FAIL, :438-441).

**Per-skill RL env done (Stack A):** AC `done=success|timeout|explosion` (`newton_approach_cable_mujoco_env.py:981`); AR adds
`cable_dropped` (`newton_aerial_regrasp_mujoco_env.py:1315`, but orchestrator ignores→FAIL); Clamp `done=success|timeout|explosion`
(`newton_grip_env.py:1252`, bilateral-AND success :1125-1131); Unclamp adds cable_dropped (:1437). **Insert RL env file is
ABSENT** (`find newton_insert*env*.py` → none; referenced only in comments) — `ABSENT_IN_DECLARED_CLOSURE`.

**Whole-route done (Stack B, `newton_route_env.py:1593-1760`):** `done=success|timeout|explosion|dropped` (:1720).
success=G6 (G5 latched ∧ c2_honest ∧ c1_retained ∧ ¬dropped ∧ span_ok, sustained `K_ROUTE_SEAT=10`, :1704-1711); explosion
(near>`EXPLOSION_DIST_THRESH=1.0`|NaN, :1635-1640); dropped (grasped ∧ held-z/contact-loss/lateral-escape, :1653-1672);
span-violation/reach-fail are informative-only (never terminate, :44-45,1674-1677). reward: explosion/drop→`TERM_PENALTY=-10`,
G6→`+200` (:1714-1717).

**Timeouts-contamination invariant (prohibited.md):** honored in `newton_route_env.py:1725`, AC:1003, AR:1334 (guarded
`int(timeout and not success and not explosion[...])`). ⚠ **latent divergence in grip env**: Clamp `newton_grip_env.py:1258`
and Unclamp `:1441` set `timeouts[w]=int(timeout)` **without** the success/explosion/drop guard → on a horizon-coincident
terminal, `time_outs=1` for a non-timeout terminal (see §10). `ROUTE_TERMINAL_STEPS=900` "time_outs fires ONLY on reaching
this" (`route_env_config.py:99`).

**Safe-interruption checkpoint = ABSENT_IN_DECLARED_CLOSURE.** Query
`grep -rniE "interrupt|preempt|safe.interrupt|safe.stop|switch.mid|mid.skill" envs/ orchestrator/ skills/ configs/` → 0 core
hits (scripts only). Nearest analogs (NOT safe-interruption): HOLD/MARCH clock-freeze (`route_executor.py:4806-4878`, a pause),
EXPLOSION→abort (`routing_orchestrator.py:1124-1126`).

---

## 4. Skill Handoff State + transition / recovery / fallback (item 4)

- **Stack A sequencer**: 43-STEP `step_table.py` (`build_step_table`); `execute_skill` dispatch →
  `_run_rl_episode`/`_run_scripted`/`_run_wait` (`routing_orchestrator.py:909-1242`); inter-skill state via `self.state_0`
  reassignment; arm-role handoff hazards handled by `mask_l_arm_action_if_needed`/`apply_finger_close_if_needed` (:261-411).
- **Recovery engine**: `execute_step` retry/rollback/abort (`MAX_RETRY=3`, `MAX_ROLLBACK_DEPTH=3`, :1063-1214); OOD gate
  `bc_p0_region_check` = **default-accept stub** (:1152-1162).
- **Handoff-state object**: `StateSnapshot` (physics state: body_q/qd, fk_jq, clip_status, fingers, ik_targets,
  `snapshot.py:19-31`); `SnapshotManager` save/restore (VBD `body_q_prev` re-align, :122-128). This is a **physics rollback
  snapshot, not a declared skill-handoff-state contract** (charter §3).
- **Stack B**: `RouteInterfaceV1` (`route_env_config.py:194-260`) — env owns obs/action/reward/term, route-executor owns phase
  clock; `reset_to_phase(k)` phase-bank re-fork (k=0 stub today, `newton_route_env.py:2028,2066-2069`); clip-pin latch
  `PIN_TRIGGER_DWELL_K=3` (`route_env_config.py:181`).
- **No dedicated recovery/fallback SKILL** — recovery = snapshot-rollback (A) or phase-bank re-fork (B); no `RECOVERY`/`FALLBACK`
  `SkillName` (`step_table.py:35-51`).

---

## 5. Current `routing_orchestrator.py` behavior + existing safety path (item 5)

- **Behavior** = the heuristic skill-chaining + retry/rollback recovery of §4 — this is the **baseline that charter gate⑨
  compares WMSO against**. Single-world only (`num_envs==1`, :799-809; multi-world deferred → intersects DDR#19).
- **Safety path — the SOMA safety envelope is UNWIRED to the live route path.** `SafetyEnvelope` (4 layers, L1-3
  measurement-only, L3 CBF placeholder, only L4 enforces; `safety_envelope.py:8-11,38,116-126`); L4 = `FallbackGuard` obs-anomaly
  → residual=0 (`fallback_guard.py:31-68`, 24D obs / 8D action — the legacy SOMA schema). **grep for
  `FallbackGuard|SafetyEnvelope|safety_guard` in `newton_route_env.py`/`route_executor.py`/`policy_route_runner.py` → 0 refs.**
  The live route path's only "safety" is a static `EE_Z_SAFETY_UPPER` Z-clip on the IK target (`newton_route_env.py:1189-1193`).
  → No independent low-level safety monitor on the live path (charter §2.4 / gate⑧).

---

## 6. Per-event deadline candidates + measurable acceptance (item 6)

- **Timing (all sim-step counts, NOT wall-clock):** `DT=1/480 s`; `RL_SIM_SUBSTEPS=4`; `PHYSICS_STEPS_PER_RL=10`
  (`newton_route_env.py:404`, cross-asserted :620) ⇒ **1 RL step = 10 physics frames ≈ 20.83 ms (~48 Hz control)**. IK budgets
  `IK_ITERATIONS_INIT=100`, `IK_ITERATIONS_RL=30`, `VBD_ITERATIONS=20` (`newton_skill_env_base.py:97-99`).
- **Episode/horizon:** route `ROUTE_TERMINAL_STEPS=900` (~18.75 s, `route_env_config.py:99`); per-skill 100–300 steps
  (`task_config.py:378-383`); orchestrator RL cap `DEFAULT_RL_MAX_STEPS=200`.
- **Sustain/latch budgets:** `K_ROUTE_SEAT=10`, `K_GRASP=5`, `K_INSERT=10`, `K_CLAMP=5`; HOLD `HOLD_THRESH_MM=15`/`MAX_HOLD_STEPS=24`
  (no-terminate); pin `PIN_TRIGGER_DWELL_K=3`.
- **Explicit latency / deadline / real-time constant = ABSENT_IN_DECLARED_CLOSURE.** Query
  `grep -rniE "latency|deadline|real.?time|wall.?clock|Hz" envs/ orchestrator/ skills/ configs/` → only derived-Hz prints in the
  unrelated `hook_hanging_env.py`. **All budgets are sim-step counts; charter §4's D_situation/T_detect/T_ground/T_select/T_handoff
  must be DESIGNED (no wall-clock deadline exists in code).**

---

## 7. Fail-closed findings register (absences, with queries)

| finding | class | query / evidence |
|---|---|---|
| No **active route checkpoint/dataset** on disk (default = B0 demo-replay) | ABSENT_IN_DECLARED_CLOSURE | `find … policy.pt/bc_dataset*.npz/*_sidecar.json` (excl thread-vault) → 0 |
| **Insert RL env** file | ABSENT_IN_DECLARED_CLOSURE | `find newton_insert*env*.py` → none (comment refs only) |
| **Safe-interruption checkpoint** (core) | ABSENT_IN_DECLARED_CLOSURE | grep interrupt/preempt/safe-stop → 0 core hits |
| **Real-time/deadline/latency constant** | ABSENT_IN_DECLARED_CLOSURE | grep latency/deadline/real-time → only unrelated Hz prints |
| Vision belief → route policy obs | UNVERIFIED→(effectively unwired) | 62D obs all privileged; assembler stub `NotImplementedError` |
| `ObsBuilder24D` config import | broken (legacy) | `OBS_DIM/OBS_MODES/OBS_NORMALIZATION` undefined in `task_config.py` |
| T3 WM trainer `train_dual_arm_msa.py`; AC/AR/IC `train_*.py` | ABSENT | `find` → 0 (artifacts exist on disk) |
| `FALLBACK`/legacy SOMA path health vs live route | UNVERIFIED (not wired to route → moot for live path) | `FALLBACK` comment at `task_config.py:192`; no route ref |

---

## 8. Charter §5 six-schema mapping (current factual state — NOT a design)

| schema surface | current factual state |
|---|---|
| state/belief | 62D privileged sim state (Stack B); no vision grounding wired |
| skill action/lifecycle | 3 unreconciled taxonomies (T1 DAPG/LoRA, T2 scripted, T3 WM-PPO); no common typed contract |
| transition (dynamics) distribution | none at skill resolution; T3 `WorldModelEncoder` predicts latent for a separate stack |
| handoff/recovery | physics-snapshot rollback (A) + phase-bank re-fork (B); no recovery skill; no declared handoff-state contract |
| safety/event/abstention | SOMA envelope unwired to route; static Z-clip only; OOD abstention = default-accept stub |
| per-event deadline | none; only sim-step budgets |

## 9. Charter §6 10-gate factual state (D0 registers, claims **NO gate PASS**)

| # | gate | current factual state (NOT a verdict) |
|---|---|---|
| 1 | algorithm independence | ABSENT — 3 taxonomies, no common contract |
| 2 | vision grounding | ABSENT on live path — obs 100% privileged; vision unwired |
| 3 | model calibration | ABSENT — no skill-resolution dynamics model |
| 4 | unknown-state abstention | stub only (`bc_p0_region_check` default-accept) |
| 5 | safe interruption | ABSENT (registered query) |
| 6 | anti-thrashing | ABSENT — no switch penalty/hysteresis/dwell at skill level |
| 7 | real-time (miss/max/fallback) | ABSENT — no wall-clock deadline; sim-step budgets only |
| 8 | safety independence | PARTIAL/unwired — envelope exists but not on live route; static Z-clip only |
| 9 | comparative value | baseline present (orchestrator heuristic recovery + fixed chain) to compare against |
| 10 | no premature claim | honored — D0 asserts no training-ready/closed-loop readiness |

---

## 10. Flagged latent finding (surfaced, NOT fixed — out of D0 scope; routes to p4/Rs)

`newton_grip_env.py:1258` (Clamp) and `:1441` (Unclamp) set `timeouts[w]=int(timeout)` **without** the
`and not success and not explosion[ and not cable_dropped]` guard that AC/AR/route envs apply. On a horizon-coincident terminal
this hands a polluted `extras["time_outs"]=1` to RSL-RL (the exact prohibited.md "timeouts汚染" pattern; historical value_loss
105× blow-up). **Impact is UNVERIFIED**: the orchestrator's `derive_skill_result` checks success/explosion before time_outs so
its verdict is unaffected; the pollution only reaches the trainer if the grip env is trained standalone via RSL-RL. This is in
`newton_grip_env.py` (§DDR #18 grip domain = **p4**); per the separation invariant I do not touch it — surfaced for p4/Rs
disposition only.

---

## Disposition

This is the D0 **factual inventory** (facts separated from design; absences fail-closed; post-bracket clean). It is NOT the
architecture design and claims no gate PASS. Request pN **D0-exit design verify** of this inventory's completeness/accuracy; the
**WMSO D0 architecture draft** (state/action/transition/safety schemas + event deadlines, per charter §5 D0 deliverable) is the
next deliverable and will go through its own design verify (charter §5 "independent design verify"). production/training/sim/
inference/closed-loop/p4-grip remain UNAUTHORIZED.
