# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Verify and optionally stage the split OP030 review and exact rebake inputs."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import shutil
import tempfile
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from encode_op030_v02 import render_log_read

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = "UR15_JB_OP030_20260910_v05"
NATIVE = "UR15_JB_OP030_split_v05.blend"
PLAN = "data/op030_split_shots_v05.json"
MOTION = "data/op030_split_animation_v05.npz"
PREPARED = "data/op030_split_animation_v05.json"
NATIVE_AUDIT = "audit/op030_split_native_v05.json"
DOCUMENT = "OP030_三ST工程・部品確認書_v05.md"
PAGE = "review_OP030_split_v05.html"
README = "README_OP030_split_v05.md"
PACKAGE_AUDIT = "audit/op030_split_package_v05.json"
INVENTORY = "DELIVERY_SHA256.json"
REVIEW_STATUS = (
    "Aは両腕同時240 mm退避、Bは同時進入と180 mm退避、Cは大小工具同時締結と近い供給器への短い移動を反映しました。"
)
SCRIPT_FILES = (
    "scripts/package_op030_split_v05.py",
    "scripts/animate_op030_split_v05.py",
    "scripts/op030_split_animation.py",
    "scripts/op030_fixed_height_timeline_v04.py",
    "scripts/op030_definition.py",
    "scripts/build_jb_op020.py",
    "scripts/allocation_product.py",
    "scripts/build_allocation_review.py",
    "scripts/clean_appearance.py",
    "scripts/continuous_common.py",
    "scripts/jb_harness.py",
    "scripts/op020_jb_geometry.py",
    "scripts/transparent_enclosure.py",
    "scripts/render_op030_v02.py",
    "scripts/encode_op030_v02.py",
    "scripts/encode_review_video.py",
    "inputs/v02_source/inputs/v01_source/scripts/build_op020.py",
    "inputs/v02_source/inputs/v01_source/scripts/build_cameras.py",
    "inputs/v02_source/inputs/v01_source/op010_base/scripts/build_op010_blender.py",
)


