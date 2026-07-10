---
title: Vision Pose Design — per-clip 6DOF (Charuco + SAM2 + PnP+RANSAC alternative path)
created: '2026-05-03T18:30:00+09:00'
updated: '2026-05-03T18:30:00+09:00'
tags:
  - knowledge
  - vision
  - pose-estimation
  - per-clip
  - mvp-3
  - phase-5-4
  - alternative-design
status: 'approved (Rs batch approve 2026-05-03 T-ROOT-COORD#s11) — alternative path adoption (Charuco + SAM2 + PnP+RANSAC)、CC4 v3.2 path 並走維持 per §0.3'
owner: 'T-Vision-Pose-Design-CC (sub-session of T-ROOT-COORD)'
parent: '[[T-Vision-Pose]]'
related: '[[LL-Vision-L1A-Architecture]] | [[PoseEstimation-Design-v3.2]] | [[PoseEstimation-Design-v3.1]] | [[LL-VisualObs-CameraSystem]]'
doc_class: design-surface
---

# Vision Pose Design — per-clip 6DOF (Charuco + SAM2 + PnP+RANSAC alt path)

> Per-clip 6DOF pose estimation MVP-3 設計の代替 path (Charuco calibration +
> SAM2 zero-shot segmentation + PnP+RANSAC pose recovery)。
> CC4 v3.2 (custom LightUNet + Cosserat rod fitting) の 9 OQs Rs approval blocker
> を、industry-standard pipeline 採用で side-step する設計。
> 04-Specs SSOT (Vision Pipeline.md) は Rs専権、本 file は CC 編集可な technical
> reference として 06-Knowledge に配置 (LL-Vision-L1A-Architecture.md:16 precedent)。

## §0 Summary

### 0.1 Goal

T-Vision-Pose (L1.A.1 leaf) の MVP-3 milestone:

- per-clip 6DOF pose estimation **median translation < 5 mm AND yaw error < 10°**
- on **N=100 eval-det scenes × 5 seeds** (eval-det mode、cuda:2 deterministic)
- p95 trans < 10 mm AND p95 yaw < 20°

### 0.2 Why this alternative path (vs CC4 v3.2)

| 観点 | CC4 v3.2 (custom LightUNet + Cosserat) | 本 alt path (Charuco + SAM2 + PnP+RANSAC) |
|------|------|------|
| segmentation backbone | custom LightUNet (~3M params)、Phase 0 dataset で訓練 | SAM2 zero-shot (Meta SAM2 ViT-B/L、訓練不要) |
| pose recovery | Cosserat rod fitting (Stage 3a/b) + temporal gate | PnP+RANSAC + clip CAD vertex correspondence (industry-standard) |
| training data 要否 | dataset re-render 必須 (MVP-0B v2 paused、wrist_R mIoU=0.248) | zero-shot (training data 不要、SAM2 prompted by ROI) |
| 9 OQs blocker | OQ-1a/1b/2/3/4/5a/5b/5c/6 全関連 | OQ-1a/1b 大幅 side-step、OQ-2-6 関連は §6 で個別 resolution |
| 実装複雑度 | ~250 LoC + ~30h GPU (state.md §1 推定) | ~150-200 LoC + ~5h GPU (zero-shot SAM2 + cv2.solvePnPRansac) |
| sim-to-real path | DR Tier 0-2 curriculum (T-Vision-DR leaf) で対処 | Charuco real-cam calibration が直接 path、SAM2 は domain-agnostic |
| latency budget (online) | Stage 1 LightUNet ~5-15ms、stage合計 ~30-50ms | SAM2 ViT-B ~30-100ms、online は破綻、**offline benchmark / async / distilled mode 想定** |

### 0.3 Scope discipline

本 path は **MVP-3 milestone の代替 deliverable**。CC4 v3.2 の Cosserat rod
fitting は L1.A.2 (T-Vision-CableState、cable 40 segment 3D position) 用途で
依然有効、本 path で置換しない。本 path は **per-clip pose only** (cable は対象外)。

CC4 v3.2 既実装 artifact (estimators/types.py + estimators/input_adapter.py +
estimators/core/segmenter.py LightUNet + scripts/eval_pose_estimator_mvp0a.py) は
**reuse 可能**: 本 path は同 R6 boundary (PoseEstimatorInputAdapter +
PoseEstimatorCore protocol) を踏襲、Stage 1 (segmentation backend) を SAM2 に、
Stage 3 (pose recovery) を PnP+RANSAC に差し替える minimal-delta refactor。

## §1 Architecture overview

