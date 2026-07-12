# HANDOFF — PLAN-KEEPER (w2:p6)

更新: 2026-07-12 ~09:55 JST (vault sidecar; memory 正本 = `handoff_cc_p6_plankeeper_2026-07-07.md`)

## Role (不変)
PLAN-KEEPER = 計画 surface 5 本 [地図 `docs/logical_decomposition.html` / node state.md / LEDGER / manifest / SOMA] の鮮度・整合 執行専任。**内容決定=%12(RS-TECH-LEAD)/Rs、私=反映執行+監視**。dispatch-driven。
standing: reply-to-sender / mechanical `$(date)` append / herdr backtick 禁止 + 2-step (send→send-keys Enter) / explicit-path atomic commit (`-A` 禁止) / node sub-milestone は IN_PROGRESS 維持。

## 現在状態 (2026-07-12 09:55、Rs 待ち ×1、manifest 244、freshness OK)
- ⭐**trainer node** `T-ROOT-optE-route-dapg-C1C2-P2-trainer` (IN_PROGRESS、**新 駆動 arc**、DEFINE banked `bf088596a8` 09:34): RL 閉ループ (RLPD residual-on-script primary = D-C 採択、p4⇄p1 co-decide under Rs autonomy grant) で whole route @DR±20mm + FORK-1 (a1 open-loop drift、静的 fix 全 REFUTED) 解消。base = byte-repro oracle `6d1cee5874`。staged DoD A-D: **次 = Stage-A (P2 env) design-gate 起草**。⛔campaign (C/D) = HIGH-COST + production-launch + fresh Rs GO (Rs W0-a 閾値確定まで GO 不可)。
- **route-executor** = ⭐**COMPLETE-with-carry-forward** (09:34): oracle DONE banked、①-⑧ orphan-zero TRANSFER→trainer (charter `TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md` §6)。**⑥ cell-2037 動画 = Rs human-GT REJECTED [cable off C1] → Stage-C RL 再達成後 再提示** (gate 自体 OPEN 継続)。comp3b retired / FORK-1 別 MW-node = trainer SUBSUME。私 cascade commit = `2504439495` (map 現在地=trainer/LEDGER trainer row+D-C note/manifest 244/routeexec 現況 closure)。
- **Rs 待ち ×1** = C2-seating 動画 human-GT (Stage-C 提示物待ち)。SOMA current-化 = Rs 判断待ち (別 open loop)。
- **vault-audit** `T-ROOT-Vault-DesignContent-Audit-20260711` = COMPLETE (`44ed2fa749`)。V1 LEDGER 122→143 (`66ec7c6651`) / V2 19/22 banner (`3fa1186a3b`、LEDGER 不触)。
- **PR-3** `T-ROOT-VaultRefCopy-SpotAudit-20260711` = PENDING (起動=Rs 別途)。
- **論文** `T-ROOT-Paper-BCRL-JA-20260710` = COMPLETE (04:46)。long-term 学術論文化 = future 別 node carry-forward。fork URL=RLRK-dev。
- **renewal** `T-ROOT-DesignDoc-Renewal-20260711` (IN_PROGRESS): batch 0/A/B done、C=C-now-prep、prep①/4 (invariance script `4e3dff5ac6`) done、prep② authoring。rewrite=別 gate。

## Standby triggers
1. **Stage-A (P2 env) design-gate 起草 milestone** (%12 relay、Rs /clear-vs-continue 後着手) → trainer node 現況+map (manifest no-op)。
2. **trainer staged 進捗** (B/C/D) / **Stage-C RL 由来 C2-seating 動画 → Rs 再提示** 着地 → Rs-待ち行 update。
3. renewal prep ②〜④ (p5)。4. PR-3 起動 (Rs 別途)。5. rewrite 発火 gate / PR-2 / 論文 whole-project scope (将来 Rs)。
✅ discharged: FORK-1 別 node (SUBSUME) / ⑨b・comp3b (TRANSFER/retired) / §運用10 (banked) / r5 (INVARIANT HOLDS)。

## Protocol 教訓 (本セッション)
- **sha 種別**: eval_runs deliverable/exec-plan = untracked content-sha (git commit でない)。`git show` fail→`sha256sum|cut -c1-8`。map に "commit" と書かない。
- **LEDGER-race hold**: executor が LEDGER/node 編集中は map-only、実反映は完了 ping 後。commit の LEDGER 不含を `git show --stat` 確認。
- **concurrent-modify**: node edit fail→re-read(Read tool)+git status→clean なら現況行のみ (session_history=executor 領域 不侵)。
- **coarse-map 圧縮** at arc closure / **no-churn on ack-only** dispatch / **surface-not-inject** (他 pane gap は報告して埋めさせる)。
- manifest §2 = status-only view → IN_PROGRESS 不変 sub-milestone は no-op。status 変化/新 node のみ regen。
- SOMA (04-Specs) = Rs 専権 hold、optE/route 欠 = known-gap (`04e05a8066`)。
