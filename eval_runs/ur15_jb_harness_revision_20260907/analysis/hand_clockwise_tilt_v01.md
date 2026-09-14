# フィンガ15度傾斜 — 把持点を維持した比較 v01

2026-09-14。ユーザー画像 `Screenshot from 2026-09-14 13-06-56.png` と、
「黒色部分を時計回りに15度程度回転」の指示を反映した静的モデル。

## 変更

- 側面の画面右をケーブル側（world +Y）、上を+Zとして、黒い本体・連動リンク10個を
  時計回り15度回転。world +X軸まわりの符号付き角度は−15度。
- 回転中心は左右取付面の原点の平均、world約 `(0, 0.066, 0.003)` m。
  黒い機構の頂点・面・色と内部の保存開閉状態は維持し、配置を剛体回転した。
- 近接姿勢の前側黒被覆パッド（Y22–30 mm）と根元ケーブルパッド（Y61–71 mm）は
  元のworld位置・形状を維持。金属端子を挟む方式に戻していない。
- 青い取付板と3穴は黒い指に追従して傾け、横桟・前側支持・根元支持は元の近接world位置へ
  接続する。旧一体メッシュを再Booleanせず、4個の単純な原形を統合してから穴を一度あけた。
- T025/T050はH025/H050を入力にした15度版。逃げ0.25/0.5 mmは比較のままで、
  0.5 mmの初期表示は製作値の採用ではない。40 mm後退後の取付位置を回転基準にしている。

near/early/openは機構全体の剛体回転を適用。clearは回転後のopenからworld +Zへ25 mmの
参考離隔を保った。開放時のworld位置は旧版と異なる。4状態は静的比較で、連続軌道ではない。

## 観測

実行結果 `hand_clockwise_tilt_observations_v01.json` と、Blender保存読戻し結果
`hand_clockwise_tilt_native_v01.json` に基づく。

| 項目 | 記録 |
|---|---|
| 黒い機構の回転角 | −14.999999999999998度（world X） |
| 近接パッド全頂点のworld変化 | 最大1.994e−17 m未満（計算丸め） |
| 黒い10メッシュ | 頂点・面・色が入力と一致 |
| 青い支持体4個 | 各1連結成分、閉じた辺構造、厳密な面積ゼロの面0個 |
| パッド支持面サンプル | 各支持面9点、旧面との最大距離1.004e−9 m未満 |
| 穴の参照円周サンプル | 各穴192点、最大距離5.646e−10 m未満 |
| Blender保存読戻し | 16シーン×20メッシュ。world行列・頂点/面SHA・個数・表示属性が一致 |
| GLB読戻し | 2候補とも20メッシュ。境界最大差1.196e−9 m未満 |

各15度候補の4姿勢で、手先対参照部品64組、キャリア対機構20組、左右追加指先9組を
既存のBVHTree（epsilon=0）で記録。0度版と比較して追加されたオブジェクトの表面交差組は0。
取付面など旧版に存在する組は記録に残る。接触、包含、貫通深さ、連続動作を判定するものではない。
保存後の観測はscene行列へ再代入せず、読取による変更がないことも比較した。

確認ページはPC幅と携帯幅それぞれ56操作を実行し、角度・姿勢・部材・高さ・表示切替を確認。
描画データの有限性、WebGLエラー、数値とJSONの一致、参照リンクと横幅を記録した。
同梱コードから別の出力先へ再生成し、メッシュJSON・Boolean入力/出力・両GLBはバイト一致。
全観測とページも生成日時以外が一致した。これらは表示と再現性の確認である。

## 工具側の個別参照部材

既存の公開寸法・7種類の比較下端高さ・4保存姿勢を再利用。主軸とソケットは個別の円筒であり、
差込み量や組合せ長を発明して一体工具にしていない。448配置の観測を保存した。

H050/T050の近接姿勢。下表は指定高さ帯の手先表面までの最小XY半径から部材半径を引いた値。

