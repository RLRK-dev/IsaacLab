# SES2001・SEV2001のメーカー例示CAD比較 v01

2026-09-18。公開トルク範囲の照合で追加候補になったSES2001の図面とSTEPを取得し、
保存済みSEV2001と同じ縮尺の比較図を作成した。
工具の採用、締結時TCP、ねじ・ビット・取付アダプターの選定は行わない。

## 比較できた寸法

| 項目 | SES2001 | SEV2001 | 根拠・範囲 |
|---|---:|---:|---|
| 締付軸から取付面まで | 約58 mm | 約80 mm | 元CADの座標。差は約22 mm |
| 図面の先端部の径寸法 | φ25 mm | φ33 mm | 各メーカー例示図面1ページ。最大外形ではない |
| 図面の本体長さ（モータを除く） | 648.5 mm | 636 mm | 例示寸法。全長ではない |
| 保存CAD全体の長手範囲 | 1,128.994 mm | 1,116.494 mm | モータ・保存された後部ケーブルを含む |
| モータを除く図面記載質量 | 2.9 kg | 6.3 kg | 指定モータ・実装時の総質量ではない |

SESの軸〜面の元STEP値は57.999999999998546 mm。GLBのfloat32平面座標による
表示用観測値は57.99999833106959 mm。差1.669 nmを丸めの差として別欄に保持した。
SEVは既存観測79.9999999999998 mmを再利用した。

