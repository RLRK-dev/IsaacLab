# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Construct trial tips and record static mesh observations, in SI units."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
REF = ROOT.parents[1] / "eval_runs/ur15_jb_harness_revision_20260907"
INNER = REF / "data/hvjb_photo_cad_v01.json.gz"
APERTURES = REF / "data/hvjb_header_interface_inputs_v01.json"
INNER_SHA = "1ac417baa3ff67ae8bc3ed5c32ac91cfb778a2effbd1e1a19d24900066c38f32"
CONFIG = {
    "status": "comparison_only_not_selected_manufacturing_dimensions",
    "source_section_z_m": -0.040,
    "rear_band_source_z_m": [-0.0405, -0.036],
    "display_relief_m": 0.0001,
    "pad_outer_offset_m": 0.001,
    "carrier_outer_offset_m": 0.003,
    "thrust_right_xy_min_m": [0.0094, -0.0008],
    "thrust_right_xy_max_m": [0.0104, 0.0008],
    "thrust_source_z_m": [-0.036, -0.0339],
    "comparison_open_each_side_m": 0.002,
    "comparison_axial_withdrawal_m": 0.008,
    "rear_only_comparison_source_z_m": [-0.0422, -0.0391],
    "rear_only_comparison_has_no_thrust_shoulder": True,
    "display_wall_header_y_m": [0.0, 0.003],
    "display_inner_transform": "header-local (X,Y,Z) = (source X + bay X, -source Z - 0.0311, source Y)",
    "display_registration_is_not_measured_mated_pose": True,
    "profile_collinear_numeric_epsilon_m": 1e-8,
    "clipped_area_reporting_epsilon_m2": 1e-16,
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_sources():
    assert sha(INNER) == INNER_SHA
    inners = json.loads(gzip.decompress(INNER.read_bytes()))
    provenance = json.loads((ROOT / "data/provenance.json").read_text())
    for row in provenance["files"]:
        assert sha(ROOT / "data" / row["file"]) == row["sha256"]
    headers = {}
    for name in ("2103340-1", "2103346-2"):
        headers[name] = json.loads(gzip.decompress((ROOT / "data" / (name + ".json.gz")).read_bytes()))
    return inners, headers, json.loads(APERTURES.read_text()), provenance


def mesh(row):
    return trimesh.Trimesh(vertices=row["vertices"], faces=row["faces"], process=False)


def rear_profile(housing):
    """Use the outer half of the actual right rear-extension section [m]."""
    lines = trimesh.intersections.mesh_plane(housing, [0, 0, 1], [0, 0, CONFIG["source_section_z_m"]])
    loops = trimesh.load_path(lines).discrete
    assert len(loops) == 2
    loop = max(loops, key=lambda row: row[:, 0].mean())[:, :2]
    center = (loop[:, 0].min() + loop[:, 0].max()) / 2
    points = [p for p in loop[:-1] if p[0] > center + 1e-10]
    for a, b in zip(loop[:-1], loop[1:], strict=True):
        if (a[0] - center) * (b[0] - center) <= 0 and abs(b[0] - a[0]) > 1e-12:
            points.append(a + (center - a[0]) / (b[0] - a[0]) * (b - a))
    points = np.unique(np.asarray(points), axis=0)
    order = np.argsort(np.arctan2(points[:, 1], points[:, 0] - center))
    profile = points[order]
    # Remove tessellation split points on a straight segment (10 nm numeric tolerance).
    result = [profile[0]]
    for i in range(1, len(profile) - 1):
        chord = profile[i + 1] - result[-1]
        delta = profile[i] - result[-1]
        distance = abs(chord[0] * delta[1] - chord[1] * delta[0]) / np.linalg.norm(chord)
        if distance > CONFIG["profile_collinear_numeric_epsilon_m"]:
            result.append(profile[i])
    result.append(profile[-1])
    return np.asarray(result)


def offset_profile(profile, distance):
    tangent = np.diff(profile, axis=0)
    tangent /= np.linalg.norm(tangent, axis=1)[:, None]
    normals = np.column_stack((tangent[:, 1], -tangent[:, 0]))
    averaged = (normals[:-1] + normals[1:]) / (1 + (normals[:-1] * normals[1:]).sum(1))[:, None]
    return profile + distance * np.vstack((normals[0], averaged, normals[-1]))


def prism(polygon, z_range, name, sign):
    """Create a convex polygon extrusion and its outward clipping planes [m]."""
    polygon = np.asarray(polygon, dtype=float)
    cross = polygon[:, 0] * np.roll(polygon[:, 1], -1) - polygon[:, 1] * np.roll(polygon[:, 0], -1)
    if cross.sum() < 0:
        polygon = polygon[::-1]
    edges = np.roll(polygon, -1, axis=0) - polygon
    turns = edges[:, 0] * np.roll(edges[:, 1], -1) - edges[:, 1] * np.roll(edges[:, 0], -1)
    assert turns.min() > -1e-14
    count = len(polygon)
    vertices = np.vstack([np.column_stack((polygon, np.full(count, z))) for z in z_range])
    faces = []
    for i in range(1, count - 1):
        faces.extend([[0, i + 1, i], [count, count + i, count + i + 1]])
    for i in range(count):
        j = (i + 1) % count
        faces.extend([[i, j, count + j], [i, count + j, count + i]])
    solid = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    solid.fix_normals()
    assert solid.is_watertight and solid.volume > 0
    normal = np.column_stack((edges[:, 1], -edges[:, 0], np.zeros(count)))
    normal /= np.linalg.norm(normal, axis=1)[:, None]
    limits = (normal[:, :2] * polygon).sum(1)
    normal = np.vstack((normal, [0, 0, -1], [0, 0, 1]))
    limits = np.r_[limits, -z_range[0], z_range[1]]
    return {"mesh": solid, "planes": (normal, limits), "name": name, "sign": sign}


def build_tips(housing):
    profile = rear_profile(housing)
    pieces = []
    for sign in (-1, 1):
        for name, inner, outer in (
            ("pad", CONFIG["display_relief_m"], CONFIG["pad_outer_offset_m"]),
            ("carrier", CONFIG["pad_outer_offset_m"], CONFIG["carrier_outer_offset_m"]),
        ):
            low, high = offset_profile(profile, inner), offset_profile(profile, outer)
            for i in range(len(profile) - 1):
                polygon = np.array([low[i], low[i + 1], high[i + 1], high[i]])
                polygon[:, 0] *= sign
                pieces.append(prism(polygon, CONFIG["rear_band_source_z_m"], name, sign))
        x0, y0 = CONFIG["thrust_right_xy_min_m"]
        x1, y1 = CONFIG["thrust_right_xy_max_m"]
        polygon = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
        polygon[:, 0] *= sign
        pieces.append(prism(polygon, CONFIG["thrust_source_z_m"], "thrust", sign))
    return pieces, profile


def moved_piece(piece, opening=0.0, withdrawal=0.0):
    delta = np.array([piece["sign"] * opening, 0, -withdrawal])
    result = piece.copy()
    result["mesh"] = piece["mesh"].copy()
    result["mesh"].apply_translation(delta)
    normals, limits = piece["planes"]
    result["planes"] = (normals, limits + normals @ delta)
    return result


def rear_only_tips(pieces):
    return [
        prism(p["mesh"].vertices[:4, :2], CONFIG["rear_only_comparison_source_z_m"], p["name"], p["sign"])
        for p in pieces
        if p["name"] != "thrust"
    ]


def clip_polygon(vertices, normals, limits):
    polygon = np.asarray(vertices)
    for normal, limit in zip(normals, limits, strict=True):
        if not len(polygon):
            break
        signed = polygon @ normal - limit
        clipped = []
        for i in range(len(polygon)):
            j = (i + 1) % len(polygon)
            a, b, da, db = polygon[i], polygon[j], signed[i], signed[j]
            if da <= 0:
                clipped.append(a)
            if (da <= 0) != (db <= 0):
                clipped.append(a + da / (da - db) * (b - a))
        polygon = np.asarray(clipped)
    return polygon


def polygon_area(polygon):
    if len(polygon) < 3:
        return 0.0
    cross = np.cross(polygon[1:-1] - polygon[0], polygon[2:] - polygon[0])
    return float(np.linalg.norm(cross, axis=1).sum() / 2)


def surfaces_in_pieces(triangles, pieces):
    """Clip source triangles to tip volumes; no solid-body clearance verdict."""
    tri_min, tri_max = triangles.min(1), triangles.max(1)
    ids, points = set(), []
    area = 0.0
    names = {}
    for piece in pieces:
        lo, hi = piece["mesh"].bounds
        candidates = np.flatnonzero(((tri_max >= lo).all(1)) & ((tri_min <= hi).all(1)))
        for index in candidates:
            clipped = clip_polygon(triangles[index], *piece["planes"])
            patch = polygon_area(clipped)
            if patch > CONFIG["clipped_area_reporting_epsilon_m2"]:
                ids.add(int(index))
                area += patch
                names[piece["name"]] = names.get(piece["name"], 0.0) + patch
                points.extend(clipped.tolist())
    return {
        "unique_source_triangles_with_positive_clipped_area": len(ids),
        "summed_clipped_surface_area_m2": area,
        "clipped_surface_area_by_tip_part_m2": names,
        "clipped_points_bounds_m": [np.min(points, axis=0).tolist(), np.max(points, axis=0).tolist()]
        if points
        else None,
        "meaning": "Saved mesh surface inside/on closed trial-tip volumes; not loaded contact area.",
    }


def aperture_sdf(points, width, inputs):
    half = np.array([width, inputs["aperture_height_m"]]) / 2
    radius = inputs["aperture_corner_radius_m"]
    q = abs(points[:, :2]) - (half - radius)
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0) - radius


