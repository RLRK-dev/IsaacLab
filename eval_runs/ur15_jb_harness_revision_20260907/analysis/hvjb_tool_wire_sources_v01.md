# 電線被覆と締付工具の公開寸法確認

2026-09-17。メーカー公開資料、保存PDF、図面の画像読取りに基づく記録。
対象は前後パッド付きPGE手先を実物寸法へ対応させるための入力調査。

TEヘッダーの接点候補について、対応する**電線本来の被覆径**を確認した。
一方、丸端子側の**黒い追加被覆の仕上がり径**と、締付工具一式の寸法付き外形は
今回確認した公開資料からは確定していない。把持する実物の径、パッド溝、工具の採用は未設定。

## 電線本来の被覆径

[TE 408-32095 Rev B][te-header] p.1 Figure 1は、HVA280の筐体側ヘッダーに使う
MCP 2.8接点として次の2品番を列挙している。MQS接点は別に記載されている。
今回の数値をMQS/HVIL線や主回路の全電線へ適用しない。

個別図面2141598 Rev A2は、最新情報を製品群図面2355029で参照するよう案内していた。
その案内先の[2355029 Rev A][te-group] p.1の表と公式製品ページを照合した。

| MCP接点候補 | 導体断面積の対応範囲 | 電線本来の被覆外径 | 製品群図面のDesign欄 |
|---|---:|---:|---:|
| [2-2141598-2][te-1598] | 1.0〜2.5 mm² | 2.4〜3.7 mm | 2 |
| [2-2141600-2][te-1600] | 2.5〜4.0 mm² | 2.7〜3.7 mm | 1 |

これは接点候補の対応範囲であり、Ampereが実際に採用した接点・電線の特定ではない。
個別の映像上の線、2022年写真の部品ID、最終のボルト位置との対応も増やしていない。

[圧着仕様114-18051-1 Rev G][te-application] p.9 Table 1には、別途、具体的な
線種・断面積の組合せが載っている。2141598の行はFLKの1.5/2.5 mm²、被覆径2.4〜3.7 mm。
2141600の行はFLRの4.0 mm²、被覆径3.4〜3.7 mm。
製品群図面の範囲とこの圧着表を混ぜ、任意の電線や圧着条件を選定する扱いにはしていない。

## 黒い追加被覆と参考端子

前側パッドの対象は、ユーザー指定の**丸端子に近い黒い被覆部**。
上表の電線被覆径だけでは、圧着後の端子、追加被覆の厚さ・重なり・収縮後形状を決められない。
実物の仕上がり外径、把持できる長さ、端子側への抜け方は引き続き未確定。

[Ampereの公開記事][ampere]とHVJB-5-400 V1.1の全4ページを確認した範囲では、
内部の個別電線の採用品番、丸端子の圧着後寸法、黒い追加被覆の仕上がり寸法を得られなかった。
公開回路やコネクタのピン表を、その寸法の代用にはしていない。

既存の参考CADである[Klauke 6R6][klauke]は50 mm²導体・M6用で、
表中の14 mmは**金属管の外径**。電線の被覆径ではなく、Ampereの採用品番とも確認されていない。
比較用電線14 mm・黒被覆15.2 mmと、p03の表示用黒被覆5.6 mmは従来の参照値として残す。
どちらも今回のTE範囲に置き換えて実物の把持適合を示す処理はしていない。

## 締付工具の公開寸法

既存候補DEPRAG E-SFMについて、[公式カタログD0062E 09.2026][deprag-pdf]の
全8ページを確認した。p.6の仕様表から得られた値は次のとおり。

| 項目 | カタログ記載値 |
|---|---|
| Size 16のトルク範囲 | 0.01〜2 N·m |
| Size 25 High Performanceのトルク範囲 | 2〜18 N·m |
| ノーズ長 | 40 / 80 mm |
| 真空仕様の自由ストローク | 50 / 100 mm |
| リニア軸ストローク | 100 / 150 / 200 / 250 mm |
| 最大ねじ頭径 | 14 mm |
| モーター取付方向 | 軸方向 / 左 / 右 |

14 mmはねじ頭の許容径であり、ノーズや工具本体の外径ではない。
この8ページには、取付部・供給ホース・ノーズ開閉状態まで含めた寸法付き全体外形はない。
構成図の画像を縮尺合わせして、工具CADを作ることもしていない。
[公式製品ページ][deprag-web]のG1/G2表記と、この版のSize 16/25表記は自動で対応させない。

この工具調査は選定前の入力整理。TEヘッダー取付けのM4・2.0〜2.5 N·mという別の
仕様を内部丸端子の締結へ流用せず、対象ねじ・積層・トルク・工具一式を接続別に確認する。
前回測った工具中心線までの22.646854 mmから、許容工具半径や必要すきまを決めていない。

## 続きに必要な形状入力と保持した作業範囲

| 形状へ反映する箇所 | 必要な入力 |
|---|---|
| 後側パッド | 対象線の個別対応、採用電線の被覆径 |
| 前側パッド | 丸端子の型式、圧着後・黒被覆後の径、有効接触長さ |
| 工具との位置関係 | 対象ねじ・締結積層、実際の工具一式、開閉ノーズ・ホース・取付部の基準座標 |

採用済みS5_AB、20枚の作業カード、D60の剛体導体保持・被覆部保持・必要な自由端案内を
維持した。ロボットの型式・台数の追加選定や、上押さえの追加はない。
既存の比較指、H04の初期値、p03、v06、T050を変更せず、アーム動作・動画も生成していない。
本記録は入力資料の確認であり、保持力、締結品質、実機成立についての判定ではない。

## 記録と検証

- `data/hvjb_tool_wire_sources_v01.json`：確認値、出典URL、保存PDFのSHA-256とページ、未確定欄。
- `audit/hvjb_tool_wire_sources_v01.txt`：JSON読戻し、6資料・9既存入力のハッシュ照合、20カードの照合。
- 新規PDFのローカル保存先：`references/hvjb_tool_wire_sources_20260917/`。
  PDF本体はローカル参照資料として保持し、出典URL・ハッシュをGitへ記録する。

事前検索は `scripts/check_thread_vault_prior_art.sh --fail-on-blocker Ampere 被覆径 工具外形`。
終了コード0、findings=0 / blockers=0 / lessons=0。指定語に対する検索結果であり、
既知の寸法未確定事項が解消したことを意味しない。
今回の変更は新しい資料記録だけで、既存の測定スクリプトの再実行や形状の昇格はしていない。

[te-header]: https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=408-32095&DocType=Specification+Or+Standard&PartCntxt=2103340-1
[te-group]: https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=2355029&DocType=Customer+Drawing&PartCntxt=2-2141598-2
[te-1598]: https://www.te.com/en/product-2-2141598-2.html
[te-1600]: https://www.te.com/en/product-2-2141600-2.html
[te-application]: https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=114-18051-1&DocType=Specification+Or+Standard&PartCntxt=2-2141598-2
[klauke]: https://www.klauke.com/nl/de/rohrkabelschuhe-cu-normalausfuhrung-4957
[ampere]: https://help.ampereev.com/hc/en-us/articles/31292470232087-High-Voltage-Junction-Box-HVJB-5-400
[deprag-pdf]: https://www.deprag.com/fileadmin/bilder_content/emedia/broschueren_pics/emedia_Automation/D0062/D0062en.pdf
[deprag-web]: https://www.deprag.com/en/automation/screwdriving-units/e-sfm.html
