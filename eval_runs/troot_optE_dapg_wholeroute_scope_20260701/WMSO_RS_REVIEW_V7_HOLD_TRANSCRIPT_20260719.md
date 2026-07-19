# Rs review v7（RV7）— D1.1-A v2.9.2 宛 ⛔HOLD as-received transcript

- node: `T-WMSO` D1.1-A; 転記者 = w2:pQ、転記 = 2026-07-19 20:18 JST（実測）
- 原文 = Rs から pQ への chat message（受信 = 本 session、pQ の 20:10 JST date 実測の直前）。**独立 file 原本なし（byte identity N/A — B1B7/C1C3/R transcript と同類）**。fidelity: **Rs 確認 PENDING**（RV6 §1 形式 — 確認は別 record で固定、本 file は以後不変）。
- 対象 = DESIGN v2.9.2（`e83a29061400b42c18a6607c96295e0ede2984cda8b9b047f338512ccb0b7f96`）+ Rs review 環境の companion set（⚠ **旧 zip 世代**: EP v1.7 `586fec2a…` / JSON `3fb7a452…` / manifest `a5d0aa0c…` — 転記者注 §末尾参照）。
- 引用規約: 本 review の指摘は **RV7-P0-1..7 / RV7-R-1..4** で完全修飾する（RV4 §1.3 規約）。

---

## 原文（逐語 — BEGIN）

## ユーザー向け

### 判定

**総合判定: HOLD**

v2.9.2の差分には正しい修正がありますが、次の2点から最終候補にはできません。

* **提示された一式がexact-pinになっていない**
* **前回指摘した規範上のブロッカーが複数残っている**

したがって、現時点では以下へ進めません。

```text
pS最終照合: 不可
pN exact-pin再検証: 不可
D1.1-A freeze: 不可
implementation / training / authority: CLOSED継続
```

---

## SHA・custody確認

再計算値は次のとおりです。

| artifact                | 提示された実ファイルのSHA-256                                                 | 判定        |
| ----------------------- | ------------------------------------------------------------------ | --------- |
| DESIGN v2.9.2           | `e83a29061400b42c18a6607c96295e0ede2984cda8b9b047f338512ccb0b7f96` | ファイル実体は正常 |
| EvidencePolicy Markdown | `586fec2a770207b5726dee557fe9a5c1a437baadc39b75c5558e473d1cdf3efe` | 旧v1.7     |
| EvidencePolicy JSON     | `3fb7a452a14867ca7e0e0ec3dbf0c7b63f87edc7527e5d095a086b9802aa3b81` | 旧metadata |
| manifest                | `a5d0aa0cfa82b436738f3246b0fee9bbdeeff6b4b1b7173a8110b8d7402cc40e` | v2.9世代のまま |

v2.9.2本文は、EvidencePolicy v1.7.1とJSON SHA `ed10c77a…`を参照しています。
しかし、現在提示されているEvidencePolicyはv1.7／親設計v2.9であり、JSON metadataも`source_markdown ... v1.7`のままです。
manifestもDESIGN v2.9、EvidencePolicy v1.7、旧SHAを固定しています。

なお、JSONについては、旧ファイルの次の文字列だけを、元の書式を保ったまま変更すると、

```text
WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md v1.7
↓
WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md v1.7.1
```

設計記載のSHA、

```text
ed10c77a4d9957368380195ee081368da3fdaa170b03ec275584e08d1c301faa
```

を正確に再現できました。したがって、**H-2のSHA主張自体は内部整合しています**。ただし、その更新済み実ファイルは今回提示されていないため、custody上のPASSにはできません。

DESIGN v2.9.2についても、実SHAは上記`e83a…`ですが、本文のversion履歴では本版のfull SHAとbank commitがまだ記録されていません。

---

## 解消を確認できた点

### 1. migrationの欠損schema規則は解消

前回のP0-5は解消しています。

構成型側とdisposition表の双方が、次へ統一されました。

```text
fixture供給可能 → Draft
fixture供給不能 → E_MIGRATE_STATICS_ABSENT
UNKNOWN／placeholder生成禁止
```

**判定: PASS**

