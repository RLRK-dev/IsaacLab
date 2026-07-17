# (d-b) D-b window gate — prereg (impl + probe + acceptance)

**v0.2 — 2026-07-17 22:45 JST** · **Author:** RS-TECH-LEAD (w2:p4) · **Node:** pin (d) — (d-b) half
**Governing:** charter §9 framing (`463f156fc6`) + §9.7 6-item RATIFY (`bd1c534678`). **Baseline code = HEAD
`469435014f`** (code identical to `5b0de67402`). **Status:** DRAFT — folds pN v0.1 conditions B1-B5
(HOLD, 2026-07-17 21:5x); awaiting pN re-readback + p5 confirm on the B1 acceptance refinement. **⛔ [CHANGE]
STOP until pN v0.2 readback PASS.** 0-code, training-ready禁止 continues.

**One line:** call the drive-agnostic `_maybe_activate_c1_pin` from the ik_chord (policy) drive loop at
pre-step, with `route_steps` hoisted unconditionally, so the G4-G6 dead zone (post-G3 C1 escape → drop) is
removed under policy drive. No reward term; no new kinematic exception.

## §0 v0.2 fold record (pN v0.1 conditions B1-B5)
- **B1 (CRIT) K/training-ready circularity → closed** (§4-A binding adversarial sweep + §carry): the spurious-
  fire rejection K is validated at prelaunch by a **deterministic adversarial speed-sweep binding leg**, NOT
  deferred; only live-policy fire-rate is post-launch monitored. M2 loader assert moved to V0/prelaunch (§1).
  ⚠ touches the acceptance/deferral boundary of §9.7.3 → **flagged to p5 for confirm** (refinement, not reversal).
- **B2 (MAJ) provenance freeze → §3.0** (verbatim commands, A-pair, frozen cfg/sha/fingerprint/bracket).
- **B3 (MAJ) binary bars → §3/§4** (WITHOUT reaches G3 then drops before G4; WITH latches G6 SUCCESS; loose-weld
  named leg; bypass-audit exact test ID).
