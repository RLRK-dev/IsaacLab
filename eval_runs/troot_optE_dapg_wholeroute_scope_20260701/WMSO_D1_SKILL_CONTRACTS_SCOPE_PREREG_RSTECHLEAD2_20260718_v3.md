# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO **D1 Skill contracts** — scope pre-registration **v3** (folds pN R1–R3; B1–B7 PASS-CLOSE)

- supersedes **v2** `…_v2.md` (commit `fed7b8d597`, sha256 `11ec8f3d0ecf9…`) → **v1** `…20260718.md` (`7b899e88c7`).
- node `T-WMSO`; author `w2:pQ`; independent verify `w2:pN`; custody `w2:p6`. prepared_at: **2026-07-18 ~23:2x JST** · **design / scope DOC
  only; no code, no impl, no run, no gate PASS.**
- **basis**: D0 EXIT GRANTED (`ac9fc83165`; LEDGER:41). charter §5 D1 = *adapters for BC+RL and at least one other policy lineage; exit =
  contract tests and hash-pinned lineage* (`WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md:124`).
- **verdicts folded**: pN v1 = HOLD B1–B7 (`39b83e551f`) → **v2 folded B1–B7**; pN v2 re-readback (2026-07-18 23:15 JST) = **B1/B3/B4/B6/B7
  PASS-CLOSE** (B7 independently reproduced: parent `d854dc2b76`=5/0/0 rc0, v1 `7b899e88c7`=13/4/3 rc2, current HEAD 19/8/5 = v1+v2 guard-line
  self-match, same class / non-block) + **HOLD R1–R3**. This v3 folds R1–R3 **only** (no design/impl expansion beyond B1–B7). **scope CONCUR
  not yet granted** — still step 1; v3 remains a scope doc.

## Fold map (this round = pN R1–R3; B1–B7 already PASS-CLOSE)
| item | pN concern | addressed |
|---|---|---|
| **R1** CRIT adapter boundary | v2 §D1-C: policy adapter "implements raw I/O→BeliefState" contradicts "A/B/C belief adapters design-only"; round-trip claim | **§3 D1-C** rewritten: 3 separated surfaces; round-trip WITHDRAWN → canonicalization/schema/determinism tests |
| **R2** HIGH status axis | v2 §D1-F 2 axes conflate O0 (offline replay) and V0 (live) under `closed_loop_admissible` | **§3 D1-F** 4 axes; D1 sets only first 2; offline+live both hard-false; O0≠closed-loop |
| **R3** records | v2:78 key `baseline_ckpt_sha256` ≠ actual `_at_start`/`_at_end`; sidecar ≠ association | **§1 + §3 D1-D** verbatim key fix + sidecar=precedent-only |

## §0. D1 gate-plan ORDER (B1 PASS-CLOSE — carried verbatim)
1. **scope prereg (→v3) → pN scope concur.** step-1 PASS opens **ONLY step 2**.
2. **author D1 contracts + adapters *design*** (design-only) → bank.
3. **`/pre-check`** on the final design draft (banked, keyed to sha).
4. ⭐ **implementation-GO gate** — **pN design readback + explicit implementation GO** (Rs where Rs-required); **freezes exact `added`/`changed`
   code + test paths**. **concur + /pre-check alone do NOT authorize code.**
5. **build — ONLY frozen paths** (schema types + BC+RL & RL-only policy adapters + contract-test harness + hash-pin utility). Read-only
   conformance + content-hash over existing artifacts. ⛔ no training / inference / production-control / closed-loop / selection-authority.
6. **run contract + adapter + negative tests; pin lineage** → bank passing evidence + input/lineage manifest (each keyed to sha).
7. **pN D1-exit independent verify** — *contract tests pass* ∧ *identity-pinned lineage* ∧ (§4.4) no authority flip.

