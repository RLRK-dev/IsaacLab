# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Add a new entry page while preserving the delivered v05 entry."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DELIVERY = Path("/home/rlrk/Downloads/HVJB_ライン全体レビュー_v05_20260923")


def main():
    source = ROOT.parent / "hvjb-review-page-v05-20260923/output/index.html"
    assert source.read_bytes() == (DELIVERY / "index.html").read_bytes()
    text = source.read_text()
    assert text.count("</header>") == 1
    text = text.replace("レビュー v05</title>", "レビュー v05.1</title>")
    link = (
        '<p style="margin-top:12px"><a class="text-link" href="unit_review/index.html">'
        "筐体内外で扱う部品群を見る — 11群・92写真特徴</a></p>"
    )
    text = text.replace("</header>", link + "\n  </header>")
    target = ROOT / "entry/index_v05_1.html"
    target.parent.mkdir(exist_ok=False)
    with target.open("x") as stream:
        stream.write(text)
    print("GROUP_ENTRY_READY", target.name, hashlib.sha256(target.read_bytes()).hexdigest(), flush=True)


if __name__ == "__main__":
    main()
