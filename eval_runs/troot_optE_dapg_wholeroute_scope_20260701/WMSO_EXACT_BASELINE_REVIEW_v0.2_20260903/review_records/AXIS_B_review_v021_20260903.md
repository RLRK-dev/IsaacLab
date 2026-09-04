# 軸 B（runtime safety / authority・反証軸）レビュー — 05 RUNTIME SPEC v0.2.1 / 06 §4-§5

- reviewer = REVIEWER B（別 context・adversarial）; 実施 = 2026-09-04 02:09–02:2x UTC（`date -u` 実測）; 対象 = `$D/WMSO_EXACT_BASELINE_REVIEW_v0.2_20260903/05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md`（792 行・全読）+ `06_WMSO_INDUSTRIAL_PROFILE_v0.2_REVIEW_CANDIDATE_20260903.md` §4-§5（456 行・全読）。`$D` = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701`。
- 版 label は照合注記のみ。内容（行番号・引用）で引く。引用行はすべて本 session で `sed -n` 再確認済。
- 陽性対照（10_*）で注入された 8 欠陥は実 doc に無いことを確認し、本 report の finding には含めない（PC-05-A/B/C/D・PC-06-E/F/G/H に相当する文は実 doc に存在しない: 05:233 旧 epoch 拒否 = CAS 同一線形化点、05:182/318 permit one-shot、05:231 `∪ {consume_offer_id}` 存在、05:419 SHADOW = DISABLED）。

## 0. 共通前提の実測

| 前提 | 結果 |
|---|---|
| pin 再測 `bash $D/…/verify_exact_baseline_pins.sh` | **11/11 PASS**（02:09 UTC）。HEAD=`297c850bb31a61b56d5f2def9dd616a7c254f6d2` branch=`claude/v0-2-design-candidates-snqbmy`。D1.1-A `00192d20…` / D1.1-B `5a1874d3…` / EP md `c474acea…` / EP JSON `e63176af…` / definition hash `e7ca4309…` / blob `1353430228…` / `ebe8154abf…` |
| 機械検査 05 `--runtime` | citations=139 **FAIL=0** WARN=6（C2 heuristic・05 anchor 23 の説明と一致） |
| 機械検査 06 | citations=55 **FAIL=0** WARN=19 |
| 追加機械検査（本 reviewer） | `RuntimeFaultCode` 33 member を抽出し §3.7 失敗表（05:281-308）と突合 → **6 member に行なし**（finding B-M12） |

## 1. 判定

**HOLD**（08 計画 §5: CRITICAL / HIGH が残る）。HIGH 3 件（B-H1 / B-H2 / B-H3）はいずれも schema delta 0 の文言追加で fold 可能だが、本 reviewer の text / logic / impact 3 lens 自己反証では refute できなかった。MEDIUM 12・LOW 6。

## 2. Findings

型 = {id, 軸, severity, 候補 doc:line, 凍結 file:line, 再現 / 反例, 最小修正（schema delta 0）}。

### B-H1（HIGH・B1）CommandGateway の admission 読みが「線形化」と「鮮度上限 manager_liveness_s の cache」の 2 読みを許し、後者では旧 epoch 拒否が CAS 線形化点から最大 manager_liveness_s 遅れる

- 候補: 05:233「CommandGateway の admission は `AuthorityState` を**線形化して読む**ため、この点以降 … `R_EPOCH_STALE_COMMAND`」／ 05:82 gateway の持つ状態 =「admission 用の `AuthorityState` 読み（線形化）+ 直近 admitted command」／ 05:344 `manager_liveness_s` =「gateway が AuthorityState の**鮮度を要求する上限**」／ 05:456「`manager_liveness_s` 内に**新鮮な** `AuthorityState` を読めない場合 (ii) を評価せず (iii)」／ INV-19 05:649。
- 凍結: `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382`（旧 epoch command 拒否 = authority manager の状態所有責務）／ `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:270-272`（one atomic token flip — exactly one owner at every instant, no double-owner interval）。
- 再現（cache 読みの下）: (1) `s0 = (EXECUTOR(X1), e, L1, …)`、gateway が t0 に s0 を読む。(2) t1 > t0 で TRANSFER_TO_EXECUTOR（X2, L2）が SUCCESS → `s1 = (EXECUTOR(X2), e+1, L2)`。X2 は活性を知り `(L2, e+1)` を送る。(3) t2 ∈ (t1, t0 + manager_liveness_s) で X1（何も知らされない）が `(L1, e)` を送る → gateway cache = s0 ⇒ **admit** → 出力 (ii) = 無効化済 lease L1 の command。同時に X2 の `(L2, e+1)` は cache 基準で `R_EPOCH_STALE_COMMAND`。(4) X1・X2 とも「自分が owner」と信じる区間が manager_liveness_s まで続き、05:234「旧 lease の直近 command は … 即座に出力から外れる」・05:235「復活経路は存在しない」に反する。線形化読みの下ではこの trace は不可能だが、05:344/456 の「鮮度上限」概念は線形化読みと両立しない（毎回同期読みなら鮮度は常に 0 で上限 parameter は意味を持たない）。doc はどちらかを選んでいない。
- 最小修正: §2 / §3.5 / §5.2 に 1 文を追加 —「gateway の admission 判定は AuthorityCas と線形化された **同期読み**（read-your-CAS）に対して行い、cache を admission に用いない。`manager_liveness_s` はその同期読みが完了しない場合に (ii) の評価を止め (iii) へ落とすまでの上限（可用性）であって、状態の許容 age ではない」。INV-19 の文言を「読みが完了しない」に統一。schema delta 0。

### B-H2（HIGH・B6）TRANSFER_TO_EXECUTOR の前提条件 1-10 に「from ∈ {S_SAFEHOLD, S_BOUNDARY_WAIT}」が無く、AuthorityManager 層に mid-skill 切替経路が残る

- 候補: 05:216-228（前提条件 1-10 — owner.kind / boundary_wait への言及なし）／ 05:181（permit 発行前提 (a)-(c) — 同）／ 05:261「表外遷移は存在しない」／ 05:265（遷移表は from = `S_SAFEHOLD` / `S_BOUNDARY_WAIT` のみ）／ INV-21 05:651 = Orchestrator 側の時刻不変量で違反時は「設計違反（test）」（manager が拒否しない）。
- 凍結: `$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59`（boundary = TERMINAL のみ・checkpoint 途中切替 = 別 gate）／ `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:273-274`（producer retains ownership）。
- 再現: (1) `s = (EXECUTOR(X1), e, L1, boundary_wait=False, seq=n)`（X1 走行中・outcome 未受領）。(2) 第 2 の Orchestrator instance（05:276 が許す「新 instance が B0 から再開」、旧 instance も生存）またはバグを持つ Orchestrator が X2 から ReadinessAck を取り `expected = s` で permit を要求。05:181 (a)-(c) は全て pass し得る。(3) CAS: 条件 1（tuple 等値）… 条件 10 の全てが満たされ **SUCCESS** → L1 は走行途中で無効化・SafeHold・L2 活性。TerminalOutcome も HandoffOffer も無い mid-skill 切替が authority 層で成立し、05:261 の主張と prereg:59 の scope を manager が守っていない。doc の設計原理（Orchestrator を信用せず manager が束縛を検査する — 05:160/221/222）と矛盾。
- 最小修正: 条件 11 を追加 —「`expected.owner.kind == SAFEHOLD ∨ expected.boundary_wait == True`。偽 = REJECTED・fault `R_PERMIT_MISBOUND`」。permit 発行前提 (d) にも同条件。INV-21 を manager 側の機械検査へ昇格。schema delta 0（既存 tuple 要素のみ使用）。

### B-H3（HIGH・B7）IndependentSafetyLayer の heartbeat 喪失 / health = failed が活性 lease 中に何の遷移も起こさず、executor が safety 層なしで走り続ける

- 候補: 05 に ISL heartbeat 喪失の runtime 規則が無い（grep: 05:64 引用、05:85 責務列挙、05:227 CAS 条件 9 = 転送時のみ、05:714 OP-9・05:721 OP-17 は別件）。05:449 (i) は「未解除 `SafetyDecision` があれば」— 死んだ ISL は decision を出さない。05:429 §4.5 無効化 trigger 列に ISL heartbeat 喪失なし。06:67 `SAFETY_LAYER_HEARTBEAT` は HealthCheckKind に在るが 06:68 stage ∈ {BEFORE_PERMIT, AT_HEALTH_CONFIRMATION, BOTH} のみで lease 中の評価点が無い。06:117 `requires_safety_layer_health: True 必須` に runtime 上の帰結が無い。
- 凍結: `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:318`「missed heartbeat ⇒ consumers must **not** assume safety alive; monitor `failed` ⇒ system fails to **safe-stop**」／ `:319`。
- 再現: (1) `S_LEASE_ACTIVE(CLOSED_LOOP_AUTHORITY)`、X1 が command を送る。(2) ISL process が停止（heartbeat 停止・decision なし）。(3) `out(t)`: (i) 該当なし → (ii) X1 の admitted command → TERMINAL まで継続。D0:318 の「fails to safe-stop」が起きない。cond 9 は次の転送まで効かない。
- 最小修正: §3.7 に行追加 —「any (EXECUTOR) | ISL heartbeat が `safety_heartbeat_timeout_s` を超えて欠落 or health == failed | TRANSFER_TO_SAFEHOLD(SAFETY) | FAULT(`R_SAFETY_OVERRIDE`)・DISPOSITION(SAFE_STOP)」+ §5.2 に (i′)「ISL heartbeat が stale なら (ii) を評価せず SafeStop」+ §4.5 trigger 追加。timeout は 06 `RuntimeTimeouts.safety_heartbeat_timeout_s`（profile 由来・INV-22 整合）。runtime 層のみ・frozen schema delta 0。

### B-M1（MEDIUM・B2/B4）TRANSFER_TO_SAFEHOLD の再試行規則が lease-scoped な trigger を再検査せず、別 lease を誤って無効化し偽の audit を残す

- 候補: 05:237「CONFLICT した場合 … current を再読して**即座に再試行**する」（理由の再検査なし）／ INV-24 05:654。
- 凍結: `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:270-272`（owner 転送の原子性）。
- 再現: (1) `s = (EXECUTOR(X1), e, L1, boundary_wait=True)`。(2) manager が X1 heartbeat 喪失を検出し TRANSFER_TO_SAFEHOLD(EXECUTOR_LOST, expected=s) を準備。(3) 先に TRANSFER_TO_EXECUTOR(X2, L2, expected=s) が SUCCESS → `s' = (EXECUTOR(X2), e+1, L2)`。(4) safehold CAS → CONFLICT → 規則どおり再読・即再試行 → SUCCESS → `(SAFEHOLD(EXECUTOR_LOST), e+2)`、健全な L2 が「EXECUTOR_LOST」で無効化・全 permit VOID・audit は L2 に対する偽の R_EXECUTOR_LOST。fail-closed 方向だが §15 records-must-match-fact に反し、INV-24 の「CONFLICT 中の出力は (i) または (iii)」も EXECUTOR_LOST / HEALTH_FAIL（manager 検出・gateway 非認知）では hold 地平内の admitted command が (ii) に残るため偽。
- 最小修正: 再試行規則を分岐 —「reason ∈ {SAFETY, SAFE_STOP, MANAGER_RESTART, GATEWAY_RESTART}（非 lease-scoped）は無条件再試行。それ以外（EXECUTOR_LOST / HEALTH_FAIL / DEADLINE_MISS / ENVELOPE_VIOLATION / TIMING_VIOLATION / NO_CHAIN / CHECKPOINT_DISABLED）は `current.active_lease_id == trigger.lease_id` のときのみ再試行、異なれば CAS を捨て FAULT を元 lease_id で記録」。INV-24 を「(i)・(iii)・または hold 地平内の既 admitted command（≤ command_deadline_s）」に訂正。

