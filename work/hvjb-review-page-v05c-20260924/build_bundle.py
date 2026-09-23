# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Bundle the single v05c movie, new local views and inherited line/part review material."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
PREVIOUS = Path("/home/rlrk/Downloads/HVJB_ライン全体レビュー_v05b_20260923")
VIDEO = WORK / "hvjb-line-video-v05c-20260924"
MOVIE = "HVJB_line_split_process_concept_v05c_review.mp4"
OLD_MOVIE = "HVJB_line_split_process_concept_v05b_review.mp4"
H06 = WORK / "hvjb-h06-motion-review-v01-20260924"
H05 = WORK / "hvjb-h05-motion-review-v01-20260924"
DATA_PATTERN = r'(<script id="review-data" type="application/json">)(.*?)(</script>)'
EXTRA_SCENES = [
    (
        "H06_loading",
        119,
        129,
        "拡大：H06 空筐体をパレットへ載せる",
        "D00",
        "着座・パレット保持へ引き継いでから指を開く",
    ),
    ("H06_pickup", 129, 139, "拡大：H06 再把持して筐体を取り出す", "D80", "ハンドの保持確認後にパレットを開放する手順"),
    ("H05_P16", 139, 147, "拡大：H05 3口ヘッダーの開放・退避", "D50", "比較形状。右の輪郭受けは把持位置の固定表示"),
    ("H05_P17", 147, 155.2, "拡大：H05 2口ヘッダーの開放・退避", "D50", "3口と2口は、それぞれのCADに沿う別の輪郭受け"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(folder: Path) -> dict[str, str]:
    return {str(path.relative_to(folder)): sha(path) for path in sorted(folder.rglob("*")) if path.is_file()}


def copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists(), target
    shutil.copy2(source, target)
    assert sha(source) == sha(target)


def inherited(out: Path, before: dict) -> list[str]:
    excluded = {"README.md", "review_manifest.json", "動画と図の開き方.md"}
    names = []
    for name in before:
        if name in excluded or name.startswith(("video_data/", "video_audit/", "video_stills/", "2026-09-23_")):
            continue
        path = Path(name)
        if path.suffix == ".mp4" or (path.parent == Path(".") and path.name.startswith("index")):
            continue
        copy(PREVIOUS / name, out / name)
        names.append(name)
    return names


def entry(out: Path) -> dict:
    page = (PREVIOUS / "index_v05b_2.html").read_text()
    match = re.search(DATA_PATTERN, page, re.S)
    assert match
    payload = json.loads(match.group(2))
    assert len(payload["jobs"]) == 20 and len(payload["features"]) == 92 and payload["duration_s"] == 119
    for identity, start, stop, title, job, note in EXTRA_SCENES:
        payload["scenes"].append(
            {"id": identity, "start_s": start, "stop_s": stop, "title_ja": title, "hold_or_limit_ja": note}
        )
        next(row for row in payload["jobs"] if row["id"] == job)["scene_ids"].append(identity)
    payload["duration_s"] = 155.2
    page = (
        page[: match.start(2)] + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + page[match.end(2) :]
    )
    replacements = {
        OLD_MOVIE: MOVIE,
        "レビュー v05b.2</title>": "レビュー v05c</title>",
        "工程の具体化 · 2026-09-23": "工程の具体化 · 2026-09-24",
        "ラインの流れを動画v05bで確認": "全体工程と把持・受け渡しを動画v05cで確認",
        "119秒。左はロボットと手先の模式動作、右は完成状態の保存モデルです。表示時間は実タクトではありません。": (
            "2分35.2秒。前半は全体工程、1分59秒から筐体の受け渡し、2分19秒からヘッダーの開放・退避を拡大します。"
            "表示時間は実タクトではありません。"
        ),
        "写真対応モデルとv05の動作を継承。v05bでは旧搬出XYZ等の表示を整理し、共用ストッカの物流図を加えました。": (
            "全体の20仕事と92写真特徴を継承。v05cは供給手の表示ずれを修正し、H06/H05の既存比較形状による拡大章を追加しました。"
        ),
        "video_audit/video_review_receipt.json": "video_audit/visual_observations.md",
        "動画の照合と表示確認": "v05c動画の照合と表示確認",
    }
    for old, new in replacements.items():
        assert old in page, old
        page = page.replace(old, new)
    quick = (
        '<div class="button-row local-chapters" aria-label="拡大章へ移動">'
        '<a class="text-link" href="#scene=H06_loading">1:59 筐体の載置</a>'
        '<a class="text-link" href="#scene=H06_pickup">2:09 筐体の取出し</a>'
        '<a class="text-link" href="#scene=H05_P16">2:19 3口ヘッダー</a>'
        '<a class="text-link" href="#scene=H05_P17">2:27 2口ヘッダー</a></div>'
        '<p class="secondary small">拡大章は既存の比較案です。'
        "全体図の手先をすべてこの形に置き換えた映像ではありません。</p>"
    )
    page = page.replace('<div class="video-layout">', quick + '<div class="video-layout">', 1)
    (out / "index.html").write_text(page)
    (out / "data/line_review_data_v05c.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    script = (out / "review.js").read_text()
    marker = '  showTab("video");\n})();'
    assert script.count(marker) == 1
    extra = """  showTab("video");
  function followSceneLink() {
    const value = new URLSearchParams(location.hash.slice(1)).get("scene");
    if (value && scenes.has(value)) seekScene(value);
  }
  window.addEventListener("hashchange", followSceneLink);
  document.querySelectorAll('a[href^="#scene="]').forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const value = new URLSearchParams(link.hash.slice(1)).get("scene");
      if (scenes.has(value)) {
        if (location.hash !== link.hash) history.pushState(null, "", link.hash);
        seekScene(value);
      }
    });
  });
  followSceneLink();
})();"""
    (out / "review.js").write_text(script.replace(marker, extra))
    return payload


def navigation(out: Path) -> None:
    for path in out.rglob("*.html"):
        if path == out / "index.html":
            continue
        text = path.read_text().replace(OLD_MOVIE, MOVIE)
        text = re.sub(r"index_v(?:04_[12]|05_1|05b_[12])\.html", "index.html", text)
        path.write_text(text)
    hand = out / "hand_review/index.html"
    text = hand.read_text()
    links = (
        '<p><a href="../index.html#scene=H06_loading">動画のH06受け渡し拡大を開く</a> · '
        '<a href="../index.html#scene=H05_P16">動画のH05輪郭受け・開放を開く</a></p>'
    )
    assert "</header>" in text
    hand.write_text(text.replace("</header>", links + "</header>", 1))
    for name in ("index_v04_1.html", "index_v04_2.html", "index_v05_1.html", "index_v05b_1.html", "index_v05b_2.html"):
        (out / name).write_text(
            '<!doctype html><html lang="ja"><meta charset="utf-8">'
            '<meta http-equiv="refresh" content="0;url=index.html"><title>全体レビューv05cへ</title>'
            '<p><a href="index.html">全体レビューv05cを開く</a></p></html>\n'
        )


def updated_video(out: Path) -> str:
    readback = json.loads((VIDEO / "audit/video_readback.json").read_text())
    assert readback["video_sha256"] == sha(VIDEO / MOVIE)
    assert readback["frame_count"] == 2328 and len(readback["samples"]) == 47
    assert (VIDEO / "audit/visual_observations.md").is_file()
    copy(VIDEO / MOVIE, out / MOVIE)
    seen = set()
    for row in readback["samples"]:
        if row["feature_id"] not in seen:
            copy(VIDEO / row["decoded_png"], out / "video_stills" / f"{row['feature_id']}.png")
            seen.add(row["feature_id"])
        copy(VIDEO / row["decoded_png"], out / "video_audit" / row["decoded_png"])
    for path in (VIDEO / "audit").iterdir():
        if path.is_file():
            copy(path, out / "video_audit" / path.name)
    for path in (VIDEO / "decoded_contacts").glob("*.png"):
        copy(path, out / "video_audit/decoded_contacts" / path.name)
    for name in ("concept_v05c.json", "video_source_bundle.json"):
        copy(VIDEO / "data" / name, out / "video_data" / name)
    copy(VIDEO / "REVIEW_SCOPE.md", out / "video_audit/今回の動画の範囲.md")
    for root in (H06, H05):
        for path in (root / "audit").rglob("*"):
            if path.is_file():
                copy(path, out / "video_audit" / root.name / path.relative_to(root / "audit"))
        for path in (root / "sources").glob("*.glb"):
            copy(path, out / "comparison_models" / path.name)
    fix = WORK / "hvjb-xyz-display-v01-20260924"
    copy(fix / "audit/display_delta.json", out / "video_audit/display_delta.json")
    return readback["video_sha256"]


def main() -> None:
    out = ROOT / "output"
    out.mkdir(exist_ok=False)
    before = snapshot(PREVIOUS)
    inherited_names = inherited(out, before)
    payload = entry(out)
    navigation(out)
    video_sha = updated_video(out)
    (out / "README.md").write_text(
        "# HVJB ライン全体レビュー v05c\n\n"
        "`index.html` をブラウザで開いてください。動画は1本、2分35.2秒です。\n\n"
        "- 0:00〜1:59：ライン全体の20仕事、A/Bの筐体外組立、Cへの合流・搭載、残接続、共用ストッカへの戻し。\n"
        "- 1:59〜2:19：H06の筐体載置・支持引継ぎ・開放と、再把持・取出し。\n"
        "- 2:19〜2:35.2：H05の3口・2口ヘッダーの保持、開放、上方退避。\n\n"
        "ページ内の場面ボタンや、仕事D00/D80/D50から拡大章へ移動できます。"
        "手先8系統・12用途の図、20仕事・92写真特徴の対応、全体6ページPDFも同じ入口にあります。\n\n"
        "拡大章は既存比較形状・保存姿勢による説明です。把持・締結・実機成立の正式判定ではありません。"
        "表示秒数はタクトではありません。5仕事の未確定な施工動作を新たに補っていません。\n\n"
        "既存資料の作成日・元観測のSHAは保持しています。今回のファイル同一性はreview_manifest.json、"
        "動画の読戻しはvideo_audit/video_readback.jsonを参照してください。旧v05bとv06は変更していません。\n"
    )
    after = snapshot(out)
    changed = [name for name in inherited_names if after[name] != before[name]]
    assert all(Path(name).suffix in (".html", ".js") for name in changed)
    assert snapshot(PREVIOUS) == before
    movies = [name for name in after if name.endswith(".mp4")]
    assert movies == [MOVIE]
    record = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "file_count": len(after),
        "files": [
            {"path": name, "sha256": digest, "bytes": (out / name).stat().st_size} for name, digest in after.items()
        ],
        "mp4_files": movies,
        "video_sha256": video_sha,
        "inherited_files_unchanged": [name for name in inherited_names if name not in changed],
        "navigation_adaptations": [
            {"path": name, "original_sha256": before[name], "new_sha256": after[name]} for name in changed
        ],
        "previous_folder_files_unchanged": len(before),
        "previous_entry_sha256": before["index_v05b_2.html"],
        "counts": {
            "jobs": len(payload["jobs"]),
            "features": len(payload["features"]),
            "scenes": len(payload["scenes"]),
        },
        "formal_physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    (out / "review_manifest.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(f"V05C_BUNDLE_COMPLETE files={len(after) + 1} mp4=1 jobs=20 features=92 scenes=22", flush=True)


if __name__ == "__main__":
    main()
