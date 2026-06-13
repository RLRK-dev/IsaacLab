# Video-Analysis Skill Improvement Proposal (2026-06-13)

**Status:** DRAFT — forward-only, non-governing. Track 3 of the 2026-06-13 autonomous window.
**Author:** verification-tooling draft agent (executor). Drafter ≠ reviewer: this doc requires an independent PV (%18) + on-disk reconcile (%12) before any landing.
**Trigger:** human-Rs challenge, `log.md:6330` (2026-06-13 22:07): 「動画解析を行って判断しているのか／動画解析skillは向上させなくてよいのか」.
**Scope of THIS doc:** propose changes only. It edits NO governing file. Every item that lands in a skill, CLAUDE.md, or a GROVE rule is flagged **PENDING-human (L3)** — see §0.

---

## §0. Version-control & forward-only note (read first)

- This is a **NEW doc** at `docs/VIDEO_ANALYSIS_SKILL_IMPROVEMENT_2026-06-13.md`. It does not overwrite any prior artifact (FAIL/decision records are forward-only; GROVE rule 7).
- `docs/` GROVE-family docs are currently **untracked** in git (verified: `git status` shows `docs/GROVE_CORE_SPEC.md` etc. as `??`). If this doc is to be a durable record, `git add` it first; do not rely on an untracked working-tree file as SSOT.
- **No governing file is touched by this draft.** Landing any §2/§3 item into the following is an **L3 change, human-gated**, per CLAUDE.md §0 auto-promotion keywords (path match):
  - `.claude/skills/video-analyzer/SKILL.md`, `.claude/skills/verify-run/SKILL.md`, `.claude/skills/log-analyzer/SKILL.md` (skill workflow/protocol).
  - `.claude/agents/video-analyst.md`, `video-analyst-generic.md` (verification agent definitions).
  - `CLAUDE.md` "テスト検証プロトコル" (lines 371-384), §運用9 (267), §運用14 (268), §運用15 (269-).
  - `docs/GROVE_CORE_SPEC.md` rule 1 / rule 2 (rule-file change = human-initiated, GROVE C3).
- The L3 verification chain for THIS artifact itself: drafter(agent) → reconcile(%12 §28) → PV(%18) → human L3-landing decision. This doc is the PROPOSE; it is not self-approving.

---

## §1. The gap, stated precisely (what's actually wrong)

The skills are **present and rigorous**; the failure is **bypass + inconsistency**, not missing capability. Distinguishing the two axes is the whole point — fixing the wrong axis (adding more skill content) would repeat the S4/S5 miss where ever-deeper numeric rigor masked an absent modality.

| Axis | Status (verified on disk) | Evidence |
|---|---|---|
| **A. Skill content/rigor** | Largely GOOD. `/video-analyzer` has 5-frame split + Step 4b vibration pass + comp_checks ground-truth penetration. `video-analyst` agent has 6-camera mega-grid + zero-exposure + decision trees. `/verify-run` enforces parallel-fork structural blindness. | `video-analyzer/SKILL.md:196-211` (vibration), `:18-19` (comp_checks gate); `agents/video-analyst.md:166-202` (decision trees); `verify-run/SKILL.md:25-31` (blindness). |
| **B. Application discipline (THE gap)** | BROKEN. The skill EXISTS but was BYPASSED for numeric shortcuts across this session and S4/S5. | `log.md:6330` (22:07): "visual verification was PRESENT at sim gates (rev6/7/9/10 manual frame Reads, 運用14) but **UNDER-RIGOROUS (manual single-frame, NOT the /video-analyzer skill) + INCONSISTENT (REVS1 leaned npz + %18 frames, no own-video)** = the known S4/S5 video-first gap recurring." |

**This is a recurrence, not a first occurrence.** The same modality gap is recorded at `feedback_video_first_verification_gap_s4s5_2026-06-10`: "the CLAUDE.md video→log→照合 order was never applied … MY PV layer never flagged it." Two independent sessions, same hole ⇒ the fix must be **structural enforcement**, not another reminder. A rule that already exists (CLAUDE.md:374 「検証順序（厳守）: 動画 → ログ → 照合」) and is still skipped twice is, by GROVE's own logic (rule 10 / runaway-bounds), evidence that the mechanism — not the operator — needs to change.

**Why the bypass is rational-looking and therefore dangerous:** at each sim gate the lead HAD frames (manual Reads) and a numeric verdict, so the gate *felt* covered. The discriminator that was missing: "is the PRIMARY modality present **via the actual skill path**, or did I substitute a cheaper proxy?" That discriminator is currently a thing the lead must *remember*; nothing *blocks* on its absence.

