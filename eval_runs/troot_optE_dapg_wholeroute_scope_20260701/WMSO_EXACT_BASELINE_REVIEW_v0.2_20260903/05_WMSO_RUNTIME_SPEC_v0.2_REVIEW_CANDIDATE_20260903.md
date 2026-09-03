# WMSO boundary-only runtime（TERMINAL boundary・checkpoint 切替なし）— RUNTIME SPEC (v0.2 REVIEW CANDIDATE)

- node: `T-WMSO`; 起草 = Claude Code web session（review candidate 起草・**authority 無し**・凍結物へ非接触）; 作成 = 2026-09-03（UTC）
- status: **REVIEW CANDIDATE v0.2（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）**
- 土台（凍結・編集しない・4 file）: contracts_v2 DESIGN v2.11.2 `00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff` @ `54f90a7de1e02fb14eaf793bf3c60d9503d0d82e` ／ EP v1.9 md `c474acea7c58acc22050c2ad9944fd45a18f5c76967964b42d11922e28fa27e7` ／ EP JSON v1.9 `e63176af9bc3a246b1c32db369ec59f8d09a4c96c381bb03a3a6024bd9811c6e`（definition hash `e7ca43093084c167a209b008533a66d26a1fd3223d2a3c11274d28306c3ff803`）／ tensor_binding DESIGN v13 `5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6` @ `07250f4a0208b3bbd27eae6fef7d980743c4b538`
- 前提文書: D0 architecture（EXIT GRANTED）／ Rs C3 裁定（slice EP evidence profile = SHADOW rank 2・非 authority；execution profile は別軸・未裁定）／ handoff 決定（2026-09-03）
- ⛔ impl / training / closed-loop authority / production / push / freeze / slice = CLOSED 継続。本 doc は設計書面のみ。
- 系譜: 起草 draft A（角度 = AUTHORITY-SAFETY-FIRST・11:20 UTC 実測）→ critic 報告（`07_critic_report.md` X1 / X2 / §3.3）の fold → **本版（16:4x UTC）**。synthesis record = §13。⚠ judge panel（3 draft × 2 judge）は session 上限で未実施 — §13 に honest に記録。`$D` = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701`。

## 0. 中心構造

```text
Frozen（不変・参照のみ）:
  Static/Cert/Elig/Authority: SkillDefinition → certify_definition → evaluate_usage_eligibility → evaluate_authority_grant → AuthorityDecision
  Runtime 型:   SkillInvocation / SkillOutcome / HandoffOffer{handoff_offer_id, control_epoch, ownership} / TransitionRecord / SchemaVersionStamp
  Runtime val.: validate_invocation_start(…, now) / validate_outcome / validate_handoff(…, authority_epoch_snapshot) … certificate を無効化しない
  値語彙:       BeliefRef{value: SnapshotRef | HashRef}/ Ownership / ProducerOutcome / ControlMode / FreshnessPolicy
  boundary:     TERMINAL outcome のみ（slice prereg）。InterruptOutcome = 受理 + HOLD（checkpoint 切替 = 無効・別 gate）
  D1.1-B:       TimingSpec / ActionTimingSpec{action_rate_hz, hold} / ActionBinding{bounds, action_scale, control_mode} / tensor_binding_hash

Runtime 層（本 doc・新語・凍結 schema 外）:
  AuthorityManager      AuthorityState = (owner, control_epoch, active_lease_id, consumed_offer_ids) の唯一 writer。遷移 = AuthorityCas のみ
  CommandGateway        actuation への唯一経路。admission = (lease_id, control_epoch) の等値 + AcceptedEnvelope 連言。既定出力 = SafeHold
  Orchestrator          boundary で BeliefRef から再選択。ReadinessAck を取り、CommitPermit を要求する（状態は持たない）
  Executor              1 lease = 1 executor = 1 invocation。D1.1-B の rate/hold で command を出す
  IndependentSafetyLayer D0 §F。gateway 出力に対し優先・ack を待たない・permit を void する
  RecoveryRoutingPolicy 外部 interface。候補 skill_action_id 列だけを返す（選択論理 = OUT）
  AuditRecorder         RuntimeAuditRecord（SchemaVersionStamp 再利用・hash 方式 = frozen U14 defer）

規範順序:
  ReadinessAck（次 executor）→ CommitPermit（one-shot・失効付き）→ AuthorityCas（owner・epoch・lease・consumed offer を 1 CAS）
     ├ 新 owner/epoch 活性   ├ 旧 epoch 拒否（同一線形化点）   └ SafeHold 活性（最初の安全 command）
  → HealthConfirmation（失敗 = SafeHold 継続 + disposition。旧 owner は復活しない）
```

## 1. 前提と再利用する凍結語彙

本 doc は frozen 4 file に **schema delta を導入しない**（D1.1-B が自らに課したのと同じ規律 — `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:4` 「frozen 3 file を編集せず・schema delta を導入しない」）。frozen enum に member を追加しない（pS C-1 — `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:5`）。再利用する凍結語彙と、本 doc が依拠する読み方を以下に固定する。

| 凍結語彙（verbatim） | 定義 locus | 本 doc での使用 |
|---|---|---|
| `SkillInvocation`（`control_epoch: int` を持つ） | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:477-486` | lease が束縛する invocation。`skill_action_id` は certified のみ（`:480` 注記） |
| `SkillOutcome`（`outcome: ProducerOutcome`） | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:488-494` | boundary の到達信号（§6） |
| `HandoffOffer`（`handoff_offer_id` / `control_epoch` / `ownership`） | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:496-506` | 消費単位 = `handoff_offer_id`（`:498` 「authority manager の使用済み拒否（replay 防止）単位」） |
| `TransitionRecord` / `SchemaVersionStamp` | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:508-529` | audit の join key（`episode_id` / `invocation_id`）と stamp 再利用（§8） |
| `BeliefRef` = {value: SnapshotRef \| HashRef, t_obs, ttl, confidence, ood_flag} / `Ownership` / `ProducerOutcome` / `FreshnessPolicy` / `FailClosedAction` | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151` | belief 参照は全て `BeliefRef`（新 belief 参照型は作らない）。`ProducerOutcome` は不変（§7） |
| `AuthorityDecision` = {granted, denials, inputs の hash/ref 束縛} / `evaluate_authority_grant` | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:345-352` | CLOSED_LOOP_AUTHORITY lease の必要条件（§4） |
| 「closed-loop 実運転権限は本 API の granted == True を必要条件とする（十分条件ではない）」 | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:354` | lease は必要条件を検査するのみ。本 doc は authority を付与しない |
| `validate_invocation_start(invocation, definition, belief, now)` — `now` 明示引数 | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:372-373` | boundary 再選択の必須 leg（§6） |
| `validate_handoff(…, authority_epoch_snapshot: int)` — snapshot は authority manager が読み取り明示引数で渡す | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:375-378` | CAS 前の等値検査（§3 R1） |
| `offer.control_epoch == authority_epoch_snapshot`（等値検査のみ、不一致 = `E_HANDOFF_EPOCH_STALE`） | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:381` | 等値ゆえ **CAS 前**に検査し、消費は **CAS 内**（§3.6） |
| 責務分離: 「epoch の CAS 更新・新 epoch 発行・旧 epoch command 拒否・使用済み offer 拒否（`handoff_offer_id` 単位）・snapshot 読出し = authority manager（O0 層）」 | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382` | AuthorityManager / CommandGateway の責務の凍結側根拠（§2） |
| `validate_invocation_start` = initiation predicate / freshness_policy（明示 `now`）/ required_control_resources vs 実 ownership（**required ⊆ offered**） | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:380` | lease.ownership の包含条件（§4） |
| `ControlMode` = DIFF_IK_EE_TARGET \| SCRIPTED_SEQUENCE \| WAIT | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:62` | gateway の command 種別照合（§5） |
| §5C strict codec（unknown field 拒否） | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:385` | runtime 型を frozen 型へ混入させない根拠（INV-16） |
| §7-2: certified `SkillActionId` のみ / runtime 記録の content-hash 化は WCJ 対象外・方式 defer（U14） | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:537` | lease 候補 = certified のみ。audit hash = defer（§8） |
| D1.1-B `TimingSpec`（`max_obs_staleness_s` = 訓練時仮定。runtime 鮮度 = frozen `FreshnessPolicy`） | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:96-99` | timing 等値束縛と鮮度の役割分離（§4） |
| D1.1-B `ActionTimingSpec` {`action_rate_hz`, `hold`} / `ActionBinding` {`control_mode`, `action_scale`, `timing`} | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:125-134` | executor の実行周期 = 等値（R5） |
| 全 action feature は `bounds` 必須 | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:138` | AcceptedEnvelope の第 1 項（§4） |
| U-1: B は epoch field を持たない。stale-epoch 検査は frozen §7 runtime | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:374` | epoch は runtime 層の状態（binding へ持ち込まない） |
| EP: 「SHADOW（非 authority）」／「SHADOW は定義上 非 authority」／ usage matrix = ceiling | `$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:136` ／ `$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:155` ／ `$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:156` | lease mode の根拠（§4 R2） |
| EP JSON `usage_ceiling.closed_loop_authority` = evaluate_authority_grant conjuncts / CLOSED_LOOP `external_conjuncts` | `$D/WMSO_EvidencePolicy_v1.9.json:213` ／ `$D/WMSO_EvidencePolicy_v1.9.json:199` | CLOSED_LOOP_AUTHORITY lease の必要条件の凍結側列挙 |
| D0 §E: offer → accept → commit \| abort、`control_ownership` の単一 writer・one atomic token flip、CAS/lock は D1 refinement | `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:267-274` | AuthorityCas の前身（本 doc は「D1 refinement」を runtime 層で具体化） |
| D0 §F: 独立 safety monitor、priority over WMSO、preemption acts first / does not wait for ack、heartbeat missed ⇒ safety alive を仮定しない | `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:310-319` | IndependentSafetyLayer（§2, §5） |
| D0 §G: 単調 clock（`CLOCK_MONOTONIC`）・単一 origin、`D_event` 等は provisional・RT0 で測る | `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:354-359` | timeout は profile parameter（数値を書かない） |
| Rs C3: slice の EP evidence profile = SHADOW（rank 2・非 authority）。execution profile は別軸・未裁定 | `$D/WMSO_RS_C3_RULING_SLICE_PROFILE_20260720.md:5` ／ `$D/WMSO_RS_C3_RULING_SLICE_PROFILE_20260720.md:65` | 本 doc は評価 profile と execution profile を混同しない（§11 R3） |
| slice prereg: boundary = skill 終端（TERMINAL outcome）のみ。checkpoint 途中切替 = 別 gate | `$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59` | §6 の boundary 種別の既定 |

読み方の固定（本 doc 全体で有効）:

