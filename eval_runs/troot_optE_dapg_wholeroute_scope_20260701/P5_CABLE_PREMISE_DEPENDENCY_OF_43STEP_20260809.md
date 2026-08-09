# 43-step 工程は cable 前提に依存するか — m-p18-210 の p5 宛て質問への回答

pane: **`w2:p5`**（本日実測。経緯 = `P5_C2_PROCESS_TABLE_CONSISTENCY_LEG_20260809.md` §0）/ 起票 **2026-08-09 09:58 JST** / bank 前に **m-p18-211（pZ の 2 build 発見）を受けて改稿**（未 bank ゆえ挿入でなく書き直し・本行が記録）
問い（逐語） = 「**p5: say whether the 43-step sequence depends on the premise, and if so what.**」
⛔ 本 file は **実読と回答のみ**。spec を編集しない・新文言を draft しない・run しない。⭐ 引用は**行の文字列**で示す（行番号は動く — 本 message 群で 3 面から stale pointer が出ている）。

---

## 1. 回答 = **依存する。文言でなく、工程の成功条件そのものが依存している。**

clip 固定 STEP の成功条件はいずれも **「側方 seated」= 横向きの着座**で、しかも **clip ごとに Y が違う**（`CANONICAL_MOTION_TABLE_V1.md`・逐語）:

| STEP | 逐語（表本文） |
|---|---|
| 9 | 「body30 が C1 groove 壁内に**側方 seated** & 保持(**Y+0.150**)、C1 独立保持 — z<840 でない」 |
| 16 | 「body25 が C2 groove **側方 seated**(**Y+0.075**)AND body30 が C1 STILL seated」 |
| 24 | 「body20 が C3 groove **側方 seated**(**Y0.000**)AND C1,C2 STILL retained」 |

⇒ Y が clip ごとに動く配索 = spec `:69` が「the 5-clip 千鳥 X-Y curvature」と名指すもの。前提はそれを「**would need a 2nd bend DOF/joint**」＝無い、ゆえに「**Horizontal routing through the staggered clips is therefore KINEMATIC**」と結論している。⇒ **43-step の配索はこの結論の上に立っている。**

## 2. ⭐ ただし「前提が偽」ではない — **build が 2 つある**（pZ 発見を採用し、私の面で確かめた）

pZ の実測（p18 再測・私は再走していない）= 前提が引く `test_newton_clip_routing.py::add_revolute_cable` は **joint 軸が 1 本だけ**。⇒ **前提は、自分が引いている build については真**。

**私の実測（本 leg の面 = 43-step が実際に走る driver）**:
- ⭐ **live driver は自前の cable builder を持つ**: `ur15_steps_wired.py:225 def cable_xml()`（⛔ `ur15_cell` を import していない = 参照 0・positive control 2/2）
- その中身 `:238-239` 逐語: `<joint name="cab{i}_y" type="hinge" axis="0 1 0" …/>` ＋ `<joint name="cab{i}_z" type="hinge" axis="0 0 1" …/>`（damping/stiffness は `_spec` 経由 = `ur15_cell_spec.py`）
- `cable_xml` を定義する **6 driver 全部**が両方の蝶番を建てる（`ur15_cell` / `ur15_route` / `ur15_steps` / `ur15_steps_wired` / `ur15_steps_c1seat` / `ur15_steps_reaim` = 各 1 行 × ループ）
- `ur15_cell.py` の関数 docstring 逐語: 「**Chain of capsules; two hinges per link so it bends in both directions but does not twist.**」／`CABLE_N = 40` ⇒ **inter-segment joint 39**（前提の「39」と**一致**）

⇒ ⭐⭐ **数（39）は合っていて、joint あたりの DOF（1 対 2）と軸が合っていない。**⭐ **前提の軸「single revolute about local-X→world-X」は、チェーンが X 方向に並ぶので *ねじれ* 軸** — builder が「**does not twist**」と明示的に除いた唯一の軸。
⚠ **境界（私が答えていないこと）**: 本測定が答えるのは「**43-step の scripted route が建てるケーブル**」のみ。**RL / Newton の routing env がどちらの constructor を選ぶか**（pZ の open = `test_newton_clip_routing.py:1386-1391` の分岐・`add_cable_rod` 未読）は **私も未測**。⛔ 混ぜない。

## 3. 前提が変わると 43-step の何が変わるか（p6 の (b)(c)(d)）

**(b) 水平配索の説明が「kinematic だから」から「物理で出る」へ。** ⭐ **段の並びは変わらない**（段は「押込→固定→解放→上昇」で DOF を前提にしていない）— 変わるのは**なぜその形が保てるかの説明**。

