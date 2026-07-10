---
doc_class: reference
---
> ⛔ SUPERSEDED / HISTORICAL (as-of 2026-07-11, COORD2 vault-audit) — tracking SSOT = LEDGER VL2 (`00-DESIGN-STATUS-LEDGER.md`). optE-B-BC-imitation: superseded by ladder-v2 / env-core. Do not copy live values — pointer task_config.py / successor docs.

# B2 KICKOFF SPEC — DR multi-demo BC for the whole C1→C2 route (schema v2 + fork-(iv))

**STATUS: FINAL (design-only; pre-check + re-check CLOSED 2026-07-02).** This document creates NO code, runs NO sim, uses NO GPU, edits NO locked file, commits nothing. It is the **INPUT** to the gate chain:

> **%12 review → 5体 or 縮退 debate → `/production-launch-gate` → Rs fresh GO.**

B2 execution is **NOT authorized by this document.** The §5.1 route-harness wiring is **designed here but NOT implemented** (its own L3 + DESIGN-GATE + Rs approval, spec §8-6b).

**Author:** COORD %11 · **Charter:** RS-TECH-LEAD %12 (B2 KICKOFF PACKAGE 起草, Rs 承認 item 1 = B2 準備 GO 起草まで) · **Drafted:** 2026-07-02 22:43 JST
**Rev v2 (2026-07-02 23:15 JST):** pre-check R1 = **BLOCK** (CRIT 1 / HIGH 2 / MED 5, all ACCEPT — caught offline pre-GPU = gate working as designed) → this v2 folds the 8 revision instructions (%12). All changes remain design-only; the `og_offline_gate.py` phase-anchor改修 (§1.4) edits a NEW 0-commit script, implementation gated on the B2 Rs GO.
**Rev v3 (2026-07-02 23:36 JST):** focused re-check = BLOCK (narrow, text-only). HIGH-3 + MED-4/5/6/7/8 CLOSED; this v3 supplies the missing DECISION-POINT NUMBERS: §3.3 pre-declared verdict table (NEW-1 — resolves decoupled-middle ⟂ any-STOP-wins), §3.2 (b)-pair numeric bands (CRIT-1), §3.4 15-phase movable/decoupled table + ≥0.15 null-beat margin (HIGH-2), held-out→(±8,±8) (NEW-4), cite fixes (NEW-5).
**Rev v3.1 (2026-07-02 23:46 JST) — FINAL:** direct checklist re-check = **PASS**; the RECONCILIATION is approved (seat γ⊥ = informative, NOT a GO-precondition — the funnel makes the seats structurally un-movable by this DR, consistent with MED-7 spend-gate/rollout-evidence). Added §1.4 og改修 **item (4)** = expand the OG-b probe/surface set to the DR-movable {0-3} (else the verdict table's movable rows are unmeasured). **This spec is now FINAL (design-only) — the input to the Rs presentation (fork-(iv) DQ6 + this FINAL + pre-check経緯; production-launch-gate runs separately just before any B2 execution).**

---

## §0. PURPOSE, DESIGN BASIS, AND FORK-ADOPTION DEPENDENCY

**Purpose.** B2 tests whether **multiple demos across a cable-XY domain-randomization (DR) range** teach the policy the **restoring term** that a single demo cannot provide — the exact gap the B1′ characterization isolated.

**Design basis (fork-(iv) separation — the load-bearing rationale).** The B1′ chain (CP1-CP5′, LEDGER row45, spec §10 E15 v2.2) established a **clean separation**:
- **fork-(iv) = 積分修復 (integration repair) — PROVEN.** Absolute-target per-phase-affine actions kill the closed-loop integration drift (Rs A-question = YES: abs-drift `corr(t)` NEGATIVE −0.42/−0.37, approach spike 433mm → re-anchor 9-16mm, video-analyst independently corroborated; vs the delta repr's monotonic 95mm-wall accumulation).
- **restoring = multi-demo の学習対象 (the B2-DR learning target) — NOT YET LEARNED.** With n=1 demo there is no off-path coverage, so the policy has no restoring term within the per-phase box (OG-b γ⊥ 0.66-1.17 = integrator; OG-b′ showed seat-phase contraction exists but box-scale residual drift remains) → B1′ rollout = BLOCKED_REACH_WALL.

**B2 = supply the restoring term via DR multi-demo.** The DR demo-SET gives the BC policy off-path coverage (many nearby cable configs) so that the learned map acquires a restoring/contraction property (γ⊥ → restoring regime). This is the direct, pre-registered test of the separation.

**⚠ FORK-ADOPTION DEPENDENCY (DQ6 Rs-PENDING).** This spec **presumes fork-(iv) adoption** (absolute-target repr, schema-v2 affine). Per LEDGER row45 the fork is **CHARACTERIZED — B2 採否 Rs-PENDING**. If Rs does NOT adopt fork-(iv), §1 (schema-v2 abs-affine) and §3 (restoring verification via OG-b) change materially. **The fork-adoption call is Rs's** (%12 to present); B2 build must not start before it.

**Grounding (§運用4 banked-design SSOT, read + cited):** LEDGER row45 (fork-(iv)) · `B_BC_BUILD_SPEC.md` v2.2 §5 / §5.1 / §5.3 / §5.5 / E3 / E7 / E15 (:128-159) · node `T-ROOT-optE-route-dapg-C1C2/state.md` DQ4/DQ5/DQ6 · `RS71-System-Spec-SSOT.md` §0 INVARIANTS + §1 · `R_S71_KO_GRASP_DAPG_DEMO_SPEC_77.md` (SPEC_77) · `task_config.py:22/:235/:264`.

---

## §1. SCHEMA v2 — 15-phase one-hot / obs 27D / abs-affine[15] (requirement 1)

**Trigger (E3, spec:113).** The FROZEN canonical npz is 13-phase (obs 25D) and drives B0/B1/B1′. The **committed recorder** (`route_demo_recorder.py`, `fd005ab83f`) emits **15 phases** on any NEW recording ⇒ **ALL B2 data is schema v2** (one-hot 15 / obs 27D), fixed at B2 kickoff. Converter asserts `len(meta.phase_names)` == schema version; mixed-version datasets = STOP.

### 1.1 The 15-phase schedule (verbatim from the committed route)

| idx (0-based) | 13-schema (`route_demo_to_bc.py:35-49`) | 15-schema (`test_newton_clip_routing.py`) | note |
|---|---|---|---|
| 0 | GRASP_HOVER | GRASP_HOVER | |
| 1 | GRASP_DESCEND | GRASP_DESCEND | |
| 2 | GRASP_CLOSE | GRASP_CLOSE | |
| 3 | LIFT | LIFT | |
| 4 | ROUTE_C1 | ROUTE_C1 | |
| 5 | C1_SEAT | C1_SEAT | verdict-critical |
| 6 | C1_PIN | C1_PIN | verdict-critical |
| 7 | L_HALF_UNCLAMP | L_HALF_UNCLAMP | |
| 8 | R_UNCLAMP_RISE | R_UNCLAMP_RISE | |
| 9 | GUIDE_C2 | GUIDE_C2 | |
| 10 | C2_REGRASP | **GUIDE_PRELIFT** ⬅ NEW | `test:4232` (inserted after GUIDE_C2) |
| 11 | C2_DUAL_SEAT | C2_REGRASP | verdict-critical · `test:4398` |
| 12 | C2_SETTLE | **C2_TRANSPORT** ⬅ NEW | `test:4535` (inserted after C2_REGRASP) |
| 13 | — | C2_DUAL_SEAT | verdict-critical · `test:4558` |
| 14 | — | C2_SETTLE | verdict-critical · `test:4575` |

**Two inserted phases:** `GUIDE_PRELIFT` (idx 10) and `C2_TRANSPORT` (idx 12) — both TRANSPORT-class (motion between seat events), proposed **NOT verdict-critical** (design-confirm with %12). The 13→15 index shift for the C2 tail is the source of the abs-affine remap below.

### 1.2 abs-affine[13] → abs-affine[15] correspondence

The B1′ converter builds `abs_affine[13][6][2]` (per-phase × per-axis lo/hi). Schema v2 builds `abs_affine[15][6][2]`:

| 15-idx | phase | affine source |
|---|---|---|
| 0-9 | GRASP_HOVER … GUIDE_C2 | **carry** (semantics unchanged; recompute lo/hi from v2 recordings) |
| 10 | GUIDE_PRELIFT (NEW) | **new box** from v2 recordings' waypoint min/max ±10% margin |
| 11 | C2_REGRASP | carry from 13-idx 10 |
| 12 | C2_TRANSPORT (NEW) | **new box** from v2 recordings |
| 13 | C2_DUAL_SEAT | carry from 13-idx 11 |
| 14 | C2_SETTLE | carry from 13-idx 12 |

**Encode/decode unchanged** (E15): `a = 2(wp−lo_p)/(hi_p−lo_p) − 1`; guard-1 v2 (span<30mm → widen to 30mm centered on midpoint (min+max)/2). **SEAT_Z_AXES=(2,5) unchanged.** **VERDICT_CRITICAL (OG gate) remaps to 15-idx {5,6,11,13,14}** = {C1_SEAT, C1_PIN, C2_REGRASP, C2_DUAL_SEAT, C2_SETTLE}.

### 1.3 ⭐ DR-critical affine design decision (multi-demo)

**The per-phase affine lo/hi MUST be computed over the UNION of ALL training demos' waypoints for that phase (aggregate demo-set), NOT per-demo.** Rationale: one policy's action encoding must be consistent across every offset variant, so the box must cover the full DR spread of each phase's waypoints (+10% margin, guard-1 floor). A per-demo affine would make identical `a` decode to different absolute targets across demos → destroys the label consistency BC depends on. This is the single most important schema-v2 converter change beyond the phase count. **Provenance + hull (E15-compliant, %12 confirm):** (i) the union affine is FROZEN into the converter output meta (`bc_dataset_abs_meta.json`) and the runner asserts affine-identity at load (B1′ provenance pattern); (ii) **held-out offsets MUST be INTERIOR to the convex hull of the SURVIVING (post-validity-filter) training offsets** so the union box covers their waypoints — a hull-external held-out waypoint would decode-clip (guard) → INVALID. **Post-filter assert (instr 4):** at convert time, each held-out offset ∈ conv-hull(surviving training offsets); a violation is **loud-reclassified to an EXTRAPOLATION probe and EXCLUDED from the primary rate** (never silently kept). The held-out (±8,±8) (instr 5) sits at |x|+|y|=16, inside even the diamond hull if the corners are filtered out. **Assert = CLOSED-hull** (boundary counts as inside) + a **per-waypoint decode-clip check**; if reclassification drops the surviving held-out count, **re-assert the ≥3 held-out floor** (fewer ⇒ widen/redesign; no silent <3).

### 1.4 Wiring items (schema v2, ALL design-only — implementation post-Rs-GO)
- Converter (`route_demo_to_bc.py`): schema-v2 branch — auto-detect `len(meta.phase_names)∈{13,15}`; build `abs_affine[15]`; obs one-hot 15 (dims 12:27); E3 assert. **seg-rule for the 2 NEW phases (instr 8 — on 15-schema, `route_demo_to_bc.py:201` `PHASES13[p]` IndexErrors and `:202` onehot-13 hardcode fail BEFORE the `:429` `==13` assert; all three need the schema-v2 branch):** `GUIDE_PRELIFT` → argmin-to-C2 (cable-follow, like GUIDE_C2); `C2_TRANSPORT` → argmin-to-C2 held-during-transport; `_seg_rule` (`:70`) gains a schema-v2 index branch (indices shift +1 after GUIDE_C2). **v1↔v2 box-span audit (instr 5):** the converter emits a per-phase box-span delta table (13→15) and **loud-flags any verdict-critical phase whose z-span grows >20%** (a looser box ⇒ degraded decode precision).
- Trainer (`bc_train_route.py`): `build_actor_critic(27, 6, …)` (obs 25→27).
- Runner (`policy_route_runner.py`): obs builder emits one-hot 15; abs-decode uses `abs_affine[15]`; repr/schema asserts extend to schema_version.
- **OG offline-code改修 (`og_offline_gate.py`, instr 1 — design-only, NEW 0-commit script, gated on B2 Rs GO):** (1) replace the uniform γ⊥ band (`:313-316`) with **phase-anchor-class dispatch** (§3.2 — clip-anchored γ⊥≤0.5 / cable-anchored (b)-pair); (2) fix the co-move arm from uniform R-fixed (`:63`, `:80` "seg co-moves with the R-arm axis") to a **phase-specific holder** sourced from `seg_rule_by_phase` (meta `held_seg_l` ⇒ phases 7-10 L-held, grip≥0.6 predicate; C2 approach = cable-argmin); **(3) band→verdict remap (instr 1 NEW-1):** replace the uniform any-MIDDLE→BLOCKED_FOR_USER combine (`:318-330`) with the **phase-class-aware §3.3 verdict table** (DR-decoupled middles EXEMPT; carried-STOP exempt) so `:318-330` no longer silently forces BLOCKED on an expected decoupled middle; **(4) expand the OG-b probe/surface SET (%12 nit, FINAL):** `og_b` computes per-phase via `range(13)` (`:97`) but the GATE + echo surface ONLY `VERDICT_CRITICAL` (`:313`/`:391`) = {5,6,11,13,14}, which EXCLUDES the DR-movable {0,1,2,3} that the §3.3 verdict table + null-beat REQUIRE → expand the surfaced/dispatched set to **{0-3} ∪ {11} (gating) ∪ decoupled (informative)** and update `range(13)`→`range(15)` (`:97`,`:250`) for the 2 new phases; else the DR-movable γ⊥ rows are computed but never surfaced (silent gap → movable rows永遠に未測定).

---

## §2. DR DEMO-SET PLAN — cable-XY ±20mm (requirement 2)

**Range (DQ4, Rs 決定 2026-07-02):** cable-XY **±20mm** (`CABLE_XY_DR_AMPLITUDE=(0.020,0.020)`, `task_config.py:264`). "開始" = later-expansion implied (Rs word) — B2 is the ±20mm start, not the final range.

**Counts (spec §1/§5.3/§8-6a):** **13 training-candidate recordings + ≥3 held-out.** Validity filter (§5.3): only **fingerprint-SUCCESS** scripted runs train; **held-out ⊂ scripted-SUCCESS draws only**; **min training floor = 6** — fewer valid ⇒ report **BLOCKED + widen/redesign** (no silent B1-redux).

### 2.1 Proposed explicit offset grid (no in-harness RNG — §5.1)

Explicit per-run offsets (mm), deterministic list (values, not RNG):

- **Training candidates (13):** center `(0,0)`; edges `(±20,0),(0,±20)`; corners `(±20,±20)`; half-edges `(±10,0),(0,±10)`.
- **Held-out (4, interior, NOT on the training grid):** `(±8,±8)` (instr 5/NEW-4 — moved IN from (±10,±10): (±10,±10) sits on the L1 edge |x|+|y|=20, so losing ONE filtered corner drops it outside the surviving diamond hull; (±8,±8) at |x|+|y|=16 keeps an ε-margin) — these ALSO require their own **scripted recording + convert (instr 3):** the OG-b′ held-out leg (§3.2) needs the held-out demos' ground-truth waypoints; **the pre-C1 reach screen CANNOT substitute** (it produces no trajectory/verdict). +4 runs +~2.7h (§4). The **post-filter hull assert (§1.3-ii)** applies to every held-out offset.

The **§6 pre-C1 reach screen + §5.3 scripted-SUCCESS filter** decide which of the 13 actually enter training (infeasible offsets self-remove — see §6 reach analysis).

### 2.2 Route-harness cable-XY offset wiring = NEW BUILD ITEM (§5.1 L3 — DESIGN ONLY)

**Verified fact (re-grepped 2026-07-02 + node state:43):** `randomize_cable_xy` is wired **only on the RL-env side** (`task_config.py:252-264`, `newton_approach_cable_mujoco_env.py`, `newton_aerial_regrasp_mujoco_env.py`). The **route harness has ZERO cable-XY wiring** — `policy_route_runner.py` / `route_demo_to_bc.py` / `route_demo_recorder.py` all read static `cable_xyz` from the demo/scene, none invoke `randomize_cable_xy`. So a route-harness cable-XY offset is a **NEW build item.**

- **Locked-file reality (§5.1, spec:67):** `build_scene` has **no cable-position param** (sig `test:1031-1032`; `cable_start` hardcoded `test:1365`). ANY wiring edits the **Rs-LOCKED route file** ⇒ **L3 + DESIGN-GATE + its own Rs approval (§8-6b) + fingerprint-equality proof that default-unset = byte-identical.**
- **Preferred form:** additive `cable_xy_offset=None` param (grasp_y precedent); `None` ⇒ byte-identical to current behavior (proven by fingerprint equality). Explicit per-run offsets, no in-harness RNG.
- **EE-target-follows-cable gate (§5.2 + SPEC_77):** the GRASP-phase EE target must **follow the ACTUAL (offset) cable** (later phases argmin-follow). **`grasp_y-sweep` is NOT a valid diversity proxy** — "EE targets must FOLLOW grasp_y to stay representative … off-center hits the known L/R reach wall" (`R_S71_KO_GRASP_DAPG_DEMO_SPEC_77.md:32-34`). ⚠ Citation hygiene: the spec's `SPEC_77:32-34` supersedes the earlier false `:56-58` cite (CC5-7a); the same bad cite in `P3_DEMO_RECORDER_SPEC.md:25` + node `state.md:41` is flagged-for-fix — re-verify the exact lines at wiring-implementation time.

### 2.3 INVARIANT #2 preservation (RS71 §0 #2 — confirmed non-touching)
A cable-XY offset **parallel-translates BOTH EE targets by the same (dx,dy)** ⇒ **88mm grasp span preserved** (`task_config.py:235`), **bases fixed at Y=∓0.35** (`task_config.py:22`) — INVARIANT #2 **untouched** (%12 concur 2026-07-02). The only feasibility question is per-arm reach-envelope, handled statically in §6 (a feasibility item, **not** an invariant change).

---

## §3. LEARNING / EVALUATION PLAN (requirement 3)

### 3.1 Training
- **multi-demo BC** on N≥6 scripted-SUCCESS schema-v2 demos (aggregate abs-affine §1.3), same trainer (`bc_train_route.py`), **seed-pinned** (E12), deterministic actor-MEAN inference (spec §3), sidecar provenance (E15).
- Same hyper as B1′ baseline (epochs 100→2000 convergence-extension clause, batch 256, lr 1e-3) unless the multi-demo loss curve dictates otherwise (record, no silent retune).
- **Val split (instr 8, pre-registered):** WHOLE-DEMO holdout (e.g. train 11 / val 2); **step-interleave FORBIDDEN** (interleaving frames of one demo across train/val leaks the trajectory → inflated val).

### 3.2 ⭐ Restoring-verification legs (the B2 acceptance core — inherits §8-1 + NEW)
- **§8-1 bars inherited (spec:94):** category-match RATE over the held-out set (deterministic-mean) + **per-rollout failure-taxonomy table** + **video-analyst on EVERY counted SUCCESS** (L-claw crop; rate reported split video-verified / numeric-only).
- **NEW restoring leg (offline, pre-sim) — pre-registered signal SPLIT by phase-anchor-class (instr 1 CRIT; the uniform γ⊥ band at `og_offline_gate.py:313-316` + the any-MIDDLE→BLOCKED combine at `:318-330` is WRONG-SIGNED for the cable-anchored phase; `:25` = the VERDICT_CRITICAL set):**
  - **(a) clip-anchored {C1_SEAT, C1_PIN, C2_DUAL_SEAT, C2_SETTLE}** (fixed-target seat, all **DR-DECOUPLED** per §3.4): co-moving probe reports γ⊥ (n=1 was **0.66-0.83** here; the 1.17 was C2_REGRASP = (b)). **Per the §3.3 verdict table this is INFORMATIVE — a restoring ≤0.5 is welcome but a MIDDLE does NOT block GO** (the seat funnels to the fixed clip; actual seating is confirmed by the rollout's seat-verified pin §4.5). The DR-supplied-restoring PROOF lives in the DR-movable phases + the C2_REGRASP (b)-pair + the null-beat (§3.3), **not** in these seats.
  - **(b) cable-anchored {C2_REGRASP}** (MOVING target = the cable): a single γ⊥≤0.5 is wrong-signed — correct cable-FOLLOWING shows as γ⊥≈1 (**n=1 measured 1.17 = integrator**). Use a **PAIRED signature (pre-registered bands, CRIT-1):**
    - **seg-following gain** = perturb {seg + L-holder-ee} together → the R decoded target follows: **∈[0.8, 1.2] = PASS** ("tracks the L-held cable").
    - **ee-only gain** = perturb R-ee only (the ACTING arm), seg fixed → R target restores to the cable: **≤0.3 = PASS** ("does not integrate its own drift / does not return to the old demo path"); **≥0.9 = STOP** (integrator recurrence).
    - **holder:** phases 7-10 = **L-held** per meta `held_seg_l` (grip≥0.6 per-frame predicate — the改修 inherits the predicate); the ee-only perturbation target is **R (the acting arm)**.
  - **(c) probe co-move arm = phase-specific holder** (NOT the uniform R-fixed at `og_offline_gate.py:63,80`): phases 7-8 (L_HALF_UNCLAMP / R_UNCLAMP_RISE) are L-held per meta `held_seg_l`, the C2 approach is cable-argmin — source the holder from `seg_rule_by_phase`.
  - **Evaluation basis (pre-declared):** OG-b measured **training-set-internal per-demo**, aggregated **worst-demo primary + median** (instr 8); OG-b′ on **held-out offsets** (next bullet).
  - **OG-a report-only E7 row (instr 5):** C2_DUAL_SEAT / C2_SETTLE **p95 z-decode-error** vs the E7 C2 margin **0.892mm**, noting the B0a **~1.2× EE→cable amplification** — report-only (informs risk R4), not a gate bar.
- **NEW closed-loop leg:** OG-b′ **transverse contraction on held-out offsets** (offsets NOT in training) — the generalization test (does restoring hold off the training grid?).
- **any-STOP-wins** for NON-carried STOP cells; the **§3.3 verdict table** refines MIDDLE handling per phase-class (DR-decoupled middles are informative, NOT GO-blockers); **held-out semantics pre-declared BEFORE runs** (§5.3).

### 3.3 Pre-declared OG verdict table (instr 1 NEW-1 — resolves the decoupled-middle ⟂ any-STOP-wins contradiction)
The current combine (`og_offline_gate.py:318-330`) maps ANY middle → overall BLOCKED_FOR_USER, so a DR-decoupled phase's EXPECTED middle would permanently block GO. Pre-declared per-phase-class verdict (implemented by the og改修 item (3), §1.4):

| phase class (§3.4 table) | GO cell | MIDDLE cell | STOP cell |
|---|---|---|---|
| **DR-movable** (grasp 0-3) | γ⊥≤0.5 (restoring) | not-yet-restoring → **BLOCKED_FOR_USER** | γ⊥≥0.9 → **STOP** |
| **cable-anchored** (C2_REGRASP) | (b)-pair PASS (seg-follow∈[0.8,1.2] ∧ ee-only≤0.3) | pair partial → **BLOCKED_FOR_USER** | ee-only≥0.9 → **STOP** |
| **DR-decoupled** (rest, incl. verdict-critical seats) | informative (γ⊥≤0.5 welcome, NOT a GO-precondition) | **informative — does NOT block GO** | non-carried → **STOP**; **§3.4-carried → informative** |

**Overall verdict (priority order):**
1. any **non-carried STOP** on any phase → **STOP** (real integrator fault; any-STOP-wins).
2. else **GO** ⇔ all DR-movable cells GO **AND** C2_REGRASP (b)-pair PASS **AND** beats the replicate-null by ≥0.15 (§3.4). *(DR-decoupled middles are EXEMPT — they do not block.)*
3. else → **BLOCKED_FOR_USER** → HOLD → %12 (a DR-movable/pair MIDDLE, or the null-margin unmet).

**Adjudication order:** OG gate (verdict table) → **if GO**, held-out rollouts (§8-1 bars) → video legs → E7 C2-margin capture (§5). ⚠ OG GO is a **spend-gate ONLY, not success evidence** (§7, instr 7); the B1′ precedent proved the gate predicts in-sim behavior with zero GPU surprise on the STOP side.

### 3.4 Attribution controls (anti-confound, pre-registered — instr 2 HIGH + 8)
- **Diversity-vs-budget null (instr 2/4):** train a null policy on **13 REPLICATES of the n=1 demo** with **matched total training steps** (seed declared), run the same OG. **Beat metric (pre-registered, instr 4):** worst-demo γ⊥ over the DR-movable phases {0-3} + C2_REGRASP's ee-only gain; the DR policy must improve on the null by **≥0.15 absolute** (a different margin needs a 1-line rationale). This is a **GO precondition in the §3.3 verdict table**, not a post-hoc note. ⚠ **cost correction (instr 4):** the null POLICY needs a cuda:0 **TRAIN** (~mins-0.3h); only the OG *evaluation* is offline (the earlier "0-GPU" was wrong) — §4 has a replicate-null-train row.
- **Funnel-null phase pre-registration (instr 2/3 HIGH-2) — rule: classify by phase-END target anchor** (cable/offset-following = MOVABLE / fixed-clip-convergent = DECOUPLED). Grounded on the demo phase-END targets vs fixed clips C1(0.35,0.15)/C2(0.4,0.075); the C1-pin (frame~2544) anchors the cable to fixed C1 so all post-pin phases funnel to fixed clips:

| 15-idx | phase | class | END-anchor rationale |
|---|---|---|---|
| 0 | GRASP_HOVER | **MOVABLE** | hover over the OFFSET cable grasp point (pre-pin, d(C1)=50mm) |
| 1 | GRASP_DESCEND | **MOVABLE** | descend to the offset cable |
| 2 | GRASP_CLOSE | **MOVABLE** | close on the offset cable |
| 3 | LIFT | **MOVABLE** | lift the grasped (offset) cable |
| 4 | ROUTE_C1 | DECOUPLED | END = C1 clip (d=0mm) |
| 5 | C1_SEAT | DECOUPLED | END = C1 clip (verdict-critical) |
| 6 | C1_PIN | DECOUPLED | pin to fixed C1 (verdict-critical) |
| 7 | L_HALF_UNCLAMP | DECOUPLED | post-pin, C1-anchored |
| 8 | R_UNCLAMP_RISE | DECOUPLED | post-pin rise, C1-anchored |
| 9 | GUIDE_C2 | DECOUPLED | funnels toward fixed C2 |
| 10 | GUIDE_PRELIFT (NEW) | DECOUPLED | prelift transition toward C2 (post-pin) |
| 11 | C2_REGRASP | **CABLE-ANCHORED** | (b)-pair — R follows the L-held cable (verdict-critical) |
| 12 | C2_TRANSPORT (NEW) | DECOUPLED | transport to the C2 seat (fixed) |
| 13 | C2_DUAL_SEAT | DECOUPLED | END = C2 clip (verdict-critical) |
| 14 | C2_SETTLE | DECOUPLED | END = C2 clip (verdict-critical) |

⇒ **DR-movable = {0,1,2,3}; cable-anchored = {11}; DECOUPLED = the other 10.** ⚠ NO verdict-critical phase is DR-movable → the restoring proof rests on the grasp phases + the C2_REGRASP (b)-pair; the decoupled seats' actual seating is confirmed by the ROLLOUT (§4.5 seat-verified pin), not by an OG middle. The §3.3 verdict table + the carried-STOP rule reference this bit.
- **n=1-carried STOP-cell rule (instr 8):** the B1′ n=1 carried sweep-z STOP cells (e.g. GRASP_HOVER Lz) — if they PERSIST in B2: persistence on a DR-**decoupled** phase = expected (not a new fault); persistence on a DR-**movable** phase = a real B2 STOP → HOLD → %12.

---

## §4. COST BREAKDOWN (requirement 4)

Whole-B aggregate updated to **~19-20h** (E15 cost/governance, spec:159); B2 slice below. **≥16 runs ≈ ≥10.7h ⇒ `/production-launch-gate` REQUIRED** (§5.4).

| Leg | Detail | Est. cost | GPU |
|---|---|---|---|
| Pre-C1 reach screen (§6, instr 6) | 13+4 offsets, IK-only PRE-C1 reach (no rollout); post-C1 feasibility only via recording | ~0.3-0.5h | cuda:0 |
| DR recording (training) | 13 training-candidate scripted routes @ ~40min (record via harness) | ~8.7h | cuda:0 |
| **Held-out DR recording + convert (instr 3)** | **4 held-out scripted routes @ ~40min + convert** (OG-b′ input; screen cannot substitute) | **~2.7h** | cuda:0 |
| Convert (schema v2) | offline numpy, all demos | ~mins | none |
| Train (multi-demo BC) | seed-pinned, ep100-2000 | ~mins–0.3h | cuda:0 |
| Replicate-null train (instr 4) | 13× the n=1 demo, matched steps, seed-declared (attribution null) | ~mins–0.3h | cuda:0 |
| OG offline gate | γ⊥ (phase-anchor split) / contraction / decode-mm | ~mins | cuda:0 (offline) |
| Held-out rollouts | ≥4 @ ~15-16min + retry budget | ~2-3h | cuda:0 |
| Video legs (incl. recording capture) | post-hoc offscreen per counted SUCCESS + §運用14 recording leg | ~0.5-1h | cuda:0 |
| **B2 subtotal** | | **~15-16h** | cuda:0 |

(Consistent with spec §1 "B2 record 8.7h + held-out ≥2h + retry ~2h" and §5.4 "≥16 runs ≈ ≥10.7h".)

---

## §5. PREMISES / RISKS TABLE (requirement 5)

| # | Premise / Risk | Direction | Note (file:line) |
|---|---|---|---|
| R1 | **fork-(iv) adoption** presumed | BLOCKER | DQ6 Rs-PENDING (LEDGER row45); if reverted, §1/§3 change |
| R2 | **P1 carried risks** | conservative-info | row54 sliding-cradle / §4 curvature / cg-GPU whole-route screen 未 / **reach-fragility** (node P1, state:32) |
| R3 | **device cuda:0 pin MANDATORY** | non-conservative if ignored | canonical route flips SUCCESS↔BLOCKED cpu(83.2mm)/cuda:0(0.9mm) at R re-grasp (memory `project-canonical-route-device-fragile`); run all recording/rollout on cuda:0; cpu only for read-only proofs |
| R4 | **E7 C2-margin FIRST measurement lands here** | conservative-info | tightest cliff = C2 `settled_in_notch` **0.892mm / 1.4mm** (spec E7:117); B1/B1′ never reached C2 seat → unmeasured; B2 (if it reaches C2) gives the first empirical C2 margin (a B2 deliverable) |
| R5 | **§5.5 non-conservative banking inherited** | ⚠ NON-CONSERVATIVE | a B2 PASS banks feasible-region + sim-perfect-state + scripted-events + pin-ON + cuda:0 ONLY — NOT full-range/deploy/real (survivorship + perfect obs; spec:71) |
| R6 | **reach-envelope at cable+20mm** | feasibility (see §6) | INVARIANT #2 preserved; binding constraint = marginal combined-obj IK conditioning, not reach limit — §6 |
| R7 | schema-v2 mixed-version data | build-time STOP | E3 `len(phase_names)` assert (spec:113) |

---

## §6. REACH-FEASIBILITY STATIC ESTIMATE (%12 anchor: R re-grasp reach-wall) (requirement 5-add)

Per %12: the reach-check leg is **design-only**, anchored on the **R re-grasp reach-wall** (P1: cuda:0 residual 0.9mm SUCCESS vs cpu 83.2mm BLOCK, node state:32/DQ6). Static estimate (offline geometry read, no run):

### 6.1 ⚠ Mechanism reconciliation (surfaced per §運用28/§運用10 — refines the anchor)
The anchor "0.9mm margin vs 20mm shift" needs one correction before the estimate is sound:
- The R re-grasp target is `(0.362, 0.119, 1.111)`; R base `(0, 0.35, 0.80)` ⇒ **reach = 530mm = 62% of UR5e's ~850mm** (both arms ≤76%, `C1_SEAT` 488mm / `C2_DUAL_SEAT` 556mm). **The re-grasp is NOT at the reach envelope.**
- Therefore **the 0.9mm is the COMBINED-objective IK residual at convergence (cuda:0), NOT a reach-envelope margin.** The cpu 83.2mm BLOCK is the same combined solver settling into a collision-dominated config — a **device-sensitive solver-conditioning cliff, not a geometric reach wall.**
- **Binding constraint = dual-arm collision-avoidance:** interEE = **99mm at C2_REGRASP / 92mm at C2_DUAL_SEAT** vs the **80mm floor** (70mm spheres + 10mm margin, `COLLISION_WEIGHT=5.0`, RS71 §1) = only **12-19mm headroom** (the "near-centre crowds wrists" regime).

**%12's intent STANDS** (plan for possibly-infeasible DR sub-ranges); the mechanism is sharpened: it is IK-conditioning-tip, not reach-margin-exceed — and this changes the estimate below.

### 6.2 (a) Static per-offset-direction estimate
A cable-XY offset **parallel-translates both EEs equally**, so:
- **Collision term (the binding constraint) is OFFSET-INVARIANT** (interEE unchanged) → the dominant wall does **not** move with the offset.
- **Per-arm reach changes only modestly** (exact 3D-norm `‖v+offset‖`, v = target−base = (0.362,−0.231,0.311)):

| offset (mm) | ΔR-reach (3D-norm) | R reach (mm) | % of 850mm |
|---|---|---|---|
| (0,0) nominal | 0 | 530 | 62% |
| (+20,0) | +13.9 | 544 | 64% |
| (−20,0) | −13.4 | 517 | 61% |
| (0,+20) | −8.4 | 522 | 61% |
| (0,−20) | +9.0 | 539 | 63% |
| (+20,−20) worst | +22.6 | 553 | 65% |
| (−20,+20) best | −22.1 | 508 | 60% |

**Method note (%12 §運用28 cross-PV):** these use the exact 3D-norm; the earlier linear `unit_xy` projection ((+20,0)=+16.9mm) OVERESTIMATES Δreach (upper bound). Since "not breached" held under the upper bound it holds a fortiori under the true smaller 3D values (%12 independent recompute concurs: (+20,0)=+13.7mm / worst +22.4mm; my recompute +13.9 / +22.6 — sub-0.3mm = input-coord rounding).

**Across the entire ±20mm box, R reach ∈ 508-553mm (60-65% of max) — the reach envelope is categorically NOT breached, and the binding collision constraint is invariant.** ⇒ **reach-BLOCK is NOT geometrically forced across ±20mm.** Any infeasible sub-range would come only from the **marginal combined-objective conditioning tipping** (the +X/−Y directions load reach most), which is **device-sensitive and NOT statically predictable** ⇒ needs the **cheap pre-C1 reach SCREEN** (instr 6 — IK-only, §4, ~0.3-0.5h, cuda:0, no rollout) to screen the PRE-C1 reach. ⚠ **the screen does NOT determine post-C1 feasibility** — the collision-marginal C2 re-grasp's real feasibility is fixed only by the full scripted recording (physics); by the offset-invariance argument above it is **nominal-expected**, but confirmed only at recording (retry budget sized for this). Expected infeasible fraction: **likely SMALL** (smaller than a naive 0.9mm-margin cut implies), but confirm empirically.

### 6.3 (b) Options for a non-feasible sub-range → **Rs DECISION ITEMS** (record-only; not selected)
If the pre-C1 reach screen finds infeasible offsets:
- **Opt-A (asymmetric DR range, e.g. +X/−Y clipped to ±10mm):** cable moves, span preserved ⇒ INVARIANT #2 untouched. *CC may-recommend (no invariant touch).*
- **Opt-B (draw training/held-out only from the feasible sub-range, §5.3 filter already enforces this):** survivorship-honest; report the feasible-region as the coverage number. *CC may-recommend (no invariant touch).*
- **Opt-C (change re-grasp Y-position to a less-crowded config):** ⚠ **touches INVARIANT #2 (grasp span / re-grasp geometry) = RS71 §0 Rs design Q.** *Record-only — cannot decide.*
- **Opt-D (relax `COLLISION_WEIGHT`/margin at the re-grasp):** ⚠ touches the dual-arm collision config = **REAL-wrist sim2real proxy** (memory `reference-dualarm-collision-objective-realrobot-proxy`; calibrating down = sim2real trap). *Record-only — cannot decide.*
- **(method, not an option)** the pre-C1 reach screen (IK-only) maps the pre-C1 reach; post-C1 feasibility is confirmed at scripted recording (offset-invariance ⇒ nominal-expected).

Opt-A/B recommendable; Opt-C/D **record-only, Rs design Q** (per %12 directive).

---

## §7. PRODUCTION-LAUNCH-GATE CHECKLIST INPUTS (requirement 6)

Skeleton input for the later `/production-launch-gate` run (NOT the gate itself; values to be finalized with B1′ results + the pre-C1 reach screen in hand):

- **Chain math (to compute at gate time):** B2 is a single-skill whole-route BC (no multi-skill chain) — effective SR = held-out category-match rate; **no chain-multiplication** (whole route is one learned unit, DQ1=B). Uplift claim = (B2 held-out rate) − baseline, where **baseline separates two distinct runs (do NOT conflate): B1 = 0/5 (delta-repr, pre-fork) and B1′ = BLOCKED_REACH_WALL (abs, n=1, the fork-adoption-relevant baseline)**; must cite the held-out json + the OG γ⊥ restoring evidence, not a proxy.
- **Assumptions + falsification tests:**
  - *iid retry / same-world reset* → falsify: N=2 byte-identity nominal (P7 pattern) confirms determinism before counting a rate.
  - *held-out ⊄ training* → falsify: assert the held-out offset list is disjoint from training offsets (§2.1).
  - *scripted-SUCCESS validity* → falsify: every training demo passes the fingerprint SUCCESS filter (§5.3) + the pre-C1 reach screen.
  - *restoring actually learned (not memorized / not budget-artifact)* → falsify: OG-b′ transverse contraction on **held-out** offsets (§3.2) **AND** the DR policy beats the 13-replicate diversity-null (§3.4).
  - *device* → falsify: cuda:0-pinned throughout; cpu excluded (R3).
- **NO_GO triggers (pre-declared):** any Unknown / unverified assumption; OG offline STOP; training floor <6; E7 C2-margin unresolved with a SUCCESS claim; §5.1 wiring not yet Rs-approved.
- **OG gate is ONE-DIRECTIONALLY validated (instr 7):** the OG offline gate is validated on the **STOP side only** (B1′ STOP correctly predicted the in-sim BLOCK); there is **NO GO→rollout-success example yet**. A B2 OG **GO is a spend-gate ONLY** (permission to spend GPU), **NOT success evidence** — success evidence = the held-out rollout alone. The **first B2 GO→rollout pair is the GO-side calibration datum** (a B2 deliverable).
- **GO ≠ GO_CANDIDATE:** production launch needs Rs explicit approval (§8-6b fresh GO).

---

## §8. GATE CHAIN + WHAT THIS DOC IS / ISN'T

- **This doc = DRAFT input.** Next: **%12 review → 5体 or 縮退 debate → `/production-launch-gate` → Rs fresh GO.**
- **NOT authorized by this doc:** B2 execution; the §5.1 route-file wiring (its own L3 + DESIGN-GATE + Rs approval); any commit.
- **Standing constraints honored:** design-only, 0-run, 0-GPU, locked 3-file 0-diff, 0-commit.

---

## §9. PROVENANCE

- **Binding sources:** `B_BC_BUILD_SPEC.md` v2.2 §5/§5.1/§5.2/§5.3/§5.5/§8/E3/E7/E15(:128-159) · LEDGER `00-DESIGN-STATUS-LEDGER.md` row45 · node `T-ROOT-optE-route-dapg-C1C2/state.md` DQ4/DQ5/DQ6 · `RS71-System-Spec-SSOT.md` §0/§1 · `R_S71_KO_GRASP_DAPG_DEMO_SPEC_77.md` · `task_config.py:22/:235/:264`.
- **Data reads (offline, cpu numpy — no run):** `p3_dod_cuda_demo_raw/route_demo_raw.npz` + `route_demo_raw_meta.json` (R/L EE + tgt at phase landmarks; resolved_clip_c1_xy=(0.35,0.15) / c2_xy=(0.4,0.075)).
- **Phase-name source:** `route_demo_to_bc.py:35-49` (13) · `route_demo_recorder.py`@`fd005ab83f` + `test_newton_clip_routing.py:4232/4398/4535/4558/4575` (15).
- **Wiring grep (2026-07-02):** `randomize_cable_xy` RL-env-side only; route harness 0-wiring — CONFIRMED.
- **v2/v3 code refs (pre-check, §運用28-verified 2026-07-02):** `og_offline_gate.py:313-316` (γ⊥ band GO≤0.5/STOP≥0.9) + `:318-330` (any-MIDDLE→BLOCKED_FOR_USER combine) + `:389` (echo); `:25` = VERDICT_CRITICAL set; `:63`,`:80` (R-fixed co-move) · `route_demo_to_bc.py:201` (`PHASES13[p]`, IndexErrors on 15-schema BEFORE `:429` `==13` assert) / `:202` (onehot-13) / `:70` (`_seg_rule`) · `bc_dataset_abs_meta.json` `held_seg_l` (phases 7-10 L-held, grip≥0.6 predicate).
- **Author:** COORD %11 · **Charter:** RS-TECH-LEAD %12 · **Drafted:** 2026-07-02 22:43 JST · **Rev v2:** 23:15 (pre-check R1 BLOCK → 8 instr) · **Rev v3:** 23:36 (re-check BLOCK → 6 instr) · **Rev v3.1 FINAL:** 23:46 (re-check PASS + item (4)) · **Status:** FINAL (design-only, 0-commit; pre-check/re-check CLOSED 2026-07-02).
