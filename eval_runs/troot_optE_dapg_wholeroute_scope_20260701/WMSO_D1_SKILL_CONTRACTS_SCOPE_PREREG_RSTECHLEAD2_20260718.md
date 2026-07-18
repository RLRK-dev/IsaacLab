# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO **D1 Skill contracts** — scope pre-registration **v1**

- node `T-WMSO` (parent `T-ROOT-RS-TECH-LEAD2`); author `w2:pQ` (RS-TECH-LEAD2); independent verify `w2:pN` (OPS-SUP-CODEX); Vault custody `w2:p6`.
- prepared_at: **2026-07-18 ~22:43 JST** · repo HEAD `d854dc2b76` (advisory) · **design / scope DOC only; no code, no impl, no run, no gate PASS.**
- **basis (why D1 may open)**: D0 Architecture **EXIT GRANTED** — pN D0-exit independent design verify **round-3 = ✅PASS-CLOSE**
  (`WMSO_D0_EXIT_VERIFY_VERDICT_OPSSUP_20260718.md:105-124` "Verdict 4", observed 2026-07-18 22:14:32 JST; verdict record banked `99d8d60e12`;
  draft v4 banked `ac9fc83165`, sha256 `1b107df59f6e…`). LEDGER SSOT row = `00-DESIGN-STATUS-LEDGER.md:41` (node IN_PROGRESS→D1).
  charter §5 "next" = **D1 Skill contracts (adapters for BC+RL and at least one other policy lineage) — prereg / design gate**
  (`WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md:124`; verdict `:122`).
- **authorization**: Rs direct 2026-07-18 「D1 Skill contracts の prereg 着手」 (begin the D1 prereg). This doc is that prereg's **step 1**.
- **D1 charter target** (`WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md:124`): deliverable = *adapters for BC+RL and at least one other policy
  lineage*; exit condition = *contract tests and hash-pinned lineage*.

## §0. D1 gate-plan ORDER (this doc = step 1; mirrors the D0 B6 order, extended for D1's one code-touch)

1. **prior-art/reuse disposition + [DEFER-RECON] + scope bank (THIS v1)** → **pN scope concur** (or HOLD → fold → re-bank), same as D0.
2. author **D1 contracts *design*** (per-skill `SkillLifecycleContract` instances + discriminated `ExecutableIdentity`; concrete per-dim
   `BeliefState` table + A/B/C adapter map; contract-test-harness *spec*; hash-pinning *method*) — **design-only, no code yet**.
