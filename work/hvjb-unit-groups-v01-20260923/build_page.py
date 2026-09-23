# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Build an offline group review without changing process assignments."""

from __future__ import annotations

import hashlib
import html
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent


def escape(value):
    return html.escape(str(value), quote=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image_pair(group, direction):
    hidden = " hidden" if direction != "oblique" else ""
    body = []
    for kind, label in (("context", "完成品の中の位置（着色）"), ("isolated", "この群だけ（元の相対位置）")):
        path = f"figures/{group['id']}_{direction}_{kind}.png"
        body.append(
            f'<figure><figcaption>{label}</figcaption><a href="{path}">'
            f'<img src="{path}" alt="{escape(group["name_ja"])}：{label}" width="960" height="660"'
            ' loading="lazy"></a></figure>'
        )
    return f'<div class="images" data-view-angle="{direction}"{hidden}>' + "".join(body) + "</div>"


def group_panel(group):
    key = group["id"]
    hidden = "" if key == "FG_FUSE" else " hidden"
    ids = "".join(
        f'<a href="../feature_atlas/figures/{escape(feature)}_isolated.png">{escape(feature)}</a>'
        for feature in group["feature_ids"]
    )
    features = "".join(
        f"<tr><td>{escape(row['id'])}</td><td>{escape(row['name_ja'])}</td></tr>"
        for row in group["features_unmodified"]
    )
    jobs = "".join(
        f'<tr><td><a href="../hand_review/index.html#job-{row["id"]}">{row["id"]}</a></td>'
        f"<td>{escape(row['title_ja'])}</td><td>{escape(row['location_ja'])}</td></tr>"
        for row in group["tasks_unmodified"]
    )
    source = group["source_group_unmodified"]
    return (
        f'<article class="group-view" data-group-panel="{key}" data-label="{escape(group["name_ja"])}"'
        f' style="--accent:{group["display_color"]}"{hidden}>'
        f"<h2>{escape(group['display_title_ja'])}</h2><p>{escape(group['display_note_ja'])}</p>"
        f'<p class="counts">{escape(group["name_ja"])} ／ 写真特徴 {len(group["feature_ids"])}項目</p>'
        + image_pair(group, "oblique")
        + image_pair(group, "front")
        + '<p class="minor">左右で拡大率が異なります。部品群の位置関係は完成時の保存座標のままです。'
        "実際の取外し方向・組立途中の状態を示す図ではありません。</p>"
        f'<div class="note"><strong>未確定：</strong>{escape(source["unresolved_ja"])}</div>'
        f'<p class="minor">既存の対応根拠：{escape(source["basis_ja"])}</p>'
        f'<div class="ids">{ids}</div><p class="minor">IDを選ぶと、1項目ずつ拡大できます。</p>'
        f'<p><a href="sheets/{key}.png">この群の説明図を開く</a></p>'
        '<details><summary>部品名と仕事の対応候補</summary><div class="details"><div>'
        f"<table><thead><tr><th>ID</th><th>写真特徴の名称</th></tr></thead><tbody>{features}</tbody></table></div>"
        "<div><p>以下は既存の検討先です。各部品を全ての仕事で扱う意味ではありません。</p>"
        f"<table><thead><tr><th>仕事</th><th>内容</th><th>場所</th></tr></thead><tbody>{jobs}</tbody></table>"
        "</div></div></details></article>"
    )


def evidence(data):
    rows = []
    for key in ("plate_024", "plate_050", "plate_146", "plate_154", "plate_158", "plate_170"):
        row = next(item for item in data["official_video_observations_unmodified"] if item["frame"] == key)
        rows.append(
            f'<tr><td><a href="{escape(row["source_url"])}">{escape(row["time_ja"])}</a></td>'
            f"<td>{escape(row['observation_ja'])}</td><td>{escape(row['limit_ja'])}</td></tr>"
        )
    return (
        "<details><summary>筐体外組立と搭載後作業を分けた映像上の根拠</summary>"
        "<p>Ampere EVの2025年組立映像について保存済みの観察を掲示しています。"
        "完成写真のモデルと同一製造版であることは未確認です。</p>"
        "<table><thead><tr><th>場面</th><th>見えること</th><th>ここでは決まらないこと</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table></details>"
    )


def document(body, title, script=False):
    tail = '<script src="groups.js"></script>' if script else ""
    return (
        '<!doctype html><html lang="ja"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>{escape(title)}</title><link rel="stylesheet" href="groups.css"></head>'
        f"<body><main>{body}</main>{tail}</body></html>\n"
    )


def main_page(data):
    buttons = "".join(
        f'<button type="button" data-select-group="{row["id"]}"'
        f' aria-pressed="{str(row["id"] == "FG_FUSE").lower()}">{escape(row["name_ja"])}</button>'
        for row in data["groups"]
    )
    coverage = "".join(
        f'<span style="flex:{len(row["feature_ids"])};background:{row["display_color"]}"'
        f' title="{escape(row["name_ja"])} {len(row["feature_ids"])}項目"></span>'
        for row in data["groups"]
    )
    jobs = "".join(
        f"<tr><td>{row['id']}</td><td>{escape(row['title_ja'])}</td>"
        f"<td>{escape(row['location_ja'])}</td><td>{escape(row['unresolved_ja'])}</td></tr>"
        for row in data["all_jobs_unmodified"]
    )
    body = (
        '<nav><a href="../index_v05_1.html">← 全体レビューへ</a>'
        '<a href="all_groups.html">11枚の図を一覧で開く</a><a href="README.md">読み方</a></nav>'
        "<h1>筐体内外の組立を、部品群で確認</h1>"
        '<p class="intro">Aで下板側、Bで補機ヒューズ板側を筐体外で組みます。Cでまとめて搭載した後、'
        "側壁の接続口と残る電気接続を扱います。下の図は完成写真に対応づけた保存モデルの部品群です。</p>"
        '<div class="flow" aria-label="既存の組立区分"><div><strong>A：下板側<br>B：補機ヒューズ板側</strong>'
        '<small>筐体外で組立・接続</small></div><b aria-hidden="true">→</b>'
        "<div><strong>C：外でまとめる</strong><small>板合わせ・持ち替え</small></div>"
        '<b aria-hidden="true">→</b><div><strong>筐体へ搭載</strong><small>本体と自由端の支持を継続</small></div>'
        '<b aria-hidden="true">→</b><div><strong>搭載後の作業</strong>'
        "<small>箱内工具・端末引出し・口固定・残接続</small></div></div>"
        "<p><strong>補機ヒューズ板側の締結は筐体外。</strong>主ヒューズP22・被覆P08の取付工程は、"
        "まだ確定していません。線の反対端を搭載後に接続する作業も別に残ります。</p>"
        f'<div class="coverage" aria-hidden="true">{coverage}</div>'
        '<p class="coverage-labels">11群で92写真特徴を重複なく表示：部品・端末の特徴42、'
        "ねじ頭等23、配線の可視区間27。実物の全BOMや全配線数ではありません。</p>"
        f'<div class="selectors" aria-label="部品群を選択">{buttons}</div>'
        '<div class="tools"><span id="selection-status" aria-live="polite">補機ヒューズ板側を表示中</span>'
        '<div><button type="button" data-select-angle="oblique" aria-pressed="true">斜めから</button> '
        '<button type="button" data-select-angle="front" aria-pressed="false">低い位置から</button></div></div>'
        + "".join(group_panel(row) for row in data["groups"])
        + "<details><summary>この図だけでは決められない形状・作業</summary><p>独立した可搬下板の全形状、"
        "抵抗等の写真で見えない対象、見えていない配線区間は追加していません。"
        "線のA/B所属・両端・必要な保持数、板同士の機械結合、隠れたねじの位置と積層は未確定です。</p>"
        "<p>この群だけをそのまま一体搬送できるとは示していません。支持の引継ぎは"
        '<a href="../parallel_review/index.html">3STの担当図</a>、手先候補は'
        '<a href="../hand_review/index.html">フィンガと仕事の対応</a>で確認できます。</p></details>'
        + evidence(data)
        + "<details><summary>20仕事を省略せず確認する</summary>"
        "<table><thead><tr><th>仕事</th><th>内容</th><th>場所</th><th>未確定事項</th></tr></thead>"
        f"<tbody>{jobs}</tbody></table></details>"
        '<div class="footer"><p>2026-09-23追加資料。部品群を表示するために周辺を非表示にしています。'
        "加工図・実機の組立中間姿勢・把持や締結の成立判定を表すものではありません。</p>"
        '<p><a href="group_review.json">部品群・仕事の対応データ</a> ／ '
        '<a href="render_receipt.json">描画の記録</a></p></div>'
    )
    return document(body, "HVJB 部品群と筐体内外の組立", True)


def all_page(data):
    cards = []
    for row in data["groups"]:
        path = f"sheets/{row['id']}.png"
        cards.append(
            f'<article class="all-card" style="--accent:{row["display_color"]}">'
            f'<h2>{escape(row["display_title_ja"])}</h2><a href="{path}">'
            f'<img src="{path}" alt="{escape(row["display_title_ja"])}の説明図" width="2000" height="1280"'
            ' loading="lazy"></a></article>'
        )
    body = (
        '<nav><a href="index.html">← 部品群を切り替えて見る</a><a href="../index_v05_1.html">全体レビューへ</a></nav>'
        "<h1>11の部品群：説明図一覧</h1><p>部品群の表示であり、分解順や一体搬送の状態ではありません。</p>"
        + "".join(cards)
    )
    return document(body, "HVJB 11部品群の説明図")


def main():
    out = ROOT / "output"
    out.mkdir(exist_ok=False)
    data = json.loads((ROOT / "data/group_review.json").read_text())
    shutil.copytree(ROOT / "render_v01/figures", out / "figures")
    shutil.copytree(ROOT / "sheets", out / "sheets")
    for source, target in (
        ("README.md", "README.md"),
        ("groups.css", "groups.css"),
        ("groups.js", "groups.js"),
        ("data/group_review.json", "group_review.json"),
        ("render_v01/render_receipt.json", "render_receipt.json"),
    ):
        shutil.copy2(ROOT / source, out / target)
    (out / "index.html").write_text(main_page(data), encoding="utf-8")
    (out / "all_groups.html").write_text(all_page(data), encoding="utf-8")
    manifest = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "files": [
            {"path": str(path.relative_to(out)), "sha256": sha(path), "bytes": path.stat().st_size}
            for path in sorted(out.rglob("*"))
            if path.is_file()
        ],
        "sources": {
            path.name: sha(path) for path in sorted(ROOT.iterdir()) if path.suffix in (".py", ".css", ".js", ".md")
        },
        "new_video": False,
    }
    (out / "group_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("GROUP_PAGE_READY groups=11 features=92 images=55 videos=0", flush=True)


if __name__ == "__main__":
    main()
