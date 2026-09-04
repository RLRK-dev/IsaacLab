# AXIS A — contract fidelity review of the WMSO v0.2.1 review candidates

- reviewer: REVIEWER A（設計軸・pS 相当）・別 context の agent・authority 無し・凍結物へ非接触
- 実施 = 2026-09-04 02:02 UTC（`date -u` 実測）
- 対象（content で引く・file 名の v0.2 label は照合用）: `$R/05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md`（792 行・sha256 `f62b0c307d1c…`）／ `$R/06_WMSO_INDUSTRIAL_PROFILE_v0.2_REVIEW_CANDIDATE_20260903.md`（456 行・`852d05724c9c…`）／ `$R/02_FIELD_OVERLAP_AND_HOME_MATRIX_20260903.csv`（41 行・`2a2704d49f3e…`）／ `$R/03_IDENTITY_HASH_EVIDENCE_IMPACT_MATRIX_20260903.csv`（15 行・`c42f93a226ec…`）／ `$R/04_EVIDENCE_POLICY_IMPACT_ASSESSMENT_20260903.md`（75 行・`4da8491b0281…`）／ `$R/07_SUCCESSOR_CONTRACT_DECISION_20260903.md`（71 行・`fa33c669dae1…`）。全 6 file の sha256 = `SHA256SUMS.txt` と一致（自分で再計算）。
- `$D` = `/home/user/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701`、`$R` = `$D/WMSO_EXACT_BASELINE_REVIEW_v0.2_20260903`、`A` = `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md`、`B` = `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md`、`EP` = `$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md`、`JSON` = `$D/WMSO_EvidencePolicy_v1.9.json`、`D0` = `$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md`。
- ⛔ 本 review は準備レビュー。two-key・Rs 裁定・freeze・gate PASS を主張しない。impl / training / closed-loop authority は CLOSED 継続。

## 0. 共通前提の履行（08 §1）

| 前提 | 結果 |
|---|---|
| 1. pin 再測 | `bash $R/verify_exact_baseline_pins.sh` → **11/11 PASS**（D1.1-A `00192d20ca00…` worktree/blob `1353430228…`/commit `54f90a7d`・D1.1-B `5a1874d3be8b…` worktree/blob `ebe8154abf…`/commit `07250f4a`・EP md `c474acea7c58…`・EP JSON `e63176af9bc3…`・definition hash `e7ca43093084…`、policy_semver 1.9.0）。HEAD = `297c850bb31a…` branch `claude/v0-2-design-candidates-snqbmy`。両 commit は `git rev-parse --verify` で実在（2026-07-19 22:23 JST / 2026-07-20 23:11 JST） |
| 2. content sha | 6 候補 file の sha256 を再計算 → `SHA256SUMS.txt` と全一致（上記） |
| 3. 機械検査 | `check_review_candidate.py`: **05 `--runtime` FAIL=0 WARN=6 ／ 06 FAIL=0 WARN=19 ／ 04 FAIL=0 WARN=7 ／ 07 FAIL=0 WARN=4**。**02 FAIL=15 ／ 03 FAIL=11** — 全て H1/S1/F1（md 用 header/section/fold-map 文脈検査）で、C1（引用の実在）は 02/03 とも 0 FAIL。CSV に対する checker の適用可能性 = finding A-08 |
| 4. finding の型 | 全 finding に doc:line + 凍結 file:line + 再現 + 最小修正（schema delta 0）を付す |
| 5. 陽性対照 | `$R/10_POSITIVE_CONTROL_RECORD_20260903.md` と `review_records/PC_KEY_20260903.md` を読了。注入 8 欠陥（PC-05-A..D／PC-06-E..H）は本 review では**実 text に存在しないことを確認**（05:233 「旧 epoch 拒否が有効化」同一線形化点／05:182 CONSUMED は CAS 成功点のみ／05:231 `∪ {consume_offer_id}` 存在／05:419 SHADOW actuation DISABLED／06:186-189 に `action_bounds_cell` 無し／06:231 等値のみ／06:116 `requires_safety_layer_health` True 必須／06:173-178 `on_invalid_state_unresolved` 無し）。以下の finding はいずれも注入欠陥ではない |
| 6. 独立手続 | 他軸（B/C）の finding は読んでいない。critic 報告（`maps/07_critic_report.md`）は引用先の存在確認にのみ用いた |

