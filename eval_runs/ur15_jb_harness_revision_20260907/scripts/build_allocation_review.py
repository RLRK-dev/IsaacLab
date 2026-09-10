# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Build separate factory-finish and provisional product/rack review scenes."""

from __future__ import annotations

import hashlib
import math
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from allocation_product import (  # noqa: E402
    box,
    build_product,
    material,
    packaging_metrics,
)
from clean_appearance import apply_clean_appearance  # noqa: E402
from continuous_common import (  # noqa: E402
    EXPECTED,
    ROOT,
    camera_settings,
    clone_mesh_children,
    digest,
    lighting_snapshot,
    look_at,
    write_json,
)


def geometry_signature(scene, names=None):
    digestor = hashlib.sha256()
    with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0]):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
    for obj in sorted(scene.objects, key=lambda item: item.name):
        if names is not None and obj.name not in names:
            continue
        digestor.update(obj.name.encode())
        digestor.update(np.asarray(obj.evaluated_get(depsgraph).matrix_world, np.float64).tobytes())
        if obj.type == "MESH":
            vertices = np.empty(len(obj.data.vertices) * 3, np.float32)
            obj.data.vertices.foreach_get("co", vertices)
            digestor.update(vertices.tobytes())
            loops = np.empty(len(obj.data.loops), np.int32)
            obj.data.loops.foreach_get("vertex_index", loops)
            digestor.update(loops.tobytes())
    return digestor.hexdigest()


def camera(scene, name, eye, target, lens=48):
    data = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.matrix_world = look_at(eye, target)
    obj.data.lens = lens
    obj.data.clip_start = 0.01
    scene.camera = obj
    return obj


def review_scene(name, center):
    scene = bpy.data.scenes.new(name)
    bpy.context.window.scene = scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.cycles.device = "GPU"
    scene.render.resolution_x, scene.render.resolution_y = 1600, 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.world = bpy.data.worlds.new(name + "_studio_world")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (
        0.4,
        0.45,
        0.5,
        1,
    )
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.28
    for number, (delta, watts, size) in enumerate(
        (
            ((1.0, -1.4, 2.5), 280, 2.0),
            ((-1.8, 0, 1.7), 210, 1.8),
            ((0, 2.0, 2.8), 350, 2.0),
        )
    ):
        light = bpy.data.lights.new(f"{name}_studio_{number}", "AREA")
        light.energy, light.shape, light.size = watts * 0.45, "DISK", size
        obj = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(obj)
        obj.matrix_world = look_at(np.array(center) + delta, center)
    floor = material("review_floor", (0.50, 0.53, 0.57), roughness=0.65)
    box(
        name + "_review_floor",
        (200, 200, 0.01),
        (center[0], center[1], -0.065),
        floor,
        bevel=0,
    )
    scene["scope"] = "Static packaging review. Not assembly execution or physical-validity certification."
    return scene


def bounds(root):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    values = []
    for obj in root.children_recursive:
        if obj.type not in {"MESH", "CURVE"}:
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        coordinates = np.empty(len(mesh.vertices) * 3, np.float64)
        mesh.vertices.foreach_get("co", coordinates)
        transform = np.asarray(evaluated.matrix_world)
        values.append(coordinates.reshape(-1, 3) @ transform[:3, :3].T + transform[:3, 3])
        evaluated.to_mesh_clear()
    values = np.vstack(values)
    return [values.min(0).tolist(), values.max(0).tolist()]


