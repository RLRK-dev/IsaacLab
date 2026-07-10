# HANDOFF — PLAN-KEEPER (w2:p6)

更新: 2026-07-11 ~06:31 JST (vault sidecar; memory 正本 = `handoff_cc_p6_plankeeper_2026-07-07.md`)

## Role (不変)
PLAN-KEEPER = 計画 surface 5 本 [地図 `docs/logical_decomposition.html` / node state.md / LEDGER / manifest / SOMA] の鮮度・整合 執行専任。**内容決定=%12(RS-TECH-LEAD)/Rs、私=反映執行+監視**。dispatch-driven。
standing: reply-to-sender / mechanical `$(date)` append / herdr backtick 禁止 + 2-step (send→send-keys Enter) / explicit-path atomic commit (`-A` 禁止) / node sub-milestone は IN_PROGRESS 維持。

## 現在状態 (2026-07-11 06:31、Rs 待ち=ゼロ、manifest 243、freshness OK)
- **route-executor** (IN_PROGRESS): ⭐comp3 残 DoD 消化 arc 開始 (Rs GO 06:29 `994b2923c2`、exec=%11)。scope=⑨b live 分子/⑥ full-fire live/C2-seating 動画/comp3b。probe-arc=終結(先行)。
- **vault-audit** `T-ROOT-Vault-DesignContent-Audit-20260711` = COMPLETE (`44ed2fa749`)。V1 LEDGER 122→143 (`66ec7c6651`) / V2 19/22 banner (`3fa1186a3b`、LEDGER 不触)。
- **PR-3** `T-ROOT-VaultRefCopy-SpotAudit-20260711` = PENDING (起動=Rs 別途)。
- **論文** `T-ROOT-Paper-BCRL-JA-20260710` = COMPLETE (04:46)。long-term 学術論文化 = future 別 node carry-forward。fork URL=RLRK-dev。
- **renewal** `T-ROOT-DesignDoc-Renewal-20260711` (IN_PROGRESS): batch 0/A/B done、C=C-now-prep、prep①/4 (invariance script `4e3dff5ac6`) done、prep② authoring。rewrite=別 gate。

## Standby triggers
1. comp3 per-item (⑨b/⑥/C2-seating/comp3b) via %11→%12 ping。
2. renewal prep ②〜④ (p5)。3. PR-3 起動 (Rs 別途)。4. rewrite 発火 gate / PR-2 (後日) / 論文 whole-project scope (将来 Rs)。

## Protocol 教訓 (本セッション)
- **sha 種別**: eval_runs deliverable/exec-plan = untracked content-sha (git commit でない)。`git show` fail→`sha256sum|cut -c1-8`。map に "commit" と書かない。
- **LEDGER-race hold**: executor が LEDGER/node 編集中は map-only、実反映は完了 ping 後。commit の LEDGER 不含を `git show --stat` 確認。
- **concurrent-modify**: node edit fail→re-read(Read tool)+git status→clean なら現況行のみ (session_history=executor 領域 不侵)。
- **coarse-map 圧縮** at arc closure / **no-churn on ack-only** dispatch / **surface-not-inject** (他 pane gap は報告して埋めさせる)。
- manifest §2 = status-only view → IN_PROGRESS 不変 sub-milestone は no-op。status 変化/新 node のみ regen。
- SOMA (04-Specs) = Rs 専権 hold、optE/route 欠 = known-gap (`04e05a8066`)。
