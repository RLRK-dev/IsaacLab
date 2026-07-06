# %12 (RS-TECH-LEAD) independent verify — ⑨a′ + ROUTE_* fix (2026-07-06 22:3x JST)

## Verdict: ⑨a′ (B)-strict = PASS (3/3 bars) / sync-guard = PASS (independent re-run) / ROUTE_* both-scope wiring = CONFIRMED

### bar① census clean
- census_env_gates.md: 19 gates classified; GEOMETRY drifts #7 CLIP_FLOAT_Z + #14 CLIP2_Y = both **FIXED** via ROUTE_* block;
  #8 SPACER / #9 CLIP2 = route-executor carry (pre-recorded in build plan, not bar-lowering). No unclassified gate.

### bar② per-cell EXACT (env predicate CODE faithful, proxy modulo)
- dod9a_prime.json: env BOTH=25/81 == offline BOTH=25/81 == predicted ceiling (dod9a_empirical_2nd_drift.md FULL-GEOM-ALIGN row);
  PER-CELL EXACT match=81/81, mismatches=[].
- Script calls the ACTUAL env methods (`_c2_seated_honest`, `_c1_retention_m`) on a built env (dod9a_prime.py:45-46, BUILD_OK log:38).
- %12 code-mirror check: script c1 composition (dod9a_prime.py:47) == env frozen def newton_route_env.py:964-968
  (z_c1<0.840 ∧ flank==flank ∧ flank<0.840) — textually identical.
- 0/81 → 25/81 flip empirically shown (old env 809/0.075 = 0/81, dod9a_empirical_2nd_drift.md sweep).

### bar③ c1 leg 81/81
- Route-side: dod9a_baseline_offline.md:5 (c1_retained_lowwall 81/81, strict_v2).
- Env-side (%12 independent, this verify): unbound `NewtonRouteEnv._c1_retention_m` (pure numpy, newton_route_env.py:762-778)
  + frozen composition over all 81 recorded finals → **c1_retained = 81/81** (scratchpad c1_leg_count.py, no GPU build needed).

### sync-guard (independent re-run by %12)
- test_route_geometry_sync.py re-run: **SYNC_GUARD: PASS 7/7** (C1_XY / C2_XY / CLIP_FLOAT_Z / GROOVE_Z==pin 829 / resolved_c2y).

### ROUTE_* both-scope wiring (%12 build+predicate flag) = CONFIRMED
- (a) predicate: newton_route_env.py:788 `rc.ROUTE_GROOVE_Z`; GROOVE_CENTER_Z import removed.
- (b) scene: newton_route_env.py:345 `target_clip_float_z=rc.ROUTE_CLIP_FLOAT_Z` → skill_base build_multiworld_scene
  :1826-1829 `TABLE_HEIGHT + dz + target_clip_float_z`; default 0.0 = other envs byte-identical (diff-verified).
- route_env_config.py:129-134 ROUTE_* block + provenance; guard set :198-201 (4/4). task_config UNTOUCHED (git diff clean).

## Commit-policy decision (%12): TWO-COMMIT SPLIT (isolate-to-HEAD is self-defeating)
- Evidence: working newton_skill_env_base.py = `ruff format --check` PASS; HEAD version = "Would reformat" →
  pre-commit would reintroduce the exact reformat noise on any staged edit. Noise = formatter-canonical output, must land.
- Commit 1 (format-only): save working copy → `git checkout HEAD -- newton_skill_env_base.py` → `ruff format` →
  verify diff vs saved copy == ONLY the 4 functional hunks → commit "Apply ruff-format to newton_skill_env_base".
- Commit 2 (functional, explicit-path): restore working copy (4 hunks: sig + docstring + clip-z + noqa) +
  route_env_config.py + newton_route_env.py + promoted test (below). Atomic per AGENTS.md.

## Dispositions (%12)
- DoD⑥: predicate unit-test **re-run required** on fixed env (prior PASS is stale vs ROUTE_GROOVE_Z predicate; DoD ledger
  must reference current code — fix-first, no bar change).
- Offset video (cell_x-20_y-15): **DEFER to route-executor** (loud, honest-scope). CABLE_XY_OFFSET is not wired at env-core →
  arm-at-offset vs cable-at-nominal = proxy that CREATES a geometric contradiction (proxy-representativeness gate) = misleading
  artifact. Same class as Rs-approved C2-seating deferral (Rs「1」21:1x); surfaced loud in COMPLETE packet for Rs.
- test_route_geometry_sync.py: promotion to `thread_isaac_lab/scripts/` **APPROVED** (was %12 systematic pin ②, state.md 22:0x)
  — convert absolute paths to repo-relative before commit.
- 58/81 exact-split = route-executor **blocking LOUD-CARRY** (unchanged, state.md 22:0x re-classification).

## Remaining before node COMPLETE
commits (above) → DoD⑥ re-run → %12 final verify → **Rs 動画 gate verdict (pending, required)** → COMPLETE → route-executor charter.
