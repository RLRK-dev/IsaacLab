# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Preserve the existing feature groups for a view-filter review."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
LOCATION = WORK / "hvjb-assembly-location-v01-20260921/output/assembly_location.json"
LINE = WORK / "hvjb-line-progress-20260923/data/line_review_data.json"
PRODUCT = WORK / "hvjb-inner-installed-access-v01-20260921/data/product_manifest.json"
NOTES = {
    "FG_CASE": ("筐体の受渡し", "XYZ供給 → 搭載・側壁作業 → 完成品を元の区画へ", "#47758a"),
    "FG_BASE": ("A：筐体外の組立", "接触器・リレー等を下板側で組む。下板全形状は未確認。", "#296db3"),
    "FG_FUSE": ("B：筐体外の組立", "補機ヒューズ板側の取付・端末締結を箱外で行う。", "#9e478f"),
    "FG_MAINFUSE": ("主ヒューズ：工程未確定", "補機ヒューズ5個とは別扱い。外組み／搭載後は未確定。", "#a7610f"),
    "FG_PORT": ("C：搭載後の側壁作業", "3口・2口ヘッダーの設置とねじ固定。主口・LVの細部は未確定。", "#198772"),
    "FG_BUS": ("C：搭載後の残接続", "後付け導体と丸端子の残接続。共締めの積層は未確定。", "#198772"),
    "FG_INNER": ("準備から搭載後まで", "自由端を支持しながら引継ぐ。A/Bへの個別所属は未確定。", "#a7610f"),
    "FG_RELAY_END": ("準備・A・Cの検討対象", "リレーに見える端末外装。電気ネット・遠端は未確定。", "#a7610f"),
    "FG_LUG": ("端末ごとに確認が必要", "外組み側と搭載後の接続側を端末ごとに区別する。", "#a7610f"),
    "FG_FASTENER": ("ねじ頭等の可視特徴", "23特徴は23本の施工ねじ・23回の締付作業ではない。", "#a7610f"),
    "FG_WIRE": ("配線の可視区間", "27区間は27本の完成ケーブルではない。所属・両端は未確定。", "#a7610f"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    out = ROOT / "data"
    assert not out.exists(), out
    location = json.loads(LOCATION.read_text())
    line = json.loads(LINE.read_text())
    product = json.loads(PRODUCT.read_text())
    features = line["feature_review_candidates"]
    groups = []
    for source in location["preserved_feature_groups"]:
        targets = [row for row in features if row["group_name_ja"] == source["name_ja"]]
        ids = [row["id"] for row in targets]
        assert ids and ("ids" not in source or set(ids) == set(source["ids"]))
        title, note, color = NOTES[source["id"]]
        tasks = {task for row in targets for task in row["review_task_ids"]}
        groups.append(
            {
                "id": source["id"],
                "name_ja": source["name_ja"],
                "source_group_unmodified": source,
                "feature_ids": ids,
                "features_unmodified": targets,
                "tasks_unmodified": [row for row in line["jobs"] if row["id"] in tasks],
                "display_title_ja": title,
                "display_note_ja": note,
                "display_color": color,
                "mesh_count": sum(len(product["features"][key]["meshes"]) for key in ids),
            }
        )
    flat = [key for row in groups for key in row["feature_ids"]]
    assert len(flat) == len(set(flat)) == 92
    assert set(flat) == set(product["features"])
    assert len(groups) == 11 and sum(row["mesh_count"] for row in groups) == 465
    result = {
        "revision": "hvjb_unit_group_review_v01_20260923",
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "groups": groups,
        "all_jobs_unmodified": line["jobs"],
        "official_video_observations_unmodified": location["source_video_observations"],
        "source_video_unmodified": location["source_video"],
        "group_count": 11,
        "feature_count": 92,
        "mesh_count": 465,
        "source_identity": {str(path.relative_to(WORK)): sha(path) for path in (LOCATION, LINE, PRODUCT)},
        "script_sha256": sha(Path(__file__)),
        "selection_is_view_filter_only": True,
        "intermediate_assembly_geometry_established": False,
        "new_physical_operation_selection": None,
        "formal_physical_validity_verdict": None,
    }
    out.mkdir()
    (out / "group_review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("GROUP_REVIEW_DATA groups=11 photo_features=92 meshes=465 no_duplicates=True", flush=True)


if __name__ == "__main__":
    main()
