# WMSO D1.1-B `tensor_binding` — DESIGN (v6)

- node: `T-WMSO`; author = w2:pQ (RS-TECH-LEAD2); v1 = 2026-07-20 09:56 JST（実測）; **v2 = 2026-07-20 **11:08–11:13 JST**（実測 bracket: 著述開始前 11:08:16 / bank 時 11:13:35。⚠records-fix: 初稿は「11:10」と実測せずに記載した date-THEN-write 違反 — 実測 bracket に置換）— CC Debate cycle-1 FAIL の fold）; v3 = 2026-07-20 11:43 JST（実測 — pN exact-pin HOLD B1-B5 の fold）; v4 = 2026-07-20 12:10 JST（実測 — cycle-2 debate の fold）; v5 = 2026-07-20 12:40 JST（実測 — pN exact-pin HOLD R1-R3 の fold）; **v6 = 2026-07-20 13:06 JST（実測 — pS v5 PASS 後に著者が自検出した検証計器の欠陥 1 件の fold。版歴 = §12）**
- 統治: **scope prereg v1.1.1**（`ffd06623e22f…` @ `cf94601f7a`・pN SCOPE CONCUR `0a5d0969218c…` @ `ccd8342c30`）§2 IN の実装設計。**土台 = frozen D1.1-A v2.11.2**（DESIGN `00192d20ca00b654…` / EP v1.9 md `c474acea7c58…` / JSON `e63176af9bc3…`）— **frozen 3 file を編集せず・schema delta を導入しない**（必要時は supersession + Rs review、prereg §1.3）。
- **binding carries 遵守**: pS **C-1**（frozen enum に member を追加しない。§1.1 は B 新 schema の内部語彙）/ pS **C-2**（drive-substrate taxonomy を焼込まない — §1.6 TimingSpec は SI 量のみ・§8-3）/ prereg §6（DC-1..6・RV5 §6 (i)-(iv)・pN (3)・kinematic 写像・L0 手段裁定）。
- gate 位置: §5 chain の **design**。経緯 = cycle-1 debate FAIL → v2 → pS PASS → **pN exact-pin HOLD B1-B5** → v3 → **cycle-2 debate 実施済（max-2-cycles 到達）** → v4 → pS 再 PASS → **pN exact-pin HOLD R1-R3** → v5 → pS 再 PASS（12:51） → **著者自検出の fold** → 本 v6。次 = **pS delta 再 verify → pN exact-pin 再判定 → ⛔Rs の B1 裁定（A/A′/B）→ freeze**。**impl/training/authority = CLOSED 継続**。
- **Rs 優先順位裁定（2026-07-20 13:04:29 JST 受領・記録のみ）**: **WMSO = 最上位概念 / top L0 integration architecture**。従属作業は WMSO への寄与で順序づける。**RL / IL / Vision / World Model は必須かつ conjoined**（[[project-l0-means-rl-il-vision-worldmodel-mandatory-2026-07-16]] を再確認）、**per-skill 実装は algorithm-agnostic**（BC+RL / 妥当なら RL-only 等）。task (d) / substrate cleanup / demo 再生成 / safety = **WMSO-enabling な前提・carry** であり競合する top-level goal ではない。⚠**本裁定は physics-realism / safety / evidence / two-key / Rs の run・launch gate を一切迂回しない**。custody は本優先順位を記録するのみで **implementation / training / closed-loop authority を主張しない**。⇒ 本 doc の gate chain・CLOSED 境界は不変（裁定が明示的に非迂回を述べている）。
- **banked fixtures（本 doc と同 commit 系列）**: `wmso_d11b_fixtures/tensor_binding_golden_{1,2,3,4}.json` + `build_goldens.py`（生成器 兼 **`--verify` 非破壊検証器**）。§6 に sha 記載 — pS/pN は banked file から独立再計算可能。

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
# scheme 別 stats payload 契約（v3 追加・§12 B-3）: stats_key の指す entry は scheme により型が決まる
#   MEAN_STD → {"mean": CanonicalDecimal[], "std": CanonicalDecimal[]}   （要素数 = 対象 feature の length）
#   MIN_MAX  → {"min":  CanonicalDecimal[], "max": CanonicalDecimal[]}   （同上）
# 述語: 要素数 == 対象 feature の length（index は当該 feature の flatten_order 順）/ MEAN_STD は std > 0
#       / MIN_MAX は min < max。⚠isfinite は payload が CanonicalDecimal である限り **frozen §2 item 5 の
#       正規形が構造的に保証**する（NaN/Inf は表現不能）ため独立述語としては vacuous — v4 で「構造的に discharge」
#       と明記し、四択のうち 1 つを「常に真」として数えない（cycle-2 CC4-C8）。
#       ⚠`std > 0` は frozen §5 U13 の `std ≥ 0` に対する **B 側の強化**（0 除算回避）であり「履行」ではない
#       — v4 で B-declared strengthening として明示（cycle-2 CC2-CH7/CC4-C11）。
#       ⚠`stats_key` の一意性規則は未定（共有可なら要素数述語が矛盾し得る）→ §10 open。
# 適用順序（v4 追加・cycle-2 CC4-C3）: raw → normalizer → transform → bounds（表明）→ container cast。
#       MEAN_STD = (x - mean)/std / MIN_MAX = (x - min)/(max - min)。順序も式も hash-visible な意味の一部。
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
    container_dtype: Dtype                  # **v2 追加**: flat vector の格納 dtype（§12 D-16）。semantic dtype との変換は §1.4b conversion table が規定（v3）
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

### 1.4b container cast 規約（v1.0 conversion table — v3 追加・§12 B-4）

`container_dtype` と feature の semantic `dtype` が異なる場合、**下表の組だけが合法**（表外 = `E_BINDING_CAST_FORBIDDEN`）。「cast が起きる」だけを書いて許容変換・可逆条件・拒否 code を欠いた v2 は、§0 の全単射主張を満たしていなかった。

| semantic dtype | container FLOAT32 | container INT32 | container BOOL |
|---|---|---|---|
| FLOAT32 | 恒等 | ⛔ | ⛔ |
| INT32 | ⛔**禁止（v5）** | 恒等 | ⛔ |
| BOOL | **可（canonical: false→`0`, true→`1`。読み出しは `v ≠ 0` を true とする）** | ⛔ | 恒等 |

