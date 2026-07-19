# WMSO D1.1-A EvidencePolicy v1.9（DESIGN 付属 normative artifact）

- node: `T-WMSO`; author = w2:pQ; v1 = 2026-07-19 10:54 JST / v1.1 = 12:02 / v1.2 = 12:41 / v1.3 = 13:33 / v1.4 = 14:00 / v1.5 = 14:24 / v1.6 = 16:03 / v1.7 = 16:40 / v1.7.1 = 17:34（pN R1 fold）/ v1.8 = 20:25（RV7 fold — pS 工程 12 design-axis PASS・pN 工程 13 ⛔HOLD B1-B4）/ **v1.9 = 21:18 JST（実測 — pN 工程 13 B1-B4 fold: §3c classifier/overlay 分割・§3d EXACT×非学習 機械拒否・projection 構造化 field map + golden 7 本・DEMO_PLUS_RL lineage — semantic 変更につき definition hash 更新）**
- 親設計: `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md` **v2.11**（本 artifact が全表の normative 実体。`policy_document_sha256` = 本 file の sha256、validator/certificate が結合するのは §6 の **`evidence_policy_definition_hash`**）
- **機械可読兄弟 artifact（RV5-W-P0-6 / RV6 §2 二層形）**: `WMSO_EvidencePolicy_v1.9.json` = `{metadata, policy_definition}`。**`evidence_policy_definition_hash` = H_WCJ(policy_definition) = `e7ca43093084c167a209b008533a66d26a1fd3223d2a3c11274d28306c3ff803`**（banked JSON から**実算出・掲載** — policy_definition は **ASCII key・ASCII str/int/bool のみ〔float・null・非 ASCII なし — RV7 R-4 訂正〕**で H_WCJ = RFC8785 正準 JSON の sha256 と一致〔UTF-16/ASCII key 順が一致する部分集合〕。導出 command = JSON metadata に埋込・第三者再計算可能。metadata の変更は hash 不変・validator 挙動を変える規則の変更のみ hash 変化）。impl 時の golden test = 本値と code 定数の一致検証。⚠**旧 pin（v1.7 系 `066eed1049f4…`/`ed10c77a…`・v1.8 系 `bdc5082008…`/JSON `00032f9091…`）は最終 pin から退役**（semantic 変更の系譜 — 各版 sha = 親設計 version 履歴 + manifest が正）。
- status: **DRAFT v1.9** — pN 工程 13 B1-B4 fold 版・pS 再照合 → pN exact-pin 再検証 PENDING（⚠版数は title/status/親 pointer の 3 所同期 — G-1 規則）
- v1 からの変更: §3 の 3 cell exact 化 / DC-3 準拠復元 / §3b ProofItem 順序・conflict 規則 / §4 EXPLICIT_NONE 免除 / §4b per-component 意味論の明示 / E_GRADE_INAPPLICABLE の S-group 拡張 / 引用 host 修正。v1.1 からの変更: §3c ApplicabilityResolver（v3 W-P0-1 sketch 採用）/ §3 total-map 宣言 + cell 表記の置換/補完 意味明示（v3 W-P0-5）/ §6 semantic hash 分離（v3 W-P1-3）。**v1.7.1 からの変更（RV7）**: §3c `resolve_applicability` 5 引数 + 優先順位 instance→profile→lineage→default（P0-2）/ §3d projection 2 種の確定形 + golden vector（P0-3）/ CONFIG_HASH total map〔stage 判別子の廃止〕（P0-4）/ evaluation certificate wiring = E_GRADE_MISMATCH・evidence_evaluation_bundle_hash・eligibility は assigned_grade 使用（P0-6）/ JSON metadata 型記述訂正（R-4）。**v1.8 からの変更（pN 工程 13 B1-B4）**: §3c を **classifier（profile 中立・component-scoped 排他 branch）+ profile overlay（eligibility 専用）** の 2 段に分割〔B1 — 逐次評価の else 吸収と None-profile min_grade 未定義を型で閉塞〕/ §3d **EXACT_TRAIN_TIME × SCRIPTED・WAIT = `E_GRADE_INAPPLICABLE` 機械拒否**〔B2 — prose bound を機械規則化〕/ projection = **構造化 field map + golden 7 本**（CM 全 3 member + HS empty/single/multi/reorder）〔B3〕/ **TrainingLineage += `DEMO_PLUS_RL`**（imitation-plus-RL 単一 joint stage — demo 系 lineage 集合 {BC_ONLY, BC_THEN_RL, DEMO_PLUS_RL} に参加）〔B4 — algorithm-neutral 化の EP 側; method registry = 親設計 §3〕

