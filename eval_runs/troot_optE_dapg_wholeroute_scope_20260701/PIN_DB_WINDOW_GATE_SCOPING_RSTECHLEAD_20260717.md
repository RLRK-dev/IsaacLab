# (d-b) D-b window gate — gate initiation / scoping (RS-TECH-LEAD)

**Created:** 2026-07-17 21:01 JST · **Author:** RS-TECH-LEAD (w2:p4) · **Node:** pin (d) — second half
**Status:** SCOPING — this doc initiates the (d-b) design gate. It poses the design questions; it does **not**
contain a design solution. Design ownership = VT-DESIGN (p5) + Rs. Builder does **not** self-derive placement /
K / label semantics (feedback-design-ask-vt-design-never-self-derive).

**Trigger:** Rs "go" (2026-07-17 ~20:5x), following (d-a) full closure. Next chunk per handoff /
`PIN_D_TRIGGER_PREREG_RSTECHLEAD_20260717.md` §12-6 = D-b window gate.

---

## §0 Where (d-a) left us
- **(d-a) = COMPLETE** (landed `e8edd96a3e`, post-land two-key FULL CLOSE `4bb329317c`, pushed to
  `5b0de67402`, 0 unpushed). It wired the live-geometric pin trigger into the **feedforward** drive branch only.
- **(d) split (governing):** charter `PIN_D_TRIGGER_CHARTER_VTDESIGN_20260717.md` §4-5 + §S4.7
  (`REWARDDESIGN…`, banked `e20d076912`): **(d) = (d-a) + (d-b)**. training-ready unlock =
  **(d-a) two-key ∧ (d-b) two-key ∧ §12-5 cell-2**. (d-a) alone does NOT unlock. ⛔ dirty-tree training stays
  forbidden until all three.

## §1 Grounded code reality (the gap (d-b) must close)
- `route_drive_mode` default = **`ik_chord`** (`newton_route_env.py:496-500`) = the step-level batched-IK +
  residual drive path (the policy/training path). `feedforward` is the recording-replay path.
- **FF branch** (`:1215-1233`): per-physics-frame loop calls `self._maybe_activate_c1_pin(route_steps, step)`
  at **`:1225`**, which is **before** `self._physics_step_all(...)` at `:1226` (pre-step check — the §8.13
  off-by-one `run_start+K` was derived for this pre-step/post-step layout).
- **ik_chord branch** (`:1234-1283`): per-physics-frame loop interpolates jq (`:1253-1254`), assigns
  joint_q/qd (`:1272-1273`), then calls `self._physics_step_all(...)` at **`:1281`** (step at loop **end**).
  **There is NO `_maybe_activate_c1_pin` call in this branch** → in the default drive mode the pin trigger is
  never evaluated (confirms pN B1: grep = 1 call site, FF only).
- `route_steps` in the ik_chord branch is computed **only under `grasp_actuation`** (`:1251`) — availability
  of the route clock for a pin call in this branch is not guaranteed in all sub-modes.
