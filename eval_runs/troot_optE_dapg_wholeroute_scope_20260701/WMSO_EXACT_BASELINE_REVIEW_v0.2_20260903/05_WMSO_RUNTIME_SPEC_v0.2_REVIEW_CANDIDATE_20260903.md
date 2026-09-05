# WMSO boundary-only runtime（TERMINAL boundary・checkpoint 切替なし）— RUNTIME SPEC (v0.2.7 REVIEW CANDIDATE)

- node: `T-WMSO`; 起草 = Claude Code web session（review candidate 起草・**authority 無し**・凍結物へ非接触）; 作成 = 2026-09-03（UTC）
- status: **REVIEW CANDIDATE v0.2.7（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.6 → v0.2.7 = v0.2.6 本文への再レビュー round 4（R5 / R6 → V5 / V6）の確定 finding の fold（§13）。旧版の系譜: — v0.2.5 → v0.2.6 = v0.2.5 本文への再レビュー round 3（R3 / R4 → V3 / V4）の確定 finding の fold（§13）。旧版の系譜: — v0.2.4 → v0.2.5 = Rs 裁定 2026-09-04（GPT5.6sol 推奨を採用・`review_records/rs_consult/`） の反映（OPP-15 B+ / OPP-11 / OPP-13 / OP-19・§13）。旧版の系譜: — v0.2.3 → v0.2.4 = v0.2.3 本文への再レビュー round（reviewer R1 / R2 + verifier V1 / V2・別 context）の確定 finding の fold（§13）。旧版の系譜: — v0.2 → v0.2.1 = 陽性対照レビューの注入外 finding の fold／ v0.2.1 → v0.2.2 = 3 軸独立レビュー（A / A2 / B / B2）の finding の fold／ v0.2.2 → v0.2.3 = 独立 verifier（3 lens）の verdict 反映 + PARTIAL 残差の処置 + 軸 C（v0.2.2 対象）finding の fold（§13・全体記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`）
- 土台（凍結・編集しない・4 file）: contracts_v2 DESIGN v2.11.2 `00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff` @ `54f90a7de1e02fb14eaf793bf3c60d9503d0d82e` ／ EP v1.9 md `c474acea7c58acc22050c2ad9944fd45a18f5c76967964b42d11922e28fa27e7` ／ EP JSON v1.9 `e63176af9bc3a246b1c32db369ec59f8d09a4c96c381bb03a3a6024bd9811c6e`（definition hash `e7ca43093084c167a209b008533a66d26a1fd3223d2a3c11274d28306c3ff803`）／ tensor_binding DESIGN v13 `5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6` @ `07250f4a0208b3bbd27eae6fef7d980743c4b538`
- 前提文書: D0 architecture（EXIT GRANTED）／ Rs C3 裁定（slice EP evidence profile = SHADOW rank 2・非 authority；execution profile は別軸・未裁定）／ handoff 決定（2026-09-03）
- ⛔ impl / training / closed-loop authority / production / push / freeze / slice = CLOSED 継続。本 doc は設計書面のみ。
- 系譜: 起草 draft A（角度 = AUTHORITY-SAFETY-FIRST・2026-09-03 11:20 UTC 実測）→ critic 報告（起草時 scratch・本 package の SHA256SUMS 外。X1 / X2 / §3.3 の内容は §13 synthesis record に inline 済 — v0.2.2 A2-10）の fold = v0.2（16:44 UTC）→ 陽性対照の注入外 finding の fold = v0.2.1（2026-09-04 01:47 UTC）→ 3 軸独立レビュー（A / A2 / B / B2）finding の fold = v0.2.2（2026-09-04 15:41 UTC）→ verifier verdict + 残差 + 軸 C の fold = v0.2.3（2026-09-04 20:47 UTC）→ v0.2.3 再レビュー round（R1 / R2 → V1 / V2）の fold = v0.2.4（2026-09-04 23:00 UTC）→ Rs 裁定（外部推奨採用）の fold = v0.2.5（2026-09-05 01:33 UTC）→ round 3（R3 / R4 → V3 / V4）の fold = v0.2.6（2026-09-05 02:15 UTC）→ **round 4（R5 / R6 → V5 / V6）の fold = 本版 v0.2.7（§13）**。⚠ judge panel（3 draft × 2 judge）は session 上限で未実施 — §13 に honest に記録。

## 0. 中心構造

```text
Frozen（不変・参照のみ）:
  Static/Cert/Elig/Authority: SkillDefinition → certify_definition → evaluate_usage_eligibility → evaluate_authority_grant → AuthorityDecision
  Runtime 型:   SkillInvocation / SkillOutcome / HandoffOffer{handoff_offer_id, control_epoch, ownership} / TransitionRecord / SchemaVersionStamp
  Runtime val.: validate_invocation_start(…, now) / validate_outcome / validate_handoff(…, authority_epoch_snapshot) … certificate を無効化しない
  値語彙:       BeliefRef{value: SnapshotRef | HashRef}/ Ownership / ProducerOutcome / ControlMode / FreshnessPolicy
  boundary:     TERMINAL outcome のみ（slice prereg）。InterruptOutcome = 受理 + HOLD（checkpoint 切替 = 無効・別 gate）
  D1.1-B:       TimingSpec / ActionTimingSpec{action_rate_hz, hold} / ActionBinding{control_mode, action_scale, timing} + FeatureBinding.bounds / tensor_binding_hash

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
| **AuthorityManager** | `AuthorityState` の唯一 writer。`AuthorityCas` の実行、`CommitPermit` の発行/失効/一回性、`authority_epoch_snapshot` の読出し提供、`consumed_offer_ids` / `invalidated_lease_ids` の保持、restart 時の fail-closed 復帰。**旧 epoch command 拒否の所有者**（v0.2.2・A2-05: 拒否の**状態**は manager が所有し、**執行点**は CommandGateway の admission — gateway は manager 所有の `AuthorityState` を線形化して読むだけで書かない） | `AuthorityState`（durable）+ permit 台帳 | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382`（CAS 更新・発行・旧 epoch 拒否・使用済み offer 拒否・snapshot 読出し = O0 層） |
| **CommandGateway** | actuation への唯一経路。admission = manager 所有 `AuthorityState` の**同期・線形化読み**（cache 不可 — v0.2.2・B-H1）の下で `(lease_id, control_epoch)` 等値 ∧ `cmd.executor_id == lease.executor_id`（v0.2.4・R1-12） ∧ `¬boundary_wait` ∧ `AcceptedEnvelope` 連言 ∧ command 種別 = lease.control_mode ∧ `cmd_seq` 単調。既定出力 = `SafeHold`。SHADOW lease の actuation port = DISABLED。`manager_liveness_s` は「線形化読みを待つ上限」であり、超過 = (ii) を評価せず (iii) | 線形化読み（cache を持たない）+ 直近 admitted command + `restart_pending` flag | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382`（旧 epoch command 拒否）; D0 `control_ownership` 単一 writer `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:270-272` |
| **Orchestrator** | boundary で `BeliefRef` から候補を再選択（`initiation_predicate` 保持候補の filter・frozen validator を呼ぶ）。`ReadinessAck` を取り、`CommitPermit` を要求し、`AuthorityCas` を依頼する。**状態を持たない**（authority を書かない） | なし（audit へ記録のみ） | D0 §D `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:207-215`（candidate filter / select / replan / OOD abstention） |
| **Executor** | 1 invocation の skill runtime instance。`ReadinessAck` を返し、lease 活性後に D1.1-B の rate/hold で command を出し、`HealthConfirmation` を返す | 自身の lease copy（読みのみ） | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:125-127`（`action_rate_hz` / `hold`） |
| **IndependentSafetyLayer** | D0 §F。gateway 出力への優先介入（STOP/HOLD/RETRACT/FORCE_LIMIT）、heartbeat、`stabilized_post_action_state`。ack を待たない | 独立（本 doc は interface のみ） | `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:317-320` |
| **RecoveryRoutingPolicy**（外部） | `RecoveryRoutingQuery` → 候補 `skill_action_id` 列 + rationale ref。選択論理は本 doc の外 | 外部 | D0 §E 4 option の 3（Recovery Skill; option 1 = compatible `SkillHandoffState` での direct handoff）`$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:243-247`; Recovery skill は同じ `SkillLifecycleContract` を持つ ordinary skill `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:280-281` |
| **AuditRecorder** | `RuntimeAuditRecord` の append-only 記録。`SchemaVersionStamp` を再利用 | 記録列（seq 単調） | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:524-529`（`SchemaVersionStamp`） |
| **DeploymentValidityMonitor**（v0.2.5・OP-19） | deployment 側の失効 event（incident・tool 交換・firmware 更新・layout revision・ISL build 変更・profile の SUSPENDED / REVOKED）を検出し AuthorityManager へ通知する。**自らは AuthorityState を書かない**（manager が唯一 writer として TRANSFER_TO_SAFEHOLD を CAS）。周期診断は timing baseline が定める drift / proof-test 項目のみ。**liveness 契約（v0.2.6・R3-08）**: monitor は heartbeat を manager へ送り（上限 = baseline 項目 `VALIDITY_MONITOR_LIVENESS`）、manager は monitor に依存しない head-check（§3.7）を周期実行する。event 通知の遅延上限 = baseline 項目（R3-20）。最小入力 = controller / ISL / tool の identity 報告・layout と baseline registry（定義 = doc 06 §8.3・cell_id ごとに 1 head・v0.2.7 R6-10）の supersession・registry の state 変化（R4-14） | 監視対象の直近観測（durable 不要） | D0 §F fail-closed `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:318`・doc 06 §8.3 |

Home matrix（handoff 決定 D を凍結根拠付きで固定。本 doc は各 home を再決定しない）:

| item | home（v0.2） | 本 doc の節 | 根拠（凍結・裁定） |
|---|---|---|---|
| 現在状態からの再選択・再初期化 | runtime / Orchestrator | §6 | D0 §D replan on outcome/event `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:210` |
| 出力 null 準備 | runtime process / authority 分離（CommandGateway `SafeHold`） | §5 | D0 §E `reject` / `abort` / `timeout` ⇒ producer retains + safe-stop、「control is never released into a vacuum and never duplicated」`$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:273-274` |
| owner・epoch 転送 | AuthorityManager / CommandGateway | §3 | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382` |
| intrinsic action bounds・rate・hold | frozen D1.1-B（参照のみ・再定義しない） | §4 | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:138`（`bounds` 必須）; `:125-127`（`action_rate_hz`/`hold`） |
| cell / controller / tool / payload 条件 | `IndustrialDeploymentProfile`（doc 06・外部） | §4（`profile_hash` 参照） | frozen 型（`SkillDefinition` `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151` / `TensorBindingSpec` `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:173-181`）に cell / controller / calibration / deployment の **field は無い**。語の出現（再現 command: `grep -ic <pat> <EP md> <EP json>`, pat ∈ {controller, calibrat, deploy, inject, epoch, lease}）= EP md / JSON で 0 hit；DESIGN 2 file には散文としての hit（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:570`「calibrated uncertainty」・`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:255` / `:313`「全 deployment の resolver」・`:337`）があり schema 語彙ではない（v0.2.2・A-03 / A2-10） |
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
class SafeHoldReason(Enum): INITIAL | HEALTH_FAIL | NO_CHAIN | EXECUTOR_LOST | MANAGER_RESTART | GATEWAY_RESTART | DEADLINE_MISS | TIMING_VIOLATION | ENVELOPE_VIOLATION | SAFETY | SAFE_STOP | CHECKPOINT_DISABLED | VALIDITY_EXPIRED   # v0.2.5（OP-19）: VALIDITY_EXPIRED = lease の validity_deadline_mono 到達 / profile の SUSPENDED・REVOKED / calibration・evidence の失効 event。v0.2.2: BOUNDARY_WAIT（flag に置換）/ TRANSFER（lease 無効化理由であって hold 理由でない）を 削除（B2-16）

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
    safehold_reason: SafeHoldReason | None            # owner.kind == SAFEHOLD ⇔ 非 null（優先順位 = §3.5・v0.2.2）
    boundary_wait: bool                               # v0.2.1: 活性 lease の SkillOutcome 受領済（以後 当該 lease の command は R_POST_OUTCOME_COMMAND で拒否）
    seq: int                                          # CAS 成功ごとに +1（durable 化の単調 key）
    safehold_disposition: RuntimeDisposition | None   # v0.2.4（R1-03）: 当該 SAFEHOLD 期間の実効 disposition の max（SAFE_STOP > HOLD）。条件 1 の等値比較の対象外だが同一線形化点で durable 更新され、§5.2 (iii) はこれを線形化読みで読む（audit 読出しに依存しない）。owner.kind == EXECUTOR では None
```

- `AuthorityState` は **durable**（AuthorityManager の再起動をまたぐ）。読出しは `read_snapshot() -> AuthorityState` で行い、frozen `validate_handoff` の `authority_epoch_snapshot` 引数にはこの `control_epoch` を渡す（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:377-378`）。
- 初期状態 = `(SAFEHOLD, epoch=e0, None, ∅, INITIAL, False, 0)` + `safehold_disposition = HOLD`（v0.2.6）。`e0` は durable 記録から復元する。**durable 記録が読めない・存在しない場合は起動拒否**（自動的に 0 から始めない — v0.2.1・B-12）。初回だけは operator が profile の clearance 手続（doc 06 `EscalationPolicy.clearance_roles`）で **genesis record**（`epoch 起点・consumed_offer_ids = ∅・invalidated_lease_ids = ∅・profile_hash`（この genesis が権限づける profile・v0.2.4 R2-15）・role = doc 06 `clearance_roles[GENESIS]`）を書き、AuthorityManager はそれを読んで起動する。store の消失は genesis の再発行（= operator 行為・audit 必須）でしか回復しない。
- **線形化点 = durable commit の完了（v0.2.2・B-M12）**: `AuthorityCas` の SUCCESS は write-ahead の durable 書込みが完了した時点で成立し、通知・audit・`permit.state := CONSUMED` はその後にのみ行う。in-memory 成功と durable 書込みの間で crash した CAS は「起きなかった」ものとして扱われ、restart の `epoch := persisted + 1` と矛盾しない。`invalidated_lease_ids` は `AuthorityState` と同じ durable store に同一 commit で書く（INV-32）。
- **genesis の下限（v0.2.2・B-L4 / B2-11）**: genesis record の epoch 起点は、（別 durable の）AuditRecorder に現れる最大 `control_epoch` より**厳密に大きい**こと。両 store が失われた場合は operator が厳密に大きい起点を宣言し、その導出を `GENESIS_RECORDED` に記録する。
- **clock domain（v0.2.2・B2-12）**: 本 doc の時刻比較は全て AuthorityManager の単調 clock（D0 §G 単一 origin `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:354-355`）で行う。`ReadinessAck.valid_until` は manager が ACK **受領時**に自 clock で確定する（`t_receive + ack_validity_s`。executor の `t_ack` は参考値）。HealthConfirmation / permit の timeout も manager が自 CAS 時刻から測る。

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
    lease_proposal_id: str                            # 提案 lease（未活性）の id = 最終 `lease_id`（proposal 時に確定・v0.2.2・B-M4）
    envelope_readback_ok: bool                        # executor が AcceptedEnvelope / TimingBinding を読み戻し等値確認した
    t_ack: float                                      # 単調 clock（D0 §G）
    valid_until: float                                # manager が受領時に自 clock で確定: t_receive + TimingBinding.ack_validity_s（v0.2.2・B2-12。executor の t_ack は参考値）
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
    authority_decision_ref: str | None                # CLOSED_LOOP_AUTHORITY ⇒ 非 null ∧ granted == True；SHADOW では None 可（存在すれば記録のみ・§4.4 と同一・v0.2.6 R3-03）
    profile_hash: str                                 # IndustrialDeploymentProfile（doc 06）
    acceptance_record_hash: str                       # v0.2.5（OPP-13）: doc 06 §8.3 ProfileAcceptanceRecord（state == ACCEPTED・generation を束縛）
    acceptance_generation: int
    validity_deadline_mono: float                     # v0.2.5（OP-19）: min(calibration 期限, required evidence 期限, acceptance 期限) を manager clock へ変換した値（wall→mono は発行時に確定・doc 06 OPP-3）。lease_max_duration_s は含めない（INV-33 / R_LEASE_DURATION_EXCEEDED が担う・v0.2.6 R3-04 / R4-06）
    validity_deadline_source: tuple[tuple[str, str, float], ...]   # v0.2.6（R3-05）: (kind ∈ {CALIBRATION, EVIDENCE, ACCEPTANCE}, id = calibration_id | record_id | record_hash, deadline_mono) — 全項目の個別 deadline。到達時の fault と disposition は kind / id から doc 06 §5 (b) の表で決まる（表に無い = SAFE_STOP）。v0.2.7（R5-08）: 副 kind は id を `lease.profile_hash` の profile `calibration_refs`（CALIBRATION）/ evidence store（EVIDENCE の record kind）で解決する（profile は content-addressed で不変・wall-clock 再読なし）；解決不能 = 表に無い = SAFE_STOP
    proposed_lease: ActiveAuthorityLease              # 未活性。proposed_lease.control_epoch == expected.control_epoch + 1
    issued_at: float
    expires_at: float                                 # = issued_at + profile.permit_ttl_s
    effective_expires_at: float                       # v0.2.5（OPP-11）: = min(expires_at, ack.valid_until, validity_deadline_mono, [decision.t_mono + decision_max_age_s — authority_decision_ref ≠ None のときのみ])。定義される項だけの min（v0.2.6 R3-03 / R4-18: SHADOW で不能判定にならない）。条件 2 はこちらを使う
```

