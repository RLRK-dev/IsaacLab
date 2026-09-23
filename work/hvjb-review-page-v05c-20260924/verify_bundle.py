# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read back the portable package, original job records and appended review-scene links."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
from zoneinfo import ZoneInfo

from build_bundle import DATA_PATTERN, EXTRA_SCENES, MOVIE, PREVIOUS, ROOT, sha
from PIL import Image


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links = [], []

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if fields.get("id"):
            self.ids.append(fields["id"])
        self.links.extend(fields[key] for key in ("href", "src", "poster") if fields.get(key))


def payload(path: Path) -> dict:
    match = re.search(DATA_PATTERN, path.read_text(), re.S)
    assert match
    return json.loads(match.group(2))


def check_data(out: Path) -> dict:
    before, after = payload(PREVIOUS / "index_v05b_2.html"), payload(out / "index.html")
    saved = json.loads((out / "data/line_review_data_v05c.json").read_text())
    assert after == saved and after["features"] == before["features"]
    assert after["scenes"][:18] == before["scenes"] and len(after["scenes"]) == 22
    expected_additions = {}
    for identity, _, _, _, job, _ in EXTRA_SCENES:
        expected_additions.setdefault(job, []).append(identity)
    for old, new in zip(before["jobs"], after["jobs"], strict=True):
        expected = {**old, "scene_ids": old["scene_ids"] + expected_additions.get(old["id"], [])}
        assert new == expected
    assert len(after["jobs"]) == 20 and len(after["features"]) == 92 and after["duration_s"] == 155.2
    ids = {row["id"] for row in after["scenes"]}
    assert all(set(row["scene_ids"]) <= ids for row in after["jobs"])
    for feature in after["features"]:
        for key in ("context_image", "isolated_image"):
            assert (out / feature[key]).is_file()
    return after


def check_links(out: Path, scenes: set[str]) -> tuple[list, list]:
    results, external = [], []
    for path in sorted(out.rglob("*.html")):
        page = Page()
        page.feed(path.read_text())
        assert len(page.ids) == len(set(page.ids)), path
        for link in page.links:
            uri = urlsplit(link)
            if uri.scheme or uri.netloc:
                assert uri.scheme == "https", (path, link)
                external.append(link)
                continue
            target = (path.parent / unquote(uri.path)).resolve() if uri.path else path.resolve()
            assert target.is_relative_to(out.resolve()) and target.is_file(), (path, link)
            if not uri.fragment:
                continue
            if uri.fragment.startswith("scene="):
                assert target.name == "index.html" and parse_qs(uri.fragment)["scene"][0] in scenes
                continue
            parsed = Page()
            parsed.feed(target.read_text())
            assert unquote(uri.fragment) in parsed.ids, (path, link)
        results.append({"path": str(path.relative_to(out)), "local_and_external_links": len(page.links)})
    return results, sorted(set(external))


def main() -> None:
    receipt, out = ROOT / "qa_receipt.json", ROOT / "output"
    assert not receipt.exists()
    manifest = json.loads((out / "review_manifest.json").read_text())
    for row in manifest["files"]:
        file = out / row["path"]
        assert file.stat().st_size == row["bytes"] and sha(file) == row["sha256"], file
    assert len(manifest["files"]) == manifest["file_count"]
    assert len(list(out.rglob("*.mp4"))) == 1 and manifest["mp4_files"] == [MOVIE]
    assert sha(out / MOVIE) == manifest["video_sha256"]
    data = check_data(out)
    pages, external = check_links(out, {row["id"] for row in data["scenes"]})
    scripts = []
    for path in sorted(out.rglob("*.js")):
        result = subprocess.run(["node", "--check", str(path)], check=True, capture_output=True, text=True)
        scripts.append({"path": str(path.relative_to(out)), "exit_code": result.returncode})
    images = 0
    for path in out.rglob("*"):
        if path.suffix.lower() in (".png", ".jpg", ".jpeg"):
            with Image.open(path) as image:
                image.load()
            images += 1
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "manifest_sha256": sha(out / "review_manifest.json"),
        "files_read_back": manifest["file_count"] + 1,
        "jobs": 20,
        "features": 92,
        "original_scenes": 18,
        "appended_local_review_scenes": 4,
        "duration_s": 155.2,
        "job_changes_only_additional_review_scene_links": expected_changes(),
        "html_pages": pages,
        "javascript_syntax": scripts,
        "images_decoded": images,
        "external_references_not_refetched": external,
        "mp4_files": [MOVIE],
        "video_sha256": manifest["video_sha256"],
        "browser_ui_observed": False,
        "browser_qa_recorded_separately": True,
        "formal_physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(
        f"V05C_PACKAGE_READBACK files={record['files_read_back']} html={len(pages)} images={images} mp4=1", flush=True
    )


def expected_changes() -> dict:
    return {"D00": ["H06_loading"], "D80": ["H06_pickup"], "D50": ["H05_P16", "H05_P17"]}


if __name__ == "__main__":
    main()
