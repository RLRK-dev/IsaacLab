---
doc_class: design-surface
---

# St2 Build Spec — Derived-Source Row Schema (Verbal-Teaching, design paper)

**Node:** T-ROOT-Verbal-Teaching-20260705. **Stage:** St2 (schema enrichment + fix-⑤-as-row). **Status:** **v0.4 — ✅ Rs-APPROVED** (design + Q2=B [absorb] + Q5 [orientation-lock executed], 2026-07-06 `b7d7857dfc`) — **paper only (0-commit); BUILD deferred + Rs-gated.** **Builds on:** `DESIGN_V1.md` v1.4 §3.3/§4 (Rs 承認 `b17b473a15`). **Authorized:** Rs「VT St2 着手可」2026-07-06 08:3x (`eba71929b3`); paper 先行 = 即時 GO, runner edit = deferred (§5).

---

## §0 Grounding + scope + baseline

- **Baseline (execution-system SSOT):** R3 = `thread_isaac_lab/scripts/test_newton_clip_routing.py` @ **committed `6808964dc3`** ("Adopt F-1b'' snap-down band", round-2 validated). **VERIFIED 2026-07-06 08:4x:** working-tree runner **== `6808964dc3`** (`git diff --stat 6808964dc3 -- <runner>` EMPTY; `git status` clean) AND runner unchanged over `6808964dc3..HEAD f6a9dd2ebd` (intervening commits `ef920efb3c`/`f6a9dd2ebd` = map/LEDGER/plan surfaces only). Committed-blob spot-check `:3946/:3986/:4240` = EXACT. **All R3 file:line cites below are anchored to `6808964dc3`.**
- **⚠ re-base at arc close (%12 2026-07-06 08:48 — drift prevention):** φ10 追撃 (①) may further evolve R3. This spec's R3 description is a **snapshot of `6808964dc3`**; it **MUST be re-based against the then-current committed runner immediately before any St2 build edit.** (The φ10/DC-1 arc has closed — %12 09:57; the runner is currently still byte-identical to `6808964dc3` per RV, but re-verify at build since HEAD advances.) Every `@6808964dc3` cite = a re-verification anchor for that re-base.
- **Scope (charter-faithful):** St2 ONLY = (a) derived-source row schema, (b) fix-⑤/F-1a row-ification proof plan, (c) per-row `emits_legs` declaration, (d) primitive audit. **Paper only.** No runner edit this turn or until the build gate (§5): spec chain complete → Rs packet → Rs build-auth → L3 + byte-id re-proof. (φ10-collision constraint RESOLVED %12 09:57; `DESIGN_V1.md` §3.3:110-111, §6:203.)
- **Grounding set (read + cite this turn):** `DESIGN_V1.md` v1.4 §2.2/§3.1/§3.3/§3.4/§4.2/§4.4; `STEPTABLE_SCOPING_COORD2.md` :35/:52/:69/:79-81 (derived-source taxonomy); `CHARTER_V1.md` :15,:23-27; `RS71-System-Spec-SSOT.md` §0 (INVARIANTS); `LEDGER:44`; RUN1_REFERENCE (latest = byte-id target, §4.2).
- **INVARIANTS (RS71 §0, Rs 専権 — St2 must NOT touch):** #1 dual-arm / #2 88mm span / #3 DiffIK-only / #4 コ-gripper LOCK / #5 no-kinematic-trick (pin = clip-retention sole exception). **St2 adds target-SOURCE expressiveness; it changes NO invariant and adds NO motion primitive.**

## §1 What St2 adds (the gap it closes)

- **Problem (validated; T2 gate MET cumulatively, `state.md` 08:09):** R3's route behavior is defined by RUNTIME-derived targets (caveat-a / fix-⑤ / argmin / F-1a / pin), but the St1a/St1b table schema carries only CONSTANT targets + within-leg amplitudes. A new derived-source teaching therefore requires **R3 hand-authoring** (fix-⑤ ~1.5h measured `STEPTABLE_SCOPING_COORD2.md:15`; F-1a in W0-e). `STEPTABLE_SCOPING_COORD2.md:35`: "schema/expressiveness drift = **the core gap**."
- **St2 = the derived-source schema:** a row declares `target_source ∈ {constant, cable-derived, clip-derived}` + a **bounded** derivation spec, so a fix-⑤-class teaching becomes a ROW EDIT, not an engine edit. (`:79-81`: "the one-time cost is building the primitive library; **thereafter fix-⑤-class changes are row edits**.")
- **⚠ Honest ROI scope (L3 NHA / CC6):** St2's value is for **FUTURE, genuinely-new (non-reuse) derived sources** — it makes NO existing source cheaper (all 5 DS are already built; fix-⑤'s ~1.5h is a SUNK cost). The "gate met by 2" counts **built** sources, and **DS1 (caveat-a) + DS2 (fix-⑤) are the SAME derivation template** (region-mean, Y vs X) ≈ 1 primitive class; the scoping calls the set "nearly closed" (`STEPTABLE_SCOPING_COORD2.md` S-7). So the St2 **BUILD stays DEFERRED** (Rs-gated, post-φ10/DC-1) on a genuine new-source trigger — NOT auto-triggered by this paper. This paper defines the schema so a future new source is a row edit; it does **not** claim the build pays off today.
- **What St2 does NOT do (scope wall):** it does NOT invent new MOTION primitives (all motion stays `ik_move_both`/`cage_close`/`settle`/`grip`/`pin`); it adds a TARGET-source layer + the leg-count audit. **Structural leg add/remove and new derivation-BRANCH add stay Rs 専権** (§2.3).

