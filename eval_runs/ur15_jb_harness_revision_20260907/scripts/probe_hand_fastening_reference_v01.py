# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Compare published component dimensions against fixed sleeve-grasp surfaces."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import probe_hand_tool_access_v01 as prior


def _placements(triangles, names, reference, heights, seat):
    result = {}
    for height in heights:
        limits = [seat + height, seat + height + reference["length_m"]]
        row = prior._slab_nearest(triangles, names, limits)
        row["z_above_seat_range_m"] = [height, height + reference["length_m"]]
        row["comparison_diameter_m"] = reference["diameter_m"]
        radius = row["radius_to_surface_m"]
        row["radial_difference_m"] = None if radius is None else radius - reference["diameter_m"] / 2
        result[str(height)] = row
    return result


def build(source: Path, config: Path, directory: Path) -> None:
    """Write individual component comparisons using published SI dimensions [m].

    Args:
        source: Immutable hand mesh payload and saved transforms.
        config: Public dimensions and separate static placement heights [m].
        directory: New output directory; existing results are not overwritten.
    """
    settings = json.loads(config.read_text())
    assert prior._digest(source) == settings["source_sha256"], "Source SHA mismatch"
    payload = json.loads(source.read_text())
    original = json.dumps(payload, sort_keys=True)
    for reference in settings["references"].values():
        assert reference["diameter_m"] > 0 and reference["length_m"] > 0
    directory.mkdir(parents=True, exist_ok=False)
    observation = prior._observe(payload, settings)
    seat = payload["config"]["target"]["seat_z_m"]
    for name, candidate in payload["candidates"].items():
        for state in candidate["states"]:
            triangles, names, _ = prior._world_hand(candidate, state, settings["axis_xy_m"])
            observation["states"][name][state]["references"] = {
                key: _placements(
                    triangles, names, reference, settings["comparison_part_lower_heights_above_seat_m"], seat
                )
                for key, reference in settings["references"].items()
            }
    assert json.dumps(payload, sort_keys=True) == original
    assert prior._digest(source) == settings["source_sha256"]
    report = {
        "recorded_at": datetime.now().astimezone().isoformat(),
        "source_sha256": prior._digest(source),
        "config_sha256": prior._digest(config),
        "settings": settings,
        "analytic_checks": prior._analytic_checks(),
        "observation": observation,
        "source_geometry_and_all_transforms_unchanged": True,
        "method": "Reused float64 triangle Z-slab clipping and minimum XY projected surface radius",
        "reference_components_displayed_individually": True,
        "assembled_tool_stack_verified": False,
        "feed_nose_geometry_known": False,
        "selection_or_motion_generated": False,
        "excluded": ["workpiece", "camera", "arms", "other hand/tool", "feed nose", "mounting", "cables/hoses"],
        "physical_acceptance_verdict": None,
    }
    (directory / "hand_fastening_reference_v01.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    template = Path(__file__).with_name("hand_fastening_reference_viewer_v01.html").read_text()
    page = template.replace("__MESH_PAYLOAD__", json.dumps(payload, separators=(",", ":")))
    page = page.replace("__OBSERVATION_PAYLOAD__", json.dumps(report, separators=(",", ":")))
    (directory / "締付部材の公開寸法比較_v01.html").write_text(page)
    for key, rows in observation["states"]["H050"]["near"]["references"].items():
        print(key, json.dumps(rows, ensure_ascii=False), flush=True)
    print("HAND_FASTENING_REFERENCE_DONE", flush=True)


def main() -> None:
    """Read pinned source and public dimension records; write a fresh comparison."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "config", "directory"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    build(args.source, args.config, args.directory)


if __name__ == "__main__":
    main()