## 1. ProofKind semantics（15 種 — 親設計 §4.2 の enum と 1:1; v1 から不変）

| ProofKind | 意味 |
|---|---|
| TRAIN_RUN_MANIFEST | 訓練 run の一次 manifest |
| SOURCE_COMMIT | 訓練時 source commit id |
| CONFIG_HASH | 訓練 config sha256 |
| INPUT_SCHEMA_HASH | 訓練時 観測 schema sha256 |
| OUTPUT_SCHEMA_HASH | 訓練時 行動 schema sha256 |
| NORMALIZER_HASH | normalizer state sha256 |
| FINAL_ARTIFACT_HASH | 対象 artifact sha256 |
| TRAIN_TIME_CRYPTO_BINDING | 訓練時暗号束縛 |
| REPRODUCTION_PROCEDURE | 再現手順書 |
| REPRODUCED_OUTPUT_HASH | 再現出力 sha256 |
| RECONSTRUCTION_SOURCES | 復元資料列挙（path+sha） |
| COMPATIBILITY_TEST | 互換性試験記録 |
| UNRESOLVED_DIFFERENCES | 未解決差分の明示列挙 |
| DIMENSION_SOURCE | 次元数の出所 |
| EVALUATOR_ARTIFACT | 評価器実装 sha256 |

## 2. component 群（v1 から不変）
- **A: artifact 系** = POLICY_ARTIFACT / MODEL_ARCHITECTURE / NORMALIZATION / TRAINING_DATASET / RUNTIME_CONFIG / TENSOR_BINDING
- **S: schema/spec 系** = OBSERVATION_SCHEMA / ACTION_SCHEMA / INITIATION_SPEC / TERMINATION_SPEC / HANDOFF_SCHEMA / CONTROL_MODE
- **P: provenance 系** = TRAINING_PROVENANCE

## 3. ProofPolicy — total machine-readable map（v3 W-P0-5）

**domain = (component_kind, evidence_grade, applicability_class) → exact required ProofKind set。** applicability_class（§3c resolver の出力）が NOT_APPLICABLE / OPTIONAL の cell は「required set 適用なし」（NOT_APPLICABLE = 集約から除外・attest 記録 / OPTIONAL = 記録可・eligibility 集約外）。REQUIRED の cell のみ下表を引く。
**cell 表記の意味（v3 W-P0-5 の曖昧性解消）**: component 名指しの cell（§3 注記の「TB/CM/RC@EXACT = {…}」等）は group 規則を**置換**する。「A 群規則 + X」形の注記は group 規則を**補完**する（和集合）。それ以外は group 規則そのまま。

### 3a. required ProofKind set（REQUIRED cell・全 cell 一意）

| grade | A: artifact 系 | S: schema/spec 系 | P: TRAINING_PROVENANCE |
|---|---|---|---|
| EXACT_TRAIN_TIME | TRAIN_RUN_MANIFEST + SOURCE_COMMIT + CONFIG_HASH + FINAL_ARTIFACT_HASH + TRAIN_TIME_CRYPTO_BINDING | TRAIN_RUN_MANIFEST + SOURCE_COMMIT + schema-hash(下記 †) | TRAIN_RUN_MANIFEST + SOURCE_COMMIT + FINAL_ARTIFACT_HASH + TRAIN_TIME_CRYPTO_BINDING |
| HASH_BOUND_REPRODUCED | **SOURCE_COMMIT** + CONFIG_HASH + FINAL_ARTIFACT_HASH + REPRODUCTION_PROCEDURE + REPRODUCED_OUTPUT_HASH + EVALUATOR_ARTIFACT | **SOURCE_COMMIT** + REPRODUCTION_PROCEDURE + REPRODUCED_OUTPUT_HASH + schema-hash(†) + EVALUATOR_ARTIFACT | **SOURCE_COMMIT** + CONFIG_HASH + FINAL_ARTIFACT_HASH + REPRODUCTION_PROCEDURE + **REPRODUCED_OUTPUT_HASH** + EVALUATOR_ARTIFACT |
| RECONSTRUCTED_COMPATIBLE | RECONSTRUCTION_SOURCES + COMPATIBILITY_TEST + UNRESOLVED_DIFFERENCES + EVALUATOR_ARTIFACT | RECONSTRUCTION_SOURCES + COMPATIBILITY_TEST + UNRESOLVED_DIFFERENCES + EVALUATOR_ARTIFACT | RECONSTRUCTION_SOURCES + **COMPATIBILITY_TEST** + UNRESOLVED_DIFFERENCES + EVALUATOR_ARTIFACT |
| DIMENSION_ONLY | **{DIMENSION_SOURCE, UNRESOLVED_DIFFERENCES}**（literal — C-CH8）。ただし**次元概念を持たない component は `E_GRADE_INAPPLICABLE`**: P 全体 + S のうち INITIATION_SPEC / TERMINATION_SPEC / HANDOFF_SCHEMA / CONTROL_MODE（D-CH10）。適用可 = OBSERVATION_SCHEMA / ACTION_SCHEMA / A 群 |
| UNKNOWN | （無条件 — authority-relevant claim 不可） |

