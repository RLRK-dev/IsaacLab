---
status_ledger: 00-DESIGN-STATUS-LEDGER.md  # authoritative success/failure status SSOT
title: Pose Estimation Design v1 — obs[16:29] Replacement via Wrist Camera RGB-D + Joint State
created: '2026-04-25T06:00:00+09:00'
tags:
  - design
  - vision
  - pose-estimation
  - cable
  - clip
  - msa-42d
  - sim-to-real-prep
  - parked-vision-stack
status: 🟡 SUPERSEDED by v2 (2026-04-25、Rs Option X2、CC Debate 完了) — v3 revision in-flight
owner: CC#4 (session 2026-04-25, pose estimation research)
superseded_by: "[[PoseEstimation-Design-v2]]"
related:
  - "[[Vision Pipeline]]"
  - "[[Camera Backend]]"
  - "[[Vision Stack Roadmap]]"
  - "[[DLO Research Survey]]"
  - "[[LL-VisualObs-CameraSystem]]"
  - "[[RL-Routing-Design]] §4"
  - "[[SOMA]] R6"
  - "[[SUBLIMATE]]"
---

# Pose Estimation Design v1 — obs[16:29] Replacement via Wrist Camera RGB-D + Joint State

> **Status:** Proposal / 承認待ち。本 doc は研究 + design のみ。実装は承認後別 session で起票 (instruction `/tmp/cc_pose_estimation_instruction.md` §Scope 準拠)。
> **Scope reassurance:** 本 design は **sim-only Phase 5 継続中の準備 design**。実機検証・env 改変・訓練実行は本 session 対象外。

---

## §1 Problem statement + scope

### §1.1 現行 obs 42D の観測経路

`thread_isaac_lab/thread-vault/07-Design/RL-Routing-Design.md` §4 (line 727-747) で定義される obs 42D のうち、13D (`obs[16:29]`) は **sim ground-truth body state を直接読む**:

| Index | 特徴量 | 次元 | 現行取得経路 |
|---|---|---|---|
| 16-18 | target seg 位置 XYZ | 3D | Newton `state.body_q[target_seg_idx][:3]` 直読 |
| 19-22 | target seg 姿勢 quat (xyzw, w>0) | 4D | Newton `state.body_q[target_seg_idx][3:7]` 直読 |
| 23-25 | 現ターゲット clip 位置 XYZ | 3D | `task_config.py` CLIP1_POS 等定数 + routing index |
| 26-29 | 現ターゲット clip 姿勢 quat | 4D | 同上 (clip は fixed quat) |

本 13D を **on-hand wrist camera RGB-D + arm joint state** からの推定量に置換するのが本 design の mission。

### §1.2 なぜ必要か (原因仮説の裏付け — prohibited.md 「解法比較の前に原因仮説を裏付けよ」)

現行設計の 3 つの構造的 blocker:

1. **Sim-only artifact:** 実ロボット移行時 cable/clip pose は **motion capture or 視覚推定** が必要。現 obs 経路は sim 内 ground-truth 読み取りに依存、実機で代替手段がない。
2. **Perception noise の学習上の欠如:** training distribution に perception noise を含めておらず、estimator 付きの実機分布への zero-shot transfer が難しい。Real2Sim2Real (DLO Research Survey §追加知見 2026-03-08) は posterior dist DR で対応可だが、本 project では sim-side noise injection ゲートが開いていない。
3. **Obs distribution shift:** noiseless GT → noisy estimate への移行は policy robustness の gap を生む。2mm 級 (T_DIST) の精密操作が要求される task で estimator 誤差分布を DR でカバーしきれない risk。

**注意:** 本 design は sim-only Phase 5 継続中の **準備 design**。即時 sim-to-real を意図しない。RL/DAPG focus 下で vision stack は parked (`Vision Stack Roadmap`)、un-park 前提の stock として位置付ける。

### §1.3 本 design の scope

| 含む | 含まない |
|---|---|
| obs[16:29] 13D の推定置換方式 (4 option + trade-off + 推奨) | 実装コード生成 (design doc 内 pseudocode は OK) |
| 既存 wrist_camera_manager.py の extras["visual_obs"] 上層として設計 | wrist_camera_manager.py 改変 |
| MSA 42D 統合 plan (obs 置換 vs 追加、error obs 再計算) | env / reward / success condition 変更 |
| Newton VBD primary target + PhysX legacy 扱い | 訓練 / eval 起動 |
| 先行研究 + 2025-2026 補強調査 | 実機検証 (sim-only Phase 5) |
| Performance budget (rendering / NN inference cost) | GPU occupation (本 session CPU-only) |
| MVP scope 提案 (1 skill / 1 camera / 1 pose から) | MVP 実装 (承認後別 session) |

### §1.4 R6 (Observation Grounding) との整合性

`thread-vault/04-Specs/Vision Pipeline.md` §R6 補足:

> センサ固有のデコード (画像→幾何量、音→周波数等) に学習を使用することは許容される。ただしデコード出力は物理モデルで制約し (Stage 3)、学習が物理量の定義を変更しないこと。

本 design は Vision Pipeline の 4-stage (WHAT / WHERE / HOW / 予測符号化) を **obs[16:29] への物理量 output として具体化** する位置付け。Stage 1 (学習可: segmentation) と Stage 2-3 (解析的 + 物理モデル) の分離を厳守。

### §1.5 THREAD 固有条件 (全 option 評価で参照)

prohibited.md 「一般解を THREAD 条件で検証せよ」遵守のため、以下を全 option の THREAD 適用欄で検証:

| 条件 | 値 / 内容 | 出典 |
|---|---|---|
| Newton VBD primary (N=32 多 world 検証済) | `env_isaaclab6` venv、`monitor_code_a.sh` 単一ハーネス | `LL-Newton.md`、`project_vbd_multiworld_verified.md` |
| PhysX legacy (N-dependency bug、N>1 で cable tunneling) | 新設計は Newton VBD のみ target | `memory/n_dependency_issue.md` |
| CABLE_BODY_COUNT | 40 (segmented rod)、target は ±1 window | `RL-Routing-Design.md` §2.1、`task_config.py` CABLE_* |
| Wrist camera | L=body 6 / R=body 15 (FRANKA_NUM_JOINTS+EE_BODY_OFFSET)、128² RGB-D、FOV=45° | `wrist_camera_manager.py:23-30` |
| Pixel 精度 | 0.86mm/px @ 133mm 作業距離 | `LL-VisualObs-CameraSystem.md:50` |
| 精度要件 | T_DIST=2mm、T_GROOVE=3mm、EE_TO_FINGERTIP=220mm | `task_config.py:27,167-170` |
| Rendering overhead | W=32 C=2 128² RGB-D = **6%** / step | `LL-VisualObs-CameraSystem.md:93` |
| Policy 規模 | MSA 42D obs、12D action、4 skill (AC/IC/AR/Grip)、DAPG+DR 訓練 | `RL-Routing-Design.md`、`DAPG_DESIGN.md` |
| Clip 配置 | 5 identical clips、X=[0.35, 0.40] 千鳥、CAD 既知 | `task_config.py`、`Vision Stack Roadmap` |

---

## §2 Prior work survey

本 survey は 3 layer:
- **(a) Vault 既存 doc** の compilation (重要)
- **(b) 2023-2024 classical** (training cutoff までの既知手法)
- **(c) 2025-2026 補強** (web search で取得)

### §2.1 Vault 既存 doc (本 design の理論骨格)

| Doc | 要点 | 本 design への寄与 |
|---|---|---|
| `Vision Pipeline.md` (04-Specs) | 4-stage 脳由来 pipeline: Stage 1 WHAT/ventral (RGB→seg/state、学習可)、Stage 2 WHERE/dorsal (seg+depth→3D point cloud、解析)、Stage 3 HOW/dorsal+物理 (**Cosserat rod fitting**、最小二乗)、Stage 4 予測符号化 (Phase 依存頻度) | **Option C (hybrid) の理論骨格既存**。本 doc は Stage 3 の obs 13D 統合具体化 |
| `Camera Backend.md` (04-Specs、Completed) | 3 camera 赤ボール: RGB 色フィルタ → 2D 重心 → Depth 逆投影 → world 変換 → 3 camera median fusion。avg 4.10cm / max 5.62cm | **Option A の precedent**。ただし誤差 ~4cm は T_DIST=2mm 要件を 20 倍下回る。cable には物理制約必須 |
| `Vision Stack Roadmap.md` (04-Specs、Parked) | 5-stage roadmap: Stage 1 赤ボール (完了) → Stage 2 ケーブル seg + 3D 再構成 (未着手) → Stage 3 画像潜在 World Model (Dreamer/CEM-MPC 全失敗) → Stage 4 VLM → Stage 5 汎用 | **本 design は Stage 2 の un-park 準備**。Stage 3 失敗経緯は WMR 経路回避の根拠 |
| `DLO Research Survey.md` (05-Thinking) | Audi Next2OEM、航空機ハーネス、ICLR 2026 微分可能 DLO sim、Task-Level ILC (1 demo + 10 試行 100%)、Real2Sim2Real DLO、WireFishing-M、VLM 統合 92.5% | Option D (differentiable rendering) の実現可能性 + Option B (Foundation Model) の参考。Phase D 長期候補 |
| `LL-VisualObs-CameraSystem.md` (06-Knowledge、Phase 2 完了) | W=32 C=2 128² RGB-D 6% overhead、Phase 3 debt: frozen encoder (R3M/ResNet-18) → 64-128D → state concat。統合 path A (env-side encoder) / B (ActorCriticCNN) / C (SkillAdapter extra_obs) | **rendering infra + 統合 path 既整理**。本 design は estimator 出力を obs 置換 pattern として使う (Phase 3 debt の具体化) |

### §2.2 Classical (cutoff 2026-01 までの確立手法、本 design に関連するもののみ)

| 手法カテゴリ | 代表手法 | 本 design での位置付け |
|---|---|---|
| CAD-based 6DoF | PoseCNN (RSS 2018)、DenseFusion (CVPR 2019)、FFB6D (CVPR 2021)、DREAM (ICRA 2020、Franka camera-to-robot calib、50K img) | clip (CAD 既知) への Option A 適用候補。cable (CAD 不定) には不適 |
| Keypoint + PnP | OpenPose、PVNet (CVPR 2019) | 汎用、cable の keypoint 定義が難しい (segmented rod で定義多義) |
| Pure visual encoder | R3M (NeurIPS 2022、2048D、Ego4D、12-task benchmark +20%/+10% vs CLIP/MoCo)、VC-1 (NeurIPS 2023、ViT-L)、VIP (ICLR 2023、value-implicit)、H-InDex (NeurIPS 2023、hand-centric) | Option B 候補。R6 対応は frozen backbone + state concat (LL-VisualObs-CameraSystem 統合 path A) |
| DLO shape from vision | MIT CSAIL Cable Following (2020、tactile + vision)、Yan et al. rope state estimation (ICRA 2020) | Cable geometry prior を利用、本 design §3C の参考 |
| Cosserat rod physics | Elastica (cosseratrods.org)、CORDE (SIGGRAPH 2008) | 物理的 fit の computational backend、本 design §3C Stage 3 |
| Differentiable rendering | nvdiffrast (NVIDIA、SIGGRAPH 2020)、BRDFdiffrast、GANs-N-Roses | Option D backend、photometric loss 通用 |

### §2.3 2025-2026 補強 (web search、2026-04-25)

