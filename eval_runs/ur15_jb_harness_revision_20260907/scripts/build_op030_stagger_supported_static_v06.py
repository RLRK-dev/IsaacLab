# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Extend only existing B lower supports to the retained floor plane [m]."""

import copy
import json
import sys
from datetime import datetime
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_op030_split_v04 import _welded_components, _world_vertices  # noqa: E402
from build_op030_stagger_static_v06 import digest, geometry, snapshot  # noqa: E402

SOURCE = ROOT / "analysis/op030_stagger_static_v06.blend"
SOURCE_SHA = "afb6428ae60ff87d845badaf34106227d04873b1b01940d131d39bdd6d220f59"
SOURCE_MANIFEST = ROOT / "audit/op030_stagger_static_v06.json"
OUTPUT = ROOT / "analysis/op030_stagger_supported_static_v06.blend"
MANIFEST = ROOT / "audit/op030_stagger_supported_static_v06.json"
DETAIL = ROOT / "audit/op030_stagger_supported_static_v06_geometry.json"
MESHES = ROOT / "data/op030_stagger_supported_static_v06_meshes.npz"
FLOOR_Z = -0.033


def extend_lower(obj: bpy.types.Object, indices: np.ndarray, target_low: float) -> dict:
    """Extend selected solid downward, preserving upper surface and width [m]."""
    old = np.array([v.co[:] for v in obj.data.vertices])
    world = _world_vertices(obj)
    points = world[indices].copy()
    low, high = points.min(0), points.max(0)
    points[:, 2] = high[2] + (points[:, 2] - high[2]) * (high[2] - target_low) / (high[2] - low[2])
    inverse = np.linalg.inv(np.asarray(obj.matrix_world))
    local = points @ inverse[:3, :3].T + inverse[:3, 3]
    obj.data = obj.data.copy()
    for index, value in zip(indices, local):
        obj.data.vertices[int(index)].co = value
    obj.data.update()
    read = np.array([v.co[:] for v in obj.data.vertices])
    retained = np.ones(len(read), dtype=bool)
    retained[indices] = False
    assert np.array_equal(read[retained], old[retained])
    return dict(
        name=obj.name,
        kind="downward_extension",
        selected_vertex_indices=indices.tolist(),
        before_bounds_m=[low.tolist(), high.tolist()],
        target_low_m=target_low,
        after_bounds_m=[points.min(0).tolist(), points.max(0).tolist()],
        retained_local_vertices=int(retained.sum()),
        retained_local_vertex_error=0.0,
    )


