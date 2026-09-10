# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Shared paths and native Blender animation helpers for OP020 continuous supply."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
V02 = ROOT / "inputs/v02_source"
V01 = V02 / "inputs/v01_source"
for directory in (V01 / "op010_base/scripts", V01 / "scripts", V02 / "scripts"):
    sys.path.insert(0, str(directory))
from build_cameras import original_signature as original_signature  # noqa: E402
from build_op020 import add_action  # noqa: E402
from build_op020 import camera_settings as camera_settings  # noqa: E402
from build_op020 import lighting_snapshot as lighting_snapshot  # noqa: E402
from build_op020 import look_at as look_at  # noqa: E402

FPS = 30
CYCLE_DURATION = 36.0
CYCLE_FRAMES = int(CYCLE_DURATION * FPS)
CYCLE_COUNT = 10
TOTAL_FRAMES = CYCLE_FRAMES * CYCLE_COUNT + 1
GRASP = 2.8
RELEASE = 19.4780185
EXPECTED = "937ac1aece8c9899fed1671845394d0805301ac24408a1f76df1248891a30957"
BLEND = "UR15_OP020_continuous10_v03.blend"


def digest(path: Path) -> str:
    """Return the SHA-256 of a local artifact."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, value: dict) -> None:
    """Write a UTF-8 record without changing its evidence inputs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def delete_tree(obj: bpy.types.Object) -> None:
    """Remove one scene object and its children from the working scene."""
    for child in list(obj.children):
        delete_tree(child)
    bpy.data.objects.remove(obj, do_unlink=True)


def action_world(
    obj: bpy.types.Object,
    poses: np.ndarray,
    frames: np.ndarray,
    *,
    cyclic: bool = False,
) -> None:
    """Bake rigid transforms [m] and optionally repeat one closed native cycle."""
    obj.animation_data_clear()
    add_action(obj, poses, frames)
    if obj.animation_data and obj.animation_data.action:
        action = obj.animation_data.action
        if action.slots:
            obj.animation_data.action_slot = action.slots[0]
        if cyclic:
            if not np.allclose(poses[0], poses[-1], atol=2e-6):
                raise ValueError(f"Cycle endpoints do not match: {obj.name}")
            for curve in action.fcurves:
                curve.modifiers.new("CYCLES")


def visibility_window(obj: bpy.types.Object, start_frame: float, end_frame: float) -> None:
    """Apply a discrete local-cell visibility interval to mesh descendants."""
    meshes = [obj, *obj.children_recursive]
    for child in meshes:
        if child.type not in {"MESH", "FONT"}:
            continue
        for frame, hidden in ((0, True), (start_frame, False), (end_frame, True)):
            child.hide_render = hidden
            child.hide_viewport = hidden
            child.keyframe_insert("hide_render", frame=frame)
            child.keyframe_insert("hide_viewport", frame=frame)
        for curve in child.animation_data.action.fcurves:
            for key in curve.keyframe_points:
                key.interpolation = "CONSTANT"


def clone_mesh_children(template: bpy.types.Object, name: str, properties: dict | None = None) -> bpy.types.Object:
    """Create a rigid assembly reusing the accepted mesh and material datablocks."""
    parent = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(parent)
    for key, value in (properties or {}).items():
        parent[key] = value
    for index, source in enumerate(template.children):
        if source.type != "MESH":
            continue
        child = bpy.data.objects.new(f"{name}_p{index:02d}", source.data)
        bpy.context.scene.collection.objects.link(child)
        child.parent = parent
        child.matrix_basis = source.matrix_basis.copy()
        for key, value in (properties or {}).items():
            child[key] = value
    return parent
