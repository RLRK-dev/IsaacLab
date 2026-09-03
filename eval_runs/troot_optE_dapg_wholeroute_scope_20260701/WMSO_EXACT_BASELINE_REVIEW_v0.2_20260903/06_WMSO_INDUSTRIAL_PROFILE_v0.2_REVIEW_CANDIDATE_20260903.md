# WMSO `IndustrialDeploymentProfile` — DEPLOYMENT PROFILE SPEC (v0.2 REVIEW CANDIDATE)

- node: `T-WMSO`; 起草 = Claude Code web session（review candidate 起草・**authority 無し**・凍結物へ非接触）; 作成 = 2026-09-03 16:5x UTC（`date -u` 実測）
- status: **REVIEW CANDIDATE v0.2（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）**
- 土台（凍結・編集しない・4 file）: contracts_v2 DESIGN v2.11.2 `00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff` @ `54f90a7de1e02fb14eaf793bf3c60d9503d0d82e` ／ EP v1.9 md `c474acea7c58acc22050c2ad9944fd45a18f5c76967964b42d11922e28fa27e7` ／ EP JSON v1.9 `e63176af9bc3a246b1c32db369ec59f8d09a4c96c381bb03a3a6024bd9811c6e`（definition hash `e7ca43093084c167a209b008533a66d26a1fd3223d2a3c11274d28306c3ff803`）／ tensor_binding DESIGN v13 `5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6` @ `07250f4a0208b3bbd27eae6fef7d980743c4b538`
- 前提文書: D0 architecture（EXIT GRANTED — `thread_isaac_lab/thread-vault/T-WMSO/state.md:91`）／ Rs C3 裁定（slice EP evidence profile = SHADOW rank 2・非 authority；execution profile は別軸・未裁定）／ handoff 決定（2026-09-03）／ 対の runtime spec = `05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md`（本 doc の型は 05 §4 `ActiveAuthorityLease.profile_hash` / `TimingBinding` / `AcceptedEnvelope` / `HealthConfirmation.profile_health_checks` に結線）
- ⛔ impl / training / closed-loop authority / production / push / freeze / slice = CLOSED 継続。本 doc は設計書面のみ。
- `$D` = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701`。全 `file:line` は起草時に `sed -n` で確認。

## 0. 中心構造

```text
IndustrialDeploymentProfile = 「cell・controller・tool・payload・workspace・safety restriction・health check・calibration・gateway config・
  timeout・escalation・deployment evidence の宣言」を content-addressed artifact にしたもの（profile_hash = H_WCJ(profile)、反循環）。
役割: (a) frozen 意味論を **狭めることしかできない**（monotone strengthening — 機械検査 P_*）
      (b) AcceptedEnvelope の非 frozen 項（ControllerEnvelope / WorkspaceRestriction / SafetyRestrictionSet）を供給する
      (c) ActiveAuthorityLease に profile_hash で束縛され、変更 = 新 lease（05 §4.1）
      (d) EP v1.9 の外にある deployment evidence を DeploymentEvidencePolicy として束ねる（EP 非改訂）
持たないもの: policy action space の bounds（D1.1-B が hash で持つ）／ 制御周波数・hold の変更権（等値のみ）／ authority ／ 合成（composition）
3 つの「profile」軸（混同しない）:
  EP evidence profile（CLOSED_LOOP / SHADOW / OFFLINE_REPLAY・required set + min_grade・EP §4）
  execution profile（boundary-only / real-time・charter :13・Rs 未裁定 C3 :65）
  deployment profile（本 doc・cell 固有条件・runtime 層）
