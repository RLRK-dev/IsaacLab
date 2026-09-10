# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Apply neutral factory finishes while preserving geometry and light outputs."""

from __future__ import annotations

import bpy

PAINT = {
    "122": (0.76, 0.77, 0.78, 1.0),  # Satin white covers and pedestal paint.
    "124": (0.81, 0.82, 0.83, 1.0),
    "428": (0.72, 0.73, 0.74, 1.0),  # Controller enclosures.
    "948": (0.70, 0.71, 0.73, 1.0),  # Existing roof panels.
    "142": (0.61, 0.63, 0.65, 1.0),  # Duct sheet metal.
}


def _floor_nodes(material: bpy.types.Material) -> None:
    """Change the procedural floor finish; preserve its packed marking texture."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes.get("Principled BSDF")
    original = shader.inputs["Base Color"].links[0].from_socket
    hsv = nodes.new("ShaderNodeSeparateColor")
    hsv.mode = "HSV"
    links.new(original, hsv.inputs["Color"])

    def threshold(socket, operation, value):
        node = nodes.new("ShaderNodeMath")
        node.operation = operation
        links.new(socket, node.inputs[0])
        node.inputs[1].default_value = value
        return node.outputs[0]

    def multiply(left, right):
        node = nodes.new("ShaderNodeMath")
        node.operation = "MULTIPLY"
        links.new(left, node.inputs[0])
        links.new(right, node.inputs[1])
        return node.outputs[0]

    # Exclude yellow markings, dark joints and white lettering. The source image
    # stays packed and byte-for-byte unchanged; no raster reference is edited.
    mask = multiply(
        threshold(hsv.outputs[1], "LESS_THAN", 0.10),
        multiply(
            threshold(hsv.outputs[2], "GREATER_THAN", 0.10),
            threshold(hsv.outputs[2], "LESS_THAN", 0.56),
        ),
    )
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 55.0
    noise.inputs["Detail"].default_value = 2.0
    coordinates = nodes.new("ShaderNodeTexCoord")
    links.new(coordinates.outputs["Object"], noise.inputs["Vector"])
    color = nodes.new("ShaderNodeMixRGB")
    color.inputs[1].default_value = (0.535, 0.55, 0.565, 1)
    color.inputs[2].default_value = (0.55, 0.565, 0.58, 1)
    links.new(noise.outputs["Fac"], color.inputs[0])
    mix = nodes.new("ShaderNodeMixRGB")
    mix.name = "Clean floor / preserved source markings"
    links.new(mask, mix.inputs[0])
    links.new(original, mix.inputs[1])
    links.new(color.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], shader.inputs["Base Color"])
    shader.inputs["Metallic"].default_value = 0.06
    shader.inputs["Roughness"].default_value = 0.48


def apply_clean_appearance(scene: bpy.types.Scene) -> dict:
    """Apply a reversible material revision and return exact changed values."""
    changes = []
    for material in bpy.data.materials:
        if not material.use_nodes or not material.users:
            continue
        shader = material.node_tree.nodes.get("Principled BSDF")
        if shader is None:
            continue
        source_id = material.get("source_material_ids")
        if source_id is None:
            continue
        if material.get("clean_appearance_v01"):
            raise ValueError(f"Appearance pass already applied: {material.name}")
        before = {
            name: list(shader.inputs[name].default_value)
            if name == "Base Color"
            else float(shader.inputs[name].default_value)
            for name in ("Base Color", "Metallic", "Roughness")
        }
        changed = False
        if source_id in PAINT:
            shader.inputs["Base Color"].default_value = PAINT[source_id]
            shader.inputs["Metallic"].default_value = 0.06
            shader.inputs["Roughness"].default_value = 0.42 if source_id != "948" else 0.68
            changed = True
        elif source_id == "1":
            _floor_nodes(material)
            changed = True
        elif shader.inputs["Metallic"].default_value >= 0.65:
            shader.inputs["Roughness"].default_value = max(0.36, shader.inputs["Roughness"].default_value)
            changed = True
        if not changed:
            continue
        roughness = shader.inputs["Roughness"].default_value
        for node in material.node_tree.nodes:
            if node.type == "BUMP":
                node.inputs["Strength"].default_value = 0.06
                node.inputs["Distance"].default_value = 0.00008
            elif node.type == "MAP_RANGE" and any(
                link.to_socket == shader.inputs["Roughness"] for output in node.outputs for link in output.links
            ):
                node.inputs["To Min"].default_value = roughness - 0.015
                node.inputs["To Max"].default_value = roughness + 0.015
        material["clean_appearance_v01"] = True
        changes.append(
            {
                "material": material.name,
                "source_id": source_id,
                "before": before,
                "after": {
                    name: list(shader.inputs[name].default_value)
                    if name == "Base Color"
                    else float(shader.inputs[name].default_value)
                    for name in before
                },
            }
        )
    return {
        "revision": "clean_appearance_v01",
        "changed_materials": changes,
        "floor_source_texture_preserved": True,
        "light_output_scale": 0.70,
        "note": "Material pass only. No light, exposure, object transform or mesh modification.",
    }