### 1.1 3-stage pipeline

```
┌────────────────────────────────────────────────────────┐
│ INPUT: RGB-D from camera (sim: Newton SensorTiledCamera│
│         real: RealSense / Logitech via Charuco-cal)    │
│         + clip CAD vertices (routing_clip_v1.usd parse)│
│         + ROI prompt (kinematic prior or center)       │
└────────────────────────┬───────────────────────────────┘
                         ▼
┌────────────────────────────────────────────────────────┐
│ Stage 1: SAM2 zero-shot segmentation                   │
│   - Input: RGB image + ROI bbox prompt (clip-shaped)   │
│   - Output: per-clip binary mask + sigmoid confidence  │
│   - Backbone: SAM2 ViT-B (recommend) or ViT-L          │
│   - Mode: offline benchmark / async inference          │
└────────────────────────┬───────────────────────────────┘
                         ▼
┌────────────────────────────────────────────────────────┐
│ Stage 2: 2D feature point extraction (subpixel refine) │
│   - Input: clip mask + RGB                             │
│   - Output: 2D keypoint set (corners / contour /       │
│             texture features) with subpixel precision  │
│   - Method: cv2.goodFeaturesToTrack within mask, OR    │
│             contour polygon vertex extraction          │
└────────────────────────┬───────────────────────────────┘
                         ▼
┌────────────────────────────────────────────────────────┐
│ Stage 3: PnP+RANSAC 6DOF pose recovery                 │
│   - Input: 2D keypoints + 3D model points (CAD parse)  │
│           + camera intrinsic K (sim: known, real:      │
│            Charuco-calibrated)                         │
│   - Output: PoseEstimate14D (R, t for clip body frame) │
│   - Method: cv2.solvePnPRansac with EPnP / IPPE / AP3P │
│             auto-selected by correspondence cardinality│
└────────────────────────┬───────────────────────────────┘
                         ▼
┌────────────────────────────────────────────────────────┐
│ OUTPUT: PoseEstimate14D + RegimeState (ACCEPT / FALLBCK│
│         / FAIL_CLOSED) + per-clip confidence           │
│         (matches CC4 v3.2 §3.2 output contract)        │
└────────────────────────────────────────────────────────┘
```

### 1.2 Module boundary (R6, CC4 v3.2 Appendix H reuse)

既存 `estimators/input_adapter.py` の `PoseEstimatorInputAdapter` を再利用、
`PoseEstimatorCore` (CC4 v3.2 Stages 0-4) を本 path 用 `PoseEstimatorCoreV2`
に差し替える (新規 module `estimators/core/pose_estimator_core_v2.py`、
~150 LoC、Stage 1 SAM2 + Stage 2 keypoint + Stage 3 PnP)。

R6 boundary 不変: PoseEstimatorCoreV2 は `EstimatorInputs` only を受け取り、
Newton / env / WristCameraManager 直 import 禁止 (CC4 v3.2 §H.3 import-lint test
そのまま適用)。

## §2 Stage 1: Charuco camera calibration

### 2.1 Sim vs Real

| Mode | Charuco 必要性 | Source |
|------|---------------|--------|
| **Sim (Newton SensorTiledCamera)** | **不要** | Camera intrinsic K は既知 (focal_length = resolution / (2 tan(FOV/2))、principal_point = (W/2, H/2))、extrinsic は body_q[wrist_L] + LOCAL_POS で env-side derived (`wrist_camera_manager.py:55-61` で expose) |
| **Real (RealSense D435i / Logitech)** | **必須** | Lens distortion (radial + tangential) + chromatic aberration + sensor mount tolerance を吸収。Charuco board (e.g., 5×7 ChArUco grid、~200mm 一辺) を fixed pose で観測、`cv2.aruco.calibrateCameraCharuco` で K + dist_coeffs 抽出 |

### 2.2 Charuco board spec (real-cam calibration)

- Board: 5×7 ChArUco (DICT_4X4_50)、square_length=40mm、marker_length=30mm
- Capture: ≥30 unique board pose を 1m 以内で撮影 (各角度・各距離)
- Output: `K` (3×3 intrinsic)、`dist_coeffs` (5-vector OpenCV format)
- 保存先: `data/camera_calibration/<camera_id>.json` (sim default は同 schema で
  null distortion + analytical K を書き込み、API 統一)

### 2.3 Sim default intrinsic JSON (Newton wrist camera)