def main() -> None:
    """Save a separate supported candidate and actual changed-surface export."""
    assert digest(SOURCE) == SOURCE_SHA
    assert not any(p.exists() for p in (OUTPUT, MANIFEST, DETAIL, MESHES))
    source_manifest_sha = digest(SOURCE_MANIFEST)
    manifest = copy.deepcopy(json.loads(SOURCE_MANIFEST.read_text()))
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = snapshot()
    records, feet, legs = [], [], []
    for x in (-2.22, -1.94):
        for y in (-2.12, -1.28):
            foot = bpy.data.objects[f"OP030B_wire_supply_foot_{x}_{y}"]
            leg = bpy.data.objects[f"OP030B_wire_supply_leg_{x}_{y}"]
            points, _ = geometry(foot)
            assert abs(points[:, 2].min()) < 2e-6
            foot.location.z -= 0.033
            records.append(
                dict(
                    name=foot.name,
                    kind="foot_translation",
                    displacement_world_m=[0, 0, -0.033],
                    before_bounds_m=[points.min(0).tolist(), points.max(0).tolist()],
                )
            )
            records.append(extend_lower(leg, np.arange(len(leg.data.vertices)), FLOOR_Z + 0.014))
            feet.append(foot.name)
            legs.append(leg.name)
    controller = bpy.data.objects["OP030B__source_0693_m0120_p01"]
    world = _world_vertices(controller)
    selected = []
    for indices in _welded_components(controller.data):
        points = world[indices]
        if (
            np.allclose(np.ptp(points, axis=0), [0.42, 0.44, 0.03], atol=2e-6)
            and abs(points[:, 2].min() - 0.005) < 2e-6
        ):
            selected.append(indices)
    assert len(selected) == 1
    records.append(extend_lower(controller, selected[0], FLOOR_Z))
    bpy.context.view_layer.update()
    after = snapshot()
    changed = {r["name"] for r in records}
    assert len(changed) == 9 and set(before) == set(after)
    for name in before:
        assert before[name]["parent"] == after[name]["parent"]
        if name not in changed:
            assert before[name] == after[name], name
        elif name not in feet:
            assert before[name]["world"] == after[name]["world"], name
    for record in records:
        points, _ = geometry(bpy.data.objects[record["name"]])
        record["evaluated_after_bounds_m"] = [points.min(0).tolist(), points.max(0).tolist()]
    binding = dict(
        source=str(SOURCE.relative_to(ROOT)),
        source_sha256=SOURCE_SHA,
        scope="B four feet/uprights and one existing controller bottom plate only; upper work geometry unchanged",
        floor_z_m=FLOOR_Z,
        records=records,
        feet=feet,
        legs=legs,
        controller_plate=controller.name,
        controller_plate_vertex_indices=selected[0].tolist(),
        object_count_unchanged=len(before),
        unchanged_objects=len(before) - len(changed),
        added_equipment_count=0,
        added_objects_count=0,
        fixed_check_pending=True,
    )
    bpy.context.scene["op030_stagger_support_v06"] = json.dumps(binding)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    manifest.update(
        source=str(SOURCE.relative_to(ROOT)),
        source_sha256=SOURCE_SHA,
        source_manifest=str(SOURCE_MANIFEST.relative_to(ROOT)),
        source_manifest_sha256=source_manifest_sha,
        output=str(OUTPUT.relative_to(ROOT)),
        output_sha256=digest(OUTPUT),
        stagger_support_v06=binding,
        observed_at=datetime.now().astimezone().isoformat(),
    )
    meshes = {name: geometry(bpy.data.objects[name]) for name in sorted(changed)}
    bounds = np.array([[v.min(0), v.max(0)] for v, _ in meshes.values()])
    fixed_geometry = json.loads((ROOT / "analysis/op040_stagger_layout_inventory.json").read_text())["objects"]
    first_geometry = json.loads((ROOT / "audit/op030_stagger_static_v06_geometry.json").read_text())
    relocated = set(first_geometry["stagger"]["moved_objects"])
    omitted = []
    for obj in bpy.context.scene.objects:
        if obj.type not in {"MESH", "CURVE"} or obj.name in changed:
            continue
        if obj.name in relocated:
            points, faces = geometry(obj)
            box = np.array([points.min(0), points.max(0)])
        else:
            box = np.asarray(fixed_geometry[obj.name]["bounds_world_m"])
            points = faces = None
        near = np.any(np.all(bounds[:, 1] + 0.10 >= box[0], axis=1) & np.all(bounds[:, 0] - 0.10 <= box[1], axis=1))
        if near:
            meshes[obj.name] = (points, faces) if points is not None else geometry(obj)
        else:
            omitted.append(dict(name=obj.name, bounds_m=box.tolist()))
    names, labels, vertices, faces, vo, mesh_face_offsets = [], [], [], [], [0], [0]
    for name, (v, f) in meshes.items():
        names.append(name)
        labels.append("changed" if name in changed else "environment")
        vertices.append(v)
        faces.append(f)
        vo.append(vo[-1] + len(v))
        mesh_face_offsets.append(mesh_face_offsets[-1] + len(f))
    np.savez_compressed(
        MESHES,
        names=names,
        labels=labels,
        vertices=np.concatenate(vertices),
        faces=np.concatenate(faces),
        vertex_offsets=vo,
        face_offsets=mesh_face_offsets,
    )
    detail = dict(
        native=manifest["output"],
        native_sha256=manifest["output_sha256"],
        source=binding["source"],
        source_sha256=SOURCE_SHA,
        builder_sha256=digest(Path(__file__)),
        support=binding,
        objects={name: dict(before=before[name], after=after[name]) for name in sorted(changed)},
        meshes=str(MESHES.relative_to(ROOT)),
        meshes_sha256=digest(MESHES),
        omitted_fixed=omitted,
        omitted_margin_m=0.10,
        original_stagger_completion="audit/op030_stagger_static_v06_completion.json",
        formal_physical_validity_verdict=None,
    )
    DETAIL.write_text(json.dumps(detail, ensure_ascii=False, indent=2) + "\n")
    manifest["stagger_support_v06"].update(
        geometry_record=str(DETAIL.relative_to(ROOT)), geometry_record_sha256=digest(DETAIL)
    )
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    assert digest(SOURCE) == SOURCE_SHA and digest(SOURCE_MANIFEST) == source_manifest_sha
    print("STAGGER_SUPPORTED_STATIC_SAVED", manifest["output_sha256"], len(changed), len(names), flush=True)


if __name__ == "__main__":
    main()
