#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Attach the supplied camera geometry to the existing animated tool frames."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "inputs/UR15_monocular_camera_v01/output"
BASE = ROOT / "op010_base"


def write_json(path: Path, value: dict | list) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def read_camera_geometry() -> tuple[dict, dict]:
    """Read final GLB camera primitives in their original tool0 frame [m]."""
    blob = (INPUT / "ur15-dual-arm-cell-monocular-v01.glb").read_bytes()
    length = struct.unpack_from("<I", blob, 12)[0]
    document = json.loads(blob[20 : 20 + length])
    binary = memoryview(blob)[28 + length :]

    def array(index: int) -> np.ndarray:
        accessor = document["accessors"][index]
        view = document["bufferViews"][accessor["bufferView"]]
        dtype = {5126: "<f4", 5125: "<u4", 5123: "<u2"}[accessor["componentType"]]
        width = {"SCALAR": 1, "VEC3": 3}[accessor["type"]]
        assert "byteStride" not in view
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        value = np.frombuffer(binary, dtype=dtype, count=accessor["count"] * width, offset=offset).copy()
        return value.reshape(-1, width) if width > 1 else value

    meshes = {}
    manifest = {}
    for node in document["nodes"]:
        name = node.get("name", "")
        if not any(name.startswith(side + "_mono_") for side in ("left", "right")) or "mesh" not in node:
            continue
        assert not any(key in node for key in ("matrix", "translation", "rotation", "scale"))
        mesh = document["meshes"][node["mesh"]]
        assert len(mesh["primitives"]) == 1
        primitive = mesh["primitives"][0]
        vertices = array(primitive["attributes"]["POSITION"])
        faces = array(primitive["indices"]).reshape(-1, 3)
        normals = array(primitive["attributes"]["NORMAL"])
        material = document["materials"][primitive["material"]]["pbrMetallicRoughness"]
        meshes[name] = (vertices, faces, normals, material)
        manifest[name] = {
            "vertices": len(vertices),
            "triangles": len(faces),
            "vertex_sha256": hashlib.sha256(vertices.tobytes()).hexdigest(),
            "face_sha256": hashlib.sha256(faces.tobytes()).hexdigest(),
            "bounds_m": [vertices.min(0).tolist(), vertices.max(0).tolist()],
            "material": material,
        }
    assert len(meshes) == 10
    return meshes, manifest


def original_signature(names: list[str]) -> str:
    """Hash original geometry, materials, parenting and animation without new objects."""
    digest = hashlib.sha256()
    mesh_seen, material_seen = set(), set()
    for name in sorted(names):
        obj = bpy.data.objects[name]
        digest.update(name.encode())
        digest.update((obj.parent.name if obj.parent else "").encode())
        digest.update(np.asarray(obj.matrix_basis, dtype="<f4").tobytes())
        digest.update(np.asarray(obj.matrix_parent_inverse, dtype="<f4").tobytes())
        digest.update(str(sorted(obj.items())).encode())
        if obj.animation_data and obj.animation_data.action:
            for curve in obj.animation_data.action.fcurves:
                digest.update(f"{curve.data_path}:{curve.array_index}".encode())
                coordinates = np.empty(len(curve.keyframe_points) * 2, dtype=np.float32)
                curve.keyframe_points.foreach_get("co", coordinates)
                digest.update(coordinates.tobytes())
                digest.update(str([point.interpolation for point in curve.keyframe_points]).encode())
        if obj.type != "MESH":
            continue
        if obj.data.name not in mesh_seen:
            mesh_seen.add(obj.data.name)
            vertices = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
            obj.data.vertices.foreach_get("co", vertices)
            indices = np.empty(len(obj.data.loops), dtype=np.int32)
            obj.data.loops.foreach_get("vertex_index", indices)
            digest.update(vertices.tobytes())
            digest.update(indices.tobytes())
        digest.update(str([slot.material.name for slot in obj.material_slots]).encode())
        for slot in obj.material_slots:
            material = slot.material
            if material.name in material_seen:
                continue
            material_seen.add(material.name)
            if material.use_nodes:
                for node in material.node_tree.nodes:
                    digest.update(node.name.encode())
                    for socket in node.inputs:
                        if hasattr(socket, "default_value"):
                            value = socket.default_value
                            digest.update(str(tuple(value) if hasattr(value, "__len__") else value).encode())
                digest.update(
                    str([(link.from_node.name, link.to_node.name) for link in material.node_tree.links]).encode()
                )
    return digest.hexdigest()


