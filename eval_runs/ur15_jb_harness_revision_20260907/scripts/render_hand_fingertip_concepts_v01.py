# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Save and render isolated fingertip comparison scenes [m].

Only static scenes are created. This renderer never opens the production native
and does not encode videos or create arm trajectories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


def _material(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    node = mat.node_tree.nodes.get("Principled BSDF")
    rgb = [(c / 255) ** 2.2 for c in color[:3]]
    node.inputs["Base Color"].default_value = (*rgb, 1)
    node.inputs["Metallic"].default_value = 0.25 if name == "hardware" else 0.05
    node.inputs["Roughness"].default_value = 0.42
    mat.diffuse_color = (*rgb, 1)
    return mat


def _camera(scene):
    data = bpy.data.cameras.new(scene.name + "_camera")
    camera = bpy.data.objects.new(scene.name + "_camera", data)
    scene.collection.objects.link(camera)
    camera.location = (0.205, -0.26, 0.19)
    camera.rotation_euler = (Vector((0, 0, 0.062)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    data.type = "ORTHO"
    data.ortho_scale = 0.245
    data.clip_start = 0.0001
    data.clip_end = 10
    scene.camera = camera


def _lighting(scene):
    world = bpy.data.worlds.new(scene.name + "_world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.85, 0.9, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.25
    scene.world = world
    for index, (location, energy, size) in enumerate(
        [
            ((0.1, -0.25, 0.32), 0.8, 0.25),
            ((-0.2, 0.1, 0.18), 0.4, 0.18),
            ((0.18, 0.22, 0.24), 0.6, 0.2),
        ]
    ):
        light = bpy.data.lights.new(f"{scene.name}_light_{index}", "AREA")
        light.energy, light.shape, light.size = energy, "DISK", size
        obj = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(obj)
        obj.location = location
        obj.rotation_euler = (Vector((0, 0, 0.06)) - obj.location).to_track_quat("-Z", "Y").to_euler()


def _mesh_data(payload):
    result = {}
    materials = {}
    for kind, candidate in payload["candidates"].items():
        for name, obj in candidate["objects"].items():
            if obj["category"] == "guide":
                continue
            data = bpy.data.meshes.new(f"{kind}_{name}")
            data.from_pydata(obj["vertices"], [], obj["faces"])
            data.update()
            key = (obj["category"], tuple(obj["color"]))
            if key not in materials:
                materials[key] = _material(obj["category"], obj["color"])
            data.materials.append(materials[key])
            result[kind, name] = data
    return result


def _scenes(payload):
    meshes = _mesh_data(payload)
    for kind, candidate in payload["candidates"].items():
        for state, snapshot in candidate["states"].items():
            scene = bpy.data.scenes.new(f"{kind}_{state}")
            scene.unit_settings.system = "METRIC"
            scene["scope"] = "static concept / no physical verdict / provisional target dimensions"
            scene["source_gripper_q_rad"] = snapshot["joint_q_rad"]
            for name, obj in candidate["objects"].items():
                if obj["category"] == "guide":
                    continue
                item = bpy.data.objects.new(f"{scene.name}__{name}", meshes[kind, name])
                scene.collection.objects.link(item)
                item.matrix_world = Matrix(snapshot["transforms"][name])
                item["role"] = obj["category"]
            _camera(scene)
            _lighting(scene)
            scene.render.engine = "CYCLES"
            scene.cycles.device = "CPU"
            scene.cycles.samples = 24
            scene.cycles.use_denoising = True
            scene.render.threads_mode = "FIXED"
            scene.render.threads = 6
            scene.render.resolution_x = 1200
            scene.render.resolution_y = 900
            scene.render.resolution_percentage = 100
            scene.render.image_settings.file_format = "PNG"
            scene.render.film_transparent = False
            scene.view_settings.view_transform = "AgX"


def _snapshot():
    for scene in bpy.data.scenes:
        for layer in scene.view_layers:
            layer.update()
    return {
        scene.name: {
            obj.name: {
                "matrix": [list(row) for row in obj.matrix_world],
                "vertices": len(obj.data.vertices),
                "polygons": len(obj.data.polygons),
                "vertex_sha": hashlib.sha256(json.dumps([list(v.co) for v in obj.data.vertices]).encode()).hexdigest(),
            }
            for obj in scene.objects
            if obj.type == "MESH"
        }
        for scene in bpy.data.scenes
    }


def main() -> None:
    """Create the static native, PNG previews and readback record."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    target = args.directory / "hand_fingertip_concepts_v01.blend"
    if target.exists():
        raise FileExistsError(target)
    payload = json.loads((args.directory / "hand_fingertip_meshes_v01.json").read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    initial = bpy.context.scene
    _scenes(payload)
    bpy.context.window.scene = bpy.data.scenes["A_near"]
    bpy.data.scenes.remove(initial)
    bpy.context.view_layer.update()
    before = _snapshot()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    bpy.ops.wm.open_mainfile(filepath=str(target))
    after = _snapshot()
    if before != after:
        failure = args.directory / "native_readback_differences_v01.json"
        failure.write_text(json.dumps({"before": before, "after": after}, indent=2) + "\n")
        raise AssertionError("Static native readback changed matrices, mesh counts or vertex data")
    rendered = []
    for name in ("A_near", "A_open", "B_near", "B_open"):
        scene = bpy.data.scenes[name]
        bpy.context.window.scene = scene
        scene.render.filepath = str(args.directory / f"{name}_v01.png")
        bpy.ops.render.render(write_still=True, scene=name)
        rendered.append(Path(scene.render.filepath).name)
        print("STATIC_PREVIEW_WRITTEN", name, flush=True)
    report = {
        "native": target.name,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "native_readback_identical": before == after,
        "static_scene_names": sorted(after),
        "mesh_objects_per_scene": {name: len(objects) for name, objects in after.items()},
        "previews": rendered,
        "tool_envelopes": "viewer-only guide meshes, excluded from native and GLB",
        "video_created": False,
        "physical_acceptance_verdict": None,
    }
    (args.directory / "hand_fingertip_native_observations_v01.json").write_text(json.dumps(report, indent=2) + "\n")
    print("HAND_FINGERTIP_NATIVE_READBACK_AND_PREVIEWS_DONE", flush=True)


if __name__ == "__main__":
    main()
