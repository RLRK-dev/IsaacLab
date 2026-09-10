# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Reschedule saved C tool paths with explicit concurrent ownership [m, rad, s].

The source trajectories remain candidates under the new simultaneous schedule
and fixed-height conveyor. A separate actual-mesh replay is required.
"""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import CY, LIFT, ROOT, lug_frame, pose, product_frame
from op030_fastener_operations_v04 import fastener_drive_append, fastener_ledger_at, fastener_pickup_append
from op030_split_fastening_motion import FixedFasteningSequence, _phase
from op030_split_top_entry import j1_lug_frame, top_entry_flange_to_tcp
from op030_split_top_entry_motion import top_entry_c_sequence
from solve_op030_motion import NODE_IDS, R, capture_robots
from split_tools_c_top_entry_replay import Replay

SOURCE = ROOT / "data/op030_split_c_motion_v03.npz"
SOURCE_SHA = "0282f498ad659d83fa6a640ac459b320439a9b8b39cf970749e7c8689b890bee"
BANK = ROOT / "data/op030_split_c_motion_v04.npz"
AUDIT = ROOT / "audit/op030_split_c_motion_v04.json"


def digest(path: Path) -> str:
    """Return the artifact SHA256 digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    """Read immutable numeric bank arrays."""
    with np.load(path, allow_pickle=False) as saved:
        return {key: saved[key].copy() for key in saved.files}


def arm_sequence(arm: int) -> tuple[FixedFasteningSequence, list[dict]]:
    """Build one arm's serial pickup/drive ledger with source phase mapping [s]."""
    seq = FixedFasteningSequence("C")
    seq.yaw = np.deg2rad(110.0)
    seq.straight_driver_sizes = {"M6", "M14"}
    seq.driver_calibrations = {0: top_entry_flange_to_tcp()}
    seq.holds[0] = (seq.driver_names[0], np.linalg.inv(seq.driver_calibrations[0]))
    seq.hands[0] = seq.objects[seq.driver_names[0]] @ np.linalg.inv(seq.driver_calibrations[0])
    size, end, thickness = ("M6", "J1", 0.0038) if arm == 0 else ("M14", "T", 0.0032)
    old_groups = (
        [(5, 11), (11, 17), (17, 18), (31, 39), (39, 45), (45, 46), (31, 39)]
        if arm == 0
        else [(18, 24), (24, 30), (30, 31), (46, 54), (54, 60), (60, 61), (46, 54)]
    )
    groups = []

    def add_group(kind, first, source_range):
        rows = seq.phases[first:]
        start, stop = source_range
        if len(rows) != stop - start:
            raise ValueError("Shared phase count differs from the saved source")
        for phase, old_index in zip(rows, range(start, stop), strict=True):
            phase["source_phase"] = old_index
        groups.append(dict(kind=kind, phase_start=first, phase_stop=len(seq.phases)))

    group = 0
    for number in (2, 1, None):
        first = len(seq.phases)
        pickup = fastener_pickup_append(
            seq, arm, size, label=f"{size}／UID{3 if number is None else 3 - number:03d}装填"
        )
        add_group("pickup", first, old_groups[group])
        group += 1
        if number is None:
            break
        frame = j1_lug_frame(number, "top_entry") if arm == 0 else lug_frame(number, "T")
        seat = product_frame(lift=LIFT) @ frame @ pose(location=(0, 0, thickness))
        first = len(seq.phases)
        fastener_drive_append(seq, pickup, seat, label=f"H03-{number}／{end}端子{size}上締め")
        add_group("drive", first, old_groups[group])
        group += 1
        first = len(seq.phases)
        park = pose(location=(-0.55, CY + (-0.72 if arm == 0 else 0.72), 1.30))
        _phase(seq, f"{size}／必須軸抜き完了後・補充への既存中継点", 4.0, arm, park, free=True)
        add_group("park", first, old_groups[group])
        group += 1
    return seq, groups


