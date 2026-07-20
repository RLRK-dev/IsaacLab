# WMSO D1.1-B / B1 — **導出 claim-set**（SHADOW 要件下で何が locator を供給し得るか）

- node: `T-WMSO` D1.1-B; 著者 = `w2:pQ` RS-TECH-LEAD2; 作成 = **2026-07-20 19:40 JST**（shell 実測）
- **前提となる確定事項**: Rs 裁定 C3 = slice の EP evidence profile = **SHADOW（rank 2・非 authority）**（custody `9ab6be4c9f302566511a22ab85ebca3fdaddea7789c682762041c8cc00aa9246` @ `42bbeafdda`）。⇒ **TENSOR_BINDING / NORMALIZATION とも rank 2 で required**、かつ **rank 2 に frozen の target-byte locator は存在しない**（premise claim-set v6 `40e5ca3bb09de3e1c632809e785bd6ed94a9941c3b31ba32067ba10eeac4483a` @ `99a1fc5c6a`・two-key 済）。
- **目的**: **B1 の選択肢を導出する前に、その導出が依存する事実を独立検証可能にする**。旧 A/A′/B は A′ 裁定破棄に伴い集合ごと未確定であり、**再提示ではなく要件からの再導出**を行う。

## ⛔ 本 artifact が主張しないこと（境界）

- ⛔**選択肢を確定しない・推奨しない・優劣を述べない**。下記 D-1..D-4 は「**凍結側の構造から論理的に到達可能な供給源の列挙**」であって評価ではない。
- ⛔**「rank 2 native だから良い」等の評価語を含めない**（評価は測定ではない）。
- ⛔implementation / training / closed-loop authority を解錠しない。
- ⛔**A′ を復活させない**（`WMSO_RS_B1_RULING_APRIME_20260720.md` = VOID・引用不可）。D-1 は A′ と同じ供給源を指すが、**裁定としては白紙**である。

## 検索空間（全 claim 共通・部分集合にしない）

| file | sha256 (先頭 16) |
|---|---|
| `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md`（frozen） | `00192d20ca00b654` |
| `WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md`（frozen） | `c474acea7c58acc2` |
| `WMSO_EvidencePolicy_v1.9.json`（frozen） | `e63176af9bc3a246` |

⚠**前回の根因を継承した規律**: 閉じた query は **①検索空間を凍結 3 file 全体に取り、②「何を意味する行を探すか」を先に述べ、③その述語を満たす別表現を列挙してから**張る（文字列 keying で 3 回・場所 keying で 1 回 取り逃した実績あり）。

---

## CLAIM D-A — rank 2 に proof kind を**追加要求できない**（B 側の拡張が塞がれている）

| 項目 | 内容 |
|---|---|
| **claim_id** | `B1D-A` |
| **主張** | proof set は**最小集合ではなく厳密集合**であり、B 側の spec が rank 2 に proof kind を追加要求することはできない |
| **期待真偽** | **TRUE** |
| **evidence** | EP JSON `policy_definition.proof_policy._domain` 逐語 = `"(component_kind, evidence_grade, applicability_class) -> **exact required ProofKind set**; REQUIRED cells only; UNKNOWN grade carries no authority-relevant claim"` ／ EP md `:114` = 「component に意味を持たない kind の混入 = **`E_PROOF_KIND_FOREIGN`**」 |
| **閉じた query** | 述語 =「proof set の外延が閉じているか（⊇ を許すか）」。表現候補 = `exact` / `厳密` / `過不足` / `superset` / `追加` を凍結 3 file 全体へ。加えて **`E_PROOF_*` code を全列挙**し、外延違反を捕捉する code の有無を確認（`E_PROOF_KIND_FOREIGN` が該当） |
| **反証条件** | (i) `_domain` に `at least` / `minimum` 相当の語があれば FALSE ／ (ii) `E_PROOF_KIND_FOREIGN` が「component に意味を持つ追加 kind」を許容する旨の但し書きを持てば FALSE ／ (iii) 他所に proof の追加を明示許可する規定が在れば FALSE |
| **含意** | 「rank 2 に `FINAL_ARTIFACT_HASH` を追加要求する」型の解は **frozen delta 無しには成立しない**（＝ D-3 に合流する） |

## CLAIM D-B — `EvidenceRecord.source_ref` は全 grade に在り、artifact 解決用途は未規定

| 項目 | 内容 |
|---|---|
| **claim_id** | `B1D-B` |
| **主張** | (a) `source_ref: str` は Optional でない必須 field。(b) 全 component が `EvidenceRecord` を持つ ⇒ **rank 2 にも存在**。(c) hash 対象 field ゆえ差替が `evidence_bundle_hash` に現れる。(d) **TENSOR_BINDING / NORMALIZATION の artifact 解決用途における指示対象は frozen 未規定**（ただし registry fixture の provenance 用途では規定あり） |
| **期待真偽** | **TRUE** |
| **evidence** | frozen DESIGN `:252`（`source_ref: str`）／`:269`（`records: tuple[EvidenceRecord, ...]`）／`:551`（hashed fields 列挙に `source_ref`）／`:396`（registry fixture 供給 static field の provenance に `source_ref` 要求・provenance 無き供給 = `E_MIGRATE_STATICS_ABSENT`）／EP md・EP JSON の `source_ref` 出現 = 0 |
| **閉じた query** | 述語 =「`source_ref` の**指示対象**を定める行があるか」。⚠**空間は凍結 3 file 全体**（EP のみに絞ると `:396` を落とす — 実際に 1 度落とした） |
| **反証条件** | (i) `source_ref` が Optional なら (a) FALSE ／ (ii) artifact 解決文脈で referent を定める行が在れば (d) FALSE |
| **含意** | 旧 A′ と同じ供給源。⚠**ただし A′ 裁定は破棄済ゆえ採否は白紙** |

