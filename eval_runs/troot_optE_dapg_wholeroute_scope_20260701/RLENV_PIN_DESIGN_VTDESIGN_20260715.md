# RL env pin 配線 — 設計裁定 v1.5

**Author:** VT-DESIGN (w2:p5)。**Drafted:** 2026-07-15 02:37 JST。**v1.5:** 2026-07-15 07:0x。**Status:** DRAFT — %12 verify 待ち。0-commit（bank = %12）。
**Trigger:** Rs 裁定 2026-07-15 00:5x「クリップ**のみ** pin を RL env に恒久配線しろ」（%12 経由）。
**Scope:** Q1（pin をいつ打つか）/ Q2（clip-only を機構でどう保証するか）/ Q3（STEP 9 述語）/ (a) body 割当規則。
**⚠ 本 doc は message の代替である**（通信規律 2026-07-15 02:35: 数値は artifact に置き、message は path だけ）。

**⛔ 読む順序（改訂が多いので明示）: §17（ERRATUM）→ §19（裁定表）→ §16（BLOCKING）→ §15（実装）。§12 = SUPERSEDED。§14.1 = 撤回。**

- **§17 ⛔ 私の撤回 6 件目** — §14.1（「∃-spec は支持 clip を認可する」）は**偽**。selector は**元から clip 中心で gate されている**（`route_executor.py:2200-2202`、XY gate は意図的な弁別器）。**私は selector を読みながら反例を論じ抜けた。**
- **§19 ⭐⭐ 真の穴 = `route_executor.py:2133-2134`** — `os.environ.get("CLIP_X", "0.40")`。**clip 中心こそ唯一の弁別器**である以上、env 既定は**弁別器を未検証の既定値から供給している**。未設定 ⇒ 「C1 gate」が**静かに built C2 を採点する**。⇒ **既定を削れ**（membership check では捕まらない）。
- **§16 ⛔ BLOCKING 2 件（①の撤回に【一切触れられない】）:** (a) `policy_route_runner.py:309` は**溝の脇の棚を溶接し得る**（live）/ (b) ⭐ `SETTLED_IN_NOTCH` は**溝の中と脇を区別できない** ⇒ **banked C2 成功数は唯一効く軸で未検証・誤差の向き UNKNOWN ⇒ bank 不可**。**本 arc で最大の blast radius。**
- **§18 ⭐⭐ 統合:** **境界の問い ≠ 同一性の問い。側方レグは「3 本目の境界」ではなく【唯一の同一性レグ】である。**

---

## §0 撤回（私の誤り 2 件）

### R-1 ⛔ 「cable は top view で直線 ⇒ pin は 2 本が上限 ⇒ 5-clip は substrate の外」= **撤回**

- **誤りの機構:** 「top view で直線」は bend 平面が **VERTICAL** のときだけ真。root = `add_joint_free`（`test_newton_clip_routing.py:1000`）⇒ **6-DOF 自由 ⇒ 平面の【向き】が自由 DOF**。水平平面なら top view は曲線そのもの。5 座面は厳密 coplanar（既 bank）⇒ 水平 bend 平面が 5 点すべてを通り得る。
- ⇒ **幾何的 infeasibility は成立しない。** 残る問いは **到達可能性**（solver が初期の垂直平面からそこへ行けるか）であって **存在可能性** ではない。
- **⚠ 反例は私自身の引用文の中に在った:** RS71 §4:62 の、私が引いた同じ文が「position (**free root**) + **free-root pose**」と書いている。
- **⚠ prior-art guard 未実行:** `scripts/check_thread_vault_prior_art.sh --fail-on-blocker` を回していない。同一主張は %12 が既に over-claim として撤回し LEDGER に載っていた（best-fit 残差 2clip 0.0 / 3clip 16.7 / 5clip 20.0mm）。**再導出だった。**
- **検出:** p3（2 度）。**Rs 上程の寸前で停止。**

### R-2 ⛔ 「述語ベース選択なので pin は D-5 に不感」= **撤回**

- **pin 1 本なら真。2 本以上で偽。** 各 clip で独立に「最近傍 body」を選ぶと **5-segment stride** になり、90.14mm の hop に 75mm しか配らない ⇒ **構成の時点で充足不能な拘束を作り込む**（= §4 の割当規則が必要な理由）。

---

## §1 裁定 Q1 — pin をいつ打つか

🔒 **表どおり STEP 9（解放後）。K = 10 フレーム。**

**根拠（静窓実測、pB、牽引ゼロ = L の EE 移動 ≤1.3mm、窓 = phase 8 R_UNCLAMP_RISE = 520 frame = 1.081 s）:**

| DOF | 溝 | 実測 |
|---|---|---|
| −Z / ±X（半径方向） | form-close | **留まる。** z 829±1 / 壁天端 840 超え **0** / 横逃げ **0** / **溝は一度も空にならない (0/520)** |
| ±Y（軸方向） | **OPEN = 設計どおりのしごき** | **滑り続ける**（1.7–10 mm/s、1.081 s で減速しない） |

⇒ **放しても半径方向には留まる ⇒ そこで pin が ±Y を閉じる ⇒ 搬送。表の順序（8 放す → 9 pin → 11 搬送）は動く。**

### ⭐ K は自由パラメータではない — **K = アンカー位置の選択**

cable が軸方向に送られている以上、**待った 1 フレームごとにアンカーが cable に沿って先へ移動する。**

`dt = 0.00208 s/frame`（`seatgate_verify_20260714/r7_B0_rsCell_NOPIN/route_demo_raw_meta.json` の `dt`）⇒ **0.0035–0.021 mm/frame**

| K | アンカー漂流 | 判定 |
|---|---|---|
| **10** | **0.035–0.21mm** | ✅ 側方 bar 3.5mm ≪、segment pitch 15mm ≪ |
| 20 | 0.07–0.42mm | ✅ |
| 520（窓全体） | 1.8–10.8mm | ⛔ **最大 0.72 segment ぶん動く** |

🔒 **K = 10**（半径方向の述語は最初のフレームから TRUE ⇒ 待つ理由がない）。`wait_max = 240` は保険、**実 wait 分布をログ**（実際は 0 の見込み）。
⇒ ⭐ **「どれだけ待つか」は「cable のどこにアンカーを打つか」= 整定でなく経路長の問題 ⇒ §4 と直結。待たない。アンカーは割当 ladder が決める、時計が決めるのではない。**

---

## §2 裁定 Q2 — clip-only を機構でどう保証するか

🔒 **【構成】で保証する。実行時チェックでは保証しない。**

- pin が activate できるのは **pre-allocated + 初期無効の CONNECT-to-world eq** のみ（`route_executor.py:770-775`: `eq_type==CONNECT ∧ eq_obj2id==0 ∧ eq_active0==0`）
- ⇒ **builder が clip にしか eq を割り当てなければ、clip 以外の溶接は【表現不可能】** — eq が存在しないので機構が溶接できない
- ⇒ **保証は構造的: 可能な溶接の集合 = pre-allocated eq の集合 = clip 集合**
- ⛔ **RL env に「実行時に eq を生成する」経路を一切与えない** ⇒ **`mjm.neq` がエピソード中不変であることを assert**
- ⭐ **positive control（必須）:** clip でない body を pin しようとする test が **RAISE すること**。黙って成功するなら保証は虚構。**そして走らせること** — 発火していない guard は発火**できない** guard と区別できない。

---

## §3 裁定 Q3 — STEP 9 述語

🔒 **改訂は要る。ただし【保持の意味】であって【順序】ではない。**

⛔ `CANONICAL_MOTION_TABLE_V1.md:128` の「**body30 が** …側方 seated & 保持」は **過剰指定**:
- cable は軸方向に滑る（実測）⇒ **溝を占める body は入れ替わる**
- 特定の物質点が留まることを要求するのは、**溝が閉じていない（かつ閉じるべきでない）自由度を閉じろ**という要求
- **軸方向の滑りは失敗ではなく設計**（表 `:32` / `:50` の半クランプ = **滑り誘導=しごき** = cable は通り抜けるためにある）。**滑る向きは C2 側 = 送り出しとして正しい。**

### 🔒 改訂述語（∃ 形）

