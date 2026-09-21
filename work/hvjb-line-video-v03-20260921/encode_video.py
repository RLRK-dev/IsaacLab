# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Encode saved process PNGs using the existing provenance-checking encoder."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = Path("/home/rlrk/IsaacLab-op040/eval_runs/ur15_jb_harness_revision_20260907/scripts")
sys.path.insert(0, str(SCRIPTS))
import collect_saved_geometry_review  # noqa: E402
import encode_process_review_video  # noqa: E402

collect_saved_geometry_review.ROOT = ROOT
encode_process_review_video.ROOT = ROOT
encode_process_review_video.encode(
    ROOT / "data/concept_v03_final.json", ["concept_v03_final"], "HVJB_line_split_process_concept_v03_review"
)
