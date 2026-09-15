# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Correct three nominal TE wall apertures in a new static native revision [m]."""

from __future__ import annotations

import gzip
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_hvjb_photo_model_v01 as photo
from allocation_product import empty
from build_header_review_v03 import rounded_corner_patch
from build_hvjb_photo_catalog_v01 import digest
from header_review_primitives import box

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "UR15_JB_photo_correspondence_v03_p02.blend"
NATIVE = "UR15_JB_photo_correspondence_v03_p03.blend"
MESH = "data/hvjb_photo_model_v03_p03.json.gz"
AUDIT = "audit/hvjb_header_interface_model_v01.json"
INPUT = "data/hvjb_header_interface_inputs_v01.json"
PREVIEW = "previews/hvjb_header_interface_v01"
PINNED = {
    SOURCE: "3da72f4c042936da0e168b71977fe09dbb1c2057eb5d0da30b215522a8ef004d",
    "data/hvjb_photo_correspondence_v03_p01.json": "6c5b7cb9bab859a33c8f5d5cd5429ce9f06fb0951b8a8fa4ae2a31ad99052ca0",
    "data/hvjb_photo_cad_v01.json.gz": "1ac417baa3ff67ae8bc3ed5c32ac91cfb778a2effbd1e1a19d24900066c38f32",
    "data/hvjb_photo_model_v03_p02.json.gz": "02659a3f27496514a8d0707fdf0057de29f36990990ced49bcf9d06fa50c2214",
    "scripts/build_header_review_v03.py": "216f596e8662b6f8a46a73fb8e3e6527972c241af6453bdb8102b98d82a1b01d",
}


def roots() -> dict:
    """Return the retained photo-feature roots."""
    return {obj["photo_feature_id"]: obj for obj in bpy.context.scene.objects if "photo_feature_id" in obj}


def by_name(geometry: dict) -> dict:
    """Compare evaluated meshes by name, independent of Blender enumeration order."""
    return {
        identifier: sorted(group["meshes"], key=lambda row: (row["name"], row["color"]))
        for identifier, group in geometry.items()
    }


def openings(wall) -> list[dict]:
    """Observe opening X extents between the existing straight piers [m]."""
    piers = []
    for obj in wall.children:
        if "_pier" in obj.name:
            x = [float((obj.matrix_world @ vertex.co).x) for vertex in obj.data.vertices]
            piers.append((min(x), max(x)))
    piers.sort()
    assert len(piers) == 6
    return [
        {"left_m": left[1], "right_m": right[0], "width_m": right[0] - left[1]}
        for left, right in zip(piers[:-1], piers[1:], strict=True)
    ]


def replace_wall(body, old, inputs: dict):
    """Reuse the established wall primitives with each documented bay width [m]."""
    name, location = old.name, old.location.copy()
    material = next(obj.data.materials[0] for obj in old.children if obj.type == "MESH")
    for obj in list(old.children_recursive) + [old]:
        bpy.data.objects.remove(obj, do_unlink=True)
    wall = empty(name, body)
    wall.location = location
    half_height = inputs["aperture_height_m"] / 2
    radius = inputs["aperture_corner_radius_m"]
    assert radius == 0.0044, "Reused corner primitive has a fixed 4.4 mm radius"
    low, high = 0.046 - half_height, 0.046 + half_height
    for bottom, top in ((0, low), (high, 0.08629)):
        box(name + "_band", (0.254, 0.003, top - bottom), (0, -0.0015, (bottom + top) / 2), material, wall, 0)
    stops = [-0.127]
    for row in inputs["apertures"]:
        stops.extend((row["center_x_m"] - row["width_m"] / 2, row["center_x_m"] + row["width_m"] / 2))
    stops.append(0.127)
    for left, right in zip(stops[::2], stops[1::2], strict=True):
        box(name + "_pier", (right - left, 0.003, high - low), ((left + right) / 2, -0.0015, 0.046), material, wall, 0)
    for row in inputs["apertures"]:
        for sx in (-1, 1):
            for sz in (-1, 1):
                rounded_corner_patch(
                    name + "_R4_4",
                    row["center_x_m"] + sx * (row["width_m"] / 2 - radius),
                    0.046 + sz * (half_height - radius),
                    sx,
                    sz,
                    wall,
                    material,
                )
    wall["aperture_basis"] = "TE 2103340 A2 / 2103346 A3 sheet 1 nominal widths; case registration remains estimated"
    wall["aperture_widths_m"] = [row["width_m"] for row in inputs["apertures"]]
    bpy.context.view_layer.update()
    return wall


def projection(inputs: dict) -> list[dict]:
    """Project bare CAD surfaces along source Z against a nominal rounded opening [m]."""
    cad = json.loads(gzip.decompress((ROOT / "data/hvjb_photo_cad_v01.json.gz").read_bytes()))
    result = []
    for row in inputs["apertures"]:
        mesh = cad[row["part_number"]]
        vertices = np.asarray(mesh["vertices"])
        half = np.array((row["width_m"], inputs["aperture_height_m"])) / 2
        radius = inputs["aperture_corner_radius_m"]
        q = abs(vertices[:, :2]) - (half - radius)
        signed = np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(np.max(q, axis=1), 0) - radius
        nearest = int(np.argmax(signed))
        result.append(
            {
                **row,
                "mesh_bounds_m": [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()],
                "mesh_extents_m": np.ptp(vertices, axis=0).tolist(),
                "vertex_count": len(vertices),
                "triangle_count": len(mesh["faces"]),
                "projection_axis": "source CAD +Z / -Z, centered XY, no rotation or scaling",
                "minimum_nominal_projected_inward_distance_m": float(-signed[nearest]),
                "nearest_source_vertex_m": vertices[nearest].tolist(),
                "scope": "bare nominal tessellated housing only; excludes wires, gripper, tolerances and actual travel",
            }
        )
    return result