```json
{
  "camera_id": "newton_wrist_L_default",
  "resolution": [128, 128],
  "fov_deg": 45.0,
  "K": [[154.553, 0, 64], [0, 154.553, 64], [0, 0, 1]],
  "dist_coeffs": [0, 0, 0, 0, 0],
  "source": "analytical (newton SensorTiledCamera GT)"
}
```

(focal_length = 128 / (2 × tan(22.5°)) ≈ 154.553)

### 2.4 Real-cam calibration script (将来実装、scope外)

`scripts/calibrate_camera_charuco.py` (impl 将来、本 design では schema 定義のみ)。
本 design memo は **sim-MVP scope**、Charuco impl は L1.A.3 (T-Vision-DR) Tier 2
real-hardware sim-to-real PoC trigger 経で起票。

## §3 Stage 2: SAM2 zero-shot segmentation

### 3.1 SAM2 model selection

| Variant | Params | Latency (A6000 fp16, 1024×1024) | VRAM | 推奨 use |
|---------|--------|------|------|---------|
| SAM2 ViT-B | 80M | ~30-50ms | ~2 GiB | **MVP-3 default** (latency vs accuracy balance) |
| SAM2 ViT-L | 308M | ~80-150ms | ~6 GiB | high-precision benchmark mode |
| SAM2 ViT-H | 636M | ~150-300ms | ~10 GiB | reference accuracy only |

Resolution: SAM2 native 1024×1024 input、wrist 128×128 を upsample (bilinear)
してから推論、出力 mask を downsample で戻す (lossy だが MVP-3 acceptable;
真の高解像度は §3.3 prompt 戦略で吸収)。

### 3.2 Prompt strategy

SAM2 は prompted segmentation; 以下を prompt source として優先選定:

1. **Bbox prompt (推奨)**: clip kinematic prior (env-side known clip nominal
   position) を camera 投影 → Bbox 拡張 (1.5× margin) → SAM2 input
2. **Point prompt (補助)**: bbox 中心 + foreground/background point sample
   (refinement 用)
3. **Mask prompt (再 inference 時)**: 前 frame の SAM2 mask を初期 prompt として
   再投入 (temporal smoothing、§3.4)

### 3.3 Inference mode (online vs offline)

CC4 v3.2 §8.1 latency budget は ~12ms/step。SAM2 ViT-B alone で ~30-50ms、
**online policy step では budget 違反**。3 mode を区別:

| Mode | use case | 実装 path |
|------|----------|----------|
| **Offline benchmark** | MVP-3 評価 (本 design 主用途) | 全 step 終了後、recorded camera frames に SAM2 を batch 実行、ground-truth と照合 |
| **Async inference** | online policy 補助 (将来) | sub-process で SAM2 推論、policy step は前 frame の cached mask を使用 (latency tolerated) |
| **Distilled mode** | 真の online (post-MVP-3) | SAM2 → 軽量 mask predictor (~3M params LightUNet 既存) を distillation で訓練、~5ms/step |

**MVP-3 scope: offline benchmark only**。distilled / async は MVP-4 以降の trigger。

### 3.4 Temporal smoothing (CC4 v3.2 §5.6 Stage 4 流用)

per-frame SAM2 mask を CC4 v3.2 §5.6 state machine (ACCEPT / PREDICT_TEMPORAL /
FALLBACK / FAIL_CLOSED) に通す:

- ACCEPT: SAM2 confidence > T_high (default 0.85)
- PREDICT_TEMPORAL: T_predict (0.5) ≤ conf ≤ T_high、前 frame mask を IoU 補正で
  carry-forward (≤K=20 frames)
- FAIL_CLOSED: conf < T_predict for K+ frames、policy_update_mask=False
  (CC4 v3.2 Appendix I 流用)

### 3.5 SAM2 dependency installation

```bash
# 必要 PyPI package (env_isaaclab6 venv)
/home/rlrk/env_isaaclab6/bin/pip install sam2
# checkpoint download (公式 Meta SAM2 hub)
mkdir -p /home/rlrk/IsaacLab/data/sam2_ckpt
wget -O /home/rlrk/IsaacLab/data/sam2_ckpt/sam2_hiera_base_plus.pt \
    https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_base_plus.pt
```

(本 cmd は MVP-3 impl phase で実行、本 design memo は dependency 記述のみ)

## §4 Stage 3: PnP+RANSAC pose recovery

### 4.1 Clip CAD model (3D point set)

`/home/rlrk/IsaacLab/data/clip/routing_clip_v1.usd` (~30 vertices binary USD)
を parse → 3D vertex array (clip body frame、metric m)。

USD parse path:

```python
from pxr import Usd, UsdGeom
stage = Usd.Stage.Open("data/clip/routing_clip_v1.usd")
clip_prim = stage.GetPrimAtPath("/Clip/Body/Mesh")
points_attr = UsdGeom.Mesh(clip_prim).GetPointsAttr()
clip_vertices = np.array(points_attr.Get())  # (~30, 3) float32 metric m
```

事前 cache: `data/clip/routing_clip_v1_vertices.npz` (np.savez_compressed)、
runtime 1 回 load only。

### 4.2 2D feature point extraction (Stage 2 → Stage 3 bridge)

SAM2 mask → 2D keypoints の 3 候補:

| Method | 推奨 | 理由 |
|--------|------|------|
| **Mask contour polygon vertex** (cv2.findContours + approxPolyDP) | **MVP-3 default** | clip 形状の幾何 corner と直接対応、~6-12 vertex 抽出可 |
| **Goodfeatures within mask** (cv2.goodFeaturesToTrack) | 補助 | texture が乏しい sim render では不安定 |
| **Mask centroid + axis** (cv2.minAreaRect) | fallback | corner cardinality < 4 時の degenerate 回避 |

**Subpixel refinement**: cv2.cornerSubPix で各 keypoint を ±0.5 px 精度に refine
(target 5mm @ 0.5m camera distance、pixel size 3.3mm → ~1.7 mm precision 達成)。

### 4.3 2D-3D correspondence

Clip CAD vertex array (4.1) と Stage 2 keypoint (4.2) を **nominal pose に基づき
ordering matching**: kinematic prior の clip pose で CAD vertex を camera 投影、
nearest-neighbor で 2D keypoint と pair。曖昧度 (multiple match) は最近 vertex
のみ採用 (false correspondence は RANSAC で除外)。

### 4.4 PnP variant 自動選択

correspondence cardinality N に応じ:

| N | PnP method | 備考 |
|---|-----------|------|
| N == 4 | AP3P (cv2.SOLVEPNP_AP3P) | minimal、4 点解析解 |
| 4 < N ≤ 6 | EPnP (cv2.SOLVEPNP_EPNP) | small-N 高速 |
| N > 6 | iterative (cv2.SOLVEPNP_ITERATIVE) | non-linear refinement、Lev-Marq |
| 全部 coplanar (clip 平面検出時) | IPPE (cv2.SOLVEPNP_IPPE) | 平面 degeneracy 回避 |

### 4.5 RANSAC parameters

```python
import cv2
success, rvec, tvec, inliers = cv2.solvePnPRansac(
    objectPoints=clip_vertices_3d,         # (N, 3) float32
    imagePoints=keypoints_2d,              # (N, 2) float32
    cameraMatrix=K,                        # (3, 3) float32
    distCoeffs=dist_coeffs,                # (5,) float32 (sim: zeros)
    iterationsCount=200,                   # RANSAC max iter
    reprojectionError=2.0,                 # px (subpixel-refined keypoint tolerance)
    confidence=0.99,                       # RANSAC convergence
    flags=auto_select_pnp_variant(N),      # §4.4
)
# Refine with iterative on inliers
if success and len(inliers) >= 4:
    rvec, tvec = cv2.solvePnPRefineLM(
        clip_vertices_3d[inliers], keypoints_2d[inliers],
        K, dist_coeffs, rvec, tvec,
    )
```

### 4.6 Pose output → PoseEstimate14D contract

```python
R_clip = cv2.Rodrigues(rvec)[0]  # (3, 3) rotation matrix
t_clip = tvec.flatten()           # (3,) translation [m]
quat_xyzw = rotation_matrix_to_quat(R_clip)  # (4,) [qx,qy,qz,qw]

# Pack into PoseEstimate14D (CC4 v3.2 §3.2 contract)
pose_14d = torch.cat([
    seg_pos_w,         # (3,) cable target seg pos (NOT recovered here, owned by L1.A.2)
    seg_quat_w,        # (4,) cable target seg quat (NOT here)
    t_clip.tensor(),   # (3,) clip pos in world frame (本 path 主成果)
    quat_xyzw.tensor() # (4,) clip quat in world frame
])
```

注: CC4 v3.2 PoseEstimate14D は `[seg_pos(3), seg_quat(4), clip_pos(3), clip_quat(4)]` 構造。
本 path は **clip 7D のみ提供**、seg 7D は L1.A.2 (T-Vision-CableState、Cosserat path)
担当 → integration は ObsAssembler で per-skill obs に統合。

### 4.7 Symmetry handling (yaw ambiguity)

