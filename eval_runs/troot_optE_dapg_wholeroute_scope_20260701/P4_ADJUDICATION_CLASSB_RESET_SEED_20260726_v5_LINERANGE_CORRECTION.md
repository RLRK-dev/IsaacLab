# class B — p4 **v5 records correction**（manifest 義務の行範囲）

**裁定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-26 17:23:34 JST（date-THEN-write）。
**応答先:** pN RETURN R4 `MSG-PN-P4-CLASSB-V4-RETURN-20260726-004`（残 records 1 件）。
**⛔ 履歴 rewrite なし** — v1〜v4 は削除も改変もしない。本書は **行範囲 1 点のみ**を訂正する。

## 0. correction chain

| 旧（維持・改変しない） | 該当箇所 | 影響先 | 訂正版 |
|---|---|---|---|
| `…_v3_RECORDS_CORRECTION.md` @ `6c87b52497`（sha256 `7d039ee16058c6b0…`） | §B「行番号の訂正（**すべて +1**）」中の **manifest 義務 = 旧 `:751-752` → 新 `:751-753`** | pN（提出）／Rs（私の 17:15 報告） | **§B**（= pN 選択肢 (a)） |

## A. 維持（pN PASS-CLOSE 済 — 変更しない）

v4 の Q2（parent 4 / v3 5 / v4 6・Q1 = 0）／candidate technical boundary／**class B = HOLD**／他 pane の record ／ source・実装・RUN・verify・status。

## B. 訂正 — 「本文」と「見出し込み範囲」を分離する（pN 選択肢 (a)）

⛔ **問題:** 私は「**すべて +1**」と書きながら、manifest だけ **start が +0**（旧 `:751` → 新 `:751`）になっていた。⇒ 規則と個別値が矛盾。

**実測（preserved snapshot `charter_v231.md` @ `f7de41961b` と、私が元に読んだ dirty WT の該当行を突き合わせ）:**

| snapshot 行 | 内容 | 対応 |
|---|---|---|
| `:751` | 「**(2) R3 = pN 正・訂正 #20。§14.23-c の ADAPT 裁定に manifest 登録義務が欠落していた。**」 | **見出し**（WT 側の私の引用には**含まれていなかった**） |
| `:752` | 「p5 実測: `check_control_method.py:58-62` の `RESET_SEED_MANIFEST` は **1 entry のみ** …」 | WT `:751` の **+1** |
| `:753` | 「⭐**追加義務（§14.23-c ADAPT に fold）**: adapt は同一 bundle 内で ① 新 seed site を … 登録 …」 | WT `:752` の **+1** |

⭐ **訂正:**
- **manifest 義務の本文 = `:752-753`**（＝ 旧 `:751-752` の真の +1 写像。**「すべて +1」の規則はこれで保たれる**）。
- **見出しを含めた拡張範囲 = `:751-753`**（`:751` は見出し）。⚠ これは **+1 写像ではなく範囲の拡張**であり、v3 で私はこの区別をせずに書いた。
- ⇒ **「すべて +1」は撤回しない**（他 5 件 = M-4 `:93`／分類 A・B `:145`／§14.2 失効 `:360`／Q3 RESET `:474`／§14.16 `:479` はいずれも +1 で正しい）。訂正は **manifest の範囲表記のみ**。

⭐ **引用内容の意味は不変**（`:752-753` = manifest が 1 entry のみである実測 ＋ 登録義務「登録なき ADAPT は不可」）。

## C. 非主張（不変）

- ⛔ class B の確定・解錠は主張しない（Rs の `:67`/`:72` reconciliation まで HOLD）。
- ⛔ §3 の 4 件は未裁定。source 変更・実装・RUN・verify relay・status flip は行わない。

---
**p4 v5 records correction = 2026-07-26 17:23:34 JST / RS-TECH-LEAD (`w2:p4`)**
