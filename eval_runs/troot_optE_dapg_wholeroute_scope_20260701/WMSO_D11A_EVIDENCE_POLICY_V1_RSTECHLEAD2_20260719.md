# WMSO D1.1-A EvidencePolicy v1（DESIGN 付属 normative artifact）

- node: `T-WMSO`; author = w2:pQ; created 2026-07-19 10:5x JST（CC Debate cycle-1 U11/U12 fix — debate cycle-2 bundle + pN DESIGN verify の対象）
- 親設計: `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md` v2.2 §4（本 artifact が §4.3「全表」と §4.4「詳細表」の実体。`evidence_policy_hash` = 本 file の sha256）
- status: DRAFT — cycle-2 debate → pS → pN DESIGN verify PENDING

## 1. ProofKind semantics（15 種 — 親設計 §4.2 の enum と 1:1）

| ProofKind | 意味（何を示せば成立か） |
|---|---|
| TRAIN_RUN_MANIFEST | 訓練 run の manifest（開始/終了・env・config 参照を含む一次記録） |
| SOURCE_COMMIT | 訓練時 source の commit id（repo 実在） |
| CONFIG_HASH | 訓練 config の sha256 |
| INPUT_SCHEMA_HASH | 訓練時 観測 schema の sha256 |
| OUTPUT_SCHEMA_HASH | 訓練時 行動 schema の sha256 |
| NORMALIZER_HASH | normalizer state の sha256 |
| FINAL_ARTIFACT_HASH | 対象 artifact（weights / dataset / config 等、component に応じた「物」）の sha256 |
| TRAIN_TIME_CRYPTO_BINDING | 訓練時に生成された暗号学的束縛（hash chain / signed manifest） |
| REPRODUCTION_PROCEDURE | 再現手順書（実行可能な手続き） |
| REPRODUCED_OUTPUT_HASH | 再現実行の出力 sha256（一致証明） |
| RECONSTRUCTION_SOURCES | 復元に用いた現存資料の列挙（path+sha） |
| COMPATIBILITY_TEST | 互換性試験の記録（手順+結果） |
| UNRESOLVED_DIFFERENCES | 未解決差分の明示列挙（空なら「なし」と明記） |
| DIMENSION_SOURCE | 次元数の出所（checkpoint shape 等） |
| EVALUATOR_ARTIFACT | 評価器実装の sha256（EvidenceRecord.evaluator_artifact_hash と一致必須） |

## 2. component 群（13 component を 3 群に分類）

- **A: artifact 系**（「物」がある）= POLICY_ARTIFACT / MODEL_ARCHITECTURE / NORMALIZATION / TRAINING_DATASET / RUNTIME_CONFIG / TENSOR_BINDING
- **S: schema/spec 系**（意味定義）= OBSERVATION_SCHEMA / ACTION_SCHEMA / INITIATION_SPEC / TERMINATION_SPEC / HANDOFF_SCHEMA / CONTROL_MODE
- **P: provenance 系** = TRAINING_PROVENANCE

## 3. ProofPolicy — (component_kind, grade) → required ProofKind set（total 定義）

規則形で全 65 cell を定義する（表外 cell は存在しない）。requires(群, grade) =

| grade | A: artifact 系 | S: schema/spec 系 | P: TRAINING_PROVENANCE |
|---|---|---|---|
| EXACT_TRAIN_TIME | TRAIN_RUN_MANIFEST + SOURCE_COMMIT + CONFIG_HASH + FINAL_ARTIFACT_HASH + TRAIN_TIME_CRYPTO_BINDING | TRAIN_RUN_MANIFEST + SOURCE_COMMIT + (INPUT_SCHEMA_HASH if OBSERVATION_SCHEMA / OUTPUT_SCHEMA_HASH if ACTION_SCHEMA / CONFIG_HASH otherwise) | TRAIN_RUN_MANIFEST + SOURCE_COMMIT + FINAL_ARTIFACT_HASH + TRAIN_TIME_CRYPTO_BINDING |
| HASH_BOUND_REPRODUCED | CONFIG_HASH + FINAL_ARTIFACT_HASH + REPRODUCTION_PROCEDURE + REPRODUCED_OUTPUT_HASH + EVALUATOR_ARTIFACT | REPRODUCTION_PROCEDURE + REPRODUCED_OUTPUT_HASH + (INPUT_SCHEMA_HASH / OUTPUT_SCHEMA_HASH / CONFIG_HASH — 同上の対応) + EVALUATOR_ARTIFACT | CONFIG_HASH + FINAL_ARTIFACT_HASH + REPRODUCTION_PROCEDURE + EVALUATOR_ARTIFACT |
| RECONSTRUCTED_COMPATIBLE | RECONSTRUCTION_SOURCES + COMPATIBILITY_TEST + UNRESOLVED_DIFFERENCES + EVALUATOR_ARTIFACT | RECONSTRUCTION_SOURCES + COMPATIBILITY_TEST + UNRESOLVED_DIFFERENCES + EVALUATOR_ARTIFACT | RECONSTRUCTION_SOURCES + UNRESOLVED_DIFFERENCES + EVALUATOR_ARTIFACT |
| DIMENSION_ONLY | DIMENSION_SOURCE（+ semantic unresolved 宣言 = UNRESOLVED_DIFFERENCES） | 同左 | （P に DIMENSION_ONLY は無意味 → **認定不可** = `E_GRADE_INAPPLICABLE`） |
| UNKNOWN | （無条件 — authority-relevant claim 一切不可） | 同左 | 同左 |