def header_in_inner_frame(header, bay_x):
    result = header.copy()
    source = np.asarray(header.vertices)
    result.vertices = np.column_stack((source[:, 0] - bay_x, source[:, 2], -source[:, 1] - 0.0311))
    return result


def aperture_measurements(pieces, aperture, inputs):
    vertices = np.vstack([piece["mesh"].vertices for piece in pieces])
    signed = aperture_sdf(vertices, aperture["width_m"], inputs)
    # Wall Y=0..3 mm in the header frame corresponds to source Z=-34.1..-31.1 mm.
    slab_normal = np.array([[0, 0, -1], [0, 0, 1]])
    slab_limit = np.array([0.0341, -0.0311])
    in_slab = []
    for piece in pieces:
        for triangle in piece["mesh"].triangles:
            in_slab.extend(clip_polygon(triangle, slab_normal, slab_limit).tolist())
    return {
        "max_signed_projected_distance_to_nominal_aperture_m": float(signed.max()),
        "projection_sign": "negative=inside_nominal_boundary, positive=outside; tips only, no tolerance stack",
        "tip_surface_points_in_display_wall_slab": len(in_slab),
        "max_signed_distance_in_display_wall_slab_m": (
            float(aperture_sdf(np.asarray(in_slab), aperture["width_m"], inputs).max()) if in_slab else None
        ),
    }