def add_boundaries(source: dict, old_sequence) -> list[dict]:
    """Evaluate only omitted stopped endpoints with the existing branch replay [s]."""
    replay = Replay(
        ROOT / "audit/split_tools_c_top_entry_connected.json",
        1.2,
        2.0,
        ROOT / "data/op030_split_c_top_entry_clip_v02_meshes.npz",
    )
    robots, rows = capture_robots(), []
    source["original_count"] = len(source["author_times"])
    for time in sorted({p[k] for p in old_sequence.phases for k in ("start", "stop")}):
        if np.min(abs(source["author_times"] - time)) < 1e-8:
            continue
        q, errors, free, target = replay.sample(time)
        captures = {577: target["root"], 578: target["root"]}
        tools = []
        for arm, side in enumerate(("left", "right")):
            robot, capture = robots[side]
            robot.base_pose = target["root"] @ R.yoke_base_pose(side)
            tools.append(robot.update(q[arm], 0.0).copy())
            captures.update(capture.poses)
        values = dict(
            author_times=time,
            joints=q,
            free_joint_motion=free,
            tools=np.array(tools),
            poses=np.array([captures[int(node)] for node in NODE_IDS]),
        )
        index = len(source["author_times"])
        for key, value in values.items():
            source[key] = np.concatenate([source[key], np.asarray(value)[None]], axis=0)
        rows.append(dict(sample_index=index, source_author_time_s=time, maximum_ik_residual=float(max(errors))))
    if max(row["maximum_ik_residual"] for row in rows) > 1e-5:
        raise ValueError("Saved continuous branch does not reproduce a stopped endpoint")
    return rows


def arm_track(arm: int, source: dict, old_sequence) -> tuple[FixedFasteningSequence, dict, list[dict], list[dict]]:
    """Copy exact source samples into one arm's new serial clock [s, rad]."""
    seq, groups = arm_sequence(arm)
    source_indices, authors, phase_rows, splices = [], [], [], []
    cursor = 0
    for phase in seq.phases:
        old = old_sequence.phases[phase["source_phase"]]
        first, last = [int(np.argmin(abs(source["author_times"] - old[key]))) for key in ("start", "stop")]
        if max(abs(source["author_times"][[first, last]] - [old["start"], old["stop"]])) > 1e-8:
            raise ValueError("Source phase endpoint is not a native frame")
        if abs((phase["stop"] - phase["start"]) - (old["stop"] - old["start"])) > 1e-8:
            raise ValueError("Shared operation duration changed")
        original = source["author_times"][: source["original_count"]]
        interior = np.flatnonzero((original > old["start"] + 1e-8) & (original < old["stop"] - 1e-8))
        indices = np.r_[first, interior, last]
        duration = len(indices) - 1
        local = phase["start"] + source["author_times"][indices] - old["start"]
        if source_indices:
            before = source_indices[-1]
            error = float(abs(source["joints"][before, arm] - source["joints"][first, arm]).max())
            splices.append(dict(arm=arm, source_before=int(before), source_after=first, joint_delta_rad=error))
            if error > 1e-6:
                raise ValueError(f"Saved IK branches do not join: {splices[-1]}")
            indices, local = indices[1:], local[1:]
        source_indices.extend(indices.tolist())
        authors.extend(local.tolist())
        phase_rows.append(
            dict(
                start_frame=cursor,
                stop_frame=cursor + duration,
                source_phase=phase["source_phase"],
                label=phase["label"],
                author_start=phase["start"],
                author_stop=phase["stop"],
            )
        )
        cursor += duration
    for group in groups:
        group["start_frame"] = phase_rows[group["phase_start"]]["start_frame"]
        group["stop_frame"] = phase_rows[group["phase_stop"] - 1]["stop_frame"]
    return seq, dict(source=np.array(source_indices), author=np.array(authors), phases=phase_rows), groups, splices


def schedule(groups: list[list[dict]]) -> tuple[list[list[dict]], int]:
    """Overlap refill only after the same arm's mandatory withdrawal [s]."""
    events = [[], []]

    def append(arm, first, last, start):
        local_first = groups[arm][first]["start_frame"]
        local_last = groups[arm][last]["stop_frame"]
        row = dict(
            start_frame=start,
            stop_frame=start + local_last - local_first,
            local_start=local_first,
            local_stop=local_last,
            action="+".join(group["kind"] for group in groups[arm][first : last + 1]),
        )
        events[arm].append(row)
        return row["stop_frame"]

    prefill = max(append(0, 0, 0, 0), append(1, 0, 0, 0))
    left_drive_1 = append(0, 1, 1, prefill)
    left_refill_2 = append(0, 2, 3, left_drive_1)
    right_drive_1 = append(1, 1, 1, left_drive_1)
    right_refill_2 = append(1, 2, 3, right_drive_1)
    left_drive_2 = append(0, 4, 4, max(right_drive_1, left_refill_2))
    append(0, 5, 6, left_drive_2)
    right_drive_2 = append(1, 4, 4, max(left_drive_2, right_refill_2))
    append(1, 5, 6, right_drive_2)
    return events, prefill


