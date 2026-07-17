# (d-b) D-b window gate — prereg (impl + probe + acceptance)

**v0.5.2 — 2026-07-18 04:18 JST** · **Author:** RS-TECH-LEAD (w2:p4) · **Node:** pin (d) — (d-b) half
**Governing:** charter §9 (`463f156fc6`) + §9.7 (`bd1c534678`) + §9.7.8/§9.7.9 (`082baa1ca6`) + §9.7.10
(`179a8e390a` + gap-bound fix `c6a7d43b9f`). **Baseline code = HEAD `469435014f`.** **Status:** DRAFT — **B1
design PASS**; C1/C2/C4 + charter fix = PASS-CLOSE (pN v0.5.1). This rev folds the last blocker **C3** (L-DB-H)
+ records-only fixes. Awaiting pN v0.5.2 re-readback. **⛔ [CHANGE] STOP until pN readback PASS.**

**One line:** call the drive-agnostic `_maybe_activate_c1_pin` from the ik_chord (policy) drive loop at
pre-step, `route_steps` hoisted unconditionally, removing the G4-G6 dead zone. No reward term, no new
kinematic exception.

## §0 the two separate questions (§9.7.10, B1 PASS) + v0.5 fold record
- **NON-CRUTCH (can the pin fabricate G6?) = NO, structural, §4-4 ALONE**: `c1_retained` reads the interpolated
  crossing from `cable_pos` INDEPENDENT of pin/eq/witness state (`:1629`). (fire ⊆ retention WITHDRAWN — it
  conflated the fire BODY surface with the retention CROSSING surface.)
- **RELIABILITY (does the pin enable G6?) = the (d-b) crux, EMPIRICAL (L-DB-I″ + L-DB-A)**: FIRE welds the
  identity BODY (`bq[seat_body,:3]`); RETENTION reads the interpolated CROSSING (`_seat_crossing`). Body-fire ⇒
  crossing-retention is MEASURED at nominal, not assumed (single nominal ≠ structural proof).
- **pN v0.4 R1-R5 folds**: R1 → §3.0 (real seed, command=template+argv, leg-specific schema). R2 → L-DB-A full
  `_seated_in_groove` continuity + L-DB-H real hold injection. R3 → §5 test dispositions (AST-red, I″
  positive+poison, L-DB-J narrowed). R4 → materials forward-sync (derivations → empirical; ~7.5mm numeric
  removed) [flagged to p5]. R5 → L-DB-L obs/actions-hash oracle + training-ready formula conjoins V0.

## §1 scope
- **IN**: (2-1) unconditional `route_steps` hoist; (2-2) `_maybe_activate_c1_pin` at ik_chord pre-step; (3) probe
  `pin_db_window_probe.py`; (4) tests (§5). **OUT**: FF branch; pin method body; reward/obs/success predicates;
  `task_config.py`; K/Z_FIRE/SEAT bars; training launch; cell-2 (DoD-7).

## §2 impl design (2 edits)
- **(2-1)** replace the `grasp_actuation`-gated `route_steps` block (`:1247-1251`) with an unconditional pre-loop
  hoist (mirrors FF `:1210`; expression byte-identical).
- **(2-2)** insert `self._maybe_activate_c1_pin(route_steps, step)` between the grip block (`:1274-1280`) and
  `_physics_step_all` (`:1281`). Order frozen: `assign → grip → pin → physics`.
- **pre-step single-clock** (§9.7.1); **sync** = `body_q.numpy()` auto-syncs (warp 1.13.0, `types.py:4083-4086`),
  no fork; **INVARIANT #5** = reuses `authorize_clip_pin` (`:987`).

## §3 probe design (`pin_db_window_probe.py`, wc=1, deterministic ik_chord — no trainer)

### §3.0 provenance freeze (R1 — real values)
- **env**: `/home/rlrk/env_isaaclab7/bin/python` · warp 1.13.0 · **CUDA_VISIBLE_DEVICES=0**, cuda:0.
- **recording (input)**: `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz` · **sha256 `5f1c3f9238f45057011cfad1d010ac43000cb179b76b61d0461733a9075416cf`** · 22 keys.
- **determinism / RNG (R1 → C1)**: the env has **no `seed()` method**; the ONLY RNG is `np.random.uniform` at
  reset (`:1061-1062`), gated by `self.INIT_XY_NOISE>0`. ⚠ **`INIT_XY_NOISE=0.005` is a CLASS attr (`:417`), NOT
  read from cfg** — a cfg entry is INEFFECTIVE. Exact procedure: (1) `np.random.seed(0)`; (2) **after build,
  before the first reset, set `env.INIT_XY_NOISE = 0.0`** (instance override of the class attr) and **hard-assert
  `env.INIT_XY_NOISE == 0.0`** (effective readback); (3) record the effective `env.INIT_XY_NOISE` +
  `np.random.get_state()` digest in the artifact. ⇒ the reset RNG is disabled → fully deterministic (ep1≡ep2).
