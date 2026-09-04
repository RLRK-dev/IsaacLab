import sys, json
P = sys.argv[1]; VERD = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
f5 = f"{P}/05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md"
t = open(f5, encoding="utf-8").read()
assert "v0.2.2" not in t, "already v0.2.2"
def rep(old, new):
    global t
    assert old in t, "MISSING: " + old[:100]
    t = t.replace(old, new, 1)
def repline(prefix, new):
    global t
    L = t.split("\n"); i = [k for k, l in enumerate(L) if l.startswith(prefix)]
    assert len(i) == 1, f"prefix {len(i)}: {prefix[:80]}"
    L[i[0]] = new; t = "\n".join(L)
def insert_after(prefix, new):
    global t
    L = t.split("\n"); i = [k for k, l in enumerate(L) if l.startswith(prefix)]
    assert len(i) == 1, f"prefix {len(i)}: {prefix[:80]}"
    L.insert(i[0] + 1, new); t = "\n".join(L)
A = "$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md"; B = "$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md"; D0 = "$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md"
# ---- header / version ----
rep("(v0.2.1 REVIEW CANDIDATE)", "(v0.2.2 REVIEW CANDIDATE)")
rep("- status: **REVIEW CANDIDATE v0.2.1（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2 → v0.2.1 = 陽性対照レビューの注入外 finding の fold（§13）",
    "- status: **REVIEW CANDIDATE v0.2.2（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2 → v0.2.1 = 陽性対照レビューの注入外 finding の fold／ v0.2.1 → v0.2.2 = 3 軸独立レビュー（A / A2 / B / B2 / C）の確定 finding の fold（§13）")
repline("- 系譜: 起草 draft A", "- 系譜: 起草 draft A（角度 = AUTHORITY-SAFETY-FIRST・2026-09-03 11:20 UTC 実測）→ critic 報告（`07_critic_report.md` X1 / X2 / §3.3）の fold = v0.2（16:44 UTC）→ 陽性対照の注入外 finding の fold = v0.2.1（2026-09-04 01:47 UTC）→ **3 軸独立レビューの確定 finding の fold = 本版 v0.2.2（§13）**。⚠ judge panel（3 draft × 2 judge）は session 上限で未実施 — §13 に honest に記録。")
repline("  D1.1-B:       TimingSpec / ActionTimingSpec{action_rate_hz, hold} / ActionBinding{bounds", "  D1.1-B:       TimingSpec / ActionTimingSpec{action_rate_hz, hold} / ActionBinding{control_mode, action_scale, timing} + FeatureBinding.bounds / tensor_binding_hash")
# ---- §2 tables ----
repline("| **AuthorityManager** |", f"| **AuthorityManager** | `AuthorityState` の唯一 writer。`AuthorityCas` の実行、`CommitPermit` の発行/失効/一回性、`authority_epoch_snapshot` の読出し提供、`consumed_offer_ids` / `invalidated_lease_ids` の保持、restart 時の fail-closed 復帰。**旧 epoch command 拒否の所有者**（v0.2.2・A2-05: 拒否の**状態**は manager が所有し、**執行点**は CommandGateway の admission — gateway は manager 所有の `AuthorityState` を線形化して読むだけで書かない） | `AuthorityState`（durable）+ permit 台帳 | `{A}:382`（CAS 更新・発行・旧 epoch 拒否・使用済み offer 拒否・snapshot 読出し = O0 層） |")
repline("| **CommandGateway** |", f"| **CommandGateway** | actuation への唯一経路。admission = manager 所有 `AuthorityState` の**同期・線形化読み**（cache 不可 — v0.2.2・B-H1）の下で `(lease_id, control_epoch)` 等値 ∧ `¬boundary_wait` ∧ `AcceptedEnvelope` 連言 ∧ command 種別 = lease.control_mode ∧ `cmd_seq` 単調。既定出力 = `SafeHold`。SHADOW lease の actuation port = DISABLED。`manager_liveness_s` は「線形化読みを待つ上限」であり、超過 = (ii) を評価せず (iii) | 線形化読み（cache を持たない）+ 直近 admitted command + `restart_pending` flag | `{A}:382`（旧 epoch command 拒否）; D0 `control_ownership` 単一 writer `{D0}:270-272` |")
repline("| cell / controller / tool / payload 条件 |", f"| cell / controller / tool / payload 条件 | `IndustrialDeploymentProfile`（doc 06・外部） | §4（`profile_hash` 参照） | frozen 型（`SkillDefinition` `{A}:151` / `TensorBindingSpec` `{B}:173-181`）に cell / controller / calibration / deployment の **field は無い**。語の出現（再現 command: `grep -ic <pat> <EP md> <EP json>`, pat ∈ {{controller, calibrat, deploy, inject, epoch, lease}}）= EP md / JSON で 0 hit；DESIGN 2 file には散文としての hit（`{A}:570`「calibrated uncertainty」・`{B}:255` / `:313`「全 deployment の resolver」・`:337`）があり schema 語彙ではない（v0.2.2・A-03 / A2-10） |")
# ---- §3.2 ----
rep("    safehold_reason: SafeHoldReason | None            # owner.kind == SAFEHOLD ⇔ 非 null\n    boundary_wait: bool",
    "    safehold_reason: SafeHoldReason | None            # owner.kind == SAFEHOLD ⇔ 非 null（優先順位 = §3.5・v0.2.2）\n    boundary_wait: bool")
rep("class SafeHoldReason(Enum): INITIAL | BOUNDARY_WAIT | TRANSFER | HEALTH_FAIL | NO_CHAIN | EXECUTOR_LOST | MANAGER_RESTART | GATEWAY_RESTART | DEADLINE_MISS | TIMING_VIOLATION | ENVELOPE_VIOLATION | SAFETY | SAFE_STOP | CHECKPOINT_DISABLED",
    "class SafeHoldReason(Enum): INITIAL | HEALTH_FAIL | NO_CHAIN | EXECUTOR_LOST | MANAGER_RESTART | GATEWAY_RESTART | DEADLINE_MISS | TIMING_VIOLATION | ENVELOPE_VIOLATION | SAFETY | SAFE_STOP | CHECKPOINT_DISABLED   # v0.2.2: BOUNDARY_WAIT（flag に置換）/ TRANSFER（lease 無効化理由であって hold 理由でない）を 削除（B2-16）")