- **B4 (MAJ) sync/clock/perf → §2/§3**: **Q1 RESOLVED** — warp **1.13.0** (env_isaaclab7, verified) `array.numpy()`
  guarantees a synchronous device-to-host copy (`warp/_src/types.py:4083-4086` docstring: "a synchronous
  device-to-host copy … will be automatically performed to ensure that any outstanding work is completed") ⇒
  **no extra `wp.synchronize`, no sync fork** (this is why the FF pin `:1225` already reads body_q without an
  explicit sync). Call order fixed; fire≺release single-clock; hold-trace + perf legs added.
- **B5 (MAJ) landing protocol → §5** (tests-only patch first, claim manifest, gate SHAs, explicit-path atomic,
  isolated-wt format, post-land, V0+gate②-L3 DoR).

## §1 scope
- **goal**: place the (d-a) live-geometric pin trigger into the **ik_chord** (default/policy) drive branch.
- **IN**: (1) unconditional `route_steps` hoist; (2) `_maybe_activate_c1_pin` at ik_chord pre-step; (3) probe
  `pin_db_window_probe.py`; (4) test additions (§5 tests-only patch first).
- **OUT**: FF branch (`:1225`, (d-a)); the pin method body (`:1821-1860`, drive-agnostic); reward/obs/success
  predicates; `task_config.py`; K/Z_FIRE/SEAT bars (§9.7.3); training launch; cell-2 (DoD-7).
- **M2 (from (d-a) §8.14) — moved to V0/prelaunch acceptance (B1):** the DAPG/BC loader additive-key consumer
  assert is asserted explicitly at V0/prelaunch acceptance (not "training-era"). Named as an acceptance item.

## §2 impl design (condition-placement; code after pN readback + [CHANGE] gates)
Baseline ik_chord else-branch (`newton_route_env.py:1245-1283`), two edits:

**(2-1) route_steps unconditional hoist** — replace the `grasp_actuation`-gated block (`:1247-1251`, computes
ONLY `route_steps`) with an unconditional hoist before the loop (mirrors FF `:1210`; expression byte-identical,
verified `[int(self.route_t[w].item()) for w in range(N)]`):
```
            old_fk_jq = np.array(self._per_world_fk_jq[:N])
            route_steps = [int(self.route_t[w].item()) for w in range(N)]  # (d-b): route clock hoisted UNCONDITIONALLY
            for step in range(self.PHYSICS_STEPS_PER_RL):
```
**(2-2) pin call at pre-step, fixed order** — the loop-body order is frozen as `joint assign (:1272-1273) →
grip (:1274-1280) → PIN → physics (:1281)`:
```
                if self._grasp_actuation:
                    self._route.apply_recorded_grip(route_steps, step, hold_mask=...)
                self._maybe_activate_c1_pin(route_steps, step)  # (d-b): ik_chord pre-step live-geometric trigger
                self._physics_step_all(substeps=RL_SIM_SUBSTEPS, sim_dt=RL_SIM_DT)
```
- **pre-step semantics (§9.7.1)**: `joint_q.assign` writes joint_q/control, not body_q; only `_physics_step_all`
  advances body_q. So the pin's `body_q.numpy()` (`:1847`) reads the PREVIOUS frame — same single-clock as FF
  (`:1225` before `:1226`); §8.13 `run_start+K` transfers unchanged.
- **sync (B4/Q1 RESOLVED)**: `body_q.numpy()` auto-syncs (warp 1.13.0, `types.py:4083-4086`) — **no explicit
  `wp.synchronize` added, no impl-time sync fork**. Version-pinned: warp 1.13.0.
- **no-op unless `route_c1_pin`** (method guard `:1841`) → (d-b) flag-OFF path byte-neutral.
- **INVARIANT #5**: reuses the single authorized writer `authorize_clip_pin` (`route_executor.py:987`, called
  `:1857`); no new kinematic exception.

## §3 probe design (`pin_db_window_probe.py`, wc=1, deterministic — no trainer)

### §3.0 provenance freeze (B2 — every run records these, pre/post)
- **command (verbatim, per run)**: `CUDA_VISIBLE_DEVICES=0 VIRTUAL_ENV=/home/rlrk/env_isaaclab7 /home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/pin_db_window_probe.py --run <NAME> --outbox <FRESH_DIR>`
  (exact flags frozen at impl; recorded in [RESULT]).
- **A-pair discipline**: WITH and WITHOUT differ ONLY by `route_c1_pin` on the SAME landed source (one worktree,
  one flag flip) — no code delta between the two.
- **frozen**: baseline `469435014f` · cuda:0 · wc=1 · seed · horizon · recording npz sha · ALL cfg
  (`route_drive_mode`=ik_chord / `grasp_actuation` / scene / `route_t` clock / `route_c1_pin`) · fresh outbox ·
  expected rc=0 · artifact schema (npz field list) · harness self-sha · loaded-source closure + env fingerprint ·
  **pre/post hash bracket: changed source set = [] between runs** (only the flag differs).

### §3.1 legs (binary bars — B3; each PASS/FAIL with an exact predicate)
- **L-DB-A (WITH/WITHOUT deadlock contrast) — core, binary.**
  - **WITHOUT** (`route_c1_pin=False`): MUST reach **G3 latch** (`_g_latched[w,2]=True`), THEN after G3 the C2
    route drives `dx_c1`→MISS(9.0mm) or >60mm ⇒ `c1_escape_after_seat`=True ⇒ `dropped`=True ⇒ **terminate
    BEFORE G4 latches** (`_g_latched[w,3]=False` at done). ⛔ a FAIL *before* G3 is **not acceptable** (the leg
    must exhibit the seat→escape deadlock, not a pre-seat failure).
  - **WITH** (`route_c1_pin=True`): MUST show genuine-seat fire (capture∧depth∧K, z≤831) + audit PASS + retention
    continuity (dx_c1≤3.5mm held) + `c1_escape`=False + **G4 ∧ G5 ∧ G6 all latch, `success`=True** +
    `invalid`=0 + `time_out` per purity. ⛔ "reachable" is NOT sufficient — **actual G6 SUCCESS latch required**.
