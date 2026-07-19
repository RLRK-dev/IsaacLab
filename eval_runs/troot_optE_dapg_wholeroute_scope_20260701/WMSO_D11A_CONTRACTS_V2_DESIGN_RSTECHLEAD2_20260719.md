# WMSO D1.1-A `contracts_v2` — DESIGN (v2.3)

- node: `T-WMSO`; author = w2:pQ (RS-TECH-LEAD2)
- created: v1 = 2026-07-19 09:09 JST / v1.1 = 09:24 / v2 = 09:32 / v2.1 = 09:43 / v2.2 = 10:59（editing 完了実測; 旧「10:5x」表記を確定 — 以後 x-mask 廃止）/ **v2.3 = 12:07 JST（実測）**
- **status: DESIGN DRAFT v2.3 — cycle-2 fold（debate = REVIEW で終結・残 fix は本版; §11）→ pS delta re-check → pN DESIGN PASS-CLOSE（最終 SHA 宛）PENDING**
- governing scope: `WMSO_D11_CONTRACT_V2_SCOPE_PREREG_RSTECHLEAD2_20260719.md` v3.2.2, sha256 `71097e58102e100657177b7ead2484bcc00840e4a788e6a295d944f7827d0966`, commit `ea6e39b93c`
- 兄弟 normative artifacts（pN DESIGN verify の対象; full 64-hex — B-CH5）:
  - **Rs review-4 transcript** = `WMSO_RS_REVIEW4_DESIGN_TRANSCRIPT_20260719.md`, sha256 `8a7915dfa3386889d4efe3cbacb063c0ea20df0f138c8099b84ec64cbab5ad50`（as-received 転記、**Rs 確認 PENDING**）
  - **Rs PLAN_STATUS review v2（W 系）** = `WMSO_RS_PLAN_STATUS_REVIEW_V2_COPY_20260719.md`, sha256 `dc57d8e10c5ba84d…`（bank `320545b477` の committed 値; **byte-identical file copy — 転記でないため fidelity 確認不要**）
  - **EvidencePolicy v1.1** = `WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md`, sha256 `9e4c5019bb1bc6ac9f418304caaf2e56752864f0bcc3db7260ccdc8154ae7a27`
  - pS design-verify record = `WMSO_D11A_DESIGN_VERIFY_WMSODESIGN_20260719.md`（banked `cd5482310d`; 現行版は pS 管理 — B-CH1 の host pin）
- version 履歴: v1 (prefix `8bec472a6ac1` — content 非保全) → v1.1 (prefix `b807ce2abbd7` — 同) → v2 (prefix `4880dc0d6c6d` — 同) → v2.1 (full `c49ff132ff200257085f072c875c58e3200754ac74ee28de8634b786ab2681e7`, bank `cd5482310d`) → v2.2 (full `3a1577f89dfa3d3c7fa642c938f56a4ff05ab60e14b57194cb3368f7ddcb95f3`, bank `ac5865b66d`) → **v2.3 (本版)**。以後毎版 bank。
- 駆動要件（host 付き — B-CH1/A-CH5 修正）: prereg §2 IN / prereg §10 (a)-(d)〔旧ラベル §5b〕/ N-1・N-2（= **pS ratify doc §8 ADDENDUM C1** の carried 2 点）/ DC-1..DC-6（**prereg §10b**）/ review-4 P0・P1・T・OP（transcript）/ **W-P0-1..4・W-P1-1..6（W-review copy — supervening Rs review）**/ pS D・V 系 / CC Debate cycle-1 U1-U19 + cycle-2 findings（verification-log task-WMSO-D11A-design-debate-001 cycle 1・2; **cycle-1 の記録上 overall = "REVIEW"** — accepted CRITICAL を skill 表で FAIL 扱いした運用注記 = D-CH7）。「review-1 P0-n」（v1 コード欠陥）と「review-4 P0-n」（設計修正）は別番号系 — 常に接頭辞付き。
- **SSOT supersession register（enumerated-only — B-CH6/NHA）**: 本 design が prereg 文言を supersede するのは**以下に列挙した点のみ**。未記録の分岐 = 欠陥であり precedence では解決しない（prereg §9 loop へ）。① DC-2 timing（TENSOR_BINDING/CONTROL_MODE enum 即時追加 — review-4 P0-4; transcript 典拠, Rs 確認 PENDING）② prereg §5 表 7→5 行（DC-5 実行）③ prereg §7b「SkillDefinitionHash」→ draft_definition_hash 読み（§6-8）④ **prereg §4 の uniform 最弱-bind→matrix 読み → per-component min_grade 意味論（EvidencePolicy §4; C-CH1/B-CH2）**⑤ **DC-6 の bounded 例外 = §6-4 の retained-in-v1 guard（D1.1-C 後継まで; D-CH2）**。EvidencePolicy の表実体は §4 の規則どおり artifact 側が normative。
- **参照規約**: 本 doc 内の「v2.2 のまま」「v2.2 §N のまま」は全て **banked commit `ac5865b66d` の blob**（sha `3a1577f89dfa…`）を指す committed pointer である（U2 で sanctioned の形式 — 消滅版参照ではない。`git show ac5865b66d:<path>` で常時復元可能）。
- ⛔ 本 doc は設計のみ。code / [CHANGE] / impl は pN DESIGN PASS → pre-check → rule-check → path freeze / impl GO まで CLOSED。