### 2. ネスト型とenumのinline化は改善

次が具体化されています。

* `SnapshotRef`
* `HashRef`
* `TerminalOutcome`
* `InterruptOutcome`
* `Dtype`
* `ExprKind`
* `TerminationClass`
* `InterruptReason`
* `FailClosedAction`

ただし後述のとおり、`IdentityKind`が残っています。

**判定: PARTIAL PASS**

### 3. DESIGNのtitle／statusはv2.9.2へ同期

title、created履歴、statusはv2.9.2で整合しています。

**判定: PASS**

---

# 未解消ブロッカー

## P0-1. EvidencePolicy v1.7.1の実体がなく、現行v1.7は依然矛盾している

v2.9.2は「EP旧重複行統一」を主張していますが、現在提示されているMarkdownは旧v1.7です。

旧ファイルには、依然として以下が同時に存在します。

```text
REPRODUCED_OUTPUT_HASH == claim_target_hash
```

と、

```text
REPRODUCED_OUTPUT_HASH == FINAL_ARTIFACT_HASH
```

さらにTTCBも、

```text
(claim_target_hash, manifest_hash)
```

と、

```text
(FINAL_ARTIFACT_HASH, TRAIN_RUN_MANIFEST)
```

の2規則が併存しています。

したがって、現在提示されたbytesに対しては、

```text
Markdown ↔ JSON parity: FAIL
R1 close: 未確認
```

です。

---

## P0-2. ApplicabilityResolverの入力と優先順位は未修正

v2.9.2でも設計側は、

```text
ApplicabilityResolver(kind, lineage, component)
```

のままです。

EvidencePolicyも、

```text
instance → lineage → profile → default
```

の順序を維持しています。

JSONも同じ順序です。

このままでは、例えば、

```text
requested_profile = OFFLINE_REPLAY
lineage = BC_ONLY
component = TRAINING_DATASET
```

で、lineage層の`REQUIRED`がprofileの「—」より先に適用されます。`TRAINING_PROVENANCE`でも同じ問題が起きます。

必要な形は少なくとも次です。

```text
resolve_applicability(
    identity_kind,
    training_lineage,
    explicit_none_components,
    requested_profile,
    component
)
```

優先順位は、

```text
1. instance EXPLICIT_NONE
2. profile の「—」
3. lineage条件
4. default
```

とする必要があります。

**判定: FAIL**

---

## P0-3. CONTROL_MODE／HANDOFF_SCHEMA projectionは依然未定義

JSONには次の名称だけがあります。

```text
CONTROL_MODE   = H_WCJ(control_mode_projection)
HANDOFF_SCHEMA = H_WCJ(handoff_schema_projection)
```

v2.9.2でenum memberや`HandoffSchemaSpec`のfieldは増えましたが、次はまだ決まっていません。

* projectionの正確なkeyed object
* slot stateを含めるか
* tuple順を保持するか、IDでsortするか
* `accepted_handoff`を含めるか
* empty tuple、EXPLICIT_NONE、UNKNOWNの表現
* golden vector

したがって、実装ごとに異なる`claim_target_hash`を生成できます。

**判定: FAIL**

---

## P0-4. CONFIG_HASHの`stage`入力が依然存在しない

JSONは次で分岐しています。

```json
{"identity_kind":"LEARNED","stage":"bc_of_bc_then_rl"}
{"identity_kind":"LEARNED","stage":"final"}
```

しかし、以下のいずれにも`stage`がありません。

* `EvidenceRecord`
* `ProofItem`
* `certify_definition`
* resolver API
* certificate

設計にはBC configとfinal configのfieldはありますが、「どのcomponent claimがどのstageを使用するか」のtotal mapがありません。

必要なのは、例えば次のどちらかです。

```text
(component_kind, training_lineage) → config target
```

を完全定義する、またはEvidenceRecordにtypedなstageを追加する。

**判定: FAIL**

---

## P0-5. validate_handoffがauthority epochを受け取れない

関数は依然として、

```text
validate_handoff(
    invocation,
    offer,
    producer_definition,
    consumer_definition
)
```

ですが、検査内容は、

```text
offer.control_epoch == 現在のauthority epoch
```

