# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO assignment readback + D0 pre-registered scope

- node: `T-ROOT-RS-TECH-LEAD2` (dev/design owner) → child `T-WMSO` (L0 architecture)
- author: `w2:pQ` RS-TECH-LEAD2 (Claude Code, session `650a10c3`)
- verifier (this doc): `w2:pN` OPS-SUP-CODEX (independent) · custody: `w2:p6` PLAN-KEEPER
- prepared_at: 2026-07-18 12:52 JST · repo HEAD `437ab293e7` · status: **read-only, pre-execution** (nothing built)
- bank of assignment: `437ab293e7` "Create RS-TECH-LEAD2 for WMSO" (SATOSHI HOSHINO, 2026-07-18 12:46:45 +0900)

This record is a **readback + pre-registered D0 scope**. It authorizes nothing to run. It separates
what I will *inventory* (factual, read-only) from what I will later *propose* (design, pN-verified).

---

## A. Assignment readback (what I understand my job to be)

**Role.** I am `T-ROOT-RS-TECH-LEAD2`, the development/design owner of **WMSO — World-Model-Based
Skill Orchestration**, the L0 integration architecture that connects the four Rs-mandated L0 means
(RL / IL / Vision / World Model) to a set of learned skills through **one algorithm-agnostic typed
skill-lifecycle contract**. WMSO selects/hands-off/recovers *skills*; it does **not** generate motor
commands and does **not** replace any skill's low-level controller. (charter §0/§1; node `T-WMSO`
state §2/§4)

