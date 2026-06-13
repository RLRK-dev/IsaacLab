# Skill-Improvement Program — landing this session's lessons into the project skills (2026-06-13)

**Status:** DRAFT — forward-only, non-governing. Track 4 of the 2026-06-13 autonomous window (alongside T1 retention, T2 GROVE v1.1, T3 video-analysis).
**Author:** skill-improvement draft agent (Opus 4.8, executor). **Drafter ≠ reviewer:** this doc requires `%12` on-disk reconcile + `%18` independent PV + a human L3-landing decision before anything lands. It is the PROPOSE; it is not self-approving.
**Trigger:** human-Rs (2026-06-13) "improve the project's skills + use them to improve outcomes (NOT delete them)", reinforced by the 22:12 challenge 「別のskillも用意されているが不要なのか？」 — `log.md:6355`: the autonomous window **under-used the formal forced gates** (爪 designs done "in the style of" `/geometric-design` but the gate was never formally invoked; the 7CC was a custom debate not `/verification-subagent`; `/pre-check` + `/verify-run` + `/video-analyzer` not formally run). That is the meta-finding this program addresses: the skills are largely **sound but bypassed**, so the fix is **targeted content additions that make the right path cheaper + harder to skip**, not new subsystems.

---

## §0. Version-control & forward-only note (READ FIRST)

**This is a NEW file** (`docs/SKILL_IMPROVEMENT_PROGRAM_2026-06-13.md`). It overwrites nothing. It edits **no** governing file — not `CLAUDE.md`, not `.claude/rules/`, not any `.claude/skills/*/SKILL.md`, not source.

**FACT (verified `git status` 2026-06-13 22:18 JST):** the two sibling improvement drafts and the GROVE spec family are **untracked** (`??`): `docs/GROVE_V1.1_IMPROVEMENT_PROPOSAL_2026-06-13.md`, `docs/VIDEO_ANALYSIS_SKILL_IMPROVEMENT_2026-06-13.md`, `docs/GROVE_CORE_SPEC.md`. Same gap the GROVE family already burned itself on once. **Recommended first action before any landing from this program: `git add` these `docs/` artifacts (or attach a vault sidecar `.sha256`)** so the proposal history is recoverable.

**Every skill landing in this program is an L3 change, human-gated**, per `CLAUDE.md §0` L3 auto-promotion keywords — path match on `.claude/skills/*/SKILL.md` workflow/protocol. This is itself the subject of §7 (`rule-check` consistency check): the program is correctly self-classifying as L3, and `rule-check` Stage 1 already covers it with **no change needed**. Each item below is tagged **[PENDING-human, L3]**.

