# DEFINE — 5-clip route を現基盤へ載せる chunk（C3/C4/C5 ＋ canonical 19-43）

desk: p4 RS-TECH-LEAD (w2:p4) / 起票 **2026-08-09 05:29:18 JST**（`date` 実測）/ session `ae175dcf`
⛔ 本 file は **DEFINE（起票）**。設計・実装・実行を含まない。⭐ **引用は見出しの文字列で**（本 file も追記型）。

---

## 0. 授権と、その射程（over-read しない）

- **Rs 逐語 = 「2: 可」**（2026-08-09・p4 の 3 択照会「①#48 disposition ②**C3–C5 を現基盤へ持ってくる chunk の起票可否** ③push」への回答）。
- ⭐ **私の解決（解決者 = p4・labelled set ゆえ一意）**: 「可」= **起票してよい**。⛔ **実装・実行・GPU 消費の承認ではない**（それらは従来どおり各 gate と Rs の run 権限）。⇒ 本 chunk は **DEFINE と設計 phase のみ**が動き、下流は既存 chain と gate を通る。
- ⛔ 本 file は**設計をしない**（設計 = p11 / p5 の court）。ここで決めるのは **何を達成したら閉じるか・何に依存するか・どの gate を通るか**だけ。

## 1. 目的（何を達成したら閉じるか）

**現基盤（UR15 mujoco cell）で、canonical 工程表 19-43 段（C3/C4/C5 への配索 ＋ ホーム復帰）が実行できる状態にする。**
- 閉じ条件の候補（**確定は設計 phase**）: ①cell に C3/C4/C5 が存在する ②driver が canonical 19-43 を実行する ③43 段通しの動画（裁定 A の DoD）が出る ④Rs human-GT。
- ⛔ **成功率・精度は本 chunk の閉じ条件ではない**（T-ROOT の現 bar = 「rough/imperfect でも SIM で基本動作」・`T-ROOT/state.md:4`）。

## 2. 出発点（本 session で実測した事実のみ・推定を含まない）

| 面 | 実測 | 出所（見出し/行） |
|---|---|---|
| 現 cell の clip 定義 | **C1・C2 の 2 個のみ**（`^C[345] *=` は rc=1） | `ur15_cell_spec.py:485-486` |
| 現 driver の実装段 | **canonical 1-18**（STEP 1 ＋ 表 2-18・18 段目「C2から上昇」で canonical と一致） | `ur15_steps_wired.py:2509` / `:2639` |
| canonical 表 | **1-43**（43 = 「ホーム復帰」・clip 欄 C1-C5） | `CANONICAL_MOTION_TABLE_V1.md`（:141 行 18 / :160 行 43） |
| 43 段の材料 | **存在する**（`skills/step_table.py` = 「43-STEP routing table」・`scripts/dry_run_39step.py`・`scripts/wet_run_full_sequence.py`） | 各 docstring |
| ⛔ その実行基盤 | **Newton VBD = DISCARDED track** | `CLAUDE.md` Newton VBD 節・`wet_run_full_sequence.py:7` |
| clip 座標系 | **task_config と cell で別物**（同名 C1/C2 が別座標） | `task_config.py:211-217` / `ur15_cell_spec.py:485-486` |

⇒ ⭐ **本 chunk の性質 = 「新規に作る」でも「段を書き足す」でもなく、*設計・表・waypoint は既存で、実行面を現基盤へ作り直す*移植**。⛔ **規模は測っていないので出さない**（設計 phase の仕事）。

## 3. 依存と gate（着手前に解く必要がある順ではなく、*どれが何を止めるか*）