† schema-hash = INPUT_SCHEMA_HASH（OBSERVATION_SCHEMA）/ OUTPUT_SCHEMA_HASH（ACTION_SCHEMA）/ CONFIG_HASH（他 S component）。

- **DC-3 準拠復元（A-CH2）**: v1 で欠落していた SOURCE_COMMIT@HASH_BOUND（全群）、REPRODUCED_OUTPUT_HASH@P×HB、COMPATIBILITY_TEST@P×RECONSTRUCTED を追加（prereg §10b DC-3 の列挙に一致 — supersession でなく準拠に戻す）。
- **3 cell の exact 化（C-CH4）**: 旧「TB/CM/RC@EXACT は…or…」の disjunction を廃止。**(TENSOR_BINDING | CONTROL_MODE | RUNTIME_CONFIG, EXACT_TRAIN_TIME) = {TRAIN_RUN_MANIFEST, SOURCE_COMMIT, CONFIG_HASH}**（config が該当節を運ぶ; FINAL_ARTIFACT_HASH / TTCB は要求しない — 独立 artifact が無い component のため）。NORMALIZATION@EXACT は A 群規則 + NORMALIZER_HASH。TRAINING_DATASET@{EXACT, HB} の FINAL_ARTIFACT_HASH = dataset sha256。
- 不足 = `E_PROOF_INSUFFICIENT`（1 段下 grade で再提出可）。**1 component = 1 certified claim**（重複 = `E_EVIDENCE_DUPLICATE`）。`notes` は evidence_bundle_hash 対象外。
- grade rank: EXACT=4 > HASH_BOUND=3 > RECONSTRUCTED=2 > DIMENSION_ONLY=1 > UNKNOWN=0（rank は親設計で `.rank` 属性、`.value` = member 名文字列 — C-CH5）。
- **record 不在の required component は UNKNOWN(0) として集約**。

### 3b. ProofItem の canonical 順序と conflict（W-P1-3）
- claim 内 ProofItem の canonical 順 = **(kind.value UTF-8 bytes, ref UTF-8 bytes, artifact_hash-or-empty ASCII)** の tuple 昇順（**RV4 §2.8 の指定文字列そのまま — 独立 rank は使わない**）。〔B6: 旧「§1 表の行順 = .value bytes 順」は事実として両者が異なり二義的だったため撤回。golden vector + shuffle test は本順序で固定（親設計 §8 #9）〕
- **exact duplicate**（kind, ref, artifact_hash 全一致）→ 冪等 dedupe（hash に 1 回のみ寄与）。
- **同 (kind, ref) で artifact_hash が異なる** → `E_PROOF_CONFLICT`（fail-closed — 曖昧な証拠を黙って選ばない）。

### 3c. applicability = classifier + profile overlay の 2 段（v3 W-P0-1 sketch → RV7 P0-2 → **pN 工程 13 B1 で分割確定**）

```text
# 段 1 — profile 中立 classifier（certification と eligibility の両方が使用）
classify_applicability(
    identity_kind,              # certificate.identity_kind
    training_lineage,           # certificate.training_lineage
    explicit_none_components,   # certificate.explicit_none_components（F-1 — certificate 単独で計算可能）
    component,
) -> NOT_APPLICABLE | OPTIONAL | REQUIRED_CLASS      # REQUIRED_CLASS は min_grade を持たない

# 段 2 — profile overlay（eligibility 専用; requested_profile は非 None 必須）
resolve_applicability(classification, requested_profile, component)
  -> REQUIRED(min_grade) | NOT_APPLICABLE | OPTIONAL
```

