# WMSO D1.1-A `contracts_v2` — DESIGN (v2.2)

- node: `T-WMSO`; author = w2:pQ (RS-TECH-LEAD2)
- created: v1 = 2026-07-19 09:09 JST / v1.1 = 09:24 / v2 = 09:32 / v2.1 = 09:43 / **v2.2 = 10:5x JST（CC Debate cycle-1 verdict FAIL の U2-U18 fold）**
- **status: DESIGN DRAFT v2.2 — CC Debate cycle-2 → pS delta re-check → pN DESIGN PASS-CLOSE PENDING**
- governing scope: `WMSO_D11_CONTRACT_V2_SCOPE_PREREG_RSTECHLEAD2_20260719.md` v3.2.2, sha256 **`71097e58102e100657177b7ead2484bcc00840e4a788e6a295d944f7827d0966`**, commit `ea6e39b93c`
- 兄弟 normative artifacts（cycle-2 debate + pN DESIGN verify の対象、本 doc と同時 bank）:
  - **Rs review-4 transcript** = `WMSO_RS_REVIEW4_DESIGN_TRANSCRIPT_20260719.md`（sha256 `8a7915dfa3386889…`; **as-received transcript、Rs 確認 PENDING** — U1 fix）
  - **EvidencePolicy v1** = `WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md`（sha256 `4e1da7d51780d06e…`; §4.3/§4.4 の全表実体 — U11 fix）
- version 履歴: v1 (09:09; sha prefix `8bec472a6ac1` — **content 非保全**〔in-place 上書き、prefix のみ記録〕) → v1.1 (09:24; prefix `b807ce2abbd7` — 同) → v2 (09:32; prefix `4880dc0d6c6d` — 同) → v2.1 (09:43; sha256 完全形 `c49ff132ff200257085f072c875c58e3200754ac74ee28de8634b786ab2681e7`、bank `cd5482310d`) → **v2.2 (本版)**。⚠ 消滅版の完全 sha は復元不能 — 以後の版は毎版 bank し content を保全する（U18）。
- 駆動要件（引用 host 明記 — U18）: prereg §2 IN / prereg §10 (a)-(d)〔旧称 §5b — prereg 内の旧ラベル〕/ pS ratify doc §5b（`WMSO_D11_SCOPE_DESIGN_RATIFY_WMSODESIGN_20260719.md`）/ N-1・N-2（= pS ratify doc §2 の carried 2 点）/ DC-1..DC-6（prereg §10b）/ **review-4 P0-1..P0-6・P1-1..P1-4・T・OP**（transcript 参照; 「review-1 P0-n」= v1 コード欠陥 6 件、「review-4 P0-n」= 本設計への必須修正 6 件 — **番号系は別物**、常に接頭辞付きで引用する — U18）/ pS D-1..D-6+N-a・V-1..V-4 / **CC Debate cycle-1 U1-U19**（verification-log `task-WMSO-D11A-design-debate-001`）。
- **SSOT precedence（U18）**: 記述が分岐した場合の優先 = review-4 transcript（Rs 確認後）> 本 design（最新版）> prereg の表・文言（DC-2 timing・§5 表 7→5 行・§7b「SkillDefinitionHash」文言は本 design が supersede — 下記各所に記録）> EvidencePolicy artifact（§4 と byte 整合を保つ; 分岐は §9 loop で解消）。
- ⛔ 本 doc は設計のみ。code / [CHANGE] / impl は pN DESIGN PASS → pre-check → rule-check → path freeze / impl GO まで CLOSED。

---

## 0. 中心構造（review-4 の確定形）

```text
Static
  DraftSkillDefinition   — UNKNOWN slot を許す / draft hash のみ / 最終 ActionId なし
  SkillDefinition        — 全 slot 解決済み / SkillActionId + SkillDefinitionHash
Provenance
  TrainingProvenance / EvidenceBundle / EvidencePolicy（兄弟 artifact）
Certification（静的）
  certify_definition() → ValidationReport → (valid のみ) ContractCertificate
Runtime（実行記録）
  SkillInvocation / SkillOutcome / HandoffOffer / TransitionRecord
Runtime validation（実行時 — certificate を無効化しない）
  validate_invocation_start() / validate_outcome() / validate_handoff()
```

---

## 1. Static 型

### 1.1 ArtifactSlot / ControlModeSlot（review-4 P0-2）

```python
class SlotState(Enum): KNOWN | EXPLICIT_NONE | UNKNOWN

@dataclass(frozen=True)
class ArtifactSlot:
    state: SlotState
    artifact_hash: str | None      # KNOWN ⇔ 64-hex 必須 / 他 ⇔ None (違反 = E_SLOT_INCONSISTENT)

@dataclass(frozen=True)
class ControlModeSlot:
    state: SlotState               # KNOWN | UNKNOWN のみ (EXPLICIT_NONE = E_SLOT_FORBIDDEN_NONE)
    value: ControlMode | None      # KNOWN ⇔ value 必須 (E_SLOT_INCONSISTENT)
```

