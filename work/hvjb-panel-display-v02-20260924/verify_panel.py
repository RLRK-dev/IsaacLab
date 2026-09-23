# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Check saved panel-hand displays and the limited change's numerical boundaries."""

import importlib.util
import json
import sys
from pathlib import Path

import correct_panel as fix
import numpy as np
import probe_panel as probe

sys.path.insert(0, str(probe.PREVIOUS))
import verify_holds as old_verify  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def branch(model, prior, source_t, scene_id, role, height):
    row = next(item for item in probe.fix.old.SCENES if item["id"] == scene_id)
    begin, end = row["source_clock"]
    values = []
    for epsilon in (1e-3, 1e-6):
        poses = []
        for time in (source_t - epsilon, source_t + epsilon):
            video_t = row["start_s"] + (time - begin) / (end - begin) * row["screen_duration_s"]
            model.animate_process(video_t)
            actual = probe.fix.old.scene_at(video_t)
            actual_clock, _ = probe.fix.old.scene_clock(video_t, actual)
            prior.apply(model, actual_clock, actual["id"])
            probe.fix.apply(model, actual_clock)
            fix.apply(model, actual_clock, height)
            poses.append(np.array([model.scene.get_pose(node) for node in model.arms[role]["hand"]]))
        values.append({"epsilon": epsilon, "hand_matrix_difference_norm": float(np.linalg.norm(poses[1] - poses[0]))})
    assert values[-1]["hand_matrix_difference_norm"] <= max(1e-12, values[0]["hand_matrix_difference_norm"] * 0.02)
    return values


def panel_hold(data, clocks, model):
    rows = []
    for label, role, target, begin, stop in (
        ("B_first", "B", "panel", 12, 34.5),
        ("B_next", "B", "panel_next", 38, 47),
        ("C_receive", "C主", "panel", 34, 38),
    ):
        selected = (clocks >= begin) & (clocks <= stop)
        indices = np.flatnonzero(selected)
        names = data["object_names"].tolist()
        palm = data["matrices"][selected, names.index(role + "_palm")]
        target_origin = data["matrices"][selected, names.index(target), :3, 3] - [0, 0, 0.13]
        relative = palm[:, :3, 3] - [0, 0, 0.18] - target_origin
        delta = np.ptp(relative, axis=0)
        assert max(delta) < 1e-12
        pairs = [
            pair
            for index in indices
            for pair in probe.overlaps(
                model, data["matrices"], int(index), role, "b_next" if target == "panel_next" else "b_unit"
            )
        ]
        positive = sum(pair["positive_aabb_overlap"] for pair in pairs)
        assert positive == 0
        yaw = np.degrees(np.arctan2(palm[:, 1, 0], palm[:, 0, 0]))
        assert np.allclose(yaw, 90, rtol=0, atol=1e-12)
        rows.append(
            {
                "id": label,
                "source_clock": [begin, stop],
                "samples": len(indices),
                "relative_first": relative[0].tolist(),
                "relative_range": delta.tolist(),
                "component_aabb_pairs_checked": len(pairs),
                "positive_aabb_pairs": positive,
                "yaw_min_max": [float(yaw.min()), float(yaw.max())],
            }
        )
    return rows


def main():
    output = probe.ROOT / "audit/panel_verification.json"
    assert not output.exists()
    delta = json.loads((probe.ROOT / "audit/panel_display_delta.json").read_text())
    target = probe.ROOT / delta["output_bank"]
    for path, digest in delta["input_sha256"].items():
        assert probe.sha(Path(path)) == digest
    assert probe.sha(target) == delta["output_sha256"]
    with np.load(probe.BANK, allow_pickle=False) as saved:
        before = {key: saved[key] for key in saved.files}
    with np.load(target, allow_pickle=False) as saved:
        after = {key: saved[key] for key in saved.files}
    assert before.keys() == after.keys()
    assert all(np.array_equal(before[key], after[key]) for key in before if key != "matrices")
    names = before["object_names"].tolist()
    untouched = [i for i, name in enumerate(names) if not name.startswith(("B_", "C主_"))]
    assert np.array_equal(before["matrices"][:, untouched], after["matrices"][:, untouched])
    helper = load("panel_verify_clock", probe.WORK / "hvjb-display-continuity-v01-20260923/probe_saved.py")
    plan = json.loads((probe.WORK / "hvjb-line-video-v05b-20260923/data/concept_v05b.json").read_text())
    _, clocks = helper.sample_scenes(after["time_s"], plan)
    measurements = old_verify.measurements(after, clocks)
    assert all(max(row["relative_position_range"]) < 1e-12 for row in measurements.values())
    model = probe.fix.old.Model()
    envelope = json.loads((probe.ROOT / "audit/panel_envelopes.json").read_text())
    assert all(sum(pair["positive_aabb_overlap"] for pair in row["pairs"]) == 1 for row in envelope["observations"])
    regression = []
    for label, index, role, group in (
        ("B_first", 315, "B", "b_unit"),
        ("B_next", 825, "B", "b_next"),
        ("C_panel", 690, "C主", "b_unit"),
    ):
        counts = [
            sum(pair["positive_aabb_overlap"] for pair in probe.overlaps(model, data["matrices"], index, role, group))
            for data in (before, after)
        ]
        assert counts == [1, 0]
        regression.append({"id": label, "sample": index, "positive_aabb_pairs_before_after": counts})
    held = panel_hold(after, clocks, model)
    prior = load("v05_schematic_corrections", probe.WORK / "hvjb-display-continuity-v01-20260923/correct_display.py")
    observations = []
    for role, time, scene in (
        ("B", 10.8, "S01"),
        ("B", 11.7, "S03"),
        ("B", 34.5, "S05"),
        ("B", 36, "S06"),
        ("B", 37.5, "S06"),
        ("B", 47, "S08"),
        ("B", 48, "S08"),
        ("C主", 32, "S05"),
        ("C主", 33.5, "S05"),
        ("C主", 34, "S05"),
        ("C主", 35, "S06"),
        ("C主", 38, "S07"),
        ("C主", 38.6, "S07"),
    ):
        observations.append(
            {
                "role": role,
                "source_clock": time,
                "values": branch(model, prior, time, scene, role, envelope["dimensions"]["illustration_target_height"]),
            }
        )
    report = {
        "source_bank_sha256": probe.sha(probe.BANK),
        "output_bank_sha256": probe.sha(target),
        "script_sha256": probe.sha(Path(__file__)),
        "source_regression": regression,
        "all_11_relative_display_ranges": measurements,
        "panel_holding_intervals": held,
        "branch_convergence": observations,
        "other_objects_and_fields_unchanged": True,
        "position_units": "Dimensionless explanatory coordinates",
        "scope": (
            "Displayed simple boxes and numeric continuity; "
            "not grip stability, clearance acceptance, or real robot feasibility."
        ),
        "physical_acceptance_verdict": None,
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        "PANEL_DISPLAY_VERIFIED relative_pairs=11 panel_windows=3 branches=13 source_overlap_reproduced=True",
        flush=True,
    )


if __name__ == "__main__":
    main()
