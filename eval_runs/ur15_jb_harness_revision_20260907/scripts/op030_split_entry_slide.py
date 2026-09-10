# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Retract the retained OP020 tooling together on a guided table [m]."""

import hashlib
import json
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from op030_geometry import box, materials


def build_entry_tooling_slide() -> dict:
    """Retain all tooling interfaces and add an outward 0.285 m table stroke [m].

    Reuses the delivered supply drawer's open guide-channel architecture and
    its actual hollow-cylinder, piston, rod and mount meshes. The table and
    receiver/C1/C2 relative transforms stay unchanged at the engaged position.
    This is provisional mechanism geometry, without a selected load rating.
    """
    scene = bpy.context.scene
    if "split_entry_tooling_slide" in scene:
        raise RuntimeError("The entry tooling slide is already built")
    machine = bpy.data.objects["OP020_direct_mating_station"]
    fixed = bpy.data.objects.new("OP020_transfer_slide_fixed", None)
    carriage = bpy.data.objects.new("OP020_transfer_slide_carriage", None)
    scene.collection.objects.link(fixed)
    scene.collection.objects.link(carriage)
    selected = [obj for obj in machine.children if obj.name.endswith("_table") or "_receiver_" in obj.name] + [
        bpy.data.objects[name] for name in ("OP020_direct_C1_guided_press", "OP020_direct_C2_lever_actuator")
    ]
    original = {obj.name: np.asarray(obj.matrix_world).tolist() for obj in selected}
    for obj in selected:
        world = obj.matrix_world.copy()
        obj.parent = carriage
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_basis = world
    columns = [obj for obj in machine.children if "_column" in obj.name]
    for obj in columns:
        obj.scale.z *= 0.317 / 0.342
        obj.location.z -= 0.0125
    mats = materials()
    guides = []
    for y in (-2.23, -2.48):
        specifications = [
            ("floor", (1.18, 0.048, 0.004), (1.17, y, 0.337), "metal", fixed),
            ("bearing", (1.18, 0.030, 0.003), (1.17, y, 0.3405), "black", fixed),
            ("moving_bar", (0.50, 0.027, 0.010), (1.0, y, 0.347), "blue", carriage),
            ("moving_neck", (0.36, 0.014, 0.009), (1.0, y, 0.3555), "blue", carriage),
        ]
        for sign in (-1, 1):
            specifications.extend(
                [
                    (f"side{sign}", (1.18, 0.004, 0.016), (1.17, y + sign * 0.022, 0.347), "metal", fixed),
                    (f"lip{sign}", (1.18, 0.010, 0.003), (1.17, y + sign * 0.014, 0.3535), "metal", fixed),
                ]
            )
        for suffix, dimensions, center, material, parent in specifications:
            obj = box(f"OP020_transfer_slide_{suffix}_{y}", dimensions, center, mats[material], parent, 0)
            guides.append(obj.name)
    drive = []
    shift = Vector((3.155, -0.355, -0.575))
    source_objects = [obj for obj in scene.objects if obj.name.startswith("OP030_supply_actuator_")]
    for source in source_objects:
        if source.name.endswith("_supply_hose"):
            continue
        obj = source.copy()
        obj.name = source.name.replace("OP030_supply_actuator", "OP020_transfer_slide_actuator")
        scene.collection.objects.link(obj)
        moving = source.name.endswith(("_piston", "_rod", "_kit_clevis"))
        obj.parent = carriage if moving else fixed
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_basis = source.matrix_basis.copy()
        obj.location += shift
        if source.name.endswith("_kit_clevis"):
            obj.scale.z *= 0.0875 / 0.081
            obj.location.z = 0.31625
        drive.append(obj.name)
    for x in (0.955, 1.180):
        box(
            f"OP020_transfer_slide_drive_crossbar_{x}",
            (0.035, 0.250, 0.025),
            (x, -2.355, 0.2205),
            mats["metal"],
            fixed,
            0,
        )
        for y in (-2.23, -2.48):
            box(
                f"OP020_transfer_slide_drive_hanger_{x}_{y}",
                (0.035, 0.025, 0.102),
                (x, y, 0.284),
                mats["metal"],
                fixed,
                0,
            )
    bpy.context.view_layer.update()
    preservation = max(
        float(np.max(abs(np.asarray(bpy.data.objects[name].matrix_world) - matrix)))
        for name, matrix in original.items()
    )
    assert preservation < 1e-7
    record = dict(
        fixed=fixed.name,
        carriage=carriage.name,
        stroke_m=0.285,
        axis_world=[1, 0, 0],
        engaged_world=np.eye(4).tolist(),
        retracted_world=(np.eye(4) + np.array([[0, 0, 0, 0.285], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])).tolist(),
        retained_tooling=[obj.name for obj in selected],
        retained_tooling_original_world=original,
        retained_tooling_max_pose_delta_m=preservation,
        shortened_columns=[obj.name for obj in columns],
        column_height_before_m=0.342,
        column_height_after_m=0.317,
        guide_stack_height_m=0.025,
        guides=guides,
        reused_drive_meshes=drive,
        source_reuse="op030_geometry.supply_kit channel architecture; actual OP030_supply_actuator meshes",
        drive_bore_m=0.032,
        retained_drive_maximum_stroke_m=0.340,
        geometry_scope=(
            "Candidate guided slide with retained hollow cylinder; pressure, force and load rating unselected"
        ),
        formal_physical_validity_verdict=None,
    )
    scene["split_entry_tooling_slide"] = json.dumps(record, ensure_ascii=False)
    return record


def set_entry_robot_park(bank_file: str | Path) -> dict:
    """Reuse the stored empty-hand supply-side OP020 pose at author time zero [m, rad, s].

    This selects an initial stationary pose for the new film. It does not
    claim a continuous connection from the previous film's final inspection.
    """
    bank_file = Path(bank_file)
    with np.load(bank_file) as saved:
        nodes, poses = saved["node_ids"].copy(), saved["poses"][0].copy()
        record = dict(
            bank=str(bank_file),
            bank_sha256=hashlib.sha256(bank_file.read_bytes()).hexdigest(),
            frame_index=0,
            author_time_s=float(saved["times"][0]),
            joints_rad=saved["joints"][0].tolist(),
            grips=saved["grips"][0].tolist(),
            original_fk_residuals=saved["errors"][0].tolist(),
            node_ids=nodes.tolist(),
            poses=poses.tolist(),
            scope="Stored pre-grasp empty-hand configuration; stationary film start, no endpoint-connection claim",
        )

    def depth(obj):
        return 0 if obj.parent is None else 1 + depth(obj.parent)

    objects = [(bpy.data.objects[f"source_{int(node):04d}"], matrix) for node, matrix in zip(nodes, poses, strict=True)]
    for level in sorted({depth(obj) for obj, _ in objects}):
        for obj, matrix in objects:
            if depth(obj) == level:
                obj.matrix_world = Matrix(matrix)
        bpy.context.view_layer.update()
    bpy.context.scene["split_entry_robot_park"] = json.dumps(record, ensure_ascii=False)
    return record
