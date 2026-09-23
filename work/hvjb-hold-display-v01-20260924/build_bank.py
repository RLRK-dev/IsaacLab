# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Create a new display bank, retaining all product, fixture, and camera values."""

import importlib.util
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import correct_holds as fix
import numpy as np
import probe_holds as probe


def main():
    target = probe.ROOT / "data/concept_display_v05d.npz"
    record = probe.ROOT / "audit/hold_display_delta.json"
    assert not target.exists() and not record.exists()
    assert probe.sha(probe.BANK) == probe.BANK_SHA
    source_paths = [
        probe.BANK,
        probe.PLAN,
        probe.HELPER,
        Path(__file__),
        probe.ROOT / "correct_holds.py",
        probe.ROOT / "probe_holds.py",
        fix.OLD / "render_process.py",
        fix.OLD / "legacy_model.py",
        Path("/home/rlrk/src/ur15-line-render/render_ur15_line.py"),
    ]
    pins = {str(path): probe.sha(path) for path in source_paths}
    spec = importlib.util.spec_from_file_location("hold_clock", probe.HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    with np.load(probe.BANK, allow_pickle=False) as saved:
        data = {key: saved[key] for key in saved.files}
    poses = data["matrices"].copy()
    scenes, clocks = helper.sample_scenes(data["time_s"], json.loads(probe.PLAN.read_text()))
    model = fix.old.Model()
    assert model.names == data["object_names"].tolist()
    counters, actions = Counter(), []
    for index, source_t in enumerate(clocks):
        # Read the saved state; never call legacy animate() to regenerate unrelated objects.
        for node, matrix in zip(model.dynamic, data["matrices"][index], strict=True):
            model.scene.set_pose(node, matrix)
        for role, action in fix.apply(model, float(source_t)).items():
            columns = [i for i, name in enumerate(model.names) if name.startswith(role + "_")]
            for column in columns:
                poses[index, column] = model.scene.get_pose(model.dynamic[column])
            counters[action] += 1
            actions.append(
                {
                    "sample": index,
                    "video_s": float(data["time_s"][index]),
                    "scene": str(scenes[index]),
                    "action": action,
                }
            )
    changes = np.any(poses != data["matrices"], axis=(2, 3))
    columns = np.flatnonzero(np.any(changes, axis=0))
    allowed = [i for i, name in enumerate(model.names) if name.startswith(("A_", "B_", "C主_"))]
    forbidden = [i for i in range(len(model.names)) if i not in allowed]
    assert np.array_equal(poses[:, forbidden], data["matrices"][:, forbidden])
    assert np.isfinite(poses).all()
    target.parent.mkdir()
    np.savez_compressed(target, **{**data, "matrices": poses})
    with np.load(target, allow_pickle=False) as saved:
        assert saved.files == list(data)
        assert all(np.array_equal(saved[key], poses if key == "matrices" else data[key]) for key in data)
    assert all(probe.sha(Path(path)) == value for path, value in pins.items())
    report = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "input_sha256": pins,
        "output_bank": str(target.relative_to(probe.ROOT)),
        "output_sha256": probe.sha(target),
        "changed_samples": int(np.any(changes, axis=1).sum()),
        "changed_columns": [{"column": int(i), "name": model.names[i]} for i in columns],
        "action_sample_counts": dict(counters),
        "actions": actions,
        "product_pallet_tools_wires_assistants_unchanged": True,
        "camera_and_time_unchanged": True,
        "readback_identical": True,
        "source_files_unchanged": True,
        "position_units": "Dimensionless explanatory coordinates",
        "new_robot_control_or_ik": False,
        "physical_acceptance_verdict": None,
    }
    record.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"HOLD_DISPLAY_BANK_COMPLETE samples={report['changed_samples']} columns={len(columns)}", flush=True)


if __name__ == "__main__":
    main()