routing_clip_v1.usd は U-shape (~30 vertex 観察より、symmetric arm 構造の可能性)。
symmetric clip では yaw が non-unique:

- **Convention**: clip body frame は longest geometric axis を z 軸、symmetric
  90°/180° invariance は **yaw error metric を mod π で計算**
- USD vertex 主成分分析 (PCA) で longest axis を pre-compute、`data/clip/routing_clip_v1_axis.npz` に cache

## §5 MVP milestone definitions

CC4 v3.2 §7.1 MVP table を本 path 用に re-scope:

| MVP | Scope (本 path) | Pass criterion | Estimated effort |
|-----|-----------------|----------------|------------------|
| **MVP-0 (本 alt)** | SAM2 ViT-B install + offline single-image inference + clip CAD parse + cv2.solvePnPRansac unit test | 1 sample image でe2e pipeline run、SAM2 mask IoU > 0.7、PnP convergence (rvec/tvec finite) | ~1 day impl + 0 GPU h |
| **MVP-1 (本 alt)** | N=10 scene benchmark、median trans / yaw 計測、failure mode 観察 | trans median < 20 mm、yaw < 30° (loose、early sanity) | ~1 day impl + ~2 GPU h |
| **MVP-2 (本 alt)** | N=100 scene 単 seed、temporal gate (CC4 §5.6) 適用 | trans median < 10 mm、yaw < 20°、ACCEPT regime > 80% | ~2 day impl + ~5 GPU h |
| **MVP-3 (本 alt、本 memo target)** | **N=100 × 5 seeds eval-det、final goal_verification 達成** | **trans median < 5 mm AND yaw median < 10° AND p95 trans < 10 mm AND p95 yaw < 20°** | ~3 day impl + ~10 GPU h |

注: CC4 v3.2 MVP-0A (custom LightUNet 訓練) は本 path で **不要** (SAM2 zero-shot)。
MVP-0B (R-side fine-tune、wrist_R mIoU=0.248 paused) も本 path で **不要**
(SAM2 は zero-shot、camera 別 fine-tune 不要)。
**本 alt path は MVP-0B v2 unpause を blocker から外す** = T-Vision-Pose state.md
external blocker の 1 件解消。

## §6 CC4 v3.2 9 OQs Resolution Plan

CC4 v3.2 末尾「Next action: Rs approval on 9 pending OQs」(OQ-1a / OQ-1b / OQ-2 /
OQ-3 / OQ-4 / OQ-5a / OQ-5b / OQ-5c / OQ-6) を本 alt path scope で解消:

| OQ | CC4 v3.2 内容 | 本 path 解消方針 |
|----|---------------|------------------|
| **OQ-1a** Concept approval | Approve Option C-2R direction + MVP-0A scoping | **Side-step**: 本 path は Option C-2R (custom LightUNet + Cosserat) を採用しない、industry-standard pipeline (SAM2 + PnP) で代替。MVP-0A 不要 (SAM2 zero-shot)。Rs 判断 = (a) 本 alt path を MVP-3 主 path 採択 / (b) C-2R + alt 並行 / (c) C-2R 単独 |
| **OQ-1b** Implementation gate (post-benchmark) | MVP-0A full impl + Stage 1 measured benchmark gate | **Side-step**: MVP-0A 不要、本 path MVP-1 (§5) で N=10 scene benchmark に置換、benchmark gate criterion は本 §7 で定義 |
| **OQ-2** MVP scope (AC-only MVP-0A→MVP-3) | AC-only MVP-3、MVP-4 (IC/AR/Grip-CLAMP) deferred pending OQ-5 | **継承**: 本 path も AC-only MVP-3 scope 維持、MVP-4 (per-skill 拡張) は OQ-5 同様 deferred。本 path は per-clip pose のみ、AC env の clip-relative obs に統合 |
| **OQ-3** Implementation timing (offline replay default) | Phase 5-1 priorities clear まで parked、cuda:2 offline replay only、4 DAPG 並走禁止 | **継承**: 本 path も同条件適用。MVP-0/1/2 は cuda:2 offline、4 DAPG 訓練と並走禁止 (GPU resource conflict 回避) |
| **OQ-4** DR noise distribution (placeholder σ) | σ_pos=3mm / σ_ori=0.03 rad placeholder、MVP-2B で measured 校正 | **継承 (修正)**: 本 path MVP-3 達成後の measured residual で σ を更新。SAM2 zero-shot は LightUNet と residual 分布が異なる可能性、placeholder 値の流用禁止 (測定必須) |
| **OQ-5a** Confirm Grip dual-arm mode as MVP-0A~3 target | Grip dual-arm only、single-arm excluded | **継承**: 本 path も Grip dual-arm scope (MVP-4 trigger 時)。本 MVP-3 は AC のみ |
| **OQ-5b** IC strategy (A unify / B per-skill heads / C defer) | A/B/C 選択、IC env 45D groove-relative vs RL-Routing-Design 42D 不整合 | **継承 (推奨 C)**: 本 path も IC defer 推奨。理由: SAM2 + PnP は per-clip pose only、IC は groove-relative 座標で別 frame、本 path で直接 cover 不可 |
| **OQ-5c** Document unified 45D base model contract | RL-Routing-Design.md §4 を 42D → 45D に修正 | **継承**: 本 path obs 統合は CC4 v3.2 §6 / Appendix E と同 contract (45D → 50D augmented obs)。RL-Routing-Design.md 修正は本 path scope外、CC4 v3.2 と共有 OQ |
| **OQ-6** Sim-to-real PoC timing (defer until MVP-4 / un-park) | Real-robot defer | **継承**: 本 path も real-robot defer。Charuco real-cam calibration (§2) は sim-to-real PoC trigger 経で起動、本 MVP-3 は sim only |

