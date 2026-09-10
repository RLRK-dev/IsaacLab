# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Export and screen constant-height entry and inter-ST payload sweeps [m, s]."""

import argparse
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from op030_definition import CY, pose, product_frame
from op030_fixed_height_timeline_v04 import Timeline
from probe_op030_split_a_payload import digest


def make_timeline(route):
    """Reuse the new timeline primitives without a workpiece vertical transition [m, s]."""
    timeline = Timeline()
    if route == "entry":
        timeline.transition("OP020 tooling outward", 2.5, entry_slide_x=0.285)
        timeline.transition("OP020 pins/stop retract", 1.5, op020_carriage_z=0.705, stopper_OP020=0.0)
        timeline.transition("OP020 to A at fixed height", 6.0, y=CY)
        timeline.arrive("A")
    else:
        departing, arriving = ("A", "B") if route == "a_b" else ("B", "C")
        timeline.values["y"] = [CY + {"A": 0.0, "B": 2.3}[departing]]
        timeline.values[departing] = [-0.014]
        timeline.values["op020_carriage_z"] = [0.705]
        timeline.values["entry_slide_x"] = [0.285]
        timeline.leave(departing)
        timeline.transition(
            departing + " to " + arriving + " at fixed height", 6.0, y=CY + {"B": 2.3, "C": 4.6}[arriving]
        )
        timeline.arrive(arriving)
    return timeline


def _fixture_families(height, entry_slide, hardware, route, remaining_wire_roots):
    import bpy

    families = {}
    for label, row in height["positioners"].items():
        for root_key in ("fixed", "carriage"):
            root = bpy.data.objects[row[root_key]]
            for obj in (root, *root.children_recursive):
                families[obj.name] = label + "_positioner"
    for key in ("fixed", "carriage"):
        root = bpy.data.objects[entry_slide[key]]
        for obj in (root, *root.children_recursive):
            families[obj.name] = "OP020_slide"
    for label, row in hardware["cells"].items():
        for key in ("body", "stopper", "sensor"):
            root = bpy.data.objects[row[key]]
            for obj in (root, *root.children_recursive):
                families[obj.name] = label + "_stopper"
        for name in row["brackets"]:
            families[name] = label + "_stopper"
    moving_families = (
        {"OP020_positioner", "OP020_slide", "OP020_stopper", "OP030A_positioner"}
        if route == "entry"
        else {
            "OP030" + label + suffix
            for label in (("A", "B") if route == "a_b" else ("B", "C"))
            for suffix in ("_positioner", "_stopper")
        }
    )
    if remaining_wire_roots:
        for name in ("OP030B_wire_supply_drawer", "OP030B_wire_supply_fixed"):
            root = bpy.data.objects[name]
            for obj in (root, *root.children_recursive):
                families[obj.name] = "OP030B_wire_supply"
        for root in remaining_wire_roots:
            for obj in (root, *root.children_recursive):
                families[obj.name] = "OP030B_wire_supply"
        # The rerouted FRL hose is a changed fixed obstacle. Keep it outside
        # the inherited guide/slider-interface group for the drawer sweep.
        hose = "OP030B_wire_supply__OP030_supply_actuator_supply_hose"
        families[hose] = "OP030B_fixed_service_hose"
        moving_families.add("OP030B_wire_supply")
    return families, moving_families