- **classifier の branch（component-scoped・互いに排他 — 逐次 fallthrough で他 component を吸収しない〔B1〕）**:
  1. **instance branch（全 component）**: component ∈ explicit_none_components → **NOT_APPLICABLE**。
  2. **TRAINING_DATASET 専用 branch**: lineage ∈ demo 系 {BC_ONLY, BC_THEN_RL, **DEMO_PLUS_RL**} → REQUIRED_CLASS / それ以外の lineage → **OPTIONAL**。**else は component = TD の時のみ効く**（他 component に波及しない — scope 明記）。
  3. **TRAINING_PROVENANCE 専用 branch**: lineage = NOT_APPLICABLE → **NOT_APPLICABLE**（RV5-W-P0-2 案 1・N/A ≠ UNKNOWN〔Rs 逐語〕）/ learned lineage → REQUIRED_CLASS。**else は component = TP の時のみ**。
  4. **default branch（残り 11 component 全て — 明示 fallthrough）**: REQUIRED_CLASS。
  - **totality**: 任意の (component, lineage, explicit_none) 入力に**ちょうど 1 branch** が適用される（component-scoped 排他）。
- **profile overlay（eligibility のみ）**: 結果 = **NOT_APPLICABLE**〔classification = N/A **または** §4 表の (component, requested_profile) cell = 「—」〕/ **OPTIONAL**〔classification = OPTIONAL かつ非「—」〕/ **REQUIRED(min_grade = §4 表の値)**〔classification = REQUIRED_CLASS かつ非「—」〕。**certification は overlay を呼ばない**（profile 中立に min_grade は存在しない — B1 の None-profile 未定義 defect を型で閉塞）。
- **RV7 P0-2 優先順位との関係**: 観測上同値 — instance→profile「—」→lineage→default の順は「overlay の dash 優先 + classifier の 3 branch」が実装する（regression vector = §8 corpus + JSON `applicability_rules.regression_vectors`）。
- ⛔ **N/A ≠ UNKNOWN**（v3 W-P0-1 逐語要求）: NOT_APPLICABLE は validated 不存在（集約除外）、UNKNOWN は知識不足（rank 0・失格・免除なし）— 型・集約の両方で区別。
- 旧署名の系譜: `ApplicabilityResolver(kind, lineage, component)`（v3 sketch）→ RV7 P0-2 の 5 引数単関数（register ⑨）→ **本 2 段分割（pN B1 — 5 引数形は classify + overlay の合成として保存**: `resolve_applicability(ik, tl, enc, rp, c) ≡ overlay(classify(ik, tl, enc, c), rp, c)`〔rp 非 None 時〕）。

### 3d. ProofKind 別 payload / binding 規則（B4 + RV6 §3 + pN C1 — grade の自己申告化防止・total 15 kinds）

**claim_target_hash（RV6 §3 — 全 component の単一束縛 anchor; pN C1 の S 系 6 cell 未定義を閉じる機構）**: `EvidenceRecord.claim_target_hash`（旧 artifact_hash を改名）は component 別導出値と**必ず一致**（不一致 = `E_PROOF_MISBOUND`）:

| component | claim_target 導出 |
|---|---|
| POLICY_ARTIFACT | ExecutionBundle.executable_artifact_hash |
| MODEL_ARCHITECTURE / TENSOR_BINDING / NORMALIZATION / RUNTIME_CONFIG | 当該 slot hash |
| TRAINING_DATASET | TrainingProvenance.demo_dataset_hash |
| TRAINING_PROVENANCE | TrainingProvenance.final_artifact_hash |
| OBSERVATION_SCHEMA / ACTION_SCHEMA | H_WCJ(semantic_obs/action_schema) |
| CONTROL_MODE | H_WCJ(control_mode projection) |
| INITIATION_SPEC / TERMINATION_SPEC | H_WCJ(当該 spec) |
| HANDOFF_SCHEMA | H_WCJ(handoff schema projection) |

