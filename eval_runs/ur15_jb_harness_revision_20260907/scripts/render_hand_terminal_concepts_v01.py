# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Save isolated terminal-fingertip scenes and render static comparisons [m]."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

# Blender does not always add the --python file's directory to sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_hand_fingertip_concepts_v01 as base  # noqa: E402


def _preview(directory, scene_name, *, detail):
    scene = bpy.data.scenes[scene_name]
    bpy.context.window.scene = scene
    if detail:
        for obj in scene.objects:
            if obj.get("role") == "hardware":
                obj.hide_render = True
        camera = scene.camera
        camera.location = (0.085, -0.120, 0.070)
        camera.rotation_euler = (Vector((0, 0.028, -0.006)) - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.ortho_scale = 0.120
    else:
        scene.camera.location.y += 0.026
        scene.camera.rotation_euler = (
            (Vector((0, 0.026, 0.062)) - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
        )
    suffix = "" if detail else "_context"
    path = directory / f"{scene_name}{suffix}_v01.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True, scene=scene_name)
    print("TERMINAL_STATIC_PREVIEW_WRITTEN", path.name, flush=True)
    return path.name


def main() -> None:
    """Create a new native and verify mesh/matrix readback before previews."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    target = args.directory / "hand_terminal_concepts_v01.blend"
    if target.exists():
        raise FileExistsError(target)
    payload = json.loads((args.directory / "hand_terminal_meshes_v01.json").read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    initial = bpy.context.scene
    base._scenes(payload)
    bpy.context.window.scene = bpy.data.scenes["GUIDE_near"]
    bpy.data.scenes.remove(initial)
    before = base._snapshot()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    bpy.ops.wm.open_mainfile(filepath=str(target))
    after = base._snapshot()
    if before != after:
        (args.directory / "terminal_native_readback_difference.json").write_text(
            json.dumps({"before": before, "after": after}, indent=2) + "\n"
        )
        raise AssertionError("Terminal static native changed on readback")
    # Native stays unchanged; the following camera/visibility changes are preview-only.
    previews = [_preview(args.directory, "GUIDE_near", detail=False)]
    previews.extend(_preview(args.directory, name, detail=True) for name in ("GUIDE_near", "GUIDE_open", "EDGE_near"))
    report = {
        "native": target.name,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "native_readback_identical": before == after,
        "static_scene_names": sorted(after),
        "mesh_objects_per_scene": {name: len(objects) for name, objects in after.items()},
        "previews": previews,
        "preview_visibility": "detail PNGs hide reused hardware; context PNG and all native scenes include it",
        "tool_access_guide": "viewer only, excluded from native and GLB",
        "video_created": False,
        "physical_acceptance_verdict": None,
    }
    (args.directory / "hand_terminal_native_observations_v01.json").write_text(json.dumps(report, indent=2) + "\n")
    print("HAND_TERMINAL_NATIVE_READBACK_AND_PREVIEWS_DONE", flush=True)


if __name__ == "__main__":
    main()
