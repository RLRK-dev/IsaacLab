# (d-b) D-b window gate — prereg (impl + probe + acceptance)

**v0.3 — 2026-07-17 23:14 JST** · **Author:** RS-TECH-LEAD (w2:p4) · **Node:** pin (d) — (d-b) half
**Governing:** charter §9 framing (`463f156fc6`) + §9.7 RATIFY (`bd1c534678`) + §9.7.8/§9.7.9 (`082baa1ca6`,
B1 refinement + pN R3/R1/R4). **Baseline code = HEAD `469435014f`** (code identical through `082baa1ca6`;
intervening = docs). **Status:** DRAFT — folds pN v0.2 R1-R5 + p5 §9.7.8/§9.7.9. Awaiting pN v0.3 re-readback.
**⛔ [CHANGE] STOP until pN readback PASS.** training-ready禁止 continues.

**One line:** call the drive-agnostic `_maybe_activate_c1_pin` from the ik_chord (policy) drive loop at
pre-step, `route_steps` hoisted unconditionally, removing the G4-G6 dead zone. No reward term, no new kinematic
exception.

## §0 v0.3 fold record (pN v0.2 R1-R5, all resolved)
- **R3 (CRIT, factual — p5 §9.7.9 corrected §9.7.0)**: the "fire capture ~5mm > retention 3.5mm loose-weld
  margin" was WRONG. `clip_capture_check` (`route_executor.py:981`) and `authorize_clip_pin` (`:1024`) BOTH use
  `clip_capture_predicate(…, rc.SEAT_LAT_BAR_M, …)` = **3.5mm** (identity, containment-by-identity `:1004-1006`);
  `match_tol_m=5e-3` (`:1014`) is the eq world-position resolution, NOT the capture width. **Correct non-crutch =
  fire strictness ≥ retention** (fire lateral 3.5mm same; fire z-window `[821,831]` ⊆ retention z `[821,836]`) ⇒
  the pin CANNOT fire at a looser seat than retention — stronger than the margin claim. **L-DB-I → L-DB-I′**
  (§3.1). Unit fix: `_SEAT_MISS_DX_M=9.0` is a **9.0 m** sentinel (`env:1301`; "9.0mm" was wrong; escape logic
  unchanged — exact-sentinel equality `dx==9.0`).
- **R1 (spurious re-def — §9.7.8 governing)**: "same-RL-step transit → no fire" is NOT derivable from K=3 (1 RL
  step = 10 physics frames, `env:404`; a ≥3-frame inside-capture dwell correctly fires). **spurious = inside
  capture∧depth for consecutive frames < K, only.** The circularity closes via fire⊆retention (a ≥K dwell fire
  is a genuine seat), so **training-ready does NOT wait on the live-policy leg**; live-policy fire distribution
  is a post-launch monitor; a pathology re-opens §8.2/§9.7.3. L-DB-G reframed (§3.1).
- **R4 (perf)**: ratio ON/OFF ≥ **0.8** frozen pre-run (p5 bar; Rs override). **N framing fix**: fork-B = 4
  process × wc=1, the pin reads world-0 body_q ⇒ **perf leg = wc=1 single-proc pin OFF/ON** (not wc=4). L-DB-K
  (§3.1).
- **R2 (provenance freeze)**: §3.0 now carries REAL values (recording sha, cfg, command, horizon, schema).
- **R5 (landing protocol)**: §5 — fixed gate order, enumerated test IDs, claim manifest.

## §1 scope
- **IN**: (1) unconditional `route_steps` hoist; (2) `_maybe_activate_c1_pin` at ik_chord pre-step; (3) probe
  `pin_db_window_probe.py`; (4) test additions (§5).
- **OUT**: FF branch (`:1225`); the pin method body (`:1821-1860`); reward/obs/success predicates;
  `task_config.py`; K/Z_FIRE/SEAT bars; training launch; cell-2 (DoD-7).
- **M2 → L-DB-L (named acceptance item at V0/prelaunch)**: the DAPG/BC loader additive-key consumer assert —
  exact loader command + expected result, run at V0/prelaunch (not "training-era").

## §2 impl design (2 edits; code after pN readback + [CHANGE] gates)
Baseline ik_chord else-branch (`newton_route_env.py:1245-1283`):
- **(2-1) route_steps unconditional hoist** — replace the `grasp_actuation`-gated block (`:1247-1251`) with an
  unconditional pre-loop hoist (mirrors FF `:1210`; expression byte-identical, verified).
- **(2-2) pin call at pre-step, order frozen** = `joint assign(:1272-1273) → grip(:1274-1280) → PIN → physics(:1281)`:
  `self._maybe_activate_c1_pin(route_steps, step)` between the grip block and `_physics_step_all`.
- **pre-step single-clock** (§9.7.1): body_q holds the previous frame (only `_physics_step_all` advances it) =
  same clock as FF (`:1225`<`:1226`); §8.13 `run_start+K` transfers.
