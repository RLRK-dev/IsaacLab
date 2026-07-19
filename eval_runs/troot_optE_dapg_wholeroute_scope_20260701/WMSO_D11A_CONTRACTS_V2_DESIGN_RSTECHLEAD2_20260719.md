# WMSO D1.1-A `contracts_v2` — DESIGN (v2)

- node: `T-WMSO`; author = w2:pQ (RS-TECH-LEAD2)
- created: v1 = 2026-07-19 09:09 JST / v1.1 = 09:24 JST / v2 = 09:32 JST / **v2.1 = 09:43 JST**
- **status: DESIGN DRAFT v2.1 — pS delta confirm → CC Debate/pre-mortem → pN DESIGN PASS-CLOSE PENDING**
- governing scope: `WMSO_D11_CONTRACT_V2_SCOPE_PREREG_RSTECHLEAD2_20260719.md` v3.2.2, sha256 **`71097e58102e100657177b7ead2484bcc00840e4a788e6a295d944f7827d0966`**, commit `ea6e39b93c`（SCOPE CLOSED 3 軸; canonical path = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/` 配下）
- version 履歴: v1 (sha `8bec472a6ac1…`) → v1.1 (pS D-1..D-6+N-a fold, sha `b807ce2abbd7…`, pS delta confirm PASS 09:28 — Rs review-4 により superseded) → v2 (09:32-36, Rs review-4 P0-1..P0-6 / P1-1..P1-4 / test / open-points 全 fold, sha `4880dc0d6c6d…`; pS 一括 verify = PASS-WITH-CONDITIONS V-1..V-4, addendum sha `e88f4940f8e2…`) → **v2.1 (09:4x, pS V-1..V-4 fold: §1.2 slot 原理を identity 入力 5 個全てへ〔ControlModeSlot 新設・kind 別許容表〕/ §2-5 CanonicalDecimal regex `-0` 拒否修正 / §4.3 EvidencePolicy artifact = design chunk 内 bank + pN DESIGN verify 対象 / §6 v1 Admissibility 4 bool = 明示 discard + loud 記録)**
- 駆動要件: prereg §2 IN / §5b / N-1・N-2 / DC-1..DC-6 / pS D-1..D-6+N-a / **Rs review-4 P0・P1・T・OP**
- ⛔ 本 doc は設計のみ。code / [CHANGE] / impl は pN DESIGN PASS → pre-check → rule-check → path freeze / impl GO まで CLOSED。

---

## 0. 中心構造（Rs review-4 の確定形）

```text
Static
  DraftSkillDefinition   — UNKNOWN slot を許す / draft hash のみ / 最終 ActionId なし
  SkillDefinition        — 全 slot 解決済み / SkillActionId + SkillDefinitionHash

Provenance
  TrainingProvenance / EvidenceBundle / EvidencePolicy

Certification（静的）
  certify_definition() → ValidationReport → (valid のみ) ContractCertificate

Runtime（実行記録）
  SkillInvocation / SkillOutcome / HandoffOffer / TransitionRecord

Runtime validation（実行時 — certificate を無効化しない）
  validate_invocation_start() / validate_outcome() / validate_handoff()
```

静的 certificate と実行時 lifecycle 検査は**別系統**（P0-1）。実行時違反は当該 invocation の違反として記録され、静的 `ContractCertificate` は無効にならない。

---

## 1. Static 型（P0-2 / P0-5 fold 済み）

### 1.1 ArtifactSlot — 知識不足と実体不存在の区別（P0-2）

```python
class SlotState(Enum): KNOWN | EXPLICIT_NONE | UNKNOWN

@dataclass(frozen=True)
class ArtifactSlot:
    state: SlotState
    artifact_hash: str | None      # KNOWN ⇔ 64-hex 必須 / EXPLICIT_NONE・UNKNOWN ⇔ None (違反 = E_SLOT_INCONSISTENT)
```

- `UNKNOWN` = まだ回収・定義されていない（知識不足）。`EXPLICIT_NONE` = 実体として存在しないことが確認済み。
- kind 別規則: **LEARNED は tensor_binding / normalization に EXPLICIT_NONE を許さない**（学習 policy には必ず実在する → KNOWN か UNKNOWN のみ; 違反 = `E_SLOT_FORBIDDEN_NONE`）。SCRIPTED / WAIT は EXPLICIT_NONE が自然。

### 1.2 ExecutionBundle（実行を決める要素のみ）

```python
class ControlMode(Enum): DIFF_IK_EE_TARGET | SCRIPTED_SEQUENCE | WAIT   # strict decode; unknown = E_ENUM_UNKNOWN