```

## 1. 前提・語彙（frozen 参照と、本 doc が依拠する読み）

| 凍結語彙（verbatim） | locus | 本 doc での位置づけ |
|---|---|---|
| `ActionBinding.features[].bounds`（全 action feature は `bounds` 必須） | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:138`、`BoundsSpec` `:52`、per-feature `bounds` `:81` | AcceptedEnvelope の INTRINSIC 項。**本 doc は写さない・上書きしない**（`tensor_binding_hash` 参照のみ） |
| `action_scale`（全次元共通 scale） | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:133` | 同上（INTRINSIC 項の適用順の一部） |
| `ActionTimingSpec{action_rate_hz, hold}` / `ActionHold = ZERO_ORDER_HOLD \| LINEAR_INTERPOLATE` | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:125-127` / `:40` | **等値のみ**（R1）。profile は変えられない |
| `TimingSpec{policy_rate_hz, obs_sampling_rate_hz, max_obs_staleness_s}`（`max_obs_staleness_s` = 訓練時仮定、runtime 鮮度 = frozen FreshnessPolicy） | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:96-99` | rate = 等値のみ。staleness は記録のみ（執行しない） |
| `control_mode`（bundle.control_mode と等値必須・LEARNED ⇒ DIFF_IK_EE_TARGET のみ） | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:132` | 等値のみ。profile は制御様式を変えない |
| `FeatureBinding.unit` / `frame` 等値必須 | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:75-76` | INTRINSIC 項は policy action space、profile 項は workspace / joint space — **空間が違うので literal 交差を作らない**（§4） |
| version bump = identity event（`tensor_binding_hash` → `ExecutionBundleHash` → `SkillActionId`） | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:185` | profile は binding を **hash で名指し**する（`BindingExpectation`）。binding が変われば expectation も変わる |
| 反循環規則（自身の hash・SkillActionId・ExecutionBundleHash を preimage に置かない） | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:23` | `profile_hash` に同型適用（§2.3） |
| `SkillDefinition.required_control_resources: ControlResourceSpec` / `freshness_policy: FreshnessPolicy` / `fail_closed_action: FailClosedAction` | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:142` / `:146` / `:147` | 変更不可。profile は **追加の連言**と **有限値への強化**しか持たない |
| `InitiationSpec` / `ExprKind` / `FreshnessPolicy` / `Ownership` / `ControlResourceSpec` = {ee_left, ee_right, gripper_left, gripper_right} | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151` | `InitiationStrengthening` の述語語彙は frozen `ExprKind` を再利用（member 追加なし）。`ResourceAvailability.control` は frozen `ControlResourceSpec` そのもの |
| `validate_invocation_start(…, now)` = initiation predicate / freshness_policy 評価 / required ⊆ offered | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:372-373`、`:380` | frozen 検査は不変。profile の強化は **runtime が別 conjunct として評価**（05 §6.2 B4） |
| WCJ 規則（UTF-16 code unit key sort 等） / `SkillDefinitionHash` = H_WCJ(SkillDefinition 全体) / `BehaviorSignature` 13 面 | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:168` / `:159` / `:218` | profile は `SkillDefinition` に触れない ⇒ いずれの hash も不変（03 matrix） |
| §5C strict codec（unknown field 拒否） | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:385` | profile 自身の codec も strict（`P_UNKNOWN_FIELD`） |
| EP §4 usage profiles（CLOSED_LOOP / SHADOW（非 authority）/ OFFLINE_REPLAY）・profile 充足の意味論・usage matrix = ceiling | `$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:154`、`:156`、`INITIATION_SPEC` 行 `:148` | **evidence profile**。本 doc の deployment profile とは別物（§1.1） |
| EP `INITIATION_SPEC` claim target = H_WCJ(当該 spec) | `$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:101` | frozen `InitiationSpec` を書き換えると claim target が動く ⇒ profile は書き換えない（連言追加のみ） |
| `evidence_policy_definition_hash` = H_WCJ(policy_definition)（metadata は hash 外） | `$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:163`、`$D/WMSO_EvidencePolicy_v1.9.json:5` | 本 doc は `policy_definition` に何も足さない（04） |
| EP `usage_ceiling.closed_loop_authority` = evaluate_authority_grant conjuncts | `$D/WMSO_EvidencePolicy_v1.9.json:213` | profile は authority を付与しない（§9） |
| D0 §F `SafetyDecision{STOP, HOLD, RETRACT, FORCE_LIMIT}` / preemption acts first | `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:317`、`:319` | profile の `SafetyRestrictionSet` は**静的**制約。live 決定は IndependentSafetyLayer（05 §5.2 (i)） |
| charter: boundary-only or real-time **execution profile** / S0 shadow = zero control authority | `$D/WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md:13`、`:129` | execution profile 軸は本 doc の外（C3 `:65`） |
| Rs C3: EP evidence profile と execution profile は別軸 | `$D/WMSO_RS_C3_RULING_SLICE_PROFILE_20260720.md:5`、`:65` | §1.1 |
| slice prereg: boundary = TERMINAL のみ | `$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59` | profile は boundary 種別を変えない |

### 1.1 3 軸の分離（表）

| 軸 | 定義元 | 決定者 | 本 doc |
|---|---|---|---|
| EP evidence profile | EP §4（required set + min_grade） | 凍結・`requested_profile` は eligibility 入力 | 参照のみ。lease の `authority_decision_ref` 経由（05 §4.4） |
| execution profile（boundary-only / real-time） | charter `:13` | **Rs 未裁定**（C3 `:65`） | 決めない |
| deployment profile（本 doc） | 本 doc | 起草 = CC・採否 = two-key + Rs | cell 固有条件の宣言。frozen を狭めるだけ |

## 2. `IndustrialDeploymentProfile` 型（全て 新語・deployment 層のみ・凍結 schema 外）

### 2.1 構成型