1. **validate_handoff は等値検査**である（`:381`）。単調性・再利用拒否は validator では保証できず authority manager の状態所有責務（`:382`）。⇒ 本 doc の AuthorityManager がその責務の runtime 側 owner。
2. **`max_obs_staleness_s` は runtime 鮮度ではない**（`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:99`）。runtime 鮮度 = frozen `FreshnessPolicy.max_staleness_s`（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151`）を profile が stricter-or-equal に narrow したもの。
3. **EP profile（CLOSED_LOOP / SHADOW / OFFLINE_REPLAY）は evidence profile**であり execution profile（boundary-only / real-time）とは別軸（`$D/WMSO_RS_C3_RULING_SLICE_PROFILE_20260720.md:5`）。本 doc は boundary-only（TERMINAL boundary）の **execution mode を仕様化するだけ**で、execution-profile 軸の裁定を行わない（§11）。
4. certified `SkillActionId` のみ runtime に入る（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:537`）。Draft は lease 候補になれない。
5. runtime validation は certificate を無効化しない（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:39`）。本 doc の fault / disposition も certificate に触れない。

## 2. Runtime 構成要素と責務分離

| 構成要素（新語） | 責務（本 doc） | 持つ状態 | 凍結側の根拠 |
|---|---|---|---|
| **AuthorityManager** | `AuthorityState` の唯一 writer。`AuthorityCas` の実行、`CommitPermit` の発行/失効/一回性、`authority_epoch_snapshot` の読出し提供、`consumed_offer_ids` の保持、restart 時の fail-closed 復帰 | `AuthorityState`（durable）+ permit 台帳 | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382`（CAS 更新・発行・旧 epoch 拒否・使用済み offer 拒否・snapshot 読出し = O0 層） |
| **CommandGateway** | actuation への唯一経路。admission = `(lease_id, control_epoch)` 等値 ∧ `AcceptedEnvelope` 連言 ∧ command 種別 = lease.control_mode。既定出力 = `SafeHold`。SHADOW lease の actuation port = DISABLED | admission 用の `AuthorityState` 読み（線形化）+ 直近 admitted command | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382`（旧 epoch command 拒否）; D0 `control_ownership` 単一 writer `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:270-272` |
| **Orchestrator** | boundary で `BeliefRef` から候補を再選択（`initiation_predicate` 保持候補の filter・frozen validator を呼ぶ）。`ReadinessAck` を取り、`CommitPermit` を要求し、`AuthorityCas` を依頼する。**状態を持たない**（authority を書かない） | なし（audit へ記録のみ） | D0 §D `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:207-215`（candidate filter / select / replan / OOD abstention） |
| **Executor** | 1 invocation の skill runtime instance。`ReadinessAck` を返し、lease 活性後に D1.1-B の rate/hold で command を出し、`HealthConfirmation` を返す | 自身の lease copy（読みのみ） | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:125-127`（`action_rate_hz` / `hold`） |
| **IndependentSafetyLayer** | D0 §F。gateway 出力への優先介入（STOP/HOLD/RETRACT/FORCE_LIMIT）、heartbeat、`stabilized_post_action_state`。ack を待たない | 独立（本 doc は interface のみ） | `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:317-320` |
| **RecoveryRoutingPolicy**（外部） | `RecoveryRoutingQuery` → 候補 `skill_action_id` 列 + rationale ref。選択論理は本 doc の外 | 外部 | D0 §E 4 option の 3（Recovery Skill; option 1 = compatible `SkillHandoffState` での direct handoff）`$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:243-247`; Recovery skill は同じ `SkillLifecycleContract` を持つ ordinary skill `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:280-281` |
| **AuditRecorder** | `RuntimeAuditRecord` の append-only 記録。`SchemaVersionStamp` を再利用 | 記録列（seq 単調） | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:524-529`（`SchemaVersionStamp`） |

Home matrix（handoff 決定 D を凍結根拠付きで固定。本 doc は各 home を再決定しない）:

| item | home（v0.2） | 本 doc の節 | 根拠（凍結・裁定） |
|---|---|---|---|
| 現在状態からの再選択・再初期化 | runtime / Orchestrator | §6 | D0 §D replan on outcome/event `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:210` |
| 出力 null 準備 | runtime process / authority 分離（CommandGateway `SafeHold`） | §5 | D0 §E `reject` / `abort` / `timeout` ⇒ producer retains + safe-stop、「control is never released into a vacuum and never duplicated」`$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:273-274` |
| owner・epoch 転送 | AuthorityManager / CommandGateway | §3 | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382` |
| intrinsic action bounds・rate・hold | frozen D1.1-B（参照のみ・再定義しない） | §4 | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:138`（`bounds` 必須）; `:125-127`（`action_rate_hz`/`hold`） |
| cell / controller / tool / payload 条件 | `IndustrialDeploymentProfile`（doc 06・外部） | §4（`profile_hash` 参照） | 凍結 4 file に該当語彙なし（EP md/json で `controller`/`calibrat`/`deploy` = 0 hit — 03 map §6(e)）⇒ 外部 |
| initiation 制約 | profile = monotone strengthening のみ | §4 | frozen `InitiationSpec` は静的契約 `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151`; 緩和は certificate 前提を壊すため不可 |
| recovery skill 選択経路 | 外部 `RecoveryRoutingPolicy`（interface のみ） | §6 | D0 §E `Recovery Skill` = 「must be designed; ABSENT today」`$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:246` |
| continuation / recovery 判断 | runtime assessment（`RuntimeAssessmentRecord`・非 certified） | §6 | frozen `recovery_rollback_target` は loud-discard・再導入は schema bump `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:148` |
| mid-skill interruptibility / atomic region | CLOSED（future static candidate） | §11 | slice = TERMINAL のみ・checkpoint 途中切替 = 別 gate `$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59` |
| skill-specific safe-hold 保証 | future static candidate | §5, §12 | frozen `FailClosedAction` = {RE_OBSERVE, SAFE_STOP, HANDBACK_TO_OWNER} に hold の物理形は無い `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151` |
| composition（ParallelRegion / arity / dual-arm 同時 executor） | 別 indivisible delta（OUT・pX court / Rs） | §11 | tensor_binding は arity 非依存で freeze（02 map FREEZE:39）; 合成容器語彙 = 凍結 3 file で 0 hit（05 map §7） |

## 3. Authority state machine（owner・`control_epoch`・ReadinessAck・`CommitPermit`・`AuthorityCas`・`ActiveAuthorityLease`・`HealthConfirmation`）

本節は本 doc の中心である。先に不変量と証明の骨格を置き（§3.1）、次にそれを成立させるために必要な型（§3.2–§3.5）、遷移（§3.6）、失敗経路（§3.7）、証明本体（§3.8）を書く。

### 3.1 中心不変量（証明対象）

- **P1 no-double-ownership**: 任意の線形化点で、actuation を駆動し得る lease は高々 1 つ（`AuthorityState.active_lease_id`）。異なる 2 lease の command が同一 `AuthorityState` の下で admit されることは無い。
- **P2 no-orphan-output**: 任意の瞬間、CommandGateway の出力は {活性 lease の admitted command（hold 地平内）, SafeHold, SafeStop, IndependentSafetyLayer の決定出力} のちょうど 1 つで定義される。「command owner 不在」の瞬間は無い（D0 「no owner-gap interval」`$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:270-272` の runtime 側実現）。
- **P3 replay/stale 遮断（R1）**: 同一 `handoff_offer_id` は 2 度消費されない。epoch が動いた後に旧 snapshot で通った validation が commit されることは無い。
- **P4 一回性**: `CommitPermit` は高々 1 回の `AuthorityCas` にしか使えず、失効後は使えない。
- **P5 単調・非復活**: `control_epoch` は CAS 成功ごとにちょうど +1。無効化された lease_id が再び活性になることは無い（旧 owner は復活しない。再選択は必ず新 lease・新 epoch）。

### 3.2 `AuthorityState`（AuthorityManager の唯一状態）

```python
# 新語（runtime 層のみ・凍結 schema 外）
class OwnerKind(Enum): SAFEHOLD | EXECUTOR          # SAFEHOLD = CommandGateway 自身が SafeHold を保持（executor 不在の「定義された owner」）
class SafeHoldReason(Enum): INITIAL | BOUNDARY_WAIT | TRANSFER | HEALTH_FAIL | NO_CHAIN | EXECUTOR_LOST | MANAGER_RESTART | DEADLINE_MISS | ENVELOPE_VIOLATION | SAFETY | SAFE_STOP | CHECKPOINT_DISABLED

@dataclass(frozen=True)
class OwnerRef:                                       # 新語
    kind: OwnerKind
    executor_id: str | None                           # EXECUTOR ⇔ 非 null / SAFEHOLD ⇔ null

@dataclass(frozen=True)
class AuthorityState:                                 # 新語 — CAS の比較・交換単位（tuple 全体）
    owner: OwnerRef
    control_epoch: int                                # frozen SkillInvocation.control_epoch / HandoffOffer.control_epoch と同じ int 領域。CAS 成功ごとに +1
    active_lease_id: str | None                       # owner.kind == EXECUTOR ⇔ 非 null
    consumed_offer_ids: frozenset[str]                # frozen HandoffOffer.handoff_offer_id の消費済み集合（CAS tuple の一部）
    safehold_reason: SafeHoldReason | None            # owner.kind == SAFEHOLD ⇔ 非 null
    seq: int                                          # CAS 成功ごとに +1（durable 化の単調 key）
```

- `AuthorityState` は **durable**（AuthorityManager の再起動をまたぐ）。読出しは `read_snapshot() -> AuthorityState` で行い、frozen `validate_handoff` の `authority_epoch_snapshot` 引数にはこの `control_epoch` を渡す（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:377-378`）。
- 初期状態 = `(SAFEHOLD, epoch=e0, None, ∅, INITIAL, 0)`。`e0` は durable 記録から復元（記録が無い初回のみ 0）。

### 3.3 `ReadinessAck`（次 executor の準備 ACK — owner 転送より前）

```python
@dataclass(frozen=True)
class ReadinessAck:                                   # 新語 — 転送の第 1 前提条件
    ack_id: str
    executor_id: str
    invocation_id: str                                # 候補 frozen SkillInvocation.invocation_id
    skill_action_id: str                              # certified のみ（frozen §7-2）
    expected_control_epoch: int                       # = snapshot.control_epoch + 1（ack 時点の snapshot に基づく期待値）
    handoff_offer_id: str | None                      # 消費予定 offer（SAFEHOLD からの起動 = null）
    lease_proposal_id: str                            # 提案 lease（未活性）の runtime-local id
    envelope_readback_ok: bool                        # executor が AcceptedEnvelope / TimingBinding を読み戻し等値確認した
    t_ack: float                                      # 単調 clock（D0 §G）
    valid_until: float                                # = t_ack + profile.ack_validity_s
```

- ACK は「候補 invocation + 期待 epoch + 消費予定 offer + lease 提案」に束縛される。いずれかが変われば ACK は無効（`R_ACK_MISBOUND`）。
- ACK を持たない転送は存在しない（`CommitPermit.ack_id` が非 null 必須）。

### 3.4 `CommitPermit`（pre-commit・one-shot・失効付き）

```python
@dataclass(frozen=True)
class CommitPermit:                                   # 新語 — pre-commit。ActiveAuthorityLease（post-commit）と分離
    permit_id: str
    ack_id: str                                       # ReadinessAck 束縛（必須）
    expected: AuthorityState                          # CAS の比較対象 = 発行時 snapshot（tuple 全体）
    handoff_offer_id: str | None                      # expected.consumed_offer_ids に含まれないこと
    handoff_validation_report_ref: str | None         # frozen HandoffValidationReport（issues 空）— snapshot = expected.control_epoch で評価済み
    invocation_validation_report_ref: str             # frozen LifecycleValidationReport（issues 空）— now を明示
    authority_decision_ref: str | None                # proposed_lease.mode == CLOSED_LOOP_AUTHORITY ⇔ 非 null ∧ granted == True
    profile_hash: str                                 # IndustrialDeploymentProfile（doc 06）
    proposed_lease: ActiveAuthorityLease              # 未活性。proposed_lease.control_epoch == expected.control_epoch + 1
    issued_at: float
    expires_at: float                                 # = issued_at + profile.permit_ttl_s
```

