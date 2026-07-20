# c66 evidence readback — §9 全面改訂（HOLD 3 件の CLOSE 確認）

**Verifier:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**Verdict 発行:** 2026-07-21 00:43 JST。
**対象:** c66 `d9bff1ad01` = `SKILL_GRANULARITY_MATERIALS_RSTECHLEAD_20260720.md` v1.9 §9 全面改訂。
**先行:** c61-c64 = PASS 4/4 (`4f53ce1f76`) ／ c65 = PARTIAL PASS / HOLD 3 件 (`0a3e3bfafa`)。

## ⭐ VERDICT: **PASS — HOLD 3 件すべて CLOSE**

## HOLD の CLOSE 確認

| # | CLOSE 内容 | 独立検証 |
|---|---|---|
| **OPEN-1** | `:126` → `:127` 是正。主語を frozen `checkpoint_specs` に置き、D0 名は「⚠v1.8 まで…」注記へ | ✅**確認**。`:118`(`SkillDefinition` 主語+注記) / `:123`(`accepted_handoff` 主語+注記) / `:127`(`checkpoint_specs` 主語+注記) が**同型**に揃った。非対称は解消 |
| **OPEN-2** | 述語列挙を廃し **doc 単位除外**へ（§9-3） | ✅**確認**。理由づけ（文脈列挙は節が増えるたび再び under-cover する）も明記 |
| **OPEN-3** | 行数 11 → **14** に訂正 ＋ **測定手順の欠陥を開示** | ✅**確認**（下記 根本原因を独立再現） |

### ⭐ OPEN-3 の根本原因 — 独立再現に成功

p4 申告:「表には 9 名を列挙しながら、**行数は 7 名の regex で数えた**（`safe_interruption_checkpoints` と
`initiation_predicate` を落とした）」。**同一 commit `b2bd31b8ec` で実測**:

| query | 行数 |
|---|---|
| 7 名（2 名を落とした集合） | **11** ← v1.8 の記載を**正確に再現** |
| 9 名（正しい閉集合） | **14** ← 私の c65 実測値と一致 |

⇒ **申告どおり。原因特定は正しい。**

⭐⭐ **最重要の構造的知見（p4 発・私が確認）: OPEN-1 と OPEN-3 は同一原因。**
落とした 2 名の一方 `safe_interruption_checkpoints` が、**まさに裸使用を持つ名前**だった。
⇒ **1 つの閉じていない query が、行数の誤りと「使用 0」の偽主張を同時に生んだ。**
一方は数値の誤り、他方は absence 主張の偽 — **症状は別カテゴリだが根は 1 本**。
（`feedback-absence-claims-need-closed-query-and-moving-tree-provenance-2026-07-18` の具体例として強い。）

## 裸使用 = 0 の独立確認（現在の load-bearing claim）

c66 as-banked に対し 9 名の閉クエリで **19 行**を全数目視分類。
**D0 名を「契約層の現行用語」として主語に置く行 = 0**。内訳:

| 文脈 | 行 |
|---|---|
| §2-1 訂正表の左列 | `:73` `:74` `:75` `:76` `:77` `:78` |
| frozen 名主語 + 「⚠v1.x まで D0 名…」注記 | `:119` `:123` **`:127`** |
| 版表行（各版が何を直したかの記録） | `:13` `:14` |
| §2-1 本文（訂正の理由づけ） | `:80` `:82` |
| §9 の OPEN 表・再測定表・除外指示 | `:223` `:225` `:227` `:248` `:257` |
| **概念言及（擁護可能・別扱いで記録済）** | `:126` = `duration_cost_distribution` を **SDM 側の量**として言及。frozen 自身が「分布推定は Phase D SDM の職務」(`contracts_v2:423`) と定める |

⇒ **`:126` を除く全行が訂正記録の文脈であり、`:126` は §9-3 に例外として明示記録済**。主張は成立。

## 完成物 integrity

| レグ | 結果 |
|---|---|
| sha256 @ `d9bff1ad01` | `c2eacee5457bf00c6b3132454cf3559606d7bac8c28c6695466203c8912a5ece` = **完全一致** |
| records-only | 1 file・`.md`・**code 0**（48 insert / 20 delete）⇒ census 35 不変は構造的に従う |
| branch 在中 | `probe/pd1-arm-pd` のみ |

## ℹ 情報注記（**defect ではない**・verdict 不変）

§9-2 の再測定値 **18 行 / 29 occurrence** は「**本節執筆直前**・`:126` 修正後の working tree」で測ったもの。
**as-banked (`d9bff1ad01`) を測ると 19 行 / 32 occurrence** になる（§9-0 の OPEN 表・§9-2 の名前別内訳・§9-3 が
D0 名を再度挙げるため）。**測定時点は §9-2 の見出しに明示されており、誤りではない。**
p4 が「c65 as-banked の 29/18 と一致する」と cross-check した推論も正しい（`:126` 修正は名を注記へ移すだけで
occurrence を減らさないため）。

⭐ **注目点: この count 漂流のクラスは OPEN-2 の CLOSE によって『修正』ではなく『解消』された。**
doc 単位除外に移行した結果、**guard がこれらの数値を一切消費しない**。数値は情報提供のみとなり、
「測定時点 vs banked 状態」の乖離が defect たり得なくなった。**部分除外を維持していれば同じ問題が再発し続けた。**

## 非主張

- ⛔ 設計判断・所管裁定（DDR #31/#32/#33）には触れない。
- ⛔ freeze / impl / training / closed-loop authority = CLOSED 継続。
- ⛔ census 35 は導出であり再測定していない。

## 本 arc の総括（記録）

3 版・3 者手番で 1 行に収束した:

| 手番 | 閉じ損ね | 検出者 |
|---|---|---|
| c63 sweep | 4 名のみ sweep・`:126` を取り逃す | — |
| pY c61-c64 readback | **c63 が名指した 4 名だけを grep**（閉クエリでない） | p4（9 名で実測） |
| p4 §9 v1.8 | **表 9 名 / 行数 regex 7 名**の不一致 → 行数誤り + 「使用 0」偽 | pY（14 行を実測・裸使用を発見） |
| p4 §9 v1.9 | — | ✅ CLOSE |

⇒ **片側の誤りではなく、両側の閉クエリ不足が重なって 1 版遅れた**（§9-4 に p4 が記録済）。
**教訓の所在 = 「absence 主張は、その主張が挙げた名前の範囲で検証してはならない」**。
検証集合は**独立した権威ソース**（本件では frozen `contracts_v2` の disposition 表）から構成する。

---
**readback 実施 = 2026-07-21 00:43 JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
