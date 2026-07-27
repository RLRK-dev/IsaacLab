# P5 仕様 — UR15 cell 定数の単一出所 (SSOT)

**Owner** = w2:p5 SKILL-DETAIL-DESIGN ・**0-commit** (bank = w2:p4)
**起動** = Rs ・依頼 = w2:p18 `-201` (クリップ設計 `-195` の scope に追加) ・**根拠** = DDR #46 + w2:p6 実測
**兄弟文書** = `P5_UR15_CLIP_DETAIL_DESIGN_20260727.md` (sha256 `32360b20…`) — クリップの形はそちらが正
**作成** 2026-07-27 ・⛔ 本書の数はすべて私が on-disk を実読・機械抽出して出しました

---

## §0 規則 (これだけ)

> ⭐ **driver は定数を定義しない。1 つの module から読む。**
> ⭐ その module は、**権威ある出所が在る量は そこから取り**、**無い量だけ 本 spec の値を持つ**。

---

## §1 測定 — 「そのクリップ」だけでなく「その cell」が 1 個ではありませんでした

**方法**: `p4_ur15_sim_20260727/*.py` **12 file** を AST で解析し、module 直下の代入を全部抽出して突き合わせ (⭐ grep でなく構文木 ⇒ 取りこぼしなし)。

⇒ ⛔ **値が食い違う定数 = 21 件。** うち **物理を変えるもの = 10 件**:

| 定数 | `ur15_cell` / `ur15_route` | `ur15_steps*` 3 本 | 差の意味 |
| --- | --- | --- | --- |
| **`CABLE_R`** | **0.005** | **0.004** | ⛔⛔ **Ø10 対 Ø8** — 別のケーブル |
| **`CABLE_N`** | **40** | **32** | リンク数 |
| **`CLIP_H`** | **0.070** | **0.026** | 壁の高さ (w2:p6 発見) |
| `TABLE_HX` | 0.95 | 0.70 | 台の長さ |
| `TABLE_HY` | 0.30 | 0.20 | 台の幅 |
| **`YOKE_SPREAD`** | **0.22** | **0.40** | ⚠ 本日 私が 118 mm と誤った量 |
| **`TILT`** | **45°** | **20°** | ヨーク角 |
| `CLAMP` | — | 255 / **236** (`c1seat` のみ) | 閉じ指令 |
| `OPEN` | — | 0 / **18** | 開き指令 |
| `HALF` | — | 170 / **214** | 半保持 |

⭐ 残り 11 件は run 固有で正当な差 (`OUT` `W` `H` `HOLD_S` `WAY` `ARMATURE` ほか導出式) ⇒ §5。

⚠ **形そのものも違います** (定義の有無): `CLIP_RISER` `REST_TOP` `REST_Y` `Z_SEAT` `CLIP_Y_ODD` `GRIP_HALF_SPAN` は **`ur15_steps` 系にしか存在しません** ⇒ `ur15_cell` / `ur15_route` の cell には rest 台も riser も無く、⭐ **同じ名前の cell が 2 種類**あります。

---

## §2 ⛔⛔ 最重要 — **「正しい方の script」は存在しません**

| 定数 | 権威ある値 | `cell`/`route` | `steps*` |
| --- | --- | --- | --- |
| `CABLE_R` | **0.004** (`task_config.py:137`) | ⛔ 0.005 | ✅ 0.004 |
| `CABLE_N` | **40** (`task_config.py:135`) | ✅ 40 | ⛔ 32 |

⇒ ⭐⭐ **一方は半径で外し、他方はリンク数で外しています。** ⇒ ⛔ **どちらかを選んで写す、という直し方は成立しません。** ⇒ ⭐ **これが「1 つの出所から読む」以外に手が無い理由です** (本 spec の存在理由)。

⭐ **3 件目**: `task_config.py:135` 逐語 `CABLE_SEGMENTS = 40  # 40 segments × 15mm = 600mm` ⇒ **1 節 = 15 mm**。⛔ **p4 の全 driver は `CABLE_SEG = 0.030` (30 mm)。**
⇒ ⭐⭐ **帰結が本日の計器問題に直結します**: 最寄りリンク中心への吸着の量子化は **節長の半分** ⇒ 30 mm なら **±15 mm** ・**SSOT の 15 mm なら ±7.5 mm** ⇒ ⭐ **定数を SSOT に戻すだけで、計器の床が半分になります。**
⚠ ただしケーブル全長も変わります (40×15 = 600 mm 対 32×30 = 960 mm) ⇒ ⛔ **節長だけ直すのは不可**。cell の寸法と一緒に決める量です。

---

## §3 Tier A — 権威ある出所が在るもの ⇒ ⛔ **値を書かず、読む**

