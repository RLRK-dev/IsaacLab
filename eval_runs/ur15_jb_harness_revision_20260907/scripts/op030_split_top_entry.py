# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Separate provisional top-entry J1 interfaces from retained rear-entry data."""

from __future__ import annotations

import json
import math
from typing import Literal

import numpy as np
from op030_definition import J1_Y, ROOT, lug_frame, pose

ConnectionMode = Literal["rear_entry", "top_entry"]
J1_TOP_ENTRY_INSET_M = 0.020


def j1_lug_frame(number: int, connection_mode: ConnectionMode = "rear_entry") -> np.ndarray:
    """Return the product-local lug seating frame [m]."""
    if number not in (1, 2):
        raise ValueError(number)
    if connection_mode == "rear_entry":
        return lug_frame(number, "J1")
    if connection_mode != "top_entry":
        raise ValueError(connection_mode)
    return pose(location=(-0.1995, J1_Y[number - 1], 0.024))


def j1_lug_part(connection_mode: ConnectionMode = "rear_entry") -> str:
    """Return the manufacturer lug part for an explicit connection mode."""
    if connection_mode not in ("rear_entry", "top_entry"):
        raise ValueError(connection_mode)
    return "6R6" if connection_mode == "top_entry" else "46R6"


def j1_lug_mesh(connection_mode: ConnectionMode = "rear_entry") -> tuple[np.ndarray, list[list[int]]]:
    """Return unscaled vendor vertices [m] and triangle indices."""
    if connection_mode == "rear_entry":
        from op030_split_wire import lug_mesh

        return lug_mesh("46R6")
    if connection_mode != "top_entry":
        raise ValueError(connection_mode)
    saved = json.loads((ROOT / "inputs/op030_reference/Klauke_6R6.json").read_text())
    v = np.asarray(saved["vertices"], dtype=float)
    return np.column_stack((v[:, 0] + 37, -v[:, 2], v[:, 1] + 8)) / 1000, saved["faces"]


def top_entry_flange_to_tcp() -> np.ndarray:
    """Return straight M6 tool0-to-socket calibration [m]."""
    from op030_split_tools import driver_flange_to_tcp

    return driver_flange_to_tcp("M4")


def top_entry_spec() -> dict:
    """Return the shared, provisional assembly configuration with SI lengths [m]."""
    return {
        "connection_mode": "top_entry",
        "j1_inset_m": J1_TOP_ENTRY_INSET_M,
        "lug_part": "6R6",
        "lug_frames_product": [j1_lug_frame(n, "top_entry").tolist() for n in (1, 2)],
        "lug_entrance_local_m": [0.037, 0.0, 0.008],
        "lug_thickness_m": 0.0038,
        "lug_hole_diameter_m": 0.0064,
        "heatshrink_center_local_m": [0.0305, 0.0, 0.008],
        "heatshrink_length_m": 0.023,
        "conductor_center_local_m": [0.0275, 0.0, 0.008],
        "conductor_length_m": 0.019,
        "sleeve_axis": "local +X",
        "terminal_pitch_m": 0.023,
        "pad_dimensions_m": [0.022, 0.020, 0.003],
        "pad_surface_z_m": 0.024,
        "stud_diameter_m": 0.006,
        "stud_pitch_m": 0.001,
        "stud_protrusion_m": 0.014,
        "insertion_z_m": 0.020,
        "tool_flange_to_tcp": top_entry_flange_to_tcp().tolist(),
        "incoming_subassembly": "J1-TOP20: retained external mating header, two insulated internal L-busbars, "
        "two permanently retained vertical M6x14 studs; supplied assembled before line entry",
        "scope": (
            "Separate v03 packaging prototype, "
            "not a released TE/Klauke electrical assembly or tool selection."  # codespell:ignore te
        ),
    }


def build_top_entry_header(product, name: str = "OP030_J1_top_entry_connections") -> dict:
    """Build incoming internal conductors and studs, preserving external J1/E01 [m]."""
    import bpy
    from op030_geometry import box, cylinder, empty, materials, thread_stud

    if bpy.data.objects.get(name):
        raise ValueError(name)
    old = [obj for obj in product.children_recursive if "OP030_J1_rear_power_connections" in obj.name]
    retained_insulators = [obj.name for obj in old if obj.name.endswith("_insulator")]
    if len(retained_insulators) != 2:
        raise ValueError("Expected both original J1 insulating collars")
    removed = []
    for obj in old:
        if obj.type == "MESH" and obj.name.endswith(("_M6x14", "_pin_extension")):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    root = empty(name, product)
    metal = materials()["metal"]
    contacts = []
    for number, y in enumerate(J1_Y, 1):
        prefix = name + f"_P{number}"
        # The retained contact ends at product X=-227 mm. The round continuation
        # passes through the original insulating collar before rising inside.
        pin = cylinder(prefix + "_round_contact", 0.004, 0.028, (-0.213, y, 0.012), metal, root, (0, math.pi / 2, 0))
        web = box(prefix + "_riser", (0.004, 0.016, 0.012), (-0.2055, y, 0.017), metal, root, 0.0005)
        pad = box(prefix + "_pad", (0.022, 0.020, 0.003), (-0.1995, y, 0.0225), metal, root, 0.0005)
        # Join the three conductive portions into one visible continuous part.
        bpy.context.view_layer.update()
        for other in (web, pad):
            modifier = pin.modifiers.new("continuous_busbar", "BOOLEAN")
            modifier.operation, modifier.solver, modifier.object = "UNION", "EXACT", other
            with bpy.context.temp_override(object=pin, active_object=pin):
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(other, do_unlink=True)
        pin.name = prefix + "_L_busbar"
        stud = thread_stud(prefix + "_M6x14_vertical", 0.006, 0.001, 0.014, metal, root)
        stud.location = (-0.1995, y, 0.024)
        pin["construction"] = "preassembled formed conductor; round mating section, riser and horizontal pad"
        stud["retention"] = "permanently retained incoming terminal stud; method/material/torque remain unselected"
        contacts.append([pin.name, stud.name, "stud root at pad Z24 mm; incoming retained interface"])
    root["incoming_subassembly"] = top_entry_spec()["incoming_subassembly"]
    root["definition_status"] = top_entry_spec()["scope"]
    root["nominal_terminal_pitch_m"] = 0.023
    return {
        "root": root,
        "removed_old_meshes": removed,
        "retained_insulators": retained_insulators,
        "intended_contacts": contacts,
        "spec": top_entry_spec(),
    }


