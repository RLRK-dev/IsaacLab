# v05d 保存姿勢データの復元と再描画

2026-09-27。v05d.2の「保持と受渡し」確認後、次の動画修正に使う保存データを復元した。
根拠は `recovery.json`、`recovery.log`、`render_readback.json` と新しく描いた12枚のPNG。

## 結果

ごみ箱に残っていたv05b入力をSHA照合し、既存の修正関数を変更せず順に適用した。
3段階すべて、保存して読み直したNPZのSHAが2026-09-24の監査記録と完全に一致した。

| 段階 | 直前の段階から変わる時点数 | 復元したNPZのSHA256 |
|---|---:|---|
| XYZの持上げ表示 v05c | 23 | `21a64890540a06d94c06c6ee8e607f90dbe9c5b69ddf14fe944135614e28c409` |
| 次品とヘッダーの保持表示 v05d | 493 | `72779ccf3e7a15087b45f2eeaa6cb5ccbb0ca1bef3cf7f06ac79a00c379d45b9` |
| 板保持表示 v05d最終 | 797 | `0bb2f0e4e55e40def49cd2cfd7eecf99e0e7a4bdc9b7ea4097768f7c1cc00044` |

各bankは1,785時点、304ノード、4×4表示行列。時刻、カメラ、ノード名を含む全フィールドを
保存読戻しで照合した。ここでいう完全一致はデータの同一性で、実機成立の判定ではない。

## 再描画の確認

既存v05b描画関数に最終bankを渡し、元のカメラ・画角で12場面を描いた。
旧払出し側の19表示ノードを省く処理と、103秒未満で蓋を隠す処理も元のまま。

- [供給・外組み・Cへの受渡し（6枚）](contact_1.jpg)
- [持ち替え・搭載・側壁・収納（6枚）](contact_2.jpg)

両一覧を補助目視した。供給・収納は同じXYZと20枠、受渡しと搭載はC主担当・C補助を表示し、
右側の完成品参照と工程説明が描かれた。これは少数時点の画像確認であり、連続軌道の干渉、
把持力、ねじ締結品質、個々の自由端の支持を確定する検証ではない。

今回、新しいMP4は生成していない。納品動画は従来のv05d一本を維持する。
H06/H05の後半4章は今回の再描画対象外。一時cloneにしかなかったv05d専用の動画生成・結合
スクリプト自体は未回収であり、今回復元したのは最終表示bankと既存描画関数への実行経路。

## 保存と再実行

`recovered/` に入力と3段階のbank、`previews/` に12PNGを保存する。これらはgit管理外。
入力と最終bank、PNG、監査JSONはDownloadsの既存レビュー内
`replay_data_20260927/` に追加保存する。コードと監査記録、一覧画像はgitで管理する。
8MBのbankを2MB上限のcommit hookから除外する設定変更は行わない。

記録済みの監査JSON・一覧画像を上書きしないよう、同じ `work/` 直下の新しいフォルダへ
2本の実行adapterだけをコピーして実行する。既存の出力先は再利用しない。

```bash
mkdir work/hvjb-display-bank-replay-local
cp work/hvjb-display-bank-recovery-v01-20260927/recover_bank.py work/hvjb-display-bank-replay-local/
cp work/hvjb-display-bank-recovery-v01-20260927/render_recovered.py work/hvjb-display-bank-replay-local/
env -u CONDA_PREFIX VIRTUAL_ENV=/home/rlrk/src/ur15-line-render/venv PYOPENGL_PLATFORM=egl TERM=xterm \
  ./isaaclab.sh -p work/hvjb-display-bank-replay-local/recover_bank.py \
  --source_bank /home/rlrk/Downloads/HVJB_保持と受渡しレビュー_v05d2_20260927/replay_data_20260927/data/source_v05b.npz
env -u CONDA_PREFIX VIRTUAL_ENV=/home/rlrk/src/ur15-line-render/venv PYOPENGL_PLATFORM=egl TERM=xterm \
  ./isaaclab.sh -p work/hvjb-display-bank-replay-local/render_recovered.py
```

実行adapterは旧絶対パスと現在のcloneの対応を監査JSONへ残す。
使用する既存コード・JSON・参照図・フォントのSHAを前後で照合する。
旧修正値、しきい値、模型形状、動作、物理仕様は変更していない。
既存のbank生成mainは旧パスと監査ファイルの不在を要求するため呼ばず、同じ修正関数を呼ぶ。
再計算・保存の手順は当時のbuild_bank.pyを踏襲し、出力SHAの一致を停止条件としている。

元のv05d.2納品が無い場合や、529ファイルの内容が変わった場合は納品処理を停止する。
納品前後で既存ファイルのSHAとMP4が1本であることを照合する。
