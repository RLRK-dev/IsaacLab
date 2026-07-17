# (d-b) D-b window gate — prereg (impl + probe + acceptance)

**v0.4 — 2026-07-18 03:36 JST** · **Author:** RS-TECH-LEAD (w2:p4) · **Node:** pin (d) — (d-b) half
**Governing:** charter §9 (`463f156fc6`) + §9.7 (`bd1c534678`) + §9.7.8/§9.7.9 (`082baa1ca6`) + §9.7.10
(`179a8e390a`, B1 surface fix). **Baseline code = HEAD `469435014f`.** **Status:** DRAFT — folds pN v0.3
B1-B7 (B1 resolved by p5 §9.7.10). Awaiting pN v0.4 re-readback. **⛔ [CHANGE] STOP until pN readback PASS.**

**One line:** call the drive-agnostic `_maybe_activate_c1_pin` from the ik_chord (policy) drive loop at
pre-step, `route_steps` hoisted unconditionally, removing the G4-G6 dead zone. No reward term, no new
kinematic exception.

## §0 fold record + the two separate questions (§9.7.10)
**⚠ non-crutch vs reliability are DIFFERENT questions (p5 §9.7.10, B1 fix):**
- **NON-CRUTCH (can the pin fabricate G6?) = NO, structural, on §4-4 ALONE.** `c1_retained` reads the
  interpolated crossing from `cable_pos` (body positions) INDEPENDENT of pin/eq/witness state
  (`newton_route_env.py:1629`). A not-in-groove cable → False → G6 cannot be fabricated, regardless of the
  body→crossing relation. **"fire ⊆ retention" is WITHDRAWN** (it conflated the fire BODY surface with the
  retention CROSSING surface — different by design, ~7.5mm; §9.7.10 / gate②-fix docstring `:1307-1310`).
- **RELIABILITY (does the pin actually enable G6?) = the (d-b) crux, verified empirically (L-DB-I″).** FIRE
  welds the identity BODY (`bq[seat_body,:3]`, `:1848-1849`); RETENTION reads the interpolated CROSSING
  (`_seat_crossing`, `:1304-1317`). If the weld body cannot hold the crossing ≤3.5mm, `c1_retained`=False →
  G6 unreachable → **(d-b) fails**. So fire⇒crossing-retention is measured, not assumed.

**pN v0.3 B1-B7 folds**: B1 → §4-4 non-crutch + L-DB-I″ (both surfaces). B2 → L-DB-G gap-reset + frozen frame
counts. B3 → §3.0 full sha + exact command + enumerated schema. B4 → L-DB-L exact loader command. B5 → real
test IDs + per-test baseline disposition + gate-order fix. B6 → L-DB-K per-proc + V0 carry. B7 → z-windows.

## §1 scope
- **IN**: (2-1) unconditional `route_steps` hoist; (2-2) `_maybe_activate_c1_pin` at ik_chord pre-step; (3)
  probe `pin_db_window_probe.py`; (4) test additions (§5).
- **OUT**: FF branch (`:1225`); pin method body (`:1821-1860`); reward/obs/success predicates; `task_config.py`;
  K/Z_FIRE/SEAT bars; training launch; cell-2 (DoD-7).

## §2 impl design (2 edits; code after pN readback + [CHANGE] gates)
- **(2-1)** replace the `grasp_actuation`-gated `route_steps` block (`:1247-1251`) with an unconditional pre-loop
  hoist (mirrors FF `:1210`; expression byte-identical).
- **(2-2)** insert `self._maybe_activate_c1_pin(route_steps, step)` between the grip block (`:1274-1280`) and
  `_physics_step_all` (`:1281`). Order frozen: `assign → grip → pin → physics`.
- **pre-step single-clock** (§9.7.1): body_q holds the previous frame; same clock as FF; §8.13 `run_start+K`.
- **sync (Q1 RESOLVED)**: `body_q.numpy()` auto-syncs GPU→CPU (**warp 1.13.0**, `warp/_src/types.py:4083-4086`);
  no `wp.synchronize`, no fork.
