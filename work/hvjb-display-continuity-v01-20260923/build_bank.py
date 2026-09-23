# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Copy the saved concept bank and replace only named hand/arm display intervals."""

import json
from collections import Counter

import correct_display as fix
import numpy as np
import probe_saved as probe


def main():
    output = probe.ROOT / "data/concept_display_v05.npz"
    receipt = probe.ROOT / "audit/display_v05_delta.json"
    assert not output.exists() and not receipt.exists()
    assert probe.sha(probe.BANK) == probe.BANK_SHA
    with np.load(probe.BANK, allow_pickle=False) as bank:
        data = {key: bank[key] for key in bank.files}
    matrices = data["matrices"].copy()
    model = fix.old.Model()
    assert model.names == data["object_names"].tolist()
    plan_path = probe.VIDEO / "data/concept_v04.json"
    ids, source_times = probe.sample_scenes(data["time_s"], json.loads(plan_path.read_text()))
    actions, intervals = Counter(), []
    for index, (source_t, scene_id) in enumerate(zip(source_times, ids)):
        for node, matrix in zip(model.dynamic, data["matrices"][index]):
            model.scene.set_pose(node, matrix)
        applied = fix.apply(model, float(source_t), str(scene_id))
        for role, action in applied.items():
            actions[action] += 1
            columns = [column for column, name in enumerate(model.names) if name.startswith(role + "_")]
            for column in columns:
                matrices[index, column] = model.scene.get_pose(model.dynamic[column])
            intervals.append({"sample_index": index, "video_s": float(data["time_s"][index]), "action": action})
    changed = np.any(matrices != data["matrices"], axis=(2, 3))
    changed_columns = np.flatnonzero(np.any(changed, axis=0))
    assert all(model.names[column].startswith(("A_", "B_", "C主_")) for column in changed_columns)
    assert np.array_equal(matrices[:, 50:], data["matrices"][:, 50:])
    data["matrices"] = matrices
    output.parent.mkdir(exist_ok=True)
    np.savez_compressed(output, **data)
    with np.load(output, allow_pickle=False) as saved:
        assert all(np.array_equal(saved[key], value) for key, value in data.items())
    assert probe.sha(probe.BANK) == probe.BANK_SHA
    probe.write(
        receipt,
        {
            "source_bank_sha256": probe.BANK_SHA,
            "output_bank_sha256": probe.sha(output),
            "script_sha256": {
                str(path): probe.sha(path) for path in (probe.ROOT / "correct_display.py", probe.ROOT / "build_bank.py")
            },
            "sample_count": len(matrices),
            "changed_sample_count": int(np.any(changed, axis=1).sum()),
            "changed_object_sample_count": int(changed.sum()),
            "changed_columns": [{"column": int(column), "name": model.names[column]} for column in changed_columns],
            "action_sample_counts": dict(actions),
            "applied_actions": intervals,
            "product_pallet_tools_wire_symbols_unchanged": True,
            "ab_and_c_assistant_unchanged": True,
            "camera_and_time_unchanged": True,
            "old_bank_unchanged": True,
            "physical_units": None,
            "physical_validity_verdict": None,
        },
    )
    print(f"DISPLAY_BANK_COMPLETE changed_samples={np.any(changed, axis=1).sum()} objects={len(changed_columns)}")
    print(dict(actions))


if __name__ == "__main__":
    main()
