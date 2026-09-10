# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Join staggered B motion to retained A/C motion on a fixed-height pallet [m, s]."""

import argparse
import hashlib
import importlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import LIFT, ROOT, pose, product_frame
from op030_fixed_height_timeline_v04 import OFFSETS, assemble_timeline, bank_sparse_track, bank_track
from op030_split_wire_motion import WirePlacementConfig

FPS = 30
RETAINED_BANK_SHA256 = {
    "A": "e56b610e5ee4642b16c03f7fb321936e3d1d11183218fe3fd0dbd3851dcc6c96",
    "C": "238c6b233871f25c0e95113b0d4d92124a569218ab8a40926773637e1ad96e38",
}


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def portable_path(path):
    """Keep rebuild references relative to the delivered artifact directory."""
    resolved = Path(path).resolve()
    return str(resolved.relative_to(ROOT)) if resolved.is_relative_to(ROOT) else str(resolved)


def shifted(matrices, y):
    result = np.asarray(matrices).copy()
    result[..., 1, 3] += y
    return result


def load_bank(path):
    with np.load(path, allow_pickle=False) as saved:
        data = {key: saved[key].copy() for key in saved.files}
    required = {"times", "author_times", "joints", "grips", "poses", "node_ids"}
    if not required.issubset(data):
        raise ValueError(f"Motion bank fields missing: {required - set(data)}")
    if not np.allclose(data["times"], np.arange(len(data["times"])) / FPS, atol=1e-8):
        raise ValueError("The bank must use exact native 30 Hz sampling")
    return data


def station_span(timeline, name):
    row = timeline.banks[name]
    return slice(row["first_frame"] - 1, row["last_frame"])


def fixed_track(first, values, span, count):
    result = np.repeat(np.asarray(first)[None], count, axis=0)
    result[span] = values
    result[span.stop :] = values[-1]
    return result


def camera_ranges(timeline, banks, station_labels, work_side):
    """Show supply pickup and assembly contacts within the complete timeline."""
    cameras = ["split_overall"] * timeline.frame
    for segment in timeline.segments:
        if segment["label"].startswith("OP020"):
            cameras[segment["first_frame"] - 1 : segment["last_frame"]] = ["split_entry"] * (
                segment["last_frame"] - segment["first_frame"] + 1
            )
    supply_events = (
        "切出しゲート",
        "単列供給",
        "次部品を切出して",
        "取得座と同軸",
        "ソケットで先頭部品",
        "同じ部品を取得座から",
    )
    assembly_events = (
        "取付穴の位置合わせ",
        "支持面へ着座",
        "ボルト先端を取付耳",
        "耳の貫通穴",
        "スタッド先端と同軸",
        "低速ねじ進行",
        "保持を解除して軸方向",
        "J1ねじ先端",
        "J1端子を",
        "T端子を",
        "両端の受けに支持",
        "仮保持クリップ",
        "仮保持パッド",
    )
    for station, labels in station_labels.items():
        # Only the C work chunk changes the primary shot. Its earlier prefill
        # is recorded independently and remains visible in the wide view.
        mapped = [
            (local, chunk.global_start + local - chunk.local_start)
            for chunk in timeline.chunks[station]
            if chunk.purpose == "work"
            for local in range(chunk.local_start, chunk.local_stop)
        ]
        for local, global_frame in mapped:
            label = labels[local]
            selected = "split_" + station
            if station in ("A", "B") and not work_side[station][local]:
                selected += "_stock"
            author = banks[station]["author_times"][local]
            if station == "A" and 4.5 <= author <= 6.5:
                selected = "support_supply"
            elif station == "B" and author <= 1.0:
                selected = "wire_supply"
            elif station in ("A", "C") and any(event in label for event in supply_events):
                selected = (
                    "split_A_feeder" if station == "A" else "split_C_" + ("M14" if "M14" in label else "M6") + "_feeder"
                )
            elif any(event in label for event in assembly_events):
                selected = "split_" + station + "_joint"
            if station == "A" and " ＋ " in label and "右フィンガ" in label:
                selected = "split_A_parallel"
            if "同時" in label and "鉛直上昇" in label:
                selected = "split_" + station
            if station == "A" and any(
                event in label for event in ("／2本締結完了", "／左右同時に鉛直上昇", "／上昇完了後")
            ):
                selected = "split_A_bimanual"
            cameras[global_frame] = selected
    for chunk in timeline.chunks["C"]:
        if chunk.purpose == "prefill_before_arrival":
            cameras[chunk.global_slice] = ["split_C"] * chunk.count
    result, start = [], 0
    for index in range(1, len(cameras) + 1):
        if index == len(cameras) or cameras[index] != cameras[start]:
            result.append(dict(first_frame=start + 1, last_frame=index, camera=cameras[start]))
            start = index
    return result


