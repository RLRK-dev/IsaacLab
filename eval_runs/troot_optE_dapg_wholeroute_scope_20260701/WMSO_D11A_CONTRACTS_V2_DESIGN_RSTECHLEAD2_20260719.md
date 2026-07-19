# WMSO D1.1-A `contracts_v2` — DESIGN (v2.9.2)

- node: `T-WMSO`; author = w2:pQ (RS-TECH-LEAD2)
- created: v1 = 2026-07-19 09:09 JST / v1.1 = 09:24 / v2 = 09:32 / v2.1 = 09:43 / v2.2 = 10:59（editing 完了実測; 旧「10:5x」表記を確定 — 以後 x-mask 廃止）/ v2.3 = 12:07 / v2.4 = 12:41（12:31 に v2.3.1 として着手後、Rs review v3 着信により拡張）/ v2.4.1 = 13:07 / v2.5 = 13:36 / v2.6 = 14:16 / v2.7 = 14:36 / v2.7.1 = 15:46 / v2.8 = 16:07 / v2.9 = 16:52 / v2.9.1 = 17:21（pS H-1..H-3 fold）/ **v2.9.2 = 17:35 JST（実測 — pN R1-R3 fold: EP 旧重複行統一 / enum member 全数 inline / 版数 3 面同期）**
- **status: DESIGN DRAFT v2.9.2（R3: 本行 = title と同期）— fold 系譜 = RV6 + pN C1-C3（v2.9）→ pS §14 H-1..H-3（v2.9.1）→ **pN 最終 pin ⛔HOLD R1-R3（17:30）の fold = 本版**。⚠**Rs の RV6 §10 は本 fold の目標版を「v2.8/EP v1.6」と命名したが、当該ラベルは直前の pS-G fold（交差）が消費済み → 実版 = v2.9/EP v1.7**（版名 collision の loud 記録）。⭐RV6 §10 逐語「これ以上一般的に精緻化せず、証拠束縛・handoff・migration の閉包だけを直して freeze」 → pS 照合 → pN 再 verify（最終 SHA 宛）→ **freeze** PENDING**
- governing scope: `WMSO_D11_CONTRACT_V2_SCOPE_PREREG_RSTECHLEAD2_20260719.md` v3.2.2, sha256 `71097e58102e100657177b7ead2484bcc00840e4a788e6a295d944f7827d0966`, commit `ea6e39b93c`
- 兄弟 normative artifacts（pN DESIGN verify の対象; full 64-hex — B-CH5）:
  - **Rs review-4 transcript** = `WMSO_RS_REVIEW4_DESIGN_TRANSCRIPT_20260719.md`, sha256 `8a7915dfa3386889d4efe3cbacb063c0ea20df0f138c8099b84ec64cbab5ad50`（as-received 転記・**bank `ac5865b66d`・file 本体は以後不変**。**fidelity = SEMANTIC FIDELITY CONFIRMED / BYTE IDENTITY N/A — 状態の正 = `WMSO_RS_REVIEW4_FIDELITY_CONFIRM_20260719.md`**〔RV6 §1 形式・§8-3 の表記分岐解消〕）
  - **Rs PLAN_STATUS review v2（W 系）** = `WMSO_RS_PLAN_STATUS_REVIEW_V2_COPY_20260719.md`, sha256 `dc57d8e10c5ba84d1d66a3977c9ccd98dac24c0bd15f53b0bba9711922e987b6`（bank `320545b477`; **byte-identical file copy — 転記でないため fidelity 確認不要**）〔R-1: full 64-hex 化〕
  - **Rs PLAN_STATUS review v3（W'-系; 対象 = v2.2 + EP v1・supervening）** = `WMSO_RS_PLAN_STATUS_REVIEW_V3_COPY_20260719.md`, sha256 `20da075f9566904e508e22c80cabce9d04d4d61ee9d306268a1a6fe311c6230b`（原本 `~/Downloads/PLAN_STATUS_review_v3_2026-07-19.md` の **byte-identical file copy** — fidelity 確認不要。⚠ **v3 の W-P0-n/W-P1-n は review v2 と別番号系** — 本 doc では常に「v3 W-」接頭辞で引用〔混同防止〕）
  - **Rs PLAN_STATUS review v4（RV4; 対象 = v2.3 + EP v1.1 期 package）** = `WMSO_RS_PLAN_STATUS_REVIEW_V4_COPY_20260719.md`, sha256 `338bdaf75a993ac2a0871d7cc975fd13fb464063323fc59ad7a356996c4f860c`（原本 `~/Downloads/PLAN_STATUS_review_v4_2026-07-19.md` の byte-identical file copy — fidelity 確認不要）
  - **Rs PLAN_STATUS review v5（RV5; 対象 = v2.5+EP v1.3 期 package）** = `WMSO_RS_PLAN_STATUS_REVIEW_V5_COPY_20260719.md`, sha256 `44792e860e82fe57ce99abb1516f6cc848025439037906d40b6668c9a570689b`（byte-identical file copy — fidelity 確認不要）
  - **pN DESIGN HOLD B1-B7 transcript** = `WMSO_PN_DESIGN_VERIFY_HOLD_B1B7_TRANSCRIPT_20260719.md`（as-received 転記 — RV5 C-P0-1 の解消; **pN 著者 readback = SEMANTIC FIDELITY CONFIRMED、15:42**）
  - **Rs review v6（RV6）** = `WMSO_RS_REVIEW_V6_COPY_20260719.md`, sha256 `3f64cbca44269bc8255fd2c0dcf4d96712248de4017d4b1943c0855daef2cead`（byte-identical file copy — fidelity 確認不要）
  - **review-4 fidelity 確認 record** = `WMSO_RS_REVIEW4_FIDELITY_CONFIRM_20260719.md`（RV6 §1 推奨形式 — transcript 本体は不変のまま別 record で CONFIRMED 固定; header/manifest の状態表記はこれを指す〔RV6 §8-3 の分岐解消〕）
  - **pN HOLD C1-C3 transcript** = `WMSO_PN_DESIGN_VERIFY_HOLD_C1C3_TRANSCRIPT_20260719.md`（as-received 転記 — pS §14 H-3 の解消; **pN 確認 PENDING**〔再 verify と併せ依頼〕）
  - **EvidencePolicy v1.7.1** = `WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md`（sha = bank commit で確定・毎版更新）+ **機械可読 fixture `WMSO_EvidencePolicy_v1.7.json`**（二層 {metadata, policy_definition}; **`evidence_policy_definition_hash` = `066eed1049f4f51a89dd86e9d50614a65adba070b2ff650424ea7cef05dec4ea`**〔実算出・掲載・metadata 編集で不変 — pN C2/独立再計算一致〕; **file sha256 = `ed10c77a4d9957368380195ee081368da3fdaa170b03ec275584e08d1c301faa`**〔H-2 — metadata の source_markdown v1.7.1 化で更新・definition hash は不変を再計算確認〕）
  - pS design-verify record = `WMSO_D11A_DESIGN_VERIFY_WMSODESIGN_20260719.md`（最終 bank = **本 v2.8 commit**〔§12 込み・G-3 fix; 以後 pS addendum 毎に同 commit で re-bank〕; 現行版は pS 管理 — B-CH1 の host pin）
- version 履歴: v1 (prefix `8bec472a6ac1` — content 非保全) → v1.1 (prefix `b807ce2abbd7` — 同) → v2 (prefix `4880dc0d6c6d` — 同) → v2.1 (full `c49ff132ff200257085f072c875c58e3200754ac74ee28de8634b786ab2681e7`, bank `cd5482310d`) → v2.2 (full `3a1577f89dfa3d3c7fa642c938f56a4ff05ab60e14b57194cb3368f7ddcb95f3`, bank `ac5865b66d`) → v2.3 (full `94a42a0ea73a08d2b85be562373322c5ebfd65f49393183b9cf7fff68040f192`, bank `efc355e52d`; **pS 全行照合 = PASS-WITH-CONDITIONS R-1..R-3**〔verify record §9〕) → v2.4 (full `772f346c32cf15f11e3c62fa14ed1342f87b7bcf0acc9e8d0ea2a93f885986d7`, bank `130813e934`; **pS 全行照合 = PASS-WITH-CONDITIONS F-1/F-2**〔verify record §10, sha `609e7a35722b…`; R-1..R-3 = 3/3 discharge・register ⑥ 解 = 検証済で pS 推奨より正当・v3 9 項 = faithful〕) → v2.4.1 (full `8310cb6fd3f8f23929fc1479f734141e481d9b3641f3227d798e311084dad15c`, bank `ba10218549`; **pS FINAL CONFIRM = PASS**〔record §11〕→ **pN DESIGN verify = ⛔HOLD B1-B7**〔13:26 実測・時刻訂正済; 全項 pQ on-disk 検証で真〕) → v2.5 (full `2f0a706833b024f25e992c29791dfd2ab0837622ac5e58f2bea2abfd97c1dfac`, bank `59b7720408` — B1-B7 fold + pS record bank) → v2.6 (full `9c8a18f83bbf1555b9adaadf72f9244a3ec8ea09dc26922e83b9a1435e98f975`, bank `51008ace1f` — RV4 fold + full self-contained 化) → v2.7 (full `5b4568903e6c1ac321106d418a8fa3e583067cffb770a994fd3fd1f402a46c59`, bank `e0257b5648` — RV5 fold) → v2.7.1 (full `64e2b005d6dd7f7a64dc884356e860da43762638c328a215ba5b464fd8164ac3`, bank `86d127b5c0`; **pS §12 全区間 re-check = PASS-WITH-CONDITIONS G-1..G-4**〔record sha `98e47cace83a…`〕) → v2.8 (full `24f5fd3d8e8ec85034bdb53cfb65d47a6636529c2aa366e9212cf1d271515fef`, bank `ba99db30f6` — G fold; **pS §13 FINAL CONFIRM = PASS** → **pN 再 verify = ⛔HOLD C1-C3**〔16:26〕) → v2.9 (full `e64c192b62e754da8050041985dd9028a67bf12c287d55bcbc1579c660b8de46`, bank `8caa19a7a4` — RV6+C 統合 fold; **pS §14 = PASS-WITH-CONDITIONS H-1..H-3**〔record sha `f6028b096032…`; hash 独立再計算一致 = airtight〕) → v2.9.1 (full `0da79321038950a916b64c36096e9bbd23d095f7e09f13cfaea24696917a956e`, bank `ea30e7fdc3` — H fold; **pN 最終 pin = ⛔HOLD R1-R3**〔17:30; custody/hash/transcript legs = PASS・C2 CLOSE〕) → **v2.9.2 (本版 — R fold: EP 重複行統一 / enum 全数 inline / 版数 3 面同期)**。以後毎版 bank。
- **review ID 完全修飾規約（RV4 §1.3）**: Rs review 引用は **RV2- / RV3- / RV4- / R4-（review-4 transcript）** 接頭辞で完全修飾する。本 doc 既出の「W-P0-n（v2 系）」= RV2-W-P0-n、「v3 W-P0-n」= RV3-W-P0-n と同値（fold-map §11 で対応）。
- 駆動要件（host 付き — B-CH1/A-CH5 修正）: prereg §2 IN / prereg §10 (a)-(d)〔旧ラベル §5b〕/ N-1・N-2（= **pS ratify doc §8 ADDENDUM C1** の carried 2 点）/ DC-1..DC-6（**prereg §10b**）/ review-4 P0・P1・T・OP（transcript）/ **W-P0-1..4・W-P1-1..6（W-review copy — supervening Rs review）**/ **RV3 = v3 W-P0-1..6・v3 W-P1-1..3（review v3 copy; §11 W'→fold-map）**/ **RV4 全項（review v4 copy; §11 RV4→fold-map）**/ **RV5 全項（review v5 copy; §11 RV5→fold-map）**/ **RV6 全項（review v6 copy — 最後発 supervening; §11 RV6→fold-map）**/ **pN C1-C3（§11 C→fold-map）**/ pS D・V・R・F 系 / **pN DESIGN verify B1-B7（§11 B→fold-map）**/ CC Debate cycle-1 U1-U19 + cycle-2 findings（verification-log task-WMSO-D11A-design-debate-001 cycle 1・2; **cycle-1 の記録上 overall = "REVIEW"** — accepted CRITICAL を skill 表で FAIL 扱いした運用注記 = D-CH7）。「review-1 P0-n」（v1 コード欠陥）と「review-4 P0-n」（設計修正）は別番号系 — 常に接頭辞付き。
- **SSOT supersession register（enumerated-only — B-CH6/NHA）**: 本 design が prereg 文言を supersede するのは**以下に列挙した点のみ**。未記録の分岐 = 欠陥であり precedence では解決しない（prereg §9 loop へ）。① DC-2 timing（TENSOR_BINDING/CONTROL_MODE enum 即時追加）— **B1 で典拠を再接地: prereg §10b DC-2 自身の「§4 の 7 component は『最低限』」floor 文言により即時追加は floor 内で整合（supersession でなく floor 内追加へ再分類; transcript P0-4 は補強典拠に降格 — 未確認 transcript への normative 依存を除去）**② prereg §5 表 7→5 行（DC-5 実行）③ prereg §7b「SkillDefinitionHash」→ draft_definition_hash 読み（§6-8）④ **〔B5 で撤回・整列済〕** 旧「per-component min_grade（TP/TD ≥2）が prereg §4 uniform 読みを精緻化 supersede」は **human-ruled ceiling の変更権限が設計内宣言に無く不成立** — EvidencePolicy v1.3 で CLOSED_LOOP 全 required min_grade ≥3 に整列し、per-component 判定は Rs 確定表と**同値**（supersession 消滅。per-component は評価機構としてのみ残る）⑤ **DC-6 の bounded 例外 = §6-4 の retained-in-v1 guard（D1.1-C 後継まで; D-CH2）**⑥ **review v2 W-P0-2 sketch の `external_gate_state` 引数 → review v3 W-P0-3 sketch（4 引数・「Acceptance tests, O0/S0/V0 two-key, and safety gates remain external conjuncts」）が supersede**（Rs 自身の後発 text; pS R-2 の推奨〔v2 sketch 採用〕より優先 — §5A2）⑦ **prereg §10b DC-2 の文言「evidence_policy_hash」→ certificate は `evidence_policy_definition_hash` を結合**（RV3-W-P1-3 が典拠・命名 = RV4 §2.3; policy_document_sha256 は custody 層に残置 — F-2）。EvidencePolicy の表実体は §4 の規則どおり artifact 側が normative。
- **self-contained 宣言（RV4 §2.4 — 旧 参照規約を置換）**: v2.6 は **normative 内容を全て本 doc + 兄弟 artifact に inline** した完全 snapshot である（transfer package 単体で再構築可能 — repo/git show 不要）。旧「v2.2 のまま」pointer は本版で全 inline 済み（歴史 blob = `ac5865b66d`、参照は provenance 用のみ）。
- ⛔ 本 doc は設計のみ。code / [CHANGE] / impl は pN DESIGN PASS → pre-check → rule-check → path freeze / impl GO まで CLOSED。

