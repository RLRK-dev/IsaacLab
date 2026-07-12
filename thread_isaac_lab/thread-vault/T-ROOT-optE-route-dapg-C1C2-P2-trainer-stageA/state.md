---
node_id: T-ROOT-optE-route-dapg-C1C2-P2-trainer-stageA
node_name: "Stage-A P2 env design-gate (off-policy + oracle-ready 拡張設計、W0-c)"
goal: "trainer charter §3-A / devplan §6 に基づき、banked env-core (spec v1.5h、newton_route_env.py f6ee1443f5) を trainer-grade に拡張する delta 設計を L3 design-gate で確定する。対象 = oracle-query-API (CRIT1 phase-clock 解決) / Δ-bound pin (P4 ERRATUM 済: per-RL-step 直接比較) / transition export / reward 成分ログ / DR hooks (CABLE_XY_OFFSET env wiring) / ⑦(b) curriculum-reset env 統合 (route_executor state-bank :314/:366 再利用 — ⚠spec §6.2 bank v2 が supersede [CRIT-1: 既存 bank は arm/gripper のみ、cable re-seed = build 項]) / OG port+composite+band 再較正 / device-parity smoke 計画。PAPER-ONLY / 0-build / 0-GPU。"
goal_verification: |
  design-gate chain 全 PASS = node COMPLETE:
  1. delta-spec doc 起草 (基底 = P2_ROUTE_ENV_SPEC_INPUT v1.5h banked basis、live 値は task_config/後継 doc pointer)
  2. /reward-design 4 成果物 (delta scope) + /pre-check (BLOCK→fold→再走 収束)
  3. 5体 [VERIFY] (CC2 correctness / CC3 physics / CC4 RL / CC5 SSOT / CC6 NHA) DECIDE=PASS
  4. %9 (OPS-SUP) 9-lens cross-PV + %10/%11 audit
  5. 層5 多視点 (幾何/物理/SSOT)
  6. [RULE-CHECK] Tier0-3 + explicit-path bank + p6 cascade
  build 着手は本 gate PASS 後の別 stage (campaign は HIGH-COST + production-launch + fresh Rs GO 背後で不変)。
status: IN_PROGRESS
parent_node: T-ROOT-optE-route-dapg-C1C2-P2-trainer
children_nodes: []
dependencies:
  precedent:
    - "trainer node DEFINE banked (bf088596a8、charter = TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md、p1 verify PASS + P4 Δ-bound discharge PASS 09:31)"
    - "P2-envcore COMPLETE (spec v1.5h、build f6ee1443f5、obs 62D / α-6D 非累積 residual / G1-G6 latched / Rs 動画 gate PASS)"
    - "P2-routeexec COMPLETE-with-carry-forward (oracle banked 6d1cee5874、⑦(b) state-bank 機構 route_executor.py:314/:366、charter §6 disposition)"
  blocker: []