@dataclass(frozen=True)
class ControlModeSlot:                  # V-3: enum 値の slot (EXPLICIT_NONE は無意味 — 制御様式は常に実在 → 禁止)
    state: SlotState                    # KNOWN | UNKNOWN のみ (EXPLICIT_NONE = E_SLOT_FORBIDDEN_NONE)
    value: ControlMode | None           # KNOWN ⇔ value 必須 (E_SLOT_INCONSISTENT)

@dataclass(frozen=True)
class ExecutionBundle:                  # V-3: slot 原理を identity 入力 5 個全てへ (str|None の混同排除)
    kind: IdentityKind                  # LEARNED | SCRIPTED | WAIT
    executable_artifact_hash: str       # 常に必須 KNOWN (これ無しは identity たり得ない — v1 も必ず保持)
    model_architecture: ArtifactSlot
    tensor_binding: ArtifactSlot
    normalization: ArtifactSlot
    control_mode: ControlModeSlot
    runtime_config: ArtifactSlot        # KNOWN 時の hash 正規形 = §2.4 (EXPLICIT_NONE 禁止 — config は常に実在)
```

- `resolved(bundle)` ⇔ 全 slot.state ≠ UNKNOWN。**「v1 → Draft」が型で書ける**（v1 に無い 3 field = UNKNOWN slot）。
- kind 別 slot 許容表（表外 = `E_SLOT_FORBIDDEN_NONE` / `E_SLOT_INCONSISTENT`）:

| slot | LEARNED | SCRIPTED | WAIT |
|---|---|---|---|
| model_architecture | KNOWN・UNKNOWN | EXPLICIT_NONE | EXPLICIT_NONE |
| tensor_binding | KNOWN・UNKNOWN | EXPLICIT_NONE | EXPLICIT_NONE |
| normalization | KNOWN・UNKNOWN | EXPLICIT_NONE | EXPLICIT_NONE |
| control_mode | KNOWN・UNKNOWN | KNOWN(SCRIPTED_SEQUENCE) | KNOWN(WAIT) |
| runtime_config | KNOWN・UNKNOWN | KNOWN・UNKNOWN | KNOWN・UNKNOWN |

- N-a: Rs DC-1 list の「action scale」は TensorBindingSpec（scale/bias、D1.1-B）に含まれ `tensor_binding` slot 経由で bundle に入る。

### 1.3 TrainingProvenance（identity 外・契約内; P0-2）

```python
@dataclass(frozen=True)
class TrainingProvenance:
    execution_family: ExecutionFamily
    training_lineage: TrainingLineage
    final_artifact_hash: str            # 検証: == ExecutionBundle.executable_artifact_hash (E_PROVENANCE_ARTIFACT_MISMATCH)
    bc_base_hash: str | None
    bc_config_hash: str | None
    demo_dataset_hash: str | None       # N-2
    demo_dataset_absent_reason: str | None   # "HISTORICAL_PRE_D11" のみ (D-2; BC 系で hash・reason 両 None = E_DEMO_HASH_MISSING)
```

来歴は実行を決めない → `SkillDefinitionHash` に入り、`ExecutionBundleHash` / `SkillActionId` に入らない（provenance records-fix が SDM 行を孤児化しない）。

### 1.4 Draft / Certified の 2 段階（P0-2）

```python
@dataclass(frozen=True)
class DraftSkillDefinition:
    # SkillDefinition と同一 field 集合。execution_bundle に UNKNOWN slot を許す。
    # 発行可: draft_definition_hash = H_WCJ(全体)。発行不可: SkillActionId / ContractCertificate。

