# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO D0 architecture draft — §A–§I (design-only schema)

- node `T-WMSO`; author `w2:pQ` (RS-TECH-LEAD2); independent verify `w2:pN` (OPS-SUP-CODEX); Vault custody `w2:p6`.
- prepared_at: **2026-07-18 16:55 JST** · repo HEAD `c66659f487` (advisory).
- **authorization to author** = Rs direct 2026-07-18「§A–I authoring に入って」. Scope is pre-registered:
  scope prereg **v2** (sha256 `674a80f303ed2a5fc80b2917979c5975d1efd6088db345c2102f222149f3010a`, intact at HEAD) +
  arch-scope-v2 records-fix R1/R2 (`WMSO_D0_ARCH_SCOPE_V2_RECORDS_FIX_R1R2_20260718.md`). This draft = scope-v2 §B6 **step 2**.
- **grounding source of all FACTUAL rows** = D0 factual inventory **v4** (sha256 `2e96ea478bdd6c83b41a8980…`, banked `513948a15e`,
  pN substantive PASS-CLOSE). File:line citations below are carried through v4; this draft does not re-run the closure.
- **pN scope-CONCUR status**: scope v2 = pN **CONTENT PASS** (2026-07-18 16:05); R1/R2 records HOLD **discharged**
  (`bd1726d6d7`). No separate on-disk pN CONCUR stamp was located at author time; I proceed on **Rs direct instruction**
  (CLAUDE.md precedence: Rs direction > plan gate). The substantive independent design verify remains scope-v2 §B6 **step 5**
  (pN D0-exit), *after* this draft + `/pre-check`.

## ⛔ Boundaries and invariants (held; a schema draft changes none of them)
- **DESIGN-ONLY.** No code, no impl, no run, no gate PASS. ⛔ production control / training launch / WMSO inference /
  closed-loop authority / removal of any existing safety-or-orchestrator path / p4 grip scope — all UNAUTHORIZED (charter §0/§8-4).
- **FOUNDATIONAL invariants (RS71 §0) unchanged by this draft**: DUAL-ARM (both UR5e hold+manipulate every motion),
  88 mm two-EE grasp span / bases at Y=∓0.35, DiffIK-only control (no kinematic teleport), コ-shape gripper geometry LOCKED,
  no-kinematic-trick (only authorized exception = clip-retention pin). Any apparent change to these = **premise change = STOP → Rs**,
  not a design tradeoff. This draft designs an *orchestration schema above* the skills; it does not touch skill geometry/control.

## §0. Method, term definitions, and status vocabulary

**WMSO** = World-Model-Based Skill Orchestration: an L0 (whole-task) integration architecture that selects, sequences, hands off,
transitions between, and recovers **learned skills** using a **skill-resolution world model** and **vision-grounded belief**, while an
**independent safety layer** retains priority. WMSO does **not** generate motor commands and does **not** replace any skill's
low-level controller (charter §0).

**Skill** = one learned or scripted low-level behavior (e.g. APPROACH_CABLE) with its own policy and obs/action schema.
**Belief state** = the abstract, grounded state WMSO reasons over (skill resolution), distinct from a skill's raw env observation.
**Handoff state** = the declared state a skill leaves behind for the next skill to accept (charter §3), distinct from a physics snapshot.
**Skill Dynamics Model (SDM)** = the world model at *skill* resolution: predicts next-belief, duration, success/fail class, cost, uncertainty.
**D_situation** = the wall-clock deadline for an event class; **T_detect/T_ground/T_select/T_handoff** = the four latency terms that must sum below it.

Every row below is tagged with one status:

| tag | meaning |
|---|---|
| **FACTUAL** | present in code today; cited to inventory v4 §N + file:line |
| **DESIGN-ONLY** | proposed net-new contract/schema; evidence-pending; not implemented |
| **ABSENT** | `ABSENT_IN_DECLARED_CLOSURE` — the declared-closure query returned 0 (v4) |
| **UNVERIFIED** | not established either way in the closure |

**Factual / proposed separation is strict**: each of §A–§I opens with the FACTUAL current state (what exists), then the DESIGN-ONLY
schema (what is proposed), then the binding requirement it satisfies and the fail-closed treatment of unknowns.