def export(args):
    """Record evaluated native triangle transforms over the actual pin/slide timeline [m, s]."""
    import bpy
    from mathutils import Matrix

    bpy.ops.wm.open_mainfile(filepath=str(args.native))
    scene = bpy.context.scene
    height = json.loads(scene["split_fixed_height_v04"])
    layout = json.loads(scene["split_layout_manifest"])
    entry_lift = json.loads(scene["split_entry_lift"])
    entry_slide = json.loads(scene["split_entry_tooling_slide"])
    hardware = json.loads(scene["split_transfer_hardware"])
    timeline = make_timeline(args.route)
    product, pallet = bpy.data.objects["JB_OP020_UID001"], bpy.data.objects["source_0292"]

    def ancestors(obj):
        values = []
        while obj:
            values.append(obj)
            obj = obj.parent
        return values

    def set_world(matrices):
        pairs = [(bpy.data.objects[name], matrix) for name, matrix in matrices.items() if name in bpy.data.objects]
        for depth in sorted({len(ancestors(obj)) for obj, _ in pairs}):
            for obj, matrix in pairs:
                if len(ancestors(obj)) == depth:
                    obj.matrix_world = Matrix(matrix)
            bpy.context.view_layer.update()

    bank_records = {}
    for cell, path in (("A", args.a_bank), ("B", args.b_bank), ("C", args.c_bank)):
        with np.load(path) as bank:
            is_departing = (cell == "A" and args.route != "entry") or (cell == "B" and args.route == "b_c")
            index = -1 if is_departing else args.c_park_index if cell == "C" else 0
            matrices = bank["poses"][index].copy()
            matrices[:, 1, 3] += layout["OP030" + cell]["offset_y_m"]
            names = layout["OP030" + cell]["source_names"]
            set_world(
                {
                    names[f"source_{int(node):04d}"]: matrix
                    for node, matrix in zip(bank["node_ids"], matrices, strict=True)
                }
            )
            if cell in {"A", "C"} and "object_names" in bank:
                held = {}
                for name, matrix in zip(bank["object_names"], bank["object_poses"][index], strict=True):
                    if str(name).startswith("OP030" + cell + "_feeder_"):
                        value = matrix.copy()
                        value[1, 3] += layout["OP030" + cell]["offset_y_m"]
                        held[str(name)] = value
                set_world(held)
            bank_records[cell] = dict(
                path=str(path),
                sha256=digest(path),
                frame=index,
                pose_scope="Supplied original-FK bank endpoint; validity is limited to these exact poses",
            )
    if args.route != "entry":
        with np.load(args.a_bank) as bank:
            last = dict(zip(bank["object_names"].tolist(), bank["object_poses"][-1], strict=True))
        inverse = np.linalg.inv(last["JB_OP020_UID001"])
        installed = [f"OP030_T{number:02d}_UID001" for number in (1, 2)]
        installed += [f"OP030A_feeder_M4_UID{number:03d}" for number in range(1, 5)]
        for name in installed:
            obj = bpy.data.objects[name]
            obj.parent = product
            obj.matrix_parent_inverse = Matrix.Identity(4)
            obj.matrix_basis = Matrix(inverse @ last[name])
    # B-to-C uses the C working snapshot, containing the exact final pair of
    # top-entry wires. Other routes use the static input before wire install.
    if args.route == "b_c":
        assert all(
            product in ancestors(bpy.data.objects[name]) for name in ("OP030B_H03_2_UID001", "OP030B_H03_1_UID005")
        )
    remaining_wire_roots = []
    if args.drawer_return:
        if args.route != "b_c":
            raise ValueError("Drawer return belongs to the B-to-C transfer")
        inventory = json.loads(scene["split_wire_inventory"])
        remaining_wire_roots = [
            bpy.data.objects[row["root"]]
            for row in inventory
            if row["uid"] not in {"OP030B_H03_2_UID001", "OP030B_H03_1_UID005"}
        ]
    wire_stock_matrices = {obj.name: np.asarray(obj.matrix_world).copy() for obj in remaining_wire_roots}
    if args.drawer_return:
        from op030_split_b_v04_drawer import drawer_extension

        drawer_values = drawer_extension(np.arange(timeline.frame) / 30, supply_start=-2.5, return_start=0.0)

    def apply(index):
        values = timeline.values
        y = values["y"][index]
        product.matrix_world = Matrix(product_frame(y=y, lift=0.350))
        pallet.matrix_world = Matrix(pose(location=(0, y, 0.789)))
        for cell in ("A", "B", "C"):
            bpy.data.objects[layout["OP030" + cell]["lift_carriage"]].location.z = values[cell][index]
        bpy.data.objects[entry_lift["carriage"]].location.z = values["op020_carriage_z"][index] - 0.756
        bpy.data.objects[entry_slide["carriage"]].location.x = values["entry_slide_x"][index]
        if args.drawer_return:
            bpy.data.objects["OP030B_wire_supply_drawer"].location.x = drawer_values[index]
            for obj in remaining_wire_roots:
                matrix = wire_stock_matrices[obj.name].copy()
                matrix[0, 3] += drawer_values[index]
                obj.matrix_world = Matrix(matrix)
        for label, row in hardware["cells"].items():
            matrix = np.asarray(row["stopper_down_world"]).copy()
            matrix[2, 3] += 0.055 * values["stopper_" + label][index]
            bpy.data.objects[row["stopper"]].matrix_world = Matrix(matrix)
        bpy.context.view_layer.update()

    apply(0)
    all_meshes = [obj for obj in scene.objects if obj.type in {"MESH", "CURVE"} and not obj.hide_render]
    payload = {obj.name for obj in all_meshes if product in ancestors(obj) or pallet in ancestors(obj)}

    def bounds(obj):
        matrix = np.asarray(obj.matrix_world)
        points = np.asarray(obj.bound_box) @ matrix[:3, :3].T + matrix[:3, 3]
        return np.asarray([points.min(0), points.max(0)])

    boxes = np.asarray([bounds(obj) for obj in all_meshes if obj.name in payload])
    delta = np.array([0, timeline.values["y"][-1] - timeline.values["y"][0], 0])
    sweep = np.array([boxes[:, 0].min(0) + np.minimum(delta, 0), boxes[:, 1].max(0) + np.maximum(delta, 0)])
    families, moving_families = _fixture_families(height, entry_slide, hardware, args.route, remaining_wire_roots)
    # Select the entire moving fixture and a conservative region around its
    # fixed support. The slide sweep adds its explicit 285 mm X travel.
    region = sweep.copy()
    for obj in all_meshes:
        if families.get(obj.name) in moving_families:
            box = bounds(obj)
            region[0] = np.minimum(region[0], box[0])
            region[1] = np.maximum(
                region[1], box[1] + ([0.285, 0, 0] if families.get(obj.name) == "OP020_slide" else [0, 0, 0])
            )
    selected = [
        obj
        for obj in all_meshes
        if obj.name in payload
        or families.get(obj.name) in moving_families
        or np.all(np.minimum(bounds(obj)[1], region[1] + 0.025) >= np.maximum(bounds(obj)[0], region[0] - 0.025))
    ]
    selected.sort(key=lambda obj: obj.name)
    graph = bpy.context.evaluated_depsgraph_get()
    vertices, faces, vo, mesh_face_offsets = [], [], [0], [0]
    for obj in selected:
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        vertices.extend([vertex.co[:] for vertex in mesh.vertices])
        faces.extend([triangle.vertices[:] for triangle in mesh.loop_triangles])
        vo.append(len(vertices))
        mesh_face_offsets.append(len(faces))
        evaluated.to_mesh_clear()
    transforms, datum_samples = [], []
    for index in range(timeline.frame):
        apply(index)
        transforms.append([np.asarray(obj.matrix_world).copy() for obj in selected])
        datum_samples.append([product.matrix_world.translation.z, pallet.matrix_world.translation.z])
        if index % 60 == 0:
            print("V04_TRANSFER_EXPORT", args.route, index, timeline.frame, flush=True)
    datum_samples = np.asarray(datum_samples)
    assert np.ptp(datum_samples, axis=0).max() < 1e-7
    np.savez_compressed(
        args.output,
        names=[obj.name for obj in selected],
        payload=[obj.name in payload for obj in selected],
        families=[families.get(obj.name, "") for obj in selected],
        vertices=vertices,
        faces=faces,
        vertex_offsets=vo,
        face_offsets=mesh_face_offsets,
        matrices=transforms,
        times=np.arange(timeline.frame) / 30,
    )
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        native=str(args.native),
        native_sha256=digest(args.native),
        route=args.route,
        output=str(args.output),
        output_sha256=digest(args.output),
        frames=timeline.frame,
        segments=timeline.segments,
        bank_endpoints=bank_records,
        payload_names=sorted(payload),
        selected_names=[obj.name for obj in selected],
        selected_meshes=len(selected),
        moving_families=sorted(moving_families),
        payload_swept_aabb_m=sweep.tolist(),
        examined_region_m=region.tolist(),
        product_pallet_z_m=datum_samples[0].tolist(),
        maximum_vertical_travel_m=float(np.ptp(datum_samples, axis=0).max()),
        source_script_sha256=digest(Path(__file__)),
        timeline_script_sha256=digest(ROOT / "scripts/op030_fixed_height_timeline_v04.py"),
        support_contact_exemptions=[],
        formal_physical_validity_verdict=None,
        drawer_return=dict(
            enabled=args.drawer_return, duration_s=2.5, remaining_uids=[obj.name for obj in remaining_wire_roots]
        ),
    )
    args.metadata.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("V04_TRANSFER_EXPORT_COMPLETE", args.route, len(selected), len(payload), flush=True)


