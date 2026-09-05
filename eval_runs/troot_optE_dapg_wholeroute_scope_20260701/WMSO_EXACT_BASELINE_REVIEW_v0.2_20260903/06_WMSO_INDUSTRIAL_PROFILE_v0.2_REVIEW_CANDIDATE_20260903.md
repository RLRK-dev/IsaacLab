# WMSO `IndustrialDeploymentProfile` — DEPLOYMENT PROFILE SPEC (v0.2.5 REVIEW CANDIDATE)

- node: `T-WMSO`; 起草 = Claude Code web session（review candidate 起草・**authority 無し**・凍結物へ非接触）; 作成 = 2026-09-03 16:36 UTC（`date -u` 実測）／ v0.2.1 = 2026-09-04 01:51 UTC（file mtime 実測 01:51:18）／ v0.2.5 = 2026-09-05 01:33 UTC（`date -u` 実測）／ v0.2.4 = 2026-09-04 23:00 UTC（`date -u` 実測）／ v0.2.3 = 2026-09-04 20:47 UTC（`date -u` 実測）／ v0.2.2 = 2026-09-04 15:41 UTC（`date -u` 実測）
- status: **REVIEW CANDIDATE v0.2.5（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.4 → v0.2.5 = Rs 裁定 2026-09-04（GPT5.6sol 推奨を採用・`review_records/rs_consult/`） の反映（OPP-15 B+ / OPP-11 / OPP-13 / OP-19・§11）。旧版の系譜: — v0.2.3 → v0.2.4 = v0.2.3 本文への再レビュー round（R1 / R2 → V1 / V2）の確定 finding の fold（§11）。旧版の系譜: — v0.2 → v0.2.1 = 陽性対照レビュー fold ／ v0.2.1 → v0.2.2 = 3 軸レビュー（A / A2 / B / B2）fold（起草者再検証のみ）／ v0.2.2 → v0.2.3 = 独立 verifier verdict 反映 + 残差 + 軸 C（reviewer C は v0.2.2 を対象・verifier C）fold（§11・全体 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`）。verdict は AI verifier のもので human two-key ではない
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
| `validate_invocation_start(…, now)` = initiation predicate / freshness_policy 評価 / required ⊆ offered | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:372-373`、`:380` | frozen 検査は不変。profile の強化は **runtime が別 conjunct として評価**（05 v0.2.1 §6.2 B4 に明示・偽 = `R_PROFILE_INITIATION_FAILED`） |
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
class HealthCheckKind(Enum):      CONTROLLER_LIVENESS | SAFETY_LAYER_HEARTBEAT | CALIBRATION_VALID | TOOL_IDENTITY | GATEWAY_CONFIG_MATCH | ENVELOPE_READBACK | CONTROLLER_IDENTITY | SAFETY_LAYER_IDENTITY
#   v0.2.4（R2-09）: SAFETY_LAYER_IDENTITY = IndependentSafetyLayer が報告する version / build と CellIdentity.safety_layer_ref の等値（heartbeat ≠ identity）
#   v0.2.3（CD-09）: CONTROLLER_IDENTITY = 各 arm の controller が報告する serial / firmware と `arms[].{robot_serial_ref, controller_firmware_ref}` の等値（LIVENESS ≠ identity・arm ごとに評価・v0.2.4 R2-04）。ENVELOPE_READBACK = 各 arm の controller 側に設定された運動学上限の readback と `arms[].controller` の等値（executor 側 envelope readback = 05 §3.3 とは別）
class HealthCheckStage(Enum):     BEFORE_PERMIT | AT_HEALTH_CONFIRMATION | BOTH
class EscalationTarget(Enum):     HOLD | SAFE_STOP                              # 05 §7 の disposition 名を再利用（SAFE_STOP 側へのみ強化）
class CalibrationKind(Enum):      TCP | CAMERA_EXTRINSIC | CAMERA_INTRINSIC | FORCE_SENSOR   # v0.2.3（CD-08）: 閉じた enum（自由文字列を廃止・未知 = codec 拒否）
class ZoneKind(Enum):             KEEP_OUT | REACH_LIMIT | HEIGHT_BAND                       # v0.2.3（CD-08）
# 評価空間は型で固定（v0.2.3・CD-08）: ControllerEnvelope = joint space、WorkspaceRestriction = workspace（05 §4.3）。自由文字列 field `representation` は削除

@dataclass(frozen=True)
class CellIdentity:
    cell_id: str
    site_id: str
    robot_model_ref: str                   # RS71 §0 の型式（UR15）と一致必須（不一致 = P_ROBOT_MODEL_MISMATCH・v0.2.1）— DDR#41 の曝露点（§10 OPP-7）。全 arm 共通
    base_frame_ref: str                    # v0.2.1（C-11）: 空間項（workspace / tool CoM / envelope）の基準 frame。全 spatial field はこの frame か tool_flange で表す
    kinematic_layout: CellKinematicLayoutRef  # v0.2.5（OPP-15 B+・Rs 裁定）: 両 arm の base transform（base_frame_ref 基準・RS71 §0 の固定 base Y = ∓0.35 を含む）・robot instance 対応・共有 collision model を content-addressed に束縛
    arms: tuple[ArmSpec, ...]              # v0.2.4（R2-04）: DUAL-ARM cell（RS71 §0 不変前提）を表現できるよう arm 単位に識別・envelope・tool・TCP を持つ（旧 robot_serial_ref / controller_firmware_ref / controller / tool_payload は ArmSpec へ移設）
    safety_layer_ref: str                  # v0.2.4（R2-09）: IndependentSafetyLayer の identity（version / build）— SAFETY_LAYER_ACCEPTANCE.subject_ref と SAFETY_LAYER_IDENTITY health check の照合先
    layout_revision_ref: str               # cell layout の版（keep-out の前提）

@dataclass(frozen=True)
class ArmSpec:                             # v0.2.4（R2-04）: 1 arm = frozen ControlResourceSpec の key 1 つ
    resource_id: str                       # "ee_left" | "ee_right"（frozen ControlResourceSpec の key・$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:142）。arms 内で一意
    robot_serial_ref: str
    controller_firmware_ref: str
    controller: ControllerEnvelope         # この arm の運動学上限（関節数 = robot_model_ref）
    base_transform_id: str                 # v0.2.5（OPP-15 B+）: kinematic_layout artifact 内の当該 arm の base transform entry（未解決 = P_ARM_BASE_UNBOUND）
    gripper_resource_id: str               # v0.2.5（OPP-15 B+）: "gripper_left" | "gripper_right"（frozen key）— arm と gripper の対応を一意化（P_ARM_COVERAGE）
    tool_payload: ToolPayloadSpec          # この arm の tool（gripper_* 資源に対応）。TCP は tool_payload.tcp_offset_ref（arm ごとに kind = TCP の calibration_refs entry・P_TCP_REF_UNRESOLVED）

@dataclass(frozen=True)
class CellKinematicLayoutRef:              # v0.2.5（OPP-15 B+）: 外部 artifact（content-addressed）。中身 = {resource_id → T_cell←base}・robot instance 対応・共有 collision model の ref + sha
    layout_id: str
    artifact_sha256: str                   # 05 §3.4 (j) の照合対象（差し替え = R_PROFILE_MISBOUND）

@dataclass(frozen=True)
class InterArmRestrictionSet:              # v0.2.5（OPP-15 B+）: arm 間の静的相互制約（単項の WorkspaceRestriction とは分離）
    min_separation_m: CanonicalDecimal     # > 0（P_INTER_ARM_RESTRICTION_MISSING）
    pairwise_keepout_refs: tuple[str, ...] # 両 arm の相対状態に対する keep-out（content hash 付き）
    pairwise_keepout_sha256: tuple[str, ...]
    swept_volume_predicate_refs: tuple[str, ...]   # 提案線分の swept volume に対する拒否述語
    swept_volume_predicate_sha256: tuple[str, ...]
    # 評価 = 05 §4.3 INTER_ARM 項（両 arm の同一線形化 snapshot で連言評価）。動的干渉は IndependentSafetyLayer が独立監視（AND・代替ではない）

@dataclass(frozen=True)
class ControllerEnvelope:                  # 運動学・力学の上限（SI）。**制御周波数を含まない**（R1）
    joint_velocity_max: tuple[CanonicalDecimal, ...]        # [rad/s]・関節順は robot_model_ref の規約
    joint_acceleration_max: tuple[CanonicalDecimal, ...]    # [rad/s^2]
    joint_jerk_max: tuple[CanonicalDecimal, ...] | None     # [rad/s^3]
    ee_speed_max: CanonicalDecimal                          # [m/s]
    ee_force_max: CanonicalDecimal | None                   # [N]   — v0.2.3（CD-07）: **監視上限**（command から評価不能。IndependentSafetyLayer / controller が測定値で監視・admission 項 CONTROLLER には含めない）
    joint_torque_max: tuple[CanonicalDecimal, ...] | None   # [N·m] — 同上（監視上限）
    stop_class: StopClass

@dataclass(frozen=True)
class ToolPayloadSpec:
    tool_id: str
    tool_mass_kg: CanonicalDecimal
    tool_com_m: tuple[CanonicalDecimal, CanonicalDecimal, CanonicalDecimal]   # frame = tool_flange（v0.2.1・C-11）
    payload_mass_max_kg: CanonicalDecimal
    tcp_offset_ref: str                    # == calibration_refs 内の kind = TCP の calibration_id（未解決 = P_TCP_REF_UNRESOLVED・v0.2.3 CD-04）— 内容は artifact_sha256 で束縛

@dataclass(frozen=True)
class ZoneRef:
    zone_id: str
    geometry_sha256: str                   # zone 幾何（外部 artifact）の content hash
    kind: ZoneKind                         # v0.2.3（CD-08）: 閉じた enum
    frame_ref: str                         # v0.2.1（C-11）: == CellIdentity.base_frame_ref（不一致 = P_FRAME_MISMATCH）

@dataclass(frozen=True)
class WorkspaceRestriction:
    zones: tuple[ZoneRef, ...]             # 追加の制約のみ（許可領域の拡張は表現不能 — §3）
    frame_ref: str                         # v0.2.1（C-11）: == CellIdentity.base_frame_ref（gateway の FK 変換の目標 frame）。v0.2.4（R2-13）: default 無し（欠落 = codec 拒否）

