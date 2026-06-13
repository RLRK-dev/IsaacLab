# GROVE v1.1 — Improvement Proposal (2026-06-13)

**Author:** methodology-improvement draft agent (Opus 4.8) · **Status:** DRAFT, forward-only · **Stakes:** L3 methodology artifact · **Substrate:** THREAD/L0 robotics, first binding.

> **GROVE** = **G**ated **R**ole-**O**riented **V**erified **E**xecution — the multi-agent development methodology this project runs under. This document proposes refinements to **GROVE CORE SPEC v1.0** (`docs/GROVE_CORE_SPEC.md`) and folds the applicable, non-human-gated items from the v3 plan in `docs/GROVE_5CC_DECIDE_2026-06-10.md`. It is evidence-driven by the **2026-06-13** working session (the F1 rev8→10 chain, the 7CC strategy debate, the R-0 scoping pass, and that session's records corrections), recorded in `thread_isaac_lab/thread-vault/log.md` (entries 6330–6346) and the §28 reconcile docs under `eval_runs/troot_optE_s5b_lift_0gpu_20260611/`.

---

## 0. Version-control note (READ FIRST — the GROVE docs are untracked)

**FACT (verified `git ls-files` / `git status` 2026-06-13):** `docs/GROVE_CORE_SPEC.md`, `docs/GROVE_5CC_DECIDE_2026-06-10.md`, and the three `grove_methodology_*.html` files are **untracked** (`??`). The GROVE family has already burned itself once on this exact gap: the v1 HTML was unrecoverable and the sole pre-restructure copy survived only as an accidental `~/Downloads` 18:46 file — i.e. the doc violated its own forward-only principle (`GROVE_5CC_DECIDE_2026-06-10.md:15`, the CC6/NHA finding; post-pause step #1 = "version-control the doc BEFORE any rewrite").

**Therefore this proposal is FORWARD-ONLY and ADDITIVE:**
- It is a **NEW file** (`GROVE_V1.1_IMPROVEMENT_PROPOSAL_2026-06-13.md`). It does **NOT** overwrite `GROVE_CORE_SPEC.md` or any existing GROVE doc.
- It proposes deltas as *patches to be applied later, by a human-gated landing*, not as in-place edits now.
- **Recommended first action before any v1.1 landing:** `git add` the GROVE docs (or attach a vault sidecar `.sha256`), so the spec history is recoverable. This is itself an instance of CORE rule 7 ("artifacts forward-only; never overwrite") and pillar C6 freshness — the methodology should not be the one file that is unversioned.

**No governing-file edits were made by this agent.** Nothing here touches `CLAUDE.md`, `.claude/`, skills, or source. All SSOT landings are flagged PENDING-human in §6.

---

## 1. Scope of this proposal

| Bucket | Content | Landing |
|---|---|---|
| **A. Five refinements/new rules from this session** | SRG (new rule), conservatism-direction (refine rules 1/3), records-mechanics (sharpen rule 3 / freshness guards), count-at-gated-launches (refine rules 7/10), bounded pre-step (refine rule 4) | §2 — proposed into CORE SPEC; the rule-FILE landing is human-gated (§6) |
| **B. Panel-size as a binding** | C3 hardcodes "5-body"; make panel-size a binding-sheet row with the lensed-challenger mechanism | §3 — binding-sheet edit |
| **C. Candidate-rule confirmations** | Which of rules 2–6,9 got a *second* incident this session (strengthens promotion) | §4 |
| **D. v3-plan fold (non-human-gated)** | Items from `GROVE_5CC_DECIDE` that do NOT need the CLAUDE.md landing | §5 |
| **E. PENDING-human (L3 SSOT landing)** | Everything that DOES need the human-gated rule-file commit | §6 |

---

## 2. The five improvements (change · where · rationale · evidence)

### 2.1 — Substrate-Resolvability Gate (SRG) — **CANDIDATE NEW operating rule (proposed rule 11)**

**The change.** Add an operating rule:

> **Rule 11 — Substrate-Resolvability Gate (CANDIDATE).** Before any run whose verdict depends on a **fidelity-bound quantity** (friction / contact / creep / retention / any property the simulation models only approximately), pre-check three things: **(1)** is the substrate **production-solver-faithful**, or a **proxy**? **(2)** if a proxy, is a **landing/validity control ALREADY green** — i.e. demonstrated *before* this run, not *scheduled inside* this run? **(3)** is a **fidelity-INDEPENDENT redesign cheaper and already data-mandated**? A proxy that is default-NO on (2) MAY run **ONCE** as an explicitly **labeled scoping probe**, but **may NOT bind a verdict and may NOT self-iterate**. This generalizes rule 8 ("gate the PREMISE") to gate the **premise's RESOLVABILITY**: before asking *is the mechanism spec-faithful?*, ask *can this substrate even answer the question I am about to put to it?*

**Where it lands.** New CORE rule 11 in `GROVE_CORE_SPEC.md` §C4. Companion: a one-line pre-check item ("SRG: is the substrate able to resolve this verdict?") referenced from the VERIFY step in C3's workflow figure. The 7CC debate already specified the *lightweight* delivery form — Vault Knowledge + a pre-check item, **not** a heavy process rule (`STRATEGY_7CC_DECIDE.md:9,19`).

**Rationale.** A run on a proxy substrate that cannot resolve the question is not a cheap experiment — it is a *guaranteed* non-answer dressed as data, and it invites the "one more sourced param" accretion spiral. SRG caps that spiral *ex ante* at one probe.

**Evidence (2026-06-13 session).**
- **The noslip detour (rev8→9→10) was predictably doomed at launch.** The proxy was *pure-mujoco* loading a scratch MJCF; the production substrate is *newton SolverMuJoCo*. That mismatch was a **known substrate fact at launch** (the F1 chain had already booked newton's regularized friction "never sticks" as the #3328 pathology, `log.md:6318`). The chain then ran THREE revs — rev8 (3 unmirrored contact pokes, `log.md:6325`), rev9 (still no-repro, `log.md:6334`), rev10 (added the 2.5 N·m clamp, still no-repro, `log.md:6337`) — before the pre-registered ABANDON tripwire fired with the conclusion: **"the divergence is STRUCTURAL (solver-path + pad-mass); the noslip resolver is UNREACHABLE in this harness"** (`F1_REV10_SEC28_RECONCILE.md:20-21,26-27`). The leg-1 *validity control* (noslip=0 must reproduce rev7's wedge-hold) **never went green across all three revs** — exactly the SRG-(2) condition. SRG would have capped the detour **at 1 rev, not 3** — the 7CC debate states this explicitly: *"(Tested: caps the noslip detour at 1 rev, not 3.)"* (`STRATEGY_7CC_DECIDE.md:19`).
- **The debate independently re-derived this rule.** 7CC body B6 proposed the concrete SRG (`log.md:6340`; `STRATEGY_7CC_DECIDE.md:5(item5),9,19`) — an independent multi-agent confirmation that the gate is real, not an author's pet idea.

**Caveat (honesty).** This is observed in **one** binding (this session). Per the GROVE candidate-promotion convention it is **CANDIDATE**, to promote on a second binding's confirmation. But note its lineage is unusually strong: it is a *generalization of an already-CORE rule* (rule 8), and it was *independently surfaced by an adversarial panel*, not just by the lead.

---

### 2.2 — Conservatism-direction / asymmetric-informativeness — **refine rules 1 and 3**

**The change.** Add to the verdict discipline:

> Every sim/proxy verdict must **state its conservatism direction** for the question being asked. A sim is *conservative* for a question if it makes success **harder** than reality; *non-conservative* if it makes success **easier**. Consequence: a **non-conservative PASS needs real-world (or higher-fidelity) confirmation** before it transfers; a **conservative FAIL is conclusive** (if it fails even in the easy case, it fails in the hard case). A verdict that omits its conservatism direction is incomplete.

**Where it lands.** Refine CORE rule 1 (primary-modality / verification) and rule 3 (expected-values handover — extend so an expected outcome carries not only a provenance tag but, for transfer-relevant quantities, a **conservatism tag**). Also surface it in C3's "Observation" guidance (transfer validity is a property of the verdict, not just the number).

**Rationale.** Two sim verdicts with identical numbers can have *opposite* transfer value depending on which way the sim is biased. Treating a non-conservative PASS as ground truth is a silent over-claim; discarding a conservative FAIL as "just sim" wastes a conclusive result. Naming the direction makes the asymmetry explicit and routes follow-up correctly (a non-conservative PASS → escalate to confirmation; a conservative FAIL → bank it).

**Evidence (2026-06-13 session).** The **surface-route probe** decision (R-0 fork, Option A). %18's PV refinement, accepted by %12 (`log.md:6345`; `R0_SEC28_RECONCILE.md:17,22`): the #3328 pathology **removes stiction**, so in-sim *drag* is **EASIER than real-HW** → a "drag works" sim-PASS is **NON-CONSERVATIVE** (transfer-unconfirmable, especially since the project is sim-only and real-HW is out of scope), whereas a "drag **fails even in the easy sim**" is **CONCLUSIVE** (→ 爪). This exact reasoning **flipped the lead's recommendation** from A toward B (`log.md:6345`: "%12 UPDATED LEAN: FLIPS toward B … re-surfacing to human with the corrected trade"). A verdict-conservatism rule would have made this property a *required field* of the probe's design rather than a late PV catch. *(Reconcile note: the lead LEANS B yet the campaign still RUNS the A surface-route probe — consistent, not contradictory: under asymmetric-informativeness a "drag fails even in the easy sim" is conclusive-and-cheap, so the A-probe is worth one shot for its downside-protection even when the recommendation leans B; the human's unlimited-budget "try multiple" directive then dissolved the either/or entirely.)*

---

### 2.3 — Records-must-match-fact mechanics — **sharpen rule 3 / the freshness guards (pillar C1 / C6)**

**The change.** Promote three mechanical sub-rules into the records discipline:

> **(a) date-THEN-write, never write-then-fix.** Timestamps are fetched (`date`) *before* the line is written — *every* message, including one-liners and status pings. Flow-derived/pre-typed stamps are a known failure mode (they run 1–2 min fast). The standard is **zero divergence at write time**, not post-hoc correction.
> **(b) existence/state claims get same-turn on-disk verification + date-qualification.** A claim that an artifact exists / a process is RUNNING / a value is X is verified against disk **in the same turn** it is asserted, and is **time-qualified** ("as of HH:MM"). Unqualified `RUNNING`/`PENDING`/`exists` is prohibited.
> **(c) a supervisor/proxy "the human decided X" inference is verified against the human's verbatim before propagation.** An inferred human decision must be tagged as *inference* and reconciled against the human's actual words before any downstream agent treats it as fact.

**Where it lands.** Sharpen CORE rule 3 (handover/provenance) and the C1 freshness-guard pillar; in THREAD terms these tighten the existing `audit_thread_vault_current_state.sh --strict-log` / freshness gates. (a)/(b) are the binding's instantiation; (c) is the cross-agent provenance discipline that pairs with the mutual-catch chain (rule 8).

**Rationale.** Records that diverge from fact are not a cosmetic problem to fix later — the human directive is *"事実と異なってしまうのはだめだ"* (records-and-fact divergence is unacceptable), and the standard is **occurrence-zero, not post-hoc-repair**. A wrong record propagates: a mislabeled number drives a decision, an inferred "the human decided" becomes a falsely-authoritative directive.

**Evidence (2026-06-13 session) — three distinct incidents:**
- **(a) timestamp corrections.** %12 self-caught **pre-typed user-facing stamps** ("18:12/18:13 JST" were not date-fetched, ~1–2 min fast vs the real 18:11), and re-tightened the rule to *every* message incl. one-liners (`log.md:6328`; `F1_CHAIN_STATE_WRAP_20260611.md:16`).
- **(b) the +311mm frame-mix records error.** The R-0 directive wrote "the pipeline lifts **+311 mm** (LIFT_Z)" — **WRONG**: LIFT_Z=1.120 is the body6/wrist-frame z, **not** a lift distance (`task_config.py:94`, verified this session: `LIFT_Z = TABLE_HEIGHT + 0.320  # 1.120: body6 height (fingertip=0.900, 100mm above table)`). The "+311mm" was `1.120 (EE) − 0.809 (groove)` = EE-height-above-groove, a *different quantity*. The **actual lift is ~50–100 mm** (fingertip to z=0.900; SOMA says 50 mm). Owned and corrected, conclusion *strengthened* (`R0_SEC28_RECONCILE.md:11-12`; `log.md:6344`).
- **(c) the cap-resolution proxy-overstep that propagated.** %12's 20:25 "CAP UPDATE: 5CC baseline, 5-vs-7 A/B, 3CC superseded" was **WRONG** — it propagated %18's `[DEBATE_CAP_RESOLVED]` relay, which was **%18's inference, NOT the human's words**. The human had said only (i) a *temporary* one-off 7CC override ("一時的に") and (ii) a *future conditional* ("7CCが5CCより結果が良ければ恒久的に7CC"). The standing 3-vs-5 cap remained **separately pending**. %12's explicit lesson: *"a supervisor's 'the human decided X' inference must be verified against the human's verbatim before I propagate it as fact"* (`log.md:6341`; re-affirmed in the PV at `log.md:6342`).

---

### 2.4 — Count-at-gated-launches — **refine rules 7 and 10 (instrument-defect governance)**

**The change.** Add an instrument-defect governance discriminator:

> An **instrument defect's count increments at GATED launches**, not at completion-tooling / post-processing crashes. The count drives a **governance bound**: past a project-set threshold, all further repairs of that instrument default to **human GO** (the executor's self-iteration slot closes; a human GO can still authorize a repair). There is **no control-leg carve-out** (a defect caught by a landing control still counts — anti-softening).

