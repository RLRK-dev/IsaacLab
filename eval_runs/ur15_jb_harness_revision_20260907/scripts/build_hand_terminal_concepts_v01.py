# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Compare two terminal fingertip concepts with reused gripper geometry [m, rad].

This isolated static builder uses a reference lug, not an adopted Ampere part.
It imports the previous static builder's FK, mesh loading and export helpers.
No production native, arm IK or wire deformation is loaded.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import build_hand_fingertip_concepts_v01 as base
import numpy as np
import trimesh


def _lug(source, config):
    raw = json.loads(source.read_text())
    if base._digest(source) != config["target"]["json_sha256"]:
        raise ValueError("Reference lug JSON does not match the recorded input")
    if raw["source_sha256"] != config["target"]["step_sha256"] or raw["unit"] != "mm":
        raise ValueError("Reference lug source or units changed")
    v = np.asarray(raw["vertices"], dtype=float)
    # Proper cyclic rotation, mm-to-m conversion and rigid translation only.
    world = np.column_stack((v[:, 2], v[:, 0] + 37, v[:, 1] + 8)) / 1000
    world[:, 2] += config["target"]["seat_z_m"]
    mesh = trimesh.Trimesh(world, raw["faces"], process=False)
    mesh.visual.vertex_colors = base.COLORS["target"]
    return mesh


def _slice_extent(mesh, z, y_low, y_high):
    lines = trimesh.intersections.mesh_plane(mesh, [0, 0, 1], [0, 0, z])
    points = []
    for first, second in lines:
        for p in (first, second):
            if y_low <= p[1] <= y_high:
                points.append(p)
        if second[1] == first[1]:
            continue
        for y in (y_low, y_high):
            t = (y - first[1]) / (second[1] - first[1])
            if 0 <= t <= 1:
                points.append(first + t * (second - first))
    if not points:
        raise ValueError(f"No lug surface in the specified contact band at Z={z}")
    return float(np.abs(np.asarray(points)[:, 0]).max())


def _edge_profile(lug, config):
    c = config["insert"]
    low, high = np.array(c["edge_z_above_seat_range_m"]) + config["target"]["seat_z_m"]
    rows = []
    for z in np.linspace(low, high, c["edge_profile_samples"]):
        x = _slice_extent(lug, z, *c["edge_y_range_m"])
        rows.append((x + c["edge_nominal_clearance_m"], z))
    return rows


def _box_union(meshes):
    # Exact axis-aligned box boundary, not a sampled voxel approximation.
    # Round arithmetic noise to 1 pm so intended shared planes use one index.
    bounds = np.round([mesh.bounds for mesh in meshes], 12)
    axes = [np.unique(bounds[:, :, axis]) for axis in range(3)]
    shape = tuple(len(axis) - 1 for axis in axes)
    occupied = np.zeros(shape, dtype=bool)
    for index in np.ndindex(shape):
        center = np.array([(axes[a][i] + axes[a][i + 1]) / 2 for a, i in enumerate(index)])
        occupied[index] = np.any(np.all(center > bounds[:, 0], axis=1) & np.all(center < bounds[:, 1], axis=1))
    vertices, faces, lookup = [], [], {}
    for index in np.ndindex(shape):
        if not occupied[index]:
            continue
        for axis, step in itertools.product(range(3), (-1, 1)):
            neighbor = list(index)
            neighbor[axis] += step
            if 0 <= neighbor[axis] < shape[axis] and occupied[tuple(neighbor)]:
                continue
            others = [a for a in range(3) if a != axis]
            face = []
            for u, v in ((0, 0), (1, 0), (1, 1), (0, 1)):
                corner = list(index)
                corner[axis] += int(step > 0)
                corner[others[0]] += u
                corner[others[1]] += v
                key = tuple(corner)
                if key not in lookup:
                    lookup[key] = len(vertices)
                    vertices.append([axes[a][i] for a, i in enumerate(corner)])
                face.append(lookup[key])
            faces.extend(((face[0], face[1], face[2]), (face[0], face[2], face[3])))
    result = base._mesh(vertices, faces, "insert")
    if not result.is_watertight:
        raise ValueError("Carrier box union is not closed")
    return result