```
SEAT9 := 解放後 K フレーム連続で、
         ∃ 自由な cable body b:
             dy_in_clip(b) ∧ inside_left_wall(b) ∧ inside_right_wall(b)
             ∧ below_wall_top(b)
```
⛔ **`on_floor(b)` は【連言から外した】（v1.0 → v1.1、§9 参照）。Rs 動画 GT により、床接触は【欠陥でなく機構】と判明。**
- ⭐ **「∃ ある body が」であって「同じ body が」ではない。**
- **free(b)** = active な connect-to-world eq の obj1 でない ∧ どの爪の Y-footprint にも入らない
- レグの実体 = `route_executor.py:665-670`（`dy_in_clip` `:666` / `inside_left_wall` `:667` / `inside_right_wall` `:668` / `below_wall_top` `:669`）
- bar の出所 = `c1_channel_from_model` `route_executor.py:554-625`（built model 実行時導出、tripwire `:607-616`）

⇒ **pB は既にこれを 520/520 で TRUE と測っている ⇒ STEP 9 の「保持」= 半径方向 = 実測で成立。**
⇒ **r7 追補として `:128` に注記**（canonical 値・工程・クリップ状態列は INVARIANT、annotation-only）。

---

## §4 (a) body 割当規則 — ⭐ **D-5 の 7-segment ladder**

### 既 bank（私の D-5、`CANONICAL_MOTION_TABLE_V1.md:184` / `:110-111`）
- 千鳥 hop 弦長 = √(50²+75²) = **90.14mm**（`task_config.py:202-204`: CLIP_Y_SPACING 0.075 / CLIP_X_ODD 0.35 / CLIP_X_EVEN 0.40）
- `CABLE_SEG_LEN = 0.015`（`task_config.py:136`）⇒ 5 seg = 75mm ⇒ **arc ≥ chord に反する ⇒ 5 seg では張れない**
- **正 = ≥7 seg**（⚠ 6 seg = 90.0mm は **0.139mm 不足で不可**）
- **正値 = C1:33 · C2:26 · C3:19 · C4:12 · C5:5 = 7-segment stride**（幾何 witness `shared/GEOM_WITNESS_5CLIP_p5_20260714.py` 6/6 PASS。**Rs 上程済・裁定待ち**）

### ⭐ 本 doc で D-5 を強化（arc ≥ chord は弱すぎた）

**溝は【チャンネル】**（Y 30mm × X 15mm、built model）⇒ 中の cable は Y に沿っていないと壁に当たる:
- 許容角 = `atan(2 × 3.5mm / 30mm)` = **±13.1°**
- ⛔ C1→C2 の弦は Y から `atan(50/75)` = **33.7°** ⇒ **直線では溝を 33.7° で出入りする = チャンネルが許さない**
- ⇒ ⭐ **cable は S 字を描かねばならない**（C1 を Y 向きに出て、50mm の X を渡り、C2 に Y 向きで入る）
- **最小 S 字**（2 円弧、両端で Y に接する）: `tan(θ/2) = 50/75` ⇒ **θ = 67.4°** / **R = 40.6mm** / **arc = 2Rθ = 95.5mm**

| 割当 | arc | vs 弦 90.14 | **vs S 字 95.5** | 判定 |
|---|---|---|---|---|
| 5 seg（**現行の最近傍**） | 75mm | ⛔ −15.1 | ⛔ **−20.5** | **構成の時点で充足不能** |
| 6 seg | 90.0mm | ⛔ −0.14 | ⛔ −5.5 | 不可 |
| **7 seg（D-5）** | **105mm** | ✅ +14.9 | ✅ **+9.5** | ⭐ **最小。余裕 9.5mm = きつい** |
| 8 seg | 120mm | ✅ | ✅ +24.5 | 余裕。⚠ 自由端が 4 seg/側に減る |

🔒 **割当規則 = D-5 の 7-seg ladder。⛔ 最近傍割当を使わないこと**（Q2 の「構成で保証」の裏返しの危険 = 構成の時点で充足不能な拘束を作り込む）。

⚠ **要確認（私は未確認）:** 必要 per-joint 曲げ角 = 15/40.6 = **21.2°**。revolute の joint limit がこれ未満なら **7 seg でも曲がらない**。

---

## §5 正しい定式化（R-1 の副産物、これは維持）

**bend 軸は 1 本**（`test_newton_clip_routing.py:1009` `axis=wp.vec3(1,0,0)`）。**平面の向きは【グローバルな 1 自由度】(root pose)** であって segment ごとの自由ではない。

⇒ ⭐ **cable は【水平曲率】か【垂直たるみ】か、どちらか一方しか表現できない。両方は不可能。**
⇒ これが RS71 §4:62「NOT horizontal routing curvature」の正確な形（= 垂直たるみを保ったまま水平曲率は無理）。

**⭐ 反証テスト（安価、p3 へ）:** pin が増えるにつれ **cable の自由端が垂直に硬くなる**はず（平面が水平に転べば垂直曲げ DOF が消え、端がテーブルへ垂れられない）。**自由端の z を、有効 pin 数の関数として測る。垂れなくなったら平面が転んでいる。**

---

## §6 権威 run — r9 の扱い

🔒 **r9 は邪魔者ではなく、gate の POSITIVE CONTROL。**

- r9 は窓の入口で **z = 843mm > 壁天端 840mm** ⇒ `below_wall_top`（z < 836）が **FALSE** ⇒ **seat gate は r9 を拒否する**
- ⇒ **r9 = 実データ上で gate が【発火する】ことの証拠。捨てない**（発火を見ていない guard は、発火**できない** guard と区別できない）
- ⇒ **「gate-REFUSED」として報告し、保持の分母から除外する。⛔ 黙って落とさない**
- ⇒ ⭐ **分母を宣言する:** 「NOPIN 5 本のうち」ではなく **「gate が pin したはずの N 本のうち、M 本が半径方向に保持した」**
- ⚠ gate の前提条件で条件付けるのは**生存者バイアスではない**（pin は gate を通った run にしか作用しない）。**ただし分母を書かなければ生存者バイアスになる。**

---

## §7 未検証 / 要確認

| # | 項目 | 誰 |
|---|---|---|
| U-1 | revolute の **joint limit**（S 字に **21.2°/joint** が必要） | 未割当 |
| U-2 | bend 平面が実際に転ぶか（到達可能性） | p3 実測中 |
| U-3 | 自由端の垂直剛性（§5 の反証テスト） | 未実行 |
| U-4 | 静窓の限界: 窓は 1.081 s のみ ⇒ その先の軸方向の行き先は**この run では観測不能**。静窓 = 「無荷重」でなく「EE 運動ゼロ」（**L の cradle 経由の残留張力は否定できない**） | pB 申告済 |
| U-5 | **D-5 = Rs 裁定待ち**（07-Design canonical の訂正は Rs 専権） | Rs |

---

## §9 ⛔ ON_FLOOR / `h_float` の撤回（v1.1、2026-07-15 03:1x、Rs 動画 GT B-0a 受領後）

### Rs 動画 GT（B-0a、逐語、%12 経由）
> 「**とまっていない、溝にはきちんとハマっている、底についたようだが完全には底についていないかもしれない**」

**3 点が独立に対応する:**

| Rs の観察 | 対応する DOF | 私の Step-5d 予測 | 判定 |
|---|---|---|---|
| **とまっていない** | ±Y（軸方向） | **OPEN = 設計どおりのしごき** | ✅ human GT が支持 |
| **溝にきちんとハマっている** | −Z / ±X（半径方向） | **form-close** | ✅ human GT が支持 |
| ⚠ **完全には底についていないかも** | 床接触 | **（私は ON_FLOOR を gate レグに置いていた）** | ⛔ **これが本節** |

### 🔒 裁定: **`on_floor` を gate レグから外す。`h_float = 2.0mm` は gate として撤回**（reported metric へ降格）

