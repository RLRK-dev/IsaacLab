# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO **D1 Skill contracts + adapters** — DESIGN draft **v3** (folds pre-check re-check N1 + L1/L2)

- supersedes **v2** (`…_v2.md`) → **v1** (`cfbdbec94b`). node `T-WMSO`; author `w2:pQ`; verify `w2:pN`; custody `w2:p6`. prepared_at **2026-07-19 ~00:25 JST**.
- ⛔ **DESIGN-ONLY; no code/impl/run/gate PASS.** basis = D1 scope prereg **v3 CONCUR** (`d64298a62b`).
- **pre-check (step-3)**: v1 = **BLOCK** (C1 CRIT + C2–C4 HIGH + C5–C7 MED) → v2 folded all 7 → re-check = **WARN** (7/7 C-items **DISCHARGED**, no new
  critical/contradiction; **N1 HIGH** + L1/L2 LOW surfaced). This v3 folds **N1/L1/L2** (N1 pQ-verified on disk). verifier `a5ad370f4a3422156`.

## Fold map (re-check N1 + L1/L2)
| id | issue | fix (pQ-verified) |
|---|---|---|
| **N1** HIGH | INSERT_INTO_CLIP's named BC+RL path (`rl_insert_clip_w256_20260405_132000/model_best.pt`) is **dead**; **0/62** insert_clip runs have both `summary.json`+`model_best.pt`; §1 "co-located model_best" overstated for insert_clip | §3 row 3 INSERT_INTO_CLIP BC+RL = **inadmissible → RL-only**; BC+RL exemplar = **APPROACH_CABLE** (15/61 clean triad-finals, e.g. `…20260409_073409`); §1 corrected |
| **L1** LOW | per-callable source-slice hash closure undefined (shared-helper change wouldn't perturb key) | §3 note: closure = callable body + transitively-called **local** symbols in `scripted_skills.py` + referenced `task_config` constants |
| **L2** LOW | §1 residual row: `d3_baseline.json` only in `residual_ppo/`, not `d4v2/` | §1 corrected |

## §1. FACTUAL on-disk inventory (basis; pivotal rows pQ-spot-verified)
| family | artifact(s) | lineage/identity record | hash-pin status |
|---|---|---|---|
| **BC route (surface-C)** | `eval_runs/…/{b1p_train,…,dq7_ii_*/bc}/policy_abs*.pt` | `policy_abs_sidecar.json` (`ckpt_sha256`,`dataset_sha256`) + `runner_verdict.json` (`policy_sha256`) | ✅ recorded (`ckpt_sha256=e165a370…`) |
| **BC base (multi-task)** | `data/bc_checkpoints/*`, `data/base_model_mixed_*.pt`, `base_model_ar_v30_best.pt` | ABSENT (`train_base_model.py:185-188` bare state_dict) | hashable, no recorded hash |
| **BC+RL / DAPG / LoRA** | `data/rl_{approach_cable_A,aerial_regrasp,grip_clamp}_w256_*/summary.json` **+ co-located `model_best.pt`** (BOTH: approach **15/61**, aerial **12/97**, grip **3/19**; **insert_clip 0/62** ⇒ excepted, N1) | `summary.json`: `base_model`=PATH(:554), `lora_rank`(:555), `dapg.demos`(:572); **0 sha256** | ⚠ path+config+co-location; **no crypto triad**; base unhashed |
| **pure RL — residual PPO** | `data/residual_ppo/ckpt_final.pt` (+`d3_baseline.json`, v_loss 60540@iter0), `data/residual_ppo_d4v2/ckpt_final.pt` (`train_log.json` only, v_loss 582.6@iter0) | from-scratch (no BC-init); `d3_baseline.json` = **residual_ppo only** (L2) | ✅ hashable; no algo config; residual-on-baseline |
| **pure RL — RSL-RL** | `logs/rsl_rl/insert_clip_20260325_235722/model_0..9.pt` | ABSENT (tfevents + empty `git/`); stock `rsl_rl/train.py`; **no `model_best`, no obs schema** | ✅ hashable; no config/schema |
| **"world model"** | `checkpoints/world_model_dual_arm/phase{1,2}_best.pt` | `train_wm_phase1.py`=supervised AE | ❌ NOT RL — excluded |
| **scripted + wait** | `skills/scripted_skills.py` (`transport_to_clip:94`,`reclamp_left:219`,`half_unclamp_release:263`), `step_table.py`, `orchestrator/routing_orchestrator.py`; `configs/task_config.py` | ABSENT (no source/config hash) | derivable per-callable; must compute |

## §2. D1-A — canonical `skill_id` reconciliation
Canonical = `SkillName`(9, `step_table.py:35-51`). `SkillType`(7): `clamp`/`clamp_r`/`clamp_l`→**CLAMP{side}** (side = variant discriminant; one-policy-+side-input vs two-policies **resolved in §8 manifest**). `bimanual_*`(6) = separate WM+PPO stack, **ORPHAN / out-of-route-scope**.

## §3. D1-B — per-skill contract + `ExecutableIdentity` (full 9-skill; per-callable scripted; explicit-named-path)
**Selection rule (C5)**: LEARNED pinned policy = **EXPLICIT NAMED PATH** in the §8 manifest — **no auto-glob**; multiple candidates + none designated ⇒ **inadmissible (ambiguous)**; the named path must pass the §8 absent-checkpoint control (N1: a summary-only run with no `model_best` is **not** a valid triad-final).

| # | skill_id | kind | on-disk candidate (named in manifest) | identity pin | D1 status |
|---|---|---|---|---|---|
| 1 | APPROACH_CABLE | LEARNED | **BC+RL exemplar** `rl_approach_cable_A_w256_20260409_073409/model_best.pt` (base=`base_model_mixed_20260404_190016.pt`, lora_rank=8; **15 clean triad-finals**) | §5 triad | BC+RL → **HOLD** (§5) |
| 2 | CLAMP{side} | LEARNED | `rl_grip_clamp_w256_<named>/model_best.pt` (April BC+RL, **3 clean triad-finals**; `_20260426_*` null-base RL-only; `_134913` no summary⇒inadmissible) | §5 / ckpt hash | side-resolution + HOLD |
| 3 | INSERT_INTO_CLIP | LEARNED | **BC+RL = ⛔ inadmissible** (N1: 0/62 insert_clip runs have `summary.json`+`model_best` together — 13 summary-only, 7 best-only) → **RL-only** `logs/rsl_rl/insert_clip_*/model_<named>.pt` (§6) | RL-only ckpt hash | BC+RL inadmissible; RL-only (§6) |
| 4 | UNCLAMP | LEARNED | **ABSENT** — no `rl_unclamp_w256_*`; only `data/rl_unclamp_cache/*.npz` (no `.pt`) | — | ⛔ hash_unpinned / inadmissible (route uses scripted HALF_UNCLAMP_RELEASE) |
| 5 | AERIAL_REGRASP | LEARNED | BC+RL `rl_aerial_regrasp_w256_<named>/model_best.pt` (**12 clean triad-finals**; alt BC+RL exemplar) | §5 triad | BC+RL → HOLD (§5) |
| 6 | TRANSPORT | SCRIPTED | `scripted_skills.py::transport_to_clip:94` | `skill_id` + **per-callable source-slice** + `config_hash` | pinnable (compute) |
| 7 | RECLAMP_L | SCRIPTED | `scripted_skills.py::reclamp_left:219` | `skill_id` + per-callable slice + config | pinnable (compute) |
| 8 | HALF_UNCLAMP_RELEASE | SCRIPTED | `scripted_skills.py::half_unclamp_release:263` | `skill_id` + per-callable slice + config | pinnable (compute) |
| 9 | CLIP_CONFIRM | WAIT | `routing_orchestrator.py::_run_wait:945` | `wait_config_hash` | pinnable (compute) |
| — | (gate① RL-only exemplar) | LEARNED | `logs/rsl_rl/insert_clip_*/model_<named>.pt` (or `residual_ppo`) | ckpt hash | identity ✅; schema=§6 |

**C2 fix + L1 closure**: SCRIPTED identity = `skill_id` + **per-callable source slice** (the function body **+ its transitively-called local
symbols in `scripted_skills.py` + the `task_config` constants it references** — the closure, so a shared-helper edit **does** perturb the key) +
`config_hash`. 3 scripted skills ⇒ 3 distinct keys.

## §4. D1-C — adapters, boundary-separated (R1 held; C3/C7)
**(1) static policy adapter — IMPLEMENTED**: `(ExecutableIdentity + declared obs/action schema) → canonical contract repr`; tests =
canonicalization/schema/determinism; **no round-trip**. **C3 (RL-only schema)**: RL-only `insert_clip`/`residual_ppo` carry shapes but no field
semantics → source schema from the **training env** if the env↔checkpoint association is establishable, **else `field_semantics=UNRESOLVED`**
(identity-pin + shape-count only) ⇒ **gate① structurally demonstrable, field-semantics UNRESOLVED, no gate① PASS at D1**.
**(2) per-dim A/B/C belief map — DESIGN-ONLY** (surface-B 62D `newton_route_env.py:1532-1584` = complete 0–61 partition, all
`PRIVILEGED_SIM`/`CONST`⇒`prod_admissible=false`; surface-C 25/27D subset). **(3) D2 runtime grounding — OUT of D1.**
**C7**: canonicalization one-way; **O0 inherits a raw↔canonical inverse-binding obligation** (dispatches in raw action space) — flagged, not built at D1.

## §5. D1-D — BC+RL lineage triad (⚠ crux)
BC+RL exemplar = `rl_approach_cable_A_w256_20260409_073409` (**clean** triad-final: `summary.json` names base=`base_model_mixed_20260404_190016.pt`
+ lora_rank=8 + demos; `model_best.pt` = final; co-located). Association = **`RECORDED_PATH_CONFIG_COLOCATION`, NOT crypto-bound** (no sha of
base/final at train-time; base file exists today = 97665 B). **Carry default ⇒ BC+RL exit#3 = HOLD** (⛔ no re-training). INSERT_INTO_CLIP has **no**
clean triad (N1) ⇒ BC+RL inadmissible there. Acceptance of the recorded association = **OPEN DECISION #1** (§9).

## §6. D1-E — RL-only + gate① (C3 + N1)
Online-RL: `logs/rsl_rl/insert_clip_*` (also INSERT_INTO_CLIP's learned path now, N1), `residual_ppo`. Checkpoint-hashable; **no obs/action schema**
⇒ RL-only exemplar `insert_clip` = identity-pinned, `field_semantics=UNRESOLVED` unless env-sourced ⇒ **gate① structural-only, no PASS at D1**;
unrecoverable schema ⇒ gate① unresolved (honest, per carry).

## §7. D1-F — 4-axis status (R2; C4 validated field)
Axes: `identity_pinned` · `contract_conformant` · `offline_orchestration_admissible`(O0; ≠closed-loop) · `closed_loop_admissible`(V0). **D1 sets
only the first two; both authority axes hard-false as a VALIDATED field** (§8). Per-skill: BC-route ✅ · APPROACH/AERIAL/CLAMP BC+RL HOLD (§5) ·
INSERT_INTO_CLIP + gate①-exemplar RL-only identity ✅/schema-unresolved (§6) · UNCLAMP inadmissible · scripted/wait pinnable-on-compute. offline+live=false ∀.

## §8. D1-G — contract-test harness (C2/C4/C6)
- hash: missing/changed hash ⇒ reject · different `skill_id`, same source file ⇒ **different key** (per-callable, C2).
- identity: same-name-different-lineage ⇒ different key · **(C6)** legit alias (`clamp_r`→CLAMP) ⇒ canonicalize/pass; genuine duplicate or unknown `skill_id` ⇒ reject.
- schema: `schema_version` mismatch ⇒ reject · `PRIVILEGED_SIM ∧ prod_admissible=true` ⇒ reject · `TERMINAL`/`INTERRUPT` missing-mandatory ⇒ reject.
- artifact: empty/absent checkpoint (incl. **summary-only run with no `model_best`**, N1) ⇒ inadmissible / `INTERRUPT` impossible.
- **(C4) authority**: positive — every emitted contract `offline=false ∧ live=false`; negative — hand-built `offline/live=true` ⇒ **REJECTED**.
- **manifest**: repo/as-read SHA + dirty-state + **explicit named** artifact/config/source closure + pre/post hash bracket + `added`/`missing`/`changed=[]`.

## §9. D1 exit criteria + OPEN DECISIONS
exit: (1) contract + adapter + **all §8 controls incl authority** pass; (2) identity-pinned over the **full 9-skill set** (BC+RL triad *or* HOLD;
INSERT_INTO_CLIP BC+RL inadmissible→RL-only; UNCLAMP inadmissible; every non-pinnable = explicit reason — **no silent gap**); (3) ≥2 lineages incl
BC+RL (APPROACH/AERIAL/CLAMP, triad) + ≥1 RL-only, else gate① unresolved (§6); (4) authority hard-false (validated); (5) no premature claim. **C7**:
O0 inherits a raw↔canonical inverse-binding obligation (not built at D1).
- ⭐ **OPEN DECISION #1 (BC+RL hash strictness) — pN/Rs**: **A** accept `RECORDED_PATH_CONFIG_COLOCATION`+present-day hashes (exemplar =
  approach_cable `…073409`; D1 proceeds, exit#3 PASS-with-caveat) vs **B** require crypto-train-time binding (BC+RL inadmissible ⇒ charter "BC+RL
  adapter" partially unmet → escalate; fix = re-train = ⛔ out of scope). Rec = A. Carry default = HOLD until ruled.
- **OPEN DECISION #2 (RL-only exemplar + schema)**: `insert_clip` (rec) vs `residual_ppo`; both `field_semantics=UNRESOLVED` unless env-sourced ⇒
  decide whether gate① structural-only suffices for D1 or the training-env schema must be recovered.

## §10. Proposed implementation surface (for step-4 freeze — NOT authorized here)
NEW additive `thread_isaac_lab/wmso/d1/` (`contracts.py`, `identity.py` [sha256 + per-callable closure hash], `policy_adapter.py`, `belief_map.py`,
`harness.py`, `tests/`). ⛔ no change to existing skill/env/orchestrator/production files. O0 inverse-binding = downstream (non-D1). Exact
`added`/`changed=[]` frozen at the implementation-GO gate.

## §11. Boundaries + next
⛔ DESIGN-ONLY; RS71 §0 invariants untouched; `T-WMSO-SDM` not created (M0); non-mixing held; offline+live false; no training to make a hash.
**Next**: bank v3 → **pN design readback + OPEN#1/#2 ruling + implementation-GO + exact-path freeze** before any code.
