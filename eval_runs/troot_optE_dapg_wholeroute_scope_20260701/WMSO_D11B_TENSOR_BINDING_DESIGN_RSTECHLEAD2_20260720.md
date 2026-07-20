# WMSO D1.1-B `tensor_binding` — DESIGN (v2)

- node: `T-WMSO`; author = w2:pQ (RS-TECH-LEAD2); v1 = 2026-07-20 09:56 JST; **v2 = 2026-07-20 11:10 JST（実測 — CC Debate cycle-1 FAIL の fold。版歴 = §12）**
- 統治: **scope prereg v1.1.1**（`ffd06623e22f…` @ `cf94601f7a`・pN SCOPE CONCUR `0a5d0969218c…` @ `ccd8342c30`）§2 IN の実装設計。**土台 = frozen D1.1-A v2.11.2**（DESIGN `00192d20ca00b654…` / EP v1.9 md `c474acea7c58…` / JSON `e63176af9bc3…`）— **frozen 3 file を編集せず・schema delta を導入しない**（必要時は supersession + Rs review、prereg §1.3）。
- **binding carries 遵守**: pS **C-1**（frozen enum に member を追加しない。§1.1 は B 新 schema の内部語彙）/ pS **C-2**（drive-substrate taxonomy を焼込まない — §1.6 TimingSpec は SI 量のみ・§8-3）/ prereg §6（DC-1..6・RV5 §6 (i)-(iv)・pN (3)・kinematic 写像・L0 手段裁定）。
- gate 位置: §5 chain の **design（cycle-1 debate 済 → fold 済 v2）**。次 = pS final-design PASS → pN DESIGN PASS-CLOSE（exact-pin）→ Rs freeze 判定。**impl/training/authority = CLOSED 継続**。
- **banked fixtures（本 doc と同 commit 系列）**: `wmso_d11b_fixtures/tensor_binding_golden_{1,2,3}.json` + `build_goldens.py`（生成器）。§6 に sha 記載 — pS/pN は banked file から独立再計算可能。

## 0. 中心構造

```text
TensorBindingSpec = 「semantic schema（意味）↔ 訓練時 tensor（メモリ配置）の全単射宣言」を
content-addressed artifact にしたもの。
ExecutionBundle.tensor_binding (ArtifactSlot) が指す実体 = H_WCJ(TensorBindingSpec)。
役割: (a) 訓練時 feature 順序・変換・境界・**要素配置**の機械可読固定
      (b) BC/demo 段と RL 段の binding 一致を機械判定（fail-closed）
      (c) TENSOR_BINDING evidence（EP v1.9 既存 component）の attest 対象を確定
      (d) belief/vision 入力の schema 水準 bind（artifact 水準は D1.1-C へ carry・§8-2）
```

- **反循環規則（D1.1-A M2 教訓 — v2 で構造まで拡張）**: TensorBindingSpec は **自身の hash・SkillActionId・ExecutionBundleHash・および「自身と同一である」ことを主張する任意の hash** を内包しない。**M2 の教訓は field 名 2 個ではなく「自己参照 hash を preimage に置かない」という構造 pattern**（v1 は `demo_dataset_binding_hash` で不動点を再導入した — §12 D-2）。
- 直列化 = **frozen DESIGN §2 WCJ を適用**（新 canonicalization 規則を追加しない）。**inherited（frozen §2/§2.3）** = UTF-16 code-unit key sort / duplicate・lone-surrogate 拒否 / JCS escape / int のみ・float 型拒否 / CanonicalDecimal / NFC / enum `.value` = member 名 / frozenset → 文字列 bytes 昇順 array。**B-declared（本 doc の追加規約 — 継承ではない）** = ①`Optional None` は省略せず明示 `null`（全域表現。省略実装との hash 分岐防止）②`int` field は `type(x) is int`（`bool` 拒否 — `isinstance(True,int)` は真、frozen §2 は bool を裁定していない）③tuple → array（JSON 自明）。package 全体への JCS 展開は D1.1-C。

## 1. 型定義（B-internal 新 schema — frozen A 型は参照のみ）

### 1.1 B-internal enum（新 schema 内部語彙 — C-1 非抵触）

```python
class FeatureSource(Enum):    SEMANTIC_OBS | SEMANTIC_ACTION | BELIEF     # HANDOFF は v1 語彙から除外（§8-4）
class FlattenOrder(Enum):     ROW_MAJOR                                   # v1.0 は 1 member（§1.2）
class HistoryOrder(Enum):     OLDEST_FIRST | NEWEST_FIRST
class HistoryLayout(Enum):    STEP_MAJOR | FEATURE_MAJOR
class HistoryPadding(Enum):   ZERO_PAD | REPEAT_OLDEST
class MaskSemantics(Enum):    ONE_IS_VALID | ZERO_IS_VALID
class MaskScope(Enum):        PER_STEP | ACROSS_STACK
class NormalizerScheme(Enum): MEAN_STD | MIN_MAX
class QuatConvention(Enum):   WXYZ_UNIT | XYZW_UNIT
class ActionHold(Enum):       ZERO_ORDER_HOLD | LINEAR_INTERPOLATE
class StageBindingRelation(Enum): IDENTICAL | EXPLICIT_SUPERSEDE
```

全て hash-visible・`.value` = member 名。**member 追加 = `binding_schema_version` bump + 本 design の supersession 版 + Rs review**（frozen 後は prereg §1.3 と同経路 — C-1 が frozen enum に課す規律を B 自身の enum にも適用。§12 D-28）。

