# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Record the delivered review package before appending the dated work record."""

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
DESTINATION = Path("/home/rlrk/Downloads/HVJB_ライン全体レビュー_v05b_20260923")
MOVIE = "HVJB_line_split_process_concept_v05b_review.mp4"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = ROOT / "package_inventory.json"
    assert not output.exists()
    files = [
        {"path": str(path.relative_to(DESTINATION)), "sha256": sha(path), "bytes": path.stat().st_size}
        for path in sorted(DESTINATION.rglob("*"))
        if path.is_file()
    ]
    lookup = {row["path"]: row["sha256"] for row in files}
    assert len(files) == 452
    assert [row["path"] for row in files if row["path"].endswith(".mp4")] == [MOVIE]
    assert lookup[MOVIE] == "65ed3f0f861370c55e3d09de5b6d5d17889aea14d1394de757aba7cf2360ba03"
    receipts = {}
    for folder in (
        "hvjb-review-page-v05b-20260923",
        "hvjb-public-assembly-review-v01-20260923",
        "hvjb-movie-coverage-v01-20260923",
    ):
        path = WORK / folder / "delivery_receipt.json"
        receipts[folder] = {"sha256": sha(path), "record": json.loads(path.read_text())}
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "package": str(DESTINATION),
        "entry": "index_v05b_2.html",
        "file_count_before_adding_day_record": len(files),
        "files": files,
        "mp4_count": 1,
        "movie_sha256": lookup[MOVIE],
        "bytes_total": sum(row["bytes"] for row in files),
        "delivery_receipts": receipts,
        "artifact_code_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"DAY_INVENTORY files={len(files)} mp4=1 entry={result['entry']}", flush=True)


if __name__ == "__main__":
    main()