[SES2001図面](https://www.stoeger.com/en/downloads.html?file=files/stoeger/downloads/CAD/SES/automatic_screwdriver_for_screws_SES2001_series.pdf)と
[SEV2001図面](https://www.stoeger.com/de/downloads.html?file=files/stoeger/downloads/CAD/SEV/automatic_screwdriver_for_screws_with_vacuum_unit_SEV2001_series.pdf)を
文字と画像で確認した。SEVのローカル図面は既存SHA
`10a4439f537ec6c1cf2d8bb32ea86d9a7bc4fc871e87a4a3f2f417b2540a1330`を維持した。
図面は寸法が例示であり個別仕様で変わると注記する。
φ25/φ33を、選択するビット径、ねじ保持チューブ径、フィンガ間に入る最大外形へ置き換えない。
SESの元STEPには半径12.5 mmの選択円筒2面が存在するが、SEVのφ33は今回CAD面へ同定していない。

比較図では両工具の全形状を保持し、先端側の拡大と全体を切り替える。
100 mmの尺度は2形式共通。配置用の原点ではなく、各保存CADの長手最小端をそろえた表示。
取付面の線は選択平面に属する面の長手範囲であり、連続した支持面積を意味しない。

## 入力と再利用

取得先は[STÖGERの配布ページ](https://www.stoeger.com/en/downloads.html)。URL、取得時刻、
SHA256、図面1ページの読み取りを`data/hvjb_ses2001_sources_v01.json`に記録した。
取得日は製造仕様日ではない。STEPヘッダーの作成日時は2016-07-28、Autodesk Inventor 2014。
新しい読取りは既存のcascadio 0.1.1、全メッシュ記録、部分BREP読取り、描画処理を再利用する。
既存オーケストレーションはSES1601・SEM2001・SEV2001を固定しているため、別形式の
SES2001用に入口だけを追加した。SEM2001をSES2001として読み替えていない。

最初の変換は完了。743,217三角形、17材質プリミティブを保持し、77の面積ゼロ三角形も
修復・削除していない。元GLBは1ノード・1メッシュで、17は材質別の読取り分割数である。
BREP面の対応が付くのは15,865三角形、付かない727,352三角形も描画用に残っている。
部分BREP記録には長手X方向の工具軸に対応する円筒が含まれなかった。

## 追加読取り前のprior-art確認と差分

実行前の`SES2001 SEV2001 先端寸法`は該当0件。
補足検索`SES2001 STEP axis`は一般語STEP/axisが他課題に一致し、30 blocker、exit 2。
出力全文は`audit/hvjb_ses2001_step_prior_art_v01.txt`に保存した。
追加計測を止めて、次の一致本文を読んだ。

- `docs/SKILL_IMPROVEMENT_PROGRAM_2026-06-13.md:124–128`：機構を増やす前の限定調査、
  接触の存在を保持能力と同一視した失敗。
- `eval_runs/model_strategy_post623_20260611/ground_truth_v2.md:13–14`：単位変更時の依存先、
  評価側とのしきい値不一致。
- `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md:640–678`：
  物理制御とオフライン表示の混同、巻戻し、旧状態の採用。
- 同ディレクトリ`BUILD_PLAN_ENVCORE_COORD_20260706.md:15–21`、
  `BUILD_PLAN_ROUTEEXEC_COORD_20260707.md:110–116`、`B_BC_BUILD_SPEC.md:128–135`：
  行動の累積誤差、把持期間、物理基盤間の成績転用。

今回の具体差分は、新規SES2001の保存STEPの明示座標を読むこと。
訓練、物理ステップ、IK、接触、把持保持、運動の再生や巻戻しは実行しない。
mm→mは明示変換し、元の図面寸法・元STEP座標・GLBのfloat32座標を区別する。
先端の形状や物理成立を推定する代替機構も作らない。
検索語を具体化した`SES2001 CYLINDRICAL_SURFACE TM_brep_faces`は該当0件だが、
これは上記blocker記録の削除・無効化を意味しない。以上の限定差分を根拠に資料読取りを続ける。

不足したBREP対応を埋めるための材質設定変更・再変換は繰り返さない。
元STEPの限定した実体番号とその参照先を読み、内容をそのまま記録する。
STEP Toolsの公開スキーマで
[cylindrical_surface](https://www.steptools.com/docs/stp_aim/html/t_cylindrical_surface.html)の
position/radiusと
[axis2_placement_3d](https://www.steptools.com/docs/stp_aim/html/t_axis2_placement_3d.html)の
location/axis/ref_directionを確認した。汎用STEP形状エンジンは作らない。

正式な物理妥当性判定はVaultProtocol V12の独立経路による。

## 元座標の読取りと表示

`build_hvjb_ses2001_comparison_v01.py`はSHAを固定したSES2001の4実体だけを読み、
その参照先の定義文も保存した。

- 円筒`#63743`、`#63745`：X方向に同軸。X=0との交点はY≈−2.010e−15 m、Z≈−3.552e−16 m。
- 平面`#13153`、`#13169`：Z≈−0.058 m、法線はZ方向。
- 元STEPの長さ単位はmm。座標は0.001倍し、方向ベクトルには長さ変換を適用しない。
  この限定読取りが解釈しない変換・mapped itemがあれば停止する。

GLBでは元平面座標をfloat32へ変換した値と完全一致する三角形を選択した。
選択面は16三角形、X=247.774〜685.774 mm、Y=−13〜13 mm、面積0.006112000532 m²。
しきい値を緩めて面を増やしたのではなく、元STEP値と格納精度を区別した抽出である。
既存の取付ねじ配置・中央溝の用途をここから決定していない。

描画用コピーのみZを57.999998331 mm平行移動して取付面をZ=0とし、既存の`_render`を再利用。
元座標から観測座標、観測座標から表示座標、両者を合成した行列を保存した。
元GLB、原STEP、ネイティブシーンへこの変換を書き戻していない。

## 実行・確認記録

- `audit/hvjb_ses2001_cad_v01.json`と同`_stdout.txt`：新規CAD変換1回、81入力のSHAが前後一致。
- `data/hvjb_ses2001_comparison_v01.json`と`audit/hvjb_ses2001_comparison_v01_stdout.txt`：
  2形式×2範囲の静止画を生成。85入力のSHAが前後一致。
- `audit/hvjb_ses2001_comparison_browser_v01.json`と同`_stdout.txt`：
  736/320 px×明暗×2範囲の8条件。両画像のSHA、縦横比、同一縮尺、軸・平面の投影、
  100 mm表示、選択、はみ出しを確認。JavaScript例外0件。代表3画面を目視確認した。
- `audit/hvjb_ses2001_comparison_v01_readback.json`：保存後の入力・成果物SHA、行列合成、
  S5_AB、20仕事、92対象、14締付軸との対応を記録する。

新スクリプトの初回ruffで122文字の引数行1か所を整形してから実行した。
計測・描画・ブラウザ確認の実行時例外はない。BREP対応の不足は取得結果として残し、
変換設定の試行や計測許容差の緩和をしていない。

工具と保持ハンドの実配置・干渉、ねじとビットの適合、ねじ供給、締結品質は未判定。
H05、T050の40 mm後退・15度、S5_ABの分担、製品p03、v06を変更していない。
新しいロボット動作や動画は生成していない。

## 再現用の入口

既存レンダーvenvを指定した`isaaclab.sh -p`経由で実行。旧出力は上書きしない。

```bash
scripts/prepare_hvjb_ses2001_cad_v01.py \
  --converter_path /tmp/ur15-cad-tools \
  --output_directory previews/hvjb_ses2001_cad_v01 \
  --output_json audit/hvjb_ses2001_cad_v01.json

scripts/build_hvjb_ses2001_comparison_v01.py \
  --output_directory previews/hvjb_ses2001_comparison_v01 \
  --output_json data/hvjb_ses2001_comparison_v01.json \
  --output_html /home/rlrk/IsaacLab/work/hvjb-ses2001-comparison-20260918/ses2001-sev2001.html
```

図のプレビュー作成後、`check_hvjb_ses2001_comparison_v01.mjs`へプレビュー、観測JSON、
新しいブラウザ確認出力ディレクトリの順に渡す。再実行はprior-artと具体差分を先に確認する。