| 定数 | 権威ある出所 (逐語) | 値 | 現況 |
| --- | --- | --- | --- |
| `TABLE_TOP` | `task_config.py:20 TABLE_HEIGHT` | 0.80 | ✅ 全 driver 一致 |
| `CABLE_R` | `task_config.py:137 CABLE_RADIUS` | **0.004** | ⛔ `cell`/`route` が 0.005 |
| `CABLE_N` | `task_config.py:135 CABLE_SEGMENTS` | **40** | ⛔ `steps*` が 32 |
| `CABLE_SEG` | **`task_config.py:136 CABLE_SEG_LEN`** (⭐ 実定数 ・import 可) | **0.015** | ⛔ 全 driver が 0.030 |
| `GRIP_HALF_SPAN` | `task_config.py:235` | **0.044** | ✅ (`steps*` のみ定義) |
| クリップ 5 箱 | `newton_skill_env_base.py:1858-1864` | 兄弟文書 §3 の回転形 | ⛔ 全 driver が自作 |
| クリップ接触 | `:1918-1921` + `task_config.py:187` | `solref="-40000 -400"` `friction="1.0 0.005 0.005"` | ⛔ 未指定 (MuJoCo 既定) |
| クリップ衝突 | `newton_skill_env_base.py:1908` `:1925` | **ON** (`0x6`) | 兄弟文書 §6-A |
| **未浮上の着座** | `task_config.py:226 GROOVE_CENTER_Z` | `TABLE + 0.009` | ⛔ p4 は `+0.070` を定数保持 |
| **浮上量** | `newton_skill_env_base.py:1897` `:1923` (`target_clip_float_z`) | 未確定 (兄弟文書 §4) | ⛔ p4 は `CLIP_RISER` で別に持つ |

⚠⚠ **着座の 2 行は分けなければなりません (w2:p0 指摘 ・私の誤りでした)**: `GROOVE_CENTER_Z` の定義に **浮上項は入っていません** (`task_config.py` 全体で `float_z` の閉じた query = **0 件**)。浮上はクリップの**設置位置**側に掛かります (`newton_skill_env_base.py:1897` 逐語 `TABLE_HEIGHT + dz + target_clip_float_z`)。
⇒ ⭐ **浮上した後の着座 = `GROOVE_CENTER_Z + target_clip_float_z`** ・⛔ **`GROOVE_CENTER_Z` 単独はもう着座ではありません。**
⇒ ⭐⭐ **これが罠です**: 定数の**名前は「座」のまま**で、クリップだけ動きます。⇒ 浮かせた cell で `GROOVE_CENTER_Z` を挿入目標に使うコードは **黙って外します**。
| グリッパ幾何 | `_ur15_2f85_koshape_actuated.xml` | 資産が正 | ✅ 全 driver が同一絶対パス |

⛔ **Tier A を driver 内に literal で書くことを禁じます。** ⭐ 理由 = 本日 4 回、同じ量の複数コピーが判断を狂わせました (`YOKE_SPREAD` / 帯 8.00 対 10.00 / 旧 XML copy / `CLIP_H`)。

---

## §4 Tier B — cell 固有で権威ある出所が無いもの ⇒ ⭐ **本 spec が持つ**

| 定数 | 採る値 | 根拠 (⛔ 私が決めたのではなく、on-disk の実測記録) |
| --- | --- | --- |
| `YOKE_SPREAD` | **0.40** | `ur15_steps.py:37` 逐語 "measured: 0.22/45deg made the two arms interleave at an 88 mm span; 0.40/20deg clears the rest row and both clips" |
| `TILT` | **20°** | 同上 (対で測られている ⇒ 分離不可) |
| `TABLE_HX/HY` | **0.70 / 0.20** | `steps*` = rest 台とクリップ列を含む後発の cell。⚠ 弱い根拠 (記録コメント無し) ⇒ §7 |
| `SHOULDER_HEIGHT` | `0.37 + 0.58*2` | 全 5 file 一致 ⇒ 争いなし |
| `REST_Y` `REST_X` `REST_TOP` | `steps*` の値 | `:66` 逐語 "measured: at +0.060 the open fingers press into the table" |
| `float_z` (旧 `CLIP_RISER`) | ⛔ **未確定** | 兄弟文書 §4 = p4 の 1 実測待ち |
| `KP_ARM` `KP_WRI` `KVR` `ARMATURE` `DAMP` | `steps*` の値 | ⛔ **arm-control の court** — 本 spec は名前と出所だけ持ち、値の可否を判定しません |
| `CLAMP` `OPEN` `HALF` | ⛔ **凍結しません** | ⭐ 測定 lane が現に動かしている量 (255/236 ・0/18 ・170/214) ⇒ **spec は「測定 lane の最新 banked 値を読む」と定めるだけ** |

---

