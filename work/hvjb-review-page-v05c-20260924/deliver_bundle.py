# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Copy the verified v05c review bundle to a new Downloads folder."""

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DESTINATION = Path("/home/rlrk/Downloads/HVJB_ライン全体レビュー_v05c_20260924")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    source = ROOT / "output"
    qa = json.loads((ROOT / "qa_receipt.json").read_text())
    browser = json.loads((ROOT / "browser_qa02/browser_receipt.json").read_text())
    playback = json.loads((ROOT / "playback_qa/playback_receipt.json").read_text())
    assert sha(source / "index.html") == browser["entry_sha256"] == playback["entry_sha256"]
    assert browser["page_errors"] == browser["unexpected_failed_requests"] == []
    assert all(row["mediaError"] is None and row["paused"] for row in playback["observations"])
    manifest_path = source / "review_manifest.json"
    assert sha(manifest_path) == qa["manifest_sha256"]
    manifest = json.loads(manifest_path.read_text())
    rows = manifest["files"] + [{"path": manifest_path.name, "sha256": sha(manifest_path)}]
    assert len(manifest["mp4_files"]) == 1
    for row in rows:
        assert sha(source / row["path"]) == row["sha256"]
    assert not DESTINATION.exists()
    print(f"V05C_DELIVERY_PREFLIGHT files={len(rows)} mp4=1", flush=True)
    if not args.execute:
        return
    receipt = ROOT / "delivery_receipt.json"
    assert not receipt.exists()
    DESTINATION.mkdir()
    for row in rows:
        target = DESTINATION / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        with (source / row["path"]).open("rb") as reader, target.open("xb") as writer:
            shutil.copyfileobj(reader, writer)
        assert sha(target) == row["sha256"]
    mp4s = [str(path.relative_to(DESTINATION)) for path in DESTINATION.rglob("*.mp4")]
    assert mp4s == manifest["mp4_files"]
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "destination": str(DESTINATION),
        "entry": "index.html",
        "files_delivered_and_read_back": len(rows),
        "manifest_sha256": sha(manifest_path),
        "qa_receipt_sha256": sha(ROOT / "qa_receipt.json"),
        "browser_receipt_sha256": sha(ROOT / "browser_qa02/browser_receipt.json"),
        "playback_receipt_sha256": sha(ROOT / "playback_qa/playback_receipt.json"),
        "video_sha256": manifest["video_sha256"],
        "mp4_files": mp4s,
        "earlier_versions_modified": False,
        "script_sha256": sha(Path(__file__)),
    }
    receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(f"V05C_DELIVERY_COMPLETE files={len(rows)} mp4=1 destination={DESTINATION}")


if __name__ == "__main__":
    main()
