# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Reuse the v05b renderer for only the 23 changed schematic samples."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / "hvjb-line-video-v05b-20260923"
FIX = ROOT.parent / "hvjb-xyz-display-v01-20260924"
spec = importlib.util.spec_from_file_location("v05b_process_renderer", OLD / "render_review.py")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)


def main() -> None:
    output = ROOT / "changed_pngs"
    assert not output.exists()
    delta = json.loads((FIX / "audit/display_delta.json").read_text())
    bank = FIX / delta["output_bank"]
    assert previous.view.sha(bank) == delta["output_bank_sha256"]
    plan = json.loads((OLD / "data/concept_v05b.json").read_text())
    with np.load(OLD / "data" / plan["motion"], allow_pickle=False) as saved:
        before = saved["matrices"]
    with np.load(bank, allow_pickle=False) as saved:
        changed = np.flatnonzero(np.any(before != saved["matrices"], axis=(1, 2, 3)))
    assert len(changed) == delta["changed_samples"] == 23
    pins = {
        **plan["input_sha256"],
        str(FIX / "audit/display_delta.json"): previous.view.sha(FIX / "audit/display_delta.json"),
        str(bank): previous.view.sha(bank),
        str(Path(__file__)): previous.view.sha(Path(__file__)),
    }
    assert all(previous.view.sha(Path(path)) == digest for path, digest in pins.items())
    subset = {**plan, "expected_source_samples": [plan["expected_source_samples"][index] for index in changed]}
    output.mkdir()
    rows, omissions, text_count = previous.render(bank, subset, changed, output)
    assert all(previous.view.sha(Path(path)) == digest for path, digest in pins.items())
    previous.view.save(
        output / "manifest.json",
        {
            "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "source_sha256": pins,
            "changed_indices": changed.tolist(),
            "images": rows,
            "display_nodes_omitted": omissions,
            "text_elements_checked": text_count,
            "all_other_main_pngs_reused": True,
            "physical_acceptance_verdict": None,
        },
    )
    print("V05C_CHANGED_PNGS_COMPLETE frames=23 same_v05b_scene_and_camera=True", flush=True)


if __name__ == "__main__":
    main()