- v1.0 では **混在 vector の container_dtype は FLOAT32 のみ**を実用形として想定するが、単一 dtype 構成では INT32/BOOL container も上表の恒等行で合法。
- cast は **feature 単位で一様**（同一 feature 内で要素毎に異なる cast をしない）。
- ⛔**INT32 → FLOAT32 は v1.0 で禁止（v5・pN R1 = CRITICAL）**: float32 の仮数は 24 bit ゆえ **16777216 と 16777217 が同一の `16777216.0` に衝突**（本 session 実測）— cast が単射でなく、§0 の全単射宣言が破れる。v4 は `E_BINDING_CAST_LOSSY` を削除（到達不能ゆえ正当）した上で**可逆性を §3 `COMPATIBILITY_TEST` に委譲**したが、frozen EP 実測では当該 proof が必須なのは **RECONSTRUCTED_COMPATIBLE（rank 2）のみ**で、**CLOSED_LOOP が要求する rank 3/4 では当該 proof 無しに通る** ⇒ 委譲先が肝心の grade を覆っていなかった（「到達不能 code の削除」は正しかったが「委譲先の到達性」を検証しなかった私の誤り）。**最小かつ fail-closed な閉じ方 = v1.0 では当該 cast を認めない**（`E_BINDING_CAST_FORBIDDEN`）。INT32 feature は INT32 container（恒等行）で表現する。将来 FLOAT32 container に INT32 を載せる必要が生じたら、**hash-visible な domain 制約 + 全 grade に効く obligation** を伴う schema delta として Rs review 経由で開ける。
- **BOOL feature には数値段を付けない（v4 追加・cycle-2 CC4-C1/CC2-CH5 = 安全関連）**: `dtype = BOOL` の feature に `normalizer` / `transform` / `bounds` を付すと、BOOL→FLOAT32 の読み出し規約（`v ≠ 0`）の下で **false/true が共に非零に写り mask が無効化される**（実証: mask 対象の validity field に MEAN_STD を付けると false→-1 / true→+1 で両方 valid）。§4 `E_BINDING_NUMERIC_STAGE_ON_BOOL` で禁止。

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
3. **B 完了前**: TensorBindingSpec artifact が存在しないため、KNOWN hash を**正当に**供給できない。⚠**v1 はこれを「構造的」と称したが、正しくは「§4 の hash-identity 検査が走って初めて構造になる」**（§12 D-5）。⛔**v4 追記（cycle-2 CC2-CH2）**: その供給経路は v3 §4 で**撤回**されたため、**DC-1 の「構造性」は §10 の B-1 解決に BLOCKED**。v2 の「供給経路を §4 で指名する」という結び句は失効。

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
**値/構造**: `E_BINDING_LENGTH_SHAPE_MISMATCH` / `E_BINDING_COVERAGE_INVALID`（offset 連鎖が `[0, total_dim)` を丁度被覆しない。⚠v1 の GAP/OVERLAP 2 code は算法上 overlap が表現不能で到達不能だったため **1 code に統合**・§12 D-18）/ `E_BINDING_EMPTY_FEATURES`（obs/action とも非空必須）/ `E_BINDING_DUPLICATE_FIELD` / `E_BINDING_INT_TYPE`（`offset`/`length`/`total_dim`/`depth` に `type(x) is int` — bool 拒否）/ `E_BINDING_NONFINITE`（CanonicalDecimal 正規形違反 — scale・bias・bounds・rate・staleness 全数）/ `E_BINDING_BOUNDS_EMPTY`・`E_BINDING_BOUNDS_INVERTED` / `E_BINDING_TIMING_NONPOSITIVE`（rate ≤ 0・staleness < 0）/ `E_BINDING_HISTORY_INVALID`（depth < 1）/ `E_BINDING_QUAT_ON_NONQUAT` / `E_BINDING_CONTAINER_DTYPE_MISSING` / `E_BINDING_CAST_FORBIDDEN`（§1.4b 表外）/ **`E_BINDING_NUMERIC_STAGE_ON_BOOL`**（BOOL feature に normalizer/transform/bounds — §1.4b）。
**source 制約（v2 追加・§12 D-8）**: `E_BINDING_SOURCE_FORBIDDEN`（action 側に `source ≠ SEMANTIC_ACTION` / obs 側に `SEMANTIC_ACTION`〔前 action feedthrough は v1.0 では非対応・§8-4〕）。
**schema 照合**: `E_BINDING_FIELD_UNKNOWN` / `E_BINDING_DTYPE_MISMATCH` / `E_BINDING_SHAPE_MISMATCH` / `E_BINDING_UNIT_MISMATCH` / `E_BINDING_FRAME_MISMATCH`。
**mask（v2 強化・§12 D-15）**: `E_BINDING_MASK_TARGET_ABSENT` / `E_BINDING_MASK_SELF` / `E_BINDING_MASK_FIELD_ABSENT` / `E_BINDING_MASK_DTYPE`（mask_field_id の dtype ≠ BOOL）/ `E_BINDING_MASK_SHAPE`（mask の要素数が対象と非整合 — 1 要素の全体 gate か同 shape の要素毎かを scope と併せ判定）。
**belief**: `E_BINDING_BELIEF_UNBOUND` / `E_BINDING_BELIEF_ORPHAN` / `E_BINDING_BELIEF_DUPLICATE`（同一 `belief_field_id` の重複 entry・§12 D-20）/ `E_BINDING_HASH_MALFORMED`（producer_schema_hash）。
**cross-artifact（certify 時・全 operand slot が KNOWN の時のみ発火** — §12 D-7）: `E_BINDING_CONTROL_MODE_MISMATCH` / `E_BINDING_NORMALIZER_MISSING`（stats_key 不在）/ `E_BINDING_NORMALIZER_ORPHAN` / `E_BINDING_NORMALIZER_VALUE`（**v3 で scheme 別に完全化**: payload が §1.2 の scheme 別契約に適合し〔MEAN_STD = mean/std・MIN_MAX = min/max〕、全要素 isfinite、要素数 == 対象 length、**MEAN_STD は std > 0・MIN_MAX は min < max** — frozen §5 U13 の委譲義務の履行。v2 は MEAN_STD 系しか述語を持たず MIN_MAX が無検査だった・§12 B-3）/ `E_BINDING_NORM_COHERENCE`（**v2 で一方向化**: `bundle.normalization = EXPLICIT_NONE ⇒ 全 normalizer null`。**逆方向は課さない** — v1 の双条件は frozen §1.2† の evidence-gated EXPLICIT_NONE と deadlock し、`empirical_normalization: False` が既定の本 project では正常構成を弾いた）/ `E_BINDING_SCALE_DOUBLE` / `E_BINDING_ACTION_UNBOUNDED` / `E_BINDING_LINEAGE_MISMATCH` / `E_BINDING_STAGE_DECLARATION_MISSING` / `E_BINDING_SUPERSEDE_DETAIL_MISSING` / `E_BINDING_IDENTICAL_HASH_PRESENT`（IDENTICAL なのに hash 非 null）/ `E_BINDING_STAGE_IDENTICAL_UNCONFIRMED`（IDENTICAL 主張に対し D1.1-C manifest の両段一致記録が無い）。

