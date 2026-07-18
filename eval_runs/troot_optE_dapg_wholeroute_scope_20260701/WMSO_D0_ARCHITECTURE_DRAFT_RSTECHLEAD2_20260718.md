# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO D0 architecture draft — §A–§I (design-only schema) **v4**

- node `T-WMSO`; author `w2:pQ` (RS-TECH-LEAD2); independent verify `w2:pN` (OPS-SUP-CODEX); Vault custody `w2:p6`.
- prepared_at: **v1 16:55** (`4baf5b2650`) · **v2 17:35** (`51e0a1c0bf`) · **v3 18:35** (`e563c87869`) · **v4 2026-07-18 ~18:5x JST** (this) per pN reverify round-2 HOLD (B7a exit-union + B6 pre-check-on-final-sha).
- **authorization to author** = Rs direct 2026-07-18「§A–I authoring に入って」. Scope pre-registered: scope prereg **v2**
  (sha256 `674a80f303ed2a5fc80b2917979c5975d1efd6088db345c2102f222149f3010a`, intact at HEAD) + arch-scope-v2 records-fix R1/R2
  (`WMSO_D0_ARCH_SCOPE_V2_RECORDS_FIX_R1R2_20260718.md`). This draft = scope-v2 §B6 **step 2**.
- **grounding source of all FACTUAL rows** = D0 factual inventory **v4** (sha256 `2e96ea478bdd6c83b41a8980…`, banked `513948a15e`,
  pN substantive PASS-CLOSE). File:line citations are carried through v4; this draft does not re-run the closure.
- **pN scope-CONCUR status (corrected per pN B6)**: scope v2 = pN **CONTENT PASS** (16:05) → **scope PASS-CLOSE / CONCUR issued 16:12**
  (relayed to p6; R1/R2 records HOLD **discharged** `bd1726d6d7`). Authoring therefore proceeded **post-CONCUR** (Rs direct go **and** pN
  concur both present). The prior header's "no CONCUR located" note was stale and is **retracted**.
- **Revision log**: **v1** (`4baf5b2650`) → **pN verify = HOLD B1–B6** (~17:24–17:31, **coarse/unverified**; see
  `WMSO_D0_EXIT_VERIFY_VERDICT_OPSSUP_20260718.md`, a **pQ transcription**, not pN-authored) → **v2** (`51e0a1c0bf`, B1–B6 discharged) →
  **pN REVERIFY = HOLD** (18:11: **B1–B5 PASS-CLOSE** + T-WMSO-SDM design CLOSE; new B7/B6/B8) → **v3** (`e563c87869`, B7 transition schema +
  atomic owner transfer + B6/B8) → **pN REVERIFY round-2 = HOLD** (18:49: **B1–B5 + B8 PASS-CLOSE**, **B7 atomic-transfer PASS**; residual
  **B7a** = `terminal_class` can't express a mid-skill safe-checkpoint interrupt → `TERMINAL | INTERRUPT` union; **B6** = pre-check must run on the
  *final* sha) → **v4 (this)** adds the `TERMINAL | INTERRUPT` outcome union (§E, B7a) and re-runs the D0-exit `/pre-check` — **its verdict + the
  pre-checked sha are in the banked pre-check record, not asserted in this draft**. **pN PASS axes** (B1–B5, B8, atomic transfer, boundaries, identity separation, 10-gate map, measurement/stress) unchanged.

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
**D_situation** = the wall-clock deadline for an event class; orchestrator classes budget `T_detect+T_ground+T_select+T_handoff < D_situation`,
while the **Safety class uses its own `T_detect_safety + T_override < D_safety`** (§G, pN B1).

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
  privileged/const float-vector enumeration, v4 §2; the wall-clock-absence part is query-backed at v4 §6. Inference from structure, not a
  dedicated field-structure closure grep, so per §0 it is **not** tagged `ABSENT`).

**DESIGN-ONLY proposed schema** — `BeliefState` = a `schema_version`-stamped set of typed `BeliefField`s (skill resolution, above raw obs).
Each `BeliefField` is the **full typed record** (pN B2 — value-alone is not interoperable):