- AuthorityManager は permit を `UNUSED | CONSUMED | VOID` の 3 状態で保持する。`CONSUMED` は CAS 成功の同一線形化点でのみ設定される。`VOID` = 失効 / 安全介入 / CAS 失敗。
- 同一 `expected` に対し複数の permit が並存してもよい（候補競合）。しかし CAS 成功は高々 1 つ（§3.8 証明 D）。

### 3.5 `AuthorityCas` と `HealthConfirmation`

```python
class CasKind(Enum): TRANSFER_TO_EXECUTOR | TRANSFER_TO_SAFEHOLD
class CasResult(Enum): SUCCESS | CONFLICT | REJECTED

@dataclass(frozen=True)
class AuthorityCas:                                   # 新語 — 唯一の状態遷移操作（記録形）
    cas_id: str
    kind: CasKind
    permit_id: str | None                             # TRANSFER_TO_EXECUTOR ⇔ 非 null
    expected: AuthorityState                          # 比較対象（tuple 全体の等値）
    new_owner: OwnerRef
    new_lease_id: str | None                          # TRANSFER_TO_EXECUTOR ⇔ 非 null
    consume_offer_id: str | None
    safehold_reason: SafeHoldReason | None            # TRANSFER_TO_SAFEHOLD ⇔ 非 null
    t_attempt: float
    result: CasResult
    fault: RuntimeFaultCode | None                    # REJECTED / CONFLICT の理由

@dataclass(frozen=True)
class HealthConfirmation:                             # 新語 — post-commit
    lease_id: str
    control_epoch: int
    executor_liveness: bool
    envelope_selfcheck: bool                          # executor 側の AcceptedEnvelope / TimingBinding 読み戻し一致
    first_command_admitted: bool                      # CLOSED_LOOP: 最初の admissible command が gateway で admit された / SHADOW: 記録された
    profile_health_checks: tuple[tuple[str, bool], ...]   # doc 06 HealthCheckSpec の結果（id, ok）
    t_confirm: float
```

**`AuthorityCas` の意味論（TRANSFER_TO_EXECUTOR）** — 以下を **1 つの線形化点**で行う。どれか 1 つでも満たされなければ状態は一切変わらない。

前提条件（全て AND・不能判定 = FALSE）:
1. `read_current() == cas.expected`（tuple 全体等値: owner / control_epoch / active_lease_id / consumed_offer_ids / safehold_reason / seq）。
2. `permit.state == UNUSED ∧ now < permit.expires_at ∧ permit.expected == cas.expected`。
3. `ack = resolve(permit.ack_id)`: `ack.expected_control_epoch == expected.control_epoch + 1 ∧ now ≤ ack.valid_until ∧ ack.invocation_id == permit.proposed_lease.invocation_id ∧ ack.handoff_offer_id == permit.handoff_offer_id ∧ ack.envelope_readback_ok`。
4. `cas.consume_offer_id ∉ expected.consumed_offer_ids`（offer がある場合）。
5. `permit.handoff_validation_report_ref`（offer がある場合）と `permit.invocation_validation_report_ref` が issues 空であり、前者の評価に用いた `authority_epoch_snapshot == expected.control_epoch`。
6. `proposed_lease.mode == CLOSED_LOOP_AUTHORITY ⇒ resolve(authority_decision_ref).granted == True`（frozen の `granted == True` 必要条件 `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:354`）かつ decision の inputs hash/ref 束縛が lease の `skill_action_id` / `profile_hash` に一致。
7. `proposed_lease.accepted_envelope.satisfiable == True`。
8. `proposed_lease.skill_action_id` が certified（certificate 存在）。
9. IndependentSafetyLayer の直近 health ∈ {ok, degraded} かつ未処理の STOP/HOLD 決定が無い（D0 `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:318` heartbeat 欠落 ⇒ alive を仮定しない）。
10. `safehold_reason ∈ {SAFETY, SAFE_STOP, MANAGER_RESTART}` の SAFEHOLD からの転送では、該当する clearance record（§5.4）が存在する。

事後条件（同一線形化点）:
- `AuthorityState := (EXECUTOR(executor_id), expected.control_epoch + 1, new_lease_id, expected.consumed_offer_ids ∪ {consume_offer_id}, None, expected.seq + 1)`。
- `permit.state := CONSUMED`。同じ `expected` に束縛された他の permit は次の CAS 試行で条件 1 を満たさず `CONFLICT`（自動的に VOID）。
- **旧 epoch 拒否が有効化**: CommandGateway の admission は `AuthorityState` を線形化して読むため、この点以降 `control_epoch ≠ expected.control_epoch + 1` の command は `R_EPOCH_STALE_COMMAND`、`lease_id ≠ new_lease_id` の command は `R_LEASE_UNKNOWN_COMMAND`。
- **SafeHold 活性**: gateway 出力は新 lease の最初の admissible command が admit されるまで `SafeHold`（最初の安全 command）。旧 lease の直近 command は hold 地平にかかわらず即座に出力から外れる。
- **旧 lease 無効化**: `expected.active_lease_id` は `LEASE_INVALIDATED` 記録（reason = TRANSFER）。復活経路は存在しない。

**TRANSFER_TO_SAFEHOLD** の前提条件 = 条件 1 のみ（+ `safehold_reason` 非 null）。permit / ack / decision を要さない（SAFEHOLD owner は常に ready で常に安全側）。事後条件 = `(SAFEHOLD, epoch+1, None, consumed そのまま, reason, seq+1)` + 旧 lease 無効化 + 全 UNUSED permit の VOID。

### 3.6 R1 — offer の検証は CAS 前、消費は CAS 内