**Reuse disposition** (scope v2 §B1, carried): Rs Option-α Cascade (measure-first staging) + Gate-4 maturity (skill_SR≥70% before
model/closed-loop) + SPlaTES skill-level WM (H<5) + model-exploitation guard + confidence-gated fast→slow + Cascading-P0/`StateSnapshot`
= **INCORPORATED**; IRIS/MuZero/World4RL/MoE-DP = **RETAINED-STOP**; Dreamer-V3-JAX = **RETAINED-rejected**; Cosmos latent WM =
**INCORPORATED-as-CAUTION** (detection reusable, recovery-generation = new, needs AUROC≥0.85 sim-shift calibration); scope-inflation
9-comp = **RETAINED NO-GO** (draft kept minimal). LL-Orchestration-Design = **PRECEDENT, NOT TRUTH** (reconciled vs inventory v4).

---

## §A. State / belief / goal schema

**FACTUAL current state** (v4 §0, §2, §7):
- Three surfaces exist, none asserted "live/active": **A** per-skill orchestrator env schemas (`routing_orchestrator.py` + 43 `StepDef`);
  **B** whole-route RL env code path 62D privileged obs (`newton_route_env.py _compute_obs_batch:1475-1587`, `route_env_config.py:45`) /
  6D alpha-residual action; **C** route runner 25/27D obs (`route_demo_to_bc.py:301`, `policy_route_runner.py:200-212`) / 6D action.
- **All 62 Surface-B dims are privileged/const — ZERO vision** (v4 §2). Vision modules (`vision_pipeline.py`, `visual_encoder.py`,
  `vision_obs_assembler.py` = `NotImplementedError` stub, `obs_builder.py` broken import) are **UNWIRED** to B/C.
- No monotonic clock, per-field provenance, per-field confidence, or OOD flag exists on any current obs vector (**inferred** from the
  privileged/const float-vector enumeration, v4 §2; the wall-clock-absence part is query-backed at v4 §6. This row is an inference from
  structure, not a dedicated field-structure closure grep, so per §0 it is **not** tagged `ABSENT`).

**DESIGN-ONLY proposed schema** — `BeliefState` as a set of typed `BeliefField`s (skill resolution, above raw obs):

| field of `BeliefField` | type / domain | purpose |
|---|---|---|
| `value` | scalar / vector | the grounded quantity |
| `provenance` | enum {`VISION_DERIVED`, `PRIVILEGED_SIM`, `SCRIPT_STATE`, `CONST`} | **mandatory per field** (pN B2) |
| `t_obs` | monotonic timestamp [s, single declared origin] | staleness reasoning; not sim-step count |
| `confidence` | [0,1] | belief confidence used by initiation predicates + abstention |
| `ood_flag` | bool | field is out-of-support / low-confidence |

`GoalContext` (pN B2 "add goal/task-context schema"): `{ target_clip ∈ {C1,C2,…}, route_phase_goal, goal_change_token, task_id }` —
a `goal_change_token` increments when the goal changes so the orchestrator (§D) can force a re-plan (charter §2.2 "replan after … events").

**Binding requirement folded (gate②, charter §6.2)**: any field with `provenance=PRIVILEGED_SIM` is **training/evaluation metadata only**
and is **forbidden as an undeclared production/closed-loop input**. The schema carries this as a hard field attribute
`prod_admissible: bool` that is `false` for every `PRIVILEGED_SIM` field. At closed-loop (V0, not now), belief selection must use
`VISION_DERIVED` fields; the current 100%-privileged vectors are admissible only for D0–S0 design/shadow, never for control authority.

**Fail-closed unknowns**: because vision is UNWIRED today, every production belief field is currently `ood_flag=true` by construction
(no in-support vision estimator exists). This is the correct fail-closed default and is the design driver for gate②/④; it is **not**
a claim that vision is present.

**Gate linkage**: ② vision grounding, ④ unknown-state abstention.

---

## §B. Unified skill lifecycle contract — keyed by **policy identity**

**FACTUAL current state** (v4 §1):
- Multiple **unreconciled** skill vocabularies: `SkillName` 9-type (5 RL: APPROACH_CABLE/CLAMP/INSERT_INTO_CLIP/UNCLAMP/AERIAL_REGRASP,
  3 scripted: TRANSPORT/RECLAMP_L/HALF_UNCLAMP_RELEASE, 1 wait: CLIP_CONFIRM) at `step_table.py:35-51` + `routing_orchestrator.py:71-81`;
  `SkillType` 7 RL at `skill_adapter.py:45-58`; `bimanual_*` 6 WM at `skill_adapter_with_prediction.py:150-157`.
