---
node_id: T-ROOT-C3C5-Port-To-Current-Substrate-20260809
node_name: 5-clip route を現基盤へ載せる — C3/C4/C5 ＋ canonical 19-43 の移植
goal: "現基盤（UR15 mujoco cell）で、canonical 工程表 19-43 段（C3/C4/C5 への配索 ＋ ホーム復帰）が実行できる状態にする。〔p4 DEFINE 見出し『## 1. 目的（何を達成したら閉じるか）』逐語 @ `9ab375026a`〕"
goal_verification: |
  ⚠ **閉じ条件は未確定**（p4 DEFINE 逐語「確定は設計 phase」）。以下は *候補* であって acceptance ではない:
    ① cell に C3/C4/C5 が存在する
    ② driver が canonical 19-43 を実行する
    ③ 43 段通しの動画（裁定 A の DoD）が出る
    ④ Rs human-GT
  ⛔ 成功率・精度は本 chunk の閉じ条件ではない（T-ROOT の現 bar =「rough/imperfect でも SIM で基本動作」`T-ROOT/state.md:4`）。
  ⛔ DoD 動画は #48（cable 第 2 DOF）が open の間 **射程注記つき** — 無印 PASS 不可（p4 DEFINE 見出し『## 3. 依存と gate』D2）。
status: PENDING
parent_node: T-ROOT
children_nodes: []
dependencies:
  precedent:
    - "D1: C-2 取付の着地（本 chunk が建てる cell の土台）— court = p4 chain（進行中）"
    - "D3: #54 部材入力 — court = p5/p11 設計 ＋ Rs"
  blocker:
    - "D2: #48 cable の第 2 DOF — DoD 動画の evidence-grade を止める（無印 PASS 不可）— court = Rs（未 disposition）"
    - "D4: L-geom が C-2 cell 配置で未確立（07-14 の witness は task_config 配置・共通 hop が 1.34 倍違う）— 設計 phase で再確立が要る"
    - "D5: #18 grip-efficacy / #49 整定ゲート / #61 env 版 pin — 既存 cap がそのまま継承"
    - "D6: 座標系の別物性（task_config と cell で同名 C1/C2 が別座標）— 移植時の値の読み替え全部・⛔ 値を写さない"
session_history: []
define_artifact: "eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P4_DEFINE_C3C5_PORT_TO_CURRENT_SUBSTRATE_20260809.md @ 9ab375026a"
created: 2026-08-09T05:46:32+09:00
last_updated: 2026-08-09T05:46:32+09:00
spec_version: LTM-1 v1.2
---

# T-ROOT-C3C5-Port-To-Current-Substrate-20260809 — 5-clip route を現基盤へ載せる

## 0. 本 node の status がなぜ PENDING か（⛔ 起動していない）

**PENDING = 起票済・未起動。** 理由は 2 つとも NEST 仕様の手続そのもの:

1. **§3.1 起動手順 3→5**: `status を IN_PROGRESS に更新` は **CC session 1 の起動（session ID = `{node_id}#s1`）の後**に来る。本 node に **binding された session は無い**（`session_history: []`）⇒ IN_PROGRESS は事実に反する。
2. **§3.1 起動条件 2**: `precedent dependency 全件 COMPLETE`。**D1 は進行中・D3 は未決** ⇒ 起動条件を満たさない。

⇒ **PENDING は判断ではなく測定**。IN_PROGRESS への遷移は上の 2 つが解けた時（＋下記 §1 の授権）。

## 1. 授権の等級（⛔ over-read しない・起票と起動は別物）

| 何 | 誰の言葉 | 等級 |
|---|---|---|
| 本 chunk の **起票** | Rs 逐語「2: 可」（3 択照会の項② =「C3–C5 を現基盤へ持ってくる chunk の**起票可否**」） | **Rs 直接**。ただし ⚠ **numeral のみの返答** — 指示対象は返答の外の labelled set から来る |
| 「可」= 起票してよい | **p4 の解決**（解決者を自ら名乗り、labelled set の所在を開示） | **labelled inference**（隠れ推論ではない・ゆえに検査可能） |
| 実装 / 実行 / GPU | — | ⛔ **無い**（p4 DEFINE 見出し『## 0. 授権と、その射程（over-read しない）』逐語） |
| **node 作成 + 起動** | — | ⛔ **記録が無い** |

