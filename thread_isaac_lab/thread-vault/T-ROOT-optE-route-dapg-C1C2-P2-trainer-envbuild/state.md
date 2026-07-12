---
node_id: T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild
node_name: "W1 P2 env build (Stage-A spec v0.8.1 実装、staged ≤800 行/diff L3 chain)"
goal: "banked Stage-A 設計 (STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md v0.8.1、全 gate PASS + Rs W0-a 承認) を env-core 上に実装する。対象 = route_t/HOLD/oracle-API/bank v2/DR+recenter+curriculum/export+会計/OG port/recording contract v2/smoke 一式 (est ~1.35-2.55k LOC)。charter = eval_runs/troot_optE_dapg_wholeroute_scope_20260701/W1_ENVBUILD_CHARTER_RSTECHLEAD_20260712.md (B0-B7 chunk 列)。設計判断は本 node で行わない — 疑義 = STOP → spec ERRATUM 手続き (charter §7-4)。campaign は不発効 (HIGH-COST + production-launch + fresh Rs GO 背後、不変)。"
goal_verification: |
  charter §3 B0-B7 全 chunk close = node COMPLETE:
  - B0: c1pin revert + og format diff disposition + baseline sha pin
  - B1-B6: 各 chunk = L3 chain (pre 5体 [implementation-vs-spec fidelity scope] + [RULE-CHECK]) + chunk DoD legs + flag-OFF byte-preserve subset (毎 chunk、pinned baseline) + %10 audit + %12+%9 verify + explicit-path commit + p6 relay
  - B7: spec §8 smoke legs 全数 (bar = spec §8 表が正)。motion-bearing leg = 視覚レグ必須、物理妥当性正式 verdict = Rs video human-GT
  - 完了報告に §6 Rs 後決項 (OG band / mix 比率 / MAX_HOLD 再導出 / M-AB 時期) を単独項で同梱
status: IN_PROGRESS
parent_node: T-ROOT-optE-route-dapg-C1C2-P2-trainer
children_nodes: []
dependencies:
  precedent:
    - "Stage-A design-gate COMPLETE (spec v0.8.1 banked d17f8f9cd6/e8d53aae10、design chain 全 PASS)"
    - "Rs W0-a =「A」一括承認 2026-07-12 13:29 (W0A_PACKET_RSTECHLEAD_20260712.md:89 —「W1 (env build) 着手可」+ D-B trigger 充足)"
    - "P2-envcore COMPLETE (基底 build f6ee1443f5→HEAD 1640L) / P2-routeexec COMPLETE-with-carry-forward (抽出 twin run_route:1028 byte-repro 81/81)"
  blocker:
    - "charter p1 (OPS-SUP) verify = PENDING (trainer-DEFINE precedent)。B0 のみ verify 前着手可 (既 co-decide: c1pin revert %11 推奨 + %12 CONCUR)。B1+ 着手 = p1 PASS 後"
created: 2026-07-12T13:51:00+09:00
last_updated: 2026-07-12T13:51:00+09:00
spec_version: LTM-1 v1.2
session_history:
  - "2026-07-12 13:51 %12 (RS-TECH-LEAD, w2:p4) ⭐node 作成 (trainer charter §1 lazy-spawn 授権 + Rs W0-a W1 着手承認 + 本 turn Rs directive「W1 build charter」)。charter v0.1 DRAFT 起草 (W1_ENVBUILD_CHARTER_RSTECHLEAD_20260712.md: B0-B7 chunk 分割 / per-chunk L3 gate template / 担当 %11 build・%10 audit・%12+%9 verify [devplan §7:192] / Rs 後決項 carry 表 / 衛生規則 M12)。prior-art V7 = PASS disposition (hits = 認可設計系譜の自己参照のみ)。on-disk 前提実測: c1pin +23/+70 残 dirty (B0-1 revert 対象) / run_route:1028 実在。1:1 binding = %11 (COORD) builder session (charter 受領時)。次: p1 verify dispatch → PASS 後 %11 B1+ 解禁 (B0 は即時可)。"
---

# T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild — working notes

- 現況 (13:51): charter v0.1 DRAFT / p1 verify PENDING / B0 即時着手可 (%11)。
- Anchors (§運用4): LEDGER row49/50 → charter (本 node) → spec v0.8.1 (設計 SSOT) → W0A_PACKET (数値 decision-of-record) → devplan §7:192 (担当)。
- 数値基盤 = Rs W0-a 採択値 (HOLD 15/12/24placeholder、Δ-bound 0.020、DR±20 OFF 既定、mix 集合のみ)。smoke 再導出条項付きの値はその条項が governs。