---

## 0. 中心構造（review-4 + W-P0-2 の確定形）

```text
Static:        DraftSkillDefinition（UNKNOWN 可・final ActionId なし）/ SkillDefinition
Provenance:    TrainingProvenance / EvidenceBundle / EvidencePolicy（兄弟 artifact）
Certification: certify_definition() → ValidationReport → (valid のみ) ContractCertificate   … profile 中立（W-P0-2）
Eligibility:   evaluate_usage_eligibility() → UsageEligibilityReport                       … profile 別・certificate-first・現行 policy で評価（RV2-W-P0-2 / RV3-W-P0-3）
Authority:     evaluate_authority_grant() → AuthorityDecision                              … RV4 §2.2 — eligibility と権限付与を型で分離（gate 群はこちらの入力）
Runtime:       SkillInvocation / SkillOutcome / HandoffOffer / TransitionRecord
Runtime val.:  validate_invocation_start(now) / validate_outcome() / validate_handoff()     … certificate を無効化しない
```

---

## 1. Static 型

### 1.1 Slot（W-P1-2 反映）

```python
class SlotState(Enum): KNOWN | EXPLICIT_NONE | UNKNOWN
@dataclass(frozen=True)
class ArtifactSlot:      state: SlotState; artifact_hash: str | None   # KNOWN ⇔ 64-hex (E_SLOT_INCONSISTENT)
@dataclass(frozen=True)
class ControlModeSlot:   state: SlotState; value: ControlMode | None   # KNOWN|UNKNOWN のみ (E_SLOT_FORBIDDEN_NONE)
@dataclass(frozen=True)
class CallableSlot:      state: SlotState; selector: str | None        # B2: KNOWN ⇔ canonical selector（形式 = §1.2）
```

### 1.2 ExecutionBundle

```python
class ControlMode(Enum): DIFF_IK_EE_TARGET | SCRIPTED_SEQUENCE | WAIT
@dataclass(frozen=True)
class ExecutionBundle:
    kind: IdentityKind
    executable_artifact_hash: str       # 常に必須 KNOWN。LEARNED = weights sha256 / SCRIPTED,WAIT = closure aggregate (§3-2)
    model_architecture: ArtifactSlot
    tensor_binding: ArtifactSlot
    normalization: ArtifactSlot
    control_mode: ControlModeSlot
    runtime_config: ArtifactSlot        # 正規形 §2.4; EXPLICIT_NONE 禁止
    callable_selector: CallableSlot     # B2: hash-visible — 同 closure + 同 config で entry callable だけ異なる SCRIPTED/WAIT の ActionId 衝突を除去
```

- `resolved(bundle)` ⇔ 全 slot.state ≠ UNKNOWN。
- **kind 別許容表（Draft / SkillDefinition 両方に適用; 表外 = E_SLOT_FORBIDDEN_NONE / E_SLOT_INCONSISTENT / E_KIND_CONTROL_MISMATCH）**:

| slot | LEARNED | SCRIPTED | WAIT |
|---|---|---|---|
| model_architecture | KNOWN・UNKNOWN | EXPLICIT_NONE | EXPLICIT_NONE |
| tensor_binding | KNOWN・UNKNOWN | EXPLICIT_NONE | EXPLICIT_NONE |
| normalization | KNOWN・UNKNOWN・**EXPLICIT_NONE†** | EXPLICIT_NONE | EXPLICIT_NONE |
| control_mode | KNOWN(値 ∈ {DIFF_IK_EE_TARGET})・UNKNOWN | KNOWN(SCRIPTED_SEQUENCE) | KNOWN(WAIT) |
| runtime_config | KNOWN・UNKNOWN | KNOWN・UNKNOWN | KNOWN・UNKNOWN |
| callable_selector | EXPLICIT_NONE（policy に entry callable なし — kind 強制） | KNOWN・UNKNOWN | KNOWN・UNKNOWN |

- **† W-P1-2（経験的仮定を型不変量にしない）**: LEARNED の normalization = EXPLICIT_NONE は、**NORMALIZATION component の evidence（grade ≥ RECONSTRUCTED_COMPATIBLE）が「前処理未適用」を証明する場合のみ**合法（evidence-gated; certify_definition が照合、無証拠の EXPLICIT_NONE = `E_SLOT_NONE_UNPROVEN`）。tensor_binding / model_architecture は学習 policy に構造上必ず存在するため従来どおり EXPLICIT_NONE 禁止。
- N-a: 「action scale」⊂ TensorBindingSpec（D1.1-B）。
- **callable_selector の canonical 形式（B2）**: `"pkg.module:qualname"`（ASCII・`re.fullmatch(r"\A[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*:[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*\Z")`、違反 = `E_CALLABLE_SELECTOR_MALFORMED`）。**hash-visible = ExecutionBundleHash → SkillActionId に参加**。旧 SkillDefinition.scripted_callable_ref（記録用・ActionId 対象外）は**本 field へ移設し廃止**（E_CALLABLE_REF_KIND_MISMATCH は kind-allowance 表の行として継承 — LEARNED = EXPLICIT_NONE 強制 / SCRIPTED,WAIT = certified 時 KNOWN 必須・Draft のみ UNKNOWN 可）。

### 1.3b ExecutionProvenance（RV6 §4 — 非学習の実行由来を definition 内で固定）

```python
@dataclass(frozen=True)
class ExecutionProvenance:            # SCRIPTED/WAIT = 必須 / LEARNED = None 必須（E_EXECUTION_PROVENANCE_KIND_MISMATCH）
    source_commit: str                # 40-hex — closure member 群を pin する repo commit（SOURCE_COMMIT proof の束縛先）
    source_closure_manifest_hash: str # == ExecutionBundle.executable_artifact_hash（coherence — E_EXECUTION_PROVENANCE_MISMATCH）
    runtime_config_hash: str          # == runtime_config slot hash〔KNOWN 時〕（CONFIG_HASH proof の束縛先; 同上 coherence）
```

- TrainingProvenance と同格の **identity 外・契約内** field（SkillDefinitionHash に入り ActionId/BehaviorSignature には入らない）。registry-fixture 保持だった closure commit を definition 内へ移し、certificate が fixture 非依存で SOURCE_COMMIT 束縛を検査可能に（RV6 §4 sketch 逐語採用 + coherence 2 本）。

### 1.3 TrainingProvenance（learned-conditional; v2.2 から不変）

```python
@dataclass(frozen=True)
class TrainingProvenance:
    execution_family: ExecutionFamily
    training_lineage: TrainingLineage
    final_artifact_hash: str | None     # learned lineage = 必須・== executable (E_PROVENANCE_ARTIFACT_MISMATCH) / NOT_APPLICABLE = null 必須
    final_training_config_hash: str | None  # RV5-W-P0-3: 最終 stage の訓練 config sha — 全 learned lineage で必須（RL_ONLY/BC_THEN_RL = final RL stage / BC_ONLY = 唯一の BC stage〔bc_config_hash は C-CH10 どおり null のまま〕）/ N/A = null 必須。CONFIG_HASH proof の束縛先（EP §3d）
    final_source_commit: str | None         # RV5-W-P0-3: 訓練時 source commit（40-hex）— learned lineage = 必須 / N/A = null 必須。SOURCE_COMMIT proof の coherence 先
    bc_base_hash: str | None
    bc_config_hash: str | None
    demo_dataset_hash: str | None
    demo_dataset_absent_reason: str | None   # "HISTORICAL_PRE_D11" のみ
```

### 1.4 SkillDefinition / DraftSkillDefinition

```python
@dataclass(frozen=True)
class SkillDefinition:
    contract_schema_version: str; skill_namespace: str; skill_id: str
    skill_variant_id: str; behavior_revision: int
    execution_bundle: ExecutionBundle           # resolved 必須 (E_BUNDLE_UNRESOLVED → Draft)
    training_provenance: TrainingProvenance
    semantic_obs_schema: tuple[SemanticFieldSpec, ...]
    semantic_action_schema: tuple[SemanticFieldSpec, ...]
    initiation_spec: InitiationSpec
    termination_spec: TerminationSpec
    checkpoint_specs: tuple[CheckpointSpec, ...]
    handoff_schema: tuple[HandoffSchemaSpec, ...]
    accepted_handoff: tuple[AcceptedHandoffSpec, ...]
    resume_capability: ResumeCapability
    resume_state_schema: str | None             # definition 級 default。CheckpointSpec 側は per-checkpoint override (A-CH8)
    required_control_resources: ControlResourceSpec
    execution_provenance: ExecutionProvenance | None   # RV6 §4（§1.3b）: SCRIPTED/WAIT = 必須 / LEARNED = None 必須
    # scripted_callable_ref は B2 で ExecutionBundle.callable_selector（hash-visible slot）へ移設・廃止 — §1.2
    support_boundary: SupportBoundary
    freshness_policy: FreshnessPolicy
    fail_closed_action: FailClosedAction
    # recovery_rollback_target は v2.3 で削除 — §6-3 の loud-discard へ（NHA: 消費者不在 field を validator 盲点付きで carry しない。recovery 層 chunk で schema bump 再導入）
```

