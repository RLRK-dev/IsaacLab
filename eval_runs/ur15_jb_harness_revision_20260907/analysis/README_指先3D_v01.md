# THREAD 指先3D確認 v0.1

2026-09-13。2F-85の既存リンクと、交換指先の形状検討サンプル。

`指先3D比較_v01.html` をブラウザーで開く。ネット接続・サーバー起動は不要。
左上でA／Aの下受け付き／B、近接／開き始め／開放／離隔を切り替える。
ドラッグで回転し、ホイールと「指先を拡大」で接触部を見る。右側で本体・対象物・工具域を表示／非表示にできる。
WebGLを使えない場合はPNGまたはGLBを開く。

- A：2本指の輪郭接触。第一候補には下へ差し込む受けを付けない。
- A_LIP：下受け付きの比較形状。開き始めのサンプル下面との位置関係を記録してある。
- B：2本指の短い丸底溝。直線サンプルの局所保持を比較する。

寸法は形状検討用の仮設定。Aは説明用円筒、Bのφ14 mmは旧H03比較値であり、Ampere部品の確定寸法ではない。
4姿勢は連続動作ではなく、S字形成、把持力、取付強度、カメラとの干渉、アーム軌道は未評価。
詳細は `指先3D確認記録_v01.md` を参照。

## ファイル

| ファイル | 内容 |
| --- | --- |
| `指先3D比較_v01.html` | データを内蔵した3D比較ページ |
| `hand_fingertip_concepts_v01.blend` | 3候補×4姿勢の12シーン。Blenderのシーン一覧で選ぶ |
| `hand_*_2F_fingertips_v01.glb` | 各候補の近接姿勢。工具域は含めない |
| `A_near_v01.png`、`A_open_v01.png`、`B_near_v01.png`、`B_open_v01.png` | 静止画 |
| `hand_fingertip_concepts_v01.json` | 仮設定パラメーター、単位m |
| `hand_fingertip_meshes_v01.json` | 全候補のメッシュと静的姿勢行列 |
| `hand_fingertip_*_observations_v01.json` | 幾何、native読戻し、ブラウザー操作の観測 |
| `scripts/`、`inputs/`、`licenses/` | 再生成コード、必要な既存形状、配布ライセンス |
| `delivery_manifest.json` | 収録ファイルのSHA、元ファイルとの対応 |

工具域はHTMLだけの説明用形状。nativeとGLBには含めない。PNGとモデルに腕の軌道はない。

## 再生成

今回の実行環境はPython 3.12.3（NumPy、SciPy、trimesh、pycolladaを備えた既存の描画環境）、Blender 4.5.13。
新しい依存パッケージは追加していない。元のラインnativeは読み込まない。
生成先は存在しない新しいフォルダーを指定する。

IsaacLabリポジトリ直下から、同梱した入力で形状を再生成する例：

```bash
HAND_REVIEW_DIR=/home/rlrk/Downloads/THREAD_指先3D確認_v01_20260913
TERM=xterm-256color VIRTUAL_ENV=/home/rlrk/src/ur15-line-render/venv \
  ./isaaclab.sh -p "$HAND_REVIEW_DIR/scripts/build_hand_fingertip_concepts_v01.py" \
  --config "$HAND_REVIEW_DIR/hand_fingertip_concepts_v01.json" \
  --asset_root "$HAND_REVIEW_DIR/inputs/robotiq_2f_85_gripper_visualization" \
  --urdf "$HAND_REVIEW_DIR/inputs/ur15-dual-arm-cell.urdf" \
  --output_directory /tmp/hand_fingertip_new_review
```

続けて静的native・PNGを生成する例：

```bash
/home/rlrk/.local/opt/blender-4.5.13-linux-x64/blender \
  --background --python-exit-code 1 \
  --python "$HAND_REVIEW_DIR/scripts/render_hand_fingertip_concepts_v01.py" \
  -- --directory /tmp/hand_fingertip_new_review
```

上記の生成コマンドは形状と観測記録を出す。配布用README、ライセンス、パラメーター表のコピーは別途必要。
URDFには元の双腕全体の記述があるが、この生成器は左ハンドの既存連動機構だけを使用する。
同梱メッシュも使用するハンド部分だけ。URDF全体のロボットを読み込むための資産一式ではない。
