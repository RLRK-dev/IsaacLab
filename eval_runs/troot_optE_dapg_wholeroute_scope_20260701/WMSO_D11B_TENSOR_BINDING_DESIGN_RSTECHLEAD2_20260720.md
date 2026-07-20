# WMSO D1.1-B `tensor_binding` — DESIGN (v1)

- node: `T-WMSO`; author = w2:pQ (RS-TECH-LEAD2); 記録 = **2026-07-20 09:56 JST（実測 09:56:56）**
- 統治: **scope prereg v1.1.1**（`ffd06623e22f…` @ `cf94601f7a`、pN SCOPE CONCUR `0a5d0969218c…` @ `ccd8342c30`）§2 IN の実装設計。**土台 = frozen D1.1-A v2.11.2 package（DESIGN `00192d20ca00b654…` / EP v1.9 `c474acea7c58…` / JSON v1.9 `e63176af9bc3…`）— 本 doc は frozen 3 file を編集しない・schema delta を導入しない**（必要が生じたら supersession + Rs review 経由 — prereg §1.3）。
- **binding carries 遵守宣言**: pS **C-1**（METHOD_REGISTRY enum-vs-row 境界 — 本 doc は frozen enum〔TrainingMethodClass / TrainingLineage / Dtype / ControlMode 等〕に member を追加しない。§1 の B-internal enum は**新 schema の内部語彙**であり frozen A enum の変更ではない）/ pS **C-2**（drive-substrate stale taxonomy 焼込み禁止 — §1.6 TimingSpec は SI 物理量のみ・substrate substep 語彙なし・U-3 disposition = §8-3）/ prereg §6（DC-1..6・RV5 §6 (i)-(iv)・pN (3)・kinematic 写像・L0 手段裁定）。
- gate 位置: §5 chain の **design draft**。次 = 5体 CC Debate → 修正 → pS final-design PASS → pN DESIGN PASS-CLOSE（exact-pin）→ Rs freeze 判定。**impl/training/authority = CLOSED 継続**。

## 0. 中心構造

```text
TensorBindingSpec = 「semantic schema（意味）↔ 訓練時 tensor（メモリ配置）の全単射宣言」を
content-addressed artifact にしたもの。
ExecutionBundle.tensor_binding (ArtifactSlot) が指す実体 = H_WCJ(TensorBindingSpec)。
役割: (a) 訓練時 feature 順序・変換・境界の機械可読固定
      (b) BC/demo 段と RL 段の binding 一致を機械判定（fail-closed）
      (c) TENSOR_BINDING evidence（EP v1.9 既存 component）の attest 対象を確定
      (d) belief/vision 入力の schema 水準 bind（artifact 水準は D1.1-C）
```

- **反循環規則（D1.1-A M2 教訓の適用)**: TensorBindingSpec は **SkillActionId / ExecutionBundleHash / 自身の hash を内包しない**（bundle → binding の単方向参照のみ。逆向き pin は validator が外部で照合）。
- 直列化 = **frozen DESIGN §2 WCJ をそのまま適用**（新 canonicalization 規則を追加しない。float 型拒否 → 実数は全て CanonicalDecimal 文字列。enum `.value` = member 名 ASCII。tuple → array。Optional None → 明示 `null`（省略しない — 全域表現）。frozenset → 文字列 bytes 昇順 array〔§2.3〕）。package 全体への JCS 展開は D1.1-C（prereg §3）。

## 1. 型定義（B-internal 新 schema — frozen A 型は参照のみ）

### 1.1 B-internal enum（新 schema 内部語彙 — C-1 非抵触）

```python
class FeatureSource(Enum):    SEMANTIC_OBS | SEMANTIC_ACTION | BELIEF | HANDOFF
class HistoryOrder(Enum):     OLDEST_FIRST | NEWEST_FIRST
class HistoryPadding(Enum):   ZERO_PAD | REPEAT_OLDEST
class MaskSemantics(Enum):    ONE_IS_VALID | ZERO_IS_VALID
class NormalizerScheme(Enum): MEAN_STD | MIN_MAX
class QuatConvention(Enum):   WXYZ_UNIT | XYZW_UNIT
class StageBindingRelation(Enum): IDENTICAL | EXPLICIT_SUPERSEDE
```

