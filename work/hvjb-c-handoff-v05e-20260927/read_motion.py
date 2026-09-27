# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Record display-only differences and support continuity without a physical-validity verdict."""

from __future__ import annotations

import json

import numpy as np
from build_motion import ROOT, SOURCE, hand_state, sha, write


def movement(data, first: int, last: int) -> float:
    points = np.array([hand_state(data, index)[0] for index in range(first, last + 1)])
    return float(np.linalg.norm(points - points[0], axis=1).max())


def main() -> None:
    before, after = np.load(SOURCE), np.load(ROOT / "data/concept_v05e.npz")
    delta = json.loads((ROOT / "audit/motion_delta.json").read_text())
    assert sha(ROOT / "data/concept_v05e.npz") == delta["output_sha256"]
    names = after["object_names"].tolist()
    unit_columns = [i for i, name in enumerate(names) if name in ("base", "panel")]
    assert len(unit_columns) == 11
    observations = {
        "basis": "Saved display matrices, not measured contact or holding signals",
        "coordinate_units": "dimensionless display coordinates; illustration seconds",
        "source_sha256": sha(SOURCE),
        "new_bank_sha256": delta["output_sha256"],
        "main_opening_window_indices": [750, 762],
        "old_hand_target_max_displacement_in_opening_window": movement(before, 750, 762),
        "new_hand_target_max_displacement_in_opening_window": movement(after, 750, 762),
        "main_closing_window_indices": [809, 825],
        "new_hand_target_max_displacement_in_closing_window": movement(after, 809, 825),
        "unit_matrix_max_delta_during_regrip": float(
            np.abs(after["matrices"][750:826, unit_columns] - after["matrices"][750, unit_columns]).max()
        ),
        "auxiliary_matrix_max_delta_during_regrip": float(
            np.abs(
                after["matrices"][750:826, names.index("C補助_palm")]
                - after["matrices"][750, names.index("C補助_palm")]
            ).max()
        ),
        "tool_C_matrix_max_delta_during_regrip": float(
            np.abs(
                after["matrices"][750:826, names.index("tool_C")] - after["matrices"][750, names.index("tool_C")]
            ).max()
        ),
        "sampled_hand_states": [],
        "physical_acceptance_verdict": None,
    }
    for index in (750, 755, 762, 763, 778, 779, 787, 788, 808, 809, 818, 819, 825):
        point, gap, yaw = hand_state(after, index)
        observations["sampled_hand_states"].append(
            {
                "index": index,
                "illustration_time_s": float(after["time_s"][index]),
                "hand_target": point.tolist(),
                "display_gap": gap,
                "display_yaw_rad": yaw,
            }
        )
    write(ROOT / "audit/saved_motion_observations.json", observations)
    print(json.dumps({key: value for key, value in observations.items() if key != "sampled_hand_states"}, indent=2))


if __name__ == "__main__":
    main()
