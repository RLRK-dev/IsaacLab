---
title: Cable State Estimation Phase 2 Impl Design (Stage C DD-PINN + Stage D Cosserat + Stage E Confidence)
created: '2026-05-04T03:55:00+09:00'
tags:
  - knowledge
  - vision
  - cable-state
  - phase-2-impl-design
  - design-reference
status: design (T-Vision-CableState-Impl-Phase-2-Design-CC、Phase 2 = design + skeleton scope only、impl + train は Phase 3-4 別 NEST node)
node_id: T-Vision-CableState-Impl-Phase-2-Design
session: T-Vision-CableState-Impl-Phase2-DDPiNN-Cosserat-Design-CC
parent_memo: thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md
doc_class: design-surface
---

# LL-Vision-CableState-Phase2-Impl-Design

> T-Vision-CableState 5-stage pipeline (Hybrid PCA + Cosserat) **Phase 2 implementation-ready design** memo。Parent memo (`LL-Vision-CableState-Design.md`、769 行、approved 2026-05-03) §2.4-§2.6 + §3 + §6 を **file/class placement + function signature + numerical design + train pipeline + test plan + risk register** level に展開。
>
> **scope:** design + skeleton のみ。impl + train は Phase 3 (Stage C train、~25h GPU + 5k labeled dataset) / Phase 4 (Stage D Cosserat impl + Stage E ECE calibration、別 NEST node) で起票。
>
> **base:** parent memo §2.4 (Stage C DD-PINN warm start)、§2.5 (Stage D Cosserat 7-term loss)、§2.6 (Stage E confidence calibration)、§3 (topology preservation)、§6 (R6 boundary integration)。
>
> **boundary:** R6 input-boundary 遵守 (新 3 modules は `thread_isaac_lab.estimators.*` + `torch` only、newton / envs import 一切なし)。`task_config.py` / `04-Specs/*.md` / `cable_state.py` 既存 skeleton / `vision_pipeline.py` Phase 1 完成 API 全 TOUCH FORBIDDEN。

---

## §0 Executive summary

- **Phase 2 = design + skeleton phase**: 3 new component skeleton modules (`estimators/cable_state_dd_pinn.py` + `cable_state_cosserat.py` + `cable_state_confidence.py`) + 1 design memo (本 file) + 1 smoke test。impl + train は Phase 3-4 別 NEST node。
- **Stage C (DD-PINN)**: 256 anchor (FPS) → per-point embed (3→64) → global pool (max+mean) → +prev_estimate (40×3 flat) → MLP 5×256 GELU → [40, 3]、~52k params (具体 count §2.1.4)、~20h GPU train + 5k labeled scenes (Phase 3)
- **Stage D (Cosserat)**: 7-term loss (L_pos + L_tan + L_bend + L_arc + L_id + L_temp + L_proj、weights §3.2)、PyTorch L-BFGS first + 5-restart σ=2mm + max_iter=200、Warp kernel optimization は Phase 5 latency profile 経で defer
- **Stage E (Confidence)**: 5 signals (visibility + density + residual + curvature + temporal) → logistic regression aggregation → ECE <5% target、val 1k sample post-train calibration (Phase 4)
- **Phase 1 → Phase 2 integration**: Phase 1 `MultiCamCableStatePipeline.estimate()` → `CableStatePhase1Result` (40×3 NaN-fillable + var_ratio + bin_counts) → Phase 2 components 接続 spec §5.1
- **既存 `estimators/cable_state.py` の `CableStateSolver` skeleton は本 Phase 2 で UNCHANGED**: Phase 4 impl で 3 sub-modules を delegate するように extend、本 Phase 2 では coarse skeleton (orchestration) + fine skeleton (3 components) の階層化のみ
- **R6 module boundary**: 新 3 modules は estimators top-level (existing `cable_state.py` 同 layer)、`core/` 配下ではない、boundary discipline 自主遵守 (Phase 4 impl 時に `tests/test_estimator_module_boundary.py` 拡張候補)

---

## §1 Scope & deliverables

### §1.1 In-scope (本 Phase 2 design + skeleton phase)

1. **Design memo** (本 file)、parent memo §2.4-§2.6 を impl-ready level に展開
2. **3 component skeleton modules**:
   - `estimators/cable_state_dd_pinn.py` (Stage C、~120 LoC)
   - `estimators/cable_state_cosserat.py` (Stage D、~150 LoC)
   - `estimators/cable_state_confidence.py` (Stage E、~100 LoC)
3. **1 smoke test**: `tests/test_cable_state_phase2_skeleton.py` (~80 LoC、imports + dataclass + DDPINN param count + Cosserat default weights + NotImplementedError reach)
4. **State.md + manifest + parent state update + Tier 2 deposit** (NEST integrity)

### §1.2 Out-of-scope (Phase 3-5 別 NEST node)

- Phase 3: Stage C DD-PINN train (~20h GPU + 5k labeled scenes generation infrastructure + checkpoint 生成)
- Phase 4: Stage D Cosserat 7-term loss impl (PyTorch L-BFGS gradient computation + multi-restart + identity inversion check) + Stage E ECE calibration (val 1k sample logistic regression coefficient fit)
- Phase 5: Q5 worst-case benchmark (10 U + 10 S scripted scenes + N=100 random + ECE measurement + identity inversion 0% verify)
- Warp kernel optimization (latency-critical 化判断は Q5 profile 経で defer)
- 04-Specs SSOT update (Rs専権、Vault Write Permissions)
- env file / `cable_state.py` / `vision_pipeline.py` 改変

### §1.3 Phase 2 deliverable summary

| deliverable | path | LoC est. | status |
|-------------|------|----------|--------|
| state.md | `T-Vision-CableState-Impl-Phase-2-Design/state.md` | ~150 | ✓ |
| design memo | `06-Knowledge/LL-Vision-CableState-Phase2-Impl-Design.md` (本 file) | ~500 | ✓ |
| Stage C skeleton | `estimators/cable_state_dd_pinn.py` | ~120 | (本 leaf) |
| Stage D skeleton | `estimators/cable_state_cosserat.py` | ~150 | (本 leaf) |
| Stage E skeleton | `estimators/cable_state_confidence.py` | ~100 | (本 leaf) |
| smoke test | `tests/test_cable_state_phase2_skeleton.py` | ~80 | (本 leaf) |
| parent state update | `T-Vision-CableState/state.md` | +5 | (本 leaf) |
| manifest update | `00-Project-Management/project-tree-manifest.md` | +10 | (本 leaf) |
| Tier 2 deposit | `_edit_requests/00010-T-Vision-CableState-Impl-Phase-2-Design-init.md` | ~30 | (本 leaf) |