insert_after("- 初期状態 = `(SAFEHOLD, epoch=e0, None, ∅, INITIAL, False, 0)`",
    f"- **線形化点 = durable commit の完了（v0.2.2・B-M12）**: `AuthorityCas` の SUCCESS は write-ahead の durable 書込みが完了した時点で成立し、通知・audit・`permit.state := CONSUMED` はその後にのみ行う。in-memory 成功と durable 書込みの間で crash した CAS は「起きなかった」ものとして扱われ、restart の `epoch := persisted + 1` と矛盾しない。`invalidated_lease_ids` は `AuthorityState` と同じ durable store に同一 commit で書く（INV-32）。\n- **genesis の下限（v0.2.2・B-L4 / B2-11）**: genesis record の epoch 起点は、（別 durable の）AuditRecorder に現れる最大 `control_epoch` より**厳密に大きい**こと。両 store が失われた場合は operator が厳密に大きい起点を宣言し、その導出を `GENESIS_RECORDED` に記録する。\n- **clock domain（v0.2.2・B2-12）**: 本 doc の時刻比較は全て AuthorityManager の単調 clock（D0 §G 単一 origin `{D0}:354-355`）で行う。`ReadinessAck.valid_until` は manager が ACK **受領時**に自 clock で確定する（`t_receive + ack_validity_s`。executor の `t_ack` は参考値）。HealthConfirmation / permit の timeout も manager が自 CAS 時刻から測る。")
# ---- §3.3 ----
rep("    lease_proposal_id: str                            # 提案 lease（未活性）の runtime-local id",
    "    lease_proposal_id: str                            # 提案 lease（未活性）の id = 最終 `lease_id`（proposal 時に確定・v0.2.2・B-M4）")
rep("    valid_until: float                                # = t_ack + TimingBinding.ack_validity_s（profile RuntimeTimeouts.ack_validity_s 由来 — v0.2.1）",
    "    valid_until: float                                # manager が受領時に自 clock で確定: t_receive + TimingBinding.ack_validity_s（v0.2.2・B2-12。executor の t_ack は参考値）")
# ---- §3.4 permit preconditions ----
rep("(c) `TimingBinding` の等値（INV-12）。permit は発行時にこれらの結果 ref を束縛する。",
    "(c) `TimingBinding` の等値（INV-12）; (d) **boundary guard**（v0.2.2・B-H2 / B2-02）: `expected.owner.kind == SAFEHOLD ∨ expected.boundary_wait == True`（違反 = `R_MIDSKILL_TRANSFER_BLOCKED`・permit 不発行）; (e) CLOSED_LOOP_AUTHORITY: `authority_decision_ref` を発行時に再解決し `granted == True ∧ age ≤ decision_max_age_s`（違反 = `R_AUTHORITY_DECISION_ABSENT`・v0.2.2・B2-14）; (f) `permit.profile_hash == proposed_lease.profile_hash`。permit は発行時にこれらの結果 ref を束縛する。permit が CONFLICT / VOID になった場合、manager は ACK 元 executor へ `PERMIT_VOIDED` を通知し executor は提案を破棄する（v0.2.2・B-L6）。")
# ---- §3.5 conditions ----
rep("2. `permit.state == UNUSED ∧ now < permit.expires_at ∧ permit.expected == cas.expected`。",
    "2. `permit.state == UNUSED ∧ now < permit.expires_at ∧ permit.expected == cas.expected ∧ cas.new_owner == EXECUTOR(permit.proposed_lease.executor_id) ∧ cas.new_lease_id == permit.proposed_lease.lease_id ∧ cas.consume_offer_id == permit.handoff_offer_id ∧ permit.profile_hash == permit.proposed_lease.profile_hash`（v0.2.2・B2-03: CAS 引数は permit に束縛される）。")
repline("3. `ack = resolve(permit.ack_id)`:", "3. `ack = resolve(permit.ack_id)`: `ack.expected_control_epoch == expected.control_epoch + 1 ∧ now ≤ ack.valid_until ∧ ack.invocation_id == permit.proposed_lease.invocation_id ∧ ack.handoff_offer_id == permit.handoff_offer_id ∧ ack.envelope_readback_ok ∧ ack.executor_id == permit.proposed_lease.executor_id ∧ ack.skill_action_id == permit.proposed_lease.skill_action_id ∧ ack.lease_proposal_id == permit.proposed_lease.lease_id`（v0.2.2・B-M4 / B2-03: ACK は executor・skill・lease 提案にも束縛）。")
repline("6. `proposed_lease.mode == CLOSED_LOOP_AUTHORITY ⇒", f"6. `proposed_lease.mode == CLOSED_LOOP_AUTHORITY ⇒ resolve(authority_decision_ref).granted == True`（frozen の `granted == True` 必要条件 `{A}:354`）かつ、decision の入力 `eligibility_report` が依拠する certificate（certificate-first `{A}:323`・`certificate.skill_action_id` `{A}:306`）の `skill_action_id == proposed_lease.skill_action_id`。⚠ frozen `AuthorityDecision` は profile を知らない（入力は 4 record のみ `{A}:346-350`）ため、`profile_hash` の束縛は permit 側（条件 2）で行う（v0.2.2・A-01 / B-M5）。cell 固有の gate を `acceptance_state` / `safety_gate_state` に載せるかは O0/S0/V0 層の事項（§12 OP-18）。")
repline("10. `safehold_reason ∈ {SAFETY, SAFE_STOP, MANAGER_RESTART}`", "10. `safehold_reason ∈ {SAFETY, SAFE_STOP, MANAGER_RESTART, GATEWAY_RESTART, CHECKPOINT_DISABLED}` の SAFEHOLD からの転送では、該当する clearance record（§5.4 — 集合は §5.4 と同一定義・v0.2.2・A2-01 / B2-07）が存在する。CHECKPOINT_DISABLED からの転送では新 lease の `InitializationRecord.previous_lease_id` に当該 lease を記録する。\n11. **boundary guard（v0.2.2・B-H2 / B2-02）**: `expected.owner.kind == SAFEHOLD ∨ expected.boundary_wait == True`。違反 = REJECTED・`R_MIDSKILL_TRANSFER_BLOCKED`（mid-skill switching 経路は authority 層でも存在しない — INV-28）。")
rep("再試行中も gateway 出力は §5.2 (i)（safety 決定）または (iii) に既に落ちているため、CONFLICT の間に executor lease が actuation を再開することは無い（INV-24）。",
    "再試行中も gateway 出力は §5.2 (i)（safety 決定）または (iii) に既に落ちているため、CONFLICT の間に executor lease が actuation を再開することは無い（INV-24）。**理由の優先順位（v0.2.2・B-M2 / B2-04）**: `SAFETY / SAFE_STOP` > `MANAGER_RESTART / GATEWAY_RESTART / CHECKPOINT_DISABLED` > その他。current が既に SAFEHOLD のとき TRANSFER_TO_SAFEHOLD は理由を**強める方向にしか**書き換えない（弱い理由への上書きは記録付き no-op = FAULT + audit・状態不変・epoch 不変 — INV-30）。manager 起動時は IndependentSafetyLayer に未解除決定を照会し、あれば reason = SAFETY で復帰する。**lease-scoped な理由**（EXECUTOR_LOST / HEALTH_FAIL / DEADLINE_MISS / TIMING_VIOLATION / ENVELOPE_VIOLATION / CHECKPOINT_DISABLED / NO_CHAIN）の再試行は `current.active_lease_id == trigger.lease_id` のときのみ（v0.2.2・B-M1: 別 lease の誤無効化を防ぐ。不一致なら CAS を捨て元 lease への FAULT のみ記録）。non-lease-scoped（SAFETY / SAFE_STOP / MANAGER_RESTART / GATEWAY_RESTART）は無条件に再試行。**SAFE_STOP の設定（v0.2.2・B-M3 / B2-05）**: 実効 disposition（profile `EscalationPolicy` 適用後）が SAFE_STOP となる遷移は全て `TRANSFER_TO_SAFEHOLD(SAFE_STOP)` を用い、原因 fault は `RuntimeAuditRecord.fault` に別途記録する（(iii) は `safehold_reason == SAFE_STOP` で SafeStop を出す）。")
