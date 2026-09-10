# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Apply the authorized constant-height conveyor delta to pinned v03 geometry [m]."""

import argparse
import copy
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from op030_split_layout import attach_world, descendants, digest

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "analysis/op030_split_top_entry_clip_static_v03.blend"
SOURCE_SHA256 = "22987fb3cbbf69fc954466f7d282703f192a0117bbba37d288f63c5f66c66f73"
SOURCE_MANIFEST = ROOT / "audit/op030_split_static_v03.json"
CONVEYOR_RISE = 0.364
PALLET_Z = 0.789
PRODUCT_Z = 0.8845
ROLLER_Z = 0.7565


def _world_vertices(obj):
    local = np.empty(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", local)
    matrix = np.asarray(obj.matrix_world)
    return local.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]


def _bounds(obj):
    points = [_world_vertices(child) for child in descendants(obj) if child.type == "MESH"]
    values = np.concatenate(points) if points else np.zeros((1, 3))
    return [values.min(0).tolist(), values.max(0).tolist()]


def _write_world_vertices(obj, vertices):
    matrix = np.linalg.inv(np.asarray(obj.matrix_world))
    local = vertices @ matrix[:3, :3].T + matrix[:3, 3]
    obj.data = obj.data.copy()
    obj.data.vertices.foreach_set("co", local.ravel())
    obj.data.update()


def _welded_components(mesh):
    """Find disconnected CAD solids without modifying the imported triangle soup."""
    vertices = np.asarray([vertex.co[:] for vertex in mesh.vertices])
    _, inverse = np.unique(np.round(vertices, 6), axis=0, return_inverse=True)
    parents = np.arange(int(inverse.max()) + 1)

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for polygon in mesh.polygons:
        first = find(inverse[polygon.vertices[0]])
        for vertex in polygon.vertices[1:]:
            other = find(inverse[vertex])
            if other != first:
                parents[other] = first
    labels = np.asarray([find(index) for index in inverse])
    return [np.flatnonzero(labels == label) for label in np.unique(labels)]


def _raise_floor_frame(root, rise, report, *, floor_part_ceiling=0.070):
    """Lengthen existing upright extrusions while retaining each levelling foot [m]."""
    entries = []
    before = _bounds(root)
    for obj in descendants(root):
        if obj.type != "MESH":
            continue
        world = _world_vertices(obj)
        components = []
        for indices in _welded_components(obj.data):
            original = world[indices].copy()
            low, high = original.min(0), original.max(0)
            size = high - low
            if high[2] <= floor_part_ceiling + 1e-6:
                operation = "floor_hardware_unchanged"
            elif low[2] < 0.081 and size[2] > 1.8 * max(size[0], size[1]):
                # Extrusion length changes; cross sections and levelling foot
                # geometry are preserved. No scale is applied to whole stands.
                world[indices, 2] += rise * (original[:, 2] - low[2]) / size[2]
                operation = "upright_extended"
            else:
                world[indices, 2] += rise
                operation = "rigid_upper_component_raised"
            components.append(dict(operation=operation, before_bounds_m=[low.tolist(), high.tolist()]))
        _write_world_vertices(obj, world)
        entries.append(dict(mesh=obj.name, components=components))
    bpy.context.view_layer.update()
    after = _bounds(root)
    if abs(after[0][2] - before[0][2]) > 2e-6:
        raise RuntimeError(f"Floor contact moved: {root.name}")
    report.append(dict(root=root.name, rise_m=rise, before_bounds_m=before, after_bounds_m=after, meshes=entries))


def _raise_root(obj, rise, report, reason):
    old = np.asarray(obj.matrix_world).copy()
    obj.matrix_world = Matrix.Translation((0, 0, rise)) @ obj.matrix_world
    report.append(dict(root=obj.name, rise_m=rise, reason=reason, original_world=old.tolist()))


def _new_base(name, parent, fixed, carriage, offset_y):
    base = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(base)
    if parent:
        base.parent = parent
    # New base is placed at the old cell origin first. Keeping local z as
    # the driver input is essential: adding .364 to location[2] breaks the
    # retained linkage expressions.
    base.matrix_world = Matrix.Translation((0, offset_y, 0))
    bpy.context.view_layer.update()
    attach_world(fixed, base)
    attach_world(carriage, base)
    base.location.z += CONVEYOR_RISE
    carriage.location.z = -0.014
    bpy.context.view_layer.update()
    return dict(
        positioner_base=base.name,
        fixed=fixed.name,
        carriage=carriage.name,
        offset_y_m=offset_y,
        carriage_retracted_local_z_m=-0.051,
        carriage_engaged_local_z_m=-0.014,
        carriage_retracted_world_z_m=0.313,
        carriage_engaged_world_z_m=0.350,
        platen_retracted_world_z_m=0.705,
        platen_engaged_world_z_m=0.742,
        pin_stroke_m=0.037,
        pallet_constant_world_z_m=PALLET_Z,
        base_world=np.asarray(base.matrix_world).tolist(),
        initial_world=np.asarray(carriage.matrix_world).tolist(),
        driver_rule="Keep carriage parent; location[2] = -.051 + .037 * pin_extension_fraction",
        bake_rule="desired_world = T(0, offset_y, .364 + local_z); bake inverse(base_world) @ desired_world",
    )


