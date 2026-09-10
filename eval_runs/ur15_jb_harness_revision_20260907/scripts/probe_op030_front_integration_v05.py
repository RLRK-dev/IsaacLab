# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read changed C waiting and transfer contexts from the final v05 native [m, s].

Reuses the prior native export, fixed-height schedule, affine-aware FCL and
named mechanism families. The original v04 and first v05 evidence is retained.
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
from probe_op030_split_a_payload import check, digest
from probe_op030_split_v04_transfer import _fixture_families, check_fixtures
from probe_op030_v05_integration import absolute, integration_plan, native_export, write


def frame_window(metadata: dict, name: str) -> np.ndarray:
    """Return inclusive native frame indices for an actual transfer or parked state."""
    segments = metadata["segments"]
    if name == "c_loaded":
        row = next(p for p in metadata["parallel_operations"] if p["purpose"] == "prefill_before_arrival")
        return np.array([row["last_frame"]])
    stations = {p["station"]: p for p in segments if p["kind"] == "station"}
    if name == "entry":
        return np.arange(1, stations["A"]["first_frame"] + 1)
    previous, following = ("A", "B") if name == "a_b" else ("B", "C")
    return np.arange(stations[previous]["last_frame"], stations[following]["first_frame"] + 1)


def export_changed(args) -> None:
    """Extract unchanged local triangles and actual evaluated frame transforms [m, s]."""
    import bpy

    metadata = json.loads(args.prepared.with_suffix(".json").read_text())
    if digest(args.prepared) != metadata["output_sha256"]:
        raise ValueError("Prepared data changed")
    static = json.loads(absolute(metadata["static_native"]["manifest"]).read_text())
    bpy.ops.wm.open_mainfile(filepath=str(args.native))
    scene = bpy.context.scene
    frame_ids = frame_window(metadata, args.window)
    scene.frame_set(int(frame_ids[0]))

    def ancestry(obj):
        while obj:
            yield obj.name
            obj = obj.parent

    meshes = sorted(
        [obj for obj in scene.objects if obj.type in {"MESH", "CURVE"} and not obj.hide_render],
        key=lambda obj: obj.name,
    )
    parents = [set(ancestry(obj)) for obj in meshes]
    families, moving_families = {}, set()
    if args.window == "c_loaded":
        with np.load(args.prepared) as data:
            aliases = static["layout"]["cells"]["OP030C"]["source_names"]
            roots = {aliases[f"source_{int(node):04d}"] for node in data["robot_nodes_C"]}
        with np.load(absolute(metadata["banks"]["C"]["path"])) as bank:
            index = int(bank["preload_frame_count"]) - 1
            # The whole-line fixed export intentionally omits tracked UID/gate
            # roots. Include the remaining stationary queue here as well as
            # tool-held nuts; old A/B contexts contain their old rear positions.
            roots.update(str(name) for name in bank["object_names"] if str(name).startswith("OP030C_feeder_"))
            roots.update(
                str(uid)
                for uid, owner in zip(bank["ledger_uids"], bank["ledger_owner"][index], strict=True)
                if owner in (1, 2)
            )
        payload = np.array([bool(roots.intersection(row)) for row in parents])
        selected = payload.copy()
    else:
        roots = {"JB_OP020_UID001", "source_0292"}
        if args.window != "entry":
            roots.update(("OP030_T01_UID001", "OP030_T02_UID001"))
            with np.load(absolute(metadata["banks"]["A"]["path"])) as bank:
                roots.update(str(name) for name in bank["assembled_uids"])
        if args.window == "b_c":
            roots.update(row["uid"] for row in metadata["wires"])
        payload = np.array([bool(roots.intersection(row)) for row in parents])
        remaining = []
        if args.window == "b_c":
            used = {row["uid"] for row in metadata["wires"]}
            remaining = [bpy.data.objects[row["uid"]] for row in static["wires"] if row["uid"] not in used]
        families, moving_families = _fixture_families(
            json.loads(scene["split_fixed_height_v04"]),
            json.loads(scene["split_entry_tooling_slide"]),
            json.loads(scene["split_transfer_hardware"]),
            args.window,
            remaining,
        )
        active = payload | np.array([families.get(obj.name) in moving_families for obj in meshes])
        boxes = np.array([obj.bound_box for obj in meshes])

        def bounds():
            matrices = np.array([np.asarray(obj.matrix_world) for obj in meshes])
            points = np.einsum("nij,nkj->nki", matrices[:, :3, :3], boxes) + matrices[:, None, :3, 3]
            return np.stack((points.min(1), points.max(1)), axis=1)

        sweep = np.array([[np.inf] * 3, [-np.inf] * 3])
        all_bounds = []
        for frame in frame_ids:
            scene.frame_set(int(frame))
            current = bounds()
            all_bounds.append(current)
            sweep[0] = np.minimum(sweep[0], current[active, 0].min(0))
            sweep[1] = np.maximum(sweep[1], current[active, 1].max(0))
        selected = active.copy()
        for current in all_bounds:
            selected |= np.all(
                np.minimum(current[:, 1], sweep[1] + 0.025) >= np.maximum(current[:, 0], sweep[0] - 0.025), axis=1
            )
    objects = [obj for obj, use in zip(meshes, selected, strict=True) if use]
    scene.frame_set(int(frame_ids[0]))
    graph = bpy.context.evaluated_depsgraph_get()
    vertices, faces, vo, mesh_face_offsets = [], [], [0], [0]
    for obj in objects:
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        points = np.array([v.co[:] for v in mesh.vertices])
        if args.window == "c_loaded":
            matrix = np.asarray(obj.matrix_world)
            points = points @ matrix[:3, :3].T + matrix[:3, 3]
        vertices.extend(points)
        faces.extend([tri.vertices[:] for tri in mesh.loop_triangles])
        vo.append(len(vertices))
        mesh_face_offsets.append(len(faces))
        evaluated.to_mesh_clear()
    arrays = dict(
        names=[obj.name for obj in objects],
        vertices=np.asarray(vertices),
        faces=np.asarray(faces),
        vertex_offsets=vo,
        face_offsets=mesh_face_offsets,
    )
    if args.window != "c_loaded":
        transforms = []
        for frame in frame_ids:
            scene.frame_set(int(frame))
            transforms.append([np.asarray(obj.matrix_world).copy() for obj in objects])
        arrays.update(
            payload=payload[selected],
            families=[families.get(obj.name, "") for obj in objects],
            matrices=np.asarray(transforms),
            times=(frame_ids - frame_ids[0]) / 30,
            global_frames=frame_ids,
        )
    if args.data.exists():
        raise FileExistsError(args.data)
    np.savez_compressed(args.data, **arrays)
    write(
        args.metadata,
        dict(
            observed_at=datetime.now().astimezone().isoformat(),
            native=str(args.native),
            native_sha256=digest(args.native),
            prepared=str(args.prepared),
            prepared_sha256=digest(args.prepared),
            output_sha256=digest(args.data),
            frames=len(frame_ids),
            global_frames=frame_ids.tolist(),
            window=args.window,
            selected_meshes=len(objects),
            payload_roots=sorted(roots),
            payload_names=np.asarray([obj.name for obj in meshes])[payload].tolist(),
            moving_families=sorted(moving_families),
            scope="Actual final-native triangles and affine transforms; new C stationary "
            "robots and presenter context included. No physical-validity verdict.",
            formal_physical_validity_verdict=None,
        ),
    )
    print("FRONT_V05_EXPORT", args.window, len(frame_ids), len(objects), flush=True)