構成型（**field 集合を inline — pN C3 の self-contained 要求。v1 `57ed32b27a` の同名型と field 同一という出自注記は provenance のみ**）: **SemanticFieldSpec** = {field_id, dtype: Dtype, shape: tuple[int, ...], unit, frame} + 全数値検証 / **InitiationSpec** = {expr_kind: ExprKind, schema_ref, schema_hash, payload_canonical_json, required_belief_fields} / TerminationSpec = {declared_classes（非空 frozenset）, predicate_schema_ref, predicate_schema_hash} / CheckpointSpec = {checkpoint_id, resume_state_schema | None} / HandoffSchemaSpec = {handoff_schema_id, schema_version（**形式 "MAJOR.MINOR"、major = 最初の int** — A-CH8）, fields, required_field_ids} / AcceptedHandoffSpec = {producer_skill_id, handoff_schema_id, schema_major_version, **producer_handoff_schema_hash**〔RV4 §2.6: producer 複数 variant の曖昧性除去 — content-addressed schema hash が compatibility 評価対象を一意化。**migration = 保守案（RV6 §7 — UNKNOWN 分岐は型に存在しないため撤回）: registry fixture が hash を供給できる → Draft 生成 / 供給不能 → `E_MIGRATE_STATICS_ABSENT`**（placeholder 生成禁止）〕} / ResumeCapability = {NONE, RESTART_ONLY, RESUME_WITH_STATE} / **SupportBoundary** = {region_ref: str | None, in_support_predicate: dict | None}（最低 1 つ非 null） / FreshnessPolicy = {max_staleness_s: CanonicalDecimal | None}（v1 Freshness の dtype 変更宣言） / **Ownership** = {contact: bool, resource: dict, control: ControlResourceSpec}（旧 untyped control dict = §6-3 で語彙 pin） / ControlResourceSpec = {ee_left, ee_right, gripper_left, gripper_right: bool} / **BeliefRef** = {value: SnapshotRef | HashRef, t_obs: float, ttl: float, confidence: float, ood_flag: bool}（**SnapshotRef = {canonical_belief_snapshot: dict} / HashRef = {ref_hash: str〔64-hex〕}** — R2 nested inline） / **ProducerOutcome** = TerminalOutcome | InterruptOutcome（TerminalOutcome = {termination_class: TerminationClass, detail: str} / InterruptOutcome = {checkpoint_id: str, reason: InterruptReason}） / **enums（member 全数 inline — R2; member 集合 = v1 同一・`.value` は v2 で member 名文字列に統一〔C-CH5・宣言された変更〕）**: **Dtype** = {FLOAT32, INT32, BOOL} / **ExprKind** = {THRESHOLD, REGION, BOOLEAN_AND, CALLABLE_REF} / **TerminationClass** = {SUCCESS, FAILURE, TIMEOUT, INVALID_STATE} / **InterruptReason** = {PLANNED_SWITCH, EVENT, SAFETY_STABILIZED} / **FailClosedAction** = {RE_OBSERVE, SAFE_STOP, HANDBACK_TO_OWNER} / ExecutionFamily = {PPO, DAPG, BC, SCRIPTED, WAIT} / TrainingLineage = {RL_ONLY, BC_ONLY, BC_THEN_RL, NOT_APPLICABLE} / SchemaRegistry = {definitions_by_id}（standalone test = fixture registry。**B7 canonical projection + RV5-W-P0-5 transitive 化**: `schema_registry_hash` = H_WCJ({"schemas": [{"schema_id", "definition_hash"}…]})、schema_id = 非空 NFC str・UTF-8 bytes 昇順 sort・definition_hash = 当該 schema 定義の H_WCJ。**対象 = 当該 definition が実際に参照する schema の推移的部分集合のみ**（宣言 handoff_schema + accepted 側 producer schema — 全 registry でなく; 無関係 schema の追加で certificate が churn しない〔RV5 逐語「bind the transitive projection actually used」〕）。**登録済み定義のみ — Draft 由来は含めない**。registry 全域で schema_id 一意（重複 = `E_REGISTRY_DUPLICATE` fail-closed — skill-local id 衝突を登録境界で排除）。挿入順に不変・1 entry 差で hash 相違 = §8 A/B golden） / MigrationReport = {issues: tuple[ValidationIssue, ...], discards: tuple[str, ...]}。
DraftSkillDefinition = 同 field 集合・bundle に UNKNOWN 可・draft_definition_hash のみ発行。

### 1.5 identity / hash（v2.2 から不変 + C-CH9 文言修正）

```text
ExecutionBundleHash   = H_WCJ(resolved ExecutionBundle)
SkillActionId         = H_WCJ({"ns", "skill", "bundle", "variant", "brev"})   # keyed object
SkillDefinitionHash   = H_WCJ(SkillDefinition 全体)
draft_definition_hash = H_WCJ(DraftSkillDefinition 全体)   # UNKNOWN slot は state object として直列化
```
最終 ActionId は resolved bundle のみ。v1 HandoffStartContext 値: state_id → previous_handoff_class（**語彙 = producer の handoff_schema_id; None → None** — D-CH6）/ initiation_context_hash → loud-discard。

---

## 2. WMSO Canonical JSON（WCJ）

1. object key sort = UTF-16 code unit 順（`k.encode("utf-16-be")` bytes 昇順）。2. lone surrogate / duplicate key 拒否。3. JCS 文字列 escape。4. int のみ・|n| ≤ 2^53−1・float 型拒否。
5. CanonicalDecimal（`re.fullmatch`; `\A(?:(0|-?[1-9][0-9]*)(\.[0-9]*[1-9])?|-0\.[0-9]*[1-9])\Z`）。順序/範囲比較 = `decimal.Decimal` exact。
6. NFC = schema 事前制約（identifier; `E_ID_NOT_NFC`）。
7. 層: (a) key-sort comparator / raw-WCJ（full-Unicode key; golden vectors の対象）/ (b) typed 入口 `canonicalize()`（ASCII-key assert）。
8. golden vectors: RFC 8785 + 非 BMP key + composite bundle vector + **≥2 要素 frozenset vector（C-CH2）**。

### 2.3 composite 直列化 pin（C-CH2/C-CH5 追補）
- 全 hash 入力 = keyed object。slot は全状態で `{"state": …, "artifact_hash"|"value": …}` object（**CallableSlot の selector は `"value"` key で直列化** — B2）。
- **enum encode: 全 hash-visible enum の `.value` = member 名と同一の ASCII 文字列**（C-CH5。**EvidenceGrade の rank int は `.rank` 属性へ移し `.value` は名前**）。strict decode は §5C。
- evidence record 順 = `component_kind.value` bytes 昇順。**ProofItem 順 = EvidencePolicy §3b**（W-P1-3）。
- **set 型 field（`declared_classes`・`required_field_ids` 等 frozenset）は member の `.value`/文字列 bytes 昇順の JSON array として直列化**（C-CH2 — 挿入順・process 依存を排除）。

### 2.4 runtime_config 正規形（v2.2 から不変）
strict decode 済み正規 object の WCJ hash。SCRIPTED schedule = `[{op, args}, …]`。WAIT = `{wait_kind, duration_s | condition_ref}`。

---

## 3. lineage 許容表（full inline — RV4 §2.4）

**許容表（validator の唯一の許容源; 表外 = `E_LINEAGE_FORBIDDEN`、unknown enum = `E_ENUM_UNKNOWN`; 照合対象 = TrainingProvenance）**:

| # | execution_family | training_lineage | 必須 hash | null 必須 | source-closure |
|---|---|---|---|---|---|
| 1 | PPO | RL_ONLY | final_artifact_hash + **final_training_config_hash + final_source_commit**〔RV5〕 | bc_base / bc_config / demo_dataset = null | null |
| 2 | PPO | BC_THEN_RL | bc_base + bc_config + final_artifact_hash + **final_training_config_hash + final_source_commit**〔RV5〕 | —（demo は hash か absent_reason — §1.3） | null |
| 3 | BC | BC_ONLY | final_artifact_hash + **final_training_config_hash（= 唯一の BC stage config）+ final_source_commit**〔RV5〕 | **`bc_base_hash = null / bc_config_hash = null`**（C-CH10/A-CH7 — BC 単独訓練に RL stage も base 概念も無い。v1 "BC" migration で bc 系 config hash 出現 = `E_MIGRATE_BC_CONFIG_UNEXPECTED` fail-close） | null |
| 4 | SCRIPTED | NOT_APPLICABLE | —（executable = closure aggregate） | final/bc/demo 全 null | **必須** |
| 5 | WAIT | NOT_APPLICABLE | — 同上 | 同上 | **必須** |

- **§3-2 source-closure（U6 — prereg §5 の fail-closed 挙動を継承）**: SCRIPTED/WAIT の `executable_artifact_hash` = enumerated closure member の aggregate sha256（決定論仕様 = §3-3）。member 欠落 = fail-closed（v1 `validate_source_closure` と同挙動; error code = §3-3）。closure member 列は runtime_config でなく registry fixture が保持。
- **prereg §5 表（7 行）との関係**: DAPG 2 行は DC-5 により除外（本表 5 行が supersede — register ②）。
- coherence: IdentityKind ↔ ExecutionFamily（LEARNED⇔{PPO,BC}, SCRIPTED⇔SCRIPTED, WAIT⇔WAIT; `E_KIND_FAMILY_MISMATCH`）+ kind ↔ control_mode 値（§1.2 表 — U15）。
- N-1: 本表は構造的許容規則。歴史 artifact の分類 verdict は evidence 過程（§4）の専管。demo hash 執行（D-2）: §1.3 のとおり。

### 3-3. source-closure hash の決定論仕様（v3 W-P1-1 — SkillActionId 参加の前提）

`source_closure_sha256` = **H_WCJ( [ {"path": p_i, "sha256": h_i}, … ] )**（member object の array; 以下全て pin）:
1. **path 正規化**: repo-root 相対・POSIX 区切り・NFC・`./` 接頭辞なし・`..` 成分禁止（違反 = `E_CLOSURE_PATH_MALFORMED`）。
2. **member 順序**: 正規化 path の UTF-8 bytes 昇順。
3. **symlink**: closure member として禁止（`E_CLOSURE_SYMLINK` — 参照先の暗黙持ち込みをしない。実体 file を列挙する）。
4. **改行/内容**: h_i = **committed bytes そのまま**の sha256（line-ending 変換・filter 一切なし）。
5. **合成形式**: 上記 WCJ array の hash（連結文字列でなく keyed object — 区切り曖昧性なし）。
6. **重複 path**: 正規化後の重複 = `E_CLOSURE_DUPLICATE_PATH`（fail-closed; 正規化前の見かけ違い同一 path を検出）。
7. **member 欠落/読取不能**（RV4 §2.5 追補）: `E_CLOSURE_MEMBER_UNREADABLE`（fail-closed — v1 FileNotFoundError 挙動の typed 化）。

### 3-4. behavior_revision の registry 不変量（v3 W-P1-2 + B3 完全化 — 手動 valve の機械 backstop）

2 案（derived BehaviorSignatureHash / registry 不変量）のうち **registry 不変量を採用**（Rs 批准済み identity 4-way split に第 5 入力を足さない — churn 最小）。**B3 で key と比較対象を完全化**:
- **key = 4-way identity scope 完全形 `(namespace, skill_id, variant, behavior_revision)`**（旧 (skill_id, brev) は ns/variant 違いの正当な並存を誤検出 — 撤回）。
- **比較対象 = `BehaviorSignature` = H_WCJ(SkillDefinition の全 static field のうち {identity 入力群, ExecutionBundle, TrainingProvenance, **ExecutionProvenance**, 記録専用 field} を除く全て)**〔provenance 2 型は挙動でなく由来 — 除外集合に追加、13 面は不変〕 — **補集合定義**（列挙漏れ構造を排除; 新 field は既定で signature 入り = fail-closed）。現行 field では **semantic_obs_schema / semantic_action_schema（RV5-W-P0-4 — schema 意味変更が同 revision で E_BEHAVIOR_REVISION_STALE を回避するのを防ぐ; 旧 11 面列挙が補集合定義と矛盾していた欠落を訂正）**/ initiation_spec / termination_spec / checkpoint_specs / handoff_schema / accepted_handoff / resume_capability / resume_state_schema / required_control_resources / support_boundary / freshness_policy / fail_closed_action の **13 面**。
- registry 登録時、同 key の既存 entry と BehaviorSignature 不一致 → `E_BEHAVIOR_REVISION_STALE`（fail-closed）。ActionId は不変のまま、忘却は登録境界で機械捕捉される。**mutation corpus = 13 面それぞれ 1 変異 → 全て検出**（§8; semantic schema 2 面の変異 test は RV5-W-P0-4 の明示要求）。
- **RV4 §2.5 との関係（loud 記録・Rs 判断事項）**: RV4 は「BehaviorSignatureHash を ActionId へ含める（前者）」を**推奨**しつつ registry validator 案も許容する（「または registry diff validator で…拒否」逐語）。本設計は **registry 案を維持**: 理由 = (a) RV2 で批准済みの identity 4-way split に第 5 入力を足さない (b) RV4 の具体懸念例（callable 変更 + revision 忘却）は **B2 の callable_selector bundle 編入で ActionId 側でも既に解消済み** (c) 残余面は本不変量が fail-closed で覆う。Rs が前者を明示指定する場合は schema bump で移行（1 行変更で可能な構造）。

