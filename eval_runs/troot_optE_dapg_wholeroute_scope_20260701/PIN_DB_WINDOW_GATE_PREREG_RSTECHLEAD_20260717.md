# (d-b) D-b window gate — prereg (impl + probe + acceptance)

**v0.1 — 2026-07-17 22:01 JST** · **Author:** RS-TECH-LEAD (w2:p4) · **Node:** pin (d) — (d-b) half
**Governing:** charter §9 framing (`463f156fc6`) + §9.7 6-item RATIFY (`bd1c534678`). **Baseline code = HEAD
`469435014f`** (code identical to `5b0de67402`; intervening commits are docs). **Status:** DRAFT — pre-bank,
awaiting pN condition review (pN condition pattern, cf. (d-a) prereg B1-B5). 0-code until [CHANGE] gates pass.

**One line:** call the drive-agnostic `_maybe_activate_c1_pin` from the ik_chord (policy) drive loop at
pre-step, with `route_steps` hoisted unconditionally. This makes the pin fire under policy drive so that the
G4-G6 dead zone (post-G3 C1 escape → drop) is removed. No reward term; no new kinematic exception.

---

## §1 scope
- **goal**: place the (d-a) live-geometric pin trigger into the **ik_chord** (default/policy) drive branch, so
  that after C1 is seated the pin welds it and the C2 route no longer self-terminates (charter §9, §9.7).
- **IN**: (1) unconditional `route_steps` hoist in the ik_chord else-branch; (2) the `_maybe_activate_c1_pin`
  call at ik_chord pre-step; (3) the (d-b) probe `pin_db_window_probe.py`; (4) test additions.
- **OUT**: FF branch (unchanged — (d-a) owns `:1225`); the pin method body `_maybe_activate_c1_pin`
  (`:1821-1860`, drive-agnostic, unchanged); reward/obs/success predicates (unchanged — (d-b) is physics
  placement, not a reward edit); `task_config.py`; K value (stays `rc.PIN_TRIGGER_DWELL_K=3`, §9.7.3);
  Z_FIRE_DEPTH / SEAT bars (unchanged); training launch; cell-2 (DoD-7, §12-5); empirical-K (deferred).

## §2 impl design (condition-placement form; code after pN review + [CHANGE] gates)
Baseline ik_chord else-branch (`newton_route_env.py:1245-1283`), two edits:

**(2-1) route_steps unconditional hoist** — replace the `grasp_actuation`-gated block (`:1247-1251`, which
computes ONLY `route_steps`) with an unconditional hoist before the per-frame loop (mirrors FF `:1210`):
```
            old_fk_jq = np.array(self._per_world_fk_jq[:N])
            # (d-b): route clock hoisted UNCONDITIONALLY (was grasp_actuation-gated) so the pin call + the
            # grip lookup both have a defined route_steps in every ik_chord sub-mode. Read HERE (pre-loop):
            # route_t is not incremented until after _apply_actions_batch returns, so it holds THIS step's t_w.
            route_steps = [int(self.route_t[w].item()) for w in range(N)]
            for step in range(self.PHYSICS_STEPS_PER_RL):
```
Rationale (§9.7.2): the fire decision is `route_steps`-independent (pure body_q, `:1849-1856`); `route_steps`
feeds only the `fired_at_frame` label (`:1846/:1858`). Hoisting guarantees the label is defined even when
`grasp_actuation` is False. **Neutrality:** when `grasp_actuation` is True the hoisted value is byte-identical
to the old `:1251` computation (same expression, same pre-loop position) — the grip lookup (`:1278`) is
unaffected (leg L-DB-F).