- **L-DB-B (fire ≺ release, single-clock — B4).** Bar = `route_t_at_fire < _route_release_step` (BOTH in the
  route_t clock; `_route_release_step` at `:558/:584-585`). ⛔ no cross-clock comparison (fired_at_frame is the
  recording-frame label, non-gate). The probe records `route_t` at the fire step.
- **L-DB-C (same-snapshot poison — binary).** The single body_q snapshot (`:1849`) feeds BOTH the capture check
  and the authorizer: a poison variant mutating the snapshot between check and authorize MUST break fire-True⇒
  accept (leg goes red). Fail-able instrument.
- **L-DB-D (fire-once + refire).** Witness latch fires once/episode (`:1841`); post-`_clear_c1_pin` the next
  episode refires; ep1≡ep2 deterministic (byte).
- **L-DB-E (flag-OFF byte-neutral, BOTH grasp_actuation — B4).** `route_c1_pin=False`: ik_chord path byte-
  identical to baseline `469435014f` (phys/obs/reward/done arrays byte-match) for **grasp_actuation=True AND
  grasp_actuation=False** (the hoist must be neutral in both). No NEW npz fields ((d-a) fields already present).
- **L-DB-F (route_steps hoist neutrality).** grasp_actuation=True: hoisted `route_steps` == old `:1251` value
  every step (grip lookup unchanged, byte). grasp_actuation=False: `route_steps` now defined (was undefined),
  consumed only by the pin label.
