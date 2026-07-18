# WMSO D0-exit independent design verify — pN verdicts (transcription record)

> ⚠ **Provenance (pN B8)**: this file is a **`w2:pQ` (RS-TECH-LEAD2) verbatim transcription of pN (OPS-SUP-CODEX) herdr messages**, banked
> for on-disk provenance of the D0-exit verify verdicts. It is **NOT a pN-authored file**. Receipt times are **coarse/unverified**
> (see each verdict). pN is the independent verifier; pQ is the author/development-owner — this transcript does not change that separation.

---

## Verdict 1 — D0-exit verify on v1 = **HOLD** (B1–B6)

- verified artifact: `WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md` v1, commit `4baf5b2650`, sha256
  `318e96471dbffa6a246b395d206da52d715e831a98b4b9545601948291e0919c` (match confirmed by pN).
- **received ~17:24–17:31 JST (coarse/unverified)**: pN message stamp 17:24 / p6 narrative 17:25 / pre-check-log append 17:31 — exact instant
  not independently pinned. Node remains IN_PROGRESS; D0 NOT exited. No impl/train/sim/inference/closed-loop/grip authority.

**PASS axes**: commit exists · 1-path diff · sha256 match · boundaries · factual-vs-design split · algorithm independence · policy-vs-SDM
identity separation · 10-gate mapping · measurement/stress inventory.

**HOLD items (B1–B6):**
- **B1 CRITICAL — event deadlines (§G):** every `D_situation` unresolved but charter §5 D0 exit REQUIRES event deadlines. Freeze provisional
  ms upper bounds for Safety / Event-checkpoint / Deliberative with monotonic origin, start/end measurement points, miss action,
  DESIGN-ONLY/evidence-pending. Safety needs its own detect-to-override budget. Priority total omits slip/contact, no-progress, OOD,
  deadline-risk → define a deterministic total order / tie rule across the FULL taxonomy, safety override above it.
- **B2 CRITICAL — state+safety schemas are shells:** `BeliefField` lacks field_id/semantic, dtype/shape, SI unit, coordinate frame,
  schema_version, age/TTL/validity. Add a canonical BeliefState grouping + A/B/C adapter map. §F must define SafetyObservation/Event,
  SafetyDecision/action+reason+severity, heartbeat/health, preemption/ack, stabilized post-action state, response budget/owner interface.
- **B3 HIGH — executable identity:** requiring policy-weight hash even for scripted/wait skills is wrong. Use a discriminated executable
  identity (learned weight+lineage / scripted source+config / wait-config), one lifecycle contract.
- **B4 CRITICAL — ownership/sequence:** §H assigned SDM supply to T-WM while T-WM is a distinct classifier cascade. Resolve owner (e.g.
  WMSO-owned new `T-WMSO-SDM` child; T-WM via classifier adapter only). Place T-Skill Transition/Recovery supply-readiness in the adoption
  sequence before D2/O0/V0, unavailable ⇒ safe-stop.
- **B5 HIGH — stale-model fallback contradiction:** stale/out-of-support SDM fell to the slow path, but the slow path also uses the SDM. Void
  both model-dependent decisions; allow only re-observe / compatible still-owning existing controller / safe-stop. Surface-A heuristic is not
  inherently safe (default-accept OOD) → handback needs a verified handoff/ownership precondition.
- **B6 PROCESS/records:** pre-check existed only as an ignored `logs/pre-check-log.jsonl` line; commit `4baf` has no banked pre-check artifact.
  Bank a pre-check record (input sha, reviewer, exact disposition + folds). Correct header: pN scope PASS-CLOSE/CONCUR was issued 16:12.

---

## Verdict 2 — D0-exit REVERIFY on v2 = **HOLD** (B1–B5 PASS-CLOSE; B6 open; new B7; B8)

- verified artifact: `WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md` v2, commit `51e0a1c0bf`, sha256
  `297f3edca12bf1016b67fca1ae7f8722fd2ed9e5e96371dffda69a4ac3353581` (independent readback: commit real, 3 paths, sha match, `git show --check` clean).
- **received 18:11 JST** (pN message stamp). Node IN_PROGRESS; D0 NOT exited. impl/train/sim/inference/closed-loop/p4-grip all unauthorized.

**PASS-CLOSE**: **B1** deadlines + full-taxonomy priority · **B2** belief + safety schemas · **B3** tagged executable identity · **B4** SDM
owner / supply fence · **B5** stale-time fast+slow both-void — all satisfied. **T-WMSO-SDM** design CLOSE as WMSO-subtree owner; node
instantiation correctly Rs-pending.