### 1.2 ExecutionBundle（実行を決める要素のみ）

```python
class ControlMode(Enum): DIFF_IK_EE_TARGET | SCRIPTED_SEQUENCE | WAIT   # strict decode; unknown = E_ENUM_UNKNOWN

@dataclass(frozen=True)
class ExecutionBundle:
    kind: IdentityKind                  # LEARNED | SCRIPTED | WAIT
    executable_artifact_hash: str       # 常に必須 KNOWN。LEARNED = weights sha256 /
                                        # SCRIPTED,WAIT = source-closure aggregate (§3-2)。
                                        # 〔識別 pin を持つ v1 契約は必ず保持。identity 無しの
                                        #   v1 manifest 行は §6-1 で E_MIGRATE_IDENTITY_ABSENT — U3〕
    model_architecture: ArtifactSlot
    tensor_binding: ArtifactSlot
    normalization: ArtifactSlot
    control_mode: ControlModeSlot
    runtime_config: ArtifactSlot        # KNOWN 時の hash 正規形 = §2.4。EXPLICIT_NONE 禁止
```

- `resolved(bundle)` ⇔ 全 slot.state ≠ UNKNOWN。
- **kind 別 slot 許容表（本表は Draft / SkillDefinition の両方に適用 — U4。表外 = `E_SLOT_FORBIDDEN_NONE` / `E_SLOT_INCONSISTENT` / `E_KIND_CONTROL_MISMATCH`）**:

| slot | LEARNED | SCRIPTED | WAIT |
|---|---|---|---|
| model_architecture | KNOWN・UNKNOWN | EXPLICIT_NONE | EXPLICIT_NONE |
| tensor_binding | KNOWN・UNKNOWN | EXPLICIT_NONE | EXPLICIT_NONE |
| normalization | KNOWN・UNKNOWN | EXPLICIT_NONE | EXPLICIT_NONE |
| control_mode | KNOWN(**値 ∈ {DIFF_IK_EE_TARGET}** — U15)・UNKNOWN | KNOWN(SCRIPTED_SEQUENCE) | KNOWN(WAIT) |
| runtime_config | KNOWN・UNKNOWN | KNOWN・UNKNOWN | KNOWN・UNKNOWN |

- N-a: review-4 DC-1 list の「action scale」は TensorBindingSpec（scale/bias、D1.1-B）に含まれ `tensor_binding` 経由で bundle に入る。

### 1.3 TrainingProvenance（identity 外・契約内; **learned-conditional — U6**）

```python
@dataclass(frozen=True)
class TrainingProvenance:
    execution_family: ExecutionFamily
    training_lineage: TrainingLineage
    final_artifact_hash: str | None     # learned lineage (RL_ONLY/BC_ONLY/BC_THEN_RL) = 必須・
                                        #   == ExecutionBundle.executable_artifact_hash (E_PROVENANCE_ARTIFACT_MISMATCH)。
                                        # NOT_APPLICABLE = null 必須（prereg §5 表の「全 training hash = null」に整合 — U6）
    bc_base_hash: str | None
    bc_config_hash: str | None
    demo_dataset_hash: str | None       # N-2
    demo_dataset_absent_reason: str | None   # "HISTORICAL_PRE_D11" のみ。BC 系で hash・reason 両 None = E_DEMO_HASH_MISSING
```

来歴は実行を決めない → `SkillDefinitionHash` に入り `ExecutionBundleHash` / `SkillActionId` に入らない。

### 1.4 SkillDefinition / DraftSkillDefinition

```python
@dataclass(frozen=True)
class SkillDefinition:
    contract_schema_version: str        # "2.0.0"
    skill_namespace: str                # "thread.wmso"
    skill_id: str                       # 登録集合 = v2 SKILL_ID_REGISTRY (§6-4: v1 EXPECTED_SKILL_IDS の 9 集合を継承)
    skill_variant_id: str               # 既定 "default"
    behavior_revision: int
    execution_bundle: ExecutionBundle           # resolved 必須 (残 UNKNOWN = E_BUNDLE_UNRESOLVED → Draft)
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
    required_control_resources: ControlResourceSpec   # U13: v1 resource_requirements の後継 (per-EE + gripper 所有宣言;
                                                      #   §5B ownership 検査の定義側 home。compute path 軸は v1 から loud-discard §6-3)
    recovery_rollback_target: str | None              # U13: v1 から継承 (recovery selector 層向け宣言)
    scripted_callable_ref: str | None                 # U13: v1 callable_qualname の後継 (SCRIPTED/WAIT のみ非 null。
                                                      #   identity は closure hash が担い、本 field は記録/可読参照 — hash 対象内・ActionId 対象外は §1.5 の通り definition hash にのみ入る)
    support_boundary: SupportBoundary
    freshness_policy: FreshnessPolicy
    fail_closed_action: FailClosedAction

# DraftSkillDefinition = 同一 field 集合、execution_bundle に UNKNOWN slot 可。
#   発行可: draft_definition_hash。発行不可: SkillActionId / ContractCertificate。
```