---

## §2. Improvements — SKILL CONTENT / RIGOR (Axis A)

Each item: the change · where it lands · rationale · session evidence · L-flag. Content items are **secondary** to §3 (enforcement); they are real but smaller.

### A1. Junk-frame / NaN-tail robustness guard for video-derived metrics — **NEW, highest content priority**
- **Change:** Add to `/video-analyzer` Step 1 (after metadata) and to `log-analyzer` a **frame-validity / metric-regime guard**: before any per-frame metric (slip, F-drag, displacement, area) is aggregated, detect the **NaN/divergence frame index** and **truncate the metric window at the last physically-valid frame**. Any metric computed across or after a NaN/teleport frame is an **artifact → void it explicitly** (do not average through it). Emit `metric_valid_until_frame=N` in the verdict.
- **Where it lands:** `.claude/skills/video-analyzer/SKILL.md` (new Step 1.5), `.claude/skills/log-analyzer/SKILL.md` (RUN_METRICS regime field). **[PENDING-human, L3]**
- **Rationale:** GROVE rule 6 (regime-conditioned metrics): a metric outside its valid regime is an artifact; reading it is a gate error. Post-divergence frames are out-of-regime by construction.
- **Session evidence:** REVS1 cost **count #6** — `log.md:6330` (21:43, %18 FINAL ruling): "the F-metric pollution **PRODUCED A FALSE VERDICT** at a gated launch = verdict-machinery = rev8-class". The F-metric averaged through the post-NaN junk void (NaN at f646, ~40mm short); the correct read was the **hand-verified npz trajectory** (stable f632-643 → f644 −45mm jump → f646 NaN, `log.md` 21:36). The metric was caught + retracted, but only after it had issued a verdict. A frame-validity truncation guard would have voided it *before* aggregation.
- **Robustness pairing:** ties to `feedback_verify_metric_proves_property_not_just_reconciles_2026-06-10` (identical-across-conditions value = artifact red flag) — a NaN-tail-polluted metric is the same failure class one layer down.

### A2. Standing PV-checklist line: "is the visual modality present, or its omission justified+stated?"
- **Change:** Add a **mandatory line** to the self-check block of `video-analyst.md` (the agent self-check, `:606-616`) AND to the `/verify-run` final report: *"Does this gate's evidence include the PRIMARY (visual) modality produced via the skill path? If not, is the omission explicitly justified and stated? (manual single-frame Reads do NOT satisfy this.)"* — verdict cannot be emitted with this line blank.
- **Where it lands:** `agents/video-analyst.md` self-check; `verify-run/SKILL.md` Step 3 report template. **[PENDING-human, L3]**
- **Rationale:** This is the checklist line the S4/S5 lesson already prescribed but which was never institutionalized into the tool: `feedback_video_first_verification_gap_s4s5_2026-06-10` "How to apply (2): My PV checklist gains a standing line: 'does this gate's evidence include the visual modality, and if not, is the omission justified+stated?'". It is currently a memory note, not a tool gate ⇒ it depends on the lead recalling it. Moving it into the skill makes omission **loud**.
- **Session evidence:** `log.md:6330` 22:07 — the omission ("no own-video" at REVS1) went unflagged by the lead's own PV until the human challenged.

### A3. Cheap-render-from-logged-state guidance (make the video leg cheap, removing the bypass incentive)
- **Change:** Add to `/video-analyzer` Step 0/1 a **render-acquisition fallback ladder** when no MP4 exists: (1) deterministic CPU re-run + `ViewerGL` attach (the committed recorder, `test_newton_clip_routing.py:228-260`, `:42 from newton.viewer import ViewerGL`); (2) `matplotlib body_q` animation from logged state as the **zero-GPU** fallback; (3) only if neither is reachable, declare `INCONCLUSIVE_visual` with the omission stated. Note the **headless-GL/EGL caveat**: if ViewerGL needs GPU/EGL that is *visualization, not sim-compute* — surface as a minimal-GPU exception to a 0-GPU posture, never silently consume GPU.
- **Where it lands:** `.claude/skills/video-analyzer/SKILL.md` Step 1 (format branch currently dead-ends at "動画なし → INCONCLUSIVE", `:69`). **[PENDING-human, L3]**
- **Rationale:** GROVE rule 1: "Cheap rendering from logged state suffices." The reason the video leg got skipped is partly that, for the F1 probe chain, **no MP4 was being produced** — the probes ran headless-numeric and the existing recorder was never invoked. If the skill *tells the operator how to cheaply obtain frames from the logged state*, the "there was no video to look at" excuse disappears.
- **Session evidence:** `feedback_video_first_verification_gap_s4s5_2026-06-10` (infra fact): "test_newton_clip_routing.py:231-260 already contains a committed ViewerGL headless per-camera MP4 recorder … the probes simply never invoked it. Deterministic CPU re-runs + viewer attach ⇒ retroactive renders of the certified runs are possible." Verified still present at `test_newton_clip_routing.py:42,228-260`.

