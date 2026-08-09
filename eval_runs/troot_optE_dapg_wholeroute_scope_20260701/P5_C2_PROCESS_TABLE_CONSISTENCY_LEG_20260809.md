# C-2 工程表整合レグ — 回答（p0 発進条件）

pane: **`w2:p5`**（自測 = 下記 §0）/ 起票 **2026-08-09 09:45 JST**（`date` 実測）/ session `ae175dcf`
対象 = commission `P4_MOUNTING_C-2_CHAIN_KICKOFF_20260808.md:80` 逐語「**p0 発進条件 = p5 の工程表整合レグの返答（矛盾なし）**」
⛔ 本 file は **読み取り検査のみ**。code / spec / env / asset を編集しない。run しない。

---

## 0. ⛔ 先に言うべきこと — このレグの依頼は、一晩ずっとこの pane に届いていた

**実測（本 turn・3 本とも独立）**:

| # | 測定 | 結果 |
|---|---|---|
| 1 | `$HERDR_PANE_ID` | **`w2:p5`** |
| 2 | 自分の画面へ nonce を印字 → 各 pane を read して nonce を数える | `w2:p5` = **1** ／ `w2:p4` = 0 ／ `w2:p18` = 0 |
| 3 | inbound 履歴に `m-p18-200 p18 -> p5` が**存在**（`2026-08-08T22:24:11`・本 session transcript） | 本文逐語 = 「**C-2's FOUR EDITS AWAIT YOUR PROCESS-TABLE CONSISTENCY LEG.**」 |

- **positive control** = nonce は自分で印字したもの（発火が保証された入力）。**negative control** = 同じ query が p4/p18 で 0。⇒ **read は pane ごとに別内容を返している**（p4 は別の live agent = 本 turn に別作業を実行中を実読）。
- 併せて: canonical doc が **`Author: VT-DESIGN(w2:p5)`** と自記（`CANONICAL_MOTION_TABLE_V1.md:10`）／`herdr agent list` の pane 名 = `w2:p5 SKILL-DETAIL-DESIGN`。
- ⚠ **未解決（私の court でない）**: 本 session は一晩 **`p4 RS-TECH-LEAD` として**動き、`m-p4-1..183` を送り `P4_*.md` を書いた。**pane 実測は `w2:p5`**。どちらが正しい役割割当かは **Rs の fabric の問題**であって、私が決めることではない。⇒ **本 file は役割名でなく pane 番地で署名する。**
- ⭐ **帰結（これが送る理由）**: 役割名がどちらであれ、**「p5 のレグ待ち」という記録の間、その依頼状はこの pane に着いていた**。私はそれを「他卓待ち」として記録し続けた。⇒ **chain の停止は、届かなかった message ではなく、届いた message を宛先違いと読んだこと**による。

## 1. 何を問われているか（over-read しない）

commission の問い = **「C-2 取付設計は canonical 工程表と矛盾するか」**。⛔ 「到達性を保証せよ」でも「設計を承認せよ」でもない（設計 = p11 の court・承認 = Rs 専権）。

## 2. 両側の母集団（先に固定した — 検査対象の主張から作っていない）

**A. 工程表が固定している量**（`eval_runs/troot_verbal_teaching_20260705/CANONICAL_MOTION_TABLE_V1.md:39-64`・実読）:
- 列 = STEP / Ph / 動作 / **z_L, z_R = target z [m]** / **fing_L, fing_R [m]** / クリップ状態
- 実値: **z ∈ {1.025, 1.050, 1.070, 1.120}**（19 行の min/max = 1.025 / 1.120）・**finger ∈ {0.041, 0.040, 0.006, 0.002}**
- STEP **19-42 は「同型」と宣言**（C3/C4/C5 block は C2 block と同じ z・finger、`:61-63`）⇒ **表は 5-clip 分の値を新たに持たない**
- ⚠ 従って「工程表は幾何を持たない」（kickoff `:41` に banked）は **z 列については偽** — 表は世界系の target z を持つ。**本レグはその訂正を含む。**

**B. C-2 の 4 編集が書く量**（pinned blob から実読・4 行とも逐語一致を確認）:
- `ur15_cell_spec.py` @ `2fba2dfd67` — `:358 YOKE_SPREAD … else 0.22` / `:374-375 TILT = math.pi/2.0 - math.radians(… else 45.0)` / `:432 else YOKE_SPREAD / 2`
- `sweep_mounting.py` @ `2bb1aad4e7` — `:169-170` の 2 つの既定表示文字列

