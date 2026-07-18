# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO **D1 Skill contracts + adapters** — DESIGN draft **v4.1.1** (folds pN v4.1 readback C1–C3, record-only)

- supersedes **v4.1** (`82d6550512`, sha256 `be48a33e2c4d…`). node `T-WMSO`; author `w2:pQ`; verify `w2:pN`; custody `w2:p6`. prepared_at **2026-07-19 ~01:00 JST**.
- ⛔ **DESIGN-ONLY / record-only; no code, no schema recovery, no run.** code GO **CLOSED until pN v4.1.1 readback**.
- **pN v4.1 readback** = **HOLD C1–C3**; **R2 (finetune projection) + R3 (source-closure) PASS-CLOSE**; decisions + code-path freeze unchanged.
- **rulings stand**: #1=A non-crypto · #2=RSL `model_9` identity-only · both learned schemas UNRESOLVED · D1 exit HOLD · offline/live=false.
- **hashes (pQ-verified full 64-hex, carried)**: final `a49b6342bd1b0e16b549a87d0dea1423e967787bf8e115d98da2f2b39e78eb9b` · base
  `065c458101137729d4ff2593014e8c2d20c8c203a0037c784f160aa0c689313a` · RL-only `7d80448612881635e1cf83d90993cf72194d5ac5f08cd97c28213950e11f4ffa`
  · raw summary `d280ea973c025d0bb5bade56eb0466bb2f4078e9ac287e2c8cd0453d59e2c620` · finetune_cfg `1977e04691912dbef1b2d4bc3527272ec82456af3451fc80ff8445747bdd5594`.