### A4. Motion-phase auto-detection → "this gate REQUIRES a video leg" classifier
- **Change:** Add a small **motion-detector** to `/verify-run` Step 0: parse the run for task-relevant motion phases (settle / grasp / close / lift / route / drag). If any motion phase is present, set `VIDEO_LEG_REQUIRED=true` in the run's `.verify/` and refuse to emit a final PASS without a `visual_verdict.md` (or an explicit, recorded omission justification). Static/no-motion runs (e.g. a pure config-readback) may set it false with a one-line reason.
- **Where it lands:** `verify-run/SKILL.md` Step 0 + Step 2 judgment rule (currently "動画なし + 数値のみ → INCONCLUSIVE" is advisory only, `:138`). **[PENDING-human, L3]**
- **Rationale:** Converts "lead decides whether video matters" into "the run's own content decides, mechanically". This is the §3 enforcement hook in skill form (see §3.2). Motion → primary modality is mandatory is exactly GROVE rule 1's domain ("for anything with behavior, LOOK before reading numbers").
- **Session evidence:** Every F1 leg (rev6-10) and REVS1 was **motion-bearing** (close/drive-through/drag) yet none ran the skill — `log.md:6330` 22:07. A motion-detector would have set `VIDEO_LEG_REQUIRED=true` on all of them.

### A5. (Lower) Zero-exposure independent-judge (Code C) wiring is already specified — make it the DEFAULT for sim results, not optional
- **Change:** In `/verify-run` Step 1c the `video-analyst` zero-exposure agent is currently **optional** ("optional だがTHREAD sim結果には推奨", `:68`). Promote it to **default-on for any THREAD dual-arm sim result**, optional-off only with a stated reason.
- **Where it lands:** `verify-run/SKILL.md` Step 1c trigger conditions (`:75-81`). **[PENDING-human, L3]**
- **Rationale:** The independent-judge path is the GROVE blind-judge role (C2) and the only path that can issue a *formal* validity verdict (rule 1: "formal validity verdicts belong to the blind judge"). Leaving it optional is why this session's PVs were the lead's own frames, not a zero-exposure verdict.
- **Session evidence:** `log.md:6330` 22:07 "REVS1 leaned npz + %18 frames, no own-video" — %18's frames are a peer PV, not the structurally-blind Code-C path.
- **Caveat (verified):** Code-C independence is already well-specified (`verify-run/SKILL.md:82-90`, `feedback_verification_video.md §8`). This is a default-flip, not new machinery — low risk, low effort.

**Content-axis summary:** A1 (junk-frame guard) is the one genuinely *missing* capability and is highest. A2/A4 are the seams where content meets enforcement. A3/A5 lower the cost/friction so §3's mandate is cheap to satisfy.

---

## §3. Improvements — APPLICATION DISCIPLINE / ENFORCEMENT (Axis B — THE real gap)

The skills are bypassable because **nothing blocks on the absence of the video leg**. The order is mandated in prose (CLAUDE.md:374 「厳守」) but enforced by memory. Two sessions skipped it. The fix is to make the video leg **structurally non-skippable for motion-bearing sim results**, tied to GROVE rule 1.

