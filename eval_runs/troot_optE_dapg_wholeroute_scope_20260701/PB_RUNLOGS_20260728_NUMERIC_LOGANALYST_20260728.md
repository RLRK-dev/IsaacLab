# pB 数値レグ — 2026-07-28 の 13 本の log（p18 `-503` / 三者照合の 1）

**測定者:** LOG-ANALYST (`w2:pB`)。**発行:** 2026-07-28 12:34 JST（date-THEN-write）。
**依頼:** p18 `MSG-P18-PB-NUMERIC-LEG-13-BANKED-LOGS-20260728-503`。
⛔ **本書は numeric 単独 PASS を出しません。** 視覚レグ = pC、最終 = Rs の動画判定。
⛔ **本書は「log がそう印字している」までを述べます。** 物理的に何が起きたかの判定ではありません。

---

## 0. 対象と pin

commit `823ddf963e` の `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/run_logs_20260728/` 全 13 本。
私は **on-disk でなく blob を `git show` で取り出して**読みました（共有ツリーは他 pane が編集中のため）。取り出した内容の sha256:

| file | 行 | 内容 sha256 |
|---|---|---|
| `run_t1.txt` | 41 | `7bceaf69ae084eaab0982cecf087193e7e56a75961541f1e480b0920af1ad50a` |
| `run_t2.txt` | 33 | `476f76bfc4eb34be2a9931a7bcb37282880d1ca48d27d2eb364c7db861116e83` |
| `run_t3.txt` | 232 | `0ff6a01232dfffb465a6ebc160a34ad9916a6056939c091793389389848f2284` |
| `run_t4.txt` | 234 | `f73e05e193399219afb39d390507979ae045532b65b7843b2360900f682cbfe5` |
| `run_t5.txt` | 210 | `768da9d40941314a8fa351023dd2efa823fcca33fa3a2f5c9261d88ad787f74e` |
| `run_t6.txt` | 232 | `e456b967def72677a6b749d809a51e9bad49a32f55a34e8327d6c741aa5b87ce` |
| `run_t7.txt` | 264 | `51aba24c5f26449b514284e6e437d01c43858b02ac7e6c6d30eec8f77e47830e` |
| `run_t8.txt` | 259 | `bf9eecedbf39bde6a89842dc3121d0677cb625dcb1b3bf1e9356b0499e4d5e3b` |
| `run_t9.txt` | 122 | `f20b6abd992a8c8c9a77db9a7e1e28853bad720aa5dd4960b775355dc08ffccd` |
| `reg_A.txt` | 40 | `05ab4bdc06031864aba7585172a556c1f7aed7536f281f66243221d66006724a` |
| `reg_B.txt` | 40 | `16edc57598b9e7ad806b2ce3a54c5f2902b33f729680d7046245d8709f94435c` |
| `reg_C.txt` | 40 | `2662af6946dead14a8f6bf2c85f21ba1c7cd5c10e3a32bd2c53d2b52345a5560` |
| `attcap2.txt` | 49 | `fbc1ea15d8c4edeea816e898bb74082cc0e197d1005b2fb7f6ba292214737330` |

⚠ p18 の依頼文にある「全 13 本（run_t1..t9 + attcap2 + reg_A/B/C）」= 13 本、私の数え **一致**。

---

## 1. ⭐⭐⭐ 素性 — 13 本は同じ code の走行ではありません（依頼に無い項目・先に述べます）

各 log の 3 番目の警告は `ur15_steps_wired.py:NNN: UserWarning ... m = cell.compile()` を印字します。
NNN = `m = cell.compile()` の行番号。**13 本で 4 種類**:

| NNN | log |
|---|---|
| 257 | `run_t1`, `run_t2` |
| **258** | `run_t3`, `reg_A`, `reg_B`, `reg_C` |
| **266** | `attcap2`, `run_t4`, `run_t5`, `run_t6`, `run_t7` |
| 267 | `run_t8`, `run_t9` |

**閉じた query:** 全 ref のこの driver（改名前の名前を含む・`git log --all --follow`）は **18 commit**。
その全部で `m = cell.compile()` の行番号を測ると **{200, 204, 220, 224, 239, 256, 257, 260, 262, 267}**。
⇒ ⛔ **258 と 266 はどの commit にも存在しません。**