- **L-DB-G (spurious-dwell adversarial speed-sweep — B1 binding, deterministic).** Drive the identity body
  through the capture volume at depth at a sweep of deterministic speeds (fast transit → slow transit). Bars:
  (i) a **settled** approach (speed→0 inside capture-at-depth) FIRES within K+1 frames (positive control);
  (ii) a **same-RL-step transit** (the body enters AND leaves capture-at-depth within one RL step's frames)
  does NOT fire (K=3 rejects it — negative control); (iii) the slowest transit that still fails to dwell K=3
  does NOT fire. ⇒ K=3's spurious-rejection is validated at design-time (not deferred). Report the fire/no-fire
  boundary vs speed.
- **L-DB-H (hold-era label trace — B4/§9.7.4).** Under `hold_mask` (a held world), record `fired_at_frame` and
  confirm it is provenance-only / drift-loud / non-gate (route_t clamped during hold, FF `:1213` idiom).
- **L-DB-I (loose-weld → no false G6 — B3/§9.7.0).** Force a weld at 3.5-5mm (inside capture ~5mm but outside
  the 3.5mm seat bar): assert `c1_retained`=False AND G6 does NOT latch (`success`=False). The safety margin is
  a NAMED, run leg.
- **L-DB-J (bypass-audit continuity — B3).** Exact test ID (`test_route_reward_identity_guards.py::<id>`): an
  `eq_active` flipped without the authorizer is audited-then-cleared on reset (`_clear_c1_pin`), unchanged by
  the ik_chord placement.
- **L-DB-K (perf hot-path — B4).** pin adds a `body_q.numpy()` sync copy every physics frame (10×/RL-step).
  Measure **matched ik_chord pin OFF vs ON** at **N=1 and N=4** worlds: transitions/s + peak GPU mem + RSS.
  Bar = throughput ratio ON/OFF ≥ **0.8** (recommended; **final bar = p5/Rs**). ⛔ do not implicitly inherit V0
  throughput. Report the numbers; if <0.8, escalate (batch the read / defer to physics-step body_q).

## §4 acceptance (§9.7.6 + B1/B3 folds)
- **positive**: fire at genuine seat (capture∧depth∧K, z≤831); L-DB-A WITH row (G4∧G5∧G6 SUCCESS latch);
  L-DB-B fire≺release (single-clock); L-DB-G positive control (settled → fires).
- **negative / falsifiable (binary)**: L-DB-A WITHOUT (G3→escape→drop→terminate-before-G4); L-DB-G (ii)/(iii)
  (transit → no fire); L-DB-I (loose weld → no G6); L-DB-C poison (red); L-DB-D fire-once.
- **B1 binding (spurious-fire, prelaunch)**: **L-DB-G is a BINDING (d-b) two-key leg** — the spurious-fire
  rejection (K's load-bearing job, §9.7.3) is validated at design-time here, NOT deferred. Only the
  **live-policy fire-rate** is post-launch monitored (§carry). ⚠ p5-confirm: this refines §9.7.3's deferral
  boundary (deterministic sweep binding-now / live-policy deferred).
- **declared delta**: pin fire → retention → `c1_escape`=False (declared geometry coupling, NOT a reward term).
- **acceptance is NOT the (d-a) [242,250] step bar** (no policy-drive onset window, §9.7.6).

## §5 change / landing protocol (B5)
1. **tests-only patch FIRST**: add the new tests (call-placement / order / hoist / L-DB-* IDs). On **baseline
   `469435014f`** they FAIL with the expected signature (NOT a collection error); on the landed bundle they
   PASS. Enumerate existing 31 + the new IDs.
2. **gate SHAs recorded**: L3 CC-Debate bank · rule-check stage2 (done, this session) · /pre-check bank.
3. **impl** = explicit-path atomic: stage only §1-IN paths (config-hunk isolation if any NOT-MINE hunk),
   record path/hunk/aggregate staged sha; `validate.sh --staged-only` PASS.
4. **claim manifest**: target source clean, frozen diff sha, changed-source set enumerated.
5. **isolated worktree format**: `VIRTUAL_ENV=/home/rlrk/env_isaaclab7 ./isaaclab.sh -f` PASS after any format
   normalization (re-run to green; porcelain 0).
6. **post-land**: pytest (31+new) exit0 · pre-commit hooks porcelain 0 · probe legs §3 · two-key (p5 design +
   pN evidence).
7. **landing binds** (record exact SHA/status at landing-time): fork-B **V0 acceptance** + gate② **L3
   training-ratification** decision-of-record.

## §Q status
- **Q-1 (sync) = RESOLVED** (§2, warp 1.13.0 `types.py:4083-4086` — auto-sync, no fork). ✅
- **Q-2 (deterministic-probe representativeness)**: the deterministic probe validates the MECHANISM +
  spurious-rejection (L-DB-G); live-policy dynamics = the post-launch monitor (§carry). Named, not open.
- **Q-3 (hoist neutrality) = L-DB-F** (binary, both grasp_actuation). ✅ specced.
- **Q-4 (flag-OFF byte scope) = L-DB-E** (both grasp_actuation; no new npz fields). ✅ specced.

## §carry / deferred / landing binds
- **deferred (post-launch monitor, trainer):** live-policy fire-rate only (the DESIGN-time spurious-rejection is
  BINDING via L-DB-G — B1). If the live fire-rate shows spurious fires, §8.2/§9.7.3 re-open.
- **landing binds:** fork-B V0 acceptance + gate② L3 DoR at landing-time (§9.7.5; (d-b) is an L3-closure
  component, not blocked).
- ⛔ **training-ready stays LOCKED** ((d-a) ∧ (d-b) two-key ∧ cell-2, §S4.7).

## §10 [RESULT] (stub — filled at probe/land time)
_pending pN v0.2 readback → /pre-check → L3 CC-Debate → impl + probe → two-key._