- component 個別の追加要求（群規則への上書き、これで total）: **NORMALIZATION**@EXACT は + NORMALIZER_HASH。**TRAINING_DATASET**@{EXACT, HASH_BOUND} の FINAL_ARTIFACT_HASH = dataset の sha256。**TENSOR_BINDING / CONTROL_MODE / RUNTIME_CONFIG**@EXACT は TRAIN_RUN_MANIFEST 内の該当節 or CONFIG_HASH で足りる（独立 manifest を要求しない — 訓練 config に含まれる性質のため）。
- 不足 = `E_PROOF_INSUFFICIENT`（1 段下の grade で再提出可 — 単調）。
- **1 component = 1 certified claim**（重複 = `E_EVIDENCE_DUPLICATE`）。複数根拠 = claim 内 ProofItem 列。duplicate proof（同 kind 同 ref）は冪等単一。`notes` は evidence_bundle_hash 対象外。
- **grade rank（明示）**: EXACT_TRAIN_TIME=4 > HASH_BOUND_REPRODUCED=3 > RECONSTRUCTED_COMPATIBLE=2 > DIMENSION_ONLY=1 > UNKNOWN=0。
- **evidence record 不在の required component は UNKNOWN(0) として集約**（missing = 最弱、fail-closed）。

## 4. Usage profiles（required set + min_grade — 親設計 §4.4 の「以上」を閉じる）

| component | CLOSED_LOOP | SHADOW（非 authority） | OFFLINE_REPLAY |
|---|---|---|---|
| POLICY_ARTIFACT | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| MODEL_ARCHITECTURE | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| OBSERVATION_SCHEMA | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| ACTION_SCHEMA | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| TENSOR_BINDING | ✓ ≥3 | ✓ ≥2 | —（replay は binding 不要 — 記録 obs/act の次元・意味は schema 側で判定） |
| NORMALIZATION | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| CONTROL_MODE | ✓ ≥3 | ✓ ≥2 | — |
| RUNTIME_CONFIG | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| **TRAINING_PROVENANCE** | **✓ ≥2**（U12 — lineage 自己申告の根絶） | ✓ ≥2 | —（provenance は replay 妥当性に効かない — 記録は §5 参照） |
| TRAINING_DATASET | BC 系 lineage のみ ✓ ≥2 | BC 系のみ ✓ ≥2 | — |
| INITIATION_SPEC | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| TERMINATION_SPEC | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |
| HANDOFF_SCHEMA | ✓ ≥3 | ✓ ≥2 | ✓ ≥2 |

（数値 = min grade rank。✓ = required。— = not required。）

- 整合確認: CLOSED_LOOP ≥3 = HASH_BOUND 以上（Rs 確定表「acceptance test 後に可」の hash 系 2 grade に一致）。SHADOW/REPLAY ≥2 = RECONSTRUCTED 以上（確定表: RECONSTRUCTED = 非 authority shadow 可 / replay 可。DIMENSION_ONLY(1) は required set を満たせない = 診断のみ、UNKNOWN(0) 不可）。**profile は monotone**: CLOSED_LOOP ⊇ SHADOW ⊇ OFFLINE_REPLAY の required 包含が成立（TENSOR_BINDING/CONTROL_MODE/TRAINING_DATASET/TRAINING_PROVENANCE の除外は下位 profile のみ）。
- **usage matrix = ceiling**。profile 充足は必要条件 — closed-loop authority は acceptance test + O0/S0/V0 two-key + 独立安全 gate を必ず conjoin（grant ではない）。
- 「条件付き」cell の意味（親設計 §4.4 から継承）: 「acceptance test 後に可」= 独立 acceptance test PASS が追加必要条件 / 「非 authority のみ」= 出力が制御に接続されない記録・比較 mode 限定 / 「診断のみ」= replay 入力にも使わず次元・形式診断限定。

## 5. 記録義務（profile 外でも常時）
- 全 13 component の EvidenceRecord（UNKNOWN 含む）を bundle に**常時記録**する（profile が要求しない component も、不在でなく UNKNOWN として明示 — 沈黙禁止）。
- D1-exit は component 別達成 grade を記録（binary 化禁止 — 親設計 P2）。

## 6. 版管理
- 本 artifact の変更は `evidence_policy_hash` を変え、既発行 ContractCertificate を retroactive に無効化しない（certificate は発行時 policy hash を持つ）。新規発行は最新 policy による。
- 改訂は親設計の §9 fail-closed re-verify loop に従う（design 変更扱い）。