frozen `validate_handoff` は `offer.control_epoch == authority_epoch_snapshot` の**等値検査**である（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:381`）。producer は旧 epoch `e` の下で offer を出す（`offer.control_epoch == e`）。したがって:

1. Orchestrator は `snapshot = AuthorityManager.read_snapshot()` を取り、`validate_handoff(invocation, offer, producer_def, consumer_def, authority_epoch_snapshot=snapshot.control_epoch)` を **CAS 前**に呼ぶ。`E_HANDOFF_EPOCH_STALE` を含む issues 非空 ⇒ `R_OFFER_INVALID` ⇒ disposition `RESELECT`（offer は捨てる。再検証は新 snapshot で）。
2. 検証を通った offer の `handoff_offer_id` は `CommitPermit.handoff_offer_id` に束縛され、**CAS の tuple 要素 `consumed_offer_ids` として CAS 内で消費**される（§3.5 条件 4・事後条件）。
3. CAS 後の epoch は `e+1` ゆえ、同じ offer を再度 validate すると `E_HANDOFF_EPOCH_STALE`、再度 CAS に載せると `R_OFFER_REUSED`（条件 4）。二重に遮断される。

### 3.7 遷移表と失敗経路

状態（manager 視点。`AuthorityState` と permit 台帳の射影）:

| state | 定義 |
|---|---|
| `S_SAFEHOLD(reason)` | owner.kind == SAFEHOLD |
| `S_LEASE_ACTIVE(mode)` | owner.kind == EXECUTOR ∧ HealthConfirmation 済 |
| `S_HEALTH_PENDING` | owner.kind == EXECUTOR ∧ HealthConfirmation 未 |
| `S_BOUNDARY_WAIT` | `S_LEASE_ACTIVE` のまま producer の `SkillOutcome` 受領済（lease は活性・gateway = SafeHold） |
| `S_TRANSFER_PENDING` | 上記いずれか + UNUSED permit ≥ 1 |

遷移（全て `AuthorityCas` 経由。表外遷移は存在しない）:

| from | 事象 | CAS | to | 記録 |
|---|---|---|---|---|
| `S_SAFEHOLD` / `S_BOUNDARY_WAIT` | ack → permit → CAS 成功 | TRANSFER_TO_EXECUTOR | `S_HEALTH_PENDING` | EPOCH_TRANSITION, LEASE_ACTIVATED, LEASE_INVALIDATED(旧) |
| `S_HEALTH_PENDING` | HealthConfirmation 全 True（timeout 内） | なし | `S_LEASE_ACTIVE(mode)` | HEALTH_CONFIRMED |
| `S_HEALTH_PENDING` | 失敗 / timeout | TRANSFER_TO_SAFEHOLD(HEALTH_FAIL) | `S_SAFEHOLD(HEALTH_FAIL)` | HEALTH_FAILED, FAULT(R_HEALTH_CONFIRM_FAILED \| R_HEALTH_CONFIRM_TIMEOUT), DISPOSITION(HOLD) |
| `S_LEASE_ACTIVE` | `SkillOutcome`（`TerminalOutcome`）受領 | なし | `S_BOUNDARY_WAIT` | ASSESSMENT |
| `S_LEASE_ACTIVE` | `SkillOutcome`（`InterruptOutcome`）受領 | TRANSFER_TO_SAFEHOLD(CHECKPOINT_DISABLED) | `S_SAFEHOLD(CHECKPOINT_DISABLED)` | ASSESSMENT, FAULT(R_CHECKPOINT_SWITCH_DISABLED), DISPOSITION(HOLD) — v0.2 は checkpoint 切替を実行しない（§6.1） |
| `S_BOUNDARY_WAIT` | 候補なし | TRANSFER_TO_SAFEHOLD(NO_CHAIN) | `S_SAFEHOLD(NO_CHAIN)` | DISPOSITION(NO_CHAIN → HOLD \| SAFE_STOP per profile) |
| any (EXECUTOR) | executor heartbeat 喪失 | TRANSFER_TO_SAFEHOLD(EXECUTOR_LOST) | `S_SAFEHOLD(EXECUTOR_LOST)` | FAULT(R_EXECUTOR_LOST), DISPOSITION(HOLD) |
| any (EXECUTOR) | gateway: command deadline miss / envelope 違反 | TRANSFER_TO_SAFEHOLD(DEADLINE_MISS \| ENVELOPE_VIOLATION) | `S_SAFEHOLD(…)` | FAULT, DISPOSITION(HOLD) |
| any | IndependentSafetyLayer STOP / HOLD | TRANSFER_TO_SAFEHOLD(SAFETY) | `S_SAFEHOLD(SAFETY)` | SAFETY_OVERRIDE, PERMIT_VOIDED(全), FAULT(R_SAFETY_OVERRIDE) |
| any | AuthorityManager 再起動 | TRANSFER_TO_SAFEHOLD(MANAGER_RESTART)（durable state からの復帰 CAS） | `S_SAFEHOLD(MANAGER_RESTART)` | MANAGER_RESTART, FAULT(R_MANAGER_RESTART) |

失敗経路（各 timeout / failure に disposition を必ず割り当てる — fail-closed 既定）:

| 失敗 | 検出者 | fault | 状態への効果 | disposition |
|---|---|---|---|---|
| ACK が `ack_timeout_s` 内に届かない | Orchestrator | `R_ACK_TIMEOUT` | 変化なし（現 owner 継続・gateway = SafeHold） | `RESELECT`（次候補）/ 候補尽きれば `NO_CHAIN` |
| ACK の束縛不一致（epoch/offer/invocation） | AuthorityManager | `R_ACK_MISBOUND` | 変化なし | `RESELECT` |
| permit 失効 | AuthorityManager | `R_PERMIT_EXPIRED` | permit VOID | `RESELECT`（ACK から再取得） |
| permit 再使用 | AuthorityManager | `R_PERMIT_REUSED` | 拒否・変化なし | `HOLD`（異常経路・audit 必須） |
| permit 束縛不一致 | AuthorityManager | `R_PERMIT_MISBOUND` | permit VOID | `RESELECT` |
| CAS conflict（expected ≠ current） | AuthorityManager | `R_CAS_CONFLICT` | 変化なし・permit VOID | 現状態に従う（SAFEHOLD なら `RESELECT`、EXECUTOR なら継続） |
| offer 再使用 | AuthorityManager | `R_OFFER_REUSED` | 拒否・変化なし | `RESELECT`（新 offer 待ち）/ 無ければ `HOLD` |
| validate_handoff 失敗（`E_HANDOFF_EPOCH_STALE` 等） | Orchestrator | `R_OFFER_INVALID` | 変化なし | `RESELECT` |
| validate_invocation_start 失敗 | Orchestrator | `R_INVOCATION_INVALID` | 変化なし | `RESELECT` / `RE_OBSERVE`（freshness 起因） |
| 新 executor が CAS 後に crash | gateway/manager | `R_EXECUTOR_LOST` \| `R_HEALTH_CONFIRM_TIMEOUT` | TRANSFER_TO_SAFEHOLD | `HOLD`（旧 owner 不復活） |
| HealthConfirmation 失敗 | AuthorityManager | `R_HEALTH_CONFIRM_FAILED` | TRANSFER_TO_SAFEHOLD(HEALTH_FAIL) | `HOLD`（profile が SAFE_STOP へ強化可） |
| AuthorityManager crash/restart | manager（起動時） | `R_MANAGER_RESTART` | durable state を読み `epoch := persisted + 1`・owner := SAFEHOLD・全 lease 無効・全 permit VOID。durable state 不読 ⇒ 起動拒否 | `HOLD`（不読 = `SAFE_STOP` + operator 介入） |
| 転送中の safety override | IndependentSafetyLayer | `R_SAFETY_OVERRIDE` | 出力は即 safety 決定（ack 不要）。in-flight CAS は線形化順で「先に成功 → 直後の safety CAS で無効化」か「後 → CONFLICT」のいずれか | `HOLD`（STOP なら `SAFE_STOP`） |
| CLOSED_LOOP 要求で decision 不在/未 granted | AuthorityManager | `R_AUTHORITY_DECISION_ABSENT` | 拒否・変化なし | `HOLD`（SHADOW への降格は自動で行わない — 別 permit） |
| SHADOW lease から actuation 要求 | CommandGateway | `R_SHADOW_OUTPUT_ATTEMPT` | 記録のみ・出力なし | 変化なし（lease 継続・audit） |

### 3.8 証明

**証明 A（P1 no-double-ownership）**。`AuthorityState` は AuthorityManager だけが書き、書込みは `AuthorityCas` の線形化点でのみ起こる（§3.2, §3.5）。CommandGateway の admission は `AuthorityState` を線形化して読み、`(cmd.lease_id, cmd.control_epoch) == (state.active_lease_id, state.control_epoch)` を要求する（§3.5 事後条件）。2 つの command `c1`（lease `L1`）と `c2`（lease `L2`, `L1 ≠ L2`）が同一の状態 `s` の下で admit されたと仮定すると、`L1 == s.active_lease_id == L2` となり矛盾。よって同一線形化点で actuation を駆動できる lease は高々 1 つ。lease は `executor_id` を 1 つだけ持つ（§4.1）ため executor についても同じ。D0 の「one atomic token flip … exactly one owner at every instant」（`$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:270-272`）を、`control_ownership` 1 field でなく tuple 全体の CAS として実現している。

**証明 B（P2 no-orphan-output）**。gateway 出力関数 `out(t)` を §5.2 のとおり定義する: (i) IndependentSafetyLayer の未解除決定があればその出力（最優先・D0 `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:319`）; (ii) さもなくば `state.owner.kind == EXECUTOR ∧ mode == CLOSED_LOOP_AUTHORITY` かつ hold 地平内の admitted command があればその command; (iii) さもなくば `SafeHold`（`safehold_reason == SAFE_STOP` なら `SafeStop`）。(i)(ii)(iii) は全域を覆い互いに排他（優先順位で決定的）。CAS の線形化点では (ii) の admitted command 集合が空にリセットされ (iii) に落ちる（事後条件「SafeHold 活性」）ため、転送の瞬間にも出力は定義される。旧 lease の command は線形化点以降 admit されない（`R_EPOCH_STALE_COMMAND`）ため (ii) に旧 lease は現れない。よって全ての `t` で `out(t)` は定義され、かつ (ii) に現れる lease は P1 により高々 1 つ。

**証明 C（P3 replay / stale）**。`consumed_offer_ids` は CAS tuple の一部（§3.2）。offer `o` を消費する 2 つの CAS `x, y` が共に成功したと仮定する。`x` の成功後、状態の `consumed_offer_ids` は `o` を含む（事後条件）。`y` は条件 1 で `expected == current` を要するが、`y.expected` が `x` の成功前の状態なら `seq`/`consumed_offer_ids` が異なり CONFLICT、`x` の成功後の状態なら条件 4（`o ∉ consumed`）が偽で REJECTED（`R_OFFER_REUSED`）。いずれも `y` は成功しないので矛盾。stale について: validation に用いた snapshot `e` は `permit.expected.control_epoch` として permit に固定され（条件 5）、CAS は `expected.control_epoch == current.control_epoch` を要する（条件 1）。epoch が動いた後は条件 1 が偽になるので、旧 snapshot で通った validation は決して commit されない。

**証明 D（P4 permit one-shot）**。`permit.state` は `UNUSED → CONSUMED` へ CAS 成功の線形化点でのみ遷移し、`CONSUMED`/`VOID` は条件 2 を偽にする。同一 permit を用いる 2 つの CAS が共に成功したとすると、2 つ目は 1 つ目の線形化点以降に評価されるので条件 2 が偽 — 矛盾。失効は `now < expires_at` の条件 2 で遮断。

**証明 E（P5 単調・非復活）**。全ての CAS 成功は `control_epoch := expected.control_epoch + 1`（両 kind 共通）ゆえ epoch は成功列に沿って厳密増加。`new_lease_id` は AuthorityManager が発行する fresh id で、無効化済 id の集合と交わらない（INV-11 で機械検査）。したがって「旧 owner の復活」（無効化された lease の再活性）は型上・手続上とも存在せず、旧 executor が再び owner になるには新 ReadinessAck → 新 CommitPermit → 新 CAS（新 epoch・新 lease）のみ。HealthConfirmation 失敗時に旧 owner へ戻す経路も同理由で存在しない（SafeHold へ落ちる）。

## 4. Lease binding

### 4.1 `ActiveAuthorityLease`（post-commit・ちょうど 1 つ活性）

```python
class LeaseMode(Enum): SHADOW_NON_AUTHORITY | CLOSED_LOOP_AUTHORITY     # 新語 — EP evidence profile と同名にしない（別軸・§11）
class EnvelopeTermKind(Enum): INTRINSIC_D11B | DEPLOYMENT_WORKSPACE | CONTROLLER | SAFETY_RESTRICTION

@dataclass(frozen=True)
class TimingBinding:                                  # 新語 — D1.1-B 値の等値 copy（narrow しない）+ profile 由来 timeout
    tensor_binding_hash: str | None                   # LEARNED ⇔ 非 null（ExecutionBundle.tensor_binding.artifact_hash）/ SCRIPTED・WAIT = null
    policy_rate_hz: CanonicalDecimal | None           # == TimingSpec.policy_rate_hz（等値必須）
    obs_sampling_rate_hz: CanonicalDecimal | None     # == TimingSpec.obs_sampling_rate_hz（等値必須）
    action_rate_hz: CanonicalDecimal | None           # == ActionTimingSpec.action_rate_hz（等値必須）
    hold: ActionHold | None                           # == ActionTimingSpec.hold（等値必須・frozen B enum 参照）
    training_max_obs_staleness_s: CanonicalDecimal | None   # 記録のみ（訓練時仮定 — 執行しない）
    runtime_max_staleness_s: CanonicalDecimal | None  # = FreshnessPolicy.max_staleness_s を profile が stricter-or-equal に narrow した値（執行値）
    ack_timeout_s: CanonicalDecimal                   # profile 由来（数値は本 doc に書かない）
    permit_ttl_s: CanonicalDecimal
    health_confirm_timeout_s: CanonicalDecimal
    command_deadline_s: CanonicalDecimal              # ≥ 1/action_rate_hz（LEARNED）。超過 = R_DEADLINE_MISS
    manager_liveness_s: CanonicalDecimal              # gateway が AuthorityState の鮮度を要求する上限

@dataclass(frozen=True)
class EnvelopeTerm:                                   # 新語 — 各 term は自分の表現で評価される（集合の literal 交差ではない）
    kind: EnvelopeTermKind
    source_ref: str                                   # INTRINSIC_D11B = tensor_binding_hash / 他 = profile_hash（+ 集合 id）
    representation: str                               # "policy_action_space" | "workspace" | "joint_space" | "gateway_predicate"
    predicate_ref: str                                # gateway が評価する述語の識別子（内容は source 側が持つ）

@dataclass(frozen=True)
class AcceptedEnvelope:                               # 新語 — 連言。全 term が admit を返す command のみ admissible
    terms: tuple[EnvelopeTerm, ...]
    satisfiable: bool                                 # CAS 前に評価。False = R_ENVELOPE_EMPTY（lease 不成立・fail-closed）

@dataclass(frozen=True)
class InitializationRecord:                           # 新語 — 再初期化の事実記録
    start_belief_ref: BeliefRef                       # frozen 型（value: SnapshotRef | HashRef — contracts_v2 :151。tag enum は frozen に無い）
    now_used: float                                   # validate_invocation_start に渡した now
    invocation_validation_report_ref: str
    handoff_validation_report_ref: str | None
    consumed_handoff_offer_id: str | None             # SAFEHOLD からの起動 = null
    previous_lease_id: str | None
    previous_control_epoch: int | None

@dataclass(frozen=True)
class ActiveAuthorityLease:                           # 新語 — 不変記録。活性 ⇔ AuthorityState.active_lease_id == lease_id
    lease_id: str
    mode: LeaseMode
    executor_id: str
    invocation_id: str                                # frozen SkillInvocation.invocation_id
    skill_action_id: str                              # certified のみ
    skill_definition_hash: str
    control_mode: ControlMode                         # frozen enum（bundle.control_mode の値）
    control_epoch: int                                # == 活性中の AuthorityState.control_epoch
    ownership: Ownership                              # frozen 型 — offered 集合。required_control_resources ⊆ ownership.control
    profile_hash: str                                 # IndustrialDeploymentProfile（doc 06）— 変更 = 新 lease（in-place 変更禁止）
    authority_decision_ref: str | None                # CLOSED_LOOP_AUTHORITY ⇔ 非 null ∧ granted == True
    initialization: InitializationRecord
    accepted_envelope: AcceptedEnvelope
    timing: TimingBinding
    activated_at: float
```

束縛規則（handoff 決定 6: profile・authority decision・初期化・envelope・timing を **完全に** lease へ束縛）:

- lease の全 field は CAS 時に確定し以後不変。いずれかを変える必要がある場合（profile 更新・envelope 変更・mode 変更）は **新 lease = 新 CAS 経路**（ACK → permit → CAS）。in-place 更新は存在しない。
- `ownership` は frozen `HandoffOffer.ownership`（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:506`）をそのまま束縛し、`validate_invocation_start` の `required ⊆ offered`（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:380`）を通過したものだけが lease になる。SAFEHOLD からの初回起動では offer が無いため、offered 集合は profile が宣言する cell の資源可用性から構成する（§12 OP-3）。
- `authority_decision_ref` の解決先は frozen `AuthorityDecision`（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:351`）。runtime はこれを**読むだけ**で、`granted` を設定・推論しない。