**Where it lands.** Refine CORE rule 7 (STOP→asset conversion / instrument-scope dispositions — *what counts as a defect and where*) and rule 10 (runaway bounds — *the count is a budget that auto-escalates*). It interlocks the two: rule 7 says "convert each STOP into an asset"; this says "and the *tally* of instrument STOPs is itself a governance budget under rule 10."

**Rationale.** Without a counting rule the instrument-defect tally is ambiguous (does a crash in the result-extraction tooling count the same as a defect in the gated run?) and the governance bound it feeds becomes arguable. The discriminator keeps the count meaningful: it measures *defects in the thing being gated*, and it is anti-soften (no "but it was only the control leg" escape).

**Evidence (2026-06-13 session + the immediately-preceding 06-11 seat).** %18's **count=5 ruling** (`log.md:6326`; `F1_CHAIN_STATE_WRAP_20260611.md:6,16`): the rev8 leg-1 no-reproduction was classified **#5 by the letter** because it occurred at a **GATED launch**, whereas the rev7 result-extraction crash **stayed at 4** because it was **completion-tooling, not gated**. Principle stated verbatim: *"count at GATED launches"*; *"NO control-leg carve-out (anti-softening)"*; *"'no repair slot' binds %13 SELF-iteration only; human GO can authorize."* This count then **governed the entire 2026-06-13 session**: every subsequent result (rev9, rev10, R-0) re-affirmed "count=5 LIVE; any NEW defect (#6) = surface to human" (`log.md:6330,6334,6337,6338,6344,6345`), and the human GO at 15:48 was explicitly noted to "consume the count=5 human-default for THIS repair-relaunch" (`log.md:6330`).

