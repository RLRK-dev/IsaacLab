# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Deliver contact-layout stills with a verified link to the unchanged process video."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_review import DESTINATION, ROOT, copy, digest, write


def main() -> None:
    assert not DESTINATION.exists()
    assert not list((ROOT / "delivery").rglob("*.mp4"))
    old = json.loads((ROOT.parent / "hvjb-c-handoff-v05e-20260927/audit/delivery_receipt.json").read_text())
    old_root = Path(old["entry"]).parent
    for row in old["files"]:
        assert digest(old_root / row["path"]) == row["sha256"], row["path"]
    for name in ("01_C工程_接触域の比較.png", "02_C工程_開放空間の比較.png"):
        assert (ROOT / "delivery" / name).is_file()
    qa = json.loads((ROOT / "browser_qa/receipt.json").read_text())
    assert len(qa["states"]) == 20 and not qa["errors"]
    copy(ROOT / "browser_qa/receipt.json", ROOT / "delivery/audit/browser_receipt.json")
    records = []
    for source in sorted((ROOT / "delivery").rglob("*")):
        if source.is_file():
            relative = source.relative_to(ROOT / "delivery")
            target = DESTINATION / relative
            copy(source, target)
            records.append({"path": str(relative), "sha256": digest(target), "bytes": target.stat().st_size})
    assert (DESTINATION.parent / old_root.name / "index.html").is_file()
    assert digest(Path(old["video"])) == old["video_sha256"]
    report = {
        "delivered_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "entry": str(DESTINATION / "index.html"),
        "files": records,
        "new_mp4_count": 0,
        "existing_video": old["video"],
        "existing_video_sha256": old["video_sha256"],
        "existing_v05e_files_unchanged": len(old["files"]),
        "physical_acceptance_verdict": None,
    }
    write(DESTINATION / "manifest.json", report)
    write(ROOT / "audit/delivery_receipt.json", report)
    print(f"C_CONTACT_DELIVERED files={len(records)} old_files_unchanged={len(old['files'])} new_mp4=0", flush=True)


if __name__ == "__main__":
    main()
