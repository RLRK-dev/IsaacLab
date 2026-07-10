---
title: Vision Domain Randomization Design (T-Vision-DR / L1.A.3)
created: '2026-05-03T10:30:00+09:00'
last_updated: '2026-05-03T10:30:00+09:00'
status: approved (Rs batch approve 2026-05-03 T-ROOT-COORD#s11) — Tier 0-1 mandatory scope confirmed、Tier 2 (D7/D8 + R7 real-cam) OUT-OF-SCOPE (L1.F.1 trigger 経の別 task)
node_id: T-Vision-DR
parent_node: T-Vision (L1.A capability axis)
spec_version: LTM-1 v1.1
tags:
  - knowledge
  - vision
  - domain-randomization
  - sim-to-real
  - phase-5-4
  - design-reference
doc_class: design-surface
---

# Vision Domain Randomization Design (L1.A.3)

> **本 file の位置付け**: T-Vision-DR (L1.A.3) の technical design reference。`project_l1a_vision_design_complete_2026-04-27.md` §4.5 (Targeted DR + Curriculum 推奨) を base に refinement、CC8 KA2 OQ5 (D8 dual-arm self-occlusion) を反映、impl 起票時 (`CC-L1A-Vision-DR-Impl` 等) の prescribed structure。
>
> **Vault permission**: 06-Knowledge は CC Create/Update 許可 (`02-Workflow/Vault Write Permissions.md:26`)。04-Specs (Vision Pipeline.md / Camera Backend.md) は Rs専権 read-only、本 file は CC 編集可な technical reference。
>
> **04-Specs との関係**: R6 (Stage 1-4 解析的計算 + 物理モデル) compliant、本 file は Stage 1 (mask) + Stage 2 (back-projection) の robust 化として DR を位置付け、Stage 3 (Cosserat fitting) は physics-aware で DR と直交 (DR amplitude が Stage 3 fitting tolerance を超えないよう curriculum で制御)。

---

## 0. Executive summary (~5 lines、read-must)

- **Goal**: vision-augmented AC fine-tune が baseline (no DR) sim eval-det SR と equivalence 以上 (差分 ≤ 5pp)、Tier 0-1 sim-domain mandatory、**Tier 2 real-hardware = OUT-OF-SCOPE** (L1.F.1 trigger 経の別 task)
- **Strategy**: **Targeted DR + Curriculum (Tier 0→1)** 採択 (Wide DR / Adaptive DR / Real-sample augmentation = §4.3 で REJECTED)
- **8 dim taxonomy**: D1 lighting / D2 texture / D3 cable color / D4 camera intrinsic / D5 sensor noise / D6 background / D7 motion blur / D8 self-occlusion (CC8 KA2 OQ5: dual-arm self-occlusion = THREAD-specific、Tier 2 default + Tier 0 promote candidate)
- **Resource**: ~150-180 LoC + ~25h GPU + 10h dataset re-render (T-Vision-CableState と shared)
- **Trigger**: T-Vision-Pose Stage 1-2 substrate ready + T-Vision-CableState Stage A-E ready 後の impl 起票 (per state.md §1 dependencies、Rs §3.1 #4 起動承認 gate)

---

## 1. Goal + scope

### 1.1 Goal (state.md goal_verification 経)

- **Tier 0 PASS criterion**: D1-D5 critical randomized sim eval-det SR が baseline no-DR sim eval-det SR と等価 (差分 ≤ 5pp、N=100 ep × 5 seeds、cuda:2 deterministic)
- **Tier 1 PASS criterion**: + D6 background variation で Tier 0 PASS 同等性 maintain (差分 ≤ 5pp from Tier 0 baseline、同 N=100 × 5 seeds protocol)
- **Tier 2 (OUT-OF-SCOPE for this leaf goal)**: D7 motion blur + D8 occlusion + R7 real-hardware mIoU ≥0.85 は L1.F.1 sim-to-real trigger 経の別 task で起票 (NEST §3.5 cascade rule の本 leaf 永久 block 化を回避、state.md §1 + T-Vision umbrella OQ2 経で確定)

### 1.2 Why this scope split (CC2 MED-5 ACCEPT 経)

R7 real-hardware は real Franka Panda × 2 + 物理 cable hardware 依存 (現状 unavailable per L1.F.1 LOW priority、far future)。本 leaf を sim-domain Tier 0-1 に限定することで、parent T-Vision umbrella が "4 leaves COMPLETE" gate (state.md §1 goal) を達成可能、L0 vision-based 95% 達成 trajectory を unblock。

### 1.3 CC8 KA2 OQ5 reflection (D8 dual-arm self-occlusion)

> 7-CC Pre-Debate verdict 経で CC8 KA2 が指摘:「THREAD-specific dual-arm setup で D8 self-occlusion is significant、Tier 2 placement は THREAD-naive 可能性。empirical fail 時 D8 を Tier 0 promote candidate」

**THREAD specificity**: 2 wrist-mounted camera (`wrist_camera_manager.py:81 self._camera_count = 2`) が L/R 両 arm の hand body 6-th body offset に attach、5-clip routing 中に opposite arm が frame に侵入する scene が dataset 観察上 30-50% (sim default)。Wide DR 文献の D8 occlusion は random rectangular mask で十分だが、THREAD では opposite-arm geometry-aware occlusion が必要 (random mask は dual-arm self-occlusion pattern を under-represent)。

**Reflection in design**:
- Tier 2 default placement 維持 (state.md prescribed structure 準拠、CC8 KA2 NEUTRAL_LEANING_STRONG conservatism)
- §6 eval gate に "D8 promote trigger" 明示: Tier 0 PASS で baseline equivalence 達成不可 (差分 > 5pp) かつ failure analysis で opposite-arm self-occlusion が dominant cause (FAIL_CLOSED rate / mask completeness による attribution) の場合、D8 を Tier 0 promote
- §4 module structure に `D8 dual_arm_self_occlusion` stub 用意 (impl は trigger 後)

### 1.4 Out-of-scope (本 leaf 範囲外)

- **R7 real cable RGB sample × 50 で cable mIoU ≥ 0.85** → L1.F.1 sim-to-real trigger 経の別 task (T-Vision umbrella OQ2 経で OUT-OF-SCOPE 確定)
- **task_config.py 改変** → SSOT 規約 (state.md §4 禁止事項)
- **env file 改変** (newton_approach_cable_env.py 等) → CC#3 Option D pattern (state.md §4 禁止事項)
- **Wide DR / Adaptive DR / Real-sample augmentation の再評価** → §4.3 REJECTED 確定 (Phase 3 全失敗 precedent + design memo §6.1 R-2 HIGH)

---

## 2. 8-dim DR taxonomy (D1-D8)

### 2.1 5 critical dims (Tier 0、design memo §4.2)

| Dim | Sim default (現状) | Real target | Randomization range (Tier 0) | Source ref |
|-----|-------------------|-------------|------------------------------|------------|
| **D1 lighting** | Newton `default_light=True` 単 point light、`default_light_shadows=False` (`wrist_camera_manager.py:93-94`) | indoor lab 複 fluorescent + ambient | intensity ×{0.5, 0.75, 1.0, 1.5, 2.0} + color temp {3000, 4000, 5000, 6000, 6500}K | post-render RGB multiplicative scaling (offline pre-render or runtime adjustment) |
| **D2 texture** | uniform color cable + clip mesh (Newton `colors_per_shape=True` `wrist_camera_manager.py:95`) | manufacturer rubber sheen + scratch | 5 preset material variation (`mat_smooth / mat_matte / mat_glossy / mat_scratched / mat_dirty`) | offline pre-render dataset variants (Newton material rebuild cost prohibitive per-episode、§4 R-DR-1) |
| **D3 cable color** | sim default monochromatic (assumed neutral RGB) | black / red / blue / yellow / custom | 5 preset RGB: `(0.05,0.05,0.05) / (0.7,0.1,0.1) / (0.1,0.1,0.7) / (0.7,0.7,0.1) / (custom user-spec)` | offline pre-render with cable shape body color override (Newton model body shape API) |
| **D4 camera intrinsic** | `compute_pinhole_camera_rays` `wrist_camera_manager.py:101-104` FOV=45° pinhole、principal point=center、no distortion | RealSense D435i / Logitech (lens distortion + chromatic aberration) | FOV ±5° (40-50°) + principal point ±5px (5-pixel translation) + k1/k2 distortion coefficient {-0.05, 0, 0.05} | per-episode ray rebuild at reset (cheap、~ms per episode、§4 R-DR-5) |
| **D5 sensor noise** | depth = ground truth (no noise)、color = perfect rasterization | depth σ ~3mm @ 1m + 5% dropout、color additive Gaussian + chromatic shift | depth: `+ N(0, 3mm) + 5% per-pixel dropout (preserve cable region floor)`; color: `+ N(0, 0.02) channel-wise + chromatic shift ±2px` | torch-level noise injection on `depth_tensor` / `rgb_tensor` after `WristCameraManager.update`、§4 R-DR-4 cable preservation |

### 2.2 Tier 1 dim (recommended、design memo §4.2 medium)

| Dim | Sim default | Real target | Randomization range | Source ref |
|-----|-------------|-------------|---------------------|------------|
| **D6 background variation** | sim: empty + table only | real lab clutter (other equipment、cables) | 10 preset clutter scenes (USD asset load via Isaac Lab `AssetBaseCfg`、wall / monitor / additional table) | T-Vision-CableState shared dataset re-render (Tier 1 stage、+~3h GPU) |

### 2.3 Tier 2 dims (OUT-OF-SCOPE for this leaf goal、L1.F.1 trigger 経で別 task)

| Dim | Sim default | Real target | Randomization range | Note |
|-----|-------------|-------------|---------------------|------|
| **D7 motion blur** | none | 30 FPS wrist motion blur | kernel σ=0.5-2px Gaussian | torch-level convolution post-render |
| **D8 self-occlusion** | gripper-cable occlusion only | hand / body / dual-arm self-occlusion | (a) random rectangular mask 5-15% area (literature default) + (b) **opposite-arm geometry-aware overlay** (THREAD-specific、CC8 KA2 OQ5 reflection) | **Tier 0 promote candidate**: §6 trigger を満たした場合、Tier 0 に promote (本 leaf empirical fail 時) |

### 2.4 D8 promote trigger (CC8 KA2 OQ5 implementation hook)

```
IF Tier 0 PASS criterion fail (差分 > 5pp、§6.1)
   AND failure attribution analysis (FAIL_CLOSED rate per CC4 v3.2 §10 R-3 + mask completeness < 0.6 for ≥30% scenes)
   = "opposite-arm self-occlusion dominant"
THEN promote D8 from Tier 2 → Tier 0 (本 leaf scope 内で再 train、~ +3h GPU)
ELSE Tier 2 維持 (L1.F.1 trigger 経で別 task 起票)
```

---

## 3. Tier boundary + curriculum protocol

### 3.1 Tier boundary (3-tier with intra-Tier 0 sub-curriculum)

```
[Tier 0a warm-up]  D4 + D5 only (geometric + sensor noise low)
    ~3h GPU, mild perturbation
    ↓ plateau detect (Δ ≤ 1pp / 100k iters × 2 sequential)
[Tier 0b mid]      + D2 + D3 (texture + color, 5 preset each)
    ~5h GPU
    ↓ plateau detect
[Tier 0c full]     + D1 (lighting full ramp, intensity + color temp)
    ~4h GPU
    ↓ Tier 0 PASS gate (§6.1)
[Tier 1]           + D6 background variation (10 preset clutter)
    ~3h GPU
    ↓ Tier 1 PASS gate (§6.2)
[Tier 2 OUT-OF-SCOPE for this leaf]
    L1.F.1 trigger 経で別 task (D7 + D8)
    OR §2.4 D8 promote trigger 該当時、本 leaf 内で D8 → Tier 0 (例外 path)
```

### 3.2 Curriculum design rationale

- **Why intra-Tier 0 sub-curriculum (0a→0b→0c)**: design memo §6.1 R-2 HIGH "Targeted DR が Tier 0-2 で coverage 不十分、real-world transfer fail" mitigation。Phase 3 over-randomize 全失敗 precedent 教訓により、Tier 0 内でも段階導入で training collapse 回避。
- **Plateau detect criterion**: Δ ≤ 1pp / 100k iters × 2 sequential = sim eval-det SR が連続 2 windowで安定。R-3 MEDIUM "Late Fusion + 50D obs migration で AC fine-tune value_loss explode" の rollback criterion (CC4 v3.2 E.6: value_loss > 3× baseline @ iter 20) と並行 monitor。
- **Why no Adaptive DR**: §4.3 で REJECTED (~300 LoC + 20h GPU、impl complexity 高、debug 困難)、manual curriculum で十分 efficient。

### 3.3 Curriculum 禁止事項 (state.md §4 経)

- **Tier skip 禁止**: Tier 0a → Tier 0c 直接 skip / Tier 0 → Tier 1 plateau detect なし skip = training collapse risk (design memo §6.1 R-2 HIGH)
- **Tier amplitude inflation 禁止**: §2 で定義した parameter range を勝手に拡張 = Wide DR への slip risk (state.md §4 禁止事項 "Wide DR 禁止")
- **Tier mid 中の rollback 禁止**: Tier 0b training 中に Tier 0a に戻すと curriculum stability 破壊。Plateau detect で次 stage 進行のみ許可、value_loss explode 時は §6 fail handling で fresh-start (rollback 連鎖は prohibited.md "崩壊 checkpoint resume 禁止" 該当)

---

## 4. Module structure + LoC accounting

### 4.1 File layout (新規 module + 既存 extension)

```
thread_isaac_lab/configs/vision_dr_config.py            (NEW、~40 LoC)
thread_isaac_lab/envs/dr/                               (NEW directory)
├── __init__.py                                         (~5 LoC)
├── material_variation.py    (D2 texture + D3 cable color、~25 LoC)
├── lighting_variation.py    (D1 lighting、~20 LoC)
├── sensor_noise.py          (D5 depth/color noise、~20 LoC)
├── camera_intrinsic.py      (D4 FOV/principal/distortion、~25 LoC)
└── curriculum.py            (Tier 0a/0b/0c/1 ramp + plateau detect、~30 LoC)
thread_isaac_lab/envs/wrist_camera_manager.py           (EXTENSION ~15 LoC、D4 entry point only)
                                                        (※ env file 改変禁止と区別: WristCameraManager は camera 管理 utility、env logic ではない)
```

### 4.2 LoC accounting (~150-180 target)

| Module | LoC | Tier coverage | Note |
|--------|-----|---------------|------|
| `configs/vision_dr_config.py` | 40 | all | DR parameter ranges + tier flags + curriculum thresholds (新 file、`task_config.py` 改変なし) |
| `envs/dr/__init__.py` | 5 | — | module export |
| `envs/dr/material_variation.py` | 25 | Tier 0b | D2 (5 preset material) + D3 (5 preset cable color)、offline pre-render hook |
| `envs/dr/lighting_variation.py` | 20 | Tier 0c | D1 post-render RGB multiplicative scaling + color temp |
| `envs/dr/sensor_noise.py` | 20 | Tier 0a | D5 depth Gaussian + dropout (cable preservation floor) + color Gaussian |
| `envs/dr/camera_intrinsic.py` | 25 | Tier 0a | D4 FOV ±5° + principal point ±5px + k1/k2 distortion (per-episode ray rebuild) |
| `envs/dr/curriculum.py` | 30 | all | plateau detect + tier ramp logic + Tier 1 D6 background variation hook |
| `envs/wrist_camera_manager.py` extension | 15 | Tier 0a (D4) | per-episode FOV / principal point override entry point (既存 method 拡張のみ、core API 変更なし) |
| **Total** | **~180** | — | within 150-180 target、Tier 2 D7/D8 module は trigger 後別 task で追加 (~20-30 LoC additional 想定) |

### 4.3 Module API outline

```python
# vision_dr_config.py (~40 LoC)
@dataclass
class VisionDRConfig:
    tier: Literal["0a", "0b", "0c", "1"] = "0a"
    enable_d1_lighting: bool = False    # Tier 0c+
    enable_d2_texture: bool = False     # Tier 0b+
    enable_d3_cable_color: bool = False # Tier 0b+
    enable_d4_intrinsic: bool = True    # Tier 0a+
    enable_d5_noise: bool = True        # Tier 0a+
    enable_d6_background: bool = False  # Tier 1+
    # parameter ranges (D1-D6)
    d1_intensity_set: tuple = (0.5, 0.75, 1.0, 1.5, 2.0)
    d1_color_temp_set: tuple = (3000, 4000, 5000, 6000, 6500)
    d4_fov_jitter: float = 5.0  # ±deg
    d4_principal_jitter: int = 5  # ±px
    d4_distortion_set: tuple = (-0.05, 0.0, 0.05)  # k1
    d5_depth_sigma: float = 0.003  # 3mm
    d5_depth_dropout: float = 0.05  # 5%
    d5_color_sigma: float = 0.02
    # curriculum thresholds
    plateau_window: int = 100_000  # iter
    plateau_eps: float = 0.01  # 1pp
    # ...
```

```python
# envs/dr/curriculum.py (~30 LoC) outline
class DRCurriculum:
    def __init__(self, config: VisionDRConfig): ...
    def step(self, sim_eval_det_sr: float, value_loss: float) -> str:
        """Returns next tier ('0a', '0b', '0c', '1', or 'PASS')."""
        # plateau detect: SR 履歴 100k iter window で Δ ≤ plateau_eps × 2 連続
        # value_loss > 3× baseline → freeze tier (CC4 v3.2 E.6 rollback)
        # Tier 0 PASS gate (§6.1) → transit to Tier 1
        # Tier 1 PASS gate (§6.2) → return 'PASS'
        ...
```

### 4.4 既存 file への影響範囲

- **wrist_camera_manager.py**: D4 entry point として `update_intrinsics(fov_deg, principal_offset, distortion_k1)` method 追加 (~15 LoC)、既存 `compute_pinhole_camera_rays` を episode reset 時 rebuild する pattern (init 時の `self._camera_rays = ... ` を method 化)
- **wrist_camera_manager.py の `_depth_buf` / `_color_buf` 操作**: D5 sensor noise は torch-level injection (post-render、`depth_tensor` / `rgb_tensor` property 取得後)、camera_manager 内部は変更不要
- **新規 `envs/dr/` directory**: 全 Tier 0/1 logic を分離、既存 env file (newton_approach_cable_env.py 等) は改変なし (state.md §4 禁止事項遵守)

---

## 5. GPU + dataset budget

### 5.1 GPU wall ~25h breakdown

| Phase | GPU wall | Cumulative |
|-------|----------|-----------|
| Tier 0a warm-up (D4 + D5) | ~3h | 3h |
| Tier 0b mid (+ D2 + D3) | ~5h | 8h |
| Tier 0c full (+ D1) | ~4h | 12h |
| Tier 1 (+ D6 background) | ~3h | 15h |
| Tier 0/1 eval gate (R5 sim eval-det N=100 × 5 seeds) | ~3h | 18h |
| Buffer / contingency (R-DR-3 curriculum collapse re-train、value_loss explode rollback) | ~7h | **~25h** |

### 5.2 Dataset re-render ~10h breakdown (T-Vision-CableState と shared)

| Stage | Dataset wall | Note |
|-------|--------------|------|
| Tier 0b D2 material (5 preset) × 10k scenes | ~4h | Newton model rebuild bottleneck per material (R-DR-1)、batch size 制約 |
| Tier 0b D3 cable color (5 preset) × 10k scenes | ~3h | cable shape body color override、Newton model rebuild |
| Tier 1 D6 background (10 preset clutter) × 5k scenes | ~3h | Isaac Lab `AssetBaseCfg` USD asset load |
| **Total** | **~10h** | T-Vision-CableState shared (1 回 re-render で双方 cover、coordinator 経で sequence per state.md §1 dependencies) |

### 5.3 Coordinator-driven sequencing (T-Vision-CableState shared blocker)

- **Pre-condition**: T-Vision-CableState の Stage A-E impl ready (Cosserat fitting + segment confidence calibration completed)
- **Re-render execution**: T-Vision-DR (本 leaf) と T-Vision-CableState の coordinator が Tier 0b stage で 1 回 re-render を sequence 実行 (重複 re-render 回避)
- **Asset shared in `data/dr_dataset_v1/`** (新 directory、`thread_isaac_lab/data/` 配下、git-ignore 済 `.gitignore` "data/" entry)

---

## 6. Eval gate (Tier 0 / Tier 1 / Tier 2 OUT-OF-SCOPE)

### 6.1 Tier 0 PASS gate (D1-D5 critical)

**Criterion**:
- D1-D5 randomized sim eval-det SR (N=100 ep × 5 seeds、cuda:2 deterministic、Tier 0c full configuration) が baseline no-DR sim eval-det SR と equivalence 以上 (差分 ≤ 5pp、within ±5pp interval)
- Tier 0c training 中の AC value_loss が baseline の 3× 未満 (CC4 v3.2 E.6 rollback criterion 整合)
- Tier 0a → 0b → 0c 各 stage で plateau detect 経た上での gate 評価 (skip 禁止、§3.3)

**Fail handling**:
- 差分 > 5pp + value_loss < 3× baseline = curriculum 過剰 → §2.4 D8 promote trigger を評価 (failure attribution: opposite-arm self-occlusion dominant か?)
- value_loss > 3× baseline = AC fine-tune collapse → fresh-start with Tier 0a baseline ckpt (prohibited.md "崩壊 checkpoint resume 禁止" 遵守、design memo §6.1 R-3 MEDIUM mitigation)
- 両条件 fail = §6.4 escalation (Rs に escalate、再 design 起票)

### 6.2 Tier 1 PASS gate (+ D6 background)

**Criterion**: Tier 1 (D1-D6) randomized sim eval-det SR が Tier 0 PASS baseline と equivalence (差分 ≤ 5pp、N=100 × 5 seeds 同 protocol)

**Fail handling**: D6 background が D1-D5 と orthogonal でない (semantic seg confusion 等) → D6 preset reduction (10 → 5 preset)、再 train

### 6.3 Tier 2 OUT-OF-SCOPE for this leaf goal (R7 real-hardware)

**本 leaf 範囲外** (state.md §1 + T-Vision umbrella OQ2)。L1.F.1 sim-to-real readiness 経の別 task で:
- R7 criterion: real cable RGB sample × 50 で cable mIoU ≥ 0.85 (現 wrist_R 0.248 → 0.85 step、L1.F.1 task で MVP-0B v2 経の R-side fine-tune 完了 prerequisite)
- D7 motion blur + D8 occlusion (literature default + opposite-arm geometry-aware) を Tier 2 で別 task 起票

### 6.4 Escalation path (§6.1 + §6.2 両 fail 時)

- Failure attribution analysis (Stage 1 mask completeness、Stage 2 back-projection error、Stage 3 Cosserat residual)
- Stage 1 mask 起因 → DR amplitude reduction + Stage 1 (semantic seg) re-train (CC4 v3.2 §5 spec)
- Stage 3 Cosserat fitting tolerance 超過 → DR amplitude を Stage 3 fitting tolerance 内に bound
- Re-design 起票 = Rs escalation (本 leaf scope 拡張 vs 設計 root cause 修正の判断、prohibited.md "対処療法禁止" 遵守)

---

## 7. Risk register (DR-specific)

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| **R-DR-1** | Newton material variation API limitation: per-episode material swap = model rebuild = cost prohibitive | **HIGH** | Offline pre-render dataset variants (Tier 0b 段で 1 回 dataset re-render、5 preset material × 10k scenes) → curriculum 中は dataset sample only |
| **R-DR-2** | D8 dual-arm self-occlusion (CC8 KA2 OQ5、THREAD-naive Tier 2 placement) | HIGH | §6.1 Tier 0 fail 時の D8 promote trigger 用意 (failure attribution evidence-based promotion、Tier 2 → Tier 0 path) |
| **R-DR-3** | Curriculum collapse (Tier 0a → 0b → 0c plateau detect なし skip / value_loss explode) | HIGH | §3.2 plateau detect (Δ ≤ 1pp / 100k iters × 2 sequential) + CC4 v3.2 E.6 value_loss rollback (3× baseline @ iter 20) + §3.3 Tier skip 禁止 |
| **R-DR-4** | D5 depth dropout cable annihilation (5% per-pixel dropout が thin cable mask を eliminate) | MEDIUM | Cable preservation min-area floor: 各 mask 内 dropout は最大 50% を超えない floor (cable region の min-area threshold)、scene-wide dropout は 5% target 維持 |
| **R-DR-5** | D4 per-episode ray rebuild cost (FOV / principal point change で `compute_pinhole_camera_rays` re-call) | LOW | Episode reset 時のみ rebuild (~ms per episode、batch size には影響なし)、step 中は不変 |
| **R-DR-6** | Dataset re-render shared with T-Vision-CableState (重複 re-render 回避 coordination) | MEDIUM | T-Vision-CableState の Stage A-E impl ready precondition 経、coordinator-driven sequence (§5.3)、asset path `data/dr_dataset_v1/` 共有 |

---

## 8. Open questions + impl trigger

### 8.1 OQ (impl 起票時に再評価)

| OQ | Topic | Trigger |
|----|-------|---------|
| OQ-DR-1 | D8 promote の地学的 trigger 閾値 (mask completeness < 0.6 for ≥30% scenes が適切か) | Tier 0 PASS gate evaluation 時の failure attribution analysis 結果 |
| OQ-DR-2 | D6 background preset 数 (10 → 5 reduction の必要性、§6.2 fail 時) | Tier 1 PASS gate evaluation 時 |
| OQ-DR-3 | Newton material API per-episode swap が将来 efficient 化された場合、offline pre-render → runtime swap 移行の cost-benefit | Newton release note + benchmark measurement |
| OQ-DR-4 | D4 distortion model (k1 only vs k1+k2 + p1+p2 tangential) が RealSense D435i fidelity に十分か | Real-hardware available 後の calibration validation (L1.F.1 trigger) |

### 8.2 Impl 起票 trigger (NEST §3.1 #4 起動承認 gate)

**Pre-condition** (state.md §1 dependencies):
- T-Vision-Pose Stage 1-2 substrate ready (3-cam mask + back-projection pipeline、CC4 EXP-046 PCA-center 3.92mm error baseline 経)
- T-Vision-CableState Stage A-E ready (Cosserat fitting + segment confidence calibration completed)
- T-Vision-CableState coordinator-driven dataset re-render sequence 確立 (§5.3 R-DR-6)

**Impl task name candidate**: `CC-L1A-Vision-DR-Impl` (T-Vision-DR child session、本 design memo prescribed structure 経で起票)

**Estimated total**: ~150-180 LoC + ~25h GPU + ~10h dataset re-render (shared with T-Vision-CableState)

---

## 9. Cross-references

### 9.1 Parent / sibling NEST nodes

- **Parent**: `thread-vault/T-Vision/state.md` (L1.A capability axis、IN_PROGRESS、4 leaves COMPLETE で Phase 5-4 G8 unblock)
- **Sibling precedent**: `thread-vault/T-Vision-Pose/state.md` (L1.A.1、Stage 1-2 substrate provider、本 leaf precedent edge)
- **Sibling shared dataset**: `thread-vault/T-Vision-CableState/state.md` (L1.A.2、shared dataset re-render asset)
- **Sibling downstream consumer**: `thread-vault/T-Vision-Fusion/state.md` (L1.A.4 / Phase 5-4 G8、本 leaf output を policy obs 50D 統合の prerequisite と扱う)

### 9.2 Design memo + 7-CC verdict

- **Design memo §4** (Targeted DR + Curriculum 推奨、4 candidate trade-off matrix): `~/.claude/projects/-home-rlrk-IsaacLab/memory/project_l1a_vision_design_complete_2026-04-27.md` §4
- **7-CC Pre-Debate verdict A' (CC8 KA2 OQ5 reflection)**: `thread-vault/T-Vision/state.md` §2 (CC8 KA2 NEUTRAL_LEANING_STRONG、D8 Tier 2 placement THREAD-naive concern)
- **L1.A architecture summary**: `thread-vault/06-Knowledge/LL-Vision-L1A-Architecture.md` §3 (Sub-task 3 Targeted DR + Curriculum)

### 9.3 Code references (impl 起票時の reference)

- `thread_isaac_lab/envs/wrist_camera_manager.py:53-207` (Newton SensorTiledCamera lifecycle、D4 entry point + D5 noise injection target)
- `thread_isaac_lab/envs/wrist_camera_manager.py:90-104` (SensorTiledCamera.Config + compute_pinhole_camera_rays、D1 + D4 affordance)
- `thread_isaac_lab/configs/task_config.py:70-71` `CABLE_SEGMENTS=40` × `CABLE_SEG_LEN=0.015` (cable shape SSOT、本 leaf 改変禁止)
- `thread_isaac_lab/tasks/hook_hanging/dual_arm_camera_env_cfg.py:1-120` (Isaac Lab 6-cam dual_arm env、Newton 2-cam canonical との区別注記)

### 9.4 Vault knowledge + 04-Specs reference (read-only)

- **04-Specs Vision Pipeline.md** (R6 Stage 1-4 spec、本 design は Stage 1-2 robust 化に位置付け、Stage 3 physics model と直交)
- **04-Specs Camera Backend.md** (Phase 2 RGB+depth pipeline、本 design extension の base)
- **04-Specs Vision Stack Roadmap.md** (Phase 3 Dreamer / CEM-MPC 全失敗 precedent、Wide DR REJECTED rationale)
- **04-Specs SOMA.md** (L0 / L1 / L2 goal、本 leaf goal は L0 vision-based 95% への precursor)
- **06-Knowledge LL-VisualObs-CameraSystem.md** (camera spec、`wrist_camera_manager.py` design rationale)
- **06-Knowledge LL-Newton.md** (Newton 環境制約、SensorTiledCamera API + material variation 制限の reference)
- **07-Design PoseEstimation-Design-v3.2.md** §10 risk register R-5 "DR distribution mismatch" (本 design mitigation 整合)、§5.4 (DD-PINN warm start、Stage 3 と DR の orthogonality 確保)

### 9.5 Logic tree + master list

- **Logic tree v1 §L1.A.3**: `~/.claude/projects/-home-rlrk-IsaacLab/memory/project_logic_tree_2026-04-27.md:44`
- **Master list v2 §9**: `~/.claude/projects/-home-rlrk-IsaacLab/memory/project_strategic_task_master_list_v2_2026-04-27.md` line 423-431 (4 task candidates 本 leaf 対応)

### 9.6 NEST infrastructure

- **LTM-1 v1.1 spec**: `thread-vault/00-Project-Management/operational-rule-LTM-1.md`
- **Manifest entry**: `thread-vault/00-Project-Management/project-tree-manifest.md` (T-Vision-DR node 登録、本 design 起票で last_updated)
- **CLAUDE.md L3 自動昇格 keywords**: `task_config.py` 改変なし / `newton` keyword present だが本 file は design memo (impl change なし) → L=L1 適切

---

## 10. Path Y / discipline references

- `feedback_premise_change_impact_analysis.md`: §1.3 で CC8 KA2 OQ5 reflection (D8 promote candidate) を proactive impact analysis で fold-in
- `feedback_check_existing_eval_grep.md`: §4.1 で `wrist_camera_manager.py` 既存 API + `dual_arm_camera_env_cfg.py` Newton 2-cam vs Isaac Lab 6-cam 区別を grep 経で fact-finding
- `feedback_factual_api_verification.md`: §2.1 D1-D5 で Newton SensorTiledCamera.Config + compute_pinhole_camera_rays の actual API source (wrist_camera_manager.py:90-104) 照合
- `feedback_geometric_vs_empirical_bc.md`: §6.1 / §6.4 で empirical eval gate (sim eval-det SR equivalence) を geometric/diagnostic 単独 NO-GO に依存させない
- `feedback_recommendation_policy_2026-04-30.md`: §0 で Targeted DR + Curriculum を ★ 推奨 (3 alternative REJECTED at design memo §4.3)、本 design は selection result の prescribed structure (新規推奨でなく refinement)

---

**Status**: Design active, impl pending Rs §3.1 #4 起動承認 (state.md §1 dependencies satisfied 後)
**Owner**: T-Vision-DR-Design-CC (本 session、design phase only)
**Next trigger**: T-Vision-Pose Stage 1-2 ready + T-Vision-CableState Stage A-E ready → Rs 経で `CC-L1A-Vision-DR-Impl` task 起票