を要求しています。

現在epochの入力がないため、純粋validatorでは検査できません。

必要な形は例えば次です。

```text
validate_handoff(
    invocation,
    offer,
    producer_definition,
    consumer_definition,
    authority_epoch_snapshot
)
```

authority managerがCAS、epoch更新、使用済みoffer拒否を担当する責務分離自体は妥当です。しかし、validatorへ比較対象を渡す境界が不足しています。

**判定: FAIL**

---

## P0-6. EvidenceEvaluationCertificateがcertification／eligibilityへ接続されていない

`EvidenceEvaluationCertificate`は定義されていますが、その後の処理系に接続されていません。

具体的には、

* `DefinitionCertificationResult`のfield集合がない
* evaluation certificateを返す場所がない
* `ContractCertificate`にevaluation bundle hashがない
* `EvidenceRecord.grade`と`assigned_grade`の一致規則がない
* usage eligibilityはrawな`evidence_bundle`を再入力として受け取る
* eligibilityが`EvidenceRecord.grade`と`assigned_grade`のどちらを使うか未定義

です。

これでは「gradeを評価器による測定値として固定する」という目的が閉じません。

最低限、次のいずれかが必要です。

```text
DefinitionCertificationResult.evidence_evaluations[]
ContractCertificate.evidence_evaluation_bundle_hash
UsageEligibilityReportはevaluation certificateのassigned_gradeを使用
```

または、certification時に`EvidenceRecord.grade == assigned_grade`を証明し、その証明hashをcertificateへ束縛します。

**判定: FAIL**

---

## P0-7. `IdentityKind`がinlineされていない

`ExecutionBundle.kind`は`IdentityKind`型を使用しています。

しかしファイル全体に、

```text
class IdentityKind(...)
```

または、

```text
IdentityKind = {LEARNED, SCRIPTED, WAIT}
```

の明示定義がありません。

line 143では「enum member全数inline」としていますが、その列挙にも`IdentityKind`は含まれていません。

意味は推測できますが、self-contained normative artifactでは推測に依存できません。

**判定: FAIL**

---

# 記録・同期上の未修正

## R-1. 現行行にEvidencePolicy v1.6参照が残っている

設計の現在規則に、

```text
全表 = EvidencePolicy v1.6
```

が残っています。

また現在の三面一致試験も、

```text
WMSO_EvidencePolicy_v1.6.json
```

をnormative fixtureとしています。

履歴説明中のv1.6は残して構いませんが、line 264とline 534は現在規則なので、v1.7.1または次のsemantic版へ更新が必要です。

---

## R-2. mutation testに旧field名が残っている

現在も、

```text
grade/source_ref/proof/artifact_hash
```

です。

少なくとも次へ直す必要があります。

```text
grade
source_ref
proof
claim_target_hash
evaluator_artifact_hash
```

---

## R-3. manifestが完全に旧版

manifestは、

* 現在地がDESIGN v2.7
* artifact表がv2.9／EP v1.7
* DESIGN SHAが`e64c…`
* JSON SHAが`3fb7…`

のままです。

v2.9.2の実SHA `e83a…`、更新後EvidencePolicy、JSON、pS／pN recordを固定した新manifestが必要です。

---

## R-4. JSON hash説明の型記述が不正確

JSON metadataは`policy_definition`を「int-and-string-only」としていますが、実際にはbooleanも含みます。

これは現行definition hashの計算結果を壊しませんが、説明は次へ修正すべきです。

```text
ASCII key/string、integer、booleanのみ。
float・null・非ASCIIなし。
```

---

## 重要なhash上の帰結

現在記載されている、

```text
evidence_policy_definition_hash =
066eed1049f4f51a89dd86e9d50614a65adba070b2ff650424ea7cef05dec4ea
```

とJSON file SHA `ed10c77a…`は、**metadata-only更新**としては整合しています。

しかし、上記の次の修正は`policy_definition`自体を変更します。

* ApplicabilityResolverの入力・優先順位
* CONTROL_MODE／HANDOFF_SCHEMA projection
* CONFIG_HASH stage map

したがって、これらを直した最終版では、