created: 2026-07-12T10:31:47+09:00
last_updated: 2026-07-12T13:04:23+09:00
spec_version: LTM-1 v1.2
session_history:
  - "2026-07-12 13:04 JST %12 (RS-TECH-LEAD, w2:p4) ⭐**design-gate chain 全 gate PASS → bank**: spec v0.8 (v0.5→v0.6 4走目 WARN 条件充足 → v0.7 %11+%9 cross-PV CONCUR-w-CORRECTIONS 全 fold [⭐C1 両者独立同着: no-C2 quiet 誤読撤回、quiet = producer 経路のみ] → v0.8 5体 [VERIFY] cycle-1 FAIL [CRIT 0 / HIGH 7 / MED 13 / LOW 7 全 ACCEPT: H2 F-1a category 転用 → ERRATUM-3 / H7 DR dead-world → HOLD arming = G1-latch gate / H5 flag-gate + banked-DoD regression legs / H6 interface v2 deprecation + consumer #6 等] → cycle-2 26/27 VERIFIED + 3 機械修正 = PASS)。NHA = CHANGE_JUSTIFIED (条件 3 点充足経路確定)。charter ERRATUM ×3 (単位 / P4 統計窓 / F-1a) 発行 + p1 実証 CONFIRMED (script v2 a2ad75955d)。層5 = PASS 3/3 lens (独立 numeric 全再現 + SSOT git-clean)。RULE-CHECK Tier0-3 ALL PASS。verification-log 2 records (stageA-designgate-5tai-20260712 cycle 1/2)。層4 prior-art = PASS (self/系譜 hit のみ)。**node COMPLETE 宣言は Rs W0-a packet review と併せて推奨 (数値 harden は W0-a まで保留 — NHA 条件)**。"
  - "2026-07-12 11:5x %12 (RS-TECH-LEAD, w2:p4) [DESIGN-GATE] iterate 収束中: spec v0.1→v0.5 (STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md) + /reward-design artifacts v3。/reward-design GATE PASS (CATCH-1 HOLD_THRESH / CATCH-2 p3×HOLD fold 済) → /pre-check 1走目 BLOCK 12 issues (3 CRIT: bank-no-cable/route-clock 未設計/EE-HOLD 発火不能) → v0.3 全 fold → 2走目 BLOCK (fold 9/12 実、新規 9: N1 CRIT = comp5 は residual≡0 canonical 構成 → nominal-quiet band 不存在、HOLD@t343 = 正しい警報、bank capture = producer 経路; N2 div_grip seg 規則) → v0.4 全 fold → 3走目 BLOCK-narrow (9 N-fold 全 VERIFIED + partial 3 CLOSED; 残 = ISSUE-A 単位系 [diag rate は mm/RL-step、charter §7 P4 も同 mislabel → ERRATUM 発行 + p1 通知予定]) → v0.5 fold 済。0-GPU probe 実測: HOLD 閾値 15mm (健全域 band 10.56 / onset f343 / 猶予 54 RL steps)。次 = 4走目 (targeted) → 5体 [VERIFY] → %9 cross-PV (ERRATUM 通知同梱) + %11 audit → 層5 → RULE-CHECK → bank。"
  - "2026-07-12 10:31 %12 (RS-TECH-LEAD, w2:p4) ⭐node 作成 (charter §1 lazy-spawn 授権 = trainer DEFINE banked + Rs 09:5x「clear して Stage-A へ進め」+ autonomy grant 08:xx)。1:1 binding = 本 session。[L-TRIAGE] = L3 (self=auto、charter §3-A pin)。[CHECK] 完了: prior-art guard disposition = PASS (BLOCKER hits = 認可 devplan 自身 + env-core banked build plan = 再利用先行設計、失敗経路再走なし) / env-core 実装実態 on-disk 確認 (62D + [50] progress + α-6D projection 実装済 / transition export・reward 成分ログ・CABLE_XY_OFFSET wiring・oracle-API = 不在 → Stage-A 設計対象) / ⑦(b) state-bank = route_executor.py:314/:366 既存 / OG = scripts/og_offline_gate.py (27D/6D 契約)。次 = delta-spec 起草 → /reward-design + /pre-check → 5体 → cross-PV → 層5 → bank。"
---

# T-ROOT-optE-route-dapg-C1C2-P2-trainer-stageA — working notes

- Anchors (§運用4 接地順): LEDGER row47 → TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md §3-A/§6/§7 → BCRL_DEVPLAN_LADDER_V2 §6/§5-R2/§4.3 → P2_ROUTE_ENV_SPEC_INPUT v1.5h (banked basis) → env-core node state.md。
- P4 Δ-bound input (charter §7 + ERRATUM): per-step drift |inc| mean 0.27 / p95 1.08 / max 1.86 **mm/RL-step** (mm/frame 表記は ERRATUM で撤回、×decimation = 二重計上)。spec §2 で pin 済 (headroom ~10×)。
- Rs W0-a (D-A〜D-D confirm + §4.3 数値閾値 + OG band α/β/γ) = campaign gate であり本 design 作業は gate しない (devplan §7 W0-c 並行可)。
