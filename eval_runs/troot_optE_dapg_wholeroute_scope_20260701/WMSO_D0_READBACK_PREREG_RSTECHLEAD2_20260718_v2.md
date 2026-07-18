# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO D0 pre-registered scope — **v2** (revised per pN HOLD B1–B4)

- supersedes: v1 `WMSO_D0_READBACK_PREREG_RSTECHLEAD2_20260718.md` (sha256 `9e6ad050…`)
- node: `T-ROOT-RS-TECH-LEAD2` (dev/design owner) → child `T-WMSO`; author `w2:pQ`; verifier `w2:pN`; custody `w2:p6`
- prepared_at: 2026-07-18 13:04 JST · repo HEAD `437ab293e7` · status: **read-only, pre-execution (nothing built)**
- pN verdict addressed: HOLD (2026-07-18 12:57 JST) — B1 CRITICAL, B2/B3 HIGH, B4 MED. pN-validated items
  (owner separation, D0 read-only, production/training/inference/closed-loop UNAUTHORIZED, factual/design
  separation, fail-closed approach, artifact-sha/HEAD pinning) are **retained unchanged** from v1 §A/§B.
- companion artifact: **frozen source manifest** `WMSO_D0_FROZEN_SOURCE_MANIFEST_20260718.tsv`
  (file sha256 `5c51eeb4c5027b3f5260d5d9cc15321abee3ecf235dd2354773322e937bb8236`,
  **aggregate hash `f462d023bc9b3af63319005973151698ab92a3ec8c889860c013ae5596e21626`**).

v1 §A (readback) and §B (boundaries) stand. This v2 replaces v1 §C/§D with a hardened provenance,
closure, charter-coverage, and fail-closed contract.

---

## B1 (CRITICAL) — as-read provenance on a dirty/shared tree

**Finding that forces this:** at HEAD `437ab293e7` the working tree has **3239 porcelain entries**, and
**21 of the 47 sources in the D0 closure are dirty (`M`)** vs HEAD — including the centerpiece
`orchestrator/routing_orchestrator.py`, `models/base_policy.py`, `skill_adapter_with_prediction.py`,
`skills/step_table.py`, `training/dual_arm_skill_rewards.py`, `models/world_model_4cam.py`,
`visual_encoder.py`, `obs_builder.py`, `obs_collector.py`, `safety_envelope.py`, `fallback_guard.py`,
`route_executor`-adjacent envs. **Therefore git commit/blob (HEAD) provenance does NOT fix as-read
content.** Only the working-tree content hash does.

**Provenance contract (per source, recorded in the frozen manifest):**
- `as_read_sha256` = `sha256sum <path>` of the working-tree bytes actually read (the pin).
- `tracked_blob_HEAD` = `git rev-parse HEAD:<path>` (sha1) — recorded for reference; `UNTRACKED`/`ABSENT` where applicable.
- `git_status` = `git status --porcelain -- <path>` → `clean` / `M` / `??` (per-source dirty flag).
- **aggregate hash** over the sorted manifest body = `f462d023…` (single value pinning the whole closure).

**Change-during-inventory bracket (`changed_during_inventory=[]`):**
- **pre-bracket** = the frozen manifest above (this state).
- **post-bracket** = at inventory end, re-run the identical `sha256sum` sweep over the closure and diff
  vs the frozen manifest. Expected `changed_during_inventory = []`. Any path whose `as_read_sha256`
  changed → **flag loudly, re-freeze, re-hash, and re-quote** that source (its earlier reads are void).
- rationale: the tree is shared (other panes edit `route_executor.py`, envs, models); the bracket is
  the guard against silent mid-inventory drift.

**Exact command / output schema (registered):**
| purpose | command | output shape |
|---|---|---|
| as-read pin | `sha256sum <path>` | `<64-hex>  <path>` |
| tracked blob | `git rev-parse HEAD:<path>` | `<40-hex>` or error→`UNTRACKED` |
| dirty flag | `git status --porcelain -- <path>` | ` M `/`??`/empty(clean) |
| content read | `Read <path>` / `Grep -n <pat> <path>` | line-numbered text |
| aggregate | `grep -vP '^#' manifest \| LC_ALL=C sort \| sha256sum` | `<64-hex>` |