| Paper / Project | 要点 | 本 design への示唆 |
|---|---|---|
| **Deep Learning-Based Object Pose Estimation: A Comprehensive Survey** (IJCV 2026, [CNJianLiu/Awesome-Object-Pose-Estimation](https://github.com/CNJianLiu/Awesome-Object-Pose-Estimation)) | 2024-2026 の包括 survey、rigid object 主 | clip pose (rigid) への最新手法 reference |
| **GoTrack: Generic 6DoF Pose Refinement and Tracking** (CV4MR 2025、Meta) | CAD-based refinement/tracking、unseen object、2D projection alignment | Option A (clip、CAD 既知) の直接参考。cable には非対応 |
| **Pose-Perceptive Convolution** (PMC 2026) | geometric-aware 受容野、aspect ratio + sampling density 適応 | Option B/C の backbone 候補 |
| **Enhanced RGB-D Feature Extraction for 6D Pose** (Nature Scientific Reports 2026) | dual-branch appearance + geometry、hierarchical fusion、keypoint vector-field | Option B/C の backbone 候補 |
| **DD-PINN for Cosserat Rod** (continuum robot、2025) | physics-informed NN surrogate、**44,000x speed-up**、70Hz GPU、3mm 誤差 | Option C Stage 3 の実装候補 (Cosserat fit を NN surrogate で高速化) |
| **Training-Free Robot Pose using Foundational Models** (arXiv 2024-2025) | Foundation Model zero-shot pose | Option B の long-term 候補 (Phase D VLM 統合と合流) |
| **VLM 統合 DLO ルーティング** (2025-10 preprint、DLO Research Survey) | VLM 計画 + RL skill + 失敗回復、総合 92.5% | Layer 3 将来統合 (本 design 射程外だが §8 で言及) |
| **WireFishing-M dataset** (Harvard Dataverse) | Franka Panda + Allegro + DIGIT、触覚+視覚+proprioception multi-modal | 本 THREAD と同一ハードウェアクラス、表現学習育成可 |

**ギャップ発見:** 「segmented cable (VBD rod) に対する RGB-D 6DoF pose estimation の 2025-2026 個別論文」は限定的。Cosserat rod fitting が依然 DLO state estimation の primary。本 design Option C は **既存 Vision Pipeline §Stage 3 + DD-PINN 高速化** で gap を埋める構図。

---

## §3 Architecture options + trade-off

以下 4 candidate を THREAD 固有条件 + R6 整合 + MVP-ability で比較。

### §3.A Option A: Pure Geometric (CAD + ICP for clip、skeletal tracking for cable)

**核心原理:** 既存 CAD (clip) / segmented geometry (cable) を depth 逆投影点群に対して analytical fit。学習 component なし。

**Clip 推定 (obs[23:29]):**
1. wrist_L/R depth → 世界座標 pointcloud
2. 事前定義 5 clip CAD mesh (task_config.py CLIP1-5_POS から placement 既知) → CAD-based ICP で各 clip mesh を pointcloud に fit
3. routing state から target clip index → 対応 ICP 結果を obs[23:29] に写像

**Cable 推定 (obs[16:22]):**
1. cable 色/class-based semantic seg (Isaac Sim native segmentation or trained SAM2)
2. Cable-masked depth → 3D pointcloud (rope skeleton)
3. Skeleton extraction (e.g., neighbor graph 上の shortest path)
4. 40 body segment の geometry を cable radius 4mm + 各 seg length から **sliding ICP** で逐次 fit → body_q 推定
5. routing plan の target seg index (C1 L_n=26 / R_n=34 等) → 対応 seg pose を obs[16:22] に写像

**R6 準拠:** ✅ 全 stage 解析的 (Stage 1 segmentation のみ学習許容、残りは物理モデル)
**THREAD 条件適合:**
- Newton VBD: ✅ 適合 (VBD body_q は seg pose 真値、fit 誤差 only)
- N=32: △ ICP は per-world 独立、batched 対応不明瞭 (Warp kernel 化要)
- ±1 window: ✅ routing index から直接 lookup
- Multi-cable (AR): ⚠ L/R arm が異なる seg を追跡、occlusion で seg loss risk
- Grip 中 occlusion: ❌ wrist camera が finger 近傍、cable が finger で遮蔽される可能性高
- Precision: △ Camera Backend 赤ボール実績 4cm vs T_DIST=2mm は 20倍 gap、sliding ICP + 物理制約で近づく可能性あり

**Pros:**
- R6 完全準拠 (学習 component 最小)
- Out-of-distribution 汎化が sim-to-real で比較的強い (domain gap が texture 等にほぼ無依存)
- Isaac Lab + Newton sensor API で segmentation output 直接取得可 (sim の正解系)
- Implementation cost 最低 (既存 Camera Backend pipeline + CAD ICP library)

**Cons:**
- Occlusion 対策が弱い (grip 中 finger 遮蔽で cable seg loss)
- Precision 2mm 到達に sliding ICP + Cosserat rod constraint の複合必要、単純 ICP では不十分
- Clip 5 個中どれが target かは routing state 外部依存、estimator 側判定不可 → architectural 制約

**Impl 工数推定:** 実装 2-3 週間 (既存 Camera Backend infra 転用 + ICP library statically integrate + Warp batched fit)

### §3.B Option B: Pure NN (frozen visual encoder + joint state → 13D pose)

**核心原理:** frozen encoder (R3M / VC-1 / H-InDex) で画像 encoded、arm joint state と concat して MLP で 13D pose を出力。

**Architecture:**
1. wrist_L RGB (3×128×128) → R3M encoder → 2048D feature_L
2. wrist_R RGB → R3M encoder → 2048D feature_R
3. arm_L joint state (9D pos + 9D vel = 18D) + arm_R (18D) → total 36D proprioception
4. concat [feature_L, feature_R, proprio_36D] → 4132D
5. MLP (4132 → 1024 → 512 → 13D pose output)

**Training:**
- supervised regression on sim data (obs[16:29] GT が label)
- DR: lighting / texture / camera noise / proprioception noise
- Loss: weighted L2 on pos + quat_dist on quat (double-cover aware)

**R6 準拠:** ❌ 物理量 (pose) を学習のみで推定、Stage 2-3 の解析的 + 物理モデル原則に反する
**THREAD 条件適合:**
- Newton VBD: ✅ 適合 (pose ground truth label が作れる)
- N=32: ✅ batched GPU forward (frozen backbone なら軽量)
- ±1 window: △ NN が target seg 選択を内部で学ぶ必要、routing index も入力必須 (+1D)
- Multi-cable: △ NN の汎化に依存
- Grip 中 occlusion: △ NN は occlusion-robust 傾向あり (training DR で覆える)
- Precision: ⚠ NN regression の精度は training data 量 + DR 設計依存、2mm 保証困難

**Pros:**
- End-to-end training で occlusion / texture 変動への robust
- 既存 manipulation RL policy と同じ frozen encoder pattern (LL-VisualObs-CameraSystem §統合 path A の拡張)
- Inference fast (< 5ms/step on GPU)

**Cons:**
- **R6 原則違反** (SUBLIMATE 設計原則に矛盾)
- Sim-to-real gap (texture / lighting) が大きい、Real2Sim2Real DR で posterior dist 同定必要
- Precision 2mm 保証が困難 (training data に infinite resolution がない限り NN 誤差 ≥ 数 mm)
- Training cost 大 (sim episode 数 × step 数 × camera update 6% overhead)
- Blackbox、failure mode diagnosis 困難

### §3.C Option C: Hybrid (NN seed + Geometric/Physical refine) — **推奨 (§4 詳述)**

**核心原理:** Option A + B の補完。Stage 1 (学習) で seg mask、Stage 2 (解析) で depth 逆投影、Stage 3 (物理) で Cosserat rod + CAD ICP、Stage 4 (予測符号化) で temporal consistency。Vision Pipeline §4-stage の具体化。

**Architecture:**
1. **Stage 1 WHAT/ventral (学習可):** wrist RGB → segmentation NN (SAM2 fine-tune or light U-Net) → {cable_mask, clip1_mask, ..., clip5_mask, background}
2. **Stage 2 WHERE/dorsal (解析):** mask-filtered depth → per-pixel 3D world coord (camera-to-world from body_q + LOCAL_POS offset)
   - Cable points: 全 wrist_L/R 両 camera 合算、2 view で triangulation 強化
   - Clip points: per-clip に分離、L/R 両 camera 合算
3. **Stage 3 HOW/物理モデル (解析):**
   - **Cable:** Cosserat rod fit (40 seg の sequential geometry constraint: seg length + bend/stretch energy minimization)。DD-PINN surrogate で 44000x 高速化候補 (2025 論文)。出力 = 全 40 body pos + tangent → routing index lookup で target seg [16:22]
   - **Clip:** per-clip CAD-based ICP (GoTrack 2025 pattern、5 clip は同一 CAD mesh の replication) → 5 transform → routing index lookup で target clip [23:29]
4. **Stage 4 予測符号化:** 前フレーム推定値 + MSA internal model の予測値 → |予測 - 新規| > 閾値 で Stage 1-3 再実行、≤ 閾値 で予測値採用 (Phase 依存頻度: 把持中 50ms/1回、移動中 200ms/1回)

**R6 準拠:** ✅ Vision Pipeline §R6 補足完全整合 (Stage 1 seg のみ学習、Stage 2-3 解析 + 物理)
**THREAD 条件適合:**
- Newton VBD: ✅ Cosserat rod と VBD rod は直接対応 (seg 数 + geometry 一致)
- N=32: ✅ stage 1 NN forward batched、stage 2-3 Warp kernel 化で batched 対応
- ±1 window: ✅ routing index で直接 lookup (Stage 3 出力の部分抽出)
- Multi-cable: ✅ Cosserat 全 seg 推定後、L/R の target seg を routing plan から独立選択
- Grip 中 occlusion: △ Stage 3 物理制約で occluded seg を補完可 (rod continuity が強い prior)、ただし完全遮蔽 seg は fit 不可
- Precision: ✅ 物理モデル制約下の LSQ fit で 2mm 近接可能性高 (DD-PINN 先行事例 3mm 実績)

**Pros:**
- R6 完全準拠 (SUBLIMATE alignment)
- Occlusion robust (物理制約で補完)
- Sim-to-real transfer 有利 (Stage 2-3 は domain independent、Stage 1 seg のみ DR で覆う)
- Precision 高い (物理 prior が NN regression を上回る傾向)
- Debug 可能 (各 stage 分離、failure mode diagnose 容易)

**Cons:**
- Implementation 工数最大 (Stage 1-4 独立実装 + integration)
- Stage 3 Cosserat fit の computational cost (DD-PINN で mitigate)
- Stage 4 predictive coding 導入で complexity 増
- SAM2 等大型 seg model 使用時は GPU memory 圧迫 (ただし light U-Net 代替可)

**Impl 工数推定:** 3-5 週間 (Stage 1 seg model light U-Net fine-tune 1-2 週、Stage 2 warp kernel 数日、Stage 3 Cosserat + ICP 1-2 週、Stage 4 predictive coding 数日、統合 1 週)

### §3.D Option D: Differentiable Rendering (photometric loss + CAD + Cosserat)

**核心原理:** 既知 geometry (CAD clip + 40 seg cable) を differentiable renderer (nvdiffrast 等) に通し、rendered RGB-D vs 実 RGB-D の photometric loss を最小化する pose 変数を勾配法で解く。

**Architecture:**
1. State: [clip1-5 transform (5×7D), cable 40 seg pos+quat (40×7D)] — 推定変数
2. nvdiffrast で state → rendered RGB-D (wrist_L/R 両 view)
3. Photometric loss = ||rendered - observed||² (per pixel、mask 重み付け) + regularization (seg continuity、CAD fixed shape)
4. SGD / LBFGS で state を最適化、収束状態を obs[16:29] として export

**R6 準拠:** ✅ Stage 2-3 相当 (学習なし、optimizer のみ)
**THREAD 条件適合:**
- Newton VBD: ✅
- N=32: ⚠ per-world optimizer が重い、batched 対応で GPU memory 爆発 risk (40 seg × 32 world × rendering)
- ±1 window: ✅ index lookup
- Multi-cable: ✅ 全 seg 同時最適化
- Grip 中 occlusion: △ mask 重み付けで occluded seg の loss contribution を下げれば fit 可
- Precision: ✅ 極めて高 (photometric alignment の幾何精度 pixel-level = 0.86mm)

**Pros:**
- Precision 最高 (pixel-level alignment)
- R6 準拠
- Geometry 変更 (CAD 変更等) に柔軟 (新 CAD 差し替えのみ)
- Occlusion mask weighting で robust

**Cons:**
- **Computational cost 最大** (N=32 world × 40 seg × per-step optimization → 100ms+ / step 現実的 risk)
- Rendering infra が Newton built-in renderer と別系統 (nvdiffrast CUDA kernel vs Newton Warp sensor)
- Local minima risk (initial pose から出発、converge 保証なし → seed に Option C Stage 1-3 必要、事実上 hybrid)
- Implementation 工数最大 + debug 困難

**Impl 工数推定:** 5-8 週間 + 性能 tuning 不確定

### §3.E Trade-off matrix (Option A-D × 8 評価軸)

| 評価軸 | Option A (Pure Geometric) | Option B (Pure NN) | Option C (Hybrid) | Option D (Diff Render) |
|---|---|---|---|---|
| R6 準拠 | ✅ | ❌ | ✅ | ✅ |
| Newton VBD 整合 | ✅ | ✅ | ✅ | ✅ |
| N=32 batched | △ (Warp kernel 要) | ✅ | ✅ (Warp kernel 要) | ⚠ (GPU 圧迫) |
| ±1 window 対応 | ✅ | △ (routing index 入力要) | ✅ | ✅ |
| Multi-cable (L/R 独立) | ⚠ | △ | ✅ | ✅ |
| Grip 中 occlusion | ❌ | △ | △ (物理 prior) | △ (mask weighting) |
| Precision (2mm 要件) | △ (20倍 gap base、improve 要) | ⚠ (NN 誤差 ≥ mm) | ✅ (物理 prior) | ✅ (pixel-level) |
| Sim-to-real transfer | ✅ | ⚠ (domain gap 大) | ✅ (Stage 1 seg のみ DR) | ✅ |
| Implementation 工数 | 2-3 週 | 2-3 週 (+training) | 3-5 週 | 5-8 週 |
| 性能予算 (ms/step) | ~5-15ms | ~3-10ms | ~10-25ms | ~50-100ms+ |
| Debug 容易性 | ✅ | ❌ (blackbox) | ✅ (stage 分離) | △ |
| Failure mode transparency | ✅ | ❌ | ✅ | △ |

### §3.F 確証バイアス check (prohibited.md 「確証バイアス禁止」遵守)

各 option の **否定証拠 (なぜこれが fail しうるか)** を明示:

- **Option A fail シナリオ:** 赤ボール Camera Backend の 4cm 誤差が cable 要件 2mm の 20 倍超。sliding ICP + Cosserat 制約で近づけるが、cable 色が clip/table と似た texture の場合 seg 失敗 → point cloud quality 不足 → fit 誤差膨張
- **Option B fail シナリオ:** R3M ベース policy の sim→real 移行で domain gap 10-20% success rate drop は複数論文で観測 (DLO Research Survey §ICRA 2025 DLO Workshop)。THREAD の 2mm 精密操作に adequate かは未実証
- **Option C fail シナリオ:** Stage 3 Cosserat fit が ill-conditioned な場合 (例: cable が straight で curvature 0 → rod orientation degeneracy) の数値不安定。Stage 4 predictive coding が stale 予測で遅延 risk
- **Option D fail シナリオ:** photometric loss の local minima (cable seg が swap されて fit) + N=32 world での GPU memory budget 破綻

全 option fail 可能性を列挙したため、§4 推奨は reasoned choice。

---

## §4 Recommended option + rationale — **Option C (Hybrid)**

### §4.1 選定理由

1. **R6 完全準拠** (SUBLIMATE alignment、Vision Pipeline §Stage 3 既存骨格の具体化)
2. **Precision 2mm 到達可能性最高** (DD-PINN + Cosserat rod 先行事例で 3mm 実績、fit 精度は物理 prior 強度に依存するが本 THREAD の VBD 40-seg geometry 既知で有利)
3. **Occlusion robust** (物理 continuity prior が grip 中の部分遮蔽を補完)
4. **Debug 容易** (stage 分離で failure mode 診断可、prohibited.md 「対処療法禁止」遵守しやすい)
5. **Sim-to-real 移行有利** (Stage 1 seg のみ DR 対象、Stage 2-3 は domain independent)
6. **工数 3-5 週** (Option D の 5-8 週より低、Option A/B 2-3 週より若干高いが性能 / R6 準拠で補償)

### §4.2 No Action 評価 (現行 GT obs 維持で十分か)

**NHA lens (prohibited.md 「複雑化エスカレーション禁止」):** 現行 obs[16:29] GT 直読で 4 skill (AC/IC/AR/Grip) の sim 内成功率は RL-Routing-Progress §最新 update で記録済。**sim-only Phase 5 継続中は現状で task 運用可能**。

**推定置換の必要性:**
- (a) 将来 sim-to-real 移行で不可避 — timeline 未確定、Vision Stack Roadmap 「parked」状態
- (b) Perception noise DR を sim training に導入可能になる — robustness gain あるが現行未実証
- (c) 42D obs の一貫性 (全量 perceivable) 達成 — policy が perceivable only を学ぶため gap 減

**Conclusion:** **即時 impl の justification は弱い**、ただし準備 design として本 doc を保持し、sim-to-real un-park 判断時に rs が fast-track で起票できる position が価値。**本 design 作成自体に対する NHA 判定は CHANGE_JUSTIFIED** (stock value)、**但し impl 起票の priority は rs 判断**。

### §4.3 Option C 内 variant 検討

Option C 内でさらに 3 sub-variant:

| Variant | 説明 | 推奨度 |
|---|---|---|
| C-1 | Stage 1 SAM2 fine-tune (heavy) + Stage 3 full Cosserat | 精度最高、GPU memory 圧迫 |
| C-2 | Stage 1 light U-Net + Stage 3 DD-PINN surrogate Cosserat | **推奨**、MVP 最適 |
| C-3 | Stage 1 Isaac Sim built-in semantic seg (sim only) + Stage 3 full Cosserat | sim-only で simpler、sim-to-real 不対応 |

**推奨:** **C-2** (light U-Net + DD-PINN surrogate、sim + real 両対応準備)。

---

## §5 Integration plan (MSA 42D 統合)

### §5.1 obs 置換 vs 追加の判断

2 方針:

| 方針 | 説明 | Pros | Cons |
|---|---|---|---|
| **置換** (obs 42D 不変、[16:29] 内容のみ GT → estimator) | policy network 形状不変 | network 再訓練不要 (finetune 可)、既存 checkpoint 互換候補 | estimator 誤差が policy に直接伝播 |
| **追加** (新 obs 55D + = GT 13D + est 13D、または新 flag 1D) | policy network 拡大 | estimator disagreement を policy に直接渡せる、uncertainty aware | checkpoint 非互換、全 skill 再訓練 |

**推奨:** **置換方針 + 訓練時 DR で est noise 注入**。checkpoint 互換性高、既存 AC/IC/AR/Grip policy を finetune で adapt 可能性あり (DAPG+DR pipeline 活用)。

### §5.2 Training pipeline 修正点

DAPG+DR 設計 (`DAPG_DESIGN.md`) + Randomize design を以下拡張:

| Component | 修正内容 |
|---|---|
| Env step | `_compute_obs_batch` 内で estimator 起動、obs[16:29] を est output で置換 |
| DR (Domain Randomization) | 新 DR 項目: estimator noise (sim 内 GT pose に σ_pos / σ_ori を add して estimator をシミュレート、または実 estimator を起動) |
| Training loss | 変更なし (obs 形状不変で policy loss 不変) |
| BC demos | 既存 demos は GT obs で生成済 → estimator post-hoc applied or regenerate with estimator。**初期は前者 (post-hoc)、stable 後に後者** |
| Reward | 変更なし (Section 4 reward は hand/target の相対 error を使用、obs で計算) |

### §5.3 Error obs [30:41] 再計算の誤差伝播

obs[30:41] 12D (L/R axis-angle + pos error) は **推定 pose から再計算される**:

```
obs[30:32] = axis_angle(quat_diff(hand_R_quat, est_seg_quat))
obs[33:35] = hand_R_clamp_pos - est_seg_pos
obs[36:38] = axis_angle(quat_diff(hand_L_quat, est_seg_quat))
obs[39:41] = hand_L_clamp_pos - est_seg_pos
```

**誤差伝播:**
- ε_pos on est_seg_pos → ε_pos 直接 propagates to obs[33:35] / obs[39:41] (linear)
- ε_quat on est_seg_quat → ε_quat が axis-angle space で propagation (quat_diff の非線形性考慮)

**Mitigation:**
- Training-time DR で est noise 分布 σ を ε estimator の実測誤差 (Option C で ~2-5mm / ~0.02-0.05 rad 予想) に設定
- Error obs 計算の quaternion double-cover flip guard は wrist_camera_manager 既存実装と同様 temporal consistency check 継続

### §5.4 N-dependency 適合性 (Newton VBD)

- Newton VBD W=32 は `project_vbd_multiworld_verified.md` で検証済 (全 pass、~55 FPS)
- Estimator 追加分: Stage 1 NN forward (batched on GPU)、Stage 2-3 Warp kernel (batched)、Stage 4 per-world independent
- 期待: 既存 6% rendering overhead + estimator = **~10-12% total overhead**、W=32 維持可

---

## §6 Performance budget

### §6.1 Rendering + Estimator breakdown (W=32 C=2 128² target)

| Stage | 所要 ms/step (W=32) | GPU memory | 出典 / 推定根拠 |
|---|---|---|---|
| Camera rendering (既存) | **28.6ms** (C=2 128²) | ~200MB | `LL-VisualObs-CameraSystem.md:93` benchmark |
| Stage 1 seg (light U-Net, 2M params, 128²×2 cam × 32 world) | 10-15ms (estimate) | ~500MB | light U-Net forward batched |
| Stage 2 depth 逆投影 (Warp kernel) | 1-2ms | <100MB | per-pixel 座標計算 |
| Stage 3a Cosserat fit (40 seg, DD-PINN surrogate) | 3-5ms | ~100MB | DD-PINN 先行事例 70Hz ≈ 14ms/frame で non-batched、batched で分摊 |
| Stage 3b CAD ICP on clip (5 clip, 閉形式 SVD) | 1-2ms | <50MB | 閉形式 ICP 先行事例 |
| Stage 4 predictive coding (threshold check) | <1ms | negligible | 差分計算のみ |
| **Estimator 合計** | **15-25ms** | **~750MB** | |
| Physics step | **~450ms** | base | `LL-VisualObs-CameraSystem.md:98` |
| Policy forward | ~5ms | base | MLP 42D→12D |
| **Total step** | **~500ms** (既存 ~478ms の **+4-5%**) | ~1GB add | |

**結論:** 期待 overhead **~10-12% total** (rendering 6% + estimator 4-5%)、budget 許容範囲内。

### §6.2 Training throughput 影響

- 現行 W=32 で ~2.1 Hz step rate (`LL-VisualObs-CameraSystem.md:93`)
- Estimator 追加で ~2.0 Hz へ微減 (<5%)
- 24h training = ~180k steps → ~170k steps で同 epoch 数に接近、許容範囲

### §6.3 GPU claim 設計 (本 design impl 起票時の参考)

- 訓練: cuda:2 (PRO 4000 Blackwell 24GB) — 推奨、現行 AC/IC/AR 訓練割当と整合
- Sim: cuda:0 (A6000 48GB) — 推奨、env 実行、W=32 VBD + 2 camera + estimator = ~8-10GB 見込み
- 同時 process 制約: cuda:0 max 4、estimator 追加で 1 process slot 消費

---

## §7 MVP scope (最小実装単位、承認後別 session impl 起票用)

### §7.1 段階的 MVP (推奨)

| Phase | Scope | 検証基準 |
|---|---|---|
| **MVP-0** (Stage 1 のみ) | wrist_L RGB → SAM2 light fine-tune → cable + 5 clip mask、1 camera、AC env only | seg mIoU > 0.8、per-frame vis 確認 |
| **MVP-1** (Stage 1+2) | 上記 + Stage 2 depth 逆投影 → cable / clip world-frame pointcloud、1 camera、AC env only | pointcloud 密度 > 50 pts/clip、cable > 200 pts |
| **MVP-2** (Stage 1+2+3a) | 上記 + Cosserat fit for cable、40 seg pose 推定、1 camera、AC env only | 推定 pos error < 5mm (medium)、quat error < 0.05 rad |
| **MVP-3** (全 Stage、2 camera) | wrist_L + wrist_R、Stage 1-4 完備、AC env で policy finetune | AC success rate が GT baseline の ≥90% |
| **MVP-4** (全 skill 展開) | IC/AR/Grip にも拡張 | 4 skill 全てで ≥85% baseline |

**MVP-0 ~ MVP-2 までで本 design の技術的実現性が検証可能**、MVP-3-4 は scaling 確認。

### §7.2 MVP-0 実装 scope (初回起票候補)

- 新規 file: `thread_isaac_lab/estimators/pose_estimator_v1.py` (仮)
- 新規 file: `thread_isaac_lab/estimators/segmenter.py` (Stage 1)
- wrist_camera_manager.py **変更なし** (上層 module として estimator を追加)
- env **変更なし** (initial は sidecar tool として起動、eval only)
- 新規 training script: `thread_isaac_lab/scripts/train_segmenter.py`
- 新規 test: `thread_isaac_lab/scripts/eval_pose_estimator_mvp0.py`

### §7.3 Non-MVP scope (別段階、以下は MVP-0 に含めない)

- Stage 3 Cosserat fit (MVP-2 以降)
- Stage 4 predictive coding (MVP-3 以降)
- Policy finetune (MVP-3 以降)
- Real-robot transfer 検証 (当面 sim-only、Phase 5 完了後)

---

## §8 Open questions — Rs 判断要求項目

以下 5 項目は Rs の明示判断を要する。

### OQ-1: Recommended Option の最終選択

**CC 推奨:** Option C (Hybrid)、variant **C-2** (light U-Net + DD-PINN surrogate Cosserat + light predictive coding)

**Rs 判断:** C 採択 or 別 option 推奨 (A-D のいずれか) 再指示

**Trade-off (feedback_tradeoff_in_nchoice.md 準拠):**

| Option | Pros | Cons | Risk | Opportunity cost | Time cost |
|---|---|---|---|---|---|
| A | R6 準拠、工数低 | Precision 到達不確実、occlusion 弱 | Camera Backend 赤ボール 4cm の redux で cable 精度未達リスク | 物理 prior の強みを捨てる | 2-3 週 |
| B | 工数低、occlusion robust | R6 違反、precision 弱 | SUBLIMATE 原則に真っ向から矛盾、sim-to-real 破綻リスク | 物理 prior / R6 を捨てる | 2-3 週 |
| **C (推奨)** | R6 準拠、precision 高、debug 容易 | 工数中、Cosserat fit complexity | Stage 3 ill-conditioned 時の数値不安定 | 工数最適化機会の 1-2 週を捨てる | **3-5 週** |
| D | Precision 最高 | 工数最大、local minima | GPU memory budget 破綻、converge 保証なし | 他 option の同工数内 impl 機会を捨てる | 5-8 週 |

### OQ-2: MVP scope (impl 着手単位)

**CC 推奨:** 段階的 MVP (MVP-0 → MVP-4)、初回起票は MVP-0 (Stage 1 segmenter のみ、1 camera、AC env eval only)

**Rs 判断:** 段階的 OK or 一気に MVP-3 まで or そもそも起票 defer

**Trade-off:**
- 段階的 (推奨): risk 最低、各 phase 検証基準明確、工数 合計 6-10 週
- 一気に MVP-3: 工数短縮 (~4-6 週)、失敗時 rollback 困難
- Defer: Vision Stack が parked 継続、sim-to-real 判断時まで本 doc stock で待機

### OQ-3: DR noise 分布 (σ_pos / σ_ori)

**CC 推奨:** MVP-3 時点の estimator 実測誤差を σ に設定 (adaptive、measurement-driven)。初期候補: σ_pos = 3mm (NN residual 想定)、σ_ori = 0.03 rad (1.7°)

**Rs 判断:** σ 初期値の指示、または MVP-3 で実測後に決定

### OQ-4: 実装優先度 (Phase 5-1 orchestrator との関係)

**現状:** CC#1 coordinator 管理下で Phase 5-1 orchestrator impl (A1+A2+A3 6-8h CC) が進行中 (`handoff_cc1_coordinator_state_2026-04-25.md`)。Option C' BC regen / Option D G3 が並行稼働。

**CC 推奨:** 本 design は **stock 化**、即時 impl 起票せず Vision Stack un-park 判断まで parked 状態で保管。Phase 5-1 + Option C' / D 完了後に Rs 判断で起票。

**Rs 判断:**
- (a) 本推奨通り stock 化 (parked)
- (b) Phase 5-1 と並行で MVP-0 のみ別 CC で起票 (GPU claim cuda:2 share risk)
- (c) Phase 5-1 完了後に sequential 起票
- (d) MVP 全体を rs 外出時 feedback_autonomous_execution_absent_rs.md 準拠で CC 自律進行 (ただし GPU 影響で不推奨)

### OQ-5: Sim-to-real transition PoC の位置付け

**CC 推奨:** 本 session scope 外、Vision Stack Roadmap un-park 判断時の別 session task として defer。MVP-4 完了が前提。

**Rs 判断:** Sim-to-real の PoC 実施 timeline (直近 / mid-term / long-term)

---

## §9 References

### §9.1 Vault (本 doc の主 reference)

- `[[Vision Pipeline]]` — 04-Specs、4-stage 脳由来 pipeline (本 design の理論骨格)
- `[[Camera Backend]]` — 04-Specs、赤ボール pipeline Completed (Option A precedent)
- `[[Vision Stack Roadmap]]` — 04-Specs、Stage 1-5 roadmap (parked 状態)
- `[[DLO Research Survey]]` — 05-Thinking、DLO 研究 2025-2026 survey
- `[[LL-VisualObs-CameraSystem]]` — 06-Knowledge、Phase 2 camera infra benchmark
- `[[RL-Routing-Design]]` §4 — obs 42D / action 12D / reward 仕様
- `[[SOMA]]` — R6 Observation Grounding 原則
- `[[SUBLIMATE]]` — R1-R8 design rules (R6 含む)

### §9.2 Code (SSOT)

- `thread_isaac_lab/configs/task_config.py` — geometry / threshold SSOT (lines 20-170)
- `thread_isaac_lab/envs/wrist_camera_manager.py` — Phase 2 WristCameraManager (Phase 3 debt: encoder 未実装)
- `thread_isaac_lab/scripts/poc_wrist_camera.py` — PoC 検証
- `thread_isaac_lab/scripts/bench_sensor_tiled_camera.py` — benchmark

### §9.3 External (2025-2026 補強、2026-04-25 web search)

- [Deep Learning-Based Object Pose Estimation: A Comprehensive Survey](https://github.com/CNJianLiu/Awesome-Object-Pose-Estimation) (IJCV 2026)
- [GoTrack: Generic 6DoF Object Pose Refinement and Tracking](https://github.com/facebookresearch/gotrack) (CV4MR 2025)
- [Pose-Perceptive Convolution](https://pmc.ncbi.nlm.nih.gov/articles/PMC12845661/) (PMC 2026)
- [Enhanced RGB-D Feature Extraction for 6D Pose Estimation](https://www.nature.com/articles/s41598-025-34757-y) (Nature Scientific Reports 2025)
- [R3M: A Universal Visual Representation](https://openreview.net/forum?id=tGbpgz6yOrI) (NeurIPS 2022)
- [Adaptive MPC of Soft Continuum Robot using PINN + Cosserat](https://arxiv.org/html/2508.12681v1) (DD-PINN 2025)
- [Cosserat Rods / Elastica](https://www.cosseratrods.org/)
- [DREAM Camera-to-Robot Pose](https://www.ri.cmu.edu/app/uploads/2020/03/dream_icra2020_final.pdf) (ICRA 2020)
- [Training-Free Robot Pose Estimation](https://arxiv.org/html/2512.06017v1) (arXiv 2024)

### §9.4 Other vault docs (tangential reference)

- `[[LL-Newton]]` — Newton VBD 制約
- `[[PhysX-N-Dependency]]` — PhysX batched collision bug (legacy)
- `[[project_vbd_multiworld_verified.md]]` (memory) — VBD W=4/8/16/32 全 pass
- `[[Unified Policy Architecture]]` — 3 層 policy 設計

---

## §10 Revision history

| Version | Date | Author | 変更 |
|---|---|---|---|
| v1 | 2026-04-25 | CC#4 (session 2026-04-25) | 初版作成、Rs 判断待ち |

---

## Appendix A: Glossary

- **MSA:** Multi-Skill Agent、THREAD 4 skill 統合 obs 42D policy
- **DR:** Domain Randomization
- **DAPG:** Demo Augmented Policy Gradient
- **VBD:** Vertex Block Descent (Newton solver for cable)
- **DD-PINN:** Domain-Decoupled Physics-Informed Neural Network
- **ICP:** Iterative Closest Point (CAD-based fitting)
- **PoC:** Proof of Concept
- **NHA:** Null Hypothesis Advocate (CC Debate pattern)
- **R6:** SUBLIMATE Observation Grounding rule
- **SSOT:** Single Source of Truth
- **±1 window:** target seg routing plan の ±1 body index 範囲 (robustness)

## Appendix B: Notation

- `obs[a:b]` — inclusive-exclusive Python slice、obs[16:29] は 13 次元
- `quat (xyzw, w>0)` — Newton convention + double-cover guard
- `body_q` — Newton state body transform `[pos(3), quat(4)]` per body
- `W` — world count (parallel batch, up to 32 in Newton VBD)
- `C` — camera count (2 for wrist L+R)

---

**本 design の status:**

- ✅ Design 記述完了 (§1-§10)
- ✅ Trade-off 4 option × 12 評価軸 完了
- ✅ Prior work 3-layer survey 完了
- ✅ THREAD 固有条件の全 option 評価済
- ✅ R6 / SUBLIMATE 整合性 check
- ✅ Rs 判断要求 5 項目 (OQ-1 to OQ-5) 明示
- 🔵 **Rs approval pending** → 承認後 MVP-0 impl 起票 (別 session)

---

**Cross-references:**
- Instruction file (本 session 起動時): `/tmp/cc_pose_estimation_instruction.md` (ephemeral)
- Handoff: `handoff_cc4_pose_estimation.md` (本 session 終了時作成)
- Memory pointer: `~/.claude/projects/-home-rlrk-IsaacLab/memory/project_pose_estimation_design_v1.md`
- Log milestone: `thread-vault/log.md` に追記 (2026-04-25)
- Pending index: `~/.claude/projects/-home-rlrk-IsaacLab/memory/_pending_index.txt` append (CC#1 coordinator merge 待ち)