### 1.2 FeatureBinding

```python
@dataclass(frozen=True)
class ValueTransform:  scale: CanonicalDecimal; bias: CanonicalDecimal      # y = scale*x + bias
@dataclass(frozen=True)
class BoundsSpec:      lower: CanonicalDecimal | None; upper: CanonicalDecimal | None   # 両 null 不可
@dataclass(frozen=True)
class NormalizerBinding:  scheme: NormalizerScheme; stats_key: str          # 実値は normalization artifact 側（§4 が値制約も課す）
@dataclass(frozen=True)
class FeatureBinding:
    field_id: str            # 参照先 semantic field（NFC・非空）
    source: FeatureSource    # SEMANTIC_OBS→semantic_obs_schema / SEMANTIC_ACTION→semantic_action_schema / BELIEF→belief schema（§1.3 belief_inputs が producer schema を pin）
    offset: int              # per-step flat vector 内の開始 index（element 単位・history 適用前）
    length: int              # == prod(shape)
    dtype: Dtype             # frozen Dtype 参照 — SemanticFieldSpec.dtype と等値必須（= **semantic dtype**。格納 dtype は §1.4 container_dtype）
    shape: tuple[int, ...]   # SemanticFieldSpec.shape と等値必須
    unit: str                # 等値必須（unit 換算は暗黙にせず transform で表す）
    frame: str               # 等値必須
    flatten_order: FlattenOrder   # **v2 追加**: 多次元 shape の要素順（v1.0 = ROW_MAJOR 固定。torch `.reshape(-1)` と同義）
    quaternion: QuatConvention | None   # quaternion のみ非 null・その場合 shape 末尾 = 4
    normalizer: NormalizerBinding | None
    transform: ValueTransform | None
    bounds: BoundsSpec | None
```

- **flatten_order（§12 D-3）**: `length == prod(shape)` は要素**数**しか固定しない。`shape=[2,3]` は row-major と column-major で別配置になり、v1 は両者が同一 hash になった＝「全単射」主張が偽だった。v1.0 では **ROW_MAJOR のみ**を許し（enum 1 member）、hash-visible に置く（将来 member 追加時に旧 binding の hash が変わらないため）。

### 1.3 ObsBinding

```python
@dataclass(frozen=True)
class HistorySpec:
    depth: int              # ≥1
    order: HistoryOrder     # 時間方向
    layout: HistoryLayout   # **v2 追加**: STEP_MAJOR = [step0 全 feature | step1 全 feature | …] / FEATURE_MAJOR = [feature0 全 step | …]
    padding: HistoryPadding
@dataclass(frozen=True)
class TimingSpec:           # C-2: SI 物理量のみ（substep/solver 語彙なし）
    policy_rate_hz: CanonicalDecimal
    obs_sampling_rate_hz: CanonicalDecimal
    max_obs_staleness_s: CanonicalDecimal | None    # 訓練時仮定（runtime 鮮度 = frozen FreshnessPolicy — 役割分離）
@dataclass(frozen=True)
class MaskBinding:
    mask_field_id: str          # ∈ 宣言 features・**dtype = BOOL 必須**
    semantics: MaskSemantics
    applies_to: frozenset[str]  # ⊆ 宣言 features・自己参照禁止
    scope: MaskScope            # **v2 追加**: stack 下で per-step か全 stack か
@dataclass(frozen=True)
class BeliefInputBinding:
    belief_field_id: str
    producer_schema_hash: str   # 64-hex — belief **SCHEMA** の content hash（producer の weights hash ではない — §8-2）
@dataclass(frozen=True)
class ObsBinding:
    features: tuple[FeatureBinding, ...]   # tuple 順 = 訓練時 feature 順序（非空必須）
    total_dim: int                          # per-step flat 次元。history 適用後の実入力次元 = total_dim × depth（配置は history.layout が決める）
    history: HistorySpec | None
    timing: TimingSpec
    masks: tuple[MaskBinding, ...]
    belief_inputs: tuple[BeliefInputBinding, ...]   # source=BELIEF の全 feature を両方向 total 被覆
    container_dtype: Dtype                  # **v2 追加**: flat vector の格納 dtype（§12 D-16）。feature の semantic dtype と異なる場合は cast が起きることを明示
```

### 1.4 ActionBinding

```python
@dataclass(frozen=True)
class ActionTimingSpec:            # **v2 追加**（prereg IN-1 action 側「control/timing」の履行 — §12 D-?/CC2）
    action_rate_hz: CanonicalDecimal
    hold: ActionHold               # policy step 間の保持規約（ZOH / 線形補間）
@dataclass(frozen=True)
class ActionBinding:
    features: tuple[FeatureBinding, ...]   # 全 feature の source = SEMANTIC_ACTION 必須（非空必須）
    total_dim: int
    control_mode: ControlMode              # frozen enum 参照 — bundle.control_mode と等値必須（LEARNED ⇒ DIFF_IK_EE_TARGET のみ = §0 DiffIK-only の契約層執行）
    action_scale: ValueTransform | None    # 全次元共通 scale。per-feature transform との併用禁止
    timing: ActionTimingSpec
    container_dtype: Dtype
```

- 全 action feature は `bounds` 必須（無界 action の訓練時仮定は宣言不能）。frozen §1.2 N-a「action scale ⊂ TensorBindingSpec」は `action_scale` + per-feature `transform` で履行。

