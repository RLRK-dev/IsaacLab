# GROVE CORE SPEC v1.0 — portable, project-agnostic (2026-06-10)

GROVE = **G**ated **R**ole-**O**riented **V**erified **E**xecution: a methodology for multi-agent development under a single human authority. This file is the PORTABLE NORMATIVE CORE — copy it into a new project and complete the BINDING sheet (§B). It contains no domain vocabulary except in labeled examples. The user-facing overview (with case studies) lives separately; governance force comes from the project's own rule files once the core is landed there (human-gated).

**Scope assumptions (known limits):** one human principal; software/system development; agent platform interchangeable (proven by a full platform swap with the methodology unchanged, 2026-06-06).

## C1. Pillars
1. **Task tree (NEST):** every task = a node in a logic tree, 1:1-bound to one agent session; parent/child cascade; freshness guards.
2. **Role topology:** authority(human) / tech-lead / supervisor(gatekeeper) / executor(s) / blind-judge — separated; drafter ≠ reviewer at high-stakes gates.
3. **Gated verification:** read-only Tier-A review; lensed adversarial debate (challengers each owning an orthogonal lens over a breadth floor + a null-hypothesis advocate; panel size + lens-set per binding ⑪); on-disk reconciliation (post-change state vs approved diff and reported numbers); post-verify after execution; SHA-verified completeness. Gate the PREMISE, not just the artifact. Reading order: primary modality → secondary measurements (logs) → reconciliation.
4. **Experience-feedback first:** smallest principled change → gated run → measured feedback → next. No spec accretion; reuse before rebuild.
5. **Foundation rigor:** the system's foundation (physics/data/infra) is built strictly; bypasses or appearance-only behavior (e.g. kinematic teleports in sim) never count as "working". Looseness applies to task performance only, never the foundation.
6. **Two-container knowledge capture:** every lesson lands in (a) the agent-native memory and (b) the repo knowledge vault — same content, two native containers; freshness-guarded.

## C2. Roles
| Role | Duties | Constraints |
|---|---|---|
| Human authority | frame/goals/policy; the non-delegables (gate list §C3) | — |
| Tech-lead | drafts designs; chairs debates; on-disk reconciliation; dispositions between runs; directs executors | escalates per rule 10; classification/re-baseline need supervisor concurrence |
| Supervisor | read-only Tier-A + independent post-verify + cross-session memory + trajectory audit per milestone + concurrence on fail-class classification and re-baselines | never launches/mutates/approves |
| Executor(s) | implement/run exactly per gated spec; STOP+surface on any new fail class | never edits gates mid-run |
| Blind judge | zero-exposure validity verdicts on artifacts alone | never shown expectations/metrics |

