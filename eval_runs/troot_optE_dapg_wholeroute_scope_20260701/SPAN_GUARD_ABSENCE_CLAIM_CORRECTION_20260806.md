# ⛔ §0#2 についての私の不在主張を訂正 — 名前で探したので、名前を言わない guard は結果に入り得なかった

desk: p4 RS-TECH-LEAD (w2:p4) / 測定 2026-08-06 17:14:41–17:16 JST
⛔ **§0#2 の内容について何も提案していない。** 訂正しているのは **「guard が在るか」という私自身の測定主張**であって、不変前提そのものではない（§0 = Rs 専権）。

---

## 1. 私が記録に入れた主張

- ✅ `assert_span_invariant`（`thread_isaac_lab/envs/route_executor.py:135`）は **call site が 0**（AST・2,770 file）
- ⛔ そして私はこう続けた —「**span を名指す生きた guard はこれだけだった**」／「`validate.sh` と `scripts/validations/` に **span token は 0**」
- ⇒ **読み手は「span は守られていない」と受け取る。** 実際 §0#2 は FOUNDATIONAL であり、これは最も高い場所に置いた主張だった。

## 2. ⛔ 実測 — span を**名指さずに** span を守る guard が生きている

**`scripts/validations/check_ssot.sh` Layer 1 Check 1**（`validate.sh:97` が dispatch = **live**）:

```bash
constants_list=$(grep -oE '^[A-Z][A-Z0-9_]+' "$TASK_CONFIG" | sort -u)
pattern="^($(echo "$constants_list" | tr '\n' '|' | sed 's/|$//')) *= *[0-9(\"'\[]"
# → task_config.py 以外の全 .py で、上記いずれかの再定義を検出
```

⇒ ⭐ **task_config.py の全定数を自動で覆う総称 guard。個々の定数名を 1 つも書いていない。**

**span が対象に入ることの実測**:

| 実測 | 値 |
|---|---|
| `task_config.py:235` | `GRIP_HALF_SPAN = 0.044`（コメント: commanded arm-to-arm span = **88mm**） |
| `task_config.py:21-22` | `ROBOT_LEFT_BASE` / `ROBOT_RIGHT_BASE`（§0#2 後半「bases fixed at Y = ∓0.35」） |
| 抽出パターン `^[A-Z][A-Z0-9_]+` に合致するか | **3 つとも合致** |

⇒ **`GRIP_HALF_SPAN` の他所での再定義は、Layer 1 が flag する。**

## 3. 3 つの保証を、私は 1 つの言い方で潰していた

| 保証 | 機構 | 状態 |
|---|---|---|
| span の **値**を実行時に表明する | `assert_span_invariant` `route_executor.py:135` | ⛔ **call site 0 = 不在**（私の所見は**維持**） |
| span 定数が **他所で再定義されない** | `check_ssot.sh` Layer 1 Check 1（総称） | ✅ **生きている** — ⛔ **私は見落とした** |
| span が **spec に固定されている** | §0#2 が `:21-22` / `:235` を引く | ✅ 在る |

⇒ ⭐ **「値の実行時表明が無い」は真。「span は守られていない」は偽。** 私は前者を書いて後者を読ませた。

## 4. ⭐⭐ 見落としの機構 — そして「確認」に使った測定が、見落とした物の**署名**だった

私は **名前で探した**（span 定数名 / `assert_span_invariant` / span token を grep）。
⇒ ⛔ **span を一度も書かない guard は、名前駆動の結果集合に原理的に入り得ない。**

⚠ そして最も痛いのはここ:

> 私が確認として出した「`validate.sh` と `scripts/validations/` に **span token 0**」は **真**である。
> ⛔ **しかしそれは総称 guard の姿そのもの** — 総称であるとは、個別名を書かないということ。
> ⇒ ⭐ **token が 0 であることは、guard が無いことの証拠ではなく、guard が総称であることの証拠だった。私はそれを逆に読んだ。**

⇒ **識別しない述語**の一族（0 件は「無い」と「名前で書かれていない」を区別しない）。

⚠ **これは自分の memory に既に在る規則の違反**: 「**不在は sink で検証・source 変数名で grep するな**」
（`feedback-verify-at-the-delivery-surface-not-the-source-variable-name-2026-07-19`）。
⇒ ⭐ **規則は手元にあり、§0 という最も高い場所で破った。** 規則を持っていることは、使うことではない。

## 5. 正しい方法（今回それで見つけた）

⛔ 主張の空間（span という語）で検索しない。
✅ **guard の空間を列挙する** — `scripts/validations/` の **8 本すべて**を数え、**各々が何を検査するか**を読む（closed query）。
⇒ 12 file 中 guard は 8 本（他 3 = データ txt、1 = test）。Layer 1/2/3/4/5/7 ＋ cable / control-method。

## 6. 射程（この訂正が**言っていない**こと）

- ⛔ §0#2 の**値**について何も述べていない（88 mm か否かは Rs 専権）
- ⛔ Layer 1 が守るのは **再定義の不在**であって、**値の正しさでも実行時の強制でもない**
- ⚠ 8 本の guard の**本文全体は読んでいない** — 読んだのは各 file の見出し／目的行と Layer 1 Check 1 の本体。⇒ **他の guard に span 関連の検査が在る可能性は排除していない**（本節がその射程）
- ⚠ `check_cable_model.sh` / `check_control_method.sh` は header コメントが無く、**目的を本文から読んでいない**

---

## 再現コマンド

```bash
grep -n 'check_ssot' scripts/validate.sh                     # Layer 1 が live か
sed -n '/Check 1: Hardcoded/,/Check 2/p' scripts/validations/check_ssot.sh
grep -n 'GRIP_HALF_SPAN' thread_isaac_lab/configs/task_config.py
sed -n '19,24p' thread_isaac_lab/configs/task_config.py | grep -oE '^[A-Z][A-Z0-9_]+'
ls -1 scripts/validations/                                    # guard 空間を列挙（名前で grep しない）
```