```python
# 新語（deployment 層のみ・凍結 schema 外）。frozen 型は名前を再利用する場合のみ「frozen」と注記。
class StopClass(Enum):            CONTROLLED_STOP | POWER_REMOVED_STOP          # 停止の種別。物理挙動は controller 固有（§10 OPP-4）
class HealthCheckKind(Enum):      CONTROLLER_LIVENESS | SAFETY_LAYER_HEARTBEAT | CALIBRATION_VALID | TOOL_IDENTITY | GATEWAY_CONFIG_MATCH | ENVELOPE_READBACK
class HealthCheckStage(Enum):     BEFORE_PERMIT | AT_HEALTH_CONFIRMATION | BOTH
class EscalationTarget(Enum):     HOLD | SAFE_STOP                              # 05 §7 の disposition 名を再利用（SAFE_STOP 側へのみ強化）

@dataclass(frozen=True)
class CellIdentity:
    cell_id: str
    site_id: str
    robot_model_ref: str                   # RS71 §0 の型式（UR15）と一致必須 — DDR#41 の曝露点（§10 OPP-7）
    robot_serial_ref: str
    controller_firmware_ref: str
    layout_revision_ref: str               # cell layout の版（keep-out の前提）

@dataclass(frozen=True)
class ControllerEnvelope:                  # 運動学・力学の上限（SI）。**制御周波数を含まない**（R1）
    joint_velocity_max: tuple[CanonicalDecimal, ...]        # [rad/s]・関節順は robot_model_ref の規約
    joint_acceleration_max: tuple[CanonicalDecimal, ...]    # [rad/s^2]
    joint_jerk_max: tuple[CanonicalDecimal, ...] | None     # [rad/s^3]
    ee_speed_max: CanonicalDecimal                          # [m/s]
    ee_force_max: CanonicalDecimal | None                   # [N]
    joint_torque_max: tuple[CanonicalDecimal, ...] | None   # [N·m]
    stop_class: StopClass
    representation: str = "joint_space"                     # AcceptedEnvelope 項の評価空間（05 §4.3）

@dataclass(frozen=True)
class ToolPayloadSpec:
    tool_id: str
    tool_mass_kg: CanonicalDecimal
    tool_com_m: tuple[CanonicalDecimal, CanonicalDecimal, CanonicalDecimal]
    payload_mass_max_kg: CanonicalDecimal
    tcp_offset_ref: str                    # calibration 側で attest される TCP offset の参照

@dataclass(frozen=True)
class ZoneRef:
    zone_id: str
    geometry_sha256: str                   # zone 幾何（外部 artifact）の content hash
    kind: str                              # "keep_out" | "reach_limit" | "height_band"

@dataclass(frozen=True)
class WorkspaceRestriction:
    zones: tuple[ZoneRef, ...]             # 追加の制約のみ（許可領域の拡張は表現不能 — §3）
    representation: str = "workspace"

@dataclass(frozen=True)
class SafetyRestrictionSet:               # 静的 restriction（gateway predicate）。live 決定は IndependentSafetyLayer
    restriction_ids: tuple[str, ...]
    predicate_refs: tuple[str, ...]        # 各 predicate は「拒否条件」のみを表現する（許可条件は表現不能）
    requires_safety_layer_health: bool     # **True 必須**（P_SAFETY_LAYER_NOT_REQUIRED）

@dataclass(frozen=True)
class ExtraInitiationConjunct:            # frozen InitiationSpec に AND される追加述語（置換ではない）
    conjunct_id: str
    expr_kind: ExprKind                    # frozen enum 参照（member 追加なし）
    schema_ref: str
    schema_hash: str
    payload_canonical_json: str
    required_belief_fields: tuple[str, ...]

@dataclass(frozen=True)
class InitiationStrengthening:
    conjuncts: tuple[ExtraInitiationConjunct, ...]   # 意味論 = frozen initiation predicate ∧ (∧ conjuncts)。OR / NOT / 置換の表現は無い

@dataclass(frozen=True)
class FreshnessStrengthening:
    max_staleness_s: CanonicalDecimal | None          # None = 強化なし。有限値 = frozen FreshnessPolicy.max_staleness_s との min（§3）

@dataclass(frozen=True)
class ResourceAvailability:               # SAFEHOLD からの初回起動で offered 集合となる（05 §12 OP-3）
    control: ControlResourceSpec           # frozen 型（{ee_left, ee_right, gripper_left, gripper_right: bool}）
    contact: bool
    resource: dict                         # frozen Ownership.resource と同じ opaque dict（値語彙は凍結に無い）
    attested_by: tuple[str, ...]           # DeploymentEvidenceRecord.record_id（CELL_COMMISSIONING）— 空 = P_RESOURCE_UNATTESTED

@dataclass(frozen=True)
class RuntimeTimeouts:                    # 05 TimingBinding へ写される（05 INV-22: 数値は profile 由来）
    ack_timeout_s: CanonicalDecimal
    permit_ttl_s: CanonicalDecimal
    health_confirm_timeout_s: CanonicalDecimal
    command_deadline_s: CanonicalDecimal   # LEARNED では ≥ 1 / action_rate_hz（05 §4.1）
    manager_liveness_s: CanonicalDecimal

@dataclass(frozen=True)
class HealthCheckSpec:
    check_id: str
    kind: HealthCheckKind
    evaluator_ref: str
    stage: HealthCheckStage
    fail_closed: bool                      # **True 必須**

@dataclass(frozen=True)
class CalibrationRef:
    calibration_id: str
    kind: str                              # "tcp" | "camera_extrinsic" | "camera_intrinsic" | "force_sensor" | ...
    artifact_sha256: str
    valid_until_iso8601: str | None        # wall-clock 有効期限（monotonic clock との関係 = §10 OPP-3）

@dataclass(frozen=True)
class GatewayConfigRef:
    config_id: str
    artifact_sha256: str

@dataclass(frozen=True)
class EscalationPolicy:                   # 05 の既定 disposition を SAFE_STOP 側へ強化するだけ（緩和は表現不能）
    on_no_chain: EscalationTarget          # 05 既定 = HOLD
    on_health_fail: EscalationTarget       # 05 既定 = HOLD
    retract_invalidates_lease: bool        # 05 §4.5 既定 = False（override のみ）。True = 強化
    force_limit_invalidates_lease: bool    # 同上
    clearance_roles: tuple[tuple[str, str], ...]   # (safehold_reason, role) — SAFETY / SAFE_STOP / CHECKPOINT_DISABLED / MANAGER_RESTART の解除に要する role（05 §5.4）

@dataclass(frozen=True)
class BindingExpectation:                 # 「この cell でこの skill を走らせる前提の binding 事実」— 等値検査の対象
    skill_action_id: str                   # certified のみ
    tensor_binding_hash: str | None        # LEARNED ⇔ 非 null
    control_mode: ControlMode              # frozen enum
    policy_rate_hz: CanonicalDecimal | None
    obs_sampling_rate_hz: CanonicalDecimal | None
    action_rate_hz: CanonicalDecimal | None
    hold: ActionHold | None                # frozen D1.1-B enum
```

### 2.2 top-level

```python
@dataclass(frozen=True)
class IndustrialDeploymentProfile:        # 新語（deployment 層のみ・凍結 schema 外）
    profile_schema_version: str            # "1.0"（既知版 allowlist・未知 = P_SCHEMA_VERSION_UNKNOWN）
    profile_label: str                     # 人間向け label（pin ではない — content sha で引く）
    cell: CellIdentity
    controller: ControllerEnvelope
    tool_payload: ToolPayloadSpec
    workspace: WorkspaceRestriction
    safety_restrictions: SafetyRestrictionSet
    initiation_strengthening: InitiationStrengthening
    freshness_strengthening: FreshnessStrengthening
    resource_availability: ResourceAvailability
    timeouts: RuntimeTimeouts
    health_checks: tuple[HealthCheckSpec, ...]
    calibration_refs: tuple[CalibrationRef, ...]
    gateway_config: GatewayConfigRef
    escalation: EscalationPolicy
    binding_expectations: tuple[BindingExpectation, ...]
    deployment_evidence_policy_hash: str   # §6 DeploymentEvidencePolicy の content hash
profile_hash = H_WCJ(IndustrialDeploymentProfile)   # 05 ActiveAuthorityLease.profile_hash / CommitPermit.profile_hash の実体
```

