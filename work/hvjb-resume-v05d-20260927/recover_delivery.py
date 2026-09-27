# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Preserve and read back the existing v05d delivery without modifying it."""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SOURCE = Path("/home/rlrk/Downloads/HVJB_ライン全体レビュー_v05d_20260924")
VIDEO_SHA = "0cdcd4d43831c3f805aa4e5960b666e7965ee6f1ac38b59d31645630d1dd40da"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest_path = SOURCE / "review_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    rows = manifest["files"] + [{"path": manifest_path.name, "sha256": sha(manifest_path)}]
    expected = {row["path"]: row["sha256"] for row in rows}
    actual = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob("*") if path.is_file()}
    assert actual == expected, "Source differs from the saved manifest"
    assert len(actual) == 515
    assert manifest["video_sha256"] == VIDEO_SHA
    movies = [name for name in expected if name.endswith(".mp4")]
    assert movies == ["HVJB_line_split_process_concept_v05d_review.mp4"]
    assert actual[movies[0]] == VIDEO_SHA
    snapshot = ROOT / "delivery_snapshot"
    assert not snapshot.exists()
    shutil.copytree(SOURCE, snapshot)
    copied = {str(path.relative_to(snapshot)): sha(path) for path in snapshot.rglob("*") if path.is_file()}
    assert copied == actual
    source_after = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob("*") if path.is_file()}
    assert source_after == actual
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "source": str(SOURCE),
        "source_manifest_sha256": sha(manifest_path),
        "source_entry_sha256": actual["index.html"],
        "files_read_back": len(actual),
        "source_files_unchanged": True,
        "local_snapshot": str(snapshot),
        "all_snapshot_bytes_match": True,
        "video_sha256": VIDEO_SHA,
        "mp4_files": movies,
        "source_commit_retrieved": "da5830de78a86c219c129702c449ff74ecb8b5ca",
        "missing_previous_work_folder": "/tmp/hvjb-line-progress-20260923",
        "original_v05d_render_and_bundle_scripts_recovered": False,
        "original_v05d_generated_matrix_bank_recovered": False,
        "original_browser_screens_and_receipts_recovered": False,
        "render_or_physical_verification_rerun": False,
        "script_sha256": sha(Path(__file__)),
        "files": rows,
    }
    receipt = ROOT / "recovery_receipt.json"
    assert not receipt.exists()
    receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(f"V05D_RECOVERED files={len(actual)} mp4=1 source_unchanged=true all_sha_match=true")


if __name__ == "__main__":
    main()
