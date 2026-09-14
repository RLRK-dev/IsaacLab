# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Save and read back the static sleeve-grasp comparison without moving poses."""

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
    """Write eight static scenes and auxiliary read-only surface observations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    directory = args.directory
    target = directory / "hand_sleeve_clamp_v01.blend"
    if target.exists():
        raise FileExistsError(target)
    source = directory / "hand_sleeve_clamp_meshes_v01.json"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    payload = json.loads(source.read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    initial = bpy.context.scene
    base._scenes(payload)
    for scene in bpy.data.scenes:
        if scene == initial:
            continue
        focus = Vector((0, 0.048, 0.004))
        scene.camera.location = (0.16, -0.16, 0.14)
        scene.camera.rotation_euler = (focus - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.camera.data.ortho_scale = 0.19
    bpy.context.window.scene = bpy.data.scenes["H050_near"]
    bpy.data.scenes.remove(initial)
    before = prior._snapshot()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    bpy.ops.wm.open_mainfile(filepath=str(target))
    after = prior._snapshot()
    assert before == after, "Saved sleeve-clamp geometry changed on readback"
    static = {
        name: {state: prior._pairs(bpy.data.scenes[f"{name}_{state}"]) for state in ("near", "early", "open", "clear")}
        for name in payload["candidates"]
    }
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
        "source_matrices_never_modified_during_sampling": True,
        "method": "Reused Blender BVHTree epsilon=0 triangle surface overlaps with AABB rejection",
        "limits": "Four static poses; no continuous path, solid containment, gripping or torque reaction verdict",
        "selected_relief_m": None,
        "material_and_pad_joint_selected": False,
        "video_created": False,
        "arm_motion_created": False,
        "physical_acceptance_verdict": None,
    }
    (directory / "hand_sleeve_clamp_native_v01.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    page = directory / "黒被覆側クランプ_v01.html"
    page.write_text(page.read_text().replace("__NATIVE_PAYLOAD__", json.dumps(result, separators=(",", ":"))))
    print(json.dumps(result["mesh_counts"], indent=2), flush=True)
    print("HAND_SLEEVE_CLAMP_NATIVE_DONE", flush=True)


if __name__ == "__main__":
    main()
