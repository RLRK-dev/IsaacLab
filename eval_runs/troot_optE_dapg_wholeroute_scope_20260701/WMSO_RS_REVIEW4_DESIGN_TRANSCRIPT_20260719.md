# Rs review-4 (WMSO D1.1-A DESIGN v1 宛) — session-received transcript

- **provenance: 本文書は w2:pQ (RS-TECH-LEAD2) が 2026-07-19 09:2x JST に session 内で Rs から受領した design review の転記である。転記者 = pQ。Rs 本人による原本 file は存在しない（会話 message として受領）。⚠ 転記の正確性は Rs 確認 PENDING — 確認までは「as-received transcript」として扱い、Rs 逐語の一次根拠には prereg 引用済み部分（review-1..3）と本 transcript の Rs 確認後を用いる。**
- 対象: `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md` v1 (sha256 `8bec472a6ac1…`、Rs は sandbox 写しをレビュー)
- 転記日時: 2026-07-19 10:5x JST（CC Debate cycle-1 U1 fix）
- 転記範囲: Rs message 全文（「ユーザー向け」+「Internal working output」+ 参照 5 件）。省略なし。sandbox リンク表記は原文のまま。

---

以下、受領 message の verbatim 転記:

## ユーザー向け

# 判定

**DESIGN HOLDです。修正後PASS見込みです。**

前回のscopeレビューで持ち越した事項はかなり正確に反映されています。特に、

* static定義とruntime記録の分離
* `SkillActionId`と`SkillDefinitionHash`の分離
* `ExecutionBundleHash`
* component別Evidence
* proof obligation
* `EvidenceBundleHash`
* 全数値の有限値検査
* lineage許容表
* v1 compatibility shim
* standalone試験とmonorepo試験の分離

まで入っており、設計の方向は正しいです。実装をまだ閉じている工程管理も適切です。

ただし、現在のままでは **pN DESIGN PASS-CLOSEには進めません**。主なブロッカーは6件です。

---

# P0：DESIGN PASS前の必須修正

## 1. 静的なスキル契約validatorと実行時validatorを分離する

現在のAPIは、

```text
validate(definition, evidence_bundle)
  → ValidationReport
  → ContractCertificate
```

ですが、その同じvalidatorに、

* 実際のoutcomeが宣言済みtermination classか
* interrupt checkpointが宣言済みか
* `HandoffOffer.producer_invocation_id`が現在invocationと一致するか

という**実行時検査**が含まれています。

これは、§1で実現したstatic/runtime分離をvalidator層で再び混合しています。

次の4系統に分けてください。

```python
certify_definition(
    definition,
    evidence_bundle,
    evidence_policy,
) -> DefinitionCertificationResult

validate_invocation_start(
    invocation,
    definition,
    belief,
) -> LifecycleValidationReport

validate_outcome(
    invocation,
    outcome,
    definition,
) -> LifecycleValidationReport

validate_handoff(
    invocation,
    offer,
    producer_definition,
    consumer_definition,
) -> HandoffValidationReport
```

役割は次です。

```text
Definition certificate:
  静的契約と証拠の整合性を証明

Lifecycle validation:
  1回の実行、終了、中断、handoffの妥当性を検査
```

実行時違反が発生しても、静的な`ContractCertificate`自体が無効になるわけではありません。実行インスタンス側の違反として記録します。

---

## 2. Execution identityとtraining provenanceを分離する

現状の`ExecutionBundle`には`training_lineage`が含まれていますが、`ExecutionFamily`、BC base/config、demo datasetなど、§3の検証表が参照する実体フィールドは型に定義されていません。

さらに、training lineageを`ExecutionBundleHash`へ入れると、

> 実行時には同一のpolicy weight、architecture、binding、normalizer、configなのに、provenanceの再分類だけでSkillActionIdが変わる

可能性があります。

SDMのデータ集約に使うaction identityは、**実行挙動を決める要素**で固定すべきです。学習履歴は証拠・provenanceであり、実行identityから外す方が適切です。

推奨構成：

```python
@dataclass(frozen=True)
class ExecutionBundle:
    kind: IdentityKind
    executable_artifact_hash: str
    model_architecture_hash: str | None
    tensor_binding: ArtifactSlot
    normalization: ArtifactSlot
    control_mode: ControlMode
    runtime_config_hash: str


@dataclass(frozen=True)
class TrainingProvenance:
    execution_family: ExecutionFamily
    training_lineage: TrainingLineage
    final_artifact_hash: str
    bc_base_hash: str | None
    bc_config_hash: str | None
    demo_dataset_hash: str | None
```

検証で、

```text
TrainingProvenance.final_artifact_hash
==
ExecutionBundle.executable_artifact_hash
```

を要求します。

### `None = ABSENT`も修正が必要