**(c) ⛔ 二面の突き合わせであって、文言ではない。**（私自身で両面を実読して確認した）
- **LEDGER `:63` 逐語**: 「AR reached 92.2% (Gate G3 PASS) but its **mechanism (spring-follow + kinematic hold)** is **fidelity-QUARANTINED**」⇒ 原因 = **機構**
- **spec `:31` 逐語**: 「the same banked sim2real fidelity limitation that already explains the AR-routing QUARANTINE (§4 `:62`, B1 substrate-upgrade DECLINED)」／**spec `:69`** も「**EXPLAINS the AR routing fidelity-QUARANTINE**」⇒ 原因 = **1-DOF 境界**
- ⇒ **同じ quarantine に、面ごとに別の原因が書いてある。** 前提を書き換えると **spec 側の原因は消え、LEDGER 側の原因は残る。**
- **私の面での帰結（43-step 側・§2 の測定に条件付き）**: 保持の述語が**非保守側**になる。表は既に自分の穴を書いている — 「`all_c1_retained_lowwall`(:4959)= **z のみ** … **側方ゼロ、z-low でも sideways escape 可**」「`bodies_in_groove`(:2694)= … **Z-check gate のみ使用、C1-retention verdict に不使用**、count-in-radius ≠ both-wall capture」。⇒ **2 本目の DOF が在る面では、横逃げは生きた物理モード**であり、**z だけの述語は「保持」と言いながら横から出ていても通る**。⚠ **これは推論でなく等級の問題**: z のみの述語に寄りかかった過去の PASS は、**その面の cell が満たしていない仮定の下で採点されている**。
- ⚠ **pZ の読みと矛盾しない**: pZ が「routing env は今も 1-DOF ゆえ (c) は *消える* のでなく *否定される* 危険」と言うのは **Newton 側の面**。私の上記は **43-step mujoco 面**。⛔ **どちらの面の話かを言わずに (c) を一文で書くと、必ずどちらかで偽になる。**

**(d) pin は同じ文で正当化されている。** premise 逐語に「the AUTHORIZED clip-retention pin, §2」。⚠ 併せて表 §2 に **D-6 が登録済**（逐語要旨「**pin(STEP 9)が 解放(STEP 8)より先に発火 ⇒ 表の順序 7→8→9 が逆転**」「**pin 時点で cable を保持しているのは【グリッパ】であって【溝】ではない**」・**未裁定**）⇒ drafter は (d) を白紙から始めない。

## 4. drafter が heading に着地しないための site 一覧（`RS71-System-Spec-SSOT.md`・91 行・`1-DOF` 3 hit・positive control 1/1）

| site | 中身 | 扱い |
|---|---|---|
| `:29` | 前提の再掲 ＋「**routing through the staggered clips is therefore KINEMATIC**」／pointer「§4 `:62`」 | ⛔ **ここも前提を述べる** — `:69` だけ直すと旧前提が残る |
| `:31` | quarantine の原因を前提に帰す文／pointer「§4 `:62`」 | ⛔ (c) の spec 側の根拠は**ここ** |
| `:69` | FIDELITY BOUNDARY 本体 | 本体 |
| `:74` | 「faithful **1-DOF** coupling (REQUIRED, unlanded)」 | ⛔ **別の物 = 指の coupling**（human-FROZEN）。巻き込まない |

⚠ **pointer 実測（私自身）**: 「§4 `:62`」は **`:29` と `:31` の 2 箇所**に在り、**`:62` は `TABLE_HEIGHT = 0.80` の bullet**。前提は `:69`。⇒ **drafter が最初に開く文書が、変更対象の文について 2 回とも違う行を指している。**

## 5. 等級と境界

- **実測（私自身）** = §1 の 3 STEP 逐語／§2 の driver 実読と 6 driver 比較（positive control つき）／§3(c) の LEDGER `:63` と spec `:31`/`:69` の両面／§3(d) の pin 言及と D-6 の存在／§4 の site 数と pointer ずれ。
- **他卓の測定を採用（再走していないと明記）** = pZ の「`add_revolute_cable` は 1 軸」＝ 前提は自分の build について真。
- **未測** = RL / Newton routing env がどちらの constructor を選ぶか（`add_cable_rod` 未読）。
- ⛔ **私がしないこと**: spec 編集／新文言 draft／(a)(c) の owner 就任（私の commission は m-p18-209 の工程表レグ）／run。⭐ ただし **§2 は (a) の材料としてそのまま使える**（43-step 面に限る、と書いた上で）。
- ⚠ **#48 の cap 据置**: Rs が新文言を **land** するまで cable 由来の主張に無印 PASS を出さない。
