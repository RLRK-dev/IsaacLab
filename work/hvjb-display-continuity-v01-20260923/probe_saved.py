# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Rank adjacent-frame changes in the saved, scale-free explanatory animation."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent
VIDEO = ROOT.parent / "hvjb-line-video-v04-20260923"
BANK = VIDEO / "data/concept_v03_reused.npz"
BANK_SHA = "52eede374a2d782aabf1cc2604801cc64e6f884b39060728c437631a8dca36dc"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def sample_scenes(times, plan):
    ids, source_times = [], []
    for time in times:
        row = next(row for row in plan["scenes"] if row["start_s"] <= time < row["stop_s"])
        proportion = (time - row["start_s"]) / (row["stop_s"] - row["start_s"])
        begin, end = row["source_clock"]
        ids.append(row["id"])
        source_times.append(begin + proportion * (end - begin))
    return np.asarray(ids), np.asarray(source_times)


def top_steps(values, mask, times, source_times, ids, positions, names, limit=40):
    selected = np.where(mask, values, -1)
    flat_indices = np.argsort(selected.ravel())[::-1][:limit]
    records = []
    for flat in flat_indices:
        frame, column = np.unravel_index(flat, values.shape)
        if selected[frame, column] < 0:
            continue
        records.append(
            {
                "from_sample_index": int(frame),
                "to_sample_index": int(frame + 1),
                "from_video_s": float(times[frame]),
                "to_video_s": float(times[frame + 1]),
                "source_clock_before_after": [float(source_times[frame]), float(source_times[frame + 1])],
                "scene_before_after": [str(ids[frame]), str(ids[frame + 1])],
                "object_column": int(column),
                "object_name": str(names[column]),
                "value": float(values[frame, column]),
                "position_before": positions[frame, column].tolist(),
                "position_after": positions[frame + 1, column].tolist(),
            }
        )
    return records


def category(name):
    if any(word in name for word in ("palm", "finger", "carrier", "joint", "link")):
        return "arm_and_hand_display"
    if name.startswith(("wire_", "sleeve_", "inner_housing_")):
        return "wire_group_symbol"
    if name.startswith(("tool_", "bit_", "infeed_", "outfeed_")) or name == "test_probe":
        return "tool_and_axis_display"
    return "product_and_pallet_display"


def main():
    out = ROOT / "audit"
    out.mkdir(exist_ok=False)
    assert sha(BANK) == BANK_SHA
    plan_path = VIDEO / "data/concept_v04.json"
    plan = json.loads(plan_path.read_text())
    with np.load(BANK, allow_pickle=False) as saved:
        matrices, times, camera, names = [saved[key] for key in ("matrices", "time_s", "camera", "object_names")]
    assert matrices.shape == (1785, 304, 4, 4)
    assert np.isfinite(matrices).all() and np.isfinite(camera).all()
    ids, source_times = sample_scenes(times, plan)
    positions = matrices[:, :, :3, 3]
    translation = np.linalg.norm(np.diff(positions, axis=0), axis=-1)
    scales = np.linalg.norm(matrices[:, :, :3, :3], axis=-2)
    assert np.all(scales > 0)
    rotations = matrices[:, :, :3, :3] / scales[:, :, None, :]
    relative_trace = np.einsum("tnij,tnij->tn", rotations[1:], rotations[:-1])
    angle = np.degrees(np.arccos(np.clip((relative_trace - 1) / 2, -1, 1)))
    known_hide = np.all(positions == [0, 0, -30.0], axis=-1)
    same_scene = ids[:-1] == ids[1:]
    mask = same_scene[:, None] & ~(known_hide[:-1] | known_hide[1:])
    camera_step = np.any(np.diff(camera, axis=0) != 0, axis=(1, 2))
    same_scene_records = {}
    for key in sorted({category(name) for name in names}):
        columns = np.array([category(name) == key for name in names])
        same_scene_records[key] = {
            "translation_display_units": top_steps(
                translation, mask & columns[None, :], times, source_times, ids, positions, names
            ),
            "normalized_rotation_degrees": top_steps(
                angle, mask & columns[None, :], times, source_times, ids, positions, names
            ),
        }
    maximums = []
    for column, name in enumerate(names):
        values = np.where(mask[:, column], translation[:, column], -1)
        index = int(np.argmax(values))
        maximums.append(
            {
                "object_column": column,
                "object_name": str(name),
                "maximum_same_scene_step_display_units": float(values[index]),
                "video_s": float(times[index + 1]),
                "scene": str(ids[index + 1]),
            }
        )
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "source": {"path": str(BANK), "sha256": BANK_SHA, "plan_sha256": sha(plan_path)},
        "sample_count": len(times),
        "object_columns": len(names),
        "unique_name_count": len(set(names)),
        "duplicate_names": {str(name): count for name, count in Counter(names).items() if count > 1},
        "identity_key": "object_column plus object_name; names alone are not unique",
        "position_units": "scale-free explanatory display units; not manufacturing meters",
        "rotation_note": "Column norms removed before angular comparison; display cylinders/carriers use scale.",
        "hide_note": "Only exact translation [0,0,-30] is tagged as the source hide signature.",
        "camera_change_indices": (np.flatnonzero(camera_step) + 1).tolist(),
        "scene_change_indices": (np.flatnonzero(~same_scene) + 1).tolist(),
        "ranked_same_scene_steps": same_scene_records,
        "all_steps_including_scene_and_hide_changes": top_steps(
            translation, np.ones_like(translation, dtype=bool), times, source_times, ids, positions, names, limit=30
        ),
        "per_object_maximum_same_scene_steps": maximums,
        "input_unchanged_after_read": sha(BANK) == BANK_SHA,
        "acceptance_threshold": None,
        "physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    write(out / "saved_display_steps.json", record)
    print("DISPLAY_STEPS_RECORDED samples=1785 columns=304 input_unchanged=true")
    for key, rows in same_scene_records.items():
        print(key)
        for row in rows["translation_display_units"][:4]:
            print(row["object_column"], row["object_name"], row["to_video_s"], row["value"])


if __name__ == "__main__":
    main()
