# UR15 OP030 千鳥配置 v06

`review_OP030_split_v06.html` を開くと、工程説明付き動画と160個の工程ジャンプを利用できます。
動画は `UR15_JB_OP030_split_process_v06_review.mp4` の1本です。1280×720、15 fps、約7分49秒。
今後も `*_split_process_*_review.mp4` だけを生成・納品します。

ケーブル設置のBを反対側へ移し、A・B・Cを千鳥配置にしました。
パレット原点は789 mmで一定です。A・Cの動作、F01の外部ハーネス支持を継承しています。
Bは両腕で取得・曲げ・設置し、解放後に同時180 mm上昇します。
2段循環の下段返送・両端移載は未実装です。寸法・部品・確認範囲は `OP030_三ST工程・部品確認書_v06.md` を参照してください。

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
blender -b --python-exit-code 1 -P scripts/render_op030_v02.py -- \
  --blend UR15_JB_OP030_split_v06.blend --views process \
  --shot_plan op030_split_shots_v06.json --video --engine CYCLES \
  --samples 16 --width 1280 --output_folder regenerated_split_process \
  2>&1 | gzip -1 > audit/regenerated_split_process_render.log.gz
python scripts/encode_process_review_video.py --folders regenerated_split_process \
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
