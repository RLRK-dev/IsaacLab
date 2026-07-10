---
title: Gripper V-Groove Design (R-S7.1) — DECIDED / FIXED
created: '2026-06-19'
owner: human-Rs (design decision); RS-TECH-LEAD (%5) records
status: ⛔ DISCARDED as a design reference (human 2026-06-21) — active finger = コ (06-Knowledge/GD-KoShape-Finger.md); the V-groove ◇ is NO LONGER a retained/locked reference. ⚠ records-ahead-of-code: committed asset 2f85_tendon_stripped.xml (7afa84b463) still physically contains the ◇ + コ is unwired scratch → ◇→コ asset swap = deferred L3. This doc = HISTORICAL record only (◇ geometry table preserved for the deferred swap + GD-S2A lineage). [prior: 🔁 SUPERSEDED→コ 2026-06-20 (◇-retained-reference); earlier ACTIVE 🟢 2026-06-19 100% MANDATORY]
status_ledger: 07-Design/00-DESIGN-STATUS-LEDGER.md
authoritative: true
tags: [design, gripper, v-groove, R-S7.1, FIXED]
---

# Gripper V-Groove Design (R-S7.1) — DECIDED / FIXED

> ## ⚠ SUPERSEDED 2026-06-20 — THE FINGER SHAPE IS NOW コ (read FIRST)
> **Human decision 2026-06-20:** the gripper finger is **コ-shape (C-bracket)**, which **REMOVES this V-groove ◇ as the active finger shape.** The コ design + the demonstrated building blocks (grasp / lift ~45mm / mid-air re-grasp / place) are recorded in **`06-Knowledge/GD-KoShape-Finger.md`**. This V-groove doc is **retained only as a HISTORICAL record** — the ◇ is **DISCARDED as a design reference** (human 2026-06-21, NOT retained/locked; the geometry table is kept only for the deferred ◇→コ asset swap + GD-S2A lineage).
> **Status:** コ = the ACTIVE finger, **BANKED 2026-06-21 (Rs source-GO)** as a CPU-verified building-block (penetration/retention/grip-down clamp 0.69, %2 cross-PV CONVERGENT; 2026-06-17 5体 crush CRITICAL retired); **GPU R-S6.6 + full-route/snag retention + R2/R3 §運用14 = PRODUCTION-pending** (same caveat as banked-(A)). The V-groove body below is **SUPERSEDED + DISCARDED as a design reference** (human 2026-06-21) — the ◇ geometry is NOT retained/locked as a reference (⚠ committed asset still ◇, swap deferred L3). Do NOT treat the V-groove body as the active finger shape.
> **Provenance:** added 2026-06-21 (%9 RS-TECH-LEAD) under the human GO + standing directive 「確定事項は設計書に即反映・vault内で整合性を常に保て」. Corrects the prior **stale-spec divergence** — each コ building-block was 「vaultに記録」'd, but those records went only to the `GD-KoShape` working doc (06-Knowledge = the only dir CC may write) while THIS authoritative spec (07-Design = human-only) kept reading "V-groove FIXED" (the same stale-spec trap as the 2026-06-21 V-vs-コ confusion).

> ## ⚠ Dated staleness + value pointer (renewal batch A, 2026-07-11)
> **(a) internal asset-status claims are pre-swap stale:** the frontmatter/banner statements "committed asset 2f85_tendon_stripped.xml (`7afa84b463`) still physically contains the ◇ / コ is unwired scratch / ◇→コ asset swap = deferred L3" are **pre-swap (stale)**. Current state per LEDGER `00-DESIGN-STATUS-LEDGER.md:57`: **◇→コ asset swap COMMITTED `85315bbec6` (2026-06-23)** — committed asset is now コ, records-vs-code CONSISTENT. Read the body's swap-deferred wording as historical.
> **(b) HALF_OPEN_RAD value pointer (4b=A residual, reference-over-copy):** the §3 body line "`GRIPPER_DRIVER_HALF_OPEN_RAD` ≈ 0.667 (PROPOSED, NOT yet landed)" is the **pre-landing historical value**. **Current SSOT value = `task_config.py:313` `GRIPPER_DRIVER_HALF_OPEN_RAD` = 0.69** (half-clamp GUIDANCE; human-confirmed 2026-06-21, LANDED; serves the active コ finger — LEDGER `:57`/`:58`). An origin-unknown working-tree edit updating the body line 0.667→0.69 was reverted to Rs-governance state 2026-07-11 (value preserved here as a pointer, not copied into this DISCARDED doc).