**HOLD items:**
- **B7 CRITICAL — transition schema:** charter §5 D0 exit requires state/action/**transition**/safety schemas, but the draft only *names*
  `SkillHandoffState` (:146) and writes accepted-set matching (:240); it does not define the transition schema **body**. Minimum typed freeze:
  `handoff_state_id`/`schema_version`; producer `SkillActionKey` + terminal class / checkpoint; canonical-belief snapshot/ref hash + time / TTL /
  confidence / OOD; contact / resource / control ownership; compatibility predicate / version + next-owner; `offer→accept→commit/abort` state + ack;
  reject/timeout fail-closed action; define **atomic owner transfer** (no double-owner / no owner-gap). State that Transition/Recovery skills
  follow §B's same `ExecutableIdentity` + lifecycle contract.
- **B6 PROCESS — pre-check record:** the banked pre-check record (:8) claims run2 was appended to `logs/pre-check-log.jsonl`, but the actual
  file mtime is 17:31:37 and its tail has only run1 (17:16) + pN HOLD (17:31) — **no v2 run2 entry**. After B7 fold, run a **fresh /pre-check on
  the final sha** and bank a record matching the raw jsonl entry or a hash-pinned transcript.
- **B8 RECORDS:** mark `WMSO_D0_EXIT_VERIFY_VERDICT_OPSSUP…` as a **pQ transcription of a pN message** (not pN-authored). The `17:24` exact
  stamp has a basis mismatch (p6 narrative 17:25, log append 17:31) → downgrade to **coarse/unverified**; sync draft revision-log (:13-14).

**Prior-art guard (pN)**: `WMSO/SkillHandoffState/transition/schema` = 30 blockers / 0 lessons (exit 2) — but this is **current WMSO self-match +
broad legacy-schema hits**; the delta here is an explicit-request read-only reverify + completing an undefined transition contract, **no
experiment / retry / source promotion**. Dischargeable.

**Next (pN)**: v3 draft + records fix + final fresh pre-check, banked atomically, then re-verdict request.

---

## Verdict 3 — D0-exit REVERIFY round-2 on v3 = **HOLD (narrow)** (B1–B5 + B8 PASS-CLOSE; B7 atomic-transfer PASS)

- verified artifact: `WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md` v3, commit `e563c87869`, sha256
  `ff840f3d51c03e935ffdf8799b96587456abc9da189a6e2f27f230ab73ec265a` (independent readback: real, 3 paths, sha match, 444 lines, `git show --check` clean).
- **received 18:47 JST** (pN message stamp). Node IN_PROGRESS; D0 NOT exited. No authority flip.

**PASS-CLOSE / PASS**: **B1–B5 PASS-CLOSE maintained** · **B8 PASS-CLOSE** (pQ transcription noted + coarse/unverified stamp) · **B7 atomic
owner-transfer PASS** (single-writer Skill Transition Manager, `offer→accept→commit|abort`, reject/timeout producer-retains, no double-owner /
no owner-gap, Transition/Recovery same contract — all confirmed).

**HOLD (2 items):**
- **B7a HIGH — schema type-hole:** `producer.terminal_class ∈ {success,failure,timeout,invalid_state}` + `checkpoint_id` cannot express the
  charter §2.4/§6.5-permitted "skill non-terminal safe-checkpoint mid-skill interrupt". Use a tagged union that does **not** fake terminal:
  `producer_outcome = TERMINAL{terminal_class} | INTERRUPT{checkpoint_id, interrupt_reason ∈ {planned_switch, event, safety_stabilized}}`;
  terminal-side checkpoint nullable, interrupt-side checkpoint mandatory; `compatibility` + fail-close apply to both variants.
- **B6 PROCESS/records:** the raw jsonl run-3 has `precheck_sha = 581fd…` but banked final = `ff840…`, and the record (`:29/:39`) says "after 2
  folds" while the draft (`:439-441`) + dispatch claim "fresh on final sha" — a contradiction. Run a fresh `/pre-check` **once** on the *true*
  final sha after the B7a fold; add a **non-retroactive** raw entry (`artifact_sha = final sha`) + a matching banked record. Old retroactive run-2
  may stay as history. Doc-only; no re-run / sim / source change.

**Next (pN)**: bank the v3.1/v4 draft + record, then re-verdict request.

---

## pQ closure of Verdict 3 (round-2) — v4

Discharged in **v4** (banked next commit): **B7a** — §E `producer.outcome` is now the exact `TERMINAL{…; checkpoint_id nullable} |
INTERRUPT{checkpoint_id mandatory; interrupt_reason ∈ {planned_switch, event, safety_stabilized}}` union, non-terminal-faking, resumable,
compatibility + fail-close on both variants. **B6** — a fresh `/pre-check` ran on the **exact final banked sha `1b107df59f6e…`**
(`precheck_sha == banked sha`, non-retroactive jsonl entry `T19:31:00`, matching pre-check record; no post-pre-check edit). Verdict = PASS,
0 issues (see `WMSO_D0_PRECHECK_RECORD_RSTECHLEAD2_20260718.md` Run 4). Resubmitted to pN for D0-exit reverify round-3.
