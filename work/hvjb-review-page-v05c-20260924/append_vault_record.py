# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Append the v05c observations while preserving the shared log's prefix."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
VAULT = Path("/home/rlrk/IsaacLab/thread_isaac_lab/thread-vault")


def main():
    receipt = ROOT / "vault_log_receipt.json"
    assert not receipt.exists()
    delivery = json.loads((ROOT / "delivery_receipt.json").read_text())
    assert delivery["files_delivered_and_read_back"] == 483 and len(delivery["mp4_files"]) == 1
    log = VAULT / "log.md"
    before = log.read_bytes()
    index = (VAULT / "index.md").read_bytes()
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    title = "HVJB v05c: H06受渡し・H05開放の拡大章とXYZ表示相対位置を記録"
    assert title.encode() not in before
    entry = f"""\n## [{now:%Y-%m-%d %H:%M:%S} JST] discovery | {title}

- 根拠は既存比較形状と保存姿勢、生成PNG・動画の読戻し、隔離headless Chromeによるページ観測。
  H06 FC02の既存5状態から載置と取出しを300PNG、H05の3口/2口の保存開放姿勢を57PNGにした。
  H06は比較状態間の図示補間、H05は既存bankの順送り。新規の実ロボットIK・把持力の測定ではない。
- 全体模式動画のXYZ取出し区間で手と筐体の相対Z表示に0.015の変動があった。
  無寸法の図解座標であり15mmの意味ではない。既存搬送中の0.14オフセットへ接近表示を合わせ、
  1785標本の23、304列の5のみZを補正した。その他の行列、時刻、カメラは元bankと一致。
  原本bank SHA256 7702cadf9e412895a14c82d1a6b85a6aa659f2978c22e59ddf16e2714c793a60 は不変。
- 全体119秒にH06載置10秒・取出し10秒・H05 3口8秒・2口8.2秒を接続し、155.2秒の動画1本を
  工程PNGから直接符号化。1920×1080、15fps、2328フレーム。全編復号と47時点の画像を補助確認した。
  動画SHA256 18372546c5298ab6b908351e1cfa68db7fa6af596c5fc1f8a72bc9cb768b0c5e。
- 確認ページは20仕事・92写真特徴を維持。D00/D80/D50へ拡大章リンクを追加した。
  シーク直後にnative controlsの読込み表示が残ったため、2章の実再生・停止も確認し、
  時刻進行と表示の消失を観測した。全編をブラウザで連続視聴した記録ではない。
  clickとhashchangeの重複シークは整理。6件の同一MP4 media cancellationは監査に残し、
  ページ例外0・予期しないrequest failure0・各章readyState=4と別に記録している。
- Downloads/HVJB_ライン全体レビュー_v05c_20260924/index.htmlへ483ファイルをコピーし全SHA読戻し。
  MP4は1本、過去版は不変。H06/H05/動画の記録は515d403e、aee5143c、d2791394、
  ページはbebcd257e5。作業は分離clone /tmp/hvjb-line-progress-20260923 で進めた。
- 1段往復・20共用区画・S5_AB・20仕事・92写真特徴を維持。実機仕様、未公開接合点、
  センサ閾値、把持力、締結品質、正式な物理妥当性は確定していない。
  本日22:00 JSTまでのHVJB図解継続指示に従う。THREAD別レーンのrun/gate/前面状態は変更しない。
""".encode()
    with log.open("ab") as stream:
        stream.write(entry)
    after = log.read_bytes()
    assert after[: len(before)] == before and entry in after[len(before) :]
    result = {
        "observed_at": now.isoformat(),
        "log": str(log),
        "index_sha256_read_before_append": hashlib.sha256(index).hexdigest(),
        "previous_bytes": len(before),
        "previous_prefix_sha256": hashlib.sha256(before).hexdigest(),
        "entry_sha256": hashlib.sha256(entry).hexdigest(),
        "previous_prefix_unchanged": True,
        "entry_present_after_append": True,
    }
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("VAULT_V05C_RECORD_APPENDED previous_prefix_unchanged=True", flush=True)


if __name__ == "__main__":
    main()