rep("前提条件 = 条件 1 ∧ `expected.owner.kind == EXECUTOR` ∧ 当該 lease の `SkillOutcome` を受領済（`validate_outcome` の report ref を CAS に添える）",
    "前提条件 = 条件 1 ∧ `expected.owner.kind == EXECUTOR` ∧ 当該 lease の `SkillOutcome` を**受領した事実**（`validate_outcome` の report ref を issues の有無にかかわらず CAS に添える — v0.2.2・B2-06: issues 非空でも `boundary_wait := True` とし、以後は `R_OUTCOME_INVALID` → B5 NO_CHAIN 経路）。`S_HEALTH_PENDING` 中の受領も同じ（v0.2.2・B2-10: pending の HealthConfirmation は取消し、未確認の事実を ASSESSMENT に記録）")
# ---- §3.7 transitions ----
repline("| `S_HEALTH_PENDING` | 失敗 / timeout |", "| `S_HEALTH_PENDING` | 失敗 / timeout | TRANSFER_TO_SAFEHOLD(HEALTH_FAIL \\| SAFE_STOP per profile.escalation.on_health_fail) | `S_SAFEHOLD(HEALTH_FAIL \\| SAFE_STOP)` | HEALTH_FAILED, FAULT(R_HEALTH_CONFIRM_FAILED \\| R_HEALTH_CONFIRM_TIMEOUT), DISPOSITION(HOLD \\| SAFE_STOP)（v0.2.2） |")
repline("| `S_LEASE_ACTIVE` | `SkillOutcome`（`TerminalOutcome`）受領 |", "| `S_LEASE_ACTIVE` / `S_HEALTH_PENDING` | `SkillOutcome`（`TerminalOutcome`）受領（issues の有無を問わず） | MARK_BOUNDARY_WAIT（v0.2.1） | `S_BOUNDARY_WAIT` | CAS_ATTEMPT, ASSESSMENT — 以後 当該 lease の command = R_POST_OUTCOME_COMMAND。issues 非空 = FAULT(R_OUTCOME_INVALID) → B5（v0.2.2） |")
repline("| `S_LEASE_ACTIVE` | `SkillOutcome`（`InterruptOutcome`）受領 |", "| `S_LEASE_ACTIVE` / `S_HEALTH_PENDING` | `InterruptOutcome`（reason = PLANNED_SWITCH / EVENT）受領 | TRANSFER_TO_SAFEHOLD(CHECKPOINT_DISABLED) | `S_SAFEHOLD(CHECKPOINT_DISABLED)` | ASSESSMENT, FAULT(R_CHECKPOINT_SWITCH_DISABLED), DISPOSITION(HOLD) — v0.2 は checkpoint 切替を実行しない（§6.1） |\n| `S_LEASE_ACTIVE` / `S_HEALTH_PENDING` | `InterruptOutcome`（reason = SAFETY_STABILIZED）受領 | TRANSFER_TO_SAFEHOLD(SAFETY) | `S_SAFEHOLD(SAFETY)` | ASSESSMENT, DISPOSITION(HOLD) — 解除 = §5.4 SAFETY 行（v0.2.2・A-10 / B-L1） |")
repline("| `S_BOUNDARY_WAIT` | 候補なし |", "| `S_BOUNDARY_WAIT` | 候補なし / `boundary_dwell_s` 超過 / `max_reselect_attempts` 超過 | TRANSFER_TO_SAFEHOLD(NO_CHAIN \\| SAFE_STOP per profile.escalation.on_no_chain) | `S_SAFEHOLD(NO_CHAIN \\| SAFE_STOP)` | DISPOSITION(NO_CHAIN → HOLD \\| SAFE_STOP), 超過時 FAULT(R_BOUNDARY_DWELL_EXCEEDED)（v0.2.2・B-M9） |")
insert_after("| any | IndependentSafetyLayer STOP / HOLD |", "| any (EXECUTOR) | IndependentSafetyLayer の heartbeat が `safety_heartbeat_timeout_s` を超えて欠落 / health == failed（v0.2.2・B2-01 / B-H3） | TRANSFER_TO_SAFEHOLD(SAFETY) | `S_SAFEHOLD(SAFETY)` | FAULT(R_SAFETY_LAYER_LOST), DISPOSITION(SAFE_STOP) — gateway は欠落を観測した時点で (ii) を評価せず (i′) SafeStop |\n| any (EXECUTOR) | `R_COMMAND_KIND_MISMATCH` が連続 `command_kind_mismatch_max` 回（v0.2.2・B2-15） | TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION) | `S_SAFEHOLD(ENVELOPE_VIOLATION)` | FAULT(R_ENVELOPE_VIOLATION), DISPOSITION(HOLD) |")
repline("| command 種別が lease.control_mode と不一致（v0.2.1・B-10）", "| command 種別が lease.control_mode と不一致（v0.2.1・B-10） | CommandGateway | `R_COMMAND_KIND_MISMATCH` | 拒否のみ・lease 継続 | 変化なし（連続 `command_kind_mismatch_max` 回で TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION) — 閾値は profile `RuntimeTimeouts`・v0.2.2） |")
insert_after("| Orchestrator 喪失（permit 発行後）", "| 旧 epoch / 無効化 lease の command（v0.2.2・B-M11 / B2-09） | CommandGateway | `R_EPOCH_STALE_COMMAND` | 拒否のみ・状態不変 | 変化なし（audit） |\n| lease 無効化の記録（v0.2.2） | AuthorityManager | `R_LEASE_INVALIDATED` | LEASE_INVALIDATED 記録（原因 fault と対） | 原因行の disposition に従う |\n| command deadline 超過（v0.2.2） | CommandGateway | `R_DEADLINE_MISS` | TRANSFER_TO_SAFEHOLD(DEADLINE_MISS) | `HOLD` |\n| envelope 項の違反（v0.2.2） | CommandGateway | `R_ENVELOPE_VIOLATION` | 拒否 + TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION) | `HOLD` |\n| AcceptedEnvelope 充足不能（v0.2.2） | AuthorityManager（permit 発行時 / CAS 前提 7） | `R_ENVELOPE_EMPTY` | permit 不発行 / CAS REJECTED | `RESELECT`（次候補）→ 尽きれば `NO_CHAIN` |\n| InterruptOutcome（PLANNED_SWITCH / EVENT）受領（v0.2.2） | AuthorityManager | `R_CHECKPOINT_SWITCH_DISABLED` | TRANSFER_TO_SAFEHOLD(CHECKPOINT_DISABLED) | `HOLD` |\n| boundary 外からの転送要求（v0.2.2・B-H2 / B2-02） | AuthorityManager | `R_MIDSKILL_TRANSFER_BLOCKED` | permit 不発行 / CAS REJECTED・状態不変 | 変化なし（audit・lease 継続） |\n| IndependentSafetyLayer の heartbeat 欠落 / health failed（v0.2.2・B2-01） | CommandGateway / AuthorityManager | `R_SAFETY_LAYER_LOST` | 出力 = SafeStop（(i′)）+ TRANSFER_TO_SAFEHOLD(SAFETY) | `SAFE_STOP`（解除 = §5.4 SAFETY 行） |\n| validate_outcome の issues 非空（v0.2.2・B2-06 / A2-12） | Orchestrator（B1） | `R_OUTCOME_INVALID` | 状態 = S_BOUNDARY_WAIT（MARK_BOUNDARY_WAIT は受領の事実で実行済） | 候補評価を行わず `NO_CHAIN` → HOLD \\| SAFE_STOP |\n| boundary 滞留 / 再選択回数の超過（v0.2.2・B-M9） | Orchestrator / AuthorityManager | `R_BOUNDARY_DWELL_EXCEEDED` | TRANSFER_TO_SAFEHOLD(NO_CHAIN \\| SAFE_STOP) | `NO_CHAIN` → HOLD \\| SAFE_STOP |\n| permit の CONFLICT / VOID の通知（v0.2.2・B-L6） | AuthorityManager → Executor | （fault なし・`PERMIT_VOIDED` 記録） | executor は提案を破棄 | 変化なし |")
# ---- §4.1 TimingBinding ----
rep("    manager_liveness_s: CanonicalDecimal              # gateway が AuthorityState の鮮度を要求する上限",
    "    manager_liveness_s: CanonicalDecimal              # gateway が線形化読みを待つ上限（超過 = (iii)）\n    safety_heartbeat_timeout_s: CanonicalDecimal      # v0.2.2（B2-01）: IndependentSafetyLayer heartbeat の欠落上限（超過 = (i′) SafeStop + R_SAFETY_LAYER_LOST）\n    decision_max_age_s: CanonicalDecimal              # v0.2.2（B2-14）: permit 発行時に AuthorityDecision に許す最大 age\n    boundary_dwell_s: CanonicalDecimal                # v0.2.2（B-M9）: boundary 滞留の上限（超過 = R_BOUNDARY_DWELL_EXCEEDED → NO_CHAIN）\n    max_reselect_attempts: int                        # v0.2.2（B-M9）: 1 boundary あたりの候補試行上限\n    command_kind_mismatch_max: int                    # v0.2.2（B2-15）: 連続 kind 不一致の許容回数\n    inter_command_jitter_s: CanonicalDecimal          # v0.2.2（B-L2）: inter-command 間隔の許容偏差（超過 = R_TIMING_VIOLATION）")
