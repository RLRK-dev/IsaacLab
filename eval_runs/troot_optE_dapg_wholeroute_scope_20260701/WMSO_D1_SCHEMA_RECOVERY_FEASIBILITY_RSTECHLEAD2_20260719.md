# [RS-TECH-LEAD2 (w2:pQ) → Rs / OPS-SUP-CODEX] WMSO D1-exit **schema-recovery feasibility** — INVESTIGATION record

- Node `T-WMSO` (parent `T-ROOT-RS-TECH-LEAD2`). Chunk = **D1-exit training-env schema recovery**, Rs-authorized ("a", 2026-07-19).
- **INVESTIGATION / read-only. No code change, no design change, no run.** Written 2026-07-19 06:32 JST.
- Question: can `obs_action_schema.field_semantics` be moved `UNRESOLVED → RESOLVED` from an **authoritative training-env source** for the two D1 learned exemplars? (This is the sole open fail-close leg — `wmso/d1/harness.py:84-85`; contract shape `contracts.py:145-181`; design v4.1.1 doc:42/55.)

## Verdict (short)
| Exemplar | Trained | Policy dims | field_semantics RESOLVED? | Authoritative source status |
|---|---|---|---|---|
| **APPROACH_CABLE** (BC+RL) | 2026-04-09 | obs 42D / act 12D | **ACHIEVABLE** (best-surviving; pN adjudicates) | surviving direct-lineage env in git + mujoco port + policy-dim + run-record all agree |
| **INSERT_INTO_CLIP** = `model_9` (RL-only, DECISION#2) | 2026-03-25 | obs 10D / act 3D | **NOT achievable on-machine** | training-time source destroyed; every surviving artifact is dims-only |

**Consequence:** D1 exit requires BOTH learned exemplars conformant. APPROACH is recoverable; `model_9`'s schema is not. So D1 exit cannot be closed by schema recovery **as the exemplar set currently stands**. This is a decision fork (below), not a pure blocker — INSERT has schema-recoverable *later* exemplars.

## Evidence

### Timeline (load-bearing)
- THREAD python source **first git-tracked** `0fca80389b` = **2026-06-07** — i.e. **~2 months AFTER both training dates** (INSERT 03-25, APPROACH 04-09). Everything before is untracked.
- env6 Newton-VBD track **deleted** `13f3d55c0a` = 2026-06-25; mujoco ApproachCable port **added** `780593d523` = 2026-06-26.
- Both run dirs' `git/` provenance subdirs are **empty** (no training-time commit pinned).

### APPROACH_CABLE — RESOLVED achievable
- Surviving direct-lineage env `git show 0fca80389b:thread_isaac_lab/envs/newton_approach_cable_env.py` = **obs 42D / act 12D**, field-by-field layout documented (hist doc:10-11, code L135/L151).
- Current mujoco port `thread_isaac_lab/envs/newton_approach_cable_mujoco_env.py:22-42` documents the **identical** 42D obs order + 12D action, assembly matches (`:845-858`).
- Base policy `base_model_mixed_20260404_190016.pt`: `actor.0.weight (128,42)`, `actor.last (12,128)` → 42/12. Final is a LoRA rank-8 finetune (summary.json `lora_rank:8`), same dims.
- Run-record action scaling corroborated: summary.json `env_config` `POS_ACTION_SCALE=0.015 / ROT_ACTION_SCALE=0.05` == current source `:230-231`.
- **Caveat (no over-claim):** the surviving env is 2026-06-07 (2 months post-training, untracked drift between), and the mujoco port explicitly deviates in clamp-pos computation (`extract_clamp_pose`→`clamp_pos_ko`, `:795-797`). So the binding is **"best-surviving authoritative env in the direct lineage"**, not the *exact* training-time source. Whether that clears the RESOLVED bar (binary enum) is a **pN design-gate judgment**.

### INSERT_INTO_CLIP `model_9` — NOT recoverable on-machine (fix-first exhausted)
- Checkpoint `logs/rsl_rl/insert_clip_20260325_235722/model_9.pt`: `actor.0.weight (64,10)` / `actor.4.weight (3,64)` → confirms 10D/3D, but **no obs normalizer / no metadata** (keys: model_state_dict, optimizer_state_dict, iter, infos=None). Dims only.
- Git-recoverable insert env (`newton_insert_clip_env.py`) at both earliest-tracked (0fca80389b) and pre-delete (13f3d55c0a^) = **45D obs / 12D act** — a *different* schema. The 10D/3D env predates tracking and is **absent from git entirely**.
- Earliest surviving insert demo npz = 2026-04-02, already **42D/12D** (`data/bc_demos/insert_clip_demos*.npz`). No 10D/3D-era demo survives (model_9 predates all of them).
- Training tfevents = `Train/mean_reward` scalars only; no hparam/config text.
- No repo-external March source (worktrees all post-June; eval_runs has only unrelated kinematic-retention insert-pin scripts).
- The **only** surviving facts about `model_9`'s schema are obs_dim=10, action_dim=3. Field order / unit / frame / action-scaling are gone.

### Constructive alternative — INSERT has schema-recoverable later exemplars
INSERT policy schema evolved: **10D/3D** (03-25/26) → 12D/3D → 12D/4D → 15D/6D (03-27) → **42D/12D** (04-02..04, many runs e.g. `data/rl_insert_clip_w256_20260403_003017` = 62 models) → **45D/12D** (04-06+, e.g. `rl_insert_clip_approach_w256_20260409_191756`). The 42D/12D and 45D/12D eras have **git-surviving env schemas**. So an INSERT exemplar picked from those eras would be schema-recoverable **without** a charter change or external archaeology — but it **reopens DECISION#2** (banked Rs/pN ruling that chose `model_9` as RL-only after rejecting residual PPO).

## Decision fork (INSERT) — Rs
- **(E) Revisit DECISION#2** → pick a schema-recoverable later insert exemplar (42D/12D or 45D/12D). No charter change, no external hunt. Reopens a banked ruling → Rs + pN. *[recommended]*
- **(A) External archaeology** for the exact 2026-03-25 10D/3D source (off-machine backup / other machine) — only if `model_9` must be retained. Needs Rs's backup pointer.
- **(B) Redefine D1 exit** to accept `model_9` as identity-pinned + permanently-schema-lost, excluded from the conformant-required set (like CLAMP/AERIAL/UNCLAMP). Charter/exit-criterion change → Rs專権 + pN.
- (C non-authoritative reconstruction = false-RESOLVED, pN would reject; D retrain = contradicts no-retrain decision#1/#2. Both dispreferred.)

## Recommendation / next
- **APPROACH:** proceed with the RESOLVED-binding design (authorized, achievable) → pN design gate → implement. Does not depend on the INSERT fork.
- **INSERT:** (E). Await Rs disposition before designing an INSERT binding.
- ⛔ No implementation until the pN design gate; ⛔ D1 exit stays HOLD until both legs land.
