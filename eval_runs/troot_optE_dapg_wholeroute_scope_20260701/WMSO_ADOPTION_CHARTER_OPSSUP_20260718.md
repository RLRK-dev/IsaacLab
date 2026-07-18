# WMSO adoption charter (OPS-SUP-CODEX, 2026-07-18)

**Status:** Rs direction accepted as an L0 architecture requirement. Rs direct 2026-07-18 assigned WMSO
development to `T-ROOT-RS-TECH-LEAD2` and authorized D0 read-only inventory to start. This record does **not**
authorize production control, training launch, or removal of existing safety and orchestrator paths.

## 0. Decision and terminology correction

Adopt **World-Model-Based Skill Orchestration (WMSO)** as the high-level architecture that
integrates learned skills, vision-grounded state, a skill-resolution world model, runtime skill selection,
handoff, transition, recovery, and safe fallback.

WMSO may use a boundary-only or a real-time execution profile. This project retains the multi-rate,
event-driven, deadline-bounded profile defined in this charter; removing “Real-Time” from the architecture
name does not weaken its real-time or safety acceptance requirements.

The assigned development owner is **`T-ROOT-RS-TECH-LEAD2`**. OPS-SUP-CODEX remains the independent evidence
verifier and p6 remains the Vault/current-state custodian. The previous p4 design assignment is superseded so
p4 can continue the grip gate chain without making WMSO wait for that checkpoint.

The high-level action is a **learned skill**, not specifically a PPO skill. Supported skill provenance includes:

- behavioral cloning (BC);
- BC followed by RL fine-tuning (BC+RL);
- PPO or another online RL method;
- DAPG or another imitation-plus-RL method.

The orchestration contract is algorithm-agnostic. Every skill must expose the same typed lifecycle contract,
regardless of how its internal policy was trained. WMSO does not generate motor commands and does not
replace the skill's low-level controller.

## 1. L0 placement and node boundary

Maintain **`T-WMSO` as the L0 architecture node under administrative owner `T-ROOT-RS-TECH-LEAD2`**, which is
itself under `T-ROOT`, rather than placing WMSO below the current `T-WM` node. The current `T-WM` is a
failure-classification/recovery cascade. WMSO is the integration architecture across all four Rs-mandated L0
means:

| L0 means | WMSO role |
|---|---|
| RL | supplies RL-trained or RL-fine-tuned skills |
| IL | supplies BC/DAPG demonstrations, initialization, and learned skills |
| Vision | grounds observations into a belief/abstract state and detects OOD/low confidence |
| World model | predicts skill-level transitions, duration, success probability, cost, and uncertainty |

Proposed dependencies are `T-Skill`, `T-Vision`, `T-WM`, the active trainer/environment path, and the existing
`routing_orchestrator.py` baseline. The current route/pin work remains an intra-skill prerequisite and is not
paused by this charter.

## 2. Component responsibilities

### 2.1 Skill Dynamics Model

Predict a distribution over the next grounded state, duration, success/failure class, accumulated cost, and
uncertainty for `(belief_state, skill, goal)`. It operates at skill resolution. It must not claim accurate
low-level cable dynamics unless separately validated.

### 2.2 Skill Orchestrator

Filter candidates by initiation and safety predicates, compare continuation and switching value, select the
next skill, and replan after outcomes or events. Use:

- a bounded fast path based on a precomputed policy/Q representation for known states; and
- a bounded short-rollout slow path for uncertain states, goal changes, or recovery planning.

### 2.3 Skill Transition Manager

Choose and execute exactly one of:

1. direct handoff at a compatible Skill Handoff State;
2. a Transition Skill;
3. a Recovery Skill;
4. re-observation or safe stop when no valid transition exists.

### 2.4 Independent safety and event layers

Low-level safety monitoring has priority over WMSO and must not wait for world-model inference. The event
layer detects completion, failure, slip/contact changes, lack of progress, OOD state, checkpoint arrival, and
deadline risk. Mid-skill switching is allowed only at a declared safe interruption checkpoint unless the safety
layer has already stopped or stabilized the system.

## 3. Required skill contract

Each BC, BC+RL, PPO, DAPG, or other learned skill must publish at least:

- `skill_id`, policy family, immutable policy/version hash, observation/action schema, and training lineage;
- initiation predicate and required belief confidence;
- success, failure, timeout, and invalid-state termination classes;
- progress phase and safe interruption checkpoints;
- Skill Handoff State schema and accepted incoming handoff set;
- expected duration/cost distribution and resource requirements;
- recovery/rollback target and a fail-closed action when no safe continuation exists.

BC+RL lineage must distinguish the BC checkpoint, RL fine-tuning configuration, and final policy hash. Two
policies with the same skill name but different lineage are different skill actions for model training and
evaluation.