---

## 0. 中心構造（review-4 + W-P0-2 の確定形）

```text
Static:        DraftSkillDefinition（UNKNOWN 可・final ActionId なし）/ SkillDefinition
Provenance:    TrainingProvenance / EvidenceBundle / EvidencePolicy（兄弟 artifact）
Certification: certify_definition() → ValidationReport → (valid のみ) ContractCertificate   … profile 中立（W-P0-2）
Eligibility:   evaluate_usage_eligibility() → UsageEligibilityReport                       … profile 別（W-P0-2）
Runtime:       SkillInvocation / SkillOutcome / HandoffOffer / TransitionRecord
Runtime val.:  validate_invocation_start(now) / validate_outcome() / validate_handoff()     … certificate を無効化しない
```

---

## 1. Static 型

### 1.1 Slot（W-P1-2 反映）

```python
class SlotState(Enum): KNOWN | EXPLICIT_NONE | UNKNOWN
@dataclass(frozen=True)
class ArtifactSlot:      state: SlotState; artifact_hash: str | None   # KNOWN ⇔ 64-hex (E_SLOT_INCONSISTENT)
@dataclass(frozen=True)
class ControlModeSlot:   state: SlotState; value: ControlMode | None   # KNOWN|UNKNOWN のみ (E_SLOT_FORBIDDEN_NONE)
```

### 1.2 ExecutionBundle

```python
class ControlMode(Enum): DIFF_IK_EE_TARGET | SCRIPTED_SEQUENCE | WAIT
@dataclass(frozen=True)
class ExecutionBundle:
    kind: IdentityKind
    executable_artifact_hash: str       # 常に必須 KNOWN。LEARNED = weights sha256 / SCRIPTED,WAIT = closure aggregate (§3-2)
    model_architecture: ArtifactSlot
    tensor_binding: ArtifactSlot
    normalization: ArtifactSlot
    control_mode: ControlModeSlot
    runtime_config: ArtifactSlot        # 正規形 §2.4; EXPLICIT_NONE 禁止
```

- `resolved(bundle)` ⇔ 全 slot.state ≠ UNKNOWN。
- **kind 別許容表（Draft / SkillDefinition 両方に適用; 表外 = E_SLOT_FORBIDDEN_NONE / E_SLOT_INCONSISTENT / E_KIND_CONTROL_MISMATCH）**:

| slot | LEARNED | SCRIPTED | WAIT |
|---|---|---|---|
| model_architecture | KNOWN・UNKNOWN | EXPLICIT_NONE | EXPLICIT_NONE |
| tensor_binding | KNOWN・UNKNOWN | EXPLICIT_NONE | EXPLICIT_NONE |
| normalization | KNOWN・UNKNOWN・**EXPLICIT_NONE†** | EXPLICIT_NONE | EXPLICIT_NONE |
| control_mode | KNOWN(値 ∈ {DIFF_IK_EE_TARGET})・UNKNOWN | KNOWN(SCRIPTED_SEQUENCE) | KNOWN(WAIT) |
| runtime_config | KNOWN・UNKNOWN | KNOWN・UNKNOWN | KNOWN・UNKNOWN |