- **command (TEMPLATE, `<LEG>` expanded at run)**: `CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/pin_db_window_probe.py --cell cell_x0_y0 --leg <LEG> --outbox <FRESH_OUTBOX>/<LEG>`. ⚠ this is a template; **the run-time EXPANDED argv is saved verbatim per leg** in the artifact.
- **cfg (frozen)**: `world_count=1` · `grasp_actuation=True` (E_gF=False) · `route_executor_impl="route_executor"` · `route_recording_npz=<above>` · `g1_scene_align=True` · **`route_drive_mode="ik_chord"`** · `route_c2_scene=True` · `route_c1_pin=<A-pair flag>` · (`route_t_clock=True` only for L-DB-H). · `env.INIT_XY_NOISE` set to 0.0 via the attr-override above (NOT cfg) · **drive** = deterministic zero-residual · **horizon** 900 (`:407`).
- **artifact schema (frozen)**: a **common envelope** (per leg) + **leg-specific payloads FROZEN as INLINE JSON**
  in the same result file (no companion trace file):
  - **common envelope (21 fields, C2)**: `leg`·`expanded_argv`·`fire_step`·`route_t_at_fire`·`fired_at_frame`·`dwell_count`·`fire_body_dx_m`·`fire_body_z_m`·`fire_cross_dx_m`·`fire_cross_z_m`·`c1_retained_at_fire`·**`audit_verdict`**·**`eq_id`**·**`mismatch_class`**·`g_latched`(6)·`success`·`invalid`·`time_out`·`dropped`·`pass`(bool)·`failed_predicates`(list). (audit_verdict added for L-DB-A's genuine-fire+audit requirement.)
  - **leg-specific payloads — FROZEN as INLINE JSON in the same result file (no separate companion, C2)**: L-DB-A → `post_fire_continuity` (per-step {step,dx_cross,z_cross,seated} + min_z/max_z/max_dx/first_fail_step); L-DB-G → `dwell_sequence` (per-frame {inside, dwell, fired}); L-DB-H → `hold_trace` (§3.1 L-DB-H bars); L-DB-I″ → `poison_subcase` ({forced_not_in_groove, leg_went_red}); L-DB-K → `perf` ({transitions_per_s, peak_gpu_mib, rss_mib} × {OFF,ON}).
  - **provenance closure (per run)**: `command`·`cfg`·`recording_sha256`·`loaded_source_closure`·`env_fingerprint`·`harness_self_sha`·`pre_hash`·`post_hash`·`changed_source_set` (=[] for the A-pair).

### §3.1 legs (binary bars)
- **L-DB-A (WITH/WITHOUT deadlock contrast + retention-continuity, R2).**
  - WITHOUT (`route_c1_pin=False`): reach **G3 latch**, THEN C2 route → `c1_escape` (dx→MISS 9.0 m OR >60mm) →
    dropped → **terminate before G4**. ⛔ FAIL before G3 not accepted.
  - WITH (`route_c1_pin=True`): genuine fire + audit + **retention-continuity = at every step from fire to
    G6/done, `_seated_in_groove(dx_cross, z_cross)` = True (dx_cross≤3.5mm ∧ 821<z_cross<836, `:1396-1400`)**;
    record min/max z_cross, max dx_cross, first-fail step. + `c1_escape`=False + **G4∧G5∧G6 latch,
    `success`=True** + `invalid`=0 + `time_out`=0.
- **L-DB-B (fire ≺ release, single route-clock).** `route_t_at_fire < _route_release_step` (`:558/:584-585`).
- **L-DB-C (same-snapshot poison).** Snapshot mutated between check and authorize ⇒ fire-True⇒accept breaks.
- **L-DB-D (fire-once + refire).** Once/episode (`:1841`); post-reset refire; ep1≡ep2.
- **L-DB-E (flag-OFF byte-neutral, BOTH grasp_actuation).** byte-identical to baseline for E_gT/E_gF. No new npz.
- **L-DB-F (route_steps hoist neutrality).** grasp=True: hoisted==old `:1251` (byte); False: defined, label-only.
- **L-DB-G (K debounce validation, frozen frame counts).** deterministic scripted inside-capture-at-depth dwell.
  (i) **≥K dwell** → fires within K+1; (ii) **K−1 dwell** → no fire; (iii) **gap-reset** (`[True]*(K-1)+[False]+
  [True]*(K-1)`, mirrors unit `test_pin_da_dwell_reset_on_gap:482`) → no fire. Record `dwell_sequence`
  per-frame. spurious = <K consecutive (§9.7.9). Residual (live-policy dist) = post-launch monitor.
- **L-DB-H (hold-era label semantics — SYNTHETIC via monkeypatch, C3 v0.5.2).** ⚠ two facts block a naive
  injection: (a) the witness is already latched at fire (`:1841`), so a hold set AFTER the fire cannot validate
  the fire-time label; (b) `step()` OVERWRITES `self._hold_mask_np = self._update_route_sync()` post-physics
  before the route_t-increment site consumes it (`:2043-2045`), so a direct `_hold_mask_np` assignment is
  clobbered. This leg therefore **monkeypatches `env._update_route_sync`** to return a CONTROLLED `hold_mask`
  sequence — **False before the fire window, True across a fixed K-frame/RL-step window that STARTS BEFORE the
  K-dwell/fire, then restored** — so the value the increment site (`:2044-2045`) actually consumes is the
  injected one (route_t clamp guaranteed). **NOT a claim about `_update_route_sync`'s real hold trigger.** Run a
  **paired no-hold vs hold on the SAME body snapshot/path** (hold starts BEFORE the K-dwell/fire). **Frozen bars
  (binary → `hold_trace`)**: (i) `hold_mask` False→True recorded; (ii) `route_t` constant while held; (iii) the
  episode clock increments while held; (iv) the fire decision (body + crossing) is IDENTICAL between the no-hold
  and hold runs (hold-independent); (v) the hold-side fire DOES occur (fire happens while held); (vi)
  `fired_at_frame = step_f[clamped route_t] + sub_i`; (vii) reward/term do NOT read the `fired_at_frame` value.
- **L-DB-I″ (fire ⇒ crossing-retention, R2/R3 — measurement leg PROVEN alive).** At EVERY fire, record BOTH
  surfaces at the SAME snapshot (`fire_body_*` from `bq[seat_body,:3]`; `fire_cross_*` from
  `_seat_metrics(cable_pos,_C1_XY)`) + **hard-assert `_seated_in_groove(fire_cross_dx,fire_cross_z)`=True**.
  **Measurement-alive proof**: a landed **positive control** (a real fire → crossing seated True) AND a
  **crossing poison / forced-false** (inject a not-in-groove crossing → the leg goes RED). ⇒ the oracle is not
  vacuous. per-cell (nominal; cell-2 deferred). Escalation (b) only if a real gap shows.
- **L-DB-J (clear-consumer continuity, R3/C4 — narrowed).** `test_route_reward_identity_guards.py::test_clear_c1_pin_clears_all_audited_fired` (`:279`): the reset CLEAR-CONSUMER handles all audited fired tuples, unchanged by the ik_chord placement. ⚠ **this leg claims clear-consumer continuity ONLY.** Two separate concerns it does NOT claim: (a) mismatch *classification* of an already-obtained fired tuple = `test_pin_da_mismatch_class_fixtures` (a **classifier**, not a bypass detector); (b) real bypass *detection* by the audit = the banked `authorize_clip_pin_controls.py` audit controls. L-DB-J neither subsumes nor depends on (a)/(b).
- **L-DB-K (perf hot-path — wc=1 per-proc; 4-proc = V0 carry).** matched wc=1 single-proc ik_chord pin OFF vs
  ON: `perf` = {transitions/s, peak GPU MiB, RSS MiB}; matched window/timer, fresh tag, positive overlap.
  **Bar = ratio ON/OFF ≥ 0.8** (frozen; Rs override); <0.8 → batched body_q read. **Claim = per-proc only**;
  the **4-concurrent-process × wc=1 aggregate contention is a V0 binding carry**.
- **L-DB-L (M2 loader consumer assert — V0/prelaunch freeze, R5).** ⚠ **V0 pre-run freeze** (deadline = V0
  acceptance; the recording-with-pin-fields + meta paths are produced at V0). Command shape:
  `route_demo_to_bc.py --npz <rec+pin> --meta <meta> --out-dir <fresh> --self-check`. **Oracle = the produced
  `bc_dataset.npz` `obs`/`actions` arrays are byte-identical with vs without the additive pin keys** — compared
  by **dtype + shape + C-contiguous bytes sha256**, NOT the container SHA (the converter embeds
  `source_npz_sha256`, `route_demo_to_bc.py:451`, so the container always differs). rc=0.

## §4 acceptance
- **non-crutch (structural, §4-4 alone)**; **reliability (empirical, L-DB-I″ + L-DB-A continuity, per-cell)**.
- **positive**: genuine fire (capture∧depth∧K, z∈(821,831]); L-DB-A WITH (G4∧G5∧G6 SUCCESS); L-DB-B; L-DB-G(i);
  L-DB-I″ (+ positive control). **negative/binary**: L-DB-A WITHOUT; L-DB-G(ii)/(iii); L-DB-C; L-DB-D; L-DB-I″
  poison (RED).
- **circularity closed**: (i) K debounce prelaunch (L-DB-G) + (ii) §4-4 structural non-crutch.
- **z-windows**: fire z∈**(821,831]** (lower strict `route_executor.clip_capture_predicate:909`; upper ≤831 via
  Z_FIRE_DEPTH `:1851`); retention z∈**(821,836)** (both strict `:1400`).

## §5 change / landing protocol (R3 — dispositions + order)
**gate order**: **L3 CC-Debate** → **rule-check stage2 (bank)** → **tests-only patch** → **impl + probe** →
**/pre-check** → **land** → **post-land** → **two-key**. (rule-check stage2 is NOT yet banked; re-run+bank AFTER
the L3 Debate on this v0.x plan.)
1. **tests-only patch first** — new IDs + per-ID baseline disposition (exact):
   - `test_ik_chord_pin_call_placement` — **baseline RED (runtime)**, substring `AssertionError: ik_chord pin call absent`.
   - `test_ik_chord_route_steps_hoist_unconditional` — **baseline RED via SOURCE/AST assertion** (the baseline block is `grasp_actuation`-gated; grasp=False does NOT consume `route_steps` at runtime, so this is an AST assert that the hoist is unconditional, NOT a runtime NameError). Substring `AssertionError: route_steps hoist is grasp-gated`.
   - `test_ik_chord_pin_fire_implies_crossing_seated` (L-DB-I″) — **landed positive-control PASS** + a **poison
     sub-case** (forced not-in-groove crossing → asserts RED) so the oracle is proven alive; on baseline the
     positive-control is **RED** (no ik_chord fire), substring `AssertionError: no ik_chord fire observed`.
   - `test_ik_chord_flagoff_byte_neutral_both_grasp` (L-DB-E) — **baseline GREEN invariant** (flag-OFF ≡
     baseline by construction; a neutrality guard, NOT baseline-red).
   - Existing 31 continue to PASS.
2. **impl** = explicit-path atomic (stage §1-IN only; hunk isolation; record path/hunk/aggregate staged sha;
   `validate.sh --staged-only` PASS). 3. **claim manifest**: baseline `469435014f`, clean status, IN paths,
   frozen diff sha, changed-source set. 4. **isolated wt format** PASS. 5. **post-land**: pytest (31+new) exit0 ·
   hooks porcelain 0 · probe legs · two-key. 6. **landing binds**: fork-B V0 + gate② L3 DoR (exact SHA/status).

## §carry / deferred / unlock formula (R5)
- **training-ready UNLOCK = (d-a) two-key ∧ (d-b) two-key ∧ cell-2 (DoD-7) ∧ V0 acceptance [incl. L-DB-K 4-proc
  aggregate + L-DB-L loader]** (§S4.7 + the binding carries conjoined — the three keys ALONE are insufficient).
- **deferred (post-launch monitor)**: live-policy fire distribution.
- ⛔ **training-ready LOCKED.**

## §10 [RESULT] (stub) — _pending pN v0.5 readback → L3 CC-Debate → rule-check stage2 → tests-only → impl +
probe → /pre-check → land → two-key._