def thrust_face_observation(housing, pieces):
    centers = housing.triangles_center
    selected = (abs(centers[:, 2] + 0.0339) < 1e-8) & (housing.face_normals[:, 2] < -0.99)
    # Use XY planes only to project the trial pushing rectangle onto the flat CAD face.
    areas = []
    for piece in pieces:
        if piece["name"] != "thrust":
            continue
        normals, limits = piece["planes"]
        total = sum(polygon_area(clip_polygon(tri, normals[:4], limits[:4])) for tri in housing.triangles[selected])
        areas.append({"side": piece["sign"], "cad_flat_face_under_thrust_rectangle_m2": total})
    return {"source_z_m": -0.0339, "trial_rectangle_area_each_m2": 1.6e-6, "sides": areas}


def observe(inners, headers, inputs, pieces, profile):
    states = [("closed", 0.0, 0.0), ("open_2mm_each", 0.002, 0.0), ("withdraw_8mm_then_open", 0.002, 0.008)]
    bays = []
    for row in inputs["apertures"]:
        base_x, number = (-0.052, "2103340-1") if row["header"] == "P16" else (0.072, "2103346-2")
        header = header_in_inner_frame(mesh(headers[number]), row["center_x_m"] - base_x)
        records = []
        for name, opening, withdrawal in states:
            pose = [moved_piece(p, opening, withdrawal) for p in pieces]
            records.append(
                {
                    "state": name,
                    "opening_each_m": opening,
                    "axial_withdrawal_m": withdrawal,
                    "aperture": aperture_measurements(pose, row, inputs),
                    "outer_header_surface_in_tip_volumes": surfaces_in_pieces(header.triangles, pose),
                }
            )
        rear = rear_only_tips(pieces)
        records.append(
            {
                "state": "rear_only_closed_comparison",
                "opening_each_m": 0.0,
                "axial_withdrawal_m": 0.0,
                "aperture": aperture_measurements(rear, row, inputs),
                "outer_header_surface_in_tip_volumes": surfaces_in_pieces(header.triangles, rear),
            }
        )
        housing = mesh(inners[row["part_number"]])
        neighbor_gaps = []
        open_width = max(p["mesh"].bounds[1, 0] for p in pieces) + CONFIG["comparison_open_each_side_m"]
        for neighbor in inputs["apertures"]:
            if neighbor["id"] != row["id"]:
                other_half = abs(mesh(inners[neighbor["part_number"]]).bounds[:, 0]).max()
                gap = abs(neighbor["center_x_m"] - row["center_x_m"]) - open_width - other_half
                neighbor_gaps.append({"id": neighbor["id"], "x_interval_gap_m": float(gap)})
        bays.append(
            {
                "id": row["id"],
                "header": row["header"],
                "key": row["key"],
                "states": records,
                "flat_shoulder": thrust_face_observation(housing, pieces),
                "opened_tips_vs_other_inner_housings_x_interval_gaps": neighbor_gaps,
            }
        )
        print(
            row["id"],
            [
                (
                    r["state"],
                    r["outer_header_surface_in_tip_volumes"]["unique_source_triangles_with_positive_clipped_area"],
                )
                for r in records
            ],
            flush=True,
        )
    vertices = np.vstack([p["mesh"].vertices for p in pieces])
    return {
        "config": CONFIG,
        "source_inner_sha256": sha(INNER),
        "apertures_sha256": sha(APERTURES),
        "profile_source_xy_m": profile.tolist(),
        "closed_tip_bounds_m": [vertices.min(0).tolist(), vertices.max(0).tolist()],
        "bays": bays,
        "limits_ja": [
            "基本案の3つの静止位置と後端寄せ比較。開閉と後退の連続軌道を計算したものではない。",
            "8 mm後退は比較の表示位置。後退前の保持解除とハウジングの残留保持は別問題。",
            "保存された内外CADの表示位置を使用。実測の嵌合位置・ロック成立を示さない。",
            "指先だけの比較。ハンド本体・取付具・実電線・他の内部部品の占有範囲は含まない。",
            "三角形の体積内切出しは補助観測であり、ゼロ件でも固体の非干渉を保証しない。",
            "0.1 mmは図示用の逃げ。閉指令・圧縮量・把持力・公差・工程受入値ではない。",
            "後端寄せ案はつば押し面を含まず、軸方向の保持・挿入力の伝達を未解決のまま残す。",
        ],
    }


