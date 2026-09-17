# HVJB 締結点と公開工具条件の対応 v01

2026-09-18。前段の工具取付面の観測を引き継ぎ、工具配置に必要な締結条件を整理した。
今回の追加は出典付きの条件表である。製品モデルの実部品、工具、締結姿勢の採用を意味しない。

## 確認できた条件

| 締結箇所 | 公開条件 | モデルとの対応・適用範囲 |
|---|---|---|
| 筐体側ヘッダーのフランジ | M4、頭径最大8.7 mm、2.0–2.5 N·m。3口8本、2口6本 | 対応表のP16＝TE 2103340-1、P17＝2103346-2。外部プラグの嵌合とは別作業 |
| GX14系の主電流端子 | ステンレスM10×1.5ボルトとフランジナット、14–20 N·m | **候補資料に限定**。P02のGIGAVAC表示は確認されているが、Ampere実物をGX14とは同定していない |
| GX14系の本体固定 | M5ボルト | 同じ候補資料の別締結箇所。本体固定トルクは今回の記録では未確定 |
| 内部の丸端子・板状導体 | 実ねじ、積層、トルクは未確定 | 写真P13/J09–J13と動画J1/J2/J3の観察を継承。両年代の個別接合点の同一性は未確認 |

ヘッダー条件は[TE 408-32095 Rev B §3.2.A.2](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=408-32095&DocType=Specification+Or+Standard&PartCntxt=2103340-1)の2頁を本文・画像で確認した。
本数は既存の確認済み[2103340図面](https://www.te.com/en/product-2103340-1.html)と
[2103346図面](https://www.te.com/en/product-2103346-2.html)、`data/hvjb_header_interface_inputs_v01.json`を継承した。
頭径上限から実ねじの頭形状、ビット種、ねじ長さは決めていない。

GX14条件は[公式データシート](https://www.sensata.com/sites/default/files/a/sensata-gigavac-gx14-series-open-contactors-datasheet.pdf?cb=14043931)の3頁にある本文から記録した。
表紙の表記は「Rev A 7/2/18」。取得日を資料の改訂日として扱わない。
発見元の商品ページはGX14BDだが、その末尾仕様をAmpereへ割り当てていない。
主端子と本体固定を分け、主端子のトルクをM5固定へ流用しない。

内部接合の観察元は[既存記録](hvjb_final_connection_v01.md)と
[Ampere公式組立映像](https://www.youtube.com/watch?v=Sm_D-vmNYqc)。
J1/J2/J3は画像中の位置ラベルで、部品番号や完全な接合点リストではない。
[Ampere製品説明](https://help.ampereev.com/hc/en-us/articles/31292470232087-High-Voltage-Junction-Box-HVJB-5-400)からも、今回必要な実接触器の型式と積層寸法は得られていない。

## 工具比較へ渡せること

ヘッダー固定、接触器本体固定、主電流端子、内部丸端子は、別の締結条件として照合する。
既存の`data/hand_fastening_reference_v01.json`にある
[DFM D3837](https://www.deprag.com/fileadmin/bilder_content/emedia/broschueren_pics/emedia_Automation/D3837/D3837en.pdf)の参照範囲は、ねじM8まで・ナットM6まで。
従って、その記載範囲には候補GX14のM10ナットは含まれない。
これは資料の範囲を比較した結果であり、E-SFM、STÖGER SEM、別構成へ一般化しない。

工具の配置には、対象ごとの実締結部材、積層厚さ、ねじ掛かり、突出量、工具の係合深さが残る。
これらが未確定のまま、保存CADの先端を実際の締結TCPに置き換えたり、ビット行程を決めたりはしていない。
前段の取付面の観測は[取付面記録](hvjb_fastening_mount_faces_v01.md)に保持する。

## 出典の取得状態と保存確認

- GX14の公式PDFはWeb抽出本文を読めた。ローカル取得はHTTP 403でPDF保存なし、図面画像の視認も未実施。ローカルSHAは`null`とし、本文以外の図面寸法は採用していない。
- 旧Ampere Wiring Guide V1.3の公式URLはWeb取得時に404。締結条件の根拠には使用していない。
- TEのPDF3件、既存対応表と役割表、元CAD等のSHAを照合し、出典レコードの保存読戻しを記録した。
- 製品p03、手先40 mm後退・15度の初期値、S5_ABと20仕事は維持。D60の剛体導体保持、被覆保持、条件付き残余案内の分担を変更していない。

データは`data/hvjb_fastener_interface_sources_v01.json`、
保全と読戻しの結果は`audit/hvjb_fastener_interface_sources_v01.json`。
新たな動作や動画はこの資料整理の対象に含めていない。正式な物理成立の判定は行っていない。