### 6.1 OQ resolution summary

| OQ | 本 path resolution |
|----|-------------------|
| OQ-1a | **Side-step (architecture pivot)** |
| OQ-1b | **Side-step (新 benchmark gate §7)** |
| OQ-2 | **継承 (AC-only MVP-3)** |
| OQ-3 | **継承 (offline replay only)** |
| OQ-4 | **継承+修正 (本 path 用 σ 再測定要)** |
| OQ-5a | **継承 (Grip dual-arm 推奨)** |
| OQ-5b | **継承 (IC defer 推奨)** |
| OQ-5c | **継承 (共有 OQ)** |
| OQ-6 | **継承 (real-robot defer)** |

**Rs approval gate**: 本 alt path 採択時、Rs は (a) MVP-3 主 path 切替 / (b) C-2R
並行維持 / (c) 本 path reject の 3 択判断。本 design memo は (a) を default 推奨
(理由: 9 OQs 解消、MVP-0B v2 unpause 不要、~150-200 LoC vs ~250、~5h GPU vs ~30h)。

## §7 Benchmark methodology (N=100×5seeds eval-det)

### 7.1 Eval scene generation

N=100 unique scene を以下 procedural generator で:

```python
# scripts/gen_pose_eval_scenes.py (将来実装、scope外、本 design は spec 定義)
for scene_id in range(100):
    rng = np.random.default_rng(scene_id)  # deterministic per scene_id
    # 5 clip 各 position randomize (in routing-feasible bounds)
    clip_positions = sample_clip_positions(rng)  # (5, 3) [m]
    # clip yaw randomize (uniform [0, 2pi))
    clip_yaws = rng.uniform(0, 2*np.pi, size=5)
    # wrist initial pose at "clip-visible" subset
    wrist_pose_l = sample_clip_visible_wrist_pose(clip_positions, rng)
    # 1 frame per scene (eval-det = 1 deterministic frame)
    yield Scene(scene_id, clip_positions, clip_yaws, wrist_pose_l)
```

注: per-clip yaw randomize は §4.7 symmetry convention 適用 (yaw mod π 観察)。

### 7.2 Eval-det mode (deterministic)

`eval_deterministic.py:50-53` precedent (NEWTON_DEVICE 固定 + cuda:0、policy.eval +
torch.no_grad) を踏襲:

```bash
CUDA_VISIBLE_DEVICES=2 NEWTON_DEVICE=cuda:0 \
    /home/rlrk/env_isaaclab6/bin/python \
    thread_isaac_lab/scripts/eval_pose_v2_alt.py \
    --num-scenes 100 --num-seeds 5 \
    --sam2-ckpt /home/rlrk/IsaacLab/data/sam2_ckpt/sam2_hiera_base_plus.pt \
    --clip-cad /home/rlrk/IsaacLab/data/clip/routing_clip_v1.usd \
    --output-report /home/rlrk/IsaacLab/data/pose_v2_alt/mvp3_benchmark.json \
    --device cuda:0
```

### 7.3 Metrics

per scene × per seed × per clip (=5):

- `trans_err = ||t_pred - t_gt||_2` [m]
- `yaw_err = wrap(|yaw_pred - yaw_gt|, π)` [rad] (§4.7 symmetry mod)
- `regime` ∈ {ACCEPT, PREDICT, FALLBACK, FAIL_CLOSED}

