# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Integrate three OP030 stations, permanent tools and finite supply [m]."""

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import bpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_allocation_review import camera
from continuous_common import delete_tree, digest, write_json
from op020_jb_geometry import box, materials
from op030_definition import ROOT, pose
from op030_geometry import internal_wire
from op030_split_entry_clearance import build_entry_lift_guides, refine_entry_tooling_clearance
from op030_split_entry_slide import build_entry_tooling_slide, set_entry_robot_park
from op030_split_layout import build_layout, descendants
from op030_split_tools import build_fastener_feeder, build_fixed_driver, convert_support_mounts_to_bolts
from op030_split_top_entry import build_top_entry_driver, build_top_entry_header, internal_wire_top_entry
from op030_split_transfer_hardware import (
    build_entry_pallet_release,
    build_entry_transfer_hardware,
    build_transfer_hardware,
)
from op030_split_transport import build_transport_clips, build_wire_supply
from op030_split_wire import WireBend


def feeder_stand(assembly):
    """Support a feeder base with floor-mounted legs [m]."""
    root = assembly.root
    mats = materials()
    base = bpy.data.objects[root.name + "_base"]
    height = float(root.matrix_world.translation.z) - 0.172
    center_x = base.location.x
    for x in (center_x - 0.10, center_x + 0.10):
        box(
            root.name + f"_stand_{x:.3f}",
            (0.040, 0.14, height - 0.014),
            (x, 0, -0.172 - (height - 0.014) / 2),
            mats["metal"],
            root,
        )
        box(
            root.name + f"_foot_{x:.3f}",
            (0.12, 0.20, 0.014),
            (x, 0, -float(root.matrix_world.translation.z) + 0.007),
            mats["black"],
            root,
        )


def build_wire(row, offset_y, *, connection_mode="rear_entry"):
    """Create one persistent wire using the retained manufacturer lug meshes."""
    number, uid, shape = row["number"], row["uid"], row["shape"]
    bend = WireBend(number, connection_mode=connection_mode)
    root = (
        internal_wire_top_entry(number, route=bend.final_points)
        if connection_mode == "top_entry"
        else internal_wire(number)
    )
    original_name = root.name
    parts = {end: bpy.data.objects[original_name + "_" + end] for end in ("J1", "T")}
    insulation = bpy.data.objects[original_name + "_insulation"]
    for obj in reversed(descendants(root)):
        obj.name = obj.name.replace(original_name, uid, 1)
        obj.hide_viewport = obj.hide_render = False
    vertices, faces = bend.tube_mesh(shape)
    mesh = bpy.data.meshes.new(uid + "_straight_insulation_mesh")
    mesh.from_pydata(vertices.tolist(), [], faces.tolist())
    for material in insulation.data.materials:
        mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    insulation_name = insulation.name
    insulation_properties = dict(insulation.items())
    bpy.data.objects.remove(insulation, do_unlink=True)
    insulation = bpy.data.objects.new(insulation_name, mesh)
    bpy.context.scene.collection.objects.link(insulation)
    insulation.parent = root
    for key, value in insulation_properties.items():
        insulation[key] = value
    root.matrix_world = Matrix.Translation((0, offset_y, 0))
    for end, part in parts.items():
        part.matrix_basis = Matrix(shape.lug_frames[end].tolist())
    root["assembly_uid"] = uid
    root["supply_row"] = row["row"]
    root["supply_count"] = 10
    root["connection_mode"] = connection_mode
    root["visible_insulation_centerline_length_m"] = bend.length
    root["definition_status"] = "straight supply and bimanual bend candidate; wire and crimp process unselected"
    return dict(
        uid=uid,
        number=number,
        root=root.name,
        insulation=insulation.name,
        lugs={end: obj.name for end, obj in parts.items()},
        connection_mode=connection_mode,
        visible_insulation_centerline_length_m=bend.length,
    )


