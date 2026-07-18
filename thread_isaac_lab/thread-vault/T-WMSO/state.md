---
node_id: T-WMSO
node_name: WMSO adoption — World-Model-Based Skill Orchestration (L0 integration architecture)
goal: "learned skill (BC / BC+RL / PPO / DAPG 等) を algorithm-agnostic な共通 lifecycle contract で扱い、vision-grounded state・skill-resolution world model・runtime skill selection・handoff・transition・recovery・safe fallback を統合する L0 architecture (WMSO) を、node 定義 + D0 architecture design から段階採択する。"
goal_verification: |
  charter §5 adoption sequence (D0→D1→D2→M0→O0→RT0→S0→V0) の各 gate exit condition + charter §6 の 10 binding acceptance gates を満たす。
  当面の accept 対象 = D0 (state/action/transition/safety schema + event deadline) の independent design verify (charter §5 D0 exit)。
  ⛔ production control / training launch / closed-loop authority は本 charter で未承認 (charter §0 / §8-4)。
status: IN_PROGRESS
parent_node: T-ROOT-RS-TECH-LEAD2
children_nodes: []
dependencies:
  precedent: []
  blocker:
    - T-Skill
    - T-Vision
    - T-WM
    - T-ROOT-optE-route-dapg-C1C2-P2-trainer
session_history:
  - id: T-WMSO#s1
    status: handed_off
    note: "p6 custody 起票。initial design owner = p4、independent verify = pN。Rs direct で s2/T-ROOT-RS-TECH-LEAD2 へ移管。"
  - id: T-WMSO#s2
    status: active
    note: "Rs direct 2026-07-18: development owner = T-ROOT-RS-TECH-LEAD2 (new Claude Code w2:pQ)。D0 read-only inventory を開始。independent verify = pN、custody = p6。"
created: 2026-07-18T09:29:01+09:00
last_updated: 2026-07-18T17:32:12+09:00
---

# WMSO — World-Model-Based Skill Orchestration (L0 統合 architecture)

## 0. 起票状態と境界 (p6 custody 起票)

**IN_PROGRESS。Rs direct 2026-07-18 09:24 で WMSO を L0 統合 architecture として採択し、同日 12:44 に新設 `T-ROOT-RS-TECH-LEAD2` へ開発を割当。** D0 read-only inventory の開始を本割当で authorize。owner 分担 = **T-ROOT-RS-TECH-LEAD2 development / pN independent verify / p6 custody**。

⭐ **名称 supersession (Rs direct 2026-07-18 11:10)**: 初回 bank `5ad800fa56` の旧称 **RT-WMSO / `T-RT-WMSO`** は provenance 上の historical label とする。current canonical name は **WMSO / `T-WMSO`**。名称から Real-Time を外しても、charter §4・§6 の multi-rate/event-driven/deadline/safety acceptance は不変。