def make_camera(name: str, collection: bpy.types.Collection, pose: Matrix, parent=None) -> bpy.types.Object:
    """Create a pinhole view with pose in its parent frame [m]."""
    camera_data = bpy.data.cameras.new(name)
    camera_data.sensor_fit = "HORIZONTAL"
    camera_data.sensor_width = 36
    camera_data.lens = 36 / (2 * math.tan(math.radians(75) / 2))
    camera_data.clip_start = 0.0002
    camera_data.clip_end = 100
    camera_data.dof.use_dof = False
    obj = bpy.data.objects.new(name, camera_data)
    collection.objects.link(obj)
    obj.parent = parent
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_basis = pose
    return obj


def main() -> None:
    scene = bpy.context.scene
    assert Path(bpy.data.filepath).name == "UR15_OP010_revision.blend"
    scene.frame_set(1)
    old_names = list(bpy.data.objects.keys())
    motion_path = ROOT / "data/motion_with_camera_clearance.npz"
    retarget_applied = motion_path.exists()
    motion = np.load(motion_path if retarget_applied else BASE / "data/motion.npz")["poses"]
    if retarget_applied:
        sys.path.insert(0, str(BASE / "scripts"))
        from build_op010_blender import add_action

        delta_path = ROOT / "audit/op010_camera_clearance_delta.json"
        if not delta_path.exists():
            delta_path = ROOT / "audit/prior_camera_v01/op010_camera_clearance_delta.json"
        delta = json.loads(delta_path.read_text())
        for node_id in delta["changed_source_node_ids"]:
            obj = bpy.data.objects[f"source_{node_id:04d}"]
            obj.animation_data_clear()
            add_action(obj, motion[:, node_id], np.arange(1, 789, dtype=np.float32))
        scene.frame_set(1)
        bpy.context.view_layer.update()
    before = original_signature(old_names)
    config = json.loads((INPUT / "camera_config.json").read_text())
    source = json.loads((BASE / "data/scene.json").read_text())
    geometry, geometry_manifest = read_camera_geometry()
    collection = bpy.data.collections.new("Onhand_monocular_v01")
    scene.collection.children.link(collection)
    mesh_data = {}
    for name, (vertices, faces, normals, material_spec) in geometry.items():
        data = bpy.data.meshes.new(name)
        data.from_pydata(vertices.tolist(), [], faces.tolist())
        data.update()
        for face in data.polygons:
            face.use_smooth = True
        data.normals_split_custom_set_from_vertices(normals.tolist())
        material = bpy.data.materials.new(name + "_provided_v01")
        material.use_nodes = True
        shader = material.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = material_spec["baseColorFactor"]
        shader.inputs["Metallic"].default_value = material_spec["metallicFactor"]
        shader.inputs["Roughness"].default_value = material_spec["roughnessFactor"]
        data.materials.append(material)
        mesh_data[name] = data
    anchors = {}
    for node in source["nodes"]:
        if node["name"] == "2f85:gripper_base":
            anchors.setdefault(node["equipment"], []).append(node["id"])
    assert len(anchors) == 19
    records = []
    for equipment, node_ids in anchors.items():
        side = "right" if equipment.endswith("_right") else "left"
        label = equipment.removeprefix("robot_") if equipment.startswith("robot_") else "outfeed_left"
        parent = bpy.data.objects[f"source_{node_ids[0]:04d}"]
        root = bpy.data.objects.new("onhand_" + label + "_mount", None)
        collection.objects.link(root)
        root.parent = parent
        root.matrix_parent_inverse = Matrix.Identity(4)
        root.matrix_basis = Matrix.Identity(4)
        root["mount_frame"] = "tool0; identical to existing gripper_base"
        root["equipment_id"] = equipment
        root["provisional_camera_geometry"] = True
        for part, mesh in mesh_data.items():
            if not part.startswith(side + "_mono_"):
                continue
            obj = bpy.data.objects.new("onhand_" + label + "_" + part.removeprefix(side + "_mono_"), mesh)
            collection.objects.link(obj)
            obj.parent = root
            obj.matrix_parent_inverse = Matrix.Identity(4)
            obj.matrix_basis = Matrix.Identity(4)
        optical = np.asarray(config["cameras"][side]["T_tool0_optical"])
        camera = make_camera("Eye_" + label, collection, Matrix(optical @ np.diag([1, -1, -1, 1])), root)
        camera["image_size_px"] = config["image_size_px"]
        camera["horizontal_fov_deg"] = config["horizontal_fov_deg"]
        camera["optical_axes"] = "x image-right, y image-down, z forward"
        records.append(
            {
                "equipment": equipment,
                "side": side,
                "label": label,
                "tool0_source_node": node_ids[0],
                "equivalent_base_nodes": node_ids,
                "mount_object": root.name,
                "camera_object": camera.name,
                "T_tool0_optical": optical.tolist(),
            }
        )
    detail_collection = bpy.data.collections.new("Onhand_review_views")
    scene.collection.children.link(detail_collection)
    left_parent = bpy.data.objects[records[0]["mount_object"]]
    eye = Vector((-0.29, -0.31, -0.14))
    target = Vector((-0.035, 0, 0.10))
    detail_pose = Matrix.Translation(eye) @ (target - eye).to_track_quat("-Z", "Y").to_matrix().to_4x4()
    detail = make_camera("Mount_OP010_left", detail_collection, detail_pose, left_parent)
    detail.data.lens = 36 / (2 * math.tan(math.radians(40) / 2))
    eye = Vector((8.5, -9.7, 8.6))
    target = Vector((0.0, 2.0, 0.9))
    line_pose = Matrix.Translation(eye) @ (target - eye).to_track_quat("-Z", "Y").to_matrix().to_4x4()
    overview = make_camera("Line_camera_inventory", detail_collection, line_pose)
    overview.data.lens = 36 / (2 * math.tan(math.radians(62) / 2))
    bpy.context.view_layer.update()
    assert original_signature(old_names) == before, "Original scene objects changed during camera attachment"
    maximum_source_error, maximum_attachment_error = 0.0, 0.0
    for frame in range(1, 789):
        scene.frame_set(frame)
        for record in records:
            expected = motion[frame - 1, record["tool0_source_node"]]
            parent = bpy.data.objects[f"source_{record['tool0_source_node']:04d}"]
            root = bpy.data.objects[record["mount_object"]]
            maximum_source_error = max(
                maximum_source_error,
                float(np.max(np.abs(np.asarray(parent.matrix_world) - expected))),
            )
            maximum_attachment_error = max(
                maximum_attachment_error,
                float(np.max(np.abs(np.asarray(root.matrix_world) - expected))),
            )
    assert max(maximum_source_error, maximum_attachment_error) < 2e-5
    scene.frame_set(1)
    scene.camera = bpy.data.objects["Film_camera"]
    scene["camera_addition_status"] = "Provided v0.1 placement on 19 arms; OP010 process review candidate"
    scene["camera_count_added"] = 19
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "UR15_OP010_onhand_v01.blend"))
    write_json(ROOT / "data/camera_instances.json", records)
    write_json(ROOT / "audit/camera_geometry_import.json", geometry_manifest)
    write_json(
        ROOT / "audit/scene_preservation.json",
        {
            "basis": (
                "Read OP010 .blend, apply documented OP010 camera-clearance trajectory, "
                "then compare existing objects before and after camera attachment"
            ),
            "base_blend_sha256": hashlib.sha256((BASE / "UR15_OP010_revision.blend").read_bytes()).hexdigest(),
            "existing_object_count": len(old_names),
            "original_geometry_material_parenting_action_signature": before,
            "original_signature_unchanged": True,
            "op010_camera_clearance_retarget_applied_before_comparison": retarget_applied,
            "camera_count": len(records),
            "added_mesh_objects": len(records) * 5,
            "frames_checked": 788,
            "max_source_tool_matrix_error": maximum_source_error,
            "max_attached_mount_matrix_error": maximum_attachment_error,
            "render_intrinsics": config["K"],
            "outfeed_assumption": "Apply supplied left variant to the single outfeed arm; no second arm added",
            "scope": "Animation/data preservation; not physical validation",
        },
    )
    print("CAMERAS_BUILT", len(records), maximum_attachment_error, flush=True)


if __name__ == "__main__":
    main()