## 1. 手動 sed 検証した引用（A4・≥15 件要求 → 60 件超・誤り 0）

contracts_v2 `A:39`（certificate を無効化しない）/ `:62`（ControlMode 3 member）/ `:142` `:146` `:147`（required_control_resources / freshness_policy / fail_closed_action）/ `:148`（recovery_rollback_target loud-discard・schema bump 再導入）/ `:151`（BeliefRef = {value: SnapshotRef \| HashRef, t_obs, ttl, confidence, ood_flag}・Ownership・ControlResourceSpec・ProducerOutcome・InitiationSpec・FreshnessPolicy・enum 全数）/ `:159`（SkillDefinitionHash）/ `:168`（WCJ）/ `:218`（BehaviorSignature 補集合定義）/ `:345-352` `:351`（AuthorityDecision {granted, denials, inputs の hash/ref 束縛}）/ `:354`（granted == True 必要条件・非十分・UNKNOWN = DENY）/ `:372-373`（now 明示）/ `:375-378`（validate_handoff signature・snapshot）/ `:380`（required ⊆ offered・interrupt checkpoint ∈ checkpoint_specs）/ `:381`（等値検査・E_HANDOFF_EPOCH_STALE）/ `:382`（責務分離 = authority manager O0 層）/ `:385`（strict codec）/ `:477-486` `:488-494` `:496-506` `:498` `:503` `:506` `:508-529` `:521` `:529`（runtime 型）/ `:537`（U14 defer）/ `:550`（metamorphic #3 serialization-boundary）/ `:570`（RV5 §6 (iii) failure/no-chain）。
tensor_binding `B:4` `:5` `:23` `:24` `:40` `:52` `:65-66` `:75-76` `:81` `:96-99` `:99` `:125-127` `:126` `:127` `:132` `:133` `:138` `:185` `:332` `:374`（U-1）`:377`（U-4）。
EP `:101` `:136` `:148` `:154` `:155` `:156` `:163`；JSON `:5` `:180`（profile_overlay）`:199`（external_conjuncts）`:213`（usage_ceiling）；policy_definition member = **17**（自分で parse・04 §1 と一致）；EP md/JSON の `epoch`/`lease` = 0 hit（04 §2 と一致）。
D0 `:179` `:207` `:210` `:217-223` `:243-247` `:246` `:267-274` `:269`（ack）`:270-272` `:273-274` `:280` `:310-320` `:317` `:318` `:319` `:320` `:354-355` `:363-365` `:367-372`。
C3 `:5` `:30-34`（`:32` = 「SHADOW（rank 2・非 authority）」）`:63` `:65`；slice prereg `:59`；charter `:13` `:129`；skill-ownership ruling `:9` `:24`；D11C custody `:36-38`；freeze record `:39`；HANDOFF_pQ `:11` `:68`；state.md `:91`；LEDGER `:136`。
⇒ **候補文書の凍結 file:line 引用に誤りは検出されなかった**。CSV 02 の 2 件の不精密（F16 / F21）は A-07 に記録。

## 2. Findings（severity 順）

