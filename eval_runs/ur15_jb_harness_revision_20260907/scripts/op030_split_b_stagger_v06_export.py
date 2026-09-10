# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Reuse the B actor-local exporter with the opposite-side fixed native [m]."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_op030_split_v03 import build_wire
from continuous_common import delete_tree, digest
from op030_definition import ROOT, TERMINAL_X, TERMINAL_Y, TERMINAL_Z, pose, product_frame
from op030_split_transport import build_transport_clips, set_drawer_extension
from op030_split_wire import supply_layout


def _owner(obj):
    parent = obj
    while parent:
        if "source_node_id" in parent:
            return int(parent["source_node_id"])
        parent = parent.parent
    return None


def _is_b(obj):
    parent = obj
    while parent:
        if parent.name == "OP030B_cell" or parent.get("split_station") == "OP030B":
            return True
        parent = parent.parent
    return False


def _place_neighbor_parks(scene, a_park_bank, c_preload_bank, b_park_bank=None):
    neighbor_parks = []
    if a_park_bank or c_preload_bank or b_park_bank:
        layout = json.loads(scene["split_layout_manifest"])

        def object_depth(obj):
            return 0 if obj.parent is None else object_depth(obj.parent) + 1

        for cell, path, delta_y in (
            ("OP030A", a_park_bank, 0.0),
            ("OP030B", b_park_bank, 2.30),
            ("OP030C", c_preload_bank, 4.60),
        ):
            if path is None:
                continue
            with np.load(path) as bank:
                frame = int(bank["preload_frame_count"]) - 1 if cell == "OP030C" else -1
                aliases = layout[cell]["source_names"]
                matrices = {}
                for node, matrix in zip(bank["node_ids"], bank["poses"][frame], strict=True):
                    name = aliases[f"source_{int(node):04d}"]
                    if name in bpy.data.objects:
                        value = matrix.copy()
                        value[1, 3] += delta_y
                        matrices[name] = value
                objects = (
                    zip(bank["object_names"], bank["object_poses"][frame], strict=True)
                    if "object_names" in bank
                    else ()
                )
                for name, matrix in objects:
                    if name in bpy.data.objects and "driver" not in name:
                        value = matrix.copy()
                        value[1, 3] += delta_y
                        matrices[str(name)] = value
            for depth in sorted({object_depth(bpy.data.objects[name]) for name in matrices}):
                for name, matrix in matrices.items():
                    if object_depth(bpy.data.objects[name]) == depth:
                        bpy.data.objects[name].matrix_world = Matrix(matrix.tolist())
                bpy.context.view_layer.update()
            neighbor_parks.append(dict(cell=cell, bank=str(path), bank_sha256=digest(path), frame_index=frame))
    return neighbor_parks