全て hash-visible・`.value` = member 名（§2.3 準拠）。member 追加 = binding_schema_version bump + 本 design の supersession 版（黙って増やさない）。

### 1.2 FeatureBinding（obs/action 共通の 1 feature 結線）

```python
@dataclass(frozen=True)
class ValueTransform:      # y = scale * x + bias（訓練時に適用された実数 affine; WCJ float 拒否ゆえ decimal 文字列）
    scale: CanonicalDecimal
    bias: CanonicalDecimal
@dataclass(frozen=True)
class BoundsSpec:          # 訓練時に仮定した値域（post-transform 空間）
    lower: CanonicalDecimal | None
    upper: CanonicalDecimal | None      # 両方 null は不可 (E_BINDING_BOUNDS_EMPTY)
@dataclass(frozen=True)
class NormalizerBinding:   # 実値 (mean/std 等) は ExecutionBundle.normalization artifact 側 — 結線のみ（二重保持 drift 排除）
    scheme: NormalizerScheme
    stats_key: str          # normalization artifact 内 entry key（NFC・非空）
@dataclass(frozen=True)
class FeatureBinding:
    field_id: str           # 参照先 semantic field（NFC・非空）
    source: FeatureSource   # field_id の解決先: SEMANTIC_OBS→semantic_obs_schema / SEMANTIC_ACTION→semantic_action_schema / BELIEF→InitiationSpec.required_belief_fields ∪ belief schema / HANDOFF→accepted handoff schema fields
    offset: int             # 訓練時 flat vector 内開始 index（element 単位）
    length: int             # == prod(shape)（E_BINDING_LENGTH_SHAPE_MISMATCH）
    dtype: Dtype            # frozen Dtype 参照 — SemanticFieldSpec.dtype と等値必須
    shape: tuple[int, ...]  # SemanticFieldSpec.shape と等値必須
    unit: str               # SemanticFieldSpec.unit と等値必須（意味変換は transform が担う — unit 換算を暗黙にしない）
    frame: str              # SemanticFieldSpec.frame と等値必須
    quaternion: QuatConvention | None   # quaternion field のみ非 null・その場合 shape 末尾 = 4 必須
    normalizer: NormalizerBinding | None
    transform: ValueTransform | None
    bounds: BoundsSpec | None
```

### 1.3 ObsBinding / 1.4 ActionBinding

```python
@dataclass(frozen=True)
class HistorySpec:  depth: int（≥1）; order: HistoryOrder; padding: HistoryPadding
@dataclass(frozen=True)
class TimingSpec:   # C-2: SI 物理量のみ。substrate の substep 数・solver 語彙を持たない
    policy_rate_hz: CanonicalDecimal        # 訓練時 policy 呼出し周波数 [Hz]
    obs_sampling_rate_hz: CanonicalDecimal  # 訓練時 obs 標本化周波数 [Hz]
    max_obs_staleness_s: CanonicalDecimal | None   # 訓練時に仮定した obs 鮮度上限 [s]（runtime 鮮度は FreshnessPolicy — 役割分離）
@dataclass(frozen=True)
class MaskBinding:
    mask_field_id: str            # ∈ 宣言 features（vector 内に実在する validity field）
    semantics: MaskSemantics
    applies_to: frozenset[str]    # ⊆ 宣言 features・自己参照禁止
@dataclass(frozen=True)
class BeliefInputBinding:         # U-2 disposition（§8-2）: schema 水準 = 本 spec / producer artifact 水準 = D1.1-C
    belief_field_id: str
    producer_schema_hash: str     # 64-hex — belief SCHEMA の content hash（producer の weights/artifact hash ではない）
@dataclass(frozen=True)
class ObsBinding:
    features: tuple[FeatureBinding, ...]   # tuple 順 = 訓練時 feature 順序（宣言そのもの — RV5-W-P0-5 の「宣言 tuple 順保持」と同思想）
    total_dim: int                          # per-step flat 次元。history stack 時の実入力次元 = total_dim × history.depth（規約）
    history: HistorySpec | None
    timing: TimingSpec
    masks: tuple[MaskBinding, ...]
    belief_inputs: tuple[BeliefInputBinding, ...]   # source=BELIEF の全 feature を被覆必須（E_BINDING_BELIEF_UNBOUND）
@dataclass(frozen=True)
class ActionBinding:
    features: tuple[FeatureBinding, ...]   # source = SEMANTIC_ACTION のみ
    total_dim: int
    control_mode: ControlMode              # frozen enum 参照 — ExecutionBundle.control_mode と等値必須（LEARNED ⇒ DIFF_IK_EE_TARGET — §0 DiffIK-only の契約層執行を維持）
    action_scale: ValueTransform | None    # 全次元共通 scale。per-feature transform との併用 = 二重適用につき禁止（E_BINDING_SCALE_DOUBLE）
```

