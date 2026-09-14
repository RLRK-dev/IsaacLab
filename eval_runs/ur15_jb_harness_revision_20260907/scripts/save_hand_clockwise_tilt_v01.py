# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Save and read back static zero/15-degree hand scenes without changing poses."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_hand_fingertip_concepts_v01 as base  # noqa: E402
import save_hand_body_setback_v01 as prior  # noqa: E402


def main() -> None:
    """Save sixteen static scenes and read-only surface-pair observations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    directory = args.directory
    target = directory / "hand_clockwise_tilt_v01.blend"
    if target.exists():
        raise FileExistsError(target)
    source = directory / "hand_clockwise_tilt_meshes_v01.json"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    payload = json.loads(source.read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    initial = bpy.context.scene
    base._scenes(payload)
    for scene in bpy.data.scenes:
        if scene == initial:
            continue
        focus = Vector((0, 0.060, 0.075))
        scene.camera.location = (0.4, 0.060, 0.075)
        scene.camera.rotation_euler = (focus - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.camera.data.ortho_scale = 0.23
    bpy.context.window.scene = bpy.data.scenes["T050_near"]
    bpy.data.scenes.remove(initial)
    before = prior._snapshot()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    bpy.ops.wm.open_mainfile(filepath=str(target))
    after = prior._snapshot()
    assert before == after, "Static tilt geometry changed on readback"
    static = {
        name: {state: prior._pairs(bpy.data.scenes[f"{name}_{state}"]) for state in candidate["states"]}
        for name, candidate in payload["candidates"].items()
    }
    for name, source_name in payload["clockwise_tilt_settings"]["candidates"].items():
        for state, groups in static[name].items():
            for label, group in groups.items():
                baseline = {
                    (row["first"], row["second"]) for row in static[source_name][state][label]["surface_overlap_pairs"]
                }
                group["additional_object_pairs_vs_source"] = [
                    row for row in group["surface_overlap_pairs"] if (row["first"], row["second"]) not in baseline
                ]
    assert after == prior._snapshot(), "Read-only surface sampling changed scene data"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    result = {
        "recorded_at": datetime.now().astimezone().isoformat(),
        "source_sha256": digest,
        "native_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "native_readback_identical": True,
        "readback_fields": ["world matrices", "vertex SHA", "face SHA", "counts", "visibility"],
        "mesh_counts": {name: len(rows) for name, rows in after.items()},
        "static_surface_pairs": static,
        "scene_unchanged_by_surface_sampling": True,
        "method": "Reused Blender BVHTree epsilon=0 triangle surface overlaps with AABB rejection",
        "limits": "Four static poses per candidate; no continuous path, solid containment, grip or torque verdict",
        "arm_motion_created": False,
        "video_created": False,
        "physical_acceptance_verdict": None,
    }
    (directory / "hand_clockwise_tilt_native_v01.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(result["mesh_counts"], indent=2), flush=True)
    print("HAND_CLOCKWISE_TILT_NATIVE_DONE", flush=True)


if __name__ == "__main__":
    main()