### 1.5 lineage 宣言（prereg IN-2 — BC+RL / RL-only の fail-closed bind）

```python
@dataclass(frozen=True)
class BcStageBinding:
    relation: StageBindingRelation
    demo_dataset_binding_hash: str | None   # **IDENTICAL ⇒ null 必須**（不動点回避 — §0 反循環）/ EXPLICIT_SUPERSEDE ⇒ 64-hex 必須
    superseded_detail: str | None           # EXPLICIT_SUPERSEDE ⇔ 非空
@dataclass(frozen=True)
class LineageBindingDeclaration:
    training_lineage: TrainingLineage       # frozen enum 参照（member 追加なし）
    bc_stage_binding: BcStageBinding | None # demo 系 lineage（BC_ONLY/BC_THEN_RL/DEMO_PLUS_RL）⇔ 必須 / RL_ONLY・NOT_APPLICABLE ⇒ null 必須
```

- **IDENTICAL の意味論（v2 で構造変更・§12 D-2）**: 「BC 段の binding = 本 binding と同一」の主張は **hash を内包せず relation のみで表明**する。検証 = **D1.1-C の run manifest が両段に同一 `tensor_binding_hash` を記録していること**を外部照合（`E_BINDING_STAGE_IDENTICAL_UNCONFIRMED`）。v1 は hash field を spec 内に置いたため `field == H_WCJ(その field を含む spec)` という sha256 不動点を要求し、構成不能かつ M2 循環の再導入だった。
- **EXPLICIT_SUPERSEDE** = BC 段が別 binding だったことの明示供述（hash + 何をなぜ変えたか）。
- 整合規則: `training_lineage == TrainingProvenance.training_lineage`（`E_BINDING_LINEAGE_MISMATCH`）。

### 1.6 TensorBindingSpec（top-level）

```python
@dataclass(frozen=True)
class TensorBindingSpec:
    binding_schema_version: str    # "1.0"（"MAJOR.MINOR"・既知版 allowlist で fail-closed）
    obs: ObsBinding
    action: ActionBinding
    lineage_declaration: LineageBindingDeclaration
tensor_binding_hash = H_WCJ(TensorBindingSpec)   # ExecutionBundle.tensor_binding.artifact_hash の実体
```

- **version 規律（§12 D-13）**: MAJOR/MINOR とも hash-visible ゆえ **bump = identity event**（`tensor_binding_hash` → `ExecutionBundleHash` → `SkillActionId` が変わる）。frozen §7 は「TransitionRecord / SkillInvocation は certified SkillActionId のみを key にする」ゆえ、bump は既存 certificate と収集済 transition 行を stranding させる。したがって **bump は移行計画（再 certify + transition 行の系譜記録）を伴う場合のみ**行い、その手続は **D1.1-C の manifest 側で定義**（本 doc は「bump = identity event である」ことの宣言と `E_BINDING_SCHEMA_VERSION_UNKNOWN` の fail-closed 化までを担う）。

## 2. DC-1 fail-closed 規則の位置づけ（v2 で over-claim 撤回）

1. certified LEARNED bundle は `resolved()` ⇒ `tensor_binding` = KNOWN（64-hex）— frozen §1.1/§1.2 から**構造的**に従う。
2. **TENSOR_BINDING を required とする profile = CLOSED_LOOP（min_grade_rank 3）と SHADOW（同 2）の両方**。OFFLINE_REPLAY のみ `not_applicable`（frozen JSON 逐語「replay does not re-execute binding」）。v1 は closed-loop だけを挙げ、**shadow 運用も同様に gate される事実を落としていた**（§12 D-19）。
3. **B 完了前**: TensorBindingSpec artifact が存在しないため、KNOWN hash を**正当に**供給できない。⚠**v1 はこれを「構造的」と称したが、正しくは「§4 の hash-identity 検査（`E_BINDING_HASH_MISMATCH` / `E_BINDING_ARTIFACT_UNRESOLVED`）が走って初めて構造になる」**（§12 D-5）。v2 は当該検査を §4 に明記し、供給経路を §4「適用位置」で指名する。

## 3. EP 結合 — TENSOR_BINDING evidence の attest 対象（EP 変更なし・v2 で全 grade 再導出）

**⚠v1 の重大な誤り（撤回・§12 D-1）**: v1 §3 は「RECONSTRUCTED_COMPATIBLE / DIMENSION_ONLY 行 = なし ⇒ 復元互換水準の layout 主張を EP が認めない」と書いた。**これは FALSE**。原因 = `proof_policy[grade].get('TENSOR_BINDING')` という **name-scoped query** で不在を導出したこと（EP は grade により per-component / wildcard / applicable-set の 3 形式で符号化する）。**閉じた query での再導出（本 session 実測、frozen JSON `e63176af…`）**:

| grade (rank) | 符号化形式 | TENSOR_BINDING に要求される proof set |
|---|---|---|
| EXACT_TRAIN_TIME (4) | per-component | `TRAIN_RUN_MANIFEST` / `SOURCE_COMMIT` / `CONFIG_HASH` |
| HASH_BOUND_REPRODUCED (3) | per-component | `SOURCE_COMMIT` / `CONFIG_HASH` / `FINAL_ARTIFACT_HASH` / `REPRODUCTION_PROCEDURE` / `REPRODUCED_OUTPUT_HASH` / `EVALUATOR_ARTIFACT` |
| RECONSTRUCTED_COMPATIBLE (2) | **wildcard `_all_13_components`（TB を含む）** | `RECONSTRUCTION_SOURCES` / `COMPATIBILITY_TEST` / `UNRESOLVED_DIFFERENCES` / `EVALUATOR_ARTIFACT` |
| DIMENSION_ONLY (1) | **`_applicable.components` に TB を明示列挙** | `DIMENSION_SOURCE` / `UNRESOLVED_DIFFERENCES` |
| UNKNOWN (0) | wildcard（空） | なし（authority-relevant claim 不可） |

