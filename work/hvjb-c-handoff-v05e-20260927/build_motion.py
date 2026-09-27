# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Separate opening, retreat, approach and closure in the existing schematic C regrip."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
SOURCE = WORK / "hvjb-display-bank-recovery-v01-20260927/recovered/panel_v05d.npz"
SOURCE_SHA = "0bb2f0e4e55e40def49cd2cfd7eecf99e0e7a4bdc9b7ea4097768f7c1cc00044"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open("x") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def hand_state(data: dict, index: int) -> tuple[np.ndarray, float, float]:
    names = data["object_names"].tolist()
    poses = data["matrices"][index]
    palm = poses[names.index("C主_palm")]
    left, right = (poses[names.index("C主_" + side + "_finger"), :3, 3] for side in ("left", "right"))
    return (
        palm[:3, 3] - palm[:3, :3] @ [0, 0, 0.18],
        float(np.linalg.norm(left - right) - 0.032),
        float(np.arctan2(palm[1, 0], palm[0, 0])),
    )


def keys_from_saved(data: dict) -> tuple[list, list, list]:
    first, last = 750, 825  # Existing S07 start/end; 50 and 55 illustration seconds.
    start, gap_start, yaw_start = hand_state(data, first)
    end, gap_end, yaw_end = hand_state(data, last)
    height = max(hand_state(data, index)[0][2] for index in range(first, last + 1))
    open_unit = max(hand_state(data, index)[1] for index in range(first, last + 1))
    # The existing B/C panel approach uses a 0.20 display opening; not a hardware stroke.
    open_panel = hand_state(data, 630)[1]  # Video 42 s / source 32.833... s, before closing.
    assert abs(open_panel - 0.20) < 1e-12
    high_start, high_end = start.copy(), end.copy()
    high_start[2] = high_end[2] = height
    points = [(50, start), (50.85, start), (51.9, high_start), (52.5, high_end), (53.9, end), (55, end)]
    gaps = [
        (50, gap_start),
        (50.35, gap_start),
        (50.85, open_panel),
        (51.9, open_panel),
        (52.5, open_unit),
        (53.9, open_unit),
        (54.55, gap_end),
        (55, gap_end),
    ]
    yaws = [(50, yaw_start), (51.9, yaw_start), (52.5, yaw_end), (55, yaw_end)]
    return points, gaps, yaws


def make_poses(data: dict, model, sample) -> tuple[np.ndarray, dict]:
    assert model.names == data["object_names"].tolist()
    poses = data["matrices"].copy()
    columns = [index for index, name in enumerate(model.names) if name.startswith("C主_")]
    points, gaps, yaws = keys_from_saved(data)
    indices = np.flatnonzero((data["time_s"] > 50) & (data["time_s"] < 55))
    for index in indices:
        for node, pose in zip(model.dynamic, data["matrices"][index], strict=True):
            model.scene.set_pose(node, pose)
        time = float(data["time_s"][index])
        model.oriented_hand("C主", sample(time, points), float(sample(time, gaps)), float(sample(time, yaws)))
        for column in columns:
            poses[index, column] = model.scene.get_pose(model.dynamic[column])
    diff = np.any(poses != data["matrices"], axis=(2, 3))
    outside = [index for index in range(len(model.names)) if index not in columns]
    assert np.array_equal(poses[:, outside], data["matrices"][:, outside])
    assert np.array_equal(poses[[750, 825]], data["matrices"][[750, 825]])
    assert np.isfinite(poses).all()
    return poses, {
        "changed_samples": int(diff.any(axis=1).sum()),
        "changed_columns": [model.names[index] for index in np.flatnonzero(diff.any(axis=0))],
        "position_keys": [[time, point.tolist()] for time, point in points],
        "gap_keys": gaps,
        "yaw_keys": yaws,
        "all_other_roles_objects_unchanged": True,
        "boundary_samples_unchanged": True,
    }


def main() -> None:
    target = ROOT / "data/concept_v05e.npz"
    assert not target.exists() and not (ROOT / "audit/motion_delta.json").exists()
    assert sha(SOURCE) == SOURCE_SHA
    recovery = json.loads((WORK / "hvjb-display-bank-recovery-v01-20260927/recovery.json").read_text())
    pins = dict(recovery["input_sha256"])
    pins.update({str(path): sha(path) for path in (SOURCE, Path(__file__), ROOT / "SCOPE.md")})
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    prior = load_module("c_handoff_prior", WORK / "hvjb-hold-display-v01-20260924/correct_holds.py")
    with np.load(SOURCE, allow_pickle=False) as saved:
        data = {key: saved[key] for key in saved.files}
    poses, observations = make_poses(data, prior.old.Model(), prior.sample)
    target.parent.mkdir(exist_ok=True)
    np.savez_compressed(target, **{**data, "matrices": poses})
    with np.load(target, allow_pickle=False) as restored:
        assert all(np.array_equal(restored[key], poses if key == "matrices" else data[key]) for key in data)
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    write(
        ROOT / "audit/motion_delta.json",
        {
            "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "input_sha256": pins,
            "output": str(target),
            "output_sha256": sha(target),
            **observations,
            "saved_readback_identical": True,
            "source_geometry_camera_time_and_product_unchanged": True,
            "coordinate_units": "dimensionless schematic display coordinates",
            "timing_basis": "illustration seconds; not real takt",
            "physical_acceptance_verdict": None,
        },
    )
    print(
        f"C_REGRIP_DISPLAY_COMPLETE changed_samples={observations['changed_samples']} sha256={sha(target)}", flush=True
    )


if __name__ == "__main__":
    main()