---

### 2.5 — Bounded pre-step / interrogate-the-premise-before-hardening — **refine rule 4 (no-accretion / experience-first)**

**The change.** Add to the experience-feedback-first pillar:

> Before committing a **full design/build cycle to harden a mechanism**, run **ONE bounded, cheap pass** that interrogates whether the mechanism is **even needed** / whether a **cheaper alternative** exists / whether a **downstream stage** is the actual risk. The pre-step is explicitly **bounded** (one pass, no rev-chain, sim-needing branches are *flagged not launched*) so it cannot itself become accretion. Output re-ranks the plan and may *shrink or redirect* the mechanism before any geometry is committed.

**Where it lands.** Refine CORE rule 4 (smallest principled change → gated run → feedback; *reuse before rebuild*). This is the *interrogate-before-build* complement to *reuse-before-build*: rule 4 already says don't rebuild what exists; this adds don't *build at all* until a cheap pass confirms the build is the right move.

**Rationale.** A "fresh geometry cycle" is the expensive path; a bounded 0-GPU geometry read is the cheap path. Jumping to the build can harden a mechanism that a cheaper route would have *deleted*, or that a downstream wall makes premature. The bound (one pass, flag-don't-launch) is what distinguishes a legitimate pre-step from the accretion spiral the no-accretion rule forbids.

**Evidence (2026-06-13 session).** **R-0** is the rule working. After the human picked 爪 (a fresh fingertip cycle), the 7CC debate (bodies B4+B2) instead mandated a **bounded pre-爪 scoping pass** (`STRATEGY_7CC_DECIDE.md:7,13,16` R-0; `log.md:6340,6343`). The one-pass R-0 scoping (`R0_SCOPING_RESULT.md`; `R0_SEC28_RECONCILE.md`) then found, *before any 爪 build*:
- **insertion is GEOMETRIC form-closure, LOW-risk** (`create_clip.py:38-46`: a 30 mm/60° V-funnel → 12 mm U-groove captures the 8 mm cable with *no friction term*) — which **REFUTED** body-5's "insertion = the longest pole" (`R0_SEC28_RECONCILE.md:6`; `log.md:6344`);
- **the lift is small and maybe-droppable** (~50–100 mm, not the mis-recorded +311 mm; geometrically droppable — `R0_SEC28_RECONCILE.md:12,17`);
- **the friction wall is CONFINED to gripper free-air RETENTION** (`R0_SEC28_RECONCILE.md:15`), which **SHRUNK the 爪 scope to retention-only** (insertion excluded — `R0_SEC28_RECONCILE.md:18`; `log.md:6344`).

A fresh 爪 cycle committed *without* R-0 would have over-built (爪 covering insertion, which form-closure already handles) and possibly hardened a lift the route may not need. The pre-step's bound held: it was "ONE pass; needs-a-rev branches flagged-not-launched" (`R0_SEC28_RECONCILE.md:26`), and the lead explicitly tied it to the accretion lesson (`STRATEGY_7CC_DECIDE.md:13`: "ACCEPT as a BOUNDED 0-GPU scoping pass, NOT an open-ended new investigation (the accretion/removable-inefficiency lesson)").

---

## 3. Debate panel-size as a BINDING parameter — improve C3 + the binding sheet

**The change (two parts).**

**3a. Make panel size a binding, not a hardcoded constant.** C3 currently hardcodes *"5-body adversarial debate (4 challengers + 1 null-hypothesis advocate)"*. Replace the hardcoded count with a **binding-sheet row**:

> **Binding ⑪ — Debate panel size + structure.** The project declares its adversarial-debate panel size (and the cost model that justifies it). The default reference is 5-body (4 challengers + 1 NHA), but panel size is **project-tunable** against the binding's cost model (⑦).

**3b. The cost/quality mechanism = the LENSED challenger.** Specify how a *smaller* panel can still cover what a larger one did:

> Challengers are **lensed**: each challenger **owns an orthogonal lens** + enters from a **decorrelated adversarial stance**, while still sweeping a **breadth floor** (a mandatory coverage checklist every body must cover — so lensing adds depth without losing breadth), rather than N *identical* challengers. Lens-ownership is the mechanism that lets a smaller panel reach the coverage a larger undifferentiated panel reached; aggregation is **UNION of valid catches** (not select-best, which discards catches).

**CANONICAL DESIGN (align here — do NOT invent a parallel one).** The portable invariant is the *mechanism* (lens-ownership + a breadth floor + decorrelated stances + lens-packing-by-N + union aggregation). The **lens-SET is debate-type-specific** and its canonical instantiation is **%18's `eval_runs/model_strategy_post623_20260611/5cc_ab/challenger_prompts/percent18_lensed_v1.md`** (the SSOT for this binding's lensed challengers):
> - **Code-review/verification debates** (the verification-subagent path): 4 lenses — **A premise/provenance · B rule/SSOT · C numerical/physics · D side-effects+regression/history** — over the committed `challenger-prompt.md` V1–V6 floor, + one **blind/anti-anchoring** body, + the unchanged NHA. Lens-packing by N is FIXED in that doc (N=3: A+C and B+D merged + NHA; N=5: A/B/C/D + NHA; N=7: A/B/C/D + blind-A + a duplicate of the hard-class lens + NHA).
> - **Strategy debates** (deciding a direction, e.g. the 2026-06-13 7CC run): a strategy lens-set (feasibility / premise-skeptic / substrate-strategy / alt-architecture / roadmap / process / NHA). Same mechanism, different lenses.

