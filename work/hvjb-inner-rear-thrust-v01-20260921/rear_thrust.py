# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Compare a split rear-rim pusher with unchanged connector CAD, in SI units."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent / "hvjb-inner-tip-access-v01-20260921"
spec = importlib.util.spec_from_file_location("retained_tip_geometry", PREVIOUS / "geometry.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)
OUTPUT = ROOT / "output"
CONFIG = {
    "status": "comparison_only_not_manufacturing_or_acceptance_specification",
    "pad_source_z_m": [-0.0422, -0.0391],
    "carrier_source_z_m": [-0.0435, -0.0391],
    "pad_offsets_from_original_rear_profile_m": [0.0001, 0.001],
    "carrier_offsets_m": [0.001, 0.003],
    "rear_lip_offsets_m": [-0.0005, 0.001],
    "rear_lip_front": "unchanged CAD minimum Z plane",
    "opening_each_side_m": 0.002,
    "withdrawal_m": 0.008,
    "cavity_section_ahead_of_rear_plane_m": 5e-7,
    "planar_selection_numeric_epsilon_m": 1e-8,
    "strict_interior_numeric_inset_m": 1e-9,
    "display_registration": G.CONFIG["display_inner_transform"],
    "display_registration_is_not_measured_mated_pose": True,
    "wall_header_y_m": [0.0, 0.003],
}


def make_tips(housing):
    profile = G.rear_profile(housing)
    pieces = []
    bands = [
        ("pad", CONFIG["pad_offsets_from_original_rear_profile_m"], CONFIG["pad_source_z_m"]),
        ("carrier", CONFIG["carrier_offsets_m"], CONFIG["carrier_source_z_m"]),
        ("thrust", CONFIG["rear_lip_offsets_m"], [CONFIG["carrier_source_z_m"][0], housing.bounds[0, 2]]),
    ]
    for sign in (-1, 1):
        for name, offsets, z_range in bands:
            low, high = [G.offset_profile(profile, offset) for offset in offsets]
            for index in range(len(profile) - 1):
                polygon = np.array([low[index], low[index + 1], high[index + 1], high[index]])
                polygon[:, 0] *= sign
                pieces.append(G.prism(polygon, z_range, name, sign))
    return pieces


def rear_faces(housing):
    z = housing.bounds[0, 2]
    planar = abs(housing.triangles[:, :, 2] - z).max(1) < CONFIG["planar_selection_numeric_epsilon_m"]
    return housing.triangles[planar & (housing.face_normals[:, 2] < -0.99)]


def xy_projection_patches(triangles, pieces):
    patches = []
    for piece in pieces:
        normals, limits = piece["planes"]
        xy = np.linalg.norm(normals[:, :2], axis=1) > 0.5
        for triangle in triangles:
            clipped = G.clip_polygon(triangle, normals[xy], limits[xy])
            if G.polygon_area(clipped) > G.CONFIG["clipped_area_reporting_epsilon_m2"]:
                patches.append(clipped)
    return patches


def cavity_loops(housing):
    z = housing.bounds[0, 2] + CONFIG["cavity_section_ahead_of_rear_plane_m"]
    lines = trimesh.intersections.mesh_plane(housing, [0, 0, 1], [0, 0, z])
    loops = trimesh.load_path(lines).discrete
    assert len(loops) == 4, f"Expected two inner and two outer section loops, got {len(loops)}"
    # The two nested loops on each side are convex in this saved section.
    result = []
    for sign in (-1, 1):
        pair = [loop for loop in loops if loop[:, 0].mean() * sign > 0]
        assert len(pair) == 2
        loop = min(pair, key=G.polygon_area)[:-1]
        edges = np.roll(loop[:, :2], -1, axis=0) - loop[:, :2]
        turns = edges[:, 0] * np.roll(edges[:, 1], -1) - edges[:, 1] * np.roll(edges[:, 0], -1)
        assert turns.min() >= -1e-12 or turns.max() <= 1e-12
        result.append(loop)
    return result


def fan_triangles(loop):
    return np.stack([loop[[0, index, index + 1]] for index in range(1, len(loop) - 1)])


def contact_observation(housing, pieces):
    flat = rear_faces(housing)
    pushing = [piece for piece in pieces if piece["name"] == "thrust"]
    bearing = []
    for sign in (-1, 1):
        patches = xy_projection_patches(flat, [piece for piece in pushing if piece["sign"] == sign])
        bearing.append({"side": sign, "rear_flat_face_projected_overlap_m2": sum(map(G.polygon_area, patches))})
    cavities = []
    for loop in cavity_loops(housing):
        patches = xy_projection_patches(fan_triangles(loop), pushing)
        cavities.append(
            {
                "section_bounds_m": [loop.min(0).tolist(), loop.max(0).tolist()],
                "section_area_m2": G.polygon_area(loop),
                "closed_lip_projection_overlap_with_section_m2": sum(map(G.polygon_area, patches)),
            }
        )
    strict_pieces = []
    for piece in pieces:
        inset = piece.copy()
        normals, limits = piece["planes"]
        inset["planes"] = (normals, limits - CONFIG["strict_interior_numeric_inset_m"])
        strict_pieces.append(inset)
    return {
        "rear_plane_source_z_m": float(housing.bounds[0, 2]),
        "rear_flat_face_triangle_count": len(flat),
        "rear_flat_face_total_m2": sum(map(G.polygon_area, flat)),
        "projected_bearing_by_side": bearing,
        "cavity_sections": cavities,
        "housing_surface_in_strict_tip_interiors": G.surfaces_in_pieces(housing.triangles, strict_pieces),
        "meaning": "Nominal CAD projection, not deformed contact area, force capacity or wire clearance.",
    }


def swept_observation(header, pieces):
    # For both pure translations, all intermediate coordinates lie between endpoint bounds.
    vertices = np.vstack(
        [
            G.moved_piece(piece, opening, withdrawal)["mesh"].vertices
            for opening, withdrawal in (
                (0, 0),
                (CONFIG["opening_each_side_m"], 0),
                (CONFIG["opening_each_side_m"], CONFIG["withdrawal_m"]),
            )
            for piece in pieces
        ]
    )
    lo, hi = vertices.min(0), vertices.max(0)
    header_rear_z = header.bounds[0, 2]
    return {
        "scope": "Open radially 0..2 mm each, then withdraw axially 0..8 mm, housing held stationary as an assumption.",
        "bound_method": "Monotone translations; union endpoint AABB contains both full translation sweeps.",
        "swept_tip_bounds_source_m": [lo.tolist(), hi.tolist()],
        "whole_header_axial_aabb_separation_m": float(header_rear_z - hi[2]),
        "display_wall_axial_separation_m": float(-0.0341 - hi[2]),
        "caveat": (
            "Only tips versus retained header/wall pose; no actual wires, hand body, other internals or latch state."
        ),
    }


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    inners, headers, inputs, provenance = G.load_sources()
    pieces = make_tips(G.mesh(inners["2103245-1"]))
    rows = []
    for aperture in inputs["apertures"]:
        base_x, number = (-0.052, "2103340-1") if aperture["header"] == "P16" else (0.072, "2103346-2")
        housing = G.mesh(inners[aperture["part_number"]])
        header = G.header_in_inner_frame(G.mesh(headers[number]), aperture["center_x_m"] - base_x)
        row = {
            "id": aperture["id"],
            "key": aperture["key"],
            "part_number": aperture["part_number"],
            "header": aperture["header"],
            "rear_contact": contact_observation(housing, pieces),
            "closed_header_surface_in_tip_volumes": G.surfaces_in_pieces(header.triangles, pieces),
            "release_comparison": swept_observation(header, pieces),
        }
        rows.append(row)
        print(
            aperture["id"],
            "bearing_mm2",
            [
                round(item["rear_flat_face_projected_overlap_m2"] * 1e6, 6)
                for item in row["rear_contact"]["projected_bearing_by_side"]
            ],
            "cavity_overlap_mm2",
            [
                item["closed_lip_projection_overlap_with_section_m2"] * 1e6
                for item in row["rear_contact"]["cavity_sections"]
            ],
            "header_axial_separation_mm",
            row["release_comparison"]["whole_header_axial_aabb_separation_m"] * 1000,
            flush=True,
        )
    result = {
        "config": CONFIG,
        "bays": rows,
        "numerical_checks": G.numerical_checks(),
        "input_inner_sha256": G.sha(G.INNER),
        "input_apertures_sha256": G.sha(G.APERTURES),
        "input_outer_provenance": provenance,
        "geometry_script_sha256": G.sha(Path(__file__)),
        "reused_geometry_script_sha256": G.sha(PREVIOUS / "geometry.py"),
        "trial_tip_meshes_sha256": G.save_meshes(pieces, OUTPUT, "rear_thrust_tip_meshes.json.gz"),
        "limits_ja": [
            "比較寸法であり製作仕様・受入条件ではない。後端樹脂縁の許容荷重は未確認。",
            "0.1 mmの表示逃げを残しているため、閉指令・圧縮量・保持成立を示さない。",
            "穴の投影を塞がないことと、実電線の経路を避けることは別であり、後者は未評価。",
            "内外CADは既存表示の登録位置。実測嵌合位置・ロック完了位置ではない。",
            "開放後に内側ハウジングが残留保持される条件・確認方法はまだ定めていない。",
            "開放・後退の図は指先だけの幾何比較。アーム軌道や実機動作を決めたものではない。",
        ],
    }
    (OUTPUT / "rear_thrust_observations.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("REAR_THRUST_OBSERVATIONS_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