⇒ ⭐⭐ **13 本のうち 9 本（t3, t4, t5, t6, t7, reg_A, reg_B, reg_C, attcap2）は、git のどの commit にも無い driver で走っています。**
⇒ この 9 本については「producing commit で読む」ができません。producing code は復元できません。
⇒ 残り 4 本のうち `t8`/`t9` の 267 は `d16c877ecd`（= `823ddf963e` の内容・on-disk sha256 `f06862863b74efcf71d8589210f2c9a2b14d3f9515d116c45075c287e45b5707` と一致）と**矛盾しません**。

**射程（この主張が言えること／言えないこと）:**
- ⭐ **言える（否定側は堅い）**: 258/266 の 9 本は、列挙した 18 commit のどれでもない。閉じた query＋陽性対照（18 版すべてで grep が 1 件ヒット。0 件なら見落としを意味する）。
- ⛔ **言えない（肯定側は弱い）**: 行番号一致は必要条件で十分条件ではない。`t8`/`t9` を「`d16c877ecd` と同一の code で走った」とは言えません。

⇒ ⛔ **13 本を横に並べて「再現した／しない」と論じることは、固定した code での比較になっていません。**

---

## 2. ① 整定ゲートの到達状況（DDR #49 軸）

DDR #49（`00-DESIGN-STATUS-LEDGER.md:144` @ `29ab7d3847`）の逐語基準は
`r6_positive_pair_result.txt:37` 「`[pos] settle gate: NOT REACHED in 20 s -- numbers below are from moving arms (tolerance 2.0 mrad)`」。**公差 2.0 mrad**。

### 2-1. run 側の整定印字は **STEP4 の 1 箇所だけ**

印字形 = `STEP4: arms settled to X mrad at t=3.24s into the step -- fingers may close`

| run | X | 行 |
|---|---|---|
| t3 | **0.00** | `run_t3.txt:56` |
| t4 | **0.00** | `run_t4.txt:58` |
| t6 | ⭐ **1.20** | `run_t6.txt:56` |
| t7 | **0.00** | `run_t7.txt:58` |
| t8 | **0.00** | `run_t8.txt:58` |
| t1, t2, t5, t9, reg_A/B/C, attcap2 | **印字なし** | — |

⇒ **完走 5 本は STEP4 では公差 2.0 内**（t6 のみ残差 1.20 mrad で非零）。
⇒ ⛔ **STEP13/14 の再把持相には整定ゲートの印字が在りません** ⇒ その相の到達／未到達は **log から言えません**。

### 2-2. より細かい計器 — 各 GRASP / REGRASP block の servo 到達判定

印字形 = `joints vs commanded [6 値] mrad -> servo arrived | did not arrive`。route run 7 本で **26 block**。

| run | GRASP L | GRASP R | REGRASP L | REGRASP R |
|---|---|---|---|---|
| t3 / t4 / t7 | arrived (≤0.3) | arrived (≤0.8) | arrived (≤0.1) | arrived (≤0.1) |
| t6 | arrived (≤0.3) | arrived (≤0.7) | arrived (≤0.1) | arrived (≤0.1) |
| t8 | arrived (≤0.3) | arrived (≤0.8) | arrived (≤0.0) | ⛔ **did not arrive** — 関節 2 が **−1728.4 mrad** |
| t5 | arrived (≤0.0) | ⛔ **did not arrive** — **−229.1 / −378.8 / −789.1** mrad | arrived (≤0.2) | arrived (≤0.0) |
| t9 | ⛔ **did not arrive** — **+10.9** mrad | ⛔ **did not arrive** — **+9.4** mrad | （相に到達せず） | （同左） |

⇒ ⭐ **26 block 中 4 block が未到達。公差 2.0 mrad に対し 5 倍〜864 倍。**
⇒ ⭐ **DDR #49 の帰結により、この 4 block と同じ block に印字された全数値は「動いている腕」で測られています**（t9 の GRASP L/R、t5 の GRASP R、t8 の REGRASP R）。

**⚠ この計器の射程（重要）:**
- 検査対象は **腕の 6 関節のみ**。⛔ **指（グリッパ）の整定は検査していません。**
- 実例: `t5` の GRASP L は `servo arrived` ですが、同 block の `pad faces +79.89`・`pad separation 93.3`・接触なし = **手は全開**（§3-1 の表）。⇒ 「servo arrived」は「掴めている」を意味しません。