def digest(path: Path) -> str:
    """Return the SHA-256 of one file."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def local_path(root: Path, relative: str) -> Path:
    """Resolve a package-relative path, rejecting absolute paths and escapes."""
    value = Path(relative)
    if value.is_absolute() or ".." in value.parts or not value.parts:
        raise ValueError(f"Expected a package-relative path: {relative}")
    target = root / value
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"File escapes package root: {relative}")
    return target


def read_json(root: Path, relative: str) -> dict:
    """Read one UTF-8 package record."""
    return json.loads(local_path(root, relative).read_text(encoding="utf-8"))


def video_stem(view: str) -> str:
    """Return the fixed v05 filename stem for a review view."""
    return f"UR15_JB_OP030_split_{view}_v05"


def phase_records(plan: dict, frames: int, fps: int) -> list[dict]:
    """Validate contiguous chapter frames and their times [s]."""
    phases = plan["phases"]
    next_frame = 1
    for phase in phases:
        first, last = phase["first_frame"], phase["last_frame"]
        if first != next_frame or not first <= last <= frames or not phase["label"].strip():
            raise ValueError(f"Invalid phase frame range: {phase}")
        for field, expected in (("start_s", (first - 1) / fps), ("stop_s", last / fps)):
            value = float(phase[field])
            if not math.isfinite(value) or abs(value - expected) > 1e-6:
                raise ValueError(f"Phase {field} does not match its native frame: {phase}")
        next_frame = last + 1
    if next_frame != frames + 1:
        raise ValueError("Phases do not cover the entire native timeline")
    return phases


def collect_inputs(root: Path, evidence: list[str]) -> tuple[dict, dict[str, dict]]:
    """Verify required native, motion and encoded-video provenance before copying.

    Args:
        root: Source package root.
        evidence: Additional report paths relative to the root.

    Returns:
        Validated presentation context and the exact selected file inventory.
    """
    files = {}

    def include(relative: str, expected: str | None = None) -> str:
        path = local_path(root, relative)
        if not path.is_file():
            raise FileNotFoundError(f"Missing required input: {relative}")
        sha = digest(path)
        if expected is not None and sha != expected:
            raise ValueError(f"SHA-256 mismatch: {relative}")
        files[relative] = dict(sha256=sha, bytes=path.stat().st_size)
        return sha

    for relative in (PLAN, PREPARED, NATIVE_AUDIT, DOCUMENT, *SCRIPT_FILES, *evidence):
        include(relative)
    plan, prepared, native_check = (read_json(root, name) for name in (PLAN, PREPARED, NATIVE_AUDIT))
    if plan["native"] != NATIVE or plan["motion"] != Path(MOTION).name or prepared["output"] != MOTION:
        raise ValueError("The prepared motion or presentation points to a different version")
    native_sha = include(NATIVE, plan["native_sha256"])
    motion_sha = include(MOTION, prepared["output_sha256"])
    if plan["motion_sha256"] != motion_sha or native_check["prepared_sha256"] != motion_sha:
        raise ValueError("Native/prepared/presentation motion identities differ")
    if native_check["output_sha256"] != native_sha:
        raise ValueError("Native readback record belongs to another saved native")
    source = prepared["static_native"]
    include(source["path"], source["sha256"])
    include(source["manifest"], source["manifest_sha256"])
    static = read_json(root, source["manifest"])
    if static["output_sha256"] != source["sha256"] or native_check["source"] != source:
        raise ValueError("Static native, static manifest and baked-native source do not agree")
    frames = prepared["frames"]
    if not isinstance(frames, int) or frames < 1 or prepared["fps"] != 30:
        raise ValueError("Expected a nonempty 30 fps native motion")
    if plan["frame_end"] != frames or native_check["frames"] != frames or native_check["fps"] != 30:
        raise ValueError("Native/prepared/presentation timelines differ")
    if native_check["matrix_readback"]["failures"]:
        raise ValueError("Native matrix readback has unresolved failures")
    if plan["phases"] != prepared["phases"]:
        raise ValueError("Presentation captions differ from the prepared timeline")
    phase_records(plan, frames, 30)
    video_checks, expected_duration = _collect_video_inputs(root, plan, frames, native_sha, motion_sha, files, include)
    return dict(
        plan=plan,
        prepared=prepared,
        frames=frames,
        duration_s=expected_duration,
        native_sha256=native_sha,
        motion_sha256=motion_sha,
        video_checks=video_checks,
        evidence=evidence,
    ), files


def _collect_video_inputs(
    root: Path,
    plan: dict,
    frames: int,
    native_sha: str,
    motion_sha: str,
    files: dict[str, dict],
    include: Callable,
) -> tuple[dict, float]:
    """Verify saved encode and render records, adding only manifests and logs."""
    expected_frames = list(range(1, frames + 1, 2))
    expected_duration = len(expected_frames) / 15
    video_checks = {}
    for view in ("process", "wide"):
        stem = video_stem(view)
        manifest_file = f"audit/{stem}_video.json"
        include(manifest_file)
        report = read_json(root, manifest_file)
        for field, expected in (
            ("native_sha256", native_sha),
            ("motion_sha256", motion_sha),
            ("presentation_sha256", files[PLAN]["sha256"]),
            ("frame_count", len(expected_frames)),
        ):
            if report[field] != expected:
                raise ValueError(f"Video {view}: {field} differs from the pinned inputs")
        if abs(report["duration_s"] - expected_duration) > 1e-6:
            raise ValueError(f"Video duration differs from the complete timeline: {view}")
        mapping = report["mapping"]
        if [row["native_frame"] for row in mapping] != expected_frames:
            raise ValueError(f"Video frame mapping is incomplete or duplicated: {view}")
        if view == "process":
            ranges = plan["ranges"]
            next_frame = 1
            for shot in ranges:
                if shot["first_frame"] != next_frame or shot["last_frame"] < next_frame:
                    raise ValueError("Shot ranges are not contiguous")
                next_frame = shot["last_frame"] + 1
            if next_frame != frames + 1:
                raise ValueError("Shot ranges do not cover the native timeline")
            index = 0
            for row in mapping:
                while row["native_frame"] > ranges[index]["last_frame"]:
                    index += 1
                if row["camera"] != ranges[index]["camera"]:
                    raise ValueError("A video frame uses a different planned camera")
        for suffix in ("raw", "review"):
            name = f"{stem}_{suffix}.mp4"
            check = report["videos"][name]
            include(name, check["sha256"])
            if check["full_decode_exit_code"] != 0 or check["full_black_intervals"]:
                raise ValueError(f"Full-decode or black-frame check failed: {name}")
            streams = [s for s in check["metadata"]["streams"] if s["codec_type"] == "video"]
            if len(streams) != 1:
                raise ValueError(f"Expected one video stream: {name}")
            stream = streams[0]
            settings = report["render_settings"]
            if (
                int(stream["nb_read_frames"]) != len(expected_frames)
                or stream["r_frame_rate"] != "15/1"
                or stream["width"] != settings["width"]
                or stream["height"] != settings["height"]
                or abs(float(check["metadata"]["format"]["duration"]) - expected_duration) >= 0.02
            ):
                raise ValueError(f"Decoded video metadata does not match the timeline/settings: {name}")
        include(f"data/{stem}.ass")
        source_frames = {}
        if not report["source_manifests"]:
            raise ValueError(f"Video has no render provenance: {view}")
        for source_manifest in report["source_manifests"]:
            include(source_manifest["path"], source_manifest["sha256"])
            include(source_manifest["render_log"], source_manifest["render_log_sha256"])
            rendered = read_json(root, source_manifest["path"])
            _, complete, overflow = render_log_read(local_path(root, source_manifest["render_log"]))
            if not complete or overflow:
                raise ValueError(f"Render log is incomplete or records shadow buffer overflow: {view}")
            if (
                not rendered["complete"]
                or rendered["native_sha256"] != native_sha
                or rendered["renderer_sha256"] != files["scripts/render_op030_v02.py"]["sha256"]
                or rendered["native_frame_end"] != frames
                or rendered["output_fps"] != 15
                or rendered["settings"] != report["render_settings"]
            ):
                raise ValueError(f"Render manifest does not match the video source: {view}")
            if view == "process" and rendered["shot_plan_sha256"] != files[PLAN]["sha256"]:
                raise ValueError("Render manifest uses a different presentation plan")
            for row in rendered["images"]:
                if row["view"] != view or row["frame"] in source_frames:
                    raise ValueError(f"Render frame view mismatch or duplicate: {view}")
                source_frames[row["frame"]] = row
        if sorted(source_frames) != expected_frames:
            raise ValueError(f"Render manifests do not cover every encoded frame: {view}")
        for row in mapping:
            source_row = source_frames[row["native_frame"]]
            if source_row["sha256"] != row["png_sha256"] or source_row["camera"] != row["camera"]:
                raise ValueError(f"Encoded-to-rendered frame mapping differs: {view}")
        video_checks[view] = dict(path=manifest_file, sha256=files[manifest_file]["sha256"])
    return video_checks, expected_duration


def page_text(context: dict) -> str:
    """Create an offline review page with dynamic timeline jumps [s]."""
    buttons = "".join(
        f'<button data-time="{p["start_s"]:.6f}">{i:02d} {html.escape(p["label"])}</button>'
        for i, p in enumerate(context["plan"]["phases"], 1)
    )
    process, wide = (video_stem(view) + "_review.mp4" for view in ("process", "wide"))
    evidence = " / ".join(
        f'<a href="{html.escape(path, quote=True)}">{html.escape(Path(path).name)}</a>'
        for path in (NATIVE_AUDIT, *context["evidence"])
    )
    return f"""<!doctype html><html lang="ja"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UR15 OP030｜支持部・内部ケーブル 3 ST v05</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#edf2f4;color:#17313d;font-family:system-ui,sans-serif}}