def build_top_entry_driver(name, flange, *, camera_root=None, gripper_nodes=None, side="left"):
    """Reuse fixed straight-tool mount/body and replace its working socket by M6 [m]."""
    import bpy
    from op030_geometry import materials, ring
    from op030_split_tools import build_fixed_driver

    assembly = build_fixed_driver(
        name,
        "M4",
        flange,
        fastener_kind="nut",
        gripper_nodes=gripper_nodes,
        camera_root=camera_root,
        side=side,
        camera_position=(-0.090, 0, 0.060),
    )
    for obj in list(assembly.spindle.children):
        if obj.name.endswith(("_socket", "_vacuum_retention_tip")):
            bpy.data.objects.remove(obj, do_unlink=True)
    ring(
        name + "_tool_socket",
        0.00515,
        0.008,
        0.024,
        (0, 0, 0.012),
        materials()["metal"],
        assembly.spindle,
        hex_inner=True,
    )
    ring(
        name + "_vacuum_retention_tip",
        0.00516,
        0.008,
        0.002,
        (0, 0, 0.001),
        materials()["black"],
        assembly.spindle,
        hex_inner=True,
    )
    assembly.root["thread_size"] = "M6"
    assembly.root["tool_variant"] = "straight_M6_top_entry"
    assembly.tool["scope"] = "fixed straight M6 envelope; reused M4/M14 100x42x42 motor, 156mm shaft and M6 socket"
    return assembly


def apply_top_entry_wire(root, number: int) -> dict:
    """Replace a canonical wire's J1 lug and its rigid insulation details [m].

    The caller must also supply the new flexible centerline from top-entry
    WireBend. This helper deliberately does not invent a second route model.
    """
    import bpy
    from mathutils import Matrix
    from op030_geometry import material, mesh_object

    frame = next(obj for obj in root.children_recursive if obj.type == "EMPTY" and obj.name.endswith("_J1"))
    old = [obj for obj in frame.children if obj.type == "MESH" and obj.name.endswith("_46R6")]
    if len(old) != 1:
        raise ValueError("Expected exactly one old J1 46R6 mesh on canonical wire")
    removed = old[0].name
    bpy.data.objects.remove(old[0], do_unlink=True)
    frame.matrix_basis = Matrix(j1_lug_frame(number, "top_entry").tolist())
    vertices, faces = j1_lug_mesh("top_entry")
    lug = mesh_object(
        frame.name + "_6R6",
        vertices.tolist(),
        faces,
        material("OP030_tinned_copper", (0.65, 0.66, 0.64), 0.80, 0.29),
        frame,
    )
    vendor = json.loads((ROOT / "inputs/op030_reference/Klauke_6R6.json").read_text())
    lug["vendor_part"], lug["source_sha256"] = "6R6", vendor["source_sha256"]
    lug["geometry_reuse"] = "All vendor vertices/faces; proper rigid transform and mm-to-m only"
    for face in lug.data.polygons:
        face.use_smooth = True
    for suffix, center in (("_conductor_in_barrel", (0.0275, 0, 0.008)), ("_heatshrink", (0.0305, 0, 0.008))):
        obj = next(obj for obj in frame.children if obj.name.endswith(suffix))
        obj.location = center
        obj.rotation_euler = (0, math.pi / 2, 0)
    root["connection_mode"] = "top_entry"
    root["incoming_wire_bom"] = f"H03-{number}: prefabricated/crimped 6R6 at J1, retained 6R14 at T; new cut length"
    return {"removed_old_lug": removed, "new_lug": lug.name, "j1_frame": frame.name, "spec": top_entry_spec()}


def internal_wire_top_entry(number: int, *, route: np.ndarray):
    """Build a canonical top-entry wire using the caller's shared centerline [m]."""
    import bpy
    from op030_geometry import internal_wire, materials, tube

    route = np.asarray(route, dtype=float)
    if route.ndim != 2 or route.shape[1] != 3:
        raise ValueError("Expected centerline points [N,3] in product coordinates")
    expected = j1_lug_frame(number, "top_entry") @ np.array([0.037, 0, 0.008, 1])
    if np.linalg.norm(route[0] - expected[:3]) > 1e-6:
        raise ValueError("Top-entry route must start at the shared 6R6 barrel entrance")
    root = internal_wire(number)
    apply_top_entry_wire(root, number)
    old = next(obj for obj in root.children if obj.name.endswith("_insulation"))
    name = old.name
    bpy.data.objects.remove(old, do_unlink=True)
    cable = tube(name, route, 0.007, materials()["orange"], root)
    cable["drawn_centerline_length_m"] = float(np.linalg.norm(np.diff(route, axis=0), axis=1).sum())
    return root
