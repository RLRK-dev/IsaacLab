# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Append the job-to-movie guide while preserving every delivered v05b file."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo

from build_page import MOVIE, MOVIE_SHA, PREVIOUS, ROOT, sha, write_json


def snapshot(folder):
    return {str(path.relative_to(folder)): sha(path) for path in sorted(folder.rglob("*")) if path.is_file()}


def planned_files():
    out = ROOT / "output"
    qa = json.loads((ROOT / "qa_receipt.json").read_text())
    visual = json.loads((ROOT / "visual_observations.json").read_text())
    assert qa["manifest_sha256"] == sha(out / "coverage_manifest.json")
    assert qa["process_scenes_preserved"] == 16 and qa["jobs_preserved"] == 20
    assert visual["diagram_inspected"] and visual["job_rows_inspected"] == 20
    manifest = json.loads((out / "coverage_manifest.json").read_text())
    for row in manifest["files"]:
        assert sha(out / row["path"]) == row["sha256"], row["path"]
    files = [
        (path, "coverage_review/" + str(path.relative_to(out))) for path in sorted(out.rglob("*")) if path.is_file()
    ]
    files.extend(
        [
            (ROOT / "qa_receipt.json", "coverage_review/qa_receipt.json"),
            (ROOT / "visual_observations.json", "coverage_review/visual_observations.json"),
            (ROOT / "entry/index_v05b_2.html", "index_v05b_2.html"),
        ]
    )
    assert not any(path.suffix == ".mp4" for path, _ in files)
    return files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    files = planned_files()
    before = snapshot(PREVIOUS)
    assert before[MOVIE] == MOVIE_SHA
    for source, name in files:
        assert name not in before or before[name] == sha(source), name
    print(f"COVERAGE_DELIVERY_PREFLIGHT files={len(files)} previous={len(before)} movie_unchanged=True", flush=True)
    if not args.execute:
        return
    receipt = ROOT / "delivery_receipt.json"
    assert not receipt.exists(), receipt
    for source, name in files:
        if name not in before:
            target = PREVIOUS / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as reader, target.open("xb") as writer:
                shutil.copyfileobj(reader, writer)
        assert sha(PREVIOUS / name) == sha(source), name
    after = snapshot(PREVIOUS)
    assert all(after[name] == value for name, value in before.items())
    assert sorted(name for name in after if name.endswith(".mp4")) == [MOVIE]
    write_json(
        receipt,
        {
            "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "destination": str(PREVIOUS),
            "entry": "index_v05b_2.html",
            "previous_files_preserved": len(before),
            "added_files": len(after) - len(before),
            "files_total": len(after),
            "files": [{"path": name, "sha256": sha(source)} for source, name in files],
            "mp4_count": 1,
            "movie_sha256_unchanged": MOVIE_SHA,
            "script_sha256": sha(ROOT / "deliver_page.py"),
        },
    )
    print(f"COVERAGE_DELIVERY_COMPLETE added={len(after) - len(before)} preserved={len(before)} mp4=1", flush=True)


if __name__ == "__main__":
    main()
