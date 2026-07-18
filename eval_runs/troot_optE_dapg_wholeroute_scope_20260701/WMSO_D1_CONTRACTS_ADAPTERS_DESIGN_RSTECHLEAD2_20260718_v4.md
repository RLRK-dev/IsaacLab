# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO **D1 Skill contracts + adapters** — DESIGN draft **v4** (folds pN step-4 readback B1–B6; decisions RULED)

- supersedes **v3** (`3fd093e70c`, sha256 `4ed5ab582ccb…`). node `T-WMSO`; author `w2:pQ`; verify `w2:pN`; custody `w2:p6`. prepared_at **2026-07-19 ~00:48 JST**.
- ⛔ **DESIGN-ONLY; no code/impl/run/gate PASS.** GO for code stays **CLOSED until pN v4 readback** (pN step-4, 00:42).
- **pN step-4 readback on v3** = **DECISIONS RULED / IMPL HOLD (B1–B6)** + **code-path FROZEN**. This v4 folds B1–B6 and returns for readback.
- **hashes below are pQ-verified** (`sha256sum`, match pN): `a49b6342`(final `model_best.pt`) · `d280ea97`(`summary.json`) · `065c4581`(base) · `7d804486`(`model_9.pt`).

## Rulings folded (pN step-4)
- **DECISION #1 = A (adopted WITH CAVEAT)**: APPROACH_CABLE BC+RL pins present bytes + `RECORDED_PATH_CONFIG_COLOCATION`; emit
  `train_time_crypto_bound=false`, `association_strength=RECORDED_PATH_CONFIG_COLOCATION`; **never claim crypto-verified lineage; no retrain**.
- **DECISION #2 = RSL-RL INSERT_INTO_CLIP** `model_9.pt` (maps to a canonical skill; residual-PPO rejected = historical residual grasp, not a clean
  canonical exemplar). **Structural-only does NOT suffice for `contract_conformant` or gate①**: record `identity_pinned=true`,
  `field_semantics=UNRESOLVED`, `contract_conformant=false`, until an authoritative training-env schema pins field order/unit/frame/action scaling.

