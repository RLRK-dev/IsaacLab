# Two-stage best-of-N → debate pipeline, with a REVIVAL channel (design v1)

**Author:** %14 | **2026-06-14 02:12 JST** | **For:** %18 (5CC design SSOT owner, L3 edit under human-GO) + the FREEZE-06-22 policy.
**Source:** human-Rs proposal (2026-06-13/14): 2段構え — Stage 1 = same prompt → multiple CCs → pick the answer closest to truth (hallucination elimination); Stage 2 = scrutinize the selected answer from multiple viewpoints; **REQUIREMENT: a mechanism so a truly-near-truth answer discarded in Stage 1 can be REVIVED.**

## 0. Why this is exactly right (grounding, not flattery)
The proposal unifies the two regimes I characterized empirically and supplies the missing bridge:
- **Stage 1 = the GENERATIVE regime** (Trial-B, `bestofn_trial/RESULT.md`): same prompt → divergent answers → select/merge. Reduces *idiosyncratic hallucination* (an error only one body makes).
- **Stage 2 = the ADVERSARIAL regime** (runs 01-04, `run04_toolmatched_v3.md`): multi-viewpoint challengers attack one answer. Reduces *shared blind spots* (errors all bodies make, caught by a lens/mandate).
- **The revival requirement names a real defect I had already flagged** — RESULT.md point 25: *"SELECT-best would drop catches."* A lossy Stage-1 selector can throw away a TRUE minority answer. The human independently re-derived this and asks for the fix. The fix is the **dissent ledger + Stage-2 evidence-based revival** below.

