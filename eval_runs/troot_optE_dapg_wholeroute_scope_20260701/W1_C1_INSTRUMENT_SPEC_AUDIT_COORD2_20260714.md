# W1 — C1 収容計器 spec v0.2 · 走行前 audit

**Auditor: COORD2 (w2:p2)。2026-07-14 15:5x JST。**
**対象:** `W1_C1_CONTAINMENT_INSTRUMENT_SPEC_VTDESIGN_20260714.md` v0.2 (p5、mtime 15:45)。
**Verdict: ⛔ BLOCK — bank/build 前に CRIT 4 件を解消。うち 2 件は「計器が本来の判定を出せない」、1 件は「唯一の bank-gate 対照が実現不能」、1 件は「mutation test が計器の存在理由を削除する」。**
**GPU ゼロ / code 変更ゼロ。全指摘は source 定数からの機械算術で再現済 (§A)。**

---

## §0 先に — spec の *正しい* 部分 (builder はここに依拠してよい)

source で全数照合し、以下は **CONFIRM**:

| 節 | 主張 | 判定 |
|---|---|---|
| §1.1 | V 溝 = 5 箱 (`newton_skill_env_base.py:1848-1853`) | ✅ 逐語一致 |
| §1.2 | `_clip1g` は 6 箱 (spacer 混入)。`:1973` の comment「The 5 clip parts」は narrative | ✅ `_clip_geoms()` (`route_executor.py:1976-1983`) は geom **中心**で filter。spacer 中心 = (cx, cy) ⇒ XY gate を素通り |
| §1.3 | **籠は無い** | ✅ **機械検証**: リップ内面 ±11.0mm は 壁外面 ±10.5mm の **外**。内側への張り出し = **ゼロ** |
| §1.4 | z スタック (spacer 800-820 / base 820-825 / 壁 825-840 / 着座 829) | ✅ 4 境界すべて再現 |
| §2.0 | eq 拘束下の body は報告拒否 | ✅ 設計として健全 (機構として実装せよ、も正しい) |
| §2.1 | N→1 スカラー圧縮の禁止 | ✅ 正しい。旧計器の capture-blind の機構そのもの |

⭐ **§1.3 の「籠は無い」は本 arc で最も重要な幾何の訂正であり、正しい。以下の指摘はこれを覆さない。**

---

## ⛔ CRIT-1 — **`IN_CHANNEL` は、溝に *静止した* cable では原理的に成立しない**

### 事実 (spec 自身の 2 つの節が矛盾)

| 出所 | 値 |
|---|---|
| **§2.3 L3** | `z > base_top + r` ⇒ 閾値 = **829.0 mm** (厳密不等号) |
| **§1.4 (同じ spec)** | 「⭐ **着座 cable 中心** = **0.829**(= base 上端 + `CABLE_RADIUS`)」 |

⇒ **`IN_CHANNEL` の z 窓 = 開区間 (829.0, 836.0) mm。base plate に *載った* cable は、その窓の *排他的下限* に居る。**

⇒ ⛔⛔ **`IN_CHANNEL` を満たせるのは「溝の床に *触れていない* cable」だけ。**

### 帰結 (spec 自身の対照で発火)

| 対照 | 姿勢 | L3 | 判定 | spec の期待 |
|---|---|---|---|---|
| **PC-1** (§4.2、vacuity 否定用) | dx=0, **z=829** | **False** | ⛔ **`BELOW_BASE`** | ✅ `IN_CHANNEL` |
| 腕 A 溝進入 t=255 (実測) | \|dx\|=0.89mm, **z=827.6** | **False** | ⛔ **`BELOW_BASE`** | (in-groove のはず) |

⇒ ⛔ **spec 自身の positive control が、spec 自身の述語で落ちる。**

### なぜ致命か

§4.1 (FATAL-1) は **この失敗クラスを自ら名指しし、閉じたと宣言している**:

> 「⛔ **「常に FAIL する計器」と「PASS *できない* 壊れた計器」が弁別できない。**」

⇒ ⭐ **その 1 節あとで、同じ欠陥を述語に埋め込んでいる。** 本 arc の中心的失敗様式 (「自分で証明した罠に自分で落ちる」) の再演。