- **action の fail-closed 追加則**: 全 action feature は `bounds` 必須（E_BINDING_ACTION_UNBOUNDED — 無界 action の訓練時仮定は宣言不能）。「action scale ⊂ TensorBindingSpec」（frozen DESIGN §1.2 N-a）は `action_scale` + per-feature `transform` で履行。

### 1.5 lineage 宣言（prereg §2 IN-2 — BC+RL / RL-only 双方の fail-closed bind）

```python
@dataclass(frozen=True)
class BcStageBinding:
    demo_dataset_binding_hash: str          # 64-hex — demo/BC 段で使用された TensorBindingSpec の H_WCJ（demo dataset 側記録 = D1.1-C manifest が供給）
    relation: StageBindingRelation          # IDENTICAL = 最終（本）binding と同一 / EXPLICIT_SUPERSEDE = 明示供述付きで異なる
    superseded_detail: str | None           # EXPLICIT_SUPERSEDE ⇔ 非 null（何をなぜ変えたか）
@dataclass(frozen=True)
class LineageBindingDeclaration:
    training_lineage: TrainingLineage       # frozen enum 参照（member 追加なし — C-1）
    bc_stage_binding: BcStageBinding | None # demo/BC を含む lineage（BC_ONLY / BC_THEN_RL / DEMO_PLUS_RL）⇔ 必須。RL_ONLY / NOT_APPLICABLE ⇒ null 必須
```

- **整合規則（validator — §4）**: `TensorBindingSpec.lineage_declaration.training_lineage == TrainingProvenance.training_lineage`（E_BINDING_LINEAGE_MISMATCH）。`relation=IDENTICAL` なのに demo 側記録 hash ≠ 本 spec の H_WCJ → E_BINDING_STAGE_MISMATCH（照合は両 artifact を外部で比較 — 自己 hash 内包はしない〔§0 反循環〕）。

### 1.6 TensorBindingSpec（top-level）

```python
@dataclass(frozen=True)
class TensorBindingSpec:
    binding_schema_version: str   # "1.0"（形式 "MAJOR.MINOR"）
    obs: ObsBinding
    action: ActionBinding
    lineage_declaration: LineageBindingDeclaration
tensor_binding_hash = H_WCJ(TensorBindingSpec)   # ExecutionBundle.tensor_binding.artifact_hash の実体
```

## 2. DC-1 fail-closed 規則の形式化

frozen DESIGN §1.2 の kind 別許容表・`resolved()` は不変のまま、以下が**構造的に**成立する（新規則の追加ではなく確認）:

1. certified LEARNED bundle は `resolved()` ⇒ tensor_binding = KNOWN（64-hex）。
2. ClosedLoopProfile は TENSOR_BINDING evidence を要求（EP v1.9 既存）。evidence の attest 対象 artifact = 本 spec（§3）。
3. **D1.1-B impl 完了前は TensorBindingSpec artifact が存在しない → KNOWN hash を正当に供給できない → closed-loop eligibility は自動的に不成立**（DC-1 逐語「当該 skill は closed-loop eligibility を得られない」の機構）。placeholder hash 生成は禁止（D1.1-A migration と同規律）。

## 3. EP 結合 — TENSOR_BINDING evidence の attest 対象確定（EP 変更なし）

**EP v1.9 実測接地**（本 session、frozen JSON `e63176af…`）: TENSOR_BINDING / CONTROL_MODE は `claim_targets` と proof_policy に**既存**。TB の proof set = **EXACT_TRAIN_TIME: {TRAIN_RUN_MANIFEST, SOURCE_COMMIT, CONFIG_HASH}** / **HASH_BOUND_REPRODUCED: {SOURCE_COMMIT, CONFIG_HASH, FINAL_ARTIFACT_HASH, REPRODUCTION_PROCEDURE, REPRODUCED_OUTPUT_HASH, EVALUATOR_ARTIFACT}** / RECONSTRUCTED_COMPATIBLE・DIMENSION_ONLY 行 = **なし**（TB は暗号学的束縛か再現のみ — 「復元互換」水準の layout 主張を認めない設計を EP が既に固定）。

