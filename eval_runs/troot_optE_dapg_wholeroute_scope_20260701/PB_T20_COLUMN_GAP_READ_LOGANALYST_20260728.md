# pB — t20 trace の「column gap」を読む（p18 `-704` / `-708`・Rs 指示 → p4 依頼 台帳 405）

**測定者:** LOG-ANALYST (`w2:pB`)。**発行:** 2026-07-28 19:33 JST（date-THEN-write）。
**問い（p4 逐語の要旨）:** column gap の値は「**動く部品がマストへ到達している**」のか、「**恒常的に重なる何かで値が変わらない**」のか。
⛔ **numeric 単独 PASS は出しません。** 視覚レグ = pC、最終 = Rs の動画判定。
⛔ **空隙は推測で埋めません。** §3 = 決められること／§4 = 決められないこと に分けます。

---

## 0. 読んだもの（pin）

| 対象 | pin |
|---|---|
| trace | `p4_ur15_sim_20260727/T20_RUN_TRACE_20260728.txt` @ `c65e0efc8b`・内容 sha256 `d2cd4bcccb2e0d277f9183be743348c46a5d3d701a736ecfcc7eb652711f33e8`（p18 申告と一致・284 行） |
| producing driver | `ur15_steps_wired.py` @ `5f477f53e5`（p18 便）・sha256 `27612e1f904f72d31b11bcd136507c0383f7b6eaf8fa91e348537b29d6932bd0` |
| 同 @ `c65e0efc8b` | sha256 `89a7fe5c1bf6ad499a321292f89bee27d6f264d1d96ba244c3dce94b08f6345a` |
| cell 定数 | `ur15_cell_spec.py` @ `c65e0efc8b` |
| 腕の body 木 | `<p4 scratch>/ur15_base.xml`・sha256 `1e182d10e35153adf0b03759b2574083534b69728b3fa81607a92d15740954aa`・**mtime 2026-07-27T02:10:15**（t20 走行より前・以後 未変更）⚠ off-git・**as-read 2026-07-28 19:2x** |
| 参照（p18 便を実読で確認） | `run_logs_20260728/run_t14.txt:277` @ `e9a27e28ec` |

⭐ **版の射程（先に述べます）:** `5f477f53e5` → `c65e0efc8b` の driver 差分は **`vertical_cap_deg()` の 1 箇所のみ**（13 挿入 / 5 削除）。⇒ **`column_gap` / `ARMG` / `COLG` はこの区間で 1 文字も変わっていません。**⇒ 本書の機構の読みは、producing 版がこの区間のどれであっても同じです。

⚠ **1 点だけ食い違いを記録します（判定しません）:** trace 末尾の traceback は `line 2029, in <module>` として **`print(f"[steps] STEP{num} {t}: fingers …`** を表示していますが、`5f477f53e5` の 2029 行は `raise RuntimeError(` で、この print が 2029 行に在るのは `c65e0efc8b` の版です。Python は traceback 整形時に source を読み直すので、⛔ **「走った code」と「表示された source」がずれ得ます**。どちらが producing かは trace からは決まりません（上記のとおり本件の結論には影響しません）。

---

## 1. 計器の定義（producing 版の code・逐語）

`ur15_steps_wired.py` @ `5f477f53e5` `:1092-1102`:

```python
def column_gap(t, dd=None):
    """Closest signed distance from this arm's geoms to the yoke column, in mm.  Negative means the
    arm is inside the column.  mj_geomDistance is a geometry query, so it reports this whether or
    not the pair can collide -- which matters here because I had switched the column's collision
    off, so nothing was stopping the arm from sweeping through the mast."""
    dd = dd if dd is not None else d
    best = 1e9
    for g in ARMG[t]:
        for c in COLG:
            best = min(best, mujoco.mj_geomDistance(m, dd, g, c, 1.0, None))
    return best * 1000.0
```