⭐ **最後の行の根拠（前例との対比・p6 実測）**: 直近の T-ROOT 子 node `T-ROOT-Kinematic-Pin-Complete-Removal-20260719` の `session_history` note は逐語で **「Rs 承認 (node 作成 + 起動、2026-07-20) により起票」** — **2 つを名指しで**承認された記録を持つ。本 node が持つのは **1 語（「可」）を 1 事（起票）へ解決したもの**。⇒ **前例と同じ強さの授権ではない**。この差を消さないために status を PENDING に置き、起動を別 gate として残す。

## 2. 本 node が **authorize しないもの**（明記）

⛔ 実装 ／ ⛔ run・GPU ／ ⛔ training・two-key・training-ready ／ ⛔ §0 不変前提（DUAL-ARM / 指令 88 mm / DiffIK-only / gripper LOCK / no-kinematic-trick）／ ⛔ C-2 chain の進行（並行・混ぜない）。
〔p4 DEFINE 見出し『## 5. 本 chunk が動かさないもの（明記）』〕

## 3. 体制（p4 提案・確定は各 court）

**設計** = p11（cell 幾何・arm control）＋ p5（工程表 19-43 の詳細・SKILL 単位）／**実装** = p0 ／**検証** = pZ ／**まとめ** = p4。= C-2 chain と同型。
〔p4 DEFINE 見出し『## 4. 体制の提案（⛔ 確定は各 court）』。⛔ 確定は各 court であり本 node は記録のみ〕

## 4. ⚠ p6 が provisional に置いたもの（p4 の court・確認待ち）

front matter の `dependencies` は NEST の **2-edge taxonomy（precedent = 完了必須 / blocker = 並行制約）**を要求するが、**p4 の DEFINE は D1–D6 をこの 2 語で分類していない**（表の列は「何を止めるか」）。
⇒ **p6 の暫定配置**: D1・D3 = precedent（cell の土台・部材入力 ＝ 完了が要る側）／D2・D4・D5・D6 = blocker。
⇒ **保守側の向き**: 迷った依存は precedent へ置いた（precedent は §3.1 #2 で**起動を止める**＝条件を増やす方向）。
⛔ **これは分類の決定ではない** — p4 が別に分ける場合は front matter を書き換える。**本 node は PENDING ゆえ、どちらの edge もまだ消費されていない**（precedent は §3.1 #2 起動で、blocker は §3.5 cascade で消費される）。

## 5. 出発点（p4 が本 session で実測・推定を含まない）

| 面 | 実測 | 出所 |
|---|---|---|
| 現 cell の clip 定義 | **C1・C2 の 2 個のみ**（`^C[345] *=` は rc=1） | `ur15_cell_spec.py:485-486` |
| 現 driver の実装段 | **canonical 1-18** | `ur15_steps_wired.py:2509` / `:2639` |
| canonical 表 | **1-43**（43 =「ホーム復帰」・clip 欄 C1-C5） | `CANONICAL_MOTION_TABLE_V1.md` |
| 43 段の材料 | **存在する** | `skills/step_table.py` ／ `scripts/dry_run_39step.py` ／ `scripts/wet_run_full_sequence.py` |
| ⛔ その実行基盤 | **Newton VBD = DISCARDED track** | `CLAUDE.md` Newton VBD 節・`wet_run_full_sequence.py:7` |

⇒ p4 逐語: 本 chunk の性質 = 「新規に作る」でも「段を書き足す」でもなく、**設計・表・waypoint は既存で、実行面を現基盤へ作り直す移植**。⛔ **規模は測っていないので出さない**（設計 phase の仕事）。

## 6. 記録の作法

- **本 node の DEFINE は追記型 file** ⇒ 引用は**見出しの文字列**で行う（p4 自身の規約・行番号と節番号は照合注記）。
- 本 file の作成 = p6 PLAN-KEEPER の執行 lane（p4 が routing 経由で court を p6 と明示・discretion 保持）。**内容の決定は各 court**、p6 は記録のみ。
