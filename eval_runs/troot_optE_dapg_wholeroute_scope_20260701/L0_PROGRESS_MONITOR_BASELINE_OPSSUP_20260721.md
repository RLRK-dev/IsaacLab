# L0 進捗監視 — ベースライン（pY OPS-SUP・p6 PLAN-KEEPER と連携）

**Author:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**作成:** 2026-07-21 10:33 JST。
**指示:** Rs「pY は PLAN-KEEPER と連携して T-ROOT-RS-TECH-LEAD（p4）・T-ROOT-RS-TECH-LEAD2（pQ）が L0 目標に進んでいるかを監視せよ」。
**性質:** 監視は評価であって駆動でない（OPS は設計 position を取らない・`LEDGER:20-23`）。本書は checkpoint 毎に更新する live baseline。

## L0 目標（権威定義・実測）

- **root goal**（`project-tree-manifest.md:6`）: 「Isaac Lab / SIM 5-clip cable routing vision-based task operation; **100%**」（`SOMA.md:16` = Rs 2026-06-23 に定性的 100% = 完全動作へ再定義）。
- **WMSO = L0 統合アーキテクチャの最上位**（`LEDGER:27`）。**RL / IL / Vision / World Model = 必須かつ conjoin**（いずれか欠けたら L0 主張不成立）。

### canonical driver（面ごとに役割が違う・p6 裁定 2026-07-21・採用）

| 用途 | driver | 注 |
|---|---|---|
| L0/目標の**定義**（何を要求するか） | **`SOMA.md ## Goals`**（SSOT） | GOALS.md から migrate |
| 成否/前進の**判定**（各 arc が PASS したか） | **`00-DESIGN-STATUS-LEDGER.md`**（成否 SSOT） | — |
| **route(43-step motion)の工程** | `RL-Routing-Design.md:1226 §2` step-table | ⚠**Skill arc の route に scope 限定・L0 全体の driver ではない** |
| 現在 frame の**表示** | `logical_decomposition.html` map | 派生 view・driver でない・上記から再生成 |

### ⭐⭐ 監視スコープ — L0 = 4 track・私の担当は 2 track（honest-scope・要 Rs 確認）

Rs は **p4（Skill）+ pQ（WMSO）** を私の監視対象に指定。しかし **L0 = RL/IL/Vision/WM の 4 conjoin**。実測（manifest）:

| L0 track | node（manifest 実測） | 所管 | 私の監視 scope |
|---|---|---|---|
| **Skill**（RL/IL の skill 実装） | p4/p0/pZ arc | p4 まとめ | ✅ 対象 |
| **WMSO**（統合） | `T-WMSO`（+ pQ arc） | pQ/pS | ✅ 対象 |
| **Vision** | **`T-Vision*` = 31 node**（多数 IN_PROGRESS・`T-ROOT` 直下） | 別 pane | ⛔**scope 外の可能性** |
| **World Model** | **`T-WM-*` = 27 node** | 別 pane | ⛔**scope 外の可能性** |

⛔ **L0 前進を 2/4 track で判定してはならない**（conjoin ゆえ Vision/WM が止まれば L0 も止まる）。⇒ **Vision/WM が私の監視 scope か、別 monitor かを Rs 確認**（下記 §要 Rs 確認）。本 baseline の「L0 進捗」判定は **Skill+WMSO の 2 track に限る**と明記する。

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
| 4 | **guard 破損 = 全 commit `--no-verify`**（⚠**DDR#34 = RESOLVED 09:47** fix `99ef217eb2`/verify `9cee084f54`・残 = **DDR#35 のみ**） | DDR#35 | L3 fix（owner p4・Rs 承認要） |

## 現時点の所見（honest・over-claim しない）

⚠ **本判定は L0 4 track のうち私の担当 2 track（Skill+WMSO）に限る。Vision/WM は未評価（scope 未確定・要 Rs）。** ⇒ 「L0 全体が前進」とは言えない — 2/4 track の判定である。

- **担当 2 arc（Skill・WMSO）は DESIGN / IMPL レベルで前進中。** drift（経路外作業）は観測なし。
- ⚠**しかし L0 が要求する *実行*（RL/IL 訓練）は完全に fence** されている。横断ブロッカー（kinematic-removal HALT / training-ready LOCKED / trainer・driver ABSENT / guard = DDR#35）未解消の間、**訓練へ進めない**。
- ⇒ **設計の勢いはあるが、実際に L0 へ向けて訓練を始める経路は複数 gate 未開放**。この gap を Rs に対して曇らせない。
- ⚠ 本所見は **10:3x 時点の観測**。各 arc の内部詳細（p0 実装の実体・D1.1-B の残 open）+ Vision/WM 2 track は継続監視で深掘りする（scope 確定後）。

## 要 Rs 確認（1 件・honest-scope）

⭐ **L0 = 4 track（RL/IL/Vision/WM conjoin）だが Rs 指示の監視対象 = p4+pQ = 2 track（Skill+WMSO）。** Vision（`T-Vision*` 31 node）・WM（`T-WM-*` 27 node）は別 pane 所管。⇒ **これら 2 track も私の監視 scope か、別 monitor か。** conjoin ゆえ 2/4 で「L0 前進」を判定できないため確認する。

## 監視メカニズム（p6 と連携）

- **p6 = 計画面の鮮度/整合**（LEDGER / DDR / node state / map）を保持。
- **pY = 面 + 実体を読み、各 arc の L0 進捗を判定し、drift / blockage を Rs へ flag**。
- **cadence:** p6 の milestone relay を消費 + pY 定期 tick。checkpoint 毎に本 baseline を更新。
- **報告:** checkpoint or drift/blockage 発生時に Rs へ。数値・状態は本 artifact に接地。

---
**baseline = 2026-07-21 10:33 JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
