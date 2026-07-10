# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""comp3 G1 arm_q-direct diagnosis run (Rs GO 2026-07-10 13:18; descend->close window only).

Closes the env-actual data gap reported by the close-window back-check (comp3_g1_closewindow_result.json
env_actual_data_gap): the G1 runner saved no per-frame achieved arm_q / claw pose / ik_resid / latch
offsets, so the suspected systematic env batched-IK claw-z bias (~4-6mm low on L; Rs human-GT: L finger
clamped BELOW the cable) could not be measured from existing artifacts. This runner re-drives the SAME
trajectory (world-0 nominal + g1_scene_align, zero residual -- INIT_XY_NOISE only perturbs the reset
_ee_target which the replay drive path never reads, so the arm path reproduces modulo device numerics)
and captures it per physics frame.

Two stages (one file):
  stage run  (default; CUDA_VISIBLE_DEVICES=0): builds the G1 env, wraps env._physics_step_all (instance
      attr; the inner drive loop at newton_route_env.py:1043 calls it once per physics frame, and
      _reset_worlds steps no physics -> capture is exactly 10 frames per RL step, PRE-reset even on a done
      step). Captures per frame: commanded arm_q (wrapper entry == post arm-assign), achieved arm_q +
      L/R EE body pose + cable body positions (wrapper exit == post solver step); per RL step: ik_resid
      (env [R, L] order). Runs t=0..T_STOP=114 (== the banked close-window T_HI,
      comp3_g1_closewindow_claw_vs_cable.py:56; latch was t=99 in G1 -> +15 steps covers full close
      ~f1123), STOPS there (no lift, no render -> well under the approved ~2min budget). Persists the
      latch offsets off_l/off_r this time. Saves the capture npz, then spawns stage table in a separate
      CUDA_VISIBLE_DEVICES='' process (keeps the CPU FK reconstruction fully isolated from the live
      cuda warp context).
  stage table (CUDA_VISIBLE_DEVICES=''): loads the capture npz + golden npz, rebuilds the recording claw
      z per frame via the SAME single-source measure as the back-check (CPU build_fk_and_init + eval_fk +
      clamp_pos_ko), cross-checks FK(achieved arm_q) vs the live-captured EE pose, and emits the
      side-by-side table (frame, L_claw_z_env vs L_claw_z_rec vs cable_z, deltas, R control) + JSON.

Frame convention: during RL step t the env interpolates the arm from IK(step t-1 target) toward
IK(step t target) over 10 physics frames; sub-frame i is mapped to recording frame t*10 + i + 1 (clamped).
The +-1-frame convention ambiguity is bounded by the back-check result (recording claw PARKED at constant
z through the close window; worst within-step interp deviation 0.28mm).

Video leg (recorded loud per CLAUDE.md rule 14): OMITTED per the Rs GO output spec (side-by-side table +
JSON commit). The motion is the same trajectory as G1, whose video leg + Rs human-GT verdict are already
banked (run 13d37af1d5, FAIL banking 6e0c7fe420); this run adds numeric state capture only, no new motion
claim.

Run:
    CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp3_g1_armq_diag.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parent
_REPO = _EVAL_DIR.parent.parent
_TIL = _REPO / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

GOLDEN_NPZ = _EVAL_DIR / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
CAPTURE_NPZ = _EVAL_DIR / "comp3_g1_armq_diag_capture.npz"
OUT_JSON = _EVAL_DIR / "comp3_g1_armq_diag_result.json"
CADENCE = 10
T_STOP = 114  # == banked close-window T_HI (back-check); G1 latch_t=99 -> +15 steps = full close ~f1123
T_LO_TABLE = 90  # close-window table start (matches the back-check rows)
CLOSE_LATCH_Q = 0.6
_DRV_L = [6, 10]
_DRV_R = [20, 24]


def _pad_and_cable_geoms(m, mujoco):
    pads, cables = [], []
    for g in range(m.ngeom):
        gname = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "").lower()
        bname = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, int(m.geom_bodyid[g])) or "").lower()
        if "pad" in (gname + bname):
            pads.append(g)
        elif int(m.geom_type[g]) == int(mujoco.mjtGeom.mjGEOM_CAPSULE) and int(m.geom_bodyid[g]) != 0:
            cables.append(g)
    return set(pads), set(cables)


def _pad_cable_contacts(d, pads, cables):
    n = 0
    for i in range(int(d.ncon)):
        pair = {int(d.contact[i].geom1), int(d.contact[i].geom2)}
        if pair & pads and pair & cables:
            n += 1
    return n


