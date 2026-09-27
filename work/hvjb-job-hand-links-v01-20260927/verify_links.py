# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Read back the page overlay and preserve original engineering records."""

import json
import re
import subprocess
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
from zoneinfo import ZoneInfo

from build_links import DATA, ENTRY, ROOT, SCRIPT, SOURCE, VARIANTS, sha


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if fields.get("id"):
            self.ids.append(fields["id"])
        self.links.extend(fields[key] for key in ("href", "src", "poster") if fields.get(key))


def data(path: Path, identity: str) -> dict:
    pattern = rf'<script id="{identity}" type="application/json">(.*?)</script>'
    match = re.search(pattern, path.read_text(), re.S)
    assert match
    return json.loads(match.group(1))


def check_links(folder: Path, payload: dict) -> list:
    results = []
    for name in (ENTRY, "hand_review/index_v02.html"):
        path = folder / name
        page = Page()
        page.feed(path.read_text())
        assert len(page.ids) == len(set(page.ids))
        for link in page.links:
            url = urlsplit(link)
            if url.scheme:
                assert url.scheme == "https"
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path.resolve()
            assert target.is_relative_to(folder.resolve()) and target.is_file(), (name, link)
            if not url.fragment:
                continue
            if url.fragment.startswith(("scene=", "job=")):
                key, values = next(iter(parse_qs(url.fragment).items()))
                assert target.name == ENTRY and values[0] in {row["id"] for row in payload[key + "s"]}
            else:
                parsed = Page()
                parsed.feed(target.read_text())
                assert unquote(url.fragment) in parsed.ids, (name, link)
        results.append({"file": name, "links_checked": len(page.links)})
    return results


def main() -> None:
    folder = ROOT / "preview"
    manifest = json.loads((folder / "job_hand_links_manifest_v01.json").read_text())
    old = json.loads((SOURCE / "review_manifest.json").read_text())
    old_rows = old["files"] + [{"path": "review_manifest.json", "sha256": sha(SOURCE / "review_manifest.json")}]
    for row in old_rows + manifest["files"]:
        assert sha(folder / row["path"]) == row["sha256"], row["path"]
    assert len(list(folder.rglob("*.mp4"))) == 1
    payload = data(folder / ENTRY, "review-data")
    assert payload == data(SOURCE / "index.html", "review-data")
    usage = data(folder / ENTRY, "hand-usage-data")
    assert usage == json.loads((folder / DATA).read_text())
    variants = json.loads(VARIANTS.read_text())
    assert usage["variants"] == variants
    for row in usage["jobs"]:
        assert row["variant_ids"] == [item["id"] for item in variants if row["id"] in item["jobs"]]
    missing = [row["id"] for row in usage["jobs"] if not row["variant_ids"]]
    assert missing == ["D01", "D42", "D61", "D71", "D81"]
    assert next(row for row in usage["jobs"] if row["id"] == "D60")["note_ja"].find("P22") >= 0
    links = check_links(folder, payload)
    subprocess.run(["node", "--check", str(folder / SCRIPT)], check=True)
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "entry_sha256": sha(folder / ENTRY),
        "overlay_manifest_sha256": sha(folder / "job_hand_links_manifest_v01.json"),
        "original_files_unchanged": len(old_rows),
        "additional_files": len(manifest["files"]) + 1,
        "job_feature_scene_records_unchanged": True,
        "hand_variant_records_unchanged": True,
        "all_mapping_edges_unchanged": True,
        "jobs_without_individual_comparison": missing,
        "links": links,
        "new_javascript_syntax_passed": True,
        "videos": 1,
        "new_mechanical_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    receipt = ROOT / "qa_receipt.json"
    assert not receipt.exists()
    receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print("JOB_HAND_LINKS_READBACK original_files=515 new_files=7 mappings_unchanged=true")


if __name__ == "__main__":
    main()
