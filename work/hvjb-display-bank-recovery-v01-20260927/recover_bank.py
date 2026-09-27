# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Recover the recorded display arrays by reusing the unchanged correction functions."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
OLD_WORK = Path("/tmp/hvjb-line-progress-20260923/work")
XYZ = WORK / "hvjb-xyz-display-v01-20260924"
HOLD = WORK / "hvjb-hold-display-v01-20260924"
PANEL = WORK / "hvjb-panel-display-v02-20260924"
PLAN = WORK / "hvjb-line-video-v05b-20260923/data/concept_v05b.json"
HELPER = WORK / "hvjb-display-continuity-v01-20260923/probe_saved.py"
SOURCE_SHA = "7702cadf9e412895a14c82d1a6b85a6aa659f2978c22e59ddf16e2714c793a60"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: dict) -> None:
    with path.open("x") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def references() -> tuple[dict, dict]:
    paths = {
        "xyz": XYZ / "audit/display_delta.json",
        "hold": HOLD / "audit/hold_display_delta.json",
        "panel": PANEL / "audit/panel_display_delta.json",
        "envelope": PANEL / "audit/panel_envelopes.json",
    }
    records = {key: json.loads(path.read_text()) for key, path in paths.items()}
    pins = {str(path): sha(path) for path in paths.values()}
    return records, pins


def verify_dependencies(records: dict) -> tuple[list[dict], dict]:
    historical = {**records["xyz"]["source_sha256"], **records["panel"]["input_sha256"]}
    # Verify every Python/JSON/font/image dependency that the reused functions import or read.
    # Historical bank and rendered-manifest pins belong to earlier, unexecuted generation steps.
    excluded = {".npz"}
    aliases, pins = [], {}
    for original, digest in historical.items():
        path = Path(original)
        if path.suffix in excluded or "/previews/" in original:
            continue
        current = WORK / path.relative_to(OLD_WORK) if path.is_relative_to(OLD_WORK) else path
        observed = sha(current)
        assert observed == digest, (str(current), digest, observed)
        aliases.append({"recorded_path": original, "current_path": str(current), "sha256": digest})
        pins[str(current)] = digest
    return aliases, pins


def save_bank(target: Path, data: dict, poses: np.ndarray, expected: str) -> str:
    assert not target.exists()
    assert np.isfinite(poses).all()
    np.savez_compressed(target, **{**data, "matrices": poses})
    with np.load(target, allow_pickle=False) as restored:
        assert restored.files == list(data)
        for key in data:
            assert np.array_equal(restored[key], poses if key == "matrices" else data[key]), key
    digest = sha(target)
    print(f"BANK_READBACK {target.name} sha256={digest}", flush=True)
    assert digest == expected, (str(target), expected, digest)
    return digest


def xyz_poses(data: dict, times: np.ndarray) -> tuple[np.ndarray, dict]:
    fix = module("recovery_xyz_correction", XYZ / "correct_infeed.py")
    names = data["object_names"].tolist()
    columns = [names.index(name) for name in fix.COLUMNS]
    assert all(names.count(name) == 1 for name in fix.COLUMNS)
    change = fix.correction(times)
    poses = data["matrices"].copy()
    poses[:, columns, 2, 3] += change[:, None]
    allowed = np.zeros(poses.shape, dtype=bool)
    allowed[:, columns, 2, 3] = change[:, None] != 0
    assert np.array_equal(poses[~allowed], data["matrices"][~allowed])
    return poses, {"changed_samples": int(np.count_nonzero(change)), "columns": columns}


def corrected_poses(data: dict, times: np.ndarray, model, apply, allowed_roles: tuple) -> tuple[np.ndarray, dict]:
    assert model.names == data["object_names"].tolist()
    poses = data["matrices"].copy()
    counts = Counter()
    for index, source_t in enumerate(times):
        for node, matrix in zip(model.dynamic, data["matrices"][index], strict=True):
            model.scene.set_pose(node, matrix)
        for role, action in apply(model, float(source_t)).items():
            for column, name in enumerate(model.names):
                if name.startswith(role + "_"):
                    poses[index, column] = model.scene.get_pose(model.dynamic[column])
            counts[action] += 1
    diff = np.any(poses != data["matrices"], axis=(2, 3))
    columns = np.flatnonzero(diff.any(axis=0)).tolist()
    assert all(model.names[column].startswith(allowed_roles) for column in columns)
    return poses, {
        "changed_samples": int(diff.any(axis=1).sum()),
        "columns": columns,
        "action_sample_counts": dict(counts),
    }


