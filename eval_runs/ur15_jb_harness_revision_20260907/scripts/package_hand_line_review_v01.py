# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Copy the single process review and its editable native with SHA verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEM = "UR15_JB_OP010_OP030_split_process_hands_v02_review"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def review_page():
    return f'''<!doctype html>
<html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>OP010〜OP030 初期ハンド・動作レビュー</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#10191e;color:#e7eff1;font:16px/1.7 sans-serif}}
main{{max-width:1280px;margin:auto;padding:28px}}h1{{font-size:26px;margin:8px 0}}
p{{color:#bcccd1}}video{{width:100%;background:#000;border-radius:8px}}
nav,.playback{{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}}
button,a{{font:inherit}}button{{border:1px solid #527d88;background:#213943;color:#edfaff;
padding:8px 14px;border-radius:5px;cursor:pointer}}button:focus-visible,a:focus-visible{{outline:3px solid #73d7e8}}
a{{color:#80d6e7}}.note{{border-left:3px solid #527d88;padding-left:16px}}
</style><main>
<p>THREAD · 初期仕様を動画で確認</p><h1>OP010〜OP030 ハンド・動作レビュー</h1>
<p>OP010：XYZ直交3軸・20個収納。単腕と双腕を作業に合わせて配置した初期版です。</p>
<video id="video" controls preload="metadata" src="{STEM}.mp4"></video>
<nav aria-label="工程へ移動">
<button data-time="0">0:00 OP010・XYZ移載</button>
<button data-time="12">0:12 OP020・単腕</button>
<button data-time="26">0:26 OP030-A・保持と締結</button>
<button data-time="40">0:40 OP030-B・両端保持</button>
<button data-time="54">0:54 OP030-C・代表動作</button>
</nav><div class="playback">
<button id="back">3秒戻る</button><button data-speed="0.5">0.5倍速</button>
<button data-speed="1">通常速度</button><button id="forward">3秒進む</button>
</div>
<p class="note">OP030は、別ワークで並行する同じ動作をA・B・Cの視点で繰り返しています。
内部の配置・部品寸法と工具取付部は初期値です。ケーブルの曲線は幾何アニメーションです。
全接続の完了、実ケーブルの曲がり方、把持・締結品質を示す動画ではありません。</p>
<p><a href="{STEM}.mp4">動画ファイル</a> ／
<a href="UR15_JB_initial_hands_v02.blend">編集用Blenderモデル</a> ／
<a href="README.md">変更内容と確認範囲</a></p>
<script>
const video=document.getElementById('video');
document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>{{video.currentTime=Number(b.dataset.time)}});
document.querySelectorAll('[data-speed]').forEach(b=>b.onclick=()=>{{video.playbackRate=Number(b.dataset.speed)}});
document.getElementById('back').onclick=()=>{{video.currentTime=Math.max(0,video.currentTime-3)}};
document.getElementById('forward').onclick=()=>{{video.currentTime=Math.min(video.duration||68,video.currentTime+3)}};
</script></main></html>
'''


def package(output):
    if output.exists():
        raise FileExistsError(output)
    video_report = json.loads((ROOT / f"audit/{STEM}_video.json").read_text())
    assert video_report["generated_mp4_count"] == 1 and not video_report["generated_raw_mp4"]
    native = ROOT / "UR15_JB_initial_hands_v02.blend"
    assert digest(native) == video_report["native_sha256"]
    for name in ("build", "surface_probe"):
        observation = json.loads((ROOT / f"audit/hand_line_review_v01_{name}.json").read_text())
        assert observation["native_sha256"] == video_report["native_sha256"]
    inputs = {
        ROOT / (STEM + ".mp4"): Path(STEM + ".mp4"),
        native: Path(native.name),
        ROOT / "analysis/hand_line_review_v01.md": Path("README.md"),
    }
    for pattern in (
        "audit/hand_line_review_v01_prepare.json",
        "audit/hand_line_review_v01_build.json",
        "audit/hand_line_review_v01_surface_probe.json",
        "audit/hand_line_review_v01_pusher_correction.json",
        f"audit/{STEM}_video.json",
        "audit/hand_line_final_v02_render.log",
        "previews/hand_line_final_v02/manifest.json",
        "data/hand_line_review_v01*.json",
    ):
        for path in ROOT.glob(pattern):
            inputs[path] = path.relative_to(ROOT)
    for name in ("motion.npz", "meshes.json.gz"):
        path = ROOT / "data/hand_line_review_v01" / name
        inputs[path] = path.relative_to(ROOT)
    for pattern in ("*hand_line_review*.py",):
        for path in (ROOT / "scripts").glob(pattern):
            inputs[path] = Path("source") / path.name
    output.mkdir(parents=True)
    manifest = []
    for source, relative in inputs.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        identity = digest(source)
        assert digest(target) == identity, target
        manifest.append(
            {"file": str(relative), "source": str(source), "sha256": identity, "bytes": target.stat().st_size}
        )
    (output / "review.html").write_text(review_page(), encoding="utf-8")
    assert len(list(output.rglob("*.mp4"))) == 1
    (output / "manifest.json").write_text(
        json.dumps({"files": manifest, "mp4_count": 1, "native_textures_packed": True}, ensure_ascii=False, indent=2)
        + "\n"
    )
    print("HAND_LINE_DELIVERY_COMPLETE", output, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", type=Path, required=True)
    package(parser.parse_args().output_dir)