- **† W-P1-2（経験的仮定を型不変量にしない）**: LEARNED の normalization = EXPLICIT_NONE は、**NORMALIZATION component の evidence（grade ≥ RECONSTRUCTED_COMPATIBLE）が「前処理未適用」を証明する場合のみ**合法（evidence-gated; certify_definition が照合、無証拠の EXPLICIT_NONE = `E_SLOT_NONE_UNPROVEN`）。tensor_binding / model_architecture は学習 policy に構造上必ず存在するため従来どおり EXPLICIT_NONE 禁止。
- N-a: 「action scale」⊂ TensorBindingSpec（D1.1-B）。

### 1.3 TrainingProvenance（learned-conditional; v2.2 から不変）

```python
@dataclass(frozen=True)
class TrainingProvenance:
    execution_family: ExecutionFamily
    training_lineage: TrainingLineage
    final_artifact_hash: str | None     # learned lineage = 必須・== executable (E_PROVENANCE_ARTIFACT_MISMATCH) / NOT_APPLICABLE = null 必須
    bc_base_hash: str | None
    bc_config_hash: str | None
    demo_dataset_hash: str | None
    demo_dataset_absent_reason: str | None   # "HISTORICAL_PRE_D11" のみ
```

### 1.4 SkillDefinition / DraftSkillDefinition

```python
@dataclass(frozen=True)
class SkillDefinition:
    contract_schema_version: str; skill_namespace: str; skill_id: str
    skill_variant_id: str; behavior_revision: int
    execution_bundle: ExecutionBundle           # resolved 必須 (E_BUNDLE_UNRESOLVED → Draft)
    training_provenance: TrainingProvenance
    semantic_obs_schema: tuple[SemanticFieldSpec, ...]
    semantic_action_schema: tuple[SemanticFieldSpec, ...]
    initiation_spec: InitiationSpec
    termination_spec: TerminationSpec
    checkpoint_specs: tuple[CheckpointSpec, ...]
    handoff_schema: tuple[HandoffSchemaSpec, ...]
    accepted_handoff: tuple[AcceptedHandoffSpec, ...]
    resume_capability: ResumeCapability
    resume_state_schema: str | None             # definition 級 default。CheckpointSpec 側は per-checkpoint override (A-CH8)
    required_control_resources: ControlResourceSpec
    scripted_callable_ref: str | None           # SCRIPTED/WAIT ⇔ 非 null (E_CALLABLE_REF_KIND_MISMATCH — D-CH9)。記録用・ActionId 対象外
    support_boundary: SupportBoundary
    freshness_policy: FreshnessPolicy
    fail_closed_action: FailClosedAction
    # recovery_rollback_target は v2.3 で削除 — §6-3 の loud-discard へ（NHA: 消費者不在 field を validator 盲点付きで carry しない。recovery 層 chunk で schema bump 再導入）
```

構成型（「≡ v1」= committed `57ed32b27a` の同名型と **field 同一（改名 or 宣言された dtype 変更のみ — A-CH8）**）: SemanticFieldSpec ≡ FieldSpec + 全数値検証 / InitiationSpec ≡ InitiationPredicate / TerminationSpec = {declared_classes（非空 frozenset）, predicate_schema_ref, predicate_schema_hash} / CheckpointSpec = {checkpoint_id, resume_state_schema | None} / HandoffSchemaSpec = {handoff_schema_id, schema_version（**形式 "MAJOR.MINOR"、major = 最初の int** — A-CH8）, fields, required_field_ids} / AcceptedHandoffSpec = {producer_skill_id, handoff_schema_id, schema_major_version} / ResumeCapability(3値) / SupportBoundary ≡ v1 / FreshnessPolicy ≡ Freshness（max_staleness_s: CanonicalDecimal | None — dtype 変更宣言） / Ownership ≡ v1（**control dict の key 語彙 = §6-3 で pin**） / ControlResourceSpec = {ee_left, ee_right, gripper_left, gripper_right: bool} / BeliefRef 系・ProducerOutcome・enums ≡ v1 / ExecutionFamily = {PPO, DAPG, BC, SCRIPTED, WAIT} / TrainingLineage = {RL_ONLY, BC_ONLY, BC_THEN_RL, NOT_APPLICABLE} / SchemaRegistry = {definitions_by_id}（standalone test = fixture registry） / MigrationReport = {issues: tuple[ValidationIssue, ...], discards: tuple[str, ...]}。
DraftSkillDefinition = 同 field 集合・bundle に UNKNOWN 可・draft_definition_hash のみ発行。