## Fold map (pN v4.1 C1–C3)
| id | blocker | fix in v4.1.1 |
|---|---|---|
| **C1** | fold-map R1 + §3 WAIT still cited numeric lines while claiming they were removed | **all numeric line references removed**; only statement retained: **banked-vs-working-tree drift proves line-based identity invalid** (no numbers) |
| **C2** | §3b missing the outer exact `SkillLifecycleContract` root shape + `required_belief_confidence`; `handoff_start_context` untyped | §3b: **explicit root required-field list** (incl `required_belief_confidence`); `handoff_start_context` typed |
| **C3** | `progress_phase` used a global `G1..G6` (route-only, can't cover 9 skill-local phase spaces); `params:obj`/`cost:{…}`/`resource:obj`/bare `predicate`/`ref` left implementation discretion | §3b: **namespaced skill-local `phase_id:str`**; typed or **`schema_ref`+`schema_hash`** forms; **cost fields+units**; explicit **fail-close** conditions |

## §1 / §2 / §4 / §5 / §6 / §7 / §9 / §10 / §11 — unchanged from v4.1 (PASS-CLOSE; incl R2 finetune projection, R3 source-closure)
(Carried verbatim: DECISION #1=A non-crypto with `train_time_crypto_bound=false`; #2 RL-only `model_9` `NOT_APPLICABLE_RL_ONLY`; belief map =
declarative `belief_map_design.json`; both learned schemas UNRESOLVED ⇒ `contract_conformant=false`; exit#3 HOLD, completion gate = training-env
schema recovery; code-path FROZEN 12 files, changed=∅, 2026 SPDX, no dep; authority validated offline/live=false; §5 finetune_cfg_hash canonical
projection = `1977e046…5594` excl `dapg.bc_losses`; §8 `source_closure_sha256` over enumerated members, fail-closed.)

## §3. D1-B — per-skill identity (C1: NO numeric lines anywhere)
Same table as v4.1 §3. **WAIT row (C1 fix)**: `thread_isaac_lab/orchestrator/routing_orchestrator.py::_run_wait` — **keyed by qualname only; a
line-based identity is invalid because the callable's line differs between the banked commit and the working tree** (drift; no numbers cited).
All SCRIPTED rows likewise key by `path::qualname`, never line. Manifest hashes = full 64-hex (doc prefixes display-only).

## §3b. Concrete contract instantiation (C2 root shape + C3 exact types; unknown/missing ⇒ reject)

**`SkillLifecycleContract` — ROOT required fields (C2, all required unless marked nullable)**:
`schema_version:semver` · `SkillActionKey` · `policy_family:enum{BC,BC+RL,PPO,DAPG,SCRIPTED,WAIT}` · `obs_action_schema` · `initiation_predicate`
· **`required_belief_confidence:[0,1]`** · `termination_classes` · `progress_phase` · `safe_interruption_checkpoints` · `handoff` (SkillHandoffState)
· `accepted_incoming_handoff_set` · `duration_cost_distribution` · `resource_requirements` · `recovery_rollback_target:handoff_state_id|null` ·
`fail_closed_action` · `policy_version` · `freshness` · `support_boundary` · `admissibility`.

- **`SkillActionKey`** = `{ skill_id, executable_identity, handoff_start_context }`, carried through `handoff.producer`.
- **`handoff_start_context`** (C2 typed) = `{ incoming_handoff_state_id:handoff_state_id|null, initiation_context_hash:hex64 }`.
- **`executable_identity`** — tagged union (unchanged v4.1): `LEARNED{ policy_weight_hash:hex64, lineage{ family, base_ckpt_hash:hex64|null,
  finetune_cfg_hash:hex64|null, final_policy_hash:hex64 }, train_time_crypto_bound:bool, association_strength:enum{CRYPTO_TRAIN_TIME_BOUND,
  RECORDED_PATH_CONFIG_COLOCATION, NOT_APPLICABLE_RL_ONLY} }` · `SCRIPTED/WAIT{ skill_id, callable_qualname:str, source_closure_sha256:hex64 }`.
- **`obs_action_schema`** = `{ obs_fields:[{field_id:str, dtype:enum{float32,int32,bool}, shape:[int], unit:str, frame:enum{world,robot_base,EE_L,EE_R,clip,N/A}}], action_fields:[…], field_semantics:enum{RESOLVED,UNRESOLVED} }`.
- **`initiation_predicate`** (C3 typed) = `{ expr_kind:enum{threshold,region,boolean_and,callable_ref}, schema_ref:str, schema_hash:hex64, payload_canonical_json:str, required_belief_fields:[field_id] }` (extensible payload pinned by `schema_ref`+`schema_hash`, not a bare `obj`).
- **`progress_phase`** (C3) = `{ phase_id:str (**namespaced skill-local**, e.g. `"APPROACH_CABLE/descend"`; NOT a global G1..G6), progress:[0,1]|null }`.
- **`termination_classes`** = set⊆`{success,failure,timeout,invalid_state}` (non-empty).
- **`safe_interruption_checkpoints`** = `[checkpoint_id:str]` (may be empty).
- **`handoff`** = `SkillHandoffState{ handoff_state_id, schema_version:semver, producer{ SkillActionKey, outcome: TERMINAL{ terminal_class:enum{success,failure,timeout,invalid_state}; checkpoint_id:id|null } | INTERRUPT{ checkpoint_id:id; interrupt_reason:enum{planned_switch,event,safety_stabilized} } }, belief_ref{ value: canonical_belief_snapshot:json | ref_hash:hex64, t_obs:monotonic_s, ttl:s, confidence:[0,1], ood_flag:bool }, ownership{ contact:bool, resource:{schema_ref,schema_hash,payload_canonical_json}, control:{EE_L:bool,EE_R:bool,gripper_L:bool,gripper_R:bool} }, compatibility{ predicate_schema_ref:str, predicate_schema_hash:hex64, predicate_version:semver, next_owner:id } }` + `accepted_incoming_handoff_set:[handoff_state_id]`.
- transition status machine: `offer → accept+ack → commit | abort`; single-writer manager atomic `control_ownership` flip; `reject|abort|timeout ⇒ producer-retains + safe-stop`.
- **`duration_cost_distribution`** (C3 fields+units) = `{ dist_kind:enum{empirical,gaussian,unknown}, duration:{ mean_s:float, std_s:float, p50_s:float, p95_s:float }|null, cost:{ mean:float, std:float, p50:float, p95:float, cost_units:enum{time_s, energy_j, normalized_unitless} }|null }` (null = unmodeled, LL-WMF gap).
- **`resource_requirements`** = `{ control_ownership:{EE_L:bool,EE_R:bool,gripper_L:bool,gripper_R:bool}, compute:enum{fast_path,slow_path} }`.
- **`fail_closed_action`** = enum`{re_observe, safe_stop, handback_to_owner}`.
- **`policy_version`** = str (semver | `"ckpt:"+policy_weight_hash`) · **`freshness`** = `{ max_staleness_s:float|null }` · **`support_boundary`** = `{ region_ref:str|null, in_support_predicate:{schema_ref,schema_hash}|null }`.
- **`admissibility`** = `{ identity_pinned:bool, contract_conformant:bool, offline_orchestration_admissible:false, closed_loop_admissible:false }` (validated, C4).

**Fail-close conditions (C3) — any of these ⇒ `contract_conformant=false`**: `obs_action_schema.field_semantics=UNRESOLVED` (B3) · unresolved
`initiation_predicate` schema (`schema_ref`/`schema_hash` absent or unverifiable) · missing `required_belief_confidence` · `freshness.max_staleness_s=null`
· `support_boundary` with **neither** `region_ref` **nor** `in_support_predicate`. **Rule**: any unknown key or missing required field ⇒ **reject**.

## §8. D1-G — harness (C1: no line numbers; else unchanged from v4.1)
Controls carried from v4.1 (R3 `source_closure_sha256` enumerated + fail-closed; C2/C4/C6; unknown/missing ⇒ reject) — with **no numeric line
references** anywhere. New fail-close checks (C3, §3b) are added as harness assertions: unresolved-initiation-schema / missing-required_belief_confidence
/ null-freshness / boundary-neither ⇒ `contract_conformant=false` (each a negative control that must come out differently on a broken contract).

## Next
bank v4.1.1 → **pN v4.1.1 readback**. code GO CLOSED; no `[CHANGE]`; no schema recovery; rulings unchanged.
