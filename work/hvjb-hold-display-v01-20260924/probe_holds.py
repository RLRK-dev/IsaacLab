# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Read relative hand/object displays over inherited schematic carry windows."""

import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
BANK = WORK / "hvjb-xyz-display-v01-20260924/data/concept_display_v05c.npz"
BANK_SHA = "21a64890540a06d94c06c6ee8e607f90dbe9c5b69ddf14fe944135614e28c409"
PLAN = WORK / "hvjb-line-video-v05b-20260923/data/concept_v05b.json"
HELPER = WORK / "hvjb-display-continuity-v01-20260923/probe_saved.py"
PAIRS = [
    ("XYZ_load", "infeed", "case", [0, 0, 0.015], 4.6, 8.7, "H06_CASE"),
    ("A_part", "A", "contactor", [0, 0, 0], 12.2, 19, "H01_BODY"),
    ("B_panel_stock", "B", "panel", [0, 0, 0.13], 12, 17, "H07_PANEL"),
    ("A_unit_to_C", "A", "base", [0, 0, 0.015], 22, 27, "H06_UNIT"),
    ("B_panel_to_C", "B", "panel", [0, 0, 0.13], 29, 34.5, "H07_PANEL"),
    ("C_unit_to_case", "C主", "base", [0, 0, 0.015], 40, 47, "H06_UNIT"),
    ("C_outer_header", "C主", "header_flange", [0, 0, 0], 50, 51.8, "H05_OUTER3"),
    ("C_busbar", "C主", "busbar", [0, 0, 0], 56.3, 58, "H03_BUS"),
    ("XYZ_return", "infeed", "case", [0, 0, 0.015], 74.7, 79.4, "H06_CASE"),
    ("A_next_unit", "A", "base_next", [0, 0, 0.015], 32, 37, "H06_UNIT"),
    ("B_next_panel", "B", "panel_next", [0, 0, 0.13], 38, 42, "H07_PANEL"),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = ROOT / "audit/relative_holds.json"
    assert not target.exists()
    assert sha(BANK) == BANK_SHA
    paths = [BANK, PLAN, HELPER, Path(__file__), WORK / "hvjb-line-video-v03-20260921/legacy_model.py"]
    pins = {str(path): sha(path) for path in paths}
    spec = importlib.util.spec_from_file_location("hold_clock_helper", HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    with np.load(BANK, allow_pickle=False) as saved:
        poses, names, times = [saved[key] for key in ("matrices", "object_names", "time_s")]
    names = names.tolist()
    scenes, clocks = helper.sample_scenes(times, json.loads(PLAN.read_text()))
    pairs = []
    for label, hand, product, offset, start, stop, application in PAIRS:
        chosen = (clocks >= start) & (clocks <= stop)
        indices = np.flatnonzero(chosen)
        palm = poses[chosen, names.index(hand + "_palm")]
        product_origin = poses[chosen, names.index(product), :3, 3] - offset
        hand_origin = palm[:, :3, 3] - np.einsum("tij,j->ti", palm[:, :3, :3], [0, 0, 0.18])
        relative = hand_origin - product_origin
        left, right = [poses[chosen, names.index(hand + suffix), :3, 3] for suffix in ("_left_finger", "_right_finger")]
        gap = np.linalg.norm(left - right, axis=1) - 0.032
        yaw = np.degrees(np.arctan2(palm[:, 1, 0], palm[:, 0, 0]))
        ends = [0, -1]
        record = {
            "id": label,
            "hand": hand,
            "product_node_first_occurrence": product,
            "application": application,
            "window_source_clock": [start, stop],
            "samples": len(indices),
            "scenes": sorted(set(scenes[chosen].tolist())),
            "first_last_sample_index": indices[ends].tolist(),
            "first_last_video_s": times[indices[ends]].tolist(),
            "relative_position_first_last": relative[ends].tolist(),
            "relative_position_range": np.ptp(relative, axis=0).tolist(),
            "opening_min_max": [float(gap.min()), float(gap.max())],
            "yaw_degrees_min_max": [float(yaw.min()), float(yaw.max())],
        }
        pairs.append(record)
        print(label, "range", record["relative_position_range"], "gap", record["opening_min_max"], flush=True)
    assert all(sha(Path(path)) == value for path, value in pins.items())
    target.parent.mkdir()
    target.write_text(
        json.dumps(
            {
                "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
                "input_sha256": pins,
                "pairs": pairs,
                "position_units": "Dimensionless explanatory coordinates; not manufacturing length units.",
                "window_basis": (
                    "Existing legacy carry key times; duplicate group names use their first object plus stored offset."
                ),
                "physical_acceptance_verdict": None,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print("HOLD_DISPLAY_PROBE_COMPLETE pairs=11 source_unchanged=True", flush=True)


if __name__ == "__main__":
    main()
