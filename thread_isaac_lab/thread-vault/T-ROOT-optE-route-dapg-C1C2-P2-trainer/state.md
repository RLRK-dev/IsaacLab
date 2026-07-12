---
node_id: T-ROOT-optE-route-dapg-C1C2-P2-trainer
node_name: "P2 whole-route RL trainer (RLPD residual-on-script) — FORK-1 closed-loop fix + carry-forward"
goal: "RL 閉ループ policy (RLPD、residual-on-script primary per devplan D-C) で whole C1→C2 route を DR±20mm 下で達成し、FORK-1 (開ループ drift、静的 fix 全 REFUTED) を per-step feedback 補正で解消する。凍結 base = banked byte-repro oracle (6d1cee5874)。charter = eval_runs/troot_optE_dapg_wholeroute_scope_20260701/TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md (DEFINE banked、p1 verify PASS + P4 PASS 09:31)。authority = BCRL_DEVPLAN_LADDER_V2 (LEDGER row47、Rs W0-a′ 承認)。"
goal_verification: |
  staged DoD (charter §3、DEFINE≠launch — campaign は全て HIGH-COST-GATE + production-launch-gate + fresh Rs GO):
  A. P2 env (L3 design-gate W0-c): oracle-query-API (CRIT1 phase-clock resolve) + progress scalar obs + contract 統一 + Δ非累積契約 (envelope = P4 ERRATUM 済: 実測 per-RL-step drift 直接比較、max ~1.9mm/RL-step ≪ bound 20mm — 旧「rate×decimation、mm/frame」は charter ERRATUM で撤回) + ⑦(b) cable-fork curriculum-reset 機構 + DR hooks (routeexec-⑦ env-level 継承) + OG port/composite/band 再較正 + throughput/device-parity smoke
  B. P3 demos: DR±20mm + script-SR-over-DR-grid 検収 + leg-2 batch
  C. R2b campaign: bar = Rs W0-a §4.3 確定値 (devplan draft ≥70% は illustrative)。carries: ⑨b live 分子 + 閉ループ full-fire + C2-seating video (Rs human-GT = Rs 専権、r5 §1.4 STEP16 CLASS-R)
  D. R3: 新規 off-policy trainer build ~500-800 LOC + campaign
  routeexec ①-⑧ full disposition (orphan-zero) = charter §6。
status: IN_PROGRESS
parent_node: T-ROOT-optE-route-dapg-C1C2
children_nodes:
  - T-ROOT-optE-route-dapg-C1C2-P2-trainer-stageA
dependencies:
  precedent:
    - "P2-routeexec = COMPLETE-with-carry-forward (2026-07-12 09:3x、oracle banked 6d1cee5874、①②⑤⑦(harness)⑧(precursor) DONE、②⑦(b)/③/④criterion/⑥/⑦env/⑧remainder TRANSFER 本 node へ — charter §6)"
    - "P2-envcore = COMPLETE (valid RL substrate — FORK-1 (a1) が builder を exonerate、Option B vindicated、routeexec state.md 04:18)"
  blocker:
    - "Rs W0-a: D-A〜D-D confirm + 数値閾値 (§4.3) + OG band α/β/γ — campaign (Stage C/D) を gate する (Stage-A design 作業は gate しない、devplan §7 W0-c 並行可)"
session_history:
  - "2026-07-12 10:31 %12 (RS-TECH-LEAD, w2:p4) Stage-A 子 node spawn (charter §1 lazy-spawn 授権): T-ROOT-optE-route-dapg-C1C2-P2-trainer-stageA 作成 (L3 design-gate W0-c、1:1 binding = %12 session)。children_nodes 反映。"
  - "2026-07-12 09:34 %12 (RS-TECH-LEAD, w2:p4) ⭐**node 作成 (DEFINE banked)** — trainer pivot = p4⇄p1 co-decide (Rs autonomy grant 08:xx「動画確認以外は君の判断か OPS-SUP と相談」; p1 CONCUR-with-corrections 09:11 → p4 draft → p1 verify PASS + P4 Δ-bound discharge PASS 両 conjunct 09:31 [magnitude: per-step drift-rate mean0.27/p95 1.08/max1.86 — ⚠単位 ERRATUM (charter 末尾): mm/RL-step が正 (mm/frame は誤)、×d は二重計上撤回、margin ~10× (script v2 a2ad75955d) / expressibility: seg24=grip seg ∈ EE-controllable subspace、α-6D で lateral 補正可; script p9_p4_deltabound_discharge.py sha fdcacf98])。charter = TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md。key structure: FORK-1 MW-substrate を本 node が SUBSUME (別 MW-node 不作成、RL closed-loop = fix そのもの) + routeexec disposition 同 turn pair (COMPLETE-with-carry-forward、①-⑧ orphan-zero 列挙 charter §6) + DEFINE/build と campaign の decouple (campaign = HIGH-COST + production-launch + fresh Rs GO、閾値 TBD 中 GO 不可)。algo = RLPD residual-on-script primary (D-C un-park、DQ1=B→A′ supersession = LEDGER 反映 p6 委任; Rs veto point = W0-a review)。次: p6 cascade (LEDGER trainer row + supersession note + map/manifest) → Stage-A design-gate 起草 (W0-c、Rs W0-a と並行可)。"
---

# T-ROOT-optE-route-dapg-C1C2-P2-trainer — working notes

- 現況: DEFINE banked (09:34)。次 = Stage-A (P2 env) design-gate 起草。campaign は Rs W0-a 閾値確定まで GO 不可。
- carry-forward 台帳 (from routeexec、charter §6 が正): ②⑦(b) curriculum-reset 機構 / ③⑨b live 分子 / ④閉ループ full-fire criterion / ⑥ C2-seating video (Rs-GT REJECTED cell-2037 → RL-deferred、Stage C) / ⑦ env-level DR wiring / ⑧ C1-escape cell + ⑬-VERDICT。
- P4 Δ-bound 結果 (Stage-A §6-9 input、ERRATUM 反映): 実測 drift max ~1.9 mm/RL-step ≪ DELTA_BOUND 0.020 (Stage-A spec §2 pin 済、旧「×decimation / mm/frame」は charter ERRATUM で撤回)。expressibility CLEARED (α-6D decision は不触)。