def save_stage(output: Path, stage: str, data: dict, poses: np.ndarray, stats: dict, reference: dict) -> dict:
    expected = reference.get("output_sha256", reference.get("output_bank_sha256"))
    target = output / f"{stage}.npz"
    digest = save_bank(target, data, poses, expected)
    assert stats["changed_samples"] == reference["changed_samples"], (stage, stats)
    assert set(stats["columns"]) == {row["column"] for row in reference["changed_columns"]}
    if "action_sample_counts" in stats:
        assert stats["action_sample_counts"] == reference["action_sample_counts"]
    row = {"stage": stage, "output": str(target), "sha256": digest, "matches_recorded_sha256": True, **stats}
    write(output / f"{stage}.json", row)
    print(f"RECOVERED_STAGE {stage} samples={stats['changed_samples']} exact_sha=True", flush=True)
    return row


def reconstruct(source: dict, records: dict, output: Path) -> list[dict]:
    helper = module("recovery_saved_clock", HELPER)
    plan = json.loads(PLAN.read_text())
    assert plan["motion_sha256"] == SOURCE_SHA
    scenes, times = helper.sample_scenes(source["time_s"], plan)
    poses, stats = xyz_poses(source, times)
    assert set(scenes[np.any(poses != source["matrices"], axis=(1, 2, 3))]) == {"S01"}
    stages = [save_stage(output, "xyz_v05c", source, poses, stats, records["xyz"])]
    data = {**source, "matrices": poses}
    hold = module("recovery_hold_correction", HOLD / "correct_holds.py")
    model = hold.old.Model()
    poses, stats = corrected_poses(data, times, model, hold.apply, ("A_", "B_", "C主_"))
    stages.append(save_stage(output, "hold_v05d", data, poses, stats, records["hold"]))
    data = {**data, "matrices": poses}
    probe = module("probe_panel", PANEL / "probe_panel.py")
    panel = module("recovery_panel_correction", PANEL / "correct_panel.py")
    model = probe.fix.old.Model()
    dimensions = probe.panel_dimensions(model)
    assert dimensions == records["envelope"]["dimensions"]
    poses, stats = corrected_poses(
        data,
        times,
        model,
        lambda instance, time: panel.apply(instance, time, dimensions["illustration_target_height"]),
        ("B_", "C主_"),
    )
    stages.append(save_stage(output, "panel_v05d", data, poses, stats, records["panel"]))
    return stages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_bank", type=Path, required=True)
    args = parser.parse_args()
    output = ROOT / "recovered"
    assert not output.exists(), output
    assert sha(args.source_bank) == SOURCE_SHA
    records, pins = references()
    aliases, source_pins = verify_dependencies(records)
    pins.update(source_pins)
    pins.update({str(Path(__file__)): sha(Path(__file__)), str(args.source_bank): SOURCE_SHA})
    with np.load(args.source_bank, allow_pickle=False) as saved:
        data = {key: saved[key] for key in saved.files}
    assert data["matrices"].shape == (1785, 304, 4, 4)
    output.mkdir()
    shutil.copy2(args.source_bank, output / "source_v05b.npz")
    assert sha(output / "source_v05b.npz") == SOURCE_SHA
    stages = reconstruct(data, records, output)
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    report = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "input_sha256": pins,
        "historical_path_aliases": aliases,
        "recovered_stages": stages,
        "all_stage_sha256_match_historical_records": True,
        "saved_readback_identical": True,
        "original_sources_unchanged": True,
        "new_motion_or_geometry": False,
        "python": sys.version,
        "packages": {name: importlib.metadata.version(name) for name in ("numpy", "pyrender", "trimesh", "Pillow")},
        "physical_acceptance_verdict": None,
    }
    write(ROOT / "recovery.json", report)
    print("RECOVERY_COMPLETE stages=3 samples=1785 nodes=304 exact_sha=True", flush=True)


if __name__ == "__main__":
    main()
