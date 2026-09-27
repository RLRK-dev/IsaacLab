# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Copy the verified review to a new Downloads directory with byte-for-byte readback."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_motion import ROOT, WORK, sha, write
from package_review import MOVIE

DESTINATION = Path("/home/rlrk/Downloads/HVJB_C工程受渡しレビュー_v05e_20260927")


def verify_prior() -> int:
    prior = json.loads((WORK / "hvjb-handoff-trace-v01-20260927/delivery_receipt.json").read_text())
    folder = Path(prior["entry"]).parent
    for row in prior["delivered_files"]:
        assert sha(folder / row["path"]) == row["sha256"], row["path"]
    return len(prior["delivered_files"])


def main() -> None:
    assert not DESTINATION.exists()
    stage = ROOT / "delivery"
    manifest = json.loads((stage / "manifest.json").read_text())
    for row in manifest["files"]:
        assert sha(stage / row["path"]) == row["sha256"]
    prior_count = verify_prior()
    assert Path("/home/rlrk/Downloads/HVJB_保持と受渡しレビュー_v05d2_20260927/index_v05d_2.html").is_file()
    sources = {
        str(path.relative_to(stage)): path
        for path in stage.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    sources.update(
        {
            "audit/package_manifest.json": stage / "manifest.json",
            "audit/browser_receipt.json": ROOT / "browser_qa/receipt.json",
            "failed_attempt/build_motion.py.txt": ROOT / "failed_attempt/build_motion.py.txt",
            "BROWSER_CHECK_DELTA.md": ROOT / "BROWSER_CHECK_DELTA.md",
            "scripts/qa_review.mjs": ROOT / "qa_review.mjs",
            "scripts/review_template.html": ROOT / "review_template.html",
        }
    )
    records = []
    DESTINATION.mkdir()
    for name, source in sorted(sources.items()):
        target = DESTINATION / name
        target.parent.mkdir(exist_ok=True, parents=True)
        with source.open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst)
        digest = sha(source)
        assert sha(target) == digest
        records.append({"path": name, "sha256": digest, "bytes": target.stat().st_size})
    assert [path.name for path in DESTINATION.rglob("*.mp4")] == [MOVIE]
    assert verify_prior() == prior_count
    receipt = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "entry": str(DESTINATION / "index.html"),
        "video": str(DESTINATION / MOVIE),
        "video_sha256": sha(DESTINATION / MOVIE),
        "duration_s": 209.2,
        "frame_count": 3138,
        "mp4_count": 1,
        "existing_files_unchanged": prior_count,
        "files": records,
        "formal_physical_validity_verdict": None,
    }
    write(DESTINATION / "manifest.json", receipt)
    write(ROOT / "audit/delivery_receipt.json", receipt)
    assert sha(DESTINATION / "manifest.json") == sha(ROOT / "audit/delivery_receipt.json")
    print(f"C_REVIEW_DELIVERED files={len(records)} old_files_unchanged={prior_count} mp4=1", flush=True)


if __name__ == "__main__":
    main()