**FIXED DECISION (human-Rs directive, repeated + final, 2026-06-19): the gripper finger is V-GROOVE-shaped. 100% mandatory.** ⚠ **SUPERSEDED→コ, banked 2026-06-21 (Rs source-GO) — see the top banner. This V-GROOVE mandate is now HISTORICAL; the ACTIVE finger is コ (`06-Knowledge/GD-KoShape-Finger.md`); the ◇ geometry survives only as the up-cap/drag reference.**
This was a locked design decision (now superseded→コ). Do NOT re-litigate the OLD flat/V-cage debate (settled); the V-groove→コ supersede is the human's 2026-06-20 decision, banked 2026-06-21.

## 🔒 LOCKED FINGER SPEC — SINGLE SSOT (human-FROZEN 2026-06-19; do NOT change)
**Human directive 2026-06-19: 「この図の仕様が確定事項である。ここから変更させないこと」** — the finger spec is FROZEN to the figure below. ⚠ **SUPERSEDED→コ banked 2026-06-21 (see top banner): the ACTIVE-finger SSOT is now `06-Knowledge/GD-KoShape-Finger.md`; THIS doc = the ◇ up-cap/drag GEOMETRY reference (the ◇ geometry remains human-LOCKED — no change without source-GO).** (Pre-supersede this doc was the single SSOT for the gripper finger; all panes conformed.)

