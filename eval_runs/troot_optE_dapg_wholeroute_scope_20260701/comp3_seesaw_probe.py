# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Rs human-GT #4 seesaw re-verification (no-GPU, existing data): camera map + per-arm engagement + lane z.

Rs #4 (01:4x): 'the NEAR (手前) side now clamps but the FAR (奥) side that WAS working now cannot -- why?'
This conflicts with my numeric report (R rise +76.5 = holds). %12: rise can come from a HOOK (clamp
quality != rise); Rs human-GT is the authority; re-verify the numeric/analyst representativeness.

Legs (all from existing data, CPU):
  leg CAM: project the L-arm claw (lane Y~0.106) and R-arm claw (lane Y~0.194) + the cable TAIL to the
    zoom + ctx camera screens using the runner's exact free-camera params (az/el/dist/lookat). Reports,
    per camera: each arm's screen-x (left/right) + camera DEPTH (near/far = 手前/奥). VALIDATION: the
    cable tail must land lower-left (every analyst saw the anchor/tail at screen lower-left) -- if it does,
    the convention is trusted. This resolves the L/R <-> 手前/奥 mapping definitively (my analysts labeled
    foreground='L'; the geometry is checked here).
  leg ENG: per-cell x arm engagement proxies from the zsweep series (driver q at latch = closure; held-seg
    z trajectory; rise) -- clamp-quality proxies, NOT just rise.
  leg SEE: lane cable z (L/R) at close onset across cells (the seesaw datum: does one arm's lane cable
    sit higher/lower, and does the 'winner' flip with dz?).

Run:
    CUDA_VISIBLE_DEVICES='' NEWTON_DEVICE=cpu /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp3_seesaw_probe.py
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

assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "", "no-GPU probe: run with CUDA_VISIBLE_DEVICES=''"

import newton_route_env as nre  # noqa: E402

GOLDEN_NPZ = _EVAL_DIR / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
CAPTURE_NPZ = _EVAL_DIR / "comp3_g1_armq_diag_capture.npz"
ZSWEEP_JSON = _EVAL_DIR / "comp3_zsweep_result.json"
OUT_JSON = _EVAL_DIR / "comp3_seesaw_result.json"

# runner free-camera params (comp3_zsweep_grasplift.py _run_cell):
#   ctx  = _render(renderer, d, (0.30, 0.10, 0.85), az=100, el=-20, dist=0.9)
#   zoom = _render(renderer, d, tuple(mid),         az=120, el=-12, dist=0.16)   (mid = claw midpoint)
CAMS = {
    "ctx": {"lookat": (0.30, 0.10, 0.85), "az": 100.0, "el": -20.0, "dist": 0.9},
    "zoom": {"lookat": (0.30, 0.15, 0.806), "az": 120.0, "el": -12.0, "dist": 0.16},
}


def cam_frame(az_deg, el_deg, dist, lookat):
    a, e = np.radians(az_deg), np.radians(el_deg)
    to_cam = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])  # lookat -> camera (unit)
    pos = np.asarray(lookat) + dist * to_cam
    forward = -to_cam  # camera viewing direction (camera -> lookat)
    world_up = np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, world_up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    return pos, forward, right, up


def project(pt, pos, forward, right, up):
    v = np.asarray(pt) - pos
    depth = float(np.dot(v, forward))  # +ve in front; smaller = nearer
    sx = float(np.dot(v, right) / depth)  # screen x: -left / +right
    sy = float(np.dot(v, up) / depth)  # screen y: -down / +up
    return sx, sy, depth