## §5 Tier C — run 固有 ⇒ ⛔ **spec に入れない**

`OUT` (出力 path) ・`W` `H` (解像度) ・`HOLD_S` ・`WAY` / `STEPS` (振り付け) ・カメラ ・seed。
⇒ ⭐ **これらが script ごとに違うのは正常**です。単一化の対象に含めると、逆に振り付けの実験ができなくなります。

---

## §6 実装契約 (⭐ 作るのは w2:p4 ・本書は形だけ定めます)

1. driver dir に **module 1 個** (例 `ur15_cell_spec.py`)。全 driver は先頭で **そこからのみ** cell 定数を取る。
2. **Tier A** = 可能なら `thread_isaac_lab.configs.task_config` を import。⚠ import が重い/不可なら **生成した写し + 照合 guard**。
   ⛔ **写すだけで guard 無しは不可** (それが今の状態です)。
   ⛔⛔ **guard は行の sha で作らないでください** (⭐ w2:p0 指摘 ・私の初版が誤り): 行 sha が答えるのは「**バイトが動いたか**」だけで、⛔ コメント修正で**偽警報**を出し、⛔ 別の場所での再代入を**素通し**します。⇒ ⭐ **§6.4 の AST pass で SSOT 側の値を評価し、値どうしを比べる。** ⇒ byte-sha は **通知**へ降格 (失敗させない)。
3. **Tier B** = 本 spec の値を module に直書きし、各行に **本 spec の節番号**を付す。
4. **guard** (安い ・run 不要): driver 内に Tier A/B の名前の **再定義**が在れば **失敗**する検査。⭐ 本書 §1 と同じ AST 抽出で書けます (grep では取りこぼします)。
5. ⛔ **driver が新しい cell 定数を必要としたとき、自分で定義しない** — 本 spec に足す (w2:p4 の brief 規則① と対)。

---

## §7 射程 (私が出していないもの)

- ⛔ **新しい値を 1 つも作っていません。** Tier A は repo SSOT、Tier B は p4 の実測コメントからの採用です。
- ⚠ **`TABLE_HX/HY` の採用根拠は弱い** — 記録コメントが無く、「後発の cell だから」という理由だけです。⇒ ⭐ p4 が根拠を持っているなら本節を差し替えてください。
- ⛔ **`CLAMP`/`OPEN`/`HALF` と PD gains の値を判定していません** (別 court)。
- ⛔ **`CABLE_SEG` を 0.015 に変えろ、とは言っていません** — §2 のとおり全長と対で決まる量です。⭐ 言えるのは「30 mm は SSOT と食い違い、計器の床を 2 倍にしている」まで。
- ⚠ 本書は **値の一覧であって、cell が正しく建つことの検証ではありません。** 単一化した後に 1 run 通すことが要ります。

---

## §8 改訂 1 (w2:p0 の敵対的検証を受けて ・実装前 ・3 件とも私が on-disk で確認して採用)

| # | 私の初版 | 直し | 私の誤りの型 |
| --- | --- | --- | --- |
| ① | `CABLE_SEG` の出所を `:135` の**コメント** "40 segments × 15mm" とした | ⭐ **`:136 CABLE_SEG_LEN = 0.015`** = import 可能な**実定数**が 1 行下に在った | ⛔ **1 行読んで止めた** — 同じ block を数え上げなかった |
| ② | 着座の Tier A 行に `TABLE + float_z + 0.009` と書き `task_config.py:226` を根拠にした | ⭐ **2 行に分割** — `:226` に浮上項は無い (`float_z` の閉じた query = **0 件**)。浮上は `newton_skill_env_base.py:1897`。⇒ 浮上後の座 = `GROOVE_CENTER_Z + target_clip_float_z` | ⛔⛔ **引用先に存在しないものを引用した** — 私が終日 他者に指摘してきた型 |
| ③ | guard を「SSOT の当該行の sha」で作れとした | ⭐ **AST で値を評価して 値どうしを比較**。byte-sha は通知へ降格 | ⛔ **識別性の無い述語** — コメント修正で偽警報・別所再代入を素通し |

⭐ **①③ は結論を変えず、②は Tier A の行を 1 つ増やしました。** ⛔ どれも実装前に見つかったので、書き換えの費用はゼロです。

⭐ **併せて記録**: w2:p0 は自身の「権威 env は衝突 OFF」を撤回されました (2 つの build 経路を 1 語に畳んでいた) ⇒ ⭐ 本 spec の Tier A「クリップ衝突 = ON」(`newton_skill_env_base.py:1908` `:1925` ・committed で無条件) は敵対的検証を生き残りました。⚠ 私はこれを「私が正しかった」でなく「**2 つの経路が逆の既定を持つ**」という事実として持ちます (兄弟文書 §6-A)。
