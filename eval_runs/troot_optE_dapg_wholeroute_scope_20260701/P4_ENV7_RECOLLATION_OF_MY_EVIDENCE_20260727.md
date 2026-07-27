# p4 — 私が producer である evidence の env 軸 再照合 (DDR #42 第 2 帰結)

作成 2026-07-27 20:57:47 JST (w2:p4 RS-TECH-LEAD)
受諾 = `MSG-P4-P18-…-074` §3 ・射程 = **私が producer である evidence のみ**・検証レグ = p0

---

## 1. 何が変わったか (権威 = p5 の bank した記録、私が実読)

`P5_ENV7_UPGRADE_20260727/pip_freeze_{BEFORE,AFTER}.txt` @ `45a832712c`:

| package | 旧 (163 節以前の evidence) | 新 (164 節以降) |
| --- | --- | --- |
| newton | 1.2.1 | **1.4.0** |
| mujoco | 3.8.1 | **3.10.0** |
| mujoco-warp | 3.8.1 | **3.10.0.3** |
| warp-lang | 1.13.0 | **1.15.0** |
| numpy / torch | 2.3.1 / 2.10.0+cu128 | ⭐ 不変 |

実行中の interpreter 実測 (`/home/rlrk/env_isaaclab7/bin/python`): newton 1.4.0 / mujoco 3.10.0 / warp 1.15.0 ⇒ AFTER と一致。

---

## 2. 私の evidence を 2 つに割る

⭐ **物理を回すかどうか**で割ります。回さないものは stack が動いても変わりようがありません。

**(a) stack に依存しない** (再測不要・理由つき):
- クリップ表の読み取り・回転 (`ur15_cell_spec` の AST 読み) — 構文解析のみ
- 定数の照合・guard・テンプレート規則 — 同上
- 退役 file の閉じた query (50,022 file) — file system のみ
- 反例列挙 (collide counterfactuals) — AST のみ

**(b) stack に依存する** (⭐ **物理を積分する** ⇒ 再測した):
掃引 / 爪の床 / 離脱点の二分探索 / ケーブル下の到達 / 鞍の窓。

---

## 3. 再測の結果 — ⭐⭐ **5 件すべて 同一**

| 再測したもの | 判定 | 出力 (banked) |
| --- | --- | --- |
| 掃引 23 点 (6 列) | ⭐⭐⭐ **byte-identical** — sha256 が banked baseline と**一致** (`0b6bb55d0b771191817836ed7df43d2643cd031d0dba53b27c0d274ba0386338`) | `env7_recollation_sweep.txt` |
| 爪の床 (飽和域) | 同一 (−2.55 / −2.59 / −2.64 / −2.75 / −2.71・爪箱 半寸法 11.0 / 9.0 / 1.2 mm・接触除外 7) | `env7_recollation_clawfloor.txt` |
| 離脱点の二分探索 | 同一 (爪先 11.50 ⇒ **ctrl 188.08** ・pad 21.70 ⇒ **188.02** ・一致 0.06 count) | `env7_recollation_bisect.txt` |
| ケーブル下の到達 | 同一 (OPEN roll 0.30 = 24.6 mm ・roll 0.55 = **35.7 mm**) | `env7_recollation_reach.txt` |
| 鞍の窓 | 同一 (600 mm で 9 個 ・960 mm で 23 個 ⇒ 3 個は入る) | `env7_recollation_saddles.txt` |

⇒ ⭐ **旧 stack で取った私の数値は、新 stack でもそのまま成立します。**
⇒ ⭐⭐ 掃引は **byte-identical** ⇒ 数値が近いのではなく **同じ計算をしています**。

---

## 4. ⚠ 射程 (この結論が **言っていないこと**)

1. ⛔ **私が producer でない evidence は対象外** — 判定 log 由来の数 (垂れ 127.8 mm ・傾き 5.55° 等) は私の再測範囲に在りません。
2. ⛔ **走行 (cell 全体の動画) は再測していません** — run 認可は Rs のもので、私は probe しか回していません。⇒ ⭐ **cell 全体が同じに走ることの証拠ではありません。**
3. ⚠ 5 件はいずれも **グリッパ単体 (ケーブル無し) か 静定 1 回**です ⇒ 接触が多い・長い積分での一致は**別の問題**。⭐ 同一だったこと自体は、少なくとも **接触ソルバの決定性が版をまたいで保たれている**ことを示します (掃引は 3000 step の静定を 23 回)。
4. ⛔ **cell の build 自体は §別 doc で確認済** (`nq=113 nu=14 nbody=88 ngeom=139 eq=8`)。本 doc はその上の**動く量**についてです。

---

## 5. 未処理

- p0 の検証レグ (独立確認) — 未実施。
- 判定 log 由来の evidence の owner — 私ではありません (p18 / p6 の割当)。
