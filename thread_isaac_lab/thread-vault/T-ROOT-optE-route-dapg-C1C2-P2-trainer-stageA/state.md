---
node_id: T-ROOT-optE-route-dapg-C1C2-P2-trainer-stageA
node_name: "Stage-A P2 env design-gate (off-policy + oracle-ready 拡張設計、W0-c)"
goal: "trainer charter §3-A / devplan §6 に基づき、banked env-core (spec v1.5h、newton_route_env.py f6ee1443f5) を trainer-grade に拡張する delta 設計を L3 design-gate で確定する。対象 = oracle-query-API (CRIT1 phase-clock 解決) / Δ-bound pin (P4: per-step-rate × decimation) / transition export / reward 成分ログ / DR hooks (CABLE_XY_OFFSET env wiring) / ⑦(b) curriculum-reset env 統合 (route_executor state-bank :314/:366 再利用) / OG port+composite+band 再較正 / device-parity smoke 計画。PAPER-ONLY / 0-build / 0-GPU。"
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
last_updated: 2026-07-12T10:31:47+09:00
spec_version: LTM-1 v1.2
session_history:
  - "2026-07-12 10:31 %12 (RS-TECH-LEAD, w2:p4) ⭐node 作成 (charter §1 lazy-spawn 授権 = trainer DEFINE banked + Rs 09:5x「clear して Stage-A へ進め」+ autonomy grant 08:xx)。1:1 binding = 本 session。[L-TRIAGE] = L3 (self=auto、charter §3-A pin)。[CHECK] 完了: prior-art guard disposition = PASS (BLOCKER hits = 認可 devplan 自身 + env-core banked build plan = 再利用先行設計、失敗経路再走なし) / env-core 実装実態 on-disk 確認 (62D + [50] progress + α-6D projection 実装済 / transition export・reward 成分ログ・CABLE_XY_OFFSET wiring・oracle-API = 不在 → Stage-A 設計対象) / ⑦(b) state-bank = route_executor.py:314/:366 既存 / OG = scripts/og_offline_gate.py (27D/6D 契約)。次 = delta-spec 起草 → /reward-design + /pre-check → 5体 → cross-PV → 層5 → bank。"
---

# T-ROOT-optE-route-dapg-C1C2-P2-trainer-stageA — working notes

- Anchors (§運用4 接地順): LEDGER row47 → TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md §3-A/§6/§7 → BCRL_DEVPLAN_LADDER_V2 §6/§5-R2/§4.3 → P2_ROUTE_ENV_SPEC_INPUT v1.5h (banked basis) → env-core node state.md。
- P4 Δ-bound input (charter §7): per-step drift-rate |inc| mean 0.27 / p95 1.08 / max 1.86 mm/frame。Δ-bound = rate × decimation、control-freq 確定後 pin (§6-9)。
- Rs W0-a (D-A〜D-D confirm + §4.3 数値閾値 + OG band α/β/γ) = campaign gate であり本 design 作業は gate しない (devplan §7 W0-c 並行可)。
