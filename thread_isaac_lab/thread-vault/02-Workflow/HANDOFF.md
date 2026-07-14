
# RS-TECH-LEAD handoff — 2026-07-15 03:5x JST

## 🔺 次セッションで実行 (Rs 指示 03:5x「つぎのセッションでそれらを実行する」)

### 1. ⭐ `authorize_clip_pin()` の実装 — L3 / 4 ファイル / **本丸**

⭐⭐ **Rs の 2 つの指示は同じ機構** (p5 発見):
- 「**ピンが打たれる前に本当に溝に居るかを確かめる**」(07-14 17:18)
- 「**クリップ *のみ* pin を RL env に恒久配線しろ**」(07-15 00:5x)
⇒ どちらも「**seat_world が clip の捕捉体積の中にあることを、溶接の前提条件として強制する**」⇒ **1 本の関数で両方 discharge**。

**現状 (on-disk 確認済 / p5 の Q2「構成で保証」は撤回された)**:
- eq は **clip ごとでなく cable body ごと**に事前割当 (`newton_skill_env_base.py:1596`)
- **eq を書く箇所が 4 つ** (`route_executor.py:792` / `:3138` / `policy_route_runner.py:328` / `test_newton_clip_routing.py:4796`) ⇒ **絞り口なし**
- ⇒ ⛔ **機構は任意の body を任意の世界点へ溶接できる。58/486 の空中溶接は、機構が *許した* もの。**

**仕様** (p5 `RLENV_PIN_DESIGN_VTDESIGN_20260715.md` §12):
```
authorize_clip_pin(mjm, mjd, seat_body, seat_world) -> eq_id
 (1) 全 clip の捕捉体積を built model から導出
 (2) seat_world がどの clip の捕捉体積にも入らなければ RAISE
     述語 = dy_in_clip ∧ inside_left ∧ inside_right ∧ 821 < z < 836  (§10)
 (3) repo 内で eq_data/eq_active を書く【唯一の関数】 ⇒ ⭐ grep が【テスト】になる
 (4) mjm.neq がエピソード中 不変を assert
 (5) 活性化後 sum(eq_active) <= n_clips を assert
```
**positive control (必須・絶対世界座標)**: 空中 880.9 ⇒ RAISE / clip の下 816 ⇒ RAISE / 捕捉体積内 829.68 ⇒ eq_id / ⭐ **grep test: `eq_data[` と `eq_active[` の書込箇所が 1 であること**

### 2. RL env への pin 配線 (Rs 承認済・クリップのみ)
- 割当 ladder = **p5 §4** (⚠ §8 ではない): **C1:33 · C2:26 · C3:19 · C4:12 · C5:5 = 7-segment stride**
- ⛔ **最近傍割当を使うな** (千鳥の弦 90.14mm に 5seg=75mm では届かない)
- ⚠ RL env は現在 **cable の eq がゼロ** (B3-α)

### 3. U-1 差替 (p5 §13) = 測定 1 本
joint limit は **存在しない** (`add_joint_revolute` に limit なし / passive spring のみ / `springref=0.0`) ⇒ 21.2°/joint は曲がれる。
⚠ **問いが変わった**: 「曲がるか」(YES) でなく「**どれだけの力が要り、その力が経路を歪めないか**」。
⭐ `springref=0` ⇒ 経路に通した cable は **バネで、pin に曲げられたまま永久に押し返す** ⇒ **pin は恒久荷重を負い、荷重は pin 本数とともに増える**。
🔒 **各 pin の eq 拘束力 (`efc_force` / `qfrc_constraint`) を測れ。本数とともに増えるなら cable は経路と戦っている。**

### 4. 報酬の 3 欠陥 (**訓練前に必須**、reward 設計ゲート = p5 + `/reward-design`)
1. `c1_retained` が **X を一度も読まない** (`newton_route_env.py:1491-1495`)
2. offline `strict_v2` の lateral 判定 `pin_ok` (`p9_recount_strict_v2.py:79-80`) が **verdict に未配線**
3. ⭐ **G3 の bar 3mm < `|dy|` 量子化床 7.32mm** ⇒ latch が抽選 (実測 24/81) ⇒ **現時点で到達不能 = campaign blocker**

### 5. BC 教師の録り直し (dataset meta 逐語「**6 demo(s) poorly seated at pin**」)

---

## ✅ 確立したこと

### Rs 逐語 (一次事実)
- **pin あり動画**: 「ケーブルが C1 の溝に入っているし C1 の底にもついているから見た目上は ok。C2 への誘導、押し込みもできている」
- ⭐ **B-0a (pin なし・同一 cell・同一 build)**: 「**とまっていない、溝にはきちんとハマっている、底についたようだが完全には底についていないかもしれない**」
- **裁定**: 「クリップ*のみ* pin を RL env に恒久配線しろ」「全 env を記録するよう recorder を直せ」「メッセージは必要なことだけ簡潔にかけ」