def _remove_retention(manifest):
    names = [
        obj.name
        for obj in bpy.context.scene.objects
        if obj.name.startswith(("OP030_transport_H1", "OP030_transport_H2"))
    ]
    meshes = [name for name in names if bpy.data.objects[name].type == "MESH"]
    if len(meshes) != 54:
        raise RuntimeError(f"Expected exactly 54 retention meshes, got {len(meshes)}")
    for name in reversed(names):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
    retained = "JB_OP020_UID001_F01_removable_transport_carrier_side_base"
    if retained not in bpy.data.objects:
        raise RuntimeError("Persistent F01 side base missing")
    previous = manifest["retention"]
    manifest["retention"] = dict(
        removed_meshes=meshes,
        removed_objects=names,
        mechanical_mesh_count=42,
        permanent_M4_mesh_count=12,
        permanent_M4_count=4,
        retained_F01_side_base=retained,
        existing_mounting_holes_retained=True,
        carrier=previous["carrier"],
        parent_pallet=previous["parent_pallet"],
        connection_mode="top_entry",
        clips=[],
        sequence="Seat both wire ends on upward studs and seats, then release fingers; no retention closure/opening",
        hidden_replacement_constraints_added=False,
    )
    bpy.context.scene["split_transport_clips"] = json.dumps(manifest["retention"])
    bpy.data.objects[previous["carrier"]]["temporary_retention_metadata"] = json.dumps(manifest["retention"])


def _raise_conveyor_stands(report):
    for node in range(10, 26):
        _raise_floor_frame(bpy.data.objects[f"source_{node:04d}"], CONVEYOR_RISE, report)
    for bay in (1, 2):
        # The v03 inserted bay has four material objects but no assembly root.
        # Group all four before checking the assembly's floor-contact minimum.
        root = bpy.data.objects.new(f"Split_bay_{bay}_conveyor_stand_v04", None)
        bpy.context.scene.collection.objects.link(root)
        selected = [obj for obj in bpy.context.scene.objects if obj.name.startswith(f"Split_bay_{bay}__source_0019_")]
        for obj in selected:
            attach_world(obj, root)
        _raise_floor_frame(root, CONVEYOR_RISE, report)


