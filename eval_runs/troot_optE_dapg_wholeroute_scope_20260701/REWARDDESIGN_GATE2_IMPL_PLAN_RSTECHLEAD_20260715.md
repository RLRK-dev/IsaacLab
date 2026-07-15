# reward-design ② seat-predicate interp fix — IMPLEMENTATION PLAN (proposal for [VERIFY])

**Author:** RS-TECH-LEAD (w2:p4). **Date:** 2026-07-16 01:5x JST. **L3** (success-condition change).
**Design of record:** `REWARDDESIGN_GATE2_SEAT_PREDICATE_RULING_VTDESIGN_20260715.md` (p5, BANKED §1-§11, commit `f49b68f825`). **Gate:** reward-design ② regenerated-PASS with this design; implement then `/pre-check`. **This doc = the concrete change for the L3 [VERIFY] debate → [RULE-CHECK] → [CHANGE].**

## Principle (p5 §1.1/§2, Rs 01:16/01:37)
The bar (3mm) and the sparse G1-G6 structure are NOT broken. The **instrument** confuses identity (which node) with boundary (how far off-axis) — the nearest-in-Y node leaks its Y-residual into `lateral`. Fix = **one shared interp helper** measuring `dx` at the exact `y=clip_y` crossing (dy≡0), reused at every RL-env measurement point. Sparse-primary preserved; **no dense shaping** (DQ1-closed). Coupling = (iii): keep the DoD-9a mirror, interp **both** sides.

## Scope
- **File A `newton_route_env.py`** (RL env) — **fully self-contained** (§11.3).
- **File B `p9_recount_strict_v2.py`** (offline recount) — offline interp re-derivation, no sim, keeps DoD-9a (§11.1).
- **Separate leg (NOT this change):** route `route_executor.py:3881` + runner `policy_route_runner.py:309` = producer's own instruments → producer re-run (GPU-free), §9. Tracked, not done here.
- **Out of task_config:** `T_GROOVE` stays in `task_config.py:368` (MPC/IC consumers); removed only as the *RL-env seat datum*.

## File A — newton_route_env.py

**A1. Shared helper** (new), p5 §2 algorithm:
```
def _seat_interp(cable_pos, clip_x, clip_y) -> (dx, z_cross):
    # over all segments straddling y=clip_y: linear-interp x,z at y=clip_y; dx=|x_cross-clip_x|
    # S-curve (D-5): min dx over all crossings ; no crossing -> (INF, INF)  [fail-closed]
```
**A2. Built-model bars** — REUSE the existing derivation pattern `route_executor.py:3031-3073`: `lat_bar = wall_inner − cable_r = 3.5mm`, `z_lo=821`, `z_hi=836` (floor/rim − cable_r). Source from the RL-env built clip geometry (`_v_groove_clip_parts` walls x=∓9 ± hx1.5 ⇒ inner ±7.5; R=4). Prefer a shared datum over re-hardcoding.
**A3. `_seat_metrics`** (`:1300-1311`) → return `(dx, z_cross)` from `_seat_interp`. Update the 3-tuple unpack sites: obs `:1427`, G3 `:1487`, G5 `:1488`, `_c2_seated_honest` `:1317`.
**A4. G3/G5** (`:1550/:1552`): `p3 = (dx_C1 ≤ lat_bar) ∧ (z_lo < z_cross_C1 < z_hi) ∧ (ph≥2)`; `p5 = (dx_C2 ≤ lat_bar) ∧ (z_lo < z_cross_C2 < z_hi)`. Remove `T_GROOVE` here.
**A5. `_c2_seated_honest`** (`:1313-1320`): `seated := (dx_C2 ≤ lat_bar) ∧ (z_lo < z_cross < z_hi)`. Remove `T_GROOVE` in `wall_ok`.
**A6. obs[OBS_SEATED_SEG_D]** (`:1428`) = `dx` (interp). Meaning shifts seat_dist→dx (env untrained ⇒ safe). ⚠ Check obs[58/59] `OBS_SEAT_ZGAP/LATERAL` (`route_env_config.py:65-67`) consumers of the old 3-tuple.
**A7. c1_retained** (`_c1_retention_m` `:1282-1298`, used `:1489-1495`, §8b): add interp-dx leg → `c1_retained := (dx_interp_C1 ≤ lat_bar) ∧ (z_lo < z_cross_C1 < z_hi)` (supersedes z-only ceiling; keep the frozen-mirror shape for DoD-9a).
**A8. `_crossing_x_dev`** (`:1322-1327`, Rs "4th site") → use `_seat_interp` (actually interpolate) for drop `:1516/:1522`. Loose bar (`DROP_LATERAL_DEV_MAX_M`) ⇒ not correctness-critical, but no mislabeled nearest-node left in-file.