**Where it lands.** C3 (replace the hardcoded "5-body" with a pointer to binding ⑪) + a new binding-sheet row (⑪) in §B of `GROVE_CORE_SPEC.md`. Also pairs with CORE rule 8 ("debate scaled by the L-tier") — panel size now has *two* knobs: L-tier (how big) and lens-set (how broad). **The concrete lens-set + packing is OWNED by %18's design SSOT and is being empirically validated by %14's seeded-defect A/B (LIVE); v1.1 must POINT to that SSOT, must NOT hard-code a config, and must NOT pre-empt the A/B's findings on which lens/seed wordings land the hard classes.**

**Rationale.** The hardcoded "5" is a binding value masquerading as a portable constant — exactly the de-domaining the v3 plan calls for elsewhere (`GROVE_5CC_DECIDE_2026-06-10.md:12,14`). Different projects have different per-body cost models (subscription quota vs per-token expense), so the *number* belongs in the binding sheet; the *structure* (lensed, breadth-floored) is the portable quality mechanism.

**Evidence (this session + the immediately-preceding cost ruling).**
- **The live 3/5/7 cap saga shows the number is genuinely contested and project-specific.** The 06-11 human ruling was **"3CCを最大数と確定する。5CCはコスト的に不可能である"** (3-max, 5 cost-infeasible — driven by *Fable* per-body expense). The 06-13 human direction was **"opus4.8による5CCDebateの改善"** (improve the Opus 5CC). These two first-hand human directives **conflict** and the cap remains **human-pending** (`log.md:6332,6333,6341`). A project where panel size is a *binding* (tied to the cost model, ⑦) makes this a clean binding-update, not a buried contradiction.
- **The 7CC trial demonstrated lensed-debate > solo, but NOT 7 > 5.** The one-off 7CC strategy debate (`log.md:6339,6340`) was *highly productive* — a 7-lens panel caught **5 of 7** things the solo lead's PROPOSE lacked (B1 category-error / B3+B7 over-broad doctrine / B4+B2 interrogate-the-lift / B5 risk-rank / B6 the SRG — `STRATEGY_7CC_DECIDE.md:4-9`). **But** the PV is precise (and this is the load-bearing methodological caveat): *"this run shows LENSED-DEBATE(7) > %12-SOLO-PROPOSE (5/7 lenses caught what CC1 lacked), NOT '7 beats 5' (no 5CC ran on the SAME subject)"* (`log.md:6342`). The clean test of the *cap* is a **same-subject, vary-ONLY-N A/B** (`log.md:6342,6340`) — which is **%18-owned and still pending**. So the binding-⑪ rationale is "panel size is a tunable that should be A/B-isolated," and the *lensed-challenger structure* is the mechanism that makes a smaller N viable — **not** a claim that more bodies are better.

