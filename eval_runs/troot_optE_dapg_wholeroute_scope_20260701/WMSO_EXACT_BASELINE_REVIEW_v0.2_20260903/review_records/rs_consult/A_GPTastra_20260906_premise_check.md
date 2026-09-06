# GPT-astra 回答（v0.2.8 外部レビュー）の前提 fact-check と verdict 記録

- 作成 = 2026-09-06 08:43 UTC（`date -u` 実測）・作成者 = CC。対象回答 = `A_GPTastra_20260906/00_REVIEW_JA.md`（sha256 `d6419a1a…7226`）/ `01_findings.json`（`8a25df85…454d`）/ chat 逐語 `A_GPTastra_20260906/A_GPTastra_20260906_chat_verbatim.md`。
- 位置づけ: 外部 AI reviewer の推奨（HOLD）。Rs 裁定・human two-key ではない。CC の verifier V9（3 lens）の判定 = `../VERIFY_V9_GA_v028_20260906.md`。

## 1. pin の再測（CC・repo 実測）

| 項目 | reviewer の宣言 | CC 実測 | 一致 |
|---|---|---|---|
| commit | `0c6f11c91bf42f3a0c0fa9a89190c8e298bd197d` | 同（branch `claude/v0-2-design-candidates-snqbmy`） | ✓ |
| 05 git blob | `ce176b4359e1364c0b71abc0da640e3f2fdaf86f` | `git rev-parse 0c6f11c9:…/05_…md` = 同 | ✓ |
| 06 git blob | `b796830db84a43136584820f3c1525626fc6cef2` | 同 | ✓ |
| 05 sha256 | `2e508b4e…10da`（SHA256SUMS の記載） | `git show 0c6f11c9:… \| sha256sum` = 同（working tree も同） | ✓ |
| 06 sha256 | `45212f20…aa49` | 同 | ✓ |
| zip | `ce2364cb…fdd8` | 受領 file の sha256 = 同・内部 SHA256SUMS 7/7 一致 | ✓ |

- reviewer 自己申告: 原本 sha のローカル再計算・`verify_exact_baseline_pins.sh`・`check_review_candidate.py`・盲検陽性対照は未実施。CC 側で V9 が pin 11/11 PASS・checker FAIL=0 を実測（`../VERIFY_V9_GA_v028_20260906.md` §0）。

## 2. 回答の「前提の訂正」に対する CC の確認

| reviewer の指摘 | CC の確認 |
|---|---|
| 「round 5 の HIGH 0」と「v0.2.8 の受理可」は別 | 正しい。11_ §11.1 も同旨を明記済（v0.2.8 本文への再レビューは未実施）。 |
| state 別の one-key 失効・arm_targets ⊆ ownership・解除義務の和集合は追加済 | 正しい（v0.2.7 R6-04・v0.2.8 R7-05 / R7-12）。 |
| 05:520「manager 不読で SafeStop が SafeHold に緩まない」は gateway 局所の Stop を含めると成立しない | 正しい（V9 confirmed GA-01・HIGH）。v0.2.9 で `stop_latch` を追加。 |
| 「同じ構成 hash」と「同じ物理 cell」は別 | 正しい（V9 confirmed GA-04・MEDIUM）。v0.2.9 で兄弟停止の key を `(site_id, cell_id)` に変更。 |

## 3. finding ごとの前提の正確さ（V9 判定）

| id | reviewer の前提（要約） | 実測 | 訂正 |
|---|---|---|---|
| GA-01 | 引用行と要約 | 正確 | 05:82 / 05:249 / 05:518 / 05:520 / D0:318-320 の引用は全て現行 text（0c6f11c9 = HEAD 8078c92b・byte 同一）に実在し、要約は正確。「pending_invalidate も (iii) へ送るだけで停止強度を保存しない」= 05:519/249 のとおり。 |
| GA-02 | 引用行と要約 | 正確 | 05:233-236 / 05:414-442（ActiveAuthorityLease block = :416-436）/ 05:565-571、A:157-160（:158 ActionId・:159 DefinitionHash）/ :306 / :372-382 は全て実在し要約は正確。「hash 衝突を仮定した反例ではない」も正（ActionId の preimage が provenance を含まないことは A:158/:218 で確認）。 |
| GA-03 | 引用行と要約 | 正確 | 05:183-191 / 05:230-234 / 05:558-577、A:151 / :372-380 は実在し要約は正確。「05:188 … BeliefRef の TTL / 開始判断の鮮度期限を含まない」= 正。 |
| GA-04 | 引用行と要約 | 正確 | 05:191 / :240 / :292、06:75-100（CellIdentity = :77-96）/ :255-260（tuple→array = :259）/ :507 は実在し正確。06:531 は「受理の権限」行で、兄弟 batch 規則の文は 06:532（1 行ずれ）。主張内容には影響しない。 |
| GA-05 | 引用行と要約 | 正確 | 05:249 / :292、06:538 / :540 は実在し正確。06:529 と引く状態遷移文は現行 06:530（1 行ずれ）。「A_g を直接 supersede すると fork 規則に抵触」= 06:540 のとおり。 |
| GA-06 | 引用行と要約 | 正確 | 05:251 / 05:712 / §3.8 証明 E（05:361）/ T-16（05:767）は実在し正確。 |
| GA-07 | 引用行と要約 | 正確 | 05:191 (l)、06:514-527（CellSafetyTimingBaseline block = :515-528）/ 06:539 は実在し正確。「数値未決定の問題ではなく入力経路の欠落」= 06:527 の tuple 型で確認。 |

## 4. verdict の扱い

- 外部 verdict HOLD（v0.2.8）は記録として保持。v0.2.9 は confirmed 7 件の fold 版であり、「HOLD が解消した」とは主張しない（同一 commit / 原本 sha を対象にした再検証が要る）。
- 外部 reviewer の「Rs が決める事項」4 点は 11_ §12.1 末尾へ転記（OPP-18 新設・OPP-16 追記）。
