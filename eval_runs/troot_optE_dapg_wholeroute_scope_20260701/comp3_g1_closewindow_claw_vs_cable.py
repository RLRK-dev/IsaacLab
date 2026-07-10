# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""comp3 G1 close-window claw-vs-cable z back-check (no-GPU; Rs human-GT mechanism verification).

Rs human-GT on the G1 videos (final G1 verdict, %12 13:08): the L finger CLAMPED BELOW the cable ->
missed the cage throat. This script quantifies the close window (t ~= 95-112, physics frames ~950-1120)
from EXISTING artifacts only (no GPU, no re-run):

  (1) RECORDING side (fully computable): per-frame claw clamp z for L/R via FK(arm_q[f][0:28]) on a
      CPU-built robot-only FK model + clamp_pos_ko (the env's own claw-point measure, single-source),
      vs the cable z at each grasp lane (cable_xyz[f] segment nearest WIDE_LEFT_Y / WIDE_RIGHT_Y).
  (2) ENV side ACTUAL: **NOT CAPTURED by the G1 runner** (data gap, reported loud): the runner saved
      driver-q minima, post-latch RELATIVE slips (latch offsets off_l/off_r not saved), post-latch
      held_z, contacts, and renders -- no per-frame achieved arm_q / claw pose / ik_resid. The env
      column below is therefore a PROXY: linear interpolation of the recording claw z between the
      route waypoint frames cf[t] -> cf[t+1] (the env drives 10-frame LINEAR joint interp toward the
      IK solution of the cf[t+1] waypoint), with caveats: assumes the env IK reaches the recorded
      pose at waypoint boundaries (ignores IK-config divergence -- the OTHER suspect) and joint-space
      vs cartesian interp differences (second order).
  (3) Missing-data report for the arm_q-direct diagnosis run (GPU ~6min, needs GO): per-frame achieved
      arm_q (or claw pose via clamp_pos_ko) + per-frame ik_resid + latch offsets, close window.

Run:
    CUDA_VISIBLE_DEVICES='' NEWTON_DEVICE=cpu /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp3_g1_closewindow_claw_vs_cable.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parent
_REPO = _EVAL_DIR.parent.parent
_TIL = _REPO / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "", "no-GPU back-check: run with CUDA_VISIBLE_DEVICES=''"

import newton  # noqa: E402
import newton_route_env as nre  # noqa: E402
from newton_skill_env_base import build_fk_and_init  # noqa: E402
from task_config import FINGER_OPEN_POS, WIDE_LEFT_Y, WIDE_RIGHT_Y  # noqa: E402

GOLDEN_NPZ = _EVAL_DIR / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
OUT_JSON = _EVAL_DIR / "comp3_g1_closewindow_result.json"
CADENCE = 10
T_LO, T_HI = 90, 114  # close window RL steps (frames 900..1140; cage90 onset f910, full close ~f1123)


def main():
    z = np.load(GOLDEN_NPZ)
    arm_q = np.asarray(z["arm_q"], dtype=np.float64)  # [frames, 74]; arm+gripper = [0:28]
    cable = np.asarray(z["cable_xyz"], dtype=np.float64)  # [frames, 40, 3]

    fk_model, fk_state, _ = build_fk_and_init(
        left_finger_pos=FINGER_OPEN_POS, right_finger_pos=FINGER_OPEN_POS, device="cpu"
    )

    def claw_z_at(frame):
        jq = fk_state.joint_q.numpy()
        jq[:28] = arm_q[frame, :28]
        fk_state.joint_q.assign(jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        bq = fk_state.body_q.numpy()
        cl = nre.clamp_pos_ko(bq[nre._LEFT_EE_BODY][:3], bq[nre._LEFT_EE_BODY][3:7])
        cr = nre.clamp_pos_ko(bq[nre._RIGHT_EE_BODY][:3], bq[nre._RIGHT_EE_BODY][3:7])
        return float(cl[2]), float(cr[2])

    def cable_z_at(frame, lane_y):
        seg = int(np.argmin(np.abs(cable[frame, :, 1] - lane_y)))
        return float(cable[frame, seg, 2])

    rows = []
    # per-RL-step table over the close window + per-physics-frame detail at the close onset.
    for t in range(T_LO, T_HI + 1):
        f = t * CADENCE
        clz, crz = claw_z_at(f)
        cabl = cable_z_at(f, WIDE_LEFT_Y)
        cabr = cable_z_at(f, WIDE_RIGHT_Y)
        # env PROXY at waypoint boundary frames == recording claw z (interp endpoints coincide there);
        # mid-window lag is shown in the sub-frame detail below.
        rows.append(
            {
                "t": t,
                "frame": f,
                "L_claw_z_rec": round(clz, 5),
                "L_cable_z": round(cabl, 5),
                "dL_rec_mm": round((clz - cabl) * 1e3, 2),
                "R_claw_z_rec": round(crz, 5),
                "R_cable_z": round(cabr, 5),
                "dR_rec_mm": round((crz - cabr) * 1e3, 2),
            }
        )

    # sub-frame interp-lag proxy: within each RL step [cf[t], cf[t+1]] the env claw z ~= LINEAR interp of
    # the endpoint claw z's, while the recording moved along its own curve -> lag = proxy - recorded.
    lag_rows = []
    for t in range(T_LO, T_HI):
        f0, f1 = t * CADENCE, (t + 1) * CADENCE
        z0l, z0r = claw_z_at(f0)
        z1l, z1r = claw_z_at(f1)
        worst_l = worst_r = 0.0
        for i in range(1, CADENCE):
            fl, fr = claw_z_at(f0 + i)
            pl = z0l + (z1l - z0l) * i / CADENCE
            pr = z0r + (z1r - z0r) * i / CADENCE
            if abs(pl - fl) > abs(worst_l):
                worst_l = pl - fl  # SIGNED: negative = proxy (env est.) BELOW the recorded claw
            if abs(pr - fr) > abs(worst_r):
                worst_r = pr - fr
        lag_rows.append(
            {"t": t, "L_interp_lag_worst_mm": round(worst_l * 1e3, 2), "R_interp_lag_worst_mm": round(worst_r * 1e3, 2)}
        )

    result = {
        "verdict_context": "Rs human-GT (G1 final): L finger clamped BELOW the cable -> missed the cage. "
        "This back-check quantifies the RECORDING geometry + the interp-lag proxy from existing artifacts.",
        "close_window_table": rows,
        "interp_lag_proxy": lag_rows,
        "env_actual_data_gap": {
            "missing": [
                "per-frame achieved arm_q (or claw pose via clamp_pos_ko) during the G1 run",
                "per-frame ik_resid (env computed _last_ik_resid but the runner did not save it)",
                "latch offsets off_l/off_r (used for the slip series but not persisted)",
            ],
            "available_env_anchors": [
                "driver-q minima per step (L stall 0.70-0.71 vs R 0.739)",
                "post-latch RELATIVE slips + held_z (L held seg sank to 0.782)",
                "render frames (visual; basis of the Rs human-GT)",
            ],
            "note": "env claw z during close is NOT reconstructable from saved artifacts without a re-run; "
            "the arm trajectory is arm-kinematic (cable-independent) so an arm_q-direct diagnosis run can "
            "capture it exactly (GPU ~6min, cuda:0, needs GO). INIT_XY_NOISE only perturbs the reset "
            "_ee_target (unused by the replay drive path) -> the diagnosis run reproduces the G1 arm path "
            "modulo device-numerics.",
        },
    }
    OUT_JSON.write_text(json.dumps(result, indent=1))

    print("frame | L_claw_rec  L_cable  dL(mm) | R_claw_rec  R_cable  dR(mm)")
    for r in rows:
        print(
            f"{r['frame']:5d} | {r['L_claw_z_rec']:.5f} {r['L_cable_z']:.5f} {r['dL_rec_mm']:7.2f} | "
            f"{r['R_claw_z_rec']:.5f} {r['R_cable_z']:.5f} {r['dR_rec_mm']:7.2f}"
        )
    print("\ninterp-lag proxy (worst sub-frame |proxy - recorded| claw z per step):")
    for r in lag_rows:
        print(f"  t={r['t']:3d}  L={r['L_interp_lag_worst_mm']:6.2f}mm  R={r['R_interp_lag_worst_mm']:6.2f}mm")
    print(f"\n-> {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
