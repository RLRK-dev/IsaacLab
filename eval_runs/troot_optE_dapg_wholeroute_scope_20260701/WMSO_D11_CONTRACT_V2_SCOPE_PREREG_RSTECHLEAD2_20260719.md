# WMSO D1.1 — Decision Record and Scope Preregistration

- node: `T-WMSO` (parent `T-ROOT-RS-TECH-LEAD2`); author = w2:pQ (RS-TECH-LEAD2)
- **decision_status: ACCEPTED** (Rs directive 2026-07-19; verbatim §0)
- **scope_status: SCOPE CLOSED（3 軸）— Rs review-3「SCOPE PASS」+ pS 設計軸 CLOSE + pN SCOPE CONCUR / PASS-CLOSE（08:49 JST、C1-C4 + R1-R3 ALL CLOSE）。解錠 = D1.1-A DESIGN AUTHORING のみ**
- **implementation_status: NOT_STARTED**（code / [CHANGE] / impl / run / authority 系は §9 gate 群 [CC Debate → pN DESIGN PASS → pre-check → rule-check → path freeze / impl GO] まで未解錠）
- grounding_head: `11da258f75` | wmso_d1_commit: `57ed32b27a` (clean at HEAD)
- version: v1 (07:42) → v2 (08:06, pS conditions fold) → v3 (08:12, Rs review-2 必須修正 #1-#8 + 重要事項 #9-#12 + pS addendum minor fold) → v3.1 (08:16, pS C-1 discharge: §0b fold-map 追記) → v3.2 (08:29 JST sha 確定, pN SCOPE HOLD C1-C4 fold: §5 lineage domain 全列挙 / §4 non-increasing 訂正 + ceiling 明記 / §9 fail-closed re-verify loop / bank 手順 §13; bank `6b6b30886b`) → v3.2.1 (08:44 編集・08:47 bank `aaab83887a`, pN records-fix R1: §13-3「3-path atomic」claim 撤回 → 実際の二 commit chain `9ee7434aa1`→`6b6b30886b` に訂正; content 無変更) → **v3.2.2 (08:5x, Rs review-3 pre-bank 2 修正の事後適用 [仮時刻確定・完全 sha 化・JCS 担当 chunk 明記 §2/§3] + Rs design carries DC-1..DC-6 を §10b に固定; records/carry のみ・設計判断 無変更)**
- design-axis: pS RATIFY-WITH-CONDITIONS → v2 実読 CONFIRM → v3 re-check = 設計軸 PASS + C-1 discharge（§0b fold-map）→ v3.2 delta PASS・bank GO → R1-R3 self-correction。**final ratify doc sha256（完全形・照合面）= `4a40bf2f59f58e17b9cb04fa4d9ef3c3d262cb09b8bf883d18434ae92ebf0e92`**（bank `aaab83887a` の committed blob と一致。過程中間版の参照 `196995598d67` / `db17a485d9d2` / `7023eb609a9b` / `cc395766296f` は short ref — 完全形は bank 版 2 点 [`cc395766296f65f5…` = `6b6b30886b`、上記 = `aaab83887a`] のみ保全）
- Rs review-2 判定 (2026-07-19 verbatim): 「修正後PASSです。現状はpNへのscope-concur送付前に修正が必要です。」「これらを直せば、**scope preregとして承認可能な水準**です。」
- Rs review-3 判定 (2026-07-19 verbatim): 「**SCOPE PASSです。**」「scope preregとしては承認可能。仮時刻・省略SHA・JCS担当範囲をbank前に修正し、その後pS delta re-checkとpN banked-SHA readbackへ進んでよい。」〔注: review-3 のレビュー対象は v3.2 時点の写し。pS delta re-check / bank / pN readback / SCOPE CONCUR は review-3 到着前に完了済み（行き違い）。指摘 2 修正は本 v3.2.2 で事後適用し再 bank + 軽 readback を回す〕

**WMSO = World-Model-Based Skill Orchestration**（skill 単位の高位意思決定・計画・遷移管理層。low-level policy および独立安全層とは分離する）。

---

## 0. Provenance (Rs verbatim — decision の出典)

Rs delivered a full written design review of the WMSO deliverable (`~/Downloads/WMSO_deliverables_2026-07-19/`) on 2026-07-19 (review-1), followed by review-2 of this prereg (same day). Decision verbatim:

> WMSOは継続する。ただし現行契約のままD2へ進まず、先にD1.1として契約モデルを修正する。

> D1.1で契約構造を直し、少数スキルのboundary-only vertical sliceを作り、transition datasetと単純なSDMでWMSOの価値をオフライン実証する。全9スキル、深層SDM、リアルタイム化、途中中断はその後に進める。

**Rs verbatim — schema-resolution の disposition (P0-5 grading; strict-vs-pragmatic を close する裁定)** (review-1 §P0-5 逐語):

> これを単純に`RESOLVED`へ変えると、証拠の強さが失われます。
>
> 次の段階を推奨します。
>
> EXACT_TRAIN_TIME — 訓練時source/config/hashが完全に固定
> HASH_BOUND_REPRODUCED — 同一artifactと設定から再現
> RECONSTRUCTED_COMPATIBLE — 現存資料から互換schemaを復元
> DIMENSION_ONLY — 入出力次元だけ判明
> UNKNOWN

(grade×usage の確定表 = review-2 精緻版を §4 に採用。review-1 表は §4 の precursor。)

**Rs verbatim — INSERT 新候補** (review-1 §P0-5 逐語):

> schemaが回収できるという理由だけで、異なる動作modeをINSERTとして登録してはいけません。

**Rs verbatim — usage matrix の地位** (review-2 #4 逐語):

> 「strict対pragmaticをgraded evidenceで解決した」とするなら、**usage matrixはD1.1 Exitの必須条件**にする必要があります。そうでなければ問題はまだ解決していません。

---

## 0b. Rs review-2 → v3 fold-map（完全性照合用; pS C-1 discharge）

| Rs # | Rs 見出し (verbatim) | fold 先 |
|---|---|---|
| #1 | WMSOの正式名称を修正する | 冒頭 太字定義行（World-Model-Based + Rs 推奨定義文） |
| #2 | `contracts_v2`のスコープとD1.1全体のスコープを分ける | §1#4（A/B/C）+ §2（IN/OUT + Exit 2 段階） |
| #3 | `contract_version`の意味を分割する | §3（schema_version / behavior_revision / SkillActionId / SkillDefinitionHash） |
| #4 | evidence gradeは契約全体に1個ではなく、構成要素ごとに持つ | §4（EvidenceRecord 7 component + 確定 usage matrix = D1.1 Exit 必須） |
| #5 | PPOとBCのidentity検証規則を修正する | §5（execution_family × training_lineage 分離 + 検証条件） |
| #6 | `ValidationReport`と`ContractCertificate`を分け切る | §6（Report 常時 / Certificate 合格時のみ + handoff compatibility） |
| #7 | Decision-of-recordとscope preregのstatusを分ける | 冒頭 status 3 行（decision_status=ACCEPTED / scope_status=DRAFT / implementation_status=NOT_STARTED） |
| #8 | 工程ゲートの順序を一本化する | §9（CC Debate = design draft 後・pN DESIGN PASS 前） |
| #9 | `self-contained`と「full-repo依存明示」の二択を残さない | §7c（standalone / monorepo 分離、「or full-repo 依存明示」削除） |
| #10 | migration testの意味を明確にする | §7b（4 移行規則 + 5 tests） |
| #11 | Offline replayだけでは「改善」を証明できない | §8 Phase E（E0 factual / E1 counterfactual / E2 prospective shadow） |
| #12 | `no dynamic alloc`の適用範囲を限定する | §8 Phase F（soft/hard 分離、対象 = hard path のみ） |

---

## 1. Decision (ACCEPTED — Rs authority)

1. **WMSO D0 architecture is accepted**（継続）。
2. 現行実装 = **WMSO 本体でなく D1 契約スキャフォールド**（SDM・skill planner・runtime grounding・transition manager・recovery selector・realtime fast path は未実装）。
3. **D2 must not begin on the current D1 contract. D1.1 is inserted before D2.**
4. **D1.1 milestone consists of**:
   - **D1.1-A `contracts_v2`**
   - **D1.1-B `tensor_binding`**
   - **D1.1-C `artifact_manifest`**
5. schema-resolution disposition = **graded evidence**（§0 verbatim; component 別 = §4）。
6. INSERT 新候補は schema 回収のみで採用しない（behavioral equivalence + initiation/termination 妥当性 + independent acceptance test の hard gate、§0 verbatim）。

---

## 2. Current scope — **this prereg covers D1.1-A `contracts_v2` ONLY**

### IN (D1.1-A)
- static definition / runtime record の分離（`SkillDefinition` / `SkillInvocation` / `SkillOutcome` / `HandoffOffer` / `TransitionRecord`; runtime 側 optional `RuntimeSnapshot`）
- stable identity と hash 体系（§3）
- **minimal JCS canonicalization（Rs review-3 修正 2）**: `SkillActionId` および `SkillDefinitionHash` の計算に必要な**最小限の** RFC 8785 canonicalization を D1.1-A 内で実装（chunk Exit の cross-process hash stability を自足で満たす。package 全体への展開は D1.1-C）
- evidence record の型（component 別 `EvidenceRecord`、§4）+ usage policy の型
- cross-field validator（値単体 / identity 整合 = execution_family×training_lineage / lifecycle 整合 / handoff **compatibility**、§5-§6）
- `ValidationReport` / `ContractCertificate`（§6）
- v1→v2 migration（deterministic / fail-closed、§7b）
- standalone unit/contract test 構造（配布物のみで全実行、§7c）

### OUT (後続 chunk — D1.1 内の別 build 単位)
- D1.1-B: tensor binding 実装（`TensorBindingSpec`: source offset/length・訓練時順序・normalization・scale/bias・bounds・quaternion convention・frame・history stack・sampling rate・action control mode）
- D1.1-C: training artifact manifest（training-time run manifest・**canonical JSON pipeline の package 全体への展開**〔artifact manifest・証拠 bundle・配布 metadata — D1.1-A の minimal JCS を基盤に拡張〕・package/CI 最終整備）
- D2 以降すべて（§8 roadmap）

### Exit 条件（2 段階、Rs #2）

**D1.1-A `contracts_v2` chunk Exit:**
```text
- contract unit test pass
- invalid contract corpus を全拒否
- v1→v2 migration test pass
- contract hash の cross-process 安定性
```

**D1.1 milestone Exit（A+B+C 完了時）:**
```text
- contracts_v2 pass
- tensor_binding pass
- artifact_manifest pass
- clean unpack → pip install -e . → 全 test pass
- component 別 evidence grade + usage matrix 確定（§4; Rs 裁定により必須）
```

---

## 3. Identity 体系（Rs #3 — action ID / schema version / definition hash の分離）

```text
contract_schema_version
  データ形式と migration 用（reader/writer/migration の互換性管理）
  action identity には含めない

behavior_revision
  initiation / termination / action semantics 等、
  スキルの振る舞い契約が変わった場合に更新

SkillActionId
  = H(skill_namespace, skill_id, executable_identity,
      skill_variant_id, behavior_revision)
  — SDM・dataset 上で同じ action として集約する安定 ID

SkillDefinitionHash
  = H(JCS で正規化した SkillDefinition 全体)   [RFC 8785]
  — 実際に使用した契約内容を完全固定する content hash
```

（JCS 実装の担当: **D1.1-A が上記 2 hash に必要な minimal canonicalization を実装**（§2 IN）。package 全体への canonical JSON pipeline 展開は D1.1-C — Rs review-3 修正 2。）

- serialization schema の v2→v3 変更だけでは **SkillActionId は変わらない**（Rs 指摘の不適切設計を排除）。
- `handoff_start_context` は action ID から外し、**SDM 入力特徴 / stratification / provenance** に置く。
- 入口により本当に挙動が別物になる場合のみ、曖昧な文字列 `entry_mode` でなく **`skill_variant_id` として独立に認定**。

---

## 4. Evidence grade — **component 別**（Rs #4）

契約全体に 1 個の grade を与えない（normalizer 不明なのに「契約は HASH_BOUND」と誤認するのを防ぐ）。

```python
EvidenceRecord(
    component_kind,   # 下記 7 種（最低限）
    grade,            # EXACT_TRAIN_TIME | HASH_BOUND_REPRODUCED | RECONSTRUCTED_COMPATIBLE | DIMENSION_ONLY | UNKNOWN
    source_ref,
    artifact_hash,
    evaluator_version,
    notes,
)
```

component（最低限）:
```text
POLICY_ARTIFACT / OBSERVATION_SCHEMA / ACTION_SCHEMA / NORMALIZATION /
INITIATION_SPEC / TERMINATION_SPEC / HANDOFF_SCHEMA
```

**closed-loop 可否 = 必須 component の grade を集約して判定**（単一 component の最良値でなく、必須集合の最弱 grade が bind）。

### Usage matrix（確定版 = Rs review-2 表; D1.1 milestone Exit の必須条件）

| Grade | Offline replay | Shadow | Authority付き closed-loop |
|---|---|---|---|
| EXACT_TRAIN_TIME | 可 | 可 | acceptance test 後に可 |
| HASH_BOUND_REPRODUCED | 可 | 可 | acceptance test 後に可 |
| RECONSTRUCTED_COMPATIBLE | 可 | 非authority のみ | 不可 |
| DIMENSION_ONLY | 診断のみ | 不可 | 不可 |
| UNKNOWN | 不可 | 不可 | 不可 |

- 表は conservative で、grade 降順に権限は **monotone non-increasing**（隣接 grade が同権限の場合を含む: EXACT_TRAIN_TIME と HASH_BOUND_REPRODUCED は同権限。「低 grade は厳密に少なく unlock」は誤りにつき撤回 — pN C2 訂正）。pS P1（単調性）= Rs 表で SATISFIED。
- **usage matrix は権限の上限（ceiling）であって authority grant ではない**（pN C2）。表の「可」は当該 usage の必要条件側を満たし得ることのみを示す。closed-loop authority は acceptance test（必要条件の一つ）に加え、**O0/S0/V0 の two-key + 独立安全 gate を必ず conjoin**。
- **「条件付き」系 cell（acceptance test 後に可 / 非authority のみ / 診断のみ）の意味は design doc で明示的に定義する — silent に「可」へ潰さない**（pS addendum §6#4）。
- D1-exit は達成 grade（component 別）を**記録**する。binary「RESOLVED」へ丸めない（pS P2）。

---

## 5. Identity 検証規則（Rs #5 — execution family と training lineage の分離）

「PPO と BC の混在禁止」は誤り（BC 初期化 → PPO fine-tune は実行 family=PPO かつ lineage=BC_THEN_RL で合法）。検証するのは**宣言された lineage と artifact 参照の一致**。

```text
execution_family: PPO | DAPG | BC | SCRIPTED | WAIT
training_lineage: RL_ONLY | BC_ONLY | BC_THEN_RL | NOT_APPLICABLE   (pN C1: 非学習 skill 用 discriminator)
```

**許容組合せの全列挙（pN C1）— 下表に無い cross-product は fail-close 拒否**:

| execution_family | training_lineage | 必須 hash | null 必須 | source-closure |
|---|---|---|---|---|
| PPO | RL_ONLY | final artifact hash | bc_base_hash / bc_config_hash = null | n/a (null) |
| PPO | BC_THEN_RL | bc_base_hash + bc_config_hash + final artifact hash | — | n/a (null) |
| DAPG | RL_ONLY (from-scratch) | final artifact hash | bc_base_hash / bc_config_hash = null | n/a (null) |
| DAPG | BC_THEN_RL | bc_base_hash + bc_config_hash + final artifact hash | — | n/a (null) |
| BC | BC_ONLY | final (BC) artifact hash | RL stage fields = null | n/a (null) |
| SCRIPTED | NOT_APPLICABLE | — | 全 training hash = null | **source_closure_sha256 必須** |
| WAIT | NOT_APPLICABLE | — | 全 training hash = null | **source_closure_sha256 必須** |

- 学習 family（PPO/DAPG/BC）に NOT_APPLICABLE は不可; 非学習 family（SCRIPTED/WAIT）に RL_ONLY/BC_ONLY/BC_THEN_RL は不可（fail-close）。
- 非学習 family の identity は source-closure（記載 member の集合 hash）で pin し、closure member 欠落は FileNotFoundError（現 v1 `validate_source_closure` の fail-closed 挙動を維持）。
- design doc で本表を validator の唯一の許容表として実装（表外 = stable error code で拒否）。

（charter gate #1「algorithm independence」の実装形 = 契約が RL_ONLY lineage を構造的に admit できること。歴史的 exemplar の exact schema 回復は要求しない — pS (d) 2軸分離、§10。）

---

## 6. Validation → Report → Certificate（Rs #6）

```text
validate(contract)
  ↓
ValidationReport（常に生成）
  - valid
  - error_codes（安定 code; 自由文 reasons は補助）
  - field_paths
  - validator_artifact_hash
  ↓ valid の場合のみ
ContractCertificate（合格時のみ発行）
  - skill_definition_hash
  - validator_artifact_hash
  - evidence_policy_version
  - issued_at
```

- 不適合契約に certificate を発行しない。
- `validation_time` / `issued_at` は **contract hash の計算対象外**。
- validator の同定は version 文字列でなく **実装 artifact hash** で固定。

### Cross-field validator（review-1 P0-4 の全項目 + 以下）
- 値単体: ID/unit/schema_ref 非空・shape 全次元>0・timestamp/duration/cost 有限・TTL>0・confidence/progress∈[0,1]・duration/cost≥0・p50≤p95・std≥0。
- identity 整合: §5 の execution_family×training_lineage 条件・`SkillActionKey.skill_id` と scripted/wait identity の一致・契約 family と identity family の一致。
- lifecycle 整合: handoff producer=現 invocation・terminal ∈ 宣言済み termination class・interrupt checkpoint ∈ 宣言済み safe checkpoints・resumable なら resume state 必須・重複 checkpoint/handoff ID 禁止。
- **handoff compatibility**: `accepted_handoff` は存在確認でなく **produced_handoff_schema compatible-with accepted_handoff_schema** を検証（field・単位・frame・version・必須/任意属性）。

---

## 7. Test / migration / packaging 規律

### 7a. Chunk tests（D1.1-A Exit を構成）
- 正常系 unit tests + **invalid contract corpus 全拒否**（review-1 §1 の全 negative 入力: 負 shape・空 field_id・`ttl=-1`/`confidence=2`・`progress=3`・負 duration・producer skill 不一致・未宣言 checkpoint・lineage/artifact 不一致 等）。
- contract hash cross-process 安定性（同一入力 → 別 process でも同一 `SkillDefinitionHash`）。

### 7b. Migration の意味定義（Rs #10 — 単純 rename ではない）
```text
v1 static fields   → SkillDefinition へ移行
v1 runtime fields  → optional RuntimeSnapshot へ移行
証拠がない field    → 推測で埋めず UNKNOWN
変換不能           → stable error code で拒否
```
必要 test:
```text
v1 fixture → v2 deterministic migration
同じ v1 → 常に同じ SkillDefinitionHash
v2 → v2 migration は no-op
不完全 v1 → fail-closed
UNKNOWN evidence を勝手に昇格しない
```

### 7c. Standalone / monorepo の分離（Rs #9 — 二択を残さない）
```text
standalone unit/contract tests:
  配布物だけで全て実行可能・unexpected skip なし
  （standalone Exit 条件から「or full-repo 依存明示」は削除）

monorepo integration tests:
  full repository 上で別 job として実行
  standalone Exit とは分離
```

---

## 8. Roadmap B–G（BANKED, DEFERRED — 本 prereg 対象外）

- **Phase B**: 2–3 skill + 1 transition/recovery の boundary-only vertical slice（mid-skill interruption なし）。
- **Phase C**: D2 transition dataset（coverage matrix = skill×incoming handoff×outcome; initiation 拒否/failure/timeout/no-progress/OOD/handoff 失敗/recovery/safety intervention も意図収集）。
- **Phase D**: M0 baseline SDM（tabular/Dirichlet + categorical outcome + duration/cost regression + 小 ensemble; NLL/Brier/ECE/coverage/OOD abstention）。⚠ `TaskObjective`/Q 値は reward/objective 設計 → **/reward-design gate 必須**。
- **Phase E（Rs #11 — 3 分割; raw replay だけで task-success 改善を Go 条件にしない）**:
  ```text
  E0: factual replay — schema 整合 / candidate filtering / support・OOD 判定 /
      実行 skill と選択 skill が一致する箇所の予測精度
  E1: counterfactual evaluation — simulator / calibrated SDM rollout /
      behavior propensity 付き off-policy evaluation
  E2: prospective shadow — WMSO の選択を記録、authority は与えない
  ```
- **Phase F（Rs #12 — soft/hard を分離; `no dynamic alloc` の適用対象を明記）**:
  ```text
  soft realtime WMSO（Python 可）:
    bounded candidate 数 / bounded model call / no unbounded allocation /
    p99・max deadline 評価
  hard realtime handoff/safety path（native）:
    preallocated buffer / GC なし / disk I/O なし
  ```
  `no dynamic alloc` の対象 = **hard path（safety path + handoff path）のみ**。Python planner 全体には要求しない。
- **Phase G**: event-driven interruption（最後; safe checkpoint 実測・continuation value データ・resume state・transition manager・switch cost/hysteresis・boundary-only 超え根拠が前提）。

---

## 9. 工程ゲート順序（Rs #8 — 一本化; CC Debate = 設計レビューとして design draft 後・pN DESIGN PASS 前）

```text
scope prereg
→ pS design re-check (v3)
→ pN SCOPE CONCUR
→ design draft (contracts_v2 DESIGN doc)
→ 5体 CC Debate / pre-mortem（設計レビュー）
→ design 修正
→ pN DESIGN PASS-CLOSE
→ /pre-check
→ /rule-check stage2
→ implementation（frozen paths）
→ pN IMPL PASS-CLOSE
```

**Fail-closed re-verify loop（pN C3）**: `/pre-check` / `/rule-check` / implementation の後段で design を変える finding が出た場合、**design 再 bank →（変更規模に応じ CC Debate 再実施）→ pN DESIGN 再 verify** に戻る。pN DESIGN PASS-CLOSE は**最終 design sha に対してのみ有効** — stale sha の PASS を後段へ持ち越さない。

lanes: dev = w2:pQ / design-ratify = w2:pS (WMSO-DESIGN) / evidence-verify = w2:pN / custody = w2:p6。
検証は fresh detached worktree（共有 dirty tree の test 結果を引用しない）。

---

## 10. pS carried design-invariants（contracts_v2 DESIGN doc へ持込む; source = pS ratify + addendum）

- **R1**: contracts_v2 は v1 型を **SUPERSEDE**（共存させない）。旧 mixed static/runtime 契約（`contracts.py:475` 系）は removed / hard-deprecated と design doc に明記。**pN carry**: v1 symbol が public API に当たる場合は AGENTS.md 規約に従い deprecation / compat shim 先行（同 release での remove 禁止）— removal 形式は design doc で確定。
- **R2**: v1 の IMPL PASS-CLOSE（`57ed32b27a`, 40P/5S/0F）を contracts_v2 の証拠として引用しない。v2 は自前の pN IMPL PASS-CLOSE が要る。
- **R3**: 名称 canonical = charter 綴り（本 v3 冒頭に反映済）。
- **P1**: grade×usage は conservative + monotone — **Rs 確定表（§4）自体で SATISFIED**（pS addendum 訂正: 表は Rs 逐語、pQ 設計ではない）。
- **P2**: D1-exit は達成 grade を記録（binary RESOLVED に丸めない; §4）。
- **P3**: INSERT 新候補の hard gate 維持（§1#6）。
- **(a)** grade は **MEASURED**（現存 on-disk schema 事実から測る）、asserted しない。**(b)**=P1。**(c)**=P2。
- **(d) 2軸分離**: 構造的 algorithm-independence（契約+validator+負制御が RL_ONLY lineage を admit — §5 実装形）と、歴史的 exemplar の **provenance grade**（identity 軸、O0/S0/V0 での実 skill 使用向け）を分離。混同すると D1 を永久 block するか over-claim する。
- **minor（pS addendum §6#4）**: §4 表の「条件付き」系 cell の意味を design doc で明示（silent 可 化 禁止）。
- **pN carry（D1.1-C 向け）**: 新規依存の追加回避（AGENTS.md）・CI action は SHA pin + admin allowlist 維持。

## 10b. Rs review-3 design carries（DC-1..DC-6 — scope は再開せず、contracts_v2 DESIGN doc の必須 carry として固定; pN DESIGN PASS-CLOSE までに必須）

- **DC-1 ExecutionBundleHash**: 実行結果を決めるのは policy weights だけではない。identity は実行 bundle に結び付ける:
  ```text
  Learned: policy weights / model architecture / tensor binding / normalizer /
           action scale / control mode / runtime parameters
  Scripted・Wait: source closure / config / schedule / wait duration・wait condition
  ExecutionBundleHash = H(executable artifact, tensor binding, normalization,
                          control mode, runtime config)
  SkillActionId = H(skill namespace, skill ID, ExecutionBundleHash,
                    skill variant, behavior revision)
  ```
  **fail-closed 規則**: D1.1-B 完了前は tensor binding hash が存在しないため、当該 skill は closed-loop eligibility を得られない。
- **DC-2 evidence の暗号学的結合**: `ContractCertificate` に `evidence_bundle_hash` / `evidence_policy_hash` / `contract_schema_version` を追加（どの EvidenceRecord 集合で合格したかを固定）。`EvidenceRecord.evaluator_version` は `evaluator_artifact_hash` へ変更または併記。**usage 別 required component set** を定義（`OfflineReplayProfile` / `ShadowProfile` / `ClosedLoopProfile`: required components + minimum grade per component; closed-loop は最低 POLICY_ARTIFACT / OBSERVATION_SCHEMA / ACTION_SCHEMA / TENSOR_BINDING / NORMALIZATION / CONTROL_MODE / INITIATION_SPEC / TERMINATION_SPEC / HANDOFF_SCHEMA）。`TENSOR_BINDING` / `CONTROL_MODE` component は D1.1-B で追加する方針を明記（§4 の 7 component は「最低限」）。
- **DC-3 grade 別 proof obligation（fail-closed）**: 各 grade の認定に要求する証拠を明文化（EXACT_TRAIN_TIME = training run manifest / source commit / config hash / input・output schema hash / normalizer hash / final artifact hash / train-time cryptographic binding。HASH_BOUND_REPRODUCED = source・config・artifact hashes / reproduction procedure / reproduced output hash / evaluator artifact hash。RECONSTRUCTED_COMPATIBLE = reconstruction sources / compatibility tests / unresolved differences / evaluator artifact hash。DIMENSION_ONLY = dimension source + semantic fields explicitly unresolved。UNKNOWN = authority-relevant claim 不可）。これが無いと grade が測定値でなく自己申告値になる（§5b (a) MEASURED の実装形）。
- **DC-4 数値検証の完全化**: `isfinite` を timestamp/duration/cost に加え **TTL / confidence / progress / p50 / p95 / std / 全 bounds 値 / normalization mean・std / scale・bias** にも適用（`ttl=+inf`・`p50=p95=+inf`・`std=+inf` は大小比較だけでは通る）。invalid corpus へ追加: `NaN` / `±Inf` / whitespace-only ID / `bool` を整数 shape として渡す / unknown enum / unknown JSON field / Unicode 正規化差 / duplicate canonical key / 非正規化 hash 文字列。property-based test（ランダム入力での不変条件試験）を加える。
- **DC-5 lineage 表の実在限定**: `DAPG | RL_ONLY (from-scratch)` を実際にサポートするか DESIGN で明示。現に利用する実装が無ければ表から外し、必要になった時点で schema version / policy update として追加する方が fail-closed（「将来の algorithm independence」のためだけに validator の許容範囲を広げない）。
- **DC-6 v1 compatibility shim の意味**: v1 と v2 を独立した二つの source of truth として共存させない。必要な v1 shim は**内部で v2 へ変換・委譲**し、新しい状態や validation logic を保持しない。

---

## 11. Process / L-triage

- **L = L3**（設計変更 + 新規/再構成多ファイル + charter 統治 node）。
- FOUNDATIONAL INVARIANT（RS71 §0: dual-arm/88mm/DiffIK/コ/no-trick）= **非抵触**（WMSO は高位 orchestration 層、物理制御に触れない）。
- design gate（`/reward-design`）は Phase D（objective/SDM）で発動（D1.1-A では非該当）。

## 12. 未解決点
- INSERT 新候補（approach-mode → INSERT exemplar 化）の可否 = behavioral equivalence test 後に判定（§1#6）。schema 回収のみでは不可。
- **charter 文書への D1-exit criterion 正式 fold**（grade×usage + 2軸分離）: 方針は Rs review-2 で確定（§0 verbatim「usage matrix は D1.1 Exit の必須条件」）。charter 本文の改訂 commit は Rs ratify + pN 経由（Rs 専権、自分で bar を動かさない）。

## 13. 次アクション
1. ✅ Rs review-2 #1-#12 fold (v3) → pS PASS + C-1 discharge (v3.1) → pN SCOPE HOLD C1-C4 fold (v3.2)。
2. ✅ pS v3.2 delta re-check = 設計軸 PASS・bank GO（08:35）。
3. ✅ bank 完了 — 実際の bank は**二 commit chain**: LEDGER = `9ee7434aa1`（p6 先行 bank）→ prereg + pS ratify = `6b6b30886b`（explicit 2 paths）。当初計画の「3-path atomic commit」記述は実行形と不一致につき**撤回**（pN R1 records-fix; 履歴 rewrite はしない）→ records-fix `aaab83887a`。
4. ✅ pN blob readback → **SCOPE CONCUR / PASS-CLOSE（08:49、C1-C4 + R1-R3 ALL CLOSE）**。
5. ✅ Rs review-3 = **SCOPE PASS** → pre-bank 2 修正を本 v3.2.2 で事後適用（行き違い、ヘッダー注記）+ DC-1..DC-6 を §10b に固定 → 再 bank + pS/pN 軽 readback。
6. **contracts_v2 DESIGN doc 執筆**（§2 IN 6 項 + §5b/N-1/N-2 + §10b DC-1..DC-6 を駆動要件に）→ §9 の順（CC Debate / pre-mortem → pN DESIGN PASS → pre-check → rule-check → path freeze / impl GO; fail-closed re-verify loop 込み）。
7. milestone verdict を p6 へ relay（都度）。
