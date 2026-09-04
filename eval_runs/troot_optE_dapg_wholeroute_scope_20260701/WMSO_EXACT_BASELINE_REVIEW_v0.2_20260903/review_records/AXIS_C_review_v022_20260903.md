# AXIS C — deployment / industrial profile 独立レビュー（対象 = v0.2.2 REVIEW CANDIDATE）

- reviewer = REVIEWER C（lens: 実 cell の commissioning / functional-safety engineer）・別 context・authority 無し・凍結物へ非接触
- 実施 = 2026-09-04 15:57 UTC（`date -u` 実測）／ 2026-09-05 00:57 JST
- 対象（content で引く。file 名の v0.2 は label・header line 1 が v0.2.2）:
  - 06 `$D/WMSO_EXACT_BASELINE_REVIEW_v0.2_20260903/06_WMSO_INDUSTRIAL_PROFILE_v0.2_REVIEW_CANDIDATE_20260903.md`（474 行・sha256 実測 `c0faa7bf99c348295b0012f509065556d525991687b77f50168310d2755a0288`）— primary
  - 05 `…/05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md`（893 行・sha256 実測 `909f24edf35e7a8f91680430e201ed96989523cd13bfcbb478f3e3a0ad74d348`）§3.4 / §4 / §5.4 / OP-19 / §13
  - 04 `…/04_EVIDENCE_POLICY_IMPACT_ASSESSMENT_20260903.md`（76 行・sha256 実測 `e85490d755129adefacf887108c6318ab1cf0557f84eb80b5b70c648521d6c85`）