### A-01 — MEDIUM — [A5/A1] 05 §3.5 CAS 前提条件 6 が frozen `AuthorityDecision` に存在しない束縛（deployment `profile_hash`・`skill_action_id`）を要求する
- 候補 doc:line: `05:224`（「decision の inputs hash/ref 束縛が lease の `skill_action_id` / `profile_hash` に一致」）、`05:300`（`R_AUTHORITY_DECISION_MISBOUND` = 「authority decision の inputs 束縛不一致」）。
- 凍結 file:line: `A:346-351` — `evaluate_authority_grant(eligibility_report, acceptance_state, two_key_state, safety_gate_state) -> AuthorityDecision # {granted: bool, denials: tuple[str, ...], inputs の hash/ref 束縛}`；`A:329-337` — `UsageEligibilityReport` の field = {requested_profile, applicable_components, exemptions, effective_grades, issues, evidence_policy_definition_hash, eligible}（`skill_action_id` 無し）；`A:354` 「two-key/安全 gate の実体・充足規則は O0/S0/V0 層（本 chunk 外）」。frozen 4 file に `profile_hash` / `IndustrialDeploymentProfile` = **0 hit**（本 session grep）。
- 主張/矛盾: frozen `AuthorityDecision` の inputs 束縛は eligibility_report / acceptance_state / two_key_state / safety_gate_state の hash/ref であり、(i) deployment `profile_hash` は frozen 世界に存在せず、(ii) `skill_action_id` は eligibility_report の field にも無い。したがって条件 6 後半の述語は frozen 型のままでは**評価対象が無い**。
- 再現: `AuthorityDecision` を `A:351` の 3 要素で構成し、`resolve(authority_decision_ref)` の inputs 束縛から `profile_hash` を取り出そうとする → 取り出す field が無い。§3.5 前文「不能判定 = FALSE」により条件 6 = FALSE ⇒ **全ての CLOSED_LOOP_AUTHORITY lease が `R_AUTHORITY_DECISION_MISBOUND` で拒否**（fail-closed だが弁別力 0 = 「弁別できない述語は証拠でない」）。逆に実装者が満たそうとすれば `AuthorityDecision` に profile_hash 束縛を足す = frozen 型への schema delta（05 §11 項 3・INV-16 と矛盾）。
- 最小修正（schema delta 0）: 条件 6 を「`resolve(authority_decision_ref).granted == True`（`A:354`）∧ decision が束縛する eligibility_report の起点 certificate の `skill_action_id == proposed_lease.skill_action_id`（certificate-first `A:323`・certificate.skill_action_id `A:306`）」に限定し、`profile_hash` との対応付けは **runtime 層の `CommitPermit`（`05:174-175` が既に `authority_decision_ref` と `profile_hash` を同一 permit に束縛）と lease の記録**で担う旨に書き換える。cell 固有の gate（acceptance_state / safety_gate_state record が profile_hash を参照するか）は O0/S0/V0 層の事項として §12 の open point に追加する。`05:300` の行はその読みに合わせて「permit 内の (decision ref, skill_action_id) 不整合」へ改める。

### A-02 — MEDIUM — [A7/A1] INV-16 / T-18 が frozen `A:550` を過大一般化し、05/06 自身の型がそれを破る
- 候補 doc:line: `05:646`（INV-16「runtime 型の全 field 名が frozen 型の WCJ payload key 集合に不在 … frozen §8 の同型 assert `:550` に倣う」）、`05:680`（T-18「runtime 型 field 名 ∩ frozen WCJ key 集合 = ∅」）、`05:55`（§1 表 INV-16 根拠行）。
- 凍結 file:line: `A:550` — 「runtime 型の全 field 名が **static hash の** WCJ payload key 集合に不在」（対象 = frozen runtime 型 vs static hash payload）。
- 主張/矛盾: 05 は「static hash の key 集合」を「frozen 型の key 集合」（runtime 型を含む全 frozen 型）へ広げた。どちらの読みでも 05/06 の型は不変量を満たさない。反例（自分で列挙）: `ActiveAuthorityLease.control_mode`（`05:376`）↔ `ExecutionBundle.control_mode`（`A:70`）/ `ActionBinding.control_mode`（`B:131`）；`TimingBinding.{policy_rate_hz, obs_sampling_rate_hz, action_rate_hz, hold}`（`05:333-336`）↔ `TimingSpec` / `ActionTimingSpec`（`B:97-98, :126-127`・static hash payload）；`AuthorityCas.kind` / `EnvelopeTerm.kind` / `RuntimeAuditRecord.kind` ↔ `ExecutionBundle.kind`（`A:65`）/ `ProofItem.kind`（`A:244`）；06 `ExtraInitiationConjunct.{expr_kind, schema_ref, schema_hash, payload_canonical_json, required_belief_fields}`（`06:121-125`）↔ `InitiationSpec`（`A:151`）；06 `ResourceAvailability.control: ControlResourceSpec`（`06:137`）の直列化 key `ee_left…` ↔ `SkillDefinition.required_control_resources`（`A:142`）。「frozen 型」読みではさらに `control_epoch` / `invocation_id` / `skill_action_id` / `ownership` / `outcome` / `belief_ref` / `episode_id` / `schema_versions` が `A:477-529` と衝突。
- 再現: T-18 を宣言どおり実装（05/06 の dataclass field 名の集合 ∩ frozen WCJ key 集合）→ 空でない ⇒ 「設計違反（test）」が常時 FAIL。
- 最小修正（schema delta 0）: INV-16 を **名前の非交差でなく型境界**として書き直す — 「runtime / profile 型は frozen 型として decode されない（frozen strict codec が runtime 型固有 field を unknown field として拒否 `A:385`）∧ runtime / profile 型の値は frozen hash（SkillDefinitionHash / SkillActionId / ExecutionBundleHash / BehaviorSignature / tensor_binding_hash / evidence_policy_definition_hash）の preimage に入らない（03 matrix C01-C07）」。T-18 は「frozen 型 payload に runtime 固有 key（`lease_id` / `permit_id` / `profile_hash` 等）を混入させた入力が `E_*` unknown-field で拒否される」負例に置換。`A:550` 引用は「同型」でなく「趣旨を継承」と改める。

