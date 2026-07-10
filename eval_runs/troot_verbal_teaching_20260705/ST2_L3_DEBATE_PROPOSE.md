# St2 Build Spec — L3 5-body [VERIFY] debate — PROPOSE (VT-DESIGN / CC1 lead)

**Subject:** `ST2_BUILD_SPEC.md` v0.2 (St2 derived-source row schema — design paper).
**Format:** §運用2 [VERIFY] adversarial debate (paper 段). CC1 (VT-DESIGN/p5) PROPOSE → CC2-5 Challenger + CC6 NHA (parallel, independent) → CC1 REBUT_OR_ACCEPT → NO_ACTION_EVALUATION + DECIDE.
**Provenance:** DESIGN_V1 v1.4 (Rs 承認 `b17b473a15`) → St2 kickoff (Rs 可 `eba71929b3`) → v0.1 → v0.1a (self-review: DS4 Rs-LOCK) → v0.1b (%12 Q1/Q2) → **v0.2 (%10 author-review CONCUR / 1 MEDIUM folded: ② branch-completeness, ④ bisectability, LOW)**.
**Baseline:** runner `test_newton_clip_routing.py` @ committed `6808964dc3` (== working tree, verified clean).
**Assignment:** %12 09:17 — CC1 = p5; DECIDE → %12 verify → Rs packet (Q2 staging decision).

> Per §運用15, this PROPOSE carries NO success/fail verdict, NO confidence, NO pre-emptive rebuttals — the neutral change statement + SSOTs + KNOWN_ALTERNATIVES for the challengers to attack.

## PROPOSE — the change under review

A **derived-source row schema (St2)** so runtime-derived route targets become table rows instead of R3 hand-authoring:
- **§2 schema:** `target_source ∈ {constant, cable-derived, clip-derived}` + a bounded derivation (`measure/reduce/transform/gate/taut_gate`); the **5 DS primitives** = caveat-a (`:3946`) / fix-⑤ (`:3983-3986`) / F-1a (`:4234-4277` + C2 analog `:4840`) / argmin C2-regrasp (`:4665`, Rs-LOCKED `:4662`) / pin (`:1384-1399`,`:4345-4357`). **F-1b excluded** (config-derived = St1a-class, `:3954`).
- **§2.3/§3 emits_legs:** a **leaf-complete conditional branch-set** (F-1a's nested high-re-measure trim gate `:4268` → highPASS/highREJECT leaves) + an **ordered-multiset primitive audit** that closes the St1a pin blind-spot.
- **§4 proof:** fix-⑤/F-1a row-ification = **behavioral npz-sha** (offset-gate byte-id on nominal; exercise both high-leaves).
- **Staging (Q2):** St2-absorbs-St1b — presented as both options, Rs decision.

**Scope:** DESIGN ONLY (paper, 0-commit). No runner edit; build deferred (post-φ10/DC-1 + %12 sequencing + L3 + Rs auth + byte-id re-proof).

## KNOWN_ALTERNATIVES (both carried per %12)

| Alt | Status in spec | Where |
|---|---|---|
| **A — keep St1b→St2 separate** (DESIGN_V1 as-approved) | carried, un-pre-decided | §7 Q2 |
| **B — St2 absorbs St1b** (single arc + 2-checkpoint proof) | %12 lean; Rs decision | §7 Q2 |
| **Null — keep R3 hand-authoring derived sources** (no St2) | the NHA baseline | §1, §7 (CC6) |
| Pure static abs-waypoint table | REJECTED (obstacle B, can't be byte-id) | DESIGN_V1 §2.2 |

## Core reference SSOTs

`ST2_BUILD_SPEC.md` v0.2; `DESIGN_V1.md` v1.4; `STEPTABLE_SCOPING_COORD2.md` (derived-source taxonomy); `RS71-System-Spec-SSOT.md §0` (INVARIANTS); `LEDGER:44`; `test_newton_clip_routing.py` @`6808964dc3`.

## Challenger lens assignment (perspective-diverse — each attacks a distinct failure mode)

| Agent | Lens | Attack surface |
|---|---|---|
| CC2 | byte-id / behavioral-proof correctness | offset-gate byte-id truly collapses to nominal? npz-sha proof proves equivalence? Q1 (5f1c3f92 unchanged, snap-down offset-gated `:3957/:3965-3966`)? 2-checkpoint CP1/CP2 sound (instrumentation truly non-behavioral)? 6-tap order (obstacle D)? |
| CC3 | INVARIANTS / Rs-LOCK / governance | schema leaks an INVARIANT (RS71 §0 #1-5)? DS4 Rs-LOCK (`:4662` anti-revert) a mandatory inv_binding? pin (DS5) gated on clip-retention SEMANTIC not token? branch-add = Rs 専権 enforced? Option-B needs Rs re-approval of DESIGN_V1 staging? |
| CC4 | schema / branch-completeness (the ② area) | branch-set NOW leaf-complete? verify F-1a `:4233-4277` for OTHER internal add/drop-leg gates beyond trim `:4268`; does the ordered-multiset audit bound the count for ALL DS (not just F-1a)? hidden leg-count variation in caveat-a/fix-⑤/argmin/pin? |
| CC5 | grounding / citation accuracy @`6808964dc3` | line-by-line verify EVERY cite (DS1-5, ② `:4268-4269/:4275-4276`, byte-id `:3957/:3965-3966`, Q1, all §2/§3/§4). Any wrong/stale/imprecise citation? |
| CC6 | NHA (null hypothesis) | is St2 NEEDED or is Null (R3 hand-authoring) sufficient? schema over-engineered? T2=exactly-2 + "nearly-closed" primitive set → is building now premature vs defer? A vs B vs defer? NULL_HYPOTHESIS: HOLD / CHANGE_JUSTIFIED. |

## DECIDE protocol (CC1, after challenges)

REBUT_OR_ACCEPT each CHALLENGE + NHA (3+ agents on one issue → rebut needs added evidence; no silent dismissal) → NO_ACTION_EVALUATION (is an alternative sufficient? NHA verdict? why not No-Action?) → DECIDE: accepted CRITICAL/HIGH → FAIL (revise); NHA HOLD + alternative sufficient → NO_ACTION; all CRITICAL/HIGH rebutted + No-Action rejected → PASS; unresolved → REVIEW (to %12/Rs). Output → %12 verify → Rs packet.

*VT-DESIGN (w2:p5) — St2 L3 debate PROPOSE.*