**Authoritative cross-section:** `eval_runs/troot_optE_rs71_kinematic_retention_20260616/R_S71_DIAMOND_LOCKED_SPEC.png` (= %2's `r_s71_diamond_pv_centered.png`, PV on the REAL committed ◇ — `R_S71_DIAMOND_PV_02_VERDICT.md:4`). Complete DIAMOND ◇: green `vgu` (upper) cap the cable top + blue `vgl` (lower) cradle the lower sides DOWN to the table (z=0.800); cable Ø8 centered (~z0.806, cradled ~2mm); S1 cage (purple) flanks laterally on the outer sides.

### 1. ◇ V-groove geometry — LOCKED (asset `2f85_tendon_stripped.xml`, committed `7afa84b463`; these values ARE the locked record)
4 collidable box geoms (contype8 / condim6), full size 15(along cable)×10×1mm, +1mm tangent clearance to Ø8:

| geom | size | pos | quat |
|---|---|---|---|
| right_pad_vgu (upper) | 0.0075 0.00500 0.0005 | 0 -0.0056 0.0362 | 0.0522 0.9986 0 0 |
| right_pad_vgl (lower) | 0.0075 0.00458 0.0005 | 0 -0.0002 0.0402 | 0.7431 0.6692 0 0 |
| left_pad_vgu (upper)  | 0.0075 0.00500 0.0005 | 0 -0.0087 0.0407 | 0 0 0.0482 0.9988 |
| left_pad_vgl (lower)  | 0.0075 0.00458 0.0005 | 0 -0.0033 0.0448 | 0 0 0.7404 0.6722 |

The two pads (right ">" + left "<") close at half-clamp into the 4-wall ◇ enclosing the cable's full circumference.

### 2. S1 form-closure cage — committed `65c056f63a`
`f1up / f1lo / f1ext / lip` per pad (lateral flanks; assists centering — %2 cross-PV: cage-dominant for static centering).

### 3. Clamp params (numeric SSOT = `task_config.py`)
- `GRIP_HALF_SPAN` 0.044 (arm-to-arm 88mm; `WIDE_LEFT_Y` 0.106 / `WIDE_RIGHT_Y` 0.194) [:235/:262-263]
- `FINGER_OPEN_POS` 0.04 / `FINGER_HALF_OPEN_POS` 0.006 / `FINGER_CLOSE_POS` 0.002 [:268-271]
- `GRIPPER_DRIVER_CLOSE_RAD` 0.7407 (full-clamp = INSERTION) [:285]
- `GRIPPER_DRIVER_HALF_OPEN_RAD` ≈ 0.667 (half-clamp = ◇ form / GUIDANCE) — **PROPOSED, NOT yet landed**
- `GROOVE_CENTER_Z` 0.809 / `EE_TO_PINCH_CLOSED` 0.25484 / `EE_TO_PINCH_TIP_CLOSED` 0.27517 [:226/:302-303]

### 4. Faithful 1-DOF coupling — REQUIRED for grip (NOT yet landed; `R_S71_FAITHFUL_SLOT_15`)
The asset's tendon/equality 4-bar is stripped → rebuilt in code, which FLOPS without these (R_S71_CLAMP_JOINTTRACE_11). For a real rigid 1-DOF grip:
- STIFFEN the 4 connect equalities: `solref` → [0.001, 1] + `solimp` rigid.
- RESTORE the L-R follower MIRROR eq (j23=j27, j9=j13, polycoef [0,1,0,0,0]) = the asset's dropped `<joint>` coupling.
- → `neq` 4 → 6 (the `test_newton_clip_routing.py:1237` neq==4 guard must be updated 4→6 at landing).

### 5. Roles (SSOT = `SOMA.md:80`) — **full-clamp = clip INSERTION / half-clamp = next-clip GUIDANCE.**

### 6. Pipeline context (`SOMA.md:31`) — Grasp → **Lift 50mm** → Route → Hook = **AERIAL** (on-table guide collides with table-mounted clips). Grasp+lift needs a **TABLE-SPACE slot** under the cable so the lower walls reach under (`R_S71_TABLE_SPACE_14` / `R_S71_FAITHFUL_SLOT_15`; multi-box table build = separate land).

**LOCK: §1-2 geometry + the figure are FROZEN. §3-4 are the required clamp/coupling. No pane changes the ◇ without human source-GO.**


## Spec
- A **V-groove (∨ pocket / channel)** on the gripper pad faces.
- **mouth < Ø8 mm** (cable diameter = 8 mm) so the groove **CAPS the top** → the cable cannot escape upward.
- **Real collidable** geom (NOT VISIBLE-only), grafted onto the gripper asset (`2f85_tendon_stripped.xml`) the same way the
  S1 cage was grafted (git `65c056f63a`).
- Contact = real physics (the only kinematic exception in the system is the authorized clip-pin, `log.md:6534`).

## Two roles (both required)
1. **full-clamp → CLIP INSERTION.** During the downward insertion press the V-groove caps the top → the cable cannot
   escape UP → the press force **TRANSMITS into the clip**. (A flat / tilted face lets the cable squirt up → no force into
   the clip → insertion FAILS.)
2. **half-clamp → GUIDANCE to the next clip.** The V-channel cradles the cable laterally → it can guide/carry the cable to
   the next clip. This **rescues** what the flat half-clamp could NOT do (the flat half-clamp `FINGER_HALF_OPEN_POS=0.006`
   = 6 mm < Ø8 pinches → the dead "しごき/slide", `task_config.py:252`).

## Why (rationale, grounded)
- The committed flat/tilted 2F-85 gripper **cannot grasp the flush cable** (D3a/b/c + Q3: silicone faces ~45° inverted-V
  wedge the Ø8 cable out; `log.md` Q3 entry).
- On-table **DRAG is forgiving** (the table supports the cable from below) — even a narrow flat pusher holds a floppy cable
  (%4 V-notch probe → V-notch NOT needed for drag; COORD2 AUDIT-PASS, `R_S71_VNOTCH_AUDIT_03.md`).
- **BUT clip INSERTION needs the cable held against UP-escape during the press** → a V-groove is the mechanism → MANDATORY.

## Related / dependencies (separate, tracked elsewhere)
- **Cable → made FLOPPY — LANDED 2026-06-19: `CABLE_BEND_STIFFNESS` = 0.005** (`task_config.py:144`; human VISUAL
  pick from the drape render, %3 AUDIT-PASS, was 1.0 = rigid rod). Power-cable-like, inside the realistic Ø8 EI
  window 1e-3..5e-2 (`06-Knowledge/Cable-Bending-Stiffness-EI-8mm.md`); 45mm drape / 200mm overhang. UNITS
  (corrected — the earlier note had it inverted): `CABLE_BEND_STIFFNESS` **IS EI [N·m²]** (build:809/827), NOT a
  joint stiffness; the active mujoco joint hinge stiffness = EI/L_seg = 0.333. The
  `estimators/cable_state_cosserat.py` `_NOMINAL_BEND_EI` mirror is a SEPARATE env6/RL track — NOT synced here (audit F-A).
- **Clip insertion press-in fidelity = RESOLVED (human 2026-06-19): the clip uses the authorized kinematic PIN ONLY** (clip-only trick; NOT a real compliant-clip press-in). → the V-groove press **SEATS** the cable into the clip; the **kinematic pin RETAINS** it. Consequence: max clip-pressure is **not physics-critical** → the hand spacing (`GRIP_HALF_SPAN`) is narrowed **"as narrow as reasonable"** for seating pressure, **NOT rigorously min-derived** (per human 「厳密に間隔を割り出さなくて良い。なるべく狭くで良い」). **LANDED 2026-06-19: `GRIP_HALF_SPAN` = 0.044** (`task_config.py:228`; arm-to-arm 120→92mm; COORD2 AUDIT-PASS + %5 MERGE, `R_S71_GRIPSPAN_AUDIT_03.md`). The prior 0.028 was UNREACHABLE in production — the dual-arm collision-avoidance IK objective (EE-EE safety spheres 35+35mm +10mm margin, `COLLISION_WEIGHT`=5.0, `newton_routing_utils` `COLLISION_SPHERE_RADII`) floors achieved arm-sep at ~80.5mm (collision-OFF reaches 0.028 exactly → by-design, NOT under-convergence [ik_move_both = ONE solve_ik_dual @ IK_ITERATIONS=100] nor a real pad collision [pads clear 34mm @28mm]). 0.044 = narrowest span passing the production 5mm/EE `moves_ok` gate (shortfall 2.21mm, margin 2.79mm; 0.040 = fragile gate-edge 4.22mm). The collision-sphere reduction that would reach full 0.028 (an IK-level `newton_routing_utils.py` change that also guards the forearms mid-trajectory → separate GO + full-trajectory re-verify) was **DECLINED** = exactly the rigorous min-derivation the human waived, benefit non-critical (pin retains).
- **GD-S2A** (aerial cage, `06-Knowledge/GD-S2A-ControlledDelivery.md`) = **PARKED** (the V-groove on-table path supersedes
  it for the current basic-SIM bar; GD-S2A is the path back to the 95% ULTIMATE goal, not discarded).

## COMPLETE DIAMOND ◇ — FINAL (verified + landed 2026-06-19)
**The V-groove evolved (human-directed, repeated) into a COMPLETE 4-WALL DIAMOND ◇** (concept
`~/Downloads/r_s71_vgroove_diamond_concept.png`, human-confirmed 「この図でよい」「これでいい」). Earlier PARTIAL
builds (top-cap-only "roof"; then a table-reaching CHANNEL that dropped the top cap) were REJECTED by the human
(「ひし形が形成されていない」「これ以外はNG」) — lesson `feedback-hold-complete-target-shape-across-refinements`.

**Geometry (asset `2f85_tendon_stripped.xml`, 4 geoms):** each pad presents a V — `vgu`=UPPER flank + `vgl`=LOWER
flank; the two pads (right ">" + left "<") close at HALF clamp into a diamond enclosing the Ø8 cable's FULL
circumference. Each geom full size 15(along cable)×10×1mm, +1mm tangent clearance. TOP vertex caps up-escape;
BOTTOM vertices reach the table (z=0.80). All 4 collidable (contype8 condim6, behavioral ncon>0). LOCKED params
untouched (`GRIP_HALF_SPAN` 0.044 / `CABLE_BEND_STIFFNESS` 0.005 / `FINGER_*`).

**Inherent cradle (geometric necessity, human-accepted Option A):** a tangent ◇ circumscribing Ø8 has its centroid
~2mm ABOVE an on-table cable center → the ◇ holds the cable cradled ~2mm off the table. "Full-circumference tangent
◇" and "cable rests on the table" are geometrically incompatible by ~2mm (audit analytic bracket [tangent 1.66 ↔
+1mm-clear 3.07]mm). The human accepted the cradle (the prior no-lift ≤0.6mm rule is overridden for this ◇).