# ---- §4.2 timing/hold ----
rep("- 実測 inter-command 間隔が profile 許容を超えて逸脱 ⇒ `R_TIMING_VIOLATION` ⇒ `HOLD`。",
    "- 実測 inter-command 間隔が profile 許容（`inter_command_jitter_s`）を超えて逸脱 ⇒ `R_TIMING_VIOLATION` ⇒ TRANSFER_TO_SAFEHOLD(TIMING_VIOLATION) ⇒ `HOLD`。\n- **hold の適用範囲（v0.2.2・B2-13）**: `hold` は連続 2 つの **admitted** command の間にのみ適用する。後続 command が未 admit の間、gateway は直近 admitted setpoint を保持する（hold 種別にかかわらず ZOH 相当・外挿禁止）。`command_deadline_s` 超過で SafeHold + `R_DEADLINE_MISS`。\n- **WAIT lease（v0.2.2・B-M6）**: `first_command_admitted` と `command_deadline_s` は `control_mode ∈ {DIFF_IK_EE_TARGET, SCRIPTED_SEQUENCE}` にのみ適用し、WAIT では両者を N/A = True として記録する。WAIT の liveness は executor heartbeat（`R_EXECUTOR_LOST`）で担う。")
# ---- §4.4 lease/profile sentence ----
repline("`LeaseMode` の member 名を EP profile 名と一致させないのは", f"`LeaseMode` の member 名を EP profile 名と一致させないのは、evidence profile（EP `requested_profile`）と runtime の出力可否を型で分離するため。lease は `authority_decision_ref` 経由で（frozen `evaluate_authority_grant` の入力 `eligibility_report` `{A}:346-347`）eligibility report の `requested_profile` を**参照するのみで再評価しない**。`profile_hash`（doc 06）は evidence profile を運ばない（v0.2.2・A-04）。")
# ---- §5.1 SafeHold + GatewayCommand ----
repline("| `DIFF_IK_EE_TARGET`（LEARNED） |", "| `DIFF_IK_EE_TARGET`（LEARNED） | **計測現在姿勢で凍結・速度 0**（直近 admitted EE target を目標に保持し続けない — 無効化 lease の運動意図を残さない・v0.2.2・B-M8）。新しい運動要求を出さない |")
rep("### 5.2 出力優先順位（D0 §F の優先を runtime で固定）",
    "```python\n@dataclass(frozen=True)\nclass GatewayCommand:                                 # 新語（v0.2.2・B-L3）— gateway が admission 判定する command の記録形\n    lease_id: str\n    control_epoch: int\n    executor_id: str\n    cmd_seq: int                                      # lease 内で厳密単調増加（重複・逆順 = R_TIMING_VIOLATION で拒否）\n    kind: ControlMode                                 # frozen enum（lease.control_mode と等値必須）\n    payload_ref: str\n    t_issue: float\n```\n\n### 5.2 出力優先順位（D0 §F の優先を runtime で固定）")
