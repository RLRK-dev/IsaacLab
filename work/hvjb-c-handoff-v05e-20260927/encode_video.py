# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Encode the checked process PNGs into the single authorized review MP4 type."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from build_motion import ROOT, WORK, sha, write

SCRIPTS = Path("/home/rlrk/IsaacLab-op040/eval_runs/ur15_jb_harness_revision_20260907/scripts")
sys.path.insert(0, str(SCRIPTS))
import collect_saved_geometry_review  # noqa: E402
import encode_process_review_video  # noqa: E402


def main() -> None:
    plan_path = ROOT / "data/concept_v05e.json"
    plan = json.loads(plan_path.read_text())
    assert not plan["preview_only"] and plan["repeat_each_source_sample"] == 1
    assert len(plan["expected_source_samples"]) == 3138 and len(plan["chapters"]) == 6
    assert plan["captions_baked_in_process_pngs"] and not plan["phases"] and not plan["scope_caption"]
    historical = json.loads((WORK / "hvjb-line-video-v03-20260921/inputs/original_sources.json").read_text())
    pins = {
        row["path"]: row["sha256"]
        for row in historical
        if Path(row["path"]).parent == SCRIPTS or Path(row["path"]).name == "video_delivery_policy.json"
    }
    assert len(pins) == 5
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    collect_saved_geometry_review.ROOT = ROOT
    encode_process_review_video.ROOT = ROOT
    encode_process_review_video.encode(plan_path, ["concept_v05e"], "HVJB_line_split_process_concept_v05e_review")
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    write(ROOT / "audit/encoder_dependency_receipt.json", {"dependencies_unchanged_before_and_after": pins})
    print("C_SINGLE_REVIEW_VIDEO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
