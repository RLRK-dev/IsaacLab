# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Bake staggered B and retained A/C motion with fixed transport height [m, s]."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from continuous_common import digest, write_json
from op030_definition import ROOT
from op030_fixed_height_timeline_v04 import CONVEYOR_RISE
from op030_split_animation import bake_local, bake_wire, bake_world


def input_path(value):
    """Resolve a recorded rebuild input inside the portable artifact folder."""
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def translations(x, y, z):
    """Create world translations [m] from broadcast-compatible coordinates."""
    coordinates = np.broadcast_arrays(x, y, z)
    poses = np.repeat(np.eye(4)[None], coordinates[0].size, axis=0)
    poses[:, :3, 3] = np.stack(coordinates, axis=-1).reshape(-1, 3)
    return poses


def rotations_z(angles):
    """Create parent-local spindle rotations [rad]."""
    angles = np.asarray(angles)
    poses = np.repeat(np.eye(4)[None], len(angles), axis=0)
    poses[:, 0, 0] = poses[:, 1, 1] = np.cos(angles)
    poses[:, 1, 0], poses[:, 0, 1] = np.sin(angles), -np.sin(angles)
    return poses


def configure_presentation_cameras():
    """Frame the extended supply trays and top-entry contacts [m]."""
    definitions = {
        "wire_supply": ((1.68, 0.60, 2.30), (1.68, 0.60, 1.04), 34),
        "split_A_stock": ((-2.55, -2.85, 1.90), (-1.50, -1.70, 1.30), 28),
        "split_B_stock": ((2.55, 1.75, 1.90), (1.50, 0.60, 1.30), 28),
        "split_B": ((-1.80, -0.65, 2.45), (0.60, 0.60, 1.45), 24),
        "split_B_joint": ((0.80, 1.60, 1.90), (0.08, 0.78, 0.96), 48),
        "split_C_joint": ((-0.65, 3.95, 1.70), (0.02, 3.05, 0.93), 48),
        "split_A_parallel": ((1.8, -0.35, 2.0), (-0.65, -1.9, 1.05), 32),
        "split_A_bimanual": ((2.3, -1.7, 2.6), (-0.4, -1.7, 1.25), 38),
    }
    for size, old_y, eye, target in (
        ("M6", 1.95, (-0.17, 1.30, 1.32), (-1.05, 1.94, 0.91)),
        ("M14", 3.85, (-0.17, 3.20, 1.32), (-1.05, 3.84, 0.91)),
    ):
        feeder = bpy.data.objects["OP030C_feeder_" + size]
        delta = feeder.matrix_world.translation - Vector((-1.0, old_y, 0.84))
        definitions["split_C_" + size + "_feeder"] = (tuple(Vector(eye) + delta), tuple(Vector(target) + delta), 48)
    records = []
    for name, (eye, target, lens) in definitions.items():
        obj = bpy.data.objects.get("Review_OP030_" + name)
        if obj is None:
            obj = bpy.data.objects["Review_OP030_split_A"].copy()
            obj.data = obj.data.copy()
            obj.name = "Review_OP030_" + name
            bpy.context.scene.collection.objects.link(obj)
        before = dict(matrix_world=[list(row) for row in obj.matrix_world], lens_mm=obj.data.lens)
        obj.location = eye
        obj.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        obj.data.lens = lens
        records.append(dict(camera=name, before=before, eye_m=eye, target_m=target, lens_mm=lens))
    bpy.context.view_layer.update()
    return records


def readback_wire(record, data, frame):
    """Compare evaluated native cable vertices [m] and rigid lug transforms."""
    prefix, uid = f"wire_{record['number']}_", record["uid"]
    parameter = data[prefix + "parameter"][frame - 1]
    index = int(np.searchsorted(data[prefix + "shape_parameters"], parameter))
    expected = data[prefix + "shape_vertices"][index]
    obj = bpy.data.objects[uid + "_insulation"]
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    vertices = np.empty((len(mesh.vertices), 3), dtype=np.float32)
    mesh.vertices.foreach_get("co", vertices.ravel())
    evaluated.to_mesh_clear()
    vertex_error = float(np.max(np.abs(vertices - expected)))
    lug_error = max(
        float(
            np.max(
                np.abs(
                    np.asarray(bpy.data.objects[uid + "_" + end].matrix_world) - data[prefix + "lugs"][frame - 1, index]
                )
            )
        )
        for index, end in enumerate(("J1", "T"))
    )
    return vertex_error, lug_error


