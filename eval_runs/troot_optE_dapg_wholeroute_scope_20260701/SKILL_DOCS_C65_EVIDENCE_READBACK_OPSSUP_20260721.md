# c65 evidence readback — §9 除外標識 / D0 名 guard 判別述語 (v1.8)

**Verifier:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**Verdict 発行:** 2026-07-21 00:36 JST。
**対象:** c65 `8d91ac350c` = `SKILL_GRANULARITY_MATERIALS_RSTECHLEAD_20260720.md` v1.8 §9 追加。
**先行:** c61-c64 readback = PASS 4/4 (`SKILL_DOCS_C61C64_EVIDENCE_READBACK_OPSSUP_20260721.md`
sha256 `0a00d8a82be8b308…` @ `4f53ce1f76`)。

## ⭐ VERDICT: **PARTIAL PASS / HOLD**

**PASS** = 完成物 integrity・per-name 計数・「語を消さない」判断・§9 の狙い自体。
⛔ **HOLD** = §9 の中核主張 **「現行用語としての使用は 0」= FALSE**（実測 1 件残存）＋ 判別述語の被覆不足＋行数不一致。

⚠ **本 HOLD は c61-c64 の PASS 4/4 を取り消さない**。c61-c64 の対象claim は依然 PASS。

## ✅ PASS したレグ

| レグ | 結果 |
|---|---|
| sha256 @ `8d91ac350c` | `8653e916451c3fd1effd89fe82cb226e59df800f168570b2d5cff9d98bd78c6f` = 申告と**完全一致** |
| records-only | 1 file・`.md`・**code 0** ⇒ census 35 不変は構造的に従う |
| branch 在中 | `probe/pd1-arm-pd` のみ（cross-lane 規律どおり commit 併記が必須） |
| **per-name 出現数**（申告 measurement point = §9 執筆直前 = c64 `b2bd31b8ec`） | ⭐**9 名 / 18 occurrence が完全一致**（`duration_cost_distribution` 5 ／ `SkillLifecycleContract`・`recovery_rollback_target`・`SkillHandoffState`・`accepted_incoming_handoff_set`・`safe_interruption_checkpoints` 各 2 ／ `SkillActionKey`・`ExecutableIdentity`・`initiation_predicate` 各 1） |
| 「語を消す直し方を採らない」判断 | ⭐**正しい**。本 doc は D0→frozen の改名/破棄の**訂正記録**であり、旧名を引用できなければ訂正が成立しない。除外標識で緩和する方針は妥当 |
| 測定時点の明示 | ⭐**正しい**（§9 自身が counts を増やすため、「本節を書く直前の閉クエリ」と scope した点は honest） |

**閉クエリの張り方:** 私は p4 の列挙を採らず、**frozen `contracts_v2` の disposition 表（`:405-440`）から
D0 側 field 名 15 個 + 型名を抽出**して照合した（前回 readback で私が 4 名しか見ていなかった欠陥の是正）。

## ⛔ OPEN 1 — 「現行用語としての使用は 0」は **FALSE**（最重要）

§9 逐語:「**現行用語としての使用は 0**（v1.6 の sweep で確認済）」。**実測で反例 1 件**:

**`:126`** = 「- `safe_interruption_checkpoints` の粒度不足（回復・中断が粗い単位でしか打てない）」

**同 §4 内の兄弟行との非対称が決定的**:

| 行 | 形 | 注記 |
|---|---|---|
| `:118` | frozen 名 **`SkillDefinition`** を主語に置く | ✅「⚠v1.5 まで D0 名 `SkillLifecycleContract` で書いていた」 |
| `:122` | frozen 名 **`accepted_handoff`** を主語に置く | ✅「⚠v1.4 まで D0 名 `accepted_incoming_handoff_set` で書いていた」 |
| `:126` | **D0 名を裸で主語に置く** | ⛔**注記なし** |

さらに **frozen 名 `checkpoint_specs` は doc 全体で `:75` の 1 回のみ**、しかもそれは §2-1 訂正表の
**右列**（＝「改名先はこれ」の説明）であって、**現行用語として使われている箇所は 0**。

⇒ **`:126` は c63 sweep の取りこぼしであり、§9 はそれを継承した。**

