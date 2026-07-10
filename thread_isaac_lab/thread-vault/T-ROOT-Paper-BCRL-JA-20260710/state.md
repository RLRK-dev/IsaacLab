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
last_updated: 2026-07-11T00:07:00+09:00
spec_version: LTM-1 v1.1
session_history:
  - "2026-07-11 00:07 p6 (PLAN-KEEPER、p9 M1 dispatch 00:06 反映): ⭐**M1 = explainer 初版 v0.1 完成 (00:0x)** — artifact = eval_runs/troot_bcrl_algorithm_explainer_20260710/BCRL_ALGORITHM_EXPLAINER_JA.md (462 行 / ~2.6k words、p6 fresh ls 照合済 00:06、untracked = 0-commit 設計どおり)。構成 = scope note / 問題設定+忠実度境界 / through-line / LADDER 地図 / 第I部 実装済 (R0 BC・OG gate・R1 4 経路・runner) / 第II部 Rs 承認済-未 build (R2 α・R3 RLPD・R4) / 文献対応 / 現況表 / 用語集 / 根拠一覧。gate: L-TRIAGE = L1 自己申告 (降格不 confirm なら L2 追加) / prior-art V7/V10 = 0 blocker / 引用行 on-disk 機械照合済 / %12 契約 4 点 機械照合 PASS (0.728 = erratum 文脈のみ / 未 build ラベル 9 / VBD = 歴史ラベルのみ)。⚠p9 が実質訂正 1 件を %12 に surface 済 (devplan:24「on-path 汎化 18×」= 実体 BC-vs-replicate-null val MSE 比、一次 = b2_cpD_report.md:14/16) — **LEDGER 行の扱い = %12/Rs 判断 pending、確定記載しない**。次 = %12 技術 cross-PV (dispatch 済) → Rs review。node IN_PROGRESS 維持。"
  - "2026-07-11 00:05 p6 (PLAN-KEEPER, w2:p6): node 登録 (%12 NEST 案 23:58 + p9 verbatim 照合 00:03)。照合結果: %12 の 3 点 goal 案は verbatim に忠実 (「新規」→(a) は文脈 inference [prior-art 廃棄/骨格再利用/新規 質問への回答] と判明) → p9 推奨どおり goal = verbatim 主 + 解釈 inference タグ付きで登録。assignee = p9 (PAPER-AUTHOR、執筆着手済・初版 draft 作成中)。成果物規約 = 初版 eval_runs/ 配下 paper-only 0-commit (evidence dir = eval_runs/troot_bcrl_algorithm_explainer_20260710 [p9 作成済]、commit 判断 = Rs)。起動承認 = Rs 直接指示 (NEST §3.1)。"
---

## goal / means / status
- **goal:** frontmatter verbatim + inference 解釈参照。粒度 = 解説レベル explainer、日本語、新規。
- **means:** p9 (PAPER-AUTHOR) 執筆。設計 SSOT 接地 (LEDGER/spec/コード精読) + 執筆契約 4 点遵守。初版 = eval_runs/troot_bcrl_algorithm_explainer_20260710/ 配下 paper-only 0-commit。
- **status:** IN_PROGRESS — ⭐M1 初版 v0.1 完成 (2026-07-11 00:0x、462 行)。残 = %12 技術 cross-PV → Rs review (最終 gate = Rs 承認)。詳細 = session_history 00:07 entry。
