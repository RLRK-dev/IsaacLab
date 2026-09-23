# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Record the actual auxiliary image observations for the v05b delivery."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
LOGISTICS = ROOT.parent / "hvjb-logistics-review-v01-20260923"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = ROOT / "audit/video_review_receipt.json"
    assert not target.exists()
    data = json.loads((ROOT / "audit/video_readback.json").read_text())
    assert len(data["samples"]) == 36
    paths = sorted((ROOT / "decoded_contacts").glob("contact-*.png"))
    assert len(paths) == 6
    paths += [ROOT / "decoded_stills" / f"frame-{number}.png" for number in ("01", "32")]
    paths += sorted((ROOT / "contacts/concept_v05b_preview02").glob("contact-*.png"))
    paths += sorted((LOGISTICS / "output/figures").glob("step-*.png"))
    assert len(paths) == 17
    manifest = json.loads((ROOT / "previews/concept_v05b/manifest.json").read_text())
    preview = json.loads((ROOT / "previews/concept_v05b_preview02/manifest.json").read_text())
    preview_matches = []
    for row in preview["images"]:
        current = manifest["images"][row["original_sample_index"]]
        assert row["sha256"] == current["sha256"]
        preview_matches.append(row["original_sample_index"])
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "basis": "Primary assistant opened the listed images with view_image in this session.",
        "video_sha256": data["video_sha256"],
        "scene_stills_inspected": 36,
        "distinct_scenes_inspected": len({row["scene"] for row in data["samples"]}),
        "images_opened": {str(path): sha(path) for path in paths},
        "preview_final_png_matches": preview_matches,
        "observations_ja": [
            "INTRO・復路・OUTROに旧搬出XYZが表示されず、供給側XYZと5腕を読める。",
            "取出しと収納の画面で同じ共用ストッカを示し、01区画の空きと完成品の戻りが見える。",
            "S14は施工未設定の注記と工程枠を残し、未採用の試験プローブ・旧搬出設備を描いていない。",
            "完成品の蓋記号は復路以降に表示し、その締付動作や合格検査を表していない。",
            "右側の完成状態の部品照合図と20仕事の対応を維持している。",
            "物流図6枚の文字・区画番号・往復矢印・01区画の状態を確認した。",
        ],
        "preview01_adjustment": (
            "Removing the old table exposed a leftover lid symbol in preview01. "
            "Preview02 hides that symbol until the completed-product return scene; no lid operation was added."
        ),
        "retained_limits_ja": [
            "左の設備・部品・指先は図解用形状であり、右の92写真特徴を全て組み付ける実動作ではない。",
            "1周期の表示のみ。20個の連続処理と実際の支持・クランプ・位置決めは未確認。",
            "保存座標の単位・動画時間から実寸や実機タクトを導出しない。",
        ],
        "continuous_video_playback_observed": False,
        "browser_ui_observed": False,
        "physical_acceptance_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("V05B_VISUAL_RECORD samples=36 scenes=18 preview_matches=18 logistics_diagrams=6")


if __name__ == "__main__":
    main()
