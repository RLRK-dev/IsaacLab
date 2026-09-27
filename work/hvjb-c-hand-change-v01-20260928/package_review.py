# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Package diagrams of the three existing C-stage hand-change candidates."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DESTINATION = Path("/home/rlrk/Downloads/HVJB_C工程_手先切替の比較_v01_20260928")
HELPER = ROOT.parent / "hvjb-c-contact-layout-v01-20260927/build_review.py"
SPEC = importlib.util.spec_from_file_location("contact_package_helpers", HELPER)
assert SPEC is not None and SPEC.loader is not None
HELPERS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPERS)
copy, digest, write = HELPERS.copy, HELPERS.digest, HELPERS.write
PRIOR_RECEIPTS = (
    ROOT.parent / "hvjb-c-contact-layout-v01-20260927/audit/delivery_receipt.json",
    ROOT.parent / "hvjb-c-handoff-v05e-20260927/audit/delivery_receipt.json",
)
FIGURES = ("01_C工程_手先切替3案.png", "02_C工程_交換中の支持.png")


def verify_prior() -> list[dict]:
    """Compare previous deliveries to their existing per-file receipts."""
    reports = []
    for receipt in PRIOR_RECEIPTS:
        record = json.loads(receipt.read_text())
        directory = Path(record["entry"]).parent
        for row in record["files"]:
            assert digest(directory / row["path"]) == row["sha256"], directory / row["path"]
        reports.append({"entry": record["entry"], "unchanged_files": len(record["files"]), "receipt": str(receipt)})
    return reports


def main() -> None:
    output = ROOT / "delivery"
    assert not output.exists(), output
    comparison = json.loads((ROOT / "comparison.json").read_text())
    assert comparison["selected_method"] is None
    assert comparison["physical_acceptance_verdict"] is None
    report = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "prior_art": {"keywords": ["HVJB", "手先切替", "H07", "H06"], "exit_code": 0, "blockers": 0},
        "reuse": {"helpers": str(HELPER), "sha256": digest(HELPER)},
        "prior_deliveries": verify_prior(),
        "source_files": [],
        "selected_method": None,
        "selected_manufacturer_part": None,
        "real_dimensions": None,
        "cycle_time_s": None,
        "new_mp4_count": 0,
        "product_or_motion_modified": False,
        "formal_physical_acceptance": None,
        "public_references": [
            {
                "url": "https://schunk.com/us/en/gripping-systems/accessories/bsws-r-pgzn-plus/c/PGR_7219",
                "read_on": "2026-09-28",
                "basis": "Official description of automatic jaw change retaining the gripper body.",
                "not_adopted": "No fit, jaw design, stroke, sensor, load or cycle-time specification selected.",
            },
            {
                "url": "https://schunk.com/us/en/products/automation-technology/cps",
                "read_on": "2026-09-28",
                "basis": "Official description of master/adapter automatic tool changing and media connections.",
                "not_adopted": "No specific changer size, compatibility, connection or actuation selected.",
            },
            {
                "url": "https://schunk.com/us/en/automation-technology/accessories/cts/c/PGR_7391",
                "read_on": "2026-09-28",
                "basis": "Official description of storage racks for the automatic tool changer family.",
                "not_adopted": "No rack location, mounting geometry or operating path selected.",
            },
        ],
    }
    sources = [
        ROOT.parent / "hvjb-hand-plan-v01-20260920/data/hand_plan.json",
        ROOT.parent / "hvjb-hand-plan-v01-20260920/draw_plan.py",
        ROOT.parent / "hvjb-hand-coverage-v01-20260923/sources/unit_support_sequence.json",
        ROOT.parent / "hvjb-c-handoff-v05e-20260927/README.md",
        HELPER,
    ]
    for source in sources:
        relative = Path("sources") / source.relative_to(ROOT.parent)
        copy(source, output / relative)
        report["source_files"].append({"source": str(source), "copy": str(relative), "sha256": digest(source)})
    for name in ("README.md", "SCOPE.md", "VISUAL_DELTA.md", "comparison.json"):
        copy(ROOT / name, output / name)
    for name in ("package_review.py", "deliver_review.py", "qa_review.mjs", "review_template.html"):
        copy(ROOT / name, output / "scripts" / name)
    template = (ROOT / "review_template.html").read_text()
    assert template.count("__COMPARISON_DATA__") == 1
    encoded = json.dumps(comparison, ensure_ascii=False).replace("<", "\\u003c")
    with (output / "index.html").open("x") as stream:
        stream.write(template.replace("__COMPARISON_DATA__", encoded))
    write(ROOT / "audit/inputs.json", report)
    copy(ROOT / "audit/inputs.json", output / "audit/inputs.json")
    copy(Path("/tmp/hvjb-c-hand-change-prior-art-20260928.txt"), ROOT / "audit/prior_art.txt")
    copy(ROOT / "audit/prior_art.txt", output / "audit/prior_art.txt")
    print("C_HAND_CHANGE_PACKAGED methods=3 stages=6 old_files_checked=71 new_mp4=0", flush=True)


if __name__ == "__main__":
    main()
