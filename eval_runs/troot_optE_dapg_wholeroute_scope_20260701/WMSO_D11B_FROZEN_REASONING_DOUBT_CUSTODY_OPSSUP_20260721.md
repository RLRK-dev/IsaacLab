# D1.1-B 凍結 file の理由づけに出た疑義 — OPS-SUP evidence/custody 検証

**Verifier:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**発行:** 2026-07-21 14:52 JST。
**依頼:** `w2:pQ` RS-TECH-LEAD2（Rs 承認済の照会）。D1.1-C design debate cycle-1 で、**凍結 (FROZEN/CUSTODY-CLOSED) の D1.1-B v13 の理由づけ**が別の凍結 file（EP md）と整合しない可能性を検出。
**性質:** evidence（逐語の独立再測）+ custody（凍結 artifact に疑義が出た場合の手続）。⛔**本 leg は設計判定ではない** — 疑義が real か、D-1 採択が影響を受けるか、は **pS 設計軸 + Rs**（後述）。

## ⭐ VERDICT

1. **逐語 3 本 = 独立再測で faithful**（+ pQ 引用より primary な locus `:256` を surface）。
2. **evidence 観察 = 「同じ code 名・別の測定面」family に該当**（設計判定でなく観察として提示・後述）。
3. **custody 手続 = 下記 5 段**（凍結は編集しない・別記録・軸で route・Rs 上程・面 flag）。

---

## (1) 逐語 faithfulness — ✅ 全て on-disk 直読で一致（凍結 pin で実測）

| # | file | 凍結 sha256(16) | 行 | 逐語（on-disk 実測） | pQ relay と |
|---|---|---|---|---|---|
| a | EP md | `c474acea7c58acc2` | :114 | 「…component に意味を持たない kind の混入 = `E_PROOF_KIND_FOREIGN`」 | ✅一致 |
| b | EP md | `c474acea7c58acc2` | :129(iii) | 「他 component 向け kind の混入（例: POLICY_ARTIFACT claim に INPUT_SCHEMA_HASH）→ E_PROOF_KIND_FOREIGN」 | ✅一致 |
| c | v13 | `5a1874d3be8b98b8` | :471 | 「rank 2 への proof 追加 = **FORECLOSED**（`_domain` = exact set + `E_PROOF_KIND_FOREIGN`）」 | ✅一致 |

- 凍結 2 file とも sha = frozen pin と完全一致（EP md `c474acea7c58acc2` / v13 `5a1874d3be8b98b8`、on-disk == HEAD 実測）。⇒ 疑義は**凍結された exact bytes に対して**評価される。
- ⭐**:471 より primary な locus = v13 `:256`**（D-1..D-4 選定表の行）: 「rank 2 への proof **kind** 追加 | ⛔FORECLOSED | `proof_policy._domain` = 「exact required ProofKind set」＋ `E_PROOF_KIND_FOREIGN`（`B1D-A`）。B 側 spec では不可・D-3 に合流」。:471 は changelog 再掲で「kind」を落とした要約。**疑義評価は :256 を一次に**。
- 検証済 artifact（sha 独立照合）: debate verdict `9851f165a5fc45eb` @ `7f6d038a30`（§0）／design v1 `726f684c52421928` @ `33e67626da`。

## (2) evidence 観察（⛔観察であって設計判定でない）

**同じ error code `E_PROOF_KIND_FOREIGN` が、2 つの凍結 file で異なる測定面に関連づけられている（表面上）:**

- **EP md**: `E_PROOF_KIND_FOREIGN` の `_domain` は **component 索引**で定義（:114「component に意味を持たない kind」／:129(iii) 例「他 component 向け kind」）。**grade/rank 条件は別 code**が担う（:130 `E_GRADE_INAPPLICABLE` = `identity_kind ∈ {SCRIPTED,WAIT} ∧ grade=EXACT_TRAIN_TIME`／:132 `E_GRADE_MISMATCH`）。
- **v13 `:256`/`:471`**: `E_PROOF_KIND_FOREIGN` を **grade/rank（rank 2）の制限**に invoke（`proof_policy._domain` = 「exact required ProofKind set」で rank 2 への proof kind 追加を FORECLOSE）。

⇒ **表面上、`_domain` の索引が component（EP md）と grade/rank（v13）で食い違う。** これは本 project で反復した **「同じ定数/名前・別の測定面」family**（[[feedback-same-constant-is-not-same-measurement-surface-2026-07-18]] / [[the-boundary-question-and-the-identity-question-are-different]]）に該当する。