**適用位置**: 値/構造/schema/mask/belief/版/cast = TensorBindingSpec 単体 validator（standalone）。hash 供給 + cross-artifact = certify 段。

⛔**供給 locator = 未解決（v3 で over-claim 撤回・§12 B-1）**。v2 は「frozen `resolve_artifact(ref, expected_sha256)` を用い slot hash を expected として解決する」と書き、pS もこれを「frozen delta 非要」と判定したが、**両者とも resolver 関数の実在を確認しただけで locator の実在を示していなかった**。実測: frozen `ArtifactSlot = {state, artifact_hash}`（`WMSO_D11A_CONTRACTS_V2_DESIGN…:47` 相当行）に **ref field は無い**。`ProofItem.ref` は evidence 側の参照であり、**TensorBindingSpec 実体の ref は全 grade の proof set に共通必須ではない**。よって `resolve_artifact` に渡す `ref` の出所が設計上未定義であり、**「frozen delta 非要」は NO-PROOF**。

**grade 別 locator 実測（cycle-2 で closed-query 測定・Rs 裁定の前提事実）**: proof item の `artifact_hash == claim_target_hash` を束縛する ProofKind は `FINAL_ARTIFACT_HASH` / `REPRODUCED_OUTPUT_HASH` の 2 種のみ（EP JSON `proof_binding`）。TENSOR_BINDING の grade 別 proof set と突き合わせると:

| grade (rank) | 束縛 ProofItem | locator |
|---|---|---|
| EXACT_TRAIN_TIME (4) | なし | **無** |
| HASH_BOUND_REPRODUCED (3) | FINAL_ARTIFACT_HASH / REPRODUCED_OUTPUT_HASH | **有（in-band・delta 不要）** |
| RECONSTRUCTED_COMPATIBLE (2) | なし | **無** |
| DIMENSION_ONLY (1) | なし | **無** |

⇒ **locator は 4 grade 中 1 つ（rank 3）にしか存在せず、最初の slice が動作する SHADOW（rank 2・§3）には無い**。rank 4 が rank 3 より弱いという逆転もここで顕在化する。

- **選択肢 A（frozen delta なし）**: `ref` を **artifact_hash から導出する canonical ref 規約**（例 `wmso-artifact:sha256:<64hex>`）として固定する。⚠ただし上表より rank 1/2/4 には ref を載せる ProofItem 自体が無いため、A は「evidence bundle に無い locator を validator が合成し、全 deployment の resolver が sha256-keyed content-addressed store であること」を要求する — frozen `trust_boundary` は locator と完全性検査を分離しており、この要求は契約解釈でなく**契約意味論の変更**に当たる。⚠さらに A の下では `resolve_artifact` が hash を key に引く content-addressed 参照になるため、**`E_BINDING_HASH_MISMATCH` は store 整合性検査に縮退し、「bundle が別の binding を宣言している」という本来の失敗モードを検出しなくなる**（Rs 裁定時に必要な帰結）。
- **選択肢 A′（frozen delta なし・cycle-2 NHA 提案）**: frozen `EvidenceRecord.source_ref: str` は**全 grade の全 evidence record に既存**であり、`claim_target_hash` は policy 規則により tensor_binding slot hash。`(source_ref, claim_target_hash)` は `resolve_artifact` の signature そのもの。`source_ref` の意味論は frozen package で未規定ゆえ、TENSOR_BINDING record についてこれを束縛することは prereg §2 IN-4（proof obligation の結合）の範囲内と解し得る。**A より小さく、rank 依存もない** — ただし Rs 承認の要否自体は Rs 判断。
- **選択肢 B（frozen delta あり）**: `certify_definition` に binding 実体（または locator）を渡す引数追加 = **frozen A の schema delta** ⇒ supersession 記録 + Rs review 経由。
- **本 doc の立場**: A / A′ / B のいずれも **CC1 が単独で確定できない**（Rs 裁定事項）。よって §10 の open point として **3 択の完全な選択肢集合 + 上表の実測**を添えて上程し、**確定するまで §4 の hash 供給レグは「設計未完」と明示する**。⚠**「述語は確定・経路のみ未確定」という v3 の切り分けは v4 で限定する**: `E_BINDING_ARTIFACT_UNRESOLVED` は経路非依存だが、**`E_BINDING_HASH_MISMATCH` は選択肢 A の下で store 整合性検査に縮退する**（上記）ため、述語の**意味**が経路に依存する。
- **同型の未解決が `bundle.normalization` にもある（v4・cycle-2 CC4-C4）**: §4 の `E_BINDING_NORMALIZER_VALUE` は normalization artifact の payload を読む必要があるが、その slot も frozen `ArtifactSlot = {state, artifact_hash}` で **ref を持たない**。B1 と同一の locator 問題であり、本 open point の対象に **`normalization` slot も含める**。

## 5. handoff の grasp/contact stability field group（**PROVISIONAL — 必須化は保留**）

RV5 §6(ii)（handoff は arm pose だけでなく grasp/contact stability を encode）への設計入力。**v2 で status を PROVISIONAL に変更**（§12 D-21/D-22・NHA 縮小提案の採用）:

| field_id | dtype | shape | unit | frame | 意味 |
|---|---|---|---|---|---|
| `grasp_engaged_left` / `_right` | BOOL | [1] | dimensionless | none | 各腕の把持係合 |
| `contact_stable_left` / `_right` | BOOL | [1] | dimensionless | none | 接触の時間安定（窓判定） |
| `chain_topology_class` | INT32 | [1] | dimensionless | none | cable chain の離散位相 class（1 mrad 級 pose 差と独立の離散状態） |
| `grasp_span_error` | FLOAT32 | [1] | m | none | 実把持スパンの **RS71 §0#2 の 88 mm 基準**（`RS71-System-Spec-SSOT.md:24` / `task_config.py:21-22,:235`）からの誤差 |
| `stability_confidence` | FLOAT32 | [1] | dimensionless | none | **v2 追加**: 上記 BOOL 群の較正済み確信度 |
| `stability_unknown` | BOOL | [1] | dimensionless | none | **v2 追加**: 判定不能の明示（occlusion 等） |

