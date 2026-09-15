# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Inspect previously unsampled assembly transitions without changing source pixels [s]."""

import argparse
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import collect_hvjb_plate_evidence_v01 as reuse
from PIL import Image

PHOTO_SHA = "99574f981ae301adf41a9ce9d4840eb15aa66dc7b477a10afe6b55a2accd2106"


def transition(photo_file: Path) -> None:
    """Extract the newly narrowed transition [s] and preserve an official still."""
    root = reuse.ROOT
    directory = root / "references/hvjb_join_transition_20260916"
    output = root / "data/hvjb_join_transition_v01.json"
    assert not directory.exists() and not output.exists(), "Refusing to overwrite evidence"
    source = json.loads((root / "data/hvjb_join_evidence_v01.json").read_text())["source"]
    video = root / source["file"]
    before = reuse.digest(video)
    assert before == source["sha256"]
    assert reuse.digest(photo_file) == PHOTO_SHA
    directory.mkdir()
    frames = []
    for milliseconds in range(87000, 88201, 200):
        seconds = milliseconds / 1000
        target = directory / f"assembly_{milliseconds:06d}ms.png"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-n", "-ss", str(seconds), "-i", str(video), "-frames:v", "1", str(target)],
            check=True,
        )
        frames.append(
            {
                "requested_seek_s": seconds,
                "timestamp_basis": "ffmpeg accurate seek; first display frame at/after the requested time",
                "file": str(target.relative_to(root)),
                "sha256": reuse.digest(target),
                "size_px": source["size_px"],
                "pixel_transform": "none; full decoded frame",
            }
        )
        print("JOIN_TRANSITION_FRAME", seconds, target.name, flush=True)
    photo = directory / "DSC02861-1.jpg"
    shutil.copy2(photo_file, photo)
    assert reuse.digest(photo) == PHOTO_SHA
    with Image.open(photo) as original:
        photo_size = list(original.size)
    after = reuse.digest(video)
    assert before == after
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "source": source,
        "source_sha256_before": before,
        "source_sha256_after": after,
        "frames": frames,
        "photo": {
            "url": "https://ampereev.com/wp-content/uploads/2022/05/DSC02861-1.jpg",
            "gallery_page": "https://ampereev.com/new-high-voltage-junction-box-taking-orders-now/",
            "file": str(photo.relative_to(root)),
            "sha256": PHOTO_SHA,
            "size_px": photo_size,
            "pixel_transform": "none; downloaded file copied byte for byte",
        },
        "observations_recorded": False,
        "physical_acceptance_verdict": None,
        "movie_created": False,
    }
    with output.open("x") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("JOIN_TRANSITION_INDEXED", len(frames), reuse.digest(output), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("sequence", "transition"), default="sequence")
    parser.add_argument("--photo_file", type=Path)
    args = parser.parse_args()
    if args.stage == "transition":
        assert args.photo_file is not None, "Provide the downloaded original DSC02861-1.jpg"
        transition(args.photo_file)
    else:
        reuse.REFERENCE = reuse.ROOT / "references/hvjb_join_sequence_20260916"
        reuse.OUTPUT = reuse.ROOT / "data/hvjb_join_evidence_v01.json"
        reuse.TIMES = (62, 64, 66, 68, 72, 82, 84, 86, 88, 90, 96, 110, 120, 128, 131, 133)
        reuse.main()