**構成型の field 定義（U2 — 未定義解消。「≡ v1」= committed `57ed32b27a` の `wmso/d1/contracts.py` 同名型と field 同一、改名のみ）**:
- `SemanticFieldSpec` ≡ v1 `FieldSpec`(field_id/dtype/shape/unit/frame) + `__post_init__` 全数値検証（§5A）。
- `InitiationPredicate 系` → `InitiationSpec` ≡ v1 `InitiationPredicate`(expr_kind/schema_ref/schema_hash/payload_canonical_json/required_belief_fields)。
- `TerminationSpec` = {declared_classes: frozenset[TerminationClass]（非空）, predicate_schema_ref: str, predicate_schema_hash: str}。
- `CheckpointSpec` = {checkpoint_id: str, resume_state_schema: str | None}（id 重複禁止）。
- `HandoffSchemaSpec` = {handoff_schema_id: str, schema_version: str, fields: tuple[SemanticFieldSpec, ...], required_field_ids: frozenset[str]}（id 重複禁止）。
- `AcceptedHandoffSpec` = {producer_skill_id: str, handoff_schema_id: str, schema_major_version: str}。
- `ResumeCapability(Enum)` = NOT_RESUMABLE | RESTART_FROM_INITIATION | RESUME_WITH_STATE。
- `SupportBoundary` ≡ v1（region_ref | in_support_predicate、少なくとも一方）。
- `FreshnessPolicy` ≡ v1 `Freshness` 改名（max_staleness_s: CanonicalDecimal | None — None は conformance で fail-close）。
- `Ownership` ≡ v1（contact/resource/control）。`ControlResourceSpec` = {ee_left: bool, ee_right: bool, gripper_left: bool, gripper_right: bool}。
- `BeliefRef`/`SnapshotRef`/`HashRef`/`ProducerOutcome`(TERMINAL|INTERRUPT union)/`TerminationClass`/`InterruptReason`/`FailClosedAction`/`IdentityKind` ≡ v1。
- `ExecutionFamily(Enum)` = {PPO, DAPG, BC, SCRIPTED, WAIT}（DAPG は enum 在住・§3 表外 = `E_LINEAGE_FORBIDDEN`）。`TrainingLineage(Enum)` = {RL_ONLY, BC_ONLY, BC_THEN_RL, NOT_APPLICABLE}。
- `SchemaRegistry` = {definitions_by_id: Mapping[(skill_id, variant), SkillDefinition | DraftSkillDefinition]}（§5A/§5D の照合 context; standalone test は fixture registry）。
- `MigrationReport` = ValidationReport と同形（issues: tuple[ValidationIssue, ...] + discards: tuple[str, ...]〔loud-discard 列挙〕）。

### 1.5 identity / hash

```text
ExecutionBundleHash   = H_WCJ(resolved ExecutionBundle)     # UNKNOWN 含みには未定義
SkillActionId         = H_WCJ({"ns": skill_namespace, "skill": skill_id,
                               "bundle": ExecutionBundleHash, "variant": skill_variant_id,
                               "brev": behavior_revision})    # keyed object (U9 — 引数列でない)
SkillDefinitionHash   = H_WCJ(SkillDefinition 全体)          # provenance・scripted_callable_ref を含む
draft_definition_hash = H_WCJ(DraftSkillDefinition 全体)
```

- 最終 `SkillActionId` は resolved bundle からのみ発行（UNKNOWN を identity に焼き込まない — review-4 P0-2）。
- `contract_schema_version` は ActionId に含めない。`behavior_revision` は振る舞い契約の改訂でのみ +1。
- 旧 `handoff_start_context` は identity から除去済み。**v1 の HandoffStartContext 値の移行先 = TransitionRecord.previous_handoff_class（class 部分）+ MigrationReport discard 記録（initiation_context_hash — 再現不能な文脈 hash のため loud-discard — U13）**。

---

## 2. WMSO Canonical JSON（WCJ — RFC 8785 準拠実装 = review-4 案 A）

`H_WCJ(x)` = sha256(WCJ(x))。

