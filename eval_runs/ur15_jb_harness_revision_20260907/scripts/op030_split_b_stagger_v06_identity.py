# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Audit saved B identity, fixed product endpoints and simultaneous task events [m, rad, s]."""

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_split_b_plan import digest
from op030_split_b_stagger_v06 import SIDE_DELTA, SOURCE_BANK, build_sequence_final
from op030_split_b_v04 import load
from op030_split_wire import _bend_radius
from op030_split_wire_motion import WirePlacementConfig, target_checks
from solve_op030_motion import NODE_IDS


def check(bank_path: Path, config_path: Path) -> dict:
    """Compare saved geometry and event timing with the selected authoring factory [m, s]."""
    bank = load(bank_path)
    source = load(SOURCE_BANK)
    config_record = json.loads(config_path.read_text())
    sequence = build_sequence_final(WirePlacementConfig(**config_record["config"]))
    assert np.array_equal(bank["node_ids"], NODE_IDS)
    assert len(bank["poses"]) == len(bank["times"])
    assert bank["poses"].shape[1:] == (78, 4, 4)
    assert np.all(np.diff(bank["author_times"]) > 0)
    assert np.max(abs(np.diff(bank["times"]) - 1 / 30)) < 1e-9
    assert abs(bank["author_times"][-1] - sequence.time) < 1e-8
    root_translation_error = float(np.max(abs(bank["root_poses"][:, :3, 3] - (0.9, -1.7, 0))))
    assert root_translation_error < 1e-9
    rows, events = [], []
    initial = sequence.evaluate(0.0)
    for number, uid in sequence.active_uids.items():
        points = bank[f"wire_points_{number}"]
        lengths = np.linalg.norm(np.diff(points, axis=1), axis=2)
        expected = sequence.bends[number].lengths
        total_error = float(np.max(abs(np.sum(lengths, axis=1) - np.sum(expected))))
        segment_redistribution = float(np.max(abs(lengths - expected)))
        final_curve_error = float(np.max(abs(points[-1] - source[f"wire_points_{number}"][-1])))
        final_lug_error = float(
            np.max(abs(bank[f"wire_lug_poses_{number}"][-1] - source[f"wire_lug_poses_{number}"][-1]))
        )
        initial_curve_error = float(np.max(abs(points[0] - initial["wires"][uid]["shape"].centerline)))
        expected_initial = source[f"wire_points_{number}"][0] @ SIDE_DELTA[:3, :3].T + SIDE_DELTA[:3, 3]
        supply_delta_error = float(np.max(abs(points[0] - expected_initial)))
        minimum_radius = min(_bend_radius(frame) for frame in points)
        assert max(final_curve_error, final_lug_error, initial_curve_error, supply_delta_error) < 1e-8
        assert total_error < 1e-8
        rows.append(
            dict(
                number=number,
                uid=uid,
                physical_left_holds="J1",
                physical_right_holds="T",
                material_grasp_offset_m=sequence.config.grasp_offset,
                insulation_cut_length_m=float(np.sum(expected)),
                maximum_total_length_error_m=total_error,
                maximum_material_segment_redistribution_m=segment_redistribution,
                minimum_geometric_centerline_radius_m=float(minimum_radius),
                final_curve_v05_error_m=final_curve_error,
                final_lug_v05_matrix_error=final_lug_error,
                supply_delta_error_m=supply_delta_error,
            )
        )
        for index, phase in enumerate(sequence.phases):
            if not phase["label"].startswith(f"H03-{number}"):
                continue
            relevant = any(
                term in phase["label"]
                for term in (
                    "両端の被覆上方",
                    "両端へ下降",
                    "被覆を把持",
                    "直線のまま持上げ",
                    "同時に開く",
                    "180mm鉛直上昇",
                    "両指を全開",
                )
            )
            if not relevant:
                continue
            start_index = int(np.argmin(abs(bank["author_times"] - phase["start"])))
            end_index = int(np.argmin(abs(bank["author_times"] - phase["stop"])))
            before = sequence.evaluate(phase["start"] + 1e-9)
            after = sequence.evaluate(phase["stop"] - 1e-9)
            item = dict(
                phase_index=index,
                label=phase["label"],
                start_frame=start_index,
                end_frame=end_index,
                start_s=float(bank["times"][start_index]),
                stop_s=float(bank["times"][end_index]),
                start_gaps_m=before["gaps"].tolist(),
                stop_gaps_m=after["gaps"].tolist(),
                free_hands=phase["free_hands"],
            )
            if "被覆上方" in phase["label"]:
                assert all(phase["free_hands"])
                first_moves = []
                for arm in (0, 1):
                    deltas = np.max(
                        abs(bank["joints"][start_index : end_index + 1, arm] - bank["joints"][start_index, arm]), axis=1
                    )
                    moving = np.flatnonzero(deltas > 1e-6)
                    assert len(moving)
                    first_moves.append(start_index + int(moving[0]))
                item["first_moving_frame_by_physical_arm"] = first_moves
                assert abs(first_moves[0] - first_moves[1]) <= 2
            if "180mm鉛直上昇" in phase["label"]:
                delta = after["hands"][:, :3, 3] - before["hands"][:, :3, 3]
                assert np.max(abs(delta - (0, 0, 0.18))) < 1e-8
                item["both_hand_translation_m"] = delta.tolist()
                if number == 1:
                    assert abs(before["gaps"][0] - 0.020) < 1e-9
                    item["H1_J1_physical_left_gap_m"] = float(before["gaps"][0])
            events.append(item)
    return dict(
        observed_at=datetime.now().astimezone().isoformat(),
        bank=str(bank_path.relative_to(ROOT)),
        bank_sha256=digest(bank_path),
        config_sha256=digest(config_path),
        source_v05_bank_sha256=digest(SOURCE_BANK),
        factory="op030_split_b_stagger_v06:build_sequence_final",
        factory_sha256=digest(ROOT / "scripts/op030_split_b_stagger_v06.py"),
        config=asdict(sequence.config),
        frames=len(bank["times"]),
        node_ids=NODE_IDS.tolist(),
        physical_arm_ids_unchanged=True,
        product_and_final_wire_world_orientation_unchanged=True,
        root_translation_error_m=root_translation_error,
        target_checks=target_checks(sequence),
        wire_rows=rows,
        events=events,
        unused_stock_uid_count=8,
        supply_uid_count=10,
        geometry_only=True,
        formal_physical_verdict=None,
        passed=True,
    )


def main() -> None:
    """Write a separate audit of an immutable saved native-frame bank [s]."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = check(args.bank.resolve(), args.config.resolve())
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("STAGGER_IDENTITY_COMPLETE", result["passed"], result["frames"], flush=True)


if __name__ == "__main__":
    main()
