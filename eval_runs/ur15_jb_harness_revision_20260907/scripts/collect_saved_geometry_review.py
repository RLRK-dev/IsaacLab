# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Verify source-sample-to-PNG mappings for a process review without claiming a new animated native."""

import json
from pathlib import Path

from encode_review_video import digest

ROOT = Path(__file__).resolve().parents[1]


def collect_saved_geometry_frames(folders: list[str], plan_path: Path) -> tuple[dict, dict, list[dict], dict]:
    """Verify source hashes, complete stored-sample coverage and output PNG identities."""
    plan = json.loads(plan_path.read_text())
    assert plan["source_kind"] == "saved_geometry_samples"
    assert plan["native"] is None and plan["native_sha256"] is None
    assert plan["motion_sha256"] == digest(ROOT / "data" / plan["motion"])
    assert all(digest(ROOT / name) == sha for name, sha in plan["input_sha256"].items())
    records, manifests, settings = {}, [], None
    for name in folders:
        if Path(name).name != name:
            raise ValueError("Each render folder must be one relative directory name")
        folder = ROOT / "previews" / name
        path = folder / "manifest.json"
        manifest = json.loads(path.read_text())
        assert manifest["complete"] and manifest["source_kind"] == plan["source_kind"]
        assert manifest["shot_plan_sha256"] == digest(plan_path)
        assert manifest["renderer_sha256"] == digest(ROOT / plan["renderer"])
        assert manifest["input_sha256_current"] == plan["input_sha256"]
        assert manifest["output_fps"] == 15
        settings = manifest["settings"] if settings is None else settings
        assert settings == manifest["settings"]
        manifests.append({"path": str(path.relative_to(ROOT)), "sha256": digest(path)})
        for row in manifest["images"]:
            assert row["view"] == "process" and row["frame"] not in records
            png = (folder / row["file"]).resolve()
            assert png.is_relative_to(folder.resolve()) and digest(png) == row["sha256"]
            assert row["camera"] == plan["camera"]
            records[row["frame"]] = dict(row, png=png)
    assert sorted(records) == list(range(1, plan["frame_end"] + 1, 2))
    ordered = [row for _, row in sorted(records.items())]

    def identity(row: dict) -> tuple:
        return row["feature_id"], row["saved_frame"], row["saved_bank_index"], row["saved_time_s"]

    expected = [identity(row) for row in plan["expected_source_samples"]]
    moving = [identity(row) for row in ordered if row["display_segment"] == "saved_sample"]
    repeat = plan["repeat_each_source_sample"]
    assert moving == [value for value in expected for _ in range(repeat)]
    assert set(identity(row) for row in ordered) == set(expected)
    assert all(row["display_segment"] in ("pause_before", "saved_sample", "pause_after") for row in ordered)
    return plan, records, manifests, settings