- **必須化は行わない（v2 変更）**: v1 は「cable を運ぶ handoff schema は本 group を `required_field_ids` に含める」と書いたが、①該当を判定する機械可読述語が無い ②error code が無い ③既存 schema への `required_field_ids` 追加は frozen §5D の `consumer required ⊆ producer fields` を破り major version event（`producer_handoff_schema_hash` の stale 化・BehaviorSignature 影響）を起こす。よって **本 group は「宣言可能な標準 field 群」として提供し、必須化の可否・移行手順は slice 詳細 prereg + Rs 裁定に委ねる**。
- **不確実性 channel（v2 追加）**: `stability_confidence` / `stability_unknown` を置く。理由 = ①RV5 §6(iii) が calibrated uncertainty を要求 ②THREAD には「grasp verdict を数値から PASS 宣言するな・human GT が最終」という standing lesson がある。boolean のみを fail-closed 必須にすると、occlusion 下の producer に「正当化できない bool を出す or handoff を諦める」を強いる＝捏造圧力になる。
- ⛔**`topology_ledger_hash` は本表から削除（v3・§12 B-5）**: v2 は dtype/shape/unit/frame を「—」として表に載せたが、frozen `HandoffSchemaSpec.fields = tuple[SemanticFieldSpec, ...]` であり `SemanticFieldSpec = {field_id, dtype, shape, unit, frame}` ゆえ **4 属性を欠く entry は格納不能**、かつ frozen に metadata slot は無い。**`chain_topology_class` の台帳同一性の束縛は D1.1-C の run manifest 側 metadata として carry**（§8-6）。⚠**この carry は §5D の穴を閉じない（v4 訂正・cycle-2 CC5-CH1）**: §5D が評価されるのは registry 静的照合（frozen §5 certify）と runtime `validate_handoff` の 2 箇所のみで、**どちらも run manifest を入力に取らない**。よって carry は台帳差を**検出可能**にするだけで**阻止しない**（§8-2 の U-2 で自ら述べた detect-vs-prevent の区別を、v3 は U-6 に持ち越し損ねた）。**契約層で閉じる路は schema delta（Rs review）のみ**。**したがって `chain_topology_class` は carry 解決後も「同 dtype/shape で意味の異なる台帳」を §5D が見抜けない穴を持ち続ける** — 本 group が PROVISIONAL である理由の一つとして loud に記録する。
- 値の算出法・class 台帳の内容・窓幅・閾値は **契約でなく計測設計**であり slice 詳細 prereg / D2 fixture が確定（本 doc は field 契約のみ）。

## 6. Golden vectors / invalid corpus（**機械可読 fixture を bank 済**）

**banked fixtures**（`eval_runs/troot_optE_dapg_wholeroute_scope_20260701/wmso_d11b_fixtures/`、生成器 `build_goldens.py` 同梱 — pS/pN は banked file から独立再計算可能。v1 は fixture 未 bank で prereg IN-6 / Exit「機械可読 fixture + golden 同梱」に違反していた・§12 D-4）:

| # | file | 内容 | H_WCJ (sha256) | canonical bytes |
|---|---|---|---|---|
| G-1 | `tensor_binding_golden_1.json` | 最小 RL_ONLY（history/normalizer/mask なし） | `af90712a293ee33d15ada71e1cf1baa7964d284af56ac45b4d50209ef12186b2` | 1491 |
| G-2 | `tensor_binding_golden_2.json` | DEMO_PLUS_RL（quat WXYZ + BELIEF ×2 + MEAN_STD + history depth3 STEP_MAJOR + mask PER_STEP + **IDENTICAL（hash = null）**） | `991651b9d6374f423c4fcc3e0bbbe1b3d90be5fca932004cbf3870d7c9d28a23` | 2028 |
| G-3 | `tensor_binding_golden_3.json` | **v2 追加 complement**: dual-arm 14dim action + `action_scale` 非 null + **≥2 要素 frozenset** + EXPLICIT_SUPERSEDE + MIN_MAX + XYZW_UNIT + ZERO_IS_VALID + OLDEST_FIRST/ZERO_PAD/**FEATURE_MAJOR** + ACROSS_STACK mask + 片側 bounds | `dd14f6b68949d0f0c11f4e5002013b43ed12a02da662f4c5f7270cbbf54842d3` | 3121 |
| G-4 | `tensor_binding_golden_4.json` | **v4 追加**: **INT32 semantic dtype + INT32 container + BOOL container**（v3 は cast table 5 legal cell 中 2 つしか使わず `container_dtype` も 1 値のみ ⇒ 当該 field を無視する実装が全 golden を再現できた — cycle-2 CC3-CH2/CC4-C10/CC5-CH3） | `59bbfbba987d8703816f82c18b576d133d32424121a29c0a365d8207ba8274a4` | 1331 |

- 補助 pin: `producer_schema_hash` = `744866166f80fd99…` / G-3 `demo_dataset_binding_hash` = `498a56fbe182f662…`（fixture 用の宣言的導出 — 実在 artifact の hash ではない）。⚠**`topology_ledger_hash` の pin は v4 で削除**（B5 で field を削除した後も §6 と builder に残り、どの fixture も束縛しない dead pin だった — cycle-2 で 4/5 が指摘）。
- **frozenset 判別性の実証（frozen §2 item 8「≥2 要素 frozenset vector」要件の履行・§12 D-14）**: G-3 の `applies_to` を**挿入順**（sorted でない）で直列化すると `838cf7292592258b…` となり G-3 の値と**異なる** ⇒ 昇順 sort 規則がこの corpus で判別される（v1 は cardinality ≤1 のみで、誤実装が同じ hash を出せた）。
- **再現**: `python3 wmso_d11b_fixtures/build_goldens.py <出力先>` が 4 fixture を再生成、`--verify <dir>` が banked bytes を非破壊で検査する。**v4 で builder を全面強化**: ①**全 14 型**に対する member 集合の双方向対称差（v3 は 5 型のみ ⇒ `HistorySpec.layout` / `MaskBinding.scope` / `ActionTimingSpec.hold` の削除が無検出だった＝B2 の欠陥そのものの再現）②enum allowlist + 既知 version ③cast table + BOOL 数値段 guard ④mask・belief の被覆/重複 ⑤**negative control 24 本**（各 assertion が実際に赤になることを実証 — 発火しなければ builder 自体が失敗する）⑥**`--verify <dir>` mode**（banked bytes を読んで検査するのみ・書き込まない）⑦**v5 追加（pN R3）**: **CanonicalDecimal（frozen §2 item 5 の正規表現そのもの）/ NFC identifier / 64-hex** の実検査 + 対応 negative control。⚠v4 の builder は `"Infinity"` を CanonicalDecimal 位置に置いても `--verify` が rc=0 で通っており（pN 実証・本 session 再現）、§6 の WCJ / invalid-corpus に関する主張が**実測を超えていた**。⚠v3 の builder は出力先省略時に **banked file を上書き**するため、改竄を検出せず修復してしまった（検証が自らの baseline を破壊する類型 — cycle-2 CC3-CH6）。**「再現する hash は schema 適合を証明しない」「PASS する assertion 群はそれが検査する範囲しか証明しない」に加え、v5 では検査範囲を明示する**:
- **builder が実検査するもの**: 全 14 型の member 集合（双方向）/ enum allowlist / 既知 version / CanonicalDecimal・NFC・64-hex / cast table / BOOL 数値段 / mask（dtype・自己参照・宛先・昇順）/ belief（被覆・重複）/ coverage 算術 / bool-as-int / lineage・stage / canonical bytes 一致。
- ⚠**v6 訂正（著者自検出・pS の v5 PASS 後）**: 上記 ⑤ の negative control は **v5 まで生成 mode でしか走らず、`--verify` では 1 本も走らなかった**。⑥ は「非破壊」を、⑤ は「毎回実証」を各々正しく述べていたが、**両者を並記したことで「検証者が使う非破壊経路が guard 発火まで実証する」と読める状態**になっていた（pN R3 と同型 = evidence 主張が、それを届ける経路より広い）。⇒ **v6 で negative control を両経路で実行**（in-memory deepcopy のみを変異させるため `--verify` の非破壊性は不変）。**検証者は 1 コマンドで「4 fixture 適合 + 24/24 発火」を非破壊に得る**。実測（v6・本 pin）: `--verify .` → 4/4 conformance PASS + `negative controls: 24/24 fired` + rc=0、事後 sha256 4 本不変。改竄 positive control: G-1 の `policy_rate_hz` に `"Infinity"` を注入 → `not a CanonicalDecimal: 'Infinity'` で **rc=1**（復元後 sha256 一致）。
- ⛔**builder が検査しないもの（= frozen WCJ 完全 validator ではない）**: 非 ASCII key の UTF-16 code-unit 順 / lone surrogate / duplicate key（Python dict では表現不能）/ JCS escape の全域。**これらの検査は impl の `canonicalize()` leg が担う**（本 doc は fixture subset の member/hash 検査であることを宣言し、WCJ 完全性は別 leg として事前登録する — pN R3）。。⚠v1 が載せた `json.load→json.dumps` one-liner は **WCJ 非忠実**（duplicate key を後勝ちで通し、NaN/Infinity/float 型も通す＝本節 invalid corpus が拒否必須とするもの）ゆえ**撤回**。`build_goldens.py` の `wcj_bytes()` は float/bool/非 ASCII key を拒否する。REPRODUCTION_PROCEDURE proof（§3）は WCJ 実装を用いること。
- **fixture の representativeness（§12 D-31）**: G-1/G-2/G-4 は意図的に合成・小規模（型網羅が目的）。G-3 のみ dual-arm 相当幅を持つ。実 demo の action 幅（12dim 系）との一致は主張しない — 実 binding の代表性は D1.1-C の run manifest が担う。
- **invalid corpus（拒否必須・impl で全列挙）**: NaN/"Infinity"/float 型 / "01"・"1.10"（decimal 非正規形）/ offset gap・overlap / length ≠ prod(shape) / total_dim 不一致 / 空 features / field_id 重複・NFC 非正規 / dtype・unit・frame 不一致 / quat on shape≠[..,4] / **bool を offset・length・total_dim・depth に混入** / mask 自己参照・宛先不在・非 BOOL mask / BELIEF binding 欠落・重複 / bounds inverted・両 null / depth 0 / rate "0" / RL_ONLY + bc_stage_binding 非 null / **IDENTICAL + hash 非 null** / EXPLICIT_SUPERSEDE + detail null / 64-hex 違反 / 未知 enum member / 未知 JSON field / duplicate canonical key / 未知 binding_schema_version / action 側の非 SEMANTIC_ACTION source / action feature の bounds 欠落 / **container_dtype 欠落** / **表外 cast（FLOAT32→INT32 等）**  / **MIN_MAX で min ≥ max・要素数不一致・非 isfinite**。

## 7. Test plan（impl GO 後 — 設計時宣言）

standalone unit（配布物のみで全実行）: 型 round-trip（encode→decode→encode で同一 bytes）/ **golden G-1/G-2/G-3 一致 + G-3 挿入順 variant が別 hash になること**（判別性の positive control）/ invalid corpus 全拒否 / coverage 算術 property test（ランダム layout → `E_BINDING_COVERAGE_INVALID` 検出）/ **G-4 を含む 4 fixture の一致 test**（v4 は §7 が G-4 を落としていた — pN R2）/ **flatten_order・history.layout の判別 test**（同一 field 集合で layout だけ異なる 2 spec が別 hash になること）/ cross-artifact 検査の赤→緑 pair（**HASH_MISMATCH は §10 B-1 の解決に条件付き** — 経路未確定のため現時点では設計上不成立・NORMALIZER_MISSING/ORPHAN/VALUE・NORM_COHERENCE・CONTROL_MODE_MISMATCH・LINEAGE_MISMATCH・IDENTICAL_HASH_PRESENT）/ Draft（slot UNKNOWN 混在）で cross-artifact 検査が発火しないこと。

## 8. 未解決点 disposition

1. **U-1（epoch 結合）= B は epoch field を持たない（確定）**: stale-epoch 検査は frozen §7 runtime（`offer.control_epoch == authority_epoch_snapshot` / `E_HANDOFF_EPOCH_STALE`）が担う。binding は静的 artifact ゆえ epoch を持てば同一 layout が epoch 毎に別 hash になり identity churn。
2. **U-2（belief/vision 粒度）= 2 層分担（推奨・C の prereg 判断事項へ降格）**: **schema 水準** = 本 spec が bind（`producer_schema_hash` が identity に参加）。**producer artifact 水準**（encoder weights 等）= D1.1-C run manifest が run 毎に pin。⚠**v1 の「両失敗を塞ぐ」は over-claim ゆえ撤回**（§12 D-27）: manifest は run を**記録**するが、発行済 certificate 下での後続 run における encoder 差替えを**阻止しない**。よって正確には「schema 変更は再 identity を強制する／artifact 差替えは記録で**検出可能**だが契約層では**阻止されない**」。**carry**: 差替え阻止を要するなら D1.1-C が closed-loop eligibility 検査として実装すること（C の prereg に本項を必須入力として渡す）。
3. **U-3（drive-substrate lineage）= B に導入しない（確定・C-2 履行）**: kinematic 全削除 rework（DDR #25/#26）進行中につき rework 前 taxonomy を焼込まない。data の substrate 識別 = D1.1-C `substrate_id`。必要が判明したら schema delta として Rs review 経由。
4. **U-4（HANDOFF source）= v1.0 語彙から除外（v2 確定・§12 D-9）**: `accepted_handoff` は tuple ゆえ producer 複数時に `field_id` が一意に解決しない。frozen は `producer_handoff_schema_hash` で同型の曖昧性を解いており、B が同じ pattern を持たないまま HANDOFF を許すのは穴。**v1.0 では `FeatureSource` から HANDOFF を落とす**（必要になった時点で `handoff_inputs`（`producer_handoff_schema_hash` 保持）+ 被覆/孤児 code を追加する schema delta として導入）。同理由で obs 側の前 action feedthrough も v1.0 非対応。
5. **U-5（既存 demo の移行）= 未解決 blocker として loud 宣言（v2 追加・§12 D-12）**: 現存 demo dataset（`thread_isaac_lab/data/` 系、CC5 実測 198 件）は TensorBindingSpec を持たない。v2 の IDENTICAL=null 化により「hash を捏造して埋める」必要は消えたが、**demo 系 lineage を宣言する skill は D1.1-C の manifest が両段 binding を記録して初めて `E_BINDING_STAGE_IDENTICAL_UNCONFIRMED` を解消できる**。したがって **prereg §4 の slice acceptance 条件 `portfolio_has_IL` は、①D1.1-C 完了 ②kinematic 全削除後の demo 再記録（DDR #25 の「demo 再記録必然化」）の両方に依存する** — 本 doc はこれを解決せず、**slice 側の到達条件として明示 carry** する。

6. **U-6（topology ledger 束縛）= D1.1-C metadata carry（v3・§12 B-5）**: `chain_topology_class` の台帳同一性は frozen `SemanticFieldSpec` に格納できない（4 属性必須）。D1.1-C run manifest の metadata として記録することを C prereg の必須入力に carry。契約層束縛が要るなら schema delta → Rs review。

## 9. Reuse gate 記録（AGENTS.md「Reuse / official-specification gate」— v2 追加・§12 D-23）

v1 は本 gate 未実施だった。実施結果（on-disk 実測）:

| 候補 | 実体 | 判定 |
|---|---|---|
| IsaacLab 公式 IO descriptor | `source/isaaclab/isaaclab/envs/utils/io_descriptors.py:27,84`（`Generic{Action,Observation}IODescriptor` = name/shape/dtype/description/full_path/extras）+ `managers/observation_manager.py:234-295 get_IO_descriptors()`（overloads: scale/clip/history_length/flatten_history_dim/modifiers/units）+ `:437-458 serialize()` + export script | **再利用不可（certification 基盤として）**。決定的理由 = `observation_manager.py:271-272` が descriptor 取得を `except Exception as e: print(...)` で握り潰し、**失敗した term を silent に脱落**させる＝**fail-open**。証明対象の集合が黙って縮む機構は evidence の土台にできない。**ただし field 語彙（shape/dtype/unit/scale/clip/history）は本設計の設計入力として参照した** |
| THREAD 既存 BC schema | `thread_isaac_lab/scripts/route_demo_to_bc.py:76,96-105,447-450`（版付き obs/action schema・不一致で `E3 STOP` = fail-closed・schema tag `BC_ROUTE_v{1|2}_{n}phase`・`action_repr` tag） | **同一問題の低形式版**。fail-closed である点は本設計と同方向。**version/tag の考え方を設計入力として採用**。置換対象ではなく、B の binding が上位互換 |
| THREAD obs builder | `thread_isaac_lab/models/obs_builder.py:30` が `task_config` から `FALLBACK/OBS_DIM/OBS_MODES/OBS_NORMALIZATION` を import — **4 symbol とも `task_config.py` に不在（dead code）**。`OBS_DIM` は 6 箇所で 4 値（25/45/62）に分裂 | **再利用不可**。むしろ **producer 面が現に分裂している証拠** |

**carry（owner 不在の gap）**: 上記より、**「TensorBindingSpec の宣言」と「実際に tensor を作る producer コード」を結ぶ責務を現在どの chunk も持っていない**。宣言が自己整合かつ hash 安定でも、実 layout と食い違い得る（CLAUDE.md §運用15 の ABSENT-IN-CODE 類型）。本 doc は §3 の `COMPATIBILITY_TEST` / `REPRODUCTION_PROCEDURE` semantics でこの照合を**要求**するが、**実装 owner の指名は impl 解錠時 or D1.1-C prereg の事項**として carry する。

## 10. Open points

- 本 v5 = **cycle-1（FAIL）→ pN HOLD B1-B5 → cycle-2（実施済・max-2-cycles 到達）→ pN HOLD R1-R3 の fold**。以後の debate 再実行は Rs 裁量。fold の検証は §5 chain の pS / pN 両軸が担う。
- ⛔**hash 供給 locator = 未確定（最重要 open・Rs 裁定事項・§4/§12）**: 対象 slot = **`tensor_binding` と `normalization` の両方**（同型）。選択肢 = **A**（hash 由来 canonical ref・ただし CAS 要求 + `E_BINDING_HASH_MISMATCH` が store 整合性検査に縮退）/ **A′**（frozen `EvidenceRecord.source_ref` を束縛・全 grade 存在・最小）/ **B**（frozen A schema delta = supersession + Rs review）。実測 = locator は **rank 3 のみ有・SHADOW rank 2 に無**（§4 表）。**CC1 単独で確定できないため Rs 裁定として上程**。
- §5 の必須化可否・class 台帳・判定器・窓幅 = slice 詳細 prereg + Rs 裁定。
- U-2 の producer artifact 阻止・U-5 の demo 移行・**U-6 の topology ledger 束縛** = D1.1-C prereg への必須入力（**DDR への登録 = p6 へ dispatch 済** — cycle-2 CC5-CH4: 4 carry がいずれも DDR 未登録では次 chunk の [DEFER-RECON] が素通りする）。
- **`stats_key` の一意性規則**（per-feature 一意か共有可か）= 未定・§1.2 参照。
- 「open = 0」の無条件宣言はしない（frozen §10 と同規律）。

## 11. Module layout（impl GO 時に確定 — 宣言のみ）

`thread_isaac_lab/wmso/contracts_v2/`: `tensor_binding.py`（型 + 単体 validator）+ `certify.py` への cross-artifact 検査追加 + `tests/test_tensor_binding.py` + `tests/fixtures/`（banked fixture を移送）。**本 chunk では書かない**（impl = CLOSED）。既存 `thread_isaac_lab/wmso/d1/` との関係（`is_hex64` / `sha256_bytes` の再利用可否・supersede か併存か）は impl 着手時に明記する。

## 12. 版歴 / fold-map

- **v1**（2026-07-20 09:56、`31d96783c3f5392c…` @ `71e3985aab`）→ **5体 CC Debate cycle-1 = ⛔FAIL**（verdict record `WMSO_D11B_CC_DEBATE_CYCLE1_VERDICT_RSTECHLEAD2_20260720.md`、panel = lens A/B/C/D + NHA、union 集約 31 項）。
- **v2**（2026-07-20 11:08–11:13 実測 bracket、本版）— fold:
  - **D-1 (CRITICAL)** §3 の EP 不在主張 = FALSE → **全 grade を閉じた query で再導出**（wildcard/`_applicable` 展開）+ SHADOW rank2 が RECONSTRUCTED_COMPATIBLE を受理する事実を明記 + 4 grade 分の subject semantics を追加。
  - **D-2 (CRITICAL)** IDENTICAL の自己 hash 不動点 → **IDENTICAL は hash を持たない**（null 必須）+ 外部確認 code。§0 の反循環規則を「構造 pattern」へ一般化。
  - **D-3 (CRITICAL)** flatten 順序未規定 → `FeatureBinding.flatten_order`（v1.0 = ROW_MAJOR）。
  - **D-4 (CRITICAL)** fixture 未 bank → **G-1/G-2/G-3 + 生成器を bank**（§6）。
  - **D-5..D-13 (HIGH)** hash-identity 検査追加 / history.layout 追加 / NORM_COHERENCE 一方向化 + KNOWN-operand gating / action source code / HANDOFF 除外 / bool 拒否 / 再現 command 撤回 + WCJ 実装 / demo 移行 blocker の loud 宣言 / version 検証 + churn 規律。
  - **D-14..D-31 (MED/LOW)** ≥2 frozenset golden / mask dtype+shape+scope / container_dtype / normalizer 値制約（frozen U13 の履行）/ COVERAGE_INVALID 統合 / 空 features / belief 重複 / §5 PROVISIONAL 化 / §5 不確実性 channel + ledger hash / reuse gate 記録（§9）/ manifest 追加義務の撤回 / CONFIG_HASH 検査可能化 / U-2 over-claim 撤回 / enum 改訂に Rs review / mis-citation 修正（frozen §7c → **§8** / RV5-W-P0-5 → **RV7-P0-3**）/ 88mm の SSOT 引用 / fixture 代表性の非主張。
  - **NHA 縮小要求**: §3 の誤主張撤回・§5 の必須化取り下げ・§8-2 降格を採用。G-2 破棄は不採用（判別に必要ゆえ修正版で再生成）。
  - **/reward-design 該当性 再判定（prereg §7 の条件付き義務・§12 D-24）**: §5 が計測 field を扱うため trigger を認め、再判定を実施 → **現時点も非該当**。理由 = 本 doc は field の**契約**（名前・dtype・単位・frame・ledger の content-address）のみを定め、**success/failure の判定式・閾値・窓幅を一切定めない**（それらは slice 詳細 prereg へ明示委譲）。⚠ただし **slice prereg が判定式・閾値を定める段では `/reward-design` + `/pre-check` が発火する**（直交ゲート・L と独立）— slice prereg の必須入力として carry。
