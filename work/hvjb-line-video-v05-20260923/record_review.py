# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Record the explicitly inspected decoded frames and their limited observations."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = ROOT / "audit/video_review_receipt.json"
    assert not output.exists()
    readback_path = ROOT / "audit/video_readback.json"
    readback = json.loads(readback_path.read_text())
    contacts = sorted((ROOT / "decoded_contacts").glob("contact-*.png"))
    assert len(contacts) == 7 and len(readback["samples"]) == 42
    preview_a = json.loads((ROOT / "previews/concept_v05_preview01/manifest.json").read_text())
    preview_b = json.loads((ROOT / "previews/concept_v05_preview02/manifest.json").read_text())
    assert [row["saved_bank_index"] for row in preview_a["images"]] == [
        row["saved_bank_index"] for row in preview_b["images"]
    ]
    identical = sum(a["sha256"] == b["sha256"] for a, b in zip(preview_a["images"], preview_b["images"], strict=True))
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "video_sha256": readback["video_sha256"],
        "readback_sha256": sha(readback_path),
        "basis": (
            "42 decoded stills read as seven contact sheets; decoded frame-18 and frame-34 also read at full size."
        ),
        "frame_count": 1785,
        "duration_s": 119.0,
        "scene_stills_inspected": 42,
        "distinct_scenes_inspected": 18,
        "contacts": {str(path.relative_to(ROOT)): sha(path) for path in contacts},
        "observations": [
            "The v05 title and original scene notes remain visible in the inspected decoded samples.",
            "A's sampled opening and upward retreat are represented before its return toward the preparation position.",
            "B's sampled approach and release show intermediate hand orientations; "
            "C's busbar hand turns during approach.",
            "The wider S12 frame includes the main hand and busbar supply in the selected pickup samples.",
            "A's unit approach is outside the tight S04 camera; "
            "that interval is checked numerically, not visually here.",
            "S02, S09, S13 and S14 retain the unresolved-task banner rather than a fabricated operation.",
            "The completed-product image remains labelled separately from the left schematic motion.",
        ],
        "preview02_identical_pngs_out_of_24": identical,
        "limits": [
            "This is sampled frame inspection, not continuous human video playback.",
            "Detailed finger-to-part contact faces and all free-end retention are not established by this schematic.",
            "No arm/equipment clearance, retention-force, fastening-quality or real-takt verdict was made.",
        ],
        "formal_physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"V05_VISUAL_RECORD samples=42 scenes=18 preview_identical={identical}/24")


if __name__ == "__main__":
    main()
