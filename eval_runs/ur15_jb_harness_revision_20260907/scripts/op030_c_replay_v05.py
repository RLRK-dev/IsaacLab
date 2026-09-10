# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Assemble the screened C v05 stage clock and direct refill paths [m, rad, s]."""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_c_refill_v05 import refill_phases
from op030_definition import ROOT
from op030_split_c_v04 import digest, load
from op030_split_c_v05 import BANK, CANDIDATE, CANDIDATE_REPORT, combined_row, drive_phases, source_tracks
from op030_split_c_v05_check import Context
from replay_op030_motion import path_sample, path_timing

AUDIT = ROOT / "audit/op030_split_c_motion_v05.json"
STAGES = ROOT / "audit/op030_c_stage_coordination_v05.npz"
REFILL = ROOT / "audit/op030_c_refill_raise_v05.json"


def aligned_pairs(first: list[int], last: list[int]) -> np.ndarray:
    """Finish original stopped arm tracks together, without skipping samples [s]."""
    length = max(b - a for a, b in zip(first, last, strict=True))
    return np.column_stack(
        [np.clip(np.arange(length + 1) - (length - (b - a)), 0, b - a) + a for a, b in zip(first, last, strict=True)]
    )


def prepare() -> None:
    """Save one complete finite-ownership 30 Hz candidate and its construction audit [s]."""
    if BANK.exists() or AUDIT.exists():
        raise FileExistsError(BANK)
    data, metadata, tracks = source_tracks()
    stages, raises = load(STAGES), load(REFILL.with_suffix(".npz"))
    routes = json.loads(REFILL.read_text())
    stage_reports = json.loads(STAGES.with_suffix(".json").read_text())
    context = Context(data["object_names"])
    inputs = [
        Path(__file__),
        ROOT / "scripts/op030_split_c_v05.py",
        CANDIDATE,
        CANDIDATE_REPORT,
        STAGES,
        STAGES.with_suffix(".json"),
        REFILL,
        REFILL.with_suffix(".npz"),
        context.mesh_file,
        context.mesh_file.with_suffix(".json"),
        context.outside_path,
        context.background_path,
    ]
    hashes = {str(path): digest(path) for path in inputs}
    rows, events, failures, seams = [], [], [], []

    def append(label, new_rows, kind):
        if rows:
            delta = float(abs(rows[-1]["joints"] - new_rows[0]["joints"]).max())
            seams.append(dict(label=label, maximum_joint_delta_rad=delta))
            if delta > 1e-6:
                raise ValueError(f"Disconnected stopped branch: {label}: {delta}")
            new_rows = new_rows[1:]
        first = max(0, len(rows) - 1)
        rows.extend(new_rows)
        events.append(
            dict(
                label=label,
                kind=kind,
                start_frame=first,
                stop_frame=len(rows) - 1,
                start_s=first / 30,
                stop_s=(len(rows) - 1) / 30,
            )
        )
        print("C_V05_ASSEMBLE", label, len(rows), flush=True)

    def row_at(pair, label, q=None, motion_pair=None):
        row = combined_row(data, tracks, *pair)
        row["control_local_indices"] = np.asarray(pair, dtype=int)
        row["motion_local_indices"] = np.asarray(pair if motion_pair is None else motion_pair, dtype=int)
        row["labels"] = label
        if q is not None:
            hits, actual = context.query(row, q)
            row.update({key: actual[key] for key in ("poses", "tools", "object_poses")})
            row["joints"] = q.copy()
            row["free_joint_motion"] = np.asarray([True, True])
            for key in ("source_frame_indices", "source_sample_indices"):
                row[key] = np.array([-1, -1])
            if hits:
                failures.append(dict(stage=label, joints=q.tolist(), pairs=hits))
        return row

    # Keep the already reviewed 385-frame prefill exactly, including its six-frame arm offset.
    prefix_count = int(data["preload_frame_count"])
    begin = [drive_phases(tracks, 2)[arm][0]["start_frame"] for arm in (0, 1)]
    prefix = [row_at([min(index, end) for end in begin], str(data["labels"][index])) for index in range(prefix_count)]
    for key in ("joints", "poses", "tools", "object_poses", "ledger_owner", "spindle_angles"):
        if not np.array_equal(np.asarray([row[key] for row in prefix]), data[key][:prefix_count]):
            raise ValueError("Prefill identity changed: " + key)
    append("両工具をワーク到着前に装填", prefix, "preload")

    for number in (2, 1):
        drive, refill = drive_phases(tracks, number), refill_phases(tracks, number)
        approach = f"H{number}_approach_" + ("aligned" if number == 2 else "arm1_first")
        for key, label in (
            (approach, f"H03-{number}／端子へ進入"),
            (f"H{number}_spin_aligned", f"H03-{number}／大小のねじを同時に締付"),
            (f"H{number}_withdraw80_aligned", f"H03-{number}／両工具を同時に80 mm軸抜き"),
        ):
            report = next(item for item in stage_reports if item["array_key"] == key)
            if not report["passed"]:
                raise ValueError("Rejected stage: " + key)
            append(label, [row_at(pair, label) for pair in stages[key]], key)

        route = next(item for item in routes if item["number"] == number)
        if not route["passed"]:
            raise ValueError("No screened refill for wire " + str(number))
        rise = raises[route["raise_pairs_key"]]
        raised_rows = []
        for index, pair in enumerate(rise):
            # Both outputs are empty: index them during the required M6-only extra rise.
            reset = [p[5]["start_frame"] + min(index, p[5]["stop_frame"] - p[5]["start_frame"]) for p in drive]
            q = combined_row(data, tracks, *pair)["joints"]
            row = row_at(reset, f"H03-{number}／M6を160 mm上げながら空ソケットを復帰", q, pair)
            row["free_joint_motion"] = np.array([False, False])
            raised_rows.append(row)
        append(f"H03-{number}／M6追加上昇・両ソケット復帰", raised_rows, "M6_raise_and_index")

        q_current = rows[-1]["joints"].copy()
        gate_start = [p[0]["start_frame"] for p in refill]
        gate_stop = [p[2]["stop_frame"] for p in refill]
        gate_clock = 0
        for leg in route["routes"]:
            arm = leg["arm"]
            path = np.asarray(leg["path"])
            if abs(q_current[arm] - path[0]).max() > 1e-6:
                raise ValueError("The selected refill path does not start at the stopped q")
            knots = path_timing(path, 1.2, 2.0)
            count = int(np.ceil(30 * knots[-1]))
            label = f"H03-{number}／{'M6' if arm == 0 else 'M14'}を供給器へ直行・自動切出し"
            free_rows = []
            for index in range(count + 1):
                pair = [min(a + gate_clock + index, b) for a, b in zip(gate_start, gate_stop, strict=True)]
                q = q_current.copy()
                q[arm] = path_sample(path, knots, index / count)
                row = row_at(pair, label, q, [-1, -1])
                row["free_joint_motion"] = np.asarray([arm == 0, arm == 1])
                free_rows.append(row)
            append(label, free_rows, f"direct_refill_arm{arm}")
            gate_clock += count
            q_current[arm] = path[-1]
        if gate_clock < max(b - a for a, b in zip(gate_start, gate_stop, strict=True)):
            raise ValueError("The queue has not stopped before pickup")

        above = route["goal_local"]
        last = [p[-1]["stop_frame"] for p in refill]
        label = f"H03-{number}／両工具へ同じ次部品を装填して待機"
        append(label, [row_at(pair, label) for pair in aligned_pairs(above, last)], "paired_pickup")

    keys = (
        "joints",
        "poses",
        "tools",
        "spindle_angles",
        "free_joint_motion",
        "local_author_times",
        "source_frame_indices",
        "source_sample_indices",
        "source_author_times",
        "object_poses",
        "ledger_owner",
        "labels",
        "motion_local_indices",
        "control_local_indices",
    )
    arrays = {key: np.asarray([row[key] for row in rows]) for key in keys}
    count = len(rows)
    times = np.arange(count) / 30.0
    arrays.update(
        times=times,
        author_times=times.copy(),
        frames=np.arange(count) + 1,
        node_ids=data["node_ids"],
        grips=np.zeros((count, 2)),
        errors=np.zeros((count, 2, 2)),
        clips=np.zeros((count, 2, 2)),
        object_names=data["object_names"],
        ledger_uids=data["ledger_uids"],
        assembled_uids=data["assembled_uids"],
        end_loaded_uids=data["end_loaded_uids"],
        preload_frame_count=np.array(prefix_count),
        preload_author_time_s=np.array((prefix_count - 1) / 30),
    )
    velocity = np.gradient(arrays["joints"], times, axis=0, edge_order=2)
    acceleration = np.gradient(velocity, times, axis=0, edge_order=2)
    peak_v, peak_a = float(abs(velocity).max()), float(abs(acceleration).max())
    if peak_v > 1.2 or peak_a > 2.0:
        raise ValueError(f"Stopped source/direct-path timing exceeds existing caps: {peak_v}, {peak_a}")
    if not np.array_equal(arrays["ledger_owner"][-1], data["ledger_owner"][-1]):
        raise ValueError("Final finite UID ownership changed")
    for key in ("joints", "poses", "tools", "object_poses", "spindle_angles"):
        if not np.allclose(arrays[key][-1], data[key][-1], atol=1e-7, rtol=0):
            raise ValueError("Final loaded waiting pose changed: " + key)
    if hashes != {str(path): digest(path) for path in inputs}:
        raise ValueError("An input changed while constructing the bank")
    np.savez_compressed(BANK, **arrays)
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        output=str(BANK),
        output_sha256=digest(BANK),
        factory="op030_split_c_v05:build_sequence",
        source_inputs_sha256=hashes,
        frames=count,
        duration_s=float(times[-1]),
        preload_frame_count=prefix_count,
        preload_author_time_s=(prefix_count - 1) / 30,
        work_duration_s=float(times[-1] - (prefix_count - 1) / 30),
        events=events,
        seams=seams,
        peak_velocity_rad_s=peak_v,
        peak_acceleration_rad_s2=peak_a,
        caps=[1.2, 2.0],
        simultaneous_fastening=True,
        geometry_modified=False,
        assembled_uids=arrays["assembled_uids"].tolist(),
        end_loaded_uids=arrays["end_loaded_uids"].tolist(),
        final_owner_counts={str(owner): int(np.sum(arrays["ledger_owner"][-1] == owner)) for owner in (0, 1, 2, 3)},
        modified_frame_checks=len(failures),
        construction_collision_frames=failures,
        geometry_checked=False,
        source_candidate_duration_s=metadata["duration_s"],
        scope=(
            "Selected saved approaches and mandatory withdrawal, plus screened direct refill; "
            "final saved-state check pending."
        ),
    )
    AUDIT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("C_V05_BANK_COMPLETE", count, float(times[-1]), peak_v, peak_a, len(failures), flush=True)


if __name__ == "__main__":
    prepare()