- **v3**（2026-07-20 11:43 実測、本版）— **pN exact-pin DESIGN HOLD B1-B5 の fold**（custody は PASS: pN が隔離 git-archive + `env_isaaclab` wrapper で builder を再走し 3 hash・byte 数・frozenset variant を再現）:
  - **B-1 (CRITICAL) 供給 locator が未定義** → §4 の「frozen delta 非要」を**撤回**。frozen `ArtifactSlot = {state, artifact_hash}` に ref が無く、`ProofItem.ref` は evidence 側の参照で TensorBindingSpec 実体 ref は全 grade 共通必須でない ⇒ `resolve_artifact` に渡す ref の出所が設計上未定義。**resolver 関数の実在確認 ≠ locator の実在**（v2 の私も pS も関数実在だけで「delta 非要」と結論した）。選択肢 A（hash 由来 canonical ref）/ B（frozen schema delta = Rs review）を明示し **Rs 裁定事項として上程**。
  - **B-2 (CRITICAL) fixture が schema 非適合** → v2 で必須化した `container_dtype` が golden 3 本とも欠落、builder も未検査。**再現する hash は schema 適合を証明しない**。fixture 再生成（全 hash 更新）+ **builder に schema 適合 assertion を追加**（必須 member 対称差 / cast table / normalizer payload / mask dtype・自己参照・昇順）。⚠pS の再走はこれを見逃した — **two-key の pN レグが機能した実例**。
  - **B-3 (HIGH) MIN_MAX 無検査** → §1.2 に scheme 別 stats payload 契約、§4 `E_BINDING_NORMALIZER_VALUE` を scheme 別述語（isfinite・要素数・std>0 / min<max）へ完全化。
  - **B-4 (HIGH) container cast 規約なし** → §1.4b に v1.0 conversion table + `E_BINDING_CAST_FORBIDDEN` / `E_BINDING_CAST_LOSSY`。
  - **B-5 (HIGH) topology_ledger_hash が格納不能** → §5 表から削除し **D1.1-C metadata carry（§8-6）**へ。残る穴（同 dtype/shape で意味の異なる台帳）を PROVISIONAL 理由として loud 記録。
  - pN 指名 3 点: ①frozen delta 非要 = **NO-PROOF（撤回済）** ②U-5 と `portfolio_has_IL` の整合 = **PASS**（C 完了 ∧ demo 再記録まで IL=false、B 単独で slice/L0 claim 不可）③**cycle-2 = REQUIRED**（B1-B5 限定）。
