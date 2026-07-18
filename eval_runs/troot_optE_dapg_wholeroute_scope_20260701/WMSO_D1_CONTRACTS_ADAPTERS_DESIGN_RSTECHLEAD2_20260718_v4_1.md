# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO **D1 Skill contracts + adapters** — DESIGN draft **v4.1** (folds pN v4 readback R1–R4, record-only)

- supersedes **v4** (`91210c26c4`, sha256 `480430b73119…`). node `T-WMSO`; author `w2:pQ`; verify `w2:pN`; custody `w2:p6`. prepared_at **2026-07-19 ~00:55 JST**.
- ⛔ **DESIGN-ONLY / record-only; no code, no schema recovery, no gate PASS.** code GO stays **CLOSED until pN v4.1 readback**.
- **pN v4 readback** = **HOLD R1–R4** (record-only); **decisions #1/#2 + B3/B5 = PASS-CLOSE**; code-path set stays frozen. This v4.1 folds R1–R4.
- **rulings unchanged**: #1=A non-crypto · #2=RSL `model_9` identity-only · both learned schemas UNRESOLVED · D1 exit HOLD · offline/live=false.
- **all hashes pQ-verified full 64-hex** (`sha256sum` / independent canonical recompute — R2 reproduced pN exactly):
  - final `model_best.pt` = `a49b6342bd1b0e16b549a87d0dea1423e967787bf8e115d98da2f2b39e78eb9b`
  - base `base_model_mixed_20260404_190016.pt` = `065c458101137729d4ff2593014e8c2d20c8c203a0037c784f160aa0c689313a`
  - RL-only `model_9.pt` = `7d80448612881635e1cf83d90993cf72194d5ac5f08cd97c28213950e11f4ffa`
  - raw `summary.json` = `d280ea973c025d0bb5bade56eb0466bb2f4078e9ac287e2c8cd0453d59e2c620`
  - `finetune_cfg_hash` (canonical projection, R2) = `1977e04691912dbef1b2d4bc3527272ec82456af3451fc80ff8445747bdd5594`

## Fold map (pN v4 readback R1–R4)
| id | blocker | fix in v4.1 |
|---|---|---|
| **R1** | SCRIPTED/WAIT paths shortened; line numbers unstable (banked `91210c` `_run_wait`=:1211, dirty tree=:1216); hashes shown as prefixes | §3: **full repo-relative paths + `::qualname`**; **remove all line numbers**; manifest hashes **full 64-hex** (doc prefixes display-only) |
| **R2** | `finetune_cfg_hash` misclassified (included outcome `dapg.bc_losses`, omitted training inputs) | §5: **exact canonical-JSON projection** over pN's key set (excl `bc_losses`) = `1977e046…5594` (pQ-verified); retain raw summary sha separately |
| **R3** | B4 whole-file hash ≠ complete identity; source closure incomplete | §3/§8: **`source_closure_sha256`** = deterministic aggregate over the enumerated members (full path + full sha); changed/missing/added ⇒ fail-closed |
| **R4** | §3b not exact: missing `SkillActionKey`, `NOT_APPLICABLE_RL_ONLY`, `belief_ref` union, concrete field types; WAIT config undefined | §3b: full concrete instantiation (below) |

## §1. FACTUAL inventory / §2. D1-A / §4. D1-C(2,3) / §7. status — unchanged from v4 (PASS-CLOSE)
(§4: belief map = declarative `belief_map_design.json`, B5; both learned exemplar schemas UNRESOLVED ⇒ `contract_conformant=false`, B3. §7: authority validated, offline/live=false ∀.)