## 1. The pipeline
### Stage 1 — generate + reconcile (variance / hallucination ↓)
1. Same prompt → **N bodies** (Opus 4.8, R5).
2. Aggregate by **MERGE, not pure SELECT** (Trial-B #3: MERGE strictly dominated all single bodies; pure SELECT can only return one body and drops the others' complementary truth).
3. Emit two artifacts:
   - **(a) merged answer** — the consensus + union of complementary correct pieces.
   - **(b) DISSENT LEDGER** — every claim where bodies DISAGREED, recorded as `{claim, which-body asserted it, cited evidence, objectively-checkable?}`. **Nothing is discarded here.**
4. Resolve at Stage 1 ONLY the disagreements that are **objectively checkable now** (disk recompute / open-the-citation — run04's biggest levers). Everything else stays in the ledger for Stage 2. This keeps Stage 1's selector from making an *irreversible* call it isn't equipped to make.

### Stage 2 — adversarial scrutiny + revival adjudication (blind spots ↓, revival)
Input: **merged answer + dissent ledger.** Challengers (mandate-carrying, disk-enabled — the run04 levers) do TWO jobs:
1. **Attack the merged answer** (standard 5CC — find NEW defects it shares).
2. **Adjudicate the dissent ledger:** for each contested/minority claim, verify against disk / ground-truth → **REVIVE** (claim was true; overturn Stage-1's drop) or **CONFIRM-DISCARD** (claim was a hallucination).
3. **UNION** valid catches (adversarial regime never select-one).
The arbiter is **disk / recompute, not a vote** → revival is evidence-based.

## 2. The revival mechanism = the answer to 「捨てられないで復活させる機能」
A minority claim at Stage 1 is **ambiguous**: it is either (a) a hallucination (one body, wrong) or (b) the one body that saw the truth (one body, RIGHT). Stage 1 **cannot tell these apart** — so any lossy selector risks discarding (b).
**Fix: defer the discard decision.** The dissent ledger *preserves* every minority claim with its provenance; Stage 2's disk-verification *resolves* it. Revival = "deferred, evidence-gated discard" instead of "eager, selector-gated discard." It is evidence-gated in BOTH directions: true minorities are revived, false minorities are confirmed-discarded (precision is part of the mechanism, not just recall).

## 3. Worked example (already in hand — run04, zero new cost)
v3 defect **N1** (numerical): the artifact claims `2·GRIP_HALF_SPAN = 2·0.060 = 0.100 m`. Disk: `task_config.py:228 GRIP_HALF_SPAN=0.060 # arm-to-arm span = 120mm` → real value **0.120**.
- Stage-1 reality (run04): generic bodies caught N1 only **1/2** (gen#1 skimmed CC1's 0.100; gen#2 recomputed 0.120). **N1 is a true minority.** A naive Stage-1 select of gen#1's answer **discards N1.**
- Revival: the dissent ledger logs gen#2's "2·0.060=0.120≠0.100"; Stage-2's recompute-mandate + disk (`:228` "120mm") **revives** it reliably (1/1). The true minority is recovered.

## 4. Cost (低コスト goal)
- Dissent ledger = **~free** (it is *not-throwing-away* + provenance logging).
- Stage-2 adjudication adds marginal cost **only on the contested claims**, not a full re-debate.
- **No bigger panel needed** (run04: completeness comes from disk/mandate levers, not headcount). Stage 1's N is a *variance dial*; the revival channel is what makes a SMALL N safe (a true minority caught by 1 body is no longer lost). → completeness↑ AND cost↓, consistent with the whole 5CC finding.

## 5. Refinement offered to the human's wording
The human said Stage 1 "選ぶ" (select). Trial-B evidence says **MERGE > SELECT**, and pure SELECT is the very thing that drops truth. Recommendation: Stage 1 = **MERGE + dissent-ledger**, not argmax-select. This *strengthens* the human's design — it removes the discard at its source AND keeps the deferred-revival backstop for whatever merge still can't reconcile. (Two layers of anti-discard: merge preserves complementary truth; ledger+Stage-2 preserves contested truth.)

## 6. Validation
- **Retrospective (run04, §3):** the N1 case already demonstrates the mechanism for free.
- **Prospective (this turn):** a single disk-enabled Opus adjudicator is given a deliberately-BAD Stage-1 selection (N1 dropped) + a dissent ledger containing one TRUE minority (N1) and one FALSE minority (a decoy: "TABLE_HEIGHT:20 should be 0.75" — disk says 0.80, accurate). Pass = REVIVE N1 + CONFIRM-DISCARD the decoy, by disk evidence, blind to the ground-truth file. Result appended below.

## 7. Disposition
Hand to %18 as design input to the 5CC SSOT (author≠reviewer: %18 PVs). Folds onto the run01-04 levers (shared-floor mandates + disk + bundle + memory-step). The two-stage wrapper + revival channel is a *pipeline* around the existing debate, not a replacement. Panel N stays **human-pending (3/5/7)** — and the revival channel makes a SMALL N defensible. Implementation = L3, human-GO gated.

## 8. Validation result (prospective, 2026-06-14 02:13 JST — PASS)
One disk-enabled Opus adjudicator, blind to the ground-truth file, 64,286 tok / 30.6 s / 5 tool-uses. Given the deliberately-bad Stage-1 selection (N1 dropped, stamped "NO DEFECT") + a 2-item dissent ledger (one TRUE minority, one FALSE decoy):
- **LEDGER-1 (true minority N1) → REVIVE.** Evidence: `task_config.py:228 GRIP_HALF_SPAN=0.060 # … arm-to-arm span = 120mm`; recompute `2×0.060=0.120≠0.100`; derived `:244-245` confirm ±0.060/side = 60mm offset, not the artifact's +40mm. Overturned the bad selection.
- **LEDGER-2 (false decoy) → CONFIRM-DISCARD.** Evidence: `:20 TABLE_HEIGHT=0.80` matches the artifact's 0.80; Reviewer C's "0.75" is false on disk. Refused to revive a wrong dissent.
- **Bonus — sub-claim precision:** flagged that Reviewer B's *own* fix-number ("+20mm/side") was itself wrong (0.120 span = 60mm/side) while still reviving B's true load-bearing claim. Revival is evidence-gated at the sub-claim level, not "revive every minority."

**Conclusion:** the revival channel works in BOTH directions — recall (true minority recovered, overturning a lossy Stage-1 select) and precision (false minority discarded; a dissent's presence in the ledger is not treated as evidence). The arbiter was disk, not a vote. This is the 「捨てられないで復活させる機能」, validated prospectively + blind. Artifacts: this doc + the run04 retrospective (§3).

## 9. %18 PV result (2026-06-14 02:38 JST — PASS, author≠reviewer)
%18 re-derived the blind-adjudication evidence ITSELF: N1 revive (`task_config.py:228`, 2·0.060=0.120≠0.100), decoy confirm-discard (`:20` TABLE_HEIGHT=0.80≠0.75), sub-claim isolation (`:244-245` ±0.060/side=60mm → reviewer-B's "+20mm" AND the artifact's "+40mm" both wrong) — all RE-DERIVE correctly. Design GATED SOUND (MERGE+ledger aligns with %18's union-not-select SSOT `percent18_lensed_v1.md:133` + Trial-B; Stage-2 attack+adjudicate, disk-as-arbiter, both-directions = precision-in-mechanism; maps to the generative-vs-adversarial split). **4 scoping notes (none blocking) — ALL ACCEPTED:**
1. **"Small-N safe" = the VARIANCE axis only.** Revival recovers true minorities caught by ≥1 body; a defect MISSED BY ALL bodies is not in the ledger → NOT helped by revival → that is the shared-floor MANDATES' job (recompute / grep-all-consumers / open-citation). **Mandates = coverage, revival = variance.** (Scopes §4/§5 here + FREEZE D2.)
2. **MERGE depends on Stage-2's attack (job #1)** to catch a FALSE-but-UNANIMOUS merged claim — the ledger logs only DISAGREEMENTS, so an uncontested-false claim isn't in it. Design handles it (Stage-2 attacks the merged answer); the dependency is now explicit.
3. **§5 MERGE>SELECT deviates from the human's literal 「選ぶ」(select)** → surface to the human at L3-GO as an evidence-grounded recommendation (human approves).
4. **Validation = sound PROOF-OF-CONCEPT** (n=1 adjudicator, author-run) → directional; the mechanism is correct BY-CONSTRUCTION (defer-discard + disk-arbitrate) → sufficient for soundness (blind-scorer strengthens, not required).
**DISPOSITION (%18):** fold into the 5CC L3 package as the two-stage wrapper + revival channel — a PIPELINE around the debate, NOT a replacement — under human-GO; **%12 routes the L3 edit**; cap stays human-pending (revival INFORMS it via variance-safety, doesn't decide it).

## Status
**HUMAN-GO GRANTED 2026-06-14 02:43 JST** — human approved BOTH (a) §5 MERGE>SELECT [Option A: MERGE+dissent-ledger] + (b) the L3 fold. **Relayed to %12** for the L3 skill edit (fold the two-stage wrapper + revival channel into the verification-subagent skill as a cap-agnostic PIPELINE; commit it — skill currently git-untracked). %18 PV recorded §9. Cap human-pending. Not frozen — pending %12's L3 implementation + commit, then I update the freeze + close.

---

## LANDING NOTE (%12, 2026-06-14 03:05 JST) — folded into the verification-subagent skill

This design landed as a fold into the on-disk operational skill. **This `docs/`
copy is the tracked durability/reviewability artifact** (Opt-1, human-approved
2026-06-14; matches the `docs/GROVE_CORE_SPEC.md` precedent — spec tracked in
`docs/`, skill on-disk).

- **Fold target (git-IGNORED by design — `.gitignore:104 /.claude/`; on-disk
  only, loaded each session):** `.claude/skills/verification-subagent/SKILL.md`
- The skill's authoritative pointer (`## Two-stage pipeline` section) resolves to
  THIS file.

**5 edits folded — a PIPELINE AROUND the debate; the core PROPOSE -> spawn ->
REBUT_OR_ACCEPT -> DECIDE (Steps 1-8) is unchanged:**
1. frontmatter `description` — +1 sentence (two-stage pipeline + revival wraps the debate, not replaces it).
2. NEW section "Two-stage pipeline + revival channel" — Stage 1 (generate + MERGE + dissent-ledger), Stage 2 (debate + dual job: ATTACK merged + ADJUDICATE ledger -> REVIVE/CONFIRM-DISCARD), revival (deferred evidence-gated discard, BOTH directions, disk-as-arbiter), coverage(=mandates) vs variance(=revival) kept distinct [note1], cost+status [note4].
3. Step 3 (input bundle) — + DISSENT LEDGER block (only if Stage 1 ran).
4. Step 4 (spawn) — + challengers ADJUDICATE ledger entries vs disk (dual mandate).
5. Step 6 (DECIDE) — + revival adjudication folds REVIVE/CONFIRM-DISCARD into the verdict.

**Invariants preserved:** cap-agnostic (no hard-coded N; cap human-pending),
UNION-not-select, pipeline-not-replacement, lensed scaffold + evidence-boundary
untouched, anti-2nd-SSOT (this doc is the pointer target; worked example/run04
numbers NOT restated in the skill).

**L3 gate trail (%12):** L-TRIAGE = L3 HIGH; RULE-CHECK stage2 PASS; layer-3
structural PASS; layer-2 post 5-body Debate = 1 consensus catch (this docs/
pointer must resolve -> fixed by committing this copy) + 2 LOW fidelity catches
(Stage-1 N not bound-equal to challenger count; Step-8 logging note for two-stage
artifacts) ACCEPTED + fixed -> DECIDE PASS; layer-5 SSOT-consistency PASS
(geometry/physics legs N/A for a governance doc — omission stated). Design =
%18-PV PASS (this doc, section 9, author!=reviewer). human-GO 2026-06-14 02:43 JST.