def stage_run():
    assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "0", (
        "diagnosis run stage runs on cuda:0 ONLY (device-pinned in the shell layer); got "
        f"{os.environ.get('CUDA_VISIBLE_DEVICES', '<unset>')!r}"
    )
    import mujoco
    import newton_route_env as nre
    import torch
    import warp as wp

    print("[DIAG] building flag-ON + g1_scene_align env (world_count=1, cuda:0; SAME config as G1) ...")
    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cuda:0",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(GOLDEN_NPZ),
            "g1_scene_align": True,
        },
    )
    m = env._solver.mj_model
    d = env._solver.mj_data
    pads, cables = _pad_and_cable_geoms(m, mujoco)
    env.reset()

    aq0 = env._arm_q_start[0]
    bws0 = env._bws[0]
    i_l, i_r = bws0 + nre._LEFT_EE_BODY, bws0 + nre._RIGHT_EE_BODY
    cable_ids = env._cable_bodies[0]

    cap = {"cmd_q": [], "ach_q": [], "ee_l": [], "ee_r": [], "cable": []}
    orig_step = env._physics_step_all

    def wrapped_physics_step(*a, **k):
        # entry: arm joint_q slice just assigned (jq_interp) == the commanded arm pose for THIS frame
        # (gripper coords 6-13/20-27 are servo-DYNAMIC carry-over, recorded as-is).
        cap["cmd_q"].append(env._state_0.joint_q.numpy()[aq0 : aq0 + 28].copy())
        r = orig_step(*a, **k)
        wp.synchronize()
        jq = env._state_0.joint_q.numpy()
        bq = env._state_0.body_q.numpy()
        cap["ach_q"].append(jq[aq0 : aq0 + 28].copy())
        cap["ee_l"].append(bq[i_l].copy())
        cap["ee_r"].append(bq[i_r].copy())
        cap["cable"].append(bq[cable_ids, :3].copy())
        return r

    env._physics_step_all = wrapped_physics_step

    ik_resid = []  # per RL step, env order [R, L]
    latch = {"latch_t": None, "held_l": None, "held_r": None, "off_l": None, "off_r": None}
    drv_series = []
    done_early = None
    zero = torch.zeros((1, 6), dtype=torch.float32)

    for t in range(T_STOP + 1):
        _, phase_peek, _, _ = env._route.step_target(t)
        if phase_peek >= 2:
            print(f"[DIAG] STOP before t={t}: next phase = G3 (never expected below T_STOP; loud)")
            break
        frames_before = len(cap["ach_q"])
        _, _, dones, _ = env.step(zero)
        n_new = len(cap["ach_q"]) - frames_before
        assert n_new == CADENCE, f"capture desync at t={t}: {n_new} frames (exp {CADENCE})"
        if bool(dones[0]):
            # done-step fix (same bug as the G1 runner): env.step() resets done worlds BEFORE returning,
            # so no state is read past this point; the wrapper frames above are PRE-reset and kept.
            done_early = t
            print(f"[DIAG] EARLY DONE at t={t} -- post-step state reads skipped (POST-RESET); frames kept")
            break
        wp.synchronize()
        jq = env._state_0.joint_q.numpy()
        bq = env._state_0.body_q.numpy()
        l_q = [float(jq[aq0 + i]) for i in _DRV_L]
        r_q = [float(jq[aq0 + i]) for i in _DRV_R]
        ik_resid.append(env._last_ik_resid[0].copy())
        drv_series.append((round(min(l_q), 4), round(min(r_q), 4)))
        ncon_pc = _pad_cable_contacts(d, pads, cables)
        if latch["latch_t"] is None and min(l_q) > CLOSE_LATCH_Q and min(r_q) > CLOSE_LATCH_Q and ncon_pc > 0:
            claw_l = np.asarray(nre.clamp_pos_ko(bq[i_l][:3], bq[i_l][3:7]))
            claw_r = np.asarray(nre.clamp_pos_ko(bq[i_r][:3], bq[i_r][3:7]))
            cable_pos = bq[cable_ids, :3]
            held_l = int(np.argmin(np.linalg.norm(cable_pos - claw_l, axis=1)))
            held_r = int(np.argmin(np.linalg.norm(cable_pos - claw_r, axis=1)))
            latch.update(
                latch_t=t,
                held_l=held_l,
                held_r=held_r,
                off_l=(cable_pos[held_l] - claw_l).tolist(),
                off_r=(cable_pos[held_r] - claw_r).tolist(),
            )
            print(f"[DIAG] CLOSE LATCH at t={t}: held L={held_l} R={held_r}, offsets PERSISTED (gap item 3)")
        if t % 20 == 0:
            print(f"[DIAG] t={t} phase={phase_peek} drv L={min(l_q):.3f} R={min(r_q):.3f} pad-cable={ncon_pc}")

    np.savez_compressed(
        CAPTURE_NPZ,
        cmd_q=np.stack(cap["cmd_q"]),
        ach_q=np.stack(cap["ach_q"]),
        ee_l=np.stack(cap["ee_l"]),
        ee_r=np.stack(cap["ee_r"]),
        cable=np.stack(cap["cable"]),
        ik_resid=np.stack(ik_resid) if ik_resid else np.zeros((0, 2), dtype=np.float32),
        drv_min=np.asarray(drv_series, dtype=np.float32),
        latch_meta=json.dumps({**latch, "done_early": done_early, "t_stop": T_STOP}),
    )
    print(f"[DIAG] capture saved: {CAPTURE_NPZ.name} ({len(cap['ach_q'])} frames)")

    print("[DIAG] spawning table stage (CUDA_VISIBLE_DEVICES='', isolated CPU FK) ...")
    env2 = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "NEWTON_DEVICE": "cpu"}
    r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--stage", "table"], env=env2)
    return r.returncode


