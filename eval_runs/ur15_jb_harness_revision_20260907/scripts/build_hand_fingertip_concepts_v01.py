# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Build static replaceable-fingertip review samples [m, rad].

Reuses the supplied 2F-85 visualization and gripper-only URDF transforms.
It does not run arm IK, contact dynamics, cable deformation or video rendering.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial.transform import Rotation

COLORS = {
    "hardware": [95, 107, 118, 255],
    "insert": [59, 142, 192, 255],
    "pad": [42, 75, 91, 255],
    "support": [238, 166, 70, 255],
    "target": [193, 201, 205, 255],
    "cable": [237, 120, 42, 255],
    "guide": [52, 183, 175, 75],
}
ROTATION = np.array([[0.0, 1, 0], [1.0, 0, 0], [0.0, 0, -1]])
SIDES = ("left_left", "left_right")


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frame(element):
    result = np.eye(4)
    if element is not None:
        result[:3, 3] = np.fromstring(element.get("xyz", "0 0 0"), sep=" ")
        angles = np.fromstring(element.get("rpy", "0 0 0"), sep=" ")
        result[:3, :3] = Rotation.from_euler("xyz", angles).as_matrix()
    return result


def _gripper_fk(urdf, angle):
    frames = {"left_gripper_base": np.eye(4)}
    values = {}
    for joint in urdf.findall("joint"):
        parent = joint.find("parent").get("link")
        if parent not in frames:
            continue
        transform = _frame(joint.find("origin"))
        value = 0.0
        if joint.get("type") == "revolute":
            mimic = joint.find("mimic")
            if mimic is None:
                value = angle
            else:
                value = values[mimic.get("joint")] * float(mimic.get("multiplier", "1"))
                value += float(mimic.get("offset", "0"))
            axis = np.fromstring(joint.find("axis").get("xyz"), sep=" ")
            turn = np.eye(4)
            turn[:3, :3] = Rotation.from_rotvec(axis * value).as_matrix()
            transform = transform @ turn
        values[joint.get("name")] = value
        frames[joint.find("child").get("link")] = frames[parent] @ transform
    return frames


def _opening_angle(urdf, config, back_x):
    point = [0.0, config["pad_back_y_m"], config["pad_center_z_m"], 1.0]

    def opening(q):
        frame = _gripper_fk(urdf, q)["left_right_inner_finger"]
        return float((frame @ point)[1])

    if not opening(0.8) <= back_x <= opening(0.0):
        raise ValueError(f"Requested static insert back plane is outside source joint range: {back_x}")
    lo, hi = 0.0, 0.8
    for _ in range(60):
        mid = (lo + hi) / 2
        if opening(mid) > back_x:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _mesh(vertices, faces, color):
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    mesh.fix_normals()
    mesh.visual.vertex_colors = COLORS[color]
    return mesh


def _profile_prism(boundary, axis, low, high, color):
    # Tessellate strips along the curved recess; a fan would fill its concavity.
    curve, back_x = boundary[:-2], boundary[-1][0]
    count = len(curve)
    profile = [*curve, *((back_x, b) for _, b in curve)]
    vertices = []
    for height in (low, high):
        for a, b in profile:
            vertices.append((a, b, height) if axis == "Z" else (a, height, b))
    faces = []
    layer = count * 2
    for index in range(count - 1):
        for offset in (0, layer):
            a, b = offset + index, offset + count + index
            faces.extend(((a, b, b + 1), (a, b + 1, a + 1)))
    perimeter = [*range(count), *range(count * 2 - 1, count - 1, -1)]
    for index, a in enumerate(perimeter):
        b = perimeter[(index + 1) % len(perimeter)]
        faces.extend(((a, b, layer + b), (a, layer + b, layer + a)))
    return _mesh(vertices, faces, color)


def _box(size, center, color):
    mesh = trimesh.creation.box(extents=size)
    mesh.apply_translation(center)
    mesh.visual.vertex_colors = COLORS[color]
    return mesh