@dataclass(frozen=True)
class SkillDefinition:
    contract_schema_version: str
    skill_namespace: str
    skill_id: str
    skill_variant_id: str               # 既定 "default"
    behavior_revision: int
    execution_bundle: ExecutionBundle   # resolved 必須 (UNKNOWN 残存 = E_BUNDLE_UNRESOLVED → Draft に留まる)
    training_provenance: TrainingProvenance
    semantic_obs_schema: tuple[SemanticFieldSpec, ...]
    semantic_action_schema: tuple[SemanticFieldSpec, ...]
    initiation_spec: InitiationSpec
    termination_spec: TerminationSpec
    checkpoint_specs: tuple[CheckpointSpec, ...]
    handoff_schema: tuple[HandoffSchemaSpec, ...]
    accepted_handoff: tuple[AcceptedHandoffSpec, ...]
    resume_capability: ResumeCapability
    resume_state_schema: str | None
    support_boundary: SupportBoundary
    freshness_policy: FreshnessPolicy   # P1-4: 改名 (許容 staleness の規則。評価は runtime §5B)
    fail_closed_action: FailClosedAction
```

### 1.5 identity / hash（P0-2）

```text
ExecutionBundleHash = H_WCJ(resolved ExecutionBundle)     # UNKNOWN を含む bundle には定義されない
SkillActionId       = H_WCJ(skill_namespace, skill_id, ExecutionBundleHash,
                            skill_variant_id, behavior_revision)
SkillDefinitionHash = H_WCJ(SkillDefinition 全体)          # provenance を含む
draft_definition_hash = H_WCJ(DraftSkillDefinition 全体)   # UNKNOWN slot は state 文字列として直列化
```

- **最終 `SkillActionId` は resolved bundle からのみ発行**（UNKNOWN を "ABSENT" として hash する v1.1 設計は撤回 — 知識不足を identity に焼き込まない）。binding が後日 KNOWN になる ⇒ その時点で初めて final ActionId が生まれる（SDM 集約は certified action でのみ行うため孤児は生じない）。
- `contract_schema_version` は serialization/migration 用 — ActionId に含めない。`behavior_revision` は振る舞い契約の改訂でのみ +1。
- `handoff_start_context` は identity から除去済み（P0-2 継承）→ TransitionRecord / provenance。

---

## 2. WMSO Canonical JSON（P0-3 — RFC 8785 準拠実装 = Rs 案 A）

`H_WCJ(x)` = sha256(WCJ(x))。WCJ = 以下を満たす canonicalizer（D1.1-A 実装、golden vectors 付き）:

1. **object key sort = UTF-16 code unit 順**（実装: `sorted(keys, key=lambda k: k.encode("utf-16-be"))` — Python 既定の code point 順 sort は使わない。非 BMP key で乖離するため）。
2. **lone surrogate 拒否**（U+D800–U+DFFF 単独出現 = raise）。**duplicate key 拒否**は codec 層（§5C）。
3. 文字列 serialization = JCS 規則（最小 escape: `\" \\ \b \f \n \r \t`、他制御文字は `\u00xx` 小文字 hex）。
4. **数値は int のみ**、`|n| ≤ 2^53 − 1`（超過 = `E_INT_RANGE` — ECMAScript 表現と同一性を保つ）。**float 型は拒否**（NaN / ±Inf 含む）。
5. **実数値は `CanonicalDecimal` 文字列**（P0-3 — 固定 6 桁化は廃止: 異なる閾値の同値化を防ぐ）:
   - 正規形 regex（V-1 修正 — 旧形は literal `-0` を許し prose と矛盾していた）: `(0|-?[1-9][0-9]*)(\.[0-9]*[1-9])?|-0\.[0-9]*[1-9]`（exponent 禁止 / trailing zero 除去 / **literal `-0` 不可**〔`-0.5` は可〕/ 先頭ゼロ禁止）。corpus に `"-0"` 拒否 case を追加（§8）。
   - binary float を経由しない（文字列のまま保持・比較）。非正規形入力は**正規化せず拒否**（`E_DECIMAL_NONCANONICAL`）。
6. **NFC は WMSO schema の事前制約**（canonicalizer は正規化しない）: 文字列値のうち identifier 類（field_id 等）は NFC 済みを要求、non-NFC は validator が拒否（`E_ID_NOT_NFC`）。
7. hash-visible な object **key は 7-bit ASCII 限定**（設計上 key = 型の field 名なので自然に成立; canonicalizer は防御的に assert）。arbitrary dict を hash 入力に許さない（型からの直列化のみ）。
8. **golden test vectors**: RFC 8785 由来 vector + 非 BMP key vector（絵文字 key vs U+FB33 key — Python 素朴 sort と結果が異なることを固定）。

### 2.4 `runtime_config_hash` の正規形（旧 open point — 昇格・確定）