---

## §2 Stage C: DD-PINN warm start (~50k params MLP)

### §2.1 Architecture (parent memo §2.4.2 → impl-ready)

#### §2.1.1 Input encoder

```
Input: cloud P ∈ ℝ^(N_pts × 3) (Stage A.3 voxel-fused output, expected N_pts ~1500-3000)
       prev_estimate (optional): CableState40 with positions [40, 3]

Step 1: Farthest Point Sampling (FPS) for diversity
  - Sample 256 anchor points P_anchor ∈ ℝ^(256 × 3) from P
  - FPS algorithm: greedy max-distance, O(256 × N_pts)
  - Implementation: pure torch native (CPU) or torch_geometric.nn.fps (GPU optional)

Step 2: Per-point xyz → 3D embed
  - Linear(3 → 64) + GELU
  - Output: E ∈ ℝ^(256 × 64)

Step 3: Global pooling
  - max-pool: e_max = E.max(dim=0)        ∈ ℝ^64
  - mean-pool: e_mean = E.mean(dim=0)     ∈ ℝ^64
  - global_feat = concat([e_max, e_mean]) ∈ ℝ^128

Step 4: prev_estimate fusion (optional)
  - if prev is not None:
      prev_flat = prev.positions.reshape(-1)  # [40, 3] → [120]
    else:
      prev_flat = zeros(120)
  - input_feat = concat([global_feat, prev_flat]) ∈ ℝ^248
```

#### §2.1.2 Backbone MLP

```
input_feat (248) → MLP {
    Linear(248 → 256) + GELU,
    Linear(256 → 256) + GELU,
    Linear(256 → 256) + GELU,
    Linear(256 → 256) + GELU,
    Linear(256 → 120),     # output
} → [120] → reshape [40, 3]
```

5 hidden layers × 256 hidden, GELU activation per parent memo §2.4.2.

#### §2.1.3 Output

`P̂_seg^(C) ∈ ℝ^(40×3)` — Stage D の initial seed として使用 (parent memo §2.4.4)。

#### §2.1.4 Param count breakdown (~52k、parent memo "~50k" abstract の concrete number)

| layer | shape | bias | params |
|-------|-------|------|--------|
| input_embed Linear(3, 64) | 3 × 64 = 192 | 64 | 256 |
| backbone Linear(248, 256) | 248 × 256 = 63,488 | 256 | 63,744 |
| backbone Linear(256, 256) ×3 | 256 × 256 × 3 = 196,608 | 256 × 3 = 768 | 197,376 |
| backbone Linear(256, 120) | 256 × 120 = 30,720 | 120 | 30,840 |
| **Total** |  |  | **292,216** |

**注**: parent memo "~50k params" は概数。具体 5×256 GELU MLP は ~290k params に膨らむ。**改訂提案**:
- Option A: hidden 128 に縮小 → ~75k params (parent memo の "~50k" に近い)
- Option B: 3 hidden layers × 128 → ~50k params (parent memo の文字通り)
- Option C: parent memo "~50k" は誤算、実際は ~290k で OK

Phase 2 design 推奨: **Option B (3 hidden × 128 GELU)** — parent memo の本来 intent を尊重、param efficiency 重視。具体 breakdown:

| layer | shape | bias | params |
|-------|-------|------|--------|
| input_embed Linear(3, 64) | 3 × 64 = 192 | 64 | 256 |
| backbone Linear(248, 128) | 248 × 128 = 31,744 | 128 | 31,872 |
| backbone Linear(128, 128) ×2 | 128 × 128 × 2 = 32,768 | 128 × 2 = 256 | 33,024 |
| backbone Linear(128, 120) | 128 × 120 = 15,360 | 120 | 15,480 |
| **Total (Option B)** |  |  | **80,632** |

依然 ~50k 超え。3 hidden × 96 で:

| layer | shape | bias | params |
|-------|-------|------|--------|
| input_embed Linear(3, 64) | 3 × 64 | 64 | 256 |
| backbone Linear(248, 96) | 248 × 96 | 96 | 23,904 |
| backbone Linear(96, 96) ×2 | 96 × 96 × 2 | 96 × 2 | 18,624 |
| backbone Linear(96, 120) | 96 × 120 | 120 | 11,640 |
| **Total** |  |  | **54,424** |

Phase 2 design **採択**: 3 hidden × 96 GELU、~54k params (parent memo "~50k" 整合)。Phase 3 train 時 OOM / capacity 観察で 128 / 256 に再調整候補。skeleton は param count を assertion で固定 (smoke test §6.2)。

### §2.2 Training pipeline (Phase 3 reference、本 Phase 2 では skeleton 接続点のみ定義)

#### §2.2.1 Dataset (parent memo §2.4.3)

| dataset | scenes | source | scenario |
|---------|--------|--------|----------|
| Random | 4,000 | newton state dump | 5-clip routing snapshots、Phase variety、cable shape variety |
| U-shape | 500 | scripted | mid-cable fold、varied fold positions × depth |
| S-shape | 500 | scripted | 2 inflection points、varied insertion depths × clip combinations |

各 scene per-frame data:
- merged cloud (`P_cloud`) shape [N_pts, 3]、N_pts ~1500-3000 (Stage A.3 output)
- finger_positions (left + right) [2, 3]
- prev_estimate (optional [40, 3])
- ground truth `P_seg^GT` [40, 3] (env state dump)

#### §2.2.2 Loss (parent memo §2.4.3 → concrete spec)

```
L_train = w_pos * MSE_pos(P̂_seg^(C), P_seg^GT) +
          w_tan * (1 - cos(tangent_pred, tangent_gt)).mean() +
          w_arc * arc_length_penalty(P̂_seg^(C))

  - w_pos = 1.0
  - w_tan = 0.3
  - w_arc = 0.5
  - tangent_pred[i] = (P̂_seg^(C)[i+1] - P̂_seg^(C)[i]).normalize()
  - tangent_gt[i] = (P_seg^GT[i+1] - P_seg^GT[i]).normalize()
  - arc_length_penalty = Σ (||P̂_seg^(C)[i+1] - P̂_seg^(C)[i]|| - 0.015)²
```

