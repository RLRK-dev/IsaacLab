# [RS-TECH-LEAD2 (w2:pQ) → OPS-SUP-CODEX (w2:pN)] WMSO **D1-exit schema recovery** — SCOPE PREREG v1

- Node `T-WMSO` (parent `T-ROOT-RS-TECH-LEAD2`). Written 2026-07-19 06:40 JST. **SCOPE-ONLY; no code, no design freeze, no run.**
- Ask: **pN SCOPE CONCUR** on this chunk's boundary before I write the design (field maps + exemplar bind). Not a design or impl-GO.
- Rs authorization: schema-recovery chunk = "a" (2026-07-19); INSERT disposition = **(E) revisit DECISION#2, reselect a schema-recoverable later exemplar** (2026-07-19).
- Grounding: feasibility record `WMSO_D1_SCHEMA_RECOVERY_FEASIBILITY_RSTECHLEAD2_20260719.md` · design v4.1.1 `b7ec765bbc` (doc:42/55) · harness `wmso/d1/harness.py:63-109` · contracts `wmso/d1/contracts.py:145-181` · manifest `wmso/d1/skill_contracts_manifest.json` · LEDGER row 41.

## Premise (from feasibility investigation)
- `contract_conformant` sole open leg for the two learned exemplars = `field_semantics=UNRESOLVED` (`harness.py:84-85`). To close: bind ordered `obs_fields`/`action_fields` (each `{field_id,dtype,shape,unit,frame}`) + set `RESOLVED`.
- **APPROACH_CABLE** (42D/12D): schema recoverable — surviving direct-lineage env `newton_approach_cable_env.py@0fca80389b` + current mujoco port `:22-42/:845-858` + base-policy dims (42/12) + run-record action-scale all agree.
- **model_9** (INSERT, 10D/3D, DECISION#2): schema unrecoverable on-machine (trained 2026-03-25 ≫ git-tracking 2026-06-07; env/demo/ckpt/tfevents all dims-only). → reselect per (E).

## Scope IN (this chunk)
1. **Reselect the INSERT_INTO_CLIP exemplar** (reopen DECISION#2 per Rs (E)): replace `model_9` (10D/3D, unrecoverable) with a schema-recoverable later exemplar.
   - Concrete candidate: **`data/rl_insert_clip_approach_w256_20260410_200300/model_best.pt`** — BC+RL DAPG, 45D/12D; base `base_model_mixed_20260410_194505.pt` (exists on disk); run-record `summary.json` (env_config 33 keys incl. POS/ROT_ACTION_SCALE=0.015/0.05). Symmetric to the APPROACH exemplar.
   - Identity standard = **DECISION#1=A** (RECORDED_PATH_CONFIG_COLOCATION, `train_time_crypto_bound=false`, no retrain) — same as APPROACH.
2. **Build RESOLVED FieldSpec bindings** for APPROACH (42D obs / 12D act) + the new INSERT exemplar (45D obs / 12D act) from the best-surviving git envs (approach: `newton_approach_cable_env.py@0fca80389b`; insert: `newton_insert_clip_env.py@0fca80389b`, doc'd 45D = 14D arm + 3D groove-err + 3D ori-err + 1D dist + 21D cable-shape + 3D cable-vel).
3. **Update `wmso/d1/skill_contracts_manifest.json`**: INSERT row (new artifacts/identity), both learned rows (`field_semantics: RESOLVED`, add `obs_fields`/`action_fields`, `contract_conformant: true` iff all fail-close pass).
4. **Harness support (if needed)**: assertion that a RESOLVED schema's `len(obs_fields)==obs_dim` and `len(action_fields)==action_dim` (fail-closed). No authority axis ever set true.
5. Re-pin new INSERT artifact hashes (final/base/run-record) on a fresh detached worktree (committed state).

## Scope OUT
- ⛔ No retrain / no new training. ⛔ No FOUNDATIONAL invariant change (dual-arm/88mm/DiffIK/コ/no-trick untouched — schema is documentation, not physics/control). ⛔ No D1-exit-criterion redefinition (E *satisfies* the existing criterion, does not relax it). ⛔ No route/env runtime behavior change. ⛔ Other 7 skills' rows unchanged. ⛔ CLAMP/AERIAL/UNCLAMP stay INADMISSIBLE.

## Selection criteria (INSERT exemplar)
(a) schema-recoverable (env layout survives in git); (b) clean identity under DECISION#1=A standard (base+finetune-cfg+final present, or RL-only); (c) representative of the INSERT_INTO_CLIP skill behavior.

## Open questions (pN concur / Rs)
- **Q1 (mode representativeness):** the clean candidates with a designated `model_best.pt` are all `InsertIntoClip-approach` runs; the `InsertIntoClip_DAPG` insert-mode 45D runs lack a designated best/base. Is an approach-mode policy an acceptable INSERT_INTO_CLIP exemplar, or must it be insert-mode? (design-correctness, needs pN+possibly Rs.)
- **Q2 (RESOLVED bar):** both bindings source from the best-surviving env (2026-06-07, ~2 mo post-train, untracked drift + a documented clamp-pos computation nuance for approach). Does that clear the binary `RESOLVED` bar, or should the design add an intermediate provenance marker (e.g. `schema_provenance = BEST_SURVIVING_LINEAGE` alongside `RESOLVED`)?
- **Q3:** confirm DECISION#2 reopening is in-scope (Rs=yes via (E)); the new pick will be surfaced to Rs before bank.

## L-TRIAGE (self-declared)
**L2** — contract-semantics change (RESOLVED binding) + manifest + reopens a banked ruling; ≥3 files; design-gate (pN readback) mandatory. Not L3 (no L3 auto-promote path/keyword; wmso pkg additive; no reward/env/physics/control change).

## Next (post-concur)
pN SCOPE CONCUR → design v1 (full 42D + 45D per-dim FieldSpec maps + exemplar bind + fail-close) → pN design readback → PASS-CLOSE → impl (manifest + harness) → pN impl-verify → **D1 exit** (both legs conformant). ⛔ D1 exit stays HOLD until both land.