def shot_ranges(prepared, frame_count):
    """Read a complete sequence of cameras for the saved native frames."""
    ranges = []
    for index, segment in enumerate(prepared["segments"]):
        first = 1 if index == 0 else ranges[-1]["last_frame"] + 1
        last = segment["last_frame"]
        if last < first:
            continue
        camera = "split_" + segment["station"] if segment["kind"] == "station" else "split_overall"
        if segment["label"].startswith("OP020"):
            camera = "split_entry"
        ranges.append(dict(first_frame=first, last_frame=last, camera=camera, label=segment["label"]))
    ranges = prepared.get("shots", ranges)
    next_frame = 1
    for shot in ranges:
        if shot["first_frame"] != next_frame or shot["last_frame"] < next_frame:
            raise ValueError("Prepared cameras do not cover consecutive native frames")
        if "Review_OP030_" + shot["camera"] not in bpy.data.objects:
            raise ValueError("A planned camera is absent from the pinned native")
        next_frame = shot["last_frame"] + 1
    if next_frame != frame_count + 1:
        raise ValueError("Prepared cameras do not cover the entire motion")
    return ranges


def readback_background(objects: dict[str, list[list[float]]], frame: int, failures: list[dict]) -> float:
    """Check fixed background transforms with translations [m] at one frame."""
    maximum = 0.0
    for name, expected in objects.items():
        error = float(np.max(np.abs(np.asarray(bpy.data.objects[name].matrix_world) - np.asarray(expected))))
        maximum = max(maximum, error)
        if error > 5e-5:
            failures.append(dict(frame=frame, background_object=name, max_matrix_error=error))
    return maximum


def check_drawer_parent(drawer: str, static: dict) -> None:
    """Require the supply actuator to retain its staggered local coordinate frame."""
    if bpy.data.objects[drawer].parent != bpy.data.objects[static["stagger_v06"]["group"]]:
        raise ValueError("The drawer no longer uses its staggered local +X frame")


