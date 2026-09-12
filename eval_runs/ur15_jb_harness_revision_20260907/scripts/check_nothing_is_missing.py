# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Check that certain questions are not silently absent from the documents.

Every other check here compares what a document says against the files beside it. None of them
can find something that was never written down, and the correction table -- forty-nine rows --
holds no entry of that kind either: every row is a thing said wrongly, not a thing left unsaid.

The renewal ran for a day with no stated finish. Nobody caught it, on either seat, because the
stage table listed v07a, v07c, v07d and v07b with a verdict against each and therefore had the
shape of an answer. A blank gets noticed; a blank shaped like an answer does not.

So this asks only whether each question below is present, either answered or recorded as open.
It never asks whether the answer is right, and a question recorded as open passes: leaving a
decision to Rs is the correct outcome, and silence is the failure.

    python3 scripts/check_nothing_is_missing.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
IN_SCOPE = ("HANDOFF_v07", "OP030_v07")

# Each question names the document that governs it. Searching every document was tried first
# and it passed on the very state it was written to catch: "何をもって成立とみなすか" matched
# v07a's validation section, which is about the fault axis alone and says nothing about the
# renewal. A question about the whole work has to be answered in the document that governs the
# whole work, or the match means nothing.
#
# A pattern that only matched an answer would not be enough either -- "recorded as open" must
# pass too, or the check pushes whoever runs it towards inventing an answer to silence it.
REQUIRED = [
    (
        "どこまで到達すれば刷新したことになるか",
        "HANDOFF_v07.md",
        "the work ran for a day without this, and the stage table hid it",
        [r"到達点", r"刷新の(終わり|完了|範囲)"],
    ),
    (
        "最後の成果物が何をもって受け入れられるか",
        "HANDOFF_v07.md",
        "work 8 produces a review page with no stated condition for accepting it",
        [r"受入条件", r"何をもって完了"],
    ),
    (
        "誰が採否を決め、誰が物理妥当性を判定するか",
        "HANDOFF_v07.md",
        "neither seat may decide either, so both have to be named",
        [r"採否.{0,20}Rs", r"VaultProtocol"],
    ),
    (
        "測定では埋まらない量が、どれで、どこへ上げられたか",
        "HANDOFF_v07.md",
        "bend radius, support pitch and separation belong to the real cable",
        [r"曲げ半径", r"支持ピッチ"],
    ),
]


def main() -> int:
    missing = 0
    for question, document, why, patterns in REQUIRED:
        path = HERE / document
        body = path.read_text() if path.exists() else ""
        hit = next((x for x in patterns if re.search(x, body)), None)
        if hit:
            print(f"ok      {question}\n          {document} matches /{hit}/")
        else:
            missing += 1
            print(f"ABSENT  {question}\n          not in {document} -- {why}")
    print(f"\n{len(REQUIRED)} questions: {missing} absent")
    print("A question recorded as open passes. Only silence fails.")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