@dataclass(frozen=True)
class SafetyRestrictionSet:               # 静的 restriction（gateway predicate）。live 決定は IndependentSafetyLayer
    restriction_ids: tuple[str, ...]
    predicate_refs: tuple[str, ...]        # 各 predicate は「拒否条件」のみを表現する（許可条件は表現不能）
    predicate_sha256: tuple[str, ...]      # v0.2.3（CD-04）: predicate_refs と同長・解決内容の content hash（登録時 + 第 2 評価点で照合、gateway は評価前に再検証・不一致 = FALSE）
    requires_safety_layer_health: bool     # **True 必須**（P_SAFETY_LAYER_NOT_REQUIRED）。v0.2.3（CD-14）: 明示宣言（省略時 default を持たせない）— False = 登録拒否・欠落 = codec 拒否

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
    # v0.2.1（C-08）: 旧 attested_by（record_id を profile preimage に置く）は 削除 — evidence → profile の一方向束縛のみ（record が profile_hash を持つ）。
    #   P_RESOURCE_UNATTESTED は登録時に evidence store（kind = CELL_COMMISSIONING ∧ record.profile_hash == 本 profile の hash）を照会して判定する

@dataclass(frozen=True)
class RuntimeTimeouts:                    # 05 TimingBinding へ写される（05 INV-22: 数値は profile 由来）
    ack_validity_s: CanonicalDecimal       # v0.2.1（C-12 / B-11）: ReadinessAck.valid_until の窓（05 TimingBinding.ack_validity_s）
    ack_timeout_s: CanonicalDecimal
    permit_ttl_s: CanonicalDecimal
    health_confirm_timeout_s: CanonicalDecimal
    command_deadline_s: CanonicalDecimal   # LEARNED では ≥ 1 / action_rate_hz（05 §4.1）
    manager_liveness_s: CanonicalDecimal
    safety_heartbeat_timeout_s: CanonicalDecimal   # v0.2.2（B2-01 / B-H3）: IndependentSafetyLayer heartbeat 欠落の上限（05 TimingBinding 同名 field・超過 = 05 §5.2 (i′) SafeStop + R_SAFETY_LAYER_LOST）
    decision_max_age_s: CanonicalDecimal           # v0.2.2（A-01 / B2-14）: permit 発行時に AuthorityDecision に許す最大 age（05 §3.4 (e)）
    boundary_dwell_s: CanonicalDecimal             # v0.2.2（B-M9）: S_BOUNDARY_WAIT 滞留の上限（超過 = 05 R_BOUNDARY_DWELL_EXCEEDED → NO_CHAIN 経路）
    max_reselect_attempts: int                     # v0.2.2（B-M9）: 1 boundary あたりの候補試行上限（≥ 1）
    command_kind_mismatch_max: int                 # v0.2.2（B2-15）: 連続 R_COMMAND_KIND_MISMATCH の許容回数（≥ 1・超過 = TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION)）
    inter_command_jitter_s: CanonicalDecimal       # v0.2.2（B-L2 / B2-13）: 連続 command 間隔の許容偏差（超過 = 05 R_TIMING_VIOLATION）
    lease_max_duration_s: CanonicalDecimal         # v0.2.3（CD-10）: lease 活性時間の上限（WAIT / TIMEOUT 非宣言 skill でも lease を有限にする・超過 = 05 R_LEASE_DURATION_EXCEEDED）

@dataclass(frozen=True)
class HealthCheckSpec:
    check_id: str
    kind: HealthCheckKind
    evaluator_ref: str
    evaluator_sha256: str                  # v0.2.3（CD-04）: evaluator 内容の content hash（第 2 評価点で照合・不一致 = R_PROFILE_MISBOUND）。v0.2.4（R2-17）: 各実行の直前にも再検証し、不一致 = check FAILED（fail_closed）
    stage: HealthCheckStage
    fail_closed: bool                      # **True 必須**（v0.2.3・CD-14: knob ではなく明示宣言。省略時 default を持たせないための field で、False は登録拒否・欠落は codec 拒否）

@dataclass(frozen=True)
class CalibrationRef:
    calibration_id: str
    kind: CalibrationKind                  # v0.2.3（CD-08）: 閉じた enum
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
    clearance_roles: tuple[tuple[str, str], ...]   # (safehold_reason, role) — SAFETY / SAFE_STOP / CHECKPOINT_DISABLED / MANAGER_RESTART / GATEWAY_RESTART の解除、および GENESIS（05 §3.2 genesis record の権限・v0.2.4 R2-15）に要する **追加の** role（05 §5.4）。v0.2.3（CD-02）→ v0.2.4（R1-04 / R2-05）: {SAFETY, SAFE_STOP, CHECKPOINT_DISABLED, MANAGER_RESTART, GATEWAY_RESTART}（+ GENESIS・R2-15） の各 reason に ≥ 1 role が必須（P_CLEARANCE_ROLE_MISSING — 05 §5.4 条件 10 の集合と同一。SAFETY の role は ISL clearance record と AND）— 未定義 = 解除不能でも任意解除でもない。v0.2.1（C-13）: IndependentSafetyLayer の clearance record・durable 整合検査の**代替ではない**（常に AND）