### 2.3 直列化と反循環

- 直列化 = frozen §2 WCJ（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:168` 以下）を適用し、D1.1-B が宣言した追加規約（`Optional None` は明示 `null`・`bool` を `int` として受理しない・tuple → array）を継承する（`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:24` 参照）。新 canonicalization 規則は足さない。
- **反循環**: profile は自身の `profile_hash`・lease id・`control_epoch`・`SkillActionId`・`ExecutionBundleHash` を内包しない（`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:23` と同型）。`binding_expectations[].skill_action_id` は**他者の** id であり自己参照ではない。`P_SELF_HASH`。
- codec は strict（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:385` と同じ 5 拒否）。`P_UNKNOWN_FIELD`。

## 3. 単調性規則（monotone strengthening）と機械検査

原則: profile が frozen の意味論に**触れられる面**を field 単位で列挙し、各面で「狭める方向しか表現できない」か「等値しか許さない」かを型と検査で固定する。**緩和を表現する field は存在しない**。

| frozen 面 | profile 側の field | 許される関係 | 機械検査（違反 code） |
|---|---|---|---|
| policy action space の `bounds`（`:138`, `:52`, `:81`） | **無し**（INTRINSIC 項は `tensor_binding_hash` 参照のみ） | 触れない | profile に action-space bounds を表す field が現れたら `P_INTRINSIC_OVERRIDE`（codec = unknown field） |
| `action_scale`（`:133`）/ transform 適用順（`:65-66`） | 無し | 触れない | 同上 |
| `policy_rate_hz` / `obs_sampling_rate_hz`（`:97-98`）/ `action_rate_hz`（`:126`）/ `hold`（`:127`） | `BindingExpectation.{…}` | **等値**（`==` TensorBindingSpec の値） | `P_RATE_MISMATCH` / `P_HOLD_MISMATCH` |
| `control_mode`（`:132`） | `BindingExpectation.control_mode` | **等値** | `P_CONTROL_MODE_MISMATCH` |
| `tensor_binding_hash`（`:185` bump = identity） | `BindingExpectation.tensor_binding_hash` | **等値**（ExecutionBundle.tensor_binding.artifact_hash と） | `P_BINDING_HASH_MISMATCH` |
| `InitiationSpec`（`:151`）・claim target `INITIATION_SPEC`（EP `:101`） | `InitiationStrengthening.conjuncts` | **AND 追加のみ**（frozen predicate は不変・評価は runtime 側 conjunct） | conjunct が frozen `ExprKind` 外・置換/OR/NOT を含む ⇒ `P_INITIATION_RELAXED`（型上 表現不能 + codec 拒否） |
| `FreshnessPolicy.max_staleness_s`（`:151`, `:146`） | `FreshnessStrengthening.max_staleness_s` | **stricter-or-equal**: frozen 有限 `f` に対し `p ≤ f`；frozen `None` に対し `p` 有限 = 強化・`None` = 強化なし | `p > f` ⇒ `P_FRESHNESS_RELAXED`。順序の `None` 扱いは本 doc の宣言（frozen は規定せず — 05 OP-16） |
| `required_control_resources`（`:142`）/ required ⊆ offered（`:380`） | `ResourceAvailability.control` | offered 集合の**宣言**（frozen 検査は不変）。cell が持たない資源を offered と宣言する = 事実誤り | `attested_by` 空 ⇒ `P_RESOURCE_UNATTESTED`（CELL_COMMISSIONING evidence 必須） |
| `fail_closed_action`（`:147`）/ 05 既定 disposition | `EscalationPolicy` | **SAFE_STOP 側へのみ**（HOLD → SAFE_STOP 可・逆不可）。invalidation は False → True のみ | HOLD への緩和は型上 表現不能（EscalationTarget に「NONE」「CONTINUE」が無い） |
| D0 §F safety 優先（`:319`） | `SafetyRestrictionSet.requires_safety_layer_health` | **True 必須** | `P_SAFETY_LAYER_NOT_REQUIRED` |
| boundary = TERMINAL のみ（BCS `:59`） | 無し | 触れない | checkpoint 切替を有効化する field は無い（05 §6.1） |
| composition（`ParallelRegion` / arity / dual-arm） | 無し | 触れない | 合成語彙の混入 ⇒ `P_COMPOSITION_CONTENT`（§7） |

追加の構造検査:

| 検査 | 違反 code |
|---|---|
| 全 `RuntimeTimeouts` > 0・有限 | `P_TIMEOUT_NONPOSITIVE` |
| `command_deadline_s ≥ 1 / action_rate_hz`（LEARNED の各 expectation） | `P_DEADLINE_BELOW_PERIOD` |
| `health_checks` に `SAFETY_LAYER_HEARTBEAT`・`CONTROLLER_LIVENESS`・`ENVELOPE_READBACK` の 3 kind が各 ≥ 1（stage は BOTH 推奨・BEFORE_PERMIT 必須） | `P_HEALTHCHECK_MISSING` |
| 全 `HealthCheckSpec.fail_closed == True` | `P_HEALTHCHECK_FAIL_OPEN` |
| `calibration_refs` の必須 kind（`tcp` + belief を担う camera 系）が存在し、`valid_until` が評価時刻より後 | `P_CALIBRATION_MISSING` / `P_CALIBRATION_EXPIRED` |
| `deployment_evidence_policy_hash` が解決でき、§6 の required kinds が profile_hash に対し存在 | `P_EVIDENCE_UNBOUND` |
| `ControllerEnvelope` の tuple 長 = `robot_model_ref` の関節数 | `P_ENVELOPE_SHAPE` |
| AcceptedEnvelope 静的充足可能性（§4） | `P_ENVELOPE_EMPTY` |
| `binding_expectations` の `skill_action_id` が certified（certificate 存在） | `P_EXPECTATION_UNCERTIFIED` |
| 反循環 / 未知 field / 版 | `P_SELF_HASH` / `P_UNKNOWN_FIELD` / `P_SCHEMA_VERSION_UNKNOWN` |

