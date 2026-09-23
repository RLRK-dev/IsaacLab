# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Preserve the existing hand requirements, comparison images and drawing helpers."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
MAIN = Path("/home/rlrk/IsaacLab/work")
RUN = Path("/home/rlrk/IsaacLab-op040/eval_runs/ur15_jb_harness_revision_20260907")
LOCAL = ROOT.parent

INPUTS = {
    "requirements.json": MAIN / "hvjb-contour-grasp-v01-20260920/output/grasp_requirements.json",
    "hand_plan.json": LOCAL / "hvjb-hand-plan-v01-20260920/data/hand_plan.json",
    "line_review_data.json": LOCAL / "hvjb-line-progress-20260923/data/line_review_data.json",
    "working_default.json": RUN / "data/hand_working_default_v01.json",
    "provisional_spec.json": RUN / "data/hand_provisional_spec_v01.json",
    "legacy_finger_drawings.py.txt": MAIN / "hvjb-review-v02-20260920/build_finger_drawings.py",
    "H05_outer_README.md": MAIN / "hvjb-contour-grasp-v01-20260920/README.md",
    "H04_README.md": MAIN / "hvjb-covered-crimp-concept-v01-20260920/output/README.md",
    "H06_FC02_README.md": MAIN / "hvjb-pallet-location-v01-20260920/output/README.md",
    "H06_FC01_README.md": MAIN / "hvjb-h06-flange-concept-v01-20260920/output/README.md",
    "unit_support_sequence.json": LOCAL / "hvjb-line-process-v03-20260921/inputs/support_sequence.json",
    "H06_FC02_observations.json": MAIN / "hvjb-pallet-location-v01-20260920/output/pallet_location_observations.json",
    "H05_inner_observations.json": LOCAL / "hvjb-inner-grasp-v01-20260921/output/inner_grasp_review.json",
    "H05_installed_observations.json": LOCAL
    / "hvjb-inner-installed-access-v01-20260921/output/installed_access_observations.json",
}
FIGURES = {
    "H04_side.png": MAIN / "hvjb-review-v02-20260920/figures/H04_side.png",
    "H04_contact.png": MAIN / "hvjb-review-v02-20260920/figures/H04_contact.png",
    "H04_open.png": MAIN / "hvjb-review-v02-20260920/figures/H04_open.png",
    "H05_outer3.png": MAIN / "hvjb-contour-grasp-v01-20260920/figures/P16_after.png",
    "H05_outer2.png": MAIN / "hvjb-contour-grasp-v01-20260920/figures/P17_after.png",
    "H05_outer3_open.png": MAIN / "hvjb-contour-grasp-v01-20260920/figures/P16_opened.png",
    "H05_inner.png": LOCAL / "hvjb-inner-grasp-v01-20260921/figures/oblique.png",
    "H05_inner_hand.png": LOCAL / "hvjb-inner-installed-access-v01-20260921/figures/hand_only.png",
    "H06_case.png": MAIN / "hvjb-pallet-location-v01-20260920/figures/handoff_both.png",
    "H06_case_clear.png": MAIN / "hvjb-pallet-location-v01-20260920/figures/handoff_clear.png",
    "H06_pin_passage.png": MAIN / "hvjb-pallet-location-v01-20260920/figures/backing_pin_passage.png",
    "unit_target_reference.png": LOCAL / "hvjb-line-progress-20260923/figures/product_final/product.png",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    destination = ROOT / "sources"
    assert not destination.exists(), destination
    paths = list(INPUTS.values()) + list(FIGURES.values())
    assert all(path.is_file() for path in paths), [str(path) for path in paths if not path.is_file()]
    before = {path: sha(path) for path in paths}
    destination.mkdir()
    figures = ROOT / "figures"
    figures.mkdir()
    records = []
    for mapping, folder in ((INPUTS, destination), (FIGURES, figures)):
        for name, source in mapping.items():
            target = folder / name
            shutil.copy2(source, target)
            assert sha(target) == before[source]
            records.append({"source": str(source), "copy": str(target.relative_to(ROOT)), "sha256": before[source]})
    assert all(sha(path) == checksum for path, checksum in before.items())
    (destination / "output").mkdir()
    receipt = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "files": records,
        "source_bytes_unchanged": True,
        "script_sha256": sha(Path(__file__)),
    }
    (ROOT / "source_identity.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(f"HAND_SOURCE_COPY_COMPLETE files={len(records)} originals_unchanged=True", flush=True)


if __name__ == "__main__":
    main()