---

## 3. ② GRASP / REGRASP の再現性 — p4 主張の独立再導出

⛔ **p4 の値は写していません。** 13 本の blob を自分で grep して並べました。

### 3-1. p4 主張「t3/t4/t6/t7/t8 で +16.23 / +6.80 同値」の照合

| run | GRASP L 背板間 | GRASP R 背板間 | REGRASP L | REGRASP R |
|---|---|---|---|---|
| t3 | **+6.80** | **+16.23** | +6.69 | +3.79 |
| t4 | **+6.80** | **+16.23** | +6.69 | +3.79 |
| t6 | **+6.80** | ⛔ **+16.27** | ⭐ +6.88 | +3.79 |
| t7 | **+6.80** | **+16.23** | +6.69 | +3.79 |
| t8 | **+6.80** | **+16.23** | ⭐ +6.59 | +3.79 |
| t5 | +79.89 | +79.89 | +3.81 | +3.79 |
| t9 | +79.89 | +79.89 | （なし） | （なし） |

⇒ ⭐ **p4 主張は 10 leg 中 9 leg 正、1 leg 誤**:
- `+6.80`（GRASP L）= **5/5 一致** ✅
- `+16.23`（GRASP R）= **4/5**。⛔ **t6 は +16.27**（`run_t6.txt:69`）。
⇒ ⭐ **p18 の spot-check「t6 のみ +16.27」は、私の独立測定と一致します。**

⇒ ⛔ **REGRASP は「同値」ではありません**: L 側は 6.59〜6.88（幅 0.29 mm）。p4 の依頼文は REGRASP に触れていませんが、「同値」を REGRASP まで広げると偽になります。

### 3-2. ⭐⭐⭐ 数値の一致が何を意味しているか — 最重要

`REGRASP R = +3.79 mm` は **到達した 6 本すべて（t3, t4, t5, t6, t7, t8）で同一**です。
同じ 6 本の同じ block の他の印字:

| run | clamped | 触れているもの | 最近ケーブルリンクまで | 背板間隔 |
|---|---|---|---|---|
| t3 | **False** | pad1 none / claws none / pad2-only none | 43.7 mm | 19.2 mm |
| t4 | **False** | 同上 | 43.7 mm | 19.2 mm |
| t5 | **False** | 同上 | **121.5 mm** | 19.2 mm |
| t6 | **False** | 同上 | 42.8 mm | 19.2 mm |
| t7 | **False** | 同上 | 43.7 mm | 19.2 mm |
| t8 | **False** | 同上 | ⛔ **1102.3 mm** | 19.2 mm |

⇒ ⭐⭐⭐ **ケーブルが 43 mm の run でも 1102 mm の run でも同じ +3.79 が出ます。**
⇒ ⛔ **+3.79 はケーブルを測っていません。右ジョーが空中で閉じ切ったときの値です。**
⇒ ⛔ **したがって「REGRASP R の値が全 run で再現した」は、再把持の再現性の証拠になりません。**逆に、**どの run でも右ジョーが何にも触れずに閉じた**という証拠です。

同型の点が GRASP R にもあります:
- `+16.23` / `+16.27` の 5 本すべてで **`clamped=False`・`pad1 none`**（接触は claws のみ、`run_t3.txt:68` 他）。
- ⇒ ⛔ **右手はどの run でも背板で掴んでいません。**ケーブルは爪先の外側部に当たっているだけです。

掴めているのは **左手だけ**です:
- GRASP L `+6.80` は 5 本すべてで `clamped=True`・`pad1 ['L','R']`・`claws ['L','R']`（`run_t3.txt:62` 他）。
- 本 driver の `clamped` は **接触だけでなく 2–8 mm の帯も要求**します（同行の括弧書き逐語:「needs both pads AND a 2-8 mm face gap; touch alone passed on a jaw that had closed through the cable」）⇒ 以前の `grip=` と違い、この述語は判別できています。

### 3-3. reg_A / reg_B / reg_C

| variant | 質量 | joint range | 出力の差 |
|---|---|---|---|
| A | 1.1243 g/link | None | 基準 |
| B | 4.0000 g/link | None | ⭐ 差が出た: ncon 13→10、drop 2.3→10.9 mm、背板間 6.80→7.24 / 6.77→7.37 |
| C | 1.1243 g/link | **(-1.2, 1.2)** | ⛔ **variant 宣言行（`:1`）以外、全行が byte 同一** |

