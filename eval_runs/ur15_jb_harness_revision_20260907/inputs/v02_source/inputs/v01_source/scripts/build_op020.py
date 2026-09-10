#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Transfer the OP020 concept geometry and sampled motion into the accepted scene."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "op010_base/scripts"))
from build_cameras import original_signature  # noqa: E402
from build_op010_blender import add_action  # noqa: E402

SAMPLE_FRAMES = (1, 61, 181, 241, 331, 451, 511, 601, 721, 788)
LIGHT_OUTPUT_SCALE = 0.70
LIGHTING_SCENE_KEY = "op020_lighting_output_record"
VIEWS = {
    "OP020_stock": ((2.7, -2.85, 1.10), (1.98, -2.85, 0.84)),
    "OP020_overview": ((3.1, -4.9, 2.7), (1.15, -2.85, 1.25)),
    "OP020_contact": ((-0.25, -2.85, 1.30), (0.335, -2.85, 0.62)),
    "OP020_product": ((0.15, -2.85, 2.20), (0.2, -2.85, 0.55)),
    "OP020_line_overview": ((8.0, 14.9, 5.4), (0.65, -0.50, 0.84)),
}


def read_json(path: Path) -> dict:
    """Read an exported scene or its change manifest."""
    return json.loads(path.read_text())


def accepted_blend_path(baseline: dict) -> Path:
    """Prefer the packaged accepted scene, keeping the original path as a fallback."""
    local_name = baseline.get("accepted_blend_local")
    if local_name:
        local_path = ROOT / local_name
        if local_path.is_file():
            return local_path
    return Path(baseline["accepted_blend"])


def _lighting_channels(scene: bpy.types.Scene) -> list[tuple]:
    """Inspect constant light controls, deduplicating shared Blender datablocks."""
    channels = []

    def constant(block: bpy.types.ID) -> None:
        animation = block.animation_data
        if animation and (animation.action or animation.drivers or animation.nla_tracks):
            raise RuntimeError(f"Animated lighting control needs explicit handling: {block.name}")

    def channel(kind, block, owner, field, *, scale, node=None, users=()):
        constant(block)
        if block.node_tree:
            constant(block.node_tree)
        if node and owner.is_linked:
            raise RuntimeError(f"Linked emission strength needs explicit handling: {block.name}")
        value = float(getattr(owner, field))
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"Invalid light output: {block.name}: {value}")
        record = {
            "kind": kind,
            "datablock": block.name,
            "node": node.name if node else None,
            "field": owner.name if node else field,
            "value": value,
            "scale": LIGHT_OUTPUT_SCALE if scale else 1.0,
            "users": sorted(obj.name for obj in users),
            "animated": False,
        }
        if node:
            color = node.inputs.get("Emission Color") or node.inputs.get("Color")
            record["color"] = list(color.default_value)
            record["color_links"] = sorted([link.from_node.name, link.from_socket.name] for link in color.links)
        else:
            record["color"] = list(block.color)
            record["light_type"] = block.type
            record["use_nodes"] = block.use_nodes
            record["value_unit"] = "W/m^2" if block.type == "SUN" else "W"
        channels.append((record, owner, field))

    light_users, material_users = {}, {}
    for obj in scene.objects:
        if obj.type == "LIGHT":
            light_users.setdefault(obj.data.name, []).append(obj)
        for slot in obj.material_slots:
            if slot.material:
                material_users.setdefault(slot.material.name, set()).add(obj)
    for name, users in sorted(light_users.items()):
        lamp = bpy.data.lights[name]
        # The accepted asset has thirteen non-node lights. Fail closed on a new
        # node/driver power path instead of multiplying two interacting controls.
        if lamp.use_nodes:
            raise RuntimeError(f"Accepted light unexpectedly uses shader nodes: {name}")
        channel("light_energy", lamp, lamp, "energy", scale=True, users=users)
    world = scene.world
    if not world or not world.use_nodes:
        raise RuntimeError("Expected the accepted node-based ambient World")
    backgrounds = [node for node in world.node_tree.nodes if node.type == "BACKGROUND"]
    if len(backgrounds) != 1:
        raise RuntimeError("Expected one accepted World Background strength control")
    for node in backgrounds:
        channel(
            "world_background",
            world,
            node.inputs["Strength"],
            "default_value",
            scale=True,
            node=node,
        )
    fixture_count = 0
    for name, users in sorted(material_users.items()):
        material = bpy.data.materials[name]
        if not material.use_nodes:
            continue
        fixture_users = [obj for obj in users if obj.get("equipment_id", "").startswith("line_lighting_")]
        for node in material.node_tree.nodes:
            strength_name = {
                "BSDF_PRINCIPLED": "Emission Strength",
                "EMISSION": "Strength",
            }.get(node.type)
            if not strength_name:
                continue
            strength = node.inputs[strength_name]
            if not strength.is_linked and strength.default_value == 0:
                continue
            if fixture_users and len(fixture_users) != len(users):
                raise RuntimeError(f"Lighting material also serves a display or status object: {name}")
            is_fixture = bool(fixture_users)
            fixture_count += int(is_fixture)
            channel(
                "fixture_emission" if is_fixture else "preserved_display_or_indicator_emission",
                material,
                strength,
                "default_value",
                scale=is_fixture,
                node=node,
                users=users,
            )
            channels[-1][0]["source_material_ids"] = material.get("source_material_ids")
    if not light_users or not fixture_count:
        raise RuntimeError("Accepted light objects or ceiling emissive fixtures are missing")
    return channels