- **permit 発行の前提条件（v0.2.1・C-07 / C-10）**: (a) `profile.health_checks` のうち stage ∈ {BEFORE_PERMIT, BOTH} の全 check が pass（失敗 = `R_HEALTHCHECK_FAILED`・permit 不発行）。全 stage の check は**各実行の直前**に evaluator の content sha256 を `evaluator_sha256` と再検証し、不一致 = check FAILED（fail_closed・v0.2.4 R2-17）; (b) profile の時刻・lease 文脈依存検査（doc 06 §8.1 (2) が第 2 評価点として列挙する**全 code**（SSOT = doc 06 §8.1 (2)・v0.2.6 R3-18 / R4-08）が発行時刻で全て pass（失敗 = `R_PROFILE_MISBOUND`）; (c) `TimingBinding` の等値（INV-12）; (d) **boundary guard**（v0.2.2・B-H2 / B2-02）: `expected.owner.kind == SAFEHOLD ∨ expected.boundary_wait == True`（違反 = `R_MIDSKILL_TRANSFER_BLOCKED`・permit 不発行）; (e) CLOSED_LOOP_AUTHORITY: `authority_decision_ref` を発行時に再解決し `granted == True ∧ age < decision_max_age_s`（厳密境界・v0.2.7 R5-07。違反 = `R_AUTHORITY_DECISION_ABSENT`・v0.2.2・B2-14）。**age の基準（v0.2.3・B2-14 残差 → v0.2.4・R1-02 で起点を評価時刻へ）**: `age = now(manager) − t_mono`、`t_mono` = `evaluate_authority_grant` が呼ばれた時（O0 層が decision を評価時刻の audit record と共に引き渡す）に記録した `RuntimeAuditRecord`（kind = ASSESSMENT・payload = decision ref + 4 入力 record の ref `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:346-352`）の `t_mono`。manager の「最初の解決」時刻ではない（それでは初回 age = 0 で常に通る）。その record が無い decision は不在として扱う（`R_AUTHORITY_DECISION_ABSENT`）。age 超過 = 再評価（新 ref）を要求し permit 不発行; (f) `permit.profile_hash == proposed_lease.profile_hash`; (g) `∃ e ∈ profile.binding_expectations: e.skill_action_id == proposed_lease.skill_action_id ∧ e.tensor_binding_hash == proposed_lease.timing.tensor_binding_hash ∧ e.control_mode == proposed_lease.control_mode`（未 commissioning の skill は lease 不可・違反 = `R_PROFILE_MISBOUND`・v0.2.3 CD-05）; (h) `proposed_lease.ownership.control ⊆ profile.resource_availability.control ∧ (ownership.contact ⇒ resource_availability.contact)`（chained handoff の offer が cell に無い資源を主張する経路を閉じる・違反 = `R_PROFILE_MISBOUND`・v0.2.3 CD-06）; (i) doc 06 §8.3 の `ProfileRegistry` で `permit.profile_hash` の head record（= registry append seq 最大・fork は registry が拒否）が `state == ACCEPTED ∧ proposed_lease.mode ∈ allowed_lease_modes ∧ 有効期限内 ∧ P_ACCEPTANCE_RECORD_INVALID == 0 を head で再評価（role 充足・operator 相異）`（v0.2.6 R3-21 / R4-04）であり、record の hash field を発行時に再検証する（v0.2.6 R4-09: 第 2 評価点の required set は `evidence_set_hash` が指す集合の**内側**で満たす（追加 evidence = 新 generation）；validator の content hash == `record.validator_hash`；`timing_baseline_hash` の artifact を解決して再検証；不一致 = `R_PROFILE_MISBOUND`；`record.role_registry_hash` == doc 06 §8.3 role registry の現 head（不一致 = `R_PROFILE_SUSPENDED`・v0.2.7 R6-05））。permit はその `acceptance_record_hash` / `generation` を束縛する（registry 不読 = `R_REGISTRY_UNAVAILABLE`・permit 不発行；SUSPENDED / REVOKED / 世代不一致 = `R_PROFILE_SUSPENDED`・v0.2.5 OPP-13。**cell 単位の停止（v0.2.6・R3-09）**: 同一 `cell_identity_hash` を持つ他 profile の head record が `state ∈ {SUSPENDED, REVOKED}`（新 generation の ACCEPTED で置換されていない）なら本 profile も `R_PROFILE_SUSPENDED`（兄弟 profile による迂回を閉じる。v0.2.7 R5-12: 述語を head 状態に固定し、条件 12 と head-check にも同じ節を置く）。旧 v0.2.4 の `accepted_profiles` / `revoked_profiles` 2 集合は本 record に置換）; (k) `validity_deadline_mono` と `effective_expires_at` を発行時に導出して permit に固定（v0.2.5・OPP-11 / OP-19）; (l) **clock 健全性（v0.2.6・R4-15）**: `wall_now ≥ max(required record の measured_at, approvals[].t)` ∧ wall / mono の drift が baseline diagnostic item の許容内 ∧ `wall_now` が直前の PERMIT_ISSUED の wall より単調。いずれか偽 = `R_CLOCK_ANOMALY`・permit 不発行。PERMIT_ISSUED payload に `(wall_now, mono_now)` を記録。周期 drift 検査（baseline 項目）の失敗 = TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \| SAFE_STOP); (m) **監視系の生存（v0.2.7・R5-03）**: DeploymentValidityMonitor の直近 heartbeat が baseline 項目 `VALIDITY_MONITOR_LIVENESS` 内 ∧ baseline `diagnostic_items` の全項目が直近周期内に pass（評価不能 / 欠落 = FALSE）∧ 直近の head-check が周期内に成功。違反 = `R_REGISTRY_UNAVAILABLE`（FAULT payload trigger = MONITOR_LOST \| DIAGNOSTIC:<item> \| HEAD_CHECK）・permit 不発行（monitor 喪失で SafeHold に落ちた系が monitor 不在のまま再 lease する flap を閉じる。manager は registry を書かない = 06 §8.3 read-only のまま）; (j) profile が宣言する**全ての** content hash = doc 06 §2.1 の `*_sha256` / `*_hash` 名の全 field（列挙: `predicate_sha256` / `evaluator_sha256` / `zones[].geometry_sha256` / `calibration_refs[].artifact_sha256` / `gateway_config.artifact_sha256` / `deployment_evidence_policy_hash` = H_WCJ(解決した policy) / `cell.kinematic_layout.artifact_sha256` / `inter_arm_restrictions.pairwise_keepout_sha256[]` / `inter_arm_restrictions.swept_volume_predicate_sha256[]` / `initiation_strengthening.conjuncts[].schema_hash`（frozen InitiationSpec と同型の payload schema hash） / `cell.arms[].tool_payload.finger_geometry_sha256`（RS71 §0 #4 の pinned gripper geometry・v0.2.7 R6-01） / required `DeploymentEvidenceRecord.artifact_sha256`。(j) の対象外 = `binding_expectations[].tensor_binding_hash`（frozen D1.1-B の hash・(g) が等値束縛する）。checker Q2 が 06 §2.1–2.2 の hash field 名が本区間に宣言 class ごとに 1 回以上現れることを機械検査・v0.2.6 R3-17 / R4-02・v0.2.7 R6-13）が解決先の内容と一致（doc 06 §3・違反 = `R_PROFILE_MISBOUND`・v0.2.3 CD-04・v0.2.4 R1-05 / R2-03 で全 hash へ一般化）。permit は発行時にこれらの結果 ref を束縛する。permit が CONFLICT / VOID になった場合、manager は ACK 元 executor へ `PERMIT_VOIDED` を通知し executor は提案を破棄する（v0.2.2・B-L6）。
- AuthorityManager は permit を `UNUSED | CONSUMED | VOID` の 3 状態で保持する。`CONSUMED` は CAS 成功の同一線形化点でのみ設定される。`VOID` = 失効 / 安全介入 / CAS 失敗。
- 同一 `expected` に対し複数の permit が並存してもよい（候補競合）。しかし CAS 成功は高々 1 つ（§3.8 証明 D）。

### 3.5 `AuthorityCas` と `HealthConfirmation`

```python
class CasKind(Enum): TRANSFER_TO_EXECUTOR | TRANSFER_TO_SAFEHOLD | MARK_BOUNDARY_WAIT   # v0.2.1: 第 3 の遷移（B-05）
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
1. `read_current() == cas.expected`（tuple 全体等値: owner / control_epoch / active_lease_id / consumed_offer_ids / safehold_reason / boundary_wait / seq）。
2. `permit.state == UNUSED ∧ now < permit.effective_expires_at`（v0.2.5・OPP-11: permit_ttl だけでなく ACK・decision age・validity deadline の最小値。**fault の優先（v0.2.6 R3-14）**: 到達した項が ACK なら `R_ACK_MISBOUND`（条件 3）、decision age なら `R_AUTHORITY_DECISION_ABSENT`（条件 6）、validity なら該当 `R_*_EXPIRED_ACTIVE` / `R_PROFILE_SUSPENDED`、ttl のみなら `R_PERMIT_EXPIRED` — 下位の失効が `R_PERMIT_EXPIRED` に優先する）` ∧ permit.expected == cas.expected ∧ cas.new_owner == EXECUTOR(permit.proposed_lease.executor_id) ∧ cas.new_lease_id == permit.proposed_lease.lease_id ∧ cas.consume_offer_id == permit.handoff_offer_id ∧ permit.profile_hash == permit.proposed_lease.profile_hash`（v0.2.2・B2-03: CAS 引数は permit に束縛される）。
3. `ack = resolve(permit.ack_id)`: `ack.expected_control_epoch == expected.control_epoch + 1 ∧ now < ack.valid_until（条件 2 と同じ厳密境界・v0.2.7 R5-07）∧ ack.invocation_id == permit.proposed_lease.invocation_id ∧ ack.handoff_offer_id == permit.handoff_offer_id ∧ ack.envelope_readback_ok ∧ ack.executor_id == permit.proposed_lease.executor_id ∧ ack.skill_action_id == permit.proposed_lease.skill_action_id ∧ ack.lease_proposal_id == permit.proposed_lease.lease_id`（v0.2.2・B-M4 / B2-03: ACK は executor・skill・lease 提案にも束縛）。
4. `cas.consume_offer_id ∉ expected.consumed_offer_ids`（offer がある場合）。
5. `permit.handoff_validation_report_ref`（offer がある場合）と `permit.invocation_validation_report_ref` が issues 空であり、前者の評価に用いた `authority_epoch_snapshot == expected.control_epoch`。
6. `proposed_lease.mode == CLOSED_LOOP_AUTHORITY ⇒ resolve(authority_decision_ref).granted == True ∧ now − decision.t_mono < decision_max_age_s`（厳密境界・v0.2.7 R5-07。age の CAS 時再検査・v0.2.5 OPP-11: permit 発行時に有効でも消費時に失効し得る）（frozen の `granted == True` 必要条件 `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:354`）かつ、decision の入力 `eligibility_report` が依拠する certificate（certificate-first `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:323`・`certificate.skill_action_id` `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:306`）の `skill_action_id == proposed_lease.skill_action_id`。⚠ frozen `AuthorityDecision` は profile を知らない（入力は 4 record のみ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:346-350`）ため、`profile_hash` の束縛は permit 側（条件 2）で行う（v0.2.2・A-01 / B-M5）。cell 固有の gate を `acceptance_state` / `safety_gate_state` に載せるかは O0/S0/V0 層の事項（§12 OP-18）。
7. `proposed_lease.accepted_envelope.satisfiable == True`。
8. `proposed_lease.skill_action_id` が certified（certificate 存在）。
9. IndependentSafetyLayer の直近 health ∈ {ok, degraded} かつ未処理の STOP/HOLD 決定が無い（D0 `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:318` heartbeat 欠落 ⇒ alive を仮定しない）。
10. `safehold_reason ∈ {SAFETY, SAFE_STOP, MANAGER_RESTART, GATEWAY_RESTART, CHECKPOINT_DISABLED}` の SAFEHOLD からの転送では、該当する clearance record（§5.4 — 集合は §5.4 と同一定義・v0.2.2・A2-01 / B2-07）が存在する。CHECKPOINT_DISABLED からの転送では新 lease の `InitializationRecord.previous_lease_id` に当該 lease を記録する。
11. **boundary guard（v0.2.2・B-H2 / B2-02）**: `expected.owner.kind == SAFEHOLD ∨ expected.boundary_wait == True`。違反 = REJECTED・`R_MIDSKILL_TRANSFER_BLOCKED`（mid-skill switching 経路は authority 層でも存在しない — INV-28）。
12. **registry 再検査（v0.2.5・OPP-13）**: doc 06 §8.3 registry の線形化読みで `permit.profile_hash` の head record が `record_hash == permit.acceptance_record_hash ∧ state == ACCEPTED ∧ generation == permit.acceptance_generation ∧ proposed_lease.mode ∈ allowed_lease_modes ∧ 同一 cell_identity_hash の他 profile の head record に state ∈ {SUSPENDED, REVOKED} が無い ∧ record.role_registry_hash == role registry の現 head（R6-05）`（v0.2.6 R4-16: hash 等値を含む・v0.2.7 R5-12: 兄弟節）。違反 = REJECTED・`R_PROFILE_SUSPENDED`（permit 発行後・CAS 前の SUSPENDED / REVOKED 競合を閉じる）。registry 不読 = REJECTED・`R_REGISTRY_UNAVAILABLE`。

事後条件（同一線形化点）:
- `AuthorityState := (EXECUTOR(executor_id), expected.control_epoch + 1, new_lease_id, expected.consumed_offer_ids ∪ {consume_offer_id}, None, False, expected.seq + 1)` + `safehold_disposition := None`（同一線形化点・v0.2.7 R5-05: 前 SAFEHOLD 期間の SAFE_STOP が新 lease の (iii) 窓へ漏れない）。
- `permit.state := CONSUMED`。同じ `expected` に束縛された他の permit は次の CAS 試行で条件 1 を満たさず `CONFLICT`（自動的に VOID）。
- **旧 epoch 拒否が有効化**: CommandGateway の admission は `AuthorityState` を線形化して読むため、この点以降 `control_epoch ≠ expected.control_epoch + 1` の command は `R_EPOCH_STALE_COMMAND`、`lease_id ≠ new_lease_id` の command は `R_LEASE_UNKNOWN_COMMAND`。
- **SafeHold 活性**: gateway 出力は新 lease の最初の admissible command が admit されるまで `SafeHold`（最初の安全 command）。旧 lease の直近 command は hold 地平にかかわらず即座に出力から外れる。
- **旧 lease 無効化**: `expected.active_lease_id` は `LEASE_INVALIDATED` 記録（reason = TRANSFER）。復活経路は存在しない。

**TRANSFER_TO_SAFEHOLD** の前提条件 = 条件 1 のみ（+ `safehold_reason` 非 null）。permit / ack / decision を要さない（SAFEHOLD owner は常に ready で常に安全側）。事後条件 = `(SAFEHOLD, epoch+1, None, consumed そのまま, reason, False, seq+1)` + `safehold_disposition := 当該遷移の実効 disposition`（reason SAFE_STOP ⇒ SAFE_STOP・v0.2.6 R3-13）+ 旧 lease 無効化 + 全 UNUSED permit の VOID。**再試行規則（v0.2.1・B-04）**: TRANSFER_TO_SAFEHOLD が `CONFLICT` した場合、AuthorityManager は current を再読して**即座に再試行**する（条件 1 しか無いため、再読後の試行は in-flight CAS が尽きれば必ず成功する — 有界）。**再試行中の gateway 出力（v0.2.3・B-M1 / B2-04 残差）**: safety 起因（SAFETY / SAFE_STOP）の CONFLICT では §5.2 (i) / (i′) / (iii) に既に落ちている。非 safety 起因（EXECUTOR_LOST / HEALTH_FAIL / DEADLINE_MISS / TIMING_VIOLATION / ENVELOPE_VIOLATION / CHECKPOINT_DISABLED / NO_CHAIN）では、CommandGateway は trigger を検出した時点で局所 flag `pending_invalidate` を立てて (iii) に落ち、再試行 CAS が SUCCESS するまで (ii) を評価しない（executor command の再 admit は無い）。manager 単独検出（EXECUTOR_LOST 等）で gateway への通知が CAS 完了より遅れる窓に限り、既 admit の setpoint 保持が最大 `command_deadline_s` 続き得る（新 command の admit は無い — INV-24）。**理由の優先順位（v0.2.2・B-M2 / B2-04）**: `SAFETY / SAFE_STOP` > `MANAGER_RESTART / GATEWAY_RESTART / CHECKPOINT_DISABLED` > その他。current が既に SAFEHOLD のとき TRANSFER_TO_SAFEHOLD は理由を**強める方向にしか**書き換えない（弱い理由への上書きは記録付き no-op = FAULT + audit・状態不変・epoch 不変 — INV-30）。**同 tier / 同 reason（v0.2.4・R1-03）**: reason は保持・epoch 不変の記録付き no-op とし、要求される clearance の**和集合**を CAS_ATTEMPT payload に記録する。いずれの no-op でも `safehold_disposition := max(現値, 実効 disposition)`（SAFE_STOP > HOLD）は同一線形化点で durable 更新する（B2-05 の例外が no-op で失われない）。manager 起動時は IndependentSafetyLayer に未解除決定を照会し、あれば reason = SAFETY で復帰する。**lease-scoped な理由**（EXECUTOR_LOST / HEALTH_FAIL / DEADLINE_MISS / TIMING_VIOLATION / ENVELOPE_VIOLATION / CHECKPOINT_DISABLED / NO_CHAIN / VALIDITY_EXPIRED の deadline 到達）の再試行は `current.active_lease_id == trigger.lease_id` のときのみ（v0.2.2・B-M1: 別 lease の誤無効化を防ぐ。不一致なら CAS を捨て元 lease への FAULT のみ記録）。non-lease-scoped（SAFETY / SAFE_STOP / MANAGER_RESTART / GATEWAY_RESTART）は無条件に再試行。**profile-scoped**（VALIDITY_EXPIRED の registry / monitor event・v0.2.6 R3-06）: event は `profile_hash` + `acceptance_record_hash` を運び、再試行は `current.active_lease.profile_hash == trigger.profile_hash` の間続ける（別 lease に切り替わっても同じ profile なら無効化する — SUSPENDED profile 上の新 lease が走り続けない）。**SAFE_STOP の設定（v0.2.2・B-M3 / B2-05）**: 実効 disposition（profile `EscalationPolicy` 適用後）が SAFE_STOP となる遷移は全て `TRANSFER_TO_SAFEHOLD(SAFE_STOP)` を用い、原因 fault は `RuntimeAuditRecord.fault` に別途記録する（(iii) は `state.safehold_disposition == SAFE_STOP` で SafeStop を出す — reason SAFE_STOP なら構成上 disposition も SAFE_STOP・v0.2.6 R3-13）。**例外（v0.2.3・B2-05 残差）**: IndependentSafetyLayer 起因の遷移（STOP 決定・heartbeat 欠落）は reason SAFETY を保つ（SafeStop 出力は (i) / (i′) から出る）。(iii) は `safehold_reason == SAFETY` でも、当該 SAFEHOLD 遷移の記録 disposition が SAFE_STOP なら §5.4 SAFETY 行の clearance record が記録されるまで SafeStop を出す（heartbeat が戻り (i′) が外れても SafeHold に緩まない）。

**MARK_BOUNDARY_WAIT**（v0.2.1・B-05）の前提条件 = 条件 1 ∧ `expected.owner.kind == EXECUTOR` ∧ 当該 lease の `SkillOutcome` を**受領した事実**（`validate_outcome` の report ref を issues の有無にかかわらず CAS に添える — v0.2.2・B2-06: issues 非空でも `boundary_wait := True` とし、以後は `R_OUTCOME_INVALID` → B5 NO_CHAIN 経路）。`S_HEALTH_PENDING` 中の受領も同じ（v0.2.2・B2-10: pending の HealthConfirmation は取消し、未確認の事実を ASSESSMENT に記録）。事後条件 = `boundary_wait := True`（他の要素不変・`seq+1`・epoch は**進めない** — lease は活性のまま）。この線形化点以降、CommandGateway は当該 lease の command を `R_POST_OUTCOME_COMMAND` で拒否し出力 = SafeHold（§5.2 (ii) の条件に `¬state.boundary_wait` を含める）。TRANSFER_TO_EXECUTOR / TRANSFER_TO_SAFEHOLD はこの後に通常どおり行う（条件 1 は `boundary_wait` を含む tuple 等値）。

### 3.6 R1 — offer の検証は CAS 前、消費は CAS 内