- **sync (Q1 RESOLVED, pN-confirmed)**: `body_q.numpy()` auto-syncs GPU→CPU (**warp 1.13.0**,
  `warp/_src/types.py:4083-4086`); **no `wp.synchronize`, no sync fork.** Version-pin: warp 1.13.0.
- **INVARIANT #5**: reuses `authorize_clip_pin` (`route_executor.py:987`, single writer); no new exception.

## §3 probe design (`pin_db_window_probe.py`, wc=1, deterministic ik_chord — no trainer)

### §3.0 provenance freeze (R2 — REAL values)
- **env venv**: `/home/rlrk/env_isaaclab7/bin/python` · warp 1.13.0 · **CUDA_VISIBLE_DEVICES=0**, device cuda:0
  (CPU mujoco stepping; one cell per process).
- **command (verbatim)**: `CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/pin_db_window_probe.py --cell cell_x0_y0 --run <LEG>` (LEG ∈ {A_with, A_without, E_gT, E_gF, F, G, H, I, J, K, L}).
- **recording (input)**: `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz` · **sha256 `5f1c3f9238f45057011cfad1…`** · 22 keys.
- **cfg (frozen)**: `world_count=1` · `grasp_actuation=True` · `route_executor_impl="route_executor"` ·
  `route_recording_npz=<above>` · `g1_scene_align=True` · **`route_drive_mode="ik_chord"`** (the (d-b) target;
  (d-a) used feedforward) · `route_c2_scene=True` · `route_c1_pin=<A-pair flag>`.
- **drive**: deterministic **zero-residual action** (action=0 ⇒ commanded = route base target ⇒ ik_chord follows
  the recorded route; reproduces seat→route without a policy). · **horizon** = MAX_EPISODE_STEPS **900**
  (`env:407`, ROUTE_TERMINAL_STEPS) · seed = N/A (deterministic replay/drive) · ep1≡ep2.
- **A-pair**: A_with vs A_without differ ONLY by `route_c1_pin` on ONE landed source (changed-source set = []).
- **output artifact**: `pin_db_window_probe_result_cell_x0_y0.json` (schema frozen at impl: per-leg fields).
- **freeze also**: fresh outbox per run · expected rc=0 · harness self-sha · loaded-source closure + env
  fingerprint · pre/post hash bracket.

### §3.1 legs (binary bars)
- **L-DB-A (WITH/WITHOUT deadlock contrast — core, binary).**
  - WITHOUT (`route_c1_pin=False`): MUST reach **G3 latch** (`_g_latched[w,2]=True`), THEN C2 route drives
    `dx_c1`→MISS (**9.0 m** sentinel, crossing lost) or >60mm ⇒ `c1_escape`=True ⇒ `dropped` ⇒ **terminate before
    G4** (`_g_latched[w,3]=False`). ⛔ a FAIL before G3 = not acceptable.
  - WITH (`route_c1_pin=True`): genuine-seat fire + audit + retention continuity + `c1_escape`=False +
    **G4 ∧ G5 ∧ G6 latch, `success`=True** + `invalid`=0 + `time_out`=0 (binary). ⛔ "reachable" insufficient.
- **L-DB-B (fire ≺ release, single route-clock).** Bar = `route_t_at_fire < _route_release_step` (both route_t;
  `:558/:584-585`). ⛔ no cross-clock.
- **L-DB-C (same-snapshot poison).** Snapshot mutated between check and authorize ⇒ fire-True⇒accept breaks (red).
- **L-DB-D (fire-once + refire).** Witness latch once/episode (`:1841`); post-reset refire; ep1≡ep2.
- **L-DB-E (flag-OFF byte-neutral, BOTH grasp_actuation).** `route_c1_pin=False`: ik_chord path byte-identical to
  baseline `469435014f` (phys/obs/reward/done) for grasp_actuation=True (E_gT) AND False (E_gF). No new npz fields.
- **L-DB-F (route_steps hoist neutrality).** grasp_actuation=True: hoisted == old `:1251` value every step (byte);
  False: `route_steps` now defined, consumed only by the pin label.
- **L-DB-G (K debounce validation — §9.7.8 binding, deterministic).** spurious = <K consecutive inside-capture-
  at-depth (§9.7.9/R1). Bars: (i) **settled** approach (dwell ≥K) FIRES within K+1 frames (positive control);
  (ii) a **<K dwell** transit (drive the identity body through capture-at-depth for exactly K−1=2 frames then
  out) does NOT fire (K debounce — negative control). Freeze the exact deterministic path + per-frame inside-
  count (K−1=no-fire / K=fire). ⇒ validates the debounce MECHANISM at design-time. Residual (live-policy fire
  distribution) = post-launch monitor (§carry) — training-ready does NOT wait on it (circularity closed by
  fire⊆retention).
- **L-DB-H (hold-era label trace).** Under `hold_mask` (injected via cfg; route_t clamped, FF `:1213` idiom):
  `fired_at_frame` is provenance-only / non-gate; assert behavior (fire predicate) is hold-independent.
