# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Check display-branch continuity and unchanged saved product/camera samples."""

import json

import correct_display as fix
import numpy as np
import probe_saved as probe


def pose_at(model, source_t, scene_id, role, corrected):
    row = next(row for row in fix.old.SCENES if row["id"] == scene_id)
    begin, end = row["source_clock"]
    video_t = row["start_s"] + (source_t - begin) / (end - begin) * row["screen_duration_s"]
    model.animate_process(video_t)
    if corrected:
        fix.apply(model, source_t, scene_id)
    return np.array([model.scene.get_pose(node) for node in model.arms[role]["hand"]])


def branch_steps(model, source_t, scene_id, role, corrected):
    values = []
    for epsilon in (0.001, 0.000001):
        before = pose_at(model, source_t - epsilon, scene_id, role, corrected)
        after = pose_at(model, source_t + epsilon, scene_id, role, corrected)
        values.append(
            {"source_clock_epsilon": epsilon, "matrix_difference_norm": float(np.linalg.norm(after - before))}
        )
    return values


def main():
    output = probe.ROOT / "audit/correction_verification.json"
    assert not output.exists()
    new_path = probe.ROOT / "data/concept_display_v05.npz"
    delta = json.loads((probe.ROOT / "audit/display_v05_delta.json").read_text())
    assert probe.sha(probe.BANK) == probe.BANK_SHA
    assert probe.sha(new_path) == delta["output_bank_sha256"]
    with np.load(probe.BANK, allow_pickle=False) as saved:
        before = {key: saved[key] for key in saved.files}
    with np.load(new_path, allow_pickle=False) as saved:
        after = {key: saved[key] for key in saved.files}
    assert before.keys() == after.keys()
    unchanged_fields = [key for key in before if np.array_equal(before[key], after[key])]
    assert set(unchanged_fields) == set(before) - {"matrices"}
    assert np.array_equal(before["matrices"][:, 50:], after["matrices"][:, 50:])
    plan = json.loads((probe.VIDEO / "data/concept_v04.json").read_text())
    _, source_times = probe.sample_scenes(before["time_s"], plan)
    held = {}
    for role, begin, end in (("A", 22, 27.7), ("B", 12, 34.5), ("C主", 56.3, 60.5)):
        mask = (source_times >= begin) & (source_times <= end)
        columns = np.array([name.startswith(role + "_") for name in before["object_names"]])
        held[role] = np.array_equal(before["matrices"][mask][:, columns], after["matrices"][mask][:, columns])
        assert held[role]
    mask = (source_times >= 12.2) & (source_times < 13.5)
    pickup_offsets = {}
    for label, data in (("before", before), ("after", after)):
        target = data["matrices"][mask, 6, :3, 3] - [0, 0, 0.18]
        part = data["matrices"][mask, 249, :3, 3]
        pickup_offsets[label] = float(np.linalg.norm(target - part, axis=-1).max())
    assert pickup_offsets["before"] > 0.001
    assert pickup_offsets["after"] < 1e-12
    model = fix.old.Model()
    branches = []
    for role, source_t, scene in (
        ("A", 21.5, "S04"),
        ("A", 27.7, "S05"),
        ("B", 11.7, "S03"),
        ("B", 34.5, "S05"),
        ("C主", 56.3, "S12"),
    ):
        original = branch_steps(model, source_t, scene, role, False)
        corrected = branch_steps(model, source_t, scene, role, True)
        # This is an epsilon-convergence regression check, not a physical acceptance limit.
        assert original[-1]["matrix_difference_norm"] > original[0]["matrix_difference_norm"] * 0.5
        assert corrected[-1]["matrix_difference_norm"] < corrected[0]["matrix_difference_norm"] * 0.02
        branches.append(
            {"role": role, "source_clock": source_t, "scene": scene, "before": original, "after": corrected}
        )
    probe.write(
        output,
        {
            "old_bank_sha256": probe.BANK_SHA,
            "new_bank_sha256": probe.sha(new_path),
            "unchanged_npz_fields": unchanged_fields,
            "held_intervals_unchanged": held,
            "product_tools_wires_pallet_columns_50_onward_unchanged": True,
            "pickup_hand_target_to_part_maximum_display_offset": pickup_offsets,
            "regression_original_has_persistent_branch_jump": True,
            "regression_corrected_difference_tends_to_zero": True,
            "branch_observations": branches,
            "test_scope": "Numerical continuity of schematic display functions, not an accepted robot trajectory.",
            "physical_validity_verdict": None,
            "script_sha256": probe.sha(probe.ROOT / "verify_corrections.py"),
        },
    )
    print("DISPLAY_REGRESSION_COMPLETE original_discontinuities=5 corrected_convergence=5")
    print("PICKUP_DISPLAY_OFFSET", pickup_offsets)
    print("HELD_INTERVALS_UNCHANGED", held)


if __name__ == "__main__":
    main()