#### §2.2.3 Optimizer + schedule

- AdamW, lr=1e-3, weight_decay=1e-4
- Cosine LR schedule, T_max = 100 epochs, eta_min = 1e-5
- Batch size: 32 scenes (cloud N_pts variable、padded to max + mask)
- Train epoch budget: 100 epochs × 5k scenes / 32 batch ≈ 15,625 iter/epoch、~20h GPU @ cuda:2 deterministic kernel
- Mixed precision (torch.cuda.amp): forward fp16、backward fp32

#### §2.2.4 Checkpoint

- save: `checkpoints/dd_pinn_warm_start/<run_id>/{epoch:03d}.pt`
- best metric: val MSE_pos (1k held-out)
- format: PyTorch state_dict (torch.save) — `model.state_dict()` only、optimizer state は別 file (resume 用、本 design では explicitly skip)

#### §2.2.5 Inference latency target

- Per-call: < 2ms (parent memo §2.4.3 + §5.4 warn at >3ms)
- Batch handling: B=1 (per-scene call) or B=N_envs (parallel rollout)
- GPU: cuda:2 (4-process limit、parent memo GPU table)

### §2.3 File placement + class skeleton

#### §2.3.1 New file: `estimators/cable_state_dd_pinn.py` (~120 LoC)

```python
# SKELETON content (skeleton 起票時)

@dataclass
class DDPINNConfig:
    """Stage C DD-PINN architecture + train config."""
    n_anchor: int = 256                   # FPS sample count
    embed_dim: int = 64                   # per-point xyz embed
    hidden_dim: int = 96                  # backbone hidden width
    n_hidden_layers: int = 3              # backbone depth
    n_segments: int = 40                  # output segments
    use_prev_estimate: bool = True        # zero-fill if False or prev=None
    activation: str = "gelu"              # GELU only spec'd
    # Training-time fields (Phase 3 impl):
    train_lr: float = 1e-3
    train_weight_decay: float = 1e-4
    train_epochs: int = 100
    train_batch_size: int = 32
    train_amp: bool = True

class DDPINNModel(torch.nn.Module):
    """Stage C DD-PINN warm start MLP (~52k params)."""
    def __init__(self, config: DDPINNConfig | None = None) -> None: ...
    def forward(self, cloud: torch.Tensor, prev: CableState40 | None = None) -> torch.Tensor:
        """[N_pts, 3] cloud → [40, 3] warm-start. SKELETON — impl pending."""
        raise NotImplementedError(...)
    @torch.no_grad()
    def load_checkpoint(self, ckpt_path: str | Path) -> None: ...
    @property
    def param_count(self) -> int: ...     # for smoke test assertion

def farthest_point_sampling(points: torch.Tensor, n_samples: int) -> torch.Tensor:
    """FPS: greedy max-distance sampling. SKELETON — impl pending."""
    raise NotImplementedError(...)
```

#### §2.3.2 Integration with existing skeleton

`estimators/cable_state.py` 既存 `CableStateSolver._stage_c_dd_pinn(cloud, prev)` メソッドは **Phase 4 impl** で:

```python
def _stage_c_dd_pinn(self, cloud, prev):
    # Phase 4 impl pattern:
    return self._dd_pinn(cloud, prev)  # delegate to DDPINNModel
```

本 Phase 2 では `cable_state.py` は UNCHANGED、`DDPINNModel` skeleton のみ起票。

---

## §3 Stage D: Cosserat rod 7-term loss fitting

### §3.1 Energy formulation (parent memo §2.5.1)

```
L = w_1 L_pos + w_2 L_tan + w_3 L_bend + w_4 L_arc + w_5 L_id + w_6 L_temp + w_7 L_proj
```

| term | formula | semantics | weight (initial) |
|------|---------|-----------|------------------|
| L_pos | Σ_i min_{p∈NN_k(i)} ‖P̂_seg(i) - p‖² | per-segment fit、k=5 NN | w_1 = 1.0 |
| L_tan | Σ_i ‖(P̂_seg(i+1) - P̂_seg(i)) - (P̂_seg(i) - P̂_seg(i-1))‖² | tangent continuity | w_2 = 0.3 |
| L_bend | (EI/2) Σ_i ‖κ_i‖² | bend energy、EI=0.1 | w_3 = 0.5 |
| L_arc | Σ_i (‖P̂_seg(i+1) - P̂_seg(i)‖ - 0.015)² | arc-length monotonicity | w_4 = 1.0 |
| L_id | ‖P̂_seg(0) - p_grasp_end‖² + ‖P̂_seg(39) - p_far_end‖² | segment identity anchor | w_5 = 0.5 (grasp) / 0.0 (none) |
| L_temp | Σ_i ‖P̂_seg(i) - P̂_seg^{(t-1)}(i)‖² | temporal smoothness | w_6 = 0.2 (steady) / 0.0 (reset) |
| L_proj | Σ_i max(0, |z_seg(i) - z_depth_at_proj| - 5mm)² | depth-consistency hinge | w_7 = 0.3 |

### §3.2 Curvature κ_i (L_bend 内訳)

```
κ_i = ||P̂_seg(i+1) - 2*P̂_seg(i) + P̂_seg(i-1)|| / dt²
where dt² is normalized to seg-length squared (CABLE_SEG_LEN² = 0.000225)
```

- 端点 (i=0, i=39): one-sided difference または 0 padding (本 design 推奨: 0 padding for symmetry)
- 単位: 曲率 [m^-1] 概念量だが、normalized form で dimensionless residual として扱う

### §3.3 NN search for L_pos

```
For each segment i, find k=5 nearest cloud points within 10mm radius:
  d_ij = ||P̂_seg(i) - P_cloud(j)||
  NN_k(i) = argsort_k(d_ij)[:k]  # top-5 by distance
  L_pos contribution = (1/k) Σ d_ij² over j ∈ NN_k(i)
```

PyTorch impl: `torch.cdist(P̂_seg, P_cloud)` → `topk(k=5, dim=1, largest=False)`、O(40 × N_pts) per iter。

GPU optimization (Phase 5 candidate): KD-tree precompute + Warp kernel batched query → O(40 × log(N_pts))。

### §3.4 Optimizer + multi-restart strategy