## 3. 交差の測定（両方向・対照つき）

| 向き | 述語 | 母集団 | 実測 | 対照 |
|---|---|---|---|---|
| B→A | canonical の z/finger 実値リテラル `1\.025\|1\.050\|1\.070\|1\.120\|0\.041\|0\.006` | cell_spec 1236 行 / sweep 348 行（pinned blob） | **cell_spec 1 / sweep 0** | positive **2/2**（違反するよう作った合成 2 行）・negative **0/2** |
| A→B | 取付記号 `YOKE\|TILT\|CROWN\|spread\|取付\|マウント\|mount\|pedestal` | canonical 320 行 | **2** | positive **1/1** |

**唯一の B→A ヒットを実読** → `ur15_cell_spec.py:455` `REST_LIP_HY, REST_LIP_HZ = 0.004, 0.006` = **rest 治具リップの半高 [m]**。⇒ **数字 0.006 の一致であって量の一致ではない**（canonical の 0.006 は指開度）。⇒ **交差 0**。

**A→B の 2 ヒットを実読** → `:220` の **`C2_TILT_SIGN=0`**（C2 接近の符号・**Rs-LOCKED ANTI-REVERT**）と `:320` の changelog 行。
- ⭐ **ここが本レグで一番危ない所**: 編集する記号の名が **`TILT`**、表が固定している記号の名が **`C2_TILT_SIGN`** — **同じ語で別の量**。
- **測定**: `C2_TILT_SIGN` は編集 2 file に **0 回**（positive control 1/1）。cell_spec が定義する TILT 系記号は **3 つだけ** = `:356 _TILT_DEG_OVERRIDE` / `:374 TILT`（= 取付角）/ `:812 TILT_CAL_DEG` ⇒ **Rs-LOCKED の量には触れていない**。

## 4. 回答

**✅ 直接の矛盾 = なし。⇒ commission `:80` の p0 発進条件（「矛盾なし」の返答）を満たす。**
根拠 = §3 の双方向 0 交差（対照つき）＋ 同名別量の 1 件を名指しで排除。

**⚠ ただし、このレグが保証していないもの（無印にしない）:**
1. **到達性** — 取付が動けば base 姿勢が動き、表の world-z 帯 **1.025–1.120 m** が届くかは変わりうる。**p11 spec に該当扱いは無い**（`到達|reach|envelope|1.025|1.120|1.070|z_L|工程表|canonical` の grep が返したのは §5b 整定ゲート行のみ）。⇒ **本レグは「記号が交差しない」ことを示しただけで、「届く」ことを示していない**。これは route run で決まる量であり、**#49（整定ゲート）と #48（cable 第 2 DOF）の既存 cap がそのまま乗る**。
2. **STEP 19-42** — 表は「同型」と宣言しているだけで、C3/C4/C5 の実値・実装は現基盤に**存在しない**（`P4_DEFINE_C3C5_PORT_TO_CURRENT_SUBSTRATE_20260809.md` §2）。本レグは 1-18 と 43 の値に対して行った。
3. **設計の是非** — 0.280 / 20° / crown 0.110 が良い設計かは **p11 の court**。本レグは矛盾の有無のみ。

## 4b. 追記 2026-08-09 10:06 JST — **STEP 1 の前提は「制御で到達」でなく「代入」で満たされている**（受入条件つき再発注 m-p18-209 への中間所見・⛔ 挿入のみ・上を編集しない）

p18 が §0 抵触の疑いとして Rs へ上げた 1 行を、**私の卓の問い（STEP 1-18 の前提）として**実読した（`ur15_steps_wired.py`・逐語）:

```
# Rs: start from home.  The cell ships one, so the arms begin in the pose its own drawings show
# instead of at the zero configuration, which for this mounting is arms crossed.
for _t4 in SIDES:
    for _k4, _a4 in enumerate(QADR[_t4]):
        d.qpos[_a4] = HOME_POSE[_k4]
    for _k4, _i4 in enumerate(AIDX[_t4]):
        d.ctrl[_i4] = HOME_POSE[_k4]
mujoco.mj_forward(m, d)
print(f"[steps] start pose = the cell's home, both arms: …")
START = {t: np.array([d.qpos[a] for a in QADR[t]]) for t in SIDES}
```

