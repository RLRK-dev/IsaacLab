# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Append the parallel-role review to Downloads without replacing prior files."""

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
ENTRY = "index_v04_2.html"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(folder):
    return {str(path.relative_to(folder)): sha(path) for path in folder.rglob("*") if path.is_file()}


def create_entry():
    previous = ROOT.parent / "hvjb-hand-coverage-v01-20260923/entry/index_v04_1.html"
    assert sha(previous) == sha(DESTINATION / previous.name)
    text = previous.read_text().replace("レビュー v04.1</title>", "レビュー v04.2</title>")
    link = (
        '<p style="margin-top:12px"><a class="text-link" href="parallel_review/index.html">'
        "3STの並行処理・共用補助の受け渡しを見る</a></p>"
    )
    assert text.count("</header>") == 1
    text = text.replace("</header>", link + "\n  </header>")
    path = ROOT / "entry" / ENTRY
    path.parent.mkdir(exist_ok=True)
    if path.exists():
        assert path.read_text() == text
    else:
        path.write_text(text)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    out = ROOT / "output"
    qa = json.loads((ROOT / "qa_receipt.json").read_text())
    assert qa["manifest_sha256"] == sha(out / "parallel_manifest.json")
    manifest = json.loads((out / "parallel_manifest.json").read_text())
    for row in manifest["files"]:
        assert sha(out / row["path"]) == row["sha256"], row["path"]
    before = snapshot(DESTINATION)
    files = [
        (path, "parallel_review/" + str(path.relative_to(out))) for path in sorted(out.rglob("*")) if path.is_file()
    ]
    files.extend([(ROOT / "qa_receipt.json", "parallel_review/qa_receipt.json"), (create_entry(), ENTRY)])
    assert len(files) == 31
    for source, name in files:
        assert name not in before or before[name] == sha(source), name
    print(f"PARALLEL_DELIVERY_PREFLIGHT files={len(files)} previous={len(before)}", flush=True)
    if not args.execute:
        return
    receipt = ROOT / "delivery_receipt.json"
    assert not receipt.exists(), receipt
    for source, name in files:
        if name not in before:
            destination = DESTINATION / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as reader, destination.open("xb") as writer:
                shutil.copyfileobj(reader, writer)
        assert sha(DESTINATION / name) == sha(source), name
    after = snapshot(DESTINATION)
    assert all(after[name] == value for name, value in before.items())
    assert sorted(name for name in after if name.endswith(".mp4")) == ["HVJB_line_split_process_concept_v04_review.mp4"]
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "destination": str(DESTINATION),
        "entry": ENTRY,
        "previous_files_preserved": len(before),
        "files": [{"path": name, "sha256": sha(source)} for source, name in files],
        "mp4_count": 1,
        "script_sha256": sha(Path(__file__)),
    }
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"PARALLEL_DELIVERY_COMPLETE added={len(after) - len(before)} preserved={len(before)} mp4=1", flush=True)


if __name__ == "__main__":
    main()
