# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Observe comparison hand volumes against the unchanged populated display model [m]."""

from __future__ import annotations

import gzip
import importlib.util
import json
from pathlib import Path

import numpy as np
import prepare_inputs as P
import trimesh
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent / "hvjb-inner-rear-thrust-v01-20260921"
spec = importlib.util.spec_from_file_location("rear_thrust_reference", PREVIOUS / "rear_thrust.py")
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)
G = T.G
OUTPUT = ROOT / "output"
ROTATION = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=float)
CONFIG = {
    "status": "comparison_only_not_selected_hardware_or_robot_motion",
    "body_jaw_datum_world_z_m": 0.090,
    "stem_width_m": 0.002,
    "mounting_shoe_thickness_m": 0.003,
    "radial_openings_each_m": [0.002, 0.004],
    "rearward_comparison_m": 0.008,
    "upward_comparison_m": 0.050,
    "strict_interior_numeric_inset_m": 1e-9,
    "mapping_numeric_epsilon_m": 1e-7,
    "whole_pge_cad": False,
    "gripper_electrical_lead_or_robot_adapter_included": False,
    "product_wire_shapes_completed": False,
}


def convex_piece(vertices, faces, name, side, kind):
    solid = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    hull = ConvexHull(np.asarray(vertices))
    return {
        "mesh": solid,
        "planes": (hull.equations[:, :3], -hull.equations[:, 3]),
        "name": name,
        "sign": side,
        "kind": kind,
    }


def box_piece(lo, hi, name, side, kind):
    solid = trimesh.creation.box(np.asarray(hi) - lo)
    solid.apply_translation((np.asarray(hi) + lo) / 2)
    return convex_piece(solid.vertices, solid.faces, name, side, kind)


def translate(piece, delta):
    result = piece.copy()
    result["mesh"] = piece["mesh"].copy()
    result["mesh"].apply_translation(delta)
    normals, limits = piece["planes"]
    result["planes"] = normals, limits + normals @ delta
    return result


def pose(parts, opening=0.0, back=0.0, lift=0.0):
    return [translate(p, [p["sign"] * opening, back, lift]) for p in parts]


def translation_sweeps(start, end):
    result = []
    for a, b in zip(start, end, strict=True):
        points = np.vstack([a["mesh"].vertices, b["mesh"].vertices])
        # A convex part translated on a segment sweeps exactly the convex hull of its endpoints.
        hull = ConvexHull(points)
        result.append(convex_piece(points, hull.simplices, a["name"], a["sign"], a["kind"]))
    return result


def build_hand(inner, saved, pge):
    source = G.mesh(inner)
    actual = np.concatenate([row["vertices"] for row in saved["meshes"]])
    assert len(saved["meshes"]) == 1 and np.array_equal(saved["meshes"][0]["faces"], source.faces)
    transformed = source.vertices @ ROTATION.T
    origin = np.median(actual - transformed, axis=0)
    residual = float(abs(actual - transformed - origin).max())
    assert residual < CONFIG["mapping_numeric_epsilon_m"]
    pieces = []
    for index, piece in enumerate(T.make_tips(source)):
        mesh = piece["mesh"]
        pieces.append(
            convex_piece(
                mesh.vertices @ ROTATION.T + origin,
                mesh.faces,
                f"tip_{piece['name']}_{index:03d}",
                piece["sign"],
                piece["name"],
            )
        )
    bounds = np.array([p["mesh"].bounds for p in pieces])
    x_outer = bounds[:, 1, 0].max() - origin[0]
    jaw_center = x_outer - CONFIG["stem_width_m"] / 2
    y_band = [bounds[:, 0, 1].min(), bounds[:, 1, 1].max()]
    datum = np.array([origin[0], np.mean(y_band), CONFIG["body_jaw_datum_world_z_m"]])
    old_frame = np.asarray(pge["geometry"]["body_datum_world_m"])
    for name, row in pge["candidates"]["PGE_SAMPLE"]["objects"].items():
        if row["category"] != "hardware":
            continue
        points = (np.asarray(row["vertices"]) - old_frame[:3, 3]) @ old_frame[:3, :3]
        side = row["side"]
        if side:
            points[:, 0] += side * jaw_center - points[:, 0].mean()
        pieces.append(convex_piece(points + datum, row["faces"], name, side, "catalogue_envelope"))
    for side in (-1, 1):
        x = origin[0] + side * jaw_center
        pieces.append(
            box_piece(
                [x - 0.001, y_band[0], origin[2]], [x + 0.001, y_band[1], datum[2]], f"stem_{side}", side, "trial_stem"
            )
        )
        pieces.append(
            box_piece(
                [x - 0.007, datum[1] - 0.007, datum[2] - 0.003],
                [x + 0.007, datum[1] + 0.007, datum[2]],
                f"shoe_{side}",
                side,
                "trial_shoe",
            )
        )
    return pieces, {
        "inner_origin_world_m": origin.tolist(),
        "inner_rigid_mapping_residual_m": residual,
        "body_jaw_datum_world_m": datum.tolist(),
        "jaw_gap_closed_m": float(2 * jaw_center - 0.014),
        "stem_vertical_extent_m": float(datum[2] - origin[2]),
    }


