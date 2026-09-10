# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Split OP030 hardware into three translated stations and a 20-place pallet.

This module reuses the delivered native geometry. It does not validate robot
motion, contact forces, or a released production layout. Distances are [m].
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from allocation_product import empty
from op020_jb_geometry import box, materials

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "UR15_JB_OP030_v02.blend"
SOURCE_SHA256 = "9ba3a948e23f7db1b026a8db4a347c98cf83c4ea9a27019d58004cd92c641c6b"
PITCH = 2.3
CUT_Y = -1.125
EXTENSION = 2 * PITCH
CELL_OFFSETS = {"OP030A": 0.0, "OP030B": PITCH, "OP030C": 2 * PITCH}


def digest(path: Path) -> str:
    """Return the SHA-256 digest of an existing file."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def descendants(root: bpy.types.Object) -> list[bpy.types.Object]:
    """Return the root and every descendant once."""
    result = [root]
    for child in root.children:
        result.extend(descendants(child))
    return result


def remove_tree(root: bpy.types.Object, removed: list[str]) -> None:
    """Remove an explicitly superseded equipment subtree."""
    for obj in reversed(descendants(root)):
        removed.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)


def freeze_frame(frame: int = 1) -> None:
    """Keep the evaluated frame while clearing the previous replay actions."""
    scene = bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    for obj in list(scene.objects):
        basis = obj.matrix_basis.copy()
        # Keep lift mechanism drivers; they remain bound to their carriage.
        if obj.animation_data:
            obj.animation_data.action = None
        obj.matrix_basis = basis
        if obj.type in {"MESH", "CURVE"} and obj.data.shape_keys:
            values = [key.value for key in obj.data.shape_keys.key_blocks]
            obj.data.shape_keys.animation_data_clear()
            for key, value in zip(obj.data.shape_keys.key_blocks, values, strict=True):
                key.value = value
    scene.frame_start = scene.frame_end = 1


def attach_world(obj: bpy.types.Object, parent: bpy.types.Object) -> None:
    """Attach an object while preserving its world pose [m, rad]."""
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_basis = parent.matrix_world.inverted() @ world


def duplicate_set(
    objects: list[bpy.types.Object], prefix: str, parent: bpy.types.Object
) -> dict[str, bpy.types.Object]:
    """Copy hardware with remapped parenting and driver object references."""
    copies = {}
    for source in objects:
        obj = source.copy()
        # Mesh vertices/materials can remain shared: only rigid poses change.
        # Camera/light data are copied so later per-cell configuration is local.
        if source.type in {"CAMERA", "LIGHT"}:
            obj.data = source.data.copy()
        obj.name = prefix + "__" + source.name
        obj["split_source_name"] = source.name
        obj["split_station"] = prefix
        bpy.context.scene.collection.objects.link(obj)
        copies[source.name] = obj
    for source in objects:
        obj = copies[source.name]
        if source.parent and source.parent.name in copies:
            obj.parent = copies[source.parent.name]
            obj.matrix_parent_inverse = source.matrix_parent_inverse.copy()
            obj.matrix_basis = source.matrix_basis.copy()
        else:
            obj.parent = parent
            obj.matrix_parent_inverse = Matrix.Identity(4)
            # The new cell parent's translation supplies the station offset.
            obj.matrix_basis = source.matrix_world.copy()
        if obj.animation_data:
            for curve in obj.animation_data.drivers:
                for variable in curve.driver.variables:
                    for target in variable.targets:
                        if target.id and target.id.name in copies:
                            target.id = copies[target.id.name]
    return copies


def mesh_components(mesh: bpy.types.Mesh) -> list[np.ndarray]:
    """Return connected vertex sets without joining independent rollers."""
    count = len(mesh.vertices)
    parent = np.arange(count)

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    edges = np.empty(len(mesh.edges) * 2, dtype=np.int32)
    mesh.edges.foreach_get("vertices", edges)
    for a, b in edges.reshape(-1, 2):
        left, right = find(a), find(b)
        if left != right:
            parent[right] = left
    groups = {}
    for index in range(count):
        groups.setdefault(find(index), []).append(index)
    return [np.asarray(values, dtype=int) for values in groups.values()]


def extend_mesh(
    obj: bpy.types.Object,
    *,
    repeat: bool,
    stretch_long: bool,
    report: dict,
    repeat_max_extent: float = PITCH - 0.05,
) -> None:
    """Insert two bays into architectural meshes in world Y [m].

    Connected hardware components move rigidly. Only long continuous rails,
    floor slabs and service beams crossing the cut are lengthened. Repeated
    rollers and facade posts are copied from the preceding 2.3-m bay.
    """
    if not obj.data.vertices:
        return
    obj.data = obj.data.copy()
    local = np.empty(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", local)
    local = local.reshape(-1, 3)
    world_matrix = np.asarray(obj.matrix_world)
    world = local @ world_matrix[:3, :3].T + world_matrix[:3, 3]
    original = world.copy()
    extra_groups = []
    rigid_count = stretch_count = 0
    for indices in mesh_components(obj.data):
        values = original[indices, 1]
        low, high = float(values.min()), float(values.max())
        center = (low + high) / 2
        if stretch_long and low < CUT_Y < high and high - low > 0.9:
            world[indices, 1] += (values > CUT_Y) * EXTENSION
            stretch_count += 1
        elif center > CUT_Y:
            world[indices, 1] += EXTENSION
            rigid_count += 1
        if repeat and CUT_Y - PITCH < center <= CUT_Y and high - low < repeat_max_extent:
            extra_groups.append(indices)
    inverse = np.linalg.inv(world_matrix)
    updated = world @ inverse[:3, :3].T + inverse[:3, 3]
    obj.data.vertices.foreach_set("co", updated.ravel())
    obj.data.update()
    if extra_groups:
        selected = set(np.concatenate(extra_groups).tolist())
        index_map = {old: index for index, old in enumerate(sorted(selected))}
        source_faces = [
            polygon for polygon in obj.data.polygons if all(index in selected for index in polygon.vertices)
        ]
        faces = [[index_map[index] for index in polygon.vertices] for polygon in source_faces]
        verts = original[sorted(selected)]
        for bay in (1, 2):
            points = verts + np.array([0.0, bay * PITCH, 0.0])
            mesh = bpy.data.meshes.new(f"Split_bay_{bay}__{obj.name}")
            mesh.from_pydata(points.tolist(), [], faces)
            for material in obj.data.materials:
                mesh.materials.append(material)
            for target, source_face in zip(mesh.polygons, source_faces, strict=True):
                target.material_index = source_face.material_index
                target.use_smooth = source_face.use_smooth
            copied = bpy.data.objects.new(mesh.name, mesh)
            bpy.context.scene.collection.objects.link(copied)
            copied["split_source_name"] = obj.name
            copied["infrastructure_repeat_offset_y_m"] = bay * PITCH
            report["infrastructure_added"].append(copied.name)
    if rigid_count or stretch_count or extra_groups:
        report["infrastructure_edits"].append(
            dict(
                name=obj.name,
                translated_components=rigid_count,
                stretched_components=stretch_count,
                repeated_components=len(extra_groups),
            )
        )


def extend_line(protected: set[str], report: dict) -> None:
    """Translate later stations intact and extend surrounding infrastructure [m]."""
    scene = bpy.context.scene
    roots = [obj for obj in scene.objects if obj.parent is None]
    for root in roots:
        if root.name in protected:
            continue
        equipment = root.get("equipment_id", "")
        match = re.search(r"(?:OP(\d{3})|(?:assembly_cell|stocker|station_hardware|operator_panel)_(\d{2}))", equipment)
        if match:
            station = int(match.group(1)) // 10 if match.group(1) else int(match.group(2))
            if station >= 4:
                root.location.y += EXTENSION
                report["later_station_roots_translated"].append(root.name)
            continue
        if root.type in {"LIGHT", "CAMERA"}:
            if root.location.y > CUT_Y:
                root.location.y += EXTENSION
            if root.type == "LIGHT" and CUT_Y - PITCH < root.location.y <= CUT_Y:
                for bay in (1, 2):
                    obj = root.copy()
                    obj.data = root.data.copy()
                    obj.name = f"Split_bay_{bay}__" + root.name
                    scene.collection.objects.link(obj)
                    obj.location.y += PITCH * bay
                    report["infrastructure_added"].append(obj.name)
            continue
        rows = descendants(root)
        meshes = [obj for obj in rows if obj.type == "MESH"]
        # Main building/conveyor/enclosure meshes contain disconnected objects
        # in world coordinates. Treat components individually, not their root.
        node = int(root.get("source_node_id", -1))
        architectural = (
            0 <= node <= 27
            or equipment in {"line_services_01", "ceiling_01", "line_lighting_01"}
            or root.name == "Transparent_line_enclosure"
        )
        if architectural:
            for obj in meshes:
                repeat = (
                    2 <= node <= 27
                    or equipment in {"line_services_01", "ceiling_01", "line_lighting_01"}
                    or root.name == "Transparent_line_enclosure"
                )
                extend_mesh(
                    obj,
                    repeat=repeat,
                    stretch_long=equipment != "line_lighting_01",
                    repeat_max_extent=3.0 if equipment == "line_lighting_01" else PITCH - 0.05,
                    report=report,
                )
            continue
        if meshes:
            bounds = [obj.matrix_world @ Vector(point) for obj in meshes for point in obj.bound_box]
            center = (min(point.y for point in bounds) + max(point.y for point in bounds)) / 2
            if center > CUT_Y:
                root.location.y += EXTENSION
                report["other_roots_translated"].append(root.name)
    bpy.context.view_layer.update()


def support_grid(cell_root: bpy.types.Object) -> dict:
    """Place 20 retained-shape supports on a 5-by-4 removable pallet [m]."""
    kit = bpy.data.objects["OP030_supply_kit"]
    removed = []
    for child in list(kit.children):
        if child.name.startswith(("OP030_supply_T", "OP030_supply_H")):
            remove_tree(child, removed)
    deck = bpy.data.objects["OP030_supply_kit_plate"]
    deck.scale.x *= 0.520 / 0.460
    pallet = empty("OP030A_support_pallet20", kit)
    mats = materials()
    box(pallet.name + "_deck", (0.500, 0.650, 0.008), (-2.02, -1.70, 0.9425), mats["white"], pallet)
    pallet["capacity"] = 20
    pallet["columns"] = 5
    pallet["rows"] = 4
    pallet["pitch_m"] = 0.120
    pallet["supply_scope"] = "20 occupied slots; pallet replenishment is not animated by this layout module"
    source_parts = {number: bpy.data.objects[f"OP030_T{number:02d}_UID001"] for number in (1, 2)}
    # First two picks retain the original identities and nearly the original
    # validated extended pick positions. The new reach must still be checked.
    identities = {5: (1, source_parts[1]), 6: (2, source_parts[2])}
    remaining = [index for index in range(20) if index not in identities]
    for index, slot in enumerate(remaining):
        number = index % 2 + 1
        serial = index // 2 + 2
        name = f"OP030A_T{number:02d}_UID{serial:03d}"
        copies = duplicate_set(descendants(source_parts[number]), name, cell_root)
        root = copies[source_parts[number].name]
        root.name = name
        root["part_uid"] = name
        identities[slot] = (number, root)
    records = []
    for index in range(20):
        row, column = divmod(index, 5)
        number, obj = identities[index]
        position = [-2.20 + row * 0.120, -1.94 + column * 0.120, 1.0]
        # All pallets and parts use the same fixed source frame before sliding.
        obj.parent = cell_root
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_basis = Matrix.Translation(position)
        obj["supply_slot"] = index
        obj["supply_pallet"] = pallet.name
        nest_height = 0.994 - 0.9465
        box(
            pallet.name + f"_nest_{index:02d}",
            (0.044, 0.050, nest_height),
            (position[0], position[1], 0.9465 + nest_height / 2),
            mats["black"],
            pallet,
        )
        records.append(
            dict(
                slot=index,
                row=row,
                column=column,
                part_number=number,
                uid=obj.name,
                stock_cell_m=position,
                extended_cell_m=[position[0] + 0.340, position[1], position[2]],
            )
        )
    kit["capacity_this_review"] = "20 support parts in a 5-by-4 removable supply pallet"
    return dict(
        pallet=pallet.name,
        drawer=kit.name,
        count=20,
        columns=5,
        rows=4,
        pitch_m=[0.120, 0.120],
        pallet_dimensions_m=[0.500, 0.650, 0.008],
        retained_slide_stroke_m=0.340,
        records=records,
        removed_old_nests=removed,
        first_cycle_uids=[source_parts[1].name, source_parts[2].name],
        reach_validation="not performed by layout module",
    )


def build_layout(output_path: Path | None = None) -> dict:
    """Create three independent cells using rigid translations [m].

    Args:
        output_path: Optional native output file for a static layout candidate.

    Returns:
        Layout record with cell source-name maps and persistent product IDs.
    """
    assert digest(SOURCE) == SOURCE_SHA256, "Latest OP030 source digest changed"
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    freeze_frame(1)
    scene = bpy.context.scene
    report = dict(
        observed_at=datetime.now(timezone(timedelta(hours=9))).isoformat(),
        evidence_basis="Native delivered OP030 v02 readback and static layout generation",
        source=str(SOURCE),
        source_sha256=SOURCE_SHA256,
        station_pitch_m=PITCH,
        later_station_translation_y_m=EXTENSION,
        later_station_roots_translated=[],
        other_roots_translated=[],
        infrastructure_edits=[],
        infrastructure_added=[],
        removed_legacy=[],
        cells={},
        formal_physical_validity_verdict=None,
    )
    equipment = {"assembly_cell_03", "station_hardware_03", "robot_OP030_left", "robot_OP030_right"}
    original_roots = [obj for obj in scene.objects if obj.parent is None and obj.get("equipment_id") in equipment]
    original_roots += [
        bpy.data.objects[name] for name in ("OP030_lift_fixed", "OP030_lift_carriage", "OP030_air_service_connections")
    ]
    original_objects = list(dict.fromkeys(obj for root in original_roots for obj in descendants(root)))
    # B/C receive no obsolete combined parts tray, handheld drivers or tool dock.
    # A retains only the guide mechanism to carry its new 20-place support pallet.
    protected = {root.name for root in original_roots}
    protected.update(obj.name for obj in scene.objects if obj.parent is None and obj.name.startswith("OP030"))
    protected.update({"source_0587", "source_0292", "JB_OP020_UID001"})
    protected.update(obj.name for obj in scene.objects if obj.name.startswith("Review_OP030"))
    extend_line(protected, report)
    cell_roots = {}
    for prefix, offset in CELL_OFFSETS.items():
        root = empty(prefix + "_cell")
        root.location.y = offset
        root["role"] = {
            "OP030A": "support placement and M4 fastening",
            "OP030B": "wire placement and bimanual bending",
            "OP030C": "M6/M14 terminal fastening",
        }[prefix]
        root["source_station_offset_y_m"] = offset
        cell_roots[prefix] = root
        if prefix == "OP030A":
            mapping = {obj.name: obj for obj in original_objects}
            for obj in original_roots:
                attach_world(obj, root)
        else:
            mapping = duplicate_set(original_objects, prefix, root)
        report["cells"][prefix] = dict(
            root=root.name,
            offset_y_m=offset,
            robot_base_m=[-0.9, -1.7 + offset, 0.0],
            pallet_work_center_m=[0.0, -1.7 + offset, 0.8845],
            source_names={name: obj.name for name, obj in mapping.items()},
            lift_carriage=mapping["OP030_lift_carriage"].name,
            source_robot_node_ids=list(range(1046, 1126)),
        )
    for name in ("source_0587", "OP030_supply_fixed", "OP030_supply_kit"):
        attach_world(bpy.data.objects[name], cell_roots["OP030A"])
    report["support_supply"] = support_grid(cell_roots["OP030A"])
    for name in ("OP030_tool_dock", "OP030_driver_M4", "OP030_driver_M6", "OP030_driver_M14", "OP030_fastener_supply"):
        obj = bpy.data.objects.get(name)
        if obj:
            remove_tree(obj, report["removed_legacy"])
    # Old coiled/prebent supply wire actors are retained as hidden references
    # until the straight-supply builder replaces their geometry/animation.
    for number in (1, 2):
        for name in (f"OP030_H03_{number}_UID001", f"OP030_H03_{number}_UID001_T"):
            for obj in descendants(bpy.data.objects[name]):
                obj.hide_render = True
                obj.hide_viewport = True
                obj["superseded_by_straight_supply"] = True
    report["persistent_assembly"] = dict(
        product="JB_OP020_UID001",
        pallet="source_0292",
        external_harness="OP020_harness_UID001",
        duplication_count=0,
        transport_rule="Move these identities along Y; attach added support/wire/nut identities after seating",
    )
    report["scope"] = (
        "Static three-ST layout and support inventory only; tools, wire supply and motion integrated separately"
    )
    scene["split_layout_manifest"] = json.dumps(report["cells"], ensure_ascii=False)
    scene["split_support_supply_manifest"] = json.dumps(report["support_supply"], ensure_ascii=False)
    scene["physical_validity_verdict"] = "not performed; static geometry candidate only"
    assert not any(obj.name.startswith("Enclosure_clear_") for obj in scene.objects)
    assert len(report["support_supply"]["records"]) == 20
    bpy.context.view_layer.update()
    if output_path:
        bpy.ops.wm.save_as_mainfile(filepath=str(output_path), compress=True)
        report.update(output=str(output_path), output_sha256=digest(output_path))
    target = ROOT / "audit/op030_split_layout_v03.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("OP030_SPLIT_LAYOUT_CREATED", len(report["cells"]), 20, flush=True)
    return report


def main() -> None:
    """Build a separate static layout file; never overwrite the delivered v02."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "analysis/split_layout_v03.blend"))
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    output = Path(args.output).resolve()
    assert output != SOURCE
    build_layout(output)


if __name__ == "__main__":
    main()