def build():
    source = ROOT / "inputs/accepted_op020_v02.blend"
    assert digest(source) == EXPECTED
    bpy.ops.wm.open_mainfile(filepath=str(source))
    factory = bpy.context.scene
    factory.name = "Factory_finish_review"
    factory.frame_set(1)
    before_geometry = geometry_signature(factory)
    before_lights = lighting_snapshot(factory)
    eyes = sorted(o.name for o in factory.objects if o.type == "CAMERA" and o.name.startswith("Eye_"))
    before_eyes = camera_settings(eyes)
    assert len(eyes) == 19
    appearance = apply_clean_appearance(factory)
    assert geometry_signature(factory) == before_geometry
    assert lighting_snapshot(factory) == before_lights
    assert camera_settings(eyes) == before_eyes
    factory["review_scope"] = (
        "Factory finishes only. Original OP020 motion; product changes are in separate review scenes."
    )
    factory.camera = bpy.data.objects["OP020_line_overview"]
    factory.render.resolution_x, factory.render.resolution_y = 1600, 1000
    factory.render.resolution_percentage = 100
    factory.cycles.samples = 24
    factory.cycles.device = "GPU"
    factory.render.image_settings.file_format = "PNG"
    overview_camera = factory.camera
    camera(factory, "Factory_finish_detail", (3.2, -6.2, 2.7), (0.1, -3.8, 1.0), 38)
    factory.camera = overview_camera
    template = bpy.data.objects["source_0293"]

    product_scene = review_scene("Product_packaging_review", (0, 0, 0.15))
    open_product = build_product(template, "Open_packaging", stage=3)
    open_product.location = (-0.58, 0, 0)
    closed_product = build_product(template, "Closed_packaging", stage=8)
    closed_product.location = (0.58, 0, 0)
    camera(product_scene, "Packaging_camera", (-1.45, -2.55, 1.9), (0, 0, 0.12), 47)
    bpy.context.view_layer.update()
    products = {obj.name: bounds(obj) for obj in (open_product, closed_product)}

    rack_scene = review_scene("Rack_packaging_review", (2.2, 8.85, 0.75))
    rack = clone_mesh_children(bpy.data.objects["source_1623"], "Existing_rack_preserved")
    rack["source_node_id"] = 1623
    units = []
    for shelf, z in enumerate((0.22, 0.60, 0.98)):
        for column, y in enumerate((8.51, 9.19)):
            product = build_product(template, f"Rack_unit_{shelf + 1}_{column + 1}", stage=8)
            product.rotation_euler.z = math.pi / 2
            product.location = (2.2, y, z + 0.015 + 0.055)
            units.append(product)
    camera(rack_scene, "Rack_camera", (4.4, 6.25, 2.25), (2.2, 8.85, 0.70), 39)
    bpy.context.view_layer.update()
    rack_bounds = {obj.name: bounds(obj) for obj in units}
    metrics = packaging_metrics()
    metrics["actual_product_bounds_m"] = products
    metrics["actual_rack_units_bounds_m"] = rack_bounds
    metrics["rack_source_geometry_reused"] = "source_1623"
    # A shared closed product envelope must clear the next shelf and the frame.
    for index, obj in enumerate(units):
        low, high = np.array(rack_bounds[obj.name])
        assert low[0] >= 1.805 and high[0] <= 2.595, (obj.name, low, high)
        assert low[1] >= 8.142 and high[1] <= 9.558, (obj.name, low, high)
        ceiling = (0.60 - 0.015, 0.98 - 0.015, 1.34)[index // 2]
        assert high[2] < ceiling, (obj.name, high[2], ceiling)
    write_json(ROOT / "audit/packaging_metrics.json", metrics)
    write_json(
        ROOT / "audit/clean_appearance.json",
        {
            **appearance,
            "input_sha256": EXPECTED,
            "source_geometry_signature": before_geometry,
            "source_geometry_unchanged": True,
            "source_lighting_unchanged": True,
            "onhand_camera_count": len(eyes),
            "onhand_camera_settings_unchanged": True,
        },
    )
    bpy.context.window.scene = product_scene
    output = ROOT / "UR15_allocation_geometry_v01.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(output), compress=True)
    write_json(
        ROOT / "audit/allocation_review_build.json",
        {
            "input_sha256": EXPECTED,
            "output_sha256": digest(output),
            "scenes": [factory.name, product_scene.name, rack_scene.name],
            "source_geometry_and_lighting_preserved_in_factory_scene": True,
            "new_process_motion": False,
            "electrical_topology": "awaiting_user_information",
            "production_quality_verdict": None,
        },
    )
    print("ALLOCATION_REVIEW_BUILT", output, flush=True)


if __name__ == "__main__":
    build()