## §1. Prior-art / reuse (B7 PASS-CLOSE — carried; R3 sidecar note)
V10 guard (keywords: skill-contract / policy-lineage / hash-pinned / skill-adapter): **as-run @ parent `d854dc2b76` = 5/0/0 rc0** (external =
charter/verdict self-refs, 0 blockers); **post-bank re-runs self-match** (v1 `7b899e88c7`=13/4/3 rc2; HEAD 19/8/5 = this doc's own guard-line
quotes) — **disposition: self-match, non-block, not a prior failed path** (independently reproduced by pN). Concrete delta = new D1 design scope
post-D0-EXIT; no experiment / retry / source promotion. Guard constraints folded: `hash_unpinned`⇒inadmissible; AC/AR/IC wrappers ABSENT; D0
handoff/fail-close non-weakening.
Reuse primitives: sha256 content-hash `bc_train_route.py:30,117-135` (`ckpt_sha256` sidecar) + `policy_route_runner.py:58-60,456,622`
(`policy_sha256`) = **INCORPORATED as hash precedent only** (⛔ **not** a finetune→final lineage association — R3); D0 schemas = INSTANTIATED;
vocabularies (`step_table.py:35-51`/`skill_adapter.py:45-58`/`skill_adapter_with_prediction.py:150-157`) = RECONCILED (D1-A); `snapshot.py`
`StateSnapshot` = capture substrate only.

## §2. [DEFER-RECON] (carried — pN accepted DDR-non-block)
No FOUNDATIONAL DDR item (#2/#4/#12/#18/#19) gates D1 scope/design (all downstream O0/M0/V0; #18 gates *closed-loop admissibility*, not contract
authoring). Only D1-local dependency = `T-Skill` hash-pinnability, fail-closed (`inadmissible` where artifact/association absent). ⛔ never train
to manufacture a hash.

## §3. D1 deliverable structure (DESIGN-ONLY; B2–B6 PASS-CLOSE, R1/R2/R3 folded)

**D1-A — canonical `skill_id` reconciliation** (map `SkillName`(9)/`SkillType`(7)/`bimanual_*`(6) → one set; flag orphans/aliases).
**D1-B — per-skill `SkillLifecycleContract` + discriminated `ExecutableIdentity`** (`LEARNED`/`SCRIPTED`/`WAIT`); never key by name alone.

**D1-C — adapters, boundary-SEPARATED (R1).** Three distinct surfaces; ⛔ do **not** conflate:
1. **D1 policy adapter — IMPLEMENTED in D1** (charter deliverable): a **static** transform `(skill ExecutableIdentity + declared obs/action
   schema) → canonical SkillLifecycleContract representation` via **schema-bound payload canonicalization** (canonical `field_id` mapping +
   unit/frame/provenance tagging **of the schema**). It does **not** ground belief and does **not** run a policy. Delivered for **BC+RL + ≥1
   RL-only** lineage.
2. **D1 per-dim A/B/C BeliefState map — DESIGN-ONLY in D1**: the per-dim table (which raw obs dim per surface A/B/C ↔ which canonical
   `field_id`). A **map/design artifact**, not an implemented runtime encoder.
3. **D2 runtime belief grounding — OUT of D1**: populating `BeliefState.value` from live/vision obs at runtime (needs vision wired) = D2/dataset.
- **Binding surface decision**: D1 **implements #1** (static policy-adapter canonicalization) for BC+RL + RL-only; **delivers #2 design-only**;
  **#3 explicitly out of D1**.
- **Round-trip claim WITHDRAWN (R1)**: canonicalization inverse (canonical→raw) is undefined/unrequired → **no round-trip**. Adapter tests =
  **canonicalization correctness + schema-conformance + determinism** (identical input schema ⇒ identical canonical output).

**D1-D — BC+RL lineage TRIAD + association (B4 PASS-CLOSE; R3 key fix).** Requires **3 artifact paths** (`base_ckpt`, `finetune_cfg`,
`final_policy`) + **each sha** + **run-specific association evidence** (final produced by fine-tuning that base with that config). **On-disk
today**: base-provenance precedent exists — `data/d1_lora_s1_demos_*/manifest.json` records **verbatim keys** `baseline_ckpt_path`,
`baseline_ckpt_sha256_at_start`, `baseline_ckpt_sha256_at_end`, `env_source_sha256`, `task_config_sha256` (R3 fix; earlier `baseline_ckpt_sha256`
was a paraphrase) — **but no finetune→final association** (demo-collection manifests, status `PHASE1V4_FAIL_…`). ⇒ **absent association ⇒ BC+RL =
`hash_unpinned`/`inadmissible`, D1 exit#3 HOLD** (⛔ no training to manufacture). Classification by DAPG name / family alone **forbidden**.