| 参照部材 | 下端の比較高さ（接続面基準） | 0度 | 15度 |
|---|---:|---:|---:|
| MINIMAT-ED、φ36×314 mm | 53.8 mm | +10.500 mm | +40.015 mm |
| 同じ主軸を低く置いた比較 | 3.8 mm | +4.647 mm | +4.647 mm |
| 804133、φ16×50 mm | 3.8 mm | +14.647 mm | +14.647 mm |
| 804134、φ19×50 mm | 3.8 mm | +13.147 mm | +13.147 mm |

上部には差が出るが、把持点を保った先端域の値は変わらない。実工具一式の最短隙間ではない。
供給ノーズの開閉外形・取付部・ホース、他の工具・腕はこの観測に含まれない。

公開寸法は[DEPRAG D3195 p.4](https://www.deprag.com/fileadmin/bilder_content/emedia/broschueren_pics/emedia_schraubtechnik/D3195/D3195en.pdf#page=4)と
[D3320 p.16](https://www.deprag.com/fileadmin/bilder_content/emedia/broschueren_pics/emedia_Automation/D3320/D3320en.pdf#page=16)。
詳細は同梱 `data/hand_fastening_reference_v01.json` の資料SHA・ページ・適用範囲を参照。
参照の黒い機構は2016年モデルで、既存調査の2018年Robotiq取付図との対応を維持した。
公式寸法との新たな対応付け、材料や製造公差の採用はしていない。

## 入力の保存と再生成

入力は `THREAD_黒被覆側クランプ_v01_20260914`。別フォルダーへ新規作成し、元版とv06を上書きしない。

- `hand_sleeve_clamp_meshes_v01.json`: `f9b3c097ea93cb7bf8ea08b17474ec293f8cd2204b6eae20362fcdcc2809c732`
- `support_boolean_inputs_v01.json`: `32bcd7a60a70778195bd0dac799e872ae5c2e4965fca182a9c82feb048ad4c62`

NumPy・SciPy・trimeshがある既存Python環境で、同梱フォルダーを作業ディレクトリとして実行する。
リポジトリ内では `./isaaclab.sh -p` のラッパーを用いる。

```bash
python scripts/build_hand_clockwise_tilt_v01.py \
  --source inputs/hand_sleeve_clamp_meshes_v01.json \
  --recipe inputs/support_boolean_inputs_v01.json \
  --config data/hand_clockwise_tilt_v01.json \
  --reference_config data/hand_fastening_reference_v01.json \
  --blender /home/rlrk/.local/opt/blender-4.5.13-linux-x64/blender \
  --directory /tmp/hand_clockwise_tilt_rebuild
blender --background --python-exit-code 1 \
  --python scripts/save_hand_clockwise_tilt_v01.py -- \
  --directory /tmp/hand_clockwise_tilt_rebuild
```

出力先が存在したら停止する。閾値は以前の数値比較用1e−7 mなどを引き継いでおり、
締付品質や物理的な合否の受入基準として使わない。

## prior-artと継続範囲

事前guardは7件、うち停止文脈3件は
`T-ROOT-optE-route-dapg-C1C2-P2-routeexec/state.md:50–52` の2026-07-11接触実験。
そのslot不足という撤回済み解釈・停止された再走は復活させない。
今回の具体的デルタはユーザー指定の静的15度取付姿勢と、別入力H025/H050の青い接続形状。
同じ接触物理実験を繰り返すものではない。実行前にmain Vault log.mdへ指示と区別を記録した。

同梱コードの確認前に「同梱」を加えたguardでは11件/停止文脈9件。
追加の2個の過去handoffコピーとledger:67–68は、BC/RL action・CP-C・同じ7月slot試験の文脈。
それらの停止・レビュー条件は維持する。別入力による本件静的モデルの再現性確認だけを行い、
学習・報酬・共有ツリーのsourceを昇格しない旨を事前にlogへ記録した。

黒被覆は参照形状で、採用済み実部品の熱収縮材・圧着形状ではない。保持力、被覆の滑りと回転、
締付反力、取付剛性・ねじのかかり長さ、パッド材と固定法は未確定。
幾何観測を正式な物理判定にしない。独立レビュー経路はVaultProtocol V12に従う。
指先構成を先に詰める方針を守り、アーム軌道・動画は本比較では生成しない。