## §3. D1-B — per-skill identity (R1 full paths, no line numbers, qualname; R3 source closure)
| # | skill_id | kind | exact artifact / source (full repo-relative; **no line numbers**) | identity | status |
|---|---|---|---|---|---|
| 1 | APPROACH_CABLE | LEARNED (BC+RL) | `thread_isaac_lab/data/rl_approach_cable_A_w256_20260409_073409/model_best.pt` | triad §5 | `identity_pinned=true`, `contract_conformant=false` (schema), exit HOLD |
| 2 | CLAMP{side} | LEARNED | — no exact artifact selected | — | ⛔ INADMISSIBLE_AMBIGUOUS |
| 3 | INSERT_INTO_CLIP | LEARNED (RL-only) | `thread_isaac_lab/logs/rsl_rl/insert_clip_20260325_235722/model_9.pt` | §6 | `identity_pinned=true`, `field_semantics=UNRESOLVED`, `contract_conformant=false` |
| 4 | UNCLAMP | LEARNED | ABSENT (`thread_isaac_lab/data/rl_unclamp_cache/*.npz` only) | — | ⛔ inadmissible (no policy) |
| 5 | AERIAL_REGRASP | LEARNED | — no exact artifact selected | — | ⛔ INADMISSIBLE_AMBIGUOUS |
| 6 | TRANSPORT | SCRIPTED | `thread_isaac_lab/skills/scripted_skills.py::transport_to_clip` | `skill_id`+`callable_qualname`+`source_closure_sha256`(§8) | pinnable |
| 7 | RECLAMP_L | SCRIPTED | `thread_isaac_lab/skills/scripted_skills.py::reclamp_left` | same | pinnable |
| 8 | HALF_UNCLAMP_RELEASE | SCRIPTED | `thread_isaac_lab/skills/scripted_skills.py::half_unclamp_release` | same | pinnable |
| 9 | CLIP_CONFIRM | WAIT | `thread_isaac_lab/orchestrator/routing_orchestrator.py::_run_wait` (**qualname only, never line** — banked/dirty drift :1211/:1216) | `skill_id`+`callable_qualname`+`source_closure_sha256`(WAIT set, §8) | pinnable |

## §3b. Concrete contract instantiation (R4 — exact; unknown/missing ⇒ reject)
- **`SkillActionKey`** = `{ skill_id, executable_identity, handoff_start_context }` — **carried through the handoff producer** (§3b handoff.producer references this `SkillActionKey`).
- **`executable_identity`** tagged union on `kind`:
  - `LEARNED{ policy_weight_hash:hex64, lineage{ family:enum{BC,BC+RL,PPO,DAPG}, base_ckpt_hash:hex64|null, finetune_cfg_hash:hex64|null, final_policy_hash:hex64 }, train_time_crypto_bound:bool, association_strength:enum{CRYPTO_TRAIN_TIME_BOUND, RECORDED_PATH_CONFIG_COLOCATION, **NOT_APPLICABLE_RL_ONLY**} }` — RL-only ⇒ `base_ckpt_hash=null, finetune_cfg_hash=null, association_strength=NOT_APPLICABLE_RL_ONLY` (R4, lets `model_9` satisfy the LEARNED union).
  - `SCRIPTED{ skill_id, callable_qualname:str, source_closure_sha256:hex64 }` · `WAIT{ skill_id, callable_qualname:str, source_closure_sha256:hex64 }`.
- **`obs_action_schema`** = `{ obs_fields:[{field_id, dtype, shape, unit, frame}], action_fields:[…], field_semantics:enum{RESOLVED, UNRESOLVED} }` — `UNRESOLVED ⇒ contract_conformant=false` (B3; no generic shape acceptance).
- **`initiation_predicate`** = `{ expr_kind:enum{threshold, region, boolean_and, callable_ref}, params:obj, required_belief_fields:[field_id] }` (required).
- **`progress_phase`** = `{ phase_id:enum{G1..G6}, progress:[0,1]|null }`.
- **`termination_classes`** = set⊆`{success, failure, timeout, invalid_state}` (required, non-empty).
- **`safe_interruption_checkpoints`** = `[checkpoint_id]` (may be empty).
- **`handoff`** = `SkillHandoffState{ handoff_state_id, schema_version:semver, producer{ SkillActionKey, outcome: TERMINAL{ terminal_class:enum{success,failure,timeout,invalid_state}; checkpoint_id:id|null } | INTERRUPT{ checkpoint_id:id(mandatory); interrupt_reason:enum{planned_switch,event,safety_stabilized} } }, belief_ref{ value: **canonical BeliefState snapshot | ref_hash:hex64**, t_obs:monotonic_s, ttl:s, confidence:[0,1], ood_flag:bool }, ownership{ contact:bool, resource:obj, control:{EE_L:bool,EE_R:bool,gripper_L:bool,gripper_R:bool} }, compatibility{ predicate, predicate_version:semver, next_owner:id } }` + `accepted_incoming_handoff_set:[handoff_state_id]`.
- transition status machine: `offer → accept+ack → commit | abort`; single-writer manager atomic `control_ownership` flip; `reject|abort|timeout ⇒ producer-retains + safe-stop`.
- **`duration_cost_distribution`** = `{ dist_kind:enum{empirical, gaussian, unknown}, duration:{mean_s,std_s,p50,p95}|null, cost:{…}|null }` (null = unmodeled, LL-WMF gap).
- **`resource_requirements`** = `{ control_ownership:{EE_L,EE_R,gripper_L,gripper_R:bool}, compute:enum{fast_path, slow_path} }`.
- **`recovery_rollback_target`** = `handoff_state_id | null` · **`fail_closed_action`** = enum`{re_observe, safe_stop, handback_to_owner}`.
- **`policy_version`** = str · **`freshness`** = `{ max_staleness_s:float|null }` · **`support_boundary`** = `{ region_ref:str|null, in_support_predicate:ref|null }`.
- **`admissibility`** = `{ identity_pinned:bool, contract_conformant:bool, offline_orchestration_admissible:false, closed_loop_admissible:false }` (validated, C4).
**Rule**: any unknown key or missing required field ⇒ **reject** (fail-closed).

