# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Save, read back and inspect static terminal-fixture scenes [m]."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_hand_fingertip_concepts_v01 as base  # noqa: E402


def _snapshot():
    visibility = {obj.name: obj.hide_viewport for obj in bpy.data.objects if obj.type == "MESH"}
    try:
        # Disabled objects may retain an unevaluated identity matrix after loading.
        # Evaluate their stored transforms without assigning or relaxing matrix values.
        for name in visibility:
            bpy.data.objects[name].hide_viewport = False
        result = base._snapshot()
    finally:
        for name, hidden in visibility.items():
            bpy.data.objects[name].hide_viewport = hidden
    for scene, records in result.items():
        for name, record in records.items():
            obj = bpy.data.objects[name]
            record["hide_render"] = obj.hide_render
            record["hide_viewport"] = visibility[name]
            record["face_sha256"] = hashlib.sha256(
                json.dumps([list(p.vertices) for p in obj.data.polygons]).encode()
            ).hexdigest()
    return result


def _geometry(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    faces = [tuple(poly.vertices) for poly in obj.data.polygons]
    lower = tuple(min(p[a] for p in points) for a in range(3))
    upper = tuple(max(p[a] for p in points) for a in range(3))
    return BVHTree.FromPolygons(points, faces, all_triangles=True, epsilon=0.0), lower, upper


def _pair_observations(scene):
    visible = [obj for obj in scene.objects if obj.type == "MESH" and not obj.hide_render]
    shapes = {obj.name: _geometry(obj) for obj in visible}
    fixtures = [obj for obj in visible if obj.get("role") == "fixture"]
    hands = [obj for obj in visible if obj.get("role") in ("hardware", "insert")]
    terminals = [obj for obj in visible if obj.name.endswith(("reference_lug_6R6_uncrimped", "illustrative_sleeve"))]
    categories = {
        "fixture_vs_hand": [(f, h) for f in fixtures for h in hands],
        "saddle_vs_reference_terminal": [
            (f, t) for f in fixtures if f.name.endswith(("lower_saddle", "upper_saddle")) for t in terminals
        ],
    }
    result = {}
    for group, pairs in categories.items():
        intersections = []
        for first, second in pairs:
            a, a_lower, a_upper = shapes[first.name]
            b, b_lower, b_upper = shapes[second.name]
            if any(a_upper[axis] < b_lower[axis] or b_upper[axis] < a_lower[axis] for axis in range(3)):
                continue
            overlap = a.overlap(b)
            if overlap:
                intersections.append({"first": first.name, "second": second.name, "triangle_pairs": len(overlap)})
        result[group] = {"object_pairs_considered": len(pairs), "surface_overlap_pairs": intersections}
    return result


def _preview(directory, name, detail):
    scene = bpy.data.scenes[name]
    bpy.context.window.scene = scene
    if detail:
        for obj in scene.objects:
            if obj.get("role") == "hardware":
                obj.hide_render = True
        focus = Vector((0, 0.041, -0.003))
        scene.camera.location = (0.125, -0.140, 0.110)
        scene.camera.data.ortho_scale = 0.155
        if name.endswith("unlatch"):
            focus.z = 0.020
            scene.camera.data.ortho_scale = 0.240
    else:
        focus = Vector((0, 0.045, 0.050))
        scene.camera.location = (0.210, -0.240, 0.200)
        scene.camera.data.ortho_scale = 0.270
    scene.camera.rotation_euler = (focus - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
    path = directory / f"{name}{'_detail' if detail else '_context'}_v01.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True, scene=name)
    print("RETAINER_PREVIEW_WRITTEN", path.name, flush=True)
    return path.name


def main() -> None:
    """Write a new native without opening the production line scene."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    native = args.directory / "pallet_terminal_retainer_v01.blend"
    if native.exists():
        raise FileExistsError(native)
    payload = json.loads((args.directory / "pallet_terminal_retainer_meshes_v01.json").read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    initial = bpy.context.scene
    base._scenes(payload)
    for kind, candidate in payload["candidates"].items():
        for name, state in candidate["states"].items():
            scene = bpy.data.scenes[f"{kind}_{name}"]
            for hidden in state["hidden_objects"]:
                obj = scene.objects[f"{scene.name}__{hidden}"]
                obj.hide_render = obj.hide_viewport = True
    bpy.context.window.scene = bpy.data.scenes["CAP_clamp"]
    bpy.data.scenes.remove(initial)
    before = _snapshot()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(native))
    bpy.ops.wm.open_mainfile(filepath=str(native))
    after = _snapshot()
    if before != after:
        (args.directory / "retainer_readback_difference_v01.json").write_text(
            json.dumps({"before": before, "after": after}, indent=2) + "\n"
        )
        raise AssertionError("Static retainer native changed on readback")
    pairs = {name: _pair_observations(bpy.data.scenes[name]) for name in sorted(after)}
    report = {
        "native_sha256": hashlib.sha256(native.read_bytes()).hexdigest(),
        "native_readback_identical": True,
        "readback_fields": ["world matrices", "vertex SHA", "face SHA", "mesh counts", "visibility"],
        "snapshot_evaluation": "temporarily enable all meshes in viewports, evaluate, then restore original flags",
        "mesh_counts": {name: len(records) for name, records in after.items()},
        "surface_observations": pairs,
        "method": "Blender BVHTree triangle surfaces, epsilon=0; axis-aligned bounds reject disjoint pairs",
        "scope": "only visible hand vs fixture, and saddles vs reference lug/sleeve; five discrete poses per candidate",
        "limitations": (
            "surface overlap is not signed clearance, solid containment, continuous motion or physical validity"
        ),
        "all_other_pairs": "not evaluated; support interfaces and hinge joints are not included",
        "physical_acceptance_verdict": None,
    }
    # Write observations before previews; preview-only changes are not saved into native.
    path = args.directory / "pallet_terminal_retainer_native_v01.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                name: {group: len(values["surface_overlap_pairs"]) for group, values in groups.items()}
                for name, groups in pairs.items()
            },
            indent=2,
        ),
        flush=True,
    )
    previews = [_preview(args.directory, "CAP_clamp", False)]
    previews.extend(_preview(args.directory, name, True) for name in ("CAP_clamp", "CAP_c_access", "CAP_unlatch"))
    report["previews"] = previews
    report["preview_note"] = "Detail PNG hides original hand hardware; fingers remain unless the state hides the hand."
    report["video_created"] = False
    path.write_text(json.dumps(report, indent=2) + "\n")
    print("PALLET_TERMINAL_RETAINER_READBACK_DONE", flush=True)


if __name__ == "__main__":
    main()