- **INVARIANT #5**: reuses `authorize_clip_pin` (`route_executor.py:987`); no new exception.

## §3 probe design (`pin_db_window_probe.py`, wc=1, deterministic ik_chord — no trainer)

### §3.0 provenance freeze (B3 — real values)
- **env**: `/home/rlrk/env_isaaclab7/bin/python` · warp 1.13.0 · **CUDA_VISIBLE_DEVICES=0**, device cuda:0.
- **recording (input)**: `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz` · **sha256 `5f1c3f9238f45057011cfad1d010ac43000cb179b76b61d0461733a9075416cf`** · 22 keys.
- **command (verbatim, per leg)**: `CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/pin_db_window_probe.py --cell cell_x0_y0 --leg <LEG> --outbox eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pin_db_window_probe_out/<LEG>` (fresh `--outbox` per leg; `<LEG>` ∈ {A_with,A_without,B,C,D,E_gT,E_gF,F,G,H,I2,J,K,L}).
- **cfg (frozen)**: `world_count=1` · `grasp_actuation=True` (E_gF sets False) · `route_executor_impl="route_executor"` · `route_recording_npz=<above>` · `g1_scene_align=True` · **`route_drive_mode="ik_chord"`** · `route_c2_scene=True` · `route_c1_pin=<A-pair flag>`.
- **drive**: deterministic **zero-residual action** · **horizon** MAX_EPISODE_STEPS=**900** (`env:407`) · **seed frozen = 0** (`env.seed(0)` at build) · ep1≡ep2.
- **output schema (frozen, per-leg JSON `pin_db_window_probe_result_cell_x0_y0.json`)**: fields = `leg` · `fire_step` · `route_t_at_fire` · `fired_at_frame` · `dwell_count` · `fire_body_dx_m` · `fire_body_z_m` · `fire_cross_dx_m` · `fire_cross_z_m` · `c1_retained_at_fire` · `g_latched` (6-tuple) · `success` · `invalid` · `time_out` · `dropped` · `audit_verdict` · `digest_sha`.
- **A-pair**: A_with vs A_without differ ONLY by `route_c1_pin`; changed-source set = [].
- **freeze also**: expected rc=0 · harness self-sha · loaded-source closure + env fingerprint · pre/post hash bracket.

### §3.1 legs (binary bars)
- **L-DB-A (WITH/WITHOUT deadlock contrast + retention-continuity).**
  - WITHOUT (`route_c1_pin=False`): reach **G3 latch** (`_g_latched[w,2]`), THEN C2 route → `dx_c1`→MISS (9.0 m
    sentinel) or >60mm ⇒ `c1_escape`=True ⇒ dropped ⇒ **terminate before G4**. ⛔ FAIL before G3 = not accepted.
  - WITH (`route_c1_pin=True`): genuine fire + audit + **retention-continuity** (every post-fire step, the C1
    identity crossing `dx_cross`≤3.5mm — the B1 reliability leg) + `c1_escape`=False + **G4∧G5∧G6 latch,
    `success`=True** + `invalid`=0 + `time_out`=0.
- **L-DB-B (fire ≺ release, single route-clock).** `route_t_at_fire < _route_release_step` (`:558/:584-585`).
- **L-DB-C (same-snapshot poison).** Mutate the snapshot between check and authorize ⇒ fire-True⇒accept breaks.
- **L-DB-D (fire-once + refire).** Once/episode (`:1841`); post-reset refire; ep1≡ep2.
- **L-DB-E (flag-OFF byte-neutral, BOTH grasp_actuation).** `route_c1_pin=False`: byte-identical to baseline
  `469435014f` (phys/obs/reward/done) for grasp_actuation=True (E_gT) AND False (E_gF). No new npz fields.
