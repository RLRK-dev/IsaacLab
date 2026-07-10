---
node_id: T-ROOT-VaultRefCopy-SpotAudit-20260711
node_name: "reference-over-copy 規約 spot-audit (PR-3 follow-on)"
goal: "reference-over-copy 規約 (memory feedback-vault-consistency-reference-over-copy 準拠) の spot-audit: 設計内容が copy-duplication でなく reference-over-copy で維持されているかを抽出検査し、逸脱 item に disposition を付与する。起票根拠 = audit node T-ROOT-Vault-DesignContent-Audit-20260711 session_history 2026-07-11 04:38 entry (Rs 最適化 package 承認 04:38 で PR-3 = follow-on task 化を承認済; ⛔本 node の起動 = Rs 別途)。"
goal_verification: |
  DoD (charter レベル、起動時に精緻化):
  ① reference-over-copy spot-audit: design content の copy-duplication 逸脱を抽出
  ② 逸脱 item に disposition (reference 化 / 許容 / archive) を付与
  ③ 改変は per-item Rs 承認 gate (設計内容改変は Rs 専権)
  ⚠除外 = 07-Design 内部 (renewal node owns) + vault-audit V1/V2 で処理済 lineage (二重 scope 禁止)
  最終 gate = per-item Rs 承認。
status: PENDING
parent_node: T-ROOT
children_nodes: []
dependencies:
  precedent:
    - "audit node T-ROOT-Vault-DesignContent-Audit-20260711 = COMPLETE (Rs package 承認 04:38 で PR-3 follow-on 化承認、commit 44ed2fa749 closure)"
  blocker:
    - "起動承認 = Rs 別途 (PENDING; task 化のみ承認済、起動 gate は未)"
created: 2026-07-11T06:18:00+09:00
last_updated: 2026-07-11T06:18:00+09:00
spec_version: LTM-1 v1.1
session_history:
  - "2026-07-11 06:18 p6 (PLAN-KEEPER、%12 node closure dispatch 06:18 反映): PR-3 follow-on node 起票 (%12 依頼)。status = **PENDING** (task 化 = Rs package 承認 04:38 で承認済 [起票根拠 = audit node session_history 04:38 entry cite]、⛔起動承認 = Rs 別途 = blocker)。parent = T-ROOT。assignee = 未定 (起動時)。除外境界 = 07-Design 内部 (renewal owns) + vault-audit V1/V2 処理済 lineage (二重 scope 禁止)。manifest §2 に PENDING node として登録。次 = Rs 起動承認待ち。"
---

## goal / means / status
- **goal:** frontmatter 参照。reference-over-copy 規約の spot-audit (PR-3 follow-on)。
- **means:** 起動後に spot-audit → 逸脱抽出 → disposition (per-item Rs 承認)。設計内容改変は Rs 専権。
- **status:** PENDING — task 化承認済 (audit node 04:38 PR-3 follow-on)、起動 = Rs 別途。除外 = 07-Design 内部 + V1/V2 処理済 lineage。