**正しい機構**: closed-loop で復元互換水準の layout 主張が通らないのは「行が無い」からではなく **`profiles.CLOSED_LOOP.min_grade_rank = 3`** だから。**SHADOW は rank 2 ゆえ RECONSTRUCTED_COMPATIBLE の TB evidence を受理する** — したがって最初の slice（shadow 系）が使う grade はこの水準であり、そこでは train-time hash 束縛が存在しない。

**proof の subject semantics（本 doc が確定する部分・全 4 grade）**:

| ProofKind | TENSOR_BINDING における attest 内容 |
|---|---|
| TRAIN_RUN_MANIFEST | frozen `manifest_content_rule` のとおり **manifest が `claim_target_hash`（= `execution_bundle.tensor_binding.artifact_hash`）を列挙**していること。⚠v1 が追加した「訓練時実次元も pin」は frozen 規則を超える強化ゆえ**撤回**し、**D1.1-C prereg への非拘束的推奨**に降格（§12 D-25） |
| SOURCE_COMMIT | `TrainingProvenance.final_source_commit` の source が同 binding を生成/消費すること |
| CONFIG_HASH | `final_training_config_hash` の config が **`tensor_binding_hash` を逐語含む**こと（v1 の「導出可能 or 埋込まれている」は反証不能ゆえ撤回 — `manifest_content_rule` と同型の検査可能述語に置換。§12 D-26） |
| REPRODUCTION_PROCEDURE / REPRODUCED_OUTPUT_HASH | 手続再走で TensorBindingSpec を再導出し `H_WCJ` が宣言値と一致（`REPRODUCED_OUTPUT_HASH` = 再導出 spec の H_WCJ）。**手続は WCJ 実装を用いること**（§6 の注記参照） |
| RECONSTRUCTION_SOURCES | 訓練 code/config/checkpoint 等、layout を再構成した出典の列挙（train-time hash が無い場合の出発点） |
| COMPATIBILITY_TEST | **再構成 binding で policy を実行し、宣言 layout と実 layout の一致を示す実測**（例: 既知入力に対する出力一致 / 各 feature slot への摂動応答が宣言 field に対応すること）。⚠**この grade には train-time の暗号学的束縛が無い**ため、compatibility test が唯一の layout 保証になる — SHADOW 運用の実質的な安全条件はここに集中する |
| UNRESOLVED_DIFFERENCES | 再構成で解消できなかった差分の明示列挙（空でないなら loud） |
| DIMENSION_SOURCE | 次元のみの出典（意味 field は未解決である旨を明示） |
| FINAL_ARTIFACT_HASH / EVALUATOR_ARTIFACT | 対象 weights / 検査器の content pin（EP §3d 既定義のまま） |

## 4. Validation 規則（fail-closed）