rep("  (i)   IndependentSafetyLayer の未解除 SafetyDecision があれば その出力（STOP/HOLD/RETRACT/FORCE_LIMIT）   … 最優先・ack を待たない\n  (ii)  else if owner == EXECUTOR ∧ ¬state.boundary_wait ∧ mode == CLOSED_LOOP_AUTHORITY ∧ hold 地平内の admitted command あり → その command",
    "  (i)   IndependentSafetyLayer の未解除 SafetyDecision があれば その出力（STOP/HOLD/RETRACT/FORCE_LIMIT）   … 最優先・ack を待たない\n  (i′)  else if IndependentSafetyLayer の heartbeat が safety_heartbeat_timeout_s を超えて欠落 → SafeStop（(ii) を評価しない・v0.2.2・B2-01）\n  (ii)  else if owner == EXECUTOR ∧ ¬state.boundary_wait ∧ ¬restart_pending ∧ mode == CLOSED_LOOP_AUTHORITY ∧ 直近 admitted command あり → その setpoint（hold は admitted 間のみ・§4.2）")
rep("- gateway が `manager_liveness_s` 内に新鮮な `AuthorityState` を読めない場合、(ii) を評価せず (iii) に落ちる（INV-19）。",
    "- admission は `AuthorityState` の**同期・線形化読み**で行う（cache を持たない — v0.2.2・B-H1）。読みが `manager_liveness_s` 内に完了しない場合、(ii) を評価せず (iii) に落ちる（INV-19）。\n- **再起動した gateway（v0.2.2・B-M10）**: 起動時に `restart_pending := True` とし、`AuthorityState.safehold_reason == GATEWAY_RESTART`（または `seq` > 起動時観測 seq）を観測するまで (i)/(i′)/(iii) のみを評価する（INV-25 の執行規則）。")
# ---- §5.4 ----
repline("| INITIAL / BOUNDARY_WAIT / TRANSFER / NO_CHAIN / EXECUTOR_LOST / DEADLINE_MISS / ENVELOPE_VIOLATION / HEALTH_FAIL |", "| INITIAL / NO_CHAIN / EXECUTOR_LOST / DEADLINE_MISS / TIMING_VIOLATION / ENVELOPE_VIOLATION / HEALTH_FAIL | 完全経路（ACK → permit → CAS）による TRANSFER_TO_EXECUTOR のみ | なし |")
insert_after("| MANAGER_RESTART | 同上 |", "| GATEWAY_RESTART | 同上 | `GATEWAY_CONFIG_MATCH` health check の pass + profile が定義する clearance role（doc 06）（v0.2.2・A2-08 / B2-08） |")
rep("Orchestrator・Executor・RecoveryRoutingPolicy は HOLD を解除できない（AuthorityState を書けない）。",
    "Orchestrator・Executor・RecoveryRoutingPolicy は HOLD を解除できない（AuthorityState を書けない）。CAS 条件 10 の集合 = 本表で「追加前提」を持つ行の集合 {SAFETY, SAFE_STOP, CHECKPOINT_DISABLED, MANAGER_RESTART, GATEWAY_RESTART}（両者を同一定義から導く — v0.2.2・A2-01 / B2-07）。")
# ---- §3.6 / §6.2 annotations ----
rep("1. Orchestrator は `snapshot = AuthorityManager.read_snapshot()` を取り、`validate_handoff(invocation, offer, producer_def, consumer_def, authority_epoch_snapshot=snapshot.control_epoch)` を **CAS 前**に呼ぶ。",
    f"1. Orchestrator は `snapshot = AuthorityManager.read_snapshot()` を取り、`validate_handoff(invocation, offer, producer_def, consumer_def, authority_epoch_snapshot=snapshot.control_epoch)` を **CAS 前**に呼ぶ（`invocation` = **producer の** `SkillInvocation`・`offer.producer_invocation_id` と一致 `{A}:381` — v0.2.2・A-11）。")
repline("B1  validate_outcome(invocation, outcome, definition)", "B1  validate_outcome(invocation, outcome, definition)                         … issues 非空 = R_OUTCOME_INVALID（v0.2.2）: MARK_BOUNDARY_WAIT は受領の事実で既に実行済（§3.5）。候補評価を行わず B5（NO_CHAIN）へ。SAFEHOLD からの起動（producer 無し）では B1 と offer 検証を skip し InitializationRecord.handoff_validation_report_ref = null")
rep("      offer あり: validate_handoff(invocation, offer, producer_def, definition_c, authority_epoch_snapshot = snapshot.control_epoch)",
    "      offer あり: validate_handoff(producer_invocation, offer, producer_def, definition_c, authority_epoch_snapshot = snapshot.control_epoch)   … invocation = producer の SkillInvocation（A-11）")