- Families: per-skill RL = **DAPG** (LoRA on BC base; `train_common.py`/`train_grip.py`; AC/AR/IC wrappers **ABSENT**); base = **BC-only**
  (`train_base_model.py`); surface-C route = **BC actor-mean** (`bc_train_route.py`); surface-B whole-route = **RL residual** (RLPD *planned*,
  BC-independent; `TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md`); `bimanual_*` = WM+PPO.
- **Version hash: present** in `bc_train_route.py:117-135` + `policy_route_runner.py:35-46,456,622`; **absent** in
  `eval_skill.py`/`train_common.py`/`train_base_model.py` (v4 §1).

**DESIGN-ONLY proposed contract** — `SkillActionKey` (the identity a skill action is modeled/evaluated under):

- `policy_hash` — immutable hash of the exact policy weights. **NEVER key by skill-name alone** (pN B2). Two policies sharing a name but
  differing in lineage are **different skill actions** (charter §3).
- `lineage` — `{ family ∈ {BC, BC+RL, PPO, DAPG, scripted, wait}, base_ckpt_hash, finetune_cfg_hash, final_policy_hash }`. **BC+RL must
  distinguish** BC checkpoint hash, RL fine-tune config hash, and final policy hash (charter §3).
- `handoff_start_context` — the incoming handoff-state id + initiation context the policy was entered from (same policy from a different
  entry is tagged distinctly for modeling).

`SkillLifecycleContract` published per skill (charter §3 fields, all DESIGN-ONLY):
`skill_id`, `policy_family`, `SkillActionKey`; obs/action schema + `training_lineage`; `initiation_predicate` + `required_belief_confidence`;
termination classes `{success, failure, timeout, invalid_state}`; `progress_phase` + **`safe_interruption_checkpoints`** (see §E);
`SkillHandoffState` schema + `accepted_incoming_handoff_set`; `duration_cost_distribution` + `resource_requirements`;
`recovery_rollback_target` + `fail_closed_action`.

**Binding requirement folded (pN B2)**: every contract additionally carries **model version / freshness / support-boundary** for the
skill's *policy* (distinct from the SDM in §C) and a **fail-closed stale / out-of-support action**: if the running policy hash is not the
one the contract/model was calibrated against, the skill is `out_of_support` → the orchestrator (§D) must not treat SDM predictions about
it as valid → route to re-observe / recovery / safe-stop, never silent-accept.

**Fail-closed unknowns**: skills whose version hash is currently absent (v4 §1: `eval_skill.py`/`train_common.py`/`train_base_model.py`)
are `hash_unpinned` and are **inadmissible** as WMSO-selectable actions until D1 pins them (charter §5 D1 exit = hash-pinned lineage).
AC/AR/IC RL wrappers are **ABSENT** and cannot be listed as available actions.

**Gate linkage**: ① algorithm independence (same typed contract for BC+RL and RL-only), ⑩ no premature claim (contracts *registered*, not passed).

---

## §C. Skill Dynamics Model (SDM) — keyed by **model identity** (distinct from policy identity)

**FACTUAL current state** (v4 §8):
- **No skill-resolution dynamics model feeds Surface B or C.** The only WM present is `WorldModelEncoder`, which predicts a *latent* for the
  **separate** `bimanual_*` stack (v4 §8) — it is not a `(belief, skill, goal) → {next-belief, duration, class, cost, uncertainty}` predictor
  for the route skills. Transition distribution at skill resolution = **not established / UNVERIFIED**.

**DESIGN-ONLY proposed model** — `SkillDynamicsModel`:
- **Model identity** (kept explicitly distinct from §B policy identity, per R1/R2 authoring precision): `model_id`, `model_version`,
  `trained_on` (dataset hash + coverage), **`support_boundary`** (the region of `(belief, skill_action_key, goal)` it is calibrated on),
  `freshness` (max staleness before predictions are void).
- input `(belief_state, skill_action_key, goal_context)` → output distribution over `{ next_belief, duration, success_fail_class, cost,
  uncertainty }`.