### 4.2 Timing（R5: 等値であって narrow ではない）

- `policy_rate_hz` / `obs_sampling_rate_hz` / `action_rate_hz` / `hold` は D1.1-B の訓練時束縛事実（`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:96-99` ／ `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:125-127`）。executor は**ちょうどその値**で走る。profile が「narrow」できるのは運動学的限界（速度/加速度/力）と鮮度だけ（doc 06 R1）。
- `hold`（`ActionHold` = ZERO_ORDER_HOLD / LINEAR_INTERPOLATE — `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:40`）は policy step 間の保持規約であり gateway がそのとおりに再生する。次 command が `command_deadline_s` 内に届かなければ hold 継続ではなく `SafeHold`（`R_DEADLINE_MISS`）— 無期限 ZOH を「安全」と見なさない。
- 実測 inter-command 間隔が profile 許容を超えて逸脱 ⇒ `R_TIMING_VIOLATION` ⇒ `HOLD`。
- 鮮度: `runtime_max_staleness_s` は frozen `FreshnessPolicy.max_staleness_s` を出発点とし profile は stricter-or-equal のみ。`training_max_obs_staleness_s`（= D1.1-B `max_obs_staleness_s`）は記録のみ（`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:99` の役割分離）。
- `FreshnessPolicy.max_staleness_s = None` の意味は frozen v2 に規定が無い（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151` は型のみ）。本 doc は **runtime 層の読み**として None = 上限なしと扱い、profile は有限値への強化のみ可（有限 → None は `P_FRESHNESS_RELAXED`・doc 06）。None のまま lease を作る場合は `runtime_max_staleness_s = None` を loud 記録し、`BeliefRef.ttl` / `ood_flag` による検査（§6.2 B2）は継続する（§12 OP-16）。

### 4.3 `AcceptedEnvelope`（R6: 表現ごとに評価される連言）

| term | source | 表現 | 評価者 | 備考 |
|---|---|---|---|---|
| INTRINSIC_D11B | `tensor_binding_hash`（D1.1-B `ActionBinding.features[].bounds` + `action_scale` / `transform` の適用順） | policy action space | CommandGateway | 適用順 = raw → normalizer → transform → bounds → cast（`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:65-66`）。**bounds は再定義しない**。LEARNED のみ存在（§12 OP-2） |
| DEPLOYMENT_WORKSPACE | profile `WorkspaceRestriction`（keep-out / reach / height） | workspace | CommandGateway（FK 後） | doc 06 |
| CONTROLLER | profile `ControllerEnvelope`（velocity / acceleration / jerk / force / torque） | joint space | CommandGateway | 制御周波数は含まない（R5） |
| SAFETY_RESTRICTION | profile `SafetyRestrictionSet`（静的） | gateway predicate | CommandGateway | IndependentSafetyLayer の live 決定は本 term ではなく §5.2 (i) の優先出力 |

- 意味論: command `c` は admissible ⇔ 全 term `T` について `T.admit(c) == True`。term の評価不能（表現変換不可・profile 未解決） = FALSE（fail-closed）。
- 空/充足不能: CAS 前に `satisfiable` を評価し False なら `R_ENVELOPE_EMPTY` で lease 不成立。静的側の同型検査は doc 06 `P_ENVELOPE_EMPTY`。
- 「∩」表記（handoff 決定 B）は各 term を **自分の空間で** 評価した連言と読む。異なる空間の literal 集合交差を作らない。

### 4.4 Lease mode（R2 — handoff 決定への追加。再決定ではない。根拠 = EP + Rs C3）

| | `SHADOW_NON_AUTHORITY` | `CLOSED_LOOP_AUTHORITY` |
|---|---|---|
| 根拠 | EP 「`SHADOW`（非 authority）」`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:136`; 「SHADOW は定義上 非 authority」`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:155`; slice = SHADOW `$D/WMSO_RS_C3_RULING_SLICE_PROFILE_20260720.md:32-34` | frozen §5A3 `granted == True` = 必要条件・非十分 `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:354`; EP `usage_ceiling.closed_loop_authority` `$D/WMSO_EvidencePolicy_v1.9.json:213` |
| gateway actuation | **DISABLED** — lease の command は admission 判定・記録（`SHADOW_COMMAND_RECORDED`）のみ。actuation port から何も出ない | admissible command を出力（§5.2 (ii)） |
| `authority_decision_ref` | 任意（存在すれば記録） | **必須・`granted == True`**。加えて profile / 上位 gate の追加条件は自由（必要条件であって十分条件でない） |
| 他の state machine 段（ACK / permit / CAS / health） | **同一**（shadow run が同じ runtime 経路を踏む） | 同一 |
| mode 変更 | 自動昇格なし。CLOSED_LOOP へは新 lease（新 CAS）のみ | 降格も新 lease |
| 本 doc の主張 | slice が使う mode。**本 doc は SHADOW でも authority を主張しない**（charter S0 「zero control authority」`$D/WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md:129`） | 定義のみ。使用は V0 等の別 gate（§11） |

`LeaseMode` の member 名を EP profile 名と一致させないのは、evidence profile（EP `requested_profile`）と runtime の出力可否を型で分離するため。lease は `profile_hash` 経由で EP evidence profile の要求（eligibility report の `requested_profile`）を参照するが、それを再評価しない。

### 4.5 Lease 無効化 trigger（全て `LEASE_INVALIDATED` 記録 + `R_LEASE_INVALIDATED` または個別 fault）

TRANSFER_TO_EXECUTOR 成功（reason TRANSFER）／ HealthConfirmation 失敗・timeout ／ executor heartbeat 喪失 ／ command deadline miss ／ envelope 違反 ／ timing 違反 ／ IndependentSafetyLayer STOP・HOLD ／ AuthorityManager 再起動 ／ profile_hash の更新要求（新 lease 経路へ）／ `NO_CHAIN` 後の SAFEHOLD 転送。RETRACT / FORCE_LIMIT は既定では lease を無効化せず出力を override する（profile が無効化へ強化可 — §12 OP-8）。

## 5. 出力ヌル準備・HOLD・safe stop

### 5.1 `SafeHold` の定義（gateway における「null output」の意味）

`SafeHold` = gateway が**自ら**出す定義済みの安全側 command であって「信号なし」ではない。control_mode 別:

| lease.control_mode（frozen） | SafeHold の内容 |
|---|---|
| `DIFF_IK_EE_TARGET`（LEARNED） | 直近 admitted EE target（無ければ計測現在姿勢）を目標として保持・速度 0。新しい運動要求を出さない |
| `SCRIPTED_SEQUENCE` | 現在関節目標の保持（sequence を進めない） |
| `WAIT` | no-op（元々運動 command を出さない） |

`SafeStop` = `SafeHold` + profile `ControllerEnvelope` が定義する stop-class 要求。SHADOW_NON_AUTHORITY では actuation port が DISABLED なので `SafeHold`/`SafeStop` は**記録上の状態**であり物理 command は出ない。「hold が物理的に何をするか」（controller 固有・skill 固有の safe-hold 保証）は本 doc の外（future static candidate・§12 OP-4）。

### 5.2 出力優先順位（D0 §F の優先を runtime で固定）

```text
out(t) =
  (i)   IndependentSafetyLayer の未解除 SafetyDecision があれば その出力（STOP/HOLD/RETRACT/FORCE_LIMIT）   … 最優先・ack を待たない
  (ii)  else if owner == EXECUTOR ∧ mode == CLOSED_LOOP_AUTHORITY ∧ hold 地平内の admitted command あり → その command
  (iii) else SafeHold（safehold_reason == SAFE_STOP なら SafeStop）
```

- (i) は D0 「preemption acts first, does not wait for ack」（`$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:319`）。runtime は (i) を上書きできない。
- CAS の線形化点で (ii) の集合は空にされる（§3.5 事後条件「SafeHold 活性」= 最初の安全 command）。
- gateway が `manager_liveness_s` 内に新鮮な `AuthorityState` を読めない場合、(ii) を評価せず (iii) に落ちる（INV-19）。

### 5.3 boundary での「producer retains ownership and safe-stops (or re-observes)」の実現

D0 §E の fail-closed 規則（`reject` / `abort` / `timeout` ⇒ producer retains — `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:273-274`）は本 doc では次のとおり: producer の `SkillOutcome` 受領後も lease は活性のまま（`S_BOUNDARY_WAIT`）、executor は新しい運動 command を出さず gateway 出力は (iii) SafeHold。転送が成立しなければその状態が続き、`NO_CHAIN` なら TRANSFER_TO_SAFEHOLD。すなわち「producer retains ownership」= lease 活性の継続、「safe-stops」= SafeHold/SafeStop、「re-observes」= disposition `RE_OBSERVE`。

### 5.4 HOLD を解除できる者

| `safehold_reason` | 解除経路 | 追加前提（CAS 条件 10） |
|---|---|---|
| INITIAL / BOUNDARY_WAIT / TRANSFER / NO_CHAIN / EXECUTOR_LOST / DEADLINE_MISS / ENVELOPE_VIOLATION / HEALTH_FAIL | 完全経路（ACK → permit → CAS）による TRANSFER_TO_EXECUTOR のみ | なし |
| SAFETY | 同上 | IndependentSafetyLayer の clearance record（`stabilized_post_action_state` `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:320` の参照を含む）。runtime は自ら解除しない |
| SAFE_STOP | 同上 | profile が定義する operator / health-check clearance（doc 06）。runtime は自ら解除しない |
| CHECKPOINT_DISABLED | 同上 | profile が定義する operator clearance + 再観測（doc 06）。解除後の転送は SAFEHOLD からの新規起動（§6.2 B0 から）であり、producer の resume ではない |
| MANAGER_RESTART | 同上 | durable state の整合検査記録 |

Orchestrator・Executor・RecoveryRoutingPolicy は HOLD を解除できない（AuthorityState を書けない）。

## 6. Boundary-only 実行（TERMINAL boundary）

### 6.1 boundary の種類

| 種類 | 到達条件 | v0.2 の扱い |
|---|---|---|
| TERMINAL boundary | `SkillOutcome.outcome` が `TerminalOutcome`（SUCCESS/FAILURE/TIMEOUT/INVALID_STATE） | 常に boundary。slice の既定（`$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59`） |
| CHECKPOINT（executor **自身**が `InterruptOutcome{checkpoint_id, reason}` を出し、`validate_outcome` が checkpoint ∈ checkpoint_specs を確認 `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:380`） | **v0.2 では受理のみ・再選択を開始しない（fail-closed）**: TRANSFER_TO_SAFEHOLD(CHECKPOINT_DISABLED)・fault `R_CHECKPOINT_SWITCH_DISABLED`・disposition `HOLD`。producer の resume も行わない。checkpoint での再選択（checkpoint 途中切替）は slice prereg が「Phase G / 別 gate」とし有効化 = chunk 改称 + scope 再審査（`$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59`）⇒ 本 doc の外。Orchestrator 発の中断（preemptive interrupt）は**存在しない**（§11） |

本 doc の「boundary」= **TERMINAL outcome のみ**（`$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59`）。frozen 型が `InterruptOutcome` を許容する事実（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151`）は変えず、受理後の runtime 処置を fail-closed に固定する。「no mid-skill switching」= Orchestrator は `TerminalOutcome` を受け取るまで再選択を開始しない（INV-21）。IndependentSafetyLayer の介入は boundary ではなく §5.2 (i) の出力優先で扱う（切替ではない）。

