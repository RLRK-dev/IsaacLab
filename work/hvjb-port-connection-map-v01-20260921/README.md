# HVJB：5口の用途・極性と未追跡配線

2026-09-21。前回 `cf523a48df` の出口比較に続く、公開資料と保存モデルの対応。
公開外観に用途表示を見つけたため、5口の位置・用途・回路上の極性を新しい台帳へ対応した。
既存の写真台帳・CAD・ハンド・軌道・nativeは変更していない。

## 今回追加した対応

[Ampere公式記事][article]の最初の製品画像は、従来の内部写真とは別の
[蓋付き正面写真 DSC02840][closed]。5つの口の上に用途が印字されている。
原画像1024×683画素を保存し、文字・部品・線の画素は変更しなかった。
既存P16の3口＋P17の2口と、保存台帳の左からの並びへ照合する。

| 既存ID | Key | 外観の用途表示 | V1.1回路のヒューズ | 既存の回路群ID |
| --- | --- | --- | ---: | --- |
| I01 | A | HEATER 1 | 20 A | EC04 |
| I02 | D | AC | 30 A | EC05 |
| I03 | E | HEATER 2 | 20 A | EC06 |
| I04 | D | CHARGER | 30 A | EC07 |
| I05 | F | DC/DC | 10 A | EC08 |

モデルIDへの対応は、公式写真の用途表示と既存の3＋2口配置を組み合わせた推論。
実物の同一個体・同一製造版・内部配線を連続追跡した意味ではない。
電流値は[HVJB-5-400 V1.1][datasheet] p.2の回路から対応した。
写真のヒューズ実体 P05 / P06 / P19 / P20 / P21のどれかに割り当ててはいない。

V1.1 p.3は、全5口の1番をHV+、2番をHV-と示している。
嵌合側の表示は左1・右2。既存の[TE内側ハウジング図面][te-drawing]と
[組立説明書][te-instruction]の電線側表示は左2・右1であり、左右をそのまま転用しない。
番号と役割の模式図を作った。図の穴形状や間隔は製作寸法ではない。

## まだ結線として埋めないもの

- 各口とヒューズ実体・丸端子・ボルト・共締め積層の対応。
- 写真のWI短区間と、内側ハウジングの個別穴番号の対応。
- HVILの3/4番のIn/Out割当、内部ループの順番と線形状。
- 採用接点、電線径、被覆、曲がり、長さ、束ね方、支持と保持。

20接点の必要欄を保持し、電力10接点の公開極性だけを新しい項目へ追加した。
`electrical_node`、`photo_wire_id`などの実配線欄はnullを維持する。
HVILのLV側5番In／11番OutはV1.1 p.4の既存値。これを各補機口の3/4番へ流用しない。
I03のWI31/WI32は退役したまま。8件の可視入口区間は8本の完全な線を意味しない。
W04→WI52、W05→WI42という既存候補も、新しく確定していない。

前回の各4 mm開放→上方50 mm退避は補助的な幾何比較。
今回の電気的役割を入れても、曲がった実電線との非干渉・把持成立・荷重は未確認。
5腕・20仕事、OP010 XYZと20枠共用、1段往復パレットを変更しない。
H04/T050の40 mm後退・15度と、今回の内側ハウジング指は別の対象として維持する。

## 調査と出典の同一性

- 現行ヘルプ添付V1.1を取得し、旧保存PDFとSHA256が同一であることを確認した。
  `643648bcea77b4d7c37c65d073664f746f68689952da2d5ce932e3d10bd5a9e1`。
  p.2〜4をPopplerで描画して確認した。
- 2024年の公式解説映像の自動字幕を探索に用い、135秒の無加工フレームを既存ffmpeg方式で1枚抽出。
  蓋の用途表示を画像として観察した。続いて公式記事の元の蓋付き写真を取得し、それを図の直接根拠とした。
  自動字幕の言葉を未検証のまま部品・結線の根拠にはしていない。
- 抽出元映像のSHAは抽出前後で同一。原フレームの記録は`output/explanation_frame_provenance.json`。
  2025年の組立映像の個別配線へ対応を移していない。
- prior-artは`HVJB HVIL 配線対応 接続図`、6件・blocker 0。該当2文書と既存のwire-origin、
  final-connection、tool-wire-sources、写真v03・配線生成の訂正を読んだ。

## 成果物・再現

- `output/pdf/`：2ページの図解。
- `output/port_connection_map.json`：前回20接点表＋公開用途・極性・必要出典・未確定欄。
- `output/document_audit.json`：入力照合、描画コード・PDF・台帳のSHA。
- `output/pages/`、`output/qa_receipt.json`：最終PDFの表示確認。
- `references/`：無加工の公式蓋写真と既存の指定内部写真。図中のI番号は別レイヤー。

既存資料の92写真特徴、17必須機能、13回路群、LV12極を照合・保持した。
元の実線割当がnullであること、20接点・8入口区間、I03入口未確認を生成時に照合する。
古い台帳を上書きせず、今回の`port_connection_map.json`を差分の参照先とする。
新しい物理シミュレーション、IK、工程動画、受入基準は作っていない。

```bash
PYTHONPATH=/tmp/hvjb_pdf_runtime_20260921 ./isaaclab.sh -p work/hvjb-port-connection-map-v01-20260921/build_review.py
pdftoppm -scale-to 1654 -png work/hvjb-port-connection-map-v01-20260921/output/pdf/HVJB_5口の用途・極性と未追跡配線_v01_20260921.pdf work/hvjb-port-connection-map-v01-20260921/output/pages/page
```

ReportLab 4.4.3は前回用意した一時ディレクトリを再利用する。IsaacLabの依存設定変更なし。
入力PDFのローカル参照は旧op040 worktree。ハッシュ一致が必須で、欠損時に別版へ自動置換しない。
標準出力の`PORT_CONNECTION_MAP_COMPLETE`とPDF監査JSONを確認する。
初回描画はフッターの下余白チェックで停止した。フッターを3 pt上へ移して再描画し、
初回ログも保存する。資料の読み取り値・端子対応・ハンド形状への影響はない。

[article]: https://help.ampereev.com/hc/en-us/articles/31292470232087-High-Voltage-Junction-Box-HVJB-5-400
[closed]: https://ampereev.com/wp-content/uploads/2022/05/DSC02840-1024x683.jpg
[datasheet]: https://help.ampereev.com/hc/en-us/article_attachments/31292430639639
[te-drawing]: https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=2103245&DocType=Customer+Drawing&PartCntxt=2103245-1
[te-instruction]: https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=408-32095&DocType=Specification+Or+Standard&PartCntxt=2103245-1
