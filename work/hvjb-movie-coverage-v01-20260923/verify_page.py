# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read back job identities, existing scene assignments and the new review guide."""

from __future__ import annotations

import json
import posixpath
import subprocess
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo

from build_page import LINE, MOVIE, MOVIE_SHA, PLAN, PREVIOUS, ROOT, sha, write_json
from PIL import Image

OUT = ROOT / "output"


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.seek_buttons = []

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if fields.get("id"):
            self.ids.append(fields["id"])
        self.links.extend(fields[key] for key in ("href", "src") if fields.get(key))
        if tag == "button" and "data-seek" in fields:
            self.seek_buttons.append((fields["data-scene"], float(fields["data-seek"])))


def resolve(name):
    if name == "index_v05b_2.html":
        return ROOT / "entry/index_v05b_2.html"
    if name.startswith("coverage_review/"):
        return OUT / name.removeprefix("coverage_review/")
    return PREVIOUS / name


def check_link(link, logical):
    uri = urlsplit(link)
    if uri.scheme or uri.netloc:
        assert uri.scheme == "https" and uri.netloc, link
        return
    name = (
        logical if not uri.path else posixpath.normpath(posixpath.join(posixpath.dirname(logical), unquote(uri.path)))
    )
    assert not name.startswith(("../", "/")), name
    target = resolve(name)
    assert target.is_file(), (logical, link, str(target))
    if uri.fragment:
        parsed = Page()
        parsed.feed(target.read_text())
        assert unquote(uri.fragment) in parsed.ids, (logical, link)


def pages(data):
    records = []
    for logical in ("coverage_review/index.html", "index_v05b_2.html"):
        path = resolve(logical)
        page = Page()
        page.feed(path.read_text())
        assert len(page.ids) == len(set(page.ids)), logical
        for link in page.links:
            check_link(link, logical)
        if logical.startswith("coverage_review/"):
            expected = [(scene["id"], scene["start_s"]) for row in data["jobs"] for scene in row["scenes_unmodified"]]
            assert page.seek_buttons == expected
            assert [key for key in page.ids if key.startswith("D")] == [
                row["job_unmodified"]["id"] for row in data["jobs"]
            ]
        records.append({"page": logical, "sha256": sha(path), "references": len(page.links)})
    return records


def content(data, manifest):
    line = json.loads(LINE.read_text())
    plan = json.loads(PLAN.read_text())
    assert data["line_source_sha256"] == sha(LINE) and data["video_plan_sha256"] == sha(PLAN)
    assert [row["job_unmodified"] for row in data["jobs"]] == line["jobs"]
    assert [row["job_unmodified"]["id"] for row in data["jobs"]] == plan["tasks_preserved"]
    assert data["source_static_task_scenes"] == plan["static_task_scenes"]
    for row in data["jobs"]:
        job = row["job_unmodified"]
        expected = [scene for scene in plan["scenes"] if job["id"] in scene.get("tasks", [])]
        assert row["scenes_unmodified"] == expected
        assert job["scene_ids"] == [scene["id"] for scene in expected]
    for row in manifest["files"]:
        path = OUT / row["path"]
        assert sha(path) == row["sha256"] and path.stat().st_size == row["bytes"]
    assert len(data["jobs"]) == 20
    assert data["static_only_jobs"] == ["D01", "D42", "D61", "D70", "D71"]
    assert sha(PREVIOUS / MOVIE) == MOVIE_SHA
    assert not list(OUT.rglob("*.mp4"))
    with Image.open(OUT / "coverage.png") as image:
        image.load()
        assert image.size == (2000, 1590)


def main():
    receipt = ROOT / "qa_receipt.json"
    assert not receipt.exists(), receipt
    data = json.loads((OUT / "coverage_data.json").read_text())
    manifest = json.loads((OUT / "coverage_manifest.json").read_text())
    content(data, manifest)
    page_records = pages(data)
    assert sha(ROOT / "entry/index_v05b_2.html") == manifest["entry_sha256"]
    js = subprocess.run(["node", "--check", str(OUT / "coverage.js")], capture_output=True, text=True, check=True)
    write_json(
        receipt,
        {
            "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "manifest_sha256": sha(OUT / "coverage_manifest.json"),
            "jobs_preserved": 20,
            "process_scenes_preserved": 16,
            "static_only_jobs": data["static_only_jobs"],
            "schematic_motion_jobs": 15,
            "page_references": page_records,
            "node_syntax_exit_code": js.returncode,
            "browser_ui_observed": False,
            "new_videos": 0,
            "existing_movie_sha256": MOVIE_SHA,
            "physical_validity_verdict": None,
            "script_sha256": sha(ROOT / "verify_page.py"),
        },
    )
    print("COVERAGE_READBACK jobs=20 scene_assignments_unchanged=True static_only=5 new_videos=0", flush=True)


if __name__ == "__main__":
    main()
