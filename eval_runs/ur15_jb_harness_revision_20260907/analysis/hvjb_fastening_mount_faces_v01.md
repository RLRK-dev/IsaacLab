# 締付工具の取付面・行程の確認 v01

2026-09-17。前回の工具軸・取付側平面の記録に続き、同じメーカー例示CADから
平面の三角形と境界線を保存した。取付ねじ・アダプターの設計や工具採用の決定ではない。
観測の全文は`data/hvjb_fastening_mount_faces_v01.json`。

## 取付側の面で観測した形状

座標は元CADのSI座標系。表は表示用にmmへ換算・丸めた値であり、加工指示寸法ではない。

| 例示形式 | 選択平面 | 長手方向の範囲 [mm] | 横方向の範囲 [mm] | 中央の間隔 [mm] | 閉じた境界線 |
|---|---|---|---|---:|---:|
| SES1601 | Z=0 | Y=24〜300 | X=−10.5〜10.5 | 8 | 2 |
| SEM2001 | Z=0 | X=−186.5〜186.5 | Y=−13〜13 | 12 | 2 |
| SEV2001 | Y=0 | Z=0〜487 | X=−28〜28 | 12 | 10 |

SESとSEMの選択面は中央を挟む2本の帯状の面。SESの境界には部分的な切欠きがある。
SEVでは長手方向Z=0〜108 mmと273.5〜487 mmに面が分かれ、面の内部にも境界線がある。
表の境界線数は外周を含む数であり、取付穴数ではない。閉じた輪郭だけから、その用途、
ねじ径、ねじピッチ、貫通・止まり穴の別を確定していない。

中央の間隔の保存値はSES 8.00000037997961 mm、SEM/SEV 12.000000104308128 mm。
選択した全三角形が横方向ゼロをまたがないことを確認し、左右の三角形の最寄り端から
算出した。頂点だけを調べて、間を横切る面を見落とす方法は使っていない。
この値が示すのは選択平面内の空きであり、溝の全断面、工具すきまや必要離隔ではない。

## メーカー資料で確認できる固定条件

SESのSTEP配布ZIPに含まれる`additional_info_SES.pdf`の2ページを読み、英語ページを
画像でも確認した。SHA256は
`0b529f27167cb96896ddf99210c76a0b75dcb26a102301876681755305214466`。
入手元は[メーカーのCAD配布ページ](https://www.stoeger.com/de/downloads.html)。

- SESの説明は取付面全体による支持、少なくとも3本のねじとキープレートを指定する。
- Y断面にはキー溝の公差記号F8と、下側+0.013 / 上側+0.035 mmの偏差が記されている。
  **F8は公差の記号であり、公称8 mmの意味ではない。** 上表の8 mmは別に行ったCAD観測。
- この補足紙だけでは、採用する固定ねじの規格と穴配置は決まらない。
  SESの説明をSEM/SEVへ一律に適用しない。

CADは前回記録した2016年作成の例示形状。取得日を現行の製造仕様日として扱わない。

## ヘッド送りとビットの行程

2026-09-17にメーカーの[head stroke](https://www.stoeger.com/en/headstroke.html)、
[feed stroke](https://www.stoeger.com/en/feed-stroke.html)、
[automatic bit stroke](https://www.stoeger.com/en/automatic-bit-stroke.html)の説明を読んだ。
head strokeとfeed strokeは同じ送りを指す。給材ヘッドの送りと、ビットがねじへ
進んで締め付ける動きは別の動きである。

前回読んだ[10/2017の冊子](https://www.stoeger.com/files/stoeger/downloads/Broschueren/SES_1017_END_ENG_web.pdf)
のSES送り15/30 mm、SEV約80 mmをビット行程へ転記しない。今回も数値のビット行程、
締結時TCP、採用する工具構成は未確定としてJSONに残した。SEM-V2001の表をSEM2001の
採用仕様へ自動的に対応させない。

資料検索中、Web閲覧側の相対URL解釈により`/en/en/`の404が生じた。
ページの`base`要素と実際のリンクを読み、上記3説明を正しく解決したURLで確認した。
別に見つかったSEMの581280.pdfは閲覧ツールで開けず、内容を確認していない。
前回確認したSEM資料をその未確認図面で差し替えていない。

## 処理と保存の確認

`probe_hvjb_fastening_mount_faces_v01.py`は既存の`_tool_parts`と
`Trimesh.outline(face_ids=..., process=False)`を再利用する。前回と同じ1e−9 mの座標照合で
SES 128 / SEM 16 / SEV 482三角形を抽出し、元座標・面番号・境界の全頂点を保存した。
この許容差はCAD座標の一致を調べるためのもので、接触・加工・受入条件ではない。

独自の円近似、形状修復、再メッシュ、間引きはしない。読取りノードの番号はこのロード内
の番号であり、実物の部品番号ではない。元GLBのSHAと保存座標で対象を特定する。
事前調査で`shapely`が未導入と分かったが、依存は追加せず、既存の境界抽出だけを使用した。
実行前のruffで文字列1行の長さ超過を修正した。測定スクリプト本実行の例外はない。

既存9入力に、前回2記録・補足PDF・3GLBを加えた15ファイルのSHAが前後で一致した。
JSON読戻しでも現在のSHA、前回と同じ選択面積、閉じた全境界、保存3D頂点から表示2D座標
への対応を照合した。記録は`audit/hvjb_fastening_mount_faces_v01_readback.json`。

図は全体と局部をそれぞれ縦横同じ縮尺で表示し、拡大窓の長手座標を明記する。
SES/SEMは長手範囲の中央、SEVは面が存在するZ=37〜107 mmを拡大する。
全三角形と境界を保持し、拡大表示のみ切り取る。新しい取付形状は追加していない。

`check_hvjb_fastening_mount_faces_v01.mjs`は既存の専用Chrome/CDP確認処理を再利用した。
736/320 px・明暗・3形式の12条件で、選択、座標投影、全頂点の表示対応、文字サイズ、
文字の重なり・はみ出しを確認し、JavaScript例外は0件。3形式の代表画面も目視確認した。
記録は`audit/hvjb_fastening_mount_faces_browser_v01.json`。

S5_AB、20仕事、D60の保持分担、40 mm後退・15度の初期値、製品p03を変更していない。
動画・ロボット動作・上押さえは追加していない。把持力・締結品質・実機成立の正式な
判定はVaultProtocol V12の独立経路による。本記録は補助的な幾何観測と資料確認である。

## 再現用コマンド

既存レンダーvenvを指定して`isaaclab.sh -p`経由で実行する。
出力があれば停止するため、再実行時はprior-artと具体差分を確認し、新規出力を指定する。

```bash
scripts/probe_hvjb_fastening_mount_faces_v01.py \
  --output_json data/hvjb_fastening_mount_faces_v01.json \
  --output_html /home/rlrk/IsaacLab/work/hvjb-fastening-mount-faces-20260917/mounting-face-detail.html
```

図のプレビューを作成後、ブラウザ確認スクリプトへプレビュー、観測JSON、新しい確認出力
ディレクトリの順に渡す。実行ログは`audit/hvjb_fastening_mount_faces_v01_stdout.txt`と
`audit/hvjb_fastening_mount_faces_browser_v01_stdout.txt`に保存している。