def build_static(output: Path, manifest_output: Path) -> dict:
    """Build the separate constant-height candidate with pallet root at 0.789 [m]."""
    if output.resolve() == SOURCE.resolve() or "v04" not in output.stem:
        raise ValueError("A separate v04 output is required")
    if digest(SOURCE) != SOURCE_SHA256:
        raise RuntimeError("Pinned v03 source digest mismatch")
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    manifest = copy.deepcopy(json.loads(SOURCE_MANIFEST.read_text()))
    changed, floor_frames, positioners = [], [], {}
    original_count = sum(obj.type == "MESH" for obj in scene.objects)
    _remove_retention(manifest)

    for node in (*range(2, 8), 26, 27):
        _raise_root(bpy.data.objects[f"source_{node:04d}"], CONVEYOR_RISE, changed, "main conveyor and end housings")
    for obj in list(scene.objects):
        if re.fullmatch(r"Split_bay_[12]__source_0004_.*", obj.name):
            _raise_root(obj, CONVEYOR_RISE, changed, "inserted conveyor rollers")
    bpy.context.view_layer.update()
    _raise_conveyor_stands(floor_frames)

    # Each carrier's old seated .439 and travelling .425 origin is mapped to
    # one .789 datum. All independent stage-detail roots share its exact delta.
    passive_groups = []
    for first in range(28, 556, 24):
        pallet = bpy.data.objects.get(f"source_{first:04d}")
        if pallet is None:
            continue
        rise = PALLET_Z - float(pallet.matrix_world.translation.z)
        members = []
        for node in range(first, first + 24):
            obj = bpy.data.objects.get(f"source_{node:04d}")
            if obj:
                _raise_root(obj, rise, changed, "same carrier group to fixed pallet datum")
                members.append(obj.name)
        passive_groups.append(dict(pallet=pallet.name, rise_m=rise, members=members))
    for name in ("JB_OP010_UID001", "JB_OP010_UID001_F01_removable_transport_carrier", "JB_OP020_UID001"):
        _raise_root(bpy.data.objects[name], 0.350, changed, "retained seated assembly to fixed work height")
    # Visible legacy installation-detail actors in the unchanged later STs.
    for node in (*range(1213, 1220), 1380, 1461):
        obj = bpy.data.objects.get(f"source_{node:04d}")
        if obj:
            _raise_root(obj, 0.350, changed, "later ST installed component follows raised seated carrier")

    for label, cell in manifest["layout"]["cells"].items():
        names = cell["source_names"]
        fixed = bpy.data.objects[names["OP030_lift_fixed"]]
        carriage = bpy.data.objects[cell["lift_carriage"]]
        positioners[label] = _new_base(
            label + "_positioner_base_v04", bpy.data.objects[cell["root"]], fixed, carriage, cell["offset_y_m"]
        )
        cell.update(positioner_base=positioners[label]["positioner_base"], positioner=positioners[label])
        _raise_root(bpy.data.objects[names["source_0683"]], CONVEYOR_RISE, changed, "positioner fixed case")
    entry = manifest["entry_lift"]
    positioners["OP020"] = _new_base(
        "OP020_positioner_base_v04",
        bpy.data.objects[entry["cell"]],
        bpy.data.objects[entry["fixed"]],
        bpy.data.objects[entry["carriage"]],
        -1.15,
    )
    entry.update(positioners["OP020"])
    _raise_root(bpy.data.objects["source_0671"], CONVEYOR_RISE, changed, "entry positioner fixed case")

    # Fixed cases, stops and sensors follow the conveying plane; inactive
    # station platens stay seated at the same .742 absolute datum as ABC.
    for station in (1, *range(4, 11)):
        first = 659 + 12 * (station - 1)
        for offset in range(5):
            obj = bpy.data.objects.get(f"source_{first + offset:04d}")
            if obj:
                rise = 0.350 if offset == 1 else CONVEYOR_RISE
                _raise_root(obj, rise, changed, "unchanged station positioner/stop/sensor at new line height")
    for label, hardware in manifest["transfer_hardware"]["cells"].items():
        for key in ("body", "stopper", "sensor"):
            _raise_root(bpy.data.objects[hardware[key]], CONVEYOR_RISE, changed, label + " transfer " + key)
        for name in hardware["brackets"]:
            _raise_root(bpy.data.objects[name], CONVEYOR_RISE, changed, label + " transfer bracket")
        for key in ("stopper_up_world", "stopper_down_world", "body_world", "sensor_world"):
            if key in hardware:
                hardware[key][2][3] += CONVEYOR_RISE
        hardware["v04_base_rise_m"] = CONVEYOR_RISE

    # OP020's already-seated product rises .350, so its matched receiver and
    # guided cylinders rise .350 together. Extend existing columns below them.
    slide = manifest["entry_slide"]
    for key in ("fixed", "carriage"):
        _raise_root(
            bpy.data.objects[slide[key]], 0.350, changed, "OP020 receiver/press unit preserves assembled relation"
        )
    for name in slide["shortened_columns"]:
        obj = bpy.data.objects[name]
        world = _world_vertices(obj)
        low, high = world[:, 2].min(), world[:, 2].max()
        before = [float(low), float(high)]
        world[:, 2] += 0.350 * (world[:, 2] - low) / (high - low)
        _write_world_vertices(obj, world)
        floor_frames.append(
            dict(root=name, rise_m=0.350, column_before_z_m=before, column_after_z_m=[float(low), float(high + 0.350)])
        )
    slide["column_height_after_m"] += 0.350
    slide["fixed_height_rise_m"] = 0.350
    slide["engaged_world"][2][3] += 0.350
    slide["retracted_world"][2][3] += 0.350
    slide["initial_world"] = slide["engaged_world"]

    # Infeed magazine and the retained outfeed rollers use their existing
    # stands. The old outfeed roller top .444 is aligned, avoiding its former
    # 51.5 mm level change at the main line end.
    _raise_floor_frame(bpy.data.objects["source_0825"], CONVEYOR_RISE, floor_frames)
    for node in range(826, 833):
        _raise_root(bpy.data.objects[f"source_{node:04d}"], CONVEYOR_RISE, changed, "infeed pallets and conveyor drive")
    outfeed_rise = ROLLER_Z - 0.444
    _raise_floor_frame(bpy.data.objects["source_0833"], outfeed_rise, floor_frames)
    _raise_root(bpy.data.objects["source_1677"], outfeed_rise, changed, "finished work on aligned outfeed roller deck")

    bpy.context.view_layer.update()
    # Physical quantities read back from actual stored object/mesh transforms.
    checks = dict(
        main_roller_top_m=_bounds(bpy.data.objects["source_0002"])[1][2],
        active_pallet_origin_m=float(bpy.data.objects["source_0292"].matrix_world.translation.z),
        active_product_origin_m=float(bpy.data.objects["JB_OP020_UID001"].matrix_world.translation.z),
        active_pallet_runner_bottom_m=float(_world_vertices(bpy.data.objects["source_0292_m0028_p01"])[:, 2].min()),
        remaining_clip_meshes=[
            obj.name
            for obj in scene.objects
            if obj.type == "MESH" and obj.name.startswith(("OP030_transport_H1", "OP030_transport_H2"))
        ],
        floor_contact_max_change_m=max(
            abs(row["after_bounds_m"][0][2] - row["before_bounds_m"][0][2])
            for row in floor_frames
            if "after_bounds_m" in row
        ),
        positioners={},
    )
    for label, row in positioners.items():
        platen_name = (
            "source_0672" if label == "OP020" else manifest["layout"]["cells"][label]["source_names"]["source_0684"]
        )
        checks["positioners"][label] = dict(
            carriage_local_z_m=float(bpy.data.objects[row["carriage"]].location.z),
            carriage_world_z_m=float(bpy.data.objects[row["carriage"]].matrix_world.translation.z),
            platen_world_z_m=float(bpy.data.objects[platen_name].matrix_world.translation.z),
        )
    assert abs(checks["main_roller_top_m"] - ROLLER_Z) < 2e-6
    assert abs(checks["active_pallet_origin_m"] - PALLET_Z) < 2e-6
    assert abs(checks["active_product_origin_m"] - PRODUCT_Z) < 2e-6
    assert abs(checks["active_pallet_runner_bottom_m"] - ROLLER_Z) < 2e-6
    for row in checks["positioners"].values():
        assert abs(row["carriage_local_z_m"] + 0.014) < 2e-6
        assert abs(row["platen_world_z_m"] - 0.742) < 2e-6
    assert not checks["remaining_clip_meshes"]
    assert original_count - sum(obj.type == "MESH" for obj in scene.objects) == 54

    manifest.update(
        observed_at=datetime.now().astimezone().isoformat(),
        evidence_basis="Pinned native reuse, explicit authorized height delta, evaluated mesh dimension readback",
        source=str(SOURCE.relative_to(ROOT)),
        source_sha256=SOURCE_SHA256,
        source_manifest=str(SOURCE_MANIFEST.relative_to(ROOT)),
        source_manifest_sha256=digest(SOURCE_MANIFEST),
        fixed_height=dict(
            pallet_origin_m=PALLET_Z,
            product_origin_m=PRODUCT_Z,
            roller_top_m=ROLLER_Z,
            main_conveyor_rise_m=CONVEYOR_RISE,
            entry_tooling_rise_m=0.350,
            outfeed_rise_m=outfeed_rise,
            work_lift_m=0.0,
            seat_lift_m=0.0,
            pin_stroke_m=0.037,
            positioners=positioners,
            changed_roots=changed,
            floor_frames=floor_frames,
            passive_carrier_groups=passive_groups,
            checks=checks,
        ),
        two_level_pallet_return_implemented=False,
        scope="Static v04 candidate; working ABC motion and surrounding parked robot collision checks are separate",
        formal_physical_validity_verdict=None,
    )
    for key, value in (
        ("split_layout_manifest", manifest["layout"]["cells"]),
        ("split_transfer_hardware", manifest["transfer_hardware"]),
        ("split_entry_lift", entry),
        ("split_entry_tooling_slide", slide),
        ("split_fixed_height_v04", manifest["fixed_height"]),
    ):
        scene[key] = json.dumps(value, ensure_ascii=False)
    scene["two_level_pallet_return_implemented"] = False
    scene["pallet_vertical_work_motion_m"] = 0.0
    scene["process_completion"] = "OP030 v04 fixed conveyor static candidate; motion checks separate"
    scene.frame_start = scene.frame_end = 1
    bpy.ops.wm.save_as_mainfile(filepath=str(output), compress=True)
    manifest.update(output=str(output.relative_to(ROOT)), output_sha256=digest(output))
    manifest_output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("OP030_SPLIT_FIXED_HEIGHT_STATIC_COMPLETE", str(output), manifest["output_sha256"], flush=True)
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "analysis/op030_split_fixed_height_static_v04.blend")
    parser.add_argument("--manifest_output", type=Path, default=ROOT / "audit/op030_split_static_v04.json")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    build_static(args.output.resolve(), args.manifest_output.resolve())


if __name__ == "__main__":
    main()