runtime config = strict decode（§5C）済みの正規 object（ASCII key / int・CanonicalDecimal・NFC 文字列 / list / object のみ）を WCJ で hash。SCRIPTED の schedule は `[{op, args}, …]` の list-of-objects 正規形。WAIT は `{wait_kind, duration_s | condition_ref}`。

---

## 3. lineage 許容表（変更なし — §3.1 は v1.1 のまま有効）

許容 5 行（PPO×RL_ONLY / PPO×BC_THEN_RL / BC×BC_ONLY / SCRIPTED×N/A / WAIT×N/A）・DAPG 除外（DC-5、acceptance 後に追加）・表外 = `E_LINEAGE_FORBIDDEN`・N-1（表 = 構造規則、分類は evidence 専管）。照合対象 = `TrainingProvenance`。coherence: IdentityKind ↔ ExecutionFamily（LEARNED⇔{PPO,BC}, SCRIPTED⇔SCRIPTED, WAIT⇔WAIT; `E_KIND_FAMILY_MISMATCH`）。

---

## 4. Evidence model（P0-4 — 閉じ切り）

### 4.1 ComponentKind（13 種 — profile が要求する全てを型で表現可能に）

```python
class ComponentKind(Enum):
    POLICY_ARTIFACT | MODEL_ARCHITECTURE | OBSERVATION_SCHEMA | ACTION_SCHEMA |
    TENSOR_BINDING | NORMALIZATION | CONTROL_MODE | RUNTIME_CONFIG |
    TRAINING_PROVENANCE | TRAINING_DATASET | INITIATION_SPEC | TERMINATION_SPEC | HANDOFF_SCHEMA
```

- `TENSOR_BINDING` / `CONTROL_MODE` を**今から enum に追加**（Spec 本体は D1.1-B でも、型表現不能を解消）。
- `demo_dataset_hash` の証拠は **TRAINING_DATASET** component（NORMALIZATION の UNKNOWN で代用禁止）。

### 4.2 EvidenceRecord / EvidenceBundle

```python
class EvidenceGrade(Enum):   # 明示 rank (P0-4)
    EXACT_TRAIN_TIME = 4 | HASH_BOUND_REPRODUCED = 3 | RECONSTRUCTED_COMPATIBLE = 2 |
    DIMENSION_ONLY = 1 | UNKNOWN = 0

class ProofKind(Enum):       # 安定 id (P0-4)
    TRAIN_RUN_MANIFEST | SOURCE_COMMIT | CONFIG_HASH | INPUT_SCHEMA_HASH | OUTPUT_SCHEMA_HASH |
    NORMALIZER_HASH | FINAL_ARTIFACT_HASH | TRAIN_TIME_CRYPTO_BINDING |
    REPRODUCTION_PROCEDURE | REPRODUCED_OUTPUT_HASH | RECONSTRUCTION_SOURCES |
    COMPATIBILITY_TEST | UNRESOLVED_DIFFERENCES | DIMENSION_SOURCE | EVALUATOR_ARTIFACT

@dataclass(frozen=True)
class ProofItem:
    kind: ProofKind
    ref: str
    artifact_hash: str | None

@dataclass(frozen=True)
class EvidenceRecord:        # 1 component = 1 certified claim (重複 = E_EVIDENCE_DUPLICATE)
    component_kind: ComponentKind
    grade: EvidenceGrade
    source_ref: str
    artifact_hash: str | None
    evaluator_artifact_hash: str
    proof: tuple[ProofItem, ...]        # 複数根拠 = claim 内の ProofItem 列
    notes: str                          # ⛔ evidence_bundle_hash の計算から除外 (自由文で hash を不安定化しない)
```

`evidence_bundle_hash` = H_WCJ(component_kind 順に sort した records の hash-visible 部分〔notes 除外〕)。record 順序に不変（metamorphic test #8）。

### 4.3 ProofPolicy（P0-4 — **(component × grade) → required ProofKind set**）

grade 一律ではなく component ごとに定義する。代表行（全表は EvidencePolicy artifact として bank され `evidence_policy_hash` で certificate に結合）:

| component | grade | required ProofKind |
|---|---|---|
| POLICY_ARTIFACT | EXACT_TRAIN_TIME | TRAIN_RUN_MANIFEST + SOURCE_COMMIT + CONFIG_HASH + FINAL_ARTIFACT_HASH + TRAIN_TIME_CRYPTO_BINDING |
| POLICY_ARTIFACT | HASH_BOUND_REPRODUCED | CONFIG_HASH + FINAL_ARTIFACT_HASH + REPRODUCTION_PROCEDURE + REPRODUCED_OUTPUT_HASH + EVALUATOR_ARTIFACT |
| OBSERVATION_SCHEMA | EXACT_TRAIN_TIME | TRAIN_RUN_MANIFEST + INPUT_SCHEMA_HASH + SOURCE_COMMIT |
| OBSERVATION_SCHEMA | RECONSTRUCTED_COMPATIBLE | RECONSTRUCTION_SOURCES + COMPATIBILITY_TEST + UNRESOLVED_DIFFERENCES + EVALUATOR_ARTIFACT |
| NORMALIZATION | EXACT_TRAIN_TIME | TRAIN_RUN_MANIFEST + NORMALIZER_HASH |
| TRAINING_DATASET | HASH_BOUND_REPRODUCED | FINAL_ARTIFACT_HASH(=dataset) + REPRODUCTION_PROCEDURE + EVALUATOR_ARTIFACT |
| 任意 | DIMENSION_ONLY | DIMENSION_SOURCE（+ semantic unresolved 宣言） |
| 任意 | UNKNOWN | （無条件 — authority-relevant claim 不可） |

- 不足 = `E_PROOF_INSUFFICIENT`（1 段下の grade で再提出可 — 単調）。
- duplicate proof（同 kind 同 ref）= 冪等に単一扱い（bundle hash に 1 回のみ寄与）。
- **EvidencePolicy artifact の bank 時期（V-2）**: 全表（13 component × grades の ProofPolicy + 3 profile の required-set / min_grade 詳細〔SHADOW / OFFLINE_REPLAY の required-set 含む〕）は **本 design chunk 内・impl GO 前に** `EvidencePolicy v1` artifact として bank し、**pN DESIGN verify の対象に含める** — impl が policy を発明しない。

### 4.4 usage profiles（v1.1 §4.4 を維持 + component 拡張反映）

- required set: CLOSED_LOOP = {POLICY_ARTIFACT, MODEL_ARCHITECTURE, OBSERVATION_SCHEMA, ACTION_SCHEMA, TENSOR_BINDING, NORMALIZATION, CONTROL_MODE, RUNTIME_CONFIG, INITIATION_SPEC, TERMINATION_SPEC, HANDOFF_SCHEMA}（+ BC 系 lineage では TRAINING_DATASET）。SHADOW / OFFLINE_REPLAY は同集合から TENSOR_BINDING・CONTROL_MODE を除いた集合以上（詳細表 = EvidencePolicy artifact）。
- min_grade（D-3 確定値のまま）: CLOSED_LOOP ≥ HASH_BOUND_REPRODUCED / SHADOW ≥ RECONSTRUCTED_COMPATIBLE / OFFLINE_REPLAY ≥ RECONSTRUCTED_COMPATIBLE（DIMENSION_ONLY = 診断のみ / UNKNOWN 不可）。
- 集約 = required set の最弱 grade。matrix = ceiling（authority grant ではない; two-key + 独立安全 gate conjoin）。「条件付き」cell 定義は v1.1 から不変。

---

## 5. Validation（P0-1 — 4 系統分離 / P1）

### 5A. 静的 certification

```python
certify_definition(definition: SkillDefinition | DraftSkillDefinition,
                   evidence_bundle: EvidenceBundle,
                   evidence_policy: EvidencePolicy,
                   schema_registry: SchemaRegistry) -> DefinitionCertificationResult
```

- 検査 = 値単体（isfinite 全域・非空・NFC・hash 形式 — v1.1 §5.1 全項目）/ identity 整合（§3 表・coherence・E_DEMO_HASH_MISSING・**E_PROVENANCE_ARTIFACT_MISMATCH**）/ 静的 lifecycle 仕様の内部整合（checkpoint・handoff id 重複禁止 / RESUME_WITH_STATE ⇔ resume_state_schema / accepted_handoff の**静的** compatibility〔§5D 規則を registry の producer 定義に対して〕）/ evidence（ProofPolicy 照合・profile 集約）。
- **Draft 入力**: 検査は走るが certificate は発行されない（`E_BUNDLE_UNRESOLVED` を issue に含む report のみ）。
- 出力:

```python
@dataclass(frozen=True)
class ValidationIssue:      # P1-2: code と path の対応を構造で保証
    code: str               # E_* 安定 code
    field_path: str
    message: str

@dataclass(frozen=True)
class ValidationReport:     # 常に生成; issues は (code, field_path) 安定順 sort
    valid: bool
    issues: tuple[ValidationIssue, ...]
    validator_artifact_hash: str

@dataclass(frozen=True)
class ContractCertificate:  # valid の場合のみ発行 (不適合に certificate は存在しない)
    skill_definition_hash: str
    skill_action_id: str
    evidence_bundle_hash: str
    evidence_policy_hash: str
    validator_artifact_hash: str
    contract_schema_version: str
    issued_at: float        # certificate 同一性判定に含めない
```

### 5B. 実行時 lifecycle validation（certificate を無効化しない — invocation 側の違反記録）

```python
validate_invocation_start(invocation, definition, belief) -> LifecycleValidationReport
    # initiation predicate 充足 / belief 鮮度 (freshness_policy 評価) / control ownership
validate_outcome(invocation, outcome, definition) -> LifecycleValidationReport
    # outcome.terminal_class ∈ termination_spec / interrupt checkpoint ∈ checkpoint_specs /
    # duration・cost 有限・非負 / invocation_id 一致
validate_handoff(invocation, offer, producer_definition, consumer_definition) -> HandoffValidationReport
    # offer.handoff_schema_id ∈ producer_definition.handoff_schema /
    # producer_invocation_id == invocation.invocation_id / control_epoch 単調 /
    # §5D 互換規則 (producer_def × consumer_def × offer)
```

### 5C. codec（P1-3 — strict JSON decoder; module `codec.py`）

- `object_pairs_hook` で **duplicate key 検出拒否** / `parse_constant` で **NaN・±Inf 拒否** / unknown field 拒否 / enum strict decode（unknown = `E_ENUM_UNKNOWN`）/ lone surrogate 拒否。通常の `json.loads` を hash 入力経路で使わない。

### 5D. handoff compatibility 規則（P1-1 — D1.1-A の保守形）

```text
consumer required fields ⊆ producer fields
dtype 完全一致 / shape 完全一致 / unit 完全一致 / frame 完全一致
schema major version 一致
producer 追加 optional field は許可
暗黙の単位変換・frame 変換は禁止 (変換は後続の明示的 transition adapter)
```

---

## 6. Migration v1→v2（P0-6）

```python
@dataclass(frozen=True)
class MigrationResult:
    draft_definition: DraftSkillDefinition | None
    runtime_snapshot: RuntimeSnapshot | None
    evidence_bundle: EvidenceBundle
    report: MigrationReport      # issues = ValidationIssue 構造
```

規則:
```text
完全に復元可能            → SkillDefinition 候補（resolved bundle）を生成
実行 identity の一部 UNKNOWN → DraftSkillDefinition のみ（最終 SkillActionId・Certificate 発行しない）
意味的に変換不能           → E_MIGRATE_* で拒否
証拠がない field           → 推測で埋めず UNKNOWN slot / UNKNOWN evidence
```

- **v1 は `runtime_config` / `control_mode` / `model_architecture` を持たない** → 対応 slot = **UNKNOWN**（§1.2 の slot 化により型で表現可能 — V-3）⇒ **v1 からの migration の主出力は Draft**（learned/scripted とも）。これが正直な帰結であり、certified 昇格は evidence 過程（回収作業）を経てのみ起こる。
- **v1 `Admissibility` 4 bool（identity_pinned / contract_conformant / offline_orchestration_admissible / closed_loop_admissible）の処遇 = 明示 discard（V-4）**: v2 では conformance = certificate の有無、authority = usage profile + two-key で**再導出**するため、入力 bool を運ばない（運ぶと廃止した自己申告 pattern が復活する）。discard は MigrationReport に **loud に記録**（silent drop にしない）。
- 既定値（DESIGN で固定）: `behavior_revision = 1` / `skill_variant_id = "default"` / `contract_schema_version = "2.0.0"`。
- v1 `policy_family` 文字列 → (ExecutionFamily, TrainingLineage) 全域写像（v1.1 D-6 表のまま有効; `"BC+RL"`→(PPO, BC_THEN_RL) 等、他 = `E_MIGRATE_FAMILY_UNKNOWN`）。
- v1 `FieldSemantics.RESOLVED` の実績根拠なし → RECONSTRUCTED_COMPATIBLE 以下で再記録（昇格しない）。
- **v1 の処遇**: v1/v2 を二つの SoT として共存させない。`wmso/d1` は DeprecationWarning + docs（同 release remove 禁止）。shim は v2 へ変換・委譲のみ（独自 state/validation なし）。v1 IMPL PASS を v2 の証拠に引用しない（R2）。

