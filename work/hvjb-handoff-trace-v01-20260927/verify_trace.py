# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Read back the support display, its provenance, links, and unchanged media."""

import json
import subprocess
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
from zoneinfo import ZoneInfo

from build_trace import DATA, ENTRY, MANIFEST, PARALLEL, PLAN, ROOT, SCRIPT, SOURCE, read_payload, sha


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


def check_links(folder: Path, payload: dict) -> list:
    results = []
    for name in (ENTRY, "hand_review/index_v03.html"):
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
            if url.fragment.startswith(("scene=", "job=", "hold=")):
                key, values = next(iter(parse_qs(url.fragment).items()))
                group = "scenes" if key == "scene" else "jobs"
                assert target.name == ENTRY and values[0] in {row["id"] for row in payload[group]}
            else:
                parsed = Page()
                parsed.feed(target.read_text())
                assert unquote(url.fragment) in parsed.ids, (name, link)
        results.append({"file": name, "links_checked": len(page.links)})
    return results


def verify_data(folder: Path, payload: dict) -> dict:
    trace = read_payload((folder / ENTRY).read_text(), "handoff-trace-data")
    assert trace == json.loads((folder / DATA).read_text())
    assert [row["id"] for row in trace["jobs"]] == [row["id"] for row in payload["jobs"]]
    group_ids = [job for group in trace["groups"] for job in group["jobs"]]
    assert len(group_ids) == len(set(group_ids)) == 20
    assert set(group_ids) == {row["id"] for row in payload["jobs"]}
    assert trace["reservations"] == json.loads(PARALLEL.read_text())["cross_task_reservations_unmodified"]
    assert trace["reservations"][1]["tasks"] == ["D31", "D40", "D42", "D45", "D50"]
    source = {row["id"]: row["source_card_unmodified"] for row in json.loads(PLAN.read_text())["cards"]}
    inherited = []
    for row in trace["jobs"]:
        if row["description_source"] != "hand_plan.source_card_unmodified":
            continue
        for key in ("start_ja", "keep_ja", "end_ja", "reuse_ja"):
            assert row[key] == source[row["id"]][key]
        inherited.append(row["id"])
    assert len(inherited) == 16
    descriptions = " ".join(row[key] for row in trace["jobs"] for key in ("start_ja", "keep_ja", "end_ja", "reuse_ja"))
    assert all(old not in descriptions for old in ("G-OUT", "二段循環", "2段循環"))
    return {"inherited_description_ids": inherited, "current_description_ids": trace["description_overrides"]}


def main() -> None:
    folder = ROOT / "preview"
    source_files = [path for path in SOURCE.rglob("*") if path.is_file()]
    assert len(source_files) == 522
    for path in source_files:
        assert sha(path) == sha(folder / path.relative_to(SOURCE)), path
    manifest = json.loads((folder / MANIFEST).read_text())
    for row in manifest["files"]:
        assert sha(folder / row["path"]) == row["sha256"]
    assert len([path for path in folder.rglob("*") if path.is_file()]) == 529
    page = (folder / ENTRY).read_text()
    original = (SOURCE / "index_v05d_1.html").read_text()
    payload = read_payload(page, "review-data")
    assert payload == read_payload(original, "review-data")
    assert read_payload(page, "hand-usage-data") == read_payload(original, "hand-usage-data")
    facts = verify_data(folder, payload)
    links = check_links(folder, payload)
    subprocess.run(["node", "--check", str(folder / SCRIPT)], check=True)
    videos = list(folder.rglob("*.mp4"))
    assert len(videos) == 1
    assert sha(videos[0]) == "0cdcd4d43831c3f805aa4e5960b666e7965ee6f1ac38b59d31645630d1dd40da"
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "entry_sha256": sha(folder / ENTRY),
        "overlay_manifest_sha256": sha(folder / MANIFEST),
        "unchanged_files": 522,
        "new_files": 7,
        "job_feature_scene_records_unchanged": True,
        "hand_use_records_unchanged": True,
        "support_reservation_records_unchanged": True,
        **facts,
        "links": links,
        "video_count": 1,
        "video_sha256": sha(videos[0]),
        "new_javascript_syntax_passed": True,
        "script_sha256": sha(Path(__file__)),
        "physical_acceptance_verdict": None,
    }
    with (ROOT / "qa_receipt.json").open("x") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print("HANDOFF_TRACE_READBACK unchanged_files=522 new_files=7 jobs=20 video_count=1")


if __name__ == "__main__":
    main()