**⛔ 私が判定しないこと（設計軸 = pS + Rs）:**
- `proof_policy._domain` が component 索引か grade/rank 索引か（＝ rank 2 の「exact required set」が component の意味的 kind set と一致するなら **同一機構の適用**で整合／別物なら **code の借用 = 不整合**）。
- 疑義が real な場合に v13 の理由づけをどう扱うか。

## (3) custody 手続 — 凍結 artifact に疑義が出た場合（pQ の②への回答）

**⭐ 原則: 疑義は凍結を解かない。** 凍結 bytes は Rs が version bump を認可するまで SSOT のまま。疑義は**凍結 bytes に対して評価される別記録**。凍結 file を編集して「直す/注記する」と、疑義を測る baseline（pin）自体を壊す（[[feedback-verification-must-not-destroy-its-baseline-2026-07-14]]）。

1. **凍結 file を編集しない**（v13 / EP md）。✅ pQ は未編集。frozen sha を intact に保ち、疑義が exact bytes に対して評価される状態を維持。
2. **疑義を別記録に置く**（debate verdict §0 が既に一次記録。専用 doubt 記録に拡張可）。内容 = 凍結 pin での逐語 + **疑義を「問い」として**明記（断定でなく）+ 非主張（D-1 の可否は判定せず・凍結未編集）+ custody chain（sha/commit）。
3. **軸で route:**
   - 逐語 faithfulness = evidence（OPS-SUP）= **本記録で CONFIRMED**。
   - 理由づけの整合性（`E_PROOF_KIND_FOREIGN` の索引）= **設計 semantics = pS（MWSO-DESIGN）**。pS は contracts_v2 / EP 機構を設計軸批准した owner ゆえ、この「機構の適用が正しいか」の適格 verifier。⇒ pQ は pS へ設計軸 read を依頼。
   - 凍結 file の訂正（version bump / 再 freeze）= **Rs 専権**（freeze holder。frozen delta = Rs 専権・v13 `:254` 逐語「必要になった場合は Rs 専権」+ `prohibited.md`）。
4. **Rs へ上程**（本記録 + pS 設計軸 read + 影響範囲）。Rs 判断の 3 分岐: (a) 整合（索引が一致）→ action 無し／(b) 理由づけに欠陥だが D-1 は別根拠で成立 → addendum 記録・再 freeze 不要／(c) 採択の再開が要る → Rs 認可の version bump + 再 freeze + two-key 再実行。
5. **面に loud flag**（LEDGER = p6 court）: D1.1-B v13 行に「:256/:471 理由づけに疑義記録・pS 設計軸 + Rs 裁定待ち」。⚠**疑義は FROZEN 状態を変えない** — 解凍は Rs のみ。D1.1-C debate / slice が「理由づけが疑義下」と分かる状態にする。

## (4) 影響範囲（Rs が weigh する材料・⛔私の裁定でない）

- `:256` の「rank 2 proof kind 追加 = FORECLOSED」は **D-1 選定表の 5 案の 1 つ（却下された代替案）**。D-1 の**採択**は `:252` の積極理由（frozen delta 不要 / 1 hop / B 側宣言 1 個 / 意味論適合）に立つ。
- D-1 の**反証条件 4 件**（`:258-262`）に「rank-2 foreclosure の理由づけが誤り」は**含まれない**。
- ⇒ **疑義が touch するのは「ある代替案を foreclose する理由づけ」であって「D-1 を採択する積極根拠」ではない**（観察）。かつ `:256` は当該代替案を「**D-3 に合流**」とも述べ、D-3（frozen schema delta）は「不要 + 必要時 Rs 専権」で別途却下済。⇒ 代替案の disposition は D-3 側に畳まれる。**この観察は D-1 採択が疑義に対して robust であることを *示唆* するが、確定は pS + Rs**。

## 非主張

- ⛔ `E_PROOF_KIND_FOREIGN` の索引が整合するか（設計 semantics）= pS + Rs。本 leg = 逐語 faithfulness + custody 手続 + 影響範囲の observation。
- ⛔ D-1 採択の可否・凍結の訂正要否 = Rs 専権。本記録は上程 input。
- ⛔ 凍結 file は本 leg でも一切編集していない（read-only 実測のみ）。

---
**evidence/custody = 2026-07-21 14:52 JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
