# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read saved H05 surfaces and record screw-axis radial distances [m]."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import probe_hand_tool_access_v01 as reuse
import trimesh

ROOT = Path(__file__).resolve().parents[1]
INPUT = "data/hvjb_header_hand_access_v01.json"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def protected_inputs(settings: dict) -> dict[str, str]:
    previous = read_json(settings["previous_readback"])
    pins = {**previous["input_sha256_current"], **previous["artifact_sha256"]}
    for path, expected in settings["additional_sha256"].items():
        assert path not in pins or pins[path] == expected, path
        pins[path] = expected
    for path in (INPUT, settings["previous_readback"]):
        pins[path] = digest(ROOT / path)
    observed = {path: digest(ROOT / path) for path in pins}
    assert observed == pins, "Protected input SHA mismatch"
    prepared, built = read_json(settings["prepare_record"]), read_json(settings["build_record"])
    assert prepared["mesh_sha256"] == built["mesh_inputs_sha256"] == pins[settings["hand_meshes"]]
    assert prepared["motion_sha256"] == built["motion_sha256"] == pins[settings["motion_bank"]]
    assert built["native_sha256"] == pins[built["native"]]
    return observed


def saved_pose(hand: dict, bank: np.lib.npyio.NpzFile, schedule: dict, settings: dict) -> tuple[dict, list[dict]]:
    """Read the nearest saved closed-holding pose and header-relative meshes [m, rad, s]."""
    target = settings["saved_movie_offset_s"] + schedule["start"] + settings["sample_after_authored_fastening_start_s"]
    index = int(np.argmin(abs(bank["time_s"] - target)))
    header_index = schedule["header"]
    header_position = bank[f"header_{header_index}_position"][index]
    assert float(bank["gripper_q"][index]) == hand["q_closed"][header_index]
    objects, matrices = [], {}
    for name, row in hand["objects"].items():
        matrix = bank["OP020_hand_" + name][index].copy()
        matrices[name] = matrix.tolist()
        vertices = np.asarray(row["vertices"]) @ matrix[:3, :3].T + matrix[:3, 3] - header_position
        faces = np.asarray(row["faces"])
        objects.append(
            {
                "name": name,
                "category": row["category"],
                "triangles": vertices[faces],
                "vertices": vertices,
                "faces": faces,
                "bounds_header_m": [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()],
            }
        )
    meta = {
        "bank_index": index,
        "frame": int(bank["frames"][index]),
        "saved_time_s": float(bank["time_s"][index]),
        "requested_time_s": target,
        "gripper_q_rad": float(bank["gripper_q"][index]),
        "header_world_position_m": header_position.tolist(),
        "header_world_rotation": np.eye(3).tolist(),
        "hand_object_world_matrices": matrices,
    }
    return meta, objects


def grouped_surfaces(objects: list[dict], axis: np.ndarray) -> dict:
    """Rotate all saved triangles into the reused Z-slab query frame [m]."""
    groups = {}
    for category in sorted({row["category"] for row in objects}):
        names, offsets, triangles = [], {}, []
        for row in (item for item in objects if item["category"] == category):
            source = row["triangles"]
            local = source[:, :, [0, 2, 1]].copy()
            local[:, :, :2] -= axis
            local[:, :, 2] *= -1
            offsets[row["name"]] = len(names)
            names.extend([row["name"]] * len(source))
            triangles.append(local)
        groups[category] = {"triangles": np.concatenate(triangles), "names": names, "offsets": offsets}
    return groups


def observe_band(group: dict, bounds: list[float], axis: np.ndarray, tolerance: float) -> dict:
    """Reuse clipped surface projection and verify its original-triangle witness [m]."""
    result = reuse._slab_nearest(group["triangles"], group["names"], bounds)
    if result["radius_to_surface_m"] is None:
        return {**result, "witness_header_m": None, "witness_on_triangle_error_m": None}
    index, name = result["source_face_index"], result["object"]
    witness = np.asarray(result.pop("witness_m"))
    error = witness_error(group["triangles"][index], witness)
    assert error < tolerance, (name, index, error)
    assert bounds[0] - tolerance <= witness[2] <= bounds[1] + tolerance
    assert abs(np.linalg.norm(witness[:2]) - result["radius_to_surface_m"]) < tolerance
    result.update(
        {
            "source_face_index": index - group["offsets"][name],
            "witness_header_m": [float(witness[0] + axis[0]), float(-witness[2]), float(witness[1] + axis[1])],
            "witness_on_triangle_error_m": error,
        }
    )
    return result


def witness_error(triangle: np.ndarray, witness: np.ndarray) -> float:
    """Validate a triangle witness [m] in normalized coordinates, then convert back to metres."""
    origin = triangle[0]
    scale = float(np.max(np.linalg.norm(np.roll(triangle, -1, axis=0) - triangle, axis=1)))
    if scale == 0:
        return float(np.linalg.norm(witness - origin))
    closest = trimesh.triangles.closest_point(((triangle - origin) / scale)[None], ((witness - origin) / scale)[None])[
        0
    ]
    return float(np.linalg.norm(closest * scale + origin - witness))


def nearest_group(rows: dict) -> dict:
    valid = [(name, row) for name, row in rows.items() if row["radius_to_surface_m"] is not None]
    if not valid:
        return {"radius_to_surface_m": None, "category": None, "object": None}
    category, selected = min(valid, key=lambda item: item[1]["radius_to_surface_m"])
    return {**selected, "category": category}