def main() -> None:
    """Save a new static model and compare all unaffected features and readback."""
    for relative in (NATIVE, MESH, AUDIT, PREVIEW):
        assert not (ROOT / relative).exists(), f"Refusing to overwrite {relative}"
    inputs = json.loads((ROOT / INPUT).read_text())
    expected = {**PINNED, **{source["file"]: source["sha256"] for source in inputs["sources"]}}
    before_hashes = {name: digest(ROOT / name) for name in expected}
    assert before_hashes == expected, "Pinned input differs"
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / SOURCE))
    bpy.context.view_layer.update()
    source_roots = roots()
    source_geometry = photo.export_geometry(source_roots)
    stored = json.loads(gzip.decompress((ROOT / "data/hvjb_photo_model_v03_p02.json.gz").read_bytes()))
    assert by_name(source_geometry) == by_name(stored), "Source native no longer matches its recorded world meshes"
    assert len(source_roots) == 92 and not bpy.data.actions
    world_before = {key: [list(row) for row in obj.matrix_world] for key, obj in source_roots.items()}
    old = next(obj for obj in source_roots["P01"].children if obj.name.endswith("_TE_mount_wall"))
    wall_name = old.name
    before_openings = openings(old)
    old_width_matches = [
        abs(measured["width_m"] - row["width_m"]) < 1e-7
        for measured, row in zip(before_openings, inputs["apertures"], strict=True)
    ]
    assert old_width_matches == [False, True, False, True, False], old_width_matches
    wall = replace_wall(source_roots["P01"], old, inputs)
    after_openings = openings(wall)
    new_width_matches = [
        abs(measured["width_m"] - row["width_m"]) < 1e-7
        for measured, row in zip(after_openings, inputs["apertures"], strict=True)
    ]
    assert all(new_width_matches), after_openings
    geometry = photo.export_geometry(source_roots)
    source_meshes, current_meshes = by_name(source_geometry), by_name(geometry)
    assert all(source_meshes[key] == current_meshes[key] for key in source_roots if key != "P01")
    unchanged_case = [row for row in source_meshes["P01"] if wall_name not in row["name"]]
    assert unchanged_case == [row for row in current_meshes["P01"] if wall_name not in row["name"]]
    scene = bpy.context.scene
    scene["scope"] = "Static photo model v03 p03: TE nominal aperture widths corrected; process interfaces unresolved"
    scene["header_interface_input_sha256"] = digest(ROOT / INPUT)
    (ROOT / MESH).write_bytes(gzip.compress(json.dumps(geometry, separators=(",", ":")).encode(), mtime=0))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / NATIVE), check_existing=True)
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / NATIVE))
    bpy.context.view_layer.update()
    reopened = roots()
    assert photo.export_geometry(reopened) == geometry, "Saved world meshes changed on readback"
    assert world_before == {key: [list(row) for row in obj.matrix_world] for key, obj in reopened.items()}
    assert not bpy.data.actions
    after_hashes = {name: digest(ROOT / name) for name in expected}
    assert before_hashes == after_hashes
    report = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "native": NATIVE,
        "native_sha256": digest(ROOT / NATIVE),
        "mesh": MESH,
        "mesh_sha256": digest(ROOT / MESH),
        "input_sha256": digest(ROOT / INPUT),
        "source_sha256_before": before_hashes,
        "source_sha256_after": after_hashes,
        "before_openings": before_openings,
        "after_openings": after_openings,
        "drawing_widths_m": [row["width_m"] for row in inputs["apertures"]],
        "before_nominal_width_matches": old_width_matches,
        "after_nominal_width_matches": new_width_matches,
        "numeric_comparison_epsilon_m": 1e-7,
        "numeric_epsilon_role": "serialized float comparison, not a manufacturing acceptance tolerance",
        "feature_count": len(reopened),
        "unaffected_feature_meshes_exact": 91,
        "non_wall_case_meshes_exact": len(unchanged_case),
        "feature_world_matrices_exact": True,
        "saved_world_meshes_exact": True,
        "animation_actions": len(bpy.data.actions),
        "nominal_bare_housing_projection": projection(inputs),
        "formal_physical_verdict": None,
        "plate_joint_or_grasp_created": False,
    }
    with (ROOT / AUDIT).open("x") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (ROOT / PREVIEW).mkdir()
    scene = bpy.context.scene
    scene.camera = bpy.data.objects["oblique"]
    scene.render.filepath = str(ROOT / PREVIEW / "model.png")
    bpy.ops.render.render(write_still=True)
    print(
        "HEADER_INTERFACE_MODEL_OK",
        json.dumps(
            {
                k: report[k]
                for k in (
                    "native",
                    "feature_count",
                    "before_nominal_width_matches",
                    "after_nominal_width_matches",
                    "unaffected_feature_meshes_exact",
                    "saved_world_meshes_exact",
                    "animation_actions",
                )
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