読み取れる性質:
- **これは最小値**です（`min` を全 pair で畳み込む）。`ARMG[t]` は片腕 38 geom（trace `:15`）、`COLG` は `("stem", "foot")` の 2 geom（`:1076`）⇒ **1 側あたり 76 pair の最小**。
- **上限（cap）は `distmax = 1.0 m` = 1000 mm。** 1 m より遠い pair、および評価できない pair は 1000 を返し、⇒ **最小値を下げません**（最小値には現れない）。
- 印字は `:2222` の `{:+7.1f}` ⇒ **分解能 0.1 mm**、⭐**符号は保存されます**（実測: `-0.04 → "-0.0"` / `+0.04 → "+0.0"`）。
- 柱は原点の 1 本（`:218-220`）: `stem` = 半径 `COLUMN_R` の円柱で **z ∈ [0, 1.5300]**、`foot` = 半径 `PEDESTAL_R` の低い台。

---

## 2. 生値（全 13 行・trace 逐語）

| STEP | trace 行 | L | R |
|---|---|---|---|
| 2 | `:42` | +112.3 | +180.2 |
| 3 | `:70` | **+0.0** | **−0.6** |
| 4 | `:105` | +73.9 | **−0.6** |
| 5 | `:117` | **+0.0** | **−0.6** |
| 6 | `:129` | +200.0 | **−0.6** |
| 7 | `:145` | +200.2 | +130.0 |
| 8 | `:161` | +201.2 | ⭐ **+387.5** |
| 9 | `:180` | ⭐ **+202.1** | +328.2 |
| 10 | `:192` | +199.0 | **−0.0** |
| 11 | `:204` | +199.4 | **−0.6** |
| 12 | `:216` | +199.4 | **−0.6** |
| 13 | `:235` | +199.4 | **−0.6** |
| 14 | `:265` | +199.4 | **−0.6** |

**私の機械 count**（p18 `-704` の数と一致）:
- R: **−0.6 が 8**（STEP 3,4,5,6,11,12,13,14）／**−0.0 が 1**（STEP10）／正値 4（STEP 2,7,8,9）
- L: **+0.0 が 2**（STEP 3,5）／**+199.4 が 4**（STEP 11-14）／その他 7

⭐ p4 message の「13 step 中 10 で −0.6」は artifact と一致しませんが、⭐**p4 は既に自己訂正済**です — `ffbc1f15af` の comment 逐語「it read negative at EIGHT steps of thirteen -- nine counting the one that read exactly zero … (I first wrote ten, from memory of the printout rather than from a count of it; p18 counted the banked trace.  The steps are 3, 4, 5, 6, 11, 12, 13, 14 at -0.6 mm and 10 at -0.0.)」⇒ **本件は決着済で、私は蒸し返しません。**

---

## 3. ⭐ 決められること（CAN）

### 3-1. ⭐⭐⭐「恒常的に重なる何かで値が変わらない」は **trace 自身が反証しています**

印字値は **最小値** です（§1）。⇒ もし query 集合の中に **常にマストと重なっている geom が 1 つでも在れば、その pair は常に負を返し、最小値は全 step で ≤ 0 になります。**

**観測された最大値:**
- **R = +387.5 mm**（STEP 8・`:161`）
- **L = +202.1 mm**（STEP 9・`:180`）

⇒ ⛔ **その step において、query が評価した全 geom はマストから 387.5 / 202.1 mm 以上離れていました。**
⇒ ⛔ **したがって、どちらの腕にも「恒常的に重なっている geom」は query の中に在りません。**

**この主張の射程:**
- ⭐ **堅い**: 1 m 超の pair や評価不能の pair は 1000 を返して最小値に現れませんが、それは**最小値を下げない**方向なので、上の論法は影響を受けません。
- ⛔ **言えないこと**: 「重なっているものが *どこにも* 無い」ではありません。**query に入っていない部品**（`COLG` は `stem`/`foot` の 2 個のみ、`ARMG` は片腕 38 個）は、この論法の外です。

