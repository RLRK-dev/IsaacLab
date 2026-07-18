# P-D1 pre-run FINDING — imported XML arm actuators: duplication + a latent tug-of-war (design correction #2 request)

- **Date:** 2026-07-19 08:52 JST (date-THEN-write)
- **Author:** RS-TECH-LEAD (w2:p4). **For:** VT-DESIGN (w2:p5) — design correction court.
- **Context:** (d) P-D1 probe build-out (design `ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md` v1.1
  = `ed24470097`). Probe env code + harness are built in a detached worktree (base `0f39f7b598`); the FIRST diagnostic
  smoke tripped the L-P6 readback assert, and the follow-up measurements below change an M-1 premise.
  **All numbers here come from the referenced logs (diag/ dir), not from memory.**
- **Evidence dir:** `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pd1_probe_20260719/diag/`
  (`dump_actuators_baseline.log` sha256 `c552013a…`, `dump_ctrl_wiring.log` `23209cdc…`, `run_smoke_pd.log` `7dd1e5c7…`,
  + the two dump scripts).

## 1. Measurements (all on the committed state `0f39f7b598` + probe diff, wc=1, cuda:0, FF cfg, nominal recording)

- **M-A (baseline actuator population):** flag-OFF build has **nu=16**: 4 gripper servos (ke 66.7) **+ 12 arm actuators
  ALREADY PRESENT** — act4-15, vendor gains (2000/−2000/−400 size3; 500/−500/−100 size1), mapped to the 12 arm joints
  by name. [`diag/dump_actuators_baseline.log`] ⇒ the ur5e.xml `<actuator>` block IS imported into the built model.
- **M-B (duplication under the M-1 proto wiring):** with `ARM_PD_DRIVE=1` (probe builder wiring per design M-1),
  the smoke build has **nu=28 = 24 arm-gain actuators + 4 gripper** — the 12 imported + 12 newly synthesized from the
  proto `joint_target_mode=POSITION` wiring = **duplicate actuators on the same joints (double-torque hazard)**.
  The L-P6 readback assert caught this BEFORE any run (`run_smoke_pd.log`: `armpd-rb: mj arm actuators = 24 != 12`).
- **M-C (the imported actuators are UNWIRED from Newton control):** baseline arm dofs carry
  `joint_target_mode = 0 (NONE)`, `ke = kd = 0`, `joint_target_pos = 0`; device-side `solver.mjw_data.ctrl` is
  **all-zero** after reset/settle/P0 (arms held at q ≈ [−2.40, −1.33, 1.91, −2.15, −1.57, −0.83] rad …);
  writing `control.joint_target_pos[arm] = q+0.1` and stepping leaves `ctrl` **still all-zero**.
  [`diag/dump_ctrl_wiring.log` sections [1]-[3]] ⇒ `joint_target_pos` does NOT reach the imported actuators;
  their ctrl is permanently 0.

## 2. Implication A — the CURRENT kinematic substrate carries a permanent hidden disturbance (substrate-level finding)

With ctrl ≡ 0 and position error up to ~2.4 rad, each of the 12 imported actuators outputs its **saturated cap**
(±150 / ±28 N·m; 2000×2.4 ≫ cap) toward qpos=0, **every substep, all run long** — masked per frame by the kinematic
joint_q re-forcing (measured: one un-forced physics frame moves the arm ~5e-4 rad [`dump_ctrl_wiring.log` [3]]),
but the torque is injected into the coupled physics every substep (reaction paths include the grasped cable
contacts). **Every banked run on this env family shares this artifact** (it predates (d); the kinematic overwrite
is what hides it). Conservatism direction: NOT determinable from this measurement alone (the disturbance could
mask or mimic either way); flagged for p5/Rs disposition. ⚠ 推測 (tagged): this artifact is a candidate
contributor to drive-sensitivity phenomena (#18 class) — untested, listed only as a hypothesis for p5's court.

## 3. Implication B — design M-1 needs correction #2 (the wiring path premise inverts)

M-1 said "⛔ ur5e.xml の `<general>` actuator import には依存しない (operative path = proto→SolverMuJoCo 合成)".
Measured reality: the import IS present and populates 12 live-but-unwired actuators; adding the proto wiring
**duplicates** them. The M-2 ctrl write (probe drive branch) is correct as designed but must target a
de-duplicated actuator set.

**Options for p5 (I do not choose):**
- **(A) Drive the imported actuators:** write the device `mjw_data.ctrl[0, 4:16]` per frame (bypasses
  `control.joint_target_pos`; solver-internal array; per-world layout must be verified for wc>1 later).
  No builder change; the tug-of-war disappears because ctrl follows the target.
- **(B) Neutralize the imported actuators + keep the M-1 proto wiring:** strip/zero the 12 imported actuators
  (import option or post-build gain zeroing) so the synthesized, `joint_target_pos`-driven set is the only one —
  gripper-mirror as designed. ⚠ if neutralization is flag-gated, the probe baseline keeps the tug-of-war while
  the PD run removes it → the contrast becomes "migration delta (realization + artifact removal)", not a pure
  realization delta — needs a declared-delta ruling (or neutralize in BOTH probe arms, which then differs from
  the banked substrate — also needs a ruling).
- **(C) other (p5 design call).**

## 4. Status / next

- Probe runs: **HOLD** until correction #2 lands (v1.2). Worktree + harness ready otherwise
  (L-P6 assert working as intended — it produced this catch).
- Prereg: drafted AFTER v1.2 (the run matrix may change with the option chosen).
- The L-P6 assert will be adapted to the chosen option (count/population semantics).

## Repro (exact)

```bash
cd <worktree>  # detached at 0f39f7b598 + probe diff
CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \
  <diag>/dump_actuators.py <worktree>/thread_isaac_lab <nominal route_demo_raw.npz>   # M-A
CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python \
  <diag>/dump_ctrl_wiring.py <worktree>/thread_isaac_lab <nominal route_demo_raw.npz> # M-C
```