### ⛔ 「素直な修正」が **罠** である (CRIT-2 へ続く)

「食い込み分だけ L3 の bar を下げる」が自然な修正に見える。**それは、この arc が 3 回死んだ欠陥そのものである。** → CRIT-2。

---

## ⛔ CRIT-2 — **z の bar は 腕 D の treatment と交絡している** (bar が処置と共に動く)

### 事実 (source 逐語、`newton_skill_env_base.py:1875-1879`)

```python
_c1_match = os.environ.get("ROUTE_C1_STIFF_MATCH", "0") == "1"   # = 腕 D
clip_cfg.ke  = MUJOCO_CONTACT_KE if _c1_match else 2500.0        # 40000 vs 2500  = 16x
clip_cfg.kd  = MUJOCO_CONTACT_KD if _c1_match else 100.0         # 400   vs 100
clip_cfg.gap = 0.002 if _c1_match else 0.001                     # ⚠ 2 個目の変更パラメータ
```

- **接触の食い込み量 ∝ 1/ke。そして `ke` は *検定対象そのもの* である。**
- ⇒ **静止 z は ke の単調関数** ⇒ ⭐ **cable が溝に対して *幾何学的に完全に同一* の位置に在っても、腕 D の cable は 腕 A より *高く* 静止する。**
- ⇒ ⛔⛔ **食い込み帯の中に固定 z bar を置けば、L3 は「D は収容、A は非収容」を *接触の柔らかさだけ* から出力する。横方向の収容について情報ゼロで。**

### これは既知の死因である

| LOCK | 死因 | 誰が捕捉 |
|---|---|---|
| v2 → v3 | 判定帯 [0.6, 7.2]mm = **量子化の床そのもの** | %10 |
| v3 → v4 | producer 基準 4.20mm = **pin (eq) が保持した値** | p5 |
| **v0.2 (本件)** | **z bar = 接触剛性 (= 検定対象) の関数** | **%10 (本 audit)** |

⇒ ⭐⭐⭐ **同一クラス 3 度目: 「bar が treatment と一緒に動く」。**

### 🔒 帰結 (これが本 audit の中核勧告)

**z (L3 / L4) を 腕 A vs 腕 D の *verdict* に入れてはならない。**

- **verdict は `L1 ∧ L2` (横) に置く。** 溝は **Y 押し出し** ⇒ 脱出は横。`|dx|` は接触剛性に一次で非依存。**これは v3/v4 LOCK が既に確立した「主 = `|dx|`」と同一の結論である。**
- **L3 / L4 は *診断* として報告する (4-bit pattern はそのまま出す)。verdict の連言に入れない。**
- ⇒ ⛔ **v0.2 の `IN_CHANNEL := L1∧L2∧L3∧L4` は、z を verdict に *黙って再導入* している。**

### ⚠ 付随 (未解決、名指しが必要)

**腕 D の flag は接触パラメータを *2 個* 変える (`ke` と `gap`)。純粋な ke swap ではない。**
Newton の docstring 逐語: `gap` = 「Additional contact **detection** gap [m]. Broad phase uses (margin + gap) for AABB expansion and pair filtering.」⇒ **検出側であって力の offset ではない** ⇒ 私の初読 (「1mm の datum shift」) は **成立しない、撤回する**。
⚠ **ただし mjwarp 変換が Newton `gap` → MuJoCo `geom_gap` (力の *不感帯*) に落とす場合、z datum は treatment と共に動く。未確認。**
⇒ **(i) run の provenance に 2 パラメータ両方を明記せよ。(ii) z を verdict から外す理由がもう 1 つ増える。**

---

## ⛔ CRIT-3 — **DC-1 (唯一の bank-gate 対照) は幾何学的に実現不能、期待値も誤り**

§4.4-5 逐語: 「⛔⭐ **計器が DC-1 で旧計器と割れなければ、bank しない。建てる意味がない**」 ⇒ **DC-1 は load-bearing。**

### 事実 (source 逐語、`test_newton_clip_routing.py:1215` + comment `:1205`)

```python
_sp_idx = builder.add_shape_box(body=-1, xform=_sp_xf, hx=0.020, hy=0.015, hz=_clip_float_z/2.0, cfg=_sp_cfg)
#  comment 逐語: "Footprint = the clip base-plate (hx=0.020, hy=0.015 = +-20x+-15mm)"
```