**理由 1 — 機構（幾何から導出、run 不要）: clip は台座であり、cable は台座に掛け渡されている。**
- テーブル面 = **800.0mm**（`task_config.py:20` TABLE_HEIGHT 0.80）。テーブル上の cable 中心 = 800 + R 4 = **804.0mm**
- clip の溝床 = **825.0mm**（clip 原点 820 = CLIP1_Z 0.800 + CLIP_FLOAT_Z 0.020、base plate 天端 = +5mm）。溝内の cable 中心 = **829.0mm**
- ⇒ ⭐ **clip は 25mm の台座。base plate は y ∈ [0.135, 0.165] の 30mm メサ。その外はテーブルまで 25mm の崖。**
- ⇒ ⭐⭐ **cable は 30mm メサに掛け渡され、両側の端が崖下へ垂れる。垂れた端の重量がメサ端に下向きモーメントを作り、【中央（＝着座 body）をメサ天端から持ち上げる】**（片持ち／オーバーハング効果）。
- ⇒ 🔒 **これは【手の有無に無関係】に起きる。溝が保持していても起きる。⇒ Rs の「完全には底についていない」は【欠陥ではなく機構】。**

**理由 2 — `on_floor` は 2 つの吊り下げを区別できない（= 識別情報がない）:**
| 吊り下げ | 良否 | `on_floor` の反応 |
|---|---|---|
| ① **グリッパのロッド結合**（L 半保持が持ち上げる） | ⛔ **悪い**（手が保持している = 捕捉していないのに捕捉に見える） | FALSE |
| ② **cable 自身の垂れ端**（台座オーバーハング） | ✅ **正常。実 cable が実 clip でやること** | FALSE |
⇒ ⭐ **同じ値を返す ⇒ 情報量ゼロ。** gate にすれば ② を落とす = **正しく着座した cell を落とす**（偽拒否）。

**理由 3 — bar が測定の分解能を下回る:**
- 静窓実測 = **z 829±1mm** ⇒ 持ち上がりは **≤1mm**
- 接触貫入は **1.541mm** に達し、剛性は **16×** 開く（env ke 2500 / producer 40000）
- ⇒ ⭐ **問いの尺度（sub-mm）が、計器自身のノイズ床（1.5mm）を下回る。この尺度で bar は引けない。**

### ⇒ **捕捉（capture）と接触（contact）は別物。Rs 自身の言葉が分けている。**
- 「溝にきちんと**ハマっている**」= **capture** ⇒ ⭐ **4 レグ（dy ∧ 左 ∧ 右 ∧ 天井）が測るのはこれ。** 側方は壁が閉じ、脱出には **15mm の持ち上げ**が要る ⇒ **床に触れていなくても捕捉されている。**
- 「完全には**底についていない**かも」= **contact** ⇒ **測って報告する。gate にしない。**

### 🔒 pB への測定目的の変更（**bar を決めるためではない**）
**目的 = 機構の同定。既存の `cable_xyz`（per-frame）で足りる。GPU ゼロ。**
- ⭐ **判別器: 溝を横切る cable の z 断面形状**（y = 0.135 → 0.165、およびメサ外）
  - **アーチ**（中央が最高、メサ端で下がる）⇒ **台座オーバーハング = 機構 ②** ⇒ **gate にしない**（確定）
  - **L 側（y=0.106）へ傾く** ⇒ **手が持ち上げている = 機構 ①** ⇒ **これは捕捉の問題 ⇒ 別途設計が要る**
- 併せて報告: `z_seat` 分布（gate 通過 run のみ、**分母を宣言**）/ 床接触の有無（接触クエリ、z 閾値でなく）

### ⚠ 私の撤回（3 件目）
**R-3:** 前便で私は `h_float = 2.0mm` を「宣言値 + 反証テスト付き」で出した。**gate レグとしては撤回。** 誤りの型 = **「溝に吊られている」の原因を 1 つ（手）しか数えず、幾何固有の第 2 の原因（台座オーバーハング）を見落とした** ⇒ 片方を捕まえる bar が、もう片方も落とす。

---

## §10 🔒 出荷済 gate の裁定（v1.2、2026-07-15 03:2x、pB 実測 STATIC_WINDOW_ANALYSIS §9 受領後）

### 実測（pB、実モデル + `mj_geomDistance`、陽性対照 完全一致）— B-0a 静窓、床との隙間
| body | 隙間 | z（= 829.0 + 隙間） |
|---|---|---|
| k27 | **−0.011mm**（接触） | 828.99 |
| ⭐ **k28（着座 body）** | ⛔ **+0.679mm（浮き）** | **829.68** |
| k29 | +1.517mm | 830.52 |
⇒ ⭐ **§9 の台座オーバーハング機構が【実証】された。** 着座 body は溝底から浮いている。

### ⛔ 出荷済 gate のレグ 1 は、この【正しい捕捉】を落とす
`route_executor.py:3053` = `_min_dist_mm([_seat_geom_gate], _clip1g)` = **pin する body 自身の geom**（`:3048` で world-pos match）。⇒ `:3055` `_touch_mm <= 0.5` ⇒ **0.679 > 0.5 ⇒ REJECT。**
⚠ pin あり run では gripper が押さえるので未発火。**しかし表どおり「放してから打つ」に移した瞬間、まさにこの状態で打つ ⇒ gate が正しい run を拒否する。**

### 🔒 裁定 = **(a) 削除。ただしレグ 2 の置換とセット**

**⛔ (b)「bar を 2.0mm へ緩和」は却下。理由 2 つ:**
1. **2.0mm は私の宣言値（R/2）であって導出値ではない。** §9 で gate として撤回済。撤回した数字で bar を引き直すのは、根拠のない datum の再導入。
2. ⭐⭐ **決定的: 浮き量は【オーバーハング長】に比例し、それは clip ごとに違う。** cable は y ∈ [−0.30, +0.30]（600mm）。**C1（y=+0.150）では +150mm / −450mm の非対称オーバーハング。C3（y=0.000）では +300mm / −300mm の対称。** ⇒ **C1 で調整した接触 bar は C3 で誤る。⇒ 単一の接触 bar は C1-C5 を通せない。⇒ 調整するな、削除せよ。**

**⛔ (c) 維持も却下**（上記のとおり、順序修正の瞬間に正しい run を落とす）。

### 🔒 置換後の述語（= 既存計器 + 新レグ 1 本）

| レグ | 式 | 出所 | 変更 |
|---|---|---|---|
| `dy_in_clip` | 壁自身の y-span 内 | `route_executor.py:666` | 維持（定義域） |
| `inside_left_wall` | `x > in_L + R` | `:667` | ⭐ 維持（**唯一の load-bearing**）+ **R1 tripwire 必須** |
| `inside_right_wall` | `x < in_R − R` | `:668` | ⭐ 維持 |
| **`below_wall_top`** | **`z < rim − R` = 836.0mm** | `:669`（rim = `:620`） | ⭐ **`\|z − groove_z\| ≤ 3.0` を置換**（上側） |
| **`above_channel_floor`** ★新 | **`z > floor_top − R` = 821.0mm** | `floor_top` = `:624` | ⭐ **同（下側）** |
| ⛔ **接触レグ** | — | — | ⛔ **削除** |
| `free(b)` | active eq の obj1 でない ∧ 爪の Y-footprint 外 | — | 追加 |

**なぜ z 窓を [826, 832] → [821, 836] にするか:**
- **上側 836 = 捕捉の天井**（これを超えると cable の上端が壁天端を越え、側方に脱出できる）⇒ ⭐ **アーチの余裕が 3mm → 7mm**（`\|z−groove_z\|≤3` は **レグ 1 と同じ罠を一歩外側に持っている** — 今日は 0.679 < 3.0 で発火していないだけ）
- **下側 821 = cable の上端が溝床面より上**（= **clip の【下】に居ない**）⇒ ⭐ **貫入の余裕が 3mm → 8mm**（実測貫入 1.541mm、剛性 **16×** 差 env 2500 / producer 40000 ⇒ 柔らかい env で下側 826 は踏み得る）