def _inserts(config, profile, with_guide):
    c, m = config["insert"], config["mechanism"]
    back = m["back_plane_x_m"]
    boundary = [*profile, (back - 0.0015, profile[-1][1]), (back - 0.0015, profile[0][1])]
    front_bottom, front_top = profile[0][1], -0.003
    result = {
        "edge_contour": base._profile_prism(boundary, "Y", *c["edge_y_range_m"], "pad"),
        "carrier": base._box(m["carrier_dimensions_m"], (back - 0.001, m["root_y_m"], 0), "insert"),
        "front_bridge": base._box(
            (0.0015, 0.008, front_top - front_bottom),
            (back - 0.00075, 0.008, (front_bottom + front_top) / 2),
            "insert",
        ),
        "side_rail": base._box((0.004, 0.032, 0.006), (back - 0.002, 0.019, -0.005), "insert"),
    }
    if with_guide:
        r = c["rear_guide_radius_m"]
        angle = np.linspace(
            -math.radians(c["rear_guide_half_angle_deg"]), math.radians(c["rear_guide_half_angle_deg"]), 41
        )
        z0 = config["target"]["seat_z_m"] + config["target"]["raw_barrel_axis_above_seat_m"]
        curve = list(zip(r * np.cos(angle), z0 + r * np.sin(angle), strict=True))
        boundary = [*curve, (back, curve[-1][1]), (back, curve[0][1])]
        result["wire_clearance_guide"] = base._profile_prism(boundary, "Y", *c["rear_guide_y_range_m"], "support")
        result["rear_bridge"] = base._box((0.0036, 0.026, 0.006), (back - 0.002, 0.043, -0.005), "insert")
    carrier_names = [name for name in result if name in ("carrier", "front_bridge", "side_rail", "rear_bridge")]
    carrier = _box_union([result.pop(name) for name in carrier_names])
    result["carrier"] = carrier
    return result


def _annulus(inner, outer, low, high, y_axis, center, color):
    mesh = trimesh.creation.annulus(r_min=inner, r_max=outer, height=high - low, sections=96)
    if y_axis:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    offset = np.array(center, dtype=float)
    offset[1 if y_axis else 2] += (low + high) / 2
    mesh.apply_translation(offset)
    mesh.visual.vertex_colors = base.COLORS[color]
    return mesh


def _targets(lug, config):
    c, e = config["target"], config["illustrative_surroundings"]
    z0 = c["seat_z_m"] + c["raw_barrel_axis_above_seat_m"]
    result = {"reference_lug_6R6_uncrimped": lug}
    result["comparison_wire"] = base._cylinder(
        c["wire_radius_m"],
        c["wire_visible_length_m"],
        (0, c["hole_center_to_barrel_end_m"] + c["wire_visible_length_m"] / 2, z0),
        "cable",
        True,
    )
    result["illustrative_sleeve"] = _annulus(
        c["wire_radius_m"], c["sleeve_outer_radius_m"], *c["sleeve_y_range_m"], True, (0, 0, z0), "hardware"
    )
    result["illustrative_busbar_coupon"] = _annulus(
        e["coupon_hole_radius_m"],
        e["coupon_radius_m"],
        c["seat_z_m"] - e["coupon_thickness_m"],
        c["seat_z_m"],
        False,
        (0, 0, 0),
        "target",
    )
    lo, hi = np.array(e["tool_z_above_seat_range_m"]) + c["seat_z_m"]
    result["tool_access_guide"] = base._cylinder(e["tool_radius_m"], hi - lo, (0, 0, (lo + hi) / 2), "guide")
    return result


