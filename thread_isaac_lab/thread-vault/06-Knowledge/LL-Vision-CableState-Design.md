---
title: Cable State Estimation Design (40 segments, < 5mm error)
created: '2026-05-03T18:00:00+09:00'
tags:
  - knowledge
  - vision
  - cable-state
  - phase-5-4
  - design-reference
status: approved (Rs batch approve 2026-05-03 T-ROOT-COORD#s11) — impl spawn ready (CC-L1A-Cable-State-Impl 別 task 起票候補、state.md §4 trigger)
node_id: T-Vision-CableState
session: T-Vision-CableState-Design-CC
doc_class: design-surface
---

# LL-Vision-CableState-Design

> T-Vision-CableState (L1.A.2) の implementation-ready design memo。40 segment cable shape の per-segment 3D position estimation を target metric (mean<5mm AND p95<10mm on N=100 + 10 U-shape + 10 S-shape worst-case) で達成する 5-stage pipeline (Hybrid PCA + Cosserat) + topology preservation + benchmark 仕様を定義。
>
> **scope:** design only。impl + train は別 task scope (state.md §4 Active rule + L1.A 9 別 task 起票候補参照)。
> **base:** L1.A design memo §3 (`memory/project_l1a_vision_design_complete_2026-04-27.md`)、CC4 v3.2 §H + §5.4、EXP-046 PCA-center 3.92mm precedent (single-midpoint scope)。
> **boundary:** R6 input-boundary (CC4 v3.2 Appendix D + H) を遵守、estimator core は env / newton state を import しない。

---

## §0 Executive summary

- **target:** 40 segments × 15mm = 600mm cable の per-segment 3D position 誤差 mean<5mm AND p95<10mm @ N=100 random clip routing scenes、加えて 10 U-shape + 10 S-shape worst-case scenes 全件 mean threshold compliant
- **architecture:** 5-stage pipeline (Hybrid PCA + Cosserat、design memo §3.4 推奨)
  - Stage A: 多 camera mask + depth back-projection → 3D point cloud
  - Stage B: PCA principal axis + 40-bin arc-length discretization (initial seed)
  - Stage C: DD-PINN warm start (~50k params、worst-case rescue)
  - Stage D: Cosserat rod 7-term loss fitting (Warp kernel L-BFGS)
  - Stage E: per-segment confidence calibration
- **topology preservation:** 4-layer defense (arc-length monotonicity + segment identity anchor + temporal smoothness + bend regularization)
- **camera coverage:** 3-cam (extend current 2-cam wrist L/R + 1× world-fixed overhead) を推奨、EXP-046 precedent (single-cam Y-bias 80mm vs 3-cam merged 3.92mm) で根拠
- **benchmark:** N=100 random + 10 U-shape + 10 S-shape held-out (Q5 gate)、per-stage diagnostics で failure 帰属可能

---

## §1 Goal & scope

### §1.1 Target metric (state.md §1 直引き)

| dataset | sample size | mean(ē) gate | mean(e_p95) gate | per-scene gate |
|---------|-------------|--------------|-------------------|-----------------|
| Random clip routing snapshots | N=100 | < 5mm | < 10mm | (aggregate) |
| U-shape worst-case | 10 | < 5mm (mean over 10) | — | 全 10 件 mean<5mm 個別 compliant |
| S-shape worst-case | 10 | < 5mm (mean over 10) | — | 全 10 件 mean<5mm 個別 compliant |

- ē = scene-mean error = (1/40) Σ_i ||P̂_seg(i) - P_seg^GT(i)||₂
- e_p95 = 95th percentile of {e_i} per scene
- eval mode: deterministic (CC4 v3.2 §10、cuda:2 deterministic kernel + fixed seed)

### §1.2 In-scope (本 design)

1. Cable segment detection (mask, ordering, identity anchor)
2. 3D back-projection (multi-camera fusion, point cloud merge)
3. Topology preservation (arc-length, segment identity, bend regularization)
4. Benchmark spec (N=100 + worst-case + per-stage diagnostics)
5. Module boundary integration with CC4 v3.2 PoseEstimatorCore (§H)

### §1.3 Out-of-scope

- impl + train (別 task `CC-L1A-Cable-State-Impl` 起票候補、state.md §4 trigger)
- 04-Specs SSOT update (Rs専権、Vault Write Permissions)
- Real-hardware deployment (T-Vision-DR Tier 2 OUT-OF-SCOPE per umbrella state.md)
- Stage A.1 mask の MVP-0B v2 fine-tune (T-Vision-Pose 範囲)

### §1.4 Existing assets (CHECK 結果、grep 証拠 pin)

| Asset | Path | Status | Reuse / Extend |
|-------|------|--------|-----------------|
| HSV cable mask + PCA-center pipeline | `thread_isaac_lab/models/vision_pipeline.py` (264 LoC) | DONE (single-midpoint) | extend to 40-bin discretization |
| Wrist camera manager (L/R, 128² FOV 45°) | `thread_isaac_lab/envs/wrist_camera_manager.py` (~210 LoC) | DONE | extend → CableStateCameraManager (+overhead) |
| MVP-0A pose estimator core (Phase 1 narrow) | `thread_isaac_lab/estimators/core/pose_estimator_core.py` | DONE (Stage 0+1) | extend to Stage 2 + Stage 3a (本 design 対象) |
| Estimator inputs / boundary types | `thread_isaac_lab/estimators/types.py` | DONE | extend EstimatorInputs (+rgb_oh, depth_oh) |
| Cable physical params | `thread_isaac_lab/configs/task_config.py:70-75` | DONE (SSOT) | reuse (CABLE_SEGMENTS=40, CABLE_SEG_LEN=0.015, CABLE_BEND_STIFFNESS=0.1) |
| EXP-046 PCA-center baseline | `thread-vault/05-Thinking/Experiment Log.md` L1673-1686 | DONE (3.92mm single-midpoint, 1635 merged pts) | precedent for multi-cam fusion |

### §1.5 SOMA / chain math context

- L0: 5-clip routing **vision-based** 95% chain target
- L1.A.2 leaf: 40-segment cable state estimation (本 design)
- T-Vision-Fusion downstream: cable state 120D (40×3) を obs に統合 (CC4 v3.2 §6.4)、Late Fusion (sub-task 1)
- chain feasibility: per-skill 86% × WM-retry × 3 → 99.7% chain → L0 95% achievable (NEST 起票時 chain math 経)

---

## §2 Pipeline architecture (Stage A-E)

### §2.1 Overview diagram

```
Stage A: Multi-cam mask + depth → 3D point cloud
  ↓ merged P ∈ ℝ^(N_pts × 3)
Stage B: PCA principal axis + 40-bin arc-length discretization
  ↓ P̂_seg^(0) ∈ ℝ^(40×3) + var_ratio
  ┌─ var_ratio ≥ 0.6 (random scene) ──→ Stage D
  └─ var_ratio < 0.6 (U/S worst-case) ──→ Stage C
Stage C: DD-PINN warm start (~50k params MLP)
  ↓ P̂_seg^(C) ∈ ℝ^(40×3)
Stage D: Cosserat 7-term loss fitting (Warp + L-BFGS)
  ↓ P̂_seg ∈ ℝ^(40×3)
Stage E: per-segment confidence calibration
  ↓ output: P̂_seg + c ∈ ℝ^(40)
```

### §2.2 Stage A: Multi-camera mask + depth → 3D point cloud

#### §2.2.1 Camera coverage spec

3-cam configuration:

| cam | mount | resolution | FOV | pose source |
|-----|-------|------------|-----|--------------|
| wrist_L | body[6] (L hand) | 128² | 45° | `body_q[wrist_L]` (robot-measurable, R6 OK) |
| wrist_R | body[FRANKA_NUM_JOINTS+6] (R hand) | 128² | 45° | `body_q[wrist_R]` (R6 OK) |
| overhead | world-fixed | 256² | 60° | static pose (z=1.6m, look-at table center) |

**Why 3-cam (not 2):** EXP-046 precedent で single front-cam の Y-direction bias = 80mm error、3-cam merged で 3.92mm achievement。Newton VBD 現状 2-cam wrist-only では coverage 不足 (両 wrist が cable の同じ section を見るため lateral coverage 欠落)。Overhead cam で全体長軸 coverage 確保。

**Alternative (2-cam fallback):** overhead 不可の場合、L_temp temporal accumulation で多 frame fusion を実装 → 但し dynamic scene で error 拡大する risk あり。recommendation: implement 3-cam from start。

#### §2.2.2 Stage A.1: Cable mask

| variant | input | output | use case |
|---------|-------|--------|---------|
| HSV (existing) | RGB → HSV [20-40, 25-255, 150-255] | binary mask | Phase 1 baseline、sim only |
| 9-class semantic seg | RGB-D → CC4 v3.2 LightUNet | class probability | MVP-0B v2 ready 後 canonical |

- HSV: A6b 実証済 IoU=0.93 (SimEnv 静的シーン)、closing only (1px cable 保護)
- 9-class: MVP-0B v2 で R-side mIoU 0.248 → ≥0.85 fine-tune 後 swap
- Stage A.1 boundary: mask 出力のみ、後段 Stage A.2 が depth と組み合わせ
- Tier 0 DR (T-Vision-DR D1-D5) 対応で sim train、real transfer 可

#### §2.2.3 Stage A.2: Per-camera depth back-projection

```
For each camera c ∈ {wrist_L, wrist_R, overhead}:
  1. ys, xs = nonzero(mask_c > 127)
  2. depths = depth_c[ys, xs]; valid = isfinite(depths) & (0 < depths < 100)
  3. Inverse pinhole projection:
     x_cam = (xs - cx) * depths / fx
     y_cam = (ys - cy) * depths / fy
     z_cam = depths
  4. Camera → world transform:
     R_c = quat_to_matrix(cam_quat_c)
     p_world = R_c @ p_cam.T + cam_pos_c
  5. Output: P_c ∈ ℝ^(N_c × 3)
```

- 既存 `vision_pipeline._backproject_mask` を Warp kernel 化 (CPU→GPU、~10x speedup)
- Per-cam intrinsic K = `wrist_camera_manager.intrinsic_matrices` (3×3 pinhole) ※ overhead は新規 spec

#### §2.2.4 Stage A.3: Multi-cam fusion + voxel downsample

```
1. P = concat(P_wrist_L, P_wrist_R, P_overhead) ∈ ℝ^(N_total × 3)
2. Voxel downsample at ε=2mm (avoid stacking-density bias):
   For each point, hash to voxel center; keep one representative per voxel
3. Output: merged P ∈ ℝ^(N_pts × 3), expected N_pts ~1500-3000
```

- 2mm voxel size justified: cable radius=4mm、segment length=15mm、2mm voxel が形状情報保持 + メモリ効率
- gate (Stage A failure 検出): N_pts < 800 → fallback to previous_estimate (FAIL_CLOSED 相当)

### §2.3 Stage B: PCA initial centerline + 40-bin discretization

#### §2.3.1 Stage B.1: PCA principal axis

```
1. centroid = P.mean(axis=0)
2. centered = P - centroid
3. SVD: _, s, Vt = svd(centered, full_matrices=False)
4. d = Vt[0]  # 1st principal direction ∈ ℝ³
5. var_ratio = s[0]² / s.sum()²  # how much variance in 1st axis
```

#### §2.3.2 Stage B.2: 40-bin arc-length discretization

```
1. Project each point onto d: t_i = (P_i - centroid) · d ∈ ℝ
2. (t_min, t_max) = projection extremes
3. L_est = t_max - t_min  # estimated cable length, expect ~0.6m
4. Bin width: w = L_est / 40
5. For each bin k ∈ {0..39}:
     mask_k = (t_min + k*w ≤ t_i < t_min + (k+1)*w)
     P̂_seg^(0)(k) = mean(P_i where mask_k holds)
6. Output: P̂_seg^(0) ∈ ℝ^(40×3)
```

**Anchoring orientation (P_seg(0) vs P_seg(39)):**
- Use gripper finger position to determine which end is index 0
- if grasp active: P̂_seg^(0) where ||P̂_seg^(0)(0) - finger_pos|| < ||P̂_seg^(0)(39) - finger_pos|| → keep order; else flip
- if no grasp: use previous_estimate to determine handedness; else default to t_min as index 0

#### §2.3.3 Stage B.3: Validity gate

| condition | action |
|-----------|--------|
| var_ratio < 0.6 | Stage B fail → trigger Stage C |
| L_est < 0.4m or > 0.8m (vs nominal 0.6m) | Stage B fail → Stage C |
| any bin empty (mask_k count < 5 points) | mark P̂_seg^(0)(k) for Stage D infill via temporal interp |

**Why 0.6 threshold:** EXP-046 で merged cloud は var_ratio≈0.85 (near-straight)。U-shape では 2-mode → var_ratio drops to ~0.4-0.5。S-shape では更に下。0.6 threshold で worst-case detect。

### §2.4 Stage C: DD-PINN warm start (worst-case rescue)

#### §2.4.1 Trigger

- Stage B var_ratio < 0.6 (multi-mode point cloud)
- Stage D non-convergence detected (loss > 5mm tail after 50 iter)
- Identity inversion suspected (§3.3 post-fit check fails)

#### §2.4.2 Architecture

```
Input encoder:
  - 256 anchor points sampled from P (farthest point sampling for diversity)
  - per-point xyz → 3D embedding (3 → 64)
  - global pool (max + mean)
  - + previous_estimate (40×3 → 120) if available, else zeros
Concat → MLP (5 layers × 256 hidden, GELU activation) → 40×3 output
Total params: ~50k
```

#### §2.4.3 Training spec

- dataset: 5k labeled scenes from newton state (40×3 ground truth via env state dump)
  - 4k random clip routing snapshots
  - 500 U-shape (scripted env scenarios with cable folding)
  - 500 S-shape (scripted env scenarios with 2 inflection points)
- loss: position MSE + tangent direction cosine + arc-length monotonicity penalty
- train: ~20h GPU @ cuda:2、Adam optimizer、cosine LR schedule
- inference latency target: <2ms per call (small MLP + GPU)

#### §2.4.4 Output

- P̂_seg^(C) ∈ ℝ^(40×3)、Stage D の initial point として使用

### §2.5 Stage D: Cosserat rod 7-term loss fitting

#### §2.5.1 Energy formulation

```
L = w_1 L_pos + w_2 L_tan + w_3 L_bend + w_4 L_arc + w_5 L_id + w_6 L_temp + w_7 L_proj
```

| term | formula | semantics | weight (initial) |
|------|---------|-----------|------------------|
| L_pos | Σ_i min_{p∈P_neighbor(i)} ‖P̂_seg(i) - p‖² | per-segment fit to nearest cloud points (k=5 NN) | w_1 = 1.0 |
| L_tan | Σ_i ‖(P̂_seg(i+1) - P̂_seg(i)) - (P̂_seg(i) - P̂_seg(i-1))‖² | tangent continuity (1st derivative smooth) | w_2 = 0.3 |
| L_bend | (EI/2) Σ_i ‖κ_i‖² where κ_i = curvature | bend energy (Cosserat rod, EI=0.1 from task_config.py) | w_3 = 0.5 |
| L_arc | Σ_i (‖P̂_seg(i+1) - P̂_seg(i)‖ - 0.015)² | arc-length monotonicity (CABLE_SEG_LEN=15mm) | w_4 = 1.0 |
| L_id | ‖P̂_seg(0) - p_grasp_end‖² + ‖P̂_seg(39) - p_far_end‖² | segment identity anchor (grasp finger / far end) | w_5 = 0.5 (when grasped) / 0.0 (else) |
| L_temp | Σ_i ‖P̂_seg(i) - P̂_seg^{(t-1)}(i)‖² | temporal smoothness (only when prev_estimate available) | w_6 = 0.2 (steady state) / 0.0 (episode start) |
| L_proj | Σ_i max(0, |z_seg(i) - z_depth_at_proj| - 5mm)² | projection feasibility (depth-consistency hinge) | w_7 = 0.3 |

**Why these weights (initial):**
- w_1=1.0: data fitting primary
- w_2=0.3, w_3=0.5: smoothness regularization (under-fitting → noise; over-fitting → ignore curvature)
- w_4=1.0: arc-length critical for segment identity
- w_5: conditional (grasp = strong anchor; no grasp = soft constraint)
- w_6: temporal soft constraint (steady) / disabled (reset)
- w_7=0.3: depth consistency mild (depth noise tolerated up to 5mm)
- final tuning via Q5 worst-case benchmark

#### §2.5.2 Optimizer

- GPU L-BFGS (Warp kernel) or PyTorch Adam with line search
- max iterations: 200 (typical convergence ~50-100)
- convergence: ‖∇L‖ < 1e-6 OR L < 1mm² OR iter == 200
- multi-restart: 5 init perturbations (gaussian noise σ=2mm) → keep best L

#### §2.5.3 Latency budget

- typical iteration: ~0.1ms per Warp kernel iter on cuda:0
- 100 iter × 1.0ms safety = 100ms? — too slow for 50ms target
- mitigation: warm start (Stage B/C) reduces iter count to ~30-50, total ~5-10ms
- final check: profile against 50ms latency goal in Q5 integration test

### §2.6 Stage E: Per-segment confidence calibration

#### §2.6.1 Confidence signals (per segment i)

| signal | computation | typical range |
|--------|-------------|---------------|
| s_visibility | # cams that see (project + non-occluded) P̂_seg(i) | {0, 1, 2, 3} |
| s_density | # nearest cloud points within 10mm of P̂_seg(i) | 0-50 |
| s_residual | ‖P̂_seg(i) - nearest_cloud_pt(i)‖₂ inverse | 0-1 (sigmoid of -residual/scale) |
| s_curvature | local bend κ_i deviation from neighbor mean | 0-1 (sigmoid of -|κ_i - μ_κ|/σ_κ) |
| s_temporal | per-segment Δ from prev_estimate, inverted | 0-1 |

#### §2.6.2 Aggregation

```
c_i = sigmoid(α_v * s_visibility + α_d * s_density + α_r * s_residual + α_κ * s_curvature + α_t * s_temporal + β)
```

- coefficients α, β: calibrated post-train via held-out val set (logistic regression)
- target ECE (expected calibration error) < 5%

#### §2.6.3 Output

- P̂_seg ∈ ℝ^(40×3) + c ∈ ℝ^(40)
- Sub-task 1 (Late Fusion) downstream: cable_state 120D (40×3) + confidence 40D = 160D contribution to obs, but per CC4 v3.2 §6.4 augmented obs specifies 50D total — actual integration TBD in T-Vision-Fusion (本 design 範囲外)

---

## §3 Topology preservation strategy

### §3.1 Why critical (failure mode without)

40 segments are physically ordered: P_seg(0) at gripper-grasped end, P_seg(39) at opposite end。Wrong segment ordering = task failure (e.g., AC env target_seg_idx point to wrong physical location → wrong grip → cascade fail)。

| failure pattern | symptom | observation |
|-----------------|---------|-------------|
| Identity inversion | P_seg(0) labeled as P_seg(39) | gripper sees nearest seg as last seg, downstream policy confused |
| U-shape mid-fold | mid segs collapse onto themselves | PCA single-axis ignores 2nd mode → wrong arc-length |
| S-shape inflection | 2 curvature flips | PCA bias toward dominant axis → ~half segs misordered |
| Spatial entanglement | cable wraps around clip | depth ambiguity at intersection → segment identity confused |

### §3.2 4-layer defense (layered topology)

| layer | mechanism | primary failure addressed |
|-------|-----------|---------------------------|
| L1 | Arc-length monotonicity (L_arc) | bin emptiness, segment skip |
| L2 | Segment identity anchor (L_id) | identity inversion, mis-handedness |
| L3 | Temporal smoothness (L_temp) | per-frame discontinuity, oscillation |
| L4 | Bend regularization (L_bend) | unphysical kinks, isolated segment outliers |

### §3.3 Identity inversion check (post-fit)

```
After Stage D:
1. Compute d_grasp = ||P̂_seg(0) - p_grasp_finger||
2. Compute d_far = ||P̂_seg(39) - p_grasp_finger||
3. If d_grasp > d_far + 50mm:
     # Identity inversion suspected
     P̂_seg = reverse(P̂_seg)
     re-run Stage D with reversed seed (one re-fit pass)
```

### §3.4 Worst-case (U-shape, S-shape) handling

| topology | challenge | mitigation chain |
|----------|-----------|-------------------|
| U-shape | PCA 2 modes, var_ratio drops | Stage B fail → Stage C DD-PINN warm start (trained on U-shape sample) → Stage D refines |
| S-shape | 3 modes, more complex | Stage B fail → Stage C → Stage D with strong L_arc + L_bend |
| spatial entanglement | depth ambiguity | Stage A.3 voxel dedupe + Stage D L_temp from prev_est |

**Why DD-PINN handles U/S better than PCA:** DD-PINN learns curve representation (not single-axis), trained on 500 U + 500 S samples → captures multi-mode structure。Stage D Cosserat then refines per-segment positions on physics constraints。

### §3.5 Anchor source priority (L_id)

| priority | source | when active |
|----------|--------|-------------|
| 1 | grasp finger position (`finger_positions`) | grasp closed AND |finger - cable| < 20mm |
| 2 | previous_estimate (P_seg^{(t-1)}) | prev_est available AND consecutive frames |
| 3 | episode-start prior (cable initial pose) | episode_step == 0 |

---

## §4 Camera coverage analysis

### §4.1 EXP-046 precedent (single-midpoint, 3-cam)

| cam | error | points | bias |
|-----|-------|--------|------|
| overhead alone | 5.23mm | 263 | minimal |
| front_left alone | 83.4mm | 719 | strong Y-direction bias |
| front_right alone | 80.8mm | 653 | strong Y-direction bias |
| **merged (3-cam)** | **3.92mm** | **1635** | minimal |

**Lesson:** single-cam (especially front-side) has strong directional bias due to occlusion + perspective foreshortening。Multi-cam fusion essential for sub-5mm precision。

### §4.2 Newton VBD env current camera infrastructure

- `wrist_camera_manager.py`: 2× wrist (L+R) only、128² each、FOV 45°
- coverage analysis: both wrist cams attached to gripper bodies → cable visibility tied to gripper pose
- when both grippers are in workspace center, mid-segments visible; when grippers retract, far-segments occluded
- MVP-0B paused: wrist_R mIoU=0.248 (R-side training distribution gap)、indicates 2-cam path not yet ready even for single-midpoint

### §4.3 Recommended: 3-cam extension

```python
# Conceptual addition to wrist_camera_manager.py:
class CableStateCameraManager(WristCameraManager):
    def __init__(self, ..., enable_overhead=True):
        super().__init__(...)
        if enable_overhead:
            self._add_overhead_camera(
                position=(0.3, 0.0, 1.6),   # world-fixed, above table center
                target=(0.3, 0.0, 0.8),      # look at table center
                resolution=256,
                fov_deg=60.0,
            )
```

**Why overhead (not duplicate front_L/R from EXP-046):**
- front cams have strong Y-bias per EXP-046 → not pure improvement over wrist
- overhead orthogonal axis (top-down) covers the full lateral cable layout
- single overhead cam (256² FOV 60°) < 2 front cams cost
- world-fixed: no body_q dependency, simpler intrinsic + extrinsic calibration

**Risk:** overhead cam at z=1.6m may have depth precision issue at far range; voxel downsample mitigates this。

### §4.4 R6 boundary: per-camera intrinsics + extrinsics

| cam | intrinsics | extrinsic source | R6 OK? |
|-----|------------|-------------------|--------|
| wrist_L | K_pinhole (FOV 45°, 128²) | body_q[wrist_L] (robot-measurable) | ✅ |
| wrist_R | K_pinhole (FOV 45°, 128²) | body_q[wrist_R] (robot-measurable) | ✅ |
| overhead | K_pinhole (FOV 60°, 256²) | static (world-fixed, calibrated) | ✅ (calibration is robot-known constant) |

CC4 v3.2 §H.2 boundary: estimator core takes `EstimatorInputs` with rgb/depth tensors + camera_pose tensors。No newton state import。Add 2 fields:
```python
@dataclass
class EstimatorInputs:
    # existing:
    rgb_l, rgb_r, depth_l, depth_r, joint_state, wrist_camera_pose_l, wrist_camera_pose_r, ...
    # new for cable state:
    rgb_oh: torch.Tensor      # [B, 3, H_oh, W_oh] overhead RGB
    depth_oh: torch.Tensor    # [B, 1, H_oh, W_oh] overhead depth
    overhead_camera_pose: torch.Tensor  # [B, 7] (px py pz qx qy qz qw) — robot-known constant
    overhead_intrinsics: torch.Tensor   # [B, 3, 3] — robot-known constant
```

### §4.5 2-cam fallback (if overhead infeasible)

If overhead cam not deployable (latency / sensor / installation constraint):

| fallback | mechanism | risk |
|----------|-----------|------|
| Temporal accumulation | 5-frame fusion at quasi-static moments (gripper hold) | dynamic scene → error inflation |
| Aggressive Stage C reliance | DD-PINN warm start with 2-cam features | DD-PINN trained for 3-cam input → distribution shift |

Recommendation: **start with 3-cam from impl phase**; 2-cam fallback only if engineering blocker found。

---

## §5 Benchmark specification (Q5 gate)

### §5.1 Eval dataset construction

#### §5.1.1 Scene composition (120 total)

| dataset | count | source | scenario |
|---------|-------|--------|----------|
| Random | 100 | held-out 5-clip routing snapshots | random Phase / skill / cable shape |
| U-shape worst-case | 10 | scripted env (cable folding between clips) | mid-cable folds back, 2 modes |
| S-shape worst-case | 10 | scripted env (2 inflection points) | 3 modes, complex curvature |

#### §5.1.2 Random scene specification

- sample from current 5-clip-routing dataset (P-state + skill execution snapshots)
- ensure diversity across:
  - Phase ∈ {approach, grip, lift, transport, insert, release}
  - skill mid-execution states (no end-of-episode bias)
  - cable shape variety (straight 50%, bent 30%, complex 20%)
- random seed fixed for reproducibility (seed=42 for 100 scenes)

#### §5.1.3 U-shape worst-case generation

```
Scripted scenario:
  1. Cable initially routed through clip[0], clip[1], clip[2]
  2. Robot grasps cable mid-segment (e.g., seg[20])
  3. Robot pulls grasp_pos toward back to fold cable
  4. Snapshot at fold-active frame (cable folded ~180°)
Expected: PCA var_ratio ≈ 0.4-0.5
```

10 scenes generated with varied fold positions (seg[15], seg[18], seg[20], seg[22], seg[25]) × 2 fold-depth (medium / deep)。

#### §5.1.4 S-shape worst-case generation

```
Scripted scenario:
  1. Cable initially routed through clip[0], clip[1], clip[2], clip[3], clip[4]
  2. Insert cable into clip[1] groove (1st inflection)
  3. Insert cable into clip[3] groove (2nd inflection)
  4. Snapshot at inserted state (S-curve formed)
Expected: PCA var_ratio ≈ 0.3-0.4
```

10 scenes generated with varied insertion depths × clip combinations。

### §5.2 Per-scene evaluation protocol

```python
def evaluate_scene(estimator, scene_inputs, scene_gt):
    P̂_seg, c = estimator.estimate_cable_state(scene_inputs)
    e_per_seg = ‖P̂_seg - scene_gt.P_seg‖₂  # [40] per-segment error
    
    metrics = {
        'mean_error': e_per_seg.mean(),    # ē
        'p95_error':  e_per_seg.quantile(0.95),
        'max_error':  e_per_seg.max(),
        'identity_inversion': check_inversion(P̂_seg, scene_gt.P_seg),
        'confidence_calibration': compute_ece(c, e_per_seg),
        'stage_diagnostics': estimator.get_stage_metrics(),
    }
    return metrics
```

### §5.3 PASS criteria (Q5 gate)

| metric | gate | rationale |
|--------|------|-----------|
| Random N=100 mean(ē) | < 5mm | EXP-046 single-midpoint baseline 3.92mm → 40-segment scaling expects similar |
| Random N=100 mean(e_p95) | < 10mm | tail handling: worst seg of typical scene |
| U-shape 10/10 ē | < 5mm each | individual scene compliance |
| S-shape 10/10 ē | < 5mm each | individual scene compliance |
| Identity inversion rate | 0% (all 120) | wrong identity = task failure |
| Confidence ECE | < 5% | calibration quality |
| Latency (P95) | < 50ms | obs pipeline budget |

### §5.4 Per-stage diagnostics (for failure attribution)

| stage | metric | warn | fail |
|-------|--------|------|------|
| A | merged point count | < 1500 | < 800 |
| A | per-cam mIoU (when seg model ready) | < 0.85 | < 0.70 |
| B | PCA var_ratio (random scene) | < 0.7 | < 0.6 (triggers Stage C as designed) |
| B | bin emptiness count | > 4 | > 8 |
| C | warm start MSE vs GT | > 8mm | > 15mm |
| C | inference latency | > 3ms | > 5ms |
| D | Cosserat residual after 100 iter | > 2mm | > 5mm |
| D | iteration count | > 150 | == 200 (timeout) |
| E | confidence ECE | > 5% | > 10% |
| Total | end-to-end latency | > 50ms | > 100ms |

### §5.5 Failure mode tabulation (mitigation plan)

| F | mode | symptom | mitigation |
|----|------|---------|------------|
| F1 | HSV mask drift (lighting, texture) | Stage A mIoU drops | MVP-0B v2 9-class seg + DR Tier 0 D1-D2 |
| F2 | Depth dropout (specular surface) | sparse cloud regions | DR Tier 0 D5 (sensor noise + dropout train) |
| F3 | Self-occlusion (cable under cable) | some segs no points | L_temp + Stage C warm start |
| F4 | PCA fail (U/S shape) | var_ratio < 0.6 | designed: Stage C DD-PINN trigger |
| F5 | Cosserat local minima | L tail > 5mm after 100 iter | multi-restart + Stage C re-init |
| F6 | Identity inversion | §3.3 check fails | reverse + re-fit |
| F7 | Latency overflow | total > 50ms | warm start reduces Stage D iter; profile + tune |

---

## §6 Module boundary integration (R6 Appendix H)

### §6.1 PoseEstimatorCore extension

CC4 v3.2 §H.4 specifies `PoseEstimatorCore.forward → (PoseEstimate14D, RegimeState)`。本 design では cable_state を additional output として追加:

```python
# thread_isaac_lab/estimators/types.py (extension):

@dataclass
class CableState40:
    """Per-segment 3D position + confidence (本 design output)."""
    positions: torch.Tensor   # [B, 40, 3] world-frame xyz [m]
    confidences: torch.Tensor # [B, 40] in [0, 1]
    stage_diagnostics: dict   # per-stage metrics for debug

# pose_estimator_core.py (extension):

class PoseEstimatorCorePhase2:
    """Phase 2: Stage 0 + Stage 1 + Stage 2 + Stage 3a (cable state)."""
    
    def __init__(self, segmenter, intrinsics, cable_solver):
        self._segmenter = segmenter
        self._intrinsics = intrinsics
        self._cable_solver = cable_solver  # CableStateSolver, see §6.2
    
    def forward(self, inputs: EstimatorInputs) -> tuple[CoreOutputPhase2]:
        # Stage 0 + 1 (Phase 1, existing)
        phase1_out = super().forward(inputs)
        
        # Stage 2: depth back-projection (mask × depth → cloud)
        cloud = stage2_backproject(phase1_out.seg_logits, inputs)
        
        # Stage 3a: cable state estimation (Stage A.3 → E, see §2)
        cable_state = self._cable_solver(cloud, inputs.previous_cable_estimate)
        
        return CoreOutputPhase2(
            phase1=phase1_out,
            cloud=cloud,
            cable_state=cable_state,
        )
```

### §6.2 CableStateSolver interface

```python
class CableStateSolver:
    """Hybrid PCA + Cosserat 5-stage cable state estimation (本 design §2)."""
    
    def __init__(self, dd_pinn, cosserat_kernel, config):
        self._dd_pinn = dd_pinn        # Stage C DD-PINN model (~50k params)
        self._cosserat = cosserat_kernel  # Stage D Warp kernel
        self._config = config           # weights, thresholds, max_iter
    
    def __call__(self, cloud: torch.Tensor, prev: CableState40 | None) -> CableState40:
        # Stage B: PCA + 40-bin
        seg_b, var_ratio = stage_b_pca(cloud)
        
        # Stage C trigger: low var_ratio OR Stage B failure
        if var_ratio < self._config.var_ratio_threshold:
            seg_init = self._dd_pinn(cloud, prev)  # Stage C
        else:
            seg_init = seg_b
        
        # Stage D: Cosserat 7-term loss
        seg_final = self._cosserat.fit(
            init=seg_init, cloud=cloud, prev=prev,
            weights=self._config.weights,
            max_iter=self._config.max_iter,
        )
        
        # Identity inversion check (§3.3)
        seg_final = self._verify_identity(seg_final, prev)
        
        # Stage E: confidence
        c = self._compute_confidence(seg_final, cloud, prev)
        
        return CableState40(positions=seg_final, confidences=c)
```

### §6.3 R6 enforcement (no GT smuggling)

- `CableStateSolver` imports only from `thread_isaac_lab.estimators.*` (no `newton`, no env)
- `EstimatorInputs` extension fields (`rgb_oh`, `depth_oh`, `overhead_camera_pose`, `overhead_intrinsics`) are robot-measurable / robot-known constants
- No `cable_body_q` access in core path (only in offline eval per `EstimatorLabelsForEvalOnly`)
- grep test in `tests/test_estimator_input_boundary.py` covers extension fields

---

## §7 Implementation roadmap (Q1-Q7 detailed)

### §7.1 Phase Q1-Q7 (extends design memo §3.4 estimate)

| Q | item | LoC | GPU wall | dependency |
|---|------|-----|----------|------------|
| Q1 | Stage A.3 multi-cam fusion + voxel downsample (Warp kernel) + extend `vision_pipeline.py` | ~120 | n/a | Stage A.1-2 existing |
| Q2 | Stage B PCA + 40-bin discretization + validity gate + handedness anchor | ~80 | n/a | Q1 |
| Q3 | Stage C DD-PINN architecture + train pipeline + 5k-scene labeled dataset | ~180 | ~25h (incl. dataset render 10h + train 15h) | Q2 + sim env labeled dump |
| Q4 | Stage D Cosserat 7-term loss Warp kernel + L-BFGS optimizer + multi-restart | ~150 | n/a | Q3 |
| Q5 | Stage E confidence calibration (post-train logistic regression on val set) | ~50 | ~2h | Q4 |
| Q6 | Identity inversion check (§3.3) + integration into solver pipeline | ~30 | n/a | Q5 |
| Q7 | Worst-case benchmark generation (10 U + 10 S scripted) + Q5 gate evaluation + per-stage diagnostics | ~80 | ~5h | Q6 + held-out eval set |

**Total: ~690 LoC + ~32h GPU**
*(design memo §3.4 estimate ~400 LoC + ~30h GPU は base spec only、本 design では benchmark + diagnostics + identity verification を含めて拡張)*

### §7.2 Camera infrastructure extension (separate sub-task)

| item | LoC | dependency |
|------|-----|------------|
| `CableStateCameraManager` extending `WristCameraManager` (+overhead cam) | ~80 | wrist_camera_manager.py existing |
| Overhead cam pose calibration script | ~50 | Newton sim setup |
| Update `EstimatorInputs` with overhead fields | ~20 | types.py existing |

### §7.3 Dependencies and prerequisites

| prerequisite | status | trigger |
|--------------|--------|---------|
| T-Vision-Pose Stage A-B substrate (3-cam mask + back-projection ready) | precedent edge per state.md | T-Vision-Pose MVP-0A done; MVP-0B v2 unblock for canonical seg |
| MVP-0B v2 9-class seg ≥0.85 mIoU | external blocker | T-Vision-Pose impl |
| Sim labeled dataset (5k random + 500 U + 500 S + 120 held-out) | external resource | newton state dump infrastructure |
| Camera infrastructure (3-cam overhead) | new sub-task | impl phase Q1 |
| Warp kernel infrastructure | existing | Newton VBD pipeline |

---

## §8 Risk register

| ID | risk | severity | likelihood | mitigation |
|----|------|----------|------------|------------|
| R-1 | Stage D Cosserat non-convex local minima | HIGH | MED | Stage C warm start + 5-init multi-restart + best-L selection |
| R-2 | U/S worst-case mean exceeds 5mm despite 7-term loss | HIGH | MED | Stage C trained on 1k worst-case samples; w_3 (bend) tuning; if persists, increase Stage C samples to 2k |
| R-3 | Overhead camera infrastructure dev cost (~50 LoC + calibration) | MEDIUM | HIGH | reuse SensorTiledCamera; calibration script ~2h; total ~1 day eng |
| R-4 | DD-PINN dataset generation 5k scenes | MEDIUM | MED | newton state dump existing; ~10h GPU render; scriptable |
| R-5 | Latency budget 50ms exceeded | MEDIUM | MED | Stage D Warp kernel JIT; profile per-stage; reduce max_iter from 200 to 100 if needed |
| R-6 | Identity inversion (P_seg(0) vs P_seg(39)) | MEDIUM | LOW | §3.3 post-fit check + L_id anchor; 0% target enforced |
| R-7 | Confidence ECE > 5% on held-out | LOW | LOW | post-train calibration with logistic regression; well-studied technique |
| R-8 | T-Vision-Pose MVP-0B v2 unblock delay | EXTERNAL | MED | HSV fallback for Stage A.1 (Phase 1); 9-class seg swap when ready |
| R-9 | EI=0.1 sim value not match real cable | LOW | MED | sim-only; T-Vision-DR Tier 2 trigger for sim-to-real EI calibration |
| R-10 | Cable color variation (T-Vision-DR D3) HSV breaks | LOW | HIGH (real) | swap to 9-class seg before real deploy (MVP-0B v2 prerequisite) |

---

## §9 Open questions (for future revision)

| OQ | topic | current decision | trigger for revision |
|----|-------|-------------------|------------------------|
| OQ1 | Overhead cam exact intrinsics (FOV, position, look-at) | tentative: z=1.6m, FOV 60°, look-at table center (0.3, 0.0, 0.8) | impl Q1 calibration |
| OQ2 | DD-PINN warm start vs Stage D end-to-end joint train | sequential (Stage C → D); JOINT alt deferred | empirical comparison in Q5 |
| OQ3 | EI value for Cosserat: sim 0.1 vs real cable | use sim value; sim-to-real gap via T-Vision-DR | T-Vision-DR Tier 2 trigger |
| OQ4 | Identity anchor source priority | grasp finger Tier 1, prev_est Tier 2, episode prior Tier 3 | empirical: identity inversion rate per Tier |
| OQ5 | Eval mode (deterministic seed vs stochastic) | deterministic (seed=42, cuda:2 deterministic kernel) | CC4 v3.2 §10 alignment |
| OQ6 | Worst-case scene definition (only U + S, vs more) | U + S = primary 2 modes; spatial entanglement = Tier 2 | empirical fail outside U/S |
| OQ7 | Fallback when N_pts < 800 (Stage A FAIL) | use prev_estimate; if no prev → return zeros + low confidence | confirmed CC4 v3.2 FAIL_CLOSED policy alignment |
| OQ8 | Confidence aggregation coefficients (α, β) | post-train logistic regression on val | tunable per scene type |
| OQ9 | 2-cam fallback empirical performance | NOT recommended; 3-cam path canonical | infrastructure blocker |
| OQ10 | Late Fusion downstream integration (cable_state 120D + conf 40D vs 50D obs spec) | T-Vision-Fusion 範囲外 | sub-task 1 trigger |

---

## §10 Cross-references

### §10.1 Internal vault

- **Parent design (L1.A 3 sub-task):** `thread-vault/06-Knowledge/LL-Vision-L1A-Architecture.md` (§ "Sub-task 2: Hybrid PCA + Cosserat")
- **L1.A design memo (full):** `~/.claude/projects/-home-rlrk-IsaacLab/memory/project_l1a_vision_design_complete_2026-04-27.md` (§3.4 Sub-task 2 推奨)
- **CC4 base spec:** `thread-vault/07-Design/PoseEstimation-Design-v3.2.md` (§H Estimator boundary, §5.4 Stage 3a expand)
- **CC4 v3.1:** `thread-vault/07-Design/PoseEstimation-Design-v3.1.md` (12-point patch, Appendix D R6 input boundary)
- **EXP-046 baseline:** `thread-vault/05-Thinking/Experiment Log.md` L1673-1686 (PCA-center 3.92mm @ single-midpoint, 1635 merged pts, 3-cam)
- **EXP-047 dynamic eval:** `thread-vault/05-Thinking/Experiment Log.md` L1655-1671 (Vision pipeline 3.85mm dynamic, 0% fallback)
- **Logic tree leaf:** `thread-vault/T-Vision-CableState/state.md` (L1.A.2 node、IN_PROGRESS dependency, Q5 gate)
- **SOMA Phase A7:** `thread-vault/04-Specs/SOMA.md` L101 (PCA-center 3.92mm < 5mm precedent)

### §10.2 Code references

- `thread_isaac_lab/configs/task_config.py:70-75` (CABLE_SEGMENTS=40, CABLE_SEG_LEN=0.015, CABLE_RADIUS=0.004, CABLE_BEND_STIFFNESS=0.1)
- `thread_isaac_lab/models/vision_pipeline.py` (existing single-midpoint baseline; extend for Stage A → 40-bin)
- `thread_isaac_lab/envs/wrist_camera_manager.py` (2-cam wrist L/R baseline; extend → CableStateCameraManager + overhead)
- `thread_isaac_lab/estimators/types.py` (EstimatorInputs boundary types; extend with overhead fields)
- `thread_isaac_lab/estimators/core/pose_estimator_core.py` (PoseEstimatorCorePhase1; extend → Phase2 with Stage 2 + 3a)

### §10.3 Sister leaves & downstream

- **T-Vision-Pose** (L1.A.1 precedent edge, Stage A-B substrate 共有): `thread-vault/T-Vision-Pose/state.md`
- **T-Vision-DR** (L1.A.3、shared dataset re-render asset): `thread-vault/T-Vision-DR/state.md`
- **T-Vision-Fusion** (L1.A.4 downstream consumer、cable_state 120D obs 統合): `thread-vault/T-Vision-Fusion/state.md`
- **T-Vision umbrella:** `thread-vault/T-Vision/state.md`

### §10.4 Schedule (cron)

- §16 commit re-trigger 2026-05-09: `T-COORD-MONITOR-S16-RECHECK`
- F1-WarmStart G5 readiness 2026-05-10: `T-COORD-MONITOR-F1-WARMSTART` (Fusion external blocker)

---

## §11 Status

- **Created:** 2026-05-03 (T-Vision-CableState-Design-CC sub-session)
- **Phase:** design-complete (impl pending, separate task per state.md §4 Active rule)
- **Author:** T-Vision-CableState-Design-CC (sub-agent of T-ROOT-COORD)
- **Permissions:** 06-Knowledge は CC Create/Update 可 (Vault Write Permissions)
- **Next steps (impl phase trigger):**
  - T-Vision-Pose MVP-0B v2 unblock + CC4 v3.2 OQ approval
  - Sim labeled dataset (5k scenes) generation infrastructure ready
  - Camera infrastructure extension (overhead cam) approved
  - 別 task `CC-L1A-Cable-State-Impl` 起票候補 per state.md §4 trigger
- **04-Specs SSOT update:** out-of-scope (Rs専権 per Vault Write Permissions); Rs 承認後 separate task で起票候補 (CC-L1A-04Specs-Update per L1.A 9 別 task 起票候補)

---

## §12 Output format compliance (CLAUDE.md §運用)

| 区分 | 主張 | 根拠（出典） |
|------|------|---------------|
| 事実 | EXP-046 PCA-center 3.92mm @ 3-cam 1635pts (single-midpoint) | `thread-vault/05-Thinking/Experiment Log.md` L1677-1684 |
| 事実 | CABLE_SEGMENTS=40, CABLE_SEG_LEN=0.015, CABLE_BEND_STIFFNESS=0.1 (EI rubber-coated) | `thread_isaac_lab/configs/task_config.py:70-75` |
| 事実 | Newton VBD 現状 camera infra = wrist L/R only (2-cam, 128² FOV 45°) | `thread_isaac_lab/envs/wrist_camera_manager.py:60-114` |
| 事実 | MVP-0A pose estimator core = Stage 0 + Stage 1 only (Phase 1 narrowed) | `thread_isaac_lab/estimators/core/pose_estimator_core.py:60-128` |
| 事実 | CC4 v3.2 §H.4 specifies PoseEstimatorCore.forward → (pose_14d, regime) with internal stage3a | `thread-vault/07-Design/PoseEstimation-Design-v3.2.md:480-496` |
| 推測 | 3-cam coverage で 40-segment p95<10mm 達成可能 (mean<5mm の延長として) | EXP-046 single-midpoint 3.92mm baseline + 7-term loss + DD-PINN warm start の 3 重防御。但し empirical 確認 = Q7 worst-case benchmark |
| 推測 | Stage D 100 iter Warp kernel ~5-10ms (warm start 経で) | typical Cosserat fitting iteration cost ~0.1ms/iter on cuda:0、warm start で 30-50 iter 収束想定。要 profiling (Q5) |
| 推測 | Identity inversion rate 0% target 達成可能 (§3.3 check + L_id anchor) | grasp finger anchor は physical contact、prev_est 連続性、episode-start prior の 3 重 anchor source |
