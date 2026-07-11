---
doc_class: design-surface
node: T-ROOT-optE-route-dapg-C1C2-P2-routeexec
component: comp5 (real C2 groove scene)
author: "%11 COORD (w2:p3)"
date: 2026-07-11
gate: DESIGN-GATE (/geometric-design + /reward-design) — pre-5体-[VERIFY]
---

# comp5 — real C2 groove scene: DESIGN-GATE (geometric + reward)

**Charter:** comp3 remaining DoD (Rs GO 06:29, node `994b2923c2`). comp5 = shared prerequisite for
⑥ full-fire / ⑨b numerator / C2-seating video (%12 CONCUR+ratify 06:45 `a72b697c6b`: charter-internal
dependency, NOT new scope — DoD⑥ "実 C2 groove scene" requires it).

## §0. Grounding (anchor set, §運用4)
- LEDGER route-executor row VL7 🟢 ACTIVE (`00-DESIGN-STATUS-LEDGER.md:128`).
- node `goal_verification:5-16` fresh-read (§運用16): DoD⑥ "C2-seating 動画 gate (実 C2 groove scene)";
  ⑤ EXACT wall/spacer predicate; ⑨b strict_v2 C2-seat leg conjoin (§運用29).
- Layer-B plan v0.2.2 §2 row 5 + §9: "real C2 groove scene (additive flag-gated, over-solid), Stage-B,
  /geometric-design"; Q2 pre-resolved = C2 even clip X=0.40 SOLID floor (no void).
- Reuse template: `newton_skill_env_base.py:1814-1840` (C1 `add_target_clip` block).
- C2-seat predicate: `newton_route_env.py:1230-1237` (`_c2_seated_honest`).
- Constants: `route_env_config.py:130` ROUTE_C2_XY=(0.40,0.000) / `:131` ROUTE_CLIP_FLOAT_Z=0.020 /
  `:134` ROUTE_GROOVE_Z=0.829 / `:113` C2_SETTLE_Z_TOL_MM=3.0 / `:114` C2_WALL_SEAT_TOL_MM=0.5;
  `task_config.py:20` TABLE_HEIGHT=0.80 / `:91` CLIP_BASE_HEIGHT=0.005 / `:137` CABLE_RADIUS=0.004 /
  `:226` GROOVE_CENTER_Z=0.809 / `:368` T_GROOVE=0.003.

## §1. [TASK] / [L-TRIAGE] = L3
Env scene/geometry change (`newton_route_env.py` core + `newton_skill_env_base.py` scene builder) +
env keyword. L3. Invariant-PRESERVING (additive geometry, flag-gated default-off; no arm/gripper/span/
control change → §0 FOUNDATIONAL INVARIANT untouched, high-care L3 NOT immediate-STOP). 5体 [VERIFY]
= %12 as CC1 (06:45).

## §2. /geometric-design (6-step)

### Step 0 — Interrogate (bounded, one pass)
Necessary? YES — DoD⑥ + ⑨b C2-seat leg (⑤ EXACT predicate does mjModel geom introspection → requires
physical C2 clip). Reuse? the C1 `add_target_clip` block IS the template (C2 = parametric mirror; no new
geometry class). Downstream risk? additive + flag-gated → OFF=byte-preserve; no rev-chain.

### Step 1 — Measure (actual values)
| Quantity | Value | Source |
|---|---|---|
| TABLE_HEIGHT | 0.800 | task_config.py:20 |
| CLIP_BASE_HEIGHT | 0.005 | task_config.py:91 |
| CABLE_RADIUS | 0.004 | task_config.py:137 |
| GROOVE_CENTER_Z (base) | 0.809 | task_config.py:226 |
| ROUTE_CLIP_FLOAT_Z | 0.020 | route_env_config.py:131 (routing clips, SPACER-supported) |
| ROUTE_GROOVE_Z (target) | 0.829 | route_env_config.py:134 |
| ROUTE_C1_XY | (0.35, 0.150) | route_env_config.py:129 |
| ROUTE_C2_XY | (0.40, 0.000) | route_env_config.py:130 (Rs 07-05) |
| C1 clip_parts (template) | base(hx.020,hy.015,hz.0025) + 2 walls(±.009,hx.0015,hz.0075) + 2 lips(±.013,hx.002,hz.005) | newton_skill_env_base.py:1820-1826 |

