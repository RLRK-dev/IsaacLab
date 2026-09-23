# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Read back diagram identity, preserved data, links and standalone callbacks."""

from __future__ import annotations

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo

from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
DELIVERY = Path("/home/rlrk/Downloads/HVJB_ライン全体と組立場所_v04_20260923")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get("id"):
            self.ids.append(data["id"])
        self.links.extend(data[key] for key in ("href", "src") if data.get(key))


def verify_link(link):
    url = urlsplit(link)
    assert not url.scheme and not url.netloc, link
    name = unquote(url.path)
    path = DELIVERY / name[3:] if name.startswith("../") else OUT / name
    assert path.is_file(), link
    if url.fragment:
        page = Page()
        page.feed(path.read_text())
        assert url.fragment in page.ids, link


def preserved_data(data):
    historical = read(ROOT / "data/historical_sharing_source.json")
    original = next(row for row in historical["plans"] if row["id"] == "S5_AB")
    current = read(ROOT.parent / "hvjb-line-progress-20260923/data/line_review_data.json")
    assert sha(ROOT / "data/historical_sharing_source.json") == data["source_identity"]["historical"]["sha256"]
    assert len(data["scenarios"]) == len(original["scenarios"]) == 8
    for row, source in zip(data["scenarios"], original["scenarios"], strict=True):
        assert all(row[key] == value for key, value in source.items()), row["id"]
    assert data["jobs_unmodified"] == current["jobs"] and len(data["jobs_unmodified"]) == 20
    assert data["role_selection_unmodified"] == current["role_selection_unmodified"]
    assert data["logistics_unmodified"] == current["logistics_unmodified"]
    assert data["cross_task_reservations_unmodified"] == original["cross_task_reservations"]
    assert data["time_values_s"] is None and data["new_physical_assignment"] is None
    assert data["physical_acceptance_verdict"] is None and data["motion_generated"] is False


def main():
    receipt = ROOT / "qa_receipt.json"
    assert not receipt.exists(), receipt
    manifest = read(OUT / "parallel_manifest.json")
    for row in manifest["files"]:
        path = OUT / row["path"]
        assert sha(path) == row["sha256"] and path.stat().st_size == row["bytes"]
    data = read(OUT / "parallel_review_data.json")
    preserved_data(data)
    for path in OUT.glob("*.html"):
        page = Page()
        page.feed(path.read_text())
        assert len(page.ids) == len(set(page.ids)), path
        for link in page.links:
            verify_link(link)
    images = []
    for path in sorted((OUT / "figures").glob("*.png")):
        with Image.open(path) as image:
            image.load()
            images.append({"path": str(path.relative_to(OUT)), "size": list(image.size), "sha256": sha(path)})
    assert len(images) == 10
    for path in (OUT / "figures").glob("*.svg"):
        ET.parse(path)
    callback = subprocess.run(
        ["node", str(ROOT / "verify_interactions.js")], check=True, capture_output=True, text=True
    )
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "manifest_sha256": sha(OUT / "parallel_manifest.json"),
        "cases_preserved": 8,
        "jobs_preserved": 20,
        "same_arm_request_overlap_cases": ["AB", "ABC"],
        "images": images,
        "node_callbacks": {"stdout": callback.stdout, "stderr": callback.stderr, "exit_code": callback.returncode},
        "visual_observation": "10 final PNGs opened as a contact sheet; handoff/reservation opened at full size.",
        "browser_ui_observed": False,
        "physical_validity_verdict": None,
        "code_sha256": {path.name: sha(path) for path in (Path(__file__), ROOT / "verify_interactions.js")},
    }
    receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print("PARALLEL_READBACK_COMPLETE cases=8 jobs=20 images=10 links=true callbacks=true browser=false", flush=True)


if __name__ == "__main__":
    main()
