---
status_ledger: 00-DESIGN-STATUS-LEDGER.md  # authoritative success/failure status SSOT
title: S1B Faithful-Finger Mechanism Design (Historical / Abandoned)
created: '2026-06-04'
tags:
  - s1b
  - faithful-finger
  - newton
  - mechanism-design
  - axis-1
  - abandoned
  - superseded
status: FAILED_ABANDONED_SUPERSEDED_BY_SIM_FOUNDATION_APPLAUNCHER_ROUTE
---

# S1B Faithful-Finger Mechanism Design — Historical / Abandoned

> **Current status (2026-06-05):** this document is **not an active design plan**. It is retained as the historical
> record of the failed/abandoned Newton faithful-prismatic route. Human-Rs rescoped S1B L0 to Isaac Lab / SIM with a
> rigorous foundation requirement; `%3` confirmed the env6 Newton faithful-prismatic + existing CABLE-jointed cable
> route is substrate-walled; `%7` records the official IsaacSim/PhysX AppLauncher path as the current primary
> SIM-foundation route after `%3` verified the launcher surface. Do not use this document as a runtime plan or as
> evidence that the Newton faithful-finger route remains active.

> **Authorship / ownership:** This document was originally a **consolidation authored by `%3`
> (T-ROOT-OPS-SUPERVISOR)** of design content that was Rs-decided and reviewed on 2026-06-03/04. It is now a
> failure-avoidance record governed by `00-DESIGN-STATUS-LEDGER.md`.

## 0. Purpose

Before this doc, the S1B faithful-finger design was **distributed across ~28 `eval_runs/troot_s1b_*` packages + the
`%3` memory trail + `log.md`**, with no single design SSOT. This file now serves a narrower purpose: preserve the
historical design and the reason it must not be restarted as the current SIM foundation route.

## 1. Product predicate (Rs decision, AXIS-1)

- **Superseded AXIS-1 state:** the 2026-06-04 `REFRAME_TO_CONTINUOUS_HOLD_UNTIL_HANDOFF` state is historical.
- **Current frame (2026-06-05):** Human-Rs abandoned/reframed the faithful-prismatic Newton rebuild, then rescoped S1B
  L0 to Isaac Lab / SIM. Real-world physical Franka x2 deployment is out of current scope; 95% is final rather than
  the current bar; the current bar is basic SIM operation first; mechanism/environment/cable foundation remains
  rigorous and no-bypass.
- **Current primary route:** official IsaacSim/PhysX AppLauncher launch-preflight, not this Newton faithful-finger
  line.

## 2. Mechanism design — faithful-finger bind-set (design-as-code)

Historical substrate: **`STANDALONE_NEWTON_VBD_ENV_ISAACLAB6`** — standalone `newton` package under
`/home/rlrk/env_isaaclab6/bin/python`. This is **not** the current primary SIM-foundation route after the 2026-06-05
IsaacSim/AppLauncher correction. The values below are retained only to document the abandoned design.

### 2.1 Actuation (both hands: `left_release_side`, `right_holding_side`; joints `panda_finger_joint1/2`)

| Parameter | Value | Source / note |
|-----------|-------|---------------|
| `effort_limit` | `200.0` N | IsaacLab `panda_hand` CFG value (`franka.py`). **Disclosed divergence:** URDF source-fact effort = `20.0` (10×); recorded as **calibration-not-spec-match**, not a faithful claim. |
| `target_ke` | `2000.0` N/m | actuation stiffness |
| `target_kd` | `100.0` N·s/m | actuation damping |
| `armature` | `0.0` | official `panda_hand` actuator has **no** armature (arms use `1e-3`) |
| limits | `[0.0, 0.04]` m | prismatic finger range |
| drive mode | `newton.JointTargetMode.POSITION_VELOCITY` | |
| API | `newton.ModelBuilder.add_joint_prismatic` | kwarg is `effort_limit` (not `effort`) |

`strict_subset_is_faithful = false` — a partial subset must not be declared "faithful."

### 2.2 Contact-material — corrected historical note

Status correction: the earlier design text described the THREAD cable as a **particle Cosserat rod**. Later source
closure found that the installed Newton `add_rod` path used here builds **rigid capsule bodies connected by CABLE
joints**, not cable particles. That cable-model mismatch, together with solver support closure, makes the
faithful-prismatic Newton route non-runnable for the current foundation. The table below is historical design content
only; it is not an active SIM-foundation contact plan.

| Side | Field | Value | Source |
|------|-------|-------|--------|
| particle / cable (soft) | `soft_contact_ke` / `kd` / `mu` | `1000.0` / `10.0` / `0.5` | `newton.Model` scalar defaults, **read at runtime** with a fail-closed mismatch guard (not hardcoded-trusted) |
| rigid / finger (shape) | `shape_material_ke` / `kd` / `mu` | `2500.0` / `100.0` / `1.0` | live `task_config.py:81-83` `CABLE_CONTACT_KE/KD/MU` |

**VBD combination rule** (`rigid_vbd_kernels.py:1366-68`, independently verified):
- effective `ke = 0.5 * (soft_contact_ke + shape_material_ke)` (arithmetic mean)
- effective `kd = 0.5 * (soft_contact_kd + shape_material_kd)` (arithmetic mean)
- effective `mu = sqrt(soft_contact_mu * shape_material_mu)` (geometric mean)

