# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Reusable ST B straight-wire supply and provisional pallet retention [m].

The existing OP030 guide channels, moving bars and 340-mm cylinder geometry
are copied as a mechanism. New support dimensions are packaging candidates,
not a selected cylinder, structural design or force validation.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from allocation_product import empty
from op020_jb_geometry import box, cylinder, materials
from op030_geometry import mesh_object, ring
from op030_split_layout import descendants, duplicate_set
from op030_split_top_entry import ConnectionMode
from op030_split_wire import WireBend, supply_layout

ROOT = Path(__file__).resolve().parent.parent
STOCK_CENTER = (-2.02, -1.70, 1.04)
ACTIVE_CENTER = (-1.68, -1.70, 1.04)
PALLET_DIMENSIONS = (0.650, 0.700, 0.010)
PALLET_TOP = 0.9485
DRAWER_STROKE = 0.340


def _discard_tree(obj: bpy.types.Object) -> list[str]:
    names = []
    for child in reversed(descendants(obj)):
        names.append(child.name)
        bpy.data.objects.remove(child, do_unlink=True)
    return names


def _arc_point(points: np.ndarray, distance: float) -> tuple[np.ndarray, np.ndarray]:
    lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    arc = np.r_[0.0, np.cumsum(lengths)]
    index = int(np.clip(np.searchsorted(arc, distance, side="right") - 1, 0, len(lengths) - 1))
    alpha = float(np.clip((distance - arc[index]) / lengths[index], 0.0, 1.0))
    point = points[index] * (1 - alpha) + points[index + 1] * alpha
    tangent = (points[index + 1] - points[index]) / lengths[index]
    return point, tangent


def _clip_distance(bend: WireBend, old_fraction: float) -> tuple[float, dict]:
    if bend.connection_mode == "rear_entry":
        return old_fraction * bend.length, {}
    old = WireBend(bend.number)
    distance = old_fraction * old.length
    index = int(np.searchsorted(old.arc, distance, side="right") - 1)
    alpha = float((distance - old.arc[index]) / old.lengths[index])
    mapped = float(bend.arc[index] + alpha * bend.lengths[index])
    old_point, _ = _arc_point(old.final_points, distance)
    point, _ = _arc_point(bend.final_points, mapped)
    if not np.allclose(point[:2], old_point[:2], atol=1e-12, rtol=0):
        raise ValueError("The retained clip segment no longer has the same product XY")
    return mapped, dict(
        contact_mapping="Retained rear-entry route segment and its barycentric position",
        reference_fraction=old_fraction,
        reference_arclength_m=distance,
        reference_segment_index=index,
        reference_segment_alpha=alpha,
        reference_center_product_m=old_point.tolist(),
        center_delta_from_reference_m=(point - old_point).tolist(),
    )