def lighting_snapshot(scene: bpy.types.Scene) -> dict:
    """Read light outputs and unchanged color-management settings for comparison."""
    return {
        "channels": [record for record, _, _ in _lighting_channels(scene)],
        "view_settings": {
            key: getattr(scene.view_settings, key) for key in ("view_transform", "look", "exposure", "gamma")
        },
    }


def verify_lighting_output(scene: bpy.types.Scene, report: dict) -> dict:
    """Verify saved output ratios; this is not a lux or physical illumination test."""
    if report.get("light_output_scale") != LIGHT_OUTPUT_SCALE:
        raise RuntimeError("Lighting report has the wrong requested output scale")
    actual = lighting_snapshot(scene)
    if actual != report["after"]:
        raise RuntimeError("Saved light controls differ from the recorded after values")
    before = report["before"]
    if before["view_settings"] != actual["view_settings"]:
        raise RuntimeError("Exposure or color management changed with the lighting")
    if len(before["channels"]) != len(actual["channels"]):
        raise RuntimeError("Light channel inventory changed during scaling")
    for old, new in zip(before["channels"], actual["channels"], strict=True):
        if {k: v for k, v in old.items() if k != "value"} != {k: v for k, v in new.items() if k != "value"}:
            raise RuntimeError(f"Light attributes changed: {new['datablock']}")
        if not math.isclose(new["value"], old["value"] * new["scale"], rel_tol=1e-7, abs_tol=1e-7):
            raise RuntimeError(f"Light output ratio differs: {new['datablock']}")
    return {
        "light_output_scale": LIGHT_OUTPUT_SCALE,
        "channels_verified": len(actual["channels"]),
        "exposure_and_color_management_unchanged": True,
        "display_and_indicator_emission_unchanged": True,
        "animated_light_controls": 0,
        "node_based_light_objects": 0,
    }


def apply_lighting_output(scene: bpy.types.Scene) -> dict:
    """Set illumination-source output to 70 percent once, preserving display emission."""
    if LIGHTING_SCENE_KEY in scene:
        report = json.loads(scene[LIGHTING_SCENE_KEY])
        verify_lighting_output(scene, report)
        return report
    before = lighting_snapshot(scene)
    channels = _lighting_channels(scene)
    for record, owner, field in channels:
        if record["scale"] != 1.0:
            setattr(owner, field, record["value"] * record["scale"])
    report = {
        "schema_version": 1,
        "scope": "Light-source output controls only; not measured illuminance, image brightness or physical validity",
        "light_output_scale": LIGHT_OUTPUT_SCALE,
        "before": before,
        "after": lighting_snapshot(scene),
        "shared_datablock_policy": (
            "One assignment per unique light or material strength; 22 ceiling fixtures share one material"
        ),
        "animation_policy": (
            "Accepted light energy and emission controls are constant; "
            "action, NLA, driver or linked-strength inputs fail closed"
        ),
        "renderer_basis": (
            "Accepted Cycles renderer, Light.energy, one World Background strength "
            "and line_lighting equipment emission; no exposure substitution"
        ),
    }
    verify_lighting_output(scene, report)
    scene[LIGHTING_SCENE_KEY] = json.dumps(report, ensure_ascii=False)
    return report


