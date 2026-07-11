---
doc_class: design-surface
node: T-ROOT-optE-route-dapg-C1C2-P2-routeexec
component: comp5 (real C2 groove scene)
author: "%11 COORD (w2:p3)"
date: 2026-07-11
rev: v2 (folds 5体 [VERIFY] DECIDE=REVISE 2257734eea + %12 boundary-steer 13:11 — 9 findings + PORT boundary)
gate: DESIGN-GATE (/geometric-design + /reward-design) — for targeted re-verify (CC1=%12)
---

# comp5 — real C2 groove scene: DESIGN-GATE v2 (geometric + reward)

**Charter:** comp3 remaining DoD (Rs GO 06:29). comp5 = %12 CONCUR+ratify 06:45 `a72b697c6b`. v1
(`32dd2a93ad`) → **REVISE** (mechanism approved-in-principle, build HOLD; 5体 `2257734eea`) + %12 CC1
boundary-steer 13:11 (PORT idiom boundary + record-time collision confirm). This v2 folds all of it.

## §0. Grounding (anchor set, §運用4)
- LEDGER route-executor VL7 🟢 ACTIVE. node `goal_verification:5-16` (fresh-read). 5体 DECIDE `2257734eea`.
- **Existing single-world C2 (CLIP2) mechanism** (%12 §運用28 reconcile): `test_newton_clip_routing.py:1214-1247`
  (locked build) + `route_executor.py:901/1195` `_clip2_geoms` + `:1170-71` CLIP2_X/Y + `:1167` CLIP_COLLISION.
  Constants: `task_config.py:168` MUJOCO_CONTACT_KE=40000 / `:169` KD=400; `route_env_config.py:130`
  ROUTE_C2_XY=(0.40,0.000) / `:131` FLOAT 0.020 / `:134` ROUTE_GROOVE_Z=0.829.
- **⭐record-time C2 config CONFIRMED (H4/M1):** canonical env-core replay recording `w0e_81rerun_snapdown_0537`
  env_gates, **uniform across ALL 81 cells**: `CLIP2=1`, `CLIP_COLLISION=1`, `CLIP2_Y=0.000`, `SPACER=1`,
  `S13_ROUTE_C2=1` (verified `route_demo_raw_meta.json`). C2 IS collidable @ y=0.000 w/ spacer — not assumed.

## §0.5. v2 CHANGELOG (9 findings + boundary-steer folded)
- **H1** rationale CORRECTED: comp5 serves **DoD⑥ C2-seating VIDEO + multi-world (MW) env-core route seating**,
  NOT ⑤/⑨b. ⑤/⑨b are SINGLE-WORLD (`route_c2_pin.json` ← `_run_mujoco_grasp_route`, already have CLIP2).
  **S2 (base-first-for-⑤) RETRACTED.**