### B-M2（MEDIUM・B7）`safehold_reason` が単一値で上書きされ、SAFETY / SAFE_STOP の clearance 要件が MANAGER_RESTART / GATEWAY_RESTART により消える（laundering）

- 候補: 05:237 事後条件 = `(SAFEHOLD, epoch+1, None, consumed, reason, …)`（reason 置換）／ 05:228 条件 10 は現在の reason だけを見る／ 05:464-470 §5.4 は reason 別の解除経路／ 05:274-275。
- 凍結: `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:320`（`stabilized_post_action_state` が resumption eligibility の根拠）／ `:318`。
- 再現: (1) ISL STOP → `SAFEHOLD(SAFETY)`。(2) AuthorityManager 再起動 → 05:274 TRANSFER_TO_SAFEHOLD(MANAGER_RESTART) → reason := MANAGER_RESTART。(3) §5.4 の解除要件は「durable state の整合検査記録」に降格。残る防壁は条件 9「未処理の STOP/HOLD 決定が無い」のみで、これは ISL が decision 状態を保持している場合に限る。ISL または gateway（(i) の「未解除 SafetyDecision」保持者）も再起動すれば要件は完全に失われる。変種: manager 停止中に ISL decision が到着すると SAFETY は state に一度も記録されず、復帰後 reason = MANAGER_RESTART。
- 最小修正: reason 上書きに優先規則 —「SAFETY / SAFE_STOP は MANAGER_RESTART / GATEWAY_RESTART / NO_CHAIN 等で上書きされない（再起動は FAULT + audit のみ・reason 維持）」。加えて manager 起動時に ISL へ「未解除 decision の有無」を問い合わせ、有れば reason := SAFETY で復帰。schema delta 0。