def lighting_normalized_signature(scene: bpy.types.Scene, names: list[str], report: dict) -> str:
    """Check the existing preservation signature with only authorized outputs normalized."""
    channels = _lighting_channels(scene)
    try:
        for old, (_, owner, field) in zip(report["before"]["channels"], channels, strict=True):
            setattr(owner, field, old["value"])
        return original_signature(names)
    finally:
        for current, owner, field in channels:
            setattr(owner, field, current["value"])


def material_from_spec(spec: dict) -> bpy.types.Material:
    """Reproduce the accepted renderer's surface response for an OP020 material."""
    material = bpy.data.materials.new("OP020_" + spec["name"])
    material.use_nodes = True
    material["source_material_ids"] = str(spec["id"])
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes.get("Principled BSDF")
    color = list(spec["base_color"])
    luminance = sum(color[:3]) / 3
    color[:3] = [0.8 * channel + 0.2 * luminance for channel in color[:3]]
    shader.inputs["Base Color"].default_value = color
    metallic, roughness = spec["metallic"], spec["roughness"]
    if metallic > 0.95 and roughness > 0.65:
        roughness = 0.34
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Coat Weight"].default_value = 0.08 if metallic < 0.65 else 0.025
    shader.inputs["Coat Roughness"].default_value = 0.28
    if metallic > 0.65:
        shader.inputs["Anisotropic"].default_value = 0.22
    for field, socket in (
        ("base_texture", "Base Color"),
        ("emission_texture", "Emission Color"),
    ):
        filename = spec.get(field)
        if not filename:
            continue
        candidates = (ROOT / "data" / filename, ROOT / "op010_base/data" / filename)
        image_path = next((path for path in candidates if path.is_file()), None)
        if image_path is None:
            raise FileNotFoundError(f"Missing OP020 material texture: {filename}")
        image = bpy.data.images.load(str(image_path), check_existing=True)
        image.pack()
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = image
        texture.interpolation = "Linear"
        coordinates = nodes.new("ShaderNodeTexCoord")
        links.new(coordinates.outputs["UV"], texture.inputs["Vector"])
        links.new(texture.outputs["Color"], shader.inputs[socket])
    emission = spec.get("emission", [0.0, 0.0, 0.0])
    if max(emission) > 0:
        shader.inputs["Emission Color"].default_value = (*emission, 1)
        shader.inputs["Emission Strength"].default_value = 4.0 if luminance > 0.4 else 1.5
    if spec.get("emission_texture"):
        shader.inputs["Emission Strength"].default_value = 1.4
    if not spec.get("emission_texture") and max(emission) < 0.5:
        coordinates = nodes.new("ShaderNodeTexCoord")
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 180.0 if metallic > 0.65 else 90.0
        noise.inputs["Detail"].default_value = 2.0
        links.new(coordinates.outputs["Object"], noise.inputs["Vector"])
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.16
        bump.inputs["Distance"].default_value = 0.00010 if metallic > 0.65 else 0.00025
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        if metallic > 0.2 and not spec.get("base_texture"):
            bevel = nodes.new("ShaderNodeBevel")
            bevel.samples = 3
            bevel.inputs["Radius"].default_value = 0.00045
            links.new(bevel.outputs["Normal"], bump.inputs["Normal"])
        links.new(bump.outputs["Normal"], shader.inputs["Normal"])
        variation = nodes.new("ShaderNodeMapRange")
        variation.inputs["From Min"].default_value = 0.0
        variation.inputs["From Max"].default_value = 1.0
        variation.inputs["To Min"].default_value = max(0.1, roughness - 0.055)
        variation.inputs["To Max"].default_value = min(0.95, roughness + 0.055)
        links.new(noise.outputs["Fac"], variation.inputs["Value"])
        links.new(variation.outputs["Result"], shader.inputs["Roughness"])
    return material