⇒ ⭐ **B が差を出しているので、計器自体は差を検出できます（陽性対照）。**
⇒ ⛔ **C は、入力を変えたのに出力が 1 文字も動いていません。**読みは 2 つあり、**log では判別できません**:
1. ±1.2 rad（±68.8°）はこの姿勢では効かない（＝妥当な null 結果）
2. range が model に適用されていない
⇒ **判別法（低コスト）:** 各リンク関節角の最大 |値| を印字する／確実に効く狭い range（例 ±0.05 rad）で 1 本走らせて出力が動くか見る。
⚠ 参考: banked driver（`ur15_steps_wired.py:170-174`）は `CABLE_JOINT_RANGE is None` のとき属性を出さず、非 None なら `range="…"` を出します。ただし **reg_C を走らせた版（:258）は git に無い**ので、この記述を reg_C の producing code の記述として使えません。

---

## 4. ③ WORST sigma_min 表

| run | WORST L sigma_min | 位置 | WORST R sigma_min | 位置 | WORST L 列との隙間 | WORST R 列との隙間 |
|---|---|---|---|---|---|---|
| t3 | 0.0381 | STEP4 t=11.2s | 0.0015 | STEP13 t=28.9s | +0.0 mm (STEP2 t=0.1s) | +0.0 mm (STEP3 t=2.5s) |
| t4 | 0.0381 | STEP4 t=11.2s | 0.0015 | STEP13 t=28.9s | +0.0 mm | +0.0 mm |
| t6 | ⛔ **0.0000** | STEP4 t=8.3s | 0.0024 | STEP13 t=28.9s | +0.0 mm | +0.0 mm (t=2.8s) |
| t7 | 0.0381 | STEP4 t=11.2s | 0.0015 | STEP13 t=28.9s | +0.0 mm | +0.0 mm |
| t8 | 0.0381 | STEP4 t=11.2s | **0.0037** | STEP13 t=28.7s | +0.0 mm | ⛔ **−25.8 mm ← INSIDE THE COLUMN** (STEP13 t=29.1s) |
| t1,t2,t5,t9,reg_A/B/C,attcap2 | **WORST 行なし** | | | | | |

出典: `run_t3.txt:227-230` / `run_t4.txt:229-232` / `run_t6.txt:227-230` / `run_t7.txt:259-262` / `run_t8.txt:254-257`。

⭐ **p4 の 3 つの申告はすべて実在**（0.0381 / t6 L 0.0000 / t8 R 0.0037）。
⛔ **ただし 0.0381 の「再現」は 4 本ではありません** — t3 / t4 / t7 は同一の走行です（§6-1）⇒ **独立な出現は 2 件**（{t3,t4,t7} と t8）。
⛔ **p4 の依頼文は t8 の R 0.0037 を挙げていますが、同じ run の列貫通 −25.8 mm を挙げていません。**（`run_t8.txt:257`。この行は log 自身が `<- INSIDE THE COLUMN` と印字しています。）

t8 の同時刻の他の印字（`run_t8.txt:177-184`）:
- `STEP13 column gap L= +206.5 R= −0.6 mm`
- `STEP13 ARM REACH: R 290.3 mm below the mouth`
- `STEP13 CARRY: R mouth[+0.510 −0.804 +0.360]` ← **y = −0.804 m**（ケーブル・クリップは y ≈ +0.28〜+0.42）
- `STEP13 右がcable再把持へ … R=1281.5mm`

---

## 5. ④ t1 / t2 / t5 / t9 の終了原因

| run | 到達した最後の相 | log に記録された終了 |
|---|---|---|
| **t1** | STEP 2 | ⛔ `NameError: name 'CLIP_RISER' is not defined`（`ur15_steps_wired.py:1483`、`run_t1.txt:41`） |
| **t2** | STEP1 R | ⛔ **記録なし**。最終行 = `release opening solved from the asset`（`run_t2.txt:33`）。traceback なし・gates 行なし・動画 write 行なし |
| **t5** | STEP16 の狙い直し | ⛔ `RuntimeError: no IK solution for R at [0.61003537 0.47908947 0.24770231]`（`solve_ik` `:1031`、呼び出し `:1430`） |
| **t9** | STEP 8 の狙い直し | ⛔ `RuntimeError: no IK solution for L at [-3.50333798 -8.29085505 20.59916309]`（`solve_ik` `:1044`、呼び出し `:1453`） |

