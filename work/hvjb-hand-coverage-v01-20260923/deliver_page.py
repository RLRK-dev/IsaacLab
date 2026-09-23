# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Append the static hand review and a versioned navigation entry to Downloads."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DESTINATION = Path("/home/rlrk/Downloads/HVJB_ライン全体と組立場所_v04_20260923")
ENTRY_NAME = "index_v04_1.html"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_files() -> list[dict]:
    manifest_path = ROOT / "output/hand_manifest.json"
    qa = json.loads((ROOT / "qa_receipt.json").read_text())
    assert qa["manifest_sha256"] == sha(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    files = []
    for row in manifest["files"]:
        source = ROOT / "output" / row["path"]
        assert sha(source) == row["sha256"], source
        files.append({"source": source, "path": "hand_review/" + row["path"], "sha256": row["sha256"]})
    for source, name in ((manifest_path, "hand_manifest.json"), (ROOT / "qa_receipt.json", "qa_receipt.json")):
        files.append({"source": source, "path": "hand_review/" + name, "sha256": sha(source)})
    return files


def create_entry() -> Path:
    source = ROOT.parent / "hvjb-review-page-v04-20260923/output/index.html"
    html = source.read_text()
    assert html.count("</header>") == 1
    html = html.replace("HVJB ライン全体レビュー v04</title>", "HVJB ライン全体レビュー v04.1</title>")
    link = (
        '<p style="margin-top:18px"><a class="text-link" href="hand_review/index.html">'
        "手先・支持の図を開く — 8系統と12用途</a></p>"
    )
    html = html.replace("</header>", link + "\n  </header>")
    entry = ROOT / "entry" / ENTRY_NAME
    if entry.exists():
        assert entry.read_text() == html
    else:
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text(html)
    return entry


def snapshot(folder: Path) -> dict[str, str]:
    return {str(path.relative_to(folder)): sha(path) for path in folder.rglob("*") if path.is_file()}


def verify_parent(destination: Path) -> dict:
    existing = snapshot(destination)
    receipt_path = ROOT.parent / "hvjb-review-page-v04-20260923/delivery_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    for row in receipt["files"]:
        assert existing[row["path"]] == row["sha256"], row["path"]
    return existing


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    existing = verify_parent(DESTINATION)
    files = collect_files()
    entry = create_entry()
    files.append({"source": entry, "path": ENTRY_NAME, "sha256": sha(entry)})
    assert len(files) == 26 and all(not row["path"].endswith(".mp4") for row in files)
    for row in files:
        if row["path"] in existing:
            assert existing[row["path"]] == row["sha256"], row["path"]
    missing = [row for row in files if row["path"] not in existing]
    print(f"HAND_DELIVERY_PREFLIGHT existing={len(existing)} append={len(missing)}", flush=True)
    if not args.execute:
        return
    receipt = ROOT / "delivery_receipt.json"
    assert not receipt.exists(), receipt
    for row in missing:
        destination = DESTINATION / row["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as target, row["source"].open("rb") as source:
            shutil.copyfileobj(source, target)
        assert sha(destination) == row["sha256"], destination
    after = snapshot(DESTINATION)
    assert all(after[path] == checksum for path, checksum in existing.items())
    assert all(after[row["path"]] == row["sha256"] for row in files)
    movies = [path for path in after if path.endswith(".mp4")]
    assert movies == ["HVJB_line_split_process_concept_v04_review.mp4"]
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "destination": str(DESTINATION),
        "entry": ENTRY_NAME,
        "existing_files_preserved": len(existing),
        "new_files_read_back": len(files),
        "files": [{"path": row["path"], "sha256": row["sha256"]} for row in files],
        "mp4_files": movies,
        "script_sha256": sha(Path(__file__)),
    }
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"HAND_DELIVERY_COMPLETE new={len(files)} previous_preserved={len(existing)} mp4=1", flush=True)


if __name__ == "__main__":
    main()