### 6.2 再選択・再初期化の手続（frozen validator を必ず経由）

```text
B0  AuditRecorder: ASSESSMENT 開始。snapshot := AuthorityManager.read_snapshot()
B1  validate_outcome(invocation, outcome, definition)                         … issues 非空 = R_INVOCATION_INVALID → HOLD
B2  belief := 現在の BeliefRef（value: SnapshotRef | HashRef）。stale/OOD（ttl 超過・ood_flag）= RE_OBSERVE（D0 §D OOD abstention）
B3  disposition_0 := §7 表（outcome × 候補有無）。RECOVERY_ROUTE なら RecoveryRoutingPolicy.route(query) → candidate ids
B4  候補 c ごとに（順序付き）:
      c.skill_action_id が certified か（§7-2）
      validate_invocation_start(new_invocation(c, control_epoch = snapshot.control_epoch + 1), definition_c, belief, now)   … now 明示
      offer あり: validate_handoff(invocation, offer, producer_def, definition_c, authority_epoch_snapshot = snapshot.control_epoch)
      AcceptedEnvelope(c).satisfiable ／ TimingBinding 等値 ／ mode 要件（CLOSED_LOOP なら AuthorityDecision.granted）
      全て通過 → ReadinessAck 要求（ack_timeout_s）→ CommitPermit 要求 → AuthorityCas
      いずれか失敗 → 次候補（fault を記録）
B5  候補が尽きた → NO_CHAIN → TRANSFER_TO_SAFEHOLD(NO_CHAIN) → disposition HOLD | SAFE_STOP（profile）
B6  RuntimeAssessmentRecord を close（採否理由・fault・disposition）
```

- `now` は単調 clock（frozen `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:373` の明示引数 + D0 `CLOCK_MONOTONIC` 単一 origin `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:354-355`）。隠れ wall-clock 参照をしない。
- 再初期化 = B4 の validation と lease の `InitializationRecord` への記録のみ。skill 内部状態の再構成（resume state）は行わない。

### 6.3 `RuntimeAssessmentRecord`（continuation / recovery 判断 — certified ではない）

```python
class BoundaryKind(Enum): TERMINAL | CHECKPOINT

@dataclass(frozen=True)
class RuntimeAssessmentRecord:                        # 新語 — runtime の判断記録。EP v1.9 の claim_target / ProofKind のいずれでもない
    assessment_id: str
    boundary_kind: BoundaryKind
    producer_invocation_id: str
    outcome: ProducerOutcome                          # frozen（不変・写し）
    belief_ref: BeliefRef                             # frozen
    snapshot_control_epoch: int
    candidates_considered: tuple[str, ...]            # skill_action_id 順序列
    candidates_rejected: tuple[tuple[str, str], ...]  # (skill_action_id, code)  code ∈ E_* ∪ R_*
    disposition: RuntimeDisposition
    fault: RuntimeFaultCode | None
    recovery_routing_result_ref: str | None
    resulting_lease_id: str | None
```

「continuation の可否」「recovery の要否」は本 record が示す runtime の判断であり、certificate や EP grade を生成・変更しない（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:39` 「certificate を無効化しない」の裏面 = 有効化もしない）。continuation predicate の静的認証は後継契約の候補（§11, handoff E）。

### 6.4 `RecoveryRoutingPolicy` interface（入出力のみ）

```python
@dataclass(frozen=True)
class RecoveryRoutingQuery:                           # 新語
    disposition: RuntimeDisposition
    fault: RuntimeFaultCode | None
    belief_ref: BeliefRef                             # frozen
    lease: ActiveAuthorityLease | None
    outcome: SkillOutcome | None                      # frozen
    certified_action_ids: tuple[str, ...]             # 候補の全域 = certified SkillActionId のみ
    profile_hash: str

@dataclass(frozen=True)
class RecoveryRoutingResult:                          # 新語
    candidate_action_ids: tuple[str, ...]             # 順序付き。空 = NO_CHAIN
    rationale_ref: str
    policy_artifact_hash: str                         # 何が答えたかの pin（内容は本 doc の外）

RecoveryRoutingPolicy.route(query: RecoveryRoutingQuery) -> RecoveryRoutingResult
```

- 出力は**候補**に過ぎず、B4 の全 validation を再度通る。policy が certified 外の id を返した場合は候補から除外し `R_NO_CANDIDATE` で記録。
- 選択論理（学習型か規則型か、SDM を使うか）は本 doc で定めない（D0 §C/§D の SDM freshness/support 規則 `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:217-223` は policy 側の義務）。

## 7. Runtime disposition と fault code

```python
class RuntimeDisposition(Enum):                       # 新語 — ProducerOutcome の member ではない
    CONTINUE_AT_BOUNDARY | RESELECT | RE_OBSERVE | HOLD | SAFE_STOP | NO_CHAIN | RECOVERY_ROUTE | ABORT

class RuntimeFaultCode(Enum):                         # 新語 — 接頭辞 R_（frozen E_* と衝突しない）
    R_ACK_TIMEOUT | R_ACK_MISBOUND |
    R_PERMIT_EXPIRED | R_PERMIT_REUSED | R_PERMIT_MISBOUND |
    R_CAS_CONFLICT | R_EPOCH_STALE_COMMAND | R_LEASE_UNKNOWN_COMMAND |
    R_OFFER_REUSED | R_OFFER_INVALID | R_INVOCATION_INVALID |
    R_HEALTH_CONFIRM_FAILED | R_HEALTH_CONFIRM_TIMEOUT | R_LEASE_INVALIDATED |
    R_SAFETY_OVERRIDE | R_DEADLINE_MISS | R_TIMING_VIOLATION |
    R_ENVELOPE_VIOLATION | R_ENVELOPE_EMPTY | R_COMMAND_KIND_MISMATCH |
    R_AUTHORITY_DECISION_ABSENT | R_AUTHORITY_DECISION_MISBOUND | R_PROFILE_MISBOUND |
    R_MANAGER_RESTART | R_MANAGER_UNAVAILABLE | R_EXECUTOR_LOST |
    R_NO_CANDIDATE | R_SHADOW_OUTPUT_ATTEMPT | R_CHECKPOINT_SWITCH_DISABLED
```

規則:

1. **`ProducerOutcome` は不変**（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151` の `TerminalOutcome | InterruptOutcome` のまま）。`NO_CHAIN` 等は runtime disposition であり、`SkillOutcome.outcome` / `TransitionRecord.outcome` に書かれることは無い（INV-20）。「failure/no-chain outcome を slice に含める」carry（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:570`）は、frozen `TerminationClass.FAILURE` + runtime `NO_CHAIN` disposition の**組**で表現する。
2. fault は常に disposition を伴う（fault だけで終わる経路は無い）。
3. frozen `E_*`（§5B の `E_HANDOFF_EPOCH_STALE` 等）は validator report に留まり、runtime は `R_OFFER_INVALID` / `R_INVOCATION_INVALID` で包んで disposition に写す（validator の code を上書きしない）。

outcome × disposition（B3 の既定表。profile は SAFE_STOP 側へのみ強化可）:

| `ProducerOutcome` | 条件 | disposition 列 |
|---|---|---|
| Terminal SUCCESS | 候補あり・validation 通過・ACK 取得 | CONTINUE_AT_BOUNDARY |
| Terminal SUCCESS | 候補なし（chain 終端） | NO_CHAIN → HOLD |
| Terminal FAILURE / TIMEOUT | RecoveryRoutingPolicy が候補を返す | RECOVERY_ROUTE → CONTINUE_AT_BOUNDARY |
| Terminal FAILURE / TIMEOUT | 候補なし | NO_CHAIN → HOLD（profile で SAFE_STOP） |
| Terminal INVALID_STATE | belief 再取得で解消し得る | RE_OBSERVE → RESELECT |
| Terminal INVALID_STATE | 解消せず | SAFE_STOP |
| Interrupt PLANNED_SWITCH / EVENT（CHECKPOINT） | v0.2 = checkpoint 切替 無効 | HOLD（fault `R_CHECKPOINT_SWITCH_DISABLED`・`safehold_reason = CHECKPOINT_DISABLED`・解除 = §5.4） |
| Interrupt SAFETY_STABILIZED | — | HOLD（`safehold_reason = SAFETY`・clearance 待ち） |
| outcome 無し（executor 喪失） | — | R_EXECUTOR_LOST → HOLD |

frozen `FailClosedAction`（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151`）→ disposition: `RE_OBSERVE → RE_OBSERVE` / `SAFE_STOP → SAFE_STOP` / `HANDBACK_TO_OWNER → HOLD`（lease を保持したまま SafeHold。「owner へ戻す」= 現 owner の継続であり、無効化済 lease への復帰ではない — §3.8 証明 E）。

## 8. Runtime audit evidence

```python
class AuditKind(Enum):
    EPOCH_TRANSITION | ACK_RECEIVED | PERMIT_ISSUED | PERMIT_CONSUMED | PERMIT_VOIDED |
    LEASE_ACTIVATED | LEASE_INVALIDATED | HEALTH_CONFIRMED | HEALTH_FAILED |
    COMMAND_REJECTED | SHADOW_COMMAND_RECORDED | SAFETY_OVERRIDE | FAULT | DISPOSITION | ASSESSMENT | MANAGER_RESTART

@dataclass(frozen=True)
class RuntimeAuditRecord:                             # 新語 — append-only
    record_id: str
    seq: int                                          # recorder 単調
    t_mono: float                                     # 単調 clock・単一 origin
    kind: AuditKind
    control_epoch: int
    lease_id: str | None
    invocation_id: str | None                         # frozen SkillInvocation / TransitionRecord との join key
    episode_id: str | None                            # frozen TransitionRecord.episode_id
    payload_ref: str                                  # kind 別の typed payload（ReadinessAck / CommitPermit / AuthorityCas / HealthConfirmation / RuntimeAssessmentRecord …）
    fault: RuntimeFaultCode | None
    disposition: RuntimeDisposition | None
    schema_versions: SchemaVersionStamp               # frozen 型を再利用（recorder_artifact_hash を含む）
```

- 記録義務: §3.7 の全事象（CAS の SUCCESS/CONFLICT/REJECTED を含む）、全 permit 発行/消費/失効、全 ACK、全 health、全 fault/disposition、全 safety override、SHADOW の全 command 判定。欠落 = INV-17 違反。
- frozen `TransitionRecord` は boundary ごとに従来どおり recorder が書き、`safety_events`（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:521`）には本 doc の `SAFETY_OVERRIDE` record id を入れる（frozen field の語彙内）。
- **hash 方式 = 定めない**: 「runtime 記録の content-hash 化は WCJ 対象外・方式は D2 prereg で確定（明示 defer — U14）」（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:537`）。本 doc は record の**内容**と**義務**だけを定め、chain / content-hash / 署名は U14 の解決先に従う。
- **EP v1.9 との分離**: 本 record は EP の component / `claim_target` / `ProofKind` / grade のいずれでもなく、`evidence_policy_definition_hash`（`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:163`）に影響しない。EP の `usage_ceiling` も不変（`$D/WMSO_EvidencePolicy_v1.9.json:213`）。runtime 決定・epoch・lease・fault = runtime audit evidence（handoff F）。cell / controller / calibration / gateway / fault injection の evidence = doc 06 `DeploymentEvidencePolicy`。

