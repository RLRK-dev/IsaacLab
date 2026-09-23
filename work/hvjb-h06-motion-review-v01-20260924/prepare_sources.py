# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Pin the previously delivered H06 geometry and comparison poses without modifying them."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SOURCE = Path("/home/rlrk/IsaacLab/work/hvjb-pallet-location-v01-20260920/output")
INPUTS = {
    "models/H06_FC02_handoff_populated_comparison.glb": (
        "c2c76dbd4fe6d408e0b9cbe9d3025619cde72457a98f6aa3b89367b707f1ad52"
    ),
    "handoff_sequence_observations.json": "8b78ecc507c109ae2f0b4490887071781d7382bd2105569a7ef64a325b58b6e3",
    "pallet_location_observations.json": "3e1c06676079bf863cda76baa515201eb474efb0c1effc4f9d69c22abf1c2d93",
    "README.md": "5c1e96ef91d6c44f7ac7e5106da8aef4e1b8428c5ad00710e9e8384f09d6554f",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    destination = ROOT / "sources"
    assert not destination.exists()
    for relative, digest in INPUTS.items():
        assert sha(SOURCE / relative) == digest, relative
    destination.mkdir()
    rows = []
    for relative, digest in INPUTS.items():
        target = destination / Path(relative).name
        shutil.copy2(SOURCE / relative, target)
        assert sha(target) == digest and sha(SOURCE / relative) == digest
        rows.append({"source": str(SOURCE / relative), "copy": str(target.relative_to(ROOT)), "sha256": digest})
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "source_files": rows,
        "source_bytes_unchanged": True,
        "script_sha256": sha(Path(__file__)),
        "scope": "Reuse FC02 comparison poses; no mechanism or controller design change.",
    }
    (ROOT / "source_identity.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(f"H06_REUSE_SOURCE_COPY files={len(rows)} originals_unchanged=True", flush=True)


if __name__ == "__main__":
    main()
