# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Replay the new display bank with the preserved main-process renderer and cameras."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from build_motion import ROOT, WORK, load_module, sha, write

PREVIEW = np.array([630, 660, 750, 763, 779, 788, 809, 819, 825, 920, 932, 945])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    output = ROOT / "previews" / ("c_preview" if args.preview else "main")
    assert not output.exists()
    delta = json.loads((ROOT / "audit/motion_delta.json").read_text())
    bank = ROOT / "data/concept_v05e.npz"
    assert sha(bank) == delta["output_sha256"]
    pins = {**delta["input_sha256"], str(bank): sha(bank), str(Path(__file__)): sha(Path(__file__))}
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    old = load_module("c_existing_renderer", WORK / "hvjb-line-video-v05b-20260923/render_review.py")
    plan = json.loads((WORK / "hvjb-line-video-v05b-20260923/data/concept_v05b.json").read_text())
    indices = PREVIEW if args.preview else np.arange(1785)
    subset = {**plan, "expected_source_samples": [plan["expected_source_samples"][int(index)] for index in indices]}
    output.mkdir(parents=True)
    rows, omissions, text_count = old.render(bank, subset, indices, output)
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    write(
        output / "manifest.json",
        {
            "complete": True,
            "preview_only": args.preview,
            "input_sha256": pins,
            "bank_sha256": sha(bank),
            "images": rows,
            "existing_camera_unchanged": True,
            "display_nodes_omitted": omissions,
            "text_elements_checked": text_count,
            "physical_acceptance_verdict": None,
        },
    )
    print(f"C_MAIN_RENDER_COMPLETE frames={len(rows)} preview={args.preview}", flush=True)


if __name__ == "__main__":
    main()