@dataclass(frozen=True)
class BindingExpectation:                 # 「この cell でこの skill を走らせる前提の binding 事実」— 等値検査の対象。v0.2.1（C-19）: LEARNED では値は tensor_binding_hash から導出される readback（第 2 の source ではない）・SCRIPTED / WAIT では timing 値を持たない（None・v0.2.3 CD-05）。lease 成立には当該 skill の expectation が存在すること（05 §3.4 (g)）
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
    profile_label: str                     # 人間向け label。hash preimage に**入る**（label 変更 = 新 profile_hash = identity event・evidence 再取得が要る）。preimage からの射影は §2.3「新 canonicalization 規則を足さない」と衝突するため OPP-12（v0.2.3・CD-15）
    cell: CellIdentity                     # v0.2.4（R2-04）: controller / tool_payload は cell.arms[] へ移設
    workspace: WorkspaceRestriction
    inter_arm_restrictions: InterArmRestrictionSet   # v0.2.5（OPP-15 B+）
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
- **反循環（v0.2.2・A-06 / A2-09 で構造 pattern に揃えた）**: profile は **自身から導かれる hash**（`profile_hash`・その部分 hash）と、「自身と同一である」ことを主張する任意の hash、および `profile_hash` を preimage に持つ runtime 値（lease id・`control_epoch`・permit id）を preimage に置かない（`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:23` の構造 pattern「自己参照 hash を preimage に置かない」と同型）。`profile_hash` は `SkillActionId` / `ExecutionBundleHash` / `tensor_binding_hash` の preimage に入らない（03 matrix C03）ため、`binding_expectations[].skill_action_id` / `tensor_binding_hash` のような**他 artifact の静的 id の参照**は自己参照ではなく許される。検出 = `P_SELF_HASH`（前者の列挙に対する検査）。
- codec は strict（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:385` と同じ 5 拒否）。`P_UNKNOWN_FIELD`。

## 3. 単調性規則（monotone strengthening）と機械検査

原則: profile が frozen の意味論に**触れられる面**を field 単位で列挙し、各面で「狭める方向しか表現できない」か「等値しか許さない」かを型と検査で固定する。**緩和を表現する field は存在しない**。

| frozen 面 | profile 側の field | 許される関係 | 機械検査（違反 code） |
|---|---|---|---|
| policy action space の `bounds`（`:138`, `:52`, `:81`） | **無し**（INTRINSIC 項は `tensor_binding_hash` 参照のみ） | 触れない | profile に action-space bounds を表す field が現れたら strict codec が `P_UNKNOWN_FIELD`（PT-05）。`P_INTRINSIC_OVERRIDE` = null-binding expectation（SCRIPTED / WAIT）に非 null の timing 値がある場合（v0.2.3・CD-05 / CD-14 で再定義） |
| `action_scale`（`:133`）/ transform 適用順（`:65-66`） | 無し | 触れない | 同上 |
| `policy_rate_hz` / `obs_sampling_rate_hz`（`:97-98`）/ `action_rate_hz`（`:126`）/ `hold`（`:127`） | `BindingExpectation.{…}` | **等値**（`==` TensorBindingSpec の値）。評価は `tensor_binding_hash ≠ null` のときのみ；null（SCRIPTED / WAIT・TensorBindingSpec が存在しない `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:289`）では timing 4 field は None 必須（非 null = `P_INTRINSIC_OVERRIDE`）・SCRIPTED の timing 執行は 05 `command_deadline_s` のみ（v0.2.3・CD-05） | `P_RATE_MISMATCH` / `P_HOLD_MISMATCH` |
| `control_mode`（`:132`） | `BindingExpectation.control_mode` | **等値** | `P_CONTROL_MODE_MISMATCH` |
| `tensor_binding_hash`（`:185` bump = identity） | `BindingExpectation.tensor_binding_hash` | **等値**（ExecutionBundle.tensor_binding.artifact_hash と） | `P_BINDING_HASH_MISMATCH` |
| `InitiationSpec`（`:151`）・claim target `INITIATION_SPEC`（EP `:101`） | `InitiationStrengthening.conjuncts` | **AND 追加のみ**（frozen predicate は不変・評価は runtime 側 conjunct） | conjunct が frozen `ExprKind` 外・置換/OR/NOT を含む ⇒ `P_INITIATION_RELAXED`（型上 表現不能 + codec 拒否） |
| `FreshnessPolicy.max_staleness_s`（`:151`, `:146`） | `FreshnessStrengthening.max_staleness_s` | **stricter-or-equal**: frozen 有限 `f` に対し `p ≤ f`；frozen `None` に対し `p` 有限 = 強化・`None` = 強化なし | `p > f` ⇒ `P_FRESHNESS_RELAXED`。順序の `None` 扱いは本 doc の宣言（frozen は規定せず — 05 OP-16） |
| `required_control_resources`（`:142`）/ required ⊆ offered（`:380`） | `ResourceAvailability.control` | offered 集合の**宣言**（frozen 検査は不変）。cell が持たない資源を offered と宣言する = 事実誤り。全 lease の `ownership.control` ⊆ 本宣言（chained handoff の offer も・05 §3.4 (h)・v0.2.3 CD-06） | evidence store に `kind = CELL_COMMISSIONING` ∧ `record.profile_hash == H_WCJ(profile)` の `DeploymentEvidenceRecord` が無い ⇒ `P_RESOURCE_UNATTESTED`（登録時・第 1 評価点・§2.1 注記と同一規則。v0.2.2 A2-03: 旧 cell は削除済 field `attested_by` を参照していた） |
| `fail_closed_action`（`:147`）/ 05 既定 disposition | `EscalationPolicy` | **SAFE_STOP 側へのみ**（HOLD → SAFE_STOP 可・逆不可）。invalidation は False → True のみ | HOLD への緩和は型上 表現不能（EscalationTarget に「NONE」「CONTINUE」が無い） |
| D0 §F safety 優先（`:319`） | `SafetyRestrictionSet.requires_safety_layer_health` | **True 必須** | `P_SAFETY_LAYER_NOT_REQUIRED` |
| boundary = TERMINAL のみ（BCS `:59`） | 無し | 触れない | checkpoint 切替を有効化する field は無い（05 §6.1） |
| composition（`ParallelRegion` / arity / dual-arm） | 無し | 触れない | 合成語彙の混入 ⇒ `P_COMPOSITION_CONTENT`（§7） |

追加の構造検査:

| 検査 | 違反 code |
|---|---|
| 全 `RuntimeTimeouts` field > 0・有限（`int` field は ≥ 1・v0.2.2） | `P_TIMEOUT_NONPOSITIVE` |
| `RuntimeTimeouts` の相対順序（v0.2.3・CD-01・v0.2.5 Rs 裁定 2026-09-04（GPT5.6sol 推奨を採用・`review_records/rs_consult/`））: `safety_heartbeat_timeout_s ≤ command_deadline_s`；`inter_command_jitter_s < 1 / action_rate_hz`（LEARNED expectation ごと）；`decision_max_age_s` は順序ではなく 05 `effective_expires_at` と CAS 条件 6 で扱う（旧 `≤ permit_ttl_s` は撤回 — 発行時有効・消費時失効の穴）；`permit_ttl_s ≤ boundary_dwell_s`；`ack_validity_s ≤ boundary_dwell_s`；`ack_timeout_s ≤ boundary_dwell_s`；`max_reselect_attempts × worst_case_attempt_s + selector_overhead_s ≤ boundary_dwell_s`（worst_case / overhead は timing baseline の値）；`health_confirm_timeout_s < lease_max_duration_s`（同時満了を避ける）；`lease_max_duration_s ≥ boundary_dwell_s`；`manager_liveness_s ≤ command_deadline_s` | `P_TIMEOUT_ORDER` |
| 各 `RuntimeTimeouts` 値 ≤ `CellSafetyTimingBaseline.approved_ceiling[field]`（baseline = acceptance record の `timing_baseline_hash` が指す content-addressed artifact・§8.3。評価 = 受理時 + 第 2 評価点）（v0.2.5・OPP-11） | `P_TIMEOUT_CEILING` |
| end-to-end 予算: `safety_heartbeat_timeout_s + detection + gateway 切替 + measured stop time ≤ baseline.safety_response_budget_s`（measured 値は CONTROLLER_ENVELOPE_MEASUREMENT / FAULT_INJECTION_RESULT の実測 artifact）（v0.2.5・OPP-11） | `P_SAFETY_BUDGET_EXCEEDED` |
| `command_deadline_s ≥ 1 / action_rate_hz`（LEARNED の各 expectation） | `P_DEADLINE_BELOW_PERIOD` |
| `health_checks` に {SAFETY_LAYER_HEARTBEAT, SAFETY_LAYER_IDENTITY, CONTROLLER_LIVENESS, ENVELOPE_READBACK, GATEWAY_CONFIG_MATCH, CONTROLLER_IDENTITY, TOOL_IDENTITY} の各 kind が ≥ 1（v0.2.4 R2-09 で SAFETY_LAYER_IDENTITY 追加）・stage ∈ {BEFORE_PERMIT, BOTH}（v0.2.3・CD-02 / CD-09） | `P_HEALTHCHECK_MISSING` |
| `clearance_roles` が {SAFETY, SAFE_STOP, CHECKPOINT_DISABLED, MANAGER_RESTART, GATEWAY_RESTART}・GENESIS（R2-15） の各 reason に ≥ 1 role を持つ（= 05 §5.4 条件 10 の集合。SAFETY は ISL clearance record と AND）（v0.2.3・CD-02・v0.2.4 R1-04 / R2-05） | `P_CLEARANCE_ROLE_MISSING` |
| mandatory kind の各 `check_id` について、誘発した不一致で `R_HEALTHCHECK_FAILED` / HEALTH_FAILED を出した negative-control の HEALTH_CHECK_RUN record（artifact_ref → 当該 record を含む audit 範囲）が CLOSED_LOOP lease 前に存在（constant-True evaluator の排除・v0.2.4 R2-06） | `P_EVIDENCE_UNBOUND`（subject = check_id#NEGATIVE） |
| 全 `HealthCheckSpec.fail_closed == True` | `P_HEALTHCHECK_FAIL_OPEN` |
| `calibration_refs` が `REQUIRED_CALIBRATION_KINDS(control_mode)` を含む（LEARNED = {TCP, CAMERA_EXTRINSIC, CAMERA_INTRINSIC}・SCRIPTED / WAIT = {TCP}・binding_expectations の各 control_mode について評価・v0.2.3 CD-08）、`valid_until` が評価時刻より後 | `P_CALIBRATION_MISSING` / `P_CALIBRATION_EXPIRED` |
| `deployment_evidence_policy_hash` が解決でき、required kinds が **(kind × subject) 単位**で profile_hash に対し存在（登録時 = MIN_SHADOW・permit 発行時 = 当該 lease mode の集合。CALIBRATION_RECORD ∀ `calibration_refs[].calibration_id`・HEALTH_CHECK_RUN ∀ `health_checks[].check_id`・FAULT_INJECTION_RESULT ∀ `fault_injection[]` with must_be_exercised_before ⊑ mode: `subject_ref == runtime_fault_code`）（v0.2.3・CD-03） | `P_EVIDENCE_UNBOUND` |
| required record の `valid_until_iso8601` が permit 発行の wall-clock より前（第 2 評価点・`validity_rule` の執行） | `P_EVIDENCE_EXPIRED` |
| `CalibrationRef.valid_until_iso8601`、および required record のうち kind ∈ {CALIBRATION_RECORD, SAFETY_LAYER_ACCEPTANCE} の `valid_until_iso8601` が None（無期限）（v0.2.4・R2-18） | `P_VALIDITY_UNBOUNDED` |
| FAULT_INJECTION_RESULT / HEALTH_CHECK_RUN の `artifact_ref` が解決する audit 範囲に、`kind = FAULT ∧ fault == subject_ref の code ∧ profile_hash 一致`（fault）／ `kind ∈ {HEALTH_CONFIRMED, HEALTH_FAILED} ∧ payload に check_id`（health）の `RuntimeAuditRecord` が ≥ 1 件（第 2 評価点・v0.2.4 R2-02） | `P_FAULT_EVIDENCE_UNVERIFIED` |
| `fault_injection[].runtime_fault_code` ∉ 05 `RuntimeFaultCode` | `P_FAULT_CODE_UNKNOWN` |
| `required_before_shadow_lease` に HEALTH_CHECK_RUN / FAULT_INJECTION_RESULT を含む、または `fault_injection[].must_be_exercised_before == SHADOW_NON_AUTHORITY`（lease でしか作れない evidence を最初の lease の前提にする循環・schema 1.0）（v0.2.4・R2-14。非単調（CLOSED_LOOP 集合 ⊉ SHADOW 集合）は MIN_CLOSED_LOOP が全 8 kind を含むため 1.0 では表現不能 — code を足さない） | `P_EVIDENCE_POLICY_CIRCULAR` |
| 各 `arms[].controller` の tuple 長 = `robot_model_ref` の関節数（arm ごと・v0.2.4） | `P_ENVELOPE_SHAPE` |
| `resource_availability.control` で True の `ee_left` / `ee_right` ごとに `cell.arms` に `resource_id` が一致する entry がちょうど 1 つ（gripper_* は当該 arm の tool_payload）。arm 単位の identity / envelope / TCP を持たない資源を offered にできない（v0.2.4・R2-04 — 単一 robot 限定案は RS71 §0 DUAL-ARM 不変前提と衝突するため不採用・OPP-15） | `P_ARM_COVERAGE` |
| schema 1.0 では `resource_availability.control` の `ee_left` / `ee_right` / `gripper_left` / `gripper_right` が全て True（DUAL-ARM cell の**能力**の宣言・RS71 §0 #1。⚠ every motion で両腕が活動する適合性は本検査の外 = OPP-17）（v0.2.5・OPP-15 B+） | `P_ARM_CAPABILITY_MISSING` |
| 各 `arms[].base_transform_id` が `kinematic_layout` artifact 内の entry に解決し、`arms[].gripper_resource_id` が arms 内で一意（v0.2.5） | `P_ARM_BASE_UNBOUND` / `P_ARM_COVERAGE` |
| `inter_arm_restrictions.min_separation_m > 0` ∧ pairwise keep-out または swept-volume predicate が ≥ 1（content hash は 05 §3.4 (j) の照合対象）（v0.2.5） | `P_INTER_ARM_RESTRICTION_MISSING` |
| `ControllerEnvelope` の全上限 > 0・有限（v0.2.3・CD-07） | `P_ENVELOPE_NONPOSITIVE` |
| `workspace.zones` に kind = REACH_LIMIT が ≥ 1（到達域の宣言なし = 空間制約なし、を許さない） | `P_WORKSPACE_EMPTY` |
| `ControllerEnvelope` の各上限 ≤ `CONTROLLER_ENVELOPE_MEASUREMENT` record の測定値（artifact schema = ControllerEnvelope と同一 field）。評価点 = **第 2 評価点・`proposed_lease.mode == CLOSED_LOOP_AUTHORITY` のとき**（登録時 = MIN_SHADOW には測定 record が無い・v0.2.4 R2-11） | `P_ENVELOPE_EXCEEDS_MEASURED` |
| profile が宣言する**全ての** content hash（`predicate_sha256` / `evaluator_sha256` / `zones[].geometry_sha256` / `calibration_refs[].artifact_sha256` / `gateway_config.artifact_sha256` / `deployment_evidence_policy_hash` / required record の `artifact_sha256`）が解決先の内容と一致（登録時；第 2 評価点の再照合は 05 §3.4 (j) `R_PROFILE_MISBOUND`；gateway は predicate と zone geometry を評価前に再検証）（v0.2.3・CD-04・v0.2.4 R1-05 / R2-03 で全 hash へ一般化） | `P_PREDICATE_HASH_MISMATCH`（名称は据え置き・対象は全宣言 hash） |
| `tcp_offset_ref` が `calibration_refs` の kind = TCP entry に解決する | `P_TCP_REF_UNRESOLVED` |
| AcceptedEnvelope 静的充足可能性（§4） | `P_ENVELOPE_EMPTY` |
| `binding_expectations` の `skill_action_id` が certified（certificate 存在） | `P_EXPECTATION_UNCERTIFIED` |
| 反循環 / 未知 field / 版 | `P_SELF_HASH` / `P_UNKNOWN_FIELD` / `P_SCHEMA_VERSION_UNKNOWN` |
| `robot_model_ref` が RS71 §0 の型式と一致（v0.2.1） | `P_ROBOT_MODEL_MISMATCH` |
| 全 spatial field の `frame_ref` == `base_frame_ref` or `tool_flange`（v0.2.1） | `P_FRAME_MISMATCH` |
| `DeploymentEvidencePolicy` が MIN_SHADOW / MIN_CLOSED_LOOP / MIN_FAULT_INJECTION を含む（v0.2.1） | `P_EVIDENCE_POLICY_TOO_WEAK` |

**「広げる」試みの網羅（反証の型・v0.2.3 CD-07 で正直化）**: profile が frozen より緩い挙動を引き起こす経路は (i) action-space bounds を緩める — field が無い、(ii) 周波数・hold・control_mode を変える — 等値検査、(iii) initiation を緩める — AND のみ、(iv) 鮮度を緩める — `p ≤ f`、(v) 資源を偽って offered にする — CELL_COMMISSIONING evidence、(vi) 安全層を不要にする — True 必須、(vii) disposition を緩める — enum に緩和値が無い、(viii) boundary を checkpoint 化する — field が無い、(ix) 合成語彙を持ち込む — `P_COMPOSITION_CONTENT`、(x) timeout を伸ばして安全機構を無効化する — `P_TIMEOUT_ORDER`（相対順序。絶対上限 = OPP-11）、(xi) envelope / zone / predicate を空虚にする — `P_ENVELOPE_NONPOSITIVE` / `P_WORKSPACE_EMPTY` / `P_ENVELOPE_EXCEEDS_MEASURED` / `P_PREDICATE_HASH_MISMATCH`。**契約層で検証できるのは形・単調性・宣言と evidence の束縛まで**であり、物理事実（資源の実在・上限値の真偽・zone 幾何の正しさ・predicate 内容の妥当性・tool 質量）は全て evidence（§6）に委ねる（OPP-5 を拡張）。

## 4. `AcceptedEnvelope` の供給（05 §4.3 の連言に対する本 doc の項）

```text
AcceptedEnvelope(lease) = ⋀ { INTRINSIC_D11B(tensor_binding_hash)   … policy action space（bounds / action_scale / transform 順）— D1.1-B、写さない
                            , CONTROLLER(profile.cell.arms[cmd.resource].controller)  … joint space（command が指す arm の envelope・v0.2.4 R2-04）（velocity / acceleration / jerk / ee_speed — admission 可能な運動学項のみ。force / torque は監視上限・v0.2.3 CD-07）
                            , DEPLOYMENT_WORKSPACE(profile.workspace) … workspace（keep-out / reach / height）
                            , SAFETY_RESTRICTION(profile.safety_restrictions) … gateway predicate（静的）}