- **`REPRODUCED_OUTPUT_HASH == claim_target_hash`**（全 component 共通の再現 anchor — S 系 cell に FINAL_ARTIFACT_HASH が無いのは claim_target が anchor を担うため = 定義済み・未定義でない〔pN C1 解消〕）。
- **`TRAIN_RUN_MANIFEST` content は claim_target_hash を列挙**（resolve_artifact で検査 — EXACT の manifest content rule も claim_target に一般化・8 cell 不整合解消）。**`TRAIN_TIME_CRYPTO_BINDING` は (claim_target_hash, manifest_hash) 対を束縛**。

**projection の確定形（RV7 P0-3 → pN 工程 13 B3 で構造化 field map + golden 拡充 — prose placeholder なし）**:
- `control_mode_projection` = **§2.3〔親設計〕slot 直列化そのもの** = keyed object **{"state": literal `"KNOWN"`, "value": ControlMode member 名文字列}**。**slot state を含む**。certified definition の control_mode slot は常に KNOWN（EXPLICIT_NONE は ControlModeSlot に型禁止〔E_SLOT_FORBIDDEN_NONE・親設計 §1.1〕/ UNKNOWN は certify 不能 = Draft のみ）— ゆえ **sentinel 表現は存在せず不要**。**golden vector = ControlMode 全 3 member（total）**: DIFF_IK_EE_TARGET → `4f0b26d50ca9…b6a01c` / SCRIPTED_SEQUENCE → `bea5102d1f91…e233aa` / WAIT → `b3b88e094516…26095c`（full 64-hex + input 全文 = JSON `projection_rules` 掲載）。
- `handoff_schema_projection` = keyed object **`{"handoff_schema": […], "accepted_handoff": […]}`**（**accepted_handoff を含む**）。**構造化 field map（B3 — 実装非依存）**: handoff_schema 要素 = {handoff_schema_id: str, schema_version: str "MAJOR.MINOR", fields: SemanticFieldSpec 配列〔宣言順〕, required_field_ids: str 配列〔UTF-8 bytes 昇順 = frozenset 正準化〕} / SemanticFieldSpec = {field_id: str, dtype: enum member 名, shape: int 配列〔宣言順〕, unit: str, frame: str} / accepted_handoff 要素 = {producer_skill_id: str, handoff_schema_id: str, schema_major_version: int, producer_handoff_schema_hash: str 64-hex}。**array 順序規則**: handoff_schema/accepted_handoff/fields/shape = **宣言順保持**・required_field_ids のみ bytes 昇順（並べ替えは SkillDefinitionHash・BehaviorSignature〔§3-4〕・本 claim target を整合して変える — 第二 canonical 順を作らない）。**空 tuple = `[]`**（EXPLICIT_NONE/UNKNOWN は tuple 型 field に存在しない — state を持つのは slot のみ）。**golden vector 4 本（B3 要求: empty / single / multi-field + accepted 非空 / reorder）**: empty → `76f0ddf30dc7…a06945` / single → `00ffb0154ddb…dfb602d` / multi+accepted → `2c1d77605096…9e615` / **fields 並べ替え → `7a6864771c2a…39619f`（≠ multi — 順序感度の実証対）**（input 全文・dummy hash 由来注記 = JSON 掲載）。
- OBSERVATION/ACTION_SCHEMA・INITIATION/TERMINATION_SPEC の H_WCJ(spec) は §2.3 composite 規則で既に一意 — projection 概念を使わない（typed spec object をそのまま hash）。

**payload 必須性**（違反 = `E_PROOF_PAYLOAD_MISSING`）: **SOURCE_COMMIT のみ artifact_hash = null 必須**（ref = 40-hex commit id が束縛そのもの; ref 形式違反 = `E_PROOF_REF_MALFORMED`。**resolver は artifact 用と別: `resolve_git_commit(commit_id)`** — RV6 §4/expected_sha256 不在問題の解消）。**他 14 kind は artifact_hash 必須**（64-hex 小文字）。ref = 全 kind 非空。

**binding 対象（cross-field coherence; 不一致 = `E_PROOF_MISBOUND`、component に意味を持たない kind の混入 = `E_PROOF_KIND_FOREIGN`）**:

| ProofKind | 束縛対象（certify 時に機械照合） |
|---|---|
| FINAL_ARTIFACT_HASH | **== claim_target_hash**（§3d 冒頭表 — 全 A/P component で単一 anchor に統一; TRAINING_PROVENANCE→final_artifact_hash は learned で == executable、E_PROVENANCE_ARTIFACT_MISMATCH が拘束） |
| REPRODUCED_OUTPUT_HASH | **== claim_target_hash**（§3d 冒頭 — HB grade の核; S 系 component も同 anchor で成立〔pN C1〕） |
| CONFIG_HASH | **total map（G-4/RV6 §4 → RV7 P0-4 で「claimed stage」判別子を廃し (identity_kind, training_lineage, component) の全域 map に確定 — stage field は EvidenceRecord/ProofItem に存在しない**）: **LEARNED × {RL_ONLY, BC_ONLY, DEMO_PLUS_RL}** = `final_training_config_hash`（全 component; BC_ONLY の唯一 stage config — C-CH10 / DEMO_PLUS_RL = 単一 joint stage — B4）/ **LEARNED × BC_THEN_RL** = component = TRAINING_DATASET → `bc_config_hash`（demo dataset は BC stage 入力 — BC config は TD claim が attest）・**他 12 component** → `final_training_config_hash` / **SCRIPTED・WAIT** = `ExecutionProvenance.runtime_config_hash`（親設計 §1.3b — runtime_config slot hash と一致を coherence 検査）。when 節は互いに素・全域（LEARNED × NOT_APPLICABLE は kind-method coherence で不可能） |
| SOURCE_COMMIT | **kind 条件付き（G-4/RV6 §4）**: learned claim = ref == `TrainingProvenance.final_source_commit` / **SCRIPTED・WAIT claim = ref == `ExecutionProvenance.source_commit`**（親設計 §1.3b — 非学習の実行由来を definition 内で固定・registry fixture 依存を解消） |
| INPUT_SCHEMA_HASH / OUTPUT_SCHEMA_HASH | definition の observation / action semantic schema の H_WCJ と一致 |
| NORMALIZER_HASH | normalization slot（KNOWN）の hash と一致（slot EXPLICIT_NONE なら claim 自体 N/A — §3c） |
| TRAIN_TIME_CRYPTO_BINDING | binding blob sha; blob は **(claim_target_hash, TRAIN_RUN_MANIFEST hash) 対**を束縛（R1 — 旧 FINAL 表記を claim_target へ統一; 内容検証 = resolve_artifact 経由） |
| EVALUATOR_ARTIFACT | `EvidenceRecord.evaluator_artifact_hash` と一致 |
| TRAIN_RUN_MANIFEST / REPRODUCTION_PROCEDURE / COMPATIBILITY_TEST / UNRESOLVED_DIFFERENCES / DIMENSION_SOURCE | 当該 file/record の sha256（存在束縛; 内容 coherence = test 層） |
| RECONSTRUCTION_SOURCES | H_WCJ([{path, sha256}…] path bytes 昇順) の集約 hash |