### 3-2. ⭐⭐ 「−0.6 は計器の床（clamp）だ」も反証されています

同じ計器・同じ関数が、**別 run で −26.3 mm を印字しています** — `run_t14.txt:277` @ `e9a27e28ec` 逐語「`[steps] WORST R: column gap   -26.3 mm at STEP10 t=23.0s   <- INSIDE THE COLUMN`」（私が git show で実読）。
⇒ ⛔ **−0.6 は計器が下に張り付いた値ではありません。**この計器は −26.3 を出せます。

### 3-3. ⭐⭐⭐ mount（column body の子）は **マストの中に在りません** — p4 の除外の根拠が artifact と合いません

**p4 の主張**（`0b0d4c462f` の新 comment 逐語）: 「Each arm is attached to the mast, so its first body is a CHILD of the column body and **its geoms sit inside the mast by construction** -- that is the mount, not a crash.」
⇒ この主張に基づき `MOUNTG = {g | body_parentid[geom_bodyid[g]] == COLB}` を **無条件除外**しています。

**実読した body 木**（`ur15_base.xml`・`<worldbody>` 直下）:
- `<geom type="mesh" mesh="base"/>` = ⭐ **arm の worldbody 直属の geom** ⇒ `attach_body(_a.bodies[1], …)` では **付いてきません**（cell の中に base の geom は無い）
- `bodies[1]` = **`shoulder_link`**（`pos="0 0 0.2186"`・`shoulder_pan_joint` を持つ・geom は `shoulder` mesh 1 個）
⇒ ⭐ **`MOUNTG` の中身は左右の `shoulder_link` の geom 2 個**です。

**算術**（`ur15_cell_spec.py` の値 + XML の pos から。柱は原点・`stem` は半径 0.102 m・z ∈ [0, 1.5300]）:

| 量 | 値 |
|---|---|
| `SHOULDER_HEIGHT` = 0.37 + 0.58×2 | 1.5300 m（= stem の天端と同じ高さ） |
| `YOKE_SPREAD` | 0.40 m |
| `TILT` = π/2 − 20° | 70.0 deg |
| 取付フレーム原点 → stem 表面 | **298.0 mm** |
| `shoulder_link` の body 原点（フレーム + 0.2186 m を 70° 傾けた先）→ stem 表面 | **508.9 mm** |

⇒ ⭐ mount の geom が「マストの中」に在るためには、**body 原点から 508.9 mm（フレーム原点から数えても 298.0 mm）マスト側へ張り出す mesh** が要ります。
⇒ ⭐ しかも `shoulder_link` は自分の関節軸まわりに回るだけで、**body 原点は動きません**（508.9 mm は姿勢によらず一定）。
⇒ ⛔ **「by construction 内側」は成立しません。**§3-1 の最大値（R +387.5）とも独立に整合します（**+387.5 mm ≒ mount の固定スタンドオフ**として無理がなく、算術上は mesh が原点から 121.4 mm 張り出す形）。

⚠⚠ **帰結（p4 への risk）:** ⛔ **`MOUNTG` を除外しても −0.6 は消えません。**−0.6 を出しているのは mount ではない別の部品です。⇒ **「負値は mount だった」と読んで除外で片付けると、実在する干渉が黙ります。**
⭐ **反証テスト（p4 の再走行 1 本で決着）:** 除外を入れた版で、R の読みの**最大値が +387.5 を超えるか**を見る。超えれば +387.5 は mount だった（＝除外は floor を上げただけ）。超えず、しかも **−0.6 が残る**なら、除外は −0.6 に対して無効だったと確定します。

### 3-4. 印字の読み方 — `+0.0` と `−0.0` は別の事実です