### 1.5 identity / hash（v2.2 から不変 + C-CH9 文言修正）

```text
ExecutionBundleHash   = H_WCJ(resolved ExecutionBundle)
SkillActionId         = H_WCJ({"ns", "skill", "bundle", "variant", "brev"})   # keyed object
SkillDefinitionHash   = H_WCJ(SkillDefinition 全体)
draft_definition_hash = H_WCJ(DraftSkillDefinition 全体)   # UNKNOWN slot は state object として直列化
```
最終 ActionId は resolved bundle のみ。v1 HandoffStartContext 値: state_id → previous_handoff_class（**語彙 = producer の handoff_schema_id; None → None** — D-CH6）/ initiation_context_hash → loud-discard。

---

## 2. WMSO Canonical JSON（WCJ）

1. object key sort = UTF-16 code unit 順（`k.encode("utf-16-be")` bytes 昇順）。2. lone surrogate / duplicate key 拒否。3. JCS 文字列 escape。4. int のみ・|n| ≤ 2^53−1・float 型拒否。
5. CanonicalDecimal（`re.fullmatch`; `\A(?:(0|-?[1-9][0-9]*)(\.[0-9]*[1-9])?|-0\.[0-9]*[1-9])\Z`）。順序/範囲比較 = `decimal.Decimal` exact。
6. NFC = schema 事前制約（identifier; `E_ID_NOT_NFC`）。
7. 層: (a) key-sort comparator / raw-WCJ（full-Unicode key; golden vectors の対象）/ (b) typed 入口 `canonicalize()`（ASCII-key assert）。
8. golden vectors: RFC 8785 + 非 BMP key + composite bundle vector + **≥2 要素 frozenset vector（C-CH2）**。

### 2.3 composite 直列化 pin（C-CH2/C-CH5 追補）
- 全 hash 入力 = keyed object。slot は全状態で `{"state": …, "artifact_hash"|"value": …}` object。
- **enum encode: 全 hash-visible enum の `.value` = member 名と同一の ASCII 文字列**（C-CH5。**EvidenceGrade の rank int は `.rank` 属性へ移し `.value` は名前**）。strict decode は §5C。
- evidence record 順 = `component_kind.value` bytes 昇順。**ProofItem 順 = EvidencePolicy §3b**（W-P1-3）。
- **set 型 field（`declared_classes`・`required_field_ids` 等 frozenset）は member の `.value`/文字列 bytes 昇順の JSON array として直列化**（C-CH2 — 挿入順・process 依存を排除）。

### 2.4 runtime_config 正規形（v2.2 から不変）
strict decode 済み正規 object の WCJ hash。SCRIPTED schedule = `[{op, args}, …]`。WAIT = `{wait_kind, duration_s | condition_ref}`。

---

## 3. lineage 許容表（v2.2 から 1 点明示化）

表 5 行（PPO×RL_ONLY / PPO×BC_THEN_RL / BC×BC_ONLY / SCRIPTED×N/A / WAIT×N/A; 必須 hash / null 必須 / source-closure 列付き）は v2.2 §3 のまま。ただし **BC×BC_ONLY 行の null 列を明示**（C-CH10/A-CH7）: `bc_base_hash = null / bc_config_hash = null`（BC 単独訓練に RL stage も base 概念も無い。v1 "BC" migration で config hash が現れた場合は `E_MIGRATE_BC_CONFIG_UNEXPECTED` として fail-close — 推測写像しない）。§3-2 source-closure・coherence・N-1・demo 執行 = v2.2 のまま。