```

- handoff 決定 B の「∩」は、各項を**自分の空間**で評価した連言と読む（05 R6）。異なる空間の集合を literal に交差させる演算は定義しない。
- 空 / 充足不能（例: keep-out が到達領域を全て覆う、`ee_speed_max = 0`）= **fail-closed**: 静的検査 `P_ENVELOPE_EMPTY`（profile 受理時）と runtime `R_ENVELOPE_EMPTY`（05 CAS 前提 7）の二重化。静的検査は「明らかな不能」の検出であり充足可能性の完全判定ではない（§10 OPP-2）。
- 単位・frame: profile 項は SI（rad, m, s, N, N·m）。D1.1-B の `unit` / `frame`（`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:75-76`）とは空間が異なるため、変換は gateway が FK / 逆写像で行い、変換不能 = 拒否（05 §4.3「評価不能 = FALSE」）。
- SCRIPTED / WAIT skill（`tensor_binding_hash = null`）では INTRINSIC 項が欠け、profile 3 項のみ（05 OP-2）。profile はこれを埋めない（intrinsic 宣言は future static candidate）。
- **DEPLOYMENT_WORKSPACE の評価対象（v0.2.3・CD-18）**: `DIFF_IK_EE_TARGET` では hold 種別にかかわらず直前 admitted setpoint（初回は実測 TCP）→ 新 setpoint の**線分**（FK 後・TCP 点）— ZOH でも腕は連続に動くため点評価では keep-out を跨げる（v0.2.4・R1-06 / R2-19）。tool 形状（collision hull）は評価しない — 物体形状に対する keep-out は IndependentSafetyLayer の監視（OPP-14）。

## 5. Lease 束縛

- `ActiveAuthorityLease.profile_hash`（05 §4.1）= 本 doc の `profile_hash`。`CommitPermit.profile_hash` と等値（05 §3.5 条件 2・§3.4 (f) の等値束縛 — v0.2.3 A-01 / B-M5 残差。条件 6 は certificate の skill_action_id のみを束縛する）。
- **profile 変更 = 新 lease**: profile を「更新」する操作は存在しない。新 profile（新 hash）は 05 の完全経路（ReadinessAck → CommitPermit → AuthorityCas）で新 lease に束縛される。活性 lease の profile を in-place で差し替える経路は無い（05 §4.1 束縛規則）。
- lease へ写される profile 由来の値: `TimingBinding.{ack_validity_s, ack_timeout_s, permit_ttl_s, health_confirm_timeout_s, command_deadline_s, manager_liveness_s, safety_heartbeat_timeout_s, decision_max_age_s, boundary_dwell_s, max_reselect_attempts, command_kind_mismatch_max, inter_command_jitter_s, lease_max_duration_s}` ← `RuntimeTimeouts`（同名 field の等値写像・v0.2.2 で 6 field・v0.2.3 で 1 field 追加）；`TimingBinding.runtime_max_staleness_s` ← `min(frozen FreshnessPolicy.max_staleness_s, FreshnessStrengthening.max_staleness_s)`（None 規則は §3）；`AcceptedEnvelope.terms` の 3 項 ← §4；`HealthConfirmation.profile_health_checks` ← `health_checks`（stage ∈ {AT_HEALTH_CONFIRMATION, BOTH}）；`lease.ownership`（SAFEHOLD 起動時）← `ResourceAvailability`。
- lease 活性中に profile の前提が崩れた場合（v0.2.2・B-M7 で 05 と同期）: (a) health check 失敗（stage AT_HEALTH_CONFIRMATION / BOTH）は 05 §4.5 `R_HEALTH_CONFIRM_FAILED` → SAFEHOLD。(b) calibration 期限切れ・deployment evidence 失効・acceptance 期限（v0.2.5・Rs 裁定 2026-09-04（GPT5.6sol 推奨を採用・`review_records/rs_consult/`）・OP-19）: **CLOSED_LOOP_AUTHORITY lease では次 permit まで待たない**。permit 発行時に既知の期限を manager clock へ変換した `validity_deadline_mono` を lease に束縛し、到達 = 05 TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)（安全機能・TCP・停止性能に関わる失効は SAFE_STOP へ強化）。期限に現れない変更（incident・tool 交換・firmware 更新・layout revision・ISL build 変更・profile SUSPENDED / REVOKED）は `DeploymentValidityMonitor` の event で即時無効化。周期診断は timing baseline（§8.3）が定める drift / proof-test 項目のみ。SHADOW_NON_AUTHORITY lease は actuation が無いため次 permit 評価で可。いずれの場合も profile 側の「更新」ではなく新 profile（新 hash）での新 lease。
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
    subject_ref: str                       # kind ごとに定義（v0.2.4・R2-16）: CELL_COMMISSIONING = cell.cell_id / CONTROLLER_ENVELOPE_MEASUREMENT = arms[].controller_firmware_ref（arm ごと） / TOOL_PAYLOAD_IDENTIFICATION = arms[].tool_payload.tool_id（arm ごと） / GATEWAY_CONFIG_ATTESTATION = gateway_config.config_id / SAFETY_LAYER_ACCEPTANCE = cell.safety_layer_ref / CALIBRATION_RECORD = calibration_id / HEALTH_CHECK_RUN = check_id / FAULT_INJECTION_RESULT = fault code（timeout 駆動は '<code>#<trigger>'）
    artifact_ref: str                      # v0.2.3（CD-16）: kind ∈ {HEALTH_CHECK_RUN, FAULT_INJECTION_RESULT} では 05 RuntimeAuditRecord の (lease_id | None, seq 範囲) に解決し、範囲内の全 record が `profile_hash == 本 record の profile_hash` を持つ（INITIAL SAFEHOLD から走る BEFORE_PERMIT check や lease 無しで誘発する fault は lease_id = None = 05 §8 `profile_hash` join・v0.2.4 R2-07）
    artifact_sha256: str
    measured_at_iso8601: str               # wall-clock（deployment evidence は暦時刻で失効する）
    operator_ref: str
    valid_until_iso8601: str | None        # v0.2.4（R2-18）: None の意味 = 失効なし（期限検査の対象外）。ただし kind ∈ {CALIBRATION_RECORD, SAFETY_LAYER_ACCEPTANCE} の required record と CalibrationRef は None 不可（P_VALIDITY_UNBOUNDED）

@dataclass(frozen=True)
class FaultInjectionRequirement:
    runtime_fault_code: str                # 05 RuntimeFaultCode の名（例: R_EPOCH_STALE_COMMAND）。v0.2.3（CD-03）: 05 enum に無い名 = P_FAULT_CODE_UNKNOWN
    must_be_exercised_before: LeaseMode    # 05 LeaseMode（SHADOW_NON_AUTHORITY / CLOSED_LOOP_AUTHORITY）

@dataclass(frozen=True)
class DeploymentEvidencePolicy:
    policy_schema_version: str             # "1.0"
    required_before_shadow_lease: tuple[DeploymentEvidenceKind, ...]      # ⊇ MIN_SHADOW（下記・規範）でなければ P_EVIDENCE_POLICY_TOO_WEAK（v0.2.1・C-09）
    required_before_closed_loop_lease: tuple[DeploymentEvidenceKind, ...] # 上記 + CONTROLLER_ENVELOPE_MEASUREMENT, TOOL_PAYLOAD_IDENTIFICATION, CALIBRATION_RECORD, HEALTH_CHECK_RUN, FAULT_INJECTION_RESULT
    fault_injection: tuple[FaultInjectionRequirement, ...]               # 最低 = R_EPOCH_STALE_COMMAND / R_OFFER_REUSED / R_PERMIT_REUSED / R_SAFETY_OVERRIDE / R_HEALTH_CONFIRM_FAILED / R_EXECUTOR_LOST を CLOSED_LOOP_AUTHORITY 前に
    validity_rule: ValidityRule            # v0.2.1（C-09）: enum。v1.0 の唯一の member = ALL_REQUIRED_VALID_AT_PERMIT_ISSUE

class ValidityRule(Enum): ALL_REQUIRED_VALID_AT_PERMIT_ISSUE

# 規範最小集合（v0.2.1・C-09 — comment ではなく本文の規則。policy がこれを含まなければ P_EVIDENCE_POLICY_TOO_WEAK）
MIN_SHADOW       = {CELL_COMMISSIONING, GATEWAY_CONFIG_ATTESTATION, SAFETY_LAYER_ACCEPTANCE}
MIN_CLOSED_LOOP  = MIN_SHADOW ∪ {CONTROLLER_ENVELOPE_MEASUREMENT, TOOL_PAYLOAD_IDENTIFICATION, CALIBRATION_RECORD, HEALTH_CHECK_RUN, FAULT_INJECTION_RESULT}
MIN_FAULT_INJECTION（CLOSED_LOOP_AUTHORITY 前）= {R_EPOCH_STALE_COMMAND, R_OFFER_REUSED, R_PERMIT_REUSED, R_SAFETY_OVERRIDE, R_HEALTH_CONFIRM_FAILED, R_EXECUTOR_LOST, R_POST_OUTCOME_COMMAND, R_GATEWAY_RESTART}
                 ∪ {R_DEADLINE_MISS, R_SAFETY_LAYER_LOST, R_TIMING_VIOLATION, R_PERMIT_EXPIRED, R_ACK_TIMEOUT, R_HEALTH_CONFIRM_TIMEOUT, R_BOUNDARY_DWELL_EXCEEDED, R_LEASE_DURATION_EXCEEDED, R_MANAGER_UNAVAILABLE}   # v0.2.3（CD-01）+ v0.2.4（R2-01）: timeout 駆動の fault は同一 profile_hash の下で commissioning 時に必ず発火させる。
#   timeout 駆動 code の FAULT_INJECTION_RESULT は subject_ref = '<code>#<timeout_trigger>'（例 R_SAFETY_LAYER_LOST#HEARTBEAT_TIMEOUT・R_BOUNDARY_DWELL_EXCEEDED#DWELL_TIMEOUT）で timeout 経路そのものを要求する（health==failed / attempts 尽きの別経路で代替できない — 05 §8 FAULT payload の trigger 副因と照合・v0.2.4 R2-01）
MIN_NEGATIVE_CONTROLS（CLOSED_LOOP_AUTHORITY 前・v0.2.5 OPP-15 B+ / OPP-11）= FAULT_INJECTION_RESULT with subject_ref ∈ {CELL#ARM_SWAP, CELL#ARM_MISSING, CELL#BASE_TRANSFORM_TAMPER, CELL#INTER_ARM_COLLISION, ENV#CLOCK_ANOMALY, ENV#SCHEDULER_STALL, ENV#COMM_LOSS}
#   期待結果 = 拒否 / SafeHold / SafeStop に baseline の予算内で到達。timeout 駆動 code の FAULT_INJECTION_RESULT artifact は worst-case 負荷下の「検出 → SafeHold / SafeStop 到達」実測上限を含み、P_SAFETY_BUDGET_EXCEEDED の入力になる
deployment_evidence_policy_hash = H_WCJ(DeploymentEvidencePolicy)
```

