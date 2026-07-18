# Producer-trace vs current-consumer DIVERGENCE — Phase0 audit + prereg (read-only diagnostic)

**Author (CC1):** RS-TECH-LEAD (w2:p4). **Stamped:** 2026-07-18 23:50 JST.
**Origin:** Rs autonomy grant (2026-07-18) → p4 decides via p5/p6/pN consult, proceeds; Rs confirms via video. Surfaced by Rs's questioning of the FF/ik_chord replay videos.
**Panes (co-decide):** pN OPS-SUP-CODEX = **CONCUR-W-CONDITIONS** (23:31); p5 VT-DESIGN = **CONCUR** (§10.13/§10.13.1, `IKCHORD_GRIPSLIP_FORCEDESIGN_VTDESIGN_20260718.md`, 23:32/23:39); p6 PLAN-KEEPER = new higher-level fidelity item, **DDR row HELD pending verify** (23:30, p4 directive).
**⚠ Honest framing (pN correction, adopted):** "substrate fidelity gap" = **UNPROVEN**. The observed fact is a **producer-trace vs current-consumer divergence**. `golden` is a **producer recording** (`ROUTE_DEMO_RAW_v1`, 7707 physics frames = 771 RL steps, `pin_active` from frame 2544), NOT a current-env success run. Substrate-regression may be claimed ONLY under pN's conditions (same executable/config/input + pre-divergence equality + single controlled delta).

---

## PHASE 0 — canonical-lineage + comparability audit (STATIC, no-sim, GO-now; done this turn)

### 0.1 Lineage / provenance → GOLDEN = TRACE_ORACLE_ONLY
- Golden npz sha256 `5f1c3f9238f4…` has **19 byte-identical copies** across `eval_runs/…` (routeexec_byte_repro/grid81/smoke, seatgate r1/r2/r2b, w0e_81rerun_0211/snapdown, w0e_f1b_150mm, w0e_liftraise, w1_b04/b1/b2/b3a).
- **Sidecar-provenance CONFLICT (pN-flagged):** the SAME npz content carries **two `route_demo_raw_meta.json`** with different code provenance:
  - `w0e_81rerun_snapdown_0537/cell_x0_y0` (canonical, `_GOLDEN`): meta `9346d7c2` / `head_sha bc09a2de` / recorder as-run `2faf8029…` / git_diff `929e…`.
  - `seatgate_verify_20260714/r2b_gate1_golden_4leg`: meta `d8e44a19` / `head_sha 5b7afd5a` / recorder as-run `a59232f8…` / git_diff `b3aa…`.
  - **All RECORDING-CONDITION fields are IDENTICAL** across the two metas: `dt=0.00208333`, `sim_dt=0.000208333`, `sim_substeps=10`, `solver_backend=mujoco`, `n_frames=7707`, `recorder_version=ROUTE_DEMO_RAW_v1`, clips `c1=[0.35,0.15]`/`c2=[0.40,0.00]`, phase_names, arm_q_layout, quat xyzw. They differ ONLY in `head_sha`/`as_run_sha256`/`git_diff_sha256`.
  - **Resolution (fail-closed per pN):** two distinct as-run closures produce byte-identical output ⇒ the historical executable is **not uniquely reconstructable by sha** ⇒ **`GOLDEN = TRACE_ORACLE_ONLY`**. We do NOT claim historical executable reproduction; we treat the golden as a **state trace** for comparison. The recording *conditions* are unambiguous (identical across metas).

### 0.2 Producer/consumer comparability
| field | golden (producer, meta) | consumer (NewtonRouteEnv) | verdict |
|---|---|---|---|
| cable topology | `cable_xyz` shape `(7707, 40, 3)` = **40 segs** | `CABLE_SEGMENTS=40` (`task_config.py:135`) | **MATCH** |
| physics frames / RL | `sim_substeps=10` (=`dt/sim_dt`) | `PHYSICS_STEPS_PER_RL=10` (`newton_route_env.py:404`) | **MATCH (recorded cadence)** |
| RL dt / physics-frame dt | `dt=0.00208333` / `sim_dt=0.000208333` | RL-loop drives 10 frames/RL | **MATCH at recorded cadence** |
| solver nsubstep | **NOT recorded** in golden meta | `RL_SIM_SUBSTEPS=4` (`newton_skill_env_base.py:95`) | ⚠ **CAVEAT** (golden inner-substep unrecorded; likely 4 = same code family, unconfirmed) |
| solver backend | `mujoco` | mujoco-warp fork-B (wc=1 CPU) | MATCH (family); build-detail P1 |
| IC (step0) | `cable_xyz[0]` z = **0.8040** (uniform, 40 segs) | `cable_z_rest=0.803977` (gonow eff) | **z-level MATCH**; full per-seg IC equality = P1 step0 |

