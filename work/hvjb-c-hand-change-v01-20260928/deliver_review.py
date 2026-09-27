# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Deliver the C hand-change diagrams and verify the prior single process video."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from package_review import DESTINATION, FIGURES, PRIOR_RECEIPTS, ROOT, copy, digest, verify_prior, write


def main() -> None:
    assert not DESTINATION.exists(), DESTINATION
    delivery = ROOT / "delivery"
    assert not list(delivery.rglob("*.mp4"))
    old = verify_prior()
    qa = json.loads((ROOT / "browser_qa/receipt.json").read_text())
    assert len(qa["states"]) == 72 and not qa["errors"]
    for name in FIGURES:
        assert (delivery / name).is_file()
        copy(delivery / name, ROOT / "figures" / name)
    copy(ROOT / "browser_qa/receipt.json", delivery / "audit/browser_receipt.json")
    records = []
    for source in sorted(delivery.rglob("*")):
        if source.is_file():
            relative = source.relative_to(delivery)
            target = DESTINATION / relative
            copy(source, target)
            records.append({"path": str(relative), "sha256": digest(target), "bytes": target.stat().st_size})
    for link in qa["links"]:
        assert (DESTINATION / link).resolve().is_file(), link
    video = json.loads(PRIOR_RECEIPTS[1].read_text())
    assert digest(Path(video["video"])) == video["video_sha256"]
    assert verify_prior() == old
    report = {
        "delivered_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "entry": str(DESTINATION / "index.html"),
        "files": records,
        "prior_deliveries_unchanged": old,
        "existing_video": video["video"],
        "existing_video_sha256": video["video_sha256"],
        "new_mp4_count": 0,
        "selected_mechanism": None,
        "physical_acceptance_verdict": None,
    }
    write(DESTINATION / "manifest.json", report)
    write(ROOT / "audit/delivery_receipt.json", report)
    print(f"C_HAND_CHANGE_DELIVERED files={len(records)} old_files_unchanged=71 new_mp4=0", flush=True)


if __name__ == "__main__":
    main()