### A-03 — MEDIUM — [A10/A11] 「凍結 4 file に cell / controller / calibration / deploy の語彙は無い」は over-broad な不在主張（測定範囲 = EP md/JSON のみ）
- 候補 doc:line: `05:97`（home matrix「凍結 4 file に該当語彙なし（EP md/json で … = 0 hit — 03 map §6(e)）」）、`07:23`（§1 根拠 4「凍結 4 file に cell / controller / calibration / deploy の語彙は無い（critic 報告 §3.7 grep）⇒ deployment profile は外部で定義できる」）、`02:37`（F36「frozen 4 file に該当語彙なし ⇒ 外部 profile」）。
- 凍結 file:line（反例・本 session 実測 `grep -n -i`）: `A:570`「calibrated uncertainty」；`B:255`「全 deployment の resolver」；`B:313`「全 deployment の resolver」；`B:337`「calibrated uncertainty」；`cell`（word）= A 8 hit / B 1 hit / EP 10 hit / JSON 1 hit。根拠に挙げた grep（`maps/03_evidence_policy_map.md:458-460`・critic §3.7）は **EP md + JSON のみ**が対象。06 は v0.2.1 C-14 で「EP md / JSON に … 語彙は無い」へ scope を狭めた（`06:330`）が、05 / 07 / 02 は同期されていない。
- 凍結側の規律: `B:279`・`B:458`（N-1）「不在主張を用途で限定せず書いた — over-broad な absence claim の再発」を defect class として記録。
- 影響: 07 §1 の 4 根拠のうち 1 つが偽の事実主張に立つ（結論「外部 profile で構成できる」は strict codec `A:385` と hash 面不変（03 C03）から独立に成立するため崩れないが、決定文書に検証されない absence claim を置く型そのもの）。
- 最小修正: 3 箇所を「EP md / JSON に 0 hit（閉じた query）。DESIGN 2 file の hit は `A:570` / `B:255,:313,:337` の散文語（「calibrated uncertainty」「全 deployment の resolver」）であり schema 語彙・型・field ではない」へ書き換え、07 §1 の根拠は「frozen 型に cell/controller/calibration の field が無い」（型の不在・`A:127-149`・`B:176-181` の field 列挙で検証可能）に置換する。