### 6.2 EP v1.9 との関係（= 無関係であることの明示）

- 本 policy は EP の `claim_targets`（13）/ `ProofKind`（15）/ grade（5）/ `profiles` のいずれにも項目を足さず、`evidence_policy_definition_hash`（`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:163`）は不変（04 参照）。
- **不在主張の範囲と再現（v0.2.2・A-03 / A2-10）**: 対象は **EP md / JSON の 2 file のみ**。再現 command（本 package 内で解決可能）: `for p in controller calibrat deploy inject epoch lease; do grep -ic "$p" $D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md $D/WMSO_EvidencePolicy_v1.9.json; done` = 全 pattern で 0 / 0（2026-09-04 実測）。`cell` は EP が usage matrix の表 cell の語として使う（md 10 行 / json 3 行）ため対象外（v0.2.1 C-14）。⚠ DESIGN 2 file には散文語の hit がある（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:570`・`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:337`「calibrated uncertainty」／ `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:255`・`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:313`「全 deployment の resolver」）— いずれも型・field・enum ではない。ゆえに deployment evidence は EP の claim_target / ProofKind の**外**にある（型レベルの根拠 = 07 §1 根拠 4）。
- grade 語（EXACT_TRAIN_TIME 等）を deployment evidence に使わない。deployment evidence は「存在・有効期限・束縛」だけを持ち、skill の certification に影響しない（certificate は runtime / deployment の事象で無効化されない — `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:39`）。
- `SAFETY_LAYER_ACCEPTANCE` の**内容**（機能安全の受入基準）は本 doc の外（§10 OPP-6）。本 doc は record の存在と束縛だけを要求する。

### 6.3 runtime audit との結線

- 05 `RuntimeAuditRecord` は runtime 事象（epoch / permit / lease / fault / disposition）を、本 doc の record は deployment 事実を持つ。両者は `profile_hash` で join し、HEALTH_CHECK_RUN / FAULT_INJECTION_RESULT は `artifact_ref` が指す (lease_id, seq 範囲) で 05 §8 の record に束縛される（v0.2.3・CD-16）。hash chain / 署名は 05 OP-5（U14 defer）に従う。

## 7. 合成（composition）の除外

- 旧 v0.1 の並行実行 profile は**削除**し、本 doc は合成（`SkillCompositionDefinition` / barrier / region postcondition / `ParallelRegion` の枝数 / DUAL-ARM 適合）を一切含まない。
- 根拠: 合成 schema delta = pX SKILL-DESIGN の court、`ParallelRegion` 枝数下限の supersede と DUAL-ARM 適合 = Rs 専権 OPEN（`$D/WMSO_RS_D11C_SCOPE_APPROVAL_CUSTODY_20260721.md:36-38`）；arity SUSPENDED は D1.1-B freeze と独立（`$D/WMSO_D11B_FREEZE_RECORD_20260721.md:39`）；SKILL の決定権 = pX（`$D/WMSO_RS_SKILL_OWNERSHIP_RULING_20260720.md:9`）。
- 機械検査: profile の**構造**（field 名・型名・enum member・`predicate_refs` / `restriction_ids` の識別子）に合成語彙（`ParallelRegion` / `SkillCompositionDefinition` / `branch_count` / `barrier` / `region_postcondition` / `arity`）が識別子単位（word boundary）で現れたら `P_COMPOSITION_CONTENT`。v0.2.1（C-17）: 自由文（`profile_label` 等）は対象外・部分文字列一致（例: `similarity` 内の `arity`）は検出しない。
- 本 doc の `ResourceAvailability.control` が両腕の資源を True にすることは「cell に両腕がある」事実の宣言であり、2 executor の同時保持（合成）を許す意味ではない（05 §11 項 5: lease は常に 1 executor）。

## 8. Validation 規則・code 一覧・Test plan（設計時宣言 — impl CLOSED）

### 8.1 code 一覧（接頭辞 `P_`・frozen `E_*` / runtime `R_*` と衝突しない）

`P_INTRINSIC_OVERRIDE` / `P_RATE_MISMATCH` / `P_HOLD_MISMATCH` / `P_CONTROL_MODE_MISMATCH` / `P_BINDING_HASH_MISMATCH` / `P_INITIATION_RELAXED` / `P_FRESHNESS_RELAXED` / `P_RESOURCE_UNATTESTED` / `P_SAFETY_LAYER_NOT_REQUIRED` / `P_COMPOSITION_CONTENT` / `P_TIMEOUT_NONPOSITIVE` / `P_DEADLINE_BELOW_PERIOD` / `P_HEALTHCHECK_MISSING` / `P_HEALTHCHECK_FAIL_OPEN` / `P_CALIBRATION_MISSING` / `P_CALIBRATION_EXPIRED` / `P_EVIDENCE_UNBOUND` / `P_ENVELOPE_SHAPE` / `P_ENVELOPE_EMPTY` / `P_EXPECTATION_UNCERTIFIED` / `P_SELF_HASH` / `P_UNKNOWN_FIELD` / `P_SCHEMA_VERSION_UNKNOWN` / `P_ROBOT_MODEL_MISMATCH` / `P_FRAME_MISMATCH` / `P_EVIDENCE_POLICY_TOO_WEAK`（v0.2.1） / `P_TIMEOUT_ORDER` / `P_CLEARANCE_ROLE_MISSING` / `P_EVIDENCE_EXPIRED` / `P_FAULT_CODE_UNKNOWN` / `P_PREDICATE_HASH_MISMATCH` / `P_TCP_REF_UNRESOLVED` / `P_ENVELOPE_NONPOSITIVE` / `P_WORKSPACE_EMPTY` / `P_ENVELOPE_EXCEEDS_MEASURED`（v0.2.3） / `P_FAULT_EVIDENCE_UNVERIFIED` / `P_ARM_COVERAGE` / `P_EVIDENCE_POLICY_CIRCULAR` / `P_VALIDITY_UNBOUNDED`（v0.2.4） / `P_ARM_CAPABILITY_MISSING` / `P_ARM_BASE_UNBOUND` / `P_INTER_ARM_RESTRICTION_MISSING` / `P_TIMEOUT_CEILING` / `P_SAFETY_BUDGET_EXCEEDED` / `P_ACCEPTANCE_RECORD_INVALID`（v0.2.5）

規則: (1) 全検査は fail-closed（評価不能 = 違反）。(2) profile の受理（`profile_hash` の登録 = `accepted_profiles` への追加・registry と受理権限は OPP-13）は全 `P_*` = 0 が前提。registry と受理・失効の手続は §8.3（v0.2.5・Rs 裁定 2026-09-04（GPT5.6sol 推奨を採用・`review_records/rs_consult/`）・旧 v0.2.4 の 2 集合 accepted / revoked は `ProfileAcceptanceRecord` に置換）。**評価点は 2 つ（v0.2.1・C-10）**: 第 1 評価点 = 登録時（構造・単調性・反循環・codec・`P_RESOURCE_UNATTESTED` / `P_EVIDENCE_POLICY_TOO_WEAK` / `P_ROBOT_MODEL_MISMATCH` / `P_FRAME_MISMATCH`）／ 第 2 評価点 = **permit 発行時**（時刻・lease 文脈依存の `P_CALIBRATION_EXPIRED` / `P_EVIDENCE_UNBOUND`（当該 lease mode の集合・subject 単位） / `P_EVIDENCE_EXPIRED` / `P_EXPECTATION_UNCERTIFIED` を再評価 — 05 §3.4 が `R_PROFILE_MISBOUND` として扱う）。(3) 受理後の事実変化（期限切れ・evidence 失効）は profile を変えない。活性 lease は継続し、次の permit 発行が `P_CALIBRATION_EXPIRED` / `P_EVIDENCE_UNBOUND` / `P_EVIDENCE_EXPIRED` → 05 `R_PROFILE_MISBOUND` で不成立になる（§5 (b)）。**profile 起因で** lease を無効化するのは health check 失敗（§5 (a)）と `lease_max_duration_s` 超過（CD-10）のみ（v0.2.3・B-M7 残差）。(4) `P_*` は certificate・EP grade・`SkillDefinitionHash` のいずれにも影響しない。

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
| PT-09 | CELL_COMMISSIONING evidence（profile_hash 束縛）が evidence store に無い profile を登録 | `P_RESOURCE_UNATTESTED`（v0.2.1: 一方向束縛） |
| PT-16 | 空の `DeploymentEvidencePolicy`（required 集合 = ∅） | `P_EVIDENCE_POLICY_TOO_WEAK`（v0.2.1） |
| PT-17 | zone の `frame_ref` を base_frame_ref 以外にする（v0.2.1） | `P_FRAME_MISMATCH` |
| PT-10 | `deployment_evidence_policy_hash` 未解決 / required kind 欠落 | `P_EVIDENCE_UNBOUND` |
| PT-11 | profile 本文に `ParallelRegion` を含める | `P_COMPOSITION_CONTENT` |
| PT-12 | profile が自身の hash を field に持つ | `P_SELF_HASH` |
| PT-13 | 受理済 profile の calibration が失効 | profile 不変。CLOSED_LOOP lease は `validity_deadline_mono` 到達で TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)（TCP calibration なら SAFE_STOP・05 R_CALIBRATION_EXPIRED_ACTIVE・v0.2.5 OP-19）。SHADOW lease は次 permit まで継続（曝露 = actuation 無し）。次の permit 発行は `P_CALIBRATION_EXPIRED` → 05 `R_PROFILE_MISBOUND` で不成立 |
| PT-14 | 同一 cell で profile A → B へ切替 | in-place 更新経路なし。B の lease は 05 完全経路（新 epoch）でのみ成立 |
| PT-15 | golden profile 2 本の `profile_hash` 再現（WCJ + B-declared 規約） | byte 同一・hash 一致（fixture は impl 解錠後に bank） |
| PT-18 | `CalibrationRef.kind` に未知文字列（typo）を与える（v0.2.3） | codec 拒否（enum strict） |
| PT-19 | SCRIPTED skill の expectation に `action_rate_hz` を非 null で宣言（v0.2.3） | `P_INTRINSIC_OVERRIDE` |
| PT-20 | `safety_heartbeat_timeout_s = 1e9`（他は妥当）の profile（v0.2.3） | `P_TIMEOUT_ORDER` |
| PT-21 | commissioning 後に firmware 更新・tool 交換（profile 不変）で permit 要求（v0.2.3） | CONTROLLER_IDENTITY / TOOL_IDENTITY が fail → 05 `R_HEALTHCHECK_FAILED`・permit 不発行 |
| PT-22 | `clearance_roles` に SAFETY の role が無い profile（v0.2.3・v0.2.4 で SAFETY を必須集合へ） | `P_CLEARANCE_ROLE_MISSING` |
| PT-23 | `SAFETY_LAYER_ACCEPTANCE` record の `valid_until` を過去にして permit 要求（v0.2.3） | `P_EVIDENCE_EXPIRED` → 05 `R_PROFILE_MISBOUND` |
| PT-24 | FAULT_INJECTION_RESULT が MIN_FAULT_INJECTION の 1 code 分しか無い profile で CLOSED_LOOP permit（v0.2.3） | `P_EVIDENCE_UNBOUND`（subject 単位） |
| PT-25 | 登録後に `keepout_pred_v1` の内容を常時許可に差し替え（v0.2.3） | 次 permit で `R_PROFILE_MISBOUND`・gateway 評価前の再検証で FALSE（拒否） |
| PT-26 | `joint_velocity_max = (1e6, …)`・`zones = ()`・`predicate_refs = ()` の profile（v0.2.3） | `P_WORKSPACE_EMPTY`・`P_ENVELOPE_EXCEEDS_MEASURED`（測定値超過） |
| PT-27 | 登録後に keep-out zone の geometry artifact を差し替え（v0.2.4） | 次 permit で `R_PROFILE_MISBOUND`・gateway 評価前の再検証で FALSE |
| PT-28 | FAULT_INJECTION_RESULT の artifact_ref が当該 fault を含まない audit 範囲を指す（v0.2.4） | `P_FAULT_EVIDENCE_UNVERIFIED` |
| PT-29 | `resource_availability.control = {ee_left: True, ee_right: True, …}` で `cell.arms` が 1 entry（v0.2.4） | `P_ARM_COVERAGE` |
| PT-30 | SAFETY_LAYER_ACCEPTANCE 後に IndependentSafetyLayer を更新して permit 要求（v0.2.4） | SAFETY_LAYER_IDENTITY fail → 05 `R_HEALTHCHECK_FAILED` |
| PT-31 | `must_be_exercised_before = SHADOW_NON_AUTHORITY` の fault_injection 要件（v0.2.4） | `P_EVIDENCE_POLICY_CIRCULAR` |
| PT-32 | TCP calibration を `valid_until = None` で宣言（v0.2.4） | `P_VALIDITY_UNBOUNDED` |
| PT-33 | `ee_right = False` の profile（v0.2.5） | `P_ARM_CAPABILITY_MISSING`（schema 1.0 は DUAL-ARM cell 能力必須） |
| PT-34 | 両 arm に同じ `gripper_resource_id`（v0.2.5） | `P_ARM_COVERAGE` |
| PT-35 | `safety_heartbeat_timeout_s` を baseline ceiling の 2 倍で宣言（v0.2.5） | `P_TIMEOUT_CEILING` |
| PT-36 | 全 timeout を同率で 100 倍（相対順序は維持）（v0.2.5） | `P_TIMEOUT_CEILING`（順序検査だけでは通る — CD-01 / GPT 前提訂正 4） |
| PT-37 | cell operator 単独の approvals で CLOSED_LOOP を許す record（v0.2.5） | `P_ACCEPTANCE_RECORD_INVALID` |
| PT-38 | 登録後に kinematic layout artifact の base transform を改変（v0.2.5） | 次 permit で 05 `R_PROFILE_MISBOUND`（(j)）・negative control CELL#BASE_TRANSFORM_TAMPER |

### 8.3 ProfileRegistry と ProfileAcceptanceRecord（v0.2.5・Rs 裁定 2026-09-04（GPT5.6sol 推奨を採用・`review_records/rs_consult/`））

```python
class AcceptanceState(Enum):     PROPOSED | ACCEPTED | SUSPENDED | REVOKED     # REVOKED は終端。再使用 = 新 generation の新 record のみ