合計 measurements: 100 scenes × 5 seeds × 5 clips = **2500 per-clip measurements**

集計:

| Metric | Statistic | Pass threshold |
|--------|-----------|----------------|
| `trans_err` | median (over 2500) | < 5 mm |
| `yaw_err` | median (over 2500) | < 10° (≈ 0.175 rad) |
| `trans_err` | p95 (over 2500) | < 10 mm |
| `yaw_err` | p95 (over 2500) | < 20° (≈ 0.349 rad) |
| `regime == ACCEPT` rate | mean | > 80% |
| `regime == FAIL_CLOSED` rate | mean | < 10% |

### 7.4 Per-seed sanity check

5 seeds の per-seed median variance を観察:

- median 個 std (over 5 seeds) < 1 mm trans / < 2° yaw → seed-robust
- variance > 上記 → seed-fragile、design revisit 必要

### 7.5 Output report schema (`mvp3_benchmark.json`)

```json
{
  "config": {"num_scenes": 100, "num_seeds": 5, "sam2_ckpt": "...", "clip_cad": "..."},
  "aggregate": {
    "trans_err_median_mm": <float>,
    "yaw_err_median_deg": <float>,
    "trans_err_p95_mm": <float>,
    "yaw_err_p95_deg": <float>,
    "accept_rate": <float>,
    "fail_closed_rate": <float>,
    "PASS": <bool>
  },
  "per_seed": [{"seed": int, "trans_median_mm": float, "yaw_median_deg": float}, ...],
  "per_scene": [{"scene_id": int, "per_clip": [{"clip_idx": int, "trans_err_mm": float, "yaw_err_deg": float, "regime": str}, ...]}, ...]
}
```

### 7.6 Camera placement gate (Failure Scenario F1 mitigation)

本 path の MVP-3 達成可否は clip visibility に依存。Pre-MVP-3 gate:

- N=100 scene の wrist_L FOV に clip が出現する frame 率を計測
- visibility rate < 80% → camera placement 再検討必要 (overhead camera 追加 = env
  change task として別起票、L3 path)
- visibility rate ≥ 80% → wrist_L only で MVP-3 進行可

## §8 Risk register

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| R-1 | wrist_L FOV に clip が映らず SAM2 segmentation 失敗 (F1) | **HIGH** | §7.6 visibility gate + overhead camera 追加検討 (env change L3 task) |
| R-2 | SAM2 ViT-B latency ~30-100ms で online 不能 (F2) | HIGH | offline benchmark mode 限定 (§3.3)、distilled mode は MVP-4+ |
| R-3 | clip CAD low-poly (~30 vertex) で PnP correspondence 不足 (F3) | MEDIUM | mask contour polygon vertex 抽出 (§4.2)、IPPE / AP3P 自動選択 (§4.4) |
| R-4 | clip rotation symmetry で yaw non-unique (F4) | MEDIUM | yaw mod π convention (§4.7)、PCA-based axis pre-compute |
| R-5 | sim-to-real gap (lighting, texture, distortion) (F5) | LOW (本 MVP-3 sim-only) | T-Vision-DR leaf scope、Charuco real-cal pre-req (§2.2) |
| R-6 | N-dependency (Newton VBD vectorized batch) | LOW | per-world isolation contract (CC4 v3.2 §5.1)、batched cv2.solvePnP per-world iter |
| R-7 | SAM2 install + checkpoint download 失敗 | LOW | §3.5 install spec、MVP-0 phase で fact-finding 1 day |
| R-8 | clip USD parse path (UsdGeom.Mesh) が Newton-side で利用不能 | LOW | offline pre-compute → npz cache (§4.1)、runtime UsdGeom 不要 |
| R-9 | RANSAC inlier count < 4 で pose 不能 | MEDIUM | fallback to mask centroid + axis (§4.2 row 3)、regime=FALLBACK 通知 |
| R-10 | benchmark scene generator (§7.1) が clip-visible scene を保証できない | HIGH | sample_clip_visible_wrist_pose の rejection sampling、failure 時 scene_id を skip + log |

## §9 Open questions