**⚠ 下側 bar は【必須】。削除だけでは穴が開く:**
- **clip は浮いている**（`CLIP1_Z = TABLE_HEIGHT = 0.800`（`task_config.py:225`, `:20`）+ `CLIP_FLOAT_Z = 0.020` ⇒ clip 底面 = **820mm**。**SPACER は ROUTE_ENV に無い** ⇒ **テーブルと clip の間に 20mm の空隙**）
- ⇒ **cable（直径 8mm）は clip の【下】に入り得る。** clip 底面に押し付けられた最大 z = 820 − 4 = **816mm**
- ⇒ `dy` ✓ / `dx` ✓ / `below_wall_top`（816 < 836）✓ ⇒ ⛔ **下側 bar が無ければ「clip の下の cable」を SEATED と呼ぶ**
- ⇒ **821 で切る ⇒ 816 は REJECT（余裕 5mm）、貫入した静置 827.5 は PASS（余裕 6.5mm）** ✓

### ⭐ 実測との照合（pB の数値で検算）
| 状態 | z | [821, 836] | 判定 |
|---|---|---|---|
| k27（接触） | 828.99 | ✅ | PASS |
| ⭐ **k28（着座・浮き 0.679mm）** | **829.68** | ✅ | ⭐ **PASS**（**旧レグ 1 は REJECT していた**） |
| k29 | 830.52 | ✅ | PASS |
| clip の下（最大） | 816 | ⛔ | **REJECT** ✓ |
| 壁の上 | 844 | ⛔ | **REJECT** ✓ |
| 空中溶接（実測最大） | 880.9 | ⛔ | **REJECT** ✓ |

### 🔒 positive control（両側から pin、⛔ 絶対世界座標。`groove_z + δ` で書かない）
| probe z | 期待 | 何を試すか |
|---|---|---|
| **816.0** | ⛔ **REJECT** | 下側 bar（clip の下） |
| 827.5 | ✅ PASS | 貫入した静置（柔らかいソルバ） |
| ⭐ **830.0** | ✅ **PASS** | ⭐ **アーチ = 旧レグ 1 の罠。これが最重要** |
| 838.0 | ⛔ REJECT | 上側 bar（捕捉の天井） |

---

## §11 🔒 動画 GT の軸被覆（pC fold、2026-07-15 03:2x）

**pC 指摘（採用）:** 溝は **Y 押し出し** ⇒ 断面図（xsec）は **Y 軸に沿って**見る ⇒ ⛔ **xsec は軸方向（±Y）に【原理的に】盲目。**

⇒ ⭐⭐⭐ **計器の盲目軸が、溝の開いた軸と【一致している】。偶然ではない — 同じ対称性**（Y 押し出しの形は、Y 方向の視線で潰れる）。

| DOF | 溝 | xsec で見えるか |
|---|---|---|
| ±X（側方） | form-close | ✅（視線に直交） |
| −Z / +Z | 床 / 開 | ✅（視線に直交） |
| **±Y（軸方向）** | ⛔ **OPEN** | ⛔ **原理的に不可視**（視線方向） |

### 🔒 一般規則（⚓ 方法論の拡張）
**視線が軸に平行な view は、その軸を分解できない。** ⇒ ⭐ **xsec は軸方向の運動を【確認】はできる（判定者がたまたま知覚すれば）が、【反証】は決してできない。片方向の計器である。**
⇒ ⛔ **「cable は滑るのを止めた」— pin の有効性判定が全て乗る主張 — は、xsec では接地不可能。** xsec に運動が見えないことは、運動が無いことの証拠にならない。
⇒ 🔒 **top-down（X-Y）panel を【必須】とする対象: ① 「軸方向の滑りが止まった」形の全主張（= 全 pin 有効性判定）② 搬送を跨ぐ「STILL 保持」主張。**

### ✅ ただし Rs の B-0a 判定は【失効しない】（範囲が確定するだけ）
私は **STEP 9 の「保持」= 半径方向**（∃ 形、§3）と裁定した。**半径方向は xsec 平面【内】** ⇒
- **Rs の xsec GT が discharge するもの:**「溝にきちんとハマっている」（半径方向の捕捉）✅ /「底についていないかも」（床との隙間）✅ — **両方とも面内**
- **接地【されない】もの:**「とまっていない」を *測定された事実* として。**Rs は知覚した（⇒ 運動は存在する = 確認）が、xsec はその【不在】を示すことは決してできなかった。**

⇒ **本節を私の containment spec `:51` へ fold 済（同 turn）。**

---

## §12 ⛔⛔ Q2 の裁定を【訂正】（v1.3、2026-07-15 03:3x）— 私の撤回 4 件目

### ⛔ §2 で私が書いたこと（**偽**）
> 「builder が clip にしか eq を割り当てなければ、clip 以外の溶接は【表現不可能】。保証は構造的: 可能な溶接の集合 = pre-allocated eq の集合 = clip 集合。」

### ⛔ 実物（on-disk）
| 事実 | cite |
|---|---|
| eq は **clip ごとでなく【cable body 1 本ごと】**に事前割当 | `newton_skill_env_base.py:1596` `for _pb in cable_bodies_proto:` → `:1597-1603` `add_equality_constraint_connect(body1=_pb, body2=-1, enabled=False)` |
| **world anchor は【実行時】に書かれる** | `route_executor.py:792-793` `eq_data[best,0:3]=[0,0,0]` / `eq_data[best,3:6]=seat_world` |
| ⛔⛔ **`eq_active`/`eq_data` の書き手が【4 箇所】= 絞り口が無い** | `route_executor.py:794`（`activate_c1_pin`）/ `route_executor.py:3140`（producer inline）/ `policy_route_runner.py:328-330`（π rollout）/ `test_newton_clip_routing.py:4798`（byte-repro 双子） |

⇒ ⛔⛔⛔ **機構は【任意の cable body を、任意の世界点へ】溶接できる。**「clip のみ」は**構成が保証していない** — **呼び手が clip 近傍の `seat_world` を渡す規律**に依存しているだけ。
⇒ **58/343 の空中溶接（最大 880.9mm）は、まさにこれが許したもの。** 機構は拒まなかった。

### ✅ 一方、良い知らせ（§4 ladder への含意）
eq が **全 body** に張られている ⇒ **どの body を pin するかは build 時に焼き付いていない。実行時の述語が選ぶ。**
⇒ ✅ **§4 の割当 ladder は build を作り直さずに実装できる**（私が §2 で警告した「構成の時点で充足不能を焼き付ける」危険は、この builder では**顕在化しない**）。

### 🔒 正しい保証形（訂正裁定）
**「clip のみ」は【単一の認可関数】でしか保証できない。4 つの書き手が全てそこを通る形にする。**

```
authorize_clip_pin(mjm, mjd, seat_body, seat_world) -> eq_id      ★新設・唯一の書き手
  1. 全 clip の捕捉体積を built model から導出 (channel_from_model を clip ごと)
  2. seat_world が【どれかの clip の捕捉体積の中】でなければ RAISE
       = dy_in_clip ∧ inside_left_wall ∧ inside_right_wall ∧ 821 < z < 836   (§10 の述語そのもの)
  3. repo 内で eq_data / eq_active を書く【唯一の関数】であること
       ⇒ grep が【テスト】になる:  grep -rn "eq_data\[\|eq_active\[" --include=*.py  ⇒ 書込は本関数のみ
  4. mjm.neq がエピソード中【不変】であることを assert (実行時 eq 生成の経路をゼロにする)
  5. 活性化後に sum(eq_active) <= n_clips を assert (二重 pin の禁止)
```

⇒ ⭐ **「clip のみ」が【呼び手 4 者の規律】から【機構の不変条件】になる。** 将来の呼び手（RL env / 新スクリプト / 方策）は迂回できない。

### ⭐⭐ そして構造上の発見: **Rs の 2 つの指示は【同じ機構】である**
- Rs「**ピンが打たれる前に、本当に溝に居るかを確かめる**」（2026-07-14 17:18）
- Rs「**クリップ *のみ* pin を RL env に恒久配線しろ**」（2026-07-15 00:5x）

⇒ **どちらも「`seat_world` が clip の捕捉体積の中にあることを、溶接の【前提条件】として強制する」= 1 本の関数で両方 discharge される。**