def _cylinder(radius, height, center, color, along_y=False):
    mesh = trimesh.creation.cylinder(radius, height, sections=64)
    if along_y:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    mesh.apply_translation(center)
    mesh.visual.vertex_colors = COLORS[color]
    return mesh


def _a_insert(config):
    c = config["A"]
    radius, contact = c["pocket_radius_m"], c["target_radius_m"]
    y = np.linspace(-c["contact_width_m"] / 2, c["contact_width_m"] / 2, 33)
    x = np.sqrt(radius * radius - y * y) - (radius - contact)
    boundary = list(zip(x, y, strict=True))
    boundary.extend(((c["back_plane_x_m"], y[-1]), (c["back_plane_x_m"], y[0])))
    height = c["contact_height_m"] / 2
    pad = _profile_prism(boundary, "Z", -height, height, "pad")
    lip_x = x - c["support_lip_depth_m"]
    lip_boundary = list(zip(lip_x, y, strict=True))
    lip_boundary.extend(((c["back_plane_x_m"], y[-1]), (c["back_plane_x_m"], y[0])))
    lip = _profile_prism(lip_boundary, "Z", -height - c["support_lip_thickness_m"], -height, "support")
    result = {"contour_contact": pad}
    if c["include_lower_lip"]:
        result["shoulder_support"] = lip
    return result


def _b_insert(config):
    c = config["B"]
    radius, wire_radius = c["groove_radius_m"], c["target_radius_m"]
    angle = np.linspace(-math.radians(c["groove_half_angle_deg"]), math.radians(c["groove_half_angle_deg"]), 41)
    x = radius * np.cos(angle) - (radius - wire_radius)
    z = radius * np.sin(angle) + c["contact_center_z_m"]
    boundary = list(zip(x, z, strict=True))
    boundary.extend(((c["back_plane_x_m"], z[-1]), (c["back_plane_x_m"], z[0])))
    return {
        "rounded_groove": _profile_prism(boundary, "Y", -c["contact_length_m"] / 2, c["contact_length_m"] / 2, "pad")
    }


def _inserts(config, kind):
    result = _a_insert(config) if kind == "A" else _b_insert(config)
    thickness = config["backplate_thickness_m"]
    result["insert_carrier"] = _box(
        (thickness, config["backplate_width_m"], config["backplate_height_m"]),
        (config[kind]["back_plane_x_m"] - thickness / 2, 0, 0),
        "insert",
    )
    return result


def _targets(config, kind):
    c = config[kind]
    if kind == "B":
        return {
            "sample_cable": _cylinder(
                c["target_radius_m"], c["target_length_m"], (0, 0, c["contact_center_z_m"]), "cable", True
            )
        }
    result = {
        "sample_body": _cylinder(
            c["target_radius_m"],
            c["target_height_m"],
            (0, 0, c["target_bottom_z_m"] + c["target_height_m"] / 2),
            "target",
        )
    }
    for sign in (-1, 1):
        y = sign * c["tool_center_y_m"]
        result[f"sample_mount_ear_{sign}"] = _box(
            (0.022, 0.031, 0.004), (0, y - sign * 0.005, c["target_bottom_z_m"] + 0.002), "target"
        )
        result[f"tool_envelope_{sign}"] = _cylinder(
            c["tool_envelope_radius_m"], c["tool_envelope_height_m"], (0, y, c["tool_envelope_height_m"] / 2), "guide"
        )
    return result


def _reuse_meshes(urdf, asset_root, frames):
    meshes, used = {}, set()
    for link in urdf.findall("link"):
        name = link.get("name")
        if name not in frames or name.endswith("_pad"):
            continue
        for index, visual in enumerate(link.findall("visual")):
            mesh_node = visual.find("geometry/mesh")
            if mesh_node is None:
                continue
            path = asset_root / "meshes/visual" / Path(mesh_node.get("filename")).name
            used.add(path)
            scene = trimesh.load(path, force="scene", process=False)
            mesh = scene.to_geometry()
            mesh.apply_scale(0.001)
            mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh, vertex_colors=COLORS["hardware"])
            meshes[f"hardware_{name}_{index}"] = (mesh, name, _frame(visual.find("origin")))
    return meshes, used