frozen `validate_handoff` は `offer.control_epoch == authority_epoch_snapshot` の**等値検査**である（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:381`）。producer は旧 epoch `e` の下で offer を出す（`offer.control_epoch == e`）。したがって:

1. Orchestrator は `snapshot = AuthorityManager.read_snapshot()` を取り、`validate_handoff(invocation, offer, producer_def, consumer_def, authority_epoch_snapshot=snapshot.control_epoch)` を **CAS 前**に呼ぶ（`invocation` = **producer の** `SkillInvocation`・`offer.producer_invocation_id` と一致 `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:381` — v0.2.2・A-11）。`E_HANDOFF_EPOCH_STALE` を含む issues 非空 ⇒ `R_OFFER_INVALID` ⇒ disposition `RESELECT`（offer は捨てる。再検証は新 snapshot で）。
2. 検証を通った offer の `handoff_offer_id` は `CommitPermit.handoff_offer_id` に束縛され、**CAS の tuple 要素 `consumed_offer_ids` として CAS 内で消費**される（§3.5 条件 4・事後条件）。
3. CAS 後の epoch は `e+1` ゆえ、同じ offer を再度 validate すると `E_HANDOFF_EPOCH_STALE`、再度 CAS に載せると `R_OFFER_REUSED`（条件 4）。二重に遮断される。

### 3.7 遷移表と失敗経路

状態（manager 視点。`AuthorityState` と permit 台帳の射影）:

| state | 定義 |
|---|---|
| `S_SAFEHOLD(reason)` | owner.kind == SAFEHOLD |
| `S_LEASE_ACTIVE(mode)` | owner.kind == EXECUTOR ∧ HealthConfirmation 済 |
| `S_HEALTH_PENDING` | owner.kind == EXECUTOR ∧ HealthConfirmation 未 |
| `S_BOUNDARY_WAIT` | owner.kind == EXECUTOR ∧ `boundary_wait == True`（lease は活性・gateway = SafeHold・当該 lease の command は R_POST_OUTCOME_COMMAND） |
| `S_TRANSFER_PENDING` | 上記いずれか + UNUSED permit ≥ 1 |

遷移（全て `AuthorityCas` 経由。表外遷移は存在しない）:

| from | 事象 | CAS | to | 記録 |
|---|---|---|---|---|
| `S_SAFEHOLD` / `S_BOUNDARY_WAIT` | ack → permit → CAS 成功 | TRANSFER_TO_EXECUTOR | `S_HEALTH_PENDING` | EPOCH_TRANSITION, LEASE_ACTIVATED, LEASE_INVALIDATED(旧 lease がある場合のみ), PERMIT_CONSUMED, CAS_ATTEMPT（v0.2.4・R1-10） |
| `S_HEALTH_PENDING` | HealthConfirmation 全 True（timeout 内） | なし | `S_LEASE_ACTIVE(mode)` | HEALTH_CONFIRMED |
| `S_HEALTH_PENDING` | 失敗 / timeout | TRANSFER_TO_SAFEHOLD(HEALTH_FAIL \| SAFE_STOP per profile.escalation.on_health_fail) | `S_SAFEHOLD(HEALTH_FAIL \| SAFE_STOP)` | HEALTH_FAILED, FAULT(R_HEALTH_CONFIRM_FAILED \| R_HEALTH_CONFIRM_TIMEOUT), DISPOSITION(HOLD \| SAFE_STOP)（v0.2.2） |
| `S_LEASE_ACTIVE` / `S_HEALTH_PENDING` | `SkillOutcome`（`TerminalOutcome`）受領（issues の有無を問わず） | MARK_BOUNDARY_WAIT（v0.2.1） | `S_BOUNDARY_WAIT` | CAS_ATTEMPT, ASSESSMENT — 以後 当該 lease の command = R_POST_OUTCOME_COMMAND。issues 非空 = FAULT(R_OUTCOME_INVALID) → B5（v0.2.2） |
| `S_LEASE_ACTIVE` / `S_HEALTH_PENDING` | `InterruptOutcome`（reason = PLANNED_SWITCH / EVENT）受領 | TRANSFER_TO_SAFEHOLD(CHECKPOINT_DISABLED) | `S_SAFEHOLD(CHECKPOINT_DISABLED)` | ASSESSMENT, FAULT(R_CHECKPOINT_SWITCH_DISABLED), DISPOSITION(HOLD) — v0.2 は checkpoint 切替を実行しない（§6.1） |
| `S_LEASE_ACTIVE` / `S_HEALTH_PENDING` | `InterruptOutcome`（reason = SAFETY_STABILIZED）受領 | TRANSFER_TO_SAFEHOLD(SAFETY) | `S_SAFEHOLD(SAFETY)` | ASSESSMENT, DISPOSITION(HOLD) — 解除 = §5.4 SAFETY 行（v0.2.2・A-10 / B-L1） |
| `S_BOUNDARY_WAIT` | 候補なし / `boundary_dwell_s` 超過 / `max_reselect_attempts` 超過 | TRANSFER_TO_SAFEHOLD(NO_CHAIN \| SAFE_STOP per profile.escalation.on_no_chain) | `S_SAFEHOLD(NO_CHAIN \| SAFE_STOP)` | DISPOSITION(NO_CHAIN → HOLD \| SAFE_STOP), 超過時 FAULT(R_BOUNDARY_DWELL_EXCEEDED)（v0.2.2・B-M9） |
| any (EXECUTOR) | executor heartbeat 喪失 | TRANSFER_TO_SAFEHOLD(EXECUTOR_LOST) | `S_SAFEHOLD(EXECUTOR_LOST)` | FAULT(R_EXECUTOR_LOST), DISPOSITION(HOLD) |
| any (EXECUTOR) | gateway: command deadline miss / envelope 違反 | TRANSFER_TO_SAFEHOLD(DEADLINE_MISS \| ENVELOPE_VIOLATION) | `S_SAFEHOLD(…)` | FAULT, DISPOSITION(HOLD) |
| any | IndependentSafetyLayer STOP / HOLD | TRANSFER_TO_SAFEHOLD(SAFETY) | `S_SAFEHOLD(SAFETY)` | SAFETY_OVERRIDE, PERMIT_VOIDED(全), FAULT(R_SAFETY_OVERRIDE), DISPOSITION(HOLD \| SAFE_STOP by decision.action)（v0.2.4・R1-09） |
| any (EXECUTOR) | IndependentSafetyLayer の heartbeat が `safety_heartbeat_timeout_s` を超えて欠落 / health == failed（v0.2.2・B2-01 / B-H3） | TRANSFER_TO_SAFEHOLD(SAFETY) | `S_SAFEHOLD(SAFETY)` | FAULT(R_SAFETY_LAYER_LOST), DISPOSITION(SAFE_STOP) — gateway は欠落を観測した時点で (ii) を評価せず (i′) SafeStop |
| any (EXECUTOR) | `R_COMMAND_KIND_MISMATCH` が連続 `command_kind_mismatch_max` 回（v0.2.2・B2-15） | TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION) | `S_SAFEHOLD(ENVELOPE_VIOLATION)` | FAULT(R_ENVELOPE_VIOLATION), DISPOSITION(HOLD) |
| `S_LEASE_ACTIVE` / `S_HEALTH_PENDING` | lease 活性時間（LEASE_ACTIVATED からの経過）が `lease_max_duration_s` を超過（v0.2.3・CD-10 — WAIT / TIMEOUT 非宣言 skill でも lease は有限） | TRANSFER_TO_SAFEHOLD(TIMING_VIOLATION) | `S_SAFEHOLD(TIMING_VIOLATION)` | FAULT(R_LEASE_DURATION_EXCEEDED), DISPOSITION(HOLD) |
| `S_LEASE_ACTIVE` / `S_HEALTH_PENDING` / `S_BOUNDARY_WAIT`（mode を問わず・v0.2.6） | `now ≥ lease.validity_deadline_mono`（calibration / evidence / acceptance の期限到達・manager clock・v0.2.5 OP-19。lease 時間上限は別行 R_LEASE_DURATION_EXCEEDED。到達項目の sub-kind（TCP / camera / SAFETY_LAYER_ACCEPTANCE 等）は `lease.profile_hash` の profile（calibration_id → kind）と evidence store（record_id → kind）から遷移時に解決し、解決不能 = 表に無い = SAFE_STOP・v0.2.7 R5-08） | TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \| SAFE_STOP — `validity_deadline_source` の到達項目を doc 06 §5 (b) 表で引く・表に無い = SAFE_STOP・v0.2.6 R3-05) | `S_SAFEHOLD(VALIDITY_EXPIRED \| SAFE_STOP)` | FAULT(R_CALIBRATION_EXPIRED_ACTIVE \| R_EVIDENCE_EXPIRED_ACTIVE \| R_PROFILE_SUSPENDED — 到達項目の kind = CALIBRATION / EVIDENCE / ACCEPTANCE に対応・v0.2.7 R5-08 / R6-21), DISPOSITION(HOLD \| SAFE_STOP) |
| any (EXECUTOR) | DeploymentValidityMonitor の失効 event = registry に `SUSPENDED(reason)` record を append した**後**の通知（reason ∈ doc 06 §8.3 `SuspensionReason`・v0.2.6 R4-11: 記録なしの event は無い。event は profile_hash + acceptance_record_hash を運ぶ） | TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \| SAFE_STOP per doc 06 §5 (b) reason→disposition 表) | `S_SAFEHOLD(…)` | FAULT(R_PROFILE_SUSPENDED — payload EVENT・reason。R_EVIDENCE_EXPIRED_ACTIVE は対応する SuspensionReason が無いため本行から除去・v0.2.7 R5-02), DISPOSITION(HOLD \| SAFE_STOP)・全 UNUSED permit VOID |
| any (EXECUTOR) | **manager 側 head-check**（baseline `diagnostic_items` の周期・monitor 非依存・registry の読みは条件 12 と同じ線形化読み・v0.2.6 R3-08・v0.2.7 R5-02 で副場合ごとに fault と disposition を固定）: (a) `head(registry, lease.profile_hash)` の `record_hash ≠ lease.acceptance_record_hash ∨ state ≠ ACCEPTED`、または同一 `cell_identity_hash` を持つ他 profile の head record が state ∈ {SUSPENDED, REVOKED}（新 generation の ACCEPTED で置換されていない）（R5-12）; (b) registry が head-check 周期を超えて読めない; (c) DeploymentValidityMonitor の heartbeat が baseline 項目 `VALIDITY_MONITOR_LIVENESS` の上限を超えて欠落; (d) baseline diagnostic item の失敗（drift 項目 / identity 再検証 / proof-test・`AUDIT_RECORDER_LIVENESS`（R5-06）・R3-20）; (e) cell_id の baseline registry head ≠ `record.timing_baseline_hash`（R6-10） || TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \| SAFE_STOP) — disposition は副場合ごと: (a) head.state ∈ {SUSPENDED, REVOKED} = head.suspension_reason を doc 06 §5 (b) 表で（REVOKED / 不読 = 表に無い = SAFE_STOP）、head が新 generation の ACCEPTED（record_hash ≠ ∧ state == ACCEPTED）= HOLD（payload GENERATION_SUPERSEDED・R5-13）、兄弟 SUSPENDED / REVOKED = その reason の行; (b)(c) = HOLD; (d) drift 項目 = CLOCK_ANOMALY 行（SAFE_STOP）・他の項目 = DIAGNOSTIC_FAILURE 行（HOLD・`on_validity_expired` で強化可）; (e) = BASELINE_SUPERSEDED 行（HOLD）。(c)(d) の disposition は起草既定（OP-19 残 open・Rs が強化可） || `S_SAFEHOLD(VALIDITY_EXPIRED \| SAFE_STOP)` | FAULT: (a) R_PROFILE_SUSPENDED（payload trigger = HEAD_CHECK・sub = SUSPENDED \| REVOKED \| GENERATION_SUPERSEDED \| SIBLING_SUSPENDED）; (b) R_REGISTRY_UNAVAILABLE（HEAD_CHECK）; (c) R_REGISTRY_UNAVAILABLE（MONITOR_LOST）; (d) drift = R_CLOCK_ANOMALY（DRIFT）・他 = R_EVIDENCE_EXPIRED_ACTIVE（DIAGNOSTIC:<item>）・recorder = R_AUDIT_UNAVAILABLE（RECORDER_LIVENESS）; (e) R_PROFILE_SUSPENDED（BASELINE_SUPERSEDED）, DISPOSITION |
| any (EXECUTOR) | INTER_ARM 項の違反（同一 command の両 arm 提案線分の対、または提案 arm の線分 × 静止 arm の点が pairwise keep-out / min separation / swept-volume predicate に反する）（v0.2.5・OPP-15 B+・v0.2.6） | TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION) | `S_SAFEHOLD(ENVELOPE_VIOLATION)` | FAULT(R_INTER_ARM_VIOLATION), DISPOSITION(HOLD) |
| any | AuthorityManager 再起動 | TRANSFER_TO_SAFEHOLD(MANAGER_RESTART)（durable state からの復帰 CAS） | `S_SAFEHOLD(max(persisted reason, MANAGER_RESTART))`（persisted が同 tier 以上なら reason・epoch 保持 — 失敗表 R_MANAGER_RESTART 行と同一・v0.2.4 R1-03） | MANAGER_RESTART, FAULT(R_MANAGER_RESTART) |
| any | CommandGateway 再起動（v0.2.1・B-09） | TRANSFER_TO_SAFEHOLD(GATEWAY_RESTART)（gateway は SafeHold 出力で起動し manager へ再起動を報告。manager が CAS） | `S_SAFEHOLD(GATEWAY_RESTART)` | GATEWAY_RESTART, FAULT(R_GATEWAY_RESTART), DISPOSITION(HOLD) — 再起動前の lease は再 admit されない（新 lease のみ） |
| any (permit 発行後) | Orchestrator 喪失（v0.2.1・B-14） | なし（permit は失効で VOID） | 不変（SAFEHOLD なら SafeHold 継続、BOUNDARY_WAIT なら SafeHold 継続） | FAULT(R_PERMIT_EXPIRED), DISPOSITION(HOLD) — Orchestrator は無状態ゆえ新 instance が B0 から再開する |

失敗経路（各 timeout / failure に disposition を必ず割り当てる — fail-closed 既定）:

| 失敗 | 検出者 | fault | 状態への効果 | disposition |
|---|---|---|---|---|
| ACK が `ack_timeout_s` 内に届かない | Orchestrator | `R_ACK_TIMEOUT` | 変化なし（現 owner 継続・gateway = SafeHold） | `RESELECT`（次候補）/ 候補尽きれば `NO_CHAIN` |
| ACK の束縛不一致（epoch/offer/invocation）または CAS 時点で ACK 失効（`now ≥ ack.valid_until`・条件 3・v0.2.7 R5-07）（v0.2.4・R1-07） | AuthorityManager | `R_ACK_MISBOUND` | 変化なし（CAS REJECTED） | `RESELECT` |
| CAS 条件 9 不成立（IndependentSafetyLayer の health 不良 / 未処理 STOP・HOLD 決定）（v0.2.4・R1-07） | AuthorityManager | `R_SAFETY_OVERRIDE`（未処理決定）/ `R_SAFETY_LAYER_LOST`（health failed・heartbeat 欠落） | CAS REJECTED・状態不変（safety 側の遷移は該当行） | 該当行の disposition（`HOLD` / `SAFE_STOP`） |
| CAS 条件 10 不成立（clearance record 不在）（v0.2.4・R1-07） | AuthorityManager | `R_PERMIT_MISBOUND`（CAS_ATTEMPT payload に欠落した clearance を記録） | CAS REJECTED・状態不変 | 変化なし（clearance 待ち・permit は VOID） |
| permit 失効 = `effective_expires_at` 到達（CAS 未試行・どの項の到達でも本 code・v0.2.7 R5-07） | AuthorityManager | `R_PERMIT_EXPIRED` | permit VOID | `RESELECT`（ACK から再取得） |
| CAS 条件 2 で validity 項（`validity_deadline_mono`）または decision age 項が到達（v0.2.7・R5-07） | AuthorityManager | `R_CALIBRATION_EXPIRED_ACTIVE` / `R_EVIDENCE_EXPIRED_ACTIVE` / `R_PROFILE_SUSPENDED` / `R_AUTHORITY_DECISION_ABSENT`（条件 2 の優先規則） | CAS REJECTED・permit VOID・状態不変（活性 lease は無い — 同 code の活性 lease 行と区別） | `RESELECT`（新 permit は §3.4 (b)(e)(i) で原因解消を要求） |
| permit 再使用 | AuthorityManager | `R_PERMIT_REUSED` | 拒否・変化なし | `HOLD`（異常経路・audit 必須） |
| permit 束縛不一致 | AuthorityManager | `R_PERMIT_MISBOUND` | permit VOID | `RESELECT` |
| CAS conflict（expected ≠ current） | AuthorityManager | `R_CAS_CONFLICT` | 変化なし・permit VOID | 現状態に従う（SAFEHOLD なら `RESELECT`、EXECUTOR なら継続） |
| offer 再使用 | AuthorityManager | `R_OFFER_REUSED` | 拒否・変化なし | `RESELECT`（新 offer 待ち）/ 無ければ `HOLD` |
| validate_handoff 失敗（`E_HANDOFF_EPOCH_STALE` 等） | Orchestrator | `R_OFFER_INVALID` | 変化なし | `RESELECT` |
| validate_invocation_start 失敗 | Orchestrator | `R_INVOCATION_INVALID` | 変化なし | `RESELECT` / `RE_OBSERVE`（freshness 起因） |
| 新 executor が CAS 後に crash | gateway/manager | `R_EXECUTOR_LOST` \| `R_HEALTH_CONFIRM_TIMEOUT` | TRANSFER_TO_SAFEHOLD | `HOLD`（旧 owner 不復活） |
| HealthConfirmation 失敗 | AuthorityManager | `R_HEALTH_CONFIRM_FAILED` | TRANSFER_TO_SAFEHOLD(HEALTH_FAIL) | `HOLD`（profile が SAFE_STOP へ強化可） |
| AuthorityManager crash/restart | manager（起動時） | `R_MANAGER_RESTART` | durable state を読む。persisted owner が EXECUTOR、または persisted が SAFEHOLD で reason が MANAGER_RESTART より弱いときのみ `epoch := persisted + 1`・owner := SAFEHOLD(MANAGER_RESTART)；persisted が SAFEHOLD(SAFETY / SAFE_STOP) なら reason と epoch を保持（INV-30 / T-28・v0.2.3 B-M2 残差）。いずれも全 lease 無効・全 permit VOID。durable state 不読 ⇒ 起動拒否 | `HOLD`（不読 = `SAFE_STOP` + operator 介入） |
| 転送中の safety override | IndependentSafetyLayer | `R_SAFETY_OVERRIDE` | 出力は即 safety 決定（ack 不要）。in-flight CAS は線形化順で「先に成功 → 直後の safety CAS で無効化」か「後 → CONFLICT」のいずれか | `HOLD`（STOP なら `SAFE_STOP`） |
| CLOSED_LOOP 要求で decision 不在/未 granted | AuthorityManager | `R_AUTHORITY_DECISION_ABSENT` | 拒否・変化なし | `HOLD`（SHADOW への降格は自動で行わない — 別 permit） |
| SHADOW lease から actuation 要求 | CommandGateway | `R_SHADOW_OUTPUT_ATTEMPT` | 記録のみ・出力なし | 変化なし（lease 継続・audit） |
| outcome 受領後に producer が command を出す（v0.2.1・B-05） | CommandGateway | `R_POST_OUTCOME_COMMAND` | 拒否・出力 = SafeHold・状態不変 | 変化なし（`S_BOUNDARY_WAIT` 継続・audit） |
| command 種別が lease.control_mode と不一致（v0.2.1・B-10） | CommandGateway | `R_COMMAND_KIND_MISMATCH` | 拒否のみ・lease 継続 | 変化なし（連続 `command_kind_mismatch_max` 回で TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION) — 閾値は profile `RuntimeTimeouts`・v0.2.2） |
| lease_id 不明の command・または `cmd.executor_id ≠ lease.executor_id`（v0.2.1・B-10・v0.2.6 R3-19） | CommandGateway | `R_LEASE_UNKNOWN_COMMAND` | 拒否のみ | 変化なし（audit） |
| authority decision の inputs 束縛不一致（v0.2.1・B-10） | AuthorityManager | `R_AUTHORITY_DECISION_MISBOUND` | permit VOID | `RESELECT` |
| profile 束縛不一致 / timing 等値違反 / profile の時刻依存検査 失敗（v0.2.1・B-10, C-10） | AuthorityManager（permit 発行時） | `R_PROFILE_MISBOUND` | permit 不発行 | `HOLD`（profile 側の是正 = 新 profile・新 lease） |
| profile の health check（BEFORE_PERMIT / BOTH）失敗（v0.2.1・C-07） | AuthorityManager（permit 発行時） | `R_HEALTHCHECK_FAILED` | permit 不発行 | `HOLD` |
| profile の initiation 強化 conjunct が偽（v0.2.1・C-06） | Orchestrator（B4） | `R_PROFILE_INITIATION_FAILED` | 変化なし | 次候補 / `RESELECT` |
| gateway が `manager_liveness_s` 内に AuthorityState を読めない（v0.2.1・B-10） | CommandGateway | `R_MANAGER_UNAVAILABLE` | 出力 = (iii) SafeHold・lease は形式上継続 | manager 復帰時に TRANSFER_TO_SAFEHOLD(MANAGER_RESTART) と同じ経路で `HOLD` |
| inter-command 間隔の逸脱（v0.2.1・B-10） | CommandGateway | `R_TIMING_VIOLATION` | TRANSFER_TO_SAFEHOLD(TIMING_VIOLATION) | `HOLD` |
| RecoveryRoutingPolicy が certified 外 / 空の候補を返す（v0.2.1・B-10） | Orchestrator | `R_NO_CANDIDATE` | 変化なし | `RESELECT` → 尽きれば `NO_CHAIN` |
| CommandGateway 再起動（v0.2.1・B-09） | CommandGateway → AuthorityManager | `R_GATEWAY_RESTART` | 起動時出力 = SafeHold。manager が TRANSFER_TO_SAFEHOLD(GATEWAY_RESTART) | `HOLD`（旧 lease の再 admit 無し） |
| Orchestrator 喪失（permit 発行後）（v0.2.1・B-14） | AuthorityManager（permit 失効） | `R_PERMIT_EXPIRED` | permit VOID・状態不変 | `HOLD`（新 Orchestrator instance が B0 から再開） |
| 旧 epoch / 無効化 lease の command（v0.2.2・B-M11 / B2-09） | CommandGateway | `R_EPOCH_STALE_COMMAND` | 拒否のみ・状態不変 | 変化なし（audit） |
| lease 無効化の記録（v0.2.2） | AuthorityManager | `R_LEASE_INVALIDATED` | LEASE_INVALIDATED 記録（原因 fault と対） | 原因行の disposition に従う |
| command deadline 超過（v0.2.2） | CommandGateway | `R_DEADLINE_MISS` | TRANSFER_TO_SAFEHOLD(DEADLINE_MISS) | `HOLD` |
| envelope 項の違反（v0.2.2） | CommandGateway | `R_ENVELOPE_VIOLATION` | 拒否 + TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION) | `HOLD` |
| AcceptedEnvelope 充足不能（v0.2.2） | AuthorityManager（permit 発行時 / CAS 前提 7） | `R_ENVELOPE_EMPTY` | permit 不発行 / CAS REJECTED | `RESELECT`（次候補）→ 尽きれば `NO_CHAIN` |
| InterruptOutcome（PLANNED_SWITCH / EVENT）受領（v0.2.2） | AuthorityManager | `R_CHECKPOINT_SWITCH_DISABLED` | TRANSFER_TO_SAFEHOLD(CHECKPOINT_DISABLED) | `HOLD` |
| boundary 外からの転送要求（v0.2.2・B-H2 / B2-02） | AuthorityManager | `R_MIDSKILL_TRANSFER_BLOCKED` | permit 不発行 / CAS REJECTED・状態不変 | 変化なし（audit・lease 継続）。Orchestrator は `boundary_dwell_s` 内に snapshot を再読して再要求（v0.2.4・R1-13） |
| IndependentSafetyLayer の heartbeat 欠落 / health failed（v0.2.2・B2-01） | CommandGateway / AuthorityManager | `R_SAFETY_LAYER_LOST` | 出力 = SafeStop（(i′)）+ TRANSFER_TO_SAFEHOLD(SAFETY) | `SAFE_STOP`（解除 = §5.4 SAFETY 行） |
| lease 活性時間が `lease_max_duration_s` 超過（v0.2.3・CD-10） | AuthorityManager | `R_LEASE_DURATION_EXCEEDED` | TRANSFER_TO_SAFEHOLD(TIMING_VIOLATION)・lease 無効 | `HOLD`（解除 = §5.4 TIMING_VIOLATION 行 = 完全経路） |
| lease の `validity_deadline_mono` 到達（calibration / evidence / acceptance 期限・v0.2.5 OP-19） | AuthorityManager | `R_CALIBRATION_EXPIRED_ACTIVE` / `R_EVIDENCE_EXPIRED_ACTIVE` / `R_PROFILE_SUSPENDED`（ACCEPTANCE 到達・v0.2.7 R5-08） | TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \| SAFE_STOP)・lease 無効・UNUSED permit VOID | `HOLD` / `SAFE_STOP`（doc 06 §5 (b) 表で決まる — 安全機能・TCP・停止性能（FI 含む）の失効は SAFE_STOP・v0.2.7 R6-17） |
| profile の SUSPENDED / REVOKED / 世代不一致（permit 発行時・CAS 条件 12・活性 lease 中の event）（v0.2.5・OPP-13） | AuthorityManager / DeploymentValidityMonitor | `R_PROFILE_SUSPENDED` | permit 不発行 / CAS REJECTED / 活性 lease（mode を問わず・v0.2.7 R5-01）は TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \| SAFE_STOP if 安全起因) | `HOLD` / `SAFE_STOP` |
| registry（doc 06 §8.3）が読めない（v0.2.5・OPP-13・v0.2.6 R3-07 で範囲を明示） | AuthorityManager | `R_REGISTRY_UNAVAILABLE` | 起動時 / permit 発行 / CAS では拒否（診断用 SAFEHOLD での起動は可・新規 actuation なし）。活性 lease は継続するが、head-check 周期（baseline diagnostic item）を超えて読めない場合は TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)（R3-08）。permit 発行時の (m) 違反（monitor 喪失 / 診断失敗）も本 code（v0.2.7 R5-03） | `HOLD` |
| wall-clock の異常（過去へ戻る / required evidence や approvals より前 / drift 超過）（v0.2.6・R4-15） | AuthorityManager（permit 発行時・周期 drift 検査） | `R_CLOCK_ANOMALY` | permit 不発行。活性 lease 中の周期検査失敗 = TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \| SAFE_STOP) | `HOLD` / `SAFE_STOP` |
| AuditRecorder が record を append できない / 応答しない（v0.2.7・R5-06） | AuthorityManager / CommandGateway | `R_AUDIT_UNAVAILABLE` | CAS SUCCESS の executor への通知・permit VOID 通知・HealthConfirmation の受理は当該 record の durable append 後（`permit.state := CONSUMED` 自体は線形化点のまま・INV-04）。recorder 不能が baseline diagnostic item `AUDIT_RECORDER_LIVENESS` の周期を超えれば head-check 行 (d) と同じ経路で TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)・全 UNUSED permit VOID。書けなかった record は復旧後に元の `t_mono` で遡って append する。gateway が `COMMAND_ADMITTED` の append 不能で admission を同期 block するかは OP-5 の open note | `HOLD` |
| INTER_ARM 項の違反（v0.2.5・OPP-15） | CommandGateway | `R_INTER_ARM_VIOLATION` | command 拒否 + TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION) | `HOLD` |
| validate_outcome の issues 非空（v0.2.2・B2-06 / A2-12） | Orchestrator（B1） | `R_OUTCOME_INVALID` | 状態 = S_BOUNDARY_WAIT（MARK_BOUNDARY_WAIT は受領の事実で実行済） | 候補評価を行わず `NO_CHAIN` → HOLD \| SAFE_STOP |
| boundary 滞留 / 再選択回数の超過（v0.2.2・B-M9） | Orchestrator / AuthorityManager | `R_BOUNDARY_DWELL_EXCEEDED` | TRANSFER_TO_SAFEHOLD(NO_CHAIN \| SAFE_STOP) | `NO_CHAIN` → HOLD \| SAFE_STOP |
| permit の CONFLICT / VOID の通知（v0.2.2・B-L6） | AuthorityManager → Executor | （fault なし・`PERMIT_VOIDED` 記録） | executor は提案を破棄 | 変化なし |

### 3.8 証明

**証明 A（P1 no-double-ownership）**。`AuthorityState` は AuthorityManager だけが書き、書込みは `AuthorityCas` の線形化点でのみ起こる（§3.2, §3.5）。CommandGateway の admission は `AuthorityState` を線形化して読み、`(cmd.lease_id, cmd.control_epoch) == (state.active_lease_id, state.control_epoch)` を要求する（§3.5 事後条件）。2 つの command `c1`（lease `L1`）と `c2`（lease `L2`, `L1 ≠ L2`）が同一の状態 `s` の下で admit されたと仮定すると、`L1 == s.active_lease_id == L2` となり矛盾。よって同一線形化点で actuation を駆動できる lease は高々 1 つ。lease は `executor_id` を 1 つだけ持つ（§4.1）ため executor についても同じ。D0 の「one atomic token flip … exactly one owner at every instant」（`$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:270-272`）を、`control_ownership` 1 field でなく tuple 全体の CAS として実現している。

**証明 B（P2 no-orphan-output）**。gateway 出力関数 `out(t)` を §5.2 のとおり定義する: (i) IndependentSafetyLayer の未解除決定があればその出力（最優先・D0 `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:319`）; (ii) さもなくば `state.owner.kind == EXECUTOR ∧ mode == CLOSED_LOOP_AUTHORITY` かつ hold 地平内の admitted command があればその command; (iii) さもなくば `SafeHold`（`safehold_reason == SAFE_STOP` なら `SafeStop`）。(i)(ii)(iii) は全域を覆い互いに排他（優先順位で決定的）。CAS の線形化点では (ii) の admitted command 集合が空にリセットされ (iii) に落ちる（事後条件「SafeHold 活性」）ため、転送の瞬間にも出力は定義される。旧 lease の command は線形化点以降 admit されない（`R_EPOCH_STALE_COMMAND`）ため (ii) に旧 lease は現れない。よって全ての `t` で `out(t)` は定義され、かつ (ii) に現れる lease は P1 により高々 1 つ。

**証明 C（P3 replay / stale）**。`consumed_offer_ids` は CAS tuple の一部（§3.2）。offer `o` を消費する 2 つの CAS `x, y` が共に成功したと仮定する。`x` の成功後、状態の `consumed_offer_ids` は `o` を含む（事後条件）。`y` は条件 1 で `expected == current` を要するが、`y.expected` が `x` の成功前の状態なら `seq`/`consumed_offer_ids` が異なり CONFLICT、`x` の成功後の状態なら条件 4（`o ∉ consumed`）が偽で REJECTED（`R_OFFER_REUSED`）。いずれも `y` は成功しないので矛盾。stale について: validation に用いた snapshot `e` は `permit.expected.control_epoch` として permit に固定され（条件 5）、CAS は `expected.control_epoch == current.control_epoch` を要する（条件 1）。epoch が動いた後は条件 1 が偽になるので、旧 snapshot で通った validation は決して commit されない。

**証明 D（P4 permit one-shot）**。`permit.state` は `UNUSED → CONSUMED` へ CAS 成功の線形化点でのみ遷移し、`CONSUMED`/`VOID` は条件 2 を偽にする。同一 permit を用いる 2 つの CAS が共に成功したとすると、2 つ目は 1 つ目の線形化点以降に評価されるので条件 2 が偽 — 矛盾。失効は `now < effective_expires_at`（v0.2.6）の条件 2 で遮断。

**証明 E（P5 単調・非復活）**。全ての CAS 成功は `control_epoch := expected.control_epoch + 1`（両 kind 共通）ゆえ epoch は成功列に沿って厳密増加。`new_lease_id` は AuthorityManager が発行する fresh id で、無効化済 id の集合と交わらない（INV-11 で機械検査）。したがって「旧 owner の復活」（無効化された lease の再活性）は型上・手続上とも存在せず、旧 executor が再び owner になるには新 ReadinessAck → 新 CommitPermit → 新 CAS（新 epoch・新 lease）のみ。HealthConfirmation 失敗時に旧 owner へ戻す経路も同理由で存在しない（SafeHold へ落ちる）。

## 4. Lease binding

### 4.1 `ActiveAuthorityLease`（post-commit・ちょうど 1 つ活性）

```python
class LeaseMode(Enum): SHADOW_NON_AUTHORITY | CLOSED_LOOP_AUTHORITY     # 新語 — EP evidence profile と同名にしない（別軸・§11）
class EnvelopeTermKind(Enum): INTRINSIC_D11B | DEPLOYMENT_WORKSPACE | CONTROLLER | SAFETY_RESTRICTION | INTER_ARM   # v0.2.6（R3-02）: INTER_ARM を term として実体化（条件 7 / INV-36 の対象）

