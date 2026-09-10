# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read actual v06 transfer, concurrent work and parked-neighbor geometry [m, s].

Reuse the v05 affine-aware native exporters and triangle checker. The new
scope is the properly rotated B robot/supply, including world -X drawer travel.
No v05 bank, source or audit is edited and no missing v06 input is substituted.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from probe_op030_front_integration_v05 import export_changed
from probe_op030_split_a_payload import check, digest
from probe_op030_split_v04_transfer import check_fixtures
from probe_op030_v05_integration import absolute, endpoint_delta, error, load_banks, native_export, write

V05_PREPARED = ROOT / "data/op030_split_animation_v05.npz"
WINDOWS = ("entry", "a_b", "b_c", "prefill", "drawer", "background", "b_initial", "b_final", "c_loaded")


def read_prepared(path: Path) -> tuple[dict, dict]:
    """Read a digest-bound prepared timeline and its actual station banks [m, s]."""
    metadata = json.loads(path.with_suffix(".json").read_text())
    if digest(path) != metadata["output_sha256"]:
        raise ValueError("Prepared NPZ digest mismatch")
    static = metadata["static_native"]
    if digest(absolute(static["path"])) != static["sha256"]:
        raise ValueError("Prepared static native digest mismatch")
    if digest(absolute(static["manifest"])) != static["manifest_sha256"]:
        raise ValueError("Prepared static manifest digest mismatch")
    if path.name.endswith("_v06.npz") and metadata.get("b_factory") != (
        "op030_split_b_stagger_v06:build_sequence_final"
    ):
        raise ValueError("Prepared v06 data must name the final staggered B factory")
    return metadata, load_banks(metadata)


def integration_plan(args) -> None:
    """Compare saved v06 identities with frozen A/C and unchanged transfer datums [m, s]."""
    metadata, banks = read_prepared(args.prepared)
    prior, old_banks = read_prepared(V05_PREPARED)
    if metadata["banks"]["B"]["sha256"] == prior["banks"]["B"]["sha256"]:
        raise ValueError("A new B bank is required; the frozen v05 bank cannot qualify v06")
    unchanged = {cell: metadata["banks"][cell]["sha256"] == prior["banks"][cell]["sha256"] for cell in "AC"}
    if not all(unchanged.values()):
        raise ValueError("The approved v06 integration scope requires frozen A/C banks")
    endpoints = {
        cell: {
            "initial": endpoint_delta(banks[cell], old_banks[cell], 0, 0),
            "final": endpoint_delta(banks[cell], old_banks[cell], -1, -1),
        }
        for cell in "ABC"
    }
    preload = int(banks["C"]["preload_frame_count"])
    endpoints["C"]["loaded_park"] = endpoint_delta(banks["C"], old_banks["C"], preload - 1, preload - 1)
    mechanical = {}
    with np.load(args.prepared, allow_pickle=False) as saved, np.load(V05_PREPARED, allow_pickle=False) as old:
        prior_segments = {row["label"]: row for row in prior["segments"] if row["kind"] == "transfer"}
        keys = (
            "product",
            "pallet",
            "drawer_B",
            "op020_carriage",
            "entry_slide_x",
            "lift_A",
            "lift_B",
            "lift_C",
            "stopper_poses",
        )
        for row in metadata["segments"]:
            if row["kind"] != "transfer":
                continue
            previous = prior_segments[row["label"]]
            a = slice(row["first_frame"] - 1, row["last_frame"])
            b = slice(previous["first_frame"] - 1, previous["last_frame"])
            mechanical[row["label"]] = {key: error(saved[key][a], old[key][b]) for key in keys}
        heights = {
            "product_z_error_m": float(np.max(abs(saved["product"][:, 2, 3] - 0.8845))),
            "pallet_z_error_m": float(np.max(abs(saved["pallet"][:, 2, 3] - 0.789))),
            "product_rotation_error": error(
                saved["product"][:, :3, :3],
                np.broadcast_to(old["product"][0, :3, :3], saved["product"][:, :3, :3].shape),
            ),
        }
        global_b = saved.get("robot_poses_B")
        root_xy = banks["B"]["root_poses"][:, :2, 3]
        b_root = {
            "baseline_xy_error_m": float(np.max(abs(root_xy - [0.9, -1.7]))),
            "minimum_root_rotation_determinant": float(np.linalg.det(banks["B"]["root_poses"][:, :3, :3]).min()),
            "global_robot_array_present": global_b is not None,
        }
    write(
        args.report,
        dict(
            observed_at=datetime.now().astimezone().isoformat(),
            prepared=str(args.prepared),
            prepared_sha256=digest(args.prepared),
            prepared_json_sha256=digest(args.prepared.with_suffix(".json")),
            source_static=metadata["static_native"],
            banks=metadata["banks"],
            frozen_v05_prepared_sha256=digest(V05_PREPARED),
            unchanged_bank_sha256=unchanged,
            endpoints=endpoints,
            mechanical_track_errors=mechanical,
            fixed_height=heights,
            b_root=b_root,
            preload_frame_count=preload,
            station_ranges=metadata["station_ranges"],
            parallel_operations=metadata["parallel_operations"],
            transfer_reuse_claim=False,
            required_native_checks=list(WINDOWS),
            scope=(
                "Saved array identity and scope checks only; changed B neighbors require actual v06 native mesh checks."
            ),
            formal_physical_validity_verdict=None,
        ),
    )
    print("V06_INTEGRATION_PLAN", metadata["frames"], unchanged, heights, b_root, flush=True)


