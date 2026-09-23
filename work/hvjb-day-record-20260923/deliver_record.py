# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Add two dated record files after checking the previously delivered inventory."""

import argparse
import json
import re
import shutil
from datetime import datetime
from urllib.parse import unquote
from zoneinfo import ZoneInfo

from capture_inventory import DESTINATION, ROOT, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    inventory = json.loads((ROOT / "package_inventory.json").read_text())
    for row in inventory["files"]:
        assert sha(DESTINATION / row["path"]) == row["sha256"], row["path"]
    report = ROOT / "DAY_RECORD.md"
    for link in re.findall(r"\]\(([^)]+)\)", report.read_text()):
        assert (DESTINATION / unquote(link)).is_file(), link
    files = {
        "2026-09-23_作業記録.md": report,
        "2026-09-23_成果物一覧.json": ROOT / "package_inventory.json",
    }
    receipt = ROOT / "delivery_receipt.json"
    assert not receipt.exists()
    assert all(not (DESTINATION / name).exists() for name in files)
    print("DAY_RECORD_PREFLIGHT preserved=452 new_files=2 mp4_unchanged=1", flush=True)
    if not args.execute:
        return
    for name, source in files.items():
        with source.open("rb") as reader, (DESTINATION / name).open("xb") as writer:
            shutil.copyfileobj(reader, writer)
        assert sha(DESTINATION / name) == sha(source), name
    for row in inventory["files"]:
        assert sha(DESTINATION / row["path"]) == row["sha256"], row["path"]
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "destination": str(DESTINATION),
        "previous_files_preserved": len(inventory["files"]),
        "added_files": [{"path": name, "sha256": sha(source)} for name, source in files.items()],
        "file_count_after": sum(path.is_file() for path in DESTINATION.rglob("*")),
        "mp4_count_after": len(list(DESTINATION.rglob("*.mp4"))),
        "script_sha256": sha(ROOT / "deliver_record.py"),
    }
    assert result["file_count_after"] == 454 and result["mp4_count_after"] == 1
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("DAY_RECORD_DELIVERED preserved=452 added=2 total=454 mp4=1", flush=True)


if __name__ == "__main__":
    main()