> **Honesty flag:** do NOT let v1.1 imply "7>5" or "5>3". The session evidence supports (i) panel-size-is-a-binding and (iii) lensed>**solo**. Claim **(ii) lensed>undifferentiated is NOT yet clean — PENDING matched-tools v3.** %14's A/B run03 (landed 2026-06-13, relayed by %18) found the lensed>generic result CONFOUNDED by **tool access**: the lensed bodies had Bash/disk access and hit the real repo, while the generic baseline was bundle-only → structurally disk-blind → an unfair comparison (tool-access ≠ persona). The only **clean, isolated** persona effect so far is the **recompute-MANDATE** (Lens-C caught a defect via mandated Bash recomputation) — and that is *addable to a generic prompt*, i.e. a MANDATE win, not a persona win. So v1.1 supports the lensed *mechanism* as a binding-⑪ structure, but must NOT yet assert lensed>undifferentiated on quality; that awaits the matched-tools v3 (parallel to the N-ordering awaiting the same-subject vary-only-N A/B). Both are %14/%18-owned, pending.

---

## 4. Candidate-rule (2–6, 9) confirmations from this session

CORE SPEC §C4 marks rules 2–6 and 9 as **CANDIDATE** (first observed 2026-06-10, "promote on a second binding"). This session is still the *same* (first) binding, so these are **additional in-binding incidents** — they do not by themselves trigger promotion (that needs a *second* binding), but they **strengthen the promotion case** by showing the rules recur and bite across many independent gates, not just the one saga they were distilled from.

