# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read logistics positions from the scale-free v05 schematic samples."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
BANK = WORK / "hvjb-line-video-v05-20260923/data/concept_display_v05_framed.npz"
BANK_SHA = "7702cadf9e412895a14c82d1a6b85a6aa659f2978c22e59ddf16e2714c793a60"
PLAN = WORK / "hvjb-line-video-v05-20260923/data/concept_v05.json"
SOURCE = WORK / "hvjb-line-video-v03-20260921/legacy_model.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scene_times(times, plan):
    path = WORK / "hvjb-display-continuity-v01-20260923/probe_saved.py"
    spec = importlib.util.spec_from_file_location("preserved_schematic_time_mapping", path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper.sample_scenes(times, plan)


def ranges(values):
    return {"minimum": values.min(axis=0).tolist(), "maximum": values.max(axis=0).tolist()}


def indices(names, name):
    return [index for index, value in enumerate(names) if value == name]


def one(names, name):
    found = indices(names, name)
    assert len(found) == 1, (name, found)
    return found[0]


def stock_record(names, poses, case_origin):
    slots = []
    for row in range(5):
        for column in range(4):
            label = f"stock_{row}_{column}"
            selected = indices(names, label)
            assert len(selected) == 8
            anchor = np.array([-4.7 - column * 0.90, -0.15 + row * 0.60, 0.855])
            origin = poses[:, selected[0], :3, 3] - [0, 0, 0.015]
            slots.append(
                {
                    "label": label,
                    "display_slot": f"{row * 4 + column + 1:02d}",
                    "columns": selected,
                    "source_slot_anchor_display_units": anchor.tolist(),
                    "stationary_saved_matrices": bool(np.all(poses[:, selected] == poses[0, selected])),
                    "saved_origin": origin[0].tolist(),
                    "source_hide_origin": bool(np.all(origin == [0, 0, -30])),
                }
            )
    assert len(slots) == 20
    first_anchor = np.array(slots[0]["source_slot_anchor_display_units"])
    return {
        "slots": slots,
        "active_case_starts_at_slot_01": bool(np.array_equal(case_origin[0], first_anchor)),
        "active_case_ends_at_slot_01": bool(np.array_equal(case_origin[-1], first_anchor)),
        "active_case_start_end_difference_display_units": (case_origin[-1] - case_origin[0]).tolist(),
        "inactive_stock_case_count": sum(not row["source_hide_origin"] for row in slots),
        "active_case_count": 1,
        "scope": "One demonstrated product cycle; other 19 case representations stay stationary.",
    }


def checkpoint_rows(times, source_times, scenes, case, pallet, hand, names, poses):
    rows = []
    events = (
        (0, "開始：区画01の筐体"),
        (3.6, "XYZの接近"),
        (4.8, "取出し上昇中"),
        (7.7, "パレットへ下降中"),
        (8.2, "受渡し後の手先開放中"),
        (10.0, "組立位置へ到着"),
        (94, "組立位置で待機"),
        (101, "後工程位置への移動中"),
        (104, "パレット復路"),
        (108.7, "同じXYZが取りに行く"),
        (110.7, "完成品の取出し中"),
        (112.5, "元の区画へ搬送中"),
        (113.5, "区画01へ下降後"),
        (115.8, "XYZの開放・上昇後"),
        (118, "終点：区画01に戻った状態"),
    )
    out_columns = [one(names, "outfeed_" + suffix) for suffix in ("palm", "left_finger", "right_finger", "carrier")]
    for wanted, label in events:
        index = int(np.argmin(np.abs(times - wanted)))
        rows.append(
            {
                "label_ja": label,
                "sample_index": index,
                "video_s": float(times[index]),
                "source_clock": float(source_times[index]),
                "scene": str(scenes[index]),
                "case_origin_display_units": case[index].tolist(),
                "pallet_center_display_units": pallet[index].tolist(),
                "xyz_hand_target_display_units": hand[index].tolist(),
                "old_outfeed_hand_hidden_signature": bool(np.all(poses[index, out_columns, :3, 3] == [0, 0, -30])),
            }
        )
    return rows


def main():
    target = ROOT / "audit/logistics_observations.json"
    assert not target.exists(), target
    assert sha(BANK) == BANK_SHA
    plan = json.loads(PLAN.read_text())
    assert plan["motion_sha256"] == BANK_SHA
    with np.load(BANK, allow_pickle=False) as saved:
        poses, times, names = [saved[key] for key in ("matrices", "time_s", "object_names")]
    assert poses.shape == (1785, 304, 4, 4)
    scenes, source_times = scene_times(times, plan)
    case_columns = indices(names, "case")
    assert len(case_columns) == 8
    case = poses[:, case_columns[0], :3, 3] - [0, 0, 0.015]
    pallet = poses[:, one(names, "pallet"), :3, 3]
    hand = poses[:, one(names, "infeed_palm"), :3, 3] - [0, 0, 0.18]
    on_pallet = (source_times >= 8.7) & (source_times <= 74.7)
    pickup = (source_times >= 4.6) & (source_times <= 8.7)
    return_carry = (source_times >= 74.7) & (source_times <= 79.4)
    out_columns = [index for index, name in enumerate(names) if name.startswith("outfeed_")]
    out_positions = poses[:, :, :3, 3][:, out_columns, :]
    assert out_positions.shape == (len(times), len(out_columns), 3)
    hides = np.all(out_positions == [0, 0, -30], axis=(1, 2))
    scene_summary = [
        {
            "scene": row["id"],
            "samples": int(np.count_nonzero(scenes == row["id"])),
            "outfeed_all_hidden_samples": int(np.count_nonzero((scenes == row["id"]) & hides)),
        }
        for row in plan["scenes"]
    ]
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "basis": "Saved schematic transforms plus the preserved display builder; not a physical simulation.",
        "source_identity": {str(path): sha(path) for path in (BANK, PLAN, SOURCE)},
        "sample_count": len(times),
        "time_units": "video seconds; source_clock is a schematic interpolation clock, not real takt",
        "position_units": "dimensionless display coordinates, not manufacturing meters",
        "stock": stock_record(names, poses, case),
        "pallet_center_range": ranges(pallet),
        "pallet_single_y": np.unique(pallet[:, 1]).tolist(),
        "pallet_single_z": np.unique(pallet[:, 2]).tolist(),
        "case_relative_to_pallet_during_transport": ranges(case[on_pallet] - pallet[on_pallet]),
        "xyz_relative_to_case_during_pickup": ranges(hand[pickup] - case[pickup]),
        "xyz_relative_to_case_during_return": ranges(hand[return_carry] - case[return_carry]),
        "checkpoints": checkpoint_rows(times, source_times, scenes, case, pallet, hand, names, poses),
        "legacy_outfeed_columns": [{"column": index, "name": str(names[index])} for index in out_columns],
        "legacy_outfeed_saved_visibility": scene_summary,
        "source_unchanged_after_read": sha(BANK) == BANK_SHA,
        "new_geometry_or_motion": False,
        "probe_correction": (
            "Initial read stopped before writing JSON because mixed NumPy indexing moved the selected-column axis. "
            "Positions are now sliced first, with the resulting shape checked explicitly. Source data is unchanged."
        ),
        "pallet_support_or_grasp_performance_verdict": None,
        "formal_physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    target.parent.mkdir(exist_ok=False)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("LOGISTICS_READBACK stock_slots=20 other_stationary_cases=19 active_case=1", flush=True)
    print("PALLET_DISPLAY_Z", result["pallet_single_z"], "Y", result["pallet_single_y"], flush=True)
    print(
        "CASE_SLOT_01", result["stock"]["active_case_starts_at_slot_01"], result["stock"]["active_case_ends_at_slot_01"]
    )
    print("OLD_OUTFEED", scene_summary, flush=True)


if __name__ == "__main__":
    main()
