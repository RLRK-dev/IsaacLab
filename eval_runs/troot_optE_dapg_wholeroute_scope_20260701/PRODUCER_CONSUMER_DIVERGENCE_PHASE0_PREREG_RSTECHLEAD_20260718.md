# Producer-trace vs current-consumer DIVERGENCE — Phase0 audit + prereg **v0.2**

**Author (CC1):** RS-TECH-LEAD (w2:p4). **Stamped:** 2026-07-18 23:50 JST. **v0.2:** 2026-07-19 00:09 JST (folds pN readback B1-B7 [23:59] + p5 §10.13.3 [00:07]).
**Origin:** Rs autonomy grant → p4 decides via p5/p6/pN, proceeds; Rs confirms via video. Surfaced by Rs's questioning of the FF/ik_chord replay videos.
**Panes:** pN OPS-SUP-CODEX = readback **HOLD** (B1-B7; direction CONCUR); p5 VT-DESIGN = **(b) GO as PROJECTED-preliminary + FF@10-decisive** (§10.13.2/.3, ACCEPTs pN's 2 corrections); p6 = new higher-level item, **DDR row HELD pending verify**.
**⚠ Honest framing:** "substrate fidelity gap" = **UNPROVEN**. Observed = **producer-trace vs current-consumer divergence**. `golden` = producer recording (`ROUTE_DEMO_RAW_v1`, 7707 frames = 771 RL steps, `pin_active` from frame 2544), NOT a current-env success. **⭐ Leading explanation (p5+pN): a KNOWN solver-substep mismatch** — producer ran `SIM_SUBSTEPS=10`, consumer runs `RL_SIM_SUBSTEPS=4` — a deliberate throughput/fidelity tradeoff, **not** a substrate defect. This must be controlled before any gap is named.

---

## PHASE 0 — canonical-lineage + comparability audit (STATIC, no-sim; independently reproduced by pN)

### 0.1 Lineage → GOLDEN = TRACE_ORACLE_ONLY  (B1 fix: full 3-file as-run map)
Golden npz `5f1c3f92…`, **19 byte-identical copies**. TWO `route_demo_raw_meta.json` for the same content — the "conflict" is code-provenance only:

| as-run file | canonical (`w0e_81rerun_snapdown_0537/cell_x0_y0`, head `bc09a2de`) | seatgate-r2b (head `5b7afd5a`) |
|---|---|---|
| `route_demo_recorder.py` | **`bd5457f3`** | **`6eace080`** |
| `test_newton_clip_routing.py` | `2faf8029` | `a59232f8` |
| `task_config.py` | `1a0851db` | `1a0851db` **(IDENTICAL)** |

(B1 correction: my v0.1 mislabeled the *test-file* shas `2faf/a592` as "recorder" — the recorder shas are `bd5457f3`/`6eace080`.) Recording **params** (`task_config`) identical; recorder + test-harness code differ. Two distinct as-run closures → **no unique executable reconstruction ⇒ `GOLDEN = TRACE_ORACLE_ONLY`**. Conditions unambiguous.

### 0.2 Comparability (B2: verdict SPLIT)
| field | golden (producer) | consumer | verdict |
|---|---|---|---|
| cable topology | `cable_xyz (7707, 40, 3)` = 40 segs | `CABLE_SEGMENTS=40` | **MATCH** |
| frames/RL + frame dt | `n_frames=7707`=771×10; `DT=1/480` | `PHYSICS_STEPS_PER_RL=10`, `DT=1/480` | **MATCH (cadence)** |
| **solver inner substep** | **`SIM_SUBSTEPS=10`** (meta `sim_substeps=10`, `SIM_DT=DT/10=0.000208`; `test_newton_clip_routing.py:123-124,3735-3737`) | **`RL_SIM_SUBSTEPS=4`** (`RL_SIM_DT=DT/4=0.000521`; `newton_skill_env_base.py:93-96`) | ⛔ **KNOWN 10-vs-4 MATERIAL delta** |
| IC (step0) | `cable_xyz[0]` z=0.8040 (uniform) | `cable_z_rest=0.803977` | z-level MATCH; full 40-seg X/Y/Z IC = decisive-run step0 |

**Verdict split (B2):** **`TRACE_PROJECTION_COMPARABLE`** (topology/cadence/IC-z ⇒ static state-projection valid) **/ `EXECUTION_NOT_COMPARABLE`** (the 10-vs-4 solver substep ⇒ *dynamic* reproduction is NOT comparable until substep is controlled). Node prior-art records the 10/4 mismatch as MATERIAL.

---

## (b) STATIC predicate PROJECTION — **cheap PROJECTED preliminary ONLY** (no-sim; p5 §10.13.3 + pN B3/B4/B5)
- Project golden stored `cable_xyz`(+`ee_pos_l/r`,`grip_cmd`,`phase_id`) onto consumer predicates A[held_z]/B[contact_loss]/C[c1_escape] (`newton_route_env.py:410-413`, drop mirror `:1653-1660`).
- **B3 latent caveat (load-bearing):** the npz does NOT carry consumer hidden state (`grasped=_g_latched[0]`, A-guard `_g_latched[1]`, C-guard `_g_latched[2]`, `contact_loss_count`, `contact_r/l`). Deriving them from `grip_cmd`+`phase_id` is **NOT** an equivalence proof ⇒ all values are **ASSUMED / PROJECTED**. **p5 retracts the (b) predicate-gap-vs-physics-gap dichotomy** — offline (b) CANNOT cleanly discriminate. p5: weight **A/B**; **C** (via derived `g_latched[2]`) = approximate.
- **B4 cadence:** evaluate at **RL-step cadence** (drop/`contact_loss_count` are 1 per RL step, not per physics frame). Freeze the frame→route_t map (10:1), `contact_loss_count` init=0 + reset rule, tail-7 handling. Fail-close any per-frame×8 miscount.
- **B5 outcome union:** **`{PROJECTED_HIT, PROJECTED_CLEAR, UNOBSERVABLE_INCONCLUSIVE}`**. ⛔ **NO causal gap label** (PROJECTED_HIT ≠ predicate-gap; PROJECTED_CLEAR ≠ physics-gap — latent unobserved + known 10/4 delta).
- **B6:** the drop logic has **NO pin branch** (`:1653-1660`); `pin_active` only *physically* changes state. (v0.1's "pin suppresses C" is RETRACTED.)

## ⭐ DECISIVE experiment — FF@10 vs golden (substep-controlled; p5 §10.13.3)
The clean discriminator (offline (b) cannot do it): re-run the **consumer FF at `RL_SIM_SUBSTEPS=10`** (matching the golden producer `SIM_SUBSTEPS=10`) — a **diagnostic-config override, NOT a production/source change** — captured with **LIVE consumer hidden state**:
- **FF@10 reproduces golden** ⇒ the divergence was the substep setting ⇒ **gap = substep (throughput config), NOT substrate — RESOLVED.**
- **FF@10 still diverges** ⇒ discriminate with live state: predicate fires *while* `cable_xyz` still matches golden = predicate-driven; fires *after* the trajectories diverge = physics-driven ⇒ residual only → (c) cable bend/stretch-stiffness compare.
- **Substep single-variable bracket (p5):** run **FF@4 AND FF@10** vs golden. ⚠ the earlier substep-refutation was ik_chord-vs-FF@4 (same substep) — it does **NOT** apply to FF-vs-golden@≠4 (confounded-comparison lesson).
- **Full IC control (p5):** compare **full step0 40-seg X/Y/Z** cable_xyz vs golden (z-level alone confounds X/Y IC diff).
- **⚠ open for pN readback:** the `substeps` override must be a **harness arg to `_physics_step_all(substeps=…)`**, NOT an env-source edit (pN's "no source edit" bar). Confirm the override mechanism is clean.

## P1 telemetry (FENCED until pN readback) + evidence bar (B7)
- 2 fresh same-seed identical legs (determinism) + per-physics-frame earliest-divergence telemetry: `frame/route_t/phase`, commanded+achieved arm/grip `q/qd`, cable body `q/qd`, `contact_r/l`+grip load, `held_i/z`, C1/C2 geometry, `pin_active/eq/body`, ALL done-predicates + term-cause + **live `_g_latched`/`contact_loss_count`**. First-divergence per channel.
- **Positive controls:** A/B/C each (known single-field perturbation must trip); **B debounce gap-reset** control; **live-helper/mirror parity** (incl. seat identity) so the offline mirror == the live predicate.
- **Provenance binding (reuse gonow helpers):** exact commands/argv, fresh outbox+COMPLETE, env_isaaclab7, CVD/device-uuid/MUJOCO_GL, wc1/seed/horizon, versions, full effective-config, recording + EVERY sidecar sha (npz/meta/recorder/test/task_config) + disposition, git HEAD+dirty, harness self-sha, import/build/post source-closure (changed/missing/added=[]), frame-map assert, rc preserved. **env/physics/source edits FORBIDDEN** (substep = a run arg only).
- **Stop:** sidecar-conflict unresolved / timebase or frame-map ambiguous / source drift / outbox exists / NaN / device mismatch / positive-control dead / substep-override touches source.

## Video (deferred; after numeric localization)
Golden side = **RECORDED_STATE_RENDER (NO PHYSICS)** explicitly labeled; current = physics-synced; global + both-gripper/C1 close views; frame/route_t/event overlay; raw+manifest pairing. Rs human-confirm; formal physical verdict = **V12 blind-review**. Which video / what to confirm = stated clearly to Rs.

## Authorization / order
Diagnostic ONLY — no fix / B6-char / B5b / impl / training unlock. Results → p5 root-fix (L3). p6 DDR row HELD. (c) cable bend/stretch-stiffness compare or any cable-param change touches §0/banked cable design ⇒ **design-gate + Rs before change (STOP if touched)**.
**Order:** Phase0 v0.2 (this) → **pN readback** → (b) PROJECTED-preliminary [cheap, A/B weight] **+ FF@10-vs-golden DECISIVE** (FF@4+FF@10 bracket, live-state, full-IC) → residual (c) → video → p5 root-fix. All results labeled TRACE_ORACLE_ONLY / EXECUTION_NOT_COMPARABLE.