- **L-DB-F (route_steps hoist neutrality).** grasp_actuation=True: hoisted == old `:1251` (byte); False: defined,
  consumed only by the label.
- **L-DB-G (K debounce validation — §9.7.8 binding; frozen frame counts).** Drive the identity body to a
  scripted inside-capture-at-depth dwell (deterministic). Bars (K=3): (i) **≥K dwell** (3 consecutive frames) →
  FIRES within K+1; (ii) **K−1 dwell** (exactly 2 frames then out) → **no fire**; (iii) **gap-reset** (2 frames
  → 1 gap frame → 2 frames) → **no fire** (mirrors unit `test_pin_da_dwell_reset_on_gap:482`, seq
  `[True]*(K-1)+[False]+[True]*(K-1)`). Frozen: per-frame inside-count sequence per bar. spurious = <K
  consecutive (§9.7.9). Residual (live-policy fire distribution) = reliability monitor, post-launch (§carry).
- **L-DB-H (hold-era label).** `hold_mask` injected via cfg (route_t clamped, FF `:1213`): `fired_at_frame`
  provenance-only/non-gate; fire predicate hold-independent.
- **L-DB-I″ (fire ⇒ crossing-retention — B1 reliability, replaces I′).** At EVERY fire, record BOTH surfaces at
  the SAME snapshot: the fire BODY (`fire_body_dx_m`,`fire_body_z_m` from `bq[seat_body,:3]` vs clip) AND the
  interpolated CROSSING (`fire_cross_dx_m`,`fire_cross_z_m` from `_seat_metrics(cable_pos,_C1_XY)`); **hard-assert
  `_seated_in_groove(fire_cross_dx, fire_cross_z)` = True** (dx_cross≤3.5mm ∧ z_cross∈(821,836)). ⚠ single
  nominal cell = evidence, NOT structural proof (per-cell; cell-2 deferred). Escalation (b) [add a crossing gate
  to fire] only if this shows a real gap (would reopen the (d-a) identity predicate §8.1/§8.10.2).
- **L-DB-J (bypass-audit continuity — real existing ID).** `test_route_reward_identity_guards.py::test_clear_c1_pin_clears_all_audited_fired` (`:279`): an `eq_active` flipped without the authorizer is audited-then-cleared on reset, unchanged by the ik_chord placement.
- **L-DB-K (perf hot-path — wc=1 per-proc; 4-proc = V0 carry, B6).** Measure **wc=1 single-proc ik_chord pin OFF
  vs ON**: transitions/s + peak GPU mem + RSS; matched window/timer; fresh tag; positive overlap. **Bar = ratio
  ON/OFF ≥ 0.8** (frozen; Rs override); <0.8 → mandate batched body_q read. **Claim scope = per-proc only**; the
  **4-concurrent-process × wc=1 aggregate contention is a V0 binding carry** (not claimed here).
- **L-DB-L (M2 loader consumer assert — V0/prelaunch, B4).** Command: `/home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/route_demo_to_bc.py --npz <recording-with-pin-fields> --meta <meta> --out-dir <fresh> --self-check`. Oracle: **rc=0** AND the produced `bc_dataset.npz` (obs, actions) is byte-identical with vs without the additive pin keys present in the input npz (the loader reads the (obs,actions) contract and ignores additive keys, D0-R3). Run at V0/prelaunch.

## §4 acceptance (§9.7.6 + §9.7.8/9.7.9/9.7.10)
- **non-crutch (structural, §4-4 ALONE)**: `c1_retained` reads the crossing independent of pin state (`:1629`)
  ⇒ no G6 fabrication. (fire⊆retention withdrawn — not needed.)
- **reliability (empirical, L-DB-I″ + L-DB-A retention-continuity)**: every fire ⇒ crossing seated; the pin
  holds the crossing ≤3.5mm through the C2 route so G6 latches. per-cell (nominal; cell-2 deferred).
