# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Append the observed v05d recovery and review-link delivery to the shared log."""

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
    recovery = json.loads((ROOT.parent / "hvjb-resume-v05d-20260927/recovery_receipt.json").read_text())
    assert delivery["original_files_unchanged"] == recovery["files_read_back"] == 515
    assert delivery["files_added_and_read_back"] == 7 and delivery["mp4_count"] == 1
    index = (VAULT / "index.md").read_bytes()
    log = VAULT / "log.md"
    before = log.read_bytes()
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    title = "HVJB v05d納品を読戻し、20仕事と12手先用途の往復リンクを追加"
    assert title.encode() not in before
    entry = f"""\n## [{now:%Y-%m-%d %H:%M:%S} JST] discovery | {title}

- ユーザーの再開指示により、前回の一時cloneを確認したが存在しなかった。
  forkから da5830de78a86c219c129702c449ff74ecb8b5ca を取得し、永続側
  work/hvjb-line-progress-20260927 内の分離cloneで継続した。共有ツリーの既存変更を流用していない。
- Downloads/HVJB_ライン全体レビュー_v05d_20260924 の515ファイルを保存manifestと全件照合した。
  動画SHA256 0cdcd4d43831c3f805aa4e5960b666e7965ee6f1ac38b59d31645630d1dd40da は一致。
  納品側の動画監査・PNGは残っているが、未commitだったv05d原生成スクリプト・行列bank・
  旧ブラウザ検査記録は未回収。新しい物理実行や再生成の成功として扱わない。
- 既存 variants.json の12用途・20仕事対応をそのまま用い、仕事から手先図へ移動する入口
  index_v05d_1.html と、手先図から同じ仕事へ戻るリンクを追加した。
  20仕事・92特徴・22動画場面の内容、用途の対応、比較形状は変更していない。
- 20仕事の表示と12用途の往復、D50の動画章移動、ブラウザの戻る、幅430pxの3場面を操作した。
  ページ例外0、予期しないrequest failure 0。8枚の画面は補助目視した。
  初回のChromeはsetsockopt制限で起動前に停止し、同じコードのホスト実行でUI確認に進んだ。
- 納品は7ファイルの追加のみ。既存515ファイルはSHA一致、MP4は既存v05dの1本。
  H05他端末、H06ユニット用爪、P22取付工程と5仕事の個別図なしを残した。
  把持力、実機機種、施工採用、正式な物理妥当性を確定していない。
- 記録は分離cloneの work/hvjb-resume-v05d-20260927 と
  work/hvjb-job-hand-links-v01-20260927。期限9月24日22:00を9月27日へ読み替えていない。
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
        "entry_present": True,
    }
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("VAULT_JOB_HAND_LINKS_APPENDED previous_prefix_unchanged=true")


if __name__ == "__main__":
    main()