#### §3.4.1 PyTorch L-BFGS first (本 Phase 2 推奨)

理由:
- autograd 完全 backward (7 term × NN search 全 differentiable in PyTorch)
- dev cost 圧縮 (Warp kernel 化は Phase 5 latency profile 経で defer)
- multi-restart 5 init + max_iter=200 で typical 30-50 iter 収束想定 (parent memo §2.5.3)

```python
# Phase 4 impl reference pattern:
optimizer = torch.optim.LBFGS(
    [seg],                     # seg ∈ ℝ^(40, 3) leaf tensor
    lr=1.0,
    max_iter=20,               # inner LBFGS iter (per outer step)
    tolerance_grad=1e-6,
    tolerance_change=1e-9,
    history_size=20,
    line_search_fn="strong_wolfe",
)

def closure():
    optimizer.zero_grad()
    loss = compute_total_loss(seg, cloud, prev, finger, weights)
    loss.backward()
    return loss

for outer_step in range(max_outer_steps):  # max_outer_steps = 10 → ~200 inner iter
    loss = optimizer.step(closure)
    if loss.item() < 1e-6 or outer_step >= max_outer_steps - 1:
        break
```

#### §3.4.2 Multi-restart (parent memo §2.5.2)

```python
best_seg = None
best_loss = inf
for restart in range(5):                     # cosserat_restart_count
    seg_init_perturbed = seg_init + torch.randn_like(seg_init) * 0.002  # σ=2mm
    seg_fitted, final_loss = run_lbfgs(seg_init_perturbed, cloud, prev, finger, weights)
    if final_loss < best_loss:
        best_loss = final_loss
        best_seg = seg_fitted
return best_seg
```

restart 0 は un-perturbed (original seg_init)、restart 1-4 は σ=2mm gaussian perturbation。

#### §3.4.3 Convergence + early stopping

- ``||∇L|| < 1e-6`` (LBFGS tolerance_grad)
- ``L < 1e-6`` (≈ 1mm² total residual、parent memo §2.5.2)
- ``max_iter == 200`` (hard cap)

### §3.5 Identity inversion check (parent memo §3.3、Stage D 内 1 pass refit)

```python
# After Stage D primary fit:
def verify_identity(seg_final, finger_positions, identity_inversion_delta_m=0.05):
    if finger_positions is None:
        return seg_final  # no anchor → skip check
    finger_avg = finger_positions.mean(dim=0)  # [3]
    d_grasp = torch.norm(seg_final[0] - finger_avg)
    d_far   = torch.norm(seg_final[-1] - finger_avg)
    if d_grasp > d_far + identity_inversion_delta_m:
        # Identity inversion suspected
        seg_reversed = torch.flip(seg_final, dims=[0])
        seg_refitted, _ = run_lbfgs(seg_reversed, cloud, prev, finger, weights)  # 1 re-fit pass
        return seg_refitted
    return seg_final
```

### §3.6 Latency budget (parent memo §2.5.3 + §5.3)

- Target: < 50ms total (Stage D portion ~30-40ms with warm start from Stage B/C)
- Typical PyTorch L-BFGS iter cost: ~1-2ms per inner iter on cuda:0
- 30-50 iter × 2ms = 60-100ms (warm start で減らす)
- 5-restart × 60ms = 300ms (Phase 5 で multi-restart parallel batch 化候補 → ~60ms)

Phase 5 latency profile 経 (Q5 worst-case benchmark):
- > 100ms total: Warp kernel 化 (CosseratWarpSolver、Phase 6 別 leaf)
- < 50ms: PyTorch L-BFGS 採択維持

### §3.7 File placement + class skeleton

#### §3.7.1 New file: `estimators/cable_state_cosserat.py` (~150 LoC)

```python
# SKELETON content

@dataclass
class CosseratLossWeights:
    """7-term Cosserat loss weights (parent memo §2.5.1)."""
    w_pos: float = 1.0
    w_tan: float = 0.3
    w_bend: float = 0.5
    w_arc: float = 1.0
    w_id_grasp: float = 0.5     # active when |finger - cable| < 20mm
    w_temp: float = 0.2          # active when prev available + not episode start
    w_proj: float = 0.3

@dataclass
class CosseratSolverConfig:
    weights: CosseratLossWeights = field(default_factory=CosseratLossWeights)
    max_iter: int = 200
    restart_count: int = 5
    restart_sigma_m: float = 0.002
    tolerance_grad: float = 1e-6
    tolerance_change: float = 1e-9
    nn_k: int = 5                 # L_pos NN count
    nn_radius_m: float = 0.010    # L_pos NN radius
    bend_ei: float = 0.1          # mirror task_config.CABLE_BEND_STIFFNESS
    seg_len_m: float = 0.015      # mirror task_config.CABLE_SEG_LEN
    proj_tolerance_m: float = 0.005  # L_proj 5mm hinge
    grasp_finger_distance_m: float = 0.020  # L_id 20mm threshold
    identity_inversion_delta_m: float = 0.050  # § 3.5 50mm threshold

class CosseratSolver:
    """Stage D Cosserat 7-term loss + L-BFGS multi-restart fitter."""
    def __init__(self, config: CosseratSolverConfig | None = None) -> None: ...
    def fit(
        self,
        seg_init: torch.Tensor,                # [40, 3] from Stage B/C
        cloud: torch.Tensor,                   # [N_pts, 3] Stage A.3 output
        prev: CableState40 | None = None,
        finger_positions: torch.Tensor | None = None,
    ) -> torch.Tensor:                          # [40, 3] refined
        """Multi-restart L-BFGS fit. SKELETON — impl pending."""
        raise NotImplementedError(...)
    def _compute_loss(
        self, seg, cloud, prev, finger, weights,
    ) -> torch.Tensor:
        """7-term loss closure. SKELETON — impl pending."""
        raise NotImplementedError(...)
    def _verify_identity(
        self, seg, finger_positions,
    ) -> torch.Tensor:
        """Identity inversion check + 1 refit pass. SKELETON — impl pending."""
        raise NotImplementedError(...)
```

---

## §4 Stage E: per-segment confidence calibration

### §4.1 Signal computation (parent memo §2.6.1)

