# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Bind v05 integration checks to the retained fixed-height schedule [m, rad, s].

This helper never changes a native or a bank. Exact matching transfer states
inherit named v04 evidence. Changed prefill/drawer overlaps are read from the
new baked native, using the retained actual-triangle checker with affine scale
baked into vertices. Station-local checks and physical validity are separate.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from op030_fixed_height_timeline_v04 import assemble_timeline
from probe_op030_split_a_payload import check, digest

OLD_PREPARED = ROOT / "data/op030_split_animation_v04.npz"
REFERENCES = {
    "entry": [
        "op030_split_v04_entry_installation_transfer_check.json",
        "op030_split_v04_entry_installation_transfer_fixtures_check.json",
    ],
    "a_b": [
        "op030_split_v04_a_b_installation_transfer_check.json",
        "op030_split_v04_a_b_installation_transfer_fixtures_check.json",
    ],
    "b_c": [
        "op030_split_v04_b_c_installation_drawer_transfer_check.json",
        "op030_split_v04_b_c_installation_drawer_transfer_fixtures_check.json",
    ],
    "drawer": ["op030_split_v04_drawer_open_check.json", "op030_split_v04_drawer_open_final_delta_check.json"],
    "prefill": ["op030_split_v04_prefill_installation_classified.json"],
    "fixed_background": [
        "op030_downstream_park_v04_classification.json",
        "op030_duct_support_trim_v04_contacts.json",
        "op030_downstream_restored_v04.json",
        "op030_downstream_restored_v04_motion_delta.json",
        "op030_downstream_restored_v04_transfer_check.json",
    ],
}


def absolute(value: str | Path) -> Path:
    """Resolve a recorded artifact path without changing working directories."""
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def write(path: Path, value: dict) -> None:
    """Write a new audit only; preserve existing candidate evidence."""
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def error(a: np.ndarray, b: np.ndarray) -> float:
    """Return elementwise numeric difference, or infinity for incompatible data."""
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape:
        return float("inf")
    if a.dtype.kind in "OUS" or b.dtype.kind in "OUS":
        return 0.0 if np.array_equal(a, b) else float("inf")
    return float(np.max(abs(a.astype(float) - b.astype(float)), initial=0.0))


def load_banks(metadata: dict) -> dict:
    """Read pinned source arrays for the actual global schedule [m, rad, s]."""
    banks = {}
    for cell, source in metadata["banks"].items():
        path = absolute(source["path"])
        if digest(path) != source["sha256"]:
            raise ValueError("Prepared bank changed: " + cell)
        with np.load(path, allow_pickle=False) as data:
            banks[cell] = {key: data[key].copy() for key in data.files}
    return banks


def endpoint_delta(new: dict, old: dict, ni: int, oi: int) -> dict:
    """Compare parked robot, loaded UID and payload endpoint arrays [m, rad]."""
    values = {}
    constant = ("node_ids", "object_names", "ledger_uids", "assembled_uids", "end_loaded_uids")
    frame_fields = (
        "joints",
        "grips",
        "poses",
        "root_poses",
        "object_poses",
        "spindle_angles",
        "ledger_owner",
        "wire_points_1",
        "wire_points_2",
        "wire_lug_poses_1",
        "wire_lug_poses_2",
    )
    for key in constant:
        if key in new or key in old:
            values[key] = error(new.get(key, []), old.get(key, []))
    for key in frame_fields:
        if key in new or key in old:
            values[key] = error(new[key][ni], old[key][oi]) if key in new and key in old else float("inf")
    return dict(new_index=ni, old_index=oi, errors=values, matches=bool(max(values.values()) < 5e-7))


