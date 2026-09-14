# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Compare socket envelopes with unchanged black-sleeve grasp surfaces [m]."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import probe_hand_tool_access_v01 as prior


def _segments(settings, socket):
    bottom = settings["comparison_tip_height_above_seat_m"]
    top = bottom + socket["length_m"]
    return {
        "socket": {"height_m": [bottom, top], "diameter_m": max(socket["d1_m"], socket["d2_m"])},
        "shaft": {
            "height_m": [top, settings["comparison_body_base_above_seat_m"]],
            "diameter_m": settings["comparison_shaft_diameter_m"],
        },
        "body": {
            "height_m": [settings["comparison_body_base_above_seat_m"], settings["comparison_body_top_above_seat_m"]],
            "diameter_m": None,
        },
    }


def _bands(triangles, names, segments, offsets, seat):
    positions = {str(offset): [offset, offset] for offset in offsets}
    positions["sweep"] = [min(offsets), max(offsets)]
    result = {}
    for position, (low_offset, high_offset) in positions.items():
        result[position] = {}
        for name, segment in segments.items():
            low, high = segment["height_m"]
            limits = [seat + low + low_offset, seat + high + high_offset]
            row = prior._slab_nearest(triangles, names, limits)
            row["z_above_seat_range_m"] = [limits[0] - seat, limits[1] - seat]
            diameter = segment["diameter_m"]
            radius = row["radius_to_surface_m"]
            row["comparison_diameter_m"] = diameter
            row["radial_difference_m"] = None if radius is None or diameter is None else radius - diameter / 2
            result[position][name] = row
    return result


def build(source: Path, config: Path, directory: Path) -> None:
    """Observe preserved source surfaces and write a separate comparison page.

    Args:
        source: Fixed sleeve-grasp mesh payload.
        config: Socket catalogue values and explicit comparison parameters.
        directory: New output folder; existing results are never overwritten.
    """
    settings = json.loads(config.read_text())
    assert prior._digest(source) == settings["source_sha256"], "Source mesh SHA mismatch"
    payload = json.loads(source.read_text())
    unchanged = json.dumps(payload, sort_keys=True)
    directory.mkdir(parents=True, exist_ok=False)
    observation = prior._observe(payload, settings)
    seat = payload["config"]["target"]["seat_z_m"]
    segments = {name: _segments(settings, socket) for name, socket in settings["socket_examples"].items()}
    assert all(s["shaft"]["height_m"][0] < s["shaft"]["height_m"][1] for s in segments.values())
    for name, candidate in payload["candidates"].items():
        for state in candidate["states"]:
            triangles, face_names, _ = prior._world_hand(candidate, state, settings["axis_xy_m"])
            observation["states"][name][state]["tools"] = {
                tool: _bands(triangles, face_names, bands, settings["comparison_vertical_offsets_m"], seat)
                for tool, bands in segments.items()
            }
    assert json.dumps(payload, sort_keys=True) == unchanged
    assert prior._digest(source) == settings["source_sha256"]
    report = {
        "recorded_at": datetime.now().astimezone().isoformat(),
        "source_sha256": prior._digest(source),
        "config_sha256": prior._digest(config),
        "settings": settings,
        "segments": segments,
        "analytic_checks": prior._analytic_checks(),
        "observation": observation,
        "geometry_and_all_saved_transforms_unchanged": True,
        "method": "Reused triangle Z-slab clipping and minimum XY surface radius in float64",
        "sweep_method": "Union of coaxial constant-radius cylinder translations: extend each Z band by offset range",
        "sweep_scope": (
            "Comparison envelopes only, with each saved hand pose fixed; no real motion or solid occupancy verdict"
        ),
        "catalogue_socket_examples_are_selected_equipment": False,
        "spindle_body_geometry_known": False,
        "workpiece_camera_arm_other_hand_and_station_excluded": True,
        "arm_motion_created": False,
        "video_created": False,
        "physical_acceptance_verdict": None,
    }
    (directory / "hand_sleeve_tool_access_v01.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    template = Path(__file__).with_name("hand_sleeve_tool_access_viewer_v01.html").read_text()
    page = template.replace("__MESH_PAYLOAD__", json.dumps(payload, separators=(",", ":")))
    page = page.replace("__OBSERVATION_PAYLOAD__", json.dumps(report, separators=(",", ":")))
    (directory / "黒被覆保持中の工具空間_v01.html").write_text(page)
    print(json.dumps({name: rows["near"]["tools"] for name, rows in observation["states"].items()}, indent=2))
    print("HAND_SLEEVE_TOOL_ACCESS_DONE", flush=True)


def main() -> None:
    """Read pinned inputs and create a fresh auxiliary review artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "config", "directory"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    build(args.source, args.config, args.directory)


if __name__ == "__main__":
    main()
