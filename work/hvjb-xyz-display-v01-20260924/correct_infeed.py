# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Correct the infeed hand's schematic vertical drift while preserving all other saved objects."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
PREVIOUS = WORK / "hvjb-line-video-v05b-20260923"
BANK = PREVIOUS / "data/concept_display_v05_reused.npz"
BANK_SHA = "7702cadf9e412895a14c82d1a6b85a6aa659f2978c22e59ddf16e2714c793a60"
PLAN = PREVIOUS / "data/concept_v05b.json"
TIME_HELPER = WORK / "hvjb-display-continuity-v01-20260923/probe_saved.py"
COLUMNS = ("infeed_palm", "infeed_left_finger", "infeed_right_finger", "infeed_carrier", "infeed_z")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def correction(source_times: np.ndarray) -> np.ndarray:
    change = np.zeros(len(source_times))
    approach = (source_times > 4) & (source_times <= 4.6)
    lift = (source_times > 4.6) & (source_times < 5.6)
    for mask, first, last, start, stop in ((approach, 4, 4.6, 0, -0.015), (lift, 4.6, 5.6, -0.015, 0)):
        u = (source_times[mask] - first) / (last - first)
        smooth = u * u * (3 - 2 * u)
        change[mask] = start + (stop - start) * smooth
    return change


def relative_ranges(poses: np.ndarray, names: list[str], mask: np.ndarray) -> dict:
    case = poses[:, names.index("case"), :3, 3] - [0, 0, 0.015]
    hand = poses[:, names.index("infeed_palm"), :3, 3] - [0, 0, 0.18]
    values = (hand - case)[mask]
    return {
        "minimum": values.min(0).tolist(),
        "maximum": values.max(0).tolist(),
        "range": np.ptp(values, axis=0).tolist(),
    }


def main() -> None:
    assert not (ROOT / "data").exists() and not (ROOT / "audit").exists()
    assert sha(BANK) == BANK_SHA
    source_pins = {str(path): sha(path) for path in (BANK, PLAN, TIME_HELPER, Path(__file__))}
    plan = json.loads(PLAN.read_text())
    assert plan["motion_sha256"] == BANK_SHA
    spec = importlib.util.spec_from_file_location("preserved_scene_clock_mapping", TIME_HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    with np.load(BANK, allow_pickle=False) as saved:
        source = {key: saved[key] for key in saved.files}
    poses = source["matrices"]
    assert poses.shape == (1785, 304, 4, 4)
    names = source["object_names"].tolist()
    ids, times = helper.sample_scenes(source["time_s"], plan)
    columns = [names.index(name) for name in COLUMNS]
    assert all(names.count(name) == 1 for name in COLUMNS)
    changes = correction(times)
    changed = np.flatnonzero(changes)
    assert set(ids[changed]) == {"S01"}
    updated = poses.copy()
    updated[:, columns, 2, 3] += changes[:, None]
    assert np.isfinite(updated).all()
    expected_mask = np.zeros(poses.shape, dtype=bool)
    expected_mask[:, columns, 2, 3] = changes[:, None] != 0
    assert np.array_equal(updated[~expected_mask], poses[~expected_mask])
    pickup = (times >= 4.6) & (times <= 8.7)
    returning = (times >= 74.7) & (times <= 79.4)
    before, after = [relative_ranges(array, names, pickup) for array in (poses, updated)]
    assert before["range"][2] > 0.014  # The unchanged bank fails the constant-relative-position check.
    assert max(after["range"]) < 1e-12  # Numerical readback tolerance, not a manufacturing allowance.
    original_return = relative_ranges(poses, names, returning)
    assert relative_ranges(updated, names, returning) == original_return
    (ROOT / "data").mkdir()
    (ROOT / "audit").mkdir()
    target = ROOT / "data/concept_display_v05c.npz"
    np.savez_compressed(target, **{**source, "matrices": updated})
    with np.load(target, allow_pickle=False) as restored:
        assert restored.files == list(source)
        for key in source:
            assert np.array_equal(restored[key], updated if key == "matrices" else source[key]), key
    assert all(sha(Path(path)) == digest for path, digest in source_pins.items())
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "source_sha256": source_pins,
        "output_bank": str(target.relative_to(ROOT)),
        "output_bank_sha256": sha(target),
        "samples": len(poses),
        "changed_samples": len(changed),
        "changed_columns": [{"column": column, "name": names[column]} for column in columns],
        "changed_matrix_elements": "translation Z only",
        "first_last_changed_video_s": source["time_s"][changed[[0, -1]]].tolist(),
        "first_last_changed_source_clock": times[changed[[0, -1]]].tolist(),
        "maximum_absolute_vertical_correction": float(abs(changes).max()),
        "pickup_hand_relative_to_case_before": before,
        "pickup_hand_relative_to_case_after": after,
        "return_hand_relative_to_case_unchanged": original_return,
        "all_other_saved_elements_bitwise_identical": True,
        "saved_readback_identical": True,
        "original_source_unchanged": True,
        "position_units": "Dimensionless explanatory coordinates, not manufacturing meters.",
        "basis": (
            "Retain the existing carry offset 0.14; correct its 0.155 pickup endpoint using the existing smoothstep."
        ),
        "new_robot_ik_or_control": False,
        "physical_acceptance_verdict": None,
    }
    (ROOT / "audit/display_delta.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(f"INFEED_DISPLAY_CORRECTED samples={len(changed)} columns={len(columns)} source_unchanged=True", flush=True)
    print("PICKUP_RELATIVE_RANGE", before["range"], "->", after["range"], flush=True)


if __name__ == "__main__":
    main()
