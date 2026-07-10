# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""comp3 drive-path decision packet: cost + IK-config-delta evidence probe (no-GPU, CPU).

Feeds COMP3_DRIVEPATH_DECISION_PACKET_COORD_20260710.md (%12 design-gate dispatch 19:07). Two legs:

leg T (timing, CPU): builds the flag-ON + g1_scene_align env on the CPU substrate (the established
    no-GPU probe substrate, comp3_void_readback precedent) and measures medians of (a) one batched IK
    solve (env._solve_ik_batch, IK_ITERATIONS_RL=30) (b) one physics frame at 4 substeps (production
    RL drive) (c) one physics frame at 10 substeps. Emits throughput models for drive-path options:
      current: T = t_IK + 10*t_f4          A (per-frame IK):  T = 10*t_IK + 10*t_f4
      B (sub10): T = t_IK + 10*t_f10       C (A+B):           T = 10*t_IK + 10*t_f10
      D (hybrid, rho = residual-window step fraction): T = rho*T_A_or_current + (1-rho)*(10*t_f4)
        (feedforward steps skip IK entirely -> D is CHEAPER than current on scripted steps)
    LOUD caveat: production trains with warp/IK kernels on cuda:0 + mujoco-CPU stepping; this CPU
    probe approximates RATIOS (both legs on the same CPU substrate), not absolute cuda wall-clocks.
    A ~1min GPU micro-probe can pin absolute numbers on request (surfaced, not run -- no-GPU dispatch).

leg Q (IK-config delta, CPU): quantifies WHY option A is NOT proven by the arm_q-direct run: the
    confirmation capture (comp3_g1_armq_diag_capture.npz, post-floor-fix, IK-DRIVEN at 4-sub) matched
    the recording's claw POSITION (z bias -0.04mm) yet L still paid through in the retry; the
    arm_q-direct bypass (which removes the IK solution + chord entirely) fixed L. The remaining
    IK-attributable delta is the CONFIGURATION/ORIENTATION of the claw: this leg measures the EE
    quaternion angle between the IK-driven capture and FK(recorded arm_q) at matched frames across the
    close window. A per-frame-target IK (option A) would still solve with the env's batched-IK config
    (rot-weight 0.5 / jlimit 10 / OPEN-finger warm start) and could retain this orientation delta.

Run:
    CUDA_VISIBLE_DEVICES='' NEWTON_DEVICE=cpu /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp3_drivepath_cost_probe.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parent
_REPO = _EVAL_DIR.parent.parent
_TIL = _REPO / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "", "no-GPU probe: run with CUDA_VISIBLE_DEVICES=''"

import newton  # noqa: E402
import newton_route_env as nre  # noqa: E402
from newton_skill_env_base import RL_SIM_DT, RL_SIM_SUBSTEPS, SIM_DT, SIM_SUBSTEPS, build_fk_and_init  # noqa: E402
from task_config import FINGER_OPEN_POS  # noqa: E402

GOLDEN_NPZ = _EVAL_DIR / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
CAPTURE_NPZ = _EVAL_DIR / "comp3_g1_armq_diag_capture.npz"
OUT_JSON = _EVAL_DIR / "comp3_drivepath_cost_probe_result.json"
T_LO, T_HI = 90, 112  # close-window park frames for leg Q (pre full-close)


def quat_angle_deg(q1_xyzw, q2_xyzw):
    d = abs(float(np.dot(q1_xyzw / np.linalg.norm(q1_xyzw), q2_xyzw / np.linalg.norm(q2_xyzw))))
    return float(np.degrees(2.0 * np.arccos(min(d, 1.0))))


