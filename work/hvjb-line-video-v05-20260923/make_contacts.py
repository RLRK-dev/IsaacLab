# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Make identified contact sheets of existing engineering PNGs for visual readback."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="concept_v05_preview01")
    args = parser.parse_args()
    assert Path(args.source).name == args.source
    directory = ROOT / "previews" / args.source
    manifest = json.loads((directory / "manifest.json").read_text())
    output = ROOT / "contacts" / args.source
    output.mkdir(parents=True, exist_ok=False)
    font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 21)
    for offset in range(0, len(manifest["images"]), 6):
        sheet = Image.new("RGB", (1600, 1440), "#F2F6F8")
        draw = ImageDraw.Draw(sheet)
        for number, row in enumerate(manifest["images"][offset : offset + 6]):
            source = directory / row["file"]
            assert hashlib.sha256(source.read_bytes()).hexdigest() == row["sha256"]
            cropped = Image.open(source).convert("RGB").crop((24, 192, 1272, 894)).resize((800, 450))
            x, y = number % 2 * 800, number // 2 * 480
            text = f"{row['feature_id']} / {row['saved_time_s']:.3f} s / sample {row['original_sample_index']}"
            draw.text((x + 12, y + 2), text, font=font, fill="#173B4D")
            sheet.paste(cropped, (x, y + 30))
        sheet.save(output / f"contact-{offset // 6 + 1}.png")
    print(f"CONTACTS_COMPLETE samples={len(manifest['images'])} output={output}")


if __name__ == "__main__":
    main()