| signal | computation | range | notes |
|--------|-------------|-------|-------|
| s_visibility | Σ_c 1[seg(i) projects into cam c FOV AND not occluded by depth] | {0, 1, 2, 3} | per-cam projection check + depth z-test |
| s_density | # cloud points within 10mm of seg(i) | 0-50 | cdist + radius_filter |
| s_residual | sigmoid(-‖seg(i) - nearest_cloud(i)‖ / scale) | (0, 1) | scale=0.005 (5mm) |
| s_curvature | sigmoid(-|κ_i - μ_κ| / σ_κ) | (0, 1) | μ_κ, σ_κ = scene-mean + std |
| s_temporal | sigmoid(-‖seg(i) - prev(i)‖ / τ) | (0, 1) | τ=0.005 (5mm) |

### §4.2 Aggregation (parent memo §2.6.2)

```
c_i = sigmoid(α_v * s_visibility(i) + α_d * s_density(i) + α_r * s_residual(i)
            + α_κ * s_curvature(i) + α_t * s_temporal(i) + β)
```

Coefficients `α, β` ∈ ℝ^6 calibrated post-train via:

```python
# Phase 4 impl pattern:
from sklearn.linear_model import LogisticRegression

X_val = stack([s_v, s_d, s_r, s_kappa, s_t]) shape [N_val × 40, 5]
y_val = (per_seg_error < threshold).astype(int) shape [N_val × 40]   # threshold=0.005m
clf = LogisticRegression(fit_intercept=True)
clf.fit(X_val, y_val)
alpha = clf.coef_[0]    # [5]
beta = clf.intercept_[0]  # scalar
```

### §4.3 ECE measurement (parent memo §2.6.2 + §5.3)

```python
def compute_ece(confidences, errors, threshold=0.005, n_bins=10):
    """Expected Calibration Error.

    ECE = Σ_b (|B_b| / N) * |acc(B_b) - conf(B_b)|
    where B_b = bin_b confidence range, acc = correct rate, conf = mean confidence.
    """
    correct = (errors < threshold).float()
    bin_edges = torch.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for b in range(n_bins):
        mask_b = (confidences >= bin_edges[b]) & (confidences < bin_edges[b+1])
        if mask_b.sum() > 0:
            acc_b = correct[mask_b].mean()
            conf_b = confidences[mask_b].mean()
            ece += (mask_b.sum() / len(confidences)) * abs(acc_b - conf_b)
    return ece.item()
```

Target: ECE < 5% (parent memo §5.3、Phase 4 で empirical 確認)。

### §4.4 Calibration sample size

- Train val split: 4k train (DD-PINN train 用) + 1k held-out for Stage E calibration
- 1k scenes × 40 segments = 40k (seg, error) pairs for logistic regression
- 5-fold cross-validation: 800 train + 200 val per fold
- ECE 観察: per-fold ECE → mean + std、target <5% mean

### §4.5 File placement + class skeleton

#### §4.5.1 New file: `estimators/cable_state_confidence.py` (~100 LoC)

```python
# SKELETON content

@dataclass
class ConfidenceSignals:
    """Per-segment 5 confidence signals."""
    s_visibility: torch.Tensor    # [40] in {0, 1, 2, 3}
    s_density: torch.Tensor       # [40] in [0, 50]
    s_residual: torch.Tensor      # [40] in (0, 1)
    s_curvature: torch.Tensor     # [40] in (0, 1)
    s_temporal: torch.Tensor      # [40] in (0, 1)

@dataclass
class ConfidenceCalibratorConfig:
    residual_scale_m: float = 0.005    # s_residual sigmoid scale
    temporal_scale_m: float = 0.005    # s_temporal sigmoid scale
    nn_radius_m: float = 0.010          # s_density radius
    n_cameras: int = 3                  # for s_visibility max value
    target_ece: float = 0.05            # ECE <5% target
    target_error_threshold_m: float = 0.005  # logistic regression label threshold

class ConfidenceCalibrator:
    """Stage E per-segment confidence calibration."""
    def __init__(self, config: ConfidenceCalibratorConfig | None = None) -> None: ...
    def compute_signals(
        self,
        seg: torch.Tensor,                       # [40, 3]
        cloud: torch.Tensor,                     # [N_pts, 3]
        prev: CableState40 | None = None,
        camera_poses: list[torch.Tensor] | None = None,
        camera_intrinsics: list[torch.Tensor] | None = None,
    ) -> ConfidenceSignals:
        """SKELETON — impl pending."""
        raise NotImplementedError(...)
    def aggregate(
        self,
        signals: ConfidenceSignals,
        coefficients: torch.Tensor,              # [5] α
        intercept: float,                        # β
    ) -> torch.Tensor:                            # [40] confidence
        """sigmoid(α·signals + β). SKELETON — impl pending."""
        raise NotImplementedError(...)

class LogisticCalibrator:
    """Post-train logistic regression for α, β fitting."""
    def fit(
        self,
        signals_list: list[ConfidenceSignals],
        per_seg_errors: list[torch.Tensor],
    ) -> tuple[torch.Tensor, float]:
        """SKELETON — impl pending."""
        raise NotImplementedError(...)

def compute_ece(
    confidences: torch.Tensor,       # [N]
    errors: torch.Tensor,            # [N]
    threshold_m: float = 0.005,
    n_bins: int = 10,
) -> float:
    """Expected Calibration Error. SKELETON — impl pending."""
    raise NotImplementedError(...)
```

---

## §5 Phase 1 → Phase 2 integration spec

### §5.1 Data flow

```
Phase 1 (existing impl):
  MultiCamCableStatePipeline.estimate(finger_positions, prev)
    → CableStatePhase1Result {
        seg_positions: [40, 3] NaN-fillable,
        bin_counts: [40] int,
        var_ratio: float,
        n_pts: int,
        fallback_reason: Optional[str],
        succeeded: bool,
      }

Phase 2 (本 design 起票、Phase 4 impl で接続):
  if Phase 1 result.succeeded:
    if result.var_ratio < 0.6:                        ← § 2.3.3 trigger
      seg_init = DDPINNModel.forward(cloud, prev)     ← Stage C
    else:
      seg_init = result.seg_positions                  ← Stage B output direct
    seg_init = nan_fill_zero(seg_init)                 ← NaN → zero (Stage C robust to zero anchor)
    seg_fitted = CosseratSolver.fit(seg_init, cloud, prev, finger)  ← Stage D
    seg_verified = CosseratSolver._verify_identity(seg_fitted, finger)  ← § 3.5
    signals = ConfidenceCalibrator.compute_signals(seg_verified, cloud, prev, cameras)
    confidences = ConfidenceCalibrator.aggregate(signals, alpha, beta)  ← Stage E
    return CableState40(positions=seg_verified, confidences=confidences, stage_diagnostics={...})
  else:
    # Stage A failure (n_pts < 800)
    return CableState40(positions=prev.positions if prev else zeros, confidences=zeros, stage_diagnostics={"fallback": result.fallback_reason})
```

