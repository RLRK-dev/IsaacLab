# WMSO D1.1-A EvidencePolicy v1.4（DESIGN 付属 normative artifact）

- node: `T-WMSO`; author = w2:pQ; v1 = 2026-07-19 10:54 JST / v1.1 = 12:02 / v1.2 = 12:41 / v1.3 = 13:33 / **v1.4 = 14:00 JST（実測）**（Rs PLAN_STATUS review v4〔RV4〕fold: §2.3 機械可読 policy object 具体形 / §2.8 順序文字列 pin。v1.3 = pN B4/B5/B6 fold）
- 親設計: `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md` v2.4 §4（本 artifact が全表の normative 実体。custody hash = 本 file の sha256、validator/certificate が結合するのは §6 の **semantic hash**）
- status: DRAFT v1.2 — pS 全行照合（v3 行込み）→ pN DESIGN verify PENDING
- v1 からの変更: §3 の 3 cell exact 化 / DC-3 準拠復元 / §3b ProofItem 順序・conflict 規則 / §4 EXPLICIT_NONE 免除 / §4b per-component 意味論の明示 / E_GRADE_INAPPLICABLE の S-group 拡張 / 引用 host 修正。v1.1 からの変更: §3c ApplicabilityResolver（v3 W-P0-1 sketch 採用）/ §3 total-map 宣言 + cell 表記の置換/補完 意味明示（v3 W-P0-5）/ §6 semantic hash 分離（v3 W-P1-3）

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

### 3c. ApplicabilityResolver（v3 W-P0-1 — Rs sketch 採用）

```text
ApplicabilityResolver(kind, lineage, component)
  -> REQUIRED(min_grade) | NOT_APPLICABLE | OPTIONAL
```

- **解決規則（優先順・全て機械判定）**:
  1. **instance 層**: certified definition の対応 slot が **EXPLICIT_NONE**（kind 別許容表 + 証拠 gate〔LEARNED は E_SLOT_NONE_UNPROVEN〕を通過済み）→ **NOT_APPLICABLE**。certificate の `explicit_none_components` が attest を運ぶ（§4 の免除と同一機構 — 名前を resolver に統一）。
  2. **lineage 層**: TRAINING_DATASET は lineage ∈ BC 系 {BC_ONLY, BC_THEN_RL} → REQUIRED(min_grade = §4 表の profile 別値〔B5 整列後〕)、それ以外の lineage → **OPTIONAL**（記録可・集約外）。
  3. **profile 層**: §4 表の「—」cell（TB/CM/TP@OFFLINE_REPLAY 等、理由明記済み）→ その profile では NOT_APPLICABLE。
  4. 上記非該当 → **REQUIRED(min_grade = §4 表の値)**。
- ⛔ **N/A ≠ UNKNOWN**（v3 W-P0-1 逐語要求）: NOT_APPLICABLE は「実体が存在しない事の validated proof（kind 別許容表 + 証拠 gate 通過）」であり、UNKNOWN（知識不足 = 失格・免除なし）と型・集約の両方で区別する。
- 本 resolver は §4 の EXPLICIT_NONE 免除規則の**typed API 形**（同一 semantics の名前付け — supersession でない）。

### 3d. ProofKind 別 payload / binding 規則（B4 — grade の自己申告化防止・total 15 kinds）

**payload 必須性**（違反 = `E_PROOF_PAYLOAD_MISSING`）: **SOURCE_COMMIT のみ artifact_hash = null 必須**（ref = 40-hex commit id が束縛そのもの; ref 形式違反 = `E_PROOF_REF_MALFORMED`）。**他 14 kind は artifact_hash 必須**（64-hex 小文字）。ref = 全 kind 非空（artifact の所在/識別子）。

**binding 対象（cross-field coherence; 不一致 = `E_PROOF_MISBOUND`、component に意味を持たない kind の混入 = `E_PROOF_KIND_FOREIGN`）**:

| ProofKind | 束縛対象（certify 時に機械照合） |
|---|---|
| FINAL_ARTIFACT_HASH | component 対応 slot/field の hash と一致: POLICY_ARTIFACT→executable_artifact_hash / MODEL_ARCHITECTURE・TENSOR_BINDING・NORMALIZATION・RUNTIME_CONFIG→当該 slot hash / TRAINING_DATASET→TrainingProvenance.demo_dataset_hash |
| CONFIG_HASH | TrainingProvenance の claimed stage config hash（BC=bc_config_hash 等・family 依存）と一致 |
| INPUT_SCHEMA_HASH / OUTPUT_SCHEMA_HASH | definition の observation / action semantic schema の H_WCJ と一致 |
| NORMALIZER_HASH | normalization slot（KNOWN）の hash と一致（slot EXPLICIT_NONE なら claim 自体 N/A — §3c） |
| REPRODUCED_OUTPUT_HASH | **HB grade の核**: 対応する FINAL_ARTIFACT_HASH の値と一致（byte-repro の定義） |
| TRAIN_TIME_CRYPTO_BINDING | binding blob sha; blob は (FINAL_ARTIFACT_HASH 値, TRAIN_RUN_MANIFEST 値) を束縛（内容検証 = test 層） |
| EVALUATOR_ARTIFACT | `EvidenceRecord.evaluator_artifact_hash` と一致 |
| TRAIN_RUN_MANIFEST / REPRODUCTION_PROCEDURE / COMPATIBILITY_TEST / UNRESOLVED_DIFFERENCES / DIMENSION_SOURCE | 当該 file/record の sha256（存在束縛; 内容 coherence = test 層） |
| RECONSTRUCTION_SOURCES | H_WCJ([{path, sha256}…] path bytes 昇順) の集約 hash |