`{:+7.1f}` は符号を保存します（実測済）。⇒
- **L の `+0.0`（STEP 3, 5）= 外側から 0〜0.05 mm** = ⭐**接触（貫入していない）**
- **R の `−0.0`（STEP10）= 内側へ 0〜0.05 mm** = ⭐**わずかに貫入**
⇒ ⛔ **「+0.0 だから離れている」と読めません。**両方とも「触っている」です。

### 3-5. ⭐⭐ 対照 — 同じ値の繰り返しが「姿勢が同じ」で説明できるのは L だけです

| | 繰り返し | その step の手先位置 |
|---|---|---|
| **L** | **+199.4 が 4 回**（STEP 11-14） | ⭐ **4 step とも同一** `L mouth[-0.003 +0.409 +0.136]`（`:209/:221/:240/:270`） |
| **R** | **−0.6 が 8 回**（STEP 3,4,5,6,11,12,13,14） | ⛔ **7 通りの別姿勢**（STEP3 と 4 のみ同一）。x が +0.207〜+0.490（283 mm）／y が −0.541〜−0.737（196 mm）／z が +0.218〜+0.400（182 mm） |

⇒ ⭐ **L 側は「姿勢が止まっている → 値も同じ」という素直な対照**になっています。
⇒ ⭐⭐ **R 側は姿勢が 283 mm 動いても値が 0.1 mm 単位で同じ。**⇒ **R の最小値を決めている部品は、手先を動かしている関節では動いていません**（＝ 腕の付け根寄り、または動きが最小値に効かない部品）。
⇒ ⛔ **ただし §3-3 より、それは mount そのものではありません。**

### 3-6. ⭐⭐ Rs の観察は **左手**、trace の負値は **全部 右**

p4 の comment が引く Rs 逐語（`0b0d4c462f`）:「**the left hand is slamming into the cylinder**」。
trace では **L は 1 度も負になりません**（最小 = `+0.0`・STEP 3 と 5）。負値は 13 step すべて R 側です。
`run_t14.txt:275` も同型 —「`WORST L: column gap +0.0 mm`」／「`WORST R: column gap -26.3 mm`」。
⇒ ⭐ **2 本の run で同じ左右非対称**（L は触れるが貫かない・R は貫く）。
⇒ ⭐ **Rs の観察に対応する trace 上の証拠は、R の −0.6 ではなく L の `+0.0` 2 step の方です**（＝ 接触。§3-4 のとおり「離れている」ではありません）。
⛔ 「Rs が見たものと L の +0.0 が同一の事象か」は判定していません（視覚レグ = pC / Rs）。

---

## 4. ⛔ 決められないこと（CANNOT）— trace に必要な情報が無い

| # | 決められないこと | なぜ（trace 側の欠落） |
|---|---|---|
| 1 | ⭐**どの geom pair が各値を出しているか** | column gap 行に geom 名が無い（p4 自認）。⇒ **−0.6 の主が「手」なのか「肘・前腕」なのかは trace からは出ません。** |
| 2 | −0.6 が **接触の静定深さ**（solver が保持する貫入）か、無接触の幾何量か | trace に **腕↔マストの接触リストが在りません**。`PENETRATION` 行は clip↔cable 専用（t20 の非 clear 7 件はすべて clip↔cable）。 |
| 3 | 8 step で **肩関節角が同じか** | ⛔ **STEP1 以降、関節角の印字が 1 つも在りません**（`joint err` は STEP1 の 2 行のみ）。⇒ §3-5 の読み（付け根寄りの部品）は**姿勢データで裏づけられません**。 |
| 4 | column の **collidability の実状態** | producing 版の docstring は「I had switched the column's collision off」と**著者証言**として述べ、`0b0d4c462f` はこの文を**裁定なしに削除**。機構（実際に切っている箇所）は p18 の grep でも未特定 ⇒ ⛔ **UNVERIFIED（私も特定していません）**。⭐ ただし **両版の docstring が一致する点** =「`mj_geomDistance` は collidability と無関係に幾何を返す」⇒ **−0.6 は幾何量であって接触の有無に依存しません**。 |
| 5 | run 全体の最悪接近 | ⛔ **t20 に `WORST` 行が在りません**（§6 のとおり未完走）。⇒ t14 の −26.3 と t20 を「同じ量の比較」として並べられるのは per-step 行までで、run 全体の最悪値は t20 側に存在しません。 |