## Fold map (pN B1–B6 IMPL-HOLD blockers)
| id | blocker | fix in v4 |
|---|---|---|
| **B1** | shortened paths + `<named>` placeholders; CLAMP/AERIAL need exact artifact or INADMISSIBLE_AMBIGUOUS; WAIT stale line :945 | §3: **full repo-relative paths**; CLAMP+AERIAL = **INADMISSIBLE_AMBIGUOUS**; WAIT keyed by **qualname** (`_run_wait`, def `:1216`; **never line**) |
| **B2** | freeze `finetune_cfg_hash` derivation; present ≠ train-time | §5: canonical sorted-JSON projection of enumerated `summary.json` keys + **retain raw summary sha** `d280ea97` separately |
| **B3** | learned schemas missing on BOTH exemplars; generic shape acceptance must fail closed | §4/§6: schema-bind from authoritative training-env **or fail-closed** (`contract_conformant=false`); no generic shape acceptance |
| **B4** | fragile transitive source-slice closure | §3: conservative identity = `skill_id + callable_qualname + whole-file sha256 + task_config sha256` (SCRIPTED); whole `routing_orchestrator.py` + wait-config (WAIT) |
| **B5** | belief map must be declarative, not runtime `.py` | §4/§10: `belief_map_design.json` (declarative, design-only); runtime grounding = D2 |
| **B6** | instantiate exact contract enums/types/required-vs-nullable + status transitions (D0 §B/§E, TERMINAL\|INTERRUPT); unknown/missing rejects; correct §9 | new **§3b** concrete instantiation; §9 corrected (#1=A alone ≠ exit#3 PASS while schemas unresolved) |

## §1. FACTUAL inventory (unchanged; hashes now pinned + pQ-verified)
Same as v3 §1. Pinned identities: APPROACH final `model_best.pt=a49b6342…`, `summary.json=d280ea97…`, base `base_model_mixed_20260404_190016.pt=065c4581…`;
INSERT-RL-only `model_9.pt=7d804486…`. (BC route `ckpt_sha256=e165a370…`; DAPG 0 sha256; `d3_baseline.json`=residual_ppo only.)

## §2. D1-A — canonical `skill_id` reconciliation (unchanged)
Canonical = `SkillName`(9). `SkillType`(7) `clamp*`→CLAMP{side}. `bimanual_*`(6) = ORPHAN/out-of-route-scope.

## §3. D1-B — per-skill identity (B1 exact paths + INADMISSIBLE_AMBIGUOUS; B4 conservative identity; qualname keys)
| # | skill_id | kind | exact artifact (full repo-relative) | identity | status |
|---|---|---|---|---|---|
| 1 | APPROACH_CABLE | LEARNED (BC+RL) | `thread_isaac_lab/data/rl_approach_cable_A_w256_20260409_073409/model_best.pt` (a49b6342) | triad §5 (final a49b6342 / summary d280ea97 / base 065c4581); `train_time_crypto_bound=false` | `identity_pinned=true`, **`contract_conformant=false`** (schema §4/B3), exit HOLD |
| 2 | CLAMP{side} | LEARNED | — no exact artifact selected | — | ⛔ **INADMISSIBLE_AMBIGUOUS** (B1) |
| 3 | INSERT_INTO_CLIP | LEARNED (RL-only) | `thread_isaac_lab/logs/rsl_rl/insert_clip_20260325_235722/model_9.pt` (7d804486) | ckpt hash | `identity_pinned=true`, `field_semantics=UNRESOLVED`, **`contract_conformant=false`** (§6), exit HOLD |
| 4 | UNCLAMP | LEARNED | ABSENT (`data/rl_unclamp_cache/*.npz` only, no `.pt`) | — | ⛔ inadmissible (no policy; route uses scripted HALF_UNCLAMP_RELEASE) |
| 5 | AERIAL_REGRASP | LEARNED | — no exact artifact selected | — | ⛔ **INADMISSIBLE_AMBIGUOUS** (B1) |
| 6 | TRANSPORT | SCRIPTED | `scripted_skills.py::transport_to_clip` | `skill_id`+`callable_qualname`+`sha256(scripted_skills.py)`+`sha256(task_config.py)` (B4) | pinnable (compute); `contract_conformant` pending §3b |
| 7 | RECLAMP_L | SCRIPTED | `scripted_skills.py::reclamp_left` | same (B4), qualname-keyed | pinnable |
| 8 | HALF_UNCLAMP_RELEASE | SCRIPTED | `scripted_skills.py::half_unclamp_release` | same (B4), qualname-keyed | pinnable |
| 9 | CLIP_CONFIRM | WAIT | `routing_orchestrator.py::_run_wait` (def `:1216`; **key by qualname**, B1) | `skill_id`+`qualname`+`sha256(routing_orchestrator.py)`+`wait_config` (B4) | pinnable |

**Admissible-for-identity D1 set** = {APPROACH (BC+RL), INSERT (RL-only), 3×SCRIPTED, WAIT}. **INADMISSIBLE** = CLAMP+AERIAL (ambiguous), UNCLAMP (absent).

## §3b. Concrete contract instantiation (B6 — instantiates D0 §B/§E; unknown/missing ⇒ reject)
`SkillLifecycleContract` (required unless (nullable)):
- `skill_id`: enum(9) · `schema_version`: semver · `policy_family`: enum{BC, BC+RL, PPO, DAPG, SCRIPTED, WAIT}
- `executable_identity`: tagged union on `kind`:
  - `LEARNED{ policy_weight_hash, lineage{ family, base_ckpt_hash(nullable for RL-only), finetune_cfg_hash(nullable), final_policy_hash }, train_time_crypto_bound: bool, association_strength: enum{CRYPTO_TRAIN_TIME_BOUND, RECORDED_PATH_CONFIG_COLOCATION} }`
  - `SCRIPTED{ skill_id, callable_qualname, source_file_sha256, config_sha256 }` · `WAIT{ skill_id, callable_qualname, source_file_sha256, wait_config_sha256 }`
- `obs_action_schema`: `{ obs_fields[], action_fields[], field_semantics: enum{RESOLVED, UNRESOLVED} }` — **`UNRESOLVED` ⇒ `contract_conformant=false`** (B3; no generic shape acceptance)
- `initiation_predicate` + `required_belief_confidence:[0,1]` · `termination_classes`: set⊆{success,failure,timeout,invalid_state}
- `progress_phase` + `safe_interruption_checkpoints[]`
- `handoff`: `SkillHandoffState{ handoff_state_id, schema_version, producer{ SkillActionKey, outcome: TERMINAL{ terminal_class∈{success,failure,timeout,invalid_state}; checkpoint_id(nullable) } | INTERRUPT{ checkpoint_id(mandatory); interrupt_reason∈{planned_switch,event,safety_stabilized} } }, belief_ref{ ref, t_obs, ttl, confidence, ood_flag }, ownership{ contact, resource, control(per-EE EE_L/EE_R + gripper) }, compatibility{ predicate, predicate_version, next_owner } }` + `accepted_incoming_handoff_set`
- transition status machine (D0 §E): `offer → accept+ack → commit | abort`; single-writer manager atomic `control_ownership` flip; `reject|abort|timeout ⇒ producer-retains + safe-stop`
- `duration_cost_distribution` + `resource_requirements` · `recovery_rollback_target` + `fail_closed_action`
- `policy_version` + `freshness` + `support_boundary`
- `admissibility`: `{ identity_pinned, contract_conformant, offline_orchestration_admissible=false, closed_loop_admissible=false }` (validated field, C4)
**Rule**: any unknown key or missing required field ⇒ **reject** (fail-closed).

## §4. D1-C — adapters (B3 schema fail-closed; B5 declarative belief map)
**(1) static policy adapter — IMPLEMENTED**: `(ExecutableIdentity + declared obs/action schema) → canonical contract repr`; tests =
canonicalization/schema/determinism; no round-trip. **B3**: a learned skill's obs/action schema must be **bound** (field order/unit/frame/action
scaling) from an **authoritative training-env source**; **generic shape acceptance (dim counts only) fails closed** ⇒ `field_semantics=UNRESOLVED`,
`contract_conformant=false`. Both exemplars (APPROACH 42D→12D, INSERT 10D→3D) currently **UNRESOLVED** ⇒ schema-recovery is the D1 completion gate.
**(2) belief map — DESIGN-ONLY declarative (B5)**: frozen as **`belief_map_design.json`** (surface-B 62D `newton_route_env.py:1532-1584` complete
0–61 partition, all `PRIVILEGED_SIM`/`CONST`⇒`prod_admissible=false`; surface-C subset). **No runtime `belief_map.py`.** Runtime grounding = **D2**.
**(3) D2 runtime grounding — OUT of D1.** **C7**: O0 inherits a raw↔canonical inverse-binding obligation (flagged, not built at D1).