### B1. Forcing gate: "motion-bearing sim result ⇒ video leg MANDATORY or omission explicitly justified" — **the core enforcement change**
- **Change:** Add a **verification-chain gate** at the RESULT/post-verify boundary (CLAUDE.md §運用15, line 269-, "結果報告前の事後独立検証"): *a sim/probe RESULT that contains task-relevant motion may NOT be reported with a verdict unless its evidence set includes a visual-modality leg produced via the skill path (`/verify-run` or `/video-analyzer` + `video-analyst`), OR the report carries an explicit, recorded justification for the omission.* The existing §運用15 execution order (line 271) already ends with "テスト検証プロトコル（動画→ログ→照合）" — this change makes that final step **conditionally mandatory and loud-on-omission** rather than a tail item that silently got skipped.
- **Where it lands:** `CLAUDE.md` §運用15 (line 271 execution-order) + a one-line addition to the "テスト検証プロトコル" block (line 371-377) stating the omission-justification requirement. **[PENDING-human, L3]**
- **Rationale:** This is the mechanism that makes the order **enforced rather than remembered**. It mirrors how other §運用 gates already work (e.g. §運用15 層3 機械的検証 is "全変更対象" / mandatory). The video leg should be the same class of mandatory for motion results.
- **Session evidence:** the recurrence itself — `log.md:6330` 22:07 + `feedback_video_first_verification_gap_s4s5_2026-06-10`. Prose-「厳守」 was insufficient twice.
- **Discriminator (kept narrow to avoid over-blocking):** the gate fires on **RESULT/verdict points for motion-bearing sim runs**, NOT on internal probe iterations, NOT on pure-numeric config readbacks, NOT on non-sim analysis. This matches GROVE rule 1's own scope ("at gate/binding runs and verdict points (not internal iterations)").

### B2. Operationalize via §A4's `VIDEO_LEG_REQUIRED` flag (machine-decided, not lead-decided)
- **Change:** Bind B1 to the §A4 motion-detector output. The `/verify-run` orchestrator writes `VIDEO_LEG_REQUIRED={true|false, reason}` to `.verify/`; the post-verify step (§運用15) reads it and blocks a PASS verdict when `true` and `visual_verdict.md` is absent. This removes lead discretion from the trigger — the **run's content** decides whether the video leg is owed.
- **Where it lands:** `verify-run/SKILL.md` Step 0/2 (flag write + block rule) — the skill-side half of B1. **[PENDING-human, L3]**
- **Rationale:** GROVE C3 "gate-edit discriminator": executors don't edit gates mid-run; making the trigger mechanical (motion-detected) prevents the lead from quietly deciding "this one doesn't need video". The lead can still record an omission justification, but it is **explicit and auditable**, not silent.
- **Session evidence:** the bypass was a silent discretionary skip (manual frames felt like enough) — `log.md:6330` 22:07 "UNDER-RIGOROUS … INCONSISTENT".

### B3. Tie to GROVE rule 1 (primary-modality-first) — promote from under-enforced principle to a gated invariant; add the bypass-detector as rule 1's true-positive
- **Change:** GROVE rule 1 (`GROVE_CORE_SPEC.md:33`) is CORE but **carries no enforcement hook** — it states the discipline, nothing gates on its violation. Add to rule 1 (or its binding ⑤ "primary verification modality") the operational clause: *"At verdict points for behavior-bearing results, the primary-modality leg is MANDATORY-or-justified; its absence is a gate failure surfaced loudly, not a silent omission. Manual single-frame inspection ≠ the skill-path primary-modality leg."* Cross-reference rule 2 (zero-claims-need-a-true-positive): treat the **bypass-detector** (§A4 motion-flag) as rule 1's own true-positive instrument — it must demonstrably fire on a known motion run before it is trusted to pass a no-motion run.
- **Where it lands:** `docs/GROVE_CORE_SPEC.md` rule 1 text + binding ⑤; rule-file change is human-initiated (GROVE C3). **[PENDING-human, L3]** Also feeds the in-flight `docs/GROVE_V1.1_IMPROVEMENT_PROPOSAL_2026-06-13.md` (Track 2) — this session is rule 1's **second-binding confirmation** that the principle alone is insufficient without an enforcement hook.
- **Rationale:** The portable GROVE methodology is the right home for the *principle*; CLAUDE.md §運用15 (B1) is the right home for the *THREAD-specific gate*. Landing in both keeps the two-container discipline (GROVE C1 pillar 6 / two-container knowledge capture) without drift: GROVE = portable invariant, CLAUDE.md = the binding's instantiation.
- **Session evidence:** rule 1 existed (`GROVE_CORE_SPEC.md:33`) during this entire session and the video leg was still skipped ⇒ a CORE rule with no gate hook is exactly the failure GROVE rule 1 warns about for *metrics*; apply the same medicine to the rule itself.
- **Honesty flag (verified):** the GROVE v1.1 draft already downgraded an over-claim this session (`log.md:6330` 21:29 "lensed>undifferentiated CONFOUNDED by tool-access"). Keep the same standard here: do NOT claim "this gate will eliminate the gap"; claim "it converts a silent skip into a loud, recorded omission" — which is the verifiable property.

