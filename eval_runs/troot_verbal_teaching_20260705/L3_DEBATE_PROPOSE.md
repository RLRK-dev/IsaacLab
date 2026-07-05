# L3 5-body [VERIFY] debate — PROPOSE (VT-DESIGN / CC1 lead)

**Subject:** `DESIGN_V1.md` v1.2 (Verbal-Teaching Motion Authoring — design proposal).
**Format:** §運用2 [VERIFY] adversarial debate (paper 段, per `CHARTER_V1.md:32` "設計案 doc → L3 chain (5体)"). CC1 (VT-DESIGN/p5) PROPOSE → CC2-5 Challenger + CC6 NHA (parallel, independent context) → CC1 REBUT_OR_ACCEPT → CC1 NO_ACTION_EVALUATION + DECIDE.
**Provenance chain:** v1.0 → %12 review 02:10 → v1.1 → %12 APPROVE 02:18 → **%10 author-review CONCUR 02:25** → v1.2 (3 LOW folded) → this debate.
**Status:** **SPAWN GO** (%12 2026-07-06 02:25).

## Reviews of record (folded into v1.2 — provided to challengers as CONTEXT, NOT as a shield)

- **%12 review 02:10 → APPROVE 02:18:** 2 fixes (St1a/b split; class-A/B teaching) + 2 notes (consumed-by; MOTION-STANDARD-vs-RUN1_REF) + 1 nit (n_steps :1960) — folded into v1.1; landings spot-verified.
- **%10 author-review 02:25 → CONCUR (0 CRIT / 0 HIGH):** lenses = scoping-fidelity / omissions / fix-⑤-facts. **fix-⑤ facts independently §運用28-re-verified by %10** (the 07-03 scoping's original author); **St1a/b split ENDORSED**. 3 LOW folded into v1.2 (§3.1 taut-route caveat / §2.1 geometry-current / §0 path convention).
- **Note to challengers:** prior APPROVE/CONCUR is context, NOT immunity — attack the substance; a real CRITICAL/HIGH overrides prior review.

> Per §運用15, this PROPOSE contains NO success/fail verdict, NO confidence, NO pre-emptive rebuttals. It is the neutral change statement + rationale + SSOTs + KNOWN_ALTERNATIVES for the challengers to attack.

---

## PROPOSE — the change under review

A **staged table-driven runner + verbal-teaching loop** for the C1→C2 route, replacing today's scattered/hand-written authoring:
- **route-table = single generative source + single param home** (`DESIGN_V1.md §3.1/§3.2`): rows carry `primitive / target_source / orientation / gripper / gate / amplitudes / inv_binding`; the ordered row list = the leg sequence; coordinate/amplitude edits keep the leg-label sequence, adding/removing a row = new motion = Rs 専権.
- **staged build** (`§3.3`): **St1a** (external param layer, R3 untouched, byte-id trivial) → **St1b** (locked-file table-read shim, L3 + Rs auth + byte-id re-proof) → **St2** (schema enrichment + fix-⑤-as-row proof) → **St3** (b) CODEGEN | (c) INTERPRETER (Rs decision D-2).
- **teaching loop** (`§4`) with **class A** (offset/param-gated → nominal preserved) / **class B** (base-motion 修正 → nominal changes → new `RUN1_REFERENCE` + loud supersession) split, classified at loop step 2, mechanically verified by leg-diff SAME-STRUCTURE + reference-diff video before Rs confirm.

**Scope:** DESIGN ONLY (paper, 0-commit). No locked-runner edit, no new motion invented. Build after W0-e close.

## Rationale + evidence (grounded)

- **fix-⑤ counterfactual** (`§1`): notes 13/21/29/37 in `full_43step.json` ("R-hand X=L-hand X") = the fix-⑤ intent, authored ~10 weeks ago, but the abs-waypoint schema had no derived-target field → demoted to prose → hand-implemented at a measured ~1.5h (`STEPTABLE_SCOPING_COORD2.md:15,38`).
- **byte-id obstacle B** (`§2.2`): even the nominal path's targets are runtime-measured (`GRASP_YC=np.mean(_near)` `:3946`; F-flags read live cable crossing `:3990`) → a pure static waypoint table can never be byte-identical → the `target_source` field is required.
- **param scatter** (`§2.3`): as-run config in 3 places (`task_config` / env override / runner default) → a direct cause of authoring round-trips.

## Target files

- **Primary (this task):** the design doc (paper).
- **Eventual build (post-approval):** St1a = a NEW external param-layer module + row-diff gate (R3 untouched); St1b would edit `test_newton_clip_routing.py` (Rs-LOCKED → L3 + Rs explicit auth); St2/St3 touch the route artifact/engine (L3).

## Core reference SSOTs

- Fixed list: `task_config.py`, `SOMA.md`, `CLAUDE.md` prohibited section.
- Design-specific: `CHARTER_V1.md`, `LEDGER:44`, `RS71-System-Spec-SSOT.md §0` (INVARIANTS #1-5), `full_43step.json`, `route_leg_diff.py`, `RUN1_REFERENCE_V2.md`, `test_newton_clip_routing.py:3569`, `STEPTABLE_SCOPING_COORD2.md`.

## KNOWN_ALTERNATIVES (considered + stated status — challengers may contest)

| Alternative | Design's stated status | Where |
|---|---|---|
| Pure static abs-waypoint table (raw `full_43step.json` schema) | REJECTED — obstacle B (can't be byte-identical) | §2.2 |
| (a) params-only / (b) codegen / (c) interpreter | staged + Rs decision (defer (b)v(c) to St2 evidence) | §3.3, D-2 |
| St1a (external) vs St1b (locked shim) | St1a recommended first (no locked-file edit, trivial byte-id) | §3.3 |
| Reuse env6/VBD robottas executor as-is | REJECTED — wrong substrate; reuse DESIGN patterns only, re-target env7/mujoco-コ | §2.1, §8 |
| NHA baseline: keep R3 hand-written + manual teaching | the null hypothesis CC6 defends | §7, §8 |

## Challenger lens assignment (perspective-diverse — each attacks a distinct failure mode)

| Agent | Lens | Attack surface |
|---|---|---|
| CC2 | byte-identity / correctness | Is St1a byte-id truly trivial? Does the class-B new-reference procedure have a hole? Is obstacle B correctly characterized (are nominal targets truly runtime-measured)? Does the npz tap-ordering claim hold? |
| CC3 | INVARIANTS / governance | Can the vocabulary/parser leak an INVARIANT change (single-arm / span≠88 / non-DiffIK / teleport)? Is the pin exception handled correctly? Is the class-B base-change → L3 / Rs-専権 boundary right? Is the L-triage correct? |
| CC4 | scope / step-table-first fidelity | Does St3 generation risk inventing legs? Is leg-diff SAME-STRUCTURE sufficient to enforce "no legs absent" (`LEDGER:44`)? Scope creep to full 5-clip? Does class B smuggle in structural change? |
| CC5 | grounding / citation accuracy | Line-by-line verify every file:line cite (runner internals, json schema, leg-diff semantics, RUN1_REFERENCE, n_steps :1960). Any wrong/stale citation? |
| CC6 | NHA (null hypothesis) | Is hand-written R3 + manual teaching actually sufficient? Does the staged plan over-engineer? Are the KNOWN_ALTERNATIVES (esp. St1a-only, or keeping R3) enough to make the heavier stages unnecessary? NULL_HYPOTHESIS: HOLD / CHANGE_JUSTIFIED. |

## DECIDE protocol (CC1, after challenges)

REBUT_OR_ACCEPT each CHALLENGE + NHA (3+ agents flagging one issue → rebut needs added evidence; no silent dismissal) → NO_ACTION_EVALUATION (is an existing alternative sufficient? NHA verdict? why not No-Action?) → DECIDE: accepted CRITICAL/HIGH → FAIL (revise doc); NHA HOLD + alternative sufficient → NO_ACTION; all CRITICAL/HIGH rebutted + No-Action rejected → PASS; unresolved → REVIEW (to %12/Rs).

*VT-DESIGN (w2:p5) — L3 debate PROPOSE, prepared, spawn-gated on %10 CONCUR.*
