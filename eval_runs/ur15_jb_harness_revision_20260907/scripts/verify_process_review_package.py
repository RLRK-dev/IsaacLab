# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Verify the delivered file inventory and its single process-review MP4."""

import fnmatch
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    inventory_path = ROOT / "DELIVERY_SHA256.json"
    inventory = json.loads(inventory_path.read_text())
    actual = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*") if path.is_file()}
    assert actual == set(inventory) | {"DELIVERY_SHA256.json"}
    for name, record in inventory.items():
        path = ROOT / name
        assert path.resolve().is_relative_to(ROOT.resolve()) and path.stat().st_size == record["bytes"]
        with path.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == record["sha256"], name
    videos = [name for name in actual if name.lower().endswith(".mp4")]
    policy = json.loads((ROOT / "data/video_delivery_policy.json").read_text())
    assert len(videos) == 1 and fnmatch.fnmatch(videos[0], policy["filename_pattern"])
    assert not policy["generate_raw_mp4"] and not policy["generate_wide_video"]
    print("PROCESS_REVIEW_PACKAGE_VERIFIED", videos[0], len(actual))


if __name__ == "__main__":
    main()