---

## 4. Evidence model（型 = 本 doc に inline — v3 W-P0-4 の自己完結要求。archive 読者は git show 不要）

```python
class ComponentKind(Enum):    # 13 種; .value = member 名 ASCII 文字列
    POLICY_ARTIFACT | MODEL_ARCHITECTURE | OBSERVATION_SCHEMA | ACTION_SCHEMA |
    TENSOR_BINDING | NORMALIZATION | CONTROL_MODE | RUNTIME_CONFIG |
    TRAINING_PROVENANCE | TRAINING_DATASET | INITIATION_SPEC | TERMINATION_SPEC | HANDOFF_SCHEMA

class EvidenceGrade(Enum):    # .value = member 名 / .rank = int（C-CH5 分離）
    EXACT_TRAIN_TIME(.rank=4) | HASH_BOUND_REPRODUCED(3) | RECONSTRUCTED_COMPATIBLE(2) |
    DIMENSION_ONLY(1) | UNKNOWN(0)

class ProofKind(Enum):        # 15 種（意味 = EvidencePolicy §1）; .value = member 名
    TRAIN_RUN_MANIFEST | SOURCE_COMMIT | CONFIG_HASH | INPUT_SCHEMA_HASH | OUTPUT_SCHEMA_HASH |
    NORMALIZER_HASH | FINAL_ARTIFACT_HASH | TRAIN_TIME_CRYPTO_BINDING |
    REPRODUCTION_PROCEDURE | REPRODUCED_OUTPUT_HASH | RECONSTRUCTION_SOURCES |
    COMPATIBILITY_TEST | UNRESOLVED_DIFFERENCES | DIMENSION_SOURCE | EVALUATOR_ARTIFACT

@dataclass(frozen=True)
class ProofItem:
    kind: ProofKind
    ref: str
    artifact_hash: str | None    # 同 (kind, ref) 異 hash = E_PROOF_CONFLICT（EP §3b）

@dataclass(frozen=True)
class EvidenceRecord:            # 1 component = 1 certified claim（重複 = E_EVIDENCE_DUPLICATE）
    component_kind: ComponentKind
    grade: EvidenceGrade
    source_ref: str
    claim_target_hash: str | None  # RV6 §3（旧 artifact_hash を改名）: component 別導出値（EP §3d 表）と必ず一致 — 任意 hex での bundle-hash 操作を型で遮断（不一致 = E_PROOF_MISBOUND）
    evaluator_artifact_hash: str
    proof: tuple[ProofItem, ...]  # canonical 順 = EP §3b（W-P1-3）
    notes: str                    # ⛔ evidence_bundle_hash 対象外

@dataclass(frozen=True)
class EvidenceEvaluationCertificate:   # RV6 §5 — grade を「測定値」として発行する明示形
    component_kind: ComponentKind
    assigned_grade: EvidenceGrade
    claim_target_hash: str
    proof_bundle_hash: str
    evaluator_artifact_hash: str       # ∈ evaluator_registry（E_EVALUATOR_UNKNOWN）
    result_code: str

@dataclass(frozen=True)
class EvidenceBundle:
    records: tuple[EvidenceRecord, ...]   # component_kind.value bytes 昇順
```

- `evidence_bundle_hash` = H_WCJ(records の hash-visible 部分〔notes 除外〕、component_kind 順)。record 入力順に不変（metamorphic #8）、ProofItem 入力順に不変（metamorphic #9 — R-3）。
- **全表 = EvidencePolicy v1.6**（sha 冒頭; **total map〔(component, grade, applicability_class)〕・ApplicabilityResolver・3 cell exact 化・DC-3 準拠復元・ProofItem 順序/conflict・§3d 束縛規則〔G-4 kind 条件付き込み〕・EXPLICIT_NONE 免除・per-component 意味論・二層 hash** を含む — G-1 fix: 本行の版数は EP header と同期更新する）。
- **applicability**（v3 W-P0-1）= EP §3c `ApplicabilityResolver(kind, lineage, component) → REQUIRED(min_grade) | NOT_APPLICABLE | OPTIONAL`。**N/A ≠ UNKNOWN**（N/A = validated 不存在・集約除外 / UNKNOWN = 知識不足・失格）。
- CLOSED_LOOP required に TRAINING_PROVENANCE（**learned lineage のみ・≥3**〔B5 整列 + RV5-W-P0-2: SCRIPTED/WAIT は resolver lineage 層で N/A — U12 の意図〔lineage 自己申告根絶〕は learned に対して維持〕）。missing = UNKNOWN(0)。
- ceiling / two-key conjoin / 「条件付き」cell 定義 = 従来どおり。

---

## 5. Validation（W-P0-2/3・W-P1-6 反映）

### 5A. 静的 certification（**profile 中立** — W-P0-2）

`certify_definition(definition, evidence_bundle, evidence_policy, schema_registry, evaluator_registry, proof_artifact_resolver) → DefinitionCertificationResult`
〔**trust boundary（RV5 gap 3 + RV6 §4/§5）**: resolver 2 種 = `resolve_artifact(ref, expected_sha256)` / **`resolve_git_commit(commit_id)`**（SOURCE_COMMIT は hash 無しのため専用）— fail-closed = `E_PROOF_ARTIFACT_UNRESOLVED`。hash 構造一致に加え asserted bytes の実在・内容整合（manifest の claim_target 列挙 / TTCB の (claim_target, manifest) 束縛 / REPRODUCED == claim_target）を検査 — grade を self-asserted にしない。**evaluator_registry を明示入力**とし `E_EVALUATOR_UNKNOWN` を判定、**certificate は evaluator_registry_hash を結合**（RV6 §5 — どの評価器集合を信頼したかを再現可能に）。詳細 = EP §3d〕

- **値単体検査の全項目（inline — U2 / RV4 §2.4）**: 全 ID/unit/schema_ref/namespace 非空（whitespace-only = `E_ID_EMPTY`）/ shape 全次元 `type(x) is int` かつ >0（bool-as-shape 拒否）/ isfinite: timestamp・duration・cost・TTL・confidence・progress・p50・p95・std・全 bounds・normalization mean/std・scale/bias〔本 chunk の型に現れない量（p50/p95/std 等）は §6-3 deferred-with-object 注記に従い D1.1-B/D2 で適用 — U13〕/ 範囲: TTL>0・confidence/progress∈[0,1]・duration/cost≥0・p50≤p95・std≥0（CanonicalDecimal は decimal.Decimal 演算）/ hash 64-hex 小文字（`E_HASH_MALFORMED`）/ NFC（`E_ID_NOT_NFC`）/ **E_SKILL_UNREGISTERED**〔skill_id ∉ SKILL_ID_REGISTRY — B-CH7〕/ **E_SLOT_NONE_UNPROVEN**〔§1.2†〕/ **E_CALLABLE_REF_KIND_MISMATCH**〔callable 行 — B2〕/ **E_CALLABLE_SELECTOR_MALFORMED**。
- identity 整合 = §3 表・coherence・E_DEMO_HASH_MISSING・E_PROVENANCE_ARTIFACT_MISMATCH（learned のみ）。静的 lifecycle 内部整合 = checkpoint/handoff id 重複禁止・RESUME_WITH_STATE ⇔ resume_state_schema・accepted_handoff の静的互換（§5D 規則を registry の producer 定義に対し — **producer 特定 = producer_handoff_schema_hash、RV4 §2.6**）。Draft 入力 = 検査は走るが certificate 不発行（`E_BUNDLE_UNRESOLVED` を含む report のみ）。
- **evidence = 「present な claim の well-formedness と ProofPolicy/束縛規則（EP §3d）適合」のみ**（**profile 充足は検査しない** — 第 3 解釈の明文化）。
- 出力 = ValidationReport（issues 安定順 = **(code, field_path, message)** — C-CH10）→ valid のみ ContractCertificate:

```python
@dataclass(frozen=True)
class ContractCertificate:
    skill_definition_hash: str; skill_action_id: str
    evidence_bundle_hash: str
    evidence_policy_definition_hash: str  # RV3-W-P1-3 + RV4 §2.3 命名: EP §6 の H_WCJ(policy_object) — 文書編集で不変・規則変更でのみ変わる（policy_document_sha256 は custody 層）
    schema_registry_hash: str          # W-P0-3 / v3 W-P0-2: H_WCJ(registry 内容) — registry A/B での結果差を certificate に固定
    explicit_none_components: tuple[str, ...]  # certified EXPLICIT_NONE slot の ComponentKind.value 昇順 — 不存在 attest の可搬形（EP §3c instance 層の入力; certificate-first を可能にする）
    evaluator_registry_hash: str       # RV6 §5: H_WCJ(sorted evaluator artifact hashes) — 信頼 evaluator 集合を certificate に固定
    identity_kind: str                 # F-1: IdentityKind.value（certify 時に definition から抽出）— EP §3c resolver の kind 依存規則を certificate 単独で計算可能に
    training_lineage: str              # F-1: TrainingLineage.value — resolver lineage 層（TD の BC 系条件）の入力。explicit_none_components と同じ completion class
    validator_artifact_hash: str; contract_schema_version: str
    issued_at: float                   # 同一性判定外
```

### 5A2. usage eligibility（**別 API** — RV2-W-P0-2 / **signature = RV3-W-P0-3 sketch、param 名 = RV4 §2.2 で `requested_profile` に確定**〔register ⑥〕）

```python
evaluate_usage_eligibility(
    certificate,               # certificate-first — 未認証 definition の eligibility 評価を型で不可能に
    evidence_bundle,           # certificate.evidence_bundle_hash と一致検査（不一致 = E_CERT_INPUT_MISMATCH、fail-closed）
    current_evidence_policy,   # 「現行」policy — 旧 certificate は歴史的に valid のまま、現行 policy が厳格化していれば ineligible（RV3-W-P0-3 の意味論）
    requested_profile,         # RV4 §2.2 の命名（RV3 の usage_profile と同一 semantics — 後発 Rs text 優先）
) -> UsageEligibilityReport

@dataclass(frozen=True)
class UsageEligibilityReport:          # field 集合 = RV3-W-P0-3 の指定どおり
    requested_profile: str
    applicable_components: tuple[str, ...]        # resolver 通過分（NOT_APPLICABLE/OPTIONAL は除外され、免除は issues でなく exemptions に loud 記録）
    exemptions: tuple[str, ...]                   # EXPLICIT_NONE 免除の component（EP §4 の loud 記録）
    effective_grades: tuple[tuple[str, str], ...] # (component, 達成 grade) — missing = UNKNOWN
    issues: tuple[ValidationIssue, ...]           # 安定 code; (code, field_path, message) 順
    evidence_policy_definition_hash: str          # 評価に使った現行 policy（RV4 命名）
    eligible: bool
```

- 判定 = EP §3c resolver → applicable へ per-component `達成 grade ≥ min_grade`（EP §4）。resolver の (kind, lineage) 入力 = `certificate.identity_kind` / `certificate.training_lineage`（F-1 — definition 実体なしで全 3 層が計算可能）。
- ⛔ **certificate ≠ authority grant / eligible ≠ authority grant**: acceptance test・O0/S0/V0 two-key・独立安全 gate は eligibility API の入力にしない（RV3-W-P0-3 逐語; RV2 sketch の external_gate_state 引数 = register ⑥ で superseded）。profile は後段で何度でも（現行 policy で）再評価可。

### 5A3. authority grant（**別 API** — RV4 §2.2 が新設指定: 「権限付与は別APIにする」）

