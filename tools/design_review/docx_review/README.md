# docx 版間レビュー支援ツール

設計書などの Word 文書（.docx）を版ごとにレビューするための、Python 標準ライブラリだけで動く小さなツール群です。
「前版と何が変わったか」を機械的に取り出し、レビューを本文の判断に集中させることが目的です。

| ファイル | 内容 |
|---|---|
| `docx_extract.py` | .docx の本文を 1 要素 1 行のテキストにする。見出し（`H1`〜）、段落（`P[スタイル名]`）、表の行（`T[表番号.行番号]`）、脚注、ヘッダ／フッタ、Word コメント（`CM[…]`）。Word 数式（OMML）は `x_{t}` のような線形表記、画像は `[image: media/imageN.png]` として残す |
| `docx_compare.py` | 前版と今版を比較して Markdown レポートを出す。SHA-256（同一ファイルの検出）、ZIP 内パートの MD5（図だけの変更の切り分け）、docProps のメタデータ回帰（生成ツール既定の creator、テンプレート日付、revision の未増加）、本文 diff と削除行の一覧、見出しの増減、新出記号（出現 1 回を ★ 表示）、前版 SHA-256 の引用確認 |
| `run_selfcheck.py` | 合成 .docx を作って上記 2 本の動作を確認する（外部依存なし） |

## 使い方

```bash
# 本文の抽出（標準出力）。--stats で要素数を標準エラーへ
python3 tools/design_review/docx_review/docx_extract.py next.docx > next.txt
python3 tools/design_review/docx_review/docx_extract.py next.docx --metadata   # docProps を JSON で

# 前版との比較。--out に prev.txt / next.txt / diff.txt / report.md を保存
python3 tools/design_review/docx_review/docx_compare.py prev.docx next.docx --out review_next \
    --symbol "γ_W" --symbol "V_open"        # 出現数を数えたい記号があれば --symbol で追加

# 動作確認
python3 tools/design_review/docx_review/run_selfcheck.py
```

`docx_compare.py` は、2 つのファイルがバイト単位で同一のとき終了コード 1 を返します（レビュー対象にならない再アップロードの検出用）。
`--known known_versions.json` に既知の版の SHA-256 先頭桁を登録しておくと、どの版と同一かを来歴として表示します。
登録ファイルは次の形式です。

```json
{"versions": [{"version": "v1", "sha256_prefix": "0123456789abcdef", "size": 12345}]}
```

## レビュー手順への対応

1. 同一ファイルの検出 → `docx_compare.py` の SHA-256（自動）
2. 本文 diff → `docx_compare.py` の `diff.txt` と、レポート内の削除行一覧（黙った削除の確認用）
3. 図の比較 → パート比較で変更のあった `word/media/*` だけを目視
4. メタデータ回帰 → レポート §3 の警告
5. 付録の対応表と実差分の突き合わせ → 手動（削除行一覧と見出しの増減を併用）
6. 新出記号の定義確認 → レポート §6（出現 1 回は未定義の可能性が高い）
7. 式の検算 → 手動
8. 擬似コードの追跡 → 手動

## 制約

- 数式は本文中の OMML だけを扱います。画像として貼られた数式や埋め込みオブジェクトは抽出しません。
- 表のセル内の改行は `//`、入れ子の表は `[table] …` として 1 行にまとめます。
- 抽出行数は段落内の手動改行（Shift+Enter）を分割して数えるため、他のツールの行数とは一致しません。
