# %12 (RS-TECH-LEAD) final-verify leg 2 — commits + DoD⑥ (2026-07-06 22:54 JST)

## Commits = VERIFIED
- fcc1a22fae (format-only): functional-token grep `target_clip_float_z` = **0** (%12 independent). Message documents isolation intent.
- a6cbc148ab (functional): numstat = newton_route_env 3+3 / skill_base 5+2 / route_env_config 21+0 / test 58+0 — **exactly 4 files,
  zero eval_runs contamination**. Working tree clean for all 4 (git status empty).
- Promoted test `thread_isaac_lab/scripts/test_route_geometry_sync.py`: %12 re-run **SYNC_GUARD PASS**; SPDX 2022-2026 header OK;
  absolute-path grep `home/rlrk` = **0** (repo-relative confirmed).

## DoD⑥ — %12 verify + disposition
Original bar (BUILD_PLAN_ENVCORE_COORD_20260706.md:22): "predicate unit-test @cuda:0 (6 phase 全 fire + no-re-fire + guards-quiet
on canonical demo)".

### Verified PASS (env-core-testable legs)
- **no-re-fire / latch monotonic**: dod6.json A_no_refire_monotonic=true over 860 live steps (recorded_replay, reset-suppressed).
- **c1_retained all phases**: dod6.json B_all_c1_retained=true (ph5/13/14).
- **c2 phase-gating — %12 FULL-POPULATION independent verification** (dod6b_firing_full_p12.py, unbound pure predicates, no GPU):
  firing set = 25/81 (== ⑨a′ env count, cross-consistent); **FALSE@ph5(C1_SEAT) = 25/25; TRUE@ph14(C2_SETTLE) = 25/25;
  violations = []**. This upgrades %11's "sampled firing cells" claim (which had NO on-disk artifact — dod6.json covers only
  non-firing cell_x0_y0) to full-population disk evidence.
- ⚠ Reading guard for dod6.json: `B_all_c2_stage_consistent=false` is an EXPECTED artifact, not a predicate bug —
  cell_x0_y0 is a non-firing (wall/spacer-gap) cell, and the script's `expect_c2=True` at **ph13** was over-strict
  (settle completes at ph14: TRUE@ph13 = 12/25 even among firing cells). Correct gating form = FALSE@5 ∧ TRUE@14, holds 25/25.

### PENDING-EVIDENCE (1 item, blocking ⑥ close)
- **guards-quiet**: %11 claimed "drop-proxy のみ done、false-terminate 無" but dod6.py counts n_done without serializing it,
  and no guard attribution exists on disk (video_nominal_log grep = 0 hits). Env exposes the needed surface:
  extras `log./metrics/drop_count`, `/metrics/explosion_count`, `/episode/success`, `time_outs` (newton_route_env.py:1056,1068-1075).
  → Required: extend dod6.py leg A to accumulate and serialize {n_done, drop_count_sum, explosion_count_sum, success_sum,
  timeouts_sum} → expect all done attributed to drop-proxy, explosion=0, success=0, timeout=0 (N=860<900).

### Re-classification disposition (%12): ACCEPT — "6-phase full fire (canonical demo, live)" → route-executor blocking LOUD-CARRY
- Class = premise-correction, same as 22:0x ⑨a (B)-strict disposition ("数え方は変えず場所を移す"):
  the bar as authored assumed recorded-target-replay ⇒ cable carried ⇒ G2-G6 fire (build plan CC5-2 (iii) intent), but the
  fingers-open proxy boundary (pre-recorded: state.md 21:4x, real grip = route-executor) makes that premise FALSE at env-core;
  the second blocker (wall/spacer 25/81 proxy ceiling) was pre-recorded in the build plan. Neither blocker is new or induced
  by this test.
- Conditions: (1) registered as **blocking** LOUD-CARRY bundled with ⑨b (live online-numerator) + ⑦ (handover) on the
  route-executor charter — route-executor cannot COMPLETE without full-fire demonstrated live; (2) surfaced loud in the
  env-core COMPLETE packet (Rs-visible); (3) guards-quiet evidence lands first (above).

## Evidence-hygiene flag (%11, minor)
- dod6.json.note asserts "全 sample" firing-cell gating with no corresponding artifact — claims must ship with on-disk
  evidence (§運用17). Resolved this time by %12 full-population run; keep note-claims artifact-backed.

## Path to node COMPLETE (unchanged)
guards-quiet artifact → ⑥ close → %12 final verify done → **Rs 動画 gate verdict (pending, required)** → COMPLETE →
route-executor charter (58/81 wall-split / CABLE_XY_OFFSET / real grip / ⑨b online / ⑦ handover / ⑥ full-fire live /
C2 groove + C2-seating video gate = blocking LOUD-CARRY 登録).