```text
evidence_policy_definition_hash: 必ず変更
JSON file SHA: 必ず変更
EvidencePolicy semantic version: 更新必要
```

です。

**`066e…`／`ed10…`を最終exact pinとして使ってはいけません。**

---

## 次の正確な工程

1. `IdentityKind`を明示inline
2. ApplicabilityResolverの入力と優先順位を修正
3. CONTROL_MODE／HANDOFF_SCHEMA projectionを完全定義
4. CONFIG_HASH stage mapを完全定義
5. `validate_handoff`へepoch snapshot入力を追加
6. EvidenceEvaluationCertificateをcertification／certificate／eligibilityへ接続
7. EvidencePolicy MarkdownとJSONを同時修正
8. line 264、527、534を修正
9. `policy_definition` hashを再計算
10. DESIGN、EvidencePolicy、JSON、manifestの全SHAを再計算
11. 新SHAをmanifestへ固定しbank commitを記録
12. その候補へpS差分照合
13. pS PASS後、その最終SHAだけをpNへ渡す
14. pN PASS後にfreeze判定

現時点では、設計の「open = 0」という記述は支持できません。

```text
WMSO scope: CLOSED
D1.1-A DESIGN: HOLD
D1.1-A freeze: HOLD
implementation / training / authority: CLOSED
次に許可される作業: 上記の設計・EvidencePolicy限定修正のみ
```

## Internal working output

**Goal**

Validate the uploaded DESIGN v2.9.2 against v2.9, the previously reported blockers, and the currently available companion artifacts.

**Checks performed**

* Recomputed SHA-256 for the new design and all available companions.
* Produced a byte-level diff from v2.9 to v2.9.2.
* Confirmed that the diff contains six limited change areas.
* Reconstructed the claimed JSON metadata-only update and reproduced SHA-256 `ed10c77a...`.
* Rechecked resolver precedence, claim-target definitions, CONFIG_HASH binding inputs, handoff epoch handling, evaluation-certificate flow, migration semantics, version references, test-plan field names, and manifest pins.

**Result**

* New design file integrity: PASS.
* Migration fail-closed correction: PASS.
* Nested type and enum expansion: PARTIAL PASS.
* Companion artifact custody: FAIL.
* Normative semantic closure: FAIL.
* Exact-pin readiness: FAIL.
* Overall verdict: HOLD.

**Verification limits**

The actual EvidencePolicy v1.7.1 Markdown, updated JSON bytes, updated manifest, v2.9.1 artifact, pS §14 record, pN R1–R3 transcript, and repository bank commits were not supplied. Claims about those missing artifacts were therefore checked only for internal consistency, not byte custody or provenance.

## 原文（逐語 — END）

---

## 転記者注（本文外 — pQ の custody 事実確認、2026-07-19 20:18 JST 実測）

1. **review 環境の companion set は旧 zip 世代**: RV7 記載の EP `586fec2a…`（v1.7）/ JSON `3fb7a452…` / manifest `a5d0aa0c…` は、**現在の `~/Downloads/` にも repo worktree にも存在しない**（20:10 実測: Downloads の実 bytes = EP v1.7.1 `27701698ed38…`〔17:37 配置〕/ JSON `ed10c77a…`〔17:37〕— repo committed blob と一致）。19:49 の design 単体納品時に companion の同梱 pointer を添えなかった pQ の bundle 納品 gap が原因。**custody FAIL 判定自体は妥当**（review 手元に bytes が無ければ PASS にできない — freeze-then-verify-then-bank 規律と同根）。
2. **帰結**: RV7-P0-1 の semantic 部分（重複行）は v1.7.1（`27701698ed38…`）で既修正・pN R1-R3 CLOSE で独立確認済みだが、**custody 部分（bytes 提示）は本 fold round の納品で解消する**。RV7-P0-2..P0-7 / R-1..R-4 は**最終版 artifact 上にも実在**（pQ on-disk 検証済み — fold 対象）。
3. 「`066e…`/`ed10…` を最終 exact pin にしない」= 本 fold で EP semantic 版 v1.8 へ bump・definition hash / JSON sha 再計算（RV7 工程 9-11）。