repline("B5  候補が尽きた", "B5  候補が尽きた / boundary_dwell_s 超過 / max_reselect_attempts 超過（v0.2.2・B-M9） → NO_CHAIN → TRANSFER_TO_SAFEHOLD(NO_CHAIN | SAFE_STOP per profile.escalation.on_no_chain) → disposition HOLD | SAFE_STOP")
# ---- §7 ----
rep("    CONTINUE_AT_BOUNDARY | RESELECT | RE_OBSERVE | HOLD | SAFE_STOP | NO_CHAIN | RECOVERY_ROUTE | ABORT",
    "    CONTINUE_AT_BOUNDARY | RESELECT | RE_OBSERVE | HOLD | SAFE_STOP | NO_CHAIN | RECOVERY_ROUTE   # v0.2.2: ABORT 削除（生成規則なし・B2-16）")
rep("    R_POST_OUTCOME_COMMAND | R_GATEWAY_RESTART | R_HEALTHCHECK_FAILED | R_PROFILE_INITIATION_FAILED   # v0.2.1",
    "    R_POST_OUTCOME_COMMAND | R_GATEWAY_RESTART | R_HEALTHCHECK_FAILED | R_PROFILE_INITIATION_FAILED |   # v0.2.1\n    R_MIDSKILL_TRANSFER_BLOCKED | R_SAFETY_LAYER_LOST | R_OUTCOME_INVALID | R_BOUNDARY_DWELL_EXCEEDED   # v0.2.2")
repline("| Terminal SUCCESS | 候補なし（chain 終端） |", "| Terminal SUCCESS | 候補なし（chain 終端） | NO_CHAIN → HOLD（`profile.escalation.on_no_chain == SAFE_STOP` なら TRANSFER_TO_SAFEHOLD(SAFE_STOP)） |")
repline("| Terminal FAILURE / TIMEOUT | 候補なし |", "| Terminal FAILURE / TIMEOUT | 候補なし | NO_CHAIN → HOLD（profile で SAFE_STOP = TRANSFER_TO_SAFEHOLD(SAFE_STOP)） |")
repline("| Terminal INVALID_STATE | 解消せず |", "| Terminal INVALID_STATE | 解消せず | SAFE_STOP（TRANSFER_TO_SAFEHOLD(SAFE_STOP)・原因 fault は別途記録・v0.2.2） |")
# ---- §8 ----
rep("    CAS_ATTEMPT | CLEARANCE_RECORDED | GATEWAY_RESTART | GENESIS_RECORDED   # v0.2.1",
    "    CAS_ATTEMPT | CLEARANCE_RECORDED | GATEWAY_RESTART | GENESIS_RECORDED |   # v0.2.1\n    COMMAND_ADMITTED   # v0.2.2（B-L3）: CLOSED_LOOP lease の admitted command（GatewayCommand 参照）")
repline("    payload_ref: str                                  # kind 別の typed payload", "    payload_ref: str                                  # kind 別の typed payload（ReadinessAck / CommitPermit / AuthorityCas / HealthConfirmation / RuntimeAssessmentRecord / GatewayCommand …）\n    profile_hash: str | None                          # v0.2.2（B2-17）: deployment 起因 record（permit 発行時 fault・MANAGER_RESTART・GENESIS_RECORDED）の join key（lease 無しでも profile と結線）")
# ---- §9 INV ----
rep("| INV-03 | admitted command: `(cmd.lease_id, cmd.control_epoch) == (state.active_lease_id, state.control_epoch)` を線形化点で満たす | R_EPOCH_STALE_COMMAND / R_LEASE_UNKNOWN_COMMAND |",
    "| INV-03 | admitted command: `(cmd.lease_id, cmd.control_epoch) == (state.active_lease_id, state.control_epoch)` を線形化点で満たし、`cmd.cmd_seq` は lease 内で厳密単調（v0.2.2） | R_EPOCH_STALE_COMMAND / R_LEASE_UNKNOWN_COMMAND / R_TIMING_VIOLATION |")
rep("| INV-07 | `ack.expected_control_epoch == permit.expected.control_epoch + 1 ∧ ack.valid_until ≥ permit.issued_at ∧ ack.invocation_id == proposed_lease.invocation_id` | R_ACK_MISBOUND |",
    "| INV-07 | `ack.expected_control_epoch == permit.expected.control_epoch + 1 ∧ ack.valid_until ≥ permit.issued_at ∧ ack.invocation_id == proposed_lease.invocation_id ∧ ack.executor_id == proposed_lease.executor_id ∧ ack.skill_action_id == proposed_lease.skill_action_id ∧ ack.lease_proposal_id == proposed_lease.lease_id`（v0.2.2） | R_ACK_MISBOUND |")
repline("| INV-16 |", f"| INV-16 | **型境界 + hash preimage の断定（v0.2.2・A-02 / A2-02 — 名前の非交差ではない）**: (a) runtime / profile 型の値は frozen 型として decode されない（frozen strict codec が runtime 固有 field〔lease_id / permit_id / profile_hash 等〕を unknown field として拒否 `{A}:385`）; (b) runtime / profile 型の値は frozen hash（SkillDefinitionHash / SkillActionId / ExecutionBundleHash / BehaviorSignature / tensor_binding_hash / evidence_policy_definition_hash）の preimage に入らない（03 matrix C01–C07）。frozen §8 の assert `{A}:550` は static hash の key 集合に対する主張であり、本 INV はその**趣旨を継承**する | 設計違反（test） |")
rep("| INV-17 | §3.7 の各事象に対応する `RuntimeAuditRecord` がちょうど 1 件 | 記録欠落 = fault |",
    "| INV-17 | §3.7 の各事象について、その行が要求する record kind ごとにちょうど 1 件の `RuntimeAuditRecord`（v0.2.2・B2-17） | 記録欠落 = fault |")
rep("| INV-19 | gateway が `manager_liveness_s` 内の `AuthorityState` を持たないとき (ii) を評価しない | R_MANAGER_UNAVAILABLE |",
    "| INV-19 | gateway の admission は `AuthorityState` の同期・線形化読みのみ（cache 不可）。読みが `manager_liveness_s` 内に完了しないとき (ii) を評価しない（v0.2.2・B-H1） | R_MANAGER_UNAVAILABLE |")
