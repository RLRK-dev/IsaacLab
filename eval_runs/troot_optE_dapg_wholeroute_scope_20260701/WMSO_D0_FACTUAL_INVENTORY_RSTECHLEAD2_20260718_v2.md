# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO D0 — factual read-only inventory **v2** (fixes B1–B5)

- supersedes v1 `…_RSTECHLEAD2_20260718.md` (sha `59d0e11c…`). node `T-WMSO`; verify `w2:pN`; custody `w2:p6`.
- prepared_at: 2026-07-18 14:40 JST · repo HEAD `7f8ef1f145` · **read-only, no run, no gate PASS claimed**.
- pN verdict addressed: D0-inventory HOLD (14:32) B1 CRITICAL / B2 CRITICAL / B3 HIGH / B4 HIGH / B5 MED. Hash concordance,
  content-delta=0, and finding *directions* were pN-confirmed; this v2 corrects provenance + the surface conflation + scope.

**Provenance (B1 fixed):**
- base closure = v3 manifest (file `6abb176e…`, aggregate `5d8d2216…`, 46 rows).
- extension = **ext-v2** `…_INVENTORY_EXT_MANIFEST_20260718_v2.tsv` (file `672bf624…`, aggregate `3f91fc85…`, 9 rows,
  **registered taxonomy** clean|modified|untracked|gitignored), adding the 5 discovered live-env sources + 2 WM checkpoints
  + **all extra cites** (`.claude/rules/prohibited.md`, `envs/hook_hanging_env.py`).
- **freeze-before-reextraction**: ext-v2 was frozen **first**, then the sources were re-extracted post-freeze (fixing the v1
  read-then-freeze deviation). Content unchanged (see post-bracket).
- **combined post-bracket = `changed_during_inventory=[]`** (base 45 + ext-v2 9 = **54 sources checked, 0 changed**).

---

## 0. Architecture orientation — **THREE surfaces** (B2 correction; NOT two stacks)

| surface | file | role | obs / action | policy |
|---|---|---|---|---|
| **A** per-skill orchestrator | `orchestrator/routing_orchestrator.py` + 43 `StepDef` (`skills/step_table.py`) | chains per-skill RL + scripted + wait; snapshot/rollback recovery | per-skill env schemas; `SkillResult` | dispatches per-skill policies |
| **B** whole-route RL env | `envs/newton_route_env.py` (`NewtonRouteEnv(VecEnv)`, :392) | the RL **training** MDP over C1→C2, G1–G6 latched phases | **62D privileged obs / 6D alpha-residual** | **does NOT load a policy internally** (`grep torch.load\|load_state_dict\|OnPolicyRunner` → 0); trainer authority = **RLPD residual-on-script** (planned, SAC-family; `TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md:7,14,21`) |
| **C** route runner/mirror | `scripts/policy_route_runner.py` | executes a route rollout (B0 default / B1 optional `--policy`) | **25/27D obs** (12 + n_phases) / 6D action | **BC actor-mean** (`bc_train_route.py`), deterministic; default B0 = open-loop demo replay |

**Correction of the v1 conflation:** v1 said "live route = BC-only 6D alpha-residual, obs 62D" — that **merged surface B and
surface C**. The 62D/6D-residual is **surface B** (RL env, RLPD trainer, no internal policy); the **BC actor-mean** is **surface C**
(25/27D runner). They are distinct surfaces with different obs schemas and different policy families.
`envs/route_executor.py` is surface B's scripted phase-clock engine; `envs/newton_skill_env_base.py` is a shared utility module
(scene/IK/quat/`physics_step`), no termination logic.

---

## 1. Learned skills + policy lineage (item 1)