### B-M3（MEDIUM・B7/B8）disposition `SAFE_STOP` を `safehold_reason = SAFE_STOP` に写す遷移が無く、profile が SAFE_STOP へ強化しても gateway 出力は SafeHold のまま

- 候補: 05:451「(iii) SafeHold（`safehold_reason == SAFE_STOP` なら SafeStop）」／ 05:270 NO_CHAIN 行 = `S_SAFEHOLD(NO_CHAIN)`・DISPOSITION(HOLD | SAFE_STOP per profile)／ 05:292 HEALTH_FAIL 行 = `S_SAFEHOLD(HEALTH_FAIL)`／ 05:590 INVALID_STATE 解消せず = SAFE_STOP／ 05:122 enum に SAFE_STOP はあるが、これを設定する遷移行が §3.7 に 1 つも無い（grep 実測）。
- 凍結: `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151`（`FailClosedAction.SAFE_STOP`）／ `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:363`（miss action = hardest safe action STOP）。
- 再現: profile `EscalationPolicy.on_no_chain = SAFE_STOP`（06:175）。B5 → TRANSFER_TO_SAFEHOLD(NO_CHAIN) → state.reason = NO_CHAIN → (iii) = SafeHold。SafeStop（stop-class 要求）は出ない。disposition record に SAFE_STOP と書かれるが物理出力は HOLD。
- 最小修正: §3.7 の NO_CHAIN / HEALTH_FAIL / INVALID_STATE 行に「escalation target == SAFE_STOP のとき `safehold_reason := SAFE_STOP`（それ以外は既存 reason）」、または CAS に `escalated: bool` を添えて (iii) の判定を `reason == SAFE_STOP ∨ escalated` にする。schema delta 0。

