# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Append the review page to the existing delivery without replacing any file."""

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


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(folder: Path) -> list[dict]:
    manifest = json.loads((folder / "review_manifest.json").read_text())
    result = [dict(row) for row in manifest["files"]]
    for source, target in (
        (folder / "review_manifest.json", "review_manifest.json"),
        (ROOT / "qa_receipt.json", "page_qa_receipt.json"),
    ):
        result.append({"path": target, "sha256": sha(source), "bytes": source.stat().st_size})
    for row in result:
        source = ROOT / "qa_receipt.json" if row["path"] == "page_qa_receipt.json" else folder / row["path"]
        assert sha(source) == row["sha256"] and source.stat().st_size == row["bytes"], source
        row["source"] = source
    return result


def preflight(destination: Path, files: list[dict]) -> dict:
    assert destination.is_dir()
    old = json.loads((destination / "delivery_manifest.json").read_text())
    assert len(old["files"]) == 26
    for row in old["files"]:
        assert sha(destination / row["path"]) == row["sha256"], row["path"]
    intended = {row["path"]: row for row in files}
    existing = {str(path.relative_to(destination)): sha(path) for path in destination.rglob("*") if path.is_file()}
    assert existing.keys() <= intended.keys(), existing.keys() - intended.keys()
    for path, checksum in existing.items():
        assert intended[path]["sha256"] == checksum, path
    movies = [row["path"] for row in files if row["path"].endswith(".mp4")]
    assert movies == ["HVJB_line_split_process_concept_v04_review.mp4"], movies
    return existing


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_dir", type=Path, default=ROOT / "output")
    parser.add_argument("--destination", type=Path, default=DESTINATION)
    parser.add_argument("--receipt", type=Path, default=ROOT / "delivery_receipt.json")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    files = collect(args.source_dir)
    existing = preflight(args.destination, files)
    missing = [row for row in files if row["path"] not in existing]
    print(f"DELIVERY_PREFLIGHT existing={len(existing)} append={len(missing)} intended={len(files)}", flush=True)
    if not args.execute:
        return
    assert not args.receipt.exists(), args.receipt
    for row in missing:
        target = args.destination / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        assert not target.exists(), target
        with target.open("xb") as stream, row["source"].open("rb") as source:
            shutil.copyfileobj(source, stream)
        assert sha(target) == row["sha256"], target
    for row in files:
        assert sha(args.destination / row["path"]) == row["sha256"], row["path"]
    for path, checksum in existing.items():
        assert sha(args.destination / path) == checksum, path
    receipt = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "destination": str(args.destination),
        "existing_files_preserved": len(existing),
        "new_files_copied": len(missing),
        "files_read_back": len(files),
        "files": [{key: value for key, value in row.items() if key != "source"} for row in files],
        "source_manifest_sha256": sha(args.source_dir / "review_manifest.json"),
        "script_sha256": sha(Path(__file__)),
    }
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(f"DELIVERY_APPEND_COMPLETE files_read_back={len(files)} existing_unchanged={len(existing)}", flush=True)


if __name__ == "__main__":
    main()