| Rule | What it says (abbrev.) | 2026-06-13 confirming incident(s) | Cite |
|---|---|---|---|
| **2 — Zero-claims need a true positive** | an instrument claiming "zero = OK" is uninterpretable until it shows a true positive (per configuration) | The **clamp bite true-positive** was *mandatory* before rev10's negative result could count: without 5.158 N·m demand → with capped EXACTLY 2.5 N·m, `bite_proven=true` — *"the clamp is not inert; the negative result is real, not a no-op artifact."* Directly invokes the xfrc-inert lesson. | `F1_REV10_SEC28_RECONCILE.md:3-7`; `log.md:6336,6337` |
| **3 — Expected-values handover (provenance tags)** | hand verifiers expected values/properties + provenance (measured/derived/authored) | The **segmass** reconcile: landed 1.124 g/seg (closed-form) = 45 g, vs the "0.8 g" log line = *cylinder-only authored-echo* print — an explicit measured-vs-authored provenance discrimination that corrected a propagated 32 g basis. | `log.md:6324,6325,6326`; `F1_CHAIN_STATE_WRAP_20260611.md:15` |
| **4 — Deviation auto-STOP + named exemptions** | re-runs auto-reconcile vs baselines; intended changes exempted BY NAME | rev8 **leg-1 landing control auto-STOPPED** on a deviation (out-of-class regime: gap 4.03/8.87, N 0/77) *before* any leg-2 verdict — the deviation-STOP firing pre-verdict, and the pad-mass change (12.5→3.5 g) was *disclosed by name* as a fidelity gate. | `log.md:6324,6325`; `F1_CHAIN_STATE_WRAP_20260611.md:14` |
| **5 — Dependency-set × deferred-list intersection** | each phase intersects its gate-dependencies with the design's deferred/pre-flagged list; non-empty ⇒ gate or argue | The rev8→9 diagnosis was exactly a dependency-set miss surfacing: **3 rev7 runtime pokes (solref/condim/roll) were in the gate's dependency set but not mirrored into the derived XML** → caught by the pad-row-vs-readback preflight assert that was then *added* to close the intersection. | `log.md:6325,6330` |
| **6 — Regime-conditioned metrics** | every metric declares its valid regime ex-ante; out-of-regime readings are artifacts | The **(a′)-airborne first-contact-with-an-uncalibrated-regime** pre-registration, and the **floor-aware criterion** (axial/vertical drift vs *matched-load floor*, NOT the 1 µm/s bar) — both explicit ex-ante regime declarations so out-of-regime readings book as artifacts not strikes. | `log.md:6316,6322,6323` |
| **9 — Measure anchors before pinning** | anchors/expectations measured in the operating regime; context change reopens calibration | The **noslip-toggle and e-curve true-positives measured in the harness's own regime** at preflight (140.2→1.841; q4 0.7407 EXACT) before any verdict; pose/load context changes (12.5→3.5 g pad mass) explicitly reopened the fidelity question. | `log.md:6324` |