```python
evaluate_authority_grant(
    eligibility_report,        # §5A2 の出力（eligible == True が前提条件 — False = 即 DENY）
    acceptance_state,          # 独立 acceptance test の結果 record（PASS/FAIL/UNKNOWN + evidence_ref）
    two_key_state,             # O0/S0/V0 two-key の状態 record
    safety_gate_state,         # 独立安全 gate の状態 record
) -> AuthorityDecision         # {granted: bool, denials: tuple[str, ...], inputs の hash/ref 束縛}
```

- **RV4 の意図**: evidence eligibility と authority を**再び混同しない** — conjoin は prose でなく本 API の型で機械可視。gate state の UNKNOWN/欠落 = fail-closed DENY。two-key/安全 gate の実体・充足規則は O0/S0/V0 層（本 chunk 外）— 本 API は conjoin 判定面のみ定義。closed-loop 実運転権限は本 API の granted == True を必要条件とする（十分条件ではない — 上位 orchestrator gate は自由に追加可）。

### 5B. 実行時 lifecycle validation（W-P1-6 反映）

```python
@dataclass(frozen=True)
class LifecycleValidationReport:      # W-P1-6: 型定義
    invocation_id: str
    issues: tuple[ValidationIssue, ...]   # (code, field_path, message) 安定順
    validator_artifact_hash: str

@dataclass(frozen=True)
class HandoffValidationReport:
    producer_invocation_id: str
    handoff_schema_id: str
    issues: tuple[ValidationIssue, ...]
    validator_artifact_hash: str

validate_invocation_start(invocation, definition, belief, now: float) -> LifecycleValidationReport
    # W-P1-6: now は明示引数 — freshness 評価に隠れ wall-clock 参照禁止（決定論テスト可能）
validate_outcome(invocation, outcome, definition) -> LifecycleValidationReport
validate_handoff(invocation, offer, producer_definition, consumer_definition) -> HandoffValidationReport
```
検査内容（inline）: `validate_invocation_start` = initiation predicate / freshness_policy 評価（明示 `now`）/ required_control_resources vs 実 ownership（比較 = **required ⊆ offered** の bool 包含 — D-CH5）。`validate_outcome` = terminal ∈ declared_classes / interrupt checkpoint ∈ checkpoint_specs / duration・cost 有限非負 / invocation_id 一致。
**`validate_handoff`（RV6 §6 で identity 検査を完全化）** = producer_invocation_id 一致 / **`offer.producer_action_id == invocation.skill_action_id`** / **`offer.producer_definition_hash == invocation.skill_definition_hash == H_WCJ(producer_definition)`** / offer.handoff_schema_id ∈ producer 宣言 schema / **consumer 側 `AcceptedHandoffSpec.producer_handoff_schema_hash == producer schema の計算 hash** / `offer.control_epoch == 現在の authority epoch`（等値検査のみ）/ §5D 互換。**certificate を無効化しない**。
**責務分離（RV6 §6 — 純 validator では epoch 単調・再利用拒否を保証できない）**: epoch の CAS 更新・新 epoch 発行・旧 epoch command 拒否・**使用済み offer 拒否（`handoff_offer_id` 単位）** = **authority manager（O0 層）の状態所有責務**として契約側から要求仕様を pin（validator は等値検査・manager は状態遷移 — 二層で fail-closed）。

### 5C. codec（strict decoder — inline）
duplicate key 拒否 / NaN・±Inf 拒否 / unknown field 拒否 / enum strict（unknown = `E_ENUM_UNKNOWN`）/ lone surrogate 拒否。hash 入力経路で素の `json.loads` を使わない。

### 5D. handoff compatibility 規則（inline）
consumer required ⊆ producer fields / dtype・shape・unit・frame 完全一致 / schema major version 一致 / producer 追加 optional 可 / 暗黙変換禁止（変換は後続 transition adapter）。**producer 定義の特定 = AcceptedHandoffSpec.producer_handoff_schema_hash（content-addressed — RV4 §2.6）**。

---

## 6. Migration v1→v2

### 6-1. 入力 domain・分割・**Draft statics 規則（D-CH1）**
- **入力 = v1 `skill_contracts_manifest.json` の rows + 構築可能な v1 契約 instance**。identity-pinned 行（実測 6/9: APPROACH_CABLE / INSERT_INTO_CLIP / TRANSPORT / RECLAMP_L / HALF_UNCLAMP_RELEASE / CLIP_CONFIRM）→ DraftSkillDefinition / identity 無し行（実測 3/9: CLAMP / UNCLAMP / AERIAL_REGRASP — INADMISSIBLE_*、artifact hash 皆無）→ `E_MIGRATE_IDENTITY_ABSENT`（loud 拒否・Draft を作らない。**placeholder hash の発明 = review-1 P0-2 の再導入につき禁止**）。完全復元可能な場合のみ SkillDefinition 候補（実 v1 corpus では発生しない見込み — §6-2）。
- **非 bundle static fields の供給規則（D-CH1）**: 実 v1 corpus（manifest 行）は semantic schema・initiation/termination/handoff spec を持たない。これらは **registry fixture が per-field で供給**する（`accepted_handoff` と同方式; **fixture 行に provenance 必須** = source_ref + 作成根拠。provenance 無き供給 = `E_MIGRATE_STATICS_ABSENT` fail-close）。fixture 供給 field は evidence 過程で RECONSTRUCTED 以下として grade（fixture = 復元資料であり訓練時 source でない — 昇格しない）。§8 の migration test は「manifest 行 + 供給 fixture」を入力に取り、fixture 欠落 case = `E_MIGRATE_STATICS_ABSENT` を負例に含む。
### 6-2. kind 条件 slot 割当（inline — 機械的導出、推測ではない; U4）

| slot | LEARNED | SCRIPTED / WAIT |
|---|---|---|
| model_architecture / tensor_binding / normalization | UNKNOWN（v1 に無し — LEARNED は callable を除く旧 5 slot が全て UNKNOWN〔executable は slot 外・常に KNOWN〕 — C-CH9） | EXPLICIT_NONE（kind 強制 — §1.2 表準拠） |
| control_mode | UNKNOWN | KNOWN(SCRIPTED_SEQUENCE) / KNOWN(WAIT)（kind 強制） |
| runtime_config | UNKNOWN | UNKNOWN（schedule 情報は v1 に無し） |
| callable_selector（B2） | EXPLICIT_NONE（kind 強制） | KNOWN（v1 registry fixture の callable path から §6-1 と同権の provenance 付き供給; 無ければ UNKNOWN → Draft のまま） |

→ いずれの kind も runtime_config 等が UNKNOWN のため**主出力は Draft**。
### 6-3. v1 全 root field の disposition 表（inline・完全列挙 — U13 + v2.3-v2.6 差分統合。silent drop なし）

| v1 field (`contracts.py:511-533` の 19) | v2 disposition |
|---|---|
| schema_version | → contract_schema_version（"2.0.0" へ、MigrationReport 記録） |
| action_key.skill_id / executable_identity | → skill_id / ExecutionBundle.executable_artifact_hash（scripted/wait = closure、learned = weights）+ TrainingProvenance（family/lineage/bc hashes — v1 family 文字列写像 = 6-5） |
| action_key.handoff_start_context | class 相当 → TransitionRecord.previous_handoff_class の語彙（**= 当該 state の handoff_schema_id; None → None** — D-CH6）/ initiation_context_hash → **loud-discard**（再現不能文脈 hash） |
| policy_family | → 6-5 写像 |
| obs_action_schema (fields + field_semantics) | → semantic_obs/action_schema + 対応 component evidence（RESOLVED 実績根拠なし → RECONSTRUCTED_COMPATIBLE 以下で再記録・昇格なし） |
| initiation_predicate | → InitiationSpec（同 field） |
| required_belief_confidence | → InitiationSpec 側 predicate payload へ吸収（MigrationReport 記録） |
| termination_classes | → TerminationSpec.declared_classes |
| progress_phase | → RuntimeSnapshot.progress_phase（runtime 側 — U13 の home 明示） |
| safe_interruption_checkpoints | → checkpoint_specs（resume_state_schema=None で） |
| handoff (SkillHandoffState 実体) | → **loud-discard + `E_MIGRATE_RUNTIME_CONTEXT_ABSENT`**（**RV4 §2.7**: v1 に producer_invocation_id / producer_definition_hash / control_epoch が存在せず v2 HandoffOffer を構築不能 — **0/placeholder 捏造禁止**。RuntimeSnapshot.handoff = None。静的 schema 部分のみ HandoffSchemaSpec に再宣言） |
| accepted_incoming_handoff_set | → accepted_handoff（producer/schema/version へ正規化 + **producer_handoff_schema_hash = 保守案〔RV6 §7 / H-1 で本行へ伝播〕: registry fixture が供給できる → Draft 生成 / 供給不能 → `E_MIGRATE_STATICS_ABSENT`** — UNKNOWN 分岐は型に存在せず撤回・placeholder 禁止） |
| duration_cost_distribution | → **loud-discard**（静的 prior 廃止 — 分布推定は Phase D SDM の職務。DC-4 p50/p95/std 検査 = deferred-with-object） |
| resource_requirements | control_ownership（untyped dict）→ required_control_resources: **key 語彙 = {ee_left, ee_right, gripper_left, gripper_right} pin・未知 key = `E_MIGRATE_OWNERSHIP_KEY`（fail-close — D-CH5）** / compute (FAST/SLOW_PATH) → **loud-discard**（O0/RT0 層の関心 — Phase F 再設計） |
| recovery_rollback_target | → **loud-discard**（NHA — 消費者 = 未実装 recovery 層。再導入は当該 chunk で schema bump） |
| fail_closed_action | → fail_closed_action |
| policy_version | → **loud-discard**（identity は hash 体系が担う; 人可読 version は provenance notes へ） |
| freshness | → FreshnessPolicy（max_staleness_s は 6-6 の decimal 変換） |
| support_boundary | → support_boundary |
| admissibility (4 bool) | → **明示 discard + MigrationReport loud 記録**（V-4 — conformance/authority は certificate + profiles で再導出） |
| (scripted/wait) callable_qualname | → **ExecutionBundle.callable_selector**（B2 — canonical 形式 §1.2 へ正規化; 旧 v2 案の scripted_callable_ref は廃止済み） |
### 6-4. v1 公開 symbol disposition（**total 化 — D-CH2/B-CH3**）

| v1 symbol | 処遇 |
|---|---|
| harness.EXPECTED_SKILL_IDS | v2 `SKILL_ID_REGISTRY` へ継承（**module home = `contracts_v2/identity.py`・更新 = Rs 承認事項**）。共存中の等値 invariant test（§8） |
| harness.validate_manifest / verify_manifest_artifacts / evaluate_conformance / validate_source_closure | retained-in-v1（D1.1-C 後継まで; **d1_exit HOLD guard 生存**。DeprecationWarning に「shim 委譲対象外」明記）。**依存面（identity.SCRIPTED/WAIT_CLOSURE_MEMBERS・source_closure_sha256・canonical_json・finetune_cfg_hash・contracts.is_hex64）も同期間 byte-retained**、v1 test suite は window 中 green 維持（§8 invariant）— D-CH2 |
| harness.assert_no_authority / parse_root_fields / parse_belief_value | retained-in-v1（上記 4 関数の補助面; 同期間） |
| identity.canonical_json | **v1-internal ONLY — v2 hash に使用禁止**（WCJ と別物; dual-canonicalization guard を DeprecationWarning + §8 negative test で明示 — B-CH3） |
| identity.source_closure_sha256 / scripted_identity / wait_identity / learned_identity_from_files / make_initiation_context_hash / handoff_start_context / sha256_file | retained-in-v1（guard 依存 + 歴史再現用）。v2 は canonical.py / identity.py が代替 |
| policy_adapter.CanonicalContractRepr / canonicalize / is_deterministic | deprecate（v2 の certify/canonical が後継; shim 委譲なし・使用検出 = DeprecationWarning） |
| contracts.py 型群 | shim = v2 へ変換・委譲のみ。**v1 `__post_init__` 検証は retained 期間 byte 保持**（負制御 test の前提 — D-CH2） |
- **closure member 二重真実の解消**: v2 registry fixture の closure 列は「v1 定数の写し」であることを §8 の**等値 invariant test** で拘束（分岐 = test FAIL）。DC-6 の bounded 例外として supersession register ⑤ に記録済み。

### 6-5. v1 `policy_family` 全域写像（inline・total — U2）

| v1 文字列 | → (ExecutionFamily, TrainingLineage) |
|---|---|
| "BC+RL" | (PPO, BC_THEN_RL) |
| "PPO" | (PPO, base/config null なら RL_ONLY、else BC_THEN_RL) |
| "BC" | (BC, BC_ONLY) |
| "DAPG" | (DAPG, 宣言 provenance) — 写像は total、可否は §3 表が判定（現行 = `E_LINEAGE_FORBIDDEN`; corpus case 必須 — NHA） |
| "SCRIPTED" | (SCRIPTED, NOT_APPLICABLE) |
| "WAIT" | (WAIT, NOT_APPLICABLE) |
| その他 / 欠落 | `E_MIGRATE_FAMILY_UNKNOWN` / identity 無し行は 6-1 の `E_MIGRATE_IDENTITY_ABSENT` が先行 |

### 6-6. **数値境界 algorithm（C-CH3/D-CH4 差替）**:
```text
convert(v: float) = Decimal(repr(v)) を正規化:
  整数値 (v == int(v)) → 整数形文字列 ("30.0"→"30", "0.0"→"0", "1.0"→"1")
  非整数値 → 固定小数点文字列・trailing zero 除去 ("0.1"→"0.1")
  |指数| が窓 (10^±12) を超える → E_MIGRATE_FLOAT_FORM (窓内は固定小数点展開で受容: 1e-07→"0.0000001")
  出力は CanonicalDecimal 正規形検査を必ず通す (二重防御)