1. **object key sort = UTF-16 code unit 順**（`sorted(keys, key=lambda k: k.encode("utf-16-be"))`）。
2. lone surrogate 拒否 / duplicate key 拒否（§5C codec）。
3. 文字列 serialization = JCS 規則（最小 escape）。
4. 数値 = int のみ、`|n| ≤ 2^53 − 1`（`E_INT_RANGE`）。float 型（NaN/±Inf 含む）は拒否。
5. 実数値 = `CanonicalDecimal` 文字列。**正規形 = `re.fullmatch`**（U16 — 束縛を規範化; 等価表記 `\A(?:(0|-?[1-9][0-9]*)(\.[0-9]*[1-9])?|-0\.[0-9]*[1-9])\Z`）。literal `-0` 不可・`-0.5` 可・exponent/trailing-zero/leading-zero 不可。**順序・範囲比較は `decimal.Decimal` の exact 演算で行い、float を経由しない**（U18）。
6. NFC は WMSO schema の事前制約（identifier 類は NFC 済み要求、non-NFC = `E_ID_NOT_NFC`。canonicalizer は正規化しない）。
7. **層の明示（U7）**: (a) **key-sort comparator / raw-WCJ 層** — full-Unicode key を受け、golden vectors（非 BMP 含む）の対象; (b) **typed-serialization 入口 `canonicalize()`** — 型からの直列化のみを受け、**防御的 ASCII-key assert** を持つ（設計上 key = field 名で ASCII）。§8 の非 BMP vector は層 (a) を対象とする。
8. golden test vectors: RFC 8785 由来 + 非 BMP key（絵文字 vs U+FB33 — 素朴 code-point sort と結果が異なることを固定）+ **composite vector 1 本（resolved ExecutionBundle 全体 → ExecutionBundleHash の期待値固定 — U9）**。

### 2.3 composite 直列化の pin（U9）
- 全 hash 入力は **keyed object**（引数リスト形は用いない）。
- `ArtifactSlot` / `ControlModeSlot` は**全状態で** `{"state": <SlotState.value>, "artifact_hash": <hash|null>}` / `{"state": …, "value": <ControlMode.value|null>}` の object として直列化（KNOWN を bare string に潰さない）。
- Enum は **`.value` 文字列**で encode（decode は §5C strict）。
- `evidence_bundle_hash` の record 順 = **`component_kind.value` の bytes 昇順**（Python Enum 比較不能問題の排除 — U9）。

### 2.4 `runtime_config_hash` 正規形
strict decode（§5C）済み正規 object（ASCII key / int・CanonicalDecimal・NFC 文字列 / list / object）を WCJ で hash。SCRIPTED schedule = `[{op, args}, …]`。WAIT = `{wait_kind, duration_s | condition_ref}`。

---

## 3. execution_family × training_lineage（**full 列 inline — U2/U6**）

**許容表（validator の唯一の許容源; 表外 = `E_LINEAGE_FORBIDDEN`、unknown enum = `E_ENUM_UNKNOWN`; 照合対象 = TrainingProvenance）**:

| # | execution_family | training_lineage | 必須 hash | null 必須 | source-closure |
|---|---|---|---|---|---|
| 1 | PPO | RL_ONLY | final_artifact_hash | bc_base / bc_config / demo_dataset = null | null |
| 2 | PPO | BC_THEN_RL | bc_base + bc_config + final_artifact_hash | —（demo は hash か absent_reason — §1.3） | null |
| 3 | BC | BC_ONLY | final_artifact_hash | RL stage fields = null | null |
| 4 | SCRIPTED | NOT_APPLICABLE | —（executable = closure aggregate） | final/bc/demo 全 null | **必須** |
| 5 | WAIT | NOT_APPLICABLE | — 同上 | 同上 | **必須** |

- **§3-2 source-closure（U6 — prereg §5 の fail-closed 挙動を継承）**: SCRIPTED/WAIT の `executable_artifact_hash` = **enumerated closure member の aggregate sha256**。member 欠落 = `FileNotFoundError`（fail-closed; v1 `validate_source_closure` と同挙動）。closure member 列は runtime_config でなく registry fixture が保持。
- **prereg §5 表（7 行）との関係**: DAPG 2 行は DC-5 により除外（本表 5 行が supersede — precedence 記録済み header）。
- coherence: IdentityKind ↔ ExecutionFamily（LEARNED⇔{PPO,BC}, SCRIPTED⇔SCRIPTED, WAIT⇔WAIT; `E_KIND_FAMILY_MISMATCH`）+ **kind ↔ control_mode 値（§1.2 表 — U15）**。
- N-1: 本表は構造的許容規則。歴史 artifact の分類 verdict は evidence 過程（§4）の専管。
- demo hash 執行（D-2）: §1.3 のとおり。

---

## 4. Evidence model