| attribute | type / domain | purpose |
|---|---|---|
| `field_id` | stable canonical id (enum) | interoperable key across surfaces (never a positional index) |
| `semantic` | text | human-readable meaning |
| `dtype` / `shape` | e.g. `float32` / `[3]` | typed layout |
| `unit` | SI: `[m]`,`[rad]`,`[m/s]`,`[N]`,`[N·m]`, dimensionless | physical unit (AGENTS.md SI rule) |
| `frame` | `world` \| `robot_base` \| `EE_L`/`EE_R` \| `clip` \| `N/A` | coordinate frame of `value` |
| `value` | per `dtype`/`shape` | the grounded quantity |
| `provenance` | enum {`VISION_DERIVED`,`PRIVILEGED_SIM`,`SCRIPT_STATE`,`CONST`} | **mandatory per field** (pN B2) |
| `prod_admissible` | bool | `false` for every `PRIVILEGED_SIM` field (gate②) |
| `t_obs` | monotonic timestamp `[s]`, single declared origin | staleness reasoning; not a sim-step count |
| `age` / `ttl` / `validity` | `age=now−t_obs`; `ttl`=max age; `validity=(age≤ttl ∧ ¬ood_flag)` | freshness gate consumed by §D/§G |
| `confidence` | `[0,1]` | belief confidence used by initiation predicates + abstention |
| `ood_flag` | bool | field out-of-support / low-confidence |
| `schema_version` | semver | belief-schema version (mismatch ⇒ fail-closed) |

**Canonical `BeliefState` content grouping** (pN B2 — minimum D0 groups the SDM/orchestrator reason over; concrete per-dim table = D1):
- **cable**: both grasp-point positions `[m, world]`, cable crossing/seat state at C1/C2, `held`/`dropped` flag.
- **arms/EE**: `EE_L`/`EE_R` wrist-flange pose `[m, rad]`, gripper open/close state.
- **task/clip**: C1/C2 seat state, pin/latch state, current route phase (G1–G6), `phase_progress`.
- **meta**: per-field `provenance`/`confidence`/`ood_flag`/`validity` (above).

**A/B/C adapter map** (pN B2 — each surface publishes an adapter into the canonical schema; the *contract* is D0, the *per-dim table* is D1):

| surface | raw obs | adapter → canonical | provenance tag |
|---|---|---|---|
| **A** per-skill env | per-skill schemas (`routing_orchestrator.py` + 43 `StepDef`) | per-skill subset → cable/arms/task groups | `PRIVILEGED_SIM`/`SCRIPT_STATE` (`prod_admissible=false`) |
| **B** whole-route | 62D privileged (`_compute_obs_batch:1475-1587`) | 62D → canonical, all privileged | `PRIVILEGED_SIM` (`prod_admissible=false`) |
| **C** route runner | 25/27D (`route_demo_to_bc.py:301`) | 25/27D → canonical subset | `PRIVILEGED_SIM`/`SCRIPT_STATE` |

`GoalContext` (pN B2 goal/task-context schema): `{ task_id, target_clip ∈ {C1,C2,…}, route_phase_goal, goal_change_token }` —
`goal_change_token` increments on goal change so the orchestrator (§D) forces a re-plan (charter §2.2 "replan after … events").

**Binding requirement folded (gate②, charter §6.2)**: any field with `provenance=PRIVILEGED_SIM` is **training/evaluation metadata only**,
carried as `prod_admissible=false`, and **forbidden as an undeclared production/closed-loop input**. At closed-loop (V0, not now), belief
selection must use `VISION_DERIVED` fields; the current 100%-privileged vectors are admissible only for D0–S0 design/shadow.

**Fail-closed unknowns**: because vision is UNWIRED today, every production belief field is currently `ood_flag=true` / `validity=false`
by construction (no in-support vision estimator exists). Correct fail-closed default; drives gate②/④. Not a claim that vision is present.

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

**DESIGN-ONLY proposed contract** — `SkillActionKey` (the identity a skill action is modeled/evaluated under). **NEVER key by skill-name
alone** (charter §3); the key carries a **discriminated `ExecutableIdentity`** (pN B3 — scripted/wait skills have no policy weights):

- `ExecutableIdentity` = **one of** (tagged union on `kind`):
  - `kind=LEARNED` → `{ policy_weight_hash, lineage{ family ∈ {BC,BC+RL,PPO,DAPG}, base_ckpt_hash, finetune_cfg_hash, final_policy_hash } }`.
    **BC+RL must distinguish** BC checkpoint / RL fine-tune config / final policy hash (charter §3). Same name, different lineage = different action.
  - `kind=SCRIPTED` → `{ source_hash, config_or_schedule_hash }` (no weights; the script source + its config/schedule are the identity).
  - `kind=WAIT` → `{ wait_config_hash }`.
- `handoff_start_context` — the incoming handoff-state id + initiation context the action was entered from (same executable from a
  different entry is tagged distinctly for modeling).