- **H2** prior-art gate RUN (§9 CLEAR) + existing-C2 correspondence table (§3) + mirror-vs-port = **PORT (hybrid)**.
- **H3** build↔replay c2y assert + MW replay uses CLIP2_Y=0.000 (recording CONFIRMED 0.000) + 0.000/0.075 split (§6).
- **H4** contact-config CONFIRMED (not assumed): recording uniform CLIP_COLLISION=1 → collidable, MUJOCO_CONTACT_KE/KD
  (shared-ref, NOT C1's 2500), SPACER 6th geom; **param-idiom boundary** (no os.environ port, §3/§7); conservatism (§5).
- **M1** phantom/producer 58/81 RETRACTED as seat gate basis → re-measure real collidable C2 post-build (§5).
- **M2** spacer resolved: recording SPACER=1 → comp5 includes spacer 6th geom (matched); ⑤ spacer-EXCLUDED (§4).
- **M3** `route_c2_scene` = env-core-build-ONLY (docstring, §7).
- **L1** reference existing clip_parts + MUJOCO_CONTACT_KE/KD constants (no 3rd literal paste, §3/§7).
- **L2** §8 assert expansion.
- **⭐%12 boundary-steer 13:11 (CC6 idiom-regression guard):** PORT = HYBRID — keep C1-block STRUCTURE
  (param-idiom + ROUTE_C2_XY single-source + pre-replicate placement); inherit ONLY the C2 contact-config VALUES
  (constants by reference). **DO NOT port `os.environ.get(CLIP2_Y/CLIP2/CLIP_COLLISION)` into the MW builder**
  (would re-inject the CC6-warned 0.075 desync). Collidability = a comp5 param decision matched to record (§4/§7).

## §1. [TASK]/[L-TRIAGE] = L3
MW env scene change (`newton_route_env.py` + `newton_skill_env_base.py`). Invariant-PRESERVING (additive
flag-gated default-off; PORTS proven contact values into the existing param-idiom → **zero new mechanism**,
re-verify (c)). 5体 = %12 CC1.

## §2. Rationale (H1) — scene ownership
| consumer | world | C2 source | needs comp5? |
|---|---|---|---|
| ⑤ EXACT predicate | single | `route_executor._clip2_geoms` on locked CLIP2 | **NO** (exists) |
| ⑨b (81 single-cell) | single | `route_c2_pin.json` ← `_run_mujoco_grasp_route` | **NO** (exists) |
| **DoD⑥ C2-seating VIDEO** | MW env-core | `NewtonRouteEnv` MW build (`_c2_seated_honest:1234` reads `_C2_XY`) | **YES** |
| **⑥ MW env-core route seating** | MW env-core | same MW build | **YES** (⑥ single-vs-MW = ⑥-gate carry) |

## §3. Existing C2 mechanism — correspondence + PORT boundary (H2, L1, boundary-steer)
| element | existing single-world | comp5 MW (HYBRID) |
|---|---|---|
| build gate | `os.environ CLIP2=="1"` (`test:1220`) | **param** `add_c2_clip` (idiom = add_target_clip); NO os.environ |
| geometry | 5 `clip_parts` (=C1) `test:1233` | **reference the same clip_parts** (L1) |
| position | `CLIP2_X/Y` env (default 0.075) `test:1222-23` | **`ROUTE_C2_XY` param single-source (0.000)**; NO os.environ CLIP2_Y |
| float | `CLIP1_Z+float` `test:1224` | `TABLE_H+dz+ROUTE_CLIP_FLOAT_Z` (param) |
| contact (if collide) | `ke=MUJOCO_CONTACT_KE/kd=KD/gap.002` `test:1228-32` | **same constants by shared-ref** (H4) |
| collidability | `os.environ CLIP_COLLISION` | **comp5 param = matched to record (=collidable)**; NO os.environ |
| spacer | `os.environ SPACER` 6th box `test:1244` | **param, matched to record (SPACER=1)** |
**mirror-vs-port = PORT (hybrid):** C1-block STRUCTURE (param-idiom, ROUTE_C2_XY sourcing, pre-replicate) +
proven C2 contact-config VALUES (constants by reference). **Zero new mechanism; zero env-gate-sourcing port**
→ no CC6 desync re-injection (re-verify (c)).

## §4. /geometric-design (updated)
- Step1: 5 clip_parts (C1-identical, referenced) at `ROUTE_C2_XY=(0.40,0.000)` + float +20mm → groove @829
  = ROUTE_GROOVE_Z (0mm error). Contact when collidable = MUJOCO_CONTACT_KE 40000/KD 400/gap.002 (shared-ref).
- **H4 contact-config = CONFIRMED collidable** (recording uniform CLIP_COLLISION=1 across 81/81 cells, §0). comp5
  C2 collidable=True (record-matched), NOT phantom, NOT assumed. Record-time parity (replay must match recording).
- **CC3-CH5 reconcile (§運用28, surface-not-override):** CC3-CH5 cited a NON-collidable 25.3mm-penetration@0.0N
  cell. That is physically INCONSISTENT with collidable KE40000 (which resists ~900N at 25mm) → CC3-CH5 measured a
  DIFFERENT (probe) recording, NOT the canonical w0e_81rerun_snapdown (uniformly collidable 81/81). **Flagged for
  %12 cross-check** — comp5 matches the CANONICAL DoD⑥/env-core recording (collidable). If %12's canonical differs,
  re-match.
- **M2 spacer:** recording SPACER=1 → comp5 includes the spacer 6th box (matched, MUJOCO_CONTACT_KE/KD). ⑤ EXACT
  predicate is spacer-EXCLUDED (5 groove walls only) → spacer is seat-measurement-independent.
- No collision: C2@X0.40 vs support-clips@GRASP_X0.30, C1@0.35/Y0.150 — clear.

## §5. /reward-design (updated) — C2-seat reachability
- **M1: phantom 58/81 RETRACTED as gate basis** (was single-world byte-repro PRODUCER rate, not MW real-collidable-C2
  seat). Predicate FORMULA unchanged. Seat reachability = **RE-MEASURE with real collidable C2 in MW env post-build**.
- **Conservatism (GROVE §2.2):** collidable KE40000 = soft contact (not rigid form-closure) — realistic route parity.
  If the MW route seats collidable C2 → transfers (conservative-favourable vs a phantom pass); if it FAILS to seat
  collidable → definite finding. Direction: **conservative-relative-to-phantom** on the seat axis; absolute seat
  quality UNKNOWN until the post-build re-measure (no phantom substitution).
- **GATE: PASS (design-reachability)** — predicate satisfiable @829 (0mm) + formula-unchanged + collidable-matched;
  numeric seat deferred to real-C2 re-measure (M1).

## §6. C2-Y split + build↔replay assert (H3)
- **Split (documented):** single-world locked route DEFAULT CLIP2_Y=+0.075 (`CLIP_POSITIONS[1]`); MW env-core +
  the canonical recording use **0.000** (recording env_gates CLIP2_Y=0.000 uniform 81/81; `route_env_config.py:130`
  ROUTE_C2_XY[1]=0.000 "!= task_config (0.40,0.075)"). 0.075 LIVE for other tracks, "parked for Rs" (`:127`).
- **comp5 (MW) uses 0.000** (matches `_c2_seated_honest`'s `_C2_XY` AND the recording). 
- **Assert (build↔replay, §8):** `abs(recording_meta_env_gates_CLIP2_Y − ROUTE_C2_XY[1]) < 1e-6` (fail-loud; the
  recording meta's `env_gates.CLIP2_Y` = 0.000 confirmed).

## §7. PROPOSE v2 (for targeted re-verify, CC1=%12)
**Change plan (Option A, additive flag-gated, HYBRID port — param-idiom + C2 contact values):**
1. `newton_skill_env_base.py` `build_multiworld_scene`: add `add_c2_clip=False` param. When True, add the C2
   V-groove by **reusing the existing add_target_clip `clip_parts`** (L1) at
   `(ROUTE_C2_XY[0]+dx, ROUTE_C2_XY[1]+dy, TABLE_HEIGHT+dz+ROUTE_CLIP_FLOAT_Z)` — **all param/rc-sourced, NO
   os.environ**. Contact = **MUJOCO_CONTACT_KE/KD + gap 0.002 constants by reference** (collidable, matched to
   record); shape_flags 0x6; + spacer 6th box (SPACER matched). NO `os.environ.get(CLIP2_Y/CLIP2/CLIP_COLLISION)`.
2. `newton_route_env.py` `_build_model`: pass `add_c2_clip=self._route_c2_scene`; parse `route_c2_scene` cfg flag
   (default False). **Docstring: env-core-build-ONLY (M3)**, not on ⑤/⑨b single-world path. + build↔replay c2y
   assert (H3, §6).
3. Flag-OFF → byte-identical to current env-core. No route_executor.py edit.
**Rationale:** DoD⑥ real C2 groove video + MW env-core route seating (H1); PORT proven CLIP2 contact values into
the MW param-idiom, zero new mechanism + zero env-gate desync (H2, boundary-steer); collidable matched to record
(H4, confirmed uniform 81/81); c2y=0.000 MW + assert (H3).
**Files:** `newton_skill_env_base.py`, `newton_route_env.py` (+ C2-geom assert test). `route_executor.py`
UNTOUCHED → NHA-cond5 byte-repro not triggered; flag-OFF env byte-identity is the guard.
**Core SSOT refs:** `test_newton_clip_routing.py:1214-1247`, `route_executor.py:901/1165-71/1195`,
`route_env_config.py:127/130-134`, `task_config.py:168-169`, recording `w0e_81rerun_snapdown_0537` env_gates.
**KNOWN_ALTERNATIVES:** B (bundle grasp_actuation — REJECT byte-risk) / C (solid-floor no-float + predicate
retarget — REJECT success-cond change) / v1's C1-soft-mirror — REJECT (H4 wrong contact) / **os.environ-sourcing
port — REJECT (boundary-steer: CC6 desync re-injection)**. Chosen = HYBRID (C1 structure + C2 contact values).
**Carry:** ⑤ EXACT spacer-excluded predicate (⑨b); ⑥ single-vs-MW (⑥ gate); x-20_y5 C2 whiff (⑨b tail);
C2-Y 0.000/0.075 Rs batch reconcile (parked); CC3-CH5 recording cross-check (%12).

## §8. Verification plan (L2 expanded) — post-re-verify → RULE-CHECK → build
- Flag-OFF byte-identity: env-core recorded-state re-regression EXACT (build_multiworld_scene w/o C2) — re-verify (d).
- Flag-ON asserts (L2): (i) mjModel finds 5+1(spacer) C2 geoms; (ii) built C2 XY == _C2_XY (ROUTE_C2_XY, 0.000);
  (iii) collidable shape_flags match; (iv) arm/cable joint-index invariant (additive geom no layout shift);
  (v) build↔replay c2y assert (H3).
- M1 real-C2 seat re-measure (post-build, MW env, collidable) replaces the retracted phantom 58/81.
- 層3 (ruff) + 層5 (L3) + 層2 (L3 post, %12). build/GPU HOLD until re-verify PASS + RULE-CHECK.

## §9. Prior-art gate output (H2, re-verify (b))
`check_thread_vault_prior_art.sh --fail-on-blocker "comp5 C2 scene" "CLIP2 build" "C2 seating video"` →
**EXIT 0, 0 blocker lines** (`scratchpad/pa_comp5_v2.txt`). Supplementary single-word run = 6 hits, ALL
self-referential node `state.md` current-work/plan entries (Rs GO / order-correction / fork-④ / SRG / Stage-A
carry); zero past-failure verdict → **CLEAR**.

## §10. Re-verify map (%12 scope (a)-(d))
- (a) 9 findings + boundary-steer: H1 §2, H2 §3/§9, H3 §6/§8, H4 §0/§4/§5, M1 §5, M2 §4, M3 §7, L1 §3/§7, L2 §8, boundary §0.5/§3/§7. ✅
- (b) prior-art no blocker: §9. ✅
- (c) zero new mechanism + zero env-gate-port: §3 (HYBRID, param-idiom, contact-constants-by-ref). ✅
- (d) flag-OFF byte-identity structural: §7.3 + §8. ✅