### 🔒 positive control（必須・両方走らせること）
| test | 期待 |
|---|---|
| 空中の `seat_world`（例 z=880.9mm、実測最大）で `authorize_clip_pin` を呼ぶ | ⛔ **RAISE** |
| clip の【下】(z=816mm) で呼ぶ | ⛔ **RAISE** |
| clip 捕捉体積内 (z=829.68mm = pB 実測 k28) で呼ぶ | ✅ **eq_id を返す** |
| **grep test:** `eq_data\[` / `eq_active\[` の書込箇所を数える | ✅ **1**（本関数のみ） |
⚠ **黙って成功するなら保証は虚構。そして走らせること** — 発火していない guard は、発火**できない** guard と区別できない。

---

## §13 ✅ U-1 = RESOLVED（joint limit は存在しない）— ただし問いが差し替わる

**`test_newton_clip_routing.py:1004-1016`: `add_joint_revolute` に `limit_lower` / `limit_upper` の指定は【無い】。** あるのは passive spring のみ:
- `mujoco:dof_passive_stiffness = CABLE_MUJOCO_BEND_K`
- `mujoco:dof_passive_damping = CABLE_BEND_DAMPING`（0.01 N·m·s、`task_config.py:152`）
- ⭐ **`mujoco:dof_springref = 0.0` ⇒ rest 形状は【直線】**

⇒ ✅ **S 字に要る 21.2°/joint は【禁止されていない】。** joint limit で不可能になることはない。
⇒ ⚠ **しかし問いが差し替わる:「曲がるか」(YES) ではなく「【どれだけの力が要るか、そしてその力が経路を歪めないか】」。**
⇒ ⭐⭐ **`springref = 0` ⇒ 経路に通された cable は【バネであり、pin に曲げられたまま永久に押し返す】。** pin は恒久荷重を負う。荷重は pin 本数とともに増える。
⇒ 🔒 **U-1 差替: 各 pin の eq 拘束力（`efc_force` / `qfrc_constraint`）を測れ。pin 本数とともに増えるなら、cable は経路と戦っている。**
⇒ **sim2real の告げ口: 実 cable は馴染む。この cable は【直線が rest のバネ】が恒久張力下にある。**

---

## §14 🔒 %12 の反証への裁定（v1.4、2026-07-15 06:2x）— ①②③④ **全て CONFIRM**（私の撤回 5 件目）

対象 = `AUTHORIZE_CLIP_PIN_FALSIFICATION_RSTECHLEAD_20260715.md`。
**⛔ %12 の message の数値では裁定していない。4 件すべて自分で on-disk を読んだ**（通信規律 3「他 pane の数字で裁定しない」）。

| # | 主張 | 私の on-disk 検証（自分で読んだ cite） | 裁定 |
|---|---|---|---|
| ① 支持 clip 4 つが経路 clip と**同一の 5 箱** | `newton_skill_env_base.py:1822-1828` の tuple 5 本は `:1848-1854` `_v_groove_clip_parts` と**逐語同一**。`:1829` `support_clip_ys = [-0.100, +0.050, +0.300, +0.450]`。`:1833` `TABLE_HEIGHT + dz`（**float 無し**）⇒ base top **805.0** / wall top **820.0** ⇒ 捕捉体積 **(801.0, 816.0) mm**。`newton_route_env.py:701` `add_support_clips = not self._g1_scene_align`、`:449` 既定 False ⇒ **route env で ON** | ✅ **CONFIRM** |
| ② 陽性対照が z 軸のみ | §10 / §12 の 4 本 = 880.9 / 816 / 829.68 / 830.0 = **全て z**。穴は (x, y) | ✅ **CONFIRM** |
| ③ `assert sum(eq_active) <= n_clips` が golden で発火 | `newton_skill_env_base.py:1646-1647`（4× connect `enabled=True`）+ `:1664-1670`（2× follower-mirror `enabled=True`）。`test_newton_clip_routing.py:1628` `_want_neq = 6 + _perclip_pin_n` ⇒ `sum(eq_active)` = pin 前 **6** / pin 後 **7** ⇒ `7 <= 5` は**偽** | ✅ **CONFIRM** |
| ④ C2〜C5 の geom 不在 / 空集合がゴミ bar | `route_env_config.py:140` `ROUTE_C2_XY = (0.40, 0.000)` 逐語「`!= task_config (0.40, 0.075)`」。selector = `route_executor.py:2190-2202` = (x_clip, y_clip) 中心 **30mm 箱**、個数 assert **無し** | ✅ **CONFIRM** |

### §14.1 ⭐⭐ ①の重大度は %12 の評価より【高い】— corner case ではなく **全 episode の初期条件**

支持 clip の x = `GRASP_X` = **0.300** = `task_config.py:231` 逐語「**Cable initial X position**」。y は逐語「**cover full cable Y range**」（`:1829`）。
⇒ **支持 clip は cable の初期直線姿勢を保持している治具である。** その溝に載った cable body の中心 z ≈ 805 + 4 = **809mm** = 捕捉体積 **(801, 816) の内側**。

⇒ ⛔⛔ **私の ∃-spec（「seat が *どれかの* clip の捕捉体積の中なら認可」）は、cable を【自分の初期支持治具】に溶接することを認可する。** = **cable の開始姿勢を凍結する溶接**。しかもそれは例外的な状態ではなく、**フレーム 0 で成立している**。
⇒ **「clip のみ」は文字通りには真（それは clip である）が、Rs が認可したもの（`route_executor.py:718` 逐語「その他は絶対禁止」= *経路* clip の retention pin）ではない。**

### §14.2 ⚠ %12 に 1 点【訂正】— 空集合は fail-OPEN ではない。**fail-LUCKY** である

%12 §3「空集合は raise せずゴミ bar を返す」= **正しい**。だが **conjunction は今日 REJECT する**（`route_executor.py:3031-3071` の算術を追った）:

| 量 | 空集合での値 | 効果 |
|---|---|---|
| `_wall_inner_mm` = `min(…, default=0.0)` | **0.0** | ⇒ `_lat_bar_mm = 0.0 − 4.0 = **−4.0**` ⇒ `|dx| <= −4.0` = **恒偽** ⇒ REJECT |
| `_y_win_mm` = `max(…, default=0.0)` | **0.0** | ⇒ `|dy| <= 0.0` ⇒ 実質恒偽 ⇒ REJECT |
| `_z_lo` / `_z_hi` | **−4.0** / **8,999,999,996.0** | ⇒ z レグ**だけ**が **fail-OPEN**（恒真） |

⇒ 🔒 **今日 gate が閉じているのは【設計】ではなく【算術の偶然】** — `default=0.0` から正の半径を引いた結果が**負**になったから。
⇒ ⭐ **「壁の内面が 0.0 は明らかにおかしい」と誰かが *直せば*、gate は fail-OPEN に反転する。意図されていない符号に fail-closed 性が依存している guard は、fail-closed ではない。fail-lucky である。**
⇒ **%12 の結論（個数 assert）は変わらない。むしろ強まる。**

---

## §15 🔒 `authorize_clip_pin` **v2** — 【bar】と【集合】を分離する

%12 §7 の読みを **採用する**。私は 2 つの別物を混同していた。

| 何を | どこから来るべきか | なぜ |
|---|---|---|
| **bar**（捕捉体積の *大きさ*） | ✅ **built model**（幾何） | 溝の寸法は**幾何の事実**。誤った中心は bar を**縮める**だけ（min-over-flanking 構成 ⇒ 受容窓は真の窓の**部分集合** ⇒ 保守側）。要件①はここでは正しい |
| **集合**（*どの* clip に打ってよいか） | ⛔ **model からは読めない** = **task の認可** | 「この V 溝は *経路* clip か *支持* clip か」は**幾何の事実ではない**。同一の 5 箱リテラル ⇒ **model は区別情報を 1 ビットも持たない** |

⭐ **要件①は「定数に触るな」ではなかった。「定数を【閾値】にするな」だった。** 中心は閾値ではなく **datum** であり、bar 導出は datum について単調・保守。⇒ **中心を定数から取ることは、要件①を動機づけた論法そのものによって【安全】。**

### §15.1 ⭐ ただし %12 提案 1（中心を**引数**で受ける）だけでは【機構にならない】