- **skill-level transitions ONLY** — it must **not** claim low-level cable dynamics unless separately validated (charter §2.1).
- **bounded short rollout `H < 5`** (SPlaTES precedent, INCORPORATED).
- **calibration is per-skill AND per-handoff** — aggregate accuracy is explicitly insufficient (charter §6.3).
- **model-exploitation guard**: regularization / constraint on planning against the model so the orchestrator cannot exploit model error
  (INCORPORATED guard vs HMBRL-inferior finding).

**Binding requirement folded (pN B3)**: **duration and cost were not modeled in prior work (LL-WMF gap)** — they are **first-class outputs
here**, designed explicitly, not implied. The SDM's `duration`/`cost` outputs are required inputs to §D's continuation-vs-switching value.

**Fail-closed unknowns**: with no SDM today, every SDM query is `out_of_support` until M0 trains and calibrates one. The orchestrator (§D)
must treat "no calibrated SDM" as "planning unavailable" → bounded slow path degrades to safe-stop / hand back to the **existing
Surface-A heuristic retry-rollback engine** (`routing_orchestrator.py:1063-1214`; **not** the net-new Recovery Skill of §E), **never** a
confident model-based switch. Closed-loop use of the SDM is blocked until held-out + OOD calibration gates pass (charter §5 M0 exit).

**Gate linkage**: ③ model calibration (per-skill + per-handoff), ⑩ no premature claim.

---

## §D. Skill Orchestrator

**FACTUAL current state** (v4 §4, §5, §7):
- Surface A = **heuristic skill-chaining + retry/rollback recovery** (`routing_orchestrator.py execute_step:1063-1214`, retry≤3/rollback≤3),
  **single-world only** (`:799-809`). This is the baseline gate⑨ compares WMSO against.
- OOD gate = `bc_p0_region_check` **default-accept stub** (`:1152-1162`).
- **Continuation-vs-switching value comparison = ABSENT** (net-new; the current path chains by fixed step table, it does not compare values).
- **Skill-level anti-thrash = ABSENT** (v4 §7: the only dwell in code is `_c1_pin_dwell` pin-latch, unrelated).

**DESIGN-ONLY proposed orchestrator** (charter §2.2), the pipeline per decision point:
1. **candidate filter** — keep skills whose `initiation_predicate` holds AND whose safety predicate (from §F) permits, at the current belief.
2. **value comparison** — compute continuation value (keep current skill) vs switching value (best alternative) using SDM
   `{success, duration, cost, uncertainty}` (§C). **Net-new; absent in the reuse baseline.**
3. **select** the argmax-value admissible skill; **replan** on outcome, event, or `goal_change_token` change.
4. **arbitration — confidence-gated fast → slow** (INCORPORATED, Qwen<0.85→API precedent): known/high-confidence belief → **bounded fast
   path** (precomputed policy/Q lookup); uncertain / goal-changed / recovery → **bounded short-rollout slow path** (§C, H<5).
5. **anti-thrash** — switch penalty + hysteresis + minimum-dwell so oscillatory switching is suppressed under repeated disturbance (gate⑥).
6. **OOD abstention** — low-confidence / `ood_flag` belief **cannot force an ordinary skill choice**; it routes to re-observe / recovery /
   safe-stop. This design **supersedes the `default-accept` stub** (pN B4) at build time (not now — the existing stub is unchanged in D0).

**Binding requirement folded (R1/R2 authoring precision)**: the orchestrator **enforces model freshness / support** before trusting §C:
if SDM `freshness` is exceeded or the query is outside `support_boundary`, the model output is void → fall to the bounded slow path's
conservative branch or safe-stop; it does not act on a stale/out-of-support prediction.

**Fail-closed unknowns**: with no SDM (§C) and no value model yet, D0 specifies the *interfaces and predicates*; the value comparison is
**DESIGN-ONLY**. Until M0/O0, the orchestrator has **zero control authority** (charter §5 S0/V0 gating).

**Gate linkage**: ④ abstention, ⑥ anti-thrash, ⑨ comparative value.

---

## §E. Skill Transition Manager

**FACTUAL current state** (v4 §4):
- Handoff-state in code = physics **`StateSnapshot`** (`snapshot.py:19-31`) — a physics restore point, **not** a charter-§3
  skill-handoff-state contract.