### B-M4（MEDIUM・B1/B3）CAS 条件 3 の ACK 束縛検査に `executor_id` と `lease_proposal_id` が無く、readback 済み envelope と permit の proposed_lease が一致しないまま CAS が成功し得る

- 候補: 05:160「ACK は『候補 invocation + 期待 epoch + 消費予定 offer + **lease 提案**』に束縛される。いずれかが変われば ACK は無効（R_ACK_MISBOUND）」／ 05:221 条件 3 = expected_control_epoch / valid_until / invocation_id / handoff_offer_id / envelope_readback_ok のみ（lease 提案・executor_id なし）／ INV-07 05:637 も同じ 3 項／ 05:154 `envelope_readback_ok` は「AcceptedEnvelope / TimingBinding を読み戻し等値確認」だが permit（05:166-179）は ACK の後に作られ proposed_lease を持つ。
- 凍結: `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:269`（candidate `next_owner` が accept + ack）／ `:272`。
- 再現: X2 が invocation I・offer O・proposal P1（envelope E1）で ACK A。Orchestrator が ack_id=A・proposed_lease = {executor_id: X3（同 invocation I の別 instance）, envelope E2} で permit を要求。条件 3 は全て真 → CAS SUCCESS → owner = X3（ACK していない）・envelope E2（誰も readback していない）。05:160 の規範と 05:221 の実装が乖離。証明 A（05:312）の「lease は executor_id を 1 つだけ持つため executor についても同じ」は admission が executor identity を検査しない（INV-03 = lease_id, epoch のみ）ため未支持。
- 最小修正: 条件 3 に `ack.executor_id == permit.proposed_lease.executor_id ∧ ack.lease_proposal_id == permit.proposed_lease.lease_id`（proposal id = 最終 lease_id と定義）を追加し INV-07 に同期。schema delta 0。

### B-M5（MEDIUM・B5）CAS 条件 6 は AuthorityDecision の inputs 束縛が `profile_hash` と一致することを要求するが、frozen `evaluate_authority_grant` の inputs に profile は無い — 不能判定 = FALSE ゆえ CLOSED_LOOP_AUTHORITY lease は構成不能（または schema delta を要する）

- 候補: 05:224 条件 6「decision の inputs hash/ref 束縛が lease の `skill_action_id` / **`profile_hash`** に一致」／ 05:218「不能判定 = FALSE」／ 06:278「`CommitPermit.profile_hash` と等値（05 §3.5 前提 6 の inputs 束縛）」。
- 凍結: `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:346-351`（inputs = eligibility_report / acceptance_state / two_key_state / safety_gate_state — profile なし）／ `:385`（strict codec — AuthorityDecision に field を足せない）。
- 再現: 任意の frozen AuthorityDecision に対し「inputs 束縛 ∋ profile_hash」は評価不能 → 条件 6 FALSE → 全 CLOSED_LOOP 転送 REJECTED。fail-closed 方向だが、doc が定義する mode が凍結型と両立しない。
- 最小修正: 条件 6 を「decision の inputs 束縛（eligibility_report ref）が lease の `skill_action_id` に一致」に限定し、`profile_hash` の等値は `permit.profile_hash == proposed_lease.profile_hash`（条件 2 系）へ移す。06:278 を同期。schema delta 0。

### B-M6（MEDIUM・B10/B8）`ControlMode.WAIT` の lease は運動 command を出さないため `first_command_admitted` と `command_deadline_s` により常に HEALTH_FAIL / DEADLINE_MISS になる