⭐⭐ **t5 と t9 は「IK 解なし」で同じに見えますが、別の壊れ方です。**

**t5 — 物理の発散が先行:**
1. `run_t5.txt:192` **`WARNING: Nan, Inf or huge value in QACC at DOF 31. The simulation is unstable. Time = 48.3408.`**
2. 直後の STEP15 で `c1[y+0.280 z+0.149] c2[y+0.280 z+0.150]` = **初期の settle 値へ復帰**、`pin=C1/--` → `pin=--/--` へ戻る（`run_t5.txt:201`。STEP14 は `pin=C1/--`）
3. STEP16 の狙い直しが `mouth->cable [-526.0 -79.1 +606.6] mm` を作る（`run_t5.txt:203`）
4. → `RuntimeError`
⇒ ⭐ **「IK 解なし」は末端症状で、根は QACC の発散です。**
⚠ **別件（発散のはるか前）**: t5 は **STEP 3 の時点で既に R tool err 823.5 mm**（`run_t5.txt:55`）。右腕はケーブルに一度も届いていません。

**t9 — ケーブルが飛んでいる:**
1. `STEP 7 C1へ押し込み … R= 790.9mm c1[y+9.089 z-19.849]`（`run_t9.txt:113`）= **横 9 m・下 20 m**
2. STEP 8 の狙いが `mouth->cable [3609.4 8640.8 -19752.1] mm`（`run_t9.txt:114`）
3. → 目標 `[-3.503, -8.291, +20.599]` m へ IK → `RuntimeError`
⇒ ⭐ **目標が 20 m 上空。到達性の話ではありません。**⛔ **この行を「腕が届かない」の根拠に使えません。**
⚠ t9 は GRASP L / R とも `servo did not arrive`（+10.9 / +9.4 mrad）かつ `pad faces +79.89` = 全開。

**⚠ t2 について:** 「外部から止められた」とは **言えません**。log に在るのは「途中で出力が終わっている」だけで、原因は log から決まりません。

---

## 6. ⑤ gates 行の全数 と、完走 5 本の同一性

### 6-1. gates 行 = **5 本のみ・全て False**

| log:行 | 内容 |
|---|---|
| `run_t3.txt:231` | `gates: {'grasp': False, 'regrasp': False}` |
| `run_t4.txt:233` | 同上 |
| `run_t6.txt:231` | 同上 |
| `run_t7.txt:263` | 同上 |
| `run_t8.txt:258` | 同上 |

⇒ ⭐ **13 本中 8 本には gates 行が在りません。**在る 5 本は **全て `grasp: False` かつ `regrasp: False`**。

### 6-2. ⭐⭐ 完走 5 本は **別々の 3 つの結果**です

| 比較 | 差分の全部 |
|---|---|
| **t3 対 t4** | ①driver 行番号 258→266 ②計器 2 行の追加（`measured pinch->mouth drop` / `Tier A cross-check`）③動画名とサイズ。**数値行は全数一致** |
| **t4 対 t7** | ①driver 行番号（同 266）②`arm in contact with the cable` の印字 **30 行**の追加 ③動画名。**数値行は全数一致** |
| **t7 対 t8** | 170 行目まで完全一致。最初の差は STEP13 の再狙い |

**動画（私が sha256 を実測）:**

| file | bytes | sha256 |
|---|---|---|
| `~/Downloads/ur15_wired_t3.mp4` | 36,394,754 | `50e4e06506dbc95db8ef82a2471430853be4ddcd8644b4375b9f7f2bdb833249` |
| `~/Downloads/ur15_wired_t4.mp4` | 18,863,599 | ⭐ `8235d726bdc56e5de308fb4c1595dfa2c519750830a746dc09659c4b755e5880` |
| `~/Downloads/ur15_wired_t6.mp4` | 20,251,307 | `7d9a5318258365f527626b67182e631372bd6a4ae3e35360b77792a5f36761eb` |
| `~/Downloads/ur15_wired_t7.mp4` | 18,863,599 | ⭐ `8235d726bdc56e5de308fb4c1595dfa2c519750830a746dc09659c4b755e5880` |
| `~/Downloads/ur15_wired_t8.mp4` | 17,705,449 | `e74e0ee87477ac4c56f53930738bdb45ffab02153214e13523b80cca92f7ebff` |

