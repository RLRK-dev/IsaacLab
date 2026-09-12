# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Export the accepted OP030 exit as OP040's incoming product snapshot [m]."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NATIVE_SHA = "e65bef607c1d29671fc982d14d72d4c2694420edd284378cb2f1445f18f354ed"


def digest(path: Path) -> str:
    """Read a file digest without modifying it."""
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def lineage(obj: bpy.types.Object) -> list[str]:
    """Return this object's name and all parent names."""
    names = []
    while obj is not None:
        names.append(obj.name)
        obj = obj.parent
    return names


def export() -> None:
    """Record incoming poses and evaluated triangle geometry [m] without baking."""
    native = ROOT / "UR15_JB_OP030_split_v06.blend"
    prepared_path = ROOT / "data/op030_split_animation_v06.npz"
    metadata_path = prepared_path.with_suffix(".json")
    output = ROOT / "data/op040_incoming_product_v01.npz"
    report_path = ROOT / "audit/op040_incoming_product_v01.json"
    if output.exists() or report_path.exists():
        raise FileExistsError("Keep an existing incoming snapshot and choose a new version")
    source_sha = digest(native)
    prepared_sha = digest(prepared_path)
    metadata_sha = digest(metadata_path)
    metadata = json.loads(metadata_path.read_text())
    if source_sha != NATIVE_SHA or prepared_sha != metadata["output_sha256"]:
        raise ValueError("The accepted v06 source has changed")
    installed = ["OP030_T01_UID001", "OP030_T02_UID001"]
    fasteners, tool_held = [], []
    for station in ("A", "C"):
        fasteners.extend(metadata["fastener_ownership"][station]["assembled_uids"])
        tool_held.extend(metadata["fastener_ownership"][station]["end_loaded_uids"])
    installed.extend(fasteners)
    if len(set(fasteners)) != 8 or set(installed) & set(tool_held):
        raise ValueError("Installed and tool-held fasteners are not distinct")
    expected, shapes = {}, {}
    with np.load(prepared_path, allow_pickle=False) as saved:
        final_frame = int(saved["frames"][-1])
        expected["JB_OP020_UID001"] = saved["product"][-1]
        expected["source_0292"] = saved["pallet"][-1]
        names = saved["object_names"].tolist()
        final_objects = saved["object_poses"][-1]
        for name in installed:
            expected[name] = final_objects[names.index(name)]
        for station in ("A", "C"):
            uids = saved["ledger_uids_" + station].tolist()
            owners = saved["ledger_owner_" + station][-1]
            if {uid for uid, owner in zip(uids, owners, strict=True) if owner == 3} != set(
                metadata["fastener_ownership"][station]["assembled_uids"]
            ):
                raise ValueError("The final ownership ledger differs from its summary")
        for wire in metadata["wires"]:
            prefix, uid = f"wire_{wire['number']}_", wire["uid"]
            expected[uid] = saved[prefix + "root"][-1]
            for index, end in enumerate(("J1", "T")):
                expected[uid + "_" + end] = saved[prefix + "lugs"][-1, index]
            parameter = saved[prefix + "parameter"][-1]
            indices = np.flatnonzero(saved[prefix + "shape_parameters"] == parameter)
            if len(indices) != 1:
                raise ValueError("The final deformation has no unique stored shape")
            shapes[uid + "_insulation"] = saved[prefix + "shape_vertices"][int(indices[0])]
    bpy.ops.wm.open_mainfile(filepath=str(native))
    scene = bpy.context.scene
    scene.frame_set(final_frame)
    bpy.context.view_layer.update()
    actor_names = sorted(expected)
    actual = np.array([np.asarray(bpy.data.objects[name].matrix_world) for name in actor_names])
    planned = np.array([expected[name] for name in actor_names])
    pose_error = float(np.max(np.abs(actual - planned)))
    if pose_error > 5e-5:
        raise ValueError(f"Incoming actor readback mismatch: {pose_error}")
    product = np.asarray(bpy.data.objects["JB_OP020_UID001"].matrix_world)
    inverse = np.linalg.inv(product)
    roots = {"JB_OP020_UID001", "source_0292", *installed, *(wire["uid"] for wire in metadata["wires"])}
    payload = sorted(
        (
            obj
            for obj in scene.objects
            if obj.type in {"MESH", "CURVE"} and not obj.hide_render and roots.intersection(lineage(obj))
        ),
        key=lambda obj: obj.name,
    )
    if not payload or any(set(tool_held).intersection(lineage(obj)) for obj in payload):
        raise ValueError("The payload is empty or includes spare tool-held hardware")
    vertices, triangles, records = [], [], []
    vertex_offsets, face_offsets = [0], [0]
    deformation_error = 0.0
    graph = bpy.context.evaluated_depsgraph_get()
    for obj in payload:
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        points = np.empty((len(mesh.vertices), 3), dtype=np.float32)
        faces = np.empty((len(mesh.loop_triangles), 3), dtype=np.int32)
        mesh.vertices.foreach_get("co", points.ravel())
        mesh.loop_triangles.foreach_get("vertices", faces.ravel())
        if obj.name in shapes:
            deformation_error = max(deformation_error, float(np.max(np.abs(points - shapes[obj.name]))))
        world = np.asarray(evaluated.matrix_world)
        records.append(
            dict(
                name=obj.name,
                ancestors=lineage(obj),
                matrix_world=world.tolist(),
                matrix_product=(inverse @ world).tolist(),
                vertices=len(points),
                triangles=len(faces),
            )
        )
        vertices.append(points)
        triangles.append(faces)
        vertex_offsets.append(vertex_offsets[-1] + len(points))
        face_offsets.append(face_offsets[-1] + len(faces))
        evaluated.to_mesh_clear()
    if deformation_error > 5e-6:
        raise ValueError(f"Incoming wire deformation mismatch: {deformation_error}")
    np.savez_compressed(
        output,
        actor_names=np.asarray(actor_names),
        actor_world=actual,
        actor_product=inverse[None] @ actual,
        mesh_names=np.asarray([row["name"] for row in records]),
        mesh_world=np.asarray([row["matrix_world"] for row in records]),
        mesh_product=np.asarray([row["matrix_product"] for row in records]),
        vertices=np.concatenate(vertices),
        triangles=np.concatenate(triangles),
        vertex_offsets=np.asarray(vertex_offsets),
        face_offsets=np.asarray(face_offsets),
    )
    if digest(native) != source_sha or digest(prepared_path) != prepared_sha or digest(metadata_path) != metadata_sha:
        raise ValueError("An input changed during read-only export")
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        source_native=native.name,
        native_sha256=source_sha,
        prepared_path=str(prepared_path.relative_to(ROOT)),
        prepared_sha256=prepared_sha,
        metadata_sha256=metadata_sha,
        source_frame=final_frame,
        actor_count=len(actor_names),
        payload_mesh_count=len(records),
        installed_support_uids=installed[:2],
        installed_fastener_uids=fasteners,
        excluded_tool_held_uids=tool_held,
        wires=metadata["wires"],
        product_world=product.tolist(),
        pallet_world=expected["source_0292"].tolist(),
        actor_readback_max_matrix_error=pose_error,
        wire_vertex_max_error_m=deformation_error,
        output=str(output.relative_to(ROOT)),
        output_sha256=digest(output),
        output_bytes=output.stat().st_size,
        mesh_records=records,
        native_saved=False,
        input_sha256_unchanged=True,
        nominal_receiver_product_y_m=4.05,
        nominal_receiver_translation_m=[0.0, 1.15, 0.0],
        transfer_collision_checked=False,
        new_branch_connections_defined=False,
        formal_physical_validity_verdict=None,
        scope="Read-only final-frame product snapshot. Mesh-local triangles use per-mesh vertex offsets. "
        "No incoming transfer, new wiring, IK, native changes, material-force or physical-validity judgment.",
    )
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("OP040_INCOMING_SNAPSHOT_COMPLETE", len(actor_names), len(records), output.stat().st_size, flush=True)


if __name__ == "__main__":
    export()
