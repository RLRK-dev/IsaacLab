# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Observe saved H05 and workpiece triangle-surface pairs [m] without changing source scenes."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_hvjb_header_tool_configuration_v01 import ROOT, _read, _sha
from check_hvjb_header_tool_tip_sources_v01 import _protected
from probe_hvjb_entry_display_v03 import tree

SETTINGS = "data/hvjb_header_workpiece_v01.json"


def _geometry(path: str) -> dict:
    return json.loads(gzip.decompress((ROOT / path).read_bytes()))


def _bounds(meshes: list[dict]) -> np.ndarray:
    points = np.concatenate([np.asarray(row["vertices"]) for row in meshes])
    return np.array([points.min(axis=0), points.max(axis=0)])


def _target(key: str, feature: str, meshes: list[dict], kind: str) -> dict:
    offsets, start = [], 0
    for index, mesh in enumerate(meshes):
        count = len(mesh["faces"])
        offsets.append({"mesh_index": index, "name": mesh["name"], "face_start": start, "face_count": count})
        start += count
    return {
        "key": key,
        "feature_id": feature,
        "kind": kind,
        "bounds": _bounds(meshes),
        "mesh_face_ranges": offsets,
        "triangles": start,
        "tree": tree({"meshes": meshes}),
    }


def _targets(product: dict) -> list[dict]:
    targets = [_target("P01_case", "P01", product["P01"]["meshes"], "saved_case")]
    for feature in ("P16", "P17"):
        meshes = product[feature]["meshes"]
        official = [row for row in meshes if "official_CAD" in row["name"]]
        screws = [row for row in meshes if "_mount_M4_" in row["name"]]
        assert len(official) + len(screws) == len(meshes), "Unclassified header geometry"
        targets.append(_target(feature + "_official", feature, official, "official_header_mesh"))
        targets.append(_target(feature + "_saved_screws", feature, screws, "unselected_display_fasteners"))
    return targets


def _mapping(spec: dict, source: dict, product: dict, tolerance: float) -> dict:
    """Check the saved header translation [m] against every material partition and source triangle."""
    meshes = [row for row in product[spec["feature_id"]]["meshes"] if "official_CAD" in row["name"]]
    expected = np.asarray(source["vertices"]) + spec["model_translation_m"]
    errors = [float(np.max(abs(np.asarray(row["vertices"]) - expected))) for row in meshes]
    original = Counter(tuple(face) for face in source["faces"])
    assembled = Counter(tuple(face) for row in meshes for face in row["faces"])
    assert original == assembled, "Source-CAD face correspondence changed"
    assert max(errors) < tolerance, (spec["feature_id"], errors)
    return {
        "feature_id": spec["feature_id"],
        "translation_m": spec["model_translation_m"],
        "material_partitions": len(meshes),
        "source_face_multiset_equal": True,
        "max_coordinate_residual_by_partition_m": errors,
        "numeric_tolerance_m": tolerance,
        "scope": "Saved display placement and serialization check, not an Ampere manufacturing datum",
    }