### A-04 — LOW — [A8] 05 §4.4 が EP evidence profile の要求を deployment `profile_hash` 経由で参照すると述べ、3 軸分離を自ら曖昧にする
- 候補 doc:line: `05:425`「lease は `profile_hash` 経由で EP evidence profile の要求（eligibility report の `requested_profile`）を参照するが、それを再評価しない」。
- 凍結 / 対の doc: `A:329-331`（`requested_profile` は `UsageEligibilityReport` の field）、`A:346-347`（eligibility_report は `evaluate_authority_grant` の入力）；`06:194-213`（`IndustrialDeploymentProfile` の全 field に EP profile / requested_profile を運ぶものは無い）。
- 矛盾: EP evidence profile への到達経路は lease → `authority_decision_ref` → `AuthorityDecision` → eligibility_report.`requested_profile` であり、deployment `profile_hash` はその経路上に無い。同段落が「evidence profile と runtime の出力可否を型で分離する」と言う直後に両軸を結線している。
- 最小修正: 「lease は `authority_decision_ref` 経由で（`A:346-347`）eligibility report の `requested_profile` を参照するのみで再評価しない。`profile_hash`（doc 06）は evidence profile を運ばない（§11 R3）」へ書き換え。

### A-05 — LOW — [A1] 05 §0 の `ActionBinding{bounds, action_scale, control_mode}` は frozen 型に無い field を帰属させる
- 候補 doc:line: `05:19`（D1.1-B 行）。同じ短縮形は `design/briefs/VOCABULARY.md:4` にもある（brief 側の label であり凍結ではない）。
- 凍結 file:line: `B:128-135` `ActionBinding` = {features, total_dim, control_mode, action_scale, timing, container_dtype}（`bounds` 無し）；`B:80-81` `FeatureBinding.bounds: BoundsSpec | None`；`B:138`「全 action feature は `bounds` 必須」。05 §4.3（`05:405`）は正しく `ActionBinding.features[].bounds` と書いている。
- 最小修正: `05:19` を `ActionBinding{control_mode, action_scale, timing} + features[].bounds` に改める。

### A-06 — LOW — [A7] 06 §2.3 反循環文が「SkillActionId を内包しない」と述べつつ `BindingExpectation.skill_action_id` を含む
- 候補 doc:line: `06:220`（「profile は自身の `profile_hash`・lease id・`control_epoch`・`SkillActionId`・`ExecutionBundleHash` を内包しない … `binding_expectations[].skill_action_id` は他者の id」）、`06:182-183`（`BindingExpectation.skill_action_id: str # certified のみ`）。
- 凍結 file:line: `B:23` — 反循環規則の対象は「**自身の** hash・SkillActionId・ExecutionBundleHash・自身と同一であることを主張する任意の hash」（自己参照 hash の不動点回避）。
- 矛盾: 文の前半は全称否定、後半で例外を認める（自己矛盾の文）。意味論上は `profile_hash` が SkillActionId の preimage に入らない（03 C03「profile_hash のみ変わる」）ため循環は無く、defect は文言のみ。
- 最小修正: 「profile は自身の `profile_hash` と、`profile_hash` を preimage に持つ値（lease id / `control_epoch` / permit）を内包しない。他 artifact の content hash（`tensor_binding_hash`）と他 skill の `SkillActionId` の参照は可（`profile_hash` はそれらの preimage に入らない — 03 C03）」。

### A-07 — LOW — [A12/A4] 02 matrix の引用不精密 2 件と v0.2.1 未同期 1 件
- `02:22`（F21）: rationale「D0『producer retains ownership and safe-stops』」の逐語は `D0:273-274`（fail-closed 項）にあるが citation 列は `D0:319`（preemption acts first）。
- `02:17`（F16）: frozen_locus `D0:270-272`（atomic flip）だが「offer→accept→ack の ack」は `D0:267-269`（step 2 の `accept` + `ack`）。
- `02:19`（F18）: 「AuthorityCas (owner, control_epoch, active_lease_id, consumed_offer_ids)」= 4 要素。v0.2.1 の `AuthorityState` は `(owner, control_epoch, active_lease_id, consumed_offer_ids, safehold_reason, boundary_wait, seq)` の 7 要素 tuple 等値（`05:130-137`・`05:219`）。05 §13 の v0.2.1 fold 表（`05:750-763`）に 02/03 の再同期行は無く、02/03 の mtime（09-03 16:39）は fold（09-04 01:5x）より前。
- 最小修正: F21 citation → `D0:273-274`、F16 locus → `D0:267-272`、F18 tuple に `safehold_reason / boundary_wait / seq` を追記し、05 §13 に「02/03 再同期」行を 1 行足す。

