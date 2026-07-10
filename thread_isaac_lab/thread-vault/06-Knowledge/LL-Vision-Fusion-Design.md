---
title: Vision-Policy Late Fusion Design (T-Vision-Fusion / L1.A.4 / Phase 5-4 G8)
created: '2026-05-03T23:55:00+09:00'
last_updated: '2026-05-03T23:55:00+09:00'
status: design-draft (Rs ★ batch T-ROOT-COORD#s11 2026-05-03、T-Vision-Fusion-Design-CC sub-session 起草、Pose/CableState/DR 3 leaves APPROVED 2026-05-03 上層 integration design memo)
node_id: T-Vision-Fusion
parent_node: T-Vision (L1.A capability axis)
session: T-Vision-Fusion-Design-CC
spec_version: LTM-1 v1.1
tags:
  - knowledge
  - vision
  - fusion
  - late-fusion
  - phase-5-4
  - g8
  - design-reference
related: '[[LL-Vision-L1A-Architecture]] | [[LL-Vision-Pose-Design]] | [[LL-Vision-CableState-Design]] | [[LL-Vision-DR-Design]] | [[PoseEstimation-Design-v3.2]]'
doc_class: design-surface
---

# Vision-Policy Late Fusion Design (L1.A.4)

> **本 file の位置付け**: T-Vision-Fusion (L1.A.4 / Phase 5-4 G8) の implementation-ready design reference。
> Pose (L1.A.1) + CableState (L1.A.2) + DR (L1.A.3) 3 APPROVED leaves の output を policy obs 50D 統合する Late Fusion architecture、PoseEstimate14D 再構成 (cable seg 7D ← CableState target_seg / clip 7D ← Pose CoreV2)、ObsAssembler env wrapper、4-leaf-↔-Fusion benchmark を定義。
>
> **scope**: design only。impl + train は別 task scope (state.md §4 Active rule + 起票候補 `CC-L1A-Phase-5-4-Impl` per L1.A 9 別 task 起票候補)。
> **base**: L1.A design memo §2 + §5 (`memory/project_l1a_vision_design_complete_2026-04-27.md`)、CC4 v3.2 §6.4 + Appendix E + Appendix H、CableState §6.1 PoseEstimatorCorePhase2、Pose alt path §4.6 PoseEstimate14D contract。
> **boundary**: R6 input-boundary (CC4 v3.2 Appendix D + H) を遵守。Fusion estimator core は env / newton 直 import 禁止、ObsAssembler は env wrapper 層に配置。task_config.py / newton_*_env.py / 04-Specs SSOT 改変禁止 (Rs専権、本 design は 06-Knowledge LL- prefix で配置)。

---

## §0 Executive summary (~6 lines、read-must)

- **Goal**: vision-based 5-clip cable routing SR ≥ 30% on N=10 ep × 5 seeds、cuda:2 deterministic、`eval_skill.py --skill multi_clip --vision` mode (G8 gate、state.md §1 直引き)
- **Architecture**: **Late Fusion (C-2R 拡張)** — Pose CoreV2 (clip 7D) + CableState Solver (cable seg 7D via target_seg_idx 抽出) → **FusionAggregator** で **PoseEstimate14D** 再構成 → **ObsAssembler** env wrapper で 45D→50D obs 拡張 → 既存 AC PPO MLP に **migrate_first_layer_45_to_50** 経で migrate
- **3 alternatives REJECTED** (design memo §2.4): Cross-Attention Fusion (PPO + transformer instability)、End-to-End CNN (existing pose 廃棄、Phase 3 全失敗 precedent)、Direct Concat (Adapter boundary 不在)
- **Bit-identical baseline (E.5 invariant)**: regime=ACCEPT + conf=1.0 + zero-init [45:50] first-layer weight → 50D policy output が 45D baseline と bit-identical (CC4 v3.2 §6.4 + Appendix E.5)
- **Resource**: ~250 LoC + ~45-50h GPU + ~3-5h benchmark wall (state.md §1 + design memo §2.4 整合)
- **Trigger**: 3 leaves COMPLETE (Pose MVP-3 + CableState Q5 + DR Tier 0-1) + T-L1-B Phase 5-3 multi-clip orchestrator ready + T-Skill milestone leaves (per-skill ≥50% floor for AC/IC/AR/Grip-CLAMP) — 全件解消後 Rs §3.1 #4 起動承認

---

## §1 Goal & scope

### §1.1 Target metric (state.md §1 直引き)

| metric | sample size | gate | eval mode |
|--------|-------------|------|-----------|
| 5-clip cable routing SR (vision-based) | N=10 ep × 5 seeds | **≥ 30%** | cuda:2 deterministic、`--skill multi_clip --vision` |
| AC fine-tune value_loss (during P4) | per iter | < 3× baseline @ iter 20 (rollback gate) | training-time monitor、CC4 v3.2 E.6 |
| Bit-identical baseline (regime=ACCEPT + conf=1.0) | exact | 50D policy output == 45D baseline policy output | unit test、E.5 invariant |
| End-to-end latency (Fusion + obs assembly) | per step | < 50ms target (offline benchmark mode) | profile per stage |

### §1.2 In-scope (本 design)

1. **L1.A 4 leaves output spec 整理** (Pose 12D + CableState 40×3D + 40D conf + DR Tier 0-1 training-time augmentation + Fusion 50D obs)
2. **Late Fusion sub-task 1 architecture** (5-stage pipeline、CC4 v3.2 §6.4 + Appendix E 反映)
3. **PoseEstimate14D 再構成 logic** (cable seg 7D ← CableState target_seg / clip 7D ← Pose CoreV2、confidence + regime aggregation)
4. **Downstream env obs hook design** (ObsAssembler env wrapper、obs[16:30] / [30:42] / [45:50] 配置)
5. **Module boundary R6 compliance** (PoseEstimatorCoreFusion 配置、env / newton 直 import 禁止、ObsAssembler は env wrapper 層配置)
6. **4-leaf-↔-Fusion benchmark spec** (G-V0 bit-identical / G-V1 leaf integration / G-V2 obs population / G-V3 PoseEstimate14D 再構成 / G-V4 G8 end-to-end / G-V5 latency)

### §1.3 Out-of-scope (本 leaf 範囲外)

- **Impl + train** — 別 task `CC-L1A-Phase-5-4-Impl` 起票候補 (state.md §4 trigger、本 design memo prescribed structure 経)
- **task_config.py / newton_*_env.py 改変** — SSOT (state.md §4 禁止事項、env file 改変禁止)
- **04-Specs SSOT update** — Rs 専権 (Vault Write Permissions)、Rs 承認後別 task `CC-L1A-04Specs-Update` 起票候補
- **Multi-skill MVP-4 拡張** (AC 以外 IC/AR/Grip-CLAMP) — CC4 v3.2 OQ-2 経 deferred (本 leaf scope は AC-only MVP-3 経 Phase 5-4 G8)
- **Real-hardware deploy** — T-Vision-DR Tier 2 OUT-OF-SCOPE per umbrella state.md OQ2、L1.F.1 sim-to-real trigger
- **WM Cascade retry path 統合** — L1.E.2 Cascade C Nemotron impl downstream、本 design は WM 不在 chain math (per-skill 78% no-retry → 5-clip 30%) を前提

### §1.4 Why Late Fusion (推奨根拠、5 軸)

design memo §2.4 + CC4 v3.2 §6.4 + 7-CC Pre-Debate CC8 KA2 STRONG 整合:

1. **CC4 v3.2 spec exact 整合**: Appendix H module boundary + Appendix E migration (45D→50D zero-init bit-identical) が直接適用可
2. **THREAD precedent 整合**: Dreamer / CEM-MPC 全失敗 (Phase 3) → simpler MLP-policy success precedent (Vision Stack Roadmap §15)
3. **Sim-to-real switch 機構**: `PoseEstimatorInputAdapter` を real-hardware 版に差し替えるだけで vision pipeline 全 sim-to-real 移行可 (Appendix H spec)
4. **Bit-identical baseline 保証**: regime=ACCEPT + conf=1.0 で 45D baseline と bit-identical → fine-tune 起動時 explosive divergence 回避 (E.5 invariant、Appendix E)
5. **Incremental rollout**: MVP-3 から段階導入可、AC-only scope (CC4 v3.2 §6.1) で risk contained、IC/AR/Grip-CLAMP は MVP-4+ 別 trigger

### §1.5 Existing assets (CHECK 結果、grep 証拠 pin)

| Asset | Path | Status | Reuse / Extend |
|-------|------|--------|-----------------|
| 45D AC obs structure | `thread_isaac_lab/envs/newton_approach_cable_env.py:1332` (`# Pad 42D → 45D for unified base model`) | DONE | obs[16:30] + obs[30:42] vision-derived 置換、obs[45:50] 拡張 |
| 45D IC obs structure | `thread_isaac_lab/envs/newton_insert_clip_env.py:1105-1118` (`# Obs (45D)`) | DONE | OQ-5b defer、本 leaf scope 外 (AC-only) |
| 45D Grip obs structure | `thread_isaac_lab/envs/newton_grip_env.py:1011-1012` (`Compute 45D dual-arm observations`) | DONE | OQ-5a defer (Grip dual-arm MVP-4)、本 leaf scope 外 |
| target_seg_indices (R/L per-world) | `thread_isaac_lab/envs/newton_approach_cable_env.py:225-226, 949` (`_target_seg_indices_r/l`) | DONE | Fusion で `EstimatorInputs.target_seg_idx` 経で受領、CableState `positions[:, target_seg_idx, :]` で seg_pos 取得 |
| PoseEstimate14D contract | `thread-vault/07-Design/PoseEstimation-Design-v3.2.md:391, 446, 487` | spec DONE | `[seg_pos(3), seg_quat(4), clip_pos(3), clip_quat(4)]` 14D、本 design で再構成 logic 定義 |
| `migrate_first_layer_45_to_50` | `PoseEstimation-Design-v3.2.md:198-220` Appendix E.4 | spec DONE | bit-identical baseline、zero-init [45:50] 列 |
| `migrate_obs_normalizer_45_to_50` | `PoseEstimation-Design-v3.2.md:151` Appendix E.2 | spec DONE | running stats 拡張 (regime + conf raw pass-through、ε-variance 禁止) |
| `migrate_policy_45_to_50` | `PoseEstimation-Design-v3.2.md:220` Appendix E.6 | spec DONE | full policy migration entry point |
| Estimator types + boundary | `thread_isaac_lab/estimators/types.py`、`input_adapter.py`、`core/pose_estimator_core.py` | DONE (Phase 1) | extend with `PoseEstimatorCoreFusion` composition + `EstimatorInputs.target_seg_idx_r/l` field |
| LightUNet (CC4 base) | `thread_isaac_lab/estimators/core/segmenter.py` | DONE | Pose alt path SAM2 distillation の student model 候補 (post-MVP-3) |

**[CHECK] grep raw output**:
```
$ grep -nE "obs\[|obs_dim|num_observations" thread_isaac_lab/envs/newton_approach_cable_env.py | head -5
1332:        # Pad 42D → 45D for unified base model (IC-compatible). Dims [42:45] = zeros.
$ grep -nE "target_seg" thread_isaac_lab/envs/newton_approach_cable_env.py | head -3
225:        self._target_seg_indices_r = None  # [world_count, n_target_segs] — right arm
226:        self._target_seg_indices_l = None  # [world_count, n_target_segs] — left arm
949:        self._target_seg_indices_r, self._target_seg_indices_l = self._compute_target_seg_indices(bq)
```

### §1.6 SOMA / chain math context

- **L0**: 5-clip routing **vision-based** 95% chain target
- **G8 (本 leaf goal)**: vision-based 5-clip ≥ 30% (per state.md §1 + design memo §2.5)
- **chain math feasibility (no-retry)**: per-skill 78% × 5 = 0.78^5 ≈ 0.29 → ~30% ✅
- **chain math (with WM Cascade retry ×1)**: per-skill 62% sufficient (L1.E.2 Cascade C Nemotron downstream)
- **本 leaf 前提**: per-skill ≥ 50% (T-Skill milestone leaves) + vision noise +5-10pp degradation 想定 → AR / Grip-CLAMP 50%+ 達成依存
- **vision noise budget**: 5-10pp degradation = pose translation residual ~5mm + cable seg residual ~5-10mm の policy 影響、Tier 0-1 DR で吸収 (T-Vision-DR Tier 0 PASS gate equivalence ≤ 5pp 整合)

---

## §2 4 leaves output spec 整理 (integration table)

### §2.1 T-Vision-Pose output contract (L1.A.1)

**source**: `LL-Vision-Pose-Design.md` §4.6 + CC4 v3.2 §3.2

| field | shape | semantic | notes |
|-------|-------|----------|-------|
| `clip_pos_w` | `[B, 3]` float32 [m] | per-clip translation in world frame | from PnP+RANSAC tvec |
| `clip_quat_w_xyzw` | `[B, 4]` float32 unit quat | per-clip rotation in world frame | from cv2.Rodrigues(rvec) → quaternion (xyzw convention) |
| `confidence` | `[B]` float32 ∈ [0, 1] | per-clip pose confidence | RANSAC inlier_count / N (or sigmoid(SAM2 mask conf × inlier_ratio)) |
| `regime` | `[B]` enum {ACCEPT, PREDICT_TEMPORAL, FALLBACK, FAIL_CLOSED} | per-clip regime state | CC4 v3.2 §5.6 Stage 4 state machine、§3.4 temporal smoothing |
| `previous_estimate` (in) | `PoseEstimate14D \| None` | temporal carry-forward | for PREDICT_TEMPORAL / FALLBACK regime |

**alt path 制約 (Pose §0.3)**: 本 path は **clip 7D のみ**を提供、cable seg 7D は L1.A.2 (CableState) 経で別 channel 取得 → Fusion 層で merge (§3.2)。

**eval-det validation**: trans median < 5mm AND yaw median < 10° AND p95 trans < 10 mm AND p95 yaw < 20° on N=100 × 5 seeds (Pose §7.3)。

### §2.2 T-Vision-CableState output contract (L1.A.2)

**source**: `LL-Vision-CableState-Design.md` §6.1 (CableState40 dataclass) + §2.6 (Stage E confidence calibration)

| field | shape | semantic | notes |
|-------|-------|----------|-------|
| `positions` | `[B, 40, 3]` float32 [m] | per-segment 3D world-frame xyz | Hybrid PCA + Cosserat 5-stage、segment 0 = grasp end / segment 39 = far end (§3.5 anchor priority) |
| `confidences` | `[B, 40]` float32 ∈ [0, 1] | per-segment confidence | post-train logistic regression on 5 signals (visibility / density / residual / curvature / temporal)、ECE < 5% target |
| `stage_diagnostics` | `dict` | per-stage debug metrics | Stage A merged_pts、Stage B var_ratio、Stage C/D residual、Stage E ECE、debug only (not policy obs) |

**eval-det validation**: mean(ē) < 5mm AND p95(ē) < 10mm on N=100 random + 10 U-shape + 10 S-shape worst-case (CableState §5.3 Q5 gate)。

**Topology preservation guarantee** (CableState §3): 4-layer defense ensures `positions[0]` corresponds physically to grasp end (post-fit identity inversion check §3.3、L_id anchor §2.5)。Fusion 層で `target_seg_idx` 経の indexing で reliable。

### §2.3 T-Vision-DR output contract (L1.A.3)

**DR は output channel ではなく training-time augmentation strategy** — Fusion module への直接出力なし、ただし以下の orthogonality を保証:

| dim | training-time augmentation | impact on Pose | impact on CableState | impact on Fusion |
|-----|---------------------------|-----------------|----------------------|------------------|
| D1 lighting | ×{0.5, 0.75, 1.0, 1.5, 2.0} intensity + 5-color temp | SAM2 mask robustness ↑ (Pose Stage 1) | HSV mask robustness ↑ (CableState Stage A.1) | downstream policy robustness ↑ (Tier 0c full) |
| D2 texture | 5 preset material variation | SAM2 generalization (offline pre-render) | mIoU stability (offline pre-render) | dataset shared (DR §5.3 coordinator) |
| D3 cable color | 5 preset RGB | SAM2 ROI prompt diverse | HSV preset robustness | dataset shared |
| D4 camera intrinsic | FOV ±5° + principal ±5px + k1 distortion | PnP camera matrix robustness | Stage A.2 back-projection robustness | per-episode ray rebuild、`EstimatorInputs.intrinsics` field 経 propagate |
| D5 sensor noise | depth σ=3mm + 5% dropout + color σ=0.02 | SAM2 mask noise robustness | Stage A.2 cloud noise (voxel downsample で吸収) | obs assembler 層 noise はゼロ (sim-to-real DR scope のみ) |
| D6 background | 10 preset clutter (Tier 1) | SAM2 false-positive 抑制 | mask false-positive 抑制 | training-time only、Fusion arch 影響なし |

**Tier boundary** (DR §3.1):
- **Tier 0a (warm-up)**: D4 + D5 randomized → ~3h GPU
- **Tier 0b (mid)**: + D2 + D3 → ~5h GPU
- **Tier 0c (full)**: + D1 → ~4h GPU、**Tier 0 PASS gate** (sim eval-det SR equivalence ≤ 5pp diff vs no-DR baseline)
- **Tier 1**: + D6 → ~3h GPU、Tier 1 PASS gate
- **Tier 2 (D7 motion blur + D8 self-occlusion + R7 real-cam)**: OUT-OF-SCOPE per umbrella state.md OQ2、L1.F.1 trigger
- **D8 promote trigger** (CC8 KA2 OQ5): Tier 0 fail + opposite-arm self-occlusion dominant → Tier 0 promote (本 leaf 内例外 path)

**Fusion との orthogonality**: DR は Fusion architecture 不変 (training-time augmentation)、Fusion benchmark (G-V4 G8) は **Tier 0c configuration** で実施 (Tier 1 D6 background は別 fine-tune phase)。

### §2.4 Fusion output spec (本 leaf deliverable)

**統合先**: 既存 AC PPO MLP policy の **50D augmented obs** (CC4 v3.2 §6.4 + §6.5)

| obs slice | dim | source | semantic |
|-----------|-----|--------|----------|
| `obs[0:8]` | 8D | env (proprio) | base arm joint state + dual-arm coordination signals (既存) |
| `obs[8:16]` | 8D | env (proprio) | L clamp pos[8:11] + quat[11:15] + finger[15] (既存、OBS_L_ARM_MASK_PROB 経 mask 可) |
| `obs[16:30]` | **14D** | **Fusion** | **PoseEstimate14D = [seg_pos(3), seg_quat(4), clip_pos(3), clip_quat(4)]** (§3.2 再構成、CC4 v3.2 §3.2 contract) |
| `obs[30:42]` | **12D** | **Fusion** | **recomputed pose error** (env target - vision pose 経で計算、§4.3) |
| `obs[42:45]` | 3D | env | structural zero pad (既存、IC-compatible) |
| `obs[45:49]` | **4D** | **Fusion** | **regime one-hot** [ACCEPT, PREDICT, FALLBACK, FAIL_CLOSED] |
| `obs[49:50]` | **1D** | **Fusion** | **confidence scalar** (aggregated from pose_conf + cable_target_conf、§3.4) |
| **Total** | **50D** | — | augmented obs (CC4 v3.2 §6.4) |

**Fusion 提供 dim count**: 14D (obs[16:30]) + 12D (obs[30:42]) + 4D (obs[45:49]) + 1D (obs[49:50]) = **31D Fusion-provided + 19D env-proprio = 50D total**

### §2.5 Aggregation rules (Fusion module 内 logic)

#### §2.5.1 PoseEstimate14D 再構成 (clip + cable seg merge)

```
PoseEstimate14D = concat([
    seg_pos_w,       # (3,) ← CableState.positions[batch_idx, target_seg_idx, :]
    seg_quat_w_xyzw, # (4,) ← computed from CableState tangent (§3.2.2 below)
    clip_pos_w,      # (3,) ← Pose CoreV2 PnP tvec
    clip_quat_w_xyzw # (4,) ← Pose CoreV2 cv2.Rodrigues(rvec) → quaternion
], dim=-1)  # → [B, 14] float32
```

**target_seg_idx source**: env-side `_target_seg_indices_r/l` (per-world、`_compute_target_seg_indices(bq)` line 949 既存) を **`EstimatorInputs.target_seg_idx_r/l` field 経で propagate** (§5.1)。

#### §2.5.2 seg_quat 計算 (tangent-based)

CableState は `positions` のみ提供 (`confidences` は scalar)、segment quaternion は提供しない。Fusion 層で tangent から計算:

```python
def compute_seg_quat_from_tangent(positions, target_seg_idx):
    # positions: [B, 40, 3]、target_seg_idx: [B] int64
    B = positions.shape[0]
    seg_idx = target_seg_idx.clamp(1, 38)  # avoid edge segments
    p_prev = positions[torch.arange(B), seg_idx - 1, :]   # [B, 3]
    p_next = positions[torch.arange(B), seg_idx + 1, :]   # [B, 3]
    tangent = (p_next - p_prev)                           # [B, 3] approximate forward axis
    tangent_normalized = tangent / (tangent.norm(dim=-1, keepdim=True) + 1e-6)
    # Construct quaternion: align local +x axis to tangent (twist convention from cable_target_axis)
    return tangent_to_quaternion(tangent_normalized)      # [B, 4] xyzw
```

**Edge case** (target_seg_idx ∈ {0, 39}): clamp to [1, 38]、edge segment quaternion uncertainty propagated to confidence aggregation (§2.5.4)。

**Twist axis ambiguity**: cable rotation about its own axis is unobservable from positions alone (cylindrical symmetry); Fusion module produces **canonical zero-twist** (right-hand rule with world +z 補助 axis)、env-side reward は cable axis 整合のみ評価 (twist 無視) 整合。

#### §2.5.3 Regime aggregation (most-restrictive)

```
regime_fusion = max_priority({
    pose_regime,                       # from Pose CoreV2
    cable_target_regime,               # from CableState target seg confidence threshold
})

priority order (most-restrictive wins):
  FAIL_CLOSED (3) > FALLBACK (2) > PREDICT_TEMPORAL (1) > ACCEPT (0)

cable_target_regime derivation:
  c_target = confidences[batch_idx, target_seg_idx]
  if c_target ≥ T_high (0.85):     ACCEPT
  elif c_target ≥ T_predict (0.5): PREDICT_TEMPORAL
  elif c_target ≥ T_fallback (0.3): FALLBACK
  else:                             FAIL_CLOSED
```

**Rationale**: 一方の channel が degraded (例: pose ACCEPT だが cable FALLBACK) でも policy には worst regime を提示、policy は obs[45:49] one-hot を解釈し pose 信頼度を down-weight 学習。

#### §2.5.4 Confidence aggregation (geometric mean、min-clamp)

```
conf_fusion = min(pose_confidence, cable_target_confidence) × edge_penalty

edge_penalty = 0.5 if target_seg_idx ∈ {0, 39} else 1.0   # §2.5.2 edge case

conf_fusion ∈ [0, 1] → obs[49] (raw pass-through、CC4 v3.2 §6.4 ε-variance 禁止)
```

**Why min not mean**: bottleneck principle — policy が一方の channel 低信頼を全 fusion-conf に反映する方が defensive、過信防止 (CC4 v3.2 §10 R-3 MEDIUM mitigation)。

**Bit-identical baseline preservation** (§3.5): 通常 inference 時は conf_fusion ≤ 1.0、ただし unit test mode で `force_accept_unit_conf=True` 設定時は conf_fusion=1.0 + regime=ACCEPT 強制 (E.5 invariant 検証用、benchmark §6.1 G-V0)。

#### §2.5.5 Recomputed error (obs[30:42])

CC4 v3.2 §6.4: 既存 obs[30:42] 12D は env-side で proprio + nominal target から計算された error signal。Fusion では vision pose で recompute:

```
# Existing (45D base):
obs[30:33] = nominal_target_pos - ee_pos_r          # 3D pos error
obs[33:36] = ori_axis_angle(nominal_target_quat, ee_quat_r)  # 3D ori error (axis-angle representation)
obs[36:39] = nominal_target_pos - ee_pos_l          # 3D pos error (L arm)
obs[39:42] = ori_axis_angle(nominal_target_quat, ee_quat_l)  # 3D ori error (L arm)

# Augmented (50D, vision-derived):
obs[30:33] = clip_pos_w - ee_pos_r                  # 3D pos error using vision clip pose
obs[33:36] = ori_axis_angle(clip_quat_w, ee_quat_r) # 3D ori error
obs[36:39] = clip_pos_w - ee_pos_l                  # 3D pos error (L arm)
obs[39:42] = ori_axis_angle(clip_quat_w, ee_quat_l) # 3D ori error (L arm)
```

**注**: `clip_pos_w` / `clip_quat_w` は **active target clip** に対するもの (multi-clip routing で current clip index に依存、env-side `current_clip_idx` を `EstimatorInputs` 経 propagate)。

**Bit-identical guarantee**: 通常 fine-tune 中は vision-derived `clip_pos_w` ≠ `nominal_target_pos` (vision noise)、ただし regime=ACCEPT + conf=1.0 + zero-init [45:50] weight で policy output unchanged から fine-tune 可能 (E.5 invariant)。

---

## §3 Late Fusion architecture (sub-task 1)

### §3.1 5-stage pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│ INPUT: EstimatorInputs (R6 boundary、CC4 v3.2 Appendix H)        │
│   - rgb_l, rgb_r, rgb_oh                  [3-cam RGB]            │
│   - depth_l, depth_r, depth_oh            [3-cam depth]          │
│   - wrist_camera_pose_l/r, overhead_camera_pose                  │
│   - intrinsics_l/r, overhead_intrinsics                          │
│   - joint_state                           [proprio for ee_pos]   │
│   - target_seg_idx_r, target_seg_idx_l    [int64、§5.1 NEW]      │
│   - current_clip_idx                      [int64、§5.1 NEW]      │
│   - previous_pose_estimate                [PoseEstimate14D \| None]│
│   - previous_cable_estimate               [CableState40 \| None] │
└──────────────────────────────┬───────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 1: Independent leaf inference (parallel-capable)           │
│  ├─ Pose CoreV2 (LL-Vision-Pose-Design §1.2、Appendix H reuse)  │
│  │    Stage 1: SAM2 mask → Stage 2: 2D feature → Stage 3: PnP    │
│  │    Output: clip_pos_w, clip_quat_w_xyzw, conf_pose, regime_pose│
│  └─ CableState Solver (LL-Vision-CableState-Design §2、§6.2)     │
│       Stage A: 3-cam mask + back-proj → Stage B: PCA + 40-bin    │
│       Stage C: DD-PINN warm start (var_ratio < 0.6)              │
│       Stage D: Cosserat 7-term loss → Stage E: confidence        │
│       Output: positions [B, 40, 3], confidences [B, 40]          │
└──────────────────────────────┬───────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 2: FusionAggregator (本 design 主成果、§3.2)              │
│  - PoseEstimate14D 再構成 (§2.5.1):                              │
│    seg_pos_w   ← positions[:, target_seg_idx, :]                 │
│    seg_quat_w  ← compute_seg_quat_from_tangent(...) (§2.5.2)     │
│    clip_pos_w  ← Pose CoreV2 output                              │
│    clip_quat_w ← Pose CoreV2 output                              │
│  - regime aggregation (most-restrictive、§2.5.3)                 │
│  - confidence aggregation (min × edge_penalty、§2.5.4)           │
│  Output: PoseEstimate14D + RegimeState + conf_fusion             │
└──────────────────────────────┬───────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 3: ObsAssembler (env wrapper 層、§4)                       │
│  - obs[16:30]   ← PoseEstimate14D[:, :14]                        │
│  - obs[30:42]   ← recomputed_error (§2.5.5)                      │
│  - obs[42:45]   ← zero pad (既存維持)                            │
│  - obs[45:49]   ← regime_one_hot (§2.5.3)                        │
│  - obs[49:50]   ← conf_fusion (§2.5.4)                           │
│  Output: obs_50d [B, 50] float32                                 │
└──────────────────────────────┬───────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 4: Policy migration (CC4 v3.2 Appendix E、§3.5)            │
│  - migrate_first_layer_45_to_50 (zero-init [45:50] weight)       │
│  - migrate_obs_normalizer_45_to_50 (raw pass-through regime+conf)│
│  - migrate_policy_45_to_50 (full ckpt migration)                 │
│  Bit-identical baseline @ regime=ACCEPT + conf=1.0 (E.5 invariant)│
└──────────────────────────────┬───────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 5: AC fine-tune (PPO + 50D obs)                            │
│  - target: AC SR ≥ 50%+ floor maintenance under vision noise     │
│  - rollback gate: value_loss > 3× baseline @ iter 20 → fresh-start│
│    (CC4 v3.2 E.6、design memo §6.1 R-3 MEDIUM)                   │
│  - eval gate: G8 5-clip ≥ 30% N=10 ep × 5 seeds (state.md §1)    │
└──────────────────────────────────────────────────────────────────┘
```

**Stage 1 並行性**: Pose CoreV2 と CableState Solver は input (RGB-D + camera pose + previous_estimate) のみ共有、output は独立 → CUDA stream で並列実行可 (latency budget §6.6)。

### §3.2 PoseEstimate14D 再構成 detail (§2.5.1 + §2.5.2 統合)

```python
@dataclass
class FusionAggregatorConfig:
    edge_seg_clamp_min: int = 1                    # target_seg_idx clamp [1, 38]
    edge_seg_clamp_max: int = 38
    edge_penalty: float = 0.5                      # §2.5.4
    regime_threshold_high: float = 0.85            # ACCEPT
    regime_threshold_predict: float = 0.5          # PREDICT_TEMPORAL
    regime_threshold_fallback: float = 0.3         # FALLBACK
    force_accept_unit_conf: bool = False           # §6.1 G-V0 unit test mode

class FusionAggregator:
    def __init__(self, config: FusionAggregatorConfig):
        self._config = config
    
    def aggregate(
        self,
        pose_out: PoseCoreV2Output,             # clip_pos_w, clip_quat_w, conf_pose, regime_pose
        cable_state: CableState40,              # positions, confidences
        target_seg_idx: torch.Tensor,           # [B] int64 (per-world target seg)
    ) -> tuple[PoseEstimate14D, RegimeState]:
        B = pose_out.clip_pos_w.shape[0]
        
        # §2.5.1 PoseEstimate14D 再構成
        seg_idx_clamped = target_seg_idx.clamp(self._config.edge_seg_clamp_min,
                                                self._config.edge_seg_clamp_max)
        b_indices = torch.arange(B, device=cable_state.positions.device)
        seg_pos_w = cable_state.positions[b_indices, seg_idx_clamped, :]   # [B, 3]
        
        # §2.5.2 seg_quat_w (tangent-based)
        seg_quat_w = compute_seg_quat_from_tangent(
            positions=cable_state.positions,
            target_seg_idx=seg_idx_clamped,
        )                                                                   # [B, 4]
        
        clip_pos_w = pose_out.clip_pos_w                                    # [B, 3]
        clip_quat_w = pose_out.clip_quat_w_xyzw                             # [B, 4]
        
        pose_14d = torch.cat([seg_pos_w, seg_quat_w, clip_pos_w, clip_quat_w], dim=-1)
        # pose_14d: [B, 14] float32 in PoseEstimate14D contract
        
        # §2.5.3 Regime aggregation
        cable_target_conf = cable_state.confidences[b_indices, seg_idx_clamped]
        cable_target_regime = self._derive_regime(cable_target_conf)
        regime_fusion = self._most_restrictive(pose_out.regime, cable_target_regime)
        
        # §2.5.4 Confidence aggregation
        edge_mask = (target_seg_idx == 0) | (target_seg_idx == 39)
        edge_factor = torch.where(edge_mask,
                                   torch.full_like(cable_target_conf, self._config.edge_penalty),
                                   torch.ones_like(cable_target_conf))
        conf_fusion = torch.minimum(pose_out.conf_pose, cable_target_conf) * edge_factor
        
        # §6.1 G-V0 unit test mode
        if self._config.force_accept_unit_conf:
            regime_fusion = torch.zeros_like(regime_fusion)  # ACCEPT == 0
            conf_fusion = torch.ones_like(conf_fusion)
        
        return PoseEstimate14D(pose_14d=pose_14d, conf=conf_fusion), regime_fusion
```

### §3.3 RegimeState aggregation (§2.5.3 detail)

| pose_regime | cable_regime | regime_fusion | obs[45:49] one-hot |
|-------------|--------------|----------------|---------------------|
| ACCEPT (0) | ACCEPT (0) | ACCEPT (0) | [1, 0, 0, 0] |
| ACCEPT (0) | PREDICT (1) | PREDICT (1) | [0, 1, 0, 0] |
| ACCEPT (0) | FALLBACK (2) | FALLBACK (2) | [0, 0, 1, 0] |
| ACCEPT (0) | FAIL_CLOSED (3) | FAIL_CLOSED (3) | [0, 0, 0, 1] |
| PREDICT (1) | ACCEPT (0) | PREDICT (1) | [0, 1, 0, 0] |
| PREDICT (1) | FALLBACK (2) | FALLBACK (2) | [0, 0, 1, 0] |
| FALLBACK (2) | * | FALLBACK or worse | priority order |
| FAIL_CLOSED (3) | * | FAIL_CLOSED (3) | [0, 0, 0, 1] |
| * | FAIL_CLOSED (3) | FAIL_CLOSED (3) | [0, 0, 0, 1] |

**Policy update mask** (CC4 v3.2 §6.5 + Appendix I): `regime_fusion == FAIL_CLOSED` 時、policy gradient 計算で `loss_mask = 0` 適用 (training-time only、inference では policy は obs[45:49] を見て自律判断)。

### §3.4 Confidence aggregation rationale (§2.5.4 detail)

**Why min not mean / weighted**:
1. **Bottleneck principle**: 5-clip routing chain で一方の channel 低信頼 = chain failure の dominant cause、min がその risk を policy に明示的に伝達
2. **Defensive learning**: PPO は exploration phase で over-confident pose を信頼しすぎる risk、min aggregation で early-iter conservative 学習
3. **No information loss**: 個別 confidence は obs[45:49] regime one-hot で別途符号化、min による情報損失 minimal

**Edge penalty rationale**: cable target_seg_idx=0 (grasp end) or =39 (far end) は §2.5.2 で clamp 必要、tangent 計算が one-sided difference になり quat 精度低下 → edge_penalty=0.5 で policy 警告。

**Alternative considered (and REJECTED)**:
- Geometric mean (sqrt(p × c)): bottleneck signal weaker than min
- Weighted sum (α × p + (1-α) × c): α tuning empirical、本 MVP-3 で defer
- Multiply (p × c): too aggressive penalty (両方 0.9 で 0.81)

### §3.5 Bit-identical baseline preservation (E.5 invariant)

**Claim**: regime=ACCEPT (one-hot [1, 0, 0, 0]) AND conf=1.0 AND zero-init [45:50] first-layer weight → 50D policy forward output == 45D baseline policy forward output (exact float32 equality)。

**Proof sketch** (CC4 v3.2 Appendix E.5):
1. 50D first-layer weight `W_50` は `[W_45 | 0_5]` 形式 (zero-init [45:50] columns)
2. 50D obs `[obs_45 | regime_onehot | conf]` → `W_50 @ obs_50 = W_45 @ obs_45 + 0 @ [regime, conf] = W_45 @ obs_45`
3. 後段 layer は変化なし → output bit-identical

**Critical condition**: `migrate_obs_normalizer_45_to_50` で **regime + conf dims に running stats normalization を適用しない** (raw pass-through、ε-variance 禁止)。Normalize すると bit-identical 破壊 (CC4 v3.2 v3.2 spec §10 R-3 MEDIUM 起因)。

**Verification gate (G-V0、§6.1)**: `force_accept_unit_conf=True` mode で 100 frames を 45D baseline と 50D augmented で並行 inference、`max(|out_45 - out_50|) < 1e-6` (float32 epsilon) を確認。

---

## §4 Downstream env obs hook design (ObsAssembler env wrapper)

### §4.1 ObsAssembler module spec

**配置**: `thread_isaac_lab/envs/wrappers/vision_obs_assembler.py` (NEW、env wrapper 層)

**Why env wrapper 層 (not estimators core)**: ObsAssembler は env-specific (45D obs 構造 + nominal_target replacement logic + multi-clip current_clip_idx 依存) → R6 enforcement に従い estimators/ には配置不可。`envs/wrappers/` は env-side utility と等価扱い (e.g., 既存 `WristCameraManager` `envs/` 配置の precedent)。

**Why env wrapper not env file modification**: state.md §4 禁止事項「env file 改変禁止」遵守。新規 wrapper module で既存 env を non-invasively 拡張、`PolicyTrainingAdapter` のような composition pattern で AC env を wrap。

```python
# thread_isaac_lab/envs/wrappers/vision_obs_assembler.py

class VisionObsAssembler:
    """Assemble 50D vision-augmented obs from 45D base obs + Fusion output.
    
    Boundary: env-side wrapper, takes env-computed 45D obs + Fusion output → 50D obs.
    Does NOT modify newton_approach_cable_env.py (env file 改変禁止 per state.md §4).
    """
    
    def __init__(self, fusion_config: FusionAggregatorConfig):
        self._aggregator = FusionAggregator(fusion_config)
        self._regime_one_hot_lookup = torch.eye(4)  # [4, 4] identity for one-hot
    
    def assemble_50d(
        self,
        obs_45d: torch.Tensor,                      # [B, 45] env-computed base obs
        pose_out: PoseCoreV2Output,                 # Fusion Stage 1 output
        cable_state: CableState40,                  # Fusion Stage 1 output
        target_seg_idx: torch.Tensor,               # [B] int64
        current_clip_pos: torch.Tensor,             # [B, 3] active target clip pos (nominal)
        current_clip_quat: torch.Tensor,            # [B, 4] active target clip quat (nominal)
        ee_pos_r: torch.Tensor,                     # [B, 3]
        ee_quat_r: torch.Tensor,                    # [B, 4]
        ee_pos_l: torch.Tensor,                     # [B, 3]
        ee_quat_l: torch.Tensor,                    # [B, 4]
    ) -> torch.Tensor:
        # Stage 2: FusionAggregator
        pose_14d_obj, regime_fusion = self._aggregator.aggregate(
            pose_out, cable_state, target_seg_idx
        )
        
        # obs[16:30] = PoseEstimate14D
        pose_14d = pose_14d_obj.pose_14d                                    # [B, 14]
        
        # obs[30:42] = recomputed error (vision-derived)
        clip_pos_w = pose_14d[:, 7:10]
        clip_quat_w = pose_14d[:, 10:14]
        recomputed_error = self._recompute_error(
            clip_pos_w, clip_quat_w, ee_pos_r, ee_quat_r, ee_pos_l, ee_quat_l
        )                                                                    # [B, 12]
        
        # obs[45:49] = regime one-hot
        regime_one_hot = self._regime_one_hot_lookup[regime_fusion]          # [B, 4]
        
        # obs[49:50] = confidence scalar
        conf_scalar = pose_14d_obj.conf.unsqueeze(-1)                        # [B, 1]
        
        # Final 50D obs
        obs_50d = obs_45d.clone()
        obs_50d[:, 16:30] = pose_14d
        obs_50d[:, 30:42] = recomputed_error
        # obs[42:45] zero pad preserved (env-computed)
        obs_50d = torch.cat([obs_50d, regime_one_hot, conf_scalar], dim=-1)  # [B, 50]
        
        return obs_50d
    
    @staticmethod
    def _recompute_error(clip_pos_w, clip_quat_w, ee_pos_r, ee_quat_r, ee_pos_l, ee_quat_l):
        # §2.5.5
        pos_err_r = clip_pos_w - ee_pos_r
        ori_err_r = quat_to_axis_angle(quat_mul(clip_quat_w, quat_conj(ee_quat_r)))
        pos_err_l = clip_pos_w - ee_pos_l
        ori_err_l = quat_to_axis_angle(quat_mul(clip_quat_w, quat_conj(ee_quat_l)))
        return torch.cat([pos_err_r, ori_err_r, pos_err_l, ori_err_l], dim=-1)  # [B, 12]
```

### §4.2 50D obs structure (CC4 v3.2 §6.4 整合)

`§2.4` table に準拠、本節は detail 補足:

| obs[i] | source | population timing | example expected value |
|--------|--------|-------------------|------------------------|
| 0-7 | env (proprio) | env step 内 | arm joint state |
| 8-15 | env (proprio) | env step 内、OBS_L_ARM_MASK_PROB applies | L clamp pos+quat+finger |
| 16-29 | Fusion (PoseEstimate14D) | Stage 2 後 | seg_pos[3] + seg_quat[4] + clip_pos[3] + clip_quat[4] |
| 30-41 | Fusion (recomputed error) | Stage 3 後 | pos_err_r[3] + ori_err_r[3] + pos_err_l[3] + ori_err_l[3] |
| 42-44 | env (zero pad) | env step 内、unchanged | [0, 0, 0] |
| 45-48 | Fusion (regime one-hot) | Stage 3 後 | [1, 0, 0, 0] (ACCEPT) |
| 49 | Fusion (confidence) | Stage 3 後 | 0.85 (typical fine-tune phase) |

### §4.3 obs[16:30] / obs[30:42] / obs[45:50] population rules

**obs[16:30] population**:
- Source: `PoseEstimate14D = [seg_pos(3), seg_quat(4), clip_pos(3), clip_quat(4)]`
- Coordinate frame: world frame (env-side `bq` 基準)
- NaN/inf 防御: `torch.nan_to_num(pose_14d, nan=0.0, posinf=1e6, neginf=-1e6)`
- FAIL_CLOSED 時: `previous_pose_estimate` carry-forward (CC4 v3.2 §5.6)、ない場合 zeros

**obs[30:42] population**:
- Source: `_recompute_error()` 経 (§2.5.5)
- 注意: 既存 env の obs[30:42] (line 1320-1323 `pos_error_l`) は `nominal_target_pos - ee_pos` 形式、Fusion 版は `clip_pos_w - ee_pos` (vision-derived)
- nominal_target_pos との差 = vision noise (~5mm) は policy fine-tune で 適応学習
- Multi-clip routing context: `clip_pos_w` は `current_clip_idx` の active clip (env-side Phase logic で決定、`EstimatorInputs.current_clip_idx` 経 propagate)

**obs[45:50] population**:
- obs[45:49]: regime one-hot (§3.3 priority logic)
- obs[49]: conf scalar ∈ [0, 1] (§3.4 min × edge_penalty)
- Raw pass-through: normalizer epsilon-variance 禁止 (CC4 v3.2 §15、E.2)

### §4.4 R6 boundary (env wrapper, NOT Fusion estimator core)

**禁止 import** (R6 enforcement):
- `vision_obs_assembler.py` は estimators/ from import可 (`from thread_isaac_lab.estimators import ...`)
- estimators/ から envs/ への import は禁止 (CC4 v3.2 §H.3 import-lint test 拡張)
- env file (newton_approach_cable_env.py) は `vision_obs_assembler` を import (env が wrapper を使う side、wrapper は env を使わない side)

**env file 改変禁止 (state.md §4)**:
- newton_approach_cable_env.py 本体は **不変** (Fusion 統合は wrapper composition)
- training entry script (`train_newton_dapg_dual_arm.py` 等) で wrapper を被せる pattern:
  ```python
  base_env = NewtonApproachCableEnv(...)
  fused_env = VisionFusedEnvAdapter(base_env, fusion_estimator, obs_assembler)
  trainer.train(fused_env)
  ```

### §4.5 target_seg_idx propagation (R6 OK、env-side computed)

`target_seg_idx_r/l` は env-side `_compute_target_seg_indices(bq)` (line 949) で per-world computed、kinematic prior + grasp finger position 経の env logic。R6 boundary 上は **robot-measurable** (env-side logic で決定、cable_body_q GT には依存しない、Phase + grasp + nominal kinematic prior のみ使用) → `EstimatorInputs.target_seg_idx_r/l` field として propagate 可。

**`EstimatorInputs` 拡張 (§5.1)**:
```python
@dataclass
class EstimatorInputs:
    # existing (CC4 v3.2 + CableState §6.3 extension):
    rgb_l, rgb_r, depth_l, depth_r, joint_state, ...
    rgb_oh, depth_oh, overhead_camera_pose, overhead_intrinsics
    
    # NEW (Fusion §4.5):
    target_seg_idx_r: torch.Tensor          # [B] int64、env-side _compute_target_seg_indices
    target_seg_idx_l: torch.Tensor          # [B] int64
    current_clip_idx: torch.Tensor          # [B] int64、multi-clip routing context
```

**Fusion 内 active arm 選択**: AC dual-arm env では right arm が primary (per-skill convention)、Fusion は `target_seg_idx_r` を default で使用。L arm path (CLAMP-R) は MVP-4+ trigger で別 OQ。

---

## §5 Module boundary R6 compliance + 既存 estimator core integration

### §5.1 PoseEstimatorCoreFusion (composition pattern)

**配置**: `thread_isaac_lab/estimators/core/pose_estimator_core_fusion.py` (NEW、~80 LoC)

**Composition over inheritance**: CC4 v3.2 PoseEstimatorCore (Phase 1) + CableState §6.1 PoseEstimatorCorePhase2 + Pose alt path PoseEstimatorCoreV2 を **internal compose** する Fusion-level 入口。

```python
# thread_isaac_lab/estimators/core/pose_estimator_core_fusion.py

@dataclass
class PoseCoreV2Output:
    """Pose alt path output (clip 7D only、LL-Vision-Pose-Design §4.6)."""
    clip_pos_w: torch.Tensor          # [B, 3]
    clip_quat_w_xyzw: torch.Tensor    # [B, 4]
    conf_pose: torch.Tensor           # [B] in [0, 1]
    regime: torch.Tensor              # [B] int64 ∈ {0, 1, 2, 3}

@dataclass
class FusionCoreOutput:
    """Composite output: PoseEstimate14D + RegimeState + diagnostics."""
    pose_14d: torch.Tensor            # [B, 14] (CC4 v3.2 §3.2 contract)
    regime: torch.Tensor              # [B] int64
    conf_fusion: torch.Tensor         # [B] in [0, 1]
    pose_v2_output: PoseCoreV2Output  # [for diagnostics]
    cable_state: CableState40         # [for diagnostics]


class PoseEstimatorCoreFusion:
    """Composition entry: Pose CoreV2 + CableState Solver + FusionAggregator.
    
    R6 boundary: import only from thread_isaac_lab.estimators.*。
    No env / newton import (CC4 v3.2 §H.3 import-lint test 拡張で enforce)。
    """
    
    def __init__(
        self,
        pose_core_v2: PoseEstimatorCoreV2,     # Pose alt path (LL-Vision-Pose-Design §1.2)
        cable_solver: CableStateSolver,         # CableState §6.2
        fusion_aggregator: FusionAggregator,    # 本 design §3.2
    ):
        self._pose = pose_core_v2
        self._cable = cable_solver
        self._fusion = fusion_aggregator
    
    def forward(self, inputs: EstimatorInputs) -> FusionCoreOutput:
        # Stage 1a: Pose CoreV2 (clip 7D)
        pose_out = self._pose.forward(inputs)
        
        # Stage 1b: CableState Solver (40 segments + confidence)
        cable_state = self._cable(
            cloud=self._build_cloud(inputs),     # internal helper、Stage A.3 wrapper
            prev=inputs.previous_cable_estimate,
        )
        
        # Stage 2: FusionAggregator
        pose_14d_obj, regime_fusion = self._fusion.aggregate(
            pose_out=pose_out,
            cable_state=cable_state,
            target_seg_idx=inputs.target_seg_idx_r,   # default right arm (§4.5)
        )
        
        return FusionCoreOutput(
            pose_14d=pose_14d_obj.pose_14d,
            regime=regime_fusion,
            conf_fusion=pose_14d_obj.conf,
            pose_v2_output=pose_out,
            cable_state=cable_state,
        )
```

**Stage 1a/1b 並行性 (latency optimization)**: Pose CoreV2 と CableState Solver は input 共有 + output 独立 → CUDA stream で並列実行可:
```python
stream_pose = torch.cuda.Stream()
stream_cable = torch.cuda.Stream()
with torch.cuda.stream(stream_pose):
    pose_out = self._pose.forward(inputs)
with torch.cuda.stream(stream_cable):
    cable_state = self._cable(cloud, prev)
torch.cuda.synchronize()
# Then Stage 2 FusionAggregator (sequential after both leaves complete)
```

### §5.2 ObsAssembler (env wrapper 層、§4 配置)

**配置**: `thread_isaac_lab/envs/wrappers/vision_obs_assembler.py` (NEW、~70 LoC)

**R6 boundary**: env wrapper layer は env-aware (env-side obs[45D] structure + ee_pos derivation 必要)。estimators/ には配置不可。Imports `from thread_isaac_lab.estimators import FusionAggregator` で one-way dependency。

### §5.3 Import-lint test (CC4 v3.2 §H.3 拡張)

**配置**: `thread_isaac_lab/tests/test_estimator_import_boundary.py` (extension)

```python
def test_fusion_core_no_env_import():
    """PoseEstimatorCoreFusion は env / newton を import しない (R6 boundary)."""
    forbidden_imports = ["thread_isaac_lab.envs", "newton", "warp"]  # warp は cable_solver 経由のみ可、core_fusion 直接禁止
    
    src_path = "thread_isaac_lab/estimators/core/pose_estimator_core_fusion.py"
    with open(src_path) as f:
        src = f.read()
    
    for forbidden in forbidden_imports:
        assert f"import {forbidden}" not in src, f"R6 boundary violation: {forbidden}"
        assert f"from {forbidden}" not in src, f"R6 boundary violation: {forbidden}"
```

### §5.4 既存 estimator core integration (CC4 v3.2 Appendix H reuse)

| Existing module | Status | Reuse / Extend strategy |
|-----------------|--------|--------------------------|
| `estimators/types.py` | DONE (Phase 1) | EXTEND: `EstimatorInputs` に target_seg_idx_r/l + current_clip_idx field 追加 (§4.5) |
| `estimators/input_adapter.py` | DONE | REUSE: `PoseEstimatorInputAdapter` Newton wrist camera bridge は本 leaf alt path 流用 (Pose §0.3) |
| `estimators/core/pose_estimator_core.py` | DONE (Phase 1: Stage 0+1) | REPLACE: Pose alt path で `PoseEstimatorCoreV2` (Stage 1 SAM2 + Stage 2 keypoint + Stage 3 PnP) を新規追加 (Pose §1.2) |
| `estimators/core/segmenter.py` (LightUNet) | DONE | DEFER: SAM2 distillation の student model 候補、MVP-4+ trigger (Pose §3.3 distilled mode) |
| `estimators/core/roi_prior.py` | DONE | REUSE: ROI prompt source として SAM2 bbox prompt (Pose §3.2) で流用 |
| `estimators/core/self_occlusion.py` | DONE | REUSE: occlusion handling logic、Stage 1 mask post-processing で利用 |
| `estimators/core/cable_state_solver.py` (NEW for L1.A.2) | impl pending | NEW: CableState §6.2 spec、本 leaf 起動 prerequisite |
| `estimators/core/pose_estimator_core_fusion.py` (NEW、本 leaf) | design only | NEW: §5.1 composition entry、~80 LoC |
| `estimators/aggregator.py` (NEW、本 leaf) | design only | NEW: `FusionAggregator` (§3.2)、~60 LoC |
| `envs/wrappers/vision_obs_assembler.py` (NEW、本 leaf) | design only | NEW: `VisionObsAssembler` (§4.1)、~70 LoC |

---

## §6 Benchmark spec (4 leaves output ↔ Fusion output validation)

### §6.1 G-V0 Bit-identical baseline test (E.5 invariant)

**Goal**: regime=ACCEPT + conf=1.0 + zero-init [45:50] weight で 50D policy output が 45D baseline と bit-identical (float32 epsilon)。

**Setup**:
- 100 frames recorded from 45D baseline policy inference (任意 AC checkpoint)
- 同 frames を 50D augmented policy (zero-init [45:50] migrated) で inference
- `force_accept_unit_conf=True` mode (§3.2 FusionAggregatorConfig)
- regime_one_hot = [1, 0, 0, 0] (ACCEPT) 強制
- conf = 1.0 強制

**Pass criterion**:
```
max_abs_diff = max(|output_45d - output_50d|)  # over 100 frames × output_dim
PASS: max_abs_diff < 1e-6 (float32 epsilon)
```

**Fail handling**: `migrate_first_layer_45_to_50` の zero-init 不正 / `migrate_obs_normalizer_45_to_50` で regime+conf に normalize 適用された (CC4 v3.2 §15 ε-variance violation)。

**実装**: `thread_isaac_lab/tests/test_fusion_bit_identical.py` (NEW、~50 LoC)

### §6.2 G-V1 Leaf output integration sanity check

**Goal**: 各 leaf output が Fusion boundary に正しく統合されることを sample-level で確認。

**Per-leaf check**:

| leaf | check | Pass criterion |
|------|-------|----------------|
| Pose CoreV2 | `clip_pos_w` shape == [B, 3] AND finite AND `clip_quat_w_xyzw` unit-norm | shape + finite + ‖q‖ ∈ [0.99, 1.01] |
| Pose CoreV2 | `conf_pose` ∈ [0, 1] AND `regime` ∈ {0, 1, 2, 3} | range check |
| CableState | `positions` shape == [B, 40, 3] AND finite | shape + finite |
| CableState | `confidences` shape == [B, 40] AND ∈ [0, 1] | shape + range |
| CableState | identity-correct (§3.3 post-fit check): `||positions[:, 0, :] - p_grasp_finger||` < `||positions[:, 39, :] - p_grasp_finger|| + 50mm` | empirical assert per scene |

**Sample size**: N=20 random scenes (G-V0 と share)、Pose CoreV2 + CableState の output が valid であること、Fusion 入力前提を満たすこと。

**実装**: `thread_isaac_lab/tests/test_fusion_leaf_integration.py` (NEW、~80 LoC)

### §6.3 G-V2 50D obs population correctness

**Goal**: ObsAssembler が 50D obs の各 slice を正しく populate することを確認。

**Setup**:
- Synthetic Fusion output (handcrafted PoseEstimate14D + regime + conf)
- Synthetic 45D base obs
- Run `VisionObsAssembler.assemble_50d` (§4.1)

**Check**:
| slice | expected | check |
|-------|----------|-------|
| `obs[0:8]`、`obs[8:16]` | unchanged from base 45D | `assert torch.equal(obs_50d[:, :16], obs_45d[:, :16])` |
| `obs[16:30]` | `pose_14d` from FusionAggregator | `assert torch.allclose(obs_50d[:, 16:30], expected_pose_14d)` |
| `obs[30:42]` | recomputed_error from `_recompute_error` | manual computation比較、within 1e-5 |
| `obs[42:45]` | zero pad (unchanged from base) | `assert torch.equal(obs_50d[:, 42:45], torch.zeros(...))` |
| `obs[45:49]` | regime one-hot (priority order from §3.3) | exact one-hot match |
| `obs[49:50]` | conf scalar (min × edge_penalty) | within 1e-5 of expected |

**実装**: `thread_isaac_lab/tests/test_obs_assembler.py` (NEW、~100 LoC)

### §6.4 G-V3 PoseEstimate14D 再構成 correctness

**Goal**: cable seg 7D ← CableState target_seg + clip 7D ← Pose CoreV2 の merging が正しいことを scene level で確認。

**Setup**:
- N=20 scenes (G-V0/V2 と share)
- Ground-truth `seg_pos_gt` from newton state dump (eval-only EstimatorLabelsForEvalOnly per CC4 v3.2 §H.4)
- Ground-truth `clip_pos_gt` from env state

**Check**:
- `||PoseEstimate14D[:, 0:3] - seg_pos_gt||` < 5mm (mean across scenes、CableState target seg precision)
- `||PoseEstimate14D[:, 7:10] - clip_pos_gt||` < 5mm (mean across scenes、Pose CoreV2 precision)
- `quat_distance(PoseEstimate14D[:, 3:7], seg_quat_gt)` < 10° (mean、tangent-based approximation acceptable)
- `quat_distance(PoseEstimate14D[:, 10:14], clip_quat_gt)` < 10° (mean、yaw mod π convention per Pose §4.7)

**実装**: `thread_isaac_lab/tests/test_pose_14d_reconstruction.py` (NEW、~120 LoC)

### §6.5 G-V4 G8 end-to-end (本 leaf goal_verification)

**Goal**: vision-based 5-clip cable routing SR ≥ 30% on N=10 ep × 5 seeds、cuda:2 deterministic、`eval_skill.py --skill multi_clip --vision` mode。

**Pre-conditions**:
- 3 leaves COMPLETE: Pose MVP-3 + CableState Q5 + DR Tier 0c PASS
- T-L1-B Phase 5-3 multi-clip orchestrator ready (external blocker、Y2/KA5 minimal child trigger)
- T-Skill milestone leaves: per-skill ≥ 50% floor (AC/IC/AR/Grip-CLAMP)
- AC fine-tune (P4) completed: vision-augmented 50D obs 経 fine-tune、value_loss < 3× baseline maintained

**Eval protocol**:
- 50 episodes total (10 ep × 5 seeds)
- cuda:2 deterministic kernel + fixed seed (seed=42, ..., 46)
- `--skill multi_clip --vision` mode: 5-clip routing chain end-to-end with vision pose substitution
- Episode termination: success (5-clip 全 routing 完了) / failure (any skill failure or episode timeout)

**Pass criterion**:
- Average SR (over 50 episodes) ≥ 30%
- Per-seed SR variance < 10pp (seed-robust)
- No catastrophic divergence (per-iter value_loss spike > 3× baseline 不在)

**Fail handling**:
- SR < 30% but value_loss healthy: vision noise budget 不足 → DR Tier 1 fine-tune (D6 background) or Pose/CableState re-train
- value_loss > 3× baseline: AC fine-tune collapse → fresh-start with Tier 0a baseline ckpt (CC4 v3.2 E.6、prohibited.md "崩壊 checkpoint resume 禁止")
- Per-seed variance > 10pp: seed-fragile → Pose alt path symmetry handling (§4.7 yaw mod π) re-validation

**実装**: 既存 `eval_skill.py` extension (`--vision` flag 追加)、~30 LoC

### §6.6 G-V5 Latency budget

**Goal**: end-to-end Fusion + obs assembly 一回 inference が < 50ms (offline benchmark mode、CC4 v3.2 §8.1 latency budget)。

**Per-stage profile**:
| stage | budget | actual (estimate) | rationale |
|-------|--------|-------------------|-----------|
| Pose Stage 1 (SAM2 ViT-B) | ~30-50ms | offline benchmark only | Pose §3.3 mode |
| Pose Stage 2 (keypoint) | ~1ms | cv2.findContours + cornerSubPix | low-cost |
| Pose Stage 3 (PnP+RANSAC) | ~1-3ms | 200 iter cv2.solvePnPRansac | low-cost |
| CableState Stage A (3-cam back-proj) | ~5ms | Warp kernel | CableState §2.5.3 mitigation |
| CableState Stage B (PCA) | ~1ms | SVD on ~2k points | low-cost |
| CableState Stage C (DD-PINN) | ~2ms | small MLP ~50k params | only triggered when var_ratio < 0.6 |
| CableState Stage D (Cosserat) | ~5-10ms | warm start で 30-50 iter Warp kernel | CableState §2.5.3 |
| CableState Stage E (confidence) | ~0.5ms | post-train logistic regression | trivial |
| Fusion Aggregator (§3.2) | ~0.5ms | tensor op | trivial |
| ObsAssembler (§4.1) | ~0.5ms | tensor op | trivial |
| **Total (Pose + CableState parallel + Fusion)** | **~50-65ms** | exceeds 50ms target | Pose Stage 1 SAM2 dominant、offline benchmark mode で吸収 |

**Online policy step impact**: 50-65ms latency は online policy step (期待 ~12ms/step) を超過 → **online は破綻、offline benchmark mode 限定** (Pose §3.3、本 MVP-3 scope の constraint)。distilled mode (LightUNet via SAM2 distillation) は MVP-4+ trigger。

**Pass criterion** (G-V5):
- Offline benchmark: total ≤ 65ms (一回 inference、N=20 scene profile median)
- Async mode (将来): online policy が前 frame cached mask 使用、policy step latency 不変

**Fail handling**:
- Pose Stage 1 SAM2 ViT-B が 50ms 超: ViT-S downgrade or distilled mode 早期 trigger
- CableState Stage D 100 iter timeout: max_iter=50 reduce + Stage C warm start 強化

### §6.7 Benchmark execution sequence (gate cascade)

```
G-V0 Bit-identical baseline (zero-init weight 検証)
   ↓ PASS
G-V1 Leaf output integration sanity (Pose + CableState valid output)
   ↓ PASS
G-V2 50D obs population correctness (ObsAssembler logic)
   ↓ PASS
G-V3 PoseEstimate14D 再構成 correctness (cable seg + clip merging)
   ↓ PASS
G-V5 Latency budget (offline benchmark mode profile)
   ↓ PASS
[AC fine-tune P4 (~30h GPU)、value_loss monitoring]
   ↓ PASS
G-V4 G8 end-to-end (5-clip vision SR ≥ 30%、本 leaf goal_verification)
   ↓ PASS
[State.md status COMPLETE、T-Vision umbrella 4-leaves COMPLETE gate update]
```

**Gate skip 禁止**: G-V0 → G-V4 順序遵守、不合格時 fix root cause、迂回 prohibited.md "対処療法禁止" 該当。

---

## §7 Implementation phasing (P1-P5、~250 LoC + ~50h GPU)

design memo §2.4 + state.md §1 整合、本 design で精緻化:

| Phase | Item | LoC | GPU wall | Dependency | Verification gate |
|-------|------|-----|----------|------------|---------------------|
| **P1** | Estimator-Core MVP-1 → MVP-2 (Pose CoreV2 + CableState Solver impl) | ~200 (alt path Pose ~150 + CableState ~400 は別 leaf 担当、ここでは composition + integration ~50) | ~10h (P1 内 fine-tune) | Pose MVP-3 + CableState Q5 (3 leaves COMPLETE precondition) | Pose §7 + CableState §5 各 gate |
| **P2** | Env ObsAssembler 拡張 (§4 VisionObsAssembler、`envs/wrappers/vision_obs_assembler.py` NEW ~70 LoC) | ~70 | n/a | P1 | G-V2 obs population test |
| **P3** | Policy migration script (`migrate_first_layer_45_to_50` + `migrate_obs_normalizer_45_to_50` + `migrate_policy_45_to_50` adapter integration) | ~50 | n/a | P2 + AC v23 base ckpt (per-skill ≥50%) | G-V0 bit-identical test |
| **P4** | AC fine-tune (PPO + 50D obs、target ≥ 50% AC SR maintenance under vision noise) | ~70 | ~30h | P3 + Tier 0c DR PASS (DR §3.1) | rollback gate: value_loss < 3× baseline @ iter 20 (E.6) |
| **P5** | Eval gate G8 (vision-based 5-clip ≥ 30% smoke、N=10 ep × 5 seeds) + benchmark wall | ~50 | ~3-5h | P4 + Phase 5-3 multi-clip orchestrator ready (T-L1-B blocker) + T-Skill 50%+ floor | G-V4 end-to-end |
| **Total** | — | **~240** | **~45-50h** | — | G-V0 → G-V4 cascade |

**Note** (state.md §1 consistency): design memo §2.4 + state.md §1 は ~250 LoC + ~45-50h GPU、本 design phasing と±10 LoC 精度で 整合。Pose alt path / CableState の本体 LoC は各 leaf 担当 (本 leaf scope は composition + integration + obs hook + benchmark)。

**Sub-task 1 LoC breakdown 細部** (~240 total):
- `estimators/aggregator.py` (FusionAggregator) ~60 LoC
- `estimators/core/pose_estimator_core_fusion.py` (PoseEstimatorCoreFusion composition) ~80 LoC
- `estimators/types.py` extension (EstimatorInputs target_seg_idx + current_clip_idx) ~10 LoC
- `envs/wrappers/vision_obs_assembler.py` (VisionObsAssembler) ~70 LoC
- `envs/wrappers/vision_fused_env_adapter.py` (composition wrapper) ~20 LoC

**GPU breakdown** (~45-50h):
- P1 internal fine-tune (Pose CoreV2 confidence calibration + CableState confidence calibration) ~10h
- P3 policy migration unit test ~0h (CPU)
- P4 AC fine-tune 50D obs ~30h
- P5 G-V4 5-clip vision eval ~3-5h (50 episodes × ~5 min/episode)

---

## §8 Risk register

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| **R-F1** | Bit-identical baseline 破壊 (E.5 invariant violation: regime+conf normalize 適用 / [45:50] non-zero init) | **HIGH** | G-V0 unit test mandatory、`migrate_obs_normalizer_45_to_50` raw pass-through enforcement (CC4 v3.2 §15 ε-variance 禁止)、test_fusion_bit_identical.py 100 frames assert |
| **R-F2** | PoseEstimate14D 再構成 で seg_quat tangent computation degenerate (target_seg_idx ∈ {0, 39}、edge case) | **HIGH** | §2.5.2 clamp [1, 38] + §2.5.4 edge_penalty=0.5、edge case quat 精度低下を policy に conf 経で警告 |
| **R-F3** | Cable target_seg_idx propagation の R6 violation (env-side computed value で R6 違反) | **MEDIUM** | §4.5 で target_seg_idx は kinematic prior + grasp finger position 経の env logic、cable_body_q GT 非依存 → R6 OK 検証、import-lint test (§5.3) で enforce |
| **R-F4** | Late Fusion + 50D obs migration で AC fine-tune value_loss explode (CC4 v3.2 §10 R-3 MEDIUM) | **MEDIUM** | E.6 rollback criterion (value_loss > 3× baseline @ iter 20 → fresh-start with Tier 0a baseline ckpt)、prohibited.md "崩壊 checkpoint resume 禁止" 遵守 |
| **R-F5** | G-V4 G8 SR < 30% with healthy value_loss (vision noise budget 不足) | **MEDIUM** | DR Tier 1 D6 background fine-tune trigger、Pose/CableState empirical residual measurement → 改善 train phase 別 task 起票 |
| **R-F6** | Pose CoreV2 + CableState parallel CUDA stream race condition (output stale tensor read) | LOW | §5.1 `torch.cuda.synchronize()` between Stage 1 (parallel) and Stage 2 (serial)、unit test で stream synchronization 確認 |
| **R-F7** | target_seg_idx hysteresis (env-side _update_target_seg_hysteresis line 891) で frame skip による Fusion divergence | LOW | hysteresis window K=3 (env-side既存)、Fusion は per-frame target_seg_idx を信頼、unit test で frame-by-frame consistency 確認 |
| **R-F8** | edge_penalty=0.5 が aggressive すぎ (target_seg=0 grasp end で常に conf 半減) | LOW | empirical: AC env target_seg は通常 mid-cable (5-25 範囲)、edge case は phase transition のみ。MVP-3 で edge case 出現率を log、必要なら edge_penalty=0.7 緩和 |
| **R-F9** | 50D obs migration script (P3) backward compatibility with 既存 RSL-RL ckpt format | LOW | CC4 v3.2 Appendix E.6 `migrate_policy_45_to_50` で full ckpt migration、obs_normalizer + first_layer + remaining params 整合保証、unit test (G-V0) で確認 |
| **R-F10** | ObsAssembler が env file 改変必要になる risk (state.md §4 violation) | LOW | §4.4 で wrapper composition pattern、newton_approach_cable_env.py 不変、training entry script で wrap、PreCheck で確認 |
| **R-F11** | Multi-clip routing で current_clip_idx propagation が AC env だけでなく IC/AR env にも必要 (multi-skill MVP-4 trigger) | LOW | 本 MVP-3 scope は AC-only (CC4 v3.2 OQ-2)、IC/AR は MVP-4 trigger 別 leaf。AC env で current_clip_idx は ApproachCable phase 内 1 clip 固定 → propagation 簡素 |
| **R-F12** | Pose CoreV2 yaw mod π convention (§4.7) と policy obs[19:23] (clip_quat) representation の不整合 | **MEDIUM** | Pose §9 OQv2-7 既知、本 leaf 起動前 Rs disposition 経で confirm。基本 path: clip_quat を unit quat (full 2π) で representation、yaw error metric が mod π (eval-only)。policy 学習は full quat、eval gate は mod π 整合。 |

---

## §9 Open questions (impl 起票時 / Rs disposition 必要)

| OQ | topic | current decision | trigger for revision |
|----|-------|-------------------|------------------------|
| **OQ-F1** | edge_penalty 値 (target_seg ∈ {0, 39} の conf 減衰) | 0.5 (default)、empirical 後 0.7 緩和候補 | MVP-3 P5 で edge case 出現率 log、necessary 時 |
| **OQ-F2** | Confidence aggregation 方式 (min vs geometric mean vs weighted sum) | min (§3.4 bottleneck principle)、weighted sum α tuning は MVP-4 defer | empirical AC SR < target 時、ablation 起票 |
| **OQ-F3** | Pose CoreV2 yaw mod π convention と policy obs full 2π representation の harmonization | full quat (policy obs) + mod π (eval gate) hybrid、Pose §9 OQv2-7 経 | MVP-3 P4 AC fine-tune 起動時 (Rs disposition 経) |
| **OQ-F4** | CUDA stream parallel inference (Stage 1a Pose + 1b CableState) | parallel、§5.1 `cuda.synchronize` で safety | latency budget G-V5 fail 時、profile per stream |
| **OQ-F5** | target_seg_idx hysteresis (env-side window K=3) と Fusion frame consistency | env-side hysteresis 信頼、Fusion 不変 | empirical Fusion divergence 観測時 |
| **OQ-F6** | DR Tier 1 (D6 background) fine-tune が AC SR ≥ 30% に必要か Tier 0c で十分か | Tier 0c で trial、不足時 Tier 1 fine-tune 起票 | G-V4 fail 時、failure attribution 経 |
| **OQ-F7** | Multi-clip routing で current_clip_idx の R6 boundary (env-side computed) | env-side _compute_current_clip_idx 経、kinematic prior + Phase logic、cable_body_q GT 非依存 | Phase 5-3 multi-clip orchestrator (T-L1-B) impl 起票時 |
| **OQ-F8** | Bit-identical baseline test の threshold (1e-6 vs 1e-5 vs exact equality) | 1e-6 (float32 epsilon、empirical safe)、1e-7 で float32 op rounding error 検出 risk | unit test 1e-6 で fail 時、test framework 経で再評価 |
| **OQ-F9** | Pose alt path (Charuco + SAM2 + PnP) と CC4 v3.2 (custom LightUNet + Cosserat) の本 leaf 起動前 並走 vs 切替 | Rs disposition 待ち (Pose §6.1 (a)/(b)/(c) 経)、本 design は alt path 採択前提 | Rs Pose alt path approval 経 |
| **OQ-F10** | LightUNet distillation via SAM2 (online distilled mode) を本 MVP-3 scope に含めるか MVP-4 defer | MVP-3 defer (Pose §3.3、offline benchmark mode 限定)、distilled mode は MVP-4+ trigger | online policy step latency 要求発生時 |

---

## §10 Cross-references

### §10.1 Internal vault (parent / sibling NEST nodes)

- **Parent (umbrella)**: `thread-vault/T-Vision/state.md` (L1.A capability axis、IN_PROGRESS、4 leaves COMPLETE で Phase 5-4 G8 unblock)
- **Sibling precedent (Pose、L1.A.1)**: `thread-vault/T-Vision-Pose/state.md` + `thread-vault/06-Knowledge/LL-Vision-Pose-Design.md` (alt path Charuco + SAM2 + PnP+RANSAC、Rs batch approve 2026-05-03)
- **Sibling precedent (CableState、L1.A.2)**: `thread-vault/T-Vision-CableState/state.md` + `thread-vault/06-Knowledge/LL-Vision-CableState-Design.md` (Hybrid PCA + Cosserat、Rs batch approve 2026-05-03)
- **Sibling precedent (DR、L1.A.3)**: `thread-vault/T-Vision-DR/state.md` + `thread-vault/06-Knowledge/LL-Vision-DR-Design.md` (Targeted DR + Curriculum Tier 0-1、Rs batch approve 2026-05-03)
- **本 leaf (Fusion、L1.A.4)**: `thread-vault/T-Vision-Fusion/state.md` (PENDING precedent 解消後 Rs §3.1 #4 起動)

### §10.2 Design memo + 7-CC verdict

- **L1.A design memo (parent)**: `~/.claude/projects/-home-rlrk-IsaacLab/memory/project_l1a_vision_design_complete_2026-04-27.md` §2 (Late Fusion 推奨、12 trade-off matrix)
- **L1.A architecture summary**: `thread-vault/06-Knowledge/LL-Vision-L1A-Architecture.md` § "Sub-task 1: Late Fusion (vision-policy)"
- **7-CC Pre-Debate verdict A' (T-Vision umbrella)**: `T-Vision/state.md` §2 (CC8 KA2 STRONG Late Fusion empirically defensible)
- **CC4 v3.2 base spec**: `thread-vault/07-Design/PoseEstimation-Design-v3.2.md` §3.2 (PoseEstimate14D contract)、§6.4 (45D→50D augmented obs)、§6.5 (FAIL_CLOSED policy mask)、Appendix E (migration scripts)、Appendix H (R6 module boundary)、Appendix I (FAIL_CLOSED training loss mask)

### §10.3 Code references (impl 起票時)

- `thread_isaac_lab/configs/task_config.py:70-75` (CABLE_SEGMENTS=40, CABLE_SEG_LEN=0.015、改変禁止 SSOT)
- `thread_isaac_lab/envs/newton_approach_cable_env.py:225-226, 949` (target_seg_indices_r/l 既存、改変禁止)
- `thread_isaac_lab/envs/newton_approach_cable_env.py:1332` (45D pad、改変禁止)
- `thread_isaac_lab/envs/newton_insert_clip_env.py:1105-1118` (IC 45D obs、本 leaf scope 外 OQ-5b defer)
- `thread_isaac_lab/envs/newton_grip_env.py:1011-1012` (Grip 45D obs、本 leaf scope 外 OQ-5a defer)
- `thread_isaac_lab/envs/wrist_camera_manager.py:53-207` (camera infra、CableState §4.3 で overhead 拡張、本 leaf reuse)
- `thread_isaac_lab/estimators/types.py` (EstimatorInputs、本 leaf §4.5 で extension)
- `thread_isaac_lab/estimators/input_adapter.py` (PoseEstimatorInputAdapter、本 leaf reuse)
- `thread_isaac_lab/estimators/core/pose_estimator_core.py` (Phase 1 base、本 leaf composition)
- `thread_isaac_lab/scripts/eval_skill.py` (本 leaf P5 で `--vision` flag 追加)

### §10.4 Vault knowledge + 04-Specs reference (read-only)

- **04-Specs Vision Pipeline.md** (R6 Stage 1-4 spec、本 leaf は Stage 4 obs assembly に位置付け)
- **04-Specs Camera Backend.md** (Phase 2 RGB+depth pipeline、本 leaf reuse)
- **04-Specs Vision Stack Roadmap.md** (Phase 3 Dreamer / CEM-MPC 全失敗 precedent、Cross-Attention REJECTED rationale)
- **04-Specs SOMA.md** (L0 / L1 / L2 goal、本 leaf goal は L0 vision-based 95% への immediate precursor)
- **06-Knowledge LL-VisualObs-CameraSystem.md** (camera spec)
- **06-Knowledge LL-Newton.md** (Newton 環境制約)
- **07-Design PoseEstimation-Design-v3.1.md** (12-point patch + §15 addendum、CC4 v3.1 元 spec)
- **07-Design PoseEstimation-Design-v3.md** (post-debate parent、1416 lines)

### §10.5 Logic tree + master list

- **Logic tree v1 §L1.A.4**: `~/.claude/projects/-home-rlrk-IsaacLab/memory/project_logic_tree_2026-04-27.md:45`
- **Master list v2 §9**: `~/.claude/projects/-home-rlrk-IsaacLab/memory/project_strategic_task_master_list_v2_2026-04-27.md` line 423-431 (4 task candidates 本 leaf 1:1 mapping)

### §10.6 NEST infrastructure

- **LTM-1 v1.1 spec**: `thread-vault/00-Project-Management/operational-rule-LTM-1.md`
- **Manifest entry**: `thread-vault/00-Project-Management/project-tree-manifest.md` (T-Vision-Fusion node 登録、本 design 起票で last_updated)
- **Tier 2 edit_request**: `00-Project-Management/_edit_requests/00001-T-Vision-init.md` (precedent for L1.A umbrella creation)

### §10.7 Schedule (cron)

- §16 commit re-trigger 2026-05-09: `T-COORD-MONITOR-S16-RECHECK` (本 leaf external blocker timing input)
- F1-WarmStart G5 readiness 2026-05-10: `T-COORD-MONITOR-F1-WARMSTART` (Fusion external blocker resolution)

---

## §11 Status + impl trigger conditions

### §11.1 Status (本 design)

- **Created**: 2026-05-03 (T-Vision-Fusion-Design-CC sub-session of T-ROOT-COORD)
- **Phase**: design-draft (Rs review pending)
- **Author**: T-Vision-Fusion-Design-CC (sub-agent of T-ROOT-COORD#s11)
- **Permissions**: 06-Knowledge は CC Create/Update 可 (`02-Workflow/Vault Write Permissions.md:26`)
- **04-Specs SSOT update**: out-of-scope (Rs専権)、Rs 承認後 separate task `CC-L1A-04Specs-Update` 起票候補

### §11.2 Impl trigger conditions (state.md §1 dependencies + Rs §3.1 #4 起動承認)

**Pre-condition cascade** (全件解消で本 leaf 起動可):

1. **3 leaves COMPLETE** (precedent edge per state.md §1):
   - T-Vision-Pose: Pose alt path MVP-3 PASS (median trans < 5mm AND yaw < 10° on N=100 × 5 seeds、Pose §7.3)
   - T-Vision-CableState: Q5 PASS (mean ē < 5mm AND p95 < 10mm on N=100 + 10 U + 10 S worst-case、CableState §5.3)
   - T-Vision-DR: Tier 0c PASS (sim eval-det SR equivalence ≤ 5pp diff vs no-DR baseline、DR §6.1)

2. **External blocker (T-Skill milestone leaves、state.md §1)**:
   - Per-skill ≥ 50% floor for AC, IC, AR, Grip-CLAMP (CLAMP-R 含むかは T-Vision OQ3 経で resolve)
   - 現状 (2026-05-03 推定): AC ~49%、IC ~39.2%、AR ~10%、Grip-CLAMP ~0% → 全件未達、本 leaf 起動前提未充足

3. **External blocker (T-L1-B Phase 5-3 multi-clip orchestrator)**:
   - T-L1-B umbrella IN_PROGRESS、children=[] (Y2/KA5 minimal)
   - 起票 trigger: per-skill ≥ 50% floor + §16 cron PASS + CLAMP-R-Train sibling 起票
   - Phase 5-3 multi-clip orchestrator impl ready (5-clip routing chain logic、env-side current_clip_idx propagation)

4. **Rs §3.1 #4 起動承認**:
   - 上記 1-3 全件 evidence pin 経で本 leaf state.md status PENDING → IN_PROGRESS 移行 Rs 承認
   - design memo (本 file) Rs review + approval status APPROVED 経
   - Pose alt path Rs disposition (Pose §6.1 (a)/(b)/(c) 選択) 経
   - 必要なら本 design memo を §6.1 disposition 反映で revise

### §11.3 Next steps (impl phase trigger 後)

1. **別 task `CC-L1A-Phase-5-4-Impl` 起票**: design memo §11.2 pre-condition 全件解消 + Rs §3.1 #4 起動承認 経で起票
2. **P1 Estimator-Core integration**: Pose CoreV2 + CableState Solver + FusionAggregator + PoseEstimatorCoreFusion implementation
3. **P2 ObsAssembler**: VisionObsAssembler env wrapper module
4. **P3 Policy migration**: `migrate_first_layer_45_to_50` adapter + G-V0 unit test
5. **P4 AC fine-tune**: PPO + 50D obs、Tier 0c DR with rollback gate
6. **P5 G-V4 G8 eval**: 5-clip vision-based ≥ 30% N=10 ep × 5 seeds
7. **State.md transition**: 本 leaf state.md PENDING → IN_PROGRESS → COMPLETE (G-V4 PASS evidence pin 経)
8. **T-Vision umbrella COMPLETE gate**: 4 leaves (Pose + CableState + DR + 本 Fusion) 全 COMPLETE で T-Vision umbrella COMPLETE → Phase 5-4 G8 PASS direct precondition (umbrella state.md §1 goal_verification)

---

## §12 Output format compliance (CLAUDE.md §運用 + Path Y discipline)

| 区分 | 主張 | 根拠（出典） |
|------|------|---------------|
| 事実 | AC env obs は 45D base、`# Pad 42D → 45D for unified base model (IC-compatible). Dims [42:45] = zeros.` | `thread_isaac_lab/envs/newton_approach_cable_env.py:1332` |
| 事実 | target_seg_indices_r/l per-world、`_compute_target_seg_indices(bq)` 経で env-side computed | `thread_isaac_lab/envs/newton_approach_cable_env.py:225-226, 949` |
| 事実 | CC4 v3.2 PoseEstimate14D contract = `[seg_pos(3), seg_quat(4), clip_pos(3), clip_quat(4)]` | `thread-vault/07-Design/PoseEstimation-Design-v3.2.md:391, 446, 487` |
| 事実 | CC4 v3.2 §15 addendum: 45D→50D augmented obs、`migrate_first_layer_45_to_50` zero-init [45:50]、ε-variance 禁止 (raw pass-through regime+conf) | `PoseEstimation-Design-v3.2.md:80, 89, 198-220, 666` |
| 事実 | Pose alt path は clip 7D のみ提供、cable seg 7D は L1.A.2 (CableState) 経で Fusion 層で merge | `LL-Vision-Pose-Design.md:54, 308-310` |
| 事実 | CableState output = positions [B, 40, 3] + confidences [B, 40] (CableState40 dataclass) | `LL-Vision-CableState-Design.md:557-562` |
| 事実 | DR Tier 0a (D4+D5) → 0b (+D2+D3) → 0c (+D1) → 1 (+D6) curriculum、Tier 2 (D7+D8+R7) OUT-OF-SCOPE | `LL-Vision-DR-Design.md:111-127` |
| 推測 | Stage 1a Pose + 1b CableState parallel CUDA stream で latency budget G-V5 達成可能 (~50-65ms total) | Pose Stage 1 SAM2 ViT-B ~30-50ms + CableState Stage A-D ~10-15ms 並走、Stage 2-3 ~1-2ms sequential、empirical 確認は G-V5 |
| 推測 | edge_penalty=0.5 (target_seg ∈ {0, 39}) は AC env target_seg 通常 mid-cable (5-25 範囲) で出現率 < 5%、policy 影響軽微 | empirical 確認は MVP-3 P5 で edge case 出現率 log、necessary 時 OQ-F1 経で 0.7 緩和 |
| 推測 | regime+conf raw pass-through (CC4 v3.2 §15) で bit-identical baseline (E.5 invariant) 達成可能 | E.5 proof sketch §3.5 + Pose §H.4 + Appendix E migration spec、empirical 確認は G-V0 unit test |
| 推測 | min aggregation (§3.4) が geometric mean / weighted sum より policy 学習で defensive | bottleneck principle + early-iter exploration risk mitigation、empirical ablation は OQ-F2 経で MVP-4 defer |

---

## §13 Path Y / discipline references

- `feedback_recommendation_policy_2026-04-30.md`: §0 で Late Fusion を推奨 (★ 単一)、3 alternative REJECTED at design memo §2.4 経、本 design は selection result の prescribed structure
- `feedback_check_existing_eval_grep.md`: §1.5 + §10.3 で 既存 env / estimator / config の grep 証拠 pin
- `feedback_factual_api_verification.md`: §2.4 + §4.3 で CC4 v3.2 §6.4 spec の actual reference (PoseEstimation-Design-v3.2.md line numbers) 照合
- `feedback_premise_change_impact_analysis.md`: §2.5 で Pose alt path 採択 (Pose §6.1 (a)) の cable seg 7D 抜けに対する proactive impact analysis (Fusion 層で CableState 経 merge logic 確立)
- `feedback_geometric_vs_empirical_bc.md`: §6.5 G-V4 + §6.7 cascade で empirical eval gate (G-V0 → G-V4) を geometric/diagnostic 単独 NO-GO に依存させない
- `feedback_user_facing_style_v2_2026-04-30.md`: 本 file は internal working output (英語混在 design reference)、user-facing summary は thread report で別途 compact 記述
- `feedback_iterative_precheck.md`: 本 design は impl 起票時 `/pre-check` を経て Claude sub-agent で BLOCK→WARN→PASS validate (3 iter pattern)、本 file は pre-check 入力の prescribed structure

---

**Created**: 2026-05-03
**Status**: design-draft (Rs review pending)、impl 起票候補 `CC-L1A-Phase-5-4-Impl` (state.md §11.2 pre-condition 全件解消 + Rs §3.1 #4 起動承認 経)
**Owner**: T-Vision-Fusion-Design-CC (sub-session of T-ROOT-COORD#s11)
**Next action**: Rs review 本 design memo (§6.1 OQ-F9 Pose alt path Rs disposition 整合確認 + §11.2 impl trigger conditions Rs disposition 受領)