def check_fixtures(args):
    """Screen moving fixture components against objects outside their own assembly [m, s]."""
    from probe_op030_split_a_payload import check

    metadata = json.loads(args.metadata.read_text())
    assert digest(args.output) == metadata["output_sha256"]
    with np.load(args.output) as saved:
        data = {key: saved[key].copy() for key in saved.files}
    moved = np.max(abs(data["matrices"] - data["matrices"][:1]), axis=(0, 2, 3)) > 1e-7
    reports = {}
    with tempfile.TemporaryDirectory(prefix="v04_fixture_", dir=ROOT / "analysis") as scratch:
        scratch = Path(scratch)
        for family in metadata["moving_families"]:
            active = (data["families"] == family) & moved
            if not active.any():
                continue
            keep = active | ((data["families"] != family) & ~data["payload"])
            selected = np.flatnonzero(keep)
            vertices, faces, vo, mesh_face_offsets = [], [], [0], [0]
            for index in selected:
                vertices.extend(data["vertices"][data["vertex_offsets"][index] : data["vertex_offsets"][index + 1]])
                faces.extend(data["faces"][data["face_offsets"][index] : data["face_offsets"][index + 1]])
                vo.append(len(vertices))
                mesh_face_offsets.append(len(faces))
            mesh = scratch / (family + ".npz")
            record = scratch / (family + ".json")
            result = scratch / (family + "_check.json")
            np.savez_compressed(
                mesh,
                names=data["names"][selected],
                payload=active[selected],
                vertices=vertices,
                faces=faces,
                vertex_offsets=vo,
                face_offsets=mesh_face_offsets,
                matrices=data["matrices"][:, selected],
                times=data["times"],
            )
            record.write_text(json.dumps(dict(output_sha256=digest(mesh))))
            check(mesh, record, result)
            reports[family] = json.loads(result.read_text())
            reports[family]["moving_meshes"] = data["names"][active].tolist()
            reports[family]["same_assembly_interfaces_omitted"] = data["names"][
                (data["families"] == family) & ~moved
            ].tolist()
    args.report.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                source=str(args.output),
                source_sha256=digest(args.output),
                route=args.route,
                frames=len(data["times"]),
                fixtures=reports,
                scope=(
                    "Moving fixture meshes vs external assemblies; payload interfaces are recorded "
                    "by the separate payload check"
                ),
                within_assembly_scope=(
                    "Retained sliding/linkage interfaces are omitted within the explicitly named mechanism only"
                ),
                formal_physical_validity_verdict=None,
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(
        "V04_FIXTURE_CHECK_COMPLETE",
        args.route,
        {key: len(value["hits"]) for key, value in reports.items()},
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("export", "check", "check_fixtures"))
    parser.add_argument("--route", choices=("entry", "a_b", "b_c"), required=True)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--a_bank", type=Path, default=ROOT / "data/op030_split_a_motion_v03.npz")
    parser.add_argument("--b_bank", type=Path, default=ROOT / "analysis/op030_split_b_top_entry_clip_v03_native30.npz")
    parser.add_argument("--c_bank", type=Path, default=ROOT / "data/op030_split_c_motion_v03.npz")
    parser.add_argument("--c_park_index", type=int, default=0)
    parser.add_argument("--drawer_return", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:])
    stem = "op030_split_v04_" + args.route + "_transfer"
    args.native = args.native or ROOT / "analysis" / (
        "op030_split_c_fixed_height_v04_meshes_snapshot.blend"
        if args.route == "b_c"
        else "op030_split_fixed_height_static_v04.blend"
    )
    args.output = args.output or ROOT / "analysis" / (stem + "_meshes.npz")
    args.metadata = args.metadata or ROOT / "audit" / (stem + "_export.json")
    args.report = args.report or ROOT / "audit" / (
        stem + ("_fixtures_check.json" if args.mode == "check_fixtures" else "_check.json")
    )
    if args.mode == "export":
        export(args)
    elif args.mode == "check_fixtures":
        check_fixtures(args)
    else:
        from probe_op030_split_a_payload import check

        check(args.output, args.metadata, args.report)


if __name__ == "__main__":
    main()
