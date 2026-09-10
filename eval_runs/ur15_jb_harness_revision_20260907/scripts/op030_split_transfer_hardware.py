# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Retain the three inherited transfer units while clearing their pallet envelope [m]."""

import json

import bpy
import numpy as np
from op030_geometry import box, cylinder, materials


def build_transfer_hardware() -> dict:
    """Apply one shared A/B/C transfer-hardware candidate [m].

    The original 0.055 m stopper stroke is retained after lowering its full
    body/blade mounting by 0.065 m. Existing separate pads support the pallet;
    the old 0.052 m diameter collars gain 0.050 m clearance bores and carry no
    assigned support load. Sensors move outward by 0.032 m on added brackets.

    Returns:
        Exact actor names and world transforms for the retained stopper stroke.
    """
    scene = bpy.context.scene
    if "split_transfer_hardware" in scene:
        raise RuntimeError("Transfer hardware delta is already applied")
    layout = json.loads(scene["split_layout_manifest"])
    mats = materials()
    result = dict(
        stopper_mount_down_m=0.065,
        stopper_stroke_m=0.055,
        collar_outer_diameter_m=0.052,
        collar_clearance_diameter_m=0.050,
        collar_radial_wall_m=0.001,
        collar_role="Clearance guide only; support remains on the existing separate seating pads",
        sensor_outward_m=0.032,
        cells={},
        bracket_scope="Provisional welded steel mounting brackets; load rating and fabrication details unselected",
    )
    _apply_units(result, {prefix: layout[prefix] for prefix in ("OP030A", "OP030B", "OP030C")}, mats)
    scene["split_transfer_hardware"] = json.dumps(result, ensure_ascii=False)
    return result


def _apply_units(result, units, mats):
    for prefix, info in units.items():
        aliases = info["source_names"]
        root = bpy.data.objects[info["root"]]
        body, blade, sensor = [bpy.data.objects[aliases[f"source_{node:04d}"]] for node in (685, 686, 687)]
        original = {obj.name: np.asarray(obj.matrix_world).tolist() for obj in (body, blade, sensor)}
        body.location.z -= 0.065
        blade.location.z -= 0.065
        sensor.location.x += 0.032
        platen = bpy.data.objects[aliases["source_0684"]]
        collar = bpy.data.objects[aliases["source_0684_m0111_p02"]]
        collar.data = collar.data.copy()
        for index, x in enumerate((-0.12, 0.12)):
            cutter = cylinder(
                prefix + f"_collar_clearance_cutter_{index}", 0.025, 0.060, (x, 0, 0.020), mats["metal"], platen
            )
            bpy.context.view_layer.update()
            modifier = collar.modifiers.new("bush_outer_clearance", "BOOLEAN")
            modifier.operation, modifier.solver, modifier.object = "DIFFERENCE", "EXACT", cutter
            with bpy.context.temp_override(object=collar, active_object=collar):
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(cutter, do_unlink=True)
        brackets = []
        for sign in (-1, 1):
            name = prefix + f"_stopper_drop_bracket_{sign:+d}"
            leg = box(name, (0.012, 0.012, 0.152), (0.476, -1.24 + sign * 0.086, 0.224), mats["metal"], root, 0)
            foot = box(
                name + "_foot_union",
                (0.052, 0.084, 0.008),
                (0.496, -1.24 + sign * 0.050, 0.152),
                mats["metal"],
                root,
                0,
            )
            bpy.context.view_layer.update()
            modifier = leg.modifiers.new("continuous_L_bracket", "BOOLEAN")
            modifier.operation, modifier.solver, modifier.object = "UNION", "EXACT", foot
            with bpy.context.temp_override(object=leg, active_object=leg):
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(foot, do_unlink=True)
            leg["mount_interfaces"] = (
                "Frame outer face X=0.470; unit base underside Z=0.156, baseline cell coordinates [m]"
            )
            brackets.append(leg.name)
        for suffix, y, top, width_y in (("photoeye", -1.40, 0.387, 0.070), ("RFID", -1.86, 0.3825, 0.075)):
            name = prefix + "_sensor_extension_bracket_" + suffix
            bracket = box(name, (0.088, width_y, 0.006), (0.514, y, top - 0.003), mats["metal"], root, 0)
            bracket["mount_interfaces"] = f"Frame outer face X=0.470; sensor original underside Z={top:.4f} [m]"
            brackets.append(bracket.name)
        bpy.context.view_layer.update()
        up = np.asarray(blade.matrix_world).copy()
        down = up.copy()
        down[2, 3] -= 0.055
        result["cells"][prefix] = dict(
            body=body.name,
            stopper=blade.name,
            sensor=sensor.name,
            collar_mesh=collar.name,
            original_world_poses=original,
            stopper_up_world=up.tolist(),
            stopper_down_world=down.tolist(),
            body_world=np.asarray(body.matrix_world).tolist(),
            sensor_world=np.asarray(sensor.matrix_world).tolist(),
            collar_platen=platen.name,
            brackets=brackets,
            offset_y_m=info["offset_y_m"],
        )


