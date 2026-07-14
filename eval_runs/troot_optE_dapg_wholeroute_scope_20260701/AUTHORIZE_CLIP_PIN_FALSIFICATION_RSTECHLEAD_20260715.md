# `authorize_clip_pin()` — 設計の反証（実装前 [VERIFY] ゲート）

**著者:** RS-TECH-LEAD (%12, w2:p4) — 2026-07-15 06:3x JST
**宛先:** VT-DESIGN (p5, 設計主) / cc: OPS-SUP (p1), PLAN-KEEPER (p6)
**対象:** `RLENV_PIN_DESIGN_VTDESIGN_20260715.md` §12（`authorize_clip_pin` 仕様）
**結論:** ⛔ **仕様どおりには出荷できない。要件①と②が built model 上で矛盾する。** 実装は停止。設計裁定を p5 に差し戻す。

**方法:** 敵対的パネル 2 体（1 体は `NewtonRouteEnv` と producer の両シーンを**実構築して実測**）＋ %12 による全決定的主張の on-disk 再検証。**agent の結論は narrative として扱い、採用したものは全て自分で確かめた**（1 件は反証して棄却した、§5）。

---

## §1 ⛔ 決定的：要件①と②は built model 上で【矛盾する】

**§12 の要件:**
1. 全 clip の捕捉体積を **built model から導出**（定数を使わない）
2. `seat_world` が**どれかの clip** の捕捉体積の中でなければ RAISE

**⛔ built model には、経路 clip と幾何的に区別不能な V 溝 clip が【あと 4 つ】ある。**

| 事実 | cite |
|---|---|
| support clip は経路 clip と**同一の 5 箱リテラル** | `newton_skill_env_base.py:1822-1828`（`clip_parts`）＝ `:1848-1854`（`_v_groove_clip_parts`） |
| 位置 = `x = GRASP_X = 0.300`、`y ∈ {−0.100, +0.050, +0.300, +0.450}`（逐語コメント「cover full cable Y range」） | `:1829-1834` |
| **route env で既定 ON** | `newton_route_env.py:701` `add_support_clips=not self._g1_scene_align`（`_g1_scene_align` 既定 False） |
| float も spacer も無い ⇒ **z 帯が違うだけ** | `:1833` `TABLE_HEIGHT + dz` |

**実測（%12、`task_config` から算出、agent の実構築測定と一致）:**

| clip | base top | wall top | **捕捉体積 z** |
|---|---|---|---|
| **経路 C1**（float +20mm） | 825.0 | 840.0 | **(821.0, 836.0) mm** ← gate の実測 bar と一致 ✅ |
| **support clip ×4**（float 無し） | 805.0 | 820.0 | ⛔ **(801.0, 816.0) mm** |

⇒ ⛔⛔ **model からしか読まない authorizer は、`(x=300mm, y=+50mm, z=801〜816mm)` への溶接を【認可する】。**
⇒ **区別できる唯一の情報は `CLIP_POSITIONS`＝定数**（`task_config.py`）。**要件①がそれを禁じている。**
⇒ **Rs の認可（`route_executor.py:718` 逐語「その他は絶対禁止」）は「経路 clip での clip-retention pin」であって「シーン中のあらゆる V 溝」ではない。**

### §1.1 ⭐ そして陽性対照は、この穴に【構造的に盲目】
§10 / §12 の陽性対照は **z しか動かさない**（880.9 / 816 / 829.68 / 830.0）。**(x, y) を一度も動かさない。**
⇒ **support clip の穴は (x, y) にある** ⇒ **対照表は自分が開けた穴を検出できない。**
⇒ ⭐ **これは p1 が独立に指摘した「陽性対照が z 軸だけ」と【同じ形】** — 2 者が別経路で同じ穴を見つけた。
⇒ ⭐ **さらに、今夜見つけた歴史的欠陥とも同じ形**（空中溶接 audit の method = `seated := |z−829| ≤ 3` = **高さのみ** ⇒ 58 本すべて高さ失敗として記録された）。

---

## §2 ⛔ 決定的：`assert sum(eq_active) <= n_clips` は【正しい pin で発火する】

**実測（%12、on-disk）:**
- producer は **6 本の構造 eq を、全て `enabled=True` で**建てる:
  - 4× four-bar CONNECT（`newton_skill_env_base.py:1647` `enabled=True`）
  - 2× follower-mirror JOINT（`:1669` `enabled=True`）
- 逐語: `test_newton_clip_routing.py:1628` `_want_neq = 6 + _perclip_pin_n` / `:1631` 「want … = **4 connect + 2 follower-mirror** + N perclip-pins」

⇒ `sum(eq_active)` = **pin 前 6 / pin 後 7**
⇒ `assert sum(eq_active) <= n_clips` ⇒ **`7 <= 5` は偽** ⇒ ⛔ **golden path で raise する。**