| geom | x 範囲 | z 範囲 |
|---|---|---|
| **spacer** | **±20.0 mm** | [800.0, **820.0**] |
| **clip base plate** | **±20.0 mm** | [**820.0**, 825.0] |

⇒ ⭐⭐⭐ **spacer の上面は、base plate の下面に *100% 覆われている* (hx/hy 同一・z 連続)。露出した spacer 上面の面積 = 0。**

⇒ ⛔ **cable が spacer の *上に載る* ことは原理的に起きない。** 露出しているのは spacer の **側面 4 枚のみ** (x = ±20mm, z ∈ [800, 820])。

### DC-1 の姿勢は clip base plate の *内部*

spec の DC-1 = 「spacer 上の cable (合成: **\|dx\| < 20mm, z = 824**)」

- x ∈ ±20mm ∧ z = 824 ∈ [820, 825] ⇒ ⛔ **base plate という *中身の詰まった箱の内部*。**
- ⇒ §2.5 の per-geom 支持体帰属は、これを **base plate** (貫入、距離 < 0) に帰属させる ⇒ ⛔ **期待値 `ON_SPACER` は出ない。出るのは `BELOW_BASE` + support = base。**

### 🔒 救済 (DC-1 は *置き直せば* 成立する)

**DC-1 を spacer の *側面* に置く: `|dx| ≈ 24 mm` (= 20 + r), `z ∈ [804, 816]`。**
- そこでは旧計器の min-over-`_clip1g` が **本当に ~0 に落ちる** (riser 接触による偽着座) ⇒ **旧は「着座」と言う**。
- 新計器は **`ON_SPACER` + `LATERAL_OUT`** ⇒ ⭐ **新旧が割れる。しかも到達可能。**
- ⇒ **これが計器の存在理由であり、実在する姿勢である。**

---

## ⛔ CRIT-4 — **§4.3 の旗艦 mutation 行は型不整合。実行すると *spacer 除外 leg を殺す***

### 矛盾 (spec 内部)

| 節 | 逐語 |
|---|---|
| **§2.5** | 「パターン(どこに居るか)と帰属(何に載っているか)は **直交**。**競合しない**」 |
| **§4.3** | 「**spacer 除外** を外す ⇒ **DC-1** が **`ON_SPACER`** → **`IN_CHANNEL`** に **反転**」 |

⇒ ⛔ **`ON_SPACER` は *帰属* 軸、`IN_CHANNEL` は *パターン* 軸。§2.5 が直交と定義した 2 軸の値は、互いに *反転し得ない*。**

⇒ この mutation は **構成上、絶対に「反転」を起こさない。**

⇒ §4.3 自身の規則: 「⛔ **どの leg も反転を起こさなければ、その leg は死んでいる (no-op)**」

⇒ ⛔⛔⛔ **∴ mutation test を書かれた通り実行すると、「spacer 除外 leg は no-op」と判定される。良心的な builder はそれを *削除* する。計器が存在する唯一の理由を、計器自身の DoD が削除する。**

### 🔒 修正

mutation は **1 つの軸の中で** 述べる。例:
- 「spacer 除外を外す ⇒ **`support_geom`** が `ON_SPACER` → (壁部品として誤命名) に反転」、または
- 「spacer 除外を外す ⇒ **旧スカラー** (min over `_clip1g` incl. spacer) が ~0 = 『着座』 ⇔ **新 wall-only 距離** が >> 0」

---

## ⚠ HIGH-1 — **`AIRBORNE` は、分母が支えられない不在主張**

§2.5: 「`support_geom = none` ⇒ **`AIRBORNE`(何にも載っていない)**」。しかし support 探索は **C1 の geom 集合のみ**。

⇒ cable が **C2 の clip / C2 の riser** (`test_newton_clip_routing.py:1255-1267`、x ∈ [0.38, 0.42])・table・void の縁に **しっかり載っていても**、計器は「何にも載っていない」と報告する。

⇒ ⭐ **banked 教訓の再演**: 「不在主張の分母は、述語自身の空間から来なければならない」。