def target_meshes(product):
    result = {}
    for key, row in product.items():
        triangles = np.concatenate([np.asarray(m["vertices"])[m["faces"]] for m in row["meshes"]])
        result[key] = {"triangles": triangles, "bounds": [triangles.min((0, 1)), triangles.max((0, 1))]}
    return result


def observations(parts, targets):
    rows = []
    for key, target in targets.items():
        lo, hi = target["bounds"]
        possible = [p for p in parts if not (np.any(p["mesh"].bounds[1] < lo) or np.any(hi < p["mesh"].bounds[0]))]
        strict = []
        for piece in possible:
            item = piece.copy()
            normal, limit = piece["planes"]
            item["planes"] = normal, limit - CONFIG["strict_interior_numeric_inset_m"]
            strict.append(item)
        clipped = G.surfaces_in_pieces(target["triangles"], strict)
        if possible:
            rows.append({"feature_id": key, "aabb_candidate_parts": len(possible), **clipped})
    return {
        "all_target_features": len(targets),
        "aabb_candidate_features": len(rows),
        "candidate_records": rows,
        "positive_surface_features": [
            r["feature_id"] for r in rows if r["unique_source_triangles_with_positive_clipped_area"]
        ],
    }


def wire_coverage(product, catalog):
    rows = []
    for wire in catalog["visible_wire_segments"]:
        if not wire["id"].startswith("WI"):
            continue
        feature = wire["nearby_features"][0]
        rear_y = max(np.asarray(m["vertices"])[:, 1].max() for m in product[feature]["meshes"])
        wire_y = min(np.asarray(m["vertices"])[:, 1].min() for m in product[wire["id"]]["meshes"])
        rows.append(
            {
                "wire_id": wire["id"],
                "nearby_inner": feature,
                "wire_min_y_minus_housing_rear_y_m": float(wire_y - rear_y),
                "source_bind_display_geometry": wire["observed_trace_ends"][0]["bind_display_geometry"],
                "cavity_number": wire["observed_trace_ends"][0]["cavity_number"],
            }
        )
    return {
        "observations": rows,
        "no_saved_WI_fragments_for": ["I03"],
        "meaning": "Axial gaps between retained display extents, not measured real wire lengths or mating defects.",
    }


