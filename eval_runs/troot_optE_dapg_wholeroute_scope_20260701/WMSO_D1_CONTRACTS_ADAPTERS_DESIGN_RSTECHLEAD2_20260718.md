# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO **D1 Skill contracts + adapters** — DESIGN draft **v1** (step-2)

- node `T-WMSO`; author `w2:pQ`; independent verify `w2:pN`; custody `w2:p6`. prepared_at **2026-07-18 ~23:58 JST**.
- **basis / authorization**: D1 scope prereg **v3 = pN SCOPE CONCUR** (`d64298a62b`, verdict 23:21; LEDGER:41). CONCUR unlocked **only §0
  step-2 = contracts+adapters DESIGN AUTHORING**. This is that deliverable.
- ⛔ **DESIGN-ONLY. No code, no impl, no run, no gate PASS.** code/impl remain locked until the §0-step-4 **implementation-GO gate** (pN design
  readback + explicit implementation GO + exact added/changed path manifest). Even this draft + a later `/pre-check` do **not** unlock `[CHANGE]`.
- **carry conditions honored (pN)**: BC+RL triad-association absent ⇒ `hash_unpinned`/`inadmissible` + exit#3 HOLD; RL-only unusable ⇒ gate①
  unresolved; `offline_orchestration_admissible` (O0) + `closed_loop_admissible` (V0) both **false** at D1. ⛔ no training to manufacture a hash.
- **charter §5 D1** (`WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md:124`): deliverable = *adapters for BC+RL and at least one other policy lineage*;
  exit = *contract tests and hash-pinned lineage*.

## §1. FACTUAL on-disk inventory (this draft's basis; independently verifiable at the cited paths; pivotal rows pQ-spot-verified)

