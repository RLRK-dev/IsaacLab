# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Arrange decoded review stills with their observed sample identities."""

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent


def main():
    record = json.loads((ROOT / "audit/video_readback.json").read_text())
    output = ROOT / "decoded_contacts"
    output.mkdir(exist_ok=False)
    font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 22)
    for offset in range(0, len(record["samples"]), 6):
        sheet = Image.new("RGB", (1920, 1704), "#F2F6F8")
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(record["samples"][offset : offset + 6]):
            source = ROOT / row["decoded_png"]
            assert hashlib.sha256(source.read_bytes()).hexdigest() == row["decoded_png_sha256"]
            frame = Image.open(source).convert("RGB").resize((960, 540), Image.Resampling.LANCZOS)
            x, y = index % 2 * 960, index // 2 * 568
            draw.text((x + 12, y), f"{row['scene']} / {row['saved_time_s']:.3f} s", font=font, fill="#173B4D")
            sheet.paste(frame, (x, y + 28))
        sheet.save(output / f"contact-{offset // 6 + 1}.png")
    print(f"DECODED_CONTACTS_COMPLETE samples={len(record['samples'])}")


if __name__ == "__main__":
    main()