def verify_mesh_buffers(mesh: bpy.types.Mesh, part: dict, arrays: np.lib.npyio.NpzFile) -> None:
    """Check exact exported vertices [m] and triangle boundaries without editing a mesh."""
    key = part["key"]
    vertices = np.asarray(arrays[key + "_vertices"], dtype=np.float32)
    faces = np.asarray(arrays[key + "_faces"], dtype=np.int32)
    if vertices.ndim != 2 or vertices.shape[1] != 3 or faces.ndim != 2 or faces.shape[1] != 3:
        raise ValueError(f"Expected vertices and triangular faces: {key}")
    if len(mesh.vertices) != len(vertices) or len(mesh.loops) != faces.size or len(mesh.polygons) != len(faces):
        raise RuntimeError(f"Primitive buffer sizes differ from the export: {key}")
    actual_vertices = np.empty(vertices.size, dtype=np.float32)
    actual_faces = np.empty(faces.size, dtype=np.int32)
    loop_totals = np.empty(len(faces), dtype=np.int32)
    loop_starts = np.empty(len(faces), dtype=np.int32)
    mesh.vertices.foreach_get("co", actual_vertices)
    mesh.loops.foreach_get("vertex_index", actual_faces)
    mesh.polygons.foreach_get("loop_total", loop_totals)
    mesh.polygons.foreach_get("loop_start", loop_starts)
    if (
        not np.array_equal(actual_vertices, vertices.ravel())
        or not np.array_equal(actual_faces, faces.ravel())
        or not np.all(loop_totals == 3)
        or not np.array_equal(loop_starts, np.arange(len(faces), dtype=np.int32) * 3)
    ):
        raise RuntimeError(f"Primitive differs from the exported geometry: {key}")


def mesh_from_part(
    part: dict,
    arrays: np.lib.npyio.NpzFile,
    material: bpy.types.Material,
    dynamic: bool = False,
) -> bpy.types.Mesh:
    """Create one shared primitive with exported vertices [m] and triangle indices."""
    key = part["key"]
    vertices = np.asarray(arrays[key + "_vertices"], dtype=np.float32)
    faces = np.asarray(arrays[key + "_faces"], dtype=np.int32)
    mesh = bpy.data.meshes.new(key)
    mesh.from_pydata(vertices.tolist(), [], faces.tolist())
    mesh.update(calc_edges=True)
    if mesh.validate(verbose=True):
        raise ValueError(f"Invalid exported geometry required changes: {key}")
    if dynamic or key + "_normals" in arrays:
        mesh.polygons.foreach_set("use_smooth", np.ones(len(faces), dtype=bool))
    if not dynamic and key + "_normals" in arrays:
        mesh.normals_split_custom_set_from_vertices(arrays[key + "_normals"].tolist())
    if key + "_uv" in arrays:
        layer = mesh.uv_layers.new(name="Original_UV")
        layer.data.foreach_set("uv", arrays[key + "_uv"][faces.ravel()].ravel())
    mesh.materials.append(material)
    mesh["source_primitive"] = key
    verify_mesh_buffers(mesh, part, arrays)
    return mesh


def original_mesh_from_part(part: dict, arrays: np.lib.npyio.NpzFile, dynamic: bool) -> bpy.types.Mesh:
    """Reuse accepted vertices [m], topology and shading after an exact export check."""
    key = part["key"]
    if dynamic:
        raise ValueError("Dynamic cable must use a new op020_ primitive")
    mesh = bpy.data.meshes.get(key)
    if mesh is None:
        raise ValueError(f"Original primitive missing from the accepted scene: {key}")
    verify_mesh_buffers(mesh, part, arrays)
    return mesh


