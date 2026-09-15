# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Extract untouched frames around the public HVJB plate installation [s]."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_photo_catalog_v01 import digest

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "references/hvjb_plate_sequence_20260916"
OUTPUT = ROOT / "data/hvjb_plate_evidence_v01.json"
TIMES = (24, 50, 134, 142, 144, 145, 146, 148, 150, 152, 154, 156, 158, 160, 162, 164, 166, 170)


def main() -> None:
    """Preserve source identities while extracting a new sequence of still frames."""
    assert not REFERENCE.exists() and not OUTPUT.exists(), "Refusing to overwrite an earlier extraction"
    evidence = json.loads((ROOT / "data/hvjb_video_evidence_v02.json").read_text())
    source = evidence["sources"]["assembly_20250607"]
    path = ROOT / source["file"]
    before = digest(path)
    assert before == source["sha256"], "Source video differs from the preserved record"
    REFERENCE.mkdir()
    frames = []
    for seconds in TIMES:
        target = REFERENCE / f"assembly_{seconds:03d}s.png"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-n", "-ss", str(seconds), "-i", str(path), "-frames:v", "1", str(target)],
            check=True,
        )
        frames.append(
            {
                "requested_seek_s": seconds,
                "timestamp_basis": "ffmpeg accurate seek; first display frame at/after the requested time",
                "file": str(target.relative_to(ROOT)),
                "sha256": digest(target),
                "size_px": source["size_px"],
                "url": f"{source['url']}&t={seconds}s",
                "pixel_transform": "none; full decoded frame without cropping or generated edits",
            }
        )
        print("PLATE_FRAME", seconds, target.name, flush=True)
    after = digest(path)
    assert before == after
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "source": source,
        "source_sha256_before": before,
        "source_sha256_after": after,
        "frames": frames,
        "observations_recorded": False,
        "physical_acceptance_verdict": None,
        "movie_created": False,
    }
    with OUTPUT.open("x") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("PLATE_EVIDENCE_INDEXED", len(frames), digest(OUTPUT), flush=True)


if __name__ == "__main__":
    main()