**Mutual-catch chain for THIS artifact** (GROVE rule 8 / the project's standing mutual-catch): drafter = this agent → reconcile = `%12` (on-disk: every `file:line` citation resolves) → PV = `%18` (independent) → human L3-landing decision. The drafter does not self-approve an L3 methodology/skill change.

**Relationship to the two sibling drafts (do NOT duplicate — map + reference):**
- `GROVE_V1.1_IMPROVEMENT_PROPOSAL_2026-06-13.md` is the **portable-methodology layer** (the GROVE CORE SPEC). It states the *portable rules* (SRG, conservatism-direction, records-mechanics, count-at-gated-launches, bounded-pre-step, panel-size-as-binding+lensed). **This program is the THREAD-skill instantiation of those same rules** — it lands each portable rule into the specific skill that executes it. GROVE = the invariant; the skill = the binding's instrument. The two-container discipline (GROVE rule, CLAUDE.md/skill instantiation) is honored: this doc points to the GROVE rule rather than restating it.
- `VIDEO_ANALYSIS_SKILL_IMPROVEMENT_2026-06-13.md` already owns the **video-first enforcement + junk-frame/NaN-truncation** content for `video-analyzer`/`verify-run`/`log-analyzer`. **§2 of this program does NOT re-specify those items** — it cross-references that draft and only adds the *non-video* parts of the `verify-run`/`video-analyzer` story (the verdict-machinery framing + how the program's six skills interlock). Where the video draft already has the change, this doc says "see the video draft" and stops.

---

## §1. The gap, stated precisely (which axis is broken)

Two distinct failures this session, and the fix differs by axis:

| Axis | Status (verified on disk) | Evidence |
|---|---|---|
| **A. Skill content** | Mostly GOOD, with a few **real missing branches** (a substrate-resolvability pre-check; an axis-resolved retention check; a named substrate-fidelity diagnostic branch; an instrument-defect index into existing LL docs). | per-skill in §2 below; each gap re-verified against the current `SKILL.md` |
| **B. Application discipline (the dominant gap)** | BROKEN. The skills EXIST and are forced gates, but the autonomous window **bypassed** them for "in-the-style-of" informal work. | `log.md:6355` (22:12): "爪 B1/B2 designs done by general-purpose agents 'in the style of' /geometric-design but the FORCED gate was NOT formally invoked; 7CC was a custom debate not /verification-subagent; /pre-check + /verify-run + /video-analyzer not formally run … this is a compliance gap." |

**Implication for this program (anti-accretion, GROVE rule 4):** because axis B (bypass) dominated, the highest-value move is **not** bulk new content — it is (i) the few genuinely-missing branches in §2, and (ii) keeping the additions small enough that the forced gates stay cheap to *actually run*. The corrective the lead already adopted at `log.md:6355` ("HOLD the μ0 build; formally run /geometric-design … then /pre-check … then /verify-run + /video-analyzer") is the *behavioral* fix; this program is the *content* fix that makes those gates land this session's lessons when they ARE run.

---

## §2. Per-skill improvements (change · where · rationale · session evidence · L-flag)

Six target skills. For each: the gap is re-verified against the **current** `SKILL.md` on disk (cited), the change is concrete and bounded, and the session evidence is `file:line`.

---

### 2.1 — `pre-check` — add the **Substrate-Resolvability Gate (SRG)** as a pre-check branch

**Gap (verified).** `pre-check/SKILL.md` is entirely **reward/learning-signal-oriented**: its analysis framework is REACHABILITY / DEADLOCKS / SPARSE SIGNALS / THRESHOLD GAPS / CAUSAL BREAKS (`pre-check/SKILL.md:82-93`), and its self-check is reward-reachability / gated-reward / success-AND-clauses / parameter-sanity / training-budget (`:135-148`). **There is no item that asks whether the substrate can even resolve the verdict the run is about to produce.** A friction/contact/retention probe on a too-lossy proxy passes every existing `pre-check` item (it has a reward path, reachable thresholds, etc.) and still produces a guaranteed non-answer. The gap is real.

**The change.** Add an SRG branch to `pre-check`, fired when **the run's verdict depends on a fidelity-bound quantity** (friction / contact / creep / retention / any property the sim models only approximately). Three questions, each a one-line check:
1. **Production-solver-faithful or proxy?** Is the substrate the production path (`newton SolverMuJoCo`), or a stand-in (e.g. pure-mujoco loading a scratch MJCF)?
2. **If a proxy — is the landing/validity control ALREADY green?** Demonstrated *before* this run, not *scheduled inside* it. (The leg-1 "the proxy reproduces the production pathology" gate must already have passed in a prior run.)
3. **Is a fidelity-INDEPENDENT redesign cheaper and already data-mandated?**

Disposition: a proxy that is **default-NO on (2)** MAY run **ONCE** as an explicitly **labeled scoping probe**, but **may NOT bind a verdict and may NOT self-iterate**. Add a new self-check line and a new `VERDICT` route `SRG_PROBE_ONLY` (distinct from BLOCK/WARN/PASS): the run is allowed once, labeled, non-verdict-binding.

**Where it lands.** `.claude/skills/pre-check/SKILL.md`: (a) a new analysis-framework item "6. SUBSTRATE-RESOLVABILITY" in the verifier prompt (`:82-93`); (b) a new self-check line in the `[PRE-CHECK SELF-CHECK]` block (`:135-148`): `[ ] If the verdict is fidelity-bound (friction/contact/retention): substrate production-faithful OR (proxy + landing-control already green) OR fidelity-independent alt is cheaper. Default-NO proxy → SRG_PROBE_ONLY, one labeled probe, no verdict-binding.`; (c) the `SRG_PROBE_ONLY` row in the Step-4 result table (`:113-118`). **[PENDING-human, L3]**

**Cross-reference.** This is the THREAD `pre-check` instantiation of GROVE v1.1 §2.1 (proposed CORE rule 11). The 7CC debate specified the SRG as **lightweight: Vault Knowledge + a pre-check item, NOT a heavy process rule** — `STRATEGY_7CC_DECIDE.md:9,19` ("deliver it LIGHTWEIGHT (Vault Knowledge + pre-check, not a heavy process rule)"). Landing it as a `pre-check` branch (not a new gate/Phase) is exactly that lightweight form, and respects the CLAUDE.md hard-stop on new gates.

**Rationale.** `pre-check`'s whole reason-to-exist is "cost of pre-check failure: hours to days … the 30-second pre-check that asked the right question" (`pre-check/SKILL.md:20-26`). The SRG is the same medicine for the substrate axis: a 30-second question ("can this substrate answer what I'm about to ask it?") that caps a multi-rev non-answer at one probe.

**Session evidence.**
- **The noslip detour (rev8→9→10) was doomed at launch and ran 3 revs.** The proxy was *pure-mujoco loading a scratch MJCF*; production is *newton SolverMuJoCo* — a known substrate fact at launch (`log.md:6322`: "pure-mujoco harness loads the scratch V30L10 MJCF directly"). The leg-1 validity control (noslip=0 must reproduce rev7's wedge-hold) **never went green across all three revs**: rev8 no-repro (`log.md:6325`), rev9 still no-repro after a working repair (`log.md:6334`), rev10 ABANDON-tripwire-fired with the conclusion **"the residual is STRUCTURAL (pad inertia 3.5 vs 16g + solver-path newton-SolverMuJoCo vs vanilla) → noslip resolver UNREACHABLE in this harness"** (`log.md:6337`; `F1_REV10_SEC28_RECONCILE.md:20-21,26-27`). That is precisely the SRG-(2) condition: the landing control never green ⇒ cap at one probe. The 7CC debate states the cap effect verbatim: *"(Tested: caps the noslip detour at 1 rev, not 3.)"* (`STRATEGY_7CC_DECIDE.md:19`).
- **The REVS1 surface-route was SRG-default-NO and cost an instrument defect.** REVS1 ran a drag probe on the substrate; `%18`'s ruling: SRG **predicted** the #3328 NaN and the run cost the count's #6 (`log.md:6352`: "SRG VALIDATED (REVS1 SRG-default-NO predicted the #3328 NaN + cost #6)"). A pre-flight SRG would have flagged it as `SRG_PROBE_ONLY` (one labeled probe, no verdict-binding) before launch.
- **The debate independently re-derived the gate** (7CC body B6, `log.md:6340`; `STRATEGY_7CC_DECIDE.md:9,19`) — multi-agent confirmation it is real, not a pet idea.

---

### 2.2 — `verify-run` + `video-analyzer` — video-first ENFORCEMENT + junk-frame/NaN truncation **(primarily covered by the video draft; this section maps + adds the non-video half)**

**Status: the core content is ALREADY drafted.** `VIDEO_ANALYSIS_SKILL_IMPROVEMENT_2026-06-13.md` owns:
- **B1/B2 video-first enforcement** (motion-bearing sim result ⇒ video leg mandatory-or-justified; the `VIDEO_LEG_REQUIRED` machine-decided flag) — that draft §3 (`:82-93`), ranked #1 there.
- **A1 junk-frame / NaN-tail metric-truncation guard** (detect the NaN/divergence frame, truncate the metric window, void post-NaN aggregates, emit `metric_valid_until_frame=N`) — that draft §2 A1 (`:42-47`), ranked #2 there.

**This program does NOT re-specify those.** It cross-references them and adds only the parts the video draft does not cover:

**Add 2.2a — frame the bypass as VERDICT-MACHINERY in `verify-run` (not just "missing video").** The session's lesson is sharper than "look at video": the REVS1 #6 was a **false verdict produced at a gated launch** because the F-drag metric averaged through a post-NaN void. `verify-run` already has the "数値PASS + 視覚FAIL → 視覚を信じる" rule (`verify-run/SKILL.md:136-138`) and an "動画なし + 数値のみ → INCONCLUSIVE" rule (`:138,188`). Add one row to the §2.3 不一致パターン table and the §195 known-anomaly table: **"metric computed across/after a NaN or teleport frame → ARTIFACT, void the metric; the hand-verified trajectory governs"** — i.e. a metric is not just lower-priority than video, a *post-divergence* metric is **void**, full stop. This is the `verify-run`-side complement to the video draft's A1 (which lives in `video-analyzer`/`log-analyzer`): `verify-run` is where the *cross-modal verdict* is issued, so the "void, don't down-weight" rule belongs in its 照合 table too.

**Add 2.2b — the omission-justification line in `verify-run`'s final report.** The video draft B1 puts the mandatory-or-justified gate in `CLAUDE.md §運用15`; the matching `verify-run` report row ("video leg: present-via-skill / justified-omission / INCONCLUSIVE_visual") is the skill-side surface. This program notes it so the two land together; the spec is the video draft's (A2/B2), not re-authored here.

**Where it lands.** `.claude/skills/verify-run/SKILL.md` §2.3 不一致パターン (`:132-138`) + §195 known-anomaly table; the report template §3 (`:144-183`). The `video-analyzer`/`log-analyzer` NaN-truncation machinery itself = **the video draft's A1**, not duplicated here. **[PENDING-human, L3]**

**Rationale.** `verify-run`'s entire premise is "片方のverdictで他方の解釈を上書きしない … 不一致時は視覚を優先" (`:36`, `:186`). The NaN-void case is a *third* failure mode beyond agreement/disagreement: the numeric verdict is not "wrong relative to video", it is **internally void** (computed out of its valid regime). GROVE rule 6 (regime-conditioned metrics): a post-divergence metric is out-of-regime by construction. `verify-run` is the right home for the "void it" disposition because it is the skill that decides the final cross-modal verdict.

**Session evidence.** `log.md:6352` (21:43, `%18` FINAL ruling): "the F-metric pollution PRODUCED A FALSE VERDICT at a gated launch = verdict-machinery = rev8-class" → the count went to **#6** (`log.md:6353`: "count = 6 FINAL"). The correct read was the hand-verified npz trajectory (stable f632-643 → f644 −45 mm jump → f646 NaN, `log.md:6350`); the metric averaged through the post-NaN void. The whole F1/REVS1 chain ran motion-bearing legs with **manual single-frame Reads, not the `/video-analyzer` skill** (`log.md:6354`: "UNDER-RIGOROUS (manual single-frame, NOT the /video-analyzer skill) + INCONSISTENT (REVS1 leaned npz + %18 frames, no own-video)").

**Honesty flag (from the video draft, carried):** do not claim these changes "eliminate" the gap; claim they "convert a silent void into a loud, recorded one" — the verifiable property (`VIDEO_ANALYSIS_SKILL_IMPROVEMENT_2026-06-13.md:100`).

---

### 2.3 — `verification-subagent` — **lensed-challenger structure + panel-size-as-a-parameter**, plus conservatism-direction + gate-the-premise discipline

**Gap (verified).** `verification-subagent/SKILL.md` **hardcodes the 5-body panel** ("5 sub-agents (CC2-6)", `:6`, `:194`) and ships **identical** challenger bodies — all five get `challenger-prompt.md` verbatim (`:201-202,217`). The skill's own Limitation 5 names the cost of this: "No model diversity … Shared blind spots" (`:424`). The committed `challenger-prompt.md` already forces a **V1-V6 breadth floor** (`challenger-prompt.md:48-66`) and explicitly says its rationale is "When 4 challengers share the same prompt, they tend to fragment coverage … Explicit checklist enforces 4x redundancy" (`:55-57`). So the skill has the **breadth floor but not the depth/decorrelation mechanism** — and the panel size is a constant, not a parameter. Both gaps are real.

**The change (three parts, all aligned to `%18`'s canonical SSOT — do NOT invent a parallel design).**

The canonical lensed design is **`eval_runs/model_strategy_post623_20260611/5cc_ab/challenger_prompts/percent18_lensed_v1.md`** (`%18`-authored, the SSOT for this binding's lensed challengers). The portable invariant is its *mechanism*; the lens-SET and packing are owned by that doc and being empirically validated by `%14`'s seeded-defect A/B (LIVE). This program **points to that SSOT and must NOT hard-code a config**.

**(a) Lensed challengers over the V1-V6 floor.** Replace "5 identical bodies" with: each body keeps the **V1-V6 breadth floor verbatim** (so breadth is retained) **but is seeded to go DEEP on one orthogonal lens + enters from a decorrelated adversarial stance**. The code-review lens-set (per `percent18_lensed_v1.md` §1-§4): **Lens A premise/provenance · Lens B rule/SSOT · Lens C numerical/physics · Lens D side-effects+regression/history**, + one **blind/anti-anchoring** body (the PROPOSE-withheld variant, `percent18_lensed_v1.md:105-118`), + the unchanged NHA. Aggregation = **UNION of valid catches** (NOT select-best — select-best discards catches; `percent18_lensed_v1.md:5,133`).

**(b) Panel size as a PARAMETER, not the constant "5".** Replace the hardcoded "5" with a panel-size parameter whose **packing-by-N is FIXED in `%18`'s doc** (`percent18_lensed_v1.md:126-129`): **N=3** = 2 challengers (Lens A+C merged, Lens B+D merged) + NHA; **N=5** = Lens A/B/C/D one-each + NHA; **N=7** = A/B/C/D + blind-A + a duplicate of the hardest-class lens + NHA. **The cap value (3 vs 5 vs 7) is NOT set here.** It is human-pending and `%14`-A/B-bound (see the BLOCKED note below); the skill text should reference the parameter + `%18`'s packing table and leave the *number* to the human decision + the A/B.

**(c) Add conservatism-direction + gate-the-premise to the challenger discipline.** Two discipline lines, both already latent in `%18`'s lens seeds:
- **Conservatism-direction (the lensed-C / premise discipline):** when a challenge concerns a sim/proxy verdict that must transfer, require it to **state the verdict's conservatism direction** — a non-conservative PASS (sim makes success *easier* than reality) needs higher-fidelity confirmation; a conservative FAIL (fails even in the easy case) is conclusive. This is the GROVE v1.1 §2.2 rule, landed as a challenger check.
- **Gate-the-premise (Lens A, the documented-miss axis):** the first challenger question is not "is the code correct?" but "what unstated assumption does this rest on, and is it spec-faithful + provenance-checked?" — `percent18_lensed_v1.md:55` already states this stance; promote it from the A/B-only prompt into the skill's challenger guidance (a metric must **prove the property**, not merely reconcile numbers; byte-identical-across-conditions = artifact red flag — `percent18_lensed_v1.md:60`).

**Where it lands.** `.claude/skills/verification-subagent/SKILL.md`: the panel-size constant (`:6,194`) → a parameter + a pointer to `percent18_lensed_v1.md`'s packing table; the "all 5 receive `challenger-prompt.md`" assembly (`:201-202,217`) → "each body = [the V1-V6 floor] + [its lens seed]" per `percent18_lensed_v1.md:124`; a discipline note under "Known Lie Patterns" (`:366`) adding the conservatism-direction + gate-the-premise checks. The lens SEEDS themselves are NOT copied into the SKILL.md — the skill points to the SSOT doc. **[PENDING-human, L3]**

**BLOCKED / do-NOT-hard-code (critical).** The **cap value stays human-pending** and the lensed>generic *quality* claim is **confound-blocked** — the skill text must NOT assert either:
- The cap is contested by two **first-hand** human directives: 06-11 「3CCを最大数と確定する。5CCはコスト的に不可能である」 (Fable per-body cost) vs 06-13 「opus4.8による5CCDebateの改善」 (`log.md:6332,6333`). Both first-hand; standing 3-vs-5 cap separately pending (`log.md:6341`). The clean test is a **same-subject, vary-only-N A/B** (`%18`-owned, pending — `log.md:6342`).
- The 7CC trial showed **LENSED-DEBATE(7) > %12-SOLO-PROPOSE** (5/7 lenses caught what CC1 lacked), **NOT "7 beats 5"** (no 5CC ran on the same subject) — `log.md:6342`. And **"lensed > undifferentiated" is itself confounded** by tool-access in `%14`'s run03 (lensed bodies had Bash/disk; the generic baseline was bundle-only/disk-blind) — the only clean isolated persona win so far is the **recompute-MANDATE** (generic-addable) — `log.md:6349`. So the skill may land the *mechanism* (lensed structure + parameterized N) but must NOT claim N-ordering or persona-superiority; both isolations are `%14`/`%18`-owned and pending.

**Rationale.** The hardcoded "5" is a binding value masquerading as a portable constant; the lensed structure is the mechanism that lets a *smaller* N reach the coverage of a larger undifferentiated panel (depth via lens-ownership, breadth via the retained V1-V6 floor). This is the GROVE v1.1 §3 binding-⑪ rule, landed in the skill that runs the debate. It also directly addresses the session's `%12`-solo limitation: the 7CC ran as a *custom* debate, not the skill (`log.md:6355`) — parameterizing the skill (N + lens-set) makes the formal `/verification-subagent` able to host strategy debates too (a strategy lens-set is `percent18_lensed_v1.md`'s second mode).

**Session evidence.** 7CC productivity + the precise non-claims: `log.md:6340` (B1 category-error / B3+B7 doctrine / B4+B2 interrogate-the-lift / B5 risk-rank / B6 SRG), `log.md:6342` (lensed>solo NOT 7>5), `log.md:6349` (lensed>generic confounded by tool-access; recompute-MANDATE the only clean win), `log.md:6332` (L3 + cap contradiction on disk). The lensed SSOT: `percent18_lensed_v1.md:5,55,60,124,126-129,133`.

---

### 2.4 — `geometric-design` — **bounded pre-step (R-0)** + **axis-resolved-retention validation**

**Gap (verified).** `geometric-design/SKILL.md` is a thorough *full-cycle* protocol — 6 steps from 実測 → 制約 → 断面図 → trade study → reality-check → record (`:60-309`). It has **no "is the mechanism even needed?" pre-step**: it assumes the geometry cycle is the right move and proceeds to measure/constrain/visualize. And while Step 5c (`:242-281`) traces dynamic causality, **it has no axis-resolved retention check** — nothing that says "a longitudinally-open enclosure retains the enclosed DOFs but NOT the axial/roll-out DOFs, and contact-presence ≠ friction-independent retention." Both gaps are real, and both bit this session.

**The change (two parts).**

**(a) A bounded pre-step before Step 1.** Add **Step 0 — Interrogate-the-mechanism (BOUNDED, one pass):** before committing the full geometry cycle, cheaply answer: (i) is the mechanism **even needed**, or does a cheaper route delete the load case? (ii) is there a **cheaper alternative** (a salvage of the existing geometry)? (iii) is a **downstream stage** the actual risk? The step is explicitly **bounded** — ONE pass, no rev-chain, sim-needing branches are **FLAGGED not launched** — so it cannot itself become accretion. Output re-ranks the plan and may *shrink or redirect* the mechanism before any geometry is committed. This is the GROVE v1.1 §2.5 / GROVE rule-4 bounded-pre-step, landed as `geometric-design` Step 0.

**(b) Axis-resolved-retention validation in Step 5 / 5c.** Add: **claim retention ONLY on the DOFs the geometry actually encloses.** A retention design must enumerate the cable DOFs (vertical / down-out / up-escape / **axial slide** / **roll-out**) and mark each **enclosed** (geometrically captured) or **friction-bound/carried** (still relies on friction → unvalidatable on a never-sticks substrate). The **falsifier of friction-independence is a μ0 (frictionless) form-closure run** — passing geometry + contact-presence at real μ proves only "contact happens", NOT "retention is friction-independent". Add the corresponding anti-pattern row: "claim retention from contact-presence at real μ" → "prove friction-independence with a μ0 form-closure run; carry the open-DOF residue explicitly."

**Where it lands.** `.claude/skills/geometric-design/SKILL.md`: a new **Step 0** before 実測 (`:60-62`); an addition to Step 5/5c (`:194-281`) for axis-resolved retention + the μ0 falsifier; two new rows in the アンチパターン table (`:348-365`). **[PENDING-human, L3]**

**Rationale.** Step 0 is the *interrogate-before-build* complement to the skill's existing *reuse-before-build* posture — `geometric-design` already forbids workarounds-as-starting-points (`:30-33`); the pre-step adds "don't build *at all* until a cheap pass confirms the build is the right move." The axis-resolved check closes the category error the skill's static-geometry focus permits: an enclosure that looks closed in a cross-section (Step 3) can be axially/roll-open in the DOF that actually fails.

**Session evidence.**
- **R-0 is the bounded pre-step working.** After the human picked 爪 (a fresh fingertip cycle), the 7CC debate (B4+B2) mandated a **bounded pre-爪 scoping pass** instead (`STRATEGY_7CC_DECIDE.md:7,13,16`; `log.md:6340,6343`). The one-pass R-0 (`R0_SEC28_RECONCILE.md`) found, **before any 爪 build**: insertion is GEOMETRIC form-closure / LOW-risk (`create_clip.py:37-46`: 30 mm/60° V-funnel → 12 mm U-groove captures the 8 mm cable with no friction term — verified on disk this session) — which **REFUTED** body-5's "insertion = longest pole" (`R0_SEC28_RECONCILE.md:6`; `log.md:6344`); the lift is small/maybe-droppable (~50-100 mm, not the mis-recorded +311 mm — `R0_SEC28_RECONCILE.md:11-12`); the friction wall is **CONFINED to gripper free-air RETENTION** → **SHRUNK the 爪 scope to retention-only**, insertion excluded (`R0_SEC28_RECONCILE.md:15,18`; `log.md:6344`). A fresh 爪 cycle committed without R-0 would have over-built (爪 covering insertion, which form-closure already handles). The bound held: "ONE pass; needs-a-rev branches flagged-not-launched" (`R0_SEC28_RECONCILE.md:26`).
- **The axis-resolved gap is the 7CC B1 CRITICAL catch.** "S-B's validate-by-geometry+contact-presence is a CATEGORY ERROR for the axial/roll-out DOFs … a longitudinally-open hook does NOT enclose the cable's AXIAL slide (rev7's −40 mm pure-substrate coast) or the rigid-capsule ROLL-OUT (`task_config.py:170-172`: cable escapes by log-rolling; impratio/solref/noslip INERT until rolling rows exist) … 爪 could ship a FALSE in-sim PASS" → FIX = "axis-resolved validation + a **μ0 form-closure falsification run** (the rev6 test) as the actual proof of friction-independence" (`STRATEGY_7CC_DECIDE.md:5`; `log.md:6340`). `%18` confirmed the μ0 gate is the proven falsification instrument (`log.md:6342`: "μ0-gate = proven falsification instrument per rev6"). `task_config.py:170-172` verified on disk this session (the condim/log-rolling comment is real).

---

### 2.5 — `physics-diagnosis` — **substrate-fidelity facts as a named diagnostic branch (pointer into the existing LL docs)**

**Gap (verified, with an important no-duplication finding).** `physics-diagnosis/SKILL.md` Step 3 enumerates explosion causes — J3 saturation / cable tension / cable-shape / solver-state accumulation / IK-target-size (`:60-126`) — and has a Cable-Model-Mismatch branch (`:159-184`) and a Newton-vs-PhysX table (`:186-194`). **It has no branch for the substrate-FIDELITY pathologies** that dominated this session: regularized friction that never sticks; `xfrc_applied` inert on SolverMuJoCo CPU; pure-mujoco ≠ newton structurally; a sudden-NaN-after-stable-tracking that is the table-drag substrate wall, not a control bug. **Critically, these facts already have dedicated Knowledge LL homes** (verified on disk): `LL-Xfrc-Inert-Actuation-TruePositive.md`, `LL-Condim-Rolling-Mechanism.md`, `LL-Creep-Characterization.md`, `LL-G3-Vacuity.md`, and `LL-Newton.md` (#3328 at `LL-Newton.md:696-710`). So the change is a **pointer/index branch, NOT a restatement of the facts** — duplicating them into the skill would violate the no-duplicate-creation rule and create a drift-prone second SSOT.

**The change.** Add a new Step-3 branch **"3f: Substrate-fidelity pathology (Newton / SolverMuJoCo)"** that is an **index of named patterns → their existing LL doc**, each with a one-line symptom and the diagnostic question "is this a control bug or a substrate-fidelity wall?":
- **Regularized friction never sticks (#3328):** zero-deceleration linear coast, no force source → `LL-Newton.md:696-710` (+ `LL-Creep-Characterization.md`). Symptom: rigid-body axial slip through a stationary grip, perfectly linear, zero decel.
- **`d.xfrc_applied` inert on SolverMuJoCo CPU:** force/drive channels silently no-op → `LL-Xfrc-Inert-Actuation-TruePositive.md`. Diagnostic mandate: a force/drive channel needs a **landing true-positive** before its first gated use (prove it bites from a measured over-cap attempt).
- **condim/roll-out inert-until-rolling-rows:** friction knobs (impratio/solref/noslip) inert until rolling contact rows exist → `LL-Condim-Rolling-Mechanism.md` (+ `task_config.py:170-172`).
- **pure-mujoco ≠ newton structurally:** a cross-solver replay (newton → vanilla mujoco) is NOT param-matchable when the divergence is structural (inertia + contact resolution) → `F1_REV10_SEC28_RECONCILE.md:21,37`.
- **Sudden NaN after stable tracking = the substrate wall, not a control bug:** a featureless-cable drag that tracks then suddenly NaNs is the substrate failing to *simulate* the regime, not an IK/control divergence → distinguish from the Step-1 explosion-pattern path.

Add a discriminator line to the Newton-vs-PhysX table (`:186-194`): a Newton NaN at the **end of stable tracking** (not seg_0-first, not tension-accumulation) routes to **3f**, not 3b/3d.

**Where it lands.** `.claude/skills/physics-diagnosis/SKILL.md`: a new **Step 3f** after `:126`; a discriminator row in the Newton/PhysX table (`:186-194`); an 出典 addition pointing to the five LL docs (`:217-225`). The facts stay in the LL docs; the skill only **indexes** them. **[PENDING-human, L3]**

**Rationale.** `physics-diagnosis`'s absolute principle is "「速度が速すぎる」は根本原因ではない" (`:17-21`) — reject the easy attribution, find the structural cause. The substrate-fidelity branch is the same discipline one layer out: a NaN/slip on Newton is easy to mis-attribute to "IK divergence" or "force spike" when the real cause is a known substrate limitation. Indexing (not copying) the LL docs keeps the SSOT single and the skill light.

**Session evidence.**
- #3328 never-sticks signature: `log.md:6318` ("zero decel = never-sticks #3328 signature; rate class = S5 measured 128.7um/f"); the cleanest #3328 datum (`log.md:6317`).
- xfrc-inert true-positive requirement: the rev10 clamp-bite gate (`F1_REV10_SEC28_RECONCILE.md:3-7`: "WITHOUT clamp … 5.158 N·m → WITH clamp … capped EXACTLY 2.5 … bite_proven … the clamp is not inert"); the LL doc head (`LL-Xfrc-Inert-Actuation-TruePositive.md:1`).
- structural non-param-matchability: `F1_REV10_SEC28_RECONCILE.md:21,37` ("cross-solver replay (newton → vanilla mujoco) is NOT param-matchable when the divergence is structural").
- sudden-NaN-as-substrate-wall: REVS1 (`log.md:6350`: "drag NaNs the cable (f646, ~40mm short of clip, #3328 wall REALIZED)"; `log.md:6351`: "NaN = sim couldn't simulate the drag, not a clean 'drag fails'").

---

### 2.6 — `rule-check` — **consistency check (likely NO change)**

**Finding (verified).** `rule-check` Stage 1 **already** auto-promotes skill-workflow edits to L3. Step 1 lists `.claude/skills/*/SKILL.md` の workflow/protocol 部分 as an L3 path pattern (`rule-check/SKILL.md:101`), and Step 4 (`:142-154`) resolves the variant: workflow/protocol → **L3 fixed**; description-with-new-trigger → workflow → **L3**; example-with-judgment-logic → **L3**; only docs/comment/typo/test → L0-L1. So **the very improvements in §2.1-2.5 of this program are correctly L3-gated by the existing skill** — which is exactly the §0 self-classification this program already states.

**The change: NONE to `rule-check` itself.** This section is a **consistency confirmation**, not an edit. It verifies that the program's claim ("all skill landings are L3, human-gated") is *produced* by `rule-check` Stage 1 as written, closing the loop. The only optional, separate item is the long-standing Day-5+ candidate "rule-check Stage 1 grep automation (shell-script the path/keyword match)" (CLAUDE.md §0 運用履歴) — **out of scope here**, listed only so it is not lost.

**Where it lands.** Nothing. **[NO CHANGE — consistency check only.]**

**Rationale / evidence.** Landing skill workflow edits without an L3 gate is precisely what `rule-check` exists to prevent (`rule-check/SKILL.md:24-32`). The session already exercised this correctly: `%18` ruled the 5CC-design change L3 because it "touches verification-subagent SKILL.md + challenger-prompt.md + CLAUDE.md §運用2/§運用15" (`log.md:6332`). That ruling is the §2.3 landing's gate — and it came from the existing rule-check logic, confirming no `rule-check` change is needed.

---

## §3. What is deliberately NOT changed (anti-accretion / preserve-rigor)

- **No new skill, gate, Phase, file, or CLI arg.** Per the CLAUDE.md hard-stop (タスク指示外の新ファイル/Gate/CLI禁止) and GROVE rule 4. Every §2 item is an **addition to an existing skill** (a Step, a self-check line, an index branch, a parameter, an anti-pattern row). The single new artifact is THIS draft doc.
- **The video-first / NaN-truncation CONTENT is not re-authored** — it is the sibling video draft's (`VIDEO_ANALYSIS_SKILL_IMPROVEMENT_2026-06-13.md` §2-§3). §2.2 here only adds the `verify-run` verdict-machinery framing + the interlock.
- **The lens SEEDS and the cap NUMBER are not written into `verification-subagent/SKILL.md`** — the skill points to `%18`'s `percent18_lensed_v1.md` SSOT; the cap (3/5/7) is human-pending + `%14`-A/B-bound; the lensed>generic quality claim is confound-blocked.
- **The substrate FACTS are not copied into `physics-diagnosis`** — they stay in the existing `LL-*` Knowledge docs; the skill only indexes them (avoids a second SSOT).
- **`verification-subagent`'s correct invariants are untouched:** the PROPOSE-no-confidence rule (`:174-175`), the independence guarantees (`:111-118`), the mandatory NO_ACTION_EVALUATION (`:275-289`), the two-script logging pipeline (`:306-359`). The lensing replaces *identical bodies*, not the debate structure.
- **`rule-check` gets no edit** (§2.6) — it already does the job.

---

## §4. PENDING-human (L3 landings) + ownership/blocking summary

Per CLAUDE.md §0 (skill-workflow edits = L3, human-initiated). **Nothing below is landed by this agent.**

| Item | Skill / target | L | Blocked on |
|---|---|---|---|
| **SRG branch** (§2.1) | `pre-check/SKILL.md` (verifier framework + self-check + result-route) | L3 | human L3-landing |
| **verdict-machinery / NaN-void framing** (§2.2a/b) | `verify-run/SKILL.md` 照合 + report; CONTENT = video draft A1/B1 | L3 | human L3-landing; co-lands with the video draft |
| **Lensed structure + panel-size parameter + conservatism/premise discipline** (§2.3) | `verification-subagent/SKILL.md`; SSOT = `percent18_lensed_v1.md` | L3 | **human cap decision (3/5/7) FIRST** + `%14` same-subject vary-only-N A/B + matched-tools v3 (lensed>generic confound). Land the *mechanism* only; do NOT hard-code N or claim N-ordering/persona-superiority |
| **Step 0 bounded pre-step + axis-resolved retention + μ0 falsifier** (§2.4) | `geometric-design/SKILL.md` Step 0/5c + anti-patterns | L3 | human L3-landing |
| **Substrate-fidelity index branch 3f** (§2.5) | `physics-diagnosis/SKILL.md` Step 3f + index to existing `LL-*` | L3 | human L3-landing |
| **Consistency check** (§2.6) | `rule-check` — **NO CHANGE** | — | n/a |

**Process note (consistent with the methodology):** this is the *drafting* leg. The mutual-catch chain requires this draft be **independently reconciled (`%12`)** and **PV'd (`%18`)** — reviewer ≠ drafter — and the L3 items require the **human gate** before any of it becomes a skill edit. The drafter does not self-approve.

---

## §5. Cover summary — ranked by outcome-impact

The ranking weights (i) how directly the item answers a verified loss THIS session, and (ii) whether the skill currently *bypasses* the lesson (axis B) vs merely *lacks content* (axis A). Bypass-fixes and false-verdict-fixes rank highest.

1. **§2.1 SRG branch in `pre-check`** — **highest outcome-impact.** It is the cheapest possible cap on the most expensive failure pattern this session: a fidelity-bound run on a too-lossy proxy that produces a guaranteed non-answer and invites the accretion spiral. Verified to have capped the noslip detour at 1 rev instead of 3, and to have predicted REVS1's #6 (`STRATEGY_7CC_DECIDE.md:19`; `log.md:6352`). One 30-second pre-flight question; no new gate. **[L3]**

2. **§2.3 lensed + parameterized `verification-subagent`** — **highest structural leverage.** The debate skill was *bypassed* this session (7CC ran custom, `log.md:6355`); parameterizing N + lens-set makes the formal skill able to host both code-review and strategy debates, and the lensed structure is the mechanism that makes a smaller N viable (cost-relevant given the cap contradiction). Must land mechanism-only (cap human-pending, lensed>generic confound-blocked). **[L3]**

3. **§2.2 `verify-run` verdict-machinery + the video draft's NaN-truncation** — **directly fixes the #6 false verdict.** A post-NaN metric is *void*, not merely lower-priority; `verify-run` is where that disposition belongs. Pairs with the sibling video draft (which owns the bulk content). **[L3]**

4. **§2.4 `geometric-design` Step 0 + axis-resolved retention** — **prevents over-building the wrong mechanism.** R-0 shrank 爪 to retention-only and the B1 CRITICAL caught the category error that would have shipped a false in-sim PASS. Highest-value content addition (a genuinely missing pre-step + a genuinely missing validation axis). **[L3]**

5. **§2.5 `physics-diagnosis` 3f index branch** — **lowest effort, real value, zero duplication.** Indexes the substrate-fidelity LL docs the session generated so a future Newton NaN/slip routes to "substrate wall?" instead of mis-attributing to a control bug. Pointer-only (facts stay in the LL docs). **[L3]**

6. **§2.6 `rule-check` consistency check** — **NO change.** Confirms the existing Stage-1 logic already L3-gates every item above, closing the program's self-classification loop. **[no edit]**

All §2.1-§2.5 items are **PENDING-human (L3)**; §2.6 is a confirmation. Nothing lands without the human's L3 decision + the `%12`/`%18` mutual-catch. This doc is the PROPOSE only.

---

## §6. Verification status of this artifact

- **Mutual-catch chain (the project's standing mutual-catch):** drafter = this agent; reconcile = `%12` (on-disk: confirm every `file:line` resolves); PV = `%18` (independent). NOT self-approved.
- **Citations re-verified against current disk this drafting pass (2026-06-13 ~22:18 JST):** all six `SKILL.md` line refs; `challenger-prompt.md:48-66`; `percent18_lensed_v1.md:5,55,60,124,126-129,133`; `create_clip.py:37-46`; `task_config.py:92,94,170-172,280`; `log.md:6310-6355`; `R0_SEC28_RECONCILE.md`, `F1_REV10_SEC28_RECONCILE.md`, `STRATEGY_7CC_DECIDE.md`; the existence of the five `LL-*` substrate docs; the untracked (`??`) status of the GROVE/video/this `docs/` family.
- **Known limit:** memory files and prior reconcile docs are point-in-time; a reconcile pass should re-confirm the `SKILL.md` line numbers before any landing (skills can shift). The two sibling drafts (`GROVE_V1.1_…`, `VIDEO_ANALYSIS_…`) are themselves DRAFT/untracked and PV-pending; this program references their *content*, which is also pre-landing.
- **No governing files were modified.** Version-control the `docs/` family (§0) before any landing.

*End of program. This doc is the drafting leg only; all skill edits are PENDING-human (L3).*