def _candidate(config, urdf, hardware, targets, inserts):
    c = config["mechanism"]
    near = base._opening_angle(urdf, c, c["back_plane_x_m"])
    opened = base._opening_angle(urdf, c, c["back_plane_x_m"] + c["release_extra_half_opening_m"])
    root = base._world_root(urdf, c, near)
    root[1, 3] += c["root_y_m"]
    frames = base._gripper_fk(urdf, near)
    local = {}
    for side, sign in zip(base.SIDES, (-1, 1), strict=True):
        link = f"{side}_inner_finger"
        for name, original in inserts.items():
            mesh = original.copy()
            # Reflect only the closing axis. Both guides stay behind the lug.
            mesh.apply_transform(np.diag([sign, 1, 1, 1]))
            mesh.apply_transform(np.linalg.inv(root @ frames[link]))
            local[f"{side}_{name}"] = mesh, link
    objects = {name: base._serialize(mesh, "hardware") for name, (mesh, _, _) in hardware.items()}
    objects.update({name: base._serialize(mesh, "insert") for name, (mesh, _) in local.items()})
    objects.update(
        {
            name: base._serialize(mesh, "guide" if name == "tool_access_guide" else "target")
            for name, mesh in targets.items()
        }
    )
    states = {}
    for name, angle, lift in (
        ("near", near, 0),
        ("early", near + 0.05 * (opened - near), 0),
        ("open", opened, 0),
        ("clear", opened, c["clearance_comparison_lift_m"]),
    ):
        frames = base._gripper_fk(urdf, angle)
        moved = root.copy()
        moved[2, 3] += lift
        transforms = {n: (moved @ frames[link] @ origin).tolist() for n, (_, link, origin) in hardware.items()}
        transforms.update({n: (moved @ frames[link]).tolist() for n, (_, link) in local.items()})
        transforms.update({n: np.eye(4).tolist() for n in targets})
        states[name] = {"joint_q_rad": angle, "root_lift_m": lift, "transforms": transforms}
    return {"objects": objects, "states": states, "note": "Static comparison only; target held fixed by the viewer."}


def _projected_radius_min(triangles):
    a, b, c = (triangles[:, i, :2] for i in range(3))
    edges = ((a, b), (b, c), (c, a))
    distances, signs = [], []
    for first, second in edges:
        direction = second - first
        norm2 = (direction * direction).sum(axis=1)
        fraction = np.divide(-(first * direction).sum(axis=1), norm2, out=np.zeros_like(norm2), where=norm2 > 0)
        point = first + np.clip(fraction, 0, 1)[:, None] * direction
        distances.append(np.linalg.norm(point, axis=1))
        signs.append(first[:, 0] * second[:, 1] - first[:, 1] * second[:, 0])
    result = np.min(distances, axis=0)
    signs = np.asarray(signs)
    area2 = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    inside = ((signs >= 0).all(axis=0) | (signs <= 0).all(axis=0)) & (np.abs(area2) > 1e-18)
    result[inside] = 0
    return float(result.min())


def _observations(candidate, config):
    rows = {}
    e = config["illustrative_surroundings"]
    seat = config["target"]["seat_z_m"]
    low, high = np.asarray(e["tool_z_above_seat_range_m"]) + seat
    for state, snapshot in candidate["states"].items():
        points, tool_bounds = [], []
        center = None
        for name, obj in candidate["objects"].items():
            if obj["category"] not in ("insert", "hardware"):
                continue
            m = np.asarray(snapshot["transforms"][name])
            world = np.asarray(obj["vertices"]) @ m[:3, :3].T + m[:3, 3]
            if obj["category"] == "insert":
                points.append(world)
            if name == "left_right_carrier":
                center = world.mean(axis=0)
            tri = world[np.asarray(obj["faces"])]
            selected = tri[(tri[:, :, 2].min(axis=1) <= high) & (tri[:, :, 2].max(axis=1) >= low)]
            if len(selected):
                tool_bounds.append((_projected_radius_min(selected) - e["tool_radius_m"], name))
        minimum, nearest = min(tool_bounds)
        rows[state] = {
            "right_carrier_vertex_mean_m": center.tolist(),
            "all_insert_vertices_min_z_minus_coupon_top_m": float(np.vstack(points)[:, 2].min() - seat),
            "tool_radius_projected_lower_bound_m": minimum,
            "tool_bound_object": nearest,
        }
    return rows


