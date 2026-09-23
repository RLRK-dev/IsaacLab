# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Append the unit-group review without replacing a delivered file."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DESTINATION = Path("/home/rlrk/Downloads/HVJB_ライン全体レビュー_v05_20260923")
ENTRY = "index_v05_1.html"
MOVIE = "HVJB_line_split_process_concept_v05_review.mp4"
MOVIE_SHA = "fd768cb5c86707d206fe499142e83b3324c7312d5a8867d31c7e98caa0a5ad5c"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(folder):
    return {str(path.relative_to(folder)): sha(path) for path in folder.rglob("*") if path.is_file()}


def planned_files():
    out = ROOT / "output"
    qa = json.loads((ROOT / "qa_receipt.json").read_text())
    assert qa["manifest_sha256"] == sha(out / "group_manifest.json")
    assert qa["photo_features_preserved"] == 92 and qa["jobs_preserved"] == 20
    manifest = json.loads((out / "group_manifest.json").read_text())
    for row in manifest["files"]:
        assert sha(out / row["path"]) == row["sha256"], row["path"]
    files = [(path, "unit_review/" + str(path.relative_to(out))) for path in sorted(out.rglob("*")) if path.is_file()]
    files.extend(
        [
            (ROOT / "qa_receipt.json", "unit_review/qa_receipt.json"),
            (ROOT / "visual_observations.json", "unit_review/visual_observations.json"),
            (ROOT / "entry" / ENTRY, ENTRY),
        ]
    )
    assert not any(path.suffix == ".mp4" for path, _ in files)
    return files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    files = planned_files()
    before = snapshot(DESTINATION)
    assert before[MOVIE] == MOVIE_SHA
    for source, name in files:
        assert name not in before or before[name] == sha(source), name
    print(f"GROUP_DELIVERY_PREFLIGHT files={len(files)} previous={len(before)} movie_unchanged=True", flush=True)
    if not args.execute:
        return
    receipt = ROOT / "delivery_receipt.json"
    assert not receipt.exists(), receipt
    for source, name in files:
        if name not in before:
            target = DESTINATION / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as reader, target.open("xb") as writer:
                shutil.copyfileobj(reader, writer)
        assert sha(DESTINATION / name) == sha(source), name
    after = snapshot(DESTINATION)
    assert all(after[name] == value for name, value in before.items())
    assert sorted(name for name in after if name.endswith(".mp4")) == [MOVIE]
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "destination": str(DESTINATION),
        "entry": ENTRY,
        "previous_files_preserved": len(before),
        "added_files": len(after) - len(before),
        "files_total": len(after),
        "files": [{"path": name, "sha256": sha(source)} for source, name in files],
        "mp4_count": 1,
        "movie_sha256_unchanged": MOVIE_SHA,
        "script_sha256": sha(Path(__file__)),
    }
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"GROUP_DELIVERY_COMPLETE added={len(after) - len(before)} preserved={len(before)} mp4=1", flush=True)


if __name__ == "__main__":
    main()