## 4. Multi-rate real-time contract

The WMSO real-time execution profile has three decision classes:

| Class | Owner | Function |
|---|---|---|
| Safety | independent low-level monitor | immediate stop, hold, retract, or force limiting |
| Event/checkpoint | event monitor + fast orchestrator path | continue, interrupt, direct handoff, or cached recovery |
| Deliberative | short world-model rollout | uncertain state, changed goal, nontrivial recovery |

For every event class define a situation deadline `D_situation` and require:

`T_detect + T_ground + T_select + T_handoff < D_situation`.

Acceptance uses worst-case and deadline-miss measurements, not mean latency alone: p50, p95, p99, maximum,
jitter, deadline-miss rate, fallback latency, and safety-override latency. Until the OS, scheduler, memory, and
communication path have bounded execution evidence, the project may claim **bounded soft/firm real-time
response**, not hard real-time. This follows the ROS 2 real-time distinction that correctness includes meeting a
defined deadline and that low average latency alone is insufficient:
<https://design.ros2.org/articles/realtime_background.html>.

## 5. Adoption sequence

| Gate | Deliverable | Exit condition |
|---|---|---|
| D0 Architecture | state/action/transition/safety schemas and event deadlines | independent design verify |
| D1 Skill contracts | adapters for BC+RL and at least one other policy lineage | contract tests and hash-pinned lineage |
| D2 Dataset | vision-grounded skill transitions including failures, handoffs, and recovery | coverage and split audit |
| M0 Skill Dynamics Model | calibrated transition/duration/success/cost/uncertainty predictions | held-out and OOD gates |
| O0 Offline orchestration | replay-only planning and switching | beats fixed-chain and heuristic baselines without safety regression |
| RT0 Bounded fast path | preloaded candidate filter and Q/policy lookup | deadline and fail-loud tests |
| S0 Shadow mode | decisions logged while existing orchestrator retains control | zero control authority and matched-event audit |
| V0 Closed-loop pilot | limited WMSO authority with fallback | safety, recovery, latency, and task-success gates |

Design, contract definition, and offline data work may proceed in parallel with current skill work. Closed-loop
authority remains blocked until the skills it selects have stable initiation/termination/handoff contracts.

## 6. Binding acceptance gates

1. **Algorithm independence:** the orchestrator accepts BC+RL and RL-only skills through the same contract.
2. **Vision grounding:** state selection uses vision-derived belief and confidence; simulator-only privileged
   state is training/evaluation metadata, not an undeclared production input.
3. **Model calibration:** transition, success, duration, cost, and uncertainty are checked per skill and per
   handoff; aggregate accuracy alone is insufficient.
4. **Unknown-state abstention:** low-confidence/OOD input cannot force an ordinary skill choice; it routes to
   re-observation, recovery, or stop.
5. **Safe interruption:** no arbitrary mid-skill switching. Checkpoints and compatibility sets are tested.
6. **Anti-thrashing:** switch penalty, hysteresis, or minimum dwell prevents oscillatory skill changes and is
   evaluated under repeated disturbances.
7. **Real-time:** event-to-handoff deadline misses, maximum latency, and fallback latency meet each declared
   class budget under contention.
8. **Safety independence:** safety action succeeds when the model/orchestrator is delayed, crashed, stale, or
   adversarially wrong.
9. **Comparative value:** compare fixed chain, current heuristic recovery, boundary-only WMSO, and WMSO with
   the event-driven, deadline-bounded execution profile.
10. **No premature claim:** D0-M0 completion is not training-ready or closed-loop GO; S0 and V0 require their
    own two-key evidence/design verdicts.

## 7. Initial measurements

Report task success, recovery success, direct-handoff success, Transition Skill success, safe-stop rate,
unnecessary-switch rate, thrash rate, OOD abstention precision/recall, model calibration error, predicted versus
actual duration/cost, event-to-decision maximum latency, event-to-handoff maximum latency, deadline-miss rate,
and independent safety interventions.

Stress cases must include long-duration skills, contact/slip disturbance, target movement, corrupted or delayed
vision, unseen abstract states, repeated switching pressure, slow world-model inference, process failure, and
stale Skill Dynamics Model data.

## 8. Immediate next action

1. Keep this direction as the founding charter for node `T-WMSO`, assigned to `T-ROOT-RS-TECH-LEAD2`.
2. Keep the node separate from the active route/pin implementation and from the existing `T-WM` classifier
   cascade; connect them through explicit dependencies.
3. `T-ROOT-RS-TECH-LEAD2` starts D0 with a read-only inventory of current skills, policy provenance (including BC+RL), observation
   schemas, termination signals, checkpoints, and existing `routing_orchestrator.py` behavior.
4. Do not modify production control or launch WMSO inference until D0 is independently verified.