- 独立手続（08 §1 項 6）: 本 report の finding は他軸の finding・`AXIS_C_review_v021.md`・`PC_C_blind.md` を**読まずに**確定した。06 §11 / 05 §13 の fold 表は読み、fold 済み finding は再報告しない（fold の不完全は指摘する）。
- `$D` = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701`。全 `file:line` は本 session で `sed -n` 実測。

## 0. 共通前提の実施記録

### 0.1 pin 再測（素の bash）

```
$ bash $D/WMSO_EXACT_BASELINE_REVIEW_v0.2_20260903/verify_exact_baseline_pins.sh
PASS  D1.1-A DESIGN v2.11.2 (worktree)  00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff
PASS  EvidencePolicy v1.9 md (worktree)  c474acea7c58acc22050c2ad9944fd45a18f5c76967964b42d11922e28fa27e7
PASS  EvidencePolicy v1.9 json (worktree)  e63176af9bc3a246b1c32db369ec59f8d09a4c96c381bb03a3a6024bd9811c6e
PASS  D1.1-B DESIGN v13 (worktree)  5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6
PASS  D1.1-A DESIGN git blob id (HEAD)  1353430228a90ad36dd190a9359cd81da52e8242
PASS  D1.1-B DESIGN git blob id (HEAD)  ebe8154abf2461a6b24db05728b20e5cee949fb2
PASS  D1.1-A DESIGN sha256 of blob 135343…  00192d20…
PASS  D1.1-B DESIGN sha256 of blob ebe815…  5a1874d3…
PASS  D1.1-A DESIGN at frozen commit 54f90a7d  00192d20…
PASS  D1.1-B DESIGN at frozen commit 07250f4a  5a1874d3…
PASS  evidence_policy_definition_hash (embedded command)  e7ca43093084c167a209b008533a66d26a1fd3223d2a3c11274d28306c3ff803
policy_semver=1.9.0   HEAD=297c850bb31a61b56d5f2def9dd616a7c254f6d2 branch=claude/v0-2-design-candidates-snqbmy   EXIT=0
```
= **11/11 PASS**。

### 0.2 機械検査（読む前に実施）

```
check_review_candidate.py 06 …            citations=59  FAIL=0 WARN=23
check_review_candidate.py 05 … --runtime  citations=151 FAIL=0 WARN=10
check_review_candidate.py 04 …            citations=18  FAIL=0 WARN=7
```
FAIL = 0 ⇒ 読解に進んだ。WARN は heuristic C2（06 §12 項 16 の説明と一致）。

### 0.3 SHA256SUMS 突合

`SHA256SUMS.txt`（mtime 09-04 01:51）の 04/05/06 の値（`4da8491b…` / `f62b0c30…` / `852d0572…`）は現 file（mtime 09-04 15:41・v0.2.2）の実測値と**不一致**（v0.2.1 の値）。⇒ CD-11 に記録。

### 0.4 手動 sed 検証した凍結引用（≥ 15）

B:23 / :24 / :40 / :52 / :65-66 / :75-76 / :81 / :96-99 / :125-127 / :132 / :133 / :138 / :185 / :255 / :289 / :313 / :332 / :337 ／ A:39 / :62 / :142 / :146 / :147 / :151 / :159 / :168 / :218 / :306 / :323 / :346-352 / :354 / :372-373 / :377-378 / :380 / :381 / :382 / :385 / :498 / :506 / :521 / :537 / :570 ／ EP:101 / :148 / :154 / :155 / :156 / :163 ／ JSON:5 / :213 ／ D0:270-274 / :317-320 / :354-355 ／ C3:5 / :65 ／ charter:13 / :129 ／ BCS:59 ／ D11C custody:36-38 ／ D11B freeze:39 ／ skill ownership:9 ／ state.md:91 ／ HANDOFF_pQ:11 / :68 — 全て 06 / 05 / 04 の引用内容と一致した（不一致 0）。

### 0.5 陽性対照（10_ record の注入 4 欠陥）が実 06 に無いことの確認

- PC-06-E（action bounds field）: 06 の型 block（:64-221）に `bounds` を表す field 無し（grep `bounds` = 語彙行 :19/:30/:235/:266/:271/:367/:419/:459 のみ）✓
- PC-06-F（rate ≤）: 06:237 「**等値**」・PT-01（:363）「narrow = `P_RATE_MISMATCH`」・05 INV-12（:686）✓
- PC-06-G（`requires_safety_layer_health` False 可）: 06:117 / :244 「True 必須」・PT-06 ✓
- PC-06-H（SAFE_STOP → HOLD 緩和）: `EscalationTarget = HOLD | SAFE_STOP`（06:69）が触れる 05 の既定は NO_CHAIN（05:275）・HEALTH_FAIL（05:271）とも HOLD。05 が SAFE_STOP を固定する経路（05:279 `R_SAFETY_LAYER_LOST`・:300 durable 不読・:632 INVALID_STATE 未解消）に profile field は無い ✓
⇒ 4 件とも実 doc に不在。以下の finding はいずれも注入欠陥の再報告ではない。

## 1. 判定

**HOLD**（08 §5: 未反証の HIGH が残る）。HIGH = 4（CD-01〜04）・MEDIUM = 7・LOW = 7。全 finding は zero frozen-schema delta の最小修正案を持つ（修正先は 06 / 05 の runtime・deployment 層の新語のみ）。凍結 4 file には何も要求しない。

## 2. Checklist 別の PASS / 未達

| id | PASS した項目（根拠） | 未達（finding） |
|---|---|---|
| C1 | action-space bounds field 無し（06:235・PT-05）／ rate・hold・control_mode・binding hash = **等値のみ**（06:237-239・PT-01/02・05 INV-12 :686 — R1 のとおり narrow は欠陥扱い）／ initiation = AND のみ（06:129-130・05:537）／ freshness `p ≤ f`（06:241・PT-04）／ escalation = SAFE_STOP 側のみ（06:69/:180-184・05:271/:275 の既定 HOLD）／ 各緩和に P_* code（06:355） | **CD-01**（timeout に上限・関係式が無く 05 の安全機構を無効化できる profile が P_* = 0 で通る）／ **CD-07**（restriction 項が空・無際限でも通る・:266 の over-claim）／ CD-05（SCRIPTED/WAIT の rate 出所） |
| C2 | 4 項の出所（06:271-274 ↔ 05:429-434）／ 空 = fail-closed 二重化（`P_ENVELOPE_EMPTY` :259・`R_ENVELOPE_EMPTY` 05:380・CAS 条件 7 :228）／ D1.1-B bounds は `tensor_binding_hash` 参照のみ（06:30・:235）／ frame = `base_frame_ref` / `tool_flange`・`P_FRAME_MISMATCH`（06:76/:105/:111/:263） | CD-07（`ee_force_max` / `joint_torque_max` は admission で評価不能な監視量）／ CD-18（workspace 項が setpoint 点評価・tool 形状無し） |
| C3 | `CommitPermit.profile_hash`（05:178）・`ActiveAuthorityLease.profile_hash`（05:403）・CAS 条件 2 で permit ↔ lease 等値（05:223）・§3.4 (f)（05:184）／ 変更 = 新 lease・in-place 無し（05:413・06:285）／ 反循環（06:226: 自己 hash・lease id・epoch・permit id を preimage に置かない）・`P_SELF_HASH`・WCJ + B-declared 規約継承（06:225 ↔ A:168・B:24） | **CD-04**（`predicate_refs` / `evaluator_ref` / `tcp_offset_ref` が content hash 無しの名前参照 ⇒ 内容が profile_hash 不変のまま差し替わる） |
| C4 | CellIdentity に識別・版（:72-79）／ calibration ref に sha + 期限（:167-172）／ gateway config ref に sha（:174-177）／ health check `fail_closed` True 必須（:165/:255）／ BEFORE_PERMIT の結線（05:184 (a)） | **CD-02**（05 §5.4 が profile に委ねる clearance / GATEWAY_CONFIG_MATCH を 06 が必須化していない）／ CD-09（controller/firmware/tool identity の permit 時確認が必須集合に無い）／ CD-08（kind が自由文字列で検査が機械化不能） |
| C5 | 8 kind とも EP md / JSON に 0 hit（本 session grep）・frozen に `P_*` / `R_*` token 0（grep）／ EP grade 語 不使用（06:337）／ certification 非影響（06:337 ↔ A:39）／ 未認証範囲の明示（06:389・OPP-5/6） | **CD-03**（validity_rule と fault_injection の per-code 要求に執行 check が無い）／ CD-16（record と audit の join に lease_id が無い） |
| C6 | 合成語彙は §7 の除外文脈のみ（word-boundary grep :246/:346-348/:375/:418/:424）／ court への pointer（custody:36-38・freeze:39・ownership:9 = sed 一致）／ 両腕 True は cell 事実であって 2 executor ではない（06:349 ↔ 05:750） | — |
| C7 | 3 軸表（06:52-58）・§0（:20-23）・§9 項 4/5（:386-387）／ `LeaseMode` を EP profile 名と分離（05:345/:451）／ 04 §5 | — |
| C8 | frozen validator は frozen definition で呼ばれ、profile conjunct はその後の別 conjunct（05:535-537）／ `required_control_resources` に触れる field 無し（06:38/:242）／ freshness は min のみ（05:356・06:134）／ FreshnessPolicy 迂回経路無し | CD-06（handoff 由来 ownership が cell の資源宣言で bound されない） |
| C9 | 凍結 E_* 95 code（grep 実測）と `P_*`（06:355・26 code）は接頭辞で非交差・frozen 4 file に `P_`/`R_` 0 hit／ validation・test plan は宣言のみ（06:7・:351・:384） | CD-14（`P_INTRINSIC_OVERRIDE` 到達不能・重複） |
| C10 | header に版・pin・CLOSED（06:1-8）／ §9 境界／ §10 open ≠ 0／ §11 fold-map／ §12 anchors 16 件（引用 sed 一致） | **CD-11**（fold-map が存在しない `11_*` を根拠に引く・SHA256SUMS 陳腐化・全 verdict が起草者自己検証） |

## 3. Findings（型 = {id, 軸, severity, 候補 doc:line, 凍結 file:line, 再現, 最小修正}）

### CD-01 ［C1］ HIGH — `RuntimeTimeouts` に上限・関係式が無く、05 の安全機構を無効化する profile が `P_*` = 0 で受理される

- 候補 doc:line: 06:145-157（`RuntimeTimeouts` 12 field）・06:252-253（唯一の検査 = `> 0`・`command_deadline_s ≥ 1/action_rate_hz`）・06:266（「広げる」経路の網羅 (i)-(ix) に timeout 経路が無い）・05:363（`safety_heartbeat_timeout_s`）・05:420（「無期限 ZOH を『安全』と見なさない」）・05:488 (i′)・05:703 INV-29・05:696 INV-22。
- 凍結 file:line（欠落の根拠）: D0:318「missed heartbeat ⇒ consumers must **not** assume safety alive」— 巨大な `safety_heartbeat_timeout_s` は「alive を仮定する」ことと等価。frozen 側に timeout は無い（06 の「frozen 意味論を狭める」検査の**外**にあるが、05 の runtime 安全不変量を profile が弱める経路）。
- 再現（反例 profile）: `safety_heartbeat_timeout_s = 1e9`・`command_deadline_s = 1e9`・`permit_ttl_s = 1e9`・`ack_validity_s = 1e9`・`decision_max_age_s = 1e9`・`inter_command_jitter_s = 1e9`。全 field > 0（`P_TIMEOUT_NONPOSITIVE` 不発火）・`1e9 ≥ 1/action_rate_hz`（`P_DEADLINE_BELOW_PERIOD` 不発火）・他の P_* は timeout を見ない ⇒ 受理。効果: (a) ISL heartbeat 喪失後も (i′) が発火せず (ii) が学習 command を出し続ける（B2-01 / B-H3 の fold が無効化）(b) 直近 admitted setpoint の ZOH が実質無期限（05:420 が「安全でない」と明記した状態）(c) permit の失効（P4「失効付き」）・ACK の鮮度・AuthorityDecision の age 検査が空文化。
- 最小修正（zero frozen delta）: (1) 06 §3 追加検査 `P_TIMEOUT_ORDER`: `safety_heartbeat_timeout_s ≤ command_deadline_s`（LEARNED / SCRIPTED）／ `inter_command_jitter_s < 1/action_rate_hz`（LEARNED）／ `decision_max_age_s ≤ permit_ttl_s ≤ boundary_dwell_s`／ `ack_validity_s ≤ boundary_dwell_s`。(2) §6.1 `MIN_FAULT_INJECTION` に timeout 駆動の fault（`R_DEADLINE_MISS` / `R_SAFETY_LAYER_LOST` / `R_TIMING_VIOLATION` / `R_PERMIT_EXPIRED` / `R_ACK_TIMEOUT` / `R_HEALTH_CONFIRM_TIMEOUT` / `R_BOUNDARY_DWELL_EXCEEDED`）を追加 — 同一 profile_hash の下で各 timeout が commissioning で実際に発火した証拠を要求する（1e9 s の timeout は試験不能ゆえ事実上 bound される）。(3) §3 の網羅 (x) として「timeout を伸ばす」を列挙し、絶対上限は RT0 / Rs（05 OP-10）へ carry する OPP を追加。

### CD-02 ［C4 / C1］ HIGH — 05 §5.4 が profile に委ねる clearance 定義・`GATEWAY_CONFIG_MATCH` を 06 が必須化しておらず、`clearance_roles = ()` の profile が受理される

- 候補 doc:line: 06:185（`clearance_roles` = 「**追加の** role」・任意 tuple）・06:254（`P_HEALTHCHECK_MISSING` の必須 kind に `GATEWAY_CONFIG_MATCH` 無し）・06:355（clearance に関する P_* 無し）／ 05:508（SAFE_STOP「profile が定義する operator / health-check clearance（doc 06）」）・05:509（CHECKPOINT_DISABLED「profile が定義する operator clearance + 再観測」）・05:511（GATEWAY_RESTART「`GATEWAY_CONFIG_MATCH` health check の pass + profile が定義する clearance role」）・05:231（CAS 条件 10「該当する clearance record が存在」）・05:513（集合 = {SAFETY, SAFE_STOP, CHECKPOINT_DISABLED, MANAGER_RESTART, GATEWAY_RESTART}）。
- 凍結 file:line: D0:320（`stabilized_post_action_state` = 復帰可否の判断材料 — 復帰権限の定義が前提）・D0:273-274（fail-closed = producer retains + safe-stop。「解除できる者」が未定義なら fail-closed は永久 HOLD になる）。
- 再現: profile に `clearance_roles = ()`・`health_checks` = {SAFETY_LAYER_HEARTBEAT, CONTROLLER_LIVENESS, ENVELOPE_READBACK} のみ ⇒ 全 P_* = 0 で受理。運転中 NO_CHAIN → `on_no_chain = SAFE_STOP` → `S_SAFEHOLD(SAFE_STOP)`。CAS 条件 10 の「該当する clearance record」は profile が何も定義しないため (a) 厳密読み = 何も該当せず永久 HOLD（可用性欠陥）(b) 緩い読み = 任意の record が該当（誰でも解除 = 拡張）。仕様はどちらかを決めていない。GATEWAY_RESTART は `GATEWAY_CONFIG_MATCH` check が profile に無いため 05:511 の前提が満たせず同型。
- 最小修正（zero frozen delta）: 06 §3 追加検査 `P_CLEARANCE_ROLE_MISSING`: ∀ reason ∈ {SAFE_STOP, CHECKPOINT_DISABLED, MANAGER_RESTART, GATEWAY_RESTART}: `∃ (reason, role) ∈ clearance_roles`（SAFETY は ISL clearance が主で、profile role は AND の追加 — 06:185 のとおり）。`P_HEALTHCHECK_MISSING` の必須集合に `GATEWAY_CONFIG_MATCH`（stage ∈ {BEFORE_PERMIT, BOTH}）を追加。05 §5.4 に「clearance record = {safehold_reason, role, operator_ref, profile_hash, t}・CAS 条件 10 の『該当』= `record.reason == current.safehold_reason ∧ record.role ∈ profile.clearance_roles[reason] ∧ record.profile_hash == permit.profile_hash`」を明文化（`CLEARANCE_RECORDED` の payload 型）。

### CD-03 ［C5］ HIGH — `DeploymentEvidencePolicy` が宣言する validity・fault-injection per-code 要求に執行 check が無い（存在検査のみ）

- 候補 doc:line: 06:257（`P_EVIDENCE_UNBOUND` = 「required kinds が profile_hash に対し**存在**」）・06:322-324（`validity_rule = ALL_REQUIRED_VALID_AT_PERMIT_ISSUE`）・06:309（`DeploymentEvidenceRecord.valid_until_iso8601`）・06:321/:329（`fault_injection` per-code・`MIN_FAULT_INJECTION` 8 code）・06:357（第 2 評価点の再評価 = `P_CALIBRATION_EXPIRED` / `P_EVIDENCE_UNBOUND` / `P_EXPECTATION_UNCERTIFIED` のみ）・05:184 (b)。
- 凍結 file:line: EP:154（per-component 意味論「不在 = UNKNOWN(0) = 失格」— EP 側は component 単位で不在を失格にするが、06 の deployment policy は kind 単位の存在で済ませ、record の失効と subject 単位の欠落を見ない）・A:354（`granted == True` は必要条件 — profile 由来条件を**足す**と 06:383 が主張するが、足した条件が空文なら足していない）。
- 再現: (1) `SAFETY_LAYER_ACCEPTANCE` record の `valid_until_iso8601 = "2025-01-01"`（失効）— `P_EVIDENCE_UNBOUND` は存在のみ ⇒ 通過。`validity_rule` を評価する code が無い。(2) `FAULT_INJECTION_RESULT` を 1 件（`subject_ref = "R_OFFER_REUSED"`）だけ登録 ⇒ kind は存在 ⇒ `P_EVIDENCE_UNBOUND` 不発火。`MIN_FAULT_INJECTION` の残り 7 code は未試験のまま CLOSED_LOOP_AUTHORITY permit の前提 (b) を通る。(3) `P_EVIDENCE_UNBOUND` は登録時表（:257）と第 2 評価点（:357）の両方に現れるが、登録時にどの lease mode の required 集合を使うか未定義。
- 最小修正（zero frozen delta）: `P_EVIDENCE_UNBOUND` を (kind × subject) 単位に定義: `CALIBRATION_RECORD` は ∀ `calibration_id`、`HEALTH_CHECK_RUN` は ∀ `check_id`、`FAULT_INJECTION_RESULT` は ∀ `req ∈ policy.fault_injection` with `must_be_exercised_before ⊑ proposed_lease.mode`: ∃ record（kind・`subject_ref == req.runtime_fault_code`・`profile_hash` 一致）。新 code `P_EVIDENCE_EXPIRED`（required record の `valid_until_iso8601 < t_wall(permit 発行)`）を第 2 評価点に追加。登録時 = `MIN_SHADOW` 集合、permit 時 = mode 別集合と明記。`FaultInjectionRequirement.runtime_fault_code ∉ 05 RuntimeFaultCode` ⇒ `P_FAULT_CODE_UNKNOWN`。

### CD-04 ［C3 / C1］ HIGH — `predicate_refs` / `evaluator_ref` / `tcp_offset_ref` が content hash 無しの名前参照で、SAFETY_RESTRICTION 項と health check の内容が profile_hash 不変のまま差し替わる

- 候補 doc:line: 06:116（`SafetyRestrictionSet.predicate_refs: tuple[str,...]`）・06:163（`HealthCheckSpec.evaluator_ref: str`）・06:98（`ToolPayloadSpec.tcp_offset_ref: str`）・06:14（「content-addressed artifact」）・06:285（「活性 lease の profile を in-place で差し替える経路は無い」）・06:274/:434（SAFETY_RESTRICTION 項 = gateway predicate）。対照: `ZoneRef.geometry_sha256`（:103）・`CalibrationRef.artifact_sha256`（:171）・`GatewayConfigRef.artifact_sha256`（:177）・`ExtraInitiationConjunct.schema_hash + payload_canonical_json`（:124-125）は content 束縛済。
- 凍結 file:line: B:23（反循環規則の趣旨 = 「preimage に何を置くか」で identity を決める content-address 規律）・A:151（frozen `InitiationSpec` = {schema_ref, **schema_hash**, **payload_canonical_json**} — 述語は名前でなく内容で束縛する frozen pattern。06 は `ExtraInitiationConjunct` でこれに倣うが `SafetyRestrictionSet` では倣わない）・B:255（凍結側は content-addressed store を**要求していない** ⇒ resolver が名前を内容へ写す規約は契約外・保証無し）。
- 再現: profile P（`predicate_refs = ("keepout_pred_v1",)`）を登録・lease 活性。resolver 側で `keepout_pred_v1` の内容を「常に admit」へ編集。`profile_hash` 不変・lease 不変・P_* / R_* いずれも発火しない・gateway は変更後の述語で admit する。健康検査 evaluator も同型（常に True を返す evaluator へ差し替え可）。
- 最小修正（zero frozen delta）: `SafetyRestrictionSet` に `predicate_sha256: tuple[str, ...]`（`predicate_refs` と同長）、`HealthCheckSpec` に `evaluator_sha256: str` を追加。permit 発行時（第 2 評価点）に resolver が返す内容の sha256 と等値検査 — 不一致 = `R_PROFILE_MISBOUND`；gateway は評価前に等値を再確認し不一致 = 評価不能 = FALSE。`tcp_offset_ref` は `calibration_refs` 内の `kind == "tcp"` の `calibration_id` へ解決必須（`P_TCP_REF_UNRESOLVED`）。

### CD-05 ［C1 / C3］ MEDIUM — `BindingExpectation` が SCRIPTED / WAIT で「唯一の source」と自己矛盾し、かつ 05 側に lease admission の消費者が無い

- 候補 doc:line: 06:188（「SCRIPTED / WAIT では唯一の source」）・06:190（`tensor_binding_hash: LEARNED ⇔ 非 null`）・06:237（`P_RATE_MISMATCH` = 「`==` TensorBindingSpec の値」）・06:357 規則 (1)（「評価不能 = 違反」）・06:19（「制御周波数・hold の変更権（等値のみ）」）・05:184 / 05:222-232（permit 前提・CAS 条件に `binding_expectations` への言及なし — 05 全文 grep で `BindingExpectation` 0 hit）。
- 凍結 file:line: B:289（SCRIPTED / WAIT は tensor_binding slot = EXPLICIT_NONE ⇒ TensorBindingSpec が存在しない）・A:62（`ControlMode` に SCRIPTED_SEQUENCE / WAIT）。
- 再現: (a) SCRIPTED skill の expectation `{tensor_binding_hash = None, action_rate_hz = 50}` — `P_RATE_MISMATCH` の比較対象が無い。規則 (1) を適用すると**全 SCRIPTED expectation が違反** = SCRIPTED skill を持つ profile が全て登録不能；適用しないなら profile が SCRIPTED の rate を自由に決める（06:19 と矛盾・単調性検査の外）。(b) 05 §3.4 は `proposed_lease.skill_action_id` が profile の expectation に含まれることを要求しないため、当該 cell で commissioning されていない certified skill でも lease が成立する — `BindingExpectation` は登録時の等値検査以外に効果が無い。
- 最小修正（zero frozen delta）: (a) 06 §3 行を「`P_RATE_MISMATCH` / `P_HOLD_MISMATCH` は `tensor_binding_hash ≠ null` のときのみ評価。null の expectation は `policy_rate_hz` / `obs_sampling_rate_hz` / `action_rate_hz` / `hold` = None 必須（非 null = `P_INTRINSIC_OVERRIDE` の実用途）」と修正し、SCRIPTED の timing は `command_deadline_s` のみで扱う旨を 05 §4.2 と同期。(b) 05 §3.4 前提 (g): `∃ e ∈ profile.binding_expectations: e.skill_action_id == proposed_lease.skill_action_id ∧ e.tensor_binding_hash == proposed_lease.timing.tensor_binding_hash ∧ e.control_mode == proposed_lease.control_mode`、違反 = `R_PROFILE_MISBOUND`。

### CD-06 ［C8］ MEDIUM — handoff 由来の `ownership` が cell の `ResourceAvailability` で bound されない

- 候補 doc:line: 05:414（「`ownership` は frozen `HandoffOffer.ownership` をそのまま束縛 … SAFEHOLD からの初回起動では … profile が宣言する cell の資源可用性から構成する」）・05:763 OP-3・06:137-142・06:242（`ResourceAvailability` = offered 集合の宣言）・06:286（`lease.ownership`（SAFEHOLD 起動時）← `ResourceAvailability`）。
- 凍結 file:line: A:380（`required ⊆ offered` の bool 包含 — offered の真偽は validator の外）・A:506（`HandoffOffer.ownership`）。
- 再現: cell の profile が `control = {ee_left: True, ee_right: False, …}`。producer（左腕 skill）が `HandoffOffer.ownership.control = {ee_left: True, ee_right: True, …}` を出す（producer の bug / 誤設定）。消費者 skill が `ee_right` を要求 ⇒ `required ⊆ offered` 通過・05 / 06 のどの検査も profile の宣言と offer を突合しない ⇒ 存在しない右腕への lease が成立。profile の資源宣言は genesis 起動時のみ効く。
- 最小修正（zero frozen delta）: 05 §3.4 前提に `proposed_lease.ownership.control ⊆ profile.resource_availability.control ∧ (proposed_lease.ownership.contact ⇒ profile.resource_availability.contact)` を追加（違反 = `R_PROFILE_MISBOUND`）。06 §3 の `required_control_resources` 行に「全 lease の offered ⊆ 宣言」を追記。

### CD-07 ［C1 / C2］ MEDIUM — restriction 項が空・無際限でも `P_*` = 0 で通り、06:266「(v) だけは契約層で判定できない」は over-claim。`ee_force_max` / `joint_torque_max` は admission で評価できない監視量

- 候補 doc:line: 06:82-90（`ControllerEnvelope` — 正値・定格との照合検査なし）・06:109（`zones` 空許容）・06:115-116（`restriction_ids` / `predicate_refs` 空許容）・06:258（`P_ENVELOPE_SHAPE` = tuple 長のみ）・06:266（「**(v) だけは**契約層では真偽を判定できない」）・06:272（CONTROLLER 項に force / torque）・06:279（「変換不能 = 拒否」）・05:433・05:436（「評価不能 = FALSE」）・06:320（`CONTROLLER_ENVELOPE_MEASUREMENT` = 存在のみ）。
- 凍結 file:line: D0:317（`FORCE_LIMIT` は ISL の `SafetyDecision` = **監視**側の決定であって command admission ではない）・D0:319（preemption acts first）。
- 再現: (1) `joint_velocity_max = (1e6,…)`・`ee_speed_max = 1e6`・`zones = ()`・`predicate_refs = ()` の profile: `P_ENVELOPE_SHAPE`（長さ OK）・`P_ENVELOPE_EMPTY`（空でない）・`P_RESOURCE_UNATTESTED`（record 存在）全て不発火 ⇒ 受理。AcceptedEnvelope の profile 3 項は全 command を admit（deployment envelope が無いのと同じ）。(2) `ee_force_max = 50 N`: EE target command から接触力は導出できない ⇒ 05:436 に従えば全 command が FALSE（fail-closed だが運転不能）、従わなければ gateway が黙って skip（未規定の非執行）。
- 最小修正（zero frozen delta）: (a) 06:266 を「契約層で真偽を判定できないのは (v) に限らず、`ControllerEnvelope` の値・zone 幾何・predicate 内容・tool 質量/CoM の全て（物理事実）であり、`P_*` は**形と単調性**のみを検査する」と正直化し OPP-5 の範囲を広げる。(b) `ControllerEnvelope` を admission 評価可能 {joint_velocity/acceleration/jerk_max, ee_speed_max} と監視限界 {ee_force_max, joint_torque_max}（ISL / controller に渡す宣言値・AcceptedEnvelope 項ではない）に分け、§4 の CONTROLLER 項から後者を外す。(c) 形の検査 `P_ENVELOPE_NONPOSITIVE`（全上限 > 0）・`P_WORKSPACE_EMPTY`（`kind = reach_limit` の zone ≥ 1）を追加し、`CONTROLLER_ENVELOPE_MEASUREMENT` の artifact に測定値 schema を与え `profile ≤ measured` を登録時に検査（`P_ENVELOPE_EXCEEDS_MEASURED`）。

### CD-08 ［C4 / C1］ MEDIUM — 自由文字列 kind により検査が機械化不能（`P_CALIBRATION_MISSING` の「belief を担う camera 系」は profile から導出不能）

- 候補 doc:line: 06:170（`CalibrationRef.kind: str` "tcp" | … | "..."）・06:256（必須 kind = 「`tcp` + belief を担う camera 系」）・06:104（`ZoneRef.kind: str`）・06:90 / :110（`representation: str`）・06:313（`runtime_fault_code: str`）・06:227（strict codec を継承すると主張）。
- 凍結 file:line: A:385（enum strict・unknown = `E_ENUM_UNKNOWN` — 06 が継承を主張する codec 規律は closed enum を前提とする）・B:31（`FeatureSource = SEMANTIC_OBS | SEMANTIC_ACTION | BELIEF` — どの sensor が belief を担うかは binding にも profile にも無い）。
- 再現: `calibration_refs = [{kind: "tcp"}, {kind: "camera_extrnsic"}]`（typo）⇒ 「camera 系」の判定規則が無いため通過も拒否も定義不能。`representation = "workspace"` を `ControllerEnvelope` に与える ⇒ 評価不能 = FALSE（fail-closed だが登録時に検出されない）。
- 最小修正（zero frozen delta）: closed enum `CalibrationKind {TCP, CAMERA_EXTRINSIC, CAMERA_INTRINSIC, FORCE_SENSOR}`・`ZoneKind {KEEP_OUT, REACH_LIMIT, HEIGHT_BAND}`・`Representation {JOINT_SPACE, WORKSPACE}`（`representation` の既定値を型で固定し free field を廃止）。`REQUIRED_CALIBRATION_KINDS(control_mode)` = LEARNED: {TCP, CAMERA_EXTRINSIC, CAMERA_INTRINSIC}／ SCRIPTED・WAIT: {TCP} を §3 に規範化。`runtime_fault_code` は 05 enum 参照（CD-03 の `P_FAULT_CODE_UNKNOWN`）。

### CD-09 ［C4］ MEDIUM — controller / firmware / tool の **identity** を permit 時に確認する health check が必須集合に無い・`ENVELOPE_READBACK` の意味が未定義

- 候補 doc:line: 06:67（`HealthCheckKind` に CONTROLLER_IDENTITY 無し。TOOL_IDENTITY / CALIBRATION_VALID / GATEWAY_CONFIG_MATCH は任意）・06:75-78（`robot_serial_ref` / `controller_firmware_ref` は宣言のみ）・06:254（必須 = SAFETY_LAYER_HEARTBEAT / CONTROLLER_LIVENESS / ENVELOPE_READBACK）・05:158（`envelope_readback_ok` = **executor** の読み戻し — 06 の `ENVELOPE_READBACK` が同じものか controller 側か未定義）。
- 凍結 file:line: B:185（bump = identity event — 凍結側は「同一性が変わったら検出する」規律を hash で実現する。deployment 側の同一性（serial / firmware / tool）に対応物が無い）・D0:318。
- 再現: commissioning 後に controller firmware 更新・tool 交換。profile 不変・必須 3 check は pass（liveness は生きている）⇒ permit 発行・CLOSED_LOOP lease 成立。`TOOL_PAYLOAD_IDENTIFICATION` evidence は commissioning 時の記録であって permit 時の実物確認ではない。
- 最小修正（zero frozen delta）: `HealthCheckKind` に `CONTROLLER_IDENTITY`（serial + firmware を `CellIdentity` と等値検査）を追加し、`P_HEALTHCHECK_MISSING` の必須集合を {SAFETY_LAYER_HEARTBEAT, CONTROLLER_LIVENESS, CONTROLLER_IDENTITY, TOOL_IDENTITY, GATEWAY_CONFIG_MATCH, ENVELOPE_READBACK}（各 stage ∈ {BEFORE_PERMIT, BOTH}）へ。`ENVELOPE_READBACK` を「controller 側に設定された運動学上限を読み戻し `ControllerEnvelope` と等値確認」と定義（executor 側は 05:158 が担う）。

### CD-10 ［C3 / C4］ MEDIUM — 「曝露 ≤ 1 skill」（06:287・PT-13・05 OP-19）は時間無制限

- 候補 doc:line: 06:287（「曝露 = 最大 1 skill（TERMINAL boundary まで）」）・06:377 PT-13・05:778 OP-19・05:423（WAIT の liveness = heartbeat のみ）・05 全文に lease の最大継続時間なし（grep `duration|lease_max` 0 hit）。
- 凍結 file:line: A:151（`TerminationSpec.declared_classes` は非空 frozenset — TIMEOUT を含む義務は無い ⇒ skill が自ら終端しない設計を凍結は許す）。
- 再現: calibration が失効した状態で WAIT skill（または TIMEOUT を declared_classes に持たない skill）の lease が活性 ⇒ 次の permit まで検出されない ⇒ 検出点は無期限に来ない。
- 最小修正（zero frozen delta）: `RuntimeTimeouts.lease_max_duration_s`（05 `TimingBinding` に同名写像・超過 = TRANSFER_TO_SAFEHOLD(DEADLINE_MISS) + `R_DEADLINE_MISS` の lease 版、または新 fault）を追加；あるいは最低限 06:287 / PT-13 / OP-19 を「≤ 1 skill、ただし skill が TIMEOUT を宣言しなければ時間無制限」と正直化し OPP に登録。

### CD-11 ［C10］ MEDIUM — fold-map の根拠 file が存在せず、SHA256SUMS が陳腐化し、v0.2.2 の全 verdict が起草者自己検証

- 候補 doc:line: 06:4・06:445・06:474（`11_THREE_AXIS_REVIEW_RECORD_20260903.md` を verdict / 機械検査出力の所在として引く）・05:825-866（同）・04:68・08 §10。`ls $D/WMSO_EXACT_BASELINE_REVIEW_v0.2_20260903/11_*` = **No such file**（本 session 実測）。`SHA256SUMS.txt`（mtime 09-04 01:51）の 04/05/06 の値は現 file（mtime 15:41）の sha256 と不一致（§0.3）。06:449-455 の verdict 列は全行「起草者再検証=CONFIRMED（独立 verifier 未了）」— 08 §5「過半が未反証の finding のみ fold」の手続を経ていない。
- 凍結 file:line: 該当なし（records-must-match-fact = CLAUDE.md §15 (b)・ハードストップ「引用先に主張された根拠が存在しない」）。
- 再現: 上記 `ls` と `sha256sum`。
- 最小修正: `11_*` を package に置く（無ければ参照を「未作成」に改める）；`SHA256SUMS.txt` を v0.2.2 で再生成；06:4 status 行に「v0.2.2 fold は起草者自己検証のみ・独立 verifier 未了」を明記。

### CD-12 ［C1 / C8］ LOW — freshness `None` の扱いが 05 と 06 で逆

- 候補 doc:line: 05:425（「有限 → None は `P_FRESHNESS_RELAXED`」）↔ 06:134（「None = 強化なし」）・06:241（「`None` = 強化なし」）。
- 凍結 file:line: A:151（`FreshnessPolicy.max_staleness_s: CanonicalDecimal | None` — 型のみ・OPP-1 / OP-16 のとおり順序は frozen 規定外）。
- 再現: frozen `f = 0.5`・profile `None` ⇒ 06 は受理（実効 0.5）、05 は `P_FRESHNESS_RELAXED` と記述。どちらも fail-safe だが trigger の定義が二重。
- 最小修正: 05 §4.2 の括弧書きを「profile `None` = 強化なし（実効 = frozen）・`P_FRESHNESS_RELAXED` は `p > f` のときのみ」に修正（06 が SSOT）。

### CD-13 ［C3］ LOW — 05 INV-22 の timeout 列挙が 6 件のまま（TimingBinding は 12 field）・05:357 の comment が B2-12 と矛盾

- 候補 doc:line: 05:696（INV-22「ack validity / ack / permit / health / command / manager liveness」）↔ 05:357-368（12 field）・06:286（12 field の写像）／ 05:357（「`valid_until = t_ack + ack_validity_s`」）↔ 05:144 / :160（`t_receive + ack_validity_s`・B2-12）。
- 再現: `safety_heartbeat_timeout_s` を profile 由来でない定数で実装しても INV-22 の字面には抵触しない。
- 最小修正: INV-22 を「`RuntimeTimeouts` の全 field」に改め、05:357 の comment を `t_receive` に統一。

### CD-14 ［C9］ LOW — `P_INTRINSIC_OVERRIDE` は到達不能（strict codec は `P_UNKNOWN_FIELD` を返す）・True 固定の bool field

- 候補 doc:line: 06:235（`P_INTRINSIC_OVERRIDE`「codec = unknown field」）・06:367 PT-05（期待 = `P_UNKNOWN_FIELD`）・06:355（両 code 併記）／ 06:117（`requires_safety_layer_health: bool` True 必須）・06:165（`fail_closed: bool` True 必須）。
- 凍結 file:line: A:385（unknown field 拒否は codec の単一 code）。
- 最小修正: `P_INTRINSIC_OVERRIDE` を CD-05 (a) の用途（null-binding expectation に非 null の timing 値）に限定して再定義するか削除。True 固定 bool は「拒否のためだけに存在する knob」ゆえ削除を推奨（削除しない場合は理由を注記）。

### CD-15 ［C3］ LOW — `profile_label` が hash preimage に入り、label 編集が全 evidence を失効させる

- 候補 doc:line: 06:204（「pin ではない」）・06:220（`profile_hash = H_WCJ(IndustrialDeploymentProfile)` = 全 field）・06:303（record は `profile_hash` で束縛）。
- 再現: label を 1 文字変更 ⇒ 新 hash ⇒ `CELL_COMMISSIONING` / `FAULT_INJECTION_RESULT` 等が全て不一致 ⇒ 再 commissioning。
- 最小修正: 「label 変更 = identity event（evidence 再取得を要する）」と明記するか、OPP に「label を hash 外へ projection するか（§2.3『新 canonicalization 規則は足さない』との緊張）」を登録。

### CD-16 ［C5］ LOW — `HEALTH_CHECK_RUN` / `FAULT_INJECTION_RESULT` record と runtime audit の join key が無い

- 候補 doc:line: 06:300-309（record に `lease_id` / audit seq 無し）・06:342（「`profile_hash` と `lease_id` で join」— record 側に `lease_id` は無い）・05:650-664（`RuntimeAuditRecord` に `profile_hash` あり）。
- 最小修正: これら 2 kind の `artifact_ref` は「当該試験を記録した `RuntimeAuditRecord` の seq 範囲 + lease_id」へ解決必須と §6.1 に明記（型追加なし）。

### CD-17 ［C3 / C10］ LOW — profile 「登録」（registry・受理権限）が未定義で OPP にも無い

- 候補 doc:line: 06:142 / :357（「登録時」「profile_hash の登録」）・06:406 OPP-9（evaluator registry のみ）・05:184 (b)（permit 発行時に profile を解決）。
- 最小修正: OPP-11 として「profile registry の所在・受理者（two-key か operator か）・permit 発行時の解決先が『受理済 registry』に限られること」を登録し、05 §3.4 に `profile_hash ∈ accepted_profiles` を前提として明記。

### CD-18 ［C2］ LOW — DEPLOYMENT_WORKSPACE 項が setpoint 点評価・tool 形状無し

- 候補 doc:line: 06:273（keep-out / reach / height）・06:279（gateway が FK で変換）・05:432（「FK 後」）・06:93-98（`ToolPayloadSpec` に collision hull 無し）。
- 凍結 file:line: B:65-66（適用順 raw → … → bounds — command は EE target の**点**）。
- 再現: 現在 EE と target がともに keep-out 外で、hold 期間の補間経路が keep-out を横切る command は点評価で admit される。
- 最小修正: §4 に「DEPLOYMENT_WORKSPACE は (現在計測 EE → target) の線分 + tool の宣言 hull で評価する」か「点評価であり経路は ISL の責務」かを明記（どちらかを選ぶ・未定なら OPP）。

## 4. 反証の自己検討（各 HIGH に対し）

- CD-01: 「値は RT0 で測り数値を書かない（OP-10）」は反証にならない — 検査は値でなく**関係式**で書けるし、`MIN_FAULT_INJECTION` の拡張は値を要さない。06:266 の網羅表が timeout 経路を欠くのは text の事実。
- CD-02: 「厳密読みなら永久 HOLD = 安全」は反証にならない — 解除権限の未定義は functional-safety の必須要素（reset authorization）の欠落であり、05:508-511 が「profile が定義する」と明示して 06 が定義していない cross-doc 事実。
- CD-03: 「validity_rule の名前が検査を含意する」は反証にならない — 06:257 / :357 の検査文は存在検査であり、失効・subject 単位を評価する文は無い。
- CD-04: 「resolver が content-addressed である」は反証にならない — B:255 が凍結側はそれを要求しないと明記し、06 も要求していない。

## 5. 主張しないこと

- gate PASS / two-key / Rs 裁定を主張しない。本 report は準備レビュー（08 §6）。
- 凍結 4 file への変更を要求しない（全 fix は 05 / 06 の新語層）。
- impl / training / closed-loop authority は CLOSED のまま。