---

## 4. Evidence model

- ComponentKind 13 / EvidenceGrade（`.rank` 4..0, `.value` = 名前）/ ProofKind 15 / EvidenceRecord（notes は hash 対象外）。
- **全表 = EvidencePolicy v1.1**（sha 冒頭; **3 cell exact 化・DC-3 準拠復元・ProofItem 順序/conflict・EXPLICIT_NONE 免除・per-component 意味論** を含む）。
- CLOSED_LOOP required に TRAINING_PROVENANCE ≥2（U12/W-P1-4）。missing = UNKNOWN(0)。
- ceiling / two-key conjoin / 「条件付き」cell 定義 = 従来どおり。

---

## 5. Validation（W-P0-2/3・W-P1-6 反映）

### 5A. 静的 certification（**profile 中立** — W-P0-2）

`certify_definition(definition, evidence_bundle, evidence_policy, schema_registry) → DefinitionCertificationResult`

- 検査 = 値単体（v2.2 §5A 全項目 + **E_SKILL_UNREGISTERED**〔skill_id ∉ SKILL_ID_REGISTRY — B-CH7〕+ **E_SLOT_NONE_UNPROVEN**〔§1.2†〕+ **E_CALLABLE_REF_KIND_MISMATCH**）/ identity 整合 / 静的 lifecycle 内部整合 / **evidence = 「present な claim の well-formedness と ProofPolicy 適合」のみ**（**profile 充足は検査しない** — 第 3 解釈の明文化）。
- 出力 = ValidationReport（issues 安定順 = **(code, field_path, message)** — C-CH10）→ valid のみ ContractCertificate:

```python
@dataclass(frozen=True)
class ContractCertificate:
    skill_definition_hash: str; skill_action_id: str
    evidence_bundle_hash: str; evidence_policy_hash: str
    schema_registry_hash: str          # W-P0-3: H_WCJ(registry 内容) — registry A/B での結果差を certificate に固定
    validator_artifact_hash: str; contract_schema_version: str
    issued_at: float                   # 同一性判定外
```

### 5A2. usage eligibility（**別 API** — W-P0-2）

`evaluate_usage_eligibility(definition, evidence_bundle, evidence_policy, profile) → UsageEligibilityReport`
- EvidencePolicy §4 の per-component 判定（EXPLICIT_NONE 免除 = loud 記録）。certificate とは独立 — profile は後段で何度でも評価。

### 5B. 実行時 lifecycle validation（W-P1-6 反映）

```python
@dataclass(frozen=True)
class LifecycleValidationReport:      # W-P1-6: 型定義
    invocation_id: str
    issues: tuple[ValidationIssue, ...]   # (code, field_path, message) 安定順
    validator_artifact_hash: str

@dataclass(frozen=True)
class HandoffValidationReport:
    producer_invocation_id: str
    handoff_schema_id: str
    issues: tuple[ValidationIssue, ...]
    validator_artifact_hash: str

validate_invocation_start(invocation, definition, belief, now: float) -> LifecycleValidationReport
    # W-P1-6: now は明示引数 — freshness 評価に隠れ wall-clock 参照禁止（決定論テスト可能）
validate_outcome(invocation, outcome, definition) -> LifecycleValidationReport
validate_handoff(invocation, offer, producer_definition, consumer_definition) -> HandoffValidationReport
```
検査内容 = v2.2 §5B と同一（ownership 比較 = **required ⊆ offered** の bool 包含 — D-CH5）。certificate を無効化しない。

### 5C. codec / 5D. handoff compatibility = v2.2 のまま。

---

## 6. Migration v1→v2

