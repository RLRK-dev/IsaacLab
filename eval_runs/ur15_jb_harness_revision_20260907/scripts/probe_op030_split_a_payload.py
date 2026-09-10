# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Native full-payload/environment sweep from completed ST A to the ST B entry [m, s]."""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
ACTORS = ROOT / "analysis/split_layout_a_handoff_actors.npz"
OUTPUT = ROOT / "analysis/split_layout_a_payload_meshes.npz"
B_BANK = ROOT / "analysis/op030_split_b_gap20_native30.npz"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export(native_override=None, output=OUTPUT, report_file=None, expected_sha256=None):
    """Export swept payload, neighboring native equipment, and B's initial parked robot [m]."""
    import bpy
    from mathutils import Matrix

    source_meta = json.loads((ROOT / "audit/op030_split_layout_a_handoff_export.json").read_text())
    mesh_meta = json.loads((ROOT / "data/op030_split_a_integrated_meshes.json").read_text())
    assert digest(ACTORS) == source_meta["output_sha256"]
    native = Path(native_override or source_meta["native"])
    assert digest(native) == (expected_sha256 or source_meta["native_sha256"])
    output = Path(output)
    report_file = Path(report_file or ROOT / "audit/op030_split_layout_a_payload_export.json")
    with np.load(ACTORS) as source:
        actor_names = source["actor_names"].tolist()
        actor_poses, times = source["actor_world"].copy(), source["times"].copy()
    with np.load(source_meta["mesh"]) as source:
        aliases = dict(zip(source["actor_world_names"].tolist(), source["actor_native_names"].tolist(), strict=True))
    bpy.ops.wm.open_mainfile(filepath=str(native))
    scene = bpy.context.scene

    def depth(obj):
        return 0 if obj.parent is None else 1 + depth(obj.parent)

    def set_world(matrices):
        objects = [(bpy.data.objects[name], matrix) for name, matrix in matrices.items() if name in bpy.data.objects]
        for level in sorted({depth(obj) for obj, _ in objects}):
            for obj, matrix in objects:
                if depth(obj) == level:
                    obj.matrix_world = Matrix(matrix.tolist())
            bpy.context.view_layer.update()

    hardware = json.loads(scene.get("split_transfer_hardware", "{}"))
    changed_actors = {cell[key] for cell in hardware.get("cells", {}).values() for key in ("body", "stopper", "sensor")}
    set_world(
        {
            aliases[name]: matrix
            for name, matrix in zip(actor_names, actor_poses[0], strict=True)
            if aliases[name] not in changed_actors
        }
    )
    product, pallet = bpy.data.objects["JB_OP020_UID001"], bpy.data.objects["source_0292"]
    for name, matrix in source_meta["assembled_product_relative_poses"].items():
        obj = bpy.data.objects[name]
        obj.parent = product
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_basis = Matrix(matrix)
    layout = json.loads(scene["split_layout_manifest"])
    b_names = layout["OP030B"]["source_names"]
    with np.load(B_BANK) as bank:
        b_nodes, b_poses = bank["node_ids"], bank["poses"][0].copy()
    b_poses[:, 1, 3] += 2.30
    set_world({b_names[f"source_{int(node):04d}"]: matrix for node, matrix in zip(b_nodes, b_poses, strict=True)})
    bpy.data.objects[layout["OP030B"]["lift_carriage"]].location.z = -0.051
    bpy.context.view_layer.update()

    def ancestors(obj):
        result = []
        while obj:
            result.append(obj)
            obj = obj.parent
        return result

    candidates = [obj for obj in scene.objects if obj.type in {"MESH", "CURVE"} and not obj.hide_render]
    payload = {obj.name for obj in candidates if product in ancestors(obj) or pallet in ancestors(obj)}
    assert any("OP020_harness_UID001" in name for name in payload), "Existing external harness must follow product"
    assert sum(name.startswith("OP030A_feeder_M4_UID") for name in payload) == 12

    def bounds(obj):
        world = np.asarray(obj.matrix_world)
        points = np.asarray(obj.bound_box) @ world[:3, :3].T + world[:3, 3]
        return np.array([points.min(0), points.max(0)])

    boxes = np.asarray([bounds(obj) for obj in candidates if obj.name in payload])
    product_index = actor_names.index(product.name)
    delta = actor_poses[-1, product_index, :3, 3] - actor_poses[0, product_index, :3, 3]
    sweep = np.array(
        [
            np.minimum(boxes[:, 0].min(0), boxes[:, 0].min(0) + delta),
            np.maximum(boxes[:, 1].max(0), boxes[:, 1].max(0) + delta),
        ]
    )
    selected = []
    for obj in candidates:
        box = bounds(obj)
        moving_lift = any(item.name in {"OP030_lift_fixed", "OP030_lift_carriage"} for item in ancestors(obj))
        if (
            obj.name in payload
            or moving_lift
            or np.all(np.minimum(box[1], sweep[1] + 0.025) >= np.maximum(box[0], sweep[0] - 0.025))
        ):
            selected.append(obj)
    selected.sort(key=lambda obj: obj.name)
    vertices, faces, vertex_offsets, face_offsets = [], [], [0], [0]
    graph = bpy.context.evaluated_depsgraph_get()
    for obj in selected:
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        vertices.extend([vertex.co[:] for vertex in mesh.vertices])
        faces.extend([triangle.vertices[:] for triangle in mesh.loop_triangles])
        vertex_offsets.append(len(vertices))
        face_offsets.append(len(faces))
        evaluated.to_mesh_clear()
    transforms = []
    tracked = ["JB_OP020_UID001", "source_0292", "OP030_lift_carriage"]
    for index, row in enumerate(actor_poses):
        set_world({name: row[actor_names.index(name)] for name in tracked})
        if hardware:
            unit = hardware["cells"]["OP030A"]
            u = float(np.clip((times[index] - 5.5) / 1.5, 0, 1))
            ease = 10 * u**3 - 15 * u**4 + 6 * u**5
            matrix = np.asarray(unit["stopper_up_world"]).copy()
            matrix[2, 3] -= hardware["stopper_stroke_m"] * ease
            set_world({unit["stopper"]: matrix})
        transforms.append([np.asarray(obj.matrix_world).copy() for obj in selected])
        if index % 60 == 0:
            print("A_PAYLOAD_NATIVE", index, len(times), len(selected), flush=True)
    matrices = np.asarray(transforms)
    np.savez_compressed(
        output,
        names=[obj.name for obj in selected],
        payload=[obj.name in payload for obj in selected],
        vertices=np.asarray(vertices),
        faces=np.asarray(faces),
        vertex_offsets=vertex_offsets,
        face_offsets=face_offsets,
        matrices=matrices,
        times=times,
    )
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        native=str(native),
        native_sha256=digest(native),
        actor_source=str(ACTORS),
        actor_source_sha256=digest(ACTORS),
        b_bank=str(B_BANK),
        b_bank_sha256=digest(B_BANK),
        b_pose="First original-FK frame plus Y=2.30 m; B worklift stowed at -0.051 m; supply drawer remains retracted",
        output=str(output),
        output_sha256=digest(output),
        frames=len(times),
        payload_meshes=len(payload),
        selected_meshes=len(selected),
        triangles=len(faces),
        payload_swept_aabb_m=sweep.tolist(),
        geometry_region=(
            "Every native mesh with bounds intersecting the conservative payload sweep +25 mm, plus all A lift meshes"
        ),
        selected_names=[obj.name for obj in selected],
        payload_names=sorted(payload),
        reused_lift_drivers=mesh_meta["driven_link_actors"],
        transfer_hardware=hardware,
        stopper_schedule=("A: UP until 5.5 s, 55 mm quintic down at 5.5–7.0 s; B: UP" if hardware else None),
        formal_physical_validity_verdict=None,
    )
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("A_PAYLOAD_EXPORT_COMPLETE", len(selected), len(payload), len(faces), flush=True)