Derived C2 z-spans (float base 0.820): base 0.820-0.825 / walls 0.825-0.840 / lips 0.840-0.850;
groove opening ≈ 0.829 (= ROUTE_GROOVE_Z); groove inner width 15mm (walls inner faces ±0.0075) vs
cable ⌀8mm → fits.

### Step 2 — Constraints
- Hard: H1 groove z = ROUTE_GROOVE_Z 0.829 (predicate satisfiable); H2 flag-OFF byte-identity
  (env-core preserved); H3 no collision (C2@X0.40 vs support-clips@GRASP_X0.30, vs C1@0.35/Y0.150 —
  clear); H4 additive-only (no removal/edit of existing geom).
- Soft: S1 mirror C1 exactly (minimal LOC, reuse); S2 C2 clip_parts base-first order so the ⑤ EXACT
  spacer-excluded predicate can identify/exclude the base plate (⑨b-gate downstream).

### Step 3 — Cross-section (C2 mirrors C1, mm)
```
Z[mm]   C1 (X0.35,Y0.150)            C2 comp5 (X0.40,Y0.000) [additive mirror]
 850   ┌lip┐     ┌lip┐               ┌lip┐     ┌lip┐         lips  840-850
 840   ├──┤groove├──┤                ├──┤groove├──┤          walls 825-840
 829 ··│wl│═⌀8═│wl│················· │wl│═⌀8═│wl│·········   ROUTE_GROOVE_Z 829 (seat)
 825   └──┴────┴──┘                  └──┴────┴──┘
 820   ▓▓ base plate ▓▓              ▓▓ base plate ▓▓         base  820-825
 800 ──░ +20mm float ░───────────────░ +20mm float ░───────  TABLE 0.800
```

### Step 4 — Trade study (flag-gating + float)
| Option | float | flag | groove z | H1 | H2 byte | verdict |
|---|---|---|---|---|---|---|
| **A ★ dedicated `add_c2_clip` param + `route_c2_scene` cfg flag + mirror C1 (+20mm)** | +20mm | new, default False | 0.829 | ✅ | ✅ OFF=byte-id | **RECOMMEND** |
| B bundle into `grasp_actuation` | +20mm | reuse grasp flag | 0.829 | ✅ | ❌ changes grasp_actuation scene (⑨a′ 81/81 was C1-only) | reject |
| C solid-floor no float + retarget predicate→809 | 0 | new | 0.809 | needs predicate edit (success-cond change) | ✅ | reject (breaks routing-clip convention + changes success predicate) |

### Step 5 — Reality-check / sensitivity / causality
- 5a sensitivity: predicate band ±3mm around 829; float +20mm lands groove EXACTLY at 829 (0mm error) → robust.
- 5b parameter-dependency: no new success threshold; ⑤ EXACT predicate (⑨b) needs to identify C2 groove-wall
  geoms (spacer/base excluded) → S2. Scene-config (`add_support_clips`/`g1_scene_align`) for live DoD runs =
  ⑥-gate concern, orthogonal to additive C2.
- 5c causal chain: C2 clip present → cable routed to C2 → descends → walls capture → predicate fires (⑤).
  Absent → phantom groove, seat leg invalid. Causally necessary. No adverse 5-step loop (static additive geom).
- Carried risk (SRG line 26): C2 re-grasp whiff at cell x-20_y5 (r_grip 0→32.8N@1.9mm) = downstream re-grasp/
  seat concern, NOT a scene-build defect → flag for ⑨b tail-cell diagnostics.