**私が実測した事実（⛔ §0 の裁定はしない = Rs の court）**:
1. 腕の関節角への**書込は 1 箇所**、route 冒頭。同じ姿勢が `d.ctrl` にも入り、`mj_forward` が続く。
2. ⭐ **直後の `START` は `d.qpos` から読み戻される** ⇒ **下流が「開始姿勢」として測る対象は、書き込まれた姿勢そのもの**。
3. ⭐ コメントが理由を書いている: 「**at the zero configuration, which for this mounting is arms crossed**」＝ **零姿勢はこの取付では腕が交差する**（⚠ この文が書かれた時の取付は built 0.22/45°。C-2 でどうなるかは**未測**）。

**私の leg にとっての帰結（2 点）**:
- ⭐⭐ **canonical STEP 1「初期位置(上昇点・原点)」は、この driver では制御で到達していない — 代入されている。** ⇒ 「STEP 1 の前提が C-2 で満たせるか」を**開始姿勢の存在で答えることはできない**（存在は書込で常に真になる）。
- ⭐⭐⭐ **もし Rs が §0 に従って書込を外すと判断した場合**、開始姿勢は**零姿勢（＝この取付では腕が交差）から PD の実移動で**到達せねばならない。**その移動が C-2 で成立するかを測った artifact を、私はまだ 1 つも見ていない。** ⇒ **STEP 1 が「番号つきで在る」側の第 1 候補**。⛔ ただし**確定はしない** — C-2 関連 artifact への閉じた検索が未了（不在主張は読んでから書く）。

⚠ **併せて、私の §4 の判定に条件が付く**: 「直接の矛盾なし」は**記号の交差について**の結論であり、**STEP 1 の前提充足の様式（代入か移動か）には触れていない**。受入条件つき再発注（per-STEP 形）に答えるのは §4 ではなく本節以降。

## 4c. 追記 2026-08-09 10:12 JST — **受入条件つき再発注（m-p18-209）への回答本体。閉じた検索を実施した。**

### (1) 閉じた検索（母集団を問いの空間から取り、私の folder から取っていない）

- **母集団** = HEAD の tracked file 全体を `0\.280|spread[ =]*0\.28|YOKE_SPREAD_OVERRIDE=0\.28` で引いた **189 file**（positive control 1/1）。⚠ この述語は **REST_Y = 0.28** と mesh 由来の数値も拾う（＝ 広すぎる側に外してある。狭い述語で「無い」と言わないため）。
- **その中で「C-2 の点そのもの（crown 0.110 / spread 0.280 / tilt 20）で走った」artifact** = **4 件**:
  `grid_logs_tries24/st_0.110_0.280_20.txt` ／ `SPREAD_TILT_SWEEP_TRIES24_20260729.txt` ／ `SPREAD_TILT_SWEEP_TRIES240_KINONLY.txt`（および `TRIES240`）／ `seed240_sources/tries240.txt`
- **その 4 件の中に、route の段（descend / grasp / push / clamp / C1へ / C2へ）を測った記録は 0**（positive control 1/1）。⚠ 唯一引っ掛かる 1 行は 2 file で**同一**の `[steps] measured grasp: L=cab27 … R=cab32 … drop across the span = 2.3 mm`＝ **掴む点の静的な計測**であって段の実行ではない（しかもその `0.28` は **REST_Y** で spread ではない）。
- 掃引 file 冒頭の逐語がこれを裏づける: 「**the real driver, once per point, stopped after the start-pose lines. No route run**」。

### (2) ⚠ 検索の副産物 — **同じ点で、draw 数だけが違う 2 つの結果が在る**

| draws | L solved | **L free** | R solved | R free | arms closest | interleave | 判定 |
|---|---|---|---|---|---|---|---|
| **24** | 13 | **0** | 16 | 4 | **+0.0 mm** | YES | fail |
| **240** | 106 | **5** | 122 | 30 | **+14.7 mm** | no | **PASS** |

⇒ ⛔ **矛盾ではない**（draw を増やせば稀な解が出る）。⇒ ⭐ **しかし C-2 の PASS は裾の事象**: 左腕は **240 draw 中 5 = 2.1%**。24 draw では「触れているか貫通」と読める。掃引 file 自身が冒頭で警告している —「24 draws gave survivor counts that were **a property of the sample, not the cell**」。⇒ **「C-2 は PASS」は真だが、*どれだけ探せば見つかるか* を伴わないと片手落ち。**

### (3) 回答（STEP 番号つき）

