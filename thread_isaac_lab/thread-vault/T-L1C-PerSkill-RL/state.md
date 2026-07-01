---
node_id: T-L1C-PerSkill-RL
node_name: "L1.C Per-Skill RL (DAPG, 5-skill routing)"
goal: "Learn the cable-routing skills via per-skill RL (DAPG) so the dual-arm routing runs as a learned policy, not just scripted building blocks."
goal_verification: |
  PENDING (gated, crucial axis). The OLD 5-skill strict-serial RL is LEGACY / P0-KILL'd (infeasible-as-scoped). The forward L1.C per-skill RL (env7 Option-E) is PREMATURE / GATED behind 4 prerequisite tracks (pre-RL readiness plan 2026-06-21): #1 grasp freeze (= R-S7.1 コ, BANKED CPU) / #2 GPU stabilization (= R-S6.6) / #3 RL skill scope (parked) / #4 env7 RL-substrate build. A no-train gate is currently up. env6 prior per-skill progress (fidelity-mixed): AC 49% / IC 39.2% / GC 0%-true-stoch / AR 92.2% (fidelity-QUARANTINED) / CR untrained; Unclamp = scripted (RL not needed). Not a product / 95-100% claim. [%2 PV 2026-06-24 (H2+M1): precedent now includes T-RS6-6 (GPU held-rate = the literal RL-training gate; R-S6.6 goal = "so RL parallel-env training is feasible"). status PENDING->IN_PROGRESS reflects the ACTIVE demo-gen prerequisite (child T-DA-MPPI IN_PROGRESS = the RL track has BEGUN via demo prep); the RL TRAINING itself remains no-train GATED behind the 4 tracks -> IN_PROGRESS != training-started.] [Rs 2026-06-24: skill count 4->5 — the GUIDE/ROUTE (しごき "guide cable to next clip", currently SCRIPTED TransportToClip step_table.py:46) is CONFIRMED as the 5th forward RL skill (Rs: "added when B was OK'd"). DESIGN/IMPL DEFERRED to a gate (the code RL-ization of step_table = [DESIGN-GATE]+L3). ⚠ the 2026-06-22 5体 (log.md:6618) flagged guide-as-RL concerns to resolve at impl: obs-reward rule-21 (a しごき stability reward needs FULL cable-shape, but the 42D skill obs exposes only the nearest segment) + composition (static SkillName/SkillType enums + hardcoded gait). ⚠ taxonomy to reconcile at impl: design doc set = AC/IC/AR/Clamp (RL-Routing-Design:1580) vs env6 progress = AC/IC/GC/AR/CR — the "5th" naming/identity is the guide/route, to be pinned. Authoritative 07-Design (RL-Routing-Design.md) reflection PENDING Rs spec-edit authorization (CC read-only).]
status: IN_PROGRESS
parent_node: T-ROOT
children_nodes: [T-ROOT-optE-route-dapg-C1C2]
dependencies:
  precedent: ["T-L1X-Substrate-Realism", "T-Forward-Capability", "T-RS6-6"]
  blocker: []
created: 2026-06-23T22:14:00+09:00
last_updated: 2026-06-23T22:14:00+09:00
spec_version: LTM-1 v1.1
---

# L1.C Per-Skill RL (DAPG, 4-skill routing) — PENDING (gated, crucial)

The learning core: per-skill RL (DAPG) that turns the scripted/proven building blocks into learned routing policies. Currently GATED — the env7 L1.C per-skill RL is premature until the 4 prerequisite tracks (grasp-freeze / GPU / RL-scope / env7-RL-build) clear and the no-train gate lifts. The legacy env6-VBD 5-skill RL is P0-KILL'd / quarantined.

Grounded: `07-Design/RL-Routing-Design.md` (LEDGER ⚠️ MIXED), `07-Design/RL-Routing-Progress.md`, pre-RL readiness plan (memory `project_pre_rl_readiness_plan_2026-06-21`), `docs/logical_decomposition.html` (L1.C per-skill RL "now" = PREMATURE frame).

*NEST live-spine re-seed (Stage-A addendum, 2026-06-23). Minimal-schema node; SSOT = log.md + the cited design docs. View regenerated via `scripts/build_nest_snapshot.py`.*