No env launch, no product run, no sim — repo scan/hash only (see B4).

---

## B2 (HIGH) — frozen source closure

The closure is **frozen** in the companion manifest (47 rows, categorized). Summary:

| category | count | notes |
|---|---|---|
| ORCH_SKILL_TRANSFORM | 9 | orchestrator + skills + transforms (item 5/4/3) |
| ENV_EXEC | 2 | `route_executor.py` (5078 L), `newton_skill_env_base.py` (2222 L) (item 2/3) |
| MODELS_POLICY | 3 | `base_policy`, `skill_adapter`, `skill_adapter_with_prediction` (item 1) |
| VISION_BELIEF | 6 | `vision_pipeline`, `visual_encoder`, `obs_builder`, `obs_collector`, `vision_dr_config`, `wrist_camera_manager` (item 2) |
| WORLD_MODEL | 2 | `world_model_4cam.py`, `evaluate_world_model.py` (WM L0 means) |
| SAFETY | 2 | `safety_envelope.py`, `fallback_guard.py` (item 3/5) |
| RL_IL_TRAINER | 7 | `train_common`, `train_base_model`, `train_grip`, `bc_pretrain`, `bc_train_route`, `route_demo_to_bc`, `dual_arm_skill_rewards` (item 1 lineage) |
| RUNNER_EVAL | 4 | `policy_route_runner`, `eval_skill`, `relabel_skills`, `route_demo_recorder` |
| CONFIG | 1 | `task_config.py` |
| REUSE_ANCHOR | 5 | see tags below |
| ABSENT_DECLARED | 1 | `docs/DAPG_DESIGN.md` — resolved below |

**`docs/DAPG_DESIGN.md` (CLAUDE.md Key-Files "唯一の権威ソース") = ABSENT at that path.** Negative-search
queries registered: `find thread_isaac_lab -iname '*dapg*'`, `grep -rIl 'DAPG_DESIGN' thread_isaac_lab`.
Result: no `docs/DAPG_DESIGN.md`; DAPG design authority currently lives in
`thread-vault/07-Design/RL-Routing-Design.md` (+ node docs `T-ROOT-optE-route-dapg-C1C2*`). Disposition:
tag `docs/DAPG_DESIGN.md` **ABSENT_IN_DECLARED_CLOSURE**; substitute authority = `RL-Routing-Design.md` +
trainer node docs (added to closure at item-1 read). **Flag to custody (p6):** CLAUDE.md Key-Files points
to a non-existent path — surface for correction (I do not edit that surface; custody/Rs disposition).

**Active policy / checkpoint (item-1 lineage).** 40 candidate policy files enumerated
(`residual_ppo_d4v2/ckpt_*.pt`, `fine_rl_*/final_policy.pt`, `base_model_*.pt`). **Active-selection is
UNVERIFIED** until item-1 reads `policy_route_runner.py`/trainer config to determine which checkpoint the
current route path loads; only that active checkpoint + its sidecar/metadata will be hashed
(immutable-policy-hash per charter §3). Enumeration frozen; selection deferred (not silently omitted).

**V11 reuse anchors (tagged; tag confirmed at read):**
| anchor | tag (declared) | use |
|---|---|---|
| `06-Knowledge/LL-Orchestration-Design.md` | historical-design-reference (confirm@read) | prior orchestrator design → reuse vs current `routing_orchestrator.py` |
| `06-Knowledge/LL-WorldModel-Feasibility.md` | historical-research (2026-04-25) | WM-candidate study → Skill Dynamics Model design reuse |
| `T-Skill/state.md` | current-node-authority | skill-supply blocker |
| `T-Vision/state.md` | current-node-authority | belief-grounding blocker |
| `T-WM/state.md` | current-node-authority | WM / classifier-cascade boundary (WMSO ≠ T-WM) |

---

## B3 (HIGH) — charter coverage trace (§5 deliverable + §6 gates)