caller が支持 clip の中心 `(0.300, +0.050)` を渡せば ⇒ 個数 assert は**通り**（geom は 5 本実在する）⇒ bar は**正常**（801, 816）⇒ **溶接は認可される。** ⇒ **穴を caller に移しただけ。**
Rs の「クリップ **のみ**」は **機構**での保証を要求している ⇒ **集合は authorizer が【自分で import する 1 つの名前付き定数】でなければならない:**

```python
# route_env_config.py — 認可された経路 clip の【唯一の】定義（支持 clip を含まない）
ROUTE_CLIP_CENTERS = (ROUTE_C1_XY, ROUTE_C2_XY)      # 5-clip 化 = この 1 行の編集

# route_executor.py — eq_data / eq_active を書く【唯一の】関数
def authorize_clip_pin(mjm, mjd, seat_body, seat_world) -> int:   # ★ 中心を引数で受けない
    for c in ROUTE_CLIP_CENTERS:                      # 集合 = task の認可（import する）
        g = clip_geoms_at(mjm, mjd, c)                # 30mm XY 箱（既存 _clip_geoms）
        if len(g) not in (5, 6):                      # ★ 空集合は「未着座」ではない
            raise BrokenSelector(c, len(g))
        if inside(seat_world, capture_volume(g, c)):  # bar = built model（walls / floor / radius）
            return _activate(mjm, mjd, seat_body, seat_world)
    raise NotInAnyRouteClip(seat_world, ROUTE_CLIP_CENTERS)
```

### §15.2 ⭐⭐ 個数 assert は衛生項目ではない — 【scene ↔ task の整合トリップワイヤ】である

認可集合の中心に geom が無ければ **RAISE** ⇒ **task の clip 表と built scene の clip 表は【黙って食い違えない】。**
⇒ これはまさに **④ のドリフト**（built C2 = y 0.000 / `task_config` C2 = y +0.075）を **build 時に捕まえる**機構。
⇒ ⭐ **5-clip 一般化の「延期」は、規律ではなく【機構】で強制される** — C3 を認可集合に足した瞬間、scene が C3 を建てるまで authorizer は RAISE する。
⇒ **%12 提案 6（5-clip 延期）を批准。ただし理由を強化:「geom が無いから書けない」ではなく「書いたら機構が拒否する」。**

### §15.3 ✅ %12 提案 3 を批准 — assert 5 は「pin 候補のみ」に

filter は既存（`route_executor.py:774` / `policy_route_runner.py:311-315`）: `eq_type==CONNECT ∧ eq_obj2id==0 ∧ eq_active0==0`。
⇒ `assert sum(eq_active[pin_ids]) <= len(ROUTE_CLIP_CENTERS)`。（発火後も `eq_active0` は 0 のまま ⇒ filter は post-fire でも効く。）

### §15.4 ⭐⭐ %12 提案 4 を批准し、**置換先を指定する** — `mjm.neq` 不変 → **episode 終端の anchor 監査**

恒真 assert である（recompile 経路が無い）= %12 の指摘どおり。**だが置換先が本質。**
実際の bypass = 「authorizer を通さず `eq_active` / `eq_data` を書く」。それは authorizer 内部の assert では捕まらない。**grep（単一書込者）は【今日の tree】についての静的主張にすぎない。**

⇒ **runtime 不変条件に置け:**
```
episode 終端: ∀ eq  s.t. (eq_active == 1 ∧ eq_active0 == 0)          # = 発火した全 pin
    その world anchor eq_data[3:6] は
    ∃ c ∈ ROUTE_CLIP_CENTERS の捕捉体積の内側 でなければならない
```
⇒ ⭐ **これは【誰が書いたかを問わない】。bypass の証拠（どの経路 clip の外にもある anchor）は call graph ではなく model state に在るから。**
⇒ ⭐⭐ **そしてこれが、58 本の空中溶接（最高 880.9mm）を捕まえる assert である。明日 5 人目の書込者が足されても効く。**

### §15.5 ✅ %12 提案 5 を批准・**拡張** — 陽性対照を【レグ × side】で列挙

| # | 制御 | 動かす軸 | 期待 | 捕まえる穴 |
|---|---|---|---|---|
| P1 | C1 中心、z = **829.68**（pB 実測 k28） | — | **ACCEPT** | golden |
| P2 | z = **830.0**（アーチ浮き） | z | **ACCEPT** | 旧接触レグの罠 |
| N1 | z = **880.9**（史上最大の空中溶接） | z+ | REJECT | 空中 |
| N2 | z = **816.0** | z− | REJECT | clip の下 |
| N3 | x = C1x + **4.0mm** | x | REJECT | 壁の外（bar 3.5mm） |
| N4 | y = C1y + **20.0mm** | y | REJECT | y 窓（15mm）の外 |
| **N5** | **(300, +50, 810) = 支持 clip の溝の中** | **集合** | **REJECT** | ⭐ **①の穴。z のみの対照では原理的に見えない** |
| **N6** | **(400, 0, 829) = built C2** | **集合** | **ACCEPT**（認可集合 = (C1, C2) のとき） | 集合の**内容を文書化する**対照 |
| **N7** | 認可集合に `task_config` C2 **(0.40, +0.075)** を入れる | **selector** | **RAISE（BROKEN SELECTOR）** | ⭐ **④ の scene↔task ドリフト。「未着座」と印字してはならない** |

**N5 は 3 レグで三重に落ちる**（z 床 821 / 側方 50mm / y 100mm）。**N7 は個数 assert でしか落ちない。**

### §15.6 ✅ 床 bar（821）— %12 の擁護を批准。**そして正当化を差し替える**

%12 §5 の棄却（agent の「符号ミス」主張）は **正しい** — bar の目的は「cable が clip の **下**に居ない」であって「床に**接している**」ではない。**agent は設計が持たない意図で採点した。**
⚠ ただし %12 の R5/R6 は残る: **コメントの正当化**（`route_executor.py:3052-3054`「route env は spacer が無く 20mm 浮くので cable が下を通れる」）は、**gate が実際に走るシーンでは偽** — C2 には spacer がある（`newton_skill_env_base.py:1923-1926`、hx=0.020 / hy=0.015、z ∈ [800, 820] を充填）。

⇒ 🔒 **bar は【維持】。正当化を、反証が明らかにしたものに差し替える:**
> **床 bar 821 は、支持 clip の捕捉帯 (801, 816) を z 軸で棄却する【唯一の】レグである。**

⇒ ⭐ **支持 clip の発見が、床 bar を【遡って正当化した】。** 仮定的な「下を通れる cable」ではなく、**シーンに実在する 4 つの溝**が、その bar の仕事である。

---

## §16 🔒 残件 (a) (b) の裁定 — ⭐ (b) は **banked 数値に触る**

### §16.1 (a) `policy_route_runner.py:309` = **REPLACE**（緩めるのではない）

逐語 `:309`: `seated = bool(cable_c1_mm <= SEAT_DIST_MM and abs(seat_z_mm - groove_z_mm) <= SEAT_Z_TOL_MM)` / `:50-51` = **0.5 / 3.0**。**側方レグが無い。**
⇒ 私が §10 で殺した述語と**同一**。第 2 の現場であって、別の設計ではない。

- **偽陰性**: pB 実測 k28 = **+0.679mm 浮き** > 0.5 ⇒ **正しい捕捉を棄却**（今日はグリッパが押さえているので休眠）
- **偽陽性**: 溝の**脇の棚**に載った cable ⇒ 接触 0.0 ∧ |dz| 0.0 ⇒ **PASS ⇒ 溶接** ← ⛔ **危険側。休眠していない。今日 live。**

⇒ 🔒 **(a) = §15 の authorizer に差し替え。差し替えるまで、π-rollout で pin が発火する run は BLOCKING。**

### §16.2 ⛔⛔ (b) `SETTLED_IN_NOTCH` は 溝の【中】と溝の【脇】を **区別できない**（構成による証明・simulation 不要）

`route_executor.py:3881` 逐語:
```python
_c2_settled = bool(_cab_c2_rel <= 0.5 and abs(_z_c2_rel - (GROOVE_CENTER_Z + _clip_float_z) * 1e3) <= 3.0)
```
測定タイミング = `:3876-3878` = **両グリッパを開いて +90 step 後**（= **解放後**）。

