# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Derive the user-requested single-video package from the verified v06 stage."""

import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from deliver_op030_split_v06 import verify_directory

PACKAGE = "UR15_JB_OP030_20260910_v06"
VIDEO = "UR15_JB_OP030_split_process_v06_review.mp4"
PAGE = "review_OP030_split_v06.html"
DOCUMENT = "OP030_三ST工程・部品確認書_v06.md"
README = "README_OP030_split_v06.md"
NATIVE_SHA = "e65bef607c1d29671fc982d14d72d4c2694420edd284378cb2f1445f18f354ed"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def document_text(text: str) -> str:
    replacements = {
        "工程映像と固定全景、それぞれの説明付き／説明なしの計4動画を生成し、": "工程説明付き動画1本を配布対象とし、",
        "4ファイルのFFprobe実測": "工程説明付きMP4のFFprobe実測",
        "説明あり・なしの双方で検査を完了した": "工程説明付き映像の検査を完了した",
        "工程／固定全景の各映像に、説明付き版と説明なし版を用意した。4本とも同じ時系列を収録する。": (
            "配布動画は工程説明付き映像1本。今後も同じ種類だけを生成する。"
        ),
    }
    for before, after in replacements.items():
        assert text.count(before) == 1, before
        text = text.replace(before, after)
    lines = []
    for line in text.splitlines():
        if line.startswith("| [UR15_JB_OP030_split_") and VIDEO not in line:
            continue
        if line.startswith("| `audit/UR15_JB_OP030_split_wide_"):
            continue
        if line.startswith("| 4動画 |"):
            line = (
                "| 工程説明付き動画 | 7,031フレーム／15 fps／実測468.734秒。1280×720。"
                "全編デコード終了0、全画面黒区間なし | `audit/UR15_JB_OP030_split_process_v06_video.json` |"
            )
        lines.append(line)
    return "\n".join(lines) + "\n"


def readme_text() -> str:
    return f"""# UR15 OP030 千鳥配置 v06

`{PAGE}` を開くと、工程説明付き動画と160個の工程ジャンプを利用できます。
動画は `{VIDEO}` の1本です。1280×720、15 fps、約7分49秒。
今後も `*_split_process_*_review.mp4` だけを生成・納品します。

ケーブル設置のBを反対側へ移し、A・B・Cを千鳥配置にしました。
パレット原点は789 mmで一定です。A・Cの動作、F01の外部ハーネス支持を継承しています。
Bは両腕で取得・曲げ・設置し、解放後に同時180 mm上昇します。
2段循環の下段返送・両端移載は未実装です。寸法・部品・確認範囲は `{DOCUMENT}` を参照してください。

## 保存モデルと再生成

モデルは `UR15_JB_OP030_split_v06.blend`。次の手順は複製したフォルダーで実行します。
Blender 4.5.13の保存配列から再ベイクします。IKや経路探索は再実行しません。
元の19 helperと静的モデル・manifest・prepared NPZ/JSONの23入力は保存時のSHAで保持しています。
隔離再ベイクの実行記録は `audit/op030_split_layout_portable_rebake_v06.json` です。

```bash
blender -b --python-exit-code 1 -P scripts/animate_op030_split_v06.py --
```

再保存後は新しいplanのnative SHAに従って描画します。
工程視点だけをCycles/OPTIX・16 samplesで描画し、画像から説明付きMP4へ直接変換します。
中間のraw MP4や全景動画は作りません。FFmpeg、FFprobe、Noto Sans CJK JPを使用します。

```bash
mkdir -p audit
set -o pipefail
blender -b --python-exit-code 1 -P scripts/render_op030_v02.py -- \\
  --blend UR15_JB_OP030_split_v06.blend --views process \\
  --shot_plan op030_split_shots_v06.json --video --engine CYCLES \\
  --samples 16 --width 1280 --output_folder regenerated_split_process \\
  2>&1 | gzip -1 > audit/regenerated_split_process_render.log.gz
python scripts/encode_process_review_video.py --folders regenerated_split_process \\
  --plan op030_split_shots_v06.json --basename UR15_JB_OP030_split_process_v06_regenerated_review
```

IsaacLab内では `python` を `./isaaclab.sh -p` に置き換えます。
生成の方針は `data/video_delivery_policy.json` に記録しています。
同梱された旧packager/encoderは過去の再ベイク入力と由来を保持する資料です。
新規動画には上記の工程専用エンコーダを使用してください。

## 同梱ファイルの照合

```bash
python scripts/verify_process_review_package.py
```

`DELIVERY_SHA256.json` の全ファイルと、動画が指定の1種類だけであることを確認します。
現動画は完成済みMP4をそのまま採用し、再圧縮していません。
生成時の記録に残る他視点・rawの観測は旧出力の履歴であり、同梱動画ではありません。
`audit/op030_process_only_derivation_v06.json` に配布形式の変更と元ステージのSHAを記録しています。
幾何・姿勢の確認は補助観測であり、実機の保持力、締結品質や正式な物理妥当性の認定ではありません。
"""


