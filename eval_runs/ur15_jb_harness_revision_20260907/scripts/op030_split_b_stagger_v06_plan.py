# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Screen finite opposite-side B joint branches against the actual moved native [m, rad]."""

import argparse
import itertools
import json
from datetime import datetime

import numpy as np
from op030_definition import ROOT
from op030_split_b_check import SplitBMeshes, unique_branches
from op030_split_b_plan import digest
from op030_split_b_stagger_v06 import SOURCE_BANK, build_sequence
from op030_split_b_v04 import load
from op030_split_b_v05 import Candidate as LegacyCandidate
from op030_split_wire_motion import WirePlacementConfig
from solve_op030_motion import capture_robots

DEFAULT_MESH = ROOT / "data/op030_split_b_stagger_v06_meshes.npz"
SURVEY = "op030_split_b_stagger_v06_survey_01"


class Candidate(LegacyCandidate):
    """Retain the original FK and named-contact mesh checker [m, rad, s]."""

    def __init__(
        self,
        mesh=DEFAULT_MESH,
        *,
        work_yaw_degrees=270.0,
        survey=SURVEY,
        grasp_side_flip=False,
        orbit_y_m=None,
        config=None,
        overbody=False,
        swap_roles=False,
        bend_during_turn=False,
        h1_yaw_bias_degrees=0.0,
    ):
        self.mesh = mesh.resolve()
        self.sequence = build_sequence(
            config,
            work_yaw_degrees=work_yaw_degrees,
            grasp_side_flip=grasp_side_flip,
            orbit_y_m=orbit_y_m,
            overbody=overbody,
            swap_roles=swap_roles,
            bend_during_turn=bend_during_turn,
            h1_yaw_bias_degrees=h1_yaw_bias_degrees,
        )
        self.survey = survey
        self.screen = SplitBMeshes(self.sequence, self.mesh)
        self.robots = capture_robots()
        self.start_state = self.sequence.evaluate(0.0)
        self.support_contacts, self.failures, self.records = [], [], []
        self.blocks = {}
        self.extra = tuple(
            uid + suffix for uid in self.sequence.active_uids.values() for suffix in ("_J1", "_T", "_insulation")
        )
        self.old = load(SOURCE_BANK)

    def held_screen(self) -> dict:
        """Check all distinct saved branch combinations in the same world clock [s]."""
        branches = load(ROOT / "analysis" / (self.survey + ".npz"))
        source = json.loads((ROOT / "audit" / (self.survey + ".json")).read_text())
        records = []
        for number, left, right in ((2, 0, 2), (1, 1, 3)):
            choices = [unique_branches(source["sections"][i], branches) for i in (left, right)]
            times = branches[f"section_{left}_times"]
            targets = [self.sequence.evaluate(float(t)) for t in times]
            combinations = []
            for a, b in itertools.product(*choices):
                hits = []
                for index, (time, target) in enumerate(zip(times, targets, strict=True)):
                    q = np.array([a["joints"][index], b["joints"][index]])
                    pairs = self.score_all(target, q)
                    if pairs:
                        hits.append(dict(time_s=float(time), phase=target["phase_index"], pairs=pairs))
                combinations.append(
                    dict(left=a["array_key"], right=b["array_key"], hits=hits, hit_frames=len(hits), passed=not hits)
                )
                print("STAGGER_HELD_MESH", number, a["array_key"], b["array_key"], len(hits), flush=True)
            records.append(
                dict(number=number, combinations=combinations, passed=any(row["passed"] for row in combinations))
            )
        return dict(
            observed_at=datetime.now().astimezone().isoformat(),
            wires=records,
            passed=all(row["passed"] for row in records),
            mesh_sha256=digest(self.mesh),
            survey_sha256=digest(ROOT / "analysis" / (self.survey + ".npz")),
            formal_physical_verdict=None,
        )


def main() -> None:
    """Save bounded branch triangle observations without promoting failed candidates."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="op030_split_b_stagger_v06_held_01")
    parser.add_argument("--survey", default=SURVEY)
    parser.add_argument("--work_yaw_degrees", type=float, default=270.0)
    parser.add_argument("--grasp_side_flip", action="store_true")
    parser.add_argument("--orbit_y_m", type=float)
    parser.add_argument("--from_survey", action="store_true")
    args = parser.parse_args()
    output = ROOT / "audit" / (args.output + ".json")
    if output.exists():
        raise FileExistsError(output)
    if args.from_survey:
        source = json.loads((ROOT / "audit" / (args.survey + ".json")).read_text())
        candidate = Candidate(
            config=WirePlacementConfig(**source["config"]),
            survey=args.survey,
            **{
                key: source[key]
                for key in (
                    "work_yaw_degrees",
                    "grasp_side_flip",
                    "orbit_y_m",
                    "overbody",
                    "swap_roles",
                    "bend_during_turn",
                )
                if key in source
            },
        )
    else:
        candidate = Candidate(
            work_yaw_degrees=args.work_yaw_degrees,
            survey=args.survey,
            grasp_side_flip=args.grasp_side_flip,
            orbit_y_m=args.orbit_y_m,
        )
    result = candidate.held_screen()
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("STAGGER_HELD_COMPLETE", result["passed"], flush=True)


if __name__ == "__main__":
    main()