def _world_root(urdf, config, angle):
    frame = _gripper_fk(urdf, angle)["left_right_inner_finger"]
    point = frame @ [0.0, config["pad_back_y_m"], config["pad_center_z_m"], 1.0]
    root = np.eye(4)
    root[:3, :3] = ROTATION
    root[2, 3] = point[2]
    return root


def _serialize(mesh, category):
    return {
        "vertices": np.asarray(mesh.vertices).round(9).tolist(),
        "faces": mesh.faces.tolist(),
        "color": mesh.visual.vertex_colors[0].tolist(),
        "category": category,
    }


def _candidate(config, kind, urdf, hardware):
    c = config[kind]
    closed = _opening_angle(urdf, config, c["back_plane_x_m"])
    opened = _opening_angle(urdf, config, c["back_plane_x_m"] + config["release_extra_half_opening_m"])
    root = _world_root(urdf, config, closed)
    near_frames = _gripper_fk(urdf, closed)
    locals_by_name = {}
    for side, sign in zip(SIDES, (-1, 1), strict=True):
        frame = root @ near_frames[f"{side}_inner_finger"]
        for name, mesh in _inserts(config, kind).items():
            mesh = mesh.copy()
            if sign == -1:
                mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [0, 0, 1]))
            mesh.apply_transform(np.linalg.inv(frame))
            locals_by_name[f"{side}_{name}"] = (mesh, f"{side}_inner_finger")
    objects = {name: _serialize(mesh, "hardware") for name, (mesh, _, _) in hardware.items()}
    objects.update({name: _serialize(mesh, "insert") for name, (mesh, _) in locals_by_name.items()})
    targets = _targets(config, kind)
    objects.update(
        {name: _serialize(mesh, "guide" if name.startswith("tool_") else "target") for name, mesh in targets.items()}
    )
    states = {}
    for name, angle, lift in (
        ("near", closed, 0),
        ("early", closed + 0.05 * (opened - closed), 0),
        ("open", opened, 0),
        ("clear", opened, config["clearance_comparison_lift_m"]),
    ):
        frames = _gripper_fk(urdf, angle)
        moved_root = root.copy()
        moved_root[2, 3] += lift
        transforms = {n: (moved_root @ frames[link] @ origin).tolist() for n, (_, link, origin) in hardware.items()}
        transforms.update({n: (moved_root @ frames[link]).tolist() for n, (_, link) in locals_by_name.items()})
        transforms.update({n: np.eye(4).tolist() for n in targets})
        states[name] = {"joint_q_rad": angle, "root_lift_m": lift, "transforms": transforms}
    return {
        "objects": objects,
        "states": states,
        "note": "Four static comparison poses, not a continuous or collision-approved trajectory.",
    }


def _export_glb(candidate, destination):
    scene = trimesh.Scene()
    for name, obj in candidate["objects"].items():
        if obj["category"] == "guide":
            continue
        mesh = trimesh.Trimesh(obj["vertices"], obj["faces"], process=False)
        mesh.visual.vertex_colors = obj["color"]
        scene.add_geometry(
            mesh, node_name=name, geom_name=name, transform=candidate["states"]["near"]["transforms"][name]
        )
    scene.export(destination, file_type="glb")
    restored = trimesh.load(destination, force="scene", process=False)
    return {
        "file": destination.name,
        "sha256": _digest(destination),
        "mesh_count": len(scene.geometry),
        "readback_mesh_count": len(restored.geometry),
        "bounds_m": scene.bounds.tolist(),
        "readback_bounds_max_difference_m": float(np.max(np.abs(scene.bounds - restored.bounds))),
    }