def build(config_path: Path, asset_root: Path, urdf_path: Path, lug_path: Path, output: Path) -> dict:
    """Create a fresh static review package using SI geometry [m]."""
    output.mkdir(parents=True, exist_ok=False)
    config = json.loads(config_path.read_text())
    urdf = ET.parse(urdf_path).getroot()
    hardware, used = base._reuse_meshes(urdf, asset_root, base._gripper_fk(urdf, 0))
    template_path = Path(__file__).with_name("hand_terminal_viewer_v01.html")
    sources = sorted({*used, config_path, urdf_path, lug_path, Path(base.__file__), Path(__file__), template_path})
    before = {str(p): base._digest(p) for p in sources}
    lug = _lug(lug_path, config)
    profile = _edge_profile(lug, config)
    targets = _targets(lug, config)
    candidates = {
        name: _candidate(config, urdf, hardware, targets, _inserts(config, profile, guide))
        for name, guide in (("EDGE", False), ("GUIDE", True))
    }
    payload = {"config": config, "candidates": candidates}
    packed = json.dumps(payload, separators=(",", ":"))
    (output / "hand_terminal_meshes_v01.json").write_text(packed + "\n")
    template = template_path.read_text()
    (output / "端末指先3D比較_v01.html").write_text(template.replace("__MESH_PAYLOAD__", packed))
    exports = [base._export_glb(c, output / f"hand_terminal_{name}_v01.glb") for name, c in candidates.items()]
    unchanged = before == {str(p): base._digest(p) for p in sources}
    if not unchanged:
        raise RuntimeError("A read-only input changed during the build")
    report = {
        "scope": "auxiliary static geometry; no physical acceptance verdict",
        "source_sha256": before,
        "inputs_unchanged": unchanged,
        "reference_lug_vertices": len(lug.vertices),
        "reference_lug_faces": len(lug.faces),
        "lug_source_faces_unchanged": np.array_equal(lug.faces, json.loads(lug_path.read_text())["faces"]),
        "lug_axes": "X=raw_Z; Y=raw_X+37 mm; Z=raw_Y+8 mm+seat_Z; proper rigid rotation and SI conversion",
        "lug_bounds_m": lug.bounds.tolist(),
        "reused_hardware_meshes_per_hand": len(hardware),
        "edge_profile_x_z_m": profile,
        "static_poses": {name: _observations(c, config) for name, c in candidates.items()},
        "measurement_basis": {
            "coupon": "minimum of ALL insert vertices relative to coupon top; not a full scene collision test",
            "tool": "XY projection of triangles overlapping tool Z band; conservative bound, not exact 3D distance",
            "poses": "four discrete fixed-object comparisons; no swept volume, release dynamics or time law",
            "carrier": "mean of carrier mesh vertices, not a center of mass; use differences between poses",
            "blue_carrier": "axis-aligned box union, boundary planes rounded to 1 pm to remove arithmetic noise",
        },
        "guide_nominal_radial_gap_m": config["insert"]["rear_guide_radius_m"] - config["target"]["wire_radius_m"],
        "exports": exports,
        "not_evaluated": config["unresolved"],
        "physical_acceptance_verdict": None,
    }
    (output / "hand_terminal_geometry_observations_v01.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    """Parse local source paths and build the two static comparisons."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "asset_root", "urdf", "lug", "output_directory"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.config, args.asset_root, args.urdf, args.lug, args.output_directory)
    print(json.dumps({"static_poses": report["static_poses"], "exports": report["exports"]}, indent=2))
    print("HAND_TERMINAL_STATIC_BUILD_DONE", flush=True)


if __name__ == "__main__":
    main()
