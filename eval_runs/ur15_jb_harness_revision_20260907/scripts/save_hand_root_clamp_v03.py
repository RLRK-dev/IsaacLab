# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Save and reload the 40 mm hand and inspect its discrete surface pairs [m]."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_hand_fingertip_concepts_v01 as renderer  # noqa: E402
import save_hand_body_setback_v01 as previous  # noqa: E402


def _root_mount_pairs(scene):
    roots = [obj for obj in scene.objects if "_root_cable_" in obj.name]
    mounts = [obj for obj in scene.objects if obj.get("role") == "hardware" or obj.name.endswith("_carrier")]
    shapes = {obj.name: previous._geometry(obj) for obj in roots + mounts}
    overlaps = []
    for root in roots:
        for mount in mounts:
            a, low_a, high_a = shapes[root.name]
            b, low_b, high_b = shapes[mount.name]
            if any(high_a[i] < low_b[i] or high_b[i] < low_a[i] for i in range(3)):
                continue
            found = a.overlap(b)
            if found:
                overlaps.append({"root": root.name, "mount": mount.name, "triangle_surface_pairs": len(found)})
    return {"object_pairs_considered": len(roots) * len(mounts), "surface_overlap_pairs": overlaps}


def main() -> None:
    """Write four static scenes and compare saved mesh data after reloading."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    source = args.directory / "hand_root_clamp_meshes_v03.json"
    target = args.directory / "hand_root_clamp_v03.blend"
    if target.exists():
        raise FileExistsError(target)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    initial = bpy.context.scene
    renderer._scenes(json.loads(source.read_text()))
    for scene in bpy.data.scenes:
        if scene == initial:
            continue
        focus = Vector((0, 0.048, 0.060))
        scene.camera.location = (0.205, -0.26, 0.19)
        scene.camera.rotation_euler = (focus - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.camera.data.ortho_scale = 0.290
    bpy.context.window.scene = bpy.data.scenes["D40_near"]
    bpy.data.scenes.remove(initial)
    before = previous._snapshot()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    bpy.ops.wm.open_mainfile(filepath=str(target))
    after = previous._snapshot()
    assert before == after, "Saved static mesh data changed"
    pairs = {}
    for name in sorted(after):
        pairs[name] = previous._pairs(bpy.data.scenes[name])
        pairs[name]["root_parts_vs_mounts"] = _root_mount_pairs(bpy.data.scenes[name])
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_sha
    report = {
        "native_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "source_mesh_payload_sha256": source_sha,
        "native_readback_identical": True,
        "readback_fields": ["world matrices", "vertex SHA", "face SHA", "mesh counts", "visibility"],
        "mesh_counts": {name: len(records) for name, records in after.items()},
        "surface_observations": pairs,
        "method": "Blender BVHTree triangle surfaces, epsilon=0; AABB rejection; mounting and pad pairs included",
        "limitations": "Surface contact is recorded, not classified as solid penetration or physical failure",
        "inherited_mount_topology": "Source v02 includes zero-area tessellation faces and mount surface overlaps",
        "comparison_cylinders": "Shown in HTML only; absent from native and GLB",
        "continuous_motion_checked": False,
        "physical_acceptance_verdict": None,
    }
    (args.directory / "hand_root_clamp_native_v03.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(pairs, indent=2), flush=True)
    print("HAND_ROOT_CLAMP_NATIVE_DONE", flush=True)


if __name__ == "__main__":
    main()
