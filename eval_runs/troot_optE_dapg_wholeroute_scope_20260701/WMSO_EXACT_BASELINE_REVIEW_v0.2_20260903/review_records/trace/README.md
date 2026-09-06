# trace 検証（期待結果先行固定）— 手続と artifact

- 根拠 = Rs 裁定 2026-09-06 §4（`review_records/rs_consult/RS_DECISION_20260906.md`）。08 §5 に必須手続として追加（v0.2.10）。
- 作成 = 2026-09-06 13:13 UTC（`date -u` 実測）。

## 手続（08 §5 と同文）

1. **固定**: 各指摘 / 決定について、初期状態・入力・事象の順序・満たすべき規範・期待結果を trace spec（JSON）に記録し、sha256 で固定する（`PIN_<date>.sha256`）。期待結果の根拠は設計上の要求（Rs 裁定 / 外部レビューの規範）であり、修正後の本文や評価器の挙動から逆算しない。固定は本文編集と評価器作成より**前**に commit する（順序は git 履歴で証明）。
2. **修正前後の評価**: 同じ期待結果で修正前（v0.2.8 / v0.2.9 = `review_records/baselines/`）と修正後（v0.2.10）を評価する。修正前で違反が現れ、修正後で消えることを確認する。修正前でも期待を満たした trace は「指摘の誤り / 前提不足 / モデル不足」を再検討し、regression control と明記する。
3. **正常系の対照**: 各 trace に control（正常経路）を付け、修正後も正常経路が通ることを確認する（全操作を拒否するだけの修正は合格にしない）。期待結果を変える場合は元の spec を上書きせず、理由と新版（新 file・新 PIN）を残す。

## label

- `PRE_PINNED` = 本文編集より前に固定した spec（`TRACES_v0210_prepinned_20260906.json`・D1–D11）。
- `POST_HOC` = 既に修正済みの版（v0.2.9）に対し、既存レビューの規範と反例を固定して事後に整備した spec（`TRACES_GA_posthoc_20260906.json`・GA-01..07）。「修正前に固定した」とは主張しない。
- `TEST_ONLY` = 設計試験専用の仮 baseline（`test_baseline_TEST_ONLY_20260906.json`・非実機・出力なし・昇格禁止）。

## 結果の記録区分（混同しない）

| 区分 | 本 dir の artifact | 意味 |
|---|---|---|
| 限定モデル検証 | `trace_eval.py` + `RESULTS_<date>.json` | 本文の規則を版ごとに小さな状態機械へ写した評価。WMSO 実装ではない |
| 文書 checker | `check_review_candidate.py`（package root） | 文字列 / 集合 / 連番 / 引用先の機械検査。時系列反例の不在証明ではない |
| 実装試験 | なし（impl CLOSED） | — |
| 実機試験 | なし（実機 authority CLOSED） | — |

限定モデルの成功を実機の安全性へ読み替えない。