- **gate② interaction is real:** the seat predicate the reward reads lives in the same file
  (`_seat_crossing` `:1304`, ruling `REWARDDESIGN_GATE2_SEAT_PREDICATE_RULING`). The pin provides retention
  (INVARIANT #5 authorized exception) → alters cable geometry → alters what the seat metric reads. So (d-b)'s
  policy-driven fire timing couples to gate②'s reward/obs instrument.

## §2 Design questions for the D-b gate (p5 to frame + rule)
The eval placement / K / label semantics are explicitly deferred to "that gate" by prereg §12-6 and §3 OUT.
Concretely, grounded against the code above:

- **Q-Db1 · eval placement in the ik_chord loop.** Where does the capture/K-dwell check go relative to the
  `_physics_step_all` at `:1281` (loop end)? The FF pre-step layout (`:1225` before `:1226`) does **not**
  transfer directly — ik_chord steps physics at the end of the loop body. Pre-step vs post-step choice
  changes the frame-anchor.
- **Q-Db2 · frame-clock / off-by-one.** Re-derive the §8.13 `run_start+K` frame formula for the ik_chord
  loop structure (recording post-step × check position). The frozen (d-a) anchors (fire 2468 / step 246 /
  830.640mm) were measured on the FF-replay clock; the ik_chord clock is a re-derivation, not a copy.
- **Q-Db3 · route clock availability.** How is `route_steps` supplied to the pin call when
  `grasp_actuation` is off (`:1251` only computes it when on)? Residual-policy sub-modes may not populate it.
- **Q-Db4 · K=3 validity in the policy-drive era.** K=3 physics frames (6.25 ms) was ruled for the FF push
  context (§8.10.1). A slow policy swing-through could dwell K=3 spuriously (CC3-4, prereg §12-6). Empirical
  re-check needs a running trainer (deferred leg, §5); parametric design (K as config, bounds) proceeds now.
- **Q-Db5 · hold-era label semantics.** `fired_at_frame` under held worlds (prereg §2-5 note) — the (d-a)
  probe does not use hold; the label meaning under ik_chord + hold_mask is a D-b design item.
- **Q-Db6 · reward-dynamics interaction.** Under policy drive the fire is policy-driven, not recording-onset.
  Declare the reward-dynamics delta and its coupling to gate② (§1). This may need coordination with the
  gate② owner chain (currently FAIL / owner-chain pending per LEDGER:57-58).

## §3 Invariants NOT in play (unchanged by (d-b))
- INVARIANT #5: clip-retention pin = the ONLY authorized kinematic exception; (d-b) adds no new one — it only
  changes *where/when* the existing single writer (`authorize_clip_pin` → `activate_c1_pin`) is triggered.
- Reward reads geometry, not pin state (charter §4-4). identity-persistence: never null identity mid-episode
  (charter §4-3). fire-once-per-episode latch (witness) maintained (charter §3 Q1).

## §4 Dependencies / deferred legs
- **⭐ multiworld substrate = fork B (this branch `optE-s2-substrate-swap`).** LEDGER:58 = ACTIVE W1 blocker:
  real env at world_count=4 freezes worlds 1-3 cable physics (by-construction: `USE_MUJOCO_CPU=True`
  `task_config.py:116` → CPU `mj_step` integrates only the single-world host template). Rs approved **fork B**
  (2026-07-16「fork Bで進めて」, `ENV_MULTIWORLD_SUBSTRATE_CHARTER_RSTECHLEAD_20260716.md`): CPU-kept +
  **process-parallel, each process = wc=1** = the proven CPU path. **Consequence for (d-b): the multiworld
  eq-inert hazard does NOT apply** — fork B trains at wc=1 per process (the same path (d-a) validated), so the
  pin eq CPU-write is live, not GPU-inert (cf. `reference-newton-eq-three-representations-cpu-write-gpu-inert`,
  which bites only at world_count>1). fork B also makes pin (c) unnecessary (charter §1).
- **(d-b) depends on fork-B substrate V0 acceptance** (PLAN-KEEPER: I0-b CLOSE, **V0 pending**). The ik_chord
  drive path (d-b) wires into is the fork-B per-process training path — design (placement + framing) proceeds
  now in parallel; **implement/land aligns with fork-B V0** (flag if the drive-branch structure changes at V0).
- **trainer not running** (ps: none) → empirical K (Q-Db4) + live-fire policy dynamics = **deferred legs**,
  same pattern as (d-a) DR-ON re-check (M1) and cell-2 (DoD-7). Parametric K design proceeds now.
- **gate② status = reconcile, do not assume.** p5 recap (2026-07-17) says gate② complete (seat-predicate
  ruling + two-keys closed); an earlier PLAN-KEEPER note cited gate② FAIL / owner-chain pending. Q-Db6 coupling
  (pin retention → seat geometry the reward reads) must be grounded against the current gate② decision-of-record,
  not either summary. Owners (p5/p6/pN) to reconcile.

## §5 Gate chain (pattern = (a)(b) / (d-a): materials → ruling)
`this scoping` → **p5 D-b charter (framing)** → my materials (/reward-design 4 artifacts + measurements +
options, per Q-Db1..6) → **p5 ruling** → implement (call-site add + condition, explicit-path atomic) → probe
→ `/pre-check` → **two-key** (p5 design axis + pN evidence axis). Then training-ready = (d-b) two-key ∧ (d-a ✓)
∧ cell-2.

## §6 First action
Dispatch to p5 (VT-DESIGN): request the D-b window-gate design framing (charter or (d)-charter extension),
with §1 grounding + Q-Db1..6. Builder follows materials→ruling. No code touched by this doc.
