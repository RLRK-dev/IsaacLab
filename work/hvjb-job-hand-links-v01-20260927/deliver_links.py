# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Append verified job/hand navigation files to the existing v05d delivery."""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_links import ENTRY, ROOT, SOURCE, sha

DESTINATION = Path("/home/rlrk/Downloads/HVJB_ライン全体レビュー_v05d_20260924")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    overlay = ROOT / "overlay"
    qa = json.loads((ROOT / "qa_receipt.json").read_text())
    browser = json.loads((ROOT / "browser_qa/browser_receipt.json").read_text())
    assert browser["entry_sha256"] == qa["entry_sha256"] == sha(overlay / ENTRY)
    assert browser["page_errors"] == browser["unexpected_failed_requests"] == []
    manifest_path = overlay / "job_hand_links_manifest_v01.json"
    assert sha(manifest_path) == qa["overlay_manifest_sha256"]
    manifest = json.loads(manifest_path.read_text())
    rows = manifest["files"] + [{"path": manifest_path.name, "sha256": sha(manifest_path)}]
    original = json.loads((SOURCE / "review_manifest.json").read_text())
    old_rows = original["files"] + [{"path": "review_manifest.json", "sha256": sha(SOURCE / "review_manifest.json")}]
    assert len(old_rows) == 515 and len(rows) == 7
    for row in old_rows:
        assert sha(DESTINATION / row["path"]) == row["sha256"], row["path"]
    for row in rows:
        assert sha(overlay / row["path"]) == row["sha256"]
        assert not (DESTINATION / row["path"]).exists(), row["path"]
    assert len(list(DESTINATION.rglob("*.mp4"))) == 1
    print("JOB_HAND_DELIVERY_PREFLIGHT original_files=515 new_files=7 mp4=1", flush=True)
    if not args.execute:
        return
    receipt = ROOT / "delivery_receipt.json"
    assert not receipt.exists()
    for row in rows:
        destination = DESTINATION / row["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        with (overlay / row["path"]).open("rb") as reader, destination.open("xb") as writer:
            shutil.copyfileobj(reader, writer)
    for row in old_rows + rows:
        assert sha(DESTINATION / row["path"]) == row["sha256"]
    assert len(list(DESTINATION.rglob("*.mp4"))) == 1
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "entry": str(DESTINATION / ENTRY),
        "files_added_and_read_back": len(rows),
        "original_files_unchanged": len(old_rows),
        "mp4_count": 1,
        "video_sha256": original["video_sha256"],
        "overlay_manifest_sha256": sha(manifest_path),
        "qa_receipt_sha256": sha(ROOT / "qa_receipt.json"),
        "browser_receipt_sha256": sha(ROOT / "browser_qa/browser_receipt.json"),
        "script_sha256": sha(Path(__file__)),
    }
    receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(f"JOB_HAND_DELIVERY_COMPLETE entry={DESTINATION / ENTRY}")


if __name__ == "__main__":
    main()