**Net:** all six candidate rules recurred with fresh, independent incidents in this session. Promotion to CORE still awaits a **second binding** (a different project), per the convention — but the in-binding recurrence is strong corroboration that they are real operating rules, not artifacts of the one saga.

---

## 5. v3-plan fold — items that do NOT require the human-gated CLAUDE.md landing

From `GROVE_5CC_DECIDE_2026-06-10.md`, the following are **document/spec-level** edits to the GROVE docs themselves (forward-only, no governing-file change) and can land in v1.1 directly:

1. **Version-control the doc before any rewrite** (post-pause step #1; CC6/NHA finding `:15,18`). → §0 above; **do this first** (`git add` or vault sidecar hash). This is the single highest-priority non-gated item.
2. **De-domain residue in the spec** (CC3 `:12`): the spec is already largely de-domained, but the *binding* (`§B`) should carry the THREAD pointers; any remaining domain words move to *labeled examples*. (v1.1: the panel-size hardcode in §3 is one such residue — fold it.)
3. **Property tables where numbers don't exist** (CC5/CC3 `:12,14`): rule 3 already allows this in v1.0; v1.1 reinforces it in the conservatism-tag extension (§2.2) — a *conservatism* tag is a property even when the quantity is qualitative.
4. **Restore provenance/qualifier lines** the v2 overclaimed (CC6 `:15`): e.g. "vault LL lands at phase-completion" qualifier, the n=1-day / human-in-loop conditionality on the baseline numbers. These are doc-accuracy fixes, not rule changes.
5. **The candidate-core relabel** (rules 2–6 = "candidate, promote on 2nd binding") is already in CORE SPEC v1.0 §C4; v1.1 *adds the in-binding confirmation table* (§4) — strengthens, does not re-label.
6. **The "5-body" → binding** edit (§3) is a spec-text edit to C3 + the binding sheet; it does **not** alter any governing rule file, so it can land in the GROVE spec now. (The *operational* cap value — 3 vs 5 vs 7 — is human-pending; see §6. The spec change is just "make it a binding row.")

These are all edits to the **GROVE docs**, which are project artifacts, not governing rule files — so they do not need the L3 human gate. (They still benefit from the §0 version-control step first.)

---

## 6. PENDING-human — items requiring the L3 human-gated SSOT landing

Per `GROVE_CORE_SPEC.md:3` ("governance force comes from the project's own rule files once the core is landed there, **human-gated**") and `GROVE_5CC_DECIDE_2026-06-10.md:21` (the CLAUDE.md landing is "rs-gated L3; human-Rs 指示起点; until then the economy stays PENDING and CLAUDE.md governs"). **Nothing below has been landed by this agent.**

| Item | Why human-gated | Landing target |
|---|---|---|
| **Adding rule 11 (SRG) to the governing rule set** | a new operating rule that gates runs = methodology change = L3; rule FILES stay human-initiated | `CLAUDE.md` / `.claude/rules/` family + a vault LL Knowledge line (SRG was 7CC-specified as *lightweight*: Vault Knowledge + pre-check, not a heavy rule — `STRATEGY_7CC_DECIDE.md:19`) |
| **The conservatism-direction verdict requirement** (§2.2) becoming a *gate* | adds a required field to verdicts at gate points = verification-protocol change = L3 | `CLAUDE.md` §運用14/15 + the verification-subagent skill |
| **Records-mechanics (a)/(b)/(c)** becoming enforced gates (§2.3) | tightens the freshness guards / `--strict-log` behavior = SSOT-surface governance = L3 | `CLAUDE.md` §運用 + the `audit_thread_vault_current_state.sh` / freshness-guard wiring |
| **Count-at-gated-launches** as a governance bound (§2.4) | an instrument-defect *budget* that closes the executor's self-iteration slot = role-authority change = L3 | `CLAUDE.md` (instrument-defect governance) + the count ledger |
| **The panel-size CAP value** (3 vs 5 vs 7) — *the number*, not the binding-row mechanism | two conflicting *first-hand* human directives (06-11 "3確定" vs 06-13 "5改善") + a future-conditional "7 if 7>5"; the standing cap is explicitly **human-pending**; touching the panel size touches `verification-subagent/SKILL.md` + challenger-prompt + `CLAUDE.md §運用2/§運用15` ⇒ L3 (`log.md:6332`) | human decision FIRST, then `CLAUDE.md` + skill landing. **Blocked on:** the same-subject vary-only-N A/B (%18-owned) to isolate the cap. |
| **Bounded-pre-step** as a mandated rule-4 sub-step (§2.5) | changes the workflow before a build cycle = methodology change = L3 | `CLAUDE.md` §運用2/§運用24 |
| **The full v3 rewrite + the v2 restructure landing** | held by the standing human-Rs pause (`GROVE_5CC_DECIDE_2026-06-10.md:1,3,17`) | per the post-pause execution order, human-initiated |

> **Process note (consistent with the methodology itself):** this proposal is the *drafting* leg. The mutual-catch chain (CORE rule 8) requires that this draft be **independently reviewed** (a reviewer ≠ this drafter), and the SSOT items above require the **human L3 gate**, before any of it becomes governance. The drafter does not self-approve an L3 methodology change.

---

## 7. Open questions / honest gaps

1. **Second-binding evidence is absent.** SRG and the rule-2–6/9 confirmations are all *first-binding*. None can promote to CORE until a *different project* confirms them. v1.1 should keep them CANDIDATE and say so.
2. **The panel-size A/B has not run, AND lensed>undifferentiated is confound-blocked.** Every claim about N (3/5/7) is bounded by "lensed > **solo**," NOT "more bodies better" — do not drift into an N-ordering claim (awaits the same-subject vary-only-N A/B). Separately, **"lensed > undifferentiated" is PENDING matched-tools v3**: %14's run03 confounded it with tool access (lensed bodies had disk/Bash, the generic baseline was bundle-only/disk-blind). The clean isolated persona win so far = only the recompute-MANDATE (addable to a generic prompt). Both isolations (cap N, lensed-vs-generic) are %14/%18-owned and pending.
3. **SRG's exact trigger boundary** (which quantities are "fidelity-bound") is project-specific and lives in the binding (⑤/⑦), not the portable rule. The portable rule states the *test*; the binding states *which substrates/quantities* it fires on.
4. **Conservatism-direction can be hard to determine** for some quantities (a sim may be conservative on one axis, non-conservative on another — exactly the rev7 "both legs substrate-confounded, opposite directions" case, `log.md:6317`). The rule should require *stating the direction per axis*, and allowing "unknown — needs determination" as an honest value rather than forcing a guess.

---

*End of proposal. No governing files were modified. Version-control the GROVE docs (§0) before any landing.*