## §5. D1-D — BC+RL triad (DECISION #1=A; R2 hash derivation frozen)
`executable_identity.LEARNED` for APPROACH: `final_policy_hash=a49b6342…78eb9b`, `base_ckpt_hash=065c4581…689313a`, `finetune_cfg_hash=1977e046…5594`
where **`finetune_cfg_hash = sha256( json.dumps(proj, sort_keys=true, ensure_ascii=false, separators=(",",":")).encode("utf-8") )`**, `proj` = the
projection over EXACT keys `{experiment, framework, base_model, lora_rank, world_count, max_iterations, num_steps_per_env, device, ppo, env_config,
dapg∖{bc_losses}, convergence∩{metric,mode,patience,min_iterations,delta}}` (⛔ **excludes `dapg.bc_losses` = outcome**, R2). **Retain
`raw_summary_sha256 = d280ea97…5e2c620` separately.** `train_time_crypto_bound=false`, `association_strength=RECORDED_PATH_CONFIG_COLOCATION`
(present-time bytes, NOT train-time proof; never claim crypto-verified; ⛔ no retrain). exit#3 HOLD until schema (§9).

## §6. D1-E — RL-only (DECISION #2; R4)
`insert_clip/model_9.pt` `policy_weight_hash=final_policy_hash=7d804486…f4ffa`, `base_ckpt_hash=null`, `finetune_cfg_hash=null`,
`association_strength=NOT_APPLICABLE_RL_ONLY`, `train_time_crypto_bound=false`. shapes 10D→3D ⇒ `field_semantics=UNRESOLVED`,
`contract_conformant=false`, offline/live=false, until training-env schema pins field order/unit/frame/action scaling. structural-only ≠ gate① PASS.

## §8. D1-G — harness + `source_closure_sha256` (R3) + fail-closed
**`source_closure_sha256`** = `sha256( "\n".join( sorted( f"{full_repo_relative_path}:{sha256(file)}" for file in closure_members ) ).encode("utf-8") )`.
- **SCRIPTED closure_members** = { `thread_isaac_lab/skills/scripted_skills.py`, `thread_isaac_lab/skills/result.py`,
  `thread_isaac_lab/scripts/newton_routing_utils.py`, `thread_isaac_lab/configs/task_config.py`, `thread_isaac_lab/skills/step_table.py` }.
- **WAIT closure_members** = SCRIPTED set ∪ { `thread_isaac_lab/orchestrator/routing_orchestrator.py` } (WAIT calls `scripted_skills.clip_confirm`; schedule/clip_index from `step_table`).
- The `skill_contracts_manifest.json` **enumerates every member** (path + full sha); any **changed/missing/added member ⇒ fail-closed** (identity invalid). `skill_id`+`callable_qualname` remain in the key (keeps the 3 scripted keys distinct). ⛔ a single whole-file hash is **not** a complete identity.
Controls (unchanged from v4, no line numbers): missing/changed hash ⇒ reject · different `skill_id`+`qualname`, same file ⇒ different key · legit alias `clamp_r`→CLAMP canonicalizes; genuine duplicate/unknown ⇒ reject · `schema_version` mismatch ⇒ reject · `PRIVILEGED_SIM∧prod_admissible=true` ⇒ reject · `field_semantics=UNRESOLVED` ⇒ `contract_conformant=false` · `TERMINAL`/`INTERRUPT` missing-mandatory ⇒ reject · empty/absent/summary-only-no-`model_best` ⇒ inadmissible · authority positive+negative · **unknown key / missing required ⇒ reject**.

## §9. D1 exit / §10 code-path / §11 — unchanged from v4
exit#3 = **HOLD** (DECISION#1=A alone ≠ PASS while exemplar schemas UNRESOLVED, B6); **completion gate = authoritative training-env schema recovery**
(APPROACH 42D→12D, INSERT 10D→3D). Code-path FROZEN (12 new files, changed=∅; 2026 SPDX; no dependency); GO CLOSED. C7 O0 inverse-binding noted.
RS71 §0 invariants untouched; `T-WMSO-SDM` not created; non-mixing held.
**Next**: bank v4.1 → **pN v4.1 readback**; no `[CHANGE]` until GO.
