# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read back the hand review files and their inherited record relationships."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo

from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text())


class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.identifiers = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        row = dict(attrs)
        if row.get("id"):
            self.identifiers.append(row["id"])
        self.links.extend(row[key] for key in ("src", "href") if row.get(key))
        assert tag != "script", "This supplemental review is intentionally static."


def check_data(data):
    source = read(ROOT / "sources/line_review_data.json")
    assert len(data["jobs"]) == len(source["jobs"]) == 20
    for row, original in zip(data["jobs"], source["jobs"], strict=True):
        assert all(row[key] == value for key, value in original.items()), row["id"]
    features = {row["id"] for row in source["feature_review_candidates"]}
    for variant in data["variants"]:
        assert set(variant["features"]) <= features
        assert variant["physical_target_to_job_assignment"] is None
        assert variant["new_gripper_model_selected"] is None
    assert data["working_default"] == read(ROOT / "sources/working_default.json")
    assert data["requirements"] == read(ROOT / "sources/requirements.json")
    assert len(data["families"]) == 8 and len(data["variants"]) == 12
    uncovered = {row["id"]: row["unmatched_families"] for row in data["jobs"] if row["unmatched_families"]}
    assert uncovered == {"D11": ["H05"], "D21": ["H05"], "D61": ["H05"]}
    fuse = next(row for row in data["variants"] if row["id"] == "H08_FUSE")
    assert fuse["unassigned_features"] == ["P22"]
    return uncovered


def main() -> None:
    receipt = ROOT / "qa_receipt.json"
    assert not receipt.exists(), receipt
    manifest = read(OUT / "hand_manifest.json")
    for row in manifest["files"]:
        path = OUT / row["path"]
        assert sha(path) == row["sha256"] and path.stat().st_size == row["bytes"], path
    data = read(OUT / "hand_review_data.json")
    unmatched = check_data(data)
    page = Reader()
    page.feed((OUT / "index.html").read_text())
    assert len(page.identifiers) == len(set(page.identifiers))
    assert all(row["id"] in page.identifiers for row in data["variants"])
    assert all("job-" + row["id"] in page.identifiers for row in data["jobs"])
    for link in page.links:
        url = urlsplit(link)
        assert not url.scheme and not url.netloc
        if url.path == "../index.html":
            assert (ROOT.parent / "hvjb-review-page-v04-20260923/output/index.html").is_file()
        elif url.path:
            assert (OUT / unquote(url.path)).is_file(), link
        if url.fragment:
            assert url.fragment in page.identifiers, link
    images = []
    for path in sorted((OUT / "figures").glob("*.png")):
        with Image.open(path) as image:
            image.load()
            images.append({"file": path.name, "size": image.size, "sha256": sha(path)})
    assert len(images) == 17
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "manifest_sha256": sha(OUT / "hand_manifest.json"),
        "files_read_back": len(manifest["files"]),
        "jobs_preserved": 20,
        "families": 8,
        "application_cards": 12,
        "unmatched_target_specific_family_illustrations": unmatched,
        "P22_stage_selected": False,
        "images": images,
        "figure_observation": (
            "Five reused schematics visually opened; H02 and H08 labels moved away from leaders/arrows."
        ),
        "browser_ui_observed": False,
        "formal_physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("HAND_PAGE_READBACK_COMPLETE jobs=20 families=8 applications=12 images=17", flush=True)


if __name__ == "__main__":
    main()
