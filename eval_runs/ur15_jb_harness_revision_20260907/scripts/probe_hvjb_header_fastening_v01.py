# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Observe header axes and saved fastener envelopes [m] without changing the model."""

from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT = "data/hvjb_header_fastening_inputs_v01.json"
PREVIOUS = "audit/hvjb_fastener_interface_sources_v01.json"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_meshes(path: str) -> dict:
    return json.loads(gzip.decompress((ROOT / path).read_bytes()))


def cross2(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


def barycentric(triangles: np.ndarray, point: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    a = triangles[:, 0]
    ab, ac = triangles[:, 1] - a, triangles[:, 2] - a
    determinant = cross2(ab, ac)
    valid = determinant != 0
    u, v = np.zeros(len(a)), np.zeros(len(a))
    u[valid] = cross2(point - a, ac)[valid] / determinant[valid]
    v[valid] = cross2(ab, point - a)[valid] / determinant[valid]
    return u, v, valid


def projected_distance(triangles: np.ndarray, point: np.ndarray) -> np.ndarray:
    """Return exact point-to-projected-triangle distances [m], including edge projections."""
    u, v, valid = barycentric(triangles, point)
    inside = valid & (u >= 0) & (v >= 0) & (u + v <= 1)
    distance = np.full(len(triangles), np.inf)
    for index in range(3):
        a = triangles[:, index]
        edge = triangles[:, (index + 1) % 3] - a
        squared_length = np.sum(edge * edge, axis=1)
        ratio = np.zeros(len(a))
        nonzero = squared_length > 0
        ratio[nonzero] = np.clip(np.sum((point - a[nonzero]) * edge[nonzero], axis=1) / squared_length[nonzero], 0, 1)
        distance = np.minimum(distance, np.linalg.norm(a + ratio[:, None] * edge - point, axis=1))
    distance[inside] = 0
    return distance


def wall_hits(walls: list[dict], point: np.ndarray, settings: dict) -> list[dict]:
    """Intersect only the named enclosure front-wall triangles with a Y-axis line [m]."""
    results = []
    epsilon = settings["barycentric_roundoff_tolerance"]
    for row in walls:
        triangles = np.asarray(row["vertices"])[np.asarray(row["faces"])]
        u, v, valid = barycentric(triangles[:, :, [0, 2]], point)
        hit = valid & (u >= -epsilon) & (v >= -epsilon) & (u + v <= 1 + epsilon)
        for index in np.flatnonzero(hit):
            tri = triangles[index]
            y = tri[0, 1] + u[index] * (tri[1, 1] - tri[0, 1]) + v[index] * (tri[2, 1] - tri[0, 1])
            results.append({"mesh": row["name"], "face_index": int(index), "y_m": float(y)})
    return results


def plane_candidates(triangles: np.ndarray, point: np.ndarray, radius: float, settings: dict) -> list[dict]:
    """Find parallel CAD planes overlapping a head's bounding disc [m]; not a contact test."""
    distance = projected_distance(triangles[:, :, [0, 2]], point)
    flat = np.ptp(triangles[:, :, 1], axis=1) <= settings["flat_plane_coordinate_tolerance_m"]
    selected = flat & (distance <= radius)
    planes = np.round(triangles[:, :, 1].mean(axis=1), settings["plane_group_decimal_places"])
    result = []
    for y in np.unique(planes[selected]):
        indices = np.flatnonzero(selected & (planes == y))
        result.append({"y_m": float(y), "face_indices": indices.tolist(), "triangles": len(indices)})
    return result


def observe_screw(head: dict, shaft: dict, spec: dict, triangles: np.ndarray, walls: list, settings: dict) -> dict:
    head_vertices, shaft_vertices = np.asarray(head["vertices"]), np.asarray(shaft["vertices"])
    hb = np.array([head_vertices.min(axis=0), head_vertices.max(axis=0)])
    sb = np.array([shaft_vertices.min(axis=0), shaft_vertices.max(axis=0)])
    translation = np.asarray(spec["model_translation_m"])
    center = hb.mean(axis=0)[[0, 2]]
    local = center - translation[[0, 2]]
    nominal = np.array([[x, z] for x in spec["hole_x_m"] for z in spec["hole_z_m"]])
    nearest = int(np.argmin(np.linalg.norm(nominal - local, axis=1)))
    radius = float(max(hb[1, [0, 2]] - hb[0, [0, 2]]) / 2)
    planes = plane_candidates(triangles, nominal[nearest], radius, settings)
    assert planes, "No parallel CAD plane in the documented head-disc query"
    backing = hb[1, 1] - translation[1]
    closest = min(planes, key=lambda row: abs(row["y_m"] - backing))
    hits = wall_hits(walls, center, settings)
    distinct = sorted(set(round(row["y_m"], settings["plane_group_decimal_places"]) for row in hits))
    assert len(distinct) == 2, "Front-wall interval was not resolved into two surfaces"
    return {
        "name": head["name"],
        "nominal_index": nearest,
        "axis_world_xz_m": center.tolist(),
        "axis_local_xz_m": local.tolist(),
        "nominal_local_xz_m": nominal[nearest].tolist(),
        "axis_nominal_delta_m": (local - nominal[nearest]).tolist(),
        "head_bounds_world_m": hb.tolist(),
        "shaft_bounds_world_m": sb.tolist(),
        "cad_parallel_plane_candidates": planes,
        "nearest_parallel_plane_local_y_m": closest["y_m"],
        "head_back_minus_plane_m": float(backing - closest["y_m"]),
        "wall_triangle_hits": hits,
        "front_wall_interval_world_y_m": distinct,
        "shaft_tip_minus_wall_inner_m": float(sb[1, 1] - distinct[-1]),
        "physical_contact_verdict": None,
    }


def observe_header(spec: dict, official: dict, product: dict, walls: list, settings: dict) -> dict:
    rows = product[spec["feature_id"]]["meshes"]
    vertices, faces = np.asarray(official["vertices"]), np.asarray(official["faces"])
    triangles = vertices[faces]
    heads = [row for row in rows if "_mount_M4_head" in row["name"]]
    shafts = {row["name"]: row for row in rows if "_mount_M4_shank" in row["name"]}
    observed = [
        observe_screw(head, shafts[head["name"].replace("_head", "_shank")], spec, triangles, walls, settings)
        for head in heads
    ]
    expected = len(spec["hole_x_m"]) * len(spec["hole_z_m"])
    assert len(observed) == expected and {row["nominal_index"] for row in observed} == set(range(expected))
    return {
        "part_number": spec["part_number"],
        "feature_id": spec["feature_id"],
        "model_translation_m": spec["model_translation_m"],
        "official_mesh_vertices": len(vertices),
        "official_mesh_triangles": len(faces),
        "model_official_mesh_triangles": sum(len(row["faces"]) for row in rows if "official_CAD" in row["name"]),
        "screws": sorted(observed, key=lambda row: row["nominal_index"]),
        "max_axis_nominal_delta_m": max(float(np.linalg.norm(row["axis_nominal_delta_m"])) for row in observed),
        "shaft_tip_minus_wall_inner_range_m": [
            min(row["shaft_tip_minus_wall_inner_m"] for row in observed),
            max(row["shaft_tip_minus_wall_inner_m"] for row in observed),
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_json", type=Path, default=ROOT / "audit/hvjb_header_fastening_v01.json")
    args = parser.parse_args()
    assert not args.output_json.exists(), "Preserve the existing observation"
    inputs = json.loads((ROOT / INPUT).read_text())
    previous = json.loads((ROOT / PREVIOUS).read_text())
    pins = {**previous["input_sha256_after"], **previous["source_and_prior_record_sha256"]}
    for path in (INPUT, PREVIOUS, inputs["header_meshes"], inputs["existing_generator"]):
        pins[path] = digest(ROOT / path)
    for row in inputs["headers"]:
        pins[row["drawing"]] = row["drawing_sha256"]
    before = {path: digest(ROOT / path) for path in pins}
    assert before == pins, "Input SHA mismatch"
    tree = ast.parse((ROOT / inputs["existing_generator"]).read_text())
    constants = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in ("BOLTS", "OFFSETS")
    }
    assert constants["BOLTS"] == tuple(tuple(row["hole_x_m"]) for row in inputs["headers"])
    assert constants["OFFSETS"] == tuple(row["model_translation_m"][0] for row in inputs["headers"])
    product, official = read_meshes(inputs["model"]), read_meshes(inputs["header_meshes"])["headers"]
    walls = [row for row in product["P01"]["meshes"] if row["name"].startswith("REF_P01_TE_mount_wall")]
    models = [
        observe_header(spec, source, product, walls, inputs["measurement_settings"])
        for spec, source in zip(inputs["headers"], official, strict=True)
    ]
    assert len(product) == 92
    after = {path: digest(ROOT / path) for path in pins}
    assert before == after
    result = {
        "observed_at": datetime.now(UTC).isoformat(),
        "scope": "Nominal-axis correspondence and saved mesh observations; not physical acceptance",
        "settings": inputs["measurement_settings"],
        "plane_query_scope": "Parallel source-CAD triangles overlapping the head bounding disc; no contact-area claim",
        "wall_query_scope": "Only named P01 TE front-wall meshes; excludes fasteners, headers and all other objects",
        "front_wall_mesh_names": [row["name"] for row in walls],
        "source_feature_count": len(product),
        "models": models,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "script_sha256": digest(Path(__file__)),
        "model_saved": False,
        "geometry_modified": False,
        "physical_acceptance_verdict": None,
    }
    with args.output_json.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    assert json.loads(args.output_json.read_text()) == result
    for row in models:
        print(
            "HEADER_OBSERVED",
            row["feature_id"],
            len(row["screws"]),
            row["max_axis_nominal_delta_m"],
            row["shaft_tip_minus_wall_inner_range_m"],
            flush=True,
        )
    print("HEADER_FASTENING_COMPLETE", args.output_json, flush=True)


if __name__ == "__main__":
    main()