def check(
    mesh_file=OUTPUT,
    metadata_file=ROOT / "audit/op030_split_layout_a_payload_export.json",
    report_file=ROOT / "audit/op030_split_layout_a_payload_check.json",
):
    """Record actual payload/environment triangle intersections and exact contacting faces [m]."""
    try:
        import fcl
    except ImportError:
        sys.path.insert(0, "/tmp/ur15_op030_fcl")
        import fcl

    metadata = json.loads(Path(metadata_file).read_text())
    assert digest(mesh_file) == metadata["output_sha256"]
    with np.load(mesh_file) as source:
        data = {key: source[key].copy() for key in source.files}
    # FCL rigid transforms require an orthogonal rotation. Native segment()
    # objects can retain a static axial scale in matrix_world. Bake the full
    # constant stretch/shear into vertices before constructing their BVHs.
    linear = data["matrices"][..., :3, :3].copy()
    left, _, right = np.linalg.svd(linear)
    determinant = np.linalg.det(left @ right)
    left[..., :, -1] *= np.where(determinant < 0, -1.0, 1.0)[..., None]
    rotations = left @ right
    stretch = np.swapaxes(rotations, -1, -2) @ linear
    stretch_variation = float(np.max(abs(stretch - stretch[:1])))
    if stretch_variation > 2e-6:
        raise ValueError(f"Time-varying mesh stretch requires per-frame geometry: {stretch_variation:.6g}")
    scaled = np.flatnonzero(np.max(abs(stretch[0] - np.eye(3)), axis=(1, 2)) > 1e-6)
    for index in range(len(data["names"])):
        start, stop = data["vertex_offsets"][index : index + 2]
        data["vertices"][start:stop] = data["vertices"][start:stop] @ stretch[0, index].T
    data["matrices"][..., :3, :3] = rotations
    names, payload = data["names"], data["payload"]
    objects, centers, extents, mesh_vertices, mesh_faces = [], [], [], [], []
    for index in range(len(names)):
        points = data["vertices"][data["vertex_offsets"][index] : data["vertex_offsets"][index + 1]]
        triangles = data["faces"][data["face_offsets"][index] : data["face_offsets"][index + 1]]
        model = fcl.BVHModel()
        model.beginModel(len(points), len(triangles))
        model.addSubModel(points, triangles)
        model.endModel()
        objects.append(fcl.CollisionObject(model, fcl.Transform()))
        centers.append((points.min(0) + points.max(0)) / 2)
        extents.append((points.max(0) - points.min(0)) / 2)
        mesh_vertices.append(points)
        mesh_faces.append(triangles)
    centers, extents = np.asarray(centers), np.asarray(extents)
    a, b = np.meshgrid(np.flatnonzero(payload), np.flatnonzero(~payload), indexing="ij")
    a, b = a.ravel(), b.ravel()
    request = fcl.CollisionRequest(num_max_contacts=20, enable_contact=True)
    hits = []

    def triangle_normal(index, face, matrix):
        if face < 0 or face >= len(mesh_faces[index]):
            return None
        points = mesh_vertices[index][mesh_faces[index][face]] @ matrix[:3, :3].T
        normal = np.cross(points[1] - points[0], points[2] - points[0])
        return (normal / max(1e-20, np.linalg.norm(normal))).tolist()

    for frame, (time, matrices) in enumerate(zip(data["times"], data["matrices"], strict=True)):
        world_centers = np.einsum("nij,nj->ni", matrices[:, :3, :3], centers) + matrices[:, :3, 3]
        world_extents = np.einsum("nij,nj->ni", abs(matrices[:, :3, :3]), extents)
        overlap = np.all(world_extents[a] + world_extents[b] - abs(world_centers[a] - world_centers[b]) > 1e-5, axis=1)
        for index, matrix in enumerate(matrices):
            objects[index].setTransform(fcl.Transform(matrix[:3, :3], matrix[:3, 3]))
        pairs = []
        for first, second in zip(a[overlap], b[overlap], strict=True):
            result = fcl.CollisionResult()
            fcl.collide(objects[first], objects[second], request, result)
            if not result.is_collision:
                continue
            contacts = [
                dict(
                    payload_face=int(contact.b1),
                    environment_face=int(contact.b2),
                    point_m=np.asarray(contact.pos).tolist(),
                    normal=np.asarray(contact.normal).tolist(),
                    depth_m=float(contact.penetration_depth),
                    payload_face_normal=triangle_normal(first, int(contact.b1), matrices[first]),
                    environment_face_normal=triangle_normal(second, int(contact.b2), matrices[second]),
                )
                for contact in result.contacts
            ]
            pairs.append(dict(payload=str(names[first]), environment=str(names[second]), contacts=contacts))
        if pairs:
            hits.append(dict(frame=frame + 1, time_s=float(time), pairs=pairs))
        if frame % 60 == 0:
            print("A_PAYLOAD_FCL", frame, len(data["times"]), len(hits), flush=True)
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        mesh_sha256=digest(mesh_file),
        frames=len(data["times"]),
        pair_samples=len(a) * len(data["times"]),
        hits=hits,
        support_contact_exemptions=[],
        affine_handling="Static stretch/shear baked into local vertices; orthogonal rotations only passed to FCL",
        affine_baked_meshes=data["names"][scaled].tolist(),
        maximum_stretch_variation=stretch_variation,
        scope=(
            "Raw payload/environment intersections. "
            "No support-face exemptions applied until exact mesh/triangle contact review."
        ),
        formal_physical_validity_verdict=None,
    )
    Path(report_file).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("A_PAYLOAD_CHECK_COMPLETE", len(data["times"]), len(hits), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("export", "check"))
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    globals()[args.mode]()