本 doc は proof の **subject semantics**（何を示せば TB evidence として成立するか）を確定する（normative な proof set = EP のまま・EP 非改訂）:

| ProofKind | TENSOR_BINDING における attest 内容 |
|---|---|
| TRAIN_RUN_MANIFEST | 訓練 run manifest（D1.1-C artifact）が `tensor_binding_hash` と訓練時 obs/action 実次元（total_dim × history）を pin していること |
| SOURCE_COMMIT | `TrainingProvenance.final_source_commit` の source が同 binding を生成/消費すること |
| CONFIG_HASH | `final_training_config_hash` の config から binding が導出可能 or 埋込まれていること |
| REPRODUCTION_PROCEDURE / REPRODUCED_OUTPUT_HASH | 手続再走で TensorBindingSpec を再導出し H_WCJ が宣言値と一致（REPRODUCED_OUTPUT_HASH = 再導出 spec の H_WCJ） |
| FINAL_ARTIFACT_HASH / EVALUATOR_ARTIFACT | 対象 weights / 検査器の content pin（EP §3d 既定義のまま） |

## 4. Validation 規則（fail-closed・全 E_ 列挙）

**値/構造**: E_BINDING_LENGTH_SHAPE_MISMATCH（length ≠ prod(shape)）/ E_BINDING_COVERAGE_GAP・E_BINDING_OVERLAP（offset 連鎖が [0, total_dim) を丁度被覆しない — 順序 = tuple 順で offset[0]=0・offset[i+1]=offset[i]+length[i]・終端=total_dim）/ E_BINDING_DUPLICATE_FIELD（field_id 重複）/ E_BINDING_NONFINITE（CanonicalDecimal 正規形違反 — scale・bias・bounds・rate・staleness 全数、DC-4: NaN/±Inf は型層で拒否される上、decimal 正規形 re 照合）/ E_BINDING_BOUNDS_EMPTY・E_BINDING_BOUNDS_INVERTED（lower > upper）/ E_BINDING_TIMING_NONPOSITIVE（rate ≤ 0・staleness < 0）/ E_BINDING_HISTORY_INVALID（depth < 1）/ E_BINDING_QUAT_ON_NONQUAT（quaternion 非 null かつ shape 末尾 ≠ 4）。
**schema 照合（SemanticFieldSpec との等値）**: E_BINDING_FIELD_UNKNOWN（field_id が source の schema に不在）/ E_BINDING_DTYPE_MISMATCH / E_BINDING_SHAPE_MISMATCH / E_BINDING_UNIT_MISMATCH / E_BINDING_FRAME_MISMATCH。
**mask/belief**: E_BINDING_MASK_TARGET_ABSENT（applies_to ⊄ features）/ E_BINDING_MASK_SELF（自己参照）/ E_BINDING_MASK_FIELD_ABSENT（mask_field_id ∉ features）/ E_BINDING_BELIEF_UNBOUND（source=BELIEF feature に対応する BeliefInputBinding 欠落）/ E_BINDING_BELIEF_ORPHAN(逆向き孤児) / E_BINDING_HASH_MALFORMED（64-hex 違反）。
**bundle/provenance 整合（cross-artifact — certify 時）**: E_BINDING_CONTROL_MODE_MISMATCH（action.control_mode ≠ bundle.control_mode.value）/ E_BINDING_NORMALIZER_MISSING（stats_key が normalization artifact に不在）/ E_BINDING_NORMALIZER_ORPHAN（normalization artifact の entry が未消費 — 両方向 total 被覆）/ **normalizer 全 null ⇔ bundle.normalization = EXPLICIT_NONE の coherence**（E_BINDING_NORM_COHERENCE — frozen §1.2† の evidence-gated 規則と両立: EXPLICIT_NONE 宣言時に binding 側が normalizer を持てば矛盾）/ E_BINDING_SCALE_DOUBLE / E_BINDING_ACTION_UNBOUNDED / E_BINDING_LINEAGE_MISMATCH / E_BINDING_STAGE_MISMATCH / E_BINDING_STAGE_DECLARATION_MISSING（demo 系 lineage で bc_stage_binding = null / 逆に RL_ONLY で非 null）/ E_BINDING_SUPERSEDE_DETAIL_MISSING（EXPLICIT_SUPERSEDE ⇔ superseded_detail 非 null 違反）。
**適用位置**: 値/構造/schema 照合 = TensorBindingSpec 単体 validator（standalone）。cross-artifact = `certify_definition()` の追加検査群（frozen の certify 出力型は不変 — issues に E_BINDING_* が加わるのみ。**frozen A の validator 規則の変更ではなく、B artifact が KNOWN で供給された場合に追加走行する検査**）。