## §2 The derived-source row schema (concrete)

### §2.1 The `target_source` object (per-arm) — extends `DESIGN_V1.md §3.1`

| Field | Domain | Meaning |
|---|---|---|
| `kind` | `constant` \| `cable-derived` \| `clip-derived` | source class |
| `anchor` | (x,y,z) or ref-id | constant coord, or reference point (clip-id / grasp-region centre) |
| `measure` | `none` \| `cable-region` \| `guarded-crossing` \| `clip-seat-event` | runtime read (constant → `none`) |
| `mask` | region predicate | e.g. `|Y − anchor_Y| < 0.10` (caveat-a/fix-⑤ grasp region, `:3945`) |
| `reduce` | `mean` \| `argmin` \| `nearest-node` | reduction over masked bodies |
| `transform` | `identity` \| `comp = clamp(−(1−λ)·δ, ±c)` | coefficient map (F-1a retention comp, `:4240`) |
| `gate` | `always` \| `offset(axis)` \| `guarded-pass` \| `clip-seat` | activation condition (byte-id preservation) |
| `taut_gate` | bool | cable-derived requires the taut-route premise (`DESIGN_V1.md §3.1` %10-caveat) |

**Byte-id preservation — TWO mechanisms (obstacle B, `DESIGN_V1.md §2.2:58`; CORRECTED per L3 CC2-HIGH):** a derived source keeps the nominal sha unchanged by ONE of two distinct mechanisms, and the row MUST declare which:
- **(a) offset-gated SKIP** — an `if offset != 0` gate skips the whole block on nominal → the target stays its banked constant (no measure, no print). Members: **DS2** fix-⑤ (`:3983`), **DS3** F-1a (`_f1a_on :4222-4223`), F-1b (`:3957`).
- **(b) always-run DETERMINISM** — the derivation runs **UNCONDITIONALLY** on nominal, but the route is **RNG-free** (no `np.random`/`manual_seed`/`wp.rand` in the route body — RV-verified) so under the **fixed initial config + deterministic physics stepping + fixed IK warm-start seeds (`seed_l`/`seed_r` `:2819`/`:3060`/`:3254`) + fixed settle counts** it reproduces the SAME measured value the reference recorded → byte-id by **deterministic reproduction, NOT collapse-to-constant**. Members: **DS1** caveat-a (unconditional `:3942-3948`; `S6_ENGAGE_YC` is the mask-CENTRE + fallback, NOT a gate — `:3946` `else _grasp_at`), **DS4** argmin (runs every `C2_REGRASP` `:4675`).

⚠ **A class-(b) row MUST NOT be built with `gate=offset`** — that would SKIP the measure on nominal → arms at a wrong constant → `route_demo_raw.npz` sha ≠ `RUN1_REFERENCE_V2 5f1c3f92` → byte-id DoD FAILS. (This is the exact fact `DESIGN_V1.md §2.2:58` recorded as "CC2 VERIFIED": `GRASP_YC=np.mean(_near)` runs unconditionally on nominal.)

### §2.2 The 5 derived-source primitives (the library — grounded @`6808964dc3`)