- All three `kind`s flow through the **one** `SkillLifecycleContract` below (gate① algorithm independence — the contract is uniform;
  only the identity discriminant differs).

`SkillLifecycleContract` published per skill (charter §3 fields, all DESIGN-ONLY):
`skill_id`, `policy_family`, `SkillActionKey` (with `ExecutableIdentity`); obs/action schema + `training_lineage`; `initiation_predicate` +
`required_belief_confidence`; termination classes `{success, failure, timeout, invalid_state}`; `progress_phase` +
**`safe_interruption_checkpoints`** (see §E); `SkillHandoffState` schema (**typed body in §E**, pN B7) + `accepted_incoming_handoff_set`;
`duration_cost_distribution` + `resource_requirements`; `recovery_rollback_target` + `fail_closed_action`.

**Binding requirement folded (pN B2)**: every contract additionally carries **policy version / freshness / support-boundary** for the
skill's *policy* (distinct from the SDM in §C) and a **fail-closed stale / out-of-support action**: if the running policy identity is not
the one the contract/model was calibrated against, the skill is `out_of_support` → the orchestrator (§D) must not treat SDM predictions
about it as valid → route to re-observe / recovery / safe-stop, never silent-accept.

**Fail-closed unknowns**: skills whose version hash is currently absent (v4 §1: `eval_skill.py`/`train_common.py`/`train_base_model.py`)
are `hash_unpinned` and **inadmissible** as WMSO-selectable actions until D1 pins them (charter §5 D1 exit = hash-pinned lineage).
AC/AR/IC RL wrappers are **ABSENT** and cannot be listed as available actions.

**Gate linkage**: ① algorithm independence (uniform contract for LEARNED/SCRIPTED/WAIT), ⑩ no premature claim (contracts *registered*, not passed).

---

## §C. Skill Dynamics Model (SDM) — keyed by **model identity** (distinct from policy identity)

**FACTUAL current state** (v4 §8):
- **No skill-resolution dynamics model feeds Surface B or C.** The only WM present is `WorldModelEncoder`, which predicts a *latent* for the
  **separate** `bimanual_*` stack (v4 §8) — it is not a `(belief, skill, goal) → {next-belief, duration, class, cost, uncertainty}` predictor
  for the route skills. Transition distribution at skill resolution = **not established / UNVERIFIED**.

**DESIGN-ONLY proposed model** — `SkillDynamicsModel` (owned by the proposed `T-WMSO-SDM` child, §H/§I):
- **Model identity** (kept explicitly distinct from §B policy identity): `model_id`, `model_version`, `trained_on` (dataset hash + coverage),
  **`support_boundary`** (the region of `(belief, skill_action_key, goal)` it is calibrated on), `freshness` (max staleness before void).
- input `(belief_state, skill_action_key, goal_context)` → output distribution over `{ next_belief, duration, success_fail_class, cost,
  uncertainty }`.
- **skill-level transitions ONLY** — must **not** claim low-level cable dynamics unless separately validated (charter §2.1).
- **bounded short rollout `H < 5`** (SPlaTES precedent, INCORPORATED).
- **calibration per-skill AND per-handoff** — aggregate accuracy explicitly insufficient (charter §6.3).
- **model-exploitation guard**: regularization / constraint on planning against the model so the orchestrator cannot exploit model error.

**Binding requirement folded (pN B3-inventory)**: **duration and cost were not modeled in prior work (LL-WMF gap)** — they are **first-class
outputs here**, designed explicitly. The SDM's `duration`/`cost` outputs are required inputs to §D's continuation-vs-switching value.

**Fail-closed unknowns (pN B5)**: with no SDM today, every SDM query is `out_of_support` until M0 trains and calibrates one. Because **both**
the fast and slow orchestrator paths consume the SDM, "no calibrated SDM" **voids both model-dependent decisions** (see §D): the orchestrator
may then only **re-observe**, **hand control to an explicitly compatible still-owning existing controller** (only under a **verified
handoff/ownership precondition** — the Surface-A heuristic is *not* inherently safe, it carries a default-accept OOD stub), or **safe-stop**.
Never a confident model-based switch. Closed-loop use of the SDM is blocked until held-out + OOD calibration gates pass (charter §5 M0 exit).

**Gate linkage**: ③ model calibration (per-skill + per-handoff), ⑩ no premature claim.

---

## §D. Skill Orchestrator