**built model の箱表から（C2 も float +20mm: `newton_skill_env_base.py:1913` `TABLE_HEIGHT + dz + target_clip_float_z`）:**

| 箱 | x 範囲（中心 c から）[mm] | z 範囲 [mm] |
|---|---|---|
| base plate | **c ± 20.0** | 820.0 – **825.0** |
| 壁（左右） | c ∓ 7.5 … 10.5 | **825.0** – 840.0 |
| lip（左右） | c ∓ 11.0 … 15.0 | 840.0 – 850.0 |

⇒ **壁の【外】に base plate の棚が x = c ± 10.5 … ± 20.0 に露出している。棚の天端 = 825.0 = 溝の床と【同一平面】**（壁は base plate の上に立つ）。
⇒ 半径 4mm の cable が棚に載ると **中心 z = 825.0 + 4.0 = 829.0mm**。溝の中の静置 z = floor_top + R = **829.0mm**。**同一。**

**述語の実際の値**（cable 中心 x ≈ c + 14.5mm、壁の外面に接触、z = 829.0mm）:
- `_cab_c2_rel` = **0.0mm** ≤ 0.5 ✅ **PASS**（棚に載り壁に触れている）
- `|829.0 − 829.0|` = **0.0mm** ≤ 3.0 ✅ **PASS**

⇒ ⛔⛔ **`SETTLED_IN_NOTCH = True`。cable は溝の【外】、軸から 14.5mm、壁の【外側】に在る。**

🔒 **これは私が今夜 memory に書いた機構そのもの**（`feedback-a-gate-validated-under-the-bug-is-validated-by-the-bug-2026-07-15`、逐語）:
> 「手を放してから判定すると、脱出した cable は base plate に着地する。base plate の天端は溝の床と【同一平面】ゆえ、脱出した cable の z は【正確に groove_z】になり、clip に接触もする ⇒ (i) と (ii) は【両方緑】。(iii) だけが残る。」

⇒ **C2 成功述語は、まさにその【解放後】の状態を、まさにその (i)+(ii) で、(iii) 無しに測っている。**

**裁定 (b):**
1. ⛔ **banked C2 成功数は「溝に着座した」を測っていない。**「**溝の高さで clip に触れている**」を測っており、それは**棚の上でも真**。
2. ⚠ **「banked 成功は偽だった」とは言わない。**「**唯一効く軸で未検証**」と言う。**誤差の向きは UNKNOWN**:
   - 偽陽性（棚）が数を**膨らませ**、偽陰性（0.679mm 浮き）が数を**削る**。**両方 live で、打ち消し合わない。**
   - ⇒ 🔒 **床としても天井としても bank できない**（§運用15 の「verdict の conservatism 方向」= **UNKNOWN** ⇒ bank 不可）。
3. ✅ **再採点は安い — 再走行ではなく【再スコア】。** 必要なのは C2 近傍 cable body の **x** だけ。
   - ⚠ 記録されている `_c2_settle_rec`（`:3882-3888`）は **z しか持たない**（`near_c2_cable_z_released_mm`）⇒ **JSON からは再採点できない。**
   - ⇒ **qpos dump があれば offline 再スコア。無ければ replay（決定的・byte-repro 有り・訓練不要・GPU 不要）。**
   - ⇒ **pB 依頼: C2 run の解放後フレームで、C2 に最も近い cable body の `|x − c2x|` を出せ。bar = 3.5mm（壁内面 − 半径、built model 由来）。**

### §16.3 ⭐⭐ (a) (b) (§14①) は【同じ 1 つの欠陥】である

3 つの現場 — **pin gate**（`route_executor.py:3074`）/ **π-rollout**（`policy_route_runner.py:309`）/ **C2 成功判定**（`route_executor.py:3881`, `test:5540`, `policy_route_runner.py:1089`）— が、**同じ 2 定数（0.5 / 3.0）**を使い、**同じ盲目**を持つ:

> ⛔ **述語が「cable が溝の *中* に居るか」を【一度も問うていない】。**

**接触は壁の【両側】で 0 を取る。高さは棚の上で【同一】。** ⇒ **残る唯一の識別軸は側方であり、3 つとも測っていない。**

---

## §17 ⛔ ERRATUM（v1.5、2026-07-15 07:0x）— **§14.1 を撤回する。私の撤回 6 件目**

%12 が自らの ① を撤回した（`AUTHORIZE_CLIP_PIN_FALSIFICATION_RSTECHLEAD_20260715.md` §0 ERRATUM）。**私は on-disk で確認し、%12 が正しいと裁定する。そして私の §14.1 は同じ誤りを含んでいた。**

### §17.1 事実（私自身の on-disk 読み）

`_clip_geoms()` は **既に clip 中心で gate されている**。`route_executor.py:2200-2202` ≡ `test_newton_clip_routing.py:3854-3856`（逐語同一）:
```python
and abs(float(mjd.geom_xpos[g][0]) - x_clip) < 0.03
and abs(float(mjd.geom_xpos[g][1]) - y_clip) < 0.03
```
そして `:3848` のコメント逐語: 「the table (also worldbody) is centred far in Y -> **excluded by the XY gate**」
⇒ ⭐ **XY gate は【意図的な弁別器】であり、そう書いてある。**

| clip | 支持 clip (x=300) との X 距離 | 窓 30mm | 結果 |
|---|---|---|---|
| C1 / C3 / C5（x=350） | **50mm** | > 30 | ⇒ **排除** |
| C2 / C4（x=400） | **100mm** | > 30 | ⇒ **排除** |

⇒ ✅ **要件①（bar は model から）と要件②（clip の中でなければ RAISE）は【矛盾していない】。**

### §17.2 ⛔ 何を撤回するか

**撤回 = §14.1 の重大度主張**（「私の ∃-spec は cable を自分の初期支持治具に溶接することを認可する / frame 0 で到達可能」）。
**これは【model 全体を走査する authorizer】を仮定していた。そんな実装は存在しないし、書く理由もない** — `_clip_geoms(x_clip, y_clip)` が既に在り、中心を受け取るのだから。

**維持される事実**（§14① の表は正しいまま）: 支持 clip は実在する / 同一の 5 箱リテラル / 捕捉帯 (801, 816) / route env で既定 ON。
**⇒ しかし「存在する」と「選ばれる」は別。私は前者を検証し、後者を【一度も検証しなかった】。**

### §17.3 ⛔⛔ 加重事由 — 私は反例を【読みながら】論じ抜けた

本ターンで私は `route_executor.py:2190-2202` を**自分で読み**、自分の作業メモにこう書いた:

> 「C1 at (0.35, +0.150): |0.30 − 0.35| = 0.05 > 0.03 ⇒ support clips are EXCLUDED from C1's selector.」

**そして次の行で「だが危険は selector ではなく authorizer に在る」と書いて、自分が見た反例を迂回した。**
⇒ 🔒 `[[your-own-tool-output-holds-the-counterexample]]` の**再演**。見えなかったのではない。**見て、避けた。**
⇒ ⭐ 迂回の理由: **私は「自分の §12 の穴」を探しており、「その穴は既に塞がっているか」を探していなかった。** 探索の目的が、証拠の読み方を決めていた。

---

## §18 ⭐⭐ 統合 — **【境界の問い】と【同一性の問い】は別の問い**（%12 の synthesis を採用・拡張）

%12 の観察を採用し、**4 例目（私）と 5 例目（§16.2）を足す**:

| # | 誰 | 問うた（**境界**） | 問わなかった（**同一性**） | 帰結 |
|---|---|---|---|---|
| 1 | 歴史 audit | 「z は正しいか」 | 「**x** は正しいか」 | 58 本すべてが「高さ失敗」として記録された |
| 2 | p1 の control matrix | 「境界は主張どおりか」 | 「**主体は正しい対象か**」 | 全摂動が C1 中心**相対** ⇒ 50mm 先の clip に**原理的に到達できない**（p1 自ら受諾） |
| 3 | %12 の反証 | 「model は clip を区別できるか」 | 「**selector はそもそも model 全体を見るのか**」 | ①を誤って提起 |
| 4 | ⭐ **私（§14.1）** | 「∃-spec は支持 clip を認可するか」 | 「**再利用する selector は既にそれを排除しているか**」 | 反例を**読みながら**論じ抜けた |
| 5 | ⭐⭐ **`SETTLED_IN_NOTCH`（§16.2）** | 接触 ≤0.5mm（十分近いか）/ \|dz\| ≤3mm（正しい高さか） | 「**溝の【中】か、棚の【上】か**」 | **banked C2 成功数** |