@dataclass(frozen=True)
class ProfileAcceptanceRecord:            # 不変・append-only。record_hash = H_WCJ(本 record)
    profile_hash: str
    generation: int                        # 同一 profile_hash の受理世代（再受理ごとに +1）
    state: AcceptanceState
    allowed_lease_modes: tuple[LeaseMode, ...]        # SHADOW_NON_AUTHORITY / CLOSED_LOOP_AUTHORITY（05）
    validator_hash: str                    # 受理時に用いた P_* validator 版の content hash
    evidence_set_hash: str                 # 受理時に照合した DeploymentEvidenceRecord 集合の hash
    timing_baseline_hash: str              # CellSafetyTimingBaseline（下記）の content hash — profile preimage には入れない（反循環）
    cell_identity_hash: str                # CellIdentity（layout_revision_ref・kinematic_layout を含む）の hash
    approvals: tuple[tuple[str, str, str], ...]        # (role, operator_ref, t_iso8601)
    valid_until_iso8601: str               # 受理の有効期限（None 不可）
    supersedes_record_hash: str | None     # 前 generation / 前 state の record

@dataclass(frozen=True)
class CellSafetyTimingBaseline:           # RT0 / cell safety court が発行する content-addressed artifact（OPP-16）。本 doc は値を持たない
    baseline_id: str
    approved_ceiling: dict                 # RuntimeTimeouts の全 field → 上限 [s]（int field は回数）
    safety_response_budget_s: CanonicalDecimal
    worst_case_attempt_s: CanonicalDecimal
    selector_overhead_s: CanonicalDecimal
    diagnostic_items: tuple[tuple[str, CanonicalDecimal, CanonicalDecimal], ...]   # (項目, 周期 [s], worst-case detection [s]) — OP-19 の周期診断はこの項目のみ
