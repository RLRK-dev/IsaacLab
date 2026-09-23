# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Append the source-evidence and movie-coverage observations to the shared log."""

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
    assert delivery["file_count_after"] == 454 and delivery["mp4_count_after"] == 1
    log = VAULT / "log.md"
    before = log.read_bytes()
    index = (VAULT / "index.md").read_bytes()
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    title = "HVJB v05b: 公開組立6場面の照合と20仕事の動画内表現を記録"
    assert title.encode() not in before
    entry = f"""\n## [{now:%Y-%m-%d %H:%M:%S} JST] discovery | {title}

- 根拠は保存済み公式組立映像・6枚の元PNG、既存観察JSON、20仕事の工程表、
  動画v05b構成JSONと納品ファイル。観察を増補して実物固定具や未接続端の両端を推定する作業ではない。
- 2025-06-07のAmpere EV映像について0:24/0:50/2:26/2:34/2:38/2:50の全画面を縮小表示し、
  元画像SHAと縮小画素を照合。筐体外の下板側・補機ヒューズ板側、同時搭載、搭載後の自由端と内部工具、
  側面開口通過後の状態を既存観察文と並べた。D30/D31は採用済み仮手順、D42の工具対象は未特定。
  2025年実作業と指定完成写真の同一製造版は未確認。
- 20仕事全件を16工程場面へ双方向照合。模式動作の場面を持つ仕事15、
  静止説明だけの仕事5（D01/D42/D61/D70/D71）。D81は復路の模式動作と準備・補給の静止説明を併用。
  これらは動画内の表現区分であり工程完了率・物理成立の分類ではない。
  92写真特徴も92件の組立動作完了を意味しない。
- Downloads/HVJB_ライン全体レビュー_v05b_20260923/index_v05b_2.html が今回の入口。
  公開映像照合15ファイルと仕事対応10ファイルを追加後、全452ファイルの一覧を採取。
  日付付き作業記録・成果物一覧を2ファイル追加し454ファイル、MP4は既存v05bの1本。
  既存452ファイルはSHA一致で保存。
- 最新動画SHA256は65ed3f0f861370c55e3d09de5b6d5d17889aea14d1394de757aba7cf2360ba03。
  工程・モデル・動作は今回の照合ページ追加で変更していない。
  HTMLブラウザ操作は未観察、静的参照とJavaScript構文・画像補助観察を区別。
  正式な物理妥当性・把持力・締結品質の判定なし。
- 記録は work/hvjb-public-assembly-review-v01-20260923、
  work/hvjb-movie-coverage-v01-20260923、work/hvjb-day-record-20260923。
  共有ツリーの既存作業やVault前面状態を編集せず、logへ追記のみ。
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
    print("VAULT_DAY_RECORD_APPENDED previous_prefix_unchanged=True", flush=True)


if __name__ == "__main__":
    main()