rep("| INV-27 | 全 `RuntimeFaultCode` member は §3.7 の失敗表に行を持つ（v0.2.1・B-10） | 設計違反（test） |",
    "| INV-27 | 全 `RuntimeFaultCode` member は §3.7 の失敗表に行を持つ（v0.2.1・B-10・v0.2.2 で total 化 B-M11 / B2-09） | 設計違反（test） |\n| INV-28 | TRANSFER_TO_EXECUTOR / permit 発行は `expected.owner.kind == SAFEHOLD ∨ expected.boundary_wait == True` のときのみ（boundary guard・v0.2.2・B-H2 / B2-02） | R_MIDSKILL_TRANSFER_BLOCKED |\n| INV-29 | IndependentSafetyLayer の heartbeat が `safety_heartbeat_timeout_s` を超えて欠落した線形化点以降、(ii) は評価されず出力 = SafeStop、かつ TRANSFER_TO_SAFEHOLD(SAFETY) が発行される（v0.2.2・B2-01） | R_SAFETY_LAYER_LOST |\n| INV-30 | `safehold_reason` は優先順位（SAFETY / SAFE_STOP > MANAGER_RESTART / GATEWAY_RESTART / CHECKPOINT_DISABLED > 他）を弱める方向に書き換えられない（v0.2.2・B-M2 / B2-04） | 設計違反（test） |\n| INV-31 | 再起動した gateway は `safehold_reason == GATEWAY_RESTART` を観測するまで (ii) を評価しない（v0.2.2・B-M10） | R_GATEWAY_RESTART |\n| INV-32 | CAS SUCCESS の線形化点 = durable commit 完了。`invalidated_lease_ids` は同一 durable store・同一 commit（v0.2.2・B-M12） | 設計違反（test） |")
# ---- §10 tests ----
rep("| T-18 | serialization boundary: runtime 型 field 名 ∩ frozen WCJ key 集合 = ∅ | INV-16 |",
    "| T-18 | serialization boundary（v0.2.2）: runtime 固有 key（lease_id / permit_id / profile_hash）を持つ payload を frozen 型として decode すると unknown field で拒否される；runtime 型の値が frozen hash の preimage に現れない | INV-16 |")
rep("| T-25 | 各 RuntimeFaultCode member を 1 回ずつ発火（v0.2.1） | 失敗表の行どおりの状態効果・disposition（INV-27） |",
    "| T-25 | 各 RuntimeFaultCode member を 1 回ずつ発火（v0.2.1） | 失敗表の行どおりの状態効果・disposition（INV-27） |\n| T-26 | S_LEASE_ACTIVE（boundary_wait = False）で permit 要求 / CAS（v0.2.2） | R_MIDSKILL_TRANSFER_BLOCKED・状態不変（INV-28） |\n| T-27 | 活性 lease 中に ISL heartbeat を停止（v0.2.2） | (i′) SafeStop・TRANSFER_TO_SAFEHOLD(SAFETY)・R_SAFETY_LAYER_LOST（INV-29） |\n| T-28 | SAFEHOLD(SAFETY) 中に MANAGER_RESTART / GATEWAY_RESTART / NO_CHAIN の CAS（v0.2.2） | 理由不変・記録付き no-op（INV-30） |\n| T-29 | validate_outcome issues 非空（v0.2.2） | boundary_wait = True・R_OUTCOME_INVALID・候補評価なし・NO_CHAIN 経路 |\n| T-30 | in-memory CAS 成功直後・durable 書込み前に manager kill（v0.2.2） | restart 後に当該 CAS は無かったものとして扱われ epoch が二重に使われない（INV-32） |\n| T-31 | S_HEALTH_PENDING 中に TerminalOutcome 受領（v0.2.2） | MARK_BOUNDARY_WAIT・health 取消・未確認事実を ASSESSMENT に記録 |")