def add_cable_shape_keys(obj: bpy.types.Object, vertices: np.ndarray, faces: np.ndarray) -> None:
    """Bake cable vertex positions [m] into relative keys at the source 30 Hz frames."""
    if obj.data.users != 1:
        raise ValueError("Dynamic cable requires a primitive key unique to its node")
    if vertices.ndim != 3 or vertices.shape[1:] != (len(obj.data.vertices), 3):
        raise ValueError(f"Cable shape mismatch: {vertices.shape}")
    actual_faces = np.empty(len(obj.data.loops), dtype=np.int32)
    obj.data.loops.foreach_get("vertex_index", actual_faces)
    if not np.array_equal(actual_faces, np.asarray(faces).ravel()):
        raise ValueError("Dynamic cable faces differ from the exported primitive")
    basis = obj.shape_key_add(name="Basis", from_mix=False)
    basis.data.foreach_set("co", np.asarray(vertices[0], dtype=np.float32).ravel())
    keys = obj.data.shape_keys
    keys.use_relative = True
    keys.animation_data_create()
    action = bpy.data.actions.new("OP020_cable_shape_samples")
    for frame, positions in enumerate(vertices, start=1):
        block = obj.shape_key_add(name=f"source_frame_{frame:04d}", from_mix=False)
        block.relative_key = basis
        block.data.foreach_set("co", np.asarray(positions, dtype=np.float32).ravel())
        block.value = 0.0
        curve = action.fcurves.new(block.path_from_id("value"))
        curve.keyframe_points.add(3)
        curve.keyframe_points.foreach_set("co", np.asarray((frame - 1, 0, frame, 1, frame + 1, 0), dtype=np.float32))
        curve.extrapolation = "CONSTANT"
        for point in curve.keyframe_points:
            point.interpolation = "LINEAR"
        curve.update()
    # Blender 4.4+ can leave an action assigned before its curves without a slot.
    # Bind after curve creation, then select its Key slot explicitly:
    # https://developer.blender.org/docs/release_notes/4.4/python_api/#slotted-actions
    keys.animation_data.action = action
    keys.animation_data.action_slot = action.slots[0]
    obj.data.update()


def look_at(eye: tuple, target: tuple) -> Matrix:
    """Return a Blender camera pose from eye and target positions [m]."""
    eye_vector = Vector(eye)
    rotation = (Vector(target) - eye_vector).to_track_quat("-Z", "Y")
    return Matrix.Translation(eye_vector) @ rotation.to_matrix().to_4x4()


def add_review_cameras(scene: bpy.types.Scene, frames: np.ndarray) -> dict:
    """Add OP020 views with 50-degree vertical field of view and 30 Hz film poses."""
    collection = bpy.data.collections.new("OP020_review_views")
    scene.collection.children.link(collection)

    def camera(name: str, poses: np.ndarray) -> bpy.types.Object:
        if name in bpy.data.objects:
            raise ValueError(f"OP020 view already exists: {name}")
        data = bpy.data.cameras.new(name)
        data.sensor_fit = "VERTICAL"
        data.sensor_height = 24
        data.lens = 24 / (2 * math.tan(math.radians(50) / 2))
        data.clip_start = 0.03
        data.clip_end = 100
        data.dof.use_dof = False
        obj = bpy.data.objects.new(name, data)
        collection.objects.link(obj)
        add_action(obj, poses, frames)
        return obj

    view_poses = {name: np.asarray(look_at(*points)) for name, points in VIEWS.items()}
    for name, pose in view_poses.items():
        camera(name, np.repeat(pose[None], len(frames), axis=0))
    film_poses, shots = [], []
    for frame in frames:
        seconds = float(frame - 1) / 30
        name = (
            "OP020_line_overview"
            if seconds < 0.9
            else "OP020_stock"
            if seconds < 3.4
            else "OP020_overview"
            if seconds < 14.6
            else "OP020_contact"
            if seconds < 23.3
            else "OP020_product"
            if seconds < 24.2
            else "OP020_line_overview"
        )
        film_poses.append(view_poses[name])
        if not shots or shots[-1]["camera"] != name:
            shots.append({"frame": int(frame), "source_time_s": seconds, "camera": name})
    film = camera("Film_OP020", np.asarray(film_poses))
    scene.camera = film
    return {"vertical_fov_deg": 50, "views": VIEWS, "film_shots": shots}


