# 小型端末保持治具 v0.1 の再生成

配布フォルダーの `端末保持治具3D比較_v01.html` は、そのままブラウザーで開ける。
メッシュはHTMLへ内蔵している。ドラッグで回転、ホイールで拡大縮小し、2案・5姿勢を切り替える。
GLBはそれぞれ押さえ閉の比較姿勢、Blenderファイルは2案×5姿勢の静的シーンを収録する。
形状比較の範囲と未確定事項は `端末保持治具_比較記録_v01.md` を参照。

## 入力と依存

- `inputs/hand_terminal_meshes_v01.json`：前回EDGE/GUIDEの保存payload。今回はEDGEのみを再利用する。
  SHA-256は `22e4d62739debfe3c20d59d8223ea6fa6703d50ebd425d54bb9def403eaf60a9`。
  生成器が照合し、不一致なら停止する。
- `pallet_terminal_retainer_v01.json`：今回の仮寸法・5姿勢・未確定欄。
- `scripts/`：新規生成器、レンダラー、HTMLテンプレートと、再利用する3本の補助スクリプト。
- `inputs/Klauke_6R6.*`：参照した元端子形状の記録。今回の生成は保存payloadを使うため、STEP変換は行わない。
  Ampere内部への採用を示す資料ではない。
- `licenses/`：IsaacLabとRobotiqメッシュのライセンス。メーカー参照CADの権利はメーカーに帰属する。

Python側は既存環境のNumPy、SciPy、trimeshを使用する。実行した既存環境は
`/home/rlrk/src/ur15-line-render/venv`、Blenderは4.5.13 LTS。
IsaacLabコアに新たな依存パッケージを加える手順ではない。

## 実行例

以下はIsaacLabリポジトリで、Downloadsへ配布したフォルダーを入力にする例。
出力フォルダー `retainer_rebuilt_v01` が無い状態で実行する。既存出力は削除・上書きせず、別名を選ぶ。

```bash
retainer_package='/home/rlrk/Downloads/THREAD_端末保持治具_v01_20260913'
retainer_output='/tmp/retainer_rebuilt_v01'

TERM=xterm-256color VIRTUAL_ENV=/home/rlrk/src/ur15-line-render/venv \
  ./isaaclab.sh -p "$retainer_package/scripts/build_pallet_terminal_retainer_v01.py" \
  --config "$retainer_package/pallet_terminal_retainer_v01.json" \
  --source_payload "$retainer_package/inputs/hand_terminal_meshes_v01.json" \
  --output_directory "$retainer_output"

/home/rlrk/.local/opt/blender-4.5.13-linux-x64/blender \
  --background --python-exit-code 1 \
  --python "$retainer_package/scripts/render_pallet_terminal_retainer_v01.py" \
  -- --directory "$retainer_output"
```

生成器の終了表示は `PALLET_TERMINAL_RETAINER_STATIC_DONE`。
Blenderの終了表示は `PALLET_TERMINAL_RETAINER_READBACK_DONE`、終了コードは0。
ラッパーの終了だけで成功とはせず、両表示と出力JSONを確認する。

再生成したHTML内の補助リンクを使う場合は、同じ出力フォルダーへ設定と比較記録もコピーする。

```bash
cp "$retainer_package/pallet_terminal_retainer_v01.json" "$retainer_output/"
cp "$retainer_package/端末保持治具_比較記録_v01.md" "$retainer_output/"
```

## 記録の読み方

- `pallet_terminal_retainer_geometry_v01.json`：実行時入力のSHA、GLBの読戻し、仮工具への投影値。
- `pallet_terminal_retainer_native_v01.json`：新規nativeのSHA、厳密な保存読戻し、静止姿勢の表面交差観測。
- `pallet_terminal_retainer_browser_v01.json`：配布HTMLで行った20操作の表示観測。Blender生成器の出力ではない。
- `pallet_terminal_retainer_provenance_v01.json`：今回の根拠資料と、修正・再実行の対応。
- `audit/`：初回失敗のログ・行列差分、修正後の実行ログ、PNG画角修正時のログ。
- `delivery_manifest.json`：同梱ファイルのSHAと、再生成コードを記録したコミット。

初回の非表示行列評価に関する失敗は合格記録に含めず、別出力先での修正後の観測を使っている。
最終native保存後に、開放姿勢PNGのカメラ範囲だけを広げて再描画した。nativeのSHAは変わっていない。
同梱レンダラーにはこの画角修正も反映してある。

再生成では保存先パスやBlender内の保存情報が変わるため、native全体が配布版とバイト一致することは
要求していない。各実行内で保存前後の行列・頂点・面・メッシュ数・表示フラグが厳密一致するかを記録する。
これらは幾何と保存の観測であり、保持力、ロック、搬送、実物適合の判定ではない。