```

- **状態遷移**: PROPOSED → ACCEPTED（受理）; ACCEPTED → SUSPENDED（一時停止・one-key fail-safe）; SUSPENDED → ACCEPTED は**新 generation の新 record**（原因除去 evidence + two-key）でのみ; ACCEPTED / SUSPENDED → REVOKED（終端）。旧 record は削除しない（append-only）。
- **受理の権限**: 全 `P_*` = 0 は必要条件。SHADOW_NON_AUTHORITY のみを許す受理 = cell commissioning 担当 + 独立 reviewer。CLOSED_LOOP_AUTHORITY を許す受理 = 「独立 safety approver」と「deployment / operations custody approver」の **two-key**。cell operator 単独では CLOSED_LOOP を許可できない。
- **失効の権限（非対称）**: incident・ISL 異常・layout / tool / controller / safety-layer identity の変更のいずれでも、認可された一者または自動 monitor（05 DeploymentValidityMonitor）が即時 SUSPENDED にできる。解除は上記の再受理のみ。
- **05 との結線**: permit は `acceptance_record_hash` / `generation` を束縛し（05 §3.4 (i)）、CAS 条件 12 で `state == ACCEPTED ∧ 同一 generation ∧ mode ∈ allowed_lease_modes` を再検査する。SUSPENDED / REVOKED は pending permit を VOID にし、活性 CLOSED_LOOP lease を SafeHold（安全起因なら SafeStop）へ移す（05 §3.7）。
- **所在**: registry は AuthorityManager と論理的に分離する（同一 transactional DB を使う場合も namespace・ACL・journal writer を分ける）。AuthorityManager は read-only consumer。registry を復元できない場合、process は診断用 SAFEHOLD で起動してよいが permit 発行・CAS・actuation は全面拒否（05 `R_REGISTRY_UNAVAILABLE`）。
- **反循環**: `timing_baseline_hash` と `acceptance_record_hash` は profile の preimage に入らない（profile_hash → record → baseline の一方向）。
- 検査: record の必須 field 欠落・generation 非単調・CLOSED_LOOP 許可で two-key 不足・`valid_until` None = `P_ACCEPTANCE_RECORD_INVALID`（受理拒否）。

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
| OPP-5 | 物理事実（`ResourceAvailability`・`ControllerEnvelope` 値・zone 幾何・predicate 内容・tool 質量）の真偽は契約層で判定不能（v0.2.3・CD-07 で範囲を拡張） | §3 (v)(xi) | 対応する evidence kind（CELL_COMMISSIONING / CONTROLLER_ENVELOPE_MEASUREMENT / …）に委ねる。P_* は形・単調性・束縛のみ |
| OPP-6 | `SAFETY_LAYER_ACCEPTANCE` の受入基準の内容 | §6.2 | 外部 court |
| OPP-7 | **DDR#41**: `CellIdentity.robot_model_ref` は RS71 §0 の型式（UR15）と一致必須。凍結 v13 `:332` の 88 mm 引用の扱い（Rs 専権）に本 doc は依存しないが、robot_model_ref の照合先が動けば profile の受理条件が動く | `thread_isaac_lab/thread-vault/02-Workflow/HANDOFF_pQ_rstechlead2_wmso.md:11` | 照合先 = RS71（本 doc は値を書かない） |
| OPP-8 | profile の複数 skill への適用（`binding_expectations` が全 certified skill を列挙するか、cell 単位で 1 profile か） | §2.2 | 1 cell : n expectations を既定。運用形は slice 詳細 prereg |
| OPP-9 | `HealthCheckSpec.evaluator_ref` の登録・版管理（EP の evaluator registry を流用しない）。kind 認証済 evaluator registry が無い間、`P_HEALTHCHECK_MISSING` は kind label の存在検査に過ぎず、evaluator の意味は negative-control evidence（§3・v0.2.4 R2-06）で担保する | EP `evaluator_registry_rule` は certification 用 | 別 registry（名前空間を分ける）— 内容は impl 解錠後 |
| OPP-10 | 本 doc 自体の two-key・Rs 裁定 | — | 未 |
| OPP-11 | **Rs 裁定 2026-09-04（GPT5.6sol 推奨を採用・`review_records/rs_consult/`）**: 絶対上限は本 doc に書かず、RT0 / cell safety court が発行する content-addressed `CellSafetyTimingBaseline`（§8.3）を唯一の ceiling source とし `P_TIMEOUT_CEILING` / `P_SAFETY_BUDGET_EXCEEDED` で検査。追加順序（`ack_timeout_s ≤ boundary_dwell_s` 等）は採用、`decision_max_age_s ≤ permit_ttl_s` は撤回し 05 `effective_expires_at` へ。**残 open** = baseline の発行主体・改訂手続（OPP-16） | §3・§8.3・05 OP-20 | 裁定反映済・値は baseline |
| OPP-12 | `profile_label` を hash preimage から射影するか（§2.3 の「新規則を足さない」と衝突） | §2.2 | 現状 = preimage に含む（label 変更 = identity event） |
| OPP-13 | **Rs 裁定 2026-09-04（GPT5.6sol 推奨を採用・`review_records/rs_consult/`）**: append-only `ProfileRegistry` + 不変 `ProfileAcceptanceRecord`（PROPOSED / ACCEPTED / SUSPENDED / REVOKED・generation）。CLOSED_LOOP 受理 = two-key（独立 safety approver + custody approver）、SUSPENDED = one-key fail-safe、CAS で再検査、registry 不読 = actuation 拒否。**残 open** = 各 role の実名（pS / pY 等）の割当 | §8.3・05 §3.4 (i)・§3.5 条件 12 | 裁定反映済・role の実名は Rs |
| OPP-14 | tool / payload の形状（collision hull）を profile に宣言して workspace 項で評価するか（現状 = TCP 点 / 線分のみ・形状は ISL 監視） | §4 | 宣言 field は無し（追加は新 evidence kind を伴う） |
| OPP-15 | **Rs 裁定 2026-09-04（GPT5.6sol 推奨を採用・`review_records/rs_consult/`）**: 案 B+ を採用 — `ArmSpec` に加え `CellKinematicLayoutRef`（両 arm の base transform・collision model）と `InterArmRestrictionSet`（min separation・pairwise keep-out・swept-volume predicate）を content-addressed に束縛し、schema 1.0 は DUAL-ARM cell 能力（両 EE・両 gripper）を必須化。案 A（単一 robot 限定）は不採用。不変前提への影響なし（DUAL-ARM を単腕化せず、88 mm span / 固定 base を変更しない）。⚠ 案 B/B+ の採用だけで「DUAL-ARM 充足済み」と宣言しない（OPP-17） | RS71 §0・§2.1・§3・05 §4.3 | 裁定反映済 |
| OPP-16 | `CellSafetyTimingBaseline` の発行主体（RT0 / cell safety court）・改訂手続・ceiling 値の根拠（cell ごとの risk assessment）。本 doc は hash 束縛と検査だけを持つ（v0.2.5・OPP-11） | §8.3・05 OP-20 | RT0 へ carry |
| OPP-17 | 「every motion で両腕が保持・操作する」（RS71 §0 #1）の実行適合性検査。本 doc は両腕**能力**の存在と arm 間の静的制約までを検査し、合成・実行適合性は composition / runtime 検査の court に残す（v0.2.5・OPP-15 B+） | §7・05 OP-21 | 主張しない |

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
- **v0.2.1 fold（2026-09-04 01:51 UTC・file mtime 実測）— 陽性対照レビュー（盲検 reviewer PC_C / PC_B）の**注入外** finding を verify して fold**:

| finding | 内容 | 変更節 |
|---|---|---|
| C-06 (HIGH) | initiation 強化の runtime 評価点が無い | 05 §6.2 B4 に明示（本 doc §1 表を更新） |
| C-07 (MEDIUM) | BEFORE_PERMIT health check の結線点が無い | 05 §3.4 permit 発行前提条件（本 doc は stage 定義のみ） |
| C-08 (MEDIUM) | `attested_by` と record.profile_hash の循環参照 | §2.1 `attested_by` 削除・一方向束縛・PT-09 |
| C-09 (MEDIUM) | 最小 required 集合が comment・validity_rule が自由文 | §6.1 MIN_SHADOW / MIN_CLOSED_LOOP / MIN_FAULT_INJECTION（規範）・`ValidityRule` enum・`P_EVIDENCE_POLICY_TOO_WEAK`・PT-16 |
| C-10 (MEDIUM) | 時刻依存 P_* の評価点が未定義 | §8.1 規則 (2) 2 評価点 |
| C-11 (MEDIUM) | 空間項に frame が無い | `base_frame_ref` / `frame_ref`・`P_FRAME_MISMATCH`・PT-17 |
| C-12 / B-11 (MEDIUM) | `ack_validity_s` の出所 | `RuntimeTimeouts.ack_validity_s` |
| C-13 (MEDIUM) | clearance_roles が ISL clearance の代替と読める | §2.1 注記（常に AND） |
| C-14 (LOW) | `cell` 語彙の誤主張 | §6.2 訂正 |
| C-15 (LOW) | robot_model_ref の不一致 code 無し | `P_ROBOT_MODEL_MISMATCH` |
| C-16 (LOW) | 作成時刻が非厳密 | header |
| C-17 (LOW) | 合成語彙検査の部分文字列誤検出 | §7 識別子単位 |
| C-19 (LOW) | BindingExpectation の値 copy の位置づけ | §2.1 注記（LEARNED = readback） |

- 陽性対照で**注入した** 4 欠陥（PC-06-E/F/G/H）は本 doc の実体には存在しない（盲検 reviewer の C-01〜C-04 は注入欠陥の検出）。

- **v0.2.2 fold（2026-09-04 15:41 UTC）— 3 軸独立レビュー（reviewer A / A2〔Opus〕/ B / B2〔Opus〕・別 context・v0.2.1 対象）の finding のうち本 doc に帰属するものを fold**。verdict 列 = 独立 verifier の判定（未了なら明記）と起草者の再検証（各 finding の前提文が本 doc に実在することは本 fold script の anchor assert で機械確認）。全 finding の一覧・処置 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`。軸 C（deployment・reviewer C）は v0.2.2 を対象に実施し v0.2.3 で fold（下表の次）:

| finding | 内容 | 変更節 | verdict |
|---|---|---|---|
| A-06 / A2-09 (LOW) | §2.3 反循環文が字義的に自己矛盾（`SkillActionId` を内包しない ↔ `binding_expectations[].skill_action_id`） | §2.3 を構造 pattern（自身から導かれる hash を preimage に置かない）で言い換え | A-06=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED; A2-09=refuted（NOT_A_DEFECT） |
| A2-03 (MEDIUM) | §3 表の `P_RESOURCE_UNATTESTED` trigger が削除済 field `attested_by` を参照 | §3 表 cell を §2.1 注記（evidence store 照会）へ同期 | A2-03=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED |
| B-M7 (MEDIUM) | §5 / PT-13「活性 lease 中の失効 ⇒ lease 無効化」に 05 側の検出点・遷移が無い | §5・PT-13 を保守既定（検出 = 次 permit 発行時・曝露 ≤ 1 skill・05 OP-19）へ同期 | B-M7=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| B2-01 / B-H3 / A-01 / B2-14 / B-M9 / B2-15 / B-L2 / B2-13 (05 由来) | 05 v0.2.2 が `TimingBinding` に足した 6 field の出所 | §2.1 `RuntimeTimeouts` += `safety_heartbeat_timeout_s` / `decision_max_age_s` / `boundary_dwell_s` / `max_reselect_attempts` / `command_kind_mismatch_max` / `inter_command_jitter_s`・§3 `P_TIMEOUT_NONPOSITIVE`・§5 写像文 | B2-01=CONFIRMED（CRITICAL）/ v0.2.2 fold = RESOLVED; B-H3=CONFIRMED（HIGH）/ v0.2.2 fold = RESOLVED; A-01=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置; B2-14=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置; B-M9=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED; B2-15=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED; B-L2=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED; B2-13=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED |
| A-03 / A2-10 (MEDIUM / LOW) | 不在主張の範囲が広すぎ・package 外 scratch（critic 報告）を根拠に引用 | §6.2 を再現 command + 範囲限定（EP md / JSON）へ | A-03=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED; A2-10=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| A-09 / A2-11 (LOW) | x-mask 時刻（01:5x） | header・§11 を file mtime 実測へ | A-09=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED; A2-11=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| A2-12 / B-L5（05 側で fold） | `validate_outcome` 失敗経路 | 本 doc 変更なし（05 §3.7） | A2-12=CONFIRMED（LOW）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置; B-L5=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |

- **v0.2.3 fold（2026-09-04 20:47 UTC）— verifier verdict の反映（上表 verdict 列）・PARTIAL 残差（A-01 / B-M5 → §5、B-M7 → §8.1 規則 (3)）・軸 C finding の fold**。verifier C（3 lens）の verdict 列 = `11_` §3 と同一:

| finding | 内容 | 変更節 | verdict |
|---|---|---|---|
| CD-01 | timeout に上限が無く安全機構を無効化できる | §3 `P_TIMEOUT_ORDER`・§6.1 MIN_FAULT_INJECTION・(x)・OPP-11 | CONFIRMED（HIGH） |
| CD-02 | clearance_roles の被覆・GATEWAY_CONFIG_MATCH 必須が無い | §2.1・§3 `P_CLEARANCE_ROLE_MISSING`・05 §5.4 | CONFIRMED（MEDIUM） |
| CD-03 | evidence の失効・subject 単位が未執行 | §3 `P_EVIDENCE_UNBOUND` 再定義・`P_EVIDENCE_EXPIRED`・`P_FAULT_CODE_UNKNOWN`・§8.1 | CONFIRMED（HIGH） |
| CD-04 | predicate / evaluator / tcp_offset が名前参照のみ | §2.1 `predicate_sha256` / `evaluator_sha256`・§3・05 §3.4 (j) | CONFIRMED（HIGH） |
| CD-05 | SCRIPTED / WAIT の expectation 評価が未定義・lease 前提に無い | §2.1・§3・05 §3.4 (g) | CONFIRMED（MEDIUM） |
| CD-06 | offer の ownership が cell 宣言と照合されない | §3・05 §3.4 (h) | CONFIRMED（MEDIUM） |
| CD-07 | 空虚な envelope が通る・force / torque が admission 項 | §2.1・§3・§4・(xi)・OPP-5 | CONFIRMED（MEDIUM） |
| CD-08 | 自由文字列 kind / representation | §2.1 enum・§3 REQUIRED_CALIBRATION_KINDS | CONFIRMED（MEDIUM） |
| CD-09 | identity を確認する health check が無い | §2.1 CONTROLLER_IDENTITY・§3 必須集合 | CONFIRMED（MEDIUM） |
| CD-10 | lease の時間上限が無い | §2.1 `lease_max_duration_s`・§5・PT-13・05 INV-33 | CONFIRMED（MEDIUM） |
| CD-11 | 11_ 不在・SHA256SUMS 陳腐・verifier 未了の明示 | header・`11_` 追加・SHA256SUMS 再生成 | CONFIRMED（MEDIUM） |
| CD-12 | None 鮮度の二重定義 | 05 §4.2（06 が SSOT） | CONFIRMED（LOW） |
| CD-13 | INV-22 列挙漏れ | 05 INV-22・§4.1 | CONFIRMED（LOW） |
| CD-14 | P_INTRINSIC_OVERRIDE が到達不能・常時 True bool | §3 再定義・§2.1 注記 | CONFIRMED（LOW） |
| CD-15 | profile_label が hash-visible | §2.2 注記・OPP-12 | CONFIRMED（LOW） |
| CD-16 | evidence record が audit に束縛されない | §6.1・§6.3 | CONFIRMED（LOW） |
| CD-17 | registry / 受理権限が未定義 | §8.1・OPP-13・05 §3.4 (i) | CONFIRMED（LOW） |
| CD-18 | workspace 項が点評価のみ | §4・OPP-14・05 §4.3 | CONFIRMED（LOW） |

- **v0.2.4 fold（2026-09-04 23:00 UTC）— v0.2.3 本文への再レビュー round（R1 / R2 → V1 / V2）の確定 finding を fold**。記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md` §7:

| finding | 内容 | 変更節 | verdict |
|---|---|---|---|
| R1-04 / R2-05 | SAFETY の clearance role が 05 で必須・06 で任意 | §2.1・§3・PT-22 | R1-04=CONFIRMED（MEDIUM）; R2-05=CONFIRMED（MEDIUM） |
| R1-05 / R2-03 | content hash の照合が 3 参照のみ | §3（全宣言 hash）・PT-27 | R1-05=CONFIRMED（HIGH）; R2-03=CONFIRMED（HIGH） |
| R1-06 / R2-19 | ZOH で点評価 | §4 | R1-06=CONFIRMED（MEDIUM）; R2-19=CONFIRMED（LOW） |
| R1-15 / R2-12 | §8.1 規則 (3) の「のみ」 | §8.1 | R1-15=CONFIRMED（LOW）; R2-12=CONFIRMED（LOW） |
| R2-01 | timeout 束縛の迂回（別経路・欠落 code・順序漏れ） | §3 `P_TIMEOUT_ORDER`・§6.1 | R2-01=CONFIRMED（MEDIUM） |
| R2-02 | fault / health evidence の内容未検証 | §3 `P_FAULT_EVIDENCE_UNVERIFIED`・PT-28 | R2-02=CONFIRMED（MEDIUM） |
| R2-04 | 単一 robot しか表現できない（DUAL-ARM 不変前提） | §2.1 `ArmSpec`・§3 `P_ARM_COVERAGE`・§4・PT-29・OPP-15 | R2-04=CONFIRMED（HIGH） |
| R2-06 | constant-True evaluator が通る | §3 negative-control・OPP-9 | R2-06=CONFIRMED（MEDIUM） |
| R2-07 | BEFORE_PERMIT の evidence が lease_id 必須で不成立 | §6.1 | R2-07=CONFIRMED（LOW） |
| R2-08 | profile の失効経路が無い | §8.1・OPP-13 | R2-08=CONFIRMED（MEDIUM） |
| R2-09 | ISL の identity が無い | §2.1 `safety_layer_ref`・SAFETY_LAYER_IDENTITY・PT-30 | R2-09=CONFIRMED（MEDIUM） |
| R2-10 | (xi) の predicate 空虚化検査が空振り | — 適用せず | R2-10=refuted（NOT_A_DEFECT） |
| R2-11 | P_ENVELOPE_EXCEEDS_MEASURED の評価点 | §3 | R2-11=CONFIRMED（LOW） |
| R2-13 | frame_ref の default | §2.1 | R2-13=CONFIRMED（LOW） |
| R2-14 | evidence policy の循環（非単調は 1.0 で表現不能） | §3 `P_EVIDENCE_POLICY_CIRCULAR`・PT-31 | R2-14=CONFIRMED（LOW） |
| R2-15 | genesis の role | §2.1 | R2-15=CONFIRMED（LOW） |
| R2-16 | singleton kind の subject | §6.1 | R2-16=CONFIRMED（LOW） |
| R2-17 | evaluator の実行直前再検証 | §2.1 | R2-17=CONFIRMED（LOW） |
| R2-18 | 無期限 calibration / acceptance | §3 `P_VALIDITY_UNBOUNDED`・PT-32 | R2-18=CONFIRMED（LOW） |

- **v0.2.5 fold（2026-09-05 01:33 UTC）— Rs 裁定 2026-09-04（GPT5.6sol 推奨を採用・`review_records/rs_consult/`）**: 推奨 4 件を全件採用（前提訂正 5 点は照合済・全て正）。凍結 schema delta = 0:

| 項目 | 内容 | 変更節 |
|---|---|---|
| 裁定 OPP-15 B+ | `CellKinematicLayoutRef`・`ArmSpec.base_transform_id` / `gripper_resource_id`・`InterArmRestrictionSet`・DUAL-ARM 能力必須・negative controls | §2.1・§2.2・§3（`P_ARM_CAPABILITY_MISSING` / `P_ARM_BASE_UNBOUND` / `P_INTER_ARM_RESTRICTION_MISSING`）・§6.1 MIN_NEGATIVE_CONTROLS・PT-33 / 34 / 38・OPP-15 / 17 |
| 裁定 OPP-11 | `CellSafetyTimingBaseline`（外部・content-addressed）・`P_TIMEOUT_CEILING` / `P_SAFETY_BUDGET_EXCEEDED`・順序の追加 2 件 + `decision_max_age_s ≤ permit_ttl_s` 撤回 | §3・§8.3・PT-35 / 36・OPP-11 / 16 |
| 裁定 OPP-13 | `ProfileRegistry` + `ProfileAcceptanceRecord`（state / generation / two-key）・`P_ACCEPTANCE_RECORD_INVALID` | §8.1 (2)・§8.3・PT-37・OPP-13 |
| 裁定 OP-19 | CLOSED_LOOP lease の validity deadline + event 無効化 + 根拠付き周期診断（SHADOW は次 permit） | §5 (b)・PT-13・§8.3 diagnostic_items |

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
16. 機械検査（`check_review_candidate.py`）= FAIL 0（v0.2.2 の実測出力は `11_THREE_AXIS_REVIEW_RECORD_20260903.md`）。C2 WARN は heuristic で、いずれも「1 行に複数 locus を並べた表の行」か「frozen 行を型根拠として引き、同じ行で本 doc の新語（`P_*` / `profile_hash` 等）を導入した行」— 引用先の内容は起草時に sed で確認済み（§1 表・§3 表・§12）。
