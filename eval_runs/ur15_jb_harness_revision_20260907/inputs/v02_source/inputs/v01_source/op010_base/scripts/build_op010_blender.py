#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Build the OP010 revision using the existing v3 Cycles materials and lighting."""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parent.parent


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def look_at(eye, target):
    eye = Vector(eye)
    return Matrix.Translation(eye) @ (Vector(target) - eye).to_track_quat("-Z", "Y").to_matrix().to_4x4()


def add_action(obj, poses, frames):
    """Bake source world transforms at the original 30 Hz sampling rate."""
    obj.rotation_mode = "QUATERNION"
    values = np.empty((len(frames), 10), dtype=np.float64)
    for index, pose in enumerate(poses):
        location, rotation, scale = Matrix(pose).decompose()
        values[index] = (*location, *rotation, *scale)
        if index and np.dot(values[index - 1, 3:7], values[index, 3:7]) < 0:
            values[index, 3:7] *= -1
    obj.location = values[0, :3]
    obj.rotation_quaternion = values[0, 3:7]
    obj.scale = values[0, 7:]
    action = None
    for offset, path, width in ((0, "location", 3), (3, "rotation_quaternion", 4), (7, "scale", 3)):
        for component in range(width):
            series = values[:, offset + component]
            if np.ptp(series) < 1e-8:
                continue
            if action is None:
                action = bpy.data.actions.new(obj.name + "_source_motion")
            curve = action.fcurves.new(path, index=component)
            curve.keyframe_points.add(len(frames))
            curve.keyframe_points.foreach_set("co", np.column_stack((frames, series)).astype(np.float32).ravel())
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"
            curve.update()
    if action is not None:
        obj.animation_data_create()
        obj.animation_data.action = action


def smooth_cad_normals(vertices, normals):
    """Smooth duplicated CAD corner normals below 35 degrees without moving vertices."""
    _, inverse = np.unique(np.round(vertices, decimals=6), axis=0, return_inverse=True)
    order = np.argsort(inverse, kind="stable")
    boundaries = np.r_[0, np.flatnonzero(np.diff(inverse[order])) + 1, len(order)]
    result = normals.copy()
    threshold = math.cos(math.radians(35))
    for begin, end in zip(boundaries[:-1], boundaries[1:]):
        indices = order[begin:end]
        if len(indices) < 2:
            continue
        candidates = normals[indices]
        weights = candidates @ candidates.T >= threshold
        averaged = weights.astype(np.float32) @ candidates
        lengths = np.linalg.norm(averaged, axis=1, keepdims=True)
        result[indices] = averaged / np.maximum(lengths, 1e-12)
    return result


def add_review_cameras(scene, motion, frames):
    """Add fixed review views and an OP010 sequence camera."""
    camera_collection = bpy.data.collections.new("Film_cameras")
    scene.collection.children.link(camera_collection)

    def camera(name, camera_poses):
        data = bpy.data.cameras.new(name)
        data.sensor_fit = "VERTICAL"
        data.sensor_height = 24
        data.lens = 24 / (2 * math.tan(math.radians(40) / 2))
        data.clip_start = 0.03
        data.clip_end = 100
        obj = bpy.data.objects.new(name, data)
        camera_collection.objects.link(obj)
        add_action(obj, camera_poses, frames)
        return obj

    camera("Reference_camera", motion["camera_poses"])
    views = {
        "OP010_overview": ((2.6, -7.7, 2.8), (-0.85, -4.0, 1.0), 50),
        "OP010_stock": ((-0.3, -6.3, 1.9), (-1.65, -4.0, 0.95), 50),
        "OP010_contact": ((1.35, -5.10, 1.60), (-0.10, -4.0, 0.65), 50),
        "OP010_product": ((0.85, -4.80, 1.65), (0.0, -4.0, 0.51), 45),
    }
    for name, (eye, target, fov) in views.items():
        matrices = np.repeat(np.asarray(look_at(eye, target))[None], len(frames), axis=0)
        view = camera(name, matrices)
        view.data.lens = 24 / (2 * math.tan(math.radians(fov) / 2))
    film_poses = motion["camera_poses"].copy()
    shot_records = []
    for index in range(len(frames)):
        seconds = index / 30
        name = (
            "OP010_stock"
            if seconds < 8.8
            else "OP010_overview"
            if seconds < 14.6
            else "OP010_contact"
            if seconds < 23.3
            else "OP010_product"
        )
        eye, target, fov = views[name]
        film_poses[index] = np.asarray(look_at(eye, target))
        shot_records.append(
            {"frame": index + 1, "source_time_s": seconds, "shot": name, "camera_matrix": film_poses[index].tolist()}
        )
    film = camera("Film_camera", film_poses)
    film.data.lens = 24 / (2 * math.tan(math.radians(50) / 2))
    for name, frame in (
        ("OP010 supply and grasp", 1),
        ("OP010 transfer", 265),
        ("OP010 seat and release", 439),
        ("OP010 completed subassembly", 700),
    ):
        scene.timeline_markers.new(name, frame=frame)
    scene.camera = film
    write_json(ROOT / "data/film_camera.json", shot_records)