def camera_settings(names: list[str]) -> dict:
    """Capture existing camera intrinsics and mounting settings for preservation."""
    result = {}
    for name in names:
        obj = bpy.data.objects[name]
        data = obj.data
        result[name] = {
            "parent": obj.parent.name if obj.parent else None,
            "basis": np.asarray(obj.matrix_basis).tolist(),
            "parent_inverse": np.asarray(obj.matrix_parent_inverse).tolist(),
            "type": data.type,
            "sensor_fit": data.sensor_fit,
            "sensor_width": data.sensor_width,
            "sensor_height": data.sensor_height,
            "lens": data.lens,
            "shift_x": data.shift_x,
            "shift_y": data.shift_y,
            "clip_start": data.clip_start,
            "clip_end": data.clip_end,
            "dof_enabled": data.dof.use_dof,
        }
    return result


def main() -> None:
    baseline = read_json(ROOT / "data/op020_baseline.json")
    source_path = accepted_blend_path(baseline)
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if source_sha != baseline["accepted_blend_sha256"]:
        raise RuntimeError("Accepted input blend differs from the recorded baseline")
    if Path(bpy.data.filepath).resolve() != source_path.resolve():
        bpy.ops.wm.open_mainfile(filepath=str(source_path))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    source = read_json(ROOT / "data/scene_op020.json")
    changes = read_json(ROOT / "data/op020_changes.json")
    arrays = np.load(ROOT / "data/geometry_op020.npz")
    motion = np.load(ROOT / "data/motion_op020.npz")
    poses = motion["poses"]
    if poses.shape != (788, len(source["nodes"]), 4, 4):
        raise ValueError(f"Unexpected source pose shape: {poses.shape}")
    frames = np.arange(1, len(poses) + 1, dtype=np.float32)
    nodes = {record["id"]: record for record in source["nodes"]}
    meshes = {record["id"]: record for record in source["meshes"]}
    materials = {record["id"]: record for record in source["materials"]}
    if sorted(nodes) != list(range(len(nodes))):
        raise ValueError("Source node IDs must index the exported pose array")
    geometry_ids = set(changes["geometry_node_ids"])
    motion_ids = set(changes["motion_node_ids"])
    new_ids = set(changes["new_node_ids"])
    cable_id = changes["dynamic_cable_node"]
    changed_ids = geometry_ids | motion_ids | new_ids
    if (geometry_ids & new_ids) or not changed_ids.issubset(nodes):
        raise ValueError("Invalid changed node IDs")
    for node_id in geometry_ids | motion_ids:
        if node_id not in new_ids and f"source_{node_id:04d}" not in bpy.data.objects:
            raise ValueError(f"Missing accepted source node: {node_id}")
    if any(f"source_{node_id:04d}" in bpy.data.objects for node_id in new_ids):
        raise ValueError("A declared new node already exists in the accepted scene")
    old_mesh_objects = [
        child
        for node_id in geometry_ids
        for child in bpy.data.objects[f"source_{node_id:04d}"].children
        if child.type == "MESH"
    ]
    excluded = {obj.name for obj in old_mesh_objects}
    excluded.update(f"source_{node_id:04d}" for node_id in motion_ids)
    # original_signature hashes only the named objects, without traversing children.
    # Geometry-only parents remain checked; their replaced mesh children are excluded.
    unchanged = [obj.name for obj in bpy.data.objects if obj.name not in excluded]
    before_signature = original_signature(unchanged)
    old_camera_names = [obj.name for obj in bpy.data.objects if obj.type == "CAMERA"]
    eye_names = [name for name in old_camera_names if name.startswith("Eye_")]
    if len(eye_names) != 19:
        raise ValueError(f"Expected 19 onhand cameras, found {len(eye_names)}")
    before_cameras = camera_settings(old_camera_names)
    for obj in old_mesh_objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    collections = {}
    for node_id in sorted(geometry_ids | new_ids):
        record = nodes[node_id]
        equipment = record["equipment"]
        if equipment not in collections:
            collection = bpy.data.collections.get(equipment)
            if collection is None:
                collection = bpy.data.collections.new(equipment)
                scene.collection.children.link(collection)
            collections[equipment] = collection
        if node_id in new_ids:
            parent = bpy.data.objects.new(f"source_{node_id:04d}", None)
            collections[equipment].objects.link(parent)
            parent["source_node_id"] = node_id
            parent["equipment_id"] = equipment
            parent["original_name"] = record["name"]
            parent.empty_display_size = 0.025
            parent.matrix_world = Matrix(poses[0, node_id])
    cable_parts = meshes[nodes[cable_id]["mesh"]]["parts"]
    if len(cable_parts) != 1 or cable_id not in (geometry_ids | new_ids):
        raise ValueError("Dynamic cable must have one newly transferred primitive")
    cable_key = cable_parts[0]["key"]
    cable_users = [
        node_id
        for node_id, record in nodes.items()
        if any(part["key"] == cable_key for part in meshes[record["mesh"]]["parts"])
    ]
    if cable_users != [cable_id]:
        raise ValueError(f"Dynamic cable primitive is shared by nodes: {cable_users}")
    material_cache, mesh_cache, child_objects = {}, {}, {}
    reused_primitives, created_primitives = [], []
    for node_id in sorted(geometry_ids | new_ids):
        record = nodes[node_id]
        parent = bpy.data.objects[f"source_{node_id:04d}"]
        children = []
        for part in meshes[record["mesh"]]["parts"]:
            key, material_id = part["key"], part["material"]
            if key not in mesh_cache:
                if key.startswith("op020_"):
                    if material_id not in material_cache:
                        material_cache[material_id] = material_from_spec(materials[material_id])
                    mesh_cache[key] = mesh_from_part(
                        part,
                        arrays,
                        material_cache[material_id],
                        dynamic=key == cable_key,
                    )
                    created_primitives.append(key)
                else:
                    # Reuse the accepted datablock intact, including its material,
                    # UV layers, custom normals and polygon shading settings.
                    mesh_cache[key] = original_mesh_from_part(part, arrays, dynamic=key == cable_key)
                    reused_primitives.append(key)
            child = bpy.data.objects.new(f"{parent.name}_{key}", mesh_cache[key])
            collections[record["equipment"]].objects.link(child)
            child.parent = parent
            child.matrix_parent_inverse = Matrix.Identity(4)
            child.matrix_basis = Matrix.Identity(4)
            child["equipment_id"] = record["equipment"]
            children.append(child)
        child_objects[node_id] = children
    for node_id in sorted(motion_ids | new_ids):
        obj = bpy.data.objects[f"source_{node_id:04d}"]
        if obj.parent is not None:
            raise ValueError(f"Source animation expects unparented world poses: {node_id}")
        obj.animation_data_clear()
        add_action(obj, poses[:, node_id], frames)
    cable_data = np.load(ROOT / changes["dynamic_vertices_file"])
    cable_vertices, cable_faces = cable_data["vertices"], cable_data["faces"]
    if len(cable_vertices) != len(frames):
        raise ValueError("Cable and source motion have different frame counts")
    cable_obj = child_objects[cable_id][0]
    add_cable_shape_keys(cable_obj, cable_vertices, cable_faces)
    view_report = add_review_cameras(scene, frames)
    scene.render.fps = 30
    scene.frame_start, scene.frame_end = 1, len(frames)
    scene.frame_set(1)
    bpy.context.view_layer.update()
    after_signature = original_signature(unchanged)
    after_cameras = camera_settings(old_camera_names)
    if before_signature != after_signature:
        raise RuntimeError("Unexpected geometry, material, parenting or animation change")
    if before_cameras != after_cameras:
        raise RuntimeError("An existing review or onhand camera was modified")
    frame_checks = []
    maximum_error, maximum_cable_error = 0.0, 0.0
    for frame in SAMPLE_FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        errors = [
            float(
                np.max(
                    np.abs(
                        np.asarray(bpy.data.objects[f"source_{node_id:04d}"].matrix_world) - poses[frame - 1, node_id]
                    )
                )
            )
            for node_id in nodes
        ]
        evaluated = cable_obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        actual = np.empty(cable_vertices[frame - 1].size, dtype=np.float32)
        evaluated.data.vertices.foreach_get("co", actual)
        cable_error = float(np.max(np.abs(actual.reshape(-1, 3) - cable_vertices[frame - 1])))
        maximum_error = max(maximum_error, max(errors))
        maximum_cable_error = max(maximum_cable_error, cable_error)
        frame_checks.append(
            {
                "frame": frame,
                "max_matrix_element_error": max(errors),
                "max_cable_vertex_component_error_m": cable_error,
            }
        )
    if maximum_error > 2e-5 or maximum_cable_error > 2e-5:
        raise RuntimeError(f"Transfer tolerance exceeded: matrix={maximum_error}, cable={maximum_cable_error}")
    scene.frame_set(1)
    bpy.context.view_layer.update()
    lighting_report = apply_lighting_output(scene)
    normalized_signature = lighting_normalized_signature(scene, unchanged, lighting_report)
    if normalized_signature != before_signature:
        raise RuntimeError("An unauthorized change accompanied the light-output adjustment")
    lighting_report["verification"] = verify_lighting_output(scene, lighting_report)
    output_path = ROOT / "UR15_OP020_v01.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path), compress=True)
    output_sha = hashlib.sha256(output_path.read_bytes()).hexdigest()
    lighting_report.update(
        accepted_blend_sha256=source_sha,
        output_blend_sha256=output_sha,
        input_sha256={
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                source_path,
                ROOT / "data/op020_baseline.json",
                Path(__file__).resolve(),
            )
            if path.is_relative_to(ROOT)
        },
        original_signature_with_authorized_outputs_normalized=normalized_signature,
    )
    (ROOT / "audit").mkdir(exist_ok=True)
    lighting_path = ROOT / "audit/op020_lighting_checks.json"
    lighting_path.write_text(json.dumps(lighting_report, ensure_ascii=False, indent=2) + "\n")
    report = {
        "scope": "OP020 source transfer and preservation; not a physical-validity verdict",
        "accepted_blend": str(source_path),
        "accepted_blend_provenance": baseline["accepted_blend"],
        "accepted_blend_sha256": source_sha,
        "baseline_sha256_verified": True,
        "output_blend": output_path.name,
        "output_blend_sha256": output_sha,
        "source_node_count": len(nodes),
        "frame_count": len(frames),
        "fps": 30,
        "geometry_node_ids": sorted(geometry_ids),
        "motion_node_ids": sorted(motion_ids),
        "new_node_ids": sorted(new_ids),
        "geometry_node_count": len(geometry_ids),
        "motion_node_count": len(motion_ids),
        "new_node_count": len(new_ids),
        "replaced_mesh_objects": len(old_mesh_objects),
        "transferred_mesh_objects": sum(len(value) for value in child_objects.values()),
        "shared_primitives_verified_bit_exact": len(mesh_cache),
        "reused_original_primitive_keys": sorted(reused_primitives),
        "newly_created_primitive_keys": sorted(created_primitives),
        "original_primitive_shading": (
            "Accepted mesh datablocks, UVs, normals and materials preserved except "
            "authorized ceiling-fixture emission strength at 70 percent"
        ),
        "unchanged_object_count": len(unchanged),
        "unchanged_signature_before": before_signature,
        "unchanged_signature_after": after_signature,
        "unchanged_signature_verified": True,
        "unchanged_signature_scope": (
            "Existing geometry/material signature checked before light adjustment "
            "and again with only authorized output values temporarily normalized"
        ),
        "lighting_normalized_signature": normalized_signature,
        "light_output_scale": LIGHT_OUTPUT_SCALE,
        "lighting_checks": str(lighting_path.relative_to(ROOT)),
        "lighting_checks_sha256": hashlib.sha256(lighting_path.read_bytes()).hexdigest(),
        "preserved_camera_settings": after_cameras,
        "onhand_camera_count": len(eye_names),
        "all_existing_camera_settings_verified": True,
        "dynamic_cable_node": cable_id,
        "dynamic_cable_shape_keys": len(frames),
        "dynamic_cable_visibility": "Source parent poses; shape vertices use world coordinates",
        "frame_transform_checks": frame_checks,
        "maximum_matrix_element_error": maximum_error,
        "maximum_cable_vertex_component_error_m": maximum_cable_error,
        "new_review_cameras": view_report,
    }
    (ROOT / "audit").mkdir(exist_ok=True)
    (ROOT / "audit/op020_scene_transfer.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("OP020_BLEND_READY", json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