def _bore(obj, name, radius, depth, center, parent):
    cutter = cylinder(name, radius, depth, center, materials()["metal"], parent, vertices=64)
    bpy.context.view_layer.update()
    modifier = obj.modifiers.new(name="clip_mounting_bore", type="BOOLEAN")
    modifier.operation, modifier.solver, modifier.object = "DIFFERENCE", "EXACT", cutter
    with bpy.context.temp_override(object=obj, active_object=obj):
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def _mount_foot(name, pivot, plate_top, fixed, product, connection_mode):
    if connection_mode == "rear_entry":
        box(name + "_foot", (0.026, 0.030, 0.008), (pivot[0], pivot[1], plate_top + 0.004), materials()["metal"], fixed)
        return plate_top + 0.008, {}
    from op030_split_tools import build_fastener

    base = next(obj for obj in descendants(product) if obj.name.endswith("_F01_removable_transport_carrier_side_base"))
    inverse = product.matrix_world.inverted()
    base_top = max((inverse @ base.matrix_world @ Vector(p)).z for p in base.bound_box)
    foot = box(
        name + "_foot", (0.038, 0.030, 0.010), (pivot[0], pivot[1], base_top + 0.005), materials()["metal"], fixed
    )
    fasteners, holes = [], []
    for index, dx in enumerate((-0.013, 0.013)):
        center = (float(pivot[0] + dx), float(pivot[1]), base_top)
        _bore(foot, name + f"_foot_bore{index}", 0.00225, 0.030, center, fixed)
        # Reuse the existing M4 receiver's 4.2-mm simplified female-thread
        # envelope. It does not model female thread flanks or clamp force.
        bore_key = f"clip_bore_{pivot[1]:.9f}_{dx:.3f}"
        if not base.get(bore_key):
            base.data = base.data.copy()
            _bore(base, name + f"_base_bore{index}", 0.0021, 0.020, center, fixed)
            base[bore_key] = True
        bolt = build_fastener(name + f"_mount_M4_UID{index + 1:03d}", "M4", "bolt", fixed)
        bolt.location = (*center[:2], base_top + 0.010)
        bolt["assembly_role"] = "Permanent F01 pallet clip mount; not an ST A process fastener"
        fasteners.append(bolt.name)
        holes.append(dict(center_product_m=list(center), foot_diameter_m=0.0045, base_envelope_diameter_m=0.0042))
    return base_top + 0.010, dict(
        mounting_base=base.name,
        foot_bottom_product_z_m=base_top,
        foot_dimensions_m=[0.038, 0.030, 0.010],
        post_bottom_product_z_m=base_top + 0.010,
        fixed_fasteners=fasteners,
        mounting_holes=holes,
        bolt_under_head_length_m=0.016,
        bolt_end_product_z_m=base_top + 0.010 + 0.0008 - 0.016,
        mounting_interface="Foot rests on F01 upper face; M4x16 into simplified female-thread envelopes",
        mounting_scope="Provisional tapped geometry; female thread flanks, material and load rating unselected",
    )


def _curved_pad(name, bend, distance, sign, center, frame_rotation, parent):
    """Reuse cable material sections for a curved half collar [m]."""
    angles = np.linspace(math.pi / 2, 3 * math.pi / 2, 37) + (math.pi if sign == 1 else 0.0)
    vertices = []
    for arc in np.linspace(distance - 0.007, distance + 0.007, 9):
        point, tangent = _arc_point(bend.final_points, arc)
        radial = np.cross([0.0, 0.0, 1.0], tangent)
        radial /= np.linalg.norm(radial)
        raised = np.cross(tangent, radial)
        for radius in (0.0071, 0.0095):
            points = point + radius * (np.cos(angles)[:, None] * radial + np.sin(angles)[:, None] * raised)
            vertices.extend(((points - center) @ frame_rotation).tolist())
    faces = []
    width = len(angles)
    stride = 2 * width
    for layer in range(8):
        a, b = layer * stride, (layer + 1) * stride
        for i in range(width - 1):
            faces.extend(
                (
                    (a + i, b + i, b + i + 1, a + i + 1),
                    (a + width + i, a + width + i + 1, b + width + i + 1, b + width + i),
                )
            )
        for i in (0, width - 1):
            faces.append((a + i, a + width + i, b + width + i, b + i))
    for layer in (0, 8):
        a = layer * stride
        for i in range(width - 1):
            faces.append((a + i, a + i + 1, a + width + i + 1, a + width + i))
    return mesh_object(name, vertices, faces, materials()["black"], parent)


