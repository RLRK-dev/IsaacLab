# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""comp3 lane-floor 81-cell sweep artifact (5tai fold CC5-M1; adopted from CC5's independent repro).

Persists the lane-aware-floor verification sweep as a rerunnable artifact + JSON. Extensions over the
original geometric-design sweep (per 5tai verdict a35cb359a0):

- TWO column families, labeled (CC3-L3): ``achieved`` = ``ee_pos_l/r`` (the recorded ACHIEVED path --
  this is what the ENV clamp actually receives, since step_target's base target = the achieved-path
  waypoint per fork-(iv)); ``target`` = ``ee_tgt_pos_l/r`` (the RECORDING RUNNER's commanded target
  series -- deeper/earlier below the old floor: it shows the flag-OFF behavior change also covers
  descend frames before the achieved window).
- Floors are the AS-CODED env floors (imported from newton_route_env: lane + C1-island carve-out +
  clip-base), vectorized with a pointwise parity cross-check against ``ee_z_floor_ko``.
- REPLAY-NEUTRALITY machine check (R-A/R-B): at every below-old-floor frame of the achieved columns,
  BOTH arms must be in-lane and outside the C1 island -> the mode-0 shared max floor == the lane floor
  and the island carve-out never touches the replay path.
- Lane-edge clearance envelope at the below-old-floor frames per arm (CC4-F2: min is NOT the nominal
  cell's 13.8/16.0mm -- the grid offsets shrink it).
- C1 island: min recorded z inside the island footprint + gap above the island floor.

Run (CPU, read-only over recordings):
    CUDA_VISIBLE_DEVICES='' NEWTON_DEVICE=cpu /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/comp3_lane_floor_sweep.py
"""

from __future__ import annotations

import glob
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

assert os.environ.get("CUDA_VISIBLE_DEVICES", None) == "", "sweep is CPU-forced (CUDA_VISIBLE_DEVICES='')"

import newton_route_env as nre  # noqa: E402

BASE = _EVAL_DIR / "w0e_81rerun_snapdown_0537"
OUT_JSON = _EVAL_DIR / "comp3_lane_floor_sweep_result.json"

F_OLD = float(nre.EE_Z_FLOOR_KO)
F_LANE = float(nre.EE_Z_FLOOR_KO_LANE)
F_ISLAND = float(nre.EE_Z_FLOOR_KO_C1_ISLAND)
X_LO, X_HI = float(nre._LANE_X_LO), float(nre._LANE_X_HI)
Y_LO, Y_HI = float(nre._LANE_Y_LO), float(nre._LANE_Y_HI)
IX_LO, IX_HI = float(nre._C1_ISLAND_X_LO), float(nre._C1_ISLAND_X_HI)
IY_LO, IY_HI = float(nre._C1_ISLAND_Y_LO), float(nre._C1_ISLAND_Y_HI)

COLUMNS = {
    "achieved": ("ee_pos_l", "ee_pos_r"),  # recorded ACHIEVED path == the ENV clamp input (fork-(iv))
    "target": ("ee_tgt_pos_l", "ee_tgt_pos_r"),  # recording RUNNER's commanded targets (label: CC3-L3)
}


def floors_vec(p):
    """Vectorized as-coded floor (island > lane > clip-base), parity-checked vs ee_z_floor_ko."""
    in_island = (p[:, 0] >= IX_LO) & (p[:, 0] <= IX_HI) & (p[:, 1] >= IY_LO) & (p[:, 1] <= IY_HI)
    in_lane = (p[:, 0] >= X_LO) & (p[:, 0] <= X_HI) & (p[:, 1] >= Y_LO) & (p[:, 1] <= Y_HI)
    return np.where(in_island, F_ISLAND, np.where(in_lane, F_LANE, F_OLD)), in_lane, in_island


def main():
    # pointwise parity: the vectorized floor must equal the env fn (in-lane, island, edge, outside).
    for x, y in ((0.300, 0.106), (0.350, 0.150), (0.234, 0.090), (0.330, 0.135), (0.100, 0.250)):
        v = floors_vec(np.array([[x, y, 0.0]]))[0][0]
        assert v == nre.ee_z_floor_ko(x, y), f"floor parity mismatch at ({x},{y})"

    cells = sorted(glob.glob(str(BASE / "cell_*" / "route_demo_raw.npz")))
    res = {
        "floors": {"old_clip_base": F_OLD, "lane": F_LANE, "c1_island_float_aware": F_ISLAND},
        "lane_box": {"x": [X_LO, X_HI], "y": [Y_LO, Y_HI]},
        "c1_island_box": {"x": [IX_LO, IX_HI], "y": [IY_LO, IY_HI]},
        "cells": len(cells),
        "columns": {},
        "replay_neutrality": None,
        "lane_edge_clearance_below_old_mm": {},
        "c1_island": {},
        "boundary_crossings": {},
    }
    neutrality_violations = 0
    edge_env = {
        "L": {"x_lo": 1e9, "x_hi": 1e9, "y_lo": 1e9, "y_hi": 1e9},
        "R": {"x_lo": 1e9, "x_hi": 1e9, "y_lo": 1e9, "y_hi": 1e9},
    }
    island_min_z = 1e9
    cross_z_min = 1e9

    for fam, (kl, kr) in COLUMNS.items():
        stats = {
            "sweeps": 0,
            "frame_counts": set(),
            "below_old_counts": set(),
            "below_old_windows": set(),
            "below_new_total": 0,
            "min_margin_new_mm": 1e9,
            "park_z_min": 1e9,
            "park_z_max": -1e9,
        }
        for c in cells:
            z = np.load(c)
            per_arm = {}
            for arm, key in (("L", kl), ("R", kr)):
                p = np.asarray(z[key], dtype=np.float64)
                stats["sweeps"] += 1
                stats["frame_counts"].add(int(p.shape[0]))
                floor, in_lane, in_island = floors_vec(p)
                margin = p[:, 2] - floor
                below_old = p[:, 2] < F_OLD
                idx = np.nonzero(below_old)[0]
                stats["below_old_counts"].add(int(below_old.sum()))
                if idx.size:
                    stats["below_old_windows"].add((int(idx.min()), int(idx.max())))
                stats["below_new_total"] += int((margin < 0).sum())
                stats["min_margin_new_mm"] = min(stats["min_margin_new_mm"], float(margin.min()) * 1e3)
                stats["park_z_min"] = min(stats["park_z_min"], float(p[1000, 2]))
                stats["park_z_max"] = max(stats["park_z_max"], float(p[1000, 2]))
                per_arm[arm] = (p, below_old, in_lane, in_island)
                if fam == "achieved":
                    # lane-edge clearance envelope at below-old frames (CC4-F2).
                    if idx.size:
                        q = p[below_old]
                        e = edge_env[arm]
                        e["x_lo"] = min(e["x_lo"], float((q[:, 0] - X_LO).min()))
                        e["x_hi"] = min(e["x_hi"], float((X_HI - q[:, 0]).min()))
                        e["y_lo"] = min(e["y_lo"], float((q[:, 1] - Y_LO).min()))
                        e["y_hi"] = min(e["y_hi"], float((Y_HI - q[:, 1]).min()))
                    # C1 island min z (any frame in island footprint).
                    isl = (np.abs(p[:, 0] - 0.35) <= (IX_HI - 0.35)) & (np.abs(p[:, 1] - 0.15) <= (IY_HI - 0.15))
                    if isl.any():
                        island_min_z = min(island_min_z, float(p[isl, 2].min()))
                    # boundary crossings.
                    chg = np.nonzero(in_lane[1:] != in_lane[:-1])[0]
                    for i in chg:
                        cross_z_min = min(cross_z_min, float(min(p[i, 2], p[i + 1, 2])))
            if fam == "achieved":
                # REPLAY-NEUTRALITY (R-A/R-B): at every below-old frame, BOTH arms in-lane, NOT in island.
                bo = per_arm["L"][1] | per_arm["R"][1]
                both_lane = per_arm["L"][2] & per_arm["R"][2]
                any_island = per_arm["L"][3] | per_arm["R"][3]
                neutrality_violations += int((bo & ~(both_lane & ~any_island)).sum())
        res["columns"][fam] = {
            "arrays": [kl, kr],
            "label": (
                "recorded ACHIEVED path == env clamp input (fork-(iv) waypoints)"
                if fam == "achieved"
                else "recording RUNNER commanded targets (flag-OFF change extends into descend)"
            ),
            "sweeps": stats["sweeps"],
            "frame_counts": sorted(stats["frame_counts"]),
            "below_old_counts": sorted(stats["below_old_counts"]),
            "below_old_windows": sorted(stats["below_old_windows"]),
            "below_new_total": stats["below_new_total"],
            "min_margin_new_mm": round(stats["min_margin_new_mm"], 3),
            "park_z_range": [round(stats["park_z_min"], 5), round(stats["park_z_max"], 5)],
        }
    res["replay_neutrality"] = {
        "violations": neutrality_violations,
        "pass": neutrality_violations == 0,
        "meaning": "0 => every below-old-floor replay frame has BOTH arms in-lane and outside the C1 "
        "island -> mode-0 shared max floor == lane floor and the island carve-out never touches replay",
    }
    res["lane_edge_clearance_below_old_mm"] = {
        a: {k: round(v * 1e3, 1) for k, v in e.items()} for a, e in edge_env.items()
    }
    res["c1_island"] = {
        "min_recorded_z_in_footprint": round(island_min_z, 5),
        "island_floor": F_ISLAND,
        "gap_above_island_floor_mm": round((island_min_z - F_ISLAND) * 1e3, 1),
    }
    res["boundary_crossings"] = {
        "min_z_at_any_crossing": round(cross_z_min, 5),
        "above_old_floor_mm": round((cross_z_min - F_OLD) * 1e3, 1),
    }
    OUT_JSON.write_text(json.dumps(res, indent=1, default=list))

    print(json.dumps({k: v for k, v in res.items() if k != "columns"}, indent=1, default=list))
    for fam, st in res["columns"].items():
        print(f"[{fam}] {st['label']}")
        print(
            f"  sweeps={st['sweeps']} frames={st['frame_counts']} below_old={st['below_old_counts']}"
            f" windows={st['below_old_windows']}"
        )
        print(
            f"  below_NEW_total={st['below_new_total']} min_margin_new={st['min_margin_new_mm']}mm"
            f" park_z={st['park_z_range']}"
        )
    assert res["replay_neutrality"]["pass"], "REPLAY-NEUTRALITY VIOLATED"
    for fam in COLUMNS:
        assert res["columns"][fam]["below_new_total"] == 0, f"{fam}: frames below NEW floor"
    print(f"-> {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
