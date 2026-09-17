# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Save and read back two isolated PGE comparison layouts [m]."""

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_hand_fingertip_concepts_v01 import _camera, _lighting, _mesh_data  # noqa: E402
from save_hand_body_setback_v01 import _snapshot  # noqa: E402


def _scenes(payload: dict) -> None:
    meshes = _mesh_data(payload)
    candidate = payload["candidates"]["PGE_SAMPLE"]
    for state, snapshot in candidate["states"].items():
        scene = bpy.data.scenes.new(f"PGE_SAMPLE_{state}")
        scene.unit_settings.system = "METRIC"
        scene["scope"] = "Isolated nominal contour sample; no force, arm motion or manufacturing verdict"
        scene["opening_per_jaw_m"] = snapshot["opening_per_jaw_m"]
        for name, obj in candidate["objects"].items():
            item = bpy.data.objects.new(f"{scene.name}__{name}", meshes["PGE_SAMPLE", name])
            scene.collection.objects.link(item)
            item.matrix_world = Matrix(snapshot["transforms"][name])
            item["role"] = obj["category"]
            item["rigid_finger"] = obj["rigid_finger"]
        _camera(scene)
        _lighting(scene)
        focus = Vector((0, 0.046, 0.050))
        scene.camera.location = (0.16, -0.17, 0.12)
        scene.camera.rotation_euler = (focus - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.camera.data.ortho_scale = 0.245
        scene.render.engine = "CYCLES"
        scene.cycles.device = "CPU"
        scene.cycles.samples = 24
        scene.cycles.use_denoising = True
        scene.render.threads_mode = "FIXED"
        scene.render.threads = 6
        scene.render.resolution_x = 1000
        scene.render.resolution_y = 900
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.view_settings.view_transform = "AgX"


def main() -> None:
    """Create a new native and static previews without opening the production scene."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    directory = args.directory.resolve()
    target = directory / "hvjb_pge_finger_v01.blend"
    if target.exists():
        raise FileExistsError(target)
    source = directory / "hvjb_pge_finger_v01_meshes.json.gz"
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    payload = json.loads(gzip.decompress(source.read_bytes()))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    initial = bpy.context.scene
    _scenes(payload)
    bpy.context.window.scene = bpy.data.scenes["PGE_SAMPLE_contour"]
    bpy.data.scenes.remove(initial)
    before = _snapshot()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    bpy.ops.wm.open_mainfile(filepath=str(target))
    after = _snapshot()
    if before != after:
        raise AssertionError("Saved matrices, mesh geometry or visibility changed on readback")
    previews = {}
    for name in sorted(after):
        scene = bpy.data.scenes[name]
        bpy.context.window.scene = scene
        scene.render.filepath = str(directory / f"{name}.png")
        bpy.ops.render.render(write_still=True, scene=name)
        path = Path(scene.render.filepath)
        previews[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        print("PGE_STATIC_PREVIEW_WRITTEN", name, flush=True)
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_sha:
        raise AssertionError("Source geometry changed")
    report = {
        "native_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "source_mesh_payload_sha256": source_sha,
        "native_readback_identical": True,
        "readback_fields": ["world matrices", "vertex SHA", "face SHA", "mesh counts", "visibility"],
        "mesh_counts": {name: len(objects) for name, objects in after.items()},
        "previews": previews,
        "production_native_opened": False,
        "video_created": False,
        "physical_acceptance_verdict": None,
    }
    (directory / "hvjb_pge_finger_v01_native.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PGE_NATIVE_READBACK_IDENTICAL", flush=True)


if __name__ == "__main__":
    main()