### A-08 — LOW — [A10/A12] 機械検査が CSV に適用不能で 08 §1 項 3 の前提（FAIL=0 で読む）が 02/03 で満たせない・CSV に pin header が無い
- 候補 doc:line: `08:23`（「FAIL があれば読む前に HOLD」）、`02:1-41` / `03:1-15`（header 行に pin / status 無し）。checker 実測: 02 FAIL=15（H1×5 / S1×5 / F1×5）、03 FAIL=11（H1×6 / S1×5）。F1 は `02:6`（F05 BeliefSnapshotRef）`02:29`（F28 IntrinsicExecutionLimits）`02:30`（F29 overlay hashes）`02:40`（F39 ParallelExecutionProfile）で発火するが、当該行の disposition 列は `removed` / `not_adopted` であり matrix として正当（checker の免除条件「版歴節 + 削除/不採用 の語」が CSV 構造に無い）。
- 凍結側: 該当なし（手続の欠陥）。C1（引用の実在）は 02/03 とも 0 FAIL であることを明記する。
- 最小修正: `check_review_candidate.py` に CSV mode（H1/S1 を skip・disposition ∈ {removed, not_adopted} の行で F1 免除・C1 は維持・行数 40/14 を assert）を追加するか、08 §1 項 3 に「CSV は行数 + C1 + 手動語彙検査で代替」と明記。CSV 先頭に `# pins: …`（4 full sha + 2 commit）の comment 行を置くと A10 の header 検査も可能になる。

### A-09 — LOW — [A10] x-mask 時刻（`16:4x` / `01:5x`）が header・版歴に残る
- 候補 doc:line: `05:8`「本版（16:4x UTC）」、`05:748`「2026-09-04 01:5x UTC」、`06:3`「v0.2.1 = 2026-09-04 01:5x UTC」、`06:420`「01:5x UTC」、`10_:3`「記録 = 2026-09-04 01:5x UTC」。
- 凍結 file:line: `A:4`「editing 完了実測; 旧『10:5x』表記を確定 — **以後 x-mask 廃止**」；`B:2`「初稿は『11:10』と実測せずに記載した date-THEN-write 違反 — 実測 bracket に置換」（records-fix の先例）。CLAUDE.md §運用15 (a) date-THEN-write。
- 最小修正: 各行を `date -u` 実測の分単位（または bracket）に置換。

### A-10 — LOW — [A5/A2・軸 B へ引継ぎ] frozen `InterruptReason.SAFETY_STABILIZED` の写像が §3.7 と §7 で不一致
- 候補 doc:line: `05:269`（§3.7: `InterruptOutcome` 受領 → 全て `TRANSFER_TO_SAFEHOLD(CHECKPOINT_DISABLED)`）vs `05:592`（§7: `Interrupt SAFETY_STABILIZED → HOLD（safehold_reason = SAFETY・clearance 待ち）`）。解除前提も異なる（`05:467` SAFETY = IndependentSafetyLayer の clearance record／`05:469` CHECKPOINT_DISABLED = operator clearance + 再観測）。
- 凍結 file:line: `A:151` `InterruptReason = {PLANNED_SWITCH, EVENT, SAFETY_STABILIZED}`（3 member を 05 §7 は全て写像しているが §3.7 が reason を区別しない）。
- 最小修正: `05:269` の行を reason で 2 行に分割（PLANNED_SWITCH / EVENT → CHECKPOINT_DISABLED；SAFETY_STABILIZED → SAFETY）。写像の total 性は軸 B の B8 で再確認。