corpus: 1.0→"1" / 30.0→"30" / 0.0→"0" / 0.1→"0.1" / 0.831→"0.831" / 1e-07→"0.0000001" / 1e-15→E_MIGRATE_FLOAT_FORM
```
### 6-7. 既定値（inline）
`behavior_revision = 1` / `skill_variant_id = "default"` / `contract_schema_version = "2.0.0"`。

### 6-8. prereg §7b 文言との関係（inline — U18）
prereg §7b「同じ v1 → 常に同じ **SkillDefinitionHash**」は、Draft model 下では「**draft_definition_hash**（完全解決可能時は SkillDefinitionHash）」と読む（register ③）。

---

## 7. Runtime 型（full inline — RV4 §2.4）+ §5B の 2 report 型（RV2-W-P1-6）

```python
@dataclass
class SkillInvocation:
    invocation_id: str
    skill_action_id: str        # certified action のみ（Draft は invocation 不可 — §7-2）
    skill_definition_hash: str
    start_belief_ref: BeliefRef
    start_time: float
    current_phase: str
    elapsed_s: float
    control_epoch: int

@dataclass(frozen=True)
class SkillOutcome:             # checkpoint_id 無し（outcome union からのみ — review-4 P0-5）
    invocation_id: str
    outcome: ProducerOutcome
    end_belief_ref: BeliefRef
    duration_s: float
    accumulated_cost: float

@dataclass(frozen=True)
class HandoffOffer:             # compatibility 無し + control_epoch（review-4 P0-5）
    handoff_offer_id: str       # RV6 §6: offer 一意 id — authority manager の使用済み拒否（replay 防止）単位
    handoff_schema_id: str
    producer_invocation_id: str
    producer_action_id: str
    producer_definition_hash: str
    control_epoch: int
    outcome: ProducerOutcome
    belief_ref: BeliefRef
    ownership: Ownership

@dataclass(frozen=True)
class TransitionRecord:
    episode_id: str
    invocation_id: str
    start_belief_ref: BeliefRef
    goal_context: str
    previous_handoff_class: str | None
    skill_action_id: str
    skill_definition_hash: str
    end_belief_ref: BeliefRef
    outcome: ProducerOutcome
    duration_s: float
    accumulated_cost: float
    safety_events: tuple[str, ...]
    schema_versions: SchemaVersionStamp

@dataclass(frozen=True)
class SchemaVersionStamp:
    contract_schema_version: str
    belief_schema_version: str
    evidence_policy_definition_hash: str   # RV4 命名（旧 evidence_policy_hash）
    recorder_artifact_hash: str

@dataclass
class RuntimeSnapshot:          # v1 runtime fields の migration 先
    progress_phase: str | None = None
    handoff: HandoffOffer | None = None    # v1 migration では常に None（§6-3 — RV4 §2.7 loud-discard）