⇒ **eq の index 空間は clip ではない。cable body（40 本、1 body に 1 本）＋ gripper の構造 eq である**（`newton_skill_env_base.py:1595-1603`）。
⇒ 欲しい不変条件は **pin 候補のみに対するもの**（`eq_type==CONNECT ∧ eq_obj2id==0 ∧ eq_active0==0` — この filter は既に `route_executor.py:774` に在る）。

---

## §3 ⛔ 決定的：C2〜C5 の geom は【存在しない】。空集合は loud に落ちない

**実測（敵対的 agent が `NewtonRouteEnv(route_c2_scene=True)` と producer の両方を実構築 → selector と bar 式を逐語再現）:**

| selector 中心 | geom 数 | z_lo | z_hi | lat | y-win |
|---|---|---|---|---|---|
| **C1 built (0.350, +0.150)** | **5-6** | 821.0 | 836.0 | 3.50 | 15.0 |
| **C2 built (0.400, +0.000)** | **6** | 821.0 | 836.0 | 3.50 | 15.0 |
| task_config C2 (0.400, **+0.075**) | ⛔ **0** | −4.0 | ⛔ **8,999,999,996.0** | −4.0 | 0.0 |
| task_config C3 (0.350, 0.000) | ⛔ **0** | −4.0 | **9e9** | −4.0 | 0.0 |
| task_config C4 (0.400, −0.075) | ⛔ **0** | −4.0 | **9e9** | −4.0 | 0.0 |
| task_config C5 (0.350, −0.150) | ⛔ **0** | −4.0 | **9e9** | −4.0 | 0.0 |

⇒ ⛔ **canonical な 5 clip 中心のうち 4 つが【空集合】を選ぶ。**
⇒ ⛔ **建っている「C2」は `ROUTE_C2_XY = (0.40, 0.000)`（`route_env_config.py:140` 逐語「!= task_config (0.40, 0.075)」）= canonical C2 ではない。**
⇒ ⛔⛔ **空集合は raise しない。`default=0.0` / `9e9` の fallback（`route_executor.py:3031-3071`）が【完全な形をしたゴミ bar】を返し、gate は `seated=False | z -4.0<829.0<9000000000.0mm` と印字する ⇒ 読み手には「clip が無い」ではなく「着座していない」と読める。**
⇒ ⭐ **本番 selector には、その解析用双子が【必須と考えている guard】が無い**: `p1b_c1_replay_video.py:118-130` は geom 数が違えば `BROKEN SELECTOR` で **raise する**。`_clip_geoms()` には**個数 assert も z 床も無い**。

⇒ **5-clip 一般化は、今日の model では【構築も検定もできない】。**

---

## §4 ⚠ 重大：gate の clip 中心は【幾何ですらない】

`route_executor.py:2133-2134` 逐語:
```python
x_clip = os.environ.get("CLIP_X", "0.40")
y_clip = os.environ.get("CLIP_Y", "0.0")
```
一方、シーン builder の C1 既定は **(0.35, +0.150)**。

⇒ ⛔ **env 未設定だと「C1 seat gate」は黙って route env の【C2】を中心に据える** — bar は完全に正常に見える値（6 geom / 821 / 836 / 3.50 / 15.0）を返しながら、`dx`/`dy` は**別の clip に対して**測られる ⇒ gate 恒久 False ⇒ **pin が静かに一生発火しない。**
⇒ これは今夜踏んだ **`--solver-backend` 既定トラップ**と同じ族（**既定値が黙って別のシーンを選ぶ**）。

---

## §5 ✅ agent の主張 1 件を【反証】して棄却した（記録）

**agent R4:「床 bar `z_lo = floor_top − CABLE_RADIUS` は符号ミス。床に載った cable の中心は `floor_top + r` = 829mm なのに、bar は 821mm = 座面の 8mm 下」**

⛔ **棄却。** p5 §10 が**意図して**そう設計している（逐語）:
> 「**下側 821 = cable の上端が溝床面より上**（= **clip の【下】に居ない**）⇒ **貫入の余裕が 3mm → 8mm**（実測貫入 1.541mm、剛性 **16×** 差 env 2500 / producer 40000 ⇒ 柔らかい env で下側 826 は踏み得る）」
> 「**821 で切る ⇒ 816 は REJECT（余裕 5mm）、貫入した静置 827.5 は PASS（余裕 6.5mm）**」

⇒ bar の目的は「**cable が clip の下に居ない**」であって「**cable が床に接している**」ではない。**agent は設計が持たない意図で採点した。**
⚠ ただし agent の **R5/R6 は残る**: 床 bar の**コメント**（`:3052-3054`「route env では spacer が無く 20mm 浮くので cable が下を通れる」）は、**gate が実際に走るシーンでは偽**（producer は `SPACER=1` で隙間 0.00mm、route env の C1 は**テーブルの穴の上**）。**guard は無害だが、その正当化は間違っている。**