**hash / 供給（v2 追加・§12 D-5）**: `E_BINDING_ARTIFACT_UNRESOLVED`（slot = KNOWN だが spec 実体を解決できない）/ `E_BINDING_HASH_MISMATCH`（`H_WCJ(解決した spec) ≠ slot.artifact_hash`）/ `E_BINDING_HASH_MALFORMED`（64-hex 違反）。
**版**: `E_BINDING_SCHEMA_VERSION_MALFORMED`（"MAJOR.MINOR" 違反）/ `E_BINDING_SCHEMA_VERSION_UNKNOWN`（既知版 allowlist 外 = fail-closed）。
**値/構造**: `E_BINDING_LENGTH_SHAPE_MISMATCH` / `E_BINDING_COVERAGE_INVALID`（offset 連鎖が `[0, total_dim)` を丁度被覆しない。⚠v1 の GAP/OVERLAP 2 code は算法上 overlap が表現不能で到達不能だったため **1 code に統合**・§12 D-18）/ `E_BINDING_EMPTY_FEATURES`（obs/action とも非空必須）/ `E_BINDING_DUPLICATE_FIELD` / `E_BINDING_INT_TYPE`（`offset`/`length`/`total_dim`/`depth` に `type(x) is int` — bool 拒否）/ `E_BINDING_NONFINITE`（CanonicalDecimal 正規形違反 — scale・bias・bounds・rate・staleness 全数）/ `E_BINDING_BOUNDS_EMPTY`・`E_BINDING_BOUNDS_INVERTED` / `E_BINDING_TIMING_NONPOSITIVE`（rate ≤ 0・staleness < 0）/ `E_BINDING_HISTORY_INVALID`（depth < 1）/ `E_BINDING_QUAT_ON_NONQUAT`。
**source 制約（v2 追加・§12 D-8）**: `E_BINDING_SOURCE_FORBIDDEN`（action 側に `source ≠ SEMANTIC_ACTION` / obs 側に `SEMANTIC_ACTION`〔前 action feedthrough は v1.0 では非対応・§8-4〕）。
**schema 照合**: `E_BINDING_FIELD_UNKNOWN` / `E_BINDING_DTYPE_MISMATCH` / `E_BINDING_SHAPE_MISMATCH` / `E_BINDING_UNIT_MISMATCH` / `E_BINDING_FRAME_MISMATCH`。
**mask（v2 強化・§12 D-15）**: `E_BINDING_MASK_TARGET_ABSENT` / `E_BINDING_MASK_SELF` / `E_BINDING_MASK_FIELD_ABSENT` / `E_BINDING_MASK_DTYPE`（mask_field_id の dtype ≠ BOOL）/ `E_BINDING_MASK_SHAPE`（mask の要素数が対象と非整合 — 1 要素の全体 gate か同 shape の要素毎かを scope と併せ判定）。
**belief**: `E_BINDING_BELIEF_UNBOUND` / `E_BINDING_BELIEF_ORPHAN` / `E_BINDING_BELIEF_DUPLICATE`（同一 `belief_field_id` の重複 entry・§12 D-20）/ `E_BINDING_HASH_MALFORMED`（producer_schema_hash）。
**cross-artifact（certify 時・全 operand slot が KNOWN の時のみ発火** — §12 D-7）: `E_BINDING_CONTROL_MODE_MISMATCH` / `E_BINDING_NORMALIZER_MISSING`（stats_key 不在）/ `E_BINDING_NORMALIZER_ORPHAN` / `E_BINDING_NORMALIZER_VALUE`（**v2 追加**: stats_key の指す mean/std が isfinite でない、または `std ≤ 0` — frozen §5 U13 が本 chunk に名指しで委譲した義務の履行・§12 D-17）/ `E_BINDING_NORM_COHERENCE`（**v2 で一方向化**: `bundle.normalization = EXPLICIT_NONE ⇒ 全 normalizer null`。**逆方向は課さない** — v1 の双条件は frozen §1.2† の evidence-gated EXPLICIT_NONE と deadlock し、`empirical_normalization: False` が既定の本 project では正常構成を弾いた）/ `E_BINDING_SCALE_DOUBLE` / `E_BINDING_ACTION_UNBOUNDED` / `E_BINDING_LINEAGE_MISMATCH` / `E_BINDING_STAGE_DECLARATION_MISSING` / `E_BINDING_SUPERSEDE_DETAIL_MISSING` / `E_BINDING_IDENTICAL_HASH_PRESENT`（IDENTICAL なのに hash 非 null）/ `E_BINDING_STAGE_IDENTICAL_UNCONFIRMED`（IDENTICAL 主張に対し D1.1-C manifest の両段一致記録が無い）。

**適用位置**: 値/構造/schema/mask/belief/版 = TensorBindingSpec 単体 validator（standalone）。hash 供給 + cross-artifact = certify 段。**供給経路 = frozen `certify_definition` の `proof_artifact_resolver`**（`resolve_artifact(ref, expected_sha256)` が sha 照合を既に提供）を用い、slot hash を expected として spec 実体を解決する。⚠**もし resolver 経由で slot 面に到達できず `certify_definition` の引数追加が必要と判明した場合、それは frozen A の schema delta であり、supersession + Rs review 経由でのみ行う**（「追加検査」として黙って持ち込まない）。本 doc は前者を設計前提とし、後者の可能性を open point（§10）に残す。

## 5. handoff の grasp/contact stability field group（**PROVISIONAL — 必須化は保留**）

RV5 §6(ii)（handoff は arm pose だけでなく grasp/contact stability を encode）への設計入力。**v2 で status を PROVISIONAL に変更**（§12 D-21/D-22・NHA 縮小提案の採用）:

| field_id | dtype | shape | unit | frame | 意味 |
|---|---|---|---|---|---|
| `grasp_engaged_left` / `_right` | BOOL | [1] | dimensionless | none | 各腕の把持係合 |
| `contact_stable_left` / `_right` | BOOL | [1] | dimensionless | none | 接触の時間安定（窓判定） |
| `chain_topology_class` | INT32 | [1] | dimensionless | none | cable chain の離散位相 class（1 mrad 級 pose 差と独立の離散状態） |
| `topology_ledger_hash` | — | — | — | — | **v2 追加**: class 台帳の content hash。同 dtype/shape でも**意味の異なる台帳**を §5D が見抜けない穴を塞ぐ（§12 D-?/CC2） |
| `grasp_span_error` | FLOAT32 | [1] | m | none | 実把持スパンの **RS71 §0#2 の 88 mm 基準**（`RS71-System-Spec-SSOT.md:24` / `task_config.py:21-22,:235`）からの誤差 |
| `stability_confidence` | FLOAT32 | [1] | dimensionless | none | **v2 追加**: 上記 BOOL 群の較正済み確信度 |
| `stability_unknown` | BOOL | [1] | dimensionless | none | **v2 追加**: 判定不能の明示（occlusion 等） |