---

## 7. Runtime 型（P0-5 — 重複除去）

```python
@dataclass(frozen=True)
class SkillOutcome:
    invocation_id: str
    outcome: ProducerOutcome     # TERMINAL | INTERRUPT union — checkpoint は outcome からのみ取得
    end_belief_ref: BeliefRef
    duration_s: float
    accumulated_cost: float
    # (checkpoint_id field は持たない — union との不一致を型で根絶)

@dataclass(frozen=True)
class HandoffOffer:
    handoff_schema_id: str           # producer definition の宣言 schema を指す
    producer_invocation_id: str
    producer_action_id: str
    producer_definition_hash: str
    control_epoch: int               # 旧 skill の stale offer/command 拒否 (validate_handoff が単調性検査)
    outcome: ProducerOutcome
    belief_ref: BeliefRef
    ownership: Ownership
    # (compatibility field は持たない — 互換は producer_def × consumer_def × offer から validate_handoff が判定。
    #  producer の「互換」自己申告を型から排除)

@dataclass
class SkillInvocation:   # v1.1 のまま (invocation_id / skill_action_id / skill_definition_hash /
                         #  start_belief_ref / start_time / current_phase / elapsed_s / control_epoch)

@dataclass(frozen=True)
class TransitionRecord:  # v1.1 の field 集合 + stamp 最小構成の確定 (旧 open point 昇格):
    ...
    schema_versions: SchemaVersionStamp

@dataclass(frozen=True)
class SchemaVersionStamp:            # 最小構成 — 確定 (「型だけ先行」を避ける)
    contract_schema_version: str
    belief_schema_version: str
    evidence_policy_hash: str
    recorder_artifact_hash: str
```

---

## 8. Test plan（Rs T — 全面改訂）

- **standalone / monorepo 分離**は v1.1 のまま（fixture registry 含む）。
- **mutation test（旧「任意 1-field 破壊」を撤回）**: 各 **mutation operator は明示的に 1 つの不変条件を破壊**し、**期待 error code + field path** を宣言して検証する（valid→valid の変異は operator にしない）。
- **generative / metamorphic test**（「property-based」表記は撤回; stdlib `random`・**seed 固定**・失敗時に seed + 入力を artifact 保存）:

| # | metamorphic 変換 | 期待 |
|---|---|---|
| 1 | `contract_schema_version` 変更 | SkillActionId 不変・SkillDefinitionHash 変化 |
| 2 | `behavior_revision` 変更 | 両方変化 |
| 3 | runtime field（invocation/outcome）変更 | static hash 全不変 |
| 4 | TrainingProvenance の grade/records 変更 | ActionId 不変・evidence/certificate hash 変化 |
| 5 | ExecutionBundle 変更 | ActionId 変化 |
| 6 | handoff start context 変更 | ActionId 不変 |
| 7 | RFC 8785 非 BMP key vector（絵文字 vs U+FB33） | WCJ 出力が RFC 期待順（素朴 sort と不一致であること自体を固定） |
| 8 | EvidenceRecord 順序 shuffle | EvidenceBundleHash 不変 |
| 9 | profile required component を 1 つ欠損 | authority eligibility 不成立 |
| 10 | 静的 certificate 発行後に runtime lifecycle 違反 | certificate 有効のまま・LifecycleReport のみ違反 |

- invalid corpus: v1.1 の全項目（DC-4 込み）+ `E_DECIMAL_NONCANONICAL`（**literal `"-0"` 拒否 case 含む** — V-1）/ lone surrogate / duplicate key（codec 層）/ non-NFC field_id / int > 2^53−1 / slot state⇔value 不整合（`E_SLOT_INCONSISTENT`）/ kind 別 slot 許容表外（`E_SLOT_FORBIDDEN_NONE`）。
- migration 5 tests（決定的 / 同一入力同一 hash / v2→v2 no-op / 不完全 v1 fail-closed / UNKNOWN 非昇格）+ **「v1 全 skill → Draft」帰結の明示 test**。
- cross-process hash stability（subprocess 起動で完全一致）+ **WCJ golden vectors**。