def verify_transfer(scene, source_objects, poses):
    """Compare Blender transforms with the revised export at sampled frames."""
    maximum_error = 0.0
    frame_errors = []
    for frame in (1, 61, 241, 451, 511, 601, 721, 788):
        scene.frame_set(frame)
        errors = [
            float(np.max(np.abs(np.asarray(obj.matrix_world) - poses[frame - 1, index])))
            for index, obj in enumerate(source_objects)
        ]
        error = max(errors)
        maximum_error = max(maximum_error, error)
        frame_errors.append({"frame": frame, "max_matrix_element_error": error})
    if maximum_error > 2e-5:
        raise RuntimeError(f"Animation transfer exceeded tolerance: {maximum_error}")
    return maximum_error, frame_errors


def main():
    started = time.monotonic()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    source = json.loads((ROOT / "data/scene.json").read_text())
    geometry = np.load(ROOT / "data/geometry.npz")
    motion = np.load(ROOT / "data/motion.npz")
    poses = motion["poses"]
    frames = np.arange(1, len(poses) + 1, dtype=np.float32)
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = len(frames)
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.render.engine = "CYCLES"
    scene.render.use_persistent_data = True
    scene.render.use_motion_blur = False
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPTIX"
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 4
    scene.cycles.transparent_max_bounces = 6
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.035
    scene.cycles.adaptive_min_samples = 16
    scene.cycles.seed = 19
    scene.cycles.use_animated_seed = False
    scene.cycles.device = "GPU"
    preferences = bpy.context.preferences.addons["cycles"].preferences
    preferences.compute_device_type = "OPTIX"
    preferences.refresh_devices()
    for device in preferences.devices:
        device.use = device.type == "OPTIX"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.6
    scene.world = bpy.data.worlds.new("Original_factory_ambient")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.58, 0.66, 0.72, 1)
    background.inputs["Strength"].default_value = 0.35

    collections = {}
    for name in source["groups"]:
        collection = bpy.data.collections.new(name)
        scene.collection.children.link(collection)
        collections[name] = collection

    images = {}
    materials = {}
    canonical = {}
    for spec in source["materials"]:
        signature = json.dumps({k: v for k, v in spec.items() if k not in ("id", "name")}, sort_keys=True)
        if signature in canonical:
            materials[spec["id"]] = canonical[signature]
            continue
        mat = bpy.data.materials.new(spec["name"])
        mat.use_nodes = True
        mat["source_material_ids"] = str(spec["id"])
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        shader = nodes.get("Principled BSDF")
        color = list(spec["base_color"])
        luminance = sum(color[:3]) / 3
        color[:3] = [0.8 * channel + 0.2 * luminance for channel in color[:3]]
        shader.inputs["Base Color"].default_value = color
        metallic = spec["metallic"]
        roughness = spec["roughness"]
        if metallic > 0.95 and roughness > 0.65:
            roughness = 0.34
        shader.inputs["Metallic"].default_value = metallic
        shader.inputs["Roughness"].default_value = roughness
        shader.inputs["Coat Weight"].default_value = 0.08 if metallic < 0.65 else 0.025
        shader.inputs["Coat Roughness"].default_value = 0.28
        if metallic > 0.65:
            shader.inputs["Anisotropic"].default_value = 0.22
        base_image_node = None
        for field, socket in (
            ("base_texture", "Base Color"),
            ("emission_texture", "Emission Color"),
        ):
            filename = spec[field]
            if filename:
                if filename not in images:
                    image = bpy.data.images.load(str(ROOT / "data" / filename))
                    image.pack()
                    images[filename] = image
                image_node = nodes.new("ShaderNodeTexImage")
                image_node.image = images[filename]
                image_node.interpolation = "Linear"
                uv = nodes.new("ShaderNodeTexCoord")
                # Both importers interpret the stored images with the same UV orientation.
                links.new(uv.outputs["UV"], image_node.inputs["Vector"])
                links.new(image_node.outputs["Color"], shader.inputs[socket])
                if field == "base_texture":
                    base_image_node = image_node
        # The original UR CAD atlas identifies metal, dark polymer, and blue end caps.
        # Preserve its color boundaries while adding the appropriate surface response.
        robot_atlas = spec["alpha_mode"] == "BLEND" and base_image_node is not None and spec["roughness"] > 0.99
        if robot_atlas:
            separate = nodes.new("ShaderNodeSeparateColor")
            separate.mode = "HSV"
            links.new(base_image_node.outputs["Color"], separate.inputs["Color"])
            neutral = nodes.new("ShaderNodeMath")
            neutral.operation = "LESS_THAN"
            neutral.inputs[1].default_value = 0.20
            links.new(separate.outputs[1], neutral.inputs[0])
            bright = nodes.new("ShaderNodeMath")
            bright.operation = "GREATER_THAN"
            bright.inputs[1].default_value = 0.24
            links.new(separate.outputs[2], bright.inputs[0])
            mask = nodes.new("ShaderNodeMath")
            mask.operation = "MULTIPLY"
            links.new(neutral.outputs[0], mask.inputs[0])
            links.new(bright.outputs[0], mask.inputs[1])
            strength = nodes.new("ShaderNodeMath")
            strength.operation = "MULTIPLY"
            strength.inputs[1].default_value = 0.88
            links.new(mask.outputs[0], strength.inputs[0])
            links.new(strength.outputs[0], shader.inputs["Metallic"])
            roughness = 0.30
            shader.inputs["Roughness"].default_value = roughness
            shader.inputs["Anisotropic"].default_value = 0.25
        emission = spec["emission"]
        if max(emission) > 0:
            shader.inputs["Emission Color"].default_value = (*emission, 1)
            shader.inputs["Emission Strength"].default_value = 4.0 if luminance > 0.4 else 1.5
        if spec["emission_texture"]:
            shader.inputs["Emission Strength"].default_value = 1.4
        if not spec["emission_texture"] and max(emission) < 0.5:
            texture_coordinate = nodes.new("ShaderNodeTexCoord")
            noise = nodes.new("ShaderNodeTexNoise")
            noise.inputs["Scale"].default_value = 180.0 if metallic > 0.65 else 90.0
            noise.inputs["Detail"].default_value = 2.0
            links.new(texture_coordinate.outputs["Object"], noise.inputs["Vector"])
            bump = nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.16
            bump.inputs["Distance"].default_value = 0.00010 if metallic > 0.65 else 0.00025
            links.new(noise.outputs["Fac"], bump.inputs["Height"])
            if metallic > 0.2 and not spec["base_texture"]:
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
        canonical[signature] = mat
        materials[spec["id"]] = mat

    mesh_parts = {}
    verified_meshes = []
    normal_cache = {}
    for mesh_spec in source["meshes"]:
        parts = []
        for primitive in mesh_spec["parts"]:
            key = primitive["key"]
            vertices = geometry[key + "_vertices"]
            faces = geometry[key + "_faces"]
            mesh = bpy.data.meshes.new(key)
            mesh.vertices.add(len(vertices))
            mesh.vertices.foreach_set("co", vertices.ravel())
            mesh.loops.add(faces.size)
            mesh.loops.foreach_set("vertex_index", faces.ravel())
            mesh.polygons.add(len(faces))
            mesh.polygons.foreach_set("loop_start", np.arange(len(faces), dtype=np.int32) * 3)
            mesh.polygons.foreach_set("loop_total", np.full(len(faces), 3, dtype=np.int32))
            mesh.update(calc_edges=True)
            if key + "_normals" in geometry:
                mesh.polygons.foreach_set("use_smooth", np.ones(len(faces), dtype=bool))
                normals = geometry[key + "_normals"]
                material_spec = source["materials"][primitive["material"]]
                if material_spec["alpha_mode"] == "BLEND" and material_spec["base_texture"]:
                    signature = primitive["vertices_sha256"]
                    if signature not in normal_cache:
                        normal_cache[signature] = smooth_cad_normals(vertices, normals)
                    normals = normal_cache[signature]
                mesh.normals_split_custom_set_from_vertices(normals.tolist())
            if key + "_uv" in geometry:
                layer = mesh.uv_layers.new(name="Original_UV")
                layer.data.foreach_set("uv", geometry[key + "_uv"][faces.ravel()].ravel())
            mesh.materials.append(materials[primitive["material"]])
            mesh["source_primitive"] = key
            actual_vertices = np.empty(vertices.shape, dtype=np.float32)
            mesh.vertices.foreach_get("co", actual_vertices.ravel())
            actual_indices = np.empty(faces.size, dtype=np.int32)
            mesh.loops.foreach_get("vertex_index", actual_indices)
            same = (
                hashlib.sha256(actual_vertices.tobytes()).hexdigest() == primitive["vertices_sha256"]
                and hashlib.sha256(actual_indices.tobytes()).hexdigest() == primitive["faces_sha256"]
            )
            if not same:
                raise RuntimeError(f"Geometry changed during transfer: {key}")
            verified_meshes.append(key)
            parts.append(mesh)
        mesh_parts[mesh_spec["id"]] = parts
    print(
        f"MESHES_READY primitives={len(verified_meshes)} elapsed={time.monotonic() - started:.1f}",
        flush=True,
    )

    source_objects = []
    for record in source["nodes"]:
        index = record["id"]
        parent = bpy.data.objects.new(f"source_{index:04d}", None)
        collection = collections[record["equipment"]]
        collection.objects.link(parent)
        parent["source_node_id"] = index
        parent["equipment_id"] = record["equipment"]
        parent["original_name"] = record["name"]
        parent.matrix_world = Matrix(poses[0, index])
        parent.empty_display_size = 0.025
        for mesh in mesh_parts[record["mesh"]]:
            obj = bpy.data.objects.new(f"{parent.name}_{mesh.name}", mesh)
            collection.objects.link(obj)
            obj.parent = parent
            obj.matrix_parent_inverse = Matrix.Identity(4)
            obj.matrix_basis = Matrix.Identity(4)
            obj["equipment_id"] = record["equipment"]
        if motion["moving"][index]:
            add_action(parent, poses[:, index], frames)
        source_objects.append(parent)
        if index % 200 == 0:
            print(
                f"ANIMATION {index}/{len(source['nodes'])} elapsed={time.monotonic() - started:.1f}",
                flush=True,
            )

    lighting = bpy.data.collections.new("Rendering_lights_original_positions")
    scene.collection.children.link(lighting)
    for spec in source["lights"]:
        kind = "SPOT" if spec["type"] == "SpotLight" else "POINT" if spec["type"] == "PointLight" else "SUN"
        lamp = bpy.data.lights.new(f"original_light_{spec['id']:02d}", kind)
        lamp.color = spec["color"]
        lamp.energy = spec["intensity"] * (3.5 if kind == "SPOT" else 15.0 if kind == "POINT" else 1.0)
        if kind in ("SPOT", "POINT"):
            lamp.shadow_soft_size = 0.75 if kind == "SPOT" else 0.40
        if kind == "SPOT":
            lamp.spot_size = spec["outer_cone"] * 2
            lamp.spot_blend = 0.65
        obj = bpy.data.objects.new(lamp.name, lamp)
        lighting.objects.link(obj)
        obj.matrix_world = Matrix(spec["matrix"])

    add_review_cameras(scene, motion, frames)

    maximum_error, frame_errors = verify_transfer(scene, source_objects, poses)
    report = {
        "scope": (
            "Transfer of the OP010 revised scene export into Blender; "
            "comparison is to the revised export, not the unmodified v3 geometry"
        ),
        "mesh_primitives_verified_bit_exact": len(verified_meshes),
        "source_node_count": len(source_objects),
        "node_additions": 0,
        "node_removals": 0,
        "geometry_modifiers": 0,
        "displacement": "none; shader bump and bevel affect normals only",
        "cad_shading_normals": "Smooth coincident CAD corners below 35 degrees; original vertices and faces unchanged",
        "frame_transform_checks": frame_errors,
        "maximum_matrix_element_error": maximum_error,
        "all_checked_matrix_elements_within_2e_minus_5": maximum_error <= 2e-5,
        "animation": "788 revised scene poses at 30 fps; no optical-flow interpolation",
        "hardware_layout": "Equipment preservation is checked separately against the v3 baseline",
    }
    write_json(ROOT / "audit/blender_transfer_checks.json", report)
    scene.frame_set(1)
    scene.render.filepath = str(ROOT / "output/frame_0001.png")
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "UR15_OP010_revision.blend"), compress=True)
    print(
        f"BLEND_READY elapsed={time.monotonic() - started:.1f} max_transform_error={maximum_error:.9g}",
        flush=True,
    )


if __name__ == "__main__":
    main()