def stage_table():
    assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "", "table stage is CPU-forced (CUDA_VISIBLE_DEVICES='')"
    import newton
    import newton_route_env as nre
    from newton_skill_env_base import build_fk_and_init
    from task_config import FINGER_OPEN_POS, WIDE_LEFT_Y, WIDE_RIGHT_Y

    capz = np.load(CAPTURE_NPZ, allow_pickle=False)
    ach_q = np.asarray(capz["ach_q"], dtype=np.float64)
    cmd_q = np.asarray(capz["cmd_q"], dtype=np.float64)
    ee_l = np.asarray(capz["ee_l"], dtype=np.float64)
    ee_r = np.asarray(capz["ee_r"], dtype=np.float64)
    env_cable = np.asarray(capz["cable"], dtype=np.float64)
    ik_resid = np.asarray(capz["ik_resid"], dtype=np.float64)
    latch_meta = json.loads(str(capz["latch_meta"]))
    n_frames = ach_q.shape[0]

    gz = np.load(GOLDEN_NPZ)
    rec_arm_q = np.asarray(gz["arm_q"], dtype=np.float64)
    rec_cable = np.asarray(gz["cable_xyz"], dtype=np.float64)
    n_rec = rec_arm_q.shape[0]

    fk_model, fk_state, _ = build_fk_and_init(
        left_finger_pos=FINGER_OPEN_POS, right_finger_pos=FINGER_OPEN_POS, device="cpu"
    )

    def fk_claw_z(arm_q_row):
        jq = fk_state.joint_q.numpy()
        jq[:28] = arm_q_row[:28]
        fk_state.joint_q.assign(jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        bq = fk_state.body_q.numpy()
        cl = nre.clamp_pos_ko(bq[nre._LEFT_EE_BODY][:3], bq[nre._LEFT_EE_BODY][3:7])
        cr = nre.clamp_pos_ko(bq[nre._RIGHT_EE_BODY][:3], bq[nre._RIGHT_EE_BODY][3:7])
        return float(cl[2]), float(cr[2])

    def lane_z(cable_frame, lane_y):
        seg = int(np.argmin(np.abs(cable_frame[:, 1] - lane_y)))
        return float(cable_frame[seg, 2])

    rows = []
    fk_xcheck_max = 0.0
    for fi in range(T_LO_TABLE * CADENCE, n_frames):
        t, sub = fi // CADENCE, fi % CADENCE
        rec_f = min(t * CADENCE + sub + 1, n_rec - 1)
        # env claw z: LIVE captured EE body pose (direct, no reconstruction).
        claw_env_l = float(nre.clamp_pos_ko(ee_l[fi][:3], ee_l[fi][3:7])[2])
        claw_env_r = float(nre.clamp_pos_ko(ee_r[fi][:3], ee_r[fi][3:7])[2])
        # cross-check: FK(achieved arm_q) must match the live EE-pose measure (validates both legs).
        fk_l, fk_r = fk_claw_z(ach_q[fi])
        fk_xcheck_max = max(fk_xcheck_max, abs(fk_l - claw_env_l), abs(fk_r - claw_env_r))
        rec_l, rec_r = fk_claw_z(rec_arm_q[rec_f])
        cab_env_l = lane_z(env_cable[fi], WIDE_LEFT_Y)
        cab_env_r = lane_z(env_cable[fi], WIDE_RIGHT_Y)
        cab_rec_l = lane_z(rec_cable[rec_f], WIDE_LEFT_Y)
        cab_rec_r = lane_z(rec_cable[rec_f], WIDE_RIGHT_Y)
        rows.append(
            {
                "frame": rec_f,
                "t": t,
                "L_claw_z_env": round(claw_env_l, 5),
                "L_claw_z_rec": round(rec_l, 5),
                "L_cable_z_env": round(cab_env_l, 5),
                "L_cable_z_rec": round(cab_rec_l, 5),
                "dL_env_rec_mm": round((claw_env_l - rec_l) * 1e3, 2),
                "dL_claw_cable_env_mm": round((claw_env_l - cab_env_l) * 1e3, 2),
                "R_claw_z_env": round(claw_env_r, 5),
                "R_claw_z_rec": round(rec_r, 5),
                "R_cable_z_env": round(cab_env_r, 5),
                "R_cable_z_rec": round(cab_rec_r, 5),
                "dR_env_rec_mm": round((claw_env_r - rec_r) * 1e3, 2),
                "dR_claw_cable_env_mm": round((claw_env_r - cab_env_r) * 1e3, 2),
            }
        )

    arr = {k: np.asarray([r[k] for r in rows]) for k in rows[0] if k not in ("frame", "t")}
    cmd_vs_ach = np.abs(ach_q - cmd_q)
    arm_cols = list(range(0, 6)) + list(range(14, 20))  # arm joints only (gripper cols are servo-dynamic)

    # ---- ROOT-CAUSE leg (EE_Z_FLOOR_KO target clip): the route target = recorded achieved ee_pos
    # (route_executor.step_target), but _apply_actions_batch clips target z to EE_Z_FLOOR_KO
    # (newton_route_env.py:988-989) BEFORE the IK solve. If the recorded grasp-park ee z sits BELOW the
    # floor, the env commands a raised target and tracks IT faithfully (small ik_resid vs the CLIPPED
    # target) while diverging from the recording by exactly the clip depth. ----
    floor = float(nre.EE_Z_FLOOR_KO)
    rec_ee_l = np.asarray(gz["ee_pos_l"], dtype=np.float64)
    rec_ee_r = np.asarray(gz["ee_pos_r"], dtype=np.float64)
    fr_all = np.arange(n_rec)
    floor_leg = {"EE_Z_FLOOR_KO": round(floor, 5)}
    for nm, rec_ee, env_ee in (("L", rec_ee_l, ee_l), ("R", rec_ee_r, ee_r)):
        below = rec_ee[:, 2] < floor
        env_park = env_ee[T_LO_TABLE * CADENCE : min(112 * CADENCE, n_frames), 2]
        floor_leg[nm] = {
            "rec_below_floor_frames": [int(fr_all[below].min()), int(fr_all[below].max())] if below.any() else None,
            "rec_below_floor_count": int(below.sum()),
            "rec_clip_depth_max_mm": round(float((floor - rec_ee[below, 2]).max()) * 1e3, 2) if below.any() else 0.0,
            "rec_ee_z_park": round(float(rec_ee[1000, 2]), 5),
            "env_achieved_ee_z_park_mean": round(float(np.mean(env_park)), 5),
            "env_park_minus_floor_mm": round((float(np.mean(env_park)) - floor) * 1e3, 2),
        }
    summary = {
        "close_window": f"t={T_LO_TABLE}..{rows[-1]['t']} (frames {rows[0]['frame']}..{rows[-1]['frame']})",
        "L_claw_bias_env_minus_rec_mm": {
            "mean": round(float(np.mean(arr["dL_env_rec_mm"])), 2),
            "min": round(float(np.min(arr["dL_env_rec_mm"])), 2),
            "max": round(float(np.max(arr["dL_env_rec_mm"])), 2),
        },
        "R_claw_bias_env_minus_rec_mm": {
            "mean": round(float(np.mean(arr["dR_env_rec_mm"])), 2),
            "min": round(float(np.min(arr["dR_env_rec_mm"])), 2),
            "max": round(float(np.max(arr["dR_env_rec_mm"])), 2),
        },
        "L_claw_minus_cable_env_mm": {
            "mean": round(float(np.mean(arr["dL_claw_cable_env_mm"])), 2),
            "min": round(float(np.min(arr["dL_claw_cable_env_mm"])), 2),
            "max": round(float(np.max(arr["dL_claw_cable_env_mm"])), 2),
        },
        "R_claw_minus_cable_env_mm": {
            "mean": round(float(np.mean(arr["dR_claw_cable_env_mm"])), 2),
            "min": round(float(np.min(arr["dR_claw_cable_env_mm"])), 2),
            "max": round(float(np.max(arr["dR_claw_cable_env_mm"])), 2),
        },
        "fk_xcheck_live_vs_fk_max_mm": round(fk_xcheck_max * 1e3, 4),
        "cmd_vs_achieved_arm_q_max_rad": round(float(np.max(cmd_vs_ach[:, arm_cols])), 6),
        "ik_resid_close_window_max_m": {
            "R": round(float(np.max(ik_resid[T_LO_TABLE:, 0])), 5) if ik_resid.shape[0] > T_LO_TABLE else None,
            "L": round(float(np.max(ik_resid[T_LO_TABLE:, 1])), 5) if ik_resid.shape[0] > T_LO_TABLE else None,
        },
        "latch": latch_meta,
    }

    result = {
        "context": "arm_q-direct diagnosis (Rs GO 13:18): quantify the env claw z vs recording claw z vs "
        "cable z through descend->close; suspect = systematic env batched-IK claw-z bias (Rs human-GT: "
        "L finger clamped BELOW the cable).",
        "frame_convention": "env RL step t sub-frame i -> recording frame t*10+i+1 (clamped); +-1-frame "
        "ambiguity bounded by the parked recording claw (back-check: constant z, interp dev <=0.28mm)",
        "summary": summary,
        "root_cause_floor_clip": {
            **floor_leg,
            "readout": "ROOT CAUSE PINNED: the recorded grasp-park ee z (1.06680, BOTH arms) sits below "
            "EE_Z_FLOOR_KO (newton_route_env.py:163) across exactly the close window, so the target z clip "
            "(newton_route_env.py:988-989) raises the commanded target by the clip depth (~3.1mm); the env "
            "tracks the CLIPPED target near-perfectly (ik_resid <=0.33mm, cmd==achieved) -> claw parks "
            "+3.07mm above the recording SYMMETRICALLY -> the close pushes the cable down/under (env lane "
            "cable sinks to L 0.79400 / R 0.78917 vs recording ~0.804) instead of caging it in the throat. "
            "The pre-registered suspect (batched-IK claw-z bias, L-low asymmetric) is REFUTED by direct "
            "measurement: the divergence is target-construction (floor clip), not IK, and is symmetric; "
            "the L-vs-R outcome asymmetry is downstream contact dynamics, not commanded-path asymmetry.",
        },
        "close_window_table_per_frame": rows,
        "video_leg_loud": "OMITTED per the Rs GO output spec (table + JSON): same trajectory as G1 whose "
        "video leg + Rs human-GT verdict are banked (run 13d37af1d5, FAIL banking 6e0c7fe420); this run "
        "adds numeric state capture only",
        "reproducibility_loud": "INIT_XY_NOISE perturbs only the reset _ee_target (unused by the replay "
        "drive path) -> same arm path as G1 modulo device numerics",
    }
    OUT_JSON.write_text(json.dumps(result, indent=1))

    print("\nframe |  L_env    L_rec   dL(mm) | L_cab_env dLc(mm) |  R_env    R_rec   dR(mm) | R_cab_env dRc(mm)")
    for r in rows:
        if r["frame"] % CADENCE == 0:  # per-RL-step rows for the readable table (full per-frame in JSON)
            print(
                f"{r['frame']:5d} | {r['L_claw_z_env']:.5f} {r['L_claw_z_rec']:.5f} {r['dL_env_rec_mm']:7.2f} | "
                f"{r['L_cable_z_env']:.5f} {r['dL_claw_cable_env_mm']:7.2f} | "
                f"{r['R_claw_z_env']:.5f} {r['R_claw_z_rec']:.5f} {r['dR_env_rec_mm']:7.2f} | "
                f"{r['R_cable_z_env']:.5f} {r['dR_claw_cable_env_mm']:7.2f}"
            )
    print("\nsummary:", json.dumps(summary, indent=1))
    print("\nroot_cause_floor_clip:", json.dumps(result["root_cause_floor_clip"], indent=1))
    print(f"-> {OUT_JSON}")
    return 0


def main():
    if "--stage" in sys.argv and sys.argv[sys.argv.index("--stage") + 1] == "table":
        return stage_table()
    return stage_run()


if __name__ == "__main__":
    sys.exit(main())
