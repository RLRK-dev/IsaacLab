# Option E — S2: Recorded Deferred Obligations (closes %3 PV D3/D4)

**Author:** %12 · **Date:** 2026-06-08 · **Context:** S2 substrate swap (Franka→UR5e+Robotiq). %3 substance-PV = ARTIFACT-PASS on the LIVE RL-env path; these are the OFF-LIVE-path items intentionally NOT remapped in S2, recorded so they are not lost.

## Scope statement (D2)
The S2 index/filter remap + the §5.6 A3-guard (`s2b_section5_6_audit.sh` = PASS) are **LIVE RL-env-path-scoped**: base + the 6 skill envs (`newton_{skill_env_base,approach_cable,insert_clip,unclamp,grip,clamp,aerial_regrasp}.py`). Repo-wide, ~80 old Franka finger patterns remain in off-live-path scripts/utils — **proven off-live by import-graph** (no `newton_*_env.py` imports them; live cross-module refs = the 6 SSOT symbols + `_tncr.DEVICE` only). So the substrate swap is correct on the path that runs; the items below are deferred, not broken-now.

## D3 — demo-gen / standalone scripts: Franka finger patterns NOT remapped
**Files (off-live; retain Franka `[7,8]` / `(7,8,FN+7,FN+8)` / `local<7` patterns):**
- reachable-but-demo-gen (imported_by>0, NOT RL-env substrate): `generate_demos_mppi.py`, `generate_demos_mppi_m2.py`, `generate_demos_mppi_m3_ar.py`
- standalone (`__main__` only): `build_mppi_scene.py`, `collect_approach_cable_demos.py`, `wet_run_full_sequence.py`, `test_newton_clip_routing_sdf_plain.py`, `test_grip_modes.py`, `diag_unclamp_step1.py`, `demo_aerial_regrasp.py`, `build_aerial_regrasp_precondition.py`, `build_unclamp_precondition.py`
- specific C5 consumer sites left un-remapped: `build_aerial_regrasp_precondition.py:220`, `generate_demos_mppi_m3_ar.py:343` ({7,8,FN+7,FN+8} sets) + `test_newton_clip_routing.build_scene` filter (RL path = `base.build_multiworld_scene`; this is the script/smoke builder).
**Why deferred:** these are demo-generation / standalone-test paths, NOT the RL-env substrate (out of S2 scope per the design's triage: "swap LIVE, flag the rest, don't scope-creep obsolete scripts").
**Latent-bug risk (the obligation):** on the UR5e SSOT (`FRANKA_NUM_JOINTS=14`, etc.) these would mis-filter (Franka `[7,8]` over UR5e bodies → wrong COLLIDE/no grasp contact) or IndexError (FN=14 over a Franka-shaped build). **They MUST be ported to the UR5e+Robotiq spaces BEFORE demo-generation / these paths are resumed** (S5+ when demos/grasp are regenerated). Until then they are inert (not on the live path).
**S2c action:** in-code comment-flag each ("Franka-legacy finger indices, not UR5e-swapped (S2); port before re-running on the UR5e substrate").

## D4 — duplicate `add_kinematic_arm` / build path NOT reconciled
**Files (off-live; S2a comment-flagged, internals untouched, 3-tuple):**
- `newton_routing_utils.py:652` `add_kinematic_arm` + `:748` `build_scene` (self-contained Franka path; `_load_finger_mesh()`, 3-tuple). UNREACHABLE: no env/orchestrator/script imports `build_scene` from it (S2a grep-confirmed).
- `test_newton_dual_clip_routing.py:323` `add_kinematic_arm` (imported by nobody; own `__main__` only).
**Why deferred:** off-live duplicates; reconciling (port to UR5e + unify on the 4-tuple) is scope-creep into unreachable paths (per Delta-H3 "reconcile WHEN triaged").
**Obligation:** if either standalone path is ever revived, reconcile it to the UR5e+Robotiq `add_kinematic_arm` (live source = `test_newton_clip_routing.py:612`, 4-tuple) OR remove it. Currently inert (S2a fail-loud comment-flag documents the hazard).

## Status
- **D1 (audit artifact):** CLOSED — `s2b_section5_6_audit.sh` (+ `.out`, PASS) materialized, classification-aware, live-env A3-guard.
- **D2 (claim scope):** CLOSED — restated live-path-scoped (this doc + the audit header).
- **D3 / D4:** RECORDED here (durable) + to be in-code comment-flagged in S2c.
- **D5:** S2c (cosmetic) — next.
These are gate-hygiene/provenance items; the S2 substance (LIVE-path substrate swap) = %3-PV ARTIFACT-PASS + §5.6 audit PASS.
