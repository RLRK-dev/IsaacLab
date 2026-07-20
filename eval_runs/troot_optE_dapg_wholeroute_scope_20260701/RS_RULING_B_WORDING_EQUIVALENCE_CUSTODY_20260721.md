# 裁定 B の表現統一 — canonical wording（custody record）

**Recorder:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**記録:** 2026-07-21 02:52 JST。
**契機:** pY が c69 readback (`526ae65bed` §C) で提起した「逐語が on-disk 2 版に分裂」への Rs 回答。

## Rs 逐語（2026-07-21 02:4x、2 段）

> ①「クリップのケーブルクランプのみ kinematic を使用可」「ただし、クリップのケーブル固定だけは kinematic を使用する」
> **この2つは同じことを意味している**
> ②**1つに統一した表現にして**

## ⭐ CANONICAL WORDING（本 record が SSOT）

> **kinematic の唯一の認可例外 = `clip-retention pin`（クリップのケーブル固定）**

⛔ 不許可（不変・併記必須）= **腕関節角の直接書込 / 指の kinematic close / `update_kinematic_bodies`（FK→physics の body 複写）/ weld・cable-finger attachment**。

⚠ **「pin 復活 = kinematic 復活」ではない。** 例外は上記 1 件のみ。

## 選定根拠（実測・pY が独自に決めていない）

統治 4 面（`CLAUDE.md` / `prohibited.md` / `RS71-System-Spec-SSOT.md` / `00-DESIGN-STATUS-LEDGER.md`）の用語頻度:

| 表現 | files | occurrences | 判定 |
|---|---|---|---|
| **`clip-retention pin`** | **4** | **16** | ⭐**支配的**。`RS71 §0#5` の**不変前提名そのもの**（`:27`「the ONLY authorized exception is the clip-retention pin」） |
| 「ケーブル固定」 | 2 | 9 | 日本語形として定着 |
| 「クランプ」 | 3 | 7 | 一般語としての使用 |
| 「**ケーブルクランプ**」 | 1 | **1** | ⛔**本件で新造された語**（`CLAUDE.md:72`）。既存 usage 無し |

⇒ **既存の不変前提名に寄せ、新造語を採らない**のが最小 churn。
canonical 形は `RS71:27` の英語表現と 1:1 対応し、日本語 gloss は既存の優勢形を採る。

## 適用（surface 別）

| surface | 現状 | 要処置 | owner |
|---|---|---|---|
| `CLAUDE.md:72` | 「クリップのケーブルクランプのみ kinematic を使用可」 | canonical へ差替え | ⛔**L3・CC read-only** ⇒ **Rs / p4** |
| `c69 §9`（`STEP43_CONTROLLER_REALIZATION_BASELINE_*`） | 「ただし、クリップのケーブル固定だけは…」 | canonical を併記（逐語節は履歴として保持可） | p4 |
| `00-DESIGN-STATUS-LEDGER.md:35` / DDR#25 | 「クリップのケーブル固定」 | canonical へ寄せ | p6 |
| memory `project-sim-is-reality-no-kinematic-20260719` / `MEMORY.md` | 「クリップのケーブル固定」 | canonical へ寄せ | pY（実施済） |
| `RS71 §0#5` | 既に canonical | **編集不要** | — |

⭐ **逐語節の扱い**: 発話の記録として残す場合は「**Rs 発話（2 表現・同義。canonical は本 record**）」と明記する。
⇒ **2 つの異なる文字列が両方「逐語」と表記されている状態を解消する**（同じ検査をする後続者が同じ flag を再提起しないため）。

## 非主張

- ⛔ どちらが literal な Rs 発話かは**確定していない**。Rs が確定させたのは**同義性**と**統一指示**であって、逐語の指定ではない。
- ⛔ 本 record は裁定 B の**適用範囲**を変更しない（範囲 = `c69 §9` の表・Rs「ok」で確定済）。**語の統一のみ**。
- ⛔ `CLAUDE.md` は CC 編集不可。pY は差替えを**提案**するのみ。

---
**記録 = 2026-07-21 02:52 JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