def _analytic_checks() -> dict:
    base = {"vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]], "faces": [[0, 1, 2]]}
    crossing = {"vertices": [[0.25, 0.25, -1], [0.25, 0.25, 1], [0.5, 0.5, 1]], "faces": [[0, 1, 2]]}
    separate = {"vertices": [[0, 0, 3], [1, 0, 3], [0, 1, 3]], "faces": [[0, 1, 2]]}
    first = tree({"meshes": [base]})
    crossed = first.overlap(tree({"meshes": [crossing]}))
    separated = first.overlap(tree({"meshes": [separate]}))
    assert crossed == [(0, 0)] and separated == []
    return {"crossing_triangle_pairs": [list(pair) for pair in crossed], "separated_triangle_pairs": separated}


def _hand_mesh(name: str, source: dict, pose: dict, bank, spec: dict, tolerance: float) -> dict:
    """Translate an unchanged stored hand surface into the saved product frame [m]."""
    index = pose["bank_index"]
    matrix = np.asarray(pose["hand_object_world_matrices"][name])
    assert np.array_equal(matrix, bank["OP020_hand_" + name][index])
    points = np.asarray(source["vertices"]) @ matrix[:3, :3].T + matrix[:3, 3]
    local = points - pose["header_world_position_m"]
    recorded = next(row for row in pose["objects"] if row["name"] == name)
    observed_bounds = np.array([local.min(axis=0), local.max(axis=0)])
    assert np.max(abs(observed_bounds - recorded["bounds_header_m"])) < tolerance
    return {
        "name": name,
        "category": source["category"],
        "vertices": (local + spec["model_translation_m"]).tolist(),
        "faces": source["faces"],
    }


def _pairs(hand: dict, targets: list[dict]) -> list[dict]:
    bounds, hand_tree = _bounds([hand]), tree({"meshes": [hand]})
    pairs = []
    for target in targets:
        disjoint = bool(np.any(bounds[1] < target["bounds"][0]) or np.any(target["bounds"][1] < bounds[0]))
        overlaps = [] if disjoint else sorted(hand_tree.overlap(target["tree"]))
        pairs.append(
            {
                "hand_object": hand["name"],
                "hand_category": hand["category"],
                "target_key": target["key"],
                "aabb_disjoint": disjoint,
                "overlapping_triangle_pair_count": len(overlaps),
                "triangle_pairs_hand_target": [list(pair) for pair in overlaps],
            }
        )
    return pairs


def _pose(axis: dict, hand: dict, bank, spec: dict, targets: list[dict], tolerance: float) -> dict:
    pose = axis["pose"]
    index, feature = pose["bank_index"], spec["feature_id"]
    header_index = 0 if feature == "P16" else 1
    assert int(bank["frames"][index]) == pose["frame"]
    assert np.array_equal(bank[f"header_{header_index}_position"][index], pose["header_world_position_m"])
    assert np.array_equal(pose["header_world_rotation"], np.eye(3))
    assert float(bank["gripper_q"][index]) == hand["q_closed"][header_index]
    inputs = pose | {"objects": axis["objects"]}
    meshes = [_hand_mesh(name, row, inputs, bank, spec, tolerance) for name, row in hand["objects"].items()]
    assert len(meshes) == 14 and sum(len(row["faces"]) for row in meshes) == 51580
    pairs = [pair for mesh in meshes for pair in _pairs(mesh, targets)]
    totals = {
        target["key"]: sum(
            row["overlapping_triangle_pair_count"] for row in pairs if row["target_key"] == target["key"]
        )
        for target in targets
    }
    print("HEADER_WORKPIECE_POSE", feature, pose["frame"], json.dumps(totals), flush=True)
    return {
        "held_header": feature,
        "nominal_index": axis["nominal_index"],
        "saved_frame": pose["frame"],
        "saved_bank_index": index,
        "original_header_world_position_m": pose["header_world_position_m"],
        "derived_translation_m": (np.asarray(spec["model_translation_m"]) - pose["header_world_position_m"]).tolist(),
        "hand_bounds_product_m": _bounds(meshes).tolist(),
        "hand_objects": len(meshes),
        "hand_triangles": 51580,
        "target_pair_totals": totals,
        "pairs": pairs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_json", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    assert not args.output_json.exists(), "Preserve the existing observation"
    settings = _read(SETTINGS)
    assert settings["bvh_epsilon_m"] == 0 and bpy.data.filepath == ""
    before = _protected(settings)
    before[SETTINGS] = _sha(SETTINGS)
    before["scripts/probe_hvjb_header_workpiece_v01.py"] = _sha("scripts/probe_hvjb_header_workpiece_v01.py")
    original_matrices = {obj.name: list(map(list, obj.matrix_world)) for obj in bpy.data.objects}
    product, sources = _geometry(settings["product_meshes"]), _geometry(settings["hand_meshes"])
    specs, old = _read(settings["header_settings"])["headers"], _read(settings["hand_observation"])
    assert len(product) == 92
    checks = _analytic_checks()
    mapping = [
        _mapping(spec, src, product, settings["numeric_mapping_tolerance_m"])
        for spec, src in zip(specs, sources["headers"], strict=True)
    ]
    targets = _targets(product)
    with np.load(ROOT / settings["motion_bank"], allow_pickle=False) as bank:
        poses = [
            _pose(axis, sources["hand"], bank, spec, targets, settings["numeric_pose_tolerance_m"])
            for spec, model in zip(specs, old["models"], strict=True)
            for axis in model["axes"]
        ]
    assert len(poses) == 14
    after = {path: _sha(path) for path in before}
    assert after == before
    assert original_matrices == {obj.name: list(map(list, obj.matrix_world)) for obj in bpy.data.objects}
    report = {
        "observed_at": datetime.now(UTC).isoformat(),
        "settings": settings,
        "blender_version": bpy.app.version_string,
        "analytic_checks": checks,
        "header_mapping": mapping,
        "targets": [
            {
                key: value.tolist() if isinstance(value, np.ndarray) else value
                for key, value in row.items()
                if key != "tree"
            }
            for row in targets
        ],
        "poses": poses,
        "input_sha256_before": before,
        "input_sha256_current": after,
        "script_sha256": _sha("scripts/probe_hvjb_header_workpiece_v01.py"),
        "source_geometry_or_motion_modified": False,
        "native_opened": False,
        "native_saved": False,
        "startup_world_matrices_unchanged": True,
        "physical_acceptance_verdict": None,
    }
    with args.output_json.open("x") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    assert json.loads(args.output_json.read_text()) == report
    print("HEADER_WORKPIECE_COMPLETE", args.output_json, "poses=14", "protected_inputs=" + str(len(before)), flush=True)


if __name__ == "__main__":
    main()