- Surface B has `RouteInterfaceV1` + `reset_to_phase(k=0 stub)`.
- **Dedicated recovery / fallback SKILL = ABSENT** (v4 §4 exact grep → rc=1, 0 hits).
- **Safe-interruption checkpoint = ABSENT** (v4 §3 exact grep → 0 core hits).
- LL-ORCH Cascading-P0 hooks (`export_terminal_state` / `load_p0_from_cascade`) = **precedent**; their impl status is *not asserted*
  (precedent-not-truth; v4 confirms the concrete in-code handoff mechanism is the physics snapshot).

**DESIGN-ONLY proposed manager** (charter §2.3) — choose+execute exactly one of:
1. **direct handoff** at a compatible `SkillHandoffState` (next skill's `accepted_incoming_handoff_set` must contain the outgoing state);
2. a **Transition Skill** (a learned/scripted bridge when states are incompatible but bridgeable);
3. a **Recovery Skill** (net-new — must be designed; ABSENT today);
4. **re-observe or safe-stop** when no valid transition exists.

- **reuse**: the physics `StateSnapshot` mechanism (`snapshot.py`) is reused as the *state-capture substrate*; the Cascading-P0 export/load
  pattern is the *precedent* for terminal-state export. The **charter-§3 `SkillHandoffState` contract itself is net-new** (semantic handoff
  state ≠ raw physics snapshot).
- **declare safe-interruption checkpoints** (pN B5; ABSENT in v4): each skill's contract (§B) enumerates the belief phases at which a
  mid-skill switch is physics-safe; the manager may interrupt **only** at those, unless §F has already stopped/stabilized the system (gate⑤).

**Fail-closed unknowns**: no recovery skill and no declared checkpoints exist today, so the *only* fail-closed transition currently
realizable is **re-observe / safe-stop**. The design mandates that until recovery skills + checkpoints are supplied and tested, the
manager's default on any incompatible/uncertain transition is safe-stop, not an untested mid-skill switch. **Ownership note**: recovery
skills are *supplied* by the **§H `T-Skill`** dependency, not built by WMSO; charter §5 has no explicit recovery-skill production stage,
so the recovery-skill production stage is flagged an **open charter-sequencing item for pN** (do not assume D1 produces it).

**Gate linkage**: ⑤ safe interruption.

---

## §F. Independent safety monitor

**FACTUAL current state** (v4 §5):
- In-env guards: **static Z-clip** on the IK target (`newton_route_env.py:1189-1193`); **task-fault detect+terminate** (explosion
  `:1635-1640`, drop `:1653-1672` → `done`+`TERM_PENALTY=-10`).
- Surface-C runner guards: action clip (`policy_route_runner.py:229,808`) + **GUARD2** per-arm 3D 15 mm rate-limit (`GUARD2_M=0.015`, `:55,830`).
- SOMA `SafetyEnvelope` / `FallbackGuard` (`safety_envelope.py:8-11,116-126`, L1-3 measure-only / L4 residual-zero) = **UNWIRED to B/C**.
- **gate⑧ conclusion (v4 §5)**: **none of the above is an independent low-level real-time safety monitor** — they are target/action clips,
  reward/termination faults, and an unwired legacy envelope.

**DESIGN-ONLY proposed monitor** (charter §2.4):
- a **separately owned interface** (its own owner/module, not inside the orchestrator or the WM), running at the safety rate.
- **priority over WMSO**; it **does not wait on world-model inference**.
- authorized actions: immediate stop / hold / retract / force-limit.
- **acceptance = fault-injection independence proof**: the safety action still fires correctly when the SDM/orchestrator is **delayed,
  crashed, stale, or adversarially wrong** (pN B4 / charter §6.8). This is a *design contract*, tested at V-gates, not now.
- reuse: the SOMA `SafetyEnvelope` may seed the predicate set, but it must be **wired and made independent** — its current unwired,
  measure-only form does not satisfy §F.

**Fail-closed unknowns**: because no independent monitor is wired today, WMSO **cannot be granted any control authority** — the safety-independence
gate is unmet by construction. This is the hard blocker on S0→V0, correctly fail-closed.

**Gate linkage**: ⑧ safety independence.

---

## §G. Event detector + per-event deadline (separately owned from §F)

**FACTUAL current state** (v4 §6):
- Timing today = **sim-step counts, not wall-clock**: `DT=1/480 s`; `PHYSICS_STEPS_PER_RL=10` (`newton_route_env.py:404`) ⇒ ~20.83 ms/RL-step
  (~48 Hz); IK 100/30, VBD 20 (`newton_skill_env_base.py:97-99`); horizon `ROUTE_TERMINAL_STEPS=900` (`route_env_config.py:99`); per-skill
  100–300 (`task_config.py:378-383`).
- **Real-time / deadline constant = ABSENT** (v4 §6 split greps: no `latency|deadline|real-time|wall-clock|hertz` source hits; the only `Hz`
  is 2 unrelated derived-Hz prints). ⇒ charter §4 `D_situation` / `T_*` **must be DESIGNED**.

**DESIGN-ONLY proposed event + deadline schema** (charter §4):
- **event taxonomy**: `{ completion, failure, slip/contact-change, no-progress, OOD-state, checkpoint-arrival, deadline-risk }`.
- **frozen decisions the schema must fix** (pN B5): (a) **event priority + co-terminal resolution** — total order over simultaneous events
  (safety/failure > checkpoint > completion > progress); (b) **monotonic clock + single time origin** — one declared monotonic source, no
  sim-step proxy; (c) **detection-to-handoff completion definition** — the event is "handled" when the successor skill has *accepted* the
  handoff, not when detection fires; (d) **fallback / deadline-miss behavior** — on miss, hand to the cached-recovery/safe path.
- **three decision classes** (charter §4): Safety (independent monitor, §F) / Event-checkpoint (fast orchestrator path) / Deliberative
  (short WM rollout).
- **budget inequality**: for each event class, `T_detect + T_ground + T_select + T_handoff < D_situation` (all **DESIGN-ONLY**,
  per-class values evidence-pending — to be measured, not asserted).
- **acceptance metrics** (worst-case, not mean; charter §4/§6.7): p50 / p95 / p99 / **max** / **jitter** / **deadline-miss rate** /
  **fallback latency** / **safety-override latency**. Claim ceiling = **bounded soft/firm real-time**, **not hard real-time**
  (no bounded-execution evidence for OS/scheduler/memory/comms yet).

**Fail-closed unknowns**: no wall-clock deadline exists in code, so every `D_situation` is a **design target with no measurement yet**; the
draft records them as unresolved/evidence-pending and forbids any real-time *claim* until RT0 measures under contention.

**Gate linkage**: ⑦ real-time.

---

## §H. Bridge + explicit dependency interfaces / owners (connect, do **not** mix)

**FACTUAL current state** (v4 §0/§8; charter §1/§6): the four integration dependencies are `T-Skill`, `T-Vision`, `T-WM`, and the active
trainer/env path; the code baseline is the existing `routing_orchestrator.py`. Vision is UNWIRED (§A); the only WM in code is the
`bimanual_*` `WorldModelEncoder` (§C), which is **distinct** from the WMSO SDM and from the `T-WM` failure-classifier cascade.

**DESIGN-ONLY explicit dependency interfaces + owners**:

| dependency | owner node | interface WMSO consumes | reuse-vs-new | mix guard |
|---|---|---|---|---|
| **T-Skill** | skill supply | `SkillLifecycleContract` + `SkillActionKey` per skill (§B) | contract = NEW; skills reuse existing BC/DAPG/RLPD policies | WMSO does not train or alter skills; consumes their published contract |
| **T-Vision** | belief grounding | `BeliefField{provenance,confidence,ood_flag,t_obs}` for `VISION_DERIVED` fields (§A) | vision pipeline = to-be-wired (currently `NotImplementedError`) | WMSO consumes belief; it does not implement the encoder |
| **T-WM** | skill-resolution WM | SDM `(belief,skill,goal)→dist` (§C) | SDM = NEW; **kept DISTINCT from the `T-WM` classifier cascade** | classifier cascade ≠ SDM; connect by explicit call, never merge state |
| **trainer (RLPD path)** | `…-P2-trainer` | policy hashes + lineage into `SkillActionKey`; env schema | reuse existing planned RLPD residual-on-script path | WMSO does not launch training (boundary held) |

**Binding requirement folded (charter §8-2, Rs「現 (d-b) route/pin は停止・混入させない」)**: the current **(d-b) route/pin** implementation
and the **`T-WM` classifier cascade** are connected to WMSO **by explicit dependency only** and are **not mixed** into WMSO state. The
current route/pin work is an intra-skill prerequisite and is **not paused** by this node.

**Gate linkage**: ① algorithm independence, plus the separation invariant.

---

## §I. Ten-gate crosswalk + measurement + evaluation (every row DESIGN-ONLY / evidence-pending)

**One row per charter §6 gate → schema surface + acceptance** (no gate PASS is claimed; D0 *registers* the contract):

| # | gate | schema surface (§) | acceptance (DESIGN-ONLY) | D0 status |
|---|---|---|---|---|
| 1 | algorithm independence | §B, §H | BC+RL and RL-only skills accepted through one `SkillLifecycleContract` | contract registered; unresolved |
| 2 | vision grounding | §A | control belief uses `VISION_DERIVED` fields; `PRIVILEGED_SIM` `prod_admissible=false` | vision UNWIRED → evidence-pending |
| 3 | model calibration | §C | per-skill **and** per-handoff calibration error bounds; aggregate insufficient | no SDM yet → evidence-pending |
| 4 | unknown-state abstention | §A, §D | `ood_flag`/low-conf → re-observe/recovery/stop; no default-accept | stub to be replaced; evidence-pending |
| 5 | safe interruption | §B, §E | switch only at declared `safe_interruption_checkpoints`; compatibility sets tested | checkpoints ABSENT → evidence-pending |
| 6 | anti-thrashing | §D | switch-penalty + hysteresis + min-dwell; tested under repeated disturbance | ABSENT → evidence-pending |
| 7 | real-time | §G | per-class deadline-miss + max + fallback latency under contention; soft/firm only | no wall-clock deadline → evidence-pending |
| 8 | safety independence | §F | safety fires under model/orchestrator delay/crash/stale/adversarial | no independent monitor wired → evidence-pending |
| 9 | comparative value | §D, §I | beat baselines on task+recovery SR without safety regression | four-baseline plan (below); evidence-pending |
| 10 | no premature claim | §0 boundaries | D0–M0 ≠ training-ready/closed-loop; S0/V0 need own two-key | held; boundary invariant |

**Gate-9 four-baseline plan** (pN B5): compare **(1) fixed chain** (current step-table order, no value comparison) · **(2) current
heuristic recovery** (Surface-A retry/rollback, `routing_orchestrator.py:1063-1214`) · **(3) boundary-only WMSO** (switch only at checkpoints,
no real-time event path) · **(4) event-driven WMSO** (full multi-rate, deadline-bounded profile). Metric = task SR + recovery SR + safety
interventions; WMSO must beat (1)+(2) **without** safety regression (charter §5 O0 exit).

**Charter §7 measurement / stress matrix** (DESIGN-ONLY; to be *measured*, never asserted):
- **measurements**: task SR, recovery SR, direct-handoff SR, Transition-Skill SR, safe-stop rate, unnecessary-switch rate, thrash rate,
  OOD-abstention precision/recall, model calibration error, predicted-vs-actual duration/cost, event-to-decision max latency, event-to-handoff
  max latency, deadline-miss rate, independent-safety-intervention count.
- **stress cases**: long-duration skills, contact/slip disturbance, target movement, corrupted/delayed vision, unseen abstract states,
  repeated switching pressure, slow WM inference, process failure, stale SDM data.

**Every D0 row is DESIGN-ONLY** with status ∈ {unresolved, evidence-pending, ABSENT, held}; **no gate is PASSED here**. D0's deliverable is
the *schemas + event-deadline design*, which then goes to its own D0-exit independent design verify (charter §5 D0 exit).

---

## Disposition and next steps (scope-v2 §B6 order)

- This draft = **step 2** (author §A–§I). It covers all 10 charter gates, holds every boundary/invariant, keeps FACTUAL (inventory v4) and
  DESIGN-ONLY strictly separated, keys **policy identity (§B) distinct from model identity (§C)**, and marks every unknown fail-closed.
- **Next**: step 3 = `/pre-check` on this own artifact (design failure-mode / deadlock / rule-violation scan) → step 4 = architecture-draft
  **bank** (via p6 custody) → step 5 = **pN D0-exit independent design verify** (charter §5 D0 exit condition).
- ⛔ Unchanged and UNAUTHORIZED until each own gate: production control / training launch / WMSO inference / closed-loop authority /
  removal of any safety-or-orchestrator path / p4 grip scope. FOUNDATIONAL invariants (RS71 §0) untouched by this schema draft.
