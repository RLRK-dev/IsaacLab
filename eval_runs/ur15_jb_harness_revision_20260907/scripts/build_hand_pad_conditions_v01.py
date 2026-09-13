# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Package the pad-compliance comparison without changing scene or force settings."""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from build_hand_function_review_v01 import file_sha256

REVISION = Path(__file__).resolve().parents[1]
CONFIG = "data/hand_pad_conditions_v01.json"
TEMPLATE = "scripts/hand_pad_conditions_viewer_v01.html"
DOCUMENT = "analysis/hand_pad_conditions_v01.md"
PAGE = "パッド追従と保持力条件_v01.html"


def main() -> None:
    """Write a new offline explanation and preserve its measurement inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise FileExistsError(output)
    config = json.loads((REVISION / CONFIG).read_text())
    source = REVISION / config["source_audit"]
    assert file_sha256(source) == config["source_audit_sha256"]
    observation = json.loads(source.read_text())
    assert observation["candidates"]["D40"]["setback_m"] == config["baseline"]["initial_body_setback_m"]
    assert config["actual_force_command"] is None
    assert all(value is None for value in config["actual_contact_force_targets_n"].values())
    assert all(row["value"] is None for row in config["required_inputs"])
    paths = [
        CONFIG,
        TEMPLATE,
        DOCUMENT,
        config["source_audit"],
        "scripts/build_hand_pad_conditions_v01.py",
        "scripts/build_hand_function_review_v01.py",
        "data/hand_root_clamp_v03.json",
    ]
    before = {name: file_sha256(REVISION / name) for name in paths}
    template = (REVISION / TEMPLATE).read_text()
    assert template.count("__REVIEW_DATA__") == 1
    output.mkdir(parents=True)
    for name in paths:
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REVISION / name, destination)
    packed = json.dumps(config, ensure_ascii=False).replace("<", "\\u003c")
    page = output / PAGE
    page.write_text(template.replace("__REVIEW_DATA__", packed))
    shutil.copy2(REVISION / DOCUMENT, output / "パッド追従と保持力条件_v01.md")
    assert before == {name: file_sha256(REVISION / name) for name in paths}
    audit = {
        "observed_at": datetime.now().astimezone().isoformat(),
        "scope": "comparison document, illustrative normalized reaction sharing and unfilled input register",
        "input_sha256": before,
        "inputs_unchanged": True,
        "page_sha256": file_sha256(page),
        "unfilled_inputs": len(config["required_inputs"]),
        "force_targets_unset": True,
        "material_unselected": config["material_references"]["selected_material"] is None,
        "scene_loaded": False,
        "arm_motion_created": False,
        "physical_acceptance_verdict": None,
    }
    (output / "audit/hand_pad_conditions_build_v01.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps({"page": str(page), "unfilled_inputs": audit["unfilled_inputs"]}, ensure_ascii=False))
    print("HAND_PAD_CONDITIONS_REVIEW_DONE")


if __name__ == "__main__":
    main()
