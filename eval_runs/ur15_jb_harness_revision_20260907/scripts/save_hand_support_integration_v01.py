# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Save static integral-support candidates and sample detached service offsets [m]."""

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
import save_hand_mount_relief_v01 as relief  # noqa: E402
import save_hand_pad_service_v01 as service  # noqa: E402


def main() -> None:
    """Create a fresh native and observe geometry without a physical verdict."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    directory = args.directory
    target = directory / "hand_support_integration_v01.blend"
    if target.exists():
        raise FileExistsError(target)
    source = directory / "hand_support_integration_meshes_v01.json"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    payload = json.loads(source.read_text())
    observations = json.loads((directory / "hand_support_integration_observations_v01.json").read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    initial = bpy.context.scene
    base._scenes(payload)
    for scene in bpy.data.scenes:
        if scene == initial:
            continue
        focus = Vector((0, 0.058, 0.004))
        scene.camera.location = (0.16, -0.16, 0.14)
        scene.camera.rotation_euler = (focus - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.camera.data.ortho_scale = 0.19
    bpy.context.window.scene = bpy.data.scenes["J050_near"]
    bpy.data.scenes.remove(initial)
    before = prior._snapshot()
    extraction = {}
    for name in payload["candidates"]:
        settings = {
            "settings": {"service": observations["service_settings"]},
            "service_definitions": observations["candidates"][name]["service_definitions"],
        }
        extraction[name] = service._extraction(bpy.data.scenes[f"{name}_open"], settings)
    assert prior._snapshot() == before, "Read-only sampling changed scene data"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    bpy.ops.wm.open_mainfile(filepath=str(target))
    after = prior._snapshot()
    assert before == after, "Saved support native changed on readback"
    static = {
        name: {state: prior._pairs(bpy.data.scenes[f"{name}_{state}"]) for state in ("near", "early", "open", "clear")}
        for name in payload["candidates"]
    }
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    result = {
        "recorded_at": datetime.now().astimezone().isoformat(),
        "source_sha256": digest,
        "native_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "native_readback_identical": True,
        "readback_fields": ["world matrices", "vertex SHA", "face SHA", "counts", "visibility"],
        "mesh_counts": {name: len(rows) for name, rows in after.items()},
        "static_surface_pairs": static,
        "one_side_service_extraction_samples": extraction,
        "sample_summary": {name: relief._summarize(rows) for name, rows in extraction.items()},
        "source_matrices_never_modified_during_sampling": True,
        "method": "Reused Blender BVHTree epsilon=0 triangle surface overlaps with AABB rejection",
        "offsets_m": observations["service_settings"]["offsets_m"],
        "service_reference_workpiece_excluded": True,
        "service_pair_count_per_sample": "Three moving parts x thirteen fixed parts = 39",
        "screws_and_index_pin_present": False,
        "limits": "Finite samples, no continuous path, solid containment, loaded mechanism or manufacturing verdict",
        "selected_relief_m": None,
        "pad_joint_selected": False,
        "video_created": False,
        "arm_motion_created": False,
        "physical_acceptance_verdict": None,
    }
    (directory / "hand_support_integration_native_v01.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    page = directory / "根元支持部の一体化_v01.html"
    page.write_text(page.read_text().replace("__NATIVE_PAYLOAD__", json.dumps(result, separators=(",", ":"))))
    print(json.dumps(result["sample_summary"], indent=2), flush=True)
    print("HAND_SUPPORT_INTEGRATION_NATIVE_DONE", flush=True)


if __name__ == "__main__":
    main()
