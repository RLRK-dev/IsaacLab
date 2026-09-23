# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read back the PNGs and diagram poses; do not classify physical retention or contact."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    output = ROOT / "audit"
    assert not output.exists()
    manifest_path = ROOT / "output/process/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    source_path = ROOT / "sources/handoff_sequence_observations.json"
    source = json.loads(source_path.read_text())
    assert manifest["source_states"] == source["states"]
    assert manifest["frame_count"] == len(manifest["images"]) == 300
    assert not manifest["preview_only"]
    assert manifest["cameras"]["loading"] == manifest["cameras"]["pickup"]
    for path, digest in manifest["source_sha256"].items():
        assert sha(Path(path)) == digest, path
    records = []
    for operation in ("loading", "pickup"):
        rows = [row for row in manifest["images"] if row["operation"] == operation]
        assert [row["local_frame"] for row in rows] == list(range(1, 151))
        poses = [row["pose"] for row in rows]
        hand = np.array([row["hand_lift_mm"] for row in poses])
        case = np.array([row["case_lift_mm"] for row in poses])
        opening = np.array([row["opening_per_jaw_mm"] for row in poses])
        toe = np.array([row["clamp_toe_outward_mm"] for row in poses])
        moving_case = np.flatnonzero(np.diff(case))
        moving_toe = np.flatnonzero(np.diff(toe))
        moving_opening = np.flatnonzero(np.diff(opening))
        drift = float(abs(np.diff(hand - case)[moving_case]).max())
        records.append(
            {
                "operation": operation,
                "samples": len(rows),
                "max_hand_minus_case_lift_change_during_case_motion_mm": drift,
                "jaw_opening_during_case_motion_mm": np.unique(opening[moving_case]).tolist(),
                "jaw_opening_during_clamp_toe_motion_mm": np.unique(opening[moving_toe]).tolist(),
                "clamp_toe_opening_during_jaw_motion_mm": np.unique(toe[moving_opening]).tolist(),
                "case_lift_during_jaw_motion_mm": np.unique(case[moving_opening]).tolist(),
            }
        )
        assert drift == 0
        assert np.all(opening[moving_case] == 0)
        assert np.all(opening[moving_toe] == 0)
        assert np.all(toe[moving_opening] == 0) and np.all(case[moving_opening] == 0)
        for row in rows:
            file = ROOT / "output/process" / row["file"]
            assert sha(file) == row["sha256"]
            with Image.open(file) as image:
                assert image.size == (1920, 1080)
                image.load()
            for bounds in row["projected_mesh_bounds_normalized"].values():
                assert abs(np.asarray(bounds)).max() < 1
    output.mkdir()
    (output / "contacts").mkdir()
    font = ImageFont.truetype(FONT, 22)
    selection = [7, 24, 41, 58, 75, 92, 108, 126, 142]
    contacts = []
    for operation in ("loading", "pickup"):
        sheet = Image.new("RGB", (1920, 1200), "#F2F6F8")
        draw = ImageDraw.Draw(sheet)
        for tile, index in enumerate(selection):
            row = next(r for r in manifest["images"] if r["operation"] == operation and r["local_frame"] == index + 1)
            x, y = tile % 3 * 640, tile // 3 * 400
            draw.text(
                (x + 12, y + 4),
                f"{operation} / frame {index + 1} / {row['local_time_s']:.2f} s",
                font=font,
                fill="#173B4D",
            )
            with Image.open(ROOT / "output/process" / row["file"]) as image:
                sheet.paste(image.resize((640, 360), Image.Resampling.LANCZOS), (x, y + 40))
        file = output / "contacts" / (operation + ".png")
        sheet.save(file)
        contacts.append({"file": str(file.relative_to(ROOT)), "sha256": sha(file)})
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "manifest_sha256": sha(manifest_path),
        "source_sha256": sha(source_path),
        "readback_frames": 300,
        "cameras_identical_for_load_and_pickup": True,
        "diagram_relationships": records,
        "framing": "All displayed mesh bounding boxes project inside each fixed render canvas.",
        "contact_sheets": contacts,
        "basis": "Image/file readback and numerical diagram poses, not force, sensors or physical retention.",
        "physical_acceptance_verdict": None,
    }
    (output / "sequence_readback.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("H06_SEQUENCE_READBACK frames=300 source_states_identical=True fixed_cameras=True", flush=True)
    print(json.dumps(records, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
