# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Save static service views and sample a detached finger's extraction [m]."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_hand_fingertip_concepts_v01 as base  # noqa: E402
import save_hand_body_setback_v01 as prior  # noqa: E402
import save_hand_root_clamp_v03 as root  # noqa: E402


def _overlap_pairs(moving, fixed, shapes):
    found = []
    for first in moving:
        a, low_a, high_a = shapes[first.name]
        for second in fixed:
            b, low_b, high_b = shapes[second.name]
            if any(high_a[i] < low_b[i] or high_b[i] < low_a[i] for i in range(3)):
                continue
            pairs = a.overlap(b)
            if pairs:
                found.append(
                    {
                        "moving": first.name.split("__", 1)[1],
                        "fixed": second.name.split("__", 1)[1],
                        "triangle_surface_pairs": len(pairs),
                    }
                )
    return found


def _extraction(scene, report):
    objects = {obj.name.split("__", 1)[1]: obj for obj in scene.objects if obj.get("role") in ("hardware", "insert")}
    points = {obj.name: [obj.matrix_world @ vertex.co for vertex in obj.data.vertices] for obj in objects.values()}
    faces = {obj.name: [tuple(poly.vertices) for poly in obj.data.polygons] for obj in objects.values()}
    rows = {}
    for side, definition in report["service_definitions"].items():
        moving = [objects[name] for name in definition["moving_objects"]]
        fixed = [obj for name, obj in objects.items() if name not in definition["moving_objects"]]
        shapes = {obj.name: prior._geometry(obj) for obj in fixed}
        samples = []
        for offset in report["settings"]["service"]["offsets_m"]:
            delta = Vector(definition["direction_world"]) * offset
            for obj in moving:
                shifted = [point + delta for point in points[obj.name]]
                lower = tuple(min(point[i] for point in shifted) for i in range(3))
                upper = tuple(max(point[i] for point in shifted) for i in range(3))
                tree = BVHTree.FromPolygons(shifted, faces[obj.name], all_triangles=True, epsilon=0.0)
                shapes[obj.name] = tree, lower, upper
            samples.append(
                {
                    "offset_m": offset,
                    "object_pairs_considered": len(moving) * len(fixed),
                    "surface_overlap_pairs": _overlap_pairs(moving, fixed, shapes),
                }
            )
        rows[side] = {"moving_objects": definition["moving_objects"], "samples": samples}
    return rows


def main() -> None:
    """Write an isolated native, check readback and record finite surface samples."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    directory = args.directory
    target = directory / "hand_pad_service_v01.blend"
    if target.exists():
        raise FileExistsError(target)
    source = directory / "hand_pad_service_meshes_v01.json"
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    payload = json.loads(source.read_text())
    input_report = json.loads((directory / "hand_pad_service_observations_v01.json").read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    initial = bpy.context.scene
    base._scenes(payload)
    for scene in bpy.data.scenes:
        if scene == initial:
            continue
        service = "_service_" in scene.name
        scene["scope"] = "Detached service illustration; fasteners absent" if service else "Unchanged D40 static pose"
        for obj in scene.objects:
            if obj.get("role") == "target" and service:
                obj.hide_render = True
                obj.hide_viewport = True
        focus = Vector((0, 0.058, 0.007))
        scene.camera.location = (0.16, -0.16, 0.14)
        scene.camera.rotation_euler = (focus - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.camera.data.ortho_scale = 0.19
    bpy.context.window.scene = bpy.data.scenes["D40_open"]
    bpy.data.scenes.remove(initial)
    before = prior._snapshot()
    extraction = _extraction(bpy.data.scenes["D40_open"], input_report)
    assert prior._snapshot() == before, "Read-only service sampling changed scene data"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    bpy.ops.wm.open_mainfile(filepath=str(target))
    after = prior._snapshot()
    if before != after:
        (directory / "hand_pad_service_readback_failure.json").write_text(
            json.dumps({"before": before, "after": after})
        )
        raise AssertionError("Service native changed on readback")
    static_pairs = {}
    for state in ("near", "early", "open", "clear"):
        scene = bpy.data.scenes[f"D40_{state}"]
        static_pairs[state] = prior._pairs(scene)
        static_pairs[state]["root_parts_vs_mounts"] = root._root_mount_pairs(scene)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_sha
    result = {
        "recorded_at": datetime.now().astimezone().isoformat(),
        "source_sha256": source_sha,
        "native_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "native_readback_identical": True,
        "readback_fields": ["world matrices", "vertex SHA", "face SHA", "counts", "visibility"],
        "mesh_counts": {name: len(rows) for name, rows in after.items()},
        "four_original_poses_surface_pairs": static_pairs,
        "one_side_service_extraction_samples": extraction,
        "source_matrices_never_modified_during_sampling": True,
        "method": "Blender BVHTree epsilon=0 triangle surface overlaps with AABB rejection",
        "sample_step_m": 0.0005,
        "service_workpiece_removed": True,
        "screws_and_index_pin_present": False,
        "limits": "Finite service samples only; no continuous collision proof, solid containment or loaded release",
        "video_created": False,
        "arm_motion_created": False,
        "physical_acceptance_verdict": None,
    }
    (directory / "hand_pad_service_native_v01.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    page = directory / "根元パッドの交換と取付_v01.html"
    page.write_text(page.read_text().replace("__NATIVE_PAYLOAD__", json.dumps(result, separators=(",", ":"))))
    print(json.dumps(result, indent=2), flush=True)
    print("HAND_PAD_SERVICE_NATIVE_DONE", flush=True)


if __name__ == "__main__":
    main()