| # | Primitive | R3 site | `kind` | measure / reduce / transform | `gate` |
|---|---|---|---|---|---|
| DS1 | caveat-a (grasp-Y re-centre, 88-span-preserving) | `:3942-3946` | cable-derived | region-mean over `|Y−grasp_at|<0.10` → `mean` → identity | **always** (unconditional run; byte-id via DETERMINISM (b); `S6_ENGAGE_YC` = mask-centre+fallback, NOT a gate) |
| DS2 | fix-⑤ (grasp-X / R.x := cable-X) | `:3983-3986` (load-bearing: gate `:3983`, mean `:3986`; comment `:3978-3982` excluded) | cable-derived | same mask, cable-X → `mean` → identity | `offset(X)` `cable_xy_offset[0]!=0` (`:3983`) |
| DS3 | F-1a comp (C1-seat X). ⚠ C2-side `:4840` `_c2x_comp` is **F-3 = WITHDRAWN deviation → EXCLUDED** (note below) | C1 `:4234-4277` | cable-derived | `guarded-crossing` `_w0e_guarded_cx`, δ=cx−x_clip → `clamp(−(1−λ)δ, ±22mm)` (`:4240`, λ=0.5 `:4230`) | `offset ∧ guarded-pass` (`:4235-4237`) |
| DS4 | argmin (C2 R re-grasp target = ACTUAL cable; **TWO Rs-LOCKED anti-reverts**) | `_kR` `:4665`, bow X/Z `:4667`; phase `:4675`; config gate `C2_DUALSEAT∧SEAT_TOPDOWN` `:4624-4626` | cable-derived | cable bodies → `argmin(|body_Y − (c2y+GHS)|)` → R bow X/Z (`:4662-4667`) | `C2_REGRASP` phase; **always-run UNDER the canonical dualseat config** (`C2_DUALSEAT∧SEAT_TOPDOWN`=1, both default 0 `:4624-4626`; state `RUN1_REFERENCE_V2`'s values at build — RV NEW-3); DETERMINISM (b) |
| DS5 | pin (clip-retention event; **INV#5 sole kinematic exception**) | pre-alloc `:1384-1399`; activate `:4356-4387` (`eq_active=1 :4379`, ACTIVATED print `:4385-4387`) | clip-derived (event) | verified seat → per-clip `eq_active` | **`PERCLIP_PIN` flag (default OFF) ∧ clip-seat** (RS71 §2; `DESIGN_V1.md §4.3`) |

**⚠ F-1b is NOT a derived-source (it is config-derived = St1a-class):** F-1b's Δy = `_dphase` bands (snap-down / B1 / B2) computed from the SCENE offset `dy` (`:3956-3974`), explicitly "**config-derived operand (NO node-state read; bright-line 4)**" (`:3954`) — a launch-computable parametric offset (St1a), NOT a runtime cable measurement. This is the exact St1a/St2 boundary the T2 count turned on (`state.md` 08:09). Listing F-1b under St2 would be the same class-error the debate CRITICAL caught.

**⚠ DS4 carries TWO Rs-LOCKED anti-reverts (`:4662` + `:4678`, both 2026-07-01「先祖返りしないように」; L3 CC3-HIGH):**
1. **Position lock (`:4662-4667`):** the target MUST be `argmin` over ACTUAL cable bodies — a fixed target reproduces the "R not re-grasping" air-grip bug (`:4633-4635`).
2. **Orientation lock (`:4678-4681`):** the re-grasp arm MUST be **square-on** (`C2_TILT_SIGN=0`); reverting to tilt-follow (`=1`) makes "R misses 0N" on the taut route.

**Mandatory `inv_binding` (IMMUTABLE, carved OUT of the §2.3 teachable set):** DS4's `{reduce=argmin over ACTUAL cable, target=c2y+GHS, orientation=square-on (C2_TILT_SIGN=0)}` are Rs-LOCKED and NOT teachable. ⚠ The "pin-to-a-constant" tripwire is INSUFFICIENT (CC3): editing `reduce` argmin→mean stays "derived" yet re-breaks the air-grip lock. So **any edit to a per-DS Rs-LOCKED derivation field → `BLOCKED_FOR_USER`** — not just a constant-pin.

**Governance escalation (CC3 — NOT a silent edit):** DESIGN_V1 §3.1 (Rs-approved v1.4) exposes per-arm `orientation`=tilt-follow with NO inv_binding → the C2_REGRASP arm's orientation companion needs the same LOCK. 07-Design is Rs-専権 (§運用4 write-side); this is **flagged for Rs**, not edited here — St2 must not bind the C2_REGRASP arm to tilt-follow, and DESIGN_V1 §3.1's orientation row should gain the matching inv_binding at Rs's discretion.

**⚠ The C2-side `_c2x_comp` (`:4836-4893`, flag `W0E_F3` **default-ON `:4845`="1", offset-gated**) is F-3 — a WITHDRAWN counterproductive deviation** (`LEDGER:44`; DESIGN_V1 §4.3「passes both gates yet is counterproductive」). Folding it into DS3 as a "C2 analog" was a **v0.1a error that echoed the DESIGN_V1 CRITICAL** (smuggling a withdrawn/structural deviation into a routine primitive). It is **EXCLUDED from the DS3 reproduced-primitive set.** ⚠ **Because F-3 is default-ON + offset-gated, §4.2's `W0E_F3=0` guard is LOAD-BEARING** — the F-1a proof runs on offset cells, so without explicitly setting `W0E_F3=0` the proof would co-execute F-3 and green-light reproducing a withdrawn deviation (RV NEW-1; CC2 + CC5 converged on the F-3 identity). **Operational realization (%12 10:04):** the official round-2 grid achieved F-3=OFF via the runner's **`FON_V1` env pin** (→ `[W0E-F3]` log 0-hit, official 0.716 as-executed intact); the code-default-ON flip (`W0E_F3`/`W0E_F1A_V2` both `:4232`/`:4845`="1") is a separate **Rs-batch item on %12's side** (banked `867625e9e1`), referenced here only.

**⚠ DS5 (pin) mandatory `inv_binding` (CC3 — parity with DS4):** the pin is INV#5's SOLE physics-bypass (RS71 §2/§5, clip-retention only). A pin / clip-derived row's `gate` MUST be **clip-seat-verified** — a pin row with `gate ≠ clip-seat` → `BLOCKED_FOR_USER` (the schema itself binds it, not only the referenced DESIGN_V1 §4.3 parser). State the reference's `PERCLIP_PIN` value at build so DS5's byte-id target membership (pin present vs absent) is explicit (CC2).

### §2.3 The 1:N problem for derived rows — CONDITIONAL leg emission (the crux)

DS3 (F-1a) emits a **variable** leg count via **NESTED** gates: (i) the initial guarded measure gates lift/shift (`:4233-4246`); (ii) a SECOND high-re-measure gate (`:4268`) adds/drops the **trim** leg — on high-PASS the `C1v2-TRIM` `ik_move_both` fires (`:4275-4276`), on high-REJECT it is SKIPPED (comp1 MAINTAINED + FLAG, `:4269`). A derived-source primitive's `emits_legs` is therefore **NOT a fixed list** — it is **gate-conditional at MULTIPLE nesting levels**.

**⚠ Branch-completeness is RECURSIVE (%10 review ②):** every internal gate that adds/drops a leg — including F-1a's high-re-measure trim gate (`:4268`) — is a DECLARED LEAF branch. The audit (§3) binds the OBSERVED **leaf** branch, not just the top-level gate; otherwise the branch-set under-bounds the leg count (the exact leak §2.3 exists to close). A conditional primitive's declaration is complete only when every leaf (product of all internal add/drop gates) is enumerated.

**Schema resolution:** `emits_legs` for a conditional primitive = a **declared SET OF BRANCHES**, each `{gate_predicate → ordered leg-label list}`. The primitive audit (§3) asserts the EXECUTED branch's leg sequence == the declared branch for the OBSERVED gate outcome (NOT a single fixed list). This makes the conditional **explicit + auditable** rather than hiding leg-count variation inside the primitive (`DESIGN_V1.md §4.4#2`, finding 3).

**⚠ Structural boundary preserved (先祖返り guard):** the BRANCH SET is fixed at AUTHORING = **Rs 専権** (adding/removing a branch = new motion; e.g. F-1a-v2's lift/shift/trim branch was Rs-authored structural work, NOT class-A — `DESIGN_V1.md §4.2:153`, LEDGER:44). **Enforcement locus (CC3):** the ordered-multiset audit (§3) guarantees CONSISTENCY (executed==declared), NOT authorship — "branch-add = Rs 専権" is a **parser/governance gate** (`DESIGN_V1.md §4.2` step 2-ii), not a property the audit provides. Teaching may edit ONLY the derivation params (λ, clamp, mask) WITHIN an existing branch, **MINUS any field a DS marks Rs-LOCKED** (e.g. DS4 `reduce`+target+orientation, §2.2 — a still-"derived" `reduce` edit can break a Rs-LOCK without tripping a "not-constant" predicate, CC3). Never add a branch; a new branch OR a Rs-LOCKED-field edit → `BLOCKED_FOR_USER`.

## §3 `emits_legs` + primitive audit (St2 runner instrumentation)

Per `DESIGN_V1.md §4.4#1/#2` (St1b+ = locked-runner edit), St2 ships the runner instrumentation. **`emits_legs` differs by DS class (CC4-MED — §3.1 previously mis-said "DS1-DS4 are ik_move_both legs"):**
- **DS1 / DS2 / DS4 = VALUE-derivations → `emits_legs = ∅`.** They emit ZERO `ik_move_both` legs; they re-target DOWNSTREAM legs (caveat-a → `[S6_ROUTE] :3947`, fix-⑤ → `:3987`, argmin → `[C2-REGRASP-R] :4672` = value prints, NOT dist-lines). Verified by the **npz-sha (§4)**, NOT the leg-sequence audit.
- **DS3 (F-1a) = the ONLY conditional leg-EMITTER** → declares its leaf-complete branch-set (§2.3); bounded by the ordered-multiset audit (item 2).
- **DS5 (pin) = an EVENT** → an `[PIN] event=seat@clip<k>` token.

1. **Structural tokens = STDOUT-to-run.log ONLY (CC2-MED):** each token MUST be a `print` to run.log (which `route_leg_diff` parses, `DESIGN_V1.md §0`), **NEVER a new recorder `note_*` tap** — a recorder tap shifts the stateful frame-stamping (`route_demo_recorder.py:158-191`) → npz CHANGES → breaks the CP1 "non-behavioral" guarantee. F-1a's `[W0E-F1A] guarded dx=…` (`:4243`) already IS a stdout branch-selector; St2 formalizes `[<row>] branch=<id> emits=<n>` (stdout).
2. **Primitive audit — ordered-multiset, DS3-ONLY (`DESIGN_V1.md §4.4#3`):** for DS3 assert executed leg SEQUENCE == the TAKEN branch's declared `emits_legs`, preserving **ORDER + MULTIPLICITY** (NOT set-union — `route_leg_diff.py:25` normalizes `k/N`, blind to a sub-leg-count change otherwise). This bounds DS3's conditional leg count; DS1/2/4/5 are out of its scope (they emit ∅ legs / an event, above).
3. **Pin blind-spot close needs BOTH a token AND a parser (CC4-MED):** St1a's blind spot (a moved/added grip/settle/**pin**, INV#5's sole kinematic exception, passing SAME-STRUCTURE) closes at St2 ONLY IF St2 (a) emits the `[PIN]`/grip/settle stdout tokens **AND (b) EXTENDS `route_leg_diff` (or ships a new sequence parser)** to consume non-`ik_move_both` tokens — the current tool (`LEG_RE:17`) parses dist-lines only, so the close is NOT delivered by the ordered-multiset audit as-grounded. Both (a)+(b) are part of the St2/St1b runner-instrumentation arc (Q2).

## §4 fix-⑤ / F-1a row-ification proof plan

**St2 proof = BEHAVIORAL tap-fingerprint (npz sha), NOT full-state equivalence** (`DESIGN_V1.md §3.4:129`; CC2-MED): the table-driven regeneration must reproduce R3's recorded `route_demo_raw.npz` (`route_demo_recorder.py:295` `np.savez`, path `:283-284` — the **RECORDER module, not R3**; preserving the 6-tap order — obstacle D `DESIGN_V1.md §2.2:60`). ⚠ npz-sha equality proves the **6 recorded taps** identical (a NECESSARY condition) but is BLIND to untapped state (IK residual `:4090`, contacts, non-`_sample` bodies) → "equivalence" = tap-fingerprint identity **+ the `_sample`-completeness assumption** (enumerate what `_sample` records at build; assert it covers the physical trajectory).

**Proof coverage — all 5 DS (CC2-MED, was 3/5 unproven):** §4.1 proves DS2, §4.2 proves DS3. **DS1/DS4** (value-derivations) are covered by the SAME nominal-regen npz-sha (the regen re-runs them as always-run rows; additionally assert row `GRASP_YC`==R3 `np.mean(_near)` `:3946` and row `_kR`-bow==R3 argmin `:4665`). **DS5** (pin) = detection (§3.3) + activation-equivalence (row `eq_active` timing==R3 `:4379`). No DS is left unproven.

### §4.1 fix-⑤ (notes 13/21; C1→C2 scope per D-3 — 29/37 deferred)

- **Row:** grasp-X target, `kind=cable-derived, measure=cable-region, mask=|Y−grasp_at|<0.10, reduce=mean, gate=offset(X)` (== DS2, R3 `:3984-3986`).
- **Proof:** table-driven regeneration on an X-offset scene → emitted `x_grasp` == R3's `np.mean(_cx_near)` (`:3986`), AND full npz sha == the R3 hand-authored run's sha, on ≥3 offset cells + nominal (offset=0 → gate off → byte-id).
- **The decisive charter case (`STEPTABLE_SCOPING_COORD2.md:38`):** notes 13/21/29/37 = "R-hand X=L-hand X" was already the fix-⑤ intent, demoted to a `note` string because the abs-waypoint schema had no derived-target field. St2 makes it an EXECUTABLE `cable-derived` row → **zero-new-behavior once the primitive exists**. ⚠ **This is a FIDELITY demo, not a prospective efficiency saving (CC6):** it proves St2 can re-express an ALREADY-built behavior byte-identically; the ~1.5h is sunk and nothing is saved retroactively — the saving accrues only to a FUTURE new derived source. It is the sharpest **fidelity** proof of the schema, honestly scoped.

### §4.2 F-1a (C1-seat X-follow)

- **Row:** C1_SEAT X target, `kind=cable-derived, measure=guarded-crossing, δ=cx−x_clip, transform=clamp(−(1−λ)δ,±22mm), λ=0.5, gate=offset ∧ guarded-pass`, with the **leaf-complete** CONDITIONAL branch set (§2.3): `{ initial-REJECT → nominal-fallback (comp=0, no lift, :4236); PASS-v1 → flat-comp descent (round-2 active); PASS-v2·highPASS → +lift +shift +trim (C1v2-TRIM fires :4275-4276); PASS-v2·highREJECT → +lift +shift, NO trim + comp1-MAINTAINED FLAG (:4268-4269) }`. The high-re-measure gate (`:4268`) is the NESTED sub-branch that adds/drops trim (%10 ②); PASS-v2 default-OFF-effective in round-2 per leg-diff SAME-STRUCTURE (`state.md` 08:09).
- **Proof:** regenerate the round-2 grid (81 cells) via the row → per-cell leg SEQUENCE == R3's + npz sha == RUN1_REFERENCE latest. Round-2 active = v1 flat comp, so exercise the PASS-v2 leaves **separately AND BOTH** — a high-PASS cell (asserts +trim) AND a high-REJECT cell (asserts no-trim + FLAG) — to prove the audit bounds the NESTED leaf count (%10 ②/③ linkage: the per-cell leg-seq assert binds the OBSERVED leaf, not a single PASS-v2 list; ② is the prerequisite for ③'s per-cell assert).
- **byte-id target = the LEDGER-registered RUN1_REFERENCE latest = currently `RUN1_REFERENCE_V2 5f1c3f92`, UNCHANGED** (%12 09:03): snap-down is **offset-gated** (`:3957,:3965-3966` "C-0 (0,0) byte-id UNTOUCHED") → the NOMINAL sha is unaffected and was proved EXACT at the round-2 C-0 gate, incl. post-`6808964dc3`. **Durable expression** (build-independent): target = the LEDGER-registered RUN1_REFERENCE latest; **re-verify the sha at build**; a class-B supersession of the standard is allowed ONLY via **D-7** (Rs authorizing key + same-turn `LEDGER:44`, `DESIGN_V1.md §4.2-7`).

### §4.3 What the proof CANNOT automate (`DESIGN_V1.md §4.4` ⚠ + finding 15)

leg-diff + sha guard STRUCTURE + nominal-drift ONLY. A coordinate-QUALITY regression (F-3-class) passes both gates yet is counterproductive (`LEDGER:44`). So the **video + Rs leg stays LOAD-BEARING** for St2 row-ification acceptance — not automatable-away. Conservatism direction: the mechanical gates are CONSERVATIVE for structure/nominal-drift, NON-conservative for motion quality → the quality axis needs the human leg.

## §5 Build sequencing + gates (NOT this turn — deferred)

1. **Order (UPDATED %12 09:57):** the **φ10-collision constraint is RESOLVED** — Rs "A" closed W0-e; **no other arc will edit the locked runner**, so the St2 runner-edit no longer waits on φ10/DC-1. The build gate is otherwise UNCHANGED and now stands alone: **spec chain complete → Rs packet → Rs build-auth → L3 + byte-id re-proof.** (%12 sequencing confirm is no longer φ10-gated; CC still pings %12 before touching R3.)
2. **Re-base (§0):** re-verify every §2 R3 cite against the then-current committed runner — **incl. the cites NOT re-read in the %10 pass (LOW): DS4 air-grip-bug `:4633-4635` + DS5 pin `:1384-1399`/`:4345-4357` → spot-check at re-base.**
3. **Gates:** L3 + Rs explicit auth + byte-id/behavioral re-proof (`DESIGN_V1.md §3.3:110`, §6:203). **Kickoff approval ≠ per-edit authorization** (%12 08:46).
4. **Chain:** this spec → %10 author-review → 5体 L3 debate → Rs.

## §6 DoD (build-time acceptance)

- fix-⑤-as-row (notes 13/21) regenerates byte/behavior-identical (`DESIGN_V1.md §5` DoD(+)).
- F-1a-as-row regenerates the round-2 grid identical (per-cell leg-seq + npz sha).
- Conditional-branch primitive audit (§2.3/§3) catches an INJECTED extra/dropped leg — regression test per `AGENTS.md` ("verify the test fails without the fix": revert audit → injected leg passes; re-apply → caught).
- pin blind-spot (St1a `§4.4` ⚠) closes: a moved pin is DETECTED under St2 instrumentation.

## §7 Open questions (Rs / %12 / build-time)

- **Q1 (RESOLVED — %12 09:03):** byte-id target = `RUN1_REFERENCE_V2 5f1c3f92`, UNCHANGED (snap-down offset-gated → nominal EXACT, round-2 C-0 gate, post-`6808964dc3`). Durable expression = LEDGER-registered RUN1_REFERENCE latest + build-time sha re-verify + D-7 supersession (§4.2). — no longer open.
- **Q2 (STAGING — ✅ Rs DECIDED = B, 2026-07-06 `b7d7857dfc`):** DESIGN_V1 (Rs-approved) staged St1b BEFORE St2; St2's runner instrumentation (§3) OVERLAPS St1b's all-primitive tokens (`DESIGN_V1.md §4.4#1`). The two options considered (Rs chose **B**):

  | axis | **A. keep St1b→St2 separate** (DESIGN_V1 as-approved) | **B. St2 ABSORBS St1b** (single arc) |
  |---|---|---|
  | locked-runner edits | 2 (St1b tokens, then St2 derived) | **1** (combined instrumentation + derived rows) |
  | byte-id re-proof | 2× | **1×** |
  | St1b standalone trigger | none identified (no proven un-env-routable literal, `DESIGN_V1.md §3.3`) | n/a (folded) |
  | L3 + Rs-auth cycles | 2 | **1** |
  | DESIGN_V1 staging fidelity | **matches approved order** | staging CHANGE → needs Rs re-approval |
  | per-edit risk | more gates, smaller diffs each | one larger diff; avoids duplicate instrumentation |
  | **bisectability** (sha-mismatch localization, %10 ④) | **easier** (per-arc diff isolates the failure) | harder (combined diff) → mitigated by the 2-checkpoint proof below |

  **✅ Rs DECIDED = B (absorb)** (2026-07-06 Q2, `b7d7857dfc`): St2 ABSORBS St1b into a **single runner-edit arc** with the 2-checkpoint bisectability guard (CP1/CP2 above). Rationale: no standalone St1b trigger + identical runner instrumentation + single byte-id re-proof (%12 09:03). **A (separate staging) = REJECTED.** The DESIGN_V1 St1b→St2 order is **superseded** by this single-arc staging (Rs-authorized change).

  **⚠ Option-B bisectability mitigation (%10 ④):** even in a single arc, split the byte-id proof into **2 checkpoints** — (CP1) **instrumentation-only** (the print/parse tokens §3, which are NON-behavioral) proves the nominal sha UNCHANGED first; (CP2) the derived-row-ification is proved SEPARATELY. A sha mismatch then localizes to CP1 (instrumentation leaked into behavior) vs CP2 (a derived row diverged) — restoring bisectability WITHIN the 1-arc, without reverting to 2 runner edits.
- **Q3:** branch-set authoring authority = Rs 専権 (§2.3); teaching edits derivation params only. — confirm.
- **Q4:** full-5-clip fix-⑤ (notes 29/37) — deferred to D-3 (separate validation).
- **Q5 (✅ Rs DECIDED = 閉鎖, 2026-07-06 `b7d7857dfc`):** Rs authorized adding the `C2_TILT_SIGN=0` inv_binding to DESIGN_V1 §3.1's C2_REGRASP `orientation` row — **executed 2026-07-06** (cite = runner `:4678-4681` ANTI-REVERT block). The teachable 先祖返り (a teaching setting the C2_REGRASP arm to tilt-follow, breaking the `:4678` Rs-LOCK) is now locked: such a teaching → `BLOCKED_FOR_USER`. DESIGN_V1 §3.1 orientation row now carries the matching inv_binding.

## §8 Changelog

- **v0.1 (2026-07-06 08:55, VT-DESIGN/p5):** initial draft. Baseline `6808964dc3` (verified clean; re-base-at-arc-close noted). Covers %12's 4 deliverables (schema §2 / row-ification proof §4 / emits_legs §2.3 / primitive audit §3).
- **v0.1a (2026-07-06 09:0x, self-review before %10):** DS4 cite corrected (`:4295/4318/4326` = F-1a-internal argmins → true C2 re-grasp = `_kR :4665`, phase `:4675`); **surfaced DS4 Rs-LOCK** (`:4662` anti-revert → `inv_binding = actual-cable-argmin`); added DS3 C2-analog (`:4840` `_c2x_comp`). → %10 author-review → 5体.
- **v0.1b (2026-07-06 09:03, %12 Q1/Q2 fold):** **Q1 RESOLVED** — byte-id target = `RUN1_REFERENCE_V2 5f1c3f92` UNCHANGED (snap-down offset-gated → nominal EXACT; §4.2 over-caution corrected; durable expression + D-7). **Q2 reframed** — both-options tradeoff table (A separate / B absorb), Rs decision item, %12 lean=B noted, NOT pre-decided. → %10 author-review (v0.1b).
- **v0.2 (2026-07-06 09:17, %10 author-review fold — CONCUR / 1 MEDIUM, no blocking):** **② F-1a branch-completeness → RECURSIVE** (high-re-measure trim sub-branch `:4268` → PASS-v2 split highPASS/highREJECT; §2.3 leaf-complete principle + §4.2 assert-propagation, exercise BOTH high-leaves); **④ Q2 bisectability** cost row + Option-B **2-checkpoint** proof (CP1 instrumentation-only nominal-sha → CP2 derived-row); **LOW** (DS2 range→`:3983-3986` load-bearing; DS4/DS5 build-time spot-check §5). → **5体 L3 debate (CC1 = p5, %12 09:17)**; PROPOSE KNOWN_ALTERNATIVES = both A/B.
- **v0.3 (2026-07-06 09:3x, 5体 L3 DECIDE=FAIL fold — %12 verify PASS 09:39):** **Group A (safety):** #1 **two-mechanism byte-id taxonomy** (DS1/DS4 always-run DETERMINISM ≠ offset-gate — the build-breaker); #2 **DS4 2nd Rs-LOCK** (orientation `C2_TILT_SIGN=0 :4678`) + DESIGN_V1 §3.1 governance-escalation; #3 per-DS **Rs-LOCK-field IMMUTABLE carve-out** (reduce/target/orientation — the "pin-to-constant" tripwire was the wrong predicate); #12 **F-3 echo REMOVED** (`:4840` = withdrawn deviation, excluded from reproduced set). **Group B:** #4 §3 reframe (DS1/2/4=∅ legs = value-derivations, audit = DS3-only), #5 pin-close needs a parser, #6 equivalence→tap-fingerprint, #7 CP1 stdout-only, #8 all-5-DS proof coverage, #9 audit≠authorship, #10 DS5 mandatory binding. **Group C:** #11 savez=recorder-module, #13 DS5 flag∧clip-seat, #14 DS4 config, #15/#16 ranges. **Group D (NHA honesty):** ROI-for-future-non-reuse + efficiency→fidelity temper + build-defer. → targeted re-verify → %12 verify → Rs packet.
- **v0.3a (2026-07-06 09:5x, RV re-verify fold — fixes ADEQUATE, 2 MED + 3 LOW):** RV confirmed the 3 HIGH + F-3 fixes ADEQUATE/code-correct, no new HIGH. Folded: **NEW-1 F-3 flag is default-ON** (`:4845`="1" — I'd wrongly written default-OFF from a relayed value; §4.2 `W0E_F3=0` guard is thus LOAD-BEARING, not cosmetic); **NEW-2 re-grounded the determinism premise** (`:355-356`=video-init NOT seed; real basis = RNG-free route + fixed config + IK warm-start seeds `:2819/:3060/:3254` + fixed settle); **NEW-3** DS4 always-run scoped to canonical dualseat config (`:4624-4626` both default 0); **NEW-4** `:3946` else-cite; **NEW-5** §7 Q5 orientation-escalation elevated to an explicit Rs item. + **%12 09:57 sequencing:** φ10-collision constraint RESOLVED (build gate = spec-chain→Rs-packet→Rs-auth→L3+byte-id, standalone). → **PASS**.
- **v0.4 (2026-07-06 10:27, ✅ Rs-APPROVED — `b7d7857dfc`):** Rs 3-decision fold: (a) **design APPROVED**; (b) **Q2 = B** (St2 absorbs St1b, single arc + 2-checkpoint bisectability) — A rejected, DESIGN_V1 St1b→St2 order superseded; (c) **Q5 = 閉鎖** — `C2_TILT_SIGN=0` inv_binding ADDED to DESIGN_V1 §3.1's C2_REGRASP orientation row (executed, cite runner `:4678-4681`). **BUILD remains deferred + Rs-gated** (the single St2-absorbs-St1b arc → Rs build-auth → L3 + byte-id re-proof, on a genuine new-source trigger per §1 NHA scope). VT node → DESIGN+STAGING-APPROVED.

*VT-DESIGN (w2:p5) — St2 build spec v0.4 (✅ Rs-APPROVED), paper-only, grounded @`6808964dc3`.*