**FACTUAL current state** (v4 §4, §5, §7):
- Surface A = **heuristic skill-chaining + retry/rollback recovery** (`routing_orchestrator.py execute_step:1063-1214`, retry≤3/rollback≤3),
  **single-world only** (`:799-809`). This is the baseline gate⑨ compares WMSO against.
- OOD gate = `bc_p0_region_check` **default-accept stub** (`:1152-1162`).
- **Continuation-vs-switching value comparison = net-new / not-present** (inference from the fixed step-table chaining fact, v4 §4/§5;
  not a dedicated closure grep, so per §0 not tagged `ABSENT`).
- **Skill-level anti-thrash = ABSENT** (v4 §7: the only dwell in code is `_c1_pin_dwell` pin-latch, unrelated).

**DESIGN-ONLY proposed orchestrator** (charter §2.2), the pipeline per decision point:
1. **candidate filter** — keep skills whose `initiation_predicate` holds AND whose safety predicate (from §F) permits, at the current belief.
2. **value comparison** — continuation value (keep) vs switching value (best alternative) from SDM `{success, duration, cost, uncertainty}`
   (§C). **Net-new; absent in the reuse baseline.**
3. **select** the argmax-value admissible skill; **replan** on outcome, event, or `goal_change_token` change.
4. **arbitration — confidence-gated fast → slow** (INCORPORATED, Qwen<0.85→API precedent): known/high-confidence belief → **bounded fast
   path** (precomputed policy/Q lookup); uncertain / goal-changed / recovery → **bounded short-rollout slow path** (§C, H<5).
5. **anti-thrash** — switch penalty + hysteresis + minimum-dwell so oscillatory switching is suppressed under repeated disturbance (gate⑥).
6. **OOD abstention** — low-confidence / `ood_flag` / `validity=false` belief **cannot force an ordinary skill choice**; it routes to
   re-observe / recovery / safe-stop. This design **supersedes the `default-accept` stub** (pN B5 / gate④) at build time (not now — stub unchanged in D0).

**Binding requirement folded (R1/R2 + pN B5) — stale/out-of-support SDM**: the orchestrator **enforces model freshness / support** before
trusting §C. If SDM `freshness` is exceeded or the query is outside `support_boundary`, **both** the fast path (precomputed policy/Q) **and**
the slow path (short rollout) are model-dependent and are therefore **both voided** — the orchestrator must **not** fall from the fast path
onto the slow path (the naive "fall to the slow path" is self-contradictory: the slow path also uses the SDM). The only admissible actions
are then: (i) **re-observe** for fresh belief; (ii) **hand to an explicitly compatible still-owning existing controller** under a **verified
handoff/ownership precondition** (a controller that currently owns control and whose handoff-state is compatible — Surface-A heuristic is
*not* inherently safe, default-accept OOD, so handback requires this precondition); else (iii) **safe-stop**.

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
- LL-ORCH Cascading-P0 hooks (`export_terminal_state` / `load_p0_from_cascade`) = **precedent**; impl status *not asserted*
  (precedent-not-truth; v4 confirms the concrete in-code handoff mechanism is the physics snapshot).