- 候補: 05:441 WAIT の SafeHold =「no-op（元々運動 command を出さない）」／ 05:211 `first_command_admitted`（CLOSED_LOOP: 最初の admissible command が admit された）／ 05:266-267 HealthConfirmation 全 True 必須／ 05:396「次 command が `command_deadline_s` 内に届かなければ … SafeHold（R_DEADLINE_MISS）」／ 05:343 `command_deadline_s` は非 null（WAIT でも要求）。
- 凍結: `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:62`（`ControlMode` = DIFF_IK_EE_TARGET | SCRIPTED_SEQUENCE | WAIT）／ `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:125-127`（action timing は LEARNED の binding）。
- 再現: WAIT skill の lease を CAS → executor は command を出さない → `health_confirm_timeout_s` で `first_command_admitted == False` → TRANSFER_TO_SAFEHOLD(HEALTH_FAIL)。仮に通っても command_deadline_s で DEADLINE_MISS。frozen enum の 1/3 が runtime で実行不能。
- 最小修正: 「`first_command_admitted` / `command_deadline_s` は control_mode ∈ {DIFF_IK_EE_TARGET, SCRIPTED_SEQUENCE} に適用。WAIT は executor heartbeat（`R_EXECUTOR_LOST`）で liveness を担保し、両検査を N/A（記録 True）とする」。schema delta 0。

### B-M7（MEDIUM・B5）06 §5 / PT-13 が主張する「lease 活性中の calibration 失効・evidence 失効 ⇒ lease 無効化」に 05 側の検出点・遷移が無い

- 候補: 06:281「lease 活性中に profile の前提が崩れた場合 … **lease 無効化**（05 §4.5 → `R_LEASE_INVALIDATED` / `R_HEALTH_CONFIRM_FAILED`）」／ 06:371 PT-13「活性 lease は無効化」／ 05:429 §4.5 trigger 列に該当なし／ 05:263-276 遷移表に該当行なし／ 06:68 HealthCheckStage に lease 中の stage なし／ HealthConfirmation は 1 回（05:266）。
- 凍結: `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:318`（fail to safe-stop の原則）。
- 再現: 受理済 profile の `CalibrationRef.valid_until` が lease 中に経過。05 の誰も検出しない → lease は TERMINAL まで継続。06 の主張（PT-13 期待値）は 05 では偽。
- 最小修正（保守案）: 06:281 / PT-13 を「検出点 = 次の permit 発行時（05 §3.4 (b) → `R_PROFILE_MISBOUND`）。活性 lease は TERMINAL boundary まで継続（曝露 ≤ 1 skill）」に改める。積極案なら 05 §3.7 に AuthorityManager の定期検査行（TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION) 流用）を足す。いずれも frozen schema delta 0。

### B-M8（MEDIUM・B2/B10）`SafeHold(DIFF_IK_EE_TARGET)` = 直近 admitted target の保持は、§4.2 が否定する「無期限 ZOH」そのものであり、無効化済 lease の運動意図が SafeHold として継続する

- 候補: 05:439「直近 admitted EE target（無ければ計測現在姿勢）を目標として保持・速度 0」／ 05:396「hold 継続ではなく `SafeHold`（`R_DEADLINE_MISS`）— 無期限 ZOH を『安全』と見なさない」／ 05:234「旧 lease の直近 command は … 即座に出力から外れる」。
- 凍結: `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:127`（hold = ZOH / 線形補間の保持規約）／ `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:273-274`（safe-stops）。
- 再現: DEADLINE_MISS → SafeHold(target = 直近 admitted target)。DiffIK の setpoint 保持 = その target への収束継続 = ZOH。05:396 の区別は物理的に空。TRANSFER 後も旧 lease の target が SafeHold 目標として残り、05:234 と語義上のみ整合。
- 最小修正: SafeHold(DIFF_IK) を「計測現在姿勢を目標に固定（直近 admitted target は使わない）」に改めるか、意図的に直近 target を残すなら 05:396 の「無期限 ZOH ≠ 安全」の文を削り「SafeHold = 直近 admitted target の ZOH + controller 側 decel（OP-4）」と正直に書く。schema delta 0。

### B-M9（MEDIUM・B7/B10）boundary 滞留・再選択試行に上限が無く、RE_OBSERVE ↔ RESELECT / HEALTH_FAIL → 即再選択の loop が無期限に続く。D0 §G の handoff deadline miss（→ safe-stop）が disposition に写像されていない

- 候補: 05:589 `RE_OBSERVE → RESELECT`（回数上限なし）／ 05:292 HEALTH_FAIL → HOLD → 05:466 解除 = 完全経路のみ（同一候補の即再試行を妨げない）／ 05:339-344 `TimingBinding` に boundary 滞留上限なし／ 06:145-151 `RuntimeTimeouts` 同／ 05:719 OP-14 は `D_event` と ack/permit timeout の整合のみ。
- 凍結: `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:273`（`timeout` — no `accept` within the handoff deadline, §G → producer retains and **safe-stops (or re-observes)**）／ `:364`（Event-checkpoint miss action = cached-recovery / safe-stop）／ `:213`（anti-thrash）。
- 再現: INVALID_STATE → RE_OBSERVE → 新 belief も INVALID → RESELECT → … `S_BOUNDARY_WAIT` に SafeHold のまま無期限。安全だが D0:273 の「deadline → safe-stop」が実装されず、B7 の「deadline miss → disposition」写像が欠ける。
- 最小修正: 06 `RuntimeTimeouts.boundary_dwell_s` と `max_reselect_attempts`（05 `TimingBinding` に写す）を追加し、超過 = `NO_CHAIN → HOLD | SAFE_STOP（profile）`。runtime/deployment 層のみ・frozen schema delta 0。