## §3. /reward-design (4 artifacts) — C2-seat reachability
Context: scripted D ρ=0 feedforward (NO policy learning at this node → deadlock/saturation patterns N/A);
the question = existing success predicate becomes achievable + formula-unchanged.

**A1 Reachability:** in_groove (|cable_z−0.829|≤3mm) + wall_ok (seat_dist≤3.5mm) both reachable at the
recorded C2-seat end-state (z_gap≈0, lateral≈0) for the 58/81 seating cells. No dead zone.
**A2 Causal DAG:** feedforward → EE to C2 → descend → [GATE C2 groove@829 present] —YES(comp5)→ capture →
seat TRUE; —NO(current)→ invalid. No deadlock.
**A3 Ground-truth:** P0 (z0.804, z_gap−25mm) FALSE ✓ / Mid (z0.840, z_gap+11mm) FALSE ✓ / Success (z~0.829,
z_gap≈0) TRUE ✓ reachable.
**A4 Episode trace:** G0→G5 recorded motion seats cable in groove; byte-repro confirms 58/81 seat → dynamics reach.
**GATE: PASS.** Predicate FORMULA unchanged (comp5 additive geometry only); C2 clip Z = float +20mm (groove@829).

## §4. PROPOSE (for 5体 [VERIFY], %12 = CC1)
**Change plan (Option A, additive flag-gated):**
1. `newton_skill_env_base.py` `build_multiworld_scene`: add param `add_c2_clip=False`. When True, add 5
   clip_parts (mirror the `add_target_clip` block, base-first order) at
   `(ROUTE_C2_XY[0]+dx, ROUTE_C2_XY[1]+dy, TABLE_HEIGHT+dz+ROUTE_CLIP_FLOAT_Z)`, shape_flags=0x6. ~20-30 LOC.
2. `newton_route_env.py` `_build_model`: pass `add_c2_clip=self._route_c2_scene`; parse `route_c2_scene`
   cfg flag (default False). ~5-10 LOC.
3. Flag-OFF (`route_c2_scene=False`) → `build_multiworld_scene` called without C2 → byte-identical to
   current env-core (25/81 EXACT re-regression guard).
**Rationale:** DoD⑥ real C2 groove; ⑨b C2-seat leg needs physical geom; plan §9; mirror C1 (reuse); float
+20mm → groove@829 matches predicate (0mm error); additive flag-gated → byte-preserve.
**Files:** `newton_skill_env_base.py`, `newton_route_env.py` (+ a C2-geom-present assert test; does NOT touch
`route_executor.py` → byte-repro self-check not NHA-cond5-triggered, but flag-OFF env byte-identity is the guard).
**Core SSOT refs:** `route_env_config.py:130-134`, `task_config.py:20/91/137/226/368`,
`newton_skill_env_base.py:1814-1840` (C1 template), `newton_route_env.py:1230-1237` (predicate), plan §9,
node `goal_verification`.
**KNOWN_ALTERNATIVES:** Option B (bundle grasp_actuation — REJECT: byte-identity risk on grasp scene) /
Option C (solid-floor no-float + predicate retarget — REJECT: changes success predicate, breaks routing-clip
convention). Option A chosen (dedicated flag + C1-mirror float).
**NOT in scope (carry):** ⑤ EXACT spacer-excluded wall-dist predicate build (⑨b gate); support-clips/
g1_scene_align live-scene config (⑥ gate); C2 re-grasp whiff cell (⑨b tail diagnostics).

## §5. Verification plan (post-5体-PASS → RULE-CHECK → build)
- Flag-OFF byte-identity: env-core recorded-state re-regression EXACT (build_multiworld_scene w/o C2 unchanged).
- Flag-ON C2 geom-present assert: mjModel introspection finds the 5 C2 clip geoms at ROUTE_C2_XY + groove@829.
- 層3 mechanical (ruff/ruff-format + write-site test) + 層5 (L3, geom/physics/SSOT) + 層2 (L3 post, %12).
- build/GPU HOLD until 5体 [VERIFY] PASS + RULE-CHECK (per %12 12:30).