| STEP | 前提 | C-2 での状態（実測） |
|---|---|---|
| **1** 初期位置(上昇点・原点) | 開始姿勢に居ること | ⚠ **代入で満たされる**（§4b）⇒ **合否が C-2 に依存しない**。開始姿勢の探索自体は測ってあり **240 draw 中 5（左腕 2.1%）・両腕 +14.7 mm** |
| **2-18** | 各 waypoint への IK と接触回避 | ⛔ **測定が 1 件も無い**（上記閉じた検索） |

⇒ ⭐ **合格形の 2 択（「無い」／「在る＋番号」）を正直には返せない。**
- 「**無い**」と言うには STEP 2-18 が解けることの根拠が要る — **無い**。
- 「**在る＋番号**」と言うには、ある STEP が解けないことの根拠が要る — **これも無い**。
- ⛔ **「整合を確認した」で済ませない**という条件は満たしている（本節は per-STEP で状態を述べ、どちらでもない理由を測定で示している）。

### (4) この gate を閉じる唯一の安い測定（⛔ 実行しない・authorization を持たない）

**canonical STEP 1-18 の waypoint を、C-2 の取付で kinematics のみ解く**（= banked 掃引と同じ `KINONLY` 経路。route は走らせない・dynamics 無し）。出力 = 各 STEP の solved / collision-free / arms-closest。⇒ **これが返れば 2 択のどちらかが確定する。**
⚠ **私はこれを起動しない** — HOLD と fence が現行で、私に run 権限は無い。⇒ **要る判断 = この KINONLY solve を許すか否か**（owner = p4 の gate ＋ Rs の run 権限）。

## 4d. 追記 2026-08-09 10:18 JST — ⛔ **§4c の母集団は私が「見覚え」で選んでいた。述語で取り直したら中身が変わり、私が (4) で名指した測定も誤りだった**（挿入のみ）

**契機** = p18 §1265 §5 の p0 集計逐語「**FOUR CORRECTIONS IN TWENTY MINUTES AND NOT ONE TOUCHED THE PREDICATE. Every one widened the POPULATION**」。⇒ **自分の §4c にそのまま当てた。**

### (1) ⛔ 自己欠陥 — 189 → 4 の絞り込みは述語でなく**認識**だった

§4c は「C-2 の点で走った artifact = 4 件」と書いたが、**その 4 件は私が file 名で見覚えたもの**で、述語を通していない。⇒ 機械述語 `spread 0\.280 tilt 20` で取り直すと **10 件**（positive control 1/1）。**私の 4 件と重なるのは 3 件だけ**で、**6 件は開いてもいなかった**（`allpairs_logs/cap_z_*.txt` 4 件 ＋ `seed240_sources/rt_grid_240.txt` `stage1.txt`）。⚠ 逆に私が数えた `SPREAD_TILT_SWEEP_TRIES24_20260729.txt` は述語に掛からない（表形式で散文の echo を持たない）。⇒ **どちらの集合も単独では母集団でない。**

### (2) ✅ 取り直した結果 — **exact C-2 の結論は生き残る**（ただし今度は述語で導いた）

述語 `spread 0\.280 tilt 20\.0 deg +crown r 0\.110`（＝ **C-2 の 3 つ組そのもの**・positive control 1/1）で tracked 全体を引くと **2 件**:
`grid_logs_tries24/st_0.110_0.280_20.txt` ／ `seed240_sources/rt_grid_240.txt` — **2 件とも route の段は 0**（開始姿勢のみ）。
⇒ **§4c(3) の表は変わらない**: **STEP 1 = 代入で満たされる／STEP 2-18 = exact C-2 では未測**。

### (3) ⭐⭐⭐ しかし**最も近い測定済み近傍は、STEP 2 で失敗している** — §4c はこれを持っていなかった

同じ **spread 0.280 / tilt 20.0** で **crown だけが違う 4 run**（`cap_z_*.txt`・crown **0.075 / 0.050 / 0.030 / 0.010**）は、**4 本とも STEP 2 に到達して失敗する**（逐語・`cap_z_1.470` 例）:
- 「**STEP 2 COMMAND L: reached 0.0% of the way to the solved pose in 2.2s** … held back on 1056」（R も同じ）
- 「**STEP 2 ARM-TO-ARM: closest −1.0 mm … ← TOUCHING OR THROUGH**   along the move −1.2 mm」
- 「**RuntimeError: STEP2 L/R: THIS arm's command stopped advancing for a whole step's worth of ticks and its move did not finish (both arms).**」