def save_meshes(pieces, output, name="trial_tip_meshes.json.gz"):
    rows = []
    for piece in pieces:
        solid = piece["mesh"]
        rows.append(
            {
                "part": piece["name"],
                "side": piece["sign"],
                "vertices": solid.vertices.tolist(),
                "faces": solid.faces.tolist(),
            }
        )
    path = output / name
    path.write_bytes(gzip.compress(json.dumps(rows, separators=(",", ":")).encode(), mtime=0))
    return sha(path)


def numerical_checks():
    """Check analytic triangle clipping examples, independently of the connector CAD."""
    solid = prism([[0, 0], [1, 0], [1, 1], [0, 1]], [-1, 1], "check", 1)
    examples = [
        ([[-1, 0, 0], [1, 0, 0], [0, 1, 0]], 0.5),
        ([[0, 0, 0], [0.5, 0, 0], [0, 0.5, 0]], 0.125),
        ([[2, 0, 0], [3, 0, 0], [2, 1, 0]], 0.0),
    ]
    values = [polygon_area(clip_polygon(np.asarray(t), *solid["planes"])) for t, _ in examples]
    assert np.allclose(values, [expected for _, expected in examples], rtol=0, atol=1e-14)
    return {"analytical_clipping_areas": values, "expected": [0.5, 0.125, 0.0]}


def main():
    output = ROOT / "output"
    output.mkdir(parents=True, exist_ok=True)
    inners, headers, inputs, provenance = load_sources()
    pieces, profile = build_tips(mesh(inners["2103245-1"]))
    result = observe(inners, headers, inputs, pieces, profile)
    result["numerical_checks"] = numerical_checks()
    result["provenance"] = provenance
    result["trial_tip_meshes_sha256"] = save_meshes(pieces, output)
    result["rear_only_tip_meshes_sha256"] = save_meshes(rear_only_tips(pieces), output, "rear_only_tip_meshes.json.gz")
    result["producing_script_sha256"] = sha(Path(__file__))
    (output / "tip_access_observations.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("TIP_ACCESS_OBSERVATIONS_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
