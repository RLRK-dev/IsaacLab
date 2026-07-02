---
node_id: T-ROOT-Planning-Surfaces-Consolidation-20260702
node_name: "計画 surface 少数化 + 整合機構 (consolidation + consistency machinery)"
goal: "計画 surface ~10 個を 4 コア (SOMA / RS71 / LEDGER / 地図) + node DB + journal に集約し、整合を 3 層 (生成 / 機械 checker / 書込 rule) で担保する。"
goal_verification: |
  DoD: (a) 読む入口 = 地図 1 本 (live ≤~60KB) から SOMA/LEDGER へ到達可能、
  (b) manifest §2 が state.md 群から再生成され 2 回実行 0-diff (idempotent)、
  (c) validate.sh 新 layer が既知 dangling (SOMA:82「LEDGER row 53」型) を fail-first で検出後 clean、
  (d) GOALS.md / RL-Routing-Progress の有害・死亡記述が消滅 (freeze banner + pointer 化)、
  (e) CLAUDE.md 2 種変更 (§運用4 計画 surface 追加 + ポインタ差替) が Rs 承認文言どおり landing、
  (f) 全変更 atomic commit + 層2 post-debate + 層5 PASS。
status: IN_PROGRESS
parent_node: T-ROOT
children_nodes: []
dependencies:
  precedent:
    - "計画ファイル監査 P0 全3件 COMMITTED (12ee5cd2a1 / e05efab04a / 8a3c265ad7) + 2c070442ef (atomic commit 初実例)"
  blocker: []
created: 2026-07-02T13:59:11+09:00
last_updated: 2026-07-02T23:04:11+09:00
spec_version: LTM-1 v1.2
session_history:
  - session_id: "T-ROOT-Planning-Surfaces-Consolidation-20260702#s1"
    status: active
    summary: "lead %12: 起票 → design v1 → 5体 pre-debate → v2 → Rs D1-D5 承認 → M0-M4 実装 (%10 委任, 11 commits) → M5 CLAUDE.md 4 hunks + D5 rows → M6 8-agent 検証 + findings 修正 landed → 完了報告 (Rs ACK 残数点)"
    ts: "2026-07-02"
---

# 計画 surface 少数化 + 整合機構 (T-ROOT-Planning-Surfaces-Consolidation-20260702) — IN_PROGRESS (COMPLETE candidate、Rs ACK 残)

**目的詳細:** 監査 (`PLANNING_AUDIT_REPORT.md`) P1-6/P1-7/P2-8/P2-9/P2-10/P2-11 + 運用ルール提案の「少数化」目標での再パッケージ。
**Rs 承認 (全 verbatim):** ① 2026-07-02 13:58「①② 承認 少数化+整合機構の設計起案を進めて」(設計 GO + CLAUDE.md 2 類型 type-level 承認) → ② 18:3x「D1 実装 GO D3 D4 も承認」(実装 GO / LTM-1 v1.2 注記 / T4 freeze) → ③ **22:24「1 2 3 承認 進めて」の項目 2 = D2 (CLAUDE.md 4 hunks 最終文言 GO) + D5 (権限 matrix 行)**。D6 (allowlist 3 node) は D1 umbrella 内で charter 記載により実施 — Rs 明示名なし、M6 報告で 1-line ratification 要請中。
**L-TRIAGE:** final_L = **L3** (path match: CLAUDE.md / validate.sh logic 変更 + LTM-1 v1.2 note + >5 files)。5体 pre-debate 済、実装後 層2 post-debate ×5 + 層5 ×3 済 (M6)。
**設計 doc:** `eval_runs/troot_planning_files_audit_20260702/PLANNING_CONSOLIDATION_DESIGN.md` (**v2** + M6 close-out 節 = as-landed 文面の耐久記録) + `PLANNING_CONSOLIDATION_DEBATE_R1.md` + `C2_DRYRUN_FP_REPORT_M3_COORD2.md` + `coord2_cp_reports/` (%10 CP 報告退避)。