def prepare() -> None:
    """Create the concurrent candidate without changing source paths [m, rad, s]."""
    if BANK.exists() or AUDIT.exists():
        raise FileExistsError(BANK)
    if digest(SOURCE) != SOURCE_SHA:
        raise ValueError("The accepted C v03 bank changed")
    source, old_sequence = load(SOURCE), top_entry_c_sequence()
    boundaries = add_boundaries(source, old_sequence)
    records = [arm_track(arm, source, old_sequence) for arm in (0, 1)]
    seqs, tracks, groups, splices = zip(*records, strict=True)
    events, prefill = schedule(groups)
    count = max(row["stop_frame"] for side in events for row in side) + 1
    local_indices = np.zeros((count, 2), dtype=int)
    for arm in (0, 1):
        cursor, held = 0, 0
        for row in events[arm]:
            start, stop = row["start_frame"], row["stop_frame"]
            local_indices[cursor:start, arm] = held
            local_indices[start : stop + 1, arm] = np.arange(row["local_start"], row["local_stop"] + 1)
            cursor, held = stop + 1, row["local_stop"]
        local_indices[cursor:, arm] = held
    maps = np.column_stack([tracks[arm]["source"][local_indices[:, arm]] for arm in (0, 1)])
    authors = np.column_stack([tracks[arm]["author"][local_indices[:, arm]] for arm in (0, 1)])
    names = np.array(sorted(seqs[0].objects))
    uids = np.array(sorted(seqs[0].fastener_initial_owners))
    owner_index = {str(uid): index for index, uid in enumerate(uids)}
    object_index = {str(name): index for index, name in enumerate(names)}
    objects = np.zeros((count, len(names), 4, 4))
    ledger = np.zeros((count, len(uids)), dtype=np.int8)
    spins = np.zeros((count, 2))
    labels, target_errors, joint_splices = [], [], [row for side in splices for row in side]
    local_cache = [dict(), dict()]
    joints = np.stack([source["joints"][maps[:, arm], arm] for arm in (0, 1)], axis=1)
    tools = np.stack([source["tools"][maps[:, arm], arm] for arm in (0, 1)], axis=1)
    captures = source["poses"][maps[:, 0]].copy()
    right_nodes = source["node_ids"] >= 1086
    captures[:, right_nodes] = source["poses"][maps[:, 1]][:, right_nodes]
    free = np.column_stack([source["free_joint_motion"][maps[:, arm], arm] for arm in (0, 1)])
    for frame in range(count):
        row_labels = []
        for arm, size in ((0, "M6"), (1, "M14")):
            local = int(local_indices[frame, arm])
            if local not in local_cache[arm]:
                t = float(authors[frame, arm])
                state = seqs[arm].evaluate(t)
                ownership = fastener_ledger_at(seqs[arm], t)
                local_cache[arm][local] = (state, ownership)
            state, ownership = local_cache[arm][local]
            target_errors.append(
                float(
                    abs(
                        state["tools"][arm]
                        - old_sequence.evaluate(float(source["author_times"][maps[frame, arm]]))["tools"][arm]
                    ).max()
                )
            )
            spins[frame, arm] = state["spindle_angles"][arm]
            row_labels.append(state["label"])
            driver = seqs[arm].driver_names[arm]
            calibration = np.linalg.inv(seqs[arm].holds[arm][1])
            actual_driver = tools[frame, arm] @ calibration
            for name, matrix in state["objects"].items():
                if size not in name:
                    continue
                value = actual_driver if name == driver else matrix
                owner = ownership["owners"].get(name)
                if owner:
                    code = {"supply": 0, "tool": arm + 1, "installed": 3}[owner["owner"]]
                    ledger[frame, owner_index[name]] = code
                    if code == arm + 1:
                        value = actual_driver @ np.linalg.inv(state["objects"][driver]) @ matrix
                objects[frame, object_index[name]] = value
        labels.append(" | ".join(row_labels))
        if frame % 600 == 0:
            print("C_V04_RESCHEDULE", frame, count, flush=True)
    if max(target_errors) > 1e-7:
        raise ValueError(f"Shared operation targets changed: {max(target_errors)}")
    times = np.arange(count) / 30.0
    velocity = np.gradient(joints, times, axis=0, edge_order=2)
    acceleration = np.gradient(velocity, times, axis=0, edge_order=2)
    peak_v, peak_a = float(abs(velocity).max()), float(abs(acceleration).max())
    if peak_v > 1.2 or peak_a > 2.0:
        raise ValueError(f"Rescheduled native samples exceed existing caps: {peak_v}, {peak_a}")
    assembled = uids[ledger[-1] == 3]
    loaded = uids[np.isin(ledger[-1], [1, 2])]
    if len(assembled) != 4 or len(loaded) != 2 or not all(str(uid).endswith("003") for uid in loaded):
        raise ValueError("Final physical UID ledger differs from 2 installed + 1 loaded per size")
    arrays = dict(
        times=times,
        author_times=times,
        frames=np.arange(count) + 1,
        joints=joints,
        node_ids=source["node_ids"],
        poses=captures,
        tools=tools,
        grips=np.zeros((count, 2)),
        free_joint_motion=free,
        errors=np.zeros((count, 2, 2)),
        spindle_angles=spins,
        clips=np.zeros((count, 2, 2)),
        object_names=names,
        object_poses=objects,
        labels=np.array(labels),
        ledger_uids=uids,
        ledger_owner=ledger,
        assembled_uids=assembled,
        end_loaded_uids=loaded,
        preload_frame_count=np.array(prefill + 1),
        preload_author_time_s=np.array(prefill / 30),
        source_frame_indices=np.where(maps < source["original_count"], maps, -1),
        source_sample_indices=maps,
        source_author_times=source["author_times"][maps],
        local_author_times=authors,
    )
    np.savez_compressed(BANK, **arrays)
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        output=str(BANK),
        output_sha256=digest(BANK),
        factory="op030_split_c_v04:build_sequence",
        source=str(SOURCE),
        source_sha256=SOURCE_SHA,
        source_script_sha256={
            name: digest(ROOT / "scripts" / name)
            for name in ("op030_split_c_v04.py", "op030_fastener_operations_v04.py")
        },
        frames=count,
        duration_s=float(times[-1]),
        preload_frame_count=prefill + 1,
        preload_author_time_s=prefill / 30,
        work_duration_s=float(times[-1] - prefill / 30),
        schedule=events,
        local_phases=[track["phases"] for track in tracks],
        maximum_target_matrix_error=max(target_errors),
        source_splices=joint_splices,
        inserted_boundaries=boundaries,
        peak_velocity_rad_s=peak_v,
        peak_acceleration_rad_s2=peak_a,
        caps=[1.2, 2.0],
        assembled_uids=assembled.tolist(),
        end_loaded_uids=loaded.tolist(),
        final_owner_counts={str(owner): int(np.sum(ledger[-1] == owner)) for owner in (0, 1, 2, 3)},
        geometry_checked=False,
        scope="Exact source q samples, common operation poses and ownership; concurrent actual-mesh replay pending.",
    )
    AUDIT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print("C_V04_RESCHEDULE_COMPLETE", count, times[-1], prefill / 30, peak_v, peak_a, flush=True)