- **必須化は行わない（v2 変更）**: v1 は「cable を運ぶ handoff schema は本 group を `required_field_ids` に含める」と書いたが、①該当を判定する機械可読述語が無い ②error code が無い ③既存 schema への `required_field_ids` 追加は frozen §5D の `consumer required ⊆ producer fields` を破り major version event（`producer_handoff_schema_hash` の stale 化・BehaviorSignature 影響）を起こす。よって **本 group は「宣言可能な標準 field 群」として提供し、必須化の可否・移行手順は slice 詳細 prereg + Rs 裁定に委ねる**。
- **不確実性 channel（v2 追加）**: `stability_confidence` / `stability_unknown` を置く。理由 = ①RV5 §6(iii) が calibrated uncertainty を要求 ②THREAD には「grasp verdict を数値から PASS 宣言するな・human GT が最終」という standing lesson がある。boolean のみを fail-closed 必須にすると、occlusion 下の producer に「正当化できない bool を出す or handoff を諦める」を強いる＝捏造圧力になる。
- 値の算出法・class 台帳の内容・窓幅・閾値は **契約でなく計測設計**であり slice 詳細 prereg / D2 fixture が確定（本 doc は field 契約と ledger の content-address 化のみ）。

## 6. Golden vectors / invalid corpus（**機械可読 fixture を bank 済**）

**banked fixtures**（`eval_runs/troot_optE_dapg_wholeroute_scope_20260701/wmso_d11b_fixtures/`、生成器 `build_goldens.py` 同梱 — pS/pN は banked file から独立再計算可能。v1 は fixture 未 bank で prereg IN-6 / Exit「機械可読 fixture + golden 同梱」に違反していた・§12 D-4）:

| # | file | 内容 | H_WCJ (sha256) | canonical bytes |
|---|---|---|---|---|
| G-1 | `tensor_binding_golden_1.json` | 最小 RL_ONLY（history/normalizer/mask なし） | `0cc2fc1616b64abd8a4a93b8b0c974f1bb3d2f2880fe12055ec2ec5fd4f9fe06` | 1435 |
| G-2 | `tensor_binding_golden_2.json` | DEMO_PLUS_RL（quat WXYZ + BELIEF ×2 + MEAN_STD + history depth3 STEP_MAJOR + mask PER_STEP + **IDENTICAL（hash = null）**） | `45cfe2c8882c2cd0a6a6180703f16b62212776ba4cc5a0e2309273a9b4fe679d` | 1967 |
| G-3 | `tensor_binding_golden_3.json` | **v2 追加 complement**: dual-arm 14dim action + `action_scale` 非 null + **≥2 要素 frozenset** + EXPLICIT_SUPERSEDE + MIN_MAX + XYZW_UNIT + ZERO_IS_VALID + OLDEST_FIRST/ZERO_PAD/**FEATURE_MAJOR** + ACROSS_STACK mask + 片側 bounds | `e1ed424fdff50546f3175505f50e966dcc057613f16904fc3b9b9a89b44ff172` | 3065 |

- 補助 pin: `producer_schema_hash` = `744866166f80fd99…` / G-3 `demo_dataset_binding_hash` = `498a56fbe182f662…` / `topology_ledger_hash` = `f5bd178074c0175c…`（fixture 用の宣言的導出 — 実在 artifact の hash ではない）。
- **frozenset 判別性の実証（frozen §2 item 8「≥2 要素 frozenset vector」要件の履行・§12 D-14）**: G-3 の `applies_to` を**挿入順**（sorted でない）で直列化すると `7def3ff593e73246…` となり G-3 の値と**異なる** ⇒ 昇順 sort 規則がこの corpus で判別される（v1 は cardinality ≤1 のみで、誤実装が同じ hash を出せた）。
- **再現**: `python3 wmso_d11b_fixtures/build_goldens.py <出力先>` が 3 fixture を再生成し hash を印字する（型 assertion 込み）。⚠v1 が載せた `json.load→json.dumps` one-liner は **WCJ 非忠実**（duplicate key を後勝ちで通し、NaN/Infinity/float 型も通す＝本節 invalid corpus が拒否必須とするもの）ゆえ**撤回**。`build_goldens.py` の `wcj_bytes()` は float/bool/非 ASCII key を拒否する。REPRODUCTION_PROCEDURE proof（§3）は WCJ 実装を用いること。
- **fixture の representativeness（§12 D-31）**: G-1/G-2 は意図的に合成・小規模（型網羅が目的）。G-3 のみ dual-arm 相当幅を持つ。実 demo の action 幅（12dim 系）との一致は主張しない — 実 binding の代表性は D1.1-C の run manifest が担う。
- **invalid corpus（拒否必須・impl で全列挙）**: NaN/"Infinity"/float 型 / "01"・"1.10"（decimal 非正規形）/ offset gap・overlap / length ≠ prod(shape) / total_dim 不一致 / 空 features / field_id 重複・NFC 非正規 / dtype・unit・frame 不一致 / quat on shape≠[..,4] / **bool を offset・length・total_dim・depth に混入** / mask 自己参照・宛先不在・非 BOOL mask / BELIEF binding 欠落・重複 / bounds inverted・両 null / depth 0 / rate "0" / RL_ONLY + bc_stage_binding 非 null / **IDENTICAL + hash 非 null** / EXPLICIT_SUPERSEDE + detail null / 64-hex 違反 / 未知 enum member / 未知 JSON field / duplicate canonical key / 未知 binding_schema_version / action 側の非 SEMANTIC_ACTION source / action feature の bounds 欠落。

## 7. Test plan（impl GO 後 — 設計時宣言）

standalone unit（配布物のみで全実行）: 型 round-trip（encode→decode→encode で同一 bytes）/ **golden G-1/G-2/G-3 一致 + G-3 挿入順 variant が別 hash になること**（判別性の positive control）/ invalid corpus 全拒否 / coverage 算術 property test（ランダム layout → `E_BINDING_COVERAGE_INVALID` 検出）/ **flatten_order・history.layout の判別 test**（同一 field 集合で layout だけ異なる 2 spec が別 hash になること）/ cross-artifact 検査の赤→緑 pair（HASH_MISMATCH・NORMALIZER_MISSING/ORPHAN/VALUE・NORM_COHERENCE・CONTROL_MODE_MISMATCH・LINEAGE_MISMATCH・IDENTICAL_HASH_PRESENT）/ Draft（slot UNKNOWN 混在）で cross-artifact 検査が発火しないこと。

## 8. 未解決点 disposition

1. **U-1（epoch 結合）= B は epoch field を持たない（確定）**: stale-epoch 検査は frozen §7 runtime（`offer.control_epoch == authority_epoch_snapshot` / `E_HANDOFF_EPOCH_STALE`）が担う。binding は静的 artifact ゆえ epoch を持てば同一 layout が epoch 毎に別 hash になり identity churn。
2. **U-2（belief/vision 粒度）= 2 層分担（推奨・C の prereg 判断事項へ降格）**: **schema 水準** = 本 spec が bind（`producer_schema_hash` が identity に参加）。**producer artifact 水準**（encoder weights 等）= D1.1-C run manifest が run 毎に pin。⚠**v1 の「両失敗を塞ぐ」は over-claim ゆえ撤回**（§12 D-27）: manifest は run を**記録**するが、発行済 certificate 下での後続 run における encoder 差替えを**阻止しない**。よって正確には「schema 変更は再 identity を強制する／artifact 差替えは記録で**検出可能**だが契約層では**阻止されない**」。**carry**: 差替え阻止を要するなら D1.1-C が closed-loop eligibility 検査として実装すること（C の prereg に本項を必須入力として渡す）。
3. **U-3（drive-substrate lineage）= B に導入しない（確定・C-2 履行）**: kinematic 全削除 rework（DDR #25/#26）進行中につき rework 前 taxonomy を焼込まない。data の substrate 識別 = D1.1-C `substrate_id`。必要が判明したら schema delta として Rs review 経由。
4. **U-4（HANDOFF source）= v1.0 語彙から除外（v2 確定・§12 D-9）**: `accepted_handoff` は tuple ゆえ producer 複数時に `field_id` が一意に解決しない。frozen は `producer_handoff_schema_hash` で同型の曖昧性を解いており、B が同じ pattern を持たないまま HANDOFF を許すのは穴。**v1.0 では `FeatureSource` から HANDOFF を落とす**（必要になった時点で `handoff_inputs`（`producer_handoff_schema_hash` 保持）+ 被覆/孤児 code を追加する schema delta として導入）。同理由で obs 側の前 action feedthrough も v1.0 非対応。
5. **U-5（既存 demo の移行）= 未解決 blocker として loud 宣言（v2 追加・§12 D-12）**: 現存 demo dataset（`thread_isaac_lab/data/` 系、CC5 実測 198 件）は TensorBindingSpec を持たない。v2 の IDENTICAL=null 化により「hash を捏造して埋める」必要は消えたが、**demo 系 lineage を宣言する skill は D1.1-C の manifest が両段 binding を記録して初めて `E_BINDING_STAGE_IDENTICAL_UNCONFIRMED` を解消できる**。したがって **prereg §4 の slice acceptance 条件 `portfolio_has_IL` は、①D1.1-C 完了 ②kinematic 全削除後の demo 再記録（DDR #25 の「demo 再記録必然化」）の両方に依存する** — 本 doc はこれを解決せず、**slice 側の到達条件として明示 carry** する。

## 9. Reuse gate 記録（AGENTS.md「Reuse / official-specification gate」— v2 追加・§12 D-23）

v1 は本 gate 未実施だった。実施結果（on-disk 実測）:

| 候補 | 実体 | 判定 |
|---|---|---|
| IsaacLab 公式 IO descriptor | `source/isaaclab/isaaclab/envs/utils/io_descriptors.py:27,84`（`Generic{Action,Observation}IODescriptor` = name/shape/dtype/description/full_path/extras）+ `managers/observation_manager.py:234-295 get_IO_descriptors()`（overloads: scale/clip/history_length/flatten_history_dim/modifiers/units）+ `:437-458 serialize()` + export script | **再利用不可（certification 基盤として）**。決定的理由 = `observation_manager.py:271-272` が descriptor 取得を `except Exception as e: print(...)` で握り潰し、**失敗した term を silent に脱落**させる＝**fail-open**。証明対象の集合が黙って縮む機構は evidence の土台にできない。**ただし field 語彙（shape/dtype/unit/scale/clip/history）は本設計の設計入力として参照した** |
| THREAD 既存 BC schema | `thread_isaac_lab/scripts/route_demo_to_bc.py:76,96-105,447-450`（版付き obs/action schema・不一致で `E3 STOP` = fail-closed・schema tag `BC_ROUTE_v{1|2}_{n}phase`・`action_repr` tag） | **同一問題の低形式版**。fail-closed である点は本設計と同方向。**version/tag の考え方を設計入力として採用**。置換対象ではなく、B の binding が上位互換 |
| THREAD obs builder | `thread_isaac_lab/models/obs_builder.py:30` が `task_config` から `FALLBACK/OBS_DIM/OBS_MODES/OBS_NORMALIZATION` を import — **4 symbol とも `task_config.py` に不在（dead code）**。`OBS_DIM` は 6 箇所で 4 値（25/45/62）に分裂 | **再利用不可**。むしろ **producer 面が現に分裂している証拠** |

**carry（owner 不在の gap）**: 上記より、**「TensorBindingSpec の宣言」と「実際に tensor を作る producer コード」を結ぶ責務を現在どの chunk も持っていない**。宣言が自己整合かつ hash 安定でも、実 layout と食い違い得る（CLAUDE.md §運用15 の ABSENT-IN-CODE 類型）。本 doc は §3 の `COMPATIBILITY_TEST` / `REPRODUCTION_PROCEDURE` semantics でこの照合を**要求**するが、**実装 owner の指名は impl 解錠時 or D1.1-C prereg の事項**として carry する。

## 10. Open points

- 本 v2 = **CC Debate cycle-1 の fold**（verdict = FAIL・record `WMSO_D11B_CC_DEBATE_CYCLE1_VERDICT_RSTECHLEAD2_20260720.md`）。cycle-2 の要否 = pS/pN/Rs 裁量（skill max-2-cycles、CC1 は自己起動しない）。
- §4 適用位置の前提（`proof_artifact_resolver` 経由で slot 面に到達できる）が impl で偽と判明した場合 = frozen A の schema delta → supersession + Rs review。**黙って引数追加しない**。
- §5 の必須化可否・class 台帳・判定器・窓幅 = slice 詳細 prereg + Rs 裁定。
- U-2 の producer artifact 阻止・U-5 の demo 移行 = D1.1-C prereg への必須入力。
- 「open = 0」の無条件宣言はしない（frozen §10 と同規律）。

## 11. Module layout（impl GO 時に確定 — 宣言のみ）

`thread_isaac_lab/wmso/contracts_v2/`: `tensor_binding.py`（型 + 単体 validator）+ `certify.py` への cross-artifact 検査追加 + `tests/test_tensor_binding.py` + `tests/fixtures/`（banked fixture を移送）。**本 chunk では書かない**（impl = CLOSED）。既存 `thread_isaac_lab/wmso/d1/` との関係（`is_hex64` / `sha256_bytes` の再利用可否・supersede か併存か）は impl 着手時に明記する。

## 12. 版歴 / fold-map

- **v1**（2026-07-20 09:56、`31d96783c3f5392c…` @ `71e3985aab`）→ **5体 CC Debate cycle-1 = ⛔FAIL**（verdict record `WMSO_D11B_CC_DEBATE_CYCLE1_VERDICT_RSTECHLEAD2_20260720.md`、panel = lens A/B/C/D + NHA、union 集約 31 項）。
- **v2**（2026-07-20 11:10 実測、本版）— fold:
  - **D-1 (CRITICAL)** §3 の EP 不在主張 = FALSE → **全 grade を閉じた query で再導出**（wildcard/`_applicable` 展開）+ SHADOW rank2 が RECONSTRUCTED_COMPATIBLE を受理する事実を明記 + 4 grade 分の subject semantics を追加。
  - **D-2 (CRITICAL)** IDENTICAL の自己 hash 不動点 → **IDENTICAL は hash を持たない**（null 必須）+ 外部確認 code。§0 の反循環規則を「構造 pattern」へ一般化。
  - **D-3 (CRITICAL)** flatten 順序未規定 → `FeatureBinding.flatten_order`（v1.0 = ROW_MAJOR）。
  - **D-4 (CRITICAL)** fixture 未 bank → **G-1/G-2/G-3 + 生成器を bank**（§6）。
  - **D-5..D-13 (HIGH)** hash-identity 検査追加 / history.layout 追加 / NORM_COHERENCE 一方向化 + KNOWN-operand gating / action source code / HANDOFF 除外 / bool 拒否 / 再現 command 撤回 + WCJ 実装 / demo 移行 blocker の loud 宣言 / version 検証 + churn 規律。
  - **D-14..D-31 (MED/LOW)** ≥2 frozenset golden / mask dtype+shape+scope / container_dtype / normalizer 値制約（frozen U13 の履行）/ COVERAGE_INVALID 統合 / 空 features / belief 重複 / §5 PROVISIONAL 化 / §5 不確実性 channel + ledger hash / reuse gate 記録（§9）/ manifest 追加義務の撤回 / CONFIG_HASH 検査可能化 / U-2 over-claim 撤回 / enum 改訂に Rs review / mis-citation 修正（frozen §7c → **§8** / RV5-W-P0-5 → **RV7-P0-3**）/ 88mm の SSOT 引用 / fixture 代表性の非主張。
  - **NHA 縮小要求**: §3 の誤主張撤回・§5 の必須化取り下げ・§8-2 降格を採用。G-2 破棄は不採用（判別に必要ゆえ修正版で再生成）。
  - **/reward-design 該当性 再判定（prereg §7 の条件付き義務・§12 D-24）**: §5 が計測 field を扱うため trigger を認め、再判定を実施 → **現時点も非該当**。理由 = 本 doc は field の**契約**（名前・dtype・単位・frame・ledger の content-address）のみを定め、**success/failure の判定式・閾値・窓幅を一切定めない**（それらは slice 詳細 prereg へ明示委譲）。⚠ただし **slice prereg が判定式・閾値を定める段では `/reward-design` + `/pre-check` が発火する**（直交ゲート・L と独立）— slice prereg の必須入力として carry。
- **v1 → v2 の非変更点**: 統治・carries・frozen 不変・impl CLOSED・§0 の WCJ 継承方針（B-declared 分を分離明記した点のみ変更）。
