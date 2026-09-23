# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Inspect hands separately from symmetric display cylinders."""

import json

import numpy as np
import probe_saved as probe


def main():
    output = probe.ROOT / "audit/hand_display_steps.json"
    assert not output.exists()
    assert probe.sha(probe.BANK) == probe.BANK_SHA
    with np.load(probe.BANK, allow_pickle=False) as bank:
        matrices, times, names = [bank[key] for key in ("matrices", "time_s", "object_names")]
    plan = json.loads((probe.VIDEO / "data/concept_v04.json").read_text())
    ids, source_times = probe.sample_scenes(times, plan)
    positions = matrices[:, :, :3, 3]
    translation = np.linalg.norm(np.diff(positions, axis=0), axis=-1)
    scales = np.linalg.norm(matrices[:, :, :3, :3], axis=-2)
    rotations = matrices[:, :, :3, :3] / scales[:, :, None, :]
    trace = np.einsum("tnij,tnij->tn", rotations[1:], rotations[:-1])
    angles = np.degrees(np.arccos(np.clip((trace - 1) / 2, -1, 1)))
    hidden = np.all(positions == [0, 0, -30.0], axis=-1)
    mask = (ids[:-1] == ids[1:])[:, None] & ~(hidden[:-1] | hidden[1:])
    entries = {}
    for actor in ("A", "B", "AB補助", "C主", "C補助", "infeed", "outfeed"):
        hand = np.array(
            [name in {actor + tail for tail in ("_palm", "_left_finger", "_right_finger")} for name in names]
        )
        entries[actor] = {}
        for key, value in (("translation_display_units", translation), ("rotation_degrees", angles)):
            rows = probe.top_steps(value, mask & hand[None, :], times, source_times, ids, positions, names, 8)
            entries[actor][key] = rows
            first = rows[0]
            print(actor, key, first["to_video_s"], first["value"], first["object_name"])
    probe.write(output, {"source_sha256": probe.BANK_SHA, "hands": entries, "physical_validity_verdict": None})


if __name__ == "__main__":
    main()
