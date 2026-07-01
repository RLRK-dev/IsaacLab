---
node_id: T-ROOT-optE-route-dapg-C1C2
node_name: "DAPG 経路全体 (whole C1→C2 route as the DAPG unit)"
goal: "Rs 決定 2026-07-01 22:00「(A) 経路全体」: committed square-on C1→C2 route (bcb7393ec8) を demo SEED に、経路全体を 1 つの学習 unit として DAPG 化する (P1 feasibility → P2 env/reward design → P3 demos → P4 train)."
goal_verification: |
  P4 trained policy が C1→C2 経路全体を P2 承認の成功条件で再現する (GPU HIGH-COST-GATE + Rs 承認後)。
  現況: P1 PASS (non-conservative) / P2 = pre-check BLOCK → 上流 DQ1 (UNIT 選択) Rs-PENDING / P3-prep (demo recorder) build 中。
status: IN_PROGRESS
parent_node: T-L1C-PerSkill-RL
children_nodes: []
dependencies:
  precedent:
    - "C1→C2 re-grasp WORKING (LEDGER row43, Rs-confirmed 2026-07-01, COMMITTED bcb7393ec8)"
  blocker:
    - "DQ1 UNIT 選択 (A residual-PPO / B BC-imitation / C narrow-RL / D RL-defer) = Rs-PENDING — P2 以降を gate"
created: 2026-07-02T07:15:00+09:00
last_updated: 2026-07-02T07:15:00+09:00
spec_version: LTM-1 v1.1
session_history:
  - "2026-07-01 lead %3 (RS-TECH-LEAD): scoping charter → %1 (COORD2) 7-dim scoping → arch A 採択 (Rs 23:28) → P1 charter → %2 (COORD) P1 probe → %0 (OPS-SUP) GT cross-PV CONCUR-WITH-CORRECTIONS"
  - "2026-07-02 lead %12 (RS-TECH-LEAD, post window-migration): P2 reward design → /pre-check BLOCK → %9 GT cross-PV CONCUR-BLOCK → Rs reframe 承認 (Q3-first) → P3 recorder spec v2.2 (5体 debate + re-verify) → %11 (COORD) build (L3) — 本 node 記録は計画ファイル監査 P0-③ (off-map 是正)"
---

# DAPG 経路全体 (T-ROOT-optE-route-dapg-C1C2) — IN_PROGRESS

**Rs 承認履歴:** 2026-07-01 23:28「推奨でよい」(arch A + P1 実行) / 2026-07-02「継続 推奨で良い」(P2 BLOCK 後の reframe = P3 demo-recorder FIRST) + 「3 go」(recorder build)。
**⚠ 記録是正:** 本 node は 2026-07-01 に PROPOSED + Rs 承認されたが state.md/manifest 未配置のまま P1 を実行 (off-map 実行、「record BEFORE execute」違反)。2026-07-02 計画ファイル監査 (eval_runs/troot_planning_files_audit_20260702) P0-③ で本記録により是正。

## Phase 構造 (node 内 phase、子 node ではない)
- **P1 feasibility** = ✅ PASS non-conservative (2026-07-02 00:1x, %2 probe + %0 GT cross-PV; whole-route+retain window EXISTS on CPU; 4 carried risks: row54 sliding-cradle / §4 curvature / cg-GPU whole-route screen 未 / reach-fragility)
- **P2 env/reward design** = ⛔ pre-check BLOCK (2026-07-02, 10 issues 2CRIT/4HIGH/4MED + %9 CONCUR-BLOCK; 上流事実: whole-route MDP env ABSENT + demos ABSENT) → **DQ1 (UNIT 選択) Rs-PENDING が gate**
- **P3-prep demo recorder** = 🔶 build 中 (%11, spec v2.2 = P3_DEMO_RECORDER_SPEC.md, L3 昇格 [diff>200], DoD 実行中) — UNIT 非依存 raw superset
- **P3 demos / P4 DAPG train** = ⏸ DQ1/DQ2 後 (P4 = GPU HIGH-COST-GATE + Rs 専権)

## DQ namespace (2026-07-02 reframe; 旧 Q1-Q7 token との衝突回避)
- **DQ1 = UNIT 選択** (A residual-PPO / B BC-imitation / C narrow-scope RL / D RL-defer) — Rs-PENDING (決定マップ図 ~/Downloads/q1_unit_decision_map.png)
- **DQ2 = whole-route env build + phase-advance 規則** — DQ1-gated (Rs design-gate L3)
- **DQ3 = demo recorder** — ✅ GO (Rs「3 go」) → build 中

## 一次記録 (pointer-only; narrative は log.md)
- log.md 2026-07-01 20:21〜 / 2026-07-02 05:38 エントリ群
- eval_runs/troot_optE_dapg_wholeroute_scope_20260701/ — DAPG_WHOLEROUTE_C1C2_SCOPING_COORD2.md / P2_REWARD_DESIGN.md (⛔BLOCK banner) / P2_PRECHECK_CROSSPV_OPSSUP.md / P3_DEMO_RECORDER_SPEC.md (v2.2) / **canonical_run_records/** (canonical env echo + fingerprint + 全 charter、/tmp から 2026-07-02 保全)
- LEDGER row43 (precedent) / logs/pre-check-log.jsonl (P2 BLOCK 記録)

*NEST minimal-schema 準拠 + session_history 付き (LTM-1 v1.1 §2.1 完全形)。View 再生成: scripts/build_nest_snapshot.py。*