# ---- §12 OP ----
repline("| OP-6 |", f"| OP-6 | durable store の実装 primitive（write-ahead の具体）。⚠ v0.2.2 で「線形化点 = durable commit 完了」は**要件化**した（§3.2・INV-32・B-M12）— 残るのは primitive の選定 | D0 「`CAS/lock` は D1 refinement」`{D0}:270-272` | 要件は §3.2 に置く |")
repline("| OP-14 |", f"| OP-14 | D0 §G `D_event`（handoff deadline）と本 doc の `ack_timeout_s` / `permit_ttl_s` / `boundary_dwell_s`（v0.2.2）の整合。deadline miss → safe-stop は `boundary_dwell_s` 超過 → NO_CHAIN 経路に写像（B-M9） | `{D0}:363-365` | RT0 で測定後に整合検査 |")
rep("| OP-16 |", "| OP-18 | cell 固有の gate（profile 依存条件）を frozen `AuthorityDecision` の入力 `acceptance_state` / `safety_gate_state` に載せるかは O0/S0/V0 層の事項（v0.2.2・A-01）。本 doc は permit 側で `profile_hash` を束縛するのみ | `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:346-350` | O0/S0/V0 へ carry |\n| OP-19 | 活性 lease 中の calibration / evidence 失効の検出（既定 = 次の permit 発行時・曝露 ≤ 1 skill）。周期検査を manager に持たせるかは未裁定（v0.2.2・B-M7） | doc 06 §5 | 既定を保守側に置く |\n| OP-16 |")
# ---- 版歴 v0.2.2 fold table (rendered from VERD map) ----
FOLDS = [
 ("B-H2 / B2-02","mid-skill 転送を authority 層が阻止する条件が無い","§3.4 (d)・§3.5 条件 11・INV-28・T-26・`R_MIDSKILL_TRANSFER_BLOCKED`"),
 ("B2-01 / B-H3","活性 lease 中の ISL heartbeat 喪失に遷移・fault が無い","§3.7 行・§5.2 (i′)・INV-29・T-27・`R_SAFETY_LAYER_LOST`・`safety_heartbeat_timeout_s`"),
 ("B-M2 / B2-04","safehold_reason が弱い理由で上書きされる","§3.5 優先順位・INV-30・T-28"),
 ("B-M3 / B2-05","SAFE_STOP を設定する遷移が無く (iii) の SafeStop が空文","§3.5 SAFE_STOP 規則・§3.7 NO_CHAIN / HEALTH_FAIL 行・§7 表"),
 ("B2-06 / A2-12 / B-L5","validate_outcome 失敗時に boundary_wait が立たず disposition が二義","§3.5 MARK_BOUNDARY_WAIT・§3.7 行・§6.2 B1・`R_OUTCOME_INVALID`・T-29"),
 ("A2-01 / B2-07 / A2-08 / B2-08","CAS 条件 10 と §5.4 の集合不一致・§5.4 の欠落行","§3.5 条件 10・§5.4（GATEWAY_RESTART / TIMING_VIOLATION 行・集合の同一定義）"),
 ("A-01 / B-M5 / B2-14","条件 6 が frozen AuthorityDecision に無い profile_hash 束縛を要求・decision の age 未規定","§3.5 条件 6・§3.4 (e)(f)・`decision_max_age_s`・OP-18"),
 ("A-02 / A2-02","INV-16 が名前の非交差として充足不能","INV-16・T-18・anchor 1"),
 ("B-H1","gateway admission が cache 読みとも線形化読みとも読める","§2 表・§5.2・INV-19"),
 ("B-M4 / B2-03","ACK / CAS 引数が executor・lease 提案・permit に束縛されない","§3.3・§3.5 条件 2・3・INV-07"),
 ("B2-10","S_HEALTH_PENDING 中の outcome 受領に行が無い","§3.5・§3.7 from 列・T-31"),
 ("B-M6","WAIT lease が HEALTH_FAIL / DEADLINE_MISS に必ず落ちる","§4.2 WAIT 規則"),
 ("B-M12 / B2-11 / B-L4","線形化点 = durable commit が未規定・genesis の下限なし","§3.2・INV-32・T-30・OP-6"),
 ("B2-12","clock domain 未宣言","§3.2・§3.3"),
 ("B2-13","hold の適用範囲が admitted 後の窓で未定義","§4.2"),
 ("B-M8","SafeHold(DIFF_IK) が無効化 lease の目標を保持","§5.1"),
 ("B-M9","boundary 滞留・再選択回数に上限が無い","§3.7・§6.2 B5・`boundary_dwell_s` / `max_reselect_attempts`・`R_BOUNDARY_DWELL_EXCEEDED`・OP-14"),
 ("B-M10","再起動 gateway が旧 lease を再 admit し得る","§5.2 `restart_pending`・INV-31"),
 ("B-M11 / B2-09","失敗表に行の無い fault code","§3.7 失敗表（11 行追加）・INV-27"),
 ("A-10 / B-L1","SAFETY_STABILIZED の safehold_reason が節間で不一致","§3.7 InterruptOutcome 行の分割"),
 ("B-M1","lease-scoped な理由の再試行が別 lease を誤無効化","§3.5 再試行規則"),
 ("B-M7","活性 lease 中の evidence 失効の扱いが 06 と不整合","OP-19（既定 = 次 permit 発行時・06 §5 / PT-13 を同期）"),
 ("B-L2 / B2-15 / A-12","05 が参照する閾値に 06 の field が無い","§4.1 TimingBinding 6 field・§3.7 行・06 RuntimeTimeouts"),
 ("B-L3","admitted command が型を持たず順序検査が無い","§5.1 `GatewayCommand`・INV-03・AuditKind `COMMAND_ADMITTED`"),
 ("B-L6","permit CONFLICT / VOID が ACK 元 executor に通知されない","§3.4"),
 ("B2-16","到達不能な enum member（ABORT / BOUNDARY_WAIT / TRANSFER）","§3.2 / §7 で 削除"),
 ("B2-17","RuntimeAuditRecord に profile_hash が無い・INV-17 の「ちょうど 1 件」","§8・INV-17"),
 ("A-03 / A2-10","凍結語彙の不在主張が広すぎ・scratch 参照","§2 home matrix（再現 command 併記）・07 §1"),
 ("A-04","lease が profile_hash 経由で EP profile を参照すると読める","§4.4"),
 ("A-05 / A2-04","ActionBinding に bounds を帰属","§0"),
 ("A2-05","旧 epoch 拒否の所有と執行点の区別","§2 表・anchor 2"),
 ("A-11","validate_handoff の invocation が producer 側であることが不明","§3.6・§6.2 B4"),
 ("A-09 / A2-11","timestamp の x mask","header・§13"),
 ("A-07 / A-08 / A2-07","02 / 03 CSV の引用・tuple・CSV 検査様式","02・03・checker CSV mode・08 §1"),
 ("A2-06","07 §3 の SkillActionId 記述","07 §3"),
 ("A-06 / A2-09 / A2-03","06 反循環文の自己矛盾・P_RESOURCE_UNATTESTED の検査 cell","06 §2.3・§3"),
]
def verd(ids):
    vs = []
    for i in ids.replace(" ", "").split("/"):
        v = VERD.get(i)
        vs.append(f"{i}={v}" if v else f"{i}=（verifier 未了）")
    return "・".join(vs)
rows = "\n".join(f"| {ids} | {desc} | {sec} | {verd(ids)} |" for ids, desc, sec in FOLDS)
rep("## 14. Review anchors", f"""- **v0.2.2 fold（2026-09-04 実測時刻は §13 末尾）— 3 軸独立レビュー（reviewer A / A2〔Opus〕/ B / B2〔Opus〕/ C・別 context・v0.2.1 対象）の finding を verifier（3 lens・別 context）の verdict と起草者の再検証に基づき fold**:

| finding | 内容 | 変更節 | verifier verdict |
|---|---|---|---|
{rows}

- fold しなかった finding（refuted / NOT_A_DEFECT / 保留）は `11_THREE_AXIS_REVIEW_RECORD_20260903.md` に理由付きで列挙する。
- v0.2.2 でも impl / training / authority = CLOSED。frozen 4 file 不変（`verify_exact_baseline_pins.sh` 11/11 PASS を再確認）。

## 14. Review anchors""")
rep("- **v0.2.1 fold（2026-09-04 01:5x UTC）", "- **v0.2.1 fold（2026-09-04 01:47 UTC 実測）")
repline("1. 本 doc は frozen 4 file に field / enum member を足していない", f"1. 本 doc は frozen 4 file に field / enum member を足していない — §1・§11 項 3・INV-16（型境界 + hash preimage の断定。`{A}:385` の strict codec が runtime 固有 field を unknown field として拒否する）。")
repline("2. `AuthorityManager` の責務", f"2. `AuthorityManager` の責務（CAS・発行・旧 epoch 拒否の**所有**・`handoff_offer_id` 単位の使用済み拒否・snapshot 読出し）は frozen の O0 層要求仕様に一致し、旧 epoch 拒否の**執行点** = CommandGateway admission（manager 所有状態の線形化読み） — §2 表 ↔ `{A}:382`。")
open(f5, "w", encoding="utf-8").write(t); print("05 -> v0.2.2 written; lines", t.count("\n"))