## C3. Gates, authority, observation
**Risk tiers:** L0 trivial (basic rule-check) / L1 normal (+DoD + independent-agent verification) / L2 new files/public API (+pre-mortem + pre-debate) / L3 SSOT/control/foundation/methodology (+multi-perspective parallel verification + post-verification chain). **Orthogonal gates** (fire on content, independent of L): DESIGN-GATE = changes to the objective function / success definition / environment contract; HIGH-COST-GATE = the binding's declared expensive-resource thresholds (default NO_GO; gate procedure + human approval above threshold — the lead runs the gate, never self-classifies around it).
**Workflow:** DEFINE → TASK(node) → L-TRIAGE → CHECK → VERIFY(adversarial) → DESIGN-GATE* → RULE-CHECK → CHANGE → HIGH-COST-GATE* → RUN → RESULT(post-verify).
**Human asks in the steady cycle (5):** ① frame/goal changes ② SSOT(L3) commits, bundled (rule FILES stay human-initiated) ③ above-threshold cost runs ④ outward-facing acts (content-confirmed) ⑤ new fail classes that change design DIRECTION. **Standing safety gates remain separate and untouched** (process kills, privileged ops, control-method changes, out-of-scope new artifacts, node-start approvals — per the binding's prohibition file).
**Lead autonomy:** sub-threshold runs; within-chain STOP→fix→rerun (low-cost, zero-source-edit, probe-local); instrument-scope dispositions per rule 7. **Drift protection:** the chain-start anchor is preserved forward-only; rule 4 reconciles against BOTH the last baseline and the origin; cumulative drift beyond a declared envelope auto-escalates; milestones are BOUNDED (declared time/cost/run budget at DEFINE); the supervisor audits trajectory per milestone (state vs root goal vs origin). **Veto mechanism:** a stop-flag channel checked at every chain-step boundary + heartbeat reports independent of milestone completion; veto ⇒ STOP+surface at the next boundary, state preserved.
**Observation (never targets — Goodhart):** human-gates/milestone, STOP→asset conversion, cross-layer catch rate, time-to-milestone — read PAIRED with counter-metrics (human-overturn rate at audit, report surprise rate, drift-envelope breaches). Re-measure after each gating reduction before reducing further.

## C4. Operating rules (11)
Status: CORE = multi-incident lineage; CANDIDATE = observed once (2026-06-10, first binding); candidates promote on confirmation in a second binding.
1. **Primary-modality first** (CORE): for anything with behavior, LOOK before reading numbers; all three verification layers eyeball independently (a reading-order discipline — formal validity verdicts belong to the blind judge). Applies at gate/binding runs and verdict points (not internal iterations; first occurrence of a new fail class always). Cheap rendering from logged state suffices.
2. **Zero-claims need a true positive** (CANDIDATE): an instrument claiming "zero detections = OK" is uninterpretable until it has shown a true positive — per instrument CONFIGURATION (re-show after filter/exclusion/topology changes).
3. **Expected-values handover** (CANDIDATE): hand verifiers a table of expected values (or checkable expected properties where numbers don't exist) PLUS the primary-modality artifacts; reconcile value-vs-value; every expectation carries a provenance tag (measured/derived/authored).
4. **Deviation auto-STOP + enumerated exemptions** (CANDIDATE): re-runs auto-reconcile vs known baselines — identity on deterministic substrates, else per-quantity ex-ante tolerances; intended changes are exempted BY NAME (no open exemption classes); foundation gates are never exempt; reconcile vs both last-baseline AND chain origin.
5. **Dependency-set × deferred-list intersection** (CANDIDATE): each phase enumerates the parameters/premises its gates depend on and intersects with the design's own deferred/pre-flagged list; non-empty ⇒ gate it in-run or argue validity explicitly before the phase is normative.
6. **Regime-conditioned metrics** (CANDIDATE): every metric declares its valid regime EX-ANTE (at gate definition); gate only inside it; out-of-regime readings are artifacts; post-hoc regime narrowing IS a gate edit (rule 7 path). Prefer conditioning over deletion.
7. **STOP→asset conversion** (CORE): new fail class ⇒ STOP + surface (no symptom-patching/threshold-loosening). Gate-edit discriminator: executors never edit gates mid-run; the lead dispositions between runs, recorded; supervisor concurrence when supervisor-issued artifacts are touched. Artifacts forward-only (never overwrite FAIL records). Every run reconciles its executed gate set against the design's enumerated GATE MANIFEST (missing gates need named exemptions). Convert each STOP into a recorded substrate fact or a sharper gate before proceeding.
8. **Mutual-catch chain** (CORE): author ≠ reconciler ≠ independent verifier, plus pre-verdict debate scaled by the L-tier. Every layer errs; the structure catches it.
9. **Measure anchors before pinning** (CANDIDATE): gate anchors/expectations/calibrations are MEASURED in the operating regime (cheap fine sweep first; never pinned from coarse extrapolation); context change (pose/load/configuration) reopens the calibration; first-run expectations are produced by the lead via fine sweep with provenance tags.
10. **Runaway bounds** (CORE): 3 failed fixes on the same fail class ⇒ mandatory escalate (question the approach). "Stuck" is operationalized: 3-strike OR declared stall-time exceeded OR declared chain budget (time/cost/runs, set at DEFINE) exceeded — each auto-escalates. Accumulated low-cost runs count against the budget.
11. **Substrate-Resolvability Gate (SRG)** (CANDIDATE): before any run whose verdict depends on a FIDELITY-BOUND quantity (friction / contact / creep / retention / any property the substrate models only approximately), pre-check three things — (1) is the substrate production-solver-faithful, or a PROXY? (2) if a proxy, is a landing/validity control ALREADY green (demonstrated BEFORE this run, not scheduled INSIDE it)? (3) is a fidelity-INDEPENDENT redesign cheaper and already data-mandated? A proxy that is default-NO on (2) MAY run ONCE as an explicitly LABELED scoping probe, but may NOT bind a verdict and may NOT self-iterate. Generalizes rule 8 (gate the PREMISE) to gate the premise's RESOLVABILITY: before asking "is the mechanism spec-faithful?", ask "can this substrate even answer the question I am about to put to it?". Delivery is lightweight (a knowledge note + a pre-check item, not a heavy process gate).

## B. BINDING SHEET (complete per project — required ①-⑥, recommended ⑦-⑩)
| # | Binding | This project's value |
|---|---|---|
| ① | Goal SSOT (root goal doc) | _____ |
| ② | Parameter SSOT (auto-L3 paths) | _____ |
| ③ | Role→entity map (incl. agent platform) | _____ |
| ④ | Domain L3 keywords + orthogonal-gate definitions (what is the objective function / success definition / environment contract here) | _____ |
| ⑤ | Primary verification modality + reconciliation channels (what is this domain's "video") | _____ |
| ⑥ | Task-tree root (+ tree spec location) | _____ |
| ⑦ | Cost model (expensive resource, unit, thresholds = HIGH-COST-GATE content) | _____ |
| ⑧ | Knowledge SSOT wiring (vault location, write protocol, freshness guard) | _____ |
| ⑨ | Production/outward definitions + blind-judge delivery channel (zero-exposure preserved) | _____ |
| ⑩ | Reproducibility tolerance policy (deterministic? per-quantity tolerances) | _____ |
| ⑪ | Debate panel size + structure — panel size cost-model-justified per ⑦; the portable quality mechanism = LENSED challengers (each owns an orthogonal lens + a decorrelated adversarial stance over a mandatory breadth floor, packed-by-N, aggregated as the UNION of valid catches) + a null-hypothesis advocate; the lens-SET is debate-type-specific; the lens-set AND the panel-size number are project-owned in the lens SSOT, NOT fixed in this portable core | _____ |
**Bootstrap order:** ① → ③ → ⑥ → ②④ → ⑤⑦ → ⑧⑨⑩⑪ (a minimal viable instance may start with ①③⑥ and grow).

## Provenance
Distilled from the THREAD/L0 robotics instantiation (first binding): named 2026-06-05; platform-swap invariance 2026-06-06; rules 2-6/9 first observed 2026-06-10 (the S5 engagement saga, 6 STOPs → 6 assets); hardened by a 5-body adversarial debate 2026-06-10 (record: `GROVE_5CC_DECIDE_2026-06-10.md`). Case studies and instance values live in the overview doc, not here.
