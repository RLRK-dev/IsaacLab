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

## 5. 権限の明示（形式の受理 ≠ 行為許可）

- 本 file は **測定と回答**であり、**p0 の gate を私が反転させるものではない**。gate の運用は p18 の routing / chain の順序に従う。
- ⛔ 役割割当が未解決（§0）のため、**もし本 pane が p5 court でないと Rs が裁定した場合、本 file は verdict でなく材料として残る** — 測定はそのまま有効で、court が採否を決める。⭐ どちらに転んでも **chain がもう一晩止まる理由にはならない**。
- ⛔ 本 file が変えないもの: HOLD（run なし）／spec §6-6 fence ／DoD の evidence-grade cap ／#48 = Rs court ／chain 順序（p0 実装 → pZ 検証 → まとめ）。