現在はD1.1-Bまで`tensor_binding_hash=None`とし、それを`"ABSENT"`としてaction identityへ含める設計です。

しかし、この`None`は「bindingが実際に存在しない」のではなく、**まだ回収・定義されていない**という意味です。知識不足と実体不存在を混同しています。

少なくとも次の3値が必要です。

```text
KNOWN(hash)
EXPLICIT_NONE
UNKNOWN
```

学習済みpolicyではtensor bindingは必ず存在するため、`UNKNOWN`の間は最終的な`SkillActionId`を発行しない方が安全です。

```text
DraftSkillDefinition:
  UNKNOWNを許す
  SkillDefinitionHashは発行可能
  最終SkillActionIdは発行不可

CertifiedSkillDefinition:
  実行決定要素がすべて解決済み
  SkillActionIdを発行可能
```

---

## 3. JCS minimalの主張を修正する

次の記述は、そのままでは成立しません。

```text
json.dumps(..., sort_keys=True, ensure_ascii=False)
がRFC 8785出力と一致する
```

RFC 8785のobject key順序は**UTF-16 code unit順**です。一方、Pythonの通常の文字列sortはUnicode code point順です。非BMP文字を含むkeyでは結果が異なります。RFC自身も、UTF-8/UTF-32順ではJCSと異なる場合があると明記しています。([RFCエディタ][1])

ローカルでも、例えば絵文字とU+FB33をkeyにした場合、Pythonの`sort_keys=True`はRFC 8785の期待順と逆になります。

修正案は二択です。

### 案A：RFC 8785を正しく実装する

* UTF-16 code unitによるkey sort
* lone surrogate拒否
* duplicate key拒否
* JCS文字列serialization
* golden test vector追加

### 案B：WMSO専用subsetとして明示する

```text
WMSO Canonical JSON v1
```

として、

* hash-visibleなobject keyは7-bit ASCII限定
* identifierはNFC済みを要求
* non-NFC入力は正規化せず拒否
* lone surrogate拒否
* arbitrary dictをhash入力に許さない

とします。

ただし、scope上でJCSを要求しているなら案Aが無難です。

### 固定小数6桁も危険

```text
"0.831000"
```

のような一律6桁化は、異なる閾値を同じ値へ丸める可能性があります。identity hashで使用するなら、次のいずれかにしてください。

* exact canonical decimal
* 物理量ごとに定義したscaled integer
* 元のdecimal文字列を厳密に正規化

例えば、

```python
CanonicalDecimal("0.831")
```

を設け、

* exponent禁止または正規化規則を固定
* trailing zero除去
* negative zero禁止
* binary floatを経由しない

とします。

なお、JCS自体はUnicode正規化を行わず、文字列をそのまま保持します。NFCを使う場合は、JCS処理ではなく**WMSO schemaの事前制約**として定義してください。([RFCエディタ][1])

---

## 4. Evidence modelを閉じ切る

現在、`ComponentKind`には7種類しかありませんが、`ClosedLoopProfile`はまだenumに存在しない`TENSOR_BINDING`と`CONTROL_MODE`を要求しています。

これはD1.1-A時点でも型として表現不能です。

### 修正

`TensorBindingSpec`本体はD1.1-Bでよいですが、component enumには今から追加します。

```text
POLICY_ARTIFACT
MODEL_ARCHITECTURE
OBSERVATION_SCHEMA
ACTION_SCHEMA
TENSOR_BINDING
NORMALIZATION
CONTROL_MODE
RUNTIME_CONFIG
TRAINING_PROVENANCE
TRAINING_DATASET
INITIATION_SPEC
TERMINATION_SPEC
HANDOFF_SCHEMA
```

特に`demo_dataset_hash`を必須化するなら、対応するevidence componentが必要です。NORMALIZATIONのUNKNOWNとして代用してはいけません。

### proof obligationはgrade単位だけでは不足

現在の表では、例えば`EXACT_TRAIN_TIME`に一律でnormalizer hashなどを要求しています。

しかし、

* POLICY_ARTIFACT
* HANDOFF_SCHEMA
* INITIATION_SPEC
* NORMALIZATION

では必要な証拠が異なります。

したがって、proof policyは、

```text
(component_kind, evidence_grade)
  → required ProofKind set
```

で定義してください。

```python
ProofPolicy[
    (ComponentKind.OBSERVATION_SCHEMA,
     EvidenceGrade.EXACT_TRAIN_TIME)
] = {...}
```

また、次も明示が必要です。

* 1 componentにつきEvidenceRecordは1件か
* 複数claimを許す場合、どれを採用するか
* grade順序を表す明示的rank
* `ProofItem`の型と安定した`ProofKind`
* duplicate proofの処理
* `notes`をevidence hashへ含めるか

推奨は、