**DESIGN-ONLY proposed manager** (charter §2.3) — choose+execute exactly one of:
1. **direct handoff** at a compatible `SkillHandoffState` (next skill's `accepted_incoming_handoff_set` must contain the outgoing state);
2. a **Transition Skill** (a learned/scripted bridge when states are incompatible but bridgeable);
3. a **Recovery Skill** (net-new — must be designed; ABSENT today);
4. **re-observe or safe-stop** when no valid transition exists.

**`SkillHandoffState` — the typed transition schema** (pN B7; charter §5 D0 requires a *transition* schema, not just its name):

| field | type | purpose |
|---|---|---|
| `handoff_state_id` | stable id | identity of this handoff state |
| `schema_version` | semver | version; mismatch ⇒ fail-closed reject |
| `producer` | `{ SkillActionKey (§B), outcome }`, `outcome` = **`TERMINAL{ terminal_class ∈ {success,failure,timeout,invalid_state}; checkpoint_id: nullable }` \| `INTERRUPT{ checkpoint_id: mandatory; interrupt_reason ∈ {planned_switch, event, safety_stabilized} }`** | producing action + its **tagged outcome** (pN B7a — does **not** fake terminal): a *terminal* end **or** a mid-skill **safe-checkpoint interrupt** (skill NOT terminated, resumable). `compatibility` + fail-close apply to **both** variants |
| `belief_ref` | `{ canonical BeliefState snapshot \| ref-hash, t_obs [monotonic], ttl, confidence, ood_flag }` | grounded state at handoff (§A canonical belief); stale/OOD ⇒ fail-closed |
| `ownership` | `{ contact_ownership, resource_ownership, control_ownership (per-EE EE_L/EE_R + gripper) }` | which physical / compute resources are held |
| `compatibility` | `{ compatibility_predicate, predicate_version, next_owner }` | who may accept and under what predicate |

(**Outcome union — pN B7a**: a `TERMINAL` outcome *ends* the producer (its `checkpoint_id` is nullable); an `INTERRUPT` outcome is a
**resumable** pause at a declared safe-interruption checkpoint (§B `safe_interruption_checkpoints` / gate⑤; `checkpoint_id` **mandatory**,
`interrupt_reason ∈ {planned_switch, event, safety_stabilized}` — planned skill switch, an external event, or a safety-stabilized handback).
The skill is **not** terminated; the manager may hand off and later **resume** the interrupted producer from its `checkpoint_id`. `belief_ref`
+ `ownership` are captured identically and `compatibility` + fail-close apply to **both** variants; the earlier terminal-only `terminal_class`
could not express a mid-skill safe interrupt.)

**Transition protocol + atomic owner transfer** (pN B7) — an `offer → accept → commit | abort` state machine with explicit `ack`:
1. producer emits `offer(SkillHandoffState)`;
2. the candidate `next_owner` evaluates `compatibility_predicate@predicate_version`: satisfied → `accept` + `ack`, else → `reject`;
3. on `accept` → the **Skill Transition Manager — the single authoritative writer of `control_ownership`** — performs `commit` = **one atomic
   token flip** of that manager-owned field (both producer and `next_owner` merely *observe* it; the concrete primitive — CAS/lock — is a D1
   refinement): thus **exactly one owner at every instant — no double-owner interval and no owner-gap interval**; if the flip cannot complete → `abort`;
4. **fail-closed**: `reject`, `abort`, or `timeout` (no `accept` within the handoff deadline, §G) → the **producer retains ownership and
   safe-stops (or re-observes)** — control is never released into a vacuum and never duplicated.

(**Reconciliation with §G**: §G's "handled = successor accepted" endpoint denotes the **commit-completed** state — the manager's atomic flip
immediately follows a valid `accept` as one primitive, so accept/commit are a single step from the deadline's view; an `abort` reverts to
producer-retains and the event is **not** counted handled.)

**Transition & Recovery skills are ordinary skills** (pN B7): each follows the **same §B `ExecutableIdentity` + `SkillLifecycleContract`**
(keyed by the discriminated identity, published through the one contract) — not a privileged side-channel.

- **reuse**: the physics `StateSnapshot` mechanism (`snapshot.py`) is reused as the *state-capture substrate*; the Cascading-P0 export/load
  pattern is the *precedent* for terminal-state export. The **charter-§3 `SkillHandoffState` contract itself is net-new** (semantic handoff
  state ≠ raw physics snapshot).
- **declare safe-interruption checkpoints** (pN B5-inventory; ABSENT in v4): each skill's contract (§B) enumerates the belief phases at which
  a mid-skill switch is physics-safe; the manager may interrupt **only** at those, unless §F has already stopped/stabilized the system (gate⑤).

**Fail-closed unknowns + sequence (pN B4)**: no recovery skill and no declared checkpoints exist today, so the *only* fail-closed transition
currently realizable is **re-observe / safe-stop**, which is the manager's default on any incompatible/uncertain transition (never an untested
mid-skill switch). Transition/Recovery skills are *supplied* by the **§H `T-Skill`** dependency, **not** built by WMSO. Rather than leave this
an open item, D0 places a **Transition/Recovery supply-readiness checkpoint** explicitly in the adoption sequence (§I): it **gates
D2/O0/V0** — any consumer proceeds only when the required Transition/Recovery skills exist and are contract-tested (D1 hash-pinned); while
**unavailable ⇒ the consuming path is safe-stop**. This removes the deadlock (a consumer cannot silently depend on an absent recovery skill).

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

**DESIGN-ONLY proposed monitor** (charter §2.4) — a **separately owned interface** (own owner/module, **not** inside the orchestrator or the
WM), running at the safety rate, with **priority over WMSO** and **no wait on world-model inference**. Full schema (pN B2 — not only an action list):

