# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Record the auxiliary observations made after opening the group images."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent


def main():
    path = ROOT / "visual_observations.json"
    assert not path.exists(), path
    opened = [
        *sorted((ROOT / "contacts").glob("*.png")),
        *sorted((ROOT / "render_contacts").glob("*.png")),
        ROOT / "sheets/FG_FUSE.png",
    ]
    assert len(opened) == 15
    result = {
        "recorded_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "basis": "Images opened with view_image by the producing assistant; auxiliary layout observations only.",
        "opened": [
            {"path": str(item.relative_to(ROOT)), "sha256": hashlib.sha256(item.read_bytes()).hexdigest()}
            for item in opened
        ],
        "coverage": {"raw_render_images_in_contacts": 44, "explanation_sheets_in_contacts": 11},
        "observations_ja": [
            "11枚の説明図で、タイトル・未確定事項・ID列の切れと重なりは見られなかった。",
            "Bの説明図を原寸でも開き、板と補機ヒューズ5個を表示として確認した。",
            "低い位置からの全体図では筐体や周辺物が対象を隠す。群だけの図との比較に利用する。",
            "配線だけの図は未見区間を持たない可視区間の集合であり、完成ハーネス形状には見立てない。",
            "主ヒューズと被覆は工程未確定の群として分かれ、補機ヒューズ群へ混在していない。",
        ],
        "browser_ui_observed": False,
        "grasp_contact_observed": False,
        "new_physical_operation_selection": None,
        "formal_physical_validity_verdict": None,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("GROUP_VISUAL_OBSERVATIONS_RECORDED opened=15 renders=44 sheets=11 physical_verdict=None", flush=True)


if __name__ == "__main__":
    main()
