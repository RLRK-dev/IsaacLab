---
node_id: T-ROOT-StepTable-Verbal-Teaching-20260703
node_name: "step-table 教示言語化 (motion authoring loop 効率化)"
goal: "Rs 意向 (2026-07-03 05:1x「今後、効率的に言葉で教示できるようにしたい」対象 = scripted 動作) を、Rs 原則「43step 表から外れるな」の延長で実装可能にする: step 表の行 (phase・動作・対象・条件) を日本語で編集 → route code 生成/パラメータ化 → byte-identity (不変行) + 動画/OG gate (変更行) で検証する motion authoring loop の設計。"
goal_verification: |
  Phase S (scoping): options 表 + 推奨が Rs に提示され、方式 (パラメータ駆動 / code-gen / interpreter) が Rs 決定される。
  最終 (実装 phase、別途 Rs GO): fix-⑤ 級の新動作 1 つが「表の行編集 → 生成 → gate PASS」だけで landing し、
  従来 loop (言葉→charter→手書き code ~1.5h) より往復数が実測で減る。
status: IN_PROGRESS
parent_node: T-ROOT
children_nodes: []
dependencies:
  precedent:
    - "B2 chain COMPLETE (fix-⑤ = 言葉→動作 ~1.5h の実測 case study; T-ROOT-optE-route-dapg-C1C2)"
  blocker: []
created: 2026-07-03T07:07:00+09:00
last_updated: 2026-07-03T07:07:00+09:00
spec_version: LTM-1 v1.2
session_history:
  - "2026-07-03 lead %12 (RS-TECH-LEAD): Rs「動いて。」(07:0x、%12 の scoping 起票 offer を引用) = DEFINE 承認 → 起票 + scoping charter → %10 (COORD2)"
---

# step-table 教示言語化 (T-ROOT-StepTable-Verbal-Teaching-20260703) — IN_PROGRESS

**Rs 承認:** 2026-07-03 07:0x verbatim「動いて。」(引用 = %12 の「step 表を教示言語そのものにする…scoping 起票はご指示があれば動きます」) = scoping DEFINE 承認。
**Rs 意向 SSOT:** memory `project-rs-goal-efficient-verbal-teaching-2026-07-03` (対象 = scripted 動作の authoring、学習系は対象外 [Rs 訂正 05:1x])。原則 = memory `feedback-step-table-structure-drives-guide-generation`「43step表からはずれるな」。
**Phase S (scoping、%10):** charter = `eval_runs/troot_steptable_verbal_teaching_20260703/charter_steptable_scoping_coord2.txt`。成果物 = options + 推奨 (方式決定 = Rs 専権)。実装なし・GPU なし・locked 編集なし。
**並行関係:** T-ROOT-optE-route-dapg-C1C2 (DQ7 (iv) ladder 実行中) と独立・並行。共有資源 = %10 の稼働のみ (%11 は DQ7 側)。
