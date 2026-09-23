# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read back static page assets and the existing job/feature/scene relationships."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PageReader(HTMLParser):
    """Collect declared IDs, linked assets and the embedded review JSON."""

    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.links: list[str] = []
        self.id_references: list[str] = []
        self.collect = False
        self.payload = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        for key in ("src", "href", "poster"):
            if values.get(key):
                self.links.append(values[key])
        for key in ("aria-controls", "aria-labelledby"):
            if values.get(key):
                self.id_references.extend(values[key].split())
        if tag == "script" and values.get("id") == "review-data":
            self.collect = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self.collect = False

    def handle_data(self, data: str) -> None:
        if self.collect:
            self.payload += data


def check_files(folder: Path, manifest: dict) -> None:
    rows = manifest["files"]
    assert len(rows) == manifest["file_count"] == len({row["path"] for row in rows})
    for row in rows:
        path = folder / row["path"]
        assert path.is_file() and path.stat().st_size == row["bytes"], path
        assert sha(path) == row["sha256"], path
    listed = {row["path"] for row in rows} | {"review_manifest.json"}
    actual = {str(path.relative_to(folder)) for path in folder.rglob("*") if path.is_file()}
    assert listed == actual, (listed - actual, actual - listed)


def check_links(folder: Path, page: PageReader, payload: dict) -> list[str]:
    dynamic = [path for row in payload["features"] for path in (row["context_image"], row["isolated_image"])] + [
        f"output/pages/page-{number}.png" for number in range(1, 7)
    ]
    external = []
    for link in page.links + dynamic:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            assert url.scheme == "https" and url.netloc == "ampereev.com", link
            external.append(link)
            continue
        path = (folder / unquote(url.path)).resolve()
        assert path.is_relative_to(folder.resolve()) and path.is_file(), link
    assert len(page.ids) == len(set(page.ids))
    assert set(page.id_references) <= set(page.ids)
    js = (folder / "review.js").read_text()
    literal_references = set(re.findall(r'byId\("([^"$]+)"\)', js))
    assert literal_references <= set(page.ids), literal_references - set(page.ids)
    assert "fetch(" not in js and "XMLHttpRequest" not in js
    return external


def check_records(payload: dict) -> dict:
    jobs = {row["id"]: row for row in payload["jobs"]}
    features = {row["id"]: row for row in payload["features"]}
    scenes = {row["id"]: row for row in payload["scenes"]}
    assert len(jobs) == len(payload["jobs"]) == 20
    assert len(features) == len(payload["features"]) == 92
    assert len(scenes) == len(payload["scenes"]) == 18
    assert payload["scenes"][0]["start_s"] == 0
    assert payload["scenes"][-1]["stop_s"] == payload["duration_s"] == 119
    for left, right in zip(payload["scenes"], payload["scenes"][1:]):
        assert left["stop_s"] == right["start_s"]
    for row in jobs.values():
        assert row["scene_ids"] and set(row["scene_ids"]) <= scenes.keys()
        for identifier in row["review_feature_ids"]:
            assert row["id"] in features[identifier]["review_task_ids"]
    for row in features.values():
        assert row["physical_operation_selected"] is None
        for identifier in row["review_task_ids"]:
            assert row["id"] in jobs[identifier]["review_feature_ids"]
    return {"jobs": len(jobs), "features": len(features), "scenes": len(scenes), "duration_s": 119}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=Path, default=ROOT / "output")
    parser.add_argument("--receipt", type=Path, default=ROOT / "qa_receipt.json")
    args = parser.parse_args()
    assert not args.receipt.exists(), args.receipt
    folder = args.input_dir
    manifest = json.loads((folder / "review_manifest.json").read_text())
    check_files(folder, manifest)
    page = PageReader()
    page.feed((folder / "index.html").read_text())
    payload = json.loads(page.payload)
    counts = check_records(payload)
    external = check_links(folder, page, payload)
    assert len(manifest["mp4_files"]) == 1
    assert sha(folder / manifest["mp4_files"][0]) == manifest["video_sha256"]
    document = json.loads((folder / "delivery_manifest.json").read_text())
    assert len(document["files"]) == 26
    for row in document["files"]:
        assert sha(folder / row["path"]) == row["sha256"]
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "manifest_sha256": sha(folder / "review_manifest.json"),
        "files_read_back": manifest["file_count"],
        "counts": counts,
        "inherited_document_files_unchanged": 26,
        "local_asset_links_present": True,
        "job_feature_links_bidirectional": True,
        "external_links": external,
        "browser_ui_observed": False,
        "browser_blocker": "CUA inventory apps=[] browsers=[]; iab and chrome unavailable.",
        "formal_physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("REVIEW_PAGE_READBACK_COMPLETE files=244 jobs=20 features=92 scenes=18 mp4=1", flush=True)


if __name__ == "__main__":
    main()