### A-11 — LOW — [A5] `validate_handoff(invocation, …)` の `invocation` が producer の SkillInvocation であることが明示されていない
- 候補 doc:line: `05:245`（§3.6 項 1）、`05:495`（§6.2 B4 — 直前行 `05:494` は consumer 用の `new_invocation(c, …)` を作る）。
- 凍結 file:line: `A:381` — `validate_handoff` は `producer_invocation_id 一致 / offer.producer_action_id == invocation.skill_action_id / offer.producer_definition_hash == invocation.skill_definition_hash == H_WCJ(producer_definition)` を検査 ⇒ `invocation` = **producer** の invocation。
- 再現: B4 で `invocation := new_invocation(c, …)` と読んで実装すると identity 検査が必ず失敗（fail-closed だが常時 `R_OFFER_INVALID` → `RESELECT` 無限）。
- 最小修正: 両行に「`invocation` = producer の `SkillInvocation`（`offer.producer_invocation_id` と一致・`A:381`）」を注記。

### A-12 — LOW — [05↔06 整合] 06 §5 の lease 写像文が v0.2.1 で追加した `ack_validity_s` を落としている
- 候補 doc:line: `06:280`「`TimingBinding.{ack_timeout_s, permit_ttl_s, health_confirm_timeout_s, command_deadline_s, manager_liveness_s}` ← `RuntimeTimeouts`」（5 個）vs `06:145`（`RuntimeTimeouts.ack_validity_s`）、`05:339`（`TimingBinding.ack_validity_s`）、`05:652`（INV-22 は 6 timeout を列挙）。
- 最小修正: `06:280` に `ack_validity_s` を追加。

## 3. Checklist 判定（A1–A12）

| id | 判定 | 根拠 |
|---|---|---|
| A1 | **PASS**（A-05 の表記 1 件） | 05 §1 表・§4.1・§6.3・§6.4・§8、06 §2.1 が引く frozen 型の field 集合は `A:151` `:345-352` `:477-529` `B:96-99` `:125-135` と一致。frozen 型に field の追加・削除・改名を要求する記述なし（A-01 は「frozen 型に無い束縛を前提にする」誤読であり、型変更の提案ではない — 修正で解消） |
| A2 | **PASS** | frozen enum への member 追加なし。`RuntimeDisposition` / `RuntimeFaultCode` / `SafeHoldReason` / `LeaseMode` / `AuditKind` / `EscalationTarget` / `HealthCheckKind` 等は全て runtime / profile 層の新 enum。`ProducerOutcome` 不変（`05:577`・INV-20・T-19）。`ControlMode` 3 member（`05:439-441`）・`FailClosedAction` 3（`05:595`）・`InterruptReason` 3（`05:591-592`）・`ActionHold` 2（`05:396`）・`ExprKind` 参照のみ（`06:121`）を確認 |
| A3 | **PASS** | `BeliefRef` = `{value: SnapshotRef \| HashRef, t_obs, ttl, confidence, ood_flag}`（`05:46` `05:360` `05:490` ↔ `A:151`）。tag enum は frozen に無く、05 は v1 code 由来の「SNAPSHOT \| HASH_REF」表記を critic X1 で全箇所訂正済（`05:746`）。`BeliefSnapshotRef` は 05/06/04/07 に 0 hit（checker F1）。⚠ 08 §2 A3 行と `VOCABULARY.md:4` の「SNAPSHOT \| HASH_REF」は brief 側の label であり凍結逐語ではない（content を優先 — 08 §1 項 2） |
| A4 | **PASS**（A-07 の CSV 2 件） | checker C1 = 全 doc 0 FAIL。手動 sed 60 件超・誤り 0（§1） |
| A5 | **PASS-WITH-CONDITIONS**（A-01 MEDIUM・A-10・A-11 LOW） | `validate_handoff` = 等値検査を CAS 前・消費は CAS 内（`05:243-247` ↔ `A:381-382`）；責務分離（`05:81` ↔ `A:382`）；`granted == True` = 必要条件・非十分（`05:224` `05:420` ↔ `A:354`）；UNKNOWN = DENY は frozen API 内部で閉じ runtime は読むだけ（`05:391`）。条件 6 後半のみ frozen に無い束縛 |
| A6 | **PASS** | `max_obs_staleness_s` = 記録のみ（`05:337` `05:398` ↔ `B:99`）；runtime 鮮度 = frozen `FreshnessPolicy` を stricter-or-equal（`05:338` `06:133` `06:235`）；`now` 明示・単調 clock（`05:494` `05:504` ↔ `A:372-373`）。None 読みは OP-16 / OPP-1 で loud |
| A7 | **PASS-WITH-CONDITIONS**（A-02 MEDIUM・A-06 LOW） | 03 matrix C01–C07 = frozen 6 hash 面 全て no；U14 defer 明記（`05:624` ↔ `A:537`）；`profile_hash` は frozen hash の preimage に入らない。INV-16 の定式化のみ不成立 |
| A8 | **PASS**（A-04 LOW） | 3 軸分離（`05:73` `05:694`、`06:19-22` `06:51-57`、`04:47-51`）；SHADOW = 非 authority は `EP:136` `:155` の逐語（`05:418`）；ceiling / conjoin 不変（`05:691` ↔ `EP:156` `JSON:213`） |
| A9 | **PASS** | U-1（`05:60` ↔ `B:374`）に従い binding / profile に epoch なし；U-4（`B:377`）— 05/06 に `FeatureSource` / `HANDOFF` = 0 hit；D1.1-C carry（`05:700` `06:386`）不参照；合成 OUT（`05:695` `06:338-343` ↔ custody `:36-38`・freeze record `:39`・ownership ruling `:9`）；execution 軸 = Rs（`05:694` `06:380` ↔ C3 `:65`・charter `:13`）。再決定なし |
| A10 | **PASS-WITH-CONDITIONS**（A-03 MEDIUM・A-08・A-09 LOW） | 主張しないこと = 05 §11 / 06 §9 / 04 §6 / 07 §5；Open points ≠ 0（05 OP-1..17・06 OPP-1..10・04 OPE-1..3・07 OPS-1..3）；header pin = 4 full 64-hex + 2 full commit（実在確認）；authority / gate 非主張 |
| A11 | **PASS** | 07 §3 の 4 理由 ↔ `A:385`（unknown field 拒否）`A:218`（補集合）`A:159` `A:308`/`EP:163`（certificate が definition hash を結合）`A:148`（schema bump）；04 §1 17 member = JSON 実 parse と一致・`e7ca4309…` 再計算一致（verify script）；04 §2 `epoch`/`lease` 0 hit 実測一致 |
| A12 | **PASS**（A-07・A-08 LOW） | 02 = header + 40 行、03 = header + 14 行；語彙（layer_of_origin / overlaps_frozen / disposition / verdict）は閉集合で一貫；引用は C1 0 FAIL + 手動確認；05/06 との矛盾なし（F13 の 8 disposition = `05:559`、F23 の 4 term = `05:404-408`、F35 = `05:481`） |

