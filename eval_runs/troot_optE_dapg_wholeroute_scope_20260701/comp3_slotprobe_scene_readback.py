# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Slot probe rider R1: as-built variant-scene READBACK (leg-C style) appended to the result JSON.

%12 rider R1 (00:24): the probe result must carry proxy-representativeness evidence -- the emitted table
box count + the AS-BUILT slot extents read back from the mj_model, checked against the study sec3a dims.
Single-source with the probe: imports _install_scene_patch/_PROBE_BOXES from comp3_slotprobe_grasplift
(the identical patch code path), builds the env on CPU (NEWTON_DEVICE=cpu; CUDA_VISIBLE_DEVICES=0 is
required by the runner module import assert -- warp merely initializes a context, the build runs on cpu),
bypasses lane_void_parity_assert the same sanctioned way, and appends "r1_scene_readback" to
comp3_slotprobe_result.json.

Run (after the probe run completes):
    CUDA_VISIBLE_DEVICES=0 NEWTON_DEVICE=cpu /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp3_slotprobe_scene_readback.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parent
_REPO = _EVAL_DIR.parent.parent
_TIL = _REPO / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs"), str(_EVAL_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import comp3_slotprobe_grasplift as probe  # noqa: E402  (runner module: patch code single-source)
import newton_route_env as nre  # noqa: E402

OUT_JSON = _EVAL_DIR / "comp3_slotprobe_result.json"
EXPECT_SLOTS_Y = [[0.093, 0.122], [0.181, 0.210]]
EXPECT_X = [0.234, 0.366]
TOL = 1e-6


def main():
    patch_state = probe._install_scene_patch()
    nre.lane_void_parity_assert = lambda m: print("[R1] parity assert bypassed (same sanctioned variant)")
    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cpu",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(probe.GOLDEN_NPZ),
            "g1_scene_align": True,
        },
    )
    m = env._solver.mj_model
    boxes = []
    for g in range(int(m.ngeom)):
        if int(m.geom_bodyid[g]) == 0 and abs(float(m.geom_size[g][2]) - 0.005) < TOL:
            if abs(float(m.geom_pos[g][2]) - 0.795) < TOL:
                boxes.append(
                    {
                        "half_xy": [round(float(m.geom_size[g][0]), 5), round(float(m.geom_size[g][1]), 5)],
                        "center_xy": [round(float(m.geom_pos[g][0]), 5), round(float(m.geom_pos[g][1]), 5)],
                        "y_extent": [
                            round(float(m.geom_pos[g][1]) - float(m.geom_size[g][1]), 5),
                            round(float(m.geom_pos[g][1]) + float(m.geom_size[g][1]), 5),
                        ],
                    }
                )
    # derive as-built slots: gaps in Y coverage of the FULL-X boxes (hx ~ 0.35) within [-0.40, 0.30].
    full_x = sorted((b for b in boxes if b["half_xy"][0] > 0.3), key=lambda b: b["center_xy"][1])
    slots = []
    for a, b in zip(full_x[:-1], full_x[1:]):
        lo, hi = a["y_extent"][1], b["y_extent"][0]
        if hi - lo > 1e-6:
            slots.append([round(lo, 5), round(hi, 5)])
    x_fills = [b for b in boxes if b["half_xy"][0] <= 0.3]
    x_window = (
        [
            round(x_fills[0]["center_xy"][0] + x_fills[0]["half_xy"][0], 5),
            round(x_fills[1]["center_xy"][0] - x_fills[1]["half_xy"][0], 5),
        ]
        if len(x_fills) == 2
        else None
    )
    ok = (
        len(boxes) == len(probe._PROBE_BOXES)
        and patch_state["suppressed"] == 4
        and len(slots) == 2
        and all(abs(s[i] - e[i]) < 1e-4 for s, e in zip(slots, EXPECT_SLOTS_Y) for i in (0, 1))
        and x_window is not None
        and abs(x_window[0] - EXPECT_X[0]) < 1e-4
        and abs(x_window[1] - EXPECT_X[1]) < 1e-4
    )
    block = {
        "emitted_table_boxes": len(boxes),
        "suppressed_original_boxes": patch_state["suppressed"],
        "as_built_slots_y": slots,
        "as_built_x_window": x_window,
        "expected_sec3a": {"slots_y": EXPECT_SLOTS_Y, "x_window": EXPECT_X},
        "match": bool(ok),
        "boxes": boxes,
    }
    result = json.loads(OUT_JSON.read_text())
    result["r1_scene_readback"] = block
    OUT_JSON.write_text(json.dumps(result, indent=1))
    print(json.dumps(block, indent=1))
    print(f"-> appended r1_scene_readback to {OUT_JSON} (match={ok})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