**「広げる」試みの網羅（反証の型）**: profile が frozen より緩い挙動を引き起こす経路は (i) action-space bounds を緩める — field が無い、(ii) 周波数・hold・control_mode を変える — 等値検査、(iii) initiation を緩める — AND のみ、(iv) 鮮度を緩める — `p ≤ f`、(v) 資源を偽って offered にする — attestation 必須（事実の検査は evidence 側）、(vi) 安全層を不要にする — True 必須、(vii) disposition を緩める — enum に緩和値が無い、(viii) boundary を checkpoint 化する — field が無い、(ix) unknown field で抜け道を作る — strict codec。**(v) だけは契約層では真偽を判定できない**（cell の物理事実）ため、`DeploymentEvidencePolicy` の CELL_COMMISSIONING に委ねる（honest scope・§10 OPP-5）。

## 4. `AcceptedEnvelope` の供給（05 §4.3 の連言に対する本 doc の項）

```text
AcceptedEnvelope(lease) = ⋀ { INTRINSIC_D11B(tensor_binding_hash)   … policy action space（bounds / action_scale / transform 順）— D1.1-B、写さない
                            , CONTROLLER(profile.controller)          … joint space（velocity / acceleration / jerk / force / torque）
                            , DEPLOYMENT_WORKSPACE(profile.workspace) … workspace（keep-out / reach / height）
                            , SAFETY_RESTRICTION(profile.safety_restrictions) … gateway predicate（静的）}
```

- handoff 決定 B の「∩」は、各項を**自分の空間**で評価した連言と読む（05 R6）。異なる空間の集合を literal に交差させる演算は定義しない。
- 空 / 充足不能（例: keep-out が到達領域を全て覆う、`ee_speed_max = 0`）= **fail-closed**: 静的検査 `P_ENVELOPE_EMPTY`（profile 受理時）と runtime `R_ENVELOPE_EMPTY`（05 CAS 前提 7）の二重化。静的検査は「明らかな不能」の検出であり充足可能性の完全判定ではない（§10 OPP-2）。
- 単位・frame: profile 項は SI（rad, m, s, N, N·m）。D1.1-B の `unit` / `frame`（`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:75-76`）とは空間が異なるため、変換は gateway が FK / 逆写像で行い、変換不能 = 拒否（05 §4.3「評価不能 = FALSE」）。
- SCRIPTED / WAIT skill（`tensor_binding_hash = null`）では INTRINSIC 項が欠け、profile 3 項のみ（05 OP-2）。profile はこれを埋めない（intrinsic 宣言は future static candidate）。

## 5. Lease 束縛

- `ActiveAuthorityLease.profile_hash`（05 §4.1）= 本 doc の `profile_hash`。`CommitPermit.profile_hash` と等値（05 §3.5 前提 6 の inputs 束縛）。
- **profile 変更 = 新 lease**: profile を「更新」する操作は存在しない。新 profile（新 hash）は 05 の完全経路（ReadinessAck → CommitPermit → AuthorityCas）で新 lease に束縛される。活性 lease の profile を in-place で差し替える経路は無い（05 §4.1 束縛規則）。
- lease へ写される profile 由来の値: `TimingBinding.{ack_timeout_s, permit_ttl_s, health_confirm_timeout_s, command_deadline_s, manager_liveness_s}` ← `RuntimeTimeouts`；`TimingBinding.runtime_max_staleness_s` ← `min(frozen FreshnessPolicy.max_staleness_s, FreshnessStrengthening.max_staleness_s)`（None 規則は §3）；`AcceptedEnvelope.terms` の 3 項 ← §4；`HealthConfirmation.profile_health_checks` ← `health_checks`（stage ∈ {AT_HEALTH_CONFIRMATION, BOTH}）；`lease.ownership`（SAFEHOLD 起動時）← `ResourceAvailability`。
- lease 活性中に profile の前提が崩れた場合（calibration 期限切れ・health check 失敗・evidence 失効）は profile 側の「更新」ではなく **lease 無効化**（05 §4.5 → `R_LEASE_INVALIDATED` / `R_HEALTH_CONFIRM_FAILED`）→ SAFEHOLD → 新 profile での新 lease。
- SHADOW_NON_AUTHORITY lease でも profile は同じ規則で束縛される（05 §4.4「他段は同一」）。deployment evidence の required kinds は mode 別（§6）。

## 6. Deployment evidence（`DeploymentEvidencePolicy` — EP v1.9 の外）

### 6.1 型