**§5 D0 deliverable mapped to the six schema surfaces** (each inventoried factually, then a separated design field):
1. **state/belief schema** — obs/action + vision-derived vs privileged (sources: envs, models/vision*, task_config)
2. **skill action / lifecycle schema** — skill_id, policy family, lineage, init/term classes (sources: skills, models, trainers)
3. **transition (dynamics) distribution schema** — next-state/duration/success/cost/uncertainty at skill resolution (sources: world_model_4cam, orchestrator, — likely PARTIAL/ABSENT)
4. **handoff / recovery schema** — handoff state, accepted-incoming set, recovery/fallback (sources: transforms, snapshot, orchestrator, fallback_guard)
5. **safety / event / abstention schema** — independent low-level safety, event classes, OOD abstention (sources: safety_envelope, fallback_guard, orchestrator)
6. **per-event deadline schema** — D_situation + T_detect/T_ground/T_select/T_handoff (sources: task_config timing, physics dt 1/120, charter §4)

**§6 10-gate trace (registered; D0 claims NO gate PASS — this is a schema/inventory, not evidence):**
| # | gate | current fact / absence | D0 contract field (schema) | downstream evidence owner / gate |
|---|---|---|---|---|
| 1 | algorithm independence | TBD@inventory (BC/BC+RL/PPO/DAPG lineages present in trainers; common contract UNVERIFIED) | typed lifecycle contract fields | D1 contract tests |
| 2 | vision grounding | TBD@inventory (privileged sim-state suspected in current path) | belief-input provenance flag (vision vs privileged) | D2/M0 held-out + eval |
| 3 | model calibration (per-skill+per-handoff) | ABSENT@D0 (no Skill Dynamics Model yet) | calibration schema stub | M0 held-out/OOD gates |
| 4 | unknown-state abstention | TBD@inventory (OOD/abstention path UNVERIFIED) | abstention route field | M0/S0 |
| 5 | safe interruption | likely ABSENT (safe-interruption checkpoints suspected absent) | checkpoint + compat-set schema | S0/V0 |
| 6 | anti-thrashing | TBD@inventory | dwell/hysteresis field | O0/S0 |
| 7 | real-time (miss+max+fallback) | ABSENT@D0 (no measured latencies) | deadline schema (§4) | RT0 deadline tests |
| 8 | safety independence | TBD@inventory (safety_envelope/fallback_guard exist; independence UNVERIFIED) | independent-safety contract | S0/V0 safety gate |
| 9 | comparative value | N/A@D0 | baseline set declaration | O0 offline compare |
| 10 | no premature claim | **honored** — D0-M0 ≠ training-ready/closed-loop GO | explicit non-claim banner | S0/V0 two-key |

---

## B4 (MED) — fail-closed taxonomy + scope fence

**Taxonomy (no blanket "ABSENT"):**
- `ABSENT_IN_DECLARED_CLOSURE` — the named artifact does not exist within the frozen closure / the
  registered negative-search query returned nothing. Must cite the exact query (e.g. DAPG_DESIGN.md above).
- `UNVERIFIED` — exists but its property/behavior is not yet read-confirmed (e.g. active-checkpoint
  selection, whether a belief input is vision-derived).
- `PARTIAL` — some but not all of the required contract is present.
Every negative claim carries its **exact query + closure boundary**; nothing is asserted globally-absent
beyond the declared closure.

**Scope fence (explicit):**
- **ALLOWED (D0 read-only):** `Read`, `Grep`, `Glob`, `git` read (`hash-object`, `rev-parse`,
  `status`, `log`, `show`), `sha256sum`, `find`, prior-art guard scripts.
- **FORBIDDEN (unauthorized):** any `Edit`/`Write` to source/spec/config; any env/product/sim/training
  run; `policy_route_runner.py`/trainer/env execution; WMSO inference; closed-loop; safety/orchestrator
  path change; touching p4's grip gate chain.

---

## Disposition

Per pN: this v2 + frozen manifest will be **banked (explicit-path atomic commit, no push)**; artifact
sha + commit presented to pN; then **STOP** until pN re-readback **PASS**. No content extraction of the
six items until PASS. (v1 §A readback + §B boundaries unchanged and still in force.)