**D1-E — gate① framing (B3 PASS-CLOSE — carried).** gate① = *BC+RL **and RL-only** through one contract*; `LEARNED/SCRIPTED/WAIT` coverage is a
**separate** contract-uniformity point. RL-only candidate PRESENT on-disk (`data/residual_ppo_d4v2/ckpt_final.pt`;
`thread_isaac_lab/logs/rsl_rl/insert_clip_20260325_235722/model_*.pt`). gate① **demonstrated only when BC+RL AND RL-only both pass one
contract — NOT claimed PASS at scope**; if step-2 finds them stale/unusable ⇒ RL-only ABSENT/inadmissible, **gate① unresolved, no PASS**.

**D1-F — status vocabulary, 4 AXES (R2).** Never conflate; **D1 may set true ONLY the first two**:
| axis | meaning | D1 |
|---|---|---|
| `identity_pinned` | hash pinned to a named artifact (+ BC+RL triad-association, D1-D) | may be true |
| `contract_conformant` | contract validates against schema (D1-G) | may be true |
| `offline_orchestration_admissible` | **O0 — replay-only** planning/switching over logged data. **O0 ≠ closed-loop.** | **hard-false at D1** |
| `closed_loop_admissible` | **V0 — live** authority | **hard-false at D1** |
- **D1 grants neither offline nor live authority** (both hard-asserted false). Downstream: offline needs O0 gates; live needs Gate-4/#18/V0 two-key.

**D1-G — harness negative controls + provenance (B6 PASS-CLOSE — carried).** Negative controls: missing/changed hash · same-name-different-lineage
⇒ different key · duplicate/alias `skill_id` · `schema_version` mismatch · `PRIVILEGED_SIM ∧ prod_admissible=true` reject · empty/absent
checkpoint ⇒ `INTERRUPT` impossible / inadmissible · `TERMINAL`/`INTERRUPT` missing-mandatory-field. Input manifest: repo/as-read SHA +
dirty-state + named `artifacts`/`config`/`source` closure + pre/post hash bracket + explicit `added`/`missing`/`changed=[]`.

## §4. D1 exit criteria (charter §5:124)
1. **contract + adapter (canonicalization/schema/determinism, D1-C) + negative-control (D1-G) tests all pass**.
2. **identity-pinned lineage**: each pinned skill's hash → named artifact; **BC+RL carries triad+association or exit#3 HOLD**; non-pinnable =
   explicit `hash_unpinned`/`inadmissible` + reason (no silent gap).
3. **≥2 lineages** incl **BC+RL (triad)** + **≥1 RL-only** (gate① candidate) — else **gate① unresolved, no PASS**.
4. **no authority flip (R2)**: D1 grants **neither** `offline_orchestration_admissible` **nor** `closed_loop_admissible` (both hard-asserted
   false); only `identity_pinned` + `contract_conformant` may be set. Orchestrator gains **zero** selection authority.
5. **no premature claim** (gate⑩): D1 ≠ training-ready/closed-loop.

## §5. Boundaries (held)
⛔ no auto-unlock of code (B1: step-4 GO gate + path-freeze) · ⛔ no offline/live authority flip at D1 (R2) · ⛔ no training to manufacture a hash
(B4) · ⛔ round-trip not claimed (R1). ⛔ UNAUTHORIZED until own gate: production control / training / WMSO inference / closed-loop / removing any
safety-or-orchestrator path / p4 grip (charter §0/§8-4). **RS71 §0 FOUNDATIONAL invariants untouched** (DUAL-ARM · 88 mm · DiffIK-only · コ-shape
LOCKED · no-kinematic-trick). `T-WMSO-SDM` child not created (M0; Rs approval). Non-mixing with (d-b) route/pin + `T-WM` cascade held.

## §6. Ask to pN
**Re-readback** v3 (R1–R3 folds per map). Check: §3 D1-C 3-surface separation + round-trip withdrawn → canonicalization/schema/determinism
(R1); §3 D1-F 4-axis status + offline&live both hard-false + O0≠closed-loop (R2); §3 D1-D / §1 verbatim manifest keys + sidecar=precedent-only
(R3). B1–B7 unchanged (already PASS-CLOSE). ⛔ design/scope only; no code / run / gate PASS; no design/impl expansion beyond B1–B7.