- **positive**: genuine fire (capture∧depth∧K, z∈(821,831]); L-DB-A WITH (G4∧G5∧G6 SUCCESS); L-DB-B; L-DB-G(i);
  L-DB-I″.
- **negative / binary**: L-DB-A WITHOUT (G3→escape→drop→terminate-before-G4); L-DB-G(ii)/(iii) (no fire);
  L-DB-C poison; L-DB-D fire-once.
- **circularity closed (R1 re-ground)**: (i) K debounce prelaunch (L-DB-G) + (ii) §4-4 structural non-crutch.
  Live-policy leg = reliability monitor, not a non-crutch gate. training-ready = the three keys.
- **z-windows (B7)**: fire depth z∈**(821,831]** (lower strict `:1400`, upper ≤831); retention z∈**(821,836)**
  (both strict `:1400`).

## §5 change / landing protocol (B5 — fixed order + real IDs)
**gate order** (⚠ rule-check stage2 is NOT yet a bank; the earlier stage2 checklist ran but must be re-run/banked
AFTER the L3 Debate on the final v0.4 plan): **L3 CC-Debate** → **rule-check stage2 (bank)** → **tests-only
patch** → **impl + probe** → **/pre-check** → **land** → **post-land** → **two-key**.
1. **tests-only patch first** — new test IDs + per-ID baseline disposition:
   - `test_ik_chord_pin_call_placement` — **baseline RED** (no pin call in ik_chord), substring `AssertionError: ik_chord pin call absent`.
   - `test_route_steps_hoist_unconditional` — **baseline RED** (route_steps undefined when grasp_actuation=False), substring `NameError`/`UnboundLocalError: route_steps`.
   - `test_ik_chord_pin_fire_implies_crossing_seated` (L-DB-I″) — **baseline RED** (no ik_chord fire to observe).
   - `test_ik_chord_flagoff_byte_neutral_both_grasp` (L-DB-E) — **baseline GREEN** (flag-OFF ≡ baseline; a
     neutrality guard is green on baseline by construction — NOT a red-on-baseline test; listed as a landed-PASS
     invariant, not a baseline-red).
   - Existing 31 continue to PASS.
2. **impl** = explicit-path atomic (stage §1-IN only; hunk isolation if any NOT-MINE hunk; record
   path/hunk/aggregate staged sha; `validate.sh --staged-only` PASS).
3. **claim manifest**: baseline source sha `469435014f`, clean status, IN exact paths, frozen diff sha,
   changed-source set.
4. **isolated wt format**: `VIRTUAL_ENV=/home/rlrk/env_isaaclab7 ./isaaclab.sh -f` PASS (porcelain 0).
5. **post-land**: pytest (31+new) exit0 · hooks porcelain 0 · probe legs §3 · two-key.
6. **landing binds (exact SHA/status at landing-time)**: fork-B **V0 acceptance** + gate② **L3 DoR**.

## §Q status
- Q-1 sync = RESOLVED (warp 1.13.0 `types.py:4083-4086`). Q-2 deterministic-probe = MECHANISM + K debounce.
  Q-3 hoist = L-DB-F. Q-4 flag-OFF = L-DB-E (both grasp).

## §carry / deferred
- **deferred (post-launch monitor)**: live-policy fire distribution (reliability monitor). Pathology → §8.2/§9.7.3.
- **V0 binding carries**: L-DB-K 4-proc aggregate contention; L-DB-L loader assert; fork-B V0 acceptance;
  gate② L3 DoR at landing-time; L-DB-I″ cell-2 (DoD-7).
- ⛔ **training-ready LOCKED** ((d-a) ∧ (d-b) two-key ∧ cell-2, §S4.7).

## §10 [RESULT] (stub — filled at probe/land time)
_pending pN v0.4 readback → L3 CC-Debate → rule-check stage2 bank → tests-only → impl + probe → /pre-check →
land → two-key._
