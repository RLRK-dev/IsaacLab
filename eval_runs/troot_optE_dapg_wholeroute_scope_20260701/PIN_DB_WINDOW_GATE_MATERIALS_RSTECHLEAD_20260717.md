# (d-b) D-b window gate — materials (/reward-design 4 artifacts + §9.3 measurements)

**Created:** 2026-07-17 21:29 JST · **Author:** RS-TECH-LEAD (w2:p4) · **Node:** pin (d) — (d-b) half
**Governing framing:** `PIN_D_TRIGGER_CHARTER_VTDESIGN_20260717.md` §9 (banked `463f156fc6`). This doc = the
materials the §9 gate chain requests; **rulings are p5's (§9.x)**. Builder does not self-derive the design.
**Producing commit for all code cites:** HEAD `5b0de67402`.

**What (d-b) changes (one line):** call the existing drive-agnostic pin trigger `_maybe_activate_c1_pin`
(`newton_route_env.py:1821-1860`) from the **ik_chord** (policy/residual) drive loop, at the **pre-step**
position (after joint assign `:1273` / grip `:1278`, before `_physics_step_all :1281`), with `route_steps`
hoisted unconditionally. No reward term is added; no new kinematic exception (INVARIANT #5). The pin welds
geometry; the reward reads geometry (charter §4-4). So (d-b)'s reward impact is **indirect**:
pin fire → C1 retention → C1 seat geometry preserved → the reward's `c1_retained` / `c1_escape` legs.

Constants (rc = `envs/route_env_config.py`, task_config = `configs/task_config.py`): SEAT_LAT_BAR_M=**3.5mm**
(`rc:174`) · SEAT_Z_LO/HI=**821/836mm** (`rc:175-176`) · Z_FIRE_DEPTH_M=**831mm** (`rc:185`) ·
PIN_TRIGGER_DWELL_K=**3 frames** (`rc:181`) · _SEAT_MISS_DX_M=**9.0 m** (`env:1301`) ·
DROP_LATERAL_DEV_MAX_M=**60mm** (`env:412`) · G_PHASE_BONUS=**+5** (`rc:104`) · G6_TASK_BONUS=**+200**
(`rc:105`) · TIME_PENALTY=**-0.01** (`rc:106`) · TERM_PENALTY=**-10** (`rc:107`) · K_ROUTE_SEAT=**10 RL steps**
(`rc:84`) · CABLE_RADIUS=**4mm** (`task_config:137`).

> **⚠ R3 forward-only correction (2026-07-17, per pN v0.2 + p5 §9.7.9 `082baa1ca6`):** two fixes to this doc.
> (1) **`_SEAT_MISS_DX_M` = 9.0 m** (a fail-closed MISS *sentinel* checked by exact equality `dx==9.0`, NOT a
> 9.0mm lateral distance) — the earlier "9.0mm" was a unit error (escape logic unchanged: exact-sentinel).
> (2) There is **no "fire capture ~5mm > retention 3.5mm" loose-weld margin**: `clip_capture_check`
> (`route_executor.py:981`) and `authorize_clip_pin` (`:1024`) both use `clip_capture_predicate(…,
> SEAT_LAT_BAR_M=3.5mm, …)` (identity); `match_tol_m=5e-3` (`:1014`) is the eq world-position resolution, not the
> capture width. The correct non-crutch argument is **fire strictness ≥ retention** (fire lateral 3.5mm same,
> fire z `[821,831]` ⊆ retention z `[821,836]`) ⇒ every fire is a genuine seat (stronger than a margin). See
> prereg §0/§3.1 L-DB-I′.

---

## Artifact 1 — Reward Signal Reachability Table

The whole-route reward = latched-monotonic ORDERED G1-G6 (`_compute_rewards_dones_batch` `env:1593-1727`).
The (d-b)-relevant question is not "does (d-b) add a dead zone" but **"under policy (ik_chord) drive, is
G4-G6 reachable at all"** — because the post-G3 escape guard drops the episode when C1 leaves its seat.

| G | Predicate (formula) | Gate to reach it | Reachable WITHOUT (d-b) pin (current ik_chord) | Reachable WITH (d-b) pin | Dead zone? |
|---|---|---|---|---|---|
| G1 | p1 = grip_r,l≥0.5 ∧ contact_r,l ∧ \|span−92.4mm\|≤8mm (`:1680`) | from P0 | **yes** | yes | no |
| G2 | p2 = held_z−z_rest ≥ 40mm (`:1685`) | after G1 | **yes** | yes | no |
| G3 | p3 = c1_seated ∧ ph≥2; c1_seated = dx_c1≤3.5mm ∧ 821<z_c1<836mm (`:1686/:1400`) | after G2 | **yes** (seat is reached; pin fires here) | yes | no |
| G4 | p4 = r_reach≤tol ∧ contact_r (`:1687`) | after G3, **while C1 stays seated** | **NO** — regrasp for C2 moves the cable; the C1 identity crossing is lost (`_seat_metrics`→MISS 9.0 m) or deviates >60mm ⇒ `c1_escape_after_seat`=True (`:1443-1457`) ⇒ dropped ⇒ **−10, terminate** before G4 latches | **yes** — pin welds the C1 identity body at seat ⇒ dx_c1 stays ≤3.5mm ⇒ no escape | **YES (without pin)** |
| G5 | p5 = c2_seated (`:1688`) | after G4, C1 still held | **NO** (same escape deadlock) | yes | **YES (without pin)** |
| G6 | c2_honest ∧ **c1_retained** ∧ ¬dropped ∧ span_ok, sustained 10 RL steps (`:1704-1711`) | after G5 | **NO** — c1_retained = c1_seated at C1 (`:1629`); lost once the cable routes to C2 ⇒ g6_live never sustains | yes — pin holds C1 ⇒ c1_retained stays True through the C2 route | **YES (without pin)** |

**Reading:** the CURRENT ik_chord (policy) path has a **hard dead zone at G4-G6** — this is the RS71 §4
**FIDELITY BOUNDARY** (Rs DECISION B2, 2026-06-25: cable = 1-DOF planar bender, routing is kinematic ⇒ a
pin-less RL env cannot represent the task; cited by section+decision, not line — the RS71 line index drifts)
expressed as a reward-reachability failure. **(d-b) removes the
dead zone**; it does not create one. The pin gradient path is not a new reward term — it re-opens the
existing G4/G5/G6 gradient that the escape guard otherwise closes.

**Fire-gate reachability (the pin's own gate):** the fire predicate = capture ∧ (z≤831mm) ∧ K=3-dwell
(`:1850-1856`). At G3 (C1 seated: dx_c1≤3.5mm, z in [821,836]), the identity body is inside the authorized
clip capture volume at depth. So the fire gate is **reached by the SAME motion the G1-G3 rewards already
incentivize** (grasp→lift→seat). No separate reward is needed to drive the pin; it rides the seat incentive.
⇒ no deadlock introduced by the fire gate.

## Artifact 2 — Causal Gate DAG

```
policy residual action (α-6D)  [ik_chord: _apply_actions_batch :1158]
  -> arm EE moves the cable
  -> C1 identity seat body enters the authorized clip capture volume, descends to z <= 831mm
      --[GATE A: capture AND depth AND K=3 consecutive frames]-->   (reached via G1-G3 seat rewards; NOT a deadlock)
          -> pin fire: authorize_clip_pin welds eq(identity seat body @ seat_world)  [env:1857, route_executor authorizer]
              -> C1 identity body held at the groove  =>  _seat_metrics(cable_pos,C1) dx_c1 stays <= 3.5mm
                  -> c1_escape_after_seat = False  [env:1443-1457]   *** removes the post-G3 drop deadlock ***
                      -> policy regrasps + routes to C2   -> G4 (+5), G5 (+5)
                          -> c1_retained = True (pin) AND c2_honest (C2 seated)
                              --[GATE B: g6_live sustained K_ROUTE_SEAT=10 RL steps]-->
                                  -> G6 SUCCESS (+200)

WITHOUT (d-b): the branch after G3 is
  -> policy routes toward C2 -> C1 identity crossing lost (MISS 9.0 m) OR |dev|>60mm
      --[c1_escape_after_seat = True]--> dropped -> r=-10 -> terminate   *** DEADLOCK: G4-G6 unreachable ***
```

- **GATE A** (pin fire) is annotated: value-at-P0 = not captured (cable at rest, dx_c1 = MISS); threshold =
  capture∧z≤831∧K=3; the reward signal driving toward it = G1-G3 (grasp/lift/seat). Reachable ⇒ not a deadlock.
- **GATE B** (G6 sustain) requires c1_retained held for 10 steps — only the pin makes this holdable under a
  policy that must simultaneously route C2. This is the load-bearing coupling (d-b) supplies.

## Artifact 3 — Ground-Truth Values

Values are geometric (the reward reads `cable_pos` via `_seat_metrics`), computed from the constants above.

| State | dx_c1 | z_c1 | c1_seated / c1_retained | c1_escape (post-G3) | dropped | r (step) | latch/notes |
|---|---|---|---|---|---|---|---|
| P0 (rest, cable not at C1) | MISS 9.0 m (no C1Y crossing) | — | False | n/a (pre-G3) | False | −0.01 | move toward cable |
| C1 approaching | ~8→4mm, descending | 840→832mm | False (dx or z out) | n/a | False | −0.01 | G1,G2 latch en route |
| **C1 seated (pre-fire)** | ≤3.5mm | ∈[821,836], ≈831 | **True** | False | False | **+5 (G3)** | fire gate now capture∧depth True; dwell begins |
| C1 seated, dwell=3 (**FIRE**) | ≤3.5mm | ≈831 (≤831 depth) | True | False | False | −0.01 | **PIN FIRES** (eq weld @ seat_world) |
| Route→C2, **WITH pin** | ≤3.5mm (held) | in-band (held) | True | **False** | False | +5 (G4/G5) | C1 held; regrasp+C2 proceed |
| Route→C2, **WITHOUT pin** | → MISS 9.0 m (crossing lost) | — | False | **True** | **True** | **−10** | **terminate — deadlock** |
| C2 seated (WITH pin), g6_live×10 | ≤3.5mm (held) | in-band | True (c1_retained) | False | False | **+200 (G6)** | c2_honest∧c1_retained∧¬drop∧span_ok |

The WITHOUT-pin row is the current ik_chord behaviour and is the concrete deadlock; the WITH-pin rows show the
same states made reachable. Note the fire is depth-gated at 831mm: a rim catch (~835.7mm) would leave <0.3mm
to the 836mm retention ceiling and elastic-restore out (charter §8.11.2 — why Z_FIRE_DEPTH is 831, not the rim).

## Artifact 4 — Episode Dynamics Trace (policy drive, WITH (d-b) pin)

```
Step 0  : P0. obs shows cable at rest. Best action: grasp (span→92.4mm, contact). -> G1 (+5) when p1.
Step a  : lift held_z +40mm. -> G2 (+5).
Step b  : route cable to C1, descend into groove. dx_c1→3.5mm, z→831mm. -> G3 (+5). ph>=2.
          Fire gate: identity body in capture volume at z<=831 -> dwell counts 1..
Step b+ : dwell reaches K=3 physics frames -> PIN FIRES (eq weld identity seat @ C1). c1_pin_witness set.
Step c  : regrasp window (G4). Arms re-cage for C2. C1 held by pin -> dx_c1 stays <=3.5mm ->
          c1_escape=False -> NO drop. -> G4 (+5) when r_reach<=tol.
Step d  : route to C2, seat it. c2_seated -> G5 (+5). c1_retained still True (pin).
Step e..e+9 : g6_live = c2_honest AND c1_retained AND not dropped AND span_ok, held 10 steps -> G6 (+200). SUCCESS.

WITHOUT (d-b): at Step c the cable's C1 crossing is lost as the arms move to C2 -> c1_escape -> dropped ->
r=-10 -> terminate. The episode can never reach G4. (This is the current policy-path behaviour.)
```

Dynamics note: the pin does not change the *policy's* action space or the G1-G5 shaping; it changes the
*physics* so that the post-G3 states the policy must pass through (regrasp, C2 route) no longer self-terminate.

## §9.3 measurements (per-Q, for the p5 ruling)

- **(i) ik_chord pre-step body_q read [Q-Db1/Q-Db2].** At the proposed placement (after `joint_q.assign :1273`
  / `apply_recorded_grip :1278`, before `_physics_step_all :1281`), `_state_0.body_q` still holds the PREVIOUS
  physics frame — `joint_q.assign` writes joint_q/control, not body_q; only `_physics_step_all` advances body_q.
  This is the SAME single-clock as the FF layout (call `:1225` before step `:1226`), so §8.13's `run_start+K`
  off-by-one transfers unchanged. **Probe item (implementation-time):** confirm a `wp.synchronize()` is present
  before the pin's `body_q.numpy()` read (the reward site does this at `:1595`); the FF call currently relies on
  the loop's step sync. **The (d-a) hard fire_step bar [242,250] does NOT transfer** — it was the FF-replay
  recording-onset window; under policy there is no recording onset, so the (d-b) acceptance is fire ≺ release +
  the geometric predicate, not a step-index bar (charter §9.2).
- **(ii) training-active ik_chord sub-modes + route_t [Q-Db3].** ik_chord × grasp_actuation:
  (a) grasp_actuation=True (comp3 R2 path) → `route_steps` computed at `:1251` (available); (b)
  grasp_actuation=False (pure IK) → `route_steps` undefined at the loop body. The route task holds the cable via
  the recorded grip staircase, so **training runs (a)** (inference: the whole-route policy needs grip; confirm
  against the trainer cfg `grasp_actuation` at trainer-time — no trainer running now). **Direction (Q-Db3 =
  label-supply, not fire-gate):** hoist `route_steps` unconditionally at the ik_chord loop head (mirror FF
  `:1210`, depends only on `route_t`), so `fired_at_frame` (`:1846/:1858`) has a defined label in every sub-mode.
  The FIRE decision is `route_steps`-independent (verified: fire uses body_q only, `:1849-1856`).
- **(iii) spurious-dwell worst-case + empirical K DoD [Q-Db4].** K=3 physics frames debounces short transits of
  the capture volume at depth. A slow policy swing-through that lingers ≥3 frames inside capture-at-depth would
  fire "early" — but capture∧depth IS a geometric seat, so an early fire welds a genuine seat (the intent), not a
  spurious one; the only true-spurious case is a transient pass that never settles. **DoD (empirical, DEFERRED —
  needs a running policy):** on policy rollouts, fire-vs-first-true-seat lag ≤ small bound AND no fire on a
  transit that leaves the volume within the same RL step; if violated, raise K. **Design-time (now):** K stays a
  config constant (`rc.PIN_TRIGGER_DWELL_K`); the worst-case transit bound = capture-volume extent ÷ max cable
  speed (to be computed from the capture geom + α-6D residual scale 15mm/step `:401`) — offered as an options
  input, not a ruling.
- **(iv) pin→seat→reward causal chain + gate② dependency [Q-Db6].** DAG = Artifact 2. gate② = the seat predicate
  ruling `REWARDDESIGN_GATE2_SEAT_PREDICATE_RULING` (`_seat_crossing :1304`, `_seat_metrics :1402`), the SAME
  instrument the pin's retention feeds. Dependency table:

  | link | direction | why | risk if wrong |
  |---|---|---|---|
  | pin fire-correctness → seat-metric validity | pin must fire ONLY at a true seat (capture∧depth guards this) | a mis-fired weld would hold the cable off-groove; `_seat_metrics` would then read the welded-wrong geometry as "seated" | false c1_retained (exploit); guarded by capture∧depth∧K |
  | pin retention → c1_escape/c1_retained | held identity body keeps dx_c1 small | this is the intended coupling (removes the deadlock) | none — this is the design goal |
  | pin retention → gate② seat metric during C2 route | pin holds C1 while C2 is measured independently | the two seats read independent crossings; pin does not distort C2's metric | needs the RATIFIED gate② seat metric (owner-chain) |

  **Landing sequences with the gate② owner chain.** ⚠ Status reconcile (not assumed): p5 recap (2026-07-17)
  says gate② complete; a PLAN-KEEPER note cited gate② FAIL / owner-chain pending. This materials doc grounds the
  coupling against `_seat_metrics` as it stands at HEAD `5b0de67402`; the (d-b) landing must bind to the gate②
  decision-of-record current at landing-time. Owners (p5/p6/pN) to reconcile before (d-b) lands.

## Gate decision (materials-side; the ruling is p5 §9.x)

```
[REWARD DESIGN GATE — (d-b), materials-side]
Reachability : PASS — (d-b) REMOVES the G4-G6 dead zone (post-G3 c1_escape deadlock under policy drive);
               the pin fire gate is reachable via the existing G1-G3 seat incentive (no new deadlock).
Causal DAG   : PASS — no deadlock introduced; GATE A (fire) reachable, GATE B (G6) enabled by pin retention.
Ground-truth : PASS — WITHOUT-pin row reproduces the concrete deadlock; WITH-pin rows are self-consistent.
Episode trace: PASS — policy reaches G6 with the pin; without it the episode self-terminates at the C2 route.

GATE (materials-side): PASS to proceed to the p5 §9.x ruling + prereg, WITH deferred legs:
  - empirical K under policy drive + spurious-fire rate (Q-Db4 DoD) — needs a running trainer (fork-B V0).
  - gate② decision-of-record reconciliation before landing (Q-Db6).
  - implement/land aligns with fork-B substrate V0 (charter §9.5); design proceeds now.
⛔ training-ready stays LOCKED: (d-a) ∧ (d-b) ∧ cell-2 (§S4.7). This gate unlocks neither by itself.
```

## Open items handed to p5 (§9.x ruling)
1. Q-Db1/2: ratify pre-step placement (`:1281`-pre) + single-clock off-by-one transfer + the sync requirement.
2. Q-Db3: ratify unconditional `route_steps` hoist (label-supply); confirm fire is route_steps-independent.
3. Q-Db4: ratify K=3 as the design-time constant + the empirical-K DoD wording (deferred leg).
4. Q-Db5: hold-era `fired_at_frame` label semantics under `hold_mask` (probe uses no hold; ik_chord may).
5. Q-Db6: ratify the pin→seat→reward coupling + the gate② dependency/sequencing (+ status reconcile).
6. Acceptance for (d-b): confirm it is the geometric predicate + fire≺release + the deadlock-removal legs
   (NOT the (d-a) [242,250] step bar).