- **L-DB-I′ (fire ⊆ retention — §9.7.9/R3, replaces L-DB-I).** For EVERY fire in the WITH run, assert the fired
  snapshot has **dx ≤ 3.5mm AND z ∈ [821,831]mm** (fire strictness ≥ retention). ⇒ a fire is always a genuine
  seat; no loose weld can fabricate G6 (structural, not a margin). (The old "3.5-5mm loose weld" is impossible on
  the authorized path — the authorizer rejects >3.5mm.)
- **L-DB-J (bypass-audit continuity — exact test ID).** `test_route_reward_identity_guards.py::test_c1_pin_bypass_audit_then_clear` (existing pattern): an `eq_active` flipped without the authorizer is audited-then-cleared on reset, unchanged by ik_chord placement.
- **L-DB-K (perf hot-path — wc=1 single-proc, R4).** Measure **wc=1 single-process ik_chord pin OFF vs ON**
  (fork-B runs 4 proc × wc=1; the pin reads world-0 only ⇒ per-proc cost is the wc=1 cost). Metrics:
  transitions/s + peak GPU mem + RSS, matched window/timer, fresh tag, positive overlap. **Bar = throughput
  ratio ON/OFF ≥ 0.8** (frozen; Rs override). <0.8 ⇒ mandate a batched/sliced body_q read.
- **L-DB-L (M2 loader consumer assert — V0/prelaunch).** Exact loader command + expected result: the DAPG/BC
  loader ingests the (d-a) additive npz keys without error (additive-key tolerance, D0-R3). Run at V0/prelaunch.

## §4 acceptance (§9.7.6 + §9.7.8/9.7.9)
- **positive**: genuine-seat fire (capture∧depth∧K, z≤831); L-DB-A WITH (G4∧G5∧G6 SUCCESS); L-DB-B fire≺release;
  L-DB-G (i) settled→fire; **L-DB-I′ fire⊆retention**.
- **negative / binary**: L-DB-A WITHOUT (G3→escape→drop→terminate-before-G4); L-DB-G (ii) <K dwell→no fire;
  L-DB-C poison (red); L-DB-D fire-once.
- **circularity closed (§9.7.8/9.7.9)**: L-DB-G validates the K debounce at design-time (binding); fire⊆retention
  (L-DB-I′) makes every fire a genuine seat ⇒ no gate②-corrupting spurious ⇒ training-ready = the three keys
  (no live-policy K key). Live-policy fire distribution = post-launch monitor only.
- **NOT the (d-a) [242,250] step bar** (no policy-drive onset window).

## §5 change / landing protocol (R5 — fixed order)
**gate order**: pre-mutation **L3 CC-Debate** → **rule-check stage2** (done `082baa1ca6`-era) → **tests-only
patch (baseline red)** → **impl + probe** → **/pre-check (concrete code)** → **land** → **post-land tests/hooks**
→ **two-key** (p5 design + pN evidence).
1. **tests-only patch first** (baseline `469435014f`: new tests FAIL with expected signature, NOT collection
   error; landed PASS). New test IDs (in `test_route_reward_identity_guards.py`): `test_ik_chord_pin_call_placement`
   (pin called pre-step in ik_chord) · `test_route_steps_hoist_unconditional` (defined when grasp_actuation=False)
   · `test_ik_chord_pin_fire_subset_retention` (L-DB-I′) · `test_ik_chord_flagoff_byte_neutral_both_grasp` (L-DB-E).
   Existing 31 continue to PASS.
2. **impl** = explicit-path atomic (stage only §1-IN; config-hunk isolation if any NOT-MINE hunk; record
   path/hunk/aggregate staged sha; `validate.sh --staged-only` PASS).
3. **claim manifest**: baseline source sha, clean status, IN exact paths, frozen diff sha, changed-source set.
4. **isolated worktree format**: `VIRTUAL_ENV=/home/rlrk/env_isaaclab7 ./isaaclab.sh -f` PASS after normalization
   (porcelain 0).
5. **post-land**: pytest (31+new) exit0 · hooks porcelain 0 · probe legs §3 · two-key.
6. **landing binds (exact SHA/status at landing-time)**: fork-B **V0 acceptance** + gate② **L3 DoR**.

## §Q status
- **Q-1 sync = RESOLVED** (§2, warp 1.13.0 `types.py:4083-4086`). ✅ pN-confirmed.
- **Q-2 deterministic-probe** = validates MECHANISM + K debounce (L-DB-G); live-policy = post-launch monitor.
- **Q-3 hoist neutrality = L-DB-F** ✅. **Q-4 flag-OFF byte = L-DB-E** (both grasp_actuation) ✅.

## §carry / deferred
- **deferred (post-launch monitor)**: live-policy fire distribution ONLY (design-time debounce is binding via
  L-DB-G). Pathology → §8.2/§9.7.3 re-open.
- **landing binds**: fork-B V0 + gate② L3 DoR at landing-time.
- ⛔ **training-ready LOCKED** ((d-a) ∧ (d-b) two-key ∧ cell-2, §S4.7).

## §10 [RESULT] (stub — filled at probe/land time)
_pending pN v0.3 readback → L3 CC-Debate → tests-only red → impl + probe → /pre-check → land → two-key._