def numerical_checks():
    start = box_piece([0, 0, 0], [1, 1, 1], "analytic", 1, "check")
    swept = translation_sweeps([start], [translate(start, [2, 0, 0])])[0]
    target = {
        "sample": {
            "bounds": [np.array([1.5, 0.2, 0.2]), np.array([1.5, 0.8, 0.8])],
            "triangles": np.array([[[1.5, 0.2, 0.2], [1.5, 0.8, 0.2], [1.5, 0.2, 0.8]]]),
        }
    }
    assert not observations([start], target)["positive_surface_features"]
    assert not observations([translate(start, [2, 0, 0])], target)["positive_surface_features"]
    found = observations([swept], target)
    area = found["candidate_records"][0]["summed_clipped_surface_area_m2"]
    assert abs(area - 0.18) < 1e-12
    return {
        "intermediate_plane_missed_at_endpoints_but_found_in_sweep": True,
        "swept_triangle_area_m2": area,
        "retained_clipping_checks": G.numerical_checks(),
    }


def examine_bay(aperture, product, inners, pge, targets):
    parts, mapping = build_hand(inners[aperture["part_number"]], product[aperture["id"]], pge)
    opened2, opened4 = pose(parts, opening=0.002), pose(parts, opening=0.004)
    comparisons = [
        ("closed", parts),
        ("open_2_sweep", translation_sweeps(parts, opened2)),
        ("back_8_after_open_2_sweep", translation_sweeps(opened2, pose(parts, opening=0.002, back=0.008))),
        ("lift_50_after_open_2_sweep", translation_sweeps(opened2, pose(parts, opening=0.002, lift=0.050))),
        ("open_4_sweep", translation_sweeps(parts, opened4)),
        ("lift_50_after_open_4_sweep", translation_sweeps(opened4, pose(parts, opening=0.004, lift=0.050))),
    ]
    report = {}
    for name, sweep in comparisons:
        result = observations(sweep, targets)
        report[name] = result
        print(aperture["id"], name, result["positive_surface_features"], flush=True)
    return {"id": aperture["id"], "key": aperture["key"], "mapping": mapping, "comparisons": report}, parts


def main():
    assert not (OUTPUT / "installed_access_observations.json").exists()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    product, manifest = P.load_product()
    inners, _, inputs, _ = G.load_sources()
    pge_path = P.DATA / "hvjb_pge_finger_v01_meshes.json.gz"
    assert P.sha(pge_path) == manifest["pge_parent_sha256"]
    pge = json.loads(gzip.decompress(pge_path.read_bytes()))
    catalog_path = G.REF / "data/hvjb_photo_correspondence_v03_p01.json"
    catalog = json.loads(catalog_path.read_text())
    targets = target_meshes(product)
    checks = numerical_checks()
    bays, hashes = [], {}
    for aperture in inputs["apertures"]:
        report, parts = examine_bay(aperture, product, inners, pge, targets)
        bays.append(report)
        hashes[aperture["id"]] = G.save_meshes(parts, OUTPUT, f"hand_{aperture['id']}.json.gz")
    result = {
        "config": CONFIG,
        "bays": bays,
        "wire_coverage": wire_coverage(product, catalog),
        "input_manifest_sha256": P.sha(P.DATA / "product_manifest.json"),
        "input_product_sha256": manifest["parent_sha256"],
        "catalog_sha256": P.sha(catalog_path),
        "pge_sha256": P.sha(pge_path),
        "script_sha256": P.sha(Path(__file__)),
        "rear_thrust_script_sha256": P.sha(PREVIOUS / "rear_thrust.py"),
        "saved_hand_meshes_sha256": hashes,
        "numerical_checks": checks,
        "formal_physical_verdict": None,
        "limits": [
            "Saved display product is not a complete manufactured assembly or an actual assembly-time state.",
            "Surface in swept convex tool volumes is auxiliary geometry, not collision-force or grasp acceptance.",
            "Zero surface hits do not exclude a tool entirely contained in an obstacle solid.",
            "Same-target rear-rim intended contact is reported separately by feature ID, not silently omitted.",
            "Source wire endpoints, contacts, HVIL leads and actual mating depth remain unresolved.",
            "PGE catalogue envelope excludes connectors, electrical lead, robot flange and mounting details.",
        ],
    }
    (OUTPUT / "installed_access_observations.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("INSTALLED_ACCESS_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