- ComponentKind 13 種 / EvidenceGrade rank 4..0 / ProofKind 15 種 / EvidenceRecord（notes は bundle hash 対象外）= v2.1 から不変（型は §1.4 相当の定義を維持）。
- **(component × grade) ProofPolicy・profile required set・min_grade の全表 = 兄弟 artifact `WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md`（sha256 `4e1da7d51780d06e…`）が normative 実体**（U11）。本文の代表行は例示であり、分岐時は EvidencePolicy artifact と §9 loop で解消。
- **CLOSED_LOOP required set に `TRAINING_PROVENANCE`（≥ RECONSTRUCTED_COMPATIBLE）を含む**（U12 — lineage 自己申告の根絶。全 13 component の required/min_grade = EvidencePolicy §4 の表）。
- **evidence record 不在の required component は UNKNOWN(0) として集約**（missing = 最弱; U18）。集約 = required set の最弱 grade が bind。
- usage matrix = ceiling（authority grant でない; acceptance test は必要条件の一つ; O0/S0/V0 two-key + 独立安全 gate を必ず conjoin）。
- **「条件付き」cell の定義（inline — U2; prereg:184 の「design doc 内明示」要求に適合）**: 「acceptance test 後に可」= 独立 acceptance test PASS が追加必要条件 / 「非 authority のみ」= 出力が制御に接続されない記録・比較 mode に限る / 「診断のみ」= replay 入力にも使わず次元・形式診断に限る。silent に「可」へ潰さない。

---

## 5. Validation（4 系統 — review-4 P0-1）

### 5A. 静的 certification

`certify_definition(definition, evidence_bundle, evidence_policy, schema_registry) → DefinitionCertificationResult`

**値単体検査の全項目（inline — U2）**: 全 ID/unit/schema_ref/namespace 非空（whitespace-only = `E_ID_EMPTY`）/ shape 全次元 `type(x) is int` かつ >0（bool-as-shape 拒否）/ isfinite: timestamp・duration・cost・TTL・confidence・progress・p50・p95・std・全 bounds・normalization mean/std・scale/bias〔対象が本 chunk の型に現れない量（p50/p95/std 等）は §6-3 の deferred-with-object 注記に従い、D1.1-B/D2 で当該型が入った時点で本規則が適用される — U13〕/ 範囲: TTL>0・confidence/progress∈[0,1]・duration/cost≥0・p50≤p95・std≥0（CanonicalDecimal は decimal.Decimal 演算）/ hash 64-hex 小文字（`E_HASH_MALFORMED`）/ NFC（`E_ID_NOT_NFC`）。
identity 整合 = §3 表・coherence・E_DEMO_HASH_MISSING・E_PROVENANCE_ARTIFACT_MISMATCH（learned のみ）。静的 lifecycle 内部整合 = checkpoint/handoff id 重複禁止・RESUME_WITH_STATE ⇔ resume_state_schema・accepted_handoff の静的互換（§5D 規則を registry の producer 定義に対し）。evidence = EvidencePolicy 照合。
Draft 入力 = 検査は走るが certificate 不発行（`E_BUNDLE_UNRESOLVED` を含む report のみ）。

出力 = `ValidationReport`（常時; issues = ValidationIssue(code/field_path/message) の (code, field_path) 安定順）→ valid のみ `ContractCertificate`（skill_definition_hash / skill_action_id / evidence_bundle_hash / evidence_policy_hash / validator_artifact_hash / contract_schema_version / issued_at〔同一性判定外〕）。

### 5B. 実行時 lifecycle validation（certificate を無効化しない）
`validate_invocation_start`（initiation predicate / freshness_policy 評価 / **required_control_resources vs 実 ownership** — U13）/ `validate_outcome`（terminal ∈ declared_classes / interrupt checkpoint ∈ checkpoint_specs / duration・cost 有限非負 / invocation_id 一致）/ `validate_handoff`（offer.handoff_schema_id ∈ producer 宣言 / producer_invocation_id 一致 / control_epoch 単調 / §5D 互換）。

### 5C. codec（strict decoder）
duplicate key 拒否 / NaN・±Inf 拒否 / unknown field 拒否 / enum strict（unknown = `E_ENUM_UNKNOWN`）/ lone surrogate 拒否。hash 入力経路で素の `json.loads` を使わない。

### 5D. handoff compatibility 規則
consumer required ⊆ producer fields / dtype・shape・unit・frame 完全一致 / schema major version 一致 / producer 追加 optional 可 / 暗黙変換禁止（変換は後続 transition adapter）。

---

## 6. Migration v1→v2（review-4 P0-6 + U3/U4/U5/U10/U13）

`MigrationResult`（draft_definition | None / runtime_snapshot | None / evidence_bundle / report: MigrationReport）。