⇒ ⭐ **t4 と t7 の動画は byte 同一。p18 の申告を独立に確認しました。**全 5 本 `frames=1182`。
⇒ ⭐ **log 差分（234 対 264 行）の性質 = 追加された接触印字 30 行のみ。**印字を足しても物理は 1 bit も動いていません（動画が byte 同一）。
⇒ ⭐ **t3 は数値が t4 と全数一致なのに動画だけ別**（36.4 MB 対 18.9 MB・同 1182 frame）⇒ 差は符号化側であって走行側ではありません。

⇒ ⭐⭐⭐ **したがって完走 5 本の独立な結果は 3 つ:** `{t3 ≡ t4 ≡ t7}` / `{t6}` / `{t8}`。
⛔ **t3・t4・t7 を 3 件の裏づけとして数えると、1 回の走行を 3 重に数えることになります。**

### 6-3. t6 と t8 が分岐した位置（log に見える範囲）

**t4 → t6 の最初の差**（`run_t4.txt:46-47` が t6 に無い）:
```
[steps] STEP3 L: standoff re-aim (y,z only), seat error  2.31 mm
[steps] STEP3 R: standoff re-aim (y,z only), seat error  5.91 mm
```
⇒ **t6 には STEP3 の狙い直しが在りません。**以後の全数値がずれます。
⇒ ⭐ t6 の特徴（整定残差 1.20 mrad・WORST L sigma_min **0.0000**・GRASP R +16.27）は、すべてこの下流です。

**t7 → t8 の最初の差**（`run_t7.txt:171,173-174` 対 `run_t8.txt:171,173-174`）:
| | t7 | t8 |
|---|---|---|
| STEP13 R 再狙いの seat error | 16.50 mm | 13.69 mm |
| z available | **1.00 mm** | **2.00 mm** |
| margin | −16.39（DOES NOT CLEAR） | −13.58（DOES NOT CLEAR） |

⇒ 両者は **170 行目まで完全一致**。ここから t8 の右腕が y=−0.804 側へ振れ、列と −0.6 mm、mouth から 290.3 mm 下、tool err 1281.5 mm、REGRASP R の関節 2 が指令と 1728.4 mrad 違い、という経過になります。
⛔ **因果は主張しません。**log に見える差分（`available 1.00 → 2.00`）は挙げましたが、log に出ない driver 変更を排除していません。

---

## 7. 参考 — クリップ貫入の印字（依頼外・完走 5 本のみ）

`PENETRATION: cab{N} is X mm INSIDE C{1,2} C{k}` の非 clear 行:

| run | 件数 / 全 PENETRATION 行 | 最大 |
|---|---|---|
| t3 | 5 / 17 | 1.8 mm (STEP15, cab26, C2_1) |
| t4 | 5 / 17 | 1.8 mm |
| t6 | 4 / 17 | ⭐ **2.4 mm** (STEP15, cab27, C2_1) |
| t7 | 5 / 17 | 1.8 mm |
| t8 | 7 / 17 | 1.1 mm (STEP 8, cab30, C1_2) |
| t5 | 2 / 14 | — |
| t9 | 0 / 6 | — |

⛔ **印字を写しただけです。**接触の物理的妥当性は判定していません。

---

## 8. ⛔ 私が主張しないこと

1. **視覚判定をしません。**動画は sha256 を取っただけで、中身を見ていません。物理妥当性 = pC + Rs。
2. **numeric 単独 PASS を出しません。**本書に PASS/FAIL の verdict は在りません。
3. **driver の行番号は同一性の証明ではありません**（§1 の射程）。否定側（258/266 は commit に無い）のみ堅い主張です。
4. **reg_C の 2 読みを判別していません**（§3-3）。判別法だけ示しました。
5. **t7 → t8 の因果を主張しません**（§6-3）。
6. **t2 の終了原因を推定しません**（§5）。
7. **本書は「log がそう印字している」までです。**印字が実体を正しく測っているかは、§3-2 で示したとおり自明ではありません。

---
**pB LOG-ANALYST measurement / 2026-07-28 12:34 JST**
