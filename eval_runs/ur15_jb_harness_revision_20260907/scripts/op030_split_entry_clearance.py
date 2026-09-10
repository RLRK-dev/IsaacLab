# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Apply the finite OP020 entry clearance corrections using the retained mechanisms [m]."""

import json
import math

import bpy
import numpy as np
from allocation_product import empty
from mathutils import Matrix, Vector
from op030_geometry import box, materials
from op030_split_layout import descendants, duplicate_set


def _open_entry_rollers() -> dict:
    """Reuse the original ST A half-roller construction around OP020 [m]."""
    changed = {}
    for suffix in ("p00", "p01"):
        obj = bpy.data.objects["source_0004_m0004_" + suffix]
        original = obj.data
        points = np.asarray([vertex.co[:] for vertex in original.vertices])
        labels = np.rint((points[:, 1] + 3.45) / 0.115).astype(int)
        vertices, faces, selected = [], [], []
        for label in np.unique(labels):
            ids = np.flatnonzero(labels == label)
            subset = points[ids]
            remap = {int(old): new for new, old in enumerate(ids)}
            polygons = [
                tuple(remap[v] for v in polygon.vertices)
                for polygon in original.polygons
                if polygon.vertices[0] in remap
            ]
            center_y = float((subset[:, 1].max() + subset[:, 1].min()) / 2)
            split = abs(center_y + 2.85) < 0.175
            if split:
                selected.append(center_y)
            for half in (-1, 1) if split else (0,):
                points_half = subset.copy()
                if half:
                    lower, upper = points_half[:, 0].min(), points_half[:, 0].max()
                    start, stop = (lower, -0.185) if half == -1 else (0.185, upper)
                    points_half[:, 0] = start + (points_half[:, 0] - lower) / (upper - lower) * (stop - start)
                offset = len(vertices)
                vertices.extend(points_half.tolist())
                faces.extend(tuple(v + offset for v in polygon) for polygon in polygons)
        mesh = bpy.data.meshes.new(original.name + "_OP020_entry_split")
        mesh.from_pydata(vertices, [], faces)
        for material in original.materials:
            mesh.materials.append(material)
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        obj.data = mesh
        obj["OP020_center_opening_m"] = 0.370
        obj["OP020_split_roller_centers_y_m"] = selected
        changed[obj.name] = selected
    return changed


def build_entry_lift_guides() -> dict:
    """Reuse ST A's complete folding guide linkage for the 51 mm OP020 release [m]."""
    scene = bpy.context.scene
    if "split_entry_lift" in scene:
        raise RuntimeError("Entry lift guide replacement is already built")
    source_fixed = bpy.data.objects["OP030_lift_fixed"]
    source_carriage = bpy.data.objects["OP030_lift_carriage"]
    exclude = set(descendants(bpy.data.objects["source_0684"]))
    originals = [
        obj
        for obj in descendants(source_fixed) + descendants(source_carriage)
        if obj not in exclude and not obj.name.startswith("OP030_lift_seating_pad_")
    ]
    cell = empty("OP020_transfer_lift_cell")
    cell.location.y = -1.15
    copies = duplicate_set(originals, "OP020_transfer_lift", cell)
    fixed, carriage = copies[source_fixed.name], copies[source_carriage.name]
    carriage.location.z = 0.0
    bpy.context.view_layer.update()
    platen = bpy.data.objects["source_0672"]
    world = platen.matrix_world.copy()
    platen.parent = carriage
    platen.matrix_parent_inverse = Matrix.Identity(4)
    platen.matrix_basis = carriage.matrix_world.inverted() @ world
    removed = []
    for name in ("source_0671_m0098_p02", "source_0671_m0098_p03"):
        obj = bpy.data.objects[name]
        removed.append(dict(name=obj.name, mesh=obj.data.name))
        bpy.data.objects.remove(obj, do_unlink=True)
    rollers = _open_entry_rollers()
    sheet = bpy.data.objects["source_0006_m0006_p00"]
    sheet.data = sheet.data.copy()
    cutter = box(
        "OP020_catch_sheet_opening_cutter",
        (0.370, 0.350, 0.100),
        (0, -2.85, 0.3075),
        materials()["metal"],
        bevel=0,
    )
    bpy.context.view_layer.update()
    modifier = sheet.modifiers.new("OP020_reused_A_catch_sheet_opening", "BOOLEAN")
    modifier.operation, modifier.solver, modifier.object = "DIFFERENCE", "EXACT", cutter
    with bpy.context.temp_override(object=sheet, active_object=sheet):
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    record = dict(
        fixed=fixed.name,
        carriage=carriage.name,
        cell=cell.name,
        platen=platen.name,
        carriage_engaged_local_z_m=0.0,
        carriage_seated_local_z_m=-0.014,
        carriage_withdrawn_local_z_m=-0.051,
        world_track_rule="carriage translation (0, -1.15, source0672_world_z - 0.392); platen is its child",
        copied_names={name: obj.name for name, obj in copies.items()},
        replaced_old_guides=removed,
        roller_opening_m=0.370,
        catch_sheet_opening_m=[0.370, 0.350],
        roller_centers_y_m=rollers,
        reuse="Actual ST A folding links, sliders, pivots, rods, case fasteners, and all their Blender drivers",
    )
    scene["split_entry_lift"] = json.dumps(record, ensure_ascii=False)
    return record