```python
class DeploymentEvidenceKind(Enum):       # 新語。EP v1.9 の ComponentKind / ProofKind / claim_target のいずれとも名前を共有しない
    CELL_COMMISSIONING | CONTROLLER_ENVELOPE_MEASUREMENT | TOOL_PAYLOAD_IDENTIFICATION | CALIBRATION_RECORD |
    GATEWAY_CONFIG_ATTESTATION | SAFETY_LAYER_ACCEPTANCE | HEALTH_CHECK_RUN | FAULT_INJECTION_RESULT

@dataclass(frozen=True)
class DeploymentEvidenceRecord:
    record_id: str
    kind: DeploymentEvidenceKind
    profile_hash: str                      # どの profile についての evidence か（束縛）
    subject_ref: str                       # cell_id / controller_firmware_ref / tool_id / calibration_id / config_id / check_id / fault code
    artifact_ref: str
    artifact_sha256: str
    measured_at_iso8601: str               # wall-clock（deployment evidence は暦時刻で失効する）
    operator_ref: str
    valid_until_iso8601: str | None

@dataclass(frozen=True)
class FaultInjectionRequirement:
    runtime_fault_code: str                # 05 RuntimeFaultCode の名（例: R_EPOCH_STALE_COMMAND）
    must_be_exercised_before: LeaseMode    # 05 LeaseMode（SHADOW_NON_AUTHORITY / CLOSED_LOOP_AUTHORITY）

@dataclass(frozen=True)
class DeploymentEvidencePolicy:
    policy_schema_version: str             # "1.0"
    required_before_shadow_lease: tuple[DeploymentEvidenceKind, ...]      # 最低 = CELL_COMMISSIONING, GATEWAY_CONFIG_ATTESTATION, SAFETY_LAYER_ACCEPTANCE
    required_before_closed_loop_lease: tuple[DeploymentEvidenceKind, ...] # 上記 + CONTROLLER_ENVELOPE_MEASUREMENT, TOOL_PAYLOAD_IDENTIFICATION, CALIBRATION_RECORD, HEALTH_CHECK_RUN, FAULT_INJECTION_RESULT
    fault_injection: tuple[FaultInjectionRequirement, ...]               # 最低 = R_EPOCH_STALE_COMMAND / R_OFFER_REUSED / R_PERMIT_REUSED / R_SAFETY_OVERRIDE / R_HEALTH_CONFIRM_FAILED / R_EXECUTOR_LOST を CLOSED_LOOP_AUTHORITY 前に
    validity_rule: str                     # "all required records valid at permit issue time"
deployment_evidence_policy_hash = H_WCJ(DeploymentEvidencePolicy)
```

### 6.2 EP v1.9 との関係（= 無関係であることの明示）

- 本 policy は EP の `claim_targets`（13）/ `ProofKind`（15）/ grade（5）/ `profiles` のいずれにも項目を足さず、`evidence_policy_definition_hash`（`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:163`）は不変（04 参照）。
- EP md / JSON に `controller` / `calibrat` / `deploy` / `inject` / `cell` の語彙は無い（critic 報告 §3.7 の grep 結果）ため、deployment evidence は**構造的に EP の外**である。
- grade 語（EXACT_TRAIN_TIME 等）を deployment evidence に使わない。deployment evidence は「存在・有効期限・束縛」だけを持ち、skill の certification に影響しない（certificate は runtime / deployment の事象で無効化されない — `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:39`）。
- `SAFETY_LAYER_ACCEPTANCE` の**内容**（機能安全の受入基準）は本 doc の外（§10 OPP-6）。本 doc は record の存在と束縛だけを要求する。

### 6.3 runtime audit との結線

- 05 `RuntimeAuditRecord` は runtime 事象（epoch / permit / lease / fault / disposition）を、本 doc の record は deployment 事実を持つ。両者は `profile_hash` と `lease_id` で join する（05 §8）。hash chain / 署名は 05 OP-5（U14 defer）に従う。

## 7. 合成（composition）の除外

- 旧 v0.1 の並行実行 profile は**削除**し、本 doc は合成（`SkillCompositionDefinition` / barrier / region postcondition / `ParallelRegion` の枝数 / DUAL-ARM 適合）を一切含まない。
- 根拠: 合成 schema delta = pX SKILL-DESIGN の court、`ParallelRegion` 枝数下限の supersede と DUAL-ARM 適合 = Rs 専権 OPEN（`$D/WMSO_RS_D11C_SCOPE_APPROVAL_CUSTODY_20260721.md:36-38`）；arity SUSPENDED は D1.1-B freeze と独立（`$D/WMSO_D11B_FREEZE_RECORD_20260721.md:39`）；SKILL の決定権 = pX（`$D/WMSO_RS_SKILL_OWNERSHIP_RULING_20260720.md:9`）。
- 機械検査: profile の直列化本文に合成語彙（`ParallelRegion` / `SkillCompositionDefinition` / `branch_count` / `barrier` / `region_postcondition` / `arity`）が現れたら `P_COMPOSITION_CONTENT`。
- 本 doc の `ResourceAvailability.control` が両腕の資源を True にすることは「cell に両腕がある」事実の宣言であり、2 executor の同時保持（合成）を許す意味ではない（05 §11 項 5: lease は常に 1 executor）。

## 8. Validation 規則・code 一覧・Test plan（設計時宣言 — impl CLOSED）

### 8.1 code 一覧（接頭辞 `P_`・frozen `E_*` / runtime `R_*` と衝突しない）

`P_INTRINSIC_OVERRIDE` / `P_RATE_MISMATCH` / `P_HOLD_MISMATCH` / `P_CONTROL_MODE_MISMATCH` / `P_BINDING_HASH_MISMATCH` / `P_INITIATION_RELAXED` / `P_FRESHNESS_RELAXED` / `P_RESOURCE_UNATTESTED` / `P_SAFETY_LAYER_NOT_REQUIRED` / `P_COMPOSITION_CONTENT` / `P_TIMEOUT_NONPOSITIVE` / `P_DEADLINE_BELOW_PERIOD` / `P_HEALTHCHECK_MISSING` / `P_HEALTHCHECK_FAIL_OPEN` / `P_CALIBRATION_MISSING` / `P_CALIBRATION_EXPIRED` / `P_EVIDENCE_UNBOUND` / `P_ENVELOPE_SHAPE` / `P_ENVELOPE_EMPTY` / `P_EXPECTATION_UNCERTIFIED` / `P_SELF_HASH` / `P_UNKNOWN_FIELD` / `P_SCHEMA_VERSION_UNKNOWN`

規則: (1) 全検査は fail-closed（評価不能 = 違反）。(2) profile の受理（`profile_hash` の登録）は全 `P_*` = 0 が前提。(3) 受理後の事実変化（期限切れ・evidence 失効）は profile を変えず lease を無効化する（§5）。(4) `P_*` は certificate・EP grade・`SkillDefinitionHash` のいずれにも影響しない。