### §5.2 NaN handling (parent memo §2.3.3 + 本 Phase 2 §1 OQ5)

Phase 1 `CableStatePhase1Result.seg_positions` は empty bin で NaN を含み得る。Phase 2 components の取り扱い:

| component | NaN handling |
|-----------|--------------|
| Stage C DD-PINN | `seg_init = nan_fill_zero(seg_positions)`、prev_estimate も zero-fill (Stage C は zero anchor を robust に処理する設計) |
| Stage D Cosserat L_pos | NN search 時に NaN segment は cloud 距離計算で NaN propagate → 該当 segment の loss contribution を skip (mask_nan = ~isnan(seg).any(dim=1))、L_arc + L_temp が NaN segment を周辺から interp の効果 |
| Stage D Cosserat L_arc / L_temp | NaN segment は周辺 (i±1) との distance / prev difference 計算で NaN、loss contribution skip。但し 連続 NaN 多数の場合 (例: 5+ 連続 NaN) は Stage C trigger 推奨 (Phase 5 で empirical 確認) |
| Stage E ConfidenceSignals | NaN segment は s_visibility=0, s_density=0, s_residual=0, s_curvature=0, s_temporal=0 (zero confidence) |

### §5.3 Integration into existing CableStateSolver (Phase 4 impl pattern、本 Phase 2 では reference のみ)

`estimators/cable_state.py` 既存 `CableStateSolver` は Phase 4 impl で 3 sub-modules を delegate するように extend:

```python
# Phase 4 impl pattern (本 Phase 2 では reference only):
class CableStateSolver:
    def __init__(
        self,
        dd_pinn: DDPINNModel | None = None,             # ← cable_state_dd_pinn.DDPINNModel
        cosserat: CosseratSolver | None = None,         # ← cable_state_cosserat.CosseratSolver
        confidence: ConfidenceCalibrator | None = None,  # ← cable_state_confidence.ConfidenceCalibrator
        config: CableStateSolverConfig | None = None,
    ) -> None: ...

    def __call__(self, cloud, prev=None, finger_positions=None) -> CableState40:
        # delegate to Phase 1 outputs ↓
        # (this method orchestrates Stage B → C/D → identity → E、existing skeleton fills in)
```

本 Phase 2 では `cable_state.py` UNCHANGED、Phase 4 impl 起票時に 3 sub-modules 経で fill in。

### §5.4 Backward compat (Phase 1 callers 影響なし)

- `MultiCamCableStatePipeline` (Phase 1) は UNCHANGED、SOMA Stage 1-3 caller (single-midpoint) keep working
- `CableStatePhase1Result` (Phase 1) は UNCHANGED、Phase 2 components が read-only consume
- `EstimatorInputs` (Phase 1 で freeze) は UNCHANGED
- `CableStateCameraManager` (Phase 1 で freeze) は UNCHANGED
- `CableStateSolver` 既存 skeleton (Phase 1 期 created) は本 Phase 2 で UNCHANGED、Phase 4 で extend

---

## §6 Test plan

### §6.1 Smoke test scope (本 Phase 2)

`tests/test_cable_state_phase2_skeleton.py` (~80 LoC):

| test | assertion |
|------|-----------|
| test_imports | 3 new modules import without error |
| test_dd_pinn_config_defaults | DDPINNConfig defaults match design memo §2.3.1 |
| test_dd_pinn_param_count | DDPINNModel().param_count is None (impl pending) OR fits ~50k-55k range when impl |
| test_cosserat_weights_default | CosseratLossWeights default values match parent memo §2.5.1 (w_pos=1.0, w_tan=0.3, w_bend=0.5, w_arc=1.0, w_id_grasp=0.5, w_temp=0.2, w_proj=0.3) |
| test_cosserat_config_defaults | CosseratSolverConfig defaults match design memo §3.7.1 |
| test_confidence_signals_shape | ConfidenceSignals fields all torch.Tensor shape [40] |
| test_confidence_config_defaults | ConfidenceCalibratorConfig defaults match design memo §4.5.1 |
| test_dd_pinn_forward_raises | DDPINNModel().forward(cloud) raises NotImplementedError (skeleton phase) |
| test_cosserat_fit_raises | CosseratSolver().fit(seg, cloud) raises NotImplementedError |
| test_confidence_compute_signals_raises | ConfidenceCalibrator().compute_signals(seg, cloud) raises NotImplementedError |
| test_compute_ece_raises | compute_ece(...) raises NotImplementedError |
| test_logistic_calibrator_fit_raises | LogisticCalibrator().fit(...) raises NotImplementedError |
| test_no_newton_import | grep test (or AST walk) on 3 new files asserts no `import newton` / `import thread_isaac_lab.envs` |

### §6.2 Phase 4 impl 時 unit test scope (reference)

| test | assertion |
|------|-----------|
| test_dd_pinn_param_count_concrete | param_count ∈ [50_000, 60_000] (Option B 3×96 GELU 範囲) |
| test_dd_pinn_forward_shape | forward(cloud[1500, 3]).shape == [40, 3] |
| test_dd_pinn_prev_optional | forward(cloud, prev=None) と forward(cloud, prev=valid) 両 path shape 同 |
| test_cosserat_fit_synthetic | scripted cable shape (straight + L-shape + U-shape) で seg_fitted MSE < 1mm |
| test_cosserat_identity_inversion | reversed seg_init → verify_identity flips back → MSE < 5mm |
| test_confidence_signals_density | known cloud + seg → s_density count match expected |
| test_confidence_aggregate_shape | aggregate(signals, alpha=ones[5], beta=0).shape == [40] |
| test_compute_ece_perfectly_calibrated | confidences == correctness → ECE = 0 |

### §6.3 Phase 5 integration test scope (Q5 benchmark)