## 9. Module layout（impl GO 時に確定）

```text
thread_isaac_lab/wmso/contracts_v2/
    __init__.py  types.py  identity.py  evidence.py
    certify.py  (5A)  lifecycle.py  (5B)  codec.py  (5C)
    canonical.py  (WCJ §2)  migrate.py  tests/  (fixtures/ 含む)
```

## 10. Open points — **なし**（旧 3 件は全て確定: runtime_config 正規形 = §2.4 / Unicode 規則 = §2-6・§2-7 / SchemaVersionStamp = §7 最小構成確定）

## 11. 先行 verify との整合
- pS D-1..D-6 + N-a（v1.1 fold）は本 v2 系で**全て保存**（D-1 = §1.3 で深化 / D-2 = §1.3 / D-3 = §4.4 / D-4 = §5A registry / D-5 = §2-7〔案 A 移行に伴い「ASCII 制限で等価」から「UTF-16 sort 実装 + 防御的 ASCII assert」へ強化〕/ D-6 = §6 / N-a = §1.2）。
- pS v1.1 delta confirm（09:28 PASS）は Rs review-4 により superseded — pS v2 一括 verify（09:39）= PASS-WITH-CONDITIONS。
- **pS V-1..V-4（v2 一括 verify 条件）→ 本 v2.1 で fold**: V-1 = §2-5（regex `-0` 拒否）/ V-2 = §4.3（EvidencePolicy bank 時期 = design chunk 内・pN DESIGN verify 対象）/ V-3 = §1.2（slot 原理を 5 入力全てへ; ControlModeSlot・kind 別許容表; 「v1→Draft」が型で書ける）/ V-4 = §6（Admissibility 4 bool 明示 discard + loud 記録）。

## 12. Rs review-4 → v2 fold-map（完全性照合用・§0b 方式; Rs 見出しは verbatim）

| Rs # | Rs 見出し (verbatim) | fold 先 |
|---|---|---|
| P0-1 | 静的契約validatorと実行時validatorを分離する | §0 / §5A / §5B / metamorphic #10 |
| P0-2 | Execution identityとtraining provenanceを分離する | §1.1–§1.5（ArtifactSlot 3 値 / final_artifact_hash 一致検証 / Draft・Certified / UNKNOWN 中は final ActionId 不可） |
| P0-3 | JCS minimalの主張を修正する | §2（案 A: UTF-16 code unit sort・lone surrogate/duplicate 拒否・golden vectors / CanonicalDecimal〔固定 6 桁廃止〕/ NFC = schema 事前制約） |
| P0-4 | Evidence modelを閉じ切る | §4（ComponentKind 13 種・TRAINING_DATASET・(component×grade) ProofPolicy・1 claim/component・grade rank・ProofKind・duplicate proof・notes hash 除外） |
| P0-5 | runtime型に重複と責務混入がある | §7（SkillOutcome.checkpoint_id 削除 / HandoffOffer.compatibility 削除 + control_epoch 追加） |
| P0-6 | migrationが必須フィールドを生成できない | §6（MigrationResult / Draft 生成規則 / 既定値固定） |
| P1-1 | Handoff compatibilityの方向を定義する | §5D |
| P1-2 | `ValidationReport`をissue構造にする | §5A（ValidationIssue + 安定 sort） |
| P1-3 | Strict JSON decoderを設計に含める | §5C / §9（`codec.py`） |
| P1-4 | `Freshness`の名称を変える | §1.4（FreshnessPolicy）/ §5B（評価は runtime） |
| T | Test planの修正 | §8（mutation operator 方式 / generative・metamorphic 表記 / seed 固定・保存 / metamorphic 10 試験） |
| OP | Open pointsの扱い | §2.4（runtime_config 正規形）/ §2-6・7（Unicode）/ §7（SchemaVersionStamp 最小構成確定）/ §10（残 0） |
| header | 文書ヘッダーの確認事項 | 冒頭（実時刻 / governing scope 完全 SHA / canonical path / commit `ea6e39b93c`） |