def build_wire_supply(
    cell_root: bpy.types.Object,
    *,
    counts: tuple[int, int] = (5, 5),
    prefix: str = "OP030B_wire_supply",
    source_fixed: str = "OP030_supply_fixed",
    source_drawer: str = "OP030_supply_kit",
    connection_mode: ConnectionMode = "rear_entry",
) -> dict:
    """Build a ten-lane straight-wire pallet and retained sliding mechanism [m].

    Args:
        cell_root: Rigid station root, normally OP030B_cell with Y offset 2.30 m.
        counts: H03-1 and H03-2 inventory counts; ten total.
        prefix: Unique object prefix for this supply device.
        source_fixed: Existing fixed OP030 guide/cylinder prototype object.
        source_drawer: Existing moving bars/piston/clevis prototype object.
        connection_mode: Use matching wire lengths and end fittings for the work station.

    Returns:
        ``fixed``, ``drawer`` and ``pallet`` object references, straight wire
        ``rows`` in the stock cell frame, and serializable ``metadata``. Wire
        meshes are created by the motion integration, never duplicated here.
    """
    if sum(counts) != 10:
        raise ValueError("The specified pallet provides exactly ten lanes")
    if bpy.data.objects.get(prefix + "_fixed"):
        raise ValueError("Wire supply already exists")
    fixed_source = bpy.data.objects[source_fixed]
    drawer_source = bpy.data.objects[source_drawer]
    originals = descendants(fixed_source) + descendants(drawer_source)
    copies = duplicate_set(originals, prefix, cell_root)
    fixed, drawer = copies[source_fixed], copies[source_drawer]
    fixed.name = prefix + "_fixed"
    drawer.name = prefix + "_drawer"
    # Copy the source mechanism at zero extension even if the caller has
    # already moved the A drawer while assembling a candidate sequence.
    drawer.location.x = 0.0
    removed = []
    for obj in list(drawer.children):
        original = obj.get("split_source_name", "")
        if original.startswith(("OP030A_support_pallet20", "OP030_supply_T", "OP030_supply_H")):
            removed.extend(_discard_tree(obj))
    carrier = copies["OP030_supply_kit_plate"]
    # Existing channels are 750 mm apart: retain an 800-mm under-carriage,
    # while the removable wire pallet itself is exactly 650 by 700 mm.
    bpy.context.view_layer.update()
    carrier.scale.x *= PALLET_DIMENSIONS[0] / carrier.dimensions.x
    carrier["role"] = "Wide guide carrier below removable 650 x 700 mm wire pallet"
    mats = materials()
    # A reused upper stocker frame would pierce this wider pallet. Build the
    # support below the mechanism, leaving the full pick volume open above it.
    for x in (-2.22, -1.94):
        for y in (-2.12, -1.28):
            box(prefix + f"_leg_{x}_{y}", (0.040, 0.040, 0.766), (x, y, 0.397), mats["metal"], fixed)
            box(prefix + f"_foot_{x}_{y}", (0.085, 0.085, 0.014), (x, y, 0.007), mats["black"], fixed)
    for x in (-2.22, -1.94):
        box(prefix + f"_lower_long_rail_{x}", (0.040, 0.880, 0.040), (x, -1.70, 0.130), mats["metal"], fixed)
    for y in (-2.12, -1.28):
        box(prefix + f"_lower_cross_rail_{y}", (0.320, 0.040, 0.040), (-2.08, y, 0.130), mats["metal"], fixed)
    pallet = empty(prefix + "_pallet10", drawer)
    box(pallet.name + "_deck", PALLET_DIMENSIONS, (-2.02, -1.70, PALLET_TOP - 0.005), mats["white"], pallet)
    pallet["capacity"] = 10
    pallet["lane_pitch_m"] = 0.065
    pallet["ownership"] = "Reusable supply pallet; the arms lift cables only"
    rows = supply_layout(counts, 0.065, STOCK_CENTER, connection_mode=connection_mode)
    saddle_records = []
    for row in rows:
        shape = row["shape"]
        length = float(np.linalg.norm(np.diff(shape.centerline, axis=0), axis=1).sum())
        for index, distance in enumerate((0.075, length - 0.075)):
            point, tangent = _arc_point(shape.centerline, distance)
            name = prefix + f"_row{row['row']:02d}_saddle{index}"
            # Open upper half permits an actual vertical removal path. The
            # finger contact is 30 mm from the cable end, 45 mm from this seat.
            saddle = ring(name, 0.0070, 0.0102, 0.018, point, mats["black"], pallet, opening_half_angle=math.pi / 2)
            up = np.array([0.0, 0.0, 1.0])
            side = np.cross(tangent, up)
            side /= np.linalg.norm(side)
            saddle.rotation_mode = "QUATERNION"
            saddle.rotation_quaternion = Matrix(np.column_stack((up, side, tangent)).tolist()).to_quaternion()
            # Join the molded lower wall over 1.7 mm without entering the
            # 7-mm inner cradle radius; a tangent-only joint would float apart.
            support_top = point[2] - 0.0085
            post_height = support_top - PALLET_TOP
            box(
                name + "_post",
                (0.018, 0.018, post_height),
                (point[0], point[1], PALLET_TOP + post_height / 2),
                mats["blue"],
                pallet,
            )
            saddle_records.append(
                dict(
                    uid=row["uid"],
                    row=row["row"],
                    name=saddle.name,
                    material_arclength_m=distance,
                    center_cell_m=point.tolist(),
                    closed_ring=False,
                    end_grasp_to_saddle_center_m=0.045,
                )
            )
    metadata = dict(
        fixed=fixed.name,
        drawer=drawer.name,
        pallet=pallet.name,
        stock_center_cell_m=list(STOCK_CENTER),
        active_center_cell_m=list(ACTIVE_CENTER),
        pallet_dimensions_m=list(PALLET_DIMENSIONS),
        carrier_dimensions_m=[0.650, 0.800, 0.010],
        drawer_axis=[1.0, 0.0, 0.0],
        extension_limits_m=[0.0, DRAWER_STROKE],
        counts=list(counts),
        lanes=10,
        lane_pitch_m=0.065,
        wire_axis_height_m=1.04,
        pallet_top_height_m=PALLET_TOP,
        cable_axis_to_deck_m=1.04 - PALLET_TOP,
        bent_lug_bottom_to_deck_m=1.04 - 0.030 - PALLET_TOP,
        saddles=saddle_records,
        removed_copied_old_nests=removed,
        source_reuse="Delivered OP030 guide channels, moving bars, hollow cylinder, piston, rod and clevis",
        scope="Candidate geometry; continuous robot/drawer collision, mass, cylinder force and rigidity unverified",
        formal_physical_validity_verdict=None,
    )
    if connection_mode == "top_entry":
        bounds = [
            WireBend(row["number"], connection_mode=connection_mode).assembly_bounds(row["shape"]) for row in rows
        ]
        metadata["connection_mode"] = connection_mode
        metadata["minimum_assembly_bottom_to_deck_m"] = min(float(bound[0, 2] - PALLET_TOP) for bound in bounds)
        metadata.pop("bent_lug_bottom_to_deck_m")
    drawer["motion_axis"] = "local X, zero to 0.340 m; stationary inventory follows this drawer"
    fixed["supply_geometry_metadata"] = json.dumps(metadata, ensure_ascii=False)
    bpy.context.view_layer.update()
    return dict(fixed=fixed, drawer=drawer, pallet=pallet, rows=rows, metadata=metadata)