## 5. handoff の grasp/contact stability encode（RV5 §6 (ii) — B の semantic spec 設計入力）

**canonical stability field group `cable_handoff_stability` v1.0**（HandoffSchemaSpec.fields へ組込む SemanticFieldSpec 群 — frozen §5D 照合機構は不変のまま、**内容**を確定）:

| field_id | dtype | shape | unit | frame | 意味 |
|---|---|---|---|---|---|
| `grasp_engaged_left` / `grasp_engaged_right` | BOOL | [1] | dimensionless | none | 各腕の把持係合（コ形 finger の係合判定 — 判定器は slice prereg で確定） |
| `contact_stable_left` / `contact_stable_right` | BOOL | [1] | dimensionless | none | 接触の時間安定（瞬時値でなく窓判定 — 窓幅 = slice prereg） |
| `chain_topology_class` | INT32 | [1] | dimensionless | none | cable chain の離散位相 class（**1 mrad 級 pose 差と独立の離散状態** — RV5 §6 (ii) の核心。class 台帳 = slice prereg fixture、ここでは field 契約のみ） |
| `grasp_span_error` | FLOAT32 | [1] | m | none | 実把持スパンの 88 mm 基準からの誤差（±） |

- **必須化**: cable を運ぶ handoff schema は本 group を `required_field_ids` に含める（producer が値を供給できない場合はその handoff を宣言できない — fail-closed）。pose 系 field（既存）に**追加**であり置換ではない。
- 語彙は substrate 中立（C-2 — solver/drive 語なし）。値の算出法・閾値は**契約でなく計測設計**であり slice 詳細 prereg / D2 fixture が確定（ここに焼込まない）。

## 6. Golden vectors / invalid corpus（DC-4 の B 適用）

**golden（本 session 実算出 — 再現 command 下記・pS/pN 独立再計算対象）**:

| # | 内容 | H_WCJ (sha256) |
|---|---|---|
| G-1 | 最小 RL_ONLY（obs 2 feature / action 2 feature / history・normalizer・mask なし） | `f7684084b3fe38c3c75587fe678b2f941e4e39e4228265964377649d66fdd496` |
| G-2 | DEMO_PLUS_RL（quat + BELIEF 2 feature + MEAN_STD normalizer + history 3 + mask + bc_stage IDENTICAL） | `4cd18a02811bbb4be7775dc14e523880eafacd998bb24b4c613793b5c4290c6f` |

- 補助 pin: G-2 の `producer_schema_hash` = sha256("WMSO-D11B-GOLDEN-BELIEF-SCHEMA-V1") = `744866166f80fd99…` / `demo_dataset_binding_hash` = sha256("WMSO-D11B-GOLDEN-DEMO-STAGE-BINDING-V1") = `0ab17d9306ac6234…`（fixture 用の宣言的導出 — 実在 artifact の hash ではない）。
- canonical bytes = G-1: 1265 / G-2: 1818。**再現**: fixture の canonical JSON（impl 時に `tests/fixtures/` へ同梱）に対し `python3 -c "import json,hashlib,sys; print(hashlib.sha256(json.dumps(json.load(open(sys.argv[1])),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest())"`（ASCII key subset では frozen §2 WCJ と一致 — 非 ASCII key の golden は frozen §2 §8 の既存 vector が担う）。
- **invalid corpus（拒否必須 — 抜粋・impl で全列挙）**: NaN/"Infinity"/float 型の scale・bias・bounds / "01"・"1.10"（decimal 非正規形）/ offset gap・overlap / length ≠ prod(shape) / total_dim 不一致 / field_id 重複・NFC 非正規 / dtype・unit・frame 不一致 / quat on shape≠[..,4] / mask 自己参照・宛先不在 / BELIEF feature の binding 欠落 / bounds inverted / depth 0 / rate "0" / RL_ONLY + bc_stage_binding 非 null / EXPLICIT_SUPERSEDE + detail null / 64-hex 違反 / unknown enum member / unknown JSON field / duplicate canonical key / bool を int shape に混入。