## File B — p9_recount_strict_v2.py
**B1. `flank_from_npz`/c1 def** (`:39-44`): add interp-dx from `cable_xyz` (mirror A7's live interp). Both-sides interp keeps DoD-9a `live == frozen` (§11.1). Offline, no sim.

## Failure modes to probe in [VERIFY]
1. **Helper edge cases:** cable never reaches y=clip_y (fail-closed INF ✓?); exactly-on-node (`ys[i]==clip_y`); degenerate `ys[i]==ys[i+1]` (guarded ✓); S-curve picks min-dx not first-cross.
2. **Blast radius:** every consumer of the old `(seat_dist, z_gap, lateral)` 3-tuple updated? obs[58/59] axis-seat dims? any test asserting the old signature?
3. **DoD-9a byte-match:** does File-B interp mirror File-A interp exactly (same positions ⇒ same dx)? Off-by-one in segment indexing?
4. **Byte-neutrality of producer/golden:** this touches ONLY the RL-env reward + offline recount — the producer route (byte-repro golden) is untouched ⇒ golden stays byte-identical (assert).
5. **§11.4 self-test:** the frozen demo may now FAIL c1_retained if its cable is off-axis at C1Y → surface as demo Rs-video re-validation, do NOT loosen the bar to pass it.
6. **z-band source:** 821/836 derived from the *RL-env* built model (not copied from route_executor's mujoco path)?

## Gates (remaining)
[VERIFY] 5-body (this) → [RULE-CHECK] stage2 → [CHANGE] → [RUN] (seat-predicate unit test on S0-S5 §5 table + regression: golden byte-repro unchanged) → **/pre-check** (BLOCK ⇒ no land) → W1 B3b-B7 unblock. p5 verify leg post-land (interp helper + DoD-9a match + c2_honest auto-follow). Video: numeric change ⇒ not required for the change; final capture verdict stays Rs-video.

---

## [VERIFY] OUTCOME (2026-07-16 02:0x) — ⚠ infra-degraded: 1/5 independent + CC1 self-review

**Debate ran degraded:** CC5 (fidelity/scope) **completed independently**; CC2/CC3/CC4/CC6 **stalled** (600s stream-watchdog, systematic infra flakiness this window). The four stalled lenses were **CC1-self-applied** (reduced independence — noted). No design-breaker found; the ruling stands. Verdict = PROCEED to [CHANGE] with 5 refinements folded in.

**Findings to fold into [CHANGE] (none blocks; all addressable):**
1. **Bar source (CC5, independent):** derive `lat_bar/z_lo/z_hi` from the **RL-env's own built `_v_groove_clip_parts`** geometry — NOT hardcoded `3.5/821/836` literals (breaks p5's built-model/datum discipline), and NOT by refactoring `route_executor.py`'s inline derivation (would touch the producer file → break the byte-repro golden). Add a shared RL-env datum helper.
2. **All obs consumers (CC3-self + CC5):** the helpers' signature change touches MORE than the reward — audit & update every obs dim: `OBS_SEATED_SEG_D(49)`, `OBS_SEAT_ZGAP(58)`, `OBS_SEAT_LATERAL(59)` (from `_seat_metrics` 3-tuple), `OBS_CROSSING_X_DEV(57)` (`:1442`, from `_crossing_x_dev`), `OBS`-retention `(60/61)` (`:1447`, from `_c1_retention_m`). Not just the reward/drop uses.
3. **Node-order assert for DoD-9a (CC4-self, CRITICAL):** the z-only def was order-independent (max-z over a window); the **interp is order-DEPENDENT** (it walks consecutive nodes as a polyline). DoD-9a `live==frozen` now requires live `cable_pos` (from `_cable_bodies` body_q) and npz `cable_xyz` to be the **same node sequence**. The recount carries a `PIN_BODY_TO_NODE=28` body-vs-node offset — add an **explicit assert** that the two walks index the same polyline before trusting the mirror.
4. **"Closest-to-groove" selection (CC2-self):** p5 §2 says "最も溝に近い交差" — implement as the crossing best satisfying BOTH legs (prefer an in-z-band crossing, then min dx), NOT literal min-dx-then-check-z (an S-curve could pick a laterally-closer crossing at a wrong z and reject a truly-seated one).
5. **Residuals (CC6-self, surface not block):** (a) the fix makes the latch REACHABLE but adds no dense gradient — training success still rests on the BC prior producing seated states (downstream empirical, validated by /pre-check + run, not this fix); (b) interim **live-vs-producer verdict split** until the producer re-run leg (known/accepted, §11.2).

**Compensating gates for the degraded independence:** /pre-check (skeptical sub-agent, pre-land) + p5's committed post-land verify leg + the S0-S5 unit test. If Rs prefers, re-run the independent debate when infra recovers before [CHANGE].

---

## /pre-check OUTCOME (2026-07-16 04:1x) — PASS-WITH-RISKS (sub-agent completed + CC1 self, converged)

Sub-agent COMPLETED (no stall). Verdict = **PASS-WITH-RISKS**. Independently confirmed clean: compiles/AST; removed imports (CLIP1_X/Y, T_GROOVE) have no live refs; interp cannot emit NaN (t∈[0,1], denom≠0 by y0!=y1); seat legs fail-closed on miss; **z-band 821/836 + lat 3.5 verified vs producer route_executor.py:3070-3078**; timeouts purity intact; no control/kinematic; G1-G6 latch preserved; no in-repo test asserts old obs semantics; **`_cable_bodies` = contiguous chain order (newton_skill_env_base.py:2023) → interp polyline valid / DoD-9a node-order assumption holds.**

**Risks — NOT code defects; LAUNCH-readiness couplings:**
1. **HIGH — c1_retained ↔ C1-pin coupling.** The fix (correctly, per ruling §8b) promotes `c1_retained` from a no-op (81/81 always-true) to a HARD `interp-dx ≤ 3.5mm` gate, now a required G6-SUCCESS conjunct (`newton_route_env.py:1516` + `:1592`). ⇒ **G6 is reachable ONLY IF C1 stays seated through the C2 window** — which the clip-retention pin (`authorize_clip_pin`, **NOT YET implemented**) is the mechanism to guarantee (C1 clip is 16× soft, ~52.87mm escape documented). **This couples reward-design ② to authorize_clip_pin.** Must-verify pre-launch: log the 4 g6_live conjuncts on a short BC-prior-seated rollout WITH the C1 pin active; confirm c1_retained holds across the C2 window. Else the GPU run yields zero terminal reward.
2. **HIGH (conditional) — obs contract change.** obs[49/57/58/59/60/61] meanings shifted (esp. [60/61] z→interp-dx). Fresh PPO fine, but a resumed pre-70fc checkpoint or BC/DAPG demos recorded on the old contract → stale semantics → destabilized training. Must confirm: fresh train / demos regenerated.
3. **MED — `_crossing_x_dev` fail-open blinds the extreme lateral-escape drop** (design-boundary, p5): no-crossing / seated+escaped S-curve → lateral_dev=0 → the −10 escape drop is suppressed (no false-success — seat gate still rejects — but the guard is removed).
4. **MED — geometric (not topological) seat** (design-boundary, p5): `_seated_in_groove` is a pure box test over the min-dx crossing; a looped cable with a NON-routed segment in the groove box reads seated (more lenient than the producer's Y-window/seat-body leg route_executor:3074-3078) → non-conservative (sim-only G6 that may not transfer).

**Verdict:** reward-design ② FIX = correct + validated (PASS-WITH-RISKS); the predicate is reachable **given the C1 pin**. W1 LAUNCH gated on: (a) C1 pin active [authorize_clip_pin] + g6_live reachability rollout (FM1), (b) fresh train / regenerated demos (FM2). FM3/FM4 = p5 design-boundary (surface, non-blocking). ⇒ **② and authorize_clip_pin are coupled for the W1 launch.**
