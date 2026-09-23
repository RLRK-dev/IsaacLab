# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read the encoded review and extract identified frames for display inspection."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
STEM = "HVJB_line_split_process_concept_v04_review"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    report_path = ROOT / "audit/video_readback.json"
    images_path = ROOT / "decoded_stills"
    assert not report_path.exists() and not images_path.exists()
    plan = json.loads((ROOT / "data/concept_v04.json").read_text())
    manifest = json.loads((ROOT / "previews/concept_v04/manifest.json").read_text())
    encoded = json.loads((ROOT / "audit" / f"{STEM}_video.json").read_text())
    movie = ROOT / f"{STEM}.mp4"
    record = encoded["videos"][movie.name]
    assert sha(movie) == record["sha256"]
    assert encoded["generated_mp4_count"] == 1
    assert not encoded["generated_raw_mp4"] and not encoded["generated_wide_video"]
    assert encoded["frame_count"] == 1785 and encoded["duration_s"] == 119.0
    assert record["full_decode_exit_code"] == 0 and record["full_black_intervals"] == []
    assert manifest["complete"] and len(manifest["images"]) == 1785
    assert encoded["presentation_sha256"] == sha(ROOT / "data/concept_v04.json")
    assert manifest["renderer_sha256"] == sha(ROOT / "render_review.py")
    assert len(plan["tasks_preserved"]) == len(set(plan["tasks_preserved"])) == 20
    expected_scenes = {row["id"] for row in plan["scenes"]}
    assert {row["feature_id"] for row in manifest["images"]} == expected_scenes
    indices = [int((row["start_s"] + 0.62 * (row["stop_s"] - row["start_s"])) * 15) for row in plan["scenes"]]
    expression = "+".join(f"eq(n\\,{index})" for index in indices)
    images_path.mkdir()
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(movie),
        "-vf",
        "select=" + expression,
        "-fps_mode",
        "vfr",
        "-frames:v",
        str(len(indices)),
        str(images_path / "frame-%02d.png"),
    ]
    decoded = subprocess.run(command, check=True, capture_output=True, text=True)
    assert len(list(images_path.glob("frame-*.png"))) == 18
    rows = []
    for number, (index, scene) in enumerate(zip(indices, plan["scenes"], strict=True), start=1):
        path = images_path / f"frame-{number:02d}.png"
        source = ROOT / "previews/concept_v04" / manifest["images"][index]["file"]
        assert sha(source) == manifest["images"][index]["sha256"]
        original = np.asarray(Image.open(source).convert("RGB"), dtype=np.int16)
        result = np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
        assert original.shape == result.shape == (1080, 1920, 3)
        # Exclude the encoder's top and bottom captions. This is an observed compression difference, not a threshold.
        difference = np.abs(original[64:1015] - result[64:1015])
        rows.append(
            {
                "scene": scene["id"],
                "source_sample_index": index,
                "saved_time_s": index / 15,
                "decoded_png": str(path.relative_to(ROOT)),
                "decoded_png_sha256": sha(path),
                "source_png_sha256": sha(source),
                "display_area_mean_absolute_rgb_difference": float(difference.mean()),
            }
        )
    report = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "video_sha256": sha(movie),
        "source_bank_sha256": plan["motion_sha256"],
        "frame_count": 1785,
        "fps": 15,
        "duration_s": 119.0,
        "size_px": [1920, 1080],
        "source_scenes": len(expected_scenes),
        "jobs_retained": plan["tasks_preserved"],
        "full_decode_exit_code": 0,
        "full_black_intervals": [],
        "sample_extraction_command": command,
        "sample_extraction_stderr": decoded.stderr,
        "samples": rows,
        "visual_inspection_recorded_separately": True,
        "formal_physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("VIDEO_READBACK_COMPLETE frames=1785 seconds=119 samples=18 jobs=20", flush=True)


if __name__ == "__main__":
    main()
