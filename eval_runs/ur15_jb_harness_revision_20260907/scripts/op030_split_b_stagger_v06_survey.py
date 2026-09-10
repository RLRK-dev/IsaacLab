# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Record the finite reused-solver B opposite-side held survey [m, rad, s]."""

import argparse
import json

import numpy as np
from op030_definition import ROOT
from op030_split_b_plan import digest
from op030_split_b_stagger_v06 import build_sequence
from op030_split_wire_motion import survey_branches


def main() -> None:
    """Save candidate-only joint branches without a mesh-validity claim [rad]."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--work_yaw_degrees", type=float, default=270.0)
    parser.add_argument("--grasp_side_flip", action="store_true")
    parser.add_argument("--orbit_y_m", type=float)
    parser.add_argument("--output", default="op030_split_b_stagger_v06_survey_01")
    args = parser.parse_args()
    name = args.output
    path = ROOT / "analysis" / (name + ".npz")
    audit = ROOT / "audit" / (name + ".json")
    if path.exists() or audit.exists():
        raise FileExistsError(path)
    report, arrays = survey_branches(
        build_sequence(
            work_yaw_degrees=args.work_yaw_degrees, grasp_side_flip=args.grasp_side_flip, orbit_y_m=args.orbit_y_m
        ),
        step=0.20,
        branch_seeds=4,
    )
    np.savez_compressed(path, **arrays)
    report.update(
        factory="op030_split_b_stagger_v06:build_sequence",
        work_yaw_degrees=args.work_yaw_degrees,
        grasp_side_flip=args.grasp_side_flip,
        orbit_y_m=args.orbit_y_m,
        output_sha256=digest(path),
    )
    audit.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("STAGGER_SURVEY_COMPLETE", report["all_held_sections_have_a_continuous_branch"], flush=True)


if __name__ == "__main__":
    main()