⚠ **計器の形が run 間で変わっています**（p18 `-708` の指摘を私も確認）: t14 には run 全体の `WORST … <- INSIDE THE COLUMN` が在り、t20 には在りません。⇒ ⛔ **t14 の −26.3 と t20 の −0.6 を「同じ計器の 2 回の測定」として直接比べないでください**（前者は run 全体の最悪値、後者は step 終端の瞬時値）。

---

## 5. ⭐ 決められるようにする最小の変更（既に半分 p4 が実装済）

1. ⭐**勝った pair の名前を column gap 行に出す。** これは能力の不足ではありません — **同じ trace の同じ step が、他の 2 つの欄では既に geom を名指ししています**: `ARM-TO-ARM: closest +0.0 mm (11 <-> 67)`（`:45`）と `ARM REACH: … (geom42)`（`:71`）。
   ⇒ ⭐ **p4 は `0b0d4c462f` で既に実装済**（`want_who` が `f"{GNAME[g]} vs {GNAME[c]}"` を返す）。⇒ **足りないのは再走行だけ**で、それまで banked の 13 個の数値は**帰属不明のまま**です。
2. §3-3 の反証テスト（除外後に R の最大値が +387.5 を超えるか／−0.6 が残るか）。
3. （§4-3 向け）負値を出した step の **6 関節角**を 1 行足す。「同じ姿勢だから同じ値」かどうかが、それだけで決まります。

⛔ 実装も走行も **p4 の court** です。私は測っただけです。

---

## 6. この run の素性（判定の前提として要る）

- ⛔ **未完走**: 末尾は STEP15 R の `RuntimeError`（fingers 11.2 deg off straight down・許容 5.73 deg）。⇒ `WORST` 行なし・`gates` 行なし。
- ⛔ **R は全域で指令から大きく外れています**: `STEP14 両手クランプ … R=1067.4mm`（tool 誤差 1.07 m）。手先は `R mouth[… y −0.541〜−0.737 …]` = **テーブルとは反対側**（テーブルは y 正側、柱は y=0）。
  ⇒ ⭐ **R の column gap は「指令位置から 1 m ずれた腕」で測られた値**です。§運用 上、これを「設計どおりの姿勢での干渉量」と読むことはできません。
- 参考: t20 の `PENETRATION` 非 clear は 7 件、すべて **clip↔cable**（0.3〜1.8 mm）。腕↔マストではありません。

---

## 7. ⛔ 私が主張しないこと

1. **どの部品がマストに当たっているか**（§4-1）。geom 名が無い以上、名指ししません。
2. **−0.6 の物理的な成因**（接触の静定か、無接触の幾何か）。§4-2。
3. **column の collision が実際に切れているか**。著者証言のみ・機構未特定（§4-4）。p18 の UNVERIFIED と同じ位置です。
4. **視覚判定**。Rs が見たものと trace のどの行が同じ事象かは、私の court ではありません。
5. **p4 の除外（`MOUNTG`）の可否**。私が言えるのは「その**根拠**が artifact と合わない」ことと「**除外しても −0.6 は消えない**」ことまでで、除外を入れるか否かは設計判断です。
6. **PASS / FAIL**。本書に verdict は在りません。
7. off-git の scratch 2 ファイル（`ur15_base.xml` 等）は **as-read**（2026-07-28 19:2x）であって banked ではありません。`ur15_base.xml` は t20 走行より前の mtime で以後変わっていませんが、⛔ **commit で固定された証拠ではありません。**