def set_drawer_extension(supply: dict, distance: float) -> None:
    """Set the retained drawer extension [m], including its piston and pallet."""
    if not 0.0 <= distance <= DRAWER_STROKE:
        raise ValueError("Drawer command exceeds the 340-mm candidate stroke")
    supply["drawer"].location.x = distance


def build_transport_clips(
    pallet: bpy.types.Object,
    product: bpy.types.Object,
    *,
    prefix: str = "OP030_transport",
    open_hinge_degrees: float = 160.0,
    connection_mode: ConnectionMode = "rear_entry",
) -> dict:
    """Add two provisional mechanical cable retaining clips to one pallet [m].

    Args:
        pallet: The single persistent transport pallet, normally source_0292.
        product: The same junction-box product used for the wire local frame.
        prefix: Unique mechanism prefix.
        open_hinge_degrees: Candidate opening angle [deg] for a finite sweep check.
        connection_mode: Select the wire route and matching provisional pallet mount.

    Returns:
        Fixed pallet root, per-wire swing arms and two sliding pad references,
        plus serializable frame/contact metadata. The parent planner operates
        these joints and checks each transition; no force law is provided.
    """
    bpy.context.view_layer.update()
    carrier = empty(prefix + "_pallet_mount", pallet)
    relative = pallet.matrix_world.inverted() @ product.matrix_world
    carrier.matrix_parent_inverse = Matrix.Identity(4)
    carrier.matrix_basis = relative
    mats = materials()
    # Source pallet top plate, excluding the higher locators and side handles.
    plate = next((obj for obj in descendants(pallet) if "_m0028_p00" in obj.name), None)
    if plate is None:
        raise ValueError("The retained transport pallet top plate was not found")
    inverse = product.matrix_world.inverted()
    plate_top = max((inverse @ plate.matrix_world @ Vector(p)).z for p in plate.bound_box)
    clip_objects, records = {}, []
    fractions = {1: 0.65, 2: 0.42}
    for number, fraction in fractions.items():
        bend = WireBend(number, connection_mode=connection_mode)
        distance, mapping = _clip_distance(bend, fraction)
        fraction = distance / bend.length
        point, tangent = _arc_point(bend.final_points, distance)
        name = prefix + f"_H{number}"
        # The product-local negative-X pallet edge is opposite the robot bank
        # because the continued product frame rotates XY by 180 degrees.
        pivot = np.array([-0.302, point[1], 0.090])
        fixed = empty(name + "_fixed", carrier)
        post_bottom, mounting = _mount_foot(name, pivot, plate_top, fixed, product, connection_mode)
        box(
            name + "_post",
            (0.014, 0.014, pivot[2] - post_bottom),
            (pivot[0], pivot[1], (pivot[2] + post_bottom) / 2),
            mats["metal"],
            fixed,
        )
        for sign in (-1, 1):
            box(
                name + f"_hinge_ear{sign}",
                (0.025, 0.006, 0.025),
                (pivot[0], pivot[1] + sign * 0.013, pivot[2]),
                mats["metal"],
                fixed,
            )
        cylinder(name + "_hinge_pin", 0.004, 0.034, pivot, mats["metal"], fixed, rotation=(math.pi / 2, 0, 0))
        swing = empty(name + "_swing", fixed)
        swing.location = pivot
        reach = point[0] - pivot[0]
        box(name + "_swing_beam", (reach, 0.010, 0.010), (reach / 2, 0, 0), mats["blue"], swing)
        # A roller is a mechanical actuation interface for a station cam or
        # manual lever. Its driving cam, spring torque and forces are unselected.
        cylinder(
            name + "_follower", 0.009, 0.010, (0.040, -0.015, 0), mats["black"], swing, rotation=(math.pi / 2, 0, 0)
        )
        cylinder(
            name + "_follower_axle",
            0.0025,
            0.020,
            (0.040, -0.008, 0),
            mats["metal"],
            swing,
            rotation=(math.pi / 2, 0, 0),
        )
        spring_y = 0.019 if number == 1 else -0.019
        spring = ring(name + "_hinge_spring_envelope", 0.0044, 0.0070, 0.010, (0, spring_y, 0), mats["black"], swing)
        spring.rotation_euler.x = math.pi / 2
        head = empty(name + "_head", swing)
        up = np.array([0.0, 0.0, 1.0])
        radial = np.cross(up, tangent)
        radial /= np.linalg.norm(radial)
        raised = np.cross(tangent, radial)
        rotation = np.column_stack((radial, raised, tangent))
        frame = np.eye(4)
        frame[:3, :3], frame[:3, 3] = rotation, point - pivot
        head.matrix_basis = Matrix(frame.tolist())
        head_top = point[2] + 0.028
        box(
            name + "_head_drop",
            (0.010, 0.010, pivot[2] - head_top),
            (reach, 0, (head_top - pivot[2]) / 2),
            mats["blue"],
            swing,
        )
        box(name + "_head_bridge", (0.066, 0.008, 0.016), (0, 0.028, 0), mats["blue"], head)
        pads = []
        for sign in (-1, 1):
            slide = empty(name + f"_pad_slide{sign}", head)
            # Two true half-collars close around insulation with a 0.1-mm
            # radial geometric clearance; this is not a measured clamp load.
            _curved_pad(name + f"_pad{sign}", bend, distance, sign, point, rotation, slide)
            box(name + f"_pad_stem{sign}", (0.018, 0.005, 0.012), (sign * 0.017, 0, 0), mats["blue"], slide)
            box(name + f"_guide{sign}", (0.009, 0.028, 0.016), (sign * 0.0275, 0.014, 0), mats["metal"], head)
            cylinder(
                name + f"_guide_pin{sign}",
                0.0025,
                0.024,
                (sign * 0.025, 0, 0),
                mats["metal"],
                slide,
                rotation=(0, math.pi / 2, 0),
            )
            # Thin leaf is a visible mechanical bias element, without imposing
            # a material stiffness or treating the envelope as simulated force.
            box(name + f"_leaf_spring{sign}", (0.0006, 0.026, 0.010), (sign * 0.032, 0.013, 0), mats["metal"], head, 0)
            pads.append(slide)
        clip_objects[number] = dict(fixed=fixed, swing=swing, head=head, pads=pads)
        records.append(
            dict(
                number=number,
                fixed=fixed.name,
                swing=swing.name,
                head=head.name,
                pads=[obj.name for obj in pads],
                material_fraction=fraction,
                material_arclength_m=distance,
                wire_length_m=bend.length,
                center_product_m=point.tolist(),
                tangent_product=tangent.tolist(),
                pivot_product_m=pivot.tolist(),
                closed_hinge_y_rad=0.0,
                open_hinge_y_rad=-math.radians(open_hinge_degrees),
                open_pad_radial_spread_m=0.011,
                closed_pad_radial_spread_m=0.0,
                pad_inner_diameter_m=0.0142,
                pad_axial_width_m=0.014,
                closest_end_grasp_arclength_separation_m=min(distance - 0.030, bend.length - 0.030 - distance),
                **mapping,
                **mounting,
            )
        )
    metadata = dict(
        carrier=carrier.name,
        parent_pallet=pallet.name,
        product_frame_reference=product.name,
        carrier_relative_to_pallet=[list(row) for row in relative],
        work_reference="product_frame(lift=0.350); use the same product-to-pallet transform at every station",
        native_product_world_at_build=[list(row) for row in product.matrix_world],
        native_pallet_world_at_build=[list(row) for row in pallet.matrix_world],
        pallet_top_in_product_frame_m=plate_top,
        clips=records,
        ownership="Transport-pallet tooling; not a vehicle component",
        sequence=(
            "Right releases and retreats; left holds while clip closes, then releases. Open after ST C tightening."
        ),
        mechanical_interface=(
            "Swing, follower and leaf-biased sliding pads; station cam/lever and spring sizing unselected"
        ),
        reuse="Retained support-tray pad/guide primitive convention and existing ring/hinge construction helpers",
        scope=("Provisional geometry; linkage, clamp force, sweep and robot/tool clearance require integration checks"),
        formal_physical_validity_verdict=None,
    )
    if connection_mode == "top_entry":
        metadata["connection_mode"] = connection_mode
    carrier["temporary_retention_metadata"] = json.dumps(metadata, ensure_ascii=False)
    result = dict(carrier=carrier, clips=clip_objects, metadata=metadata)
    for number in (1, 2):
        set_transport_clip(result, number, hinge_closed=0.0, pads_closed=0.0)
    bpy.context.view_layer.update()
    return result