Only `ke/kd/mu` are consumed by VBD soft-contact; `kf / restitution / mu_torsional / mu_rolling / ka / margin / gap / hydroelastic_kh` are **NOT consumed** (bucketed `DISPOSITION_REQUIRED_NOT_VERIFIED`).

### 2.3 Forbidden success paths (exact set of 10, validator-enforced: set-equality + `len==10` + unique==10)

`spring_follow_success`, `passive_fk_cache_held_success`, `zero_inverse_mass_support_success`, `kinematic_pin_support_success`, `hidden_fixture_success`, `geometry_only_credit`, `wrapper_exit_only_success`, `hold_to_completion_success`, `active_at_completion_success`, `diagnostic_contact_as_product_proof`.

(These reconcile the earlier code-list/attestation divergence — "C1" — by including `hidden_fixture_success` + `diagnostic_contact_as_product_proof`.)

## 3. Calibration policy (Rs decision)

- **`RS_APPROVED_DIAGNOSTIC_BASELINE_CALIBRATION_POLICY_V1`** (Rs, 2026-06-04), scope = **first Newton/env6 faithful-finger prerequisite DIAGNOSTIC run only**.
- Permitted basis = **source/API-resolved current Newton/VBD baseline values only** (the §2.2 values).
- It is explicitly **NOT** real-gripper measurement, **NOT** sim2real calibration proof, **NOT** physical-grasp proof, **NOT** product proof, **NOT** a faithful contact-value claim.
- Contact values are classified `CALIBRATION_DIMENSION_NOT_OFFICIAL_SPEC_MATCH` (no official Franka ground-truth for the cable/particle side, unlike the PD gains which trace to `franka.py`).
- Runtime stays HOLD absent a reviewed sim2real / real-measurement / Rs-approved calibration basis.

## 4. Status & authoritative artifact

- **Design lifecycle status: FAILED / ABANDONED / SUPERSEDED.** The not-applied faithful-finger diffs were
  artifact-clean, but subsequent run attempts and source closure found the active route substrate-walled.
- **Source state:** some reviewed diagnostic helper patches were applied during the investigation, but the route is not
  current and must not be advanced through Newton faithful-prismatic retry, Kamino single-solver retry, or
  Featherstone+VBD-external retry.
- **Historical design-as-code:** `eval_runs/troot_s1b_axis1_calibration_policy_and_direct_run_wiring_exact_source_diff_package_0gpu_20260604/PROPOSED_SOURCE_DIFF_NOT_APPLIED.patch`
  and successor harness/repair packages are retained as evidence only.
- **Current primary SIM-foundation path:** reviewed IsaacSim/PhysX AppLauncher launch-preflight, followed only after a
  passing gate by bounded import/source repair and a no-bypass SIM foundation runner.

## 5. Current next gate

Do **not** create another Newton faithful-finger run harness or repair package from this document.

The current next gate is:

1. `ISAACSIM_APPLAUNCHER_LAUNCH_PREFLIGHT_DECISION` under explicit `%7` / Human-Rs high-cost-gate.
2. Fresh no-clobber output root on `/data`.
3. No model build beyond the reviewed source-check surface.
4. If launch-preflight passes, a bounded DeformableObject / modular-split import repair.
5. Then a no-bypass SIM foundation bring-up runner.

This is route/foundation bring-up only. It is not a task success, product, sim2real, T-ROOT95, Stage-2, or production
claim.

## 6. Boundaries — what this design is NOT

`CUSTOM_NEWTON_DIAGNOSTIC_QUARANTINED` remains active for historical Newton evidence. **PRODUCT_GO = false.** This
design is **not** a faithful/official-Franka spec-match, **not** a retention/grasp success claim, **not**
physical-grasp / sim2real / T-ROOT95 / Stage-2 / production proof, and **not** the active route.

## 7. Provenance map (where the design content lives)

- **Historical design-as-code (not current):** the patch in §4.
- **Current route correction:** `eval_runs/troot_s1b_l0_sim_foundation_isaacsim_launcher_resolvability_correction_package_0gpu_20260605/`
  and `%3` Tier-A verdict 2026-06-05.
- **Increment chain + rationale (~28 pkgs):** `eval_runs/troot_s1b_*/S1B_*.md` + JSON — `unit_a/a1/a2`, `unit_b`, `unit_d`, `franka_actuation_topology(+cc2)`, `contact_material_(fidelity/particle_guardfix)`, `faithful_finger_exact_source_diff`, `axis1_calibration_policy_and_direct_run_wiring` (multiple not-applied patches overlap the same `2f60a968` base).
- **Review / decision trail:** `%3` memory `project_s1b_frame_decision_ca_physx_prereq_axis1_open_2026-06-04` + `thread-vault/log.md` (rows ~5870-6010).
- **State / boundary:** `thread-vault/04-Specs/SOMA.md:56-63` (quarantine caveat + diagnostic-run history) + `docs/logical_decomposition.html`.
- **Process lessons:** `LL-Process` `LL-2026-06-03-PROC-006` (reuse-first) + `LL-2026-06-04-PROC-007` (removable inefficiencies).

---

*Consolidation by `%3` (read-only supervisor); design owned by Rs. Reviewed content basis: 2026-06-04 diff-level Tier-A + 4-body CC Debate (ARTIFACT-PASS). No apply / runtime / GPU authorized by this document.*