def integration_plan(prepared: Path, output: Path) -> None:
    """Assert the common schedule and classify exact-state transfer reuse [s]."""
    meta = json.loads(prepared.with_suffix(".json").read_text())
    old_meta = json.loads(OLD_PREPARED.with_suffix(".json").read_text())
    if digest(prepared) != meta["output_sha256"] or digest(OLD_PREPARED) != old_meta["output_sha256"]:
        raise ValueError("Prepared data digest mismatch")
    banks, old = load_banks(meta), load_banks(old_meta)
    timeline = assemble_timeline(banks)
    if timeline.frame != meta["frames"] or timeline.segments != meta["segments"]:
        raise ValueError("Prepared timeline differs from the shared fixed-height implementation")
    endpoint = {}
    for cell in "ABC":
        endpoint[cell] = {
            "initial": endpoint_delta(banks[cell], old[cell], 0, 0),
            "final": endpoint_delta(banks[cell], old[cell], -1, -1),
        }
    nc, oc = int(banks["C"]["preload_frame_count"]), int(old["C"]["preload_frame_count"])
    endpoint["C"]["loaded_park"] = endpoint_delta(banks["C"], old["C"], nc - 1, oc - 1)
    initial_clear = all(endpoint[c]["initial"]["matches"] for c in "ABC")
    ab_clear = (
        endpoint["A"]["final"]["matches"]
        and endpoint["B"]["initial"]["matches"]
        and endpoint["C"]["loaded_park"]["matches"]
    )
    bc_clear = all(endpoint[c]["final"]["matches"] for c in "AB") and endpoint["C"]["loaded_park"]["matches"]
    transfer = dict(entry=initial_clear, a_b=ab_clear, b_c=bc_clear, drawer_return=bc_clear)
    overlap = {}
    for purpose, count in (("drawer", 76), ("prefill", nc)):
        differences = {}
        for cell in "AC":
            for key in ("poses", "object_poses", "spindle_angles", "ledger_owner"):
                differences[cell + "/" + key] = error(banks[cell][key][:count], old[cell][key][:count])
        overlap[purpose] = dict(
            frames=count,
            errors=differences,
            matches=bool(max(differences.values()) < 5e-7 and (purpose == "drawer" or nc == oc)),
        )
    # The prepared mechanism tracks must reproduce the same normalized
    # transition samples even when the work banks have become shorter.
    mechanical = {}
    with np.load(prepared) as data, np.load(OLD_PREPARED) as original:
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
        old_segments = {row["label"]: row for row in old_meta["segments"] if row["kind"] == "transfer"}
        for row in meta["segments"]:
            if row["kind"] != "transfer":
                continue
            prior = old_segments[row["label"]]
            new_slice = slice(row["first_frame"] - 1, row["last_frame"])
            old_slice = slice(prior["first_frame"] - 1, prior["last_frame"])
            mechanical[row["label"]] = {key: error(data[key][new_slice], original[key][old_slice]) for key in keys}
    references = {
        scope: [{"path": "audit/" + name, "sha256": digest(ROOT / "audit" / name)} for name in names]
        for scope, names in REFERENCES.items()
    }
    write(
        output,
        dict(
            observed_at=datetime.now().astimezone().isoformat(),
            prepared=str(prepared),
            prepared_sha256=digest(prepared),
            source_static=meta["static_native"],
            timeline_sha256=digest(ROOT / "scripts/op030_fixed_height_timeline_v04.py"),
            endpoints=endpoint,
            transfer_endpoint_reuse=transfer,
            mechanical_track_errors=mechanical,
            overlaps=overlap,
            references=references,
            required_new_scope=[
                "Changed prefill/drawer simultaneous native poses",
                "New A/B/C motion versus fixed background outside each checked mesh context",
                "Frozen downstream robot/background signatures in final native",
            ],
            physical_scope="Auxiliary finite-frame geometry only; no force or physical-validity verdict",
            formal_physical_validity_verdict=None,
        ),
    )


def native_roots(scene, prepared: dict, static: dict) -> tuple[set, set]:
    """Collect explicitly animated root families, including driven mechanisms."""
    data = np.load(absolute(prepared["output"]))
    moving = {str(name) for name in data["object_names"]} | {str(name) for name in data["stopper_names"]}
    moving.update(("JB_OP020_UID001", "source_0292", static["wire_supply"]["drawer"]))
    moving.update(row["uid"] for row in static["wires"])
    for cell in "ABC":
        aliases = static["layout"]["cells"]["OP030" + cell]["source_names"]
        moving.update(aliases[f"source_{int(node):04d}"] for node in data["robot_nodes_" + cell])
    height = json.loads(scene["split_fixed_height_v04"])
    for record in height["positioners"].values():
        moving.update(record[key] for key in ("fixed", "carriage"))
    moving.update(static["entry_slide"][key] for key in ("fixed", "carriage"))
    carrier = static.get("retention", {}).get("carrier")
    if carrier:
        moving.add(carrier)
    data.close()
    c_roots = set(static["layout"]["cells"]["OP030C"]["source_names"].values())
    c_roots.update(name for name in moving if name.startswith("OP030C_feeder_"))
    return moving, c_roots