**Skill vocabularies (multiple, unreconciled — the main gate① integration risk):**
- **`SkillName`** — 9-type **MIXED** step-table taxonomy (`step_table.py:35-51`; RL/scripted/wait split via
  `routing_orchestrator.py:71-81`): **5 RL** (APPROACH_CABLE, CLAMP, INSERT_INTO_CLIP, UNCLAMP, AERIAL_REGRASP), **3 scripted**
  (TRANSPORT, RECLAMP_L, HALF_UNCLAMP_RELEASE), **1 wait** (CLIP_CONFIRM). (Corrects v1's "T2=scripted".)
- **`SkillType`** — 7 RL adapter types (`models/skill_adapter.py:45-58`): the RL subset above + CLAMP_R/CLAMP_L variants.
- **scripted functions** — `skills/scripted_skills.py` (transport/reclamp/half_unclamp/clip_confirm; IK-waypoint + finger interp).
- **`bimanual_*`** — 6 World-Model skills (`skill_adapter_with_prediction.py:150-157`; `dual_arm_skill_rewards.py:180-187`).

**Policy families (evidence):**
- **Per-skill RL (A) = DAPG** (PPO + BC-aux, LoRA on frozen base; `train_common.py:7,126,195,249-255,343-345`); Grip wrapper
  present (`train_grip.py:268-291`); AC/AR/IC per-skill `train_*.py` wrappers **ABSENT** (artifacts exist on disk).
- **Base model = BC-only** (`train_base_model.py:96,140-147`, `45→128→128→12`) — frozen base, not a skill.
- **Surface C route policy (B1) = BC-only deterministic actor-mean** (`bc_train_route.py:74-78` `obs_dim→6,(128,128)`;
  `policy_route_runner.py:216-226` uses `policy.actor(obs)` mean, never `.act()` sample).
- **Surface B whole-route policy = RL residual (planned RLPD residual-on-script)** — the env is BC-independent; there is **no BC
  route policy inside surface B**.
- **`bimanual_*` = WM + PPO** (frozen 352D `WorldModelEncoder` + Gaussian policy; `base_policy.py:66-104,281-297`); trainer
  `train_dual_arm_msa.py` **ABSENT**.

**Immutable policy/version hash:** YES `bc_train_route.py:117-135` (`ckpt_sha256`/`dataset_sha256` sidecar) +
`policy_route_runner.py:35-46,456,622` (`policy_sha256`, fail-closed `ROUTE_SHA_ACCEPT`/`TASKCFG_SHA`/`BASE_SHA`). NO in
`eval_skill.py:862` / `train_common.py` / `train_base_model.py`.

---

## 2. Observation / action schema + vision (item 2)

**Surface B (`newton_route_env.py`):** obs **62D** (`_compute_obs_batch:1475-1587`; SSOT `route_env_config.py:45 OBS_DIM=62`);
action **6D alpha-residual** (`num_actions=6`, :427; `POS_RESIDUAL_SCALE=0.015 m`, :401), non-accumulating, phase-conditional
projection `_project_residual` (:1137-1156), commanded = absolute base + residual (`_apply_actions_batch:1158-1195`); grip is a
scripted servo, not an action dim (:1174). **All 62 obs dims = PRIVILEGED SIM GROUND-TRUTH or config constants; ZERO
vision-derived** (contact `[53:55]` is a geometric proximity proxy, :1564-1568).

**Surface C (`policy_route_runner.py`):** obs **25/27D** (12 + n_phases: `R_EE[0:3],L_EE[3:6],seg[6:9],next_clip[9:12],
phase-onehot[12:]`, `route_demo_to_bc.py:301`, runner `:200-212,361-370`); action 6D (ΔEE R/L). Separate schema from surface B.

**Vision belief exists but is UNWIRED to surfaces B and C:** `VisionPipelineStage1to3`/`MultiCamCableStatePipeline`
(`vision_pipeline.py:45,456` — estimator track), `FrozenResNetEncoder` (`visual_encoder.py:21` — feeds separate camera
`BasePolicy`), `VisionObsAssembler` (**`NotImplementedError` stub**, `vision_obs_assembler.py:149-153,189-193`), `ObsBuilder24D`
(`obs_builder.py:33` — vision only if `num_envs==1`; config import broken: `OBS_DIM/OBS_MODES/OBS_NORMALIZATION` undefined in
`task_config.py:30`). None feeds surface B/C obs.

---

## 3. Termination / failure / timeout + safe-interruption (item 3)

`SkillResult` = SUCCESS/TIMEOUT/FAIL/CABLE_DROP/EXPLOSION (`skills/result.py:18-25`); orchestrator mapping
`derive_skill_result:419-469` (CABLE_DROP subsumed by FAIL, :438-441). Per-skill env done: AC
`newton_approach_cable_mujoco_env.py:981`, AR `newton_aerial_regrasp_mujoco_env.py:1315`, Clamp/Unclamp `newton_grip_env.py:1252/1437`.
Surface B done `newton_route_env.py:1720` (`success|timeout|explosion|dropped`); success=G6 (:1704-1711); explosion (near>1.0|NaN,
:1635-1640); dropped (:1653-1672); span/reach informative-only (:44-45). **Insert RL env file** `ABSENT_IN_DECLARED_CLOSURE`
(query `find thread_isaac_lab -name 'newton_insert*env*.py'` → 0; comment refs only).

Timeouts-invariant honored: `newton_route_env.py:1725`, AC:1003, AR:1334. ⚠ latent divergence: grip `newton_grip_env.py:1258/1441`
`timeouts=int(timeout)` unguarded (§10). **Safe-interruption checkpoint = `ABSENT_IN_DECLARED_CLOSURE`** (exact query
`grep -rniE "interrupt|preempt|safe.interrupt|safe.stop|switch.mid|mid.skill" thread_isaac_lab/envs/ thread_isaac_lab/orchestrator/ thread_isaac_lab/skills/ thread_isaac_lab/configs/` → 0 core hits; nearest analogs HOLD/MARCH pause `route_executor.py:4806-4878`, EXPLOSION→abort).

---

## 4. Skill Handoff State + transition / recovery / fallback (item 4)

Surface A: 43-STEP sequencer; `execute_skill`→`_run_rl_episode`/`_run_scripted`/`_run_wait`; state via `self.state_0`; handoff
hazards `mask_l_arm_action_if_needed`/`apply_finger_close_if_needed` (`routing_orchestrator.py:261-411`); recovery engine
`execute_step` retry/rollback/abort (`MAX_RETRY=3`, `MAX_ROLLBACK_DEPTH=3`, :1063-1214); OOD gate `bc_p0_region_check` =
**default-accept stub** (:1152-1162). Handoff-state object = `StateSnapshot` **physics-rollback snapshot** (`snapshot.py:19-31`),
not a declared skill-handoff-state contract (charter §3). Surface B: `RouteInterfaceV1` (`route_env_config.py:194-260`),
`reset_to_phase(k)` phase-bank re-fork (k=0 stub, `newton_route_env.py:2028,2066-2069`). **No dedicated recovery/fallback SKILL.**

---

## 5. Surface behavior + existing safety path (item 5 — B5 corrected)

- Surface A behavior = heuristic skill-chaining + retry/rollback recovery (§4) = the **baseline gate⑨ compares WMSO against**.
  Single-world only (`num_envs==1`, `routing_orchestrator.py:799-809`; multi-world deferred → DDR#19).
- **Surface B live-route "safety" has TWO in-env mechanisms, NEITHER an independent low-level monitor:**
  1. **static Z-clip** on the IK target: `target_z = clip(z, lane-floor, EE_Z_SAFETY_UPPER)` (`newton_route_env.py:1189-1193`,
     comment "Substrate Z safety floor/ceiling ONLY").
  2. **task-level fault detection + episode termination**: explosion (`near>EXPLOSION_DIST_THRESH=1.0`|NaN, :1635-1640) and
     drop (:1653-1672) set `done` + `TERM_PENALTY=-10` (:1714-1720). This is a *reward/termination* fault response, **not** a
     real-time actuator-level safety layer.
- **The SOMA `SafetyEnvelope`/`FallbackGuard` (L1-3 measure-only, L4 residual-zero; `safety_envelope.py:8-11,116-126`,
  `fallback_guard.py:31-68`) is UNWIRED to surfaces B and C** (`grep FallbackGuard|SafetyEnvelope|safety_guard` in
  `newton_route_env.py`/`route_executor.py`/`policy_route_runner.py` → 0 refs).
- ⇒ charter §2.4 / gate⑧: **no independent low-level safety monitor on the live route**; only a static clip + task-level fault
  termination + an unwired legacy envelope.

---

## 6. Per-event deadline candidates + acceptance (item 6)

Timing (all sim-step counts, NOT wall-clock): `DT=1/480 s`; `RL_SIM_SUBSTEPS=4`; `PHYSICS_STEPS_PER_RL=10`
(`newton_route_env.py:404`, cross-asserted :620) ⇒ 1 RL step ≈ 20.83 ms (~48 Hz); IK budgets 100/30, VBD 20
(`newton_skill_env_base.py:97-99`). Horizon `ROUTE_TERMINAL_STEPS=900` (~18.75 s, `route_env_config.py:99`); per-skill 100–300
(`task_config.py:378-383`); orch cap `DEFAULT_RL_MAX_STEPS=200`. Sustain `K_ROUTE_SEAT=10`/`K_CLAMP=5` etc.
**Real-time/deadline/latency constant = `ABSENT_IN_DECLARED_CLOSURE`** (exact query
`grep -rniE "latency|deadline|real.?time|wall.?clock|Hz|hertz" thread_isaac_lab/envs/ thread_isaac_lab/orchestrator/ thread_isaac_lab/skills/ thread_isaac_lab/configs/` → only derived-Hz prints in the unrelated `envs/hook_hanging_env.py:989-991`). charter §4's
`D_situation`/`T_detect/T_ground/T_select/T_handoff` must be DESIGNED.

---

## 7. Fail-closed findings register (exact queries, no elision)

| finding | class | exact query / evidence |
|---|---|---|
| Surface-C **route policy.pt / bc_dataset / sidecar** not materialized | ABSENT_IN_DECLARED_CLOSURE | `find data thread_isaac_lab/data -maxdepth 3 \( -name 'policy.pt' -o -name 'policy_abs*.pt' -o -name 'bc_dataset*.npz' \)` → 0 |
| **Default** active checkpoint selection (surface C runner) | ABSENT (default) | `policy_route_runner.py` `--policy default=None` (:1491) |
| **Current** active checkpoint selection | UNVERIFIED | no default; candidate checkpoints exist (§ below), none is selected-by-default |
| **Insert RL env** file | ABSENT_IN_DECLARED_CLOSURE | `find thread_isaac_lab -name 'newton_insert*env*.py'` → 0 (comment refs only) |
| **Safe-interruption checkpoint** (core) | ABSENT_IN_DECLARED_CLOSURE | grep query in §3 → 0 core hits |
| **Real-time/deadline/latency constant** | ABSENT_IN_DECLARED_CLOSURE | grep query in §6 → only unrelated Hz prints |
| Vision belief → surface B/C obs | UNVERIFIED (effectively unwired) | 62D & 25/27D obs carry no vision term; assembler is `NotImplementedError` |
| `ObsBuilder24D` config import | broken (legacy) | `OBS_DIM/OBS_MODES/OBS_NORMALIZATION` undefined in `task_config.py` |
| T3 WM trainer / AC-AR-IC `train_*.py` | ABSENT_IN_DECLARED_CLOSURE | `find … train_dual_arm_msa.py / train_{approach,insert,aerial,clamp}*.py` → 0 |

**Candidate checkpoints that DO exist (B3 correction — v1's "no active checkpoint" was overbroad/FALSE):** exact roots/patterns:
`data/residual_ppo_d4v2/ckpt_{iter50,iter100,iter150,final}.pt`, `data/residual_ppo/ckpt_final.pt`,
`data/residual_ppo_d4/ckpt_*.pt` (surface-B residual candidates), `data/fine_rl_*/final_policy.pt`,
`thread_isaac_lab/data/base_model_*.pt`, `data/rl_{grip,aerial_regrasp,insert_clip,grasp_cable}_*` dirs,
`thread_isaac_lab/checkpoints/world_model_dual_arm/phase{1,2}_best.pt`. **Disposition:** none is a default/selected active route
policy → active selection UNVERIFIED; per the two-stage rule, if any is later selected it is frozen (v3_ext-style) **before**
content read. No checkpoint binary was opened.

---

## 8. Charter §5 six-schema mapping (current factual state — NOT a design)

| schema surface | current factual state |
|---|---|
| state/belief | surface B 62D / surface C 25-27D — all privileged sim state; vision unwired |
| skill action/lifecycle | multiple unreconciled vocabularies (SkillName-9 mixed / SkillType-7 RL / scripted fns / bimanual-6 WM); no common typed contract |
| transition distribution | none at skill resolution; `WorldModelEncoder` predicts latent for the separate `bimanual_*` stack |
| handoff/recovery | physics-snapshot rollback (A) + phase-bank re-fork (B); no recovery skill; no declared handoff-state contract |
| safety/event/abstention | Z-clip + task-level fault termination on B; SOMA envelope unwired; OOD abstention = default-accept stub |
| per-event deadline | none; sim-step budgets only |

## 9. Charter §6 10-gate factual state (D0 registers contracts; **NO gate PASS**; taxonomy per v3 discipline)

| # | gate | state | class |
|---|---|---|---|
| 1 | algorithm independence | multiple unreconciled skill vocabularies; no common contract | PARTIAL |
| 2 | vision grounding | obs 100% privileged on B & C; vision unwired | ABSENT_IN_DECLARED_CLOSURE |
| 3 | model calibration | no skill-resolution dynamics model | ABSENT_IN_DECLARED_CLOSURE |
| 4 | unknown-state abstention | `bc_p0_region_check` default-accept stub | PARTIAL (stub) |
| 5 | safe interruption | grep query → 0 core hits | ABSENT_IN_DECLARED_CLOSURE |
| 6 | anti-thrashing | no skill-level switch penalty/hysteresis/dwell | UNVERIFIED |
| 7 | real-time | no wall-clock deadline; sim-step budgets only | ABSENT_IN_DECLARED_CLOSURE |
| 8 | safety independence | Z-clip + task-fault termination; envelope unwired; no independent low-level monitor | PARTIAL |
| 9 | comparative value | baseline present (orchestrator heuristic recovery + fixed chain) | PARTIAL (baseline exists) |
| 10 | no premature claim | **contract registered / evidence pending** (D0 asserts no training-ready/closed-loop readiness) | — |

---

## 10. Flagged latent finding (surfaced, NOT fixed — p4/§DDR#18 domain)

`newton_grip_env.py:1258` (Clamp) / `:1441` (Unclamp) set `timeouts[w]=int(timeout)` **without** the
`and not success and not explosion[ and not cable_dropped]` guard that AC/AR/route envs apply (prohibited.md "timeouts汚染";
value_loss 105× history). **Impact UNVERIFIED** — orchestrator `derive_skill_result` checks success/explosion before time_outs
(verdict unaffected); pollution reaches the trainer only if grip is trained standalone via RSL-RL. Grip = p4 domain; surfaced for
p4/Rs disposition only (I do not touch it).

---

## Disposition

D0 **factual inventory v2** — provenance fixed (freeze-before-reextraction, combined 54-source post-bracket `[]`, extra cites
frozen), 3-surface conflation corrected, checkpoint claim scoped, taxonomy/fail-closed made consistent, safety wording separated.
Facts separated from design; no gate PASS. Request pN independent verify; on **D0 factual PASS**, the charter §5 **architecture
draft** proceeds to its own D0-exit design verify. production/training/sim/inference/closed-loop/p4-grip remain UNAUTHORIZED.
