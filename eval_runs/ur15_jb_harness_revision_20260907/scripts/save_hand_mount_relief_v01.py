# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Save plate-relief comparisons and observe the same finite service samples [m]."""

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
import save_hand_pad_service_v01 as service  # noqa: E402
import save_hand_root_clamp_v03 as root  # noqa: E402


def _upper_face_diagnostic(scene, observations):
    rows = {}
    for side, definition in observations["service_definitions"].items():
        carrier = scene.objects[f"{scene.name}__{side}_carrier"]
        hardware = scene.objects[f"{scene.name}__hardware_{side}_inner_finger_0"]
        original = [carrier.matrix_world @ vertex.co for vertex in carrier.data.vertices]
        faces = [tuple(face.vertices) for face in carrier.data.polygons]
        tree = prior._geometry(hardware)[0]
        adjacent = set(observations["candidates"]["R000"]["carriers"][side]["adjacent_face_indices"])
        samples = []
        for offset in observations["service_settings"]["offsets_m"]:
            if not offset:
                continue
            delta = Vector(definition["direction_world"]) * offset
            points = [point + delta for point in original]
            moving = BVHTree.FromPolygons(points, faces, all_triangles=True, epsilon=0.0)
            hits = moving.overlap(tree)
            if hits:
                indices = sorted({a for a, _ in hits})
                samples.append(
                    {
                        "offset_m": offset,
                        "carrier_face_indices": indices,
                        "hardware_face_indices": sorted({b for _, b in hits}),
                        "carrier_faces_all_adjacent_to_upper_edge": set(indices) <= adjacent,
                        "triangle_surface_pairs": len(hits),
                    }
                )
        rows[side] = samples
    return rows


def _summarize(extraction):
    result = {}
    for side, row in extraction.items():
        samples = row["samples"]
        positive = [sample for sample in samples if sample["offset_m"] > 0]
        result[side] = {
            "all_samples": len(samples),
            "all_samples_with_surface_pairs": sum(bool(sample["surface_overlap_pairs"]) for sample in samples),
            "positive_offset_samples": len(positive),
            "positive_offset_samples_with_surface_pairs": sum(
                bool(sample["surface_overlap_pairs"]) for sample in positive
            ),
            "zero_offset_pairs": samples[0]["surface_overlap_pairs"],
            "positive_offsets_with_surface_pairs_m": [
                sample["offset_m"] for sample in positive if sample["surface_overlap_pairs"]
            ],
        }
    return result


def main() -> None:
    """Create an isolated native, verify exact readback and record surface pairs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    directory = args.directory
    target = directory / "hand_mount_relief_v01.blend"
    if target.exists():
        raise FileExistsError(target)
    source = directory / "hand_mount_relief_meshes_v01.json"
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    payload = json.loads(source.read_text())
    observations = json.loads((directory / "hand_mount_relief_observations_v01.json").read_text())
    extraction_settings = {
        "service_definitions": observations["service_definitions"],
        "settings": {"service": observations["service_settings"]},
    }
    bpy.ops.wm.read_factory_settings(use_empty=True)
    initial = bpy.context.scene
    base._scenes(payload)
    for scene in bpy.data.scenes:
        if scene == initial:
            continue
        focus = Vector((0, 0.058, 0.007))
        scene.camera.location = (0.16, -0.16, 0.14)
        scene.camera.rotation_euler = (focus - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.camera.data.ortho_scale = 0.19
    bpy.context.window.scene = bpy.data.scenes["R050_open"]
    bpy.data.scenes.remove(initial)
    before = prior._snapshot()
    extraction = {
        name: service._extraction(bpy.data.scenes[f"{name}_open"], extraction_settings)
        for name in payload["candidates"]
    }
    diagnostic = _upper_face_diagnostic(bpy.data.scenes["R000_open"], observations)
    assert prior._snapshot() == before, "Read-only service observation changed the scene"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    bpy.ops.wm.open_mainfile(filepath=str(target))
    after = prior._snapshot()
    if before != after:
        (directory / "hand_mount_relief_readback_failure.json").write_text(
            json.dumps({"before": before, "after": after})
        )
        raise AssertionError("Relief native changed on readback")
    static = {}
    for name in payload["candidates"]:
        static[name] = {}
        for state in ("near", "early", "open", "clear"):
            scene = bpy.data.scenes[f"{name}_{state}"]
            static[name][state] = prior._pairs(scene)
            static[name][state]["root_parts_vs_mounts"] = root._root_mount_pairs(scene)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_sha
    report = {
        "recorded_at": datetime.now().astimezone().isoformat(),
        "source_sha256": source_sha,
        "native_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "native_readback_identical": True,
        "readback_fields": ["world matrices", "vertex SHA", "face SHA", "counts", "visibility"],
        "mesh_counts": {name: len(rows) for name, rows in after.items()},
        "original_poses_surface_pairs": static,
        "one_side_service_extraction_samples": extraction,
        "sample_summary": {name: _summarize(rows) for name, rows in extraction.items()},
        "baseline_nonzero_offset_face_diagnostic": diagnostic,
        "source_matrices_never_modified_during_sampling": True,
        "method": "Reused Blender BVHTree epsilon=0 triangle surface overlaps with AABB rejection",
        "offsets_m": observations["service_settings"]["offsets_m"],
        "service_reference_workpiece_excluded": True,
        "screws_and_index_pin_present": False,
        "limits": "Finite samples only; no continuous path, containment, tolerance, stress or physical acceptance test",
        "selected_relief_m": None,
        "video_created": False,
        "arm_motion_created": False,
        "physical_acceptance_verdict": None,
    }
    (directory / "hand_mount_relief_native_v01.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    page = directory / "取付上端の逃げ比較_v01.html"
    page.write_text(page.read_text().replace("__NATIVE_PAYLOAD__", json.dumps(report, separators=(",", ":"))))
    print(json.dumps(report["sample_summary"], indent=2), flush=True)
    print("HAND_MOUNT_RELIEF_NATIVE_DONE", flush=True)


if __name__ == "__main__":
    main()