### B4. Make omission auditable in the post-verify trajectory (supervisor catch)
- **Change:** When a motion-bearing RESULT is reported with the video leg omitted-and-justified, the justification string is recorded in the `.verify/` verdict so the **per-milestone trajectory audit** (GROVE C3, supervisor duty) can count omissions. A rising omission rate is a counter-metric signaling the gate is being routed-around.
- **Where it lands:** `verify-run/SKILL.md` report template + supervisor's milestone audit checklist (memory/process, not a governing-file edit if kept in the supervisor's own notes; if it lands in CLAUDE.md §運用15 it is **[PENDING-human, L3]**).
- **Rationale:** GROVE "Observation (never targets)": read gate-pass PAIRED with counter-metrics; omission-rate is the counter-metric for the video gate. Prevents the gate from being satisfied by ever-more "justified omissions".
- **Session evidence:** the gap was caught by the **human**, not the lead's PV or the supervisor (`log.md:6330` 22:07). The catch must move upstream; an auditable omission count is the upstream signal.

**Enforcement-axis summary:** B1 is the load-bearing change (mandatory-or-justified gate). B2 makes its trigger mechanical (no lead discretion). B3 roots it in the portable methodology + gives it a true-positive. B4 keeps it honest over time (counter-metric).

---

## §4. What is deliberately NOT changed (anti-accretion / preserve-rigor)

- **The structural blindness of `/verify-run` (parallel fork)** — already correct (`verify-run/SKILL.md:25-31`); do not touch.
- **Code-C independence spec** — already correct (`:82-90`); only the default-on flip (A5), no new machinery.
- **The 5-frame + Step 4b vibration sampling** — adequate; A1 (NaN-tail truncation) is orthogonal, not a replacement.
- **No new gate, Phase, file, or CLI arg beyond the above.** Per CLAUDE.md hard-stop (タスク指示外の新ファイル/Gate/CLI禁止) and GROVE rule 4 (experience-feedback first, no spec accretion): this proposal is **refinements to existing skills + one conditional gate**, not a new verification subsystem. The single new artifact is THIS draft doc.
- **Do not add per-frame `wp.printf` or pixel-coordinate analysis** — both already prohibited (`agents/video-analyst.md:143`, AGENTS.md Warp-debug); A-items stay LLM-visual + ffmpeg only.

---

## §5. Ranked top-5 (for the cover summary)

1. **B1 — forcing gate (motion sim result ⇒ video leg mandatory-or-justified).** The fix for the actual recurring gap. CLAUDE.md §運用15. **[L3]**
2. **A1 — junk-frame/NaN-tail metric-truncation guard.** The one genuinely missing capability; directly answers the #6 false-verdict cost. video-analyzer + log-analyzer. **[L3]**
3. **B3 — root B1 in GROVE rule 1 + add its true-positive (bypass-detector).** Promotes an under-enforced CORE principle to a gated invariant; feeds GROVE v1.1. **[L3]**
4. **B2/A4 — mechanical `VIDEO_LEG_REQUIRED` motion-detector.** Removes lead discretion from the trigger; operationalizes B1. verify-run. **[L3]**
5. **A2 — standing PV-checklist "is the visual modality present-or-justified?" line + A3 cheap-render ladder.** Makes omission loud and the leg cheap to satisfy. agent self-check + video-analyzer. **[L3]**

All five are **PENDING-human (L3)**. Nothing in this draft lands without the human's L3 decision; this doc is the PROPOSE only.

---

## §6. Verification status of this artifact

- **Mutual-catch chain (GROVE rule 8 / mutual-catch):** drafter = this agent; reconcile = %12 §28 (on-disk: confirm every file:line citation resolves); PV = %18 (independent). NOT self-approved.
- **Citations to verify on reconcile:** `log.md:6330` (the 22:07 / 21:43 / 21:36 / 21:29 entries), `video-analyzer/SKILL.md` line refs, `verify-run/SKILL.md` line refs, `agents/video-analyst.md` line refs, `GROVE_CORE_SPEC.md:33`, `CLAUDE.md:267-271,371-384`, `test_newton_clip_routing.py:42,228-260`, `feedback_video_first_verification_gap_s4s5_2026-06-10`.
- **Known limit:** the memory files cited are point-in-time; file:line claims about skills/code were re-verified against current disk in this drafting pass (2026-06-13), but a reconcile pass should re-confirm before any landing.