def factory(name, *args):
    module, function = name.split(":", 1)
    return getattr(importlib.import_module(module), function)(*args)


def recorded_labels(bank, station):
    """Describe C's idle arms from their stopped source clocks and UID owners."""
    labels = bank["labels"].tolist()
    if station != "C" or "local_author_times" not in bank:
        return labels
    times = bank["local_author_times"]
    # A stopped source clock across both neighboring native samples is an
    # actual wait, unlike a tool pose held during an active screw rotation.
    idle = np.zeros_like(times, dtype=bool)
    idle[1:-1] = (np.abs(times[1:-1] - times[:-2]) < 1e-10) & (np.abs(times[2:] - times[1:-1]) < 1e-10)
    for frame, label in enumerate(labels):
        arms = label.split(" | ")
        if len(arms) != 2:
            continue
        for arm, size in enumerate(("M6", "M14")):
            if idle[frame, arm]:
                loaded = np.any(bank["ledger_owner"][frame] == arm + 1)
                arms[arm] = size + ("／装填済み待機" if loaded else "／補充待機")
        labels[frame] = " | ".join(arms)
    return labels


def canonical_shape(sequence, number, parameter):
    bend = sequence.bends[number]
    if parameter <= 1.0:
        return bend.sample(float(parameter), np.zeros(3), np.eye(3))
    root = pose(location=-bend.final_center)
    return sequence._shape(number, {"mode": "insert", "root": root, "t_raise": (parameter - 1.0) * 0.040})


def wire_record(sequence, number, state):
    uid = sequence.active_uids[number]
    record = state["wires"][uid]
    control = record["control"]
    if control["mode"] == "bend":
        root = pose(control["rotation"], control["center"])
        parameter = float(control["progress"])
    else:
        root = control["root"] @ pose(location=sequence.bends[number].final_center)
        parameter = 1.0 + float(control["t_raise"]) / 0.040
    return root, parameter, record["shape"]


def extend_c_wire_track(number, bank, span, product, roots, parameters, lugs):
    """Apply a checked C wire-support motion when explicitly present [m]."""
    fields = [f"wire_{name}_{number}" for name in ("control_root", "parameter", "lug_poses")]
    if not any(name in bank for name in fields):
        return
    if not all(name in bank for name in fields):
        raise ValueError("C wire support motion needs all rigid/deformation tracks")
    c_roots = shifted(bank[fields[0]], OFFSETS["C"])
    c_parameters = bank[fields[1]]
    c_lugs = shifted(bank[fields[2]], OFFSETS["C"])
    if (
        not np.allclose(c_roots[0], roots[span.start], atol=5e-6)
        or abs(c_parameters[0] - parameters[span.start]) > 1e-8
    ):
        raise ValueError("C starts with a different wire from the arriving B product")
    if not np.allclose(c_roots[-1], c_roots[0], atol=5e-6) or abs(c_parameters[-1] - c_parameters[0]) > 1e-8:
        raise ValueError("Temporary C support must return the wire to its defined final shape")
    roots[span], parameters[span] = c_roots, c_parameters
    work = shifted(product_frame(lift=LIFT), OFFSETS["C"])
    movement = product @ np.linalg.inv(work)
    roots[span.stop :] = movement[span.stop :] @ c_roots[-1]
    parameters[span.stop :] = c_parameters[-1]
    for index, track in enumerate(lugs):
        if not np.allclose(c_lugs[0, index], track[span.start], atol=5e-6):
            raise ValueError("C starts with a different physical cable terminal")
        track[span] = c_lugs[:, index]
        track[span.stop :] = movement[span.stop :] @ c_lugs[-1, index]


def stagger_delta(stagger: dict) -> np.ndarray:
    """Validate the B-only layout and return its rigid world transform [m]."""
    delta = np.asarray(stagger["robot_supply_delta_world"])
    if not np.allclose(delta[:3, :3], np.diag([-1, -1, 1])) or not np.allclose(delta[:3, 3], [0, 1.2, 0]):
        raise ValueError("The B-only staggered world transform differs from the recorded layout")
    if not np.allclose(stagger["robot_base_baseline_m"], [0.9, -1.7, 0]):
        raise ValueError("The B bank must use the opposite-side baseline before the one Y offset")
    return delta