| element | schema | note |
|---|---|---|
| `SafetyObservation` | raw low-level signals read directly (not via belief/WM): F/T, EE velocity, cable-tension proxy, near-contact/penetration, NaN/explosion flag, grip-loss | independent sensing path |
| `SafetyEvent` | `{ type ∈ {force_limit, velocity_limit, penetration, explosion, nan, grip_loss}, severity ∈ {warn, critical}, t_detect }` | detected hazard |
| `SafetyDecision` | `{ action ∈ {STOP, HOLD, RETRACT, FORCE_LIMIT}, reason, severity, t_issue }` | action + **reason + severity** |
| `heartbeat / health` | periodic heartbeat + `health ∈ {ok, degraded, failed}` | missed heartbeat ⇒ consumers must **not** assume safety alive; monitor `failed` ⇒ system fails to **safe-stop** |
| `preemption / ack` | monitor **preempts** WMSO; WMSO must `ack` + yield; **preemption acts first, does not wait for ack** | one-way authority |
| `stabilized_post_action_state` | the declared safe state after a safety action | lets §D reason about resumption eligibility |
| `response_budget` + `owner_interface` | `D_safety` detect-to-override (§G); separately-owned module interface | worst-case, not mean |

- **acceptance = fault-injection independence proof**: the safety action still fires correctly when the SDM/orchestrator is **delayed,
  crashed, stale, or adversarially wrong** (pN B4 / charter §6.8). Design contract; tested at V-gates, not now.
- reuse: the SOMA `SafetyEnvelope` may seed the predicate set, but must be **wired and made independent** — its current unwired,
  measure-only form does not satisfy §F.

**Fail-closed unknowns**: because no independent monitor is wired today, WMSO **cannot be granted any control authority** — the safety-independence
gate is unmet by construction. Hard blocker on S0→V0, correctly fail-closed.

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

- **event taxonomy** (7): `completion, failure, slip/contact-change, no-progress, OOD-state, checkpoint-arrival, deadline-risk`.
- **deterministic total order across the FULL taxonomy** (pN B1 — **independent safety override above all**). Tiers, high→low:
  **T0 independent safety override (§F) — dominates everything** > **T1 hazard** `failure` > `slip/contact-change` > **T2 time** `deadline-risk`
  > **T3 epistemic** `OOD-state` > **T4 transition** `checkpoint-arrival` > `completion` > **T5 progress** `no-progress`.
  **Tie / co-terminal rule** (same step): higher tier wins; **within a tier**, break ties by (i) earliest `t_detect` (monotonic), then
  (ii) the fixed enum order above — fully deterministic. Safety-override (T0) is evaluated first and can preempt any lower tier. (Note: T2
  `deadline-risk` and T3 `OOD-state` both resolve to a *safe* fallback — cached-safe path / abstain-to-safe — so their relative order only
  selects which safe path is taken, never a model-based choice.)
- **monotonic clock + single time origin**: one declared monotonic source (e.g. `CLOCK_MONOTONIC`), origin = process/episode start; **no
  sim-step proxy**.
- **detection→handoff completion definition**: an event is "handled" when the successor skill has **accepted** the handoff (not when
  detection fires).
- **three decision classes + provisional deadline budgets** (pN B1 — **provisional numeric upper bounds, DESIGN-ONLY / evidence-pending,
  to be *measured* at RT0, NOT claims of achieved latency**; @~48 Hz control ⇒ 1 RL-step ≈ 20.83 ms, 1 physics-step ≈ 2.08 ms):

| class | owner | **budget formula** | **provisional D upper bound** | start → end measurement points | miss action |
|---|---|---|---|---|---|
| **Safety** | independent monitor (§F) | `T_detect_safety + T_override < D_safety` (**own detect-to-override budget, NOT the 4-term formula**) | `D_safety ≤ 20 ms` (~1 control step; ideally physics-rate ~2 ms) | raw triggering-sample `t` → safety actuator command issued | escalate to hardest safe action (STOP) |
| **Event-checkpoint** | event monitor + fast orchestrator path | `T_detect + T_ground + T_select + T_handoff < D_event` | `D_event ≤ 100 ms` (~5 control steps) | event `t_detect` → successor accepts handoff | cached-recovery / safe-stop |
| **Deliberative** | short WM rollout (§C, H<5) | `T_detect + T_ground + T_select(rollout) + T_handoff < D_delib` | `D_delib ≤ 500 ms` (~24 control steps) | deliberation trigger → decision committed | fall to Event-checkpoint cached path / safe-stop |

