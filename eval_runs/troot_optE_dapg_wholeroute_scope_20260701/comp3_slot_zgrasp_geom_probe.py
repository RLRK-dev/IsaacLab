# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Slot-redesign + z_grasp study: BUILT-MODEL claw geometry readback (no-GPU, CPU).

Feeds SLOT_REDESIGN_STUDY_COORD_20260710.md (Rs design directives 23:02/23:04/23:06). Per Rs (a): claw
geometry from the AS-BUILT model readback (mj_model geoms), NOT synthetic/asset-XML alone.

Legs:
  G (claw geometry): identify each arm's koshape pad/f1ext/f2ext geoms by name in mj_model; report
     as-built sizes + world extents at the settled P0 pose: per-claw Y footprint (the along-cable width a
     per-finger slot must admit), X gap between opposing pads, and the throat z-structure (f1ext bottom
     plate top surface / f2ext top plate bottom surface / the 14mm ko gap) as offsets from the wrist EE.
  Z (z_grasp variants): with the recorded grasp-park EE z (1.06680) and the throat offsets, tabulate the
     cable-center position INSIDE the throat (distance above the f1ext plate / below f2ext) at z_grasp
     {+0, +3, +4, +5}mm, using the settled cable center z 0.8040 (table-resting) -- the geometric leg of
     the Rs bend hypothesis (clamp-too-low -> cable near throat top -> bend under close).

Run:
    CUDA_VISIBLE_DEVICES='' NEWTON_DEVICE=cpu /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp3_slot_zgrasp_geom_probe.py
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

import mujoco  # noqa: E402
import newton_route_env as nre  # noqa: E402

GOLDEN_NPZ = _EVAL_DIR / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
OUT_JSON = _EVAL_DIR / "comp3_slot_zgrasp_geom_result.json"
REC_PARK_EE_Z = 1.06680  # recorded grasp-park EE z (both arms; comp3_g1_armq_diag)
SETTLED_CABLE_Z = 0.8040  # table-resting cable center (env settle == recording)


def main():
    print("[GEOM] building flag-ON + g1_scene_align env on CPU ...")
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
    m = env._solver.mj_model
    d = env._solver.mj_data
    mujoco.mj_forward(m, d)

    result = {"claw_geoms_as_built": {}, "y_footprint_mm": {}, "throat_z_structure": {}, "z_grasp_variants": []}
    # leg G: named koshape geoms readback (as-built sizes + world pose at P0).
    names = {}
    for g in range(int(m.ngeom)):
        gname = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or ""
        if any(k in gname for k in ("pad1", "pad2", "f1ext", "f2ext")):
            names[gname] = g
    per_claw = {}
    for gname, g in sorted(names.items()):
        size = [float(x) for x in m.geom_size[g]]
        wpos = [float(x) for x in d.geom_xpos[g]]
        xmat = np.asarray(d.geom_xmat[g]).reshape(3, 3)
        # world-axis half-extents of the box: |R| @ size
        wext = np.abs(xmat) @ np.asarray(size)
        # NOTE: the asset's left_pad*/right_pad* names are the TWO FINGERS OF ONE GRIPPER and collide
        # across the two arms -> key by geom id and group arms by WORLD Y (L lane ~0.106 / R ~0.194).
        key = f"{gname}#g{g}"
        result["claw_geoms_as_built"][key] = {
            "size_half": size,
            "world_pos": [round(v, 5) for v in wpos],
            "world_half_extent_xyz": [round(float(v), 5) for v in wext],
        }
        arm = "L" if wpos[1] < 0.15 else "R"
        per_claw.setdefault(arm, []).append((gname, wpos, wext))
    for arm, geoms in per_claw.items():
        y_lo = min(p[1] - e[1] for _, p, e in geoms)
        y_hi = max(p[1] + e[1] for _, p, e in geoms)
        x_lo = min(p[0] - e[0] for _, p, e in geoms)
        x_hi = max(p[0] + e[0] for _, p, e in geoms)
        result["y_footprint_mm"][arm] = {
            "y_extent": [round(y_lo, 5), round(y_hi, 5)],
            "width_mm": round((y_hi - y_lo) * 1e3, 2),
            "x_extent": [round(x_lo, 5), round(x_hi, 5)],
        }
    # throat z structure: f1ext/f2ext plate z offsets measured DIRECTLY from the P0 world poses minus the
    # EE z (pose-rigid at the upright grasp orientation; EE bodies via the newton state, asset-name-free).
    bq = env._state_0.body_q.numpy()
    ee_l_z = float(bq[env._bws[0] + nre._LEFT_EE_BODY][2])
    ee_r_z = float(bq[env._bws[0] + nre._RIGHT_EE_BODY][2])
    for arm, ee_z in (("L", ee_l_z), ("R", ee_r_z)):
        rows = {}
        for gname, p, e in per_claw[arm]:
            key = "f1ext" if "f1ext" in gname else "f2ext" if "f2ext" in gname else gname
            rows.setdefault(key, {})  # f1ext/f2ext exist once per finger-side; offsets identical (z-mirror)
            rows[key] = {
                "z_top_off_ee": round(p[2] + e[2] - ee_z, 5),
                "z_bot_off_ee": round(p[2] - e[2] - ee_z, 5),
            }
        f1_top = rows["f1ext"]["z_top_off_ee"]  # bottom claw plate TOP surface (cable rests above this)
        f2_bot = rows["f2ext"]["z_bot_off_ee"]  # top claw plate BOTTOM surface
        result["throat_z_structure"][arm] = {
            "offsets_from_ee": rows,
            "ko_gap_mm": round((f2_bot - f1_top) * 1e3, 2),
        }
    # leg Z: cable-center position in the throat at z_grasp variants (geometry only; park EE z + dz).
    f1_top_off = result["throat_z_structure"]["L"]["offsets_from_ee"]["f1ext"]["z_top_off_ee"]
    f2_bot_off = result["throat_z_structure"]["L"]["offsets_from_ee"]["f2ext"]["z_bot_off_ee"]
    for dz_mm in (0, 3, 4, 5):
        ee_z = REC_PARK_EE_Z + dz_mm * 1e-3
        f1_top = ee_z + f1_top_off
        f2_bot = ee_z + f2_bot_off
        result["z_grasp_variants"].append(
            {
                "dz_mm": dz_mm,
                "park_ee_z": round(ee_z, 5),
                "f1ext_plate_top_z": round(f1_top, 5),
                "f2ext_plate_bot_z": round(f2_bot, 5),
                "cable_above_f1ext_mm": round((SETTLED_CABLE_Z - f1_top) * 1e3, 2),
                "cable_below_f2ext_mm": round((f2_bot - SETTLED_CABLE_Z) * 1e3, 2),
            }
        )
    OUT_JSON.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    print(f"-> {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
