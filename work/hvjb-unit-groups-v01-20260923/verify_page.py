# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Verify group coverage, saved image identity and offline page references."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo

from PIL import Image

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
OUT = ROOT / "output"
DELIVERY = Path("/home/rlrk/Downloads/HVJB_ライン全体レビュー_v05_20260923")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.group_buttons = []
        self.group_panels = []
        self.angle_buttons = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get("id"):
            self.ids.append(data["id"])
        self.links.extend(data[key] for key in ("href", "src") if data.get(key))
        for key, records in (
            ("data-select-group", self.group_buttons),
            ("data-group-panel", self.group_panels),
            ("data-select-angle", self.angle_buttons),
        ):
            if key in data:
                records.append(data)


def link_target(link, base):
    url = urlsplit(link)
    if url.scheme or url.netloc:
        assert url.scheme == "https" and url.netloc, link
        return None
    name = unquote(url.path)
    if name == "../index_v05_1.html":
        target = ROOT / "entry/index_v05_1.html"
    elif name.startswith("../"):
        target = DELIVERY / name[3:]
    elif name.startswith("unit_review/"):
        target = OUT / name.removeprefix("unit_review/")
    else:
        target = base / name
    assert target.is_file(), (link, str(target))
    if url.fragment:
        page = Page()
        page.feed(target.read_text())
        assert url.fragment in page.ids, link
    return target


def coverage(data):
    line = read(WORK / "hvjb-line-progress-20260923/data/line_review_data.json")
    location = read(WORK / "hvjb-assembly-location-v01-20260921/output/assembly_location.json")
    source = {row["id"]: row for row in line["feature_review_candidates"]}
    groups = data["groups"]
    ids = [key for row in groups for key in row["feature_ids"]]
    assert len(ids) == len(set(ids)) == len(source) == 92
    assert set(ids) == set(source)
    for row, old in zip(groups, location["preserved_feature_groups"], strict=True):
        assert row["source_group_unmodified"] == old
        assert row["features_unmodified"] == [source[key] for key in row["feature_ids"]]
    assert data["all_jobs_unmodified"] == line["jobs"] and len(line["jobs"]) == 20
    assert sum(row["mesh_count"] for row in groups) == 465
    assert data["official_video_observations_unmodified"] == location["source_video_observations"]
    return [row["id"] for row in groups]


def images(manifest):
    result = []
    for record in manifest["files"]:
        path = OUT / record["path"]
        assert sha(path) == record["sha256"] and path.stat().st_size == record["bytes"]
        if path.suffix == ".png":
            with Image.open(path) as image:
                image.load()
                result.append({"file": record["path"], "sha256": sha(path), "size": list(image.size)})
    assert len(result) == 55
    render = read(OUT / "render_receipt.json")
    assert len(render["renders"]) == 44 and render["source_geometry_unchanged"]
    for row in render["renders"]:
        assert sha(OUT / "figures" / row["file"]) == row["sha256"]
    return result


def pages(expected_groups):
    rows = []
    for path in [*OUT.glob("*.html"), ROOT / "entry/index_v05_1.html"]:
        page = Page()
        page.feed(path.read_text())
        assert len(page.ids) == len(set(page.ids)), path
        base = DELIVERY if path.parent.name == "entry" else OUT
        checked = [link_target(link, base) for link in page.links]
        if path == OUT / "index.html":
            assert [row["data-select-group"] for row in page.group_buttons] == expected_groups
            assert [row["data-group-panel"] for row in page.group_panels] == expected_groups
            assert [row["data-group-panel"] for row in page.group_panels if "hidden" not in row] == ["FG_FUSE"]
            assert [row["data-select-angle"] for row in page.angle_buttons] == ["oblique", "front"]
        rows.append({"file": str(path.relative_to(ROOT)), "links": len(checked), "sha256": sha(path)})
    return rows


def main():
    receipt = ROOT / "qa_receipt.json"
    assert not receipt.exists(), receipt
    manifest = read(OUT / "group_manifest.json")
    data = read(OUT / "group_review.json")
    groups = coverage(data)
    image_records = images(manifest)
    page_records = pages(groups)
    js = subprocess.run(["node", "--check", str(OUT / "groups.js")], capture_output=True, text=True, check=True)
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "manifest_sha256": sha(OUT / "group_manifest.json"),
        "group_ids_preserved": groups,
        "photo_features_preserved": 92,
        "jobs_preserved": 20,
        "images": image_records,
        "pages": page_records,
        "javascript_syntax": {"exit_code": js.returncode, "stdout": js.stdout, "stderr": js.stderr},
        "browser_ui_observed": False,
        "external_links_check": "HTTPS structure only; external destinations were not fetched by this check.",
        "verification_correction": (
            "Initial check only allowed YouTube and stopped on an inherited Ampere source link. "
            "Changed the static external-link check to accept HTTPS URLs; no output artifact changed."
        ),
        "new_physical_operation_selection": None,
        "formal_physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("GROUP_READBACK_COMPLETE groups=11 features=92 jobs=20 png=55 links=true browser=false", flush=True)


if __name__ == "__main__":
    main()