---
**pB LOG-ANALYST measurement / 2026-07-28 19:33 JST**

---

# 追記 §8 — 2026-07-28 20:09 JST（追記のみ・上の判定は 1 つも変えません）

**きっかけ:** p18 `-725`（FYI・依頼なし）。**私が自分で読んだもの:** `T22_RUN_TRACE_20260728.txt` @ `4c2cd5dc77`・内容 sha256 `a6bc06a4cb841fee3e1437d509fd95b6d1d05c23b6b2f2d11cec8486dd066867`（p18 申告と一致・349 行）＋ 同 commit の driver。

## 8-1. ⭐⭐⭐ 計器が部品を名指しし、§3 の 2 つの反証が直接確認されました

t22 の mast 行は `mast L=+X mm (gN vs stem) R=+Y mm (gM vs stem)` の形になりました。R 側 14 行の勝者と値:

| 勝者 | 出現 | 値 |
|---|---|---|
| **g43** | 11 回 | **−0.6 / −0.6 / −0.5 / −0.6 / −0.6 / −0.6** と **+23.5 / +28.6 / +60.7 / +73.1 / +124.3** |
| g44 | 1 回 | +429.9 |
| g42 | 1 回 | +432.9 |
| **g67** | 1 回 | **−1.1** |

⇒ ⭐⭐⭐ **同じ 1 個の geom（g43）が、負の値も正の値も出しています。**⇒ **「動く部品がマストへ到達している」で確定**（マストに入り、出て、また入る）。§3-1 の反証が**名前つきで**裏づけられました。
⇒ ⭐ **R 側でマストに入る部品は 1 個ではありません** — g43 のほかに **g67 が −1.1 mm**。
⇒ L 側の勝者は g7 / g9 / g29 の 3 種で、**g9 が `+0.0`**（= 接触。§3-4 の読みどおり）。

## 8-2. ⭐⭐ mount は、除外を外しても一度も最小値を取りません

p4 は `4c2cd5dc77`「Drop an exclusion whose reason was refuted, and name the part」で **`MOUNTG` を撤去**しました（`COLFREE = {t: sorted(ARMG[t]) for t in SIDES}` — 差し引きなし）。
⇒ ⭐ **t22 では mount geom も query に入っています。それでも R の勝者は 11/14 が g43、残りも g44 / g42 / g67 で、mount は一度も勝ちません。**
⇒ ⭐⭐ **§3-3 の結論（mount は −0.6 の主ではない／除外しても消えない）は、実測で確認されました。**
⇒ ⛔ **§3-3 の反証テストは不要になりました**（前提の除外が撤去されたため）。⭐ 名前印字が直接答えます。

## 8-3. ⚠ 自己訂正 — §3-3 の推測 1 行を取り下げます

§3-3 末尾に「**+387.5 mm ≒ mount の固定スタンドオフとして無理がない**」と書きました。t22 では **+429.9（g44）/ +432.9（g42）** の位置に立つのは mount ではない別の部品で、mount は勝ちません。
⇒ ⛔ **「t20 の +387.5 は mount だった」という読みは支持されません。取り下げます。**
⚠ ただし **§3-3 の結論は変わりません** — 結論が乗っているのは ①最小値の論法（§3-1）と ②算術（フレーム原点 298.0 mm / body 原点 508.9 mm）であって、+387.5 の帰属ではありません。
⛔ t20 の +387.5 がどの geom だったかは、**依然として決まりません**（t20 の行には名前が無く、t22 は別 run・別 code）。

## 8-4. ⭐⭐ §4-2（−0.6 は接触か）に **t22 側の答え**が出ました — ただし t20 側は未決のままです

