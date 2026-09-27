# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Append observed delivery-path loss and the checked replacement location."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
VAULT = Path("/home/rlrk/IsaacLab/thread_isaac_lab/thread-vault")


def main() -> None:
    receipt = ROOT / "vault_log_receipt.json"
    assert not receipt.exists()
    delivery = json.loads((ROOT / "delivery_receipt.json").read_text())
    assert delivery["files_copied_and_read_back"] == 529 and delivery["mp4_count"] == 1
    index = (VAULT / "index.md").read_bytes()
    log = VAULT / "log.md"
    before = log.read_bytes()
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    title = "HVJB保持受渡し表示を追加、納品先不在により新規フォルダへ保存"
    assert title.encode() not in before
    entry = f"""\n## [{now:%Y-%m-%d %H:%M:%S} JST] discovery | {title}

- ユーザーがv05d.1確認済みと述べた後、既存20仕事の保持・受渡しを確認ページへ追加した。
  16仕事の記述とC継続予約は原文を保持。物流3仕事と準備1仕事は現行方針で説明し、
  旧保存カードの二段循環・G-OUTを使用していない。新しい支持面や採用機種は決めていない。
- ブラウザで20仕事の往復、12手先用途の往復、8動画場面のシークと戻るを確認した。
  保存画面6枚を補助目視。ページ例外0。幅430pxの3仕事で水平はみ出し0。
  これらは資料とUIの観測であり、実動作・正式な物理妥当性の判定ではない。
- Downloadsの旧v05dフォルダはpreflight時に522ファイル照合済みだったが、
  追加実行時にFileNotFoundError、2026-09-27 13:17 JSTの読取ではフォルダ不在だった。
  原因・実行者は不明。当セッションの追加処理は書込み前に停止している。
- 保存済み522ファイルと今回7ファイルを、新規フォルダへ保存し全529ファイルをSHAで読戻した。
  入口：{delivery["entry"]}
  動画は既存v05dの1本、SHA256 {delivery["video_sha256"]}。
  元の動画生成スクリプト・行列bankが未回収という制約は解消していない。
- 記録は分離clone work/hvjb-line-progress-20260927 内の
  work/hvjb-handoff-trace-v01-20260927。DELIVERY_CHANGE.md と delivery_receipt.json を参照。
""".encode()
    with log.open("ab") as writer:
        writer.write(entry)
    after = log.read_bytes()
    assert after[: len(before)] == before and entry in after[len(before) :]
    result = {
        "observed_at": now.isoformat(),
        "index_sha256_read_before_append": hashlib.sha256(index).hexdigest(),
        "previous_prefix_sha256": hashlib.sha256(before).hexdigest(),
        "previous_bytes": len(before),
        "entry_sha256": hashlib.sha256(entry).hexdigest(),
        "previous_prefix_unchanged": True,
    }
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("HANDOFF_VAULT_RECORD_APPENDED previous_prefix_unchanged=true")


if __name__ == "__main__":
    main()