def build_entry_transfer_hardware() -> dict:
    """Apply the same retained hardware correction to the OP020 entry unit [m].

    Call after :func:`build_transfer_hardware`. The entry station uses its
    original source 0672–0675 actors and remains outside the three new cells.
    The original pilot-pin length is unchanged by this mounting correction.
    """
    scene = bpy.context.scene
    result = json.loads(scene["split_transfer_hardware"])
    if "OP020" in result["cells"]:
        raise RuntimeError("Entry transfer hardware delta is already applied")
    root = bpy.data.objects.new("OP020_transfer_mount", None)
    scene.collection.objects.link(root)
    root.location.y = -1.15
    bpy.context.view_layer.update()
    info = dict(
        root=root.name,
        offset_y_m=-1.15,
        source_names={
            "source_0684": "source_0672",
            "source_0684_m0111_p02": "source_0672_m0099_p02",
            "source_0685": "source_0673",
            "source_0686": "source_0674",
            "source_0687": "source_0675",
        },
    )
    _apply_units(result, {"OP020": info}, materials())
    scene["split_transfer_hardware"] = json.dumps(result, ensure_ascii=False)
    return result


def build_entry_pallet_release() -> dict:
    """Reuse ST A's 45 mm pilot tips and support pads at the OP020 entry [m].

    The original OP020 platen starts at Z=0.392 m. It lowers to 0.378 m
    with the pallet, then to 0.341 m alone before longitudinal transport.
    """
    scene = bpy.context.scene
    result = json.loads(scene["split_transfer_hardware"])
    entry = result["cells"]["OP020"]
    if "pallet_release" in entry:
        raise RuntimeError("Entry pallet-release delta is already applied")
    platen = bpy.data.objects[entry["collar_platen"]]
    pins = bpy.data.objects["source_0672_m0099_p01"]
    pins.data = pins.data.copy()
    for vertex in pins.data.vertices:
        vertex.co.z = 0.0065 + (vertex.co.z - 0.0065) * (0.045 - 0.0065) / (0.077 - 0.0065)
    pads = []
    for y in (-0.115, 0.115):
        obj = box(
            f"OP020_transfer_seating_pad_{y}",
            (0.260, 0.030, 0.0235),
            (0, y, 0.03775),
            materials()["black"],
            platen,
            0,
        )
        pads.append(obj.name)
    entry["pallet_release"] = dict(
        platen=platen.name,
        pins=pins.name,
        pads=pads,
        original_pilot_tip_z_m=0.077,
        pilot_tip_z_m=0.045,
        platen_up_z_m=0.392,
        platen_seated_z_m=0.378,
        platen_withdrawn_z_m=0.341,
        reuse="Exact linear pin projection and pad dimensions already used by op030_geometry.pallet_lift",
    )
    bpy.context.view_layer.update()
    scene["split_transfer_hardware"] = json.dumps(result, ensure_ascii=False)
    return entry["pallet_release"]