def export_park(args) -> None:
    """Export one actual parked B or loaded C state as world triangles [m]."""
    import bpy

    metadata, banks = read_prepared(args.prepared)
    static = json.loads(absolute(metadata["static_native"]["manifest"]).read_text())
    bpy.ops.wm.open_mainfile(filepath=str(args.native))
    scene = bpy.context.scene
    if scene.get("split_animation_sha256") != metadata["output_sha256"]:
        raise ValueError("Native animation digest does not match the prepared NPZ")
    cell = "C" if args.window == "c_loaded" else "B"
    if cell == "C":
        interval = next(row for row in metadata["parallel_operations"] if row["purpose"] == "prefill_before_arrival")
        frame = interval["last_frame"]
    else:
        row = metadata["station_ranges"]["B"]
        frame = row["first_frame"] if args.window == "b_initial" else metadata["station_ranges"]["C"]["first_frame"]
    scene.frame_set(frame)
    aliases = static["layout"]["cells"]["OP030" + cell]["source_names"]
    roots = {aliases[f"source_{int(node):04d}"] for node in banks[cell]["node_ids"]}
    if cell == "B":
        # The product and the two installed wires must not be frozen into the
        # neighbor export. Remaining stock stays on the drawer at this frame.
        roots.update((static["wire_supply"]["drawer"], "OP030B_wire_supply_fixed"))
        installed = {"OP030B_H03_2_UID001", "OP030B_H03_1_UID005"} if args.window == "b_final" else set()
        roots.update(row["uid"] for row in static["wires"] if row["uid"] not in installed)
    else:
        roots.update(str(name) for name in banks[cell]["object_names"] if str(name).startswith("OP030C_feeder_"))

    def family(obj):
        while obj:
            yield obj.name
            obj = obj.parent

    selected = sorted(
        [
            obj
            for obj in scene.objects
            if obj.type in {"MESH", "CURVE"} and not obj.hide_render and roots.intersection(family(obj))
        ],
        key=lambda obj: obj.name,
    )
    if not selected:
        raise ValueError("Empty actual parked-neighbor selection")
    vertices, faces, vo, mesh_face_offsets = [], [], [0], [0]
    graph = bpy.context.evaluated_depsgraph_get()
    for obj in selected:
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        world = np.asarray(obj.matrix_world)
        points = np.asarray([v.co[:] for v in mesh.vertices])
        vertices.extend(points @ world[:3, :3].T + world[:3, 3])
        faces.extend(triangle.vertices[:] for triangle in mesh.loop_triangles)
        vo.append(len(vertices))
        mesh_face_offsets.append(len(faces))
        evaluated.to_mesh_clear()
    if args.data.exists():
        raise FileExistsError(args.data)
    np.savez_compressed(
        args.data,
        names=[obj.name for obj in selected],
        vertices=vertices,
        faces=faces,
        vertex_offsets=vo,
        face_offsets=mesh_face_offsets,
    )
    write(
        args.metadata,
        dict(
            observed_at=datetime.now().astimezone().isoformat(),
            native=str(args.native),
            native_sha256=digest(args.native),
            prepared_sha256=digest(args.prepared),
            output_sha256=digest(args.data),
            window=args.window,
            global_frames=[frame],
            meshes=len(selected),
            explicit_roots=sorted(roots),
            excluded_product=True,
            scope="Actual saved parked neighbor and stock; no formal physical verdict.",
            formal_physical_validity_verdict=None,
        ),
    )
    print("V06_PARK_EXPORT", args.window, frame, len(selected), flush=True)


