# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Save the limited panel display change and retain every other bank field."""

import importlib.util
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import correct_panel as fix
import numpy as np
import probe_panel as probe


def main():
    output = probe.ROOT / "data/concept_display_v05d.npz"
    record = probe.ROOT / "audit/panel_display_delta.json"
    assert not output.exists() and not record.exists()
    dimensions_path = probe.ROOT / "audit/panel_envelopes.json"
    envelope = json.loads(dimensions_path.read_text())
    assert probe.sha(probe.BANK) == envelope["input_bank_sha256"]
    paths = [
        probe.BANK,
        dimensions_path,
        Path(__file__),
        probe.ROOT / "correct_panel.py",
        probe.ROOT / "probe_panel.py",
    ]
    pins = {str(path): probe.sha(path) for path in paths}
    plan_path = probe.WORK / "hvjb-line-video-v05b-20260923/data/concept_v05b.json"
    helper_path = probe.WORK / "hvjb-display-continuity-v01-20260923/probe_saved.py"
    pins.update({str(path): probe.sha(path) for path in (plan_path, helper_path)})
    pins.update(json.loads(plan_path.read_text())["input_sha256"])
    prior_delta = json.loads((probe.PREVIOUS / "audit/hold_display_delta.json").read_text())
    pins.update(prior_delta["input_sha256"])
    assert probe.sha(probe.fix.OLD / "legacy_model.py") == envelope["model_source_sha256"]
    assert all(probe.sha(Path(path)) == digest for path, digest in pins.items())
    spec = importlib.util.spec_from_file_location("panel_clock_helper", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    with np.load(probe.BANK, allow_pickle=False) as saved:
        data = {key: saved[key] for key in saved.files}
    poses = data["matrices"].copy()
    ids, times = helper.sample_scenes(data["time_s"], json.loads(plan_path.read_text()))
    model = probe.fix.old.Model()
    assert model.names == data["object_names"].tolist()
    dims = probe.panel_dimensions(model)
    assert dims == envelope["dimensions"]
    actions, counts = [], Counter()
    for index, source_t in enumerate(times):
        for node, pose in zip(model.dynamic, data["matrices"][index], strict=True):
            model.scene.set_pose(node, pose)
        for role, action in fix.apply(model, float(source_t), dims["illustration_target_height"]).items():
            for column, name in enumerate(model.names):
                if name.startswith(role + "_"):
                    poses[index, column] = model.scene.get_pose(model.dynamic[column])
            counts[action] += 1
            actions.append(
                {"index": index, "video_s": float(data["time_s"][index]), "scene": str(ids[index]), "action": action}
            )
    diff = np.any(poses != data["matrices"], axis=(2, 3))
    columns = np.flatnonzero(np.any(diff, axis=0))
    assert all(model.names[col].startswith(("B_", "C主_")) for col in columns)
    forbidden = [i for i, name in enumerate(model.names) if not name.startswith(("B_", "C主_"))]
    assert np.array_equal(poses[:, forbidden], data["matrices"][:, forbidden])
    assert np.isfinite(poses).all()
    output.parent.mkdir()
    np.savez_compressed(output, **{**data, "matrices": poses})
    with np.load(output, allow_pickle=False) as saved:
        assert saved.files == list(data)
        assert all(np.array_equal(saved[key], poses if key == "matrices" else data[key]) for key in data)
    assert all(probe.sha(Path(path)) == digest for path, digest in pins.items())
    report = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "input_sha256": pins,
        "output_bank": str(output.relative_to(probe.ROOT)),
        "output_sha256": probe.sha(output),
        "changed_samples": int(np.any(diff, axis=1).sum()),
        "changed_columns": [{"column": int(i), "name": model.names[i]} for i in columns],
        "action_sample_counts": dict(counts),
        "actions": actions,
        "schematic_dimensions": dims,
        "product_tools_wires_pallet_assistants_cameras_times_unchanged": True,
        "source_files_unchanged": True,
        "readback_identical": True,
        "position_units": "Dimensionless explanatory coordinates",
        "physical_acceptance_verdict": None,
    }
    record.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"PANEL_DISPLAY_BANK_COMPLETE samples={report['changed_samples']} columns={len(columns)}", flush=True)


if __name__ == "__main__":
    main()