## CLAIM D-C — `RECONSTRUCTION_SOURCES` は rank 2 の**必須 proof** であり、payload が path–sha 配列である

| 項目 | 内容 |
|---|---|
| **claim_id** | `B1D-C` |
| **主張** | (a) `RECONSTRUCTED_COMPATIBLE`（rank 2）の required proof set = `[RECONSTRUCTION_SOURCES, COMPATIBILITY_TEST, UNRESOLVED_DIFFERENCES, EVALUATOR_ARTIFACT]` であり、**`_all_13_components` wildcard ゆえ TENSOR_BINDING / NORMALIZATION 双方に適用**。(b) `RECONSTRUCTION_SOURCES` の payload は **`[{path, sha256}…]`（path bytes 昇順）の配列**で、`artifact_hash` はその **集約 H_WCJ**。(c) **配列に何を載せてよいかの制約は frozen 未規定** |
| **期待真偽** | **TRUE** |
| **evidence** | EP JSON `proof_policy.RECONSTRUCTED_COMPATIBLE._all_13_components` 逐語 ／ EP md `:23`「RECONSTRUCTION_SOURCES ｜ 復元資料列挙（path+sha）」／`:127`「`H_WCJ([{path, sha256}…] path bytes 昇順)` の集約 hash」／ EP JSON `proof_binding` の当該 rule = `"artifact_hash = H_WCJ of path-sha object array, path bytes ascending"` |
| **閉じた query** | 述語 =「`RECONSTRUCTION_SOURCES` の payload 構造と内容制約を述べる行」。凍結 3 file 全体で `RECONSTRUCTION_SOURCES` / `復元資料` / `reconstruction` を列挙し、**構造記述と内容制約を分けて**判定 |
| **反証条件** | (i) rank 2 の required set が component 別に分岐し片方に本 kind が無ければ (a) FALSE ／ (ii) 配列要素の意味・範囲を限定する行（例「claim target 自身を含めてはならない」）が在れば (c) FALSE |
| **⚠未主張（重要）** | ⛔**「配列に claim target を載せてよい」とは主張していない** — **未規定である**ことのみを主張する。載せる場合は **B 側の宣言**が要り、その妥当性は本 artifact の射程外 |

## CLAIM D-D — rank 2 の他 3 kind は target-byte locator を供給しない

| 項目 | 内容 |
|---|---|
| **claim_id** | `B1D-D` |
| **主張** | `COMPATIBILITY_TEST`（`artifact_hash = test record sha256`）／`UNRESOLVED_DIFFERENCES`（`artifact_hash = doc sha256`）／`EVALUATOR_ARTIFACT`（`artifact_hash == EvidenceRecord.evaluator_artifact_hash`）は、いずれも **自身の artifact を指し、claim target の bytes を供給しない** |
| **期待真偽** | **TRUE** |
| **evidence** | EP JSON `proof_binding` の各 rule 逐語（上記） |
| **閉じた query** | 述語 =「その kind の `artifact_hash` は **claim target 自身**か、**別 artifact 自身**か」。rank 2 の 4 kind すべてに適用（`RECONSTRUCTION_SOURCES` = 配列の集約 hash ゆえ **これも claim target 自身ではない**） |
| **反証条件** | いずれかの rule が claim target への束縛を述べていれば FALSE |
| **含意** | ⚠**`RECONSTRUCTION_SOURCES` を locator に使う場合、解決は 2 hop になる**（proof item の ref → 配列 → 該当 entry の path）。frozen は entry の sha と `claim_target_hash` の一致を**要求していない**ため、それも B 側の宣言事項 |

---

## 導出される供給源の列挙（**評価ではない**）

| # | 供給源 | frozen delta | 依拠する未規定領域 | 解決 hop |
|---|---|---|---|---|
| **D-1** | `EvidenceRecord.source_ref`（= 旧 A′ と同一供給源・**採否は白紙**） | 不要 | `source_ref` の artifact 解決時 referent（`B1D-B`(d)） | 1 |
| **D-2** | `RECONSTRUCTION_SOURCES` 配列の entry | 不要 | 配列の内容制約（`B1D-C`(c)）＋ entry の sha と claim_target の一致（`B1D-D` 含意） | **2** |
| **D-3** | frozen schema delta（`ArtifactSlot` に ref 追加 等） | **要**（supersession + Rs review） | — | 1 |
| **D-4** | hash 由来 canonical ref（= 旧 A） | 不要（ただし CAS を要求） | 実装環境が content-addressed store であること | 1 |
| ⛔ | rank 2 への proof kind 追加 | **FORECLOSED**（`B1D-A`） | — | — |

⚠**本表は「到達可能性」の列挙であり、実現可能性・妥当性・コストを判定していない**。D-2 の 2 hop、D-4 の CAS 要求、D-1 の用途転用がそれぞれ許容されるかは**未判定**。

## 未測定（本 artifact が主張していない事項）

- `COMPATIBILITY_TEST` が rank 2 で何を証明する義務を負うか（過去に一度、可逆性をここへ誤って委譲した経緯あり — §12 R1）
- D-1..D-4 各案の実装コスト・運用上の含意
- `normalization` slot 固有の追加制約（rank 2 では TB と同じ wildcard 被覆であることのみ確認済）
- **どの案を採るべきか**（＝ Rs 裁定事項。本 artifact は判断材料の前提のみを固める）
