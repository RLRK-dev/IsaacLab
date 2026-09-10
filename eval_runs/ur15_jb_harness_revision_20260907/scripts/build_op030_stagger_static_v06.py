# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Relocate B robot/supply rigidly while keeping the conveyor frame fixed [m]."""

import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "analysis/op030_split_front_feeders_static_v05.blend"
SOURCE_SHA = "b3d22be1dfba8e2c0247677a6f05eb8761d357572d9aac95a372b58f074fd22f"
SOURCE_MANIFEST = ROOT / "audit/op030_split_static_v05.json"
SOURCE_MANIFEST_SHA = "ab107d29e93ddfbc7c72cb037f36d60e2cdd2236ad57593bd273077e686a3dd6"
INVENTORY = ROOT / "analysis/op040_stagger_layout_inventory.json"
OUTPUT = ROOT / "analysis/op030_stagger_static_v06.blend"
MANIFEST = ROOT / "audit/op030_stagger_static_v06.json"
DETAIL = ROOT / "audit/op030_stagger_static_v06_geometry.json"
MESHES = ROOT / "data/op030_stagger_static_v06_meshes.npz"
GROUP = "OP030B_robot_supply_stagger_root"


def digest(path: Path) -> str:
    """Return a saved file SHA256 digest."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def shape_signature(obj: bpy.types.Object) -> str | None:
    """Hash local geometry and materials without moving it."""
    if obj.type == "MESH":
        data = obj.data
        vertices = np.array([v.co[:] for v in data.vertices], dtype=np.float64)
        polygons = [(tuple(p.vertices), p.material_index) for p in data.polygons]
        keys = []
        if data.shape_keys:
            keys = [(k.name, k.value, [v.co[:] for v in k.data]) for k in data.shape_keys.key_blocks]
        payload = [vertices.tolist(), polygons, keys]
    elif obj.type == "CURVE":
        data = obj.data
        payload = [data.bevel_depth, data.bevel_resolution, data.resolution_u, []]
        for spline in data.splines:
            points = [list(p.co) for p in spline.points]
            bezier = [(list(p.co), list(p.handle_left), list(p.handle_right)) for p in spline.bezier_points]
            payload[-1].append([spline.type, points, bezier, spline.use_cyclic_u])
    else:
        return None
    payload += [[m.name if m else None for m in data.materials]]
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()


def geometry(obj: bpy.types.Object) -> tuple[np.ndarray, np.ndarray]:
    """Return actual evaluated world vertices [m] and triangle indices."""
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    vertices = np.array([v.co[:] for v in mesh.vertices], dtype=np.float64)
    matrix = np.asarray(evaluated.matrix_world)
    vertices = vertices @ matrix[:3, :3].T + matrix[:3, 3]
    faces = np.array([tuple(t.vertices) for t in mesh.loop_triangles], dtype=np.int32)
    evaluated.to_mesh_clear()
    return vertices, faces


def snapshot() -> dict:
    """Read world transforms [m, rad], parents, and local signatures."""
    return {
        o.name: dict(
            parent=o.parent.name if o.parent else None,
            world=np.asarray(o.matrix_world).tolist(),
            shape=shape_signature(o),
            type=o.type,
        )
        for o in bpy.context.scene.objects
    }


def main() -> None:
    """Build a separate static candidate and its comparison inputs."""
    assert digest(SOURCE) == SOURCE_SHA and digest(SOURCE_MANIFEST) == SOURCE_MANIFEST_SHA
    assert not any(p.exists() for p in (OUTPUT, MANIFEST, DETAIL, MESHES)), "Preserve existing candidates"
    inventory = json.loads(INVENTORY.read_text())
    manifest = copy.deepcopy(json.loads(SOURCE_MANIFEST.read_text()))
    selection = inventory["B_candidate_exact_selection"]
    roots = list(selection["move_rigid_subtree_roots"])
    drops = [f"Split_bay_1__source_0783_m0210_p{i:02d}" for i in range(4)]
    roots += drops
    moved = set(selection["all_selected_object_names"]) | set(drops)
    fixed = set(selection["all_kept_conveyor_fixture_objects"])
    assert len(roots) == 104 and len(moved) == 420 and len(fixed) == 76
    assert not moved & fixed
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    before = snapshot()
    assert all(name in before for name in moved | fixed)
    assert all(before[name]["parent"] not in moved for name in roots)
    actual = {o.name for name in roots for o in (bpy.data.objects[name], *bpy.data.objects[name].children_recursive)}
    assert actual == moved
    delta = np.diag([-1.0, -1.0, 1.0, 1.0])
    delta[1, 3] = 1.2
    baseline = delta.copy()
    baseline[1, 3] = -3.4
    group = bpy.data.objects.new(GROUP, None)
    scene.collection.objects.link(group)
    group.matrix_world = Matrix(delta) @ bpy.data.objects["OP030B_cell"].matrix_world
    group["purpose"] = "Rigid right-bank robot/supply frame; conveyor positioner remains outside"
    group["drawer_local_extension_m"] = [0.0, 0.34]
    bpy.context.view_layer.update()
    inverse = group.matrix_world.inverted()
    for name in roots:
        obj = bpy.data.objects[name]
        desired = Matrix(delta @ np.asarray(before[name]["world"]))
        obj.parent = group
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_basis = inverse @ desired
    bpy.context.view_layer.update()
    after = snapshot()
    assert set(after) - set(before) == {GROUP}
    changed_shapes, changed_fixed, unexpected_parents = [], [], []
    moved_errors = {}
    for name, old in before.items():
        new = after[name]
        if old["shape"] != new["shape"]:
            changed_shapes.append(name)
        expected = delta @ np.asarray(old["world"]) if name in moved else np.asarray(old["world"])
        error = float(np.max(abs(np.asarray(new["world"]) - expected)))
        if name in moved:
            moved_errors[name] = error
            assert error < 2e-6, (name, error)
        elif error:
            changed_fixed.append([name, error])
        expected_parent = GROUP if name in roots else old["parent"]
        if new["parent"] != expected_parent:
            unexpected_parents.append(name)
    assert not changed_shapes and not changed_fixed and not unexpected_parents
    drawer = bpy.data.objects["OP030B_wire_supply_drawer"]
    assert drawer.parent == group and abs(drawer.location.x) < 1e-7
    branch = bpy.data.objects["OP030B__OP030_air_service_connections_header_branch"]
    points = np.array([p.co[:] for p in branch.data.splines[0].points]) @ np.asarray(branch.matrix_world).T
    assert np.max(abs(points[0, :3] - [1.42, 1.105, 2.62])) < 2e-6
    hose = bpy.data.objects["OP030B_wire_supply__OP030_supply_actuator_supply_hose"]
    hose_points = np.array([p.co[:] for p in hose.data.splines[0].points]) @ np.asarray(hose.matrix_world).T
    binding = dict(
        group=GROUP,
        group_world=np.asarray(group.matrix_world).tolist(),
        robot_supply_delta_world=delta.tolist(),
        robot_supply_delta_baseline=baseline.tolist(),
        robot_base_world_m=[0.9, 0.6, 0.0],
        robot_base_baseline_m=[0.9, -1.7, 0.0],
        global_y_offset_m=2.3,
        fixed_cell_root="OP030B_cell",
        moved_roots=roots,
        moved_objects=sorted(moved),
        added_drop_meshes=drops,
        fixed_line_objects=sorted(fixed),
        drawer=drawer.name,
        drawer_parent=GROUP,
        drawer_local_extension_m=[0.0, 0.34],
        drawer_world_axis=[-1.0, 0.0, 0.0],
        drawer_initial_world=np.asarray(drawer.matrix_world).tolist(),
        drawer_bake_rule=(
            "Keep parent. desired_world=group_world@Tx(extension); bake inverse(group_world)@desired_world"
        ),
        product_world_rotation_unchanged=True,
        header_branch_world_points_m=points[:, :3].tolist(),
        right_header="source_0780_m0207_p03",
        header_axis_world_x_z_m=[1.42, 2.62],
        actuator_hose_world_points_m=hose_points[:, :3].tolist(),
        fixed_check_pending=True,
    )
    manifest.update(
        source=str(SOURCE.relative_to(ROOT)),
        source_sha256=SOURCE_SHA,
        source_manifest=str(SOURCE_MANIFEST.relative_to(ROOT)),
        source_manifest_sha256=SOURCE_MANIFEST_SHA,
        stagger_v06=binding,
        observed_at=datetime.now().astimezone().isoformat(),
    )
    cell = manifest["layout"]["cells"]["OP030B"]
    cell.update(robot_base_m=[0.9, 0.6, 0], robot_supply_root=GROUP, robot_supply_delta_world=delta.tolist())
    supply = manifest["wire_supply"]
    for key in ("stock_center_cell_m", "active_center_cell_m"):
        point = np.r_[supply[key], 1.0]
        supply[key] = (baseline @ point)[:3].tolist()
    for row in supply.get("saddles", []):
        if "center_cell_m" in row:
            row["center_cell_m"] = (baseline @ np.r_[row["center_cell_m"], 1])[:3].tolist()
    supply.update(drawer_parent=GROUP, drawer_axis_world=[-1, 0, 0], drawer_axis_local=[1, 0, 0])
    scene["op030_stagger_v06"] = json.dumps(binding)
    scene["split_layout_manifest"] = json.dumps(manifest["layout"]["cells"])
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    manifest.update(output=str(OUTPUT.relative_to(ROOT)), output_sha256=digest(OUTPUT))

    # Evaluated world triangles include CURVE hoses. AABBs only select query candidates.
    mesh_rows = {}
    for name in sorted(moved):
        obj = bpy.data.objects[name]
        if obj.type in {"MESH", "CURVE"}:
            mesh_rows[name] = geometry(obj)
    moved_bounds = np.array([[v.min(0), v.max(0)] for v, _ in mesh_rows.values()])
    omitted = []
    for obj in scene.objects:
        if obj.type not in {"MESH", "CURVE"} or obj.name in moved:
            continue
        box = inventory["objects"][obj.name].get("bounds_world_m")
        if not box:
            continue
        box = np.asarray(box)
        near = np.any(
            np.all(moved_bounds[:, 1] + 0.10 >= box[0], axis=1) & np.all(moved_bounds[:, 0] - 0.10 <= box[1], axis=1)
        )
        if near:
            mesh_rows[obj.name] = geometry(obj)
        else:
            omitted.append(dict(name=obj.name, bounds_world_m=box.tolist()))
    names, labels, vertices, faces, vo, mesh_face_offsets = [], [], [], [], [0], [0]
    for name, (v, f) in mesh_rows.items():
        names.append(name)
        labels.append("moved" if name in moved else "fixed")
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
        observed_at=datetime.now().astimezone().isoformat(),
        source=manifest["source"],
        source_sha256=SOURCE_SHA,
        output=manifest["output"],
        output_sha256=manifest["output_sha256"],
        builder_sha256=digest(Path(__file__)),
        inventory_sha256=digest(INVENTORY),
        stagger=binding,
        existing_object_count=len(before),
        added_empty_count=1,
        geometry_shapes_unchanged=len([v for v in before.values() if v["shape"]]),
        unchanged_object_world_count=len(before) - len(moved),
        unchanged_objects_world_sha256=hashlib.sha256(
            json.dumps({n: before[n] for n in sorted(before) if n not in moved}, sort_keys=True).encode()
        ).hexdigest(),
        moved_objects={
            n: dict(before=before[n], after=after[n], maximum_delta_matrix_error=moved_errors[n]) for n in sorted(moved)
        },
        added_empty_world=after[GROUP]["world"],
        maximum_rigid_matrix_error=max(moved_errors.values()),
        unexpected_changed_fixed=changed_fixed,
        unexpected_shape_changes=changed_shapes,
        unexpected_parent_changes=unexpected_parents,
        fixed_check_meshes=str(MESHES.relative_to(ROOT)),
        fixed_check_meshes_sha256=digest(MESHES),
        fixed_check_names=names,
        fixed_check_labels=labels,
        omitted_fixed_aabb_separated=omitted,
        formal_physical_validity_verdict=None,
    )
    DETAIL.write_text(json.dumps(detail, ensure_ascii=False, indent=2) + "\n")
    manifest["stagger_v06"].update(geometry_audit=str(DETAIL.relative_to(ROOT)), geometry_audit_sha256=digest(DETAIL))
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    assert digest(SOURCE) == SOURCE_SHA and digest(SOURCE_MANIFEST) == SOURCE_MANIFEST_SHA
    print("OP030_STAGGER_STATIC_V06_SAVED", manifest["output_sha256"], len(moved), len(mesh_rows), flush=True)


if __name__ == "__main__":
    main()
