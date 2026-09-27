# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Append the verified support review without replacing any delivered file."""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_trace import ENTRY, MANIFEST, ROOT, SOURCE, sha

DESTINATION = Path("/home/rlrk/Downloads/HVJB_ライン全体レビュー_v05d_20260924")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    overlay = ROOT / "overlay"
    qa = json.loads((ROOT / "qa_receipt.json").read_text())
    browser = json.loads((ROOT / "browser_qa/browser_receipt.json").read_text())
    assert qa["entry_sha256"] == browser["entry_sha256"] == sha(overlay / ENTRY)
    assert browser["page_errors"] == browser["unexpected_failed_requests"] == []
    assert qa["overlay_manifest_sha256"] == sha(overlay / MANIFEST)
    manifest = json.loads((overlay / MANIFEST).read_text())
    rows = manifest["files"] + [{"path": MANIFEST, "sha256": sha(overlay / MANIFEST)}]
    originals = [path for path in SOURCE.rglob("*") if path.is_file()]
    assert len(originals) == 522 and len(rows) == 7
    for path in originals:
        assert sha(path) == sha(DESTINATION / path.relative_to(SOURCE)), path
    for row in rows:
        assert sha(overlay / row["path"]) == row["sha256"]
        assert not (DESTINATION / row["path"]).exists(), row["path"]
    assert len(list(DESTINATION.rglob("*.mp4"))) == 1
    print("HANDOFF_DELIVERY_PREFLIGHT unchanged_files=522 new_files=7 mp4=1", flush=True)
    if not args.execute:
        return
    receipt = ROOT / "delivery_receipt.json"
    assert not receipt.exists()
    for row in rows:
        destination = DESTINATION / row["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        with (overlay / row["path"]).open("rb") as reader, destination.open("xb") as writer:
            shutil.copyfileobj(reader, writer)
    for path in originals:
        assert sha(path) == sha(DESTINATION / path.relative_to(SOURCE)), path
    for row in rows:
        assert sha(DESTINATION / row["path"]) == row["sha256"]
    assert len(list(DESTINATION.rglob("*.mp4"))) == 1
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "entry": str(DESTINATION / ENTRY),
        "entry_sha256": sha(DESTINATION / ENTRY),
        "files_added_and_read_back": 7,
        "original_files_unchanged": 522,
        "mp4_count": 1,
        "video_sha256": qa["video_sha256"],
        "overlay_manifest_sha256": sha(overlay / MANIFEST),
        "qa_receipt_sha256": sha(ROOT / "qa_receipt.json"),
        "browser_receipt_sha256": sha(ROOT / "browser_qa/browser_receipt.json"),
        "script_sha256": sha(Path(__file__)),
    }
    with receipt.open("x") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(f"HANDOFF_DELIVERY_COMPLETE entry={DESTINATION / ENTRY}")


if __name__ == "__main__":
    main()