def build_static(output):
    """Build a separate native candidate from the digest-pinned latest v02."""
    layout = build_layout()
    scene = bpy.context.scene
    removed = []
    for number in (1, 2):
        for name in (f"OP030_H03_{number}_UID001", f"OP030_H03_{number}_UID001_T"):
            obj = bpy.data.objects.get(name)
            if obj:
                removed.extend(child.name for child in descendants(obj))
                delete_tree(obj)
    loose_fasteners = [
        obj
        for obj in scene.objects
        if obj.parent is None and obj.name.startswith(("OP030_T", "OP030_H03")) and "_nut" in obj.name
    ]
    for obj in loose_fasteners:
        removed.extend(child.name for child in descendants(obj))
        delete_tree(obj)
    drivers, feeders = {}, {}
    settings = (
        ("A", "left", "M4", "bolt", (-0.73, -2.65, 0.82)),
        ("C", "left", "M6", "nut", (-1.0, -2.65, 0.84)),
        ("C", "right", "M14", "nut", (-1.0, -0.75, 0.84)),
    )
    for cell, side, size, kind, position in settings:
        prefix = "OP030" + cell
        cell_map = layout["cells"][prefix]
        names = cell_map["source_names"]
        node = 1067 if side == "left" else 1107
        flange = bpy.data.objects[names[f"source_{node:04d}"]]
        camera_name = "onhand_OP030_" + side + "_mount"
        camera_root = bpy.data.objects.get(names.get(camera_name, camera_name))
        if cell != "A" and camera_root and not camera_root.name.startswith(prefix):
            raise RuntimeError("Wrong cell camera selected")
        gripper_nodes = [
            bpy.data.objects[names[f"source_{index:04d}"]]
            for index in range(node, node + 17)
            if f"source_{index:04d}" in names
        ]
        if size == "M6":
            assembly = build_top_entry_driver(
                prefix + "_driver_" + size,
                flange,
                gripper_nodes=gripper_nodes,
                camera_root=camera_root,
                side=side,
            )
        else:
            assembly = build_fixed_driver(
                prefix + "_driver_" + size,
                size,
                flange,
                fastener_kind=kind,
                gripper_nodes=gripper_nodes,
                camera_root=camera_root,
                side=side,
            )
        drivers[prefix + "_" + size] = dict(
            root=assembly.root.name,
            tcp=assembly.tool.name,
            spindle=assembly.spindle.name,
            flange=flange.name,
            flange_to_tcp=assembly.flange_to_tcp.tolist(),
            side=side,
            kind=kind,
            removed_gripper_meshes=assembly.removed_gripper_meshes,
            camera=assembly.camera_record,
        )
        world = pose(location=position)
        world[1, 3] += cell_map["offset_y_m"]
        feeder = build_fastener_feeder(
            prefix + "_feeder_" + size,
            size,
            kind,
            world,
            count=12,
            min_rail_length=0.387 if size == "M4" else 0.34,
        )
        feeder_stand(feeder)
        feeders[prefix + "_" + size] = dict(
            root=feeder.root.name,
            escapement=feeder.escapement.name,
            pickup=feeder.pickup.name,
            fasteners=[obj.name for obj in feeder.fasteners],
            pose=world.tolist(),
            count=12,
            kind=kind,
            size=size,
        )
    mount_record = convert_support_mounts_to_bolts(bpy.data.objects["JB_OP020_UID001"])
    header = build_top_entry_header(bpy.data.objects["JB_OP020_UID001"])
    header["root"] = header["root"].name
    supply = build_wire_supply(bpy.data.objects["OP030B_cell"], connection_mode="top_entry")
    wires = [
        build_wire(row, layout["cells"]["OP030B"]["offset_y_m"], connection_mode="top_entry") for row in supply["rows"]
    ]
    retention = build_transport_clips(
        bpy.data.objects["source_0292"],
        bpy.data.objects["JB_OP020_UID001"],
        open_hinge_degrees=90.0,
        connection_mode="top_entry",
    )
    build_transfer_hardware()
    build_entry_transfer_hardware()
    build_entry_pallet_release()
    entry_slide = build_entry_tooling_slide()
    entry_park = set_entry_robot_park(ROOT / "data/op020_direct_v10.npz")
    entry_lift = build_entry_lift_guides()
    entry_clearance = refine_entry_tooling_clearance()
    transfer_hardware = json.loads(scene["split_transfer_hardware"])
    # An engineering review camera outside the frame and stock closeups inside
    # it make the changed inventory and physical tool attachment inspectable.
    views = {
        "Review_OP030_split_overall": ((-5.6, -5.1, 4.3), (-0.4, 0.6, 0.85), 38),
        "Review_OP030_wide": ((-5.6, -5.1, 4.3), (-0.4, 0.6, 0.85), 38),
        "Review_OP030_split_entry": ((2.6, -4.2, 1.8), (0.6, -2.65, 0.7), 40),
        "Review_OP030_split_A": ((2.1, -3.7, 2.6), (-0.65, -1.7, 1.2), 35),
        "Review_OP030_split_B": ((2.1, -1.4, 2.6), (-0.65, 0.6, 1.2), 35),
        "Review_OP030_split_C": ((2.1, 0.9, 2.6), (-0.65, 2.9, 1.2), 35),
        "Review_OP030_split_A_stock": ((-2.3, -3.6, 2.15), (-0.35, -1.7, 0.95), 43),
        "Review_OP030_split_B_stock": ((-2.3, -1.3, 2.15), (-0.35, 0.6, 0.95), 43),
        "Review_OP030_support_supply": ((-1.60, -1.70, 2.0), (-1.68, -1.70, 1.0), 34),
        "Review_OP030_wire_supply": ((-2.04, 0.1, 2.30), (-2.02, 0.6, 1.00), 42),
        "Review_OP030_split_A_feeder": ((0.10, -3.30, 1.30), (-0.78, -2.66, 0.89), 48),
        "Review_OP030_split_C_M6_feeder": ((-0.17, 1.30, 1.32), (-1.05, 1.94, 0.91), 48),
        "Review_OP030_split_C_M14_feeder": ((-0.17, 3.20, 1.32), (-1.05, 3.84, 0.91), 48),
        "Review_OP030_split_A_joint": ((0.85, -2.25, 1.60), (0.02, -1.55, 0.93), 48),
        "Review_OP030_split_B_joint": ((0.85, 0.05, 1.60), (0.02, 0.75, 0.93), 48),
        "Review_OP030_split_C_joint": ((0.85, 2.35, 1.60), (0.02, 3.05, 0.93), 48),
    }
    for name, (eye, target, lens) in views.items():
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        camera(scene, name, eye, target, lens)
        if name == "Review_OP030_support_supply":
            bpy.data.objects[name].rotation_euler.rotate_axis("Z", math.pi / 2)
    scene.camera = bpy.data.objects["Review_OP030_split_overall"]
    exposure_before = scene.view_settings.exposure
    scene.view_settings.exposure = exposure_before - 1.0
    scene["process_completion"] = "OP030 three-ST candidate; native motion and checks recorded separately"
    scene["split_wire_inventory"] = json.dumps(wires, ensure_ascii=False)
    scene["split_fixed_tools"] = json.dumps(drivers, ensure_ascii=False)
    scene["split_fastener_feeders"] = json.dumps(feeders, ensure_ascii=False)
    bpy.context.view_layer.update()
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        evidence_basis="Native source readback and integrated geometry construction",
        source=layout["source"],
        source_sha256=layout["source_sha256"],
        layout=layout,
        drivers=drivers,
        feeders=feeders,
        support_mounts=mount_record,
        j1_connection=header,
        wire_supply=supply["metadata"],
        wires=wires,
        retention=retention["metadata"],
        transfer_hardware=transfer_hardware,
        entry_slide=entry_slide,
        entry_park=entry_park,
        entry_lift=entry_lift,
        entry_clearance=entry_clearance,
        display_exposure=dict(
            before_ev=exposure_before,
            after_ev=scene.view_settings.exposure,
            delta_ev=-1.0,
            purpose="Retain highlight detail for Cycles; scene light outputs remain unchanged",
            comparison="audit/op030_split_a_joint_exposure_snapshot.json",
        ),
        removed_superseded=removed,
        formal_physical_validity_verdict=None,
        scope="Static integrated candidate; motion validation is separate",
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(output), compress=True)
    report.update(output=str(output), output_sha256=digest(output))
    write_json(ROOT / "audit/op030_split_static_v03.json", report)
    print("OP030_SPLIT_STATIC_COMPLETE", str(output), len(wires), len(drivers), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "analysis/op030_split_static_v03.blend"))
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    build_static(Path(args.output))


if __name__ == "__main__":
    main()
