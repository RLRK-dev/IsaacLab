# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO D0 architecture-draft — scope pre-registration **v2** (folds pN B1–B6)

- supersedes v1 `…_SCOPE_PREREG_…_20260718.md` (sha `adf39cb1…`). node `T-WMSO`; author `w2:pQ`; verify `w2:pN`; custody `w2:p6`.
- prepared_at: 2026-07-18 15:56 JST · repo HEAD `d993c550d7` (advisory) · **design DOC scope only; no code/impl/run; no gate PASS**.
- basis: D0 factual inventory PASS-CLOSE (`…_v4.md`, `513948a15e`). pN v1 review PASSed the A–I skeleton (covers gates 1-10) +
  design-only/boundaries; HOLD for B1–B6 corrections → this v2 folds them and re-banks before authoring.

## B6 — corrected gate-plan ORDER (this doc = step 1)
1. **prior-art/reuse disposition + revised scope bank (THIS v2)** → 2. author §A–§I draft → 3. **/pre-check** (own artifact + bank)
→ 4. architecture-draft bank → 5. **pN D0-exit independent design verify**. ⛔ no production/training/sim/inference/closed-loop/grip.

## B1 — prior-art / reuse disposition (V10 guard run before authoring)
V10 guard `check_thread_vault_prior_art.sh --fail-on-blocker "world model" "orchestration" "recovery chaining" cascade SPlaTES`
→ 30 keyword-matches (prior orchestration/cascade **design context**, e.g. `LL-{Orchestration,Cascade-C-*,BaseAdapter,L1-B-Routing}-Design`,
`EXEC_PLAN_V1V2`), **no hard NO_GO on WMSO**. WMSO is a new Rs-mandated L0 architecture — it **reuses** these conclusions, does not
repeat a failed path. Explicit disposition (retained / superseded / incorporated):

| prior-art item | source | disposition |
|---|---|---|
| **Rs Option-α Cascade A→C→{B\|D}** (measure-first, gated staging) | LL-WMF (Rs-adopted 2026-04-25) | **INCORPORATED** — WMSO D0→V0 staging aligns to it: measure Cluster-G recovery floor first; stage WM behind skill-SR gates |
| **Gate-4 maturity** (min skill_SR ≥70% before RC/SPlaTES) | LL-WMF | **INCORPORATED** — WMSO does not build the skill-dynamics-model/closed-loop before the skill-SR floor is met |
| **STOP candidates** IRIS / MuZero / World4RL(Diffusion-WM) / MoE-DP | LL-WMF | **RETAINED (STOP)** — not proposed |
| **Dreamer V3 official (JAX)** | LL-WMF | **RETAINED (rejected)** — torch-port/self-built latent WM only if needed |
| **Cosmos latent WM** (detection-only, sim-shift calibration) | LL-WMF | **INCORPORATED as CAUTION** — detection reusable; recovery-generation = new research; needs AUROC≥0.85 sim-shift calibration |
| **SPlaTES skill-level WM + short rollout H<5** | LL-WMF | **INCORPORATED** — §C = skill-level transitions ONLY, bounded rollout H<5 |
| **model-exploitation / HMBRL-inferior** | LL-WMF | **INCORPORATED as guard** — §C mandates regularization/constraint + per-skill/per-handoff calibration |
| **scope-inflation NO-GO** (9-comp = 4.5× rejected, Rs「精密制御不要」) | LL-WMF | **RETAINED** — draft kept minimal; net-new only where charter-required |
| **confidence-gated fast→slow arbitration** (Qwen<0.85→API) | LL-WMF | **INCORPORATED** — §D fast/slow arbitration pattern |
| **Cascading-P0 handoff + `StateSnapshot`** | LL-ORCH | **INCORPORATED as PRECEDENT** — §E; P0 hooks `export_terminal_state`/`load_p0_from_cascade` are UNIMPLEMENTED (reconcile vs v4) |
| **LL-Orchestration-Design as "current truth"** | LL-ORCH | **PRECEDENT, NOT TRUTH** — reconciled against inventory v4 (v4 confirms recovery engine in `routing_orchestrator.py`; test-counts/impl-status treated as precedent, re-verified vs v4, not asserted) |
| **L1-adapter-orchestration** | EXEC_PLAN | **PARKED (Rs-confirm)** — noted, not built |

## Revised A–I structure (B2–B5 requirements folded)
| § | schema | binding requirements added (pN B2–B5) |
|---|---|---|
| A | **state / belief / goal** | cover **all 3 surfaces A/B/C** (A per-skill env obs, B 62D, C 25-27D); add **goal/task-context** schema; each field carries **provenance** (vision-derived \| privileged-sim \| script-state \| const) + **monotonic clock/timestamp** + **confidence** + **OOD flag**; privileged sim state = **training/evaluation metadata only**, never an undeclared production input (charter gate②) |
| B | **unified skill lifecycle contract** | key each skill action by **immutable policy hash + lineage + handoff/start context** (NEVER skill-name alone); include model **version/freshness/support-boundary** + **fail-closed stale/out-of-support** action |
| C | **skill dynamics model** | skill-level transitions only; **bounded short rollout H<5**; per-skill + per-handoff **calibration**; **model-exploitation guard** (regularization/constraint); outputs {next-belief, duration, success/fail class, cost, uncertainty} (note LL-WMF gap: duration/cost were not modeled → explicitly design them) |
| D | **orchestrator** | candidate filter(init+safety) → continuation-vs-switching **value comparison** (net-new; absent in reuse) → select → replan; **confidence-gated fast(precomputed policy/Q)→slow(short rollout)** arbitration; anti-thrash; OOD abstention (replace default-accept stub) |
| E | **transition manager** | {direct handoff@compatible handoff-state \| transition skill \| recovery skill \| re-observe/safe-stop}; reuse Cascading-P0 + `StateSnapshot`; **declare safe-interruption checkpoints** (ABSENT in v4) |
| F | **independent safety monitor** | **separately owned interface**; priority over WMSO; **prove it does NOT wait on WMSO** (succeeds when model/orchestrator delayed/crashed/stale/adversarially-wrong) |
| G | **event detector + per-event deadline** | **separately owned** from F; freeze **event priority / co-terminal resolution**, **monotonic clock / time origin**, **detection-to-handoff completion definition**, **fallback / deadline-miss behavior**; 3 decision classes; D_situation + T_detect+T_ground+T_select+T_handoff; acceptance p50/p95/p99/max/jitter/deadline-miss/fallback/safety-override; bounded soft/firm (not hard) |
| H | **bridge + explicit dependency interfaces/owners** | reuse-vs-new table; **explicit dep interfaces + owners**: T-Skill (skill supply) / T-Vision (belief) / T-WM (WM — keep **DISTINCT from the T-WM classifier cascade**) / trainer (RLPD path); connect NOT mix |
| I | **10-gate crosswalk + measurement + eval** | exact **1-row-per-gate crosswalk** (gate → schema + acceptance); charter **§7 measurement/stress matrix**; **gate-9 four-baseline plan** (fixed chain / current heuristic recovery / boundary-only WMSO / event-driven WMSO); every D0 row **DESIGN-ONLY**, status = unresolved / evidence-pending |

## Boundaries (held)
⛔ production control / training launch / WMSO inference / closed-loop / removing safety-or-orchestrator paths / p4 grip.
FOUNDATIONAL invariants (RS71 §0) unchanged by a schema draft; apparent change = premise change = STOP + Rs.

## Ask to pN
Concur on this **revised scope (B1 dispositions + B2–B6 folds)**, or flag remaining gaps, before I author §A–§I per the B6 order.