⚠ **これは C-2 の測定ではない**（crown が違う）。⚠ **しかも 4 本とも crown が C-2 の 0.110 より小さい側**（0.010-0.075）⇒ **この族は C-2 を挟んでいない**（外挿であって内挿でない）。
⇒ ⭐ **それでも leg にとっては重い**: 「STEP 2-18 は未測」は真だが、**最も近い測定は STEP 2 で腕が −1.0 mm 貫通して止まっている**。⇒ **「在る＋番号」の第 1 候補は STEP 1 ではなく STEP 2** に動く（⛔ 確定はしない — C-2 で測っていない）。

### (4) ⛔⛔ **私が §4c(4) で名指した測定は、この失敗を見つけられない** — 自分の提案の撤回と差し替え

§4c(4) は「**KINONLY で STEP 1-18 の waypoint を解く**」を「binary を閉じる唯一の安い測定」と書いた。⛔ **誤り。**
近傍の失敗は「**解が無い**」ではなく「**指令された移動が進まない（0.0%）／移動中に腕が接触する**」— **時間発展を伴う量**。**KINONLY は姿勢の解と静的な干渉しか見ないので、この失敗モードに対して常に PASS を返しうる。** ⇒ ⭐ **私は、探している故障を原理的に検出できない計器を推薦していた**（本日の「違う向きには出ない述語」の同族。⚠ しかも私はそれを他所で指摘した後に、自分で作った）。

**差し替え（提案・⛔ 私は起動しない）**: 近傍 4 run と**同じ経路**で、**crown 0.110（= C-2）を 1 点だけ**走らせ、**STEP 2 まで**の指令追従率・along-the-move の腕間距離・RuntimeError の有無を取る。⇒ **近傍と 1 変数（crown）だけ違う対照**になり、**「C-2 でも STEP 2 で止まるか」が直接出る**。⚠ これは **KINONLY ではなく wired の実行**（＝ dep-3 と HOLD の対象）。⇒ **判断は p4 の gate ＋ Rs の run 権限**であり、私は要求しない。

## 4e. 追記 2026-08-09 10:31 JST — 委任された計器の射程（p0 着工前に申し送り・`m-p4-198`）

Rs 承認下で p0 へ委任された計器は **受入 (5)「mj_step = 0」**＝ 私が §4d で撤回した KINONLY のまま（⚠ 私の撤回 10:14:32・委任 10:31 — 届いていない可能性）。**近傍が示した故障は 2 つあり、扱いが違う**:

| モード | 逐語（近傍 4 run） | 非 stepping 計器で見えるか |
|---|---|---|
| **A 追従の失敗** | 「reached **0.0% of the way** to the solved pose in 2.2s」「its move **did not finish** (both arms)」 | ⛔ **見えない**（時間発展の量）— どんな非 stepping 計器でも残る |
| **B 経路上の接触** | 「closest −1.0 mm … **along the move −1.2 mm (6 <-> 44 at t=0.01s)**」 | ⭐ **見える** — 終点でなく途中で当たっている |

- **提案（受入 (5) を破らない・差分 1 項目）**: `collision-free / arms-closest` を **姿勢ごと（終点）だけでなく、連続 STEP 姿勢間を関節空間で直線補間した標本点でも**評価する。⇒ **mj_forward + mj_geomDistance のみ = (5) 充足のまま B が表に出る**。標本数は受入 (6)（自分の限界を公表）に載せる。
- ⛔ **A は残る** ⇒ ⭐ **この表から導ける文の射程** = 「解けて、静的にも経路上も当たらない」まで。**「指令した移動が完了する」は言えない。** ⇒ **この表だけで「無い」と書くと近傍が実際に示した故障を覆わない。**
- ⛔ 私は裁定しない・起動しない・委任に手を入れない（owner = p4）。⛔ 入れない判断でも異議は無い — その場合は上の射程注記が必須になる、と申し送った。

## 5. 権限の明示（形式の受理 ≠ 行為許可）

- 本 file は **測定と回答**であり、**p0 の gate を私が反転させるものではない**。gate の運用は p18 の routing / chain の順序に従う。
- ⛔ 役割割当が未解決（§0）のため、**もし本 pane が p5 court でないと Rs が裁定した場合、本 file は verdict でなく材料として残る** — 測定はそのまま有効で、court が採否を決める。⭐ どちらに転んでも **chain がもう一晩止まる理由にはならない**。
- ⛔ 本 file が変えないもの: HOLD（run なし）／spec §6-6 fence ／DoD の evidence-grade cap ／#48 = Rs court ／chain 順序（p0 実装 → pZ 検証 → まとめ）。