### 6-1. 入力 domain と分割（U3）
- **入力 = v1 `skill_contracts_manifest.json` の rows + 構築可能な v1 契約 instance**。
- **identity-pinned 行（実測 6/9**: APPROACH_CABLE / INSERT_INTO_CLIP / TRANSPORT / RECLAMP_L / HALF_UNCLAMP_RELEASE / CLIP_CONFIRM**）→ DraftSkillDefinition**。
- **identity 無し行（実測 3/9**: CLAMP / UNCLAMP / AERIAL_REGRASP — INADMISSIBLE_*、artifact hash 皆無**）→ `E_MIGRATE_IDENTITY_ABSENT`（loud 拒否; Draft を作らない**。placeholder hash の発明 = review-1 P0-2 の再導入につき禁止**）。
- 完全復元可能（全 slot KNOWN/EXPLICIT_NONE が evidence 込みで立つ）場合のみ SkillDefinition 候補; 実 v1 corpus では発生しない見込み（下記 6-2）。

### 6-2. kind 条件付き slot 割当（U4 — 機械的導出、推測ではない）
| slot | LEARNED | SCRIPTED / WAIT |
|---|---|---|
| model_architecture / tensor_binding / normalization | UNKNOWN（v1 に無し — **LEARNED は 5 slot 中 executable 以外の全てが UNKNOWN**、旧「3 field」表現は撤回 — U17） | EXPLICIT_NONE（kind により強制 — §1.2 表準拠） |
| control_mode | UNKNOWN | KNOWN(SCRIPTED_SEQUENCE) / KNOWN(WAIT)（kind により強制） |
| runtime_config | UNKNOWN | UNKNOWN（schedule 情報は v1 に無し） |
→ いずれの kind も runtime_config（等）が UNKNOWN のため **主出力は Draft**。

### 6-3. v1 全 root field の disposition 表（U13 — 完全列挙。silent drop なし）
| v1 field (`contracts.py:511-533` の 19) | v2 disposition |
|---|---|
| schema_version | → contract_schema_version（"2.0.0" へ、MigrationReport 記録） |
| action_key.skill_id / executable_identity | → skill_id / ExecutionBundle.executable_artifact_hash（scripted/wait = closure、learned = weights）+ TrainingProvenance（family/lineage/bc hashes — **v1 family 文字列写像 = 6-5**） |
| action_key.handoff_start_context | class 相当 → TransitionRecord.previous_handoff_class の語彙 / initiation_context_hash → **loud-discard**（再現不能文脈 hash） |
| policy_family | → 6-5 写像 |
| obs_action_schema (fields + field_semantics) | → semantic_obs/action_schema + 対応 component evidence（RESOLVED 実績根拠なし → RECONSTRUCTED_COMPATIBLE 以下で再記録・昇格なし） |
| initiation_predicate | → InitiationSpec（同 field） |
| required_belief_confidence | → InitiationSpec 側 predicate payload へ吸収（belief confidence 閾値は initiation 条件 — MigrationReport 記録） |
| termination_classes | → TerminationSpec.declared_classes |
| progress_phase | → **RuntimeSnapshot.progress_phase**（runtime 側 — U13 の home 明示） |
| safe_interruption_checkpoints | → checkpoint_specs（resume_state_schema=None で） |
| handoff (SkillHandoffState 実体) | → RuntimeSnapshot.handoff（runtime 記録; 静的 schema 部分は HandoffSchemaSpec に再宣言） |
| accepted_incoming_handoff_set | → accepted_handoff（producer/schema/version の 3 組へ正規化; 不足情報は UNKNOWN 扱いで registry fixture が補完） |
| duration_cost_distribution | → **loud-discard**（静的 prior は廃止 — 分布推定は Phase D SDM の職務。DC-4 の p50/p95/std 検査は「対象型が再導入された時点で適用」の deferred-with-object と注記 — review-4 OP と整合） |
| resource_requirements | control_ownership → **required_control_resources** / compute (FAST/SLOW_PATH) → **loud-discard**（orchestrator compute path は O0/RT0 層の関心 — Phase F で再設計） |
| recovery_rollback_target | → recovery_rollback_target（継承） |
| fail_closed_action | → fail_closed_action |
| policy_version | → **loud-discard**（identity は hash 体系が担う; 人可読 version は provenance notes へ） |
| freshness | → FreshnessPolicy（max_staleness_s は 6-6 の decimal 変換） |
| support_boundary | → support_boundary |
| admissibility (4 bool) | → **明示 discard + MigrationReport loud 記録**（V-4） |
| (scripted/wait) callable_qualname | → **scripted_callable_ref**（U13） |

### 6-4. v1 公開 symbol の disposition（U5 — shim が委譲できない面の明示）
| v1 symbol (`harness.py` 等) | 処遇 |
|---|---|
| EXPECTED_SKILL_IDS | → v2 `SKILL_ID_REGISTRY` 定数として**継承**（9 集合同一; shim は re-export） |
| validate_manifest / verify_manifest_artifacts / evaluate_conformance / validate_source_closure | **retained-in-v1 例外**: D1.1-C の後継（v2 manifest/registry 検証）が land するまで v1 実装が生存し、**d1_exit=="HOLD" の機械 guard を維持**する。shim 委譲対象外であることを DeprecationWarning docstring に明記（loud）。同 release remove 禁止（AGENTS.md）を再確認 |
| contracts.py の型群 | shim = v2 へ変換・委譲のみ（独自 state/validation なし — DC-6） |
- v1 IMPL PASS（`57ed32b27a`）を v2 の証拠に引用しない（R2）。

