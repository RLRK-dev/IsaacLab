# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Widen the schematic S12 framing without changing any displayed object pose."""

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
CORRECTION = ROOT.parent / "hvjb-display-continuity-v01-20260923"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = CORRECTION / "data/concept_display_v05.npz"
    output = ROOT / "data/concept_display_v05_framed.npz"
    receipt = ROOT / "audit/camera_framing.json"
    assert not output.exists() and not receipt.exists()
    delta = json.loads((CORRECTION / "audit/display_v05_delta.json").read_text())
    assert sha(source) == delta["output_bank_sha256"]
    with np.load(source, allow_pickle=False) as saved:
        data = {key: saved[key] for key in saved.files}
    original_span = data["span"].copy()
    mask = (data["time_s"] >= 85) & (data["time_s"] < 93)
    assert mask.sum() == 120
    assert np.all(original_span[mask] == 1.30)
    data["span"][mask] = 1.85
    np.savez_compressed(output, **data)
    with np.load(source, allow_pickle=False) as original, np.load(output, allow_pickle=False) as final:
        unchanged = [key for key in original.files if np.array_equal(original[key], final[key])]
        assert set(unchanged) == set(original.files) - {"span"}
    records = {
        "source_sha256": sha(source),
        "output_sha256": sha(output),
        "scene": "S12",
        "video_interval_s": [85, 93],
        "changed_samples": int(mask.sum()),
        "old_orthographic_half_width_display_units": 1.30,
        "new_orthographic_half_width_display_units": 1.85,
        "unchanged_arrays": unchanged,
        "reason": "In preview01 the C main hand at the busbar supply approached the image top; widen the view.",
        "physical_camera_specification": None,
        "physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    receipt.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    print("CAMERA_FRAME_COMPLETE S12=120_samples span=1.30_to_1.85 object_matrices_unchanged=true")


if __name__ == "__main__":
    main()
