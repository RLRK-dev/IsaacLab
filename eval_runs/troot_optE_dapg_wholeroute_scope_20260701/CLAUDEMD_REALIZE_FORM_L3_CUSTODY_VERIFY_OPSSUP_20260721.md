# CLAUDE.md:72 clip-retention pin realize 形 — L3 custody 検証（逐語 vs 機構の分離）

**Verifier:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**発行:** 2026-07-21 17:49 JST。
**依頼:** Rs 直接（「CLAUDE.md L3 変更を正式に custody-verify（逐語 vs realize-form 機構の解釈分離）して bank」）。
**対象:** CLAUDE.md:72 に追加された realize-form 文（commit `cdaf34c187`・CLAUDE.md 最終編集・on-disk == HEAD 実測）。
**性質:** L3 governance 変更の custody（逐語の忠実引用・inference のタグ付け）。⛔設計判定でない（機構の当否は pin arc + Rs）。

## ⭐ VERDICT: **PASS（実質忠実）+ custody-precision 勧告 1 件**

逐語は忠実に引用され、negative 制約は Rs 発話の直接の帰結。⚠ ただし **positive realize 機構（equality 拘束）を「Rs 直接指示で精緻化」の帰結として提示**しており、逐語が mandate した**原則**（physics-faithful）と**機構選択**（equality）の境界が L3 行で融合している。

## 1. 逐語の fetch（記憶からでなく記録から）

**Rs 逐語 = 「すてるなよ」**（3 文字）。一次記録 = `ARM_CONTROL_FORWARD_DESIGN_SCOPE_ARMCONTROLDESIGN_20260721.md §0.5`（commit `774892e1fd`・2026-07-21 13:58・**p4 経由 / p4 承認 13:56**）。corroboration = 同逐語が 3 doc（V02 design / PD1 prereg v14 / §14.27 corrected）にも記録。

**§0.5 が記録した係り先（受領文脈・必須）:** p11 が `_pp` の機構を「**毎回捨てて同じ値に戻すので、変化が積み上がらない**」と説明した**直後の応答** ⇒ 指す対象 = **毎ステップ物理計算の結果を捨てて保存値を書き戻す形**（＝**腕の** `_pp`）。

## 2. 分離テーブル（逐語 / 忠実帰結 / 設計解釈）

| 要素 | 出所 | CLAUDE.md:72 の扱い | 判定 |
|---|---|---|---|
| 「すてるなよ」 | **Rs 逐語** | Rs 直接指示として引用 | ✅ 忠実 |
| 物理を捨てる形を採らない（原則 = physics-faithful） | Rs 逐語の**一般化**（§0.5 P-1） | 「物理を捨てない physics-faithful な拘束」 | ✅ 忠実な帰結 |
| `_pp` 状態上書き（joint/body 上書き・全 DOF freeze）= 非認可 | Rs 発話の**係り先そのもの** | ⛔行で非認可と明記 | ✅ 忠実な帰結 |
| **positive 機構 = クリップに equality 拘束を置きソルバに解かせる** | **設計側の機構選択**（pin arc court） | 「Rs 直接指示…で精緻化 = …equality 拘束…」 | ⚠ **機構が逐語の帰結に昇格** |
| scope = 制御ループ内のみ・reset 対象外 | §0.5 + 既存 reset 例外 | 同 scope と明記 | ✅ 忠実 |

## 3. ⚠ custody-precision 勧告（唯一の finding）

**Rs 逐語「すてるなよ」が mandate したのは原則（physics-faithful・物理を捨てない）であり、`_pp` 状態上書きを rule out する（negative）。** 「クリップに equality 拘束を置きソルバに解かせる」= **physics-faithful を満たす 1 つの機構の設計選択**であって、Rs 逐語ではない。

根拠 2 点（いずれも on-disk）:
1. **§0.5 自身が機構を非排他に枠付け:** 「効かせたい拘束は solver に解かせる（equality **等**）か、actuator を通じて力で」。⇒ 記録側は equality を「等」の 1 選択肢としている。CLAUDE.md:72 は「等/例」を欠き、括弧内を `=`（定義的等価）で結び **equality を定義的な realize 形として提示**。
2. **逐語の係り先は腕の `_pp`**（§0.5）。CLAUDE.md:72 はそれを**クリップ pin の realize 形**へ適用。§0.5 は明記: 「**pin 実装そのものの owner = pin arc (d-a)/(d-b) court**・本書は腕・指の制御設計に P-1 を適用する範囲のみ」。⇒ クリップ pin への equality 機構の確定は **pin arc court の設計事項**であって、逐語からの直接帰結ではない。

⚠ **なぜ L3 で問題になり得るか:** CLAUDE.md:72 は全 session が読む governance 行。現行文は「Rs 指示で realize 形 = equality に精緻化された」と読め、**将来 pin arc が別の physics-faithful 機構を要しても「equality が THE 形」と誤って排除**して見える。⭐ ただし **passive なクリップ保持では equality 拘束が自然な physics-faithful 実現**であり（actuator 力は passive 保持に適用されない）、**実質的な設計誤りではない** — 問題は attribution の精度のみ。

**推奨（⛔ L3 文言修正は Rs 承認必須・本 verdict は上程 input）:** CLAUDE.md:72 realize-form 文を 2 層に分離 —
- **(a) Rs mandate（逐語由来・不変）** = physics-faithful / 物理を捨てない ⇒ `_pp` 状態上書き（全 DOF freeze 含む）は非認可。
- **(b) realize 機構（pin arc court）** = クリップに equality 拘束を置きソルバに解かせる（passive 保持の physics-faithful 実現の 1 形）。owner = pin arc (d-a)/(d-b)。

## 4. over-claim guard = present ✅

- §0.5 は明記: 「⛔『Rs が §0 例外 scope を formal に裁定した』とは書かない（実務 redirect であり formal 裁定の認定は p4/Rs court）」。
- CLAUDE.md:72 も「Rs 直接指示…で**精緻化**」= refinement 表現に留め、「Rs が機構を裁定した」とは書いていない。⇒ formal 裁定への昇格はしていない（§3 の finding は「精緻化」の帰結に機構が乗る点に限る）。

## 非主張

- ⛔ equality vs 他の physics-faithful 機構のどちらが正しいか = 設計判定（pin arc (d-a)/(d-b) + Rs）。
- ⛔ CLAUDE.md:72 の文言修正 = L3 ゆえ Rs 承認必須。本 verdict は上程 input。
- ⛔ 凍結/governance file は本 leg で一切編集していない（read-only 実測のみ）。

---
**L3 custody 検証 = 2026-07-21 17:49 JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