def _opening_observations(candidates, config):
    observations = {}
    for kind, candidate in candidates.items():
        name = "left_right_insert_carrier"
        center = np.asarray(candidate["objects"][name]["vertices"]).mean(axis=0)
        rows = {}
        for state, snapshot in candidate["states"].items():
            transform = np.asarray(snapshot["transforms"][name])
            world = transform[:3, :3] @ center + transform[:3, 3]
            rows[state] = {"carrier_center_world_m": world.tolist()}
        observations[kind] = rows
    candidate = candidates["A_LIP"]
    name = "left_right_shoulder_support"
    vertices = np.asarray(candidate["objects"][name]["vertices"])
    top = vertices[len(vertices) // 2 :]
    for state, snapshot in candidate["states"].items():
        transform = np.asarray(snapshot["transforms"][name])
        world = top @ transform[:3, :3].T + transform[:3, 3]
        inside = np.linalg.norm(world[:, :2], axis=1) < config["A"]["target_radius_m"]
        offsets = world[inside, 2] - config["A"]["target_bottom_z_m"]
        observations["A_LIP"][state]["lip_upper_vertices_inside_sample_radius"] = int(inside.sum())
        observations["A_LIP"][state]["upper_z_minus_sample_bottom_range_m"] = (
            [float(offsets.min()), float(offsets.max())] if len(offsets) else None
        )
    return observations


def build(config_path: Path, asset_root: Path, urdf_path: Path, output_directory: Path) -> dict:
    """Create standalone static fingertip samples and source records [m]."""
    output_directory.mkdir(parents=True, exist_ok=False)
    config = json.loads(config_path.read_text())
    urdf = ET.parse(urdf_path).getroot()
    hardware, used = _reuse_meshes(urdf, asset_root, _gripper_fk(urdf, 0))
    source_paths = sorted({*used, config_path, urdf_path})
    before = {str(path): _digest(path) for path in source_paths}
    candidates = {kind: _candidate(config, kind, urdf, hardware) for kind in ("A", "B")}
    lip_config = {**config, "A": {**config["A"], "include_lower_lip": True}}
    candidates["A_LIP"] = _candidate(lip_config, "A", urdf, hardware)
    payload = {"config": config, "candidates": candidates}
    (output_directory / "hand_fingertip_meshes_v01.json").write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    template = Path(__file__).with_name("hand_fingertip_viewer_v01.html").read_text()
    (output_directory / "指先3D比較_v01.html").write_text(
        template.replace("__MESH_PAYLOAD__", json.dumps(payload, separators=(",", ":")))
    )
    exports = [
        _export_glb(candidates[kind], output_directory / f"hand_{kind}_2F_fingertips_v01.glb") for kind in candidates
    ]
    unchanged = before == {str(path): _digest(path) for path in source_paths}
    if not unchanged:
        raise RuntimeError("An input changed during the build")
    report = {
        "kind": "auxiliary_static_geometry_observation",
        "source_sha256": before,
        "input_bytes_unchanged": unchanged,
        "reused_hardware_meshes_per_hand": len(hardware),
        "exports": exports,
        "joint_q_rad": {k: {s: v["joint_q_rad"] for s, v in c["states"].items()} for k, c in candidates.items()},
        "static_opening_observations": _opening_observations(candidates, config),
        "not_evaluated": [
            "grasp_force",
            "cable_compression",
            "S_shape_formation",
            "continuous_collision",
            "actual_part_fit",
            "mounting_screws",
            "arm_motion",
            "on_hand_camera_clearance",
        ],
        "physical_acceptance_verdict": None,
    }
    (output_directory / "hand_fingertip_geometry_observations_v01.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    """Parse CLI paths and create the new review directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--asset_root", type=Path, required=True)
    parser.add_argument("--urdf", type=Path, required=True)
    parser.add_argument("--output_directory", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.config, args.asset_root, args.urdf, args.output_directory)
    print(json.dumps(report, indent=2))
    print("HAND_FINGERTIP_STATIC_BUILD_DONE")


if __name__ == "__main__":
    main()