| family | artifact(s) | lineage/identity record on disk | hash-pin status |
|---|---|---|---|
| **BC route (surface-C)** | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/{b1p_train,b1p_train_e2000,b2_cpD/bc,dq7_ii_*/bc}/policy_abs*.pt` | `policy_abs_sidecar.json` (**`ckpt_sha256`**, `dataset_sha256`, `action_repr`) + `runner_verdict.json` (`policy_sha256`) | ✅ **content-hash identity RECORDED** (pQ-verified `ckpt_sha256=e165a370…`; BC-only, no finetune) |
| **BC base (multi-task)** | `thread_isaac_lab/data/bc_checkpoints/base_model_ac_ar_v25v11*.pt`; `data/base_model_mixed_*.pt`, `base_model_ar_v30_best.pt` | **ABSENT** (`train_base_model.py:185-188` writes bare `model_state_dict`, no sidecar) | hashable, but **no recorded hash** |
| **BC+RL / DAPG / LoRA** | `data/rl_approach_cable_A_w256_2026040*/`, `rl_aerial_regrasp_w256_*/`, `rl_insert_clip_w256_20260405_132000/`, `rl_grip_clamp_w256_20260409_2146*/` → `summary.json` + co-located `model_best.pt` | `summary.json` (`train_common.py:551-594`): **`base_model`=PATH-string** (:554), `lora_rank` (:555), `dapg.demos`=PATH (:572); final = co-located `model_best.pt` (:530). **NO sha256 of base or final** (pQ-verified: 0 sha256 keys) | ⚠ **association = path+config+co-location ONLY; base unhashed; final not pre-hashed → no crypto triad** |
| **pure RL — residual PPO** | `data/residual_ppo/ckpt_final.pt`, `data/residual_ppo_d4v2/ckpt_final.pt` (+`ckpt_iter*`) | `train_log.json` (per-iter PPO metrics; v_loss~60540@iter0 ⇒ from-scratch, not BC-init) + `d3_baseline.json` (scripted baseline it is residual to) | ✅ ckpt hashable; ⚠ **no algo/BC-init config**; **residual-on-baseline** (identity incl. baseline) |
| **pure RL — RSL-RL** | `thread_isaac_lab/logs/rsl_rl/insert_clip_20260325_235722/model_*.pt` | **ABSENT** (tfevents + empty `git/` only); stock `rsl_rl/train.py` (on-policy PPO) | ✅ ckpt hashable; ⚠ **no config record** |
| **"world model"** | `thread_isaac_lab/checkpoints/world_model_dual_arm/phase{1,2}_best.pt` | tfevents only; `train_wm_phase1.py` = supervised autoencoder | ❌ **NOT an RL policy** — excluded from RL-only |
| **scripted + wait** | `skills/step_table.py`, `skills/scripted_skills.py`, `orchestrator/routing_orchestrator.py`; config `configs/task_config.py` | **ABSENT** (no `source_hash`/`config_hash` emitted) | derivable (source+config hashable); **must be computed** |

**Bottom line:** only **BC-only route** carries a recorded content-hash identity. **BC+RL/DAPG lineage is path+config+co-location, NOT crypto-bound**
(base unhashed). Pure-RL (`residual_ppo`, `rsl_rl/insert_clip`) is genuinely online-RL, hashable, thin/absent config. Scripted/wait pinnable-but-uncomputed.

## §2. D1-A — canonical `skill_id` reconciliation

**Canonical set = `SkillName` (9)** (`step_table.py:35-51`, the route driver): RL {APPROACH_CABLE, CLAMP, INSERT_INTO_CLIP, UNCLAMP,
AERIAL_REGRASP}, SCRIPTED {TRANSPORT, RECLAMP_L, HALF_UNCLAMP_RELEASE}, WAIT {CLIP_CONFIRM}.

| source vocab | maps to canonical | note |
|---|---|---|
| `SkillType` (7, `skill_adapter.py:45-58`) | `approach_cable→APPROACH_CABLE`; `clamp`/`clamp_r`/`clamp_l`→**CLAMP** (per-arm variant discriminant, not new skills); `insert_into_clip→INSERT_INTO_CLIP`; `unclamp→UNCLAMP`; `aerial_regrasp→AERIAL_REGRASP` | RL-only vocab; **CLAMP 1↔3 alias** (base/R/L); scripted absent by design (orchestrator-dispatched) |
| `bimanual_*` (6, `skill_adapter_with_prediction.py:150-157`) | `{reach,grasp,lift,transport,hang,release}` = **SEPARATE WM+PPO stack** | ⚠ **NOT the route skills** — distinct decomposition (D0 §C/§H); flagged **ORPHAN / out-of-route-scope**, not merged into the canonical set |

**Design rule**: canonical `skill_id` is the stable enum key (never a positional index); `clamp_r`/`clamp_l` become `CLAMP{side∈{R,L}}` variant discriminants under one `skill_id`; `bimanual_*` is recorded as a separate vocabulary, not a canonical route skill.

## §3. D1-B — per-skill `SkillLifecycleContract` + discriminated `ExecutableIdentity`

Contract fields (charter §3 `:82-96`; D0 §B `…DRAFT…:147-156`), instantiated per canonical skill: `skill_id`, `policy_family`, `SkillActionKey`
(with `ExecutableIdentity`), obs/action schema + `training_lineage`, `initiation_predicate` + `required_belief_confidence`, termination classes
{success,failure,timeout,invalid_state}, `progress_phase` + `safe_interruption_checkpoints`, `SkillHandoffState` + `accepted_incoming_handoff_set`,
`duration_cost_distribution` + `resource_requirements`, `recovery_rollback_target` + `fail_closed_action`, `policy_version/freshness/support_boundary`.

**`ExecutableIdentity` discriminant per canonical skill** (kind + how identity is pinned):
| skill_id | kind | policy source (this draft's candidate) | identity pin method |
|---|---|---|---|
| APPROACH_CABLE / AERIAL_REGRASP / INSERT_INTO_CLIP / CLAMP | `LEARNED` | BC+RL DAPG (`rl_*_w256_*/model_best.pt`) **or** BC-only route policy | §5 (BC+RL triad) / BC-route `ckpt_sha256` |
| (RL-only exemplar for gate①) | `LEARNED` | pure-RL `rsl_rl/insert_clip/model_*.pt` | checkpoint content-hash (§6) |
| TRANSPORT / RECLAMP_L / HALF_UNCLAMP_RELEASE | `SCRIPTED` | `scripted_skills.py` + `step_table.py` | `source_hash` + `config_hash` (task_config.py), computed by D1 |
| CLIP_CONFIRM | `WAIT` | `routing_orchestrator.py _run_wait:945` | `wait_config_hash` |

## §4. D1-C — adapters, boundary-SEPARATED (R1 held)

**(1) D1 policy adapter — IMPLEMENTED** (charter deliverable): a **static** transform
`(ExecutableIdentity + declared obs/action schema) → canonical SkillLifecycleContract representation` via **schema-bound payload
canonicalization** (canonical `field_id` mapping + unit/frame/provenance tagging of the *schema*). Delivered for **BC+RL** (§5) **+ ≥1 RL-only**
(§6). ⛔ does not ground belief, does not run a policy. **Tests = canonicalization correctness + schema-conformance + determinism** (identical
input schema ⇒ identical canonical output); **round-trip NOT claimed** (canonical→raw inverse undefined).

**(2) D1 per-dim A/B/C BeliefState map — DESIGN-ONLY** (a map, not a runtime encoder). Concrete for **surface-B 62D**
(`newton_route_env.py:1532-1584`, all `PRIVILEGED_SIM`/`CONST` ⇒ every field `prod_admissible=false`):
| canonical group | surface-B dims → field | frame/unit |
|---|---|---|
| **arms/EE** | [0:3] EE_R clamp-pt pos, [3:7] EE_R quat, [7] R finger, [8:11] EE_L pos, [11:15] EE_L quat, [15] L finger, [30:36] R ori/pos err, [36:42] L ori/pos err, [55:57] IK resid | world / EE; [m],[rad] |
| **cable** | [16:19] lane-matched seg target, [19:23] seg quat, [48] held-cable z, [57] crossing-x dev, [60:62] C1-retention (dx_c1,z_cross_c1) | world; [m] |
| **task/clip** | [23:26] C1 xy+z (CONST), [26:30] clip quat (CONST), [42:48] phase one-hot, [49] seated-seg dist, [50] within-phase progress, [51:53] next-clip xy (CONST), [53:55] R/L contact flags, [58:60] seat z-gap/lateral | world / dimensionless |
| **meta** | **NONE present** — no `t_obs`/`provenance`/`confidence`/`ood_flag` field on the current vector (D0 §A) ⇒ D1 map adds them as canonical-schema fields, `provenance=PRIVILEGED_SIM`, `validity=false` (fail-closed, no vision) |

Surface-C 25/27D (`route_demo_to_bc.py:301`) = a **subset** of the canonical fields (D0 §A:106); surface-A per-skill = per-skill subset. Full
per-dim A/C tables are D1-map appendices (design-only).

**(3) D2 runtime belief grounding — OUT of D1** (populating `value` from live/vision obs; vision UNWIRED).

## §5. D1-D — BC+RL lineage triad + association (⚠ the crux)

**FACTUAL**: for the April AC/AR/IC/grip LoRA runs, `summary.json` records `base_model`(path) + `lora_rank` + `dapg.demos`(path) +
co-located `model_best.pt` — a **run-specific training association**, but **NOT content-hash-bound**: no sha of base or final, and the base
(`base_model_mixed_20260404_190016.pt`, exists, 97665 B) was **unhashed at train-time**. Newer grip `_20260426_*` = `base_model:null`
(**DAPG-from-scratch ⇒ RL-only, not BC+RL**); newest `_134913` = `model_best.pt` with **no summary.json** (no lineage ⇒ inadmissible).

**DESIGN**: D1 content-hashes the three artifacts **as they exist today** — base (`base_model_mixed_*.pt`), config (`summary.json` + lora params),
final (`model_best.pt`) — and records `summary.json` as the run association. **Association strength = `RECORDED_PATH_CONFIG_COLOCATION`**, explicitly
**NOT `CRYPTO_TRAIN_TIME_BOUND`** (the base file today is not provably the base used then).

**exit#3 disposition (carry default = conservative)**: because the triad is **not** crypto-bound at train-time, the BC+RL lineage is
**`hash_unpinned` for exit purposes ⇒ BC+RL exit#3 = HOLD** (⛔ no re-training to manufacture the binding). Whether the recorded (non-crypto)
association + present-day content-hashes may be **accepted** as sufficient is **OPEN DECISION #1** (§9) for pN/Rs — the carry default holds it HOLD
until ruled otherwise. Classification by DAPG name/family alone remains **forbidden**; the pin is over the actual artifacts.

## §6. D1-E — RL-only + gate①

**FACTUAL**: genuine online-RL exists — `rsl_rl/insert_clip/model_*.pt` (standalone per-skill PPO; config ABSENT, tfevents only) and
`residual_ppo*/ckpt_final.pt` (from-scratch PPO; `train_log.json`+`d3_baseline.json`; **residual-on-scripted-baseline**). `world_model_*` =
supervised, excluded. **DESIGN**: RL-only exemplar = **`rsl_rl/insert_clip`** (cleanest standalone-RL semantics), pinned by **checkpoint
content-hash**; `residual_ppo` = alternative (more provenance, but identity must include its baseline `d3_baseline.json`). Both carry `config_record
= thin/ABSENT` (flagged in the contract). **gate①** = *BC+RL AND RL-only through one `SkillLifecycleContract`* — **demonstrated only when both pass
the one contract**, ⛔ **not PASS at design**; if the RL-only config-thinness makes it unusable in step-5 ⇒ **gate① unresolved, no PASS**.

## §7. D1-F — 4-axis status + per-skill assignment (R2 held)

Axes: `identity_pinned` · `contract_conformant` · `offline_orchestration_admissible` (O0 replay; **O0 ≠ closed-loop**) · `closed_loop_admissible`
(V0 live). **D1 may set true ONLY the first two; both authority axes are hard-false at D1.**

| skill / lineage | identity_pinned | contract_conformant | offline (O0) | live (V0) |
|---|---|---|---|---|
| BC-route (surface-C) | ✅ (`ckpt_sha256`) | pending harness | **false** | **false** |
| BC+RL DAPG (AC/AR/IC/grip April) | ⚠ **HOLD** (recorded-not-crypto, §5/OPEN#1) | pending | **false** | **false** |
| RL-only (`insert_clip`) | ✅ (ckpt hash) | pending | **false** | **false** |
| BC base (multi-task) | ⚠ external-hash only (no sidecar) | pending | **false** | **false** |
| Scripted / Wait | ✅ derivable (compute source+config hash) | pending | **false** | **false** |

**hard test**: no D1 artifact sets `offline_orchestration_admissible` or `closed_loop_admissible` true. `closed_loop_admissible` additionally needs
Gate-4 (skill_SR≥70%) + #18 + checkpoint/compatibility (all downstream, out of D1).

## §8. D1-G — contract-test harness spec

Negative controls (each must reject / behave fail-closed): missing/changed hash · same-name-different-lineage ⇒ different key · duplicate/alias
`skill_id` · `schema_version` mismatch · `PRIVILEGED_SIM ∧ prod_admissible=true` ⇒ reject · empty/absent checkpoint ⇒ `INTERRUPT` impossible /
inadmissible · `TERMINAL`/`INTERRUPT` missing-mandatory-field. **Input manifest** (per run): repo/as-read SHA + dirty-state + named
`artifacts`/`config`/`source` closure + pre/post hash bracket + explicit `added`/`missing`/`changed=[]`.

## §9. D1 exit criteria + OPEN DECISIONS

**exit** (charter §5:124): (1) contract + adapter (canonicalization/schema/determinism) + negative-control tests pass; (2) identity-pinned lineage —
BC+RL triad+association **or** exit#3 HOLD; non-pinnable = explicit `hash_unpinned`/reason; (3) ≥2 lineages incl BC+RL (triad) + ≥1 RL-only, else
gate① unresolved; (4) no authority flip (offline+live hard-false); (5) no premature claim.

- ⭐ **OPEN DECISION #1 (BC+RL hash-pinning strictness) — for pN readback + Rs**: the charter-required **BC+RL** lineage has a **recorded but
  non-crypto** association (summary.json path+config+co-location; base unhashed at train-time). Per the carry default it is **HOLD**. **Consequence**:
  if train-time crypto-binding is required, BC+RL exit#3 is **structurally unreachable in D1** (the only fixes are re-training with lineage
  recording = ⛔ out of scope, or accepting the recorded association). **Options**: **(A)** accept `RECORDED_PATH_CONFIG_COLOCATION` +
  present-day content-hashes as the BC+RL identity, with the caveat surfaced in the contract (D1 proceeds, exit#3 PASS-with-caveat); **(B)** require
  crypto-train-time binding ⇒ BC+RL stays `inadmissible`/exit#3 HOLD; D1 then delivers **BC-only + RL-only** adapters and the charter "BC+RL
  adapter" line is **partially unmet → escalate**. **Recommendation = A** (the association IS run-specific and recorded; present-day hashes pin the
  actual artifacts; the residual risk is documented) — but this is pN/Rs's ruling, not mine.
- **OPEN DECISION #2 (RL-only exemplar)**: `insert_clip` (no config) vs `residual_ppo` (residual-on-baseline, has train_log). Recommendation =
  `insert_clip` for cleanest RL-only semantics; flag `config_record=ABSENT`.

## §10. Proposed implementation surface (for the §0-step-4 freeze — NOT authorized here)

All **NEW**, additive; ⛔ **no change to any existing skill/env/orchestrator/production file** (read-only over existing artifacts). Proposed new
package `thread_isaac_lab/wmso/d1/`: `contracts.py` (schema types), `identity.py` (`ExecutableIdentity` + content-hash util reusing
`hashlib.sha256`), `policy_adapter.py` (static canonicalization), `belief_map.py` (per-dim A/B/C map data), `harness.py` (contract-test +
negative controls) + `tests/`. Exact `added`/`changed=[]` path manifest is frozen at the implementation-GO gate, not now.

## §11. Boundaries + next
⛔ DESIGN-ONLY; no code/run/gate PASS; RS71 §0 FOUNDATIONAL invariants untouched (this designs contracts *above* skills); `T-WMSO-SDM` not created
(M0); non-mixing with (d-b)/`T-WM` held; offline+live authority false; no training to manufacture a hash.
**Next**: `/pre-check` this design draft → bank → **pN design readback + OPEN DECISION #1/#2 ruling + implementation-GO + path-freeze** (step-4)
before any code.