- **acceptance metrics** (worst-case, not mean; charter §4/§6.7): p50 / p95 / p99 / **max** / **jitter** / **deadline-miss rate** /
  **fallback latency** / **safety-override latency**. Claim ceiling = **bounded soft/firm real-time**, **not hard real-time** (no
  bounded-execution evidence for OS/scheduler/memory/comms yet). The three `D` bounds above are **design targets to validate, not met deadlines.**

**Fail-closed unknowns**: no wall-clock deadline exists in code; the three `D` bounds are provisional design targets with **no measurement
yet**. D0 records them as evidence-pending and forbids any real-time *claim* until RT0 measures under contention.

**Gate linkage**: ⑦ real-time.

---

## §H. Bridge + explicit dependency interfaces / owners (connect, do **not** mix)

**FACTUAL current state** (v4 §0/§8; charter §1/§6): the four integration dependencies are `T-Skill`, `T-Vision`, `T-WM`, and the active
trainer/env path; the code baseline is the existing `routing_orchestrator.py`. Vision is UNWIRED (§A); the only WM in code is the
`bimanual_*` `WorldModelEncoder` (§C), **distinct** from the WMSO SDM and from the `T-WM` failure-classifier cascade.

**DESIGN-ONLY explicit dependency interfaces + owners** (pN B4 — SDM ownership resolved; T-WM is NOT the SDM supplier):

| dependency | owner node | interface WMSO consumes | reuse-vs-new | mix guard |
|---|---|---|---|---|
| **T-Skill** | skill supply | `SkillLifecycleContract` + `SkillActionKey` per skill (§B); Transition/Recovery skill supply (§E) | contract = NEW; skills reuse existing BC/DAPG/RLPD policies | WMSO does not train or alter skills; consumes their published contract |
| **T-Vision** | belief grounding | `BeliefField{…}` for `VISION_DERIVED` fields (§A) | vision pipeline = to-be-wired (currently `NotImplementedError`) | WMSO consumes belief; it does not implement the encoder |
| **`T-WMSO-SDM`** (proposed **new child** of `T-WMSO`; NEST child-node creation = **Rs approval**) | skill-resolution WM (SDM) | SDM `(belief,skill,goal)→dist` (§C) | SDM = **NEW, WMSO-owned** | SDM owned inside the WMSO subtree, **not** by `T-WM` |
| **T-WM** | failure-classifier cascade | **classification outputs via a classifier adapter only** | reuse existing cascade | **T-WM does NOT supply the SDM** (pN B4); exposed only through the adapter unless Rs explicitly extends its charter; never merge state |
| **trainer (RLPD path)** | `…-P2-trainer` | policy identities + lineage into `SkillActionKey`; env schema | reuse existing planned RLPD residual-on-script path | WMSO does not launch training (boundary held) |

**Binding requirement folded (charter §8-2, Rs「現 (d-b) route/pin は停止・混入させない」)**: the current **(d-b) route/pin** implementation
and the **`T-WM` classifier cascade** are connected to WMSO **by explicit dependency only** and are **not mixed** into WMSO state. The
current route/pin work is an intra-skill prerequisite and is **not paused** by this node.

**Gate linkage**: ① algorithm independence, plus the separation invariant.

---

## §I. Ten-gate crosswalk + adoption sequence + measurement + evaluation (every row DESIGN-ONLY / evidence-pending)

**One row per charter §6 gate → schema surface + acceptance** (no gate PASS is claimed; D0 *registers* the contract):

| # | gate | schema surface (§) | acceptance (DESIGN-ONLY) | D0 status |
|---|---|---|---|---|
| 1 | algorithm independence | §B, §H | LEARNED/SCRIPTED/WAIT accepted through one `SkillLifecycleContract` | contract registered; unresolved |
| 2 | vision grounding | §A | control belief uses `VISION_DERIVED` fields; `PRIVILEGED_SIM` `prod_admissible=false` | vision UNWIRED → evidence-pending |
| 3 | model calibration | §C | per-skill **and** per-handoff calibration error bounds; aggregate insufficient | no SDM yet → evidence-pending |
| 4 | unknown-state abstention | §A, §D | `ood_flag`/`validity=false` → re-observe/recovery/stop; no default-accept | stub to be superseded; evidence-pending |
| 5 | safe interruption | §B, §E | switch only at declared `safe_interruption_checkpoints`; compatibility sets tested | checkpoints ABSENT → evidence-pending |
| 6 | anti-thrashing | §D | switch-penalty + hysteresis + min-dwell; tested under repeated disturbance | ABSENT → evidence-pending |
| 7 | real-time | §G | per-class deadline-miss + max + fallback latency under contention; soft/firm only; provisional D bounds | no measurement → evidence-pending |
| 8 | safety independence | §F | safety fires under model/orchestrator delay/crash/stale/adversarial | no independent monitor wired → evidence-pending |
| 9 | comparative value | §D, §I | beat baselines on task+recovery SR without safety regression | four-baseline plan (below); evidence-pending |
| 10 | no premature claim | §0 boundaries | D0–M0 ≠ training-ready/closed-loop; S0/V0 need own two-key | held; boundary invariant |