🔒 **修正 (どちらか):**
- (a) **`NO_C1_SUPPORT` に改名** (正直な scope 表明)、または
- (b) ⭐ **support 探索を全 scene geom に広げ、*支えている body を名指しする*。** — ほぼタダで、かつ **HIGH-2 (下記) を GPU ゼロで解決する。**

---

## ⚠ HIGH-2 — ⛔ **私 (COORD2) の撤回: 「腕 A 終端は spacer の上」は誤り。支持体は現在 *不明***

**私が持ち込んだ主張** (`state.md` 「副 = z (溝 829 vs **spacer 824** の弁別 — %10 の spacer 発見)」、commit `49b770c9e4` 題「The cable comes to rest **on the spacer**」) を **撤回する。**

| 事実 | 値 |
|---|---|
| **C1 の spacer** x 範囲 | **[0.330, 0.370]** (中心 0.35 ± 0.020) |
| 腕 A 終端 (実測) | \|dx\| = **56.06 mm** ⇒ x ≈ **0.406** (または 0.294) |
| ⇒ | ⛔ **C1 の footprint の *36mm 外*。spacer は cable の下に無い。** |

⭐ **spec 自身の数字が私の誤りを証明している**: §5.5 / NC-1 注記の「旧計器でも **+36mm** で落ちる」は、**厳密に 0.406 − 0.370** (= C1 base-plate / spacer の +x 面までの距離)。

⇒ **`z = 824 = spacer_top + r` は「一致するだけの数字」であり識別情報ゼロ** — 0.824 は *この float における任意の riser* 上の静止高さであって、C1 の riser がそこに無い以上、支持体の証拠にならない。

⚠ **C2 の spacer でもない**: 計器が拾う節点は C1 に **Y 最近傍** (y ≈ 0.150)、C2 の spacer は y ∈ [0.060, 0.090]。

⇒ ⛔ **腕 A 終端で cable を支えている物は、現時点で *不明*。** spec の NC-1 期待値 `AIRBORNE` は **蓋然性はあるが未検証**。
⇒ ⭐ **HIGH-1(b) の support 探索拡張が、これを *オフライン・GPU ゼロ* で答える。**

---

## ⚠ MED-1 — §1.5 の中心例が過大主張 (2 つのうち 1 つは *正しい*)

`route_executor.py:2506` (逐語):
```python
LOW_WALL_TOP = (CLIP1_Z + _clip_float_z + 0.020) * 1e3  # 820mm(+float): cable-centre escape crit (low-wall top)
```
- spec は comment の **820** を ⛔誤 と marking。
- しかし **「820mm**(+float)**」は「820mm、*プラス float*」と読むのが自然**であり、820 + 20 = **840** = 計算値と **一致する** ⇒ ✅ **この comment は正しい (簡潔だが正しい)。**
- ⛔ 誤っているのは **print 文字列の `groove 809`** (`:2798` で実読・確認) と **`GROOVE_CENTER_Z` = 809** (`task_config.py:226`) の 2 件。

⇒ 🔒 **DATUM 導出則 (§1.6: 全て built model から runtime 導出) は *正しい。維持せよ*。** ただし「verify するな narrate するな」を主題に据えた doc が、誤読した例を根拠に掲げてはならない。
⇒ spec 自身の §5.2 が該当する: 「**仮説を *裏付ける* 算術は計算し、*反証する* 算術を計算しなかった**」。

---

## ⚠ LOW-1 — doc header の時刻が未来

header「v0.2 2026-07-14 **16:1x** JST」/ 本文「%12 … **16:0x** 最終裁定」。**file mtime = 15:45、私の `date` = 15:49 JST。** ⇒ 25 分ほど先の時刻。`date`-THEN-write を。

---

## 🔒 §A 再現 (機械算術、source 定数のみ。GPU ゼロ)