### ⇒ 3 つの観察が全て機構として説明された (Rs の目・pB の数値・p5 の設計が一致)
| Rs の言葉 | 機構 |
|---|---|
| **溝にきちんとハマっている** | 半径方向 form-close (−Z・±X) ⇒ z 829±1 / 壁天端超え 0 / 横逃げ 0 |
| **とまっていない** | ⭐ **軸方向 (±Y) は設計どおり開いている** (＝しごき) ⇒ C2 側へ 1.7〜10mm/s、減速せず、**終端で溝は空** (pC 視覚 + 数値一致) ⇒ **pin の仕事は ±Y を閉じること** |
| **完全には底についていない** | ⭐ **アーチ** (clip は 30mm メサの上 ⇒ 垂れた両端が中央を持ち上げる片持ち) ⇒ 着座 body は **0.679mm 浮き** / 隣は接触 −0.011mm。**手は反証済** (pin ON 対照で R の上昇は同一なのに cable は上がらない) |

### 出荷したもの
- **seat gate** (両 producer = byte-repro 双子。`9c69776528` → `5b7afd5a9c` → `24390ebb69`)
  現行 **4 連言** = **821 < z < 836** (floor_top−R / wall_top−R、**built model 由来・datum なし**) ∧ **側方 |dx| ≤ 3.5mm** ∧ **定義域 |dy| ≤ 15mm**
  ⛔ **接触レグは削除** (正しく捕捉されたアーチを落とすため。浮きは clip ごとに違い単一 bar は不可能)
  `C1_SEAT_GATE=0` で **byte 一致**。検証: golden を通し **かつ byte 一致** (pure observer) / 空中溶接 cell を落とす
- **recorder が全 env を記録** (`b7553662a4`、19→60 key、**source から抽出**ゆえ自動追随)
- **RS71 §0 INVARIANT #5** に Rs 裁定を記録 (`4de2c9fd42`) + **ERRATUM 訂正** (`c5ae6ffdc5`)
- **CLAUDE.md §27** (通信規律、`4ca9d9007d`)

### 空中溶接は【歴史】
p3 の統制実験: 同一 env で **旧コード = z 880.9mm (banked と 0.1mm 一致) / 新コード = 829.2mm** ⇒ **差はコードのみ** ⇒ Rs 承認済の W0-e route fixes が既に直していた ⇒ **復旧 = BC 教師の録り直しのみ**。

### 5-clip は通せる (壁は 3 つとも潰れた)
① 平面性 ⇒ **root は 6-DOF 自由** (`test_newton_clip_routing.py:1000`) + 5 座面は厳密 coplanar ⇒ 水平平面なら 5 点を通れる
② 弧長 ⇒ **7-segment ladder で足りる** (p5 §4)
③ 関節限界 ⇒ **存在しない**
⇒ **p3 実測: 3-clip も 5-clip も残差 0.000mm** (`P5_PLANARITY_CLAIM_FALSIFICATION_COORD_20260715.md`)

---

## ⚠ 私の失敗 (繰り返さないために)

1. ⛔⛔ **artifact に無い数値 (「14.5%」) を FOUNDATIONAL INVARIANT に書いた** (p3 の message から取り on-disk 検証せず)。しかも **交絡した窓** (腕が牽引中) の数値 ⇒ p5 が STOP、訂正済。
2. **時刻の捏造 2 回** (`date` を叩かず頭で書いた / 2.5h の間隔を跨いで叩き直さなかった)。
3. **「ghost 第 2 波」= 誤報** (検出器の false-positive クラスを分母に入れていなかった)。真の ghost = **06:08-06:45 の 17 本のみ**。
4. **stale な行番号を自分の dispatch で全 pane に配布** ⇒ p6 が忠実に転記。
5. **裁定を 3 回撤回** (mutation test が発火しない実装を試験 / gate の legs の主語が違う / pin は放す前に打つほかない) — **3 回とも他 pane が捕捉**。
6. **revert が「撤回済みの誤前提」を地図に復活させた** (p6 捕捉) ⇒ ⭐ **「この commit は汚染前だ」は *時刻* の主張であって *内容* の主張ではない**。

---

## Standing

- ⭐ **CLAUDE.md §27 (新規)**: メッセージは 3 行 (何をしたか / 数値 + どこに在るか / 要るもの)。**詳細は artifact に書き path だけ送る。artifact に無い数値を送らない。他 pane の数値で裁定しない。**
- **設計は p5 に *聞く*。計画 surface は p6。** (Rs:「VT-DESIGN、PLAN-KEEPER が君のアンカー」)
- **Rs 専権 = 動画 human-GT。** 04-Specs / 07-Design は CC read-only (例外 = Rs の「かいて」)
- ⚠ **断面カメラは軸方向に盲目** (溝は Y 押し出し) ⇒ **軸方向の主張には top-down 必須** (pC)
- push は提案のみ (auto-push 禁止)。全 message 末尾に `date` 実測の JST。

Related: [[feedback-rs-video-gt-c1-seated-ok-2026-07-14]] [[feedback-human-gt-is-fetched-not-cited-2026-07-14]] [[feedback-design-ask-vt-design-never-self-derive-2026-07-14]]
