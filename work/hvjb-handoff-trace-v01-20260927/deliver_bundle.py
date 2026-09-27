# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Deliver a complete checked bundle to a new folder after the old path vanished."""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_trace import ENTRY, MANIFEST, ROOT, SOURCE, sha

DESTINATION = Path("/home/rlrk/Downloads/HVJB_保持と受渡しレビュー_v05d2_20260927")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    folder = ROOT / "preview"
    qa = json.loads((ROOT / "qa_receipt.json").read_text())
    browser = json.loads((ROOT / "browser_qa/browser_receipt.json").read_text())
    assert qa["entry_sha256"] == browser["entry_sha256"] == sha(folder / ENTRY)
    assert browser["page_errors"] == browser["unexpected_failed_requests"] == []
    assert qa["overlay_manifest_sha256"] == sha(folder / MANIFEST)
    manifest = json.loads((folder / MANIFEST).read_text())
    original_files = [path for path in SOURCE.rglob("*") if path.is_file()]
    assert len(original_files) == 522
    rows = [{"path": str(path.relative_to(SOURCE)), "sha256": sha(path)} for path in original_files]
    rows += manifest["files"] + [{"path": MANIFEST, "sha256": sha(folder / MANIFEST)}]
    assert len(rows) == len({row["path"] for row in rows}) == 529
    assert len([path for path in folder.rglob("*") if path.is_file()]) == 529
    for row in rows:
        assert sha(folder / row["path"]) == row["sha256"]
    videos = [row for row in rows if row["path"].endswith(".mp4")]
    assert len(videos) == 1 and videos[0]["sha256"] == qa["video_sha256"]
    assert not DESTINATION.exists()
    assert not (ROOT / "delivery_receipt.json").exists()
    print("HANDOFF_BUNDLE_PREFLIGHT recovered_files=522 added_files=7 video_count=1", flush=True)
    if not args.execute:
        return
    DESTINATION.mkdir(exist_ok=False)
    for row in rows:
        target = DESTINATION / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        with (folder / row["path"]).open("rb") as reader, target.open("xb") as writer:
            shutil.copyfileobj(reader, writer)
    for row in rows:
        assert sha(DESTINATION / row["path"]) == row["sha256"], row["path"]
    assert len(list(DESTINATION.rglob("*.mp4"))) == 1
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "entry": str(DESTINATION / ENTRY),
        "delivery_mode": "new_complete_directory_after_old_destination_missing",
        "files_copied_and_read_back": 529,
        "saved_files_unchanged": 522,
        "new_review_files": 7,
        "files_overwritten": 0,
        "mp4_count": 1,
        "video_sha256": qa["video_sha256"],
        "overlay_manifest_sha256": sha(folder / MANIFEST),
        "qa_receipt_sha256": sha(ROOT / "qa_receipt.json"),
        "browser_receipt_sha256": sha(ROOT / "browser_qa/browser_receipt.json"),
        "script_sha256": sha(Path(__file__)),
        "delivered_files": rows,
    }
    with (ROOT / "delivery_receipt.json").open("x") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(f"HANDOFF_BUNDLE_DELIVERED files=529 video_count=1 entry={DESTINATION / ENTRY}")


if __name__ == "__main__":
    main()
