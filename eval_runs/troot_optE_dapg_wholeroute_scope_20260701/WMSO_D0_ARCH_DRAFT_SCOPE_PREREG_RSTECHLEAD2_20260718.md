# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO D0 architecture-draft — scope pre-registration (approach concurrence before authoring)

- node `T-WMSO`; author `w2:pQ`; verify `w2:pN`; custody `w2:p6`.
- prepared_at: 2026-07-18 15:43 JST · repo HEAD `e163517969` (advisory) · **design DOC only; no code/impl/run; no gate PASS**.
- basis: D0 factual inventory **PASS-CLOSE** (`…_v4.md`, commit `513948a15e`, sha `2e96ea47…`). This prereg registers the
  architecture-draft **structure + grounding + design-gate plan** so pN can concur on the approach before I author the full draft
  (front-loading process agreement, given the D0 verify iteration).

**What this deliverable is (charter §5 D0):** the WMSO D0 **Architecture draft** = state/belief, skill-lifecycle, skill-dynamics,
orchestrator, transition, independent-safety, and per-event-deadline **schemas** — a design document whose **exit condition is pN
independent design verify** (charter §5). It is NOT implementation, NOT a training/env change, NOT a gate PASS.

## Grounding (to be cited in the draft)
- verified inventory v4 (the 3-surface current state + siloed RL/IL/Vision/WM + gap register).
- charter §2 (components), §3 (skill contract), §4 (multi-rate real-time), §5 (adoption sequence), §6 (10 gates), §7 (measurements).
- node `T-WMSO` §3 first-deliverable requirements (source+hash+read-time; factual/design separation; fail-closed unknowns;
  RL/IL/Vision/WM all connected; worst-case latency / deadline-miss / OOD abstention / safety independence in acceptance).
- **V11 reuse anchors** (being digested read-only): `LL-WorldModel-Feasibility.md`, `LL-Orchestration-Design.md` — reuse-first for
  the Skill Dynamics Model + Orchestrator; any documented NO-GO folded in.

## Proposed draft structure (9 sections)
| § | schema | charter | current→WMSO bridge (from inventory) | key gates |
|---|---|---|---|---|
| A | **belief-state** | gate② / §2 | 62D(B)/25-27D(C) privileged → declared belief = vision-grounded estimates + confidence/OOD + phase + progress; privileged=eval metadata only | ② |
| B | **unified skill lifecycle contract** | §3 | unify SkillName-9 / SkillType-7 / bimanual-6 into one typed contract (id, family, immutable hash, obs/act, lineage, init-predicate+confidence, term classes, progress+safe-interrupt ckpt, handoff-state+accepted set, duration/cost, recovery/fail-closed) | ①⑤ |
| C | **skill dynamics model** | §2.1 | none at skill-resolution today → (belief,skill,goal)→{next-belief,duration,success/fail class,cost,uncertainty}; per-skill+per-handoff calibration | ③ |
| D | **skill orchestrator** | §2.2 | replace surface-A heuristic + default-accept OOD stub → candidate filter(init+safety) → continuation/switch value → select → replan; bounded fast path + slow rollout; anti-thrash; OOD abstention | ④⑥⑨ |
| E | **transition manager** | §2.3 | surface-A snapshot-rollback + surface-B phase-bank refork → declared {direct handoff \| transition skill \| recovery skill \| re-observe/safe-stop}; declare safe-interruption checkpoints (ABSENT today) | ⑤ |
| F | **independent safety + event layer** | §2.4 | unwired SOMA envelope + static Z-clip + task-fault termination → independent low-level safety (priority over WMSO, no WM wait) + event detector | ⑧ |
| G | **multi-rate per-event deadline** | §4 | sim-step budgets only (~48 Hz, no wall-clock) → 3 decision classes; D_situation + T_detect+T_ground+T_select+T_handoff; acceptance p50/p95/p99/max/jitter/deadline-miss/fallback/safety-override; bounded soft/firm (not hard) | ⑦ |
| H | **bridge + reuse-vs-new + explicit deps** | §1 | reuse (orchestrator recovery, snapshot, skills, WM encoder, vision pipeline) vs new (unified contract, dynamics model, belief bridge, independent safety, deadlines, abstention); deps T-Skill/T-Vision/T-WM/trainer = connect NOT mix | — |
| I | **10-gate mapping + D0-exit acceptance** | §5/§6 | each schema → each gate; D0 asserts DESIGN only (no training-ready/closed-loop) | ⑩ |

## Design-gate plan
1. author draft (design DOC, grounded above) → 2. **/pre-check** (skeptical failure-mode / deadlock / rule-violation review of the
   design) → 3. bank → 4. **pN D0-exit independent design verify** (charter §5). Any schema that would touch reward/env/success
   *implementation* later triggers `/reward-design` + `/pre-check` at that (D1+) point — not in this D0 draft.

## Boundaries (unchanged, held)
⛔ production control change / training launch / WMSO inference / closed-loop authority / removing safety-or-orchestrator paths /
touching p4 grip. FOUNDATIONAL invariants (RS71 §0: DUAL-ARM / 88 mm / DiffIK / コ-gripper / no-kinematic-trick) not changed by a
schema draft; if any schema appeared to change one, that is a premise change = STOP + Rs.

## Ask to pN
Concur on this **structure + grounding + design-gate plan** (or flag missing schemas / scope errors / a gate not covered) before I
author the full draft. On concurrence I write §A–§I, run /pre-check, bank, and submit for the D0-exit design verify.