def check_native_binding(args) -> None:
    """Read B root/drawer/supply identities from the baked native [m, s]."""
    import bpy

    metadata, banks = read_prepared(args.prepared)
    static = json.loads(absolute(metadata["static_native"]["manifest"]).read_text())
    bpy.ops.wm.open_mainfile(filepath=str(args.native))
    scene = bpy.context.scene
    if scene.get("split_animation_sha256") != metadata["output_sha256"]:
        raise ValueError("Native animation digest does not match prepared data")
    drawer = bpy.data.objects[static["wire_supply"]["drawer"]]
    parent = bpy.data.objects["OP030B_robot_supply_stagger_root"]
    aliases = static["layout"]["cells"]["OP030B"]["source_names"]
    uids = [row["uid"] for row in static["wires"]]
    stock_end = {"OP030B_H03_2_UID001", "OP030B_H03_1_UID005"}
    interval = next(
        row for row in metadata["parallel_operations"] if row["purpose"] == "present_10_wires_while_A_works"
    )
    presentation = np.arange(interval["first_frame"], interval["last_frame"] + 1)
    return_interval = next(
        row for row in metadata["parallel_operations"] if row["purpose"] == "return_remaining_8_during_outfeed"
    )
    return_frames = np.arange(return_interval["first_frame"], return_interval["last_frame"] + 1)
    frames = sorted(
        set(
            presentation.tolist()
            + [
                1,
                metadata["station_ranges"]["B"]["first_frame"],
                metadata["station_ranges"]["B"]["last_frame"],
                metadata["station_ranges"]["C"]["first_frame"],
                metadata["frames"],
            ]
        )
    )
    a_first = metadata["station_ranges"]["A"]["first_frame"]
    frames = sorted(set(frames + [a_first + frame - 1 for frame in (2818, 2840, 2841, 2954, 6026, 6047, 6048, 6162)]))
    with np.load(args.prepared, allow_pickle=False) as saved:
        # Full original-FK node matrices, not a separately rotated cell parent.
        poses_key = next((key for key in ("robot_poses_B", "poses_B") if key in saved), None)
        if poses_key is None:
            raise ValueError("Prepared B node poses are absent")
        node_ids = saved["robot_nodes_B"]
        differences, drawer_samples, relative_samples = [], [], []
        retained_differences = {cell: [] for cell in "AC"}
        determinant_min = np.inf
        for frame in frames:
            scene.frame_set(frame)
            authored_frames = saved["robot_frames_B"]
            right = min(int(np.searchsorted(authored_frames, frame)), len(authored_frames) - 1)
            if int(authored_frames[right]) == frame or right == 0:
                expected = saved[poses_key][right]
            else:
                left = right - 1
                # The queried gaps precede/follow B work and must be parked.
                # Do not invent interpolated FK for an unsampled moving gap.
                if np.max(abs(saved[poses_key][right] - saved[poses_key][left])) > 1e-8:
                    raise ValueError("Binding frame lies inside a nonconstant sparse B motion interval")
                expected = saved[poses_key][left]
            actual = np.asarray(
                [np.asarray(bpy.data.objects[aliases[f"source_{int(node):04d}"]].matrix_world) for node in node_ids]
            )
            differences.append(float(np.max(abs(actual - expected))))
            for cell in "AC":
                cell_frames = saved["robot_frames_" + cell]
                cell_poses = saved["robot_poses_" + cell]
                cr = min(int(np.searchsorted(cell_frames, frame)), len(cell_frames) - 1)
                if int(cell_frames[cr]) == frame or cr == 0:
                    wanted = cell_poses[cr]
                else:
                    if np.max(abs(cell_poses[cr] - cell_poses[cr - 1])) > 1e-8:
                        raise ValueError("A/C binding frame is inside a moving sparse interval")
                    wanted = cell_poses[cr - 1]
                cell_aliases = static["layout"]["cells"]["OP030" + cell]["source_names"]
                observed = np.asarray(
                    [
                        np.asarray(bpy.data.objects[cell_aliases[f"source_{int(node):04d}"]].matrix_world)
                        for node in saved["robot_nodes_" + cell]
                    ]
                )
                retained_differences[cell].append(float(np.max(abs(observed - wanted))))
            determinant_min = min(determinant_min, float(np.linalg.det(np.asarray(parent.matrix_world)[:3, :3])))
            if frame in presentation:
                world = np.asarray(drawer.matrix_world).copy()
                drawer_samples.append(world)
                relative_samples.append(
                    [np.linalg.inv(world) @ np.asarray(bpy.data.objects[uid].matrix_world) for uid in uids]
                )
        drawer_samples = np.asarray(drawer_samples)
        delta = drawer_samples[-1, :3, 3] - drawer_samples[0, :3, 3]
        expected_delta = np.array([-0.340, 0.0, 0.0])
        relative = np.asarray(relative_samples)
        scene.frame_set(metadata["station_ranges"]["C"]["first_frame"])
        remaining_parents = {
            uid: bpy.data.objects[uid].parent.name if bpy.data.objects[uid].parent else None
            for uid in uids
            if uid not in stock_end
        }
        # The native baker writes individual world tracks and removes parents.
        # Verify the actual retained relationship instead of requiring hierarchy.
        drawer_track = saved["drawer_B_world"]
        returned_relative, returned_world_errors, returned_drawer_errors = [], [], []
        for frame in return_frames:
            scene.frame_set(int(frame))
            world = np.asarray(drawer.matrix_world).copy()
            returned_drawer_errors.append(float(np.max(abs(world - drawer_track[frame - 1]))))
            actual = np.asarray([np.asarray(bpy.data.objects[uid].matrix_world) for uid in remaining_parents])
            # Remaining wire roots share the drawer datum; per-wire geometry
            # offsets are below these roots. animate_op030_split_v06.py writes
            # world(wire["uid"], data["drawer_B_world"]) for these eight UIDs.
            expected = drawer_track[frame - 1][None]
            returned_world_errors.append(float(np.max(abs(actual - expected))))
            returned_relative.append(np.linalg.inv(world) @ actual)
        returned_relative = np.asarray(returned_relative)
    result = dict(
        b_pose_maximum_error=float(max(differences)),
        b_pose_sample_frames=len(frames),
        b_pose_nodes=len(node_ids),
        retained_a_c_maximum_pose_errors={cell: max(values) for cell, values in retained_differences.items()},
        sampled_global_frames=frames,
        positive_stagger_parent_determinant_minimum=float(determinant_min),
        drawer_present_frames=len(presentation),
        drawer_world_displacement_m=delta.tolist(),
        drawer_world_minus_x_error_m=float(np.max(abs(delta - expected_delta))),
        ten_stock_uids=uids,
        stock_uid_count=len(uids),
        stock_relative_to_drawer_maximum_error=float(np.max(abs(relative - relative[:1]))),
        remaining_stock_after_B=remaining_parents,
        remaining_stock_return_frames=return_frames.tolist(),
        remaining_stock_return_relative_maximum_error=float(np.max(abs(returned_relative - returned_relative[:1]))),
        remaining_stock_prepared_pose_maximum_error=max(returned_world_errors),
        return_drawer_prepared_pose_maximum_error=max(returned_drawer_errors),
        native_stock_binding="Individual baked world tracks; parent names are descriptive only.",
        remaining_stock_expected_track="drawer_B_world, shared root datum; unique geometry below each UID root",
        baker_source="scripts/animate_op030_split_v06.py",
        baker_source_sha256=digest(ROOT / "scripts/animate_op030_split_v06.py"),
    )
    checks = {
        "original_b_nodes_match_prepared": result["b_pose_maximum_error"] < 2e-6,
        "retained_a_c_nodes_match_prepared": max(result["retained_a_c_maximum_pose_errors"].values()) < 2e-6,
        "proper_stagger_parent_rotation": abs(result["positive_stagger_parent_determinant_minimum"] - 1) < 2e-6,
        "drawer_moves_world_minus_x": result["drawer_world_minus_x_error_m"] < 2e-6,
        "ten_uids_present": result["stock_uid_count"] == 10,
        "ten_uids_follow_drawer": result["stock_relative_to_drawer_maximum_error"] < 2e-6,
        "eight_remaining_uids_follow_returning_drawer": len(remaining_parents) == 8
        and result["remaining_stock_return_relative_maximum_error"] < 2e-6,
        "remaining_uids_and_drawer_match_prepared": max(
            result["remaining_stock_prepared_pose_maximum_error"],
            result["return_drawer_prepared_pose_maximum_error"],
        )
        < 2e-6,
    }
    write(
        args.report,
        dict(
            observed_at=datetime.now().astimezone().isoformat(),
            native=str(args.native),
            native_sha256=digest(args.native),
            prepared_sha256=digest(args.prepared),
            source_static=metadata["static_native"],
            results=result,
            checks=checks,
            failed_checks=[name for name, passed in checks.items() if not passed],
            scope="Saved world poses and stock identities only; separate triangle checks cover concurrent geometry.",
            formal_physical_validity_verdict=None,
        ),
    )
    print("V06_NATIVE_BINDING", json.dumps(result, ensure_ascii=False), flush=True)
    if not all(checks.values()):
        raise SystemExit(1)


