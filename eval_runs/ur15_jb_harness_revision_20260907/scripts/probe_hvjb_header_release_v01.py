# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Observe all saved H05 opening/withdrawal samples [m, rad, s] without recomputing motion."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_hvjb_header_tool_configuration_v01 import ROOT, _read, _sha
from check_hvjb_header_tool_tip_sources_v01 import _protected
from probe_hvjb_header_workpiece_v01 import _analytic_checks, _bounds, _geometry, _mapping, _pairs, _targets

SETTINGS = "data/hvjb_header_release_v01.json"


def phase_name(time: float, done: float, settings: dict) -> str:
    """Name the source timeline phase [s], without asserting a real fastening-completion signal."""
    if time <= done + settings["source_opening_start_after_done_s"]:
        return "held"
    if time <= done + settings["source_opening_stop_after_done_s"]:
        return "opening"
    return "upward_withdrawal"


def hand_meshes(hand: dict, bank, index: int, translation: np.ndarray) -> list[dict]:
    """Use original saved matrices and a constant product-frame translation [m]."""
    meshes = []
    for name, row in hand["objects"].items():
        matrix = bank["OP020_hand_" + name][index]
        vertices = np.asarray(row["vertices"]) @ matrix[:3, :3].T + matrix[:3, 3] + translation
        meshes.append({"name": name, "category": row["category"], "vertices": vertices, "faces": row["faces"]})
    return meshes


def observe_sample(hand: dict, bank, index: int, translation: np.ndarray, targets: list[dict]) -> dict:
    """Reuse full-surface BVH queries at one stored sample [m, rad, s]."""
    meshes = hand_meshes(hand, bank, index, translation)
    assert len(meshes) == 14 and sum(len(row["faces"]) for row in meshes) == 51580
    pairs = [pair for mesh in meshes for pair in _pairs(mesh, targets)]
    totals = {
        target["key"]: sum(
            row["overlapping_triangle_pair_count"] for row in pairs if row["target_key"] == target["key"]
        )
        for target in targets
    }
    pads = {
        row["name"]: np.mean(row["vertices"], axis=0).tolist() for row in meshes if row["category"] == "contact_pad"
    }
    return {
        "bank_index": index,
        "saved_frame": int(bank["frames"][index]),
        "saved_time_s": float(bank["time_s"][index]),
        "gripper_q_rad": float(bank["gripper_q"][index]),
        "hand_bounds_product_m": _bounds(meshes).tolist(),
        "pad_centers_product_m": pads,
        "target_pair_totals": totals,
        "pairs": pairs,
    }


def observe_header(
    spec: dict, header_index: int, hand: dict, bank, targets: list, settings: dict, prepared: dict
) -> dict:
    """Bracket the authored release interval [s] with existing bank samples; omit no interior samples."""
    schedule = [row for row in prepared["display_bolt_schedule"] if row["header"] == header_index]
    done = max(row["stop"] for row in schedule) + settings["saved_movie_offset_s"]
    last_time = done + settings["source_retreat_stop_after_done_s"]
    first = int(np.searchsorted(bank["time_s"], done, side="right") - 1)
    last = int(np.searchsorted(bank["time_s"], last_time, side="left"))
    positions = bank[f"header_{header_index}_position"][first : last + 1]
    assert np.array_equal(positions, np.broadcast_to(positions[0], positions.shape))
    assert float(bank["gripper_q"][first]) == hand["q_closed"][header_index]
    assert float(bank["gripper_q"][last]) == hand["q_open"][header_index]
    translation = np.asarray(spec["model_translation_m"]) - positions[0]
    samples = []
    for index in range(first, last + 1):
        row = observe_sample(hand, bank, index, translation, targets)
        row["source_phase"] = phase_name(row["saved_time_s"], done, settings)
        samples.append(row)
        print("HEADER_RELEASE_SAMPLE", spec["feature_id"], row["saved_frame"], row["target_pair_totals"], flush=True)
    return {
        "feature_id": spec["feature_id"],
        "requested_source_window_s": [done, last_time],
        "source_header_position_m": positions[0].tolist(),
        "derived_translation_m": translation.tolist(),
        "header_position_unchanged": True,
        "hand_objects": 14,
        "hand_triangles": 51580,
        "samples": samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_json", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    assert not args.output_json.exists() and bpy.data.filepath == ""
    settings = _read(SETTINGS)
    before = _protected(settings)
    for path in (SETTINGS, "scripts/probe_hvjb_header_release_v01.py"):
        before[path] = _sha(path)
    world_before = {obj.name: list(map(list, obj.matrix_world)) for obj in bpy.data.objects}
    previous = _read(settings["workpiece_settings"])
    assert previous["bvh_epsilon_m"] == 0
    product, source = _geometry(previous["product_meshes"]), _geometry(previous["hand_meshes"])
    specs, prepared = _read(previous["header_settings"])["headers"], _read(settings["prepare_record"])
    assert len(product) == 92
    mapping = [
        _mapping(spec, mesh, product, previous["numeric_mapping_tolerance_m"])
        for spec, mesh in zip(specs, source["headers"], strict=True)
    ]
    targets = _targets(product)
    with np.load(ROOT / previous["motion_bank"], allow_pickle=False) as bank:
        models = [
            observe_header(spec, index, source["hand"], bank, targets, settings, prepared)
            for index, spec in enumerate(specs)
        ]
    after = {path: _sha(path) for path in before}
    assert before == after
    assert world_before == {obj.name: list(map(list, obj.matrix_world)) for obj in bpy.data.objects}
    report = {
        "observed_at": datetime.now(UTC).isoformat(),
        "settings": settings,
        "workpiece_settings": previous,
        "header_mapping": mapping,
        "analytic_checks": _analytic_checks(),
        "blender_version": bpy.app.version_string,
        "targets": [
            {
                key: value.tolist() if isinstance(value, np.ndarray) else value
                for key, value in row.items()
                if key != "tree"
            }
            for row in targets
        ],
        "models": models,
        "input_sha256_before": before,
        "input_sha256_current": after,
        "script_sha256": _sha("scripts/probe_hvjb_header_release_v01.py"),
        "native_opened": False,
        "native_saved": False,
        "source_motion_or_geometry_modified": False,
        "startup_world_matrices_unchanged": True,
        "continuous_collision_checked": False,
        "physical_acceptance_verdict": None,
    }
    with args.output_json.open("x") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    assert json.loads(args.output_json.read_text()) == report
    print("HEADER_RELEASE_COMPLETE", args.output_json, "samples", sum(len(m["samples"]) for m in models), flush=True)


if __name__ == "__main__":
    main()