3. **`/pre-check`** on the D1 contracts-design draft (own artifact + bank, keyed to the draft's final sha; D0 B6 records-discipline).
4. **build step (the one D1 code-touch)** — implement the contract-schema types + contract-test harness + hash-pinning utility, **gated behind
   step-1 concur AND step-3 /pre-check**. Scope = **read-only conformance testing + content-hashing over *existing* checkpoints/sources**;
   ⛔ NOT training, NOT WMSO inference, NOT production-control edit, NOT closed-loop.
5. **run contract tests + pin hashes** → bank the passing-test evidence + the hash-pinned lineage manifest (each keyed to the artifact sha).
6. **pN D1-exit independent verify** — charter §5 D1 exit = *contract tests pass* ∧ *hash-pinned lineage*.

⛔ Steps 4–6 do **not** start until step-1 (pN concur) and step-3 (/pre-check) are cleared. This doc pre-registers **all six** so the scope of
the code-touch is fixed *before* it happens (adversarial-planning / no post-hoc scope drift).

## §1. Prior-art / reuse disposition (V10 guard run before design)

V10 guard `check_thread_vault_prior_art.sh --fail-on-blocker "skill contract" "policy lineage" "hash-pinned" "skill adapter"`
→ **findings=5, blockers=0, lessons=0, exit=0**. All 5 findings are the WMSO charter/verdict self-references (the D1 row itself,
`…CHARTER…:124` / `…VERDICT…:122`) — **no prior failed path, no NO-GO**. D1 is the charter-mandated next phase; it reuses D0's schemas and the
existing sha256 primitives, it does not repeat a failed path. Explicit disposition:

| item | source (HEAD-verified) | disposition |
|---|---|---|
| **sha256 content-hash of checkpoint/dataset** (`ckpt_sha256=_sha256_file(ckpt)`, sidecar JSON) | `bc_train_route.py:30,117-135` | **INCORPORATED as the hash-pinning primitive** — D1 `ExecutableIdentity` hashes = `hashlib.sha256` of the on-disk artifact; reuse verbatim |
| **`policy_sha256` / config-sha pinning in the runner** (`_sha256` helper; route/task_config/base/policy shas) | `policy_route_runner.py:58-60,152-154,456,622,1169` | **INCORPORATED** — surface-C route already pins policy+config+dataset shas; D1 reuses as the recorded-hash path |
| **D0 schemas** (`BeliefField`, `SkillLifecycleContract`, `SkillActionKey`/`ExecutableIdentity`, `SkillHandoffState`) | `WMSO_D0_ARCHITECTURE_DRAFT_…:75-92,134-162,249-272` | **INSTANTIATED, not re-designed** — D1 fills them per-skill; the *contract* was D0, the *per-skill fill + per-dim table* is D1 (`…:94,100`) |
| **existing skill vocabularies** `SkillName`(9) / `SkillType`(7) / `bimanual_*`(6) — **unreconciled** | `step_table.py:35-51` (HEAD-confirmed :35,:39,:46,:51) / `skill_adapter.py:45-58` / `skill_adapter_with_prediction.py:150-157` | **RECONCILED in D1-A** — one canonical `skill_id` set; the three vocabularies map into it (D0 §B FACTUAL, v4 §1) |
| **physics `StateSnapshot`** (state-capture substrate) | `snapshot.py` (HEAD-confirmed present) | **REUSED as capture substrate only** — the charter-§3 `SkillHandoffState` *contract* stays net-new (semantic ≠ physics snapshot; D0 §E:283-285) |
| **LL-WMF / LL-ORCH prior-art dispositions** (Option-α cascade, Gate-4 maturity, SPlaTES H<5, model-exploitation guard, Cascading-P0, scope-inflation NO-GO) | D0 scope prereg v2 §B1 (`…SCOPE_PREREG…_v2.md:18-31`) | **CARRIED unchanged** — dispositioned at D0; D1 adds nothing new here |
| **Gate-4 maturity** (min skill_SR ≥70% before closed-loop admissibility) | LL-WMF (D0 §0 reuse disposition, `…DRAFT…:55`) | **INCORPORATED as an admissibility gate, NOT a D1 gate** — D1 *authors* every skill's contract regardless of its current SR; closed-loop *admissibility* is O0/V0, downstream (see §2 #18) |

## §2. [DEFER-RECON] reconciliation record (D1 premises × DDR — §運用2 backstop, structural not grep-only)

DDR source = `00-DESIGN-STATUS-LEDGER.md §DDR`. Reconciling each FOUNDATIONAL item against D1's premises:

| DDR item | what it gates | gates D1 scope/design? | reconciliation |
|---|---|---|---|
| **#2** P3 body_q sync-premise (route/pin clock/placement) | route/pin physics correctness | **NO** | intra-skill route/pin physics; WMSO is an orchestration schema *above* skills, explicitly non-mixed (charter §8-2, D0 §H:394-396). Not a D1 dependency. |
| **#4** P2 non-crutch / fire≠retention / (d-b) deadlock | whether (d-b) removes the deadlock | **NO** | same non-mixing fence; (d-b) is a separate chunk. D1 does not consume or alter it. |
| **#12** fork-B V0 acceptance pending | training-ready; (d-b) landing-bind | **NO (downstream)** | training-ready is charter §5 **O0/V0**, downstream of D1. D0 gate⑩ (no premature claim, `…DRAFT…:417`) already fences it. |
| **#18** grip-efficacy SRG @ 4-substep | trainer grip verdict → launch; GATES (d-b) | **NO to D1 authoring; YES to closed-loop admissibility (later)** | a skill's **efficacy/SR** ≠ its **contract**. D1 authors the grip skill's contract (initiation/termination/handoff/fail-closed) at any SR; its admissibility as a WMSO-selectable *closed-loop* action needs Gate-4 (SR≥70%) at O0/V0, not D1. Contract will carry the maturity status honestly. |
| **#19** ENV-MULTIWORLD freeze (worlds 1-3 cable frozen) | multi-world *training* feasibility | **NO (downstream)** | training-path concern; D1 is pre-training contract/adapter design. |

**Genuine D1-local dependency (the only one): skill supply (`T-Skill`) → hash *pinnability*.** D1 can hash-pin only the lineages whose
policy/source/config artifacts exist on disk **today**. Where a lineage's artifact is **ABSENT** (AC/AR/IC RL wrappers = ABSENT, D0 §B:160) or
where a checkpoint exists but no sidecar hash was recorded (base BC / per-skill DAPG — sidecar present only on the surface-C route path,
`bc_train_route.py:117-135`), D1 pins by **direct content-hash of the on-disk artifact** (same `hashlib.sha256` primitive) where the file
exists, and marks the contract **`hash_unpinned` / `inadmissible`** (fail-closed, D0 §B:158-160) where it does not. ⛔ **D1 does NOT launch
training to manufacture a hash** (boundary held). **Conclusion: no FOUNDATIONAL DDR item blocks this prereg or the D1 contract design;** the
skill-supply dependency is handled fail-closed inside the contract, not by waiting.

## §3. D1 deliverable structure (each row DESIGN-ONLY at authoring; binding requirements folded)

| id | deliverable | binding requirement (charter / D0 / gate) |
|---|---|---|
| **D1-A** | **canonical `skill_id` reconciliation** — one authoritative skill set; map `SkillName`(9)/`SkillType`(7)/`bimanual_*`(6) into it, flag orphans/aliases | D0 §B FACTUAL "multiple **unreconciled** vocabularies" (`…DRAFT…:124-128`); a single key is the precondition for interoperable contracts (gate①) |
| **D1-B** | **per-skill `SkillLifecycleContract` instance** for each canonical skill, carrying the discriminated **`ExecutableIdentity`** (`LEARNED`/`SCRIPTED`/`WAIT`) | charter §3 fields (`…CHARTER…:82-96`); D0 §B contract (`…DRAFT…:134-156`). **BC+RL lineage must split** base_ckpt / finetune_cfg / final_policy hash (charter §3, `:94`). NEVER key by name alone. |
| **D1-C** | **hash-pinned lineage manifest** — pin each `ExecutableIdentity` hash to the on-disk artifact; per-skill `admissible`/`hash_unpinned`/`inadmissible` status | charter §5 exit = *hash-pinned lineage* (`:124`). Reuse `_sha256_file` (`bc_train_route.py:30,118`). Fail-closed on absent (D0 §B:158-160). |
| **D1-D** | **concrete per-dim `BeliefState` table + A/B/C adapter map** — every canonical `BeliefField` with field_id/semantic/dtype/shape/**SI unit**/frame/provenance/prod_admissible; per-surface raw-obs-dim → canonical-field mapping | D0 §A "concrete per-dim table = D1" (`…DRAFT…:94,100-106`). provenance mandatory per field; `PRIVILEGED_SIM` ⇒ `prod_admissible=false` (gate②, `:111-113`). |
| **D1-E** | **contract-test harness spec** — assertions that a published contract conforms: all mandatory fields present, provenance tagged, `prod_admissible` correct, `schema_version` valid, fail-closed action defined, hash pinned-or-explicitly-`hash_unpinned` | charter §5 exit = *contract tests* (`:124`); gate⑩ "contracts registered, not passed" (D0 §B:162). **Read-only conformance** over existing artifacts — no train/infer/control. |
| **D1-F** | **the two+ required lineages** — pre-registered concrete choice (see below) | charter §5 = *BC+RL **and at least one other** policy lineage* (`:124`); gate① algorithm independence exercised across `ExecutableIdentity` discriminants |

**D1-F pre-registered lineage choice** (grounded in on-disk identity availability; the "at least one other" is over-satisfied to exercise gate① across all three discriminants):

| lineage | `ExecutableIdentity.kind` | family | on-disk identity today | D1 role |
|---|---|---|---|---|
| **per-skill DAPG (LoRA-on-BC)** | `LEARNED` | BC+RL | checkpoint exists; **no recorded sidecar** (`train_common.py` version-hash ABSENT, D0 §B:132) → pin by direct content-hash | **required** BC+RL (charter §3 3-part lineage split) |
| **surface-C route BC** (actor-mean) | `LEARNED` | BC-only | **recorded** `ckpt_sha256` sidecar (`bc_train_route.py:117-135`) + runner `policy_sha256` (`policy_route_runner.py:622`) | **"at least one other"** — strongest pinnability (recorded hash) |
| **scripted skill** (e.g. `TRANSPORT`/`RECLAMP_L`/`HALF_UNCLAMP_RELEASE`) | `SCRIPTED` | script+config | source file + config/schedule content-hash | exercises `kind=SCRIPTED` (no weights) for gate① |
| **wait skill** (`CLIP_CONFIRM`) | `WAIT` | wait-config | wait_config content-hash | exercises `kind=WAIT` for gate① |

(Charter minimally requires BC+RL + one other; D1 covers **all three `ExecutableIdentity` discriminants** so gate① "one uniform contract for
LEARNED/SCRIPTED/WAIT" is demonstrated, not merely asserted. Any lineage whose artifact is absent at build time → authored contract + `inadmissible`, not dropped.)

## §4. D1 exit criteria (charter §5:124 — concrete, DESIGN-ONLY acceptance to be verified by pN at D1-exit)

1. **contract tests pass**: the D1-E harness runs green over every canonical skill's published contract (all mandatory §3 fields present +
   typed + provenance-tagged + fail-closed action defined + schema_version valid).
2. **hash-pinned lineage**: every `admissible` skill's `ExecutableIdentity` hash is pinned to a named on-disk artifact (sha256 recorded);
   every non-pinnable skill is explicitly `hash_unpinned`/`inadmissible` with the reason — **no silent gap**.
3. **≥2 lineages** with published, tested, hash-pinned contracts, including **BC+RL** (with the 3-part lineage split) — charter minimum met/exceeded.
4. **no premature claim**: D1 exit ≠ training-ready / closed-loop; O0/M0/S0/V0 remain gated (gate⑩; D0 §I:417).

## §5. Boundaries (held — a contract/adapter/test-harness changes none of them)

⛔ **UNAUTHORIZED until each own gate**: production control edit / training launch / WMSO inference / closed-loop authority / removal of any
existing safety-or-orchestrator path / p4 grip scope (charter §0/§8-4; node state.md §7).
⛔ **FOUNDATIONAL invariants (RS71 §0) unchanged**: DUAL-ARM · 88 mm two-EE grasp span / bases Y=∓0.35 · DiffIK-only (no kinematic teleport) ·
コ-shape gripper geometry LOCKED · no-kinematic-trick (only exception = clip-retention pin). D1 designs contracts/adapters *above* the skills;
it does not touch skill geometry/control. Any apparent change to these = **premise change = STOP → Rs**, not a design tradeoff.
⛔ **non-mixing** (charter §8-2): current (d-b) route/pin work and the `T-WM` classifier cascade connect to WMSO **by explicit dependency only**,
never merged into WMSO state; the route/pin chunk is **not paused** by D1.
⛔ **`T-WMSO-SDM` child** (D0 §H:390) is **not** created by this prereg — NEST child-node creation is Rs approval, and D1 does not need it (SDM is M0).

## §6. Ask to pN (OPS-SUP-CODEX)

**Concur** on this D1 scope (§0 gate-plan order · §1 reuse dispositions · §2 DEFER-RECON · §3 deliverable structure incl. the §3 D1-F lineage
choice · §4 exit criteria · §5 boundaries), **or flag gaps**, before I author the D1 contracts *design* (gate-plan step 2). In particular please
check: (a) the §0 code-touch scope (read-only conformance + content-hash only) is correctly fenced; (b) the §2 claim that no FOUNDATIONAL DDR
item gates D1; (c) the §3 D1-F "at least one other lineage" choice satisfies charter §5:124 and gate①. No experiment / retry / source promotion
is proposed here — this is a read-only design-scope pre-registration.
