# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Cross-reference published tool torque ranges [N·m] and saved header/CAD records without new poses."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = "data/hvjb_header_tool_configuration_v01.json"


def _read(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def _inputs(settings: dict) -> dict:
    previous = _read(settings["previous_readback"])
    expected = previous["input_sha256_current"].copy()
    for path, value in previous["artifacts_sha256"].items():
        assert path not in expected or expected[path] == value, path
        expected[path] = value
    for source in settings["sources"]:
        path, value = source["file"], source["sha256"]
        assert path not in expected or expected[path] == value, path
        expected[path] = value
    for key in (
        "previous_readback",
        "interface_record",
        "screw_options_record",
        "hand_observation",
        "datum_record",
        "mount_record",
    ):
        path = settings[key]
        expected.setdefault(path, _sha(path))
    expected[SETTINGS] = _sha(SETTINGS)
    actual = {path: _sha(path) for path in expected}
    assert actual == expected, [path for path in expected if actual[path] != expected[path]]
    return actual


def _glb_content(path: str) -> dict:
    raw = (ROOT / path).read_bytes()
    magic, version, total = struct.unpack_from("<III", raw)
    assert magic == 0x46546C67 and version == 2 and total == len(raw)
    length, kind = struct.unpack_from("<II", raw, 12)
    assert kind == 0x4E4F534A
    metadata = json.loads(raw[20 : 20 + length])
    return {
        "nodes": len(metadata.get("nodes", [])),
        "meshes": len(metadata.get("meshes", [])),
        "material_primitives": sum(len(mesh["primitives"]) for mesh in metadata.get("meshes", [])),
        "animations": len(metadata.get("animations", [])),
        "skins": len(metadata.get("skins", [])),
        "scope": "Stored GLB content counts only; absence of animation does not establish a mechanism state",
    }


def _cad_reference(key: str | None, datum: dict, mounting: dict) -> dict | None:
    if key is None:
        return None
    source, face = datum["models"][key], mounting["models"][key]
    observation = source["observation"]
    assert source["source_glb_sha256"] == face["source_glb_sha256"] == _sha(source["source_glb_file"])
    return {
        "file": source["source_glb_file"],
        "sha256": source["source_glb_sha256"],
        "glb_content": _glb_content(source["source_glb_file"]),
        "surface_nodes_in_prior_trimesh_read": source["surface_nodes"],
        "triangles": source["triangles"],
        "axis_point_m": observation["axis_point_m"],
        "axis_direction": observation["axis_direction"],
        "mount_plane_normal_index": observation["plane_normal_index"],
        "mount_plane_coordinate_m": observation["plane_coordinate_m"],
        "axis_to_mount_plane_distance_m": observation["axis_to_plane_distance_m"],
        "mount_face_bounds_m": face["bounds_m"],
        "mounting_bolt_pattern": face["mounting_bolt_pattern"],
        "engagement_tcp": None,
        "configuration_adopted": False,
    }


def _ranges(rows: list[dict], requirement: list[float], datum: dict, mount: dict) -> list[dict]:
    results = []
    for row in rows:
        lower, upper = row["torque_range_n_m"]
        common = [max(lower, requirement[0]), min(upper, requirement[1])]
        results.append(
            {
                "model": row["model"],
                "published_torque_range_n_m": [lower, upper],
                "required_torque_range_n_m": requirement,
                "common_range_n_m": common if common[0] <= common[1] else None,
                "contains_required_range": lower <= requirement[0] and upper >= requirement[1],
                "maximum_head_diameter_m": row["maximum_screw_head_diameter_m"],
                "washer_or_collar_feed_compatibility": None,
                "saved_example_cad": _cad_reference(row["saved_example_model_key"], datum, mount),
                "physical_acceptance_verdict": None,
            }
        )
    return results


def _axis_links(hand: dict, targets: list[dict]) -> list[dict]:
    models = {model["feature_id"]: model for model in hand["models"]}
    assert len(models) == len(hand["models"]) == len(targets)
    results = []
    for target in targets:
        model = models[target["part_id"]]
        assert model["part_number"] == target["header_part_number"]
        assert len(model["axes"]) == target["documented_mounting_fastener_count"]
        for axis in model["axes"]:
            results.append(
                {
                    "part_id": target["part_id"],
                    "part_number": model["part_number"],
                    "nominal_index_zero_based": axis["nominal_index"],
                    "screw_name": axis["screw_name"],
                    "nominal_local_xz_m": axis["nominal_local_xz_m"],
                    "saved_hand_frame": axis["pose"]["frame"],
                    "interface": "HEADER_TO_ENCLOSURE",
                    "tool_to_header_transform": None,
                }
            )
    assert len({row["screw_name"] for row in results}) == len(results) == 14
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_json", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output_json.exists(), args.output_json
    settings = _read(SETTINGS)
    before = _inputs(settings)
    interfaces = _read(settings["interface_record"])
    matches = [item for item in interfaces["interfaces"] if item["id"] == "HEADER_TO_ENCLOSURE"]
    assert len(matches) == 1
    interface = matches[0]
    requirement = interface["published_conditions"]["torque_range_n_m"]
    screws = _read(settings["screw_options_record"])
    assert requirement == screws["te_conditions"]["torque_range_nm"] == [2.0, 2.5]
    assert interface["published_conditions"]["thread_designation"] == screws["te_conditions"]["thread"] == "M4"
    hand = _read(settings["hand_observation"])
    links = _axis_links(hand, interface["model_targets"])
    ranges = _ranges(
        settings["published_standard_rows"],
        requirement,
        _read(settings["datum_record"]),
        _read(settings["mount_record"]),
    )
    after = {path: _sha(path) for path in before}
    assert before == after
    result = {
        "observed_at": datetime.now(UTC).isoformat(),
        "scope": "Published interval correspondence and saved-coordinate inputs, not tool adoption or clearance",
        "settings": SETTINGS,
        "script_sha256": _sha(str(Path(__file__).relative_to(ROOT))),
        "requirement": interface["published_conditions"],
        "source_revision": "STOEGER Status 10/2017; TE 408-32095 Rev B",
        "tool_range_comparisons": ranges,
        "header_axis_links": links,
        "prior_source_feature_count": hand["source_feature_count"],
        "source_input_sha256_before": before,
        "source_input_sha256_after": after,
        "geometry_modified": False,
        "new_cad_conversion": False,
        "native_opened": False,
        "native_saved": False,
        "motion_recomputed": False,
        "tool_placement_or_clearance_measured": False,
        "selected_tool_configuration": None,
        "physical_acceptance_verdict": None,
    }
    with args.output_json.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    assert json.loads(args.output_json.read_text()) == result
    for row in ranges:
        print(
            row["model"],
            "published torque range",
            row["published_torque_range_n_m"],
            "contains TE range",
            row["contains_required_range"],
        )
    print(f"COMPLETE: {len(links)} saved header axes linked; {len(before)} protected files unchanged")
    print(args.output_json)


if __name__ == "__main__":
    main()