### 6-5. v1 `policy_family` 全域写像（total — U2 inline）
| v1 文字列 | → (ExecutionFamily, TrainingLineage) |
|---|---|
| "BC+RL" | (PPO, BC_THEN_RL) |
| "PPO" | (PPO, base/config null なら RL_ONLY、else BC_THEN_RL) |
| "BC" | (BC, BC_ONLY) |
| "DAPG" | (DAPG, 宣言 provenance) — **写像は total、可否は §3 表が判定（現行 = `E_LINEAGE_FORBIDDEN`; corpus case 必須 — NHA caveat）** |
| "SCRIPTED" | (SCRIPTED, NOT_APPLICABLE) |
| "WAIT" | (WAIT, NOT_APPLICABLE) |
| その他 / 欠落 | `E_MIGRATE_FAMILY_UNKNOWN` / identity 無し行は 6-1 の `E_MIGRATE_IDENTITY_ABSENT` が先行 |

### 6-6. 数値境界（U10）
v1 binary float（freshness.max_staleness_s / predicate payload 内数値等）→ **Python `repr()`（shortest round-trip）で decimal 文字列化 → CanonicalDecimal 正規形検査**。exponent 形になる値（例 1e-07）= `E_MIGRATE_FLOAT_FORM`（fail-closed）。float-bearing v1 fixture の migration test を §8 に追加。

### 6-7. 既定値
`behavior_revision = 1` / `skill_variant_id = "default"` / `contract_schema_version = "2.0.0"`。

### 6-8. prereg §7b 文言との関係（U18）
prereg §7b「同じ v1 → 常に同じ **SkillDefinitionHash**」は、review-4 の Draft model 下では「**draft_definition_hash**（完全解決可能時は SkillDefinitionHash）」と読む（supersession 記録）。

---

## 7. Runtime 型

```python
@dataclass
class SkillInvocation:          # U2 inline（v2 で確定済みの field 集合を明記）
    invocation_id: str
    skill_action_id: str        # certified action のみ（Draft は invocation 不可 — §7-2）
    skill_definition_hash: str
    start_belief_ref: BeliefRef
    start_time: float
    current_phase: str
    elapsed_s: float
    control_epoch: int

@dataclass(frozen=True)
class SkillOutcome:             # checkpoint_id 無し（outcome union からのみ — review-4 P0-5）
    invocation_id: str
    outcome: ProducerOutcome
    end_belief_ref: BeliefRef
    duration_s: float
    accumulated_cost: float

@dataclass(frozen=True)
class HandoffOffer:             # compatibility 無し + control_epoch（review-4 P0-5）
    handoff_schema_id: str
    producer_invocation_id: str
    producer_action_id: str
    producer_definition_hash: str
    control_epoch: int
    outcome: ProducerOutcome
    belief_ref: BeliefRef
    ownership: Ownership

@dataclass(frozen=True)
class TransitionRecord:         # U2 inline（full field set）
    episode_id: str
    invocation_id: str
    start_belief_ref: BeliefRef
    goal_context: str
    previous_handoff_class: str | None
    skill_action_id: str
    skill_definition_hash: str
    end_belief_ref: BeliefRef
    outcome: ProducerOutcome
    duration_s: float
    accumulated_cost: float
    safety_events: tuple[str, ...]
    schema_versions: SchemaVersionStamp

@dataclass(frozen=True)
class SchemaVersionStamp:
    contract_schema_version: str
    belief_schema_version: str
    evidence_policy_hash: str
    recorder_artifact_hash: str

@dataclass
class RuntimeSnapshot:          # v1 runtime fields の migration 先
    progress_phase: str | None = None
    handoff: HandoffOffer | None = None
```

**§7-2 明示帰結（U14）**: TransitionRecord / SkillInvocation は **certified SkillActionId のみ**を key にする（Draft 不可）。したがって **D2 データ収集は certified skill に限られ、D1.1-B 完了（tensor binding 回収）まで learned skill の transition 行は 0 になり得る** — これは fail-closed の意図された帰結であり、隠れた前提ではない。**runtime 記録（float fields を含む）の content-hash 化は WCJ 対象外であり、その方式は D2 prereg で確定する（明示 defer — U14）**。

---

## 8. Test plan

