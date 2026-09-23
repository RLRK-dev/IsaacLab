# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Encode the identified PNG composition with the existing one-video delivery implementation."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = Path("/home/rlrk/IsaacLab-op040/eval_runs/ur15_jb_harness_revision_20260907/scripts")
sys.path.insert(0, str(SCRIPTS))
import collect_saved_geometry_review  # noqa: E402
import encode_process_review_video  # noqa: E402


def main() -> None:
    plan_path = ROOT / "data/concept_v05c.json"
    plan = json.loads(plan_path.read_text())
    assert not plan["preview_only"] and plan["repeat_each_source_sample"] == 1
    assert len(plan["expected_source_samples"]) == 2328 and len(plan["chapters"]) == 5
    assert plan["captions_baked_in_process_pngs"] and not plan["phases"] and not plan["scope_caption"]
    historical = json.loads((ROOT.parent / "hvjb-line-video-v03-20260921/inputs/original_sources.json").read_text())
    pins = {
        row["path"]: row["sha256"]
        for row in historical
        if Path(row["path"]).parent == SCRIPTS or Path(row["path"]).name == "video_delivery_policy.json"
    }
    assert len(pins) == 5
    for path, expected in pins.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
    collect_saved_geometry_review.ROOT = ROOT
    encode_process_review_video.ROOT = ROOT
    encode_process_review_video.encode(plan_path, ["concept_v05c"], "HVJB_line_split_process_concept_v05c_review")
    for path, expected in pins.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
    receipt = ROOT / "audit/encoder_dependency_receipt.json"
    with receipt.open("x") as stream:
        stream.write(json.dumps({"dependencies_unchanged_before_and_after": pins}, indent=2) + "\n")


if __name__ == "__main__":
    main()
