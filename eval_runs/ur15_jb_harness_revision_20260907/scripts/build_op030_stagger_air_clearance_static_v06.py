# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Preserve the supported B scene and translate one existing air drop along Y [m]."""

import copy
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_op030_stagger_static_v06 import digest, geometry, snapshot  # noqa: E402

SOURCE = ROOT / "analysis/op030_stagger_supported_static_v06.blend"
SOURCE_SHA = "e197a90c8c804425ee53db98b267ef4f052d945c8d4c7ae92f81e5bc5aef6311"
SOURCE_MANIFEST = ROOT / "audit/op030_stagger_supported_static_v06.json"
OUTPUT = ROOT / "analysis/op030_stagger_air_clearance_static_v06.blend"
MANIFEST = ROOT / "audit/op030_stagger_air_clearance_static_v06.json"
DETAIL = ROOT / "audit/op030_stagger_air_clearance_static_v06_geometry.json"
MESHES = ROOT / "data/op030_stagger_air_clearance_static_v06_world.npz"
CANDIDATE = ROOT / "audit/op030_air_drop_v06_candidate_03.json"
DROP = [f"Split_bay_1__source_0782_m0209_p{i:02d}" for i in range(4)]


def signature(value: dict) -> str:
    """Return a deterministic signature of an object-state mapping."""
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def main() -> None:
    """Save only the measured four-object displacement and verify its readback [m]."""
    assert digest(SOURCE) == SOURCE_SHA
    assert not any(path.exists() for path in (OUTPUT, MANIFEST, DETAIL, MESHES))
    report = json.loads(CANDIDATE.read_text())
    assert report["source_static_sha256"] == SOURCE_SHA
    assert report["finite_pose_count"] == 975
    assert len(report["candidates"]) == 1
    choice = report["candidates"][0]
    assert not choice["motion_hits"] and not choice["omitted_fixed_aabb_overlaps"]
    # Only the existing drop tube/tee interfaces with the continuous right main may remain.
    assert {(row["drop"], row["fixed"]) for row in choice["static_hits"]} == {
        (DROP[0], "source_0780_m0207_p03"),
        (DROP[1], "source_0780_m0207_p03"),
    }
    delta = np.array([0, choice["delta_y_m"], 0])
    source_manifest_sha = digest(SOURCE_MANIFEST)
    manifest = copy.deepcopy(json.loads(SOURCE_MANIFEST.read_text()))
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = snapshot()
    actual_before = {name: geometry(bpy.data.objects[name]) for name in DROP}
    for name in DROP:
        obj = bpy.data.objects[name]
        assert obj.type == "MESH" and obj.parent is None
        obj.location.y += float(delta[1])
    bpy.context.view_layer.update()
    after = snapshot()
    assert set(before) == set(after)
    retained = {name: row for name, row in before.items() if name not in DROP}
    assert retained == {name: row for name, row in after.items() if name not in DROP}
    records, vertices, faces, vo, mesh_face_offsets = [], [], [], [0], [0]
    for name in DROP:
        old_v, old_f = actual_before[name]
        new_v, new_f = geometry(bpy.data.objects[name])
        assert before[name]["parent"] == after[name]["parent"] is None
        # Local geometry/material signatures must be identical; only translation changes.
        for key in before[name]:
            if key != "world":
                assert before[name][key] == after[name][key], (name, key)
        error = float(np.max(np.abs(new_v - old_v - delta)))
        assert error < 2e-7 and np.array_equal(old_f, new_f)
        records.append(
            dict(
                name=name,
                before=before[name],
                after=after[name],
                actual_rigid_translation_error_m=error,
                before_bounds_m=[old_v.min(0).tolist(), old_v.max(0).tolist()],
                after_bounds_m=[new_v.min(0).tolist(), new_v.max(0).tolist()],
            )
        )
        vertices.append(new_v)
        faces.append(new_f)
        vo.append(vo[-1] + len(new_v))
        mesh_face_offsets.append(mesh_face_offsets[-1] + len(new_f))
    np.savez_compressed(
        MESHES,
        names=DROP,
        vertices=np.concatenate(vertices),
        faces=np.concatenate(faces),
        vertex_offsets=vo,
        face_offsets=mesh_face_offsets,
    )
    binding = dict(
        source=str(SOURCE.relative_to(ROOT)),
        source_sha256=SOURCE_SHA,
        original_center_global_y_m=0.45,
        center_global_y_m=choice["center_y_m"],
        displacement_global_m=delta.tolist(),
        displacement_bank_baseline_m=delta.tolist(),
        objects=DROP,
        records=records,
        unchanged_object_count=len(retained),
        unchanged_object_signature=signature(retained),
        object_count=len(before),
        added_objects=0,
        added_equipment=0,
        local_geometry_unchanged=True,
        parent_unchanged=True,
        retained_main_axis_x_z_m=[1.42, 2.62],
        support="Existing tube and upper tee suspended from continuous right main; no floor stand",
        candidate_check=str(CANDIDATE.relative_to(ROOT)),
        candidate_check_sha256=digest(CANDIDATE),
        finite_pose_count=report["finite_pose_count"],
        full_motion_bank_complete=False,
        formal_physical_validity_verdict=None,
    )
    bpy.context.scene["op030_air_drop_clearance_v06"] = json.dumps(binding)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    saved_sha = digest(OUTPUT)
    bpy.ops.wm.open_mainfile(filepath=str(OUTPUT))
    bpy.context.scene.frame_set(1)
    readback = snapshot()
    assert readback == after
    detail = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        native=str(OUTPUT.relative_to(ROOT)),
        native_sha256=saved_sha,
        builder_sha256=digest(Path(__file__)),
        source=manifest["output"],
        source_sha256=SOURCE_SHA,
        binding=binding,
        readback_object_count=len(readback),
        readback_mismatches=0,
        source_manifest_sha256=source_manifest_sha,
        meshes=str(MESHES.relative_to(ROOT)),
        meshes_sha256=digest(MESHES),
        faces_unchanged=True,
        formal_physical_validity_verdict=None,
    )
    DETAIL.write_text(json.dumps(detail, ensure_ascii=False, indent=2) + "\n")
    manifest.update(
        source=str(SOURCE.relative_to(ROOT)),
        source_sha256=SOURCE_SHA,
        source_manifest=str(SOURCE_MANIFEST.relative_to(ROOT)),
        source_manifest_sha256=source_manifest_sha,
        output=str(OUTPUT.relative_to(ROOT)),
        output_sha256=saved_sha,
        observed_at=detail["observed_at"],
        air_drop_clearance_v06=binding,
    )
    manifest["air_drop_clearance_v06"].update(
        geometry_record=str(DETAIL.relative_to(ROOT)), geometry_record_sha256=digest(DETAIL)
    )
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    assert digest(SOURCE) == SOURCE_SHA and digest(SOURCE_MANIFEST) == source_manifest_sha
    print("STAGGER_AIR_CLEARANCE_SAVED", saved_sha, len(DROP), len(readback), flush=True)


if __name__ == "__main__":
    main()