⇒ 🔒 **述語は【境界レグを 2 本】持ち、【同一性レグを 0 本】持つ。**
⇒ ⭐⭐ **側方レグは「3 本目の境界」ではない。【唯一の同一性レグ】である。**
⇒ **だから外すと致命的であり、他の 2 本をいくら締めても回復しない。** 接触は壁の**両側**で 0 を取り、高さは棚の上で**同一**。**どちらも「どの対象か」について情報量ゼロ。**

⇒ ⭐ **これが、同じ欠陥が 3 現場（pin gate / π-rollout / C2 成功判定）に同時に在る理由である。** 3 つとも境界だけを測っている。

---

## §19 🔒 %12 の (1)-(7) への裁定（§15/§16 の更新差分のみ）

| # | 項目 | 裁定 |
|---|---|---|
| **(5)** | `x_clip` の env 既定 (0.40) が C1 実位置 (0.35) と食い違う | ⭐⭐ **本 arc の【真の穴】に昇格。** clip 中心が**唯一の弁別器**と分かった以上、`route_executor.py:2133-2134` の `os.environ.get("CLIP_X", "0.40")` は瑕疵ではなく**弁別器を未検証の既定値から供給している**。env 未設定 ⇒ 中心 (0.40, 0.0) = **built C2 の中心そのもの** ⇒ 「C1 gate」が**静かに C2 を採点する**。bar は正常に見え、raise もしない。⇒ 🔒 **既定を削れ。中心は caller が渡す**（caller は知っている: `newton_route_env.py:1306`）。⛔ **membership check では捕まらない** — (0.40, 0.0) は正当な経路 clip（C2）だから。**検証ではなく削除。** |
| **(1)** | 空集合がゴミ bar | ✅ 個数 assert を批准（§15.2）。⚠ **ただし「authorizer は何でも認可する」は【言い過ぎ】** — 現行 gate の**連言は REJECT する**（`_lat_bar_mm = 0.0 − 4.0 = −4.0` ⇒ `|dx| <= −4.0` は恒偽）。**fail-open ではなく fail-LUCKY**（§14.2）。⇒ **新規 authorizer にはその幸運が無い ⇒ 個数 assert は【必須】。** そして今日の gate でも**診断は嘘をつく**（「clip が無い」を「未着座」と印字）。 |
| **(2)(3)(4)** | assert 5 は golden で発火 / assert 4 は恒真 / 5-clip 延期 | ✅ **すべて批准**（§15.3 / §15.4 / §15.2）。assert 4 の**置換先 = episode 終端の anchor 監査**（誰が書いたかを問わない ⇒ 58 本を捕まえる）。 |
| **(6)(7)** | π-rollout の接触レグ / C2 成功判定 | ⛔ **§16 のまま。①の撤回は §16 に【一切触れない】** — 棚の構成は支持 clip と独立。**(7) が本 arc で最も blast radius が大きい。①の撤回で埋もれさせるな。** |
| **signature** | `authorize_clip_pin(..., clip_xy)` | ✅ **%12 の処方を採用**（私の §15.1「引数では機構にならない」は**弱める**）— 中心は**元から**弁別器であり、caller は知っている。**加えて** 認可集合 `ROUTE_CLIP_CENTERS` への membership check を 1 行入れる（支持 clip 中心を渡す caller を機構で拒否）。⚠ ただし上記のとおり **(5) は membership では防げない ⇒ env 既定の削除が本体。** |

---

## §8 接地

| ソース | cite |
|---|---|
| cable 構造 | `test_newton_clip_routing.py:1000`（`add_joint_free` = root 6-DOF）/ `:1009`（`axis=(1,0,0)` = 単一 bend 軸） |
| clip 幾何 | `newton_skill_env_base.py:1847-1853`（`_v_groove_clip_parts` 5 box）= producer `test_newton_clip_routing.py:1169-1175`（同一値） |
| clip 配置 | `task_config.py:202-204`（CLIP_Y_SPACING 0.075 / CLIP_X_ODD 0.35 / CLIP_X_EVEN 0.40）/ `:136`（CABLE_SEG_LEN 0.015） |
| gate 実体 | `route_executor.py:554-625`（channel from built model + tripwire）/ `:628-643`（cable radius）/ `:665-670`（レグ）/ `:680-724`（拒否メッセージ）/ `:727-807`（activate、全失敗 RAISE） |
| pin eq 制約 | `route_executor.py:770-775`（pre-allocated + 初期無効 CONNECT-to-world のみ） |
| 静窓 dt | `seatgate_verify_20260714/r7_B0_rsCell_NOPIN/route_demo_raw_meta.json`（`dt` = 0.00208 s/frame） |
| fidelity boundary | `RS71-System-Spec-SSOT.md:62`（Rs DECISION B2、2026-06-25） |
| D-5 | `CANONICAL_MOTION_TABLE_V1.md:184` / `:110-111` + `shared/GEOM_WITNESS_5CLIP_p5_20260714.py` |
| STEP 7/8/9 | `CANONICAL_MOTION_TABLE_V1.md:49` / `:50` / `:51`（指状態）+ `:126` / `:127` / `:128`（secured-predicate） |
| **支持 clip ×4**（§14①） | `newton_skill_env_base.py:1822-1828`（5 箱、`:1848-1854` と逐語同一）/ `:1829`（y 4 点）/ `:1833`（float 無し）/ `newton_route_env.py:701` + `:449`（route env 既定 ON）/ `task_config.py:231`（`GRASP_X = 0.30` =「Cable initial X position」） |
| **構造 eq 6 本**（§14③） | `newton_skill_env_base.py:1646-1647`（4× connect `enabled=True`）/ `:1664-1670`（2× follower-mirror `enabled=True`）/ `test_newton_clip_routing.py:1628`（`_want_neq = 6 + N`） |
| **scene↔task ドリフト**（§14④） | `route_env_config.py:140`（`ROUTE_C2_XY = (0.40, 0.000)`、逐語「`!= task_config (0.40, 0.075)`」）/ `route_executor.py:2190-2202`（selector = 30mm 箱、個数 assert 無し）/ `:2133-2134`（`CLIP_X` 既定 `"0.40"` / `CLIP_Y` 既定 `"0.0"` = **built C2 の中心**） |
| **空集合の bar**（§14.2） | `route_executor.py:3031-3071`（`default=0.0` ⇒ `_lat_bar_mm = −4.0` 恒偽 ⇒ **fail-lucky**；`_z_hi = 8,999,999,996.0` = z レグのみ fail-open） |
| **C2 の棚**（§16.2） | `newton_skill_env_base.py:1913`（C2 も `+ target_clip_float_z`）/ `:1848-1854`（base plate hx=**0.020** vs 壁 外面 ∓10.5mm ⇒ 棚 = c ± 10.5–20.0、天端 825.0 = 溝床と同一平面）/ `route_executor.py:3881`（`_c2_settled`）/ `:3876-3878`（**解放後**に測る） |
| **同じ 2 定数の 3 現場**（§16.3） | `route_executor.py:3881` / `test_newton_clip_routing.py:5540` / `policy_route_runner.py:1089` + `:50-51`（`SEAT_DIST_MM=0.5` / `SEAT_Z_TOL_MM=3.0`）/ `policy_route_runner.py:309` |
| **反証 artifact** | `AUTHORIZE_CLIP_PIN_FALSIFICATION_RSTECHLEAD_20260715.md`（%12、2026-07-15 06:3x） |
| **no-repeat guard** | `check_thread_vault_prior_art.sh --fail-on-blocker "SETTLED_IN_NOTCH" "c2_settled" "seat predicate lateral" "SEAT_DIST_MM"` ⇒ **PASS**（findings=0 blockers=0、2026-07-15 06:2x）= 本 §16.2 の主張は既往の再導出ではない |