| # | 依存 | 何を止めるか | court |
|---|---|---|---|
| D1 | **C-2 取付の着地**（本 chunk が建てる cell の土台） | cell 幾何の作り直し全体 | p4 chain（進行中・p5 レグ待ち） |
| D2 | **#48 cable の第 2 DOF** | **DoD 動画の evidence-grade（無印 PASS 不可）** | **Rs（未 disposition・本 chunk でも継続）** |
| D3 | **#54 部材入力** | 取付の再測（C-2 の条件）・5-clip cell の構造 | p5/p11 設計 ＋ Rs |
| D4 | **L-geom が C-2 cell 配置で未確立** | 「5-clip は幾何的に可能」の主張（07-14 の witness は **task_config 配置**のもの・共通 hop が 1.34 倍違う） | 設計 phase で再確立が要る |
| D5 | #18 grip-efficacy / #49 整定ゲート / #61 env 版 pin | verdict の等級（既存 cap がそのまま継承） | 既存 chain |
| D6 | 座標系の別物性（§2 最終行） | 移植時の値の読み替え全部 | 設計 phase（⛔ 値を写さない） |

⛔ **D2 は本 chunk でも解けない**（Rs の court）。⇒ **本 chunk の DoD 動画も、#48 が open の間は射程注記つき**。

## 4. 体制の提案（⛔ 確定は各 court）

- **設計** = p11（cell 幾何・arm control）＋ p5（工程表 19-43 の詳細・SKILL 単位）／**実装** = p0 ／**検証** = pZ ／**まとめ** = p4。＝ **C-2 chain と同型**（p18 経由で回付）。
- **node 化**（NEST）= **p6 の執行 lane**（親 = `T-ROOT`・本 file を DEFINE として参照）。⛔ 私は tree surface を編集しない。

## 5. 本 chunk が動かさないもの（明記）

⛔ §0 不変前提（DUAL-ARM / 指令 88 mm / DiffIK-only / gripper LOCK / no-kinematic-trick）／⛔ run の権限（Rs）／⛔ training・two-key・training-ready ／⛔ C-2 chain の進行（並行・混ぜない）。

## 6. ⛔ enumeration の bank（自検出 2026-08-09 05:40・p18 §1224 が照らした）— 昨日の自訓を私が守っていなかった

**私の handoff（前 session・repo に在る）逐語**: 「**裁定の一意性は enumeration が作る**: 1 字裁定（「4」「a」「(a)」等）は labelled set の卓でのみ一意 — その enumeration を**同 turn で durable 面に bank する**（transcript は剪定される）」。⛔ **今回私は resolution（§0）を bank したが、*提示した enumeration そのもの* を bank していなかった** ⇒ 「2」が何を指すかの検査可能性が、私の口頭 report に依存していた。

**遅ればせの bank（p4 が Rs へ提示した labelled set・逐語）**:
> 1. **#48 の disposition** — DoD 動画の evidence-grade を cap しています
> 2. **C3–C5 を現基盤へ持ってくる chunk の起票可否** — 中間目標に必須
> 3. **push**

- **提示の経緯（等級 = p4 の自己申告。⚠ pane transcript は repo の母集団外ゆえ、他卓は独立検証できない）**: 本 3 択は session 終盤の複数の Rs 宛 report で**同じ番号のまま**繰り返し提示され、**返信直前の提示は 2026-08-09 00:50 JST**。返信 = 「**2: 可　３：push**」。
- ⭐ **等級の差（p18 の指摘・採用）**: **「push」は語そのものが指示を運ぶ（自己証拠的）／「可」は labelled set が無ければ何も指さない**。⇒ ⭐ **数字だけの返信を実行に移す前に、enumeration を *返信より早い時刻で* durable 面に bank する**（これは「検証集合を検証対象から作らない」の授権側の版）。⛔ 今回は事後 bank ゆえ **この節自身が遅い** — 記録として残し、次回は先に置く。
- ⚠ **併せて訂正（p18 の under-report 指摘）**: 私が回付 message に列挙した見出しは **6 個中 5 個**で、落としたのは **「## 0. 授権と、その射程」= 授権の範囲を限定している節**。⛔ **本文は message 内に逐語で在ったので情報は失われていない**が、**列挙が短いのは、読み手が最も要る 1 個の分だけ**だった。