def main():
    result = {"leg_T_timing": {}, "leg_Q_ik_config_delta": {}}
    skip_timing = "--skip-timing" in sys.argv
    if skip_timing:
        result["leg_T_timing"] = json.loads(OUT_JSON.read_text())["leg_T_timing"]
        print("[T] --skip-timing: leg_T reused from existing JSON")
        return _leg_q(result)

    # ---- leg T: timing on the CPU probe substrate ----
    print("[T] building flag-ON + g1_scene_align env on CPU ...")
    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cpu",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(GOLDEN_NPZ),
            "g1_scene_align": True,
        },
    )
    env.reset()
    jq_starts = np.array(env._per_world_fk_jq[:1])
    tl = np.array([env._settled_ee_l_pos], dtype=np.float32)
    tr = np.array([env._settled_ee_r_pos], dtype=np.float32)

    def med_time(fn, n, warmup=3):
        for _ in range(warmup):
            fn()
        ts = []
        for _ in range(n):
            t0 = time.perf_counter()
            fn()
            ts.append(time.perf_counter() - t0)
        return float(np.median(ts))

    t_ik = med_time(lambda: env._solve_ik_batch(tl + 0.001, tr + 0.001, jq_starts), 20)
    t_f4 = med_time(lambda: env._physics_step_all(substeps=RL_SIM_SUBSTEPS, sim_dt=RL_SIM_DT), 60)
    t_f10 = med_time(lambda: env._physics_step_all(substeps=SIM_SUBSTEPS, sim_dt=SIM_DT), 60)

    def model(name, t_step):
        return {"t_step_ms": round(t_step * 1e3, 2), "steps_per_s": round(1.0 / t_step, 2)}

    cur = t_ik + 10 * t_f4
    models = {
        "current (1xIK + 10xf4)": model("current", cur),
        "A per-frame IK (10xIK + 10xf4)": model("A", 10 * t_ik + 10 * t_f4),
        "B sub10 (1xIK + 10xf10)": model("B", t_ik + 10 * t_f10),
        "C A+B (10xIK + 10xf10)": model("C", 10 * t_ik + 10 * t_f10),
        "D rho=0 feedforward-only (10xf4, no IK)": model("D0", 10 * t_f4),
        "D rho=0.25 (A-style residual steps)": model("D25", 0.25 * (10 * t_ik + 10 * t_f4) + 0.75 * 10 * t_f4),
    }
    result["leg_T_timing"] = {
        "substrate_loud": "CPU probe substrate (both numerator and denominator on CPU) -- RATIO evidence;"
        " production = warp/IK on cuda:0 + mujoco-CPU stepping; ~1min GPU micro-probe available on"
        " request (not run: no-GPU dispatch)",
        "t_ik_solve_ms": round(t_ik * 1e3, 2),
        "t_frame_4sub_ms": round(t_f4 * 1e3, 2),
        "t_frame_10sub_ms": round(t_f10 * 1e3, 2),
        "ik_share_of_current_step": round(t_ik / cur, 3),
        "throughput_models": models,
        "relative_to_current": {k: round((t_ik + 10 * t_f4) / (v["t_step_ms"] / 1e3), 2) for k, v in models.items()},
    }
    print(json.dumps(result["leg_T_timing"], indent=1))

    return _leg_q(result)


def _leg_q(result):
    # ---- leg Q: IK-config (orientation) delta at matched frames, TWO windows ----
    # descend (t=60..89, arms in MOTION -> includes the interp/chord dynamic delta) and close park
    # (t=90..111, arms static -> pure IK-solution equilibrium delta).
    print("[Q] measuring EE orientation delta: IK-driven capture vs FK(recorded arm_q) ...")
    cap = np.load(CAPTURE_NPZ)
    ee_l, ee_r = np.asarray(cap["ee_l"], dtype=np.float64), np.asarray(cap["ee_r"], dtype=np.float64)
    rec_arm_q = np.asarray(np.load(GOLDEN_NPZ)["arm_q"], dtype=np.float64)
    fk_model, fk_state, _ = build_fk_and_init(
        left_finger_pos=FINGER_OPEN_POS, right_finger_pos=FINGER_OPEN_POS, device="cpu"
    )

    def rec_ee_quat(frame):
        jq = fk_state.joint_q.numpy()
        jq[:28] = rec_arm_q[frame, :28]
        fk_state.joint_q.assign(jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        bq = fk_state.body_q.numpy()
        return bq[nre._LEFT_EE_BODY][3:7].copy(), bq[nre._RIGHT_EE_BODY][3:7].copy()

    windows = {"descend_motion_t60_89": (60, 90), "close_park_t90_111": (90, 112)}
    out = {
        "meaning": "EE orientation angle [deg] between the IK-DRIVEN post-fix capture (position-matched,"
        " z bias -0.04mm) and FK(recorded arm_q). close_park = static IK equilibrium delta;"
        " descend_motion = dynamic delta incl the 10-frame joint-interp chord. This is the residual"
        " IK-path-attributable delta that option A (per-frame targets, same batched-IK config) may"
        " RETAIN and that the arm_q-direct bypass removed.",
        "claw_arm_note": "clamp point sits 260.92mm below the EE -- 1 deg of EE tilt displaces the claw"
        " tip by ~4.6mm laterally (EE_TO_PINCH_OPEN * sin(1deg))",
    }
    for wname, (lo, hi) in windows.items():
        ang_l, ang_r = [], []
        for t in range(lo, hi):
            for sub in (0, 4, 9):  # sample start/mid/end sub-frames (dynamic delta varies within a step)
                fi = t * 10 + sub
                if fi >= ee_l.shape[0]:
                    continue
                ql_rec, qr_rec = rec_ee_quat(min(fi + 1, rec_arm_q.shape[0] - 1))
                ang_l.append(quat_angle_deg(ee_l[fi][3:7], ql_rec))
                ang_r.append(quat_angle_deg(ee_r[fi][3:7], qr_rec))
        out[wname] = {
            "L_deg": {"mean": round(float(np.mean(ang_l)), 3), "max": round(float(np.max(ang_l)), 3)},
            "R_deg": {"mean": round(float(np.mean(ang_r)), 3), "max": round(float(np.max(ang_r)), 3)},
            "claw_tip_max_mm": round(0.26092 * np.sin(np.radians(float(np.max(ang_l + ang_r)))) * 1e3, 2),
        }
    result["leg_Q_ik_config_delta"] = out
    print(json.dumps(result["leg_Q_ik_config_delta"], indent=1))

    OUT_JSON.write_text(json.dumps(result, indent=1))
    print(f"-> {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