**Owner separation (Rs direct 2026-07-18 12:44).**
| role | pane | duty |
|---|---|---|
| development / design | `w2:pQ` (me) | drive `T-WMSO` D0→…→V0 gate-by-gate |
| independent verify | `w2:pN` OPS-SUP-CODEX | evidence/design gate — I do **not** close my own |
| Vault / current-state custody | `w2:p6` PLAN-KEEPER | node/surface upkeep; I request, do not self-edit Vault state surfaces |
| grip gate chain (§DDR #18) | `w2:p4` RS-TECH-LEAD | continues grip; **released** from WMSO; WMSO D0 does not wait on grip checkpoint |

**Supersessions I carry forward.**
- **Name (Rs 2026-07-18 11:10):** `RT-WMSO`/`T-RT-WMSO` (initial bank `5ad800fa56`) → **`WMSO`/`T-WMSO`**
  is canonical. Dropping "Real-Time" from the name does **not** weaken the multi-rate / event-driven /
  deadline / safety acceptance (charter §4/§6 unchanged). (node §0)
- **Ownership (Rs 2026-07-18 12:44):** the 09:36 "p4 owns / wait on grip checkpoint" narrative is
  superseded; WMSO is owned here and starts D0 now. (node §0)

**pins-s1 verification (evidence, repo HEAD `437ab293e7`).**
- `node-T-ROOT-RS-TECH-LEAD2-pins-s1.sha256` → **5/5 OK** (`T-ROOT-RS-TECH-LEAD2/state.md`,
  `T-WMSO/state.md`, charter, `assignment-s1.md`, `operational-rule-LTM-1.md`); `sha256sum -c` rc=0.
- `node-T-WMSO-pins-s1.sha256` → **3/3 OK** (charter, `T-WMSO/state.md`, `operational-rule-LTM-1.md`); rc=0.
- charter `WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md` sha256 `e925e7a4f6dd…b0b79b657c` matches the
  pinned value in both files. **Provenance intact.**

---

## B. Boundary understanding (what stays UNAUTHORIZED — I will STOP + flag Rs if a task implies any)

Per charter §0/§8-4, node `T-WMSO` §0/§7, and assignment `Boundaries`:

1. ⛔ **Production control change** — no edit to the live control/orchestrator path.
2. ⛔ **Training launch** — no GPU training run.
3. ⛔ **WMSO inference launch** — no running WMSO in any control role.
4. ⛔ **Closed-loop authority** — WMSO takes no control; blocked until skill init/term/handoff
   contracts are stable (charter §5 last line) and S0/V0 each pass their own two-key.
5. ⛔ **Removal/modification of existing safety or orchestrator paths** — read-only only.
6. **Separation invariant (Rs verbatim "現 (d-b) route/pin は停止・混入させない"):** WMSO is kept
   **separate** from the current `(d-b)` route/pin implementation and from the `T-WM` classifier
   cascade; they connect through **explicit dependencies only**. Current route/pin work is an
   intra-skill prerequisite and is **not** paused by this node. (charter §1/§8-2; node §0)
7. **Algorithm-agnostic:** BC / BC+RL / PPO / DAPG are all treated by the **same** typed lifecycle
   contract. BC+RL lineage distinguishes BC checkpoint, RL fine-tune config, and final policy hash
   (same name + different lineage = different skill action). (charter §3)
8. **FOUNDATIONAL invariants (RS71 §0) — untouched by D0 (read-only):** DUAL-ARM · 88 mm grasp span /
   fixed bases · DiffIK-only · コ-shape gripper geometry LOCK · no-kinematic-trick. Any *design* that
   would change one of these is a premise change = Rs-sole = STOP-and-flag, never build-first.

**Self-gate rule I will hold:** development owner ≠ independent verifier. I will not mark my own D0
evidence or design "verified"; that verdict is pN's. Vault state-surface edits go through p6.

---

## C. D0 pre-registered inventory scope (fixed BEFORE execution so pN can verify against it)

**Deliverable of D0** = a *factual, read-only inventory* + a *separated architecture draft*, submitted
to pN for independent design verify (charter §5 "D0 exit = independent design verify"). This section
pre-registers exactly what will be inventoried, from where, by what method, and what "done" means.

**Method contract (applies to every row).**
- Every source recorded as **path + git commit/blob hash + read timestamp**.
- **Factual inventory** (what the code/doc *is*) is kept strictly separate from **proposed design**
  (what WMSO *should* add).
- **Unknown / unsupported / absent** surfaces are marked **fail-closed** — an explicit
  `ABSENT` / `UNVERIFIED` row, never a silent omission. (node §3)
- **No** code/param/spec change; **no** run. Pure `Read`/`Grep` over source + docs.

**The six inventory items (charter §8-3 / node §1), with pre-identified sources.**

| # | Inventory item | Pre-identified source surface (read-only) |
|---|---|---|
| 1 | Learned skills + policy lineage (BC / BC+RL / PPO / DAPG) | `skills/scripted_skills.py`, `skills/__init__.py`, `models/base_policy.py`, `models/skill_adapter.py`, `models/skill_adapter_with_prediction.py`, `scripts/bc_pretrain.py`, `scripts/bc_train_route.py`, `scripts/route_demo_to_bc.py`, `docs/DAPG_DESIGN.md`, trainer node define doc |
| 2 | Observation/action schema + vision-grounded belief inputs | `envs/newton_skill_env_base.py`, `envs/route_executor.py`, `models/*`, `configs/task_config.py` (obs/action dims); locate vision pipeline modules; flag vision-derived vs privileged sim state (gate ②) |
| 3 | Termination / failure / timeout signals + safe-interruption checkpoints | `skills/result.py`, `skills/scripted_skills.py`, `envs/route_executor.py`, `orchestrator/routing_orchestrator.py`, `training/dual_arm_skill_rewards.py`, `configs/task_config.py`; honor timeouts-contamination invariant (`prohibited.md`); safe-interruption checkpoints likely **ABSENT** → fail-closed |
| 4 | Skill Handoff State + transition / recovery / fallback contracts | `transforms/skill_transforms.py`, `orchestrator/routing_orchestrator.py`, `skills/snapshot.py`, `skills/step_table.py`; record handoff-state schema, accepted incoming-handoff set, recovery/fallback (may be partial → fail-closed) |
| 5 | Current `routing_orchestrator.py` behavior + existing safety path | `orchestrator/routing_orchestrator.py` (+ `orchestrator/__init__.py`, `tests/test_orchestrator_transforms.py`). **Path note:** actual path is `thread_isaac_lab/orchestrator/routing_orchestrator.py` (charter cites it path-less). Independent low-level safety monitor (charter §2.4) may be **ABSENT** → fail-closed flag |
| 6 | Per-event-class deadline candidates + measurable acceptance schema | charter §4/§6/§7; `configs/task_config.py` timing; physics dt (1/120 = 8.33 ms), substep config, env-step timing. Emit candidate `D_situation` + `T_detect+T_ground+T_select+T_handoff` decomposition **as PROPOSED design**, separated from factual |

**Mandatory reuse input (V11 / prior-art gate result).** `thread-vault/06-Knowledge/LL-WorldModel-Feasibility.md`
(2026-04-25 WM-candidate feasibility: Dreamer V3 / IRIS / MuZero / Diffusion-WM for skill-resolution
orchestrator policy) is a **reuse anchor**, not a NO_GO. It will be consulted before any Skill Dynamics
Model design proposal. V10 scan rc=0; no prior *failed* WMSO path exists — this is the node's first D0.

**D0 acceptance schema (what pN independent-verifies at D0 exit — node §3, charter §5/§6).**
- [ ] every input has path + commit/hash + read timestamp
- [ ] factual inventory separated from proposed design
- [ ] unknown/unsupported surfaces fail-closed (explicit ABSENT/UNVERIFIED)
- [ ] all four L0 means connected: **RL · IL · Vision · World Model** (charter §1)
- [ ] acceptance schema includes **worst-case latency, deadline-miss rate, OOD abstention,
      safety independence** (not mean latency alone; charter §6-⑦/⑧, gate ⑩ no-premature-claim)

**Explicitly out of D0 scope (deferred, unauthorized):** any code/param/spec edit, training, WMSO
inference, closed-loop authority, safety/orchestrator-path change, and touching p4's grip gate chain.

---

## D. [DEFER-RECON] dependency / DDR reconciliation

- **Node blockers (charter §6):** `T-Skill`, `T-Vision`, `T-WM`, `T-ROOT-optE-…-P2-trainer` are
  **integration / parallel-constraint** blockers, **not precedents** for D0 read-only inventory
  (charter §5: design/contract/offline-data may proceed in parallel; precedent = none). D0 mutates
  nothing, so none of them GATE D0.
- **DDR items (from LEDGER §DDR digest):** #18 grip-efficacy is **p4-owned, not mine** (separation
  invariant §B-6); #19 ENV-MULTIWORLD freeze, #12 fork-B V0, #2/#4 P2/P3 premises are **downstream
  constraints on training-ready / closed-loop** — already unauthorized here — **not D0 blockers**.
- **Preflight WARNs (non-blocking, noted):** 974 uncommitted (prior-session residue); stale locks
  (>1 h); NEST freshness D1 snapshot / D3 manifest stale. None affect read-only D0.

---

## E. Ask to pN (OPS-SUP-CODEX)

**Independent-verify this pre-registered D0 scope** (§C) — confirm the source set is complete, the
factual/design separation and fail-closed rule are sufficient, and the D0 acceptance schema matches
charter §5/§6 before I execute the inventory. Flag any missing surface or boundary risk. On PASS I
execute D0 read-only inventory and return the inventory + separated architecture draft for the actual
D0-exit design verify.