@dataclass(frozen=True)
class TimingBinding:                                  # 新語 — D1.1-B 値の等値 copy（narrow しない）+ profile 由来 timeout
    tensor_binding_hash: str | None                   # LEARNED ⇔ 非 null（ExecutionBundle.tensor_binding.artifact_hash）/ SCRIPTED・WAIT = null
    policy_rate_hz: CanonicalDecimal | None           # == TimingSpec.policy_rate_hz（等値必須）
    obs_sampling_rate_hz: CanonicalDecimal | None     # == TimingSpec.obs_sampling_rate_hz（等値必須）
    action_rate_hz: CanonicalDecimal | None           # == ActionTimingSpec.action_rate_hz（等値必須）
    hold: ActionHold | None                           # == ActionTimingSpec.hold（等値必須・frozen B enum 参照）
    training_max_obs_staleness_s: CanonicalDecimal | None   # 記録のみ（訓練時仮定 — 執行しない）
    runtime_max_staleness_s: CanonicalDecimal | None  # = FreshnessPolicy.max_staleness_s を profile が stricter-or-equal に narrow した値（執行値）
    ack_validity_s: CanonicalDecimal                  # v0.2.1（B-11 / C-12）: ReadinessAck.valid_until = t_receive + ack_validity_s（manager clock・§3.2 clock domain・profile 由来・v0.2.3 CD-13）
    ack_timeout_s: CanonicalDecimal                   # profile 由来（数値は本 doc に書かない）
    permit_ttl_s: CanonicalDecimal
    health_confirm_timeout_s: CanonicalDecimal
    command_deadline_s: CanonicalDecimal              # ≥ 1/action_rate_hz（LEARNED）。超過 = R_DEADLINE_MISS（計時範囲 = §4.2・v0.2.4 R1-01）
    manager_liveness_s: CanonicalDecimal              # gateway が線形化読みを待つ上限（超過 = (iii)）
    safety_heartbeat_timeout_s: CanonicalDecimal      # v0.2.2（B2-01）: IndependentSafetyLayer heartbeat の欠落上限（超過 = (i′) SafeStop + R_SAFETY_LAYER_LOST）
    decision_max_age_s: CanonicalDecimal              # v0.2.2（B2-14）: permit 発行時に AuthorityDecision に許す最大 age
    boundary_dwell_s: CanonicalDecimal                # v0.2.2（B-M9）: boundary 滞留の上限（超過 = R_BOUNDARY_DWELL_EXCEEDED → NO_CHAIN）
    max_reselect_attempts: int                        # v0.2.2（B-M9）: 1 boundary あたりの候補試行上限
    command_kind_mismatch_max: int                    # v0.2.2（B2-15）: 連続 kind 不一致の許容回数
    inter_command_jitter_s: CanonicalDecimal          # v0.2.2（B-L2）: inter-command 間隔の許容偏差（超過 = R_TIMING_VIOLATION）
    lease_max_duration_s: CanonicalDecimal            # v0.2.3（CD-10）: lease 活性時間の上限（超過 = R_LEASE_DURATION_EXCEEDED → TRANSFER_TO_SAFEHOLD(TIMING_VIOLATION)）

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
    acceptance_record_hash: str                       # v0.2.5（OPP-13）: permit から複写（generation を含む record の hash）
    validity_deadline_mono: float                     # v0.2.5（OP-19）: permit から複写。到達 = TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)（mode を問わず・保守側・v0.2.6 R4-18。SHADOW は actuation が無いので実害なし）
    validity_deadline_source: tuple[tuple[str, str, float], ...]   # v0.2.6（R3-05）: permit から複写
    authority_decision_ref: str | None                # CLOSED_LOOP_AUTHORITY ⇒ 非 null ∧ granted == True；SHADOW では None 可（存在すれば記録のみ・v0.2.6 R3-03）
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
- 実測 inter-command 間隔が profile 許容（`inter_command_jitter_s`）を超えて逸脱 ⇒ `R_TIMING_VIOLATION` ⇒ TRANSFER_TO_SAFEHOLD(TIMING_VIOLATION) ⇒ `HOLD`。
- **`command_deadline_s` / `inter_command_jitter_s` の計時範囲（v0.2.4・R1-01）**: 計時は `owner == EXECUTOR ∧ ¬boundary_wait ∧ 当該 lease で admitted command ≥ 1` のときのみ（mode は問わない — SHADOW でも admission 判定は行うため deadline / jitter は計測でき、結果の SafeHold は記録のみ。v0.2.6 R3-11: R2-01 の commissioning evidence が最初の CLOSED_LOOP 前に作れる）。S_BOUNDARY_WAIT では停止（滞留上限 = `boundary_dwell_s`）、初回 command 前の上限は `health_confirm_timeout_s`（`first_command_admitted`）。よって TERMINAL boundary が DEADLINE_MISS に化けて再選択が SAFEHOLD 起動（B1 の offer 検証を迂回）へ逸れることは無い。executor heartbeat 義務（`R_EXECUTOR_LOST`）は LEASE_INVALIDATED まで継続。
- **hold の適用範囲（v0.2.2・B2-13）**: `hold` は連続 2 つの **admitted** command の間にのみ適用する。後続 command が未 admit の間、gateway は直近 admitted setpoint を保持する（hold 種別にかかわらず ZOH 相当・外挿禁止）。`command_deadline_s` 超過で SafeHold + `R_DEADLINE_MISS`。
- **WAIT lease（v0.2.2・B-M6）**: `first_command_admitted` と `command_deadline_s` は `control_mode ∈ {DIFF_IK_EE_TARGET, SCRIPTED_SEQUENCE}` にのみ適用し、WAIT では両者を N/A = True として記録する。WAIT の liveness は executor heartbeat（`R_EXECUTOR_LOST`）で担う。
- 鮮度: `runtime_max_staleness_s` は frozen `FreshnessPolicy.max_staleness_s` を出発点とし profile は stricter-or-equal のみ。`training_max_obs_staleness_s`（= D1.1-B `max_obs_staleness_s`）は記録のみ（`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:99` の役割分離）。
- `FreshnessPolicy.max_staleness_s = None` の意味は frozen v2 に規定が無い（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151` は型のみ）。本 doc は **runtime 層の読み**として None = 上限なしと扱い、profile は有限値への強化のみ可（profile None = 強化なし = frozen 値が執行値；`P_FRESHNESS_RELAXED` ⇔ `p > f` — doc 06 §3 が SSOT・v0.2.3 CD-12）。None のまま lease を作る場合は `runtime_max_staleness_s = None` を loud 記録し、`BeliefRef.ttl` / `ood_flag` による検査（§6.2 B2）は継続する（§12 OP-16）。

### 4.3 `AcceptedEnvelope`（R6: 表現ごとに評価される連言）

| term | source | 表現 | 評価者 | 備考 |
|---|---|---|---|---|
| INTRINSIC_D11B | `tensor_binding_hash`（D1.1-B `ActionBinding.features[].bounds` + `action_scale` / `transform` の適用順） | policy action space | CommandGateway | 適用順 = raw → normalizer → transform → bounds → cast（`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:65-66`）。**bounds は再定義しない**。LEARNED のみ存在（§12 OP-2） |
| DEPLOYMENT_WORKSPACE | profile `WorkspaceRestriction`（keep-out / reach / height） | workspace | CommandGateway（FK 後） | doc 06。評価対象 = `DIFF_IK_EE_TARGET` では hold 種別にかかわらず**線分**（直前 admitted setpoint → 新 setpoint；初回は実測 TCP → setpoint・FK 後の TCP 点）— 物理的な腕は setpoint 間を連続に動くため ZOH でも点評価では keep-out を跨げる（v0.2.4・R1-06 / R2-19）。hold は時間 parameterization のみを変える。tool 形状は評価しない（doc 06 §4・OPP-14・v0.2.3 CD-18）。gateway は評価前に zone geometry の解決内容 sha256 を `geometry_sha256` と再検証し、不一致 = 評価不能 = FALSE（v0.2.4・R1-05） |
| CONTROLLER | profile `ControllerEnvelope`（velocity / acceleration / jerk / ee_speed — admission 可能な運動学項のみ） | joint space | CommandGateway | 制御周波数は含まない（R5）。`ee_force_max` / `joint_torque_max` は command から評価不能なため admission 項ではなく**監視上限**（IndependentSafetyLayer / controller が測定値で監視・v0.2.3 CD-07） |
| SAFETY_RESTRICTION | profile `SafetyRestrictionSet`（静的） | gateway predicate | CommandGateway | IndependentSafetyLayer の live 決定は本 term ではなく §5.2 (i) の優先出力。gateway は評価前に predicate の解決内容 sha256 を `predicate_sha256` と再検証し、不一致 = 評価不能 = FALSE（v0.2.3・CD-04） |
| INTER_ARM（v0.2.5・OPP-15 B+・v0.2.6 R3-01 / R4-01） | profile `InterArmRestrictionSet`（min separation / pairwise keep-out / swept-volume predicate・content hash 付き）+ `CellKinematicLayoutRef`（両 arm の base transform） | workspace（両 arm） | CommandGateway | 評価対象 = **同一 command（同一 cmd_seq）の `arm_targets` が提案する両 arm の線分の対**（直前 admitted setpoint → 新 setpoint・同一時間 parameterization・FK 後の TCP 点）を pairwise keep-out / min separation（TCP 点間距離）/ swept-volume predicate で連言評価。command が 1 arm しか提案しない場合、他 arm は直近 admitted setpoint での**点**（同一線形化 snapshot で静止を確認・動いていれば評価不能 = FALSE）。評価前に layout / pairwise keep-out / swept-volume predicate の解決内容 sha256 を宣言と再検証し、不一致 = 評価不能 = FALSE（R3-17 / R4-02）。動的干渉の独立監視は IndependentSafetyLayer（本 term の代替ではない・AND） |

- 意味論: command `c` は admissible ⇔ 全 term `T` について `T.admit(c) == True`（INTER_ARM は両 arm の状態を同一 snapshot で連言評価・v0.2.5）。term の評価不能（表現変換不可・profile 未解決） = FALSE（fail-closed）。
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

`LeaseMode` の member 名を EP profile 名と一致させないのは、evidence profile（EP `requested_profile`）と runtime の出力可否を型で分離するため。lease は `authority_decision_ref` 経由で（frozen `evaluate_authority_grant` の入力 `eligibility_report` `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:346-347`）eligibility report の `requested_profile` を**参照するのみで再評価しない**。`profile_hash`（doc 06）は evidence profile を運ばない（v0.2.2・A-04）。

### 4.5 Lease 無効化 trigger（全て `LEASE_INVALIDATED` 記録 + `R_LEASE_INVALIDATED` または個別 fault）

TRANSFER_TO_EXECUTOR 成功（reason TRANSFER）／ HealthConfirmation 失敗・timeout ／ executor heartbeat 喪失 ／ command deadline miss ／ envelope 違反 ／ timing 違反（TIMING_VIOLATION）／ IndependentSafetyLayer STOP・HOLD ／ AuthorityManager 再起動 ／ CommandGateway 再起動（v0.2.1）／ profile_hash の更新要求（新 lease 経路へ）／ `NO_CHAIN` 後の SAFEHOLD 転送 ／ **validity deadline 到達・deployment 失効 event・profile の SUSPENDED / REVOKED（VALIDITY_EXPIRED・v0.2.5 OP-19 / OPP-13）** ／ INTER_ARM 項の違反（v0.2.5）。RETRACT / FORCE_LIMIT は既定では lease を無効化せず出力を override する（profile が無効化へ強化可 — §12 OP-8）。

## 5. 出力ヌル準備・HOLD・safe stop

### 5.1 `SafeHold` の定義（gateway における「null output」の意味）

`SafeHold` = gateway が**自ら**出す定義済みの安全側 command であって「信号なし」ではない。control_mode 別:

| lease.control_mode（frozen） | SafeHold の内容 |
|---|---|
| `DIFF_IK_EE_TARGET`（LEARNED） | **計測現在姿勢で凍結・速度 0**（直近 admitted EE target を目標に保持し続けない — 無効化 lease の運動意図を残さない・v0.2.2・B-M8）。新しい運動要求を出さない |
| `SCRIPTED_SEQUENCE` | 現在関節目標の保持（sequence を進めない） |
| `WAIT` | no-op（元々運動 command を出さない） |

`SafeStop` = `SafeHold` + profile `ControllerEnvelope` が定義する stop-class 要求。SHADOW_NON_AUTHORITY では actuation port が DISABLED なので `SafeHold`/`SafeStop` は**記録上の状態**であり物理 command は出ない。「hold が物理的に何をするか」（controller 固有・skill 固有の safe-hold 保証）は本 doc の外（future static candidate・§12 OP-4）。

```python
@dataclass(frozen=True)
class GatewayCommand:                                 # 新語（v0.2.2・B-L3）— gateway が admission 判定する command の記録形
    lease_id: str
    control_epoch: int
    executor_id: str
    cmd_seq: int                                      # lease 内で厳密単調増加（重複・逆順 = R_TIMING_VIOLATION で拒否）
    kind: ControlMode                                 # frozen enum（lease.control_mode と等値必須）
    arm_targets: tuple[tuple[str, str], ...]          # v0.2.6（R3-01 / R4-01 / R3-16）: (resource_id ∈ {ee_left, ee_right}, setpoint_ref) — この command が提案する arm ごとの setpoint。DUAL-ARM regime では通常 2 entry。1 entry の command は他 arm が直近 admitted setpoint で静止していることを前提にし、gateway はそれを線形化 snapshot で確認する
    payload_ref: str
    t_issue: float
