# 項目 5（§0#4 開口）— 不一致は**休眠していない。毎 session 配信されている**

desk: p4 RS-TECH-LEAD (w2:p4) / 測定 2026-08-06 16:51:37–16:52:43 JST
⛔ **測ったのは「配達」であって「幾何」ではない。** 開口寸法の再導出は**していない**（§0 = FOUNDATIONAL・Rs 専権。加えて位置/形状パラメータは `/geometric-design` の強制ゲート対象）。
⛔ **どの値が正しいかを提案していない。** 値の選択は Rs 専権。

---

## 1. きっかけ — 本日の「近さの系列」の次の項

系列: disk に在った → 配達物に在った → 自分の出力に在った → 保存された過去の配達物に在った。
⇒ **次に近いのは session 開始時に自分へ渡される hook の出力**。⭐ **項目 5 は §0 の問いで、§0 はその hook が毎回 echo している。** ⇒ 見た。

## 2. 実測 — §0#4 自身は**数値を持たない。ポインタである**

`handoff_grounding_gate` の echo（本 session の SessionStart 出力 `:12` 逐語・要点）:

> **4. GRIPPER GEOMETRY LOCKED** — the active finger DESIGN is **コ-shape** … its geometry is human-LOCKED. … **committed asset = `2f85_koshape.xml` = コ** … [§5; `06-Knowledge/GD-KoShape-Finger.md`]

⇒ ⭐ **§0#4 は寸法を述べず、asset を指す。**（＝ 私の「spec = 参照」は正しかった）

**その指す先を開いた実測** — `thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/2f85_koshape.xml`（mtime **2026-06-22 11:02**・6 月以降 不変）:

```
:10   (top, z=0.0258), gap ~10 mm. Derived from 2f85_tendon_stripped.xml …
:111  toward the cable (gap ~10 mm) to wrap the Ø8 cable top+bottom …
```

⇒ **§0#4 のポインタを辿ると、asset 自身の記述は「gap ~10 mm」。**

## 3. ⭐ そして DDR #44 が **同じ hook で毎回 配信されている**

同 echo の DEFERRED/PENDING DEPENDENCY REGISTER digest `:31` 逐語（要点）:

> **#44 [FOUNDATIONAL] ⭐⭐§0 #4 GRIPPER GEOMETRY — コ の開口が 10.00 → 14.00 mm に変更され、working model には既に入っている（Rs 指示 逐…）**

**配信条件の実測**（`~/.claude/settings.json:187-215`）: `SessionStart` の matcher = **`startup` / `resume` / `clear`** がいずれも同一 orchestrator を起動（本 session の header は `compact` でも発火を示す）。
⚠ **`/clear` は §運用11 でタスク完了ごとに必須。** ⇒ **実質、全 session・全タスク境界で配信される。**

## 4. ⭐⭐ 帰結 — これは**休眠中の不整合ではなく、既定として継承される値**

| 面 | 値 | 到達性 |
|---|---|---|
| §0#4 本文 | **数値なし（ポインタ）** | 毎 session 配信 |
| ポインタ先 = LOCK asset | **~10 mm**（asset 内の記述・6-22 以降不変） | 開けば読める（自動配信されない） |
| DDR #44 | **14.00**（「working model には既に入っている」と述べる） | **毎 session 配信** |
| 作業 asset（別途測定・本 artifact の範囲外） | 16.00 | 開けば読める |

⇒ ⭐ **新しい session が最初に受け取る数は 14.00 であり、それは asset を開かずに得られる唯一の数。**
⇒ ⛔ **DDR #44 は「working model に入っている」と述べるが、私が別途測った作業 asset は 16.00。** ⇒ **register の working-model 記述自体が現況と合っていない可能性**（⚠ 本 artifact では再測していない — 引用のみ）。

## 5. ⭐ 本日の memory-freeze 所見の**裏返し**

- 凍結規則: **自動読込面が 0** ⇒ 見えず、守られなかった ⇒ **見えない規則は確定した違反になる**（`CLAUDE.md:160` §運用31 の理由節）
- §0#4 の争点値: **最も読まれる自動読込面に在る** ⇒ **開かずに継承される**

⇒ ⭐ **同じ軸の両端。到達性が 0 なら規則は効かず、到達性が最大なら未決の値が既定になる。**
⇒ **どちらも「その面に何が在るか」で決まり、内容の正しさとは独立。**

## 6. ⛔ 私がしていないこと（明示）

- 開口寸法の**再導出・測定・提案**をしていない（§0 + `/geometric-design` ゲート）
- **どの値が正しいかを述べていない**
- 作業 asset の 16.00 を**本日 再測していない**（過去の自分の測定の引用。⚠ 再測が要るなら別途）
- DDR #44 の全文を引いていない（hook digest が切り詰めた形で配信している。**全文は register 本体**）

## 7. Rs に要るもの

**どの面を権威とするか の一言**（10.00 / 14.00 / 16.00）。⇒ それが決まるまで、**毎 session 14.00 が既定として配られ続ける**ことを、決定の入力として添える。

---

## 再現コマンド

```bash
# hook の echo（本 session 分は tool-results に保存されている）
grep -n 'GRIPPER GEOMETRY' <session>/tool-results/hook-*-stdout.txt
# 配信条件
sed -n '187,215p' ~/.claude/settings.json
# §0#4 のポインタ先
grep -n 'gap ~' thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/2f85_koshape.xml
```