⭐ **ownership supersession (Rs direct 2026-07-18 12:44)**: 09:36 の p4 ownership/grip-checkpoint 待ち narrative を supersede。p4 は grip gate chain (§DDR #18) を継続し、WMSO は新 Claude Code (`w2:pQ`) の `T-ROOT-RS-TECH-LEAD2` が独立に担当する。これにより WMSO D0 は grip checkpoint を待たず開始する。production/training 未承認は不変。

⛔ **境界 (charter §0 / §8-4)**: 本記録が承認するのは **設計 + node definition + D0 開始**のみ。**production control 変更 / training launch / WMSO inference launch / closed-loop authority / 既存 safety・orchestrator path の除去は未承認**。D0 は read-only inventory から開始 (charter §8-3)。

⛔ **分離 invariant (Rs direct 逐語「現 (d-b) route/pin は停止・混入させない」)**: 現 (d-b) route/pin 実装 と 既存 `T-WM` classifier cascade とは **混入させず**、explicit dependency で接続する (charter §1 / §8-2)。current route/pin work は intra-skill prerequisite であり本 charter で停止されない (charter §1 末尾) — 本 node と (d-b) work は別 chunk。

⭐ **用語訂正 (charter §0、Rs 逐語)**: high-level action は PPO 限定でなく **learned skill 一般** — BC / BC+RL / PPO / DAPG 等を **algorithm-agnostic な共通 lifecycle contract** で扱う。WMSO は motor command を生成せず skill の low-level controller を置換しない。

## 1. founding documents

- **founding charter** = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md` (OPS-SUP-CODEX 起草、Rs direction accepted)。
  - file sha256 = `e925e7a4f6dd16136118b7e1c44c499be1225c8d4f91552b8737fab0b79b657c` (deposit に pin)。initial bank = `5ad800fa56`、canonical rename bank = `0f6e4af8e4`、owner-assignment bank = 本 commit。
- **provenance/integrity deposit** = `00-Project-Management/_handoff/node-T-WMSO-pins-s1.sha256` (charter + 本 state.md + NEST rule を pin、repo-root から `sha256sum -c`)。
- **governing rule** = NEST 仕様書 `00-Project-Management/operational-rule-LTM-1.md` (LTM-1 v1.2)。

## 2. goal + L0 placement (charter §1)

WMSO = 4 つの Rs-mandated L0 means (RL / IL / Vision / World model) を横断する統合 architecture。`T-ROOT` 直下の administrative owner `T-ROOT-RS-TECH-LEAD2` の child として置く (`T-WM` 直下でない — T-WM は failure-classification/recovery cascade、WMSO は統合 architecture)。L0 means ↔ role: **RL**=RL-trained/fine-tuned skill 供給 / **IL**=BC/DAPG demo・init・learned skill 供給 / **Vision**=observation を belief/abstract state に接地・OOD/低信頼検出 / **WM**=skill-level transition・duration・success prob・cost・uncertainty 予測。

## 3. component 責務 (charter §2)

- **Skill Dynamics Model** (§2.1): `(belief_state, skill, goal)` に対し next grounded state・duration・success/failure class・cost・uncertainty の分布を skill 解像度で予測 (low-level cable dynamics は別途 validate なしに主張しない)。
- **Skill Orchestrator** (§2.2): initiation/safety predicate で候補 filter → continuation vs switching value 比較 → 次 skill 選択 → replan。bounded fast path (precomputed policy/Q) + bounded short-rollout slow path。
- **Skill Transition Manager** (§2.3): direct handoff / Transition Skill / Recovery Skill / re-observe-or-safe-stop の 1 つを選択実行。
- **独立 safety + event layer** (§2.4): low-level safety は WMSO より優先・WM 推論を待たない。mid-skill switching は declared safe interruption checkpoint でのみ。

## 4. required skill contract (charter §3)

各 learned skill (BC / BC+RL / PPO / DAPG 他) は共通 typed lifecycle contract を publish: skill_id・policy family・immutable policy/version hash・obs/action schema・training lineage / initiation predicate + belief confidence / success・failure・timeout・invalid termination class / progress phase + safe interruption checkpoint / Skill Handoff State schema + accepted incoming handoff set / duration・cost 分布 + resource 要件 / recovery-rollback target + fail-closed action。**BC+RL lineage は BC checkpoint・RL fine-tune config・final policy hash を区別** (同名異 lineage = 別 skill action)。

## 5. adoption sequence (charter §5) + real-time contract (charter §4) + acceptance gates (charter §6)

**sequence**: D0 Architecture → D1 Skill contracts → D2 Dataset → M0 Skill Dynamics Model → O0 Offline orchestration → RT0 Bounded fast path → S0 Shadow mode → V0 Closed-loop pilot。設計・contract・offline data は current skill work と並行可。**closed-loop authority は skill の initiation/termination/handoff contract 安定まで block** (charter §5 末尾)。

**multi-rate real-time (charter §4)**: Safety / Event-checkpoint / Deliberative の 3 decision class。`T_detect + T_ground + T_select + T_handoff < D_situation`。acceptance = p50/p95/p99/max/jitter/deadline-miss/fallback/safety-override (**bounded soft/firm real-time**、hard real-time は未主張)。

**10 binding acceptance gates (charter §6)**: ①algorithm independence ②vision grounding ③model calibration (per-skill+per-handoff、aggregate 不十分) ④unknown-state abstention ⑤safe interruption ⑥anti-thrashing ⑦real-time (deadline-miss+max+fallback latency、mean だけ不十分) ⑧safety independence ⑨comparative value ⑩**no premature claim (D0-M0 完了 ≠ training-ready/closed-loop GO、S0/V0 は各自 two-key)**。

## 6. dependencies (charter §1) + 責任分担

- **blocker (並行制約・統合依存)**: `T-Skill` (skill 供給) / `T-Vision` (belief 接地) / `T-WM` (WM、ただし WMSO ≠ T-WM classifier cascade) / `T-ROOT-optE-route-dapg-C1C2-P2-trainer` (active trainer/env path)。
- **code baseline dependency**: 既存 `routing_orchestrator.py` (D0 read-only inventory 対象、charter §8-3)。node でないため dependencies front-matter 外・本節に記録。
- **precedent**: なし (D0 設計/inventory は並行進行可、charter §5)。
- **責任分担 (Rs direct 2026-07-18 12:44)**: development/design = **T-ROOT-RS-TECH-LEAD2 (`w2:pQ`)** / independent verify = **pN** / custody (node/surface 保守) = **p6**。p4 は grip gate chain を継続し、本 node ownership から release。

## 7. 次 action (charter §8) + boundary invariants

**次** = D0 開始 (read-only inventory: current skill・policy provenance [BC+RL 含む]・obs schema・termination signal・checkpoint・`routing_orchestrator.py` 挙動) → **D0 independent design verify** (charter §5 D0 exit)。

⛔ **boundary invariants (未承認、超えたら STOP→Rs)**: production control 変更 / WMSO inference launch / training launch / closed-loop authority / 既存 safety・orchestrator path 除去。D0 が independent verify されるまで上記いずれも不可 (charter §8-4)。

## 8. D0 progress (custody-reflected, verifier-governed)

⭐ **2026-07-18 17:32 — D0 architecture draft milestone (PROGRESS, NOT a D0 gate PASS)**:

- **D0 §A–I architecture draft = BANKED** (`4baf5b2650`, sha256 `318e96471dbf…`, design-only): `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md` (author `w2:pQ`)。
- ⏸ **D0-exit independent design verify = HOLD** (`w2:pN`, 2026-07-18 17:25): commit/blob integrity PASS だが 7 design blockers — numeric event deadlines absent / event priority incomplete / belief+safety schema underspecified / scripted-wait identity undefined / SDM↔`T-WM` classifier ownership conflict / recovery-skill supply stage open / stale-SDM fallback → SDM slow path recursion。
- **pre-check = pending re-run/bank** (pN: ignored JSONL line のみで banked artifact でない; custody on-disk 確認 — banked `WMSO*PRECHECK*` doc なし)。pQ relay 17:20 の「pre-check PASS / verify PENDING」framing は pN verdict 17:25 に **superseded**。
- **node status = IN_PROGRESS 継続** (両 pane 一致・no D0-exit/status flip)。次 = pQ correction + pre-check re-run/bank + pN reverify。
- ⛔ boundary 不変 (charter §0/§8-4): production / training / inference / closed-loop 未承認。