def main():
    result = {"leg_CAM": {}, "leg_ENG": {}, "leg_SEE": {}}

    # world points: L/R arm claws at a park frame + the cable tail (long free end).
    gz = np.load(GOLDEN_NPZ)
    cable = np.asarray(gz["cable_xyz"], dtype=np.float64)  # [frames, 40, 3]
    f = 1000
    # arm claws via FK of the recorded arm_q (clamp_pos_ko), at park frame.
    import newton
    from newton_skill_env_base import build_fk_and_init
    from task_config import FINGER_OPEN_POS

    fk_model, fk_state, _ = build_fk_and_init(
        left_finger_pos=FINGER_OPEN_POS, right_finger_pos=FINGER_OPEN_POS, device="cpu"
    )
    jq = fk_state.joint_q.numpy()
    jq[:28] = np.asarray(gz["arm_q"], dtype=np.float64)[f, :28]
    fk_state.joint_q.assign(jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
    bq = fk_state.body_q.numpy()
    claw_L = np.asarray(nre.clamp_pos_ko(bq[nre._LEFT_EE_BODY][:3], bq[nre._LEFT_EE_BODY][3:7]))  # lane Y~0.106
    claw_R = np.asarray(nre.clamp_pos_ko(bq[nre._RIGHT_EE_BODY][:3], bq[nre._RIGHT_EE_BODY][3:7]))  # lane Y~0.194
    # cable tail = the free end farthest from the grasp midspan (both ends checked -> the longer-tail end).
    seg0, segN = cable[f, 0], cable[f, -1]
    mid = 0.5 * (claw_L + claw_R)
    tail = seg0 if np.linalg.norm(seg0 - mid) > np.linalg.norm(segN - mid) else segN

    for cname, cp in CAMS.items():
        pos, fwd, right, up = cam_frame(cp["az"], cp["el"], cp["dist"], cp["lookat"])
        pL = project(claw_L, pos, fwd, right, up)
        pR = project(claw_R, pos, fwd, right, up)
        pT = project(tail, pos, fwd, right, up)
        near = "L" if pL[2] < pR[2] else "R"
        result["leg_CAM"][cname] = {
            "cam_pos": [round(float(x), 4) for x in pos],
            "L_arm_Y0106": {"screen_x": round(pL[0], 3), "screen_y": round(pL[1], 3), "depth": round(pL[2], 4)},
            "R_arm_Y0194": {"screen_x": round(pR[0], 3), "screen_y": round(pR[1], 3), "depth": round(pR[2], 4)},
            "cable_tail": {"screen_x": round(pT[0], 3), "screen_y": round(pT[1], 3), "depth": round(pT[2], 4)},
            "NEAR_arm_手前": near,
            "FAR_arm_奥": "R" if near == "L" else "L",
            "L_screen_side": "left" if pL[0] < pR[0] else "right",
            "R_screen_side": "left" if pR[0] < pL[0] else "right",
            "tail_validation": f"screen ({'left' if pT[0] < 0 else 'right'},{'down' if pT[1] < 0 else 'up'})"
            " -- analysts saw the tail at lower-left; match => convention trusted",
        }

    # leg ENG + SEE from the zsweep series.
    z = json.loads(ZSWEEP_JSON.read_text())
    for c in z["cells"]:
        dz = c["dz_mm"]
        s = c["series"]
        lg = c["legs"]
        lt = lg["close_latched"]["latch_t"]
        ti = s["t"].index(lt) if lt in s["t"] else min(range(len(s["t"])), key=lambda i: abs(s["t"][i] - lt))
        # engagement proxies: driver q at latch (closure depth), held seg z at latch vs end (retention).
        result["leg_ENG"][f"dz{dz}"] = {
            "latch_t": lt,
            "l_drv_q_at_latch": s["l_drv_q"][ti] if ti < len(s["l_drv_q"]) else None,
            "r_drv_q_at_latch": s["r_drv_q"][ti] if ti < len(s["r_drv_q"]) else None,
            "L_rise_m": lg.get("lift_rise", {}).get("rise_l_m"),
            "R_rise_m": lg.get("lift_rise", {}).get("rise_r_m"),
            "L_z_drop_end_mm": lg.get("creep_budget", {}).get("L_z_drop", {}).get("end_mm"),
            "R_z_drop_end_mm": lg.get("creep_budget", {}).get("R_z_drop", {}).get("end_mm"),
            "note": "rise/z_drop are OUTCOME proxies; a positive rise can be a HOOK not a clamp"
            " (%12 rise!=clamp) -- crop the near-arm throat for the true clamp verdict (Rs human-GT)",
        }
        # seesaw: lane cable z (L/R) at close onset + the L-R difference.
        cl = s["cable_z_lane_l"][ti] if ti < len(s.get("cable_z_lane_l", [])) else None
        cr = s["cable_z_lane_r"][ti] if ti < len(s.get("cable_z_lane_r", [])) else None
        result["leg_SEE"][f"dz{dz}"] = {
            "close_onset_t": lt,
            "cable_z_lane_L": cl,
            "cable_z_lane_R": cr,
            "lane_dz_L_minus_R_mm": round((cl - cr) * 1e3, 2) if (cl is not None and cr is not None) else None,
            "claw_z_L": s["claw_z_l"][ti] if ti < len(s["claw_z_l"]) else None,
            "claw_z_R": s["claw_z_r"][ti] if ti < len(s["claw_z_r"]) else None,
        }

    OUT_JSON.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    print(f"-> {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