### B-M10（MEDIUM・B4）INV-25「再起動前の lease は新 CAS 無しに再 admit されない」を成立させる gateway 側の規則が無い

- 候補: 05:275「gateway は SafeHold 出力で起動し manager へ再起動を報告。manager が CAS」／ 05:307／ INV-25 05:655。gateway が再起動後に fresh な `AuthorityState`（旧 lease 活性）を読めば §5.2 (ii) の条件は満たされる。
- 凍結: `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:272`（no owner-gap / no double-owner — 復帰時の一貫性）。
- 再現: (1) `s = (EXECUTOR(X1), e, L1)`、gateway 再起動 t0・SafeHold・s を読む・報告送信。(2) t0+δ で X1 が `(L1, e)` → state 一致 → admit → (ii)。(3) t0+2δ で manager の TRANSFER_TO_SAFEHOLD(GATEWAY_RESTART) 着地。(2)-(3) 間で INV-25 違反（直近 admitted command・timing 履歴を失った gateway が検査なしに admit）。
- 最小修正: 「再起動した gateway は `restart_pending` を立て、`AuthorityState.safehold_reason == GATEWAY_RESTART`（または seq > 起動時 seq）を観測するまで (ii) を評価しない」。schema delta 0。

### B-M11（MEDIUM・B8）INV-27「全 `RuntimeFaultCode` member は §3.7 失敗表に行を持つ」は偽 — 6 member に行が無い（v0.2.1 fold B-10 は「7 行追加」と記録）

- 候補: 05:561-572 enum（33 member）vs 05:281-308 失敗表。機械突合結果: **`R_EPOCH_STALE_COMMAND` / `R_LEASE_INVALIDATED` / `R_DEADLINE_MISS` / `R_ENVELOPE_VIOLATION` / `R_ENVELOPE_EMPTY` / `R_CHECKPOINT_SWITCH_DISABLED`** に行なし（うち R_CHECKPOINT_SWITCH_DISABLED は遷移表 05:269 のみ、R_DEADLINE_MISS / R_ENVELOPE_VIOLATION は 05:272 で「FAULT」と無名）。INV-27 05:657・fold 表 05:755。
- 凍結: `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382`（旧 epoch command 拒否 = manager 責務 — その disposition が表に無い）。
- 再現: `python3` で enum member を抽出し 05:281-308 に grep → 6 件不在（本 report §0）。
- 最小修正: 6 行を失敗表に追加（例: `R_EPOCH_STALE_COMMAND` | CommandGateway | 拒否のみ・状態不変 | 変化なし（audit）; `R_DEADLINE_MISS` | CommandGateway | TRANSFER_TO_SAFEHOLD(DEADLINE_MISS) | HOLD; `R_ENVELOPE_VIOLATION` 同 ENVELOPE_VIOLATION; `R_ENVELOPE_EMPTY` | AuthorityManager | permit 不発行 | RESELECT; `R_LEASE_INVALIDATED` | AuthorityManager | 記録 | 個別 reason に従う; `R_CHECKPOINT_SWITCH_DISABLED` | AuthorityManager | TRANSFER_TO_SAFEHOLD(CHECKPOINT_DISABLED) | HOLD）。T-25 に反映。

### B-M12（MEDIUM・B4/B3）AuthorityManager restart: CAS SUCCESS が durable commit と同一線形化点である旨が無く、`epoch := persisted + 1` が失われた成功 CAS の epoch 値を再利用し得る（OP-6 が open として一部言及）

- 候補: 05:140「`AuthorityState` は durable」／ 05:293「durable state を読み `epoch := persisted + 1`」／ 05:711 OP-6「durable 書込みと CAS の原子性」= open／ 証明 E 05:320「epoch は成功列に沿って厳密増加」。
- 凍結: `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:270-272`（one atomic token flip・CAS/lock は D1 refinement）。
- 再現: in-memory CAS SUCCESS（L2, e+1）→ X2 へ活性通知・LEASE_ACTIVATED(e+1) 記録 → durable 書込前に crash → 再起動で persisted = e → `(SAFEHOLD(MANAGER_RESTART), e+1)`。X2 の `(L2, e+1)` は lease_id 不一致で拒否される（安全）が、epoch e+1 が 2 つの異なる状態（L2 活性 / SAFEHOLD）で使われ、audit には manager 状態に無い LEASE_ACTIVATED が残る（P5・§15 records-must-match-fact）。
- 最小修正: §3.2 に「CAS SUCCESS の線形化点 = durable commit の完了。通知・audit・permit CONSUMED はその後」（write-ahead）。OP-6 を要件文へ昇格。schema delta 0。

### B-L1（LOW・B8）`InterruptOutcome(SAFETY_STABILIZED)` の `safehold_reason` が §3.7 と §7 で不一致

