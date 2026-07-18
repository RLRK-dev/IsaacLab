# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO **D1 Skill contracts** — scope pre-registration **v2** (folds pN B1–B7 HOLD)

- supersedes **v1** `WMSO_D1_SKILL_CONTRACTS_SCOPE_PREREG_RSTECHLEAD2_20260718.md` (commit `7b899e88c7`, sha256 `5704174927971f…`).
- node `T-WMSO` (parent `T-ROOT-RS-TECH-LEAD2`); author `w2:pQ`; independent verify `w2:pN`; custody `w2:p6`.
- prepared_at: **2026-07-18 ~23:1x JST** · repo HEAD advisory · **design / scope DOC only; no code, no impl, no run, no gate PASS.**
- **basis**: D0 Architecture EXIT GRANTED (pN round-3 PASS-CLOSE, `ac9fc83165`; LEDGER:41). charter §5 D1 row = *adapters for BC+RL and at
  least one other policy lineage; exit = contract tests and hash-pinned lineage* (`WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md:124`).
- **verdict folded**: pN D1 scope-concur on v1 = **HOLD (B1–B7)** (relayed 2026-07-18 23:00 JST; p6 reflect `39b83e551f`). This v2 folds all
  seven and requests re-readback. **scope CONCUR is NOT yet granted** — still gate-plan step 1; v2 remains a scope doc (no contract authoring).

## Fold map (pN B1–B7 → where addressed)
| item | pN concern | addressed |
|---|---|---|
| **B1** AUTH/ORDER | concur+/pre-check must not auto-unlock code; add separate implementation-GO gate; pre-freeze exact paths | **§0** (step 4 = new GO gate + path-freeze) |
| **B2** DELIVERABLE | charter deliverable = *adapters*; v1 had schema/harness/hash-util but no adapter substance | **§3 D1-C** (adapters = first-class) + **§4.1** |
| **B3** GATE① | LEARNED/SCRIPTED/WAIT ≠ algorithm independence; need on-disk RL-only or mark ABSENT + gate① unresolved | **§3 D1-E** (RL-only candidate named; PASS forbidden at scope) |
| **B4** LINEAGE | final-ckpt hash ≠ BC+RL triad; pre-register 3 artifact paths + shas + association; absent ⇒ inadmissible + exit#3 HOLD | **§3 D1-D** + **§4.2** |
| **B5** STATUS | split identity-pinned/conformant vs WMSO-selectable/closed-loop; hard test = no authority flip | **§3 D1-F** + **§4.4** + **§5** |
| **B6** TEST/PROV | harness needs negative controls + input manifest (as-read SHA, closure, pre/post bracket, added/missing/changed=[]) | **§3 D1-G** |
| **B7** V10 RECORDS | 5/0/0 not reproducible post-bank (self-match); record as-run@parent + disposition self-match; fold guard constraints | **§1** |

## §0. D1 gate-plan ORDER (B1 — explicit implementation-GO gate; concur+/pre-check do NOT unlock code)

1. **scope prereg (v1→THIS v2) → pN scope concur.** step-1 PASS opens **ONLY step 2** (design authoring). Nothing else.
2. **author D1 contracts + adapters *design*** (per-skill `SkillLifecycleContract` + `ExecutableIdentity`; the BC+RL & RL-only **adapters**
   §3 D1-C; per-dim `BeliefState` table + A/B/C map; harness *spec* + hash-pin *method*) — **design-only, no code** → bank.