```text
1 component = 1 certified claim
複数の根拠 = claim内のProofItem列
```

です。

---

## 5. runtime型に重複と責務混入がある

### `SkillOutcome.checkpoint_id`が重複

`ProducerOutcome`自体が、

* TerminalOutcome
* InterruptOutcome

のtagged unionであり、その中にcheckpoint情報があります。それとは別に`SkillOutcome.checkpoint_id`を持たせると不一致が発生します。

修正：

```python
@dataclass(frozen=True)
class SkillOutcome:
    invocation_id: str
    outcome: ProducerOutcome
    end_belief_ref: BeliefRef
    duration_s: float
    accumulated_cost: float
```

checkpointは`outcome`からのみ取得します。

### `HandoffOffer.compatibility`も重複

互換条件はすでに、

* producer側の`handoff_schema`
* consumer側の`accepted_handoff`

として静的定義されています。runtime offerに`compatibility`を再度入れると、producerが「互換」と自己申告できてしまいます。

推奨：

```python
@dataclass(frozen=True)
class HandoffOffer:
    handoff_schema_id: str
    producer_invocation_id: str
    producer_action_id: str
    producer_definition_hash: str
    control_epoch: int
    outcome: ProducerOutcome
    belief_ref: BeliefRef
    ownership: Ownership
```

互換性は、

```text
producer definition
× consumer definition
× actual offer
```

から`validate_handoff()`が判定します。

`control_epoch`をofferにも入れることで、旧スキルが生成した古いhandoffやcommandを拒否できます。

---

## 6. migrationが必須フィールドを生成できない

migration規則では、

```text
証拠なし → UNKNOWN evidence / None
```

としています。

一方、v2の`SkillDefinition`や`ExecutionBundle`には、

* `runtime_config_hash`
* `control_mode`
* `model_architecture_ref`
* `behavior_revision`
* `skill_variant_id`

など、非optionalの新規フィールドがあります。

そのため、v1に情報がない場合、

* 有効なSkillDefinitionを作るのか
* draftだけ作るのか
* migration自体を拒否するのか

が決まりません。

次の出力型を定義してください。

```python
@dataclass(frozen=True)
class MigrationResult:
    draft_definition: DraftSkillDefinition | None
    runtime_snapshot: RuntimeSnapshot | None
    evidence_bundle: EvidenceBundle
    report: MigrationReport
```

規則は次が安全です。

```text
完全に復元可能:
  SkillDefinition候補を生成

実行identityの一部がUNKNOWN:
  DraftSkillDefinitionのみ生成
  最終SkillActionIdとCertificateは発行しない

意味的に変換不能:
  E_MIGRATE_*で拒否
```

`behavior_revision`や`skill_variant_id`のmigration既定値も、DESIGNで固定する必要があります。

---

# P1：DESIGN文書で追加修正すべき事項

## Handoff compatibilityの方向を定義する

現状は「field・単位・frame・version・必須/任意属性を比較」とありますが、compatibleの意味が未確定です。

D1.1-Aでは、まず保守的に次でよいです。

```text
consumer required fields ⊆ producer fields
dtype完全一致
shape完全一致
unit完全一致
frame完全一致
schema major version一致
producer追加optional fieldは許可
暗黙の単位変換・frame変換は禁止
```

変換対応は、後で明示的なtransition adapterとして追加します。

## `ValidationReport`をissue構造にする

現在の、

```python
error_codes: tuple[str, ...]
field_paths: tuple[str, ...]
```

では、codeとpathの対応が崩れる可能性があります。

```python
@dataclass(frozen=True)
class ValidationIssue:
    code: str
    field_path: str
    message: str
```

を使い、安定順でsortしてください。

## Strict JSON decoderを設計に含める

invalid corpusには、

* duplicate key
* unknown field
* NaN/Inf
* Unicode差

がありますが、通常の`json.loads()`はduplicate keyを自動的に上書きします。

module layoutへ、

```text
codec.py
```

を追加し、

* `object_pairs_hook`によるduplicate検出
* `parse_constant`によるNaN/Inf拒否
* unknown field拒否
* enum strict decode

を担当させる必要があります。

## `Freshness`の名称を変える

static definitionに入れるのは「現在新鮮か」ではなく、許容stalenessの規則です。

```text
Freshness
→ FreshnessPolicy
```

とし、実際のstaleness評価はruntime validatorへ置く方が明確です。

---

# Test planの修正

現在の、

```text
任意の1-field破壊変異はReport.valid=False
```

は成立しません。fieldを1つ変えても、別の有効契約になる場合があるためです。

次に変更してください。

```text
各mutation operatorは、
明示的に1つの不変条件を破壊し、
期待するerror codeとfield pathを返す
```

また、stdlib `random`を使う場合は、

* seed固定
* 失敗時にseedと入力を保存
* 「property-based」ではなく「generative/metamorphic test」と表記

