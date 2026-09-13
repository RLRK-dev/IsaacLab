# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Package the finger-held fastening workflow without loading a robot scene."""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from build_hand_function_review_v01 import file_sha256

REVISION = Path(__file__).resolve().parents[1]
CONFIG = "data/hand_held_fastening_v01.json"
TEMPLATE = "scripts/hand_held_fastening_viewer_v01.html"
DOCUMENT = "analysis/hand_held_fastening_v01.md"
PAGE = "フィンガ保持締結_工程案_v01.html"


def main() -> None:
    """Write a fresh offline workflow page and record the preserved inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise FileExistsError(output)
    paths = [
        CONFIG,
        TEMPLATE,
        DOCUMENT,
        "scripts/build_hand_held_fastening_review_v01.py",
        "scripts/build_hand_function_review_v01.py",
        "analysis/hand_terminal_3d_review_v01.md",
        "data/hand_terminal_concepts_v01.json",
    ]
    before = {name: file_sha256(REVISION / name) for name in paths}
    config = json.loads((REVISION / CONFIG).read_text())
    template = (REVISION / TEMPLATE).read_text()
    if template.count("__REVIEW_DATA__") != 1:
        raise ValueError("Expected exactly one data placeholder")
    output.mkdir(parents=True)
    for name in paths:
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REVISION / name, destination)
    packed = json.dumps(config, ensure_ascii=False).replace("<", "\\u003c")
    page = output / PAGE
    page.write_text(template.replace("__REVIEW_DATA__", packed))
    shutil.copy2(REVISION / DOCUMENT, output / "フィンガ保持締結_工程案_v01.md")
    if before != {name: file_sha256(REVISION / name) for name in paths}:
        raise RuntimeError("Read-only input changed during packaging")
    audit = {
        "observed_at": datetime.now().astimezone().isoformat(),
        "scope": "documentation and role diagram only",
        "input_sha256": before,
        "inputs_unchanged": True,
        "page_sha256": file_sha256(page),
        "diagram_steps": len(config["steps"]),
        "candidate_counts": config["comparison_candidate"],
        "station_redistribution_selected": False,
        "scene_loaded": False,
        "physical_acceptance_verdict": None,
    }
    (output / "audit").mkdir()
    (output / "audit/hand_held_fastening_build_v01.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n"
    )
    print(
        json.dumps({"page": str(page), "steps": audit["diagram_steps"], "inputs_unchanged": True}, ensure_ascii=False)
    )
    print("HAND_HELD_FASTENING_REVIEW_DONE")


if __name__ == "__main__":
    main()