## §5. D1-D — BC+RL triad (DECISION #1=A; B2 hash derivation)
APPROACH exemplar: final `model_best.pt`=a49b6342, `summary.json`=d280ea97, base=065c4581. **B2 finetune_cfg_hash** =
`sha256(canonical_sorted_json({base_model, lora_rank, dapg.demos, dapg.alpha_init, dapg.alpha_min, dapg.bc_losses}))` — the enumerated projection —
**AND** retain `raw_summary_sha256=d280ea97` separately. `base_ckpt_hash=065c4581` (present-time), `final_policy_hash=a49b6342` (present-time).
**All are present-time hashes, NOT train-time** ⇒ `train_time_crypto_bound=false`, `association_strength=RECORDED_PATH_CONFIG_COLOCATION`; never
claim crypto-verified lineage; ⛔ no retrain. exit#3 = HOLD until schema (B3/§9).

## §6. D1-E — RL-only (DECISION #2)
Exemplar = `insert_clip .../model_9.pt`=7d804486 (canonical-skill mapped). residual-PPO **rejected** (historical residual grasp phase, not a clean
canonical exemplar). shapes 10D→3D only ⇒ `identity_pinned=true`, `field_semantics=UNRESOLVED`, `contract_conformant=false`, offline/live=false, until
training-env schema pins field order/unit/frame/action scaling. **structural-only ≠ gate① PASS**; D1 exit HOLD if schema unrecovered.