| OQ | topic | status | trigger |
|----|-------|--------|---------|
| OQv2-1 | wrist_L FOV insufficient → overhead camera 追加 (Newton env change、L3) | Rs 判断待ち、§7.6 visibility gate 結果次第 | MVP-1 後 visibility rate 計測完了 |
| OQv2-2 | SAM2 ViT-B vs ViT-L 選択 (latency vs precision tradeoff) | MVP-1 で両者比較 benchmark 推奨 | MVP-1 起動時 |
| OQv2-3 | clip USD vertex set vs richer feature set (texture / normal / curvature) 採用 | MVP-2 で PnP correspondence 充足度を観察、不足時 feature 拡張 | MVP-2 結果次第 |
| OQv2-4 | distilled mode (online policy 用) を MVP-4 で着手するか defer | OQ-2 (AC-only MVP-3) と整合、MVP-4 trigger 経 | MVP-4 起票時 |
| OQv2-5 | T-Vision-CableState (L1.A.2) との integration: 本 path は clip 7D only、cable 7D は別 path で provider | T-Vision-CableState 別 leaf、本 path scope 外 | T-Vision-CableState impl 起票時 |
| OQv2-6 | real-cam Charuco calibration script 起票 (T-Vision-DR Tier 2 trigger) | OQ-6 と同 deferred | sim-to-real PoC trigger 経 |
| OQv2-7 | symmetry yaw mod π convention と RL policy obs 整合 (policy が full 2π を期待する場合) | RL policy obs design 確認必要 | MVP-3 後の AC fine-tune (CC4 v3.2 §6 Appendix E migration) 起動時 |

## §10 Cross-references

### Parent / sister leaves
- Parent leaf: `[[T-Vision-Pose]]` (本 path の deliverable target = MVP-3 milestone)
- Sister leaf 1 (cable state): `[[T-Vision-CableState]]` (Cosserat rod path 維持、本 alt path で置換しない)
- Sister leaf 2 (DR): `[[T-Vision-DR]]` (sim-to-real Tier 0-2 curriculum、本 path Charuco 統合は Tier 2 trigger)
- Sister leaf 3 (Fusion): `[[T-Vision-Fusion]]` (Phase 5-4 G8 obs 統合、本 path output を AC obs[16:30] / [30:42] 推奨 path と統合)

### CC4 v3.2 base design
- `[[PoseEstimation-Design-v3.2]]` (685 lines、CC4 v3.2 spec、9 OQs Rs approval pending — 本 design memo §6 で resolution plan)
- `[[PoseEstimation-Design-v3.1]]` (12-point patch + §15 addendum)
- `[[PoseEstimation-Design-v3]]` (post-debate parent、1416 lines)

### Existing impl artifacts (reusable)
- `thread_isaac_lab/estimators/types.py` — EstimatorInputs / EstimatorLabelsForEvalOnly (R6 boundary、本 path も流用)
- `thread_isaac_lab/estimators/input_adapter.py` — PoseEstimatorInputAdapter (Newton wrist camera bridge、本 path も流用)
- `thread_isaac_lab/estimators/core/segmenter.py` — LightUNet (本 path で SAM2 distillation の student model 候補、MVP-4+)
- `thread_isaac_lab/scripts/eval_pose_estimator_mvp0a.py` — eval framework template (本 path eval_pose_v2_alt.py の base)
- `thread_isaac_lab/scripts/eval_deterministic.py` — eval-det runner template (NEWTON_DEVICE + policy.eval + torch.no_grad)

### Vault knowledge (camera + spec)
- `[[LL-Vision-L1A-Architecture]]` — sister design reference (204 lines、3 sub-task architecture)
- `[[LL-VisualObs-CameraSystem]]` — Newton wrist camera spec
- `[[Vision Pipeline]]` (04-Specs、R6 4-stage skeleton、Rs専権、参照のみ)
- `[[Camera Backend]]` (04-Specs、Phase 2 RGB+depth)

### Assets
- Clip CAD: `/home/rlrk/IsaacLab/data/clip/routing_clip_v1.usd` (~30 vertex、§4.1 で parse)
- SAM2 checkpoint (将来配置): `/home/rlrk/IsaacLab/data/sam2_ckpt/sam2_hiera_base_plus.pt`
- Camera calibration cache: `data/camera_calibration/<camera_id>.json` (§2.3 schema)

### Related task / RL
- `[[SOMA]]` — L0 / L1 / L2 goal definition、本 path は L1.A.1 leaf MVP-3
- Phase 5-4 G8 path: T-Vision-Fusion umbrella、本 path output は Fusion で AC obs に統合
- `RL-Routing-Design.md §4` — 45D base model input contract (OQ-5c 共有)

---

**Created:** 2026-05-03
**Status:** Design draft、Rs approval pending (主要 decision: §6.1 (a)/(b)/(c) 選択)
**Owner:** T-Vision-Pose-Design-CC (sub-session of T-ROOT-COORD)
**Next action:** Rs disposition on §6.1 path selection + §7.6 visibility gate empirical measurement (MVP-1 phase)