3. **`/pre-check`** on the final design draft (own artifact, banked, keyed to that draft's sha).
4. ⭐ **implementation-GO gate (NEW, B1)** — **pN design readback + explicit implementation GO** (Rs GO where Rs-required). This gate **freezes
   the exact `added`/`changed` code + test paths** as a manifest. **concur (step 1) + /pre-check (step 3) alone do NOT authorize any code.**
5. **build — ONLY the frozen paths** (schema types + BC+RL & RL-only adapters + contract-test harness + hash-pin utility). Read-only
   conformance + content-hash over *existing* artifacts. ⛔ no training / inference / production-control / closed-loop / selection-authority.
6. **run contract + adapter + negative tests; pin lineage** → bank the passing evidence + the input/lineage manifest (each keyed to sha).
7. **pN D1-exit independent verify** — charter §5 exit = *contract tests pass* ∧ *hash-pinned (identity-pinned) lineage* ∧ (§4.4) no authority flip.

## §1. Prior-art / reuse disposition (B7 — records fixed)

**V10 guard** `check_thread_vault_prior_art.sh --fail-on-blocker "skill contract" "policy lineage" "hash-pinned" "skill adapter"`:
- **as-run @ parent `d854dc2b76`** (before this doc existed, v1 §1's actual run) = **findings=5, blockers=0, lessons=0, exit=0** — the 5 findings
  are charter/verdict self-references (the D1 row), no prior failed path.
- **post-bank re-run @ `7b899e88c7`** = **findings=13, blockers=4, lessons=3, exit=2** — the +8/4/3 delta is **THIS doc's own `:31` line quoting
  the guard command** (self-reference). **Disposition: self-match, not a prior-art blocker.** v1's "5/0/0" was true at the parent, not
  reproducible post-bank *because the doc now contains the keywords* — recorded honestly here (records-match-fact). **Concrete delta = new D1
  design scope after D0 EXIT; not an experiment / retry / source promotion.**
- **guard-surfaced constraints folded** (pN B7): `hash_unpinned` ⇒ inadmissible (D0 §B:158-160); AC/AR/IC RL wrappers **ABSENT** (D0 §B:160);
  D0 handoff / fail-close semantics are **not weakened** by D1.

Reuse dispositions (carried from v1, unchanged): sha256 content-hash primitive `bc_train_route.py:30,117-135` (`ckpt_sha256`) +
`policy_route_runner.py:58-60,456,622` (`policy_sha256`) = **INCORPORATED**; D0 schemas = **INSTANTIATED not re-designed**; skill vocabularies
(`step_table.py:35-51` / `skill_adapter.py:45-58` / `skill_adapter_with_prediction.py:150-157`) = **RECONCILED (D1-A)**; `snapshot.py`
`StateSnapshot` = capture substrate only; LL-WMF/LL-ORCH dispositions = carried from D0 scope v2 §B1.

## §2. [DEFER-RECON] reconciliation (carried — pN accepted DDR-non-block)

No FOUNDATIONAL DDR item (#2/#4/#12/#18/#19) gates the D1 scope or contract *design* — all are training-ready / route-pin, downstream (O0/M0/V0);
D0 gate⑩ fences them. #18 gates *closed-loop admissibility* (Gate-4), **not** contract authoring (see §3 D1-F). Only D1-local dependency =
`T-Skill` hash-pinnability, handled fail-closed (`inadmissible` where the artifact/association is absent; §3 D1-D). ⛔ D1 never trains to
manufacture a hash.

## §3. D1 deliverable structure (each DESIGN-ONLY at authoring; B2–B6 folded)

**D1-A — canonical `skill_id` reconciliation.** One authoritative set; map `SkillName`(9)/`SkillType`(7)/`bimanual_*`(6) into it; flag
orphans/aliases. (D0 §B FACTUAL "unreconciled vocabularies", `…DRAFT…:124-128`.)

**D1-B — per-skill `SkillLifecycleContract` + discriminated `ExecutableIdentity`** (`LEARNED`/`SCRIPTED`/`WAIT`). charter §3 fields
(`…CHARTER…:82-96`); D0 §B (`…DRAFT…:134-156`). Never key by name alone.

**D1-C — adapters as FIRST-CLASS deliverable (B2).** charter §5:124 deliverable = *adapters*. D1 implements at minimum:
- a **BC+RL adapter** and a **≥1 other learned-policy (RL-only) adapter**: `raw skill I/O (obs/action schema + policy identity) → canonical
  `SkillLifecycleContract` + `BeliefState` output`; with an explicit **implementation target** and **adapter tests** (I/O conformance +
  round-trip), bound into build (§0 step 5) and exit (§4.1).
- the **§A Belief A/B/C surface adapters** are **separately scoped**: state per surface whether D1 **implements** the adapter or delivers it
  **design-only** (a map). (Default proposal: implement the adapter for the two lineages above; A/B/C 62D/25-27D belief adapters = design-only
  map at D1, implemented at D2/dataset when vision is wired — flagged, not silently deferred.)

**D1-D — BC+RL lineage TRIAD + association (B4).** charter §3 requires distinguishing **base BC ckpt / RL finetune cfg / final policy**
(`…CHARTER…:94`). D1 pre-registers, per BC+RL skill: **3 concrete artifact paths** (`base_ckpt`, `finetune_cfg`, `final_policy`) + **each sha** +
**run-specific association evidence** proving the final was produced by fine-tuning that base with that config. **On-disk today**: base-provenance
precedent EXISTS (`data/d1_lora_s1_demos_*/manifest.json` records `baseline_ckpt_path` + `baseline_ckpt_sha256` + `env_source_sha256` +
`task_config_sha256`; `bc_train_route.py` sidecar) — but a **complete finetune→final association is NOT demonstrated** (those are demo-collection
manifests, status `PHASE1V4_FAIL_…`, no final-policy lineage record). ⇒ **if step-2 finds no on-disk triad-association, the BC+RL contract is
`hash_unpinned`/`inadmissible` and D1 exit#3 is HOLD** (⛔ no training to manufacture it). Classification by DAPG name / trainer family alone is
**forbidden**.

**D1-E — gate① framing corrected (B3).** charter §6① = *BC+RL **and RL-only** through the same contract* (`…CHARTER…:137`).
`LEARNED/SCRIPTED/WAIT` discriminant coverage is a **separate** "contract-uniformity" point, **not** gate① evidence. **RL-only candidate PRESENT
on-disk**: `data/residual_ppo_d4v2/ckpt_final.pt` (PPO residual) and `thread_isaac_lab/logs/rsl_rl/insert_clip_20260325_235722/model_*.pt`
(RSL-RL/PPO per-skill). D1 authors ≥1 RL-only contract from these. **gate① is *demonstrated* only when BC+RL AND the RL-only skill both pass the
one contract — NOT claimed PASS at scope.** If step-2 finds the RL-only artifacts stale/unusable ⇒ RL-only = **ABSENT/inadmissible**, **gate①
unresolved**, and ⛔ **no gate① PASS may be claimed** at D1.

**D1-F — status semantics split (B5).** Two distinct axes; never conflate:
- **`identity_pinned` ∧ `contract_conformant`** = D1's scope (the hash is pinned + the contract validates). **Necessary only.**
- **`closed_loop_admissible`** = downstream (O0/V0): additionally requires **Gate-4 maturity (skill_SR≥70%)**, the **#18** grip verdict, and
  checkpoint/compatibility — **out of D1 scope.** D1 grants **no** selection authority.
- **hard assertion (tested, §4.4)**: D1 flips **no** selection authority — `closed_loop_admissible` is never set true by any D1 artifact.

**D1-G — contract-test harness: negative controls + provenance (B6).** The harness is **not** presence-happy-path only. Binding negative
controls: missing/changed hash rejected · same-name-different-lineage ⇒ **different key** · duplicate/alias `skill_id` rejected · `schema_version`
mismatch ⇒ fail-closed · `PRIVILEGED_SIM ∧ prod_admissible=true` ⇒ reject · empty/absent checkpoint ⇒ `INTERRUPT` impossible / artifact absent ⇒
inadmissible · `TERMINAL`/`INTERRUPT` missing-mandatory-field ⇒ reject. **Input manifest** (per run): repo/as-read SHA + dirty-state + named
`artifacts`/`config`/`source` closure + **pre/post hash bracket** + explicit `added`/`missing`/`changed=[]`.

## §4. D1 exit criteria (charter §5:124 — concrete; verified by pN at D1-exit)
1. **contract tests + adapter tests + negative controls (D1-C/D1-G) all pass** over every canonical skill.
2. **identity-pinned lineage**: every `identity_pinned` skill's `ExecutableIdentity` hash pinned to a named on-disk artifact; **BC+RL carries the
   3-artifact triad + association or exit#3 is HOLD**; every non-pinnable skill = explicit `hash_unpinned`/`inadmissible` + reason (no silent gap).
3. **≥2 lineages** with tested, pinned contracts incl **BC+RL (triad)** and **≥1 RL-only** (gate① candidate) — else **gate① unresolved, no PASS**.
4. **no authority flip (B5)**: `closed_loop_admissible` granted to **no** skill at D1; the §D orchestrator gains **zero** selection authority (hard-asserted).
5. **no premature claim** (gate⑩): D1 ≠ training-ready/closed-loop; M0/O0/S0/V0 remain gated.

## §5. Boundaries (held)
⛔ **no auto-unlock of code (B1)**: step-1 concur + step-3 /pre-check do not authorize implementation; the §0 step-4 GO gate + path-freeze does.
⛔ **no selection-authority flip (B5)** · ⛔ **no training to manufacture a hash (B4)**.
⛔ **UNAUTHORIZED until own gate**: production control / training launch / WMSO inference / closed-loop / removing any safety-or-orchestrator path
/ p4 grip (charter §0/§8-4). **RS71 §0 FOUNDATIONAL invariants untouched** (DUAL-ARM · 88 mm span · DiffIK-only · コ-shape LOCKED · no-kinematic-trick).
`T-WMSO-SDM` child **not** created here (M0; Rs approval). Non-mixing with (d-b) route/pin + `T-WM` cascade held (charter §8-2).

## §6. Ask to pN
**Re-readback** this v2 (B1–B7 folds per the map above) and issue **scope CONCUR or a further HOLD**. Points to check: §0 step-4 GO gate +
path-freeze (B1); §3 D1-C adapter substance (B2); §3 D1-E RL-only candidate + gate①-no-PASS (B3); §3 D1-D triad+association + fail-closed (B4);
§3 D1-F/§4.4 status split + no-authority-flip hard test (B5); §3 D1-G negative controls + manifest (B6); §1 V10 as-run@parent + self-match
disposition (B7). ⛔ design/scope only; no code / run / gate PASS. No experiment / retry / source promotion is proposed.
