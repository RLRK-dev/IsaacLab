# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""C v05 concurrent fastening and direct empty-tool refill [m, rad, s]."""

import json
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_split_c_v04 import BankSequence, digest, load

CANDIDATE = ROOT / "analysis/op030_c_parallel_candidate_v05.npz"
CANDIDATE_REPORT = ROOT / "audit/op030_c_parallel_candidate_v05.json"
BANK = ROOT / "data/op030_split_c_motion_v05.npz"


def source_tracks() -> tuple[dict, dict, list[dict]]:
    """Recover the complete original per-arm tracks from the finite same-start candidate [s]."""
    data, metadata = load(CANDIDATE), json.loads(CANDIDATE_REPORT.read_text())
    if digest(CANDIDATE) != metadata["output_sha256"]:
        raise ValueError("Parent's C comparison candidate changed")
    tracks = []
    for arm in (0, 1):
        count = metadata["local_phases"][arm][-1]["stop_frame"] + 1
        mapping = np.full(count, -1, dtype=int)
        for row in metadata["schedule"][arm]:
            mapping[row["local_start"] : row["local_stop"] + 1] = np.arange(row["start_frame"], row["stop_frame"] + 1)
        if np.any(mapping < 0):
            raise ValueError("Incomplete serial arm track")
        tracks.append(dict(mapping=mapping, phases=metadata["local_phases"][arm]))
    return data, metadata, tracks


def combined_row(data: dict, tracks: list[dict], first: int, second: int) -> dict:
    """Combine two original local samples with the same finite ownership and FK poses [m, rad]."""
    indices = [int(tracks[0]["mapping"][first]), int(tracks[1]["mapping"][second])]
    poses = data["poses"][indices[0]].copy()
    right_nodes = data["node_ids"] >= 1086
    poses[right_nodes] = data["poses"][indices[1], right_nodes]
    objects = data["object_poses"][indices[0]].copy()
    names = np.asarray(data["object_names"], dtype=str)
    right_objects = np.char.find(names, "M14") >= 0
    objects[right_objects] = data["object_poses"][indices[1], right_objects]
    ledger = data["ledger_owner"][indices[0]].copy()
    right_uids = np.char.find(np.asarray(data["ledger_uids"], dtype=str), "M14") >= 0
    ledger[right_uids] = data["ledger_owner"][indices[1], right_uids]
    labels = []
    for arm, index in ((0, first), (1, second)):
        phase = next((p for p in tracks[arm]["phases"] if index <= p["stop_frame"]), tracks[arm]["phases"][-1])
        labels.append(phase["label"])
    return dict(
        joints=np.asarray([data["joints"][index, arm] for arm, index in enumerate(indices)]),
        tools=np.asarray([data["tools"][index, arm] for arm, index in enumerate(indices)]),
        spindle_angles=np.asarray([data["spindle_angles"][index, arm] for arm, index in enumerate(indices)]),
        free_joint_motion=np.asarray([data["free_joint_motion"][index, arm] for arm, index in enumerate(indices)]),
        local_author_times=np.asarray([data["local_author_times"][index, arm] for arm, index in enumerate(indices)]),
        source_frame_indices=np.asarray(
            [data["source_frame_indices"][index, arm] for arm, index in enumerate(indices)]
        ),
        source_sample_indices=np.asarray(
            [data["source_sample_indices"][index, arm] for arm, index in enumerate(indices)]
        ),
        source_author_times=np.asarray([data["source_author_times"][index, arm] for arm, index in enumerate(indices)]),
        poses=poses,
        object_poses=objects,
        ledger_owner=ledger,
        ledger_uids=data["ledger_uids"],
        labels=" | ".join(labels),
    )


def drive_phases(tracks: list[dict], number: int) -> list[list[dict]]:
    """Return original approach/drive/withdraw/reset phase groups for one wire [s]."""
    return [[p for p in track["phases"] if p["label"].startswith(f"H03-{number}／")] for track in tracks]


def build_sequence() -> BankSequence:
    """Load the C v05 final 30 Hz bank for timeline integration [s]."""
    return BankSequence(Path(BANK))