### 8.2 Test plan

| id | 試験 | 期待 |
|---|---|---|
| PT-01 | `BindingExpectation.action_rate_hz` を TensorBindingSpec より小さく（「narrow」）宣言 | `P_RATE_MISMATCH`（等値のみ） |
| PT-02 | `hold` を ZERO_ORDER_HOLD → LINEAR_INTERPOLATE に変更 | `P_HOLD_MISMATCH` |
| PT-03 | conjunct に OR 相当 / frozen `ExprKind` 外の kind を注入 | codec 拒否 + `P_INITIATION_RELAXED` |
| PT-04 | frozen `max_staleness_s = 0.5` に対し profile `1.0` | `P_FRESHNESS_RELAXED`；`0.2` は受理；frozen None に対し `0.2` は受理（強化） |
| PT-05 | unknown field `action_bounds` を profile に追加 | `P_UNKNOWN_FIELD`（strict codec）— INTRINSIC override の唯一の経路が閉じる |
| PT-06 | `requires_safety_layer_health = False` | `P_SAFETY_LAYER_NOT_REQUIRED` |
| PT-07 | `EscalationPolicy.on_no_chain` に HOLD より緩い値を与えようとする | 型上 表現不能（enum に無い）— negative control は codec 拒否 |
| PT-08 | keep-out が全到達域を覆う profile | `P_ENVELOPE_EMPTY` |
| PT-09 | `attested_by` 空の `ResourceAvailability` | `P_RESOURCE_UNATTESTED` |
| PT-10 | `deployment_evidence_policy_hash` 未解決 / required kind 欠落 | `P_EVIDENCE_UNBOUND` |
| PT-11 | profile 本文に `ParallelRegion` を含める | `P_COMPOSITION_CONTENT` |
| PT-12 | profile が自身の hash を field に持つ | `P_SELF_HASH` |
| PT-13 | 受理済 profile の calibration が失効 | profile 不変・活性 lease は無効化（05 `R_LEASE_INVALIDATED`）・新 lease は `P_CALIBRATION_EXPIRED` で不成立 |
| PT-14 | 同一 cell で profile A → B へ切替 | in-place 更新経路なし。B の lease は 05 完全経路（新 epoch）でのみ成立 |
| PT-15 | golden profile 2 本の `profile_hash` 再現（WCJ + B-declared 規約） | byte 同一・hash 一致（fixture は impl 解錠後に bank） |

## 9. 主張しないこと（境界）

1. **authority**: profile は authority を付与しない。`CLOSED_LOOP_AUTHORITY` lease の必要条件（frozen `granted == True`・EP `usage_ceiling.closed_loop_authority` の conjuncts `$D/WMSO_EvidencePolicy_v1.9.json:213`）に profile 由来の条件を**足す**だけで、外すことは無い。
2. **impl**: code / fixture / 実行を含まない（§8 は宣言のみ）。
3. **schema delta**: frozen 4 file を編集せず、`SkillDefinition` / `ExecutionBundle` / `TensorBindingSpec` / EP `policy_definition` に field を足さない。frozen enum に member を足さない（`ExprKind` / `ControlMode` / `ActionHold` は参照のみ）。
4. **execution profile 軸**: boundary-only / real-time の裁定は Rs（`$D/WMSO_RS_C3_RULING_SLICE_PROFILE_20260720.md:65`）。本 doc は timeout の**器**を与えるだけで real-time 主張をしない。
5. **EP evidence profile**: SHADOW / CLOSED_LOOP / OFFLINE_REPLAY の意味・required set・min_grade に触れない。`requested_profile` の評価は frozen eligibility（EP `:154`）。
6. **composition**: §7。
7. **機能安全の内容**: `SafetyRestrictionSet` / `SAFETY_LAYER_ACCEPTANCE` / `StopClass` の**物理的・規格的内容**は本 doc の外（IndependentSafetyLayer と cell の安全設計の court）。本 doc は「存在・束縛・fail-closed」を要求するのみ。
8. **skill-specific safe-hold 保証 / intrinsic envelope の静的宣言（SCRIPTED / WAIT）**: future static candidate（07）。
9. **freeze / two-key / gate PASS / Rs 承認**: いずれも主張しない。前 package（v0.1）の内容は handoff 決定以外を引き継がない。
10. **D1.1-C artifact manifest**: 未凍結（open-11 pending）。本 doc は manifest の field を参照しない。

## 10. Open points（⛔ open = 0 を宣言しない）