- 候補: 05:269（全 InterruptOutcome → CHECKPOINT_DISABLED）vs 05:592（SAFETY_STABILIZED → `safehold_reason = SAFETY`）。解除経路が異なる（05:467 vs 05:469）。
- 凍結: `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151`（`InterruptReason` 3 member）／ D0 `:262`。
- 最小修正: 05:269 を reason 分岐（PLANNED_SWITCH / EVENT → CHECKPOINT_DISABLED、SAFETY_STABILIZED → SAFETY）に書き分ける。

### B-L2（LOW・B10）05 が参照する閾値のうち 06 `RuntimeTimeouts` に器が無いもの: kind-mismatch の連続回数 N（05:298）、inter-command 間隔の「profile 許容」（05:397）、（B-H3 採用時）safety heartbeat timeout。06:280 の「lease へ写される値」列挙は `ack_validity_s` を落としている（06:146 と 05:339 には在る）

- 凍結: `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:354-359`（timing は provisional・RT0 測定）。INV-22（05:652）「全 timeout は profile_hash 由来」。
- 最小修正: 06 `RuntimeTimeouts` に `command_kind_mismatch_max: int`・`inter_command_jitter_s`（+ `safety_heartbeat_timeout_s`）を追加し 05 `TimingBinding` へ写す。06:280 に `ack_validity_s` を追記。

### B-L3（LOW・B9/B3）gateway が admit する command 型が未定義で、`COMMAND_ADMITTED` の AuditKind が無く、lease 内の command 通番も無い（同一 lease 内の重複配送・順序入替は検出されない）

- 候補: 05:600-604 AuditKind（`COMMAND_REJECTED` / `SHADOW_COMMAND_RECORDED` はあるが CLOSED_LOOP の admitted command 記録なし）／ INV-03 05:633 = (lease_id, epoch) のみ／ 05:622 記録義務に admitted command なし。
- 凍結: `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:498`（replay 防止単位 = offer のみ）／ `:537`（runtime 記録の hash 方式 = U14 defer — 内容は定めてよい）。
- 最小修正: runtime 型 `GatewayCommand{lease_id, control_epoch, executor_id, cmd_seq, kind, payload_ref, t_issue}` を §5 に置き、INV-03 に `cmd_seq` 厳密増加を追加、AuditKind に `COMMAND_ADMITTED` を追加。

### B-L4（LOW・B3）genesis record の epoch 起点が既観測 epoch を上回ることを要求していない — store 消失後の再 genesis で epoch 再利用が可能

- 候補: 05:141「genesis record（epoch 起点 …）」／ INV-26 05:656。
- 凍結: `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382`（epoch 単調 = manager 責務）。
- 最小修正: 「genesis の epoch 起点 > AuditRecorder に残る最大 `control_epoch`（audit store は別 durable）。両 store 消失時は operator が明示的に上位値を宣言し GENESIS_RECORDED に根拠を記録」。

### B-L5（LOW・B6/B8）§6.2 B1 `validate_outcome` 失敗 → 「HOLD」に対応する CAS / reason が無く、SAFEHOLD 起点（outcome 不在）の B0-B6 手続で B1 を skip する規定が無い

- 候補: 05:489（B1 → HOLD）／ 05:239 MARK_BOUNDARY_WAIT は report ref を添えるだけで issues 空を要求しない／ 05:469「SAFEHOLD からの新規起動（§6.2 B0 から）」。
- 凍結: `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:374`（`validate_outcome`）。
- 最小修正: 「B1 失敗 = `S_BOUNDARY_WAIT` に留まり（既に SafeHold）候補評価を行わず B5 NO_CHAIN 経路へ」／「SAFEHOLD 起点では producer invocation 不在ゆえ B1・offer 検証を skip（`InitializationRecord.handoff_validation_report_ref = null`）」を明記。

### B-L6（LOW・B4）Orchestrator 二重生存（旧 instance の遅延復帰）時、敗者側 executor（ACK 済・未活性）への通知が未定義

- 候補: 05:276「Orchestrator は無状態ゆえ新 instance が B0 から再開」／ 05:183 同一 expected の複数 permit。CAS 条件 1 で高々 1 つ成功する点は PASS（証明 D）。
- 凍結: `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:272`。
- 最小修正: 「CONFLICT / VOID となった permit の ack 先 executor へ `PERMIT_VOIDED` を通知し、executor は proposal を破棄する」を §3.7 に 1 文。

## 3. PASS 項目（checklist id 別・根拠行）