## §7. D1-F — 4-axis status (per-skill, post-ruling)
| skill | identity_pinned | contract_conformant | offline(O0) | live(V0) |
|---|---|---|---|---|
| APPROACH_CABLE (BC+RL) | true (a49b6342) | **false** (schema UNRESOLVED, B3) | false | false |
| INSERT_INTO_CLIP (RL-only) | true (7d804486) | **false** (field_semantics UNRESOLVED) | false | false |
| CLAMP / AERIAL_REGRASP | — | — | false | false | (INADMISSIBLE_AMBIGUOUS) |
| UNCLAMP | — | — | false | false | (inadmissible: absent) |
| TRANSPORT/RECLAMP_L/HALF_UNCLAMP_RELEASE/CLIP_CONFIRM | true (on compute) | pending §3b | false | false |
Authority axes are a **validated field** (C4): every emitted contract offline=false ∧ live=false; hand-built true ⇒ rejected.

## §8. D1-G — harness (C2/C4/C6 + B4 identity + B6 fail-closed)
Controls (must differ on broken input): missing/changed hash ⇒ reject · different `skill_id`+`callable_qualname`, same source file ⇒ **different
key** (B4) · same-name-diff-lineage ⇒ different key · legit alias (`clamp_r`→CLAMP) ⇒ canonicalize; genuine duplicate/unknown `skill_id` ⇒ reject
(C6) · `schema_version` mismatch ⇒ reject · `PRIVILEGED_SIM ∧ prod_admissible=true` ⇒ reject · `field_semantics=UNRESOLVED` ⇒ `contract_conformant=false`
(no generic shape acceptance, B3) · `TERMINAL`/`INTERRUPT` missing-mandatory ⇒ reject · empty/absent/summary-only-no-`model_best` ⇒ inadmissible ·
**authority**: positive (all emitted offline∧live=false) + negative (hand-built true ⇒ reject) · **unknown key / missing required ⇒ reject** (B6).
**manifest** `skill_contracts_manifest.json`: repo/as-read SHA + dirty-state + **full-path** artifact/config/source closure + pre/post hash bracket + `added`/`missing`/`changed=[]`.

## §9. D1 exit criteria (B6 corrected)
(1) contract + adapter + all §8 controls pass; (2) identity-pinned over the full 9-skill set (admissible = APPROACH+INSERT+3 scripted+wait; CLAMP/AERIAL
INADMISSIBLE_AMBIGUOUS; UNCLAMP inadmissible — **no silent gap**); (3) ≥2 lineages incl BC+RL (APPROACH) + ≥1 RL-only (INSERT), **both currently
`contract_conformant=false`**; (4) authority hard-false (validated); (5) no premature claim. **B6 correction**: **DECISION #1=A alone does NOT make
exit#3 PASS while the exemplar schemas are UNRESOLVED** ⇒ **D1 exit = HOLD**. **Remaining D1 completion gate = authoritative training-env schema
recovery** for APPROACH (42D→12D) + INSERT (10D→3D); unrecovered ⇒ HOLD (honest). C7: O0 inherits inverse-binding.

## §10. Code-path FROZEN (pN step-4; GO CLOSED until v4 readback)
**added (only)**: `thread_isaac_lab/wmso/__init__.py`, `wmso/d1/__init__.py`, `wmso/d1/contracts.py`, `wmso/d1/identity.py`,
`wmso/d1/policy_adapter.py`, `wmso/d1/harness.py`, `wmso/d1/skill_contracts_manifest.json`, `wmso/d1/belief_map_design.json`,
`wmso/d1/tests/test_contracts.py`, `test_identity.py`, `test_policy_adapter.py`, `test_harness.py`. **changed = ∅**. New `.py` need **2026 SPDX**;
**no new dependency**. Design/evidence records = explicit-path, outside code freeze.

## §11. Boundaries + next
⛔ DESIGN-ONLY; RS71 §0 invariants untouched; `T-WMSO-SDM` not created (M0); non-mixing held; offline+live false; no retrain.
**Next**: bank v4 → **pN v4 readback** (design + frozen path). GO for code CLOSED until that readback. No `[CHANGE]` yet.
