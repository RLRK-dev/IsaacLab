# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Exercise the existing process renderer on twelve recovered display samples."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import recover_bank as recovery
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
INDICES = np.array([54, 72, 123, 315, 650, 690, 757, 825, 920, 1195, 1660, 1702])


def contact_sheets(rows: list[dict], output: Path) -> list[dict]:
    font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 22)
    sheets = []
    for page in range(2):
        image = Image.new("RGB", (1920, 1740), "#E9F0F4")
        draw = ImageDraw.Draw(image)
        for ordinal, row in enumerate(rows[page * 6 : (page + 1) * 6]):
            left, top = ordinal % 2 * 960, ordinal // 2 * 580
            frame = Image.open(output / row["file"]).convert("RGB")
            image.paste(frame.resize((960, 540), Image.Resampling.LANCZOS), (left, top))
            index = row["original_sample_index"]
            draw.text(
                (left + 16, top + 544),
                f"保存表示の再描画 | {index / 15:.2f} 秒 | sample {index}",
                font=font,
                fill="#173B4D",
            )
        path = ROOT / f"contact_{page + 1}.jpg"
        assert not path.exists()
        image.save(path, quality=92)
        sheets.append({"file": path.name, "sha256": recovery.sha(path)})
    return sheets


def main() -> None:
    output = ROOT / "previews"
    assert not output.exists()
    receipt_path = ROOT / "recovery.json"
    receipt = json.loads(receipt_path.read_text())
    bank = ROOT / "recovered/panel_v05d.npz"
    assert recovery.sha(bank) == receipt["recovered_stages"][-1]["sha256"]
    pins = {**receipt["input_sha256"], str(receipt_path): recovery.sha(receipt_path)}
    pins.update({str(bank): recovery.sha(bank), str(Path(__file__)): recovery.sha(Path(__file__))})
    assert all(recovery.sha(Path(path)) == digest for path, digest in pins.items())
    renderer_path = recovery.WORK / "hvjb-line-video-v05b-20260923/render_review.py"
    renderer = recovery.module("recovered_existing_renderer", renderer_path)
    plan = json.loads(recovery.PLAN.read_text())
    subset = {**plan, "expected_source_samples": [plan["expected_source_samples"][int(index)] for index in INDICES]}
    output.mkdir()
    rows, omissions, text_count = renderer.render(bank, subset, INDICES, output)
    assert all(recovery.sha(Path(path)) == digest for path, digest in pins.items())
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "input_sha256": pins,
        "images": rows,
        "contact_sheets": contact_sheets(rows, output),
        "display_nodes_omitted": omissions,
        "text_elements_checked": text_count,
        "unchanged_existing_renderer": True,
        "unchanged_saved_camera": True,
        "new_mp4_created": False,
        "physical_acceptance_verdict": None,
    }
    recovery.write(ROOT / "render_readback.json", record)
    print(f"RECOVERED_RENDER_COMPLETE frames={len(rows)} excluded_nodes={len(omissions)}", flush=True)


if __name__ == "__main__":
    main()