⭐ **機序（p4 §8 の規律そのものに該当）**: §9 は「現行使用 0」を **v1.6 sweep の結論として引用**しており、
**§9 を書く時点で再測定していない**。sweep が 1 行取り逃していたため、その誤りが「確認済」と付記された形で
§9 に伝播した。= **「指摘は欠陥クラスの標本」を name 軸には適用したが、`用法` 軸（裸使用 vs 注記付き）には
適用しなかった**。関連 memory = `feedback-a-gate-validated-under-the-bug-is-validated-by-the-bug-2026-07-15`
（バグの下で緑になった検査はそのバグに検証されている）/ `feedback-an-absence-claim-must-be-read-not-relayed-2026-07-15`。

## ⛔ OPEN 2 — 判別述語 (a)(b)(c) が全 occurrence を覆わない

§9 は guard 実装者に「本 doc 内の D0 名は**全て** (a) §2-1 訂正表の左列／(b)「⚠v1.x まで D0 名 X で書いていた」型
注記／(c) §9 集計表 のいずれか」と宣言する。**実測では最低 3 クラスが外れる**（c64 時点の行番号）:

| 外れる occurrence | 実際の文脈 | (a)(b)(c) 該当 |
|---|---|---|
| `:13` `:14` | **版表の行**（各版が何を直したかの記録） | ⛔なし（**第 4 の文脈**） |
| `:78` `:80` | §2-1 の**本文**（pQ framing の採用／§4 列は正しかった旨） | ⛔左列でない |
| `:124` `:126` | §4 の**箇条書き** | ⛔注記型でない |

⇒ **述語どおりに実装した guard は依然 hit する**。§9 の目的（誤読の防止）が達成されない。
⚠ なお `:124`（`duration_cost_distribution` を SDM 側の量として言及）は、frozen の disposition 自身が
「分布推定は Phase D SDM の職務」と述べており **概念としての言及は擁護可能**。**`:126` とは別扱いにすべき**
（`:126` は改名済 field 名の裸使用で擁護不能）。

## ⛔ OPEN 3 — 行数 **11 ≠ 14**

§9 表:「**grep が hit する行数（重複行を 1 と数える）= 11**」。
**同一 9 名・同一 commit (`b2bd31b8ec`) で実測 = 14 行**（occurrence 18 は一致するので、差は行の数え方のみ）。
内訳 = `:13` `:14` `:71` `:72` `:73` `:74` `:75` `:76` `:78` `:80` `:117` `:121` `:124` `:125`。
**11 を再現する自然な閉クエリを私は構成できなかった。** 差 3 の由来 = 未特定（p4 の測定手順の開示待ち）。

⚠ 参考（別数値・混同注意）: **as-banked (`8d91ac350c`) では 29 occurrence / 18 行**（§9 自身が名を挙げるため増加）。
§9 の counts は c64 時点の値であり、**banked 版に対して grep する読み手は必ず違う数を得る**。
測定時点は明示されているので誤りではないが、**guard 実装者は「11」を期待値に使えない**。

## ⭐ CLOSE 条件（提案・p4 の裁量）

1. **`:126` を `:118` `:122` と同型に直す**（frozen 名 `checkpoint_specs` を主語にし、D0 名は注記へ）
   ⇒ これで「現行使用 0」が**初めて真になる**。
2. **述語に第 4 文脈（版表行）と §2-1 本文・§4 箇条書きを加える**、または
   **doc 単位の除外**（「本 doc 全体を D0 名 guard の対象外とする」）へ単純化する。
   ⚠ 後者の方が堅い — 文脈列挙は将来 節が増えるたびに再び under-cover する。
3. **行数 11 の測定手順を開示 or 14 へ訂正**。
4. ⭐**再測定してから「0」と書く**（v1.6 の結論を引用しない）。OPEN 1 の機序への直接の対処。

## 非主張

- ⛔ 設計判断・所管裁定（DDR #31/#32/#33）には触れない。**p4 が裁定していないことのみ確認**。
- ⛔ freeze / impl / training / closed-loop authority = CLOSED 継続。
- ⛔ census 35 は**導出であり再測定していない**（code 0 file ゆえ動き得ない）。
- ⛔ 本 verdict は **c61-c64 の PASS 4/4 を取り消さない**。

## 自己申告 — 前回 readback の欠陥

c61-c64 readback で私は **c63 が名指した 4 名だけを grep** した。閉クエリでなく、
**「absence 主張を、その主張が挙げた名前の範囲で検証した」**という同型の誤り。p4 の実測（9 名）が正しい。
本 readback では frozen contract の disposition 表から名の集合を独立に構成して是正した。
⇒ **OPEN 1 は、私が前回 閉じ損ねた面から出た**。

---
**readback 実施 = 2026-07-21 00:36 JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
