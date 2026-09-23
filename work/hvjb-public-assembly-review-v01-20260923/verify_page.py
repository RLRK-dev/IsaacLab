# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Verify source identity, unchanged observations, full-frame resizing and links."""

from __future__ import annotations

import json
import posixpath
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo

from build_page import FRAME_JOBS, LOCATION, MOVIE, MOVIE_SHA, PREVIOUS, REFERENCE_ROOT, ROOT, sha, write_json
from PIL import Image, ImageChops

OUT = ROOT / "output"


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.markers = 0

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if fields.get("id"):
            self.ids.append(fields["id"])
        self.links.extend(fields[key] for key in ("href", "src") if fields.get(key))
        if tag == "circle":
            self.markers += 1


def resolve(name):
    if name == "index_v05b_1.html":
        return ROOT / "entry/index_v05b_1.html"
    if name.startswith("public_review/"):
        return OUT / name.removeprefix("public_review/")
    return PREVIOUS / name


def pages():
    records = []
    for logical in ("public_review/index.html", "index_v05b_1.html"):
        path = resolve(logical)
        page = Page()
        page.feed(path.read_text())
        assert len(page.ids) == len(set(page.ids)), logical
        for link in page.links:
            uri = urlsplit(link)
            if uri.scheme or uri.netloc:
                assert uri.scheme == "https" and uri.netloc, link
                continue
            name = (
                logical
                if not uri.path
                else posixpath.normpath(posixpath.join(posixpath.dirname(logical), unquote(uri.path)))
            )
            assert not name.startswith(("../", "/")), name
            target = resolve(name)
            assert target.is_file(), (logical, link, str(target))
            if uri.fragment:
                parsed = Page()
                parsed.feed(target.read_text())
                assert unquote(uri.fragment) in parsed.ids, (logical, link)
        records.append({"page": logical, "sha256": sha(path), "references_checked": len(page.links)})
    return records


def content(data, manifest):
    source = json.loads(LOCATION.read_text())
    assert data["all_jobs_unmodified"] == source["task_locations"]
    assert len(data["all_jobs_unmodified"]) == 20
    assert [row["id"] for row in data["frames"]] == list(FRAME_JOBS)
    assert data["source_video_unmodified"] == source["source_video"]
    records = []
    for row in data["frames"]:
        original = row["source_frame_unmodified"]
        raw = REFERENCE_ROOT / original["file"]
        image = OUT / row["display_image"]
        assert sha(raw) == original["sha256"]
        assert sha(image) == row["display_image_sha256"]
        assert row["observation_unmodified"] == next(
            item for item in source["source_video_observations"] if item["frame"] == row["id"]
        )
        assert row["related_jobs_unmodified"] == [
            item for item in source["task_locations"] if item["id"] in FRAME_JOBS[row["id"]]
        ]
        with Image.open(raw) as before, Image.open(image) as after:
            expected = before.convert("RGB").resize((1200, 675), Image.Resampling.LANCZOS)
            assert after.size == (1200, 675)
            assert ImageChops.difference(expected, after).getbbox() is None
        records.append({"frame": row["id"], "source_sha256": sha(raw), "display_sha256": sha(image)})
    for row in manifest["files"]:
        path = OUT / row["path"]
        assert sha(path) == row["sha256"] and path.stat().st_size == row["bytes"]
        assert path.stat().st_size < 2 * 1024 * 1024, path
    assert not list(OUT.rglob("*.mp4"))
    assert sha(PREVIOUS / MOVIE) == MOVIE_SHA
    return records


def main():
    receipt = ROOT / "qa_receipt.json"
    assert not receipt.exists(), receipt
    data = json.loads((OUT / "evidence_data.json").read_text())
    manifest = json.loads((OUT / "evidence_manifest.json").read_text())
    image_records = content(data, manifest)
    page_records = pages()
    assert sha(ROOT / "entry/index_v05b_1.html") == manifest["entry_sha256"]
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "manifest_sha256": sha(OUT / "evidence_manifest.json"),
        "observations_preserved": 6,
        "jobs_preserved": 20,
        "full_frame_resize_pixel_readback": image_records,
        "page_references": page_records,
        "browser_ui_observed": False,
        "new_videos": 0,
        "existing_movie_sha256": MOVIE_SHA,
        "physical_validity_verdict": None,
        "script_sha256": sha(ROOT / "verify_page.py"),
    }
    write_json(receipt, record)
    print("PUBLIC_ASSEMBLY_READBACK observations=6 jobs=20 resized_frames=6 new_videos=0", flush=True)


if __name__ == "__main__":
    main()