**⚠ CONTRADICTED 2026-06-20 (records-must-match-fact; %9 RS-TECH-LEAD records; do NOT re-adopt the "half-clamp ◇ = load-bearing" claim below for the aerial LIFT):** the ◇ FORMS (encloses, no lift) XOR LIFTS (◇-below, doesn't enclose) — mutually exclusive via the OPEN BOTTOM; depth AND clamp tuning are EXHAUSTED (`RS71-System-Spec-SSOT.md:37` §3 + `r_s71_depth_sweep_cablerise_38` + `r_s71_depth_clamp_sweep_39` [HALF≈FULL at every depth], %2-verified). The full-clamp "symmetric lift" was an EMPTY-gripper artifact + the V-groove was NOT clamping the cable (mid-finger flat pinch, human-verified video `r_s71_arm_physfinger.mp4`). The "carry 0.90" below is HORIZONTAL drag-retention + up-cap ONLY — NOT the aerial vertical lift. RESOLUTION = the OPEN FORM-vs-LIFT design fork (escalated to human, `RS71-System-Spec-SSOT.md:37`); the ◇ geometry stays human-LOCKED pending that call. [2026-06-20 17:56 JST]

**Verified 2026-06-19 (CPU, half clamp = load-bearing) — 3 independent angles [⚠ SUPERSEDED for the LIFT claim — see the CONTRADICTED caveat above; valid only for up-cap + horizontal drag-retention]:**
- **%5 §運用14 (shape):** the complete ◇ FORMS — all 4 walls, top vertex caps, bottom at table, tangent (render
  `~/Downloads/r_s71_diamond_real.png`, DIAMOND_FORMS=True / no_crush=True).
- **%3 static-geometry audit (PASS):** 4 walls tangent surf_clear ≥0 (RU+1.17 / RL+0.03 / LU+1.22 / LL+0.02 mm),
  cradle +2.01mm inherent, LOCKED intact, diff = 4 geom lines (`R_S71_DIAMOND_AUDIT_03.md`).
- **%2 dynamic cross-PV (CONCUR-WITH-REFINEMENTS):** up-escape **0.0mm** (fixes the prior channel's 0.7mm), carry
  **0.90** drag-retention (cable held 3.9–6.2mm above the table THROUGH the drag = ◇-held, not table-dragged);
  centering −3.0→+2.0mm (contact-driven; vgl contacts confirmed) (`R_S71_DIAMOND_PV_02_VERDICT.md`).

**SCOPE / conservatism (records-match-fact):**
- The ◇ carries the **up-cap + drag-retention/guidance** (= the human's 「半クランプで保持・誘導」). The **initial
  static centering is CAGE-ASSISTED** (the retained S1 cage does most of it; do NOT over-credit the ◇ for static
  centering) — %2 R1.
- **CPU-validated only** (current basic-operation bar). GPU production transfer NOT claimed (GPU mjw non-det NaN =
  separate R-S6.6 blocker) — %2 R3.
- **Production choreography** (descend height + `GRIPPER_DRIVER_HALF_OPEN_RAD` to use the ◇ in the grasp sequence)
  = a SEPARATE follow-up [CHANGE] (R-S6.1), NOT in this asset land.

**Status: COMPLETE DIAMOND ◇ asset LANDED 2026-06-19** (human GO; %5 §運用14 + %3 audit + %2 cross-PV all PASS).

## Status / build (cap-from-above design — SUPERSEDED by the COMPLETE DIAMOND ◇ above)
- **Build DONE → COORD2 (%3) AUDIT-PASS → RS-TECH-LEAD (%5) MERGE=GO (2026-06-19)** — geometry+collidability faithful (4 collidable ∨ geoms, mouth 6.44mm<8mm caps the cable, same method as the S1 cage); **dynamic roles (capture/insert/guide) = deferred gated test** (the dynamic-efficacy doubt that walled the prior V-cage 5体 is DEFERRED, NOT settled; 5体 pre-debate waived per the human source-GO); audit notes: cable PERCHES on the mouth lips (capped+cradled, not seated inside), `_tmp_*.xml`=stale scratch, close-jam covered by the right_pad↔left_pad exclude (:184); ⚠ `EE_TO_PINCH_TIP_CLOSED` shift (∨ protrudes 3.69mm) FLAGGED → downstream R-S6.1 re-derive (`task_config.py:296`). Originally dispatched to COORD (%4) 2026-06-19: graft the V-groove onto the gripper pads + rule-check stage2 + build/geometry
  verification (compiles, mouth < 8 mm, the 8 mm cable nests in the ∨, real collidable). 0-GPU.
- gripper-geom = source-level [CHANGE]; **source-GO = the human V-groove directive**.

## Provenance
- Human directive 2026-06-19 (repeated + final: 「V字こう状にしろ」「V字こう状のものは100％必須」「半クランプでケーブルを次のクリップに誘導」「テーブルにフィンガ先端がくいこめる空間」).
- `docs/logical_decomposition.html` 2026-06-19 ~01:33 CURRENT FRAME.
- `thread-vault/log.md` 2026-06-19 entry.