def main() -> None:
    """Run one pinned read-only v06 integration step without replacing old evidence."""
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("plan", "export", "check", "check_fixtures", "binding", "check_wait"))
    parser.add_argument("--prepared", type=Path, default=ROOT / "data/op030_split_animation_v06.npz")
    parser.add_argument("--native", type=Path)
    parser.add_argument("--window", choices=WINDOWS, default="entry")
    parser.add_argument("--prefix", default="op030_stagger_v06_integration")
    parser.add_argument("--cell", choices=("A", "B", "C"))
    parser.add_argument("--mesh", type=Path)
    parser.add_argument("--config", type=Path, default=ROOT / "audit/op030_split_b_stagger_motion_v06.json")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:])
    stem = args.prefix + "_" + args.window
    args.data = ROOT / "analysis" / (stem + "_meshes.npz")
    args.metadata = ROOT / "audit" / (stem + "_export.json")
    suffix = "_" + args.cell if args.mode == "check_wait" and args.cell else ""
    args.report = ROOT / "audit" / (stem + suffix + "_" + args.mode + ".json")
    if args.mode != "export" and args.report.exists():
        raise FileExistsError(args.report)
    if args.mode == "plan":
        integration_plan(args)
    elif args.mode == "binding":
        check_native_binding(args)
    elif args.mode == "export":
        if args.native is None:
            raise ValueError("Explicit v06 baked native is required")
        read_prepared(args.prepared)
        if args.window in {"b_initial", "b_final", "c_loaded"}:
            export_park(args)
        elif args.window in {"prefill", "drawer", "background"}:
            native_export(args)
        else:
            export_changed(args)
    elif args.mode == "check_wait":
        from probe_op030_stagger_background_v06 import waiting_check

        if args.window not in {"b_initial", "b_final", "c_loaded"} or args.cell is None or args.mesh is None:
            raise ValueError("check_wait needs a parked export, target cell and actual station mesh")
        waiting_check(args)
    elif args.mode == "check_fixtures":
        check_fixtures(SimpleNamespace(output=args.data, metadata=args.metadata, report=args.report, route=args.window))
    elif args.window in {"background", "b_initial", "b_final", "c_loaded"}:
        raise ValueError("World-only data requires the dedicated v06 background/wait check")
    else:
        check(args.data, args.metadata, args.report)


if __name__ == "__main__":
    main()