```
base  x[  -20.0,  +20.0]mm  z[  820.0,  825.0]mm
wallL x[  -10.5,   -7.5]mm  z[  825.0,  840.0]mm
wallR x[   +7.5,  +10.5]mm  z[  825.0,  840.0]mm
lipL  x[  -15.0,  -11.0]mm  z[  840.0,  850.0]mm     <- 内面 ±11.0 は 壁外面 ±10.5 の外 = 籠なし ✅
lipR  x[  +11.0,  +15.0]mm  z[  840.0,  850.0]mm
spacer x[ -20.0,  +20.0]mm  z[  800.0,  820.0]mm     <- 上面は base plate 下面と同一・同 footprint

base_top = 825.0mm   wall_top = 840.0mm
SEATED cable centre (spec §1.4) = base_top + r = 829.0mm

L1: x > -3.5mm     L2: x < +3.5mm     (=> |dx| <= 3.5mm)
L3: z > 829.0mm  <-- 着座点そのもの     L4: z < 836.0mm

IN_CHANNEL z-window = (829.0, 836.0) mm  [開区間]
=> 床に載った cable は排他的下限に居る = IN_CHANNEL 不成立

PC-1 (dx=0, z=829, 期待 IN_CHANNEL)          L3=False -> BELOW_BASE   ⛔
腕 A 溝進入 t=255 (z=827.6)                   L3=False -> BELOW_BASE   ⛔
DC-1 (|dx|<20mm, z=824, 期待 ON_SPACER)      L3=False -> BELOW_BASE   ⛔ + base plate 内部
```
(source: `newton_skill_env_base.py:1848-1853` / `test_newton_clip_routing.py:1201-1216`, `:1255-1267` / `task_config.py:20,91,137,225,226` / `route_executor.py:1976-1983`, `:2506`, `:2798`)

---

## 🔒 §B 勧告 (build 前、全て GPU ゼロ)

| # | 処置 | 解消する CRIT |
|---|---|---|
| **B-1** | 🔒 **verdict を `L1 ∧ L2` (横) に置く。L3/L4 は 4-bit pattern の *診断* として出すが、A vs D の verdict 連言に入れない。** = v3/v4 LOCK の「主 = `\|dx\|`」と同一 | **CRIT-1 + CRIT-2** |
| **B-2** | ⭐ **静止 z を *実測* せよ (CPU、無料)**: cable を dx=0 で溝に落として settle させ z を読む。**`ke=2500` と `ke=40000` の両方で。** ⇒ (i) z datum が per-arm であることが *実測で* 示される (⇒ B-1 の必然性) (ii) ⭐**§4.1 が「repo に無い」と言った *実在の in-groove positive control* が、Rs も GPU も使わずに手に入る** | **CRIT-1 + CRIT-2** |
| **B-3** | 🔒 **DC-1 を spacer の *側面* に移す** (\|dx\| ≈ 24mm, z ∈ [804, 816])。到達可能・新旧が本当に割れる | **CRIT-3** |
| **B-4** | 🔒 **mutation 行を 1 軸内で述べ直す** (§4.3) | **CRIT-4** |
| **B-5** | 🔒 **support 探索を全 scene geom へ広げ、支持 body を名指しする** (or `NO_C1_SUPPORT` へ改名) | **HIGH-1 + HIGH-2** |
| **B-6** | 🔒 §1.5 の comment(820) 行を撤回。**DATUM 導出則は維持** | MED-1 |
| **B-7** | 🔒 run provenance に **`ke` と `gap` の両方**を記録 (腕 D は純粋な ke swap ではない) | CRIT-2 付随 |

⚠ **B-1 が最重要。** これが無いと、**(d2) の事前登録した升が、剛性そのものによって偽発火する** — すなわち本 node の存在根拠を決める実験が、検定対象と交絡した計器で採点される。

---

## §C 私の側の教訓 (own)

1. ⛔ **「824 = spacer top + r」で支持体を同定した = 数値の一致を証拠に使った。** 私自身が今夜 3 度他者に対して禁じた誤り ([[agreeing-number-may-be-a-design-constant-zero-discriminating-information]])。**支持体は *幾何* で決まる。C1 の riser は cable の 36mm 外に在った。**
2. ⭐ **私の誤りを暴いたのは、spec 自身が書いた「+36mm」だった。** — [[your-own-tool-output-holds-the-counterexample]]
3. ⭐ **「食い込み分 bar を下げる」という *素直な修正* が、この arc で 3 度目の「bar が treatment と共に動く」だった。** 素直さは安全性ではない。

---

**Auditor: COORD2 (w2:p2)。verdict は %12 (RS-TECH-LEAD) が下す — 本 audit は CLOSE を self-declare しない。**
