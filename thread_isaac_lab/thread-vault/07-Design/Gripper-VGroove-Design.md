---
title: Gripper V-Groove Design (R-S7.1) — DECIDED / FIXED
created: '2026-06-19'
owner: human-Rs (design decision); RS-TECH-LEAD (%5) records
status: ACTIVE (🟢) — human-DECIDED 2026-06-19, 100% MANDATORY
status_ledger: 07-Design/00-DESIGN-STATUS-LEDGER.md
authoritative: true
tags: [design, gripper, v-groove, R-S7.1, FIXED]
---

# Gripper V-Groove Design (R-S7.1) — DECIDED / FIXED

**FIXED DECISION (human-Rs directive, repeated + final, 2026-06-19): the gripper finger is V-GROOVE-shaped. 100% mandatory.**
This is a locked design decision, not a proposal. Do NOT re-litigate (flat / V-cage / "is V-groove needed" were already settled).

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

**Verified 2026-06-19 (CPU, half clamp = load-bearing) — 3 independent angles:**
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