### 6-1. 入力 domain・分割・**Draft statics 規則（D-CH1）**
- identity-pinned 6/9 → Draft / identity-less 3/9 → `E_MIGRATE_IDENTITY_ABSENT`（v2.2 のまま）。
- **非 bundle static fields の供給規則（D-CH1）**: 実 v1 corpus（manifest 行）は semantic schema・initiation/termination/handoff spec を持たない。これらは **registry fixture が per-field で供給**する（`accepted_handoff` と同方式; **fixture 行に provenance 必須** = source_ref + 作成根拠。provenance 無き供給 = `E_MIGRATE_STATICS_ABSENT` fail-close）。fixture 供給 field は evidence 過程で RECONSTRUCTED 以下として grade（fixture = 復元資料であり訓練時 source でない — 昇格しない）。§8 の migration test は「manifest 行 + 供給 fixture」を入力に取り、fixture 欠落 case = `E_MIGRATE_STATICS_ABSENT` を負例に含む。
### 6-2. kind 条件 slot 割当 = v2.2 のまま（**表現修正: LEARNED は全 5 slot が UNKNOWN〔executable は slot 外・常に KNOWN〕** — C-CH9）。
### 6-3. v1 19-field disposition 表 = v2.2 のまま、ただし:
- `recovery_rollback_target` → **loud-discard に変更**（NHA — 消費者 = 未実装 recovery 層。再導入は当該 chunk で schema bump）。
- `resource_requirements.control_ownership`（**untyped dict**）→ ControlResourceSpec: **key 語彙 = {ee_left, ee_right, gripper_left, gripper_right} に pin。未知 key = `E_MIGRATE_OWNERSHIP_KEY`（fail-close — D-CH5）**。
- `handoff_start_context.incoming_handoff_state_id` → previous_handoff_class（**= 当該 state の handoff_schema_id; None → None** — D-CH6）。
### 6-4. v1 公開 symbol disposition（**total 化 — D-CH2/B-CH3**）

| v1 symbol | 処遇 |
|---|---|
| harness.EXPECTED_SKILL_IDS | v2 `SKILL_ID_REGISTRY` へ継承（**module home = `contracts_v2/identity.py`・更新 = Rs 承認事項**）。共存中の等値 invariant test（§8） |
| harness.validate_manifest / verify_manifest_artifacts / evaluate_conformance / validate_source_closure | retained-in-v1（D1.1-C 後継まで; **d1_exit HOLD guard 生存**。DeprecationWarning に「shim 委譲対象外」明記）。**依存面（identity.SCRIPTED/WAIT_CLOSURE_MEMBERS・source_closure_sha256・canonical_json・finetune_cfg_hash・contracts.is_hex64）も同期間 byte-retained**、v1 test suite は window 中 green 維持（§8 invariant）— D-CH2 |
| harness.assert_no_authority / parse_root_fields / parse_belief_value | retained-in-v1（上記 4 関数の補助面; 同期間） |
| identity.canonical_json | **v1-internal ONLY — v2 hash に使用禁止**（WCJ と別物; dual-canonicalization guard を DeprecationWarning + §8 negative test で明示 — B-CH3） |
| identity.source_closure_sha256 / scripted_identity / wait_identity / learned_identity_from_files / make_initiation_context_hash / handoff_start_context / sha256_file | retained-in-v1（guard 依存 + 歴史再現用）。v2 は canonical.py / identity.py が代替 |
| policy_adapter.CanonicalContractRepr / canonicalize / is_deterministic | deprecate（v2 の certify/canonical が後継; shim 委譲なし・使用検出 = DeprecationWarning） |
| contracts.py 型群 | shim = v2 へ変換・委譲のみ。**v1 `__post_init__` 検証は retained 期間 byte 保持**（負制御 test の前提 — D-CH2） |
- **closure member 二重真実の解消**: v2 registry fixture の closure 列は「v1 定数の写し」であることを §8 の**等値 invariant test** で拘束（分岐 = test FAIL）。DC-6 の bounded 例外として supersession register ⑤ に記録済み。

