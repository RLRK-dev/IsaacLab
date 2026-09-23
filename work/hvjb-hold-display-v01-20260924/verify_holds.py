# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Verify display attachment and unchanged source fields, without physical acceptance."""

import importlib.util
import json
from pathlib import Path

import correct_holds as fix
import numpy as np
import probe_holds as probe


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def measurements(data, times):
    names = data["object_names"].tolist()
    poses = data["matrices"]
    rows = {}
    for label, hand, product, offset, start, stop, _ in probe.PAIRS:
        selected = (times >= start) & (times <= stop)
        palm = poses[selected, names.index(hand + "_palm")]
        target = palm[:, :3, 3] - np.einsum("tij,j->ti", palm[:, :3, :3], [0, 0, 0.18])
        relative = target - (poses[selected, names.index(product), :3, 3] - offset)
        left, right = [poses[selected, names.index(hand + end), :3, 3] for end in ("_left_finger", "_right_finger")]
        gaps = np.linalg.norm(left - right, axis=1) - 0.032
        yaw = np.degrees(np.arctan2(palm[:, 1, 0], palm[:, 0, 0]))
        rows[label] = {
            "relative_position_range": np.ptp(relative, axis=0).tolist(),
            "relative_position_first": relative[0].tolist(),
            "opening_min_max": [float(gaps.min()), float(gaps.max())],
            "yaw_min_max": [float(yaw.min()), float(yaw.max())],
        }
    return rows


def branch_values(model, earlier, source_t, scene, role):
    row = next(item for item in fix.old.SCENES if item["id"] == scene)
    begin, end = row["source_clock"]
    values = []
    for epsilon in (1e-3, 1e-6):
        hands = []
        for time in (source_t - epsilon, source_t + epsilon):
            video_t = row["start_s"] + (time - begin) / (end - begin) * row["screen_duration_s"]
            model.animate_process(video_t)
            actual = fix.old.scene_at(video_t)
            actual_clock, _ = fix.old.scene_clock(video_t, actual)
            earlier.apply(model, actual_clock, actual["id"])
            fix.apply(model, actual_clock)
            hands.append(np.array([model.scene.get_pose(node) for node in model.arms[role]["hand"]]))
        values.append(
            {"epsilon_source_clock": epsilon, "hand_matrix_difference_norm": float(np.linalg.norm(hands[1] - hands[0]))}
        )
    # Numerical convergence with decreasing epsilon, not a robot-clearance allowance.
    assert values[-1]["hand_matrix_difference_norm"] <= max(1e-12, values[0]["hand_matrix_difference_norm"] * 0.02)
    return values


def main():
    output = probe.ROOT / "audit/hold_verification.json"
    assert not output.exists()
    receipt = json.loads((probe.ROOT / "audit/hold_display_delta.json").read_text())
    target = probe.ROOT / receipt["output_bank"]
    assert probe.sha(probe.BANK) == probe.BANK_SHA and probe.sha(target) == receipt["output_sha256"]
    for path, digest in receipt["input_sha256"].items():
        assert probe.sha(Path(path)) == digest
    with np.load(probe.BANK, allow_pickle=False) as saved:
        before = {key: saved[key] for key in saved.files}
    with np.load(target, allow_pickle=False) as saved:
        after = {key: saved[key] for key in saved.files}
    assert before.keys() == after.keys()
    assert all(np.array_equal(before[key], after[key]) for key in before if key != "matrices")
    names = before["object_names"].tolist()
    untouched = [i for i, name in enumerate(names) if not name.startswith(("A_", "B_", "C主_"))]
    assert np.array_equal(before["matrices"][:, untouched], after["matrices"][:, untouched])
    helper = load_module("verify_hold_clock", probe.HELPER)
    _, times = helper.sample_scenes(before["time_s"], json.loads(probe.PLAN.read_text()))
    original, corrected = [measurements(data, times) for data in (before, after)]
    # Regression: the unmodified input violates constant relative display attachment.
    assert original["C_outer_header"]["relative_position_range"][1] > 0.05
    assert original["A_next_unit"]["relative_position_range"][2] > 0.09
    assert original["B_next_panel"]["yaw_min_max"] != original["B_panel_to_C"]["yaw_min_max"]
    assert all(max(row["relative_position_range"]) < 1e-12 for row in corrected.values())
    for next_key, first_key in (("A_next_unit", "A_unit_to_C"), ("B_next_panel", "B_panel_to_C")):
        for field in ("relative_position_first", "opening_min_max", "yaw_min_max"):
            assert np.allclose(corrected[next_key][field], corrected[first_key][field], rtol=0, atol=1e-12)
    previous_file = probe.WORK / "hvjb-display-continuity-v01-20260923/correct_display.py"
    earlier = load_module("prior_schematic_corrections", previous_file)
    model = fix.old.Model()
    branches = []
    for role, source_t, scene in (
        ("A", 29, "S05"),
        ("A", 32, "S05"),
        ("A", 43, "S08"),
        ("A", 44, "S08"),
        ("B", 36, "S06"),
        ("B", 38, "S07"),
        ("B", 47, "S08"),
        ("B", 48, "S08"),
        ("C主", 50, "S11"),
        ("C主", 54, "S11"),
        ("C主", 54.5, "S11"),
        ("C主", 55, "S12"),
    ):
        branches.append(
            {
                "role": role,
                "source_clock": source_t,
                "scene": scene,
                "values": branch_values(model, earlier, source_t, scene, role),
            }
        )
    report = {
        "input_bank_sha256": probe.BANK_SHA,
        "output_bank_sha256": probe.sha(target),
        "script_sha256": probe.sha(Path(__file__)),
        "previous_correction_sha256": probe.sha(previous_file),
        "before": original,
        "after": corrected,
        "branch_convergence": branches,
        "unmodified_source_exhibits_the_reported_relative_drift": True,
        "next_unit_displays_match_first_unit_relative_pose_and_gap": True,
        "all_other_fields_and_non_A_B_Cmain_objects_unchanged": True,
        "position_units": "Dimensionless explanatory coordinates",
        "physical_acceptance_verdict": None,
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("HOLD_DISPLAY_VERIFIED pairs=11 branches=12 original_regression_reproduced=True", flush=True)


if __name__ == "__main__":
    main()