class BankSequence:
    """Expose the recorded native 30 Hz C states to the integrating timeline [s]."""

    driver_names = {0: "OP030C_driver_M6", 1: "OP030C_driver_M14"}
    driver_sizes = {0: "M6", 1: "M14"}

    def __init__(self, path: Path = BANK):
        self.data = load(path)
        self.time = float(self.data["times"][-1])
        self.objects = dict(zip(self.data["object_names"], self.data["object_poses"][0], strict=True))

    def evaluate(self, time: float) -> dict:
        """Return a recorded native-frame state; reject off-grid time [s]."""
        index = int(round(time * 30))
        if index < 0 or index >= len(self.data["times"]) or abs(time - self.data["times"][index]) > 1e-7:
            raise ValueError("Recorded C v04 evaluation requires a native 30 Hz time")
        d = self.data
        return dict(
            root=d["poses"][index, 0].copy(),
            tools=d["tools"][index].copy(),
            objects=dict(zip(d["object_names"], d["object_poses"][index], strict=True)),
            grips=d["grips"][index],
            free=d["free_joint_motion"][index],
            spindle_angles=d["spindle_angles"][index],
            label=str(d["labels"][index]),
            clips={},
        )


def build_sequence() -> BankSequence:
    """Load the C v04 recorded sequence for native-frame integration [s]."""
    return BankSequence()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    prepare()


if __name__ == "__main__":
    main()