**Phase0 comparability verdict = COMPARABLE (with 2 caveats):** (i) golden inner-substep unrecorded (solver-granularity), (ii) full per-segment IC equality deferred to P1 step0. Topology + recorded cadence + IC-z match ⇒ trace-level comparison at the 10-frame/RL cadence is valid. **NOT_COMPARABLE is NOT triggered.**

---

## (b) STATIC predicate-on-golden check (no-sim; predicate-gap vs physics-gap) — method
Evaluate the golden's stored `cable_xyz` (+ `ee_pos_l/r`, `grip_cmd`, `phase_id`) against the **consumer drop predicates** (`newton_route_env.py:410-413` + drop logic `:1653-1660` mirror):
- **A `held_z_floor`:** `grasped ∧ g_latched[1] ∧ held_z < cable_z_rest(0.803977) + DROP_LIFT_MARGIN_M(0.010)`; `held_i=argmin‖cable_xy − mid(ee_l,ee_r)_xy‖`, `held_z=cable[held_i,z]`.
- **B `contact_loss`:** `grasped ∧ contact_loss_count ≥ DROP_CONTACT_LOSS_DEBOUNCE(8)`; contact = `nearest_cable < CONTACT_PROXIMITY_M(0.012) ∧ grip≥0.5`.
- **C `c1_escape`:** `grasped ∧ _c1_escape_after_seat(dx_c1, seated)`; `dx_c1` from `_seat_metrics(cable, C1_xy=[0.35,0.15])`; escape = `dx==MISS(9.0) ∨ >0.060`.
- **Outcome map:** golden trips A/B/C on its own known-good states → **PREDICATE gap** (consumer predicates are stricter than the golden that completed 771 = instrument artifact; #18 "drop" needs re-interpretation; direct case of "a gate validated under the bug"). Golden all-PASS → **PHYSICS gap** → (a).
- **⚠ (b) impl note:** `grasped`/`g_latched` guard state is NOT stored raw in the npz → derive from `grip_cmd` + `phase_id` (documented in the (b) harness). `pin_active` (from f2544) suppresses C after seat in golden.

---

## P1 — current FF+pin telemetry run (FENCED until pN readback; per pN conditions)
- Current FF+pin ONLY, **2 fresh same-seed identical legs** (determinism) + **per-physics-frame earliest-divergence telemetry**; NO ik_chord / no-pin rerun; NO B6/impl.
- Alignment fields (pN): `frame/route_t/phase`, commanded+achieved arm/grip `q/qd`, cable body `q/qd`, `contact_r/l`+grip load, `held_i/z`, C1/C2 geometry, `pin_active/eq/body`, all done-predicates/term-cause. First-divergence **per channel**.
- **P2:** offline detector positive-control (a known single-field perturbation MUST trip) + two-leg first-divergence step/channel agreement.
- **Verdict union:** `{COMPARABLE_LOCALIZED, TRACE_CONTRACT_DIVERGENCE, NOT_COMPARABLE, INCONCLUSIVE}`. Substrate-regression only with pre-divergence equality + single controlled delta.
- **Provenance binding (reuse gonow helpers):** exact commands/expanded argv, fresh outbox+COMPLETE, env_isaaclab7, CVD/device-uuid/MUJOCO_GL, wc1/seed/horizon, package/solver versions, full effective-config, recording + EVERY sidecar sha/disposition, git HEAD+dirty, harness self-sha, import/build/post source-closure (changed/missing/added=[]), rc preserved. **env/physics/source edits FORBIDDEN.**
- **Stop:** sidecar-conflict unresolved / timebase or frame-map ambiguous / source drift / outbox exists / NaN / device mismatch / positive-control dead.

## Video (deferred; AFTER numeric localization)
Separate leg: golden side = **RECORDED_STATE_RENDER (NO PHYSICS)** explicitly labeled; current = physics-synced; global + both-gripper/C1 close views; frame/route_t/event overlay; raw+manifest pairing. Rs human-confirm; formal physical verdict = **V12 blind-review** (pN/p4 self-judgment non-authoritative). Which video / what to confirm = stated clearly to Rs at delivery.

## Authorization / scope
Diagnostic ONLY — does NOT unlock fix / B6-char / B5b / impl / training. Results → p5 (design owner) for L3/root-fix decision. p6 DDR FOUNDATIONAL row HELD until (b)+localization+Rs-video verify. (c) cable bend/stretch-stiffness compare may touch §0/banked cable design ⇒ design-gate + Rs before any change (STOP if touched).

## Order
Phase0 (done, this doc) → **pN readback** → (b) [no-sim, GO on comparable] → (a) [FF+pin cable_xyz divergence localize] → P1 telemetry (if physics-gap) → video → p5 root-fix decision.