- **v4**（2026-07-20 12:10 実測、本版）— **B1-B5 限定 cycle-2 debate の fold**（panel = lens B1 / B2 / B3+B4 / B5 + NHA。fold 判定 = B2/B3/B5 に FAITHFUL+SUFFICIENT 票、B1/B4 は全員が FAITHFUL-BUT-INSUFFICIENT。custody = 4/4 が builder 独立再走で hash 再現）:
  - **C2-1（安全関連・CRITICAL）** BOOL feature に normalizer/transform を付すと mask が無効化される（B4 fold の `v ≠ 0` 読み出し規約が可能にした）→ `E_BINDING_NUMERIC_STAGE_ON_BOOL` + builder guard。
  - **C2-2（5/5 + NHA）** `E_BINDING_CAST_LOSSY` が standalone validator で到達不能（**v2 が D-18 で除去した類型の再発**）→ **削除**し、可逆性を §3 `COMPATIBILITY_TEST` の producer 側 obligation へ。
  - **C2-3（CRITICAL）** B1 の escalation が問う範囲が誤り → **grade 別 locator 実測表**（rank 3 のみ有・**SHADOW rank 2 は無** = 最初の slice が動く grade）+ **選択肢 A′**（frozen `EvidenceRecord.source_ref` 束縛）+ **A の下で `E_BINDING_HASH_MISMATCH` が store 整合性検査に縮退する帰結** を追記し、3 択の完全集合として上程。**`normalization` slot も同型の locator 問題として open に収容**。
  - **C2-4（CRITICAL）** §2 DC-1 と §7 が撤回済みの供給経路に依存したまま → 両所に BLOCKED flag。
  - **C2-5（HIGH）** §5 の carry が §5D の穴を閉じるかのような記述 → **detect ≠ prevent** に訂正（§5D の入力に run manifest は無い）。
  - **C2-6（HIGH×3）** builder が 14 型中 5 型しか検査せず（B2 の欠陥そのものが `HistorySpec.layout` 等で再現）/ `container_dtype` が 1 値のみで判別不能 / negative control 皆無 / 出力先省略時に **banked file を上書きして改竄を修復** → 全型検査 + enum allowlist + **negative control 16 本（16/16 発火を毎回実証）** + **`--verify` 非破壊 mode** + **G-4 追加**（INT32 dtype・INT32 container・BOOL container）。
  - **C2-7（MED/LOW）** isfinite 述語の vacuity 明示 / `std > 0` を B-declared strengthening と明示 / 正規化の**適用順序と式**を明文化 / `stats_key` 一意性を open に登録 / dead `topology_ledger_hash` pin を §6 と builder から削除 / §10 の版・cycle-2 状態・U-6 欠落を訂正。
  - **NHA = HOLD（縮小せよ）**: 収束はしているが「fold が新 surface を生み次の finding を生む」構造（pN 5 findings のうち 4 件が v2 自身の追加物由来）。v4 は NHA の minimal path 3 点（option A′+実測 / CAST_LOSSY 削除 / topology pin sweep）を全採用し、**§5 への field 追加・cast table 拡張・stats payload の追加規定は行わない**。