## 9. Invariants と validation 規則（fail-closed 既定: 評価不能 = FALSE）

| id | 不変量（機械検査式） | 違反時 |
|---|---|---|
| INV-01 | `state.owner.kind == EXECUTOR ⇔ state.active_lease_id != None`; `state.owner.kind == SAFEHOLD ⇔ state.safehold_reason != None` | 起動拒否 / R_MANAGER_RESTART |
| INV-02 | 全 CAS SUCCESS: `new.control_epoch == expected.control_epoch + 1 ∧ new.seq == expected.seq + 1` | 設計違反（test） |
| INV-03 | admitted command: `(cmd.lease_id, cmd.control_epoch) == (state.active_lease_id, state.control_epoch)` を線形化点で満たす | R_EPOCH_STALE_COMMAND / R_LEASE_UNKNOWN_COMMAND |
| INV-04 | `permit.state` の遷移は `UNUSED→CONSUMED`（CAS SUCCESS の線形化点のみ）or `UNUSED→VOID`。`CONSUMED` の permit を持つ CAS SUCCESS は高々 1 | R_PERMIT_REUSED |
| INV-05 | CAS SUCCESS(offer o): `o ∉ expected.consumed_offer_ids ∧ o ∈ new.consumed_offer_ids` | R_OFFER_REUSED |
| INV-06 | `permit.expected.control_epoch == authority_epoch_snapshot`（handoff validation に渡した値）`== expected.control_epoch`（CAS 時） | R_CAS_CONFLICT |
| INV-07 | `ack.expected_control_epoch == permit.expected.control_epoch + 1 ∧ ack.valid_until ≥ permit.issued_at ∧ ack.invocation_id == proposed_lease.invocation_id` | R_ACK_MISBOUND |
| INV-08 | `lease.mode == CLOSED_LOOP_AUTHORITY ⇒ lease.authority_decision_ref != None ∧ resolve(ref).granted == True` | R_AUTHORITY_DECISION_ABSENT |
| INV-09 | `lease.mode == SHADOW_NON_AUTHORITY ⇒` actuation port から当該 lease 由来の command が 0 件 | R_SHADOW_OUTPUT_ATTEMPT |
| INV-10 | 全 `t`: `out(t)` は §5.2 の (i)(ii)(iii) のちょうど 1 つ | 設計違反（test） |
| INV-11 | CAS SUCCESS の `new_lease_id ∉ invalidated_lease_ids`（無効化済集合との交わり空） | 設計違反（test） |
| INV-12 | LEARNED lease: `timing.{policy_rate_hz, obs_sampling_rate_hz, action_rate_hz, hold} == TensorBindingSpec(tensor_binding_hash).{…}`（等値） | R_PROFILE_MISBOUND |
| INV-13 | CAS SUCCESS(TRANSFER_TO_EXECUTOR): `proposed_lease.accepted_envelope.satisfiable == True` | R_ENVELOPE_EMPTY |
| INV-14 | `definition.required_control_resources ⊆ lease.ownership.control`（frozen `:380` の包含） | R_INVOCATION_INVALID |
| INV-15 | `lease.skill_action_id` に対する `ContractCertificate` が存在（Draft 不可） | 候補除外 |
| INV-16 | runtime 型の全 field 名が frozen 型の WCJ payload key 集合に不在（serialization-boundary assert。frozen §8 の同型 assert `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:550` に倣う） | 設計違反（test） |
| INV-17 | §3.7 の各事象に対応する `RuntimeAuditRecord` がちょうど 1 件 | 記録欠落 = fault |
| INV-18 | SafetyDecision 受領の線形化点以降、同一 cycle の lease command admission に先立って (i) が適用され、全 UNUSED permit が VOID | 設計違反（test） |
| INV-19 | gateway が `manager_liveness_s` 内の `AuthorityState` を持たないとき (ii) を評価しない | R_MANAGER_UNAVAILABLE |
| INV-20 | `RuntimeDisposition` / `RuntimeFaultCode` の値が `SkillOutcome.outcome` / `TransitionRecord.outcome` に現れない | 設計違反（test） |
| INV-21 | Orchestrator の再選択開始時刻 ≥ 当該 `SkillOutcome`（`TerminalOutcome`）受領時刻（preemptive interrupt なし）。`InterruptOutcome` からは再選択を開始しない | 設計違反（test） |
| INV-22 | 全 timeout（ack / permit / health / command / manager liveness）は `profile_hash` 由来で lease に写され、本 doc に数値定数は無い | R_PROFILE_MISBOUND |

## 10. Test plan（設計時宣言 — impl は CLOSED）

| id | 試験 | 期待 |
|---|---|---|
| T-01 | 線形化: 同一 `expected` に対する 2 permit の並行 CAS | ちょうど 1 SUCCESS・他は CONFLICT（R_CAS_CONFLICT）。INV-02 |
| T-02 | permit 再使用 | 拒否（R_PERMIT_REUSED）。状態不変 |
| T-03 | permit 失効後の CAS | 拒否（R_PERMIT_EXPIRED） |
| T-04 | 同一 `handoff_offer_id` の 2 回目 | 1 回目 SUCCESS、2 回目 = validate_handoff で `E_HANDOFF_EPOCH_STALE`、CAS で R_OFFER_REUSED |
| T-05 | validation 後に epoch を進めてから CAS | CONFLICT（INV-06） |
| T-06 | CAS 直後に旧 lease の command を投入 | R_EPOCH_STALE_COMMAND。gateway 出力 = SafeHold（新 lease の最初の command まで） |
| T-07 | HealthConfirmation 失敗 / timeout | TRANSFER_TO_SAFEHOLD(HEALTH_FAIL)。旧 lease_id が再活性しない（INV-11） |
| T-08 | 転送中の SafetyDecision(STOP) 注入（CAS 前 / 線形化点直後） | 出力 = safety 決定。permit 全 VOID。最終状態 = SAFEHOLD(SAFETY) |
| T-09 | AuthorityManager kill → restart | epoch = persisted + 1・owner = SAFEHOLD・旧 lease 無効。durable 不読 ⇒ 起動拒否 |
| T-10 | executor heartbeat 喪失 | TRANSFER_TO_SAFEHOLD(EXECUTOR_LOST) |
| T-11 | SHADOW lease から actuation | actuation port 出力 0 件・SHADOW_COMMAND_RECORDED 記録（INV-09） |
| T-12 | CLOSED_LOOP 要求 × decision 不在 / granted=False | 拒否（R_AUTHORITY_DECISION_ABSENT）。SHADOW へ自動降格しない |
| T-13 | AcceptedEnvelope: 各 term 単独違反 × 4・充足不能 profile | R_ENVELOPE_VIOLATION（term 別）/ R_ENVELOPE_EMPTY |
| T-14 | timing: action_rate_hz を profile で「narrow」した lease 提案 | R_PROFILE_MISBOUND（等値のみ許容） |
| T-15 | command deadline 超過 | SafeHold + R_DEADLINE_MISS（hold の無期限継続をしない） |
| T-16 | ランダム interleaving（model check）: 全 trace で INV-01/02/03/10/11 | 反例 0（探索範囲を宣言） |
| T-17 | audit 完全性: 全事象 ↔ record の全単射 | INV-17 |
| T-18 | serialization boundary: runtime 型 field 名 ∩ frozen WCJ key 集合 = ∅ | INV-16 |
| T-19 | disposition 分離: `NO_CHAIN` が `ProducerOutcome` に現れない | INV-20 |
| T-20 | frozen validator との結線: `validate_handoff` に渡す snapshot が `read_snapshot()` 由来であること（隠れ状態参照なし） | 決定論再現 |

## 11. 主張しないこと（境界）

1. **authority**: 本 doc は authority を付与・解錠しない。`CLOSED_LOOP_AUTHORITY` は lease mode の**定義**であり、その使用は frozen §5A3 `granted == True`（必要条件）+ `closed-loop authority` の conjoin 条件 = O0/S0/V0 two-key + 独立安全 gate（`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:156`）+ 上位 gate の全てを要する。slice の mode = SHADOW_NON_AUTHORITY（Rs C3）。closed-loop authority は CLOSED 継続（`$D/WMSO_RS_C3_RULING_SLICE_PROFILE_20260720.md:63`）。
2. **impl**: code / test 実装 / 実行を含まない。§10 は宣言のみ。
3. **schema delta**: frozen 4 file を編集せず、`SkillDefinition` / `ExecutionBundle` / `TensorBindingSpec` / EP `policy_definition` に field を足さない。frozen enum（`ProducerOutcome` / `ControlMode` / `TrainingLineage` / `ProofKind` 等）に member を足さない。新型は全て runtime 層。
4. **execution-profile 軸（R3）**: 本 doc は D1.1-B/C/slice prereg の「boundary-only vertical slice」が名指す boundary-only **execution mode** を仕様化するだけで、real-time decision class / RT0 / `execution profile` 軸（charter `$D/WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md:13-15`）の裁定は Rs 専権のまま（`$D/WMSO_RS_C3_RULING_SLICE_PROFILE_20260720.md:65`）。D0 §G の `D_event` 等は provisional・RT0 測定前であり、本 doc は real-time 主張をしない（`$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:367-372`）。
5. **composition / dual-arm（R7）**: lease は `Ownership` の offered 集合を束縛するが、2 つの executor が同時に別資源を持つ構成（dual-arm 同時実行・`ParallelRegion`・arity）は本 doc の外 = 別 indivisible composition delta（pX court / Rs 専権）。本 doc の lease は常に 1 executor。
6. **mid-skill interruptibility / atomic region / resume-from-checkpoint / checkpoint 途中切替**: CLOSED（future static candidate；切替の有効化 = 別 gate + scope 再審査）。v0.2 は executor 自発の `InterruptOutcome` を受理して HOLD へ落とすだけで、checkpoint からの再選択・Orchestrator 発の中断・producer の resume のいずれも行わない。
7. **skill-specific safe-hold 保証 / continuation predicate / intrinsic recovery capability の静的認証**: いずれも後継契約（handoff E: `contracts_v3`）の候補であり本 doc は定義しない。
8. **EP v1.9 の変更**: なし。runtime audit は EP claim_target ではない（§8）。
9. **freeze / two-key / gate PASS / Rs 承認**: いずれも主張しない。前 package（v0.1）の内容は handoff 決定以外を引き継がない。
10. **D1.1-C artifact manifest**: 未凍結（open-11 pending）。本 doc は manifest の field を参照しない。

## 12. Open points（⛔ open = 0 を宣言しない）