def check_retained_banks(paths: dict[str, Path]) -> None:
    """Require the completed v05 A/C trajectories to remain byte-identical."""
    for station, expected in RETAINED_BANK_SHA256.items():
        if digest(paths[station]) != expected:
            raise ValueError("An A/C motion bank changed during the B-only relocation: " + station)


def check_transport(product: np.ndarray, pallet: np.ndarray) -> None:
    """Require fixed product/pallet orientations and transport heights [m]."""
    if not np.allclose(product[:, :3, :3], np.diag([-1, -1, 1])) or not np.allclose(pallet[:, :3, :3], np.eye(3)):
        raise ValueError("Staggering the robot must not rotate the product or pallet")
    if not np.allclose(product[:, 2, 3], 0.8845) or not np.allclose(pallet[:, 2, 3], 0.789):
        raise ValueError("The product and pallet transport heights must remain fixed")


def main():
    parser = argparse.ArgumentParser()
    for name in ("a", "b", "c"):
        parser.add_argument("--" + name + "_motion", type=Path, required=True)
    parser.add_argument("--b_config", type=Path, required=True)
    parser.add_argument("--a_factory", default="op030_support_motion_v05:support_sequence_v05")
    parser.add_argument("--b_factory", default="op030_split_b_stagger_v06:build_sequence_final")
    parser.add_argument("--c_factory", required=True)
    parser.add_argument(
        "--static_manifest", type=Path, default=ROOT / "audit/op030_stagger_air_clearance_static_v06.json"
    )
    parser.add_argument("--output", type=Path, default=ROOT / "data/op030_split_animation_v06.npz")
    args = parser.parse_args()
    static = json.loads(args.static_manifest.read_text())
    static_path = Path(static["output"])
    if not static_path.is_absolute():
        static_path = ROOT / static_path
    if digest(static_path) != static["output_sha256"]:
        raise ValueError("Integrated static native differs from its recorded digest")
    stagger = static["stagger_v06"]
    delta = stagger_delta(stagger)
    bank_paths = {name: getattr(args, name.lower() + "_motion") for name in OFFSETS}
    check_retained_banks(bank_paths)
    banks = {name: load_bank(path) for name, path in bank_paths.items()}
    config = json.loads(args.b_config.read_text())
    config = config.get("config", config)
    sequences = {
        "A": factory(args.a_factory),
        "B": factory(args.b_factory, WirePlacementConfig(**config)),
        "C": factory(args.c_factory),
    }
    if config.get("transport_clips", True):
        raise ValueError("v06 must not contain cable holding mechanisms")
    for name, sequence in sequences.items():
        if abs(banks[name]["author_times"][-1] - sequence.time) > 1e-6:
            raise ValueError("The factory and checked motion bank duration differ: " + name)
    timeline = assemble_timeline(banks)
    count = timeline.frame
    frames = np.arange(1, count + 1)
    product = np.array(
        [
            product_frame(y=y, lift=height)
            for y, height in zip(timeline.values["y"], timeline.values["lift"], strict=True)
        ]
    )
    pallet = np.array(
        [
            pose(location=(0, y, 0.439 + height))
            for y, height in zip(timeline.values["y"], timeline.values["lift"], strict=True)
        ]
    )
    prepared = dict(frames=frames, product=product, pallet=pallet, drawer_B=np.asarray(timeline.values["drawer_B"]))
    drawer_original = np.repeat(np.eye(4)[None], count, axis=0)
    drawer_original[:, 0, 3] = prepared["drawer_B"]
    drawer_original[:, 1, 3] = OFFSETS["B"]
    prepared["drawer_B_world"] = delta[None] @ drawer_original
    check_transport(product, pallet)
    prepared["op020_carriage"] = np.array([pose(location=(0, -2.85, z)) for z in timeline.values["op020_carriage_z"]])
    prepared["entry_slide_x"] = np.asarray(timeline.values["entry_slide_x"])
    stopper_names, stopper_poses = [], []
    for name, hardware in static["transfer_hardware"]["cells"].items():
        fraction = np.asarray(timeline.values["stopper_" + name])
        up, down = np.asarray(hardware["stopper_up_world"]), np.asarray(hardware["stopper_down_world"])
        stopper_names.append(hardware["stopper"])
        stopper_poses.append(down[None] + fraction[:, None, None] * (up - down)[None])
    prepared["stopper_names"] = np.array(stopper_names)
    prepared["stopper_poses"] = np.stack(stopper_poses, axis=1)
    for name in OFFSETS:
        prepared["lift_" + name] = np.asarray(timeline.values[name])
        bank = banks[name]
        robot_frames, robot_poses = bank_sparse_track(bank["poses"], timeline.chunks[name], count)
        prepared["robot_frames_" + name] = robot_frames
        prepared["robot_poses_" + name] = shifted(robot_poses, OFFSETS[name])
        prepared["robot_nodes_" + name] = bank["node_ids"]
    object_tracks = {}
    station_labels = {}
    station_work_side = {}
    skipped = {"JB_OP020_UID001", "source_0292", "OP030_lift_carriage"}
    if static.get("retention", {}).get("clips"):
        raise ValueError("Cable holding mechanisms remain in the v06 static manifest")
    ledgers = {}
    for name in ("A", "C"):
        bank, seq, span = banks[name], sequences[name], station_span(timeline, name)
        logical_drivers = set(seq.driver_names.values())
        states = [seq.evaluate(float(time)) for time in bank["author_times"]]
        station_labels[name] = recorded_labels(bank, name) if "labels" in bank else [state["label"] for state in states]
        station_work_side[name] = [state["root"][1, 0] >= 0 for state in states]
        keys = sorted(set(states[0]["objects"]) - skipped - logical_drivers)
        if "object_names" in bank:
            actual = {str(key): index for index, key in enumerate(bank["object_names"])}
        else:
            actual = {}
        for key in keys:
            values = (
                bank["object_poses"][:, actual[key]]
                if key in actual
                else np.array([state["objects"][key] for state in states])
            )
            values = shifted(values, OFFSETS[name])
            object_tracks[key] = bank_track(values, timeline.chunks[name], count)
        spins = bank.get("spindle_angles", np.array([state["spindle_angles"] for state in states]))
        prepared["spindle_" + name] = bank_track(spins, timeline.chunks[name], count)
        required = {"assembled_uids", "end_loaded_uids", "ledger_owner", "ledger_uids"}
        if not required.issubset(bank):
            raise ValueError(f"Missing explicit product/tool/supply ownership for {name}: {required - set(bank)}")
        assembled = list(bank["assembled_uids"]) + (["OP030_T01_UID001", "OP030_T02_UID001"] if name == "A" else [])
        if set(bank["assembled_uids"]) & set(bank["end_loaded_uids"]):
            raise ValueError("A fastener cannot be installed and loaded in the tool simultaneously")
        prepared["ledger_uids_" + name] = bank["ledger_uids"]
        prepared["ledger_owner_" + name] = bank_track(bank["ledger_owner"], timeline.chunks[name], count)
        ledgers[name] = dict(
            assembled_uids=bank["assembled_uids"].tolist(),
            end_loaded_uids=bank["end_loaded_uids"].tolist(),
            end_counts={str(owner): int(np.sum(bank["ledger_owner"][-1] == owner)) for owner in (0, 1, 2, 3)},
        )
        work = shifted(product_frame(lift=LIFT), OFFSETS[name])
        movement = product @ np.linalg.inv(work)
        for key in assembled:
            final = object_tracks[key][span.stop - 1]
            object_tracks[key][span.stop :] = movement[span.stop :] @ final
    sequence, bank, span = sequences["B"], banks["B"], station_span(timeline, "B")
    states = [sequence.evaluate(float(time)) for time in bank["author_times"]]
    station_labels["B"] = [state["label"] for state in states]
    station_work_side["B"] = [bool(state["work_side"]) for state in states]
    if not np.allclose(np.array([state["root"][:2, 3] for state in states]), [0.9, -1.7]):
        raise ValueError("B motion retained an old base or added the global Y offset twice")
    c_span = station_span(timeline, "C")
    wire_metadata = []
    for number in (1, 2):
        records = [wire_record(sequence, number, state) for state in states]
        roots = shifted(np.array([record[0] for record in records]), OFFSETS["B"])
        parameters = np.array([record[1] for record in records])
        full_roots = fixed_track(roots[0], roots, span, count)
        full_roots[: span.start, 0, 3] -= prepared["drawer_B"][: span.start] - 0.340
        full_parameters = fixed_track(parameters[0], parameters, span, count)
        work = shifted(product_frame(lift=LIFT), OFFSETS["B"])
        movement = product @ np.linalg.inv(work)
        full_roots[span.stop :] = movement[span.stop :] @ roots[-1]
        lugs = []
        for end in ("J1", "T"):
            values = shifted(np.array([record[2].lug_frames[end] for record in records]), OFFSETS["B"])
            track = fixed_track(values[0], values, span, count)
            track[: span.start, 0, 3] -= prepared["drawer_B"][: span.start] - 0.340
            track[span.stop :] = movement[span.stop :] @ values[-1]
            lugs.append(track)
        c_chunk = timeline.chunks["C"][-1]
        c_wire_bank = {
            key: value[c_chunk.local_slice]
            for key, value in banks["C"].items()
            if key.startswith("wire_") and len(value) == len(banks["C"]["times"])
        }
        extend_c_wire_track(number, c_wire_bank, c_span, product, full_roots, full_parameters, lugs)
        unique = np.unique(full_parameters)
        vertices = np.array(
            [sequence.bends[number].tube_mesh(canonical_shape(sequence, number, parameter))[0] for parameter in unique],
            dtype=np.float32,
        )
        prepared[f"wire_{number}_root"] = full_roots
        prepared[f"wire_{number}_parameter"] = full_parameters
        prepared[f"wire_{number}_lugs"] = np.stack(lugs, axis=1)
        prepared[f"wire_{number}_shape_parameters"] = unique
        prepared[f"wire_{number}_shape_vertices"] = vertices
        wire_metadata.append(dict(number=number, uid=sequence.active_uids[number], deformation_keys=len(unique)))
    prepared["object_names"] = np.array(sorted(object_tracks))
    prepared["object_poses"] = np.stack([object_tracks[key] for key in prepared["object_names"]], axis=1)
    labels = [""] * count
    for segment in timeline.segments:
        labels[segment["first_frame"] - 1 : segment["last_frame"]] = [segment["label"]] * (
            segment["last_frame"] - segment["first_frame"] + 1
        )
    for name, values in station_labels.items():
        for chunk in timeline.chunks[name]:
            if chunk.purpose == "work":
                labels[chunk.global_slice] = values[chunk.local_slice]
    for chunk in timeline.chunks["C"]:
        if chunk.purpose == "prefill_before_arrival":
            for local in range(chunk.local_start, chunk.local_stop):
                frame = chunk.global_start + local - chunk.local_start
                labels[frame] = "C事前装填（A準備と並行）｜" + station_labels["C"][local]
    caption_phases, start = [], 0
    for index in range(1, count + 1):
        if index == count or labels[index] != labels[start]:
            caption_phases.append(
                dict(
                    first_frame=start + 1,
                    last_frame=index,
                    start_s=start / FPS,
                    stop_s=index / FPS,
                    label=labels[start],
                )
            )
            start = index
    np.savez_compressed(args.output, **prepared)
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        static_native=dict(
            path=portable_path(static_path),
            sha256=static["output_sha256"],
            manifest=portable_path(args.static_manifest),
            manifest_sha256=digest(args.static_manifest),
        ),
        banks={name: dict(path=portable_path(path), sha256=digest(path)) for name, path in bank_paths.items()},
        b_config=config,
        a_factory=args.a_factory,
        b_factory=args.b_factory,
        c_factory=args.c_factory,
        frames=count,
        duration_s=(count - 1) / FPS,
        fps=FPS,
        segments=timeline.segments,
        station_ranges=timeline.banks,
        bank_chunks={
            name: [
                dict(
                    global_start=chunk.global_start,
                    local_start=chunk.local_start,
                    local_stop=chunk.local_stop,
                    purpose=chunk.purpose,
                )
                for chunk in chunks
            ]
            for name, chunks in timeline.chunks.items()
        },
        parallel_operations=timeline.overlaps,
        staggered_layout=dict(
            robot_base_B_world_m=stagger["robot_base_world_m"],
            robot_supply_delta_world=stagger["robot_supply_delta_world"],
            drawer_world_direction=[-1, 0, 0],
            product_and_pallet_rotation_preserved=True,
            preserved_A_C_banks=True,
        ),
        fastener_ownership=ledgers,
        fixed_conveyor=dict(
            pallet_reference_z_m=float(pallet[0, 2, 3]),
            pallet_z_range_m=float(np.ptp(pallet[:, 2, 3])),
            product_reference_z_m=float(product[0, 2, 3]),
            workstation_pallet_lift=False,
            two_level_return_implemented=False,
        ),
        shots=camera_ranges(timeline, banks, station_labels, station_work_side),
        phases=caption_phases,
        wires=wire_metadata,
        objects=prepared["object_names"].tolist(),
        output=portable_path(args.output),
        output_sha256=digest(args.output),
        formal_physical_validity_verdict=None,
        scope=(
            "Same product/pallet/part identities; "
            "station-bank checks and full integrated-native checks recorded separately"
        ),
    )
    args.output.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("OP030_SPLIT_ANIMATION_PREPARED", count, [row["deformation_keys"] for row in wire_metadata], flush=True)


if __name__ == "__main__":
    main()