```

### 5.2 出力優先順位（D0 §F の優先を runtime で固定）

```text
out(t) =
  (i)   IndependentSafetyLayer の未解除 SafetyDecision があれば その出力（STOP/HOLD/RETRACT/FORCE_LIMIT）   … 最優先・ack を待たない
  (i′)  else if IndependentSafetyLayer の heartbeat が safety_heartbeat_timeout_s を超えて欠落 → SafeStop（(ii) を評価しない・v0.2.2・B2-01）
  (ii)  else if owner == EXECUTOR ∧ ¬state.boundary_wait ∧ ¬restart_pending ∧ ¬pending_invalidate ∧ mode == CLOSED_LOOP_AUTHORITY ∧ 直近 admitted command あり → その setpoint（hold は admitted 間のみ・§4.2。`pending_invalidate`（VALIDITY_EXPIRED の deadline / event を含む・v0.2.6 R3-06）= gateway が TRANSFER_TO_SAFEHOLD の trigger を検出してから、再試行 CAS の SUCCESS **または** 線形化読みで trigger の lease が既に非活性（`state.active_lease_id ≠ trigger.lease_id ∨ owner.kind == SAFEHOLD`）と分かるまで True・v0.2.3 B-M1 / B2-04・v0.2.4 R1-16: lease-scoped CAS が捨てられても flag が残らない）
  (iii) else SafeHold（`state.safehold_disposition == SAFE_STOP` なら SafeStop — 線形化読み・v0.2.4 R1-03。SAFETY 理由でも当該期間の実効 disposition が SAFE_STOP なら clearance record まで SafeStop・v0.2.3 B2-05）
```

- (i) は D0 「preemption acts first, does not wait for ack」（`$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:319`）。runtime は (i) を上書きできない。
- CAS の線形化点で (ii) の集合は空にされる（§3.5 事後条件「SafeHold 活性」= 最初の安全 command）。
- admission は `AuthorityState` の**同期・線形化読み**で行う（cache を持たない — v0.2.2・B-H1）。読みが `manager_liveness_s` 内に完了しない場合、(ii) を評価せず (iii) に落ちる（INV-19）。
- **再起動した gateway（v0.2.2・B-M10）**: 起動時に `restart_pending := True` とし、`AuthorityState.safehold_reason == GATEWAY_RESTART`（または `seq` > 起動時観測 seq）を観測するまで (i)/(i′)/(iii) のみを評価する（INV-25 の執行規則）。

### 5.3 boundary での「producer retains ownership and safe-stops (or re-observes)」の実現

D0 §E の fail-closed 規則（`reject` / `abort` / `timeout` ⇒ producer retains — `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:273-274`）は本 doc では次のとおり: producer の `SkillOutcome` 受領後も lease は活性のまま（`S_BOUNDARY_WAIT`）、executor は新しい運動 command を出さず gateway 出力は (iii) SafeHold。転送が成立しなければその状態が続き、`NO_CHAIN` なら TRANSFER_TO_SAFEHOLD。すなわち「producer retains ownership」= lease 活性の継続、「safe-stops」= SafeHold/SafeStop、「re-observes」= disposition `RE_OBSERVE`。

### 5.4 HOLD を解除できる者

| `safehold_reason` | 解除経路 | 追加前提（CAS 条件 10） |
|---|---|---|
| INITIAL / NO_CHAIN / EXECUTOR_LOST / DEADLINE_MISS / TIMING_VIOLATION / ENVELOPE_VIOLATION / HEALTH_FAIL / VALIDITY_EXPIRED（v0.2.5） | 完全経路（ACK → permit → CAS）による TRANSFER_TO_EXECUTOR のみ（VALIDITY_EXPIRED では新 permit が §3.4 (b)(i)(l)(m) で失効原因の解消を要求する — deadline = (b)、event / head 不一致 = (i)、clock = (l)、monitor 喪失 / 診断失敗 = (m) が拒否（v0.2.7 R5-03）。event 起因なら registry の SUSPENDED record が新 generation + two-key で置換されるまで (i) が拒否する = 自動再 lease は無い・v0.2.6 R4-11） | なし |
| SAFETY | 同上 | IndependentSafetyLayer の clearance record（`stabilized_post_action_state` `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:320` の参照を含む）。executor 発の SAFETY_STABILIZED（ISL 決定が先行しない場合）では、ISL の clearance record が executor の報告した stabilized state を確認したものであること（確認不能なら CHECKPOINT_DISABLED 行と同じ operator clearance + 再観測）（v0.2.4・R1-14）。runtime は自ら解除しない |
| SAFE_STOP | 同上 | profile が定義する operator / health-check clearance（doc 06）。runtime は自ら解除しない |
| CHECKPOINT_DISABLED | 同上 | profile が定義する operator clearance + 再観測（doc 06）。解除後の転送は SAFEHOLD からの新規起動（§6.2 B0 から）であり、producer の resume ではない |
| MANAGER_RESTART | 同上 | durable state の整合検査記録 |
| GATEWAY_RESTART | 同上 | `GATEWAY_CONFIG_MATCH` health check の pass + profile が定義する clearance role（doc 06）（v0.2.2・A2-08 / B2-08） |

**clearance record の形と「該当」の定義（v0.2.3・CD-02）**: clearance record = `RuntimeAuditRecord`（kind = CLEARANCE_RECORDED・payload = `{safehold_reason, role, operator_ref, role_registry_hash, profile_hash, evidence_ref}`）。CAS 条件 10 の「該当する clearance record」= `record.safehold_reason == current.safehold_reason ∧ record.role ∈ profile.escalation.clearance_roles[reason] ∧ record.profile_hash == permit.profile_hash ∧ record.seq > 当該 SAFEHOLD 遷移の record.seq ∧ record.role_registry_hash == doc 06 §8.3 role registry の現 head ∧ (record.operator_ref, record.role) ∈ その registry`（v0.2.7 R6-06: role label の自己申告では解除できない。資格照合不能 = 該当 record 無し）。SAFETY 行は加えて IndependentSafetyLayer の clearance record（AND）。profile が当該 reason の role を 1 つも宣言しない場合は登録時に doc 06 `P_CLEARANCE_ROLE_MISSING`（定義なし = 解除不能 HOLD にも「任意の record で解除」にもしない）。

Orchestrator・Executor・RecoveryRoutingPolicy は HOLD を解除できない（AuthorityState を書けない）。CAS 条件 10 の集合 = 本表で「追加前提」を持つ行の集合 {SAFETY, SAFE_STOP, CHECKPOINT_DISABLED, MANAGER_RESTART, GATEWAY_RESTART}（両者を同一定義から導く — v0.2.2・A2-01 / B2-07）。

## 6. Boundary-only 実行（TERMINAL boundary）

### 6.1 boundary の種類

| 種類 | 到達条件 | v0.2 の扱い |
|---|---|---|
| TERMINAL boundary | `SkillOutcome.outcome` が `TerminalOutcome`（SUCCESS/FAILURE/TIMEOUT/INVALID_STATE） | 常に boundary。slice の既定（`$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59`） |
| CHECKPOINT（executor **自身**が `InterruptOutcome{checkpoint_id, reason}` を出し、`validate_outcome` が checkpoint ∈ checkpoint_specs を確認 `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:380`） | **v0.2 では受理のみ・再選択を開始しない（fail-closed）**: reason ∈ {PLANNED_SWITCH, EVENT} ⇒ TRANSFER_TO_SAFEHOLD(CHECKPOINT_DISABLED)・fault `R_CHECKPOINT_SWITCH_DISABLED`・disposition `HOLD`；reason == SAFETY_STABILIZED ⇒ TRANSFER_TO_SAFEHOLD(SAFETY)・fault なし（§3.7・§5.4 SAFETY 行と同一・v0.2.3 A-10 残差）。producer の resume も行わない。checkpoint での再選択（checkpoint 途中切替）は slice prereg が「Phase G / 別 gate」とし有効化 = chunk 改称 + scope 再審査（`$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59`）⇒ 本 doc の外。Orchestrator 発の中断（preemptive interrupt）は**存在しない**（§11） |

本 doc の「boundary」= **TERMINAL outcome のみ**（`$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59`）。frozen 型が `InterruptOutcome` を許容する事実（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151`）は変えず、受理後の runtime 処置を fail-closed に固定する。「no mid-skill switching」= Orchestrator は `TerminalOutcome` を受け取るまで再選択を開始しない（INV-21）。IndependentSafetyLayer の介入は boundary ではなく §5.2 (i) の出力優先で扱う（切替ではない）。

### 6.2 再選択・再初期化の手続（frozen validator を必ず経由）

```text
B0  AuditRecorder: ASSESSMENT 開始。snapshot := AuthorityManager.read_snapshot()。producer / offer がある場合は `snapshot.boundary_wait == True` を要求し、偽なら `boundary_dwell_s` 内に再読（MARK_BOUNDARY_WAIT の線形化を待つ）— permit 要求は boundary_wait 観測後のみ（v0.2.4・R1-13）
B1  validate_outcome(invocation, outcome, definition)                         … issues 非空 = R_OUTCOME_INVALID（v0.2.2）: MARK_BOUNDARY_WAIT は受領の事実で既に実行済（§3.5）。候補評価を行わず B5（NO_CHAIN）へ。SAFEHOLD からの起動（producer 無し）では B1 と offer 検証を skip し InitializationRecord.handoff_validation_report_ref = null
B2  belief := 現在の BeliefRef（value: SnapshotRef | HashRef）。stale/OOD（ttl 超過・ood_flag）= RE_OBSERVE（D0 §D OOD abstention）
B3  disposition_0 := §7 表（outcome × 候補有無）。RECOVERY_ROUTE なら RecoveryRoutingPolicy.route(query) → candidate ids
B4  候補 c ごとに（順序付き）:
      c.skill_action_id が certified か（§7-2）
      validate_invocation_start(new_invocation(c, control_epoch = snapshot.control_epoch + 1), definition_c, belief, now)   … now 明示
      offer あり: validate_handoff(producer_invocation, offer, producer_def, definition_c, authority_epoch_snapshot = snapshot.control_epoch)   … invocation = producer の SkillInvocation（A-11）
      profile.initiation_strengthening.conjuncts を belief に対して評価（全 True 必須・偽 = R_PROFILE_INITIATION_FAILED）／ 鮮度 = runtime_max_staleness_s（profile 強化後の値）で再判定（v0.2.1・C-06）
      AcceptedEnvelope(c).satisfiable ／ TimingBinding 等値 ／ mode 要件（CLOSED_LOOP なら AuthorityDecision.granted）
      全て通過 → ReadinessAck 要求（ack_timeout_s）→ CommitPermit 要求 → AuthorityCas
      いずれか失敗 → 次候補（fault を記録）
B5  候補が尽きた / boundary_dwell_s 超過 / max_reselect_attempts 超過（v0.2.2・B-M9） → NO_CHAIN → TRANSFER_TO_SAFEHOLD(NO_CHAIN | SAFE_STOP per profile.escalation.on_no_chain) → disposition HOLD | SAFE_STOP
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
    CONTINUE_AT_BOUNDARY | RESELECT | RE_OBSERVE | HOLD | SAFE_STOP | NO_CHAIN | RECOVERY_ROUTE   # v0.2.2: ABORT 削除（生成規則なし・B2-16）

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
    R_NO_CANDIDATE | R_SHADOW_OUTPUT_ATTEMPT | R_CHECKPOINT_SWITCH_DISABLED |
    R_POST_OUTCOME_COMMAND | R_GATEWAY_RESTART | R_HEALTHCHECK_FAILED | R_PROFILE_INITIATION_FAILED |   # v0.2.1
    R_MIDSKILL_TRANSFER_BLOCKED | R_SAFETY_LAYER_LOST | R_OUTCOME_INVALID | R_BOUNDARY_DWELL_EXCEEDED |   # v0.2.2
    R_LEASE_DURATION_EXCEEDED |   # v0.2.3（CD-10）
    R_PROFILE_SUSPENDED | R_REGISTRY_UNAVAILABLE | R_CALIBRATION_EXPIRED_ACTIVE | R_EVIDENCE_EXPIRED_ACTIVE | R_INTER_ARM_VIOLATION |   # v0.2.5
    R_CLOCK_ANOMALY | R_AUDIT_UNAVAILABLE   # v0.2.7（R5-06）: R_AUDIT_UNAVAILABLE = AuditRecorder の append 不能 / 停止。v0.2.6（round 3）（Rs 裁定: OPP-13 / OP-19 / OPP-15）— ProducerOutcome には足さない（§7 規則 1）
```

規則:

1. **`ProducerOutcome` は不変**（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151` の `TerminalOutcome | InterruptOutcome` のまま）。`NO_CHAIN` 等は runtime disposition であり、`SkillOutcome.outcome` / `TransitionRecord.outcome` に書かれることは無い（INV-20）。「failure/no-chain outcome を slice に含める」carry（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:570`）は、frozen `TerminationClass.FAILURE` + runtime `NO_CHAIN` disposition の**組**で表現する。
2. fault は常に disposition を伴う（fault だけで終わる経路は無い）。
3. frozen `E_*`（§5B の `E_HANDOFF_EPOCH_STALE` 等）は validator report に留まり、runtime は `R_OFFER_INVALID` / `R_INVOCATION_INVALID` / `R_OUTCOME_INVALID`（validate_outcome・v0.2.3 A2-12 残差）で包んで disposition に写す（validator の code を上書きしない）。

outcome × disposition（B3 の既定表。profile は SAFE_STOP 側へのみ強化可）:

| `ProducerOutcome` | 条件 | disposition 列 |
|---|---|---|
| Terminal SUCCESS | 候補あり・validation 通過・ACK 取得 | CONTINUE_AT_BOUNDARY |
| Terminal SUCCESS | 候補なし（chain 終端） | NO_CHAIN → HOLD（`profile.escalation.on_no_chain == SAFE_STOP` なら TRANSFER_TO_SAFEHOLD(SAFE_STOP)） |
| Terminal FAILURE / TIMEOUT | RecoveryRoutingPolicy が候補を返す | RECOVERY_ROUTE → CONTINUE_AT_BOUNDARY |
| Terminal FAILURE / TIMEOUT | 候補なし | NO_CHAIN → HOLD（profile で SAFE_STOP = TRANSFER_TO_SAFEHOLD(SAFE_STOP)） |
| Terminal INVALID_STATE | belief 再取得で解消し得る | RE_OBSERVE → RESELECT |
| Terminal INVALID_STATE | 解消せず | NO_CHAIN 経路 = §3.7 の S_BOUNDARY_WAIT 退出行（TRANSFER_TO_SAFEHOLD(NO_CHAIN \| SAFE_STOP per on_no_chain)・fault = `R_NO_CANDIDATE` / `R_BOUNDARY_DWELL_EXCEEDED`）— v0.2.4 R1-08 で §3.7 / B5 と同一定義に |
| Interrupt PLANNED_SWITCH / EVENT（CHECKPOINT） | v0.2 = checkpoint 切替 無効 | HOLD（fault `R_CHECKPOINT_SWITCH_DISABLED`・`safehold_reason = CHECKPOINT_DISABLED`・解除 = §5.4） |
| Interrupt SAFETY_STABILIZED | — | HOLD（`safehold_reason = SAFETY`・clearance 待ち） |
| outcome 無し（executor 喪失） | — | R_EXECUTOR_LOST → HOLD |

frozen `FailClosedAction`（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151`）→ disposition: `RE_OBSERVE → RE_OBSERVE` / `SAFE_STOP → SAFE_STOP` / `HANDBACK_TO_OWNER → HOLD`（lease を保持したまま SafeHold。「owner へ戻す」= 現 owner の継続であり、無効化済 lease への復帰ではない — §3.8 証明 E）。

## 8. Runtime audit evidence

```python
class AuditKind(Enum):
    EPOCH_TRANSITION | ACK_RECEIVED | PERMIT_ISSUED | PERMIT_CONSUMED | PERMIT_VOIDED |
    LEASE_ACTIVATED | LEASE_INVALIDATED | HEALTH_CONFIRMED | HEALTH_FAILED |
    COMMAND_REJECTED | SHADOW_COMMAND_RECORDED | SAFETY_OVERRIDE | FAULT | DISPOSITION | ASSESSMENT | MANAGER_RESTART |
    CAS_ATTEMPT | CLEARANCE_RECORDED | GATEWAY_RESTART | GENESIS_RECORDED |   # v0.2.1
    COMMAND_ADMITTED   # v0.2.2（B-L3）: CLOSED_LOOP lease の admitted command（GatewayCommand 参照・記録義務 = §8 本文）
    # v0.2.1（B-13）: CAS の CONFLICT/REJECTED も CAS_ATTEMPT で記録・clearance / genesis は独立 kind

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
    payload_ref: str                                  # kind 別の typed payload（ReadinessAck / CommitPermit / AuthorityCas / HealthConfirmation / RuntimeAssessmentRecord / GatewayCommand …）
    profile_hash: str | None                          # v0.2.2（B2-17）: deployment 起因 record（permit 発行時 fault・MANAGER_RESTART・GENESIS_RECORDED）の join key（lease 無しでも profile と結線）。permit 発行時の health-check-run record も lease_id = None・profile_hash 必須（doc 06 §6.1 の audit 範囲解決・v0.2.4 R2-07）
    fault: RuntimeFaultCode | None
    disposition: RuntimeDisposition | None
    schema_versions: SchemaVersionStamp               # frozen 型を再利用（recorder_artifact_hash を含む）
```

- 記録義務: §3.7 の全事象（CAS の SUCCESS/CONFLICT/REJECTED を含む）、全 permit 発行/消費/失効、全 ACK、全 health、全 fault/disposition、全 safety override（FAULT record の payload は trigger 副因を持つ — `R_SAFETY_LAYER_LOST`: HEARTBEAT_TIMEOUT | HEALTH_FAILED、`R_BOUNDARY_DWELL_EXCEEDED`: DWELL_TIMEOUT | ATTEMPTS_EXHAUSTED、`R_CALIBRATION_EXPIRED_ACTIVE` / `R_EVIDENCE_EXPIRED_ACTIVE`: DEADLINE | HEAD_CHECK | DIAGNOSTIC:<item> | CAS_COND2、`R_PROFILE_SUSPENDED`: EVENT | HEAD_CHECK | CAS_COND12 | PERMIT | DEADLINE、`R_REGISTRY_UNAVAILABLE`: HEAD_CHECK | MONITOR_LOST | DIAGNOSTIC:<item> | PERMIT | CAS_COND12 | STARTUP、`R_CLOCK_ANOMALY`: PERMIT | DRIFT、`R_AUDIT_UNAVAILABLE`: RECORDER_LIVENESS（trigger 語彙の SSOT = 本列挙。doc 06 `FaultInjectionRequirement.trigger` はここに無い語を P_FAULT_CODE_UNKNOWN で拒否・v0.2.7 R5-10 / R6-03） — doc 06 §6.1 の fault-injection evidence が timeout 経路を要求するため・v0.2.4 R2-01）、SHADOW の全 command 判定、**CLOSED_LOOP lease の全 admitted command（`COMMAND_ADMITTED`・`GatewayCommand` payload・v0.2.3 B-L3 残差）**。欠落 = INV-17 違反。**記録が先（v0.2.7・R5-06）**: CAS SUCCESS の通知・permit VOID 通知・HealthConfirmation の受理は当該 record の durable append 後。recorder 不能が baseline diagnostic item `AUDIT_RECORDER_LIVENESS` を超える = `R_AUDIT_UNAVAILABLE`（§3.7 失敗表・head-check 行 (d) の経路）。
- frozen `TransitionRecord` は boundary ごとに従来どおり recorder が書き、`safety_events`（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:521`）には本 doc の `SAFETY_OVERRIDE` record id を入れる（frozen field の語彙内）。
- **hash 方式 = 定めない**: 「runtime 記録の content-hash 化は WCJ 対象外・方式は D2 prereg で確定（明示 defer — U14）」（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:537`）。本 doc は record の**内容**と**義務**だけを定め、chain / content-hash / 署名は U14 の解決先に従う。
- **EP v1.9 との分離**: 本 record は EP の component / `claim_target` / `ProofKind` / grade のいずれでもなく、`evidence_policy_definition_hash`（`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:163`）に影響しない。EP の `usage_ceiling` も不変（`$D/WMSO_EvidencePolicy_v1.9.json:213`）。runtime 決定・epoch・lease・fault = runtime audit evidence（handoff F）。cell / controller / calibration / gateway / fault injection の evidence = doc 06 `DeploymentEvidencePolicy`。

## 9. Invariants と validation 規則（fail-closed 既定: 評価不能 = FALSE）

| id | 不変量（機械検査式） | 違反時 |
|---|---|---|
| INV-01 | `state.owner.kind == EXECUTOR ⇔ state.active_lease_id != None`; `state.owner.kind == SAFEHOLD ⇔ state.safehold_reason != None`; `state.owner.kind == SAFEHOLD ⇔ state.safehold_disposition != None`（v0.2.7 R5-05） | 起動拒否 / R_MANAGER_RESTART |
| INV-02 | 全 CAS SUCCESS: `new.control_epoch == expected.control_epoch + 1 ∧ new.seq == expected.seq + 1` | 設計違反（test） |
| INV-03 | admitted command: `(cmd.lease_id, cmd.control_epoch) == (state.active_lease_id, state.control_epoch)` を線形化点で満たし、`cmd.executor_id == lease.executor_id`（v0.2.4・R1-12・不一致 = `R_LEASE_UNKNOWN_COMMAND`・v0.2.6 R3-19）、`cmd.cmd_seq` は lease 内で厳密単調（v0.2.2） | R_EPOCH_STALE_COMMAND / R_LEASE_UNKNOWN_COMMAND / R_TIMING_VIOLATION |
| INV-04 | `permit.state` の遷移は `UNUSED→CONSUMED`（CAS SUCCESS の線形化点のみ）or `UNUSED→VOID`。`CONSUMED` の permit を持つ CAS SUCCESS は高々 1 | R_PERMIT_REUSED |
| INV-05 | CAS SUCCESS(offer o): `o ∉ expected.consumed_offer_ids ∧ o ∈ new.consumed_offer_ids` | R_OFFER_REUSED |
| INV-06 | `permit.expected.control_epoch == authority_epoch_snapshot`（handoff validation に渡した値）`== expected.control_epoch`（CAS 時） | R_CAS_CONFLICT |
| INV-07 | `ack.expected_control_epoch == permit.expected.control_epoch + 1 ∧ ack.valid_until ≥ permit.issued_at ∧ ack.invocation_id == proposed_lease.invocation_id ∧ ack.executor_id == proposed_lease.executor_id ∧ ack.skill_action_id == proposed_lease.skill_action_id ∧ ack.lease_proposal_id == proposed_lease.lease_id`（v0.2.2） | R_ACK_MISBOUND |
| INV-08 | `lease.mode == CLOSED_LOOP_AUTHORITY ⇒ lease.authority_decision_ref != None ∧ resolve(ref).granted == True` | R_AUTHORITY_DECISION_ABSENT |
| INV-09 | `lease.mode == SHADOW_NON_AUTHORITY ⇒` actuation port から当該 lease 由来の command が 0 件 | R_SHADOW_OUTPUT_ATTEMPT |
| INV-10 | 全 `t`: `out(t)` は §5.2 の (i)(ii)(iii) のちょうど 1 つ | 設計違反（test） |
| INV-11 | CAS SUCCESS の `new_lease_id ∉ invalidated_lease_ids`（無効化済集合との交わり空） | 設計違反（test） |
| INV-12 | LEARNED lease: `timing.{policy_rate_hz, obs_sampling_rate_hz, action_rate_hz, hold} == TensorBindingSpec(tensor_binding_hash).{…}`（等値） | R_PROFILE_MISBOUND |
| INV-13 | CAS SUCCESS(TRANSFER_TO_EXECUTOR): `proposed_lease.accepted_envelope.satisfiable == True` | R_ENVELOPE_EMPTY |
| INV-14 | `definition.required_control_resources ⊆ lease.ownership.control`（frozen `:380` の包含） | R_INVOCATION_INVALID |
| INV-15 | `lease.skill_action_id` に対する `ContractCertificate` が存在（Draft 不可） | 候補除外 |
| INV-16 | **型境界 + hash preimage の断定（v0.2.2・A-02 / A2-02 — 名前の非交差ではない）**: (a) runtime / profile 型の値は frozen 型として decode されない（frozen strict codec が runtime 固有 field〔lease_id / permit_id / profile_hash 等〕を unknown field として拒否 `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:385`）; (b) runtime / profile 型の値は frozen hash（SkillDefinitionHash / SkillActionId / ExecutionBundleHash / BehaviorSignature / tensor_binding_hash / evidence_policy_definition_hash）の preimage に入らない（03 matrix C01–C07）。frozen §8 の assert `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:550` は static hash の key 集合に対する主張であり、本 INV はその**趣旨を継承**する | 設計違反（test） |
| INV-17 | §3.7 の各事象について、その行が要求する record kind ごとにちょうど 1 件の `RuntimeAuditRecord`；加えて §8 記録義務の各項目（admitted command 等・§3.7 事象でないもの）について 1 件（v0.2.2・B2-17・v0.2.4 R1-10） | R_AUDIT_UNAVAILABLE（記録欠落 = fault・v0.2.7 R5-06） |
| INV-18 | SafetyDecision 受領の線形化点以降、同一 cycle の lease command admission に先立って (i) が適用され、全 UNUSED permit が VOID | 設計違反（test） |
| INV-19 | gateway の admission は `AuthorityState` の同期・線形化読みのみ（cache 不可）。読みが `manager_liveness_s` 内に完了しないとき (ii) を評価しない（v0.2.2・B-H1） | R_MANAGER_UNAVAILABLE |
| INV-20 | `RuntimeDisposition` / `RuntimeFaultCode` の値が `SkillOutcome.outcome` / `TransitionRecord.outcome` に現れない | 設計違反（test） |
| INV-21 | Orchestrator の再選択開始時刻 ≥ 当該 `SkillOutcome`（`TerminalOutcome`）受領時刻（preemptive interrupt なし）。`InterruptOutcome` からは再選択を開始しない | 設計違反（test） |
| INV-22 | `TimingBinding` の profile 由来 field（`RuntimeTimeouts` の全 field — v0.2.3 CD-13 で列挙から「全 field」へ）は `profile_hash` 由来で lease に写され、本 doc に数値定数は無い | R_PROFILE_MISBOUND |
| INV-23 | `state.boundary_wait == True` の線形化点以降、`state.active_lease_id` 由来の command は admit されない（v0.2.1・B-05） | R_POST_OUTCOME_COMMAND |
| INV-24 | TRANSFER_TO_SAFEHOLD の CONFLICT は必ず再試行される。CONFLICT 中の出力: safety 起因 = (i) / (i′) / (iii)；非 safety 起因 = gateway が検出時点で `pending_invalidate` により (iii)（(ii) を評価しない）。manager 単独検出で gateway 未通知の窓に限り既 admit setpoint の保持が最大 `command_deadline_s` 続き得る（新 command の admit は無い）（v0.2.1・B-04・v0.2.3 B-M1 / B2-04） | 設計違反（test） |
| INV-25 | CommandGateway の起動直後の出力 = SafeHold。再起動前の lease は新 CAS 無しに再 admit されない（v0.2.1・B-09） | R_GATEWAY_RESTART |
| INV-26 | durable store 不在 / 不読で AuthorityManager は起動しない。epoch が 0 から自動再開することは無い（genesis record は operator 行為・GENESIS_RECORDED）（v0.2.1・B-12） | 起動拒否 |
| INV-27 | 全 `RuntimeFaultCode` member は §3.7 の失敗表に行を持つ（v0.2.1・B-10・v0.2.2 で total 化 B-M11 / B2-09） | 設計違反（test） |
| INV-28 | TRANSFER_TO_EXECUTOR / permit 発行は `expected.owner.kind == SAFEHOLD ∨ expected.boundary_wait == True` のときのみ（boundary guard・v0.2.2・B-H2 / B2-02） | R_MIDSKILL_TRANSFER_BLOCKED |
| INV-29 | IndependentSafetyLayer の heartbeat が `safety_heartbeat_timeout_s` を超えて欠落した線形化点以降、(ii) は評価されず出力 = SafeStop、かつ TRANSFER_TO_SAFEHOLD(SAFETY) が発行される（v0.2.2・B2-01） | R_SAFETY_LAYER_LOST |
| INV-30 | `safehold_reason` は優先順位（SAFETY / SAFE_STOP > MANAGER_RESTART / GATEWAY_RESTART / CHECKPOINT_DISABLED > 他）を弱める方向に書き換えられない（v0.2.2・B-M2 / B2-04） | 設計違反（test） |
| INV-31 | 再起動した gateway は `safehold_reason == GATEWAY_RESTART` を観測するか、自分の再起動報告以後に `seq` が進んだ（= manager が復帰 CAS を線形化した）ことを観測するまで (ii) を評価しない（v0.2.2・B-M10・v0.2.4 R1-03） | R_GATEWAY_RESTART |
| INV-32 | CAS SUCCESS の線形化点 = durable commit 完了。`invalidated_lease_ids` は同一 durable store・同一 commit（v0.2.2・B-M12） | 設計違反（test） |
| INV-33 | `S_LEASE_ACTIVE` / `S_HEALTH_PENDING` における lease の活性時間（LEASE_ACTIVATED からの経過）は `lease_max_duration_s` 以下（超過 = TRANSFER_TO_SAFEHOLD(TIMING_VIOLATION) + `R_LEASE_DURATION_EXCEEDED`）— WAIT を含む。`S_BOUNDARY_WAIT` の滞留は `boundary_dwell_s` が上限（NO_CHAIN 経路・§3.7）ゆえ lease の総活性時間 ≤ `lease_max_duration_s + boundary_dwell_s`（v0.2.3・CD-10・v0.2.4 R1-15 / R2-12: boundary 滞留を TIMING_VIOLATION に写さない — R1-01 と同根） | R_LEASE_DURATION_EXCEEDED |
| INV-34 | lease は `validity_deadline_mono` を超えて活性でない（到達 = TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)・mode を問わず）。deadline = permit 発行時に wall-clock 期限を manager clock へ変換して固定した calibration / evidence / acceptance の min（lease 時間上限は INV-33）。到達項目は `validity_deadline_source` から決まる（v0.2.5・OP-19・v0.2.6 R3-04 / R3-05） | R_CALIBRATION_EXPIRED_ACTIVE / R_EVIDENCE_EXPIRED_ACTIVE / R_PROFILE_SUSPENDED |
| INV-35 | permit の消費（CAS SUCCESS）時点で acceptance record が ACCEPTED・同一 generation であり decision age ≤ decision_max_age_s（条件 6・12）。permit 発行時の検査だけで足りるとしない（v0.2.5・OPP-11 / OPP-13） | R_PROFILE_SUSPENDED / R_AUTHORITY_DECISION_ABSENT |
| INV-36 | admitted command は INTER_ARM 項を満たす: 同一 command の `arm_targets` が提案する両 arm の線分の対（1 arm 提案なら他 arm は線形化 snapshot で静止した点）を同一評価で連言（v0.2.5・OPP-15・v0.2.6 R3-01） | R_INTER_ARM_VIOLATION |

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
| T-09 | AuthorityManager kill → restart | persisted = EXECUTOR or 弱い reason: epoch = persisted + 1・owner = SAFEHOLD(MANAGER_RESTART)・旧 lease 無効；persisted = SAFEHOLD(SAFETY / SAFE_STOP): reason・epoch 保持（INV-30）。durable 不読 ⇒ 起動拒否（v0.2.3 B-M2 残差） |
| T-10 | executor heartbeat 喪失 | TRANSFER_TO_SAFEHOLD(EXECUTOR_LOST) |
| T-11 | SHADOW lease から actuation | actuation port 出力 0 件・SHADOW_COMMAND_RECORDED 記録（INV-09） |
| T-12 | CLOSED_LOOP 要求 × decision 不在 / granted=False | 拒否（R_AUTHORITY_DECISION_ABSENT）。SHADOW へ自動降格しない |
| T-13 | AcceptedEnvelope: 各 term 単独違反 × 5（INTER_ARM 含む・v0.2.6）・充足不能 profile | R_ENVELOPE_VIOLATION（term 別）/ R_ENVELOPE_EMPTY |
| T-14 | timing: action_rate_hz を profile で「narrow」した lease 提案 | R_PROFILE_MISBOUND（等値のみ許容） |
| T-15 | command deadline 超過 | SafeHold + R_DEADLINE_MISS（hold の無期限継続をしない） |
| T-16 | ランダム interleaving（model check）: 全 trace で INV-01/02/03/10/11 | 反例 0（探索範囲を宣言） |
| T-17 | audit 完全性: (事象, その §3.7 行が要求する record kind) ↔ record の全単射（欠落なし・重複なし）（v0.2.3・B2-17 残差） | INV-17 |
| T-18 | serialization boundary（v0.2.2）: runtime 固有 key（lease_id / permit_id / profile_hash）を持つ payload を frozen 型として decode すると unknown field で拒否される；runtime 型の値が frozen hash の preimage に現れない | INV-16 |
| T-19 | disposition 分離: `NO_CHAIN` が `ProducerOutcome` に現れない | INV-20 |
| T-20 | frozen validator との結線: `validate_handoff` に渡す snapshot が `read_snapshot()` 由来であること（隠れ状態参照なし） | 決定論再現 |
| T-21 | outcome 受領後の producer command（v0.2.1） | R_POST_OUTCOME_COMMAND・出力 SafeHold・状態不変（INV-23） |
| T-22 | safety CAS と transfer CAS の競合（v0.2.1） | safety CAS は再試行で成功・競合中の出力は (i)（INV-24） |
| T-23 | CommandGateway kill → restart（v0.2.1） | 起動出力 SafeHold・TRANSFER_TO_SAFEHOLD(GATEWAY_RESTART)・旧 lease 不再 admit（INV-25） |
| T-24 | durable store を消して AuthorityManager 起動（v0.2.1） | 起動拒否。genesis record 投入後のみ起動（INV-26） |
| T-25 | 各 RuntimeFaultCode member を 1 回ずつ発火（v0.2.1） | 失敗表の行どおりの状態効果・disposition（INV-27） |
| T-26 | S_LEASE_ACTIVE（boundary_wait = False）で permit 要求 / CAS（v0.2.2） | R_MIDSKILL_TRANSFER_BLOCKED・状態不変（INV-28） |
| T-27 | 活性 lease 中に ISL heartbeat を停止（v0.2.2） | (i′) SafeStop・TRANSFER_TO_SAFEHOLD(SAFETY)・R_SAFETY_LAYER_LOST（INV-29） |
| T-28 | SAFEHOLD(SAFETY) 中に MANAGER_RESTART / GATEWAY_RESTART / NO_CHAIN の CAS（v0.2.2） | 理由不変・記録付き no-op（INV-30）；同 tier / 同 reason の再遷移で reason・epoch 不変かつ `safehold_disposition` が max へ更新される（v0.2.4） |
| T-29 | validate_outcome issues 非空（v0.2.2） | boundary_wait = True・R_OUTCOME_INVALID・候補評価なし・NO_CHAIN 経路 |
| T-30 | in-memory CAS 成功直後・durable 書込み前に manager kill（v0.2.2） | restart 後に当該 CAS は無かったものとして扱われ epoch が二重に使われない（INV-32） |
| T-31 | S_HEALTH_PENDING 中に TerminalOutcome 受領（v0.2.2） | MARK_BOUNDARY_WAIT・health 取消・未確認事実を ASSESSMENT に記録 |
| T-32 | WAIT lease を `lease_max_duration_s` 超過まで放置（v0.2.3） | TRANSFER_TO_SAFEHOLD(TIMING_VIOLATION)・R_LEASE_DURATION_EXCEEDED・lease 無効（INV-33） |
| T-33 | 活性 CLOSED_LOOP lease 中に calibration の valid_until を経過（v0.2.5） | deadline 到達で TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)・R_CALIBRATION_EXPIRED_ACTIVE（TCP なら SAFE_STOP） |
| T-34 | permit 発行後・CAS 前に profile を SUSPENDED（v0.2.5） | CAS 条件 12 で REJECTED・R_PROFILE_SUSPENDED・permit VOID |
| T-35 | permit 発行後・CAS 前に decision age が decision_max_age_s を超過（v0.2.5） | 条件 6 で REJECTED・再評価要求 |
| T-36 | registry 不読で起動（v0.2.5） | 診断用 SAFEHOLD で起動可・permit / CAS / actuation 全面拒否・R_REGISTRY_UNAVAILABLE |
| T-37 | 左右 arm の提案線分が pairwise keep-out を跨ぐ command（v0.2.5） | INTER_ARM 項 FALSE・R_INTER_ARM_VIOLATION・TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION) |
| T-38 | CAS SUCCESS 直後に AuditRecorder を停止（v0.2.7） | executor へ LEASE_ACTIVATED が通知されない・`AUDIT_RECORDER_LIVENESS` 超過で TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)・R_AUDIT_UNAVAILABLE・復旧後に record を遡って append |
| T-39 | SAFE_STOP disposition の SAFEHOLD から clearance → CAS SUCCESS → 最初の command 前（v0.2.7） | (iii) 窓の出力 = SafeHold（SafeStop ではない）・`safehold_disposition == None` |
| T-40 | DeploymentValidityMonitor 停止中に permit 要求（v0.2.7） | 前提条件 (m) 不成立・R_REGISTRY_UNAVAILABLE（MONITOR_LOST）・permit 不発行 |
| T-41 | `now == ack.valid_until` で CAS（v0.2.7） | 条件 2 / 3 とも不成立（厳密境界）・R_ACK_MISBOUND・REJECTED |
| T-42 | 兄弟 profile（同一 cell_identity_hash）を SUSPENDED にして CAS（v0.2.7） | 条件 12 の兄弟節で REJECTED・R_PROFILE_SUSPENDED（SIBLING_SUSPENDED） |

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
| OP-2 | SCRIPTED / WAIT skill には D1.1-B `bounds` が無く INTRINSIC_D11B term が欠ける。AcceptedEnvelope は profile 4 term（DEPLOYMENT_WORKSPACE / CONTROLLER / SAFETY_RESTRICTION / INTER_ARM・v0.2.6）のみ | `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:138` は action feature（LEARNED）に限る | lease に `tensor_binding_hash = null` を loud 記録。intrinsic envelope の静的宣言 = future static candidate |
| OP-3 | SAFEHOLD からの初回起動で `validate_invocation_start` に渡す offered `Ownership` の出所（profile の cell 資源可用性） | doc 06 | doc 06 の `CellIdentity` / 資源宣言に依存 |
| OP-4 | `SafeHold` の物理的実現（controller 固有）と skill-specific safe-hold 保証 | handoff D「future static candidate」 | §5.1 は種別のみ |
| OP-5 | `RuntimeAuditRecord` の content-hash / chain 方式 | frozen `U14` `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:537` | 定めない。v0.2.7（R5-06）open note: gateway が `COMMAND_ADMITTED` の append 不能時に admission を同期 block するか（(iii) へ落とすか）は設計選択・未決 |
| OP-6 | durable store の実装 primitive（write-ahead の具体）。⚠ v0.2.2 で「線形化点 = durable commit 完了」は**要件化**した（§3.2・INV-32・B-M12）— 残るのは primitive の選定 | D0 「`CAS/lock` は D1 refinement」`$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:270-272` | 要件は §3.2 に置く |
| OP-7 | mid-skill の obs 鮮度執行の所在（executor か gateway predicate か） | boundary-only ゆえ boundary 検査のみ規定 | §4.2 は boundary の鮮度のみ |
| OP-8 | RETRACT / FORCE_LIMIT が lease を無効化すべきか（既定 = override のみ） | D0 §F `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:317` | profile で強化可としたが既定は未裁定 |
| OP-9 | `HealthConfirmation` と D0 §F `heartbeat` / health の関係（同一 channel か別か） | `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:318` | 別物として扱い、CAS 条件 9 で §F health を参照 |
| OP-10 | 全 timeout の値 | profile parameter（doc 06）・RT0 測定前 | 数値を書かない |
| OP-11 | `InterruptOutcome` 受理後の HOLD（CHECKPOINT_DISABLED）からの復帰手続（operator clearance の内容）と、checkpoint 切替を将来有効化する場合の scope 再審査の入口 | `$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59` | v0.2 = 切替無効（HOLD）。有効化 = chunk 改称 + scope 再審査 |
| OP-12 | SHADOW 運転時に実際に actuation を持つ外部 controller の扱い（本 doc の外） | charter S0 `$D/WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md:129` | 記述しない |
| OP-13 | Executor の process 境界（in-process か別 process か）と heartbeat の実装 | D0 §H | interface のみ |
| OP-14 | D0 §G `D_event`（handoff deadline）と本 doc の `ack_timeout_s` / `permit_ttl_s` / `boundary_dwell_s`（v0.2.2）の整合。deadline miss → safe-stop は `boundary_dwell_s` 超過 → NO_CHAIN 経路に写像（B-M9） | `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:363-365` | RT0 で測定後に整合検査 |
| OP-15 | 本 doc 自体の two-key・Rs 裁定 | — | 未 |
| OP-17 | CommandGateway 停止中（再起動前）の物理側 failsafe（controller watchdog / IndependentSafetyLayer heartbeat）は本 doc の外（v0.2.1・B-09） | `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:318` | 要件のみ（gateway 不在 = safety 側が stop） |
| OP-18 | cell 固有の gate（profile 依存条件）を frozen `AuthorityDecision` の入力 `acceptance_state` / `safety_gate_state` に載せるかは O0/S0/V0 層の事項（v0.2.2・A-01）。本 doc は permit 側で `profile_hash` を束縛するのみ | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:346-350` | O0/S0/V0 へ carry |
| OP-19 | 活性 lease 中の calibration / evidence 失効の検出。**Rs 裁定 2026-09-04（GPT5.6sol 推奨を採用・`review_records/rs_consult/`）**: CLOSED_LOOP では「次 permit まで検出しない」を採らず、(1) 既知期限 = `validity_deadline_mono` の決定論的 deadline、(2) 変更 event の即時通知（DeploymentValidityMonitor → manager CAS）、(3) 周期診断は timing baseline（doc 06 §8.3）が定める drift / proof-test 項目のみ、の三層。SHADOW も mode を問わず deadline / event / head-check で無効化（記録上の SafeHold・§3.7・INV-34。裁定の「SHADOW は次 permit で許容できる」は採らず保守側に統一・v0.2.7 R5-01 / R6-16）。**残 open** = 周期診断の対象項目と周期の出所（RT0 safety case）、および head-check 副場合 (c) monitor 喪失 / (d) 診断失敗の disposition 既定（v0.2.7 R5-02: HOLD を起草既定とした・Rs が強化可） | doc 06 §5 / §8.3 | 三層で確定・周期の値は baseline |
| OP-20 | `CellSafetyTimingBaseline`（doc 06 §8.3）の発行主体（RT0 / cell safety court）と改訂手続。本 doc は `timing_baseline_hash` を acceptance record 経由で束縛するだけで値を持たない（v0.2.5・OPP-11） | doc 06 OPP-16 | RT0 へ carry |
| OP-21 | 「every motion で両腕が保持・操作する」（RS71 §0 DUAL-ARM）の実行適合性は本 doc の INTER_ARM 項では検査しない（両 arm の**能力**の存在と相互制約まで）。適合性検査は composition / runtime 検査の court（v0.2.5・OPP-15 B+） | RS71 §0・doc 06 OPP-17 | 本 doc は主張しない |
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
- **synthesis record（2026-09-03 16:44 UTC）**: base = draft A（sha256 は本 package の SHA256SUMS 外・scratch）。予定していた judge panel（draft B/C + judge J1/J2）は session 上限で**未実施** — 本版は single-draft + critic fold であり、多視点 judge を経ていない（08 計画の 3 軸レビューで補う）。critic fold: **X1** = `BeliefRef` の判別は `value: SnapshotRef | HashRef`（frozen `:151`）— 旧表記「SNAPSHOT | HASH_REF」は v1 code 由来ゆえ全箇所を訂正（§0・§4.1・§6.2）／ **X2** = boundary = TERMINAL のみ（slice prereg `:59`）— CHECKPOINT を「TERMINAL と同一扱い」から「受理 + HOLD（切替無効・fail-closed）」へ改め、`SafeHoldReason.CHECKPOINT_DISABLED`・`R_CHECKPOINT_SWITCH_DISABLED`・§3.7 遷移・§5.4 解除行・§7 表・INV-21・§11 項 6・OP-11・anchor 17 を更新、題名を「boundary-only（TERMINAL boundary・checkpoint 切替なし）」へ／ **§3.3** = `FreshnessPolicy.max_staleness_s = None` の意味を runtime 層の読みとして loud 化（§4.2・OP-16）。