| id | open | 出所 / 依存 | 本 doc の扱い |
|---|---|---|---|
| OP-1 | **DDR#32**: D0 slow-path rollout `H < 5`（`H<5`）（`$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:179`）と実測 routing 周期長 7 の緊張が boundary 再選択（RecoveryRoutingPolicy が SDM rollout を使う場合）に影響する | `$D/WMSO_RS_SKILL_OWNERSHIP_RULING_20260720.md:24`（両 court にまたがる）; `thread_isaac_lab/thread-vault/07-Design/00-DESIGN-STATUS-LEDGER.md:136` | **解かない**。依存として列挙。本 doc の再選択は policy の horizon に依存しない interface 設計 |
| OP-2 | SCRIPTED / WAIT skill には D1.1-B `bounds` が無く INTRINSIC_D11B term が欠ける。AcceptedEnvelope は profile 3 term のみ | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:138` は action feature（LEARNED）に限る | lease に `tensor_binding_hash = null` を loud 記録。intrinsic envelope の静的宣言 = future static candidate |
| OP-3 | SAFEHOLD からの初回起動で `validate_invocation_start` に渡す offered `Ownership` の出所（profile の cell 資源可用性） | doc 06 | doc 06 の `CellIdentity` / 資源宣言に依存 |
| OP-4 | `SafeHold` の物理的実現（controller 固有）と skill-specific safe-hold 保証 | handoff D「future static candidate」 | §5.1 は種別のみ |
| OP-5 | `RuntimeAuditRecord` の content-hash / chain 方式 | frozen `U14` `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:537` | 定めない |
| OP-6 | `AuthorityState` の durable 化 primitive と restart 時の `epoch := persisted + 1` の十分性（durable 書込みと CAS の原子性） | D0 「`CAS/lock` は D1 refinement」`$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:270-272` | 要件（線形化・durable）のみ |
| OP-7 | mid-skill の obs 鮮度執行の所在（executor か gateway predicate か） | boundary-only ゆえ boundary 検査のみ規定 | §4.2 は boundary の鮮度のみ |
| OP-8 | RETRACT / FORCE_LIMIT が lease を無効化すべきか（既定 = override のみ） | D0 §F `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:317` | profile で強化可としたが既定は未裁定 |
| OP-9 | `HealthConfirmation` と D0 §F `heartbeat` / health の関係（同一 channel か別か） | `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:318` | 別物として扱い、CAS 条件 9 で §F health を参照 |
| OP-10 | 全 timeout の値 | profile parameter（doc 06）・RT0 測定前 | 数値を書かない |
| OP-11 | `InterruptOutcome` 受理後の HOLD（CHECKPOINT_DISABLED）からの復帰手続（operator clearance の内容）と、checkpoint 切替を将来有効化する場合の scope 再審査の入口 | `$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59` | v0.2 = 切替無効（HOLD）。有効化 = chunk 改称 + scope 再審査 |
| OP-12 | SHADOW 運転時に実際に actuation を持つ外部 controller の扱い（本 doc の外） | charter S0 `$D/WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md:129` | 記述しない |
| OP-13 | Executor の process 境界（in-process か別 process か）と heartbeat の実装 | D0 §H | interface のみ |
| OP-14 | D0 §G `D_event`（handoff deadline）と本 doc の `ack_timeout_s` / `permit_ttl_s` の整合 | `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:363-365` | RT0 で測定後に整合検査 |
| OP-15 | 本 doc 自体の two-key・Rs 裁定 | — | 未 |
| OP-16 | `FreshnessPolicy.max_staleness_s = None` の runtime 意味（上限なし）は runtime 層の読みであり frozen の規定ではない | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151` | §4.2 に loud 記録。frozen 側の確定 = 後継契約 or Rs |

## 13. 版歴 / fold-map

- v0.1（前 package・別 sandbox・本 session では参照不能。内容は handoff 決定 C のみを根拠に再構成）→ **v0.2（本 doc）**。
- handoff 決定 C の各訂正 → 本 doc の節:

| 訂正 | 内容 | 実装節 |
|---|---|---|
| 1 | `BeliefSnapshotRef` 削除 → frozen `BeliefRef` 再利用 | §1 表・§4.1 `InitializationRecord.start_belief_ref: BeliefRef`・§6.3・§6.4 |
| 2 | 次 executor の readiness ACK を owner 転送より前に取得 | §3.3 `ReadinessAck`・§3.5 CAS 条件 3・INV-07 |
| 3 | owner と `control_epoch` を単一 CAS で原子的に切替 | §3.2 `AuthorityState` tuple・§3.5 `AuthorityCas`・証明 A |
| 4 | 旧 epoch 拒否は同一 CAS で有効（post-transfer ACK に遅延しない） | §3.5 事後条件「旧 epoch 拒否が有効化」・INV-03・T-06 |
| 5 | pre-commit `CommitPermit` と post-commit `ActiveAuthorityLease` を分離 | §3.4 / §4.1・証明 D |
| 6 | profile・authority decision・初期化・envelope・timing を lease へ完全束縛 | §4.1 `ActiveAuthorityLease`（`profile_hash` / `authority_decision_ref` / `initialization` / `accepted_envelope` / `timing`）・§4.5 |
| 7 | profile は monotone strengthening のみ | §4.2（鮮度 stricter-or-equal・rate 等値）・§4.3・INV-12 ／ 機械検査の本体 = doc 06 |
| 8 | `continuation_overlay_hash` 削除・`recovery_overlay_hash` 削除 | 代替 = §6.3 `RuntimeAssessmentRecord`（非 certified）+ §6.4 `RecoveryRoutingResult.rationale_ref` |
| 9 | `ParallelExecutionProfile` 削除（composition delta へ返却） | §11 項 5（OUT）／ doc 06 側で 削除 |
| 10 | `NO_CHAIN` 等を `ProducerOutcome` に足さない → runtime disposition / fault code | §7 `RuntimeDisposition` / `RuntimeFaultCode`・INV-20・T-19 |
| B | `IntrinsicExecutionLimits` 不採用（D1.1-B の TimingSpec / ActionTimingSpec / bounds を参照） | §4.2・§4.3 INTRINSIC_D11B term |

- 旧順序「new epoch → new owner ACK → old epoch rejection」の二重所有窓 → v0.2 順序（§0・§3.5）。窓が閉じる根拠 = 証明 A/B。
- **追加（handoff 外・再決定ではない）**: lease mode `SHADOW_NON_AUTHORITY` / `CLOSED_LOOP_AUTHORITY`（§4.4）。根拠 = EP 「SHADOW は定義上 非 authority」+ Rs C3（slice = SHADOW）。BRIEF R2 に従う。
- **追加（BRIEF R1/R5/R6/R7）**: §3.6（offer 検証 = CAS 前・消費 = CAS 内）／ §4.2（timing 等値）／ §4.3（envelope 連言）／ §11 項 5（ownership 部分保持の OUT）。
- **synthesis record（2026-09-03 16:4x UTC）**: base = draft A（sha256 は本 package の SHA256SUMS 外・scratch）。予定していた judge panel（draft B/C + judge J1/J2）は session 上限で**未実施** — 本版は single-draft + critic fold であり、多視点 judge を経ていない（08 計画の 3 軸レビューで補う）。critic fold: **X1** = `BeliefRef` の判別は `value: SnapshotRef | HashRef`（frozen `:151`）— 旧表記「SNAPSHOT | HASH_REF」は v1 code 由来ゆえ全箇所を訂正（§0・§4.1・§6.2）／ **X2** = boundary = TERMINAL のみ（slice prereg `:59`）— CHECKPOINT を「TERMINAL と同一扱い」から「受理 + HOLD（切替無効・fail-closed）」へ改め、`SafeHoldReason.CHECKPOINT_DISABLED`・`R_CHECKPOINT_SWITCH_DISABLED`・§3.7 遷移・§5.4 解除行・§7 表・INV-21・§11 項 6・OP-11・anchor 17 を更新、題名を「boundary-only（TERMINAL boundary・checkpoint 切替なし）」へ／ **§3.3** = `FreshnessPolicy.max_staleness_s = None` の意味を runtime 層の読みとして loud 化（§4.2・OP-16）。

## 14. Review anchors

1. 本 doc は frozen 4 file に field / enum member を足していない — §1・§11 項 3・INV-16（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:385` strict codec と整合）。
2. `AuthorityManager` の責務（CAS・発行・旧 epoch 拒否・`handoff_offer_id` 単位の使用済み拒否・snapshot 読出し）は frozen の O0 層要求仕様に一致 — §2 表 ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382`。
3. `validate_handoff` は等値検査であり、本 doc は CAS 前に呼び、offer 消費を CAS 内に置く — §3.6 ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:381`。
4. 順序 ReadinessAck → CommitPermit → AuthorityCas → HealthConfirmation が §3 の型・条件・遷移表に一貫 — §3.3–§3.7。
5. no-double-ownership 証明が tuple CAS + 線形化 admission に還元されている — §3.8 A ↔ D0 `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:270-272`。
6. no-orphan-output 証明が出力関数 (i)(ii)(iii) の全域・排他性に還元され、safety 優先が (i) — §3.8 B・§5.2 ↔ `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:319`。
7. offer replay / stale が CAS tuple の `consumed_offer_ids`（`handoff_offer_id` 単位）と条件 1/4/5 で二重遮断 — §3.8 C・INV-05/06 ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:498`。
8. permit one-shot・失効 — §3.4・§3.8 D・INV-04。
9. 旧 owner 非復活・epoch 単調 — §3.8 E・INV-02/11・T-07。
10. HealthConfirmation 失敗 = SafeHold + disposition、旧 owner 不復活 — §3.7 表・§3.8 E。
11. CLOSED_LOOP_AUTHORITY lease の必要条件 = `granted == True` + EP `closed_loop_authority` conjuncts、十分条件ではない — §4.4・INV-08 ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:354`・`$D/WMSO_EvidencePolicy_v1.9.json:213`。
12. SHADOW lease は actuation を出さず他段は同一 — §4.4・INV-09 ↔ `$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:155`・`$D/WMSO_RS_C3_RULING_SLICE_PROFILE_20260720.md:32-34`。
13. timing は D1.1-B と等値（narrow 禁止）、鮮度は frozen FreshnessPolicy 起点 — §4.2・INV-12 ↔ `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:96-99`・`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:125-127`。
14. AcceptedEnvelope は表現別評価の連言で、bounds を再定義しない — §4.3 ↔ `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:138`・`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:65-66`。
15. `ProducerOutcome` 不変・`NO_CHAIN` は disposition（frozen carry の `no-chain` outcome は FAILURE + disposition の組） — §7 ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151`・`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:570`。
16. audit hash 方式は U14 defer・EP 分離 — §8 ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:537`・`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:163`。
17. boundary = TERMINAL のみ；executor 自発 `InterruptOutcome` は受理 + HOLD（checkpoint 切替 無効・fail-closed）、Orchestrator 発の中断なし — §6.1・§7・INV-21 ↔ `$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59`・`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:380`。
18. `now` 明示・隠れ wall-clock なし — §6.2 ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:372-373`。
19. execution-profile 軸を裁定していない — §11 項 4 ↔ `$D/WMSO_RS_C3_RULING_SLICE_PROFILE_20260720.md:5`・`$D/WMSO_RS_C3_RULING_SLICE_PROFILE_20260720.md:65`。
20. composition / 2 executor 同時保持は OUT — §11 項 5。
21. 全 timeout は profile parameter で本 doc に数値なし — INV-22・§12 OP-10。
22. Open points に DDR#32 を解かずに列挙 — §12 OP-1 ↔ `$D/WMSO_RS_SKILL_OWNERSHIP_RULING_20260720.md:24`。
23. 機械検査（`check_review_candidate.py --runtime`）= FAIL 0。残る C2 WARN（6 件）は heuristic で、いずれも「引用行が別の規範（TERMINAL のみ / 型定義）を担い、同じ文に並ぶ識別子はその帰結として本 doc が導入したもの」— slice prereg `:59` を `InterruptOutcome` の処置の根拠として引く行（§6.1・§6.2・OP-11・anchor 17）と、frozen `:151` を `FreshnessPolicy.max_staleness_s = None` の型根拠として引く行（§4.2）。引用先の内容は sed で再確認済み。