- **B1 PASS（部分）**: tuple 全体 CAS（05:130-138・05:219 条件 1）／ 旧 epoch 拒否 = CAS 同一線形化点の**規範文**（05:32・05:233・INV-03 05:633）／ ReadinessAck → CommitPermit → CAS の順序（05:31・05:265）／ permit one-shot（05:182・証明 D 05:318・INV-04）／ 旧 owner へ事前通知なし（CAS は manager 内部）。**未 PASS**: B-H1（cache 読み）・B-M4（ACK 束縛の抜け）。
- **B2 PASS**: `out(t)` の全域・排他（05:448-451・証明 B 05:314・INV-10）／ 初期状態 SAFEHOLD(INITIAL)（05:141）／ CAS 線形化点で (ii) 集合を空に（05:234・05:455）／ gateway 起動出力 = SafeHold（05:275・INV-25）／ gateway 停止中の物理 failsafe は OP-17（05:721）で loud に外出し。**注記**: B-M8（SafeHold の実体）・B-M1（INV-24 の文言）。
- **B3 PASS**: offer 検証 = CAS 前・消費 = CAS 内（05:241-247・05:231 `∪ {consume_offer_id}`・証明 C 05:316・INV-05/06）／ permit 失効 = 条件 2（05:220）／ ACK 失効 = 条件 3（05:221）・INV-07 `ack.valid_until ≥ permit.issued_at`／ 二重 permit = 条件 1 で高々 1 SUCCESS（05:232・T-01）／ T-04・T-05。**注記**: B-L3（lease 内 command replay）・B-L4（genesis）。
- **B4 PASS（部分）**: 新 executor の CAS 後 crash → EXECUTOR_LOST | HEALTH_CONFIRM_TIMEOUT → SAFEHOLD・旧 owner 不復活（05:291・05:267・証明 E 05:320・INV-11・T-07）／ 転送窓内の safety override（05:294・INV-18・T-08）／ permit 発行後の Orchestrator 喪失（05:276・05:308）／ manager restart → SAFEHOLD(MANAGER_RESTART)・durable 不読 = 起動拒否（05:274・05:293・INV-26）。**未 PASS**: B-M10（gateway restart の enforcing 規則）・B-M12（durable commit）・B-L6。
- **B5 PASS（部分）**: 活性 lease はちょうど 1（05:133・05:369）／ profile_hash / authority_decision_ref / initialization / accepted_envelope / timing の束縛（05:369-385・05:387-391）／ 変更 = 新 lease（05:389・06:279）／ 無効化 trigger 列挙（05:429）／ SHADOW = actuation DISABLED（05:419・INV-09・T-11）／ CLOSED_LOOP = `granted == True` 必要条件 + 外部 gate（05:224・INV-08・05:691・06:377）。**未 PASS**: B-M5（条件 6 の profile_hash）・B-M7（06:281 の mid-lease 無効化）。
- **B6 PASS（部分）**: INV-21（05:651）／ InterruptOutcome = 受理 + HOLD（05:269・05:481-483・05:591）／ 再選択 = 新 BeliefRef + 明示 now（05:490・05:494・05:504）／ `RuntimeAssessmentRecord` = 非 certified（05:513-528）。**未 PASS**: B-H2（manager 層の前提条件欠落）。
- **B7 PASS（部分）**: (i) 最優先・ack を待たない（05:449・05:454・INV-18）／ HOLD 解除権の定義（05:464-472）／ command deadline → R_DEADLINE_MISS（05:396）／ 条件 9・10（05:227-228）。**未 PASS**: B-H3（ISL heartbeat 喪失）・B-M2（reason laundering）・B-M3（SAFE_STOP 出力）・B-M9（D0 §G handoff deadline）。
- **B8 PASS（部分）**: `ProducerOutcome` 不変（05:577・INV-20・T-19）／ outcome × disposition 表が Terminal 4 class + Interrupt 3 reason + outcome 無しを覆う（05:583-593）／ `FailClosedAction` 写像（05:595）／ fault は常に disposition を伴う（05:578）。**未 PASS**: B-M11（INV-27 偽）・B-L1・B-L5。
- **B9 PASS（部分）**: AuditKind が permit issue/consume/void・CAS_ATTEMPT・LEASE_ACTIVATED/INVALIDATED・HEALTH_*・SAFETY_OVERRIDE・FAULT・DISPOSITION・GATEWAY_RESTART・GENESIS を持つ（05:600-604）／ record は `control_epoch` + `lease_id` を持つ（05:612-613）／ hash 方式 = U14 defer を正直に記載（05:624・OP-5）／ EP 分離（05:625）。**未 PASS**: B-L3（COMMAND_ADMITTED）。
- **B10 PASS（部分）**: rate / hold は D1.1-B と等値（05:395・INV-12 05:642・T-14）／ ActionHold の再生 + deadline（05:396）／ 全 timeout は profile 由来・数値定数なし（INV-22 05:652・05:339-344・06:145-151）。**未 PASS**: B-L2（器の無い閾値）・B-M6（WAIT）・B-M8。

## 4. 主張しないこと

- 本 report は gate / two-key / Rs 裁定 / freeze を主張しない。凍結 4 file 不変（11/11 PASS）。
- finding は 08 計画 §5 の 3 lens 反証を**他 reviewer が**行う前の独立確定版。severity は本 reviewer の評価。
