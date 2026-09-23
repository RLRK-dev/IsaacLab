# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Read simple displayed panel, accessory, and hand envelopes."""

import hashlib
import importlib.util
import json
from itertools import product
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
PREVIOUS = WORK / "hvjb-hold-display-v01-20260924"
spec = importlib.util.spec_from_file_location("prior_hold_display", PREVIOUS / "correct_holds.py")
fix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fix)
BANK = PREVIOUS / "data/concept_display_v05d.npz"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def world_bounds(node, matrix):
    corners = np.array(list(product(*node.mesh.bounds.T.tolist())))
    points = corners @ matrix[:3, :3].T + matrix[:3, 3]
    return np.array([points.min(0), points.max(0)])


def panel_dimensions(model):
    board, offset = model.b_unit[0]
    board_top = float(board.mesh.bounds[1, 2] + offset[2])
    component_top = max(float(node.mesh.bounds[1, 2] + pos[2]) for node, pos in model.b_unit[1:])
    finger_bottom_from_target = float(model.arms["B"]["hand"][1].mesh.bounds[0, 2] + 0.055)
    assert component_top < board_top
    tip_bottom = (board_top + component_top) / 2
    return {
        "board_top_above_origin": board_top,
        "component_top_above_origin": component_top,
        "finger_bottom_from_target": finger_bottom_from_target,
        "display_free_band": [component_top, board_top],
        "illustration_tip_bottom": tip_bottom,
        "illustration_target_height": tip_bottom - finger_bottom_from_target,
        "rule": "Center the finger bottom in the free upper band of the existing schematic board.",
        "physical_length_unit": None,
    }


def overlaps(model, matrices, row, role, group):
    names = model.names
    parts = getattr(model, group)
    candidates = []
    for hand_name in (role + "_left_finger", role + "_right_finger"):
        hand_index = names.index(hand_name)
        hand_bounds = world_bounds(model.dynamic[hand_index], matrices[row, hand_index])
        for ordinal, (node, _) in enumerate(parts[1:], start=1):
            part_index = model.dynamic.index(node)
            part_bounds = world_bounds(node, matrices[row, part_index])
            widths = np.minimum(hand_bounds[1], part_bounds[1]) - np.maximum(hand_bounds[0], part_bounds[0])
            candidates.append(
                {
                    "finger": hand_name,
                    "component_ordinal": ordinal,
                    "aabb_overlap_widths": widths.tolist(),
                    "positive_aabb_overlap": bool(np.all(widths > 0)),
                }
            )
    return candidates


def main():
    output = ROOT / "audit/panel_envelopes.json"
    assert not output.exists()
    delta = json.loads((PREVIOUS / "audit/hold_display_delta.json").read_text())
    assert sha(BANK) == delta["output_sha256"]
    with np.load(BANK, allow_pickle=False) as saved:
        matrices = saved["matrices"]
    model = fix.old.Model()
    cases = [
        ("B_first", 315, "B", "b_unit"),
        ("B_next", 825, "B", "b_next"),
        ("C_panel", 690, "C主", "b_unit"),
    ]
    observations = [
        {"id": label, "sample": index, "pairs": overlaps(model, matrices, index, role, group)}
        for label, index, role, group in cases
    ]
    report = {
        "input_bank": str(BANK),
        "input_bank_sha256": sha(BANK),
        "script_sha256": sha(Path(__file__)),
        "model_source_sha256": sha(fix.OLD / "legacy_model.py"),
        "dimensions": panel_dimensions(model),
        "observations": observations,
        "scope": "Axis-aligned bounds of simple schematic boxes, not real contact judgment.",
        "physical_acceptance_verdict": None,
    }
    output.parent.mkdir()
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("PANEL_ENVELOPES", report["dimensions"], flush=True)
    for row in observations:
        print(row["id"], "positive_aabb_pairs", sum(pair["positive_aabb_overlap"] for pair in row["pairs"]), flush=True)


if __name__ == "__main__":
    main()