def set_transport_clip(retention: dict, number: int, *, hinge_closed: float, pads_closed: float) -> None:
    """Set candidate mechanical hinge/pad closure fractions in [0, 1].

    The swing closes before the pads; the parent sequence must hold the cable
    with the left gripper until both commanded geometric joints have closed.
    """
    if not 0.0 <= hinge_closed <= 1.0 or not 0.0 <= pads_closed <= 1.0:
        raise ValueError("Clip closure fractions must lie in [0, 1]")
    clip = retention["clips"][number]
    record = next(row for row in retention["metadata"]["clips"] if row["number"] == number)
    clip["swing"].rotation_euler.y = record["open_hinge_y_rad"] * (1 - hinge_closed)
    for sign, pad in zip((-1, 1), clip["pads"], strict=True):
        pad.location.x = sign * 0.011 * (1 - pads_closed)


def main() -> None:
    """Create a separate supply geometry probe from the accepted split layout."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(ROOT / "analysis/split_layout_v03.blend"))
    parser.add_argument("--output", default=str(ROOT / "analysis/split_layout_transport_probe.blend"))
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=args.source)
    supply = build_wire_supply(bpy.data.objects["OP030B_cell"])
    bpy.ops.wm.save_as_mainfile(filepath=args.output, compress=True)
    (ROOT / "audit/op030_split_layout_transport.json").write_text(
        json.dumps(supply["metadata"], ensure_ascii=False, indent=2) + "\n"
    )
    print("OP030B_STRAIGHT_SUPPLY_BUILT", 10, 20, flush=True)


if __name__ == "__main__":
    main()