- 10 U-shape + 10 S-shape worst-case scenes 全件 mean<5mm (parent memo §5.3 PASS criteria)
- N=100 random scenes mean(ē) < 5mm AND mean(e_p95) < 10mm
- Identity inversion rate 0/120
- ECE < 5%
- Latency p95 < 50ms

---

## §7 Risk register (Phase 2 specific)

| ID | risk | severity | likelihood | mitigation |
|----|------|----------|------------|------------|
| P2-R1 | DD-PINN param count parent memo "~50k" との乖離 で OOM / capacity 不足 | MED | MED | Phase 2 design で 3×96 GELU = ~54k 採択、Phase 3 train 直前 assertion で確認。Phase 3 で OOM if hidden_dim=128/256 にスケールアップ |
| P2-R2 | Phase 4 impl 時 PyTorch L-BFGS が latency 50ms 超過 | MED | MED | Phase 2 design で warm start + 5-restart parallel batch 経で 30-60ms 想定、超過時 Warp kernel 化 (Phase 6 別 leaf) |
| P2-R3 | Stage E ECE <5% target が val 1k 不足 で未達 | MED | LOW | Phase 4 で 5-fold CV + sample size 倍増 (1k → 2k) 候補、feature engineering (s_density 重み増) も candidate |
| P2-R4 | NaN segment が Stage D L_pos NN search で gradient explosion | HIGH | LOW | Phase 2 design §5.2 で NaN handling spec 明示、Phase 4 impl で mask_nan 必須、smoke test で NaN reach 確認 |
| P2-R5 | 既存 cable_state.py CableStateSolver と新 3 modules の重複 (混乱 risk) | MED | MED | Phase 2 design §5.3 で integration spec 明示、Phase 4 impl で delegate pattern locking、本 Phase 2 では cable_state.py UNCHANGED |
| P2-R6 | R6 boundary 違反 (新 modules で newton import 紛れ込み) | HIGH | LOW | Phase 2 design 段階で `thread_isaac_lab.estimators.*` + `torch` only import discipline、Phase 4 impl 時に test_estimator_module_boundary.py 拡張 |
| P2-R7 | 5k labeled dataset (4k random + 500 U + 500 S) generation infrastructure が T-Vision-DR-Impl-Phase0 で未整備 | EXTERNAL | MED | Phase 3 起票 trigger に dataset readiness 含む、T-Vision-DR-Impl-Phase0-PrepDesign 進捗 monitor |
| P2-R8 | Phase 3 train 20h GPU 時間 cuda:2 占有 競合 | EXTERNAL | MED | Phase 3 起票時に GPU schedule 確認 (4-process limit) |
| P2-R9 | Stage D multi-restart 5x が parallel 化されず latency 5x 増 | MED | MED | Phase 4 impl で torch.vmap or batched dim で parallel 化、PyTorch native 不可なら Phase 6 で Warp kernel 化 |
| P2-R10 | Identity inversion check の anchor source priority (parent memo §3.5) で finger_positions absent 時 fallback 不安定 | MED | MED | Phase 2 design §3.5 で Tier 1 (finger) / Tier 2 (prev) / Tier 3 (default t_min) 明示、Phase 4 impl で Tier fallback chain 実装 |

---

## §8 Open questions (Phase 3+ revision trigger)

| OQ | topic | Phase 2 disposition | trigger for revision |
|----|-------|---------------------|----------------------|
| OQ-P2-1 | DD-PINN hidden_dim 96 vs 128 vs 256 | 96 (~54k params、parent memo "~50k" 整合) | Phase 3 train val MSE 経で OOM / underfit 観察 |
| OQ-P2-2 | DD-PINN n_anchor 256 vs 128 | 256 (parent memo §2.4.2 default) | Phase 3 inference latency >2ms 経で 128 化 |
| OQ-P2-3 | Stage D PyTorch L-BFGS vs Warp kernel | PyTorch first (本 Phase 2)、Warp は Phase 6 latency profile 経 | Q5 latency p95 >50ms 経で Warp 化決定 |
| OQ-P2-4 | Stage D multi-restart parallel vs sequential | Phase 4 で parallel batched 試行、PyTorch native 不可なら sequential | Phase 4 latency profile 経 |
| OQ-P2-5 | Stage E logistic regression sample size 1k val | 1k 初期、5-fold CV | Phase 4 ECE >5% 経で 2k 化 |
| OQ-P2-6 | NaN segment 連続 5+ 時の Stage C trigger | Phase 2 では skip (parent memo §2.3.3 row 3 で Stage D infill)、Phase 5 で empirical 確認 | Phase 5 worst-case で連続 NaN 観察 経 |
| OQ-P2-7 | DD-PINN train/val split (4k/1k vs 4.5k/500) | 4k train + 500 val + 500 calib (Stage E 用) | Phase 3 val MSE 安定性 経 |
| OQ-P2-8 | Stage E s_visibility cam pose の Phase 4 接続 | Phase 4 で `EstimatorInputs.wrist_camera_pose_l/r/overhead_camera_pose` 経 inject | Phase 4 impl spec |

---

## §9 Cross-references

### §9.1 Internal vault

- **Parent design memo (本 memo の base)**: `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md` (769 行、approved 2026-05-03)
- **Sibling Phase 1 state**: `thread_isaac_lab/thread-vault/T-Vision-CableState-Impl-Phase-1/state.md` (COMPLETE 2026-05-04T03:50)
- **Parent NEST node**: `thread_isaac_lab/thread-vault/T-Vision-CableState/state.md`
- **CC4 v3.2 base spec**: `thread_isaac_lab/thread-vault/07-Design/PoseEstimation-Design-v3.2.md` §H Estimator boundary、§5.4 Stage 3a expand
- **R6 boundary tests**: `thread_isaac_lab/tests/test_estimator_input_boundary.py` (Appendix D 名前 grep) + `tests/test_estimator_module_boundary.py` (`estimators/core/` AST lint)

### §9.2 Code references