## 7. Test plan（impl GO 後 — 設計時宣言）

standalone unit（配布物のみで全実行 — frozen §7c と同型）: 型 round-trip（encode→decode→encode 同一 bytes）/ golden G-1・G-2 一致 / invalid corpus 全拒否 / coverage 算術 property test（ランダム layout 生成→gap/overlap 検出）/ cross-artifact 検査（fixture bundle + normalization artifact での NORMALIZER_MISSING・ORPHAN・NORM_COHERENCE・CONTROL_MODE_MISMATCH・LINEAGE_MISMATCH・STAGE_MISMATCH の赤→緑 pair）/ §5 stability group の HandoffSchemaSpec 組込み fixture（§5D 照合が通る/落ちる pair）。

## 8. 未解決点 disposition（prereg §8 U-1/U-2/U-3）

1. **U-1（epoch 結合）= B は epoch field を持たない（確定案）**: stale-epoch 検査は frozen §7 runtime（`offer.control_epoch == authority_epoch_snapshot`・E_HANDOFF_EPOCH_STALE）が既に担う。binding は静的 artifact であり epoch を持てば同一 layout が epoch 毎に別 hash になり identity churn（反循環・単一 source 原則）。slice の stale-epoch 必須試験 = frozen runtime 検査 + C の run manifest 記録で充足。
2. **U-2（belief/vision 粒度）= 2 層分担（確定案・CC Debate 検証対象）**: **schema 水準**（layout・意味・`producer_schema_hash`）= 本 spec が bind（ActionId に参加 — belief schema が変われば別 identity）。**producer artifact 水準**（encoder weights 等）= D1.1-C run manifest が run 毎に pin し、closed-loop eligibility の C 段検査で照合。根拠: producer 再訓練の度に policy identity が churn するのは過剰（policy の重み・binding は不変）だが、無 pin は silent swap を許す — schema は identity / artifact は run 記録という分担が両失敗を塞ぐ。
3. **U-3（drive-substrate lineage）= B に導入しない（確定・C-2 履行）**: kinematic 全削除 rework（DDR #25/#26）進行中につき rework 前 taxonomy を焼込まない。data の substrate 識別 = D1.1-C `substrate_id`（RV5 §6 (i)）が担う。契約層で drive taxonomy が必要と判明した場合のみ schema delta として Rs review 経由（frozen §10 (c) と同経路）。

## 9. Module layout（impl GO 時に確定 — 設計宣言のみ）

`thread_isaac_lab/wmso/contracts_v2/tensor_binding.py`（型 + 単体 validator）+ `certify.py` への cross-artifact 検査追加 + `tests/test_tensor_binding.py` + `tests/fixtures/tensor_binding_golden_{1,2}.json`。**本 chunk では書かない**（impl = CLOSED）。

## 10. Open points

- 本 v1 = CC Debate 未通過（§5 chain の次段）。U-2 の 2 層分担・§5 field group の過不足・E_ 網羅性が主な debate 対象と自己申告。
- §5 `chain_topology_class` の class 台帳と判定器、§5 窓判定幅 = slice 詳細 prereg へ委譲（本 doc は field 契約のみ — 「契約 ≠ 計測設計」境界）。
- 「open = 0」の無条件宣言はしない（frozen §10 と同規律 — 未充足 gate = CC Debate → pS final → pN exact-pin → Rs freeze）。

## 11. 版歴

- v1（2026-07-20 09:56 実測）: 初版。prereg v1.1.1 §2 IN 1-7 の全項実装（IN-1 = §1 / IN-2 = §1.5・§4 / IN-3 = §1.6・§2 / IN-4 = §3 / IN-5 = §5 / IN-6 = §6 / IN-7 = §8-3）。