def main() -> None:
    source = ROOT / "deliverables" / PACKAGE
    target = ROOT / "deliverables" / (PACKAGE + "_process_only")
    source_inventory = verify_directory(source)
    assert source_inventory["UR15_JB_OP030_split_v06.blend"]["sha256"] == NATIVE_SHA
    original = json.loads((ROOT / "audit/op030_split_delivery_v06.json").read_text())
    assert digest(source / "DELIVERY_SHA256.json") == original["inventory_sha256"]
    target.mkdir(exist_ok=False)
    removed = []
    for name in source_inventory:
        if name.endswith(".mp4") and name != VIDEO:
            removed.append(name)
            continue
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / name, destination)
    assert len(removed) == 3
    extra = [
        "data/video_delivery_policy.json",
        "scripts/encode_process_review_video.py",
        "scripts/verify_process_review_package.py",
        "analysis/process_only_delivery_scope_v06.md",
    ]
    for name in extra:
        shutil.copy2(ROOT / name, target / name)
    text = (target / PAGE).read_text()
    text, count = re.subn(r'<a href="[^"]*split_wide_v06_review.mp4">固定全景</a>', "", text)
    assert count == 1
    text, count = re.subn(r"<section><h2>固定全景</h2>.*?</section>", "", text, flags=re.DOTALL)
    assert count == 1
    assert text.count("4本の動画") == 1
    text = text.replace("4本の動画", "工程動画1本")
    assert len(re.findall(r"<video\b", text)) == 1
    assert "_wide_v06_review.mp4" not in text and "_raw.mp4" not in text
    (target / PAGE).write_text(text)
    (target / DOCUMENT).write_text(document_text((target / DOCUMENT).read_text()))
    (target / README).write_text(readme_text())
    selection_path = target / "analysis/op030_v06_package_evidence.json"
    selection = json.loads(selection_path.read_text())
    selection["source_selection_before_process_only"] = dict(
        sha256=digest(source / "analysis/op030_v06_package_evidence.json"),
        archive_sha256=original["archive_sha256"],
    )
    selection["observed_at"] = datetime.now().astimezone().isoformat()
    selection["status"] = "one_process_review_video_selected_browser_check_follows"
    videos = selection["video_plan"]
    videos["views"] = 1
    for key in ("measured_duration_s", "measured_video_sha256", "videos"):
        videos[key] = {VIDEO: videos[key][VIDEO]}
    videos["reports"] = {"process": videos["reports"]["process"]}
    selection["document"]["sha256"] = digest(target / DOCUMENT)
    save(selection_path, selection)
    portable = json.loads((target / "audit/op030_split_layout_portable_rebake_v06.json").read_text())
    for name, record in portable["copied_inputs"].items():
        assert digest(target / name) == record["sha256"], name
    derivation = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        user_instruction="Only *_split_process_*_review.mp4 for future generation and Downloads/ZIP video delivery",
        source_stage=str(source),
        source_inventory_sha256=original["inventory_sha256"],
        original_delivery_report_sha256=digest(ROOT / "audit/op030_split_delivery_v06.json"),
        original_archive_sha256=original["archive_sha256"],
        native_sha256=NATIVE_SHA,
        video=VIDEO,
        video_sha256=digest(target / VIDEO),
        video_reencoded=False,
        removed_video_files=removed,
        exact_rebake_inputs_unchanged=23,
        future_encoder="scripts/encode_process_review_video.py",
        future_generated_mp4_count=1,
        future_raw_mp4_intermediate=False,
        formal_physical_validity_verdict=None,
    )
    save(target / "audit/op030_process_only_derivation_v06.json", derivation)
    audit_path = target / "audit/op030_split_package_v06.json"
    package_audit = json.loads(audit_path.read_text())
    package_audit.update(
        observed_at=derivation["observed_at"],
        videos={"process_review": dict(path=VIDEO, sha256=digest(target / VIDEO))},
        derived_from_inventory_sha256=original["inventory_sha256"],
        scope="Single process-review MP4 projection; exact native and 23 rebake inputs unchanged",
    )
    package_audit["input_files"] = {
        path.relative_to(target).as_posix(): dict(sha256=digest(path), bytes=path.stat().st_size)
        for path in sorted(target.rglob("*"))
        if path.is_file() and path != audit_path
    }
    save(audit_path, package_audit)
    inventory = {
        path.relative_to(target).as_posix(): dict(sha256=digest(path), bytes=path.stat().st_size)
        for path in sorted(target.rglob("*"))
        if path.is_file()
    }
    assert [name for name in inventory if name.endswith(".mp4")] == [VIDEO]
    save(target / "DELIVERY_SHA256.json", inventory)
    verify_directory(target)
    save(
        ROOT / "audit/op030_process_only_stage_v06.json",
        dict(
            **derivation,
            stage=str(target),
            inventory_sha256=digest(target / "DELIVERY_SHA256.json"),
            file_count=len(inventory) + 1,
        ),
    )
    print("PROCESS_ONLY_V06_STAGED", target, len(inventory) + 1, flush=True)


if __name__ == "__main__":
    main()
