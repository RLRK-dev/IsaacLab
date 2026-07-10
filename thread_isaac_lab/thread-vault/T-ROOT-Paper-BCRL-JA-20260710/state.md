---
node_id: T-ROOT-Paper-BCRL-JA-20260710
node_name: "論文 (explainer): 現用 BC+RL アルゴリズム解説・日本語"
goal: "Rs 直接指示 verbatim (原文ママ、誤字含む):「新規、いまはここで使用されているBC+RLのアルゴリズムの解説れべるでよい・日本語で」。解釈 (inference、p9 起案・Rs verbatim ではない): (a) 先行 draft 不使用・新規 (prior-art troot_s1b_academic_paper_draft_ja_0gpu_20260601 は基盤 superseded、骨格再利用も不使用) (b) 対象 = 現用 BC+RL アルゴリズム (c) 粒度 = 解説レベル (explainer、論文完成品でない) (d) 言語 = 日本語。"
goal_verification: |
  DoD: 初版 draft 完成 + 執筆契約 4 点遵守 (%12→p9 2026-07-10 23:57 送付済):
  ① 段階ラベル厳密化 — R2-R4 (α residual DC-1 / RLPD DC-2 等) = 「Rs 承認済 設計・未 build」明記、現在形で動作記述しない (ABSENT-IN-CODE 規律)
  ② 数値 trap — SR は公式値 0.716 のみ (strict_v2 58/81、W0-e CLOSED、pin W0E_F1B_SNAPDOWN=1)。0.728 は cite 禁止 (ERRATUM 値; 系譜 0.494→0.716 に触れる場合は erratum 明記)
  ③ DISCARDED track (env6-VBD 系) = 歴史として明示ラベル時のみ言及可
  ④ scope note 1 節 (主従の線引き、Rs が trim できる形)
  最終 gate = Rs 承認 (scope 最終権威 = Rs)。
status: IN_PROGRESS
parent_node: T-ROOT
children_nodes: []
dependencies:
  precedent:
    - "Rs 直接指示 (Rs→p9; Rs 側送信時刻 = 未確認 [p9 観測範囲外、正直記載]; p9 report 2026-07-10 23:5x → %12 relay 23:58 → p6 verbatim 照合 = p9 直接返信 2026-07-11 00:03)"
    - "執筆契約 4 点 (%12→p9 2026-07-10 23:57) + prior-art 評価 (troot_s1b 系 = superseded、Rs「新規」で不使用確定)"
  blocker: []
created: 2026-07-11T00:05:00+09:00
last_updated: 2026-07-11T00:05:00+09:00
spec_version: LTM-1 v1.1
session_history:
  - "2026-07-11 00:05 p6 (PLAN-KEEPER, w2:p6): node 登録 (%12 NEST 案 23:58 + p9 verbatim 照合 00:03)。照合結果: %12 の 3 点 goal 案は verbatim に忠実 (「新規」→(a) は文脈 inference [prior-art 廃棄/骨格再利用/新規 質問への回答] と判明) → p9 推奨どおり goal = verbatim 主 + 解釈 inference タグ付きで登録。assignee = p9 (PAPER-AUTHOR、執筆着手済・初版 draft 作成中)。成果物規約 = 初版 eval_runs/ 配下 paper-only 0-commit (evidence dir = eval_runs/troot_bcrl_algorithm_explainer_20260710 [p9 作成済]、commit 判断 = Rs)。起動承認 = Rs 直接指示 (NEST §3.1)。"
---

## goal / means / status
- **goal:** frontmatter verbatim + inference 解釈参照。粒度 = 解説レベル explainer、日本語、新規。
- **means:** p9 (PAPER-AUTHOR) 執筆。設計 SSOT 接地 (LEDGER/spec/コード精読) + 執筆契約 4 点遵守。初版 = eval_runs/troot_bcrl_algorithm_explainer_20260710/ 配下 paper-only 0-commit。
- **status:** IN_PROGRESS (p9 執筆中、初版 draft 作成済・引用行の機械照合中 [00:03 時点])。最終 gate = Rs 承認。