- standalone / monorepo 分離（fixture registry / closure fixture 含む）。standalone = 配布物のみで全実行・unexpected skip 0。
- **mutation test**: 各 operator は 1 不変条件を明示破壊し期待 error code + field path を宣言（valid→valid 変異は operator にしない）。
- **generative / metamorphic**（stdlib random・seed 固定・失敗時 seed+入力保存）:

| # | 変換 | 期待 |
|---|---|---|
| 1 | contract_schema_version 変更 | ActionId 不変・DefinitionHash 変化 |
| 2 | behavior_revision 変更 | 両方変化 |
| 3 | runtime field 変更 | static hash 全不変 |
| **4a** | **TrainingProvenance field 変更** | **ActionId・evidence_bundle_hash 不変 / DefinitionHash・certificate 変化**（U8） |
| **4b** | **TRAINING_PROVENANCE 系 EvidenceRecord 変更** | **ActionId・DefinitionHash 不変 / evidence・certificate 変化**（U8） |
| 5 | ExecutionBundle 変更 | ActionId 変化 |
| 6 | TransitionRecord.previous_handoff_class 変更 | ActionId・static hash 不変（旧「handoff start context」の具体化 — U18） |
| 7 | **非 BMP key vector を層 (a)（key-sort comparator）に適用**（U7） | RFC 期待順（素朴 sort と不一致であることを固定） |
| 8 | EvidenceRecord 順序 shuffle | EvidenceBundleHash 不変 |
| 9 | profile required component 1 欠損 | authority eligibility 不成立（missing→UNKNOWN 集約） |
| 10 | certificate 発行後の runtime lifecycle 違反 | certificate 有効のまま・LifecycleReport のみ違反 |

- invalid corpus: review-1 実証 negative + DC-4 追加分 + `E_DECIMAL_NONCANONICAL`（`-0` / **anchoring-trap: `junk-0.5`・`0.0`・`1.50`・`03`・`1e3`・`5.`** — U16）+ lone surrogate + duplicate key + non-NFC + int>2^53−1 + slot 不整合（E_SLOT_INCONSISTENT / E_SLOT_FORBIDDEN_NONE / **E_KIND_CONTROL_MISMATCH: LEARNED×KNOWN(WAIT)** — U15）+ **"DAPG" 契約 → E_LINEAGE_FORBIDDEN**（NHA）+ **identity-less v1 行 → E_MIGRATE_IDENTITY_ABSENT**（U3）+ **float-bearing v1 → 変換 or E_MIGRATE_FLOAT_FORM**（U10）。
- migration tests: 決定的 / 同一入力同一 hash（6-8 の読みで）/ v2→v2 no-op / 不完全 v1 fail-closed / UNKNOWN 非昇格 / **「identity-pinned 6/9 → Draft」+「3 行 → E_MIGRATE_IDENTITY_ABSENT」**（U3）。
- cross-process hash stability（subprocess）+ WCJ golden vectors + **composite bundle vector**（U9）。

## 9. Module layout（impl GO 時に確定）
`thread_isaac_lab/wmso/contracts_v2/`: `types.py identity.py evidence.py certify.py lifecycle.py codec.py canonical.py migrate.py tests/`（`wmso/d1/` は §6-4 の処遇）。

## 10. Open points
**なし。**（EvidencePolicy v1 = 兄弟 artifact として本 v2.2 と同時に作成済み・cycle-2 debate + pN DESIGN verify の対象 — U11。旧 open 3 件は v2 で解消済み。）

## 11. 検証系譜と保存
- pS D-1..D-6+N-a / V-1..V-4: v2.2 で全保存（配置は v2.1 §11 と同一 + U 系 fold で深化）。
- **CC Debate cycle-1（5 体 lensed + NHA）= FAIL → 本 v2.2 が fix**: U1（transcript bank）/ U2-U18（本文 fold — §別対応は verification-log の consolidator 参照）/ U19 = prereg 次回 re-bank 時の records-fix 提案として保留。
- DC-2 timing supersession（TENSOR_BINDING/CONTROL_MODE enum 即時追加）= review-4 P0-4 による（transcript §「4. Evidence modelを閉じ切る」— Rs 確認 PENDING の transcript を典拠とすることを明示）。

## 12. review-4 → fold-map（v2.2 更新版; Rs 見出し verbatim は transcript 参照）
| review-4 # | fold 先 |
|---|---|
| P0-1 | §0 / §5A / §5B / metamorphic #10 |
| P0-2 | §1.1–§1.5 |
| P0-3 | §2 |
| P0-4 | §4 + EvidencePolicy v1 artifact |
| P0-5 | §7 |
| P0-6 | §6（6-1..6-8） |
| P1-1..P1-4 | §5D / §5A / §5C / §1.4 FreshnessPolicy+§5B |
| T | §8 |
| OP | §2.4 / §2-6・7 / §7 SchemaVersionStamp / §10 |
| header | 冒頭 |