- **v5**（2026-07-20 12:40 実測、本版）— **pN exact-pin HOLD R1-R3 の fold**（custody/evidence は PASS: pN が隔離 archive + `./isaaclab.sh -p` で `--verify` の非書込・4/4 hash 再現・negative control 全発火を確認）:
  - **R1（CRITICAL・全単射破れ）** §1.4b が INT32→FLOAT32 を無条件許可 → **16777216 と 16777217 が同一 float32 に衝突**（本 session 実測）。v4 の「可逆性は §3 `COMPATIBILITY_TEST` へ委譲」は、frozen EP 実測で当該 proof が **rank 2 でのみ必須**・**CLOSED_LOOP の rank 3/4 では不要**ゆえ肝心の grade を覆っていなかった。⇒ **v1.0 で当該 cast を禁止**（最小・fail-closed）。**自己評価**: v4 で私は「削除する code の到達不能性」は検証したが「**委譲先 obligation の到達性**」を検証しなかった — pS が本 arc で記録した恒久教訓「**存在 ≠ 十分**」の同型（proof kind の存在 ≠ 全 grade での要求）。
  - **R2（records/current-state）** header が cycle-2 を「次工程」と書いたまま / fixture 列挙が {1,2,3} のまま / §7 test plan に G-4 欠落 / §10 の Rs 選択肢が A/B のみで **A′ と `normalization` 同型 locator を落としていた** → 全て現行 decision surface（**A/A′/B × tensor_binding + normalization**）と G-1..G-4・cycle-2 完了へ同期。
  - **R3（evidence over-claim）** builder の `wcj_bytes`/`check_type` は frozen WCJ の完全 validator ではないのに §6 がそう読める主張をしていた。**実証負例（pN 提示・本 session 再現）**: `policy_rate_hz` を `"Infinity"` に置換しても `--verify` が rc=0 / conformance PASS。⇒ **CanonicalDecimal（frozen 正規表現そのもの）・NFC・64-hex を実検査に追加**（negative control 16→**24 本**、24/24 発火）+ **§6 に「検査するもの / しないもの」を明記**し、WCJ 完全性は impl の `canonicalize()` leg として事前登録。
  - ⚠**fixture hash は全て不変**（`af90712a…` / `991651b9…` / `dd14f6b6…` / `59bbfbba…`）— 既存 fixture は INT32→FLOAT32 を使っておらず、追加した検査も既存値を拒否しないため。**再 pin 不要**（NHA が警告した churn を回避）。
- **v6**（2026-07-20 13:06 実測、本版）— **著者自検出 1 件の fold**（pS の v5 設計軸 PASS `4e633489a9c2…`（12:51）**後**に発見。pS/pN いずれの指摘でもない）:
  - **S-1（検証計器の欠陥・MED）** negative control 24 本が **生成 mode でしか走らず `--verify` では 0 本**だった。⇒ 両経路で実行（§6 の v6 訂正ブロック）。**発見経緯**: pS が「optional・cosmetic」とした §6 invalid corpus の `等` 表記を判定する際、「禁止は列挙されているか」ではなく「**禁止が実際に発火するか**」を閉じた query で確かめに行き、negative control の実在を確認 → **実在 ≠ 発火**ゆえ走らせ → 発火は確認できたが**それが生成経路でしか起きない**ことが判明。pS の当該 optional 指摘自体は**判定どおり cosmetic**（`表外 cast` の一般則 + §1.4b 表セル ⛔ + negative control #45 が INT32→FLOAT32 を実際に拒否）ゆえ **v6 でも変更しない**（NHA の churn 規律）。
  - **自己評価**: v5 で私は §6 に「検査するもの / しないもの」を書いて R3 を閉じたつもりだったが、**その分類は「builder は何を検査するか」の軸しか持たず、「どの経路で走るか」の軸を欠いていた**。R3 の本質は *主張の広さ > 経路の届く範囲* であり、v5 の修正は主張の内容だけを絞って**経路の被覆を検証しなかった** ⇒ 同じ穴が一段ずれて残った。R1 の「委譲先 obligation の到達性を検証しなかった」と**同型の反復**（到達性の軸を見ない）。今回は verifier の指摘を待たず自検出したが、**v5 の時点で気づくべきだった**。
  - **fixture hash は全て不変**（`af90712a…` / `991651b9…` / `dd14f6b6…` / `59bbfbba…`）— negative control は in-memory deepcopy のみを変異させるため。**再 pin 不要**。変更は `build_goldens.py` と本 doc §6/§12/header のみ。
- **v1 → v2 の非変更点**: 統治・carries・frozen 不変・impl CLOSED・§0 の WCJ 継承方針（B-declared 分を分離明記した点のみ変更）。