def check_wait(args) -> None:
    """Compare the loaded C park against A/B moving actual meshes at all saved times [m, s]."""
    from op030_split_product_delta import DeltaCheck, load, mesh_points
    from probe_op030_v05_background import Station

    data = load(args.data)
    metadata = json.loads(args.metadata.read_text())
    if digest(args.data) != metadata["output_sha256"]:
        raise ValueError("C waiting mesh changed")
    prepared = json.loads(args.prepared.with_suffix(".json").read_text())
    bank_path = absolute(prepared["banks"][args.cell]["path"])
    station = Station(args.cell, args.mesh, bank_path, args.config)
    low = np.array([mesh_points(data, i)[0].min(0) for i in range(len(data["names"]))])
    high = np.array([mesh_points(data, i)[0].max(0) for i in range(len(data["names"]))])
    active = np.flatnonzero(station.active)
    probe = DeltaCheck(data, station.screen, [])
    probe.indices = active
    maximum_overlap = 0
    minimum_distance = np.inf
    first = 0
    if args.cell == "A":
        with np.load(absolute(prepared["banks"]["C"]["path"])) as c_bank:
            first = int(c_bank["preload_frame_count"]) - 1
    for frame in range(first, len(station.bank["times"])):
        world = station.apply(frame)
        centers = np.einsum("nij,nj->ni", world[:, :3, :3], station.screen.centers) + world[:, :3, 3]
        extents = np.einsum("nij,nj->ni", abs(world[:, :3, :3]), station.screen.extents)
        separation = np.maximum(
            (centers - extents)[active, None] - high[None], low[None] - (centers + extents)[active, None]
        )
        overlap = int(np.count_nonzero(np.all(separation <= 1e-6, axis=-1)))
        maximum_overlap = max(maximum_overlap, overlap)
        minimum_distance = min(minimum_distance, float(np.linalg.norm(np.maximum(separation, 0), axis=-1).min()))
        if overlap:
            world = station.apply(frame, exact_wire=True)
            probe.sample(frame + 1, float(station.bank["times"][frame]), np.eye(4), world)
    write(
        args.report,
        dict(
            observed_at=datetime.now().astimezone().isoformat(),
            cell=args.cell,
            source_native=metadata["native"],
            native_sha256=metadata["native_sha256"],
            waiting_mesh=str(args.data),
            waiting_mesh_sha256=digest(args.data),
            station_mesh=str(args.mesh),
            station_mesh_sha256=digest(args.mesh),
            bank=str(bank_path),
            bank_sha256=digest(bank_path),
            first_bank_index=first,
            frames=len(station.bank["times"]) - first,
            maximum_aabb_pair_count=maximum_overlap,
            minimum_aabb_distance_m=minimum_distance,
            results=probe.record(),
            formal_physical_validity_verdict=None,
        ),
    )
    print("FRONT_V05_WAIT", args.cell, maximum_overlap, len(probe.record()["hit_frames"]), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("plan", "export", "check", "check_fixtures", "check_wait"))
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--native", type=Path)
    parser.add_argument(
        "--window", choices=("entry", "a_b", "b_c", "prefill", "drawer", "background", "c_loaded"), default="prefill"
    )
    parser.add_argument("--prefix", default="op030_front_v05_integration")
    parser.add_argument("--cell", choices=("A", "B"))
    parser.add_argument("--mesh", type=Path)
    parser.add_argument("--config", type=Path, default=ROOT / "audit/op030_split_b_motion_v05.json")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:])
    stem = args.prefix + "_" + args.window
    args.data = ROOT / "analysis" / (stem + "_meshes.npz")
    args.metadata = ROOT / "audit" / (stem + "_export.json")
    suffix = "_" + args.cell if args.mode == "check_wait" else ""
    args.report = ROOT / "audit" / (stem + suffix + "_" + args.mode + ".json")
    if args.mode != "export" and args.report.exists():
        raise FileExistsError(args.report)
    if args.mode == "plan":
        integration_plan(args.prepared, args.report)
    elif args.mode == "export":
        if args.native is None:
            raise ValueError("Explicit final native is required")
        if args.window in ("prefill", "drawer", "background"):
            native_export(args)
        else:
            export_changed(args)
    elif args.mode == "check_wait":
        if args.window != "c_loaded" or args.cell is None or args.mesh is None:
            raise ValueError("check_wait needs c_loaded, A/B cell and its actual mesh")
        check_wait(args)
    elif args.mode == "check_fixtures":
        check_fixtures(SimpleNamespace(output=args.data, metadata=args.metadata, report=args.report, route=args.window))
    else:
        if args.window in ("background", "c_loaded"):
            raise ValueError("World-only data needs a dedicated background/wait checker")
        check(args.data, args.metadata, args.report)


if __name__ == "__main__":
    main()