def native_export(args) -> None:
    """Read the final native at actual simultaneous frames, without modifying it [m, s]."""
    import bpy

    metadata = json.loads(args.prepared.with_suffix(".json").read_text())
    if digest(args.prepared) != metadata["output_sha256"]:
        raise ValueError("Prepared data changed")
    static = json.loads(absolute(metadata["static_native"]["manifest"]).read_text())
    bpy.ops.wm.open_mainfile(filepath=str(args.native))
    scene = bpy.context.scene
    moving_roots, c_roots = native_roots(scene, metadata, static)
    scene.frame_set(1)

    def ancestry(obj):
        while obj:
            yield obj.name
            obj = obj.parent

    candidates = sorted(
        [obj for obj in scene.objects if obj.type in {"MESH", "CURVE"} and not obj.hide_render],
        key=lambda obj: obj.name,
    )
    families = [set(ancestry(obj)) for obj in candidates]
    if args.window == "background":
        selected = np.array([not moving_roots.intersection(family) for family in families])
        unknown = [
            obj.name
            for obj, use in zip(candidates, selected, strict=True)
            if use and any(bpy.data.objects[name].animation_data for name in ancestry(obj))
        ]
        if unknown:
            raise ValueError("Background contains unexplained animation data: " + str(unknown[:20]))
        frame_ids, active = np.array([1]), np.zeros(len(candidates), dtype=bool)
    else:
        purpose = "prefill_before_arrival" if args.window == "prefill" else "present_10_wires_while_A_works"
        interval = next(row for row in metadata["parallel_operations"] if row["purpose"] == purpose)
        frame_ids = np.arange(interval["first_frame"], interval["last_frame"] + 1)
        roots = (
            c_roots
            if args.window == "prefill"
            else {static["wire_supply"]["drawer"], *(row["uid"] for row in static["wires"])}
        )
        active = np.array([bool(roots.intersection(family)) for family in families])
        selected = active.copy()
        boxes = np.array([obj.bound_box for obj in candidates])

        def bounds():
            matrices = np.array([np.asarray(obj.matrix_world) for obj in candidates])
            points = np.einsum("nij,nkj->nki", matrices[:, :3, :3], boxes) + matrices[:, None, :3, 3]
            return np.stack((points.min(1), points.max(1)), axis=1)

        sweep = np.array([[np.inf] * 3, [-np.inf] * 3])
        for frame in frame_ids:
            scene.frame_set(int(frame))
            current = bounds()[active]
            sweep[0] = np.minimum(sweep[0], current[:, 0].min(0))
            sweep[1] = np.maximum(sweep[1], current[:, 1].max(0))
        for frame in frame_ids:
            scene.frame_set(int(frame))
            current = bounds()
            selected |= np.all(
                np.minimum(current[:, 1], sweep[1] + 0.025) >= np.maximum(current[:, 0], sweep[0] - 0.025), axis=1
            )
    selected_objects = [obj for obj, use in zip(candidates, selected, strict=True) if use]
    scene.frame_set(int(frame_ids[0]))
    graph = bpy.context.evaluated_depsgraph_get()
    vertices, faces, vo, mesh_face_offsets = [], [], [0], [0]
    for obj in selected_objects:
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        points = np.array([v.co[:] for v in mesh.vertices])
        if args.window == "background":
            world = np.asarray(obj.matrix_world)
            points = points @ world[:3, :3].T + world[:3, 3]
        vertices.extend(points)
        faces.extend([tri.vertices[:] for tri in mesh.loop_triangles])
        vo.append(len(vertices))
        mesh_face_offsets.append(len(faces))
        evaluated.to_mesh_clear()
    transforms = []
    for frame in frame_ids:
        scene.frame_set(int(frame))
        transforms.append([np.asarray(obj.matrix_world).copy() for obj in selected_objects])
    arrays = dict(
        names=[obj.name for obj in selected_objects],
        vertices=np.array(vertices),
        faces=np.array(faces),
        vertex_offsets=vo,
        face_offsets=mesh_face_offsets,
    )
    signatures = None
    if args.window == "background":
        # A fixed-pose audit can only be inherited when the evaluated geometry
        # and world placement match the pinned source, including robot parks.
        source = absolute(metadata["static_native"]["path"])
        if digest(source) != metadata["static_native"]["sha256"]:
            raise ValueError("Pinned static source changed")
        bpy.ops.wm.open_mainfile(filepath=str(source))
        bpy.context.scene.frame_set(1)
        original_graph = bpy.context.evaluated_depsgraph_get()
        differences, maximum = [], 0.0
        for index, name in enumerate(arrays["names"]):
            obj = bpy.data.objects.get(name)
            if obj is None:
                differences.append(dict(name=name, reason="missing_in_pinned_static"))
                continue
            evaluated = obj.evaluated_get(original_graph)
            mesh = evaluated.to_mesh()
            mesh.calc_loop_triangles()
            points = np.array([v.co[:] for v in mesh.vertices])
            triangles = np.array([tri.vertices[:] for tri in mesh.loop_triangles])
            world = np.asarray(obj.matrix_world)
            points = points @ world[:3, :3].T + world[:3, 3]
            delta = error(points, arrays["vertices"][vo[index] : vo[index + 1]])
            topology = np.array_equal(
                triangles, arrays["faces"][mesh_face_offsets[index] : mesh_face_offsets[index + 1]]
            )
            maximum = max(maximum, delta)
            if delta > 5e-6 or not topology:
                differences.append(dict(name=name, maximum_world_vertex_error_m=delta, topology_equal=topology))
            evaluated.to_mesh_clear()
        signatures = dict(
            source=str(source),
            source_sha256=digest(source),
            compared_meshes=len(arrays["names"]),
            maximum_world_vertex_error_m=maximum,
            differences=differences,
            fixed_background_reuse=not differences,
        )
    if args.window != "background":
        arrays.update(
            payload=active[selected],
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
            prepared_sha256=digest(args.prepared),
            output_sha256=digest(args.data),
            window=args.window,
            global_frames=frame_ids.tolist(),
            meshes=len(arrays["names"]),
            fixed_source_comparison=signatures,
            explicit_moving_root_names=sorted(moving_roots),
            moving_meshes=np.asarray(arrays["names"])[active[selected]].tolist(),
            scope="Actual final-native frame matrices. Station-internal pairs remain in station audits; "
            "all concurrent external geometry considered. No formal physical verdict.",
            formal_physical_validity_verdict=None,
        ),
    )
    print("V05_INTEGRATION_EXPORT", args.window, len(frame_ids), len(arrays["names"]), flush=True)


def main() -> None:
    """Run one explicit read-only integration preparation or native overlap check."""
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("plan", "export", "check"))
    parser.add_argument("--prepared", type=Path, default=ROOT / "data/op030_split_animation_v05.npz")
    parser.add_argument("--native", type=Path)
    parser.add_argument("--window", choices=("prefill", "drawer", "background"), default="prefill")
    parser.add_argument("--prefix", default="op030_v05_integration")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:])
    args.data = ROOT / "analysis" / (args.prefix + "_" + args.window + "_meshes.npz")
    args.metadata = ROOT / "audit" / (args.prefix + "_" + args.window + "_export.json")
    output = (
        ROOT / "audit" / (args.prefix + "_" + ("plan" if args.mode == "plan" else args.window + "_check") + ".json")
    )
    if args.mode == "plan":
        integration_plan(args.prepared, output)
    elif args.mode == "export":
        if args.native is None:
            raise ValueError("An explicit final native is required")
        native_export(args)
    elif args.window == "background":
        raise ValueError("Use the station-context delta checker for the exported static background")
    else:
        if output.exists():
            raise FileExistsError(output)
        check(args.data, args.metadata, output)


if __name__ == "__main__":
    main()