t22 `:101` / `:262` 逐語（GRASP R / REGRASP R）:
`WHY IT DID NOT ARRIVE -- worst joint j1 short by -1.606 rad`（REGRASP は `-1.728 rad`）; `act force [ 25.3 433. 8.5 0. 0. 0. ] N.m of (433.0, 433.0, …)`; `at its limit = [False, True, False, False, False, False]`; **`touching ['column (via g43)']`**

⇒ ⭐ **接触リストに柱が載っています**（`touching()` の読み）⇒ **t22 では腕↔柱の接触が実在**し、**関節 j1 が 433 N·m の上限に張り付いた状態で押し当てている**。⇒ −0.6 は「押し当てたまま静定した貫入」と整合します。
⇒ ⛔ **t20 側は banked のまま未決**です（t20 の trace に接触リストが無いのは §4-2 のとおり）。t22 の答えを t20 に持ち込みません（別 run・別 code）。

⚠ 関節番号の対応は自分で確認しました: driver `:1770` が `_worst = int(np.argmax(np.abs(qerr)))` で `j{_worst}` と印字 ⇒ **0 始まりの添字**。⇒ `j1` = 6 要素ベクトルの **index 1** = `J6`（`:64` = URDF の運動学順）の **2 番目の関節**。`at its limit` と `act force` の True / 433 も同じ index 1 に立っています。

## 8-5. ⭐⭐ 朝の numeric レグ（t8）と繋がりました

私の朝の記録 `PB_RUNLOGS_20260728_NUMERIC_LOGANALYST_20260728.md` は、t8 の `REGRASP R` を **`servo did not arrive`・6 要素ベクトルの index 1 が −1728.4 mrad** と記録し、⛔ **原因は未判定**としていました（同書 §2-2）。

| | t8（`run_t8.txt:199` @ `823ddf963e`） | t22（`:262` @ `4c2cd5dc77`） |
|---|---|---|
| 未到達の関節 | index 1 | `j1` = index 1 |
| 不足量 | **−1728.4 mrad** | **−1.728 rad** |
| 原因の印字 | ⛔ なし | ⭐ `at its limit` = index 1 が True・**433 N·m**・`touching ['column (via g43)']` |

⇒ ⭐ **同じ関節・同じ不足量（有効数字 4 桁で一致）が 2 本の run に出ており、t22 の側にだけ原因が印字されています** = 右腕が **g43 でマストに押し当たり、j1 がトルク上限に張り付いて動けない**。
⇒ ⭐ 朝の記録が「p4 の依頼文が触れていない」と挙げた **t8 の `WORST R: column gap −25.8 mm at STEP13 t=29.1s`**（同書 §4）は、t22 の `:341`「`WORST R: mast -24.5 mm at g43 vs stem, STEP13 t=29.1s`」と **同じ step・同じ時刻**です。
⚠ **射程**: t8 と t22 は別 run・別 driver 版です。⇒ ⭐**同型の反復**として述べるまでで、⛔ **同一事象とは言いません**。数値の一致（−1.728 rad）も、独立な 2 回の観測が一致した事実であって、同一性の証明ではありません。

## 8-6. ⛔ この追記でも決まらないこと

1. **t20 の 13 個の値の帰属**（どの geom か）。t20 の行に名前が無いことは変わりません。
2. **g43 / g67 / g42 / g44 がそれぞれ腕のどの部品か**。t22 は geom 番号までで、body 名を印字していません。
3. **柱の collidability の実状態**（§4-4）。⚠ ただし t22 の `touching` は接触リスト由来なので、⭐ **少なくとも t22 では腕↔柱の接触が生成されています**（＝ その pair は無効化されていない）。t20 については依然 UNVERIFIED。
4. **raw と banked の byte 同一**（p18 `-725`(iii)）。p4 の宣言であって、私は banked 側しか読んでいません。
5. **PASS / FAIL**。本追記にも verdict は在りません。視覚レグ = pC、最終 = Rs。

---
**pB LOG-ANALYST append / 2026-07-28 20:09 JST**