---

## §6 ⚠ p1 の構造的論拠も【空だった】（p1 に通知済）

p1（%12 が受諾・bank 済）: 「4 bar は built model 由来の**幾何量**であって宣言値ではない ⇒ 5-clip 一般化は構成上正しい」

⛔ **論拠は空**（agent の実測）: **codebase には clip 形状が 1 つしかない**（同じ 5 箱リテラルが 3 箇所に複製 — `newton_skill_env_base.py:1848-1854` / `:1822-1828` / `test_newton_clip_routing.py:1169-1175`）。bar は **そのリテラル + `CLIP_FLOAT_Z` + `CABLE_RADIUS` の代数関数**で、**per-clip の自由度がゼロ**。
⇒ **どの clip も byte 同一の bar を返す**（実測表、§3）⇒ **実行時読み取りは per-clip 情報を 1 ビットも運んでいない。**
⇒ **結論（全 clip 同形 ⇒ 一つの bar で足りる）は生きるが、論拠（per-clip に適応する）は偽。**
⇒ ⚠ そして §3 の failure mode（空集合 → ゴミ bar）は、**リテラルなら存在しなかった**。

---

## §7 🔒 p5 への差し戻し（設計裁定を要求。%12 は自前導出しない）

**§12 が【2 つの別物】を混同している、というのが %12 の読み（p5 の裁定を仰ぐ）:**

| 何を | どこから来るべきか | 理由 |
|---|---|---|
| **bar**（捕捉体積の *大きさ*） | ✅ **built model**（幾何） | 溝の寸法は幾何の事実。§12 の要件①はここでは正しい。 |
| **集合**（*どの* clip に打ってよいか） | ⛔ **model からは読めない。task の認可** = `CLIP_POSITIONS` | 「この V 溝は *経路* clip か *支持* clip か」は**幾何の事実ではなく task の事実**。**model は知り得ない。** |

**⇒ %12 の提案（p5 裁定待ち・実装しない）:**
1. `authorize_clip_pin` は **認可された clip 中心の集合を引数で受け取る**（`CLIP_POSITIONS` 由来）。bar は各中心の周りで **model から** 導く。
2. **selector に個数 assert を入れる**（解析双子 `p1b_c1_replay_video.py:118-130` と同じ）— **空集合は「未着座」ではなく `BROKEN SELECTOR` として raise。**
3. **assert 5 を「pin 候補のみ」に直す**（`eq_type==CONNECT ∧ eq_obj2id==0 ∧ eq_active0==0`、filter は `route_executor.py:774` に既存）。**`sum(eq_active) <= n_clips` は golden で発火する。**
4. **assert 4（`mjm.neq` 不変）は恒真**（mid-episode に recompile する経路が無い）⇒ 削除するか、**実際の bypass を突く assert に置換**。
5. **陽性対照を (x, y, z) 3 軸に**。**必須の 1 本 = `(x=300, y=+50, z=810)`（support clip の中）⇒ REJECT であること。**
6. **5-clip 一般化は【延期】** — C2〜C5 の geom が存在しない。今日書ける authorizer は **C1 と built C2 の 2 つまで**。5-clip は **model 側の作業が先**。

**⛔ %12 は実装を停止し、p5 の裁定を待つ。** 設計は p5 専権（Rs 2026-07-14「VT-DESIGN にきけよ」）。

---

## §8 ✅ 本反証で【壊れなかった】もの（実装可能な部分）

1. **§12 の §2 撤回は正しい**（eq は cable body ごとに事前割当、anchor は実行時に書かれる ⇒ **機構は任意の body を任意の点へ溶接できる**）。**診断は正しい。**
2. **書込点の統合それ自体は独立に価値がある** — 実際に **3 つの別述語に drift している**（`route_executor.py:665-670`（テスト専用）/ `:3074-3078`（出荷版）/ `policy_route_runner.py:309`（**接触レグと ±3mm 窓が生きたまま**））。
3. ⛔ **そして §12 が触れていない残存欠陥**: `policy_route_runner.py:309` の π-rollout path は、**p5 が殺した接触レグ（0.5mm）と ±3mm 窓を今も使っている** ⇒ **0.679mm 浮きの偽陰性は refactor 後も生き残る。**
4. ⛔ **同じ 2 定数が C2 の成功判定を支配している**（`route_executor.py:3881` / `test:5540` / `policy_route_runner.py:1089` → `SETTLED_IN_NOTCH`）⇒ **route の banked C2 成功数は、設計が「不適」と宣言した述語で測られている** — しかも overhang が違う clip で。**p5 はこれを受け入れるか撤回するかを裁定する必要がある。**

---

*根拠 file:line は本文中。反証に使った agent の実構築測定スクリプトは scratchpad（repo 非汚染）。%12 は全決定的主張を on-disk で再検証し、1 件（R4）を反証して棄却した。*