が適切です。

追加すべき重要試験は次です。

1. `contract_schema_version`変更
   → `SkillActionId`不変、`SkillDefinitionHash`変化

2. `behavior_revision`変更
   → 両方変化

3. runtime field変更
   → static hash不変

4. training provenanceのgrade変更
   → action ID不変、evidence/certificate hash変化

5. execution bundle変更
   → action ID変化

6. handoff start context変更
   → action ID不変

7. RFC 8785の非BMP key test vector

8. EvidenceRecord順序変更
   → EvidenceBundleHash不変

9. profile required component欠損
   → authority eligibility不成立

10. static certificateとruntime lifecycle reportが独立

---

# Open pointsの扱い

文書は次の3件を「non-blocking」としています。

* `runtime_config_hash`の正規形
* Unicode正規化
* `SchemaVersionStamp`の最小構成

しかし、少なくとも最初の2件はidentityとhashを直接左右するため、**DESIGN PASS前のblocking項目**です。

`SchemaVersionStamp`は、次のどちらかにしてください。

* 今回実装するなら最小fieldを確定
* 未確定のままなら`TransitionRecord`実装をD2へ完全にdefer

「型だけ先行実装し、内容は後で決める」は避けるべきです。

---

# 文書ヘッダーの確認事項

`created 2026-07-19 09:0x JST`が仮値のままです。また、governing scopeのsha256 `71097...`は、今回添付されたファイル群だけでは対応するbanked preregを独立確認できません。DESIGN bank前に、

* 実時刻
* canonical path
* governing scopeの完全SHA
* commit object

をreadbackしてください。

---

# 修正後の中心構造

```text
Static
  DraftSkillDefinition
    └─ UNKNOWNを許す、最終action IDなし

  SkillDefinition
    ├─ ResolvedExecutionBundle
    ├─ static lifecycle specification
    └─ SkillActionId / SkillDefinitionHash

Provenance
  TrainingProvenance
  EvidenceBundle
  EvidencePolicy

Certification
  certify_definition()
    → ValidationReport
    → valid時のみContractCertificate

Runtime
  SkillInvocation
  SkillOutcome
  HandoffOffer
  TransitionRecord

Runtime validation
  validate_invocation_start()
  validate_outcome()
  validate_handoff()
```

# 最終判断

| 項目                   | 判定       |
| -------------------- | -------- |
| Scope準拠              | PASS     |
| 基本アーキテクチャ            | PASS     |
| static/runtime型分離    | 条件付きPASS |
| identity設計           | HOLD     |
| canonical hash       | HOLD     |
| evidence設計           | HOLD     |
| runtime validation   | HOLD     |
| migration            | HOLD     |
| test plan            | 修正必要     |
| pN DESIGN PASS-CLOSE | **不可**   |

次の版では、最低限以下を直せば再判定できます。

1. static certificationとruntime lifecycle validationの分離
2. ExecutionBundleとTrainingProvenanceの分離
3. UNKNOWN／EXPLICIT_NONEの区別と最終ActionId発行条件
4. JCS実装または厳密なsubset制約
5. component×grade proof policy
6. outcome/handoff重複除去
7. migration resultとdraft contractの定義
8. identity/hashのmetamorphic test追加

[チェック対象のDESIGN文書](sandbox:/mnt/data/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md)

---

## Internal working output

**Verdict**

DESIGN HOLD. The document is materially stronger than the preregistration draft and remains within scope, but it is not implementation-ready.

**Primary blockers**

1. Static certification and runtime lifecycle validation are conflated.
2. Execution identity includes training provenance and lacks fields required by its own lineage table.
3. Unknown execution metadata is treated as actual absence and hashed into a final action identity.
4. The proposed Python serialization is not generally RFC 8785 compliant.
5. Evidence obligations are grade-wide rather than component-and-grade specific.
6. Runtime records duplicate checkpoint and compatibility semantics.
7. Migration cannot deterministically populate several required v2 fields.

**Required verification after revision**

* Identity metamorphic test matrix
* RFC 8785 or explicitly restricted canonicalization golden vectors
* Strict duplicate-key and unknown-field decoding
* Evidence-profile completeness and monotonicity tests
* Separate static and runtime validator suites
* Deterministic migration tests for unresolved execution bundles

[1]: https://www.rfc-editor.org/info/rfc8785/?utm_source=chatgpt.com "RFC 8785: JSON Canonicalization Scheme (JCS) | RFC Editor"

---

（転記終わり。転記者注: 上記「## 1.〜## 6.」が design doc §12 の P0-1..P0-6、「# P1」4 項が P1-1..P1-4、「# Test planの修正」が T、「# Open pointsの扱い」が OP、「# 文書ヘッダーの確認事項」が header 行に対応する。）