**(2-2) pin call at pre-step** — insert after the grip block (`:1274-1280`), before `_physics_step_all`
(`:1281`):
```
                if self._grasp_actuation:
                    self._route.apply_recorded_grip(route_steps, step, hold_mask=...)
                self._maybe_activate_c1_pin(route_steps, step)  # (d-b): ik_chord pre-step live-geometric trigger
                self._physics_step_all(substeps=RL_SIM_SUBSTEPS, sim_dt=RL_SIM_DT)
```
Rationale (§9.7.1): pre-step placement — `joint_q.assign` (`:1272-1273`) writes joint_q/control, not body_q;
only `_physics_step_all` advances body_q. So at the call site `_state_0.body_q` holds the PREVIOUS frame, the
SAME single-clock as the FF layout (call `:1225` before step `:1226`), and §8.13's `run_start+K` off-by-one
transfers unchanged. **The call is identical in signature to the FF call** (`route_steps, step`); the method is
drive-agnostic. **No-op unless `route_c1_pin`** (the method's own guard `:1841`), so the (d-b) flag-OFF path is
byte-neutral (leg L-DB-E). ⚠ **sync check (impl-time):** confirm the pin's `body_q.numpy()` read (`:1847`) is
synchronized at pre-step; the reward site does `wp.synchronize()` at `:1595`. If the ik_chord loop does not
already sync before this point, add one (see §Q-1).

## §3 probe design (`pin_db_window_probe.py`, wc=1, deterministic — no trainer)
Drive the ik_chord path with a **deterministic action** (zero residual ⇒ commanded = route base target ⇒ the
recorded route trajectory) at wc=1. This reproduces the seat→route sequence without a policy.

- **L-DB-A (WITH/WITHOUT deadlock contrast) — the core leg.** Same deterministic route, two configs:
  - WITHOUT pin (baseline `route_c1_pin=False`): expect after G3 (C1 seated) the C2 route loses the C1 identity
    crossing ⇒ `c1_escape_after_seat`=True ⇒ dropped ⇒ terminate before G4. (EMPIRICALLY validates the
    materials deadlock claim — the claim is design-time; this leg confirms it.)
  - WITH pin (d-b, `route_c1_pin=True`): expect C1 seat → pin fires (capture∧depth∧K=3) → eq weld → dx_c1 stays
    ≤3.5mm → `c1_escape`=False → no drop → G4/G5 reached; c1_retained holds through the C2 route.
- **L-DB-B (fire ≺ release).** The pin fires before the scheduled release step (`_route_release_step`) — pin
  retains before the arms let go (charter §9.2 acceptance).
- **L-DB-C (same-snapshot poison).** Assert the single body_q snapshot (`:1849`) is passed to BOTH the capture
  check and the authorizer: a poison variant that mutates the snapshot between check and authorize must break
  the fire-True⇒accept invariant (fail-able instrument, cf. (d-a) §8.14 poison leg).
- **L-DB-D (fire-once + refire).** Witness latch fires once per episode (`:1841` guard); after `_clear_c1_pin`
  reset the next episode refires (ep1≡ep2 determinism).
- **L-DB-E (flag-OFF byte-neutral).** With `route_c1_pin=False` the ik_chord path is byte-identical to baseline
  `469435014f` (the pin call is a no-op; the route_steps hoist is value-identical under grasp_actuation) —
  phys/obs/reward/done arrays byte-match. (sim-replay byte-neutral, cf. (d-a) M2 scope; artifact-face additions
  = the (d-a) npz fields already present.)
- **L-DB-F (route_steps hoist neutrality).** Under grasp_actuation=True, the hoisted `route_steps` equals the
  old `:1251` value every step (grip staircase lookup unchanged); under grasp_actuation=False, `route_steps` is
  now defined (was undefined) and only the pin label consumes it.

## §4 acceptance (§9.7.6)
- **positive**: (i) fire at a genuine seat (capture∧depth∧K, not rim — z≤831); (ii) fire ≺ release;
  (iii) deadlock-removal — WITH-pin ik_chord: no c1_escape after C1 seat, G4-G6 reachable.
- **negative / falsifiable**: (i) WITHOUT-pin escape deadlock reproduced (L-DB-A WITHOUT row);
  (ii) a loose weld (3.5-5mm, inside capture but outside the 3.5mm seat bar) does NOT fabricate G6 — c1_retained
  still requires ≤3.5mm (structural safety margin, §9.7.0); (iii) fire-once; (iv) bypass-audit continuity
  (`_clear_c1_pin` audit-then-clear unaffected).
- **declared delta**: the only reward-dynamics change = pin fire → retention → `c1_escape`=False (a declared
  coupling via geometry, NOT a hidden reward term; success still reads geometry, §4-4).
- **acceptance is NOT the (d-a) step bar**: `[242,250]` was the FF-replay recording-onset window; under policy
  drive there is no onset window (§9.7.6). (d-b) acceptance = the geometric predicate + fire≺release + the
  deadlock-removal legs.

## §Q open questions (anticipated pN conditions — to be discharged pre-bank)
- **Q-1 (sync at pre-step):** does the ik_chord loop guarantee body_q is synchronized before the pin's
  `body_q.numpy()` read at pre-step? If not, an explicit `wp.synchronize()` is needed (matching `:1595`).
  Impl-time measurement.
- **Q-2 (deterministic-probe representativeness):** zero-residual ik_chord follows the route base target ≈ the
  recorded route. Is this representative enough of policy drive for the design-time legs? (Empirical policy
  dynamics = the deferred K leg; the deterministic probe validates the MECHANISM, not the policy.)
- **Q-3 (hoist neutrality proof):** show the unconditional hoist is byte-neutral under grasp_actuation=True
  (L-DB-F) and only adds a defined label under False.
- **Q-4 (flag-OFF byte-identity scope):** L-DB-E asserts sim-replay byte-neutrality; the artifact-face
  additions are the (d-a) npz/manifest fields already present — no NEW fields in (d-b) (confirm).

## §carry / deferred / landing binds
- **deferred (trainer):** empirical K + policy fire-rate DoD (§9.7.3) — needs fork-B V0 + a running policy.
- **landing binds:** fork-B substrate **V0 acceptance** (§9.5) + gate② **L3 training-ratification**
  decision-of-record at landing-time (three-layer, §9.7.5 — (d-b) is an L3-closure component, not blocked).
- **M2 (from (d-a) §8.14):** the DAPG/BC loader additive-key consumer assert is (d-b)/training-era's — fold
  into the training-time legs, not this probe.
- ⛔ **training-ready stays LOCKED** ((d-a) ∧ (d-b) two-key ∧ cell-2, §S4.7). This prereg's chunk unlocks
  neither by itself.

## §10 [RESULT] (stub — filled at probe/land time)
_pending impl + probe + /pre-check + two-key._