## 4. 反証（3 lens）に耐えるかの自己検査

- A-01: text lens — `A:351` の 3 要素と `A:329-337` の field を逐語で確認、`profile_hash` は frozen 0 hit（grep）。logic lens — 「inputs の hash/ref 束縛」を外部 record への ref と読んでも、その record が profile_hash を持つ規定は 05/06/frozen のどこにも無い。impact lens — 条件は AND・不能判定 = FALSE ゆえ CLOSED_LOOP lease が全滅、または schema delta 誘引。
- A-02: text lens — `A:550` は「static hash の」と限定。logic lens — 反例 field を frozen dataclass 行で列挙。impact lens — INV-16 は A7 を担保する要の不変量であり、常時 FAIL の不変量は担保でない。
- A-03: text lens — grep 実測 4 hit。logic lens — 根拠 grep の対象範囲（map 03 §6(e)）が EP のみ。impact lens — 07 の決定根拠に偽の事実主張（frozen 側が同 class を defect と記録）。

## 5. Verdict

**PASS-WITH-CONDITIONS**（CRITICAL / HIGH = 0、MEDIUM = 3〔A-01・A-02・A-03〕、LOW = 9）。3 件の MEDIUM はいずれも schema delta を要さず fold 案が確定している。fold 後は `check_review_candidate.py` FAIL=0 の再確認と、02/03 の v0.2.1 再同期（A-07）を同一 fold で行うこと。本 verdict は準備レビューであり two-key / Rs 裁定 / gate を代替しない。