def observe_axis(axis_record: dict, pose: dict, objects: list[dict], settings: dict) -> dict:
    axis = np.asarray(axis_record["nominal_local_xz_m"])
    groups = grouped_surfaces(objects, axis)
    depth = np.concatenate([row["triangles"][:, :, 2].reshape(-1) for row in groups.values()])
    step, tolerance = settings["profile_bin_depth_m"], settings["numeric_comparison_tolerance_m"]
    first, last = math.floor(float(depth.min()) / step), math.ceil(float(depth.max()) / step)
    boundaries = np.arange(first, last + 1, dtype=float) * step
    profile = []
    for lower, upper in zip(boundaries[:-1], boundaries[1:], strict=True):
        band = [float(lower), float(upper)]
        rows = {name: observe_band(group, band, axis, tolerance) for name, group in groups.items()}
        profile.append({"depth_range_m": band, "categories": rows, "all": nearest_group(rows)})
    whole_range = [float(depth.min()), float(depth.max())]
    whole = {name: observe_band(group, whole_range, axis, tolerance) for name, group in groups.items()}
    for category, row in whole.items():
        samples = [band["categories"][category]["radius_to_surface_m"] for band in profile]
        assert abs(min(value for value in samples if value is not None) - row["radius_to_surface_m"]) < tolerance
    return {
        "screw_name": axis_record["name"],
        "nominal_index": axis_record["nominal_index"],
        "nominal_local_xz_m": axis.tolist(),
        "saved_product_axis_delta_m": axis_record["axis_nominal_delta_m"],
        "pose": pose,
        "objects": [
            {key: value for key, value in row.items() if key not in ("triangles", "vertices", "faces")}
            | {"vertices": len(row["vertices"]), "triangles": len(row["faces"])}
            for row in objects
        ],
        "objects_included": len(objects),
        "triangles_included": sum(len(row["faces"]) for row in objects),
        "hand_depth_range_m": whole_range,
        "whole_span": {"categories": whole, "all": nearest_group(whole)},
        "profile": profile,
    }


def observe_header(spec: dict, hand: dict, bank: np.lib.npyio.NpzFile, schedule: list, settings: dict) -> dict:
    rows = []
    for axis, item in zip(spec["screws"], schedule, strict=True):
        pose, objects = saved_pose(hand, bank, item, settings)
        assert len(objects) == settings["expected_objects_per_pose"]
        assert sum(len(row["faces"]) for row in objects) == settings["expected_triangles_per_pose"]
        assert set(row["category"] for row in objects) == set(settings["categories"])
        old_local_axis = (np.asarray(item["tip"]) - pose["header_world_position_m"])[[0, 2]]
        assert np.max(abs(old_local_axis - axis["nominal_local_xz_m"])) < settings["numeric_comparison_tolerance_m"]
        row = observe_axis(axis, pose, objects, settings)
        rows.append(row)
        nearest = row["whole_span"]["all"]
        print(
            "HEADER_HAND_AXIS_OBSERVED",
            spec["feature_id"],
            axis["nominal_index"],
            "frame",
            pose["frame"],
            "radius_m",
            nearest["radius_to_surface_m"],
            "object",
            nearest["object"],
            flush=True,
        )
    return {"feature_id": spec["feature_id"], "part_number": spec["part_number"], "axes": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_json", type=Path, default=ROOT / "audit/hvjb_header_hand_access_v01.json")
    args = parser.parse_args()
    assert not args.output_json.exists(), "Preserve the existing observation"
    settings = read_json(INPUT)
    before = protected_inputs(settings)
    prepared, axes = read_json(settings["prepare_record"]), read_json(settings["header_axes"])
    hand = json.loads(gzip.decompress((ROOT / settings["hand_meshes"]).read_bytes()))["hand"]
    assert hand["q_closed"] == prepared["hand_q_closed_rad"]
    analytic = reuse._analytic_checks()
    with np.load(ROOT / settings["motion_bank"], allow_pickle=False) as bank:
        models = [
            observe_header(
                spec,
                hand,
                bank,
                [row for row in prepared["display_bolt_schedule"] if row["header"] == index],
                settings["measurement"],
            )
            for index, spec in enumerate(axes["models"])
        ]
    after = {path: digest(ROOT / path) for path in before}
    assert after == before, "Protected input changed"
    report = {
        "observed_at": datetime.now(UTC).isoformat(),
        "scope": settings["scope"],
        "settings": settings,
        "analytic_checks_reused": analytic,
        "models": models,
        "source_feature_count": axes["source_feature_count"],
        "method": (
            "Reused triangle clipping over complete 2 mm intervals, radial surface projection, full saved hand meshes"
        ),
        "witness_validator": (
            "Triangle origin translation and longest-edge normalization before closest_point; errors in m"
        ),
        "source_input_sha256_before": before,
        "source_input_sha256_after": after,
        "script_sha256": digest(Path(__file__)),
        "native_opened": False,
        "native_saved": False,
        "motion_recomputed": False,
        "geometry_modified": False,
        "physical_acceptance_verdict": None,
    }
    with args.output_json.open("x") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    assert json.loads(args.output_json.read_text()) == report
    print("HEADER_HAND_ACCESS_COMPLETE", args.output_json, flush=True)


if __name__ == "__main__":
    main()
