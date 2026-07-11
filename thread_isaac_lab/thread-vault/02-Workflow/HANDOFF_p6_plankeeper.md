# HANDOFF — PLAN-KEEPER (w2:p6)

更新: 2026-07-12 ~03:25 JST (vault sidecar; memory 正本 = `handoff_cc_p6_plankeeper_2026-07-07.md`)

## Role (不変)
PLAN-KEEPER = 計画 surface 5 本 [地図 `docs/logical_decomposition.html` / node state.md / LEDGER / manifest / SOMA] の鮮度・整合 執行専任。**内容決定=%12(RS-TECH-LEAD)/Rs、私=反映執行+監視**。dispatch-driven。
standing: reply-to-sender / mechanical `$(date)` append / herdr backtick 禁止 + 2-step (send→send-keys Enter) / explicit-path atomic commit (`-A` 禁止) / node sub-milestone は IN_PROGRESS 維持。

## 現在状態 (2026-07-12 03:25、Rs 待ち=C2-seating 動画 human-GT PENDING、manifest 243、freshness OK)
- **route-executor** (IN_PROGRESS): ⭐**DoD⑥ (C2-seating video gate) = B RESOLVED** (Rs「推奨でよい」03:24 07-12、commit `8f8d5f9fa6`)。C2-seating = single-world locked-runner seated-cell `2037_x-20_y-15_Fon` 経由充足 (c2_seated_honest wall−0.257mm + c1_retained z_c1 828.9 → §運用29 両 leg conjoin PASS; 三者照合 AGREE pB numeric+pC video+§運用14; 動画 ~/Downloads DoD6_C2seating_working_producer_2037_x-20_y-15.mp4)。⚠env-core MW replay = FORK-1 grip-retention divergence で BLOCKED → 別 node (option A、RL/substrate track) carve-out (⚠未作成 = %12 DEFINE post-pB → 私 EXECUTE、創出 HOLD)。最終 = Rs human-GT (動画、numeric≠standalone PASS) PENDING。§運用30: 単一 cell ≠ seat-rate(⑨b)。反映 = node 現況+last_updated/map/LEDGER 07-12 marker (manifest no-op C3 243、SOMA hold)。残 arc = ⑨b live 分子/comp3b/FORK-1 別 node。先行: comp5 build ACCEPTED → ⑥ NUMERIC_NOGO (EXONERATED、FORK-1) → capability-first 三者照合 AGREE → probe arc 終結(fork④=F-A)。
- **vault-audit** `T-ROOT-Vault-DesignContent-Audit-20260711` = COMPLETE (`44ed2fa749`)。V1 LEDGER 122→143 (`66ec7c6651`) / V2 19/22 banner (`3fa1186a3b`、LEDGER 不触)。
- **PR-3** `T-ROOT-VaultRefCopy-SpotAudit-20260711` = PENDING (起動=Rs 別途)。
- **論文** `T-ROOT-Paper-BCRL-JA-20260710` = COMPLETE (04:46)。long-term 学術論文化 = future 別 node carry-forward。fork URL=RLRK-dev。
- **renewal** `T-ROOT-DesignDoc-Renewal-20260711` (IN_PROGRESS): batch 0/A/B done、C=C-now-prep、prep①/4 (invariance script `4e3dff5ac6`) done、prep② authoring。rewrite=別 gate。

## Standby triggers
1. **FORK-1 別 node 起票** = %12 DEFINEs content (post-pB localization: cable-drift vs build-parity で mechanism 分岐) → 私 EXECUTE (state.md + manifest §2 regen + map)。⛔創出 HOLD until %12 DEFINE (carve-out 決定は session_history 03:24 + LEDGER 07-12 marker + map で §運用4 即反映済、node = tracking vehicle)。
2. **⑨b live 分子/comp3b 進捗** (%11→%12 ping) → node 現況+map。**Rs human-GT** (C2-seating 動画最終確認) 着地 → map Rs-待ち行 clear。
3. renewal prep ②〜④ (p5)。4. PR-3 起動 (Rs 別途)。5. rewrite 発火 gate / PR-2 (後日) / 論文 whole-project scope (将来 Rs)。

## Protocol 教訓 (本セッション)
- **sha 種別**: eval_runs deliverable/exec-plan = untracked content-sha (git commit でない)。`git show` fail→`sha256sum|cut -c1-8`。map に "commit" と書かない。
- **LEDGER-race hold**: executor が LEDGER/node 編集中は map-only、実反映は完了 ping 後。commit の LEDGER 不含を `git show --stat` 確認。
- **concurrent-modify**: node edit fail→re-read(Read tool)+git status→clean なら現況行のみ (session_history=executor 領域 不侵)。
- **coarse-map 圧縮** at arc closure / **no-churn on ack-only** dispatch / **surface-not-inject** (他 pane gap は報告して埋めさせる)。
- manifest §2 = status-only view → IN_PROGRESS 不変 sub-milestone は no-op。status 変化/新 node のみ regen。
- SOMA (04-Specs) = Rs 専権 hold、optE/route 欠 = known-gap (`04e05a8066`)。