```

**§7-2 明示帰結（U14）**: TransitionRecord / SkillInvocation は **certified SkillActionId のみ**を key にする（Draft 不可）。D2 データ収集は certified skill に限られ、D1.1-B 完了まで learned skill の transition 行は 0 になり得る — fail-closed の意図された帰結。**runtime 記録の content-hash 化は WCJ 対象外・方式は D2 prereg で確定（明示 defer — U14）**。

## 8. Test plan（base inline — RV4 §2.4 + 全差分統合）

**base（v2.2 から inline）**:
- standalone / monorepo 分離（fixture registry / closure fixture 含む）。standalone = 配布物のみで全実行・unexpected skip 0。
- **mutation test**: 各 operator は 1 不変条件を明示破壊し期待 error code + field path を宣言（valid→valid 変異は operator にしない）。
- **generative / metamorphic**（stdlib random・seed 固定・失敗時 seed+入力保存）: #1 contract_schema_version 変更 → ActionId 不変・DefinitionHash 変化 / #2 behavior_revision 変更 → 両方変化 / #3 = 下記差替 / #4a TrainingProvenance field 変更 → ActionId・evidence_bundle_hash 不変・DefinitionHash/certificate 変化（U8） / #4b TRAINING_PROVENANCE 系 EvidenceRecord 変更 → ActionId・DefinitionHash 不変・evidence/certificate 変化 / #5 ExecutionBundle 変更 → ActionId 変化 / #6 previous_handoff_class 変更 → ActionId・static hash 不変 / #7 非 BMP key vector を層(a)に適用 → RFC 期待順 / #8 EvidenceRecord shuffle → EvidenceBundleHash 不変 / #9 = 下記 / #10 certificate 発行後の lifecycle 違反 → certificate 有効のまま・LifecycleReport のみ違反。
- invalid corpus（base）: review-1 実証 negative + DC-4 追加分 + `E_DECIMAL_NONCANONICAL`（`-0`・anchoring-trap: `junk-0.5`・`0.0`・`1.50`・`03`・`1e3`・`5.` — U16）+ lone surrogate + duplicate key + non-NFC + int>2^53−1 + slot 不整合（E_SLOT_INCONSISTENT / E_SLOT_FORBIDDEN_NONE / E_KIND_CONTROL_MISMATCH: LEARNED×KNOWN(WAIT)）+ "DAPG" → E_LINEAGE_FORBIDDEN + identity-less v1 行 → E_MIGRATE_IDENTITY_ABSENT + float-bearing v1 → 変換 or E_MIGRATE_FLOAT_FORM。
- migration tests: 決定的 / 同一入力同一 hash（6-8 の読み）/ v2→v2 no-op / 不完全 v1 fail-closed / UNKNOWN 非昇格 / identity-pinned 6/9 → Draft + 3 行 → E_MIGRATE_IDENTITY_ABSENT。
- cross-process hash stability（subprocess）+ WCJ golden vectors + composite bundle vector（U9）。

**差分**:
- metamorphic **#3 差替（D-CH8）**: 「runtime 型の全 field 名が static hash の WCJ payload key 集合に不在」の **serialization-boundary assert**（vacuous 変異試験を廃止）。
- **#4b は hashed fields（grade/source_ref/proof/artifact_hash）限定 + notes-mutation 行追加（全 hash 不変）**（C-CH7）。
- **metamorphic #9（R-3 — W-P1-3 の明示要求）**: claim 内 **ProofItem の入力順 shuffle で全 hash 不変**（EP §3b canonical 順に正規化されるため。#8 = record 級 shuffle とは別 object）。
- corpus 追加: `E_EVIDENCE_DUPLICATE` / `E_PROOF_INSUFFICIENT` / `E_GRADE_INAPPLICABLE`（P と S 非次元の両方 — D-CH10）/ `E_PROOF_CONFLICT`（W-P1-3）/ `E_SLOT_NONE_UNPROVEN` / `E_CALLABLE_REF_KIND_MISMATCH` / `E_MIGRATE_OWNERSHIP_KEY` / `E_MIGRATE_STATICS_ABSENT` / `E_MIGRATE_BC_CONFIG_UNEXPECTED` / integral float 群（§6-6 corpus）。
- corpus 追加（v3 fold）: `E_CLOSURE_PATH_MALFORMED` / `E_CLOSURE_SYMLINK` / `E_CLOSURE_DUPLICATE_PATH` + closure 決定論 golden vector（§3-3）/ `E_BEHAVIOR_REVISION_STALE`（§3-4 — 同 revision・異 termination_spec hash の登録拒否）/ `E_CERT_INPUT_MISMATCH`（§5A2）/ **N/A ≠ UNKNOWN 判別 case**（SCRIPTED の MODEL_ARCHITECTURE = NOT_APPLICABLE で eligible / LEARNED の UNKNOWN = ineligible — v3 W-P0-1）/ **現行 policy 厳格化 case**（旧 certificate + 新 policy → ineligible・certificate は valid のまま — v3 W-P0-3）。
- corpus/test 追加（B 系 fold）: **B2 衝突 regression**（同 closure・同 runtime_config・異 callable_selector の SCRIPTED 2 定義 → ExecutionBundleHash/ActionId 相違を assert）+ `E_CALLABLE_SELECTOR_MALFORMED` / **B3 mutation corpus**（§3-4 の **13 面**〔G-2 fix — semantic_obs/action_schema 2 面込み〕× 各 1 変異 → 全て E_BEHAVIOR_REVISION_STALE 検出; ns/variant 違いの並存 = 非検出を併記）/ **B4 negative controls**（wrong-but-valid-hex → E_PROOF_MISBOUND・null-where-required → E_PROOF_PAYLOAD_MISSING・foreign kind → E_PROOF_KIND_FOREIGN — EP §3d）/ **B6 order golden**（ProofKind.value bytes 昇順の期待列を固定 + #9 shuffle と対）/ **B7 registry A/B golden**（1 entry 差 → hash 相違・挿入順 → 不変・重複 id → E_REGISTRY_DUPLICATE）/ **B5 境界 case**（TP=RECONSTRUCTED(2) の definition → CLOSED_LOOP ineligible・SHADOW eligible）。
- **invariant tests（D-CH2）**: `SKILL_ID_REGISTRY == EXPECTED_SKILL_IDS`・registry fixture closure == v1 定数（retained window 中）・v1 test suite green。
- **RV4 fold 追加**: EP markdown 表 ↔ code 定数 一致試験（parser artifact hash 記録 — RV4 §2.3）/ `evaluate_authority_grant` の conjoin tests（eligible=False → DENY・gate UNKNOWN → fail-closed DENY・全 PASS → grant — §5A3）/ `E_CLOSURE_MEMBER_UNREADABLE` / `E_MIGRATE_RUNTIME_CONTEXT_ABSENT`（v1 handoff 実体 → loud-discard）/ producer_handoff_schema_hash による §5D 一意特定 case（同 producer 複数 variant）。frozenset vector（C-CH2）維持。
- **RV5 fold 追加**: EP markdown ↔ **JSON fixture** ↔ code 定数の**三面一致試験**（`WMSO_EvidencePolicy_v1.6.json` = normative fixture・semantic hash はこの test が確定 — RV5-W-P0-6）/ **B3 mutation 13 面**（semantic_obs/action_schema の 2 変異 → E_BEHAVIOR_REVISION_STALE — RV5-W-P0-4）/ `E_PROOF_ARTIFACT_UNRESOLVED`（resolver 取得不能・sha 不一致・zero-length — RV5-W-P0-3）/ `E_EVALUATOR_UNKNOWN` / **TP applicability 判別 case**（SCRIPTED の TP = N/A で CLOSED_LOOP 可〔他 required 充足時〕・LEARNED の TP 不在 = UNKNOWN 失格 — RV5-W-P0-2）/ **registry transitive projection case**（definition 非参照の schema 追加 → schema_registry_hash 不変・参照 schema 変更 → 変化 — RV5-W-P0-5）/ final_training_config_hash / final_source_commit の lineage 別 null/必須 corpus（RV5-W-P0-3）。
- **G-4 corpus 追加**: SCRIPTED の POLICY_ARTIFACT = kind 条件付き束縛（closure commit / runtime_config hash）で **HB(3) 到達 → CLOSED_LOOP eligible**（他 required 充足時）/ 同 EXACT(4) 要求 → `E_PROOF_INSUFFICIENT`（期待 — 非学習の明示 bound）/ learned claim に closure-commit 束縛を流用 → `E_PROOF_MISBOUND`。
- **RV6/C fold 追加**: **claim_target golden（S 系 6 component 含む全 13）**— REPRODUCED == claim_target で HB 成立・wrong claim_target → E_PROOF_MISBOUND（pN C1 の negative/golden 要求）/ **JSON parity test** = 掲載 `evidence_policy_definition_hash` と policy_definition の H_WCJ 再計算一致（pN C2）/ `resolve_git_commit` 経路（存在/不在 — RV6 §4）/ `E_EVALUATOR_UNKNOWN` + certificate.evaluator_registry_hash 再現 case（RV6 §5）/ **handoff identity negatives**（producer_action_id 不一致・definition_hash 不一致・schema hash 不一致 → 各 FAIL — RV6 §6）+ handoff_offer_id 再利用拒否（authority manager 側 test に委譲・契約側は要求仕様 pin）/ ExecutionProvenance coherence 2 本（closure manifest ≠ executable / runtime_config 不一致 → E_EXECUTION_PROVENANCE_MISMATCH）+ kind mismatch / migration: producer_handoff_schema_hash fixture 供給不能 → E_MIGRATE_STATICS_ABSENT（RV6 §7 保守案）。

## 9. Module layout（inline — pN C3; impl GO 時に確定）
`thread_isaac_lab/wmso/contracts_v2/`: `types.py identity.py evidence.py certify.py lifecycle.py codec.py canonical.py migrate.py tests/`（`wmso/d1/` は §6-4 の処遇）。`SKILL_ID_REGISTRY` の home = identity.py（D-CH2）。

## 10. Open points
**設計内 open = 0**。review-4 transcript の fidelity は **RV4 §1.4 で Rs 確認済み: semantic fidelity CONFIRMED**（byte fidelity = N/A — 原本が chat message であり独立 file でないという限定付き。この限定を明記して PENDING 解消 — RV4 逐語「Rs確認PENDINGは、この限定を明記した上で解消してよい」）。W-review v2/v3/v4 は byte-identical file copy のため確認不要。
**process 注記（over-claim 防止）**: CC Debate cycle-2 の対象 = v2.2 であり、**v2.3 以降の fold 内容は debate 未通過**（skill の max-2-cycles 到達）。fold の検証 = pS 全行照合 + pN DESIGN verify が担う。cycle-3 の要否 = Rs 裁量（自己起動しない）。
**RV5 §6 の後続 chunk carries（loud 記録 — 消失防止; DC-系と同格の binding carry）**: (i) **D2 transition data = 修正済み clean substrate のみ**・旧 contaminated log は明示 **substrate_id** を付け silent pooling 禁止 (ii) **handoff state は arm pose だけでなく grasp/contact stability を encode**（1 mrad 級 arm 差が discrete chain flip と共存し得る — D1.1-B semantic spec の設計入力）(iii) **最初の vertical slice は failure/no-chain outcome + calibrated uncertainty を含む**（成功 transition のみで作らない）(iv) **D1.1-A は本 bounded fix 後 freeze**（契約完全主義で slice を無期延期しない — Rs 逐語）。
**kinematic COMPLETE REMOVAL directive の写像（Rs 13:34 via pN relay・p6 FYI 14:03 — loud 記録）**: (a) 本契約構造は drive 方式を hard-code しない — LEARNED の control_mode 許容値 = DIFF_IK_EE_TARGET のみ（kinematic mode は enum に存在しない — §0 DiffIK-only を契約層で執行）。(b) v1 executable（kinematic 期 closure/weights）は migration で **Draft/evidence 化され実行候補にならない**（§7-2 certified-only + eligibility + authority — 「歴史 artifact = evidence 保存・実行候補から除外」指示と構造的に整合）。(c) demo 再記録必然化は demo_dataset_hash の content-address 構造に影響なし（新 demo = 新 hash・新 evidence record）。drive-substrate lineage を provenance 型で明示する必要が生じた場合は D1.1-B/C の schema delta として Rs review 経由。(d) 本 design + EP に clip-pin/weld/attachment/kinematic-drive への依存記述なし（grep 確認済み — 「pin」は全て仕様固定の語義）。(e) impl/run/training は本 chunk で元より CLOSED — HALT/fail-closed 指示と整合。

## 11. 検証系譜
- cycle-1 = 19 項 accepted → v2.2 fix → **cycle-2 で 4-lens 全数 discharge 検証（16-18/18 + 残差）**。cycle-2 verdict = **REVIEW**（max-2-cycles; log cycle 2）→ escalation = Rs 報告済み。**本 v2.3 が cycle-2 残差 + W 系 + NHA 指摘の fold**（fix 台帳 = verification-log cycle 2 consolidation + scratchpad fix-list）。
- **W→fold-map（review v2）**: W-P0-1 = §1.3（v2.2 先行治癒）/ W-P0-2 = §0・§5A・§5A2〔external_gate_state は register ⑥ で v3 が supersede〕/ W-P0-3 = §5A certificate / W-P0-4 = EvidencePolicy（存在 = `ac5865b66d`、内容 = v1.4）/ W-P1-1 = §2-7（U7）/ W-P1-2 = §1.2† / W-P1-3 = EvidencePolicy §3b / W-P1-4 = EvidencePolicy §4（U12）/ W-P1-5 = §8 #4a/4b（U8）/ W-P1-6 = §5B。
- **W'→fold-map（review v3 WMSO 全 9 項; 対象 = v2.2+EP v1 — 「先行治癒」= v2.3 が review 執筆時点で既に fold 済みの意）**:
  - **v3 W-P0-1**（SCRIPTED/WAIT が profile 恒久不能）= 実質は v2.3 の EP §4 免除で先行治癒 + **本版で Rs sketch の typed 形 `ApplicabilityResolver` を EP §3c に採用**（instance/lineage/profile 3 層・N/A ≠ UNKNOWN 逐語反映・OPTIONAL = TD 非 BC lineage）。
  - **v3 W-P0-2**（registry hash 未結合）= v2.3 §5A `schema_registry_hash` で先行治癒（review v2 W-P0-3 と同項）。
  - **v3 W-P0-3**（eligibility API/report 不在）= v2.3 §5A2 で先行治癒 + **本版で v3 sketch 逐語採用**（certificate-first・current_evidence_policy・4 引数・gate 群 external conjuncts〔register ⑥〕・report field 集合 = 指定どおり）。
  - **v3 W-P0-4**（evidence 型 自己完結）= **本版 §4 に全型 inline**（ComponentKind/EvidenceGrade/ProofKind/ProofItem/EvidenceRecord/EvidenceBundle + §5A2 report — archive 読者に git show を要求しない）。
  - **v3 W-P0-5**（EP 意味 gap 4 点）= (a)(b) = EP v1.1 の DC-3 準拠復元で先行治癒（HB@TP に REPRODUCED_OUTPUT_HASH ✓ / RC@TP に COMPATIBILITY_TEST ✓）/ (c) override 置換/補完の意味 = **本版 EP §3 冒頭で明文化** / (d) 同 (kind,ref) 異 hash = EP §3b `E_PROOF_CONFLICT` で先行治癒。total map 形 = **EP §3 を (component, grade, applicability_class) domain で宣言**。
  - **v3 W-P0-6**(transcript 不在) = 設計側: header に bank commit `ac5865b66d` + full sha 記載済み。package 側 = p6 が v4 で 11_ 同梱 + full SHA 表（p6 report 12:31）。Rs fidelity 確認 = §10 で PENDING のまま保持。
  - **v3 W-P1-1**（closure hash 決定論）= **本版 §3-3**（6 側面 pin: path 正規化/順序/symlink 禁止/bytes-as-committed/WCJ 合成/重複拒否）。
  - **v3 W-P1-2**（behavior_revision 手動 valve）= **本版 §3-4 registry 不変量 `E_BEHAVIOR_REVISION_STALE`**（2 案中 registry 案 — identity 4-way split を不変に保つ選択、理由付き）。
  - **v3 W-P1-3**（semantic/custody hash 分離）= **EP §6 二層 hash + §5A/§5A2 の結合先変更**（v2.4 導入; RV4 §2.3 で `evidence_policy_definition_hash` / `policy_document_sha256` に命名確定）。
  - （review v3 §5 の A-P0/A-P1 系 = arm-control 設計 = p4/p5 管轄 — 本 node 範囲外、fold 対象にしない。§6 package 系 = p6 管轄。）
- **B→fold-map（pN DESIGN verify HOLD B1-B7、13:26 — 全項 pQ on-disk 検証で真と確認の上 fold）**:
  - **B1**（custody/fidelity）= pS verify record を本 bank で explicit-path bank（同 commit）。transcript normative 依存 = register ① の prereg-floor 再接地で除去（§10 注記; Rs 確認は継続要請）。
  - **B2**（callable identity 衝突）= §1.1 CallableSlot + §1.2 bundle field `callable_selector`（hash-visible・canonical 形式 pin・kind-allowance 行）+ §1.4 の旧 scripted_callable_ref 廃止 + §6-2 供給行 + §8 衝突 regression。
  - **B3**（behavior_revision 不変量の不完全）= §3-4 完全化: key = (ns, skill_id, variant, brev) / BehaviorSignature = **補集合定義**（**13 面** — G-2 fix; RV5-W-P0-4 の 2 面込み）/ mutation corpus。
  - **B4**（proof 自己申告化）= EP §3d: payload 必須性（null 可 = SOURCE_COMMIT のみ）+ 15 kind の束縛対象表 + E_PROOF_MISBOUND / E_PROOF_PAYLOAD_MISSING / E_PROOF_KIND_FOREIGN + §8 negative controls。
  - **B5**（ceiling 抵触）= EP §4 CLOSED_LOOP 列 TP/TD ≥2 → **≥3 整列**（Rs 確定表と同値化; register ④ 撤回注記。緩和は Rs 再裁定のみ — §10 でなく Rs 判断事項として報告）。
  - **B6**（順序二義性）= EP §3b: 唯一の正 = **ProofKind.value ASCII bytes 昇順**（表行順 claim 撤回）+ §8 order golden。
  - **B7**（registry projection 未定義）= §1.4 SchemaRegistry canonical projection（sorted array・Draft 除外・E_REGISTRY_DUPLICATE・A/B golden）。
- **RV4→fold-map（Rs PLAN_STATUS review v4、対象 = v2.3+EP v1.1 期; 「先行治癒」= review 執筆時点で後続版が既に fold 済みの意）**:
  - **RV4 §1.1/§1.2**（file 07 sha 不一致・工程 stale）= p6 lane（summary v5）+ 根因 = pS record 未 bank → **B1 で解消済み**（`59b7720408`）。
  - **RV4 §1.3**（review ID 混同）= header の完全修飾規約採用（RV2-/RV3-/RV4-）。指摘自体は正確: RV2 と RV3 の W-P1 番号は別物 — 本 doc は v2.4 以降「v3 W-」接頭辞で既に区別済み、規約として明文化。
  - **RV4 §1.4**（transcript fidelity）= **semantic fidelity CONFIRMED → §10 で PENDING 解消**（byte N/A 限定明記）。
  - **RV4 §2.2**（R-1..R-3）= R-1/R-3 先行治癒（v2.4）。R-2 = certificate-first 先行治癒（v2.4）+ **本版で param 名 requested_profile 確定 + `evaluate_authority_grant` 別 API 新設（§5A3）** — RV3「external conjuncts」と RV4「別 API」は整合（eligibility の外・typed API へ）。register ⑥ 注記維持。
  - **RV4 §2.3**（EP 機械可読）= EP §6 二層 hash 先行治癒（v1.2）+ **本版 EP v1.4 で RV4 命名（policy_document_sha256 / evidence_policy_definition_hash）+ dataclass/golden fixture/parser hash/一致試験 requirement pin**。
  - **RV4 §2.4**（self-contained）= **本版で全 committed pointer を inline**（§3 表・§5A 検査・§5C/5D・§6-2/6-3/6-5/6-7/6-8・§7・§8 base・§12）— full snapshot 化（Rs 推奨案 1）。
  - **RV4 §2.5**（closure/behavior identity）= closure 6 側面 = §3-3 先行治癒（v2.5）+ **本版 §3-3 に E_CLOSURE_MEMBER_UNREADABLE 追補**。behavior = §3-4 registry 不変量（B3 完全化済み）+ **RV4 推奨（ActionId 編入）との差 = §3-4 に loud 記録・Rs 判断事項**（callable 面は B2 で ActionId 編入済み）。
  - **RV4 §2.6**（AcceptedHandoffSpec producer 曖昧）= **本版 §1.4 producer_handoff_schema_hash 追加**（content hash 案採用）+ §5D 特定規則。
  - **RV4 §2.7**（v1 runtime handoff 構築不能）= **本版 §6-3 handoff 行 = loud-discard + E_MIGRATE_RUNTIME_CONTEXT_ABSENT**（Rs 提示 2 案中 loud-discard 択 — 捏造禁止逐語準拠。LegacySnapshot 案は不採用: authority/runtime 再利用不可の型を作るより不在を明示）。
  - **RV4 §2.8**（ProofItem 順序文）= B6 先行治癒（EP v1.3）+ **本版 EP §3b を RV4 指定文字列そのままに整列**。
  - **RV4 §2.9**（v2.4 として bank せよ）= 実際の版進行 v2.4/v2.4.1/v2.5/v2.6 が充足。
  - （RV4 §3 arm 系 = p4/p5 管轄・§1.1 package 系 = p6 管轄 — 本 node 対象外。）
- **RV5→fold-map（Rs PLAN_STATUS review v5、対象 = v2.5+EP v1.3 期 package）**:
  - **RV5 C-P0-1**（pN HOLD artifact 不在）= **本版で as-received transcript を bank**（`WMSO_PN_DESIGN_VERIFY_HOLD_B1B7_TRANSCRIPT_20260719.md`、**pN 著者 readback = CONFIRMED 15:42** — fidelity のみ・DESIGN 再判定ではない）。package 同梱 = p6。
  - **RV5 C-P0-2**（pS record 未 bank）= **B1 で解消済み**（`59b7720408`）— RV5 は bank 前 package を見た（時系列正常）。
  - **RV5 C-P0-3**（transcript fidelity）= CONFIRMED 再確認（RV4 §1.4 と同判定; §10 で解消済み）。
  - **RV5 C-P0-4**（filename/version 非同期）= p6 package lane（canonical filename or manifest 方式）。
  - **RV5-W-P0-1**（stale v1.2/≥2 参照）= **本版で全掃**: §4 の「TP ≥2」→ learned のみ ≥3 / EP header 親設計 pointer v2.4→v2.7 / EP status 行 v1.2→v1.5。
  - **RV5-W-P0-2**（SCRIPTED/WAIT TP 恒久不能）= **EP §3c lineage 層に TP N/A 規則追加**（Rs 案 1 採用; 案 2〔EXECUTION_PROVENANCE 分割〕は不採用 — 実行来歴は source-closure が identity で担い、新 component は schema 拡大に見合わない）+ EP §4 表 TP 行 = learned lineage 条件付き + 判別 corpus。
  - **RV5-W-P0-3**（proof binding 3 gap）= gap1: **TrainingProvenance += `final_training_config_hash` + `final_source_commit`**（§1.3 + §3 表の lineage 別 必須/null 規則; BC_ONLY の唯一 stage config は final_* が担い bc_* は C-CH10 どおり null）/ gap2: **EP §3d に TP→final_artifact_hash 束縛行** / gap3: **`certify_definition(..., proof_artifact_resolver)`**（Rs 2 案中 resolver 案採用）+ E_PROOF_ARTIFACT_UNRESOLVED / E_EVALUATOR_UNKNOWN。
  - **RV5-W-P0-4**（BehaviorSignature の semantic schema 欠落）= **§3-4 列挙を 13 面に訂正**（semantic_obs/action_schema 追加 — 補集合定義と列挙の矛盾解消）+ 2 mutation tests。
  - **RV5-W-P0-5**（handoff/registry 曖昧）= producer_handoff_schema_hash = v2.6 先行治癒 / **registry projection = 本版で transitive 化**（definition 参照部分集合のみ bind — 無関係 schema の churn 排除、Rs 逐語採用）+ global schema_id 一意性は E_REGISTRY_DUPLICATE が登録境界で担保。
  - **RV5-W-P0-6**（機械可読 policy object 不在）= **`WMSO_EvidencePolicy_v1.6.json` を normative fixture として新設**（total map + binding + profiles + resolver 規則）。semantic hash 値は WCJ 実装を要するため **impl 時 golden test で確定**（手計算 hash の先行掲載はしない — 検証不能な自己申告を作らない）。
  - **RV5-W-P1-1**（delta doc）= v2.6 full snapshot で先行治癒。
  - **RV5 §6-5 freeze 指示**= status 行 + §10 carries に反映（bounded fix 完了 → freeze → D1.1-B/C へ）。
  - （RV5 §5 arm 系 = p4/p5 管轄 — 本 node 対象外。）
- **G→fold-map（pS §12 全区間 re-check PASS-WITH-CONDITIONS、v2.7.1 宛）**:
  - **G-1**（records）= §4 の「EvidencePolicy v1.4」→ **v1.6**（同期注記付き — W-P0-1 型 stale の 2 度目につき「EP header と同期更新」規則を行内に固定）。
  - **G-2**（records）= §8/§11 の「11 面」→ **13 面**（body §3-4 と整合 — impl の過少 test を防止）。
  - **G-3**（records）= header の pS record bank cite `cd5482310d` → **本 v2.8 commit で §12 込み re-bank**（以後 addendum 毎に同 commit re-bank 規則を明記 — RV5 §7-8 充足）。
  - **G-4**（MEDIUM・実欠陥と確認）= **EP v1.6 §3d: SOURCE_COMMIT / CONFIG_HASH を kind 条件付き束縛に**（SCRIPTED/WAIT claim = closure source commit / runtime_config slot hash）→ **非学習 skill が POLICY_ARTIFACT 等で HB(3) に到達可能 = CLOSED_LOOP eligible**（intent = (a) 非学習 evidence path — closed-loop で scripted skill を使えない設計は WMSO の目的〔scripted/transition/recovery/wait 依存 — review-1 逐語〕に反するため (b) SHADOW cap は不採用）。EXACT(4) は非学習で到達不能のまま（訓練時 proof 実体なし — HB と同 ceiling row ゆえ機能欠損なし・明示 bound として EP に記録）。JSON fixture 同期 + **filename を v1.6 に改名**（C-P0-4 の filename/内容同期規則を自遵守）。corpus: SCRIPTED POLICY_ARTIFACT HB 到達 → CLOSED_LOOP eligible / EXACT 要求 → E_PROOF_INSUFFICIENT（期待）。
- **RV6→fold-map（Rs review v6、対象 = v2.7.1 世代 bundle; §8 records 8 項中 1/2/4/5 = v2.8 で先行治癒）**:
  - **RV6 §1**（transcript 確認の別 record 化）= `WMSO_RS_REVIEW4_FIDELITY_CONFIRM_20260719.md` 新設（履歴 file 不変・分岐解消）。
  - **RV6 §2**（semantic hash 二重定義）= JSON を **{metadata, policy_definition} 二層化**・hash = H_WCJ(policy_definition) に一意化・EP §6 の projection member 16 個を JSON と定義上同一に（pN C2 と同根）。**hash 実算出・掲載 = `066eed1049f4…`**（導出 command 埋込・第三者再計算可能）。
  - **RV6 §3**（HB の schema/spec 成立不能 + artifact_hash 未束縛）= **`claim_target_hash` 機構**: EvidenceRecord field 改名 + 全 13 component の導出表（EP §3d）+ REPRODUCED == claim_target + TTCB (claim_target, manifest) + manifest 列挙も claim_target に一般化（**pN C1 の S 系 6 cell・EXACT 8 cell 不整合を同時解消**）。
  - **RV6 §4**（SCRIPTED/WAIT binding + resolver）= G-4 で先行治癒（kind 条件付き束縛）+ **本版で `ExecutionProvenance` 型を採用**（Rs sketch 逐語 + coherence 2 本 — fixture 依存を definition 内へ）+ **resolver 分割 `resolve_artifact` / `resolve_git_commit`**（SOURCE_COMMIT の expected_sha256 不在問題）。
  - **RV6 §5**（evaluator trust）= certify += `evaluator_registry` / certificate += `evaluator_registry_hash` / `EvidenceEvaluationCertificate` 型新設。
  - **RV6 §6**（handoff identity/epoch）= validate_handoff に producer_action_id / producer_definition_hash（== invocation ==H_WCJ(producer_definition)）/ producer_handoff_schema_hash 照合を明記 + **HandoffOffer.handoff_offer_id** + **authority manager 責務分離**（CAS/発行/旧 epoch 拒否/使用済み offer 拒否 = O0 層状態所有・validator は等値検査）。
  - **RV6 §7**（migration UNKNOWN 型不能）= **保守案採用**: fixture 供給可 → Draft / 不能 → E_MIGRATE_STATICS_ABSENT（UNKNOWN 分岐撤回・placeholder 禁止）。
  - **RV6 §8**（records 8 項）= #1 title/status（v2.8 で解消）#2 EP v1.4 参照（G-1）#3 transcript 表記分岐（fidelity record + header 更新）#4 pS bank cite（G-3）#5 EP 親 pointer（v1.7 で v2.9 に）#6 JSON「impl 時作成」文言（EP §6 訂正）#7 JSON sha の記載所在（header + manifest に明記）#8 manifest「本 commit」（bank 後に具体 id 記入）。
  - **RV6 §9**（JSON の自然言語 rule）= proof_binding を **when/target_path の typed 配列**に・applicability_rules/trust_boundary/evaluator_registry_rule も typed 化（Rs 例示形式そのまま）。
  - **RV6 §10**（bounded fix → freeze）= status 行反映。版名 collision（Rs 命名 v2.8/v1.6 → 実版 v2.9/v1.7）は header で loud 記録。
- **C→fold-map（pN v2.8 再 verify ⛔HOLD C1-C3、16:26 — B1-B3/B5-B7 CLOSE・B4 residual 継承）**:
  - **C1 CRITICAL**（HB S 系 6 cell の reproduced 対象未定義）= RV6 §3 の claim_target 機構で解消（上記 — S 系の anchor = H_WCJ(spec)、FINAL 非要求 cell の意味を定義済みに）+ S 系/非学習 golden・negative corpus（§8）。
  - **C2 HIGH**（hash projection 矛盾 + semantic SHA 未発行）= RV6 §2 の二層化 + **banked JSON から実算出・掲載**（導出 command 付き — ASCII 部分集合ゆえ WCJ == RFC8785 が成立、impl golden test が再確認）。
  - **C3 HIGH**（構成型の ≡ v1 pointer / §9 layout pointer）= **本版で全 inline**（SemanticFieldSpec/InitiationSpec/SupportBoundary/Ownership/BeliefRef/ProducerOutcome/enums の field 集合 + §9 module list —「repo/git show 不要」宣言と整合化）。
- pS D/V 系・review-4 fold-map（§12 相当）= v2.2 の記録を継承（transcript 参照）。

## 12. review-4（R4-）→ fold-map（inline; Rs 見出し verbatim は transcript 参照）

| review-4 # | fold 先 |
|---|---|
| R4-P0-1 | §0 / §5A / §5B / metamorphic #10 |
| R4-P0-2 | §1.1–§1.5 |
| R4-P0-3 | §2 |
| R4-P0-4 | §4 + EvidencePolicy artifact |
| R4-P0-5 | §7 |
| R4-P0-6 | §6（6-1..6-8） |
| R4-P1-1..P1-4 | §5D / §5A / §5C / §1.4 FreshnessPolicy+§5B |
| R4-T | §8 |
| R4-OP | §2.4 / §2-6・7 / §7 SchemaVersionStamp / §10 |
| R4-header | 冒頭 |