| id | open | 出所 / 依存 | 本 doc の扱い |
|---|---|---|---|
| OPP-1 | `FreshnessPolicy.max_staleness_s = None` との順序（None = 上限なし）は本 doc / 05 の宣言で frozen の規定ではない | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151`（型のみ） | §3 に loud 記録。frozen 側の確定 = 後継契約 or Rs |
| OPP-2 | `P_ENVELOPE_EMPTY` の静的判定は「明らかな不能」に限る（完全な充足可能性判定は幾何計算を要する） | §4 | runtime `R_ENVELOPE_EMPTY` と二重化 |
| OPP-3 | calibration / evidence の有効期限は wall-clock、runtime は monotonic clock（D0 §G）。両者の対応の取り方 | `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:354-355` | permit 発行時に wall-clock で評価し結果を lease に固定（以後は lease 無効化で扱う） |
| OPP-4 | `StopClass` の物理挙動・`SafeStop` の controller 固有実現 | 05 OP-4 | 種別のみ |
| OPP-5 | `ResourceAvailability` の真偽は契約層で判定不能（cell の物理事実） | §3 (v) | CELL_COMMISSIONING evidence に委ねる |
| OPP-6 | `SAFETY_LAYER_ACCEPTANCE` の受入基準の内容 | §6.2 | 外部 court |
| OPP-7 | **DDR#41**: `CellIdentity.robot_model_ref` は RS71 §0 の型式（UR15）と一致必須。凍結 v13 `:332` の 88 mm 引用の扱い（Rs 専権）に本 doc は依存しないが、robot_model_ref の照合先が動けば profile の受理条件が動く | `thread_isaac_lab/thread-vault/02-Workflow/HANDOFF_pQ_rstechlead2_wmso.md:11` | 照合先 = RS71（本 doc は値を書かない） |
| OPP-8 | profile の複数 skill への適用（`binding_expectations` が全 certified skill を列挙するか、cell 単位で 1 profile か） | §2.2 | 1 cell : n expectations を既定。運用形は slice 詳細 prereg |
| OPP-9 | `HealthCheckSpec.evaluator_ref` の登録・版管理（EP の evaluator registry を流用しない） | EP `evaluator_registry_rule` は certification 用 | 別 registry（名前空間を分ける）— 内容は impl 解錠後 |
| OPP-10 | 本 doc 自体の two-key・Rs 裁定 | — | 未 |

## 11. 版歴 / fold-map

- v0.1（前 package・別 sandbox・本 session では参照不能）→ **v0.2（本 doc・2026-09-03）**。起草 = 単独（judge panel は session 上限で未実施 — 08 の 3 軸レビューで補う）。
- handoff 決定 → 本 doc の節:

| 決定 | 内容 | 実装節 |
|---|---|---|
| 6 | profile・authority decision・初期化・envelope・timing を lease へ完全束縛 | §5（`profile_hash` = lease field・変更 = 新 lease） |
| 7 | deployment profile は frozen 意味論を狭めることだけ許可（monotone strengthening） | §3（面別の関係 + `P_*`）・§8 |
| 9 | `ParallelExecutionProfile` を産業プロファイルから 削除 し合成差分へ返却 | §7（`P_COMPOSITION_CONTENT`） |
| B | `IntrinsicExecutionLimits` 不採用 — intrinsic bounds・rate・hold は D1.1-B を hash 参照 | §1・§3 第 1-3 行・§4 INTRINSIC 項 |
| F | cell / controller / tool / calibration / gateway / fault injection は別 `DeploymentEvidencePolicy`（EP v1.9 不変） | §6 |
| D | initiation 制約 = profile による単調な強化のみ | §2.1 `InitiationStrengthening`（AND のみ）・§3 |

- **BRIEF 修正の反映（R1-R4）**: 制御周波数・hold・control_mode は**等値のみ**（brief 骨子の「rate ≤ / hold stricter-or-equal」は起草前に R1 で supersede — critic X3）／ 狭めてよい「rate limit」= `ControllerEnvelope` の運動学上限／ `AcceptedEnvelope` = 空間別評価の連言（R3）／ 語彙 = VOCABULARY.md（R4）。
- 旧 v0.1 の識別子: `ParallelExecutionProfile` 削除、`IntrinsicExecutionLimits` 不採用、`continuation_overlay_hash` / `recovery_overlay_hash` 削除（05 と同じ根拠）。

## 12. Review anchors

1. profile に policy action space の bounds を表す field が無く、INTRINSIC 項は `tensor_binding_hash` 参照のみ — §2.1・§3 第 1 行 ↔ `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:138`。
2. 制御周波数・hold・control_mode・binding hash は等値検査（`P_RATE_MISMATCH` 等）で、narrow を許さない — §3 ↔ `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:125-127`・`:132`・`:185`。
3. initiation 強化は frozen `InitiationSpec` を書き換えず AND 追加のみ（claim target 不変） — §2.1・§3 ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151`・`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:101`。
4. 鮮度は stricter-or-equal（`p ≤ f`）・None 規則は loud — §3 ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:146`。
5. offered 資源の宣言は frozen `required ⊆ offered` 検査を変えず、真偽は evidence に委ねる（honest scope） — §3 (v) ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:380`。
6. escalation は SAFE_STOP 側へのみ強化（緩和値が enum に無い） — §2.1 `EscalationPolicy`。
7. safety layer health は True 必須・live 決定は IndependentSafetyLayer — §2.1・§3 ↔ `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:319`。
8. AcceptedEnvelope = 空間別評価の連言、空 = fail-closed の二重化 — §4 ↔ 05 §4.3。
9. profile 変更 = 新 lease・in-place 更新経路なし — §5 ↔ 05 §4.1。
10. DeploymentEvidencePolicy は EP の claim_target / ProofKind / grade / profiles に何も足さず definition hash 不変 — §6.2 ↔ `$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:163`・`$D/WMSO_EvidencePolicy_v1.9.json:5`。
11. 合成 OUT（court と Rs 専権の根拠） — §7 ↔ `$D/WMSO_RS_D11C_SCOPE_APPROVAL_CUSTODY_20260721.md:36-38`・`$D/WMSO_D11B_FREEZE_RECORD_20260721.md:39`。
12. 3 軸（EP evidence / execution / deployment）の分離と execution 軸の非裁定 — §1.1・§9 項 4 ↔ `$D/WMSO_RS_C3_RULING_SLICE_PROFILE_20260720.md:5`・`:65`・`$D/WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md:13`。
13. 反循環・strict codec — §2.3 ↔ `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:23`・`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:385`。
14. boundary 種別・checkpoint 切替に触れる field が無い — §3 ↔ `$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59`。
15. 全 `P_*` は certificate / EP grade / `SkillDefinitionHash` に影響しない — §8.1 規則 (4) ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:39`。
16. 機械検査（`check_review_candidate.py`）= FAIL 0。C2 WARN（19 件）は heuristic で、いずれも「1 行に複数 locus を並べた表の行」か「frozen 行を型根拠として引き、同じ行で本 doc の新語（`P_*` / `profile_hash` 等）を導入した行」— 引用先の内容は起草時に sed で確認済み（§1 表・§3 表・§12）。