def bake_native(data_path, output):
    """Apply exact 30 Hz transforms and deformation samples to native objects."""
    prepared = json.loads(data_path.with_suffix(".json").read_text())
    if digest(data_path) != prepared["output_sha256"]:
        raise ValueError("Prepared motion digest differs")
    source = prepared["static_native"]
    if (
        digest(input_path(source["path"])) != source["sha256"]
        or digest(input_path(source["manifest"])) != source["manifest_sha256"]
    ):
        raise ValueError("Static integration source differs")
    static = json.loads(input_path(source["manifest"]).read_text())
    with np.load(data_path, allow_pickle=False) as saved:
        data = {key: saved[key] for key in saved.files}
    bpy.ops.wm.open_mainfile(filepath=str(input_path(source["path"])))
    scene = bpy.context.scene
    retention = static.get("retention", {})
    retained_carrier = bpy.data.objects.get(retention.get("carrier", ""))
    carrier_relative = None
    if retained_carrier is not None:
        carrier_relative = np.linalg.inv(np.asarray(bpy.data.objects["source_0292"].matrix_world)) @ np.asarray(
            retained_carrier.matrix_world
        )
    presentation_cameras = configure_presentation_cameras()
    frames = data["frames"]
    scene.render.fps, scene.render.fps_base = 30, 1.0
    scene.frame_start, scene.frame_end = 1, int(frames[-1])
    tracked = {}

    def world(name, poses, times=frames):
        obj = bpy.data.objects[name]
        bake_world(obj, poses, times)
        tracked[name] = (np.asarray(times), np.asarray(poses))

    def parent_local(name, poses):
        # Positioners read local Z; the relocated drawer actuator reads local
        # +X. Both must retain their fixed parent while following world tracks.
        obj = bpy.data.objects[name]
        if obj.parent is None:
            raise ValueError("A driven carriage lost its fixed parent: " + name)
        local = np.linalg.inv(np.asarray(obj.parent.matrix_world))[None] @ poses
        bake_local(obj, local, frames)
        tracked[name] = (np.asarray(frames), np.asarray(poses))

    world("JB_OP020_UID001", data["product"])
    world("source_0292", data["pallet"])
    parent_local(static["entry_lift"]["carriage"], translations(0, -1.15, data["op020_carriage"][:, 2, 3] - 0.392))
    world(static["entry_slide"]["carriage"], translations(data["entry_slide_x"], 0, 0.350))
    for index, name in enumerate(data["stopper_names"]):
        world(str(name), data["stopper_poses"][:, index])
    removed_robot_nodes = []
    for station in ("A", "B", "C"):
        cell = static["layout"]["cells"]["OP030" + station]
        node_frames, poses = data["robot_frames_" + station], data["robot_poses_" + station]
        for index, node in enumerate(data["robot_nodes_" + station]):
            source_name = f"source_{int(node):04d}"
            name = cell["source_names"][source_name]
            if name in bpy.data.objects:
                world(name, poses[:, index], node_frames)
            else:
                removed_robot_nodes.append(name)
        parent_local(
            cell["lift_carriage"], translations(0, cell["offset_y_m"], CONVEYOR_RISE + data["lift_" + station])
        )
    for index, name in enumerate(data["object_names"]):
        world(str(name), data["object_poses"][:, index])
    for station, size, side in (("A", "M4", 0), ("C", "M6", 0), ("C", "M14", 1)):
        driver = static["drivers"]["OP030" + station + "_" + size]
        root = bpy.data.objects[driver["root"]]
        if root.parent != bpy.data.objects[driver["flange"]]:
            raise ValueError("A permanent tool lost its original tool0 parent")
        spindle = bpy.data.objects[driver["spindle"]]
        initial = np.asarray(spindle.matrix_basis).copy()
        # Rotation occurs at the existing spindle origin, retaining its mount.
        matrices = initial[None] @ rotations_z(data["spindle_" + station][:, side])
        bake_local(spindle, matrices, frames)
    drawer = static["wire_supply"]["drawer"]
    check_drawer_parent(drawer, static)
    parent_local(drawer, data["drawer_B_world"])
    active = {row["uid"] for row in prepared["wires"]}
    for wire in static["wires"]:
        if wire["uid"] not in active:
            world(wire["uid"], data["drawer_B_world"])
    wire_results = []
    for record in prepared["wires"]:
        number, uid = record["number"], record["uid"]
        prefix = f"wire_{number}_"
        wire_results.append(
            bake_wire(
                uid,
                frames,
                data[prefix + "root"],
                data[prefix + "parameter"],
                {end: data[prefix + "lugs"][:, index] for index, end in enumerate(("J1", "T"))},
                data[prefix + "shape_parameters"],
                data[prefix + "shape_vertices"],
            )
        )
        tracked[uid] = (frames, data[prefix + "root"])
    if retention.get("clips"):
        raise ValueError("Removed cable restraints remain in v06")
    # Retain the pallet mounting frame/F01 without adding substitute clamps.
    if retained_carrier is not None:
        carrier = retained_carrier
        carrier.parent = bpy.data.objects["source_0292"]
        carrier.matrix_parent_inverse = Matrix.Identity(4)
        carrier.matrix_basis = Matrix(carrier_relative)
        tracked[carrier.name] = (frames, data["pallet"] @ carrier_relative)
    scene["split_animation_data"] = str(data_path)
    scene["split_animation_sha256"] = prepared["output_sha256"]
    scene["process_completion"] = (
        "Three-ST authored assembly sequence; auxiliary kinematic/mesh checks are recorded separately"
    )
    scene["physical_validity_verdict"] = "Independent formal review not performed"
    scene["fixed_conveyor_pallet_reference_z_m"] = 0.789
    scene["workstation_pallet_lift"] = False
    scene["two_level_pallet_return_implemented"] = False
    scene["robot_layout"] = "Alternating conveyor sides; OP030A -X, OP030B +X, OP030C -X"
    # The segment schedule has shared endpoint frames; film cuts partition it.
    ranges = shot_ranges(prepared, len(frames))
    scene.camera = bpy.data.objects["Review_OP030_split_overall"]
    # Compare stored matrices at process boundaries and evenly-spaced native
    # samples. This is an animation readback check, not a collision verdict.
    samples = sorted(
        set(np.linspace(1, len(frames), 31).astype(int))
        | {int(r[k]) for r in ranges for k in ("first_frame", "last_frame")}
        | {int((phase["first_frame"] + phase["last_frame"]) // 2) for phase in prepared["phases"]}
    )
    # Include actual deformation states, not just long stationary intervals.
    for record in prepared["wires"]:
        parameters = data[f"wire_{record['number']}_parameter"]
        _, unique_frames = np.unique(parameters, return_index=True)
        selected = np.linspace(0, len(unique_frames) - 1, min(65, len(unique_frames))).astype(int)
        samples.extend((unique_frames[selected] + 1).tolist())
    samples = sorted({int(frame) for frame in samples})
    max_error, failures = 0.0, []
    wire_error, lug_error, tool_error = 0.0, 0.0, 0.0
    background_error = 0.0
    background_objects = static.get("downstream_restored_objects", {})
    for frame in samples:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        background_error = max(background_error, readback_background(background_objects, frame, failures))
        for name, (times, poses) in tracked.items():
            found = np.flatnonzero(times == frame)
            if not len(found):
                continue
            error = float(np.max(np.abs(np.asarray(bpy.data.objects[name].matrix_world) - poses[found[-1]])))
            max_error = max(max_error, error)
            if error > 5e-5:
                failures.append(dict(frame=frame, object=name, max_matrix_error=error))
        for record in prepared["wires"]:
            error, end_error = readback_wire(record, data, frame)
            wire_error, lug_error = max(wire_error, error), max(lug_error, end_error)
            if error > 5e-6 or end_error > 5e-5:
                failures.append(
                    dict(frame=frame, wire=record["uid"], local_vertex_error_m=error, lug_matrix_error=end_error)
                )
        for driver in static["drivers"].values():
            flange = bpy.data.objects[driver["flange"]]
            root = bpy.data.objects[driver["root"]]
            # The permanently mounted adapter stays at the original tool0.
            error = float(np.max(np.abs(np.asarray(root.matrix_world) - np.asarray(flange.matrix_world))))
            tool_error = max(tool_error, error)
            if error > 5e-5:
                failures.append(dict(frame=frame, tool=root.name, flange_matrix_error=error))
    if failures:
        write_json(ROOT / "audit/op030_split_native_v06_readback_failed.json", failures)
        raise RuntimeError("Native animation differs from prepared matrices")
    bpy.ops.file.pack_all()
    external_images = [
        image.name for image in bpy.data.images if image.source == "FILE" and image.filepath and not image.packed_file
    ]
    external_libraries = [library.filepath for library in bpy.data.libraries]
    if external_images or external_libraries:
        raise RuntimeError(f"Unpacked native dependencies: {external_images}, {external_libraries}")
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(output), compress=True)
    output_sha = digest(output)
    write_json(
        ROOT / "data/op030_split_shots_v06.json",
        dict(
            native=str(output.relative_to(ROOT)),
            native_sha256=output_sha,
            ranges=ranges,
            motion=str(data_path.relative_to(ROOT / "data")),
            motion_sha256=prepared["output_sha256"],
            frame_end=len(frames),
            phases=prepared["phases"],
            phase_prefix="",
            scope_caption="EV用ジャンクションボックス｜支持部取付・ケーブル設置・端子締結｜千鳥配置 v06",
        ),
    )
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        source=source,
        prepared_motion=str(data_path),
        prepared_sha256=prepared["output_sha256"],
        output=str(output),
        output_sha256=output_sha,
        fps=30,
        frames=len(frames),
        duration_s=(len(frames) - 1) / 30,
        wire_animation=wire_results,
        removed_gripper_nodes=removed_robot_nodes,
        matrix_readback=dict(frames=samples, max_error=max_error, failures=failures),
        deformation_readback=dict(frames=samples, max_vertex_error_m=wire_error, max_lug_matrix_error=lug_error),
        permanent_tool_readback=dict(frames=samples, max_flange_matrix_error=tool_error),
        downstream_restored_readback=dict(
            frames=samples, objects=list(background_objects), max_matrix_error=background_error
        ),
        native_dependencies=dict(
            packed_image_count=sum(bool(image.packed_file) for image in bpy.data.images),
            external_images=external_images,
            external_libraries=external_libraries,
        ),
        presentation_cameras=presentation_cameras,
        fixed_conveyor=prepared["fixed_conveyor"],
        parallel_operations=prepared["parallel_operations"],
        staggered_layout=prepared["staggered_layout"],
        fastener_ownership=prepared["fastener_ownership"],
        formal_physical_validity_verdict=None,
    )
    write_json(ROOT / "audit/op030_split_native_v06.json", report)
    print("OP030_SPLIT_NATIVE_COMPLETE", str(output), len(frames), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=ROOT / "data/op030_split_animation_v06.npz")
    parser.add_argument("--output", type=Path, default=ROOT / "UR15_JB_OP030_split_v06.blend")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    bake_native(args.data, args.output)