**進捗 2026-07-02 23:04 (M6 close):**
- **M0-M4 landed (%10、11 commits `bd38b26bbd`..`21c4c92aae`):** 地図/manifest → 薄い live view + 2026H1 archive (byte 保全 sha 検証済) / manifest §2 = GEN 生成 234 node (idempotent 2×0-diff, fidelity 20/20) / validate.sh layer 7 (C1-C5) + V9 wrapper 配線 (fail-first 証跡付) / GOALS.md pointer 化 (verify_goal_contract.sh PASS) / LTM-1 v1.2 注記 (design §3.5 verbatim, md5 一致) / T4 FROZEN banner (D4 文言 byte 一致)。
- **M5 landed (%12):** CLAUDE.md 4 hunks on-disk (:72 / :226 / :421 / §運用4(3)) — **CLAUDE.md は意図的 gitignore (.gitignore:2) → on-disk landing、as-landed 文面の耐久記録 = design doc M6 節 + log.md**。D5 権限行 = commit `55dae1a15a`。
- **M6 landed (%12):** 8-agent 検証 (層2×5 [CC6 NHA=IMPROVED / CC4 = **Fable slot 初適用**] + 層5×3 [STRUCT/RULE/SSOT]) → findings 修正: (i) records sweep (本 state.md + log.md M6 節 + LEDGER 統合行 + 地図 今ここ/正本ポインタ), (ii) checker 堅牢化 4 点 (crash-sentinel fail-closed / check 側 HARD 検出 / C2 membership = snapshot ∪ §2 / C2b row-ref leg 新設 — 各 fail-first 注入証跡 = scratchpad m6fix/), (iii) LTM-1 sha sidecar 再 pin (`sha256sum -c` OK), (iv) tracking 補完 (validate.sh layer script 6 本 + .validateignore + 本 state.md + design doc), (v) manifest :47 / index.md 00-PM / v1.2 label collision note。
- **DoD 照合:** (a) PASS — M6 で地図に正本ポインタ strip landed (それ以前は prose のみ = CC4/CC5 指摘)、(b) PASS (M2 acceptance)、(c) PASS — C2b leg が row-ref 型を検出 (row-999 注入 fail-first ✓、SOMA:82 は現在 resolve = clean)、(d) PASS (harmful 0 + FROZEN banner)、(e) PASS-with-2-deltas (hunk-1 に「(Rs D2 承認)」挿入 + bold 落ち — Rs retro-ACK 要請中)、(f) PASS (11+M6 commits atomic / 層2+層5 完了)。**DoD (a) の正直形 = 「地図 = router、正本へ ≤2 hop で機械的真実」(NHA 指摘の weakened form を採用)。**
- **残 Rs ACK (M6 報告で要請):** A1 権限 matrix の draft 超過分 (07-Design carve-out 明文化 + node-dir 拡張) / A2 hunk-1 の 2 delta retro-ACK / A3 LTM-1 :534・:611 cross-ref 1-line (NEST §9 Rs-gated) / A4 D6 ratification / A5 CLAUDE.md gitignore 非対称の扱い / A6 regen exit-2 注記の hunk 追記可否 / A7 RL-Routing-Progress:17 の qualifier (07-Design Rs-gated) / A8 SOMA:82 の行番号参照は現在 valid だが脆弱 (SOMA = Rs専権)。

**prior-art gate:** BLOCKER hit は旧 C9 系「guard-manifest (JSON artifact)」= 同語異義の false positive (RL harness 起動 pipeline の話)。計画 surface 統合の失敗 prior-art は無し — delta 記録済 (設計 doc §0)。
**scope 境界:** LTM-1 = v1.2 注記 1 件のみ (Rs D3; §7.2/P17 cross-ref は Rs ACK 待ち) / SOMA・RS71 の内容改訂なし (P1-4 = 別途 Rs専権) / log.md = 追記のみ / 履歴削除なし (archive = 移設、byte 保全)。
**rollback 注記 (M6 CC5):** 6 file が fused-blob first-track (validate.sh / LTM-1 / LL-ApproachCable / index.md / permissions / build_nest_snapshot.py) — **step rollback = 外科的 edit であり plain revert 不可** (revert は file 全削除になる)。GOALS.md は pre-chain 状態が復元不能 (gitignored → 上書き; Rs 承認済の意図的破棄; 断片 = PLANNING_AUDIT_REPORT.md:28) — **M4 rollback = design §2 T3 から pointer を再生成、revert ではない**。f60eebf3ee は既存 uncommitted .gitignore ~27 行を同時 first-commit (root-cleanup 由来、無害だが commit msg 未申告 — 本注記が開示)。