- **v0.2.1 fold（2026-09-04 01:47 UTC 実測）— 陽性対照レビュー（盲検 reviewer PC_B / PC_C）の**注入外** finding を verify（text / logic / impact を起草者が実施・agent 3 lens は後続）して fold**:

| finding | 内容 | 変更節 |
|---|---|---|
| B-05 (HIGH) | outcome 受領後も producer の command が admission を通る | §3.2 `boundary_wait`・§3.5 MARK_BOUNDARY_WAIT・§3.7・§5.2 (ii)・INV-23・T-21・`R_POST_OUTCOME_COMMAND` |
| B-04 (HIGH) | TRANSFER_TO_SAFEHOLD の CONFLICT に再試行規則が無い | §3.5 再試行規則・INV-24・T-22 |
| B-09 (MEDIUM) | crash matrix に CommandGateway 再起動が無い | `SafeHoldReason.GATEWAY_RESTART`・§3.7 行・`R_GATEWAY_RESTART`・INV-25・T-23・OP-17 |
| B-10 (MEDIUM) | 7 つの fault code に失敗表の行が無い | §3.7 失敗表（7 行追加）・INV-27・T-25・`SafeHoldReason.TIMING_VIOLATION` |
| B-11 / C-12 (MEDIUM) | `ack_validity_s` の出所が無い | §3.3・§4.1 `TimingBinding.ack_validity_s`・INV-22（06 `RuntimeTimeouts.ack_validity_s`） |
| B-12 (LOW) | durable 記録不在時に epoch 0 から自動再開 | §3.2 初期状態（起動拒否 + genesis record）・INV-26・T-24・`GENESIS_RECORDED` |
| B-13 (LOW) | clearance / CAS CONFLICT の AuditKind 不在 | §8 `CAS_ATTEMPT` / `CLEARANCE_RECORDED` / `GATEWAY_RESTART` / `GENESIS_RECORDED` |
| B-14 (LOW) | permit 発行後の Orchestrator 喪失に disposition が無い | §3.7 行 |
| C-06 (HIGH) | profile の initiation 強化を runtime が評価する段が無い | §6.2 B4・`R_PROFILE_INITIATION_FAILED` |
| C-07 (MEDIUM) | BEFORE_PERMIT の health check に結線点が無い | §3.4 permit 発行前提条件・`R_HEALTHCHECK_FAILED` |
| C-10 (MEDIUM) | profile の時刻依存 P_* の評価点が未定義 | §3.4 (b)（permit 発行時に再評価 → `R_PROFILE_MISBOUND`） |
| PC-05-C（計器の盲点） | CAS 事後条件の `∪ {consume_offer_id}` 欠落を盲検 reviewer が検出できなかった | 機械検査 O3 に断定を追加（`check_review_candidate.py --runtime`）— 設計変更なし |

- 陽性対照で**注入した** 8 欠陥（KEY.md）は本 doc の実体には存在しない（盲検 reviewer の PC-B-01/02/03/08・C-01〜C-05/C-18 は注入欠陥の検出であり本 doc への finding ではない）。
- v0.2.1 でも impl / training / authority = CLOSED。frozen 4 file 不変（`verify_exact_baseline_pins.sh` 11/11 PASS を再確認）。

- **v0.2.2 fold（2026-09-04 実測時刻は §13 末尾）— 3 軸独立レビュー（reviewer A / A2〔Opus〕/ B / B2〔Opus〕・別 context・v0.2.1 対象。reviewer C は session 上限で遅れ v0.2.2 を対象に実施 → v0.2.3 で fold）の finding を起草者の再検証に基づき fold（verdict 列は v0.2.3 で独立 verifier の判定に差し替え）**:

| finding | 内容 | 変更節 | verifier verdict |
|---|---|---|---|
| B-H2 / B2-02 | mid-skill 転送を authority 層が阻止する条件が無い | §3.4 (d)・§3.5 条件 11・INV-28・T-26・`R_MIDSKILL_TRANSFER_BLOCKED` | B-H2=CONFIRMED（HIGH）/ v0.2.2 fold = RESOLVED・B2-02=CONFIRMED（HIGH）/ v0.2.2 fold = RESOLVED |
| B2-01 / B-H3 | 活性 lease 中の ISL heartbeat 喪失に遷移・fault が無い | §3.7 行・§5.2 (i′)・INV-29・T-27・`R_SAFETY_LAYER_LOST`・`safety_heartbeat_timeout_s` | B2-01=CONFIRMED（CRITICAL）/ v0.2.2 fold = RESOLVED・B-H3=CONFIRMED（HIGH）/ v0.2.2 fold = RESOLVED |
| B-M2 / B2-04 | safehold_reason が弱い理由で上書きされる | §3.5 優先順位・INV-30・T-28 | B-M2=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置・B2-04=CONFIRMED（HIGH）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| B-M3 / B2-05 | SAFE_STOP を設定する遷移が無く (iii) の SafeStop が空文 | §3.5 SAFE_STOP 規則・§3.7 NO_CHAIN / HEALTH_FAIL 行・§7 表 | B-M3=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED・B2-05=CONFIRMED（HIGH）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| B2-06 / A2-12 / B-L5 | validate_outcome 失敗時に boundary_wait が立たず disposition が二義 | §3.5 MARK_BOUNDARY_WAIT・§3.7 行・§6.2 B1・`R_OUTCOME_INVALID`・T-29 | B2-06=CONFIRMED（HIGH）/ v0.2.2 fold = RESOLVED・A2-12=CONFIRMED（LOW）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置・B-L5=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| A2-01 / B2-07 / A2-08 / B2-08 | CAS 条件 10 と §5.4 の集合不一致・§5.4 の欠落行 | §3.5 条件 10・§5.4（GATEWAY_RESTART / TIMING_VIOLATION 行・集合の同一定義） | A2-01=CONFIRMED（HIGH）/ v0.2.2 fold = RESOLVED・B2-07=CONFIRMED（HIGH）/ v0.2.2 fold = RESOLVED・A2-08=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED・B2-08=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED |
| A-01 / B-M5 / B2-14 | 条件 6 が frozen AuthorityDecision に無い profile_hash 束縛を要求・decision の age 未規定 | §3.5 条件 6・§3.4 (e)(f)・`decision_max_age_s`・OP-18 | A-01=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置・B-M5=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置・B2-14=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| A-02 / A2-02 | INV-16 が名前の非交差として充足不能 | INV-16・T-18・anchor 1 | A-02=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED・A2-02=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED |
| B-H1 | gateway admission が cache 読みとも線形化読みとも読める | §2 表・§5.2・INV-19 | B-H1=CONFIRMED（HIGH）/ v0.2.2 fold = RESOLVED |
| B-M4 / B2-03 | ACK / CAS 引数が executor・lease 提案・permit に束縛されない | §3.3・§3.5 条件 2・3・INV-07 | B-M4=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED・B2-03=CONFIRMED（HIGH）/ v0.2.2 fold = RESOLVED |
| B2-10 | S_HEALTH_PENDING 中の outcome 受領に行が無い | §3.5・§3.7 from 列・T-31 | B2-10=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED |
| B-M6 | WAIT lease が HEALTH_FAIL / DEADLINE_MISS に必ず落ちる | §4.2 WAIT 規則 | B-M6=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED |
| B-M12 / B2-11 / B-L4 | 線形化点 = durable commit が未規定・genesis の下限なし | §3.2・INV-32・T-30・OP-6 | B-M12=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED・B2-11=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED・B-L4=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| B2-12 | clock domain 未宣言 | §3.2・§3.3 | B2-12=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED |
| B2-13 | hold の適用範囲が admitted 後の窓で未定義 | §4.2 | B2-13=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED |
| B-M8 | SafeHold(DIFF_IK) が無効化 lease の目標を保持 | §5.1 | B-M8=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED |
| B-M9 | boundary 滞留・再選択回数に上限が無い | §3.7・§6.2 B5・`boundary_dwell_s` / `max_reselect_attempts`・`R_BOUNDARY_DWELL_EXCEEDED`・OP-14 | B-M9=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED |
| B-M10 | 再起動 gateway が旧 lease を再 admit し得る | §5.2 `restart_pending`・INV-31 | B-M10=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED |
| B-M11 / B2-09 | 失敗表に行の無い fault code | §3.7 失敗表（11 行追加）・INV-27 | B-M11=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED・B2-09=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED |
| A-10 / B-L1 | SAFETY_STABILIZED の safehold_reason が節間で不一致 | §3.7 InterruptOutcome 行の分割 | A-10=CONFIRMED（LOW）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置・B-L1=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| B-M1 | lease-scoped な理由の再試行が別 lease を誤無効化 | §3.5 再試行規則 | B-M1=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| B-M7 | 活性 lease 中の evidence 失効の扱いが 06 と不整合 | OP-19（既定 = 次 permit 発行時・06 §5 / PT-13 を同期） | B-M7=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| B-L2 / B2-15 / A-12 | 05 が参照する閾値に 06 の field が無い | §4.1 TimingBinding 6 field・§3.7 行・06 RuntimeTimeouts | B-L2=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED・B2-15=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED・A-12=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| B-L3 | admitted command が型を持たず順序検査が無い | §5.1 `GatewayCommand`・INV-03・AuditKind `COMMAND_ADMITTED` | B-L3=CONFIRMED（LOW）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| B-L6 | permit CONFLICT / VOID が ACK 元 executor に通知されない | §3.4 | B-L6=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| B2-16 | 到達不能な enum member（ABORT / BOUNDARY_WAIT / TRANSFER） | §3.2 / §7 で 削除 | B2-16=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| B2-17 | RuntimeAuditRecord に profile_hash が無い・INV-17 の「ちょうど 1 件」 | §8・INV-17 | B2-17=CONFIRMED（LOW）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| A-03 / A2-10 | 凍結語彙の不在主張が広すぎ・scratch 参照 | §2 home matrix（再現 command 併記）・07 §1 | A-03=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED・A2-10=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| A-04 | lease が profile_hash 経由で EP profile を参照すると読める | §4.4 | A-04=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| A-05 / A2-04 | ActionBinding に bounds を帰属 | §0 | A-05=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED・A2-04=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| A2-05 | 旧 epoch 拒否の所有と執行点の区別 | §2 表・anchor 2 | A2-05=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| A-11 | validate_handoff の invocation が producer 側であることが不明 | §3.6・§6.2 B4 | A-11=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| A-09 / A2-11 | timestamp の x mask | header・§13 | A-09=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED・A2-11=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| A-07 / A-08 / A2-07 | 02 / 03 CSV の引用・tuple・CSV 検査様式 | 02・03・checker CSV mode・08 §1 | A-07=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED・A-08=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED・A2-07=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED |
| A2-06 | 07 §3 の SkillActionId 記述 | 07 §3 | A2-06=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED |
| A-06 / A2-09 / A2-03 | 06 反循環文の自己矛盾・P_RESOURCE_UNATTESTED の検査 cell | 06 §2.3・§3 | A-06=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED・A2-09=refuted（NOT_A_DEFECT）・A2-03=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED |

- fold しなかった finding（refuted / NOT_A_DEFECT / 保留）は `11_THREE_AXIS_REVIEW_RECORD_20260903.md` に理由付きで列挙する。
- v0.2.2 でも impl / training / authority = CLOSED。frozen 4 file 不変（`verify_exact_baseline_pins.sh` 11/11 PASS を再確認）。

- **v0.2.3 fold（2026-09-04 20:47 UTC）— 独立 verifier（3 lens・別 context・v0.2.1 finding を v0.2.1 本文で検証し v0.2.2 での fold 状態を判定）の verdict を上表に反映し、PARTIAL とされた残差と、軸 C（reviewer C・v0.2.2 対象・verifier C）の確定 finding を fold**。全 verdict と処置 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`:

| finding | 内容 | 変更節 | verdict |
|---|---|---|---|
| A-01 / B-M5（残差） | 06 §5 の stale 参照（条件 6） | doc 06 §5 | A-01=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置; B-M5=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| A-10（残差） | §6.1 CHECKPOINT 行が SAFETY_STABILIZED を除外していない | §6.1 | A-10=CONFIRMED（LOW）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| A2-12（残差） | 規則 3 が R_OUTCOME_INVALID を列挙しない | §7 規則 3 | A2-12=CONFIRMED（LOW）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| B-M1 / B2-04（残差） | INV-24 と再試行文が非 safety 起因で過大主張 | §3.5・§5.2 (ii) `pending_invalidate`・INV-24 | B-M1=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置; B2-04=CONFIRMED（HIGH）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| B-M2（残差） | R_MANAGER_RESTART 行 / T-09 が無条件 epoch+1 | §3.7 失敗表・T-09 | B-M2=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| B-M7（残差） | 06 §8.1 規則 (3) が旧文 | doc 06 §8.1 | B-M7=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| B-L3（残差） | 記録義務が admitted CLOSED_LOOP command を含まない | §8 記録義務・AuditKind comment | B-L3=CONFIRMED（LOW）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| B2-05（残差） | ISL 起因行で reason SAFETY / disposition SAFE_STOP の食い違い | §3.5 例外・§5.2 (iii) | B2-05=CONFIRMED（HIGH）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| B2-14（残差） | age の基準が無い | §3.4 (e) | B2-14=CONFIRMED（MEDIUM）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| B2-17（残差） | T-17 が旧 INV-17 の文 | T-17 | B2-17=CONFIRMED（LOW）/ v0.2.2 fold = PARTIAL→ v0.2.3 で残差処置 |
| CD-12 | None 鮮度の規則が 05/06 で二重定義 | §4.2 | CONFIRMED（LOW） |
| CD-13 | INV-22 の列挙漏れ・ack_validity の clock | INV-22・§4.1 comment | CONFIRMED（LOW） |
| CD-10 | lease に時間上限が無く曝露が無限 | `lease_max_duration_s`・§3.7・`R_LEASE_DURATION_EXCEEDED`・INV-33・T-32・OP-19 | CONFIRMED（MEDIUM） |
| CD-05 | commissioning 済 expectation の照合が無い | §3.4 (g) | CONFIRMED（MEDIUM） |
| CD-06 | offer の ownership が cell 資源と照合されない | §3.4 (h) | CONFIRMED（MEDIUM） |
| CD-17 | accepted profile 集合の前提が無い | §3.4 (i) | CONFIRMED（LOW） |
| CD-04 | 参照内容の content hash が無い | §3.4 (j)・§4.3 SAFETY_RESTRICTION | CONFIRMED（HIGH） |
| CD-02 | clearance record の形と「該当」が未定義 | §5.4 | CONFIRMED（MEDIUM） |
| CD-07 | force / torque を admission 項にしている | §4.3 CONTROLLER | CONFIRMED（MEDIUM） |
| CD-18 | workspace 項が点評価のみ | §4.3 DEPLOYMENT_WORKSPACE | CONFIRMED（LOW） |
| CD-03 | evidence 失効・subject 単位が未執行 | §3.4 (b) | CONFIRMED（HIGH） |

- **v0.2.4 fold（2026-09-04 23:00 UTC）— v0.2.3 本文への再レビュー round**: reviewer R1（05・contract + runtime lens）/ R2（06・deployment lens）が v0.2.3 を対象に fold 回帰 + 新規反証を実施し、verifier V1 / V2（3 lens・別 context）が全 finding を判定。確定分を fold（refuted は適用せず）。記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md` §7:

| finding | 内容 | 変更節 | verdict |
|---|---|---|---|
| R1-01 | command_deadline_s の計時範囲が無い | §4.1 comment・§4.2 | R1-01=CONFIRMED（MEDIUM） |
| R1-02 | age の起点が初回解決で無意味 | §3.4 (e) | R1-02=CONFIRMED（MEDIUM） |
| R1-03 | 同 tier / 同 reason の SAFEHOLD 遷移が未定義・(iii) が audit 読出しに依存 | §3.2 `safehold_disposition`・§3.5・§3.7・§5.2 (iii)・INV-31・T-28 | R1-03=CONFIRMED（MEDIUM） |
| R1-05 / R2-03 | content hash の照合が 3 参照のみ | §3.4 (j)・§4.3 DEPLOYMENT_WORKSPACE | R1-05=CONFIRMED（HIGH）; R2-03=CONFIRMED（HIGH） |
| R1-06 / R2-19 | ZOH で点評価 | §4.3 DEPLOYMENT_WORKSPACE（線分・hold 非依存） | R1-06=CONFIRMED（MEDIUM）; R2-19=CONFIRMED（LOW） |
| R1-07 | 条件 9 / 10 / ACK 失効に fault・行が無い | §3.7 失敗表 3 行 | R1-07=CONFIRMED（LOW） |
| R1-08 | §7 INVALID_STATE 行が §3.7 / B5 と不一致 | §7 | R1-08=CONFIRMED（LOW） |
| R1-09 | ISL 行に DISPOSITION record が無い | §3.7 | R1-09=CONFIRMED（LOW） |
| R1-10 | TRANSFER_TO_EXECUTOR 行の record 集合 | §3.7・INV-17 | R1-10=CONFIRMED（LOW） |
| R1-11 | S_TRANSFER_PENDING の定義・gateway state 列 | — 適用せず | R1-11=refuted（NOT_A_DEFECT） |
| R1-12 | executor_id が admission に無い | §2・INV-03 | R1-12=CONFIRMED（LOW） |
| R1-13 | B0 snapshot が MARK_BOUNDARY_WAIT に先行し得る | §6.2 B0・§3.7 失敗表 | R1-13=CONFIRMED（LOW） |
| R1-14 | executor 発 SAFETY_STABILIZED の解除経路 | §5.4 SAFETY 行 | R1-14=CONFIRMED（LOW） |
| R1-15 / R2-12 | INV-33 の範囲と CD-10 行の from 集合が不一致 | INV-33（範囲を明示・boundary 滞留は boundary_dwell_s 側） | R1-15=CONFIRMED（LOW）; R2-12=CONFIRMED（LOW） |
| R1-16 | pending_invalidate が残留 | §5.2 (ii) | R1-16=CONFIRMED（LOW） |
| R2-01 | timeout 束縛の迂回（05 側 = FAULT 副因） | §8 記録義務 | R2-01=CONFIRMED（MEDIUM） |
| R2-08 | profile の失効経路 | §3.4 (i) | R2-08=CONFIRMED（MEDIUM） |
| R2-15 | genesis の role / profile_hash | §3.2 | R2-15=CONFIRMED（LOW） |
| R2-17 | evaluator の実行直前再検証 | §3.4 (a) | R2-17=CONFIRMED（LOW） |
| （06 側の fold 行は doc 06 §11） | | | |

- **v0.2.5 fold（2026-09-05 01:33 UTC）— Rs 裁定 2026-09-04（GPT5.6sol 推奨を採用・`review_records/rs_consult/`）**: Rs が外部 AI（GPT5.6sol）に問い合わせ、その推奨 4 件を全件採用と裁定（本 session で Rs = 利用者本人が選択）。推奨の前提訂正 5 点は本文で照合済（全て正・`review_records/rs_consult/A_GPT56sol_20260904.md` 末尾）。凍結 schema delta = 0（runtime / deployment 層の型追加のみ）:

| 項目 | 内容 | 変更節 |
|---|---|---|
| 裁定 OPP-11 | permit の実効失効 `effective_expires_at` = min(ttl, ACK, decision age, validity deadline)・CAS で decision age 再検査・timing baseline は acceptance record 経由 | §3.4 CommitPermit・(k)・§3.5 条件 2 / 6・INV-35・T-35・OP-20 |
| 裁定 OPP-13 | `ProfileAcceptanceRecord`（generation・state・allowed modes）を permit / lease に束縛・CAS 条件 12 で registry 再検査・SUSPENDED / REVOKED で lease 無効化・registry 不読 = actuation 拒否 | §3.4 (i)・§3.5 条件 12・§3.7・§4.1・`R_PROFILE_SUSPENDED` / `R_REGISTRY_UNAVAILABLE`・INV-35・T-34 / T-36 |
| 裁定 OP-19 | CLOSED_LOOP lease の `validity_deadline_mono`（三層: deadline・event・根拠付き周期診断）・`DeploymentValidityMonitor`・`SafeHoldReason.VALIDITY_EXPIRED` | §2・§3.2・§3.4・§3.7・§4.1・§4.5・§5.4・`R_CALIBRATION_EXPIRED_ACTIVE` / `R_EVIDENCE_EXPIRED_ACTIVE`・INV-34・T-33・OP-19 |
| 裁定 OPP-15 B+ | INTER_ARM 項（両 arm の同一 snapshot 連言評価）・`R_INTER_ARM_VIOLATION`・every-motion 適合性は court へ | §4.3・§3.7・INV-36・T-37・OP-21 |

- **v0.2.6 fold（2026-09-05 02:15 UTC）— round 3（reviewer R3 / R4・v0.2.5 対象 → verifier V3 / V4・3 lens）の確定 finding の fold**。記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md` §9:

| finding | 内容 | 変更節 | verdict |
|---|---|---|---|
| R3-01 / R4-01 / R3-16 | INTER_ARM が他 arm を静的に扱う・GatewayCommand に arm が無い | `GatewayCommand.arm_targets`・§4.3 INTER_ARM・§3.7・INV-36 | R3-01=CONFIRMED（HIGH）; R4-01=CONFIRMED（HIGH）; R3-16=CONFIRMED（LOW） |
| R3-02 | EnvelopeTermKind に INTER_ARM が無い | §4.3 enum・T-13・OP-2 | R3-02=CONFIRMED（MEDIUM） |
| R3-17 / R4-02 | content hash 列挙に v0.2.5 の 3 hash が無い | §3.4 (j)・checker Q2 | R3-17=CONFIRMED（LOW）; R4-02=CONFIRMED（HIGH） |
| R3-03 / R4-18 | effective_expires_at が SHADOW で不能判定 | §3.4 CommitPermit・§4.1 | R3-03=CONFIRMED（MEDIUM）; R4-18=CONFIRMED（LOW） |
| R3-04 / R4-06 / R3-05 | validity_deadline_mono の lease_max 項・到達項目が不明 | §3.4 / §4.1 `validity_deadline_source`・§3.7・INV-34 | R3-04=CONFIRMED（MEDIUM）; R4-06=CONFIRMED（MEDIUM）; R3-05=CONFIRMED（MEDIUM） |
| R3-06 | VALIDITY_EXPIRED の再試行 scope | §3.5・§5.2 (ii) | R3-06=CONFIRMED（MEDIUM） |
| R3-07 / R3-08 / R3-20 | registry 不読の範囲・monitor の liveness・診断失敗 | §2・§3.7 head-check 行・失敗表 | R3-07=CONFIRMED（MEDIUM）; R3-08=CONFIRMED（MEDIUM）; R3-20=CONFIRMED（LOW） |
| R3-09 | 兄弟 profile による cell 停止の迂回 | §3.4 (i) | R3-09=CONFIRMED（MEDIUM） |
| R3-11 | R1-01 × R2-01 の衝突 | §4.2 計時範囲 | R3-11=CONFIRMED（MEDIUM） |
| R3-13 | safehold_disposition が遷移で設定されない | §3.2 初期状態・§3.5 事後条件 | R3-13=CONFIRMED（MEDIUM） |
| R3-14 | effective expiry の fault 優先順・証明 D | §3.5 条件 2・§3.8 | R3-14=CONFIRMED（LOW） |
| R3-15 | decision t_mono の clock domain | — 適用せず | R3-15=refuted（NOT_A_DEFECT） |
| R3-18 / R4-08 | 第 2 評価点の list が 06 と不一致 | §3.4 (b) | R3-18=CONFIRMED（LOW）; R4-08=CONFIRMED（MEDIUM） |
| R3-19 | executor_id 不一致の fault | INV-03・失敗表 | R3-19=CONFIRMED（LOW） |
| R3-21 / R4-09 / R4-16 / R4-04 | head record の再評価・hash field の再検証・fork | §3.4 (i)・§3.5 条件 12 | R3-21=CONFIRMED（LOW）; R4-09=CONFIRMED（MEDIUM）; R4-16=CONFIRMED（LOW）; R4-04=CONFIRMED（HIGH） |
| R4-15 | clock 異常の検査が無い | §3.4 (l)・`R_CLOCK_ANOMALY`・失敗表 | R4-15=CONFIRMED（MEDIUM） |
| R4-11 | event の記録・disposition 決定・自動再 lease | §3.7・§5.4 | R4-11=CONFIRMED（MEDIUM） |
| （06 側の fold 行は doc 06 §11） | | | |

- **v0.2.7 fold（2026-09-05 23:32 UTC）— round 4（reviewer R5 / R6・v0.2.6 対象 → verifier V5 / V6・3 lens）の確定 finding の fold**。記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md` §10:

| finding | 内容 | 変更節 | verdict |
|---|---|---|---|
| R5-01 / R6-16 | SHADOW の deadline 扱いが 3 通り | OP-19・失敗表 R_PROFILE_SUSPENDED 行 | R5-01=CONFIRMED（MEDIUM）; R6-16=CONFIRMED（LOW） |
| R5-02 | head-check 行が total でない・event 行の到達不能 code | §3.7 head-check 行・event 行 | R5-02=CONFIRMED（MEDIUM） |
| R5-03 | monitor 喪失後の再 permit を止める前提が無い | §3.4 (m)・§5.4 | R5-03=CONFIRMED（MEDIUM） |
| R5-05 | TRANSFER_TO_EXECUTOR が safehold_disposition を戻さない | §3.5 事後条件・INV-01 | R5-05=CONFIRMED（MEDIUM） |
| R5-06 | AuditRecorder 不能の code / 行が無い | `R_AUDIT_UNAVAILABLE`・§3.7・§8・INV-17 | R5-06=CONFIRMED（MEDIUM） |
| R5-07 | 条件 2 / 3 / 6 の境界不一致・CAS 時失効の行 | §3.5 条件 3 / 6・§3.4 (e)・失敗表 | R5-07=CONFIRMED（LOW） |
| R5-08 / R6-21 | ACCEPTANCE 到達の fault code・sub-kind の解決元 | §3.7 deadline 行・失敗表 | R5-08=CONFIRMED（LOW）; R6-21=CONFIRMED（LOW） |
| R5-10 / R6-03 | trigger 副因の語彙が 2 code 分しか無い | §8 記録義務 | R5-10=CONFIRMED（LOW）; R6-03=CONFIRMED（MEDIUM） |
| R5-11 | gateway は deadline を検出できない | — 適用せず | R5-11=refuted（NOT_A_DEFECT） |
| R5-12 | 兄弟 SUSPENDED が permit 発行時にしか効かない | §3.4 (i)・§3.5 条件 12・head-check 行 | R5-12=CONFIRMED（LOW） |
| R6-05 / R6-06 | acceptance / clearance record の role registry 照合 | §3.4 (i)・§3.5 条件 12・§5.4 clearance record 定義 | R6-05=CONFIRMED（MEDIUM）; R6-06=CONFIRMED（MEDIUM） |
| R6-10 | baseline registry の定義先 | §2 monitor 行 | R6-10=CONFIRMED（LOW） |
| R6-17 | 失効 disposition の根拠 | 失敗表 validity 行 | R6-17=CONFIRMED（LOW） |
| R6-01 | finger geometry hash の (j) 列挙 | §3.4 (j) | R6-01=CONFIRMED（HIGH） |
| R6-13 | (j) 区間の除外宣言（checker Q2 強化と対） | §3.4 (j) | R6-13=CONFIRMED（LOW） |
| （06 側の fold 行は doc 06 §11） | | | |

## 14. Review anchors

1. 本 doc は frozen 4 file に field / enum member を足していない — §1・§11 項 3・INV-16（型境界 + hash preimage の断定。`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:385` の strict codec が runtime 固有 field を unknown field として拒否する）。
2. `AuthorityManager` の責務（CAS・発行・旧 epoch 拒否の**所有**・`handoff_offer_id` 単位の使用済み拒否・snapshot 読出し）は frozen の O0 層要求仕様に一致し、旧 epoch 拒否の**執行点** = CommandGateway admission（manager 所有状態の線形化読み） — §2 表 ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382`。
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
