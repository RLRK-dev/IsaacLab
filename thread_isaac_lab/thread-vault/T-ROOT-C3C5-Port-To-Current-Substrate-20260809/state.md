---
node_id: T-ROOT-C3C5-Port-To-Current-Substrate-20260809
node_name: 5-clip route を現基盤へ載せる — C3/C4/C5 ＋ canonical 19-43 の移植
goal: "現基盤（UR15 mujoco cell）で、canonical 工程表 19-43 段（C3/C4/C5 への配索 ＋ ホーム復帰）が実行できる状態にする。〔p4 DEFINE 見出し『## 1. 目的（何を達成したら閉じるか）』逐語 @ `9ab375026a`〕"
goal_verification: |
  ⭐ **③ = 必須（Rs 確定 2026-08-09 09:3x・逐語「dod動画は必要」）**。⛔ 残り ①②④ は依然 *候補*（p4 DEFINE 逐語「確定は設計 phase」）:
    ① cell に C3/C4/C5 が存在する                         — 候補
    ② driver が canonical 19-43 を実行する                 — 候補
    ③ **43 段通しの動画（裁定 A の DoD）が出る — ⭐必須**  ＝ **腕・ハンド・フィンガを描画した動画**（裁定 A 逐語・LEDGER 内容で引く）
    ④ Rs human-GT                                          — 候補
  ⚠ **p6 が読み取らなかったこと（明示）**: Rs 発話は ③ を **必須**にしただけで、⛔ ①②④ を *不要* にしていない・⛔ ③ を *唯一の* 閉じ条件とも言っていない。
  ⚠ **等級**: Rs 直接発話（当卓が直接受領）。⭐ 裁定 A の「DoD = 腕・ハンド・フィンガを描画した動画」自体は本日以前から LEDGER に banked（本確定はそれを *本 chunk の閉じ条件* として固定したもの）。
  ⛔ 成功率・精度は本 chunk の閉じ条件ではない（T-ROOT の現 bar =「rough/imperfect でも SIM で基本動作」`T-ROOT/state.md:4`）。
  ⛔ DoD 動画は #48（cable 第 2 DOF）が open の間 **射程注記つき** — 無印 PASS 不可（p4 DEFINE 見出し『## 3. 依存と gate』D2）。
status: PENDING
parent_node: T-ROOT
children_nodes: []
dependencies:
  # ⚠ 本欄は NEST の 2-edge（precedent / blocker）しか持てない。p4 裁定 2026-08-09 06:01
  #   （kickoff 見出し「B. 裁定 — DEFINE の D1-D6 を NEST の語に割る」@ `ff4132f4c7`）は 4 class を使う:
  #     D1 = precedent ／ D3 = precedent（ただし *再測* の）／ D4 = precedent（ただし *主張* の）
  #     D2・D5 = grade cap（precedent でも blocker でもない）／ D6 = constraint（依存ではない）
  #   ⇒ ⭐ blocker = 0 件（設計 phase の着手を止めるものは無い）。
  #   ⛔ D3/D4/D2/D5/D6 は本欄の 2 語に収まらないので下に載せていない — 全 6 件は本文 §4 の表が正。
  #   ⛔「依存がある」を「止まっている」と読まない（p4 逐語）。
  precedent:
    - "D1: C-2 取付の着地（この cell の上に建てる。着地前に幾何を作り直せない）— court = p4 chain（進行中）"
  blocker: []
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

## 4. 依存の分類 — p4 裁定で確定（⛔ p6 の暫定配置は SUPERSEDED）

**確定 = p4 裁定 2026-08-09 06:01**（kickoff 見出し『**B. 裁定 — DEFINE の D1-D6 を NEST の語に割る**』@ `ff4132f4c7`・当卓 first-hand 実読）。⛔ **05:49 の p6 暫定配置（D1・D3 = precedent ／ D2・D4・D5・D6 = blocker）は失効**。

| # | p4 の分類（逐語） | 理由（p4 逐語） |
|---|---|---|
| **D1** C-2 取付の着地 | ⭐ **precedent** | この cell の上に建てる。着地前に幾何を作り直せない |
| **D3** #54 部材入力 | **precedent（ただし *再測* の）** | 設計着手の precedent ではない。**部材込み再測**が D3 を待つ |
| **D4** L-geom が C-2 配置で未確立 | **precedent（ただし *主張* の）** | 設計は進む。⛔「5-clip は幾何的に可能」と**言う**前に再確立が要る |
| **D2** #48 ／ **D5** #18・#49・#61 | ⭐ **grade cap**（precedent でも blocker でもない） | 作業を止めない。**verdict の等級**だけを縛る |
| **D6** 座標系の別物性 | **constraint**（作業中ずっと効く注意） | 依存ではない。**値を写さない**という作業規律 |

⇒ ⭐ **blocker = 0 件**。⛔ **「依存がある」を「止まっている」と読ませない**（p4 逐語 — 本夜 2 時間止めた誤読と同じ形）。

**⚠ p6 の執行上の注記（機構の限界・隠さない）**: NEST の `dependencies` 欄は **precedent / blocker の 2 語しか持てない**（NEST §2.1 = 2-edge へ縮小済）。p4 の 4 class のうち **front matter に載るのは D1 のみ**。⛔ **D3/D4 を `precedent` 欄に書けない** — 同欄は §3.1 #2 で**起動条件**として消費され、「起動を止める」意味になるが、p4 は 3 件とも**着手を止めない**と裁定しているため。⇒ **欄に載らない 5 件は本表が正**、front matter からは YAML コメントで本表を指している。

**⇒ status への影響 = 無し（再確認）**: 本 node が PENDING である理由 2 つのうち、§3.1 #2（precedent 全件 COMPLETE）は **D1 のみが該当**するようになったが、**D1 は進行中**ゆえ条件は依然 不成立。もう 1 つの理由（session 未 binding）も不変。⇒ **PENDING のまま**。

## 4-A. DDR row 64 に FOUNDATIONAL tag を付けない（p4 裁定 2026-08-09 06:08・p6 は従う）

- **裁定**（kickoff 見出し『**2026-08-09 06:08:37 — 裁定 2 件: DDR row 64 の FOUNDATIONAL tag ＝ ⛔付けない**』）: 当該 tag の運用実態は「**§0 の不変前提に触れるか**」の述語。row 64 は**証拠の *射程* についての行**であり **premise を変えていない** ⇒ **付けない**。
- ⛔ **p4 逐語の核心**:「**session 開始 digest に載せたいから tag する**」は採らない — **述語を、その副作用のために使うこと**になり、以後その述語は誰にとっても意味を失う。
- **p6 の測定（p4 の明示した限界を埋める）**: p4 は「digest は tag 付き行だけを配る」を第一手で確認できていないと明記（hook *script* を grep して 0）。⇒ **p6 は hook の *出力* を実読して確認済**（形 = `- #<id> [FOUNDATIONAL] <claim, cut> -> <解消条件, cut>`・内容 88 字で切り・**id 集合が tag 付き 27 行と完全一致**）。**p18 が同じ query を独立に走らせて再現**（27 / 64 / row64=0 / row54=1）。
- ⇒ **残る事実（隠さない）**: row 64 は **session 開始時には配られない**。p4 が置いた代替の保護 = ① row 64 の head marker が **88 字の内側**に警告を持つ（**p6 実測で成立**）② **C3-C5 設計者の入口は DEFINE** で、そこに D4 が同内容を持つ ③ **本 node の §4 表**。⇒ **入口から入る読み手には届く**。

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