main{{max-width:1180px;margin:auto;padding:26px 20px 60px}}h1{{font-size:clamp(24px,4vw,38px)}}
p{{line-height:1.8}}section{{background:white;padding:20px;margin:20px 0;border-radius:10px}}
video{{display:block;width:100%;border-radius:7px}}a{{color:#075a83;overflow-wrap:anywhere}}
.links,.chapters{{display:flex;gap:8px;flex-wrap:wrap}}.chapters{{margin-top:16px}}
button,.links a{{padding:9px 11px;border:1px solid #b8cbd6;background:white;border-radius:6px;
font:inherit;text-align:left;overflow-wrap:anywhere}}button{{font-size:13px;cursor:pointer}}
button:hover{{background:#e6f2fa}}small{{color:#4b6675}}table{{width:100%;border-collapse:collapse}}
td,th{{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid #d4dfe5}}
code{{overflow-wrap:anywhere}}summary{{cursor:pointer}}</style><main>
<small>EV用ジャンクションボックス＋高電圧ハーネス / OP030 / v05</small>
<h1>支持部取付・ケーブル設置・端子締結を3つのSTで行う</h1>
<p>同じ製品とパレットをA→B→Cへ搬送し、支持部、内部ケーブル、締結部品の組み付けを追跡します。
OP020で組み付けた外部ハーネスも保持します。パレット基準高さは789 mmで一定です。</p>
<p><small>{html.escape(REVIEW_STATUS)}</small></p>
<div class="links"><a href="{process}">工程動画</a><a href="{wide}">固定全景</a>
<a href="{NATIVE}">Blenderモデル</a><a href="{DOCUMENT}">工程・部品確認書</a>
<a href="{README}">再生成方法</a></div>
<section><h2>3 STの1サイクル</h2><video id="process" controls preload="metadata" src="{process}"></video>
<p><small>約{context["duration_s"] / 60:.1f}分。量産タクトの評価ではありません。</small></p>
<div class="chapters">{buttons}</div></section>
<section><h2>固定全景</h2><video controls preload="metadata" src="{wide}"></video>
<p>工程動画と同じ時間・同じ動作を固定視点で確認できます。</p></section>
<section><h2>工程と供給</h2><table><thead><tr><th>ST</th><th>工程</th><th>部品・工具</th></tr></thead><tbody>
<tr><td>A</td><td>端子支持部を取り付け、ボルトで固定</td><td>支持部20個を5×4の格子で供給。
右フィンガで設置・締結中の保持を行い、左の常設M4工具で固定。設置とボルト取得を並行。</td></tr>
<tr><td>B</td><td>ケーブルのみを取り出し、両手で曲げて設置</td><td>ケーブル10本を65 mmピッチで並列供給。
両端付近の被覆を把持して曲げ、両端を接続座へ設置してから解放。
左右同時に進入し、解放後も同時に鉛直180 mm退避します。ケーブル押さえ2基は撤去。</td></tr>
<tr><td>C</td><td>ケーブル端子を締結</td><td>左右腕へ常設した締付けユニットを使用。
大小工具を同時に締め、80 mmの軸抜きも同期します。手前に移設した供給器へ短い経路で戻り、
次のナットを両工具へ装填します。事前装填と供給個体の追跡を含みます。</td></tr></tbody></table>
<p>Aは支持部の2本目の締結後、右フィンガを開いてから両腕が同時に合計240 mm上昇します。
保存動作の時間はAが238.8秒、Bが151.667秒、Cが80.967秒です。
Cは事前装填8.767秒を含み、v04より28.2秒短くなりました。実機の量産タクトを示す値ではありません。
供給器へ戻る距離は、M6で約73%、M14で約51%短縮しています。
固定コンベアはv04の高さを継承し、ローラー上面756.5 mm・パレット原点789 mmで一定です。
2段循環の下段返送・両端移載は未実装です。</p>
<p>J1の内側接続部は、上から端子を設置・締結する仮配置へ変更しています。
23 mmのピッチを保ち、内側へ移した接続座と縦向きスタッドを入荷済みのサブアセンブリとして扱います。
外部ハーネスの嵌合部は継承し、内部配線の中心線長を新しい入口に合わせています。</p>
<p>締付けユニットの腕はフィンガを外した構成です。支持部の20個配置は指定条件です。
ケーブルの内訳5本＋5本、M4／M6／M14の締結寸法は検討用の仮設定で、採用機種・締付けトルクは未選定です。
10本の供給量は10サイクルの連続生産成立を意味しません。</p>
<p>オンハンドカメラ、外部LED、カバー枠を継承しています。透明パネルはありません。
寸法・動作・供給容量と未確認事項は工程・部品確認書を参照してください。</p></section>
<section><details><summary>補助確認とファイル対応</summary>
<p>保存モデル、動作配列、描画対応表、4本の動画のSHAを照合しています。
動画は全フレームのデコード完了を記録したものです。幾何・姿勢の確認は補助観測であり、
独立レビューによる正式な物理妥当性判定、接触力や電気的成立の確認ではありません。</p>
<p>{evidence}</p><p><a href="{PACKAGE_AUDIT}">配布入力の照合</a> /
<a href="{INVENTORY}">同梱ファイルのSHA一覧</a></p></details></section>
</main><script>document.querySelectorAll('[data-time]').forEach(b=>b.addEventListener('click',()=>{{
const v=document.getElementById('process');v.currentTime=Number(b.dataset.time);v.play();
v.scrollIntoView({{behavior:'smooth',block:'center'}});}}));</script></html>
"""


def readme_text(context: dict) -> str:
    """Describe replay and exact rebake from the packaged saved inputs."""
    source = context["prepared"]["static_native"]
    return f"""# UR15 OP030 3 ST 工程確認 v05

`{PAGE}` を開くと、工程動画、固定全景、工程ジャンプ、確認書を参照できます。
字幕付きは `*_review.mp4`、同じ場面の字幕なしは `*_raw.mp4` です。
Blenderモデルは `{NATIVE}`、工程・部品確認書は `{DOCUMENT}` です。
支持部20個（5×4）、直線状ケーブル10本、常設締付け工具の3 STを収録しています。
パレット基準高さ789 mmを保ち、作業STでは昇降しません。
支持部を保持した締結、設置とボルト取得の並行、Aの両腕同時240 mm上昇を反映しています。
Bは両腕同時に進入し、解放後に同時180 mm鉛直退避します。
Aの保存動作は7,165フレーム・238.8秒、Bは4,551フレーム・151.667秒です。
Cは2,430フレーム・80.967秒で、事前装填264フレーム・8.767秒を含み、v04より28.2秒短縮しています。
Cの大小工具は同時締結と80 mm軸抜きを行い、M6のみ追加160 mm上昇してから補充へ戻ります。
供給器をCの手前側へ移し、工具本体の余分な半回転と待機位置を経由する大回りを省きました。
80 mm軸抜き後から供給器上方までの戻り距離は、M6で約73%、M14で約51%短縮しています。
{REVIEW_STATUS}
v04の搬送支持形状を継承し、ローラー上面756.5 mmと左右ランナー下面が接します。
ケーブル押さえ2基は撤去しました。2段循環の下段返送・両端移載は未実装です。
ケーブル5本＋5本の内訳とM4／M6／M14は仮設定で、工具機種・締付けトルクは未選定です。
J1内側は上締めの接続座・縦スタッドを備える受入サブアセンブリの仮設計です。
新しいJ1側6R6端子、可視被覆の中心線長、元ケース・外部嵌合部との対応は確認書に記載しています。
1製品の組付け動作であり、10回連続組付けや全ライン循環運転の完成は示しません。

## 保存した動作から再生成

展開フォルダーを複製し、そのルートで以下を実行します。フォルダー構成を維持してください。
保存した配列を使うため、IK、経路探索、元の設備生成スクリプトは再実行しません。
Blender 4.5.13とその付属NumPyを使用します。再ベイク・再描画にFCL/OMPLは不要です。

- 静的モデル: `{source["path"]}`
- 静的モデルの対応表: `{source["manifest"]}`
- 保存動作: `{MOTION}` と `{PREPARED}`
- ベイクコード: `scripts/animate_op030_split_v05.py` と同梱のimport先

19個のhelperと上記の静的モデル・対応表・保存動作2個を合わせた23入力を最小構成として扱います。
`scripts/op030_fixed_height_timeline_v04.py` は共通実装として旧名のまま再利用しています。
隔離フォルダーでの実再ベイク結果は、`audit/op030_split_layout_portable_rebake_v05.json` を参照してください。
同記録に全入力の前後SHA比較、保存姿勢の読み戻し、外部画像・外部libraryの数を記載しています。

```bash
blender -b --python-exit-code 1 -P scripts/animate_op030_split_v05.py --
```

このコマンドは複製先のモデル、`{PLAN}`、`{NATIVE_AUDIT}` を作り直します。
再保存でモデルのSHAは変わり得ます。新しく生成されたplanを次の描画に使用してください。
旧動画の照合記録は元の納品nativeに対応するため、新しい動画は別名で生成します。
JSON中の過去観測の絶対パスは由来の記録です。再ベイクの入力は上記の相対パスで解決します。

## 描画と動画化

PNG出力には十分な空き容量が必要です。次は工程動画1280×720・全景960×540の例です。
Blender内では30 fps、動画は全タイムラインから1フレームおきに描画した15 fpsです。
描画ログも動画化の照合に使うため、gzip圧縮して保存します。

```bash
mkdir -p audit
set -o pipefail
blender -b --python-exit-code 1 -P scripts/render_op030_v02.py -- \\
  --blend {NATIVE} --views process --shot_plan {Path(PLAN).name} \\
  --video --engine CYCLES --samples 16 --width 1280 \\
  --output_folder regenerated_split_process 2>&1 | gzip -1 > audit/regenerated_split_process_render.log.gz
python scripts/encode_op030_v02.py --folders regenerated_split_process --view process \\
  --plan {Path(PLAN).name} --basename UR15_JB_OP030_split_process_v05_regenerated

blender -b --python-exit-code 1 -P scripts/render_op030_v02.py -- \\
  --blend {NATIVE} --views wide --video --engine CYCLES \\
  --samples 16 --width 960 --output_folder regenerated_split_wide \\
  2>&1 | gzip -1 > audit/regenerated_split_wide_render.log.gz
python scripts/encode_op030_v02.py --folders regenerated_split_wide --view wide \\
  --plan {Path(PLAN).name} --basename UR15_JB_OP030_split_wide_v05_regenerated
```

動画化にFFmpeg／FFprobeとNoto Sans CJK JPが必要です。通常Pythonの追加パッケージは不要です。
描画はCycles／OPTIX対応GPUを使用します。光源設定は保存モデルに含まれます。
IsaacLab内で実行する場合は `python` を `./isaaclab.sh -p` に置き換え、スクリプトを絶対パスで指定します。
同梱render/encodeのv02というファイル名は再利用コードの名前です。入力planと出力名はv05を明示しています。

## ファイル照合と範囲

`{INVENTORY}` は同梱ファイルのサイズとSHAです。全描画PNGは含めず、
動画manifestと元の描画manifestにnativeフレーム・カメラ・PNGのSHAを残しています。
`{PACKAGE_AUDIT}` に入力native、保存動作、各動画の対応と検査範囲を記録しています。
動画の全デコードはエンコーダの完了記録をSHAで結び付けて照合します。
本スクリプトが動画を再エンコードすることはありません。

```bash
python scripts/package_op030_split_v05.py
```

このコマンドは入力を読み取り照合するだけです。`--stage` を付けた場合だけ
`deliverables/{PACKAGE}` を新規作成します。既存ステージは上書きせず、Downloadsへはコピーしません。
配列を変更した新しい経路計画や正式な物理妥当性評価は、この再生成手順の範囲外です。
"""


def stage_package(root: Path, context: dict, files: dict[str, dict]) -> Path:
    """Create one new staging directory after all source checks pass."""
    destination = root / "deliverables" / PACKAGE
    if destination.exists():
        raise FileExistsError(f"Keep the existing stage unchanged: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{PACKAGE}_", dir=destination.parent) as temporary:
        staging = Path(temporary) / PACKAGE
        staging.mkdir()
        for relative, record in files.items():
            target = local_path(staging, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path(root, relative), target)
            if digest(target) != record["sha256"]:
                raise ValueError(f"Input changed during copying: {relative}")
        (staging / PAGE).write_text(page_text(context), encoding="utf-8")
        (staging / README).write_text(readme_text(context), encoding="utf-8")
        report = dict(
            observed_at=datetime.now().astimezone().isoformat(),
            package=PACKAGE,
            native=dict(path=NATIVE, sha256=context["native_sha256"]),
            prepared_motion=dict(path=MOTION, sha256=context["motion_sha256"]),
            static_native=context["prepared"]["static_native"],
            videos=context["video_checks"],
            frames=context["frames"],
            duration_s=context["duration_s"],
            input_files=files,
            evidence=context["evidence"],
            checks=dict(
                input_sha256=True,
                copy_sha256=True,
                complete_native_to_render_to_video_mapping=True,
                full_decode="Encoder reports checked; videos bound to reports by SHA-256",
            ),
            formal_physical_validity_verdict=None,
            scope="Saved motion rebake and review package; no replan, physical verdict or Downloads publishing",
        )
        (staging / PACKAGE_AUDIT).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inventory = {
            path.relative_to(staging).as_posix(): dict(sha256=digest(path), bytes=path.stat().st_size)
            for path in sorted(staging.rglob("*"))
            if path.is_file()
        }
        (staging / INVENTORY).write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # Rename the finished directory only after copying and hashing it fully.
        if destination.exists():
            raise FileExistsError(destination)
        staging.rename(destination)
    return destination


def main() -> None:
    """Check inputs by default; copy only after an explicit --stage invocation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", action="store_true", help="Create the final local staging directory after verification"
    )
    parser.add_argument(
        "--evidence", nargs="*", default=[], help="Additional report paths relative to the project root"
    )
    args = parser.parse_args()
    context, files = collect_inputs(ROOT, args.evidence)
    output = dict(
        status="inputs_verified",
        source_files=len(files),
        source_bytes=sum(row["bytes"] for row in files.values()),
        frames=context["frames"],
        video_duration_s=context["duration_s"],
        stage_written=False,
    )
    if args.stage:
        output.update(stage_written=True, destination=str(stage_package(ROOT, context, files)))
    print(json.dumps(output, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