### 6-5. family 写像 = v2.2 のまま。6-6. **数値境界 algorithm（C-CH3/D-CH4 差替）**:
```text
convert(v: float) = Decimal(repr(v)) を正規化:
  整数値 (v == int(v)) → 整数形文字列 ("30.0"→"30", "0.0"→"0", "1.0"→"1")
  非整数値 → 固定小数点文字列・trailing zero 除去 ("0.1"→"0.1")
  |指数| が窓 (10^±12) を超える → E_MIGRATE_FLOAT_FORM (窓内は固定小数点展開で受容: 1e-07→"0.0000001")
  出力は CanonicalDecimal 正規形検査を必ず通す (二重防御)
corpus: 1.0→"1" / 30.0→"30" / 0.0→"0" / 0.1→"0.1" / 0.831→"0.831" / 1e-07→"0.0000001" / 1e-15→E_MIGRATE_FLOAT_FORM
```
### 6-7. 既定値 / 6-8. §7b supersession = v2.2 のまま。

---

## 7. Runtime 型 = v2.2 のまま（SkillInvocation / SkillOutcome / HandoffOffer / TransitionRecord / SchemaVersionStamp / RuntimeSnapshot）+ §5B の 2 report 型（W-P1-6）。§7-2（certified-only D2 帰結・runtime hash は D2 prereg へ defer）= 不変。

## 8. Test plan（v2.2 から差分のみ）
- metamorphic **#3 差替（D-CH8）**: 「runtime 型の全 field 名が static hash の WCJ payload key 集合に不在」の **serialization-boundary assert**（vacuous 変異試験を廃止）。
- **#4b は hashed fields（grade/source_ref/proof/artifact_hash）限定 + notes-mutation 行追加（全 hash 不変）**（C-CH7）。
- corpus 追加: `E_EVIDENCE_DUPLICATE` / `E_PROOF_INSUFFICIENT` / `E_GRADE_INAPPLICABLE`（P と S 非次元の両方 — D-CH10）/ `E_PROOF_CONFLICT`（W-P1-3）/ `E_SLOT_NONE_UNPROVEN` / `E_CALLABLE_REF_KIND_MISMATCH` / `E_MIGRATE_OWNERSHIP_KEY` / `E_MIGRATE_STATICS_ABSENT` / `E_MIGRATE_BC_CONFIG_UNEXPECTED` / integral float 群（§6-6 corpus）。
- **invariant tests（D-CH2）**: `SKILL_ID_REGISTRY == EXPECTED_SKILL_IDS`・registry fixture closure == v1 定数（retained window 中）・v1 test suite green。
- 他（mutation 方式・generative seed 固定・golden vectors・cross-process・migration 分割 test）= v2.2 のまま + frozenset vector。

## 9. Module layout = v2.2 + `SKILL_ID_REGISTRY` の home = identity.py（D-CH2）。

## 10. Open points
**1 件**: review-4 transcript の **Rs 確認 PENDING**（fidelity）。W-review は file copy（byte 同一）のため確認不要。他の設計内 open = 0。

## 11. 検証系譜
- cycle-1 = 19 項 accepted → v2.2 fix → **cycle-2 で 4-lens 全数 discharge 検証（16-18/18 + 残差）**。cycle-2 verdict = **REVIEW**（max-2-cycles; log cycle 2）→ escalation = Rs 報告済み。**本 v2.3 が cycle-2 残差 + W 系 + NHA 指摘の fold**（fix 台帳 = verification-log cycle 2 consolidation + scratchpad fix-list）。
- **W→fold-map**: W-P0-1 = §1.3（v2.2 先行治癒）/ W-P0-2 = §0・§5A・§5A2 / W-P0-3 = §5A certificate / W-P0-4 = EvidencePolicy（存在 = `ac5865b66d`、内容 = v1.1）/ W-P1-1 = §2-7（U7）/ W-P1-2 = §1.2† / W-P1-3 = EvidencePolicy §3b / W-P1-4 = EvidencePolicy §4（U12）/ W-P1-5 = §8 #4a/4b（U8）/ W-P1-6 = §5B。
- pS D/V 系・review-4 fold-map（§12 相当）= v2.2 の記録を継承（transcript 参照）。

## 12. review-4 fold-map = v2.2 §12 のまま有効（対象 sha のみ本版に更新）。