**Adoption-sequence supply-readiness gate (pN B4)**: the charter §5 sequence (D0→D1→D2→M0→O0→RT0→S0→V0) is annotated with two explicit
preconditions so no consumer silently depends on an absent supplier:
- **Transition/Recovery supply-readiness** (owner **T-Skill**): **D2/O0/V0 may not consume a Transition or Recovery skill until that skill
  exists and is contract-tested (D1 hash-pinned)**; while unavailable, the consuming path is **safe-stop**.
- **SDM ownership** (owner proposed **`T-WMSO-SDM`** child, not T-WM): **M0/O0 may not consume SDM outputs until held-out + OOD calibration
  pass**; the node itself requires Rs/NEST child-creation approval before instantiation.

**Gate-9 four-baseline plan** (pN B5-inventory): compare **(1) fixed chain** (current step-table order, no value comparison) · **(2) current
heuristic recovery** (Surface-A retry/rollback, `routing_orchestrator.py:1063-1214`) · **(3) boundary-only WMSO** (switch only at checkpoints,
no real-time event path) · **(4) event-driven WMSO** (full multi-rate, deadline-bounded profile). Metric = task SR + recovery SR + safety
interventions; WMSO must beat (1)+(2) **without** safety regression (charter §5 O0 exit).

**Charter §7 measurement / stress matrix** (DESIGN-ONLY; to be *measured*, never asserted):
- **measurements**: task SR, recovery SR, direct-handoff SR, Transition-Skill SR, safe-stop rate, unnecessary-switch rate, thrash rate,
  OOD-abstention precision/recall, model calibration error, predicted-vs-actual duration/cost, event-to-decision max latency, event-to-handoff
  max latency, deadline-miss rate, independent-safety-intervention count.
- **stress cases**: long-duration skills, contact/slip disturbance, target movement, corrupted/delayed vision, unseen abstract states,
  repeated switching pressure, slow world-model inference, process failure, stale SDM data.

**Every D0 row is DESIGN-ONLY** with status ∈ {unresolved, evidence-pending, ABSENT, held}; **no gate is PASSED here**. D0's deliverable is
the *schemas + event-deadline design*, which goes to its own D0-exit independent design verify (charter §5 D0 exit).

---

## Disposition and next steps

- **v3** (`e563c87869`) discharged the first reverify HOLD (B7 transition schema + atomic owner transfer + B6/B8). **pN reverify round-2 (18:49)
  = B1–B5 + B8 PASS-CLOSE, B7 atomic-transfer PASS**; narrow residual.
- **v4 (this)** discharges the round-2 residual: **B7a** — `producer.outcome` is now a tagged **`TERMINAL | INTERRUPT`** union (INTERRUPT
  carries a mandatory `checkpoint_id` + `interrupt_reason ∈ {planned_switch, event, safety_stabilized}`; TERMINAL's `checkpoint_id` nullable;
  `compatibility` + fail-close apply to both) so a mid-skill **safe-checkpoint interrupt** (resumable, gate⑤) is expressible without faking a
  terminal class, which the terminal-only `terminal_class` could not (§E); **B6** — the D0-exit `/pre-check` is re-run on this final version and
  its **record + raw `pre-check-log.jsonl` are (re)banked in this same commit, keyed to this draft's banked sha** (the record carries the
  verdict + pre-checked sha; this draft makes no self-referential pre-check-status claim).
- **D0-exit `/pre-check` verdict + pre-checked sha** = see the banked `WMSO_D0_PRECHECK_RECORD_RSTECHLEAD2_20260718.md` (not restated here).
- **Next**: **resubmit to pN D0-exit reverify** (charter §5 D0 exit) — v4 draft + pre-check record + verdict file banked atomically.
- ⛔ Unchanged and UNAUTHORIZED until each own gate: production control / training launch / WMSO inference / closed-loop authority /
  removal of any safety-or-orchestrator path / p4 grip scope. FOUNDATIONAL invariants (RS71 §0) untouched by this schema draft.
