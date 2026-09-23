# 主電力・低圧の相手側部品：公開取扱資料の追加確認

2026-09-23 13:42 JST時点。午前の製品ページ・V1.1確認に対し、今回は公式ユーザーガイドと
サポートの取付資料一覧まで確認範囲を広げた。採用品番や新しい工程を決める変更ではない。

## 今回読めた範囲

- [公式ユーザーガイド紹介ページ][guide-page]は2025-04-09更新で、Version 1.0を添付している。
  添付PDFは13ページ。運転、充電、画面操作、クルーズコントロール、空調が中心で、
  HVJB主電力・低圧コネクタの注文品番表は今回の確認範囲で見つからなかった。
- PDFの改訂表はVersion 1.0、10/2/2023。2025年の紹介ページ更新日をPDF改訂日としない。
- [取付資料一覧][install]は、全文アクセスにパートナーのサインインが必要と案内する。
  今回表示された公開一覧は診断と技術サービス通報。非公開資料の内容は取得・推測していない。
- [公開部品仕様一覧][components]からHVJB記事を再確認。リンクはV1.1のままで、
  主電力2口・LV12極の相手側品番を新しく特定できる情報は今回読んだページでは見つからなかった。

## 取得結果と限界

サポートの[公開添付PDF][guide-pdf]を取得した。1,045,463 bytes、SHA256：
`4eeec2fa6a32e0c40549c8ff73a13e95979e9a8f7ca5527af786eb721a6c1178`。
取得URL、日時、ファイル名は`manual_source_identity.json`に記録。

旧Webサイトの公開PDFリンクはWeb検索キャッシュから本文を読めたが、ローカルへの取得は
HTTP 404だった。旧Webサイト版とサポート添付版のバイト一致は確認できていない。
最初の取得スクリプトはそこで停止。URLごとのHTTPエラーを記録して他の公開リンクの取得を続けるように
直した。本文・測定値・採用品番への変更ではない。保存済みPDFは上書きしない。

`HVJB / Amphenol / Molex`のPDFテキスト検索は該当なし。`connector`の一致は車両の充電説明であり、
HVJBの組立手順へ流用しない。公式資料に存在しないことの一般的な証明ではなく、上記公開範囲の記録。
他社や他車両の似た部品を採用品番として埋めない。

## 工程資料への扱い

- 主電力2口とLV12極の相手側品番、専用着脱治具は未確定のまま。
- D71の検査接続集合・条件・順序・時間も未確定のまま。
- 補機5口のTE候補とCPAの一般操作は、前の`connector_followup.md`を維持する。
- 3ST、5腕の役割、20仕事、1段往復、20枠の共有、既存モデル・動作を変更しない。

prior-art：`HVJB 主電力 コネクタ 取扱資料`、exit 0、INFO 4、blocker 0。
該当UR15調査の公開資料・外形とコネクタ突出・機種と手先空間・実物対応の注意を読んだ。

[guide-page]: https://help.ampereev.com/hc/en-us/articles/31296865713559-Atom-Drive-System-User-Guide
[guide-pdf]: https://help.ampereev.com/hc/en-us/article_attachments/31296839281047
[install]: https://help.ampereev.com/hc/en-us/categories/29996463410199-Atom-Drive-System-Documentation
[components]: https://help.ampereev.com/hc/en-us/categories/31291641631639-Component-Specifications
