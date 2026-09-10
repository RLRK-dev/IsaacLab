# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Explicit top-entry C candidate, using original FK and finite fastener IDs."""

import hashlib
import json
from pathlib import Path

import numpy as np
from op030_definition import CY, LIFT, ROOT, lug_frame, pose, product_frame
from op030_split_fastening_motion import FixedFasteningSequence, _clip_frames, _clip_release, _phase, append_fastening
from op030_split_top_entry import j1_lug_frame, top_entry_flange_to_tcp

FINAL_MESH = ROOT / "data/op030_split_c_top_entry_clip_v02_meshes.npz"
FINAL_MESH_SHA256 = "5a7b87d2a1525a90ce05e89c99b832151c3ec893abba5ef734668202f17201b9"
FINAL_METADATA_SHA256 = "16de5b1d3a9676774844d4888e738d51fdbc1477c39cdff61aaabea27f5ed597"


def top_entry_c_sequence(mesh_file: Path | None = None, *, torso_yaw_degrees: float = 110.0) -> FixedFasteningSequence:
    """Rebuild a top-entry target candidate from actual clip calibration [m, s].

    This factory only defines targets. Continuous IK and actual mesh checks
    must accompany a rendered/replayed bank before it can be accepted.
    """
    path = mesh_file or FINAL_MESH
    if mesh_file is None:
        for actual, expected in ((path, FINAL_MESH_SHA256), (path.with_suffix(".json"), FINAL_METADATA_SHA256)):
            if hashlib.sha256(actual.read_bytes()).hexdigest() != expected:
                raise ValueError(f"Pinned C geometry/calibration digest changed: {actual}")
    metadata = json.loads(path.with_suffix(".json").read_text())["clip_metadata"]
    with np.load(path) as data:
        calibration = dict(
            metadata=metadata,
            world=dict(zip(data["actor_world_names"], data["actor_world"], strict=True)),
            local=dict(zip(data["actor_world_names"], data["actor_local"], strict=True)),
            parents=dict(zip(data["actor_world_names"], data["actor_parents"], strict=True)),
        )
    seq = FixedFasteningSequence("C")
    seq.yaw = np.deg2rad(torso_yaw_degrees)
    seq.straight_driver_sizes = {"M6", "M14"}
    seq.driver_calibrations = {0: top_entry_flange_to_tcp()}
    seq.holds[0] = (seq.driver_names[0], np.linalg.inv(seq.driver_calibrations[0]))
    seq.hands[0] = seq.objects[seq.driver_names[0]] @ np.linalg.inv(seq.driver_calibrations[0])
    seq.connection_mode = "top_entry"
    seq.calibration_mesh_path = str(path)
    seq.calibration_mesh_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    seq.clip_calibration = calibration
    seq.clips = {1: [1.0, 1.0], 2: [1.0, 1.0]}
    for n in (1, 2):
        seq.objects.update(_clip_frames(calibration, n, 1.0, 1.0))
    seq.phase("OP030C／J1上締め端子・位置決めと支持を確認", 1.0)
    _clip_release(seq, 2)
    _clip_release(seq, 1)
    work = product_frame(lift=LIFT)
    for n in (2, 1):
        for arm, size, end, thickness in ((0, "M6", "J1", 0.0038), (1, "M14", "T", 0.0032)):
            frame = j1_lug_frame(n, "top_entry") if end == "J1" else lug_frame(n, end)
            seat = work @ frame @ pose(location=(0, 0, thickness))
            append_fastening(seq, arm, size, seat, label=f"H03-{n}／{end}端子{size}・上締め", wire_number=n)
            park = pose(location=(-0.55, CY + (-0.72 if arm == 0 else 0.72), 1.30))
            _phase(seq, f"OP030C／{size}固定工具を待機位置へ", 4.0, arm, park, free=True)
    seq.phase("OP030C／同じ4ナットの締結終了・両工具待機", 1.0)
    return seq