def main() -> None:
    """Export actual robot/environment/clip/rigid-wire meshes from one snapshot."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", type=Path, default=ROOT / "analysis/op030_stagger_static_v06.blend")
    parser.add_argument("--output", default="op030_split_b_stagger_v06_meshes")
    parser.add_argument("--open_hinge_degrees", type=float, default=160.0)
    parser.add_argument("--connection_mode", choices=("rear_entry", "top_entry"), default="rear_entry")
    parser.add_argument("--without_transport_clips", action="store_true")
    parser.add_argument("--fixed_transport_height", action="store_true")
    parser.add_argument("--a_park_bank", type=Path)
    parser.add_argument("--c_preload_bank", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    native_sha = digest(args.native)
    bpy.ops.wm.open_mainfile(filepath=str(args.native))
    scene = bpy.context.scene
    scene.frame_set(1)
    if "OP030B_robot_supply_stagger_root" not in bpy.data.objects:
        raise ValueError("Missing opposite-side robot/supply parent")
    neighbor_parks = _place_neighbor_parks(scene, args.a_park_bank, args.c_preload_bank)
    config = json.loads((ROOT / "audit/op030_split_b_motion_v05.json").read_text())["config"]
    work = product_frame(lift=0.350)
    rows = supply_layout(
        tuple(config["counts"]), config["stock_pitch"], config["stock_center"], connection_mode=args.connection_mode
    )
    offset_y = 2.30
    offset = pose(location=(0, offset_y, 0))
    inverse_offset = pose(location=(0, -offset_y, 0))
    product, pallet = bpy.data.objects["JB_OP020_UID001"], bpy.data.objects["source_0292"]
    product.matrix_world = Matrix((offset @ work).tolist())
    pallet.matrix_world = Matrix((offset @ pose(location=(0.0, -1.70, 0.439 + 0.350))).tolist())
    bpy.context.view_layer.update()
    # The two continuing supports are the same IDs taken from the A stock tray.
    for number in (1, 2):
        support = bpy.data.objects[f"OP030_T{number:02d}_UID001"]
        world = offset @ work @ pose(location=(TERMINAL_X[number - 1], TERMINAL_Y, TERMINAL_Z))
        support.parent = product
        support.matrix_parent_inverse = Matrix.Identity(4)
        support.matrix_world = Matrix(world.tolist())
    installed_parts = {}
    if args.connection_mode == "top_entry":
        installed_path = ROOT / "audit/op030_split_a_installed_parts.json"
        installed = json.loads(installed_path.read_text())["product_relative_poses"]
        for name, relative in installed.items():
            obj = bpy.data.objects[name]
            obj.parent = product
            obj.matrix_parent_inverse = Matrix.Identity(4)
            obj.matrix_world = Matrix((offset @ work @ np.asarray(relative)).tolist())
            installed_parts[name] = relative
    carriage = bpy.data.objects["OP030B__OP030_lift_carriage"]
    carriage.location.z = -0.014 if args.fixed_transport_height else 0.350
    bpy.context.view_layer.update()
    drawer = bpy.data.objects["OP030B_wire_supply_drawer"]
    set_drawer_extension({"drawer": drawer}, 0.340)
    for number in (1, 2):
        for name in (f"OP030_H03_{number}_UID001", f"OP030_H03_{number}_UID001_T"):
            obj = bpy.data.objects.get(name)
            if obj:
                delete_tree(obj)
    if args.connection_mode == "top_entry":
        for name in [row["uid"] for row in rows] + [
            "OP030_transport_pallet_mount",
            "OP030B_check_transport_pallet_mount",
        ]:
            obj = bpy.data.objects.get(name)
            if obj:
                delete_tree(obj)
    wires = [build_wire(row, offset_y, connection_mode=args.connection_mode) for row in rows]
    # Static hardware is already moved. Only these newly rebuilt supply wires
    # need the same positive-determinant world transform, once.
    side_delta = np.diag([-1.0, -1.0, 1.0, 1.0])
    side_delta[1, 3] = 1.20
    for row in rows:
        obj = bpy.data.objects[row["uid"]]
        obj.matrix_world = Matrix((side_delta @ np.asarray(obj.matrix_world)).tolist())
    bpy.context.view_layer.update()
    retention = (
        dict(clips={}, metadata=dict(clips=[], transport_clips=False))
        if args.without_transport_clips
        else build_transport_clips(
            pallet,
            product,
            prefix="OP030B_check_transport",
            open_hinge_degrees=args.open_hinge_degrees,
            connection_mode=args.connection_mode,
        )
    )
    bpy.context.view_layer.update()
    actor_objects = {}
    for obj in scene.objects:
        node = _owner(obj)
        if _is_b(obj) and node is not None and (node in (576, 577, 578) or 1046 <= node < 1084 or 1086 <= node < 1124):
            parent = obj
            while parent and int(parent.get("source_node_id", -1)) != node:
                parent = parent.parent
            if parent:
                actor_objects[f"source_{node:04d}"] = parent
    for record in wires:
        for end, name in record["lugs"].items():
            actor_objects[name] = bpy.data.objects[name]
    clip_records = []
    for number, clip in retention["clips"].items():
        for obj in [clip["swing"], *clip["pads"]]:
            actor_objects[obj.name] = obj
        clip_records.append(
            {
                "number": number,
                "swing": clip["swing"].name,
                "swing_rest": np.asarray(clip["swing"].matrix_parent_inverse @ clip["swing"].matrix_basis).tolist(),
                "fixed_world": (inverse_offset @ np.asarray(clip["fixed"].matrix_world)).tolist(),
                "head_local": np.asarray(clip["head"].matrix_basis).tolist(),
                "pads": [obj.name for obj in clip["pads"]],
            }
        )
    names, nodes, actors, vertices, faces = [], [], [], [], []
    vertex_offsets, face_offsets = [0], [0]
    graph = bpy.context.evaluated_depsgraph_get()
    deforming = {record["insulation"] for record in wires}
    original_name = {obj.name: name for name, obj in actor_objects.items()}
    for obj in sorted(scene.objects, key=lambda item: item.name):
        if obj.type not in {"MESH", "CURVE"} or obj.hide_render or obj.name in deforming:
            continue
        world = inverse_offset @ np.asarray(obj.matrix_world)
        corners = np.asarray(obj.bound_box) @ world[:3, :3].T + world[:3, 3]
        node = _owner(obj)
        robot = (
            _is_b(obj) and node is not None and (node in (576, 577, 578) or 1046 <= node < 1084 or 1086 <= node < 1124)
        )
        if not robot and not (
            np.all(corners.max(0) > [-0.85, -3.20, 0.25]) and np.all(corners.min(0) < [2.80, -0.20, 2.80])
        ):
            continue
        actor = f"source_{node:04d}" if robot else ""
        if not robot:
            parent = obj
            while parent:
                if parent.name in original_name:
                    actor = original_name[parent.name]
                    break
                parent = parent.parent
        local = np.asarray(actor_objects[actor].matrix_world.inverted() @ obj.matrix_world) if actor else world
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        p = np.asarray([vertex.co[:] for vertex in mesh.vertices])
        f = np.asarray([triangle.vertices[:] for triangle in mesh.loop_triangles])
        if len(p) and len(f):
            p = p @ local[:3, :3].T + local[:3, 3]
            vertices.extend(p.tolist())
            faces.extend(f.tolist())
            vertex_offsets.append(len(vertices))
            face_offsets.append(len(faces))
            names.append(obj.name)
            nodes.append(node if robot else -1)
            actors.append(actor)
        evaluated.to_mesh_clear()
    output = ROOT / "data" / (args.output + ".npz")
    actor_names = sorted(set(actors) - {""})
    np.savez_compressed(
        output,
        names=np.array(names),
        nodes=np.array(nodes),
        actors=np.array(actors),
        vertices=np.asarray(vertices),
        faces=np.asarray(faces),
        vertex_offsets=vertex_offsets,
        face_offsets=face_offsets,
        actor_world_names=np.array(actor_names),
        actor_world=np.array([inverse_offset @ np.asarray(actor_objects[name].matrix_world) for name in actor_names]),
        fixed_base=inverse_offset @ np.asarray(actor_objects["source_0576"].matrix_world),
    )
    scene["split_b_check_wire_inventory"] = json.dumps(wires, ensure_ascii=False)
    snapshot = ROOT / "analysis" / (args.output + "_snapshot.blend")
    bpy.ops.wm.save_as_mainfile(filepath=str(snapshot), compress=True)
    report = {
        "observed_at": datetime.now().astimezone().isoformat(),
        "native_input": str(args.native),
        "native_input_sha256": native_sha,
        "native_snapshot": str(snapshot),
        "snapshot_sha256": digest(snapshot),
        "output_sha256": digest(output),
        "meshes": len(names),
        "triangles": len(faces),
        "wire_inventory": wires,
        "clip_actors": clip_records,
        "clip_metadata": retention["metadata"],
        "coordinate_frame": "Global native minus ST B +2.30m Y translation",
        "stagger_robot_base_baseline_m": [0.9, -1.7, 0.0],
        "static_side_transform_applied_again": False,
        "newly_rebuilt_wire_side_transform_count": 1,
        "reuse_exporter": "export_op030_split_b_meshes.py; positive-X spatial selection and explicit rebuilt-wire D",
        "drawer_extension_m": 0.340,
        "open_hinge_degrees": args.open_hinge_degrees,
        "connection_mode": args.connection_mode,
        "transport_clips": not args.without_transport_clips,
        "fixed_transport_height": args.fixed_transport_height,
        "neighbor_parks": neighbor_parks,
        "installed_a_parts": installed_parts,
        "deforming_wire_insulation": "Rebuild exact fixed-topology tube mesh from each target shape during FCL checks",
        "formal_physical_verdict": None,
        "scope": (
            "Separate working-scene actual mesh export, including the four installed ST A M4 bolts"
            if installed_parts
            else "Separate working-scene actual mesh export; ST A bolt hardware has not been added"
        ),
        "sources": {
            str(path.relative_to(ROOT)): digest(path)
            for path in (
                Path(__file__),
                ROOT / "scripts/build_op030_split_v03.py",
                ROOT / "scripts/op030_split_transport.py",
                ROOT / "scripts/op030_split_wire.py",
                ROOT / "audit/op030_split_wire_motion_initial.json",
            )
        },
    }
    (ROOT / "audit" / (args.output + ".json")).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("OP030B_MESH_EXPORT_COMPLETE", len(names), len(faces), flush=True)


if __name__ == "__main__":
    main()