- **negative controls（親設計 §8 corpus 必須）**: (i) wrong-but-valid-hex（形式適合・対象不一致）→ E_PROOF_MISBOUND (ii) null-where-required → E_PROOF_PAYLOAD_MISSING (iii) 他 component 向け kind の混入（例: POLICY_ARTIFACT claim に INPUT_SCHEMA_HASH）→ E_PROOF_KIND_FOREIGN (iv) resolver 不能 artifact → E_PROOF_ARTIFACT_UNRESOLVED（下記）。
- **非学習 skill の到達可能 grade（G-4 の帰結 → pN 工程 13 B2 で機械規則化）**: SCRIPTED/WAIT の A/S 群 component は上記 kind 条件付き束縛により **HASH_BOUND_REPRODUCED(3) まで到達可能**（= CLOSED_LOOP ceiling row 充足可）。**EXACT_TRAIN_TIME(4) は機械的に拒否**: **`identity_kind ∈ {SCRIPTED, WAIT} ∧ grade = EXACT_TRAIN_TIME → E_GRADE_INAPPLICABLE`**（**proof 検査より前に kind × grade 段で拒否** — synthetic な TRAIN_RUN_MANIFEST/TTCB を提出しても EXACT は成立しない。B2: 旧版の prose bound は proof_policy 上で強制されていなかった）。負例 corpus = §8（SCRIPTED × EXACT + synthetic manifest → E_GRADE_INAPPLICABLE）。HB と同 ceiling row〔prereg §4 表〕ゆえ機能的欠損なし。
- **trust boundary（RV5-W-P0-3 gap 3 + RV6 §4/§5 — 「構造 hash 一致だけでは grade は self-asserted」の解消）**: `certify_definition(definition, evidence_bundle, evidence_policy, schema_registry, evaluator_registry, proof_artifact_resolver)`。resolver は **2 種**: `resolve_artifact(ref, expected_sha256) → bytes | UNRESOLVED` / `resolve_git_commit(commit_id) → exists | UNRESOLVED`（SOURCE_COMMIT は hash 無しのため専用 — RV6 §4）。いずれも fail-closed（= `E_PROOF_ARTIFACT_UNRESOLVED`）。certify は hash 構造一致に加え **asserted bytes の実在と内容整合**（manifest の claim_target 列挙 / TTCB の (claim_target, manifest) 束縛 / REPRODUCED == claim_target）を resolver 経由で検査する。**evaluator trust（RV6 §5）**: `EvidenceRecord.evaluator_artifact_hash ∈ evaluator_registry`（∉ = `E_EVALUATOR_UNKNOWN`）、**certificate は `evaluator_registry_hash` を結合**（どの評価器集合を信頼した certificate かを再現可能に）。grade 測定の明示形 = 親設計 §4 の `EvidenceEvaluationCertificate`。standalone test は fixture resolver + fixture registry で全経路実行。
- **grade 測定の閉包（RV7 P0-6 — evaluation certificate の wiring）**: certify は **評価した EvidenceRecord ごとに `EvidenceEvaluationCertificate` を発行**（canonical 順 = component_kind.value bytes 昇順）し、**`EvidenceRecord.grade == assigned_grade` を証明**する（不一致 = **`E_GRADE_MISMATCH`** fail-closed — grade は自己申告でなく評価器の測定値）。発行列は `DefinitionCertificationResult.evidence_evaluations` で返され、**`ContractCertificate.evidence_evaluation_bundle_hash` = H_WCJ(発行列)** が evaluation 束を certificate に固定する。**eligibility（親設計 §5A2）は evaluation certificate の `assigned_grade` のみを使用**（入力 = evidence_evaluations、certificate の bundle hash と照合 — 不一致 = `E_CERT_INPUT_MISMATCH`）。

## 4. Usage profiles（required set + min_grade）

| component | CLOSED_LOOP | SHADOW（非 authority） | OFFLINE_REPLAY |
|---|---|---|---|
| POLICY_ARTIFACT | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| MODEL_ARCHITECTURE | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| OBSERVATION_SCHEMA | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| ACTION_SCHEMA | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| TENSOR_BINDING | ✓ ≥3 | ✓ ≥2 | —（replay は記録済み obs/act を扱い binding を再実行しない） |
| NORMALIZATION | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| CONTROL_MODE | ✓ ≥3 | ✓ ≥2 | —（replay は制御を発行しない — 制御様式の証拠は再生妥当性に効かない） |
| RUNTIME_CONFIG | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| TRAINING_PROVENANCE | **learned lineage のみ** ✓ **≥3**〔B5; SCRIPTED/WAIT = N/A — §3c lineage 層・RV5-W-P0-2〕 | learned lineage のみ ✓ ≥2 | —（来歴は replay 妥当性に効かない; 記録義務は §5） |
| TRAINING_DATASET | demo 系のみ ✓ **≥3**〔B5; 系集合は B4 で拡張〕 | demo 系のみ ✓ ≥2 | — |
| INITIATION_SPEC | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| TERMINATION_SPEC | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| HANDOFF_SCHEMA | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |

- 「**demo 系**」= **{BC_ONLY, BC_THEN_RL, DEMO_PLUS_RL}**（明示列挙 — A-CH8; 旧称「BC 系」を B4 の DEMO_PLUS_RL 追加で改称 — demo dataset を消費する lineage の集合）。
- **EXPLICIT_NONE 免除（C-CH6/D-CH3; typed 形 = §3c ApplicabilityResolver の instance 層）**: 対応 bundle slot が **EXPLICIT_NONE** の component は required set から**免除**される — certified definition 自体（kind 別許容表を通過した契約）が「実体不存在」を attest する。免除は `UsageEligibilityReport` に **loud に記録**（silent skip でない）。これにより SCRIPTED/WAIT は MODEL_ARCHITECTURE / TENSOR_BINDING / NORMALIZATION を免除され、残る required で eligibility を評価できる。UNKNOWN slot に免除は**無い**（知識不足は免除でなく失格）。
- **eligibility の意味論（per-component; C-CH1/B-CH2 + B5 整列）**: profile 充足 ⇔ **免除されない全 required component について、その component の達成 grade ≥ 表の min_grade**（不在 = UNKNOWN(0) = 失格）。**B5 により CLOSED_LOOP 列の min_grade は全 required で ≥3 に整列** — これで per-component 判定の帰結は Rs 確定表（prereg §4）の「必須集合の最弱 grade が bind → matrix 行」読みと**同値**になる（最弱 ≥3 ⇔ RECONSTRUCTED(2) の closed-loop 不可 row を厳守）。旧 v1.1-v1.2 の「TP/TD ≥2 が uniform 読みを精緻化 supersede」は **B5 で撤回**（human-ruled ceiling の変更権限は設計内宣言に無い — 親設計 register ④ の注記参照）。
- 整合: CLOSED_LOOP 全 required ≥3 = Rs 確定表「EXACT/HASH_BOUND = acceptance test 後に可」row。SHADOW の ≥2 = 「RECONSTRUCTED = 非 authority のみ」row（SHADOW は定義上 非 authority）✓。OFFLINE_REPLAY ≥2 = 「可」row ✓。profile 単調: CLOSED_LOOP ⊇ SHADOW ⊇ OFFLINE_REPLAY（免除前の集合比較）。
- usage matrix = ceiling。acceptance test は必要条件の一つ。closed-loop authority は O0/S0/V0 two-key + 独立安全 gate を必ず conjoin。「条件付き」cell 定義は親設計 §4 と同一。

## 5. 記録義務（v1 から不変）
- 全 13 component の EvidenceRecord（UNKNOWN 含む）を常時 bundle に記録（沈黙禁止）。D1-exit は component 別達成 grade を記録（binary 化禁止 — **prereg §10 (c)=P2**〔host 修正 — B-CH1〕）。

## 6. 版管理と hash 二層（v3 W-P1-3 + RV4 §2.3 具体形）
- **`policy_document_sha256`**（RV4 命名） = 本 markdown file の sha256（custody 用 — status/timestamp/編集も拾う）。
- **`evidence_policy_definition_hash`**（RV4 命名） = **H_WCJ(policy_definition)**。**projection は JSON 兄弟 artifact の `policy_definition` object と定義上同一の member 17 個に一意化**（RV6 §2 / pN C2 の二重定義解消; **RV7 P0-3 で `projection_rules` を追加し 16 → 17**）: {policy_semver, grades, component_groups, **claim_targets**, **projection_rules**, proof_policy, **reproduction_rules**, proof_item_canonical_order, proof_conflict_rules, proof_binding, payload_rules, trust_boundary, evaluator_registry_rule, applicability_rules, profiles, exemption_reporting, usage_ceiling}。**metadata（artifact 名・source_markdown・導出 command・掲載 hash 値・informative 注記）は hash 対象外** — metadata 変更 = hash 不変 / validator 挙動を変える規則の変更のみ hash 変化。**現行値 = `e7ca43093084c167a209b008533a66d26a1fd3223d2a3c11274d28306c3ff803`**（header 参照 — banked JSON から実算出。⚠旧値 `066eed1049f4…`〔v1.7 系〕/ `bdc5082008…`〔v1.8 系〕は semantic 変更系譜につき退役）。**validator / ContractCertificate / UsageEligibilityReport が結合するのはこちら**（親設計 §5A/§5A2）。
- **機械可読実体（RV4 §2.3 / RV6 §8-6 訂正）**: **golden JSON fixture = `WMSO_EvidencePolicy_v1.9.json` として存在・bank 済み**（data artifact — 旧「impl 時に作成」文言は fixture 部分について撤回）。impl 時に残るのは **`EvidencePolicyDefinition` frozen dataclass**（fixture の parser/型）と (a) code 定数の H_WCJ == 掲載 definition hash、(b) markdown ↔ JSON ↔ code の三面一致試験（parser artifact hash 記録付き — 親設計 §8）のみ。
- 本 artifact の規則変更は definition hash を変え、既発行 certificate を retroactive に無効化しない。改訂は **prereg §9 の fail-closed re-verify loop**（host 明記 — A-CH4）に従う（design 変更扱い）。