- `thread_isaac_lab/configs/task_config.py:70-75` (CABLE_SEGMENTS=40, CABLE_SEG_LEN=0.015, CABLE_BEND_STIFFNESS=0.1) — TOUCH FORBIDDEN、新 3 modules で private constant mirror
- `thread_isaac_lab/models/vision_pipeline.py` (Phase 1 完成 `MultiCamCableStatePipeline` + `CableStatePhase1Result`、L406-727) — TOUCH FORBIDDEN、Phase 2 components が read-only consume
- `thread_isaac_lab/envs/wrist_camera_manager.py` (Phase 1 完成 `CableStateCameraManager`、overhead world-fixed cam) — TOUCH FORBIDDEN
- `thread_isaac_lab/estimators/types.py` (Phase 1 freeze `CableState40` + `EstimatorInputs` Phase 2 fields) — TOUCH FORBIDDEN
- `thread_isaac_lab/estimators/cable_state.py` (既存 `CableStateSolver` skeleton) — 本 Phase 2 で UNCHANGED、Phase 4 impl で extend
- `thread_isaac_lab/estimators/aggregator.py`、`thread_isaac_lab/estimators/input_adapter.py` — Phase 2 boundary 範囲外、Phase 4 で extend candidate
- 新 3 modules (本 Phase 2 起票):
  - `thread_isaac_lab/estimators/cable_state_dd_pinn.py`
  - `thread_isaac_lab/estimators/cable_state_cosserat.py`
  - `thread_isaac_lab/estimators/cable_state_confidence.py`

### §9.3 Sister leaves & downstream

- **T-Vision-CableState** (parent umbrella): design APPROVED 2026-05-03 + impl Phase 1 COMPLETE
- **T-Vision-Pose** (sister precedent for Stage A-B substrate)
- **T-Vision-DR** (sister、shared dataset re-render asset、Tier 0 ~10h GPU、Phase 3 dataset prerequisite cascade)
- **T-Vision-Fusion** (downstream consumer、cable_state 120D obs 統合、L1.A.4 = Phase 5-4 G8)

### §9.4 Future Phase 3-5 trigger spec

- Phase 3 (Stage C train、別 NEST node `T-Vision-CableState-Impl-Phase-3-Stage-C-Train`):
  - 5k labeled scenes generation (T-Vision-DR-Impl-Phase0 cascade)
  - ~20h GPU @ cuda:2 deterministic kernel
  - DD-PINN checkpoint 生成
- Phase 4 (Stage D Cosserat impl + Stage E ECE calibration、別 NEST node `T-Vision-CableState-Impl-Phase-4-Stage-DE`):
  - PyTorch L-BFGS impl + multi-restart + identity inversion check
  - ConfidenceCalibrator + LogisticCalibrator + compute_ece impl
  - 1k val held-out で post-train calibration
  - cable_state.py CableStateSolver delegate 接続
- Phase 5 (Q5 worst-case benchmark、別 NEST node `T-Vision-CableState-Impl-Phase-5-Q5-Bench`):
  - 10 U + 10 S scripted scene generation
  - N=100 random + worst-case full benchmark execution
  - Identity inversion 0% verify
  - ECE <5% verify
  - Latency p95 <50ms verify
  - per-stage diagnostics report

---

## §10 Status

- **Created:** 2026-05-04T03:55:00 (T-Vision-CableState-Impl-Phase2-DDPiNN-Cosserat-Design-CC sub-session)
- **Phase:** design + skeleton (impl + train pending、Phase 3-5 別 NEST node)
- **Author:** T-Vision-CableState-Impl-Phase2-DDPiNN-Cosserat-Design-CC (sub-agent of T-ROOT-COORD#s11)
- **Permissions:** 06-Knowledge は CC Create/Update 可 (Vault Write Permissions)
- **Authority:** L0 Rs proxy approve (`feedback_autonomous_full_authority_2026-05-03` 3-step expansion)
- **Next steps (Phase 3 trigger):**
  - 本 Phase 2 design + skeleton COMPLETE
  - 5k labeled dataset generation infrastructure ready (T-Vision-DR-Impl-Phase0 cascade)
  - cuda:2 ~20h GPU schedule 確認
  - Rs §3.1 #4 起動承認

---

## §11 Output format compliance (CLAUDE.md §運用)

| 区分 | 主張 | 根拠（出典） |
|------|------|-------------|
| 事実 | parent memo §2.4 = DD-PINN warm start spec 256 anchor + 5×256 GELU + 50k params | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md:217-238` |
| 事実 | parent memo §2.5 = Cosserat 7-term loss spec + L-BFGS optimizer + 5-restart σ=2mm | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md:243-279` |
| 事実 | parent memo §2.6 = Stage E 5 signals + sigmoid aggregation + ECE <5% target | `thread_isaac_lab/thread-vault/06-Knowledge/LL-Vision-CableState-Design.md:283-307` |
| 事実 | Phase 1 完成 `MultiCamCableStatePipeline.estimate()` returns `CableStatePhase1Result` with seg_positions [40,3] NaN-fillable + var_ratio + bin_counts | `thread_isaac_lab/models/vision_pipeline.py:428-696` (Phase 1 impl COMPLETE 2026-05-04T03:50) |
| 事実 | 既存 `CableStateSolver` skeleton (382 LoC) at `estimators/cable_state.py` with `_stage_c/d/e` methods raising NotImplementedError | `thread_isaac_lab/estimators/cable_state.py:136-345` |
| 事実 | CABLE_SEGMENTS=40, CABLE_SEG_LEN=0.015, CABLE_BEND_STIFFNESS=0.1 = task_config.py SSOT | `thread_isaac_lab/configs/task_config.py:70-75` (mirror constants in 新 modules で R6 自主遵守) |
| 推測 | DD-PINN 3×96 GELU で ~54k params が parent memo "~50k" abstract に整合 | parent memo は abstract、5×256 = 290k 過剰 → 3×96 = 54k で param efficiency + capacity 平衡。Phase 3 train 経で empirical 確認 |
| 推測 | PyTorch L-BFGS first で latency 50ms 達成可能 (warm start 経で 30-50 iter 収束想定) | parent memo §2.5.3 "warm start で 30-50 iter 収束 → 5-10ms" 引用、5-restart × 5-10ms = 25-50ms。Phase 5 profile 経で empirical 確認 |
| 推測 | Stage E ECE <5% target は val 1k で達成可能 | logistic regression 5 features × 1k sample × 40 segments = 40k pair で十分。well-studied calibration technique。Phase 4 で empirical 確認 |
| 推測 | Phase 1 NaN handling spec (本 memo §5.2) で Stage C/D/E NaN propagation 防止可能 | mask_nan + zero-fill anchor + L_arc/L_temp interp で連続 NaN <5 segments まで頑健。連続 NaN 多発時 (>5) は Stage C trigger 推奨。Phase 5 で empirical 確認 |