- **negative controls（親設計 §8 corpus 必須）**: (i) wrong-but-valid-hex（形式適合・対象不一致）→ E_PROOF_MISBOUND (ii) null-where-required → E_PROOF_PAYLOAD_MISSING (iii) 他 component 向け kind の混入（例: POLICY_ARTIFACT claim に INPUT_SCHEMA_HASH）→ E_PROOF_KIND_FOREIGN。

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
| TRAINING_PROVENANCE | ✓ **≥3**〔B5〕 | ✓ ≥2 | —（来歴は replay 妥当性に効かない; 記録義務は §5） |
| TRAINING_DATASET | BC 系のみ ✓ **≥3**〔B5〕 | BC 系のみ ✓ ≥2 | — |
| INITIATION_SPEC | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| TERMINATION_SPEC | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| HANDOFF_SCHEMA | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |

- 「**BC 系**」= **{BC_ONLY, BC_THEN_RL}**（明示列挙 — A-CH8）。
- **EXPLICIT_NONE 免除（C-CH6/D-CH3; typed 形 = §3c ApplicabilityResolver の instance 層）**: 対応 bundle slot が **EXPLICIT_NONE** の component は required set から**免除**される — certified definition 自体（kind 別許容表を通過した契約）が「実体不存在」を attest する。免除は `UsageEligibilityReport` に **loud に記録**（silent skip でない）。これにより SCRIPTED/WAIT は MODEL_ARCHITECTURE / TENSOR_BINDING / NORMALIZATION を免除され、残る required で eligibility を評価できる。UNKNOWN slot に免除は**無い**（知識不足は免除でなく失格）。
- **eligibility の意味論（per-component; C-CH1/B-CH2 + B5 整列）**: profile 充足 ⇔ **免除されない全 required component について、その component の達成 grade ≥ 表の min_grade**（不在 = UNKNOWN(0) = 失格）。**B5 により CLOSED_LOOP 列の min_grade は全 required で ≥3 に整列** — これで per-component 判定の帰結は Rs 確定表（prereg §4）の「必須集合の最弱 grade が bind → matrix 行」読みと**同値**になる（最弱 ≥3 ⇔ RECONSTRUCTED(2) の closed-loop 不可 row を厳守）。旧 v1.1-v1.2 の「TP/TD ≥2 が uniform 読みを精緻化 supersede」は **B5 で撤回**（human-ruled ceiling の変更権限は設計内宣言に無い — 親設計 register ④ の注記参照）。
- 整合: CLOSED_LOOP 全 required ≥3 = Rs 確定表「EXACT/HASH_BOUND = acceptance test 後に可」row。SHADOW の ≥2 = 「RECONSTRUCTED = 非 authority のみ」row（SHADOW は定義上 非 authority）✓。OFFLINE_REPLAY ≥2 = 「可」row ✓。profile 単調: CLOSED_LOOP ⊇ SHADOW ⊇ OFFLINE_REPLAY（免除前の集合比較）。
- usage matrix = ceiling。acceptance test は必要条件の一つ。closed-loop authority は O0/S0/V0 two-key + 独立安全 gate を必ず conjoin。「条件付き」cell 定義は親設計 §4 と同一。

## 5. 記録義務（v1 から不変）
- 全 13 component の EvidenceRecord（UNKNOWN 含む）を常時 bundle に記録（沈黙禁止）。D1-exit は component 別達成 grade を記録（binary 化禁止 — **prereg §10 (c)=P2**〔host 修正 — B-CH1〕）。

## 6. 版管理と hash 二層（v3 W-P1-3 + RV4 §2.3 具体形）
- **`policy_document_sha256`**（RV4 命名） = 本 markdown file の sha256（custody 用 — status/timestamp/編集も拾う）。
- **`evidence_policy_definition_hash`**（RV4 命名; 旧称 evidence_policy_semantic_hash） = **H_WCJ(policy_object)**。policy_object = keyed object {`grades`（rank 付き列挙）, `component_groups`, `proof_policy`（§3 total map の REQUIRED cell 全列挙）, `proof_binding`（§3d の payload/束縛規則）, `profiles`（§4 required/min_grade 表）, `applicability_rules`（§3c の 1-4）, `policy_semver`}。文書編集で変わらず、**規則が変わった時のみ変わる**。**validator / ContractCertificate / UsageEligibilityReport が結合するのはこちら**（親設計 §5A/§5A2）。
- **機械可読実体（RV4 §2.3 Required）**: impl 時に **`EvidencePolicyDefinition` frozen dataclass + golden JSON fixture**（`WMSO_EvidencePolicy_v1.x.json`）を作成し、(a) fixture の H_WCJ == 本 §6 の definition hash、(b) **本 markdown 表 ↔ code 内定数の一致試験**（parser artifact hash 記録付き）を standalone test に含める（親設計 §8）。⛔ impl CLOSED 中は作成しない — 本項は設計 requirement の pin のみ。
- 本 artifact の規則変更は definition hash を変え、既発行 certificate を retroactive に無効化しない。改訂は **prereg §9 の fail-closed re-verify loop**（host 明記 — A-CH4）に従う（design 変更扱い）。
