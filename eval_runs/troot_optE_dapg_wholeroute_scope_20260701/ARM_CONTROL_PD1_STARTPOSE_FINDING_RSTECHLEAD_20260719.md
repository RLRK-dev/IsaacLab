# P-D1 FINDING #2 — route-start pose bridge (design correction #3 request) + FF-site impl note

- **Date:** 2026-07-19 09:2x JST (date-THEN-write at commit). **Author:** RS-TECH-LEAD (w2:p4). **For:** VT-DESIGN (w2:p5).
- **Context:** (d) P-D1 build-out under design v1.2 (`3b5f75c131`). Option B wiring landed + census PASS.
  Evidence: `pd1_probe_20260719/diag/` + this doc's logs (`dump_pose_streams_{kin,pd}.log`, `run_smoke3_pd.log`).

## 1. Impl-to-spec note (no design change; my gap, fixed)

Design v1.2 §2 prescribes the FF-path ctrl replacement at `route_executor.py` (`apply_recorded_arm_ff`);
my first probe branch wired only the RL-path site (`newton_route_env.py:1270` loop), which the FF drive
bypasses — smoke-2's 6.1 rad "tracking error" was the stale never-rewritten ctrl vs the still-kinematic FF
writes (`dump_pose_streams_pd.log`: [pd] q follows the recording exactly like [kin]; ctrl frozen at the
post-reset sync value). **Fixed:** `apply_recorded_arm_ff` now writes `control.joint_target_pos[arm]`
:= the recorded per-frame arm row under the flag. Plumbing re-validated (`run_smoke3_pd.log` +
`smoke3_pd/armpd_frames_*.npz`): ctrl[frame 0] = recording frame-0 pose `[3.194, -1.980, 1.600, …]` and
advances with the stream; census PASS (inert 12 / live 12).

## 2. FINDING — reset home ≠ recording frame-0 arm pose (the banked runs bridge it by a hard teleport)

- **Measured** (`dump_pose_streams_kin.log`, baseline kinematic build):
  - post-reset arm q = `[-2.401, -1.330, 1.910, -2.151, -1.571, -0.830 | 2.255, -1.369, 1.961, 0.980, 1.571, 0.684]`
  - recording frame-0 arm pose = `[3.194, -1.980, 1.600, -1.853, 2.000, -1.518 | -0.052, -1.162, -1.600, -1.288, -2.000, -1.623]`
  - per-joint |Δ| up to **5.6 rad** (j0), a DIFFERENT joint-space configuration (not a 2π wrap).
  - **[kin] after RL step 0 the arm IS AT the recording pose** ⇒ the kinematic FF drive bridges the gap by
    a **hard forced re-pose within the first RL step** — banked behavior in every FF run, invisible because
    the write is kinematic.
- Under PD this becomes a **real physical transit**: smoke-3 shows the servo hauling the arm from home
  toward the recording pose (~1.7 rad on j0 in the first 0.2 s, saturated) while the route clock marches on
  ⇒ the whole playback lags by the transit; L-P1 numbers are garbage until this is designed away.

## 3. Options for p5 (correction #3 — I do not choose)

- **(a) Reset-init seed = recording frame-0 arm pose** (flag-gated, probe branch): a sanctioned
  reset-init kinematic pose (§4 B-class) + M-4 target-sync (ctrl starts at the same pose; frame-1 FF target
  = the same stream) ⇒ **no jump at all**; playback fidelity from frame 0. My recommendation — it makes the
  PD run start exactly where every banked kinematic run effectively starts (they teleport into it anyway).
  Note: the settle/P0/grasp-prep choreography before route start would then end at a pose the recording
  defines — whether to re-pose only at route start (after grasp-prep) or to seed the whole reset needs
  p5's word (the grasp state must remain consistent with the cable).
- **(b) M-5 ramp-in with a route-clock hold**: physically transit home→recording-start before starting the
  clock. Needs a new hold mechanism (scope) + a 5.6 rad sweep with the gripper near the table/cable
  (collision risk during the sweep).
- **(c) other.**

## 4. Observation (no action requested)

`solver.mjw_data.ctrl` reads all-zero even with live wired servos driving (gripper positive control
proves the joint_target_pos→actuator flow works) — the mirror appears stale/not-the-operative array.
Design/asserts should not rely on reading that mirror (L-P6 census reads model arrays instead).

## Files

- FF ctrl branch: worktree `thread_isaac_lab/envs/route_executor.py` (`apply_recorded_arm_ff` + init flag).
- Logs: `pd1_probe_20260719/diag/dump_pose_streams_{kin,pd}.log`, `run_smoke3_pd.log` (committed alongside).