def refine_entry_tooling_clearance(c2_park: str = "inward_raised") -> dict:
    """Apply the approved table reliefs, sensor shift, and existing C2 pivot park [m]."""
    scene = bpy.context.scene
    if "split_entry_clearance" in scene:
        raise RuntimeError("Entry tooling clearance delta is already applied")
    hardware = json.loads(scene["split_transfer_hardware"])
    entry = hardware["cells"]["OP020"]
    sensor = bpy.data.objects[entry["sensor"]]
    sensor.location.y -= 0.100
    for name in entry["brackets"]:
        if "sensor_extension" in name:
            bpy.data.objects[name].location.y -= 0.100
    guide = bpy.data.objects["OP020_direct_C1_guided_press_guide-2.36"]
    bush = bpy.data.objects["OP020_direct_C1_guided_press_guide_bush-0.04"]
    guide.location.y += 0.015
    bush.location.y += 0.015
    if c2_park not in {"outward", "inward_raised"}:
        raise ValueError(c2_park)
    pivot = Vector((0.56, -2.55, 0.40))
    c2_names = ["OP020_direct_C2_lever_actuator_" + suffix for suffix in ("barrel", "rod", "roller_shoe")]
    plinth = None
    if c2_park == "outward":
        rotation = Matrix.Translation(pivot) @ Matrix.Rotation(math.pi, 4, "Y") @ Matrix.Translation(-pivot)
        for name in c2_names:
            obj = bpy.data.objects[name]
            obj.matrix_world = rotation @ obj.matrix_world
    else:
        c2_root = bpy.data.objects["OP020_direct_C2_lever_actuator"]
        c2_root.location.z += 0.040
        plinth = box(
            "OP020_transfer_C2_support_plinth",
            (0.080, 0.090, 0.026),
            (0.560, -2.550, 0.393),
            materials()["metal"],
            bpy.data.objects["OP020_transfer_slide_carriage"],
            0,
        )
    table = bpy.data.objects["OP020_direct_mating_station_table"]
    table.data = table.data.copy()
    for existing in list(table.modifiers):
        with bpy.context.temp_override(object=table, active_object=table):
            bpy.ops.object.modifier_apply(modifier=existing.name)
    cuts = [
        ("rear_edge", (0.60, 0.050, 0.080), (1.20, -2.575, 0.370)),
        ("stopper_edge", (0.120, 0.170, 0.080), (0.590, -2.390, 0.370)),
    ]
    for suffix, dimensions, center in cuts:
        cutter = box("OP020_table_relief_cutter_" + suffix, dimensions, center, materials()["metal"], bevel=0)
        bpy.context.view_layer.update()
        modifier = table.modifiers.new("entry_clearance_" + suffix, "BOOLEAN")
        modifier.operation, modifier.solver, modifier.object = "DIFFERENCE", "EXACT", cutter
        with bpy.context.temp_override(object=table, active_object=table):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
    bpy.context.view_layer.update()
    entry["sensor_world"] = np.asarray(sensor.matrix_world).tolist()
    entry["sensor_longitudinal_delta_m"] = -0.100
    scene["split_transfer_hardware"] = json.dumps(hardware, ensure_ascii=False)
    record = dict(
        sensor=entry["sensor"],
        sensor_delta_y_m=-0.100,
        shifted_c1_guide=guide.name,
        shifted_c1_bush=bush.name,
        c1_delta_y_m=0.015,
        c1_guide_pitch_before_m=0.080,
        c1_guide_pitch_after_m=0.065,
        c2_park_candidate=c2_park,
        c2_rotated_parts=c2_names if c2_park == "outward" else [],
        c2_raised_root="OP020_direct_C2_lever_actuator" if c2_park == "inward_raised" else None,
        c2_whole_unit_delta_z_m=0.040 if c2_park == "inward_raised" else 0,
        c2_support_plinth=plinth.name if plinth else None,
        c2_support_plinth_dimensions_m=[0.080, 0.090, 0.026] if plinth else None,
        c2_pivot_before_world_m=list(pivot),
        c2_pivot_world_m=list(pivot + Vector((0, 0, 0.040 if c2_park == "inward_raised" else 0))),
        c2_park_rotation_y_rad=math.pi if c2_park == "outward" else 0,
        c2_park_before_m=[0.35, -2.55, 0.40],
        c2_park_after_m=[0.77, -2.55, 0.40] if c2_park == "outward" else [0.35, -2.55, 0.44],
        table=table.name,
        table_nominal_dimensions_m=[0.92, 0.40, 0.020],
        table_relief_boxes=[
            dict(name=name, dimensions_m=list(dims), center_world_m=list(center)) for name, dims, center in cuts
        ],
        note="Table global bounds preserved; only rear X>=0.90/Y<=-2.55 strip and left stopper relief are removed",
    )
    scene["split_entry_clearance"] = json.dumps(record, ensure_ascii=False)
    return record
