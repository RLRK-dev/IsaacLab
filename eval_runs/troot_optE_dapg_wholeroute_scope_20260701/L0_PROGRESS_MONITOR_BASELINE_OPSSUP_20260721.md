# L0 進捗監視 — ベースライン（pY OPS-SUP・p6 PLAN-KEEPER と連携）

**Author:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**作成:** 2026-07-21 10:33 JST。
**指示:** Rs「pY は PLAN-KEEPER と連携して T-ROOT-RS-TECH-LEAD（p4）・T-ROOT-RS-TECH-LEAD2（pQ）が L0 目標に進んでいるかを監視せよ」。
**性質:** 監視は評価であって駆動でない（OPS は設計 position を取らない・`LEDGER:20-23`）。本書は checkpoint 毎に更新する live baseline。

## L0 目標（権威定義・実測）

- **root goal**（`project-tree-manifest.md:6`）: 「Isaac Lab / SIM 5-clip cable routing vision-based task operation; **100%**」（⚠`:19` 注記: 95% as-originally-scoped は 2026-05-19 P0 KILL で infeasible 判定・再構成済）。
- **WMSO = L0 統合アーキテクチャの最上位**（`LEDGER:27`）。**RL / IL / Vision / World Model = 必須かつ conjoin**（いずれか欠けたら L0 主張不成立）。
- ⇒ 監視対象 = L0 へ流れ込む **2 arc**。

## 現 topology（10:33 peek 実測・stored map 不使用）

| pane | 役割 | arc |
|---|---|---|
| `p4` RS-TECH-LEAD | **まとめ役**（自分で実装も検証もしない） | Skill |
| `p0` IMPL-BUILDER | 腕の制御を**実装** | Skill |
| `pZ` IMPL-VERIFIER | p0 実装を**独立検証** | Skill |
| `pQ` RS-TECH-LEAD2 | WMSO 構築 | WMSO |
| `pS` MWSO-DESIGN | WMSO 設計批准 | WMSO |
| `pX` SKILL-DESIGN / `p5` SKILL-DETAIL-DESIGN | skill 分解・詳細設計 | 両 arc へ入力 |

⚠ p0/pZ は 2026-07-21 10:1x 新設（Rs 役割組み替え = 実装と検証を別 CC に分離）。⚠ brief 間 不整合 1 件（pZ brief「p4 の実装を検証」= p0 新設前の stale・p4 へ flag 済）。

## Arc 1: Skill-building（p4 / p0 / pZ）

- **目的:** WMSO が選択する skill を作る（`project-p4-purpose-...`）。当面 = 43-step 表を腕とコントローラで実現（Rs 裁定 A・DoD = 腕/ハンド/フィンガ描画動画）。
- **現在地:** 新体制発足直後。p0 が arm control 実装に着手。**(d) kinematic 完全削除 rework 下**（clip-retention pin のみ例外・裁定 B）。census 35 の source landing 待ち。
- **直近 gate:** 腕を actuator 駆動へ（kinematic 上書き除去）→ pZ 独立検証 → 動画 DoD。
- ⛔ **実行系 = CLOSED**（source/[CHANGE]/RUN/landing/push/training・kinematic-removal HALT 下）。

## Arc 2: WMSO（pQ / pS）

- **目的:** L0 統合（skill の選択・順序付け・handoff・回復）。
- **現在地:** **D1.1-A `contracts_v2` = FROZEN**（Rs freeze+push・parity 0/0）。**D1.1-B design（v13）in progress**。
- **直近 gate:** D1.1-B freeze — ⛔ blocked on: (a) **OPS-SUP consultation leg 未実施**（pY・Rs go 待ち）(b) **arity（枝数 B/A）SUSPENDED**（Rs 専権・Rs 自身の B/A 発言不整合が §運用10 STOP 中）。
- **続く:** D1.1-C・slice。impl/training/authority = CLOSED 継続。

## ⛔ L0 への横断ブロッカー（両 arc の *実行* が fence）

| # | ブロッカー | 出典 | 解ける条件 |
|---|---|---|---|
| 1 | **kinematic-removal HALT** — 全 run/training/production fence | `LEDGER:89` DDR header | 完全削除 + 独立 verify 完了 |
| 2 | **training-ready LOCKED** | DDR training-ready unlock 式 | (d-b) two-key ∧ cell-2 DoD-7 ∧ V0 acceptance |
| 3 | **trainer / 実行 driver ABSENT** | DDR#31（AC/IC/AR 削除・RoutingOrchestrator 構築点 0） | pX+pS 検討・決定 → 該当 lane build |
| 4 | **guard 破損 = 全 commit `--no-verify`** | DDR#34/#35 | L3 fix（owner p4・Rs 承認要） |

## 現時点の所見（honest・over-claim しない）

- **両 arc は DESIGN / IMPL レベルで前進中。** drift（L0 経路外の作業）は現時点で観測なし。
- ⚠**しかし L0 が要求する *実行*（RL/IL 訓練）は完全に fence** されている。上表 4 ブロッカーが未解消の間、**訓練へ進めない**。
- ⇒ **設計の勢いはあるが、実際に L0 へ向けて訓練を始める経路は ≥4 gate 未開放**。この gap を Rs に対して曇らせない。
- ⚠ 本所見は **10:33 時点の観測**。各 arc の内部詳細（p0 実装の実体・D1.1-B の残 open）は継続監視で深掘りする。

## 監視メカニズム（p6 と連携）

- **p6 = 計画面の鮮度/整合**（LEDGER / DDR / node state / map）を保持。
- **pY = 面 + 実体を読み、各 arc の L0 進捗を判定し、drift / blockage を Rs へ flag**。
- **cadence:** p6 の milestone relay を消費 + pY 定期 tick。checkpoint 毎に本 baseline を更新。
- **報告:** checkpoint or drift/blockage 発生時に Rs へ。数値・状態は本 artifact に接地。

---
**baseline = 2026-07-21 10:33 JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
